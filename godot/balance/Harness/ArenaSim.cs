using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>One arena to play: who, how they draft, where, how long; the
/// survivor's character level (points in the calling's own attribute), and
/// whether the hands are deft (they read lunges, pots and burning ground as a
/// player who knows the fight does: a death is then the game's, not the bot's).</summary>
public sealed record RunSpec(int Seed, string Calling, string Policy, int Tier = 1, string People = "pack", string[]? Oaths = null,
    double Cap = 40, double Beyond = 0, int Weapon = 0, int Art = 0, int Level = 1, bool Deft = false, double Minutes = 30,
    string Type = "", string Lamps = "empty", string For = "", string Flare = "")
{
    public string Key => $"{Calling}/{Policy}/t{Tier}/{People}/s{Seed}/w{Weapon}" + (Level > 1 ? $"/L{Level}" : "") + (Deft ? "/deft" : "") +
        (Oaths is { Length: > 0 } ? $"/{string.Join("+", Oaths)}" : "") + (Minutes != 30 ? $"/m{Minutes:0}" : "") +
        (Type != "" ? $"/{Type}" : "") + (Lamps != "empty" ? $"/lamps-{Lamps}" : "") + (For != "" ? $"/for-{For}" : "") + (Flare != "" ? $"/flare-{Flare}" : "");
}

/// <summary>A minute of the fight, as the harness saw it.</summary>
public sealed class Minute
{
    public int Ember, Kills, Alive, Drafts;
    public double Damage, Taken, LowHp = 1, TtkFodder, TtkFodder90, TtkElite;
    /// <summary>The horde's charges: runs started, the most at once, seconds with three or
    /// more at once, and spikes (Sim/Charges.cs).</summary>
    public int Charges, ChargePeak, Spikes;
    public double Overlap;
}

public sealed class RunResult
{
    public RunSpec Spec = null!;
    public double? WonAt;
    public bool Died;
    public double Minutes;
    public int Kills, Ember, Cards, Respites, Rerolls, Banishes, Skips;
    public string KilledBy = "", Build = "", Path = "";
    public double DamageTaken, LowHp = 1;
    public double? BossTtk;
    public List<double> HeraldTtk = new();
    public List<Minute> ByMinute = new();
    public Dictionary<string, double> DamageBy = new();
    public Dictionary<string, int> Offered = new(), Taken = new();
    /// <summary>Evolutions, with the minute each came.</summary>
    public List<(string Id, double At)> Evolved = new();
    /// <summary>The minute the arsenal was full and every combat skill evolved, if it was.</summary>
    public double? CompleteAt;
    /// <summary>Normal drafts with a card that ranks or evolves something carried; drafts in all.</summary>
    public int Advancing, NormalDrafts;
    public List<string> Greats = new();
    /// <summary>Every card taken, with the minute it was taken (for comparing runs that took a card early).</summary>
    public List<(string Card, double Minute)> Picks = new();
    /// <summary>What was left of the boss when the survivor fell to it (-1: it was not up).</summary>
    public double BossLeft = -1;
    public int Quaffs;
    /// <summary>The boss's fight: its telegraphed blows marked and landed, its Break (of its
    /// health), its staggers, the phase it reached, and whether it grew wild (three minutes).</summary>
    public int BossMarked, BossLanded, BossStaggers, BossPhase = -1;
    public double BossBreak;
    /// <summary>Each boss phase as it ended: [the Flare's cut, seconds, seconds to its mark or -1] (the last as the fight ended).</summary>
    public List<double[]> BossPhases = new();
    public bool BossSoft;
    /// <summary>The long night: the boss's returns that came, and the dark's oaths sworn.</summary>
    public int Returns, Dark;
    /// <summary>The Kindling's ember-core broken within its minute (null: it never came).</summary>
    public bool? CoreBroken;
    /// <summary>The minibosses met (by def) and those killed: how long each took, and the minute.</summary>
    public List<string> MinibossesMet = new();
    public List<(string Def, double Ttk, double At)> Minibosses = new();
    /// <summary>What the night pays (for the crafting economy, docs/CRAFTING_DESIGN.md):
    /// the gold picked up, the champions slain, and the slain by family.</summary>
    public double Gold;
    public int Champions;
    public Dictionary<string, int> KillsBy = new();
    /// <summary>The survivor's type (road) and the lamps lit (free ones too) at the start.</summary>
    public string Road = "";
    public int LampsLit;
    /// <summary>The Flare: casts, the first cast's minute, the mean gap between casts (s), casts while a boss was up,
    /// its share of the damage done to bosses, clutch casts, and the meter's fill by source.</summary>
    public int FlareCasts, FlareBossCasts, FlareClutches;
    /// <summary>Casts whose blows reached a boss; the Flare's damage to bosses, and all damage to bosses.</summary>
    public int FlareCastsOnBoss;
    public int FlareFullBankShots;
    /// <summary>What each Flare did to the crowd round her (Battle.FlareCrowd's rows).</summary>
    public List<double[]> FlareCrowd = new();
    public double FlareBossDamage, BossDamage;
    /// <summary>The Flare's share of what was truly taken off bosses (health, and a gate's Break up to a tenth).</summary>
    public double FlareBossTook = double.NaN;
    /// <summary>Health taken off bosses (as FlareBossTook counts it), by source: each skill's share of a boss.</summary>
    public Dictionary<string, double> BossTookBy = new();
    /// <summary>A Stand's uplift on a boss: health taken off bosses while it held, and its seconds on a boss (Battle).</summary>
    public double StandTook, StandSeconds;
    /// <summary>The Bulwark's wall: blocks, rebukes, the most stones held at once.</summary>
    public int Blocks, Rebukes, StonesPeak;
    public double FlareFirst = double.NaN, FlareGap = double.NaN, FlareBossShare = double.NaN;
    public Dictionary<string, double> FlareFills = new();

    /// <summary>Won at the half hour and still standing for the boss: the target.</summary>
    public bool Won => WonAt != null;
}

/// <summary>An ember arena played through headless, as the game runs it
/// (Play/Zones/ArenaRun.cs on a map from MapGen), by the Pilot's hands and a
/// Picker's taste in cards.</summary>
public static class ArenaSim
{
    public const double Dt = 1 / 60.0;
    /// <summary>--charges 0: every charger on its own clock, as before the charge director.</summary>
    public static bool Director = true;
    /// <summary>Lamps lit past the board (--light; "{calling}" is the survivor's calling): a measuring aid,
    /// for a lamp Light my way never lights (Banked Flame).</summary>
    public static List<string> Light = new();
    /// <summary>--dark: lamps put out after the board is lit (a Flare's modifiers one at a time on the full board; their points stay unspent).</summary>
    public static List<string> Dark = new();

    public static string Card(Offer o) => o.Kind switch
    {
        OfferKind.Weapon => $"w:{o.Id}",
        OfferKind.Rank => $"r:{o.Id}",
        OfferKind.Evolve => $"e:{o.Branch}",
        OfferKind.Boon when o.Great => $"g:{o.Id}",
        OfferKind.Boon when o.Blessing => $"b:{o.Id}",
        OfferKind.Boon => $"p:{o.Id}",
        OfferKind.Hone => $"h:{o.Id}",
        OfferKind.Union => $"u:{o.Id}",
        OfferKind.Heal => "heal",
        _ => "gold",
    };

    /// <summary>Settle every draft owed, the policy's way (banish, reroll,
    /// skip and choose through the same calls the game makes).</summary>
    public static void Drafts(Battle b, Picker pick, Rng rng, RunResult r, Minute? m)
    {
        int guard = 0;
        while (b.DraftOwed && guard++ < 200)
        {
            bool normal = LevelUp.SkillNext(b);
            var offers = LevelUp.Draft(b);
            if (offers.Count == 0) break;
            int ban = b.Banishes > 0 ? pick.Banish(b, offers) : -1;
            if (ban >= 0 && LevelUp.Banish(b, offers[ban]) is { } afterBan) { offers = afterBan; r.Banishes++; }
            if (b.Rerolls > 0 && pick.Reroll(b, offers) && LevelUp.Reroll(b) is { } again) { offers = again; r.Rerolls++; }
            foreach (var o in offers) r.Offered[Card(o)] = r.Offered.GetValueOrDefault(Card(o)) + 1;
            if (normal)
            {
                r.NormalDrafts++;
                if (offers.Any(o => o.Kind is OfferKind.Rank or OfferKind.Evolve or OfferKind.Hone || (o.Kind == OfferKind.Boon && o.From > 0))) r.Advancing++;
                if (offers.All(o => o.Kind is OfferKind.Heal or OfferKind.Gold)) r.Respites++;
                if (pick.Skip(b, offers) && LevelUp.Skip(b)) { r.Skips++; continue; }
            }
            var take = offers[Math.Clamp(pick.Choose(b, offers, rng), 0, offers.Count - 1)];
            r.Taken[Card(take)] = r.Taken.GetValueOrDefault(Card(take)) + 1;
            if (take.Great) r.Greats.Add(take.Id);
            r.Picks.Add((Card(take), b.Time / 60));
            if (take.Kind == OfferKind.Evolve) r.Evolved.Add((take.Branch!, b.Time / 60));
            LevelUp.Choose(b, take);
            r.Cards++;
            if (m != null) m.Drafts++;
        }
    }

    public static RunResult Play(RunSpec spec)
    {
        var a = Callings.Archetype(spec.Calling);
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = spec.Calling, Background = "hunter", Palette = a.Palettes[0].Id,
            WeaponItem = a.Weapons[Math.Min(spec.Weapon, a.Weapons.Count - 1)], Ability = a.Abilities[Math.Min(spec.Art, a.Abilities.Count - 1)],
            // The type (road), picked at creation as a player picks it (docs/design/CLASSES.md section 2).
            Type = spec.Type,
        }, (uint)spec.Seed);
        // A survivor further on: the levels, and the points put into the calling's own.
        while (j.Ch.Level < spec.Level) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        switch (spec.Calling) { case "arcanist": j.Ch.Attributes.Wits += j.Ch.Points; break; case "stalker": j.Ch.Attributes.Finesse += j.Ch.Points; break; default: j.Ch.Attributes.Might += j.Ch.Points; break; }
        j.Ch.Points = 0;
        // The lamps lit.
        if (spec.Lamps == "full")
        {
            foreach (var id in Lamps.StoryFights) j.World.Facts[$"arena.{id}"] = "won";
            j.World.Facts["lamps.atlas"] = LampBook.AtlasLamps;
        }
        if (spec.Lamps is "suggested" or "full")
        {
            // An arena board is past Act 1: Light my way's whole path (§7's early rule is for the story).
            bool had = j.World.Facts.ContainsKey("chapter.done");
            if (!had) j.World.Facts["chapter.done"] = true;
            LampBook.LightSuggested(j.Ch, j.World);
            if (!had) j.World.Facts.Remove("chapter.done");
        }
        foreach (var id in Light.Select(x => x.Replace("{calling}", spec.Calling)))
            if (!LampBook.Now(j.Ch).Lit.Contains(id)) LampBook.Now(j.Ch).Lit.Add(id);
        foreach (var id in Dark) LampBook.Now(j.Ch).Lit.Remove(id);
        // --flare stand: carry the road's Stand (its lamp lit past its gate if the board hasn't reached it; a measuring aid).
        if (spec.Flare == "stand")
        {
            var road = Lamps.Road(LampBook.Now(j.Ch).Type);
            if (Lamps.FlareLamp(road.Stand) is { } fl && !LampBook.Now(j.Ch).Lit.Contains(fl)) LampBook.Now(j.Ch).Lit.Add(fl);
            if (!LampBook.Carry(j.Ch, road.Stand)) throw new InvalidOperationException($"can't carry {road.Stand}");
        }
        // (A night shorter than the table's is a story's: it ends on its boss.)
        var arena = new ArenaSpec { Id = "table:bot", Name = "The Harness", Seed = spec.Seed, Tier = spec.Tier, People = spec.People, Oaths = (spec.Oaths ?? []).ToList(),
            Minutes = spec.Minutes, Story = spec.Minutes != 30 };
        Arenas.Begin(j.World, arena);
        var map = MapGen.Generate(arena.Map);
        var host = new HeadlessHost(j, spec.Seed);
        var zone = new ArenaRun(host, map, arena);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)spec.Seed, arena: true);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        b.Charges.On = Director;
        int lastStarted = 0, lastSpikes = 0;

        var pick = Picker.Make(spec.Policy);
        var rng = new Rng((uint)(spec.Seed * 7919 + 13));
        var r = new RunResult { Spec = spec, Path = pick.Path?.Id ?? "" };
        var firstHit = new Dictionary<int, double>();
        var fodder = new List<double>();
        var elite = new List<double>();
        double bossAt = -1, bossUp = -1;
        var p = b.Player;
        var m = new Minute();
        double lastDamage = 0, lastTaken = 0;
        int lastKills = 0;
        double t = 0;
        var trace = Environment.GetEnvironmentVariable("ARENA_TRACE") is { } tr && tr.Split('@')[0] == spec.Key ? tr : null;
        double traceFrom = trace != null && trace.Contains('@') ? double.Parse(trace.Split('@')[1], System.Globalization.CultureInfo.InvariantCulture) * 60 : 0;
        while (t < spec.Cap * 60 && p.Alive && host.Result == null)
        {
            var (mx, mz) = Pilot.Steer(b, spec.Deft, zone.BossScript);
            if (Pilot.Act(b, j, mx, mz, zone.BossScript)) r.Quaffs++;
            zone.Step(Dt);
            zone.Frame(Dt);
            b.Tick(Dt, mx, mz);
            foreach (var ev in b.Events.Drain())
            {
                switch (ev)
                {
                    case Ev.Spawn s:
                        firstHit.Remove(s.Enemy);
                        if (Enemies.Get(s.Def).Miniboss) r.MinibossesMet.Add(s.Def);
                        break;
                    case Ev.Hit h when h.Amount > 0 && !firstHit.ContainsKey(h.Target): firstHit[h.Target] = t; break;
                    case Ev.Kill k when k.ByPlayer:
                        r.KillsBy[k.Family.ToString()] = r.KillsBy.GetValueOrDefault(k.Family.ToString()) + 1;
                        if (k.Elite && !k.Boss) r.Champions++;
                        if (firstHit.TryGetValue(k.Enemy, out var t0))
                        {
                            double ttk = t - t0;
                            if (k.Boss) r.BossTtk = ttk;
                            else if (k.Elite)
                            {
                                elite.Add(ttk);
                                if (Enemies.Get(k.Def).Miniboss) r.Minibosses.Add((k.Def, ttk, t / 60));
                                if (b.Enemies.Items[k.Enemy].Named?.Title?.StartsWith("Herald") == true) r.HeraldTtk.Add(ttk);
                            }
                            else fodder.Add(ttk);
                        }
                        firstHit.Remove(k.Enemy);
                        break;
                    case Ev.Kill k2: firstHit.Remove(k2.Enemy); break;
                    case Ev.Telegraph tg when tg.Boss && tg.Kind == TelegraphKind.Blow: r.BossMarked++; break;
                    case Ev.Announce an when an.Title == "Staggered": r.BossStaggers++; break;
                    // ARENA_TRACE=KEY@MINUTE: the blows that land on the survivor, from that minute (why a run fell).
                    case Ev.PlayerHit ph when trace != null && t >= traceFrom:
                        Console.Error.WriteLine($"{t / 60:0.000} {ph.Source,-22} {ph.Amount,6:0} {(ph.Dodged ? "dodged" : ph.Blocked ? "blocked" : "")} hp {p.Hp:0}/{b.MaxHp:0} shield {p.Shield:0}");
                        break;
                }
            }
            host.Pass(Dt);
            j.BankArt(b);
            Drafts(b, pick, rng, r, m);
            m.LowHp = Math.Min(m.LowHp, p.Hp / b.MaxHp);
            m.ChargePeak = Math.Max(m.ChargePeak, b.Charges.Live);
            if (b.Charges.Live >= 3) m.Overlap += Dt;
            t += Dt;
            if (bossUp < 0 && (int)Math.Round(t * 60) % 30 == 0 && b.Enemies.Living().Any(e => e.Boss)) bossUp = b.Time;
            if (r.WonAt == null && zone.Won)
            {
                r.WonAt = t / 60;
                bossAt = t;
            }
            if (r.CompleteAt == null && b.Weapons.Count == Weapons.MaxWeapons && b.Weapons.All(w => w.Evolution != null)) r.CompleteAt = t / 60;
            if ((int)(t / 60) != (int)((t - Dt) / 60))
            {
                double dealt = b.DamageBy.Values.Sum();
                m.Ember = b.EmberLevel;
                m.Kills = b.KillCount - lastKills;
                m.Damage = dealt - lastDamage;
                m.Taken = b.DamageTaken - lastTaken;
                m.Alive = b.Enemies.Items.Count(e => e.Alive && e.Disposition == Disposition.Hostile);
                m.TtkFodder = Median(fodder);
                m.TtkFodder90 = fodder.Count == 0 ? double.NaN : fodder.OrderBy(x => x).ElementAt((int)(fodder.Count * 0.9));
                m.TtkElite = Median(elite);
                m.Charges = b.Charges.Started - lastStarted;
                m.Spikes = b.Charges.SpikesRun - lastSpikes;
                lastStarted = b.Charges.Started; lastSpikes = b.Charges.SpikesRun;
                r.ByMinute.Add(m);
                lastKills = b.KillCount; lastDamage = dealt; lastTaken = b.DamageTaken;
                fodder.Clear(); elite.Clear();
                m = new Minute();
            }
            // Past the win, only as long as asked.
            if (bossAt > 0 && t - bossAt > spec.Beyond * 60) break;
        }
        r.Died = !p.Alive;
        r.Minutes = t / 60;
        if (r.Died && r.WonAt == null && host.Boss is { } bar && t >= arena.Minutes * 60) r.BossLeft = bar.Hp / Math.Max(1, bar.MaxHp);
        // What rules the horde comes at the half hour (an elite, not a Boss, by its kind).
        if (r.WonAt is double won) r.BossTtk = won * 60 - arena.Minutes * 60;
        if (zone.BossScript is { } bs)
        {
            r.BossLanded = b.BossBlowsTaken;
            r.BossBreak = bs.BreakSum / Math.Max(1, bs.MaxHp);
            r.BossPhase = bs.PhaseIx;
            r.BossSoft = bs.Soft;
            r.BossPhases = bs.PhaseLog.Select(x => new[] { x.Cut, x.Seconds, x.MarkAt }).Append(new[] { bs.FlareCut, bs.PhaseT, -1 }).ToList();
        }
        r.Returns = zone.Returns;
        r.CoreBroken = zone.CoreBroken;
        r.Dark = zone.DarkSworn;
        r.Kills = b.KillCount;
        r.Gold = b.GoldGained;
        r.Ember = b.EmberLevel;
        r.DamageTaken = b.DamageTaken;
        r.LowHp = r.ByMinute.Count > 0 ? r.ByMinute.Min(x => x.LowHp) : 1;
        r.KilledBy = r.Died ? p.FellTo ?? p.LastKiller?.Def.Id ?? "?" : "";
        r.DamageBy = new Dictionary<string, double>(b.DamageBy);
        r.Build = Describe(b);
        r.Road = LampBook.Now(j.Ch).Type;
        r.LampsLit = LampBook.Now(j.Ch).Lit.Count;
        r.FlareCasts = b.FlareCasts;
        r.Blocks = b.Blocks; r.Rebukes = b.Rebukes; r.StonesPeak = b.StonesPeak;
        r.FlareClutches = b.FlareClutches;
        r.FlareFills = new Dictionary<string, double>(b.FlareFills);
        if (b.FlareTimes.Count > 0) r.FlareFirst = b.FlareTimes[0] / 60;
        if (b.FlareTimes.Count > 1) r.FlareGap = (b.FlareTimes[^1] - b.FlareTimes[0]) / (b.FlareTimes.Count - 1);
        if (bossUp >= 0) r.FlareBossCasts = b.FlareTimes.Count(x => x >= bossUp);
        double bossDmg = b.BossDamageBy.Values.Sum();
        r.FlareCastsOnBoss = b.FlareCastsOnBoss;
        r.FlareFullBankShots = b.FlareFullBankShots;
        r.FlareCrowd = b.FlareCrowd.ToList();
        r.BossDamage = bossDmg;
        r.FlareBossDamage = b.BossDamageBy.GetValueOrDefault("flare");
        double took = b.BossHealthBy.Values.Sum();
        if (took > 0) r.FlareBossTook = b.BossHealthBy.GetValueOrDefault("flare") / took;
        r.BossTookBy = new Dictionary<string, double>(b.BossHealthBy);
        r.StandTook = b.BossTookInStand; r.StandSeconds = b.StandOnBossSeconds;
        if (bossDmg > 0) r.FlareBossShare = b.BossDamageBy.GetValueOrDefault("flare") / bossDmg;
        return r;
    }

    public static string Describe(Battle b) =>
        string.Join(" ", b.Weapons.Select(w => $"{w.Evolution?.Id ?? w.Id}{w.Rank}")) + " | " +
        string.Join(" ", b.Boons.Select(kv => $"{kv.Key}{kv.Value}"));

    public static double Median(List<double> xs)
    {
        if (xs.Count == 0) return double.NaN;
        var s = xs.OrderBy(x => x).ToList();
        return s[s.Count / 2];
    }
}
