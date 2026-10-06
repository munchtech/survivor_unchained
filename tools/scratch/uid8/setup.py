import os
S = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(os.path.dirname(S), 'uid7')
for f in ['shot.ps1', 'crop.py', 'review.py', 'sub.py', 'sheet.py', 'grid.py', 'fortune.json', 'b8.ps1']:
    t = open(os.path.join(src, f), encoding='utf-8-sig', newline='').read()
    t = t.replace('agent-a565196002a51af40', 'agent-aa1f430bd64b8d1ce').replace('scratchpad\\uid7', 'scratchpad\\uid8')
    enc = 'utf-8-sig' if f.endswith('.ps1') else 'utf-8'
    open(os.path.join(S, f), 'w', encoding=enc, newline='').write(t)
    print(f)
