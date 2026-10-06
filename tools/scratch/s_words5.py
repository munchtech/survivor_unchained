PAIRS = [
('''        foreach (var g in Fight.Place.Gates.Where(g => g.Into == ground)) StoryPlace.Shut(B.Collision, g);
        open.Clear();
        open.Add(ground);''', '''        foreach (var g in Fight.Place.Gates.Where(g => g.Into == ground))
        {
            StoryPlace.Shut(B.Collision, g);
            if (Fight.ShutSight is { } sight) B.Events.Emit(new Ev.Bark { X = (g.X0 + g.X1) / 2, Z = (g.Z0 + g.Z1) / 2, Text = sight });
        }
        open.Clear();
        open.Add(ground);'''),
]
