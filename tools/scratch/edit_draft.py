import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Sim/Battle.cs', [
("""public enum OfferKind { Weapon, Rank, Boon, Evolve, Heal, Gold }""",
"""public enum OfferKind { Weapon, Rank, Boon, Evolve, Heal, Gold, Hone }"""),
("""    public Rarity Rarity;
    public string Title = "", Text = "", Icon = "";
    public int? From, To;
    public Tag[] Tags = Array.Empty<Tag>();
}""", """    public Rarity Rarity;
    public string Title = "", Text = "", Icon = "";
    public int? From, To;
    public Tag[] Tags = Array.Empty<Tag>();
    /// <summary>Ranks beyond the one (a surge: two at once).</summary>
    public int Surge;
    /// <summary>The build path it belongs to, if the build walks one it is on.</summary>
    public string? Path;
    /// <summary>Learned by day: it comes a rank higher.</summary>
    public bool Familiar;
    /// <summary>Why the draft dealt it (shown on the card): on your path, familiar, evolves something.</summary>
    public readonly List<string> Why = new();
}"""),
("""    public readonly HashSet<Tag> Favours = new();
    public int Rerolls = 2, Banishes = 1;""", """    public readonly HashSet<Tag> Favours = new();
    /// <summary>The build paths the calling leans toward, for the draft.</summary>
    public readonly HashSet<string> CallingPaths = new();
    /// <summary>Combat skills learned by day: the night's draft offers them
    /// sooner, and a rank higher (Rpg/SkillBook.cs).</summary>
    public readonly HashSet<string> Familiar = new();
    /// <summary>What the draft remembers between drafts (LevelUp).</summary>
    public readonly DraftMemory Drafting = new();
    /// <summary>Rerolls and banishes in hand; each milestone level adds a reroll, up to MaxRerolls.</summary>
    public int Rerolls = 3, Banishes = 2;
    public const int MaxRerolls = 9;"""),
("""    public void GainEmber(double v)
    {
        if (!EmberOn) return;
        EmberXp += v * Stats.Get(Stat.XpGain);""", """    /// <param name="raw">As it is, not multiplied by what grows ember (a skipped draft's refund).</param>
    public void GainEmber(double v, bool raw = false)
    {
        if (!EmberOn) return;
        EmberXp += v * (raw ? 1 : Stats.Get(Stat.XpGain));"""),
("""            if (Content.Boons.IsMilestone(EmberLevel)) PendingBlessings.Add(EmberLevel);""", """            if (Content.Boons.IsMilestone(EmberLevel))
            {
                PendingBlessings.Add(EmberLevel);
                // A milestone also hands back a reroll.
                Rerolls = Math.Min(MaxRerolls, Rerolls + 1);
            }"""),
("""    public void Evolve(string id, string branch)""", """    /// <summary>A finished weapon honed (the endless dark's draft): a little more damage each time.</summary>
    public void Hone(string id)
    {
        var w = Weapons.Find(x => x.Id == id);
        if (w == null || w.Honed >= LevelUp.MaxHone) return;
        w.Honed++;
        w.Mods.Damage *= 1 + LevelUp.HoneStep;
    }

    public void Evolve(string id, string branch)"""),
])

edit('logic/Sim/Weapons.cs', [
("""    /// <summary>For beams and orbits: active until.</summary>
    public double ActiveT;""", """    /// <summary>For beams and orbits: active until.</summary>
    public double ActiveT;
    /// <summary>Times it has been honed (finished, in the endless dark).</summary>
    public int Honed;"""),
])

edit('logic/Play/Journey.cs', [
("""        b.Favours.UnionWith(Callings.Archetype(Ch.Archetype).Favours);
        b.GearIds.UnionWith(kit.GearIds);
        b.GearStatuses.UnionWith(kit.GearStatuses);
        b.Rerolls = kit.Rerolls;
        b.Banishes = 1;""", """        b.Favours.UnionWith(Callings.Archetype(Ch.Archetype).Favours);
        b.CallingPaths.UnionWith(Content.Paths.All.Where(p => p.Callings.Contains(Ch.Archetype)).Select(p => p.Id));
        // What was learned by day comes to hand sooner in the night's draft.
        if (b.EmberOn) b.Familiar.UnionWith(Ch.Skills.Where(id => Content.Weapons.All.ContainsKey(id)));
        b.GearIds.UnionWith(kit.GearIds);
        b.GearStatuses.UnionWith(kit.GearStatuses);
        b.Rerolls = kit.Rerolls;
        b.Banishes = 2;"""),
])

edit('logic/Rpg/Character.cs', [
("""    public int StartLevels, Revives, Rerolls = 2;""", """    public int StartLevels, Revives, Rerolls = 3;"""),
])

edit('logic/Play/Zones/ArenaRun.cs', [
("""            great15 = true;
            B.GreatOwed++;""", """            great15 = true;
            B.GreatOwed++;
            // And a banish with it: by now the build knows what it does not want.
            B.Banishes++;"""),
])

edit('src/Game/GameMenus.cs', [
("""        Present(LevelUp.Draft(b, LevelUp.Count(b)));""", """        Present(LevelUp.Draft(b));"""),
("""        LevelUp.Choose(b, o);
        if (o.Kind == OfferKind.Weapon) Toast(new Toast(ToastKind.Level, $"{o.Title} joins your arsenal"));
        if (b.DraftOwed) Present(LevelUp.Draft(b, offers.Count));
        else CloseDraft();
    }

    void Reroll()
    {
        var b = Battle!;
        if (b.Rerolls <= 0) return;
        b.Rerolls--;
        Present(LevelUp.Draft(b, offers.Count));
    }

    void Banish(int i)
    {
        var b = Battle!;
        if (i < 0 || i >= offers.Count || b.Banishes <= 0 || offers[i].Kind == OfferKind.Evolve) return;
        b.Banishes--;
        b.BannedCards.Add(offers[i].Id);
        Present(LevelUp.Draft(b, offers.Count));
    }""", """        LevelUp.Choose(b, o);
        if (o.Kind == OfferKind.Weapon) Toast(new Toast(ToastKind.Level, $"{o.Title} joins your arsenal"));
        if (b.DraftOwed) Present(LevelUp.Draft(b));
        else CloseDraft();
    }

    void Reroll()
    {
        if (LevelUp.Reroll(Battle!) is { } again) Present(again);
    }

    void Banish(int i)
    {
        if (i < 0 || i >= offers.Count || LevelUp.Banish(Battle!, offers[i]) is not { } again) return;
        Present(again);
    }

    void Skip()
    {
        var b = Battle!;
        if (!LevelUp.Skip(b)) return;
        if (b.DraftOwed) Present(LevelUp.Draft(b));
        else CloseDraft();
    }"""),
])
print("ok")
