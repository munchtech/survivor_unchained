p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot\src\Game\Game.cs"
s = open(p, encoding="utf-8").read()
a = '''        // --give A,B[:RANK][@EVOLUTION],+PASSIVE[:RANK]: a build in hand from the start'''
b = '''        // --loot [--loot-at T]: one of every tier of loot falling round the survivor T seconds in (3 by
        // default), each landing as shown loot does (Ev.Drop), for pictures of their light.
        if (!lootDone && Args.Has("loot") && Battle is { } lb && Journey.Playtime >= Args.Num("loot-at", 3))
        {
            lootDone = true;
            var tiers = new[] { LootTier.Common, LootTier.Uncommon, LootTier.Rare, LootTier.Epic, LootTier.Set, LootTier.Legendary, LootTier.Storied, LootTier.Chart, LootTier.Quest, LootTier.Rare, LootTier.Epic };
            for (int i = 0; i < tiers.Length; i++)
            {
                double a = i * Math.Tau / tiers.Length + 0.3, d = 3.2 + (i % 3) * 1.1;
                var k = lb.SpawnPickup(tiers[i] is LootTier.Quest ? PickupKind.Quest : PickupKind.Item, lb.Player.X + Math.Cos(a) * d, lb.Player.Z + Math.Sin(a) * d, 0.01);
                if (k == null) continue;
                k.Loot = (int)tiers[i]; k.Tier = Math.Min(5, (int)tiers[i]); k.Vx = k.Vz = 0; k.Age = -600;
                lb.Events.Emit(new Ev.Drop { Tier = k.Loot, X = k.X, Z = k.Z, Kind = k.Kind });
            }
        }
        // --give A,B[:RANK][@EVOLUTION],+PASSIVE[:RANK]: a build in hand from the start'''
assert a in s
s = s.replace(a, b, 1)
a2 = "    bool hordeDone, dropsDone, castDone,"
assert a2 in s
s = s.replace(a2, "    bool hordeDone, dropsDone, lootDone, castDone,")
open(p, "w", encoding="utf-8").write(s)
print("ok")
