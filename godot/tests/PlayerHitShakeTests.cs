using System.IO;
using SurvivorUnchained.Core;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A hit on her raises the camera shake to its size (HitShake), never sums.
/// BattleFx.cs is not compiled into the tests, so this scans the source.</summary>
public class PlayerHitShakeTests
{
    [Fact]
    public void PlayerHit_shake_goes_through_HitShake()
    {
        var godot = Path.GetFullPath(Path.Combine(DataFiles.Dir, ".."));
        var src = File.ReadAllText(Path.Combine(godot, "src", "Fx", "BattleFx.cs"));
        int a = src.IndexOf("case Ev.PlayerHit e:");
        Assert.True(a >= 0);
        int b = src.IndexOf("case Ev.", a + 10);
        var block = b > a ? src.Substring(a, b - a) : src.Substring(a);
        Assert.Contains("HitShake(", block);
        Assert.DoesNotContain("AddTrauma((float)Math.Min(0.5, 0.12 + e.Amount / 60))", block);
    }
}
