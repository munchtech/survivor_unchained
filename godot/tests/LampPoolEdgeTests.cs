using SurvivorUnchained.Sim;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

public class LampPoolEdgeTests
{
    static SurvivorUnchained.Sim.LampMark L(bool caught, bool lit) => new() { X = 10, Z = -4, Pool = 5, Caught = caught, Lit = lit };

    [Fact]
    public void Caught_lit_and_outside_shows_it()
    {
        Assert.True(LampPoolEdge.Show(L(true, true), 16, -4));
        Assert.True(LampPoolEdge.Show(L(true, true), 10, 2));
    }

    [Fact]
    public void Inside_or_on_the_edge_hides_it()
    {
        Assert.False(LampPoolEdge.Show(L(true, true), 10, -4));
        Assert.False(LampPoolEdge.Show(L(true, true), 14, -4));
        Assert.False(LampPoolEdge.Show(L(true, true), 15, -4));
    }

    [Fact]
    public void Unlit_uncaught_or_no_lamp_hides_it()
    {
        Assert.False(LampPoolEdge.Show(L(true, false), 30, 30));
        Assert.False(LampPoolEdge.Show(L(false, true), 30, 30));
        Assert.False(LampPoolEdge.Show(L(false, false), 30, 30));
        Assert.False(LampPoolEdge.Show(null, 30, 30));
    }

    [Fact]
    public void It_fades_in_and_out_over_a_fifth_of_a_second()
    {
        float a = 0;
        for (int i = 0; i < 6; i++) a = LampPoolEdge.Step(a, true, 0.02f);
        Assert.Equal(0.6f, a, 0.001f);
        for (int i = 0; i < 20; i++) a = LampPoolEdge.Step(a, true, 0.02f);
        Assert.Equal(1f, a);
        for (int i = 0; i < 10; i++) a = LampPoolEdge.Step(a, false, 0.02f);
        Assert.Equal(0f, a, 0.001f);
    }
}
