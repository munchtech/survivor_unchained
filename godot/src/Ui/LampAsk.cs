using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>What the Lamps screen asks of the board (docs/design/LAMPS_SCREEN_BRIEF.md §14), in one place. Classes
/// is adding these to LampBook and WickBook with the same signatures; until then each is a UI-side stand-in, and
/// when theirs lands each body here becomes a one-line call. Session undo needs nothing from Classes: the screen
/// keeps the lamps lit since it opened and puts them out with LampBook.Unlight, skipping only the place check.</summary>
public static class LampAsk
{
    /// <summary>§14.3: the unlit lamps to light, in lighting order, so each can be lit after the ones before it; the
    /// fewest, honoring gates and home. Empty when it is lit or can't be reached. Spare lamps are not checked.</summary>
    public static IReadOnlyList<string> PathTo(CharacterData ch, WorldState? w, string id)
    {
        var lit = LampBook.Now(ch).Lit.ToHashSet();
        if (lit.Contains(id) || Lamps.Find(id) is not { } goal || (goal.Home && goal.Calling != ch.Archetype)) return [];
        // Stand-in: breadth-first from the lit set over the roads. A lamp is passable when it is home (or no home lamp)
        // and its road's gate is met by the lit lamps plus those the path lights before it on the same road.
        var depth = new Dictionary<string, int>();
        foreach (var l in lit) if (Lamps.Find(l)?.Road is { } r) depth[r] = depth.GetValueOrDefault(r) + 1;
        var from = new Dictionary<string, string?>();
        bool Ok(string n, string? via)
        {
            if (Lamps.Find(n) is not { } d || (d.Home && d.Calling != ch.Archetype)) return false;
            if (d.Road == null || d.Gate <= 0) return true;
            int k = depth.GetValueOrDefault(d.Road);
            for (string? c = via; c != null && k < d.Gate; c = from[c]) if (Lamps.Find(c)?.Road == d.Road) k++;
            return k >= d.Gate || (Lamps.V2 && d.Calling != null && d.Calling != ch.Archetype && lit.Any(Unhouses));
        }
        var q = new Queue<string>();
        foreach (var l in lit) foreach (var n in Lamps.Next(l)) if (!lit.Contains(n) && !from.ContainsKey(n) && Ok(n, null)) { from[n] = null; q.Enqueue(n); }
        while (q.Count > 0)
        {
            var c = q.Dequeue();
            if (c == id) break;
            foreach (var n in Lamps.Next(c)) if (!lit.Contains(n) && !from.ContainsKey(n) && Ok(n, c)) { from[n] = c; q.Enqueue(n); }
        }
        if (!from.ContainsKey(id)) return [];
        var path = new List<string>();
        for (string? c = id; c != null; c = from[c]) path.Add(c);
        path.Reverse();
        return path;
    }

    static bool Unhouses(string id) => Lamps.Find(id) is { } d && d.Effects.Any(e => e.Rule == "blue.unhoused" && e.Phase <= Lamps.LivePhase);

    /// <summary>§14.3: light the whole path or nothing (on a refusal every lamp it lit goes back out, and the Flare
    /// is as it was).</summary>
    public static bool LightPath(CharacterData ch, WorldState? w, string id)
    {
        var p = PathTo(ch, w, id);
        if (p.Count == 0 || p.Count > LampBook.Spare(ch, w)) return false;
        var l = LampBook.Now(ch);
        var keep = l.Lit.ToList();
        var flare = l.Flare;
        foreach (var x in p)
            if (!LampBook.Light(ch, w, x)) { l.Lit.Clear(); l.Lit.AddRange(keep); l.Flare = flare; return false; }
        return true;
    }

    /// <summary>"Copy to II / III" (§9): the active layout, the whole build (type, lamps, Flare, wicks, links, the skills
    /// carried), copied over another. Only where layouts change (LampBook.LayoutsOpen). Stand-in until Classes has one.</summary>
    public static bool CopyLayout(CharacterData ch, int to, WorldState? w, string? zone)
    {
        var s = LampBook.State(ch);
        if (to < 0 || to >= s.Layouts.Count || to == s.Active || !LampBook.LayoutsOpen(w, zone)) return false;
        LampBook.Keep(ch);
        var a = s.Now;
        s.Layouts[to] = new LampLayout
        {
            Type = a.Type, Lit = a.Lit.ToList(), Flare = a.Flare,
            Wicks = a.Wicks.ToDictionary(kv => kv.Key, kv => kv.Value.ToList()),
            Links = new Dictionary<string, string>(a.Links), Carried = a.Carried.ToList(),
        };
        return true;
    }

    /// <summary>§14.4: why a lamp is dim (lit: asleep). Null when it feeds what she carries, or feeds nothing named.
    /// Otherwise the skills (ids) and tags any one of which would wake it, for the card to word.</summary>
    public static LampSleep? Sleeps(CharacterData ch, string id)
    {
        if (Lamps.Find(id) is not { } d || d.Feeds.Length == 0) return null;
        var carried = SkillBook.Carried(ch).Select(s => s.Id).ToHashSet();
        return d.Feeds.Any(carried.Contains) ? null : new LampSleep(d.Feeds, []);
    }

    /// <summary>§14.5: the skill a link fires (her pick, else Light my way's), the skills she may bind, and the pick.</summary>
    public static string? LinkPick(CharacterData ch, string link) => LampBook.Now(ch).Links.GetValueOrDefault(link);
    public static IReadOnlyList<string> LinkChoices(CharacterData ch, string link) => SkillBook.Carried(ch).Select(s => s.Id).ToList();
    public static bool SetLinkPick(CharacterData ch, string link, string skill)
    {
        if (!LinkChoices(ch, link).Contains(skill)) return false;
        LampBook.Now(ch).Links[link] = skill;
        return true;
    }

    /// <summary>§14.6: the next n lamps Light my way would light, in order, without lighting them.</summary>
    public static IReadOnlyList<string> Suggested(CharacterData ch, WorldState? w, int n)
    {
        // Stand-in: light them for real, read them, and put them back out (one thread; nothing else reads meanwhile).
        var lit = LampBook.Now(ch).Lit;
        var got = new List<string>();
        while (got.Count < n && LampBook.Suggest(ch, w) is { } s && LampBook.Light(ch, w, s)) got.Add(s);
        foreach (var s in got) lit.Remove(s);
        return got;
    }

    /// <summary>§14.8: the wick's whole sum for one skill, from the sim (no hidden multipliers). Null until Classes ships it.</summary>
    public static WickSumView? Sum(CharacterData ch, string skill, bool night) => null;
}

/// <summary>A dim lamp's reason: any one of these skills (ids) or tags, carried, wakes it.</summary>
public sealed record LampSleep(string[] Skills, string[] Tags);

/// <summary>"Damage 142 = 100 base · Hand ×1.15 · rites +12% · Turn: every 2nd swing heavy": the stat's name, its total,
/// then every part in order as (what, worded value), the Turn's line last when one is planned.</summary>
public sealed record WickSumView(string Stat, double Total, IReadOnlyList<(string What, string Value)> Parts);
