from ed import sub
NEW = '''    /* --------------------------------------------------- the still-room -- */

    public static BrewRule? BrewOf(string draught) => Rules.Brews.FirstOrDefault(b => b.Draught == draught);

    /// <summary>The draughts a crafter brews, in the order they are shown.</summary>
    public static IEnumerable<BrewRule> Brews(string crafter) => Rules.Brews.Where(b => b.Crafter == crafter);

    /// <summary>Brew: draughts from what the survivor brings, cheaper than the shop's, never
    /// stronger (design 12.1: brewing makes them cheaper, not better).</summary>
    public static Quote Brew(CraftCtx x, string draught, int count = 1)
    {
        var r = BrewOf(draught);
        var q = Begin(Verb.Brew, r?.Crafter ?? "", "Brew");
        q.Def = draught;
        q.Count = count = Math.Max(1, count);
        if (r == null) { q.Blocked = "Nobody here brews that."; return q; }
        foreach (var (m, n) in r.Takes) q.Takes[m] = n * count;
        q.Gold = Price(x, r.Crafter, r.Gold) * count;
        q.Gives[draught] = count;
        q.After = Items.Get(draught).Description;
        if (Inventory.Room(x.Ch, draught) < count) q.Blocked = "No room in your pack for it.";
        Afford(x, q);
        return q;
    }

    /// <summary>How many of a draught could be brewed now, up to a limit (for "brew five").</summary>
    public static int CanBrew(CraftCtx x, string draught, int most)
    {
        int n = 0;
        while (n < most && Brew(x, draught, n + 1).Ok) n++;
        return n;
    }

    public static bool HasFlask(CharacterData ch) => Inventory.Count(ch, Rules.Flask.Item) > 0;

    /// <summary>Wenna's flask: bought once; from then on the inn keeps the survivor's draughts topped up.</summary>
    public static Quote BuyFlask(CraftCtx x)
    {
        var f = Rules.Flask;
        var q = Begin(Verb.Buy, f.Crafter, "Her flask");
        q.Def = f.Item;
        q.Gold = Price(x, f.Crafter, f.Gold);
        q.Gives[f.Item] = 1;
        if (HasFlask(x.Ch)) q.Blocked = "You have it.";
        else if (Inventory.Room(x.Ch, f.Item) < 1) q.Blocked = "No room in your pack for it.";
        Afford(x, q);
        return q;
    }

    /// <summary>A night at the inn with the flask: the draughts topped up to the flask's number, a
    /// material each. How many were filled, and whether it ran dry (some were wanted, none filled).</summary>
    public static (int Filled, bool Dry) Refill(CharacterData ch)
    {
        var f = Rules.Flask;
        if (!HasFlask(ch)) return (0, false);
        int want = Math.Max(0, f.Upto - Inventory.Count(ch, f.Draught)), n = 0;
        while (n < want && Inventory.Count(ch, f.Material) >= f.Per && Inventory.Room(ch, f.Draught) > 0)
        {
            Inventory.Take(ch, f.Material, f.Per);
            Inventory.AddToPack(ch, Inventory.Make(ch, f.Draught));
            n++;
        }
        return (n, want > 0 && n == 0);
    }

    /* ------------------------------------------------------- commissions -- */

    /// <summary>The bases the smith can make, each with whether his respect opens it yet and what it asks.</summary>
    public static List<(string Def, bool Open, string? Needs)> Patterns(CraftCtx x)
    {
        var o = new List<(string Def, bool Open, string? Needs)>();
        foreach (var p in Rules.Commission.Patterns)
        {
            bool open = World.Rules.Test(p.When, x.Ctx);
            var ids = p.Calling ? Callings.Archetype(x.Ch.Archetype).Weapons : p.Id != null ? new List<string> { p.Id } : new();
            foreach (var id in ids)
                if (Items.Find(id) != null && o.All(e => e.Def != id)) o.Add((id, open, open ? null : p.Needs));
        }
        return o;
    }

    /// <summary>What a commission makes, before it is made: the piece as it will come off the anvil.</summary>
    public static ItemInstance Pattern(string def, string affix) =>
        new() { Def = def, Rarity = Rules.Commission.Rarity, Affixes = new() { new AffixRoll { Id = affix, Tier = 0 } } };

    /// <summary>What is on the smith's bench for the survivor, and the day it is ready (null: nothing).</summary>
    public static (string Def, string Affix, string Material, int Ready)? Ordered(WorldState w) =>
        w.Fact("commission.def").Str is { Length: > 0 } d
            ? (d, w.Fact("commission.affix").Str ?? "", w.Fact("commission.material").Str ?? "", (int)w.Fact("commission.ready").Number)
            : null;

    /// <summary>"Make me one": a base the smith knows and a material's answer in it, Uncommon, its
    /// affix at grade I and its heat full, ready the next morning (C20: the wait is part of it).</summary>
    public static Quote Commission(CraftCtx x, string def, string material, string affix)
    {
        var c = Rules.Commission;
        var q = Begin(Verb.Commission, c.Crafter, "Make it");
        q.Def = def;
        q.Material = material;
        q.Affix = affix;
        var d = Items.Find(def);
        var pat = Patterns(x).FirstOrDefault(p => p.Def == def);
        if (d == null || pat.Def == null) { q.Blocked = "He doesn't know that pattern."; return q; }
        if (!Rules.Materials.TryGetValue(material, out var r) || r.Crafter != c.Crafter || !r.Into.Contains(affix) || !Fits(d, affix)) { q.Blocked = "That doesn't go in that way."; return q; }
        var made = Pattern(def, affix);
        q.After = $"{Inventory.Name(made)}: {Line(affix, 0)}";
        q.Takes[material] = r.Qty;
        q.Takes[Iron] = c.Iron;
        // What the finished piece would fetch at the shop (Journey.Value's rule): the work is the price.
        q.Gold = Price(x, c.Crafter, (int)Math.Round(d.Value * (1 + 0.6 * Math.Max(0, c.Rarity - d.Rarity)) * 1.15));
        if (!pat.Open) q.Blocked = $"He'll make that at {pat.Needs}.";
        else if (Ordered(x.World) != null) q.Blocked = "He has one on his bench for you already.";
        Afford(x, q);
        return q;
    }

    /// <summary>The morning after: what was ordered, handed over (null if nothing is ready, or the pack
    /// is full and it waits on the bench).</summary>
    public static ItemInstance? Collect(CraftCtx x)
    {
        if (Ordered(x.World) is not { } o || x.World.Day < o.Ready || Items.Find(o.Def) == null) return null;
        var c = Rules.Commission;
        var it = Inventory.Make(x.Ch, o.Def, rarity: c.Rarity, affixes: new() { new AffixRoll { Id = o.Affix, Tier = 0 } });
        if (!Inventory.AddToPack(x.Ch, it)) return null;
        if (Rules.Materials.GetValueOrDefault(o.Material)?.Marks is { } mark) (it.Marks ??= new()).Add(mark);
        (it.History ??= new()).Add(History(x, c.Crafter, "commission", "Made for you by {who}, day {day}"));
        foreach (var k in new[] { "commission.def", "commission.affix", "commission.material", "commission.ready" }) x.World.Facts.Remove(k);
        return it;
    }

    /* ---------------------------------------------------------- settings -- */

    /// <summary>The trophies the survivor carries that this crafter could set into this piece.</summary>
    public static List<string> Settable(CharacterData ch, ItemInstance it, string crafter = "brannoc") =>
        Rules.Settings.Where(kv => kv.Value.Crafter == crafter && Inventory.Count(ch, kv.Key) > 0 && kv.Value.Kinds.Contains(Items.Get(it.Def).Kind))
            .Select(kv => kv.Key).ToList();

    /// <summary>Set a trophy into a piece: its power goes in outside the seams, spends no heat, and the
    /// world can tell (Greymuzzle's fang: the Pack knows it by sight).</summary>
    public static Quote Set(CraftCtx x, ItemInstance it, string trophy, string crafter = "brannoc")
    {
        var q = Begin(Verb.Set, crafter, "Set it");
        q.Def = trophy;
        if (!Rules.Settings.TryGetValue(trophy, out var s) || s.Crafter != crafter) { q.Blocked = "Nobody here sets that."; return q; }
        q.Affix = s.Affix;
        q.After = Line(s.Affix, 0);
        if (!s.Kinds.Contains(Items.Get(it.Def).Kind)) q.Blocked = "It won't sit in this kind of piece.";
        else if (!Workable(it)) q.Blocked = "That's somebody's work. Leave it be.";
        else if (it.Setting != null) q.Blocked = "Something is set in it already.";
        q.Takes[trophy] = 1;
        q.Gold = Price(x, crafter, s.Gold);
        Afford(x, q);
        return q;
    }

    /* ------------------------------------------------------------- doing -- */

    /// <summary>Do a quoted craft that makes something new rather than working a piece: a brew, the
    /// flask, a commission put on the bench. False if it could not be done.</summary>
    public static bool Make(CraftCtx x, Quote q)
    {
        if (!q.Ok || q.Verb is not (Verb.Brew or Verb.Buy or Verb.Commission)) return false;
        var ch = x.Ch;
        if (q.Crafter != "" && Closed(q.Crafter, x.Ctx, q.Verb) is not null) return false;
        foreach (var (m, n) in q.Takes) if (Inventory.Count(ch, m) < n) return false;
        foreach (var (m, n) in q.Gives) if (Inventory.Room(ch, m) < n) return false;
        if (ch.Gold < q.Gold || q.Verb == Verb.Commission && Ordered(x.World) != null) return false;
        foreach (var (m, n) in q.Takes) Inventory.Take(ch, m, n);
        ch.Gold -= q.Gold;
        foreach (var (m, n) in q.Gives)
            for (int k = 0; k < n; k++) Inventory.AddToPack(ch, Inventory.Make(ch, m));
        if (q.Verb == Verb.Commission)
        {
            var w = x.World;
            w.Facts["commission.def"] = q.Def;
            w.Facts["commission.affix"] = q.Affix;
            w.Facts["commission.material"] = q.Material;
            w.Facts["commission.ready"] = w.Day + Rules.Commission.Days;
        }
        if (q.Verb != Verb.Buy) Worked(x, q.Crafter);
        return true;
    }
'''
sub('logic/Rpg/Crafting.cs', [
("""    /* ------------------------------------------------------------- doing -- */
""", NEW),
("""        if (q.Crafter != "" && Closed(q.Crafter, x.Ctx) is not null) return false;
        foreach (var (m, n) in q.Takes) if (Inventory.Count(ch, m) < n) return false;
        if (ch.Gold < q.Gold) return false;""",
"""        if (q.Verb is Verb.Brew or Verb.Buy or Verb.Commission) return Make(x, q);
        if (q.Crafter != "" && Closed(q.Crafter, x.Ctx, q.Verb) is not null) return false;
        foreach (var (m, n) in q.Takes) if (Inventory.Count(ch, m) < n) return false;
        if (ch.Gold < q.Gold) return false;"""),
("""            case Verb.Rekindle:
                it.Heat = Math.Min(it.HeatFull ?? 0, (it.Heat ?? 0) - cost);
                it.Rekindled = (it.Rekindled ?? 0) + 1;
                cost = 0;
                break;
        }""",
"""            case Verb.Rekindle:
                it.Heat = Math.Min(it.HeatFull ?? 0, (it.Heat ?? 0) - cost);
                it.Rekindled = (it.Rekindled ?? 0) + 1;
                cost = 0;
                break;
            case Verb.Set:
            {
                var s = Rules.Settings[q.Def!];
                it.Setting = s.Affix;
                if (s.Mark != null && !(it.Marks?.Contains(s.Mark) ?? false)) (it.Marks ??= new()).Add(s.Mark);
                (it.History ??= new()).Add(History(x, q.Crafter, s.Moment, "Set by {who}, day {day}"));
                cost = 0;
                break;
            }
        }"""),
])
