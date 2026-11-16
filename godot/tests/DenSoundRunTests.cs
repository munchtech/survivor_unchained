using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Sound;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>A den run, played by the harness's bot, with the sound layer's rules run over its events as the game runs them
/// (SoundBridge + DenAudio, minus the mixer): which den sounds fire, when, how often, what the limiter holds back, and that the
/// score follows the room. DEN_SOUND_RUN=path writes the log that tools/sound/den_proof.py turns into the event table.</summary>
[Collection("Balance")]
public class DenSoundRunTests
{
    readonly ITestOutputHelper _out;
    public DenSoundRunTests(ITestOutputHelper o) { _out = o; }

    sealed record Line(double T, string Id, bool Played, double X, double Z);

    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    /// <summary>The run: every sound id the den layer would ask for, in order.</summary>
    static (List<Line> Log, MapRunResult Result) Run(int seed, string bot)
    {
        var data = SoundBankData.Parse(File.ReadAllText(Path.Combine(Root(), "data", "content", "sounds.json")));
        var fam = JsonSerializer.Deserialize<Dictionary<string, int>>(File.ReadAllText(Path.Combine(Root(), "art", "sound", "sounds.json")))!;
        bool Has(string id) => data.Banked(id, fam.ContainsKey);
        var log = new List<Line>();
        var limiter = new DenSound.VoiceLimiter();
        var her = new DenSound.HerVoice();
        var music = new DenSound.MusicRule();
        var far = new DenSound.PackFarRule();
        var bigHit = new DenSound.BigHitRule();
        var rng = new Random(seed);
        var prevTrack = DenSound.Track.None;
        double lastCombat = -99, lastT = 0;
        void Say(double t, string id, bool played, double x = 0, double z = 0) => log.Add(new Line(t, id, played, x, z));

        MapSim.Tap = (t, evs, b, bossUp) =>
        {
            double dt = Math.Max(0, t - lastT); lastT = t;
            double px = b.Player.X, pz = b.Player.Z;
            if (t < 0.02) Say(t, "_start.nearest_hostile", true, b.Enemies.Items.Where(e => e.Alive && e.Disposition == Disposition.Hostile)
                .Select(e => Math.Sqrt((e.X - px) * (e.X - px) + (e.Z - pz) * (e.Z - pz))).DefaultIfEmpty(-1).Min(), b.Enemies.Items.Count(e => e.Alive && e.Disposition == Disposition.Hostile));
            if (evs.Any(e => e is Ev.Hit or Ev.PlayerHit)) lastCombat = t;
            bool hostileNear = b.Enemies.Items.Any(e => e.Alive && e.Disposition == Disposition.Hostile && (e.X - px) * (e.X - px) + (e.Z - pz) * (e.Z - pz) < 400);
            music.Update(true, bossUp, dt);
            if (music.Want != prevTrack)
            {
                if (prevTrack != DenSound.Track.None) Say(t, $"music.den.{prevTrack.ToString().ToLowerInvariant()}.off", true);
                if (music.Want != DenSound.Track.None) Say(t, $"music.den.{music.Want.ToString().ToLowerInvariant()}", true);
                prevTrack = music.Want;
            }
            if (far.Admit(true, hostileNear || t - lastCombat < 10 || bossUp, dt, rng.NextDouble())) Say(t, "den.pack_far", true);
            if (evs.Any(e => DenSound.BigHit(e, b.MaxHp)) && music.Want != DenSound.Track.None && bigHit.Admit(t)) Say(t, "duck.bighit", true);
            foreach (var w in DenSound.Wants(evs, px, pz))
            {
                string id = $"voice.{w.Kind}.{w.Moment}";
                if (!Has(id)) continue;
                Say(t, id, limiter.Admit(w.Kind, w.Moment, t), w.X, w.Z);
            }
            foreach (var e in evs)
            {
                if (e is Ev.Sound s && s.Id.StartsWith("voice.packmother.") && Has(s.Id)) Say(t, s.Id, true, s.X ?? 0, s.Z ?? 0);
                foreach (var (id, _, _) in her.Of(e, t, rng.NextDouble())) Say(t, id, true);
                if (e is Ev.PerfectDodge) Say(t, "dodge.perfect", true);
                // (what the sim asked for, before the rules: the log's own context, not sounds)
                if (e is Ev.Cast { Heavy: true } or Ev.Cast { Weapon: "sunder" }) Say(t, "_asked.heavy_cast", true);
                if (e is Ev.Slash) Say(t, "_asked.slash", true);
                if (e is Ev.Dash) Say(t, "_asked.dash", true);
            }
        };
        try
        {
            var def = DungeonGen.Get("hollow")!;
            var r = MapSim.Play(new MapRunSpec(seed, "warden", 1, def.People, 6, 1, [], bot, 25, "hollow"));
            return (log, r);
        }
        finally { MapSim.Tap = null; }
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(3)]
    [InlineData(4)]
    [InlineData(5)]
    [InlineData(6)]
    public void TheDenRunSoundsAsDesigned(int seed)
    {
        var (log, r) = Run(seed, "deft");
        _out.WriteLine($"seed {seed}: {(r.Cleared ? "cleared" : "fell")} in {r.Minutes:0.0} min; {log.Count} sound lines");
        foreach (var g in log.GroupBy(l => l.Id).OrderBy(g => g.Key))
            _out.WriteLine($"  {g.Key}: {g.Count(l => l.Played)} played, {g.Count(l => !l.Played)} held");
        var path = Environment.GetEnvironmentVariable("DEN_SOUND_RUN");
        if (path != null)
            File.AppendAllLines(path, log.Select(l => $"{seed},{l.T:F2},{l.Id},{(l.Played ? "played" : "held")},{l.X:F1},{l.Z:F1}"));

        var played = log.Where(l => l.Played).ToList();
        Assert.Contains(played, l => l.Id.EndsWith(".notice"));
        Assert.Contains(played, l => l.Id.EndsWith(".death"));
        // the score: the exploration track first; if the boss came, its track after, and (cleared) the sting and then quiet
        Assert.Equal("music.den.explore", played.First(l => l.Id.StartsWith("music.den.")).Id);
        if (r.Cleared)
        {
            var order = played.Where(l => l.Id.StartsWith("music.den.") && !l.Id.EndsWith(".off")).Select(l => l.Id).ToList();
            Assert.Equal(["music.den.explore", "music.den.boss", "music.den.falls"], order);
            Assert.Contains(played, l => l.Id == "voice.packmother.arrival");
            Assert.Contains(played, l => l.Id == "voice.packmother.drive");
            Assert.Contains(played, l => l.Id == "voice.packmother.death");
        }
        // the far pack: never within ten seconds of a blow, never with the ruler up
        var blows = log.Where(l => l.Id.StartsWith("voice.") && (l.Id.EndsWith(".bite") || l.Id.EndsWith(".hurt") || l.Id.EndsWith(".death"))).Select(l => l.T).ToList();
        double bossAt = played.Where(l => l.Id == "music.den.boss").Select(l => l.T).DefaultIfEmpty(1e9).Min();
        Assert.All(played.Where(l => l.Id == "den.pack_far"), l =>
        {
            Assert.True(l.T < bossAt, $"the pack far off at {l.T:F1} with the ruler up");
            Assert.DoesNotContain(blows, b => b <= l.T && l.T - b < 10);
        });
        // never more than MaxVoices creature voices held at once (a death is always heard: it is let past the cap)
        foreach (var l in played.Where(l => l.Id.StartsWith("voice.") && !l.Id.StartsWith("voice.packmother.") && !l.Id.EndsWith(".death")))
        {
            string moment(string id) => id[(id.LastIndexOf('.') + 1)..];
            int held = played.Count(o => o.Id.StartsWith("voice.") && !o.Id.StartsWith("voice.packmother.") && !o.Id.EndsWith(".death") && o.T <= l.T && o.T + DenSound.Holds(moment(o.Id)) > l.T);
            Assert.True(held <= DenSound.MaxVoices, $"{held} voices held at {l.T:F2}");
        }
    }
}
