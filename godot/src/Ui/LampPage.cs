using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Direction C, "The Day's Book" (docs/design/LAMPS_SCREEN_BRIEF.md §4, §7, §9, §12 C, §16; the mock is
/// tools/uiforge/lamps_mock/mock/frames_c.py and skins/c.py): the Lamps page around the board. Laid out absolutely in the
/// book's content rect, as the mock is (CONTENT (1030, 152)-(1876, 948) at 1080): the header row (the layouts, the
/// count, the keys), the board's window (LampBoard, y 232-874), the wick tabs (centered at y 911) and the prompt row
/// (y 971). Every piece draws its own type (one canvas item each), so the page costs a handful of draw calls.
/// </summary>
public partial class LampPage : Control
{
    /// <summary>The mock's rows, from the content rect's top (y 152 at 1080).</summary>
    public const float HeaderH = 80, BoardTop = 80, BoardH = 642, TabsY = 759, PromptY = 819, Height = 846;

    public readonly LampBoard Board;
    public readonly LampHeader Header;
    public WickTabs Tabs { get; private set; }
    Container prompts;
    readonly LampFind find;
    /// <summary>The wick panel (§8, §16), open over the page's foot when a tab is chosen.</summary>
    public readonly LampWick Wick;
    bool wickOpen, openAtStart;
    int wickTab;
    readonly LampCard coinCard = new();
    readonly CharacterData ch;
    readonly WorldState? w;
    readonly string? zone;
    /// <summary>Open wide (Z, View): phase 5 builds it; the page only calls this.</summary>
    public event Action? OpenWide;

    enum Zone { Board, Header, Tabs, Find, Wick }
    Zone zone_ = Zone.Board;
    int layoutShown;

    /// <summary>A, Open wide (§4, §16): the page over the whole screen, the board across the field (y 84-960), the HUD's
    /// seats its wick tabs (and the keeper's fire the Flare's), the wick panel placed from the HUD's geometry.</summary>
    public readonly bool Wide;
    public Rect2 WickRect;
    /// <summary>A: the field's top and bottom.</summary>
    public const float FieldTop = 84, FieldBottom = 960;

    public LampPage(CharacterData ch, WorldState? w, string? zone, LampSession? visit = null, bool safe = true, bool wide = false, Rect2 wickRect = default, List<Vector2>? seats = null)
    {
        this.ch = ch; this.w = w; this.zone = zone;
        Wide = wide; WickRect = wickRect;
        MouseFilter = MouseFilterEnum.Pass;
        CustomMinimumSize = new Vector2(0, Height);
        SizeFlagsHorizontal = SizeFlags.ExpandFill;
        bool night = w?.Time == TimeOfDay.Night;
        AddChild(Header = new LampHeader(ch, w, zone, wide));
        AddChild(Board = new LampBoard(ch, w) { Wide = wide });
        if (wide) Board.Fe = new Vector4(0, 40, 0, FieldBottom - 900);
        Board.Visit = visit ?? new LampSession(ch);
        Board.Night = night;
        Board.Safe = safe;
        Board.AtPost = !night && LampBook.LayoutsOpen(w, zone);
        AddChild(Wick = new LampWick(ch) { Visible = false, Safe = safe });
        AddChild(Tabs = new WickTabs(ch));
        if (wide) { Wick.SetWide(wickRect.Size); Tabs.SetSeats(seats ?? new()); }
        AddChild(find = new LampFind(ch) { Visible = false });
        AddChild(coinCard);
        prompts = Prompts();
        AddChild(prompts);
        Tabs.Clicked += OpenWick;
        Wick.Picked += sk => { Wick.Open(sk); SetPrompts(); };
        // by night the board is read-only and the night's growth is the wicks: the page opens on the first one
        openAtStart = night;
        layoutShown = LampBook.State(ch).Active;
        Board.LampsChanged += Changed;
        Header.Hovered += i => ShowCoinCard(i, false);
        Header.Picked += (i, right) => Pick(i, right);
        find.Changed += () => Board.SetFound(find.Marked);
        Resized += Lay;
        Lay();
    }

    // (A is sized before it is in the tree, where Resized does not fire: lay out again on entering)
    public override void _Ready() => Lay();

    /// <summary>The visit, for the screen to keep across its pages (the session undo lasts until the book closes).</summary>
    public LampSession Visit => Board.Visit;

    /// <summary>The book's page sits at (1034, 154), 840 wide; C's content rect is (1030, 152), 846 wide: the page
    /// bleeds 4 px left, 2 px right and 2 px up so the board's window lands on the mock's (1030, 232)-(1876, 874).</summary>
    static readonly Vector2 Bleed = new(-4, -2);
    const float Wider = 6;

    void Lay()
    {
        if (Wide) { LayWide(); return; }
        float wd = Size.X + Wider;
        Header.Position = Bleed;
        Header.Size = new Vector2(wd, HeaderH);
        Board.Position = Bleed + new Vector2(0, BoardTop);
        Board.Size = new Vector2(wd, wickOpen ? LampWick.BandTop - BoardTop : BoardH);
        Wick.Position = Bleed + new Vector2(0, LampWick.Top);
        Wick.Size = new Vector2(wd, LampWick.H);
        if (wickOpen) Wick.TabAt = Tabs.Position + Tabs.Centers[Math.Clamp(wickTab, 0, Tabs.Centers.Count - 1)] - Wick.Position;
        Tabs.Position = Bleed + new Vector2(0, TabsY - WickTabs.H / 2);
        Tabs.Size = new Vector2(wd, WickTabs.H);
        find.Position = Bleed + new Vector2(0, HeaderH + 2);
        find.Size = new Vector2(wd, LampFind.H);
        var ps = prompts.GetCombinedMinimumSize();
        prompts.Size = ps;
        prompts.Position = Bleed + new Vector2(Mathf.Round((wd - ps.X) / 2), Mathf.Round(PromptY - ps.Y / 2));
    }

    void LayWide()
    {
        Header.Position = new Vector2(26, 22);
        Header.Size = new Vector2(1920 - 52, 54);
        Board.Position = new Vector2(0, FieldTop);
        if (!wickOpen) Board.Size = new Vector2(1920, FieldBottom - FieldTop);
        Wick.Position = WickRect.Position;
        Wick.Size = WickRect.Size;
        Tabs.Position = Vector2.Zero;
        Tabs.Size = new Vector2(1920, 1080);
        if (wickOpen && Tabs.Count > 0) Wick.TabAt = Tabs.Centers[Math.Clamp(wickTab, 0, Tabs.Count - 1)] - Wick.Position;
        find.Position = new Vector2(560, FieldTop + 2);
        find.Size = new Vector2(800, LampFind.H);
        var ps = prompts.GetCombinedMinimumSize();
        prompts.Size = ps;
        prompts.Position = new Vector2(1900 - ps.X, 1052 - ps.Y);
    }

    void Changed()
    {
        Header.Refresh();
        var st = LampBook.State(ch);
        if (st.Active == layoutShown) { ShowCoinCard(Header.Focused, true); return; }
        // a switch: a new visit (its lamps are another layout's), her carried skills' tabs and Find's chips again
        layoutShown = st.Active;
        Board.Visit = new LampSession(ch);
        RemoveChild(Tabs);
        Tabs.QueueFree();
        AddChild(Tabs = new WickTabs(ch));
        MoveChild(Tabs, 3);
        Tabs.Clicked += OpenWick;
        if (wickOpen) CloseWick();
        find.Rebuild();
        Lay();
        ShowCoinCard(Header.Focused, true);
    }

    /* ------------------------------------------------------------- the wick (§8, §16) -- */

    /// <summary>The foot row (§16, the build lead's input of 2 November): by day the board's, with the wick open the
    /// wick's.</summary>
    Container Prompts()
    {
        bool pad = Pad;
        if (Wide)
        {
            var v = new VBoxContainer { MouseFilter = MouseFilterEnum.Ignore, Alignment = BoxContainer.AlignmentMode.End };
            v.AddThemeConstantOverride("separation", 8);
            var rows = wickOpen
                ? pad ? new[] { new[] { ("A", "Plan") }, new[] { ("Y", "Light my way") }, new[] { ("B", "Back") } }
                      : new[] { new[] { ("Click", "Plan") }, new[] { ("Space", "Light my way") }, new[] { ("Tab", "Back") } }
                : pad ? new[] { new[] { ("LT", ""), ("RT", "Zoom"), ("D-pad", "Next lamp") }, new[] { ("L3", "Home"), ("R3", "The book") } }
                      : new[] { new[] { ("Wheel", "Zoom"), ("F", "Find") }, new[] { ("H", "Home"), ("Z", "The book") } };
            foreach (var r in rows)
            {
                var h = LampInk.Row(r, pad, 15, 16);
                h.Alignment = BoxContainer.AlignmentMode.End;
                v.AddChild(h);
            }
            return v;
        }
        return LampInk.Row(wickOpen
            ? pad ? [("A", "Plan"), ("Y", "Light my way"), ("B", "Board")] : [("Click", "Plan"), ("Space", "Light my way"), ("Tab", "Board")]
            : pad ? [("A", "Light"), ("Y", "Light my way"), ("L3", "Home"), ("R3", "Open wide")]
                  : [("Click", "Light"), ("Space", "Light my way"), ("H", "Home"), ("F", "Find"), ("Z", "Open wide")], pad);
    }

    void SetPrompts()
    {
        RemoveChild(prompts);
        prompts.QueueFree();
        AddChild(prompts = Prompts());
        Lay();
    }

    /// <summary>A wick tab chosen (a click, A on a focused tab, Tab): its wick opens over the page's foot, the board's
    /// window ends at the band and the view slides (and zooms out if it must) to keep her lit cluster in it.</summary>
    public void OpenWick(int i)
    {
        if (Tabs.Count == 0) return;
        i = Math.Clamp(i, 0, Tabs.Count - 1);
        wickTab = i;
        Tabs.Choose(i);
        if (Wide && i >= Tabs.Skills.Count) return;   // (A: the keeper's fire is the Flare's tab: focus only)
        if (i >= Tabs.Skills.Count) Wick.OpenList(); else Wick.Open(Tabs.Skills[i]);
        bool was = wickOpen;
        wickOpen = true;
        zone_ = Zone.Wick;
        Tabs.Focused = -1; Header.Focused = -1;
        Tabs.QueueRedraw(); Header.QueueRedraw();
        coinCard.Visible = false;
        Lay();
        if (!was) Board.Reframe(Wide ? WickRect.Position.Y + 60 - FieldTop : LampWick.BandTop - BoardTop, true);
        SetPrompts();
        Sound.Sfx.Page();
    }

    public void CloseWick()
    {
        if (!wickOpen) return;
        wickOpen = false;
        Wick.Visible = false;
        zone_ = Zone.Board;
        Board.Reframe(Wide ? FieldBottom - FieldTop : BoardH, false);
        SetPrompts();
        Sound.Sfx.Page();
        GD.Print("LAMPBOARD wick closed");
    }

    public bool IsWickOpen => wickOpen;

    /* ------------------------------------------------------------- the coins' card (§9) -- */

    void ShowCoinCard(int i, bool keep)
    {
        if (i is < 0 or > 2) { coinCard.Visible = false; return; }
        var st = LampBook.State(ch);
        var l = st.Layouts[i];
        string road = Lamps.Roads.TryGetValue(l.Type, out var r) ? r.Name : "";
        string type = road.StartsWith("Road of the ") ? "The " + road[12..] : road == "" ? "Not yet walked" : road;
        string flare = Lamps.Flare(l.Flare)?.Name ?? "";
        var glyphs = (l.Carried ?? new()).Where(Weapons.All.ContainsKey).Select(s => (Weapons.All[s].Art, true)).ToList();
        bool open = LampBook.LayoutsOpen(w, zone), pad = Play.Controls.Instance?.UsingPad == true, active = i == st.Active;
        var others = Enumerable.Range(0, 3).Where(k => k != st.Active).ToArray();
        string stateLine = active ? "The layout she walks" : open ? "Take it up: the whole build" : "Layouts change by day at a town’s lamp-post";
        var pr = new List<(string, string)>();
        if (active && open)
        {
            if (pad) { pr.Add(("X", $"Copy to {ArtsScreen.Numerals[others[0]]}")); pr.Add(("Y", $"Copy to {ArtsScreen.Numerals[others[1]]}")); }
            else stateLine = $"Copy to {ArtsScreen.Numerals[others[0]]} / {ArtsScreen.Numerals[others[1]]}: right-click its coin";
        }
        else if (open) { pr.Add(pad ? ("A", "Take it up") : ("Click", "Take it up")); if (!pad) pr.Add(("Right-click", $"Copy {ArtsScreen.Numerals[st.Active]} here")); }
        var t = new LampCardText($"{ArtsScreen.Numerals[i]} · {type}", null, LampInk.Chip, $"{flare} · {l.Lit.Count} lamps", "", glyphs,
            glyphs.Count > 0 ? "Carries " + string.Join(", ", (l.Carried ?? new()).Where(Weapons.All.ContainsKey).Select(s => Weapons.All[s].Name)) : null,
            null, stateLine, active ? LampInk.Gold : open ? LampInk.Gold : LampInk.Gate, null, pr);
        coinCard.Show(t, pad);
        coinCard.Position = Bleed + new Vector2(8, HeaderH - 14);
        coinCard.Visible = true;
    }

    void Pick(int i, bool right)
    {
        var st = LampBook.State(ch);
        if (i <= 2)
        {
            if (right) Copy(i);
            else if (i != st.Active) Board.Switch(i, zone);
            ShowCoinCard(i, true);
        }
        else if (i == 3) Board.LightMyWay();
        else if (i == 4)
        {
            if (find.Visible) { find.Close(); Board.SetFound(null); SetZone(Zone.Board); }
            else { find.Open(!Pad); SetZone(Pad ? Zone.Find : Zone.Board); }
        }
        else OpenWideNow();
    }

    void Copy(int to)
    {
        if (LampAsk.CopyLayout(ch, to, w, zone)) { Sound.Sfx.Pick(); GD.Print($"LAMPBOARD copy {LampBook.State(ch).Active + 1} to {to + 1}"); Header.Refresh(); }
        else Board.Deny("Layouts change by day at a town’s lamp-post");
    }

    void OpenWideNow()
    {
        GD.Print("LAMPBOARD open wide (phase 5)");
        OpenWide?.Invoke();
    }

    /* ------------------------------------------------------------- the pad and the keys (§10) -- */

    static IEnumerable<int> Pads() => Input.GetConnectedJoypads();
    static bool PadHeld(JoyButton b) => Pads().Any(d => Input.IsJoyButtonPressed(d, b));
    static Vector2 PadAxis(JoyAxis x, JoyAxis y)
    {
        var v = Vector2.Zero;
        foreach (var d in Pads()) { var a = new Vector2(Input.GetJoyAxis(d, x), Input.GetJoyAxis(d, y)); if (a.Length() > v.Length()) v = a; }
        return v;
    }
    static bool Pad => Play.Controls.Instance?.UsingPad == true;

    void SetZone(Zone z)
    {
        zone_ = z;
        Header.Focused = z == Zone.Header ? Math.Max(0, Header.Focused < 0 ? LampBook.State(ch).Active : Header.Focused) : -1;
        Tabs.Focused = z == Zone.Tabs ? Math.Max(0, Tabs.Chosen) : -1;
        find.Focused = z == Zone.Find ? Math.Max(0, find.Focused) : -1;
        Header.QueueRedraw(); Tabs.QueueRedraw(); find.QueueRedraw();
        ShowCoinCard(Header.Focused, false);
        Sound.Sfx.Hover();
    }

    /// <summary>An action from the book (ArtsScreen.Key): true when the page took it.</summary>
    public bool Key(Act a)
    {
        if (find.Typing) return true;
        if (wickOpen && WickKey(a) is { } took) return took;
        switch (a)
        {
            case Act.Up or Act.Down or Act.Left or Act.Right:
                // the keys pan and the left stick steps (both polled each frame); the D-pad walks the page's rows
                if (!Pad || PadAxis(JoyAxis.LeftX, JoyAxis.LeftY).Length() > 0.4f) return true;
                Dpad(a);
                return true;
            case Act.Confirm:
                switch (zone_)
                {
                    case Zone.Board: Board.LightFocus(); break;
                    case Zone.Header: Pick(Header.Focused, false); break;
                    case Zone.Tabs: OpenWick(Tabs.Focused); break;
                    case Zone.Find: find.Toggle(find.Focused); break;
                }
                return true;
            case Act.Cancel:
                if (zone_ == Zone.Find || find.Visible) { find.Close(); Board.SetFound(null); SetZone(Zone.Board); return true; }
                if (zone_ != Zone.Board) { SetZone(Zone.Board); return true; }
                if (Wide) { OpenWideNow(); return true; }   // (A: B goes back to the book)
                return false;
            case Act.Alt:
                if (zone_ == Zone.Header && Header.Focused == LampBook.State(ch).Active) { Copy(Enumerable.Range(0, 3).First(k => k != LampBook.State(ch).Active)); return true; }
                if (zone_ == Zone.Board) Board.BeginOut(() => PadHeld(JoyButton.X));
                return true;
            case Act.Alt2:
                if (zone_ == Zone.Header && Header.Focused == LampBook.State(ch).Active) { Copy(Enumerable.Range(0, 3).Last(k => k != LampBook.State(ch).Active)); return true; }
                Board.LightMyWay();
                return true;
            // LB/RB turn the book's tabs (Overlay); LT/RT zoom (as the Map's); L3 Home, R3 Open wide (§16, 2 Nov)
            case Act.TabPrev or Act.TabNext: return Wide;
            case Act.SubPrev or Act.SubNext: Board.ZoomStop(a == Act.SubNext ? 1 : -1); return true;
            case Act.Answer when Pad: Board.Home(); return true;
            case Act.Skip when Pad: OpenWideNow(); return true;
            case Act.Expand: OpenWideNow(); return true;
            case Act.Inventory:
                if (!Pad && Input.IsPhysicalKeyPressed(Godot.Key.Tab)) { OpenWick(wickTab); return true; }
                return false;
            case Act.Dash when !Pad: Board.LightMyWay(); return true;
            case Act.Interact when !Pad && Input.IsPhysicalKeyPressed(Godot.Key.F): find.Open(true); return true;
            case Act.Pick1 or Act.Pick2 or Act.Pick3: Board.Switch(a - Act.Pick1, zone); return true;
        }
        return false;
    }

    /// <summary>The wick open (§8): the arrows and the D-pad walk its nodes, A or Enter plans, Y or Space lays Light my
    /// way's strand, B, Esc or Tab closes it. LB/RB still turn the book, LT/RT still zoom. null: not the wick's.</summary>
    bool? WickKey(Act a)
    {
        switch (a)
        {
            case Act.Up or Act.Down or Act.Left or Act.Right:
                if (Pad && PadAxis(JoyAxis.LeftX, JoyAxis.LeftY).Length() > 0.4f) return true;   // the stick steps in _Process
                Wick.Move(a == Act.Left ? -1 : a == Act.Right ? 1 : 0, a == Act.Up ? -1 : a == Act.Down ? 1 : 0);
                return true;
            case Act.Confirm: Wick.Press(); return true;
            case Act.Alt2: Wick.LightMyWay(); return true;
            case Act.Dash when !Pad: Wick.LightMyWay(); return true;
            case Act.Cancel: CloseWick(); return true;
            case Act.Inventory when !Pad && Input.IsPhysicalKeyPressed(Godot.Key.Tab): CloseWick(); return true;
            case Act.Alt or Act.Pick1 or Act.Pick2 or Act.Pick3 or Act.Answer or Act.Skip: return true;
            case Act.Interact when !Pad: return true;
        }
        return null;
    }

    void Dpad(Act a)
    {
        int dx = a == Act.Left ? -1 : a == Act.Right ? 1 : 0;
        switch (zone_)
        {
            case Zone.Board:
                if (a == Act.Down) SetZone(Zone.Tabs);
                else if (a == Act.Up) SetZone(find.Visible ? Zone.Find : Zone.Header);
                else Board.NextLamp(dx);        // D-pad left/right: the previous or next lamp she can light now
                break;
            case Zone.Header:
                if (a == Act.Down) SetZone(find.Visible ? Zone.Find : Zone.Board);
                else if (dx != 0) { Header.Focused = Math.Clamp(Header.Focused + dx, 0, 5); Header.QueueRedraw(); ShowCoinCard(Header.Focused, false); Sound.Sfx.Hover(); }
                break;
            case Zone.Tabs:
                if (a == Act.Up) { SetZone(Zone.Board); if (Wide) Board.SetFound(null); }
                else if (dx != 0)
                {
                    Tabs.Focused = Math.Clamp(Tabs.Focused + dx, 0, Tabs.Count - 1); Tabs.QueueRedraw(); Sound.Sfx.Hover();
                    // (A: the keeper's fire is the Flare's tab: focused, the Flare's lamps are marked)
                    if (Wide) Board.SetFound(Tabs.Focused == Tabs.Count - 1 ? Board.FlareLamps() : null);
                }
                break;
            case Zone.Find:
                if (a == Act.Down) SetZone(Zone.Board);
                else if (a == Act.Up) SetZone(Zone.Header);
                else if (dx != 0) { find.Focused = Math.Clamp(find.Focused + dx, 0, find.Count - 1); find.QueueRedraw(); Sound.Sfx.Hover(); }
                break;
        }
    }

    /// <summary>Keys no action names (H; Find's typing; Esc out of Find), before the game's input hears them.</summary>
    public override void _Input(InputEvent e)
    {
        if (e is not InputEventKey { Pressed: true } k || !IsVisibleInTree()) return;
        if (find.Typing)
        {
            if (k.PhysicalKeycode == Godot.Key.Escape) { find.Close(); Board.SetFound(null); }
            else if (k.PhysicalKeycode is Godot.Key.Enter or Godot.Key.KpEnter) Board.FocusNext(find.Matches);
            else if (k.PhysicalKeycode == Godot.Key.Backspace) find.Type(null);
            else if (k.Unicode >= 32) find.Type(char.ConvertFromUtf32((int)k.Unicode));
            GetViewport().SetInputAsHandled();
            return;
        }
        if (k.Echo) return;
        if (k.PhysicalKeycode == Godot.Key.H) { Board.Home(); GetViewport().SetInputAsHandled(); }
        else if (k.PhysicalKeycode == Godot.Key.Escape && find.Visible) { find.Close(); Board.SetFound(null); SetZone(Zone.Board); GetViewport().SetInputAsHandled(); }
    }

    // the left stick: a step on the push, then after 0.32 s at 7 a second; the right stick and the keys pan
    double stickT, stickNext;
    double? stickAngle;
    bool panning;
    // --lamps-moves: a scripted hand for the shots and the report (pad moves by name, 0.35 s apart)
    string[]? moves;
    int moveI;
    double moveT = 2.5;

    public override void _Process(double delta)
    {
        if (!IsVisibleInTree()) return;
        if (openAtStart && Board.Size.X > 8 && Tabs.Count > 0) { openAtStart = false; OpenWick(0); }
        Script(delta);
        if (find.Typing) return;
        var ls = PadAxis(JoyAxis.LeftX, JoyAxis.LeftY);
        if ((zone_ == Zone.Board || zone_ == Zone.Wick) && ls.Length() > 0.5f)
        {
            double ang = Math.Atan2(ls.Y, ls.X);
            if (stickAngle is not { } held || Math.Abs(Math.IEEERemainder(ang - held, 2 * Math.PI)) > 35 * Math.PI / 180)
            {
                stickAngle = ang; stickT = 0; stickNext = 0.32;
                StickStep(ang);
            }
            else
            {
                stickT += delta;
                if (stickT >= stickNext) { stickNext += 1.0 / 7; stickAngle = ang; StickStep(ang); }
            }
        }
        else stickAngle = null;
        if (wickOpen) return;
        var rs = PadAxis(JoyAxis.RightX, JoyAxis.RightY);
        float m = rs.Length();
        if (m > 0.2f)
        {
            // up to 1400 board units a second, eased in from the dead zone
            float k = Mathf.Pow(Mathf.Min(1, (m - 0.2f) / 0.75f), 1.6f);
            Board.PanBy(-rs / m * k * 1400f * (float)Board.View.S * (float)delta);
            panning = true;
        }
        else if (panning) { panning = false; Board.PanReleased(); }
        var kd = Vector2.Zero;
        if (Input.IsPhysicalKeyPressed(Godot.Key.A) || Input.IsPhysicalKeyPressed(Godot.Key.Left)) kd.X -= 1;
        if (Input.IsPhysicalKeyPressed(Godot.Key.D) || Input.IsPhysicalKeyPressed(Godot.Key.Right)) kd.X += 1;
        if (Input.IsPhysicalKeyPressed(Godot.Key.W) || Input.IsPhysicalKeyPressed(Godot.Key.Up)) kd.Y -= 1;
        if (Input.IsPhysicalKeyPressed(Godot.Key.S) || Input.IsPhysicalKeyPressed(Godot.Key.Down)) kd.Y += 1;
        if (kd != Vector2.Zero) Board.PanBy(-kd.Normalized() * 760f * (float)delta);
    }

    /// <summary>The left stick's step: on the board §10's, in the wick its rows and pitch (the nearest of four ways).</summary>
    void StickStep(double ang)
    {
        if (!wickOpen) { Board.Step(ang); return; }
        double c = Math.Cos(ang), sn = Math.Sin(ang);
        if (Math.Abs(c) >= Math.Abs(sn)) Wick.Move(c > 0 ? 1 : -1, 0); else Wick.Move(0, sn > 0 ? 1 : -1);
    }

    // --lamps-moves' real hand: pending checks and releases (time left, what to do)
    readonly List<(double T, Action Do)> later = new();
    Vector2 pointer = new(-1, -1);
    string? lastClicked;

    static void Send(InputEvent e) => Input.ParseInputEvent(e);

    void MouseTo(Vector2 at)
    {
        pointer = at;
        Send(new InputEventMouseMotion { Position = at, GlobalPosition = at });
    }

    void MouseButtonAt(Vector2 at, MouseButton b, bool down)
    {
        Send(new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = b, Pressed = down,
            ButtonMask = down ? (MouseButtonMask)(1 << ((int)b - 1)) : 0, Factor = 1 });
    }

    void KeyTap(Key k)
    {
        Send(new InputEventKey { PhysicalKeycode = k, Keycode = k, Pressed = true });
        later.Add((0.08, () => Send(new InputEventKey { PhysicalKeycode = k, Keycode = k, Pressed = false })));
    }

    void PadTap(JoyButton b, double hold = 0.08)
    {
        Send(new InputEventJoypadButton { ButtonIndex = b, Pressed = true, Device = 0 });
        later.Add((hold, () => Send(new InputEventJoypadButton { ButtonIndex = b, Pressed = false, Device = 0 })));
    }

    static void Said(string mv, bool ok, string what) => GD.Print($"LAMPBOARD move {mv} {(ok ? "ok" : "no")}: {what}");

    /// <summary>A real-input token (Input.ParseInputEvent, through the game's own routing): click@id, rhold@id, wheel+,
    /// wheel-, drag:dx,dy, key:Name, pad:Button, xhold. False: not one.</summary>
    bool RealMove(string mv)
    {
        if (mv.StartsWith("click@") || mv.StartsWith("rhold@"))
        {
            string id = mv[6..] != "focus" ? mv[6..] : lastClicked ?? (Board.Focus >= 0 ? LampBoard.M.Nodes[Board.Focus].Id : "");
            if (mv[0] == 'c') lastClicked = id;
            if (Board.ScreenOf(id) is not { } at) { Said(mv, false, "the lamp is off the window"); return true; }
            bool was = LampBook.IsLit(ch, id);
            MouseTo(at);
            if (mv[0] == 'c')
            {
                MouseButtonAt(at, MouseButton.Left, true);
                MouseButtonAt(at, MouseButton.Left, false);
                later.Add((0.05, () => Said(mv, !was && LampBook.IsLit(ch, id), $"{id} was {(was ? "lit" : "unlit")}, now {(LampBook.IsLit(ch, id) ? "lit" : "unlit")}, spare {LampBook.Spare(ch, w)}")));
            }
            else
            {
                MouseButtonAt(at, MouseButton.Right, true);
                later.Add((1.4, () =>
                {
                    MouseButtonAt(at, MouseButton.Right, false);
                    Said(mv, was && !LampBook.IsLit(ch, id), $"{id} was {(was ? "lit" : "unlit")}, now {(LampBook.IsLit(ch, id) ? "lit" : "unlit")}{(Board.Said is { } why ? $" ({why})" : "")}");
                }));
            }
            return true;
        }
        if (mv is "wheel+" or "wheel-")
        {
            var at = pointer.X >= 0 ? pointer : Board.GetGlobalRect().GetCenter() + new Vector2(120, -60);
            MouseTo(at);
            var before = Board.BoardAt(at);
            double s0 = Board.View.S;
            var b = mv == "wheel+" ? MouseButton.WheelUp : MouseButton.WheelDown;
            MouseButtonAt(at, b, true);
            MouseButtonAt(at, b, false);
            later.Add((0.3, () =>
            {
                var after = Board.BoardAt(at);
                double drift = Math.Sqrt((after.X - before.X) * (after.X - before.X) + (after.Y - before.Y) * (after.Y - before.Y)) * Board.View.S;
                Said(mv, Math.Abs(Board.View.S - s0) > 1e-4 && drift < 2, $"scale {s0:F3} to {Board.View.S:F3}, the point under the cursor drifted {drift:F2} px");
            }));
            return true;
        }
        if (mv.StartsWith("drag:"))
        {
            var d = mv[5..].Split(';', ':', '/');
            var dv = new Vector2(float.Parse(d[0], System.Globalization.CultureInfo.InvariantCulture), float.Parse(d[1], System.Globalization.CultureInfo.InvariantCulture));
            var from = Board.EmptyNear(Board.Size / 2);
            var c0 = (Board.View.Cx, Board.View.Cy);
            MouseTo(from);
            MouseButtonAt(from, MouseButton.Left, true);
            // (motion is accumulated per frame: one step a frame, the release after)
            for (int k = 1; k <= 6; k++) { var to = from + dv * k / 6f; later.Add((0.034 * k, () => MouseTo(to))); }
            later.Add((0.26, () => MouseButtonAt(from + dv, MouseButton.Left, false)));
            later.Add((0.32, () =>
            {
                double mx = (c0.Item1 - Board.View.Cx) * Board.View.S, my = (Board.View.Cy - c0.Item2) * Board.View.S;
                Said(mv, Math.Abs(mx - dv.X) < 3 && Math.Abs(my - dv.Y) < 3, $"the board moved {mx:F1},{my:F1} px for a drag of {dv.X:F0},{dv.Y:F0}");
            }));
            return true;
        }
        if (mv.StartsWith("key:"))
        {
            if (!Enum.TryParse<Key>(mv[4..], true, out var k)) { Said(mv, false, "no such key"); return true; }
            KeyTap(k);
            later.Add((0.1, () => Said(mv, true, $"wick {(wickOpen ? $"open, focus {Wick.FocusId}, plan {Wick.PlanCount}" : "closed")}, board focus {(Board.Focus >= 0 ? LampBoard.M.Nodes[Board.Focus].Id : "-")}, scale {Board.View.S:F3}")));
            return true;
        }
        if (mv.StartsWith("pad:"))
        {
            if (!Enum.TryParse<JoyButton>(mv[4..], true, out var jb)) { Said(mv, false, "no such button"); return true; }
            PadTap(jb);
            later.Add((0.1, () => Said(mv, true, $"wick {(wickOpen ? $"open, focus {Wick.FocusId}, plan {Wick.PlanCount}" : "closed")}, board focus {(Board.Focus >= 0 ? LampBoard.M.Nodes[Board.Focus].Id : "-")}")));
            return true;
        }
        if (mv == "xhold")
        {
            string? id = Board.Focus >= 0 ? LampBoard.M.Nodes[Board.Focus].Id : null;
            bool was = id != null && LampBook.IsLit(ch, id);
            PadTap(JoyButton.X, 1.4);
            later.Add((1.5, () => Said(mv, id != null && was && !LampBook.IsLit(ch, id), $"{id ?? "-"} was {(was ? "lit" : "unlit")}, now {(id != null && LampBook.IsLit(ch, id) ? "lit" : "unlit")}{(Board.Said is { } why ? $" ({why})" : "")}")));
            return true;
        }
        return false;
    }

    void Script(double dt)
    {
        for (int k = later.Count - 1; k >= 0; k--)
        {
            var (t, act) = later[k];
            if ((t -= dt) <= 0) { later.RemoveAt(k); act(); } else later[k] = (t, act);
        }
        moves ??= SurvivorUnchained.Args.Get("lamps-moves")?.Split(',') ?? [];
        if (moveI >= moves.Length) return;
        moveT -= dt;
        if (moveT > 0) return;
        moveT = 0.35;
        var mv = moves[moveI++];
        if (RealMove(mv)) { if (mv.StartsWith("rhold@") || mv == "xhold") moveT = 1.7; return; }
        double? ang = mv switch { "R" => 0, "DR" => Math.PI / 4, "D" => Math.PI / 2, "DL" => 3 * Math.PI / 4, "L" => Math.PI, "UL" => -3 * Math.PI / 4, "U" => -Math.PI / 2, "UR" => -Math.PI / 4, _ => null };
        if (ang is { } a) StickStep(a);
        else switch (mv)
        {
            case "in": Board.ZoomStop(1); break;
            case "out": Board.ZoomStop(-1); break;
            case "home": Board.Home(); break;
            case "next": Board.NextLamp(1); break;
            case "light": Board.LightFocus(); break;
            case "lmw": Board.LightMyWay(); break;
            case "find": find.Open(false); SetZone(Zone.Find); find.Toggle(0); break;
            case "wait": moveT = 1; break;
            case "wick": OpenWick(wickTab); break;
        }
        GD.Print($"LAMPBOARD move {mv}: focus {(Board.Focus >= 0 ? LampBoard.M.Nodes[Board.Focus].Id : "-")}, scale {Board.View.S:F3}, worst focus {Board.WorstFocusMs:F2} ms");
    }
}

/// <summary>
/// Find (§10, L3 or F): a row of chips under the header (her carried skills, the schools, blue lamps, links, rites, the
/// Flare); the chosen chip marks the lamps it feeds (§6 Found). With F the keys type a filter (a lamp's name, its line,
/// its kind or the skills it feeds) and Enter steps through the matches.
/// </summary>
public partial class LampFind : Control
{
    public const float H = 30;
    readonly CharacterData ch;
    readonly List<(string Word, string? Glyph, HashSet<int> Lamps)> chips = new();
    int chosen = -1;
    string typed = "";
    public int Focused = -1;
    public bool Typing { get; private set; }
    public int Count => chips.Count;
    public event Action? Changed;
    /// <summary>The marked lamps (null: none), and as a list in board order (Enter's steps).</summary>
    public HashSet<int>? Marked { get; private set; }
    public List<int> Matches { get; private set; } = new();

    public LampFind(CharacterData ch) { this.ch = ch; MouseFilter = MouseFilterEnum.Pass; Rebuild(); }

    public void Rebuild()
    {
        chips.Clear();
        var m = LampBoard.M;
        HashSet<int> Where(Func<LampDef, LampBoardModel.Node, bool> f) =>
            m.Nodes.Where(nd => Lamps.Find(nd.Id) is { } d && f(d, nd)).Select(nd => nd.I).ToHashSet();
        var carried = SkillBook.Carried(ch).Select(c => c.Id).Where(Weapons.All.ContainsKey).ToList();
        foreach (var s in carried) chips.Add((Weapons.All[s].Name, Weapons.All[s].Art, Where((d, _) => d.Feeds.Contains(s))));
        foreach (var school in carried.Select(s => Weapons.All[s].School).Distinct())
            chips.Add((Style.Cap1(school.ToString()), null, Where((d, _) => d.Feeds.Any(f => Weapons.All.TryGetValue(f, out var wd) && wd.School == school))));
        chips.Add(("Blue lamps", null, Where((_, nd) => nd.Kind == "blue")));
        chips.Add(("Links", null, Where((_, nd) => nd.Kind == "link")));
        chips.Add(("Rites", null, Where((_, nd) => nd.Kind == "rite")));
        chips.Add(("The Flare", null, Where((_, nd) => nd.Kind is "ultimate" or "ultimateMod" or "flareLamp")));
        chosen = -1;
        Mark();
    }

    public void Open(bool typing)
    {
        Visible = true;
        Typing = typing;
        if (typing) { chosen = -1; Mark(); }
        QueueRedraw();
    }

    public void Close()
    {
        Visible = false; Typing = false; chosen = -1; typed = ""; Focused = -1;
        Marked = null; Matches = new();
        QueueRedraw();
    }

    public void Toggle(int i)
    {
        if (i < 0 || i >= chips.Count) return;
        chosen = chosen == i ? -1 : i;
        typed = ""; Typing = false;
        Sound.Sfx.Click();
        Mark();
    }

    public void Type(string? s)
    {
        typed = s == null ? typed.Length > 0 ? typed[..^1] : "" : typed + s;
        chosen = -1;
        Mark();
    }

    void Mark()
    {
        var m = LampBoard.M;
        if (chosen >= 0) Marked = chips[chosen].Lamps;
        else if (typed.Trim().Length >= 2)
        {
            var q = typed.Trim().ToLowerInvariant();
            Marked = m.Nodes.Where(nd => Lamps.Find(nd.Id) is { } d && (d.Name.ToLowerInvariant().Contains(q) || d.Text.ToLowerInvariant().Contains(q)
                || nd.Kind.ToLowerInvariant().Contains(q) || d.Feeds.Any(f => Weapons.All.TryGetValue(f, out var wd) && wd.Name.ToLowerInvariant().Contains(q))))
                .Select(nd => nd.I).ToHashSet();
        }
        else Marked = null;
        Matches = Marked?.OrderBy(i => i).ToList() ?? new();
        QueueRedraw();
        Changed?.Invoke();
    }

    readonly List<Rect2> rects = new();

    public override void _GuiInput(InputEvent e)
    {
        if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left } mb)
            for (int i = 0; i < rects.Count; i++) if (rects[i].HasPoint(mb.Position)) { Toggle(i); AcceptEvent(); return; }
    }

    public override void _Draw()
    {
        rects.Clear();
        var f = Style.Ui;
        const int Px = 14;
        float x = 16, cy = H / 2;
        if (Typing || typed != "")
        {
            string t = $"Find: {typed}{(Typing ? "|" : "")}";
            LampInk.Text(this, LampInk.F("alegreya-400-italic"), 15, x, cy + 5, t, LampInk.Gold);
            x += LampInk.W(LampInk.F("alegreya-400-italic"), t, 15) + 10;
            if (Marked != null) { var c = $"{Marked.Count} found · Enter steps"; LampInk.Text(this, f, 13, x, cy + 5, c, LampInk.Dim); x += LampInk.W(f, c, 13) + 18; }
        }
        for (int i = 0; i < chips.Count; i++)
        {
            var (word, glyph, set) = chips[i];
            float tw = LampInk.W(f, word, Px), gw = glyph != null ? 18 : 0;
            var r = new Rect2(x, cy - 11, tw + gw + 18, 22);
            if (r.End.X > Size.X - 12) break;
            bool on = i == chosen;
            DrawStyleBox(new StyleBoxFlat { BgColor = new Color("#0d1015") with { A = on ? 0.9f : 0.6f }, BorderColor = on ? LampInk.Gold : LampInk.RimGold with { A = 0.45f },
                BorderWidthBottom = 1, BorderWidthTop = 1, BorderWidthLeft = 1, BorderWidthRight = 1, CornerRadiusBottomLeft = 11, CornerRadiusBottomRight = 11,
                CornerRadiusTopLeft = 11, CornerRadiusTopRight = 11, AntiAliasing = true }, r);
            if (i == Focused) DrawStyleBox(new StyleBoxFlat { BgColor = Colors.Transparent, BorderColor = new Color("#fff2cf"), BorderWidthBottom = 2, BorderWidthTop = 2,
                BorderWidthLeft = 2, BorderWidthRight = 2, CornerRadiusBottomLeft = 13, CornerRadiusBottomRight = 13, CornerRadiusTopLeft = 13, CornerRadiusTopRight = 13,
                AntiAliasing = true }, r.Grow(3));
            if (glyph != null) DrawTextureRect(Glyphs.Texture(glyph, 32, Colors.White, line: true), new Rect2(x + 8, cy - 8, 16, 16), false, on ? LampInk.Gold : LampInk.Body);
            LampInk.Text(this, f, Px, x + 9 + gw, cy + 5, word, on ? LampInk.Gold : LampInk.Body with { A = 0.9f });
            rects.Add(r);
            x = r.End.X + 8;
        }
    }
}

/// <summary>The page's type and colors (skins/a.py's), and drawing helpers for one-canvas-item controls.</summary>
public static class LampInk
{
    public static readonly Color Ink = new("#efe4cc"), Body = new("#d8cfbd"), Dim = new("#9b9282"), Gold = new("#e9c27a"),
        RimGold = new("#cdae72"), Red = new("#e0705a"), Cobalt = new("#8fb0ff"), Fire = new("#ff9a52"), Focus = new("#e8c87a"),
        Post = new("#e8b36a"), Dark = new("#07080b"), Gate = new("#c9a46a"), Chip = new("#d9c08a");

    static readonly Dictionary<string, Font> fonts = new();
    /// <summary>A house font (art/fonts/name.woff2), letterspaced by track px when asked.</summary>
    public static Font F(string name, int track = 0)
    {
        var key = $"{name}/{track}";
        if (fonts.TryGetValue(key, out var f)) return f;
        Font b = GD.Load<Font>($"res://art/fonts/{name}.woff2");
        return fonts[key] = track == 0 ? b : new FontVariation { BaseFont = b, SpacingGlyph = track };
    }

    public static float W(Font f, string s, int px) => f.GetStringSize(s, HorizontalAlignment.Left, -1, px).X;

    /// <summary>Text with its baseline at (x, y); align -1 left, 0 center, 1 right. Returns the advance.</summary>
    public static float Text(CanvasItem ci, Font f, int px, float x, float y, string s, Color c, int align = -1, float halo = 0, float haloA = 0.7f)
    {
        float w = W(f, s, px);
        float x0 = Mathf.Round(align < 0 ? x : align == 0 ? x - w / 2 : x - w);
        var at = new Vector2(x0, Mathf.Round(y));
        if (halo > 0)
        {
            ci.DrawStringOutline(f, at, s, HorizontalAlignment.Left, -1, px, (int)(halo * 2), Dark with { A = haloA * 0.45f * c.A });
            ci.DrawStringOutline(f, at, s, HorizontalAlignment.Left, -1, px, (int)halo, Dark with { A = haloA * c.A });
        }
        ci.DrawString(f, at, s, HorizontalAlignment.Left, -1, px, c);
        return w;
    }

    /// <summary>The house's rule: 1 px gold at 28%, its ends faded over 30 px.</summary>
    public static void Rule(CanvasItem ci, float x0, float x1, float y, float a = 0.28f)
    {
        var c = RimGold with { A = a };
        var z = RimGold with { A = 0 };
        y += 0.5f;
        ci.DrawPolylineColors([new(x0, y), new(x0 + 30, y), new(x1 - 30, y), new(x1, y)], [z, c, c, z], 1f, true);
    }

    /// <summary>Words broken greedily to fit maxw.</summary>
    public static List<string> Wrap(string s, Font f, int px, float maxw)
    {
        var lines = new List<string>();
        var cur = "";
        // (a number keeps its unit: "3 m", "10 s", "5 %" never break)
        s = System.Text.RegularExpressions.Regex.Replace(s, @"(\d) (m|s|%|px)\b", "$1\u00a0$2");
        foreach (var word in s.Split(' ', StringSplitOptions.RemoveEmptyEntries))
        {
            var t = cur == "" ? word : cur + " " + word;
            if (cur == "" || W(f, t, px) <= maxw) cur = t;
            else { lines.Add(cur); cur = word; }
        }
        if (cur != "") lines.Add(cur);
        return lines;
    }

    /// <summary>A key cap as the device in hand has it: a pad button's art, else the book's key cap.</summary>
    public static Control Cap(string key, bool pad) =>
        pad && key is "A" or "B" or "X" or "Y" or "LB" or "RB" or "LT" or "RT" or "View" or "Menu" or "L3" or "R3" or "D-pad down" or "D-pad up" or "D-pad"
            ? Style.PadButton(key) : Style.Key(key);

    /// <summary>The book's prompt row: each cap, then its word (Alegreya Sans 16), 32 px between.</summary>
    public static HBoxContainer Row(IEnumerable<(string Key, string Word)> items, bool pad, int size = 16, int sep = 32)
    {
        var h = Style.H(sep);
        h.MouseFilter = Control.MouseFilterEnum.Ignore;
        foreach (var (k, wd) in items)
        {
            var one = Style.H(9, Cap(k, pad), Style.Label(wd, Style.Ui, size, Body with { A = 0.95f }, false, HorizontalAlignment.Left, false));
            one.Alignment = BoxContainer.AlignmentMode.Center;
            h.AddChild(one);
        }
        return h;
    }
}

/// <summary>
/// The header row (§4, §9, §12 C; skins/c.py header()): left, the three layout coins (32 px, I II III, the active one
/// lit) and the layout's name (Alegreya 700 17, her type's: "The Sunderer"); center, "3 LAMPS TO LIGHT" (Cinzel 700 30
/// and 600 16 letterspaced, warm gold), under it what was earned (Alegreya Sans 14, dim) and by day at a town's
/// lamp-post the warm italic line (by night, the board is read-only); right, Light my way and Open wide with their caps.
/// </summary>
public partial class LampHeader : Control
{
    int count, active;
    string sub = "", name = "";
    string? post, night;
    readonly HBoxContainer keys;
    readonly CharacterData ch;
    readonly WorldState? w;
    readonly string? zone;
    /// <summary>The pad's focus in the header (0-2 the coins, 3 Light my way, 4 Find, 5 Open wide; -1 none).</summary>
    public int Focused = -1;
    /// <summary>The mouse over an item (-1 none), and a click on one (the right button: true).</summary>
    public event Action<int>? Hovered;
    public event Action<int, bool>? Picked;
    int hover = -1;

    public LampHeader(CharacterData ch, WorldState? w, string? zone, bool wide = false)
    {
        this.ch = ch; this.w = w; this.zone = zone;
        MouseFilter = MouseFilterEnum.Pass;
        bool pad = Play.Controls.Instance?.UsingPad == true;
        // (A: Light my way and Find; the way back to the book is in the lower right)
        if (wide) keys = LampInk.Row(pad ? [("Y", "Light my way"), ("D-pad up", "Find")] : [("Space", "Light my way"), ("F", "Find")], pad, 16, 22);
        else keys = LampInk.Row(pad ? [("Y", "Light my way"), ("D-pad up", "Find"), ("R3", "Open wide")] : [("Space", "Light my way"), ("F", "Find"), ("Z", "Open wide")], pad, 16, 22);
        AddChild(keys);
        Resized += Lay;
        Refresh();
    }

    public override void _Ready() => Lay();

    /// <summary>The count, the layout and the lines again (after a light, a put out, a switch).</summary>
    public void Refresh()
    {
        count = Math.Max(0, LampBook.Spare(ch, w));
        var st = LampBook.State(ch);
        active = st.Active;
        var type = LampBook.Now(ch).Type;
        var road = Lamps.Roads.TryGetValue(type, out var r) ? r.Name : "";
        name = road.StartsWith("Road of the ") ? "The " + road[12..] : road;
        int lit = LampBook.Now(ch).Lit.Count, levels = Math.Max(0, ch.Level - 1), story = LampBook.StoryLamps(w),
            atlas = LampBook.AtlasLit(w), posts = LampBook.PostLamps(w);
        var parts = new List<string> { $"{levels} from levels" };
        if (story > 0) parts.Add($"{story} from the story");
        if (atlas > 0) parts.Add($"{atlas} from the atlas");
        if (posts > 0) parts.Add($"{posts} from the lamp-posts");
        sub = $"{lit} lit  ·  {string.Join(", ", parts)}";
        bool isNight = w?.Time == TimeOfDay.Night;
        if (isNight) night = "By night the board is read-only";
        else if (LampBook.LayoutsOpen(w, zone))
            post = $"At the {Style.Cap1(zone ?? "")}’s lamp-post: lamps go out free";
        else post = null;
        QueueRedraw();
    }

    /// <summary>An item's rect (the coins, then the two keys).</summary>
    public Rect2 ItemRect(int i)
    {
        if (i < 3) return new Rect2(new Vector2(16 + i * 40 - 18, Ccy - 18), new Vector2(36, 36));
        var kids = keys.GetChildren();
        if (kids.Count <= i - 3 || kids[i - 3] is not Control k) return new Rect2();
        return new Rect2(keys.Position + k.Position - new Vector2(6, 4), k.Size + new Vector2(12, 8));
    }

    public override void _GuiInput(InputEvent e)
    {
        int At(Vector2 p) { for (int i = 0; i < 6; i++) if (ItemRect(i).HasPoint(p)) return i; return -1; }
        if (e is InputEventMouseMotion mm && At(mm.Position) is var h && h != hover) { hover = h; Hovered?.Invoke(h); }
        if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left or MouseButton.Right } mb && At(mb.Position) is >= 0 and var k)
        {
            Picked?.Invoke(k, mb.ButtonIndex == MouseButton.Right);
            AcceptEvent();
        }
    }

    const float Yb = 28;            // the count's baseline (skins/c.py: y0 + 28)
    float Ccy => Yb - 9;            // the coins' and keys' middle

    void Lay()
    {
        var s = keys.GetCombinedMinimumSize();
        keys.Size = s;
        keys.Position = new Vector2(Mathf.Round(Size.X - s.X), Mathf.Round(Ccy - s.Y / 2));
        QueueRedraw();
    }

    public override void _Draw()
    {
        var fnum = LampInk.F("cinzel-700");
        var fw = LampInk.F("cinzel-600", 3);
        string num = count.ToString(), words = count == 1 ? "LAMP TO LIGHT" : "LAMPS TO LIGHT";
        float wn = LampInk.W(fnum, num, 30), ww = LampInk.W(fw, words, 16) - 3;
        // the count centered on the row; where the keys reach it (C on a pad: three keys), it moves left to clear them
        // by 24 px, never past the layout's name
        float wc = wn + 10 + ww, nameR = 16 + 2 * 40 + 28 + LampInk.W(LampInk.F("alegreya-700"), name, 17) + 32;
        float xs = Mathf.Max(nameR, Mathf.Min(Size.X / 2 - wc / 2, keys.Position.X - 24 - wc));
        float cx = xs + wc / 2;
        LampInk.Text(this, fnum, 30, xs, Yb, num, LampInk.Gold);
        LampInk.Text(this, fw, 16, xs + wn + 10, Yb - 1, words, LampInk.Gold with { A = 0.95f });
        LampInk.Text(this, LampInk.F("alegreya-sans-400"), 14, cx, Yb + 19, sub, LampInk.Dim, 0);
        if (post != null) LampInk.Text(this, LampInk.F("alegreya-400-italic"), 15, cx, Yb + 38, post, LampInk.Post with { A = 0.95f }, 0);
        if (night != null) LampInk.Text(this, LampInk.F("alegreya-400-italic"), 15, cx, Yb + 38, night, LampInk.Dim with { A = 0.85f }, 0);
        for (int i = 0; i < 3; i++) Coin(this, new Vector2(16 + i * 40, Ccy), ArtsScreen.Numerals[i], i == active);
        LampInk.Text(this, LampInk.F("alegreya-700"), 17, 16 + 2 * 40 + 28, Ccy + 6, name, LampInk.Ink with { A = 0.95f });
        int f = Focused >= 0 ? Focused : hover;
        if (f >= 0)
        {
            var r = ItemRect(f);
            var col = LampInk.Focus with { A = Focused >= 0 ? 1f : 0.6f };
            if (f < 3) DrawArc(r.GetCenter(), 20, 0, Mathf.Tau, 64, col, 1.5f, true);
            else DrawStyleBox(new StyleBoxFlat { BgColor = Colors.Transparent, BorderColor = col, CornerDetail = 6, AntiAliasing = true,
                BorderWidthBottom = 1, BorderWidthTop = 1, BorderWidthLeft = 1, BorderWidthRight = 1, CornerRadiusBottomLeft = 4,
                CornerRadiusBottomRight = 4, CornerRadiusTopLeft = 4, CornerRadiusTopRight = 4 }, r);
        }
    }

    /// <summary>A layout coin (skins/a.py coin()): bronze, 32 px; the active one lit, its numeral warm.</summary>
    public static void Coin(CanvasItem ci, Vector2 c, string numeral, bool on)
    {
        const float R = 16;
        if (on)
        {
            for (int k = 6; k >= 1; k--) ci.DrawCircle(c, R + k * 2.2f, new Color("#ffb04a") with { A = 0.022f }, true, -1, true);
            ci.DrawCircle(c, R, new Color("#2c2112"), true, -1, true);
            ci.DrawCircle(c + new Vector2(-3, -4), R * 0.62f, new Color("#5b4526") with { A = 0.55f }, true, -1, true);
            ci.DrawArc(c, R - 0.9f, 0, Mathf.Tau, 64, new Color("#e8c27a"), 1.8f, true);
            ci.DrawArc(c, R - 3.2f, 0, Mathf.Tau, 64, new Color("#a8823e") with { A = 0.6f }, 0.8f, true);
        }
        else
        {
            ci.DrawCircle(c, R, new Color("#1a150d") with { A = 0.92f }, true, -1, true);
            ci.DrawCircle(c + new Vector2(-3, -4), R * 0.6f, new Color("#2d2418") with { A = 0.5f }, true, -1, true);
            ci.DrawArc(c, R - 0.6f, 0, Mathf.Tau, 64, new Color("#6b5532") with { A = 0.85f }, 1.2f, true);
        }
        LampInk.Text(ci, LampInk.F("cinzel-700"), 14, c.X + 0.5f, c.Y + 5, numeral, on ? new Color("#ffe2a6") : new Color("#7d6a4c"), 0);
    }
}

/// <summary>
/// The wick tabs (§12 C, §16; skins/c.py tabs()): "WICKS" in small caps, her carried skills as the HUD's own seats
/// (its bronze ring and river-glass well with the skill's gold inlay, at 56 px), a hairline, then "All learned". The
/// chosen tab wears the gold ring. Choosing opens the wick panel (phase 4); here it only moves the choice.
/// </summary>
public partial class WickTabs : Control
{
    public const float H = 64, D = 56, Pitch = 70;
    public int Chosen { get; private set; }
    /// <summary>The pad's focus on a tab (-1: the focus is elsewhere).</summary>
    public int Focused = -1;
    public int Count => Centers.Count;
    public event Action<int>? ChosenChanged;
    /// <summary>A tab clicked (its wick opens, chosen or not).</summary>
    public event Action<int>? Clicked;
    readonly List<(string Id, string Art, Color School)> seats = new();
    /// <summary>The carried skills' ids, in tab order (the last tab is All learned).</summary>
    public IReadOnlyList<string> Skills => seats.Select(s => s.Id).ToList();
    readonly GlyphMark scroll = new("scroll", 24, new Color("#d6c4a0") with { A = 0.85f });
    readonly Control row = new() { MouseFilter = MouseFilterEnum.Ignore };
    float lead, allX;
    const string Lead = "WICKS", All = "All learned";
    /// <summary>The tab centers in this control (the wick stem rises from these in phase 4).</summary>
    public readonly List<Vector2> Centers = new();

    public WickTabs(CharacterData ch)
    {
        MouseFilter = MouseFilterEnum.Pass;
        AddChild(row);
        int i = 0;
        foreach (var (id, _) in SkillBook.Carried(ch))
        {
            if (!Weapons.All.TryGetValue(id, out var wd) || i >= 6) continue;
            seats.Add((id, wd.Art, ItemViews.SchoolColors[wd.School]));
            i++;
        }
        row.AddChild(scroll);
        Resized += Lay;
    }

    /// <summary>The HUD seat's bezel (36.6 px out) to the tab's 56 px.</summary>
    static float K => D / (2 * 36.6f);

    float Total(out float ldw, out float lw)
    {
        ldw = LampInk.W(LampInk.F("alegreya-sans-700", 2), Lead, 13) - 2;
        lw = LampInk.W(Style.Ui, All, 15);
        int n = seats.Count;
        return ldw + 20 + n * D + Math.Max(0, n - 1) * (Pitch - D) + 26 + D + 8 + lw;
    }

    /// <summary>A: the HUD's own seats are the tabs (their screen centers; the last the keeper's fire, the Flare's). Only
    /// the chosen seat's gold ring and the pad's focus are drawn: the seats are the HUD's.</summary>
    public bool Wide;
    public void SetSeats(List<Vector2> centers)
    {
        Wide = true;
        Centers.Clear();
        Centers.AddRange(centers);
        scroll.Visible = false;
        MouseFilter = MouseFilterEnum.Ignore;
        QueueRedraw();
    }

    void Lay()
    {
        if (Wide) { QueueRedraw(); return; }
        float tot = Total(out var ldw, out _);
        float x = Mathf.Round(Size.X / 2 - tot / 2), cy = Size.Y / 2;
        lead = x;
        x += ldw + 20;
        Centers.Clear();
        foreach (var _ in seats)
        {
            Centers.Add(new Vector2(x + D / 2, cy));
            x += Pitch;
        }
        if (seats.Count > 0) x += D - Pitch;
        x += 26;
        allX = x;
        var ce = new Vector2(x + D / 2, cy);
        Centers.Add(ce);
        scroll.Position = ce - scroll.Size / 2;
        QueueRedraw();
    }

    public override void _GuiInput(InputEvent e)
    {
        if (e is not InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left } mb) return;
        for (int i = 0; i < Centers.Count; i++)
            if (mb.Position.DistanceTo(Centers[i]) <= D / 2 + 2) { Choose(i); Clicked?.Invoke(i); AcceptEvent(); return; }
    }

    /// <summary>Move the choice (the last tab is All learned).</summary>
    public void Choose(int i)
    {
        i = Math.Clamp(i, 0, Centers.Count - 1);
        if (i == Chosen) return;
        Chosen = i;
        QueueRedraw();
        ChosenChanged?.Invoke(i);
    }

    public override void _Draw()
    {
        if (Wide)
        {
            float s = HudBottom.Scale;
            float R(int i) => i == Centers.Count - 1 ? (DgPanel.GlassOuterR + 3) * s : (DgPanel.SeatR + 1.5f) * s;
            if (Chosen >= 0 && Chosen < Centers.Count - 1)
            {
                var c = Centers[Chosen];
                for (int k = 4; k >= 1; k--) DrawArc(c, R(Chosen), 0, Mathf.Tau, 72, LampInk.Focus with { A = 0.07f }, 2 + k * 2.5f, true);
                DrawArc(c, R(Chosen), 0, Mathf.Tau, 72, LampInk.Focus, 2f, true);
            }
            if (Focused >= 0 && Focused < Centers.Count)
                DrawArc(Centers[Focused], R(Focused) + 4, 0, Mathf.Tau, 72, new Color("#fff2cf") with { A = 0.9f }, 1.5f, true);
            return;
        }
        float cy = Size.Y / 2;
        Total(out _, out _);
        LampInk.Text(this, LampInk.F("alegreya-sans-700", 2), 13, lead, cy + 5, Lead, LampInk.Dim with { A = 0.95f });
        // the HUD's bronze ring under each seat's well (the plate bakes it in play; here each tab carries its own)
        for (int k = 0; k < seats.Count; k++) Seat(this, Centers[k], D, k, seats[k].Art, seats[k].School);
        Seat(this, Centers[^1], D, 5, null, new Color("#3f6a6a"));
        // the hairline, then All learned
        float hx = allX - 13;
        DrawLine(new Vector2(hx, cy - 18), new Vector2(hx, cy + 18), LampInk.RimGold with { A = 0.35f }, 1);
        LampInk.Text(this, Style.Ui, 15, allX + D + 8, cy + 5, All, LampInk.Body with { A = 0.95f });
        if (Chosen >= 0 && Chosen < Centers.Count)
        {
            var c = Centers[Chosen];
            for (int k = 4; k >= 1; k--) DrawArc(c, 29.5f, 0, Mathf.Tau, 72, LampInk.Focus with { A = 0.07f }, 2 + k * 2.5f, true);
            DrawArc(c, 29.5f, 0, Mathf.Tau, 72, LampInk.Focus, 2f, true);
        }
        if (Focused >= 0 && Focused < Centers.Count)
            DrawArc(Centers[Focused], 34f, 0, Mathf.Tau, 72, new Color("#fff2cf") with { A = 0.9f }, 1.5f, true);
    }

    /// <summary>A tab's seat as the HUD lights it (C_day.png's tabs): the HUD's bronze ring, lifted toward lit bronze; a
    /// well of glass lit in the skill's school, brightest up and left; the skill's gold inlay, bright, warm-lit under.
    /// art null: an empty well (All learned).</summary>
    static Texture2D? well;
    /// <summary>A radial well: alpha (1 - t)^1.2 from the middle to the edge, clipped to the disc.</summary>
    static Texture2D Well
    {
        get
        {
            if (well != null) return well;
            const int n = 96;
            var im = Image.CreateEmpty(n, n, false, Image.Format.Rgba8);
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    float t = new Vector2(x + 0.5f - n / 2f, y + 0.5f - n / 2f).Length() / (n / 2f);
                    im.SetPixel(x, y, new Color(1, 1, 1, t >= 1 ? 0 : Mathf.Pow(1 - t, 1.2f)));
                }
            return well = ImageTexture.CreateFromImage(im);
        }
    }

    public static void Seat(CanvasItem ci, Vector2 c, float d, int idx, string? art, Color school)
    {
        float k = d / (2 * 36.6f);
        float hr = (DgRiver.Hole(idx) > 0 ? DgRiver.Hole(idx) : 26.5f) * k;
        // (p5b: the mock's tab ring, foot.py seat_ring as C_day.png draws it: a clean bronze band lit up and left, a dark
        // seat line inside; the HUD's ornate ring read dark and blotchy at the tab's size)
        float rr = hr + 4.5f;
        ci.DrawArc(c, rr, 0, Mathf.Tau, 72, new Color("#1a120a") with { A = 0.85f }, 7.5f, true);
        ci.DrawArc(c, rr, 0, Mathf.Tau, 72, new Color("#8c6a3c"), 4.2f, true);
        ci.DrawArc(c, rr + 0.6f, Mathf.Pi * 0.95f, Mathf.Pi * 1.75f, 40, new Color("#e8c98a") with { A = 0.5f }, 1.6f, true);
        ci.DrawArc(c, rr - 0.4f, -Mathf.Pi * 0.05f, Mathf.Pi * 0.75f, 40, new Color("#4a3418") with { A = 0.8f }, 1.6f, true);
        ci.DrawCircle(c, hr + 1, new Color("#0b0a0c"), true, -1, true);
        // (the mock's seats, foot.py paint_seat: the school's glass lit from the middle, up and left, to a dark rim. p5b:
        // the glass filled in a deep shade of the school's color first, so the tint shows across the well as C_day.png's,
        // then its light (1 - t)^1.2 over 1.08 of the well's radius and a soft spot up and left)
        float fa = art != null ? 1f : 0.45f;
        ci.DrawCircle(c, hr, (school * new Color(0.26f, 0.26f, 0.26f)).Lerp(new Color("#0b0a0c"), 0.3f) with { A = fa }, true, -1, true);
        ci.DrawTextureRect(Well, new Rect2(c - Vector2.One * hr * 1.08f + new Vector2(-hr * 0.13f, -hr * 0.16f), Vector2.One * hr * 2.16f), false,
            (school * new Color(0.62f, 0.62f, 0.62f)) with { A = 0.85f * fa });
        ci.DrawTextureRect(DgMeters.Disc, new Rect2(c - Vector2.One * hr * 0.7f + new Vector2(-hr * 0.2f, -hr * 0.26f), Vector2.One * hr * 1.4f), false,
            school.Lightened(0.3f) with { A = art != null ? 0.22f : 0.10f });
        ci.DrawArc(c, hr - 1.5f, 0, Mathf.Tau, 64, new Color(0, 0, 0, 0.45f * fa), 3f, true);
        if (art != null && art != "")
        {
            int gi = (int)Mathf.Round(hr * 2 * 0.62f);
            var (gold, glow) = DgGold.Of(art, gi);
            float gs = gi + 2 * DgGold.Pad;
            var gr = new Rect2(c - new Vector2(gs, gs) / 2, new Vector2(gs, gs));
            ci.DrawTextureRect(glow, gr, false, new Color(1f, 0.7f, 0.35f, 0.55f));
            ci.DrawTextureRect(gold, gr, false, new Color(1.45f, 1.36f, 1.2f));
        }
    }
}

/// <summary>A line glyph (Glyphs) drawn at a size and color.</summary>
public partial class GlyphMark : Control
{
    readonly string key;
    readonly int px;
    readonly Color color;
    public GlyphMark(string key, int px, Color color)
    {
        this.key = key; this.px = px; this.color = color;
        MouseFilter = MouseFilterEnum.Ignore;
        Size = new Vector2(px, px);
    }
    public override void _Draw() => DrawTextureRect(Glyphs.Texture(key, px * 2, Colors.White, line: true), new Rect2(Vector2.Zero, Size), false, color);
}

/// <summary>What the focus card says (§7, in order; LampBoard words it from the lamp).</summary>
public sealed record LampCardText(string Name, string? Chip, Color ChipColor, string Place, string Line,
    IReadOnlyList<(string Glyph, bool Carried)> Feeds, string? FeedsText, string? Price, string State, Color StateColor,
    string? Fires, IReadOnlyList<(string Key, string Word)> Prompts);

/// <summary>
/// The focus card (§7, §16; skins/a.py card()): 380 px of smoked glass with the HUD's 1 px gold rim and a soft 20 px
/// drop shadow (black 45%), padding 16: the name (Alegreya 700 21) with the kind's chip at its right, the place
/// (Alegreya Sans 13 caps, dim), a rule, the one line (Alegreya 17, up to two lines), what it feeds (16 px glyphs,
/// carried gold, others gray), a blue lamp's price in red (Alegreya italic 16, #e0705a), a rule, the state line, a
/// link's pick, then this lamp's prompts.
/// </summary>
public partial class LampCard : Control
{
    public const float Wd = 380, Pad = 16;
    LampCardText? c;
    List<string> lines = new(), price = new();
    readonly HBoxContainer promptHost = new() { MouseFilter = MouseFilterEnum.Ignore };
    readonly StyleBoxFlat glass;
    float promptY;

    public LampCard()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Visible = false;
        glass = new StyleBoxFlat
        {
            BgColor = new Color("#0d1015") with { A = 0.86f }, BorderColor = LampInk.RimGold with { A = 0.70f },
            ShadowColor = new Color(0, 0, 0, 0.45f), ShadowSize = 20, ShadowOffset = new Vector2(0, 4), AntiAliasing = true,
        };
        glass.SetBorderWidthAll(1);
        glass.SetCornerRadiusAll(3);
        AddChild(promptHost);
    }

    static Font FName => LampInk.F("alegreya-700");
    static Font FPlace => LampInk.F("alegreya-sans-500", 1);
    static Font FLine => LampInk.F("alegreya-400");
    static Font FUi => Style.Ui;
    static Font FPrice => LampInk.F("alegreya-400-italic");

    /// <summary>Its height for these words (skins/a.py _card()'s rows).</summary>
    public static float HeightOf(LampCardText t, out List<string> lines, out List<string> price, out float promptY)
    {
        float iw = Wd - 2 * Pad;
        lines = t.Line != "" ? LampInk.Wrap(t.Line, FLine, 17, iw) : new();
        price = t.Price is { } p ? LampInk.Wrap(p, FPrice, 16, iw) : new();
        float y = Pad + 19 + 20 + 11 + 8 + 22 * lines.Count;
        if (t.FeedsText != null) y += 27;
        y += 21 * price.Count + 13 + 22;
        if (t.Fires != null) y += 22;
        promptY = 0;
        if (t.Prompts.Count > 0) { y += 27; promptY = y; }
        return y + Pad - 2;
    }

    List<(string Key, string Word)>? shownPrompts;
    bool shownPad;

    public float Show(LampCardText t, bool pad)
    {
        c = t;
        float h = HeightOf(t, out lines, out price, out promptY);
        Size = new Vector2(Wd, h);
        // the prompt row is rebuilt only when its words change (a focus move costs no new controls)
        bool same = shownPrompts != null && shownPad == pad && shownPrompts.SequenceEqual(t.Prompts);
        if (same) { if (promptHost.GetChildCount() > 0) promptHost.Position = new Vector2(Pad, promptY - 5 - promptHost.Size.Y / 2); QueueRedraw(); return h; }
        shownPrompts = t.Prompts.ToList(); shownPad = pad;
        foreach (var ch in promptHost.GetChildren()) { promptHost.RemoveChild(ch); ch.QueueFree(); }
        if (t.Prompts.Count > 0)
        {
            var row = LampInk.Row(t.Prompts, pad, 15, 20);
            promptHost.AddChild(row);
            var s = row.GetCombinedMinimumSize();
            promptHost.Position = new Vector2(Pad, promptY - 5 - s.Y / 2);
            promptHost.Size = s;
        }
        QueueRedraw();
        return h;
    }

    public override void _Draw()
    {
        if (c == null) return;
        DrawStyleBox(glass, new Rect2(Vector2.Zero, Size));
        DrawLine(new Vector2(3, 1.5f), new Vector2(Wd - 3, 1.5f), new Color(1, 1, 1, 0.06f), 1);
        float x0 = Pad, x1 = Wd - Pad, y = Pad;
        // the name, the chip at its right
        y += 19;
        float xc = x1;
        if (c.Chip != null) xc = Chip(x1, y - 2, c.Chip, c.ChipColor) - 8;
        LampInk.Text(this, FName, 21, x0, y, Ellipsize(c.Name, FName, 21, xc - x0), LampInk.Ink);
        y += 20;
        LampInk.Text(this, FPlace, 13, x0, y, c.Place, LampInk.Dim);
        y += 11;
        LampInk.Rule(this, x0, x1, y);
        y += 8;
        foreach (var ln in lines) { y += 22; LampInk.Text(this, FLine, 17, x0, y, ln, LampInk.Body); }
        if (c.FeedsText != null)
        {
            y += 27;
            float x = x0;
            foreach (var (g, carried) in c.Feeds)
            {
                DrawTextureRect(Glyphs.Texture(g, 32, Colors.White, line: true), new Rect2(x, y - 13, 16, 16), false, carried ? LampInk.Gold : LampInk.Dim);
                x += 21;
            }
            LampInk.Text(this, FUi, 15, x + 4, y, c.FeedsText, LampInk.Body with { A = 0.95f });
        }
        foreach (var ln in price) { y += 21; LampInk.Text(this, FPrice, 16, x0, y, ln, LampInk.Red); }
        y += 13;
        LampInk.Rule(this, x0, x1, y);
        y += 22;
        LampInk.Text(this, FUi, 15, x0, y, c.State, c.StateColor);
        if (c.Fires != null) { y += 22; LampInk.Text(this, FUi, 15, x0, y, c.Fires, LampInk.Body); }
    }

    /// <summary>The kind's chip, right-aligned at xr (Alegreya Sans 700 13 caps in a thin rounded outline); its left x.</summary>
    float Chip(float xr, float yb, string s, Color col)
    {
        var f = LampInk.F("alegreya-sans-700", 1);
        float w = LampInk.W(f, s, 13) - 1;
        float x0 = xr - w - 14;
        var box = new StyleBoxFlat { BgColor = (col * 0.25f) with { A = 0.35f }, BorderColor = col with { A = 0.55f }, AntiAliasing = true };
        box.SetBorderWidthAll(1);
        box.SetCornerRadiusAll(3);
        DrawStyleBox(box, new Rect2(x0, yb - 13.5f, xr - x0, 18));
        LampInk.Text(this, f, 13, x0 + 7, yb, s, col with { A = 0.95f });
        return x0;
    }

    static string Ellipsize(string s, Font f, int px, float maxw)
    {
        if (LampInk.W(f, s, px) <= maxw) return s;
        while (s.Length > 0 && LampInk.W(f, s + "…", px) > maxw) s = s[..^1].TrimEnd();
        return s + "…";
    }
}
