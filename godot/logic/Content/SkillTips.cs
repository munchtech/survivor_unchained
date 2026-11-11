using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

/* The skill tooltips' words (U1; data/content/skill_tips.json): each skill's plain line, its number rows (label and a
 * value with placeholders) and the small "how" line. Wording is data; Rpg/SkillTipModel.cs fills the placeholders. */
public sealed class SkillTipRec
{
    public string Line = "";
    /// <summary>Rows of [label, value template].</summary>
    public string[][] Numbers = System.Array.Empty<string[]>();
    /// <summary>The small line when she carries it kindled.</summary>
    public string? Kindled;
    /// <summary>Overrides of the shared "how" by cast form.</summary>
    public Dictionary<string, string>? How;
}

public static class SkillTips
{
    sealed class File
    {
        public Dictionary<string, string> How = new();
        public Dictionary<string, string[]> Cost = new();
        public Dictionary<string, SkillTipRec> Skills = new();
    }

    static File? file;
    static File F => file ??= Json.Parse<File>(Json.ReadContent("skill_tips.json"));

    public static void Reload() => file = null;

    /// <summary>The skill's own record, or null (the model then falls back to its description).</summary>
    public static SkillTipRec? Of(string skill) => F.Skills.TryGetValue(skill, out var r) ? r : null;

    /// <summary>The small line for a cast form ("hold", "press", "channel", "kindle"), or "".</summary>
    public static string How(string cast) => F.How.TryGetValue(cast, out var s) ? s : "";

    /// <summary>The cost row's template ([label, value]) by what pays: resolve, drain, cooldown, chain.</summary>
    public static (string Label, string Value)? CostTemplate(string kind) =>
        F.Cost.TryGetValue(kind, out var c) && c.Length >= 2 ? (c[0], c[1]) : null;

    public static IEnumerable<string> Skills => F.Skills.Keys;
}
