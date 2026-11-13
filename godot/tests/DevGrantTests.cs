using System.Linq;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M3) A dev grant on a campaign survivor whose taught build fills the six keys (Sim/DevGrants.cs): the union is
/// carried on two keys, the grip stays on the first.</summary>
public class DevGrantTests
{
    [Fact]
    public void A_union_granted_on_six_full_keys_takes_two_and_the_grip_stays()
    {
        var j = MapSim.Survivor("warden", 30, 2, 5);
        var b = j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7, worldTier: false);
        Assert.True(b.Campaign);
        var taught = TaughtBuilds.Of("warden")!;
        Assert.Equal(Weapons.MaxWeapons, b.SlotsUsed);
        var grip = b.Weapons.Single(w => w.Id == taught.Grip);
        Assert.Equal(0, grip.Slot);
        // (the bare grant is refused: no two keys free)
        Assert.Null(b.GrantUnion("bladestorm"));

        var said = DevGrants.Apply(b, null, "bladestorm", null);

        var u = Unions.Find("bladestorm")!;
        var storm = b.Weapons.Single(w => w.Id == u.Into);
        Assert.True(storm.Slot >= 0 && storm.Slot2 >= 0 && storm.Slot != storm.Slot2);
        Assert.Contains(said, l => l.StartsWith("grant-union: bladestorm on slots"));
        Assert.True(b.SlotsUsed <= Weapons.MaxWeapons);
        // The grip is still carried on the first key, or is the union's own part (then the union answers its key).
        var gripNow = b.Weapons.Find(w => w.Id == taught.Grip);
        if (taught.Grip == u.A || taught.Grip == u.B) Assert.True(storm.Slot == 0 || storm.Slot2 == 0);
        else { Assert.NotNull(gripNow); Assert.Equal(0, gripNow!.Slot); }
        // A second ask changes nothing more.
        int carried = b.Weapons.Count;
        Assert.Contains(DevGrants.Apply(b, null, "bladestorm", null), l => l.StartsWith("grant-union: bladestorm already carried on slots"));
        Assert.Equal(carried, b.Weapons.Count);
        Assert.Contains(DevGrants.Apply(b, "no_such_skill", "no_such_union", null), l => l == "grant: no_such_skill not added (no such skill)");
    }

    static Battle Fight(Journey j) => j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7, worldTier: false);

    /// <summary>(M3 lead 8) The game's --veteran L[:G] is the harness's `--level L`, gG survivor (Play/DevVeteran.cs: one
    /// dressing for both), and the old `--xp N` alone was not: the level with every point unspent and nothing worn (the clip's
    /// veteran fell on maps the sim's cleared).</summary>
    [Fact]
    public void The_games_veteran_is_the_harnesss_and_the_level_alone_is_not()
    {
        var sim = MapSim.Survivor("warden", 30, 2, 5);
        DevVeteran.Belt(sim.Ch);
        string simLine = DevVeteran.Line(Fight(sim), sim);

        var a = Callings.Archetype("warden");
        Journey Quick() => Journey.Begin(new CreationChoice
        {
            Name = "Wren", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 99);
        // The clip's old veteran: --xp to level 30 (bd-ranks: 100000000 was the old cap's; the cap is 75 now).
        var bare = Quick();
        Character.GainXp(bare.Ch, Enumerable.Range(1, 29).Sum(Character.XpForLevel));
        var bb = Fight(bare);
        Assert.Equal(30, bare.Ch.Level);
        Assert.True(bare.Ch.Points > 50, $"{bare.Ch.Points} points unspent");
        var sb = Fight(sim);
        Assert.True(bb.MaxHp < 0.6 * sb.MaxHp, $"life {bb.MaxHp:0} against the harness's {sb.MaxHp:0}");
        Assert.True(bb.Stats.Get(Stat.Damage) < 0.5 * sb.Stats.Get(Stat.Damage));
        Assert.NotEqual(simLine, DevVeteran.Line(bb, bare));

        // --veteran 30:2 (with or without the old --xp before it): the harness's, to the line.
        foreach (bool xp in new[] { false, true })
        {
            var game = Quick();
            if (xp) Character.GainXp(game.Ch, Enumerable.Range(1, 29).Sum(Character.XpForLevel));
            Assert.StartsWith("veteran: level 30, gear rarity 2", DevVeteran.Apply(game.Ch, "30:2", 5));
            Assert.Equal(simLine, DevVeteran.Line(Fight(game), game));
        }
    }

    /// <summary>(M3 lead 8) The grip under the union (ARPG.md 3.3): Bladestorm sits on Sunder's key, and out of a storm the
    /// plan's hands hold that key as the grip (PressHands.HalfGrip: what a clip's presses print as Sunder held): Sunder
    /// swings, lands and builds Resolve with no storm begun.</summary>
    [Fact]
    public void Under_the_union_the_plan_holds_Sunders_key_as_the_grip()
    {
        var j = MapSim.Survivor("warden", 30, 2, 5);
        var b = Fight(j);
        DevGrants.Apply(b, null, "bladestorm", null);
        var storm = b.Weapons.Single(w => w.Id == Unions.Find("bladestorm")!.Into);
        Assert.Equal(0, storm.Slot2);
        var hands = PressHands.Grip(3);
        var p = b.Player;
        var foe = b.SpawnEnemy("footpad", p.X + 1.6, p.Z);
        foe.Hp = foe.MaxHp = 1e7;
        double hp0 = foe.Hp, resolve0 = b.Resolve.Value;
        int held = 0, steps = 0;
        double seenAt = double.NaN;
        for (double t = 0; t < 4; t += 1 / 60.0)
        {
            foe.X = p.X + 1.6; foe.Z = p.Z;
            seenAt = b.Time;
            PressPlan.Run(b, hands);
            steps++;
            if (hands.HalfGrip == "sunder") held++;
            b.Tick(1 / 60.0, 0, 0);
            b.Events.Drain();
            Assert.False(storm.Channeling);
        }
        Assert.True(held > 0.9 * steps, $"Sunder's key held {held} of {steps} steps");
        Assert.True(foe.Hp < hp0, "Sunder never landed");
        Assert.True(b.Resolve.Value > resolve0, "the grip built no Resolve");
        // With nothing in reach the key is let go: by the hands' gap rule (GripGaps, Sim/PressPlan.cs). (sw2) Sunder ships
        // chained, so its key stays down through the chain's grace, counted from the last step a foe stood in its reach
        // (these hands have no lapse), and is up on the first step past it.
        double grace = GripGaps.Grace(Firing.HalfOf(storm));
        Assert.Equal(0.40, grace);
        int inGrace = 0;
        for (int k = 1; ; k++)
        {
            Assert.True(k < 60, "the key never came up");
            foe.X = p.X + 30; foe.Z = p.Z; foe.Vx = foe.Vz = 0;
            double gap = b.Time - seenAt;
            PressPlan.Run(b, hands);
            if (gap <= grace)
            {
                // inside the grace: the half's key is still held (the first such step is the step after the foe left)
                Assert.Equal("sunder", hands.HalfGrip);
                inGrace++;
            }
            else
            {
                // one step past the grace: let go
                Assert.InRange(gap, grace, grace + 1 / 60.0 + 1e-9);
                Assert.Null(hands.HalfGrip);
                break;
            }
            b.Tick(1 / 60.0, 0, 0);
            b.Events.Drain();
            Assert.False(storm.Channeling);
        }
        // (0.40 s of 1/60 s steps)
        Assert.Equal(24, inGrace);
        // and it stays up: a key that came up goes down again only at a foe
        b.Tick(1 / 60.0, 0, 0);
        PressPlan.Run(b, hands);
        Assert.Null(hands.HalfGrip);
    }
}
