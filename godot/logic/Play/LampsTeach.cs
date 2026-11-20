using System;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/// <summary>The one prompt that tells her the Lamps tree exists: the first time she holds a point to spend (a level-up that gave
/// one, or a fight begun with one held), "Press L to open your Lamps". Pure; the HUD asks it each fight frame and shows the hint.
/// Once per save (World.Facts "lesson.lamps", as the unlock lessons remember theirs); never in the arena, never while a story
/// choice is up. Opening the Lamps tab herself settles it too (Used).</summary>
public static class LampsTeach
{
    public const string Id = "lamps";
    public const string Fact = "lesson." + Id;
    public const string Title = "Lamps";
    public const string Key = "Lamps";
    // (lane K, the owner 19 Nov: "oh it only does it near a lamp. it said like out of combat or something so I was confused")
    public const string Text = "Lamp ready: *{key}*. Light it out of a fight.";

    /// <summary>More than one held (lane B j1: "the point you hold" read wrong over 6).</summary>
    public const string TextMany = "{n} lamps ready: *{key}*. Light them out of a fight.";

    public static string TextFor(Func<string, string> keyLabel, int points = 1) =>
        (points > 1 ? TextMany.Replace("{n}", points.ToString(System.Globalization.CultureInfo.InvariantCulture)) : Text).Replace("{key}", keyLabel(Key));

    /// <summary>True when the prompt should go up now: a lamp more is ready than she was last told of (lane K, the owner 19 Nov:
    /// "I sitll can't light my lamps": each new lamp says so, not only the first). The fact keeps the count told.</summary>
    public static bool Take(CharacterData ch, WorldState? w, bool choiceUp)
    {
        if (w == null || choiceUp || w.Arena != null) return false;
        int spare = LampBook.Spare(ch, w), told = Told(w);
        if (spare < told) { w.Facts[Fact] = spare; return false; }
        if (spare <= told || !LampBook.LightMyWayWaits(ch, w)) return false;
        w.Facts[Fact] = spare;
        return true;
    }

    /// <summary>The lamps ready she was last told of (an old save's true: one).</summary>
    static int Told(WorldState w) => w.Fact(Fact) is var f && f.Truthy ? Math.Max(1, (int)f.Number) : 0;

    /// <summary>She opened the Lamps tab herself: the lamps ready now are not owed a prompt.</summary>
    public static void Used(WorldState? w, CharacterData? ch = null) { if (w != null) w.Facts[Fact] = ch != null ? Math.Max(1, LampBook.Spare(ch, w)) : 1e6; }
}
