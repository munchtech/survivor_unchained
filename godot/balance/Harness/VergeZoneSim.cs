using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Pilots;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Balance;

public sealed record VergeZoneSpec(int Seed, string Calling = "warden", string Bot = "human", int Tier = 2, int Level = 5, int Day = 1);
public sealed record VergeZoneResult(VergeZoneSpec Spec, bool Reached, int Falls, int Skipped, DensityMeasures Density, string StopReason = "", RunMeasures? Measures = null, string Build = "");

/// <summary>The existing StoryPlay day walk, using the spawner's packs and the campaign's pressing hands.</summary>
public static class VergeZoneSim
{
    /// <summary>(bd-sockets, the `storm` command) Grant the taught build before the fight and light every point (as
    /// DevVeteran.Dress does), and take these skills off her bar after (to measure what one adds).</summary>
    public static bool Lit;
    public static string[] Drop = Array.Empty<string>();
    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
    public static VergeZoneResult Play(VergeZoneSpec spec, TimeSpan? maxWallTime = null, double maxSeconds = 1800)
    {
        var clock = Stopwatch.StartNew();
        var wallLimit = maxWallTime ?? TimeSpan.FromSeconds(60);
        if (wallLimit <= TimeSpan.Zero) throw new ArgumentOutOfRangeException(nameof(maxWallTime));
        if (!double.IsFinite(maxSeconds) || maxSeconds <= 0) throw new ArgumentOutOfRangeException(nameof(maxSeconds));
        if (spec.Bot is not ("human" or "careless" or "deft" or "plain" or "idler")) throw new ArgumentException("Unsupported Verge bot: " + spec.Bot);
        var a = Callings.Archetype(spec.Calling);
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = spec.Calling, Background = "hunter", Palette = a.Palettes[0].Id,
            WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)spec.Seed);
        j.World.Facts["prologue.done"] = true;
        j.World.Facts[WorldTiers.Key] = spec.Tier;
        j.World.Day = spec.Day;
        j.World.Time = TimeOfDay.Day;
        while (j.Ch.Level < spec.Level) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        SurvivorUnchained.Play.DevVeteran.Road(j.Ch);
        switch (spec.Calling) { case "arcanist": j.Ch.Attributes.Wits += j.Ch.Points; break; case "stalker": j.Ch.Attributes.Finesse += j.Ch.Points; break; default: j.Ch.Attributes.Might += j.Ch.Points; break; }
        j.Ch.Points = 0;
        if (Lit || Drop.Length > 0) { TaughtBuilds.Grant(j.Ch, j.Ch.Level); if (Lit) WickBook.LightAll(j.Ch); }
        foreach (var d in Drop) SkillBook.Unslot(j.Ch, d);
        var meta = ZoneMeta.Load("verge");
        var host = new HeadlessHost(j, spec.Seed);
        var zone = new Verge(host, meta);
        var at = zone.ArrivalFrom("waystation");
        var b = j.StartBattle(true, meta.Collision(), Heightfield.Load(meta).HeightAt, at.X, at.Z, at.Facing, (uint)spec.Seed);
        host.Battle = b;
        var probe = new DensityProbe(b, () => DensityProbe.Verge(zone));
        var h = BattleHooks.Following(zone.Hooks);
        h.OnKill = (e, by) => { probe.Killed(e, by); j.Killed(e, by); zone.Hooks.OnKill?.Invoke(e, by); };
        h.OnPickup = p => (zone.Hooks.OnPickup?.Invoke(p) ?? true) && j.PickedUp(p);
        b.Hooks = h;
        zone.Begin(b);
        probe.Sample();
        var human = spec.Bot is "human" or "careless" or "idler" ? new Human(spec.Seed, spec.Bot == "careless") { Idle = spec.Bot == "idler" } : null;
        var hands = spec.Bot switch
        {
            "human" => PressHands.Human((uint)spec.Seed, human!.React),
            "careless" => PressHands.Careless((uint)spec.Seed, human!.React),
            "deft" => PressHands.Deft((uint)spec.Seed),
            "idler" => PressHands.Grip((uint)spec.Seed),
            _ => null,
        };
        if (human != null) human.Hands = hands;
        var meter = new RunMeter();
        string build = DevVeteran.Line(b, j);
        // As StoryPlay: nearest field pack, then the next nearest, and back to the entry. Quest camps are incidental.
        var pending = zone.Packs.Where(kv => kv.Key.StartsWith("field:") && kv.Value.Count > 0).Select(kv => kv.Key).ToList();
        var route = new List<string>();
        (double X, double Z) from = (b.Player.X, b.Player.Z);
        (double X, double Z) Home(string id) { var e = zone.Packs[id][0].E; return (e.HomeX, e.HomeZ); }
        while (pending.Count > 0)
        {
            string id = pending.MinBy(id => Dist(Home(id).X, Home(id).Z, from.X, from.Z))!;
            route.Add(id); pending.Remove(id); from = Home(id);
        }
        var entry = meta.Place("V", "entry");
        List<(double X, double Z)>? walk = null;
        (double X, double Z) walkGoal = default;
        int walkIx = 0;
        bool wasWalking = false;
        int k = 0, skipped = 0;
        double since = 0;
        bool reached = false;
        string stopReason = "simulation limit";
        int ticks = 0;
        while (ticks++ < Math.Ceiling(maxSeconds / ArenaSim.Dt) + route.Count + 1 && b.Time < maxSeconds && b.Player.Alive)
        {
            if (clock.Elapsed >= wallLimit) { stopReason = "wall-time limit"; break; }
            var p = b.Player;
            if (k < route.Count && zone.Packs[route[k]].All(m => !DensityProbe.Up(m))) { k++; since = b.Time; continue; }
            if (k < route.Count && b.Time - since > 90) { skipped++; k++; since = b.Time; continue; }
            var goal = k < route.Count ? Home(route[k]) : (entry.X + 4, entry.Z);
            var foe = b.Enemies.Living().Where(e => e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying &&
                (e.Wake <= 0 || e.Roused) && Dist(e.X, e.Z, p.X, p.Z) < 22).MinBy(e => Dist(e.X, e.Z, p.X, p.Z));
            bool fight = foe != null;
            if (k == route.Count && !fight && Dist(goal.Item1, goal.Item2, p.X, p.Z) < 7) { reached = skipped == 0; stopReason = reached ? "complete" : "skipped packs"; break; }
            bool inReach = foe != null && Dist(foe.X, foe.Z, p.X, p.Z) < Math.Max(1.5, Pilot.Reach(b));
            var (mx, mz) = spec.Bot == "idler" ? human!.Steer(b, null, goal: inReach ? null : goal)
                : human != null ? human.Steer(b, null, onward: goal) : Pilot.Steer(b, spec.Bot == "deft", onward: goal);
            bool walking = foe == null || !GroundPath.Clear(b.Collision, (p.X, p.Z), (foe.X, foe.Z), p.Radius);
            if (walking)
            {
                // Keep the route through combat pauses; a foe across a wall cannot pull her through that wall.
                bool displaced = !wasWalking && walk is { Count: > 0 } && !GroundPath.Clear(b.Collision, (p.X, p.Z), walk[walkIx], p.Radius);
                if (walk == null || walkGoal != goal || displaced)
                {
                    // The cross-zone return can exhaust the fine grid; the coarse grid still checks her radius.
                    walk = GroundPath.Find(b.Collision, p.X, p.Z, goal.Item1, goal.Item2, p.Radius)
                        ?? GroundPath.Find(b.Collision, p.X, p.Z, goal.Item1, goal.Item2, p.Radius, cell: 1);
                    walkGoal = goal; walkIx = 0;
                    if (walk is not { Count: > 0 }) { stopReason = "no walkable route"; break; }
                }
                while (walk != null && walkIx < walk.Count - 1 && Dist(p.X, p.Z, walk[walkIx].X, walk[walkIx].Z) < 0.5) walkIx++;
                var to = walk is { Count: > 0 } ? walk[walkIx] : goal;
                mx = to.Item1 - p.X; mz = to.Item2 - p.Z;
                double length = Math.Sqrt(mx * mx + mz * mz);
                if (length > 0) { mx /= length; mz /= length; }
            }
            wasWalking = walking;
            if (human != null) human.Act(b, j, mx, mz, null);
            else Pilot.Act(b, j, mx, mz, hands: hands);
            zone.Step(ArenaSim.Dt);
            b.Tick(ArenaSim.Dt, mx, mz);
            var evs = b.Events.Drain();
            probe.Observe(evs);
            meter.Step(b, b.Time, ArenaSim.Dt, evs, fight);
            zone.Frame(ArenaSim.Dt);
            host.Pass(ArenaSim.Dt);
        }
        if (!b.Player.Alive) stopReason = "fell";
        string diagnostic = $"{stopReason}; sim {b.Time:0.00}s, wall {clock.Elapsed.TotalSeconds:0.00}s, at ({b.Player.X:0.00},{b.Player.Z:0.00}), route {k}/{route.Count}, skipped {skipped}, alive {b.Player.Alive}";
        if (!reached) Console.Error.WriteLine($"verge/{spec.Bot}/s{spec.Seed}: {diagnostic}");
        var m = new RunMeasures();
        meter.Finish(b, b.Time, m, hands);
        return new(spec, reached, b.Player.Alive ? 0 : 1, skipped, probe.Finish(b.Time), diagnostic, m, build);
    }
}
