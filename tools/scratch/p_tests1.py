import os
ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ac4ec5bbd2763a0df\godot\tests"
FILES = {
os.path.join(ROOT, "EncounterTests.cs"): [
("""using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;
using Xunit;""",
"""using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Sim;
using Xunit;"""),
("""    [Fact]
    public void The_hordes_burning_ground_is_capped_oldest_first()""",
"""    /* ---------------------------------------------------- the new verbs -- */

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
        string? word = null;
        Play(b, 10, _ =>
        {
            foreach (var ev in b.Events.Pending.OfType<Ev.Telegraph>()) if (ev.Label != null) word = ev.Label;
            if (near.HasteT > 0) return;
        });
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
        var b = BattleTests.Arena(39);
        var d = One(b, "drowned", 0.9);
        for (double t = 0; t < 3 && b.Player.SlowT <= 0; t += 1 / 60.0) b.Tick(1 / 60.0, 0, 0);
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
    public void The_hordes_burning_ground_is_capped_oldest_first()"""),
],
}
