using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The Waystation, run without a screen (Play/Zones/Waystation.cs).</summary>
public class WaystationTests
{
    sealed record Setup(Journey J, FakeHost Host, Waystation Zone, Battle B);

    static Setup Make(TimeOfDay time = TimeOfDay.Day, string? from = null)
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
        var at = zone.ArrivalFrom(from);
        var b = j.StartBattle(false, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 3);
        host.Battle = b;
        zone.Begin(b);
        return new Setup(j, host, zone, b);
    }

    static void Run(Setup s, double seconds)
    {
        for (double t = 0; t < seconds; t += 1 / 30.0)
        {
            s.Zone.Frame(1 / 30.0);
            s.Host.Pass(1 / 30.0);
        }
    }

    static Interactable I(Setup s, string id) => s.Zone.Interactables.Single(i => i.Id == id);

    [Fact]
    public void The_town_is_lived_in_by_day()
    {
        var s = Make();
        Assert.Same(Atmospheres.Day, s.Host.Air);
        Assert.True(s.Zone.Actors.Count >= 10);
        Run(s, 20);
        Assert.True(s.Host.FakeLook.Walkers >= 8, $"{s.Host.FakeLook.Walkers} walkers");
        Assert.Contains(s.Host.Said, l => l.StartsWith("The Waystation"));
        Assert.NotEmpty(s.Host.FakeLook.LastPlates);
        // The lanes the town walks run clear of every wall.
        Assert.Empty((System.Collections.Generic.List<string>)s.Zone.Debug()["lanes"]!);
    }

    [Fact]
    public void At_night_the_braziers_light_and_the_town_goes_in()
    {
        var s = Make(TimeOfDay.Night);
        Assert.Same(Atmospheres.NightTown, s.Host.Air);
        Assert.True(s.Host.FakeLook.Night);
        foreach (var b in new ZoneMetaReader().Braziers) Assert.True(s.Host.FakeLook.IsLit(b));
        // Tam goes home at night.
        Assert.True(s.Zone.Actors["tam"].Hidden);
    }

    sealed class ZoneMetaReader
    {
        public int[] Braziers = ZoneMeta.Load("waystation").Refs.GetProperty("braziers").EnumerateArray().Select(b => b.GetInt32()).ToArray();
    }

    [Fact]
    public void The_old_road_costs_five_gold_once()
    {
        var s = Make();
        var gate = I(s, "gate:east");
        s.J.Ch.Gold = 3;
        Assert.NotNull(gate.Locked!());
        s.J.Ch.Gold = 8;
        Assert.Null(gate.Locked!());
        gate.Act();
        Assert.Equal(3, s.J.Ch.Gold);
        Assert.Equal("verge", s.Host.Travelled?.Zone);
        s.J.Ch.Gold = 0;
        Assert.Null(gate.Locked!());
    }

    [Fact]
    public void Pells_warehouse_opens_at_night_to_picks_or_to_a_key()
    {
        var s = Make();
        var wh = I(s, "warehouse");
        Assert.Equal("Locked, and Pell is watching the door", wh.Locked!());
        s.J.World.Time = TimeOfDay.Night;
        Assert.NotNull(wh.Locked!());
        s.J.GiveItem("lockpicks");
        Assert.Null(wh.Locked!());
        wh.Act();
        Assert.Contains(s.J.Ch.Pack, p => p?.Def == "pell_ledger");
        Assert.Contains(s.J.World.History, h => h.Id == "burgled_pell");
        Assert.False(wh.When!());
    }

    [Fact]
    public void Every_thing_that_can_be_done_can_be_done()
    {
        var s = Make(TimeOfDay.Dusk, "verge");
        foreach (var it in s.Zone.Interactables.ToList())
        {
            if (it.When?.Invoke() == false || it.Locked?.Invoke() != null) continue;
            it.Act();
        }
        Run(s, 5);
        Assert.NotEmpty(s.Zone.MapMarks());
        _ = s.Zone.Ambience(0, 0);
        Assert.Contains("rook", s.Host.Talked);
        Assert.True(s.J.Ch.Gold >= 25);
    }

    /// <summary>The markers over people's heads are worked out when something may have
    /// changed them, not every frame (performance): one a conversation clears is gone
    /// the very frame the conversation ends, and one for someone not yet met shows at once.</summary>
    [Fact]
    public void A_marker_clears_the_frame_its_conversation_ends()
    {
        var s = Make();
        s.Zone.Frame(1 / 30.0);
        char? Mark(string id) => s.Host.FakeLook.LastPlates.SingleOrDefault(p => p.Id == id)?.Marker;
        var who = s.Zone.Actors.Keys.First(id => !s.Zone.Actors[id].Hidden && Mark(id) == '!');
        // What the conversation does (met), then what the game does as it ends (Touched).
        s.J.World.Npc(who).Flags["met"] = true;
        s.Zone.Touched();
        s.Zone.Frame(1 / 30.0);
        Assert.Null(Mark(who));
        // And the slow check catches what nothing announced.
        s.J.World.Npc(who).Flags["met"] = false;
        Run(s, 2.2);
        Assert.Equal('!', Mark(who));
    }
}
