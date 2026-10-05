using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The owner's encounter notes (docs/SKILLS_DESIGN.md, "Encounters"): charges in
/// waves with lulls and deliberate spikes, never a lattice of lanes that does not stop.</summary>
public class EncounterTests
{
    /// <summary>A crossbow kneels to shoot (RangedSpec.Aim; the animation lead's kneel): planted for its
    /// aim, the wind-up shown from its start, and its line fixed as it kneels, so a step off the line
    /// in time is a dodge, as a lunge's wind-up is.</summary>
    [Fact]
    public void A_crossbow_kneels_and_aims_before_it_looses_and_its_line_is_fixed()
    {
        var b = BattleTests.Arena(7);
        var p = b.Player;
        var x = b.SpawnEnemy("levy_crossbow", p.X + 7, p.Z, new Battle.SpawnOpts { Level = 1 })!;
        x.RangedT = 0;
        double aim = x.Def.Ranged!.Aim;
        Assert.InRange(aim, 0.4, 0.8);
        bool knelt = false;
        for (int i = 0; i < 60 && !knelt; i++)
        {
            b.Tick(1 / 60.0, 0, 0);
            b.Events.Drain();
            knelt = x.State == EnemyState.Casting && x.Cast == CastKind.Aim;
        }
        Assert.True(knelt);
        Assert.Equal(EnemyAnim.Windup, x.Anim);
        Assert.True(x.AnimT < 0.05);
        Assert.DoesNotContain(b.Projectiles.Living(), pr => pr.Owner == Side.Enemy);
        // She steps well off the line while it aims; it looses down the line it knelt to.
        double lineZ = p.Z;
        p.Z += 4;
        for (double t = 0; t < aim + 0.05; t += 1 / 60.0) { b.Tick(1 / 60.0, 0, 0); b.Events.Drain(); p.Z = lineZ + 4; }
        var bolts = b.Projectiles.Living().Where(pr => pr.Owner == Side.Enemy).ToList();
        Assert.NotEmpty(bolts);
        // The middle bolt of the three flies along the fixed line, not toward where she went.
        var mid = bolts.OrderBy(pr => Math.Abs(pr.Vz)).First();
        Assert.True(Math.Abs(mid.Vz) < Math.Abs(mid.Vx) * 0.05, $"bolt ({mid.Vx:0.0},{mid.Vz:0.0})");
        Assert.NotEqual(CastKind.Aim, x.Cast);
    }

    /// <summary>A survivor who cannot fall, with nothing of her own to kill them, and a ring of
    /// `n` of a kind round her, all in reach of a run.</summary>
    static Battle Ring(string def, int n, uint seed = 5, double r0 = 5, double r1 = 9)
    {
        var b = BattleTests.Arena(seed);
        b.RemoveWeapon("oathblade");
        for (int i = 0; i < n; i++)
        {
            double a = (double)i / n * Math.Tau, r = r0 + (r1 - r0) * b.Rng.Next();
            b.SpawnEnemy(def, b.Player.X + Math.Cos(a) * r, b.Player.Z + Math.Sin(a) * r,
                new Battle.SpawnOpts { Style = SpawnStyle.Walk, Disposition = Disposition.Hostile });
        }
        return b;
    }

    /// <summary>Runs the fight for `seconds`, the survivor kept standing; the runs going after each tick.</summary>
    static List<(double T, int Live, int Started)> Play(Battle b, double seconds, Action<double>? each = null)
    {
        var o = new List<(double, int, int)>();
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            each?.Invoke(t);
            b.Player.Hp = b.MaxHp;
            b.Tick(1 / 60.0, 0, 0);
            b.Events.Drain();
            o.Add((b.Time, b.Charges.Live, b.Charges.Started));
        }
        return o;
    }

    [Fact]
    public void Left_to_their_own_clocks_a_ring_of_tuskers_is_a_lattice_of_lanes()
    {
        // The owner's note, measured: what the director is for.
        var b = Ring("boar", 60);
        b.Charges.On = false;
        var tl = Play(b, 30);
        Assert.True(tl.Max(x => x.Live) >= 10, $"most at once {tl.Max(x => x.Live)}");
    }

    [Fact]
    public void Sixty_tuskers_run_in_waves_never_more_than_the_cap_with_lulls_between()
    {
        var b = Ring("boar", 60);
        b.Charges.Cap = 3;
        var tl = Play(b, 60);
        Assert.True(tl.Max(x => x.Live) <= 3, $"most at once {tl.Max(x => x.Live)}");
        // They do run: a wave is not a wall.
        int started = tl[^1].Started;
        Assert.True(started >= 30, $"only {started} runs in a minute");
        // And they stop: lulls of three seconds or more with no run begun.
        int lulls = 0;
        double lastStart = 0;
        for (int i = 1; i < tl.Count; i++)
            if (tl[i].Started > tl[i - 1].Started)
            {
                if (tl[i].T - lastStart >= 3) lulls++;
                lastStart = tl[i].T;
            }
        Assert.True(lulls >= 3, $"{lulls} lulls in a minute");
        // One after another, not together: never two starts in the same half second of a wave.
        var starts = new List<double>();
        for (int i = 1; i < tl.Count; i++) if (tl[i].Started > tl[i - 1].Started) starts.Add(tl[i].T);
        Assert.All(starts.Zip(starts.Skip(1)), p => Assert.True(p.Second - p.First >= 0.49, $"{p.First:0.00} then {p.Second:0.00}"));
    }

    [Fact]
    public void A_spike_is_told_runs_many_at_once_and_lets_go()
    {
        var b = Ring("boar", 60, seed: 7);
        b.Charges.Cap = 3;
        b.Charges.Spikes = true;
        b.Charges.Tell = "The wolves give tongue.";
        var told = new List<double>();
        var live = new List<(double T, int Live, ChargeDirector.Beat Beat)>();
        bool fired = false;
        for (double t = 0; t < 30; t += 1 / 60.0)
        {
            if (!fired && t >= 8) { fired = true; b.Charges.Spike(b); }
            b.Player.Hp = b.MaxHp;
            b.Tick(1 / 60.0, 0, 0);
            if (b.Events.Drain().OfType<Ev.Bark>().Any(k => k.Text == b.Charges.Tell)) told.Add(b.Time);
            live.Add((b.Time, b.Charges.Live, b.Charges.Now));
        }
        Assert.Single(told);
        double spikeAt = told[0];
        // Told first: nothing runs past the cap until the tell has been heard.
        Assert.All(live.Where(x => x.T < spikeAt + 1.2), x => Assert.True(x.Live <= 3));
        // Then many at once.
        int most = live.Where(x => x.T < spikeAt + 6).Max(x => x.Live);
        Assert.True(most >= 5, $"the spike ran {most} at once");
        // And it lets go: a lull, and back under the wave's cap.
        Assert.Contains(live, x => x.T > spikeAt + 4.8 && x.T < spikeAt + 7 && x.Beat == ChargeDirector.Beat.Lull);
        Assert.All(live.Where(x => x.T > spikeAt + 8), x => Assert.True(x.Live <= 3, $"{x.Live} at {x.T:0.0}"));
    }

    [Fact]
    public void Spikes_come_by_themselves_every_half_minute_or_so_once_there_are_runners()
    {
        var b = Ring("boar", 40, seed: 9);
        b.Charges.Cap = 3;
        b.Charges.Spikes = true;
        b.Charges.Tell = "Now.";
        int spikes0 = b.Charges.SpikesRun;
        // (The first comes after the opening minutes.)
        Play(b, 400);
        int n = b.Charges.SpikesRun - spikes0;
        Assert.InRange(n, 5, 8);
    }

    [Fact]
    public void A_calm_holds_the_crowds_lanes_but_not_a_champions()
    {
        // (Greymuzzle: the tuskers are not his quarrel, as they would be a barrow knight's.)
        var b = Ring("boar", 30, seed: 11);
        var knight = b.SpawnEnemy("wolf_alpha", b.Player.X + 7, b.Player.Z, new Battle.SpawnOpts { Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
        // (Held where it stands: one that has walked up beside her has no run to make.)
        knight.Speed = 0;
        b.Charges.Cap = 3;
        b.Charges.Calm(b, 20);
        bool crowd = false, champion = false;
        Play(b, 15, _ =>
        {
            foreach (var e in b.Enemies.Living())
                if (e.State == EnemyState.Windup) { if (e == knight) champion = true; else crowd = true; }
        });
        Assert.False(crowd);
        Assert.True(champion);
    }

    [Fact]
    public void Tunnellers_go_under_a_few_at_a_time()
    {
        var b = Ring("lampling", 40, seed: 13, r0: 18, r1: 22);
        int most = 0;
        Play(b, 6, _ => most = Math.Max(most, b.Enemies.Living().Count(e => e.State == EnemyState.Burrowed)));
        Assert.InRange(most, 1, b.Charges.UnderCap);
    }

    /* ---------------------------------------------------- the new verbs -- */

    static Enemy One(Battle b, string def, double dx, double dz = 0, bool elite = false) =>
        b.SpawnEnemy(def, b.Player.X + dx, b.Player.Z + dz, new Battle.SpawnOpts { Style = SpawnStyle.Walk, Disposition = Disposition.Hostile, Elite = elite })!;

    static Battle Bare(uint seed)
    {
        var b = BattleTests.Arena(seed);
        b.RemoveWeapon("oathblade");
        return b;
    }

    [Fact]
    public void A_howl_quickens_the_pack_round_it_and_says_so_over_the_howler()
    {
        var b = Bare(31);
        var howler = One(b, "wolf_howler", 12);
        var near = One(b, "wolf", 13, 2);
        var far = One(b, "wolf", -20, 0);
        // (Held where it stands, out of the howl's reach.)
        far.Speed = 0;
        string? word = null;
        for (double t = 0; t < 10; t += 1 / 60.0)
        {
            b.Player.Hp = b.MaxHp;
            b.Tick(1 / 60.0, 0, 0);
            foreach (var ev in b.Events.Drain().OfType<Ev.Telegraph>()) if (ev.Label != null) word = ev.Label;
        }
        Assert.Equal("Howl", word);
        // (Its pulse lasts four seconds of every eight: it has run at least once in ten.)
        Assert.True(near.Haste > 1.2);
        Assert.Equal(0, far.HasteT);
    }

    [Fact]
    public void A_call_marks_where_they_will_come_and_they_come_there()
    {
        var b = Bare(33);
        var nan = One(b, "mb_pike_captain", 9, 0, elite: true);
        var marks = new List<(double X, double Z)>();
        int before = b.Enemies.Living().Count(e => e.Def.Id == "levy_pike");
        for (double t = 0; t < 12 && b.Enemies.Living().Count(e => e.Def.Id == "levy_pike") == before; t += 1 / 60.0)
        {
            b.Player.Hp = b.MaxHp;
            b.Tick(1 / 60.0, 0, 0);
            foreach (var ev in b.Events.Drain().OfType<Ev.Telegraph>()) if (ev.Kind == TelegraphKind.Ground) marks.Add((ev.X, ev.Z));
        }
        var came = b.Enemies.Living().Where(e => e.Def.Id == "levy_pike").ToList();
        Assert.Equal(4, marks.Count);
        Assert.Equal(4, came.Count - before);
        // Each came where a mark was.
        Assert.All(came, e => Assert.Contains(marks, m => Math.Abs(m.X - e.X) < 1.5 && Math.Abs(m.Z - e.Z) < 1.5));
    }

    [Fact]
    public void A_slam_is_marked_where_she_stood_and_lands_only_there()
    {
        var b = Bare(35);
        var door = One(b, "mb_barn_door", 3, 0, elite: true);
        door.SlamT = 0;
        Ev.Telegraph? mark = null;
        for (double t = 0; t < 3 && mark == null; t += 1 / 60.0)
        {
            b.Tick(1 / 60.0, 0, 0);
            mark = b.Events.Drain().OfType<Ev.Telegraph>().FirstOrDefault(x => x.Label == "Down!");
        }
        Assert.NotNull(mark);
        Assert.Equal(CastKind.Slam, door.Cast);
        // She steps off the mark: it lands, and misses.
        b.Player.X += 8;
        double hp = b.Player.Hp;
        for (double t = 0; t < 1.3; t += 1 / 60.0) b.Tick(1 / 60.0, 0, 0);
        Assert.Equal(hp, b.Player.Hp);
    }

    [Fact]
    public void Old_Tusk_runs_its_lane_three_times_and_a_fuse_runner_goes_up_where_its_lane_ends()
    {
        var b = Bare(37);
        var tusk = One(b, "mb_old_tusk", 9, 0, elite: true);
        tusk.RangedT = 0;
        int lanes = 0;
        for (double t = 0; t < 6; t += 1 / 60.0)
        {
            b.Player.Hp = b.MaxHp;
            b.Tick(1 / 60.0, 0, 0);
            lanes += b.Events.Drain().OfType<Ev.Telegraph>().Count(x => x.Id == tusk.Id && x.Shape == TelegraphShape.Line);
        }
        Assert.Equal(3, lanes);

        var b2 = Bare(38);
        var fuse = One(b2, "lampling_fuse", 8);
        fuse.RangedT = 0;
        bool blew = false;
        for (double t = 0; t < 4 && !blew; t += 1 / 60.0)
        {
            b2.Player.Hp = b2.MaxHp;
            b2.Tick(1 / 60.0, 0, 0);
            blew = b2.Events.Drain().OfType<Ev.Kill>().Any(k => k.Def == "lampling_fuse");
        }
        Assert.True(blew);
    }

    [Fact]
    public void A_drowneds_blow_chills_and_a_ward_takes_what_it_says()
    {
        var b = Bare(39);
        var d = One(b, "drowned", 0.9);
        // Its blow chills; and its wet ground, though it hurts, buys no moment of grace from the blow.
        bool bitten = false;
        for (double t = 0; t < 3 && !bitten; t += 1 / 60.0)
        {
            b.Tick(1 / 60.0, 0, 0);
            bitten = b.Events.Drain().OfType<Ev.PlayerHit>().Any(h => h.Source == "Drowned" && h.Amount > 0);
        }
        Assert.True(bitten);
        Assert.True(b.Player.SlowT > 0);

        var wolf = One(b, "wolf", 20);
        double before = wolf.Hp;
        b.HitEnemy(wolf, 10, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        double plain = before - wolf.Hp;
        wolf.WardT = 4; wolf.Ward = 0.3;
        before = wolf.Hp;
        b.HitEnemy(wolf, 10, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        Assert.Equal(plain * 0.7, before - wolf.Hp, 3);
    }

    /* -------------------------------------------------------- the Signs -- */

    [Fact]
    public void A_signed_champion_is_its_kind_with_one_more_verb_and_says_so()
    {
        var knight = Enemies.Get("barrow_knight");
        var d = Signs.Wear(knight, ["swift", "kindled"]);
        Assert.Equal("barrow_knight", d.Id);
        Assert.Equal("Swift, Kindled Barrow Knight", d.Name);
        Assert.True(d.Speed > knight.Speed * 1.3);
        Assert.True(d.Lunge!.Cooldown < knight.Lunge!.Cooldown);
        Assert.NotNull(d.Trail);
        Assert.NotNull(d.Tint);
        // Kept: the same Signs give the same def.
        Assert.Same(d, Signs.Wear(knight, ["swift", "kindled"]));
        // The kind itself is untouched.
        Assert.Null(knight.Trail);
        Assert.Empty(knight.Signs);
    }

    [Fact]
    public void Signs_that_may_not_go_together_never_do()
    {
        var knight = Enemies.Get("barrow_knight");
        Assert.False(Signs.Fits(knight, "rimed", ["swift"]));
        Assert.False(Signs.Fits(knight, "gravebound", ["brood"]));
        Assert.False(Signs.Fits(knight, "volatile", ["swift"]));
        // Never a shield on what already guards.
        Assert.False(Signs.Fits(Enemies.Get("bruiser"), "shielded", []));
        Assert.True(Signs.Fits(knight, "kindled", ["swift"]));
    }

    /* ------------------------------------------------ the new kinds -- */

    [Fact]
    public void Every_people_has_five_stretches_each_with_a_miniboss_and_every_kind_on_a_rig_we_have()
    {
        foreach (var p in MapOffers.Peoples)
        {
            Assert.Equal(5, p.Stretches.Length);
            Assert.All(p.Stretches, s =>
            {
                var mb = Enemies.Get(s.Miniboss);
                Assert.True(mb.Miniboss && mb.Elite, s.Miniboss);
                Assert.False(string.IsNullOrEmpty(mb.Lesson), s.Miniboss);
                Assert.Equal(p.Id, MapOffers.Peoples.First(q => q.Stretches.Any(x => x.Miniboss == s.Miniboss)).Id);
                // Every kind a stretch brings is one of the people's, and joins at its stretch.
                Assert.All(s.Joins, k => Assert.Contains(p.Arena, h => h.Def == k && h.From == s.At));
                Assert.All(s.Signs, g => Signs.Get(g));
            });
            // Minutes rise, and leave room for the heralds at ten and twenty.
            Assert.Equal(p.Stretches.OrderBy(s => s.At).Select(s => s.At), p.Stretches.Select(s => s.At));
            Assert.DoesNotContain(p.Stretches, s => s.At is 10 or 20);
        }
        // On the rigs the crowd already draws: no new model yet (that is the art pass's).
        string[] rigs = ["wolf", "wolf_alpha", "wolf_blighted", "boar", "lampling", "lampling_sapper", "skeleton_minion", "skeleton_warrior",
            "skeleton_warrior_elite", "skeleton_rogue", "skeleton_mage", "kerchief_rogue", "kerchief_hooded", "kerchief_brute", "kerchief_enforcer"];
        var all = MapOffers.Peoples.SelectMany(p => p.Arena.Select(h => h.Def).Concat(p.Stretches.Select(s => s.Miniboss)));
        Assert.All(all, id => Assert.Contains(Enemies.Get(id).Visual, rigs));
        // And no two kinds of a people the same body at the same size and colour.
        foreach (var p in MapOffers.Peoples)
        {
            var looks = p.Arena.Select(h => Enemies.Get(h.Def)).Concat(p.Stretches.Select(s => Enemies.Get(s.Miniboss)))
                .Select(d => (d.Visual, Math.Round(d.Scale ?? 1, 2), d.Tint)).ToList();
            Assert.Equal(looks.Count, looks.Distinct().Count());
        }
    }

    [Fact]
    public void The_hordes_burning_ground_is_capped_oldest_first()
    {
        var b = BattleTests.Arena(15);
        GroundZone? first = null;
        for (int i = 0; i < 40; i++)
        {
            var z = b.SpawnZone(Side.Enemy, i, 0, 1.2, 10, 1, School.Fire);
            first ??= z;
            b.Tick(1 / 60.0, 0, 0);
        }
        Assert.Equal(b.Charges.GroundCap, b.Zones.Living().Count(z => z.Owner == Side.Enemy));
        Assert.DoesNotContain(b.Zones.Living(), z => z.Owner == Side.Enemy && z.X < 1);
    }
}
