#!/bin/sh
# Delete a raw movie-maker AVI for good once its mp4 is verified (user 2026-11-25: "휴지통에 넣지말고 완전 삭제").
# Moving AVIs to ~/.Trash kept them on the same disk and filled it (ENOSPC, 2026-11-24).
#   tools/story/drop_avi.sh /ABS/x.avi /ABS/x.mp4
# Verified = the mp4 decodes and lasts at least 90 % of the AVI. Otherwise the AVI is kept and the script says so.
AVI="$1"; MP4="$2"
[ -n "$AVI" ] && [ -f "$AVI" ] || exit 0
case "$AVI" in *.avi) ;; *) echo "drop_avi: not an .avi: $AVI"; exit 2;; esac
dur() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$1" 2>/dev/null; }
A=$(dur "$AVI"); M=$(dur "$MP4")
if [ -n "$M" ] && python3 -c "import sys; a=float('${A:-0}' or 0); m=float('$M'); sys.exit(0 if m > 0 and m >= 0.9*a else 1)"; then
  rm -f -- "$AVI"
else
  echo "drop_avi: KEPT $AVI (mp4 ${M:-missing}s vs avi ${A:-?}s): check the encode, then delete it"
fi
