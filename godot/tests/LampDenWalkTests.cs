using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>The den's walk (lane B): a Warden at level 6, 7 and 8 can spend every point the den gives, on the board (a lamp
/// is always offered and lights) and on the wicks (the first lamp of every strand of her taught keys can be planned).</summary>
public sealed class LampDenWalkTests
{
    readonly ITestOutputHelper log;
    public LampDenWalkTests(ITestOutputHelper log) { this.log = log; }

    static CharacterData Warden(int level)
    {
        var a = Callings.Archetype("warden");
        var ch = Character.Create(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id,
            WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, seed: 7);
        ch.Level = level;
        return ch;
    }

    [Theory]
    [InlineData(6)]
    [InlineData(7)]
    [InlineData(8)]
    public void Every_point_can_be_spent_on_every_wardens_road(int level)
    {
        var w = new WorldState { Time = TimeOfDay.Day };
        foreach (var road in Lamps.Roads.Values.Where(r => r.Calling == "warden"))
        {
            var ch = Warden(level);
            Assert.True(LampBook.ChooseRoad(ch, road.Id), $"{road.Id} at {level}");
            int spare = LampBook.Spare(ch, w);
            Assert.True(spare > 0);
            int lit = 0;
            while (LampBook.Spare(ch, w) > 0)
            {
                var id = LampBook.Suggest(ch, w);
                Assert.True(id != null, $"{road.Id} level {level}: {LampBook.Spare(ch, w)} points and no lamp offered");
                Assert.True(LampBook.Light(ch, w, id!), $"{road.Id} level {level}: {id} would not light");
                lit++;
            }
            log.WriteLine($"{road.Id} level {level}: {spare} points, {lit} lamps lit, last {LampBook.Now(ch).Lit.Last()}");
            Assert.Equal(spare, lit);
        }
    }

    [Fact]
    public void The_first_lamp_of_every_strand_of_her_taught_skills_can_be_planned()
    {
        var ch = Warden(6);
        var skills = new[] { "sunder", "heroic_leap", "bladestorm", "groundbreaker", "iron_vow" };
        foreach (var sk in skills)
        {
            if (Wicks.Of(sk) == null) { log.WriteLine($"{sk}: no wick"); continue; }
            foreach (var s in Wicks.StrandsOf(sk))
                Assert.Equal(WickNo.None, WickBook.CanPlan(ch, sk, s.LampId(1)));
        }
    }
}
