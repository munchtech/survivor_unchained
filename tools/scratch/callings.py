import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:100], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Content/Boons.cs', [
("""    public string[]? DeeperText;
    public TriggerDef[][]? Deeper;
}""",
"""    public string[]? DeeperText;
    public TriggerDef[][]? Deeper;
    /// <summary>A calling's own great blessing: offered to that calling alone.</summary>
    public string? Calling;
}"""),
("""        "from_the_ashes", "grounding", "rootbind", "go_for_the_throat",
    ];""",
"""        "from_the_ashes", "grounding", "rootbind", "go_for_the_throat",
        "hold_the_crossing", "blood_up", "second_reading", "hunters_blind",
    ];"""),
("""        ["restless_hands"] = GreatRole.Tempo, ["ember_tithe"] = GreatRole.Tempo,
    };""",
"""        ["restless_hands"] = GreatRole.Tempo, ["ember_tithe"] = GreatRole.Tempo,
        ["hold_the_crossing"] = GreatRole.Power, ["blood_up"] = GreatRole.Power, ["second_reading"] = GreatRole.Power, ["hunters_blind"] = GreatRole.Power,
    };"""),
("""        new() { Id = "ember_tithe", Name = "Ember Tithe", Icon = "coin", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing,""",
"""        // Each calling's own: the way it fights, and no one else's.
        new() { Id = "hold_the_crossing", Name = "Hold the Crossing", Icon = "aegis", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Calling = "warden",
            Text = "Stand your ground and you are a crossing nothing passes: while you stand still, +6 armour and your weapons fire 20% faster.",
            Mods = r => [new StatMod(Stat.Armor, ModKind.Flat, r >= 2 ? 10 : 6, "syn:hold_the_crossing", ModWhen.Still),
                new StatMod(Stat.Cooldown, ModKind.More, r >= 2 ? -0.25 : -0.2, "syn:hold_the_crossing", ModWhen.Still),
                .. (r >= 3 ? new[] { new StatMod(Stat.Regen, ModKind.Flat, 3, "syn:hold_the_crossing", ModWhen.Still) } : [])],
            DeeperText = ["+10 armour, and 25% faster.", "And you mend 3 health a second while you hold."] },
        new() { Id = "blood_up", Name = "Blood Up", Icon = "drain", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Calling = "reaver",
            Text = "Below a third of your health your blows land 40% harder, and every kill mends 1% of it.",
            Mods = r => [new StatMod(Stat.Damage, ModKind.More, r >= 2 ? 0.6 : 0.4, "syn:blood_up", ModWhen.LowHealth)],
            Triggers = [T(TriggerEvent.Kill, [new Effect.Heal(0.01, Basis.MaxHp)], new() { SelfHpBelow = 0.35 })],
            DeeperText = ["60% harder.", "Each kill mends 2%."],
            Deeper = [[], [T(TriggerEvent.Kill, [new Effect.Heal(0.01, Basis.MaxHp)], new() { SelfHpBelow = 0.35 })]] },
        new() { Id = "second_reading", Name = "Second Reading", Icon = "arcane", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Spell], Calling = "arcanist",
            Text = "A spell read twice is cast twice: every 8 s, everything you carry fires at once.",
            Triggers = [T(TriggerEvent.Tick, [new Effect.Cooldown(99, Effect.CooldownScope.All)], icd: 8)],
            DeeperText = ["Every 6 s.", "Every 4 s."],
            Deeper = [[T(TriggerEvent.Tick, [new Effect.Cooldown(99, Effect.CooldownScope.All)], icd: 24)],
                [T(TriggerEvent.Tick, [new Effect.Cooldown(99, Effect.CooldownScope.All)], icd: 12)]] },
        new() { Id = "hunters_blind", Name = "The Hunters' Blind", Icon = "mark", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing, Tags = [Tag.Ranged], Calling = "stalker",
            Text = "From cover, the first blow is the one that counts: half your blows on anything unhurt are critical strikes.",
            Mods = r => r >= 3 ? [Flat(Stat.CritDamage, 0.25, "syn:hunters_blind")] : [],
            DeeperText = ["All of them.", "+25% critical strike damage."] },
        new() { Id = "ember_tithe", Name = "Ember Tithe", Icon = "coin", Rarity = Rarity.Legendary, Max = 3, Kind = BoonKind.Blessing,"""),
])

edit('logic/Sim/Battle.cs', [
("""    public readonly HashSet<string> Stands = new();
    public bool Roads, Omens;""",
"""    public readonly HashSet<string> Stands = new();
    public bool Roads, Omens;
    /// <summary>The survivor's calling (its own great blessing is offered to it alone).</summary>
    public string? Calling;"""),
("""            // Night-Eyes: the far ones, in the dark, are seen best.""",
"""            // The Hunters' Blind: the first blow on anything unhurt.
            if (e.Hp >= e.MaxHp && Boons.TryGetValue("hunters_blind", out int blind)) chance += blind >= 2 ? 1 : 0.5;
            // Night-Eyes: the far ones, in the dark, are seen best."""),
])

edit('logic/Play/Journey.cs', [
("""        b.Favours.UnionWith(Callings.Archetype(Ch.Archetype).Favours);""",
"""        b.Favours.UnionWith(Callings.Archetype(Ch.Archetype).Favours);
        b.Calling = Ch.Archetype;"""),
])

edit('logic/Sim/LevelUp.cs', [
("""                if (r >= d.Max || b.BannedCards.Contains(id)) continue;
                bool deeper = r > 0 && d.DeeperText is { } dt && r - 1 < dt.Length;""",
"""                if (r >= d.Max || b.BannedCards.Contains(id) || (d.Calling != null && d.Calling != b.Calling)) continue;
                bool deeper = r > 0 && d.DeeperText is { } dt && r - 1 < dt.Length;"""),
("""                bool suits = OnPath(id, p => p.Great);
                if (suits) o.Why.Add("Suits your path");
                pool.Add(new Cand { O = o, W = (deeper ? 3 : 1) * (suits ? 1.5 : 1) * Again(o) });""",
"""                bool suits = OnPath(id, p => p.Great);
                if (d.Calling != null) o.Why.Add("Your calling's own");
                else if (suits) o.Why.Add("Suits your path");
                pool.Add(new Cand { O = o, W = (deeper ? 3 : 1) * (suits || d.Calling != null ? 1.5 : 1) * Again(o) });"""),
])

P = 'logic/Content/Paths.cs'
edit(P, [
('Great = ["iron_vow", "bloodthirst", "from_the_ashes", "hunters_mark"],', 'Great = ["iron_vow", "bloodthirst", "from_the_ashes", "hunters_mark", "hold_the_crossing"],'),
('Great = ["bloodthirst", "momentum", "duelists_grace", "restless_hands", "cinderwake"],', 'Great = ["bloodthirst", "momentum", "duelists_grace", "restless_hands", "cinderwake", "hold_the_crossing", "blood_up"],'),
('Great = ["bloodthirst", "spirit_companion", "go_for_the_throat"],', 'Great = ["bloodthirst", "spirit_companion", "go_for_the_throat", "blood_up"],'),
('Great = ["arcane_overflow", "glass_cannon", "hunters_mark", "ember_tithe", "grounding"],', 'Great = ["arcane_overflow", "glass_cannon", "hunters_mark", "ember_tithe", "grounding", "second_reading"],'),
('Great = ["from_the_ashes", "cinderwake", "arcane_overflow"],', 'Great = ["from_the_ashes", "cinderwake", "arcane_overflow", "second_reading"],'),
('Great = ["hunters_mark", "glass_cannon", "duelists_grace", "momentum", "bloodthirst"],', 'Great = ["hunters_mark", "glass_cannon", "duelists_grace", "momentum", "bloodthirst", "hunters_blind"],'),
('Great = ["rootbind", "spirit_companion", "iron_vow"],', 'Great = ["rootbind", "spirit_companion", "iron_vow", "hunters_blind"],'),
])
edit('tests/BlessingTests.cs', [('Assert.InRange(p.Great.Length, 3, 5);', 'Assert.InRange(p.Great.Length, 3, 7);')])
print('ok')
