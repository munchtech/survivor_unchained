import glob, os
D = os.path.dirname(os.path.abspath(__file__))
pairs = [(b'agent-a6007bf07fd45ab0d', b'agent-a2f7b0f1283f6144a'), (b'scratchpad\\face5', b'scratchpad\\face6'),
         (b'scratchpad/face5', b'scratchpad/face6')]
for p in glob.glob(os.path.join(D, '*.ps1')) + glob.glob(os.path.join(D, '*.py')):
    if os.path.basename(p) in ('repoint.py', 'dirdiff.py', 'crcheck.py'): continue
    b = open(p, 'rb').read(); a = b
    for x, y in pairs: a = a.replace(x, y)
    if a != b:
        open(p, 'wb').write(a); print('repointed', os.path.basename(p))
left = [os.path.basename(p) for p in glob.glob(os.path.join(D, '*.p*')) if b'a6007bf07fd45ab0d' in open(p, 'rb').read() and 'repoint' not in p and 'dirdiff' not in p and 'crcheck' not in p]
print('still old:', left)
