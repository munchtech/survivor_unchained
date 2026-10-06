from ed import sub
sub('logic/Play/JourneyCrafting.cs', [
("""        if (!Crafting.Do(Craft, it, q, craftRng)) { Warn("It could not be done."); return false; }
        if (q.Crafter != "") CraftSaid = Crafting.Speak(Craft, q.Crafter, q.Verb);""",
"""        if (!Crafting.Do(Craft, it, q, craftRng)) { Warn("It could not be done."); return false; }
        // A trophy set has its own words, said the once ("fang.set").
        string? moment = q.Verb == Verb.Set && Crafting.Rules.Settings.GetValueOrDefault(q.Def ?? "") is { } s ? $"{s.Moment}.set" : null;
        if (q.Crafter != "") CraftSaid = Crafting.Speak(Craft, q.Crafter, q.Verb, moment);"""),
("""            Verb.Cage when q.Affix == null => "Three more coals",""",
"""            Verb.Cage when q.Affix == null => "Three more coals",
            Verb.Set => q.After,"""),
("""    /// <summary>What the arena's end carried out goes in the pouch;""",
"""    /// <summary>Do a quoted craft that makes something new (a brew, the flask, a commission put on
    /// the bench); what it did, said. False if it could not be done.</summary>
    public bool Make(Quote q)
    {
        if (!q.Ok) { Warn(q.Blocked!); return false; }
        if (!Crafting.Make(Craft, q)) { Warn("It could not be done."); return false; }
        var brew = q.Verb == Verb.Brew ? Crafting.BrewOf(q.Def!) : null;
        CraftSaid = q.Verb switch
        {
            Verb.Buy => CraftSaid,
            Verb.Commission => Crafting.Line(q.Crafter, "commission.take") is { } l ? new Said(null, l, null) : null,
            _ => Crafting.Speak(Craft, q.Crafter, q.Verb, brew?.Moment, brew?.Say),
        };
        var def = Items.Get(q.Def!);
        string title = q.Verb switch
        {
            Verb.Brew => q.Count == 1 ? def.Name : $"{def.Name} ×{q.Count}",
            Verb.Commission => q.After?.Split(':')[0] ?? def.Name,
            _ => def.Name,
        };
        string? sub = q.Verb switch
        {
            Verb.Brew => $"You carry {Inventory.Count(Ch, q.Def!)}",
            Verb.Commission => $"On {Crafting.Crafter(q.Crafter)?.Name ?? "the"}'s bench: ready tomorrow morning",
            _ => def.Description,
        };
        OnToast(new Toast(ToastKind.Loot, title, sub, def.Icon, q.Verb == Verb.Commission ? Crafting.Rules.Commission.Rarity : def.Rarity));
        OnTouch();
        return true;
    }

    /// <summary>A commission ready on the smith's bench, handed over (null if none is, or the pack is full).</summary>
    public ItemInstance? CollectCommission()
    {
        var it = Crafting.Collect(Craft);
        if (it == null) return null;
        if (Crafting.Line(Crafting.Rules.Commission.Crafter, "commission.ready") is { } l) CraftSaid = new Said(null, l, null);
        OnToast(new Toast(ToastKind.Loot, Inventory.Name(it), "Made for you", Items.Get(it.Def).Icon, it.Rarity));
        OnTouch();
        return it;
    }

    /// <summary>Wenna's flask, filled by the inn overnight: what the morning report says of it.</summary>
    string? Flask()
    {
        var (filled, dry) = Crafting.Refill(Ch);
        string crafter = Crafting.Rules.Flask.Crafter;
        if (filled > 0)
        {
            World.Facts.Remove("flask.dry.said");
            string n = filled switch { 1 => "one draught", 2 => "two draughts", 3 => "three draughts", _ => $"{filled} draughts" };
            return Crafting.Line(crafter, "flask.filled")?.Replace("{n} draughts", n).Replace("{n}", $"{filled}");
        }
        // Dry: said once, until it is filled again (a nag every morning would be a chore).
        if (dry && !World.Fact("flask.dry.said").Truthy)
        {
            World.Facts["flask.dry.said"] = true;
            return Crafting.Line(crafter, "flask.dry");
        }
        return null;
    }

    /// <summary>What the arena's end carried out goes in the pouch;"""),
])
sub('logic/Play/Journey.cs', [
("""    int Draughts => Inventory.Count(Ch, "health_draught");

    /// <summary>R: drink a health draught.</summary>
    public void Quaff(Battle? b)
    {
        if (b == null || !b.Player.Alive) return;
        if (Draughts == 0) { Warn("No draughts left"); return; }
        if (b.Player.Hp >= b.MaxHp - 0.5) { Warn("You are unhurt"); return; }
        Inventory.Take(Ch, "health_draught", 1);
        b.HealPlayer(b.MaxHp * (Items.Get("health_draught").Consumable?.Heal ?? 0.4), "draught");
        OnTouch();
    }""",
"""    const string Draught = "health_draught", Moonpetal = "moonpetal_draught";

    /// <summary>The draughts the draught key can drink, of either kind (the HUD's count).</summary>
    public int Draughts => Inventory.Count(Ch, Draught) + Inventory.Count(Ch, Moonpetal);

    /// <summary>R: drink a draught: the one that fits the wound. The moonpetal (60%) only for a deep
    /// one, 55% of health or more gone, so a rare draught is not spent on a scratch (combat's rule).</summary>
    public void Quaff(Battle? b)
    {
        if (b == null || !b.Player.Alive) return;
        if (Draughts == 0) { Warn("No draughts left"); return; }
        if (b.Player.Hp >= b.MaxHp - 0.5) { Warn("You are unhurt"); return; }
        bool deep = 1 - b.Player.Hp / b.MaxHp >= 0.55, moon = Inventory.Count(Ch, Moonpetal) > 0, plain = Inventory.Count(Ch, Draught) > 0;
        string pick = (deep && moon) || !plain ? Moonpetal : Draught;
        Inventory.Take(Ch, pick, 1);
        b.HealPlayer(b.MaxHp * (Items.Get(pick).Consumable?.Heal ?? 0.4), "draught");
        OnTouch();
    }"""),
("""        if (lines.Count == 0) lines.Add("A quiet night. Rook's bread is hot, and nobody died.");""",
"""        if (Flask() is { } flask) lines.Add(flask);
        if (lines.Count == 0) lines.Add("A quiet night. Rook's bread is hot, and nobody died.");"""),
])
sub('src/Game/Game.cs', [
("""            hud.Frame(Battle, ch.Gold, Inventory.Count(ch, "health_draught"), (ch.Level, ch.Xp / Character.XpForLevel(ch.Level)));""",
"""            hud.Frame(Battle, ch.Gold, Journey.Draughts, (ch.Level, ch.Xp / Character.XpForLevel(ch.Level)));"""),
])
sub('src/Game/GameMenus.cs', [
("""            case "craft": if (talkNpc is string who) afterTalk = $"forge:{who}"; return false;""",
"""            case "craft": if (talkNpc is string who) afterTalk = $"forge:{who}"; return false;
            // A still-room: the crafter's brews and wares, beside the world (Wenna's).
            case "still": if (talkNpc is string brewer) afterTalk = $"still:{brewer}"; return false;"""),
("""            _ when kind.StartsWith("forge:") => new ForgeScreen(this, kind[6..]),""",
"""            _ when kind.StartsWith("forge:") => new ForgeScreen(this, kind[6..]),
            _ when kind.StartsWith("still:") => new StillRoom(this, kind[6..]),"""),
])
