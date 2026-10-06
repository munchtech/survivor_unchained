PAIRS = [
('''                A.Bark(k.E.X, k.E.Z, "The picket comes down off the lip with his torch.", null);''',
'''                A.Bark(k.E.X, k.E.Z, "The picket comes down the bank at you, torch first.", null);'''),
('''                // Not while he stands in front of it.
                if (Up(door, doorSeed) && Dist(door!.X, door.Z, l.X, l.Z) < 4) continue;''',
'''                // Not while he stands in front of it.
                if (Up(door, doorSeed) && Dist(door!.X, door.Z, l.X, l.Z) < 4)
                {
                    if (!blocked && l.At(B)) { blocked = true; A.Say("Barn-Door is in the way", "Draw him off the lock, then break it", "info"); }
                    continue;
                }'''),
('''        double doorSeed, storeT = 6;
        bool told;''', '''        double doorSeed, storeT = 6;
        bool told, blocked;'''),
('''Form(); A.Say("The levy forms again", "Round its ends", "danger"); }''', '''Form(); A.Say("The levy forms again", "Round its ends to the captain", "danger"); }'''),
('''    public override string BossAt => "boss_at";''', '''    public override string BossAt => "boss_at";
    public override string ShutSight => "Behind you, his people drag a cart across the way you came.";'''),
]
