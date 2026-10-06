import os, sys
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)
if sys.argv[1] == 'on':
    rep('shaders/arena_ground.gdshader', [
    ('		glow += (white * line * 2.4 * lip_glow * lip_glow + ember * (halo * 0.5 * lip_glow + vein * 0.9 + spark * 1.4 * flick)) * breathe * ember_glow;',
     '		glow += (white * line * 2.4 * lip_glow * lip_glow * D(1) + ember * (halo * 0.5 * lip_glow * D(2) + vein * 0.9 * D(3) + spark * 1.4 * flick * D(4))) * breathe * ember_glow;'),
    ('	glow += ember * hot * (0.5 + 0.8 * crack) * breathe * ember_glow;', '	glow += ember * hot * (0.5 + 0.8 * crack) * breathe * ember_glow * D(5);'),
    ('vec2 hash2(vec2 p) {', 'uniform int ember_dbg = 0;\nfloat D(int k) { return ember_dbg == 0 || ember_dbg == k ? 1.0 : 0.0; }\n\nvec2 hash2(vec2 p) {'),
    ])
    rep('src/World/ArenaGround.cs', [('if (System.Environment.GetEnvironmentVariable("ARENA_DEBUG") == "noglow") mat.SetShaderParameter("ember_glow", 0f);',
     'if (System.Environment.GetEnvironmentVariable("ARENA_DEBUG") is string dbg && dbg.StartsWith("g")) mat.SetShaderParameter("ember_dbg", int.Parse(dbg[1..]));')])
print('ok')
