from ed import edit
edit(r"src\Fx\BattleFx.Skills.cs", [
    ("""            // The survivor's own marks are quiet: a thin ring, so they never read as a threat.
            var pal = Palette.Of(e.School);
            if (art != "slash_quake") Ring(e.X, e.Z, r, pal.Glow * 0.3f, (float)e.Delay, false);""",
     """            // The survivor's own marks are quiet: where it will fall, a faint light gathering on the
            // ground as it comes, never a ring (six thin rings round her at once read as the
            // interface's circles, and as a threat).
            var pal = Palette.Of(e.School);
            if (art != "slash_quake")
                Sparks.Spawn(V(e.X, Y(e.X, e.Z) + 0.15, e.Z), Vector3.Zero, (float)e.Delay, r * 0.25f, pal.Glow * 0.12f, pal.Glow * 0.4f, r * 0.9f, alpha: 0.8f);"""),
    ("""                var col = Hdr("#8ab4ff", 1f);
                Ribbons.Bolt(top, ground + Vector3.Up * 0.2f, (clap ? 0.55f : small ? 0.22f : 0.38f) * g, clap ? 0.3f : 0.22f, col, 4f, small ? 1 : 3, 0.18f);
                // Its glow round the thread, so the strike reads as a blow of light, not a hairline.
                Ribbons.Bolt(top, ground + Vector3.Up * 0.2f, (clap ? 1.4f : small ? 0.6f : 1f) * g, 0.14f, Hdr("#2a5cff", 1f), 1.3f, 0, 0.16f);""",
     """                // Electric blue with a hot thread, never white: at four times a pale blue every bolt
                // and its burst came out white, a blown-out ball where each one landed.
                var col = Hdr("#7aa6ff", 1f);
                Ribbons.Bolt(top, ground + Vector3.Up * 0.2f, (clap ? 0.45f : small ? 0.18f : 0.3f) * g, clap ? 0.3f : 0.22f, col, 2.6f, small ? 1 : 3, 0.18f);
                // Its glow round the thread, so the strike reads as a blow of light, not a hairline.
                Ribbons.Bolt(top, ground + Vector3.Up * 0.2f, (clap ? 1.2f : small ? 0.5f : 0.85f) * g, 0.14f, Hdr("#2a50ff", 1f), 1.1f, 0, 0.16f);"""),
])
edit(r"src\Fx\BattleFx.cs", [
    ("""            var lt = school == School.Fire ? new Color(glow * 0.7f, glow * 0.45f, glow * 0.22f, 0.8f) : new Color(glow * 0.7f, glow * 0.7f, glow * 0.7f, 0.8f);""",
     """            // In its school's hue: grey-white, a storm's burst under every bolt was a white ball.
            var lt = school == School.Fire ? new Color(glow * 0.7f, glow * 0.45f, glow * 0.22f, 0.8f)
                : school == School.Storm ? new Color(glow * 0.3f, glow * 0.45f, glow * 0.95f, 0.75f)
                : new Color(glow * 0.7f, glow * 0.7f, glow * 0.7f, 0.8f);"""),
])
