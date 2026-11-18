using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Rpg;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The owner, 17 Nov: "hide all 3 besides warden for demo." On body B the demo's starting kit dresses her in the
/// Warden set only: the Prologue's watch chest and the dev veteran's kit give the padded jerkin (or the chain shirt), whose
/// pieces are the ranger's; data/body/her_body.json "outfits_hidden_on_b" keeps them off B (HerWear.LookFor), A unchanged.</summary>
public class HiddenOnBWearTests
{
    // (what the demo start can put on her: the Prologue's chest (Prologue.cs, Prologue.Day.cs: padded_jerkin) and the dev
    // veteran's dress (DevVeteran.cs: iron_helm or leather_cap, chain_shirt or padded_jerkin, travelers_boots))
    static readonly string[][] Kits =
    [
        ["padded_jerkin"],
        ["iron_helm", "chain_shirt", "travelers_boots"],
        ["leather_cap", "padded_jerkin", "travelers_boots"],
        ["iron_helm", "padded_jerkin", "travelers_boots"],
        ["leather_cap", "chain_shirt", "travelers_boots"],
    ];
    static readonly string[] Hidden = ["ranger", "reaver", "arcanist"];

    static Equipment Dress(string[] kit)
    {
        var eq = new Equipment();
        int uid = 1;
        foreach (var id in kit)
        {
            var def = Items.Find(id);
            Assert.NotNull(def);
            eq[Items.SlotFor(def!)!.Value] = new ItemInstance { Uid = (uid++).ToString(), Def = id };
        }
        return eq;
    }

    [Fact]
    public void Her_body_data_hides_the_three_other_outfits_on_B()
    {
        Assert.Equal(Hidden.OrderBy(x => x), Wear.OutfitsHiddenOnB.OrderBy(x => x));
    }

    [Fact]
    public void The_demo_start_on_B_wears_no_ranger_reaver_or_arcanist_piece()
    {
        var ix = ArmorIndex.Load(ArmorIndex.Text);
        foreach (var kit in Kits)
        {
            var worn = Wear.Of(Dress(kit));
            var onB = Wear.Look(Wear.Without(worn, ix, Wear.OutfitsHiddenOnB), "warden", ix);
            var bad = onB.Values.Where(id => Hidden.Contains(ix.Find(id)?.Outfit)).ToList();
            Assert.True(bad.Count == 0, $"{string.Join(",", kit)} on B shows {string.Join(",", bad)}");
            Assert.Equal("warden.top", onB["top"]);
        }
    }

    [Fact]
    public void On_A_the_jerkin_still_shows_its_own_top()
    {
        // (A untouched: no filter, the jerkin's ranger.top is drawn as before)
        var ix = ArmorIndex.Load(ArmorIndex.Text);
        var onA = Wear.Look(Wear.Of(Dress(["padded_jerkin"])), "warden", ix);
        Assert.Equal("ranger.top", onA["top"]);
        // (and an empty list is the one switch back)
        var back = Wear.Look(Wear.Without(Wear.Of(Dress(["padded_jerkin"])), ix, new List<string>()), "warden", ix);
        Assert.Equal("ranger.top", back["top"]);
    }
}
