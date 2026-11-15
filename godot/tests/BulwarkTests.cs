using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Bulwark (Content/Abilities.cs: "Plant your feet for 3 s: blows are cut by 65%, arrows and bolts are turned
/// back on whoever loosed them, and the horde turns on you", wait 15), held in the real fight: the art fires as a calling's
/// reflex (the only way it fires), each number against the same fight on the same seed without it.</summary>
public sealed class BulwarkTests
{
    const double Frame = 1 / 60.0;

    static Battle Arena(AbilityKind inHand = AbilityKind.Bulwark)
    {
        var s = new StatBlock();
        s.SetBase(new Dictionary<string, double>
        {
            [Stat.MaxHealth] = 200, [Stat.MoveSpeed] = 5, [Stat.PickupRadius] = 2.4, [Stat.CritChance] = 0, [Stat.CritDamage] = 1.5, [Stat.Luck] = 1,
        });
        var b = new Battle(new BattleSetup { Seed = 5, Collision = new CollisionWorld(120), Combat = true, Stats = s, Weapons = [], Ability = inHand });
        b.Rules.DashForms = true;
        return b;
    }

    /// <summary>Bulwark wired as a reflex with this wait (0: none of its own), fired on the next sense tick.</summary>
    static ReflexRun Plant(Battle b, double wait = 99)
    {
        var l = new LampLoadout();
        l.Reflexes.Add(new ReflexDef("bulwark", "every", wait, null));
        b.SetLamps(l);
        b.Tick(Frame, 0, 0);
        b.Events.Drain();
        var r = b.Reflexes.Single();
        Assert.Equal(1, r.Fired);
        return r;
    }

    static void Tick(Battle b, double seconds)
    {
        for (double t = 0; t < seconds - 1e-9; t += Frame) { b.Tick(Frame, 0, 0); b.Events.Drain(); }
    }

    static Enemy Foe(Battle b, string def, double x, double z)
    {
        var e = b.SpawnEnemy(def, x, z)!;
        e.MaxHp = e.Hp = 1e6;
        e.AttackT = e.RangedT = 99;
        return e;
    }

    /// <summary>One blow of 40 reaching her, through the whole of HurtPlayer (armour, dodge, block, the bulwark).</summary>
    static double Blow(Battle b) => b.HurtPlayer(40, School.Physical, "test", null);

    /// <summary>The blow a fight without the bulwark takes, a frame in.</summary>
    static double Whole()
    {
        var plain = Arena();
        Tick(plain, Frame);
        double whole = Blow(plain);
        Assert.True(whole > 0);
        return whole;
    }

    [Fact]
    public void Planted_blows_are_cut_by_65_percent()
    {
        var planted = Arena();
        Plant(planted);
        Assert.Equal(0.35, Blow(planted) / Whole(), 6);
    }

    [Fact]
    public void The_plant_holds_three_seconds_and_no_longer()
    {
        double whole = Whole();
        var b = Arena();
        Plant(b);
        // Up for 3 s from the frame it went up on (at most that frame's own tick gone).
        Assert.InRange(b.Player.BulwarkT, 3 - Frame - 1e-9, 3);
        // Just before: still cut. Just after: a blow lands whole again.
        var before = Arena();
        Plant(before);
        Tick(before, 3 - 4 * Frame);
        Assert.True(before.Player.BulwarkT > 0);
        Assert.Equal(0.35, Blow(before) / whole, 6);
        var past = Arena();
        Plant(past);
        Tick(past, 3 + 2 * Frame);
        Assert.Equal(0, past.Player.BulwarkT);
        Assert.Equal(1.0, Blow(past) / whole, 6);
    }

    [Fact]
    public void A_bolt_loosed_at_her_while_planted_turns_back_on_its_archer()
    {
        // Unplanted, the Bowman's bolt lands on her and the Bowman is untouched.
        var plain = Arena();
        var pa = Foe(plain, "risen_archer", 7, 0);
        Tick(plain, Frame);
        pa.RangedT = 0;
        Tick(plain, 2.0);
        Assert.True(plain.Player.Hp < plain.MaxHp, "the bolt should land on her unplanted");
        Assert.Equal(pa.MaxHp, pa.Hp);

        // Planted, the same bolt reaches her, flies back and strikes the one who loosed it; she takes nothing.
        var b = Arena();
        var a = Foe(b, "risen_archer", 7, 0);
        Plant(b);
        a.RangedT = 0;
        int turned = 0;
        for (double t = 0; t < 2.0; t += Frame)
        {
            b.Tick(Frame, 0, 0);
            turned += b.Projectiles.Items.Count(pr => pr.Alive && pr.Owner == Side.Player);
            b.Events.Drain();
        }
        Assert.True(b.Player.BulwarkT > 0, "still planted when the bolt came");
        Assert.True(turned > 0, "the bolt was turned back");
        Assert.Equal(b.MaxHp, b.Player.Hp);
        Assert.True(a.Hp < a.MaxHp, "the turned bolt strikes its archer");
    }

    [Fact]
    public void Planted_the_horde_turns_on_her_from_her_reflections()
    {
        // Mirror Step in hand leaves two reflections where she stood: what hunts her goes for them, unless she is planted.
        static Enemy Fled(bool plant)
        {
            var b = Arena(AbilityKind.MirrorStep);
            var e = Foe(b, "risen", 6, 0);
            Tick(b, 1.0);
            Assert.Equal(-1, e.Target);
            Assert.True(b.Dash(-1, 0));
            Tick(b, 0.3);
            Assert.Equal(2, b.Decoys.Count);
            Assert.Contains(b.Decoys, d => d.Id == e.Target);
            if (plant) Plant(b);
            Tick(b, 2.0);
            if (plant) Assert.True(b.Player.BulwarkT > 0);
            else Assert.Contains(b.Decoys, d => d.Id == e.Target);
            return e;
        }
        Fled(false);
        Assert.Equal(-1, Fled(true).Target);
    }

    [Fact]
    public void Planted_the_horde_leaves_her_allies_for_her()
    {
        // A creature on her side stands right by the foe, she farther off: the foe goes for the nearer one, unless she is planted.
        static (Enemy Foe, Enemy Ally) Fight(bool plant)
        {
            var b = Arena();
            var e = Foe(b, "risen", 6, 0);
            var ally = b.SpawnEnemy("risen", 6, 1.2, new Battle.SpawnOpts { Disposition = Disposition.Ally, Faction = Faction.Ally })!;
            ally.MaxHp = ally.Hp = 1e6;
            ally.AttackT = 99;
            if (plant) Plant(b);
            Tick(b, 1.0);
            return (e, ally);
        }
        var (pf, pally) = Fight(false);
        Assert.Equal(pally.Id, pf.Target);
        var (f, _) = Fight(true);
        Assert.Equal(-1, f.Target);
    }

    [Fact]
    public void Its_wait_is_fifteen_seconds_where_the_lamp_gives_none()
    {
        var b = Arena();
        var r = Plant(b, wait: 0);
        Assert.Equal(15, r.Full, 6);
        Tick(b, 15 - 3 * Frame);
        Assert.Equal(1, r.Fired);
        Tick(b, 0.2);
        Assert.Equal(2, r.Fired);

        // A lamp that names its own wait keeps it (the Warden's Oath: "Every 20 s").
        Assert.Equal(20, Plant(Arena(), wait: 20).Full, 6);
    }
}
