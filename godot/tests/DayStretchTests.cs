using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The Low Ford Road by day (H4 item 10): a permanent zone reset as data (data/content/zone_resets.json,
/// World/ZoneReset.cs) and its stretch (data/content/day_stretch.json, Play/Zones/DayStretch.cs).</summary>
public class DayStretchTests
{
    const double Dt = 1 / 60.0;

    /// <summary>An open fight as big as the Low Ford's ground (the test arena's 120 m would hold her off the road).</summary>
    static Battle Road(uint seed) => new(new BattleSetup
    {
        Seed = seed, Collision = new CollisionWorld(260), Combat = true, Stats = BattleTests.BaseStats(), Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash,
    });

    [Fact]
    public void The_road_resets_on_the_day_change()
    {
        var w = new WorldState { Day = 1 };
        Assert.Equal("day", ZoneReset.For("lowford")!.Reset);
        ZoneReset.Apply(w, "lowford");
        w.Zone("lowford")[DayStretch.DoneKey("boars")] = true;
        w.Zone("lowford")[DayStretch.DoneKey("strongbox")] = true;
        w.Day = 2;
        Assert.True(ZoneReset.Apply(w, "lowford"));
        Assert.False(w.Zone("lowford").ContainsKey(DayStretch.DoneKey("boars")));
        Assert.False(w.Zone("lowford").ContainsKey(DayStretch.DoneKey("strongbox")));
    }

    [Fact]
    public void The_road_is_kept_within_the_day()
    {
        var w = new WorldState { Day = 3 };
        ZoneReset.Apply(w, "lowford");
        w.Zone("lowford")[DayStretch.DoneKey("kerchiefs")] = true;
        // Out to the Waystation and back, the same day: still down.
        Assert.False(ZoneReset.Apply(w, "lowford"));
        Assert.False(ZoneReset.Apply(w, "lowford"));
        Assert.True(w.Zone("lowford")[DayStretch.DoneKey("kerchiefs")].Truthy);
        // A zone without a rule is never touched.
        w.Zone("verge")["roost_kitchen"] = true;
        w.Day = 4;
        Assert.False(ZoneReset.Apply(w, "verge"));
        Assert.True(w.Zone("verge")["roost_kitchen"].Truthy);
    }

    [Fact]
    public void The_lamp_post_is_never_reset()
    {
        bool was = Content.Lamps.V2;
        Content.Lamps.UseV2(true);
        try
        {
            var w = new WorldState { Day = 1 };
            ZoneReset.Apply(w, "lowford");
            Assert.True(LampBook.RelightPost(w, "act1.post1"));
            for (int d = 2; d < 6; d++) { w.Day = d; ZoneReset.Apply(w, "lowford"); }
            Assert.True(LampBook.PostLit(w, "act1.post1"));
            Assert.Equal(1, LampBook.PostLamps(w));
            Assert.False(LampBook.RelightPost(w, "act1.post1"));
        }
        finally { Content.Lamps.UseV2(was); }
    }

    [Fact]
    public void The_stretch_runs_up_the_road_in_order_between_the_handback_and_the_gate()
    {
        var s = DayStretch.For("lowford")!;
        Assert.Equal(new[] { "boars", "kerchiefs", "post", "strongbox", "wolves" }, s.Beats.Select(b => b.Id));
        foreach (var bt in s.Beats) Assert.InRange(bt.Z, s.GateZ + 4, s.From[1] - 10);
        Assert.Equal("act1.post1", s.Get("post")!.Post);
        Assert.Equal("charge", s.Get("boars")!.Tell);
        Assert.NotNull(Content.Enemies.Get(s.Get("kerchiefs")!.Captain!));
        Assert.NotNull(Content.Telegraphs.Get(s.Get("boars")!.Tell!));
    }

    [Fact]
    public void Packs_down_today_stay_down_and_the_rest_rest_until_she_comes()
    {
        var b = Road(11);
        var st = new Dictionary<string, Fact> { [DayStretch.DoneKey("boars")] = true };
        var d = new DayStretch(DayStretch.For("lowford")!, b, st, 2, 1);
        d.Place();
        Assert.False(d.Packs.ContainsKey("boars"));
        Assert.True(d.Standing("kerchiefs").Count >= 6);
        Assert.NotNull(d.Captain("kerchiefs"));
        Assert.True(d.Captain("kerchiefs")!.Elite);
        // Far from her, they rest.
        b.Player.X = 0; b.Player.Z = 60;
        for (int i = 0; i < 120; i++) { b.Tick(Dt, 0, 0); d.Tick(Dt); b.Events.Drain(); }
        Assert.False(d.WokeAt.ContainsKey("kerchiefs"));
    }

    [Fact]
    public void The_boars_charge_through_the_kit_and_the_ring_closes_with_the_flare_full()
    {
        var b = Road(5);
        var s = DayStretch.For("lowford")!;
        var d = new DayStretch(s, b, new Dictionary<string, Fact> { [DayStretch.DoneKey("kerchiefs")] = true }, 2, 1);
        d.Place();
        var boars = s.Get("boars")!;
        b.Player.X = boars.X; b.Player.Z = boars.Z + 7;
        b.Weapons.Clear();   // (her own blows off: the boars live to charge)
        var told = new List<string>();
        d.Told = (bt, e, blow) => told.Add(bt.Id + ":" + blow.Tell);
        for (double t = 0; t < 6 && told.Count == 0; t += Dt) { b.Player.Hp = b.MaxHp; b.Tick(Dt, 0, 0); d.Tick(Dt); b.Events.Drain(); }
        Assert.Contains("boars:charge", told);
        // North past the ring's line, having come from the south: it closes round her.
        b.Player.Hp = b.MaxHp;
        b.FlareMeter = 0;
        var ring = s.Get("wolves")!;
        b.Player.X = ring.X; b.Player.Z = ring.ArmZ + 2;
        d.Tick(Dt);
        b.Player.Z = ring.Z - 0.5;
        d.Tick(Dt);
        Assert.True(d.RingAt >= 0);
        Assert.True(d.Standing("wolves").Count >= 6);
        if (b.Flare != null) Assert.True(b.FlareReady);
    }
}
