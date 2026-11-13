using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The Lamps board's geometry (src/Ui/LampBoardModel.cs; LAMPS_SCREEN_BRIEF.md §5, §13, §16): the pad's
/// neighbor lists, the hit grid, and the labels' placement at every stop (no label on a lamp or another label).</summary>
public sealed class LampBoardTests(TestContent content) : IClassFixture<TestContent>
{
    static readonly string File_ = Path.Combine(DataFiles.Dir, "content", "lamps_v2.json");
    static bool HasData => File.Exists(File_);
    LampBoardModel M => content.LampBoard;
    static readonly Box Window = new(0, 0, 846, 642);       // C's board window

    /// <summary>Cinzel 600's advance, near enough: 0.78 em a letter (caps), plus the 0.16 em tracking.</summary>
    static double Width(string t, int px) => t.Length * px * 0.78 + (t.Length - 1) * Math.Round(px * 0.16);

    [Fact]
    public void Every_lamp_has_a_neighbor_list_and_a_pad_move()
    {
        if (!HasData) return;
        var m = M;
        Assert.Equal(574, m.Nodes.Length);
        foreach (var nd in m.Nodes)
        {
            Assert.NotEmpty(nd.Pad);
            Assert.Equal(nd.Pad.Length, nd.PadAngle.Length);
            Assert.All(nd.Adj, j => Assert.Contains(j, nd.Pad));
            // some direction always leads somewhere: toward each pad neighbor, the step lands
            Assert.True(m.Step(nd.I, nd.PadAngle[0]) >= 0, nd.Id);
        }
    }

    [Fact]
    public void The_hit_grid_finds_each_lamp_at_its_own_center()
    {
        if (!HasData) return;
        var m = M;
        foreach (var nd in m.Nodes)
            Assert.Equal(nd.I, m.Hit(nd.X, nd.Y, i => LampBoardModel.RoadD(m.Nodes[i].Kind) / 2 / LampBoardModel.RoadScale));
        Assert.Equal(-1, m.Hit(5000, 5000, _ => 10));
    }

    public static IEnumerable<object[]> Stops() =>
        new[] { "valley", "road", "lamp" }.SelectMany(s => new[] { "warden", "reaver", "arcanist", "stalker", "ford" }.Select(c => new object[] { s, c }));

    [Theory]
    [MemberData(nameof(Stops))]
    public void Labels_sit_clear_of_lamps_and_each_other(string stopName, string where)
    {
        if (!HasData) return;
        var m = M;
        double vs = m.ValleyScale(Window, 48);
        var start = m.Nodes.FirstOrDefault(nd => nd.Kind == "start" && nd.Calling == where);
        double cx = start?.X ?? 0, cy = start?.Y ?? 0;
        var v = stopName switch
        {
            "valley" => new BoardView(0, 0, vs, Window.W / 2, Window.H / 2),
            "lamp" => new BoardView(cx, cy, LampBoardModel.LampScale, Window.W / 2, Window.H / 2),
            _ => new BoardView(cx, cy, LampBoardModel.RoadScale, Window.W / 2, Window.H / 2),
        };
        var stop = LampBoardModel.StopOf(v.S, vs);
        Assert.Equal(stopName, stop.ToString().ToLowerInvariant());
        var discs = new List<(double X, double Y, double R)>();
        var lampOf = new List<int>();
        foreach (var nd in m.Nodes)
        {
            var (x, y) = v.Project(nd.X, nd.Y);
            if (x > -60 && x < Window.W + 60 && y > -60 && y < Window.H + 60)
            { discs.Add((x, y, LampBoardModel.Diameter(nd.Kind, v.S, vs) / 2 + 5)); lampOf.Add(nd.I); }
        }
        var allowed = new Box(40, 40, Window.W - 40, Window.H - 40);
        var lit = start != null ? new HashSet<int> { start.I } : null;
        var placed = m.PlaceLabels(v, stop, discs, allowed, [], Width, lit, lampOf);
        if (where != "ford") Assert.NotEmpty(placed);    // the Ford's middle names nothing at the Road and Lamp stops
        for (int a = 0; a < placed.Count; a++)
        {
            var b = placed[a].Box;
            Assert.True(b.Inside(allowed), placed[a].Text);
            Assert.DoesNotContain(discs, d => b.Hits(d.X, d.Y, d.R));
            for (int c = a + 1; c < placed.Count; c++) Assert.False(b.Overlaps(placed[c].Box), $"{placed[a].Text} / {placed[c].Text}");
        }
        // her own hearth is always named at the Road stop
        if (stopName == "road" && start != null)
            Assert.Contains(placed, p => p.Text.Contains("HEARTH") && p.Text.Contains(where.ToUpperInvariant()));
    }

    static readonly Box Win = new(0, 0, 846, 642);

    [Fact]
    public void The_card_goes_right_when_clean_and_stays_in_the_window()
    {
        var lamps = new List<(double X, double Y, double R)> { (200, 300, 10), (150, 300, 8) };
        var s = LampBoardModel.PlaceCard(200, 300, 15, 380, 200, lamps, [(200, 300, 15)], [], Win);
        Assert.Equal("right", s.Side);
        Assert.Equal(0, s.Score);
        Assert.True(s.Rect.Inside(Win.Grow(-16)));
        Assert.Equal(200 + 15 + 22, s.Rect.X0);
    }

    [Fact]
    public void The_card_never_covers_a_lit_lamp_or_the_focus()
    {
        // lit lamps fill the right side and the lower right: it must go elsewhere (above, where a 380 x 200 card fits)
        var lit = new List<(double X, double Y, double R)>();
        for (int x = 260; x < 830; x += 30) for (int y = 280; y < 600; y += 30) lit.Add((x, y, 6));
        var s = LampBoardModel.PlaceCard(200, 300, 15, 380, 200, lit, lit.Append((200, 300, 15)).ToList(), [], Win);
        Assert.NotEqual("right", s.Side);
        Assert.True(s.Score < 100, $"covers a protected lamp: {s}");
        Assert.DoesNotContain(lit, d => s.Rect.Hits(d.X, d.Y, d.R));
        Assert.False(s.Rect.Hits(200, 300, 15));
        Assert.True(s.Rect.Inside(Win.Grow(-16)));
    }

    [Fact]
    public void The_card_takes_the_least_overlap_when_no_spot_is_clean()
    {
        // unlit lamps everywhere, 16 px apart (none protected): every edge band crosses some (a lamp wholly under the
        // card is covered, not crossed), so the least crossed spot, still inside the window
        var lamps = new List<(double X, double Y, double R)>();
        for (int x = 10; x < 846; x += 16) for (int y = 10; y < 642; y += 16) lamps.Add((x, y, 6));
        var s = LampBoardModel.PlaceCard(420, 320, 15, 380, 200, lamps, [(420, 320, 15)], [], Win);
        Assert.True(s.Score > 0 && s.Score < 100);
        Assert.True(s.Rect.Inside(Win.Grow(-16)));
        Assert.False(s.Rect.Hits(420, 320, 15));
        // brute force: its score on the band's rule (6 px either side of the edge)
        int Score(Box r)
        {
            var band = r.Grow(6);
            int c = lamps.Count(d => band.Hits(d.X, d.Y, d.R) && !(d.X - d.R >= r.X0 + 6 && d.X + d.R <= r.X1 - 6 && d.Y - d.R >= r.Y0 + 6 && d.Y + d.R <= r.Y1 - 6));
            return c + (band.Hits(420, 320, 15) ? 100 : 0);
        }
        Assert.Equal(Score(s.Rect), s.Score);
    }

    [Fact]
    public void A_lamp_just_inside_the_cards_edge_counts_as_crossing_it()
    {
        // fix round 1 (C_mouse: the card's top edge touched a lamp): a disc 2 px inside the edge is on the band
        var r = new Box(100, 100, 480, 300);
        Assert.True(LampBoardModel.Crosses(r, (300, 104, 6)));
        Assert.True(LampBoardModel.Crosses(r, (300, 96, 6)));
        Assert.False(LampBoardModel.Crosses(r, (300, 200, 6)));
        Assert.False(LampBoardModel.Crosses(r, (300, 80, 6)));
    }

    [Fact]
    public void A_protected_lamp_is_a_hard_reject_and_the_card_pushes_out_to_clear_it()
    {
        // fix round 1 (C_day: clear about 24 px further up). The focus near the right edge, lit lamps beside and below it,
        // one just above the default "above" spot's band and the left side walled in: only a spot pushed further up clears
        var win = new Box(0, 0, 846, 642);
        var lit = new List<(double X, double Y, double R)>();
        for (int x = 20; x < 830; x += 24) for (int y = 360; y < 640; y += 24) lit.Add((x, y, 6));
        for (int y = 20; y < 360; y += 24) { lit.Add((20, y, 6)); lit.Add((60, y, 6)); }
        // a lit lamp in the band of every "above" spot at 22 px: a 220 px card's bottom at y 300 - 15 - 22 = 263
        for (int x = 80; x < 830; x += 24) lit.Add((x, 270, 6));
        var prot = lit.Append((420, 300, 15)).ToList();
        var s = LampBoardModel.PlaceCard(420, 300, 15, 380, 220, lit, prot, [], win);
        Assert.True(s.Score < 100, $"covers a protected lamp: {s}");
        Assert.DoesNotContain(prot, d => s.Rect.Grow(6).Hits(d.X, d.Y, d.R));
        Assert.True(s.Rect.Inside(win.Grow(-16)));
    }

    [Fact]
    public void The_card_avoids_labels_and_clamps_when_nothing_fits()
    {
        // a label right of the focus: the card goes below it, 40 px clear of the label (§16: labels keep 40 px)
        var label = new Box(230, 200, 640, 290);
        var s = LampBoardModel.PlaceCard(200, 300, 15, 380, 200, [], [(200, 300, 15)], [label], Win);
        Assert.Equal(0, s.Score);
        Assert.False(s.Rect.Grow(40).Overlaps(label));
        var tiny = new Box(0, 0, 300, 200);
        var c = LampBoardModel.PlaceCard(100, 100, 10, 380, 200, [], [], [], tiny);
        Assert.Equal("clamped", c.Side);
    }

    [Fact]
    public void Board_text_is_at_least_13_px()
    {
        foreach (var s in Enum.GetValues<BoardStop>()) Assert.True(LampBoardModel.LabelPx(s) >= 13);
        Assert.True(LampBoardModel.ChipPx >= 13);
    }

    [Fact]
    public void Sizes_follow_the_stops()
    {
        Assert.Equal(34, LampBoardModel.Diameter("start", LampBoardModel.RoadScale, 0.2), 3);
        Assert.Equal(34 * 1.3, LampBoardModel.Diameter("start", LampBoardModel.LampScale, 0.2), 3);
        Assert.Equal(14, LampBoardModel.Diameter("start", 0.2, 0.2), 3);
        Assert.Equal(4, LampBoardModel.Diameter("small", 0.15, 0.2), 3);
    }
}

/// <summary>Fix round 1: the card over the demo build (--lamps-demo's warden: the mock's lit set) at the Road stop. Each
/// lamp she can light now or within 4 (the frontier, the far notables the open focuses) is focused in turn with its path
/// preview, the view centered as the open centers it (her lit lamps, the path and the focus): the card never covers a
/// lit lamp, her hearth, the path or the focus (§16), its edge band tested against every lamp drawn.</summary>
[Collection("Balance")]
public sealed class LampCardDemoTests(TestContent content) : IClassFixture<TestContent>
{
    static readonly string File_ = Path.Combine(DataFiles.Dir, "content", "lamps_v2.json");
    static readonly string[] MockLit =
    [
        "warden.the_wardens_oath", "warden.hearth.p2", "sunderer.two_hands", "sunderer.s1", "sunderer.s2", "sunderer.s3",
        "sunderer.s4", "sunderer.the_long_cut", "sunderer.the_long_cut.second_cut", "sunderer.rite1",
        "sunderer.breaking_point", "warden.iron_hide", "warden.shield_bash", "warden.concussion", "warden.hand1",
    ];

    [Theory]
    [InlineData(200)]   // a short card (a small lamp: the collapsed title)
    [InlineData(236)]   // a notable's card with its feeds and prompt
    public void No_card_over_the_demo_build_covers_her_lit_lamps_hearth_path_or_focus(double h)
    {
        if (!File.Exists(File_)) return;
        Lamps.UseV2(true);
        try
        {
            var m = content.LampBoard;
            var a = Callings.Archetype("warden");
            var ch = Character.Create(new CreationChoice
            {
                Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
            }, seed: 7);
            ch.Level = 200;
            LampBook.Begin(ch, null);
            var litIds = LampBook.Now(ch).Lit;
            foreach (var id in MockLit) if (m.Index.ContainsKey(id)) litIds.Add(id);
            var lit = litIds.Where(m.Index.ContainsKey).Select(id => m.Index[id]).ToHashSet();
            int hearth = m.Index[Lamps.Start("warden")];
            var win = new Box(0, 0, 846, 642);       // C's board window
            double valleyS = m.ValleyScale(win, 48);
            int n = m.Nodes.Length;
            int tried = 0, covered = 0, moved = 0;
            var bad = new List<string>();
            for (int f = 0; f < n; f++)
            {
                if (lit.Contains(f)) continue;
                var path = LampAsk.PathTo(ch, null, m.Nodes[f].Id).Where(m.Index.ContainsKey).Select(id => m.Index[id]).ToList();
                if (path.Count is 0 or > 4) continue;
                tried++;
                var view = m.Center(lit.Concat(path).Append(f), win);
                var P = new (double X, double Y)[n];
                var R = new double[n];
                var drawn = new List<(double X, double Y, double R)>();
                for (int i = 0; i < n; i++)
                {
                    P[i] = view.Project(m.Nodes[i].X, m.Nodes[i].Y);
                    R[i] = LampBoardModel.Diameter(m.Nodes[i].Kind, view.S, valleyS) / 2 * (i == f ? 1.1 : 1.0);
                    if (P[i].X >= -60 && P[i].X <= 906 && P[i].Y >= -60 && P[i].Y <= 702) drawn.Add((P[i].X, P[i].Y, R[i]));
                }
                var prot = new List<(double X, double Y, double R)>();
                foreach (var i in lit) prot.Add((P[i].X, P[i].Y, R[i] + (i == hearth ? 12 : 4)));
                prot.Add((P[f].X, P[f].Y, R[f] + 4));
                // the path from the lit lamp next to its first step, its lamps and roads sampled as the board does
                int from = m.Nodes[path[0]].Adj.FirstOrDefault(lit.Contains, -1);
                var chain = new List<int>();
                if (from >= 0) chain.Add(from);
                chain.AddRange(path);
                foreach (var i in path) prot.Add((P[i].X, P[i].Y, R[i] + 4));
                for (int k = 0; k + 1 < chain.Count; k++)
                    for (int t = 0; t <= 12; t++)
                        prot.Add((P[chain[k]].X + (P[chain[k + 1]].X - P[chain[k]].X) * t / 12, P[chain[k]].Y + (P[chain[k + 1]].Y - P[chain[k]].Y) * t / 12, 3));
                var s = LampBoardModel.PlaceCard(P[f].X, P[f].Y, R[f] + 5, 380, h, drawn, prot, [], win);
                if (s.Score >= 100)
                {
                    // no spot clear here: the board makes room (LampBoard.Room), the focus and its path 64 px inside, her lit lamps 64 px inside
                    var near = path.Append(f).Select(i => P[i]).ToList();
                    var ro = LampBoardModel.RoomFor(P[f].X, P[f].Y, R[f] + 5, 380, h, new LampBoardModel.DiscGrid(prot, 32), win,
                        (ox, oy) => near.All(q => q.X + ox >= 64 && q.X + ox <= win.X1 - 64 && q.Y + oy >= 64 && q.Y + oy <= win.Y1 - 64)
                            && lit.All(i => P[i].X + ox >= 64 && P[i].X + ox <= win.X1 - 64 && P[i].Y + oy >= 64 && P[i].Y + oy <= win.Y1 - 64));
                    moved++;
                    if (ro is { } o) s = LampBoardModel.PlaceCard(P[f].X, P[f].Y, R[f] + 5, 380, h, drawn, prot, [], new Box(-o.X, -o.Y, win.X1 - o.X, win.Y1 - o.Y));
                }
                var band = s.Rect.Grow(6);
                if (s.Side == "clamped" || prot.Any(d => band.Hits(d.X, d.Y, d.R)))
                {
                    covered++;
                    if (bad.Count < 8) bad.Add($"{m.Nodes[f].Id} ({P[f].X:F0},{P[f].Y:F0}) {s}");
                }
            }
            Assert.True(tried > 10, $"only {tried} lamps 1-4 out");
            Assert.True(covered == 0, $"{covered} of {tried} cards cover a protected lamp ({moved} needed room): " + string.Join("; ", bad));
        }
        finally { Lamps.UseV2(false); }
    }
}
