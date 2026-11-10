using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>M9 loot (docs/design/ARPG.md 7.1, 7.3): a zone left gives Rare and better lying to Rook's storeroom; a story
/// night no longer tallies its materials; the world tier's drop weights.</summary>
public class LootM9ZoneTests
{
    static Journey Begin()
    {
        var a = Callings.Archetype("warden");
        return Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 42);
    }

    static ItemInstance At(string def, int rarity, int level, uint seed = 7) => Inventory.Make(null, def, rarity: rarity, seed: seed, level: level);

    static Pickup Lay(Battle b, ItemInstance it, Verdict look, double x)
    {
        var tier = (int)Drops.TierOf(it);
        var p = b.Spill(new Sim.Loot(PickupKind.Item, it.Def, 1, true, it.Rarity, null, it, tier, look), x, 30)!;
        Assert.Equal(look, p.Look);
        return p;
    }

    [Fact]
    public void A_zone_left_stores_shown_rare_and_better_and_leaves_the_rest_lying()
    {
        var j = Begin();
        var b = j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3);
        int toasts = 0;
        j.OnToast = t => { if (t.Text.StartsWith("Rook kept")) toasts++; };
        var rare = Lay(b, At("iron_helm", 2, 5, 1), Verdict.Shown, 30);
        var common = Lay(b, At("leather_cap", 0, 5, 2), Verdict.Shown, 32);
        var unc = Lay(b, At("iron_helm", 1, 5, 3), Verdict.Shown, 34);
        var hiddenRare = Lay(b, At("iron_helm", 2, 5, 4), Verdict.Hidden, 36);
        var legend = Lay(b, At("drowned_coat", 4, 5, 5), Verdict.Shown, 38);
        int kept = j.Abandon(b);
        Assert.Equal(2, kept);
        Assert.Equal(1, toasts);
        Assert.False(rare.Alive);
        Assert.False(legend.Alive);
        Assert.True(common.Alive && unc.Alive && hiddenRare.Alive);
        Assert.Equal(2, j.World.Stash.Count(s => s != null));
        Assert.Equal(0, j.Abandon(b));
    }

    [Fact]
    public void A_full_storeroom_leaves_the_piece_lying()
    {
        var j = Begin();
        for (int i = 0; i < j.World.Stash.Count; i++) j.World.Stash[i] = At("iron_helm", 1, 1, (uint)(100 + i));
        int size = j.World.Stash.Count;
        var b = j.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3);
        var rare = Lay(b, At("iron_helm", 2, 5, 1), Verdict.Shown, 30);
        Assert.Equal(0, j.Abandon(b));
        Assert.True(rare.Alive);
        Assert.Equal(size, j.World.Stash.Count);
    }

    [Fact]
    public void Without_the_tally_a_story_nights_materials_fall_as_loot_and_the_arena_tallies()
    {
        var j = Begin();
        int mats = 0;
        for (int s = 0; s < 300; s++)
            mats += j.Drops(new DropCtx { Source = DropSource.Champion, Level = 4, People = "pack", R = new Random(s).NextDouble }).Count(l => l.Kind == PickupKind.Material);
        Assert.True(mats > 20);
        Assert.Empty(j.NightTally);
        for (int s = 0; s < 300; s++)
            j.Drops(new DropCtx { Source = DropSource.Champion, Level = 4, People = "pack", Tally = true, R = new Random(s).NextDouble });
        Assert.True(j.NightTally.Values.Sum() > 20);
    }

    static (double Rare, double Legend, double Level) Rolls(int tier, bool on)
    {
        var j = Begin();
        j.World.Facts["act1.done"] = true;
        j.World.Facts["campaign.done"] = true;
        Assert.True(WorldTiers.Set(j.World, tier));
        j.WorldTierOn = on;
        int gear = 0, rare = 0, legend = 0; double lv = 0;
        for (int s = 0; s < 4000; s++)
            foreach (var l in j.Drops(new DropCtx { Source = s % 2 == 0 ? DropSource.Boss : DropSource.Champion, Level = 8, People = "pack", Hush = true, R = new Random(s).NextDouble }))
            {
                if (l.Payload is not ItemInstance it || Items.SlotFor(Items.Get(it.Def)) == null) continue;
                gear++;
                if (it.Rarity >= 2) rare++;
                if (l.Tier is int t && Rpg.Drops.Jackpot((LootTier)t)) legend++;
                lv += Rpg.Drops.LevelOf(it);
            }
        return (rare / (double)gear, legend / (double)gear, lv / gear);
    }

    [Fact]
    public void World_tiers_raise_rare_and_legendary_shares_and_item_level()
    {
        var r = Enumerable.Range(1, 4).Select(t => Rolls(t, true)).ToArray();
        Assert.True(r[1].Rare > r[0].Rare, "II > I");
        Assert.True(r[2].Rare > r[1].Rare, "III > II");
        Assert.True(r[3].Rare > r[2].Rare, "IV > III");
        Assert.True(r[2].Legend > r[1].Legend, "legendary at III");
        Assert.True(r[3].Legend > r[2].Legend, "legendary at IV");
        Assert.InRange(r[2].Level - r[1].Level, 4.0, 6.0);
        Assert.InRange(r[3].Level - r[1].Level, 9.0, 11.0);
        // Off (an arena or a map), the tier is ignored.
        var off = Enumerable.Range(1, 4).Select(t => Rolls(t, false)).ToArray();
        Assert.All(off, o => Assert.Equal(off[0], o));
    }
}
