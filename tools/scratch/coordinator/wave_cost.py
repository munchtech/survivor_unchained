import json,glob,os,sys
from datetime import datetime
P={'in':4,'cr':0.20,'cw':8,'out':20}  # usage_week.py's Opus list price per M
base=os.path.expanduser('~/.claude/projects/C--Users-munch-Desktop-survivorsunchained/')
for sess in sys.argv[1:]:
    print('=== session',sess[:8])
    rows=[]
    for f in glob.glob(base+sess+'/subagents/*.jsonl'):
        aid=os.path.basename(f)[6:-6]
        try: meta=json.load(open(f[:-6]+'.meta.json'))
        except: meta={}
        c={'in':0,'cr':0,'cw':0,'out':0}; seen=set(); ts=[]; models=set(); maxctx=0
        for line in open(f,encoding='utf-8'):
            try: d=json.loads(line)
            except: continue
            if d.get('timestamp'): ts.append(d['timestamp'])
            m=d.get('message') or {}
            u=m.get('usage'); mid=m.get('id')
            if not u or mid in seen: continue
            seen.add(mid); models.add(m.get('model','?'))
            c['in']+=u.get('input_tokens',0); c['cr']+=u.get('cache_read_input_tokens',0); c['cw']+=u.get('cache_creation_input_tokens',0); c['out']+=u.get('output_tokens',0)
            maxctx=max(maxctx,u.get('input_tokens',0)+u.get('cache_read_input_tokens',0)+u.get('cache_creation_input_tokens',0))
        cost=sum(c[k]*P[k] for k in P)/1e6
        t0=min(ts)[:16] if ts else '';t1=max(ts)[11:16] if ts else ''
        rows.append((meta.get('agentType','?'),meta.get('description','')[:34],t0,t1,maxctx//1000,c['out']//1000,cost,','.join(sorted(x.replace('claude-','') for x in models))))
    rows.sort(key=lambda r:r[2])
    tot={}
    for r in rows:
        print(f"{r[0]:15} {r[1]:34} {r[2]}-{r[3]} ctx{r[4]:4}k out{r[5]:4}k ${r[6]:6.1f} {r[7]}")
        tot.setdefault(r[0],[0,0]); tot[r[0]][0]+=1; tot[r[0]][1]+=r[6]
    print('by type:',{k:(v[0],round(v[1])) for k,v in tot.items()},'total $',round(sum(r[6] for r in rows)))
