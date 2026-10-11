import json,sys,os
aid,out=sys.argv[1],sys.argv[2]
p=os.path.expanduser(f'~/.claude/projects/C--Users-munch-Desktop-survivorsunchained/181eef02-779f-45de-b419-31a949a4d27e/subagents/agent-{aid}.jsonl')
last=None
for line in open(p,encoding='utf-8'):
    try: d=json.loads(line)
    except: continue
    m=d.get('message') or {}
    if m.get('role')=='assistant' and isinstance(m.get('content'),list):
        txt=''.join(c.get('text','') for c in m['content'] if isinstance(c,dict) and c.get('type')=='text')
        if txt.strip(): last=txt
os.makedirs(os.path.dirname(out),exist_ok=True)
open(out,'w',encoding='utf-8').write(last)
print(len(last), last[:60])
