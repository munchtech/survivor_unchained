using System;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Thornhollow Verge, run without a screen (Play/Zones/Verge.cs).</summary>
public class VergeTests
{
    sealed record Setup(Journey J, FakeHost Host, Verge Zone, Battle B, ZoneMeta Meta);

    static Setup Make(TimeOfDay time = TimeOfDay.Day, Journey? j = null)
    {
        var a = Callings.Archetype("warden");
        j ??= Journey.Begin(new CreationChoice
        {
            Name = "Ashe", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 42);
        j.World.Time = time;
        var meta = ZoneMeta.Load("verge");
        var host = new FakeHost(j, meta);
        var zone = new Verge(host, meta);
        var ground = Heightfield.Load(meta);
        var at = zone.ArrivalFrom("waystation");
        var b = j.StartBattle(true, meta.Collision(), ground.HeightAt, at.X, at.Z, at.Facing, 11);
        b.Hooks = zone.Hooks;
        host.Battle = b;
        zone.Begin(b);
        return new Setup(j, host, zone, b, meta);
    }

    static void Run(Setup s, double seconds, double mx = 0, double mz = 0)
    {
        for (double t = 0; t < seconds; t += 1 / 60.0)
        {
            s.Zone.Step(1 / 60.0);
            s.B.Tick(1 / 60.0, mx, mz);
            s.B.Events.Drain();
            s.Host.Pass(1 / 60.0);
        }
    }

    static Interactable I(Setup s, string id) => s.Zone.Interactables.Single(i => i.Id == id);

    [Fact]
    public void Arriving_starts_the_day_and_the_tracker()
    {
        var s = Make();
        Assert.Same(Atmospheres.Day, s.Host.Air);
        Assert.Contains(s.Host.Announced, a => a.Title == "zone");
        // Quiet at the gate: nothing near it, and nothing coming.
        Run(s, 10);
        var p = s.B.Player;
        Assert.DoesNotContain(s.B.Enemies.Living(), e => e.Disposition == Disposition.Hostile && (e.Roused || Math.Sqrt((e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z)) < 25));
    }

    [Fact]
    public void By_day_the_wood_keeps_its_packs_where_they_lie_until_you_come()
    {
        var s = Make();
        Assert.False(s.B.EmberOn);
        var packs = s.B.Enemies.Living().Where(e => e.Disposition == Disposition.Hostile && e.Wake > 0).ToList();
        Assert.True(packs.Count > 12, $"{packs.Count} resting");
        // Nothing comes looking for you while you keep your distance.
        Run(s, 20);
        Assert.All(packs.Where(e => e.Alive), e => Assert.False(e.Roused));
        Assert.Equal(packs.Count, s.B.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile && e.Wake > 0));
        // Go close to one, and it wakes, and its fellows with it.
        var one = packs.First(e => e.Def.Id == "wolf");
        s.B.Player.X = one.X + 6; s.B.Player.Z = one.Z;
        Run(s, 1);
        Assert.True(one.Roused);
        Assert.All(packs.Where(o => o.HomeX == one.HomeX && o.HomeZ == one.HomeZ), o => Assert.True(o.Roused));
        // Putting them down teaches the survivor.
        double xp = s.J.Ch.Xp;
        s.J.Killed(one, true);
        Assert.True(s.J.Ch.Xp > xp);
    }

    [Fact]
    public void After_dark_the_ember_burns_through_and_pulls_you_into_an_arena()
    {
        // None by day.
        Assert.DoesNotContain(Make().Zone.Interactables, i => i.Id.StartsWith("scar:"));
        var s = Make(TimeOfDay.Night);
        var scars = s.Zone.Interactables.Where(i => i.Id.StartsWith("scar:")).ToList();
        Assert.InRange(scars.Count, 2, 4);
        Assert.Contains(s.Zone.MapMarks(), m => m.Kind == MarkKind.Danger && m.Label.StartsWith("The Scar"));
        // Stepping in pulls you into an arena held by that part of the wood's people, and brings you back where you stood.
        var dead = scars.Single(i => i.Name == "The Scar at the Sealed Door");
        s.B.Player.X = dead.X; s.B.Player.Z = dead.Z;
        dead.Act();
        var spec = s.Host.Entered!;
        Assert.Equal("dead", spec.People);
        Assert.Equal("verge", spec.ReturnZone);
        Assert.Equal(dead.X, spec.ReturnX, 3);
        // Won, it is out for the rest of the night.
        s.J.Apply(spec.OnWin!);
        var again = Make(TimeOfDay.Night, s.J);
        Assert.DoesNotContain(again.Zone.Interactables, i => i.Name == "The Scar at the Sealed Door");
    }

    [Fact]
    public void The_wreck_gives_up_the_manifest_once()
    {
        var s = Make();
        var wreck = I(s, "wreck");
        Assert.True(wreck.When!());
        wreck.Act();
        Assert.Contains(s.J.Ch.Pack, p => p?.Def == "caravan_manifest");
        Assert.Contains("wreck", s.J.World.Quests["caravan"].Entries);
        Assert.False(wreck.When!());
        Assert.NotEmpty(s.Host.Said);
    }

    [Fact]
    public void The_watch_fire_lights_and_rests_you_once()
    {
        var s = Make();
        Assert.False(I(s, "postrest").When!());
        I(s, "postfire").Act();
        Assert.True(I(s, "postrest").When!());
        s.B.Player.Hp = 5;
        I(s, "postrest").Act();
        Assert.Equal(s.B.MaxHp, s.B.Player.Hp);
        Assert.Contains("fire", s.Host.Saved);
        Assert.NotNull(I(s, "postrest").Locked!());
    }

    [Fact]
    public void Fire_opens_the_brambles()
    {
        var s = Make();
        var br = s.Meta.Refs.GetProperty("brambles")[0];
        int col = br.GetProperty("collider").GetInt32();
        string node = br.GetProperty("node").GetString()!;
        Assert.True(s.Host.FakeLook.Shown(node));
        s.Zone.Hooks.OnHitProp!("bramble:0", col, School.Fire, 5, br.GetProperty("x").GetDouble(), br.GetProperty("z").GetDouble());
        Assert.False(s.Host.FakeLook.Shown(node));
        Assert.DoesNotContain(s.B.Collision.All(), c => c.Id == col);
        Assert.Contains(s.Host.Said, l => l.Contains("brambles go up"));
    }

    [Fact]
    public void Greymuzzle_waits_at_the_hollow_and_his_death_is_remembered()
    {
        var s = Make();
        var hollow = s.Meta.Place("V", "hollow");
        s.B.Player.X = hollow.X + 20; s.B.Player.Z = hollow.Z;
        Run(s, 0.5);
        var grey = s.B.Enemies.Living().Single(e => e.Tag == "greymuzzle");
        s.B.KillEnemy(grey, true, null);
        Assert.Equal("dead", s.J.World.Fact("greymuzzle").Str);
        Assert.Contains("alpha_dead", s.J.World.Quests["beasts"].Entries);
        Assert.Contains(s.J.World.History, h => h.Id == "killed_greymuzzle");
    }

    [Fact]
    public void Breaking_the_pump_stops_the_wheel_and_its_light()
    {
        var s = Make();
        var pump = I(s, "pump");
        Assert.Null(pump.Locked!());
        pump.Act();
        Assert.Equal("broken", s.J.World.Fact("dig.pump").Str);
        Assert.Contains("pump_wheel", s.Host.FakeLook.Stopped);
        Assert.False(pump.When!());
    }

    [Fact]
    public void Every_thing_that_can_be_done_can_be_done()
    {
        // Every interactable offered and not refused runs (its effects are
        // valid rules, its lines are there), the map and the sound read.
        var s = Make(TimeOfDay.Night);
        s.J.GiveItem("blasting_ember");
        foreach (var it in s.Zone.Interactables.ToList())
        {
            if (it.When?.Invoke() == false || it.Locked?.Invoke() != null) continue;
            it.Act();
        }
        Run(s, 8);
        Assert.NotEmpty(s.Zone.MapMarks());
        _ = s.Zone.Ambience(0, 0);
        s.Zone.Frame(1 / 60.0);
        Assert.Equal("waystation", s.Host.Travelled?.Zone);
        Assert.Contains("moonpetal", s.J.Ch.Pack.Where(p => p != null).Select(p => p!.Def));
    }
}
