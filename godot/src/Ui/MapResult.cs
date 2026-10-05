using System;
using System.Linq;
using Godot;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>
/// A Wayfinder's map over (Play/Zones/MapRun.cs), on its own page, of the night's result's
/// family but told for the build, not the hum (docs/EXPERIENCE_AUDIT.md, "A map's shape"): the
/// verdict and the chart it was; the time, the falls, the slain and the ground taken counting
/// up; then loot first, a find at a time, the best last (gear by rarity, the charts won, what
/// was carried out, the gold); and the atlas's line, the mark the map left on it.
/// </summary>
public partial class MapResultScreen : TellingScreen
{
    readonly MapResult r;
    readonly MapSpoils spoils;
    public override string Kind => "mapresult";
    public override bool Dismissable => false;

    public MapResultScreen(Game g, MapResult result, MapSpoils spoils) : base(g) { r = result; this.spoils = spoils; }

    protected override void Build()
    {
        HideHud();
        Retell();
        // (a click anywhere tells the rest at once)
        AddChild(new Backdrop(() => told = true, r.Cleared ? 0.82f : 0.9f));
        var wrap = Style.Centered(Style.V(14), new Vector2(1420, 940));
        AddChild(wrap);
        var people = MapOffers.People(r.Chart.People);
        var banner = Style.Panel(OrnateBox.Make(OrnateBox.Kind.Banner, 30, r.Cleared ? Style.Gold : Style.BloodHi),
            Style.Label(r.Cleared ? "THE MAP IS CLEARED" : "THE MAP CLOSES", Style.Display, 40, r.Cleared ? new Color("#ffe6b8") : Style.BloodHi, false, HorizontalAlignment.Center));
        banner.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        wrap.AddChild(banner);
        wrap.AddChild(Style.Label(r.Chart.Name, Style.TextItalic, Style.Lead, Style.GoldHi, false, HorizontalAlignment.Center));
        // What the chart was: its tier, who held it, what it was sworn under.
        var sworn = r.Chart.Rolled.Select(m => m.Name).ToList();
        wrap.AddChild(Style.Label($"Tier {r.Chart.Tier}  ·  held by {people.Name}{(sworn.Count > 0 ? "  ·  " + string.Join(", ", sworn) : "")}",
            Style.Ui, Style.Small, Style.InkDim, true, HorizontalAlignment.Center));

        // Beat one: the map's numbers.
        var tally = Style.H(48, Stat("hourglass", r.Seconds, Clock, r.Cleared ? "cleared in" : "held out", 0.5, r.Cleared));
        double at = 0.85;
        // Falls are counted where a map allows more than one, or where she rose again (Not Yet) and
        // cleared it; where one fall ends it, the verdict has already said so.
        if (MapRun.FallsAllowed > 1 || r.Falls > 0 && r.Cleared)
        {
            tally.AddChild(Stat("heart", r.Falls, x => MapRun.FallsAllowed > 1 ? $"{x:0} / {MapRun.FallsAllowed}" : $"{x:0}", MapRun.FallsAllowed > 1 ? "falls" : "rose again", at, r.Falls < MapRun.FallsAllowed));
            at += 0.35;
        }
        tally.AddChild(Stat("skull", r.Kills, x => $"{x:N0}", "slain", at, r.Cleared));
        tally.AddChild(Stat("sigil", r.PacksCleared, x => $"{x:0} / {r.Packs}", "packs broken", at + 0.35, r.Cleared));
        tally.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(tally);
        double cue = at + 0.35 + Count + 0.3;

        var two = Style.H(18);
        two.SizeFlagsVertical = SizeFlags.ExpandFill;
        wrap.AddChild(two);

        // Beat two: what came out, loot first, the best last.
        var outv = Style.V(10, new Section("What came out"));
        void Next(Control c, Action? sound, double gap = 0.42) { outv.AddChild(Beat(c, cue, sound)); cue += gap; }
        if (spoils.Gear.Count > 0)
        {
            var grid = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore };
            grid.AddThemeConstantOverride("h_separation", 12);
            grid.AddThemeConstantOverride("v_separation", 10);
            outv.AddChild(grid);
            foreach (var it in spoils.Gear)
            {
                var found = it;
                grid.AddChild(Beat(Find(it), cue, () => Sound.Sfx.Loot(found.Rarity >= 3)));
                cue += it.Rarity >= 3 ? 0.6 : 0.32;
            }
        }
        else Next(Style.Label("No gear came out of it.", Style.TextItalic, Style.Small, Style.InkDim), null, 0.3);
        foreach (var c in spoils.Charts) Next(ChartFound(c), () => Sound.Sfx.Loot(true), 0.55);
        if (spoils.Materials.Count > 0 || r.Spilled.Count > 0) Next(Haul(spoils.Materials, r.Spilled, "Carried out"), () => Sound.Sfx.Loot(), 0.5);
        if (spoils.Gold >= 1) Next(Line("coin", $"{spoils.Gold:N0} gold", Style.GoldHi), Sound.Sfx.Gold);
        two.AddChild(Card(outv));

        // Beat three: the atlas, and the mark the map left on it.
        var atlas = Style.V(10, new Section("The atlas"));
        atlas.CustomMinimumSize = new Vector2(420, 0);
        var line = MapSpoils.AtlasLine(r.Chart, r.Cleared, r.FirstClear);
        atlas.AddChild(Beat(Style.Label(line, Style.TextItalic, Style.Lead, r.FirstClear ? Style.EmberHi : r.Cleared ? Style.Ink : Style.InkDim, true), cue, r.FirstClear ? Sound.Sfx.Discovery : null));
        cue += 0.45;
        atlas.AddChild(Beat(AtlasGrid(G.Journey.World, r.Chart), cue));
        cue += 0.4;
        int unspent = Atlas.Unspent(G.Journey.World);
        if (unspent > 0)
        {
            atlas.AddChild(Beat(Style.Label($"{unspent} point{(unspent == 1 ? "" : "s")} to spend on the atlas, at the Wayfinder's table.", Style.UiBold, Style.Small, Style.EmberHi, true), cue));
            cue += 0.3;
        }
        two.AddChild(Card(atlas, Style.Slab(18)));

        // Beat four: a line for how it went, and back to the Waystation.
        var after = r.Cleared ? "The Wayfinder will want it for her margins." : $"The chart is spent. {people.BossName} keeps the ground, for now.";
        wrap.AddChild(Beat(Style.Label(after, Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center), cue, Sound.Sfx.Page));
        cue += 0.5;
        wrap.AddChild(Beat(Onward("Back to the Waystation", () => G.LeaveMap(r)), cue));
    }

    /// <summary>A find, as a small card in its rarity: the thing, its name and kind, its first line;
    /// held over, the whole card beside it.</summary>
    Control Find(ItemInstance it)
    {
        var col = Style.RarityOf(it.Rarity);
        var card = Style.Panel(UiArt.Frame("card_light", Style.Box(new Color(0.07f, 0.062f, 0.08f, 0.9f), col with { A = 0.5f }, 1, 4, 10)));
        card.CustomMinimumSize = new Vector2(300, 0);
        card.MouseFilter = MouseFilterEnum.Stop;
        var slot = ItemViews.Slot(it, 56);
        slot.MouseFilter = MouseFilterEnum.Ignore;
        var words = Style.V(1, Style.Label(Inventory.Name(it), Style.TextBold, Style.Small, col, true),
            Style.Label(Inventory.RarityName(it), Style.Ui, Style.Caption, Style.InkDim));
        if (Inventory.Lines(it).FirstOrDefault(l => l != "") is { } first) words.AddChild(Style.Label(first, Style.Ui, Style.Caption, Style.Ink, true));
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        card.AddChild(Style.H(10, slot, words));
        card.MouseEntered += () => Tip(ItemViews.Card(it, G.Journey.Ch, true), card);
        card.MouseExited += () => Tip(null, null);
        return card;
    }

    /// <summary>A chart won: the next map in hand, its tier and who holds it, what it is sworn under.</summary>
    static Control ChartFound(ItemInstance it)
    {
        var c = it.Chart!;
        var col = Style.RarityOf(c.Rarity);
        var mods = c.Rolled.Select(m => m.Name).ToList();
        var words = Style.V(1, Style.Label(c.Name, Style.TextBold, Style.Body, col, true),
            Style.Label($"A chart: tier {c.Tier}, held by {MapOffers.People(c.People).Name}", Style.Ui, Style.Small, Style.Ink, true),
            Style.Label(mods.Count > 0 ? string.Join(", ", mods) : "Sworn under nothing", Style.TextItalic, Style.Caption, Style.InkDim, true));
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var mark = new Medallion(56, "", "map") { Ring = col, Ink = col.Lightened(0.3f), Core = new Color("#20160e") };
        var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        mc.AddChild(mark);
        return Style.H(12, mc, words);
    }

    /// <summary>The peoples against the tiers, a stone for each pair, lit where its ruler has fallen;
    /// the pair this map was, ringed. The beta shows the first tier and the next, still dark.</summary>
    public static Control AtlasGrid(World.WorldState w, Chart? here = null, bool paper = false)
    {
        // Up to the tier past the best (the next, dark, so the road shows), at most a window's worth.
        int last = Math.Clamp(Math.Max(Atlas.Best(w) + 1, here?.Tier ?? 1) + 1, 2, 16), span = paper ? 8 : 6, first = Math.Max(1, last - span + 1);
        var grid = new GridContainer { Columns = last - first + 2, MouseFilter = MouseFilterEnum.Ignore };
        grid.AddThemeConstantOverride("h_separation", 10);
        grid.AddThemeConstantOverride("v_separation", 6);
        grid.AddChild(new Control { MouseFilter = MouseFilterEnum.Ignore });
        for (int t = first; t <= last; t++) grid.AddChild(Style.Label(Numeral(t), Style.DisplayLight, 14, paper ? new Color("#5a4126") : Style.GoldDim, false, HorizontalAlignment.Center, !paper));
        foreach (var p in MapOffers.Peoples)
        {
            var name = Style.Label(Style.Cap1(p.Name), Style.UiBold, Style.Small, paper ? new Color("#2e1d10") : Style.Ink, false, HorizontalAlignment.Left, !paper);
            name.CustomMinimumSize = new Vector2(150, 0);
            grid.AddChild(name);
            for (int t = first; t <= last; t++)
                grid.AddChild(new AtlasStone(Atlas.Done(w, p.Id, t), here != null && here.People == p.Id && here.Tier == t, paper));
        }
        return grid;
    }

    static readonly string[] Numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI"];
    static string Numeral(int n) => n > 0 && n < Numerals.Length ? Numerals[n] : n.ToString();

    public override bool Key(Act a)
    {
        // The first press tells the rest at once; the next goes back to the Waystation.
        if (a is Act.Confirm or Act.Cancel && !Told) { told = true; return true; }
        if (a == Act.Confirm) { G.LeaveMap(r); return true; }
        return a is not (Act.Up or Act.Down or Act.Left or Act.Right);
    }
}

/// <summary>A pair of the atlas (a people at a tier): a dark stone, or one lit in ember where its
/// ruler has fallen; ringed in gold where the map just run was.</summary>
public partial class AtlasStone : Control
{
    readonly bool lit, here, paper;

    public AtlasStone(bool lit, bool here, bool paper = false)
    {
        this.lit = lit;
        this.here = here;
        this.paper = paper;
        CustomMinimumSize = new Vector2(30, 26);
        MouseFilter = MouseFilterEnum.Ignore;
    }

    public override void _Draw()
    {
        var c = Size / 2;
        Vector2[] Diamond(float r) => new[] { c + new Vector2(0, -r), c + new Vector2(r, 0), c + new Vector2(0, r), c + new Vector2(-r, 0) };
        if (lit)
        {
            DrawCircle(c, 11, Style.Ember with { A = 0.18f });
            DrawColoredPolygon(Diamond(7), Style.Ember);
            DrawColoredPolygon(Diamond(3.5f), Style.EmberHi);
        }
        else
        {
            // (on the atlas's paper, an empty pair is a ring of ink; on the dark page, a dark stone)
            DrawPolyline(Diamond(6).Append(c + new Vector2(0, -6)).ToArray(), paper ? new Color("#5a4126") with { A = 0.7f } : Style.GoldDim with { A = 0.6f }, paper ? 1.4f : 1, true);
        }
        if (here) DrawArc(c, 11, 0, Mathf.Tau, 28, paper ? new Color("#8a2a18") : Style.GoldHi, 1.5f, true);
    }
}
