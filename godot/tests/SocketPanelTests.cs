using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>bd-ui W11: the socket panel's plain-C# side (Rpg/SocketModel.cs).</summary>
public sealed class SocketPanelTests
{
    [Fact]
    public void Gem_colours_by_kind()
    {
        Assert.Equal("#E6EEFF", SocketModel.GemHex(Supports.Find("haste")!));
        Assert.Equal("#3F7FD8", SocketModel.GemHex(Supports.Find("bulwark")!));
        Assert.Equal("#C42B3A", SocketModel.GemHex(Supports.Find("brutality")!));
    }

    [Fact]
    public void The_head_note_follows_the_rank()
    {
        Assert.Equal("rank III opens the first, VI the second", SocketModel.Note(2));
        Assert.Equal("rank III opens the first, VI the second", SocketModel.Note(4));
        Assert.Equal("both open", SocketModel.Note(6));
    }

    [Fact]
    public void The_rank_line_says_what_gear_adds()
    {
        Assert.Equal("rank III", SocketModel.RankLine(3, 3));
        Assert.Equal("rank IV (III, and +1 from your gear)", SocketModel.RankLine(3, 4));
    }

    [Fact]
    public void The_chooser_lists_the_gems_that_fit_with_free_counts_and_the_ones_that_do_not()
    {
        var s = new SupportState();
        s.Owned["brutality"] = 2; s.Owned["haste"] = 1; s.Owned["bulwark"] = 3;
        var melee = Weapons.All.Values.First(w => w.Tags.Contains(Sim.Tag.Melee) && !w.Tags.Contains(Sim.Tag.Shield)).Id;
        Assert.True(Supports.Socket(s, melee, 6, 0, "brutality"));
        var (rows, dont) = SocketModel.Chooser(s, melee, 1);
        Assert.Equal(3, dont); // bulwark fits Shield only
        var br = rows.Single(r => r.Gem.Id == "brutality");
        Assert.Equal((2, 1), (br.Owned, br.Free));
        Assert.Equal(1, rows.Single(r => r.Gem.Id == "haste").Free);
        // the socket that holds it marks it "set here"; its copy is not free
        var here = SocketModel.Chooser(s, melee, 0).Rows.Single(r => r.Gem.Id == "brutality");
        Assert.True(here.Here); Assert.Equal(1, here.Free);
        Assert.Equal("3 of your gems don't fit Sunder.", SocketModel.DontFitLine(3, "Sunder"));
        Assert.Equal("1 of your gems doesn't fit Sunder.", SocketModel.DontFitLine(1, "Sunder"));
    }

    [Fact]
    public void A_gem_with_no_free_copy_shows_zero_free()
    {
        var s = new SupportState();
        s.Owned["haste"] = 1;
        Assert.True(Supports.Socket(s, "sunder", 6, 0, "haste"));
        Assert.Equal(0, SocketModel.Chooser(s, "heroic_leap", 0).Rows.Single().Free);
    }

    [Fact]
    public void More_room_comes_where_the_ladder_grows()
    {
        Assert.Equal(new[] { 4, 5, 7, 9, 10 }, SocketModel.MoreRoom(1));
        Assert.Equal(new[] { 9, 10 }, SocketModel.MoreRoom(8));
        Assert.Equal("More room comes at the ninth and the tenth level.", SocketModel.MoreRoomLine(8));
        Assert.Equal("More room comes at the seventh, the ninth and the tenth level.", SocketModel.MoreRoomLine(5));
        Assert.Equal("", SocketModel.MoreRoomLine(12));
    }

    [Fact]
    public void Ordinals_read_as_words()
    {
        Assert.Equal("twelfth", SocketModel.Ordinal(12));
        Assert.Equal("twentieth", SocketModel.Ordinal(20));
        Assert.Equal("twenty-first", SocketModel.Ordinal(21));
    }

    [Fact]
    public void A_union_has_its_two_halves_and_a_plain_skill_has_none()
    {
        Assert.Equal(("heroic_leap", "shield_charge"), SocketModel.Halves("falling_wall"));
        Assert.Null(SocketModel.Halves("heroic_leap"));
    }
}
