using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The hands after the Lamps (docs/design/CLASSES.md Â§0, Â§2.3, Â§3): the dash forms, the reflexes,
/// the Flare and how its meter fills (Sim/Forms.cs, Sim/Flare.cs).</summary>
public class HandsTests
{
    static CharacterData Survivor(string calling, params string[] lit)
    {
        var a = Callings.Archetype(calling);
        var ch = Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 1, 7);
        ch.Ability = Abilities.Kin[calling];
        LampBook.State(ch);
        foreach (var id in lit) LampBook.Now(ch).Lit.Add(id);
        return ch;
    }

    /// <summary>The lamp that teaches the calling's default Strike.</summary>
    static string Ultimate(string calling)
    {
        var road = Lamps.Road(LampBook.DefaultType(calling));
        return Lamps.All.Values.First(l => l.Kind == LampKind.Ultimate && l.Calling == calling && l.Effects.Any(e => e.Do == LampDo.Flare && e.Flare == road.Strike)).Id;
    }

    static Battle Fight(CharacterData ch, double flareStart = 0)
    {
        var kit = Character.Kit(ch, false);
        return new Battle(new BattleSetup
        {
            Seed = 5, Collision = new CollisionWorld(120), Combat = true, Stats = kit.Stats, Weapons = [], Ability = kit.Ability,
            ArtRank = kit.ArtRank, Facets = kit.Facets, Lamps = kit.Lamps, ReflexRanks = kit.ReflexRanks, Level = ch.Level, FlareStart = flareStart,
        });
    }

    static void Tick(Battle b, double seconds, double mx = 0, double mz = 0)
    {
        for (double t = 0; t < seconds - 1e-9; t += 1 / 60.0) { b.Tick(1 / 60.0, mx, mz); b.Events.Drain(); }
    }

    static Enemy Foe(Battle b, double x, double z)
    {
        var e = b.SpawnEnemy("risen", x, z)!;
        e.AttackT = 99;
        e.RangedT = 99;
        return e;
    }

    static Battle Flaring(string calling = "warden") => Fight(Survivor(calling, Ultimate(calling)));

    [Fact]
    public void A_warden_dashes_into_a_bull_rush_once_then_plain()
    {
        var b = Fight(Survivor("warden"));
        var p = b.Player;
        Assert.Equal(AbilityKind.BullRush, b.Ability);
        Assert.True(b.FormReady);
        Assert.True(b.Dash(1, 0));
        Assert.Equal(AbilityKind.BullRush, b.Art.Rush);
        Assert.Equal(8 * b.Stats.Get(Stat.AbilityCooldown) * Abilities.RankHaste(b.ArtRank), p.AbilityCd, 2);
        Assert.Equal(b.MaxHp * 0.15, b.Art.Barrier, 3);
        Assert.True(p.Shield > 0);
        Tick(b, 0.6);
        Assert.Null(b.Art.Rush);
        Assert.True(b.Dash(1, 0));
        Assert.True(p.DashT > 0);
        Assert.Null(b.Art.Rush);
    }

    [Fact]
    public void A_stalkers_vault_leaps_the_way_of_the_dash()
    {
        var b = Fight(Survivor("stalker"));
        var p = b.Player;
        Assert.Equal(AbilityKind.Vault, b.Ability);
        Assert.True(b.Dash(1, 0));
        Assert.NotNull(p.Leap);
        Assert.True(p.Leap!.X1 > p.Leap.X0 + 1);
        Assert.True(p.AbilityCd > 0);
    }

    [Fact]
    public void A_reavers_grapple_with_nothing_to_bite_is_a_plain_dash()
    {
        var b = Fight(Survivor("reaver"));
        var p = b.Player;
        Assert.Equal(AbilityKind.Grapple, b.Ability);
        Assert.True(b.Dash(1, 0));
        Assert.True(p.DashT > 0);
        Assert.Equal(0, p.AbilityCd);
    }

    [Fact]
    public void The_shield_bash_reflex_fires_itself_on_a_crowd_and_leaves_the_forms_wait()
    {
        var b = Fight(Survivor("warden", "warden.shield_bash"));
        var p = b.Player;
        var r = b.Reflexes.Single(x => x.Def.Art == "shield_bash");
        for (int i = 0; i < 3; i++) Foe(b, 1.2 + 0.2 * i, 0.3 * i);
        double wait = p.AbilityCd;
        Tick(b, 0.2);
        Assert.Equal(1, r.Fired);
        Assert.True(r.Cd > 0);
        Assert.Equal(wait, p.AbilityCd, 6);
    }

    [Fact]
    public void The_smoke_bomb_reflex_answers_a_perfect_dodge()
    {
        var b = Fight(Survivor("stalker", "stalker.smoke_bomb"));
        var r = b.Reflexes.Single(x => x.Def.Art == "smoke_bomb");
        Assert.True(b.Dash(1, 0));
        b.HurtPlayer(5, School.Physical, "t", null, telegraphed: true);
        Assert.True(b.Player.PerfectThisDash);
        Assert.Equal(1, r.Fired);
    }

    [Fact]
    public void The_red_tide_reflex_answers_a_low_health()
    {
        var b = Fight(Survivor("reaver", "reaver.red_tide"));
        var r = b.Reflexes.Single(x => x.Def.Art == "red_tide");
        b.Player.Hp = b.MaxHp * 0.2;
        double before = b.Player.Hp;
        Tick(b, 0.2);
        Assert.Equal(1, r.Fired);
        Assert.True(b.Player.Hp > before + b.MaxHp * 0.05);
    }

    [Fact]
    public void The_flare_strikes_and_holds_her_untouchable()
    {
        var b = Flaring();
        var p = b.Player;
        Assert.NotNull(b.Flare);
        Assert.False(b.UseFlare(1, 0));
        b.FillFlare(100, "t");
        Assert.True(b.FlareReady);
        var e = Foe(b, 2, 0);
        Assert.True(b.UseFlare(1, 0));
        Assert.Equal(0, b.FlareMeter, 6);
        Assert.Equal(1, b.FlareCasts);
        Assert.True(p.Iframes >= Math.Min(Battle.StrikeMax, b.Flare!.Length) + Battle.StrikeAfter - 1e-9);
        Assert.True(b.FlareHold > 0);
        Tick(b, 1.4);
        Assert.True(b.DamageBy.GetValueOrDefault("flare") > 0);
        Assert.True(e.Hp < e.MaxHp || !e.Alive);
    }

    [Fact]
    public void A_clutch_flare_mends_a_fifth_over_a_second()
    {
        var b = Flaring();
        b.Player.Hp = b.MaxHp * 0.2;
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        Tick(b, 1.1);
        Assert.Equal(1, b.FlareClutches);
        Assert.InRange(b.Player.Hp / b.MaxHp, 0.36, 0.46);
    }

    [Fact]
    public void A_bright_map_mends_nothing()
    {
        var b = Flaring();
        b.Rules.FlareMends = false;
        b.Player.Hp = b.MaxHp * 0.2;
        b.FillFlare(100, "t");
        Assert.True(b.UseFlare(1, 0));
        Tick(b, 1.1);
        Assert.Equal(1, b.FlareClutches);
        Assert.InRange(b.Player.Hp / b.MaxHp, 0.19, 0.24);
    }

    [Fact]
    public void The_flare_fills_from_a_perfect_dodge_and_from_trouble()
    {
        var b = Flaring("reaver");
        var p = b.Player;
        Assert.True(b.Dash(1, 0));
        b.HurtPlayer(5, School.Physical, "t", null, telegraphed: true);
        Assert.Equal(10, b.FlareMeter, 3);

        // 10% of health lost: +5.5; below a third, +11.
        b.FlareMeter = 0;
        p.Hp = b.MaxHp * 0.5;
        b.HurtPlayerRaw(b.MaxHp * 0.1, School.Physical, "t", null);
        Assert.Equal(5.5, b.FlareMeter, 3);
        b.FlareMeter = 0;
        p.Hp = b.MaxHp * 0.4;
        b.HurtPlayerRaw(b.MaxHp * 0.1, School.Physical, "t", null);
        Assert.Equal(11, b.FlareMeter, 3);

        // The first drop below a quarter: the ember answers (+35), once in 45 s.
        b.FlareMeter = 0;
        p.Hp = b.MaxHp * 0.3;
        b.HurtPlayerRaw(b.MaxHp * 0.1, School.Physical, "t", null);
        Assert.Equal(11 + 35, b.FlareMeter, 3);
        b.FlareMeter = 0;
        p.Hp = b.MaxHp * 0.3;
        b.HurtPlayerRaw(b.MaxHp * 0.1, School.Physical, "t", null);
        Assert.Equal(11, b.FlareMeter, 3);
    }

    [Fact]
    public void Kills_fill_at_most_their_rate_and_a_story_fight_starts_at_half()
    {
        var b = Flaring();
        var foes = Enumerable.Range(0, 12).Select(i => Foe(b, 8 + i * 0.1, 8)).ToList();
        foreach (var e in foes) b.HitEnemy(e, 1e6, School.Physical, [Tag.Physical]);
        double kills = b.FlareFills.GetValueOrDefault("kills");
        Assert.InRange(kills, 0.1 - 1e-9, Battle.FillKillRate + 1e-9);

        Assert.Equal(50, Fight(Survivor("warden", Ultimate("warden")), flareStart: 50).FlareMeter, 3);
    }

    [Fact]
    public void Facet_ids_are_unique_across_every_art()
    {
        var ids = Abilities.All.Values.SelectMany(a => a.Facets.Select(f => f.Id)).ToList();
        Assert.Equal(ids.Count, ids.Distinct().Count());
    }

    [Fact]
    public void A_survivor_made_holding_a_callings_art_ends_holding_the_kin()
    {
        foreach (var (calling, kin) in Abilities.Kin)
        {
            var art = Abilities.All.Values.First(a => a.Calling == calling && !a.Movement);
            var a = Callings.Archetype(calling);
            var ch = Character.Create(new CreationChoice
            {
                Name = "Ashe", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = art.Id,
            }, 1, 7);
            Assert.Equal(kin, ch.Ability);
            Assert.Contains(kin, ch.Known);
        }
        var old = Survivor("warden");
        old.Ability = "shield_bash";
        ArtBook.HoldKin(old);
        Assert.Equal("bull_rush", old.Ability);
        old.Ability = "sprint";
        ArtBook.HoldKin(old);
        Assert.Equal("sprint", old.Ability);
    }
}
