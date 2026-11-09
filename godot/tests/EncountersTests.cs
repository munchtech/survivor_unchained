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
/// World/ZoneReset.cs) and its stretch (data/content/encounters.json, Play/Zones/Encounters.cs).</summary>
public class EncountersTests
{
    const double Dt = 1 / 60.0;

    /// <summary>An open fight as big as the Low Ford's ground (the test arena's 120 m would hold her off the road).</summary>
    static Battle Road(uint seed) => new(new BattleSetup
    {
        Seed = seed, Collision = new CollisionWorld(260), Combat = true, Stats = BattleTests.BaseStats(), Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash,
    });

    [Fact]
    public void The_road_resets_when_she_comes_back_from_another_zone()
    {
        // (ARPG 7.3: the Low Ford's rule is "leave", zone_resets.json; a reload keeps it)
        var w = new WorldState { Day = 1 };
        Assert.Equal("leave", ZoneReset.For("lowford")!.Reset);
        w.Zone("lowford")[Encounters.DoneKey("boars")] = true;
        w.Zone("lowford")[Encounters.DoneKey("strongbox")] = true;
        Assert.False(ZoneReset.Apply(w, "lowford", "load"));
        Assert.True(w.Zone("lowford")[Encounters.DoneKey("boars")].Truthy);
        Assert.True(ZoneReset.Apply(w, "lowford", "waystation"));
        Assert.False(w.Zone("lowford").ContainsKey(Encounters.DoneKey("boars")));
        Assert.False(w.Zone("lowford").ContainsKey(Encounters.DoneKey("strongbox")));
    }

    [Fact]
    public void The_road_is_kept_within_the_day()
    {
        var w = new WorldState { Day = 3 };
        ZoneReset.Apply(w, "lowford");
        w.Zone("lowford")[Encounters.DoneKey("kerchiefs")] = true;
        // Out to the Waystation and back, the same day: still down.
        Assert.False(ZoneReset.Apply(w, "lowford"));
        Assert.False(ZoneReset.Apply(w, "lowford"));
        Assert.True(w.Zone("lowford")[Encounters.DoneKey("kerchiefs")].Truthy);
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

    const string Pockets = "lowford.pockets";

    [Fact]
    public void Pocket_beats_need_the_zones_feature_and_are_off_without_it()
    {
        var s = Encounters.For("lowford")!;
        var pockets = s.Beats.Where(b => b.Needs != null).ToList();
        Assert.Equal(10, pockets.Count);
        Assert.All(pockets, b => Assert.Equal(Pockets, b.Needs));
        Assert.All(pockets, b => Assert.Contains("PROVISIONAL", b.About));
        // Off: not in either phase's list, not placed, and the gate is as it was.
        Assert.DoesNotContain(s.In("day"), b => b.Needs != null);
        Assert.DoesNotContain(s.In("night"), b => b.Needs != null);
        var off = new Encounters(s, Road(3), new Dictionary<string, Fact>(), 2, 1);
        off.Place();
        var offN = new Encounters(s, Road(3), new Dictionary<string, Fact>(), 1, 0, "night");
        offN.Place();
        Assert.DoesNotContain(off.Packs.Keys.Concat(offN.Packs.Keys), id => s.Get(id)!.Needs != null);
        var done = s.In("day").ToDictionary(x => Encounters.DoneKey(x.Id), _ => (Fact)true);
        var gateOff = new Encounters(s, Road(3), done, 2, 1);
        var gateOn = new Encounters(s, Road(3), done, 2, 1, features: [Pockets]);
        Assert.Equal(gateOff.GateOpen, gateOn.GateOpen);
        Assert.DoesNotContain(gateOff.Of("pack").Concat(gateOff.Of("ring")), b => b.Needs != null);
    }

    [Fact]
    public void With_the_feature_on_the_pockets_load_and_the_goal_visits_them()
    {
        var s = Encounters.For("lowford")!;
        var b = Road(4);
        var dayDone = new Dictionary<string, Fact> { ["boars"] = true, ["kerchiefs"] = true, ["strongbox"] = true }
            .ToDictionary(kv => Encounters.DoneKey(kv.Key), kv => kv.Value);
        var d = new Encounters(s, b, dayDone, 2, 1, features: [Pockets]);
        d.Place();
        foreach (var id in new[] { "pk2_a", "pk2_b", "pk2_c", "pk3_a", "pk3_b", "pk3_c" }) Assert.True(d.Packs.ContainsKey(id), id);
        Assert.NotNull(d.Captain("pk2_b"));
        Assert.True(d.Champions.ContainsKey("pk2_c"));
        b.Player.X = 40; b.Player.Z = -85;
        Assert.Equal("pk2_a", d.Goal(_ => true, _ => null, 0).For?.Id);
        var n = new Encounters(s, Road(4), new Dictionary<string, Fact>(), 1, 0, "night", [Pockets]);
        n.Place();
        foreach (var id in new[] { "n_pk1_a", "n_pk1_b", "n_pk1_c", "n_pk1_d" }) Assert.True(n.Packs.ContainsKey(id), id);
        Assert.True(n.Champions.ContainsKey("n_pk1_d"));
        // (the night's route: n_road1, then the first pocket pack)
        var done = new Dictionary<string, Fact>();
        foreach (var id in new[] { "n_lone", "n_three", "n_first", "n_cart", "n_road1" }) done["night." + id] = true;
        var n2 = new Encounters(s, Road(4), done, 1, 0, "night", [Pockets]);
        n2.Place();
        Assert.Equal("n_pk1_a", n2.Goal(_ => true, _ => null, 0).For?.Id);
    }

    [Fact]
    public void A_post_moves_with_the_feature_and_the_goal_follows()
    {
        var post = Content.LampPosts.Get("act1.post1")!;
        Assert.Equal((-0.99, -86.0, 14), post.At(null));
        Assert.Equal((-0.99, -86.0, 14), post.At([]));
        var moved = post.At([Pockets]);
        Assert.InRange(moved.X, 55, 70);
        Assert.InRange(moved.Z, -75, -60);
        Assert.Equal(-1, moved.Light);
    }

    [Fact]
    public void The_stretch_runs_up_the_road_in_order_between_the_handback_and_the_gate()
    {
        var s = Encounters.For("lowford")!;
        Assert.Equal(new[] { "boars", "kerchiefs", "strongbox", "road_ambush", "post", "wallow", "track_ambush", "wolves" }, s.In("day").Select(b => b.Id));
        foreach (var bt in s.In("day")) Assert.InRange(bt.Z, s.GateZ + 4, s.From[1] - 10);
        Assert.Equal("act1.post1", s.Get("post")!.Post);
        Assert.Equal("charge", s.Get("boars")!.Tell);
        Assert.NotNull(Content.Enemies.Get(s.Get("kerchiefs")!.Captain!));
        Assert.NotNull(Content.Telegraphs.Get(s.Get("boars")!.Tell!));
    }

    [Fact]
    public void Packs_down_today_stay_down_and_the_rest_rest_until_she_comes()
    {
        var b = Road(11);
        var st = new Dictionary<string, Fact> { [Encounters.DoneKey("boars")] = true };
        var d = new Encounters(Encounters.For("lowford")!, b, st, 2, 1);
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
        var s = Encounters.For("lowford")!;
        var d = new Encounters(s, b, new Dictionary<string, Fact> { [Encounters.DoneKey("kerchiefs")] = true }, 2, 1);
        d.Place();
        var boars = s.Get("boars")!;
        b.Player.X = boars.X; b.Player.Z = boars.Z + 7;
        b.Weapons.Clear();   // (her own blows off: the boars live to charge)
        var told = new List<string>();
        d.Told = (bt, e, blow) => told.Add(bt.Id + ":" + blow.Tell);
        for (double t = 0; t < 6 && told.Count == 0; t += Dt) { b.Player.Hp = b.MaxHp; b.Tick(Dt, 0, 0); d.Tick(Dt); b.Events.Drain(); }
        Assert.Contains("boars:charge", told);
        // Not while the boars are up: the ring waits for the quiet.
        var ring = s.Get("wolves")!;
        b.Player.X = ring.X; b.Player.Z = ring.ArmZ + 2;
        d.Tick(Dt);
        b.Player.Z = ring.Z - 0.5;
        d.Tick(Dt);
        Assert.True(d.RingAt < 0);
        // North past the ring's line, having come from the south, the road's packs down: it closes round her.
        d = new Encounters(s, b, s.In("day").Where(x => x.Kind == "pack").ToDictionary(x => Encounters.DoneKey(x.Id), _ => (Fact)true), 2, 1);
        d.Place();
        b.Player.Hp = b.MaxHp;
        b.FlareMeter = 0;
        b.Player.X = ring.X; b.Player.Z = ring.ArmZ + 2;
        d.Tick(Dt);
        b.Player.Z = ring.Z - 0.5;
        d.Tick(Dt);
        Assert.True(d.RingAt >= 0);
        Assert.True(d.Standing("wolves").Count >= 6);
        if (b.Flare != null) Assert.True(b.FlareReady);
        // (r3) The rest of the pack waits for the ring to be down and a breath; the gate holds till they are.
        Assert.False(d.GateOpen);
        foreach (var e in d.Standing("wolves")) b.KillEnemy(e, true, null);
        for (double t = 0; t < 1; t += Dt) { b.Player.Hp = b.MaxHp; b.Tick(Dt, 0, 0); d.Tick(Dt); b.Events.Drain(); }
        Assert.Empty(d.Standing("wolves"));
        Assert.False(d.GateOpen);
        for (double t = 0; t < ring.FollowAfter + 0.5; t += Dt) { b.Player.Hp = b.MaxHp; b.Tick(Dt, 0, 0); d.Tick(Dt); b.Events.Drain(); }
        Assert.True(d.Standing("wolves").Count >= 4);
        Assert.False(d.GateOpen);
    }

    [Fact]
    public void A_gate_is_shut_before_the_ring()
    {
        // (H8, N22, the owner on demo-rc2: "we are able to just run up to the waystation and skip the whole day time
        // tutorial". The gate was open until a ring was sprung; a player round by the wall never sprang it.)
        var b = Road(9);
        var s = Encounters.For("lowford")!;
        var d = new Encounters(s, b, s.In("day").Where(x => x.Kind == "pack").ToDictionary(x => Encounters.DoneKey(x.Id), _ => (Fact)true), 2, 1);
        d.Place();
        var ring = s.Get("wolves")!;
        Assert.False(d.GateOpen);
        Assert.NotNull(d.RingOwed);
        // Round by the wall, off the road, to the gate's apron: still shut, the ring still owed.
        b.Player.X = ring.X + ring.HalfWidth + 3; b.Player.Z = s.GateZ + 1;
        for (double t = 0; t < 0.5; t += Dt) { b.Player.Hp = b.MaxHp; d.Tick(Dt); }
        Assert.True(d.RingAt < 0);
        Assert.False(d.GateOpen);
        // A step onto the road there springs it, armed or not (she never came up the road from the south).
        b.Player.X = ring.X;
        d.Tick(Dt);
        Assert.True(d.RingAt >= 0);
        Assert.Null(d.RingOwed);
        Assert.False(d.GateOpen);
        // Down, and its second wave down: open.
        for (int k = 0; k < 2; k++)
        {
            foreach (var e in d.Standing("wolves")) b.KillEnemy(e, true, null);
            for (double t = 0; t < ring.FollowAfter + 0.5; t += Dt) { b.Player.Hp = b.MaxHp; b.Tick(Dt, 0, 0); d.Tick(Dt); b.Events.Drain(); }
        }
        foreach (var e in d.Standing("wolves")) b.KillEnemy(e, true, null);
        b.Tick(Dt, 0, 0); d.Tick(Dt); b.Events.Drain();
        Assert.True(d.GateOpen);
        // Done before a reload (no ring sprung this run): open.
        var again = new Encounters(s, Road(10), new Dictionary<string, Fact>(s.In("day").Where(x => x.Kind is "pack" or "ring").ToDictionary(x => Encounters.DoneKey(x.Id), _ => (Fact)true)), 2, 1);
        Assert.True(again.GateOpen);
    }

    [Fact]
    public void A_pack_left_standing_far_off_does_not_hold_the_ring()
    {
        // (H4 lead 3, j08 g3: one ambush foe stuck in the trees held the ring, and the gate, for good.)
        var b = Road(7);
        var s = Encounters.For("lowford")!;
        var d = new Encounters(s, b, s.In("day").Where(x => x.Kind == "pack" && x.Id != "boars").ToDictionary(x => Encounters.DoneKey(x.Id), _ => (Fact)true), 2, 1);
        d.Place();
        var boars = s.Get("boars")!;
        b.Player.X = boars.X; b.Player.Z = boars.Z + 7;
        b.Weapons.Clear();
        for (double t = 0; t < 4 && !d.Fighting; t += Dt) { b.Player.Hp = b.MaxHp; b.Tick(Dt, 0, 0); d.Tick(Dt); b.Events.Drain(); }
        Assert.True(d.Fighting);
        var ring = s.Get("wolves")!;
        b.Player.X = ring.X; b.Player.Z = ring.ArmZ + 2;
        d.Tick(Dt);
        b.Player.Z = ring.Z - 0.5;
        for (double t = 0; t < Encounters.FightGrace + 1 && d.RingAt < 0; t += Dt)
        {
            foreach (var e in d.Standing("boars")) { e.X = boars.X + 60; e.Z = boars.Z; }
            b.Player.Hp = b.MaxHp; b.Player.X = ring.X; b.Player.Z = ring.Z - 0.5; b.Tick(Dt, 0, 0); d.Tick(Dt); b.Events.Drain();
        }
        Assert.True(d.RingAt >= 0);
    }

    [Fact]
    public void The_road_ambush_springs_on_her_way_back_once_the_strongbox_is_open()
    {
        var b = Road(7);
        var s = Encounters.For("lowford")!;
        var am = s.Get("road_ambush")!;
        var st = s.In("day").Where(x => x.Kind == "pack").ToDictionary(x => Encounters.DoneKey(x.Id), _ => (Fact)true);
        var d = new Encounters(s, b, st, 2, 1);
        d.Place();
        b.Player.X = am.X; b.Player.Z = am.Z;
        d.Tick(Dt);
        Assert.False(d.Packs.ContainsKey(am.Id));
        // Its way lies through it once the box is open (the route's next place), and there it springs.
        d.MarkDone("strongbox");
        b.Player.X = am.X + 20; b.Player.Z = am.Z;
        var g = d.Goal(_ => true, _ => null, 0);
        Assert.Same(am, g.For);
        b.Player.X = am.X; b.Player.Z = am.Z;
        d.Tick(Dt);
        Assert.Equal(am.Foes.Sum(f => f.N), d.Standing(am.Id).Count);
        Assert.All(d.Standing(am.Id), e => Assert.True(MathX.Dist(e.X, e.Z, am.X, am.Z) >= 5));
        Assert.True(d.Fighting);
    }

    [Fact]
    public void No_two_packs_wake_within_20_m_of_each_other()
    {
        // (each fight and its callout stand alone: a pack's waking ring, its wake round each of its foes, 20 m or more
        // clear of the next one's; the ring waits while any pack is up and fighting, Encounters.Tick)
        var s = Encounters.For("lowford")!;
        double Reach(Encounters.Beat bt) => bt.Wake + bt.Spread;
        var fights = s.In("day").Where(bt => bt.Kind is "pack").ToList();
        Assert.True(fights.Count >= 3);
        for (int i = 0; i < fights.Count; i++)
            for (int j = i + 1; j < fights.Count; j++)
            {
                var (a, c) = (fights[i], fights[j]);
                double gap = MathX.Dist(a.X, a.Z, c.X, c.Z) - Reach(a) - Reach(c);
                Assert.True(gap >= 20, $"{a.Id} and {c.Id}: {gap:0.0} m between their waking rings");
            }
        // Each pack 5-10 strong with its champion, and as many again in its waves (the road's boars, the charge's lesson,
        // 3-4 and no waves); the strongbox in its keepers' camp.
        foreach (var bt in s.In("day").Where(x => x.Kind == "pack"))
        {
            Assert.InRange(bt.Foes.Sum(f => f.N) + (bt.Captain != null ? 1 : 0), bt.Id == "boars" ? 3 : 5, bt.Id == "boars" ? 4 : 10);
            // (a pulse after a breath, r3, is a smaller beat: 2-4)
            foreach (var w in bt.Waves) Assert.InRange(w.Foes.Sum(f => f.N) + (w.Elite != null ? 1 : 0), w.After != null ? 2 : 4, w.After != null ? 4 : 10);
            if (bt.Id != "boars") Assert.NotEmpty(bt.Waves);
        }
        var box = s.Get("strongbox")!; var camp = s.Get(box.Guard!)!;
        Assert.InRange(MathX.Dist(box.X, box.Z, camp.X, camp.Z), 0, camp.Spread + 2);
    }

    [Fact]
    public void Every_beat_off_the_road_has_a_way_there_round_the_trees()
    {
        var s = Encounters.For("lowford")!;
        var col = ZoneMeta.Load("lowford").Collision();
        foreach (var bt in s.In("day").Where(x => x.Kind is "pack" or "chest"))
        {
            Assert.False(col.Blocked(bt.X, bt.Z, 0.7), bt.Id + " stands in a tree");
            var path = GroundPath.Find(col, 1, -84, bt.X, bt.Z, 0.8);
            Assert.True(path != null, bt.Id + ": no way there");
            Assert.True(MathX.Dist(path![^1].X, path[^1].Z, bt.X, bt.Z) < 1.5, $"{bt.Id}: the way ends at ({path[^1].X:0.0}, {path[^1].Z:0.0})");
        }
    }

    /// <summary>The Low Ford's night (M5, when: night): the beats from the fire to the ford, in order.</summary>
    static readonly string[] NightBeats = ["n_lone", "n_three", "n_first", "n_cart", "n_road1", "n_road2", "n_post", "n_road3", "n_road4", "n_ford"];

    [Fact]
    public void The_night_beats_load_and_rest_on_open_ground_by_the_road()
    {
        var s = Encounters.For("lowford")!;
        Assert.False(s.Draft);
        Assert.Equal(NightBeats, s.In("night").Select(b => b.Id));
        // (the day's beats are the day's: none of the night's leak in)
        Assert.DoesNotContain(s.In("day"), b => b.Id.StartsWith("n_"));
        var meta = ZoneMeta.Load("lowford");
        var col = meta.Collision();
        // Along the road north, the fire's end first; each pack's ground open and within 9 m of the road's line.
        var road = meta.Paths["ROAD"];
        double ToRoad(double x, double z) => Enumerable.Range(0, road.Length - 1).Min(i => SegDist(x, z, road[i], road[i + 1]));
        double lastZ = 200;
        foreach (var bt in s.In("night"))
        {
            Assert.True(bt.Z < lastZ, bt.Id + " is out of the road's order");
            lastZ = bt.Z;
            if (bt.Kind != "pack") continue;
            Assert.False(col.Blocked(bt.X, bt.Z, 0.7), bt.Id + " stands in a tree");
            Assert.True(ToRoad(bt.X, bt.Z) < 9, $"{bt.Id} is {ToRoad(bt.X, bt.Z):0.0} m off the road");
        }
        // The wagon's ditch: 8 risen, 3 bowmen and a charger whose charge is the dash's lane; sprung by the zone (r 0).
        var cart = s.Get("n_cart")!;
        Assert.Equal("ambush", cart.Kind);
        Assert.Equal(0, cart.R);
        Assert.Equal(("charge", "risen_warrior"), (cart.Tell, cart.TellBy));
        Assert.Equal(8, cart.Foes.Where(f => f.Def == "risen").Sum(f => f.N));
        Assert.Equal(3, cart.Foes.Where(f => f.Def == "risen_archer").Sum(f => f.N));
        Assert.Equal(1, s.Get("n_lone")!.Foes.Sum(f => f.N));
        Assert.Equal(3, s.Get("n_three")!.Foes.Sum(f => f.N));
        Assert.Equal("risen_warrior", s.Get("n_first")!.Captain);

        // Placed on the Low Ford's own ground: every foe of every pack on open ground (no tree, no wall, not the river).
        var b = new Battle(new BattleSetup
        {
            Seed = 5, Collision = col, Combat = true, Stats = BattleTests.BaseStats(), Weapons = [("oathblade", 1)], Ability = AbilityKind.ShieldBash,
            StartX = -7.5, StartZ = 87.5,
        });
        var n = new Encounters(s, b, new Dictionary<string, Fact>(), 1, 0, "night");
        n.Place();
        Assert.Equal(s.In("night").Where(x => x.Kind == "pack").Select(x => x.Id), n.Packs.Keys);
        foreach (var (id, list) in n.Packs)
        {
            var bt = s.Get(id)!;
            Assert.Equal(bt.Foes.Sum(f => f.N) + (bt.Captain != null ? 1 : 0), list.Count);
            foreach (var (e, _) in list)
            {
                Assert.False(col.Blocked(e.X, e.Z, 0.6), $"{id}: a foe in a tree at ({e.X:0.0}, {e.Z:0.0})");
                Assert.False(System.Math.Abs(e.Z - Prologue.RiverZ(e.X)) < 9 && System.Math.Abs(e.X) > 14, $"{id}: a foe in the river");
                Assert.StartsWith("night:", e.Tag);
            }
        }
        // (and the night's done keys are its own: a day's "day." key does not put a night beat down)
        Assert.Equal("night.n_lone", n.Key("n_lone"));
        Assert.False(n.Done("n_lone"));
        // A day instance on the same data places only the day's packs, as before.
        var d = new Encounters(s, Road(9), new Dictionary<string, Fact>(), 2, 1);
        d.Place();
        Assert.Equal(s.In("day").Where(x => x.Kind == "pack").Select(x => x.Id), d.Packs.Keys);
        Assert.Equal("wolves", d.RingOwed?.Id);
    }

    static double SegDist(double x, double z, double[] a, double[] c)
    {
        double dx = c[0] - a[0], dz = c[1] - a[1], l = dx * dx + dz * dz;
        double t = l <= 0 ? 0 : System.Math.Clamp(((x - a[0]) * dx + (z - a[1]) * dz) / l, 0, 1);
        return MathX.Dist(x, z, a[0] + t * dx, a[1] + t * dz);
    }
}
