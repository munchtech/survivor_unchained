using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Balance;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Corvane in the doorway (Play/Story/Corvane.cs, Play/Bosses/CorvaneStory.cs): the court that opens
/// Behind the Sealed Door. The talk, the raise, the hold, the signature's tell, the rising, the walk-away and the loss.</summary>
[Collection("Balance")]
public class CorvaneTests
{
    const double Dt = 1 / 60.0;

    static StoryNightTests.Night Court(Action<Journey>? before = null)
    {
        var a = Callings.Archetype("warden");
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = "warden", Background = "hunter", Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 3u);
        before?.Invoke(j);
        var spec = StoryFights.Spec("vault", j.Ctx, "verge", 0, 0, 0);
        spec.Tier = 1;
        Arenas.Begin(j.World, spec);
        var map = MapGen.Generate(spec.Map);
        var host = new HeadlessHost(j, 3);
        var zone = new StoryNight(host, map, spec, StoryScripts.For(spec.Id)!);
        var at = zone.ArrivalFrom(null);
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, 3u, arena: true, ember: true);
        b.Hooks = BattleHooks.Following(zone.Hooks);
        host.Battle = b;
        zone.Begin(b);
        b.GreatOwed = 0;
        return new StoryNightTests.Night(j, host, zone, b, spec);
    }

    /// <summary>StoryNightTests.Step, but the events are kept (in `log`) before they are drained.</summary>
    static double Run(StoryNightTests.Night n, List<(double T, CombatEvent E)> log, double seconds, bool keep = true, Action<double>? each = null, Func<bool>? until = null)
    {
        double t = 0;
        for (; t < seconds; t += Dt)
        {
            n.Zone.Step(Dt);
            n.Zone.Frame(Dt);
            n.B.Tick(Dt, 0, 0);
            foreach (var e in n.B.Events.Drain()) log.Add((n.B.Time, e));
            n.Host.Pass(Dt);
            n.B.PendingLevels = 0; n.B.PendingBlessings.Clear(); n.B.GreatOwed = 0;
            if (keep) n.B.Player.Hp = n.B.MaxHp;
            each?.Invoke(t);
            if (n.Host.Result != null || until?.Invoke() == true) break;
        }
        return t;
    }

    static Enemy Him(StoryNightTests.Night n) => n.B.Enemies.Items.First(e => e.Alive && e.Def.Id == "corvane");
    static bool Raised(StoryNightTests.Night n) => n.Zone.Beat?.Goal == "Bring down Corvane";
    static bool Fact(StoryNightTests.Night n, string k) => n.J.World.Fact(k).Truthy;
    static bool Shut(StoryNightTests.Night n) => n.J.World.Quests.TryGetValue("vault", out var q) && q.Entries.Contains("shut");

    /// <summary>Talk (raise by default) until the raise.</summary>
    static void ToRaise(StoryNightTests.Night n, List<(double, CombatEvent)> log) => Run(n, log, 20, until: () => Raised(n));

    [Fact]
    public void The_court_plays_start_to_finish_and_opens_the_door()
    {
        var n = Court();
        var log = new List<(double T, CombatEvent E)>();
        var g = VaultOpened.Ground.Gates.First(x => x.Id == "door");
        double mx = (g.X0 + g.X1) / 2, mz = (g.Z0 + g.Z1) / 2;
        Assert.True(n.B.Collision.Blocked(mx, mz, 0.5));
        ToRaise(n, log);
        Assert.True(Raised(n));
        Assert.False(Fact(n, "corvane.rose"));
        // A fight of the Ford-Warden's length, then he is brought down.
        var him = Him(n);
        Run(n, log, 62, each: _ => { n.B.Player.X = him.X - 1.5; n.B.Player.Z = him.Z; Assert.False(Fact(n, "corvane.rose")); }, until: () => Fact(n, "corvane.rose"));
        Assert.False(Fact(n, "corvane.rose"));
        him.HpFloor = 0;
        him.Hp = 1;
        Run(n, log, 20, each: _ => { n.B.Player.X = him.X - 1.5; n.B.Player.Z = him.Z; him.Hp = Math.Min(him.Hp, 1); }, until: () => Fact(n, "corvane.rose"));
        Assert.True(Fact(n, "corvane.rose"));
        Run(n, log, 60, until: () => n.B.Collision.Blocked(mx, mz, 0.5) == false && n.Zone.BeatIx > 0 && n.Zone.Beat?.Goal == "Bring down the Decurion");
        Assert.Contains(log, x => x.E is Ev.Cue c && c.Id == "door_sigil");
        Assert.False(n.B.Collision.Blocked(mx, mz, 0.5));
        Assert.Equal("Bring down the Decurion", n.Zone.Beat!.Goal);
    }

    [Fact]
    public void The_walk_away_lets_the_night_go_without_a_mark()
    {
        var n = Court();
        var log = new List<(double T, CombatEvent E)>();
        SceneTalk.Chooser = (c, node, shown) => node == "lie_down" ? shown.First(x => !x.Ends).Index : null;
        try { Run(n, log, 30, until: () => n.Host.Result != null); }
        finally { SceneTalk.Chooser = null; }
        Assert.False(Fact(n, "corvane.rose"));
        Assert.False(Fact(n, "corvane.carried"));
        Assert.False(Shut(n));
        Assert.True(n.Zone.Over);
        Assert.NotNull(n.Host.Result);
        Assert.False(Fact(n, "arena.last.fell"));
        Assert.True(n.Host.Result!.Spec.WalkedAway);
        Assert.Equal(Doorway.WalkAway, n.Host.Result.Spec.EndLost);
    }

    [Fact]
    public void A_loss_with_no_rise_left_is_carried_home_and_the_vault_stays_open()
    {
        var n = Court(j => j.World.Facts["chapter.done"] = true);
        var log = new List<(double T, CombatEvent E)>();
        ToRaise(n, log);
        Assert.True(Raised(n));
        var him = Him(n);
        Run(n, log, 6, each: _ => { n.B.Player.X = him.X - 1.5; n.B.Player.Z = him.Z; });
        Run(n, log, 30, keep: false, each: _ => { n.B.Player.X = him.X - 1.5; n.B.Player.Z = him.Z; n.B.Player.Hp = 0; }, until: () => n.Host.Result != null);
        Assert.NotNull(n.Host.Result);
        Assert.True(Fact(n, "corvane.carried"));
        Assert.False(Fact(n, "corvane.rose"));
        Assert.False(Shut(n));
        var node = Dialogue.Find("chid")!.Nodes["carried_chid"];
        Assert.Equal(0, Dialogue.PickIndex(node.Text, n.J.Ctx));
    }

    [Fact]
    public void He_does_not_strike_in_the_hold_after_the_raise()
    {
        var n = Court();
        var log = new List<(double T, CombatEvent E)>();
        ToRaise(n, log);
        Assert.True(Raised(n));
        var him = Him(n);
        log.Clear();
        Run(n, log, 2.4, each: _ => { n.B.Player.X = him.X - 1.2; n.B.Player.Z = him.Z; });
        Assert.DoesNotContain(log, x => x.E is Ev.PlayerHit h && h.Amount > 0);
        Assert.DoesNotContain(log, x => x.E is Ev.Telegraph);
    }

    [Fact]
    public void His_signature_tell_comes_seven_tenths_before_its_mark()
    {
        var n = Court();
        var log = new List<(double T, CombatEvent E)>();
        ToRaise(n, log);
        var him = Him(n);
        Run(n, log, 15, each: _ => { n.B.Player.X = him.X + 4; n.B.Player.Z = him.Z; }, until: () => log.Any(x => x.E is Ev.Telegraph t && t.Tell == "pull"));
        var bark = log.First(x => x.E is Ev.Bark b && b.Text == "Lie down.");
        var tell = log.First(x => x.E is Ev.Telegraph t && t.Tell == "pull");
        Assert.InRange(tell.T - bark.T, 0.7 - 2 * Dt, 0.7 + 2 * Dt);
    }
}
