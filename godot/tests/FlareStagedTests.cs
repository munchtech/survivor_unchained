using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Phase 2's four staged Flares (docs/design/CLASSES.md §3.5-3.6; Sim/FlareStaged.cs): their blows on their
/// beat's times, what each does, and the events the view stages them by.</summary>
public class FlareStagedTests
{
    static Battle Carrying(string flare, params string[] mods)
    {
        var f = Lamps.Flare(flare)!;
        var a = Callings.Archetype(f.Calling);
        var ch = Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = f.Calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 1, 7);
        ch.Ability = Abilities.Kin[f.Calling];
        LampBook.State(ch);
        LampBook.SetType(ch, f.Road);
        var lit = LampBook.Now(ch).Lit;
        lit.Add(Lamps.All.Values.First(l => l.Effects.Any(e => e.Do == LampDo.Flare && e.Flare == flare)).Id);
        foreach (var m in mods) lit.Add(Lamps.All.Values.First(l => l.Effects.Any(e => e.Do == LampDo.FlareMod && e.Rule == m)).Id);
        Assert.True(LampBook.Carry(ch, flare));
        var kit = Character.Kit(ch, false);
        var b = new Battle(new BattleSetup
        {
            Seed = 5, Collision = new CollisionWorld(120), Combat = true, Stats = kit.Stats, Weapons = [], Ability = kit.Ability,
            ArtRank = kit.ArtRank, Facets = kit.Facets, Lamps = kit.Lamps, ReflexRanks = kit.ReflexRanks, Level = ch.Level,
        });
        Assert.Equal(flare, b.Flare?.Id);
        return b;
    }

    static List<Ev.Flare> Run(Battle b, double seconds)
    {
        var got = new List<Ev.Flare>();
        for (double t = 0; t < seconds - 1e-9; t += 1 / 60.0)
        {
            b.Tick(1 / 60.0, 0, 0);
            got.AddRange(b.Events.Drain().OfType<Ev.Flare>());
        }
        return got;
    }

    static Enemy Foe(Battle b, double x, double z, double hp = 1e6, bool elite = false, bool boss = false)
    {
        var e = b.SpawnEnemy("risen", x, z)!;
        e.AttackT = 99;
        e.RangedT = 99;
        e.MaxHp = e.Hp = hp;
        e.Elite = elite || boss;
        e.Boss = boss;
        return e;
    }

    static List<Ev.Flare> Cast(Battle b, double seconds = 1.5)
    {
        b.FillFlare(100, "t");
        var got = b.Events.Drain().OfType<Ev.Flare>().ToList();
        Assert.True(b.UseFlare(1, 0));
        got.AddRange(Run(b, seconds));
        return got;
    }

    [Fact]
    public void Every_staged_flare_releases_once_after_its_key_pose_and_ends()
    {
        foreach (var id in new[] { "bell_of_the_morning", "burns_twice", "the_roads_toll", "butchers_hour" })
        {
            var b = Carrying(id);
            Foe(b, 2, 0);
            var ev = Cast(b, 9);
            Assert.Single(ev, e => e.Phase == FlarePhase.Press);
            Assert.Single(ev, e => e.Phase == FlarePhase.Release);
            Assert.Single(ev, e => e.Phase == FlarePhase.End);
            int press = ev.FindIndex(e => e.Phase == FlarePhase.Press), release = ev.FindIndex(e => e.Phase == FlarePhase.Release);
            Assert.True(release > press, id);
        }
    }

    [Fact]
    public void The_bell_tolls_three_times_a_quarter_second_apart_stuns_the_lesser_and_its_last_is_the_blast()
    {
        var b = Carrying("bell_of_the_morning");
        var lesser = Foe(b, 3, 0);
        var champ = Foe(b, -3, 0, elite: true);
        b.Player.Hp = b.MaxHp * 0.5;
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        var ev = Run(b, 0.32);
        Assert.Equal(["toll"], ev.Where(e => e.Phase == FlarePhase.Blow).Select(e => e.Part));
        Assert.True(lesser.Status.Has(StatusKind.Stun));
        Assert.False(champ.Status.Has(StatusKind.Stun));
        Assert.True(lesser.Status.Has(StatusKind.Sear));
        ev.AddRange(Run(b, 1));
        var blows = ev.Where(e => e.Phase == FlarePhase.Blow).ToList();
        Assert.Equal(["toll", "toll", "blast"], blows.Select(e => e.Part));
        Assert.True(blows[^1].Last);
        Assert.Equal([4, 4, 8], blows.Select(e => e.Hitstop));
        Assert.True(b.Player.Hp > b.MaxHp * (0.5 + 3 * 0.04 - 0.01));
    }

    [Fact]
    public void The_fourth_toll_and_the_healing_peal()
    {
        double Mended(Battle b)
        {
            Foe(b, 3, 0);
            b.Player.Hp = b.MaxHp * 0.5;
            Cast(b);
            return b.Player.Hp / b.MaxHp - 0.5;
        }
        var b = Carrying("bell_of_the_morning", "bell.fourth_toll", "bell.healing_peal");
        double plain = Mended(Carrying("bell_of_the_morning")), more = 0;
        Foe(b, 3, 0);
        b.Player.Hp = b.MaxHp * 0.5;
        var ev = Cast(b);
        more = b.Player.Hp / b.MaxHp - 0.5;
        Assert.Equal(["toll", "toll", "toll", "blast"], ev.Where(e => e.Phase == FlarePhase.Blow).Select(e => e.Part));
        // Four tolls at 8% against three at 4% (through the same healing; about x2.67).
        Assert.InRange(more / plain, 2.4, 2.9);
    }

    [Fact]
    public void Burns_twice_freezes_then_twelve_embers_fall_four_on_a_boss_and_the_ice_shatters()
    {
        var b = Carrying("burns_twice");
        var pack = Enumerable.Range(0, 4).Select(i => Foe(b, 6 + 0.4 * i, 3)).ToList();
        var boss = Foe(b, -6, 0, boss: true);
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        var ev = Run(b, 0.32);
        Assert.Equal(["frost"], ev.Where(e => e.Phase == FlarePhase.Blow).Select(e => e.Part));
        Assert.All(pack, e => Assert.True(e.Status.Has(StatusKind.Frozen)));
        Assert.True(boss.Status.Has(StatusKind.Chill));
        ev.AddRange(Run(b, 1));
        var embers = ev.Where(e => e.Phase == FlarePhase.Blow && e.Part == "ember").ToList();
        Assert.Equal(12, embers.Count);
        Assert.Equal(4, embers.Count(e => e.Target == boss.Id));
        // The pack's ice broke under the first ember on it.
        Assert.All(pack, e => Assert.False(e.Status.Has(StatusKind.Frozen)));
    }

    [Fact]
    public void The_roads_toll_cuts_the_strongest_last_and_a_boss_four_times_and_what_it_leaves_low_dies()
    {
        var b = Carrying("the_roads_toll");
        var lesser = Enumerable.Range(0, 9).Select(i => Foe(b, 2 + 0.5 * i, 2)).ToList();
        var champ = Foe(b, -3, 0, hp: 2e6, elite: true);
        var boss = Foe(b, 0, -4, hp: 1e9, boss: true);
        var ev = Cast(b);
        var cuts = ev.Where(e => e.Phase == FlarePhase.Blow && e.Part == "cut").ToList();
        Assert.Equal(12, cuts.Count);
        Assert.All(cuts.TakeLast(4), c => Assert.Equal(boss.Id, c.Target));
        Assert.Equal(champ.Id, cuts[7].Target);
        Assert.Equal([1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 6], cuts.Select(c => c.Hitstop));

        // A thing its cut leaves below a quarter of its health dies.
        var c2 = Carrying("the_roads_toll");
        double one = Lamps.FlarePower(c2.Flare!, c2.Level);
        var weak = Foe(c2, 2, 0, hp: one * 4);
        Cast(c2);
        Assert.False(weak.Alive && weak.State != EnemyState.Dying);
    }

    [Fact]
    public void The_roads_tolls_boss_cuts_carry_the_whole_flare_however_many_stand_round_it()
    {
        // Alone, the boss takes all twelve cuts; with nine round it, four, each three times as hard.
        var alone = Carrying("the_roads_toll");
        // No crits: four hits against twelve would swing on them.
        alone.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -alone.Stats.Get(Stat.CritChance), "test"));
        var b1 = Foe(alone, 0, -4, hp: 1e9, boss: true);
        Cast(alone, 8);
        var crowded = Carrying("the_roads_toll");
        foreach (var i in Enumerable.Range(0, 9)) Foe(crowded, 2 + 0.5 * i, 2, hp: 1e7);
        crowded.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -crowded.Stats.Get(Stat.CritChance), "test"));
        var b2 = Foe(crowded, 0, -4, hp: 1e9, boss: true);
        // Long enough for the poison to run out: it is the Flare's too.
        var ev = Cast(crowded, 8);
        Assert.Equal(4, ev.Count(e => e.Phase == FlarePhase.Blow && e.Target == b2.Id));
        double took1 = alone.BossDamageBy["flare"], took2 = crowded.BossDamageBy["flare"];
        Assert.InRange(took2 / took1, 0.95, 1.2);
    }

    [Fact]
    public void The_roads_toll_passes_over_a_boss_it_cant_hurt_and_its_poison_is_the_flares()
    {
        foreach (var pin in new[] { "shut", "gated" })
        {
            var b = Carrying("the_roads_toll");
            var adds = Enumerable.Range(0, 3).Select(i => Foe(b, 2 + i, 2, hp: 1e8)).ToList();
            var boss = Foe(b, 0, -4, hp: 1e9, boss: true);
            if (pin == "shut") boss.TakenMul = 0;
            else { boss.HpFloor = boss.Hp; boss.Overflow = 0.1 * boss.MaxHp; }
            var ev = Cast(b);
            Assert.DoesNotContain(ev, e => e.Phase == FlarePhase.Blow && e.Target == boss.Id);
            Assert.Equal(12, ev.Count(e => e.Phase == FlarePhase.Blow && adds.Any(a => a.Id == e.Target)));
        }
        var c = Carrying("the_roads_toll");
        var foe = Foe(c, 2, 0, hp: 1e9);
        Cast(c);
        Assert.Equal("flare", foe.Status[StatusKind.Poison]?.From);
    }

    [Fact]
    public void Butchers_hour_doubles_her_speed_and_each_kill_holds_it_longer_and_mends()
    {
        var b = Carrying("butchers_hour");
        var w = b.Weapons.FirstOrDefault();
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        Assert.True(b.HourHolds);
        if (w != null) Assert.Equal(0.5, b.FlareCooldownMul(w), 6);
        double before = b.FlareT;
        b.Player.Hp = b.MaxHp * 0.5;
        var e = Foe(b, 2, 0, hp: 10);
        b.KillEnemy(e, true, null);
        Assert.Equal(before + 0.3, b.FlareT, 6);
        Assert.InRange(b.Player.Hp / b.MaxHp, 0.505, 0.515);
        Run(b, 20);
        Assert.False(b.HourHolds);
    }

    [Fact]
    public void A_flare_that_kills_a_boss_says_so_once()
    {
        var b = Carrying("the_roads_toll");
        var boss = Foe(b, 2, 0, hp: 100, boss: true);
        var ev = Cast(b);
        Assert.False(boss.Alive && boss.State != EnemyState.Dying);
        var kill = Assert.Single(ev, e => e.Phase == FlarePhase.Kill);
        Assert.Equal(boss.Id, kill.Target);
    }
}
