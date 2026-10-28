using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* The Wicks (docs/design/CLASS_IDENTITY_AND_TALENTS.md 3.3): each skill's own tree of 12 lamps, three strands of
 * four, the fourth a Turn that changes what the skill is. The data is data/content/wicks.json; Rpg/WickBook.cs
 * plans a wick, Sim/Turns.cs turns its lit lamps into the skill's numbers in the fight. */
public enum StrandKind { Shape, School, Bind }

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
    /// <summary>Defined and plannable, not yet in the fight (Pulse, On-kill: P5b).</summary>
    public bool Inert;
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

    public WickLeadIn[] LeadIns => Lamps is { Length: 3 } l ? l : Wicks.LeadInsOf(Kind);
    public TurnDef TurnDef => Wicks.Turn(Turn);
    public string LampId(int n) => $"{Id}.{n}";
}

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
        return f;
    }

    public static void Reload() => file = null;

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
