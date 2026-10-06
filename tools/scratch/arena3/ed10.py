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
('	float wr = smoothstep(0.32, 0.52, slope + (nM.b - 0.5) * 0.15);',
 '''	float wr = smoothstep(0.32, 0.52, slope + (nM.b - 0.5) * 0.15);
	// (A place's second ground can keep its own face on a slope: the Dig's spoil tips are
	// black rock all the way up, never the cut walls' clay.)
	wr *= 1.0 - face_skip_b * smoothstep(0.35, 0.7, s2.a);'''),
('uniform float relief = 1.0;', 'uniform float relief = 1.0;\nuniform float face_skip_b = 0.0;'),
])
rep('src/World/ArenaGround.cs', [
('        mat.SetShaderParameter("lip_glow", z.Story ? 0.3f : 1f);',
 '        mat.SetShaderParameter("lip_glow", z.Story ? 0.3f : 1f);\n        mat.SetShaderParameter("face_skip_b", place.Id == "dig" ? 1f : 0f);'),
])
rep('src/World/Pieces.Arena.cs', [
('            "deadfall" => Deadfall(seed),',
 '            "deadfall" => Deadfall(seed),\n            "timber" => Timber(seed),\n            "winch" => Winch(),'),
('''    /// <summary>A deadfall: a dead tree come down years ago''',
'''    /// <summary>The Dig's timber, stacked where it was unloaded: squared props and sleepers in
    /// courses laid crosswise, a few askew, one leaning against the stack. Knee to waist high;
    /// from above, the crosshatch of pale sawn ends and dark sides reads as worked wood.</summary>
    static Node3D Timber(int seed)
    {
        var wood = new Build();
        var rng = new RandomNumberGenerator { Seed = (ulong)(seed * 977 + 5) };
        int courses = 3 + (int)(rng.Randf() * 3);
        float y = 0;
        for (int c = 0; c < courses; c++)
        {
            bool across = c % 2 == 1;
            int n = 4 - (c > 2 ? 1 : 0);
            for (int k = 0; k < n; k++)
            {
                float o = (k - (n - 1) / 2f) * 0.3f + (rng.Randf() - 0.5f) * 0.05f;
                float len = 2.2f + 0.4f * rng.Randf(), skew = (rng.Randf() - 0.5f) * 0.12f;
                var a = across ? new Vector3(o, y + 0.1f, -len / 2) : new Vector3(-len / 2, y + 0.1f, o);
                var b = across ? new Vector3(o + skew, y + 0.1f, len / 2) : new Vector3(len / 2, y + 0.1f, o + skew);
                Beam(wood, a, b, 0.22f, 0.18f);
            }
            y += 0.19f;
        }
        // One prop leant against the stack.
        Beam(wood, new Vector3(1.6f, 0.02f, 0.4f), new Vector3(0.7f, y + 0.1f, 0.2f), 0.2f);
        return Hold((wood.Mesh(true), Surface("rough_wood", 1.0f, "#8a7a64")));
    }

    /// <summary>A windlass at the pit's lip: two A-frame trestles, a drum between them wound with
    /// rope, an iron crank. It stands on the lip with the rope going down; under 2 m.
    /// Its axle along X; origin at its middle on the ground.</summary>
    static Node3D Winch()
    {
        var wood = new Build();
        var iron = new Build();
        var rope = new Build();
        foreach (float sx in new[] { -1.1f, 1.1f })
        {
            Beam(wood, new Vector3(sx, 0, -0.7f), new Vector3(sx, 1.25f, 0), 0.16f);
            Beam(wood, new Vector3(sx, 0, 0.7f), new Vector3(sx, 1.25f, 0), 0.16f);
            Beam(wood, new Vector3(sx, 0.45f, -0.48f), new Vector3(sx, 0.45f, 0.48f), 0.1f);
        }
        Tube(iron, new List<Vector3> { new(-1.35f, 1.2f, 0), new(1.35f, 1.2f, 0) }, 0.05f, 6);
        Lathe(wood, Pts(0.26f, -0.85f, 0.3f, -0.8f, 0.3f, 0.8f, 0.26f, 0.85f), 14, new Transform3D(new Basis(Vector3.Back, Mathf.Pi / 2), new Vector3(0, 1.2f, 0)));
        // The rope wound on the drum, and paid out over its front.
        for (int k = 0; k < 9; k++)
        {
            float x = -0.7f + k * 0.175f;
            Tube(rope, Path(16, t => new Vector3(x, 1.2f + 0.31f * Mathf.Sin(t * Mathf.Tau), 0.31f * Mathf.Cos(t * Mathf.Tau)), true), 0.025f, 4, true);
        }
        Tube(rope, new List<Vector3> { new(0.2f, 1.2f, 0.32f), new(0.25f, 0.2f, 1.6f), new(0.25f, -2.5f, 2.2f) }, 0.025f, 4);
        // The crank.
        Tube(iron, new List<Vector3> { new(1.35f, 1.2f, 0), new(1.35f, 1.55f, 0.15f), new(1.6f, 1.55f, 0.15f) }, 0.035f, 5);
        return Hold((wood.Mesh(true), Surface("rough_wood", 0.9f, "#7a6a56")), (iron.Mesh(), Wrought()), (rope.Mesh(), Mat("#8a7a5a", 0, 0.9f)));
    }

    /// <summary>A deadfall: a dead tree come down years ago'''),
])
rep('logic/Maps/Arenas/Dig.cs', [
('''        // ---------------------------------------------------------- the rails --''',
'''        // A windlass at the lip, the way down for what the cage won't carry; a fence of
        // stakes along the lip either side of the headframe's feet.
        var (wx, wz) = (pitX + Math.Sin(face) * (PitR + 1.4) + ux * 4.2, pitZ + Math.Cos(face) * (PitR + 1.4) + uz * 4.2);
        if (B.CanStand(wx, wz)) { B.Piece("arena/winch", wx, wz, face + Math.PI); B.Block(wx, wz, 1.0); }
        for (int k = -6; k <= 6; k++)
        {
            if (Math.Abs(k) < 2) continue;
            double a = face + k * 0.16;
            double fx1 = pitX + Math.Sin(a) * (PitR + 0.6), fz1 = pitZ + Math.Cos(a) * (PitR + 0.6);
            if (!B.CanStand(fx1, fz1)) continue;
            B.Piece("village/Prop_WoodenFence_Single", fx1, fz1, a + Math.PI / 2, 1.0);
        }

        // ---------------------------------------------------------- the rails --'''),
('''        // Lamps along the rails.''',
'''        // Timber stacked by the rails where it was unloaded, sleepers and props for the workings.
        for (int k = 14; k < rails.Length - 8; k += 19)
        {
            var (x, z, hw) = rails[k];
            var (nx, nz, _) = rails[k + 1];
            double dx = nx - x, dz = nz - z, len = Math.Sqrt(dx * dx + dz * dz);
            int side = (k / 19) % 2 == 0 ? 1 : -1;
            double px = x - dz / len * side * (hw + 2.2), pz = z + dx / len * side * (hw + 2.2);
            if (!B.Free(px, pz, 1.6)) continue;
            B.Piece("arena/timber", px, pz, Math.Atan2(dx, dz) + Rng.Range(-0.2, 0.2));
            B.Slab(px, pz, 1.2, 0.7, Math.Atan2(dx, dz));
            B.Take(px, pz, 2);
        }
        // Lamps along the rails.'''),
])
print('ok')
