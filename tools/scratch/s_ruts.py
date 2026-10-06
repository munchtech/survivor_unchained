PAIRS = [
('''    /// <summary>Three pickets on the lips of the ruts, torch and whistle each. A whistle calls footpads
    /// off both banks at once, either side of her (the pincer: get out from between them). Firepot Nan
    /// comes with the third, and lobs from the lip with her throwers. It teaches his thrown torch: the
    /// lobbed circle, and fire left burning.</summary>''',
'''    /// <summary>Three pickets on the lips of the ruts, torch and whistle each, lit one after another up the
    /// road: a picket silenced, the next answers further up. A whistle calls footpads off both banks at
    /// once, either side of her (the pincer: get out from between them). Firepot Nan comes with the third,
    /// and lobs from the lip with her throwers. It teaches his thrown torch: the lobbed circle, and fire
    /// left burning.</summary>'''),
('''        double nanSeed, whistleT = 3;
        int whistles, turn;
        bool seen, pincered;
        int Silenced => pickets.Count(p => !Up(p.E, p.Seed));

        protected override void Open()
        {
            foreach (var post in new[] { "picket_a", "picket_b", "picket_c" })
            {
                var (x, z) = A.Place[post];
                var e = A.Foe("footpad", x, z, 3.5, quiet: true);
                if (e == null) continue;
                e.Named = new Named { Title = "Kerchief Picket" };
                e.HomeX = x; e.HomeZ = z;
                pickets.Add((e, e.Seed, post));
                A.Script(e, Hold);
            }
        }''',
'''        double nanSeed, whistleT = 2, lightT = -1;
        int lit;
        bool seen, pincered;
        static readonly string[] Posts = ["picket_a", "picket_b", "picket_c"];
        int Silenced => lit - pickets.Count(p => Up(p.E, p.Seed));

        protected override void Open() => Light();

        /// <summary>The next picket up the road takes up his torch.</summary>
        void Light()
        {
            var (x, z) = A.Place[Posts[lit++]];
            var e = A.Foe("footpad", x, z, 3, quiet: true);
            if (e == null) return;
            e.Named = new Named { Title = "Kerchief Picket" };
            e.HomeX = x; e.HomeZ = z;
            pickets.Add((e, e.Seed, Posts[lit - 1]));
            A.Script(e, Hold);
            whistleT = Math.Min(whistleT, 1.5);
        }'''),
('''            // The whistles, in turn among those still standing: each calls the pincer.
            if (up.Count > 0 && (whistleT -= dt) <= 0)
            {
                whistleT = 8;
                var k = up[turn++ % up.Count];
                whistles++;
                A.Bark(k.E.X, k.E.Z, "(A whistle, short and sharp. Another answers it, further up.)", null);
                Pincer();
                if (whistles == 3 && nan == null) Nan();
            }
            // The goal: the nearest picket standing, then Nan.
            var next = up.OrderBy(k => Dist(k.E.X, k.E.Z, p.X, p.Z)).FirstOrDefault();
            A.Goal = next.E != null ? (next.E.X, next.E.Z) : Up(nan, nanSeed) ? (nan!.X, nan.Z) : null;
            if (up.Count == 0 && nan == null) Nan();
            if (up.Count == 0 && nan != null && !Up(nan, nanSeed)) Done = true;''',
'''            // A picket silenced: his torch goes down the bank, and the next answers further up.
            if (up.Count == 0 && lightT < 0 && lit < Posts.Length)
            {
                var (sx, sz) = A.Place[Posts[lit - 1]];
                A.Bark(sx, sz, "The torch tumbles down the bank. That whistle will not answer again.", null);
                lightT = 2.5;
            }
            if (lightT > 0 && (lightT -= dt) <= 0) { lightT = -1; Light(); up = pickets.Where(k => Up(k.E, k.Seed)).ToList(); }
            // His whistle, on its own time: each calls the pincer. Nan comes with the third picket's first.
            if (up.Count > 0 && (whistleT -= dt) <= 0)
            {
                whistleT = 9;
                var k = up[0];
                A.Bark(k.E.X, k.E.Z, "(A whistle, short and sharp. Another answers it, further up.)", null);
                Pincer();
                if (lit == 3 && nan == null) Nan();
            }
            var next = up.FirstOrDefault();
            A.Goal = next.E != null ? (next.E.X, next.E.Z) : Up(nan, nanSeed) ? (nan!.X, nan.Z) : null;
            if (Silenced == Posts.Length && lit == Posts.Length && nan == null) Nan();
            if (Silenced == Posts.Length && lit == Posts.Length && nan != null && !Up(nan, nanSeed)) Done = true;'''),
]
