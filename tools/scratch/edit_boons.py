import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:80], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Sim/Battle.cs', [
("""                    Events.Emit(new Ev.Chain { Points = [x, z, e.X, e.Z], School = fx.Kind == StatusKind.Burn ? School.Fire : School.Nature });""",
"""                    Events.Emit(new Ev.Chain { Points = [x, z, e.X, e.Z], School = fx.Kind switch
                    {
                        StatusKind.Burn => School.Fire, StatusKind.Mark => School.Arcane, StatusKind.Bleed => School.Physical,
                        StatusKind.Chill => School.Frost, StatusKind.Shock => School.Storm, StatusKind.Sear => School.Holy, _ => School.Nature,
                    } });"""),
("""        if (id == "vitality") HealPlayer(25, "vitality");""", """        if (id == "vitality") HealPlayer(25, "vitality");
        // Wisdom is the draft's own passive: each rank a reroll.
        if (id == "wisdom") Rerolls++;"""),
])

edit('logic/Content/Boons.cs', [
("""/// <summary>What a build must have for a card to be offered.</summary>
public sealed record Requirement(StatusKind? Status = null, Tag? Tag = null, string? Boon = null, Requirement[]? Any = null);""",
"""/// <summary>What a build must have for a card to be offered: a status it
/// applies, a kind of skill, a blessing held; any of several, or all of them
/// (a duo blessing wants two families at once).</summary>
public sealed record Requirement(StatusKind? Status = null, Tag? Tag = null, string? Boon = null, Requirement[]? Any = null, Requirement[]? All = null);"""),
("""        new() { Id = "greed", Name = "Greed's Pull", Icon = "magnet", Rarity = Rarity.Common, Max = 5, Kind = BoonKind.Passive,
            Text = "Ember, gold and potions fly to you from 1.2 m farther.", Mods = r => [Flat(Stat.PickupRadius, 1.2 * r, "boon:greed")] },""",
"""        new() { Id = "greed", Name = "Greed's Pull", Icon = "magnet", Rarity = Rarity.Common, Max = 5, Kind = BoonKind.Passive,
            Text = "Ember, gold and draughts fly to you from 1.2 m farther, and every stone holds 4% more ember.",
            Mods = r => [Flat(Stat.PickupRadius, 1.2 * r, "boon:greed"), Inc(Stat.XpGain, 0.04 * r, "boon:greed")] },"""),
("""        new() { Id = "fortune", Name = "Fortune", Icon = "coin", Rarity = Rarity.Uncommon, Max = 4, Kind = BoonKind.Passive,
            Text = "+10% luck: more and better drops, and rarer cards.", Mods = r => [Flat(Stat.Luck, 0.1 * r, "boon:fortune")] },
        new() { Id = "wisdom", Name = "Wisdom", Icon = "book", Rarity = Rarity.Uncommon, Max = 4, Kind = BoonKind.Passive,
            Text = "+10% ember from every stone.", Mods = r => [Inc(Stat.XpGain, 0.1 * r, "boon:wisdom")] },""",
"""        new() { Id = "fortune", Name = "Fortune", Icon = "coin", Rarity = Rarity.Uncommon, Max = 4, Kind = BoonKind.Passive,
            Text = "+10% luck: a fourth card more often, rarer cards, ranks that surge, better drops.", Mods = r => [Flat(Stat.Luck, 0.1 * r, "boon:fortune")] },
        new() { Id = "wisdom", Name = "Wisdom", Icon = "book", Rarity = Rarity.Uncommon, Max = 4, Kind = BoonKind.Passive,
            Text = "+6% ember from every stone, and a reroll with every rank.", Mods = r => [Inc(Stat.XpGain, 0.06 * r, "boon:wisdom")] },"""),
("""        new() { Id = "velocity", Name = "Velocity", Icon = "spear", Rarity = Rarity.Common, Max = 3, Kind = BoonKind.Passive, Tags = [Tag.Projectile],
            Text = "+15% projectile speed.", Mods = r => [Inc(Stat.ProjectileSpeed, 0.15 * r, "boon:velocity")] },""",
"""        new() { Id = "velocity", Name = "Velocity", Icon = "spear", Rarity = Rarity.Common, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Projectile],
            Text = "Projectiles fly 12% faster and land 5% harder.",
            Mods = r => [Inc(Stat.ProjectileSpeed, 0.12 * r, "boon:velocity"), Inc(Stat.DamageOf(Tag.Projectile), 0.05 * r, "boon:velocity")] },"""),
("""        new() { Id = "thorns", Name = "Thorns", Icon = "thorn", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive,
            Text = "Whatever strikes you takes 4 + 20% of the blow back.", Mods = r => [Flat(Stat.Thorns, r, "boon:thorns")] },""",
"""        new() { Id = "thorns", Name = "Thorns", Icon = "thorn", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Nature, Tag.Aura],
            Text = "Struck, you burst with thorns: everything close takes a blow that grows with the ember, and what struck you takes a fifth of its blow back.",
            Mods = r => [Flat(Stat.Thorns, r, "boon:thorns")] },"""),
("""        new() { Id = "searing", Name = "Searing Aura", Icon = "retaura", Rarity = Rarity.Rare, Max = 4, Kind = BoonKind.Passive, Tags = [Tag.Holy, Tag.Aura, Tag.Area],
            Text = "A holy aura sears everything near you twice a second.", Mods = _ => [] },""",
"""        new() { Id = "searing", Name = "Searing Aura", Icon = "retaura", Rarity = Rarity.Rare, Max = 4, Kind = BoonKind.Passive, Tags = [Tag.Holy, Tag.Aura, Tag.Area],
            Text = "A holy aura sears everything near you twice a second.", Mods = _ => [] },
        new() { Id = "emberblood", Name = "Emberblood", Icon = "flame", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Fire, Tag.Dot],
            Text = "+10% fire damage, and what you set burning burns 15% longer.",
            Mods = r => [Inc(Stat.DamageOf(School.Fire), 0.1 * r, "boon:emberblood"), Inc(Stat.StatusDurationOf(Burn), 0.15 * r, "boon:emberblood")] },
        new() { Id = "conduit", Name = "Conduit", Icon = "static", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Storm, Tag.Chain],
            Text = "+10% storm damage, and the shocked take 6% more from the blow that finds them.",
            Mods = r => [Inc(Stat.DamageOf(School.Storm), 0.1 * r, "boon:conduit"), Flat(Stat.ShockBonus, 0.06 * r, "boon:conduit")] },
        new() { Id = "venom", Name = "Venom", Icon = "plague", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Dot],
            Text = "Damage over time (burning, bleeding, poison, searing) is 12% stronger, and poisons take hold 10% more often.",
            Mods = r => [Inc(Stat.DamageOf(Tag.Dot), 0.12 * r, "boon:venom"), Inc(Stat.StatusChance, 0.1 * r, "boon:venom")] },
        new() { Id = "kinship", Name = "Kinship", Icon = "spiritwolf", Rarity = Rarity.Uncommon, Max = 5, Kind = BoonKind.Passive, Tags = [Tag.Summon],
            Text = "What fights for you strikes 15% harder and is 15% tougher.",
            Mods = r => [Inc(Stat.SummonDamage, 0.15 * r, "boon:kinship"), Inc(Stat.SummonHealth, 0.15 * r, "boon:kinship")] },"""),
("""            Text = "The dark grows: more of them, and faster. You grow too: +15% ember and gold.",""",
"""            Text = "The dark grows: 15% more of them, and 5% faster. You grow too: +15% ember and gold.","""),
("""            Text = "Fire on the frozen is a violent thing: burning a frozen creature makes it explode.", Requires = new(Any: [new(Status: Chill)]),
            Triggers = [T(TriggerEvent.Hit, [new Effect.Explode(2.6, 1.2, Basis.Hit, School.Frost)], new() { School = School.Fire, TargetStatus = Frozen }, icd: 0.05)] },""",
"""            Text = "Fire on the frozen is a violent thing: burning a frozen creature makes it explode.", Requires = new(All: [new(Status: Chill), new(Status: Burn)]),
            Triggers = [T(TriggerEvent.Hit, [new Effect.Explode(2.6, 1.2, Basis.Hit, School.Frost)], new() { School = School.Fire, TargetStatus = Frozen }, icd: 0.05)] },

        /* --------------------------------- duos: two families, one rule -- */
        new() { Id = "overload", Name = "Overload", Icon = "bolt", Rarity = Rarity.Epic, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Storm, Tag.Fire, Tag.Explosion],
            Text = "Lightning on the burning is a blast: storm damage to a burning creature makes it explode.",
            Requires = new(All: [new(Any: [new(Status: Shock), new(Tag: Tag.Storm)]), new(Status: Burn)]),
            Triggers = [T(TriggerEvent.Hit, [new Effect.Explode(2.2, 0.9, Basis.Hit, School.Fire)], new() { School = School.Storm, TargetStatus = Burn }, icd: 0.08)] },
        new() { Id = "frostbite", Name = "Frostbite", Icon = "frost", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Frost, Tag.Physical, Tag.Dot],
            Text = "The frozen bleed out: a frozen creature's bleeding hurts three times as much.",
            Requires = new(All: [new(Status: Chill), new(Status: Bleed)]) },

        /* ------------------------------ more for the families that had few -- */
        new() { Id = "contagion", Name = "Contagion", Icon = "plague", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Dot, Tag.Nature],
            Text = "Poison spreads on its own: each second a poisoned creature passes a dose to the nearest of its neighbours.", Requires = new(Status: Poison) },
        new() { Id = "deaths_due", Name = "Death's Due", Icon = "mark", Rarity = Rarity.Rare, Max = 1, Kind = BoonKind.Blessing, Tags = [Tag.Arcane, Tag.Explosion],
            Text = "A marked creature that dies bursts for a fifth of its health, and the toughest thing near it is marked.", Requires = new(Status: Mark),
            Triggers = [T(TriggerEvent.Kill, [new Effect.Explode(2.4, 0.2, Basis.MaxHp, School.Arcane), new Effect.Apply(P(Mark, 1, 1, 5), OnHit: false, Radius: 7, Count: 1)],
                new() { TargetStatus = Mark }, icd: 0.08)] },"""),
])

edit('logic/Sim/LevelUp.cs', [("""        if (req.Any != null) return req.Any.Any(r => Meets(b, r, statuses, tags));""", """        if (req.Any != null) return req.Any.Any(r => Meets(b, r, statuses, tags));
        if (req.All != null) return req.All.All(r => Meets(b, r, statuses, tags));""")])
print("ok")
