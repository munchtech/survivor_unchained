using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Weapons sheathed in town (Play/Sheath.cs): sheathed at once on entering a safe place, after 1.5 s of quiet
/// otherwise, and drawn at once on a threat, on acting or on leaving the safe place.</summary>
public class SheathTests
{
    static bool Run(Sheath s, double seconds, bool safe, bool threat = false, bool acting = false)
    {
        bool changed = false;
        for (double t = 0; t < seconds - 1e-9; t += 0.1) changed |= s.Update(0.1, safe, threat, acting);
        return changed;
    }

    [Fact]
    public void EnteringASafePlaceSheathesAtOnce()
    {
        var s = new Sheath();
        s.Enter(true);
        Assert.True(s.Sheathed);
        Assert.False(s.Update(0.016, true, false, false));
        Assert.True(s.Sheathed);
    }

    [Fact]
    public void EnteringAnUnsafePlaceStaysDrawn()
    {
        var s = new Sheath();
        s.Enter(false);
        Assert.False(s.Sheathed);
        Assert.False(Run(s, 10, false));
    }

    [Fact]
    public void SheathesOnlyAfterAQuietMoment()
    {
        var s = new Sheath();
        s.Enter(false);
        Assert.False(Run(s, 1.4, true));
        Assert.False(s.Sheathed);
        Assert.True(Run(s, 0.3, true));
        Assert.True(s.Sheathed);
    }

    [Fact]
    public void ADrawnWeaponInTheMiddleOfTheWaitStartsTheWaitAgain()
    {
        var s = new Sheath();
        s.Enter(false);
        Run(s, 1.2, true);
        s.Update(0.1, true, true, false);  // a threat for a frame
        Run(s, 1.2, true);
        Assert.False(s.Sheathed);
        Run(s, 0.5, true);
        Assert.True(s.Sheathed);
    }

    [Fact]
    public void AThreatDrawsAtOnce()
    {
        var s = new Sheath();
        s.Enter(true);
        Assert.True(s.Update(0.016, true, true, false));
        Assert.False(s.Sheathed);
    }

    [Fact]
    public void ActingDrawsAtOnce()
    {
        var s = new Sheath();
        s.Enter(true);
        Assert.True(s.Update(0.016, true, false, true));
        Assert.False(s.Sheathed);
    }

    [Fact]
    public void LeavingTheSafePlaceDrawsAtOnce()
    {
        var s = new Sheath();
        s.Enter(true);
        Assert.True(s.Update(0.016, false, false, false));
        Assert.False(s.Sheathed);
    }

    [Fact]
    public void ItDoesNotFlipFlop()
    {
        var s = new Sheath();
        s.Enter(true);
        int changes = 0;
        // A threat every other half second: drawn, and never sheathed between (the wait is 1.5 s).
        for (int i = 0; i < 100; i++)
            if (s.Update(0.1, true, i % 5 == 0, false)) changes++;
        Assert.Equal(1, changes);
        Assert.False(s.Sheathed);
        // Quiet for good: one change, and then none.
        changes = 0;
        for (int i = 0; i < 100; i++)
            if (s.Update(0.1, true, false, false)) changes++;
        Assert.Equal(1, changes);
        Assert.True(s.Sheathed);
    }

    [Fact]
    public void PickChoosesTheTownClipOnlyWhenItExists()
    {
        var have = new System.Collections.Generic.HashSet<string> { "stop_warden_town_l" };
        Assert.Equal("stop_warden_l", Sheath.Pick(false, "stop_warden", "_l", have.Contains));
        Assert.Equal("stop_warden_town_l", Sheath.Pick(true, "stop_warden", "_l", have.Contains));
        Assert.Null(Sheath.Pick(true, "stop_warden", "_r", have.Contains));
        Assert.Null(Sheath.Pick(true, "idle_warden", "_break", have.Contains));
    }

    [Fact]
    public void SheathedTriesTheKindsTownClipThenTheCallingsThenTheArmedOnes()
    {
        Assert.Equal(new[] { "idle_arcanist_staff_town", "idle_arcanist_staff", "idle_arcanist" },
            Sheath.Names("idle", "arcanist", "staff", true));
        Assert.Equal(new[] { "idle_arcanist_wand_town", "idle_arcanist_town", "idle_arcanist_wand", "idle_arcanist" },
            Sheath.Names("idle", "arcanist", "wand", true));
        Assert.Equal(new[] { "run_stalker_daggers", "run_stalker" }, Sheath.Names("run", "stalker", "daggers", false));
        // The warden has one town stand for every kind she holds.
        var have = new System.Collections.Generic.HashSet<string> { "idle_warden_town", "idle_arcanist_staff_town" };
        Assert.True(Sheath.HasTown("warden", "sword+shield", have.Contains));
        Assert.True(Sheath.HasTown("arcanist", "staff", have.Contains));
        Assert.False(Sheath.HasTown("arcanist", "wand", have.Contains));
        Assert.False(Sheath.HasTown("reaver", "axe", have.Contains));
    }

    [Fact]
    public void AStaffStaysInHerHandSoTheCallingsTownStandIsNotItsOwn()
    {
        var have = new System.Collections.Generic.HashSet<string> { "idle_arcanist_town" };
        Assert.False(Sheath.HasTown("arcanist", "staff", have.Contains));
        Assert.True(Sheath.HasTown("arcanist", "wand", have.Contains));
        foreach (var kind in new[] { "axe", "axes", "sword", "daggers", "crossbow", "sword+shield" })
            Assert.True(Sheath.HasTown("arcanist", kind, have.Contains), kind);
    }

    [Fact]
    public void AStaffSheathedNeverTriesTheCallingsFreeArmedTownClips()
    {
        Assert.DoesNotContain("run_arcanist_town", Sheath.Names("run", "arcanist", "staff", true));
        Assert.DoesNotContain("idle_arcanist_town", Sheath.Names("idle", "arcanist", "staff", true));
        Assert.Equal(new[] { "run_arcanist_staff_town", "run_arcanist_staff", "run_arcanist" }, Sheath.Names("run", "arcanist", "staff", true));
        Assert.Contains("run_arcanist_town", Sheath.Names("run", "arcanist", "wand", true));
    }

    [Fact]
    public void ADrawnKindWithItsOwnRunButNoWalkGetsNoWalk()
    {
        var has = new System.Func<string, bool>(n => n is "run_warden_sword" or "walk_warden");
        Assert.Empty(Sheath.WalkNames("warden", "sword", false, has));
        Assert.Equal(["walk_warden_greatsword", "walk_warden"], Sheath.WalkNames("warden", "greatsword", false, n => n == "x"));
        Assert.Equal(Sheath.Names("walk", "warden", "sword", true), Sheath.WalkNames("warden", "sword", true, has));
    }
}
