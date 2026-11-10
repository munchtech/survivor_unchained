using SurvivorUnchained.Look;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(L1 lead 22, mirror) The bone twin map --hold-mirror swaps left and right by.</summary>
public class MirrorPairsTests
{
    [Theory]
    [InlineData("hand_l", "hand_r")]
    [InlineData("hand_r", "hand_l")]
    [InlineData("upperarm.L", "upperarm.R")]
    [InlineData("thigh_R", "thigh_L")]
    [InlineData("index_01_l_end", "index_01_r_end")]
    [InlineData("LeftHand", "RightHand")]
    [InlineData("grip_slide_l", "grip_slide_r")]
    [InlineData("pelvis", "pelvis")]
    [InlineData("spine_02", "spine_02")]
    [InlineData("head", "head")]
    [InlineData("eyebrow_ctrl", "eyebrow_ctrl")]
    public void Twin(string name, string twin) => Assert.Equal(twin, MirrorPairs.Pair(name));

    [Theory]
    [InlineData("hand_l")]
    [InlineData("upperarm.R")]
    [InlineData("index_01_l_end")]
    [InlineData("RightFoot")]
    [InlineData("pelvis")]
    public void TwinOfTwinIsSelf(string name) => Assert.Equal(name, MirrorPairs.Pair(MirrorPairs.Pair(name)));
}
