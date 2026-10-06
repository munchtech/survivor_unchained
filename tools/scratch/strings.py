import re, sys
pat = re.compile(r'"((?:[^"\\\n]|\\.){%s,})"' % (sys.argv[1]))
for f in sys.argv[2:]:
    for i, l in enumerate(open(f, encoding='utf8'), 1):
        if l.strip().startswith('//') or l.strip().startswith('*'):
            continue
        for m in pat.findall(l):
            if ' ' in m:
                print(f"{f.split('/')[-1]}:{i}: {m}")
