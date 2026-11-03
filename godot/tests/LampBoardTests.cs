using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The Lamps board's geometry (src/Ui/LampBoardModel.cs; LAMPS_SCREEN_BRIEF.md §5, §13, §16): the pad's
/// neighbor lists, the hit grid, and the labels' placement at every stop (no label on a lamp or another label).</summary>
public sealed class LampBoardTests
{
    static readonly string File_ = Path.Combine(DataFiles.Dir, "content", "lamps_v2.json");
    static bool HasData => File.Exists(File_);
    static LampBoardModel M => LampBoardModel.FromJson(File.ReadAllText(File_));
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
        // brute force: no candidate on the same rules does better
        int Score(Box r)
        {
            var band = r.Grow(6);
            int c = lamps.Count(d => band.Hits(d.X, d.Y, d.R) && !(d.X - d.R >= r.X0 && d.X + d.R <= r.X1 && d.Y - d.R >= r.Y0 && d.Y + d.R <= r.Y1));
            return c + (band.Hits(420, 320, 15) ? 100 : 0);
        }
        Assert.Equal(Score(s.Rect), s.Score);
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
