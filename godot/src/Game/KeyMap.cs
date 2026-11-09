using System;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Play;

/// <summary>What the player can ask for, whatever key or button means it.</summary>
public enum Act
{
    Up, Down, Left, Right, Dash, Flare, Draught, Interact, Inventory, Character, Journal, Map,
    Pause, Confirm, Cancel, Reroll, Banish, Pick1, Pick2, Pick3, Pick4, TabNext, TabPrev, Arts, Skip,
    /// <summary>A menu's second and third thing to do with what has focus (pad X and Y).</summary>
    Alt, Alt2,
    /// <summary>A page within a screen (pad LT and RT): the journal's sections, the map's zoom.</summary>
    SubPrev, SubNext,
    /// <summary>Held at night in the town or the wood: answer the night, the ember pulling her to
    /// the night's fight (docs/design/STORY_NIGHTS_AND_TIME.md).</summary>
    Answer,
    /// <summary>The book's Journal or Map opened wide over the world, or folded back into its panel.</summary>
    Expand,
    /// <summary>Held in play (the Drowned Girl HUD): her level and experience (by night the ember) on the river's card,
    /// readable without a mouse (UI 18, XpLight).</summary>
    Experience,
    /// <summary>The day's book's Lamps tab (L): the board and the wicks (docs/design/LAMPS_SCREEN_BRIEF.md §10).</summary>
    Lamps,
    /// <summary>The six skill slots' keys (M4: LMB, RMB, 1-4; or LMB, RMB, Q E R F): a pressed or channelled skill on that
    /// slot goes off (Battle.PressSkill, HoldSkill); an auto skill ignores them. The draft's Pick1-4 share Digit1-4: a
    /// press a menu takes is never also a skill's (Down), and WorldScene drops any kept through a pause.</summary>
    Skill1, Skill2, Skill3, Skill4, Skill5, Skill6,
}

/// <summary>
/// M4 (docs/design/M4_HUD.md §1): the bindings as data, with no engine in them (Controls reads them; the tests check
/// them). Keys are named as the web game names them (KeyboardEvent.code: 'KeyW', 'Digit1'); mouse buttons are 'Mouse0'
/// (LMB), 'Mouse1' (MMB), 'Mouse2' (RMB). Pad buttons by the names the prompts show ('A', 'LB', 'LT', 'D-pad up').
/// </summary>
public static class KeyMap
{
    /// <summary>The defaults (preset 0, "Mouse and 1-4"): Skill1 the grip on LMB, Skill2 on RMB, Skill3-6 on 1-4; the
    /// Flare on Q only (it gave RMB to Skill2).</summary>
    public static readonly Dictionary<Act, string[]> Defaults = new()
    {
        [Act.Up] = ["KeyW", "ArrowUp"], [Act.Down] = ["KeyS", "ArrowDown"], [Act.Left] = ["KeyA", "ArrowLeft"], [Act.Right] = ["KeyD", "ArrowRight"],
        [Act.Dash] = ["Space", "ShiftLeft"], [Act.Flare] = ["KeyQ"], [Act.Draught] = ["KeyR"], [Act.Interact] = ["KeyE", "KeyF"],
        [Act.Inventory] = ["KeyI", "Tab"], [Act.Character] = ["KeyC"], [Act.Journal] = ["KeyJ"], [Act.Map] = ["KeyM"],
        [Act.Pause] = ["Escape", "KeyP"], [Act.Confirm] = ["Enter", "NumpadEnter"], [Act.Cancel] = ["Escape", "Backspace"],
        [Act.Reroll] = ["KeyX"], [Act.Banish] = ["KeyB"], [Act.Pick1] = ["Digit1"], [Act.Pick2] = ["Digit2"], [Act.Pick3] = ["Digit3"], [Act.Pick4] = ["Digit4"],
        [Act.TabNext] = ["BracketRight"], [Act.TabPrev] = ["BracketLeft"], [Act.Arts] = ["KeyK"], [Act.Skip] = ["KeyV"],
        [Act.Alt] = ["Delete"], [Act.Alt2] = [], [Act.SubPrev] = ["Comma"], [Act.SubNext] = ["Period"], [Act.Answer] = ["KeyN"],
        [Act.Expand] = ["KeyZ"], [Act.Experience] = [XpLight.HoldKey], [Act.Lamps] = ["KeyL"],
        [Act.Skill1] = ["Mouse0"], [Act.Skill2] = ["Mouse2"], [Act.Skill3] = ["Digit1"], [Act.Skill4] = ["Digit2"], [Act.Skill5] = ["Digit3"], [Act.Skill6] = ["Digit4"],
    };

    /// <summary>The skill slots' keys in slot order (slot i is Skills[i]).</summary>
    public static readonly Act[] Skills = [Act.Skill1, Act.Skill2, Act.Skill3, Act.Skill4, Act.Skill5, Act.Skill6];

    public static bool IsSkill(Act a) => a >= Act.Skill1 && a <= Act.Skill6;

    /// <summary>What the controls page lets a player move (a key means one of these at most).</summary>
    public static readonly Act[] Rebindable = [Act.Up, Act.Left, Act.Down, Act.Right, Act.Dash, Act.Flare, Act.Draught, Act.Interact, Act.Inventory, Act.Character, Act.Arts, Act.Lamps, Act.Journal, Act.Map, Act.Reroll, Act.Banish, Act.Skip, Act.Answer, Act.Experience,
        Act.Skill1, Act.Skill2, Act.Skill3, Act.Skill4, Act.Skill5, Act.Skill6];
    /// <summary>Keys no rebind may take (the menus' own). The digits are the draft's, but a skill, the Flare or the Draught
    /// may sit on one (the draft is a menu: a press it takes is never also theirs).</summary>
    public static readonly string[] Reserved = ["Escape", "Enter", "NumpadEnter", "Backspace", "Digit1", "Digit2", "Digit3", "Digit4", "BracketLeft", "BracketRight", "Comma", "Period", "Delete"];
    static bool DigitOk(Act a) => IsSkill(a) || a is Act.Flare or Act.Draught;

    /// <summary>What a player presses in play (a key here means one of these only).</summary>
    public static readonly Act[] PlayActs = [Act.Up, Act.Down, Act.Left, Act.Right, Act.Dash, Act.Flare, Act.Draught, Act.Interact, Act.Inventory, Act.Character, Act.Journal, Act.Map,
        Act.Pause, Act.Arts, Act.Lamps, Act.Answer, Act.Experience, Act.Expand, Act.Skill1, Act.Skill2, Act.Skill3, Act.Skill4, Act.Skill5, Act.Skill6];

    /* ------------------------------------------------------------ presets -- */

    /// <summary>The two layouts on the keys page (M4 §1): 0 "Mouse and 1-4", 1 "Q E R F".</summary>
    public static readonly string[] PresetNames = ["Mouse and 1-4", "Q E R F"];

    /// <summary>What a preset puts where (LMB and RMB are the same in both and are not touched).</summary>
    public static Dictionary<Act, string[]> PresetKeys(int preset) => preset == 1
        ? new() { [Act.Skill3] = ["KeyQ"], [Act.Skill4] = ["KeyE"], [Act.Skill5] = ["KeyR"], [Act.Skill6] = ["KeyF"], [Act.Flare] = ["Digit1"], [Act.Draught] = ["Digit2"], [Act.Interact] = ["KeyG"] }
        : new() { [Act.Skill3] = ["Digit1"], [Act.Skill4] = ["Digit2"], [Act.Skill5] = ["Digit3"], [Act.Skill6] = ["Digit4"], [Act.Flare] = ["KeyQ"], [Act.Draught] = ["KeyR"], [Act.Interact] = ["KeyE", "KeyF"] };

    /// <summary>A fresh copy of the defaults.</summary>
    public static Dictionary<Act, string[]> Fresh() => Defaults.ToDictionary(kv => kv.Key, kv => kv.Value.ToArray());

    /// <summary>Puts a preset's keys on (any other act holding one of them lets it go; one left keyless takes its default).</summary>
    public static void ApplyPreset(Dictionary<Act, string[]> keys, int preset)
    {
        var put = PresetKeys(preset);
        var taken = put.Values.SelectMany(v => v).ToHashSet();
        foreach (var a in Rebindable) if (!put.ContainsKey(a)) keys[a] = keys[a].Where(c => !taken.Contains(c)).ToArray();
        foreach (var (a, v) in put) keys[a] = v.ToArray();
        foreach (var a in Rebindable) if (keys[a].Length == 0) keys[a] = Defaults[a].Where(c => !taken.Contains(c)).ToArray();
    }

    /* ------------------------------------------------------------ rebinds -- */

    /// <summary>Put this key on this action. A skill takes the key alone (its old key or button goes); any other action
    /// in place of its first key (a mouse button stays). Another action holding the key lets it go, and if that leaves
    /// it keyless it takes this action's old key (a swap): no play action is ever left without one. False: refused.</summary>
    public static bool Rebind(Dictionary<Act, string[]> keys, Act a, string code)
    {
        if (!Rebindable.Contains(a)) return false;
        if (Reserved.Contains(code) && !(code.StartsWith("Digit") && DigitOk(a))) return false;
        if (code.StartsWith("Mouse") && !IsSkill(a)) return false;
        var old = keys[a];
        if (old.Contains(code) && (IsSkill(a) || old[0] == code)) return true;
        string[] now;
        if (IsSkill(a)) now = [code];
        else
        {
            var list = old.ToList();
            int i = list.FindIndex(c => !c.StartsWith("Mouse"));
            if (i >= 0) list[i] = code; else list.Insert(0, code);
            now = list.Distinct().ToArray();
        }
        var freed = old.Where(c => !now.Contains(c)).ToList();
        foreach (var b in Rebindable)
        {
            if (b == a || !keys[b].Contains(code)) continue;
            keys[b] = keys[b].Where(c => c != code).ToArray();
            if (keys[b].Length == 0)
            {
                // (the swap: it takes the key this action gave up, one it can hold)
                var give = freed.FirstOrDefault(c => !c.StartsWith("Mouse") || IsSkill(b));
                if (give != null) { keys[b] = [give]; freed.Remove(give); }
            }
        }
        keys[a] = now;
        return true;
    }

    /// <summary>After a load (an old save): a key a skill holds is the skill's (the old Flare's RMB goes); an action left
    /// keyless takes its defaults back. Returns what it changed, for a log.</summary>
    public static List<string> Sanitize(Dictionary<Act, string[]> keys)
    {
        var said = new List<string>();
        var skill = Skills.SelectMany(s => keys[s]).ToHashSet();
        foreach (var a in Rebindable)
        {
            if (IsSkill(a)) continue;
            var keep = keys[a].Where(c => !skill.Contains(c)).ToArray();
            if (keep.Length != keys[a].Length) { said.Add($"{a}: {string.Join(",", keys[a].Except(keep))} given to a skill"); keys[a] = keep; }
        }
        foreach (var a in Rebindable)
            if (keys[a].Length == 0)
            {
                var used = Rebindable.Where(b => b != a).SelectMany(b => keys[b]).ToHashSet();
                keys[a] = Defaults[a].Where(c => !used.Contains(c)).ToArray();
                said.Add($"{a}: keyless, back to {string.Join(",", keys[a])}");
            }
        return said;
    }

    /// <summary>Every key two play actions share ("KeyQ: Flare, Skill3"); none is right.</summary>
    public static List<string> Collisions(Dictionary<Act, string[]> keys)
    {
        var by = new Dictionary<string, List<Act>>();
        foreach (var a in PlayActs)
            foreach (var c in keys[a].Distinct())
                (by.TryGetValue(c, out var l) ? l : by[c] = new()).Add(a);
        return by.Where(kv => kv.Value.Count > 1).Select(kv => $"{kv.Key}: {string.Join(", ", kv.Value)}").ToList();
    }

    /* ---------------------------------------------------------------- pad -- */

    /// <summary>The pad (M4 §1): the grip on A (the thumb holds the swing while the index fires the pressed movement skills
    /// on RB and RT), Skill2 X, Skill3 RB, Skill4 RT, Skill5 Y, Skill6 B; the dash LB, the Flare LT, the draught d-pad
    /// up; Interact shares A out of a fight (Controls.Fighting); the level's card held on d-pad down. In a menu A
    /// confirms, B goes back, X and Y act on what has focus, LB and RB turn the book's tabs, LT and RT a screen's pages.
    /// In play the d-pad does not move her (Controls.Poll): it holds the draught and the card.</summary>
    public static readonly Dictionary<Act, string[]> Pad = new()
    {
        [Act.Skill1] = ["A"], [Act.Skill2] = ["X"], [Act.Skill3] = ["RB"], [Act.Skill4] = ["RT"], [Act.Skill5] = ["Y"], [Act.Skill6] = ["B"],
        [Act.Dash] = ["LB"], [Act.Flare] = ["LT"], [Act.Draught] = ["D-pad up"], [Act.Interact] = ["A"], [Act.Experience] = ["D-pad down"],
        [Act.Confirm] = ["A"], [Act.Cancel] = ["B"], [Act.Inventory] = ["View"], [Act.Pause] = ["Menu"],
        [Act.Up] = ["D-pad up"], [Act.Down] = ["D-pad down"], [Act.Left] = ["D-pad left"], [Act.Right] = ["D-pad right"],
        [Act.TabNext] = ["RB"], [Act.TabPrev] = ["LB"], [Act.Reroll] = ["X"], [Act.Banish] = ["Y"],
        [Act.Skip] = ["R3"], [Act.Answer] = ["L3"],
        [Act.Alt] = ["X"], [Act.Alt2] = ["Y"],
        // (the right stick's click is the skip in play; in the book it opens a page wide)
        [Act.Expand] = ["R3"],
        [Act.SubPrev] = ["LT"], [Act.SubNext] = ["RT"],
    };

    /// <summary>In play the d-pad's directions are not movement (the stick is), and A's Interact is the grip's out of a
    /// fight: two pad buttons that mean two play actions on purpose. The rest of the pad must not.</summary>
    public static List<string> PadCollisions()
    {
        var by = new Dictionary<string, List<Act>>();
        foreach (var a in PlayActs)
        {
            if (a is Act.Up or Act.Down or Act.Left or Act.Right) continue;
            if (!Pad.TryGetValue(a, out var bs)) continue;
            foreach (var b in bs) (by.TryGetValue(b, out var l) ? l : by[b] = new()).Add(a);
        }
        return by.Where(kv => kv.Value.Count > 1 && !(kv.Key == "A" && kv.Value.Count == 2 && kv.Value.Contains(Act.Interact) && kv.Value.Contains(Act.Skill1)))
            .Select(kv => $"{kv.Key}: {string.Join(", ", kv.Value)}").ToList();
    }

    /* -------------------------------------------------------------- seats -- */

    /// <summary>M4 §1: the bar's seats left to right, [1][2][3] (coin) [4][LMB][RMB]: seat k shows slot SeatSlot[k] (the
    /// keyboard's keys on the left, the mouse's on the right). A view only: slots stay stable.</summary>
    public static readonly int[] SeatSlot = [2, 3, 4, 5, 0, 1];

    /// <summary>The seat a slot shows on (SeatSlot's inverse).</summary>
    public static int SeatOf(int slot) => Array.IndexOf(SeatSlot, slot);
}
