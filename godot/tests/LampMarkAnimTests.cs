using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

public class LampMarkAnimTests
{
    [Fact]
    public void Steady_lit_is_full_brightness_and_normal_halo()
    {
        Assert.Equal(1f, LampMarkAnim.Brightness(true, float.PositiveInfinity), 0.001f);
        Assert.Equal(1f, LampMarkAnim.HaloScale(true, float.PositiveInfinity), 0.001f);
        Assert.Equal(0f, LampMarkAnim.Brightness(false, float.PositiveInfinity), 0.001f);
    }

    [Fact]
    public void Going_out_flares_then_fades_to_dark()
    {
        Assert.InRange(LampMarkAnim.Brightness(false, 0.1f), 1.3f, 1.4001f);
        Assert.Equal(1.4f, LampMarkAnim.Brightness(false, 0.12f), 0.001f);
        Assert.True(LampMarkAnim.Brightness(false, 0.4f) < 1.4f);
        Assert.Equal(0f, LampMarkAnim.Brightness(false, 0.62f), 0.001f);
    }

    [Fact]
    public void Relight_blooms_then_settles()
    {
        Assert.Equal(1.7f, LampMarkAnim.HaloScale(true, 0.2f), 0.001f);
        Assert.True(LampMarkAnim.HaloScale(true, 0.5f) < 1.7f && LampMarkAnim.HaloScale(true, 0.5f) > 1f);
        Assert.Equal(1f, LampMarkAnim.HaloScale(true, 0.8f), 0.001f);
        Assert.Equal(1f, LampMarkAnim.Brightness(true, 0.2f), 0.001f);
    }

    [Fact]
    public void Targets_light_from_the_left()
    {
        Assert.Equal(new[] { true, true, false }, LampMarkAnim.Targets(3, 2));
    }
}
