using System.Linq;
using Godot;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>The Wayfinder's table by the east gate: today's maps, three of
/// them, each an ember arena (a place, a people, a tier and the oaths it is
/// sworn under), and the story's fights that were lost, to be taken again
/// (Maps/MapOffers.cs, Arena/Arena.cs). Drawn as what it is (docs/UI_DESIGN.md
/// 7.8): three map sheets in their wooden frames lying on the Wayfinder's
/// table, each lettered with its place and sealed with its oaths, the way in
/// at its foot.</summary>
public partial class MapTableScreen : Overlay
{
    public override string Kind => "maps";

    public MapTableScreen(Game g) : base(g) { }

    static readonly Color Ink = new("#2e1d10"), InkSoft = new("#5a4126"), Asks = new("#8a2a18"), Gives = new("#2f5a22"), Answer = new("#4a3270");

    protected override void Build()
    {
        var w = G.Journey.World;
        int won = (int)w.Fact("arena.best").Number;
        var offers = MapOffers.Today(w.Day, System.Math.Max(1, won), (int)w.Fact("map.drawn").Number);
        bool again = w.Rematches.Count > 0;
        AddChild(Style.Scrim(G.CloseOverlay, 0.62f));
        const float W = 1580;
        float H = again ? 916 : 816;
        var at = new Vector2((1920 - W) / 2, (1080 - H) / 2);
        var plate = Style.Panel(Style.Plate(0));
        plate.Position = at;
        plate.Size = new Vector2(W, H);
        AddChild(plate);
        var table = new TableTop { Position = at + new Vector2(22, 92), Size = new Vector2(W - 44, H - 114) };
        AddChild(table);

        // The head: the table's name on its plaque, what the maps are, Close.
        var plaque = new Plaque("The Wayfinder's Table", 30, 110);
        AddChild(plaque);
        plaque.Position = new Vector2((1920 - plaque.CustomMinimumSize.X) / 2, at.Y + 14);
        var sub = Style.Label($"Maps to places the road forgets: each an ember arena, half an hour and what rules it at the end. {(won > 0 ? $"You have won tier {won}." : "You have won none yet.")} Spoils lean toward what answers the map.",
            Style.TextItalic, Style.Small, Style.InkDim, false, HorizontalAlignment.Center);
        sub.Position = at + new Vector2(0, 58);
        sub.Size = new Vector2(W, 22);
        AddChild(sub);
        var close = Nav.Skip(CloseButton("Esc", G.CloseOverlay));
        close.Position = at + new Vector2(W - 26 - close.CustomMinimumSize.X, 22);
        AddChild(close);

        // The three sheets, a little askew as they lie.
        float sheetW = 448, sheetH = 548, gap = (W - 44 - 3 * sheetW) / 4;
        float[] tilt = { -1.2f, 0.6f, -0.5f };
        for (int i = 0; i < offers.Count && i < 3; i++)
        {
            var o = offers[i];
            var pos = at + new Vector2(22 + gap + i * (sheetW + gap), 92 + 26);
            AddChild(Sheet(o, pos, new Vector2(sheetW, sheetH), tilt[i]));
            var pick = o;
            var enter = Nav.Id(Style.Button("Enter the arena", () => G.SetOut(pick), true), $"enter:{o.Spec.Name}");
            enter.CustomMinimumSize = new Vector2(240, 44);
            enter.Position = pos + new Vector2((sheetW - 240) / 2, sheetH + 22);
            AddChild(enter);
        }

        // The story's lost fights, to be taken again, on a slab along the table's foot.
        if (again)
        {
            var row = Style.H(Style.Gap4, Style.Label("FIGHTS TO TAKE AGAIN", Style.UiHeavy, Style.Caption, Style.Gold));
            foreach (var r in w.Rematches)
            {
                var spec = r;
                row.AddChild(Style.H(10, Style.V(0, Style.Label(r.Name, Style.UiBold, 17, Style.GoldHi), Style.Label(r.Sub != "" ? r.Sub : $"Tier {r.Tier}", Style.TextItalic, 14, Style.InkDim)),
                    Style.Button("Take it again", () => G.Rematch(spec), false, true)));
            }
            var slab = Style.Panel(Style.Slab(12), row);
            slab.Position = at + new Vector2(60, H - 112);
            slab.Size = new Vector2(W - 120, 72);
            AddChild(slab);
        }
        if (Controls.Instance.UsingPad)
        {
            var f = Footer((Act.Left, "Choose a map"), (Act.Confirm, "Enter the arena"), (Act.Cancel, "Close"));
            f.Position = new Vector2(0, at.Y + H + 12);
            f.Size = new Vector2(1920, 30);
            AddChild(f);
        }
    }

    /// <summary>One map: a sheet of parchment in a wooden frame, lettered by the Wayfinder.</summary>
    Control Sheet(MapOffer o, Vector2 pos, Vector2 size, float tiltDeg)
    {
        var holder = new Control { Position = pos, Size = size, PivotOffset = size / 2, RotationDegrees = tiltDeg, MouseFilter = MouseFilterEnum.Ignore };
        // Its shadow on the table.
        for (int k = 5; k >= 1; k--)
            holder.AddChild(new ColorRect { Color = new Color(0, 0, 0, 0.1f), Position = new Vector2(-k * 2 + 5, -k * 2 + 9), Size = size + new Vector2(k * 4, k * 4), MouseFilter = MouseFilterEnum.Ignore });
        var paper = Style.Panel(Style.Paper(30));
        paper.Size = size;
        paper.MouseFilter = MouseFilterEnum.Ignore;
        holder.AddChild(paper);
        // The compass the Wayfinder draws on every sheet, faint in its corner.
        var rose = Glyphs.Icon("compass", 84, InkSoft with { A = 0.22f });
        rose.Position = new Vector2(size.X - 118, size.Y - 150);
        holder.AddChild(rose);
        var people = MapOffers.People(o.People);
        Label L(string t, Font f, int sz, Color c) => Style.Label(t, f, sz, c, true, HorizontalAlignment.Left, false);
        var v = Style.V(6,
            Style.H(8, Style.Label($"TIER {o.Spec.Tier}", Style.UiHeavy, Style.Caption, InkSoft, false, HorizontalAlignment.Left, false), Style.Gems(System.Math.Min(o.Spec.Tier - 1, 5), 6)),
            L(o.Spec.Name.ToUpperInvariant(), Style.Display, 30, Ink),
            L($"Held by {people.Name}", Style.TextItalic, Style.Body, Ink),
            L($"Ruled by {people.BossName}", Style.Text, Style.Small, InkSoft),
            L($"Their bane: {string.Join(", ", people.Lean.Select(a => SurvivorUnchained.Rpg.Items.Affix(a)?.Name ?? a))} gear", Style.TextItalic, Style.Caption, Answer),
            Style.Rule());
        if (o.Spec.Oaths.Count == 0) v.AddChild(L("Sworn under no oath.", Style.TextItalic, Style.Small, InkSoft));
        foreach (var id in o.Spec.Oaths)
        {
            var oath = MapOffers.Oath(id);
            // Each oath sealed in wax beside its terms.
            var seal = new Panel { CustomMinimumSize = new Vector2(26, 26), MouseFilter = MouseFilterEnum.Ignore, SizeFlagsVertical = SizeFlags.ShrinkBegin };
            var wax = Style.Box(new Color("#8a1c14"), new Color("#5a0e0a"), 2, 13, 0);
            wax.ShadowColor = new Color(0, 0, 0, 0.35f); wax.ShadowSize = 3; wax.ShadowOffset = new Vector2(1, 2);
            seal.AddThemeStyleboxOverride("panel", wax);
            var terms = Style.V(1,
                L(oath.Name, Style.TextBold, Style.Small, Ink),
                L($"Asks: {oath.Asks}", Style.Text, Style.Caption, Asks),
                L($"Gives: {oath.Gives}", Style.Text, Style.Caption, Gives),
                L($"Answered by {oath.Answer}", Style.TextItalic, Style.Caption, Answer));
            terms.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            v.AddChild(Style.H(10, seal, terms));
        }
        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        v.AddChild(L("Half an hour; the ember from nothing", Style.TextItalic, Style.Caption, InkSoft));
        v.Position = new Vector2(34, 30);
        v.Size = size - new Vector2(68, 60);
        holder.AddChild(v);
        // The frame it is pinned in (frames/map_frame.png), laid over the sheet's edge.
        if (UiArt.Has("map_frame"))
        {
            var rim = new Panel { Size = size, MouseFilter = MouseFilterEnum.Ignore };
            rim.AddThemeStyleboxOverride("panel", UiArt.Frame("map_frame", new StyleBoxEmpty()));
            holder.AddChild(rim);
        }
        return holder;
    }
}

/// <summary>The Wayfinder's table top: dark oiled wood, its grain running the length, lit from above.</summary>
public partial class TableTop : Control
{
    public TableTop() { MouseFilter = MouseFilterEnum.Ignore; }

    public override void _Draw()
    {
        var s = Size;
        var top = new Color("#3a2416");
        var foot = new Color("#1c1009");
        DrawPolygon(new[] { Vector2.Zero, new Vector2(s.X, 0), s, new Vector2(0, s.Y) }, new[] { top, top, foot, foot });
        // The grain: long faint strokes, fixed so it does not shimmer.
        var rng = new RandomNumberGenerator { Seed = 7 };
        for (int i = 0; i < 140; i++)
        {
            float y = rng.Randf() * s.Y, x0 = rng.Randf() * s.X * 0.6f, len = rng.RandfRange(s.X * 0.2f, s.X * 0.7f);
            float wob = rng.RandfRange(-3, 3);
            DrawLine(new Vector2(x0, y), new Vector2(Mathf.Min(s.X, x0 + len), y + wob), new Color(0, 0, 0, rng.RandfRange(0.06f, 0.16f)), rng.RandfRange(1, 2.5f), true);
        }
        for (int i = 0; i < 40; i++)
        {
            float y = rng.Randf() * s.Y, x0 = rng.Randf() * s.X;
            DrawLine(new Vector2(x0, y), new Vector2(Mathf.Min(s.X, x0 + rng.RandfRange(80, 400)), y + rng.RandfRange(-2, 2)), new Color(1, 0.8f, 0.55f, 0.05f), 1, true);
        }
        // The lamp's light pooled in the middle, the edges falling into shadow.
        for (int k = 0; k < 10; k++)
            DrawRect(new Rect2(new Vector2(k * 6, k * 6), s - new Vector2(k * 12, k * 12)), new Color(0, 0, 0, 0.05f), false, 6);
        DrawRect(new Rect2(Vector2.Zero, s), new Color(0, 0, 0, 0.6f), false, 2);
    }
}
