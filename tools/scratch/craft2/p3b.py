from ed import sub
NEW = '''    /* ----------------------------------------------------------- binding -- */

    /// <summary>A power that can be lifted out of one piece into another: a plain affix. Coals are
    /// the forge's, a worn skill is its piece's, a trophy's power and the slurry's will not let go.</summary>
    public static bool Bindable(AffixDef? d) => d != null && d.Kindled == null && d.Grants == null && !d.Unique;

    /// <summary>What the survivor carries that could give this piece a power: each piece in the pack and
    /// the place of a bindable affix in it that this kind of piece takes.</summary>
    public static List<(ItemInstance Donor, int Index)> Donors(CharacterData ch, ItemInstance it)
    {
        var kind = Items.Get(it.Def).Kind;
        var o = new List<(ItemInstance, int)>();
        foreach (var d in ch.Pack)
        {
            if (d == null || d.Uid == it.Uid || Items.SlotFor(Items.Get(d.Def)) == null) continue;
            for (int k = 0; k < d.Affixes.Count; k++)
                if (Items.Affix(d.Affixes[k].Id) is { } a && Bindable(a) && a.Slots.Contains(kind)) o.Add((d, k));
        }
        return o;
    }

    /// <summary>Bind: one power lifted out of a donor and set in this piece at the donor's grade (to this
    /// piece's cap), in an open seam or in place of a chosen affix. The donor is unmade (design 7.3).</summary>
    public static Quote Bind(CraftCtx x, ItemInstance it, ItemInstance donor, int donorIndex, int replace = -1, string? crafter = null)
    {
        var r = Rules.Bind;
        crafter ??= r.Crafter;
        var q = Begin(Verb.Bind, crafter, "Bind");
        q.Donor = donor.Uid;
        q.Index = replace;
        if (donorIndex < 0 || donorIndex >= donor.Affixes.Count) { q.Blocked = "Choose what to lift out of it."; return q; }
        var roll = donor.Affixes[donorIndex];
        var a = Items.Affix(roll.Id);
        q.Affix = roll.Id;
        q.Grade = Math.Min(roll.Tier, Math.Max(Cap(it), 0));
        q.After = Line(roll.Id, q.Grade);
        if (a?.Kindled != null) { q.Blocked = Line(crafter, "bind.coal") ?? "That one is caged. It will not come out."; return q; }
        if (!Bindable(a)) { q.Blocked = "That will not let go of what holds it."; return q; }
        if (!Fits(Items.Get(it.Def), roll.Id)) { q.Blocked = "It doesn't take to that kind of piece."; return q; }
        if (replace >= 0)
        {
            if (replace >= it.Affixes.Count) { q.Blocked = "Choose what it goes in over."; return q; }
            q.Before = Line(it.Affixes[replace].Id, it.Affixes[replace].Tier);
        }
        else if (OpenSeams(it) == 0) q.Blocked = Seams(it) == 0 ? "No seam to hold it: have it remade first." : "No open seam: choose what it goes in over.";
        if (it.Affixes.Where((b, i) => i != replace).Any(b => b.Id == roll.Id)) q.Blocked ??= "It already has that.";
        if (Inventory.Find(x.Ch, donor.Uid) is not { InPack: true }) q.Blocked ??= "Take it off first: what gives its power is unmade.";
        var (top, _, _) = Terms(crafter, x.Ctx);
        q.Takes[Shard] = r.ShardsPerGrade * (q.Grade + 1);
        q.Gold = Price(x, crafter, r.GoldPerGrade * (q.Grade + 1));
        (q.HeatLo, q.HeatHi) = HeatRange(r.Heat, top);
        Hot(it, q);
        Afford(x, q);
        return q;
    }

    /* ----------------------------------------------------------- the slurry -- */

    public static bool Slurried(ItemInstance it) => it.Marks?.Contains(Rules.Slurry.Mark) == true;

    /// <summary>Snib sells jars while the pump runs and he has been met: three a day.</summary>
    public static Quote BuyJar(CraftCtx x)
    {
        var s = Rules.Slurry;
        var q = Begin(Verb.Buy, s.Crafter, "A jar");
        q.Def = s.Jar;
        q.Gold = Price(x, s.Crafter, s.Gold);
        q.Gives[s.Jar] = 1;
        var w = x.World;
        int sold = (int)w.Fact("slurry.day").Number == w.Day ? (int)w.Fact("slurry.sold").Number : 0;
        if (!World.Rules.Test(s.Sold, x.Ctx)) q.Blocked = "Nobody is selling it.";
        else if (sold >= s.PerDay) q.Blocked = Line(s.Crafter, "jar.none") ?? "No more today.";
        if (q.Blocked == null && x.Ch.Gold < q.Gold) q.Blocked = $"{q.Gold} gold; you have {Math.Floor(x.Ch.Gold)}.";
        return q;
    }

    /// <summary>A jar bought: paid, in the pouch, and counted against the day's three.</summary>
    public static bool Buy(CraftCtx x, Quote q)
    {
        if (!q.Ok || q.Def != Rules.Slurry.Jar || x.Ch.Gold < q.Gold) return false;
        var w = x.World;
        int sold = (int)w.Fact("slurry.day").Number == w.Day ? (int)w.Fact("slurry.sold").Number : 0;
        x.Ch.Gold -= q.Gold;
        Inventory.AddToPack(x.Ch, Inventory.Make(x.Ch, q.Def, 1));
        w.Facts["slurry.day"] = w.Day;
        w.Facts["slurry.sold"] = sold + 1;
        return true;
    }

    /// <summary>Steep: a piece in a jar of the Dig's slurry, by the survivor's own hand. One affix past the
    /// forge's cap (to the bright grade), a slurry affix past the seams, only the veins, or a grade lost;
    /// then it is set for good (design 9). Said in full before the jar is opened.</summary>
    public static Quote Steep(CraftCtx x, ItemInstance it)
    {
        var s = Rules.Slurry;
        var q = Begin(Verb.Steep, "", "Steep in slurry");
        q.Takes[s.Jar] = 1;
        if (!Workable(it)) q.Blocked = "That's somebody's work. Leave it be.";
        else if (Slurried(it)) q.Blocked = "It has been steeped. Once is all it takes.";
        else if (Seams(it) == 0) q.Blocked = "Too plain a piece: there is nothing in it for the slurry to take.";
        else if (Inventory.Count(x.Ch, s.Jar) < 1) q.Blocked = "You have no slurry.";
        q.HeatLo = q.HeatHi = it.Heat ?? 0;
        q.After = "It is set for good after, whatever it comes to.";
        return q;
    }

    /// <summary>The chances of each outcome, as shares of one (for the card that says them).</summary>
    public static IEnumerable<(string Outcome, double Chance)> Odds()
    {
        double total = Math.Max(1, Rules.Slurry.Odds.Values.Sum());
        return Rules.Slurry.Odds.Select(kv => (kv.Key, kv.Value / total));
    }

    static void Steeped(CraftCtx x, ItemInstance it, Quote q, Rng rng)
    {
        var s = Rules.Slurry;
        string pick = rng.Weighted(s.Odds.Keys.ToList(), k => s.Odds[k]);
        var plain = it.Affixes.Select((a, i) => (a, i)).Where(p => Bindable(Items.Affix(p.a.Id))).ToList();
        // Nothing in it to raise or lower: what would have happened to an affix happens past the seams.
        if (pick is "up" or "down" && plain.Count == 0) pick = pick == "up" ? "slurry" : "nothing";
        switch (pick)
        {
            case "up":
            {
                // The lowest-raised first would be kind; the slurry is not: any of them, past the cap, to the bright grade.
                var (a, _) = plain[rng.Int(0, plain.Count - 1)];
                a.Tier = Math.Min(4, a.Tier + 1);
                q.Affix = a.Id;
                break;
            }
            case "down":
            {
                var (a, _) = plain[rng.Int(0, plain.Count - 1)];
                if (a.Tier > 0) a.Tier--; else pick = "nothing";
                q.Affix = a.Id;
                break;
            }
            case "slurry":
            {
                var pool = s.Affixes.Where(id => Items.Affix(id) is { } d && d.Slots.Contains(Items.Get(it.Def).Kind) && it.Affixes.All(b => b.Id != id)).ToList();
                if (pool.Count == 0) { pick = "nothing"; break; }
                var id = pool[rng.Int(0, pool.Count - 1)];
                it.Affixes.Add(new AffixRoll { Id = id, Tier = 0 });
                q.Affix = id;
                break;
            }
        }
        q.Outcome = pick;
        it.Heat = 0;
        (it.Marks ??= new()).Add(s.Mark);
        (it.History ??= new()).Add(History(x, s.Crafter, "steep", "Steeped in the Dig's slurry, day {day}"));
    }

    /* ------------------------------------------------------------- doing -- */
'''
sub('logic/Rpg/Crafting.cs', [
("""    /* ------------------------------------------------------------- doing -- */
""", NEW),
# Doing: bind and steep in Do.
("""        if (q.Verb is Verb.Brew or Verb.Buy or Verb.Commission) return Make(x, q);""",
"""        if (q.Verb is Verb.Brew or Verb.Buy or Verb.Commission) return Make(x, q);
        if (q.Verb == Verb.Steep)
        {
            if (Inventory.Count(ch, Rules.Slurry.Jar) < 1 || Slurried(it)) return false;
            Inventory.Take(ch, Rules.Slurry.Jar, 1);
            Steeped(x, it, q, rng);
            return true;
        }
        if (q.Verb == Verb.Bind && (q.Donor == null || Inventory.Find(ch, q.Donor) is not { InPack: true })) return false;"""),
("""            case Verb.Set:
            {""",
"""            case Verb.Bind:
            {
                var roll = new AffixRoll { Id = q.Affix!, Tier = q.Grade };
                if (q.Index >= 0) it.Affixes[q.Index] = roll; else it.Affixes.Add(roll);
                // The donor is unmade: held over the lamp until it lets go.
                var d = Inventory.Find(ch, q.Donor!)!;
                ch.Pack[d.Index] = null;
                (it.History ??= new()).Add(History(x, q.Crafter, "bind", "Bound by {who}, day {day}"));
                break;
            }
            case Verb.Set:
            {"""),
# Make: Buy for a jar too.
("""        if (!q.Ok || q.Verb is not (Verb.Brew or Verb.Buy or Verb.Commission)) return false;""",
"""        if (!q.Ok || q.Verb is not (Verb.Brew or Verb.Buy or Verb.Commission)) return false;
        if (q.Verb == Verb.Buy && q.Def == Rules.Slurry.Jar) return Buy(x, q);"""),
])
sub('logic/Rpg/Items.cs', [
("""    /// <summary>Given, never rolled: a trophy's power set into a piece (Greymuzzle's fang).</summary>
    public bool Unique;""",
"""    /// <summary>Given, never rolled: a trophy's power set into a piece (Greymuzzle's fang), or what the
    /// slurry leaves in a steeped one.</summary>
    public bool Unique;
    /// <summary>The slurry's: strong, with a price; shown in its sick green.</summary>
    public bool Slurry;"""),
("""        /* Skills worn: fine gear that fights for you. */""",
"""        /* The slurry's, past the seams (design 9): strong, and each with its price. */
        new() { Id = "seeping", Name = "Seeping", Prefix = true, Unique = true, Slurry = true,
            Slots = [ItemKind.Weapon, ItemKind.Offhand, ItemKind.Head, ItemKind.Body, ItemKind.Cloak, ItemKind.Amulet, ItemKind.Ring, ItemKind.Relic],
            Mods = _ => [M(Stat.Damage, ModKind.Inc, 0.2), M(Stat.Healing, ModKind.Inc, -0.15)], Text = _ => "+20% damage; you mend 15% less" },
        new() { Id = "of_the_sump", Name = "of the Sump", Prefix = false, Unique = true, Slurry = true,
            Slots = [ItemKind.Weapon, ItemKind.Offhand, ItemKind.Head, ItemKind.Body, ItemKind.Cloak, ItemKind.Amulet, ItemKind.Ring, ItemKind.Relic],
            Mods = _ => [M(Stat.Area, ModKind.Inc, 0.25), M(Stat.MoveSpeed, ModKind.Inc, -0.1)], Text = _ => "+25% area; you are 10% slower" },
        new() { Id = "green_veined", Name = "Green-Veined", Prefix = true, Unique = true, Slurry = true,
            Slots = [ItemKind.Weapon, ItemKind.Offhand, ItemKind.Head, ItemKind.Body, ItemKind.Cloak, ItemKind.Amulet, ItemKind.Ring, ItemKind.Relic],
            Mods = _ => [M(Stat.CritChance, ModKind.Flat, 0.15), M(Stat.MaxHealth, ModKind.Inc, -0.1)], Text = _ => "+15% critical chance; 10% less health" },

        /* Skills worn: fine gear that fights for you. */"""),
])
