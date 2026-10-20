#!/bin/bash
# kp2.sh CLIP TAG JSON: variant; f7 flat/edge/haft-dir and the biggest frame-to-frame haft turn f4-f16 (deg, frame)
cd "$(dirname "$0")"
python x5.py "$1" "$2" "$3" >/dev/null 2>&1 || { echo FAIL $2; exit 1; }
python ../solver_atk/atkm.py $1 --folder x/$2 --play idle_reaver --frames 4-16 | tail -13 | python -c "
import sys,re,numpy as np
rows=[l for l in sys.stdin]
d=[];fl=[];ev=[]
for l in rows:
    m=re.findall(r'\[([^\]]*)\]',l); v=np.array(m[3].split(),float); d.append(v/np.linalg.norm(v))
    rest=l.split(']')[4].split(); fl.append(float(rest[0])); ev.append(float(rest[2]))
j=[np.degrees(np.arccos(np.clip(d[i]@d[i+1],-1,1))) for i in range(len(d)-1)]
k=int(np.argmax(j[2:]))+2
print('$2', 'f7 flat %.2f edge %.2f dir %s haft %.0f | f5-10 flat %s | jump %.0f at f%d'%(fl[3],ev[3],np.round(d[3],2),-np.degrees(np.arcsin(d[3][1])),' '.join('%.2f'%x for x in fl[1:7]),j[k],k+4))
"
