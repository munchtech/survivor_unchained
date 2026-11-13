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
    [InlineData(0, 3)] [InlineData(1, 4)] [InlineData(2, 5)] [InlineData(6, 9)] [InlineData(7, 9)] [InlineData(40, 9)]
    public void The_row_holds_her_three_then_the_item_places_from_1012(int items, int places) =>
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
    public void Item_autos_grow_right_from_1012_and_never_pass_the_statue_edge_1263()
    {
        var p = AutoRowModel.Places(3);
        Assert.Equal(1012, p[3].X);
        Assert.Equal(p[3].X + 40, p[4].X);
        Assert.Equal(p[4].X + 40, p[5].X);
        foreach (float start in new[] { 1012f, 1100f, 1111f })
            Assert.All(AutoRowModel.Places(9, start).Where(x => x.Kind != AutoRowModel.Kind.Her), x => Assert.True(x.X + 34 <= 1263 && x.X >= start));
        Assert.All(AutoRowModel.Places(9).Where(x => x.Kind == AutoRowModel.Kind.Her), x => Assert.True(x.X < 1008));
    }

    [Fact]
    public void The_item_tiles_start_10_px_after_the_swap_chip_or_at_1012_without_the_stance_block()
    {
        Assert.Equal(1100, AutoRowModel.ItemStart(true, 1090));
        Assert.Equal(1012, AutoRowModel.ItemStart(false, 1090));
        Assert.Equal(1100, AutoRowModel.Places(1, AutoRowModel.ItemStart(true, 1090))[3].X);
        Assert.Equal(6, AutoRowModel.ItemCapacity(1012));
        Assert.Equal(4, AutoRowModel.ItemCapacity(1100));
    }

    [Theory]
    [InlineData(7, 2)] [InlineData(8, 3)] [InlineData(10, 5)]
    public void With_more_items_than_places_the_last_place_shows_plus_N(int items, int rest)
    {
        var p = AutoRowModel.Places(items);
        Assert.Equal(AutoRowModel.Kind.Item, p[7].Kind);
        Assert.Equal(AutoRowModel.Kind.More, p[8].Kind);
        Assert.Equal(rest, p[8].Index);
        // (4 places from the swap chip: three items and "+N")
        var q = AutoRowModel.Places(items, 1100);
        Assert.Equal(AutoRowModel.Kind.More, q[^1].Kind);
        Assert.Equal(items - 3, q[^1].Index);
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
    public void The_row_bottom_stands_12_px_above_the_key_caps_top_edge()
    {
        float capTop = AutoRowModel.CapTop(TopY, SeatY, SeatR, Chip);
        float top = AutoRowModel.RowTop(TopY, SeatY, SeatR, Chip);
        Assert.True(top + AutoRowModel.Tile < capTop);
        Assert.Equal(capTop - 12, top + AutoRowModel.Tile, 0.001f);
        // (the shorter key chips (16 tall) are cleared too)
        Assert.True(top + AutoRowModel.Tile < AutoRowModel.CapTop(TopY, SeatY, SeatR, 16));
    }

    [Fact]
    public void The_status_shelf_rises_to_6_px_over_the_tiles()
    {
        float top = AutoRowModel.RowTop(TopY, SeatY, SeatR, Chip);
        float raise = AutoRowModel.ShelfRaise(top);
        Assert.True(raise > 0);
        Assert.Equal(top - 6, AutoRowModel.ShelfBottom - raise, 0.001f);
        Assert.Equal(0, AutoRowModel.ShelfRaise(2000));   // (a row far below: nothing to clear)
    }

    [Fact]
    public void The_tiers_stack_cap_row_shelf_card_with_their_gaps()
    {
        float top = AutoRowModel.RowTop(TopY, SeatY, SeatR, Chip);
        Assert.Equal(top - 6 - 30, AutoRowModel.ShelfTop(top), 0.001f);
        Assert.Equal(AutoRowModel.ShelfTop(top) - 8, AutoRowModel.CardBottom(top), 0.001f);
        Assert.Equal(8, SurvivorUnchained.Ui.LevelCardPlace.Clear);
    }

    [Fact]
    public void The_tile_timer_bar_fills_with_the_ready_share_and_the_fire_cue_is_120_ms()
    {
        Assert.Equal(0f, AutoRowModel.BarFill(0));
        Assert.Equal(14f, AutoRowModel.BarFill(0.5), 0.001f);
        Assert.Equal(28f, AutoRowModel.BarFill(2), 0.001f);
        Assert.Equal(1.6f, AutoRowModel.FireModulate(0), 0.001f);
        Assert.Equal(1.15f, AutoRowModel.FireScale(0), 0.001f);
        Assert.Equal(1f, AutoRowModel.FireScale(0.12));
        Assert.Equal(1f, AutoRowModel.FireModulate(-1));
    }
}
