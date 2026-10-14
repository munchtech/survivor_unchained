import json,sys,os
aid,out=sys.argv[1],sys.argv[2]
import glob
hits=glob.glob(os.path.expanduser(f'~/.claude/projects/C--Users-munch-Desktop-survivorsunchained/*/subagents/**/agent-{aid}.jsonl'),recursive=True)
p=max(hits,key=os.path.getmtime)
last=None
for line in open(p,encoding='utf-8'):
    try: d=json.loads(line)
    except: continue
    m=d.get('message') or {}
    if m.get('role')=='assistant' and isinstance(m.get('content'),list):
        txt=''.join(c.get('text','') for c in m['content'] if isinstance(c,dict) and c.get('type')=='text')
        if txt.strip(): last=txt
        for c in m['content']:
            if isinstance(c,dict) and c.get('type')=='tool_use' and c.get('name')=='SendMessage':
                msg=(c.get('input') or {}).get('message')
                if isinstance(msg,str) and msg.strip(): last=msg
os.makedirs(os.path.dirname(out),exist_ok=True)
open(out,'w',encoding='utf-8').write(last)
print(len(last), last[:60])
