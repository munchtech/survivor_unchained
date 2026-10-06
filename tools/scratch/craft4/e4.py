from ed import sub

sub("src/Game/Game.cs", [
("""        var spoils = SurvivorUnchained.Maps.MapSpoils.Between(mapStart ?? Journey.Ch, Journey.Ch);
        Wait(alive ? 1.0 : 2.2, () =>""",
"""        var spoils = SurvivorUnchained.Maps.MapSpoils.Between(mapStart ?? Journey.Ch, Journey.Ch);
        // (pictures and probes of the atlas's pay read it from the log as well)
        if (Args.Has("shot"))
            GD.Print($"map paid: {spoils.Gear.Count} gear [{string.Join(", ", spoils.Gear.Select(g => $"{Inventory.RarityName(g)} {g.Def}"))}]; "
                + $"charts {spoils.Charts.Count}; {string.Join(", ", spoils.Materials.Select(m => $"{m.Key} {m.Value}"))}; gold {spoils.Gold:0}; {r.Gathered}");
        Wait(alive ? 1.0 : 2.2, () =>"""),
])
