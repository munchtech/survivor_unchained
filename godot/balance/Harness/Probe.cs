using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>A build drafted to an ember level and put through a standard
/// test: a crowd of the people at a minute's strength, then a champion that
/// does not die, the survivor untouchable and walking a slow circle. Fast
/// enough for the tests (a second or so), steady enough to compare builds.</summary>
public sealed record ProbeSpec(int Seed, string Calling, string Policy, int Level, int Weapon = 0, int Art = 0, string People = "dead")
{
    public string Key => $"{Calling}/{Policy}/L{Level}/s{Seed}/w{Weapon}";
}

public sealed class ProbeResult
{
    public ProbeSpec Spec = null!;
    public string Build = "";
    /// <summary>Damage a second into a crowd that keeps coming; things killed a second.</summary>
    public double CrowdDps, KillsPerSec;
    /// <summary>Damage the survivor took a second in the crowd (the price of fighting close).</summary>
    public double Intake;
    /// <summary>Damage a second into one champion (a crowd about it).</summary>
    public double BossDps;
    /// <summary>Health as armour, dodge, block and mending make it.</summary>
    public double Ehp;
    public int Weapons, Evolved, OnPath;
    public Dictionary<string, double> DamageBy = new();
    public List<string> Taken = new();

    /// <summary>One number for power: the geometric mean of crowd and champion damage.</summary>
    public double Power => Math.Sqrt(Math.Max(1, CrowdDps) * Math.Max(1, BossDps));
}

public static class Probe
{
    /// <summary>The minute an ember level is usually reached, and the horde's
    /// level then (the arena's own formula, tier 1): the test's strength.</summary>
    public static double MinuteOf(int ember) => Targets.MinuteOf(ember);

    public static int FoeLevel(int ember) => Math.Max(1, 1 + (int)(MinuteOf(ember) / 2.5));

    /// <summary>Draft a build to the level, the policy's way (great blessings at
    /// the start and at the fifteenth minute's level).</summary>
    public static (Journey J, Battle B, List<string> Taken) Build(ProbeSpec spec)
    {
        var a = Callings.Archetype(spec.Calling);
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Probe", Archetype = spec.Calling, Background = "hunter", Palette = a.Palettes[0].Id,
            WeaponItem = a.Weapons[Math.Min(spec.Weapon, a.Weapons.Count - 1)], Ability = a.Abilities[Math.Min(spec.Art, a.Abilities.Count - 1)],
        }, (uint)spec.Seed);
        var b = j.StartBattle(true, new CollisionWorld(200), (_, _) => 0, 0, 0, 0, (uint)spec.Seed, arena: true);
        var pick = Picker.Make(spec.Policy);
        var rng = new Rng((uint)(spec.Seed * 104729 + 7));
        var r = new RunResult { Spec = new RunSpec(spec.Seed, spec.Calling, spec.Policy) };
        int second = Targets.LevelAt(15);
        b.GreatOwed = 1;
        bool gave = false;
        int guard = 0;
        while (guard++ < 400)
        {
            ArenaSim.Drafts(b, pick, rng, r, null);
            if (!gave && b.EmberLevel >= second) { gave = true; b.GreatOwed++; continue; }
            if (b.EmberLevel >= spec.Level) break;
            b.Time = MinuteOf(b.EmberLevel) * 60;
            b.GainEmber((b.EmberNext - b.EmberXp) / b.Stats.Get(Stat.XpGain) + 0.001);
        }
        ArenaSim.Drafts(b, pick, rng, r, null);
        return (j, b, r.Taken.Keys.ToList());
    }

    public static ProbeResult Run(ProbeSpec spec)
    {
        var (j, b, taken) = Build(spec);
        var res = new ProbeResult
        {
            Spec = spec, Build = ArenaSim.Describe(b), Taken = taken, Weapons = b.Weapons.Count,
            Evolved = b.Weapons.Count(w => w.Evolution != null), Ehp = Ehp(b),
        };
        var path = Picker.Make(spec.Policy).Path;
        if (path != null) res.OnPath = b.Weapons.Count(w => path.Weapons.Contains(w.Id));
        b.Time = MinuteOf(spec.Level) * 60;
        Measure(b, res, FoeLevel(spec.Level), spec.People, spec.Seed, drafts: true, spec.Policy);
        return res;
    }

    /// <summary>One combat skill alone (at a rank, or evolved), nothing else
    /// taken, against the standard crowd and champion at a minute's strength:
    /// for keeping the skills even with each other.</summary>
    public static ProbeResult Weapon(string id, int rank, string? evolution, int foeLevel, int seed, string people = "dead")
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Probe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)seed);
        var b = j.StartBattle(true, new CollisionWorld(200), (_, _) => 0, 0, 0, 0, (uint)seed, arena: true);
        foreach (var w in b.Weapons.ToList()) b.RemoveWeapon(w.Id);
        b.AddWeapon(id, rank);
        if (evolution != null)
        {
            var w = b.Weapons[0];
            var evo = w.Def.Evolutions.First(e => e.Id == evolution);
            // Its passive at one rank, as an evolution is earned.
            b.AddBoon(evo.Catalysts[0]);
            b.Evolve(id, evolution);
        }
        b.EmberLevel = Targets.LevelAt(Math.Max(1, (foeLevel - 1) * 2.5));
        b.Time = (foeLevel - 1) * 2.5 * 60;
        var spec = new ProbeSpec(seed, "warden", "first", b.EmberLevel, 0, 0, people);
        var res = new ProbeResult { Spec = spec, Build = ArenaSim.Describe(b), Weapons = 1, Evolved = evolution != null ? 1 : 0, Ehp = Ehp(b) };
        Measure(b, res, foeLevel, people, seed, drafts: false);
        return res;
    }

    /// <summary>The standard test, as an arena of tier 1 is at that minute: the
    /// horde kept at its number, in groups from out of sight, for half a minute
    /// (after it has had time to arrive); then a champion that does not fall
    /// and chases, half the horde about it.</summary>
    static void Measure(Battle b, ProbeResult res, int level, string peopleId, int seed, bool drafts, string? policy = null)
    {
        var people = MapOffers.People(peopleId);
        double minute = b.Time / 60;
        // The yardstick is the people's rank and file as the day knows them (Denizens.Horde), not
        // the arena's growing roster: a new kind of splitter or guard would otherwise move every
        // path's number with it, and the bounds would measure the roster, not the paths.
        var kinds = people.Horde.Select(h => h.Def).Where(d => Enemies.Get(d).Ranged == null && people.Arena.Any(a => a.Def == d && a.From <= minute)).ToList();
        if (kinds.Count == 0) kinds = [people.Arena[0].Def];
        var rng = new Rng((uint)seed * 31 + 5);
        int horde = (int)(22 + 7.5 * minute);
        b.Hooks.OnPlayerDeath = _ => true;
        // The horde's charges as an arena of the fifteenth minute's tier runs them (Sim/Charges.cs).
        b.Charges.Cap = 3;
        b.Charges.Spikes = true;

        double Tick(double seconds, int keep, Enemy? champion)
        {
            double dealt = 0, spawnT = 0;
            for (double t = 0; t < seconds; t += ArenaSim.Dt)
            {
                var p = b.Player;
                // Hurt, never felled: what it costs is counted, and the test goes on.
                if (p.Hp < b.MaxHp * 0.25) p.Hp = b.MaxHp;
                int alive = 0;
                foreach (var e in b.Enemies.Items) if (e.Alive && e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying) alive++;
                if ((spawnT -= ArenaSim.Dt) <= 0 && alive < keep)
                {
                    spawnT = 0.45;
                    double a = rng.Next() * Math.PI * 2, d = 22 + rng.Next() * 6;
                    double gx = p.X + Math.Cos(a) * d, gz = p.Z + Math.Sin(a) * d;
                    string kind = kinds[rng.Int(0, kinds.Count - 1)];
                    for (int k = 0, n = 3 + rng.Int(0, 3) + (int)(minute / 5); k < n; k++)
                        b.SpawnEnemy(kind, gx + (rng.Next() - 0.5) * 5, gz + (rng.Next() - 0.5) * 5, new Battle.SpawnOpts { Level = level });
                }
                // Moved as the arena bot moves (giving ground, closing when it is quiet), the champion chasing.
                var (mx, mz) = Pilot.Steer(b);
                b.Tick(ArenaSim.Dt, mx, mz);
                foreach (var ev in b.Events.Drain())
                    if (ev is Ev.Hit h && champion != null && h.Target == champion.Id) dealt += h.Amount;
                if (drafts && b.DraftOwed) ArenaSim.Drafts(b, Picker.Make(policy!), rng, new RunResult { Spec = new RunSpec(0, "", "") }, null);
                // Nothing more is learned in the test itself.
                if (!drafts) { b.PendingLevels = 0; b.PendingBlessings.Clear(); }
            }
            return dealt;
        }

        Tick(10, horde, null);
        double before = b.DamageBy.Values.Sum();
        int kills = b.KillCount;
        double taken = b.DamageTaken;
        const double crowd = 30;
        Tick(crowd, horde, null);
        res.CrowdDps = (b.DamageBy.Values.Sum() - before) / crowd;
        res.KillsPerSec = (b.KillCount - kills) / crowd;
        res.Intake = (b.DamageTaken - taken) / crowd;
        foreach (var (k, v) in b.DamageBy) res.DamageBy[k] = v;
        foreach (var e in b.Enemies.Items) if (e.Alive && e.Disposition == Disposition.Hostile) b.Enemies.Release(e);
        double ca = rng.Next() * Math.PI * 2;
        var boss = b.SpawnEnemy(people.Champion, b.Player.X + Math.Cos(ca) * 8, b.Player.Z + Math.Sin(ca) * 8, new Battle.SpawnOpts { Level = level + 1, Elite = true });
        if (boss != null) boss.MaxHp = boss.Hp = 1e12;
        const double duel = 25;
        res.BossDps = Tick(duel, horde / 2, boss) / duel;
    }

    /// <summary>Health as the horde sees it: armour, dodge, a ward's blocks, a
    /// barrier and twenty seconds of mending.</summary>
    public static double Ehp(Battle b)
    {
        var st = b.Stats;
        double hp = b.MaxHp;
        double mitig = (1 - StatBlock.ArmorReduction(st.Get(Stat.Armor))) * (1 - Math.Min(0.75, st.Get(Stat.Dodge)));
        double mend = st.Get(Stat.Regen) * 20 * st.Get(Stat.Healing);
        int block = MathX.RoundInt(st.Get(Stat.Block));
        double ward = block > 0 ? hp * 0.08 * (20 / new[] { 12.0, 9, 6 }[Math.Min(3, block) - 1]) : 0;
        int vow = b.Boons.GetValueOrDefault("iron_vow");
        double barrier = vow > 0 ? hp * (vow >= 3 ? 0.24 : vow >= 2 ? 0.18 : 0.12) : 0;
        return (hp + barrier + ward) / Math.Max(0.05, mitig) + mend;
    }
}
