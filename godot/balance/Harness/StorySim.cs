using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>One story night to play: which fight, who, how they draft, how hard; whether it is past
/// Act 1 (no rise of its own), and what she chooses at the boss's side where the story lets her.</summary>
public sealed record StoryRunSpec(int Seed, string Calling, string Policy, string Fight = "hollow", int Tier = 1, int Level = 1, bool Deft = false,
    bool Act2 = false, string Choice = "spare", double Cap = 25, bool Crates = false, bool Naive = false, bool Learned = false)
{
    public string Key => $"{Fight}/{Calling}/{Policy}/t{Tier}/s{Seed}" + (Level > 1 ? $"/L{Level}" : "") + (Deft ? "/deft" : "") + (Act2 ? "/act2" : "") + $"/{Choice}" + (Crates ? "/crates" : "") + (Naive ? "/naive" : "") + (Learned ? "/learned" : "");
    /// <summary>Plain and naive hands meet the boss for the first time on its first life (BossSense.Meeting);
    /// deft hands, and any with --learned, know it already.</summary>
    public bool Meets => !Deft && !Learned;
}

public sealed class StoryRunResult
{
    public StoryRunSpec Spec = null!;
    public bool Won, Spared;
    public double Minutes;
    public List<StoryNight.StageLog> Stages = new();
    public int Falls, Rose, Cards, CardsAtBoss = -1;
    /// <summary>The boss: how long its fight took (won), the marked blows that landed, its Break
    /// (of its health), the phase it reached, whether it grew wild.</summary>
    public double? BossSeconds;
    public int BossMarked, BossLanded, BossPhase = -1;
    public double BossBreak;
    public bool BossSoft;
    public string KilledBy = "", Build = "";
    /// <summary>Where the night stood when it ended or was cut off (a stage that would not end).</summary>
    public string Where = "";
    /// <summary>Each fall: the part of the night, and at the boss its phase, its fight's seconds and how much of
    /// it was left; her health then (whether a fall was the build's or the hands').</summary>
    public List<string> FellAt = new();
    /// <summary>Her health as the boss's ground opened, and how far her weapons reach then (a blade build's
    /// fight is at his flank, a bow's at range).</summary>
    public double MaxHpAtBoss, ReachAtBoss;
    /// <summary>What hurt her, by part of the night ("stage 2", "boss") and source, as a share of her
    /// health: where the danger is.</summary>
    public Dictionary<string, Dictionary<string, double>> HurtBy = new();

    /// <summary>The way in: its minutes, and how low she went on it.</summary>
    public double WayIn => Stages.Where(s => s.Name != "boss").Sum(s => s.Seconds) / 60;
    public double LowWayIn => Stages.Where(s => s.Name != "boss").Select(s => s.LowHp).DefaultIfEmpty(1).Min();
    /// <summary>Won without a fall at the boss: it did not kill her on its first life.</summary>
    public bool BossFirstLife => Won && Stages.LastOrDefault(s => s.Name == "boss")?.Falls == 0;
}

/// <summary>A story night played through headless, as the game runs it (Play/Zones/StoryNight.cs on its
/// people's arena), by the Pilot's hands reading the stage's goal and the boss, and a Picker's taste.</summary>
public static class StorySim
{
    public static StoryRunResult Play(StoryRunSpec spec)
    {
        var a = Callings.Archetype(spec.Calling);
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = spec.Calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[spec.Seed % a.Weapons.Count], Ability = a.Abilities[0],
        }, (uint)spec.Seed);
        while (j.Ch.Level < spec.Level) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        switch (spec.Calling) { case "arcanist": j.Ch.Attributes.Wits += j.Ch.Points; break; case "stalker": j.Ch.Attributes.Finesse += j.Ch.Points; break; default: j.Ch.Attributes.Might += j.Ch.Points; break; }
        j.Ch.Points = 0;
        if (spec.Act2) j.World.Facts["chapter.done"] = true;
        // Where the story lets her choose (Greymuzzle: she knelt and promised, the stream is clean).
        if (spec.Choice != "none") { j.World.Facts["promise.pack"] = true; j.World.Facts["stream.clear"] = true; }
        var arena = StoryFights.Spec(spec.Fight, j.Ctx, "verge", 0, 0, 0);
        arena.Tier = spec.Tier;
        Arenas.Begin(j.World, arena);
        var map = MapGen.Generate(arena.Map);
        var host = new HeadlessHost(j, spec.Seed);
        var zone = new StoryNight(host, map, arena, StoryScripts.For(arena.Id) ?? throw new ArgumentException($"no story night {arena.Id}"));
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)spec.Seed, arena: true, ember: true);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);

        var pick = Picker.Make(spec.Policy);
        SurvivorUnchained.Play.Bosses.BossSense.Meeting? meeting = null;
        bool met = false;
        var rng = new Rng((uint)(spec.Seed * 7919 + 17));
        var drafts = new RunResult { Spec = new RunSpec(spec.Seed, spec.Calling, spec.Policy) };
        var r = new StoryRunResult { Spec = spec };
        double t = 0;
        bool trace = Environment.GetEnvironmentVariable("STORY_TRACE") == spec.Key, outside = false;
        NavField? nav = null;
        double navX = 0, navZ = 0, navT = 0;
        int openedAt = -1;
        var path = new List<(double X, double Z)>();
        int pathI = 0;
        double progressT = 0, bestToGo = double.MaxValue;
        // STORY_TRACE: can each of the place's points be stood on (the crowd and the waves come from them)?
        if (trace)
            foreach (var (id, (px, pz)) in zone.Place.Points)
                Console.Error.WriteLine($"   POINT {id} ({px},{pz}) stand {map.CanStand(px, pz)} blocked {b.Collision.Blocked(px, pz, 0.6)} inside {zone.Place.Inside(px, pz, 0.6)}");
        while (t < spec.Cap * 60 && host.Result == null)
        {
            // The stage's goal, walked to the way a player would (round the walls, through the gates).
            (double X, double Z)? way = null;
            // A run that fires the crates goes to them first, while they are offered.
            var goal = spec.Crates && zone.Interactables.FirstOrDefault(i => i.Id == "story:crates") is { } cr ? (cr.X, cr.Z) : zone.Goal;
            if (goal is var (wx, wz))
            {
                navT -= ArenaSim.Dt;
                var pl = b.Player;
                bool replan = nav == null || navT <= 0 && (Math.Abs(wx - navX) + Math.Abs(wz - navZ) > 2 || openedAt != zone.BeatIx * 10 + (int)zone.Now);
                // Pushed well off her way, or no nearer in three seconds: the way again from where she is.
                if (!replan && path.Count > 0 && (pathI < path.Count && Math.Abs(path[pathI].X - pl.X) + Math.Abs(path[pathI].Z - pl.Z) > 5 || t - progressT > 3)) replan = true;
                if (replan)
                {
                    if (nav == null || Math.Abs(wx - navX) + Math.Abs(wz - navZ) > 0.5 || openedAt != zone.BeatIx * 10 + (int)zone.Now) nav = new NavField(map, b, wx, wz, zone.Place.Bounds());
                    (navX, navZ, navT, openedAt) = (wx, wz, 0.5, zone.BeatIx * 10 + (int)zone.Now);
                    path = nav.Path(pl.X, pl.Z);
                    pathI = 0;
                    progressT = t;
                    bestToGo = double.MaxValue;
                }
                double toGo = Math.Abs(wx - pl.X) + Math.Abs(wz - pl.Z);
                if (toGo < bestToGo - 0.5) { bestToGo = toGo; progressT = t; }
                if (toGo < 2 || path.Count == 0) way = (wx, wz);
                else
                {
                    // Down the way she planned: past the points she has reached, toward the furthest still in a
                    // straight line from her, three metres ahead. (The field's slope alone flipped from one side
                    // of her to the other in a neck, and she stood there for minutes.)
                    while (pathI < path.Count - 1 && Math.Abs(path[pathI].X - pl.X) + Math.Abs(path[pathI].Z - pl.Z) < 1.2) pathI++;
                    int best = pathI;
                    for (int k = pathI; k < Math.Min(path.Count, pathI + 14); k++) if (nav!.Clear(pl.X, pl.Z, path[k].X, path[k].Z)) best = k;
                    double dx = path[best].X - pl.X, dz = path[best].Z - pl.Z, dl = Math.Sqrt(dx * dx + dz * dz);
                    if (dl < 0.2) { dx = wx - pl.X; dz = wz - pl.Z; dl = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz)); }
                    way = (pl.X + dx / dl * 3, pl.Z + dz / dl * 3);
                }
            }
            if (trace && ((int)(t / 5) != (int)((t - ArenaSim.Dt) / 5) || Environment.GetEnvironmentVariable("STORY_TICKS") is string tk0 && t > double.Parse(tk0) && t < double.Parse(tk0) + 8 && (int)(t * 4) != (int)((t - ArenaSim.Dt) * 4))) Console.Error.WriteLine($"{t / 60:0.00} {zone.Now} {zone.BeatIx} at ({b.Player.X:0.0},{b.Player.Z:0.0}) d {zone.Place.Dist(b.Player.X, b.Player.Z):0.00} way {way} goal {zone.Goal} | {zone.Beat?.Goal} | {(zone.Beat?.Bar is { } bar ? $"{bar.Name} {bar.Hp:0}/{bar.MaxHp:0}" : "")} ember {b.EmberLevel} hp {b.Player.Hp:0}/{b.MaxHp:0} shut {zone.Debug()["shut"]} open {zone.Debug()["open"]}{(zone.Now == StoryNight.Stage.Boss && zone.BossScript is { } bsx && bsx.E != null ? $" | boss {bsx.E.Hp:0}/{bsx.E.MaxHp:0} at ({bsx.E.X:0},{bsx.E.Z:0}) ph {bsx.PhaseIx} t {bsx.FightT:0} {bsx.E.State} {bsx.E.Disposition} taken {bsx.E.TakenMul:0.00} floor {bsx.E.HpFloor:0}" : "")}");
            // The boss's first life is a first meeting with it; a fall there teaches it.
            if (zone.Now == StoryNight.Stage.Boss && !met) { met = true; if (spec.Meets) meeting = new(); }
            Pilot.Debug = trace && Environment.GetEnvironmentVariable("STORY_TICKS") is string tk3 && t > double.Parse(tk3) && t < double.Parse(tk3) + 8 && (int)(t * 4) != (int)((t - ArenaSim.Dt) * 4);
            var (mx, mz) = Pilot.Steer(b, spec.Deft, zone.BossScript, goal: way, naive: spec.Naive, strikes: true, first: meeting);
            if (trace && ((int)(t / 5) != (int)((t - ArenaSim.Dt) / 5) || Environment.GetEnvironmentVariable("STORY_TICKS") is string tk && t > double.Parse(tk) && t < double.Parse(tk) + 0.25)) Console.Error.WriteLine($"   steer ({mx:0.00},{mz:0.00}) way {way} zones {b.Zones.Living().Count()} pickups {b.Pickups.Living().Count()} blows {b.Blows.Count} slow {b.Player.SlowF:0.00} speed {b.Stats.Get(Stat.MoveSpeed):0.00} bulwark {b.Player.BulwarkT:0.0} dash {b.Player.DashT:0.00} leap {b.Player.Leap != null} vel ({b.Player.Vx:0.00},{b.Player.Vz:0.00}) still {b.Player.StillT:0.0} hurt {b.Player.HurtT:0.00}");
            if (trace && Environment.GetEnvironmentVariable("STORY_TICKS") is string tk2 && t > double.Parse(tk2) && t < double.Parse(tk2) + 8 && (int)(t * 4) != (int)((t - ArenaSim.Dt) * 4))
                foreach (var k in b.Pickups.Living().Where(k => Math.Abs(k.X - b.Player.X) + Math.Abs(k.Z - b.Player.Z) < 6))
                    Console.Error.WriteLine($"   PICKUP {k.Kind} at ({k.X:0.0},{k.Z:0.0}) value {k.Value:0.0}");
            if (trace && (int)(t / 30) != (int)((t - ArenaSim.Dt) / 30))
                foreach (var c in b.Collision.Within(b.Player.X, b.Player.Z, 2.5))
                    Console.Error.WriteLine($"   PROBE {c.Kind} {c.Tag} at ({c.X:0.0},{c.Z:0.0}) r {c.R:0.0} hw {c.Hw:0.0} hd {c.Hd:0.0} soft {c.Soft} canstand {map.CanStand(b.Player.X + mx, b.Player.Z + mz)}");
            if (trace && (int)(t / 30) != (int)((t - ArenaSim.Dt) / 30))
                foreach (var e in b.Enemies.Living().Where(e => Math.Abs(e.X - b.Player.X) + Math.Abs(e.Z - b.Player.Z) < 3))
                    Console.Error.WriteLine($"   NEAR {e.Def.Id} {e.Disposition} {e.State} at ({e.X:0.0},{e.Z:0.0}) r {e.Radius:0.0} scripted {e.Scripted}");
            Pilot.Act(b, j, mx, mz);
            int fallsBefore = zone.Falls;
            var bossBefore = zone.BossScript;
            zone.Step(ArenaSim.Dt);
            zone.Frame(ArenaSim.Dt);
            b.Tick(ArenaSim.Dt, mx, mz);
            if (zone.Falls > fallsBefore && zone.Now == StoryNight.Stage.Boss) meeting = null;
            if (zone.Falls > fallsBefore)
                r.FellAt.Add(zone.Now == StoryNight.Stage.Boss && bossBefore?.E is { } fe
                    ? $"boss ph{bossBefore.PhaseIx + 1} t{bossBefore.FightT:0} left {fe.Hp / Math.Max(1, fe.MaxHp):0%} max {b.MaxHp:0}"
                    : $"stage {zone.BeatIx + 1} at {t / 60:0.0} max {b.MaxHp:0}");
            foreach (var ev in b.Events.Drain())
            {
                if (ev is Ev.Telegraph { Boss: true, Kind: TelegraphKind.Blow } && zone.Now == StoryNight.Stage.Boss) r.BossMarked++;
                if (ev is Ev.PlayerHit { Dodged: false } hit && hit.Amount > 0)
                {
                    string part = zone.Now == StoryNight.Stage.Boss ? "boss" : $"stage {zone.BeatIx + 1}";
                    var by = r.HurtBy.TryGetValue(part, out var d) ? d : r.HurtBy[part] = new();
                    string src = hit.Label is { } lb ? $"{hit.Source}: {lb}" : hit.Source;
                    by[src] = by.GetValueOrDefault(src) + hit.Amount / Math.Max(1, b.MaxHp);
                }
                // STORY_TRACE=KEY: what lands on her, and the night's turns (why a run fell).
                if (trace && ev is Ev.PlayerHit ph) Console.Error.WriteLine($"{t / 60:0.000} {zone.Now,-7} {(ph.Label is { } phl ? ph.Source + ": " + phl : ph.Source),-36} {ph.Amount,6:0} {(ph.Dodged ? "dodged" : ph.Blocked ? "blocked" : "")} hp {b.Player.Hp:0}/{b.MaxHp:0}");
                if (trace && ev is Ev.Announce an) Console.Error.WriteLine($"{t / 60:0.000} {zone.Now,-7} ** {an.Title} {an.Subtitle}");
            }
            host.Pass(ArenaSim.Dt);
            j.BankArt(b);
            ArenaSim.Drafts(b, pick, rng, drafts, null);
            if (r.CardsAtBoss < 0 && zone.Now == StoryNight.Stage.Boss) { r.CardsAtBoss = drafts.Cards; r.MaxHpAtBoss = b.MaxHp; r.ReachAtBoss = Pilot.Reach(b); }
            // Her choice at his side, by the run's own; and the crates, fired or left, by the run's own.
            var offer = zone.Interactables.FirstOrDefault(i => i.Id == (spec.Choice == "finish" ? "story:finish" : "story:let_go"))
                ?? zone.Interactables.FirstOrDefault(i => i.Id is "story:let_go" or "story:finish");
            offer?.Act();
            if (spec.Crates && zone.Interactables.FirstOrDefault(i => i.Id == "story:crates") is { } crates
                && Math.Abs(crates.X - b.Player.X) + Math.Abs(crates.Z - b.Player.Z) < 6) crates.Act();
            t += ArenaSim.Dt;
            if (trace && !outside && !zone.Place.Inside(b.Player.X, b.Player.Z, -0.6))
            {
                outside = true;
                Console.Error.WriteLine($"{t / 60:0.000} OUT at ({b.Player.X:0.0},{b.Player.Z:0.0}) stage {zone.Now} {zone.BeatIx} dash {b.Player.DashT:0.00} leap {b.Player.Leap != null} rush {b.Art.Rush != null} blocked {b.Collision.Blocked(b.Player.X, b.Player.Z, 0.3)}");
            }
        }
        r.Won = zone.Won;
        r.Spared = arena.Spared || j.World.Fact("greymuzzle").Str == "spared" || j.World.Fact("redcowl").Str == "spared";
        r.Minutes = t / 60;
        r.Stages = zone.Log.ToList();
        r.Falls = zone.Falls;
        r.Rose = b.Player.Rose;
        r.Cards = drafts.Cards;
        r.BossSeconds = r.Won ? r.Stages.LastOrDefault(s => s.Name == "boss")?.Seconds : null;
        if (zone.BossScript is { } bs)
        {
            r.BossLanded = b.BossBlowsTaken;
            r.BossBreak = bs.BreakSum / Math.Max(1, bs.MaxHp);
            r.BossPhase = bs.PhaseIx;
            r.BossSoft = bs.Soft;
        }
        r.KilledBy = !r.Won && host.Result != null ? b.Player.FellTo ?? b.Player.LastKiller?.Def.Id ?? "?" : "";
        r.Build = ArenaSim.Describe(b);
        var pp = b.Player;
        r.Where = $"{zone.Now} {zone.BeatIx} at ({pp.X:0},{pp.Z:0}) goal {(zone.Goal is var (gx, gz) ? $"({gx:0},{gz:0})" : "-")} hostiles {zone.Hostiles()} {zone.Beat?.Goal}";
        return r;
    }

    static double Median(IEnumerable<double> xs)
    {
        var s = xs.OrderBy(x => x).ToList();
        return s.Count == 0 ? double.NaN : s[s.Count / 2];
    }

    static string Pct(int n, int of) => of == 0 ? "-" : $"{100.0 * n / of:0}%";

    /// <summary>STORY_BOSSES.md 0.6's table: one row a fight, tier, draft and pair of hands.</summary>
    public static string Report(List<StoryRunResult> rs)
    {
        var sb = new StringBuilder();
        sb.AppendLine("| Fight | Tier | Draft | Hands | Runs | Won | Night (median min) | Way in | Stage 1 / 2 / 3 (s) | Boss (s) | Under half on the way in | Falls a stage | Boss on its first life | Marked blows landed | Cards at boss |");
        sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|");
        foreach (var g in rs.GroupBy(r => (r.Spec.Fight, r.Spec.Tier, r.Spec.Policy, Hands: r.Spec.Deft ? "deft" : r.Spec.Naive ? "naive" : "plain")).OrderBy(g => g.Key))
        {
            var l = g.ToList();
            int won = l.Count(r => r.Won);
            string stage(int i) => $"{Median(l.Select(r => r.Stages.FirstOrDefault(s => s.Name == $"stage {i}")?.Seconds ?? double.NaN).Where(x => !double.IsNaN(x))):0}";
            int stages = l.Sum(r => r.Stages.Count(s => s.Name != "boss")), fellIn = l.Sum(r => r.Stages.Where(s => s.Name != "boss").Count(s => s.Falls > 0));
            sb.AppendLine($"| {g.Key.Fight} | {g.Key.Tier} | {g.Key.Policy} | {g.Key.Hands} | {l.Count} | {Pct(won, l.Count)} | {Median(l.Select(r => r.Minutes)):0.0} | {Median(l.Select(r => r.WayIn)):0.0} | {stage(1)} / {stage(2)} / {stage(3)} | {Median(l.Where(r => r.BossSeconds != null).Select(r => r.BossSeconds!.Value)):0} | {Pct(l.Count(r => r.LowWayIn < 0.5), l.Count)} | {Pct(fellIn, stages)} | {Pct(l.Count(r => r.BossFirstLife), l.Count)} | {(l.Count == 0 ? 0 : l.Average(r => r.BossLanded)):0.0} | {Median(l.Where(r => r.CardsAtBoss >= 0).Select(r => (double)r.CardsAtBoss)):0} |");
        }
        return sb.ToString();
    }
}
