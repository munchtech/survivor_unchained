using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/* M4 §4, the level-up card's pure side (no Godot: the tests compile it): what a card says (LevelCardSpec), which kind a
 * campaign level-up makes (LevelCards.ForCampaignLevel, from data/content/unlock_cards.json's row for it; the calling's skill
 * waits for a quiet moment, CallingDue), its words built once (LevelCards.Header/Line), and its clock
 * (LevelCardQueue: in 0.18 s, hold by its words (LevelCards.HoldSecs), out 0.3 s; waiting while held). LevelCard.cs draws it. */

public enum LevelCardKind : byte { NewKey, LampLit, Plain, NewSkill, NewAuto, NewStance, NewRoad }

/// <summary>bd-ui W6: where a card stands and where its tail ends, pure (the tests compile it). The card's bottom (its frame
/// included) stays at least Clear above the status shelf's top in the campaign; the tail is vertical, ending on the top of
/// what opened (a key seat's cap, an auto tile, the front stance disc), so the card shifts sideways until that x lies at
/// least Spare inside its span, then stays inside 720..1244 (clear of the statues). bd-ui W8: rowTop is the status shelf's top, Clear above it.</summary>
public static class LevelCardPlace
{
    public const float Clear = AutoRowModel.CardGap, Spare = 24, MinX = 720, MaxX = 1244, MaxW = MaxX - MinX, Land = 2;

    /// <summary>The room a card's one line has: the card's width less the name's column (the well) and the right pad. A 72-character
    /// line at the line font (UI sans 16, about 6.5 px a character at most) fits it on ONE line: 524 is the whole span between the statues.</summary>
    public const float NameX = 72, Pad = 18, LineRoom = MaxW - NameX - Pad, PxPerChar = 6.5f, LineChars = 72;

    /// <summary>The key a NewKey card's chip shows: the same act the bar's seat of that slot wears (Instrument builds its caps
    /// from this too, so card and seat cannot drift).</summary>
    public static Act CapAct(int slot) => KeyMap.SeatOf(slot) is int seat and >= 0 ? KeyMap.Skills[KeyMap.SeatSlot[seat]] : KeyMap.Skills[Math.Clamp(slot, 0, KeyMap.Skills.Length - 1)];   // (the fifth key has no seat until the HUD is redrawn)

    /// <summary>The card's left x, top y, the tail's x (card space; the card's own centre when no target) and its length
    /// below the card (0 when the target is not below it).</summary>
    /// <summary>(bd-ui W13) The spans of a tail (a vertical line at x from y0 to y1, drawn halfW each side) that stay clear of
    /// the rects (left, top, right, bottom) by clear px on every side: where it would cross a tile or a disc it breaks. A rect
    /// the tail only reaches (its top at or below y1: the target) is not avoided.</summary>
    public static List<(float Y0, float Y1)> StemSpans(float x, float y0, float y1, IEnumerable<(float L, float T, float R, float B)> avoid, float clear = 3, float halfW = 2)
    {
        var cuts = new List<(float, float)>();
        foreach (var (l, t, r, b) in avoid)
        {
            if (t >= y1 - 0.5f || b <= y0) continue;
            // (the target itself is never avoided: a rect holding the tail's x whose bottom reaches y1 is what it lands on)
            if (x >= l && x <= r && b >= y1) continue;
            if (x + halfW <= l - clear || x - halfW >= r + clear) continue;
            cuts.Add((t - clear, b + clear));
        }
        cuts.Sort();
        var l2 = new List<(float, float)>();
        float at = y0;
        foreach (var (c0, c1) in cuts)
        {
            if (c0 > at) l2.Add((at, Math.Min(c0, y1)));
            at = Math.Max(at, c1);
        }
        if (at < y1) l2.Add((at, y1));
        return l2;
    }

    public static (float X, float Y, float TailX, float Stem) Compute(float w, float h, float foot, float? rowTop, (float X, float Y)? target)
    {
        float bottom = rowTop is { } r ? Math.Min(foot, r - Clear) : foot;
        float y = (float)Math.Round(bottom - h);
        float x = 960 - w / 2;
        if (target is { } t)
        {
            float lo = t.X - w + Spare, hi = t.X - Spare;
            if (lo <= hi) x = Math.Clamp(x, lo, hi);
        }
        x = (float)Math.Round(Math.Clamp(x, MinX, Math.Max(MinX, MaxX - w)));
        if (target is not { } tg) return (x, y, w / 2, 0);
        float tx = Math.Clamp(tg.X - x, Spare, Math.Max(Spare, w - Spare));
        return (x, y, (float)Math.Round(tx), Math.Max(0, tg.Y - Land - (y + h)));
    }
}

/// <summary>One level-up card (GameHud.LevelCard; M6 and M7 call it).</summary>
public sealed class LevelCardSpec
{
    public LevelCardKind Kind = LevelCardKind.Plain;
    public int Level = 1;
    /// <summary>NewKey / LampLit / NewSkill: the skill's id (its glyph, name and, but for a lamp, its one line).</summary>
    public string Skill = "";
    /// <summary>NewKey: the slot that opened (0-3, KeyMap.Skills[Slot] is its key; the card folds toward its seat);
    /// -1 none (the card folds toward the coin).</summary>
    public int Slot = -1;
    /// <summary>NewStance (bd-ui W4): the stance's id (its glyph when no off-hand item is worn) and the off-hand item's icon key
    /// ("" none: the ring shows the stance's glyph).</summary>
    public string StanceId = "", Icon = "";
    /// <summary>The header's words after "LEVEL N · " (the unlock row's title); null: the kind's own.</summary>
    public string? Title;
    /// <summary>NewAuto: a skill taught on an auto slot (slot >= Weapons.MaxKeys): no key cap. NewStance: Skill is the stance's
    /// name and the card's cap is Act.Swap.</summary>
    /// <summary>NewKey / NewSkill / NewAuto / NewStance: what it does in one line (null: the skill's description's first clause, LevelCards.Line).</summary>
    public string? Line;
    /// <summary>LampLit: the measure and its before/after ("a blow 42 -> 47").</summary>
    public string Measure = "a blow";
    public double Before, After;
    /// <summary>The prompt row (optional): its key and words ("C", "Choose a new trait"); the card holds 3 s.</summary>
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

    /// <summary>How long a card holds, to be read: 1.4 s and 0.25 s a word (its name and its line), 2.8 to 4.5 s, and 0.8 s more
    /// when it has a prompt row. In and Out stay as they are.</summary>
    public static double HoldSecs(int words, bool prompt) => Math.Clamp(1.4 + 0.25 * words, 2.8, 4.5) + (prompt ? 0.8 : 0);

    /// <summary>The words in some text (split at spaces; an arrow or a lone sign counts as none).</summary>
    public static int Words(string text) => text.Split(' ', StringSplitOptions.RemoveEmptyEntries).Count(w => w.Any(char.IsLetterOrDigit));

    /// <summary>"LEVEL 4 · A NEW KEY", "LEVEL 6 · A LAMP LIT", "LEVEL 6 · A NEW SKILL", "LEVEL 5"; a new skill's card that
    /// follows its level's key card carries no level (Level 0): "A NEW SKILL".</summary>
    public static string Header(LevelCardSpec s) => s.Kind switch
    {
        LevelCardKind.NewKey => $"LEVEL {s.Level} · {s.Title ?? "A NEW KEY"}",
        LevelCardKind.NewAuto => $"LEVEL {s.Level} · {s.Title ?? "AN AUTO SKILL"}",
        LevelCardKind.NewStance => $"LEVEL {s.Level} · {s.Title ?? "A SECOND WEAPON"}",
        LevelCardKind.NewRoad => $"LEVEL {s.Level} · {s.Title ?? "YOUR ROAD"}",
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
    /// <summary>(bd-ui W14) The card's function line for a skill id: its row's in data/content/unlock_cards.json where it has
    /// one, else the description's first clause (Line).</summary>
    public static string Line(string id, string description) =>
        Content.UnlockCards.ForSkill(id) is { Line: not "" } row ? row.Line : Line(description);

    /// <summary>(bd-ui W14) The key the NewKey card draws for a skill: the seat's own (SeatIcon), drawn as the seat draws it (SeatPicture).</summary>
    public static string PictureKey(string skill) =>
        Content.Weapons.All.TryGetValue(skill, out var d) ? SeatIcon.For(skill, d.Art) : "";

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
    public static string PromptFor(int traitPicks) => traitPicks > 0 ? "Choose a new trait" : "Attribute points to spend";

    /// <summary>The card a campaign level makes: a new key when the taught build teaches a skill at that level and the
    /// fight carries it on a slot (slotOf: its slot, -1 when not carried), else plain; with the trait/attribute prompt.</summary>
    public static LevelCardSpec ForCampaignLevel(int level, Content.TaughtBuild? build, Func<string, int> slotOf, int traitPicks, Rpg.CharacterData? ch = null, bool roadRaised = false)
    {
        string? calling = ch?.Archetype ?? Content.TaughtBuilds.CallingOf(build);
        var spec = new LevelCardSpec { Level = level, PromptKey = Act.Character, PromptText = PromptFor(traitPicks) };
        foreach (var s in (IEnumerable<Content.TaughtSlot>?)build?.Slots ?? Array.Empty<Content.TaughtSlot>())
        {
            if (s.Level != level) continue;
            int slot = slotOf(s.Skill);
            if (slot < 0) continue;
            spec.Kind = slot >= Content.Weapons.MaxKeys ? LevelCardKind.NewAuto : LevelCardKind.NewKey; spec.Skill = s.Skill; spec.Slot = slot;
            if (Content.UnlockCards.Of(calling, s.Skill) is { } row) { spec.Title = row.Title; if (row.Line != "") spec.Line = row.Line; }
            break;
        }
        // (the stance's level: a key or auto taught there keeps the card; else the second weapon's card, before any lamp offer)
        if (spec.Kind == LevelCardKind.Plain && build?.Stance is { } st && st.Level == level && StanceCard(level, build, ch) is { } sc)
        {
            sc.PromptKey = spec.PromptKey; sc.PromptText = spec.PromptText;
            if (Content.UnlockCards.Of(calling, "stance") is { } row) { sc.Title = row.Title; if (row.Line != "") sc.Line = row.Line; }
            return sc;
        }
        // (the road's level: a plain level at which Journey raised the road is the road's card, with no prompt row)
        if (spec.Kind == LevelCardKind.Plain && roadRaised && RoadCard(level, calling) is { } road) return road;
        if (spec.Kind == LevelCardKind.Plain && ch != null && LampOffer(ch, level) is { } offer) return offer;
        return spec;
    }

    /// <summary>Your road's card: its row's words (title, line, glyph), no key cap and no prompt row. Null: the calling has no road row.</summary>
    public static LevelCardSpec? RoadCard(int level, string? calling) =>
        Content.UnlockCards.Of(calling, "road") is { } row
            ? new LevelCardSpec { Kind = LevelCardKind.NewRoad, Level = level, Skill = RoadNames(calling), Title = row.Title, Line = row.Line, Icon = row.Icon }
            : null;

    /// <summary>The calling's roads' names joined with " or " (lamps.json, "Road of the " dropped: "Sunderer or Bulwark"), else "Your road".</summary>
    public static string RoadNames(string? calling)
    {
        var names = calling == null ? [] : Content.Lamps.RoadsOf(calling).Select(r => r.Name.StartsWith("Road of the ", StringComparison.Ordinal) ? r.Name["Road of the ".Length..] : r.Name).ToList();
        return names.Count > 0 ? string.Join(" or ", names) : "Your road";
    }

    /// <summary>The cards one campaign level makes (always one: a level that teaches a layer teaches nothing else, and the
    /// calling's own skill is queued apart, at a quiet moment: CallingDue).</summary>
    public static List<LevelCardSpec> CardsFor(int level, Content.TaughtBuild? build, Func<string, int> slotOf, int traitPicks, Rpg.CharacterData? ch = null, bool roadRaised = false) =>
        [ForCampaignLevel(level, build, slotOf, traitPicks, ch, roadRaised)];

    /// <summary>The calling's skill waits until nothing else is up: its card is made when no card shows or waits and no foe
    /// has been near her for QuietFor seconds.</summary>
    public const double QuietFor = 2.0;
    public static bool CallingDue(bool cardUp, double quietFor) => !cardUp && quietFor >= QuietFor;

    /// <summary>The second-weapon card: the stance she takes up (hers if she chose one the calling offers, else the default),
    /// its name, its short line (the flavor's first clause, else "Swap strike: NAME"), the Swap key's cap. Null: no such stance.</summary>
    public static LevelCardSpec? StanceCard(int level, Content.TaughtBuild? build, Rpg.CharacterData? ch)
    {
        if (build?.Stance is not { } st) return null;
        string id = ch != null && ch.Stance != "" && System.Array.IndexOf(st.Offers, ch.Stance) >= 0 ? ch.Stance : st.Default;
        var card = StanceCard(level, id);
        if (card != null && ch?.Equipment[Rpg.EquipSlot.Offhand] is { } oh && Rpg.Items.Get(oh.Def) is { } od) card.Icon = od.Icon;
        return card;
    }

    public static LevelCardSpec? StanceCard(int level, string id)
    {
        if (Content.Stances.Find(id) is not { } d) return null;
        string line = Line(d.Flavor);
        if (line == "") line = d.Strike.Name != "" ? "Swap strike: " + d.Strike.Name : "";
        else line += ", and every swap lands a strike.";
        return new LevelCardSpec { Kind = LevelCardKind.NewStance, Level = level, Skill = d.Name, StanceId = d.Id, Line = line, PromptKey = Act.Character };
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
                PromptKey = Act.Lamps, PromptText = "Light it: " + Content.Wicks.Text(id, lamp),
            };
        }
        return null;
    }

    /// <summary>The dev offer card (--level-card offer:...) made as the real offer is: the skill's next lamp, its live text in the
    /// prompt, and (when BEFORE/AFTER were left out) the blow's real before and after on this character.</summary>
    public static void ResolveDevOffer(LevelCardSpec s, Rpg.CharacterData ch)
    {
        if (!s.Offer || s.Lamp != "" || Rpg.WickBook.NextLamp(ch, s.Skill) is not { } lamp) return;
        var (measure, before, after) = Rpg.WickBook.LampMeasure(ch, s.Skill, lamp);
        s.Lamp = lamp;
        if (double.IsNaN(s.Before) || double.IsNaN(s.After)) { s.Measure = measure; s.Before = before; s.After = after; }
        s.PromptText = "Light it: " + Content.Wicks.Text(s.Skill, lamp);
    }

    /// <summary>The offer taken: the card turns to the lit state (header "A LAMP LIT", no lighting prompt).</summary>
    public static void Lit(LevelCardSpec s) { s.Offer = false; s.PromptKey = null; s.PromptText = null; }

    /// <summary>A new skill's prompt row: the skills screen's key and these words (it is on no key yet).</summary>
    public const string SkillPrompt = "Put it on a key";

    /// <summary>The card of a skill the calling taught (Journey.CallingTaught): its glyph, name and one line, no key cap
    /// (it is on none), the skills screen's prompt. Level 0: no level in its header.</summary>
    public static LevelCardSpec NewSkill(int level, string skill) =>
        new() { Kind = LevelCardKind.NewSkill, Level = level, Skill = skill, PromptKey = Act.Arts, PromptText = SkillPrompt };

    /// <summary>--level-card's spec: slot:SKILL:LEVEL[:SLOT] (SLOT 4+ an auto card) | stance[:ID] (the second weapon's card, level 8) | lamp:SKILL:LEVEL:BEFORE:AFTER | offer:SKILL:LEVEL[:BEFORE:AFTER] | plain:LEVEL | skill:SKILL:LEVEL, each with an optional
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
            case "slot" when (p.Length == 3 || p.Length == 4) && I(p[2]) is { } l:
                // (slot:SKILL:LEVEL[:SLOT]: a slot from MaxKeys on is an auto skill's card)
                int sl = p.Length == 4 && I(p[3]) is { } n ? n : -1;
                return (new LevelCardSpec { Kind = sl >= Content.Weapons.MaxKeys ? LevelCardKind.NewAuto : LevelCardKind.NewKey, Skill = p[1], Level = l, Slot = sl }, at);
            case "stance" when p.Length <= 2:
                return StanceCard(8, p.Length == 2 ? p[1] : Content.Stances.All[0].Id) is { } stanceCard ? (stanceCard, at) : null;
            case "lamp" when p.Length == 5 && I(p[2]) is { } l && D(p[3]) is { } b && D(p[4]) is { } f:
                return (new LevelCardSpec { Kind = LevelCardKind.LampLit, Skill = p[1], Level = l, Before = b, After = f }, at);
            case "offer" when p.Length == 3 && I(p[2]) is { } l:
                return (new LevelCardSpec { Kind = LevelCardKind.LampLit, Offer = true, Skill = p[1], Level = l, Before = double.NaN, After = double.NaN, PromptKey = Act.Lamps, PromptText = "Light" }, at);
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

    /// <summary>The showing card's hold set by what it says (LevelCards.HoldSecs); 0: the plain defaults.</summary>
    public double HoldNow;

    public double HoldFor(LevelCardSpec s) => HoldNow > 0 ? HoldNow : s.HasPrompt ? LevelCards.HoldPrompt : LevelCards.Hold;

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
            Current = waiting.Dequeue(); HoldNow = 0;
            Now = Phase.In; T = 0; Began = true;
            return;
        }
        T += dt;
        if (Now == Phase.In && T >= LevelCards.In) { T -= LevelCards.In; Now = Phase.Hold; }
        if (Now == Phase.Hold && T >= HoldFor(Current)) { T -= HoldFor(Current); Now = Phase.Out; Folding = true; }
        if (Now == Phase.Out && T >= LevelCards.Out) { Current = null; Now = Phase.None; T = 0; }
    }
}

/// <summary>The card never covers her or a telegraph: when any of their screen rects (left, top, right, bottom) meets the
/// card's grown 8 px, its alpha eases to 0.25 within 0.12 s (and back to 1 when clear); while it is faded its hold clock
/// pauses, 3 s in all, and then it leaves anyway. Pure; LevelCard feeds it each frame.</summary>
public sealed class CardFade
{
    public const float Low = 0.25f, Secs = 0.12f, Grow = 8, MaxPause = 3;
    public float Alpha { get; private set; } = 1;
    /// <summary>Seconds of hold clock paused so far this card.</summary>
    public float Paused { get; private set; }

    /// <summary>True when any of `under` meets the card grown by Grow px.</summary>
    public static bool Blocked((float L, float T, float R, float B) card, IEnumerable<(float L, float T, float R, float B)> under)
    {
        foreach (var u in under)
            if (u.L < card.R + Grow && u.R > card.L - Grow && u.T < card.B + Grow && u.B > card.T - Grow) return true;
        return false;
    }

    /// <summary>A card begins: alpha 1, nothing paused.</summary>
    public void Reset() { Alpha = 1; Paused = 0; }

    /// <summary>One frame: move the alpha toward its goal; true when the hold clock must stand still this frame (faded by a
    /// block, holding, and the 3 s not yet spent).</summary>
    public bool Step(bool blocked, bool holding, float dt)
    {
        Alpha = Math.Clamp(Alpha + (blocked ? -1 : 1) * (1 - Low) / Secs * dt, Low, 1);
        if (!blocked || !holding || Paused >= MaxPause) return false;
        Paused = Math.Min(MaxPause, Paused + dt);
        return true;
    }
}
