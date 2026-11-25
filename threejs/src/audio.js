// Web Audio playback of the recorded Godot audio events (voice, music, ambience beds, fx).
// Unlocked by the first tap (iOS needs a gesture). On iOS 17+ `navigator.audioSession.type = 'playback'` makes the
// page ignore the silent switch (Capacitor: AVAudioSession .playback in the AppDelegate instead).
const db2gain = (db) => Math.pow(10, db / 20);

export class AudioPlayer {
  constructor(base) {
    this.base = base;
    this.ctx = null;
    this.buffers = new Map();
    this.loading = new Map();
    this.voices = new Map(); // godot player id -> {src, gain}
    this.buses = new Map();
    this.bytes = 0;
    this.started = 0;
    this.log = [];
  }

  // the context exists from the start (suspended until a tap) so clips can be decoded while the page loads
  ensure() {
    if (!this.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AC({ latencyHint: 'playback' });
      this.master = this.ctx.createGain();
      this.master.connect(this.ctx.destination);
      // output meter (tests: tools/threejs/check_tale.mjs reads it)
      this.meter = this.ctx.createAnalyser();
      this.meter.fftSize = 1024;
      this.master.connect(this.meter);
    }
    return this.ctx;
  }

  level() {
    if (!this.meter) return 0;
    const a = new Float32Array(this.meter.fftSize);
    this.meter.getFloatTimeDomainData(a);
    let s = 0;
    for (const v of a) s += v * v;
    return Math.sqrt(s / a.length);
  }

  unlock() {
    try { if (navigator.audioSession && navigator.audioSession.type !== 'playback') navigator.audioSession.type = 'playback'; } catch (e) { /* older Safari */ }
    if (!this.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AC({ latencyHint: 'playback' });
      this.master = this.ctx.createGain();
      this.master.connect(this.ctx.destination);
    }
    if (this.ctx.state !== 'running') { this.ctx.resume(); this.poke(); }
    return this.ctx;
  }

  get running() { return !!this.ctx && this.ctx.state === 'running'; }

  bus(name) {
    let b = this.buses.get(name);
    if (!b) {
      b = this.ctx.createGain();
      b.connect(this.master);
      this.buses.set(name, b);
    }
    return b;
  }

  setBuses(list) {
    if (!this.ctx) return;
    for (const [name, db, mute] of list) {
      const g = this.bus(name);
      g.gain.setTargetAtTime(mute ? 0 : db2gain(db), this.ctx.currentTime, 0.03);
    }
  }

  url(path) { return this.base + path.replace('res://', ''); }

  load(path) {
    if (this.buffers.has(path)) return Promise.resolve(this.buffers.get(path));
    if (this.loading.has(path)) return this.loading.get(path);
    this.ensure();
    const p = fetch(this.url(path))
      .then((r) => { if (!(r.ok || r.status === 0)) throw new Error(path + ' ' + r.status); return r.arrayBuffer(); })
      .then((ab) => { this.bytes += ab.byteLength; return this.ctx.decodeAudioData(ab); })
      .then((buf) => { this.buffers.set(path, buf); return buf; })
      .catch((e) => { console.warn('audio', e); return null; });
    this.loading.set(path, p);
    return p;
  }

  preload(paths) { return Promise.all(paths.map((p) => this.load(p))); }

  event(ev, listener) {
    if (!this.ctx) return;
    if (ev.ev === 'start') {
      this.stop(ev.p);
      const buf = this.buffers.get(ev.path);
      this.log.push([ev.path.split('/').pop(), !!buf, +(this.ctx.currentTime.toFixed(2))]);
      if (!buf) { this.load(ev.path); return; }
      const src = this.ctx.createBufferSource();
      src.buffer = buf;
      src.loop = !!ev.loop;
      if (src.loop && ev.dur && buf.duration - ev.dur > 0.005) {
        // the decoder kept the mp3 encoder delay + padding: loop only the real samples (LAME delay 1105 samples)
        src.loopStart = Math.min(1105 / buf.sampleRate, buf.duration - ev.dur);
        src.loopEnd = src.loopStart + ev.dur;
      }
      src.playbackRate.value = ev.pitch || 1;
      const gain = this.ctx.createGain();
      let g = db2gain(ev.vol || 0);
      if (ev.pos && listener && ev.model !== 3) {
        // AudioStreamPlayer3D inverse / inverse-square distance attenuation (Godot: unit_size, max_db)
        const dx = ev.pos[0] - listener.x, dy = ev.pos[1] - listener.y, dz = ev.pos[2] - listener.z;
        const dist = Math.max(Math.hypot(dx, dy, dz), 0.001);
        const unit = ev.unit || 10;
        let att = 1;
        if (ev.model === 0) att = unit / dist; else if (ev.model === 1) att = (unit / dist) ** 2; else if (ev.model === 2) att = Math.exp(-dist / unit * 0.5);
        g *= Math.min(att, db2gain(ev.maxdb ?? 3));
        if (ev.maxdist && dist > ev.maxdist) g = 0;
      }
      gain.gain.value = g;
      src.connect(gain).connect(this.bus(ev.bus || 'Master'));
      src.start(0, (ev.at || 0) % buf.duration);
      this.voices.set(ev.p, { src, gain, base: g / db2gain(ev.vol || 0) });
      this.started++;
      src.onended = () => { const v = this.voices.get(ev.p); if (v && v.src === src) this.voices.delete(ev.p); };
    } else if (ev.ev === 'stop') {
      this.stop(ev.p);
    } else if (ev.ev === 'vol') {
      const v = this.voices.get(ev.p);
      if (v) v.gain.gain.setTargetAtTime(db2gain(ev.vol) * v.base, this.ctx.currentTime, 0.02);
    }
  }

  stop(id) {
    const v = this.voices.get(id);
    if (v) { try { v.src.stop(); } catch (e) { /* already stopped */ } this.voices.delete(id); }
  }

  stopAll() { for (const id of [...this.voices.keys()]) this.stop(id); }

  // a short buffer played on the unlocking tap: iOS only opens the output on a sound started inside the gesture
  poke() {
    if (!this.ctx) return;
    const b = this.ctx.createBuffer(1, 1, 22050);
    const s = this.ctx.createBufferSource();
    s.buffer = b; s.connect(this.ctx.destination); s.start(0);
  }

  // between tales: drop decoded clips that are not shared (keeps memory flat over a long session)
  clear() { this.stopAll(); this.buffers.clear(); this.loading.clear(); this.log.length = 0; this.started = 0; }
}
