using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.Play;

/// <summary>What the player can ask for, whatever key or button means it.</summary>
public enum Act
{
    Up, Down, Left, Right, Dash, Ability, Ultimate, Interact, Inventory, Character, Journal, Map,
    Pause, Confirm, Cancel, Reroll, Banish, Pick1, Pick2, Pick3, Pick4, TabNext, TabPrev,
}

/// <summary>
/// Input (src/core/input.ts): keyboard, mouse and gamepad folded into named
/// actions. The simulation never reads keys: it reads Move (a vector, analog
/// on a pad), and actions either held or pressed since the last fixed tick.
/// Presses are latched until taken, so a tap between two simulation ticks is
/// never lost. One key can mean several actions (Escape is pause and
/// cancel): the first one a listener takes is the one it meant. Bindings are
/// data, so the settings can rebind them; menus keep theirs (Escape, Enter,
/// the draft's number keys) so nobody can lock themselves out.
/// </summary>
public partial class Controls : Node
{
    /// <summary>A binding: a physical key ('KeyW', as the web game names
    /// them, so saved bindings carry over) or a mouse button ('Mouse2').</summary>
    public static readonly Dictionary<Act, string[]> Defaults = new()
    {
        [Act.Up] = ["KeyW", "ArrowUp"], [Act.Down] = ["KeyS", "ArrowDown"], [Act.Left] = ["KeyA", "ArrowLeft"], [Act.Right] = ["KeyD", "ArrowRight"],
        [Act.Dash] = ["Space", "ShiftLeft"], [Act.Ability] = ["KeyQ", "Mouse2"], [Act.Ultimate] = ["KeyR"], [Act.Interact] = ["KeyE", "KeyF"],
        [Act.Inventory] = ["KeyI", "Tab"], [Act.Character] = ["KeyC"], [Act.Journal] = ["KeyJ"], [Act.Map] = ["KeyM"],
        [Act.Pause] = ["Escape", "KeyP"], [Act.Confirm] = ["Enter", "NumpadEnter"], [Act.Cancel] = ["Escape", "Backspace"],
        [Act.Reroll] = ["KeyX"], [Act.Banish] = ["KeyB"], [Act.Pick1] = ["Digit1"], [Act.Pick2] = ["Digit2"], [Act.Pick3] = ["Digit3"], [Act.Pick4] = ["Digit4"],
        [Act.TabNext] = ["BracketRight"], [Act.TabPrev] = ["BracketLeft"],
    };

    public static readonly Act[] Rebindable = [Act.Up, Act.Left, Act.Down, Act.Right, Act.Dash, Act.Ability, Act.Ultimate, Act.Interact, Act.Inventory, Act.Character, Act.Journal, Act.Map, Act.Reroll, Act.Banish];
    static readonly string[] Reserved = ["Escape", "Enter", "NumpadEnter", "Backspace", "Digit1", "Digit2", "Digit3", "Digit4", "BracketLeft", "BracketRight"];

    /// <summary>The standard pad layout: View opens the pack; the self, the
    /// journal and the map are in the pause menu (Menu), so a pad reaches everything.</summary>
    static readonly Dictionary<Act, JoyButton[]> Pad = new()
    {
        [Act.Dash] = [JoyButton.A], [Act.Ability] = [JoyButton.X], [Act.Ultimate] = [JoyButton.Y], [Act.Interact] = [JoyButton.B],
        [Act.Confirm] = [JoyButton.A], [Act.Cancel] = [JoyButton.B], [Act.Inventory] = [JoyButton.Back], [Act.Pause] = [JoyButton.Start],
        [Act.Up] = [JoyButton.DpadUp], [Act.Down] = [JoyButton.DpadDown], [Act.Left] = [JoyButton.DpadLeft], [Act.Right] = [JoyButton.DpadRight],
        [Act.TabNext] = [JoyButton.RightShoulder], [Act.TabPrev] = [JoyButton.LeftShoulder], [Act.Reroll] = [JoyButton.X], [Act.Banish] = [JoyButton.Y],
    };

    public static Controls Instance { get; private set; } = null!;

    public Dictionary<Act, string[]> Bindings = Defaults.ToDictionary(kv => kv.Key, kv => kv.Value.ToArray());
    readonly HashSet<string> down = new();
    readonly HashSet<Act> latched = new();
    readonly List<Func<Act, bool>> listeners = new();
    /// <summary>Movement intent, length at most 1 (x east, z south, as the sim has it).</summary>
    public float MoveX, MoveZ;
    public bool UsingPad;
    /// <summary>A menu or conversation has the keys: the survivor stands still.</summary>
    public bool Captured;

    const string SaveFile = "user://bindings.json";

    public Controls() { Instance = this; ProcessPriority = -100; }

    public override void _Ready() => LoadBindings();

    /// <summary>The interface hears actions as they happen (menus move on a
    /// press). A listener returning true takes it.</summary>
    public Action On(Func<Act, bool> fn)
    {
        listeners.Add(fn);
        return () => listeners.Remove(fn);
    }

    IEnumerable<Act> ActsFor(string code) => Bindings.Where(kv => kv.Value.Contains(code)).Select(kv => kv.Key);

    void Down(string code)
    {
        down.Add(code);
        bool handled = false;
        foreach (var a in ActsFor(code).ToList())
        {
            latched.Add(a);
            if (handled) continue;
            foreach (var l in listeners.ToList()) if (l(a)) { handled = true; break; }
        }
    }

    public override void _Input(InputEvent e)
    {
        switch (e)
        {
            case InputEventKey k when !k.Echo:
                var code = CodeOf(k.PhysicalKeycode);
                if (code == null) return;
                if (k.Pressed) { UsingPad = false; Down(code); }
                else down.Remove(code);
                break;
            case InputEventMouseButton m:
                var mc = m.ButtonIndex switch { MouseButton.Left => "Mouse0", MouseButton.Middle => "Mouse1", MouseButton.Right => "Mouse2", _ => null };
                if (mc == null) return;
                if (m.Pressed) { foreach (var a in ActsFor(mc)) latched.Add(a); down.Add(mc); }
                else down.Remove(mc);
                break;
            case InputEventJoypadButton j:
                if (!j.Pressed) return;
                UsingPad = true;
                bool taken = false;
                foreach (var (a, buttons) in Pad)
                {
                    if (!buttons.Contains(j.ButtonIndex)) continue;
                    latched.Add(a);
                    if (!taken) foreach (var l in listeners.ToList()) if (l(a)) { taken = true; break; }
                }
                break;
        }
    }

    public override void _Notification(int what)
    {
        // Away from the window, nothing stays held.
        if (what == NotificationApplicationFocusOut) down.Clear();
    }

    public bool Held(Act a)
    {
        foreach (var c in Bindings[a]) if (down.Contains(c)) return true;
        if (Pad.TryGetValue(a, out var bs)) foreach (var b in bs) foreach (var dev in Input.GetConnectedJoypads()) if (Input.IsJoyButtonPressed(dev, b)) return true;
        return false;
    }

    /// <summary>True once per press; takes the latch.</summary>
    public bool Pressed(Act a) => latched.Remove(a);

    public void ClearLatches() => latched.Clear();

    /// <summary>A press as if the key went down (tools, the autopilot).</summary>
    public void Press(Act a)
    {
        latched.Add(a);
        foreach (var l in listeners.ToList()) if (l(a)) break;
    }

    public override void _Process(double delta) => Poll();

    /// <summary>Movement from the keys and the left stick.</summary>
    void Poll()
    {
        float x = 0, z = 0;
        if (Held(Act.Left)) x -= 1;
        if (Held(Act.Right)) x += 1;
        if (Held(Act.Up)) z -= 1;
        if (Held(Act.Down)) z += 1;
        foreach (var dev in Input.GetConnectedJoypads())
        {
            float ax = Input.GetJoyAxis(dev, JoyAxis.LeftX), az = Input.GetJoyAxis(dev, JoyAxis.LeftY);
            float m = Mathf.Sqrt(ax * ax + az * az);
            if (m > 0.18f)
            {
                float s = Mathf.Min(1, (m - 0.18f) / 0.72f) / m;
                x += ax * s;
                z += az * s;
                UsingPad = true;
            }
        }
        float len = Mathf.Sqrt(x * x + z * z);
        if (len > 1) { x /= len; z /= len; }
        MoveX = Captured ? 0 : x;
        MoveZ = Captured ? 0 : z;
    }

    /* ----------------------------------------------------------- binding -- */

    /// <summary>Put this key on this action (in place of its first key; a
    /// mouse button stays). A key means one of the rebindable actions only.</summary>
    public bool Rebind(Act a, string code)
    {
        if (!Rebindable.Contains(a) || Reserved.Contains(code)) return false;
        foreach (var b in Rebindable) if (b != a) Bindings[b] = Bindings[b].Where(c => c != code).ToArray();
        var list = Bindings[a].ToList();
        int i = list.FindIndex(c => !c.StartsWith("Mouse"));
        if (i >= 0) list[i] = code; else list.Insert(0, code);
        Bindings[a] = list.Distinct().ToArray();
        SaveBindings();
        return true;
    }

    public void ResetBindings()
    {
        Bindings = Defaults.ToDictionary(kv => kv.Key, kv => kv.Value.ToArray());
        SaveBindings();
    }

    void LoadBindings()
    {
        if (!FileAccess.FileExists(SaveFile)) return;
        try
        {
            var saved = JsonSerializer.Deserialize<Dictionary<string, string[]>>(FileAccess.GetFileAsString(SaveFile));
            if (saved == null) return;
            foreach (var a in Rebindable)
                if (saved.TryGetValue(Key(a), out var v) && v.Length > 0) Bindings[a] = v;
        }
        catch (JsonException) { /* nothing sensible in it */ }
    }

    void SaveBindings()
    {
        var o = Rebindable.ToDictionary(Key, a => Bindings[a]);
        using var f = FileAccess.Open(SaveFile, FileAccess.ModeFlags.Write);
        f?.StoreString(JsonSerializer.Serialize(o));
    }

    /// <summary>The web game's name for an action ('ability').</summary>
    static string Key(Act a) => char.ToLowerInvariant(a.ToString()[0]) + a.ToString()[1..];

    /* ------------------------------------------------------------- names -- */

    /// <summary>A Godot key as the web game names it (KeyboardEvent.code).</summary>
    public static string? CodeOf(Key k) => k switch
    {
        >= Godot.Key.A and <= Godot.Key.Z => "Key" + (char)('A' + (k - Godot.Key.A)),
        >= Godot.Key.Key0 and <= Godot.Key.Key9 => "Digit" + (char)('0' + (k - Godot.Key.Key0)),
        Godot.Key.Space => "Space", Godot.Key.Shift => "ShiftLeft", Godot.Key.Ctrl => "ControlLeft", Godot.Key.Alt => "AltLeft",
        Godot.Key.Escape => "Escape", Godot.Key.Enter => "Enter", Godot.Key.KpEnter => "NumpadEnter", Godot.Key.Backspace => "Backspace",
        Godot.Key.Tab => "Tab", Godot.Key.Up => "ArrowUp", Godot.Key.Down => "ArrowDown", Godot.Key.Left => "ArrowLeft", Godot.Key.Right => "ArrowRight",
        Godot.Key.Bracketleft => "BracketLeft", Godot.Key.Bracketright => "BracketRight", Godot.Key.Capslock => "CapsLock",
        Godot.Key.Semicolon => "Semicolon", Godot.Key.Apostrophe => "Quote", Godot.Key.Comma => "Comma", Godot.Key.Period => "Period",
        Godot.Key.Slash => "Slash", Godot.Key.Backslash => "Backslash", Godot.Key.Minus => "Minus", Godot.Key.Equal => "Equal", Godot.Key.Quoteleft => "Backquote",
        _ => null,
    };

    static readonly Dictionary<string, string> Named = new()
    {
        ["Mouse0"] = "LMB", ["Mouse1"] = "MMB", ["Mouse2"] = "RMB", ["ShiftLeft"] = "Shift", ["ControlLeft"] = "Ctrl", ["AltLeft"] = "Alt",
        ["CapsLock"] = "Caps", ["ArrowUp"] = "↑", ["ArrowDown"] = "↓", ["ArrowLeft"] = "←", ["ArrowRight"] = "→", ["BracketLeft"] = "[",
        ["BracketRight"] = "]", ["NumpadEnter"] = "Enter", ["Escape"] = "Esc", ["Backspace"] = "Backspace", ["Semicolon"] = ";", ["Quote"] = "'",
        ["Comma"] = ",", ["Period"] = ".", ["Slash"] = "/", ["Backslash"] = "\\", ["Minus"] = "-", ["Equal"] = "=", ["Backquote"] = "`",
    };

    public static string Label(string code) =>
        Named.TryGetValue(code, out var n) ? n : code.StartsWith("Key") ? code[3..] : code.StartsWith("Digit") ? code[5..] : code;

    public string KeyLabel(Act a) => Label(Bindings[a].FirstOrDefault() ?? "");
    public IEnumerable<string> KeyLabels(Act a) => Bindings[a].Select(Label);

    static readonly Dictionary<JoyButton, string> PadNames = new()
    {
        [JoyButton.A] = "A", [JoyButton.B] = "B", [JoyButton.X] = "X", [JoyButton.Y] = "Y", [JoyButton.LeftShoulder] = "LB", [JoyButton.RightShoulder] = "RB",
        [JoyButton.Back] = "View", [JoyButton.Start] = "Menu", [JoyButton.DpadUp] = "D-pad up", [JoyButton.DpadDown] = "D-pad down",
        [JoyButton.DpadLeft] = "D-pad left", [JoyButton.DpadRight] = "D-pad right",
    };

    public IEnumerable<string> PadLabels(Act a) => Pad.TryGetValue(a, out var bs) ? bs.Select(b => PadNames.TryGetValue(b, out var n) ? n : $"B{(int)b}") : [];
}
