using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>M4 (docs/design/M4_HUD.md §2-3): Resolve's veins' motion (src/Ui/ResolveMotion.cs), the under-bar rule and
/// the step-won choice.</summary>
public sealed class ResolveMotionTests
{
    const float Dt = 1 / 60f;

    static float Run(float from, float to, float secs)
    {
        float s = from;
        for (float t = 0; t < secs; t += Dt) s = ResolveMotion.Ease(s, to, Dt);
        return s;
    }

    [Fact]
    public void Ease_up_in_012_down_in_02()
    {
        Assert.InRange(Run(0, 1, 0.12f), 0.93f, 1f);
        Assert.InRange(Run(0, 1, 0.04f), 0.3f, 0.8f);        // eased, not a jump
        Assert.InRange(Run(1, 0, 0.12f), 0.1f, 0.4f);        // down slower than up
        Assert.InRange(Run(1, 0, 0.2f), 0f, 0.07f);
        Assert.Equal(0.5f, ResolveMotion.Ease(0.4995f, 0.5f, Dt));   // snapped
    }

    [Theory]
    [InlineData(ResolveReason.Landed, ResolveMotion.Motion.Landed)]
    [InlineData(ResolveReason.Taken, ResolveMotion.Motion.Taken)]
    [InlineData(ResolveReason.Blocked, ResolveMotion.Motion.Blocked)]
    [InlineData(ResolveReason.Spent, ResolveMotion.Motion.Spent)]
    [InlineData(ResolveReason.Drained, ResolveMotion.Motion.Drained)]
    [InlineData(ResolveReason.Faded, ResolveMotion.Motion.Faded)]
    public void Each_reason_its_motion(ResolveReason r, ResolveMotion.Motion m) => Assert.Equal(m, ResolveMotion.MotionFor(r));

    [Fact]
    public void Landed_runs_a_core_packet_to_the_front_then_flares()
    {
        var m = new ResolveMotion();
        m.Feed(true, 60, 100, ResolveReason.Landed, 1.0, 1.0);
        m.Tick(Dt);
        Assert.Equal(ResolveMotion.Packet.Core, m.PktColor);
        Assert.True(m.PktK > 0.99f && m.PktG >= 0);
        float g0 = m.PktG;
        for (int i = 0; i < 6; i++) m.Tick(Dt);
        Assert.True(m.PktG > g0);                                  // it runs up
        for (int i = 0; i < 12; i++) m.Tick(Dt);                   // past 0.25 s: the flare
        Assert.True(m.PktK == 0 && m.Flare > 0);
        for (int i = 0; i < 12; i++) m.Tick(Dt);
        Assert.True(m.Flare == 0 && m.PktG < 0);
    }

    [Fact]
    public void Taken_is_edge_and_blocked_is_a_smaller_spark()
    {
        var m = new ResolveMotion();
        m.Feed(true, 30, 100, ResolveReason.Taken, 1.0, 1.0); m.Tick(Dt);
        Assert.Equal(ResolveMotion.Packet.Edge, m.PktColor);
        m.Feed(true, 34, 100, ResolveReason.Blocked, 1.2, 1.2); m.Tick(Dt);
        Assert.Equal(ResolveMotion.Packet.Spark, m.PktColor);
        Assert.True(m.PktK < 1 && m.PktW < ResolveMotion.PacketW);
    }

    [Fact]
    public void Spent_flashes_its_band_and_goes_dark_in_02()
    {
        var m = new ResolveMotion();
        m.Feed(true, 80, 100, ResolveReason.Landed, 0.5, 0.5);
        for (int i = 0; i < 60; i++) m.Tick(Dt);
        m.Feed(true, 50, 100, ResolveReason.Spent, 1.5, 1.5);
        m.Tick(Dt);
        Assert.True(m.SpentK > 0.9f && m.SpentLo < 0.51f && m.SpentHi > 0.79f);
        for (int i = 0; i < 13; i++) m.Tick(Dt);
        Assert.Equal(0, m.SpentK);
    }

    [Fact]
    public void Drained_and_faded_run_while_they_last()
    {
        var m = new ResolveMotion();
        m.Feed(true, 60, 100, ResolveReason.Drained, 2.0, 2.0);
        for (int i = 0; i < 10; i++) m.Tick(Dt);
        Assert.Equal(1, m.Drain);
        m.Feed(true, 60, 100, ResolveReason.Drained, 2.0, 3.0);    // a second since: it stopped
        for (int i = 0; i < 20; i++) m.Tick(Dt);
        Assert.Equal(0, m.Drain);
        float c = 0;
        for (int i = 0; i < 90; i++) { m.Feed(true, 60 - i * 0.1, 100, ResolveReason.Faded, 4 + i * Dt, 4 + i * Dt); m.Tick(Dt); c = m.Cool; }
        Assert.InRange(c, 0.6f, ResolveMotion.CoolMost);           // mid -> edge -> toward bronze as it falls
    }

    [Fact]
    public void Full_glints_once_shimmers_and_rims_never_blazes()
    {
        var m = new ResolveMotion();
        m.Feed(true, 100, 100, ResolveReason.Landed, 1.0, 1.0);
        m.Tick(Dt);
        Assert.Equal(1, m.Glint);
        int glintFrames = 1, shimmerFrames = 0;
        for (int i = 0; i < 300; i++)
        {
            m.Feed(true, 100, 100, ResolveReason.Landed, 1.0, 1.0 + i * Dt);
            m.Tick(Dt);
            if (m.Glint > 0) glintFrames++;
            if (m.ShimmerG >= 0) shimmerFrames++;
        }
        Assert.InRange(glintFrames, 2, 5);                         // 2-3 frames at 30 fps
        Assert.InRange(shimmerFrames, 60, 150);                    // two shimmers of 0.9 s in 5 s
        Assert.Equal(1, m.Rim);
    }

    [Fact]
    public void Off_draws_nothing()
    {
        var m = new ResolveMotion();
        m.Feed(false, 50, 100, ResolveReason.Landed, 1.0, 1.0);
        m.Tick(Dt);
        Assert.False(m.Shown);
    }

    [Fact]
    public void Old_changes_play_no_motion_when_the_view_comes()
    {
        var m = new ResolveMotion();
        m.Feed(true, 40, 100, ResolveReason.Landed, 1.0, 9.0);
        m.Tick(Dt);
        Assert.True(m.PktK == 0 && m.PktG < 0);
    }

    [Fact]
    public void Veins_hold_at_06_when_she_fades()
    {
        Assert.Equal(1f, ResolveMotion.Alpha(1, 0.3f), 0.001f);
        Assert.Equal(ResolveMotion.Hold, ResolveMotion.Alpha(0.3f, 0.3f), 0.001f);
    }

    [Fact]
    public void Pins_freeze_each_reason()
    {
        var m = new ResolveMotion();
        m.Pin(0.6f, "spent");
        m.Feed(true, 0, 100, ResolveReason.Landed, 5, 5);
        m.Tick(1);
        Assert.True(m.Level == 0.6f && m.SpentK > 0 && m.SpentHi > 0.6f);
        var f = new ResolveMotion();
        f.Pin(1, "full");
        Assert.True(f.Glint == 1 && f.Rim == 1 && f.ShimmerG > 0);
    }

    [Fact]
    public void Under_bar_in_campaign_fights_too_and_fades_at_peace()
    {
        Assert.True(ResolveMotion.UnderWanted(true, true, false, false, true, true, false));    // a night (ember)
        Assert.True(ResolveMotion.UnderWanted(true, false, true, true, true, true, false));    // a campaign fight
        Assert.False(ResolveMotion.UnderWanted(true, false, true, false, true, true, false));   // the campaign at peace
        Assert.False(ResolveMotion.UnderWanted(true, false, false, true, true, true, false));   // neither
        Assert.False(ResolveMotion.UnderWanted(true, false, true, true, true, false, false));   // the setting off
        Assert.False(ResolveMotion.UnderWanted(true, false, true, true, true, true, true));     // the Lamps wide
        Assert.False(ResolveMotion.UnderWanted(true, false, true, true, false, true, false));   // dead
    }

    [Fact]
    public void Only_a_charge_pops_a_new_pip()
    {
        Assert.True(ResolveMotion.StepPopsNew(DashStepKind.Charge));
        Assert.False(ResolveMotion.StepPopsNew(DashStepKind.Length));
        Assert.False(ResolveMotion.StepPopsNew(DashStepKind.Recharge));
        Assert.False(ResolveMotion.StepPopsNew(DashStepKind.Landing));
    }
}
