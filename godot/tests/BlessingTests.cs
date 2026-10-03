using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Blessings: the ones a survivor starts with, how they deepen, and
/// when the ember brings more (Content/Boons.cs).</summary>
public class BlessingTests
{
    static void Tick(Battle b, double seconds, double mx = 0, double mz = 0)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0) { b.Tick(1 / 60.0, mx, mz); b.Events.Drain(); }
    }

    [Fact]
    public void The_first_blessing_comes_early_and_the_rest_further_apart()
    {
        Assert.Equal(5, Boons.Milestones[0]);
        Assert.True(Boons.IsMilestone(5));
        Assert.False(Boons.IsMilestone(6));
        for (int i = 1; i < 6; i++) Assert.True(Boons.Milestones[i] - Boons.Milestones[i - 1] > Boons.Milestones[i - 1] - (i > 1 ? Boons.Milestones[i - 2] : 0) - 1);
        var b = BattleTests.Arena(4);
        for (int i = 0; i < 4; i++) b.GainEmber(b.EmberNext - b.EmberXp + 0.01);
        Assert.Equal(5, b.EmberLevel);
        Assert.Equal(new[] { 5 }, b.PendingBlessings);
    }

    [Fact]
    public void Every_starting_blessing_deepens_twice_and_says_how()
    {
        foreach (var id in Boons.Great)
        {
            var d = Boons.All[id];
            Assert.Equal(3, d.Max);
            Assert.NotNull(d.DeeperText);
            Assert.Equal(2, d.DeeperText!.Length);
            var b = BattleTests.Arena(5);
            for (int r = 0; r < 3; r++) b.AddBoon(id);
            Assert.Equal(3, b.Boons[id]);
            Tick(b, 1);
        }
    }

    [Fact]
    public void A_milestone_offers_to_deepen_the_blessing_held()
    {
        var b = BattleTests.Arena(6);
        b.AddBoon("stormborn");
        b.PendingBlessings.Add(4);
        bool seen = false;
        for (int k = 0; k < 30 && !seen; k++)
        {
            var offers = LevelUp.Draft(b, 3);
            var deeper = offers.FirstOrDefault(o => o.Id == "stormborn");
            if (deeper == null) continue;
            seen = true;
            Assert.Equal(2, deeper.To);
            Assert.StartsWith("Rank 2:", deeper.Text);
        }
        Assert.True(seen);
    }

    [Fact]
    public void Duelists_grace_widens_the_moment_and_fires_everything()
    {
        var b = BattleTests.Arena(7);
        b.AddBoon("duelists_grace");
        b.AddBoon("duelists_grace");
        b.Dash(1, 0);
        Assert.Equal(Abilities.Dash.Perfect * 1.5, b.Player.DodgeWindow, 3);
        var w = b.Weapons[0];
        w.Timer = 5;
        var wolf = b.SpawnEnemy("wolf", b.Player.X + 1, b.Player.Z)!;
        Tick(b, 1 / 60.0);
        b.HurtPlayer(10, School.Physical, "wolf", wolf, telegraphed: true);
        Assert.Equal(0, w.Timer, 3);
        Assert.True(b.Player.SureCritT > Abilities.Dash.Riposte);
    }

    [Fact]
    public void Cinderwake_leaves_fire_along_the_dash()
    {
        var b = BattleTests.Arena(8);
        b.AddBoon("cinderwake");
        b.Dash(1, 0);
        Tick(b, Abilities.Dash.Time + 0.02);
        Assert.True(b.Zones.Living().Count(z => z.Art == "cinder") >= 4);
    }

    [Fact]
    public void Iron_vow_comes_back_while_nothing_reaches_you()
    {
        var b = BattleTests.Arena(9);
        for (int r = 0; r < 3; r++) b.AddBoon("iron_vow");
        Tick(b, 4.2);
        Assert.Equal(b.MaxHp * 0.24, b.Player.Shield, 1);
        var r1 = b.SpawnEnemy("risen", b.Player.X + 1.5, b.Player.Z)!;
        Tick(b, 1 / 60.0);
        // It breaks, and throws back what is close.
        b.HurtPlayer(b.MaxHp, School.Physical, "risen", r1);
        Tick(b, 1 / 60.0);
        Assert.Equal(0, b.Player.Shield, 3);
        Assert.True(r1.Hp < r1.MaxHp);
        Tick(b, 4.2);
        Assert.True(b.Player.Shield > 0);
    }

    [Fact]
    public void Restless_hands_trade_an_art_for_a_dash()
    {
        var b = BattleTests.Arena(10);
        b.AddBoon("restless_hands");
        b.Player.DashCharges = 0;
        var r = b.SpawnEnemy("risen", b.Player.X + 2, b.Player.Z)!;
        Tick(b, 1 / 60.0);
        Assert.True(b.UseAbility(1, 0));
        Tick(b, 1 / 60.0);
        Assert.Equal(1, b.Player.DashCharges);
        Assert.True(b.Art.CdFull < Abilities.All[AbilityKind.ShieldBash].Cooldown);
    }

    [Fact]
    public void Stormborn_calls_lightning_on_what_is_near()
    {
        var b = BattleTests.Arena(11, ("oathblade", 1));
        b.RemoveWeapon("oathblade");
        b.AddBoon("stormborn");
        var r = b.SpawnEnemy("risen_warrior", b.Player.X + 4, b.Player.Z)!;
        r.AttackT = 99;
        Tick(b, 1.2);
        Assert.True(r.Hp < r.MaxHp);
    }

    [Fact]
    public void A_milestone_with_nothing_left_to_give_is_a_respite_not_an_empty_draft()
    {
        var b = BattleTests.Arena(8);
        foreach (var id in Boons.Order) if (Boons.All[id].Kind == BoonKind.Blessing && !Boons.IsGreat(id)) b.BannedCards.Add(id);
        b.PendingBlessings.Add(4);
        var offers = LevelUp.Draft(b, 3);
        Assert.NotEmpty(offers);
        Assert.All(offers, o => Assert.True(o.Blessing));
        LevelUp.Choose(b, offers[0]);
        Assert.Empty(b.PendingBlessings);
    }
}
