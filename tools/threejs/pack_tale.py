#!/usr/bin/env python3
"""three.js player: turn a tale dump (tools/threejs/export_tale.gd) into streamable web data. Read-only on game/.

  python3 tools/threejs/pack_tale.py TALE [--dump build/threejs_dump/TALE] [--out threejs/public/data]

Layout under --out (shared folders are content- or path-addressed, so tales share what they have in common):
  shared/res/<res path>.webp     file textures (png / jpg -> webp q90, webp copied)
  shared/tex/<hash>.webp         runtime-built textures (ground maps, …) from the dump
  shared/prints/<hash>.webp      each batched card print, cropped out of its 4096² card-atlas page
  shared/audio/<res path>.mp3    sound (mp3 / wav copied, ogg -> mp3 128k: Safari has no Vorbis in decodeAudioData)
  tales/TALE/index.json          meta, chunk list, Godot line list, voice clip -> line map
  tales/TALE/c<i>.json           one chunk per beat: the textures / materials / meshes / nodes first needed in it,
                                 then its frames; binary ranges are [chunk, offset, bytes] into c<chunk>.bin.gz
  tales/TALE/c<i>.bin.gz         the chunk's vertex / index / instance blobs (gzip; the page inflates it)
A beat streams: the player starts on chunk 0 while the next chunks load.
"""
import gzip
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAME = os.path.join(ROOT, 'game')


def res_to_disk(p):
    return os.path.join(GAME, p.replace('res://', ''))


def main():
    from PIL import Image
    args = sys.argv[1:]
    tale = args[0]
    dump = os.path.join(ROOT, 'build/threejs_dump', tale)
    out = os.path.join(ROOT, 'threejs/public/data')
    if '--dump' in args:
        dump = args[args.index('--dump') + 1]
    if '--out' in args:
        out = args[args.index('--out') + 1]
    tdir = os.path.join(out, 'tales', tale)
    if os.path.isdir(tdir):
        for f in os.listdir(tdir):  # only our own files: c<i>.json / c<i>.bin.gz / index.json / gen/
            if re.fullmatch(r'c\d+\.(json|bin\.gz)|index\.json', f):
                os.remove(os.path.join(tdir, f))
    os.makedirs(tdir, exist_ok=True)
    sh = os.path.join(out, 'shared')
    d = json.load(open(os.path.join(dump, 'scene.json')))
    geo = bytearray(open(os.path.join(dump, 'geo.bin'), 'rb').read())
    T, MAT, ME, NO, FR = d['textures'], d['materials'], d['meshes'], d['nodes'], d['frames']
    sizes = {'res_tex': 0, 'run_tex': 0, 'prints': 0, 'audio': 0}
    shared_new = {'res_tex': 0, 'run_tex': 0, 'prints': 0, 'audio': 0}

    # ---------------------------------------------------------------- chunks: one per beat
    chunk_of_frame = []
    beats = []
    ci = -1
    for f in FR:
        if 'beat' in f or ci < 0:
            ci += 1
            beats.append({'id': f.get('beat', ''), 't0': f['t']})
        chunk_of_frame.append(ci)
    for i, b in enumerate(beats):
        b['t1'] = beats[i + 1]['t0'] if i + 1 < len(beats) else FR[-1]['t']
    n_chunks = len(beats)

    # ---------------------------------------------------------------- card atlas -> per-print crops
    skip_tex = set()
    pages = {}
    mm_meshes_by_frame = []

    def print_crops(batch, mesh_ids):
        """batch material -> {print idx: shared path} for the prints these MultiMesh meshes use."""
        atlas_id = batch['params']['atlas']['tex']
        params_id = batch['params']['params']['tex']
        skip_tex.add(atlas_id)
        pf = T[params_id]['file']
        pw = pf['w']
        pdata = struct.unpack_from(f'<{pf["float"][1] // 4}f', geo, pf['float'][0])
        px = lambda row, i: pdata[(row * pw + i) * 4:(row * pw + i) * 4 + 4]
        layers = T[atlas_id]['layers']
        prints = batch.setdefault('prints', {})
        for mid in mesh_ids:
            s = ME[mid]['surfaces'][0]
            if 'uv2' not in s['attrs']:
                continue
            idx = int(round(struct.unpack_from('<2f', geo, s['attrs']['uv2'][0])[1]))
            if idx >= pw or str(idx) in prints:
                continue
            u0, v0, du, dv = px(0, idx)
            layer = int(round(px(1, idx)[0]))
            key = (atlas_id, layer)
            if key not in pages:
                pages[key] = Image.open(os.path.join(dump, layers[layer]))
            pg = pages[key]
            W, H = pg.size
            box = (round(u0 * W), round(v0 * H), round((u0 + du) * W), round((v0 + dv) * H))
            crop = pg.crop(box)
            hsh = hashlib.sha1(crop.tobytes() + repr(crop.size).encode()).hexdigest()[:16]
            rel = f'shared/prints/{hsh}.webp'
            dst = os.path.join(out, rel)
            if not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                crop.save(dst, 'WEBP', quality=92, method=5)
                shared_new['prints'] += os.path.getsize(dst)
            sizes['prints'] += os.path.getsize(dst)
            prints[str(idx)] = rel

    batch_mats = [m for m in MAT if str(m.get('shader', '')).endswith('card_batch.gdshader')]
    for m in MAT:
        if str(m.get('shader', '')).endswith('card_shadow.gdshader') and 'mask_atlas' in m.get('params', {}):
            skip_tex.add(m['params']['mask_atlas']['tex'])
    if batch_mats:
        # every MultiMesh mesh drawn with a batch material (as the mesh's surface material or the node's override)
        uses = {id(b): set() for b in batch_mats}
        by_id = {b['id']: b for b in batch_mats}
        def mm_use(mm, mo):
            if not mm or mm.get('mesh', -1) < 0:
                return
            me = ME[mm['mesh']]
            mid = mo if mo is not None and mo >= 0 else me['surfaces'][0]['material']
            if mid in by_id:
                uses[id(by_id[mid])].add(mm['mesh'])
        mo_of = {}
        for f in FR:
            for c in f.get('set', []):
                if 'mo' in c:
                    mo_of[c['n']] = c['mo']
                if 'mm' in c:
                    mm_use(c['mm'], mo_of.get(c['n']))
                elif c.get('v') and NO[c['n']].get('mm'):
                    mm_use(NO[c['n']]['mm'], mo_of.get(c['n']))
        for b in batch_mats:
            print_crops(b, sorted(uses[id(b)]))

    # ---------------------------------------------------------------- file / runtime textures
    for e in T:
        if e['id'] in skip_tex:
            e['skip'] = True
            continue
        rp = e.get('res')
        if rp:
            src = res_to_disk(rp)
            rel = 'shared/img/' + os.path.splitext(rp.replace('res://', ''))[0] + '.webp'
            dst = os.path.join(out, rel)
            if not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                im = Image.open(src)
                im = im.convert('RGBA') if im.mode in ('RGBA', 'LA', 'P') or 'transparency' in im.info else im.convert('RGB')
                if re.search(r'paper_fibre|felt|noise|grain', rp, re.I):
                    im.save(dst, 'WEBP', lossless=True, method=5)  # data textures (fibre / grain) stay exact
                else:
                    # the art sources are lossless webp / png; lossy q85 is ~1/4 the bytes (the Godot web build ships
                    # lossy textures too)
                    im.save(dst, 'WEBP', quality=85, alpha_quality=90, method=5)
                shared_new['res_tex'] += os.path.getsize(dst)
            e['web'] = rel
            sizes['res_tex'] += os.path.getsize(dst)
            continue
        fl = e.get('file')
        if isinstance(fl, str):
            rel = 'shared/' + fl  # tex/<hash>.webp
            dst = os.path.join(out, rel)
            if not os.path.exists(dst):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(os.path.join(dump, fl), dst)
                shared_new['run_tex'] += os.path.getsize(dst)
            e['web'] = rel
            sizes['run_tex'] += os.path.getsize(dst)
        if e.get('layers'):
            ls = []
            for fl2 in e['layers']:
                rel = 'shared/' + fl2
                dst = os.path.join(out, rel)
                if not os.path.exists(dst):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copyfile(os.path.join(dump, fl2), dst)
                    shared_new['run_tex'] += os.path.getsize(dst)
                ls.append(rel)
                sizes['run_tex'] += os.path.getsize(dst)
            e['web_layers'] = ls

    # ---------------------------------------------------------------- audio
    amap = {}
    for f in FR:
        for a in f.get('audio', []):
            if a.get('ev') != 'start' or a['path'].startswith('<'):
                continue
            rp = a['path']
            if rp not in amap:
                if rp.startswith('dump://'):
                    src = os.path.join(dump, rp[len('dump://'):])
                    rel = f'tales/{tale}/' + os.path.splitext(rp[len('dump://'):])[0] + '.mp3'
                else:
                    src = res_to_disk(rp)
                    rel = 'shared/audio/' + os.path.splitext(rp.replace('res://', ''))[0] + '.mp3'
                ext = os.path.splitext(src)[1].lower()
                dst = os.path.join(out, rel)
                if not os.path.exists(dst):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    if ext == '.mp3':
                        shutil.copyfile(src, dst)
                    else:
                        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-c:a', 'libmp3lame', '-b:a', '128k', dst], check=True)
                    shared_new['audio'] += os.path.getsize(dst)
                dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src],
                                           capture_output=True, text=True).stdout.strip() or 0)
                amap[rp] = (rel, round(dur, 4))
                sizes['audio'] += os.path.getsize(dst)
            a['path'], a['dur'] = amap[rp]

    # ---------------------------------------------------------------- MultiMesh motion: keep every 3rd dump of a run
    # A fold / pop-up moves every card of a batch each frame (turnip feast: 2768 full instance dumps, 23 MB). The
    # player interpolates instance matrices between kept dumps (10 fps keys + the last pose), so 2 of 3 are dropped.
    dumps = {}  # node -> [(frame index, set entry)]
    for fi, f in enumerate(FR):
        for c in f.get('set', []):
            if c.get('mm'):
                dumps.setdefault(c['n'], []).append((fi, c))
    dropped = 0
    for lst in dumps.values():
        run = []
        for k, (fi, c) in enumerate(lst + [(None, None)]):
            if run and (fi is None or fi - run[-1][0] != 1 or c['mm'].get('n') != run[-1][1]['mm'].get('n')):
                for j, (_, cc) in enumerate(run):
                    if j % 3 != 0 and j != len(run) - 1:
                        cc['_drop'] = True
                run = []
            if fi is not None:
                run.append((fi, c))
    for f in FR:
        for c in f.get('set', []):
            if c.pop('_drop', False):
                del c['mm']
                c.pop('mmh', None)
                dropped += 1
    for f in FR:
        f['set'] = [c for c in f.get('set', []) if len(c) > 1] if 'set' in f else None
        if f['set'] is None or not f['set']:
            f.pop('set', None)

    # ---------------------------------------------------------------- MultiMesh keys as deltas
    # Between two kept keys of a node only some cards move (a pop-up wave, a fold): a key stores the instances that
    # changed since the node's previous key (indices + 16 floats each); the player rebuilds the full buffer.
    import numpy as np
    blob_cache = {}

    def add_blob(b):
        k = hashlib.sha1(b).hexdigest()
        if k in blob_cache:
            return blob_cache[k]
        off = len(geo)
        geo.extend(b)
        geo.extend(b'\0' * ((4 - len(geo) % 4) % 4))
        blob_cache[k] = [off, len(b)]
        return blob_cache[k]

    prev_xf = {}
    full_b = delta_b = 0
    for n in NO:
        if n.get('mm') and n['mm'].get('xf'):
            r = n['mm']['xf']
            prev_xf[n['id']] = np.frombuffer(bytes(geo[r[0]:r[0] + r[1]]), dtype=np.float32).reshape(-1, 16)
    for f in FR:
        for c in f.get('set', []):
            mm = c.get('mm')
            if not mm or not mm.get('xf'):
                continue
            r = mm['xf']
            cur = np.frombuffer(bytes(geo[r[0]:r[0] + r[1]]), dtype=np.float32).reshape(-1, 16)
            prev = prev_xf.get(c['n'])
            prev_xf[c['n']] = cur
            if prev is None or prev.shape != cur.shape:
                full_b += r[1]
                continue
            ch = np.nonzero(np.any(np.abs(cur - prev) > 1e-6, axis=1))[0].astype(np.uint32)
            if len(ch) * 17 > len(cur) * 16 * 0.8:
                full_b += r[1]
                continue
            mm['dx'] = add_blob(ch.tobytes())
            mm['dv'] = add_blob(np.ascontiguousarray(cur[ch]).tobytes())
            del mm['xf']
            delta_b += len(ch) * 68
    print(f'  MultiMesh keys: full {full_b / 1048576:.1f} MB, deltas {delta_b / 1048576:.1f} MB')

    # ---------------------------------------------------------------- compact transforms
    # 12 numbers (the last column is always 0,0,0,1), 4 decimals (0.1 mm in a ~10 m world): JSON about half the size
    def cx(x):
        return [round(v, 4) + 0.0 for k, v in enumerate(x) if k not in (3, 7, 11, 15)]
    for f in FR:
        for c in f.get('set', []):
            if 'x' in c:
                c['x'] = cx(c['x'])
        if f.get('cam'):
            for vn in f['cam']:
                if 'x' in f['cam'][vn]:
                    f['cam'][vn]['x'] = cx(f['cam'][vn]['x'])
        for l in f.get('lights', []):
            if 'x' in l:
                l['x'] = cx(l['x'])

    # ---------------------------------------------------------------- dependency walk -> chunk of first use
    owner = {'tex': {}, 'mat': {}, 'mesh': {}, 'node': {}}
    blob_owner = {}  # (off, size) -> chunk

    def blob(r, c):
        k = (r[0], r[1])
        if k not in blob_owner:
            blob_owner[k] = c

    def need_tex(i, c):
        if i is None or i < 0 or i in owner['tex']:
            return
        owner['tex'][i] = c
        e = T[i]
        if isinstance(e.get('file'), dict) and 'float' in e['file']:
            blob(e['file']['float'], c)
        if e.get('atlas', -1) >= 0:
            need_tex(e['atlas'], c)

    def need_params(p, c):
        for v in (p or {}).values():
            if isinstance(v, dict) and 'tex' in v:
                need_tex(v['tex'], c)

    def need_mat(i, c):
        if i is None or i < 0 or i in owner['mat']:
            return
        owner['mat'][i] = c
        need_params(MAT[i].get('params'), c)
        if 'next_pass' in MAT[i]:
            need_mat(MAT[i]['next_pass'], c)

    def need_mesh(i, c):
        if i is None or i < 0 or i in owner['mesh']:
            return
        owner['mesh'][i] = c
        for s in ME[i]['surfaces']:
            need_mat(s['material'], c)
            for r in s['attrs'].values():
                blob(r, c)
            if 'index' in s:
                blob(s['index'], c)

    def need_mm(mm, c):
        if not mm:
            return
        need_mesh(mm.get('mesh', -1), c)
        for k in ('xf', 'cu', 'co', 'dx', 'dv'):
            if k in mm:
                blob(mm[k], c)

    def need_node(i, c):
        if i in owner['node']:
            return
        owner['node'][i] = c
        need_mm(NO[i].get('mm'), c)

    for fi, f in enumerate(FR):
        c = chunk_of_frame[fi]
        for s in f.get('set', []):
            need_node(s['n'], c)
            if 'm' in s:
                need_mesh(s['m'], c)
            for m in s.get('mats', []):
                need_mat(m, c)
            for k in ('mo', 'ov'):
                if k in s:
                    need_mat(s[k], c)
            if 'mm' in s:
                need_mm(s['mm'], c)
            if 'ip' in s:
                need_params(s['ip'], c)
            if s.get('spr') and s['spr'].get('tex', -1) >= 0:
                need_tex(s['spr']['tex'], c)
        for mc in f.get('mat', []):
            need_mat(mc['mat'], c)
            need_params(mc['p'], c)
        for vn, rd in (f.get('rig') or {}).items():
            need_params(rd, c)
        for l in f.get('lights', []):
            need_node(l['n'], c)
        for a in f.get('audio', []):
            need_node(a['p'], c) if a.get('p', -1) >= 0 else None

    # ---------------------------------------------------------------- write chunk bins, rewrite ranges
    normal_blobs = {(s['attrs'][k][0], s['attrs'][k][1]) for m in ME for s in m['surfaces'] for k in ('normal', 'tangent') if k in s['attrs']}
    other_use = {(r[0], r[1]) for m in ME for s in m['surfaces'] for k, r in s['attrs'].items() if k not in ('normal', 'tangent')}
    new_range = {}
    bins = [bytearray() for _ in range(n_chunks)]
    import array
    for (off, size), c in sorted(blob_owner.items(), key=lambda kv: (kv[1], kv[0][0])):
        b = bins[c]
        o = len(b)
        if (off, size) in normal_blobs and (off, size) not in other_use:
            # unit normals / tangents as normalized int8 (3 / 4 bytes a vertex instead of 12 / 16)
            fl = array.array('f'); fl.frombytes(geo[off:off + size])
            q = bytes((max(-127, min(127, round(v * 127))) & 0xff) for v in fl)
            b += q
            b += b'\0' * ((4 - len(b) % 4) % 4)
            new_range[(off, size)] = [c, o, len(q), 'i8']
            continue
        b += geo[off:off + size]
        b += b'\0' * ((4 - len(b) % 4) % 4)
        new_range[(off, size)] = [c, o, size]

    def rr(r):
        return new_range.get((r[0], r[1]), [-1, 0, 0])

    def fix_mm(mm):
        if mm:
            for k in ('xf', 'cu', 'co', 'dx', 'dv'):
                if k in mm:
                    mm[k] = rr(mm[k])

    for e in T:
        if isinstance(e.get('file'), dict) and 'float' in e['file']:
            e['file']['float'] = rr(e['file']['float'])
    for m in ME:
        for s in m['surfaces']:
            s['attrs'] = {k: rr(v) for k, v in s['attrs'].items()}
            if 'index' in s:
                s['index'] = rr(s['index'])
    for n in NO:
        fix_mm(n.get('mm'))
    for f in FR:
        for s in f.get('set', []):
            fix_mm(s.get('mm'))

    # ---------------------------------------------------------------- write chunks
    chunks = []
    for c in range(n_chunks):
        defs = {k: [] for k in ('textures', 'materials', 'meshes', 'nodes')}
        for kind, lst, key in (('tex', T, 'textures'), ('mat', MAT, 'materials'), ('mesh', ME, 'meshes'), ('node', NO, 'nodes')):
            defs[key] = [lst[i] for i, cc in sorted(owner[kind].items()) if cc == c]
        frs = [f for fi, f in enumerate(FR) if chunk_of_frame[fi] == c]
        defs['frames'] = frs
        jp = os.path.join(tdir, f'c{c}.json')
        json.dump(defs, open(jp, 'w'), ensure_ascii=False, separators=(',', ':'))
        bp = os.path.join(tdir, f'c{c}.bin.gz')
        with gzip.open(bp, 'wb', compresslevel=9) as gz:
            gz.write(bytes(bins[c]))
        aud = sorted({a['path'] for f in frs for a in f.get('audio', []) if a.get('ev') == 'start' and not a['path'].startswith('<')})
        jgz = len(gzip.compress(open(jp, 'rb').read(), 6))
        chunks.append({**beats[c], 'json': f'c{c}.json', 'bin': f'c{c}.bin.gz', 'json_bytes': os.path.getsize(jp), 'json_gz': jgz,
                       'bin_bytes': os.path.getsize(bp), 'bin_raw': len(bins[c]), 'audio': aud,
                       'audio_bytes': sum(os.path.getsize(os.path.join(out, p)) for p in aud),
                       'tex': sorted({e['web'] for e in defs['textures'] if e.get('web')} |
                                     {p for m in defs['materials'] for p in (m.get('prints') or {}).values()})})

    # ---------------------------------------------------------------- lines: Godot's LINE list (same run) + clip map
    lines = []
    log = os.path.join(dump, 'export.log')
    if os.path.exists(log):
        for ln in open(log, encoding='utf-8', errors='replace'):
            m = re.match(r'LINE (\S+) t=([\d.]+)', ln)
            if m:
                lines.append([m.group(1), float(m.group(2))])
    sc = json.load(open(os.path.join(GAME, 'stories', tale, 'script.json')))
    clip_line = {}
    line_clips = {}
    for l in sc.get('lines', []):
        for s in l.get('segs', []):
            if s.get('audio') and s['audio'] in amap:
                clip_line[amap[s['audio']][0]] = l['id']  # display only: one clip can serve two lines
                line_clips.setdefault(l['id'], []).append(amap[s['audio']][0])
    # lines whose voice is generated (NameVoice) or shared: take the clip the runner actually started for each LINE
    vstarts = [(f.get('clock', f['t']), a['path']) for f in FR for a in f.get('audio', []) if a.get('ev') == 'start' and a.get('voice')]
    for lid, lt in lines:
        for ck, pth in vstarts:
            if abs(ck - lt) < 0.3 and pth not in line_clips.setdefault(lid, []):
                line_clips[lid].append(pth)
    cover = {}
    cj = os.path.join(GAME, 'stories', tale, 'cover.json')
    if os.path.exists(cj):
        cover = json.load(open(cj)).get('cover', {})
    meta = d['meta']
    idx = {'tale': tale, 'title': sc.get('title', tale), 'fps': meta['fps'], 'viewport': meta['viewport'], 'godot': meta['godot'],
           'made': meta['made'], 'done_at': meta.get('done_at'), 'unhandled': meta.get('unhandled'), 'shaders': meta.get('shaders'),
           'chunks': chunks, 'lines': lines, 'clip_line': clip_line, 'line_clips': line_clips, 'taps': meta.get('taps'), 'cover': cover}
    json.dump(idx, open(os.path.join(tdir, 'index.json'), 'w'), ensure_ascii=False, separators=(',', ':'))

    # ---------------------------------------------------------------- report
    tot_json = sum(c['json_gz'] for c in chunks)
    tot_bin = sum(c['bin_bytes'] for c in chunks)
    # each shared file once (the same print / clip can be listed by several batch materials and chunks)
    used = set()
    for c in chunks:
        used |= set(c['tex']) | set(c['audio'])
    kind = lambda p: 'prints' if '/prints/' in p else 'audio' if p.endswith(('.mp3', '.wav')) else 'run_tex' if '/tex/' in p else 'res_tex'
    sizes = {'res_tex': 0, 'run_tex': 0, 'prints': 0, 'audio': 0}
    for pth in used:
        sizes[kind(pth)] += os.path.getsize(os.path.join(out, pth))
    wire = tot_json + tot_bin + sum(sizes.values())
    MB = 1048576
    print(f'{tale}: {len(FR)} frames, {n_chunks} chunks, {len(lines)} lines, audio clips {len(amap)}, MultiMesh dumps dropped {dropped}')
    for c in chunks:
        print(f'  c{chunks.index(c):<2} {c["id"]:<12} t={c["t0"]:7.2f}  json {c["json_gz"] / MB:5.2f} MB gz  bin {c["bin_bytes"] / MB:5.2f} MB'
              f'  audio {c["audio_bytes"] / MB:5.2f} MB  tex {len(c["tex"])}')
    print(f'  wire: json {tot_json / MB:.2f}  geo {tot_bin / MB:.2f}  res tex {sizes["res_tex"] / MB:.2f}  runtime tex {sizes["run_tex"] / MB:.2f}'
          f'  prints {sizes["prints"] / MB:.2f}  audio {sizes["audio"] / MB:.2f}  = {wire / MB:.2f} MB')
    print(f'  new in shared/: ' + '  '.join(f'{k} {v / MB:.2f}' for k, v in shared_new.items()))
    unres = sorted({a['path'] for f in FR for a in f.get('audio', []) if a.get('ev') == 'start' and a['path'].startswith('<')})
    if unres:
        print('  UNRESOLVED audio', unres)
    json.dump({'tale': tale, 'wire_bytes': wire, 'json_gz': tot_json, 'geo_gz': tot_bin, 'sizes': sizes,
               'chunks': [{k: c[k] for k in ('id', 'json_gz', 'bin_bytes', 'audio_bytes')} for c in chunks]},
              open(os.path.join(tdir, '..', f'{tale}.size.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
