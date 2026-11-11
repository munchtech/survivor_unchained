using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Godot;

namespace SurvivorUnchained.Play;

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
    /// them, so saved bindings carry over) or a mouse button ('Mouse2'). The data is KeyMap's (M4).</summary>
    public static Dictionary<Act, string[]> Defaults => KeyMap.Defaults;

    /// <summary>The skill slots' keys in slot order (slot i is Skills[i]).</summary>
    public static readonly Act[] Skills = KeyMap.Skills;

    public static readonly Act[] Rebindable = KeyMap.Rebindable;

    /// <summary>The pad (KeyMap.Pad, M4 §1) as the engine's buttons; LT and RT are axes (PadTrig: 1 LT, 2 RT).</summary>
    static readonly Dictionary<Act, JoyButton[]> Pad = KeyMap.Pad.ToDictionary(kv => kv.Key, kv => kv.Value.Select(ButtonOf).Where(b => b != JoyButton.Invalid).ToArray());
    static readonly Dictionary<Act, int> PadTrig = KeyMap.Pad.ToDictionary(kv => kv.Key, kv => (kv.Value.Contains("LT") ? 1 : 0) | (kv.Value.Contains("RT") ? 2 : 0));
    /// <summary>What LT and RT mean in play (their menu meaning, SubPrev and SubNext, is MenuPoll's).</summary>
    static readonly Act[] PlayLT = KeyMap.Pad.Where(kv => kv.Value.Contains("LT") && kv.Key is not (Act.SubPrev or Act.SubNext)).Select(kv => kv.Key).ToArray();
    static readonly Act[] PlayRT = KeyMap.Pad.Where(kv => kv.Value.Contains("RT") && kv.Key is not (Act.SubPrev or Act.SubNext)).Select(kv => kv.Key).ToArray();

    static JoyButton ButtonOf(string name) => name switch
    {
        "A" => JoyButton.A, "B" => JoyButton.B, "X" => JoyButton.X, "Y" => JoyButton.Y, "LB" => JoyButton.LeftShoulder, "RB" => JoyButton.RightShoulder,
        "View" => JoyButton.Back, "Menu" => JoyButton.Start, "D-pad up" => JoyButton.DpadUp, "D-pad down" => JoyButton.DpadDown,
        "D-pad left" => JoyButton.DpadLeft, "D-pad right" => JoyButton.DpadRight, "L3" => JoyButton.LeftStick, "R3" => JoyButton.RightStick,
        _ => JoyButton.Invalid,
    };

    /// <summary>In a menu one button means its menu meaning first: A is
    /// confirm before it is a dash, B is back before it is a word with
    /// someone, X and Y act on what has focus.</summary>
    static readonly Act[] MenuFirst = [Act.Confirm, Act.Cancel, Act.Alt, Act.Alt2, Act.Up, Act.Down, Act.Left, Act.Right, Act.TabNext, Act.TabPrev, Act.SubNext, Act.SubPrev, Act.Pause, Act.Inventory];
    static readonly Act[] Directions = [Act.Up, Act.Down, Act.Left, Act.Right];

    public static Controls Instance { get; private set; } = null!;

    public Dictionary<Act, string[]> Bindings = KeyMap.Fresh();
    /// <summary>The keys page's layout (KeyMap.PresetNames: 0 "Mouse and 1-4", 1 "Q E R F"), saved beside the bindings.</summary>
    public int Preset { get; private set; }
    /// <summary>Counts every change of the bindings (a rebind, a preset, a reset, a load): the HUD's key caps re-label
    /// when it moves (an int compared each frame, nothing built).</summary>
    public int Version { get; private set; }
    /// <summary>A fight is on round her (GameHud.Frame sets it): the pad's A is the grip's alone, not also Interact.</summary>
    public bool Fighting;
    readonly HashSet<string> down = new();
    /// <summary>Keys and buttons whose press a listener took (a menu, a word with someone): while they stay down they
    /// hold no skill (a tap of A that opened a chest does not also swing).</summary>
    readonly HashSet<string> taken = new();
    readonly HashSet<JoyButton> padTaken = new();
    readonly HashSet<Act> latched = new();
    readonly List<Func<Act, bool>> listeners = new();
    /// <summary>Movement intent, length at most 1 (x east, z south, as the sim has it).</summary>
    public float MoveX, MoveZ;
    /// <summary>The right stick, past its dead zone (x right, y down): what a
    /// screen turns or brings near with it (the figure in creation).</summary>
    public Vector2 Look;
    /// <summary>The mouse wheel turned since last taken (notches, up positive): in play, the close view of
    /// her in town (CloseUp); the screens hear the wheel themselves.</summary>
    public double Wheel;
    /// <summary>Anything at all was touched since last taken (a key, a button, a click, the mouse moved, a
    /// stick): the idle close view ends.</summary>
    public bool Touched;
    bool usingPad;
    /// <summary>The pad was touched last (the prompts show its buttons); a
    /// key, a click or a real move of the mouse turns it back.</summary>
    public bool UsingPad
    {
        get => usingPad;
        set { if (usingPad == value) return; usingPad = value; DeviceChanged?.Invoke(); }
    }
    /// <summary>The device last touched changed: prompts redraw with its keys or buttons.</summary>
    public event Action? DeviceChanged;
    /// <summary>A menu or conversation has the keys: the survivor stands still.</summary>
    public bool Captured;
    /// <summary>Something over the game has the buttons (a screen, the draft, a
    /// conversation): pad buttons mean their menu meaning first, and a held
    /// direction repeats.</summary>
    public bool MenuMode;
    // A held direction (pad or stick) repeats after a beat, then steadily.
    const double RepeatDelay = 0.36, RepeatEvery = 0.11;
    Act? heldDir;
    double heldT;
    bool triggerL, triggerR;

    const string SaveFile = "user://bindings.json";

    public Controls() { Instance = this; ProcessPriority = -100; }

    public override void _Ready()
    {
        LoadBindings();
        // (--keys-preset N, pictures: that layout on, and saved as a player's pick would be)
        if (Args.Get("keys-preset") is string kp && int.TryParse(kp, out int pi)) ApplyPreset(pi);
        // (--pad: the prompts and the seats' caps as a pad's from the first frame, a picture's)
        if (Args.Has("pad")) UsingPad = true;
    }

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
        // A key a menu took (the draft's 1-4) is not also a skill's press once the menu closes, nor a held one.
        if (handled) { foreach (var s in Skills) latched.Remove(s); taken.Add(code); }
    }

    public override void _Input(InputEvent e)
    {
        if (e is not InputEventMouseMotion and not InputEventJoypadMotion || e is InputEventMouseMotion { Relative: var rel } && rel.Length() > 2) Touched = true;
        switch (e)
        {
            case InputEventMouseButton { ButtonIndex: MouseButton.WheelUp or MouseButton.WheelDown, Pressed: true } w:
                UsingPad = false;
                Wheel += (w.ButtonIndex == MouseButton.WheelUp ? 1 : -1) * (w.Factor > 0 ? Mathf.Min(w.Factor, 1) : 1);
                return;
            case InputEventKey k:
                var code = CodeOf(k.PhysicalKeycode);
                if (code == null) return;
                // A key held in a menu repeats (the system's own rate); in play it is held, not repeated.
                if (k.Echo && !(MenuMode && ActsFor(code).Any(a => Directions.Contains(a)))) return;
                if (k.Pressed) { UsingPad = false; Down(code); }
                else { down.Remove(code); taken.Remove(code); }
                break;
            case InputEventMouseButton m:
                var mc = m.ButtonIndex switch { MouseButton.Left => "Mouse0", MouseButton.Middle => "Mouse1", MouseButton.Right => "Mouse2", _ => null };
                if (mc == null) return;
                if (m.Pressed)
                {
                    UsingPad = false;
                    // (M4: LMB and RMB are skills; a click on the interface, or in a menu, is not a swing)
                    bool onUi = MenuMode || Captured || GetViewport()?.GuiGetHoveredControl() is { MouseFilter: Control.MouseFilterEnum.Stop };
                    foreach (var a in ActsFor(mc)) if (!(onUi && KeyMap.IsSkill(a))) latched.Add(a);
                    down.Add(mc);
                    if (onUi) taken.Add(mc);
                }
                else { down.Remove(mc); taken.Remove(mc); }
                break;
            case InputEventMouseMotion mm when mm.Relative.Length() > 6:
                UsingPad = false;
                break;
            case InputEventJoypadButton j:
                if (!j.Pressed) { padTaken.Remove(j.ButtonIndex); return; }
                UsingPad = true;
                bool tookIt = false;
                foreach (var a in PadActs(j.ButtonIndex))
                {
                    latched.Add(a);
                    if (!tookIt) foreach (var l in listeners.ToList()) if (l(a)) { tookIt = true; break; }
                }
                // (as a key: a press a listener took is no skill's, now or while held)
                if (tookIt) { foreach (var s in Skills) latched.Remove(s); padTaken.Add(j.ButtonIndex); }
                if (MenuMode && PadActs(j.ButtonIndex).Where(Directions.Contains).Cast<Act?>().FirstOrDefault() is Act dir) { heldDir = dir; heldT = 0; }
                break;
        }
    }

    /// <summary>What a pad button means now, in the order it is offered.</summary>
    IEnumerable<Act> PadActs(JoyButton b)
    {
        var acts = Pad.Where(kv => kv.Value.Contains(b)).Select(kv => kv.Key);
        // (M4: A is Interact only out of a fight; in play Interact is offered before the grip, so a chest takes it)
        if (!MenuMode && Fighting) acts = acts.Where(a => a != Act.Interact);
        return MenuMode ? acts.OrderBy(a => Array.IndexOf(MenuFirst, a) is int i and >= 0 ? i : 99) : acts.OrderBy(a => KeyMap.IsSkill(a) ? 1 : 0);
    }

    /// <summary>An action fired as a fresh press (a repeat, a trigger).</summary>
    void Fire(Act a)
    {
        UsingPad = true;
        latched.Add(a);
        foreach (var l in listeners.ToList()) if (l(a)) break;
    }

    public override void _Notification(int what)
    {
        // Away from the window, nothing stays held.
        if (what == NotificationApplicationFocusOut) { down.Clear(); taken.Clear(); padTaken.Clear(); }
    }

    // (The pads plugged in, asked of the engine once a frame: each ask is a new tracked Godot array, and Held asks per
    // binding, many times a frame; they outlived the young collection.)
    static int[] pads = System.Array.Empty<int>();
    static ulong padsFrame = ulong.MaxValue;
    static int[] Pads()
    {
        ulong f = Engine.GetProcessFrames();
        if (f != padsFrame) { padsFrame = f; var a = Input.GetConnectedJoypads(); pads = a.Count == pads.Length ? Fill(a, pads) : Fill(a, new int[a.Count]); }
        return pads;
        static int[] Fill(Godot.Collections.Array<int> a, int[] into) { for (int k = 0; k < into.Length; k++) into[k] = a[k]; return into; }
    }

    public bool Held(Act a)
    {
        bool skill = KeyMap.IsSkill(a);
        foreach (var c in Bindings[a]) if (down.Contains(c) && !(skill && taken.Contains(c))) return true;
        // (M4: in play the d-pad is the draught and the level's card, not movement; the stick moves her)
        if (!MenuMode && a is Act.Up or Act.Down or Act.Left or Act.Right) return false;
        if (Pad.TryGetValue(a, out var bs)) foreach (var b in bs) foreach (var dev in Pads()) if (Input.IsJoyButtonPressed(dev, b) && !(skill && padTaken.Contains(b))) return true;
        if (!MenuMode && PadTrig.TryGetValue(a, out int tr) && tr != 0)
            foreach (var dev in Pads())
                if ((tr & 1) != 0 && Input.GetJoyAxis(dev, JoyAxis.TriggerLeft) > TriggerOn || (tr & 2) != 0 && Input.GetJoyAxis(dev, JoyAxis.TriggerRight) > TriggerOn) return true;
        return false;
    }
    const float TriggerOn = 0.5f;

    /// <summary>True once per press; takes the latch.</summary>
    public bool Pressed(Act a) => latched.Remove(a);

    public void ClearLatches() => latched.Clear();

    /// <summary>A press as if the key went down (tools, the autopilot).</summary>
    public void Press(Act a)
    {
        latched.Add(a);
        foreach (var l in listeners.ToList()) if (l(a)) break;
    }

    public override void _Process(double delta)
    {
        Poll();
        if (MenuMode) MenuPoll(delta); else { heldDir = null; PlayTriggers(); }
    }

    /// <summary>In play (M4): LT and RT pressed are their play actions' presses (the Flare, Skill4).</summary>
    void PlayTriggers()
    {
        bool l = false, r = false;
        foreach (var dev in Pads())
        {
            float lt = Input.GetJoyAxis(dev, JoyAxis.TriggerLeft), rt = Input.GetJoyAxis(dev, JoyAxis.TriggerRight);
            l |= lt > 0.6f || triggerL && lt > 0.3f;
            r |= rt > 0.6f || triggerR && rt > 0.3f;
        }
        if (l && !triggerL) foreach (var a in PlayLT) Fire(a);
        if (r && !triggerR) foreach (var a in PlayRT) Fire(a);
        triggerL = l; triggerR = r;
    }

    /// <summary>In a menu: the left stick moves focus like the D-pad, a held
    /// direction repeats, and the triggers turn pages.</summary>
    void MenuPoll(double dt)
    {
        Act? stick = null, dpad = null;
        foreach (var dev in Pads())
        {
            float ax = Input.GetJoyAxis(dev, JoyAxis.LeftX), ay = Input.GetJoyAxis(dev, JoyAxis.LeftY);
            if (Mathf.Max(Mathf.Abs(ax), Mathf.Abs(ay)) > 0.55f) stick = Mathf.Abs(ax) > Mathf.Abs(ay) ? (ax > 0 ? Act.Right : Act.Left) : (ay > 0 ? Act.Down : Act.Up);
            foreach (var d in Directions) if (Pad[d].Any(b => Input.IsJoyButtonPressed(dev, b))) dpad = d;
            bool l = Input.GetJoyAxis(dev, JoyAxis.TriggerLeft) > 0.6f, r = Input.GetJoyAxis(dev, JoyAxis.TriggerRight) > 0.6f;
            if (l && !triggerL) Fire(Act.SubPrev);
            if (r && !triggerR) Fire(Act.SubNext);
            triggerL = l || Input.GetJoyAxis(dev, JoyAxis.TriggerLeft) > 0.3f && triggerL;
            triggerR = r || Input.GetJoyAxis(dev, JoyAxis.TriggerRight) > 0.3f && triggerR;
        }
        var now = dpad ?? stick;
        if (now == null) { heldDir = null; return; }
        if (now != heldDir)
        {
            // The stick's first push is a press of its own (the D-pad's came as a button).
            heldDir = now;
            heldT = 0;
            if (dpad == null) Fire(now.Value);
            return;
        }
        heldT += dt;
        if (heldT >= RepeatDelay) { heldT -= RepeatEvery; Fire(now.Value); }
    }

    /// <summary>Movement from the keys and the left stick.</summary>
    void Poll()
    {
        float x = 0, z = 0;
        if (Held(Act.Left)) x -= 1;
        if (Held(Act.Right)) x += 1;
        if (Held(Act.Up)) z -= 1;
        if (Held(Act.Down)) z += 1;
        foreach (var dev in Pads())
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
        var look = Vector2.Zero;
        foreach (var dev in Pads())
        {
            var r = new Vector2(Input.GetJoyAxis(dev, JoyAxis.RightX), Input.GetJoyAxis(dev, JoyAxis.RightY));
            float m = r.Length();
            if (m > 0.2f) { look += r / m * Mathf.Min(1, (m - 0.2f) / 0.7f); UsingPad = true; }
        }
        Look = look.LimitLength(1);
        if (Look != Vector2.Zero || x != 0 || z != 0) Touched = true;
    }

    /* ----------------------------------------------------------- binding -- */

    /// <summary>Put this key on this action (in place of its first key; a
    /// mouse button stays). A key means one of the rebindable actions only.</summary>
    public bool Rebind(Act a, string code)
    {
        if (!KeyMap.Rebind(Bindings, a, code)) return false;
        Version++;
        SaveBindings();
        return true;
    }

    public void ResetBindings()
    {
        Bindings = KeyMap.Fresh();
        Preset = 0;
        Version++;
        SaveBindings();
    }

    /// <summary>The keys page's layout (M4 §1): its keys on, saved; the HUD's caps re-label at once (Version).</summary>
    public void ApplyPreset(int preset)
    {
        preset = Math.Clamp(preset, 0, KeyMap.PresetNames.Length - 1);
        KeyMap.ApplyPreset(Bindings, preset);
        Preset = preset;
        Version++;
        SaveBindings();
    }

    void LoadBindings()
    {
        if (!FileAccess.FileExists(SaveFile)) return;
        try
        {
            var saved = JsonSerializer.Deserialize<Dictionary<string, string?[]?>>(FileAccess.GetFileAsString(SaveFile));
            if (saved == null) return;
            // (every entry checked: a bad one keeps that action's default, never the rest's, SU-011)
            if (KeyMap.LoadSaved(saved, Bindings) is int pi) Preset = Math.Clamp(pi, 0, KeyMap.PresetNames.Length - 1);
            // (an old save: the skills' keys are theirs; the Flare's old RMB goes)
            foreach (var line in KeyMap.Sanitize(Bindings)) GD.Print($"bindings: {line}");
            Version++;
        }
        catch (JsonException) { /* nothing sensible in it */ }
    }

    void SaveBindings()
    {
        var o = Rebindable.ToDictionary(Key, a => Bindings[a]);
        o["preset"] = [Preset.ToString(System.Globalization.CultureInfo.InvariantCulture)];
        // (written beside, then moved over: a failed write keeps the old bindings, SU-010)
        if (!Core.AtomicFile.Write(ProjectSettings.GlobalizePath(SaveFile), JsonSerializer.Serialize(o))) GD.PushWarning("bindings: could not be saved");
    }

    /// <summary>The web game's name for an action ('flare', once 'ability'; LoadBindings reads the old keys).</summary>
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
        Godot.Key.Delete => "Delete",
        _ => null,
    };

    static readonly Dictionary<string, string> Named = new()
    {
        ["Mouse0"] = "LMB", ["Mouse1"] = "MMB", ["Mouse2"] = "RMB", ["ShiftLeft"] = "Shift", ["ControlLeft"] = "Ctrl", ["AltLeft"] = "Alt",
        ["CapsLock"] = "Caps", ["ArrowUp"] = "Up", ["ArrowDown"] = "Down", ["ArrowLeft"] = "Left", ["ArrowRight"] = "Right", ["BracketLeft"] = "[",
        ["BracketRight"] = "]", ["NumpadEnter"] = "Enter", ["Escape"] = "Esc", ["Backspace"] = "Backspace", ["Semicolon"] = ";", ["Quote"] = "'",
        ["Comma"] = ",", ["Period"] = ".", ["Slash"] = "/", ["Backslash"] = "\\", ["Minus"] = "-", ["Equal"] = "=", ["Backquote"] = "`",
        ["Delete"] = "Del",
    };

    public static string Label(string code) =>
        Named.TryGetValue(code, out var n) ? n : code.StartsWith("Key") ? code[3..] : code.StartsWith("Digit") ? code[5..] : code;

    public string KeyLabel(Act a) => Label(Bindings[a].FirstOrDefault() ?? "");
    public IEnumerable<string> KeyLabels(Act a) => Bindings[a].Select(Label);

    public IEnumerable<string> PadLabels(Act a) => KeyMap.Pad.TryGetValue(a, out var bs) ? bs : [];

    /// <summary>The one key or button that means this now, for a prompt.</summary>
    public string PromptLabel(Act a) => UsingPad ? PadLabels(a).FirstOrDefault() ?? KeyLabel(a) : KeyLabel(a);
}
