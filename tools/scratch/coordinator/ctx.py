# Context size of agents by id, from their transcripts (reads only the tail).
#   python tools/scratch/coordinator/ctx.py <agent-id> [...]
# Transcripts live under ~/.claude/projects/<project>/<session>/subagents/agent-<id>.jsonl,
# in whichever session spawned the agent, so every session folder is searched.
import glob
import json
import os
import sys

ROOT = os.path.expanduser(r"~/.claude/projects")
for i in sys.argv[1:]:
    hits = glob.glob(os.path.join(ROOT, "*", "*", "subagents", f"agent-{i}.jsonl"))
    if not hits:
        print(i, "no transcript")
        continue
    f = max(hits, key=os.path.getmtime)
    size = os.path.getsize(f)
    with open(f, "rb") as fh:
        fh.seek(max(0, size - 2000000))
        tail = fh.read().decode("utf-8", "replace").splitlines()
    for line in reversed(tail):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        m = d.get("message")
        if isinstance(m, dict) and m.get("usage"):
            u = m["usage"]
            print(i, u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0))
            break
    else:
        print(i, "no usage yet")
