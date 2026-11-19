#!/usr/bin/env python3
"""Regression guard: every used line of a tale, and every segment of it, played exactly once, in script order.

  python3 tools/story/check_lines.py <tale_id> <run.log>      # run = a full --autoplay --quit-on-done log

Reads the `SEG <line id> <seg index> t=` prints of StoryRunner._say and the script's beats. The expected order comes
from walking the beats' steps (prompts, lines, segs of split lines); hint / more lines are expected only when no
autoplay tap was late (they are idle fallbacks) and are not required. Exit 1 and a loud FAIL list on any missing,
doubled or out-of-order segment; prints OK otherwise.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def expected(script):
    lines = {l["id"]: l for l in script["lines"]}
    out = []

    def add(lid, segs=None):
        if not lid or lid not in lines:
            return
        n = len(lines[lid]["segs"])
        for i in (segs if segs is not None else range(n)):
            out.append((lid, int(i)))

    for b in script["beats"]:
        for st in b.get("steps", []):
            do = st.get("do")
            segs = st.get("segs")
            if do == "cover":
                add(st.get("prompt"))
            elif do in ("say", "walk", "walk_to", "walk_away", "climb", "go_inside", "flash"):
                add(st.get("line"), segs)
            elif do in ("tap", "tap_each", "build", "huff", "tap_steps", "blow", "shine", "gentle"):
                add(st.get("prompt"))
                for l in st.get("lines", []):
                    add(l)
                for s2 in st.get("steps", []) if isinstance(st.get("steps"), list) else []:
                    for l in s2.get("lines", []):
                        add(l)
                    add(s2.get("next"))
                if do == "gentle":
                    pass
            elif do == "quiz":
                add(st.get("prompt"))
                for v in st.get("wrong", {}).values():
                    for l in v:
                        add(l)
                for l in st.get("right", []):
                    add(l)
            elif do == "end":
                add(st.get("line"))
                add(st.get("after"))
    return out, lines


def main():
    tale, log = sys.argv[1], sys.argv[2]
    script = json.loads((ROOT / "game" / "stories" / tale / "script.json").read_text(encoding="utf-8"))
    exp, lines = expected(script)
    got = [(m.group(1), int(m.group(2))) for m in re.finditer(r"^SEG (\S+) (\d+) t=", Path(log).read_text(errors="replace"), re.M)]
    hints = {st.get(k) for b in script["beats"] for st in b.get("steps", []) for k in ("hint", "more") if st.get(k)}
    fails = []
    # doubles (a hint replaying a prompt is not a double of a different step: count against the expected count)
    from collections import Counter
    ce, cg = Counter(exp), Counter(got)
    for k, n in cg.items():
        if n > ce.get(k, 0) and k[0] not in hints:
            fails.append(f"DOUBLED {k[0]} seg {k[1]}: played {n}x, expected {ce.get(k, 0)}x")
    for k, n in ce.items():
        if cg.get(k, 0) < n:
            fails.append(f"MISSING {k[0]} seg {k[1]}: played {cg.get(k, 0)}x, expected {n}x")
    # order: the expected sequence must be a subsequence of what played (hints may interleave)
    it = iter(got)
    for k in exp:
        for g in it:
            if g == k:
                break
        else:
            fails.append(f"OUT OF ORDER at {k[0]} seg {k[1]}")
            break
    used = [l["id"] for l in script["lines"] if l.get("used", True)]
    never = [u for u in used if u not in {g[0] for g in got} and u not in hints]
    for u in never:
        fails.append(f"USED LINE NEVER PLAYED {u}")
    if fails:
        print(f"CHECK_LINES {tale} FAIL ({len(fails)}):")
        for f in fails:
            print("  ", f)
        sys.exit(1)
    print(f"CHECK_LINES {tale} OK: {len(exp)} segments in order, each exactly once ({len(got)} played)")


if __name__ == "__main__":
    main()
