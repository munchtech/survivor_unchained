using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The art in hand: the ways of moving, their facets, and how
/// arts are learned and grow (Sim/Arts.cs, Rpg/ArtBook.cs).</summary>
public class ArtTests
{
    static Battle Arena(AbilityKind art, params string[] facets)
    {
        var s = new StatBlock();
        s.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = 200, [Stat.MoveSpeed] = 5, [Stat.PickupRadius] = 2.4, [Stat.CritChance] = 0, [Stat.CritDamage] = 1.5, [Stat.Luck] = 1,
        });
        var col = new CollisionWorld(120);
        col.AddCircle(20, 0, 1.5);
        return new Battle(new BattleSetup { Seed = 5, Collision = col, Combat = true, Stats = s, Weapons = [], Ability = art, Facets = facets.ToList() });
    }

    static void Tick(Battle b, double seconds, double mx = 0, double mz = 0)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0) { b.Tick(1 / 60.0, mx, mz); b.Events.Drain(); }
    }

    static CreationChoice Choice(string calling)
    {
        var a = Callings.Archetype(calling);
        return new CreationChoice
        {
            Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0], StartBoon = Boons.StartBlessings[0],
        };
    }

    static CharacterData Survivor(string calling) => Character.Create(Choice(calling), 1, 42);
    static Play.Journey Journey(string calling) => Play.Journey.Begin(Choice(calling), 42);

    static Enemy Foe(Battle b, string def, double x, double z)
    {
        var e = b.SpawnEnemy(def, x, z)!;
        e.AttackT = 99;
        e.RangedT = 99;
        return e;
    }

    [Fact]
    public void Sprint_is_pace_and_nothing_slows_it()
    {
        var b = Arena(AbilityKind.Sprint);
        double walk = b.Stats.Get(Stat.MoveSpeed);
        b.Player.SlowT = 5; b.Player.SlowF = 0.4;
        Assert.True(b.UseAbility(1, 0));
        Assert.Equal(walk * 1.7, b.Stats.Get(Stat.MoveSpeed), 3);
        double x0 = b.Player.X;
        Tick(b, 1, 1, 0);
        Assert.True(b.Player.X - x0 > walk * 1.5, $"ran {b.Player.X - x0:0.0} m");
        Tick(b, 3.2);
        Assert.Equal(walk, b.Stats.Get(Stat.MoveSpeed), 3);
    }

    [Fact]
    public void Trample_throws_aside_what_you_run_through()
    {
        var b = Arena(AbilityKind.Sprint, "trample");
        var r = Foe(b, "risen", 2.5, 0);
        b.UseAbility(1, 0);
        Tick(b, 0.8, 1, 0);
        Assert.True(r.Hp < r.MaxHp);
    }

    [Fact]
    public void Mirror_step_leaves_reflections_the_horde_turns_on()
    {
        var b = Arena(AbilityKind.MirrorStep, "glass_heart");
        var wolf = Foe(b, "wolf", -6, 0);
        Tick(b, 0.2);
        Assert.True(b.UseAbility(1, 0));
        Assert.True(b.Player.X > 4, $"stepped to {b.Player.X:0.0}");
        Assert.Equal(2, b.Decoys.Count);
        Assert.Contains(b.Decoys, d => d.Id == wolf.Target);
        // Hostile weapons and the survivor's own leave them be.
        Assert.All(b.Decoys, d => Assert.False(b.Targetable(d)));
        // When one breaks it bursts, and a glass heart mends you.
        b.Player.Hp = 100;
        var mirror = b.Decoys[0];
        b.KillEnemy(mirror, false, null);
        Assert.Single(b.Decoys);
        Assert.True(b.Player.Hp > 100);
    }

    [Fact]
    public void Reflections_stand_still_and_break_when_their_time_is_up()
    {
        var b = Arena(AbilityKind.MirrorStep, "three_mirrors");
        b.UseAbility(1, 0);
        Assert.Equal(3, b.Decoys.Count);
        var at = b.Decoys.Select(d => (d.X, d.Z)).ToList();
        Tick(b, 2);
        Assert.Equal(at, b.Decoys.Select(d => (d.X, d.Z)).ToList());
        Tick(b, 3.5);
        Assert.Empty(b.Decoys);
    }

    [Fact]
    public void Bull_rush_is_a_barrier_and_a_charge_a_champion_stops()
    {
        var b = Arena(AbilityKind.BullRush);
        var small = Foe(b, "risen", 3, 0.2);
        var champ = Foe(b, "enforcer", 6.5, 0);
        Assert.True(b.UseAbility(1, 0));
        Assert.Equal(b.MaxHp * 0.18, b.Player.Shield, 3);
        Assert.False(b.Dash(1, 0));
        Tick(b, 0.6);
        Assert.Null(b.Art.Rush);
        Assert.True(small.Hp < small.MaxHp);
        Assert.True(champ.Hp < champ.MaxHp);
        Assert.True(champ.Status.Has(StatusKind.Stun));
        // Stopped at the champion, not through it.
        Assert.InRange(b.Player.X, 3.5, champ.X);
    }

    [Fact]
    public void A_wraith_is_passed_through_by_missiles_and_mends_on_what_it_drains()
    {
        var b = Arena(AbilityKind.WraithWalk);
        b.Player.Hp = 100;
        var r = Foe(b, "risen", 0.6, 0);
        b.UseAbility(0, 1);
        Tick(b, 0.1);
        Assert.True(r.Hp < r.MaxHp);
        Assert.True(b.Player.Hp > 100);
        // A bolt through the ghost.
        double hp = b.Player.Hp;
        b.Player.Iframes = 0;
        var pr = b.SpawnProjectile(Side.Enemy, b.Player.X - 1, b.Player.Z, 40, School.Frost)!;
        pr.Vx = 20; pr.Speed = 20; pr.Life = 1;
        Tick(b, 0.2);
        Assert.True(b.Player.Hp >= hp);
    }

    [Fact]
    public void A_cinder_trail_burns_where_you_ran_and_backdraft_sets_it_off()
    {
        var b = Arena(AbilityKind.CinderTrail, "backdraft");
        b.UseAbility(1, 0);
        Tick(b, 1.5, 1, 0);
        var trail = b.Zones.Living().Where(z => z.Art == "cinder").ToList();
        Assert.True(trail.Count >= 6, $"{trail.Count} fires");
        var r = Foe(b, "risen", trail[2].X, trail[2].Z + 0.5);
        double before = r.Hp;
        Tick(b, 3);
        Assert.True(r.Hp < before);
        Assert.Empty(b.Zones.Living().Where(z => z.Art == "cinder" && z.Age < z.Life - 0.5));
    }

    [Fact]
    public void The_chain_hauls_you_to_what_it_bites()
    {
        var b = Arena(AbilityKind.Grapple);
        var r = Foe(b, "risen_warrior", 9, 0);
        Tick(b, 1 / 60.0);
        Assert.True(b.UseAbility(1, 0));
        Assert.Equal(AbilityKind.Grapple, b.Art.Rush);
        Tick(b, 0.5);
        Assert.Null(b.Art.Rush);
        Assert.InRange(b.Player.X, 7.5, 9);
        Assert.True(r.Hp < r.MaxHp);
        Assert.True(r.Status.Has(StatusKind.Stun));
    }

    [Fact]
    public void Reel_drags_lesser_things_in()
    {
        var b = Arena(AbilityKind.Grapple, "reel");
        var r = Foe(b, "risen", 8, 0);
        Tick(b, 1 / 60.0);
        b.UseAbility(1, 0);
        Tick(b, 0.6);
        Assert.InRange(b.Player.X, -0.1, 0.1);
        Assert.True(r.X < 3, $"dragged to {r.X:0.0}");
    }

    [Fact]
    public void Stepping_back_into_an_echo_gives_back_half_what_was_lost()
    {
        var b = Arena(AbilityKind.EchoStep);
        Assert.True(b.UseAbility(0, 0));
        Assert.True(b.Player.AbilityCd > 0);
        Tick(b, 1, 1, 0);
        b.Player.Hp -= 80;
        double moved = b.Player.X;
        Assert.True(moved > 3);
        Assert.True(b.UseAbility(0, 0));
        Assert.Equal(0, b.Player.X, 1);
        Assert.Equal(160, b.Player.Hp, 1);
        // Once: the echo is spent.
        Assert.False(b.UseAbility(0, 0));
    }

    [Fact]
    public void An_echo_fades_if_it_is_not_taken()
    {
        var b = Arena(AbilityKind.EchoStep, "decoy_echo");
        b.UseAbility(0, 0);
        Assert.Single(b.Decoys);
        Tick(b, 4.2);
        Assert.Empty(b.Decoys);
        Assert.False(b.UseAbility(0, 0));
    }

    [Fact]
    public void Vault_springs_back_from_the_aim_and_leaves_snares()
    {
        var b = Arena(AbilityKind.Vault, "light_feet");
        b.Aim = (8, 0);
        b.Player.DashCharges = 0;
        Assert.True(b.UseAbility(0, 0));
        Assert.NotNull(b.Player.Leap);
        Tick(b, 0.45);
        Assert.InRange(b.Player.X, -6.2, -5);
        Assert.Contains(b.Zones.Living(), z => z.Art == "snare" && Math.Abs(z.X) < 0.1);
        Assert.Equal(1, b.Player.DashCharges);
    }

    [Theory]
    [InlineData(AbilityKind.Leap)]
    [InlineData(AbilityKind.Blink)]
    [InlineData(AbilityKind.MirrorStep)]
    [InlineData(AbilityKind.Vault)]
    public void No_art_carries_you_off_the_fights_ground(AbilityKind art)
    {
        var b = Arena(art);
        b.InBounds = (x, z) => Math.Abs(x) < 3;
        b.Aim = art == AbilityKind.Vault ? (-8, 0) : (8, 0);
        Assert.True(b.UseAbility(1, 0));
        Tick(b, 0.6);
        Assert.InRange(b.Player.X, -3, 3);
    }

    [Fact]
    public void Marked_prey_dies_outright_below_the_line()
    {
        var b = Arena(AbilityKind.MarkPrey, "executioner");
        var e = Foe(b, "enforcer", 6, 0);
        Tick(b, 1 / 60.0);
        Assert.True(b.UseAbility(1, 0));
        Assert.True(e.Prey);
        e.Hp = e.MaxHp * 0.4;
        b.HitEnemy(e, 1, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        Assert.True(e.Alive && e.State != EnemyState.Dying);
        e.Hp = e.MaxHp * 0.29;
        b.HitEnemy(e, 1, School.Physical, [Tag.Physical], new HitOpts { NoCrit = true });
        Assert.Equal(EnemyState.Dying, e.State);
    }

    [Fact]
    public void An_art_grows_with_use_and_kills_made_while_it_is_fresh()
    {
        var b = Arena(AbilityKind.Sprint);
        b.UseAbility(1, 0);
        Assert.Equal(1, b.ArtXp, 3);
        var r = Foe(b, "risen", 4, 0);
        b.HitEnemy(r, 1e6, School.Physical, [Tag.Physical]);
        Assert.Equal(1.2, b.ArtXp, 3);
    }

    [Fact]
    public void Ranks_open_facets_and_the_book_keeps_them()
    {
        var ch = Survivor("warden");
        Assert.Contains("shield_bash", ch.Known);
        Assert.Contains("bulwark", ch.Known);
        Assert.Contains("bull_rush", ch.Known);
        Assert.Contains("sprint", ch.Known);
        Assert.Equal(1, ArtBook.Rank(ch, "sprint"));
        Assert.False(ArtBook.Choose(ch, "sprint", "trample"));
        Assert.Equal(2, ArtBook.Grow(ch, "sprint", Abilities.RankXp[1]));
        Assert.True(ArtBook.Choose(ch, "sprint", "trample"));
        Assert.False(ArtBook.Choose(ch, "sprint", "second_wind"));
        Assert.False(ArtBook.Choose(ch, "sprint", "no_such_facet"));
        ArtBook.Grow(ch, "sprint", Abilities.RankXp[3]);
        Assert.Equal(4, ArtBook.Rank(ch, "sprint"));
        Assert.True(ArtBook.Choose(ch, "sprint", "second_wind"));
        Assert.True(ArtBook.Hold(ch, "sprint"));
        var kit = Character.Kit(ch);
        Assert.Equal(AbilityKind.Sprint, kit.Ability);
        Assert.Equal(4, kit.ArtRank);
        Assert.Equal(new[] { "trample", "second_wind" }, kit.Facets);
        // Nobody carries what they do not know.
        Assert.False(ArtBook.Hold(ch, "wraith_walk"));
    }

    [Fact]
    public void A_manual_teaches_a_way_of_moving_but_not_another_callings_art()
    {
        var j = Journey("warden");
        Assert.False(ArtBook.Knows(j.Ch, "wraith_walk"));
        Assert.True(j.GiveItem("manual_wraith_walk"));
        var it = j.Ch.Pack.First(i => i?.Def == "manual_wraith_walk")!;
        j.Use(it.Uid, null);
        Assert.True(ArtBook.Knows(j.Ch, "wraith_walk"));
        Assert.DoesNotContain(j.Ch.Pack, i => i?.Def == "manual_wraith_walk");
        Assert.False(ArtBook.Learn(j.Ch, "smoke_bomb"));
        // A survivor from before the book knows their calling's arts.
        var old = Survivor("stalker");
        old.Known.Clear();
        Assert.Contains("vault", ArtBook.Known(old));
        Assert.Contains("mark_prey", ArtBook.Known(old));
    }

    [Fact]
    public void The_fight_writes_what_the_art_grew_to_the_survivor()
    {
        var j = Journey("warden");
        ArtBook.Hold(j.Ch, "sprint");
        var b = BattleTests.Arena(9);
        b.SetArt(AbilityKind.Sprint, 1, []);
        b.ArtXp = Abilities.RankXp[1] + 1;
        j.BankArt(b);
        Assert.Equal(0, b.ArtXp);
        Assert.Equal(2, ArtBook.Rank(j.Ch, "sprint"));
        Assert.Equal(2, b.ArtRank);
        j.ChooseFacet("sprint", "tailwind", true, b);
        Assert.True(b.Has("tailwind"));
    }
}
