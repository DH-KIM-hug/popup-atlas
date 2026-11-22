#!/usr/bin/env python3
"""Creative-tale name lines as 'name piece + fixed pieces' (톡톡 동화극장's method, its commit 373ad128, 2026-11-22).

  python3 -B tools/app/name_pieces.py            # witch_candy: copy + prepare the pieces, write pieces.json, patch script.json
  python3 -B tools/app/name_pieces.py --dry      # only print the mapping

A line holding the child's name is played as pieces joined on the device into one seamless clip
(game/app/name_voice.gd, same rules as 톡톡 engine/names.js assemble()):
  trim leading / trailing silence (-45 dB, 20 ms RMS window, keep 15 ms / 30 ms) -> the name piece's level matched to the
  mean RMS of the fixed pieces (+-6 dB) -> 6 ms fade in / 12 ms fade out -> the gap after each piece -> one clip ->
  the line's loudness gain (to -16 LUFS, measured here on the default-name join) + a soft limiter at 0.8.

Sources (톡톡 is READ-ONLY; nothing there is written — its tools are imported with bytecode writing off):
  - the split spec / plan: 톡톡 tools/elevenlabs/gen_name_split.py lines() + jobs() (name_split_spec.py, user-approved text)
  - fixed pieces: 톡톡 audio/el/witch_candy/parts/ko_<sig>.mp3 (its app bundle; trimmed, not polished)
  - default name pieces ("다현이랑", "다현이가", ...): the recordings 톡톡 chose for its build (~/.paper-tale/name_split/raw,
    sel.json 'best'), each the take recorded in that line's own context
Every piece here goes through 톡톡's polish EQ / compression chain (no loudnorm; the join gets the loudness gain), and is
stored as 16-bit mono 24 kHz WAV with importer "keep" (read as bytes and parsed by AudioStreamWAV.load_from_buffer).

Writes: game/audio/voice/witch_candy/name/<lang>_<sig>.wav (+ .import), game/audio/voice/witch_candy/name/pieces.json
(line id -> new text + pieces + gain + 톡톡 source), and the `pieces` / text fields of those lines in
game/stories/witch_candy/script.json (tools/story/seed_script.py re-applies them on a reseed: NAME_PIECES in the tale table).
"""
import json, os, re, subprocess, sys, tempfile
import numpy as np

sys.dont_write_bytecode = True
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TTK = os.path.expanduser('~/projects/2026/patjuk-game')
sys.path.insert(0, os.path.join(TTK, 'tools', 'elevenlabs'))
import gen_name_split as G  # noqa: E402  (read-only use: lines(), jobs(), SEL, WORK, gap_after, TRIM)
from polish import CHAIN  # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from name_pieces_apply import apply_to_script  # noqa: E402

TALE = 'witch_candy'
OUT = os.path.join(ROOT, 'game', 'audio', 'voice', TALE, 'name')
RES = f'res://audio/voice/{TALE}/name'
SCRIPT = os.path.join(ROOT, 'game', 'stories', TALE, 'script.json')
SR = 24000
TARGET_LUFS = -16.0
KEEP_IMPORT = '[remap]\n\nimporter="keep"\n'


def ff(*a):
    p = subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', '-y', *a], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-800:])
    return p.stderr


def prep(src, dst, trim):
    """src mp3 -> (trim) -> 톡톡 polish chain (EQ + compression, no loudnorm) -> 16-bit mono 24 kHz wav."""
    af = (G.TRIM + ',' if trim else '') + CHAIN
    ff('-i', src, '-af', af, '-ac', '1', '-ar', str(SR), '-sample_fmt', 's16', '-map_metadata', '-1', '-bitexact', dst)


def read_wav(p):
    raw = open(p, 'rb').read()
    i = raw.find(b'data')
    return np.frombuffer(raw[i + 8:], dtype='<i2').astype(np.float32) / 32768.0


def trim(d):  # names.js trimBuf (the runtime does the same; pieces are already trimmed, this only tightens)
    W = round(SR * .02); thr = 10 ** (-45 / 20); step = round(W / 4)
    def loud(i):
        s = d[i:min(len(d), i + W)]
        return len(s) and np.sqrt(np.mean(s * s)) > thr
    a = 0
    while a < len(d) and not loud(a):
        a += step
    b = len(d)
    while b > a and not loud(max(0, b - W)):
        b -= step
    return d[max(0, a - round(SR * .015)):min(len(d), b + round(SR * .03))]


def rms_db(d):
    return 20 * np.log10(np.sqrt(np.mean(d * d)) + 1e-9)


def join(parts):
    """parts = [(k, samples, gap)] -> joined samples (no loudness gain yet), names.js assemble() rules."""
    S = [rms_db(x) for k, x, g in parts if k == 'S']
    ref = sum(S) / len(S) if S else None
    out = []
    for i, (k, x, gap) in enumerate(parts):
        x = trim(x).copy()
        if k == 'N' and ref is not None:
            x *= 10 ** (max(-6, min(6, ref - rms_db(x))) / 20)
        fi, fo, L = round(SR * .006), round(SR * .012), len(x)
        x[:fi] *= np.arange(fi) / fi
        x[L - fo:] *= np.clip((L - np.arange(L - fo, L)) / fo, 0, 1)
        out.append(x)
        if i < len(parts) - 1:
            out.append(np.zeros(round(SR * gap), np.float32))
    return np.concatenate(out)


def lufs(d):
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, 'j.wav')
        write_wav(p, d)
        m = re.findall(r'^\s+I:\s+(-?[\d.]+) LUFS', ff('-i', p, '-af', 'ebur128', '-f', 'null', '-'), re.M)
        return float(m[-1]) if m else None


def write_wav(p, d):
    import wave
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(d, -1, 1) * 32767).astype('<i2').tobytes())


def strip_q(t):
    return t.strip().strip('"“”').strip()


def main():
    dry = '--dry' in sys.argv
    LS = G.lines(); J, plan = G.jobs(LS)
    sel = json.load(open(G.SEL))
    script = json.load(open(SCRIPT, encoding='utf-8'))
    by_text = {}
    for l in script['lines']:
        for si, s in enumerate(l['segs']):
            if '다현' in s['text']:
                by_text[strip_q(s['text'])] = (l['id'], si)
    os.makedirs(OUT, exist_ok=True)
    table = {}
    for a in plan:
        L = a['L']
        if L['tale'] != TALE or a['lang'] != 'ko' or a['v'] != 'o':
            continue
        hit = by_text.get(strip_q(L['key'])) or by_text.get(strip_q(L['keyNew']))
        if not hit:
            print('  (not in this app)', L['n'], L['key'])
            continue
        lid, si = hit
        P = L['parts']['ko']
        seg = [p for p in P['pieces'] if p['k'] != 'K']
        pieces, parts = [], []
        for j, ((how, sig), p) in enumerate(zip(a['seq'], seg)):
            assert how == 'rec', (L['n'], how)
            gap = G.gap_after(p, None) if j < len(seg) - 1 else 0
            name = f'ko_{sig}.wav'
            dst = os.path.join(OUT, name)
            if p['k'] == 'S':
                src = os.path.join(TTK, 'audio', 'el', TALE, 'parts', f'ko_{sig}.mp3'); src_rel = os.path.relpath(src, TTK)
                do_trim = False
            else:
                src = os.path.join(G.WORK, 'raw', sel[sig]['best']); src_rel = '~/.paper-tale/name_split/raw/' + sel[sig]['best']
                do_trim = True
            if not dry and not os.path.exists(dst):
                prep(src, dst, do_trim)
                open(dst + '.import', 'w').write(KEEP_IMPORT)
            pieces.append({'k': p['k'], 'tpl': p['tpl'], 'gap': gap, 'audio': f'{RES}/{name}', 'src': src_rel})
            if not dry:
                parts.append((p['k'], read_wav(dst), gap))
        gain = 0.0
        if not dry:
            j = join(parts)
            lu = lufs(j)
            gain = 0.0 if lu is None else round(max(-12, min(18, TARGET_LUFS - lu)), 2)
        full = next(r for r in json.load(open(os.path.join(TTK, 'tools', 'elevenlabs', 'name_split_manifest.json')))['tales'][TALE] if r['n'] == L['n'])
        table[lid] = {'seg': si, 'ttk_n': L['n'], 'text_old': L['key'], 'text': L['keyNew'], 'gain_db': gain,
                      'ttk_full_default': full['parts']['ko']['url'], 'pieces': pieces}
        print(lid, si, L['n'], L['keyNew'], 'gain', gain, '|', ' + '.join(f"{p['k']}:{p['tpl']}" for p in pieces))
    doc = {'note': "Name lines as name piece (N) + fixed pieces (S), joined on the device by game/app/name_voice.gd "
                   "(톡톡 동화극장 method, 2026-11-22). tpl: {A:<after a final consonant>/<after a vowel>} = the child's name + "
                   "particle. Made by tools/app/name_pieces.py from 톡톡's bundle (parts/) and its chosen default-name takes.",
           'tale': TALE, 'slot': 'A', 'default_name': '다현', 'sample_rate': SR, 'target_lufs': TARGET_LUFS, 'lines': table}
    if dry:
        return
    json.dump(doc, open(os.path.join(OUT, 'pieces.json'), 'w'), ensure_ascii=False, indent=1)
    apply_to_script(script, doc)
    open(SCRIPT, 'w', encoding='utf-8').write(json.dumps(script, ensure_ascii=False, indent=1) + '\n')
    print('pieces.json:', len(table), 'lines;', len([f for f in os.listdir(OUT) if f.endswith('.wav')]), 'wav pieces')


if __name__ == '__main__':
    main()
