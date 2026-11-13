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
    public void A_union_granted_on_four_full_keys_takes_two_and_the_grip_stays()
    {
        var j = MapSim.Survivor("warden", 30, 2, 5);
        var b = j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 7, worldTier: false);
        Assert.True(b.Campaign);
        var taught = TaughtBuilds.Of("warden")!;
        Assert.Equal(b.KeyCount, b.SlotsUsed); // (bd-keys) her four keys full
        var grip = b.Weapons.Single(w => w.Id == taught.Grip);
        Assert.Equal(0, grip.Slot);
        // (the bare grant is refused: no two keys free)
        Assert.Null(b.GrantUnion("butchers_wheel"));

        var said = DevGrants.Apply(b, null, "butchers_wheel", null);

        var u = Unions.Find("butchers_wheel")!;
        var storm = b.Weapons.Single(w => w.Id == u.Into);
        Assert.True(storm.Slot >= 0 && storm.Slot2 >= 0 && storm.Slot != storm.Slot2);
        Assert.Contains(said, l => l.StartsWith("grant-union: butchers_wheel on slots"));
        Assert.True(b.SlotsUsed <= b.KeyCount);
        // The grip is still carried on the first key, or is the union's own part (then the union answers its key).
        var gripNow = b.Weapons.Find(w => w.Id == taught.Grip);
        if (taught.Grip == u.A || taught.Grip == u.B) Assert.True(storm.Slot == 0 || storm.Slot2 == 0);
        else { Assert.NotNull(gripNow); Assert.Equal(0, gripNow!.Slot); }
        // A second ask changes nothing more.
        int carried = b.Weapons.Count;
        Assert.Contains(DevGrants.Apply(b, null, "butchers_wheel", null), l => l.StartsWith("grant-union: butchers_wheel already carried on slots"));
        Assert.Equal(carried, b.Weapons.Count);
        Assert.Contains(DevGrants.Apply(b, "no_such_skill", "no_such_union", null), l => l == "grant: no_such_skill not added (no such skill)");
    }

    /// <summary>(13 Nov 2026) Bladestorm is no union: the old `--grant-union bladestorm` line grants the skill at full rank
    /// into a free key and says so, and the grip stays on key 1.</summary>
    [Fact]
    public void Grant_union_bladestorm_falls_back_to_granting_the_skill()
    {
        var j = MapSim.Survivor("warden", 30, 2, 5);
        var b = Fight(j);
        var storm = b.Weapons.Single(w => w.Id == "bladestorm"); // (the taught build carries it in key 3)
        Assert.Equal(-1, storm.Slot2);
        storm.Rank = 1;
        var said = DevGrants.Apply(b, null, "bladestorm", null);
        Assert.Contains(said, l => l.StartsWith("grant-union: bladestorm is no union now"));
        Assert.Equal(Weapons.MaxRank, storm.Rank);
        Assert.Equal(0, b.Weapons.Single(w => w.Id == TaughtBuilds.Of("warden")!.Grip).Slot);
        // Not carried: it takes a free key, at full rank.
        var c = BattleTests.Arena(9, ("sunder", 4));
        var said2 = DevGrants.Apply(c, null, "bladestorm", null);
        var w = c.Weapons.Single(x => x.Id == "bladestorm");
        Assert.Equal(Weapons.MaxRank, w.Rank);
        Assert.Contains(said2, l => l.StartsWith("grant-union: bladestorm is no union now"));
        Assert.Contains(said2, l => l.StartsWith("grant: bladestorm rank"));
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

    /// <summary>(M3 lead 8, bd-sockets) The grip beside Bladestorm (the Warden's own skill since 13 Nov 2026): the plan's hands
    /// hold Sunder's own key as the grip (the grip loop in PressPlan.Run): Sunder swings, lands and builds Resolve with no
    /// storm begun (the grip-only hands never press Bladestorm's key).</summary>
    [Fact]
    public void Beside_Bladestorm_the_plan_holds_Sunders_key_as_the_grip()
    {
        var j = MapSim.Survivor("warden", 30, 2, 5);
        var b = Fight(j);
        var storm = b.Weapons.Single(w => w.Id == "bladestorm");
        var sunder = b.Weapons.Single(w => w.Id == "sunder");
        Assert.Equal(0, b.BreakSlot(storm));
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
            if (sunder.Held) held++;
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
        double grace = GripGaps.Grace(sunder);
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
                Assert.True(sunder.Held);
                inGrace++;
            }
            else
            {
                // one step past the grace: let go
                Assert.InRange(gap, grace, grace + 1 / 60.0 + 1e-9);
                Assert.False(sunder.Held);
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
        Assert.False(sunder.Held);
    }
}
