using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play.Pilots;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

public sealed record DensityGroup(string Id, IReadOnlyList<(Enemy E, double Seed)> Members, bool Cleared);

/// <summary>Adapts the spawners' member lists and the battle's events without controlling either.</summary>
public sealed class DensityProbe(Battle battle, Func<IEnumerable<DensityGroup>> groups)
{
    public DensityRecorder Recorder { get; } = new();
    readonly Dictionary<(int, double), string> membership = new();

    void Sync()
    {
        foreach (var g in groups())
        {
            var p = Recorder.Pack(g.Id);
            p.Cleared = g.Cleared;
            foreach (var (e, seed) in g.Members)
            {
                membership[(e.Id, seed)] = g.Id;
                if (e.Seed == seed && e.Elite && !e.Boss) p.Elite = true;
            }
        }
    }
    public void Killed(Enemy e, bool byPlayer)
    {
        Sync();
        Recorder.Kill(battle.Time, membership.GetValueOrDefault((e.Id, e.Seed)), byPlayer && e.Disposition != Disposition.Ally);
    }
    public void Observe(IReadOnlyList<CombatEvent> events)
    {
        Sync();
        foreach (var ev in events)
            if (ev is Ev.Hit { Amount: > 0 } hit)
                Recorder.Hit(hit.Time, membership.GetValueOrDefault((hit.Target, hit.TargetSeed)));
        Sample();
    }
    public void Sample()
    {
        var p = battle.Player;
        bool near = battle.Enemies.Living().Any(e => e.Disposition == Disposition.Hostile &&
            e.State is not (EnemyState.Dying or EnemyState.Burrowed) &&
            Math.Sqrt((e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z)) - e.Radius <= Pilot.EngageRange(battle, e));
        Recorder.Sample(battle.Time, near);
    }
    public DensityMeasures Finish(double seconds) { Sync(); return Recorder.Finish(seconds); }

    public static IEnumerable<DensityGroup> LowFord(Prologue zone)
    {
        foreach (var enc in new[] { zone.Night, zone.Day })
        {
            if (enc == null) continue;
            foreach (var (id, members) in enc.Packs)
                yield return new(enc.Phase + ":" + id, members, enc.DownAt.ContainsKey(id));
            // Placed champions have their own spawner keys; pack captains already belong to their pack.
            foreach (var (id, member) in enc.Champions)
                if (!enc.Packs.ContainsKey(id))
                    yield return new(enc.Phase + ":" + id, new[] { member }, !Up(member));
        }
    }
    public static bool Up((Enemy E, double Seed) member) => member.E.Seed == member.Seed &&
        member.E.Alive && member.E.State != EnemyState.Dying;
    public static IEnumerable<DensityGroup> Verge(Verge zone) => zone.Packs.Select(kv =>
        new DensityGroup(kv.Key, kv.Value, kv.Value.Count > 0 && kv.Value.All(m => !Up(m))));
}
