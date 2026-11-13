using System.Collections.Generic;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A package's own held props (manifest "held", World.NpcHeld) and the lamp carry keyed on a flag, not an id.</summary>
public class NpcHeldTests
{
    [Fact]
    public void Manifest_block_reads_by_slot_with_its_carry()
    {
        var skipped = new List<string>();
        var h = NpcHeld.Parse("""
            {"name": "x", "held": {
              "handslot.r": {"file": "props/hammer.glb", "carry": "hand"},
              "handslot.l": {"file": "props/lamp.glb", "carry": "lamp"},
              "forearm.l": {"file": "props/shield.glb"},
              "handslot.x": {"file": "a.glb"}}}
            """, skipped);
        Assert.Equal(2, h.Count);
        Assert.Equal(new NpcHeld.Prop("props/hammer.glb", NpcHeld.Carry.Hand), h["handslot.r"]);
        Assert.Equal(new NpcHeld.Prop("props/lamp.glb", NpcHeld.Carry.Lamp), h["handslot.l"]);
        Assert.Equal(2, skipped.Count);
    }

    [Fact]
    public void Carry_defaults_to_hand_and_rejects_the_unknown()
    {
        var skipped = new List<string>();
        var h = NpcHeld.Parse("""{"held": {"handslot.r": {"file": "h.glb"}, "handslot.l": {"file": "l.glb", "carry": "torch"}}}""", skipped);
        Assert.Equal(NpcHeld.Carry.Hand, h["handslot.r"].Carry);
        Assert.False(h.ContainsKey("handslot.l"));
        Assert.Single(skipped);
        Assert.Empty(NpcHeld.Parse("""{"name": "no block"}"""));
        Assert.Empty(NpcHeld.Parse("""{"held": {"handslot.r": {"carry": "lamp"}}}"""));
    }

    [Fact]
    public void Routes_by_the_flag_not_the_id()
    {
        var lamp = new NpcHeld.Prop("props/lamp.glb", NpcHeld.Carry.Lamp);
        var hammer = new NpcHeld.Prop("props/hammer.glb", NpcHeld.Carry.Hand);
        // a package's own: by its carry, whatever the table says
        Assert.Equal(NpcHeld.Route.Lamp, NpcHeld.RouteOf(true, "handslot.l", lamp, false, false));
        Assert.Equal(NpcHeld.Route.Hand, NpcHeld.RouteOf(true, "handslot.r", hammer, true, true));
        Assert.Equal(NpcHeld.Route.None, NpcHeld.RouteOf(false, "handslot.r", hammer, false, false));
        // a table row: the lamp carry only for a flagged row in a package's hand
        Assert.Equal(NpcHeld.Route.Lamp, NpcHeld.RouteOf(true, "handslot.r", null, true, true));
        Assert.Equal(NpcHeld.Route.Table, NpcHeld.RouteOf(false, "handslot.r", null, true, true));
        Assert.Equal(NpcHeld.Route.Table, NpcHeld.RouteOf(true, "handslot.r", null, true, false));
        Assert.Equal(NpcHeld.Route.None, NpcHeld.RouteOf(true, "handslot.r", null, false, false));
    }

    [Fact]
    public void Keeper_lamp_row_is_flagged_in_the_table_source()
    {
        // (Arms is engine code: read its source; the branch keys on Spec.Lamp, never on the literal id)
        var dir = System.AppContext.BaseDirectory;
        while (dir != null && !System.IO.File.Exists(System.IO.Path.Combine(dir, "src/Actors/Arms.cs"))) dir = System.IO.Path.GetDirectoryName(dir);
        Assert.NotNull(dir);
        var arms = System.IO.File.ReadAllText(System.IO.Path.Combine(dir!, "src/Actors/Arms.cs"));
        Assert.Matches(@"\[""keeper_lamp""\] = new\([^\n]*Lamp: true", arms);
        var view = System.IO.File.ReadAllText(System.IO.Path.Combine(dir!, "src/Actors/PersonView.cs"));
        Assert.DoesNotContain("\"keeper_lamp\"", view);
    }
}
