using System;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The dash grows by named, visible steps (data/content/dash_steps.json), never by being pressed (the owner,
/// 8 Nov). The checker, each step's effect, and the retired rank-by-use. Content/DashSteps.cs, Sim/DashGrowth.cs.</summary>
public class DashStepTests
{
    const double Dt = 1 / 60.0;

    static Battle Arena(AbilityKind? art, params string[] steps)
    {
        var col = new CollisionWorld(120);
        return new Battle(new BattleSetup { Seed = 3, Collision = col, Combat = true, Stats = BattleTests.BaseStats(), Weapons = [], Ability = art, DashSteps = steps.ToList() });
    }

    static void Tick(Battle b, double s) { for (double t = 0; t < s - 1e-9; t += Dt) { b.Tick(Dt, 0, 0); b.Events.Drain(); } }

    [Fact]
    public void The_steps_file_checks_out()
    {
        var all = DashSteps.All;
        Assert.Equal(all.Count, all.Select(s => s.Id).Distinct().Count());
        foreach (var s in all)
        {
            Assert.False(string.IsNullOrWhiteSpace(s.Name), s.Id);
            Assert.False(string.IsNullOrWhiteSpace(s.Card), s.Id);
            Assert.True(s.Card.Length <= 90 && !s.Card.Contains('\n'), $"{s.Id}: a card is one plain line");
            switch (s.Kind)
            {
                case DashStepKind.Landing: Assert.True(s.Radius > 0 && s.Knockback > 0 && s.Damage > 0, s.Id); break;
                default: Assert.True(s.Amount > 0, s.Id); break;
            }
        }
        foreach (var id in new[] { "second_wind_pip", "long_stride", "quick_breath", "hard_landing" }) Assert.NotNull(DashSteps.Find(id));
        // Hard Landing alone is a board lamp; the rest come from story beats and gear (ARPG.md 3.3), never a card.
        foreach (var s in all)
            if (s.Id == "hard_landing") { Assert.Equal("dash.hard_landing", s.Lamp); Assert.Empty(s.From); }
            else { Assert.Equal("", s.Lamp); Assert.Equal(["story", "gear"], s.From); }
        Assert.True(all.Where(s => s.Kind == DashStepKind.Charge).Sum(s => s.Amount * s.Most) <= DashSteps.MaxPips);
    }

    [Fact]
    public void Another_breath_adds_a_pip_twice_at_most_and_fills_it()
    {
        var b = Arena(null);
        int baseMax = b.MaxDashCharges;
        Assert.True(b.GrantDashStep("second_wind_pip"));
        Assert.Contains(b.Events.Drain(), e => e is Ev.DashStep { Id: "second_wind_pip" });
        Assert.Equal(baseMax + 1, b.MaxDashCharges);
        Assert.Equal(baseMax + 1, b.Player.DashCharges);
        Assert.True(b.GrantDashStep("second_wind_pip"));
        Assert.False(b.GrantDashStep("second_wind_pip"));
        Assert.Equal(baseMax + 2, b.MaxDashCharges);
        // Brought into a fight, silently, full.
        var c = Arena(null, "second_wind_pip");
        Assert.Equal(baseMax + 1, c.Player.DashCharges);
        Assert.DoesNotContain(c.Events.Drain(), e => e is Ev.DashStep);
    }

    static double DashDistance(params string[] steps)
    {
        var b = Arena(null, steps);
        double x0 = b.Player.X;
        Assert.True(b.Dash(1, 0));
        Tick(b, 0.25);
        return b.Player.X - x0;
    }

    [Fact]
    public void Long_stride_carries_the_dash_farther()
    {
        double plain = DashDistance(), far = DashDistance("long_stride");
        Assert.InRange(far / plain, 1.25, 1.35);
    }

    static double Recharge(params string[] steps)
    {
        var b = Arena(null, steps);
        int max = b.MaxDashCharges;
        b.Dash(1, 0);
        double t = 0;
        while (b.Player.DashCharges < max && t < 10) { b.Tick(Dt, 0, 0); b.Events.Drain(); t += Dt; }
        return t;
    }

    [Fact]
    public void Quick_breath_brings_charges_back_sooner()
    {
        Assert.InRange(Recharge("quick_breath") / Recharge(), 0.72, 0.78);
    }

    [Fact]
    public void Hard_landing_shoves_lesser_things_aside_at_the_end_of_a_dash()
    {
        var b = Arena(null, "hard_landing");
        var near = b.SpawnEnemy("footpad", b.Player.X + 6.5, b.Player.Z)!;
        var elite = b.SpawnEnemy("footpad", b.Player.X + 6.5, b.Player.Z + 1, new Battle.SpawnOpts { Elite = true })!;
        near.AttackT = elite.AttackT = 999;
        double hp = near.Hp, ehp = elite.Hp;
        b.Dash(1, 0);
        bool landed = false;
        for (int i = 0; i < 20; i++) { b.Tick(Dt, 0, 0); landed |= b.Events.Drain().Any(e => e is Ev.HardLanding { Radius: 2 }); }
        Assert.True(landed);
        Assert.True(near.Hp < hp);
        Assert.Equal(ehp, elite.Hp);
        // Without the step, nothing.
        var c = Arena(null);
        bool any = false;
        c.Dash(1, 0);
        for (int i = 0; i < 20; i++) { c.Tick(Dt, 0, 0); any |= c.Events.Drain().Any(e => e is Ev.HardLanding); }
        Assert.False(any);
    }

    [Fact]
    public void A_movement_art_gains_no_rank_by_use_and_its_facets_come_by_step()
    {
        var j = Play.Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = Callings.Archetype("warden").Palettes[0].Id,
            WeaponItem = Callings.Archetype("warden").Weapons[0], Ability = Callings.Archetype("warden").Abilities[0],
        }, 42);
        var ch = j.Ch;
        ArtBook.Hold(ch, "bull_rush");
        Assert.Equal(0, ArtBook.Grow(ch, "bull_rush", 500));
        Assert.Equal(1, ArtBook.Rank(ch, "bull_rush"));
        Assert.Equal(0, ArtBook.OpenSlots(ch, "bull_rush"));
        Assert.False(ArtBook.Choose(ch, "bull_rush", "iron_hide"));
        // The dash (with its form riding it) earns no art xp.
        var b = Arena(AbilityKind.BullRush);
        Assert.True(b.Dash(1, 0));
        Tick(b, 1);
        Assert.Equal(0, b.ArtXp);
        Assert.Equal(1, b.ArtRank);
        // A step is kept on her, in the kit, in the fight.
        Assert.True(j.GrantDashStep("hard_landing", null));
        Assert.False(ch.GrantDashStep("hard_landing"));
        Assert.Empty(ArtBook.Facets(ch, "bull_rush"));
        var kit = Character.Kit(ch);
        Assert.Contains("hard_landing", kit.DashSteps);
        var f = Arena(AbilityKind.BullRush, kit.DashSteps.ToArray());
        Assert.Contains("hard_landing", f.DashSteps);
        f.SetArt(AbilityKind.BullRush, 3, []);
        Assert.Contains("hard_landing", f.DashSteps);
        Assert.Equal(1, f.ArtRank);
        // Saved with her.
        var back = Core.Json.Parse<CharacterData>(Core.Json.Write(ch));
        Assert.Equal(["hard_landing"], back.DashSteps.ToArray());
    }
}
