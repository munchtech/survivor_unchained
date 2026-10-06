import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Sim/Battle.cs', [
("""    /// <summary>Learned by day: it comes a rank higher.</summary>
    public bool Familiar;""", """    /// <summary>Carried by day (attuned): it comes in at a higher rank.</summary>
    public bool Attuned;"""),
("""    /// <summary>Combat skills learned by day: the night's draft offers them
    /// sooner, and a rank higher (Rpg/SkillBook.cs).</summary>
    public readonly HashSet<string> Familiar = new();""", """    /// <summary>The skills carried by day, attuned for the night, and the rank
    /// each comes in at: the draft offers them first (Rpg/SkillBook.cs).</summary>
    public readonly Dictionary<string, int> Attuned = new();
    /// <summary>Skills learned by day and not carried: offered a little more.</summary>
    public readonly HashSet<string> Familiar = new();"""),
])

edit('logic/Play/Journey.cs', [
("""        // What was learned by day comes to hand sooner in the night's draft.
        if (b.EmberOn) b.Familiar.UnionWith(Ch.Skills.Where(id => Content.Weapons.All.ContainsKey(id)));""",
"""        // What is carried by day is attuned for the night (offered first, a
        // rank or two up); what is only learned comes a little more often.
        if (b.EmberOn)
        {
            foreach (var id in SkillBook.Attuned(Ch)) b.Attuned[id] = SkillBook.NightRank(Ch);
            b.Familiar.UnionWith(Ch.Skills.Where(id => Content.Weapons.All.ContainsKey(id) && !b.Attuned.ContainsKey(id)));
        }"""),
])

edit('logic/Rpg/SkillBook.cs', [
("""    /// <summary>Every third level the calling teaches one of its own kind the""", """    /// <summary>The skills attuned for the night: those carried by day (and
    /// measured up to). In an arena the ember offers them in its first drafts,
    /// and each comes in at NightRank.</summary>
    public static IEnumerable<string> Attuned(CharacterData ch) => Carried(ch).Select(c => c.Id).Where(id => Weapons.All[id].Findable);

    /// <summary>The rank an attuned skill comes in at by night: two, and three
    /// once the survivor has grown (the tenth level), so the day's growth is
    /// felt in the dark without the ember starting anywhere but low.</summary>
    public static int NightRank(CharacterData ch) => ch.Level >= 10 ? 3 : 2;

    /// <summary>Every third level the calling teaches one of its own kind the"""),
])

edit('logic/Sim/LevelUp.cs', [
("""    public const double PathLean = 1.5, CallingLean = 1.3, FamiliarLean = 1.6, PassivePathLean = 1.3;""",
"""    public const double PathLean = 1.5, CallingLean = 1.3, AttunedLean = 2.0, FamiliarLean = 1.3, PassivePathLean = 1.3;
    /// <summary>The first skill drafts of an arena in which an attuned skill not yet
    /// taken is always among the cards.</summary>
    public const int AttunedDrafts = 4;"""),
("""                // Learned by day: it comes to hand sooner, and a rank higher.
                if (b.Familiar.Contains(id))
                {
                    w *= FamiliarLean;
                    o.Familiar = true;
                    o.To = 2;
                    o.Why.Insert(0, "Familiar: learned by day, it comes a rank higher");
                }
                combat.Add(new Cand { O = o, W = w, NewWeapon = true });""",
"""                // Carried by day: attuned, it comes first and comes in higher.
                if (b.Attuned.TryGetValue(id, out int at))
                {
                    w *= AttunedLean;
                    o.Attuned = true;
                    o.To = at;
                    o.Why.Insert(0, $"Attuned: carried by day, it comes in at rank {at}");
                }
                else if (b.Familiar.Contains(id))
                {
                    w *= FamiliarLean;
                    o.Why.Add("Familiar: you have learned it");
                }
                combat.Add(new Cand { O = o, W = w, NewWeapon = true, Attuned = o.Attuned });"""),
("""        public bool NewWeapon;
    }""", """        public bool NewWeapon, Attuned;
    }"""),
("""        // At least one combat skill; until three are carried, a new one among them.
        bool young = b.Weapons.Count < 3;""", """        // The first drafts bring what was carried by day.
        if (Open() > 0 && mem.SkillDrafts < AttunedDrafts && !offers.Any(o => o.Attuned))
            Add(TakeFrom(b, combat, c => c.Attuned));
        // At least one combat skill; until three are carried, a new one among them.
        bool young = b.Weapons.Count < 3;"""),
("""        if (offers.Any(o => o.Rarity >= Rarity.Rare && o.Kind == OfferKind.Boon)) mem.RarePity = 0;
        else mem.RarePity++;""", """        if (offers.Any(o => o.Rarity >= Rarity.Rare && o.Kind == OfferKind.Boon)) mem.RarePity = 0;
        else mem.RarePity++;
        if (!mem.Shown.Any()) mem.SkillDrafts++;"""),
("""    /// <summary>Drafts skipped, and great blessings taken (the fifteenth minute's deals four).</summary>
    public int Skipped, Greats;""", """    /// <summary>Drafts skipped, and great blessings taken (the fifteenth minute's deals four).</summary>
    public int Skipped, Greats;
    /// <summary>Skill drafts dealt this arena (a reroll is the same draft).</summary>
    public int SkillDrafts;"""),
])
print('ok')
