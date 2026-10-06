PAIRS = [
# the ruts: two whistles from the lip before he comes down
('''        bool onLip;
        bool OnLip => onLip && Got < Need;''',
'''        bool onLip;
        /// <summary>Whistles from the lip: he comes down to her only when two pincers have been broken.</summary>
        int fromLip;
        bool OnLip => onLip && (fromLip < 2 || Got < Need);'''),
('''            // Up on the lip, out of her reach, he whistles at once.
            onLip = true;''',
'''            // Up on the lip, out of her reach, he whistles at once.
            onLip = true;
            fromLip = 0;
            wave.Clear();'''),
('''                var called = Pincer();
                if (onLip && wave.Count == 0) wave.AddRange(called.Select(c => (c, c.Seed)));''',
'''                var called = Pincer();
                if (onLip) { fromLip++; wave.AddRange(called.Select(c => (c, c.Seed))); whistleT = 7; }'''),
('''            nan = A.Foe("mb_firepot_nan", x, z, 2.5);
            nanSeed = nan?.Seed ?? 0;''',
'''            nan = A.Foe("mb_firepot_nan", x, z, 3.5);
            nanSeed = nan?.Seed ?? 0;
            // Three pots at a time is her lesson; each of them need not be a third of a life.
            if (nan != null) nan.Damage *= 0.6;'''),
# the cage yard
('''                    Locks.Add(new StandBy { X = x, Z = z, Reach = 3.2, Takes = 9 });''',
'''                    Locks.Add(new StandBy { X = x, Z = z, Reach = 3.2, Takes = 10 });'''),
('''            door = A.Foe("mb_barn_door", bx, bz, 2.5);''', '''            door = A.Foe("mb_barn_door", bx, bz, 3.5);'''),
# the camp: the captain, and his line formed again twice
('''            captain = A.Foe("mb_pike_captain", bx, bz, 3);''', '''            captain = A.Foe("mb_pike_captain", bx, bz, 4);'''),
('''            if (levy is { Broken: true } && lines < 2 && c.Hp > c.MaxHp * 0.4 && !cratesLit) { Form(); A.Say("The levy forms again", "Round its ends", "danger"); }''',
'''            if (levy is { Broken: true } && lines < 3 && c.Hp > c.MaxHp * 0.25 && !cratesLit) { Form(); A.Say("The levy forms again", "Round its ends", "danger"); }'''),
]
