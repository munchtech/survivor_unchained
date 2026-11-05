using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Cinema;

/// <summary>
/// (P9 C13) A film's say over the zone's own creatures (the "foe" cue): the play's bodies stay in the world while a
/// film plays (Corvane laid where he fell, the Barrow Lord coming up the stair), so a film addresses them by def, as
/// the boss, or nearest a place, and for its length may hide one (a film that casts its own double of him), or draw it
/// dark (its glow, tint and carried light: the Barrow Lord a backlit shape, not his play's grave-green glow). The view
/// reads it each frame (CrowdView, BattleFx.Auras); the film's end clears it, after the zone's done has run (P6's done
/// removes Corvane's body, so the hidden body is never shown again).
/// </summary>
public static class FilmFoes
{
    /// <summary>How a creature is drawn for the film: hidden, its glow (null: its own), its tint scaled (r, g, b; null:
    /// its own), its carried light's level (1 its own, 0 out); `Fallen`: a body going down drawn at its fall's end
    /// (the film holds the world, so its fall's clock does not run: C13's Barrow Lord stood pale in his death's first
    /// frame), laid there as the fight's dead lie, and the look kept on the body where it lies.</summary>
    public sealed record Look(bool Hidden, double? Glow, (double R, double G, double B)? Tint, double Light, bool Fallen = false);

    static readonly Dictionary<(int Id, double Seed), Look> looks = new();

    public static bool Any => looks.Count > 0;

    /// <summary>The film's look on this creature, or null for its own.</summary>
    public static Look? Of(Enemy e) => Of(e.Id, e.Seed);

    /// <summary>The film's look on the body of this creature (a body laid where it fell keeps its id and seed).</summary>
    public static Look? Of(int id, double seed) => looks.Count == 0 ? null : looks.GetValueOrDefault((id, seed));

    public static void Set(Enemy e, Look look) => looks[(e.Id, e.Seed)] = look;

    public static void Clear() => looks.Clear();

    /// <summary>The zone's living creature a cue means: of def <paramref name="def"/> (any when null), the boss only when
    /// <paramref name="boss"/>, the nearest (x, z) when given (else the first). <paramref name="down"/>: a body that is
    /// down counts too, falling or already let go by the fight (its slot not yet taken by another): pass the pool's
    /// every slot (Pool.Items), not only the living.</summary>
    public static Enemy? Pick(IEnumerable<Enemy> living, string? def, bool boss, (double X, double Z)? near, bool down = false)
    {
        var them = living.Where(e => e != null && (e.Alive || down && e.State == EnemyState.Dying) && (def == null || e.Def.Id == def) && (!boss || e.Boss));
        return near is var (x, z) ? them.OrderBy(e => (e.X - x) * (e.X - x) + (e.Z - z) * (e.Z - z)).FirstOrDefault() : them.FirstOrDefault();
    }
}
