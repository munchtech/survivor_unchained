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
        foreach (var m in mods) lit.Add(m == "!banked" ? $"{f.Calling}.banked_flame" : Lamps.All.Values.First(l => l.Effects.Any(e => e.Do == LampDo.FlareMod && e.Rule == m)).Id);
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

    static double Gap(Enemy e, double x, double z) => Math.Sqrt((e.X - x) * (e.X - x) + (e.Z - z) * (e.Z - z));

    [Fact]
    public void Burns_twice_aims_each_ember_a_fifth_of_a_second_before_it_lands_and_lands_where_it_aimed()
    {
        var b = Carrying("burns_twice");
        Enumerable.Range(0, 4).Select(i => Foe(b, 6 + 0.4 * i, 3)).ToList();
        Enumerable.Range(0, 3).Select(i => Foe(b, -2, 7 + 0.5 * i)).ToList();
        var boss = Foe(b, -6, 0, hp: 1e9, boss: true);
        b.FillFlare(100, "t");
        b.Events.Drain();
        Assert.True(b.UseFlare(1, 0));
        var at = new List<(double T, Ev.Flare E)>();
        for (int i = 1; i <= 90; i++)
        {
            b.Tick(1 / 60.0, 0, 0);
            at.AddRange(b.Events.Drain().OfType<Ev.Flare>().Select(e => (i / 60.0, e)));
        }
        var aims = at.Where(x => x.E.Phase == FlarePhase.Blow && x.E.Part == "aim").ToList();
        var embers = at.Where(x => x.E.Phase == FlarePhase.Blow && x.E.Part == "ember").ToList();
        Assert.Equal(12, aims.Count);
        Assert.Equal(12, embers.Count);
        // They aim at what the frost froze, so never before it.
        double frost = at.First(x => x.E.Part == "frost").T;
        Assert.All(aims, a => Assert.True(a.T >= frost));
        for (int k = 0; k < 12; k++)
        {
            Assert.InRange(embers[k].T - aims[k].T, 0.2 - 1.5 / 60, 0.2 + 1.5 / 60);
            Assert.Equal(aims[k].E.Target, embers[k].E.Target);
            // A frozen pack hasn't moved; a chilled boss may have stepped a little.
            Assert.InRange(Math.Sqrt(Math.Pow(aims[k].E.TX - embers[k].E.TX, 2) + Math.Pow(aims[k].E.TZ - embers[k].E.TZ, 2)), 0, 1);
            Assert.Equal(k == 11, aims[k].E.Last);
            Assert.Equal(0, aims[k].E.Hitstop);
        }
        Assert.Equal(4, aims.Count(a => a.E.Target == boss.Id));
    }

    [Fact]
    public void Burns_twices_last_ember_throws_back_and_staggers_what_stands_and_a_boss_only_staggers()
    {
        var b = Carrying("burns_twice");
        var pack = Enumerable.Range(0, 4).Select(i => Foe(b, 6 + 0.4 * i, 3)).ToList();
        var boss = Foe(b, -6, 0, hp: 1e9, boss: true);
        // 62 ticks: the last ember (1.05 s) has not yet fallen.
        var ev = Cast(b, 1.02);
        Assert.DoesNotContain(ev, e => e.Part == "shove");
        var was = pack.Select(e => (e.X, e.Z)).ToList();
        ev = Run(b, 0.02);
        var shoves = ev.Where(e => e.Phase == FlarePhase.Blow && e.Part == "shove").ToList();
        Assert.Equal(5, shoves.Count);
        Assert.Equal(0, shoves.Single(e => e.Target == boss.Id).Radius);
        Assert.Equal(0, boss.Kbx);
        Assert.All(pack, e => Assert.True(e.Status.Has(StatusKind.Stun)));
        // The last ember fell on the boss, across the field: the pack is thrown away from it, about 3 m, and comes to
        // rest where its shove said while the stagger holds it.
        Run(b, 0.45);
        for (int i = 0; i < pack.Count; i++)
        {
            var e = pack[i];
            var s = shoves.Single(x => x.Target == e.Id);
            Assert.InRange(s.Radius, 2.5, 8);
            Assert.True(e.X - was[i].X > 0.8 * s.Radius, $"thrown away from the boss: {was[i].X:0.00} to {e.X:0.00}");
            // Near where its shove said (a packed crowd spreads itself a little as it lands).
            Assert.InRange(Gap(e, s.TX, s.TZ), 0, 1.25);
        }
    }

    [Fact]
    public void Burns_twice_strikes_a_boss_with_its_four_embers_alone_or_in_a_crowd()
    {
        double Took(bool crowd)
        {
            var b = Carrying("burns_twice");
            b.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -b.Stats.Get(Stat.CritChance), "test"));
            var boss = Foe(b, -6, 0, hp: 1e9, boss: true);
            // A frozen pack packed round the boss: its embers fall there, but only the four aimed at the boss strike it.
            if (crowd) foreach (var i in Enumerable.Range(0, 6)) Foe(b, -6 + 0.5 * (i % 3), 0.6 * (i / 3) - 0.3, hp: 1e9);
            Cast(b);
            return b.BossDamageBy["flare"];
        }
        Assert.InRange(Took(true) / Took(false), 0.9, 1.1);
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
    public void The_roads_toll_with_nothing_near_cuts_the_air_along_her_aim_on_open_ground()
    {
        var b = Carrying("the_roads_toll");
        b.Aim = (0, 10);
        var cuts = Cast(b).Where(e => e.Phase == FlarePhase.Blow && e.Part == "cut").ToList();
        Assert.Equal(12, cuts.Count);
        Assert.All(cuts, c =>
        {
            double dx = c.TX - b.Player.X, dz = c.TZ - b.Player.Z, d = Math.Sqrt(dx * dx + dz * dz);
            // Out on the ground ahead of her (her aim is +z), within her reach, each with a visible mark.
            Assert.InRange(d, 1.5, 14);
            Assert.True(dz > 0.7 * d, $"ahead: {dx:0.0},{dz:0.0}");
            Assert.True(c.Radius > 0);
            Assert.Equal(0, c.Target);
        });
        // Twelve different places, the last the farthest, on her aim.
        Assert.Equal(12, cuts.Select(c => (Math.Round(c.TX, 1), Math.Round(c.TZ, 1))).Distinct().Count());
        Assert.InRange(cuts[^1].TX - b.Player.X, -0.01, 0.01);
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
        Assert.True(foe.Status.Has(StatusKind.Poison));
        double direct = c.DamageBy["flare"];
        Run(c, 6);
        // Its poison is the Flare's: half its cuts again, over 4 s.
        Assert.InRange(c.DamageBy["flare"] / direct, 1.3, 1.7);

        // Her own poison stack keeps its strength and its owner: the cut doesn't make it the Flare's.
        var d = Carrying("the_roads_toll");
        var bitten = Foe(d, 2, 0, hp: 1e9);
        d.ApplyStatus(bitten, new StatusPayload(StatusKind.Poison, 1, 1, 4), 10, from: "venom");
        double power = bitten.Status[StatusKind.Poison]!.Power;
        Cast(d);
        Assert.Equal(power, bitten.Status[StatusKind.Poison]!.Power, 6);
        Assert.Equal("venom", bitten.Status[StatusKind.Poison]!.From);
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
    public void Butchers_hour_blows_deepen_one_bleed()
    {
        // Every blow while the Hour holds deepens the bleed (up to 5), so the Hour carries its weight on a boss.
        var b = Carrying("butchers_hour");
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        var e = Foe(b, 2, 0, hp: 1e9, boss: true);
        for (int i = 0; i < 3; i++) b.HitEnemy(e, 50, School.Physical, [Tag.Physical], new HitOpts { Projectile = true, NoCrit = true });
        Assert.Equal(3, e.Status[StatusKind.Bleed]!.Stacks);
        for (int i = 0; i < 4; i++) b.HitEnemy(e, 50, School.Physical, [Tag.Physical], new HitOpts { Projectile = true, NoCrit = true });
        Assert.Equal(5, e.Status[StatusKind.Bleed]!.Stacks);
    }

    [Fact]
    public void A_press_staggers_a_boss_a_little_never_outright()
    {
        var b = Carrying("burns_twice");
        var boss = Foe(b, 2, 0, boss: true);
        Run(b, 2); // risen things come up out of the ground untouchable
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        Assert.Equal(0, boss.StaggeredT);
        Assert.InRange(boss.Stagger, 0.01, 0.5);
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

    /* Banked Flame (judge 4, 12 October): the price and the power sit only on the held charge, so a player who
     * lights it and never holds a second fills and strikes as without it. */

    [Fact]
    public void Banked_flame_prices_only_the_held_charge_in_its_data()
    {
        var banked = Lamps.All.Values.Where(l => l.Id.EndsWith(".banked_flame")).ToList();
        Assert.Equal(4, banked.Count);
        foreach (var l in banked)
        {
            var e = l.Effects.Single(x => x.Rule == "flare.banked");
            Assert.Equal(0, e.Arg("slower", -1));
            Assert.Equal(0, e.Arg("harder", -1));
            Assert.Equal(0.5, e.Arg("second", -1));
            Assert.Equal(0.75, e.Arg("held", -1));
        }
    }

    [Fact]
    public void Banked_flame_never_held_fills_and_strikes_as_without_it_and_the_held_shot_strikes_harder()
    {
        static (Battle b, Enemy foe) Bell(bool banked)
        {
            var b = Carrying("bell_of_the_morning", banked ? ["!banked"] : []);
            return (b, Foe(b, 2, 0, boss: true));
        }
        // The first charge fills as without the lamp; the second (the one held) at half.
        var (plain, _) = Bell(false);
        var (lamp, _) = Bell(true);
        Assert.Equal(2, lamp.FlareCharges);
        plain.FillFlare(40, "t"); lamp.FillFlare(40, "t");
        Assert.Equal(plain.FlareMeter, lamp.FlareMeter, 6);
        lamp.FillFlare(Battle.FlareFull - 40, "t");
        Assert.Equal(Battle.FlareFull, lamp.FlareMeter, 6);
        lamp.FillFlare(40, "t");
        Assert.Equal(Battle.FlareFull + 20, lamp.FlareMeter, 6);
        // A Flare spent from one charge strikes as a Flare without the lamp would (its glow aside: one more lamp lit);
        // one spent with both held strikes 75% harder.
        double Took(bool full)
        {
            var (b, foe) = Bell(true);
            b.FillFlare(full ? 4 * Battle.FlareFull : Battle.FlareFull, "t");
            Assert.Equal(full ? 2 * Battle.FlareFull : Battle.FlareFull, b.FlareMeter, 6);
            Assert.True(b.UseFlare(1, 0));
            Run(b, 1.5);
            return foe.MaxHp - foe.Hp;
        }
        Assert.Equal(1.75, Took(true) / Took(false), 2);
    }
}
