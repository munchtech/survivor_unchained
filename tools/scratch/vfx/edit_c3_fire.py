from ed import edit
edit(r"src\Fx\BattleFx.Story.cs", [
    ("""///   a fed fire    a story night's deadfall alight: flame standing the length of the dead tree,
///                 embers going up, its light lying on the ground out to the reach the Pack will
///                 not cross, and its flames sinking and smoking as its burning runs out (feed it);""",
     """///   a fed fire    a story night's deadfall alight: flame standing the length of the dead tree,
///                 embers going up, and its flames sinking and smoking as its burning runs out (feed
///                 it). Its reach is its own light's (a flat disc of firelight out to the reach read as
///                 an orange circle painted on the ground);"""),
    ("""    static readonly Color WayCold = new(0.32f, 0.52f, 1.0f), DeadfallRoom = new(1.0f, 0.42f, 0.1f);""",
     """    static readonly Color WayCold = new(0.32f, 0.52f, 1.0f);"""),
    ("""            // An ellipse round the tree: the length of it and a little past each end, narrow across,
            // so its flames stand along the trunk.
            float reachAlong = len / 2 + 0.55f, reachAcross = 0.55f;
            look.Mesh.Position = new Vector3(mid.X, Y(mid.X, mid.Z) - 0.05f, mid.Z);
            look.Mesh.Basis = new Godot.Basis(Vector3.Up, -turn) * Godot.Basis.FromScale(new Vector3(reachAlong, 0.6f + 1.3f * look.Burn, reachAcross));""",
     """            // The ring of cards pressed flat to a line along the trunk and a little past each end, so
            // its flames stand up out of the tree. (Half a metre across, it was a hoop of flame round
            // the log with the log lying cold inside it.)
            float reachAlong = len / 2 + 0.45f, reachAcross = 0.1f;
            look.Mesh.Position = new Vector3(mid.X, Y(mid.X, mid.Z) - 0.05f, mid.Z);
            look.Mesh.Basis = new Godot.Basis(Vector3.Up, -turn) * Godot.Basis.FromScale(new Vector3(reachAlong, 0.7f + 1.6f * look.Burn, reachAcross));"""),
    ("""    /// <summary>The lights lying on the ground in loot's batch: the way out's band, the fed fires'
    /// rooms. Drawn as loot's light is drawn (EndLoot).</summary>
    void StoryLights()
    {
        // The way out breathes while its pulse keeps coming (a second and a half after the last).
        float way = (float)Mathf.Clamp(1 - (time - waySeen - 1.3) / 0.6, 0, 1);
        if (way > 0) Light(wayAt.X, wayAt.Y, wayAt.Z, Lit.Band, 0, wayReach, wayReach * 0.86f, WayCold, way * 0.9f);
        if (Deadfalls == null) return;
        foreach (var d in Deadfalls)
            if (fireLooks.TryGetValue(d.Light, out var look) && look.Burn > 0.02f)
            {
                var c = look.Mesh.Position;
                Light(c.X, c.Y + 0.05f, c.Z, Lit.Room, 0, (float)d.Reach, (float)d.Reach * 0.86f, DeadfallRoom, Mathf.Clamp(look.Burn, 0, 1));
            }
    }""",
     """    /// <summary>The way out's band of light, drawn in loot's batch as loot's light is (EndLoot).</summary>
    void StoryLights()
    {
        // It breathes while its pulse keeps coming (a second and a half after the last).
        float way = (float)Mathf.Clamp(1 - (time - waySeen - 1.3) / 0.6, 0, 1);
        if (way > 0) Light(wayAt.X, wayAt.Y, wayAt.Z, Lit.Band, 0, wayReach, wayReach * 0.86f, WayCold, way * 0.9f);
    }"""),
    ("""                for (int k = 0; k < 2; k++)
                    Smoke.Spawn(head + fwd * 0.1f * sc, fwd * (0.7f + R() * 0.5f) * sc + new Vector3((R() - 0.5f) * 0.3f, 0.35f + R() * 0.3f, (R() - 0.5f) * 0.3f),
                        0.9f + R() * 0.4f, 0.1f * sc, new Color(0.78f, 0.86f, 1.0f), new Color(0.6f, 0.66f, 0.78f), 0.42f * sc, drag: 2.2f, alpha: 0.42f);""",
     """                // (Two small puffs a pant were lost on the ground from thirty metres up.)
                for (int k = 0; k < 3; k++)
                    Smoke.Spawn(head + fwd * 0.12f * sc, fwd * (0.8f + R() * 0.6f) * sc + new Vector3((R() - 0.5f) * 0.4f, 0.45f + R() * 0.35f, (R() - 0.5f) * 0.4f),
                        1.1f + R() * 0.5f, 0.2f * sc, new Color(0.86f, 0.92f, 1.0f), new Color(0.62f, 0.68f, 0.8f), 0.75f * sc, drag: 1.8f, alpha: 0.6f);"""),
])
edit(r"src\Fx\BattleFx.Loot.cs", [
    ("Shaft = 7, Band = 8, Room = 9 }", "Shaft = 7, Band = 8 }"),
])
edit(r"shaders\loot_beam.gdshader", [
    ("""//   8 Band: a band of light lying on the ground at its reach (the way out), breathing.
//   9 Room: a fire's light lying on the ground out to its reach and no further (a fed deadfall).
""", """//   8 Band: a band of light lying on the ground at its reach (the way out), breathing.
"""),
    ("""	} else if (kind > 8.5) {
		// A fire's light on the ground, even out to its reach and falling away there (the room the
		// pack will not cross), a little stronger toward its heart. Never a line at its edge.
		vec2 e = vec2(x / half_w, y / (half_w * 0.83));
		float r = length(e);
		float lit = smoothstep(1.08, 0.86, r) * (0.55 + 0.45 * exp(-r * r * 2.5));
		light = deep * lit * 0.22;
		veil = 0.0;
	} else if (kind > 7.5) {""", """	} else if (kind > 7.5) {"""),
])
