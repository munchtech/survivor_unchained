using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Sound;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The den's sound rules (src/Audio/DenSound.cs, docs/team/den_sound_events.md): the sim says what a creature does
/// (Ev.Voice, Ev.Hit, Ev.Kill), the limiter keeps a pack from becoming noise, her grunts are chance plus cooldown,
/// the pits are found in the hole field, and every event the den uses is in the real bank.</summary>
public class DenSoundTests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    [Fact]
    public void EachCreatureHasItsKindAndAnUnknownOneHasNone()
    {
        Assert.Equal("wolf", DenSound.KindOf("wolf"));
        Assert.Equal("wolfb", DenSound.KindOf("wolf_blighted"));
        Assert.Equal("boar", DenSound.KindOf("boar"));
        Assert.Equal("yearling", DenSound.KindOf("lt_pack"));
        Assert.Equal("packmother", DenSound.KindOf("boss_pack"));
        Assert.Null(DenSound.KindOf("risen"));
        Assert.True(DenSound.Unlimited("packmother"));
        Assert.False(DenSound.Unlimited("wolf"));
    }

    [Fact]
    public void TheLimiterHoldsMaxVoicesAndTheCooldownsAndLetsABossThrough()
    {
        var l = new DenSound.VoiceLimiter();
        Assert.True(l.Admit("wolf", "lunge", 0));
        Assert.False(l.Admit("wolf", "lunge", 0.5));   // inside the per-kind cooldown
        Assert.True(l.Admit("wolf", "lunge", 1.0));    // outside it
        Assert.True(l.Admit("boar", "bite", 1.0));
        Assert.True(l.Admit("wolfb", "hurt", 1.05));
        Assert.True(l.Admit("yearling", "lunge", 1.05)); // four held now
        Assert.False(l.Admit("yearling", "bite", 1.1)); // a fifth is refused
        Assert.True(l.Admit("yearling", "death", 1.1)); // a death is always heard
        Assert.True(l.Admit("packmother", "arrival", 1.1));
        Assert.True(l.Admit("packmother", "arrival", 1.11));
    }

    [Fact]
    public void APackWakesAsOneHowlThenTheNext()
    {
        var l = new DenSound.VoiceLimiter();
        Assert.True(l.Admit("wolf", "notice", 0));
        Assert.False(l.Admit("wolfb", "notice", 0.2)); // inside the gap whatever the kind
        Assert.True(l.Admit("wolfb", "notice", 0.5));
    }

    [Fact]
    public void HerEffortIsChancePlusCooldownAndAHeavyOneGrunts()
    {
        var g = new DenSound.GruntRule();
        Assert.True(g.Admit(true, 10, 0.5));
        Assert.False(g.Admit(true, 10.3, 0.5));   // cooldown
        Assert.False(g.Admit(true, 11, 0.9));     // the chance said no
        Assert.True(g.Admit(true, 11, 0.5));
        Assert.False(g.Admit(false, 11.5, 0.1));  // a light cut after a grunt: cooldown
        Assert.False(g.Admit(false, 14, 0.5));    // a light cut seldom
        Assert.True(g.Admit(false, 14, 0.1));
    }

    [Fact]
    public void ThePitsAreTheConnectedHolesOverTwoSquareMetres()
    {
        const int res = 40; const double step = 0.5, half = 10;
        var f = new float[res * res];
        for (int k = 0; k < f.Length; k++) f[k] = 1;
        for (int j = 5; j < 13; j++) for (int i = 5; i < 13; i++) f[j * res + i] = -1;   // 4 m x 4 m
        f[30 * res + 30] = -1;                                                         // a pebble: 0.25 m2, not a pit
        var p = DenSound.Pits(f, res, half, step);
        var pit = Assert.Single(p);
        Assert.InRange(pit.X, -half + 8 * step - 0.3, -half + 8 * step + 0.3);
        Assert.InRange(pit.R, 1.9, 2.4);
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    public void TheRealDensHaveTheirPitsFoundInTheHoleField(int seed)
    {
        var m = SurvivorUnchained.Maps.MapGen.Generate(new SurvivorUnchained.Maps.MapSpec { Seed = seed, Dungeon = "hollow", Tier = 1, Night = false });
        Assert.Equal("den", m.DungeonTheme);
        double half = m.Meta.Size / 2, step = m.Meta.Size / (m.Meta.Res - 1);
        var pits = DenSound.Pits(m.HoleField!, m.Meta.Res, half, step);
        Assert.NotEmpty(pits);
        foreach (var (x, z, r) in pits)
        {
            Assert.InRange(x, -half, half); Assert.InRange(z, -half, half);
            Assert.True(r >= 0.7, $"a pit of radius {r}");
        }
        // she starts well clear of every pit
        var st = m.Start;
        Assert.All(pits, p => Assert.True(Math.Sqrt((p.X - st.X) * (p.X - st.X) + (p.Z - st.Z) * (p.Z - st.Z)) > p.R + 3));
    }

    [Fact]
    public void ALoopIsFullInsideAPitAndGoneBeyondItsReach()
    {
        Assert.Equal(1, DenSound.Falloff(1, 3));
        Assert.Equal(1, DenSound.Falloff(3, 3));
        Assert.True(DenSound.Falloff(14, 3) is > 0.1 and < 0.5);
        Assert.Equal(0, DenSound.Falloff(40, 3));
    }

    [Fact]
    public void TheMusicFollowsTheDenFromEntranceToBossToStingToQuiet()
    {
        var m = new DenSound.MusicRule();
        m.Update(false, false, 1); Assert.Equal(DenSound.Track.None, m.Want);
        m.Update(true, false, 1); Assert.Equal(DenSound.Track.Explore, m.Want);
        m.Update(true, true, 1); Assert.Equal(DenSound.Track.Boss, m.Want);
        m.Update(true, true, 1); Assert.Equal(DenSound.Track.Boss, m.Want);
        m.Update(true, false, 0.1); Assert.Equal(DenSound.Track.Falls, m.Want);
        m.Update(true, false, 5); Assert.Equal(DenSound.Track.Falls, m.Want);
        m.Update(true, false, 1.5); Assert.Equal(DenSound.Track.None, m.Want);   // then quiet
        m.Update(true, false, 30); Assert.Equal(DenSound.Track.None, m.Want);
        m.Update(false, false, 1); m.Update(true, false, 1);                     // a new den run begins again
        Assert.Equal(DenSound.Track.Explore, m.Want);
    }

    [Fact]
    public void ThePackIsHeardFarOffBeforeTheFirstFightAndNeverDuringOrAfter()
    {
        var r = new DenSound.PackFarRule();
        int heard = 0;
        for (double t = 0; t < 120; t += 0.1) if (r.Admit(true, false, 0.1, 0.5)) heard++;
        Assert.InRange(heard, 2, 4);
        Assert.False(r.Admit(true, true, 0.1, 0.5));       // a fight begins
        for (double t = 0; t < 200; t += 0.1) Assert.False(r.Admit(true, false, 0.1, 0.5));   // and the pack is never far again
        Assert.False(new DenSound.PackFarRule().Admit(false, false, 100, 0.5));   // not in the den
    }

    /// <summary>The 5-wolf pack fight the limiter's numbers were picked from: every voice the sim wants, offered nearest first.</summary>
    internal sealed record Row(double T, string Kind, string Moment, double Dist, bool Played);

    internal static List<Row> PackFight(uint seed, out int wanted)
    {
        var b = BattleTests.Arena(seed);
        b.Player.X = 0; b.Player.Z = 0;
        for (int i = 0; i < 5; i++)
        {
            double a = i * Math.PI * 2 / 5;
            b.SpawnEnemy("wolf", Math.Cos(a) * 9, Math.Sin(a) * 9, new Battle.SpawnOpts { Style = SpawnStyle.Walk });
        }
        var limiter = new DenSound.VoiceLimiter();
        var rows = new List<Row>();
        wanted = 0;
        const double dt = 1.0 / 60;
        for (double t = 0; t < 40; t += dt)
        {
            b.Tick(dt, Math.Sin(t * 0.7) * 0.3, Math.Cos(t * 0.7) * 0.3);
            var want = DenSound.Wants(b.Events.Drain(), b.Player.X, b.Player.Z);
            wanted += want.Count;
            foreach (var w in want)
                rows.Add(new Row(t, w.Kind, w.Moment, w.Dist, limiter.Admit(w.Kind, w.Moment, t)));
        }
        return rows;
    }

    [Fact]
    public void ThePackFightIsHeardButNeverOverFourAtOnceNorTwoNoticesTogether()
    {
        var rows = PackFight(4, out int wanted);
        var played = rows.Where(r => r.Played).ToList();
        Assert.True(wanted > 8, $"the sim says too little: {wanted}");
        Assert.Contains(played, r => r.Moment == "notice");
        Assert.Contains(played, r => r.Moment == "lunge" || r.Moment == "bite");
        Assert.Contains(played, r => r.Moment == "death");
        Assert.True(rows.Any(r => !r.Played), "the limiter never limited");
        for (int i = 1; i < played.Count; i++)
            if (played[i].Moment == "notice" && played[i - 1].Moment == "notice")
                Assert.True(played[i].T - played[i - 1].T >= DenSound.NoticeGap - 1e-9);
        // at no moment more than MaxVoices non-death voices are being held
        foreach (var r in played.Where(p => p.Moment != "death"))
        {
            int held = played.Count(o => o.Moment != "death" && o.T <= r.T && o.T + DenSound.Holds(o.Moment) > r.T);
            Assert.True(held <= DenSound.MaxVoices, $"{held} held at {r.T:F2}");
        }
        var path = Environment.GetEnvironmentVariable("DEN_SOUND_LOG");
        if (path != null)
            File.WriteAllLines(path, rows.Select(r => $"{r.T:F2},{r.Kind},{r.Moment},{r.Dist:F1},{(r.Played ? "played" : "dropped")}"));
    }

    [Fact]
    public void TheSimSaysWhenAWolfNoticesBitesAndLunges()
    {
        var b = BattleTests.Arena(7);
        b.Player.X = 0; b.Player.Z = 0;
        b.SpawnEnemy("wolf", 6, 0, new Battle.SpawnOpts { Style = SpawnStyle.Walk });
        var moments = new List<string>();
        for (double t = 0; t < 20; t += 1.0 / 60)
        {
            b.Tick(1.0 / 60, 0, 0);
            foreach (var ev in b.Events.Drain()) if (ev is Ev.Voice v && v.Def == "wolf") moments.Add(v.Moment);
        }
        Assert.Equal("notice", moments.FirstOrDefault());
        Assert.Equal(1, moments.Count(m => m == "notice"));   // once a life
        Assert.Contains("bite", moments);
    }

    [Fact]
    public void EveryEventTheDenUsesIsInTheBankWithItsTakesRecorded()
    {
        var root = Root();
        var data = SoundBankData.Parse(File.ReadAllText(Path.Combine(root, "data", "content", "sounds.json")));
        var fam = JsonSerializer.Deserialize<Dictionary<string, int>>(File.ReadAllText(Path.Combine(root, "art", "sound", "sounds.json")))!;
        var ids = new List<string> { "bed.den", "den.pits", "den.pack_far", "music.den.explore", "music.den.boss", "music.den.falls",
            "her.grunt", "her.leap", "her.land", "her.dodge", "dodge.perfect", "her.stance", "heartbeat", "voice.wolf.bite" };
        foreach (var k in new[] { "wolf", "wolfb", "boar", "yearling" })
            foreach (var m in new[] { "notice", "lunge", "death" }) ids.Add($"voice.{k}.{m}");
        foreach (var m in new[] { "arrival", "drive", "hamstring", "moonhowl", "phase", "call", "death" }) ids.Add($"voice.packmother.{m}");
        foreach (var id in ids)
        {
            Assert.True(data.Events.TryGetValue(id, out var e), id);
            foreach (var l in e!.Layers)
            {
                Assert.True(fam.ContainsKey(l.Take), $"{id}: {l.Take}");
                for (int n = 0; n < fam[l.Take]; n++)
                    Assert.True(File.Exists(Path.Combine(root, "art", "sound", $"{l.Take}_{n}.wav")), $"{id}: {l.Take}_{n}.wav");
            }
        }
        Assert.Empty(data.Problems(fam.ContainsKey));
    }
}
