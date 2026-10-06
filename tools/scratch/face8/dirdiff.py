import os, hashlib, sys
O = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6007bf07fd45ab0d'
N = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2f7b0f1283f6144a'
def h(p):
    m = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): m.update(b)
    return m.hexdigest()
for sub in sys.argv[1:]:
    for root, dirs, files in os.walk(os.path.join(O, sub)):
        dirs[:] = [d for d in dirs if d not in ('.godot', '.shots')]
        for fn in files:
            if fn.endswith('.import'): continue
            p = os.path.join(root, fn); rel = os.path.relpath(p, O); q = os.path.join(N, rel)
            if not os.path.exists(q): print('ONLY-OLD', rel, os.path.getsize(p))
            elif os.path.getsize(p) != os.path.getsize(q) or h(p) != h(q): print('DIFF', rel, os.path.getsize(p))
