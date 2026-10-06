from ed import edit
edit(r"src\Audio\Sfx.cs", [
    ("public static class Sfx\n", "public static partial class Sfx\n"),
])
edit(r"src\Audio\SoundBridge.cs", [
    ("""                    if (h.Blocked) Sfx.Blocked(At(h.X, h.Z)); else Sfx.Hit(h.School, h.Crit, At(h.X, h.Z));""",
     """                    if (h.Blocked) Sfx.Blocked(At(h.X, h.Z)); else { Sfx.Hit(h.School, h.Crit, At(h.X, h.Z)); Sfx.HitOf(h.Art, At(h.X, h.Z)); }"""),
    ("""                case Ev.Explosion ex: Sfx.Explosion(ex.Power, At(ex.X, ex.Z)); break;""",
     """                case Ev.Explosion ex: Sfx.Burst(ex.Art, ex.Power, At(ex.X, ex.Z)); break;"""),
    ("""                case Ev.Slash s: Sfx.Swing(At(s.X, s.Z)); break;
                case Ev.Muzzle m: Sfx.Shoot(m.School, At(m.X, m.Z)); break;""",
     """                // Each skill in its own voice (Sfx.Skills), the school's where it has none.
                case Ev.Slash s: Sfx.Swing(s.Art, At(s.X, s.Z)); break;
                case Ev.Muzzle m: Sfx.Cast(m.Art, m.School, At(m.X, m.Z)); break;
                case Ev.Strike st when st.Art != null: Sfx.Falling(st.Art, st.Delay, At(st.X, st.Z)); break;
                case Ev.Chain ch when ch.Points.Length >= 2: Sfx.Arc(At(ch.Points[0], ch.Points[1])); break;
                case Ev.Beam bm when bm.Art?.StartsWith("beam") == true: Sfx.Lance(bm.Art, bm.Duration, At(bm.X1, bm.Z1)); break;"""),
])
