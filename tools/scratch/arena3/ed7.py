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
('	n = normalize(mix(n, n_geo, pool * 0.92));', '	// Standing water lies level, whatever the ground under it does (a level face holds the\n	// moon in one place; a tilted one slides a white streak down the bank).\n	n = normalize(mix(n, vec3(0.0, 1.0, 0.0), pool * 0.92));'),
])
rep('src/World/ArenaGround.cs', [
('["hollow"] = (new Color("#304620"), 0.3f, 1.6f),', '["hollow"] = (new Color("#304620"), 0.16f, 1.6f),'),
])
print('ok')
