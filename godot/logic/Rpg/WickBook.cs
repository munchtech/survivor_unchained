using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Rpg;

/// <summary>"Damage 142 = 100 base · rank 3 ×1.20 · wicks +12% · Turn: Twin Swing ×1.10": the stat's name, its total,
/// then every part in order as (what, worded value), the Turn's line last when one is lit (WickBook.Sum).</summary>
public sealed record WickSumView(string Stat, double Total, IReadOnlyList<(string What, string Value)> Parts)
{
    /// <summary>A chained skill by day: the damage of one cut, and the seconds between cuts. Null otherwise.</summary>
    public double? Cut { get; init; }
    public double? Every { get; init; }
}

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

    /// <summary>A skill as a fight takes it up at a rank: its wick lit to the rank (Battle.Relight's rule, on Path's lamps).</summary>
    public static WeaponInst Weapon(CharacterData ch, string skill, int rank)
    {
        var w = new WeaponInst(skill, rank, 0);
        if (Lights == Mode.None || Wicks.Of(skill) == null) return w;
        var path = Path(ch, skill);
        var ids = path.Take(System.Math.Min(rank, path.Length)).ToArray();
        w.Wick = Turns.Build(w, ids.Select(id => Wicks.Lamp(skill, id)).Where(l => l != null).Select(l => l!.Value), ids);
        return w;
    }

    /// <summary>The rank a skill comes into a fight at: the gear's own rank either way; else by day its carried rank
    /// (SkillBook.Rank), by night the ember's (SkillBook.NightRank, before the night ranks it further).</summary>
    public static int RankIn(CharacterData ch, string skill, bool night)
    {
        foreach (var (id, rank) in Character.DaySkills(ch, gearOnly: true)) if (id == skill) return rank;
        return night ? SkillBook.NightRank(ch) : SkillBook.Rank(ch);
    }

    /// <summary>§14.8: the wick's whole sum for one skill's damage, the number its blows start from in the fight
    /// (WeaponInst.Damage on WickBook.Weapon: base, rank, the lead-ins, the Turns), at RankIn. Night has no other size on
    /// a wick (Turns.Build reads none). The Hand, rites and lamps change blows by condition (a heavy, a bleeding thing,
    /// low health), not this number, so they are not parts. Null for a skill with no wick or no damage of its own.</summary>
    public static WickSumView? Sum(CharacterData ch, string skill, bool night)
    {
        if (!Weapons.All.TryGetValue(skill, out var def) || Wicks.Of(skill) == null || (def.Base.Damage ?? 0) <= 0) return null;
        int rank = RankIn(ch, skill, night);
        var w = Weapon(ch, skill, rank);
        var inv = System.Globalization.CultureInfo.InvariantCulture;
        var parts = new List<(string What, string Value)> { ("base", def.Base.Damage!.Value.ToString("0.#", inv)) };
        double growth = 1 + def.Growth * (rank - 1);
        if (growth != 1) parts.Add(($"rank {rank}", "×" + growth.ToString("0.00", inv)));
        if (w.Wick is { } fx)
        {
            double lead = 0;
            foreach (var id in fx.Lit)
                if (Wicks.Lamp(skill, id) is { } ln && ln.N < Wicks.PerStrand) lead += ln.Strand.LeadIns[ln.N - 1].Damage;
            if (lead != 0) parts.Add(("wicks", (lead > 0 ? "+" : "") + (lead * 100).ToString("0.#", inv) + "%"));
            foreach (var t in fx.Turns.Select(Wicks.Turn))
                parts.Add(("Turn:", t.Damage != 1 ? $"{t.Name} ×{t.Damage.ToString("0.00", inv)}" : t.Name));
            foreach (var t in fx.Dark.Select(Wicks.Turn)) parts.Add(("Turn (dark):", t.Name));
        }
        var view = new WickSumView("Damage", w.Damage, parts);
        if (!night && def.Press?.Chain?.Period is > 0 and var period)
            view = view with { Cut = w.Damage * period / (def.Press.Wait ?? def.Base.Cooldown ?? 1), Every = period };
        return view;
    }

    /// <summary>Every wick's path for a fight (BattleSetup.Wicks), or null when the fights read none.</summary>
    public static Dictionary<string, string[]>? Paths(CharacterData ch) =>
        Lights == Mode.None ? null : Wicks.Skills.ToDictionary(id => id, id => Path(ch, id));
}
