import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Content/Boons.cs', [
("""    public static readonly string[] Great =
    [
        "hunters_mark", "momentum", "bloodthirst", "spirit_companion", "arcane_overflow", "glass_cannon",
        "duelists_grace", "restless_hands", "cinderwake", "iron_vow", "ember_tithe", "stormborn",
    ];""",
"""    public static readonly string[] Great =
    [
        "hunters_mark", "momentum", "bloodthirst", "spirit_companion", "arcane_overflow", "glass_cannon",
        "duelists_grace", "restless_hands", "cinderwake", "iron_vow", "ember_tithe", "stormborn",
        "from_the_ashes", "grounding", "rootbind", "go_for_the_throat",
    ];

    /// <summary>What each great blessing is for (docs/SKILLS_DESIGN.md, "Great
    /// blessings"): every path's list holds a ward, and a path slow to fell a
    /// champion holds an answer.</summary>
    public enum GreatRole { Power, Ward, Answer, Tempo }

    public static readonly Dictionary<string, GreatRole> GreatRoles = new()
    {
        ["momentum"] = GreatRole.Power, ["arcane_overflow"] = GreatRole.Power, ["glass_cannon"] = GreatRole.Power,
        ["duelists_grace"] = GreatRole.Power, ["cinderwake"] = GreatRole.Power, ["stormborn"] = GreatRole.Power,
        ["spirit_companion"] = GreatRole.Power,
        ["bloodthirst"] = GreatRole.Ward, ["iron_vow"] = GreatRole.Ward, ["from_the_ashes"] = GreatRole.Ward, ["grounding"] = GreatRole.Ward,
        ["hunters_mark"] = GreatRole.Answer, ["rootbind"] = GreatRole.Answer, ["go_for_the_throat"] = GreatRole.Answer,
        ["restless_hands"] = GreatRole.Tempo, ["ember_tithe"] = GreatRole.Tempo,
    };"""),
("""        new() { Id = "ember_tithe", Name = "Ember Tithe", Icon = "coin", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing,""",
"""        // The wards and answers the paths were missing: a ward for fire and for
        // storm, an answer to champions for the green and for the host.
        new() { Id = "from_the_ashes", Name = "From the Ashes", Icon = "embers", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Fire],
            Text = "Once a night, a blow that would end you burns instead: you rise with half your health, and everything near you catches fire.",
            DeeperText = ["You rise whole, and the fire reaches twice as far.", "Twice a night."] },
        new() { Id = "grounding", Name = "Grounding", Icon = "static", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Storm, Tag.Chain],
            Text = "A fifth of every blow that reaches you is turned aside as lightning, which leaps from you to three creatures near you.",
            Triggers = [T(TriggerEvent.Hurt, [new Effect.Chain(3, 7, 4, Basis.Hit, School.Storm)], icd: 0.3)],
            DeeperText = ["A third of every blow.", "The lightning leaps to six, and shocks all it strikes."],
            Deeper = [[], [T(TriggerEvent.Hurt, [new Effect.Chain(3, 7, 4, Basis.Hit, School.Storm), new Effect.Apply(P(Shock, 1, 1, 3), OnHit: false, Radius: 7, Count: 6)], icd: 0.3)]] },
        new() { Id = "rootbind", Name = "Rootbind", Icon = "thorn", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Nature],
            Text = "Every 6 s roots seize the toughest thing near you: they hold it fast for a second, and while they hold it, it takes 40% more from everything.",
            Triggers = [T(TriggerEvent.Tick, [new Effect.Apply(P(Stun, 1, 1, 1), OnHit: false, Radius: 12, Count: 1), new Effect.Apply(P(Mark, 1, 1.35, 1.5), OnHit: false, Radius: 12, Count: 1)], icd: 6)],
            DeeperText = ["The two toughest are seized.", "The roots come every 4 s."],
            Deeper = [[T(TriggerEvent.Tick, [new Effect.Apply(P(Stun, 1, 1, 1), OnHit: false, Radius: 12, Count: 2), new Effect.Apply(P(Mark, 1, 1.35, 1.5), OnHit: false, Radius: 12, Count: 2)], icd: 6)],
                [T(TriggerEvent.Tick, [new Effect.Apply(P(Stun, 1, 1, 1), OnHit: false, Radius: 12, Count: 2), new Effect.Apply(P(Mark, 1, 1.35, 1.5), OnHit: false, Radius: 12, Count: 2)], icd: 12)]] },
        new() { Id = "go_for_the_throat", Name = "Go for the Throat", Icon = "howl", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Summon],
            Text = "What fights for you goes for the toughest thing near you, and strikes champions 40% harder.",
            Mods = r => r >= 2 ? [Inc(Stat.SummonHaste, 0.2, "syn:go_for_the_throat")] : [],
            DeeperText = ["They strike 20% faster.", "Each champion that falls calls up a spirit wolf that stays the night."],
            Deeper = [[], [T(TriggerEvent.Kill, [new Effect.Raise(Effect.RaiseKind.SpiritWolf, 0, 6)], new() { Elite = true })]] },
        new() { Id = "ember_tithe", Name = "Ember Tithe", Icon = "coin", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing,"""),
])
print('boons ok')
