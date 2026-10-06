import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)

rep('src/World/ArenaGround.cs', [
('''        ["hollow"] = [new(0.08f, 1.0f, Lift: 0.02f), new(0.045f, 0.85f), new(0.065f, 0.8f, Lift: 0.03f, Bump: 0.1f), new(0.026f, 0.8f, Lift: -0.03f),
            new(0.1f, 0.6f, Lift: -0.05f, Bump: 0.08f), new(0.085f, 0.9f, Lift: 0.01f), new(0.07f, 0.7f)],''',
'''        // (Leaves drawn half again as large as the scan's: a leaf must be a few pixels to read
        // as one from the arena camera, or the litter reads as gravel.)
        ["hollow"] = [new(0.11f, 1.0f, Con: 1.4f, Lift: 0.02f, Size: 1.7f), new(0.06f, 0.9f, Con: 1.35f, Size: 1.5f), new(0.075f, 0.8f, Lift: 0.03f, Bump: 0.1f, Size: 1.3f),
            new(0.03f, 0.8f, Lift: -0.03f), new(0.1f, 0.6f, Lift: -0.05f, Bump: 0.08f), new(0.1f, 0.9f, Con: 1.35f, Lift: 0.01f, Size: 1.4f), new(0.07f, 0.7f)],'''),
('["hollow"] = (new Color("#304620"), 0.55f, 1.6f),', '["hollow"] = (new Color("#304620"), 0.4f, 1.6f),'),
])
rep('shaders/arena_ground.gdshader', [
('''	float thr = smoothstep(0.48, 0.72, swirl) * (0.6 + 0.4 * texture(noise_tex, w * 0.41 + vec2(-TIME * 0.01, TIME * 0.007)).g);''',
'''	float rn = texture(noise_tex, w * 0.23 + vec2(TIME * 0.008, -TIME * 0.011) + swirl * 0.35).r;
	float thr = pow(1.0 - abs(rn * 2.0 - 1.0), 7.0) * (0.5 + 0.5 * smoothstep(0.35, 0.7, swirl));'''),
('glow += slurry * slurry_glow * s3.g * smoothstep(0.1, 0.6, wet) * (0.1 + 1.3 * thr) * (1.0 - charred);',
 'glow += slurry * slurry_glow * s3.g * smoothstep(0.1, 0.6, wet) * (0.06 + 1.6 * thr) * (1.0 - charred);'),
])
rep('logic/Maps/Arenas/HollowNight.cs', [
('''        double keep = d < 6 ? 0 : d < 14 ? 0.2 : d < 30 ? 0.34 : 0.15;
        if (Rng.Chance(keep)) B.Put(Rng.Pick(new[] { "pine", "broadleaf", "pine", "dead", "broadleaf" }), x, z, 0.9 + Math.Min(0.6, d * 0.02));
        if (d < 9 && Rng.Chance(0.4)) B.Put(Rng.Pick(new[] { "scan_fern", "scan_fern", "scan_shrub", "fern", "bramble" }), x + Rng.Range(-1, 1), z + Rng.Range(-1, 1), Rng.Range(0.9, 1.4));''',
'''        // Bare trees read from above as tangles over the fight; the crowns stand back.
        double keep = d < 11 ? 0 : d < 18 ? 0.22 : d < 32 ? 0.34 : 0.15;
        if (Rng.Chance(keep)) B.Put(Rng.Pick(new[] { "pine", "broadleaf", "pine", "broadleaf" }), x, z, 0.9 + Math.Min(0.6, d * 0.02));
        if (d < 11 && Rng.Chance(0.5)) B.Put(Rng.Pick(new[] { "scan_fern", "scan_fern", "scan_shrub", "fern", "bramble", "scan_shrub" }), x + Rng.Range(-1, 1), z + Rng.Range(-1, 1), Rng.Range(1.0, 1.6));'''),
])
print('ok')
