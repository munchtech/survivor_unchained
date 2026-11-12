using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Ui;
using SurvivorUnchained.World;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The Lamps screen's interaction rules (src/Ui/LampNav.cs, LampAsk.cs; LAMPS_SCREEN_BRIEF.md §9, §10): every
/// lamp reached by the stick alone, the visit's undo, a far lamp's path all or nothing, a branch out from its tips, and
/// labels clear at every zoom between the stops. Runs alone (it switches the board to v2).</summary>
[Collection("Balance")]
public sealed class LampNavTests(ITestOutputHelper log, TestContent content) : IClassFixture<TestContent>
{
    static readonly string File_ = Path.Combine(DataFiles.Dir, "content", "lamps_v2.json");
    static bool HasData => File.Exists(File_);
    LampBoardModel M => content.LampBoard;
    static readonly Box Window = new(0, 0, 846, 642);

    static CharacterData Make(string calling)
    {
        var a = Callings.Archetype(calling);
        var ch = Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, seed: 7);
        LampBook.DropUnknown(ch);
        return ch;
    }

    static WorldState Day => new() { Time = TimeOfDay.Day };

    [Fact]
    public void The_stick_alone_reaches_every_lamp_from_each_hearth()
    {
        if (!HasData) return;
        var m = M;
        var dirs = Enumerable.Range(0, 8).Select(k => k * Math.PI / 4).ToArray();
        int worstAll = 0;
        foreach (var start in m.Nodes.Where(nd => nd.Kind == "start"))
        {
            var d = new int[m.Nodes.Length];
            Array.Fill(d, -1);
            d[start.I] = 0;
            var q = new Queue<int>();
            q.Enqueue(start.I);
            var scratch = new List<int>();
            while (q.Count > 0)
            {
                int a = q.Dequeue();
                foreach (var ang in dirs)
                {
                    int b = LampNav.Stick(m, a, ang, scratch);
                    if (b >= 0 && d[b] < 0) { d[b] = d[a] + 1; q.Enqueue(b); }
                }
            }
            var missed = m.Nodes.Where(nd => d[nd.I] < 0).Select(nd => nd.Id).ToList();
            int worst = d.Max();
            worstAll = Math.Max(worstAll, worst);
            log.WriteLine($"{start.Id}: reached {m.Nodes.Length - missed.Count}/{m.Nodes.Length}, worst {worst} moves, mean {d.Where(x => x >= 0).Average():F1}");
            Assert.True(missed.Count == 0, $"{start.Id} misses {missed.Count}: {string.Join(", ", missed.Take(12))}");
        }
        log.WriteLine($"worst over the hearths: {worstAll}");
    }

    [Fact]
    public void A_road_neighbor_wins_within_fifty_degrees()
    {
        if (!HasData) return;
        var m = M;
        foreach (var nd in m.Nodes)
            foreach (var j in nd.Adj)
            {
                var o = m.Nodes[j];
                double ang = Math.Atan2(-(o.Y - nd.Y), o.X - nd.X);
                int got = LampNav.Stick(m, nd.I, ang);
                // straight at a road neighbor, the stick lands on a road neighbor (that one, or one as near in angle)
                Assert.Contains(got, nd.Adj);
            }
    }

    [Fact]
    public void Undo_restores_the_lamps_and_the_flare_exactly()
    {
        if (!HasData) return;
        Lamps.UseV2(true);
        try
        {
            foreach (var calling in new[] { "warden", "reaver", "arcanist", "stalker" })
                for (int seed = 1; seed <= 6; seed++)
                {
                    var ch = Make(calling);
                    ch.Level = 80;
                    var w = Day;
                    var rng = new Random(seed * 31 + calling.Length);
                    // some lamps lit before the visit
                    for (int k = 0; k < 8 && LampBook.Suggest(ch, w) is { } s0; k++) LampBook.Light(ch, w, s0);
                    var before = LampBook.Now(ch).Lit.ToList();
                    var flare = LampBook.Now(ch).Flare;
                    var visit = new LampSession(ch);
                    for (int k = 0; k < 30; k++)
                    {
                        var lit = LampBook.Now(ch).Lit;
                        if (rng.Next(4) == 0)
                        {
                            // a far lamp's path
                            var far = Lamps.All.Keys.Where(id => !lit.Contains(id)).OrderBy(id => id, StringComparer.Ordinal).ToList();
                            var pick = far[rng.Next(far.Count)];
                            var p = LampAsk.PathTo(ch, w, pick);
                            if (p.Count is > 0 and <= 4) Assert.NotNull(visit.LightPath(w, pick));
                            continue;
                        }
                        var can = lit.SelectMany(Lamps.Next).Distinct().Where(id => LampBook.CanLight(ch, w, id) == LampNo.None).OrderBy(id => id, StringComparer.Ordinal).ToList();
                        if (can.Count == 0) break;
                        Assert.True(visit.Light(w, can[rng.Next(can.Count)]));
                    }
                    Assert.NotEmpty(visit.LitHere);
                    // the visit's lamps go out anywhere (away from a lamp-post), newest first
                    while (visit.LitHere.Count > 0) Assert.NotNull(visit.UndoNewest());
                    Assert.Equal(before, LampBook.Now(ch).Lit);
                    Assert.Equal(flare, LampBook.Now(ch).Flare);
                }
        }
        finally { Lamps.UseV2(false); }
    }

    [Fact]
    public void A_later_lamp_blocks_an_earlier_one_away_from_a_post_and_lamps_from_before_need_the_post()
    {
        if (!HasData) return;
        Lamps.UseV2(true);
        try
        {
            var ch = Make("warden");
            ch.Level = 80;
            var w = Day;
            var old = LampBook.Suggest(ch, w)!;
            LampBook.Light(ch, w, old);
            var visit = new LampSession(ch);
            // a chain: a, then b hanging on a
            var a = LampBook.Now(ch).Lit.SelectMany(Lamps.Next).Distinct().First(id => LampBook.CanLight(ch, w, id) == LampNo.None);
            Assert.True(visit.Light(w, a));
            var b = Lamps.Next(a).First(id => LampBook.CanLight(ch, w, id) == LampNo.None);
            Assert.True(visit.Light(w, b));
            if (LampSession.Branch(ch, a)!.Count > 1) Assert.Equal(OutNo.Holds, visit.CanOut(a, false, false, out _));
            Assert.Equal(OutNo.None, visit.CanOut(b, false, false, out var ob));
            Assert.Equal(new[] { b }, ob);
            if (LampBook.CanUnlight(ch, old) == LampNo.None) Assert.Equal(OutNo.Place, visit.CanOut(old, false, false, out _));
            Assert.Equal(OutNo.Night, visit.CanOut(b, true, true, out _));
            Assert.Equal(OutNo.Free, visit.CanOut(Lamps.Start("warden"), false, true, out _));
        }
        finally { Lamps.UseV2(false); }
    }

    [Fact]
    public void At_a_post_a_lamp_others_hang_on_takes_its_branch_from_the_tips()
    {
        if (!HasData) return;
        Lamps.UseV2(true);
        try
        {
            var ch = Make("warden");
            ch.Level = 80;
            var w = Day;
            for (int k = 0; k < 20 && LampBook.Suggest(ch, w) is { } s; k++) LampBook.Light(ch, w, s);
            var lit = LampBook.Now(ch).Lit.ToList();
            var free = LampBook.Free(ch);
            // the lit lamp with the biggest branch
            var (root, br) = lit.Where(id => !free.Contains(id)).Select(id => (id, LampSession.Branch(ch, id))).Where(q => q.Item2 != null)
                .OrderByDescending(q => q.Item2!.Count).First();
            Assert.True(br!.Count > 1, "some lamp holds others");
            Assert.Equal(lit, LampBook.Now(ch).Lit);         // asking changed nothing
            var visit = new LampSession(ch);
            Assert.Equal(OutNo.None, visit.CanOut(root, false, true, out var order));
            Assert.Equal(root, order[^1]);
            Assert.True(visit.PutOut(order));
            var now = LampBook.Now(ch).Lit;
            Assert.DoesNotContain(now, order.Contains);
            Assert.Equal(lit.Count - order.Count, now.Count);
            // what stays still hangs together: every lamp left could go out on its own or holds others, none is stranded
            Assert.All(now.Where(id => !free.Contains(id)), id => Assert.NotEqual(LampNo.Unlit, LampBook.CanUnlight(ch, id)));
        }
        finally { Lamps.UseV2(false); }
    }

    [Fact]
    public void A_far_lamps_path_is_lit_all_or_nothing()
    {
        if (!HasData) return;
        Lamps.UseV2(true);
        try
        {
            var ch = Make("warden");
            ch.Level = 3;
            var w = Day;
            var lit = LampBook.Now(ch).Lit;
            var spare = LampBook.Spare(ch, w);
            // a lamp more than her points away
            var far = Lamps.All.Keys.OrderBy(id => id, StringComparer.Ordinal).First(id => LampAsk.PathTo(ch, w, id).Count > spare);
            var keep = lit.ToList();
            var flare = LampBook.Now(ch).Flare;
            Assert.False(LampAsk.LightPath(ch, w, far));
            Assert.Equal(keep, LampBook.Now(ch).Lit);
            Assert.Equal(flare, LampBook.Now(ch).Flare);
            // with the points, exactly its path, in order
            ch.Level = 80;
            var p = LampAsk.PathTo(ch, w, far);
            Assert.NotEmpty(p);
            Assert.True(LampAsk.LightPath(ch, w, far));
            Assert.Equal(keep.Concat(p), LampBook.Now(ch).Lit);
            // every lamp on any path can be lit in order (gates honored as the path climbs)
            var ch2 = Make("warden");
            ch2.Level = 80;
            int tried = 0;
            foreach (var id in Lamps.All.Keys.OrderBy(id => id, StringComparer.Ordinal).Where((_, i) => i % 7 == 0))
            {
                var pp = LampAsk.PathTo(ch2, w, id);
                if (pp.Count == 0 || pp.Count > LampBook.Spare(ch2, w)) continue;
                var k2 = LampBook.Now(ch2).Lit.ToList();
                Assert.True(LampAsk.LightPath(ch2, w, id), id);
                var l2 = LampBook.Now(ch2).Lit;
                l2.Clear(); l2.AddRange(k2);
                tried++;
            }
            Assert.True(tried > 10);
        }
        finally { Lamps.UseV2(false); }
    }

    /// <summary>Phase 1's label test, at scales between the stops, each zoomed about a point off the center (the wheel
    /// about the cursor, the triggers about the focus).</summary>
    [Fact]
    public void Labels_sit_clear_at_every_zoom_about_a_point()
    {
        if (!HasData) return;
        var m = M;
        double vs = m.ValleyScale(Window, 48);
        static double Width(string t, int px) => t.Length * px * 0.78 + (t.Length - 1) * Math.Round(px * 0.16);
        int views = 0, labels = 0;
        foreach (var start in m.Nodes.Where(nd => nd.Kind == "start"))
        {
            var v0 = new BoardView(start.X, start.Y, LampBoardModel.RoadScale, Window.W / 2, Window.H / 2);
            foreach (var (px, py) in new[] { (200.0, 180.0), (640.0, 460.0), (423.0, 321.0) })
                for (double s = vs; s <= LampBoardModel.LampScale * 1.0001; s *= 1.18)
                {
                    // zoom about (px, py): the board point under it stays under it
                    var (bx, by) = v0.Unproject(px, py);
                    var v = new BoardView(bx - (px - v0.Sx) / s, by - (v0.Sy - py) / s, s, v0.Sx, v0.Sy);
                    var (qx, qy) = v.Project(bx, by);
                    Assert.True(Math.Abs(qx - px) < 1e-6 && Math.Abs(qy - py) < 1e-6);
                    var stop = LampBoardModel.StopOf(v.S, vs);
                    var discs = new List<(double X, double Y, double R)>();
                    var lampOf = new List<int>();
                    foreach (var nd in m.Nodes)
                    {
                        var (x, y) = v.Project(nd.X, nd.Y);
                        if (x > -60 && x < Window.W + 60 && y > -60 && y < Window.H + 60)
                        { discs.Add((x, y, LampBoardModel.Diameter(nd.Kind, v.S, vs) / 2 + 5)); lampOf.Add(nd.I); }
                    }
                    var allowed = new Box(40, 40, Window.W - 40, Window.H - 40);
                    var placed = m.PlaceLabels(v, stop, discs, allowed, [], Width, new HashSet<int> { start.I }, lampOf);
                    views++;
                    labels += placed.Count;
                    for (int a = 0; a < placed.Count; a++)
                    {
                        var b = placed[a].Box;
                        Assert.True(b.Inside(allowed), placed[a].Text);
                        Assert.DoesNotContain(discs, d => b.Hits(d.X, d.Y, d.R));
                        for (int c = a + 1; c < placed.Count; c++) Assert.False(b.Overlaps(placed[c].Box), $"{s:F3}: {placed[a].Text} / {placed[c].Text}");
                    }
                }
        }
        log.WriteLine($"{views} views, {labels} labels, none crossing");
    }
}
