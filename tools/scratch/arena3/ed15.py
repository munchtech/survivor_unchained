import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)
rep('shaders/canopy.gdshader', [
('	float leaf = step(1.0 - cover, crowns + 0.08) * (1.0 - step(0.5, open));',
 '''	// (The noise's sum sits about a half, spread narrowly: cover is mapped onto that spread.)
	float leaf = step(0.62 - cover * 0.24, crowns) * (1.0 - step(0.5, open));'''),
])
rep('src/World/ArenaEdge.cs', [
('            CastShadow = GeometryInstance3D.ShadowCastingSetting.ShadowsOnly,\n        };\n    }',
 '            CastShadow = System.Environment.GetEnvironmentVariable("ARENA_DEBUG") == "canopy" ? GeometryInstance3D.ShadowCastingSetting.On : GeometryInstance3D.ShadowCastingSetting.ShadowsOnly,\n        };\n    }'),
])
print('ok')
