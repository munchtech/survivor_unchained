using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// A crafter's bench (docs/CRAFTING_DESIGN.md section 14; built from the brief so it can
/// be played, for the UI design lead to restyle). A full page laid out like the shop's
/// counter: the crafter as a person on the left (how they feel about you, their terms);
/// the anvil in the middle, with the chosen piece, its seams and grades, its heat, and
/// every craft that applies, each saying what it takes, the heat it may cost, and what
/// the piece will read after, before the press; what can be worked and the materials
/// pouch on the right. Mouse: click a piece to put it on the anvil, press a craft. Pad:
/// move to a piece, A puts it on the anvil, then move to a craft and A.
/// </summary>
public partial class ForgeScreen : Overlay
{
    public override string Kind => "forge";
    readonly string crafter;
    string? sel;
    /// <summary>The affix place a work-in or a coal goes over (-1: an open seam).</summary>
    int place = -1;
    bool breaking;

    public ForgeScreen(Game g, string crafter) : base(g) { this.crafter = crafter; Nav.Prefer = "worn:0"; }

    CharacterData Ch => G.Journey.Ch;
    CraftCtx X => G.Journey.Craft;

    ItemInstance? Chosen => sel != null ? Inventory.Find(Ch, sel)?.Item : null;

    protected override void Build()
    {
        var def = Crafting.Crafter(crafter);
        var who = Lore.Person(crafter);
        var page = Page(def?.Place ?? "The forge", who != null ? $"{who.Name}, {who.Role.ToLowerInvariant()}" : null, null, "Esc");
        // Something on the anvil from the start: what is in hand.
        if (Chosen == null) sel = Workable().FirstOrDefault()?.Uid;
        Them(Pane(page, new Rect2(0, 0, 400, 920)), def, who);
        Anvil(Pane(page, new Rect2(430, 0, 960, 920)));
        Bench(Pane(page, new Rect2(1420, 0, 420, 920)));
        PageFooter(Controls.Instance.UsingPad
            ? Footer((Act.Confirm, "Put on the anvil, or do it"), (Act.Cancel, "Close"))
            : MouseFooter("Click a piece to put it on the anvil", "every craft says what it takes and what the piece will be before you press", "nothing is ever broken by a craft"));
    }

    /* ------------------------------------------------------- the crafter -- */

    void Them(VBoxContainer v, CrafterDef? def, NpcDef? who)
    {
        if (who?.Person != null)
        {
            var frame = Style.Panel(Style.Well(0));
            frame.CustomMinimumSize = new Vector2(360, 430);
            frame.AddChild(new Portrait(new Vector2I(360, 430), Portrait.Framing.Bust).Of(who.Person, who.Arms, who.Scale ?? 1));
            v.AddChild(frame);
        }
        if (who != null)
        {
            var plaque = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            plaque.AddChild(new Plaque(who.Name, 26, 40));
            v.AddChild(plaque);
            v.AddChild(Style.Label(Style.Cap1(Rules.Attitude(G.Journey.World.Npc(crafter))), Style.TextItalic, Style.Body, Style.InkDim, false, HorizontalAlignment.Center));
            double mod = G.Journey.PriceMod(crafter);
            int pct = (int)Math.Round((mod - 1) * 100);
            v.AddChild(Style.Label(pct == 0 ? "His usual prices" : pct < 0 ? $"Prices {-pct}% under his usual" : $"Prices {pct}% over his usual",
                Style.UiBold, Style.Small, pct < 0 ? Style.Good : pct > 0 ? Style.Bad : Style.Ink, false, HorizontalAlignment.Center));
        }
        var terms = Crafting.TermLines(crafter, G.Journey.Ctx);
        foreach (var t in terms) v.AddChild(Style.Label(t, Style.TextItalic, Style.Small, Style.Good, true, HorizontalAlignment.Center));
        // What it is all made of, in his words.
        v.AddChild(Style.Panel(Style.Slab(14), Style.Label("“Iron for the shape. Fur for the kind.”", Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center)));
        v.AddChild(Style.Label("Every piece has heat: each craft spends some, and when it is gone the piece is set for good. Nothing is ever broken by a craft.",
            Style.TextItalic, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
    }

    /* --------------------------------------------------------- the bench -- */

    IEnumerable<ItemInstance> Workable() =>
        Items.EquipSlots.Select(s => Ch.Equipment[s]).Concat(Ch.Pack).Where(it => it != null && Crafting.Workable(it)).Select(it => it!);

    void Bench(VBoxContainer v)
    {
        v.AddChild(new Section("What you wear", "click to put it on the anvil"));
        var worn = Items.EquipSlots.Select(s => Ch.Equipment[s]).ToList();
        v.AddChild(Grid(worn, "worn"));
        v.AddChild(new Section("Your pack"));
        var pack = Ch.Pack.Where(it => it != null && Items.SlotFor(Items.Get(it.Def)) != null).ToList();
        while (pack.Count < 10 || pack.Count % 5 != 0) pack.Add(null);
        v.AddChild(Style.Scroll(Grid(pack, "pack")));
        v.AddChild(new Section("The pouch", "materials, never in the pack"));
        var pouch = Inventory.Pouch(Ch).Cast<ItemInstance?>().ToList();
        if (pouch.Count == 0) v.AddChild(Style.Label("Nothing yet. The night's fights and the Verge's beasts fill it; breaking down gives old iron.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        else
        {
            var well = Style.Panel(Style.Well(8));
            well.AddChild(ItemViews.Grid(pouch, 5, 72, null, null, null, null, (it, over) => Tip(it != null ? ItemViews.Card(it, Ch, false) : null, over), "pouch"));
            v.AddChild(well);
        }
        var purse = Style.H(Style.Gap2, Glyphs.Icon("coin", 26, Style.GoldHi), Style.Label($"{Math.Floor(Ch.Gold)}", Style.Display, 30, Style.GoldHi), Style.Label("gold", Style.TextItalic, Style.Body, Style.InkDim));
        purse.Alignment = BoxContainer.AlignmentMode.Center;
        v.AddChild(purse);
    }

    Control Grid(List<ItemInstance?> items, string nav)
    {
        var well = Style.Panel(Style.Well(8));
        var g = ItemViews.Grid(items, 5, 72, it => it.Uid == sel, null, it => Choose(it.Uid), it => Choose(it.Uid),
            (it, over) => Tip(it != null && it.Uid != sel ? ItemViews.Card(it, Ch, false) : null, over), nav, null,
            (i, it, view) => { if (it != null && !Crafting.Workable(it)) view.Modulate = new Color(1, 1, 1, 0.3f); });
        well.AddChild(g);
        return well;
    }

    void Choose(string uid)
    {
        if (Inventory.Find(Ch, uid) is not { } loc || !Crafting.Workable(loc.Item)) { Sound.Sfx.Deny(); return; }
        sel = uid;
        place = -1;
        breaking = false;
        Sound.Sfx.Click();
        Refresh();
    }

    /* --------------------------------------------------------- the anvil -- */

    void Anvil(VBoxContainer v)
    {
        var it = Chosen;
        if (it == null)
        {
            v.AddChild(Style.Gap(Style.Gap6));
            v.AddChild(Style.Label("Nothing on the anvil.", Style.Text, Style.Title, Style.Ink, false, HorizontalAlignment.Center));
            v.AddChild(Style.Label("Choose a piece you wear or carry. Plain gear and weapons can be worked; somebody else's named work is left be.", Style.TextItalic, Style.Body, Style.InkDim, true, HorizontalAlignment.Center));
            return;
        }
        var closed = Crafting.Closed(crafter, G.Journey.Ctx);
        var body = Style.V(Style.Gap3);
        body.AddChild(Head(it));
        if (closed != null) body.AddChild(Style.Panel(Style.Slab(12), Style.Label(closed, Style.TextItalic, Style.Body, Style.Bad, true, HorizontalAlignment.Center)));
        body.AddChild(Seams(it));
        if (Crafting.Does(crafter, Verb.WorkIn)) body.AddChild(WorkIn(it));
        if (Crafting.Does(crafter, Verb.Cage)) body.AddChild(Coals(it));
        body.AddChild(Pattern(it));
        var scroll = Style.Scroll(body);
        scroll.CustomMinimumSize = new Vector2(900, 860);
        v.AddChild(scroll);
    }

    Control Head(ItemInstance it)
    {
        var def = Items.Get(it.Def);
        var col = Style.RarityOf(it.Rarity);
        var h = Style.H(Style.Gap4);
        h.AddChild(Style.Panel(Style.Box(new Color(0.03f, 0.03f, 0.04f), col with { A = 0.4f }, 1, 4, 6), ItemPhotos.Icon(def.Icon, 96, col.Lightened(0.25f))));
        var names = Style.V(Style.Gap1);
        names.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        names.AddChild(Style.Label(Inventory.Name(it), Style.TextBold, 26, col, true));
        names.AddChild(Style.H(Style.Gap2, Style.Label($"{Inventory.RarityName(it)} {def.Kind.ToString().ToLowerInvariant()}", Style.Ui, Style.Small, Style.InkDim), Style.Gems(it.Rarity, 7)));
        names.AddChild(HeatBar(it));
        h.AddChild(names);
        return h;
    }

    /// <summary>Its heat, as a bar the ember's colour: how much more it can take.</summary>
    static Control HeatBar(ItemInstance it)
    {
        int heat = it.Heat ?? 0, full = Math.Max(1, it.HeatFull ?? 1);
        var row = Style.H(Style.Gap2);
        var bar = new Control { CustomMinimumSize = new Vector2(360, 14), MouseFilter = MouseFilterEnum.Ignore };
        bar.AddChild(new ColorRect { Color = new Color("#1a1210"), Size = new Vector2(360, 14), MouseFilter = MouseFilterEnum.Ignore });
        bar.AddChild(new ColorRect { Color = heat > 0 ? Style.Ember : Style.InkFaint, Size = new Vector2(360f * Math.Clamp(heat / (float)full, 0, 1), 14), MouseFilter = MouseFilterEnum.Ignore });
        row.AddChild(bar);
        row.AddChild(Style.Label(heat > 0 ? $"Heat {heat} of {full}" : "Set: nothing more can be worked into it", Style.UiBold, Style.Small, heat > 0 ? Style.EmberHi : Style.InkDim));
        return row;
    }

    /// <summary>A cost and its heat, on one line ("4 old iron · 25 gold · heat 3–5").</summary>
    string Cost(Quote q)
    {
        var parts = q.Takes.Select(kv => $"{kv.Value} {Items.Find(kv.Key)?.Name.ToLowerInvariant() ?? kv.Key}").ToList();
        if (q.Gold > 0) parts.Add($"{q.Gold} gold");
        if (q.HeatHi > 0) parts.Add(q.HeatLo == q.HeatHi ? $"heat {q.HeatLo}" : $"heat {q.HeatLo}–{q.HeatHi}");
        else if (q.HeatLo < 0) parts.Add($"+{-q.HeatLo} heat");
        return string.Join("  ·  ", parts);
    }

    /// <summary>A craft as a row: what it does (before and after), what it takes, and the press.</summary>
    Control Row(string title, Quote q, Action press, string? lead = null, Control? icon = null)
    {
        var slab = Style.Panel(Style.Slab(12));
        var h = Style.H(Style.Gap3);
        if (icon != null) h.AddChild(icon);
        var words = Style.V(2);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        if (lead != null) words.AddChild(Style.Label(lead, Style.UiBold, Style.Small, Style.GoldHi, true));
        if (q.Before != null && q.After != null)
            words.AddChild(Style.H(Style.Gap2, Style.Label(q.Before, Style.Ui, Style.Small, Style.InkDim), Style.Label("to", Style.TextItalic, Style.Caption, Style.InkFaint), Style.Label(q.After, Style.UiBold, Style.Small, new Color("#9ad8ff"))));
        else if (q.After != null) words.AddChild(Style.Label(q.After, Style.UiBold, Style.Small, new Color("#9ad8ff"), true));
        words.AddChild(Style.Label(Cost(q), Style.Ui, Style.Caption, q.Ok ? Style.Ink : Style.InkDim, true));
        if (!q.Ok) words.AddChild(Style.Label(q.Blocked!, Style.TextItalic, Style.Caption, Style.Bad, true));
        h.AddChild(words);
        var b = Style.Button(title, q.Ok ? press : () => Sound.Sfx.Deny(), q.Ok, true);
        b.Disabled = !q.Ok;
        b.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        h.AddChild(b);
        slab.AddChild(h);
        return slab;
    }

    void Work(Quote q, Action? sound = null, bool off = false)
    {
        if (!q.Ok || sel == null) { Sound.Sfx.Deny(); return; }
        string uid = sel;
        // Broken down, it leaves the anvil before the page is built again.
        if (off) sel = null;
        (sound ?? Sound.Sfx.Bash)();
        G.Gear((j, b) => j.Work(uid, q, b));
    }

    Control Seams(ItemInstance it)
    {
        var v = Style.V(Style.Gap2);
        int seams = Crafting.Seams(it), cap = Crafting.Cap(it);
        v.AddChild(new Section("Its seams", seams == 0 ? "a plain piece: remake it to open a seam" : $"grades up to {Crafting.Grade(cap)} on a {Inventory.RarityName(it).ToLowerInvariant()} piece"));
        for (int i = 0; i < it.Affixes.Count; i++)
        {
            int k = i;
            var a = it.Affixes[i];
            var ad = Items.Affix(a.Id);
            bool coal = ad?.Kindled != null || ad?.Grants != null;
            var q = Crafting.Temper(X, it, i, crafter);
            string lead = coal ? (ad?.Kindled != null ? "A caged coal" : "A worn skill") : $"Grade {Crafting.Grade(a.Tier)}{(a.Tier >= cap ? ", as high as it goes" : "")}";
            var mark = Style.Button(place == k ? "Working over this" : "Work over this", () => { place = place == k ? -1 : k; Sound.Sfx.Click(); Refresh(); }, place == k, true);
            Nav.Id(mark, $"over:{k}");
            var row = Row("Temper", q, () => Work(q), $"{lead}: {ad?.Text(a.Tier) ?? a.Id}");
            var line = Style.V(2, row);
            if (Crafting.OpenSeams(it) == 0) line.AddChild(Style.H(Style.Gap2, mark, Style.Label("work in or cage over this place (it is lost)", Style.TextItalic, Style.Caption, Style.InkDim)));
            v.AddChild(line);
        }
        for (int i = 0; i < Crafting.OpenSeams(it); i++)
            v.AddChild(Style.Panel(Style.Slab(12), Style.Label("An open seam: work a material in, or cage a coal.", Style.TextItalic, Style.Small, Style.GoldHi, true)));
        return v;
    }

    Control WorkIn(ItemInstance it)
    {
        var v = Style.V(Style.Gap2);
        var choices = Crafting.WorkInChoices(it, crafter);
        v.AddChild(new Section("Work in", "a material becomes its answer: what a place yields answers that place"));
        // Discovery by touch: a material shows once it has been carried.
        var known = choices.Where(c => Inventory.Count(Ch, c.Material) > 0).ToList();
        if (known.Count == 0)
        {
            v.AddChild(Style.Label(choices.Count == 0 ? "Nothing he works goes into this kind of piece." : "Bring him something to work in: wolf pelts, boar hide, red cloth, barrow dust, ember shards.",
                Style.TextItalic, Style.Small, Style.InkDim, true));
            return v;
        }
        foreach (var (m, a) in known)
        {
            int over = Crafting.OpenSeams(it) > 0 ? -1 : place;
            var q = Crafting.WorkIn(X, it, m, a, over, crafter);
            var md = Items.Get(m);
            v.AddChild(Row("Work in", q, () => Work(q), $"{md.Name} (you have {Inventory.Count(Ch, m)}): {Items.Affix(a)?.Name}", ItemPhotos.Icon(md.Icon, 40, Style.InkDim)));
        }
        return v;
    }

    Control Coals(ItemInstance it)
    {
        var v = Style.V(Style.Gap2);
        v.AddChild(new Section("Cage a coal", "a coal from the night, caged: it shapes the ember's draft"));
        if (Inventory.Count(Ch, Crafting.Shard) == 0 && !it.Affixes.Any(a => Items.Affix(a.Id)?.Kindled != null))
        {
            v.AddChild(Style.Label("Ember wants a cage. Bring him shards carried out of the night.", Style.TextItalic, Style.Small, Style.InkDim, true));
            return v;
        }
        if (it.Rarity < Crafting.Rules.Cage.MinRarity)
        {
            v.AddChild(Style.Label("Too plain a piece to hold a coal: rare and up.", Style.TextItalic, Style.Small, Style.InkDim, true));
            return v;
        }
        var wanted = Crafting.Wanted(Ch);
        var cards = Style.H(Style.Gap3);
        foreach (var id in Crafting.Coals(Ch, it, G.Journey.World.Day))
        {
            var a = Items.Affix(id)!;
            var q = Crafting.Cage(X, it, id, place, crafter);
            var card = Style.Panel(Style.Box(new Color("#1d1410"), wanted.Contains(a.Kindled!) ? Style.Ember : Style.Line, 1, 6, 12));
            card.CustomMinimumSize = new Vector2(280, 0);
            var cv = Style.V(Style.Gap2);
            cv.AddChild(Style.Label(a.Name, Style.TextBold, 19, Style.EmberHi, true));
            cv.AddChild(Style.Label(a.Text(0), Style.Ui, Style.Small, Style.Ink, true));
            if (wanted.Contains(a.Kindled!)) cv.AddChild(Style.Label("Your skills evolve with it", Style.UiHeavy, Style.Caption, Style.Ember));
            cv.AddChild(Style.Label(Cost(q), Style.Ui, Style.Caption, q.Ok ? Style.Ink : Style.InkDim, true));
            if (!q.Ok) cv.AddChild(Style.Label(q.Blocked!, Style.TextItalic, Style.Caption, Style.Bad, true));
            var b = Style.Button("Cage it", q.Ok ? () => Work(q, Sound.Sfx.Discovery) : () => Sound.Sfx.Deny(), q.Ok, true);
            b.Disabled = !q.Ok;
            cv.AddChild(b);
            card.AddChild(cv);
            cards.AddChild(card);
        }
        v.AddChild(cards);
        var again = Crafting.Redraw(X, it, crafter);
        v.AddChild(Row("Three more", again, () => Work(again, Sound.Sfx.Click), "Not these: three more coals"));
        return v;
    }

    Control Pattern(ItemInstance it)
    {
        var v = Style.V(Style.Gap2);
        v.AddChild(new Section("The piece itself"));
        if (Crafting.Does(crafter, Verb.Remake))
        {
            var q = Crafting.Remake(X, it, crafter);
            v.AddChild(Row("Remake", q, () => Work(q, () => Sound.Sfx.Loot(true)), q.Title));
        }
        if (Crafting.Does(crafter, Verb.Rekindle))
        {
            var q = Crafting.Rekindle(X, it, crafter);
            v.AddChild(Row("Rekindle", q, () => Work(q, Sound.Sfx.Discovery), "Rekindle: heat back, half its full heat; dearer each time"));
        }
        if (Crafting.Does(crafter, Verb.BreakDown))
        {
            var q = Crafting.BreakDown(X, it);
            string gives = string.Join(", ", q.Gives.Select(kv => $"{kv.Value} {Items.Get(kv.Key).Name.ToLowerInvariant()}"));
            v.AddChild(Row(breaking ? "Break it down for good" : "Break down", q, () =>
            {
                if (!breaking) { breaking = true; Sound.Sfx.Hover(); Refresh(); return; }
                breaking = false;
                Work(q, Sound.Sfx.Shatter, off: true);
            }, $"Break it down for {gives}: it cannot be undone"));
        }
        return v;
    }

    public override bool Key(Act a)
    {
        if (a == Act.Cancel && breaking) { breaking = false; Refresh(); return true; }
        return false;
    }
}
