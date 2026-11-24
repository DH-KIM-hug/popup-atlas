#!/bin/sh
# Refuse to start a recording without room: a full 1200x900 run writes ~1-6 GB of AVI, and a full disk ruins the
# run silently (corrupt AVI, log lines lost). tools/story/need_disk.sh [GB, default 10]
NEED="${1:-10}"
FREE=$(df -g "$(cd "$(dirname "$0")" && pwd)" | awk 'NR==2 {print $4}')
if [ "$FREE" -lt "$NEED" ]; then echo "NEED_DISK: only ${FREE} GB free, need ${NEED} GB"; exit 3; fi
