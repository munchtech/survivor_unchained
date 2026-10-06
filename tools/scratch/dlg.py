import json,sys
sys.stdout.reconfigure(encoding='utf-8')
ROOT=r'C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a26f4d6a900ab8201/godot/data/content/'
d=json.load(open(ROOT+'dialogue.json',encoding='utf-8'))
W=int(sys.argv[2]) if len(sys.argv)>2 else 90
def c(x):
    if x is None: return ''
    if isinstance(x,dict):
        if 'all' in x: return 'ALL('+', '.join(c(y) for y in x['all'])+')'
        if 'any' in x: return 'ANY('+', '.join(c(y) for y in x['any'])+')'
        if 'not' in x: return '!'+c(x['not'])
        if 'fact' in x:
            r={k:v for k,v in x.items() if k!='fact'}
            return f"{x['fact']}{r}"
        if 'quest' in x:
            q=x['quest']; return f"Q:{q['id']}/{q.get('entry','')}{'['+q['status']+']' if 'status' in q else ''}"
        return json.dumps(x,separators=(',',':'))
    return str(x)
def e(x):
    if not x: return ''
    if isinstance(x,dict): x=[x]
    out=[]
    for y in x:
        if 'if' in y: out.append(f"IF {c(y['if'])} THEN [{e(y.get('then'))}] ELSE [{e(y.get('else'))}]")
        elif 'quest' in y: q=y['quest']; out.append(f"+Q:{q['id']}/{q.get('entry','')}{'['+q['status']+']' if 'status' in q else ''}{' out='+q['outcome'] if 'outcome' in q else ''}")
        elif 'set' in y: out.append('set'+json.dumps(y['set'],separators=(',',':')))
        elif 'history' in y: out.append('hist:'+y['history']['id'])
        elif 'rel' in y: out.append('rel:'+y['rel']['npc'])
        else: out.append(json.dumps(y,separators=(',',':'))[:80])
    return '; '.join(out)
def t(x):
    if isinstance(x,str): return [('',x)]
    return [(c(v.get('when'))+(' ADD' if v.get('add') else ''),v['text']) for v in x]
cv=d[sys.argv[1]]
only=sys.argv[3].split(',') if len(sys.argv)>3 else None
print('ENTRY:')
for en in cv['entry']: print('  ',c(en.get('when')),'->',en['node'])
for m in cv.get('marker',[]) or []: print('  MARK',m.get('mark'),c(m.get('when')))
for nid,n in cv['nodes'].items():
    if only and nid not in only: continue
    print(f"== {nid}" + (f" [speaker {n['speaker']}]" if 'speaker' in n else '') + (f" next->{n['next']}" if 'next' in n else ''))
    for w,tx in t(n['text']): print(f"   T{' <'+w+'>' if w else ''}: {tx[:W]}")
    if n.get('effects'): print('   FX:',e(n['effects']))
    for ch in n.get('choices',[]) or []:
        tx=t(ch['text'])
        s=f"   * {tx[0][1][:60]}"
        if ch.get('show'): s+=f"  SHOW {c(ch['show'])}"
        if ch.get('when'): s+=f"  WHEN {c(ch['when'])}"
        if ch.get('locked'): s+=f"  LOCK '{ch['locked']}'"
        if ch.get('once'): s+=f"  ONCE {ch['once']}"
        if ch.get('action'): s+=f"  ACT {ch['action']}"
        if ch.get('goto'): s+=f"  -> {ch['goto']}"
        if ch.get('end'): s+="  END"
        print(s)
        if ch.get('effects'): print('       FX:',e(ch['effects']))
