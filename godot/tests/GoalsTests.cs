using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The goals (data/content/goals.json): one entry is a tracker line, a pin, a waypoint.</summary>
public class GoalsTests
{
    static (Journey J, Waystation Zone) Town(TimeOfDay time)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
        j.World.Time = time;
        var meta = ZoneMeta.Load("waystation");
        var host = new FakeHost(j, meta);
        var zone = new Waystation(host, meta);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(false, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 3);
        host.Battle = b;
        zone.Begin(b);
        return (j, zone);
    }

    [Fact]
    public void The_goals_parse_and_their_glyphs_exist()
    {
        Assert.True(Goals.All.Count >= 3);
        var glyphs = Json.Parse<Dictionary<string, string>>(Json.ReadContent("glyphs.json"));
        foreach (var g in Goals.All)
        {
            Assert.Contains(g.Glyph, glyphs.Keys);
            Assert.NotEmpty(g.Steps);
            Assert.NotEqual("", g.Pin);
        }
    }

    [Fact]
    public void The_table_is_a_goal_once_the_prologue_is_done()
    {
        var (j, zone) = Town(TimeOfDay.Day);
        var none = Goals.Active(Goals.All, j.Ctx, zone.Id, zone.Interactables);
        Assert.Empty(none);
        j.World.Facts["prologue.done"] = true;
        var day = Goals.Active(Goals.All, j.Ctx, zone.Id, zone.Interactables);
        var g = Assert.Single(day);
        Assert.True(g.Line);
        var list = Goals.Merge(new List<Tracked> { new("tonight", "Tonight", TrackTone.Main, new() { new Step("x") }) }, day, _ => null);
        Assert.Equal(new[] { "tonight", "table" }, list.Select(t => t.Id));
        Assert.Equal("The Wayfinder's Table", list[1].Title);
        Assert.Equal(2, list[1].Steps.Count);

        j.World.Time = TimeOfDay.Night;
        var night = Goals.Active(Goals.All, j.Ctx, zone.Id, zone.Interactables);
        var n = Assert.Single(night);
        Assert.False(n.Line);
        Assert.Single(Goals.Merge(new List<Tracked> { new("tonight", "Tonight", TrackTone.Main, new() { new Step("x") }) }, night, _ => null));
    }

    [Fact]
    public void The_way_out_joins_the_arenas_block_once_it_stands()
    {
        var (j, _) = Town(TimeOfDay.Night);
        bool shown = false;
        var pins = new List<Interactable> { new() { Id = "way_out", X = 3, Z = 4, R = 2.6, When = () => shown } };
        var block = new Tracked("arena", "The Night", TrackTone.Main, new() { new Step("Survive"), new Step("Third", Optional: true) });
        string? Word(string k) => k == "boss" ? "Mordrake" : null;

        var before = Goals.Active(Goals.All, j.Ctx, "arena", pins);
        Assert.Empty(before);
        Assert.Equal(2, Goals.Merge(new() { block }, before, Word)[0].Steps.Count);

        shown = true;
        var now = Goals.Active(Goals.All, j.Ctx, "arena", pins);
        var g = Assert.Single(now);
        Assert.Equal((3, 4), (g.X, g.Z));
        var merged = Goals.Merge(new() { block }, now, Word);
        Assert.Single(merged);
        Assert.Equal(3, merged[0].Steps.Count);
        Assert.Equal("Leave by the way out, where Mordrake fell", merged[0].Steps[1].Text);
        Assert.Equal(2, block.Steps.Count);
    }

    [Fact]
    public void A_first_goal_leads_the_tracker_after_tonight()
    {
        var def = new GoalDef { Id = "lead", Title = "Lead", First = true, Steps = new() { new GoalStep { Text = "Go" } } };
        var act = new List<ActiveGoal> { new(def, 0, 0, 1, true) };
        var tonight = new Tracked("tonight", "Tonight", TrackTone.Main, new() { new Step("x") });
        var other = new Tracked("other", "Other", TrackTone.Main, new() { new Step("y") });
        Assert.Equal(new[] { "lead", "other" }, Goals.Merge(new() { other }, act, _ => null).Select(t => t.Id));
        Assert.Equal(new[] { "tonight", "lead", "other" }, Goals.Merge(new() { tonight, other }, act, _ => null).Select(t => t.Id));
        Assert.Equal(new[] { "other", "tonight", "lead" }, Goals.Merge(new() { other, tonight }, act, _ => null).Select(t => t.Id));
        def.First = false;
        Assert.Equal(new[] { "other", "lead" }, Goals.Merge(new() { other }, act, _ => null).Select(t => t.Id));
    }

    [Fact]
    public void The_table_leads_and_the_way_out_fades_at_the_ring()
    {
        Assert.True(Goals.All.Single(g => g.Id == "table").First);
        foreach (var g in Goals.All.Where(g => g.Id != "table")) { Assert.False(g.First); Assert.Equal(6, g.Fade); Assert.Equal("arch", g.Glyph); }
        Assert.Null(Goals.All.Single(g => g.Id == "table").Fade);
        Assert.Equal("chart", Goals.All.Single(g => g.Id == "table").Glyph);
        Assert.True(System.Enum.IsDefined(typeof(MarkKind), "Goal"));
    }
}
