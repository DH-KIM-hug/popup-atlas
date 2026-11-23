#!/bin/sh
# (Re)start the local static server for build/web and a Cloudflare quick tunnel to it; print the public URL.
#   tools/web/serve.sh            -> https://<random>.trycloudflare.com (works while this Mac is awake and both run)
#   tools/web/serve.sh stop       -> stop both
# PIDs go to build/web/serve_pids.txt; only those PIDs are ever stopped.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WEB="$ROOT/build/web"
PORT="${PORT:-8765}"
PIDS="$WEB/serve_pids.txt"
CF="$(command -v cloudflared || echo /opt/homebrew/bin/cloudflared)"
if [ -f "$PIDS" ]; then
  while read -r name pid; do
    [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null && kill "$pid" && echo "stopped $name $pid"
  done < "$PIDS"
  mv "$PIDS" "$HOME/.Trash/serve_pids_$(date +%Y%m%d_%H%M%S).txt"
fi
[ "$1" = "stop" ] && exit 0
[ -f "$WEB/index.html" ] || { echo "no build/web/index.html: run tools/web/export_web.sh first"; exit 1; }
nohup python3 "$ROOT/tools/web/serve.py" "$PORT" "$WEB" > "$WEB/server.log" 2>&1 &
echo "server $!" > "$PIDS"
nohup "$CF" tunnel --no-autoupdate --url "http://localhost:$PORT" > "$WEB/tunnel.log" 2>&1 &
echo "tunnel $!" >> "$PIDS"
i=0
while [ $i -lt 60 ]; do
  URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$WEB/tunnel.log" | head -1)
  [ -n "$URL" ] && break
  i=$((i + 1)); sleep 1
done
echo "local:  http://localhost:$PORT/"
echo "public: ${URL:-(no URL yet, see $WEB/tunnel.log)}"
echo "$URL" > "$WEB/public_url.txt"
cat "$PIDS"
