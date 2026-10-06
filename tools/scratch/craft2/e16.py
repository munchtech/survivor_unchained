from ed import sub
sub('src/Game/Game.cs', [
("""                var parts = spec.Split(':');
                var idq = parts[0].Split('*');
                int qty = idq.Length > 1 && int.TryParse(idq[1], out var nq) ? nq : 1;
                Journey.GiveItem(idq[0], qty, parts.Length > 1 && int.TryParse(parts[1], out var r) ? r : null);""",
"""                var parts = spec.Split(':');
                var idq = parts[0].Split('*');
                int qty = idq.Length > 1 && int.TryParse(idq[1], out var nq) ? nq : 1;
                int? rar = parts.Length > 1 && int.TryParse(parts[1], out var r) ? r : null;
                // iron_helm:3:of_the_wolf@1+of_the_lantern@2 : a piece with just those affixes, at those grades.
                if (parts.Length > 2)
                {
                    var affixes = parts[2].Split('+').Select(a => a.Split('@')).Select(a => new AffixRoll { Id = a[0], Tier = a.Length > 1 && int.TryParse(a[1], out var t) ? t : 0 }).ToList();
                    Inventory.AddToPack(Journey.Ch, Inventory.Make(Journey.Ch, idq[0], rarity: rar, affixes: affixes));
                }
                else Journey.GiveItem(idq[0], qty, rar);"""),
])
