"""The bench's crafts grouped by what is done (Temper, Work in, Cage...), one group open under tabs,
so the left panel fits the screen without a long scroll; and the strip and cards made compact."""
import re
from ed import sub, ROOT
import os
P = os.path.join(ROOT, "src/Ui/Forge.cs")
s = open(P, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
s = s.replace("\r\n", "\n")

def rep(old, new, count=1):
    global s
    if old not in s:
        raise SystemExit("NOT FOUND: " + old[:100])
    s = s.replace(old, new, count)

# Every card and note goes into the group being offered.
s = re.sub(r"\b(o|off)\.Cards\.Add\(", r"\1.Add(", s)
s = re.sub(r"\b(o|off)\.Notes\.Add\(", r"\1.Note(", s)

rep("""    sealed class Offer
    {
        public readonly List<Control> Cards = new();
        public readonly List<string> Notes = new();
        public Control? Wide;
    }""",
"""    sealed class Offer
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
    string? craftTab;""")

rep("""        bool open = seam >= it.Affixes.Count;
        string? where = seam >= 0 && SeamCrafts ? open ? "at the open seam" : $"at {Items.Affix(it.Affixes[seam].Id)?.Name ?? "the seam"}" : null;
        v.AddChild(Kit.Head($"What {He} can do with it", where != null ? $"{where}  ·  and with the whole piece" : null));
        Lay(v, offer);
    }""",
"""        bool open = seam >= it.Affixes.Count;
        string? where = seam >= 0 && SeamCrafts ? open ? "at the open seam" : $"at {Items.Affix(it.Affixes[seam].Id)?.Name ?? "the seam"}" : null;
        Lay(v, offer, $"What {He} can do", where);
    }""")

rep("""    /// <summary>The offer laid out: the wide card, the cards two to a row (scrolling past three rows),
    /// and the quiet notes, each a line.</summary>
    void Lay(VBoxContainer v, Offer offer)
    {
        if (offer.Wide != null) v.AddChild(offer.Wide);
        if (offer.Cards.Count > 0)
        {
            var grid = new GridContainer { Columns = 2, MouseFilter = MouseFilterEnum.Ignore };
            grid.AddThemeConstantOverride("h_separation", 12);
            grid.AddThemeConstantOverride("v_separation", 10);
            foreach (var card in offer.Cards) grid.AddChild(card);
            if (offer.Cards.Count > 6)
            {
                // More than three rows (a pack of donors to bind from): the rest scroll, the panel holds.
                var scroll = Style.Scroll(grid);
                scroll.CustomMinimumSize = new Vector2(LeftW - 2 * Pad, 3 * 128 + 20);
                v.AddChild(scroll);
            }
            else v.AddChild(grid);
        }
        foreach (var n in offer.Notes) v.AddChild(Style.Label(n, Style.TextItalic, 15, Kit.Dim, true));
    }""",
"""    /// <summary>The offer laid out under its head: the wide card (the slurry's odds); tabs by what is done
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
        v.AddChild(Kit.Head(title, groups.Count > 1 ? null : note, end));
        if (groups.Count > 1 && note != null) v.AddChild(Style.Label(note, Style.TextItalic, 15, Kit.Dim, false));
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
    }""")

# Groups, set where each kind of craft is offered.
rep("""        if (Plain(ad) && Crafting.Does(crafter, Verb.Temper))
        {
            int cap = Crafting.Cap(it);""",
"""        if (Plain(ad) && Crafting.Does(crafter, Verb.Temper))
        {
            o.Group = "Temper";
            int cap = Crafting.Cap(it);""")
rep("""    void WorkIn(ItemInstance it, int over, AffixDef? lost, Offer o)
    {
""", """    void WorkIn(ItemInstance it, int over, AffixDef? lost, Offer o)
    {
        o.Group = "Work in";
""")
rep("""    void Coals(ItemInstance it, int k, bool open, bool coal, Offer o)
    {
""", """    void Coals(ItemInstance it, int k, bool open, bool coal, Offer o)
    {
        o.Group = "Cage";
""")
rep("""        if (!Crafting.Does(crafter, Verb.Set)) return;
""", """        if (!Crafting.Does(crafter, Verb.Set)) return;
        o.Group = "Set";
""")
rep("""    void Whole(ItemInstance it, Offer o)
    {
""", """    void Whole(ItemInstance it, Offer o)
    {
        o.Group = "The piece";
""")
rep("""    void Binding(ItemInstance it, int k, bool open, AffixDef? lost, Offer o)
    {
""", """    void Binding(ItemInstance it, int k, bool open, AffixDef? lost, Offer o)
    {
        o.Group = "Bind";
""")
rep("""    void Marking(ItemInstance it, int k, bool open, AffixDef? here, Offer o)
    {
""", """    void Marking(ItemInstance it, int k, bool open, AffixDef? here, Offer o)
    {
        o.Group = "Mark";
""")
rep("""    void Steeping(ItemInstance it, Offer o)
    {
""", """    void Steeping(ItemInstance it, Offer o)
    {
        o.Group = "Steep";
""")
# The set heat's note belongs to every seam craft: under Temper.
rep("""        // Set: every seam's craft would refuse alike, so it is said once.
        if (it.Heat is 0)
        {""", """        // Set: every seam's craft would refuse alike, so it is said once.
        o.Group = "The seam";
        if (it.Heat is 0)
        {""")
# The chart's crafts: the oath chosen, then the whole chart.
rep("""        var o = new Offer();
        if (seam >= 0 && seam < mods.Count)
        {
            var m = mods[seam];""", """        var o = new Offer();
        if (seam >= 0 && seam < mods.Count)
        {
            o.Group = "The oath";
            var m = mods[seam];""")
rep("""        var inkFoe = Crafting.Ink(X, it, true, crafter);""", """        o.Group = "The chart";
        var inkFoe = Crafting.Ink(X, it, true, crafter);""")
rep("""        v.AddChild(Kit.Head($"What {He} can do with it", seam >= 0 && seam < mods.Count ? $"with {mods[seam].Name}  ·  and with the whole chart" : "with the whole chart"));
        Lay(v, o);""", """        Lay(v, o, $"What {He} can do", seam >= 0 && seam < mods.Count ? $"with {mods[seam].Name}, or the whole chart" : null);""")
rep("""            v.AddChild(Kit.Head("What goes in it", $"{Crafting.Article(Items.RarityNames[c.Rarity].ToLowerInvariant())} {pd.Name.ToLowerInvariant()}, and its answer"));
            Lay(v, off);""", """            off.Group = "What goes in it";
            Lay(v, off, "What goes in it", $"{Crafting.Article(Items.RarityNames[c.Rarity].ToLowerInvariant())} {pd.Name.ToLowerInvariant()}, and its answer");""")
rep("""            var off = new Offer();
            var choices""", """            var off = new Offer { Group = "What goes in it" };
            var choices""")

# A new piece or seam opens its own first group.
rep("""        sel = uid;
        seam = -1;
        making = false;""", """        sel = uid;
        seam = -1;
        craftTab = null;
        making = false;""")
rep("""        if (seam == k) return;
        seam = k;""", """        if (seam == k) return;
        seam = k;
        craftTab = null;""")

# The card knows whether it can be done (for the tabs' counts).
rep("""        var card = Style.Panel(lit ? box : UiArt.Frame("panel", box));
        card.CustomMinimumSize = new Vector2(CardW, 0);""", """        var card = Style.Panel(lit ? box : UiArt.Frame("panel", box));
        card.CustomMinimumSize = new Vector2(CardW, 0);
        card.SetMeta("ok", q.Ok);""")
# Compact cards.
rep("""        box.ContentMarginTop = 11;
        box.ContentMarginBottom = 12;""", """        box.ContentMarginTop = 9;
        box.ContentMarginBottom = 10;""")
rep("""        var v = Style.V(5);
        var top = Style.H(10);""", """        var v = Style.V(3);
        var top = Style.H(10);""")

# The strip: the anvil's own tabs ride its name's row; a smaller likeness.
rep("""        var size = new Vector2I(124, 132);""", """        var size = new Vector2I(104, 112);""")
rep("""        words.AddChild(Style.Label((name ?? def?.Place ?? "The bench").ToUpperInvariant(), Style.Display, 30, Kit.Ink, false, HorizontalAlignment.Left, false));""",
"""        var named = Style.H(12, Style.Label((name ?? def?.Place ?? "The bench").ToUpperInvariant(), Style.Display, 30, Kit.Ink, false, HorizontalAlignment.Left, false));
        ((Control)named.GetChild(0)).SizeFlagsHorizontal = SizeFlags.ExpandFill;
        // "Make me one" is the anvil's other work: a new piece from a pattern rather than one carried.
        if (Crafting.Does(crafter, Verb.Commission))
        {
            var tabs = Kit.Tabs(new[] { "At the anvil", "Make me one" }, making ? 1 : 0, k => { making = k == 1; if (making) sel = null; Refresh(); }, 15, 20,
                new[] { "", Crafting.Ordered(G.Journey.World) is { } o ? (G.Journey.World.Day >= o.Ready ? "ready" : "on the bench") : "" });
            tabs.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            named.AddChild(tabs);
        }
        words.AddChild(named);""")
rep("""        // "Make me one" is the anvil's other work: a new piece from a pattern rather than one carried.
        if (Crafting.Does(crafter, Verb.Commission))
            left.AddChild(Kit.Tabs(new[] { "At the anvil", "Make me one" }, making ? 1 : 0, k => { making = k == 1; if (making) sel = null; Refresh(); }, 16, 26,
                new[] { "", Crafting.Ordered(G.Journey.World) is { } o ? (G.Journey.World.Day >= o.Ready ? "ready" : "on the bench") : "" }));
""", "")
# The terms on one flowing line under a quiet head.
rep("""        v.AddChild(Kit.Head($"{Style.Cap1(His)} terms", axes.Count > 0 ? $"{His} {string.Join(", ", axes.Select(a => $"{a.ToString().ToLowerInvariant()} {npc[a]:0}"))}" : null));""",
"""        v.AddChild(Kit.Head($"{Style.Cap1(His)} terms", axes.Count > 0 ? $"{His} {string.Join(", ", axes.Select(a => $"{a.ToString().ToLowerInvariant()} {npc[a]:0}"))}" : null));
        v.AddThemeConstantOverride("separation", 2);""")

open(P, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))
print("ok")
