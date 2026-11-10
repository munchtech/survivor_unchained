using System;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using SurvivorUnchained.Content;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The Low Ford's ARPG beats A5-A10 (docs/story/TUTORIAL_COPY.md, M6), without a screen.</summary>
public class PrologueArpgTeachTests
{
    sealed record Setup(Journey J, FakeHost Host, Prologue Zone, Battle B, ZoneMeta Meta);

    static Setup Make()
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
        var meta = ZoneMeta.Load("lowford");
        var host = new FakeHost(j, meta);
        var zone = new Prologue(host, meta);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 5, ember: zone.Ember);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        return new Setup(j, host, zone, b, meta);
    }

    static void Run(Setup s, double seconds)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            s.B.Player.Hp = s.B.MaxHp;
            s.Zone.Step(1 / 60.0);
            s.B.Tick(1 / 60.0, 0, 0);
            s.B.Events.Drain();
            s.Zone.Frame(1 / 60.0);
            s.Host.Pass(1 / 60.0);
        }
    }

    static void Stand(Setup s, double x, double z) { s.B.Player.X = x; s.B.Player.Z = z; }

    static void KillPack(Setup s, string id)
    {
        for (int i = 0; i < 60 && s.Zone.Night!.Pending(id); i++) Run(s, 0.5);
        foreach (var e in s.Zone.Night!.Standing(id)) s.B.KillEnemy(e, true, null);
        Run(s, 0.1);
        Assert.True(s.Zone.Night.Done(id));
    }

    static void ToTheRoad(Setup s)
    {
        Run(s, 4);
        KillPack(s, "n_lone");
        KillPack(s, "n_three");
        Assert.Equal(Prologue.Stage.Road, s.Zone.Now);
    }

    static void ToThePost(Setup s)
    {
        ToTheRoad(s);
        KillPack(s, "n_first");
        var cart = s.Meta.Place("LOWFORD", "cart");
        Stand(s, cart.X, cart.Z + 5);
        Run(s, 0.1);
        for (int i = 0; i < 400 && !s.Zone.Sprung; i++) Run(s, 0.1);
        KillPack(s, "n_cart");
        var post = s.Meta.Place("LOWFORD", "post");
        Stand(s, post.X - 6, post.Z + 4);
        Run(s, 0.1);
        Assert.Equal(Prologue.Stage.Post, s.Zone.Now);
    }

    static Callout Offered(Setup s, string id)
    {
        var asked = s.Host.Asked.Where(c => c.Id == id).ToList();
        Assert.NotEmpty(asked);
        Assert.Single(asked.Select(c => (c.Title, c.Line, c.Kind)).Distinct());
        return asked[0];
    }

    static void ClearFoes(Setup s) { foreach (var e in s.B.Enemies.Living().ToList()) s.B.KillEnemy(e, false, null); }

    [Fact]
    public void A5_captain_waits_for_the_first_packs_captain_awake_and_near()
    {
        var s = Make();
        ToTheRoad(s);
        Assert.DoesNotContain(s.Host.Asked, c => c.Id == "captain");
        var bt = Encounters.For("lowford")!.Get("n_first")!;
        for (int i = 0; i < 200 && !s.Host.Asked.Any(c => c.Id == "captain"); i++) { Stand(s, bt.X, bt.Z + 6); Run(s, 0.1); }
        var c = Offered(s, "captain");
        Assert.Equal(("Captain", "Packs travel with a captain. The captain carries the better gear.", CalloutKind.Freeze), (c.Title, c.Line, c.Kind));
        Assert.True(c.Target.Safe && c.Target.Open);
        var cap = s.Zone.Night!.Captain("n_first")!;
        Assert.Equal("risen_warrior", cap.Def.Id);
        // (the arrow on his plate, over his head; his body ringed)
        Assert.True(c.Target.World!().Single().Y > s.Host.Look.HeightAt(cap.X, cap.Z) + 1.5);
        Assert.Single(c.Target.Ring!());
    }

    [Fact]
    public void A5a_lamp_is_inert_until_skills_p7_offers_a_lamp()
    {
        var s = Make();
        Run(s, 2);
        Assert.DoesNotContain(s.Host.Asked, c => c.Id == "lamp");
        string? offer = null;
        s.Zone.Seams.LampOffered = () => offer;
        Run(s, 0.5);
        Assert.DoesNotContain(s.Host.Asked, c => c.Id == "lamp");
        offer = "wick:sunder";
        Run(s, 0.1);
        var c = Offered(s, "lamp");
        Assert.Equal(("A lamp", "Each level lights a lamp on a skill. This one makes every third swing heavy.", CalloutKind.Panel), (c.Title, c.Line, c.Kind));
        Assert.Equal("wick:sunder", c.Target.Hud);
    }

    [Fact]
    public void A6_rare_is_inert_until_loot_m9_lays_a_rare_and_waits_for_calm()
    {
        var s = Make();
        Run(s, 2);
        ClearFoes(s);
        Run(s, 0.5);
        Assert.DoesNotContain(s.Host.Asked, c => c.Id == "rare");
        var p = s.B.Player;
        s.Zone.Seams.RareOnGround = () => (p.X + 2, p.Z);
        // (a foe within 8 m holds it)
        var foe = s.B.SpawnEnemy("risen", p.X + 3, p.Z, new Battle.SpawnOpts { Level = 1 })!;
        Run(s, 0.1);
        Assert.DoesNotContain(s.Host.Asked, c => c.Id == "rare");
        s.B.KillEnemy(foe, false, null);
        Run(s, 0.2);
        var c = Offered(s, "rare");
        Assert.Equal(("A Rare", "That beam is a Rare: rarer and better. Click its name to take it.", CalloutKind.Arrow), (c.Title, c.Line, c.Kind));
        Assert.Single(c.Target.World!());
    }

    [Fact]
    public void A6b_filter_comes_3_s_after_the_rare_is_taken_with_three_commons_and_a_key()
    {
        var s = Make();
        Run(s, 2);
        ClearFoes(s);
        var p = s.B.Player;
        (double, double)? rare = (p.X + 2, p.Z);
        int commons = 3;
        string? key = null;
        s.Zone.Seams.RareOnGround = () => rare;
        s.Zone.Seams.CommonsOnGround = () => commons;
        s.Zone.Seams.FilterKey = () => key;
        Run(s, 0.2);
        rare = null;   // (taken)
        Run(s, 4);
        Assert.DoesNotContain(s.Host.Asked, c => c.Id == "filter");   // (no binding yet: inert)
        key = "Alt";
        Run(s, 0.1);
        var c = Offered(s, "filter");
        Assert.Equal(("The filter", "Alt: hide what you don't want. Rares and better always show.", CalloutKind.Arrow), (c.Title, c.Line, c.Kind));
        Assert.Equal("filter", c.Target.Hud);
        // (and not within 3 s of the take, nor with fewer than three commons)
        var t = Make();
        Run(t, 2); ClearFoes(t);
        (double, double)? r2 = (t.B.Player.X + 2, t.B.Player.Z);
        t.Zone.Seams.RareOnGround = () => r2; t.Zone.Seams.FilterKey = () => "Alt"; t.Zone.Seams.CommonsOnGround = () => 2;
        Run(t, 0.2); r2 = null; Run(t, 2.5);
        Assert.DoesNotContain(t.Host.Asked, c => c.Id == "filter");
        Run(t, 1);
        Assert.DoesNotContain(t.Host.Asked, c => c.Id == "filter");
    }

    [Fact]
    public void A7_dash_freezes_on_the_wagons_charger_lane_with_her_on_it()
    {
        var s = Make();
        ToTheRoad(s);
        KillPack(s, "n_first");
        var cart = s.Meta.Place("LOWFORD", "cart");
        Stand(s, cart.X, cart.Z + 5);
        Run(s, 0.1);
        for (int i = 0; i < 400 && !s.Zone.Sprung; i++) Run(s, 0.1);
        Assert.True(s.Zone.Sprung);
        for (int i = 0; i < 300 && !s.Host.Asked.Any(c => c.Id == "dash"); i++)
        {
            if (s.Zone.Night!.Standing("n_cart").FirstOrDefault(e => e.Def.Id == "risen_warrior") is { } w) Stand(s, w.X + 1.2, w.Z);
            Run(s, 0.1);
        }
        var c = Offered(s, "dash");
        Assert.Equal(("Dash", "Red on the ground is a blow coming.\nD: roll through; nothing touches you mid-roll.", CalloutKind.Freeze), (c.Title, c.Line, c.Kind));
        Assert.Equal("dash", c.Target.Hud);
        Assert.Equal("dash", c.Answer);
        Assert.True(c.Target.Safe);
        Assert.Equal(Prologue.Stage.Ambush, s.Zone.Now);
    }

    [Fact]
    public void A7_falls_back_to_the_Knights_first_red_line_and_A8_names_the_elite()
    {
        var s = Make();
        ToThePost(s);
        var knight = s.B.Enemies.Living().Single(e => e.Tag == "knight");
        for (int i = 0; i < 600 && !(s.Host.Asked.Any(c => c.Id == "dash") && s.Host.Asked.Any(c => c.Id == "elite")); i++)
        {
            Stand(s, knight.X - 5, knight.Z);
            Run(s, 0.1);
        }
        var e = Offered(s, "elite");
        Assert.Equal(("An elite", "Elites carry a name, a bar and an affix. Read the affix before you close.", CalloutKind.Freeze), (e.Title, e.Line, e.Kind));
        Assert.True(e.Target.World!().Single().Y > s.Host.Look.HeightAt(knight.X, knight.Z) + 1.5);
        var d = Offered(s, "dash");
        Assert.Equal("Red on the ground is a blow coming.\nD: roll through; nothing touches you mid-roll.", d.Line);
        Assert.True(d.Target.Open);
        Assert.NotNull(d.Target.Ring);
    }

    [Fact]
    public void A9_post_points_at_the_lit_post_on_the_corner_map_2_s_after()
    {
        var s = Make();
        Run(s, 2);
        s.B.LampLitAt = s.B.Time;
        Run(s, 1.5);
        Assert.DoesNotContain(s.Host.Asked, c => c.Id == "post");
        Run(s, 0.6);
        var c = Offered(s, "post");
        Assert.Equal(("Lamp-post", "Fall, and you rise here. M: travel between lit posts.", CalloutKind.Arrow), (c.Title, c.Line, c.Kind));
        Assert.StartsWith("map:", c.Target.Hud);
    }

    [Fact]
    public void A10_raiser_rings_the_Grave_Caller_and_retires_the_art()
    {
        var s = Make();
        ToThePost(s);
        s.B.KillEnemy(s.B.Enemies.Living().Single(e => e.Tag == "knight"), true, null);
        Run(s, 0.1);
        Stand(s, 0, 18);
        Run(s, 0.1);
        Assert.Equal(Prologue.Stage.Barrow, s.Zone.Now);
        var caller = s.B.Enemies.Living().Single(e => e.Tag == "caller");
        for (int i = 0; i < 300 && !s.Host.Asked.Any(c => c.Id == "raiser"); i++) { Stand(s, caller.X + 8, caller.Z); Run(s, 0.1); }
        var c = Offered(s, "raiser");
        Assert.Equal(("Raiser", "It raises the dead. Hover it to target it, and kill it first.", CalloutKind.Freeze), (c.Title, c.Line, c.Kind));
        Assert.Single(c.Target.Ring!());
        Assert.DoesNotContain(s.Host.Asked, c => c.Id is "art" or "red_line" or "day_hover");
    }
}
