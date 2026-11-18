import sys, json
t = sys.stdin.read(); i = t.index('{'); d = json.loads(t[i:t.rindex('}') + 1])
print("build_ms", round(d.get("build_ms", 0)), json.dumps(d.get("variants")))
