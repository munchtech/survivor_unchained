using System.Collections.Generic;
using System.Threading;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(L1 lead 21 QUIT) The quit watchdog's logic (src/QuitGuard.cs), without Godot.</summary>
public class QuitGuardTests
{
    [Fact]
    public void Fires_after_its_time_the_line_first_then_the_kill()
    {
        var order = new List<string>();
        var g = new QuitGuard(40, () => { lock (order) order.Add("say"); }, () => { lock (order) order.Add("kill"); });
        Assert.True(g.Start().Join(5000));
        Assert.True(g.Fired);
        Assert.Equal(new[] { "say", "kill" }, order);
    }

    [Fact]
    public void Kills_though_the_line_never_returns()
    {
        using var never = new ManualResetEventSlim(false);
        bool killed = false;
        var g = new QuitGuard(20, () => never.Wait(), () => killed = true, sayMs: 60);
        Assert.True(g.Start().Join(5000));
        Assert.True(killed);
        never.Set();
    }

    [Fact]
    public void Called_off_it_never_fires()
    {
        bool said = false, killed = false;
        var g = new QuitGuard(60000, () => said = true, () => killed = true);
        var t = g.Start();
        g.Cancel();
        Assert.True(t.Join(5000));
        Assert.False(g.Fired || said || killed);
    }

    [Fact]
    public void Is_never_armed_in_the_test_host()
    {
        Assert.True(QuitGuard.InTestHost);
        Assert.Null(QuitGuard.ArmForProcess(() => { }, 0, 1));
        Assert.Equal("quit guard: fired", QuitGuard.FiredLine);   // (tools/experience/demo_run.py and quit_starts.py count this line)
        Assert.Equal(2000, QuitGuard.Ms);
    }
}
