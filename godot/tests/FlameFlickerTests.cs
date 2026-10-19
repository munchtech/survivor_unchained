using System;
using System.Linq;
using SurvivorUnchained.World;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The flame kit's light flicker (look bible 10_props_flames): +-10-15% energy over ten
/// seconds, never a strobe (no jump between two frames at 60 fps bigger than 5%: a flame's quickest licks, about ten a second).</summary>
public class FlameFlickerTests
{
    readonly ITestOutputHelper log;
    public FlameFlickerTests(ITestOutputHelper log) => this.log = log;

    [Fact]
    public void FlickerSwingsTenToFifteenPercentSmoothly()
    {
        foreach (var phase in new[] { 0f, 0.17f, 0.42f, 0.73f, 0.91f })
        {
            var e = Enumerable.Range(0, 600).Select(i => FlameFlicker.At(i / 60f, phase)).ToArray();
            float lo = e.Min(), hi = e.Max();
            float step = Enumerable.Range(1, 599).Max(i => Math.Abs(e[i] - e[i - 1]));
            log.WriteLine($"phase {phase}: {lo:F3}..{hi:F3}, biggest frame step {step:F4}");
            Assert.InRange(1 - lo, 0.08f, 0.15f);
            Assert.InRange(hi - 1, 0.08f, 0.15f);
            Assert.True(step < 0.05f, $"step {step}");
        }
    }
}
