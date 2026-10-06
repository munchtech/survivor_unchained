PAIRS = [
('''            if (runT < 0) return false;
            runT += dt;
            if (runT < 1.0)''',
'''            if (runT < 0) return false;
            runT += dt;
            if (runT < mark)'''),
('''            double k = Math.Min(1, (runT - 1.0) / 0.45);''', '''            double k = Math.Min(1, (runT - mark) / 0.45);'''),
('''                if (!hit)
                {
                    pantT = Pant;
                    B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Safe, X = e.X, Z = e.Z, Radius = 2.4, Delay = Pant, From = e, Label = "She missed" });
                }''',
'''                if (!hit)
                {
                    pantT = Pant;
                    B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Safe, X = e.X, Z = e.Z, Radius = 2.4, Delay = Pant, From = e, Label = "She missed" });
                    if (!missedOnce) { missedOnce = true; A.Bark(e.X, e.Z, "She missed, and stands there blowing. Now.", null); }
                }
                else if (!hitOnce) { hitOnce = true; A.Bark(B.Player.X, B.Player.Z, "The gap was hers. Through the wolves, not the gap.", null); }'''),
('''            A.Bark(w.X, w.Z, "A rising howl: the Pack wheels.", null);
            double dx = p.X - w.X, dz = p.Z - w.Z, d = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));''',
'''            A.Bark(w.X, w.Z, "A rising howl: the Pack wheels.", null);
            // The first is a lesson: marked longer, and said.
            mark = drives == 0 ? 1.7 : 1.0;
            if (drives == 0) A.Say("The drive", "The gap is her lane: go through the wolves", "danger");
            drives++;
            double dx = p.X - w.X, dz = p.Z - w.Z, d = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));'''),
('''                Shape = TelegraphShape.Line, X = laneX0, Z = laneZ0, X1 = laneX1, Z1 = laneZ1, Width = 2.4, Delay = 1.0,''',
'''                Shape = TelegraphShape.Line, X = laneX0, Z = laneZ0, X1 = laneX1, Z1 = laneZ1, Width = 2.4, Delay = mark,'''),
('''        bool hit, wheeled;''', '''        bool hit, wheeled, missedOnce, hitOnce, spent;
        int drives;
        /// <summary>How long a drive's lane is marked before she runs it (the first, longer: a lesson).</summary>
        double mark = 1.0;
        /// <summary>Her drives are numbered: after this many she has nothing left to run with, and her guard
        /// is gone (the stage is bounded by her drives, so hands that run into the gap are hurt, not held).</summary>
        const int Drives = 7;'''),
('''            white.TakenMul = Ringed ? 0 : pantT > 0 ? Opened : Guarded;''',
'''            if (!spent && drives >= Drives && runT < 0 && pantT <= 0)
            {
                spent = true;
                A.Say("Whitethroat is spent", "She has nothing left to run with", "boon");
            }
            white.TakenMul = Ringed ? 0 : pantT > 0 ? Opened : spent ? 1.25 : Guarded;'''),
('''            driveT -= dt;
            if (driveT <= 0 && runT < 0 && pantT <= 0)''', '''            driveT -= dt;
            if (!spent && driveT <= 0 && runT < 0 && pantT <= 0)'''),
]
