PAIRS = [
# ---- stage 1: the picket on the lip, out of reach until his pincer is broken
('''    /// <summary>Three pickets on the lips of the ruts, torch and whistle each, lit one after another up the
    /// road: a picket silenced, the next answers further up. A whistle calls footpads off both banks at
    /// once, either side of her (the pincer: get out from between them). Firepot Nan comes with the third,
    /// and lobs from the lip with her throwers. It teaches his thrown torch: the lobbed circle, and fire
    /// left burning.</summary>''',
'''    /// <summary>Three pickets on the lips of the ruts, torch and whistle each, lit one after another up the
    /// road: a picket silenced, the next answers further up. His whistle calls footpads off both banks at
    /// once, either side of her (the pincer: get out from between them). Up on the lip he is out of her
    /// reach until his pincer is broken; then he comes down to it, and his whistle goes on calling them.
    /// Firepot Nan comes with the third, and lobs from the lip with her throwers. It teaches his thrown
    /// torch: the lobbed circle, and fire left burning.</summary>'''),
('''        public override string Goal => $"Silence the pickets ({Silenced} of 3)";''',
'''        public override string Goal => OnLip ? $"Break the pincer ({Got} of {Need})" : $"Silence the pickets ({Silenced} of 3)";
        /// <summary>The pincer his whistle called as he lit his torch: while it stands he is up on the lip.</summary>
        readonly List<(Enemy E, double Seed)> wave = new();
        int Need => Math.Max(0, wave.Count - 1);
        int Got => Math.Min(Need, wave.Count(w => !Up(w.E, w.Seed)));
        bool onLip;
        bool OnLip => onLip && Got < Need;'''),
('''            var e = A.Foe("footpad", x, z, 3, quiet: true);
            if (e == null) return;
            e.Named = new Named { Title = "Kerchief Picket" };
            e.HomeX = x; e.HomeZ = z;
            pickets.Add((e, e.Seed, Posts[lit - 1]));
            A.Script(e, Hold);
            whistleT = Math.Min(whistleT, 1.5);
        }''',
'''            var e = A.Foe("footpad", x, z, 3, quiet: true);
            if (e == null) return;
            e.Named = new Named { Title = "Kerchief Picket" };
            e.HomeX = x; e.HomeZ = z;
            pickets.Add((e, e.Seed, Posts[lit - 1]));
            A.Script(e, Hold);
            // Up on the lip, out of her reach, he whistles at once.
            onLip = true;
            e.Disposition = Disposition.Neutral;
            e.TakenMul = 0;
            whistleT = 0.5;
        }'''),
('''        bool Hold(Enemy e, double dt)
        {
            var p = B.Player;
            double d = Dist(p.X, p.Z, e.X, e.Z);
            if (d < 3.5) return false;''',
'''        bool Hold(Enemy e, double dt)
        {
            var p = B.Player;
            double d = Dist(p.X, p.Z, e.X, e.Z);
            if (d < 3.5 && !OnLip) return false;'''),
('''            if (lightT > 0 && (lightT -= dt) <= 0) { lightT = -1; Light(); up = pickets.Where(k => Up(k.E, k.Seed)).ToList(); }''',
'''            if (lightT > 0 && (lightT -= dt) <= 0) { lightT = -1; Light(); up = pickets.Where(k => Up(k.E, k.Seed)).ToList(); }
            // His pincer broken, he comes down off the lip to it.
            if (onLip && !OnLip && up.Count > 0)
            {
                onLip = false;
                var k = up[0];
                k.E.Disposition = Disposition.Hostile;
                k.E.TakenMul = 1;
                A.Bark(k.E.X, k.E.Z, "The picket comes down off the lip with his torch.", null);
            }'''),
('''                A.Bark(k.E.X, k.E.Z, "(A whistle, short and sharp. Another answers it, further up.)", null);
                Pincer();''',
'''                A.Bark(k.E.X, k.E.Z, "(A whistle, short and sharp. Another answers it, further up.)", null);
                var called = Pincer();
                if (onLip && wave.Count == 0) wave.AddRange(called.Select(c => (c, c.Seed)));'''),
('''            var next = up.FirstOrDefault();
            A.Goal = next.E != null ? (next.E.X, next.E.Z) : Up(nan, nanSeed) ? (nan!.X, nan.Z) : null;''',
'''            var next = up.FirstOrDefault();
            A.Goal = OnLip ? null : next.E != null ? (next.E.X, next.E.Z) : Up(nan, nanSeed) ? (nan!.X, nan.Z) : null;
            if (!onLip && wave.Count > 0 && up.Count == 0) wave.Clear();'''),
('''        /// <summary>Off both banks at once, level with her: two knots of footpads, one each side.</summary>
        void Pincer()
        {
            var p = B.Player;
            int n = 2 + A.Tier;
            double z = Math.Clamp(p.Z, -44, -25);
            A.Group("footpad", n, -5.6, z, 1.5);
            A.Group("footpad", n, 5.6, z, 1.5);
            if (!pincered) { pincered = true; A.Say("Off both banks at once", "Get out from between them", "danger"); }
        }''',
'''        /// <summary>Off both banks at once, level with her: two knots of footpads, one each side.</summary>
        List<Enemy> Pincer()
        {
            var p = B.Player;
            int n = 2 + A.Tier;
            double z = Math.Clamp(p.Z, -44, -25);
            var o = A.Group("footpad", n, -5.6, z, 1.5);
            o.AddRange(A.Group("footpad", n, 5.6, z, 1.5));
            if (!pincered) { pincered = true; A.Say("Off both banks at once", "Get out from between them", "danger"); }
            return o;
        }'''),
('''        public override BossBar? Bar => Up(nan, nanSeed)
            ? new BossBar(nan!.Def.Name, nan.Def.Lesson, nan.Hp, nan.MaxHp, IsBoss: false)
            : null;
    }

    /* ----------------------------------------------------------- the cage yard -- */''',
'''        public override BossBar? Bar => OnLip ? new BossBar("The pincer", "The picket is out of reach until it breaks", Need - Got, Math.Max(1, Need), Shielded: true, IsBoss: false)
            : Up(nan, nanSeed) ? new BossBar(nan!.Def.Name, nan.Def.Lesson, nan.Hp, nan.MaxHp, IsBoss: false)
            : null;
    }

    /* ----------------------------------------------------------- the cage yard -- */'''),
# ---- stage 2: Barn-Door stands in front of the lock she works at
('''    /// <summary>The cage row, held by Barn-Door. A lock gives for the one who stands by it (her weapons
    /// break the one she stands by: his cage, at the boss). The last lock frees the teamsters as by day;
    /// the fourth cage stands open and empty. With the cages empty, it is Barn-Door alone.</summary>''',
'''    /// <summary>The cage row, held by Barn-Door. A lock gives for the one who stands by it (her weapons
    /// break the one she stands by: his cage, at the boss), but not while he stands in front of it: bring
    /// him down, or draw him off (he is slow, and will not leave the yard). The last lock frees the
    /// teamsters as by day; the fourth cage stands open and empty. With the cages empty, it is Barn-Door
    /// alone.</summary>'''),
('''                    Locks.Add(new StandBy { X = x, Z = z, Reach = 3.2, Takes = 8 });''',
'''                    Locks.Add(new StandBy { X = x, Z = z, Reach = 3.2, Takes = 9 });'''),
('''            door = A.Foe("mb_barn_door", bx, bz, 1.5);''', '''            door = A.Foe("mb_barn_door", bx, bz, 2.5);'''),
('''                if (!told && l.At(B)) { told = true; A.Say("Stand by a lock", "Your weapons break the one you stand by", "info"); }
                if (l.Step(B, dt, 871000 + i))''',
'''                if (!told && l.At(B)) { told = true; A.Say("Stand by a lock", "Your weapons break the one you stand by", "info"); }
                // Not while he stands in front of it.
                if (Up(door, doorSeed) && Dist(door!.X, door.Z, l.X, l.Z) < 4) continue;
                if (l.Step(B, dt, 871000 + i))'''),
# ---- stage 3: a wider line that all but stops shots
('''            levy = new Levy(A, lx, lz, p.X, p.Z, 6 + A.Tier, caller: "The Pike-Captain") { Wheel = 0.5 };''',
'''            levy = new Levy(A, lx, lz, p.X, p.Z, 8 + A.Tier, caller: "The Pike-Captain") { Wheel = 0.5 };'''),
('''            // Shots through the line reach him at a third; round it, he is open.
            bool behind = levy != null && levy.Between(p.X, p.Z, c.X, c.Z);
            c.TakenMul = behind ? 0.35 : 1;''',
'''            // Through the line little reaches him; round it, he is open.
            bool behind = levy != null && levy.Between(p.X, p.Z, c.X, c.Z);
            c.TakenMul = behind ? 0.15 : 1;'''),
]
