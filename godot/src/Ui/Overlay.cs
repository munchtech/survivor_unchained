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
        Theme = Style.PageTheme;
    }

    /// <summary>The keys or the pad have their focus on this control (a hold-to-confirm press asks).</summary>
    public bool Focused(Control c) => Nav.Enabled && Nav.KeyMode && Nav.Current?.C == c;

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
        panes.Clear();
        Build();
        Dividers();
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
        if (e is InputEventMouseMotion { Relative: var rel } && rel.Length() > 0.5f) Nav.MouseMotion();
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
        AddChild(new Backdrop(page: true));
        var band = Style.Panel(UiArt.Frame("header", OrnateBox.Make(OrnateBox.Kind.Slab, 0)));
        band.Position = new Vector2(-4, -4);
        band.Size = new Vector2(1928, 100);
        band.MouseFilter = MouseFilterEnum.Ignore;
        AddChild(band);
        // The book's tabs ride the same chain on a full page as on the panel, so turning from the
        // Pack to the Journal keeps one object under the hand.
        if (InBook)
        {
            int on = Array.FindIndex(Book, b => b.Kind == Kind);
            var tabs = new ChainTabs(Book.Select(b => (b.Name, Controls.Instance?.KeyLabel(b.Key) ?? "")).ToArray(), on, k => { Sound.Sfx.Page(); G.Open(Book[k].Kind); })
                { Position = new Vector2(40, 16) };
            AddChild(tabs);
        }
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
        // The foot band (frames/footer.png), the header's match: the page is bound top and bottom.
        // Laid before the content, so a pane's faded foot runs over its top edge rather than under it.
        if (UiArt.Has("footer"))
        {
            var foot = Style.Panel(UiArt.Frame("footer", new StyleBoxEmpty()));
            foot.Position = new Vector2(-4, 1016);
            foot.Size = new Vector2(1928, 68);
            foot.MouseFilter = MouseFilterEnum.Ignore;
            AddChild(foot);
        }
        var content = new Control { Position = new Vector2(40, 112), Size = new Vector2(1840, 920), MouseFilter = MouseFilterEnum.Ignore };
        AddChild(content);
        return content;
    }

    /// <summary>Where the survivor should stand across the screen while this is open, in
    /// pixels from the middle (a side panel: beside it, in view). 0 leaves them centred.</summary>
    public virtual float CameraShift => 0;

    /// <summary>How near the camera comes while this is open (1: as it was).</summary>
    public virtual float CameraNear => 1;

    /// <summary>A place on the ground the view looks at while this is open, instead of the survivor
    /// (a counter: the keeper, live in the world between its two panels). Null: the survivor.</summary>
    public virtual (double X, double Z)? CameraLook => null;

    /// <summary>
    /// A panel down one side of the screen (docs/UI_DESIGN.md 6, "Page or panel"):
    /// for what is tweaked mid-play, where the world should stay in view (Diablo
    /// IV, PoE, Last Epoch keep the pack and the character beside the world). The
    /// world is shaded only toward the panel; the HUD steps away; the head carries
    /// the book's tabs, Close and the title plaque. Returns the content area.
    /// </summary>
    protected Control SidePanel(string title, string? sub, bool right, float width, Action? close = null, string? closeKey = null)
    {
        HideHud();
        var shade = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(0.02f, 0.015f, 0.03f, 0), new Color(0.02f, 0.015f, 0.03f, 0.25f), new Color(0.02f, 0.015f, 0.03f, 0.85f) }, Offsets = new[] { 0f, 0.4f, 1f } },
                FillFrom = new Vector2(right ? 0 : 1, 0), FillTo = new Vector2(right ? 1 : 0, 0), Width = 256, Height = 4,
            },
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
        };
        Style.Fill(shade);
        AddChild(shade);
        float x = right ? 1920 - width - 16 : 16;
        var plate = Style.Panel(Style.Plate(0));
        plate.Position = new Vector2(x, 16);
        plate.Size = new Vector2(width, 1048);
        plate.MouseFilter = MouseFilterEnum.Stop;
        AddChild(plate);
        if (InBook) BookTabs(new Vector2(x + 28, 36));
        var btn = Nav.Skip(CloseButton(closeKey ?? (Toggle is Act t ? G.Key(t) : "Esc"), close ?? G.CloseOverlay));
        btn.Position = new Vector2(x + width - 28 - btn.CustomMinimumSize.X, 36);
        AddChild(btn);
        var plaque = new Plaque(title, 30, 110);
        AddChild(plaque);
        plaque.Position = new Vector2(x + (width - plaque.CustomMinimumSize.X) / 2, 84);
        float top = 132;
        if (sub != null)
        {
            var s = Style.Label(sub, Style.TextItalic, Style.Small, Style.InkDim, false, HorizontalAlignment.Center);
            s.Position = new Vector2(x, 128);
            s.Size = new Vector2(width, 22);
            AddChild(s);
            top = 158;
        }
        var content = new Control { Position = new Vector2(x + 26, top), Size = new Vector2(width - 52, 1064 - top - 70), MouseFilter = MouseFilterEnum.Ignore };
        AddChild(content);
        sideX = x; sideW = width;
        return content;
    }

    float sideX, sideW;

    /* --------------------------------------------- the approved layouts -- */

    /// <summary>The day's book's panel: its left edge and width (docs/ui_review/self_v2). The book
    /// (Pack, Self, Arts) is one right-hand panel, so turning its tabs changes only what is in it.</summary>
    public const float BookX = 1920 - 16 - BookW, BookW = 900;

    /// <summary>The margin inside every panel, the same on all four sides.</summary>
    public const int Margin = 28;

    /// <summary>How much of the world shows through a panel's ground (the owner: "the whole
    /// backdrop can get a ever so slight transparency"): evenly, everywhere, never in a fade.</summary>
    public const float GroundAlpha = 0.93f;

    /// <summary>
    /// The day's book as a panel at the right, over the live world (the owner: "we like to see our
    /// beautiful game"). It hugs what it holds and ends cleanly at its content with the same margin on
    /// every side (the owner on the old taper: "the fade away isn't needed"); its ground lets the
    /// world through ever so slightly. Its head carries the book's tabs on their chain and Close, then
    /// the title when there is one (Self's name; the Pack's open tab says enough). Returns its column.
    /// </summary>
    protected VBoxContainer BookPanel(string? title, Action? close = null)
    {
        HideHud();
        var shade = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(0.02f, 0.015f, 0.03f, 0), new Color(0.02f, 0.015f, 0.03f, 0.06f), new Color(0.02f, 0.015f, 0.03f, 0.3f), new Color(0.02f, 0.015f, 0.03f, 0.3f) }, Offsets = new[] { 0f, 0.3f, BookX / 1920f, 1f } },
                Width = 256, Height = 4,
            },
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
            Position = Vector2.Zero, Size = new Vector2(1920, 1080),
        };
        AddChild(shade);
        var panel = Style.Panel(Kit.Window(Margin, Margin, Margin));
        panel.Position = new Vector2(BookX, 16);
        panel.CustomMinimumSize = new Vector2(BookW, 0);
        panel.MouseFilter = MouseFilterEnum.Stop;
        // (only the ground is see-through: what is on it stays whole)
        panel.SelfModulate = Colors.White with { A = GroundAlpha };
        AddChild(panel);
        var v = Style.V(Style.Gap3);
        panel.AddChild(v);
        var head = Style.H(Style.Gap3);
        if (InBook)
        {
            int on = Array.FindIndex(Book, b => b.Kind == Kind);
            head.AddChild(new ChainTabs(Book.Select(b => (b.Name, Controls.Instance?.KeyLabel(b.Key) ?? "")).ToArray(), on, k => { Sound.Sfx.Page(); G.Open(Book[k].Kind); }));
        }
        head.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        var btn = Nav.Skip(CloseButton(Toggle is Act t ? G.Key(t) : "Esc", close ?? G.CloseOverlay));
        btn.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        head.AddChild(btn);
        v.AddChild(head);
        if (title != null) v.AddChild(new Title(title, 30, false));
        sideX = BookX; sideW = BookW;
        return v;
    }

    /// <summary>A fitted panel at a counter (theirs at the left, yours at the right, the keeper live
    /// in the world between): as tall as what it holds, the same margin on every side, its ground
    /// ever so slightly see-through. Returns its column.</summary>
    protected VBoxContainer Fitted(Vector2 at, float width, int gap = Style.Gap4)
    {
        var panel = Style.Panel(Kit.Window(Margin, Margin, Margin));
        panel.Position = at;
        panel.CustomMinimumSize = new Vector2(width, 0);
        panel.MouseFilter = MouseFilterEnum.Stop;
        panel.SelfModulate = Colors.White with { A = GroundAlpha };
        AddChild(panel);
        var v = Style.V(gap);
        panel.AddChild(v);
        return v;
    }

    /// <summary>A screen's prompts along the foot of the world, under its panels (a counter, the bench):
    /// the world can be bright there, so a soft oval of shade lies behind them, darkest at their middle
    /// and gone well before its edge, so no shape is seen. No plate.</summary>
    protected void PromptsOnWorld(Control row)
    {
        float w = row.GetCombinedMinimumSize().X + 260;
        var wash = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f), Width = 128, Height = 128,
                Gradient = new Gradient { Colors = new[] { new Color(0.02f, 0.015f, 0.02f, 0.78f), new Color(0.02f, 0.015f, 0.02f, 0.6f), new Color(0.02f, 0.015f, 0.02f, 0) }, Offsets = new[] { 0f, 0.5f, 1f } },
            },
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
            Position = new Vector2(960 - w / 2, 1016 - 50), Size = new Vector2(w, 100),
        };
        AddChild(wash);
        var centre = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore, Position = new Vector2(0, 1000), Size = new Vector2(1920, 32) };
        centre.AddChild(row);
        AddChild(centre);
    }

    /// <summary>A side panel's prompts, along its foot.</summary>
    protected void SideFooter(Control row)
    {
        if (row is BoxContainer b) b.Alignment = BoxContainer.AlignmentMode.Center;
        if (row is Label l) l.HorizontalAlignment = HorizontalAlignment.Center;
        row.Position = new Vector2(sideX + 20, 1010);
        row.Size = new Vector2(sideW - 40, 32);
        AddChild(row);
    }

    /// <summary>A pane on a page, at a place, with a column inside it: no frame unless one is
    /// asked for (the page's one hero plate, say), so frames are not nested in frames.</summary>
    protected VBoxContainer Pane(Control parent, Rect2 at, StyleBox? box = null, int gap = Style.Gap3)
    {
        var p = Style.Panel(box ?? Style.Column(20));
        p.Position = at.Position;
        p.Size = at.Size;
        p.MouseFilter = MouseFilterEnum.Ignore;
        parent.AddChild(p);
        panes.Add((parent, at));
        var v = Style.V(gap);
        p.AddChild(v);
        return v;
    }

    readonly System.Collections.Generic.List<(Control Parent, Rect2 At)> panes = new();

    /// <summary>A forged rail down each gap between a page's columns, a stone at its middle
    /// (frames/column_divider.png): the columns read as one page, not boxes floating apart.</summary>
    void Dividers()
    {
        var stone = UiArt.Art("frames/column_divider_stone.png");
        if (UiArt.Has("column_divider"))
            foreach (var (parent, a) in panes)
                foreach (var (other, b) in panes)
                {
                    float gap = b.Position.X - a.End.X, top = Mathf.Max(a.Position.Y, b.Position.Y), foot = Mathf.Min(a.End.Y, b.End.Y);
                    if (other != parent || gap < 12 || gap > 48 || foot - top < 160) continue;
                    var rail = new Panel { MouseFilter = MouseFilterEnum.Ignore, Position = new Vector2(a.End.X + gap / 2 - 12, top + 10), Size = new Vector2(24, foot - top - 20) };
                    rail.AddThemeStyleboxOverride("panel", UiArt.Frame("column_divider", new StyleBoxEmpty()));
                    parent.AddChild(rail);
                    if (stone == null) continue;
                    var s = stone.GetSize();
                    parent.AddChild(new TextureRect { Texture = stone, MouseFilter = MouseFilterEnum.Ignore, Size = s, Position = rail.Position + new Vector2(12 - s.X / 2, rail.Size.Y / 2 - s.Y / 2) });
                }
        panes.Clear();
    }

    /// <summary>The page's footer of prompts, under the content area.</summary>
    protected void PageFooter(Control row)
    {
        if (row is BoxContainer b) b.Alignment = BoxContainer.AlignmentMode.Center;
        if (row is Label l) l.HorizontalAlignment = HorizontalAlignment.Center;
        // (on the foot band's leather when there is one, below its rail)
        row.Position = new Vector2(40, UiArt.Has("footer") ? 1044 : 1040);
        row.Size = new Vector2(1840, 32);
        AddChild(row);
    }

    /// <summary>Close, with its key: a pad shows B, the keyboard the screen's own key.</summary>
    protected static Button CloseButton(string closeKey, Action close)
    {
        // Close as words with its key, not a button box (words as type, the owner's rule).
        var btn = new Button { FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand, Flat = true };
        foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) btn.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
        btn.Pressed += close;
        var word = Style.Label("Close", Style.UiBold, Style.Small, Kit.Ink2);
        var row = Style.H(Style.Gap2, Controls.Instance?.UsingPad == true ? Style.PadButton("B") : Style.Key(closeKey), word);
        row.MouseFilter = MouseFilterEnum.Ignore;
        row.Position = new Vector2(0, 5);
        btn.AddChild(row);
        btn.MouseEntered += () => word.AddThemeColorOverride("font_color", Kit.Ink);
        btn.MouseExited += () => word.AddThemeColorOverride("font_color", Kit.Ink2);
        btn.CustomMinimumSize = new Vector2(row.GetCombinedMinimumSize().X, 36);
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

    /// <summary>
    /// A thing's card beside it, on the world's side of the panel it lies in (UI_RESEARCH 7: no
    /// inspect panel; the card opens beside the thing, the worn piece beside that, so the eye goes
    /// from the thing to its card to what it would replace). leftward: the cards open to the left
    /// of edge (a panel at the screen's right); else to the right of it. The worn card goes on
    /// further out where there is room, under the first where there is not.
    /// </summary>
    protected void TipBeside(Control? card, Control? worn, Control? over, bool leftward, float edge)
    {
        tip?.QueueFree();
        tip = null;
        if (card == null || over == null) return;
        var holder = new Control { MouseFilter = MouseFilterEnum.Ignore, ZIndex = 40, Modulate = Colors.Transparent };
        holder.AddChild(card);
        if (worn != null) holder.AddChild(worn);
        tip = holder;
        AddChild(holder);
        void Place()
        {
            if (!IsInstanceValid(holder) || holder != tip || !IsInstanceValid(over)) return;
            var r = over.GetGlobalRect();
            var vp = GetViewportRect().Size;
            card.ResetSize();
            var cs = card.Size;
            float x = leftward ? edge - 14 - cs.X : edge + 14;
            float y = Mathf.Max(8, Mathf.Min(r.Position.Y - 8, vp.Y - 8 - cs.Y));
            card.Position = new Vector2(x, y);
            if (worn == null) return;
            worn.ResetSize();
            var ws = worn.Size;
            float wx = leftward ? x - 12 - ws.X : x + cs.X + 12;
            bool beside = leftward ? wx >= 8 : wx + ws.X <= vp.X - 8;
            // Beside it, its top a little lower, so the two read as a pair and not a wall; under it otherwise.
            worn.Position = beside ? new Vector2(wx, Mathf.Max(8, Mathf.Min(y + 22, vp.Y - 8 - ws.Y))) : new Vector2(x, Mathf.Max(8, Mathf.Min(y + cs.Y + 10, vp.Y - 8 - ws.Y)));
        }
        Place();
        Callable.From(() => { Place(); if (IsInstanceValid(holder)) holder.Modulate = Colors.White; }).CallDeferred();
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
