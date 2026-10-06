import glob, os
D = os.path.dirname(os.path.abspath(__file__))
pairs = [(b'agent-a2f7b0f1283f6144a', b'agent-a7905c3e498df9528'), (b'scratchpad\\face6', b'scratchpad\\face7'),
         (b'scratchpad/face6', b'scratchpad/face7')]
SKIP = ('repoint.py', 'dirdiff.py', 'crcheck.py')
for p in glob.glob(os.path.join(D, '*.ps1')) + glob.glob(os.path.join(D, '*.py')):
    if os.path.basename(p) in SKIP: continue
    b = open(p, 'rb').read(); a = b
    for x, y in pairs: a = a.replace(x, y)
    if a != b:
        open(p, 'wb').write(a); print('repointed', os.path.basename(p))
left = []
for p in glob.glob(os.path.join(D, '*.p*')):
    if os.path.basename(p) in SKIP: continue
    b = open(p, 'rb').read()
    if b'a2f7b0f1283f6144a' in b or b'face6' in b or b'a6007bf07fd45ab0d' in b or b'face5' in b:
        left.append(os.path.basename(p))
print('still old:', left)
