#!/usr/bin/env python3
"""작업표의 id 들을 한 장씩 생성하는 큐 뼈대 (예: codex exec + image_gen).
  python3 run_jobs.py jobs_<묶음>.json id1 id2 ...   (id 를 안 주면 전부, 파일 순서대로 — pass 2 는 pass 1 뒤)
- 이미 있으면 건너뜀(중단 뒤 다시 돌리면 이어짐)
- 한도 메시지면 풀리는 시각까지(최대 1시간 간격) 기다렸다 같은 그림부터
- 타임아웃이면 프로세스 그룹째 종료(고아 생성 프로세스 방지)
GEN_CMD 는 자기 도구에 맞게 바꾼다."""
import datetime, json, os, re, subprocess, sys, time

GEN_CMD = ['codex', 'exec', '-s', 'workspace-write', '--skip-git-repo-check']
LIMIT_RE = re.compile(r'(usage limit|rate limit|limit reached|too many requests|quota|try again (?:at|in))', re.I)
TIMEOUT = 900

def wait_until(text):
    now = datetime.datetime.now()
    m = re.search(r'resets_at\\?"?:\s*(\d{10})', text)
    if m: return datetime.datetime.fromtimestamp(int(m.group(1))) + datetime.timedelta(minutes=2)
    m = re.search(r'try again in\s+(?:(\d+)\s*h\w*)?\s*(?:(\d+)\s*m\w*)?', text, re.I)
    if m and any(m.groups()):
        return now + datetime.timedelta(hours=int(m.group(1) or 0), minutes=int(m.group(2) or 0) + 2)
    return now + datetime.timedelta(minutes=30)

def instruction(j, pf):
    asp = j.get('aspect') or ('square 1:1' if j['kind'] == 'sprite' else 'landscape 16:9')
    refs = ' '.join(j.get('refs', []))
    return (f"Use your image generation tool to create ONE image, {asp}. Read the full prompt from {pf} and pass it VERBATIM. "
            + (f"Pass these reference images in referenced_image_paths (read-only): {refs} . " if refs else '')
            + f"Save (copy) the generated image to {j['out']} . No other file changes, no installs, no git. Reply only SAVED or FAILED <reason>.")

def main():
    jobs = json.load(open(sys.argv[1])); want = set(sys.argv[2:])
    for j in jobs:
        if want and j['id'] not in want: continue
        if os.path.exists(j['out']): print('skip', j['id']); continue
        os.makedirs(os.path.dirname(j['out']), exist_ok=True)
        pf = f".prompt_{j['id']}.txt"   # 작업별 임시 파일(실행기 여러 개가 덮어쓰지 않게)
        open(pf, 'w').write(j['prompt'])
        txt = ''
        for _ in range(200):
            pr = subprocess.Popen(GEN_CMD + [instruction(j, pf)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, start_new_session=True)
            try: so, se = pr.communicate(timeout=TIMEOUT)
            except subprocess.TimeoutExpired:
                try: os.killpg(pr.pid, 15)
                except Exception: pass
                so, se = pr.communicate(); so = (so or '') + ' TIMEOUT'
            txt = (so or '') + (se or '')
            if os.path.exists(j['out']) or not LIMIT_RE.search(txt): break
            until = wait_until(txt)
            print(f'{datetime.datetime.now():%H:%M} limit -> wait until {until:%m-%d %H:%M}', flush=True)
            time.sleep(min(3600, max(60, (until - datetime.datetime.now()).total_seconds())))
        print(j['id'], 'ok' if os.path.exists(j['out']) else 'FAIL ' + txt[-300:], flush=True)
        os.remove(pf)

if __name__ == '__main__':
    main()
