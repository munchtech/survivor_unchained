using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Tests;

/// <summary>What the ported tests share: survivors, worlds, and conditions and
/// changes written the way the web game's tests write them (JavaScript object
/// literals: bare keys, single quotes).</summary>
static class H
{
    static readonly Regex BareKey = new(@"([{,]\s*)([A-Za-z_$][\w$]*)\s*:", RegexOptions.Compiled);

    /// <summary>A JavaScript object literal as JSON.</summary>
    public static string Js(string lit)
    {
        // Single-quoted strings to double-quoted (content has no quotes inside these tests' strings).
        var s = Regex.Replace(lit, @"'((?:[^'\\]|\\.)*)'", m => "\"" + m.Groups[1].Value.Replace("\"", "\\\"") + "\"");
        // Bare keys quoted (twice: overlapping matches).
        s = BareKey.Replace(s, "$1\"$2\":");
        s = BareKey.Replace(s, "$1\"$2\":");
        return s;
    }

    public static Cond C(string lit) => Json.Parse<Cond>(Js(lit));
    public static Change E(string lit) => Json.Parse<Change>(Js(lit));
    public static List<Change> Es(string lit) => Json.Parse<List<Change>>(Js(lit));
    public static DailyRule Rule(string lit) => Json.Parse<DailyRule>(Js(lit));

    public static CharacterData Survivor(string bg = "hunter", string name = "Ashe", long seed = 42)
    {
        var a = Callings.Archetype("warden");
        return Character.Create(new CreationChoice
        {
            Name = name, Archetype = "warden", Background = bg, Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0],
            Ability = a.Abilities[0],
        }, 1, seed);
    }

    public sealed record Setup(CharacterData Ch, WorldState World, Ctx C, List<Notice> Notices);

    public static Setup Make(string bg = "hunter", string name = "Ashe", uint seed = 42)
    {
        var ch = Survivor(bg, name, seed);
        var world = WorldState.Fresh(seed);
        var notices = new List<Notice>();
        return new Setup(ch, world, Lore.Context(world, ch, notices.Add), notices);
    }

    /// <summary>Talk: pick choices by a fragment of their text, in order.</summary>
    public static Presented? Talk(Conversation convo, Ctx c, params string[] picks)
    {
        var r = new DialogueRunner(convo, c);
        var p = r.Start();
        foreach (var pick in picks)
        {
            if (p == null) throw new InvalidOperationException($"conversation ended before \"{pick}\"");
            if (p.Choices.Count == 0) { p = r.Advance(); if (p == null) throw new InvalidOperationException("ended"); }
            var choice = p.Choices.FirstOrDefault(x => x.Text.Contains(pick, StringComparison.OrdinalIgnoreCase))
                ?? throw new InvalidOperationException($"no choice \"{pick}\" in [{string.Join(" | ", p.Choices.Select(x => x.Text))}]");
            if (!choice.Enabled) throw new InvalidOperationException($"choice \"{pick}\" is locked: {choice.Locked}");
            p = r.Choose(choice.Index).Next;
        }
        return p;
    }

    /// <summary>Start a conversation and click through whatever is said
    /// before the first question (a remark on your calling, a deed quoted
    /// back): the greeting, with its choices.</summary>
    public static Presented Greet(Conversation convo, Ctx c)
    {
        var r = new DialogueRunner(convo, c);
        var p = r.Start();
        while (p != null && p.Choices.Count == 0) p = r.Advance();
        return p ?? throw new InvalidOperationException("the conversation ended before a question");
    }

    /// <summary>A seeded stream for gossip.</summary>
    public static Func<double> Lcg(double start)
    {
        double r = start;
        return () => r = (r * 9301 + 49297) % 233280 / 233280;
    }
}
