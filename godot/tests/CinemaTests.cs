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
        foreach (var f in All().Where(f => f.Conversation.StartsWith("cin_")))
        {
            var said = Lay(f).Cues.Where(c => c.Cue.Do == "line").Select(c => c.Cue.Str("id")!).ToList();
            var convo = Dialogue.Find(f.Conversation)!;
            var order = new List<string>();
            for (var n = convo.Entry[0].Node; n != null; n = convo.Nodes[n].Next) order.Add($"{f.Conversation}.{n}");
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
    public void The_opening_is_narration_whoever_voices_it()
    {
        // C01's voice may be recast (Vonnra calling her home): the timing follows
        // the take, and the subtitle stays narration while the speaker is listed.
        var f = CineFile.Load("c01");
        var ctx = Make("hunter", "Wren", 1).C;
        foreach (var c in Lay(f).Cues.Where(c => c.Cue.Do == "line"))
            Assert.Contains(CineLines.Find(c.Cue.Str("id")!, ctx).SpeakerId, f.Narrators);
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
