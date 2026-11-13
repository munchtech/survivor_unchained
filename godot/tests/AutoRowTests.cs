using System.Linq;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>bd-ui W4: the campaign bar's auto row, as numbers: its places, the "+N", the ready share, the row clear of the key
/// caps, the status shelf raised over it.</summary>
public class AutoRowTests
{
    const float TopY = 1003, SeatY = 1042, SeatR = 35, Chip = 21;

    [Theory]
    [InlineData(0, 3)] [InlineData(1, 4)] [InlineData(2, 5)] [InlineData(3, 5)] [InlineData(6, 5)]
    public void The_row_holds_her_three_then_up_to_two_item_places(int items, int places) =>
        Assert.Equal(places, AutoRowModel.Places(items).Count);

    [Fact]
    public void Her_tiles_grow_left_from_the_coin_at_34_px_with_a_6_px_gap()
    {
        var p = AutoRowModel.Places(0);
        Assert.Equal(34, AutoRowModel.Tile);
        Assert.Equal(910 - 34, p[0].X);
        Assert.Equal(p[0].X - 40, p[1].X);
        Assert.Equal(p[1].X - 40, p[2].X);
        Assert.All(p, x => Assert.Equal(AutoRowModel.Kind.Her, x.Kind));
    }

    [Fact]
    public void Item_autos_continue_leftward_and_stay_inside_the_floor()
    {
        var p = AutoRowModel.Places(2);
        Assert.Equal(p[2].X - 40, p[3].X);
        Assert.Equal(p[3].X - 40, p[4].X);
        Assert.All(AutoRowModel.Places(9), x => Assert.True(x.X >= AutoRowModel.Floor));
    }

    [Theory]
    [InlineData(3, 2)] [InlineData(4, 3)] [InlineData(9, 8)]
    public void More_than_two_item_autos_show_the_first_and_a_plus_N_for_the_rest(int items, int rest)
    {
        var p = AutoRowModel.Places(items);
        Assert.Equal(AutoRowModel.Kind.Item, p[3].Kind);
        Assert.Equal(AutoRowModel.Kind.More, p[4].Kind);
        Assert.Equal(rest, p[4].Index);
    }

    [Fact]
    public void The_ready_share_darkens_what_is_not_ready_and_a_fire_is_seen()
    {
        Assert.Equal(0f, AutoRowModel.NotReady(1));
        Assert.Equal(0.75f, AutoRowModel.NotReady(0.25), 0.001f);
        Assert.Equal(1f, AutoRowModel.NotReady(-2));
        Assert.True(AutoRowModel.Fired(1, 0.1));
        Assert.False(AutoRowModel.Fired(0.5, 0.1));
        Assert.Equal(1f, AutoRowModel.Flash(0));
        Assert.Equal(0f, AutoRowModel.Flash(0.25));
    }

    [Fact]
    public void The_row_bottom_stands_3_px_above_the_key_caps_top_edge()
    {
        float capTop = AutoRowModel.CapTop(TopY, SeatY, SeatR, Chip);
        float top = AutoRowModel.RowTop(TopY, SeatY, SeatR, Chip);
        Assert.True(top + AutoRowModel.Tile < capTop);
        Assert.Equal(capTop - 3, top + AutoRowModel.Tile, 0.001f);
        // (the shorter key chips (16 tall) are cleared too)
        Assert.True(top + AutoRowModel.Tile < AutoRowModel.CapTop(TopY, SeatY, SeatR, 16));
    }

    [Fact]
    public void The_status_shelf_rises_to_5_px_over_the_tiles()
    {
        float top = AutoRowModel.RowTop(TopY, SeatY, SeatR, Chip);
        float raise = AutoRowModel.ShelfRaise(top);
        Assert.True(raise > 0);
        Assert.Equal(top - 5, AutoRowModel.ShelfBottom - raise, 0.001f);
        Assert.Equal(0, AutoRowModel.ShelfRaise(2000));   // (a row far below: nothing to clear)
    }
}
