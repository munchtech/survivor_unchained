using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>What a control that is not a button does when it has focus and
/// is pressed (an item's slot, a line of a conversation).</summary>
public sealed class NavItem
{
    public string Id = "";
    public Action? Press, Alt, Alt2, Focus, Blur;
    /// <summary>Left and right change it instead of moving away (a slider): -1 or +1.</summary>
    public Action<int>? Adjust;
}

/// <summary>
/// Focus, moved with the keys or a pad (docs/UI_DESIGN.md, "Navigation").
/// Every visible button on a screen can take focus; other controls join
/// with <see cref="Mark"/>. The arrows, the D-pad and the stick move it to
/// the nearest thing that way; A or Enter presses it; X and Y do what the
/// thing offers besides. Focus is kept by name, so a screen built again
/// after a change still has it where it was. The mouse and the pad hand
/// focus to each other: the pointer moves it, the first press of a
/// direction shows where it is, and the ring round it only shows while
/// the keys or the pad are in use.
/// </summary>
public sealed class Nav
{
    static readonly ConditionalWeakTable<Control, NavItem> marks = new();

    /// <summary>The ring is shown: the keys or the pad were used last, not the mouse.</summary>
    public static bool KeyMode;

    static ulong mouseMovedAt;
    /// <summary>The mouse was moved by a hand just now (not a control built under a resting pointer).</summary>
    public static bool MouseMoved => Time.GetTicksMsec() - mouseMovedAt < 200;
    public static void MouseMotion() => mouseMovedAt = Time.GetTicksMsec();

    readonly Control host;
    /// <summary>Only what is under this can take focus (a side panel); null, all of the host.</summary>
    public Control? Scope;
    /// <summary>What takes focus first, when what had it is gone.</summary>
    public string? Prefer;
    public string? FocusId;
    public bool Enabled = true;
    readonly List<(Control C, string Id, NavItem? Info)> items = new();
    Panel? ring;
    double t;
    // A screen built this frame has not been laid out: a direction waits a frame for it.
    ulong builtFrame;
    readonly List<Act> waiting = new();

    public Nav(Control host) { this.host = host; }

    /// <summary>A control that can take focus, with what pressing it does.</summary>
    public static T Mark<T>(T c, string id, Action? press, Action? alt = null, Action? alt2 = null, Action? focus = null, Action? blur = null, Action<int>? adjust = null) where T : Control
    {
        marks.AddOrUpdate(c, new NavItem { Id = id, Press = press, Alt = alt, Alt2 = alt2, Focus = focus, Blur = blur, Adjust = adjust });
        return c;
    }

    /// <summary>Kept out of the focus order (a list that moves its own focus).</summary>
    public static T Skip<T>(T c) where T : Control { c.SetMeta("nav_skip", true); return c; }

    /// <summary>A stable name for a button, so focus survives a rebuild.</summary>
    public static T Id<T>(T c, string id) where T : Control { c.SetMeta("nav_id", id); return c; }

    public (Control C, string Id, NavItem? Info)? Current
    {
        get
        {
            foreach (var i in items) if (i.Id == FocusId && GodotObject.IsInstanceValid(i.C) && i.C.IsVisibleInTree()) return i;
            return null;
        }
    }

    /// <summary>The screen was built (again): find what can take focus, put the ring on top.</summary>
    public void Collect()
    {
        items.Clear();
        var seen = new Dictionary<string, int>();
        void Walk(Node n)
        {
            if (n is Control c)
            {
                if (!c.Visible || c.HasMeta("nav_skip")) return;
                if (marks.TryGetValue(c, out var info)) { Add(c, info.Id, info); return; }
                if (c is BaseButton b)
                {
                    string id = b.HasMeta("nav_id") ? (string)b.GetMeta("nav_id") : $"{b.GetType().Name}:{(b as Button)?.Text}";
                    int k = seen.GetValueOrDefault(id);
                    seen[id] = k + 1;
                    Add(b, k > 0 ? $"{id}#{k}" : id, null);
                    return;
                }
            }
            foreach (var ch in n.GetChildren()) Walk(ch);
        }
        Walk(Scope ?? host);
        builtFrame = Engine.GetProcessFrames();
        if (FocusId == null || items.All(i => i.Id != FocusId))
            FocusId = Prefer != null && items.Any(i => i.Id == Prefer) ? Prefer : items.Count > 0 ? items[0].Id : null;
        ring = new Panel { MouseFilter = Control.MouseFilterEnum.Ignore, TopLevel = true, Visible = false, ZIndex = 50 };
        ring.AddThemeStyleboxOverride("panel", Style.FocusFrame());
        host.AddChild(ring);
        if (KeyMode && Current?.Info?.Focus is { } f) f();
    }

    void Add(Control c, string id, NavItem? info)
    {
        items.Add((c, id, info));
        // The pointer moves focus too, so a pad picks up where the mouse left off.
        c.MouseEntered += () => { if (!KeyMode) FocusId = id; };
    }

    /// <summary>An action for focus: true if it was taken.</summary>
    public bool Key(Act a)
    {
        if (!Enabled || items.Count == 0) return false;
        switch (a)
        {
            case Act.Up or Act.Down or Act.Left or Act.Right when Engine.GetProcessFrames() == builtFrame:
                // Built this very frame (the press that switched to the pad redrew it): move once it has its places.
                waiting.Add(a);
                return true;
            case Act.Up or Act.Down or Act.Left or Act.Right:
                if (Current is not { } cur)
                {
                    FocusId = items[0].Id;
                    Show();
                    return true;
                }
                if (a is Act.Left or Act.Right && cur.Info?.Adjust is { } adj && KeyMode) { adj(a == Act.Right ? 1 : -1); return true; }
                // The first press shows where focus is; the next ones move it.
                if (!KeyMode) { Show(); return true; }
                Move(a);
                return true;
            case Act.Confirm:
                if (!KeyMode || Current is not { } c) return false;
                Press(c);
                return true;
            case Act.Alt when Current?.Info?.Alt is { } alt:
                alt();
                return true;
            case Act.Alt2 when Current?.Info?.Alt2 is { } alt2:
                alt2();
                return true;
        }
        return false;
    }

    void Show()
    {
        KeyMode = true;
        if (Current is { } c) { Reveal(c.C); c.Info?.Focus?.Invoke(); }
    }

    static void Press((Control C, string Id, NavItem? Info) c)
    {
        if (c.Info?.Press is { } p) { Sound.Sfx.Click(); p(); return; }
        if (c.C is BaseButton b)
        {
            if (b.Disabled) { Sound.Sfx.Deny(); return; }
            if (b.ToggleMode) b.ButtonPressed = !b.ButtonPressed;
            b.EmitSignal(BaseButton.SignalName.Pressed);
        }
    }

    /// <summary>To the nearest thing in that direction: straight ahead counts
    /// for more than off to the side, and something level with the focus
    /// (sharing its row or column) wins over a nearer one that is not.</summary>
    void Move(Act a)
    {
        if (Current is not { } cur) return;
        if (Nearest(cur, a) is not { } next) { Sound.Sfx.Deny(); return; }
        cur.Info?.Blur?.Invoke();
        FocusId = next.Id;
        Sound.Sfx.Hover();
        Reveal(next.C);
        next.Info?.Focus?.Invoke();
    }

    (Control C, string Id, NavItem? Info)? Nearest((Control C, string Id, NavItem? Info) cur, Act a)
    {
        var dir = a switch { Act.Up => Vector2.Up, Act.Down => Vector2.Down, Act.Left => Vector2.Left, _ => Vector2.Right };
        var from = cur.C.GetGlobalRect();
        var fc = from.GetCenter();
        (Control C, string Id, NavItem? Info)? best = null;
        float bestScore = float.MaxValue;
        foreach (var it in items)
        {
            if (it.Id == cur.Id || !GodotObject.IsInstanceValid(it.C) || !it.C.IsVisibleInTree()) continue;
            var r = it.C.GetGlobalRect();
            var d = r.GetCenter() - fc;
            float along = d.Dot(dir);
            if (along <= 2) continue;
            // Edge to edge along the way, centre to centre across it.
            float gap = dir.X != 0 ? Mathf.Max(0, dir.X > 0 ? r.Position.X - from.End.X : from.Position.X - r.End.X) : Mathf.Max(0, dir.Y > 0 ? r.Position.Y - from.End.Y : from.Position.Y - r.End.Y);
            float across = Mathf.Abs(dir.X != 0 ? d.Y : d.X);
            bool level = dir.X != 0 ? r.Position.Y < from.End.Y && r.End.Y > from.Position.Y : r.Position.X < from.End.X && r.End.X > from.Position.X;
            float score = gap + across * (level ? 0.3f : 2.2f) + (level ? 0 : 40);
            if (score < bestScore) { bestScore = score; best = it; }
        }
        return best;
    }

    /// <summary>
    /// The focus routes walked without a hand on the pad (--navcheck): from
    /// where focus starts, which things the four directions reach, which they
    /// never do, which sit off the screen, and which way back is not the way
    /// out (right then left should come home). A list in a scroll is walked as
    /// laid out, without scrolling.
    /// </summary>
    public List<string> Audit()
    {
        var live = items.Where(i => GodotObject.IsInstanceValid(i.C) && i.C.IsVisibleInTree()).ToList();
        var lines = new List<string>();
        if (live.Count == 0) { lines.Add("no focusable controls"); return lines; }
        var start = Current ?? live[0];
        var dirs = new[] { Act.Up, Act.Down, Act.Left, Act.Right };
        Act Back(Act a) => a switch { Act.Up => Act.Down, Act.Down => Act.Up, Act.Left => Act.Right, _ => Act.Left };
        var reached = new HashSet<string> { start.Id };
        var queue = new Queue<(Control C, string Id, NavItem? Info)>();
        queue.Enqueue(start);
        int oneWay = 0;
        var oneWays = new List<string>();
        var screen = host.GetViewportRect();
        while (queue.Count > 0)
        {
            var at = queue.Dequeue();
            foreach (var d in dirs)
            {
                if (Nearest(at, d) is not { } to) continue;
                if (Nearest(to, Back(d)) is { } home && home.Id != at.Id) { oneWay++; if (oneWays.Count < 6) oneWays.Add($"{at.Id} {d} {to.Id} {Back(d)} {home.Id}"); }
                if (reached.Add(to.Id)) queue.Enqueue(to);
            }
        }
        lines.Add($"{live.Count} focusable, {reached.Count} reached from '{start.Id}', {oneWay} one-way steps");
        foreach (var it in live.Where(i => !reached.Contains(i.Id))) lines.Add($"unreachable: '{it.Id}' at {it.C.GetGlobalRect()}");
        foreach (var it in live.Where(i => !screen.Encloses(i.C.GetGlobalRect()) && !InScroll(i.C))) lines.Add($"off screen: '{it.Id}' at {it.C.GetGlobalRect()}");
        foreach (var it in live.Where(i => i.C.Size.X < 4 || i.C.Size.Y < 4)) lines.Add($"no size: '{it.Id}'");
        foreach (var w in oneWays) lines.Add($"one-way: {w}");
        return lines;
    }

    static bool InScroll(Control c)
    {
        for (Node? n = c.GetParent(); n != null; n = n.GetParent()) if (n is ScrollContainer) return true;
        return false;
    }

    /// <summary>Scrolled into view, if it sits in a scrolling list.</summary>
    static void Reveal(Control c)
    {
        for (Node? n = c.GetParent(); n != null; n = n.GetParent())
            if (n is ScrollContainer s) { s.EnsureControlVisible(c); return; }
    }

    /// <summary>Each frame: the ring on what has focus, breathing a little.</summary>
    public void Update(double delta)
    {
        if (waiting.Count > 0 && Engine.GetProcessFrames() > builtFrame)
        {
            var now = waiting.ToList();
            waiting.Clear();
            foreach (var a in now) Key(a);
        }
        if (ring == null || !GodotObject.IsInstanceValid(ring)) return;
        t += delta;
        var cur = Current;
        ring.Visible = Enabled && KeyMode && cur != null;
        if (!ring.Visible) return;
        // A word set as type (KEEP on Self's ledger) is marked by an ember line under it, not a ring round it.
        bool under = cur!.Value.C.HasMeta("nav_underline");
        if (under != underlined)
        {
            underlined = under;
            ring.AddThemeStyleboxOverride("panel", under ? Underline : Style.FocusFrame());
        }
        var r = under ? cur.Value.C.GetGlobalRect() : cur.Value.C.GetGlobalRect().Grow(4);
        ring.GlobalPosition = under ? new Vector2(r.Position.X, r.End.Y - 1) : r.Position;
        ring.Size = under ? new Vector2(r.Size.X, 3) : r.Size;
        ring.Modulate = Colors.White with { A = 0.8f + 0.2f * Mathf.Sin((float)t * 4) };
    }

    bool underlined;
    static readonly StyleBoxFlat Underline = new() { BgColor = Style.Ember with { A = 0.85f }, ShadowColor = Style.Ember with { A = 0.35f }, ShadowSize = 4 };

    /// <summary>Marked by an ember line under it when it has focus, not a ring: for words set as type.</summary>
    public static T Underlined<T>(T c) where T : Control { c.SetMeta("nav_underline", true); return c; }
}
