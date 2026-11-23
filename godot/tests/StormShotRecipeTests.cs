using System;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(lane B, 16 Nov 2026) Why the storm shot stood still: the den shot's recipe (a level-7 Warden, --veteran 7: Sunder
/// key 1, Heroic Leap key 2, Bladestorm key 3, Groundbreaker and Iron Vow kindled; a bound pack round her; --resolve-at),
/// as the game's keys drive it (WorldScene.Skills: every key's hold each step, then the press). A meter set FULL with a
/// crowd near is spent at once by the kindled Groundbreaker's heave (it fires itself at ResolveMeter.SelfAt of the cap and
/// takes all of it), so the storm's press finds 0 and is refused; set short of full it stays (no fade with foes near) and
/// key 3 held spins. The shot asks 95, never 100 (DevSlots says so in the log).</summary>
public sealed class StormShotRecipeTests
{
    const double Dt = 1 / 60.0;

    static (Battle B, WeaponInst Storm) Den()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice { Name = "T", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 11);
        DevVeteran.Apply(j.Ch, "7", 11);
        var b = j.StartBattle(true, new CollisionWorld(120), (_, _) => 0, 0, 0, 0, 11);
        var rng = new Random(3);
        for (int i = 0; i < 10; i++)
        {
            double ang = rng.NextDouble() * Math.Tau, d = 2.5 + rng.NextDouble() * 3;
            var e = b.SpawnEnemy("wolf", Math.Cos(ang) * d, Math.Sin(ang) * d)!;
            e.Hp *= 400; e.MaxHp *= 400; e.BoundX = e.X; e.BoundZ = e.Z; e.Status.Ensure(StatusKind.Bound, 9, 1, 1, 0);
        }
        return (b, b.Weapons.Single(w => w.Id == "bladestorm"));
    }

    /// <summary>The shot to 6.3 s with the meter set at 0.52 s, then key 3 held 3 s and pressed as the keys do.</summary>
    static (double ResolveAtPress, int Ticks, bool SpunAtEnd) Shoot(double resolve)
    {
        var (b, w) = Den();
        Assert.Equal(2, w.Slot);
        bool set = false, pressed = false, spun = false;
        double resAtPress = -1;
        int ticks = 0;
        for (double t = 0; t < 9.6; t += Dt)
        {
            if (!set && b.Time >= 0.5) { set = true; b.Resolve.Set(resolve); }
            bool down = t >= 6.3 && t < 9.3;
            for (int i = 0; i < 4; i++) b.HoldSkill(i, i == 2 && down);
            if (down && !pressed) { pressed = true; resAtPress = b.Resolve.Value; b.PressSkill(2, b.Player.X, b.Player.Z); }
            b.Tick(Dt, 0, 0);
            foreach (var ev in b.Events.Drain()) if (ev is Ev.Spin { Phase: SpinPhase.Tick }) ticks++;
            if (t > 9.2 && t < 9.25) spun |= w.Channeling;
        }
        return (resAtPress, ticks, spun);
    }

    [Fact]
    public void A_meter_short_of_full_waits_for_the_storm_and_key_three_held_spins()
    {
        var (res, ticks, spun) = Shoot(95);
        Assert.Equal(95, res, 6);
        Assert.True(spun, "still spinning near the end of the 3 s hold");
        // a blow each ChannelGap (0.3 s) over the 3 s held: about ten
        Assert.InRange(ticks, 9, 11);
    }
}
