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
    public const string Text = "Press *{key}* to open your Lamps and spend the point you hold.";

    public static string TextFor(Func<string, string> keyLabel) => Text.Replace("{key}", keyLabel(Key));

    /// <summary>True when the prompt should go up now (and it marks itself taught); false otherwise.</summary>
    public static bool Take(CharacterData ch, WorldState? w, bool choiceUp)
    {
        if (w == null || choiceUp || w.Arena != null || w.Fact(Fact).Truthy) return false;
        if (!LampBook.LightMyWayWaits(ch, w)) return false;
        w.Facts[Fact] = true;
        return true;
    }

    /// <summary>She opened the Lamps tab herself: the prompt is never owed.</summary>
    public static void Used(WorldState? w) { if (w != null) w.Facts[Fact] = true; }
}
