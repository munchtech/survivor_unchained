using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>What the ember draft promises (Sim/LevelUp.cs, docs/SKILLS_DESIGN.md
/// "The offer"): the guarantees that keep a draft from being a dud, the
/// leans that keep it from being a lottery, and the tools that keep it the
/// player's.</summary>
public class OfferTests
{
    /// <summary>A level's own skill draft owed.</summary>
    static void Owe(Battle b)
    {
        if (b.EmberLevel < 2) b.EmberLevel = 2;
        b.PendingLevels = Math.Max(1, b.PendingLevels);
    }

    static bool Advances(Offer o) => o.Kind is OfferKind.Rank or OfferKind.Evolve or OfferKind.Hone or OfferKind.Union || (o.Kind == OfferKind.Boon && !o.Blessing && o.From > 0);

    /// <summary>A whole arena's worth of drafts, taken at random: every one keeps its promises.</summary>
    [Fact]
    public void Every_skill_draft_keeps_its_promises()
    {
        var rng = new Random(5);
        for (uint seed = 1; seed <= 12; seed++)
        {
            var b = BattleTests.Arena(seed);
            for (int level = 0; level < 60; level++)
            {
                b.GainEmber(b.EmberNext - b.EmberXp + 0.01);
                while (b.DraftOwed)
                {
                    bool skill = LevelUp.SkillNext(b);
                    var offers = LevelUp.Draft(b);
                    Assert.NotEmpty(offers);
                    // Never the same card twice in one draft.
                    Assert.Equal(offers.Count, offers.Select(LevelUp.Key).Distinct().Count());
                    if (skill)
                    {
                        Assert.InRange(offers.Count, 3, 4);
                        // An evolution or union earned always comes.
                        if (b.Weapons.Any(w => LevelUp.EarnedBranches(b, w.Id).Count > 0))
                            Assert.Contains(offers, o => o.Kind == OfferKind.Evolve);
                        else if (LevelUp.ReadyUnions(b).Any())
                            Assert.Contains(offers, o => o.Kind == OfferKind.Union);
                        // Always a combat skill, while there is one to offer.
                        bool honable(WeaponInst w) => w.Rank >= Weapons.MaxRank && (w.Evolution != null || w.Def.Evolutions.Length == 0) && w.Honed < LevelUp.MaxHone;
                        bool newLeft = b.Weapons.Count < Weapons.MaxWeapons && Weapons.Pool.Any(id => !b.Weapons.Exists(w => w.Id == id) && !b.BannedCards.Contains(id));
                        bool combatLeft = newLeft || b.Weapons.Any(w => w.Rank < Weapons.MaxRank || honable(w));
                        if (combatLeft) Assert.Contains(offers, o => o.Kind is OfferKind.Weapon or OfferKind.Rank or OfferKind.Evolve or OfferKind.Hone or OfferKind.Union);
                        // Until three are carried, a new one.
                        if (b.Weapons.Count < 3 && newLeft) Assert.Contains(offers, o => o.Kind == OfferKind.Weapon);
                        // Once two are carried, something that ranks what is carried.
                        bool advanceLeft = b.Weapons.Any(w => w.Rank < Weapons.MaxRank || honable(w)) ||
                            b.Boons.Any(kv => Boons.Find(kv.Key) is { Kind: BoonKind.Passive } d && kv.Value < d.Max && !b.BannedCards.Contains(kv.Key));
                        if (b.Weapons.Count >= 2 && advanceLeft) Assert.Contains(offers, Advances);
                    }
                    LevelUp.Choose(b, offers[rng.Next(offers.Count)]);
                }
            }
        }
    }

    [Fact]
    public void A_weapon_ready_to_evolve_never_waits_long_for_its_passive()
    {
        int worst = 0;
        for (uint seed = 1; seed <= 40; seed++)
        {
            var b = BattleTests.Arena(seed, ("volley", Weapons.MaxRank - 1), ("rimeshard", 3), ("seeking_motes", 3));
            int waited = 0;
            for (int d = 0; d < 12; d++)
            {
                Owe(b);
                var offers = LevelUp.Draft(b);
                if (offers.Any(o => o.Kind == OfferKind.Boon && o.Id is "velocity" or "precision")) break;
                waited++;
                // Take anything but the passive it waits for (and not a rank of it, so it stays waiting at 7).
                LevelUp.Choose(b, offers.FirstOrDefault(o => !(o.Kind == OfferKind.Rank && o.Id == "volley")) ?? offers[0]);
            }
            worst = Math.Max(worst, waited);
        }
        Assert.True(worst <= LevelUp.CatalystPity, $"waited {worst} drafts");
    }

    [Fact]
    public void Unions_come_when_both_halves_are_evolved_and_free_a_slot()
    {
        var b = BattleTests.Arena(3, ("cinderfall", Weapons.MaxRank), ("rimeshard", Weapons.MaxRank), ("volley", 2));
        b.Evolve("cinderfall", "fallen_star");
        Assert.Empty(LevelUp.ReadyUnions(b));
        b.Evolve("rimeshard", "deepwinter");
        Owe(b);
        var union = Assert.Single(LevelUp.Draft(b), o => o.Kind == OfferKind.Union);
        Assert.Equal("frostfire_comet", union.Id);
        LevelUp.Choose(b, union);
        Assert.DoesNotContain(b.Weapons, w => w.Id is "cinderfall" or "rimeshard");
        var comet = Assert.Single(b.Weapons, w => w.Id == "frostfire_comet");
        Assert.Equal(Weapons.MaxRank, comet.Rank);
        Assert.Equal(2, b.Weapons.Count);
        // Its own rule is in the fight; the halves' evolutions' are gone.
        Assert.Contains(b.Triggers, t => t.Source == "weapon:frostfire_comet");
        Assert.DoesNotContain(b.Triggers, t => t.Source.StartsWith("evo:fallen_star") || t.Source.StartsWith("evo:deepwinter"));
    }

    [Fact]
    public void What_is_carried_by_day_comes_first_at_night_and_comes_in_higher()
    {
        var a = Callings.Archetype("stalker");
        var j = Journey.Begin(new CreationChoice { Name = "A", Archetype = "stalker", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0] }, 9);
        j.Ch.Discovered.AddRange(["gale_chakram", "thornbloom"]);
        Assert.True(SkillBook.Learn(j.Ch, "gale_chakram"));
        Assert.True(SkillBook.Learn(j.Ch, "thornbloom"));
        SkillBook.Unslot(j.Ch, "thornbloom");
        var night = j.StartBattle(true, new CollisionWorld(80), (_, _) => 0, 0, 0, 0, 3, arena: true);
        Assert.Equal(SkillBook.NightRank(j.Ch), night.Attuned["gale_chakram"]);
        Assert.Contains("thornbloom", night.Familiar);
        // The first drafts all bring it until it is taken.
        for (int d = 0; d < LevelUp.AttunedDrafts; d++)
        {
            Owe(night);
            var offers = LevelUp.Draft(night);
            var attuned = Assert.Single(offers, o => o.Attuned);
            Assert.Equal("gale_chakram", attuned.Id);
            if (d == LevelUp.AttunedDrafts - 1)
            {
                LevelUp.Choose(night, attuned);
                Assert.Equal(SkillBook.NightRank(j.Ch), night.Weapons.First(w => w.Id == "gale_chakram").Rank);
            }
            else LevelUp.Choose(night, offers.First(o => !o.Attuned));
        }
        // By day it is still a day's skill; at the tenth level the night brings it a rank higher still.
        while (j.Ch.Level < 10) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        Assert.Equal(3, SkillBook.NightRank(j.Ch));
    }

    [Fact]
    public void A_reroll_looks_again_and_a_banish_is_for_good()
    {
        double overlap = 0;
        int n = 0;
        for (uint seed = 1; seed <= 40; seed++)
        {
            var b = BattleTests.Arena(seed, ("volley", 3), ("rimeshard", 2), ("seeking_motes", 2));
            Owe(b);
            var first = LevelUp.Draft(b).Select(LevelUp.Key).ToHashSet();
            int before = b.Rerolls;
            var again = LevelUp.Reroll(b)!;
            Assert.Equal(before - 1, b.Rerolls);
            Assert.Equal(first.Count, again.Count);
            overlap += again.Count(o => first.Contains(LevelUp.Key(o)));
            n++;
            var ban = again.First(o => o.Kind != OfferKind.Evolve);
            Assert.NotNull(LevelUp.Banish(b, ban));
            for (int d = 0; d < 20; d++)
            {
                Owe(b);
                var offers = LevelUp.Draft(b);
                Assert.DoesNotContain(offers, o => o.Id == ban.Id && o.Kind == ban.Kind);
                LevelUp.Choose(b, offers[0]);
            }
        }
        // What was just shown is far less likely to come back.
        Assert.True(overlap / n < 0.8, $"{overlap / n:0.00} cards came back on average");
        // None left: none to spend.
        var c = BattleTests.Arena(2);
        Owe(c);
        c.Rerolls = 0;
        Assert.Null(LevelUp.Reroll(c));
    }

    [Fact]
    public void A_skip_gives_ember_back_and_a_blessing_cannot_be_skipped()
    {
        var b = BattleTests.Arena(4);
        b.GainEmber(b.EmberNext - b.EmberXp + 0.01);
        Assert.True(LevelUp.SkillNext(b));
        double xp = b.EmberXp;
        int level = LevelUp.DraftLevel(b);
        Assert.True(LevelUp.Skip(b));
        Assert.False(b.DraftOwed);
        Assert.Equal(xp + Battle.EmberNeed(level - 1) * LevelUp.SkipRefund, b.EmberXp, 6);
        b.PendingBlessings.Add(5);
        Assert.True(LevelUp.BlessingNext(b));
        Assert.False(LevelUp.Skip(b));
        b.GreatOwed = 1;
        Assert.False(LevelUp.Skip(b));
    }

    [Fact]
    public void A_fourth_card_comes_with_luck_and_never_without()
    {
        int Fours(double luck)
        {
            int n = 0;
            for (uint seed = 1; seed <= 300; seed++)
            {
                var b = BattleTests.Arena(seed);
                b.Stats.Add(new StatMod(Stat.Luck, ModKind.Flat, luck - 1, "test"));
                Owe(b);
                if (LevelUp.Draft(b).Count == 4) n++;
            }
            return n;
        }
        Assert.Equal(0, Fours(1));
        // 1 - 1/1.5 is a third.
        Assert.InRange(Fours(1.5) / 300.0, 0.25, 0.42);
    }

    [Fact]
    public void Rare_passives_cannot_go_missing_for_long()
    {
        int longest = 0;
        for (uint seed = 1; seed <= 20; seed++)
        {
            var b = BattleTests.Arena(seed, ("volley", 2), ("rimeshard", 2), ("seeking_motes", 2), ("cinderfall", 2), ("arcweb", 2), ("knifestorm", 2));
            int run = 0;
            for (int d = 0; d < 80; d++)
            {
                Owe(b);
                var offers = LevelUp.Draft(b);
                if (offers.Any(o => o.Kind == OfferKind.Boon && o.Rarity >= Rarity.Rare)) run = 0;
                else longest = Math.Max(longest, ++run);
                // Take a rank (never a passive), so the passives stay open.
                LevelUp.Choose(b, offers.FirstOrDefault(o => o.Kind == OfferKind.Rank) ?? offers[0]);
            }
        }
        Assert.True(longest <= LevelUp.RareFloor, $"{longest} drafts without a rare passive");
    }

    [Fact]
    public void A_passive_for_skills_the_build_has_none_of_is_rarely_offered_and_says_so()
    {
        int Count(params (string, int)[] kit)
        {
            int n = 0;
            for (uint seed = 1; seed <= 300; seed++)
            {
                var b = BattleTests.Arena(seed, kit);
                b.Stats.Add(new StatMod(Stat.Luck, ModKind.Flat, 0.5, "test"));
                Owe(b);
                foreach (var o in LevelUp.Draft(b).Where(o => o.Id == "kinship"))
                {
                    n++;
                    if (!b.Weapons.Any(w => w.Tags.Contains(Tag.Summon))) Assert.Contains("Little use to what you carry now", o.Why);
                }
            }
            return n;
        }
        int none = Count(("volley", 2), ("rimeshard", 2), ("knifestorm", 2));
        int some = Count(("gravecall", 2), ("spirit_herd", 2), ("knifestorm", 2));
        Assert.True(none * 2 < some, $"kinship offered {none} times to a build with nothing summoned, {some} to one with");
    }

    [Fact]
    public void A_surge_gives_two_ranks_at_once()
    {
        for (uint seed = 1; seed <= 400; seed++)
        {
            var b = BattleTests.Arena(seed, ("volley", 3), ("rimeshard", 2));
            Owe(b);
            var surge = LevelUp.Draft(b).FirstOrDefault(o => o.Surge > 0 && o.Kind == OfferKind.Rank);
            if (surge == null) continue;
            int before = b.Weapons.First(w => w.Id == surge.Id).Rank;
            LevelUp.Choose(b, surge);
            Assert.Equal(before + 2, b.Weapons.First(w => w.Id == surge.Id).Rank);
            return;
        }
        Assert.Fail("no surge in 400 drafts");
    }

    [Fact]
    public void Milestones_hand_back_a_reroll_and_the_fifteenth_minute_deals_four()
    {
        var b = BattleTests.Arena(6);
        int rerolls = b.Rerolls;
        while (b.EmberLevel < Boons.Milestones[1]) b.GainEmber(b.EmberNext - b.EmberXp + 0.01);
        Assert.Equal(rerolls + 2, b.Rerolls);
        b.PendingLevels = 0; b.PendingBlessings.Clear();
        b.GreatOwed = 1;
        Assert.Equal(3, LevelUp.Draft(b).Count);
        LevelUp.Choose(b, LevelUp.Draft(b)[0]);
        b.GreatOwed = 1;
        Assert.Equal(4, LevelUp.Draft(b).Count);
    }

    [Fact]
    public void The_draft_leans_toward_the_paths_the_build_walks()
    {
        // How often the Pyre's other skills (carried by neither build) are offered.
        string[] rest = ["hallowed_ring", "thunderhead", "verdant_lance"];
        double Share(bool walking)
        {
            int on = 0, all = 0;
            for (uint seed = 1; seed <= 300; seed++)
            {
                // Two of the Pyre's own (or two of nobody's in particular) carried.
                var b = walking ? BattleTests.Arena(seed, ("cinderfall", 2), ("firepot", 2)) : BattleTests.Arena(seed, ("gale_chakram", 2), ("arcweb", 2));
                Owe(b);
                foreach (var o in LevelUp.Draft(b).Where(o => o.Kind == OfferKind.Weapon))
                {
                    all++;
                    if (rest.Contains(o.Id)) on++;
                }
            }
            return (double)on / all;
        }
        Assert.Contains(LevelUp.BuildPaths(BattleTests.Arena(1, ("cinderfall", 2), ("firepot", 2))), p => p.Id == "pyre");
        Assert.True(Share(true) > Share(false) * 1.2, $"{Share(true):0.00} against {Share(false):0.00}");
    }

    [Fact]
    public void A_great_hand_always_holds_a_ward_and_a_power()
    {
        for (uint seed = 1; seed <= 200; seed++)
        {
            var b = BattleTests.Arena(seed);
            b.GreatOwed = 1;
            var hand = LevelUp.Draft(b);
            Assert.Equal(3, hand.Count);
            Assert.All(hand, o => Assert.True(o.Great));
            var roles = hand.Select(o => Boons.GreatRoles[o.Id]).ToList();
            Assert.Contains(Boons.GreatRole.Ward, roles);
            Assert.Contains(Boons.GreatRole.Power, roles);
            Assert.Contains(roles, r => r is Boons.GreatRole.Answer or Boons.GreatRole.Tempo);
        }
    }
}
