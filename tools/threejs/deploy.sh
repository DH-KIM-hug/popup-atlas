#!/bin/sh
# Publish the three.js player (threejs/dist) to gh-pages/three/ -> https://dh-kim-hug.github.io/popup-atlas/three/
#   (cd threejs && npm run build) && tools/threejs/deploy.sh
# Adds ONE commit on top of the current gh-pages that only replaces three/ (no force push), so the Godot web build
# at the root stays as it is. tools/web/deploy_pages.sh (which rewrites the branch) copies three/ over on its deploys.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIST="$ROOT/threejs/dist"
WT="$ROOT/build/pages_three_wt"
[ -f "$DIST/index.html" ] && [ -f "$DIST/data/tales.json" ] || { echo "build threejs/ first (npm run build)"; exit 1; }
cd "$ROOT"
for f in $(find "$DIST" -type f); do s=$(stat -f %z "$f"); [ "$s" -lt 99000000 ] || { echo "$f is $s bytes (over the Pages limit)"; exit 1; }; done
try=0
while :; do
  git fetch -q origin gh-pages
  if [ -d "$WT" ]; then git worktree remove --force "$WT"; fi
  git worktree add -q --detach "$WT" origin/gh-pages
  cd "$WT"
  if [ -d three ]; then git rm -rq three; fi
  mkdir three
  cp -R "$DIST"/. three/
  git add -A three
  git commit -qm "three.js player $(git -C "$ROOT" rev-parse --short HEAD)" || { echo "nothing changed"; cd "$ROOT"; git worktree remove --force "$WT"; exit 0; }
  if git push -q origin HEAD:gh-pages; then break; fi
  try=$((try + 1)); [ $try -lt 3 ] || { echo "push failed 3 times"; exit 1; }
  cd "$ROOT"
done
cd "$ROOT"
git worktree remove --force "$WT"
echo "deployed: https://dh-kim-hug.github.io/popup-atlas/three/ (Pages takes about a minute to update)"
