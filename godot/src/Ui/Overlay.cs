using System;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// A screen over the game (the pack, the self, the journal, the map, a
/// shop, the pause menu...): built from the journey's state and built again
/// whenever it changes, so what it shows is never stale. Keys reach it
/// before the game; Escape (or its own key again) puts it away. Focus moves
/// over it with the keys or a pad (<see cref="Ui.Nav"/>); the five screens of
/// the day (the pack, the self, the arts, the journal, the map) are tabs of
/// one book, turned with LB and RB.
/// </summary>
public abstract partial class Overlay : Control
{
    protected readonly Game G;
    protected readonly Nav Nav;
    /// <summary>What it is ('inventory', 'character', 'journal', 'map', 'shop', 'stash', 'rest', 'pause', 'chapter').</summary>
    public abstract string Kind { get; }
    /// <summary>The key that opens it closes it too.</summary>
    public virtual Act? Toggle => null;
    /// <summary>Escape closes it (not the chapter's end, not the title).</summary>
    public virtual bool Dismissable => true;

    /// <summary>The day's book: its tabs in order, each with the key that opens it.</summary>
    public static readonly (string Kind, string Name, Act Key)[] Book =
    {
        ("inventory", "Pack", Act.Inventory), ("character", "Self", Act.Character), ("arts", "Arts", Act.Arts),
        ("journal", "Journal", Act.Journal), ("map", "Map", Act.Map),
    };
    bool InBook => Book.Any(b => b.Kind == Kind);

    protected Overlay(Game g)
    {
        G = g;
        Nav = new Nav(this);
        Style.Fill(this);
        MouseFilter = MouseFilterEnum.Ignore;
    }

    public override void _Ready()
    {
        // A screen opened from the pad starts with its focus shown.
        if (Controls.Instance?.UsingPad == true) Nav.KeyMode = true;
        Refresh();
    }

    /// <summary>Everything again, from the state as it is now.</summary>
    public void Refresh()
    {
        tip = null;
        foreach (var c in GetChildren()) { RemoveChild(c); c.QueueFree(); }
        Build();
        Nav.Collect();
    }

    protected abstract void Build();

    /// <summary>An action for this screen: true if it took it.</summary>
    public virtual bool Key(Act a) => false;

    /// <summary>An action, heard by the screen first, then by focus, then by the book's tabs.</summary>
    public bool Handle(Act a)
    {
        if (Key(a)) return true;
        if (Nav.Key(a)) return true;
        if (!InBook) return false;
        if (a is Act.TabNext or Act.TabPrev)
        {
            int i = Array.FindIndex(Book, b => b.Kind == Kind);
            Sound.Sfx.Page();
            G.Open(Book[(i + (a == Act.TabNext ? 1 : Book.Length - 1)) % Book.Length].Kind);
            return true;
        }
        // Another tab's key turns to it; the open tab's own key, or View on a pad, closes the book.
        foreach (var (kind, _, key) in Book)
        {
            if (key != a) continue;
            if (kind == Kind || a == Act.Inventory && Controls.Instance?.UsingPad == true) G.CloseOverlay();
            else { Sound.Sfx.Page(); G.Open(kind); }
            return true;
        }
        return false;
    }

    public override void _Process(double delta) => Nav.Update(delta);

    /// <summary>Its focus routes walked (--navcheck).</summary>
    public System.Collections.Generic.List<string> NavAudit() => Nav.Audit();

    public override void _Input(InputEvent e)
    {
        // The mouse moving takes the ring away; the pointer is the focus now.
        if (e is InputEventMouseMotion mm && mm.Relative.Length() > 6 && Nav.KeyMode) Nav.KeyMode = false;
    }

    /// <summary>
    /// A plate in the middle of the screen with a heading and a close button.
    /// A fixed size for screens whose insides scroll; fit, it is as tall as
    /// what is in it (never an empty half plate).
    /// </summary>
    protected VBoxContainer Frame(string title, Vector2 size, string closeKey, string? sub = null, Action? close = null, bool fit = false)
    {
        AddChild(Style.Scrim(close ?? G.CloseOverlay));
        var plate = Style.Panel(Style.Plate());
        if (fit)
        {
            var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            Style.Fill(centre);
            plate.CustomMinimumSize = new Vector2(size.X, 0);
            centre.AddChild(plate);
            AddChild(centre);
        }
        else AddChild(Style.Centered(plate, size));
        // The book's tabs sit on the plate's top edge, like the tabs of a ledger.
        if (InBook)
        {
            var tabs = BookTabs(new Vector2((1920 - size.X) / 2, (1080 - size.Y) / 2 - 42));
            if (fit) Callable.From(() => { if (IsInstanceValid(plate)) tabs.Position = plate.GlobalPosition + new Vector2(0, -42); }).CallDeferred();
        }
        var v = Style.V(Style.Gap3);
        plate.AddChild(v);
        var head = Style.H(Style.Gap3);
        var names = Style.V(2, Style.Cap(title, 20));
        if (sub != null) names.AddChild(Style.Label(sub, Style.TextItalic, Style.Small, Style.InkDim, true));
        names.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        head.AddChild(names);
        // B and Escape close; the button is for the mouse, so focus never starts or sticks on it.
        var btn = Nav.Skip(CloseButton(closeKey, close ?? G.CloseOverlay));
        btn.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        head.AddChild(btn);
        v.AddChild(head);
        return v;
    }

    bool hidHud;

    /// <summary>A screen that has the whole screen: the HUD steps away while it is open and comes back with the world.</summary>
    protected void HideHud()
    {
        if (hidHud) return;
        hidHud = true;
        G.Hud.ShowPlay(false);
        TreeExiting += () => { if (G.Mode == "play") G.Hud.ShowPlay(true); };
    }

    /// <summary>
    /// A full-screen page (docs/UI_DESIGN.md, "The page"): the world dark
    /// behind, a header band across the top with the book's tabs at the left,
    /// the page's title plaque in the middle and Close at the right; returns
    /// the content area, 1840 by 920 at (40, 112). Screens lay their panes in
    /// it with <see cref="Pane"/>.
    /// </summary>
    protected Control Page(string title, string? sub = null, Action? close = null, string? closeKey = null)
    {
        HideHud();
        AddChild(new Backdrop());
        var band = Style.Panel(UiArt.Frame("header", OrnateBox.Make(OrnateBox.Kind.Slab, 0)));
        band.Position = new Vector2(-4, -4);
        band.Size = new Vector2(1928, 100);
        band.MouseFilter = MouseFilterEnum.Ignore;
        AddChild(band);
        if (InBook) BookTabs(new Vector2(40, 30));
        var plaque = new Plaque(title, 34, 120);
        AddChild(plaque);
        plaque.Position = new Vector2((1920 - plaque.CustomMinimumSize.X) / 2, sub != null ? 14 : 26);
        if (sub != null)
        {
            var s = Style.Label(sub, Style.TextItalic, Style.Small, Style.InkDim, false, HorizontalAlignment.Center);
            s.Position = new Vector2(360, 58);
            s.Size = new Vector2(1200, 24);
            AddChild(s);
        }
        var btn = Nav.Skip(CloseButton(closeKey ?? (Toggle is Act t ? G.Key(t) : "Esc"), close ?? G.CloseOverlay));
        btn.Position = new Vector2(1880 - btn.CustomMinimumSize.X, 30);
        AddChild(btn);
        var content = new Control { Position = new Vector2(40, 112), Size = new Vector2(1840, 920), MouseFilter = MouseFilterEnum.Ignore };
        AddChild(content);
        return content;
    }

    /// <summary>A pane on a page: an ornate frame at a place, with a column inside it.</summary>
    protected static VBoxContainer Pane(Control parent, Rect2 at, StyleBox? box = null, int gap = Style.Gap3)
    {
        var p = Style.Panel(box ?? Style.Plate(20));
        p.Position = at.Position;
        p.Size = at.Size;
        p.MouseFilter = MouseFilterEnum.Ignore;
        parent.AddChild(p);
        var v = Style.V(gap);
        p.AddChild(v);
        return v;
    }

    /// <summary>The page's footer of prompts, under the content area.</summary>
    protected void PageFooter(Control row)
    {
        if (row is BoxContainer b) b.Alignment = BoxContainer.AlignmentMode.Center;
        if (row is Label l) l.HorizontalAlignment = HorizontalAlignment.Center;
        row.Position = new Vector2(40, 1040);
        row.Size = new Vector2(1840, 32);
        AddChild(row);
    }

    /// <summary>Close, with its key: a pad shows B, the keyboard the screen's own key.</summary>
    protected static Button CloseButton(string closeKey, Action close)
    {
        var btn = Style.Button("", close, false, true);
        var row = Style.H(Style.Gap2, Controls.Instance?.UsingPad == true ? Style.PadButton("B") : Style.Key(closeKey), Style.Label("Close", Style.UiBold, Style.Small, Style.GoldHi));
        row.MouseFilter = MouseFilterEnum.Ignore;
        row.Position = new Vector2(10, 5);
        btn.AddChild(row);
        btn.CustomMinimumSize = new Vector2(row.GetCombinedMinimumSize().X + 22, 36);
        Nav.Id(btn, "close");
        return btn;
    }

    /// <summary>The book's tabs above a plate: each with its key, the one open lit; LB and RB at the ends.</summary>
    protected Control BookTabs(Vector2 at)
    {
        var bar = Style.H(Style.Gap1);
        bar.MouseFilter = MouseFilterEnum.Ignore;
        bool pad = Controls.Instance?.UsingPad == true;
        bar.AddChild(pad ? Style.PadButton("LB") : Style.Key(Controls.Instance?.KeyLabel(Act.TabPrev) ?? "["));
        foreach (var (kind, name, key) in Book)
        {
            bool on = kind == Kind;
            var b = Style.Button("", () => { if (!on) G.Open(kind); }, on, true);
            var row = Style.H(Style.Gap2, Style.Label(name, Style.UiBold, Style.Small, on ? Colors.White : Style.GoldHi));
            if (!pad) row.AddChild(Style.Key(Controls.Instance?.KeyLabel(key) ?? ""));
            row.MouseFilter = MouseFilterEnum.Ignore;
            row.Position = new Vector2(12, 6);
            b.AddChild(row);
            b.CustomMinimumSize = new Vector2(row.GetCombinedMinimumSize().X + 24, 36);
            if (on) b.AddThemeStyleboxOverride("normal", UiArt.Frame("tab_on", Style.Box(new Color("#3a2614"), Style.LineHi, 1, 4)));
            else if (UiArt.Has("tab")) b.AddThemeStyleboxOverride("normal", UiArt.Frame("tab", new StyleBoxEmpty()));
            // The tabs are reached with LB and RB, not by walking focus up to them.
            Nav.Skip(b);
            bar.AddChild(b);
        }
        bar.AddChild(pad ? Style.PadButton("RB") : Style.Key(Controls.Instance?.KeyLabel(Act.TabNext) ?? "]"));
        bar.Position = at;
        AddChild(bar);
        return bar;
    }

    /// <summary>The footer every screen keeps: what the buttons do here, for the device in hand.</summary>
    protected static Control Footer(params (Act Act, string Text)[] items)
    {
        var h = Style.Hints(items);
        h.Alignment = BoxContainer.AlignmentMode.Center;
        return h;
    }

    /// <summary>The same footer for the mouse: what clicks do, quietly.</summary>
    protected static Control MouseFooter(params string[] lines)
    {
        var l = Style.Label(string.Join("   ·   ", lines), Style.TextItalic, Style.Caption, Style.InkDim, false, HorizontalAlignment.Center);
        return l;
    }

    /* ------------------------------------------------ hovering a thing -- */

    Control? tip;

    /// <summary>A card beside what the mouse is over, or what has focus (null: gone).</summary>
    protected void Tip(Control? card, Control? over)
    {
        tip?.QueueFree();
        tip = null;
        if (card == null || over == null) return;
        tip = card;
        tip.MouseFilter = MouseFilterEnum.Ignore;
        tip.ZIndex = 40;
        AddChild(tip);
        // Placed now and again once laid out: wrapped words only know their height after a frame,
        // and a card measured before that stands as tall as the screen.
        tip.Modulate = Colors.Transparent;
        var shown = tip;
        void Place()
        {
            if (!IsInstanceValid(shown) || shown != tip || !IsInstanceValid(over)) return;
            var r = over.GetGlobalRect();
            var vp = GetViewportRect().Size;
            shown.ResetSize();
            var size = shown.Size;
            float x = r.End.X + 10, y = r.Position.Y;
            if (x + size.X > vp.X - 8) x = r.Position.X - size.X - 10;
            if (y + size.Y > vp.Y - 8) y = vp.Y - size.Y - 8;
            shown.GlobalPosition = new Vector2(Mathf.Max(8, x), Mathf.Max(8, y));
        }
        Place();
        Callable.From(() => { Place(); if (IsInstanceValid(shown)) shown.Modulate = Colors.White; }).CallDeferred();
    }
}

/// <summary>Where the overlays live: over the HUD, under the fade.</summary>
public partial class Screens : CanvasLayer
{
    public Overlay? Current { get; private set; }

    public Screens() { Layer = 20; }

    public void Show(Overlay o)
    {
        Close();
        Current = o;
        AddChild(o);
    }

    public void Close()
    {
        if (Current == null) return;
        RemoveChild(Current);
        Current.QueueFree();
        Current = null;
    }
}
