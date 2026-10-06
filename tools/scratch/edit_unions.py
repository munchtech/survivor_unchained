import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

UNIONS = '''
        /* ------------------------------------- unions (Content/Unions.cs) -- */
        new()
        {
            Id = "frostfire_comet", Name = "Frostfire Comet", School = School.Fire, Behavior = WeaponBehavior.Aimed, Tags = [Tag.Projectile, Tag.Spell, Tag.Fire, Tag.Frost, Tag.Explosion],
            Base = new() { Cooldown = 1.5, Damage = 70, Speed = 9, Projectiles = 1, Pierce = 0, Range = 16, Splash = 2.8, Life = 2.4, Radius = 0.5, Status = S(Chill, 1, 2.5, 3), GroundOnHit = G(2.4, 3, 0.3) },
            Art = "star", BossDamage = 1.6,
            Description = "Fire and frost in one falling star: it bursts, freezes what it does not burn, and the frozen it finds explode.",
            Triggers = [T(TriggerEvent.Hit, [new Effect.Explode(2.4, 1.0, Basis.Hit, School.Fire)], new() { Weapon = "frostfire_comet", TargetStatus = Frozen }, icd: 0.1)],
        },
        new()
        {
            Id = "the_tempest", Name = "The Tempest", School = School.Storm, Behavior = WeaponBehavior.Storm, Tags = [Tag.Storm, Tag.Area, Tag.Spell, Tag.Chain],
            Base = new() { Cooldown = 1.6, Damage = 45, Strikes = 6, StormRadius = 7, Splash = 1.8, Status = S(Shock, 1, 1, 3) },
            Art = "storm_eye", BossDamage = 2.2,
            Description = "The storm and its lightning are one: bolts fall on the crowd and leap from every shocked thing they strike.",
            Triggers = [T(TriggerEvent.Hit, [new Effect.Chain(3, 6, 0.5, Basis.Hit, School.Storm)], new() { Weapon = "the_tempest", TargetStatus = Shock }, icd: 0.05)],
        },
        new()
        {
            Id = "rotwood", Name = "Rotwood", School = School.Nature, Behavior = WeaponBehavior.Zone, Tags = [Tag.Zone, Tag.Area, Tag.Dot, Tag.Nature, Tag.Shadow],
            Base = new() { Cooldown = 3.6, Damage = 22, Radius = 4.2, Duration = 6, TickRate = 0.4, AtTarget = true, Slow = 0.45, Status = S(Poison, 0.8, 0.25, 4) },
            Art = "zone_plague", BossDamage = 2.0,
            Description = "The blight grows thorns: a wide, slow thicket that holds what it rots, and spreads the rot from what dies in it.",
            Triggers = [T(TriggerEvent.Kill, [new Effect.Spread(Poison, 3, 3, 2)], new() { Weapon = "rotwood" }, icd: 0.1)],
        },
        new()
        {
            Id = "butchers_wheel", Name = "Butcher's Wheel", School = School.Physical, Behavior = WeaponBehavior.Orbit, Tags = [Tag.Orbit, Tag.Melee, Tag.Steel, Tag.Physical, Tag.Area],
            Base = new() { Cooldown = 3.8, Damage = 30, Projectiles = 4, OrbitRadius = 2.9, OrbitSpeed = 4.8, Duration = 5, Radius = 0.75, Status = S(Bleed, 1, 0.4, 3, stack: true) },
            Art = "axe_blood", BossDamage = 1.6,
            Description = "The axes become cleavers and never stop turning: every cut a wound, and wounds that deepen.",
        },
        new()
        {
            Id = "hail_of_steel", Name = "Hail of Steel", School = School.Physical, Behavior = WeaponBehavior.Ring, Tags = [Tag.Projectile, Tag.Thrown, Tag.Ranged, Tag.Steel, Tag.Physical],
            Base = new() { Cooldown = 1.2, Damage = 40, Speed = 10, Projectiles = 12, Pierce = 3, Life = 1.2, Radius = 0.22, Status = S(Bleed, 0.4, 0.3, 3) },
            Art = "dagger_flurry", BossDamage = 2.2,
            Description = "Arrows and knives together, in every direction at once, opening wounds.",
        },
        new()
        {
            Id = "dawns_judgement", Name = "Dawn's Judgement", School = School.Holy, Behavior = WeaponBehavior.Bounce, Tags = [Tag.Projectile, Tag.Thrown, Tag.Bounce, Tag.Nova, Tag.Holy],
            Base = new() { Cooldown = 1.8, Damage = 34, Speed = 10.5, Projectiles = 2, Bounces = 9, Range = 16, Life = 3.5, Radius = 0.32, Knockback = 0.3, Status = S(Sear, 1, 1, 3) },
            Art = "disc_reckon", BossDamage = 1.8,
            Description = "Two shields of morning that ricochet through the crowd, and break into light wherever they strike.",
            Triggers = [T(TriggerEvent.Hit, [new Effect.Nova(2.4, 0.6, Basis.Hit, School.Holy, 0.4)], new() { Weapon = "dawns_judgement" }, icd: 0.12)],
        },
        new()
        {
            Id = "barrow_host", Name = "The Barrow Host", School = School.Shadow, Behavior = WeaponBehavior.Raise, Tags = [Tag.Summon, Tag.Spell, Tag.Shadow, Tag.Nature],
            Base = new() { Cooldown = 3, Damage = 70, Projectiles = 3, Duration = 40, Raises = "knight_ally" },
            Art = "risen", BossDamage = 1.0,
            Description = "The barrows send their knights, and the herd runs with them: a host that does not lie down.",
        },
        new()
        {
            Id = "soul_lantern", Name = "Soul Lantern", School = School.Shadow, Behavior = WeaponBehavior.Aimed, Tags = [Tag.Projectile, Tag.Spell, Tag.Shadow, Tag.Heal],
            Base = new() { Cooldown = 1.0, Damage = 80, Speed = 10, Projectiles = 2, Pierce = 6, Range = 16, Homing = 3, Life = 2.4, Radius = 0.3, Heal = 1.0, Status = S(Mark, 1, 1, 4) },
            Art = "siphon", BossDamage = 1.4,
            Description = "Shadow that passes through everything, marks it for the grave, and brings a little of it back to you.",
        },
        new()
        {
            Id = "starfall", Name = "Starfall", School = School.Arcane, Behavior = WeaponBehavior.Storm, Tags = [Tag.Spell, Tag.Arcane, Tag.Area, Tag.Projectile],
            Base = new() { Cooldown = 1.5, Damage = 50, Strikes = 5, StormRadius = 6.5, Splash = 1.7, Status = S(Mark, 0.5, 1, 4) },
            Art = "moonfall", BossDamage = 1.8,
            Description = "Moons fall among them and break into motes that hunt the strongest.",
            Triggers = [T(TriggerEvent.Hit, [new Effect.Missiles(2, 0.35, Basis.Hit, School.Arcane, Seek.Strongest, 10, "mote")], new() { Weapon = "starfall" }, icd: 0.06)],
        },
    }.ToDictionary(w => w.Id);
'''

p = 'logic/Content/Weapons.cs'
s = open(p, encoding='utf-8').read()
end = s.index("    }.ToDictionary(w => w.Id);")
s = s[:end].rstrip() + '\n' + UNIONS + s[end + len("    }.ToDictionary(w => w.Id);\n"):]
s = s.replace("""    /// <summary>Damage each rank adds (of the base). A single bolt grows more
    /// with its ranks than a field that already strikes a crowd does.</summary>
    public double Growth = Weapons.DamageStep;""", """    /// <summary>Damage each rank adds (of the base). A single bolt grows more
    /// with its ranks than a field that already strikes a crowd does.</summary>
    public double Growth = Weapons.DamageStep;
    /// <summary>Rules it brings into the fight while carried (a union's own).</summary>
    public TriggerDef[] Triggers = System.Array.Empty<TriggerDef>();""")
open(p, 'w', encoding='utf-8').write(s)

edit('logic/Sim/Battle.cs', [
("""        var w = new WeaponInst(id, rank, Weapons.Count);
        Weapons.Add(w);
        CheckDiscoveries();
        return w;
    }

    public void RemoveWeapon(string id)
    {
        int i = Weapons.FindIndex(w => w.Id == id);
        if (i < 0) return;
        Weapons.RemoveAt(i);
        for (int k = 0; k < Weapons.Count; k++) Weapons[k].Slot = k;
    }""", """        var w = new WeaponInst(id, rank, Weapons.Count);
        Weapons.Add(w);
        foreach (var t in w.Def.Triggers) AddTrigger(t, $"weapon:{id}", 1, id);
        CheckDiscoveries();
        return w;
    }

    public void RemoveWeapon(string id)
    {
        int i = Weapons.FindIndex(w => w.Id == id);
        if (i < 0) return;
        var w = Weapons[i];
        // Its own rules, and its evolution's, go with it.
        RemoveTriggers($"weapon:{id}");
        if (w.Evolution != null) RemoveTriggers($"evo:{w.Evolution.Id}");
        Weapons.RemoveAt(i);
        for (int k = 0; k < Weapons.Count; k++) Weapons[k].Slot = k;
    }

    /// <summary>Two evolved skills become one (Content/Unions.cs): both go, the
    /// union comes in at full rank, and a combat slot is free again.</summary>
    public WeaponInst? Unite(string union)
    {
        var u = Content.Unions.Find(union);
        if (u == null) return null;
        var a = Weapons.Find(w => w.Id == u.A);
        var c = Weapons.Find(w => w.Id == u.B);
        if (a?.Evolution == null || c?.Evolution == null) return null;
        RemoveWeapon(u.A);
        RemoveWeapon(u.B);
        var w = AddWeapon(u.Into, Content.Weapons.MaxRank);
        Events.Emit(new Ev.Evolve { Weapon = u.Into, Into = u.Id });
        Events.Emit(new Ev.Announce { Kicker = "Union", Title = u.Name, Subtitle = u.Description, Tone = Tone.Boon });
        return w;
    }"""),
("""public enum OfferKind { Weapon, Rank, Boon, Evolve, Heal, Gold, Hone }""", """public enum OfferKind { Weapon, Rank, Boon, Evolve, Heal, Gold, Hone, Union }"""),
])

edit('logic/Sim/LevelUp.cs', [
("""        int passiveRoom = Boons.MaxPassives - PassivesHeld(b);""", """        // So are unions, once both halves are evolved.
        if (offers.Count == 0 && ReadyUnions(b).FirstOrDefault() is { } un)
        {
            var wa = b.Weapons.First(w => w.Id == un.A);
            var wb = b.Weapons.First(w => w.Id == un.B);
            offers.Add(new Offer
            {
                Kind = OfferKind.Union, Id = un.Id, Rarity = Rarity.Legendary, Title = un.Name,
                Text = $"{wa.Evolution!.Name} and {wb.Evolution!.Name} become one. {un.Description} A combat slot is free again.",
                Icon = Content.Weapons.All[un.Into].Art, Tags = Content.Weapons.All[un.Into].Tags,
                Path = Paths.All.FirstOrDefault(p => p.Capstones.Contains(un.Id))?.Id,
            });
        }

        int passiveRoom = Boons.MaxPassives - PassivesHeld(b);"""),
("""    static bool IsCatalyst(Offer o, WeaponInst w) =>""", """    /// <summary>The unions whose two halves are carried, both evolved.</summary>
    public static IEnumerable<UnionDef> ReadyUnions(Battle b) =>
        Unions.All.Where(u => b.Weapons.Any(w => w.Id == u.A && w.Evolution != null) && b.Weapons.Any(w => w.Id == u.B && w.Evolution != null));

    static bool IsCatalyst(Offer o, WeaponInst w) =>"""),
("""            case OfferKind.Hone: b.Hone(o.Id); break;""", """            case OfferKind.Hone: b.Hone(o.Id); break;
            case OfferKind.Union: b.Unite(o.Id); break;"""),
("""        var list = offers.Take(System.Math.Max(count, offers.Count(o => o.Kind == OfferKind.Evolve))).ToList();""",
"""        var list = offers.Take(System.Math.Max(count, offers.Count(o => o.Kind is OfferKind.Evolve or OfferKind.Union))).ToList();"""),
("""        if (b.Banishes <= 0 || o.Kind is OfferKind.Evolve or OfferKind.Heal or OfferKind.Gold || !b.DraftOwed) return null;""",
"""        if (b.Banishes <= 0 || o.Kind is OfferKind.Evolve or OfferKind.Union or OfferKind.Heal or OfferKind.Gold || !b.DraftOwed) return null;"""),
])
print('ok')
