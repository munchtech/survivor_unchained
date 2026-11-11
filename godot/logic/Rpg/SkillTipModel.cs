using System;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using System.Text.RegularExpressions;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Rpg;

/// <summary>A skill's hover card (U1): the name, the small "how" line, the plain line, the number rows and the cost row.
/// Own: the skill has its own record in skill_tips.json (else the description fallback). Unresolved lists any
/// placeholder the numbers could not fill (shown as "?"; tests demand none).</summary>
public sealed record SkillTipView(string Name, string How, string Line, IReadOnlyList<(string Label, string Value)> Rows,
    (string Label, string Value)? Cost, string? Key, bool Own, IReadOnlyList<string> Unresolved);

public static class SkillTipModel
{
    static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
    static readonly Regex Hole = new(@"\{([^{}]*)\}", RegexOptions.Compiled);

    /// <summary>A damage: whole at 10 or more, else one place (no trailing zeros).</summary>
    public static string Damage(double v) => Math.Abs(v) >= 10 ? Math.Round(v).ToString("0", Inv) : Math.Round(v, 1).ToString("0.#", Inv);
    /// <summary>A plain number, up to two places, no trailing zeros.</summary>
    public static string Plain(double v) => Math.Round(v, 2).ToString("0.##", Inv);
    /// <summary>Seconds: one place, no trailing zeros ("7.8", "0.5", "8").</summary>
    public static string Seconds(double v) => Math.Round(v, 1).ToString("0.#", Inv);
    static string Percent(double v) => Math.Round(v * 100, 1).ToString("0.#", Inv) + "%";

    /// <summary>The card for a skill. With a battle: the fight's own weapon (so its numbers are the fight's); without, the
    /// skill as a day fight would take it up (WickBook.Weapon at RankIn, its campaign press record and cast form on).</summary>
    public static SkillTipView Build(CharacterData ch, Battle? b, string skill, CastMode cast, string? key = null) =>
        Build(ch, b, skill, cast == CastMode.Channel ? "channel" : cast == CastMode.Press ? "press" : "auto", key);

    /// <summary>As above, the cast as the taught build writes it: hold, press, channel or kindle.</summary>
    public static SkillTipView Build(CharacterData ch, Battle? b, string skill, string cast, string? key = null)
    {
        if (!Weapons.All.TryGetValue(skill, out var def))
            return new SkillTipView(skill, "", "", Array.Empty<(string, string)>(), null, key, false, Array.Empty<string>());
        var rec = SkillTips.Of(skill);
        var w = b?.Weapons.Find(x => x.Id == skill);
        bool live = w != null;
        bool resolveOn = b != null ? b.Resolve.On : ch.Archetype == "warden";
        if (w == null)
        {
            w = WickBook.Weapon(ch, skill, WickBook.RankIn(ch, skill, false), false);
            w.Press = def.Press;
            if (w.Press != null) w.SetForm(cast);
        }
        var unresolved = new List<string>();
        double cooldown = live ? Firing.CooldownOf(b!, w) : Firing.CampaignCooldownOf(w, resolveOn, StatMul(ch));
        double resolve = live ? b!.CostOf(w) : resolveOn ? def.Press?.Resolve ?? 0 : 0;
        double drain = def.Press?.Drain ?? 0;
        double dmg = w.Damage;
        double? cut = null, every = null;
        if (w.Chained && w.Press!.Chain!.Period is > 0 and var period)
        {
            every = period;
            cut = dmg * period / (w.Press.Wait ?? def.Base.Cooldown ?? 1);
        }

        string Fill(string t) => Hole.Replace(t, m =>
        {
            string? s = Lookup(m.Groups[1].Value, w, dmg, cut, every, cooldown, resolve, drain);
            if (s == null) { unresolved.Add(m.Value); return "?"; }
            // a value read as seconds (the hole followed by " s") prints 0.#
            bool secs = string.CompareOrdinal(t, m.Index + m.Length, " s", 0, 2) == 0
                && (m.Index + m.Length + 2 == t.Length || !char.IsLetter(t[m.Index + m.Length + 2]));
            if (secs && double.TryParse(s, NumberStyles.Float, Inv, out double sv)) return Seconds(sv);
            return s;
        });

        string how = cast == "kindle" && rec?.Kindled is { } k ? Fill(k)
            : rec?.How is { } h && h.TryGetValue(cast, out var ho) ? ho : SkillTips.How(cast);
        string line;
        var rows = new List<(string, string)>();
        if (rec != null)
        {
            line = Fill(rec.Line);
            foreach (var r in rec.Numbers) if (r.Length >= 2) rows.Add((r[0], Fill(r[1])));
        }
        else
        {
            line = FirstSentence(def.Description);
            if (dmg > 0) rows.Add(("Damage", Damage(dmg)));
        }

        (string, string)? cost = null;
        string? ck = resolveOn && (def.Press?.Resolve ?? 0) > 0 ? "resolve"
            : resolveOn && drain > 0 ? "drain"
            : every != null ? "chain"
            : cooldown >= 0.1 ? "cooldown" : null;
        if (ck != null && SkillTips.CostTemplate(ck) is { } ct) cost = (ct.Label, Fill(ct.Value));
        return new SkillTipView(def.Name, how, line, rows, cost, key, rec != null, unresolved);
    }

    /// <summary>Her Cooldown stat as a fight starts with it (kit stats: calling, gear, lamps).</summary>
    public static double StatMul(CharacterData ch) => Character.Kit(ch, false).Stats.Get(Stat.Cooldown);

    static string FirstSentence(string d)
    {
        d = d.Replace("{", "").Replace("}", "").Trim();
        int i = d.IndexOf(". ", StringComparison.Ordinal);
        return i > 0 ? d[..(i + 1)] : d;
    }

    /// <summary>One placeholder's text, or null when the data has nothing for it.</summary>
    static string? Lookup(string name, WeaponInst w, double dmg, double? cut, double? every, double cooldown, double resolve, double drain)
    {
        switch (name)
        {
            case "damage": return Damage(dmg);
            case "cut": return Damage(cut ?? dmg);
            case "every": return Seconds(every ?? cooldown);
            case "cooldown": return Seconds(cooldown);
            case "resolve": return Plain(resolve);
            case "drain": return drain > 0 ? Plain(drain) : null;
        }
        if (name.StartsWith("base.", StringComparison.Ordinal))
        {
            bool pct = name.EndsWith(":%", StringComparison.Ordinal);
            string f = pct ? name[5..^2] : name[5..];
            var fi = typeof(WeaponStats).GetField(f, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
            if (fi?.GetValue(w.Def.Base) is not { } v) return null;
            double d = Convert.ToDouble(v, Inv);
            return pct ? Percent(d) : Plain(d);
        }
        if (name.StartsWith("kindle.", StringComparison.Ordinal))
        {
            string f = name[7..];
            Func<KindleDef, double?>? pick = f switch
            {
                "count" => x => x.Count,
                "radius" => x => x.Radius,
                "within" => x => x.Within,
                "below" => x => x.Below,
                _ => null,
            };
            if (pick == null) return null;
            double? r = Find(w.Press?.Kindled?.Condition(), pick) ?? Find(w.Def.Kindle, pick);
            return r == null ? null : Plain(r.Value);
        }
        return null;
    }

    static double? Find(KindleDef? k, Func<KindleDef, double?> f)
    {
        if (k == null) return null;
        if (f(k) is { } v) return v;
        if (k.Any != null) foreach (var a in k.Any) if (Find(a, f) is { } x) return x;
        return null;
    }
}
