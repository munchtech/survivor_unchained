using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Storybook;
using SurvivorUnchained.World;
using SurvivorUnchained.Content;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>(M6, docs/story/TUTORIAL_COPY.md A11b, A12, A14) The Flare is lent: none on the Low Ford road, the ember's
/// at C02's hand-back, taken by the dawn page, lit for good at the Waystation's lamp.</summary>
public class PrologueFlareLentTests
{
    sealed record Setup(Journey J, FakeHost Host, Prologue Zone, Battle B, ZoneMeta Meta);

    static Journey NewJourney()
    {
        var a = Callings.Archetype("warden");
        return Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
    }

    static Setup Make(Journey? journey = null)
    {
        var j = journey ?? NewJourney();
        var meta = ZoneMeta.Load("lowford");
        var host = new FakeHost(j, meta);
        var zone = new Prologue(host, meta) { Draft = false };
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

    /// <summary>Straight to the ford and into the Warden's fight (C02 handed back as captions).</summary>
    static Setup AtTheWarden()
    {
        var s = Make();
        var ford = s.Meta.Place("LOWFORD", "ford");
        typeof(Prologue).GetMethod("Go", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance)!.Invoke(s.Zone, [Prologue.Stage.ToFord]);
        Stand(s, ford.X, ford.Z + 12);
        Run(s, 0.1);
        Run(s, 7);
        Assert.Equal(Prologue.Stage.Boss, s.Zone.Now);
        return s;
    }

    [Fact]
    public void She_has_no_Flare_on_the_road_before_C02()
    {
        var s = Make();
        Assert.Null(s.B.Flare);
        Assert.Equal(0, s.B.FlareMeter);
        Run(s, 2);
        Assert.Null(s.B.Flare);
        Assert.False(s.B.FlareReady);
        Assert.False(s.B.UseFlare(1, 0));
    }

    [Fact]
    public void The_ember_lends_it_full_at_the_Warden_and_A11b_follows_A11()
    {
        var s = AtTheWarden();
        Assert.NotNull(s.B.Flare);
        Assert.True(s.B.FlareReady);
        Assert.Equal(Battle.FlareFull, s.B.FlareMeter, 3);
        Run(s, 3.5);
        Assert.Contains(s.Host.Asked, c => c.Id == "lamps");
        s.Host.TaughtIds.Add("lamps");
        Run(s, 0.2);
        var a = s.Host.Asked.Last(c => c.Id == "flare");
        Assert.Equal("The Flare", a.Title);
        Assert.Equal(CalloutKind.Freeze, a.Kind);
        Assert.Equal("The ember lends you its fire for this fight.\nF: break a lamp.", a.Line);
        Assert.Equal("flare", a.Answer);
        Assert.Equal("lamps", a.After);
        Assert.Equal(3, a.Gap);
        Assert.Equal("art", a.Target.Hud);
        Assert.Single(a.Target.World!());
    }

    [Fact]
    public void The_dawn_page_takes_it_and_the_banner_says_so_and_the_day_runs_without()
    {
        var s = AtTheWarden();
        s.B.KillEnemy(s.B.Enemies.Living().Single(e => e.Tag == "warden"), true, null);
        Run(s, 12);
        foreach (var l in s.B.Pickups.Living().Where(k => k.Loot is (int)LootTier.Legendary or (int)LootTier.Storied).ToList()) s.B.Pickups.Release(l);
        for (int i = 0; i < 400 && s.Host.Stories.Count == 0; i++) Run(s, 0.1);
        Assert.True(s.Zone.Now >= Prologue.Stage.Dawn);
        Assert.Equal("sb_dawn", Assert.Single(s.Host.Stories));
        Assert.Null(s.B.Flare);
        Assert.Equal(0, s.B.FlareMeter);
        Assert.True(s.J.World.Fact(Prologue.FlareOutFact).Truthy);
        Run(s, 4);
        var ban = Assert.Single(s.Host.Announced, a => a.Title == "The Flare goes out");
        Assert.Equal("Lent for the night. It burns again at the Waystation's lamp.", ban.Sub);
        // (the dawn card, Douse's "The ember goes out" and the level banner's traits are retired)
        Assert.Empty(s.Host.Dawns);
        Assert.DoesNotContain(s.Host.Announced, a => a.Title == "The ember goes out" || (a.Sub ?? "").Contains("trait"));
        Run(s, 12);
        Assert.Null(s.B.Flare);
        // The next battle on the road (a reload at the Low Ford) still has none until the lamp.
        var j = s.J;
        var meta = ZoneMeta.Load("lowford");
        var b2 = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, 0, 0, 0, 5);
        Assert.Null(b2.Flare);
    }

    [Fact]
    public void The_square_s_lamp_lights_it_for_good()
    {
        var j = NewJourney();
        j.World.Facts["prologue.done"] = true;
        j.World.Facts[Prologue.FlareOutFact] = true;
        var meta = ZoneMeta.Load("waystation");
        var host = new FakeHost(j, meta);
        var zone = new Waystation(host, meta);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(false, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, 3);
        host.Battle = b;
        zone.Begin(b);
        Assert.Null(b.Flare);
        var post = LampPosts.Get("waystation.square")!;
        b.Player.X = post.X + 10; b.Player.Z = post.Z;
        zone.Frame(1 / 30.0);
        Assert.Null(b.Flare);
        Assert.False(j.World.Fact(Prologue.FlareLitFact).Truthy);
        b.Player.X = post.X + Waystation.FlareLampReach - 0.5;
        zone.Frame(1 / 30.0);
        Assert.True(j.World.Fact(Prologue.FlareLitFact).Truthy);
        Assert.NotNull(b.Flare);
        var ban = Assert.Single(host.Announced, a => a.Title == "The Flare");
        Assert.Equal("Lit for good. F", ban.Sub);
        // Every later battle carries it.
        var lf = ZoneMeta.Load("lowford");
        Assert.NotNull(j.StartBattle(true, lf.Collision(), Heightfield.Load(lf).HeightAt, 0, 0, 0, 5).Flare);
    }

    [Fact]
    public void A_save_past_the_prologue_keeps_its_Flare()
    {
        var j = NewJourney();
        j.World.Facts["prologue.done"] = true;
        var s = Make(j);
        Assert.NotNull(s.B.Flare);
    }

    [Fact]
    public void Sb_dawn_is_one_plate_over_the_dawn_line()
    {
        var f = StoryFile.Load("sb_dawn");
        Assert.Empty(f.Problems());
        Assert.Equal("sb_stay_where_they_reach", f.Conversation);
        var plate = Assert.Single(f.Plates);
        Assert.Contains(plate.Layers, l => l.Image.EndsWith("sb00/p3d/dawn.png"));
        var line = Assert.Single(new StoryTimeline(f).Cues, c => c.Cue.Do == "line");
        Assert.Equal("dawn", line.Cue.Str("id"));
        Assert.InRange(f.End, 8, 10);
    }
}
