import os, re
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)

p = os.path.join(G, 'shaders/arena_ground.gdshader')
s = open(p, encoding='utf-8').read()
start = s.index('// Burnt ground splits into plates:')
end = s.index('vec2 g_uv(')
s = s[:start] + '''// Burnt ground splits into plates: the distance to the nearest plate's border
// (half the gap between the nearest two cells' points, never below nothing:
// the exact border's search went wrong under the warp and filled whole plates
// as border, which lit as flat orange blobs), and that plate's own hash.
vec3 plates(vec2 x) {
	vec2 n = floor(x), f = fract(x);
	float d1 = 8.0, d2 = 8.0;
	vec2 id = n;
	for (int j = -1; j <= 1; j++)
		for (int i = -1; i <= 1; i++) {
			vec2 g = vec2(float(i), float(j));
			vec2 r = g + hash2(n + g) - f;
			float d = length(r);
			if (d < d1) { d2 = d1; d1 = d; id = n + g; }
			else if (d < d2) d2 = d;
		}
	return vec3((d2 - d1) * 0.5, hash2(id));
}

''' + s[end:]
s = s.replace('uniform int ember_dbg = 0;\nfloat D(int k) { return ember_dbg == 0 || ember_dbg == k ? 1.0 : 0.0; }\n\n', '')
s = s.replace(' * D(1)', '').replace(' * D(2)', '').replace(' * D(3)', '').replace(' * D(4)', '').replace(' * D(5)', '')
s = s.replace('		if (ember_dbg == 6) glow += vec3(step(pl.x, 0.0) * 2.0, clamp(px * 40.0, 0.0, 1.0) * 2.0, clamp(pl.x, 0.0, 1.0) * 2.0);\n', '')
assert 'ember_dbg' not in s and 'D(' not in s
open(p, 'w', encoding='utf-8').write(s)
rep('src/World/ArenaGround.cs', [('        if (System.Environment.GetEnvironmentVariable("ARENA_DEBUG") is string dbg && dbg.StartsWith("g")) mat.SetShaderParameter("ember_dbg", int.Parse(dbg[1..]));\n', '')])
print('ok')
