import os
S = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(os.path.dirname(S), 'uid6')
for f in ['shot.ps1', 'crop.py', 'cands.py', 'review.py', 'sub.py', 'sheet.py']:
    t = open(os.path.join(src, f), encoding='utf-8-sig', newline='').read()
    t = t.replace('agent-a4fdbc49786ba8b7f', 'agent-a565196002a51af40').replace('scratchpad\\uid6', 'scratchpad\\uid7')
    enc = 'utf-8-sig' if f.endswith('.ps1') else 'utf-8'
    open(os.path.join(S, f), 'w', encoding=enc, newline='').write(t)
    print(f)
