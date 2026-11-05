using SurvivorUnchained.Content;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The Ford-Warden's teeth (H8, N20; H6's numbers in teeth.json "prologue"): two crashes are the way through.</summary>
public class FordWardenTeethTests
{
    [Fact]
    public void The_Ford_Warden_has_floors_by_lamps_unbroken()
    {
        Teeth.Reload();
        var fw = Teeth.Ford;
        Assert.NotNull(fw);
        Assert.Equal(4, fw!.Floors.Length);
        Assert.Equal(0.67, fw.Floors[3], 3);
        Assert.Equal(0.34, fw.Floors[2], 3);
        Assert.Equal(0, fw.Floors[1]);
        Assert.Equal(4, fw.Ward.Length);
        Assert.InRange(fw.HpMul, 1, 3);
        Assert.Equal(60, fw.MinSeconds);
    }
}
