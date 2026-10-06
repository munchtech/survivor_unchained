from ed import sub

sub("logic/Play/JourneyLoot.cs", [
("""                // The people's material left lying is the night's too.
                if (p.Kind == PickupKind.Material && p.Ref != null) { Inventory.AddToPack(Ch, Inventory.Make(Ch, p.Ref, Math.Max(1, MathX.RoundInt(p.Value)))); b.Pickups.Release(p); }
                continue;""",
"""                // The people's material left lying is the night's too.
                if (p.Kind == PickupKind.Material && p.Ref != null) { Inventory.AddToPack(Ch, Inventory.Make(Ch, p.Ref, Math.Max(1, MathX.RoundInt(p.Value)))); b.Pickups.Release(p); }
                // A chart or a ruler's thing left lying comes home as if picked up (they go to the
                // satchel, which never fills): left, the ruler's charts and Marks were lost with the map.
                else if (p.Kind == PickupKind.Item && p.Ref != null && p.Look != Verdict.Hidden && PickedUp(p)) { home++; b.Pickups.Release(p); }
                continue;"""),
])
