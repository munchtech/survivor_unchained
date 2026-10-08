import json,glob,os,time
roots=[os.path.expanduser('~/.claude/projects/C--Users-munch-Desktop-survivorsunchained'),os.path.expanduser('~/.claude/projects/C--Users-munch-Desktop-wowsurvivors')]
since=time.time()-8*86400
imgread=0; cr_hi=0; cr_all=0; cr_mid=0; coord=0; agents=0
for r in roots:
  for f in glob.glob(r+'/**/*.jsonl',recursive=True):
    if os.path.getmtime(f)<since: continue
    seen=set(); imgs=0
    for line in open(f,encoding='utf-8',errors='ignore'):
        try: d=json.loads(line)
        except: continue
        m=d.get('message') or {}
        if isinstance(m.get('content'),list):
            for x in m['content']:
                if isinstance(x,dict) and x.get('type')=='tool_result' and isinstance(x.get('content'),list):
                    imgs+=sum(1 for y in x['content'] if isinstance(y,dict) and y.get('type')=='image')
        u=m.get('usage'); mid=m.get('id')
        if not u or mid in seen: continue
        seen.add(mid)
        b=u.get('cache_read_input_tokens',0); ctx=b+u.get('input_tokens',0)+u.get('cache_creation_input_tokens',0)
        imgread+=min(imgs,100)*1600; cr_all+=b
        if ctx>300000: cr_hi+=b
        elif ctx>150000: cr_mid+=b
        if 'agent-' in f: agents+=b
        else: coord+=b
print(f"cache reads: total {cr_all/1e9:.1f}B; at ctx>300k {100*cr_hi/cr_all:.0f}%; 150-300k {100*cr_mid/cr_all:.0f}%")
print(f"main sessions {100*coord/cr_all:.0f}% vs subagents {100*agents/cr_all:.0f}% of cache reads")
print(f"images re-read ~{imgread/1e9:.2f}B tokens = {100*imgread/cr_all:.0f}% of cache reads (assumes 1.6k/image, <=100 kept)")
