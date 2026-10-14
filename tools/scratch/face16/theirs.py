import sys,re
for p in sys.argv[1:]:
    s=open(p,encoding='utf-8',newline='').read()
    out=[];mode=0
    for line in s.splitlines(keepends=True):
        if line.startswith('<<<<<<< '): mode=1; continue
        if mode==1 and line.startswith('======='): mode=2; continue
        if mode==2 and line.startswith('>>>>>>> '): mode=0; continue
        if mode==1: continue
        out.append(line)
    open(p,'w',encoding='utf-8',newline='').write(''.join(out))
