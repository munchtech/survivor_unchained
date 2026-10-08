"""Copy the face9 and face8 scratch scripts from the repo's mirror into face10 and repoint them to this worktree and
scratchpad. face9's own outputs (old scratchpad face9) -> face10; face4..face7 inputs stay in survivorsunchained_inputs."""
import glob, os, shutil
D = os.path.dirname(os.path.abspath(__file__))
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abe65bc929823a791'
MIRROR = os.path.join(W, 'tools', 'scratch')
OLD9 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\74e72383-70c7-41d5-8e96-2fad2ed58481\scratchpad'
OLD8 = r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad'
NEW = os.path.dirname(D)
INP = r'C:\Users\munch\Desktop\survivorsunchained_inputs'
pairs = [(OLD9 + '\\face9', D), (OLD8 + '\\face8', D)]
for n in ('face4', 'face5', 'face6', 'face7'):
    pairs.append((OLD8 + '\\' + n, INP + '\\' + n))
pairs += [(OLD9, NEW), (OLD8, NEW)]
pairs = pairs + [(a.replace('\\', '/'), b.replace('\\', '/')) for a, b in pairs]
pairs += [('agent-aed215ba3ca60cc29', 'agent-abe65bc929823a791'), ('agent-a43570e07edbe40b2', 'agent-abe65bc929823a791')]
SKIP = ('repoint.py', 'repoint9.py', 'repoint10.py', 'dirdiff.py', 'crcheck.py', 'predlist.py', 'predmissing.py', 'sidecars.py')
n = 0
for sub in ('face8', 'face9'):                       # (face9's copies win where both have a script)
    for p in glob.glob(os.path.join(MIRROR, sub, '*.p*')):
        b = os.path.basename(p)
        if b in SKIP:
            continue
        a = open(p, 'rb').read()
        for x, y in pairs:
            a = a.replace(x.encode(), y.encode())
        open(os.path.join(D, b), 'wb').write(a)
        n += 1
print('copied and repointed', n)
left = [os.path.basename(p) for p in glob.glob(os.path.join(D, '*.p*'))
        if os.path.basename(p) not in SKIP and (b'wowsurvivors' in open(p, 'rb').read() or b'74e72383' in open(p, 'rb').read())]
print('still old:', left)
