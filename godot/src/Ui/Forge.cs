using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// A crafter's bench (docs/CRAFTING_DESIGN.md section 14; the approved greybox,
/// docs/ui_review/greybox/greybox_bench.png): two fitted panels with the crafter live in the world
/// between them, as every counter is. Theirs at the left: the person as a strip (who, how they feel
/// about you, what they say), the anvil (the piece, its heat, its seams), and what they can do
/// with it as cards, two to a row, each with its one press; their terms along the foot. Yours at the
/// right: what you wear (the day's kit or the night's), what you carry, the stores and the purse.
/// The same page serves every hand that works gear (Brannoc's forge, Wenna's bench, Vonnra's
/// table, Snib's jar) and the Wayfinder's table with charts on it.
///
/// The anvil works one seam at a time, as Last Epoch's forge does: a seam is chosen, and only the
/// crafts that apply to it are offered, each saying what it takes, the heat it may cost and what
/// the seam will read after; what works the whole piece (remake, rekindle, break down, a trophy
/// set) sits with them. The heat gauge shows, while a press is under the pointer or the focus,
/// what that craft may spend; when the hammer falls, the seam rings and the heat burns out of the
/// gauge. Mouse: click a piece to put it on the anvil, click a seam, press a craft (held for what
/// cannot be undone). Pad: the same with the stick and A.
/// </summary>
public partial class ForgeScreen : Overlay
{
    public override string Kind => "forge";
    readonly string crafter;
    string? sel;
    /// <summary>The seam chosen on the anvil: an affix's place, or past the affixes an open
    /// seam (-1: the one most worth working, chosen when the piece is put down).</summary>
    int seam = -1;
    HeatGauge? gauge;
    /// <summary>Why the crafter is not working now (the forge banked), said once at the top.</summary>
    string? closed;
    /// <summary>"Make me one" is on the anvil instead of a piece, and the pattern chosen for it.</summary>
    bool making;
    string? pattern;
    /// <summary>Which kit's worn pieces the gear panel shows (Rpg/Kits.cs): the one on, until turned.</summary>
    KitKind? kitShown;
    /// <summary>The craft just done, for its moment when the page is built again: which piece,
    /// which seam, and the heat it had before.</summary>
    (string Uid, int Seam, int Heat, Verb Verb)? struck;
    readonly Dictionary<int, (Control Row, Control Badge)> rows = new();

    /// <summary>The two panels: theirs at the left, yours at the right, the crafter between.</summary>
    const float LeftW = 860, RightW = 548, Top = 40, Pad = 28;
    /// <summary>A craft card's width, two to a row in the left panel.</summary>
    const float CardW = (LeftW - 2 * Pad - 12) / 2;
    float RightX => 1920 - 40 - RightW;

    /// <summary>The crafter live in the world between the panels: the view looks at them, near, and
    /// sets them in the gap (the counters' shape); a crafter not standing here leaves it on the survivor.</summary>
    public override (double X, double Z)? CameraLook => G.Zone?.Actors.TryGetValue(crafter, out var a) == true ? (a!.X, a.Z) : null;
    public override float CameraShift => (40 + LeftW + RightX) / 2 - 960;
    public override float CameraNear => 0.62f;

    // --focus ID: that control has the focus first (with --pad, pictures of a craft's heat shown);
    // --make: "make me one" on the anvil, --pattern DEF its pattern chosen (pictures).
    public ForgeScreen(Game g, string crafter) : base(g)
    {
        this.crafter = crafter;
        Nav.Prefer = Args.Get("focus") ?? "worn:0";
        // Sitting down at the bench: a greeting, not what was said over the last craft.
        g.Journey.CraftSaid = null;
        // What was ordered yesterday is handed over first, and put on the anvil.
        if (crafter == Crafting.Rules.Commission.Crafter && g.Journey.CollectCommission() is { } made) sel = handed = made.Uid;
        if (Args.Has("make") && Crafting.Does(crafter, Verb.Commission)) { making = true; pattern = Args.Get("pattern"); }
        if (PutDown != null) { sel = PutDown; PutDown = null; }
    }

    CharacterData Ch => G.Journey.Ch;
    CraftCtx X => G.Journey.Craft;

    ItemInstance? Chosen => sel != null ? Inventory.Find(Ch, sel)?.Item : null;

    /* -------------------------------------------------- who is at the bench -- */

    bool She => Lore.Person(crafter)?.Person?.Sex == Sex.Female;
    string He => She ? "she" : "he";
    string His => She ? "her" : "his";
    string Him => She ? "her" : "him";

    /// <summary>A piece this crafter can do something with: anything workable for the smith; for a
    /// crafter who only works materials in, a piece their materials fit.</summary>
    bool Takes(ItemInstance it) => Charting ? it.Chart != null :
        Crafting.Workable(it) && (Crafting.Does(crafter, Verb.Temper) || Crafting.Does(crafter, Verb.Remake) || Crafting.WorkInChoices(it, crafter).Count > 0
            || Crafting.Does(crafter, Verb.Bind) || Crafting.Does(crafter, Verb.Steep));

    /// <summary>The Wayfinder's table: charts on the anvil, not gear (design 20.4).</summary>
    bool Charting => Crafting.Does(crafter, Verb.Ink);

    /// <summary>What the next bench opened puts on its anvil first (the table's chart in hand).</summary>
    public static string? PutDown;

    /// <summary>The crafter does something to one seam (temper, work in, cage, bind); the slurry works the whole piece.</summary>
    bool SeamCrafts => Crafting.Does(crafter, Verb.Temper) || Crafting.Does(crafter, Verb.WorkIn) || Crafting.Does(crafter, Verb.Cage) || Crafting.Does(crafter, Verb.Bind);

    protected override void Build()
    {
        HideHud();
        var def = Crafting.Crafter(crafter);
        var who = Lore.Person(crafter);
        // Something on the anvil from the start: what is in hand (--anvil DEF: that piece, for pictures),
        // the first piece this hand can do something with before one it would only refuse.
        if (Chosen == null && !making)
        {
            sel = (Workable().FirstOrDefault(it => it.Def == Args.Get("anvil")) ?? Workable().Where(Takes).OrderBy(it => Apt(it) ? 0 : 1).FirstOrDefault())?.Uid;
            seam = -1;
        }
        // Banked by night; or, for a bench that only works things in, not yet open (Wenna's, till the cure).
        closed = Crafting.Closed(crafter, G.Journey.Ctx) ?? (Crafting.Does(crafter, Verb.Temper) ? null : Crafting.Closed(crafter, G.Journey.Ctx, Verb.WorkIn));
        rows.Clear();

        var left = Fitted(new Vector2(40, Top), LeftW, Style.Gap3);
        left.AddChild(Strip(def, who));
        if (Crafting.Does(crafter, Verb.Buy) && crafter == Crafting.Rules.Slurry.Crafter) left.AddChild(JarTile());
        if (making) Making(left); else Anvil(left);
        if (Terms() is { } terms) left.AddChild(terms);

        Gear(Fitted(new Vector2(RightX, Top), RightW, Style.Gap3));

        var plate = Style.Panel(Kit.PanelBox(18, 6, Kit.Ground with { A = 0.9f }), Prompts());
        plate.MouseFilter = MouseFilterEnum.Ignore;
        var foot = new CenterContainer { Position = new Vector2(0, 996), Size = new Vector2(1920, 48), MouseFilter = MouseFilterEnum.Ignore };
        foot.AddChild(plate);
        AddChild(foot);
        Strike();
    }

    Control Prompts()
    {
        bool pad = Controls.Instance.UsingPad;
        var p = pad ? Kit.Prompts(Kit.Prompt(Act.Confirm, "Choose, or do it"), Kit.Prompt(Act.Cancel, "Close"))
            : Charting ? Kit.Prompts(Kit.Prompt("Click", "Lay a chart on the table"), Kit.Prompt("Click", "Choose an oath"), Kit.Prompt("Esc", "Close"))
            : SeamCrafts ? Kit.Prompts(Kit.Prompt("Click", "Put a piece on the anvil"), Kit.Prompt("Click", "Choose a seam"), Kit.Prompt("Hold", "What cannot be undone"), Kit.Prompt("Esc", "Close"))
            : Kit.Prompts(Kit.Prompt("Click", "Put a piece on the anvil"), Kit.Prompt("Hold", "What cannot be undone"), Kit.Prompt("Esc", "Close"));
        p.MouseFilter = MouseFilterEnum.Ignore;
        return p;
    }

    /* ------------------------------------------------------- the crafter -- */

    /// <summary>Who is at the bench, by name and calling: one of the town's people, or one who only
    /// speaks (Snib, foreman of the Dig, self-appointed).</summary>
    (string? Name, string? Role) WhoAt(NpcDef? who) =>
        who != null ? (who.Name, who.Role)
        : Lore.Speakers.TryGetValue(crafter, out var sp) ? (sp.Name, sp.Title)
        : (Crafting.Crafter(crafter)?.Name, null);

    /// <summary>A piece this hand would do something with, not only refuse: the slurry wants seams in
    /// a piece not steeped before.</summary>
    bool Apt(ItemInstance it) => !Crafting.Does(crafter, Verb.Steep) || Crafting.Seams(it) > 0 && !Crafting.Slurried(it);

    /// <summary>The person as a strip (the counters' shape): their likeness, their name, where this is,
    /// how they feel about you and what they charge, on one line; then what they say, under it (a
    /// first craft's telling runs to about seven lines, and has the room).</summary>
    Control Strip(CrafterDef? def, NpcDef? who)
    {
        var (name, role) = WhoAt(who);
        var h = Style.H(18);
        // The likeness: one of the town's people at head and shoulders, or the creature a crafter is (Snib).
        var size = new Vector2I(104, 112);
        Portrait? figure = who?.Person != null ? new Portrait(size, Portrait.Framing.Bust).Of(who.Person, who.Arms, who.Scale ?? 1)
            : def?.Visual is { } vis && SurvivorUnchained.View.Beasts.Of(vis) is { } beast ? new Portrait(size, Portrait.Framing.Bust).Of(beast) : null;
        if (figure != null)
        {
            var frame = Style.Panel(Kit.WellBox(0));
            frame.CustomMinimumSize = new Vector2(size.X, size.Y);
            frame.SizeFlagsVertical = SizeFlags.ShrinkBegin;
            frame.AddChild(figure);
            h.AddChild(frame);
        }
        var words = Style.V(4);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var named = Style.H(12, Style.Label((name ?? def?.Place ?? "The bench").ToUpperInvariant(), Style.Display, 30, Kit.Ink, false, HorizontalAlignment.Left, false));
        ((Control)named.GetChild(0)).SizeFlagsHorizontal = SizeFlags.ExpandFill;
        // "Make me one" is the anvil's other work: a new piece from a pattern rather than one carried.
        if (Crafting.Does(crafter, Verb.Commission))
        {
            var tabs = Kit.Tabs(new[] { "At the anvil", "Make me one" }, making ? 1 : 0, k => { making = k == 1; if (making) sel = null; Refresh(); }, 15, 20,
                new[] { "", Crafting.Ordered(G.Journey.World) is { } o ? (G.Journey.World.Day >= o.Ready ? "ready" : "on the bench") : "" });
            tabs.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            named.AddChild(tabs);
        }
        words.AddChild(named);
        var npc = G.Journey.World.Npc(crafter);
        double mod = G.Journey.PriceMod(crafter);
        int pct = (int)Math.Round((mod - 1) * 100);
        var line = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore };
        line.AddThemeConstantOverride("h_separation", 0);
        void Part(string text, Color col, bool first = false)
        {
            if (!first) line.AddChild(Style.Label("  ·  ", Style.Ui, 15, Kit.Faint, false, HorizontalAlignment.Left, false));
            line.AddChild(Style.Label(text, Style.Ui, 15, col, false, HorizontalAlignment.Left, false));
        }
        Part(def?.Place ?? Style.Cap1(role ?? ""), Kit.Ink2, true);
        if (who != null) Part(Rules.Attitude(npc), Kit.Dim);
        Part(pct == 0 ? $"{His} usual prices" : pct < 0 ? $"prices {-pct}% under {His} usual" : $"prices {pct}% over {His} usual", pct < 0 ? Style.Good : pct > 0 ? Style.Bad : Kit.Dim);
        words.AddChild(line);
        // What they say: over the last craft done, or a greeting (the story lead's words, in data).
        var said = G.Journey.CraftSaid ?? new Said(null, Crafting.Line(crafter, "greet", G.Journey.World.Day), null);
        var box = Style.V(3);
        if (said.Before != null) box.AddChild(Style.Label(said.Before, Style.TextItalic, 16, Kit.Dim, true));
        if (said.Line != null) box.AddChild(Style.Label($"“{said.Line}”", Style.TextItalic, 18, Kit.Ink, true));
        if (said.After != null) box.AddChild(Style.Label(said.After, Style.TextItalic, 16, Kit.Dim, true));
        if (box.GetChildCount() > 0)
        {
            words.AddChild(box);
            // Said just now: it comes in, rather than being there already.
            if (struck != null) { box.Modulate = Colors.White with { A = 0 }; box.CreateTween().TweenProperty(box, "modulate:a", 1f, 0.45).SetDelay(0.25); }
        }
        h.AddChild(words);
        return h;
    }

    /// <summary>Their terms along the panel's foot: those given now, and the way up to the rest (C18:
    /// standing sets the terms), with the standing they ask for as it is now.</summary>
    Control? Terms()
    {
        var ladder = Crafting.TermLadder(crafter, G.Journey.Ctx);
        if (ladder.Count == 0) return null;
        var npc = G.Journey.World.Npc(crafter);
        var axes = new[] { Axis.Respect, Axis.Trust, Axis.Affection }.Where(a => ladder.Any(t => t.Needs?.Contains(a.ToString().ToLowerInvariant()) == true)).ToList();
        var v = Style.V(4);
        v.AddChild(Kit.Head($"{Style.Cap1(His)} terms", axes.Count > 0 ? $"{His} {string.Join(", ", axes.Select(a => $"{a.ToString().ToLowerInvariant()} {npc[a]:0}"))}" : null));
        v.AddThemeConstantOverride("separation", 2);
        var flow = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore };
        flow.AddThemeConstantOverride("h_separation", 22);
        flow.AddThemeConstantOverride("v_separation", 4);
        foreach (var (said, fx, needs, met) in ladder)
        {
            // "at respect 20", but "after you have accused her": a standing is reached, a deed is done.
            string when = needs == null || met ? "" : needs.Any(char.IsDigit) ? $", at {needs}" : $", {needs}";
            var t = Style.H(6, Glyphs.Icon(met ? "flame" : "lock", 14, met ? Style.Ember : Kit.Faint),
                Style.Label($"{Style.Cap1(fx)}{when}", Style.Ui, 15, met ? Kit.Ink : Kit.Dim, false, HorizontalAlignment.Left, false));
            t.TooltipText = said;
            t.MouseFilter = MouseFilterEnum.Stop;
            flow.AddChild(t);
        }
        var def = Crafting.Crafter(crafter);
        if (def is { RespectPerCraft: > 0 })
            flow.AddChild(Style.Label($"Every craft {He} does for you raises {His} {def.Grows.ToString().ToLowerInvariant()} a little.", Style.TextItalic, 15, Kit.Faint, false, HorizontalAlignment.Left, false));
        v.AddChild(flow);
        return v;
    }

    /* ------------------------------------------------------- your gear -- */

    IEnumerable<ItemInstance> Workable() => Charting ? Maps.Charts.Carried(Ch) :
        Items.EquipSlots.Select(s => Ch.Equipment[s]).Concat(Kits.Aside(Ch).Select(a => a.Item)).Concat(Ch.Pack).Where(it => it != null && Crafting.Workable(it)).Select(it => it!);

    /// <summary>Your side of the counter: what you wear (either kit, once there are two), what you
    /// carry, the stores and the purse; at the Wayfinder's table, the charts you carry.</summary>
    void Gear(VBoxContainer v)
    {
        var head = Style.H(12, new Title(Charting ? "Your charts" : "Your gear", 28, false), Nav.Skip(CloseButton("Esc", G.CloseOverlay)));
        ((Control)head.GetChild(1)).SizeFlagsVertical = SizeFlags.ShrinkBegin;
        v.AddChild(head);
        if (Charting) { ChartsCarried(v); return; }
        // Worn: the kit on now, or the other, turned by its switch once there are two (design 20.2).
        var shown = kitShown ?? Kits.On(Ch);
        Control? switcher = Kits.Shown(Ch)
            ? Kit.Tabs(new[] { "By day", "By night" }, (int)shown, k => { kitShown = (KitKind)k; Refresh(); }, 15, 16)
            : null;
        v.AddChild(Kit.Head("Worn", switcher == null ? "choose a piece" : null, switcher != null ? new[] { switcher } : Array.Empty<Control>()));
        var worn = new GridContainer { Columns = 6, MouseFilter = MouseFilterEnum.Ignore };
        worn.AddThemeConstantOverride("h_separation", 8);
        worn.AddThemeConstantOverride("v_separation", 8);
        int i = 0;
        bool fallback = false;
        foreach (var s in Items.EquipSlots)
        {
            var it = Kits.Piece(Ch, shown, s);
            // By night, a slot with nothing of its own wears the day's piece: shown faint, "as by day".
            bool asDay = shown == KitKind.Night && it != null && !Kits.HasOwn(Ch, KitKind.Night, s);
            fallback |= asDay;
            var (name, glyph) = InventoryScreen.Slots[s];
            var view = ItemViews.Slot(it, 72, it != null && it.Uid == sel && !making, null, false, it != null ? () => Choose(it.Uid) : null, null,
                over => Hover(it, over), glyph, name, $"worn:{i++}");
            if (it != null && (!Takes(it) || asDay)) view.Modulate = new Color(1, 1, 1, asDay ? 0.4f : 0.35f);
            worn.AddChild(view);
        }
        v.AddChild(Style.Panel(Kit.WellBox(6), worn));
        if (fallback) v.AddChild(Style.Label("Faint: as by day. The night kit wears the day's piece where it has none of its own.", Style.TextItalic, 14, Kit.Faint, true));
        var block = new PackBlock
        {
            Ch = Ch, Width = RightW - 2 * Pad, Cols = 6, Tile = 72, Nav = "pack", BigPurse = true, Refresh = Refresh,
            Selected = it => it.Uid == sel && !making, Click = it => Choose(it.Uid), Primary = it => Choose(it.Uid), Hover = Hover,
            // What this hand cannot work is dimmed; materials are read, not worked.
            Setup = (_, it, view) => { if (it != null && Items.SlotFor(Items.Get(it.Def)) != null && !Takes(it)) view.Modulate = new Color(1, 1, 1, 0.35f); },
        };
        v.AddChild(block.Build());
    }

    /// <summary>A thing's card beside it, over the world between the panels (no inspect panel).</summary>
    void Hover(ItemInstance? it, Control? over) =>
        TipBeside(it != null && it.Uid != sel ? ItemViews.Card(it, Ch, false) : null, null, over, true, RightX);

    void Choose(string uid)
    {
        if (Inventory.Find(Ch, uid) is not { } loc || !Takes(loc.Item)) { Sound.Sfx.Deny(); return; }
        sel = uid;
        seam = -1;
        craftTab = null;
        making = false;
        Sound.Sfx.Click();
        Refresh();
    }

    void Pick(int k)
    {
        if (seam == k) return;
        seam = k;
        craftTab = null;
        Sound.Sfx.Click();
        Refresh();
    }

    /* --------------------------------------------------------- the anvil -- */

    static int Places(ItemInstance it) => Math.Max(Crafting.Seams(it), it.Affixes.Count);

    static bool Plain(AffixDef? d) => d != null && d.Kindled == null && d.Grants == null && !d.Slurry;

    /// <summary>The seam most worth working when a piece is put down: an affix that can still be
    /// tempered, else an open seam, else the first. A hand that only works things in (Wenna's)
    /// starts at the open seam, never offering to work over what the piece has.</summary>
    int DefaultSeam(ItemInstance it)
    {
        int cap = Crafting.Cap(it);
        if (!Crafting.Does(crafter, Verb.Temper) && Crafting.OpenSeams(it) > 0) return it.Affixes.Count;
        for (int k = 0; k < it.Affixes.Count; k++)
            if (Plain(Items.Affix(it.Affixes[k].Id)) && it.Affixes[k].Tier < cap) return k;
        return Crafting.OpenSeams(it) > 0 ? it.Affixes.Count : 0;
    }

    /// <summary>What the anvil offers for the piece on it: cards, two to a row; one wide card that
    /// needs the row (the slurry's odds); and what is said quietly instead of a card.</summary>
    sealed class Offer
    {
        public readonly List<(string Group, Control Card, bool Ok)> Cards = new();
        public readonly List<(string Group, string Text)> Notes = new();
        public Control? Wide;
        /// <summary>What is being offered now (Temper, Work in, Cage...): its cards and notes go under it.</summary>
        public string Group = "";
        public void Add(Control card) => Cards.Add((Group, card, card.GetMeta("ok", false).AsBool()));
        public void Note(string text) => Notes.Add((Group, text));
        public List<string> Groups => Cards.Select(c => c.Group).Concat(Notes.Select(n => n.Group)).Distinct().ToList();
    }

    /// <summary>The group of crafts open under the anvil's tabs (null: the first with something to do).</summary>
    string? craftTab;

    void Anvil(VBoxContainer v)
    {
        var it = Chosen;
        if (it == null)
        {
            v.AddChild(Kit.Head("The anvil"));
            v.AddChild(Style.Label("Nothing on the anvil.", Style.Text, Style.Title, Kit.Ink, false, HorizontalAlignment.Center));
            v.AddChild(Style.Label(Charting ? "Choose a chart you carry. A map's ruler leaves the next when it falls."
                : Crafting.Does(crafter, Verb.Temper)
                ? "Choose a piece you wear or carry. Plain gear and weapons can be worked; somebody else's named work is left be."
                : $"Choose a piece you wear or carry that {His} {string.Join(" or ", Crafting.Rules.Materials.Where(m => m.Value.Crafter == crafter).Select(m => Items.Get(m.Key).Plural ?? m.Key))} can go into.",
                Style.TextItalic, 16, Kit.Dim, true, HorizontalAlignment.Center));
            if (closed != null) v.AddChild(Closed());
            return;
        }
        if (it.Chart != null) { ChartAnvil(v, it); return; }
        if (seam < 0 || seam >= Places(it)) seam = Places(it) > 0 ? DefaultSeam(it) : -1;
        v.AddChild(Head(it));
        if (closed != null) v.AddChild(Closed());
        // What the jar just did to it, plainly, before the seams that show it.
        if (came is { } c && c.Uid == it.Uid) v.AddChild(Came(c.Text, c.Mood));
        v.AddChild(SeamList(it));
        var offer = new Offer();
        if (seam >= 0 && SeamCrafts) AtSeam(it, offer);
        if (Crafting.Does(crafter, Verb.Steep)) Steeping(it, offer);
        Setting(it, offer);
        Whole(it, offer);
        bool open = seam >= it.Affixes.Count;
        // ("at of the Wolf" read as a slip: the seam is named by its place)
        string? where = seam >= 0 && SeamCrafts ? open ? "at the open seam" : $"at the {Ordinal(seam)} seam" : null;
        Lay(v, offer, $"What {He} can do", where);
    }

    /// <summary>The offer laid out under its head: the wide card (the slurry's odds); tabs by what is done
    /// (Temper · Work in 4 · Cage 4 · The piece 3), each counting what can be done now; the open group's
    /// cards two to a row; and its quiet notes. All of a smith's crafts at once ran to a dozen cards
    /// and off the foot of the screen; one kind at a time stays short, and the counts say the rest.</summary>
    void Lay(VBoxContainer v, Offer offer, string title, string? note)
    {
        var groups = offer.Groups;
        if (craftTab == null || !groups.Contains(craftTab))
            craftTab = groups.FirstOrDefault(g => offer.Cards.Any(c => c.Group == g && c.Ok)) ?? groups.FirstOrDefault();
        int on = Math.Max(0, groups.IndexOf(craftTab ?? ""));
        Control[] end = groups.Count > 1
            ? new Control[] { Kit.Tabs(groups.ToArray(), on, k => { craftTab = groups[k]; Refresh(); }, 15, 18,
                groups.Select(g => offer.Cards.Count(c => c.Group == g && c.Ok) is var n and > 0 ? $"{n}" : "").ToArray()) }
            : Array.Empty<Control>();
        v.AddChild(Kit.Head(title, note, end));
        if (offer.Wide != null) v.AddChild(offer.Wide);
        var cards = offer.Cards.Where(c => c.Group == craftTab).Select(c => c.Card).ToList();
        if (cards.Count > 0)
        {
            var grid = new GridContainer { Columns = 2, MouseFilter = MouseFilterEnum.Ignore };
            grid.AddThemeConstantOverride("h_separation", 12);
            grid.AddThemeConstantOverride("v_separation", 10);
            foreach (var card in cards) grid.AddChild(card);
            if (cards.Count > 4)
            {
                // More than two rows (a pack full of donors to bind from): the rest scroll, the panel holds.
                var scroll = Style.Scroll(grid);
                scroll.CustomMinimumSize = new Vector2(LeftW - 2 * Pad, 2 * 122 + 70);
                v.AddChild(scroll);
            }
            else v.AddChild(grid);
        }
        foreach (var (_, text) in offer.Notes.Where(n => n.Group == craftTab)) v.AddChild(Style.Label(text, Style.TextItalic, 15, Kit.Dim, true));
    }

    Control Closed() => Style.Label(closed!, Style.TextItalic, 17, Style.Bad, true);

    static string Ordinal(int k) => k switch { 0 => "first", 1 => "second", 2 => "third", 3 => "fourth", _ => $"{k + 1}th" };

    Control Head(ItemInstance it)
    {
        var def = Items.Get(it.Def);
        var col = Style.RarityOf(it.Rarity);
        bool slurried = Crafting.Slurried(it);
        var h = Style.H(18);
        var pic = ItemPhotos.Icon(def.Icon, 88, col.Lightened(0.25f));
        if (slurried) ItemViews.Steeped(pic);
        var photo = Style.Panel(Kit.TileBox(it, true), pic);
        photo.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        h.AddChild(photo);
        var names = Style.V(4);
        names.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        names.AddChild(Style.Label(Inventory.Name(it), Style.TextBold, 26, col, true));
        string what = it.Chart is { } ch ? $"{(ch.Rarity switch { 2 => "A rare chart", 1 => "A fine chart", _ => "A plain chart" })}, tier {ch.Tier}: {Crafting.Ground(ch.People)}"
            : $"{Inventory.RarityName(it)} {def.Kind.ToString().ToLowerInvariant()}";
        // Where it is: on now, set aside in the other kit, or carried.
        var loc = Inventory.Find(Ch, it.Uid);
        if (it.Chart == null && loc is { Worn: true }) what += Kits.Shown(Ch) ? $", worn {(Kits.On(Ch) == KitKind.Night ? "by night" : "by day")}" : ", worn";
        else if (loc is { Aside: true }) what += $", worn {(Kits.On(Ch) == KitKind.Night ? "by day" : "by night")}";
        var kind = Style.H(Style.Gap2, Style.Label(what, Style.Ui, 15, Kit.Ink2), Style.Gems(it.Rarity, 7));
        // Made for you this morning: said where the piece is named, the first time it is seen.
        if (handed == it.Uid) kind.AddChild(Style.Label("·  made for you, ready this morning", Style.TextItalic, 15, Style.GoldHi));
        if (slurried) kind.AddChild(Style.Label("·  slurried: green-black veins, set for good", Style.TextItalic, 15, ItemViews.SlurryGreen));
        names.AddChild(kind);
        gauge = new HeatGauge(it, 420);
        names.AddChild(gauge);
        h.AddChild(names);
        // The whole piece rings here (a remake, a rekindle, a jar that only left its veins): its picture
        // is a panel, so the flare lies over it.
        rows[-1] = (photo, photo);
        if (handed == it.Uid && !handedShown) { handedShown = true; struck = (it.Uid, -1, it.Heat ?? 0, Verb.Commission); }
        return h;
    }

    bool handedShown;

    /// <summary>What the slurry did, in a slab coloured by how it went: green for a gain, red for a
    /// grade lost, the grey of the veins for nothing at all.</summary>
    static Control Came(string text, int mood)
    {
        var col = mood > 0 ? ItemViews.SlurryGreen : mood < 0 ? Style.Bad : new Color("#9aa890");
        var row = Style.H(Style.Gap3, Glyphs.Icon("drop", 26, col),
            Style.V(1, Style.Label("WHAT THE JAR DID", Style.UiHeavy, 13, col), Style.Label(text, Style.UiBold, 17, mood < 0 ? Style.Bad : Kit.Ink, true)));
        ((Control)row.GetChild(1)).SizeFlagsHorizontal = SizeFlags.ExpandFill;
        return Style.Panel(Kit.PanelBox(14, 10, new Color("#18200f")), row);
    }

    /* ---------------------------------------------------------- the seams -- */

    Control SeamList(ItemInstance it)
    {
        var v = Style.V(6);
        int cap = Crafting.Cap(it), places = Places(it);
        string rarity = Inventory.RarityName(it).ToLowerInvariant();
        if (places == 0)
        {
            v.AddChild(Kit.Head("Its seams"));
            // What a seam could take once it is open, from what is in the pouch (discovery by touch).
            var could = Crafting.WorkInChoices(it, crafter).Where(c => Inventory.Count(Ch, c.Material) > 0)
                .Select(c => $"{Items.Affix(c.Affix)?.Name} from {Items.Find(c.Material)?.Plural ?? c.Material}").ToList();
            v.AddChild(Style.Label("A plain piece: no seams to work. Remade on a better pattern, it opens one."
                + (could.Count > 0 ? $" Then {He} could work in {string.Join(", ", could.Take(could.Count - 1))}{(could.Count > 1 ? " or " : "")}{could[^1]}." : ""),
                Style.TextItalic, 15, Kit.Dim, true));
            return v;
        }
        // A hand that works the whole piece (the slurry) shows the seams as what it may move, not as a choice.
        v.AddChild(Kit.Head("Its seams", SeamCrafts ? $"choose one to work  ·  grades to {Crafting.Grade(cap)} on {Crafting.Article(rarity)} piece"
            : $"what is in it  ·  the forge takes {Crafting.Article(rarity)} piece to {Crafting.Grade(cap)}"));
        for (int k = 0; k < places; k++) v.AddChild(SeamRow(it, k, cap));
        return v;
    }

    Control SeamRow(ItemInstance it, int k, int cap)
    {
        bool open = k >= it.Affixes.Count;
        var a = open ? null : it.Affixes[k];
        var ad = a != null ? Items.Affix(a.Id) : null;
        bool coal = ad?.Kindled != null, skill = ad?.Grants != null, slurry = ad?.Slurry == true, mark = ad?.Mark == true, on = k == seam && SeamCrafts;
        // The seam at the anvil is the one raised panel with the ember's edge; the rest lie in the well.
        var box = new StyleBoxFlat { BgColor = on ? new Color("#33251b") : Kit.Well, BorderColor = on ? Style.Ember : new Color("#0a090b"), CornerDetail = 4 };
        box.SetCornerRadiusAll(3);
        box.SetBorderWidthAll(on ? 1 : 0);
        box.BorderWidthTop = 1;
        box.ContentMarginLeft = box.ContentMarginRight = 12;
        box.ContentMarginTop = box.ContentMarginBottom = 7;
        var panel = Style.Panel(box);
        panel.MouseFilter = MouseFilterEnum.Stop;
        var h = Style.H(14);
        var badge = new GradeBadge(open ? GradeBadge.Mark.Open : coal ? GradeBadge.Mark.Coal : skill ? GradeBadge.Mark.Skill : slurry ? GradeBadge.Mark.Slurry
            : mark ? GradeBadge.Mark.Inscribed : GradeBadge.Mark.Grade, a?.Tier ?? 0, cap);
        h.AddChild(badge);
        var words = Style.V(1);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        words.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        string title = open ? "An open seam" : ad?.Text(a!.Tier) ?? a!.Id;
        string rarity = Inventory.RarityName(it).ToLowerInvariant();
        bool bright = !open && !mark && a!.Tier >= Crafting.Bright;
        string note = open ? (Crafting.Does(crafter, Verb.Cage) ? "work a material in, or cage a coal" : Crafting.Does(crafter, Verb.WorkIn) ? "work a material in"
                : Crafting.Does(crafter, Verb.Mark) ? "bind a power into it, or write a mark" : Crafting.Does(crafter, Verb.Bind) ? "bind a power into it" : "empty")
            : coal ? $"{ad!.Name}: a caged coal, it shapes the ember's draft"
            : skill ? $"{ad!.Name}: a worn skill, it has no grades"
            : slurry ? $"{ad!.Name}: the slurry's, past its seams; it has no grades"
            : mark ? $"{ad!.Name}  ·  a mark at grade {Crafting.Grade(a!.Tier)}: it works in the Wayfinder's maps"
            : bright ? $"{ad?.Name}  ·  the bright grade, V: past every forge"
            : a!.Tier > cap ? $"{ad?.Name}  ·  grade {Crafting.Grade(a.Tier)}, past what the forge makes of {Crafting.Article(rarity)} piece"
            : a!.Tier >= cap ? $"{ad?.Name}  ·  grade {Crafting.Grade(a.Tier)}, as fine as {Crafting.Article(rarity)} piece is made"
            : $"{ad?.Name}  ·  grade {Crafting.Grade(a.Tier)}; tempers to {Crafting.Grade(cap)}";
        words.AddChild(Style.Label(title, Style.UiBold, 17, open ? Style.GoldHi : coal ? Style.EmberHi : slurry ? ItemViews.SlurryGreen : mark ? ItemViews.MarkInk : bright ? ItemViews.BrightGrade : Kit.Ink, true));
        words.AddChild(Style.Label(note, Style.TextItalic, 15, Kit.Dim, true));
        h.AddChild(words);
        if (on) h.AddChild(Style.Label("AT THE ANVIL", Style.UiHeavy, 12, Style.Ember));
        panel.AddChild(h);
        if (SeamCrafts)
        {
            panel.MouseDefaultCursorShape = CursorShape.PointingHand;
            panel.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) Pick(k); };
            Nav.Mark(panel, $"seam:{k}", () => Pick(k));
        }
        rows[k] = (panel, badge);
        return panel;
    }

    /// <summary>The crafts for the chosen seam: temper it, work a material in, cage a coal, bind, mark.</summary>
    void AtSeam(ItemInstance it, Offer o)
    {
        int k = seam;
        bool open = k >= it.Affixes.Count;
        var a = open ? null : it.Affixes[k];
        var ad = a != null ? Items.Affix(a.Id) : null;
        bool coal = ad?.Kindled != null;
        // Set: every seam's craft would refuse alike, so it is said once.
        o.Group = "The seam";
        if (it.Heat is 0)
        {
            o.Note(Crafting.Slurried(it) ? "Steeped and set for good: no hand works it again. It can still be worn, or broken down."
                : Crafting.Does(crafter, Verb.Rekindle) ? "Set: its heat is spent. Rekindled, it could be worked again." : "Set: its heat is spent. Nothing more can be worked into it.");
            return;
        }
        if (Plain(ad) && Crafting.Does(crafter, Verb.Temper))
        {
            o.Group = "Temper";
            int cap = Crafting.Cap(it);
            if (a!.Tier >= cap)
                o.Note(it.Rarity < Crafting.Rules.RemakeCap
                    ? $"Grade {Crafting.Grade(a.Tier)} is as fine as {Crafting.Article(Inventory.RarityName(it).ToLowerInvariant())} piece is made. Remade on a better pattern, it could be tempered further."
                    : $"Grade {Crafting.Grade(a.Tier)} is as fine as the forge makes it. Finer is the world's to give.");
            else
            {
                var q = Crafting.Temper(X, it, k, crafter);
                // A count of blows: one for each grade it climbs to.
                o.Add(Card("Temper", q, () => Work(q, () => Sound.Sfx.Anvil(2 + a.Tier)), "Temper", "temper"));
            }
        }
        if (Crafting.Does(crafter, Verb.WorkIn)) WorkIn(it, open ? -1 : k, ad, o);
        if (Crafting.Does(crafter, Verb.Cage)) Coals(it, k, open, coal, o);
        if (Crafting.Does(crafter, Verb.Bind)) Binding(it, k, open, ad, o);
        if (Crafting.Does(crafter, Verb.Mark)) Marking(it, k, open, ad, o);
    }

    void WorkIn(ItemInstance it, int over, AffixDef? lost, Offer o)
    {
        o.Group = "Work in";
        var choices = Crafting.WorkInChoices(it, crafter);
        // Discovery by touch: a material shows once it is in the pouch.
        var known = choices.Where(c => Inventory.Count(Ch, c.Material) > 0).ToList();
        // An answer it already has, in another seam or in this one, is no choice.
        var offer = known.Where(c => !it.Affixes.Any(x => x.Id == c.Affix)).ToList();
        if (offer.Count == 0)
        {
            string? had = known.Count > 0 ? string.Join(" and ", known.Select(c => Items.Affix(c.Affix)?.Name ?? c.Affix).Distinct()) : null;
            var others = choices.Where(c => Inventory.Count(Ch, c.Material) == 0).Select(c => Items.Find(c.Material)?.Plural ?? c.Material).Distinct().ToList();
            o.Note(choices.Count == 0 ? $"Nothing {He} works in goes into this kind of piece."
                : had != null ? $"It has {had} in it already." + (others.Count > 0 ? $" {Style.Cap1(string.Join(", ", others))} would give it something else." : "")
                : $"To work something in, bring {Him} {string.Join(", ", others)}.");
            return;
        }
        foreach (var (m, a) in offer)
        {
            var q = Crafting.WorkIn(X, it, m, a, over, crafter);
            q.Before = null;
            var md = Items.Get(m);
            o.Add(Card($"Work in: {Items.Affix(a)?.Name}", q, () => Work(q, () => Sound.Sfx.Anvil(1)), "Work in", $"workin:{m}:{a}",
                ItemPhotos.Icon(md.Icon, 40, Kit.Dim), lost != null ? $"From {md.Plural ?? md.Name}, in place of {lost.Name}, which is lost" : $"From {md.Plural ?? md.Name}: the answer to what it came from"));
        }
    }

    void Coals(ItemInstance it, int k, bool open, bool coal, Offer o)
    {
        o.Group = "Cage";
        int held = it.Affixes.FindIndex(x => Items.Affix(x.Id)?.Kindled != null);
        if (Inventory.Count(Ch, Crafting.Shard) == 0 && held < 0) { o.Note($"To cage a coal, bring {Him} ember shards carried out of the night."); return; }
        if (it.Rarity < Crafting.Rules.Cage.MinRarity) { o.Note("Too plain a piece to hold a coal: rare and up."); return; }
        // One coal a piece: it goes where the old one sat.
        if (held >= 0 && held != k) { o.Note("Its coal sits in another seam. Choose that seam to cage another in its place."); return; }
        var wanted = Crafting.Wanted(Ch);
        int n = 0;
        foreach (var id in Crafting.Coals(Ch, it, G.Journey.World.Day))
        {
            var a = Items.Affix(id)!;
            var q = Crafting.Cage(X, it, id, open ? -1 : k, crafter);
            q.Before = null;
            q.After = a.Text(0);
            bool wants = wanted.Contains(a.Kindled!);
            o.Add(Card($"Cage: {a.Name}", q, () => Work(q, Sound.Sfx.Cage), "Cage it", $"coal:{n++}", null,
                wants ? "Your skills evolve with it" : coal ? "In place of the coal it holds, which goes out" : "A coal from the night, caged: it shapes the ember's draft",
                ink: Style.EmberHi, lit: wants));
        }
        var again = Crafting.Redraw(X, it, crafter);
        o.Add(Card("Three more coals", again, () => Work(again, Sound.Sfx.Click), "Three more", "redraw", null, "Not these: the fire offers three others"));
    }

    /// <summary>A trophy the survivor carries, set into this piece (Greymuzzle's fang): the smith's own
    /// words lead it. Offered only while one is carried; said quietly where the piece cannot take it.</summary>
    void Setting(ItemInstance it, Offer o)
    {
        if (!Crafting.Does(crafter, Verb.Set)) return;
        o.Group = "Set";
        foreach (var (trophy, s) in Crafting.Rules.Settings.Where(kv => kv.Value.Crafter == crafter && Inventory.Count(Ch, kv.Key) > 0))
        {
            var td = Items.Get(trophy);
            if (!s.Kinds.Contains(Items.Get(it.Def).Kind))
            {
                o.Note($"{td.Name}: {He} sets it in {string.Join(" or ", s.Kinds.Select(k => Crafting.Article(k.ToString().ToLowerInvariant())))}. Put one on the anvil.");
                continue;
            }
            var q = Crafting.Set(X, it, trophy, crafter);
            q.Before = null;
            q.After = $"{q.After}. It leads the piece's name, spends no heat and takes no seam.";
            o.Add(Card($"Set {td.Name} in it", q, () => Work(q, () => { Sound.Sfx.Anvil(3); Sound.Sfx.Discovery(); }), "Set it", "set",
                ItemPhotos.Icon(td.Icon, 40, Kit.Dim), Crafting.Line(crafter, $"{s.Moment}.choice") is { } lead ? $"“{lead}”" : null));
        }
    }

    /// <summary>What works on the whole piece: a better pattern, heat back, or the iron in it.</summary>
    void Whole(ItemInstance it, Offer o)
    {
        o.Group = "The piece";
        if (Crafting.Does(crafter, Verb.Remake))
        {
            var q = Crafting.Remake(X, it, crafter);
            // At the last pattern, or remade today and cooling: said quietly, no press.
            if (q.Blocked != null && (q.Takes.Count == 0 || it.Remade == G.Journey.World.Day)) o.Note(q.Blocked);
            else o.Add(Card(q.Title, q, () => Work(q, () => { Sound.Sfx.Anvil(4); Sound.Sfx.Loot(true); }), "Remake", "remake"));
        }
        if (Crafting.Does(crafter, Verb.Rekindle))
        {
            var q = Crafting.Rekindle(X, it, crafter);
            bool full = it.Heat is int h && h >= (it.HeatFull ?? 0);
            if (Crafting.Slurried(it)) o.Note(q.Blocked ?? Crafting.SetForGood);
            else if (!full) o.Add(Card("Rekindle", q, () => Work(q, Sound.Sfx.Cage), "Rekindle", "rekindle"));
        }
        if (Crafting.Does(crafter, Verb.BreakDown))
        {
            var q = Crafting.BreakDown(X, it, crafter);
            string gives = string.Join(" and ", q.Gives.Select(kv => Items.Several(kv.Key, kv.Value)));
            bool worn = Inventory.Find(Ch, it.Uid) is { Worn: true } or { Aside: true };
            if (worn) o.Note("Worn: take it off first to break it down.");
            else
            {
                q.Before = null;
                q.After = $"Gives {gives}";
                o.Add(Card("Break down", q, () => Work(q, Sound.Sfx.Shatter, off: true), "Break down", "break", null, "The piece is gone", hold: true));
            }
        }
    }

    /* ---------------------------------------------------- the binder's -- */

    /// <summary>What can be bound into this seam: the powers in what the survivor carries that this kind
    /// of piece takes, each at the grade it would come in at. The thing it comes from is unmade, so the
    /// press is held.</summary>
    void Binding(ItemInstance it, int k, bool open, AffixDef? lost, Offer o)
    {
        o.Group = "Bind";
        var donors = Crafting.Donors(Ch, it).Where(d => it.Affixes.Where((a, i) => open || i != k).All(a => a.Id != d.Donor.Affixes[d.Index].Id)).ToList();
        // A coal in what is carried will not come out for her: said in her words, once.
        bool caged = Ch.Pack.Any(p => p != null && p.Affixes.Any(a => Items.Affix(a.Id) is { Kindled: not null } c && c.Slots.Contains(Items.Get(it.Def).Kind)));
        if (donors.Count == 0)
        {
            o.Note($"To bind, carry something with a power this {Items.Get(it.Def).Kind.ToString().ToLowerInvariant()} would take: {He} lifts it out, and what it came from is gone. What you wear cannot give: take it off first.");
            if (caged && Crafting.Line(crafter, "bind.caged") is { } c1) o.Note($"“{c1}”");
            return;
        }
        int n = 0;
        string rarity = Inventory.RarityName(it).ToLowerInvariant();
        foreach (var (d, i) in donors)
        {
            var q = Crafting.Bind(X, it, d, i, open ? -1 : k, crafter);
            q.Before = null;
            var dd = Items.Get(d.Def);
            var roll = d.Affixes[i];
            int grade = q.Grade >= 0 ? q.Grade : roll.Tier;
            // The power and the grade it comes in at; where it comes from, and what that costs.
            string note = $"Out of your {Inventory.Name(d)}, which is unmade"
                + (roll.Tier > grade ? $" (grade {Crafting.Grade(roll.Tier)} there; {Crafting.Article(rarity)} piece holds {Crafting.Grade(grade)})" : "")
                + (lost != null ? $"; in place of {lost.Name}, which is lost" : "");
            o.Add(Card($"Bind: {Items.Affix(roll.Id)?.Name}, grade {Crafting.Grade(grade)}", q, () => Work(q, () => { Sound.Sfx.Cage(); Sound.Sfx.Discovery(); }),
                "Bind", $"bind:{n++}", ItemPhotos.Icon(dd.Icon, 40, Style.RarityOf(d.Rarity)), note, hold: true));
        }
        if (caged && Crafting.Line(crafter, "bind.caged") is { } c2) o.Note($"Not the caged coals: “{c2}”");
    }

    /// <summary>What a map's rulers left, read and written in (design 20.3): each thing carried that holds a
    /// Mark, at the grade it fell at, its own picture on its card. One Mark to a piece: a second goes where
    /// the first was.</summary>
    void Marking(ItemInstance it, int k, bool open, AffixDef? here, Offer o)
    {
        o.Group = "Mark";
        int held = it.Affixes.FindIndex(x => Items.Affix(x.Id)?.Mark == true);
        var carried = Crafting.MarksCarried(Ch);
        if (carried.Count == 0)
        {
            o.Note($"To write a mark, bring {Him} what a map's ruler leaves: {He} reads how it fought, and writes it into a piece. It works in the Wayfinder's maps, three worn at once.");
            return;
        }
        if (held >= 0 && held != k) { o.Note("Its mark sits in another seam. Choose that seam to write another in its place."); return; }
        int n = 0;
        foreach (var from in carried)
        {
            var m = Crafting.MarkIn(from)!;
            var q = Crafting.Inscribe(X, it, from, open ? -1 : k, crafter);
            q.Before = null;
            var fd = Items.Get(from.Def);
            o.Add(Card($"Mark: {Items.Affix(m.Id)?.Name}, grade {Crafting.Grade(m.Tier)}", q, () => Work(q, () => { Sound.Sfx.Cage(); Sound.Sfx.Discovery(); }),
                "Inscribe", $"mark:{n++}", ItemPhotos.Icon(fd.Icon, 40, Style.RarityOf(from.Rarity)),
                $"From your {fd.Name}, which is used up" + (held >= 0 ? "; in place of the mark it has" : here != null ? $"; in place of {here.Name}, which is lost" : ""), ink: ItemViews.MarkInk));
        }
    }

    /* ------------------------------------------------- the Wayfinder's -- */

    /// <summary>The charts carried, to choose among (the highest tier first), and the pouch.</summary>
    void ChartsCarried(VBoxContainer v)
    {
        var charts = Maps.Charts.Carried(Ch).Cast<ItemInstance?>().ToList();
        v.AddChild(Kit.Head("Charts", charts.Count == 0 ? "none carried" : $"{charts.Count}  ·  choose one"));
        while (charts.Count < 12 || charts.Count % 6 != 0) charts.Add(null);
        var g = ItemViews.Grid(charts, 6, 72, it => it.Uid == sel, null, it => Choose(it.Uid), it => Choose(it.Uid), Hover, "pack", null, null, null, Ch);
        v.AddChild(Style.Panel(Kit.WellBox(6), g));
        var pouch = Inventory.Pouch(Ch).Cast<ItemInstance?>().ToList();
        var purse = Style.H(5, Glyphs.Icon("coin", 22, Style.GoldHi), Style.Label($"{Math.Floor(Ch.Gold)}", Style.Display, 24, Style.GoldHi, false, HorizontalAlignment.Left, false));
        v.AddChild(Kit.Head("Pouch", pouch.Count == 0 ? "empty" : null, purse));
        if (pouch.Count > 0) v.AddChild(ItemViews.Grid(pouch, 8, 52, null, null, null, null, Hover, "pouch", null, null, null, Ch, 6));
    }

    /// <summary>A chart on the table (design 20.4): its mods as rows, the foe's then yours, one chosen to pin
    /// or scrape; what works the whole chart with them (ink a side, burn and redraw, annotate); its heat the
    /// budget, as a piece's is.</summary>
    void ChartAnvil(VBoxContainer v, ItemInstance it)
    {
        var c = it.Chart!;
        var mods = c.Rolled.OrderBy(m => m.Prefix ? 0 : 1).ToList();
        if (seam >= mods.Count) seam = mods.Count > 0 ? 0 : -1;
        if (seam < 0 && mods.Count > 0) seam = 0;
        v.AddChild(Head(it));
        if (closed != null) v.AddChild(Closed());
        var list = Style.V(6);
        list.AddChild(Kit.Head("Sworn on it", mods.Count == 0 ? null : $"choose one to pin or scrape  ·  three to a side  ·  {Pct(c.Quantity - 1)} more found, {Pct(c.RarityBonus - 1)} finer"));
        if (mods.Count == 0) list.AddChild(Style.Label("Sworn under nothing: plain ground, plain pay. Ink it to swear it to more, and to pay more.", Style.TextItalic, 15, Kit.Dim, true));
        for (int k = 0; k < mods.Count; k++) list.AddChild(ModRow(c, mods[k], c.Mods.IndexOf(mods[k].Id), k));
        v.AddChild(list);
        var o = new Offer();
        if (seam >= 0 && seam < mods.Count)
        {
            o.Group = "The oath";
            var m = mods[seam];
            var pin = Crafting.Pin(X, it, m.Id, crafter);
            o.Add(Card(c.Pinned == m.Id ? "Pinned" : $"Pin {m.Name}", pin, () => Work(pin, Sound.Sfx.Click), "Pin it", "pin"));
            var scrape = Crafting.Scrape(X, it, m.Id, crafter);
            scrape.Before = null;
            o.Add(Card($"Scrape {m.Name} off", scrape, () => Work(scrape, Sound.Sfx.Click), "Scrape", "scrape"));
        }
        o.Group = "The chart";
        var inkFoe = Crafting.Ink(X, it, true, crafter);
        o.Add(Card("Ink the foe's side", inkFoe, () => Work(inkFoe, Sound.Sfx.Click), "Ink", "ink:foe"));
        var inkYou = Crafting.Ink(X, it, false, crafter);
        o.Add(Card("Ink your side", inkYou, () => Work(inkYou, Sound.Sfx.Click), "Ink", "ink:you"));
        var burn = Crafting.Burn(X, it, crafter);
        o.Add(Card("Burn and redraw", burn, () => Work(burn, Sound.Sfx.Cage), "Burn", "burn"));
        var from = Crafting.AnnotateFrom(Ch, it);
        var note = Crafting.Annotate(X, it, from, crafter);
        if (from?.Chart is { } f) { note.Before = null; note.After = $"{note.After}, written from {f.Name}, which is given up"; }
        o.Add(Card("Annotate", note, () => Work(note, Sound.Sfx.Page), "Annotate", "annotate"));
        Lay(v, o, $"What {He} can do", seam >= 0 && seam < mods.Count ? $"with {mods[seam].Name}, or the whole chart" : null);
    }

    static string Pct(double x) => $"{Math.Round(x * 100)}%";

    /// <summary>One mod sworn on a chart, sealed in wax beside its terms (the table's own look): red wax for
    /// the foe's side, violet for yours; what it asks, what it pays; pinned, said so.</summary>
    Control ModRow(Maps.Chart c, Maps.ChartMod m, int index, int k)
    {
        bool on = k == seam, pinned = c.Pinned == m.Id;
        var box = new StyleBoxFlat { BgColor = on ? new Color("#33251b") : Kit.Well, BorderColor = on ? Style.Ember : new Color("#0a090b"), CornerDetail = 4 };
        box.SetCornerRadiusAll(3);
        box.SetBorderWidthAll(on ? 1 : 0);
        box.BorderWidthTop = 1;
        box.ContentMarginLeft = box.ContentMarginRight = 12;
        box.ContentMarginTop = box.ContentMarginBottom = 7;
        var panel = Style.Panel(box);
        panel.MouseFilter = MouseFilterEnum.Stop;
        var seal = new Panel { CustomMinimumSize = new Vector2(34, 34), MouseFilter = MouseFilterEnum.Ignore, SizeFlagsVertical = SizeFlags.ShrinkCenter };
        var wax = Style.Box(m.Prefix ? new Color("#8a1c14") : new Color("#3a2a5a"), m.Prefix ? new Color("#5a0e0a") : new Color("#221636"), 2, 17, 0);
        wax.ShadowColor = new Color(0, 0, 0, 0.35f); wax.ShadowSize = 3; wax.ShadowOffset = new Vector2(1, 2);
        seal.AddThemeStyleboxOverride("panel", wax);
        var pays = new List<string>();
        if (m.Quantity > 0) pays.Add($"{Pct(m.Quantity)} more found");
        if (m.Rarity > 0) pays.Add($"{Pct(m.Rarity)} finer");
        if (m.PackSize > 0) pays.Add($"packs {Pct(m.PackSize)} larger");
        var words = Style.V(1, Style.Label(m.Says, Style.UiBold, 17, Kit.Ink, true),
            Style.Label($"{m.Name}  ·  pays {string.Join(", ", pays)}", Style.TextItalic, 15, Kit.Dim, true));
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var h = Style.H(14, seal, words);
        if (pinned) h.AddChild(Style.Label("PINNED", Style.UiHeavy, 12, Style.GoldHi));
        if (on) h.AddChild(Style.Label("ON THE TABLE", Style.UiHeavy, 12, Style.Ember));
        panel.AddChild(h);
        panel.MouseDefaultCursorShape = CursorShape.PointingHand;
        panel.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) Pick(k); };
        Nav.Mark(panel, $"seam:{k}", () => Pick(k));
        if (index >= 0) rows[index] = (panel, seal);
        return panel;
    }

    /* ---------------------------------------------------- the slurry's -- */

    /// <summary>The one gamble, as the anvil's main work at Snib's (and the scars' glass after the cure):
    /// one wide card with his word on the jar, the odds as a bar cut by their weights, what each would
    /// mean for this piece, and the press, held.</summary>
    void Steeping(ItemInstance it, Offer o)
    {
        o.Group = "Steep";
        var q = Crafting.Steep(X, it, crafter);
        // Refused for what the piece is (not for want of a jar): said once, quietly, with no odds.
        if (q.Blocked is { } why && (!Crafting.Workable(it) || Crafting.Slurried(it) || Crafting.Seams(it) == 0)) { o.Note(why); return; }
        var slab = Style.V(Style.Gap3);
        var top = Style.H(10, Style.Label("Steep it in slurry", Style.TextBold, 19, ItemViews.SlurryGreen, false, HorizontalAlignment.Left, false));
        if (Crafting.Line(crafter, "jar") is { } said) top.AddChild(Style.Label($"“{said}”", Style.TextItalic, 15, Kit.Dim, true));
        ((Control)top.GetChild(top.GetChildCount() - 1)).SizeFlagsHorizontal = SizeFlags.ExpandFill;
        slab.AddChild(top);
        slab.AddChild(SlurryOdds(it, LeftW - 2 * Pad - 32));
        var foot = Style.H(Style.Gap4);
        var words = Style.V(2);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        words.AddChild(Style.Label("Whatever it comes to, it is set for good after: no hand will work it again.", Style.UiBold, 15, Kit.Ink, true));
        string cost = string.Join("  ·  ", q.Takes.Select(kv => Items.Several(kv.Key, kv.Value)).Append(it.Heat is > 0 and int h ? $"all {h} of its heat" : "it is set already"));
        words.AddChild(Style.Label(cost, Style.Ui, 15, q.Ok ? Kit.Ink2 : Kit.Dim, true));
        // No jar: where one is had, rather than only that there is none.
        bool noJar = q.Takes.Keys.Any(m => Inventory.Count(Ch, m) == 0);
        if (!q.Ok && q.Blocked != closed)
            words.AddChild(Style.Label(noJar && Crafting.Does(crafter, Verb.Buy) ? $"No jar yet: {He} sells them, above the anvil." : q.Blocked!, Style.TextItalic, 15, Style.Bad, true));
        foot.AddChild(words);
        var b = Hold("Steep", q, () => Work(q, Sound.Sfx.Pour), "steep");
        b.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        foot.AddChild(b);
        slab.AddChild(foot);
        o.Wide = Style.Panel(Kit.PanelBox(16, 14, new Color("#151d12")), slab);
    }

    /// <summary>The slurry's odds, seen before the jar is opened (design 9): a bar cut by the weights,
    /// each cut its chance and its words, and under it what that would mean for this piece. Shared by
    /// Snib's bench and the pack, where the survivor steeps by hand.</summary>
    public static Control SlurryOdds(ItemInstance it, float width)
    {
        var v = Style.V(Style.Gap1);
        var odds = Crafting.Odds().ToList();
        var bar = Style.H(2);
        var cols = new Dictionary<string, Color>
        {
            ["up"] = ItemViews.BrightGrade, ["affix"] = ItemViews.SlurryGreen, ["nothing"] = new Color("#6f7a66"), ["down"] = Style.Bad,
        };
        var cap = Crafting.Cap(it);
        var plain = it.Affixes.Where(a => Items.Affix(a.Id) is { } d && d.Kindled == null && d.Grants == null && !d.Slurry).ToList();
        string Name(AffixRoll a) => Items.Affix(a.Id)?.Name ?? a.Id;
        // Wide (the bench), each outcome is a column under its cut of the bar; narrow (the pack), the
        // bar runs alone and the outcomes are listed under it.
        bool wide = width >= 700;
        var list = Style.V(Style.Gap1);
        foreach (var (o, p) in odds)
        {
            var col = cols.GetValueOrDefault(o, Style.Ink);
            var cell = Style.V(3);
            cell.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            cell.SizeFlagsStretchRatio = (float)p;
            var strip = new ColorRect { Color = col with { A = 0.85f }, CustomMinimumSize = new Vector2(wide ? Mathf.Max(120, (width - 2 * (odds.Count - 1)) * (float)p) : 0, 8), MouseFilter = MouseFilterEnum.Ignore };
            strip.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            strip.SizeFlagsStretchRatio = (float)p;
            var words = Style.V(2);
            words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            var head = Style.H(Style.Gap2, Style.Label($"{p:0%}", Style.Display, wide ? 22 : 17, col), Style.Label(Crafting.OddsWords(o), Style.UiBold, Style.Caption, Style.Ink, true));
            ((Control)head.GetChild(1)).SizeFlagsHorizontal = SizeFlags.ExpandFill;
            words.AddChild(head);
            // What it would be here: the powers it could move, the ones it could gain.
            string here = o switch
            {
                "up" => string.Join(", or ", plain.Where(a => a.Tier < Crafting.Bright)
                    .Select(a => $"{Name(a)} {Crafting.Grade(a.Tier)} to {Crafting.Grade(Math.Min(Crafting.Bright, Math.Max(a.Tier + 1, cap + 1)))}")),
                "affix" => string.Join(", ", Crafting.Rules.Slurry.Affixes.Select(Items.Affix).Where(d => d != null && d.Slots.Contains(Items.Get(it.Def).Kind) && it.Affixes.All(b => b.Id != d.Id)).Select(d => $"{d!.Name} ({d.Text(0)})")),
                "down" => string.Join(", or ", plain.Where(a => a.Tier > 0).Select(a => $"{Name(a)} {Crafting.Grade(a.Tier)} to {Crafting.Grade(a.Tier - 1)}")),
                _ => "the piece as it is, veined and set",
            };
            if (here == "") here = o switch { "down" => "nothing in it can fall a grade: only the veins", "affix" => "no slurry power fits it: only the veins", _ => "nothing in it can rise: only the veins" };
            words.AddChild(Style.Label(here, Style.TextItalic, Style.Caption, Style.InkDim, true));
            if (wide)
            {
                cell.AddChild(strip);
                cell.AddChild(words);
                bar.AddChild(cell);
            }
            else
            {
                bar.AddChild(strip);
                var chip = new ColorRect { Color = col with { A = 0.85f }, CustomMinimumSize = new Vector2(6, 0), MouseFilter = MouseFilterEnum.Ignore };
                list.AddChild(Style.H(Style.Gap2, chip, words));
            }
        }
        bar.CustomMinimumSize = new Vector2(width, 0);
        v.AddChild(bar);
        if (!wide) v.AddChild(list);
        return v;
    }

    /// <summary>A jar of the Dig's slurry: Snib's three a day, bought at his bench.</summary>
    Control JarTile()
    {
        var q = Crafting.BuyJar(X);
        var s = Crafting.Rules.Slurry;
        var h = Style.H(Style.Gap3);
        h.AddChild(ItemPhotos.Icon(Items.Get(s.Jar).Icon, 48, new Color("#8acf6a")));
        var words = Style.V(1);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        int carry = Inventory.Count(Ch, s.Jar), left = Crafting.JarsLeft(G.Journey.World);
        words.AddChild(Style.Label("A jar of slurry", Style.TextBold, 19, new Color("#a8e08a")));
        words.AddChild(Style.Label(q.Ok ? $"{q.Gold} gold  ·  {left} left today  ·  you carry {carry}" : q.Blocked!, Style.TextItalic, 15, q.Ok ? Kit.Dim : Style.Bad, true));
        h.AddChild(words);
        var b = Style.Button("Buy", null, q.Ok, true);
        b.Disabled = !q.Ok;
        b.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        b.Pressed += () => { if (!q.Ok) { Sound.Sfx.Deny(); return; } Sound.Sfx.Loot(false); if (G.Journey.Make(q)) Refresh(); };
        Nav.Mark(b, "jar", () => b.EmitSignal(BaseButton.SignalName.Pressed));
        h.AddChild(b);
        return Style.Panel(Kit.PanelBox(14, 10, new Color("#151d12")), h);
    }

    /* ------------------------------------------------------ make me one -- */

    /// <summary>"Make me one" on the anvil: his patterns, then what goes in the one chosen, each
    /// with what it takes and the piece it makes; or what is already on his bench.</summary>
    void Making(VBoxContainer v)
    {
        var c = Crafting.Rules.Commission;
        var ordered = Crafting.Ordered(G.Journey.World);
        var h = Style.H(18);
        string icon = pattern != null ? Items.Get(pattern).Icon : ordered is { } o0 ? Items.Get(o0.Def).Icon : "iron";
        var col = Style.RarityOf(c.Rarity);
        var photo = Style.Panel(Kit.TileBox(new ItemInstance { Def = pattern ?? ordered?.Def ?? "iron_helm", Rarity = c.Rarity }, true), ItemPhotos.Icon(icon, 88, col.Lightened(0.25f)));
        photo.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        h.AddChild(photo);
        var names = Style.V(4);
        names.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        names.AddChild(Style.Label("Make me one", Style.TextBold, 26, Style.GoldHi));
        names.AddChild(Style.Label($"A new piece off {His} anvil: {Items.RarityNames[c.Rarity].ToLowerInvariant()}, a material's answer in it at grade I, its heat full. Ready the next morning.",
            Style.TextItalic, 16, Kit.Dim, true));
        h.AddChild(names);
        v.AddChild(h);
        if (closed != null) v.AddChild(Closed());
        if (ordered is { } o)
        {
            var made = Crafting.Pattern(o.Def, o.Affix);
            bool ready = G.Journey.World.Day >= o.Ready;
            v.AddChild(Style.Label($"On {His} bench for you: {Inventory.Name(made)} ({Items.Affix(o.Affix)?.Text(0)}). "
                + (ready ? "Ready, but your pack is full: make room, and it is yours." : "Ready tomorrow morning."), Style.TextItalic, 16, Kit.Ink2, true));
            return;
        }
        v.AddChild(Kit.Head($"{Style.Cap1(His)} patterns", $"choose one  ·  more as {His} respect grows"));
        var grid = new GridContainer { Columns = 7, MouseFilter = MouseFilterEnum.Ignore };
        grid.AddThemeConstantOverride("h_separation", 10);
        grid.AddThemeConstantOverride("v_separation", 8);
        int i = 0;
        foreach (var (def, open, needs) in Crafting.Patterns(X))
        {
            var d = Items.Get(def);
            string id = def;
            var cell = Style.V(2);
            cell.CustomMinimumSize = new Vector2(106, 0);
            var view = ItemViews.Slot(new ItemInstance { Def = def, Rarity = c.Rarity }, 72, pattern == def, null, !open, open ? () => { pattern = id; Sound.Sfx.Click(); Refresh(); } : () => Sound.Sfx.Deny(), null,
                over => Tip(null, over), null, null, $"pattern:{i++}");
            if (!open) view.Modulate = new Color(1, 1, 1, 0.35f);
            var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            centre.AddChild(view);
            cell.AddChild(centre);
            cell.AddChild(Style.Label(d.Name, Style.UiBold, 14, open ? (pattern == def ? Style.GoldHi : Kit.Ink2) : Kit.Faint, true, HorizontalAlignment.Center));
            if (!open) cell.AddChild(Style.H(3, Glyphs.Icon("lock", 12, Kit.Faint), Style.Label($"at {needs}", Style.TextItalic, 13, Kit.Faint)));
            grid.AddChild(cell);
        }
        v.AddChild(grid);
        if (pattern != null && Items.Find(pattern) is { } pd)
        {
            var off = new Offer { Group = "What goes in it" };
            var choices = Crafting.Rules.Materials.Where(m => m.Value.Crafter == c.Crafter)
                .SelectMany(m => m.Value.Into.Where(a => Items.Affix(a)?.Slots.Contains(pd.Kind) == true).Select(a => (Material: m.Key, Affix: a))).ToList();
            var known = choices.Where(x => Inventory.Count(Ch, x.Material) > 0).ToList();
            if (known.Count == 0)
                off.Note(choices.Count == 0 ? $"Nothing {He} works goes into that."
                    : $"Bring {Him} something to work into it: {string.Join(", ", choices.Select(x => Items.Find(x.Material)?.Plural ?? x.Material).Distinct())}.");
            foreach (var (m, a) in known)
            {
                var q = Crafting.Commission(X, pattern, m, a);
                var md = Items.Get(m);
                off.Add(Card($"{pd.Name}: {Items.Affix(a)?.Name}", q, () => Order(q), "Make it", $"make:{m}:{a}", ItemPhotos.Icon(md.Icon, 40, Kit.Dim), $"From {md.Plural ?? md.Name}"));
            }
            off.Group = "What goes in it";
            Lay(v, off, "What goes in it", $"{Crafting.Article(Items.RarityNames[c.Rarity].ToLowerInvariant())} {pd.Name.ToLowerInvariant()}, and its answer");
        }
    }

    void Order(Quote q)
    {
        if (!q.Ok) { Sound.Sfx.Deny(); return; }
        Sound.Sfx.Anvil(1);
        if (G.Journey.Make(q)) { pattern = null; Refresh(); }
    }

    /* ----------------------------------------------------------- pieces -- */

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

    /// <summary>A press for what cannot be undone: held to full (Style.HoldButton), never asked twice; while
    /// under the pointer or the focus, the heat gauge shows what it may spend, as a press does.</summary>
    Button Hold(string title, Quote q, Action act, string navId)
    {
        var b = Style.HoldButton(title, () => { if (q.Ok) act(); else Sound.Sfx.Deny(); });
        b.Disabled = !q.Ok;
        void Show() => gauge?.Preview(q.HeatLo, q.HeatHi, q.Verb == Verb.Remake);
        void Hide() => gauge?.Clear();
        b.MouseEntered += Show;
        b.MouseExited += Hide;
        Nav.Mark(b, navId, b.Nudge, focus: Show, blur: Hide);
        return b;
    }

    /// <summary>A craft as a card, two to a row (the approved bench): its name; what it makes of the seam
    /// or the piece (before, then after, the after lit); where it comes from; then what it takes beside
    /// its one press, or why it cannot be done. lit: the card the night leans toward (a coal your
    /// skills evolve with) has the ember's edge.</summary>
    Control Card(string title, Quote q, Action act, string button, string navId, Control? icon = null, string? note = null, bool hold = false, Color? ink = null, bool lit = false)
    {
        var box = new StyleBoxFlat { BgColor = lit ? new Color("#33251b") : new Color("#2d2a2e"), BorderColor = lit ? Style.Ember : Kit.PanelHi, CornerDetail = 4 };
        box.SetCornerRadiusAll(3);
        box.SetBorderWidthAll(lit ? 1 : 0);
        box.BorderWidthTop = 1;
        box.ContentMarginLeft = box.ContentMarginRight = 14;
        box.ContentMarginTop = 9;
        box.ContentMarginBottom = 10;
        var card = Style.Panel(lit ? box : UiArt.Frame("panel", box));
        card.CustomMinimumSize = new Vector2(CardW, 0);
        card.SetMeta("ok", q.Ok);
        var v = Style.V(3);
        var top = Style.H(10);
        if (icon != null) { icon.SizeFlagsVertical = SizeFlags.ShrinkBegin; top.AddChild(icon); }
        var name = Style.Label(title, Style.TextBold, 19, ink ?? Kit.Ink, true);
        name.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        top.AddChild(name);
        v.AddChild(top);
        var after = new Color("#9ad8ff");
        if (q.Before != null && q.After != null)
        {
            var flow = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore };
            flow.AddThemeConstantOverride("h_separation", 6);
            flow.AddChild(Style.Label(q.Before, Style.Ui, 15, Kit.Dim, false, HorizontalAlignment.Left, false));
            flow.AddChild(Style.Label("to", Style.TextItalic, 15, Kit.Faint, false, HorizontalAlignment.Left, false));
            flow.AddChild(Style.Label(q.After, Style.UiBold, 15, after, false, HorizontalAlignment.Left, false));
            v.AddChild(flow);
        }
        else if (q.After != null) v.AddChild(Style.Label(q.After, Style.UiBold, 15, after, true));
        if (note != null) v.AddChild(Style.Label(note, Style.TextItalic, 15, lit ? Style.Ember : Kit.Dim, true));
        var foot = Style.H(12);
        var costs = Style.V(1);
        costs.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        costs.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        string cost = Cost(q);
        if (cost != "") costs.AddChild(Style.Label(cost, Style.Ui, 15, q.Ok ? Kit.Ink2 : Kit.Dim, true));
        if (!q.Ok && q.Blocked != closed) costs.AddChild(Style.Label(q.Blocked!, Style.TextItalic, 15, Style.Bad, true));
        foot.AddChild(costs);
        var b = hold ? Hold(button, q, act, navId) : Press(Style.Button(button, null, q.Ok, true), q, act, navId);
        b.SizeFlagsVertical = SizeFlags.ShrinkEnd;
        foot.AddChild(b);
        // (the press sits at the card's foot whatever its words run to, so a row of cards reads level)
        var room = new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore };
        v.AddChild(room);
        v.AddChild(foot);
        card.AddChild(v);
        return card;
    }

    void Work(Quote q, Action? sound = null, bool off = false)
    {
        if (!q.Ok || sel == null) { Sound.Sfx.Deny(); return; }
        string uid = sel;
        int heat = Chosen?.Heat ?? 0, at = seam;
        // Broken down, it leaves the anvil before the page is built again.
        if (off) { sel = null; seam = -1; }
        (sound ?? Sound.Sfx.Bash)();
        // The pad's focus comes back to the seam worked when the press it was on is gone.
        Nav.Prefer = seam >= 0 && SeamCrafts ? $"seam:{seam}" : "worn:0";
        // A craft changes what a piece does, never how it looks: the kit is folded back into the
        // fight (Journey.Work), and the figure is not dressed again.
        bool done = G.Journey.Work(uid, q, G.Battle);
        // What rings: the seam worked (a power bound into an open seam lands where it was); where the
        // slurry touched; the whole piece for what works all of it (-1: its head).
        int rung = q.Verb switch
        {
            Verb.Temper or Verb.WorkIn or Verb.Cage or Verb.Bind or Verb.Mark => q.Index >= 0 ? q.Index : at,
            Verb.Steep => q.Index,
            // A chart's new mod rings where it was written; a pin where it holds.
            Verb.Ink => (Inventory.Find(Ch, uid)?.Item.Chart?.Mods.Count ?? 0) - 1,
            Verb.Pin => Inventory.Find(Ch, uid)?.Item.Chart?.Mods.IndexOf(q.Affix ?? "") ?? -1,
            _ => -1,
        };
        struck = off || !done ? null : (uid, rung, heat, q.Verb);
        if (done && q.Verb == Verb.Steep && Inventory.Find(Ch, uid)?.Item is { } steeped)
        {
            var (text, mood) = Crafting.Outcome(steeped, q);
            came = (uid, text, mood);
        }
        Refresh();
    }

    /// <summary>What a gamble just came to, said on the anvil while that piece is on it.</summary>
    (string Uid, string Text, int Mood)? came;
    /// <summary>A commission just handed over: new on the anvil.</summary>
    string? handed;

    /// <summary>The hammer's moment, once the page is built again after a craft: the seam worked
    /// rings (its badge jumps, the row flares and cools), sparks fly off it, and the heat the craft
    /// took burns out of the gauge, or what it gave glows in.</summary>
    void Strike()
    {
        if (struck is not { } s || Chosen is not { } it || it.Uid != s.Uid) { struck = null; return; }
        if (striking || !IsInsideTree()) return;
        striking = true;
        // A craft can build the page more than once (the gear folded back into the fight, then the
        // pack touched): the moment plays once, a moment later, on the page as it stands then.
        GetTree().CreateTimer(0.05).Timeout += () =>
        {
            striking = false;
            if (!IsInsideTree() || struck is not { } now) return;
            struck = null;
            if (IsInstanceValid(gauge) && gauge!.IsInsideTree()) gauge.Burn(now.Heat);
            if (!rows.TryGetValue(now.Seam, out var r) || !IsInstanceValid(r.Row) || !r.Row.IsInsideTree()) return;
            var (row, badge) = r;
            badge.PivotOffset = badge.Size / 2;
            badge.Scale = Vector2.One * (now.Seam < 0 ? 1.12f : 1.4f);
            badge.CreateTween().TweenProperty(badge, "scale", Vector2.One, 0.4).SetTrans(Tween.TransitionType.Back).SetEase(Tween.EaseType.Out);
            // The row flares as the work does, and cools: the iron under the hammer, the lamp's warmth
            // a power was held over, the slurry's sick green, the gold of a thing made for you.
            var (fill, edge, slow) = now.Verb switch
            {
                Verb.Bind => (new Color(1f, 0.86f, 0.55f, 0.32f), new Color(1f, 0.95f, 0.78f, 0.9f), 1.6),
                Verb.Mark => (new Color(0.62f, 0.5f, 0.95f, 0.3f), new Color(0.9f, 0.82f, 1f, 0.9f), 1.6),
                Verb.Steep => (new Color(0.45f, 0.85f, 0.3f, 0.4f), new Color(0.8f, 1f, 0.6f, 0.9f), 1.4),
                Verb.Commission => (new Color(1f, 0.78f, 0.35f, 0.35f), new Color(1f, 0.9f, 0.6f, 0.95f), 1.6),
                _ => (new Color(1f, 0.55f, 0.18f, 0.5f), new Color(1f, 0.85f, 0.5f, 0.9f), 0.9),
            };
            var flare = new Panel { MouseFilter = MouseFilterEnum.Ignore, Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add } };
            flare.AddThemeStyleboxOverride("panel", Style.Box(fill, edge, 2, 5, 0));
            flare.Size = row.Size;
            row.AddChild(flare);
            flare.CreateTween().TweenProperty(flare, "modulate:a", 0f, slow).SetTrans(Tween.TransitionType.Quad).SetEase(Tween.EaseType.Out);
            flare.GetTree().CreateTimer(slow + 0.1).Timeout += () => { if (IsInstanceValid(flare)) flare.QueueFree(); };
            var at = badge.GetGlobalRect().GetCenter() - row.GetGlobalRect().Position;
            switch (now.Verb)
            {
                case Verb.Bind: Motes(row, at, new Color("#fff4d8"), new Color("#ffd27a"), -30, 1.8); break;
                case Verb.Mark: Motes(row, at, new Color("#efe2ff"), new Color("#9a7ae0"), -30, 1.8); break;
                case Verb.Steep: Motes(row, at, new Color("#e8ffc8"), new Color("#6fbf4a"), -70, 1.3); break;
                case Verb.Commission: Motes(row, at, new Color("#fff2c0"), new Color("#ffb24a"), -40, 1.5); break;
                case Verb.Ink or Verb.Pin or Verb.Scrape or Verb.Annotate: Motes(row, at, new Color("#f4ead0"), new Color("#9ab0d8"), -25, 1.4); break;
                default: Sparks(row, at, now.Verb is Verb.Cage or Verb.Rekindle or Verb.Burn); break;
            }
        };
    }

    static GradientTexture2D? mote;
    static GradientTexture2D Mote => mote ??= new GradientTexture2D
    {
        Width = 24, Height = 24, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f),
        Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.4f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.3f, 1f } },
    };

    /// <summary>Soft lights rising slowly off the work, not flying from it: a breath let go over the
    /// lamp (a binding), the slurry's bubbles (a steeping), a thing handed over.</summary>
    static void Motes(Control at, Vector2 local, Color hot, Color cool, float rise, double life)
    {
        var ramp = new Gradient
        {
            Colors = new[] { hot with { A = 0 }, hot, cool, cool with { A = 0 } },
            Offsets = new[] { 0f, 0.15f, 0.6f, 1f },
        };
        var p = new CpuParticles2D
        {
            Amount = 34, Lifetime = life, OneShot = true, Explosiveness = 0.7f, Emitting = false,
            Direction = new Vector2(0, -1), Spread = 55, Gravity = new Vector2(0, rise),
            InitialVelocityMin = 30, InitialVelocityMax = 120, DampingMin = 10, DampingMax = 40,
            EmissionShape = CpuParticles2D.EmissionShapeEnum.Sphere, EmissionSphereRadius = 22,
            ScaleAmountMin = 0.5f, ScaleAmountMax = 1.3f, ColorRamp = ramp, Position = local, ZIndex = 30,
            Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add },
            Texture = Mote,
        };
        at.AddChild(p);
        p.Emitting = true;
        p.GetTree().CreateTimer(life + 0.3).Timeout += () => { if (IsInstanceValid(p)) p.QueueFree(); };
    }

    bool striking;

    static GradientTexture2D? spark;
    static GradientTexture2D Spark => spark ??= new GradientTexture2D
    {
        Width = 10, Height = 30, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(0.5f, 0f),
        Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.55f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.35f, 1f } },
    };

    /// <summary>A burst of sparks off the anvil at a point in a control (embers for a coal).</summary>
    static void Sparks(Control at, Vector2 local, bool ember)
    {
        var ramp = new Gradient
        {
            Colors = ember
                ? new[] { new Color("#fff2c0"), new Color("#ff9a3c"), new Color("#c8321e"), new Color(0.5f, 0.08f, 0.02f, 0) }
                : new[] { new Color("#ffffff"), new Color("#ffd27a"), new Color("#ff8a2a"), new Color(0.6f, 0.15f, 0.02f, 0) },
            Offsets = new[] { 0f, 0.15f, 0.55f, 1f },
        };
        var p = new CpuParticles2D
        {
            Amount = ember ? 70 : 64, Lifetime = 0.95, OneShot = true, Explosiveness = 0.95f, Emitting = false,
            Direction = new Vector2(0.35f, -1), Spread = 75, Gravity = new Vector2(0, ember ? 140 : 700),
            InitialVelocityMin = 200, InitialVelocityMax = 560, DampingMin = 30, DampingMax = 80,
            ScaleAmountMin = 0.55f, ScaleAmountMax = 1.15f, ColorRamp = ramp, Position = local, ZIndex = 30,
            Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add },
            // Streaks, not squares: a soft spindle of light along the way each spark flies.
            Texture = Spark, ParticleFlagAlignY = true,
        };
        at.AddChild(p);
        p.Emitting = true;
        p.GetTree().CreateTimer(1.2).Timeout += () => { if (IsInstanceValid(p)) p.QueueFree(); };
    }

    public override bool Key(Act a)
    {
        if (a == Act.Cancel && making && pattern != null) { pattern = null; Refresh(); return true; }
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
    public enum Mark { Grade, Coal, Skill, Open, Slurry, Inscribed }
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
        bool bright = mark == Mark.Grade && tier >= Crafting.Bright;
        var col = mark switch { Mark.Coal => Style.Ember, Mark.Open => Style.GoldDim, Mark.Skill => Style.Day, Mark.Slurry => ItemViews.SlurryGreen, Mark.Inscribed => ItemViews.MarkInk, _ => bright ? ItemViews.BrightGrade : Style.RarityOf(tier) };
        // The bright grade gives off a little light of its own, past the badge's edge.
        if (bright)
            for (int i = 3; i >= 1; i--) DrawRect(r.Grow(i * 2.5f), ItemViews.SlurryGreen with { A = 0.07f * (4 - i) }, false, 2.5f);
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
        if (mark is Mark.Coal or Mark.Skill or Mark.Slurry)
        {
            DrawRect(r.Grow(-2), col with { A = 0.12f });
            var tex = Glyphs.Texture(mark switch { Mark.Coal => "flame", Mark.Slurry => "drop", _ => "book" }, 30, col);
            DrawTextureRect(tex, new Rect2(r.GetCenter() - new Vector2(15, 15), new Vector2(30, 30)), false);
            return;
        }
        DrawRect(r.Grow(-2), col with { A = 0.08f + 0.04f * tier });
        string numeral = Crafting.Grade(tier);
        var font = Style.Display;
        var size = font.GetStringSize(numeral, HorizontalAlignment.Left, -1, 22);
        DrawString(font, new Vector2((Size.X - size.X) / 2, 30), numeral, HorizontalAlignment.Left, -1, 22, col.Lightened(0.15f));
        // Pips: one for each grade it can reach here, lit for those it has.
        int n = mark == Mark.Inscribed ? 6 : Math.Max(cap, tier) + 1;
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

    /// <summary>The heat a craft just took, burning out of the cells it had (from the heat before
    /// to now), or what it gave glowing in: the gauge's half of the hammer's moment.</summary>
    public void Burn(int before)
    {
        if (before == heat) return;
        // A preview already up (the focus stayed on the press) waits its turn.
        if (preview) { pending = (lo, hi, grows); preview = false; }
        burnFrom = before;
        burnT = 0;
        Say();
        cells.QueueRedraw();
    }

    int burnFrom = -1;
    double burnT;
    (int Lo, int Hi, bool Grows)? pending;

    /// <summary>Show what a craft may cost (lo to hi), or add (negative); a remake grows the
    /// piece's full heat as well, a rekindle only refills it.</summary>
    public void Preview(int lo, int hi, bool grows = false)
    {
        if (lo == 0 && hi == 0) { Clear(); return; }
        // The heat a craft just took is seen go first; what the next would take, after.
        if (burnFrom >= 0) { pending = (lo, hi, grows); return; }
        this.lo = lo;
        this.hi = hi;
        this.grows = grows;
        preview = true;
        Say();
        cells.QueueRedraw();
    }

    public void Clear()
    {
        pending = null;
        if (!preview) return;
        preview = false;
        Say();
        cells.QueueRedraw();
    }

    void Say()
    {
        if (heat <= 0 && !(preview && lo < 0)) { words.Text = "Set: nothing more can be worked into it"; words.AddThemeColorOverride("font_color", Style.InkDim); return; }
        words.AddThemeColorOverride("font_color", Style.EmberHi);
        // Just worked: what it took, said while the cells burn out.
        if (burnFrom >= 0 && !preview)
        {
            words.Text = burnFrom > heat ? $"{burnFrom - heat} heat spent: {heat} of {full}" : $"+{heat - burnFrom} heat: {heat} of {full}";
            if (heat == 0) words.Text = "Set: the last of its heat spent";
            return;
        }
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
        if (burnFrom >= 0)
        {
            burnT += delta;
            if (burnT > 1.6)
            {
                burnFrom = -1;
                Say();
                if (pending is { } p) { pending = null; Preview(p.Lo, p.Hi, p.Grows); }
            }
            cells.QueueRedraw();
        }
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
                // Just spent: the cell flares white-hot and dies to dark over a second, the last first.
                if (!has && g.burnFrom > i)
                {
                    float t = Mathf.Clamp((float)(g.burnT - (g.burnFrom - 1 - i) * 0.07) / 0.8f, 0, 1);
                    DrawRect(r, dark);
                    DrawRect(r, new Color("#fff4d0").Lerp(Style.Ember, Mathf.Min(1, t * 2)) with { A = 1 - t });
                    DrawRect(r, Style.Line with { A = 0.25f * t }, false, 1);
                    continue;
                }
                if (!has) { DrawRect(r, dark); DrawRect(r, Style.Line with { A = 0.25f }, false, 1); continue; }
                // Just given (a rekindle, a remake): the new cells glow in from gold.
                if (g.burnFrom >= 0 && g.burnFrom <= i)
                {
                    float t = Mathf.Clamp((float)(g.burnT - (i - g.burnFrom) * 0.06) / 0.7f, 0, 1);
                    DrawRect(r, Style.Gold.Lerp(lit, t) with { A = 0.35f + 0.65f * t });
                    DrawRect(r, Colors.White with { A = 0.8f * (1 - t) }, false, 1.5f);
                    continue;
                }
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
