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
    double Cap = 40, double Beyond = 0, int Weapon = 0, int Art = 0, int Level = 1, bool Deft = false)
{
    public string Key => $"{Calling}/{Policy}/t{Tier}/{People}/s{Seed}/w{Weapon}" + (Level > 1 ? $"/L{Level}" : "") + (Deft ? "/deft" : "") +
        (Oaths is { Length: > 0 } ? $"/{string.Join("+", Oaths)}" : "");
}

/// <summary>A minute of the fight, as the harness saw it.</summary>
public sealed class Minute
{
    public int Ember, Kills, Alive, Drafts;
    public double Damage, Taken, LowHp = 1, TtkFodder, TtkFodder90, TtkElite;
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
    public bool BossSoft;

    /// <summary>Won at the half hour and still standing for the boss: the target.</summary>
    public bool Won => WonAt != null;
}

/// <summary>An ember arena played through headless, as the game runs it
/// (Play/Zones/ArenaRun.cs on a map from MapGen), by the Pilot's hands and a
/// Picker's taste in cards.</summary>
public static class ArenaSim
{
    public const double Dt = 1 / 60.0;

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
        }, (uint)spec.Seed);
        // A survivor further on: the levels, and the points put into the calling's own.
        while (j.Ch.Level < spec.Level) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        switch (spec.Calling) { case "arcanist": j.Ch.Attributes.Wits += j.Ch.Points; break; case "stalker": j.Ch.Attributes.Finesse += j.Ch.Points; break; default: j.Ch.Attributes.Might += j.Ch.Points; break; }
        j.Ch.Points = 0;
        var arena = new ArenaSpec { Id = "table:bot", Name = "The Harness", Seed = spec.Seed, Tier = spec.Tier, People = spec.People, Oaths = (spec.Oaths ?? []).ToList() };
        Arenas.Begin(j.World, arena);
        var map = MapGen.Generate(arena.Map);
        var host = new HeadlessHost(j, spec.Seed);
        var zone = new ArenaRun(host, map, arena);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)spec.Seed, arena: true);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);

        var pick = Picker.Make(spec.Policy);
        var rng = new Rng((uint)(spec.Seed * 7919 + 13));
        var r = new RunResult { Spec = spec, Path = pick.Path?.Id ?? "" };
        var firstHit = new Dictionary<int, double>();
        var fodder = new List<double>();
        var elite = new List<double>();
        double bossAt = -1;
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
            if (Pilot.Act(b, j, mx, mz)) r.Quaffs++;
            zone.Step(Dt);
            zone.Frame(Dt);
            b.Tick(Dt, mx, mz);
            foreach (var ev in b.Events.Drain())
            {
                switch (ev)
                {
                    case Ev.Spawn s: firstHit.Remove(s.Enemy); break;
                    case Ev.Hit h when h.Amount > 0 && !firstHit.ContainsKey(h.Target): firstHit[h.Target] = t; break;
                    case Ev.Kill k when k.ByPlayer:
                        if (firstHit.TryGetValue(k.Enemy, out var t0))
                        {
                            double ttk = t - t0;
                            if (k.Boss) r.BossTtk = ttk;
                            else if (k.Elite)
                            {
                                elite.Add(ttk);
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
            t += Dt;
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
            r.BossBreak = bs.BreakSum / Math.Max(1, bs.E.MaxHp);
            r.BossPhase = bs.PhaseIx;
            r.BossSoft = bs.Soft;
        }
        r.Kills = b.KillCount;
        r.Ember = b.EmberLevel;
        r.DamageTaken = b.DamageTaken;
        r.LowHp = r.ByMinute.Count > 0 ? r.ByMinute.Min(x => x.LowHp) : 1;
        r.KilledBy = r.Died ? p.FellTo ?? p.LastKiller?.Def.Id ?? "?" : "";
        r.DamageBy = new Dictionary<string, double>(b.DamageBy);
        r.Build = Describe(b);
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
