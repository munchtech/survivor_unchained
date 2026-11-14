using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using SurvivorUnchained.Viewer;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The live look viewer's pure parts (docs/tools/LOOK_VIEWER.md): a request read into the game's switches
/// exactly as Marionette's game_frame.py builds them, the package fingerprint, the settled-change watch, the request
/// queue, the switch override (Args.Override) and what NpcPackage.Forget drops.</summary>
public class LookViewerTests
{
    [Fact]
    public void A_request_becomes_game_frames_switches_for_each_camera()
    {
        var s = LookSettings.Parse("{\"package\": \"C:/p/gf_x\", \"cams\": \"play,chest\", \"clock\": 120, \"off\": [\"ink\", \"glow\", \"key\"], \"turn\": 30}", "r1");
        Assert.Equal("r1", s.Id);
        var play = s.GameArgs("play", "gf_x", "C:\\p\\gf_x", s.Tag("play"));
        Assert.Equal(new[] { "--quick", "warden", "--sex", "female", "--nohud", "--zone", "waystation", "--facing", "0", "--seed", "1", "--time", "day",
            "--clock", "120", "--npc-overlay", "gf_x=C:/p/gf_x", "--ink", "off", "--idle-after", "1000000", "--seconds", "6",
            "--npc", "gf_x:turn30", "--npc-debug", "--shot", "gf_r1_play" }, play);
        var chest = s.GameArgs("chest", "gf_x", null, s.Tag("chest"));
        Assert.Contains("gf_x:swap:chest:turn30", chest);
        Assert.Equal("8", chest[chest.IndexOf("--seconds") + 1]);
        var (terms, pats, game) = s.OffTerms();
        Assert.Equal(new[] { "glow" }, terms);
        Assert.Equal(new[] { "atmosphere/key" }, pats);
        Assert.Equal(new[] { "--ink", "off" }, game);
    }

    [Fact]
    public void Walk_and_no_turn_flags_follow_game_frame()
    {
        var s = LookSettings.Parse("{\"walk\": true, \"turn\": 0}");
        Assert.Contains("n:walk", s.GameArgs("play", "n", null, "t"));
        Assert.Contains("n:walk:swap:chest", s.GameArgs("chest", "n", null, "t"));
        Assert.Equal("base", s.Id);
        Assert.Equal(new[] { "play", "chest" }, s.CamList);
    }

    [Theory]
    [InlineData("{\"cams\": [\"side\"]}", "no camera side")]
    [InlineData("{\"off\": [\"bloom\"]}", "no term bloom")]
    [InlineData("{\"time\": \"dusk\"}", "time dusk")]
    [InlineData("{\"spot\": \"shade\", \"zone\": \"lowford\"}", "ray search")]
    [InlineData("{\"spot\": \"left\"}", "spot left")]
    [InlineData("{\"size\": \"big\"}", "size WxH")]
    [InlineData("{\"id\": \"a b\"}", "id a b")]
    [InlineData("{\"colour\": 1}", "no setting colour")]
    [InlineData("[1]", "a JSON object")]
    [InlineData("{", "not JSON")]
    public void A_bad_request_is_refused_with_why(string json, string why)
    {
        var e = Assert.Throws<LookError>(() => LookSettings.Parse(json));
        Assert.Contains(why, e.Message);
    }

    [Fact]
    public void Shade_in_the_waystation_is_the_tables_offset()
    {
        var s = LookSettings.Parse("{\"spot\": \"shade\"}");
        Assert.Equal((-1.0, 6.0), s.SpotOffset());
        Assert.Equal("-1.0,6.0", s.SpotSent);
        Assert.Null(LookSettings.Parse("{}").SpotOffset());
        Assert.Equal((0.5, -2.0), LookSettings.Parse("{\"spot\": \"0.5,-2\"}").SpotOffset());
    }

    [Fact]
    public void A_package_is_named_as_game_frame_names_it()
    {
        Assert.Equal("gf_keeper", LookSettings.NameFor(null, "C:/x/_pkg/gf_keeper/", "other"));
        Assert.Equal("gf_keeper", LookSettings.NameFor(null, "C:/drop/live", "gf_keeper"));
        Assert.Equal("live", LookSettings.NameFor(null, "C:/drop/live", null));
        Assert.Equal("given", LookSettings.NameFor("given", "C:/drop/live", "gf_keeper"));
    }

    static Func<string, byte[]?> Files(Dictionary<string, string> f) => rel => f.TryGetValue(rel, out var v) ? Encoding.UTF8.GetBytes(v) : null;

    [Fact]
    public void The_fingerprint_covers_the_manifest_and_every_file_it_names()
    {
        var man = "{\"name\": \"n\", \"pieces\": [{\"id\": \"cap\"}, {\"id\": \"belt\", \"file\": \"armor/b2.glb\"}], \"hair\": {\"file\": \"hair/braid.glb\"}, \"lod\": {\"file\": \"lod.glb\"}}";
        Assert.Equal(new[] { "manifest.json", "body.glb", "armor/cap.glb", "armor/b2.glb", "hair/braid.glb", "lod.glb" }, PackageFingerprint.Files(man)!);
        var files = new Dictionary<string, string> { ["manifest.json"] = man, ["body.glb"] = "B", ["armor/cap.glb"] = "C", ["armor/b2.glb"] = "D", ["hair/braid.glb"] = "H", ["lod.glb"] = "L", ["other.txt"] = "x" };
        var a = PackageFingerprint.Compute(Files(files));
        Assert.Empty(a.Missing);
        Assert.Equal(6, a.Files.Count);
        files["other.txt"] = "y";
        Assert.Equal(a.Hash, PackageFingerprint.Compute(Files(files)).Hash);   // (a file it does not name is not its look)
        files["armor/b2.glb"] = "D2";
        Assert.NotEqual(a.Hash, PackageFingerprint.Compute(Files(files)).Hash);
        files.Remove("lod.glb");
        Assert.Equal(new[] { "lod.glb" }, PackageFingerprint.Compute(Files(files)).Missing);
        Assert.Throws<LookError>(() => PackageFingerprint.Compute(Files(new Dictionary<string, string>())));
        Assert.Null(PackageFingerprint.Files("[1]"));
    }

    [Fact]
    public void The_body_file_named_in_the_manifest_is_the_one_hashed()
    {
        Assert.Equal(new[] { "manifest.json", "b.glb" }, PackageFingerprint.Files("{\"body\": \"b.glb\"}")!);
    }

    sealed class FakeStats : IFileStats
    {
        public readonly Dictionary<string, (long Size, long Written)> Files = new();
        public IEnumerable<FileStat> List(string root) =>
            Files.Where(f => f.Key == root || f.Key.StartsWith(root + "/")).Select(f => new FileStat(f.Key, f.Value.Size, f.Value.Written));
    }

    [Fact]
    public void A_change_is_handed_on_only_once_it_has_stood_still()
    {
        var fs = new FakeStats();
        fs.Files["d/live/manifest.json"] = (10, 1);
        var w = new ChangeWatch(fs, new[] { "d/live", "d/live.json" }, 0.3);
        Assert.False(w.Poll(0.0));          // (first seen)
        Assert.False(w.Poll(0.2));
        Assert.True(w.Poll(0.35));          // settled: replay
        w.Taken();
        Assert.False(w.Poll(1.0));          // nothing new
        fs.Files["d/live/body.glb"] = (100, 5);   // a glb being written...
        Assert.False(w.Poll(1.1));
        fs.Files["d/live/body.glb"] = (200, 6);   // ...still growing
        Assert.False(w.Poll(1.3));
        Assert.False(w.Poll(1.5));
        Assert.True(w.Poll(1.65));          // 0.35 s still
        Assert.Equal(1.3, w.ChangedAt);
        w.Taken();
        fs.Files["d/live.json"] = (5, 9);   // the settings count too
        Assert.False(w.Poll(2.0));
        Assert.True(w.Poll(2.4));
        w.Taken();
        fs.Files["d/livexyz"] = (5, 9);     // (not under the roots)
        Assert.False(w.Poll(3.0));
        Assert.False(w.Poll(3.5));
        w.Again();
        Assert.True(w.Poll(3.6));           // F5: the same files replayed again
    }

    [Fact]
    public void Requests_wait_settled_and_answered_ones_are_skipped()
    {
        long T(double s) => (long)(s * TimeSpan.TicksPerSecond);
        var files = new[]
        {
            new FileStat("r/b.json", 1, T(1)), new FileStat("r/a.json", 1, T(2)), new FileStat("r/c.json", 1, T(9.9)),
            new FileStat("r/d.json", 1, T(0.5)), new FileStat("r/d.done.json", 1, T(3)),
            new FileStat("r/e.json", 1, T(0.6)), new FileStat("r/e.failed.json", 1, T(3)), new FileStat("r/f.json.tmp", 1, T(1)),
        };
        Assert.Equal(new[] { "b", "a" }, RequestQueue.Pending(files, T(10)));
        Assert.Equal(new[] { "b", "a", "c" }, RequestQueue.Pending(files, T(10.5)));
    }

    [Fact]
    public void Switches_read_as_the_game_reads_them_and_an_override_replaces_them()
    {
        var line = new[] { "--quick", "warden", "--nohud", "--zone", "waystation", "stray", "--clock", "-5", "--npc-debug" };
        int reads = 0;
        var t = new ArgTable(() => { reads++; return line; });
        Assert.Equal("warden", t.All()["quick"]);
        Assert.Equal("1", t.All()["nohud"]);
        Assert.Equal("-5", t.All()["clock"]);
        Assert.Equal("1", t.All()["npc-debug"]);
        Assert.False(t.All().ContainsKey("stray"));
        t.Override(new[] { "--zone", "lowford", "--shot", "x" });
        Assert.True(t.Overridden);
        Assert.Equal("lowford", t.All()["zone"]);
        Assert.False(t.All().ContainsKey("quick"));
        t.Override(null);
        Assert.Equal("waystation", t.All()["zone"]);
        Assert.Equal(1, reads);   // (the command line is read once)
    }

    [Fact]
    public void Forget_drops_only_that_packages_entries()
    {
        var scenes = new Dictionary<string, int> { ["res://art/npc/gf_a/body.glb"] = 1, ["res://art/npc/gf_a/armor/cap.glb"] = 2, ["res://art/npc/gf_ab/body.glb"] = 3, ["res://art/people/heroine.glb"] = 4 };
        Assert.Equal(2, PackageCache.Forget(scenes, f => PackageCache.OwnsFile("gf_a", f)));
        Assert.Equal(new[] { "res://art/npc/gf_ab/body.glb", "res://art/people/heroine.glb" }, scenes.Keys.OrderBy(k => k));
        var trimmed = new Dictionary<(string, ulong), int> { [("gf_a", 1)] = 1, [("gf_b", 1)] = 2 };
        Assert.Equal(1, PackageCache.Forget(trimmed, k => k.Item1 == "gf_a"));
        Assert.Single(trimmed);
    }
}
