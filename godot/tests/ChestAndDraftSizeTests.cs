using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>SU-081: a chest pays every unused slot. SU-082: a draft keeps its size and
/// the advancement guarantee replaces the lowest-priority guarantee.</summary>
public class ChestAndDraftSizeTests
{
    [Fact]
    public void A_chest_with_nothing_to_rank_pays_every_slot_and_one_draught()
    {
        var b = BattleTests.Arena(3, ("oathblade", Content.Weapons.MaxRank));
        foreach (var w in b.Weapons) w.Rank = Content.Weapons.MaxRank;
        b.Player.Hp = b.MaxHp * 0.2;
        double hp0 = b.Player.Hp, gold0 = b.GoldGained;
        var got = LevelUp.OpenChest(b, 3);
        var golds = got.Where(i => i.Kind == ChestItemKind.Gold).ToList();
        Assert.Single(golds);
        Assert.Equal(gold0 + 75, b.GoldGained);
        Assert.StartsWith("75 gold", golds[0].Name);
        Assert.Equal(hp0 + b.MaxHp * 0.3, b.Player.Hp, 3);
    }

    [Fact]
    public void A_full_draft_of_guarantees_still_offers_a_card_that_advances_and_stays_three()
    {
        var b = BattleTests.Arena(5);
        // Two carried weapons at rank 7 waiting on different passives, none held.
        var withCat = Content.Weapons.Pool.Where(id => Content.Weapons.CanCarry(b.Calling, id) && LevelUp.EvolvesWith(id).Any()).ToList();
        string a = withCat[0];
        string c = withCat.First(id => id != a && !LevelUp.EvolvesWith(id).SelectMany(e => e.Passives).Intersect(LevelUp.EvolvesWith(a).SelectMany(e => e.Passives)).Any());
        string att = Content.Weapons.Pool.First(id => id != a && id != c && Content.Weapons.CanCarry(b.Calling, id));
        b.Weapons.Clear();
        b.AddWeapon(a, 7);
        b.AddWeapon(c, 7);
        b.Attuned[att] = 3;
        b.Drafting.SkillDrafts = 0;
        b.Drafting.CatalystWait[a] = LevelUp.CatalystPity;
        b.Drafting.CatalystWait[c] = LevelUp.CatalystPity;
        var offers = LevelUp.Draft(b, 3);
        Assert.Equal(3, offers.Count);
        Assert.Contains(offers, o => o.Kind is OfferKind.Rank or OfferKind.Evolve or OfferKind.Hone || (o.Kind == OfferKind.Boon && !o.Blessing && o.From > 0));
    }
}
