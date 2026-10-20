import subprocess, numpy as np, re, sys
b = np.array(eval(sys.argv[1]), float); b /= np.linalg.norm(b)
v = sys.argv[2]
angs = [int(x) for x in sys.argv[3].split(',')]
u = np.cross(b, [0, 0, 1.0]); u /= np.linalg.norm(u); w = np.cross(b, u)
for ang in angs:
    a = np.radians(ang); k = np.cos(a) * u + np.sin(a) * w
    s = open('p_flick.py').read()
    s = re.sub(r'^F0R = .*$', f'F0R = dict(v={v}, pole=(-0.8,-0.3,-0.4), blade=({b[0]:.3f},{b[1]:.3f},{b[2]:.3f}), kn=({k[0]:.3f},{k[1]:.3f},{k[2]:.3f}))', s, count=1, flags=re.M)
    open('p_flick.py', 'w').write(s)
    subprocess.run(['python', 'drive.py', 'actions', 'cast_flick', 'out_f1', 'p_flick.py'], capture_output=True)
    o = subprocess.run(['python', '../solver_atk/auditx.py', 'out_f1', 'cast_flick'], capture_output=True, text=True).stdout
    m = subprocess.run(['python', '../solver_atk/atkm.py', 'cast_flick', '--play', 'idle_arcanist', '--key', 'wand@hand_r', '--folder', 'out_f1', '--frames', '0-0'], capture_output=True, text=True).stdout.splitlines()[-1]
    g = re.search(r'r: spin (\S+) wtw (\d+) wbend (\d+) wdev (\d+) ftw (\d+)', o).groups()
    print(ang, np.round(k, 2), g, len(o.splitlines()) - 1, 'flags |', m[33:52], m[52:72], m[-34:])
