using System.IO;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The owner, 22 Nov: the level coin became the fifth ability seat and a plain thin XP bar replaced its ring. DgPanel
/// itself is Godot-side, so these pin its numbers where they live: the geo's four seats around the coin, the seat order,
/// the arena's six, and the bar's place in the gap over the key caps.</summary>
public class HudFiveSeatsTests
{
    static JsonElement Panel()
    {
        var d = new DirectoryInfo(System.AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(d!.FullName, "art", "ui", "dg_keeper", "hud_a_geo.json")));
        return doc.RootElement.GetProperty("panel").Clone();
    }

    [Fact]
    public void The_campaign_has_five_seats_the_fifth_in_the_coins_middle_and_the_arena_six()
    {
        var p = Panel();
        var four = p.GetProperty("seats4").EnumerateArray().Select(a => (a[0].GetDouble(), a[1].GetDouble())).ToArray();
        var c = p.GetProperty("coin").GetProperty("center");
        double cx = c[0].GetDouble(), cy = c[1].GetDouble();
        Assert.Equal(4, four.Length);
        Assert.Equal(5, Weapons.MaxKeys);                       // four from the geo + the coin's seat = five
        Assert.Equal(Weapons.MaxKeys, KeyMap.SeatSlot.Length);
        Assert.Equal(4, KeyMap.SeatSlot[4]);                    // the last seat index (DgPanel.CoinSeat) is the fifth key
        Assert.Equal(cx, (four[1].Item1 + four[2].Item1) / 2, 1);   // the coin stands midway between the pairs
        Assert.All(four, s => Assert.Equal(cy, s.Item2, 1));    // one row: the fifth seat shares it
        Assert.Equal(6, p.GetProperty("seats").GetArrayLength());
        Assert.Equal(6, Weapons.MaxWeapons);
    }

    [Fact]
    public void The_fifth_seat_is_clear_of_its_neighbours_and_the_plate_order_is_one_two_fifth_lmb_rmb()
    {
        var p = Panel();
        var four = p.GetProperty("seats4").EnumerateArray().Select(a => a[0].GetDouble()).ToArray();
        double cx = p.GetProperty("coin").GetProperty("center")[0].GetDouble(), r = p.GetProperty("seat_r").GetDouble();
        Assert.True(four[1] + r < cx - r && cx + r < four[2] - r);   // no seat's bezel meets the fifth's
        // plate order: seat indices 0,1 (Skill3, Skill4), the fifth key, then 2,3 (Skill1, Skill2)
        Assert.Equal(new[] { Act.Skill3, Act.Skill4, Act.Skill5, Act.Skill1, Act.Skill2 }, new[] { 0, 1, 4, 2, 3 }.Select(k => KeyMap.Skills[KeyMap.SeatSlot[k]]));
    }

    [Fact]
    public void The_xp_bar_is_5_px_in_the_gap_over_the_key_caps_and_under_the_stance_ring()
    {
        float capTop = AutoRowModel.CapTop(1003, 1042, 35, 21);
        float top = AutoRowModel.XpBarTop(capTop);
        Assert.Equal(5, AutoRowModel.XpBarH);
        Assert.True(top + AutoRowModel.XpBarH < capTop);                              // clear of the caps
        float rowTop = AutoRowModel.RowTop(1003, 1042, 35, 21);
        // the stance disc (r 20, centred on the row's middle) and its ring (4 out) end above the bar
        Assert.True(rowTop + AutoRowModel.Tile / 2 + AutoRowModel.StanceR + 4 < top);
        Assert.True(AutoRowModel.XpBarX0 >= AutoRowModel.Floor && AutoRowModel.XpBarX1 - AutoRowModel.XpBarX0 > 400);
    }
}
