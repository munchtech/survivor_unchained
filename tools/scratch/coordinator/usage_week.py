import json,glob,os,time,datetime as dt
roots=[os.path.expanduser('~/.claude/projects/C--Users-munch-Desktop-survivorsunchained'),os.path.expanduser('~/.claude/projects/C--Users-munch-Desktop-wowsurvivors')]
since=time.time()-8*86400
P={'in':4,'cr':0.20,'cw':8,'out':20}
rows=[];T={'cr':0,'cw':0,'in':0,'out':0,'req':0,'rew':0,'rewtok':0,'img':0}
first_ctx=[]; gaps=[]
for r in roots:
  for f in glob.glob(r+'/**/*.jsonl',recursive=True):
    if os.path.getmtime(f)<since: continue
    seen=set(); prev_t=None; ctxs=[]; cw_big=0; cwtok=0; c={'cr':0,'cw':0,'in':0,'out':0}; img=0
    for line in open(f,encoding='utf-8',errors='ignore'):
        try: d=json.loads(line)
        except: continue
        m=d.get('message') or {}
        if isinstance(m.get('content'),list):
            for x in m['content']:
                if isinstance(x,dict) and x.get('type')=='tool_result' and isinstance(x.get('content'),list):
                    img+=sum(1 for y in x['content'] if isinstance(y,dict) and y.get('type')=='image')
        u=m.get('usage'); mid=m.get('id')
        if not u or mid in seen: continue
        seen.add(mid)
        ts=d.get('timestamp'); t=dt.datetime.fromisoformat(ts.replace('Z','+00:00')).timestamp() if ts else None
        a=u.get('input_tokens',0); b=u.get('cache_read_input_tokens',0); w=u.get('cache_creation_input_tokens',0); o=u.get('output_tokens',0)
        ctx=a+b+w; ctxs.append(ctx)
        if w>100000 and len(ctxs)>1:
            cw_big+=1; cwtok+=w
            if prev_t and t: gaps.append(t-prev_t)
        prev_t=t
        c['cr']+=b;c['cw']+=w;c['in']+=a;c['out']+=o
    if not ctxs: continue
    cost=(c['in']*P['in']+c['cr']*P['cr']+c['cw']*P['cw']+c['out']*P['out'])/1e6
    rows.append((cost,os.path.basename(f)[:28],len(ctxs),max(ctxs),sum(ctxs)//len(ctxs),cw_big,cwtok,img))
    for k in c: T[k]+=c[k]
    T['req']+=len(ctxs); T['rew']+=cw_big; T['rewtok']+=cwtok; T['img']+=img
    if 'agent-' in f and len(ctxs)>20: first_ctx.append(ctxs[min(25,len(ctxs)-1)])
rows.sort(reverse=True)
tot=sum(r[0] for r in rows)
print(f"files {len(rows)}  requests {T['req']}  images {T['img']}  est ${tot:.0f} at Opus list price")
print(f"cache read {T['cr']/1e6:.0f}M (${T['cr']*0.2/1e6:.0f})  cache write {T['cw']/1e6:.0f}M (${T['cw']*8/1e6:.0f})  output {T['out']/1e6:.1f}M (logged)")
print(f"big rewrites (>100k written mid-run) {T['rew']}  tokens {T['rewtok']/1e6:.0f}M (${T['rewtok']*8/1e6:.0f})")
if gaps:
  gaps.sort(); n=len(gaps); print('gap before rewrite: median %.0fs, >5min %d%%, >1h %d%%'%(gaps[n//2],100*sum(g>300 for g in gaps)//n,100*sum(g>3600 for g in gaps)//n))
first_ctx.sort(); print('agent ctx at 25th request: median %dk'%(first_ctx[len(first_ctx)//2]//1000), 'n',len(first_ctx))
print('top 12:')
for r in rows[:12]: print(f"  ${r[0]:6.1f} {r[1]} reqs {r[2]} max {r[3]//1000}k avg {r[4]//1000}k rewrites {r[5]} imgs {r[7]}")
