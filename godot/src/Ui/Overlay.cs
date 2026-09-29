using System;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// A screen over the game (the pack, the self, the journal, the map, a
/// shop, the pause menu...): built from the journey's state and built again
/// whenever it changes, so what it shows is never stale. Keys reach it
/// before the game; Escape (or its own key again) puts it away.
/// </summary>
public abstract partial class Overlay : Control
{
    protected readonly Game G;
    /// <summary>What it is ('inventory', 'character', 'journal', 'map', 'shop', 'stash', 'rest', 'pause', 'chapter').</summary>
    public abstract string Kind { get; }
    /// <summary>The key that opens it closes it too.</summary>
    public virtual Act? Toggle => null;
    /// <summary>Escape closes it (not the chapter's end, not the title).</summary>
    public virtual bool Dismissable => true;

    protected Overlay(Game g)
    {
        G = g;
        Style.Fill(this);
        MouseFilter = MouseFilterEnum.Ignore;
    }

    public override void _Ready() => Refresh();

    /// <summary>Everything again, from the state as it is now.</summary>
    public void Refresh()
    {
        foreach (var c in GetChildren()) { RemoveChild(c); c.QueueFree(); }
        Build();
    }

    protected abstract void Build();

    /// <summary>An action for this screen: true if it took it.</summary>
    public virtual bool Key(Act a) => false;

    /// <summary>A plate in the middle of the screen with a heading and a close button.</summary>
    protected VBoxContainer Frame(string title, Vector2 size, string closeKey, string? sub = null, Action? close = null)
    {
        AddChild(Style.Scrim(close ?? G.CloseOverlay));
        var plate = Style.Centered(Style.Panel(Style.Plate()), size);
        AddChild(plate);
        var v = Style.V(10);
        plate.AddChild(v);
        var head = Style.H(12);
        var names = Style.V(0, Style.Cap(title, 18));
        if (sub != null) names.AddChild(Style.Label(sub, Style.TextItalic, 15, Style.InkDim));
        names.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        head.AddChild(names);
        var btn = Style.Button("", close ?? G.CloseOverlay, false, true);
        var row = Style.H(6, Style.Key(closeKey), Style.Label("Close", Style.UiBold, 14, Style.GoldHi));
        row.MouseFilter = MouseFilterEnum.Ignore;
        btn.AddChild(row);
        btn.CustomMinimumSize = new Vector2(96, 30);
        row.Position = new Vector2(12, 4);
        head.AddChild(btn);
        v.AddChild(head);
        return v;
    }

    /* ------------------------------------------------ hovering a thing -- */

    Control? tip;

    /// <summary>A card beside what the mouse is over (null: gone).</summary>
    protected void Tip(Control? card, Control? over)
    {
        tip?.QueueFree();
        tip = null;
        if (card == null || over == null) return;
        tip = card;
        tip.MouseFilter = MouseFilterEnum.Ignore;
        AddChild(tip);
        var r = over.GetGlobalRect();
        var vp = GetViewportRect().Size;
        tip.ResetSize();
        var size = tip.GetCombinedMinimumSize();
        float x = r.End.X + 10, y = r.Position.Y;
        if (x + size.X > vp.X - 8) x = r.Position.X - size.X - 10;
        if (y + size.Y > vp.Y - 8) y = vp.Y - size.Y - 8;
        tip.GlobalPosition = new Vector2(x, Mathf.Max(8, y));
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
