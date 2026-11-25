#!/usr/bin/env python3
"""three.js pilot: turn a Godot dump (tools/threejs_pilot/export_scene.gd) into the web data folder.
Read-only on game/.

  python3 tools/threejs_pilot/pack_assets.py <dump_dir> [out_dir]
  (out_dir default pilot/threejs/public/data/turnip_seed; it must not exist or be empty)

- geo.bin copied; scene.json rewritten compact.
- file textures (textures[i].res) -> out/res/<path>.webp (webp copied, png / jpg -> webp q90 with alpha); "web" set.
- runtime textures copied, except the card atlas pages: each print the spread's batched cards use is cropped out
  of its 4096² atlas page (params texture row 0 = rect, row 1 = layer) into out/res/prints/p<idx>.webp and listed in
  scene.json "prints" {idx: path}. (The atlas holds every print the app registered, 8 pages = 512 MB as RGBA;
  the spread needs a small part of it.)
- audio the recording starts -> out/<path> (mp3 / wav copied, ogg -> mp3 128k: no Vorbis in Safari's
  decodeAudioData, and Playwright's WebKit has no AAC); "dur" = the source length, so loops can skip the mp3
  encoder delay; event paths rewritten.
"""
import json
import os
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
    dump = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'pilot/threejs/public/data/turnip_seed')
    if os.path.isdir(out) and os.listdir(out):
        sys.exit(f'{out} is not empty (delete it first)')
    os.makedirs(out, exist_ok=True)
    d = json.load(open(os.path.join(dump, 'scene.json')))
    geo = open(os.path.join(dump, 'geo.bin'), 'rb').read()
    import gzip
    # shipped gzipped (Pages serves .bin uncompressed); the page inflates it with DecompressionStream
    with gzip.open(os.path.join(out, 'geo.bin.gz'), 'wb', compresslevel=9) as gz:
        gz.write(geo)
    sizes = {'tex_res': 0, 'tex_runtime': 0, 'prints': 0, 'audio': 0}

    # card atlas -> per-print crops
    batch = next((m for m in d['materials'] if str(m.get('shader', '')).endswith('card_batch.gdshader')), None)
    skip_tex = set()
    prints = {}
    if batch:
        atlas_id = batch['params']['atlas']['tex']
        params_id = batch['params']['params']['tex']
        skip_tex.add(atlas_id)
        mask = next((m for m in d['materials'] if str(m.get('shader', '')).endswith('card_shadow.gdshader')), None)
        if mask and 'mask_atlas' in mask.get('params', {}):
            skip_tex.add(mask['params']['mask_atlas']['tex'])
        pf = d['textures'][params_id]['file']
        pw = pf['w']
        pdata = struct.unpack_from(f'<{pf["float"][1] // 4}f', geo, pf['float'][0])
        px = lambda row, i: pdata[(row * pw + i) * 4:(row * pw + i) * 4 + 4]
        mm_meshes = set()
        for n in d['nodes']:
            if n.get('mm'):
                mm_meshes.add(n['mm']['mesh'])
        for f in d['frames']:
            for c in f.get('set', []):
                if 'mm' in c and c['mm']:
                    mm_meshes.add(c['mm']['mesh'])
        pages = {}
        layers = d['textures'][atlas_id]['layers']
        for mid in mm_meshes:
            if mid < 0:
                continue
            s = d['meshes'][mid]['surfaces'][0]
            if 'uv2' not in s['attrs']:
                continue
            idx = int(round(struct.unpack_from('<2f', geo, s['attrs']['uv2'][0])[1]))
            if idx >= pw or str(idx) in prints:
                continue
            u0, v0, du, dv = px(0, idx)
            layer = int(round(px(1, idx)[0]))
            if layer not in pages:
                pages[layer] = Image.open(os.path.join(dump, layers[layer]))
            pg = pages[layer]
            W, H = pg.size
            box = (round(u0 * W), round(v0 * H), round((u0 + du) * W), round((v0 + dv) * H))
            rel = f'res/prints/p{idx}.webp'
            os.makedirs(os.path.join(out, 'res/prints'), exist_ok=True)
            pg.crop(box).save(os.path.join(out, rel), 'WEBP', quality=92, method=5)
            prints[str(idx)] = rel
            sizes['prints'] += os.path.getsize(os.path.join(out, rel))
        d['prints'] = prints

    for e in d['textures']:
        rp = e.get('res')
        if e['id'] in skip_tex:
            continue
        if not rp:
            fl = e.get('file')
            if isinstance(fl, str):
                os.makedirs(os.path.join(out, 'tex'), exist_ok=True)
                shutil.copyfile(os.path.join(dump, fl), os.path.join(out, fl))
                sizes['tex_runtime'] += os.path.getsize(os.path.join(out, fl))
            continue
        src = res_to_disk(rp)
        rel = 'res/' + os.path.splitext(rp.replace('res://', ''))[0] + '.webp'
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            if src.lower().endswith('.webp'):
                shutil.copyfile(src, dst)
            else:
                im = Image.open(src)
                im = im.convert('RGBA') if im.mode in ('RGBA', 'LA', 'P') else im.convert('RGB')
                im.save(dst, 'WEBP', quality=90, method=5)
        e['web'] = rel
        sizes['tex_res'] += os.path.getsize(dst)

    amap = {}
    for f in d['frames']:
        for a in f.get('audio', []):
            if a.get('ev') != 'start' or a['path'].startswith('<'):
                continue
            rp = a['path']
            if rp not in amap:
                src = res_to_disk(rp)
                base, ext = os.path.splitext(rp.replace('res://', ''))
                rel = base + ('.mp3' if ext == '.ogg' else ext)
                dst = os.path.join(out, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if not os.path.exists(dst):
                    if ext == '.ogg':
                        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', src, '-c:a', 'libmp3lame', '-b:a', '128k', dst], check=True)
                    else:
                        shutil.copyfile(src, dst)
                dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src],
                                           capture_output=True, text=True).stdout.strip() or 0)
                amap[rp] = (rel, dur)
                sizes['audio'] += os.path.getsize(dst)
            a['path'], a['dur'] = amap[rp]
    sj = os.path.join(out, 'scene.json')
    json.dump(d, open(sj, 'w'), ensure_ascii=False, separators=(',', ':'))
    sizes['scene_json'] = os.path.getsize(sj)
    sizes['geo_bin_gz'] = os.path.getsize(os.path.join(out, 'geo.bin.gz'))
    for k, v in sizes.items():
        print(f'{k:12s} {v / 1048576:7.2f} MB')
    print(f'{"total":12s} {sum(sizes.values()) / 1048576:7.2f} MB   prints {len(prints)}  audio clips {len(amap)}  '
          f'unresolved audio {sorted({a["path"] for f in d["frames"] for a in f.get("audio", []) if a.get("ev") == "start" and a["path"].startswith("<")})}')


if __name__ == '__main__':
    main()
