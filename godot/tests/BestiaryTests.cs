using System.Linq;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The bestiary's measured problems, fixed (docs/bestiary/IMPLEMENTATION.md
/// section 1; docs/SKILLS_DESIGN.md, "Enemies and bosses").</summary>
public class BestiaryTests
{
    static void Tick(Battle b, double seconds)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0) { b.Tick(1 / 60.0, 0, 0); b.Events.Drain(); }
    }

    static Enemy Spawn(Battle b, string def, double dx, bool elite = false) =>
        b.SpawnEnemy(def, b.Player.X + dx, b.Player.Z, new Battle.SpawnOpts { Elite = elite, Style = SpawnStyle.Walk, Disposition = Disposition.Hostile })!;

    [Fact]
    public void More_cold_does_not_keep_the_frozen_frozen_and_the_thawed_cannot_refreeze_at_once()
    {
        var b = BattleTests.Arena(21);
        b.RemoveWeapon("oathblade");
        var wolf = Spawn(b, "wolf", 30);
        wolf.Speed = 0;
        var chill = new StatusPayload(StatusKind.Chill, 1, 2, 3);
        bool thawed = false, refrozeInWindow = false;
        double thawAt = -1;
        for (double t = 0; t < 8; t += 0.2)
        {
            b.ApplyStatus(wolf, chill, 10);
            Tick(b, 0.2);
            bool frozen = wolf.Status.Has(StatusKind.Frozen);
            if (!frozen && thawAt < 0 && t > 0.5) { thawed = true; thawAt = t; }
            if (thawAt >= 0 && frozen && t - thawAt < 2.9) refrozeInWindow = true;
        }
        Assert.True(thawed, "chilled twice a second, it stayed frozen");
        Assert.False(refrozeInWindow);
    }

    [Fact]
    public void Poison_on_the_survivor_says_so_and_names_the_death()
    {
        var b = BattleTests.Arena(22);
        b.Player.PoisonT = 3;
        b.Player.PoisonDps = 6;
        bool said = false;
        for (double t = 0; t < 1.2; t += 1 / 60.0)
        {
            b.Tick(1 / 60.0, 0, 0);
            said |= b.Events.Drain().OfType<Ev.PlayerHit>().Any(h => h.Dot && h.Source == "poison" && h.Amount > 0);
        }
        Assert.True(said);
        b.Player.Hp = 1;
        b.Player.PoisonT = 3;
        b.Player.PoisonDps = 50;
        string? killer = null;
        for (double t = 0; t < 1 && killer == null; t += 1 / 60.0)
        {
            b.Tick(1 / 60.0, 0, 0);
            killer = b.Events.Drain().OfType<Ev.PlayerDeath>().FirstOrDefault()?.Killer;
        }
        Assert.Equal("poison", killer);
        Assert.Equal("poison", b.Player.FellTo);
    }

    [Fact]
    public void A_champions_guard_holds_back_at_most_three_fifths()
    {
        double Through(bool elite)
        {
            var b = BattleTests.Arena(23);
            var brute = Spawn(b, "bruiser", 4, elite);
            brute.Facing = System.Math.Atan2(b.Player.Z - brute.Z, b.Player.X - brute.X);
            double before = brute.Hp;
            b.HitEnemy(brute, 100, School.Physical, [Tag.Projectile], new HitOpts { Projectile = true, FromX = 1, FromZ = 0, NoCrit = true });
            return before - brute.Hp;
        }
        // A plain bruiser's guard takes 80%; a champion's at most 60%.
        Assert.True(Through(true) > Through(false) * 1.8, $"{Through(true)} against {Through(false)}");
    }

    [Fact]
    public void Champions_are_not_fooled_by_a_reflection()
    {
        var b = BattleTests.Arena(24);
        b.RemoveWeapon("oathblade");
        var wolf = Spawn(b, "wolf", 9);
        var alpha = Spawn(b, "wolf", -9, elite: true);
        var mirror = b.SpawnEnemy("mirror", b.Player.X, b.Player.Z + 3, new Battle.SpawnOpts { Disposition = Disposition.Ally, Faction = Faction.Ally })!;
        mirror.Decoy = true;
        mirror.MaxHp = mirror.Hp = 1e6;
        b.Decoys.Add(mirror);
        Tick(b, 1.2);
        Assert.Equal(mirror.Id, wolf.Target);
        Assert.Equal(-1, alpha.Target);
    }

    [Fact]
    public void The_raised_carry_no_ember()
    {
        var b = BattleTests.Arena(25);
        b.EmberOn = true;
        var risen = Spawn(b, "risen", 40);
        risen.Raised = true;
        int stones = b.Pickups.Items.Count(k => k.Alive && k.Kind == PickupKind.Ember);
        b.KillEnemy(risen, true, null);
        Assert.Equal(stones, b.Pickups.Items.Count(k => k.Alive && k.Kind == PickupKind.Ember));
        var plain = Spawn(b, "risen", 40);
        b.KillEnemy(plain, true, null);
        Assert.True(b.Pickups.Items.Count(k => k.Alive && k.Kind == PickupKind.Ember) > stones);
    }

    [Fact]
    public void The_oaths_pay_by_how_they_play_and_the_lamplings_send_a_digger()
    {
        Assert.Equal(1.6, MapOffers.Oath("blight").Gear);
        Assert.Equal(1.3, MapOffers.Oath("champions").Gear);
        Assert.Equal("lampling", MapOffers.People("lamplings").Champion);
    }
}
