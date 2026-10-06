from ed import sub
sub('logic/World/Lore.cs', [
("""    /// <summary>A person's line said once in a playthrough, at the first chance
    /// once it holds (npcs.json "said": Brannoc's "Twelve, I made.").</summary>
    public bool? Once;
}""",
"""    /// <summary>A person's line said once in a playthrough, at the first chance
    /// once it holds (npcs.json "said": Brannoc's "Twelve, I made.").</summary>
    public bool? Once;
    /// <summary>What a once-only line does when said (Maeca, seeing the fang worn: her regard falls).</summary>
    public List<Change>? Effects;
}"""),
])
sub('logic/Play/Zone.cs', [
("""    /// <summary>Remember that a once-only line has been said.</summary>
    protected void MarkSaid(NpcDef def, string text) => W.Npc(def.Id).Flags[SaidKey(text)] = true;""",
"""    /// <summary>Remember that a once-only line has been said, and do what saying it does.</summary>
    protected void MarkSaid(NpcDef def, string text)
    {
        var n = W.Npc(def.Id);
        if (n.Flag(SaidKey(text)).Truthy) return;
        n.Flags[SaidKey(text)] = true;
        if (def.Said?.FirstOrDefault(l => l.Once == true && l.Text == text)?.Effects is { Count: > 0 } fx) Rules.Apply(fx, C);
    }"""),
])
sub('logic/World/Logic.cs', [
("""    public string? Give, Take;""",
"""    public string? Give, Take;
    /// <summary>With a give: who made it and the moment ("maeca:shedFur"), so the thing carries
    /// their history line (crafting.json, "history.shedFur").</summary>
    public string? Made;"""),
("""            var it = Inventory.Make(ch, e.Give, qty: qty, rarity: e.Rarity);
            var name = Items.Get(e.Give).Name;""",
"""            var it = Inventory.Make(ch, e.Give, qty: qty, rarity: e.Rarity);
            if (e.Made?.Split(':') is [var by, var moment]) (it.History ??= new()).Add(Crafting.History(w, by, moment));
            var name = Items.Get(e.Give).Name;"""),
])
sub('logic/Rpg/Crafting.cs', [
("""        if (q.Verb == Verb.Commission)
        {
            var w = x.World;
            w.Facts["commission.def"] = q.Def;
            w.Facts["commission.affix"] = q.Affix;
            w.Facts["commission.material"] = q.Material;
            w.Facts["commission.ready"] = w.Day + Rules.Commission.Days;
        }""",
"""        if (q.Verb == Verb.Commission)
        {
            var w = x.World;
            int ready = w.Day + Rules.Commission.Days;
            w.Facts["commission.def"] = q.Def;
            w.Facts["commission.affix"] = q.Affix;
            w.Facts["commission.material"] = q.Material;
            w.Facts["commission.ready"] = ready;
            // Ready by morning: then it shows over the smith's head.
            w.Scheduled.Add(new ScheduledChange { Day = ready, Id = "commission.done", Effect = new() { new Change { Set = new() { ["commission.done"] = true } } } });
        }"""),
("""        foreach (var k in new[] { "commission.def", "commission.affix", "commission.material", "commission.ready" }) x.World.Facts.Remove(k);""",
"""        foreach (var k in new[] { "commission.def", "commission.affix", "commission.material", "commission.ready", "commission.done" }) x.World.Facts.Remove(k);"""),
])
