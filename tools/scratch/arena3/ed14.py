import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)
rep('shaders/arena_ground.gdshader', [
('''		mo = smoothstep(0.45, 0.6, s3.r + (nM.g - 0.5) * 0.28 + (dome - 0.55) * 0.35 + (0.5 - hgt) * 0.12);''',
'''		// Solid where the paint is deep; toward its edge the mat breaks into separate round
		// cushions, each there or not by its own hash, so the edge is a scatter of moss and
		// never a line round a painted island.
		float inner = smoothstep(0.62, 0.82, s3.r + (nM.g - 0.5) * 0.2);
		float pres = smoothstep(-0.04, 0.08, s3.r * 1.15 + (nM.g - 0.5) * 0.25 + (0.5 - hgt) * 0.1 - hb.y * 0.6 - 0.18);
		float cushion = 1.0 - smoothstep(0.3, 0.7, db);
		mo = max(inner, pres * cushion);'''),
])
print('ok')
