using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The wardrobe (bd-ui W18), opened from the Pack: looks collected from gear she has found, shown over any piece of the
/// same place, and dyes on the zones of what is shown. It changes how she looks, never what she wears (Rpg/Wardrobe.cs).
/// Her, whole, on the left (a hover over a look or a dye previews it); on the right the places, the looks as the Pack's
/// tiles, and a row of swatches for each zone the shown piece has. Esc goes back to the Pack.
/// </summary>
public partial class WardrobeScreen : Overlay
{
    public override string Kind => "wardrobe";
    public override bool Dismissable => false;
    public override float CameraShift => -330;
    public override float CameraNear => 0.56f;
    public override (float Pitch, float Distance, float Height)? CameraFrame => BookFrame;

    const int DollW = 420, DollH = 720, Tile = 70, Cols = 5, Swatch = 26;
    static readonly string[] SlotNames = ["Head", "Body", "Feet"];
    static readonly Dictionary<string, string> ZoneNames = new() { ["metal"] = "Metal", ["trim"] = "Trim", ["leather"] = "Leather", ["cloth"] = "Cloth" };
    // What a zone looks like as made, when the piece names no dye of its own for it.
    static readonly Dictionary<string, Color> ZoneMade = new()
    {
        ["metal"] = new Color("#8a8f98"), ["trim"] = new Color("#b08a3a"), ["leather"] = new Color("#5a3a28"), ["cloth"] = new Color("#6a665c"),
    };

    static int slot = -1;
    Control? dollHolder;
    Label? status;

    public WardrobeScreen(Game g) : base(g)
    {
        if (Args.Get("wardrobe-slot") is string s && Array.IndexOf(Wardrobe.LookSlots, s) is var i and >= 0) slot = i;
        if (slot < 0) slot = 1;
    }

    CharacterData Ch => G.Journey.Ch;
    string Slot => Wardrobe.LookSlots[slot];

    public override bool Key(Act a)
    {
        if (a is Act.Cancel or Act.Pause) { Sound.Sfx.Page(); G.Open("inventory"); return true; }
        return false;
    }

    protected override void Build()
    {
        var ch = Ch;
        Wardrobe.BackFill(ch);
        var v = BookPanel(null, () => G.Open("inventory"));
        var (found, total) = Wardrobe.Count(ch);
        var body = Style.H(24);
        dollHolder = new Control { CustomMinimumSize = new Vector2(DollW, DollH), MouseFilter = MouseFilterEnum.Ignore };
        dollHolder.AddChild(Doll(Loadouts.Of(ch)));
        body.AddChild(dollHolder);
        var right = Style.V(Style.Gap3);
        right.CustomMinimumSize = new Vector2(400, 0);
        right.AddChild(Kit.Head("Wardrobe", null, Style.Label($"{found} of {total} looks found", Style.TextItalic, 15, Kit.Dim, false, HorizontalAlignment.Left, false)));
        right.AddChild(Kit.Tabs(SlotNames, slot, k => { slot = k; Refresh(); }, 16, 22));
        status = Style.Label("", Style.TextItalic, 15, Kit.Ink2, false, HorizontalAlignment.Left, false);
        status.CustomMinimumSize = new Vector2(0, 22);
        right.AddChild(status);
        right.AddChild(Looks(ch));
        if (Slot == "head")
        {
            bool shown = ch.Headgear != false;
            right.AddChild(Nav.Skip(Kit.Word(shown ? "Hide the helm" : "Show the helm", () => { ch.Headgear = !shown; Sound.Sfx.Page(); Refresh(); })));
        }
        right.AddChild(Style.Gap(6));
        right.AddChild(Kit.Head("Dyes"));
        right.AddChild(DyeRows(ch));
        right.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        body.AddChild(right);
        v.AddChild(body);
        v.AddChild(Style.Label("Looks come from gear you have found. They change how you look, never what you wear.", Style.TextItalic, 15, Kit.Dim, true, HorizontalAlignment.Center));
        bool pad = Controls.Instance.UsingPad;
        var p = pad ? Kit.Prompts(Kit.Prompt(Act.Confirm, "Choose"), Kit.Prompt(Act.Cancel, "Back"))
            : Kit.Prompts(Kit.Prompt("Click", "Choose"), Kit.Prompt("Hover", "Preview"), Kit.Prompt("Esc", "Back"));
        p.CustomMinimumSize = new Vector2(0, 30);
        v.AddChild(p);
        Describe(null);
    }

    /* ------------------------------------------------------------- doll -- */

    static Portrait? doll;
    static string dollKey = "";

    /// <summary>Her, whole: kept across a rebuild while she looks the same (her idle never restarted).</summary>
    static Control Doll(Loadout lo)
    {
        var key = Loadouts.Look(lo);
        if (doll != null && IsInstanceValid(doll) && !doll.IsQueuedForDeletion() && key == dollKey && doll.GetParent() is { } was) { was.RemoveChild(doll); return doll; }
        dollKey = key;
        return doll = new Portrait(new Vector2I(DollW, DollH)) { CheckTag = "doll" }.Of(lo);
    }

    /// <summary>Her as she would be with `tweak` applied to the wardrobe (a hover); null puts back what is set.</summary>
    void Preview(Action<CharacterData>? tweak)
    {
        if (dollHolder == null || !IsInstanceValid(dollHolder)) return;
        var ch = Ch;
        Loadout lo;
        if (tweak == null) lo = Loadouts.Of(ch);
        else
        {
            var shown = new Dictionary<string, string>(ch.Shown);
            var dyes = ch.Dyes.ToDictionary(kv => kv.Key, kv => new Dictionary<string, string>(kv.Value));
            tweak(ch);
            lo = Loadouts.Of(ch);
            ch.Shown = shown; ch.Dyes = dyes;
        }
        var next = Doll(lo);
        foreach (var c in dollHolder.GetChildren()) if (c != next) { dollHolder.RemoveChild(c); c.QueueFree(); }
        if (next.GetParent() == null) dollHolder.AddChild(next);
    }

    void Describe(string? text)
    {
        if (status == null || !IsInstanceValid(status)) return;
        if (text == null)
        {
            var ch = Ch;
            var shown = Wardrobe.ShownDef(ch, Slot);
            var own = ch.Equipment[Wardrobe.EquipOf(Slot)];
            text = shown != null ? shown.Name : own != null ? $"Your own: {Items.Get(own.Def).Name}" : "Nothing worn";
        }
        status.Text = text;
    }

    /* ------------------------------------------------------------ looks -- */

    Control Looks(CharacterData ch)
    {
        var grid = new GridContainer { Columns = Cols, MouseFilter = MouseFilterEnum.Ignore };
        grid.AddThemeConstantOverride("h_separation", 6);
        grid.AddThemeConstantOverride("v_separation", 6);
        var shownDef = Wardrobe.ShownDef(ch, Slot);
        // Your own: what is equipped, or an empty place.
        var worn = ch.Equipment[Wardrobe.EquipOf(Slot)];
        var own = ItemViews.Slot(worn, Tile, shownDef == null, null, false, () => Set(null), null, over => { if (over != null) { Preview(c => Wardrobe.SetShown(c, Slot, null)); Describe(worn != null ? $"Your own: {Items.Get(worn.Def).Name}" : "Nothing worn"); } else { Preview(null); Describe(null); } },
            null, null, $"look:own");
        if (worn == null)
        {
            var l = Style.Label("Nothing worn", Style.TextItalic, 12, Kit.Dim, true, HorizontalAlignment.Center);
            l.Size = new Vector2(Tile - 8, Tile - 8); l.Position = new Vector2(4, 22);
            own.AddChild(l);
        }
        own.TooltipText = worn != null ? "Your own" : "Nothing worn";
        grid.AddChild(own);
        foreach (var def in Wardrobe.All(ch, Slot))
        {
            bool have = ch.Looks.Contains(def.Id);
            var inst = Inventory.Make(null, def.Id);
            var id = def.Id;
            var t = ItemViews.Slot(inst, Tile, have && shownDef?.Id == id, null, false, have ? () => Set(id) : null, null,
                have ? over => { if (over != null) { Preview(c => Wardrobe.SetShown(c, Slot, id)); Describe(def.Name); } else { Preview(null); Describe(null); } } : null, null, null, have ? $"look:{id}" : null);
            if (!have)
            {
                // A look not yet found: a dim silhouette, no name.
                foreach (var c in t.GetChildren().OfType<Control>()) c.Modulate = new Color(0, 0, 0, 1);
                t.Modulate = new Color(1, 1, 1, 0.4f);
            }
            else t.TooltipText = def.Name;
            grid.AddChild(t);
        }
        return grid;
    }

    void Set(string? id)
    {
        var at = Slot;
        Sound.Sfx.Equip();
        G.Gear((j, b) => Wardrobe.SetShown(j.Ch, at, id));
    }

    /* ------------------------------------------------------------- dyes -- */

    Control DyeRows(CharacterData ch)
    {
        var v = Style.V(8);
        var zones = Wardrobe.ZonesOfSlot(ch, Slot);
        if (zones.Count == 0) { v.AddChild(Style.Label("Nothing here takes a dye.", Style.TextItalic, 15, Kit.Dim)); return v; }
        var offered = Wardrobe.Offered(ch);
        foreach (var zone in zones)
        {
            var z = zone;
            ch.Dyes.TryGetValue(Slot, out var set);
            string? now = set != null && set.TryGetValue(z, out var cur) ? cur : null;
            var row = Style.H(8);
            var name = Style.Label(ZoneNames.GetValueOrDefault(z, z), Style.Ui, 16, Kit.Ink2, false, HorizontalAlignment.Left, false);
            name.CustomMinimumSize = new Vector2(70, 0);
            name.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            row.AddChild(name);
            var sw = new HFlowContainer { SizeFlagsHorizontal = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore };
            sw.AddThemeConstantOverride("h_separation", 6);
            sw.AddThemeConstantOverride("v_separation", 6);
            sw.AddChild(MakeSwatch(MadeColour(ch, z), null, "As made", now == null, true, () => { Wardrobe.SetDye(ch, Slot, z, null); Changed(); }, over => Hover(over, "As made", c => Wardrobe.SetDye(c, Slot, z, null))));
            foreach (var d in offered.Where(d => d.Zones.Contains(z)))
            {
                var dd = d;
                sw.AddChild(MakeSwatch(new Color(Wear.DyeFinish(d.Hex).Hex), null, d.Name, now == d.Id, false, () => { Wardrobe.SetDye(ch, Slot, z, dd.Id); Changed(); }, over => Hover(over, dd.Name, c => Wardrobe.SetDye(c, Slot, z, dd.Id))));
            }
            row.AddChild(sw);
            v.AddChild(row);
        }
        return v;
    }

    void Hover(bool over, string name, Action<CharacterData> tweak)
    {
        if (over) { Preview(tweak); Describe(name); } else { Preview(null); Describe(null); }
    }

    void Changed() { Sound.Sfx.Page(); G.Gear((j, b) => { }); }

    /// <summary>The colour a zone has as made: the equipped item's own dye for it, else the zone's usual.</summary>
    Color MadeColour(CharacterData ch, string zone)
    {
        var worn = ch.Equipment[Wardrobe.EquipOf(Slot)];
        if (worn?.Dye != null && worn.Dye.TryGetValue(zone, out var h)) return new Color(Wear.DyeFinish(h).Hex);
        return ZoneMade.GetValueOrDefault(zone, new Color("#777777"));
    }

    static Control MakeSwatch(Color colour, string? _, string name, bool set, bool asMade, Action press, Action<bool> hover)
    {
        var s = new DyeSwatch { Colour = colour, Set = set, AsMade = asMade, TooltipText = name, CustomMinimumSize = new Vector2(Swatch, Swatch), MouseDefaultCursorShape = Control.CursorShape.PointingHand };
        s.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) press(); };
        s.MouseEntered += () => hover(true);
        s.MouseExited += () => hover(false);
        return s;
    }
}

/// <summary>A round dye swatch, 26 px; the one set has a 2 px ember ring, "As made" a thin diagonal.</summary>
public partial class DyeSwatch : Control
{
    public Color Colour;
    public bool Set, AsMade;

    public override void _Draw()
    {
        var c = Size / 2;
        float r = Math.Min(Size.X, Size.Y) / 2 - 3;
        DrawCircle(c, r, Colour);
        DrawArc(c, r, 0, Mathf.Tau, 32, new Color(0, 0, 0, 0.55f), 1, true);
        if (AsMade) DrawLine(c + new Vector2(-r * 0.7f, r * 0.7f), c + new Vector2(r * 0.7f, -r * 0.7f), new Color(0.95f, 0.92f, 0.85f, 0.9f), 1.2f, true);
        if (Set) DrawArc(c, r + 2, 0, Mathf.Tau, 40, Style.Ember, 2, true);
    }
}
