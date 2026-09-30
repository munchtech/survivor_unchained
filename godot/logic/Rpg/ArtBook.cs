using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Rpg;

/// <summary>How far an art has come with this survivor, and the facets chosen for it.</summary>
public sealed class ArtState
{
    public double Xp;
    public List<string> Facets = new();
}

/* The arts a survivor knows.
 *
 * A calling starts knowing its own two, a sprint, and the way of moving its
 * kin are taught (a warden's charge, a stalker's vault). More are learned
 * from manuals. One is carried at a time; it grows with use, and its ranks
 * open facets. Which art is in hand, and which facets, can be changed
 * wherever the survivor is safe (a town, a table); a facet newly opened can
 * be chosen anywhere. */
public static class ArtBook
{
    public static List<string> Starting(string archetype)
    {
        var a = Callings.Archetype(archetype);
        var o = new List<string>(a.Abilities);
        if (Abilities.Kin.TryGetValue(archetype, out var kin) && !o.Contains(kin)) o.Add(kin);
        if (!o.Contains("sprint")) o.Add("sprint");
        return o;
    }

    /// <summary>What the survivor knows (a survivor from before the book knows its calling's).</summary>
    public static List<string> Known(CharacterData ch)
    {
        if (ch.Known.Count == 0)
        {
            ch.Known.AddRange(Starting(ch.Archetype));
            if (ch.Ability != "" && !ch.Known.Contains(ch.Ability)) ch.Known.Add(ch.Ability);
        }
        return ch.Known;
    }

    public static bool Knows(CharacterData ch, string id) => Known(ch).Contains(id);

    public static bool CanLearn(CharacterData ch, string id) =>
        Abilities.Find(id) is { } def && Abilities.Learnable(def, ch.Archetype) && !Knows(ch, id);

    /// <summary>Learn an art (from a manual, a teacher). False if already known or not theirs to learn.</summary>
    public static bool Learn(CharacterData ch, string id)
    {
        if (!CanLearn(ch, id)) return false;
        Known(ch).Add(id);
        return true;
    }

    public static ArtState State(CharacterData ch, string id)
    {
        if (!ch.Arts.TryGetValue(id, out var s)) ch.Arts[id] = s = new ArtState();
        return s;
    }

    public static int Rank(CharacterData ch, string id) => Abilities.RankOf(ch.Arts.TryGetValue(id, out var s) ? s.Xp : 0);

    /// <summary>Facets opened by rank and not yet chosen.</summary>
    public static int OpenSlots(CharacterData ch, string id) => Math.Max(0, Abilities.FacetSlots(Rank(ch, id)) - Facets(ch, id).Count);

    /// <summary>The chosen facets that belong to the art and fit its rank.</summary>
    public static List<string> Facets(CharacterData ch, string id)
    {
        if (Abilities.Find(id) is not { } def || !ch.Arts.TryGetValue(id, out var s)) return new();
        return s.Facets.Where(f => def.Facets.Any(x => x.Id == f)).Take(Abilities.FacetSlots(Rank(ch, id))).ToList();
    }

    /// <summary>Choose a facet for an art, if a slot is open.</summary>
    public static bool Choose(CharacterData ch, string id, string facet)
    {
        if (Abilities.Find(id) is not { } def || def.Facets.All(f => f.Id != facet)) return false;
        var s = State(ch, id);
        s.Facets = Facets(ch, id);
        if (s.Facets.Contains(facet) || OpenSlots(ch, id) <= 0) return false;
        s.Facets.Add(facet);
        return true;
    }

    public static bool Unchoose(CharacterData ch, string id, string facet) => ch.Arts.TryGetValue(id, out var s) && s.Facets.Remove(facet);

    /// <summary>Carry a known art.</summary>
    public static bool Hold(CharacterData ch, string id)
    {
        if (!Knows(ch, id)) return false;
        ch.Ability = id;
        return true;
    }

    /// <summary>The art grows; the new rank if it rose, else 0.</summary>
    public static int Grow(CharacterData ch, string id, double xp)
    {
        if (xp <= 0 || id == "") return 0;
        int before = Rank(ch, id);
        State(ch, id).Xp += xp;
        int after = Rank(ch, id);
        return after > before ? after : 0;
    }

    /// <summary>How far to the next rank, 0..1 (1 at the last).</summary>
    public static double Progress(CharacterData ch, string id)
    {
        int r = Rank(ch, id);
        if (r >= Abilities.MaxRank) return 1;
        double xp = ch.Arts.TryGetValue(id, out var s) ? s.Xp : 0;
        double lo = Abilities.RankXp[r - 1], hi = Abilities.RankXp[r];
        return Math.Clamp((xp - lo) / (hi - lo), 0, 1);
    }

    /// <summary>The manual that teaches an art.</summary>
    public static string Manual(string id) => $"manual_{id}";

    /// <summary>An art a manual found now might teach: one of the ways of
    /// moving the survivor does not know yet, or null.</summary>
    public static string? Unknown(CharacterData ch, Core.Rng rng)
    {
        var pool = Abilities.All.Values.Where(a => a.Movement && CanLearn(ch, a.Id)).Select(a => a.Id).ToList();
        return pool.Count == 0 ? null : rng.Pick(pool);
    }
}
