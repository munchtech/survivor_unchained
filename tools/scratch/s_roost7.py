PAIRS = [
('''            var next = Locks.Where(l => !l.Broken).OrderBy(l => Dist(l.X, l.Z, p.X, p.Z)).FirstOrDefault();
            A.Goal = next != null ? (next.X, next.Z) : Up(door, doorSeed) ? (door!.X, door.Z) : null;''',
'''            var next = Locks.Where(l => !l.Broken).OrderBy(l => Dist(l.X, l.Z, p.X, p.Z)).FirstOrDefault();
            // The lock, unless he stands in front of it: then him.
            bool guarded = next != null && Up(door, doorSeed) && Dist(door!.X, door.Z, next.X, next.Z) < 4;
            A.Goal = next != null && !guarded ? (next.X, next.Z) : Up(door, doorSeed) ? (door!.X, door.Z) : null;'''),
]
