#!/bin/sh
# Publish build/web to the orphan `gh-pages` branch (GitHub Pages: https://dh-kim-hug.github.io/popup-atlas/).
#   tools/web/deploy_pages.sh
# Uses a throwaway empty orphan worktree in build/pages_wt; main is never touched. Each deploy replaces the branch with one commit
# (force push), so old builds do not pile up in the repo history.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WEB="$ROOT/build/web"
WT="$ROOT/build/pages_wt"
[ -f "$WEB/index.html" ] && [ -f "$WEB/index.pck.0" ] || { echo "run tools/web/export_web.sh first"; exit 1; }
cd "$ROOT"
if [ -d "$WT" ]; then git worktree remove --force "$WT"; fi
git branch -D gh-pages-new >/dev/null 2>&1 || true
git worktree add --orphan -b gh-pages-new "$WT" >/dev/null   # empty orphan worktree (git 2.42+)
cd "$WT"
for f in "$WEB"/index.html "$WEB"/index.js "$WEB"/index.wasm "$WEB"/index.pck.* "$WEB"/index.png "$WEB"/index.icon.png \
         "$WEB"/index.apple-touch-icon.png "$WEB"/index.audio.worklet.js "$WEB"/index.audio.position.worklet.js; do
  [ -f "$f" ] && case "$f" in *.gz) ;; *) cp "$f" . ;; esac
done
touch .nojekyll
for f in *; do s=$(stat -f %z "$f"); [ "$s" -lt 99000000 ] || { echo "$f is $s bytes (over the Pages limit)"; exit 1; }; done
git add -A
git commit -qm "web build $(git -C "$ROOT" rev-parse --short HEAD)"
git push -f origin gh-pages-new:gh-pages
cd "$ROOT"
git worktree remove --force "$WT"
git branch -D gh-pages-new >/dev/null 2>&1 || true
echo "deployed: https://dh-kim-hug.github.io/popup-atlas/ (Pages takes about a minute to update)"
