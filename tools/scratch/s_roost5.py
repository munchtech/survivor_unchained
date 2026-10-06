PAIRS = [
('''        public override (string Def, double Weight)[] Crowd => [("footpad", 4), ("pillager", 1), ("bruiser", 1)];
        public override int CrowdAlive => 16;''',
'''        public override (string Def, double Weight)[] Crowd => [("footpad", 5), ("bruiser", 1)];
        public override int CrowdAlive => 16;'''),
('''        public override (string Def, double Weight)[] Crowd => [("footpad", 4), ("pillager", 1), ("bruiser", 1)];
        public override int CrowdAlive => 12;''',
'''        public override (string Def, double Weight)[] Crowd => [("footpad", 5), ("bruiser", 1)];
        public override int CrowdAlive => 12;'''),
('''            // He holds the cage row: he does not follow her down the ruts.
            if (door != null) { door.HomeX = bx; door.HomeZ = bz; door.Leash = 7; }''',
'''            // He holds the cage row: he does not follow her down the ruts. His door and his slam are the
            // lesson (go round it, off the ground it brings down), not his fists.
            if (door != null) { door.HomeX = bx; door.HomeZ = bz; door.Leash = 7; door.Damage *= 0.6; }'''),
]
