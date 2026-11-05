using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play;

/// <summary>
/// The card at first light (H8, the owner's N24 on demo-rc2: "losing everything after the warden fight
/// feels bad and the explanation is very quick"): what the ember takes back as it goes out, and what she
/// keeps, on one storybook page held over the dawn until a click. The words live here; the game only
/// draws them (Ui/DawnCardView).
/// </summary>
public sealed record DawnCard(string Title, string TakesHead, IReadOnlyList<string> Takes, string KeepsHead, IReadOnlyList<string> Keeps, string Last, string Go)
{
    /// <summary>The most lines a column holds: past it, the last of the night's skills are counted, not named.</summary>
    public const int MaxLines = 5;

    /// <summary>The night's skills by their names (what the ember drafted beyond her day kit: its arts, then its
    /// blessings), read before the dawn takes them.</summary>
    public static List<string> NightSkills(Battle b, IEnumerable<string> kit)
    {
        var day = kit.ToHashSet();
        var names = new List<string>();
        foreach (var w in b.Weapons)
            if (!day.Contains(w.Id) && w.Def.Name is { Length: > 0 } n && !names.Contains(n)) names.Add(n);
        foreach (var id in b.Boons.Keys)
            if (Content.Boons.Find(id)?.Name is { Length: > 0 } n && !names.Contains(n)) names.Add(n);
        return names;
    }

    /// <summary>The card's words: the skills the night gave (by name), the Lamps' light; her gear, her gold,
    /// what she learned (and the level the night taught, if it taught one).</summary>
    public static DawnCard Build(IReadOnlyList<string> skills, int? level)
    {
        var takes = new List<string>();
        int room = MaxLines - 1;
        if (skills.Count <= room) takes.AddRange(skills);
        else { takes.AddRange(skills.Take(room - 1)); takes.Add($"And {skills.Count - (room - 1)} more"); }
        takes.Add("The Lamps' light");
        var keeps = new List<string> { "Your gear", "Your gold", "Your traits" };
        if (level is int l) keeps.Add($"Level {l}");
        return new DawnCard("The ember goes out", "The ember takes", takes, "You keep", keeps,
            "When the dark comes again, it will burn again.", "Click to go on");
    }

    /// <summary>Every word the card shows, in reading order (for tests and the run's log).</summary>
    public IEnumerable<string> Words() => new[] { Title, TakesHead }.Concat(Takes).Append(KeepsHead).Concat(Keeps).Append(Last).Append(Go);
}
