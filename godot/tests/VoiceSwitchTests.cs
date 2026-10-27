using SurvivorUnchained.World;
using Xunit;

public class VoiceSwitchTests
{
    [Fact] public void OffByDefault() => Assert.False(VoiceLines.Enabled);
    [Fact] public void OnlyVoOnTurnsItOn()
    {
        Assert.True(VoiceLines.FromArg("on"));
        Assert.False(VoiceLines.FromArg(null));
        Assert.False(VoiceLines.FromArg("off"));
    }
}
