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

    /// <summary>A skill as a fight takes it up at a rank: its wick lit to the rank (Battle.Relight's rule, on Path's lamps;
    /// by day on DayPath, so a skill holding points lights only its burning ones).</summary>
    public static WeaponInst Weapon(CharacterData ch, string skill, int rank, bool night = false)
    {
        var w = new WeaponInst(skill, rank, 0);
        if (Lights == Mode.None || Wicks.Of(skill) == null) return w;
        var path = night ? Path(ch, skill) : DayPath(ch, skill);
        var ids = path.Take(System.Math.Min(rank, path.Length)).ToArray();
        w.Wick = Turns.Build(w, ids.Select(id => Wicks.Lamp(skill, id)).Where(l => l != null).Select(l => l!.Value), ids);
        return w;
    }

    /// <summary>The rank a skill comes into a fight at: the gear's own rank either way; else by day its carried rank
    /// (SkillBook.Rank), by night the ember's (SkillBook.NightRank, before the night ranks it further).</summary>
    public static int RankIn(CharacterData ch, string skill, bool night)
    {
        foreach (var (id, rank) in Character.DaySkills(ch, gearOnly: true)) if (id == skill) return rank;
        return night ? SkillBook.NightRank(ch) : DayRank(ch, skill);
    }

    /// <summary>§14.8: the wick's whole sum for one skill's damage, the number its blows start from in the fight
    /// (WeaponInst.Damage on WickBook.Weapon: base, rank, the lead-ins, the Turns), at RankIn. Night has no other size on
    /// a wick (Turns.Build reads none). The Hand, rites and lamps change blows by condition (a heavy, a bleeding thing,
    /// low health), not this number, so they are not parts. Null for a skill with no wick or no damage of its own.</summary>
    public static WickSumView? Sum(CharacterData ch, string skill, bool night)
    {
        if (!Weapons.All.TryGetValue(skill, out var def) || Wicks.Of(skill) == null || (def.Base.Damage ?? 0) <= 0) return null;
        int rank = RankIn(ch, skill, night);
        var w = Weapon(ch, skill, rank, night);
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

    /// <summary>Every wick's path for a fight (BattleSetup.Wicks), or null when the fights read none. By day a skill
    /// holding points gets only its burning lamps (DayPath: Battle.Relight lights min(rank, path), so exactly Burning);
    /// a night (an arena, an ember's) takes the whole path, for the ember ranks it (held points are a day rule).</summary>
    public static Dictionary<string, string[]>? Paths(CharacterData ch, bool night = false) =>
        Lights == Mode.None ? null : Wicks.Skills.ToDictionary(id => id, id => night ? Path(ch, id) : DayPath(ch, id));

    /* ------------------------------------------------ held points (M7a) --
     * docs/design/ARPG.md 3.5: a skill's points come at SkillBook.PointsAt (one at the first level, then one every
     * second level). A point earned while she carries the skill is HELD until she lights it (the level-up card's
     * offer, Light my way, a lamp-post); with LampState.LightMyWay on nothing is held. Held 0 is today's rule exactly:
     * every point burns, rank = SkillBook.Rank. Held > 0: the burning points are Rank - Held; the fight takes rank
     * max(1, Burning) (rank 0 maps onto the weapon's rank 1, skill_lamps.json rules.rank.zero) and lights Burning lamps. */

    static Dictionary<string, int> HeldMap(CharacterData ch) => LampBook.Now(ch).Held ??= new();

    /// <summary>The points this skill holds unlit (0: every point burns).</summary>
    public static int Held(CharacterData ch, string skill) =>
        LampBook.Now(ch).Held is { } h && h.TryGetValue(skill, out var n) ? System.Math.Max(0, n) : 0;

    /// <summary>The points that burn: SkillBook.Rank less the held ones (never below 0).</summary>
    public static int Burning(CharacterData ch, string skill) => System.Math.Max(0, SkillBook.Rank(ch) - Held(ch, skill));

    /// <summary>The rank a day fight takes the skill at: Rank when nothing is held, else max(1, Burning).</summary>
    public static int DayRank(CharacterData ch, string skill) =>
        Held(ch, skill) > 0 ? System.Math.Max(1, Burning(ch, skill)) : SkillBook.Rank(ch);

    /// <summary>The lamps a day fight lights for the skill, in order: the first Burning of Path when it holds points,
    /// else the whole Path (Relight takes the rank's share).</summary>
    public static string[] DayPath(CharacterData ch, string skill)
    {
        var path = Path(ch, skill);
        return Held(ch, skill) > 0 ? path.Take(Burning(ch, skill)).ToArray() : path;
    }

    /// <summary>The lamp the next held point would light (Path[Burning]), or null: nothing held, or the path ends.</summary>
    public static string? NextLamp(CharacterData ch, string skill)
    {
        if (Held(ch, skill) <= 0) return null;
        var path = Path(ch, skill);
        int b = Burning(ch, skill);
        return b < path.Length ? path[b] : null;
    }

    /// <summary>Light one held point: Held less one; the lamp now burning (NextLamp before the call), or null when nothing
    /// is held. A point past the path's end still burns (its rank grows) and returns null.</summary>
    public static string? Light(CharacterData ch, string skill)
    {
        if (Held(ch, skill) <= 0) return null;
        var lamp = NextLamp(ch, skill);
        var h = HeldMap(ch);
        if (--h[skill] <= 0) h.Remove(skill);
        return lamp;
    }

    /// <summary>Hold n more points on a skill with a wick (Wicks.Of(skill) != null); a skill with none ignores it.</summary>
    public static void Hold(CharacterData ch, string skill, int n)
    {
        if (n <= 0 || Wicks.Of(skill) == null) return;
        var h = HeldMap(ch);
        h[skill] = h.GetValueOrDefault(skill) + n;
    }

    /// <summary>Light my way, by day: every held point burns (each skill's next lamps along its path).</summary>
    public static void LightAll(CharacterData ch) => LampBook.Now(ch).Held?.Clear();

    /// <summary>True when the points she earns wait for her to light them (LampState.LightMyWay off).</summary>
    public static bool Holds(CharacterData ch) => !LampBook.State(ch).LightMyWay;

    /// <summary>A level gained (from, to): each carried skill with a wick holds the points earned (PointsAt(to) -
    /// PointsAt(from)) while she lights them herself. Character.GainXp calls it, the one place every level passes.</summary>
    public static void Grew(CharacterData ch, int from, int to)
    {
        int n = SkillBook.PointsAt(to) - SkillBook.PointsAt(from);
        if (n <= 0 || !Holds(ch)) return;
        foreach (var (id, _) in SkillBook.Carried(ch).ToList()) Hold(ch, id, n);
    }

    /// <summary>A skill come into her hands (creation, the calling's teaching): it holds every point it has
    /// (PointsAt(level)), its first point waiting for her too, while she lights them herself.</summary>
    public static void Arrived(CharacterData ch, string skill)
    {
        if (!Holds(ch) || Wicks.Of(skill) == null) return;
        HeldMap(ch)[skill] = SkillBook.Rank(ch);
    }

    /// <summary>The level-up card's before and after for lighting lampId (the skill's next held lamp, NextLamp): the
    /// skill's blow (Sum's day Total: base, rank growth, lit lead-ins and Turns) at Burning lamps and rank max(1, Burning)
    /// against Burning + 1, Measure "a blow", when they differ; else the lamp's own card numbers (skill_lamps.json
    /// lamps[].card, Wicks.Card); else ("", 0, 0): nothing to show (the card leaves the line out).</summary>
    public static (string Measure, double Before, double After) LampMeasure(CharacterData ch, string skill, string lampId)
    {
        int b = Burning(ch, skill);
        if (Blow(ch, skill, b) is { } before && Blow(ch, skill, b + 1) is { } after && System.Math.Abs(after - before) > 1e-6)
            return ("a blow", System.Math.Round(before, 1), System.Math.Round(after, 1));
        if (Wicks.Card(lampId) is { } c) return (c.Measure, c.Before, c.After);
        return ("", 0, 0);
    }

    /// <summary>The skill's blow by day with lit lamps of its path burning (rank max(1, lit), as DayRank maps it).</summary>
    static double? Blow(CharacterData ch, string skill, int lit)
    {
        if (!Weapons.All.TryGetValue(skill, out var def) || Wicks.Of(skill) == null || (def.Base.Damage ?? 0) <= 0) return null;
        var path = Path(ch, skill);
        var ids = path.Take(System.Math.Clamp(lit, 0, path.Length)).ToArray();
        var w = new WeaponInst(skill, System.Math.Clamp(lit, 1, Weapons.MaxRank), 0);
        if (Lights != Mode.None)
            w.Wick = Turns.Build(w, ids.Select(id => Wicks.Lamp(skill, id)).Where(l => l != null).Select(l => l!.Value), ids);
        return w.Damage;
    }
}
