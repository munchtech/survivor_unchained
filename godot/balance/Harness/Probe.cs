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
            ArenaSim.Drafts(b, pick, rng, r, null, ArenaSim.Cards);
            if (!gave && b.EmberLevel >= second) { gave = true; b.GreatOwed++; continue; }
            if (b.EmberLevel >= spec.Level) break;
            b.Time = MinuteOf(b.EmberLevel) * 60;
            b.GainEmber((b.EmberNext - b.EmberXp) / b.Stats.Get(Stat.XpGain) + 0.001);
        }
        ArenaSim.Drafts(b, pick, rng, r, null, ArenaSim.Cards);
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
        var people = MapOffers.People(spec.People);
        double minute = MinuteOf(spec.Level);
        int level = FoeLevel(spec.Level);
        var kinds = people.Arena.Where(h => h.From <= minute).Select(h => h.Def).Where(d => Enemies.Get(d).Ranged == null).ToList();
        if (kinds.Count == 0) kinds = [people.Arena[0].Def];
        var rng = new Rng((uint)spec.Seed * 31 + 5);
        b.Time = minute * 60;

        // The crowd: kept at forty, coming from every side.
        double Tick(double seconds, int keep, Enemy? champion)
        {
            double angle = 0, dealt = 0;
            for (double t = 0; t < seconds; t += ArenaSim.Dt)
            {
                var p = b.Player;
                p.Iframes = 1;
                p.Hp = b.MaxHp;
                int alive = 0;
                foreach (var e in b.Enemies.Items) if (e.Alive && e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying) alive++;
                for (int k = alive; k < keep; k++)
                {
                    double a = rng.Next() * Math.PI * 2, d = 9 + rng.Next() * 4;
                    b.SpawnEnemy(kinds[rng.Int(0, kinds.Count - 1)], p.X + Math.Cos(a) * d, p.Z + Math.Sin(a) * d, new Battle.SpawnOpts { Level = level });
                }
                // A slow circle, four metres across: moving, never fleeing.
                angle += ArenaSim.Dt * 0.6;
                b.Tick(ArenaSim.Dt, -Math.Sin(angle), Math.Cos(angle));
                foreach (var ev in b.Events.Drain())
                    if (ev is Ev.Hit h && champion != null && h.Target == champion.Id) dealt += h.Amount;
                if (b.DraftOwed) ArenaSim.Drafts(b, Picker.Make(spec.Policy), rng, new RunResult { Spec = new RunSpec(0, "", "") }, null, ArenaSim.Cards);
            }
            return dealt;
        }

        Tick(4, 40, null);
        double before = b.DamageBy.Values.Sum();
        int kills = b.KillCount;
        const double crowd = 30;
        Tick(crowd, 40, null);
        res.CrowdDps = (b.DamageBy.Values.Sum() - before) / crowd;
        res.KillsPerSec = (b.KillCount - kills) / crowd;
        foreach (var (k, v) in b.DamageBy) res.DamageBy[k] = v;

        // The champion: what rules the people, at the minute's strength, that does not fall.
        foreach (var e in b.Enemies.Items) if (e.Alive && e.Disposition == Disposition.Hostile) b.Enemies.Release(e);
        var boss = b.SpawnEnemy(people.Champion, b.Player.X + 3, b.Player.Z, new Battle.SpawnOpts { Level = level + 1, Elite = true });
        if (boss != null) { boss.MaxHp = boss.Hp = 1e12; boss.Speed = 0; }
        const double duel = 20;
        double hit = Tick(duel, 12, boss);
        res.BossDps = hit / duel;
        return res;
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
