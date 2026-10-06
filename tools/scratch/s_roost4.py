PAIRS = [
('''                    Locks.Add(new StandBy { X = x, Z = z, Reach = 3.2, Takes = 5 });''',
'''                    Locks.Add(new StandBy { X = x, Z = z, Reach = 3.2, Takes = 8 });'''),
('''            captain = A.Foe("mb_pike_captain", bx, bz, 1.5);
            if (captain != null)
            {
                // His line is the lesson, not his own teeth: less of them when she gets round to him.
                captain.Damage *= 0.6;''',
'''            captain = A.Foe("mb_pike_captain", bx, bz, 3);
            if (captain != null)
            {
                // His line is the lesson, not his own teeth: less of them when she gets round to him.
                captain.Damage *= 0.5;'''),
('''            levy = new Levy(A, lx, lz, p.X, p.Z, 6 + A.Tier, caller: "The Pike-Captain");''',
'''            levy = new Levy(A, lx, lz, p.X, p.Z, 6 + A.Tier, caller: "The Pike-Captain") { Wheel = 0.5 };'''),
('''            if (d > 0.2) { double s = Math.Min(d, 4 * dt); e.X += dx / d * s; e.Z += dz / d * s; }''',
'''            if (d > 0.2) { double s = Math.Min(d, 5.5 * dt); e.X += dx / d * s; e.Z += dz / d * s; }'''),
('''            // Shots through the line reach him at half; round it, he is open.
            bool behind = levy != null && levy.Between(p.X, p.Z, c.X, c.Z);
            c.TakenMul = behind ? 0.5 : 1;''',
'''            // Shots through the line reach him at a third; round it, he is open.
            bool behind = levy != null && levy.Between(p.X, p.Z, c.X, c.Z);
            c.TakenMul = behind ? 0.35 : 1;'''),
]
