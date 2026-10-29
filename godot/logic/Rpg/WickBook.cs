using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Rpg;

/// <summary>Why a wick lamp can't be planned or unplanned (None: it can).</summary>
public enum WickNo { None, NoWick, Unknown, Planned, Unplanned, Order, Turn, Full, Holds }

/* Each skill's wick plan (docs/design/CLASS_IDENTITY_AND_TALENTS.md 3.3).
 *
 * By day she plans the order a skill's lamps light: within a strand in order, one Turn at most, twelve at most.
 * The skill's rank is its points, so the lit lamps at rank r are the first r of its path: the plan, then Light my
 * way (the suggested strand in order, then the other strands' lead-ins). A skill she never planned follows Light
 * my way alone. By day the rank grows with her level; at night the ember ranks it, and the battle lights the next
 * lamp of the same path (Battle.Relight). The plan lives on the lamp layout, so it saves with her. */
public static class WickBook
{
    public enum Mode { None, Suggested, Plan }
    /// <summary>What the fights read: the plan (the game), Light my way alone, or no wicks (the harness's --wicks).</summary>
    public static Mode Lights = Mode.Plan;
    /// <summary>The harness's --turn: this strand lights first on every skill that has it.</summary>
    public static string? ForceTurn;

    static List<string>? Find(CharacterData ch, string skill) =>
        LampBook.Now(ch).Wicks.TryGetValue(skill, out var p) ? p : null;

    public static IReadOnlyList<string> PlanOf(CharacterData ch, string skill) => (IReadOnlyList<string>?)Find(ch, skill) ?? System.Array.Empty<string>();

    public static WickNo CanPlan(CharacterData ch, string skill, string lamp)
    {
        if (Wicks.Of(skill) == null) return WickNo.NoWick;
        if (Wicks.Lamp(skill, lamp) is not { } ln) return WickNo.Unknown;
        var (s, n) = ln;
        var plan = PlanOf(ch, skill);
        if (plan.Contains(lamp)) return WickNo.Planned;
        if (plan.Count >= Wicks.LampCount) return WickNo.Full;
        if (n > 1 && !plan.Contains(s.LampId(n - 1))) return WickNo.Order;
        if (n == Wicks.PerStrand && plan.Any(id => Wicks.IsTurn(skill, id))) return WickNo.Turn;
        return WickNo.None;
    }

    public static WickNo Plan(CharacterData ch, string skill, string lamp)
    {
        var why = CanPlan(ch, skill, lamp);
        if (why != WickNo.None) return why;
        var wicks = LampBook.Now(ch).Wicks;
        if (!wicks.TryGetValue(skill, out var plan)) wicks[skill] = plan = new List<string>();
        plan.Add(lamp);
        return WickNo.None;
    }

    /// <summary>A lamp comes out of the plan only when no later lamp of its strand stands on it.</summary>
    public static WickNo CanUnplan(CharacterData ch, string skill, string lamp)
    {
        if (Wicks.Of(skill) == null) return WickNo.NoWick;
        if (Wicks.Lamp(skill, lamp) is not { } ln) return WickNo.Unknown;
        var (s, n) = ln;
        var plan = PlanOf(ch, skill);
        if (!plan.Contains(lamp)) return WickNo.Unplanned;
        if (n < Wicks.PerStrand && plan.Contains(s.LampId(n + 1))) return WickNo.Holds;
        return WickNo.None;
    }

    public static WickNo Unplan(CharacterData ch, string skill, string lamp)
    {
        var why = CanUnplan(ch, skill, lamp);
        if (why != WickNo.None) return why;
        var plan = Find(ch, skill)!;
        plan.Remove(lamp);
        if (plan.Count == 0) LampBook.Now(ch).Wicks.Remove(skill);
        return WickNo.None;
    }

    public static void Reset(CharacterData ch, string skill) => LampBook.Now(ch).Wicks.Remove(skill);

    /// <summary>The order a skill's lamps light: the forced strand (the harness), the plan, then Light my way. Each
    /// candidate is taken only if it keeps the rules (its strand's lamps before it, one Turn), so the path is
    /// always a legal plan.</summary>
    public static string[] Path(IReadOnlyList<string> plan, string skill) => Path(plan, skill, ForceTurn);

    public static string[] Path(IReadOnlyList<string> plan, string skill, string? force)
    {
        if (Wicks.Of(skill) is not { } w) return System.Array.Empty<string>();
        var strands = Wicks.StrandsOf(skill).ToList();
        var want = new List<string>();
        if (force != null && strands.Find(s => s.Id == force) is { } forced)
            for (int n = 1; n <= Wicks.PerStrand; n++) want.Add(forced.LampId(n));
        want.AddRange(plan);
        if (strands.Find(s => s.Id == w.Suggested) is { } sug)
            for (int n = 1; n <= Wicks.PerStrand; n++) want.Add(sug.LampId(n));
        foreach (var s in strands)
            for (int n = 1; n < Wicks.PerStrand; n++) want.Add(s.LampId(n));
        var path = new List<string>(Wicks.LampCount);
        bool turn = false;
        foreach (var id in want)
        {
            if (path.Count >= Wicks.LampCount) break;
            if (path.Contains(id) || Wicks.Lamp(skill, id) is not { } ln) continue;
            var (s, n) = ln;
            if (n > 1 && !path.Contains(s.LampId(n - 1))) continue;
            if (n == Wicks.PerStrand) { if (turn) continue; turn = true; }
            path.Add(id);
        }
        return path.ToArray();
    }

    /// <summary>A survivor's path for a skill, by the mode the fights read.</summary>
    public static string[] Path(CharacterData ch, string skill) =>
        Lights == Mode.None ? System.Array.Empty<string>() : Path(Lights == Mode.Plan ? PlanOf(ch, skill) : System.Array.Empty<string>(), skill);

    /// <summary>The lamps lit at a rank: the first rank of the path.</summary>
    public static string[] Lit(CharacterData ch, string skill, int rank) => Path(ch, skill).Take(System.Math.Max(0, rank)).ToArray();

    /// <summary>The lamps a skill has lit in a fight now (its weapon's wick), or none.</summary>
    public static string[] Lit(Battle b, string skill) =>
        b.Weapons.Find(x => x.Id == skill)?.Wick?.Lit ?? System.Array.Empty<string>();

    /// <summary>The lamps a skill would light in this fight at a rank.</summary>
    public static string[] Lit(Battle b, string skill, int rank) =>
        b.WickPaths.TryGetValue(skill, out var p) ? p.Take(System.Math.Max(0, rank)).ToArray() : System.Array.Empty<string>();

    /// <summary>Every wick's path for a fight (BattleSetup.Wicks), or null when the fights read none.</summary>
    public static Dictionary<string, string[]>? Paths(CharacterData ch) =>
        Lights == Mode.None ? null : Wicks.Skills.ToDictionary(id => id, id => Path(ch, id));
}
