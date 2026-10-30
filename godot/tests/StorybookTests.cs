using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SurvivorUnchained.Cinema;
using SurvivorUnchained.Core;
using SurvivorUnchained.Storybook;
using Xunit;
using static SurvivorUnchained.Tests.H;

namespace SurvivorUnchained.Tests;

/// <summary>The storybook player's rules (docs/storybook/README.md): the files read,
/// the 2.5D lens, the camera's smooth keys, which plates are drawn and how far a
/// transition has got, the cues in order, the skip, and C01 after SB00.</summary>
public class StorybookTests
{
    static IEnumerable<StoryFile> All() =>
        Directory.GetFiles(Path.Combine(DataFiles.Dir, "storybook"), "*.json").Select(f => StoryFile.Parse(File.ReadAllText(f)));

    [Fact]
    public void Sb00_is_not_live_while_its_plates_are_placeholders()
    {
        Assert.False(StoryFile.Load("sb00").Live);
    }

    [Fact]
    public void A_storybook_that_says_nothing_about_live_is_live()
    {
        var f = StoryFile.Parse("""{ "id": "x", "conversation": "c" }""");
        Assert.True(f.Live);
    }

    [Fact]
    public void Every_storybook_reads_and_holds_together()
    {
        var files = All().ToList();
        Assert.Contains(files, f => f.Id == "sb00");
        Assert.Contains(files, f => f.Id == "test_plates");
        foreach (var f in files)
        {
            Assert.Empty(f.Problems());
            var ctx = Make("hunter", "Wren", 1).C;
            // Every line it says is in the dialogue (its own conversation, or a full id).
            foreach (var c in new StoryTimeline(f).Cues.Where(c => c.Cue.Do == "line"))
            {
                var id = c.Cue.Str("id")!;
                var l = CineLines.Find(id.Contains('.') ? id : $"{f.Conversation}.{id}", ctx);
                Assert.NotEqual("", l.Raw);
            }
        }
    }

    [Fact]
    public void Sb00_is_the_doc_s_timeline()
    {
        var f = StoryFile.Load("sb00");
        Assert.Equal("sb_stay_where_they_reach", f.Conversation);
        var want = new (string Id, double At, double Until)[]
        {
            ("ink_p0", 0, 2.5), ("ink_p1d", 2.5, 15.5), ("ink_p2", 15.5, 25.5), ("ink_p3", 25.5, 38), ("ink_p3d", 38, 46),
            ("ink_p4", 46, 56), ("ink_p5", 56, 71), ("ink_p6", 71, 81.5), ("ink_p7", 81.5, 87.5), ("ink_p7u", 87, 89.5),
        };
        Assert.Equal(want.Select(w => w.Id), f.Plates.Select(p => p.Id));
        foreach (var (p, w) in f.Plates.Zip(want)) { Assert.Equal(w.At, p.At); Assert.Equal(w.Until, p.Until); }
        Assert.Equal(89.5, f.End);
        // The nine lines in plate order, the first tagged; the song in P10 in italics under its tag.
        var tl = new StoryTimeline(f);
        var lines = tl.Cues.Where(c => c.Cue.Do == "line").ToList();
        Assert.Equal(new[] { "legion", "chained", "ember", "dead", "dawn", "keepers", "winter", "waiting", "lamps", "cin_none_cross.call" },
            lines.Select(c => c.Cue.Str("id")));
        Assert.Equal("An old Watchman", lines[0].Cue.Str("tag"));
        Assert.All(lines.Skip(1).Take(8), c => Assert.Null(c.Cue.Str("tag")));
        Assert.Equal("A voice under the water", lines[^1].Cue.Str("tag"));
        Assert.True(lines[^1].T >= 78);
        var ctx = Make("hunter", "Wren", 1).C;
        Assert.True(CineLines.Find("cin_none_cross.call", ctx).Sung);
        // Each of the nine is said while its plate is up (the ink plates carry the old cards' lines at their times:
        // legion and chained in the cut, dawn under the dead, winter and waiting in the ford, lamps by the fire).
        var host = new[] { "ink_p1d", "ink_p1d", "ink_p2", "ink_p3", "ink_p3", "ink_p4", "ink_p5", "ink_p5", "ink_p6" };
        for (int i = 0; i < 9; i++)
        {
            var p = f.Plates.Single(q => q.Id == host[i]);
            Assert.InRange(lines[i].T, p.At, p.Until);
        }
        // It starts in silence and ends in it, the last sound gone down the well before the end.
        Assert.Contains(tl.Cues, c => c.T == 0 && c.Cue.Do == "music" && c.Cue.Str("mood") == "silence");
        var well = tl.Cues.Last(c => c.Cue.Do == "bus");
        Assert.True(well.T + well.Cue.Num("over") <= f.End + 1e-9);
        Assert.True(well.Cue.Num("gain") <= -40);
    }

    [Fact]
    public void Sb00_s_lines_are_the_doc_s_words_in_the_watchman_s_voice()
    {
        var ctx = Make("hunter", "Wren", 1).C;
        var l = CineLines.Find("sb_stay_where_they_reach.lamps", ctx);
        Assert.Equal("Lamps are lit. Stay where they reach.", l.Text);
        Assert.Equal("watchman", l.SpeakerId);
        Assert.False(l.Sung);
        Assert.Equal("Long ago, the Seventh Legion found something under these hills that wouldn't die,",
            CineLines.Find("sb_stay_where_they_reach.legion", ctx).Text);
    }

    /* ---------------------------------------------------------- the lens -- */

    const double CW = 3200, CH = 1800, SW = 1920, SH = 1080;

    [Fact]
    public void At_rest_every_layer_sits_where_it_was_painted()
    {
        var rest = new StoryView(CW / 2, CH / 2, 1, 0, 0);
        foreach (var z in new[] { 0.5, 1, 3, 12 })
        {
            var (x, y) = StoryLens.Project(rest, z, 800, 300, CW, CH, SW, SH);
            Assert.Equal(800 * SW / CW, x, 6);
            Assert.Equal(300 * SW / CW, y, 6);
        }
    }

    [Fact]
    public void A_pan_moves_each_layer_by_the_pan_over_its_depth()
    {
        var rest = new StoryView(CW / 2, CH / 2, 1, 0, 0);
        var pan = rest with { X = CW / 2 + 400 };
        double s0 = SW / CW;
        foreach (var z in new[] { 0.6, 1, 2.5, 12 })
        {
            var (x0, _) = StoryLens.Project(rest, z, 1000, 900, CW, CH, SW, SH);
            var (x1, _) = StoryLens.Project(pan, z, 1000, 900, CW, CH, SW, SH);
            Assert.Equal(-400 / z * s0, x1 - x0, 6);
        }
        // The reference plane follows the camera exactly: the point under the centre is X.
        var (cx, cy) = StoryLens.Project(pan, 1, pan.X, pan.Y, CW, CH, SW, SH);
        Assert.Equal(SW / 2, cx, 6);
        Assert.Equal(SH / 2, cy, 6);
    }

    [Fact]
    public void A_dolly_grows_near_layers_faster_than_far_and_zoom_grows_all_alike()
    {
        var rest = new StoryView(CW / 2, CH / 2, 1, 0, 0);
        double s0 = SW / CW;
        var push = rest with { Dolly = 0.3 };
        foreach (var z in new[] { 0.6, 1, 5 })
            Assert.Equal(s0 * z / (z - 0.3), StoryLens.Layer(push, z, CW, CH, SW, SH).Scale, 9);
        Assert.True(StoryLens.Layer(push, 0.6, CW, CH, SW, SH).Scale > StoryLens.Layer(push, 5, CW, CH, SW, SH).Scale);
        var zoom = rest with { Zoom = 1.25 };
        foreach (var z in new[] { 0.6, 1, 5 })
            Assert.Equal(s0 * 1.25, StoryLens.Layer(zoom, z, CW, CH, SW, SH).Scale, 9);
        // A zoom keeps the centre where it is; a plane the dolly passes is held just ahead of the lens.
        var (cx, cy) = StoryLens.Project(zoom, 3, CW / 2, CH / 2, CW, CH, SW, SH);
        Assert.Equal(SW / 2, cx, 6); Assert.Equal(SH / 2, cy, 6);
        Assert.True(double.IsFinite(StoryLens.Layer(rest with { Dolly = 2 }, 0.6, CW, CH, SW, SH).Scale));
    }

    [Fact]
    public void A_roll_turns_about_the_screen_s_centre()
    {
        var cam = new StoryView(1000, 700, 1.1, 0.1, 5);
        var (cx, cy) = StoryLens.Project(cam, 1, 1000, 700, CW, CH, SW, SH);
        Assert.Equal(SW / 2, cx, 6); Assert.Equal(SH / 2, cy, 6);
        var (sc, _, _, rot) = StoryLens.Layer(cam, 1, CW, CH, SW, SH);
        Assert.Equal(5 * Math.PI / 180, rot, 9);
        var (ax, ay) = StoryLens.Project(cam, 1, 1100, 700, CW, CH, SW, SH);
        Assert.Equal(sc * 100 * Math.Cos(rot), ax - cx, 6);
        Assert.Equal(sc * 100 * Math.Sin(rot), ay - cy, 6);
    }

    /* ------------------------------------------------------- the camera -- */

    static StoryCurve Curve(double[] t, double[] v, string?[] e) => new(t, v, e);

    static double Speed(StoryCurve c, double t, double h = 1e-4) => (c.At(t + h) - c.At(t - h)) / (2 * h);

    [Fact]
    public void Keys_start_and_end_at_rest_and_keep_their_speed_through_the_middle()
    {
        var c = Curve([0, 4, 10], [0, 100, 400], [null, null, null]);
        Assert.Equal(0, c.At(0)); Assert.Equal(100, c.At(4), 9); Assert.Equal(400, c.At(10));
        Assert.Equal(0, Speed(c, 1e-3), 0);
        Assert.Equal(0, Speed(c, 10 - 1e-3), 0);
        // The same speed either side of the middle key, and moving.
        double before = (c.At(4) - c.At(4 - 1e-4)) / 1e-4, after = (c.At(4 + 1e-4) - c.At(4)) / 1e-4;
        Assert.Equal(before, after, 1);
        Assert.True(before > 10);
        // No jitter: monotone, and smooth step to step.
        double last = -1;
        for (double t = 0; t <= 10; t += 0.01) { var v = c.At(t); Assert.True(v >= last - 1e-9); last = v; }
    }

    [Fact]
    public void A_peak_is_never_overshot_and_eases_change_the_ends()
    {
        var c = Curve([0, 3, 6], [0, 100, 20], [null, null, null]);
        for (double t = 0; t <= 6; t += 0.01) Assert.InRange(c.At(t), 0 - 1e-9, 100 + 1e-9);
        // inout on the middle key: it comes to rest there.
        var stop = Curve([0, 3, 6], [0, 100, 300], [null, "inout", null]);
        Assert.Equal(0, Speed(stop, 3 - 1e-3), 0);
        // linear: constant speed between two keys.
        var lin = Curve([0, 2], [0, 10], [null, "linear"]);
        Assert.Equal(5, Speed(lin, 0.3), 6); Assert.Equal(5, Speed(lin, 1.7), 6);
        // in: from rest, not slowed at the end.
        var ein = Curve([0, 2], [0, 10], [null, "in"]);
        Assert.Equal(0, Speed(ein, 1e-3), 0);
        Assert.True(Speed(ein, 2 - 1e-3) > 4);
    }

    [Fact]
    public void A_hold_keeps_the_value_then_jumps()
    {
        var c = Curve([0, 2, 4], [1, 1.5, 1], [null, "hold", null]);
        Assert.Equal(1, c.At(1.999), 9);
        Assert.Equal(1.5, c.At(2.0), 9);
        // After the cut the next move starts from rest.
        Assert.Equal(0, Speed(c, 2 + 1e-3), 1);
    }

    [Fact]
    public void Camera_keys_carry_unset_values_and_zoom_moves_evenly()
    {
        var cam = StoryMotion.Camera([
            new StoryCamKey { T = 0, X = 1000, Zoom = 1 },
            new StoryCamKey { T = 4, Zoom = 2, Ease = "linear" },
        ], CW, CH);
        Assert.Equal(1000, cam(2).X, 9);
        Assert.Equal(CH / 2, cam(2).Y, 9);
        // In log space: half way in time is the geometric middle.
        Assert.Equal(Math.Sqrt(2), cam(2).Zoom, 6);
    }

    [Fact]
    public void Layer_keys_start_from_rest_when_the_first_is_late_and_frames_crossfade_without_a_dip()
    {
        var pose = StoryMotion.Layer([new StoryLayerKey { T = 5, Dx = 100, Opacity = 0.5 }], 1);
        Assert.Equal(0, pose(0).Dx); Assert.Equal(1, pose(0).Opacity);
        Assert.Equal(100, pose(5).Dx, 9); Assert.Equal(0.5, pose(9).Opacity, 9);
        var frames = new List<StoryFrame> { new() { T = 0, Image = "a" }, new() { T = 2, Image = "b", Fade = 1 } };
        Assert.Equal(new[] { 1.0, 0 }, StoryMotion.Frames(frames, 1));
        var mid = StoryMotion.Frames(frames, 2.5);
        Assert.Equal(1, mid[0], 9); Assert.Equal(1, mid[1], 9);
        Assert.Equal(new[] { 0.0, 1 }, StoryMotion.Frames(frames, 3.1));
    }

    /* ----------------------------------------------------- the timeline -- */

    static StoryFile Three() => StoryFile.Parse("""
        { "id": "t", "plates": [
            { "id": "a", "at": 0, "until": 5, "in": {"kind": "ink", "dur": 1} },
            { "id": "b", "at": 5, "until": 9, "in": {"kind": "dissolve", "dur": 2}, "out": {"kind": "fade", "dur": 1} },
            { "id": "c", "at": 9, "until": 12, "in": {"kind": "cut"} } ],
          "end": 14 }
        """);

    [Fact]
    public void A_plate_is_drawn_until_the_next_one_s_transition_ends()
    {
        var tl = new StoryTimeline(Three());
        Assert.Equal(7, tl.Spans[0].DrawEnd);
        Assert.Equal(9, tl.Spans[1].DrawEnd);
        Assert.Equal(12, tl.Spans[2].DrawEnd);
        // The first comes in over black.
        var m0 = tl.Mix(0.5);
        Assert.Null(m0.Under); Assert.Equal("a", m0.Over!.Plate.Id); Assert.Equal(0.5, m0.K, 9);
        Assert.Equal("a", tl.Mix(3).Under!.Plate.Id); Assert.Null(tl.Mix(3).Over);
        var m = tl.Mix(6);
        Assert.Equal("a", m.Under!.Plate.Id); Assert.Equal("b", m.Over!.Plate.Id); Assert.Equal(0.5, m.K, 9);
        Assert.Equal(new[] { "a", "b" }, tl.Drawn(6.9).Select(s => s.Plate.Id));
        Assert.Equal(new[] { "b" }, tl.Drawn(7).Select(s => s.Plate.Id));
        // A cut: the next is up at once, alone.
        Assert.Equal("c", tl.Mix(9).Under!.Plate.Id);
        Assert.Null(tl.Mix(9).Over);
        // Black after the last plate, to the end.
        Assert.Null(tl.Mix(13).Under);
        // B's own fade out over its last second.
        Assert.Equal(0, StoryTimeline.OutFade(tl.Spans[1], 7.9), 9);
        Assert.Equal(0.5, StoryTimeline.OutFade(tl.Spans[1], 8.5), 9);
    }

    [Fact]
    public void Cues_go_in_time_order_the_file_s_own_first_at_the_same_moment()
    {
        var f = StoryFile.Parse("""
            { "id": "t", "plates": [
                { "id": "a", "at": 0, "until": 5, "cues": [ {"at": 1, "do": "sfx", "name": "x"}, {"at": 0, "do": "sfx", "name": "y"} ] },
                { "id": "b", "at": 4, "until": 8, "cues": [ {"at": 0, "do": "sfx", "name": "z"} ] } ],
              "cues": [ {"at": 4, "do": "music", "mood": "night"}, {"at": 0, "do": "music", "mood": "silence"} ],
              "end": 8 }
            """);
        var tl = new StoryTimeline(f);
        Assert.Equal(new[] { 0.0, 0, 1, 4, 4 }, tl.Cues.Select(c => c.T));
        Assert.Equal(new[] { "music", "sfx", "sfx", "music", "sfx" }, tl.Cues.Select(c => c.Cue.Do));
        Assert.Equal("z", tl.Cues[^1].Cue.Str("name"));
        // A frame sets off what falls in it, once: from just below 0 the cues at 0 go first.
        Assert.Equal(2, tl.Between(-1e-6, 0).Count());
        Assert.Equal(3, tl.Between(0.5, 4).Count());
        Assert.Empty(tl.Between(4, 7));
    }

    [Fact]
    public void Skip_waits_1_5_s_on_a_first_view_and_not_once_seen()
    {
        var s = new StorySkip();
        Assert.False(StoryTimeline.CanSkip(1.4, false, s));
        Assert.True(StoryTimeline.CanSkip(1.5, false, s));
        Assert.True(StoryTimeline.CanSkip(0, true, s));
        Assert.Equal(1.5, StoryFile.Load("sb00").Skip.From);
    }

    /* --------------------------------------------------- C01 after SB00 -- */

    [Fact]
    public void After_sb00_c01_drops_its_drowning()
    {
        var f = CineFile.Load("c01");
        CineSchedule Lay(bool ended)
        {
            var ctx = new CineContext();
            if (ended) ctx.Facts.Add("sb00.ended");
            return new CineSchedule(f, ctx, _ => 3.0);
        }
        var asWritten = Lay(false);
        var after = Lay(true);
        // 29 Oct: C01 opens on black with the bedroll line at 1.2 s; the shot is the same length either way
        // (the line's take sets it), and only the water is left out after SB00.
        Assert.Equal(1.2 + 3.0 + 0.3, asWritten.Shots[0].Dur, 6);
        Assert.Equal(asWritten.Shots[0].Dur, after.Shots[0].Dur, 6);
        bool Water(CineSchedule s) => s.Cues.Any(c => c.Cue.Do == "sfx" && c.Cue.Str("name") == "water_close");
        Assert.True(Water(asWritten));
        Assert.False(Water(after));
        // The drops and the owl keep their places from the shot's end.
        var end = after.Shots[0].Dur;
        var drops = after.Cues.Where(c => c.Shot.Index == 0 && c.Cue.Do == "sfx").Select(c => Math.Round(c.T, 6));
        Assert.Equal(new[] { end - 1.3, end - 0.55, end - 0.4 }.Select(d => Math.Round(d, 6)), drops);
        Assert.Equal(asWritten.Length, after.Length, 9);
    }

    static StoryTimeline Blacks() => new(StoryFile.Parse("""
        { "id": "x", "conversation": "c", "end": 20,
          "plates": [
            { "id": "a", "at": 0, "until": 5, "in": { "kind": "fade", "dur": 1 } },
            { "id": "b", "at": 4, "until": 9, "in": { "kind": "dissolve", "dur": 1 }, "out": { "kind": "fade", "dur": 1 } },
            { "id": "c", "at": 9, "until": 12, "in": { "kind": "cut" }, "out": { "kind": "fade", "dur": 2, "color": "#ffffff" } },
            { "id": "d", "at": 14, "until": 18, "out": { "kind": "fade", "dur": 2 } }
          ] }
        """));

    [Fact]
    public void The_screen_goes_black_at_gaps_fades_out_to_black_and_the_end()
    {
        var l = Blacks();
        // b fades to black at 9 with nothing over it (c cuts in on the black).
        Assert.Equal(9, l.BlackAfter(2), 9);
        // c fades to white: not black; the gap from 12 is.
        Assert.Equal(12, l.BlackAfter(9), 9);
        Assert.Equal(18, l.BlackAfter(12), 9);
        Assert.Equal(20, l.BlackAfter(18), 9);
        Assert.True(double.IsPositiveInfinity(l.BlackAfter(20)));
    }

    [Fact]
    public void A_subtitle_is_gone_by_the_black()
    {
        var l = Blacks();
        Assert.Equal(3, l.SubtitleFor(1, 3), 9);
        Assert.Equal(1.5, l.SubtitleFor(7.5, 4), 9);
        Assert.Equal(2, l.SubtitleFor(16, 6), 9);
        // Set in a black gap, it reads over the black until the next black (the end here).
        Assert.Equal(4, l.SubtitleFor(13, 4), 9);
    }

    [Fact]
    public void A_subtitle_fades_with_the_picture_into_a_fade_to_black()
    {
        var l = Blacks();
        // b fades to black over 8-9: a line up until 9 goes down from 8 with it.
        Assert.Equal(1.0, l.SubtitleFade(7, 4), 9);
        Assert.Equal(1.0, l.SubtitleFade(7.5, 4), 9);
        Assert.Equal(0.5, l.SubtitleFade(8.5, 4), 9);
        // One that ends before the fade starts: the quarter second.
        Assert.Equal(0.25, l.SubtitleFade(1, 3), 9);
        // Into the end black (no fade of its own): the quarter second.
        Assert.Equal(0.25, l.SubtitleFade(18.5, 10), 9);
        // d fades to black over 16-18: ending inside it at 17 still goes down from 16.
        Assert.Equal(1.0, l.SubtitleFade(15, 2), 9);
    }

    [Fact]
    public void Sb00_s_sung_line_fades_with_its_last_plate()
    {
        var f = StoryFile.Load("sb00");
        var l = new StoryTimeline(f);
        var last = f.Plates[^1];
        double dur = last.Out!.Dur;
        foreach (var c in l.Cues.Where(c => c.Cue.Do is "line" or "say"))
        {
            double shown = l.SubtitleFor(c.T, 30);
            if (c.T + shown > last.Until - dur + 1e-6)
                Assert.True(l.SubtitleFade(c.T, 30) >= c.T + shown - Math.Max(c.T, last.Until - dur) - 1e-9);
        }
    }

    static double Chars(string s) => s.Length * 10.0;

    [Fact]
    public void A_long_subtitle_breaks_at_a_sentence_end_never_one_word_alone()
    {
        var t = "Now the drowned stand along the ford road, waiting. And something in the water is singing.";
        Assert.Equal("Now the drowned stand along the ford road, waiting.\nAnd something in the water is singing.",
            CineLines.Break(t, Chars, 600));
        // It fits: as it is; the script's '/' wins.
        Assert.Equal("Short line.", CineLines.Break("Short line.", Chars, 600));
        Assert.Equal("One two / three four five six", CineLines.Break("One two / three four five six", Chars, 100));
        // No sentence end: the most balanced word break.
        Assert.Equal("aaaa bbbb cccc\ndddd eeee ffff", CineLines.Break("aaaa bbbb cccc dddd eeee ffff", Chars, 200));
        // A sentence end that would leave a short line loses to balance.
        Assert.Equal("Yes. Then the\nlong road home", CineLines.Break("Yes. Then the long road home", Chars, 160));
        foreach (var line in new[] { t, "a b c d e f g h i j k l m n o p q r s t u v w x y z" })
        {
            var parts = CineLines.Break(line, Chars, 300).Split('\n');
            Assert.All(parts, p => Assert.Contains(' ', p));
        }
    }

    [Fact]
    public void Sb00_s_last_lines_are_gone_before_its_end_black()
    {
        var f = StoryFile.Load("sb00");
        var l = new StoryTimeline(f);
        var last = f.Plates[^1];
        foreach (var c in l.Cues.Where(c => c.Cue.Do is "line" or "say"))
            Assert.True(c.T + l.SubtitleFor(c.T, 30) <= last.Until + 1e-9, $"line at {c.T} runs past {last.Until}");
    }

    [Fact]
    public void The_scripted_skip_is_due_from_its_moment()
    {
        Assert.False(StoryTimeline.SkipDue(100, null));
        Assert.False(StoryTimeline.SkipDue(4.99, 5));
        Assert.True(StoryTimeline.SkipDue(5, 5));
        Assert.True(StoryTimeline.SkipDue(5.02, 5));
    }

    [Fact]
    public void The_seam_cut_takes_the_load_from_a_timed_black_down_to_its_drops()
    {
        // A black shot with a length for after the storybook (a "durs" with a when): it loses the load, down to keep.
        CineShot Shot() => new() { Dur = 3.5, Durs = new() { new CineDur { When = new CineWhen { Facts = new() { "sb00.ended" } }, Dur = 2.5 } } };
        var shot = Shot();
        Assert.Equal(1.0, StoryTimeline.CutSeam(shot, 1.0, 1.3), 9);
        Assert.Equal(1.5, shot.Durs![0].Dur, 9);
        shot = Shot();
        Assert.Equal(1.2, StoryTimeline.CutSeam(shot, 2.5, 1.3), 9);
        Assert.Equal(1.3, shot.Durs![0].Dur, 9);
        Assert.Equal(3.5, shot.Dur, 9);   // as written, untouched
    }

    [Fact]
    public void C01_s_opening_black_is_not_cut_by_the_load()
    {
        // 29 Oct (Cinematics 10 C01 final cut): C01 opens on black with the bedroll line at 1.2 s, the same length
        // with or without SB00 (no "durs"), so the seam has no silence to lose; the load is not cut from it.
        var shot = CineFile.Load("c01").Shots[0];
        double was = shot.Dur;
        Assert.Equal(0.0, StoryTimeline.CutSeam(shot, 2.5, 1.3), 9);
        Assert.Equal(was, shot.Dur, 9);
    }
}
