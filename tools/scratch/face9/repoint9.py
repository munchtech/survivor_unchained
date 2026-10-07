"""Repoint the predecessor's face8 scripts to this worktree and scratchpad (face9).
Old scratchpad outputs (face8) -> my scratchpad face9; old inputs (face4..face7) -> survivorsunchained_inputs."""
import glob, os
D = os.path.dirname(os.path.abspath(__file__))
OLD_SP = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad'
NEW_SP = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad'
INP = r'C:\Users\munch\Desktop\survivorsunchained_inputs'
pairs = [(OLD_SP + '\\face8', NEW_SP + '\\face9')]
for n in ('face4', 'face5', 'face6', 'face7'):
    pairs.append((OLD_SP + '\\' + n, INP + '\\' + n))
pairs.append((OLD_SP, NEW_SP))
fwd = [(a.replace('\\', '/'), b.replace('\\', '/')) for a, b in pairs]
pairs = pairs + fwd + [('agent-a43570e07edbe40b2', 'agent-aed215ba3ca60cc29')]
SKIP = ('repoint.py', 'repoint9.py', 'dirdiff.py', 'crcheck.py', 'predlist.py', 'predmissing.py')
changed = []
for p in glob.glob(os.path.join(D, '*.ps1')) + glob.glob(os.path.join(D, '*.py')):
    if os.path.basename(p) in SKIP:
        continue
    b = open(p, 'rb').read(); a = b
    for x, y in pairs:
        a = a.replace(x.encode(), y.encode())
    if a != b:
        open(p, 'wb').write(a); changed.append(os.path.basename(p))
print('repointed', len(changed))
left = []
for p in glob.glob(os.path.join(D, '*.p*')):
    if os.path.basename(p) in SKIP:
        continue
    b = open(p, 'rb').read()
    if b'wowsurvivors' in b or b'a43570e07edbe40b2' in b:
        left.append(os.path.basename(p))
print('still old:', left)
