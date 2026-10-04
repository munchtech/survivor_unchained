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
/// counter: the crafter as a person on the left (how they feel about you, the terms they
/// give and the ones still to earn); the anvil in the middle; what can be worked and the
/// materials pouch on the right.
///
/// The anvil works one seam at a time, as Last Epoch's forge does: the piece's seams are
/// listed, one is chosen, and only the crafts that apply to it are offered under it, each
/// saying what it takes, the heat it may cost and what the seam will read after. What
/// works on the whole piece (remake, rekindle, break down) sits at the foot. The heat gauge
/// shows, while a craft is under the pointer or the focus, what that craft may spend.
/// Mouse: click a piece to put it on the anvil, click a seam, press a craft. Pad: the same
/// with the stick and A.
/// </summary>
public partial class ForgeScreen : Overlay
{
    public override string Kind => "forge";
    readonly string crafter;
    string? sel;
    /// <summary>The seam chosen on the anvil: an affix's place, or past the affixes an open
    /// seam (-1: the one most worth working, chosen when the piece is put down).</summary>
    int seam = -1;
    bool breaking;
    HeatGauge? gauge;
    /// <summary>Why the crafter is not working now (the forge banked), said once at the top.</summary>
    string? closed;

    // --focus ID: that control has the focus first (with --pad, pictures of a craft's heat shown).
    public ForgeScreen(Game g, string crafter) : base(g)
    {
        this.crafter = crafter;
        Nav.Prefer = Args.Get("focus") ?? "worn:0";
        // Sitting down at the bench: a greeting, not what was said over the last craft.
        g.Journey.CraftSaid = null;
    }

    CharacterData Ch => G.Journey.Ch;
    CraftCtx X => G.Journey.Craft;

    ItemInstance? Chosen => sel != null ? Inventory.Find(Ch, sel)?.Item : null;

    protected override void Build()
    {
        var def = Crafting.Crafter(crafter);
        var who = Lore.Person(crafter);
        var page = Page(def?.Place ?? "The forge", who != null ? $"{who.Name}, {who.Role.ToLowerInvariant()}" : null, null, "Esc");
        // Something on the anvil from the start: what is in hand (--anvil DEF: that piece, for pictures).
        if (Chosen == null)
        {
            sel = (Workable().FirstOrDefault(it => it.Def == Args.Get("anvil")) ?? Workable().FirstOrDefault())?.Uid;
            seam = -1;
        }
        closed = Crafting.Closed(crafter, G.Journey.Ctx);
        Them(Pane(page, new Rect2(0, 0, 400, 920)), def, who);
        Anvil(Pane(page, new Rect2(430, 0, 960, 920)));
        Bench(Pane(page, new Rect2(1420, 0, 420, 920)));
        PageFooter(Controls.Instance.UsingPad
            ? Footer((Act.Confirm, "Choose, or do it"), (Act.Cancel, "Close"))
            : MouseFooter("Click a piece to put it on the anvil, then a seam", "every craft says what it takes and what it will make before you press", "nothing is ever broken by a craft"));
    }

    /* ------------------------------------------------------- the crafter -- */

    void Them(VBoxContainer v, CrafterDef? def, NpcDef? who)
    {
        if (who?.Person != null)
        {
            var frame = Style.Panel(Style.Well(0));
            frame.CustomMinimumSize = new Vector2(360, 380);
            frame.AddChild(new Portrait(new Vector2I(360, 380), Portrait.Framing.Bust).Of(who.Person, who.Arms, who.Scale ?? 1));
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
        // His terms: those he gives now, and the way up to the rest (C18: standing sets the terms).
        var ladder = Crafting.TermLadder(crafter, G.Journey.Ctx);
        if (ladder.Count > 0)
        {
            var npc = G.Journey.World.Npc(crafter);
            v.AddChild(new Section("His terms", $"his respect for you: {npc.Respect:0}"));
            foreach (var (line, fx, needs, met) in ladder)
            {
                var words = Style.V(0, Style.Label(line, Style.TextItalic, Style.Small, met ? Style.Good : Style.InkDim, true),
                    Style.Label(met || needs == null ? Style.Cap1(fx) : $"{Style.Cap1(fx)}, at {needs}", Style.Ui, Style.Caption, met ? Style.Ink : Style.InkFaint, true));
                words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
                v.AddChild(Style.H(Style.Gap2, Glyphs.Icon(met ? "flame" : "lock", 18, met ? Style.Ember : Style.InkFaint), words));
            }
            if (def is { RespectPerCraft: > 0 })
                v.AddChild(Style.Label("He likes work: every craft he does for you raises his respect a little.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        }
        v.AddChild(Style.Gap(4));
        // What he says: over the last craft done, or a greeting (the story lead's words, in data).
        var said = G.Journey.CraftSaid ?? new Said(null, Crafting.Line(crafter, "greet", G.Journey.World.Day), null);
        var box = Style.V(Style.Gap1);
        if (said.Before != null) box.AddChild(Style.Label(said.Before, Style.TextItalic, Style.Small, Style.InkDim, true, HorizontalAlignment.Center));
        if (said.Line != null) box.AddChild(Style.Label($"“{said.Line}”", Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center));
        if (said.After != null) box.AddChild(Style.Label(said.After, Style.TextItalic, Style.Small, Style.InkDim, true, HorizontalAlignment.Center));
        if (box.GetChildCount() > 0) v.AddChild(Style.Panel(Style.Slab(12), box));
    }

    /* --------------------------------------------------------- the bench -- */

    IEnumerable<ItemInstance> Workable() =>
        Items.EquipSlots.Select(s => Ch.Equipment[s]).Concat(Ch.Pack).Where(it => it != null && Crafting.Workable(it)).Select(it => it!);

    void Bench(VBoxContainer v)
    {
        v.AddChild(new Section("What you wear", "choose a piece"));
        var worn = new GridContainer { Columns = 5, MouseFilter = MouseFilterEnum.Ignore };
        worn.AddThemeConstantOverride("h_separation", 5);
        worn.AddThemeConstantOverride("v_separation", 5);
        int i = 0;
        foreach (var s in Items.EquipSlots)
        {
            var it = Ch.Equipment[s];
            var (name, glyph) = InventoryScreen.Slots[s];
            var view = ItemViews.Slot(it, 72, it != null && it.Uid == sel, null, false, it != null ? () => Choose(it.Uid) : null, null,
                over => Tip(it != null && it.Uid != sel ? ItemViews.Card(it, Ch, false) : null, over), glyph, name, $"worn:{i++}");
            if (it != null && !Crafting.Workable(it)) view.Modulate = new Color(1, 1, 1, 0.35f);
            worn.AddChild(view);
        }
        v.AddChild(Style.Panel(Style.Well(8), worn));

        var pack = Ch.Pack.Where(it => it != null && Items.SlotFor(Items.Get(it.Def)) != null).ToList();
        v.AddChild(new Section("Your pack", pack.Count == 0 ? "no gear in it" : null));
        while (pack.Count < 10 || pack.Count % 5 != 0) pack.Add(null);
        v.AddChild(Grid(pack, "pack"));

        v.AddChild(new Section("The pouch", "materials, never in the pack"));
        var pouch = Inventory.Pouch(Ch).Cast<ItemInstance?>().ToList();
        if (pouch.Count == 0)
            v.AddChild(Style.Label("Nothing yet. The night's fights and the Verge's beasts fill it; breaking gear down gives old iron.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        else
        {
            while (pouch.Count % 5 != 0) pouch.Add(null);
            v.AddChild(Style.Panel(Style.Well(8), ItemViews.Grid(pouch, 5, 72, null, null, null, null, (it, over) => Tip(it != null ? ItemViews.Card(it, Ch, false) : null, over), "pouch")));
        }
        var room = new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore };
        v.AddChild(room);
        var purse = Style.H(Style.Gap2, Glyphs.Icon("coin", 26, Style.GoldHi), Style.Label($"{Math.Floor(Ch.Gold)}", Style.Display, 30, Style.GoldHi), Style.Label("gold", Style.TextItalic, Style.Body, Style.InkDim));
        purse.Alignment = BoxContainer.AlignmentMode.Center;
        v.AddChild(purse);
    }

    Control Grid(List<ItemInstance?> items, string nav)
    {
        var g = ItemViews.Grid(items, 5, 72, it => it.Uid == sel, null, it => Choose(it.Uid), it => Choose(it.Uid),
            (it, over) => Tip(it != null && it.Uid != sel ? ItemViews.Card(it, Ch, false) : null, over), nav, null,
            (i, it, view) => { if (it != null && !Crafting.Workable(it)) view.Modulate = new Color(1, 1, 1, 0.35f); });
        return Style.Panel(Style.Well(8), g);
    }

    void Choose(string uid)
    {
        if (Inventory.Find(Ch, uid) is not { } loc || !Crafting.Workable(loc.Item)) { Sound.Sfx.Deny(); return; }
        sel = uid;
        seam = -1;
        breaking = false;
        Sound.Sfx.Click();
        Refresh();
    }

    void Pick(int k)
    {
        if (seam == k) return;
        seam = k;
        breaking = false;
        Sound.Sfx.Click();
        Refresh();
    }

    /* --------------------------------------------------------- the anvil -- */

    static int Places(ItemInstance it) => Math.Max(Crafting.Seams(it), it.Affixes.Count);

    static bool Plain(AffixDef? d) => d != null && d.Kindled == null && d.Grants == null;

    /// <summary>The seam most worth working when a piece is put down: an affix that can still be
    /// tempered, else an open seam, else the first.</summary>
    static int DefaultSeam(ItemInstance it)
    {
        int cap = Crafting.Cap(it);
        for (int k = 0; k < it.Affixes.Count; k++)
            if (Plain(Items.Affix(it.Affixes[k].Id)) && it.Affixes[k].Tier < cap) return k;
        return Crafting.OpenSeams(it) > 0 ? it.Affixes.Count : 0;
    }

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
        if (seam < 0 || seam >= Places(it)) seam = Places(it) > 0 ? DefaultSeam(it) : -1;
        var body = Style.V(Style.Gap3);
        body.AddChild(Head(it));
        if (closed != null) body.AddChild(Style.Panel(Style.Slab(12), Style.Label(closed, Style.TextItalic, Style.Body, Style.Bad, true, HorizontalAlignment.Center)));
        body.AddChild(SeamList(it));
        if (seam >= 0) body.AddChild(AtSeam(it));
        body.AddChild(Whole(it));
        var scroll = Style.Scroll(body);
        scroll.CustomMinimumSize = new Vector2(920, 880);
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
        gauge = new HeatGauge(it);
        names.AddChild(gauge);
        h.AddChild(names);
        return h;
    }

    /* ---------------------------------------------------------- the seams -- */

    Control SeamList(ItemInstance it)
    {
        var v = Style.V(Style.Gap1);
        int cap = Crafting.Cap(it), places = Places(it);
        string rarity = Inventory.RarityName(it).ToLowerInvariant();
        if (places == 0)
        {
            v.AddChild(new Section("Its seams"));
            // What a seam could take once it is open, from what is in the pouch (discovery by touch).
            var could = Crafting.WorkInChoices(it, crafter).Where(c => Inventory.Count(Ch, c.Material) > 0)
                .Select(c => $"{Items.Affix(c.Affix)?.Name} from {Items.Find(c.Material)?.Plural ?? c.Material}").ToList();
            v.AddChild(Quiet("A plain piece: no seams to work. Remade on a better pattern, it opens one."
                + (could.Count > 0 ? $" Then he could work in {string.Join(", ", could.Take(could.Count - 1))}{(could.Count > 1 ? " or " : "")}{could[^1]}." : "")));
            return v;
        }
        v.AddChild(new Section("Its seams", $"choose one to work  ·  grades to {Crafting.Grade(cap)} on {Crafting.Article(rarity)} piece"));
        for (int k = 0; k < places; k++) v.AddChild(SeamRow(it, k, cap));
        return v;
    }

    Control SeamRow(ItemInstance it, int k, int cap)
    {
        bool open = k >= it.Affixes.Count;
        var a = open ? null : it.Affixes[k];
        var ad = a != null ? Items.Affix(a.Id) : null;
        bool coal = ad?.Kindled != null, skill = ad?.Grants != null, on = k == seam;
        var panel = Style.Panel(Style.Box(on ? new Color("#2a1c12") : new Color("#141118"), on ? Style.Focus : Style.Line with { A = 0.25f }, on ? 2 : 1, 5, 10));
        panel.MouseFilter = MouseFilterEnum.Stop;
        var h = Style.H(Style.Gap3);
        h.AddChild(new GradeBadge(open ? GradeBadge.Mark.Open : coal ? GradeBadge.Mark.Coal : skill ? GradeBadge.Mark.Skill : GradeBadge.Mark.Grade, a?.Tier ?? 0, cap));
        var words = Style.V(1);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        words.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        string title = open ? "An open seam" : ad?.Text(a!.Tier) ?? a!.Id;
        string rarity = Inventory.RarityName(it).ToLowerInvariant();
        string note = open ? "work a material in, or cage a coal"
            : coal ? $"{ad!.Name}: a caged coal, it shapes the ember's draft"
            : skill ? $"{ad!.Name}: a worn skill, it has no grades"
            : a!.Tier >= cap ? $"{ad?.Name}  ·  grade {Crafting.Grade(a.Tier)}, as fine as {Crafting.Article(rarity)} piece is made"
            : $"{ad?.Name}  ·  grade {Crafting.Grade(a.Tier)}; tempers to {Crafting.Grade(cap)}";
        words.AddChild(Style.Label(title, Style.UiBold, Style.Body, open ? Style.GoldHi : coal ? Style.EmberHi : Style.Ink, true));
        words.AddChild(Style.Label(note, Style.TextItalic, Style.Caption, Style.InkDim, true));
        h.AddChild(words);
        if (on) h.AddChild(Style.Label("at the anvil", Style.UiHeavy, Style.Badge, Style.Focus));
        panel.AddChild(h);
        panel.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) Pick(k); };
        Nav.Mark(panel, $"seam:{k}", () => Pick(k));
        return panel;
    }

    /// <summary>The crafts for the chosen seam: temper it, work a material in, cage a coal.</summary>
    Control AtSeam(ItemInstance it)
    {
        var v = Style.V(Style.Gap2);
        int k = seam;
        bool open = k >= it.Affixes.Count;
        var a = open ? null : it.Affixes[k];
        var ad = a != null ? Items.Affix(a.Id) : null;
        bool coal = ad?.Kindled != null;
        if (Plain(ad))
        {
            v.AddChild(new Section("Temper", "the same, a grade finer"));
            int cap = Crafting.Cap(it);
            if (a!.Tier >= cap)
                v.AddChild(Quiet(it.Rarity < Crafting.Rules.RemakeCap
                    ? $"Grade {Crafting.Grade(a.Tier)} is as fine as {Crafting.Article(Inventory.RarityName(it).ToLowerInvariant())} piece is made. Remade on a better pattern, it could be tempered further."
                    : $"Grade {Crafting.Grade(a.Tier)} is as fine as the forge makes it. Finer is the world's to give."));
            else
            {
                var q = Crafting.Temper(X, it, k, crafter);
                v.AddChild(Craft("Temper", q, () => Work(q), q.Title, null, "temper"));
            }
        }
        if (Crafting.Does(crafter, Verb.WorkIn)) v.AddChild(WorkIn(it, open ? -1 : k, ad));
        if (Crafting.Does(crafter, Verb.Cage)) v.AddChild(Coals(it, k, open, coal));
        return v;
    }

    Control WorkIn(ItemInstance it, int over, AffixDef? lost)
    {
        var v = Style.V(Style.Gap2);
        var choices = Crafting.WorkInChoices(it, crafter);
        v.AddChild(new Section("Work in", lost != null ? $"over {lost.Name}, which is lost" : "a material becomes its answer: what a place yields answers that place"));
        // Discovery by touch: a material shows once it is in the pouch.
        var known = choices.Where(c => Inventory.Count(Ch, c.Material) > 0).ToList();
        if (known.Count == 0)
        {
            v.AddChild(Quiet(choices.Count == 0 ? "Nothing he works goes into this kind of piece."
                : $"Bring him something to work in: {string.Join(", ", choices.Select(c => Items.Find(c.Material)?.Plural ?? c.Material).Distinct())}."));
            return v;
        }
        // Two to a row, each only what it makes: what it goes in over is said once, above.
        var grid = new GridContainer { Columns = 2, MouseFilter = MouseFilterEnum.Ignore };
        grid.AddThemeConstantOverride("h_separation", Style.Gap2);
        grid.AddThemeConstantOverride("v_separation", Style.Gap2);
        foreach (var (m, a) in known)
        {
            // An answer it already has, in another seam or in this one, is no choice.
            if (it.Affixes.Any(x => x.Id == a)) continue;
            var q = Crafting.WorkIn(X, it, m, a, over, crafter);
            q.Before = null;
            var md = Items.Get(m);
            var card = Craft("Work in", q, () => Work(q), $"{md.Name}: {Items.Affix(a)?.Name}", ItemPhotos.Icon(md.Icon, 44, Style.InkDim), $"workin:{m}:{a}");
            card.CustomMinimumSize = new Vector2(452, 0);
            grid.AddChild(card);
        }
        v.AddChild(grid);
        return v;
    }

    Control Coals(ItemInstance it, int k, bool open, bool coal)
    {
        var v = Style.V(Style.Gap2);
        v.AddChild(new Section("Cage a coal", coal ? "another in its place: the coal it holds goes out" : "a coal from the night, caged: it shapes the ember's draft"));
        int held = it.Affixes.FindIndex(x => Items.Affix(x.Id)?.Kindled != null);
        if (Inventory.Count(Ch, Crafting.Shard) == 0 && held < 0)
        {
            v.AddChild(Quiet("Ember wants a cage. Bring him shards carried out of the night."));
            return v;
        }
        if (it.Rarity < Crafting.Rules.Cage.MinRarity)
        {
            v.AddChild(Quiet("Too plain a piece to hold a coal: rare and up."));
            return v;
        }
        // One coal a piece: it goes where the old one sat.
        if (held >= 0 && held != k)
        {
            v.AddChild(Quiet("Its coal sits in another seam. Choose that seam to cage another in its place."));
            return v;
        }
        var wanted = Crafting.Wanted(Ch);
        var cards = Style.H(Style.Gap3);
        int n = 0;
        foreach (var id in Crafting.Coals(Ch, it, G.Journey.World.Day))
        {
            var a = Items.Affix(id)!;
            var q = Crafting.Cage(X, it, id, open ? -1 : k, crafter);
            bool wants = wanted.Contains(a.Kindled!);
            var card = Style.Panel(Style.Box(new Color("#1d1410"), wants ? Style.Ember : Style.Line, wants ? 2 : 1, 6, 12));
            card.CustomMinimumSize = new Vector2(290, 0);
            var cv = Style.V(Style.Gap2);
            cv.AddChild(Style.Label(a.Name, Style.TextBold, 19, Style.EmberHi, true));
            cv.AddChild(Style.Label(a.Text(0), Style.Ui, Style.Small, Style.Ink, true));
            if (wants) cv.AddChild(Style.Label("Your skills evolve with it", Style.UiHeavy, Style.Caption, Style.Ember));
            var room = new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore };
            cv.AddChild(room);
            cv.AddChild(Style.Label(Cost(q), Style.Ui, Style.Caption, q.Ok ? Style.Ink : Style.InkDim, true));
            if (!q.Ok && q.Blocked != closed) cv.AddChild(Style.Label(q.Blocked!, Style.TextItalic, Style.Caption, Style.Bad, true));
            cv.AddChild(Press(Style.Button("Cage it", null, q.Ok, true), q, () => Work(q, Sound.Sfx.Discovery), $"coal:{n++}"));
            card.AddChild(cv);
            cards.AddChild(card);
        }
        v.AddChild(cards);
        var again = Crafting.Redraw(X, it, crafter);
        v.AddChild(Craft("Three more", again, () => Work(again, Sound.Sfx.Click), "Not these: three more coals", null, "redraw"));
        return v;
    }

    /// <summary>What works on the whole piece: a better pattern, heat back, or the iron in it.</summary>
    Control Whole(ItemInstance it)
    {
        var v = Style.V(Style.Gap2);
        v.AddChild(new Section("The piece itself"));
        var row = Style.H(Style.Gap3);
        if (Crafting.Does(crafter, Verb.Remake))
        {
            var q = Crafting.Remake(X, it, crafter);
            bool top = q.Blocked != null && q.Takes.Count == 0;
            row.AddChild(Tile(q.Title, top ? null : q.After, q, () => Work(q, () => Sound.Sfx.Loot(true)), "Remake", "remake", top ? q.Blocked : null));
        }
        if (Crafting.Does(crafter, Verb.Rekindle))
        {
            var q = Crafting.Rekindle(X, it, crafter);
            bool full = it.Heat is int h && h >= (it.HeatFull ?? 0);
            row.AddChild(Tile("Rekindle", full ? null : q.After, q, () => Work(q, Sound.Sfx.Discovery), "Rekindle", "rekindle",
                full ? "As hot as it gets. When its heat runs low, ember shards bring half of it back, dearer each time." : null));
        }
        if (Crafting.Does(crafter, Verb.BreakDown))
        {
            var q = Crafting.BreakDown(X, it, crafter);
            string gives = string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value)));
            bool worn = Inventory.Find(Ch, it.Uid) is { InPack: false };
            row.AddChild(Tile(breaking ? "Break it down for good?" : "Break down", $"For {gives}. It cannot be undone.", q, () =>
            {
                if (!breaking) { breaking = true; Sound.Sfx.Hover(); Refresh(); return; }
                breaking = false;
                Work(q, Sound.Sfx.Shatter, off: true);
            }, breaking ? "Break it" : "Break down", "break", worn ? "Worn: take it off first to break it down." : q.Ok ? null : q.Blocked));
        }
        v.AddChild(row);
        return v;
    }

    /* ----------------------------------------------------------- pieces -- */

    /// <summary>Something said quietly: why a craft is not here, or what would open it.</summary>
    static Control Quiet(string text) => Style.Panel(Style.Slab(12), Style.Label(text, Style.TextItalic, Style.Small, Style.InkDim, true));

    /// <summary>A cost and its heat, on one line ("4 old iron · 25 gold · heat 3–5").</summary>
    static string Cost(Quote q)
    {
        var parts = q.Takes.Select(kv => Items.Several(kv.Key, kv.Value)).ToList();
        if (q.Gold > 0) parts.Add($"{q.Gold} gold");
        if (q.HeatHi > 0) parts.Add(q.HeatLo == q.HeatHi ? $"heat {q.HeatLo}" : $"heat {q.HeatLo}–{q.HeatHi}");
        else if (q.HeatLo < 0) parts.Add($"+{-q.HeatLo} heat");
        return string.Join("  ·  ", parts);
    }

    /// <summary>A craft's press: it does the craft when it can, and while under the pointer or
    /// the focus the heat gauge shows what it may spend.</summary>
    Button Press(Button b, Quote q, Action act, string navId)
    {
        b.Disabled = !q.Ok;
        Action press = q.Ok ? act : () => Sound.Sfx.Deny();
        b.Pressed += press;
        void Show() => gauge?.Preview(q.HeatLo, q.HeatHi, q.Verb == Verb.Remake);
        void Hide() => gauge?.Clear();
        b.MouseEntered += Show;
        b.MouseExited += Hide;
        Nav.Mark(b, navId, press, focus: Show, blur: Hide);
        return b;
    }

    /// <summary>A craft as a row: what it does (before and after), what it takes, and the press.</summary>
    Control Craft(string title, Quote q, Action act, string lead, Control? icon, string navId)
    {
        var slab = Style.Panel(Style.Slab(12));
        var h = Style.H(Style.Gap3);
        if (icon != null) h.AddChild(icon);
        var words = Style.V(2);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        words.AddChild(Style.Label(lead, Style.UiBold, Style.Small, Style.GoldHi, true));
        if (q.Before != null && q.After != null)
            words.AddChild(Style.H(Style.Gap2, Style.Label(q.Before, Style.Ui, Style.Small, Style.InkDim), Style.Label("to", Style.TextItalic, Style.Caption, Style.InkFaint), Style.Label(q.After, Style.UiBold, Style.Small, new Color("#9ad8ff"))));
        else if (q.After != null) words.AddChild(Style.Label(q.After, Style.UiBold, Style.Small, new Color("#9ad8ff"), true));
        words.AddChild(Style.Label(Cost(q), Style.Ui, Style.Caption, q.Ok ? Style.Ink : Style.InkDim, true));
        if (!q.Ok && q.Blocked != closed) words.AddChild(Style.Label(q.Blocked!, Style.TextItalic, Style.Caption, Style.Bad, true));
        h.AddChild(words);
        var b = Press(Style.Button(title, null, q.Ok, true), q, act, navId);
        b.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        h.AddChild(b);
        slab.AddChild(h);
        return slab;
    }

    /// <summary>A craft on the whole piece, as one of three tiles side by side; quiet when it
    /// does not apply now (said why), with no press.</summary>
    Control Tile(string title, string? after, Quote q, Action act, string button, string navId, string? quiet)
    {
        var slab = Style.Panel(Style.Slab(12));
        slab.CustomMinimumSize = new Vector2(292, 0);
        slab.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var v = Style.V(3);
        v.AddChild(Style.Label(title, Style.UiBold, Style.Small, quiet != null ? Style.InkDim : Style.GoldHi, true));
        if (quiet != null)
        {
            v.AddChild(Style.Label(quiet, Style.TextItalic, Style.Caption, Style.InkDim, true));
            slab.AddChild(v);
            return slab;
        }
        if (after != null) v.AddChild(Style.Label(after, Style.UiBold, Style.Small, new Color("#9ad8ff"), true));
        var room = new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore };
        v.AddChild(room);
        string cost = Cost(q);
        if (cost != "") v.AddChild(Style.Label(cost, Style.Ui, Style.Caption, q.Ok ? Style.Ink : Style.InkDim, true));
        if (!q.Ok && q.Blocked != closed) v.AddChild(Style.Label(q.Blocked!, Style.TextItalic, Style.Caption, Style.Bad, true));
        var b = Press(Style.Button(button, null, q.Ok, true), q, act, navId);
        b.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
        v.AddChild(b);
        slab.AddChild(v);
        return slab;
    }

    void Work(Quote q, Action? sound = null, bool off = false)
    {
        if (!q.Ok || sel == null) { Sound.Sfx.Deny(); return; }
        string uid = sel;
        // Broken down, it leaves the anvil before the page is built again.
        if (off) { sel = null; seam = -1; }
        (sound ?? Sound.Sfx.Bash)();
        G.Gear((j, b) => j.Work(uid, q, b));
    }

    public override bool Key(Act a)
    {
        if (a == Act.Cancel && breaking) { breaking = false; Refresh(); return true; }
        return false;
    }
}

/// <summary>
/// A seam's mark at the head of its row: a grade as its numeral, coloured as the rarity of
/// the same rank (grade IV reads as epic), with pips under it for the grades it has and the
/// ones it can still be tempered to; a caged coal as a flame; an open seam as a gap waiting.
/// </summary>
public partial class GradeBadge : Control
{
    public enum Mark { Grade, Coal, Skill, Open }
    readonly Mark mark;
    readonly int tier, cap;

    public GradeBadge(Mark mark, int tier, int cap)
    {
        this.mark = mark;
        this.tier = tier;
        this.cap = cap;
        CustomMinimumSize = new Vector2(54, 54);
        MouseFilter = MouseFilterEnum.Ignore;
    }

    public override void _Draw()
    {
        var r = new Rect2(Vector2.Zero, Size);
        var col = mark switch { Mark.Coal => Style.Ember, Mark.Open => Style.GoldDim, Mark.Skill => Style.Day, _ => Style.RarityOf(tier) };
        DrawRect(r, new Color(0.04f, 0.035f, 0.05f, 0.95f));
        if (mark == Mark.Open)
        {
            // A gap waiting: a dashed frame and a cross.
            for (int i = 0; i < 4; i++)
            {
                var a = new[] { r.Position, r.Position + new Vector2(r.Size.X, 0), r.End, r.Position + new Vector2(0, r.Size.Y) };
                DrawDashedLine(a[i], a[(i + 1) % 4], col, 1.5f, 5);
            }
            var c = r.GetCenter();
            DrawLine(c + new Vector2(-9, 0), c + new Vector2(9, 0), col, 2);
            DrawLine(c + new Vector2(0, -9), c + new Vector2(0, 9), col, 2);
            return;
        }
        DrawRect(r, col with { A = 0.7f }, false, 1.5f);
        if (mark is Mark.Coal or Mark.Skill)
        {
            DrawRect(r.Grow(-2), col with { A = 0.12f });
            var tex = Glyphs.Texture(mark == Mark.Coal ? "flame" : "book", 30, col);
            DrawTextureRect(tex, new Rect2(r.GetCenter() - new Vector2(15, 15), new Vector2(30, 30)), false);
            return;
        }
        DrawRect(r.Grow(-2), col with { A = 0.08f + 0.04f * tier });
        string numeral = Crafting.Grade(tier);
        var font = Style.Display;
        var size = font.GetStringSize(numeral, HorizontalAlignment.Left, -1, 22);
        DrawString(font, new Vector2((Size.X - size.X) / 2, 30), numeral, HorizontalAlignment.Left, -1, 22, col.Lightened(0.15f));
        // Pips: one for each grade it can reach here, lit for those it has.
        int n = Math.Max(cap, tier) + 1;
        float w = 7, gap = 3, x0 = (Size.X - (n * w + (n - 1) * gap)) / 2;
        for (int i = 0; i < n; i++)
        {
            var p = new Rect2(x0 + i * (w + gap), Size.Y - 13, w, 5);
            if (i <= tier) DrawRect(p, col);
            else DrawRect(p, col with { A = 0.55f }, false, 1);
        }
    }
}

/// <summary>
/// A piece's heat as cells of ember: lit for what is left, dark for what is spent. While a
/// craft is under the pointer or the focus, it shows what that craft may cost: the cells it
/// will surely take dimmed, the ones it might take pulsing; or, for a craft that adds heat,
/// the new cells, outlined in gold. The budget shown before it is spent (C3, C4).
/// </summary>
public partial class HeatGauge : HBoxContainer
{
    readonly int heat, full;
    int lo, hi;
    bool preview, grows;
    readonly Cells cells;
    readonly Label words;

    public HeatGauge(ItemInstance it, float width = 430)
    {
        heat = it.Heat ?? 0;
        full = Math.Max(1, it.HeatFull ?? heat);
        AddThemeConstantOverride("separation", Style.Gap3);
        MouseFilter = MouseFilterEnum.Ignore;
        cells = new Cells(this) { CustomMinimumSize = new Vector2(width, 18) };
        cells.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        AddChild(cells);
        words = Style.Label("", Style.UiBold, Style.Small, Style.EmberHi);
        AddChild(words);
        Say();
    }

    /// <summary>Show what a craft may cost (lo to hi), or add (negative); a remake grows the
    /// piece's full heat as well, a rekindle only refills it.</summary>
    public void Preview(int lo, int hi, bool grows = false)
    {
        if (lo == 0 && hi == 0) { Clear(); return; }
        this.lo = lo;
        this.hi = hi;
        this.grows = grows;
        preview = true;
        Say();
        cells.QueueRedraw();
    }

    public void Clear()
    {
        if (!preview) return;
        preview = false;
        Say();
        cells.QueueRedraw();
    }

    void Say()
    {
        if (heat <= 0 && !(preview && lo < 0)) { words.Text = "Set: nothing more can be worked into it"; words.AddThemeColorOverride("font_color", Style.InkDim); return; }
        words.AddThemeColorOverride("font_color", Style.EmberHi);
        if (!preview) { words.Text = $"Heat {heat} of {full}"; return; }
        if (lo < 0) { words.Text = $"+{NewHeat - heat} heat: {NewHeat} of {Grown}"; return; }
        int left = Math.Max(0, heat - hi), most = Math.Max(0, heat - lo);
        words.Text = left == most ? $"Heat {heat} to {left}" : $"Heat {heat} to {left}–{most}";
        if (left == 0) words.AddThemeColorOverride("font_color", Style.Bad);
    }

    /// <summary>The full heat after a craft that adds it: a remake grows the piece's full heat,
    /// a rekindle only refills it.</summary>
    int Grown => preview && lo < 0 && grows ? full - lo : full;
    int NewHeat => preview && lo < 0 ? Math.Min(Grown, heat - lo) : heat;

    public override void _Process(double delta)
    {
        if (preview && (lo < 0 || hi > lo)) cells.QueueRedraw();
    }

    sealed partial class Cells : Control
    {
        readonly HeatGauge g;
        public Cells(HeatGauge g) { this.g = g; MouseFilter = MouseFilterEnum.Ignore; }

        public override void _Draw()
        {
            int n = g.Grown;
            float gap = n > 24 ? 1 : 2, w = (Size.X - gap * (n - 1)) / n, hgt = Size.Y;
            float pulse = 0.55f + 0.45f * Mathf.Sin((float)Time.GetTicksMsec() / 180f);
            var dark = new Color("#1a1210");
            for (int i = 0; i < n; i++)
            {
                var r = new Rect2(i * (w + gap), 0, w, hgt);
                var lit = Style.Ember.Lerp(Style.EmberHi, n > 1 ? i / (float)(n - 1) * 0.6f : 0);
                bool has = i < g.heat;
                if (g.preview && g.lo < 0 && i >= g.heat && i < g.NewHeat)
                {
                    // Heat a craft would add: new cells, outlined in gold.
                    DrawRect(r, Style.Gold.Lerp(Style.EmberHi, 0.4f) with { A = 0.45f + 0.35f * pulse });
                    DrawRect(r, Colors.White with { A = 0.8f }, false, 1.5f);
                    continue;
                }
                if (!has) { DrawRect(r, dark); DrawRect(r, Style.Line with { A = 0.25f }, false, 1); continue; }
                if (g.preview && g.lo >= 0)
                {
                    bool sure = i >= g.heat - g.lo, maybe = !sure && i >= g.heat - g.hi;
                    if (sure) { DrawRect(r, lit with { A = 0.22f }); DrawRect(r, Style.Bad with { A = 0.8f }, false, 1.5f); continue; }
                    if (maybe) { DrawRect(r, lit with { A = 0.3f + 0.5f * pulse }); DrawRect(r, Style.Bad with { A = 0.5f }, false, 1); continue; }
                }
                DrawRect(r, lit);
                DrawRect(new Rect2(r.Position, new Vector2(w, hgt * 0.35f)), Colors.White with { A = 0.18f });
            }
        }
    }
}
