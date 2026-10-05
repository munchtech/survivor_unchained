using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
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

    [Fact]
    public void Every_great_blessing_has_a_role_and_every_path_a_ward()
    {
        foreach (var id in Boons.Great) Assert.True(Boons.GreatRoles.ContainsKey(id), $"{id} has no role");
        foreach (var p in Paths.All)
        {
            Assert.Contains(p.Great, id => Boons.GreatRoles[id] == Boons.GreatRole.Ward);
            Assert.InRange(p.Great.Length, 3, 7);
        }
    }

    [Fact]
    public void From_the_ashes_lifts_you_once_burning_and_the_dawn_takes_it()
    {
        var b = BattleTests.Arena(8);
        b.AddBoon("from_the_ashes");
        Assert.Equal(1, b.Player.Ashes);
        var wolf = b.SpawnEnemy("wolf", b.Player.X + 2, b.Player.Z, new Battle.SpawnOpts { Elite = true, Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
        Tick(b, 1 / 60.0);
        b.HurtPlayer(b.MaxHp * 5, School.Physical, "wolf", wolf, telegraphed: true);
        Assert.True(b.Player.Alive);
        Assert.Equal(b.MaxHp * 0.5, b.Player.Hp, 1);
        Assert.True(wolf.Status.Has(StatusKind.Burn));
        Assert.Equal(0, b.Player.Ashes);
        // Once a night at every rank (the owner: rising twice was too generous); the third rank
        // owes no second rising.
        b.AddBoon("from_the_ashes");
        Assert.Equal(0, b.Player.Ashes);
        b.AddBoon("from_the_ashes");
        Assert.Equal(0, b.Player.Ashes);
        b.Douse([]);
        Assert.Equal(0, b.Player.Ashes);
    }

    /// <summary>The owner: getting up and fighting on is rare, "or it is a balancing nightmare". Carried
    /// as an art and drafted as a blessing, it still gets her up once a fight, and a blessing taken
    /// after she has got up does not get her up again.</summary>
    [Fact]
    public void One_rise_a_fight_however_many_ways_she_carries_it()
    {
        var b = BattleTests.Arena(10);
        b.Player.Revives = 1;
        b.AddBoon("from_the_ashes");
        b.HurtPlayer(b.MaxHp * 5, School.Physical, "wolf", null, telegraphed: true);
        Assert.True(b.Player.Alive);
        Assert.Equal(1, b.Player.Rose);
        Assert.Equal(0, b.Player.Revives + b.Player.Ashes);
        b.Player.Iframes = 0;
        b.HurtPlayer(b.MaxHp * 5, School.Physical, "wolf", null, telegraphed: true);
        Assert.False(b.Player.Alive);

        var c = BattleTests.Arena(11);
        c.Player.Rose = 1;
        c.AddBoon("from_the_ashes");
        Assert.Equal(0, c.Player.Ashes);
    }

    [Fact]
    public void Cold_Then_Not_held_in_the_arts_place_is_a_rise_in_the_kit()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 5);
        Assert.Equal(0, Character.Kit(j.Ch).Revives);
        j.Ch.Ability = "cold_then_not";
        Assert.Equal(1, Character.Kit(j.Ch).Revives);
    }

    [Fact]
    public void From_the_ashes_whole_lifts_you_whole()
    {
        var b = BattleTests.Arena(9);
        b.AddBoon("from_the_ashes");
        b.AddBoon("from_the_ashes");
        Assert.Equal(1, b.Player.Ashes);
        b.HurtPlayer(b.MaxHp * 5, School.Physical, "wolf", null, telegraphed: true);
        Assert.True(b.Player.Alive);
        Assert.Equal(b.MaxHp, b.Player.Hp, 1);
    }

    [Fact]
    public void Grounding_turns_part_of_a_blow_into_lightning()
    {
        double Taken(bool grounded)
        {
            var b = BattleTests.Arena(9);
            if (grounded) b.AddBoon("grounding");
            var wolf = b.SpawnEnemy("wolf", b.Player.X + 2, b.Player.Z, new Battle.SpawnOpts { Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
            Tick(b, 1 / 60.0);
            double before = b.Player.Hp;
            b.HurtPlayer(40, School.Physical, "wolf", wolf, telegraphed: true);
            return before - b.Player.Hp;
        }
        Assert.Equal(Taken(false) * 0.8, Taken(true), 1);
        var g = BattleTests.Arena(10);
        g.AddBoon("grounding");
        var near = g.SpawnEnemy("wolf", g.Player.X + 3, g.Player.Z, new Battle.SpawnOpts { Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
        Tick(g, 1 / 60.0);
        double hp = near.Hp;
        g.HurtPlayer(40, School.Physical, "wolf", near, telegraphed: true);
        Tick(g, 0.2);
        Assert.True(near.Hp < hp || !near.Alive, "the lightning found nothing");
    }

    [Fact]
    public void Rootbind_holds_and_opens_the_toughest_near_you()
    {
        var b = BattleTests.Arena(11);
        b.RemoveWeapon("oathblade");
        var pup = b.SpawnEnemy("wolf", b.Player.X + 3, b.Player.Z, new Battle.SpawnOpts { Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
        var alpha = b.SpawnEnemy("wolf", b.Player.X + 6, b.Player.Z, new Battle.SpawnOpts { Elite = true, Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
        b.AddBoon("rootbind");
        Tick(b, 0.2);
        Assert.True(alpha.Status.Has(StatusKind.Stun));
        Assert.True(alpha.Status.Has(StatusKind.Mark));
        Assert.False(pup.Status.Has(StatusKind.Stun));
    }

    [Fact]
    public void Go_for_the_throat_sends_the_pack_at_the_champion()
    {
        int TargetOf(bool throat)
        {
            var b = BattleTests.Arena(12);
            b.RemoveWeapon("oathblade");
            if (throat) b.AddBoon("go_for_the_throat");
            b.AddBoon("spirit_companion");
            var pup = b.SpawnEnemy("wolf", b.Player.X + 2.5, b.Player.Z, new Battle.SpawnOpts { Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
            var alpha = b.SpawnEnemy("wolf", b.Player.X - 7, b.Player.Z, new Battle.SpawnOpts { Elite = true, Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
            Tick(b, 1.5);
            var ally = b.Enemies.Items.First(e => e.Alive && e.Disposition == Disposition.Ally);
            return ally.Target == alpha.Id ? 1 : ally.Target == pup.Id ? 0 : -1;
        }
        Assert.Equal(0, TargetOf(false));
        Assert.Equal(1, TargetOf(true));
    }

    [Fact]
    public void What_burns_strikes_an_emberblood_weaker()
    {
        double Taken(int ranks, bool burning)
        {
            var b = BattleTests.Arena(13);
            for (int r = 0; r < ranks; r++) b.AddBoon("emberblood");
            var wolf = b.SpawnEnemy("wolf", b.Player.X + 2, b.Player.Z, new Battle.SpawnOpts { Elite = true, Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
            Tick(b, 1 / 60.0);
            if (burning) b.ApplyStatus(wolf, new StatusPayload(StatusKind.Burn, 1, 1, 5), 10);
            double before = b.Player.Hp;
            b.HurtPlayer(40, School.Physical, "wolf", wolf, telegraphed: true);
            return before - b.Player.Hp;
        }
        Assert.Equal(Taken(0, true), Taken(5, false), 1);
        Assert.Equal(Taken(0, true) * 0.7, Taken(5, true), 1);
    }

    [Fact]
    public void Watch_mail_counts_and_turns_every_tenth_blow()
    {
        var b = BattleTests.Arena(14);
        b.AddBoon("ironhide");
        int turned = 0;
        for (int i = 0; i < 30; i++)
        {
            b.Player.Iframes = 0;
            b.Player.Hp = b.MaxHp;
            if (b.HurtPlayer(5, School.Physical, "test", null) == 0) turned++;
        }
        Assert.Equal(3, turned);
    }

    [Fact]
    public void Bitterroot_draws_burning_and_poison_out_twice_as_fast()
    {
        double Left(bool root)
        {
            var b = BattleTests.Arena(15);
            if (root) b.AddBoon("recovery");
            b.Player.BurnT = 2; b.Player.BurnDps = 0;
            Tick(b, 0.5);
            return b.Player.BurnT;
        }
        Assert.Equal(1.5, Left(false), 1);
        Assert.Equal(1.0, Left(true), 1);
    }

    [Fact]
    public void A_callings_own_great_is_offered_to_it_alone()
    {
        var own = Boons.Great.Where(id => Boons.All[id].Calling != null).ToDictionary(id => id, id => Boons.All[id].Calling!);
        Assert.Equal(4, own.Count);
        Assert.Equal(new[] { "arcanist", "reaver", "stalker", "warden" }, own.Values.OrderBy(x => x));
        foreach (var calling in own.Values)
        {
            bool seen = false;
            for (uint seed = 1; seed <= 120; seed++)
            {
                var b = BattleTests.Arena(seed);
                b.Calling = calling;
                b.GreatOwed = 1;
                var hand = LevelUp.Draft(b);
                Assert.DoesNotContain(hand, o => own.TryGetValue(o.Id, out var c) && c != calling);
                seen |= hand.Any(o => own.TryGetValue(o.Id, out var c) && c == calling);
            }
            Assert.True(seen, $"{calling} never saw its own");
        }
        // Once a night: at Dusk or, failing that, at Midnight.
        for (uint seed = 1; seed <= 60; seed++)
        {
            var b = BattleTests.Arena(seed);
            b.Calling = "reaver";
            b.GreatOwed = 1;
            var dusk = LevelUp.Draft(b);
            bool atDusk = dusk.Any(o => o.Id == "blood_up");
            LevelUp.Choose(b, dusk.First(o => o.Id != "blood_up"));
            b.GreatOwed = 1;
            var midnight = LevelUp.Draft(b);
            Assert.True(atDusk || midnight.Any(o => o.Id == "blood_up"), $"seed {seed}");
        }
    }

    [Fact]
    public void The_hunters_blind_strikes_true_on_the_unhurt()
    {
        var b = BattleTests.Arena(16);
        b.RemoveWeapon("oathblade");
        b.AddBoon("hunters_blind");
        b.AddBoon("hunters_blind");
        b.Stats.Add(new StatMod(Stat.CritChance, ModKind.Flat, -b.Stats.Get(Stat.CritChance), "test"));
        var wolf = b.SpawnEnemy("wolf", b.Player.X + 3, b.Player.Z, new Battle.SpawnOpts { Elite = true, Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;
        Tick(b, 1 / 60.0);
        double first = b.HitEnemy(wolf, 10, School.Physical, [Tag.Physical]);
        double second = b.HitEnemy(wolf, 10, School.Physical, [Tag.Physical]);
        Assert.True(first > second * 1.2, $"{first} against {second}");
    }

    [Fact]
    public void Holding_the_crossing_hardens_you_while_you_stand()
    {
        var b = BattleTests.Arena(17);
        double before = b.Stats.Get(Stat.Armor);
        b.AddBoon("hold_the_crossing");
        Tick(b, 0.5);
        Assert.Equal(before + 6, b.Stats.Get(Stat.Armor), 3);
        Tick(b, 0.5, 1, 0);
        Assert.Equal(before, b.Stats.Get(Stat.Armor), 3);
    }
}
