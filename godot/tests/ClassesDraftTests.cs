using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Sim;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The road lean, the Flare great blessings, and the Flare map mods (docs/design/CLASSES.md 2.10, 3.4, 5).</summary>
public sealed class ClassesDraftTests
{
    [Fact]
    public void The_road_lit_deepest_leans_its_signature_skills_by_night_and_is_capped()
    {
        var road = Lamps.Roads.Values.First(r => r.Skills.Length > 0);
        var b = BattleTests.Arena(1);
        b.Lamps = new LampLoadout { Lean = road.Id };
        var o = new Offer();
        Assert.Equal(Lamps.RoadLean, LevelUp.RoadLeaned(b, road.Skills[0], 1, o), 6);
        Assert.Contains(o.Why, w => w.Contains(road.Name));
        // With the path and calling leans, the product stops at the cap.
        Assert.Equal(Lamps.LeanCap, LevelUp.RoadLeaned(b, road.Skills[0], LevelUp.PathLean * LevelUp.CallingLean, new Offer()), 6);
        // Not its skill, or no road, or by day: no lean.
        Assert.Equal(1, LevelUp.RoadLeaned(b, "not_a_skill", 1, new Offer()), 6);
        b.Lamps = new LampLoadout();
        Assert.Equal(1, LevelUp.RoadLeaned(b, road.Skills[0], 1, new Offer()), 6);
        b.Lamps = new LampLoadout { Lean = road.Id };
        b.EmberOn = false;
        Assert.Equal(1, LevelUp.RoadLeaned(b, road.Skills[0], 1, new Offer()), 6);
    }

    [Fact]
    public void The_flare_great_blessings_are_offered_only_with_a_flare()
    {
        var seen = new System.Collections.Generic.HashSet<string>();
        for (uint seed = 1; seed <= 300; seed++)
        {
            var plain = BattleTests.Arena(seed);
            plain.GreatOwed = 1;
            Assert.DoesNotContain(LevelUp.Draft(plain, 4), o => Boons.FlareGreat.Contains(o.Id));
            var lit = BattleTests.Arena(seed);
            lit.Flare = Lamps.Flares.Values.First();
            lit.GreatOwed = 1;
            foreach (var o in LevelUp.Draft(lit, 4)) if (Boons.FlareGreat.Contains(o.Id)) seen.Add(o.Id);
        }
        Assert.Equal(Boons.FlareGreat.Length, seen.Count);
    }

    [Fact]
    public void Smothered_and_bright_set_their_rules()
    {
        var c = new Chart();
        c.Mods.Add("smothered");
        Assert.Equal(0.7, c.Rules().FlareFill, 6);
        Assert.True(c.Rules().FlareMends);
        var d = new Chart();
        d.Mods.Add("bright");
        Assert.False(d.Rules().FlareMends);
        Assert.True(Charts.Mod("smothered").Prefix);
        Assert.False(Charts.Mod("bright").Prefix);
    }
}
