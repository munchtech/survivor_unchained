using System.Linq;
using System.Numerics;
using SurvivorUnchained.Cinema;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The dip hand-back (GameSeam): a film whose last shot does not hold her dips to black and rises on the
/// play camera; every other film eases (the one cut rule). CineHandover.Dips decides.</summary>
public class CineDipTests
{
    static readonly Vector3 Fwd = new(0, 0, -1), Up = Vector3.UnitY;
    const double Vfov = 34, Aspect = 16 / 9.0;
    static bool Dips(Vector3 her, string camera = "follow") => CineHandover.Dips(camera, Vector3.Zero, Fwd, Up, Vfov, Aspect, her);

    [Fact]
    public void A_last_frame_that_holds_her_near_eases()
    {
        Assert.False(Dips(new Vector3(0, 0, -10)));
        Assert.False(Dips(new Vector3(2, -1, -24)));
    }

    [Fact]
    public void A_last_frame_over_25_m_from_her_dips_even_with_her_in_it()
    {
        Assert.True(Dips(new Vector3(0, 0, -25.5f)));
        Assert.True(Dips(new Vector3(126, 0, 0)));   // (C15: places in the Verge, she stands 126 m off)
    }

    [Fact]
    public void A_last_frame_she_is_outside_dips()
    {
        Assert.True(Dips(new Vector3(0, 0, 5)));        // behind the lens
        Assert.True(Dips(new Vector3(12, 0, -10)));     // off the right edge (half-width tan 17 deg * 16/9 = 0.54)
        Assert.True(Dips(new Vector3(0, 4, -10)));      // over the top (tan 17 deg = 0.31)
        Assert.False(Dips(new Vector3(5, 0, -10)));     // inside the right edge
    }

    [Fact]
    public void The_end_can_ask_for_the_dip_and_a_hidden_her_never_forces_one()
    {
        Assert.True(Dips(new Vector3(0, 0, -10), "dip"));
        Assert.False(CineHandover.Dips("follow", Vector3.Zero, Fwd, Up, Vfov, Aspect, null));
    }

    [Fact]
    public void Every_film_ends_on_follow_or_dip_and_the_prologue_films_ease()
    {
        foreach (var id in new[] { "c01", "c02", "c03", "c04a", "c04b", "c15" })
        {
            var f = CineFile.Load(id);
            Assert.Contains(f.End.Camera, new[] { "follow", "dip" });
            if (id != "c15") Assert.Equal("follow", f.End.Camera);
        }
    }
}
