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
('''		coal = mix(coal, vec3(0.062, 0.06, 0.057) * grain, ash * 0.75);''',
'''		// Ash: grey, broken by the ground's own grain and the plates' seams, never a flat
		// sheet (under the ring's red lights a flat pale drift reads as orange paint).
		float abreak = smoothstep(0.3, 0.7, nF.r * 0.6 + pl.y * 0.4);
		coal = mix(coal, vec3(0.045, 0.044, 0.042) * grain * (0.6 + 0.5 * abreak), ash * 0.6);'''),
('''	glow += slurry * slurry_glow * s3.g * smoothstep(0.1, 0.6, wet) * (0.06 + 1.6 * thr) * (1.0 - charred);''',
'''	glow += slurry * slurry_glow * s3.g * smoothstep(0.3, 0.8, wet) * (0.05 + 1.4 * thr) * (1.0 - charred);'''),
('''	float thr = pow(1.0 - abs(rn * 2.0 - 1.0), 7.0) * (0.5 + 0.5 * smoothstep(0.35, 0.7, swirl));''',
'''	float thr = pow(1.0 - abs(rn * 2.0 - 1.0), 10.0) * (0.35 + 0.65 * smoothstep(0.4, 0.7, swirl));'''),
])
rep('logic/Maps/ArenaGen.cs', [
('''            if (Outline != null)
            {
                // Along a story place's own edge, one every ten metres or so, just inside it.
                var rim = Rim();
                for (int k = 0; k < rim.Count; k += 7)
                {
                    var (x, z, nx, nz) = rim[k];
                    double lx = x - nx * 1.5, lz = z - nz * 1.5;
                    Lights.Add(new LightDef { X = lx, Y = HeightAt(lx, lz) + 0.7, Z = lz, Color = Place.Air.Ember, Intensity = 3.0, Distance = 8, Flicker = 0.35, On = true });
                }
                return;
            }''',
'''            // A story place's edge is its banks, its lip burning low: no lights of the ring's
            // (their red on its char read as pools of paint along every bank).
            if (Outline != null) return;'''),
])
rep('src/World/ArenaGround.cs', [
('["hollow"] = (new Color("#304620"), 0.4f, 1.6f),', '["hollow"] = (new Color("#304620"), 0.3f, 1.6f),'),
])
print('ok')
