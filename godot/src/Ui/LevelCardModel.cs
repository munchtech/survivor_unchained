using System;
using System.Collections.Generic;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/* M4 §4, the level-up card's pure side (no Godot: the tests compile it): what a card says (LevelCardSpec), which kind a
 * campaign level-up makes (LevelCards.ForCampaignLevel; WithCalling when the calling taught a skill at it), its words built once (LevelCards.Header/Line), and its clock
 * (LevelCardQueue: in 0.18 s, hold 2.2 s or 3 s with a prompt row, out 0.3 s; waiting while held). LevelCard.cs draws it. */

public enum LevelCardKind : byte { NewKey, LampLit, Plain, NewSkill }

/// <summary>One level-up card (GameHud.LevelCard; M6 and M7 call it).</summary>
public sealed class LevelCardSpec
{
    public LevelCardKind Kind = LevelCardKind.Plain;
    public int Level = 1;
    /// <summary>NewKey / LampLit / NewSkill: the skill's id (its glyph, name and, but for a lamp, its one line).</summary>
    public string Skill = "";
    /// <summary>NewKey: the slot that opened (0-5, KeyMap.Skills[Slot] is its key; the card folds toward its seat);
    /// -1 none (the card folds toward the coin).</summary>
    public int Slot = -1;
    /// <summary>NewKey / NewSkill: what it does in one line (null: the skill's description's first clause, LevelCards.Line).</summary>
    public string? Line;
    /// <summary>LampLit: the measure and its before/after ("a blow 42 -> 47").</summary>
    public string Measure = "a blow";
    public double Before, After;
    /// <summary>The prompt row (optional): its key and words ("C", "A new trait can be chosen"); the card holds 3 s.</summary>
    public Act? PromptKey;
    public string? PromptText;
    /// <summary>M7a: a lamp offer (a held point waits for her: Act.Lamps lights it); false once lit. Kind LampLit.</summary>
    public bool Offer;
    /// <summary>The lamp this card offers or lit (its full id, "sunder.stroke.1"), "" none.</summary>
    public string Lamp = "";

    public bool HasPrompt => PromptKey != null && !string.IsNullOrEmpty(PromptText);
}

public static class LevelCards
{
    public const double In = 0.18, Hold = 2.2, HoldPrompt = 3.0, Out = 0.3;

    /// <summary>"LEVEL 4 · A NEW KEY", "LEVEL 6 · A LAMP LIT", "LEVEL 6 · A NEW SKILL", "LEVEL 5"; a new skill's card that
    /// follows its level's key card carries no level (Level 0): "A NEW SKILL".</summary>
    public static string Header(LevelCardSpec s) => s.Kind switch
    {
        LevelCardKind.NewKey => $"LEVEL {s.Level} · A NEW KEY",
        LevelCardKind.LampLit => s.Offer ? $"LEVEL {s.Level} · A LAMP TO LIGHT" : $"LEVEL {s.Level} · A LAMP LIT",
        LevelCardKind.NewSkill => s.Level > 0 ? $"LEVEL {s.Level} · A NEW SKILL" : "A NEW SKILL",
        _ => $"LEVEL {s.Level}",
    };

    /// <summary>A number as the card shows it (whole when whole, else one place).</summary>
    public static string Num(double v) => Math.Abs(v - Math.Round(v)) < 0.05
        ? Math.Round(v).ToString(System.Globalization.CultureInfo.InvariantCulture)
        : v.ToString("0.0", System.Globalization.CultureInfo.InvariantCulture);

    /// <summary>What a skill does in one short line from its description: the first sentence, cut at a colon, then, while
    /// longer than `max` characters, back to its last comma
    /// (never shorter than half of `max`: a longer line widens the card).</summary>
    public static string Line(string description, int max = 48)
    {
        var s = (description ?? "").Trim();
        int dot = s.IndexOf(". ", StringComparison.Ordinal);
        if (dot > 0) s = s[..dot];
        s = s.TrimEnd('.');
        int colon = s.IndexOf(':');
        if (colon > 0) s = s[..colon];
        while (s.Length > max)
        {
            int comma = s.LastIndexOf(',', Math.Min(s.Length - 1, max));
            // (not to a stub: "A heavy, wide chop..." stays whole, the card widens for it)
            if (comma < max / 2) break;
            s = s[..comma];
        }
        return s.Trim();
    }

    /// <summary>The campaign's level-up prompt row (the trait or attribute line Journey's banner used to carry).</summary>
    public static string PromptFor(int traitPicks) => traitPicks > 0 ? "A new trait can be chosen" : "Attribute points to spend";

    /// <summary>The card a campaign level makes: a new key when the taught build teaches a skill at that level and the
    /// fight carries it on a slot (slotOf: its slot, -1 when not carried), else plain; with the trait/attribute prompt.</summary>
    public static LevelCardSpec ForCampaignLevel(int level, Content.TaughtBuild? build, Func<string, int> slotOf, int traitPicks, Rpg.CharacterData? ch = null)
    {
        var spec = new LevelCardSpec { Level = level, PromptKey = Act.Character, PromptText = PromptFor(traitPicks) };
        foreach (var s in (IEnumerable<Content.TaughtSlot>?)build?.Slots ?? Array.Empty<Content.TaughtSlot>())
        {
            if (s.Level != level) continue;
            int slot = slotOf(s.Skill);
            if (slot < 0) continue;
            spec.Kind = LevelCardKind.NewKey; spec.Skill = s.Skill; spec.Slot = slot;
            break;
        }
        if (spec.Kind == LevelCardKind.Plain && ch != null && LampOffer(ch, level) is { } offer) return offer;
        return spec;
    }

    /// <summary>M7a: the lamp card for a level whose carried skill (first in slot order) holds a point: Kind LampLit, Offer,
    /// the live lamp's own text ("Light: +10% damage", Wicks.Text: what the fight runs, not skill_lamps.json's name),
    /// Act.Lamps to light it, the blow's (or the lamp's own) before and after. Null when no skill holds a point.</summary>
    public static LevelCardSpec? LampOffer(Rpg.CharacterData ch, int level)
    {
        foreach (var (id, _) in Rpg.SkillBook.Carried(ch))
        {
            if (Rpg.WickBook.NextLamp(ch, id) is not { } lamp) continue;
            var (measure, before, after) = Rpg.WickBook.LampMeasure(ch, id, lamp);
            return new LevelCardSpec
            {
                Kind = LevelCardKind.LampLit, Offer = true, Level = level, Skill = id, Lamp = lamp,
                Measure = measure, Before = before, After = after,
                PromptKey = Act.Lamps, PromptText = "Light: " + Content.Wicks.Text(id, lamp),
            };
        }
        return null;
    }

    /// <summary>The offer taken: the card turns to the lit state (header "A LAMP LIT", no lighting prompt).</summary>
    public static void Lit(LevelCardSpec s) { s.Offer = false; s.PromptKey = null; s.PromptText = null; }

    /// <summary>A new skill's prompt row: the skills screen's key and these words (it is on no key yet).</summary>
    public const string SkillPrompt = "Put it on a key";

    /// <summary>The card of a skill the calling taught (Journey.CallingTaught): its glyph, name and one line, no key cap
    /// (it is on none), the skills screen's prompt. Level 0: no level in its header.</summary>
    public static LevelCardSpec NewSkill(int level, string skill) =>
        new() { Kind = LevelCardKind.NewSkill, Level = level, Skill = skill, PromptKey = Act.Arts, PromptText = SkillPrompt };

    /// <summary>The calling taught `skill` at this card's level. A plain card becomes the new skill's card, keeping its
    /// level (null back); any other card stays as it is and the new skill's own card, without the level, is returned
    /// to follow it in the queue.</summary>
    public static LevelCardSpec? WithCalling(LevelCardSpec card, string skill)
    {
        if (card.Kind != LevelCardKind.Plain) return NewSkill(0, skill);
        card.Kind = LevelCardKind.NewSkill; card.Skill = skill;
        card.PromptKey = Act.Arts; card.PromptText = SkillPrompt;
        return null;
    }

    /// <summary>--level-card's spec: slot:SKILL:LEVEL | lamp:SKILL:LEVEL:BEFORE:AFTER | offer:SKILL:LEVEL:BEFORE:AFTER | plain:LEVEL | skill:SKILL:LEVEL, each with an optional
    /// @T (seconds into the fight). Null when it does not parse.</summary>
    public static (LevelCardSpec Spec, double At)? Parse(string arg)
    {
        double at = 1.5;
        var a = arg.Trim();
        int k = a.IndexOf('@');
        if (k >= 0)
        {
            if (!double.TryParse(a[(k + 1)..], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out at)) return null;
            a = a[..k];
        }
        var p = a.Split(':');
        static int? I(string v) => int.TryParse(v, out var n) ? n : null;
        static double? D(string v) => double.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var n) ? n : null;
        switch (p[0])
        {
            case "slot" when p.Length == 3 && I(p[2]) is { } l:
                return (new LevelCardSpec { Kind = LevelCardKind.NewKey, Skill = p[1], Level = l }, at);
            case "lamp" when p.Length == 5 && I(p[2]) is { } l && D(p[3]) is { } b && D(p[4]) is { } f:
                return (new LevelCardSpec { Kind = LevelCardKind.LampLit, Skill = p[1], Level = l, Before = b, After = f }, at);
            case "offer" when p.Length == 5 && I(p[2]) is { } l && D(p[3]) is { } b && D(p[4]) is { } f:
                return (new LevelCardSpec { Kind = LevelCardKind.LampLit, Offer = true, Skill = p[1], Level = l, Before = b, After = f, PromptKey = Act.Lamps, PromptText = "Light" }, at);
            case "plain" when p.Length == 2 && I(p[1]) is { } l:
                return (new LevelCardSpec { Kind = LevelCardKind.Plain, Level = l }, at);
            case "skill" when p.Length == 3 && I(p[2]) is { } l:
                return (NewSkill(l, p[1]), at);
        }
        return null;
    }

    /// <summary>--level-card's whole argument: one spec, or two joined by '+' (a key card and the new skill's card that
    /// follows it: "slot:heroic_leap:9@1.5+skill:dawnpulse"). A spec with no @T of its own comes at the time of the one
    /// before it (the queue shows them one after the other). Null when any part does not parse.</summary>
    public static List<(LevelCardSpec Spec, double At)>? ParseAll(string arg)
    {
        var all = new List<(LevelCardSpec Spec, double At)>();
        foreach (var part in arg.Split('+'))
        {
            // (a part after the first may be skill:SKILL with no level: the card that follows its level's key card,
            // "A NEW SKILL"; alone it stays refused, as a card with no level follows nothing)
            var bits = part.Split('@')[0].Split(':');
            bool follow = all.Count > 0 && bits.Length == 2 && bits[0].Trim() == "skill" && bits[1].Trim() != "";
            if (Parse(follow ? part.Replace(bits[1], bits[1] + ":0") : part) is not { } one) return null;
            if (all.Count > 0 && !part.Contains('@')) one.At = all[^1].At;
            all.Add(one);
        }
        return all.Count > 0 ? all : null;
    }
}

/// <summary>The cards' clock: one at a time in the order given; a card waits to begin while held (banners held, a screen
/// open) and, once showing, pauses while held. No allocation per tick.</summary>
public sealed class LevelCardQueue
{
    public enum Phase : byte { None, In, Hold, Out }

    readonly Queue<LevelCardSpec> waiting = new();
    public LevelCardSpec? Current { get; private set; }
    public Phase Now { get; private set; }
    /// <summary>Seconds into the current phase.</summary>
    public double T { get; private set; }
    /// <summary>Set for the one tick a card begins (draw it) and the one its out begins (flash its seat).</summary>
    public bool Began { get; private set; }
    public bool Folding { get; private set; }

    public int Count => waiting.Count + (Current != null ? 1 : 0);

    public void Add(LevelCardSpec s) => waiting.Enqueue(s);

    public double HoldFor(LevelCardSpec s) => s.HasPrompt ? LevelCards.HoldPrompt : LevelCards.Hold;

    /// <summary>The phase's share done (0..1).</summary>
    public double K => Now switch
    {
        Phase.In => Math.Clamp(T / LevelCards.In, 0, 1),
        Phase.Hold => Current != null ? Math.Clamp(T / HoldFor(Current), 0, 1) : 0,
        Phase.Out => Math.Clamp(T / LevelCards.Out, 0, 1),
        _ => 0,
    };

    public void Tick(double dt, bool held)
    {
        Began = Folding = false;
        if (held) return;
        if (Current == null)
        {
            if (waiting.Count == 0) return;
            Current = waiting.Dequeue();
            Now = Phase.In; T = 0; Began = true;
            return;
        }
        T += dt;
        if (Now == Phase.In && T >= LevelCards.In) { T -= LevelCards.In; Now = Phase.Hold; }
        if (Now == Phase.Hold && T >= HoldFor(Current)) { T -= HoldFor(Current); Now = Phase.Out; Folding = true; }
        if (Now == Phase.Out && T >= LevelCards.Out) { Current = null; Now = Phase.None; T = 0; }
    }
}
