PAIRS = [
('''            var (bx, bz) = A.Place["yard"];
            door = A.Foe("mb_barn_door", bx, bz, 3);
            doorSeed = door?.Seed ?? 0;''',
'''            var (bx, bz) = A.Place["yard"];
            door = A.Foe("mb_barn_door", bx, bz, 1.5);
            doorSeed = door?.Seed ?? 0;
            // He holds the cage row: he does not follow her down the ruts.
            if (door != null) { door.HomeX = bx; door.HomeZ = bz; door.Leash = 7; }'''),
]
