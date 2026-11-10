using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M6, TUTORIAL_COPY.md A3/A3b, A13/A13b) The ember the dead spill by day (experience stones that fly to her
/// and pay as they land) and the day's new keys (Heroic Leap at the ring, Shield Charge at the next pack).</summary>
public class PrologueDayKeysTests
{
    sealed record Setup(Journey J, FakeHost Host, Prologue Zone, Battle B);

    static Setup Make(bool dayStart = false)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
        var meta = ZoneMeta.Load("lowford");
        var host = new FakeHost(j, meta);
        var zone = new Prologue(host, meta) { DayStart = dayStart };
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 5, ember: zone.Ember);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        return new Setup(j, host, zone, b);
    }

    static void Run(Setup s, double seconds)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            s.B.Player.Hp = s.B.MaxHp;
            s.Zone.Step(1 / 60.0);
            s.B.Tick(1 / 60.0, 0, 0);
            s.B.Events.Drain();
            s.Zone.Frame(1 / 60.0);
        }
    }

    /// <summary>A scripted fight: twelve wolves (two of them champions) killed at 3 to 8 m from her.</summary>
    static void Fight(Setup s)
    {
        for (int i = 0; i < 12; i++)
        {
            var e = s.B.SpawnEnemy("wolf", s.B.Player.X + 3 + i % 6, s.B.Player.Z + (i % 2 == 0 ? 2 : -2), new Battle.SpawnOpts { Level = 1 + i / 4, Elite = i % 6 == 5 })!;
            s.B.KillEnemy(e, true, null);
            s.J.Killed(e, true);
        }
    }

    static int XpStones(Battle b) => b.Pickups.Living().Count(k => k.Kind == PickupKind.Ember && k.Ref == Battle.XpStoneRef);

    [Fact]
    public void Stones_pay_exactly_what_the_kills_paid_straight()
    {
        // Before: the kills paid at once (no stones).
        var straight = Make();
        Assert.False(straight.B.EmberOn);
        straight.B.PayXp = null;
        double xp0 = straight.J.Ch.Xp; int lv0 = straight.J.Ch.Level;
        Fight(straight);
        Assert.Equal(0, XpStones(straight.B));

        // Now: stones, paid as they land.
        var stones = Make();
        stones.Host.TaughtIds.Add("ember_ground");
        Fight(stones);
        Assert.True(XpStones(stones.B) > 0);
        Assert.Equal((xp0, lv0), (stones.J.Ch.Xp, stones.J.Ch.Level));   // (nothing paid at the kill)
        Run(stones, 0.3);
        Assert.True(XpStones(stones.B) > 0);   // (resting: XpStoneRest)
        Run(stones, 3);
        Assert.Equal(0, XpStones(stones.B));
        Assert.Equal((straight.J.Ch.Level, straight.J.Ch.Xp), (stones.J.Ch.Level, stones.J.Ch.Xp), new XpEq());
        Assert.True(straight.J.Ch.Xp > xp0 || straight.J.Ch.Level > lv0);
    }

    sealed class XpEq : System.Collections.Generic.IEqualityComparer<(int, double)>
    {
        public bool Equals((int, double) a, (int, double) b) => a.Item1 == b.Item1 && System.Math.Abs(a.Item2 - b.Item2) < 1e-6;
        public int GetHashCode((int, double) o) => o.Item1;
    }

    [Fact]
    public void The_journeys_first_stone_is_held_until_A3_closes()
    {
        var s = Make();
        Run(s, 0.05);
        var e = s.B.SpawnEnemy("wolf", s.B.Player.X + 3, s.B.Player.Z, new Battle.SpawnOpts { Level = 1 })!;
        s.B.KillEnemy(e, true, null);
        s.J.Killed(e, true);
        var held = s.B.HeldStone;
        Assert.NotNull(held);
        double xp0 = s.J.Ch.Xp;
        Run(s, 2);
        Assert.True(held!.Alive && s.B.HeldStone == held && !held.Pulled);
        Assert.Equal(xp0, s.J.Ch.Xp);
        // A3 closes: it flies to her and pays; A3b follows on the first stone landed.
        s.Host.TaughtIds.Add("ember_ground");
        Run(s, 2);
        Assert.Null(s.B.HeldStone);
        Assert.True(s.J.Ch.Xp > xp0 || s.J.Ch.Level > 1);
        Assert.Contains(s.Host.Asked, c => c.Id == "ember_ring");
        // A second kill's stones are never held.
        var e2 = s.B.SpawnEnemy("wolf", s.B.Player.X + 3, s.B.Player.Z, new Battle.SpawnOpts { Level = 1 })!;
        s.B.KillEnemy(e2, true, null);
        s.J.Killed(e2, true);
        Assert.Null(s.B.HeldStone);
    }

    [Fact]
    public void A3_says_it_comes_to_you()
    {
        var s = Make();
        var lone = Play.Zones.Encounters.For("lowford")!.Get("n_lone")!;
        for (double t = 0; t < 4; t += 0.1) { s.B.Player.X = lone.X; s.B.Player.Z = lone.Z + 30; Run(s, 0.1); }   // (into the Rising)
        var e = s.B.SpawnEnemy("wolf", s.B.Player.X + 3, s.B.Player.Z, new Battle.SpawnOpts { Level = 1 })!;
        s.B.KillEnemy(e, true, null);
        s.J.Killed(e, true);
        Run(s, 1);
        var c = s.Host.Asked.First(x => x.Id == "ember_ground");
        Assert.Equal(("Ember", "The light the dead carry. It comes to you, and it makes you stronger.", CalloutKind.Freeze), (c.Title, c.Line, c.Kind));
        Assert.NotEmpty(c.Target.World!());
    }

    [Fact]
    public void A_zone_end_pays_the_stones_still_lying_or_flying()
    {
        var straight = Make();
        straight.B.PayXp = null;
        Fight(straight);
        var s = Make();
        Run(s, 0.05);
        Fight(s);
        Assert.NotNull(s.B.HeldStone);
        Assert.True(XpStones(s.B) > 0);
        s.J.Capture(s.B);
        Assert.Equal(0, XpStones(s.B));
        Assert.Equal((straight.J.Ch.Level, straight.J.Ch.Xp), (s.J.Ch.Level, s.J.Ch.Xp), new XpEq());
    }

    [Fact]
    public void Arena_runs_spill_no_experience_stones()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice { Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 42);
        var meta = ZoneMeta.Load("lowford");
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, 0, 0, 0, 5, arena: true);
        Assert.Null(b.PayXp);
    }

    /// <summary>The day's ring sprung round her with a skill put on a seat (a fake seat where skills-p7 has not granted it).</summary>
    static Setup Ringed(string? seat, int slot)
    {
        var s = Make(dayStart: true);
        Run(s, 0.1);
        if (seat != null)
        {
            var w = s.B.AddWeapon(seat)!;
            w.Slot = slot;
        }
        return s;
    }

    [Fact]
    public void A13_leap_asks_at_the_closed_ring_on_its_real_seat_and_day_gap_only_without_it()
    {
        foreach (var (seat, slot) in new (string?, int)[] { ("heroic_leap", 2), ("heroic_leap", 3), (null, -1) })
        {
            var s = Ringed(seat, slot);
            var rb = s.Zone.Day!.Of("ring").First();
            for (int i = 0; i < 400 && !s.Host.Asked.Any(c => c.Id is "leap" or "day_gap"); i++)
            {
                if (s.Zone.Day.RingAt < 0) { s.B.Player.X = rb.X; s.B.Player.Z = rb.Z - 0.5; }
                Run(s, 0.05);
            }
            Assert.True(s.Zone.Day.RingAt >= 0);
            Assert.DoesNotContain(s.Host.Asked, c => c.Id == "day_flare");
            if (seat == null) { Assert.Contains(s.Host.Asked, c => c.Id == "day_gap"); Assert.DoesNotContain(s.Host.Asked, c => c.Id == "leap"); continue; }
            var c = s.Host.Asked.First(c => c.Id == "leap");
            string act = $"Skill{slot + 1}";
            Assert.Equal("seat:" + act, c.Target.Hud);
            Assert.Equal(act.ToLowerInvariant(), c.Answer);
            Assert.EndsWith(": leap where you aim. Over them and out of the ring.", c.Line);
            Assert.DoesNotContain(s.Host.Asked, x => x.Id == "day_gap");
            // The point lies outside the ring the wolves stand on.
            var ring = s.Zone.Day!.Standing("wolves");
            var pt = Assert.Single(c.Target.World!());
            double cx = ring.Average(e => e.X), cz = ring.Average(e => e.Z), r = ring.Max(e => System.Math.Sqrt((e.X - cx) * (e.X - cx) + (e.Z - cz) * (e.Z - cz)));
            Assert.True(System.Math.Sqrt((pt.X - cx) * (pt.X - cx) + (pt.Z - cz) * (pt.Z - cz)) > r);
        }
    }

    [Fact]
    public void A13b_charge_asks_with_the_next_pack_within_10_m_on_its_real_seat()
    {
        foreach (var slot in new[] { 3, 2 })
        {
            var s = Ringed("shield_charge", slot);
            var boars = Play.Zones.Encounters.For("lowford")!.Get("boars")!;
            s.B.Player.X = boars.X; s.B.Player.Z = boars.Z + 30;
            Run(s, 0.5);
            Assert.DoesNotContain(s.Host.Asked, c => c.Id == "charge");
            for (int i = 0; i < 300 && !s.Host.Asked.Any(c => c.Id == "charge"); i++)
            {
                s.B.Player.X = boars.X; s.B.Player.Z = boars.Z + 8;
                Run(s, 0.05);
            }
            var c = s.Host.Asked.First(c => c.Id == "charge");
            string act = $"Skill{slot + 1}";
            Assert.Equal(("Shield Charge", "seat:" + act, act.ToLowerInvariant()), (c.Title, c.Target.Hud, c.Answer));
            Assert.EndsWith(": charge into the pack. The first one you hit is stunned.", c.Line);
            Assert.NotEmpty(c.Target.World!());
        }
    }

    [Fact]
    public void Without_the_skills_on_a_seat_the_rows_stay_inert()
    {
        var s = Ringed(null, -1);
        var boars = Play.Zones.Encounters.For("lowford")!.Get("boars")!;
        for (int i = 0; i < 100; i++) { s.B.Player.X = boars.X; s.B.Player.Z = boars.Z + 8; Run(s, 0.05); }
        Assert.DoesNotContain(s.Host.Asked, c => c.Id is "charge" or "leap");
    }
}
