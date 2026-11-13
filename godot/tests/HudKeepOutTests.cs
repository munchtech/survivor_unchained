using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Ground labels give way to the instrument's pieces only (gems judge round 4: one rectangle around the whole
/// instrument took in the open ground between the girl and the keeper, and a gem's name there faded to 14%).</summary>
public class HudKeepOutTests
{
    // The default geometry (DgPanel's fallbacks): the girl's head near (220, 760), the bar, the keeper.
    static readonly (float X, float Y, float W, float H)[] Pieces =
        HudKeepOut.Pieces((220, 760), (576, 988, 768, 92), (1254, 873, 341, 207));

    [Fact]
    public void A_label_on_the_open_ground_between_the_girl_and_the_keeper_keeps_full_strength()
    {
        // land_29's "Brutality gem": above the bar's buff shelf, right of the girl, left of the keeper
        Assert.False(HudKeepOut.Under((895, 905, 130, 20), Pieces));
        Assert.False(HudKeepOut.Under((600, 880, 140, 20), Pieces));
        Assert.False(HudKeepOut.Under((1100, 800, 130, 20), Pieces));
    }

    [Fact]
    public void A_label_over_a_piece_gives_way()
    {
        Assert.True(HudKeepOut.Under((900, 1000, 130, 20), Pieces));   // the bar
        Assert.True(HudKeepOut.Under((900, 935, 130, 20), Pieces));    // the buff shelf over it
        Assert.True(HudKeepOut.Under((300, 900, 130, 20), Pieces));    // the girl
        Assert.True(HudKeepOut.Under((1300, 900, 130, 20), Pieces));   // the keeper
    }
}
