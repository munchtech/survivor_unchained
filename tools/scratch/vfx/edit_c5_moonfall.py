from ed import edit
edit(r"src\Fx\BattleFx.cs", [
    ("""            : holy ? new Color(glow * 0.95f, glow * 0.7f, glow * 0.32f, 0.85f) : new Color(glow, glow, glow, 1);""",
     """            : holy ? new Color(glow * 0.95f, glow * 0.7f, glow * 0.32f, 0.85f)
            // A storm's in its own blue (white, Thunderclap's burst was a blown-out ball).
            : school == School.Storm ? new Color(glow * 0.45f, glow * 0.65f, glow * 1.1f, 1) : new Color(glow, glow, glow, 1);"""),
])
edit(r"src\Fx\BattleFx.Skills.cs", [
    ("""                Ribbons.Line(new[] { top, top.Lerp(ground, 0.5f), ground + Vector3.Up * 0.3f }, 0.45f * g, 0.25f, Hdr("#c8b8ff", 1f), 2.6f, Ribbons.Style.Glow, new[] { 0f, 0.6f, 1f });
                // The moon breaks into stardust (filmed, LTX), its light thrown out in a ring.
                Books.Spawn("moon_burst", ground + Vector3.Up * 0.6f, r * 0.8f, 0.7f, new Color(0.6f, 0.5f, 1.1f, 0.85f), flat: true, sizeEnd: r * 2.6f);
                Flash(ground + Vector3.Up * 1.5f, new Color(0.75f, 0.7f, 1f), 7, 0.3f, r * 3);
                Scars.Add("runes", ground, r * 0.6f, 1.2f, -0.7f);
                AddFront(ground, r * 1.3f, 0.35f, 0.25f * g, Hdr("#c8b8ff", 1f), 2.2f, Ribbons.Style.Glow, 0.2f);""",
     """                // Moonlight cold silver-blue, its breaking a deep violet: pale lilac streaks, stardust
                // and rings read pink-white, a field of lavender hoops.
                Ribbons.Line(new[] { top, top.Lerp(ground, 0.5f), ground + Vector3.Up * 0.3f }, 0.3f * g, 0.22f, Hdr("#a8bcff", 1f), 2.0f, Ribbons.Style.Glow, new[] { 0f, 0.6f, 1f });
                // The moon breaks into stardust (filmed, LTX), its light thrown out.
                Books.Spawn("moon_burst", ground + Vector3.Up * 0.6f, r * 0.7f, 0.65f, new Color(0.26f, 0.22f, 0.95f, 0.6f), flat: true, sizeEnd: r * 2.0f);
                Flash(ground + Vector3.Up * 1.5f, new Color(0.55f, 0.6f, 1f), 6, 0.3f, r * 3);
                Scars.Add("runes", ground, r * 0.6f, 1.2f, -0.7f);
                AddFront(ground, r * 1.2f, 0.3f, 0.16f * g, Hdr("#6a5aff", 1f), 1.2f, Ribbons.Style.Wisp, 0.2f);"""),
])
