using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The Red Hand's Toll takes by damage (bd-storm, 13 Nov): the skill that has dealt the most damage
/// in this fight, not her top-rank skill (taking Sunder, her first and highest key, left a Bladestorm build
/// clearing worse than none). Ties go to the higher rank, then the lower key.</summary>
[Collection("Balance")]
public class RedHandTollTests
{
    sealed record Fight(Battle B, ArenaRun Zone, HeadlessHost Host);

    /// <summary>A Kerchiefs arena at the edge of the half hour, kept alive; `before` runs on the battle before
    /// the boss comes (damage dealt then is not this fight's).</summary>
    static Fight Kerchiefs(int seed, Action<Battle>? before = null)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)seed);
        var spec = new ArenaSpec { Id = "table:test", Name = "Test", Seed = seed, Tier = 1, People = "kerchiefs" };
        Arenas.Begin(j.World, spec);
        var map = MapGen.Generate(spec.Map);
        var host = new HeadlessHost(j, seed);
        var zone = new ArenaRun(host, map, spec);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)seed, arena: true);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        b.GreatOwed = 0;
        before?.Invoke(b);
        b.Time = 30 * 60 - 0.05;
        var f = new Fight(b, zone, host);
        Step(f, 0.2);
        Assert.IsType<RedHand>(zone.BossScript);
        return f;
    }

    static void Step(Fight f, double seconds, Action<List<CombatEvent>>? seen = null)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            f.Zone.Step(1 / 60.0);
            f.Zone.Frame(1 / 60.0);
            f.B.Tick(1 / 60.0, 0, 0);
            var evs = f.B.Events.Drain();
            seen?.Invoke(evs);
            f.Host.Pass(1 / 60.0);
            f.B.PendingLevels = 0; f.B.PendingBlessings.Clear(); f.B.GreatOwed = 0;
            f.B.Player.Hp = f.B.MaxHp;
            if (f.Zone.Won) return;
        }
    }

    /// <summary>Her kit as the storm build carries it: Sunder at the top rank, two others below it.</summary>
    static void Kit(Battle b)
    {
        foreach (var (id, rank) in new[] { ("sunder", 6), ("heroic_leap", 3), ("bladestorm", 2) })
        {
            var w = b.Weapons.FirstOrDefault(x => x.Id == id) ?? b.AddWeapon(id, rank);
            Assert.NotNull(w);
            w!.Rank = rank;
        }
    }

    static WeaponInst W(Battle b, string id) => b.Weapons.First(w => w.Id == id);

    /// <summary>Two seeded fights where rank and damage disagree: the Toll, landing for real (she stands in its
    /// ring), takes the skill that has dealt the most this fight, never Sunder for its rank.</summary>
    [Theory]
    [InlineData(3, "bladestorm")]
    [InlineData(7, "heroic_leap")]
    public void The_toll_takes_the_skill_that_has_dealt_the_most_this_fight(int seed, string top)
    {
        var f = Kerchiefs(seed, Kit);
        var rh = (RedHand)f.Zone.BossScript!;
        // This fight's damage: the low-rank skill far ahead of the rest (whatever the others deal on their own).
        W(f.B, top).DamageDealt += 1e6;
        Assert.Same(W(f.B, top), rh.TollPick(f.B.Weapons));
        var (taken, missed) = Tolls(f, 40, slip: false);
        // The Toll's own blow gives her the hurt grace before the theft is judged: that is no slip.
        Assert.True(taken.Count > 0, $"the toll never took anything ({missed} missed)");
        Assert.Equal(W(f.B, top).Def.Name, taken[0]);
        Assert.NotEqual(W(f.B, "sunder").Def.Name, taken[0]);
    }

    /// <summary>A dash's or a leap's grace as the ring lands slips the Toll: nothing is taken.</summary>
    [Fact]
    public void Grace_as_the_ring_lands_slips_the_toll()
    {
        var f = Kerchiefs(3, Kit);
        var (taken, missed) = Tolls(f, 40, slip: true);
        Assert.Empty(taken);
        Assert.True(missed > 0);
    }

    /// <summary>The fight stepped with her standing still (or in a dash's grace, `slip`): what the Toll took, and
    /// how often it missed.</summary>
    static (List<string> Taken, int Missed) Tolls(Fight f, double seconds, bool slip)
    {
        var taken = new List<string>();
        int missed = 0;
        Step(f, seconds, evs =>
        {
            foreach (var ev in evs)
            {
                if (ev is Ev.Announce an && an.Title.EndsWith(" is taken")) taken.Add(an.Title[..^" is taken".Length]);
                if (ev is Ev.Bark { Text: "The toll missed." }) missed++;
            }
            f.B.Player.Iframes = slip ? 1 : 0;
        });
        return (taken, missed);
    }

    /// <summary>Damage dealt before the fight is not this fight's: a skill that carried the night in does not
    /// outweigh the one carrying the fight.</summary>
    [Fact]
    public void Damage_before_the_fight_does_not_count()
    {
        var f = Kerchiefs(5, b => { Kit(b); W(b, "sunder").DamageDealt += 1e7; });
        var rh = (RedHand)f.Zone.BossScript!;
        double sunderNow = rh.DealtThisFight(W(f.B, "sunder"));
        Assert.True(sunderNow < 1e6, $"sunder's pre-fight damage counted: {sunderNow}");
        W(f.B, "heroic_leap").DamageDealt += 1e6 + sunderNow;
        Assert.Same(W(f.B, "heroic_leap"), rh.TollPick(f.B.Weapons));
    }

    /// <summary>Ties (the fight's first seconds, nothing dealt yet) break the same way every time: the higher
    /// rank, then the lower key; a skill already taken (disabled) is passed over.</summary>
    [Fact]
    public void Ties_break_by_rank_then_key()
    {
        var f = Kerchiefs(3, Kit);
        var rh = (RedHand)f.Zone.BossScript!;
        foreach (var w in f.B.Weapons) w.DamageDealt += 1e6 - rh.DealtThisFight(w);
        Assert.All(f.B.Weapons, w => Assert.Equal(1e6, rh.DealtThisFight(w), 6));
        Assert.Same(W(f.B, "sunder"), rh.TollPick(f.B.Weapons));
        W(f.B, "heroic_leap").Rank = 6;
        var first = W(f.B, "sunder").Slot < W(f.B, "heroic_leap").Slot ? "sunder" : "heroic_leap";
        Assert.Same(W(f.B, first), rh.TollPick(f.B.Weapons));
        Assert.Same(W(f.B, first), rh.TollPick(f.B.Weapons.AsEnumerable().Reverse()));
        W(f.B, first).DisabledT = 5;
        Assert.Same(W(f.B, first == "sunder" ? "heroic_leap" : "sunder"), rh.TollPick(f.B.Weapons));
    }
}
