using System.Text.Json;
using SurvivorUnchained.Rpg;
using Xunit;

public class ArmorHoldSupportTests
{
    [Fact]
    public void LiftPressFillDefaultToSupport()
    {
        var h = JsonSerializer.Deserialize<ArmorHold>("{\"support\":0.6}")!;
        Assert.Equal(0.6, h.LiftValue); Assert.Equal(0.6, h.PressValue); Assert.Equal(0.6, h.FillValue);
    }

    [Fact]
    public void RowValuesOverridePerShape()
    {
        var h = JsonSerializer.Deserialize<ArmorHold>("{\"support\":1,\"lift\":0.3,\"fill\":0}")!;
        Assert.Equal(0.3, h.LiftValue); Assert.Equal(1, h.PressValue); Assert.Equal(0, h.FillValue);
    }

    [Fact]
    public void NoSupportDerivesFromAmount()
    {
        var h = JsonSerializer.Deserialize<ArmorHold>("{\"amount\":0.55}")!;
        Assert.Equal(1, h.LiftValue, 6);
    }
}
