#!/bin/bash
# Launch round-2 sheets in parallel queues of 2 (run from repo root).
cd /Users/house_of_4k2b/orca/popup-atlas
ids=($(python3 -c "import json;print(' '.join(j['id'] for j in json.load(open('tools/art/jobs_cards_r2.json'))))"))
n=${#ids[@]}; q=0
for ((i=0;i<n;i+=2)); do q=$((q+1)); python3 tools/run_jobs.py tools/art/jobs_cards_r2.json ${ids[@]:i:2} > tools/art/logs/r2q$q.log 2>&1 & done
wait
tail -n 2 tools/art/logs/r2q*.log
