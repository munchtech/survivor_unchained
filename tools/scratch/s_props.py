PAIRS = [
('''        foreach (var pc in map.Pieces) G.Look.AddProp(pc.Id, pc.X, pc.Z, pc.Rot, pc.Scale);''',
'''        // Until arena art builds a fight's place to its outline (PlaceBuilt), the old round arena's props
        // stand inside it: a stump in a neck the fight needs, a cart across a gate. Where the place is, they
        // go, drawn and solid both; its own cover comes with its own build.
        bool clear = !Fight.PlaceBuilt;
        foreach (var pc in map.Pieces)
            if (!clear || !Fight.Place.Inside(pc.X, pc.Z, -1.5)) G.Look.AddProp(pc.Id, pc.X, pc.Z, pc.Rot, pc.Scale);
        if (clear)
            foreach (var c in b.Collision.All().Where(c => c.Tag == null && Fight.Place.Inside(c.X, c.Z, -1.5)).ToList()) b.Collision.Remove(c.Id);'''),
]
