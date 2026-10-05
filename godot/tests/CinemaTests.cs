using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Cinema;
using SurvivorUnchained.Core;
using SurvivorUnchained.World;
using Xunit;
using static SurvivorUnchained.Tests.H;

namespace SurvivorUnchained.Tests;

/// <summary>The cinematic timelines (godot/data/cinematics, docs/cinematics/shoot):
/// every one reads, knows each cue it gives, says only lines its conversation
/// holds, and plays the same however the frames fall; a skip lands on the end
/// with what lasts done and nothing heard.</summary>
public class CinemaTests
{
    static IEnumerable<CineFile> All() =>
        Directory.GetFiles(Path.Combine(DataFiles.Dir, "cinematics"), "*.json")
            .Where(f => !Path.GetFileName(f).StartsWith('_'))
            .Select(f => CineFile.Parse(File.ReadAllText(f)));

    static CineSchedule Lay(CineFile f, string calling = "warden") =>
        new(f, new CineContext { Calling = calling }, id => 3.0);

    [Fact]
    public void Every_timeline_reads_and_knows_its_cues_marks_and_lines()
    {
        var files = All().ToList();
        Assert.Contains(files, f => f.Id == "c01");
        foreach (var f in files)
        {
            Assert.NotEmpty(f.Shots);
            foreach (var s in f.Shots)
            {
                Assert.True(s.Dur > 0, $"{f.Id} shot {s.Id} has no length");
                foreach (var c in s.Cues)
                {
                    Assert.True(CineCue.Kinds.Contains(c.Do), $"{f.Id} shot {s.Id}: no cue '{c.Do}'");
                    if (c.Str("mark") is string m) f.Mark(m);
                    if (c.Do == "line")
                    {
                        var id = c.Str("id")!;
                        Assert.StartsWith(f.Conversation + ".", id);
                        var node = id[(f.Conversation.Length + 1)..];
                        Assert.True(Dialogue.Find(f.Conversation)!.Nodes.ContainsKey(node), $"{f.Id}: no line {id}");
                    }
                }
            }
            if (f.End.Her != null) f.Mark(f.End.Her);
        }
    }

    [Fact]
    public void A_cinematic_says_every_line_of_its_conversation_once_in_order()
    {
        // A cinematic in parts (C04's north bank and its Waystation) says its
        // conversation across them, the parts in order of their ids.
        foreach (var parts in All().Where(f => f.Conversation.StartsWith("cin_")).GroupBy(f => f.Conversation))
        {
            var said = parts.OrderBy(f => f.Id, StringComparer.Ordinal)
                .SelectMany(f => Lay(f).Cues.Where(c => c.Cue.Do == "line").Select(c => c.Cue.Str("id")!)).ToList();
            var convo = Dialogue.Find(parts.Key)!;
            var order = new List<string>();
            for (var n = convo.Entry[0].Node; n != null; n = convo.Nodes[n].Next) order.Add($"{parts.Key}.{n}");
            Assert.Equal(order, said);
        }
    }

    [Fact]
    public void A_longer_take_makes_a_longer_shot_and_moves_what_follows()
    {
        var f = CineFile.Load("c01");
        var shortTakes = new CineSchedule(f, new CineContext(), id => 2.0);
        var longTakes = new CineSchedule(f, new CineContext(), id => id.EndsWith(".prints") ? 11.0 : 2.0);
        var s7 = longTakes.Shots.First(s => s.Shot.Id == "7");
        var line = longTakes.Cues.First(c => c.Cue.Str("id") == "cin_drowned_fire.prints");
        Assert.Equal(line.T + 11.0 + s7.Shot.Tail, s7.End, 6);
        Assert.Equal(longTakes.Length - shortTakes.Length, s7.Dur - shortTakes.Shots.First(s => s.Shot.Id == "7").Dur, 6);
    }

    [Fact]
    public void The_clock_fires_every_cue_once_in_order_however_the_frames_fall()
    {
        var f = CineFile.Load("c01");
        List<(double, int)> Run(Func<int, double> dt)
        {
            var p = new CinePlayer(Lay(f));
            var o = p.Advance(0).Select(c => (c.T, c.Order)).ToList();
            for (int i = 0; !p.Done && i < 100000; i++) o.AddRange(p.Advance(dt(i)).Select(c => (c.T, c.Order)));
            return o;
        }
        var steady = Run(_ => 1.0 / 60);
        var ragged = Run(i => i % 7 == 0 ? 0.25 : i % 3 == 0 ? 0.001 : 1.0 / 30);
        Assert.Equal(steady, ragged);
        Assert.Equal(Lay(f).Cues.Count, steady.Count);
    }

    [Fact]
    public void The_camera_is_a_function_of_time_and_lands_in_the_game_camera()
    {
        var f = CineFile.Load("c01");
        var places = new CinePlaces(f, (x, z) => 0);
        var a = new CinePlayer(Lay(f));
        var b = new CinePlayer(Lay(f));
        a.Advance(20.0);
        for (int i = 0; i < 400; i++) b.Advance(0.05);
        Assert.Equal(a.Camera(places.Resolve), b.Camera(places.Resolve));
        var end = new CinePlayer(Lay(f));
        end.Advance(end.S.Length);
        Assert.Equal(1.0, end.Camera(places.Resolve).FollowK, 6);
        Assert.Equal(39.6, CineCamera.Hfov(50), 1);
        Assert.Equal(104.3, CineCamera.Hfov(14), 1);
    }

    [Fact]
    public void A_skip_lands_on_the_end_with_what_lasts_and_nothing_heard()
    {
        var f = CineFile.Load("c01");
        var p = new CinePlayer(Lay(f));
        p.Advance(0.5);
        Assert.False(p.CanSkip(false));
        Assert.True(p.CanSkip(true));
        p.Advance(1.2);
        Assert.True(p.CanSkip(false));
        var left = p.SkipToEnd();
        Assert.True(p.Done);
        Assert.All(left, c => Assert.True(c.Cue.Lasting));
        Assert.DoesNotContain(left, c => c.Cue.Do is "line" or "sfx" or "music");
        // The dead it raises are raised whether it is watched or not.
        Assert.Equal(4, left.Count(c => c.Cue.Do == "spawn"));
    }

    [Fact]
    public void The_opening_is_narration_whoever_voices_it_and_one_labelled_voice()
    {
        // The narrator may be recast (the timing follows the take; the subtitle stays
        // narration while the speaker is listed). The one other voice is the call up
        // the road, Vonnra's, never named but labelled "A voice up the road": the
        // narrator never speaks a person's words, and the label is how a careful
        // player later knows her (docs/STORY_BIBLE.md, "Who tells it").
        var f = CineFile.Load("c01");
        var ctx = Make("hunter", "Wren", 1).C;
        var lines = Lay(f).Cues.Where(c => c.Cue.Do == "line").Select(c => CineLines.Find(c.Cue.Str("id")!, ctx)).ToList();
        var call = Assert.Single(lines, l => l.SpeakerId == "far_voice");
        Assert.DoesNotContain("far_voice", f.Narrators);
        Assert.Equal("A voice up the road", call.Speaker);
        Assert.All(lines.Where(l => l != call), l => Assert.Contains(l.SpeakerId, f.Narrators));
    }

    [Fact]
    public void A_subtitle_drops_how_a_line_is_said_but_keeps_what_is_shown()
    {
        // A lower-case parenthesis is a direction for the voice (docs/VOICES.md):
        // the subtitle drops it, and "sung" sets the line in italics. A capitalised
        // one is words to show, as C13's translations of the Latin. The take is
        // still matched to the words as written.
        var ctx = Make("hunter", "Wren", 1).C;
        var call = CineLines.Find("cin_none_cross.call", ctx);
        Assert.Equal("Lamps are lit... stay where they reach...", call.Text);
        Assert.True(call.Sung);
        Assert.StartsWith("(sung, under the water)", call.Raw);
        var grateful = CineLines.Find("cin_heart_goes_down.grateful", ctx);
        Assert.Equal("Finders keepers, surface-m— ...Downstairs'll be ever so grateful.", grateful.Text);
        Assert.False(grateful.Sung);
        foreach (var node in new[] { "nondum", "redi" })
        {
            // The reader's variant: the Latin and its translation.
            var latin = Dialogue.Find("cin_behind_the_door")!.Nodes[node].Text[0].Text;
            Assert.Contains("(", latin);
            Assert.Equal((latin, false), CineLines.Subtitle(latin));
        }
        Assert.Equal(("...Ashford. There. Now we've both said it.", false), CineLines.Subtitle("...Ashford. (a laugh) There. Now we've both said it."));
        Assert.Equal(("Lie down, lie down.", true), CineLines.Subtitle("(sung) Lie down, lie down."));
    }

    [Fact]
    public void A_line_can_run_over_a_cut_and_a_cue_can_wait_for_it()
    {
        // The far lamp's line begins on the wide shot and ends on her close-up; the
        // call waits for it, and the close-up holds until the call is said.
        var f = CineFile.Parse("""
            { "id": "t", "conversation": "cin_drowned_fire", "shots": [
              { "id": "1", "dur": 2, "cues": [ { "at": 0.5, "do": "line", "id": "cin_drowned_fire.lamp" } ] },
              { "id": "2", "dur": 1, "fit": ["cin_drowned_fire.lamp", "cin_drowned_fire.call"], "tail": 0.5,
                "cues": [ { "at": "after:cin_drowned_fire.lamp+0.4", "do": "line", "id": "cin_drowned_fire.call" } ] } ] }
            """);
        var s = new CineSchedule(f, new CineContext(), id => id.EndsWith(".lamp") ? 6.0 : 3.0);
        Assert.Equal(2.0, s.Shots[1].Start, 6);
        Assert.Equal(6.9, s.Cues.First(c => c.Cue.Str("id") == "cin_drowned_fire.call").T, 6);
        Assert.Equal(6.9 + 3.0 + 0.5, s.Length, 6);
        var bad = CineFile.Parse("""{ "id": "u", "shots": [ { "id": "1", "dur": 1, "fit": ["x.y"], "cues": [] } ] }""");
        Assert.Throws<FormatException>(() => new CineSchedule(bad, new CineContext(), _ => 1));
    }

    [Fact]
    public void A_shot_for_one_calling_is_played_only_for_it()
    {
        var f = CineFile.Load("c01");
        bool Casts(string calling) => Lay(f, calling).Cues.Any(c => c.Cue.Do == "anim" && c.Cue.Str("clip") == "Spell_Simple_Enter");
        Assert.True(Casts("arcanist"));
        Assert.False(Casts("warden"));
    }
}
