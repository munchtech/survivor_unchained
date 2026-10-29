using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The play camera's close view of her (Play/CloseUp.cs): the wheel only where it is safe, the idle view
/// never with anything hostile near, and any input ends it.</summary>
public class CloseUpTests
{
    static CloseUp.Situation Town => new(Safe: true, Held: false, Threat: false, Moving: false);
    static CloseUp.Situation Wild => new(Safe: false, Held: false, Threat: false, Moving: false);

    static double Run(CloseUp c, CloseUp.Situation s, double seconds)
    {
        double t = 0;
        for (double e = 0; e < seconds; e += 0.1) t = c.Update(0.1, s);
        return t;
    }

    [Fact]
    public void TheWheelBringsHerNearOnlyWhereItIsSafe()
    {
        var c = new CloseUp { IdleOn = false };
        c.Wheel(3, 0, Wild);
        Assert.Equal(0, c.Manual);
        Assert.Equal(0, c.Update(0.1, Wild));
        c.Wheel(3, 0, Town);
        Assert.Equal(0.3, c.Manual, 6);
        Assert.Equal(0.3, c.Update(0.1, Town), 6);
        // as far as it goes, and back out to play's own distance
        c.Wheel(20, 0, Town);
        Assert.Equal(1, c.Manual);
        for (int i = 0; i < 10; i++) c.Wheel(-1, 0, Town);
        Assert.Equal(0, c.Manual);
    }

    [Fact]
    public void LeavingTheSafePlaceTakesTheViewBackOut()
    {
        var c = new CloseUp { IdleOn = false };
        c.Wheel(6, 0, Town);
        Assert.Equal(0.6, c.Update(0.1, Town), 6);
        Assert.Equal(0, c.Update(0.1, Wild));
        Assert.Equal(0, c.Update(0.1, Town));
    }

    [Fact]
    public void NeverInACinematicAConversationOrAScreen()
    {
        var c = new CloseUp();
        c.Wheel(8, 0, Town);
        var held = Town with { Held = true };
        Assert.Equal(0, Run(c, held, 30));
        Assert.False(c.Idling);
        // the wheel's level is kept for when it lets go
        Assert.Equal(0.8, c.Update(0.1, Town), 6);
        c.Wheel(-2, 0, held);
        Assert.Equal(0.8, c.Manual, 6);
    }

    [Fact]
    public void MovingHoldsTheViewBackSoTheWayAheadShows()
    {
        var c = new CloseUp { IdleOn = false };
        c.Wheel(10, 0, Town);
        Assert.Equal(CloseUp.MoveCap, c.Update(0.1, Town with { Moving = true }), 6);
        Assert.Equal(1, c.Update(0.1, Town), 6);
    }

    // Her pose (the owner, 17 October 2026): the wheel never turns her; a framed screen does in the town and the
    // ember's arenas, not in the field; a true idle (a minute) does.
    [Fact]
    public void ZoomingInWithNoScreenNeverTurnsHer()
    {
        var c = new CloseUp();
        c.Wheel(10, 0, Town);
        Assert.Equal(1, Run(c, Town, 30), 6);
        Assert.Equal(CloseUp.Pose.Own, c.PoseFor(framed: false, safe: true, ember: false));
    }

    [Fact]
    public void AScreenOpenInTownTurnsHer()
    {
        var c = new CloseUp();
        Assert.Equal(CloseUp.Pose.ToTheView, c.PoseFor(framed: true, safe: true, ember: false));
        // (an arena or the prologue's night road, where screens stop the world, too)
        Assert.Equal(CloseUp.Pose.ToTheView, c.PoseFor(framed: true, safe: false, ember: true));
    }

    [Fact]
    public void AScreenOpenInTheFieldLeavesHerAsSheWas()
    {
        var c = new CloseUp();
        Assert.Equal(CloseUp.Pose.Own, c.PoseFor(framed: true, safe: false, ember: false));
    }

    [Fact]
    public void AMinuteIdleTurnsHer()
    {
        var c = new CloseUp();
        Run(c, Town, 59);
        Assert.Equal(CloseUp.Pose.Own, c.PoseFor(false, true, false));
        Run(c, Town, 1.5);
        Assert.True(c.Idling);
        Assert.Equal(CloseUp.Pose.ToTheView, c.PoseFor(false, true, false));
        c.Input();
        Assert.Equal(CloseUp.Pose.Own, c.PoseFor(false, true, false));
    }

    [Fact]
    public void LeftAloneSheIsShownCloseAnywhereQuiet()
    {
        var c = new CloseUp { IdleAfter = 12 };
        Assert.Equal(0, Run(c, Wild, 11.5));
        Assert.False(c.Idling);
        Assert.Equal(CloseUp.IdleLevel, Run(c, Wild, 1), 6);
        Assert.True(c.Idling);
        // it drifts in slowly and leaves quickly
        Assert.True(c.Rate(CloseUp.IdleLevel, 0.2) < 1);
        c.Input();
        Assert.True(c.Rate(0, 0.8) >= 3);
    }

    [Fact]
    public void AnyInputEndsTheIdleView()
    {
        var c = new CloseUp { IdleAfter = 12 };
        Run(c, Wild, 13);
        Assert.True(c.Idling);
        c.Input();
        Assert.False(c.Idling);
        Assert.Equal(0, c.Update(0.1, Wild));
        // and the quiet counts again from nothing
        Assert.Equal(0, Run(c, Wild, 11.5));
        // in town it goes back to the wheel's level, not play's
        var t = new CloseUp { IdleAfter = 12 };
        t.Wheel(4, 0, Town);
        Run(t, Town, 13);
        Assert.True(t.Idling);
        t.Input();
        Assert.Equal(0.4, t.Update(0.1, Town), 6);
    }

    [Fact]
    public void TheWheelDuringTheIdleViewCarriesOnFromWhereItIs()
    {
        var c = new CloseUp { IdleAfter = 12 };
        Run(c, Town, 13);
        Assert.True(c.Idling);
        c.Wheel(-1, 0.9, Town);
        Assert.False(c.Idling);
        Assert.Equal(0.8, c.Manual, 6);
        // out in the wild the wheel only ends it
        var w = new CloseUp { IdleAfter = 12 };
        Run(w, Wild, 13);
        w.Wheel(1, 0.9, Wild);
        Assert.False(w.Idling);
        Assert.Equal(0, w.Update(0.1, Wild));
    }

    [Fact]
    public void NeverWithAnythingHostileNear()
    {
        var c = new CloseUp { IdleAfter = 12 };
        Assert.Equal(0, Run(c, Wild with { Threat = true }, 60));
        Assert.False(c.Idling);
        // something drawing near ends it at once, and the quiet starts again once it has gone
        Run(c, Wild, 13);
        Assert.True(c.Idling);
        Assert.Equal(0, c.Update(0.1, Wild with { Threat = true }));
        Assert.False(c.Idling);
        Assert.Equal(0, Run(c, Wild, 11.5));
    }

    [Fact]
    public void TheSettingTurnsTheIdleViewOff()
    {
        var c = new CloseUp { IdleOn = false, IdleAfter = 12 };
        Assert.Equal(0, Run(c, Wild, 60));
        Assert.False(c.Idling);
    }

    [Fact]
    public void ThreatIsAnythingHostileNearOrRousedAndComing()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 42);
        var b = j.StartBattle(true, new CollisionWorld(200), (_, _) => 0, 0, 0, 0, 7);
        Assert.False(CloseUp.Threat(b));
        var far = b.SpawnEnemy("wolf", 80, 0)!;
        Assert.False(CloseUp.Threat(b));
        // roused and within reach of her
        far.X = 35;
        far.State = EnemyState.Active;
        Assert.True(CloseUp.Threat(b));
        far.State = EnemyState.Idle;
        Assert.False(CloseUp.Threat(b));
        // near, whether it has seen her or not
        far.X = 12;
        Assert.True(CloseUp.Threat(b));
        // a creature that leaves her be until provoked is no threat
        far.Disposition = Disposition.Neutral;
        Assert.False(CloseUp.Threat(b));
    }

    [Fact]
    public void WalkersKeepOutOfTheViewBehindHer()
    {
        // She stands at the origin, the camera south of her looking north (-z).
        var c = (0.0, 0.0, 0.0, -1.0);
        // Right behind her head, 8 m back: pushed sideways, by the nearer side.
        var (x, _) = Folk.OutOfView(c, 0.3, -8);
        Assert.True(x > 0.5);
        Assert.True(Folk.OutOfView(c, -0.3, -8).X < -0.5);
        // At her side: pushed off.
        Assert.True(Folk.OutOfView(c, 2, 0).X > 0.5);
        // Well clear of the wedge, or in front of the camera's view behind her: left alone.
        Assert.Equal((0.0, 0.0), Folk.OutOfView(c, 6, -8));
        Assert.Equal((0.0, 0.0), Folk.OutOfView(c, 0, 30));
    }

    [Fact]
    public void ACarriedTorchKeysTheCloseViewByNight()
    {
        Assert.Equal(1, CloseUp.CarriedShare(night: false, carries: true));
        Assert.Equal(1, CloseUp.CarriedShare(night: true, carries: false));
        Assert.InRange(CloseUp.CarriedShare(night: true, carries: true), 0.3, 0.4);
        // From his left (x+), level with his chest: keyed from there, level.
        var (az, el) = CloseUp.CarriedAim(0.4, 0, 0.3);
        Assert.Equal(System.Math.Atan2(0.4, 0.3), az, 6);
        Assert.Equal(0, el, 6);
        // Below his chin: held level, never lit from under; high above: held at the cap.
        Assert.Equal(0, CloseUp.CarriedAim(0.3, -0.5, 0.3).El, 6);
        Assert.Equal(CloseUp.CarriedElMax * System.Math.PI / 180, CloseUp.CarriedAim(0.1, 2, 0.1).El, 6);
    }
}
