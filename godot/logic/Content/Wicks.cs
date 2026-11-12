using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* The Wicks (docs/design/CLASS_IDENTITY_AND_TALENTS.md 3.3): each skill's own tree of 12 lamps, three strands of
 * four, the fourth a Turn that changes what the skill is. The data is data/content/wicks.json; Rpg/WickBook.cs
 * plans a wick, Sim/Turns.cs turns its lit lamps into the skill's numbers in the fight. */
/// <summary>Calling: a calling skill's own bespoke strand (its lead-ins written out in "lamps", under the skill's "own").</summary>
public enum StrandKind { Shape, School, Bind, Calling }

/// <summary>A lead-in lamp's numbers. Increases, so lamps add (two +10% damage lamps are +20%).</summary>
public sealed class WickLeadIn
{
    public string Text = "";
    public double Damage, Area, Cooldown, Speed;
    /// <summary>A projectile skill takes this speed instead of Area (the shape strands' second lamp).</summary>
    public double ProjectileSpeed;
    /// <summary>School lead-ins, on the strand's Turn's status.</summary>
    public double StatusChance, VsStatus, StatusDuration;
    public double VsChampion;
}

/// <summary>A Turn: how it transforms the skill. Multipliers default to 1, counts to 0.</summary>
public sealed class TurnDef
{
    public string Id = "", Name = "", Text = "";
    public double Projectiles = 1, Damage = 1, Area = 1, Cooldown = 1;
    public int Chains, Bounces;
    public GroundSpec? Ground;
    public School? School;
    /// <summary>The school's status ("burning", "chilled", "seared": the cards' word for what has it).</summary>
    public StatusPayload? Status;
    public string Statused = "";
    /// <summary>Pulse: it goes off this many times in all, the follow-ups PulseGap seconds apart (each the cast's own
    /// firing again, at the Turn's damage and area).</summary>
    public int Pulses = 1;
    public double PulseGap = 0.3;
    /// <summary>On-kill: a kill by its own hit fires it once more from the corpse, at OnKillDamage, at most once every
    /// OnKillGap seconds; that firing's kills never fire it again.</summary>
    public bool OnKill;
    public double OnKillGap = 0.5, OnKillDamage = 0.6;
    /// <summary>Its own heavy count becomes every this many firings (the skill's HeavyEvery; 0 leaves it).</summary>
    public int HeavyEvery;
    /// <summary>Again: its blow lands again on the same spot Again seconds later, at AgainDamage (0: never).</summary>
    public double Again, AgainDamage = 0.6;
    /// <summary>Its strike leaves her a barrier of BarrierEach of max health for each creature struck, at most
    /// BarrierMost a strike (0: none; Shield of Morning).</summary>
    public double BarrierEach, BarrierMost;
    /// <summary>Each firing lays this many Stones, and StonesChampion more for each champion it draws (Stone Bell).</summary>
    public int Stones, StonesChampion;
}

/// <summary>One alternative a strand suits: any of its behaviors, any of its tags, an explosion; absent, any.</summary>
public sealed class WickSuit
{
    public WeaponBehavior[]? Behaviors;
    public Tag[]? Tags;
    public bool? Splash;
}

public sealed class StrandDef
{
    public string Id = "";
    public StrandKind Kind;
    public string Turn = "";
    /// <summary>Its three lead-ins: written out (a bespoke strand), else its kind's shared ones.</summary>
    public WickLeadIn[]? Lamps;
    public WickSuit[]? Suits;

    /// <summary>A rule strand (a P7 tree read from skill_lamps.json, every lamp engine "rule" or "built"): each place's
    /// effects (1-4 at [0]-[3]): rules the fight reads by id (Sim/WardenWicks.cs), an evolve the weapon becomes. Its
    /// lead-ins carry no numbers; null on wicks.json's strands.</summary>
    public WickRule[][]? Rules;

    public WickLeadIn[] LeadIns => Lamps is { Length: 3 } l ? l : Wicks.LeadInsOf(Kind);
    public TurnDef TurnDef => Wicks.Turn(Turn);
    public string LampId(int n) => $"{Id}.{n}";
}

/// <summary>A rule strand lamp's effect: a rule lit in the fight (its LampEffect), or the evolution it becomes.</summary>
public sealed record WickRule(LampEffect? Rule, string? Evolve);

public sealed class SkillWick
{
    public string[] Strands = Array.Empty<string>();
    public string Suggested = "";
    /// <summary>Strands this skill alone has (the callings' bespoke ones), by id.</summary>
    public Dictionary<string, StrandDef>? Own;
}

public static class Wicks
{
    public const int LampCount = 12, PerStrand = 4;

    sealed class File
    {
        public Dictionary<string, WickLeadIn[]> LeadIns = new();
        public Dictionary<string, TurnDef> Turns = new();
        public Dictionary<string, StrandDef> Strands = new();
        public Dictionary<string, SkillWick> Skills = new();
    }

    static File? file;
    static File F => file ??= Load();

    static File Load()
    {
        var f = Json.Parse<File>(Json.ReadContent("wicks.json"));
        foreach (var (id, t) in f.Turns) t.Id = id;
        foreach (var (id, s) in f.Strands) s.Id = id;
        foreach (var w in f.Skills.Values)
            if (w.Own != null) foreach (var (id, s) in w.Own) s.Id = id;
        RuleTrees(f, LampsData);
        return f;
    }

    /// <summary>The skills a rule tree, not wicks.json, gives a wick: in skill_lamps.json, absent from wicks.json, every
    /// lamp engine "rule" or "built" (tools/classes/skill_lamps_check.py names them). Today Heroic Leap, Shield Charge,
    /// Iron Vow and the Cleaver (SU-051).</summary>
    public static bool IsRuleTree(string skill) => Of(skill)?.Own?.Values.Any(s => s.Rules != null) == true;

    /// <summary>(SU-051) Each eligible skill's three strands as its own ("heroic_leap.quake"), its lamps' ids skill_lamps.json's
    /// ("heroic_leap.quake.1"): lead-ins whose text is the lamp's name and sentence, a Turn named for the fourth lamp, and
    /// each place's effects, which Turns.Build gathers and the fight lights as rules (Battle.SyncWickRules).</summary>
    static void RuleTrees(File f, LampsFile data)
    {
        var bySkill = data.Lamps.Where(l => l.Skill != "").GroupBy(l => l.Skill).ToDictionary(g => g.Key, g => g.ToList());
        foreach (var sk in data.Skills)
        {
            if (f.Skills.ContainsKey(sk.Id) || !bySkill.TryGetValue(sk.Id, out var lamps) || sk.Strands.Count != 3) continue;
            if (lamps.Any(l => l.Engine is not ("rule" or "built"))) continue;
            var own = new Dictionary<string, StrandDef>();
            foreach (var st in sk.Strands)
            {
                var row = Enumerable.Range(1, PerStrand).Select(n => lamps.FirstOrDefault(l => l.Strand == st.Id && l.N == n)).ToArray();
                if (row.Any(r => r == null)) { own.Clear(); break; }
                string sid = $"{sk.Id}.{st.Id}";
                var turn = row[PerStrand - 1]!;
                f.Turns[sid] = new TurnDef { Id = sid, Name = turn.Name, Text = turn.Rule };
                own[sid] = new StrandDef
                {
                    Id = sid, Turn = sid,
                    Kind = st.Kind switch { "calling" => StrandKind.Calling, "shape" => StrandKind.Shape, "element" => StrandKind.School, _ => StrandKind.Bind },
                    Lamps = row.Take(PerStrand - 1).Select(r => new WickLeadIn { Text = $"{r!.Name}: {r.Rule}" }).ToArray(),
                    Rules = row.Select(r => r!.Effects.Select(e => RuleOf(r.Id, e)).Where(x => x != null).Select(x => x!).ToArray()).ToArray(),
                };
            }
            if (own.Count != 3) continue;
            f.Skills[sk.Id] = new SkillWick { Strands = own.Keys.ToArray(), Suggested = $"{sk.Id}.{sk.Suggested}", Own = own };
        }
    }

    /// <summary>A lamp effect as the fight takes it: a rule with its numeric args (a "skill" word names its skill; a
    /// "skill.status" rule's status kind), or an evolve's evolution.</summary>
    static WickRule? RuleOf(string lamp, System.Text.Json.JsonElement e)
    {
        string d = e.TryGetProperty("do", out var dv) ? dv.GetString() ?? "" : "";
        if (d == "evolve") return e.TryGetProperty("evolution", out var ev) ? new WickRule(null, ev.GetString()) : null;
        if (d != "rule" || !e.TryGetProperty("rule", out var rv)) return null;
        var fx = new LampEffect { Do = LampDo.Rule, Rule = rv.GetString(), Args = new Dictionary<string, double>(), Lamp = lamp };
        if (e.TryGetProperty("args", out var args))
            foreach (var a in args.EnumerateObject())
            {
                if (a.Value.ValueKind == System.Text.Json.JsonValueKind.Number) fx.Args[a.Name] = a.Value.GetDouble();
                else if (a.Name == "skill") fx.Skill = a.Value.GetString();
                else if (a.Name == "status" && fx.Rule == "skill.status" && a.Value.TryGetProperty("kind", out var k)
                    && Enum.TryParse<StatusKind>(k.GetString(), true, out var kind)) fx.Status = kind;
            }
        return new WickRule(fx, null);
    }

    public static void Reload() { file = null; cards = null; lampsData = null; }

    /// <summary>A lamp's numbers for the level-up card when lighting it leaves the skill's blow as it was (M7a): what
    /// changes ("a heavy blow every"), before and after (swings). skill_lamps.json lamps[].card.</summary>
    public sealed class LampCard
    {
        public string Measure = "";
        public double Before, After;
    }

    sealed class LampRow
    {
        public string Id = "", Name = "", Skill = "", Strand = "", Engine = "";
        /// <summary>The lamp's sentence (its spec).</summary>
        public string Rule = "";
        public int N;
        public LampCard? Card;
        public List<System.Text.Json.JsonElement> Effects = new();
    }

    sealed class StrandRow { public string Id = "", Name = "", Kind = ""; }
    sealed class SkillRow { public string Id = "", Suggested = ""; public List<StrandRow> Strands = new(); }
    sealed class LampsFile { public List<LampRow> Lamps = new(); public List<SkillRow> Skills = new(); }

    static LampsFile? lampsData;
    static LampsFile LampsData => lampsData ??= Json.Parse<LampsFile>(Json.ReadContent("skill_lamps.json"));

    static Dictionary<string, LampRow>? cards;
    /// <summary>skill_lamps.json's lamps by full id ("sunder.stroke.1"): their names and card numbers (and, for the rule
    /// trees, their effects: RuleTrees).</summary>
    static Dictionary<string, LampRow> Rows => cards ??= LampsData.Lamps
        .Where(r => r.Id != "").GroupBy(r => r.Id).ToDictionary(g => g.Key, g => g.First());

    /// <summary>A lamp's card numbers (skill_lamps.json lamps[].card) by its full id ("sunder.stroke.1"), or null.</summary>
    public static LampCard? Card(string lampId) => Rows.TryGetValue(lampId, out var r) ? r.Card : null;

    /// <summary>A lamp's name (skill_lamps.json lamps[].name: "Third Blow") by its full id, or null.</summary>
    public static string? Name(string lampId) => Rows.TryGetValue(lampId, out var r) && r.Name != "" ? r.Name : null;

    /// <summary>A measuring aid (the harness's --strands): this skill's strands for this run, its wick made if it has
    /// none yet (Light my way then follows the first).</summary>
    public static void SetStrands(string skill, string[] strands)
    {
        if (!F.Skills.TryGetValue(skill, out var w)) F.Skills[skill] = w = new SkillWick { Suggested = strands[0] };
        w.Strands = strands;
    }

    /// <summary>The skills that have a wick.</summary>
    public static IEnumerable<string> Skills => F.Skills.Keys;

    public static SkillWick? Of(string skill) => F.Skills.TryGetValue(skill, out var w) ? w : null;

    public static TurnDef Turn(string id) => F.Turns.TryGetValue(id, out var t) ? t : throw new KeyNotFoundException($"unknown turn {id}");

    public static WickLeadIn[] LeadInsOf(StrandKind k) =>
        F.LeadIns.TryGetValue(k.ToString().ToLowerInvariant(), out var l) ? l : throw new KeyNotFoundException($"no lead-ins for {k}");

    /// <summary>A skill's strand: its own bespoke one, else the library's.</summary>
    public static StrandDef? Strand(string skill, string id) =>
        Of(skill)?.Own?.TryGetValue(id, out var own) == true ? own : F.Strands.TryGetValue(id, out var s) ? s : null;

    /// <summary>A skill's strands in its order.</summary>
    public static IEnumerable<StrandDef> StrandsOf(string skill) =>
        Of(skill)?.Strands.Select(id => Strand(skill, id) ?? throw new KeyNotFoundException($"{skill}: unknown strand {id}")) ?? Enumerable.Empty<StrandDef>();

    /// <summary>A lamp id ("wide.2") as its strand and place (1-4; 4 is the Turn), or null if not this skill's.</summary>
    public static (StrandDef Strand, int N)? Lamp(string skill, string lamp)
    {
        int dot = lamp.LastIndexOf('.');
        if (dot <= 0 || !int.TryParse(lamp.AsSpan(dot + 1), out int n) || n < 1 || n > PerStrand) return null;
        var sid = lamp[..dot];
        if (Of(skill) is not { } w || Array.IndexOf(w.Strands, sid) < 0 || Strand(skill, sid) is not { } s) return null;
        return (s, n);
    }

    public static bool IsTurn(string skill, string lamp) => Lamp(skill, lamp) is { N: PerStrand };

    /// <summary>Does a strand suit a skill of this behavior, tags and school (an explosion: splash)?</summary>
    public static bool Suits(StrandDef s, WeaponBehavior behavior, Tag[] tags, School school, bool splash)
    {
        if (s.Kind == StrandKind.School && s.TurnDef.School == school) return false;
        if (s.Suits is not { Length: > 0 } alts) return true;
        foreach (var a in alts)
        {
            if (a.Behaviors is { Length: > 0 } bs && Array.IndexOf(bs, behavior) < 0) continue;
            if (a.Tags is { Length: > 0 } ts && !ts.Any(tags.Has)) continue;
            if (a.Splash == true && !splash) continue;
            return true;
        }
        return false;
    }

    /// <summary>A lamp's line on the card: a lead-in's text (a school's status named), or the Turn's.</summary>
    public static string Text(string skill, string lamp)
    {
        if (Lamp(skill, lamp) is not { } ln) return "";
        var (s, n) = ln;
        var t = s.TurnDef;
        if (n == PerStrand) return $"{t.Name}: {t.Text}";
        var kind = t.Status?.Kind.ToString().ToLowerInvariant() ?? "";
        return s.LeadIns[n - 1].Text.Replace("{statused}", t.Statused).Replace("{status}", kind)
            .Replace("{Status}", kind.Length > 0 ? char.ToUpperInvariant(kind[0]) + kind[1..] : "");
    }
}
