using System;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

public class FrameGuardTests
{
    [Fact]
    public void AFailedCloseUpLogsOnceAndTheFrameContinues()
    {
        var guard = new FrameGuard();
        int ticks = 0, reports = 0, frames = 0;
        var failure = new ObjectDisposedException("DirectionalLight3D");
        for (int i = 0; i < 10; i++)
        {
            guard.Run(guard, 0.1, (_, _) => { ticks++; throw failure; },
                e => { Assert.Same(failure, e); reports++; });
            frames++;
        }
        Assert.True(guard.Failed);
        Assert.Equal(1, ticks);
        Assert.Equal(1, reports);
        Assert.Equal(10, frames);
    }

    [Fact]
    public void ANewZoneCanTickAgain()
    {
        var guard = new FrameGuard();
        guard.Run(guard, 0.1, (_, _) => throw new InvalidOperationException(), _ => { });
        guard.Reset();
        double elapsed = 0;
        guard.Run(guard, 0.25, (_, dt) => elapsed += dt, _ => Assert.True(false));
        guard.Run(guard, 0.5, (_, dt) => elapsed += dt, _ => Assert.True(false));
        Assert.False(guard.Failed);
        Assert.Equal(0.75, elapsed);
    }
}
