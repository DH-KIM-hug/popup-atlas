#!/usr/bin/env python3
"""Score a critic's blind picks against the key.
usage: score_ab.py NAME PICKS_JSON   PICKS_JSON = {"pair_01": "X", ...}  (the label the critic judged BETTER)
Prints reference_pick_rate = fraction of pairs where the critic preferred the reference (lower is better for us)."""
import json, sys
name, picks = sys.argv[1], json.loads(sys.argv[2])
key = json.load(open(f'artifacts/ab_keys/{name}.json'))
n = len(key); ref_better = sum(1 for k, ref in key.items() if picks.get(k) == ref)
print(json.dumps({'name': name, 'pairs': n, 'reference_preferred': ref_better, 'reference_pick_rate': round(ref_better / max(1, n), 2)}))
