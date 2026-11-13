using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(bd-gear) The forge's one gamble: a piece quenched in open flame for a shot at a perfect one, with a
/// real chance to come out worse. Seeded, so it is the same dice every time for one seed.</summary>
public class QuenchTests
{
    static Route Town()
    {
        var p = Route.New();
        p.W.Npc("brannoc").Flags["met"] = true;
        p.W.Time = TimeOfDay.Day;
        p.J.Ch.Gold = 100000;
        p.Give("ember_shard", 90);
        return p;
    }

    static ItemInstance Carry(Route p, string def, int rarity, params (string Id, int Tier)[] affixes)
    {
        var it = Inventory.Make(p.J.Ch, def, rarity: rarity, affixes: affixes.Select(a => new AffixRoll { Id = a.Id, Tier = a.Tier }).ToList());
        Assert.True(Inventory.AddToPack(p.J.Ch, it));
        return it;
    }

    static ItemInstance Plain(Route p) => Carry(p, "iron_helm", 3, ("hale", 2), ("of_the_wolf", 1), ("keen", 0));
    static int Sum(ItemInstance it) => it.Affixes.Sum(a => a.Tier);

    [Fact]
    public void The_gamble_is_in_data_and_brannoc_does_it()
    {
        var r = Crafting.Rules.Quench;
        Assert.True(Crafting.Does("brannoc", Verb.Quench));
        Assert.True(r.Odds["perfect"] > 0 && r.Odds["perfect"] < r.Odds["up"], "a rare prize");
        Assert.InRange(Crafting.QuenchOdds().Sum(o => o.Chance), 0.999, 1.001);
        // A real chance to lose value: a fifth or more of the weight is a loss.
        Assert.True(Crafting.QuenchOdds().Where(o => o.Outcome is "down" or "ruin").Sum(o => o.Chance) >= 0.2);
    }

    [Fact]
    public void The_same_seed_throws_the_same_dice()
    {
        for (uint s = 1; s <= 40; s++)
        {
            var p = Town();
            var a = Plain(p);
            var b = Plain(p);
            var qa = Crafting.Quench(p.J.Craft, a); var qb = Crafting.Quench(p.J.Craft, b);
            Assert.True(Crafting.Do(p.J.Craft, a, qa, new Rng(s * 104729)));
            Assert.True(Crafting.Do(p.J.Craft, b, qb, new Rng(s * 104729)));
            Assert.Equal(qa.Outcome, qb.Outcome);
            Assert.Equal(a.Affixes.Select(x => (x.Id, x.Tier)), b.Affixes.Select(x => (x.Id, x.Tier)));
        }
    }

    [Fact]
    public void Each_outcome_does_what_it_says_and_the_piece_is_set_and_marked_once()
    {
        var seen = new Dictionary<string, int>();
        int lost = 0, won = 0;
        const int N = 1500;
        for (uint s = 1; s <= N; s++)
        {
            var p = Town();
            var it = Plain(p);
            var before = it.Affixes.Select(a => a.Tier).ToList();
            int shards = p.Count("ember_shard");
            double gold = p.J.Ch.Gold;
            var q = Crafting.Quench(p.J.Craft, it);
            Assert.True(q.Ok, q.Blocked);
            Assert.True(Crafting.Do(p.J.Craft, it, q, new Rng(s * 7919)));
            string o = q.Outcome!;
            seen[o] = seen.GetValueOrDefault(o) + 1;
            Assert.Equal(shards - Crafting.Rules.Quench.Shards, p.Count("ember_shard"));
            Assert.Equal(gold - q.Gold, p.J.Ch.Gold);
            Assert.Equal(0, it.Heat);
            Assert.True(Crafting.Quenched(it));
            Assert.Equal("It has been quenched. Once is all a piece takes.", Crafting.Quench(p.J.Craft, it).Blocked);
            Assert.Contains(it.History!, h => h.StartsWith("Quenched"));
            var after = it.Affixes.Select(a => a.Tier).ToList();
            var moved = after.Zip(before, (a, b) => a - b).ToList();
            switch (o)
            {
                case "perfect":
                    Assert.All(after, t => Assert.Equal(Crafting.Bright, t));
                    won++;
                    break;
                case "up":
                    Assert.InRange(moved.Count(m => m != 0), 1, Crafting.Rules.Quench.Up);
                    Assert.All(moved, m => Assert.InRange(m, 0, 1));
                    Assert.All(after, t => Assert.True(t <= Crafting.Cap(it)));
                    Assert.True(Sum(it) > before.Sum());
                    won++;
                    break;
                case "nothing":
                    Assert.Equal(before, after);
                    break;
                case "down":
                    Assert.InRange(moved.Count(m => m != 0), 1, Crafting.Rules.Quench.Down);
                    Assert.All(moved, m => Assert.InRange(m, -1, 0));
                    Assert.True(Sum(it) < before.Sum());
                    lost++;
                    break;
                case "ruin":
                    Assert.All(after.Zip(before), pair => Assert.Equal(Math.Max(0, pair.Second - Crafting.Rules.Quench.Ruin), pair.First));
                    Assert.True(Sum(it) < before.Sum());
                    lost++;
                    break;
                default: Assert.Fail($"unknown outcome {o}"); break;
            }
            var (said, mood) = Crafting.QuenchOutcome(q);
            Assert.False(string.IsNullOrWhiteSpace(said));
            Assert.Equal(o is "perfect" or "up" ? 1 : o == "nothing" ? 0 : -1, mood);
        }
        // Every outcome is reachable, and the odds come near their weights.
        foreach (var (outcome, chance) in Crafting.QuenchOdds())
        {
            Assert.True(seen.GetValueOrDefault(outcome) > 0, $"{outcome} never came");
            Assert.InRange(seen.GetValueOrDefault(outcome) / (double)N, chance - 0.04, chance + 0.04);
        }
        // A real chance to lose value, a real chance to win it all.
        Assert.True(lost > won * 0.5 && lost > N * 0.15, $"lost {lost}, won {won}");
        Assert.True(seen["perfect"] > 0);
    }

    [Fact]
    public void It_will_not_take_what_it_cannot_use()
    {
        var p = Town();
        var q = Crafting.Quench(p.J.Craft, Plain(p));
        Assert.Equal(Crafting.Rules.Quench.Shards, q.Takes["ember_shard"]);
        Assert.True(q.Gold > 0 && q.HeatLo >= 1);
        // A legendary is somebody's work.
        var l = Carry(p, "wardens_lampiron", 4);
        Assert.NotNull(Crafting.Quench(p.J.Craft, l).Blocked);
        // A plain piece with no power to quench; a piece set by the slurry; a piece out of heat.
        Assert.Equal("Nothing in it for the flame to take.", Crafting.Quench(p.J.Craft, Carry(p, "iron_helm", 0)).Blocked);
        var s = Plain(p); (s.Marks ??= new()).Add(Crafting.Rules.Slurry.Mark);
        Assert.Equal(Crafting.SetForGood, Crafting.Quench(p.J.Craft, s).Blocked);
        var cold = Plain(p); cold.Heat = 0;
        Assert.NotNull(Crafting.Quench(p.J.Craft, cold).Blocked);
        // No shards, no flame.
        var poor = Route.New();
        poor.W.Npc("brannoc").Flags["met"] = true;
        poor.W.Time = TimeOfDay.Day;
        poor.J.Ch.Gold = 100000;
        Assert.StartsWith("Needs", Crafting.Quench(poor.J.Craft, Plain(poor)).Blocked);
        // The forge is banked by night.
        p.W.Time = TimeOfDay.Night;
        Assert.NotNull(Crafting.Quench(p.J.Craft, Plain(p)).Blocked);
    }

    [Fact]
    public void A_quench_done_at_the_bench_says_what_it_came_to()
    {
        var p = Town();
        var it = Plain(p);
        var q = Crafting.Quench(p.J.Craft, it);
        var toasts = new List<Toast>();
        p.J.OnToast = toasts.Add;
        Assert.True(p.J.Work(it.Uid, q, null));
        Assert.True(Crafting.Quenched(it));
        Assert.Contains(toasts, t => t.Sub == Crafting.QuenchOutcome(q).Text);
        Assert.NotNull(p.J.CraftSaid?.Line);
    }
}
