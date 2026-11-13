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
/// Her, the world's, beside the page (a hover over a look or a dye previews it on her after 120 ms); on the page the places, the looks as
/// 96 px thumbnails, and a row of swatches for each zone the shown piece has. Esc goes back to the Pack.
/// </summary>
public partial class WardrobeScreen : Overlay
{
    public override string Kind => "wardrobe";
    public override bool Dismissable => false;
    // One her: the world's, framed low and tall beside the panel (W22). --ward-frame P,D,H,SHIFT tries another.
    public override float CameraShift => WardFrame.Shift;
    public override float CameraNear => 0.56f;
    // Head has its own frame (a tall hat keeps its tip in view, her chin near the middle); Body and Feet keep WardFrame. The screen
    // re-applies it when the tab changes (Game.Reframe).
    public override (float Pitch, float Distance, float Height)? CameraFrame => slot == 0 ? HeadFrame : (WardFrame.Pitch, WardFrame.Distance, WardFrame.Height);
    static (float Pitch, float Distance, float Height) HeadFrame => Args.Get("head-frame") is string f && f.Split(',') is [var p, var d, var h]
        ? (Pf(p), Pf(d), Pf(h)) : (8, 2.0f, 1.75f);
    protected override string CloseWord => "Back";

    static (float Pitch, float Distance, float Height, float Shift) WardFrame => Args.Get("ward-frame") is string f && f.Split(',') is [var p, var d, var h, var sh]
        ? (Pf(p), Pf(d), Pf(h), Pf(sh)) : (12, 3.9f, 0.95f, -460);
    static float Pf(string s) => float.Parse(s, System.Globalization.CultureInfo.InvariantCulture);

    const int Tile = 112, Cols = 7, Swatch = 34;
    static readonly string[] SlotNames = ["Head", "Body", "Feet"];
    static readonly Dictionary<string, string> ZoneNames = new() { ["metal"] = "Metal", ["trim"] = "Trim", ["leather"] = "Leather", ["cloth"] = "Cloth" };
    // What a zone looks like as made, when the piece names no dye of its own for it.
    static readonly Dictionary<string, Color> ZoneMade = new()
    {
        ["metal"] = new Color("#8a8f98"), ["trim"] = new Color("#b08a3a"), ["leather"] = new Color("#5a3a28"), ["cloth"] = new Color("#6a665c"),
    };

    static int slot = -1;
    Label? status;
    // A hover shows on the world her after a rest of 120 ms (a re-dress per pass would stutter).
    Action<CharacterData>? want;
    bool wantDirty;
    double rest;

    public WardrobeScreen(Game g) : base(g)
    {
        if (Args.Get("wardrobe-slot") is string s && Array.IndexOf(Wardrobe.LookSlots, s) is var i and >= 0) slot = i;
        if (slot < 0) slot = 1;
        // Her sword and shield away while the wardrobe is open (put back in _ExitTree).
        Loadouts.ArmsAway = true;
    }

    CameraAttributes? lensWas;
    bool dofSet;
    ColorRect? blur;

    /// <summary>A far depth of field on the world camera while open (blur from 1.5 m past her, a 4 m transition, amount 0.08); the camera's own put back on close.</summary>
    void Dof()
    {
        if (!dofSet) { lensWas = G.WorldLens; dofSet = true; }
        float reach = CameraFrame?.Distance ?? 3.9f;
        G.WorldLens = new CameraAttributesPractical
        {
            DofBlurFarEnabled = true, DofBlurFarDistance = reach + 1.5f, DofBlurFarTransition = 4f, DofBlurAmount = 0.08f,
        };
    }

    public override void _ExitTree()
    {
        Loadouts.ArmsAway = false;
        if (dofSet) G.WorldLens = lensWas;
        if (G.Scene is { } sc && IsInstanceValid(sc)) sc.SetLoadout(Loadouts.Of(Ch));
    }

    public override void _Process(double delta)
    {
        if (!wantDirty) return;
        rest += delta;
        if (rest < 0.12) return;
        wantDirty = false;
        ApplyWorld(want);
    }

    static readonly Shader BlurShader = new()
    {
        Code = @"shader_type canvas_item;
uniform sampler2D screen : hint_screen_texture, filter_linear;
void fragment() {
    vec2 px = 1.0 / vec2(textureSize(screen, 0));
    vec3 c = texture(screen, SCREEN_UV).rgb;
    float w = 1.0;
    for (int i = 0; i < 12; i++) {
        float a = float(i) * 0.5236 * 2.0;
        float r = (i % 2 == 0) ? 6.0 : 3.0;
        c += texture(screen, SCREEN_UV + vec2(cos(a), sin(a)) * r * px).rgb;
        w += 1.0;
    }
    COLOR = vec4(c / w, 1.0);
}",
    };

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
        LookThumbs.Prefetch(ch, Tile - 4);
        var v = BookPanel(null, () => G.Open("inventory"));
        Dof();
        // A 6 px blur of what is behind the page, under the panel.
        if (v.GetParent() is Control panel)
        {
            blur = new ColorRect { Color = Colors.White, MouseFilter = MouseFilterEnum.Ignore, Material = new ShaderMaterial { Shader = BlurShader } };
            AddChild(blur);
            MoveChild(blur, panel.GetIndex());
            void Fit() { blur.Position = panel.Position; blur.Size = panel.Size; }
            panel.Resized += Fit;
            Fit();
        }
        var (found, total) = Wardrobe.Count(ch);
        var names = Wardrobe.LookSlots.Select((s, i) => $"{SlotNames[i]} {Wardrobe.Found(ch, s).Count}/{Wardrobe.All(ch, s).Count}").ToArray();
        v.AddChild(Kit.Head("Wardrobe", null, Style.Label($"{found} of {total} looks in all", Style.TextItalic, 15, Kit.Dim, false, HorizontalAlignment.Left, false)));
        v.AddChild(Kit.Tabs(names, slot, k => { slot = k; want = null; wantDirty = false; ApplyWorld(null); G.Reframe(this); Refresh(); }, 16, 22));
        // The shown look's name is the page's title; under it, what it is worn over.
        var shownDef = Wardrobe.ShownDef(ch, Slot);
        var own = ch.Equipment[Wardrobe.EquipOf(Slot)];
        var ownName = own != null ? Items.Get(own.Def).Name : null;
        v.AddChild(Style.Label((shownDef?.Name ?? ownName ?? "Nothing worn").ToUpperInvariant(), Style.Display, 28, shownDef != null ? Style.EmberHi : Kit.Ink, false, HorizontalAlignment.Left, false));
        v.AddChild(Style.Label(shownDef == null ? "your own piece, as it is" : ownName != null ? $"over: {ownName}" : "over nothing", Style.TextItalic, 14, Kit.Dim, false, HorizontalAlignment.Left, false));
        status = Style.Label("", Style.TextItalic, 15, Kit.Ink2, false, HorizontalAlignment.Left, false);
        status.CustomMinimumSize = new Vector2(0, 22);
        v.AddChild(status);
        v.AddChild(Looks(ch));
        if (Slot == "head")
        {
            bool on = ch.Headgear != false;
            v.AddChild(Nav.Skip(TickRow("Show headgear", on, () => { ch.Headgear = !on; Sound.Sfx.Page(); G.Gear((j, b) => { }); })));
        }
        v.AddChild(Style.Gap(8));
        v.AddChild(Kit.Head("Dyes"));
        v.AddChild(DyeRows(ch));
        v.AddChild(Style.Gap(6));
        v.AddChild(Style.Label("Every piece you find adds its look here. Looks change how you look, never what your gear does.", Style.TextItalic, 15, Kit.Dim, true, HorizontalAlignment.Center));
        bool pad = Controls.Instance.UsingPad;
        var p = pad ? Kit.Prompts(Kit.Prompt(Act.Confirm, "Choose"), Kit.Prompt(Act.Cancel, "Back"))
            : Kit.Prompts(Kit.Prompt("Click", "Choose"), Kit.Prompt("Hover", "Preview"), Kit.Prompt("Esc", "Back"));
        p.CustomMinimumSize = new Vector2(0, 30);
        v.AddChild(p);
        Describe(null);
        ApplyWorld(null);
    }

    /* ---------------------------------------------------------- her, world -- */

    /// <summary>Her, in the world, as she would be with `tweak` applied to the wardrobe (a hover); null puts back what is set.</summary>
    void ApplyWorld(Action<CharacterData>? tweak)
    {
        if (G.Scene is not { } sc || !IsInstanceValid(sc)) return;
        var ch = Ch;
        if (tweak == null) { sc.SetLoadout(Loadouts.Of(ch)); return; }
        var shown = new Dictionary<string, string>(ch.Shown);
        var dyes = ch.Dyes.ToDictionary(kv => kv.Key, kv => new Dictionary<string, string>(kv.Value));
        tweak(ch);
        var lo = Loadouts.Of(ch);
        ch.Shown = shown; ch.Dyes = dyes;
        sc.SetLoadout(lo);
    }

    void Preview(Action<CharacterData>? tweak)
    {
        want = tweak; wantDirty = true; rest = 0;
    }

    void Describe(string? text)
    {
        if (status == null || !IsInstanceValid(status)) return;
        if (text == null)
        {
            var ch = Ch;
            text = Slot == "head" && ch.Headgear == false ? "Headgear hidden" : "";
        }
        status.Text = text;
    }

    /* ------------------------------------------------------------ looks -- */

    Control Looks(CharacterData ch)
    {
        var grid = new GridContainer { Columns = Cols, MouseFilter = MouseFilterEnum.Ignore };
        grid.AddThemeConstantOverride("h_separation", 10);
        grid.AddThemeConstantOverride("v_separation", 10);
        var shownDef = Wardrobe.ShownDef(ch, Slot);
        bool hidden = Slot == "head" && ch.Headgear == false;
        // Your own first: what is equipped, or an empty place. A look has no level and no rarity.
        var worn = ch.Equipment[Wardrobe.EquipOf(Slot)];
        var ownDef = worn != null ? Items.Get(worn.Def) : null;
        grid.AddChild(LookTile(ownDef, Slot, worn != null ? "Your own" : "Nothing worn", shownDef == null, true, hidden && shownDef == null, true,
            () => Set(null), over => { if (over) { Preview(c => Wardrobe.SetShown(c, Slot, null)); Describe(worn != null ? $"Your own: {ownDef!.Name}" : "Nothing worn"); } else { Preview(null); Describe(null); } },
            "look:own", worn != null ? "Your own" : "Nothing worn"));
        // Then the found looks, then the ones not yet found.
        foreach (var def in Wardrobe.All(ch, Slot).OrderBy(d => ch.Looks.Contains(d.Id) ? 0 : 1))
        {
            bool have = ch.Looks.Contains(def.Id);
            var id = def.Id;
            bool sel = have && shownDef?.Id == id;
            grid.AddChild(LookTile(def, Slot, null, sel, have, hidden && sel, false, have ? () => Set(id) : null,
                have ? over => { if (over) { Preview(c => Wardrobe.SetShown(c, Slot, id)); Describe(def.Name); } else { Preview(null); Describe(null); } } : null,
                have ? $"look:{id}" : null, have ? def.Name : null));
        }
        return grid;
    }

    /// <summary>A look's tile, 96 px: a dark neutral fill, a 1 px quiet line, the look worn (LookThumbs); no level, rarity, badge or
    /// count. Selected is an ember frame, hover a 6% white fill; not found is the same picture dim and desaturated with a lock.</summary>
    static Control LookTile(ItemDef? def, string slot, string? caption, bool selected, bool found, bool crossed, bool own, Action? press, Action<bool>? hover, string? navId, string? tip)
    {
        var box = new Panel { CustomMinimumSize = new Vector2(Tile, Tile), MouseFilter = Control.MouseFilterEnum.Stop };
        var sb = new StyleBoxFlat { BgColor = Kit.Tile };
        sb.SetCornerRadiusAll(4);
        sb.SetBorderWidthAll(selected ? 2 : 1);
        sb.BorderColor = selected ? Style.Ember : Kit.Rule;
        box.AddThemeStyleboxOverride("panel", sb);
        if (def != null || own)
        {
            Control pic = own ? LookThumbs.For(def?.Id ?? "none", slot, Tile - 4, false, true) : LookThumbs.For(def!.Id, slot, Tile - 4, !found);
            pic.Position = new Vector2(2, 2);
            pic.Size = new Vector2(Tile - 4, Tile - 4);
            pic.MouseFilter = Control.MouseFilterEnum.Ignore;
            box.AddChild(pic);
        }
        if (caption != null)
        {
            if (def != null || own)
            {
                var strip = new ColorRect { Color = new Color(0, 0, 0, 0.55f), Position = new Vector2(2, Tile - 20), Size = new Vector2(Tile - 4, 18), MouseFilter = Control.MouseFilterEnum.Ignore };
                box.AddChild(strip);
            }
            var l = Style.Label(caption, Style.TextItalic, 12, Kit.Ink2, false, HorizontalAlignment.Center, false);
            l.Size = new Vector2(Tile, 16);
            l.Position = new Vector2(0, Tile - 19);
            l.MouseFilter = Control.MouseFilterEnum.Ignore;
            box.AddChild(l);
        }
        if (!found)
        {
            var lk = Glyphs.Icon("lock", 18, Kit.Ink2);
            lk.Modulate = new Color(1, 1, 1, 0.8f);
            lk.Position = new Vector2(Tile - 18 - 5, Tile - 18 - 5);
            lk.Size = new Vector2(18, 18);
            lk.MouseFilter = Control.MouseFilterEnum.Ignore;
            box.AddChild(lk);
        }
        if (crossed)
        {
            var eye = new EyeBadge { Position = new Vector2(Tile - 20 - 5, 5), Size = new Vector2(20, 20), MouseFilter = Control.MouseFilterEnum.Ignore };
            box.AddChild(eye);
        }
        if (found)
        {
            var wash = new ColorRect { Color = new Color(1, 1, 1, 0.06f), Visible = false, MouseFilter = Control.MouseFilterEnum.Ignore };
            wash.SetAnchorsPreset(Control.LayoutPreset.FullRect);
            box.AddChild(wash);
            box.MouseEntered += () => { wash.Visible = true; hover?.Invoke(true); };
            box.MouseExited += () => { wash.Visible = false; hover?.Invoke(false); };
            box.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) press?.Invoke(); };
            box.MouseDefaultCursorShape = Control.CursorShape.PointingHand;
            if (navId != null) Nav.Mark(box, navId, press ?? (() => { }), null, null, () => hover?.Invoke(true), () => hover?.Invoke(false));
        }
        if (tip != null) box.TooltipText = tip;
        return box;
    }

    /// <summary>A left-aligned tick row: an 18 px box (ticked = shown) and its words.</summary>
    static Control TickRow(string text, bool on, Action press)
    {
        var row = Style.H(10);
        row.MouseFilter = MouseFilterEnum.Stop;
        row.MouseDefaultCursorShape = Control.CursorShape.PointingHand;
        var box = new TickBox { On = on, CustomMinimumSize = new Vector2(18, 18), SizeFlagsVertical = SizeFlags.ShrinkCenter, MouseFilter = MouseFilterEnum.Ignore };
        var l = Style.Label(text, Style.Ui, 16, Kit.Ink2, false, HorizontalAlignment.Left, false);
        l.MouseFilter = MouseFilterEnum.Ignore;
        row.AddChild(box);
        row.AddChild(l);
        row.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) press(); };
        return row;
    }

    void Set(string? id)
    {
        var at = Slot;
        Sound.Sfx.Equip();
        want = null; wantDirty = false;
        G.Gear((j, b) => Wardrobe.SetShown(j.Ch, at, id));
    }

    /* ------------------------------------------------------------- dyes -- */

    Control DyeRows(CharacterData ch)
    {
        var v = Style.V(10);
        var zones = Wardrobe.ZonesOfSlot(ch, Slot);
        if (zones.Count == 0) { v.AddChild(Style.Label("Nothing here takes a dye.", Style.TextItalic, 15, Kit.Dim)); return v; }
        var offered = Wardrobe.Offered(ch);
        bool hiddenHat = Slot == "head" && ch.Headgear == false;
        foreach (var zone in zones)
        {
            var z = zone;
            ch.Dyes.TryGetValue(Slot, out var set);
            string? now = set != null && set.TryGetValue(z, out var cur) ? cur : null;
            var row = Style.H(16);
            if (hiddenHat) row.Modulate = new Color(1, 1, 1, 0.45f);
            var name = Style.Label(ZoneNames.GetValueOrDefault(z, z) + (hiddenHat ? " (hidden)" : ""), Style.Ui, 16, Kit.Ink2, false, HorizontalAlignment.Left, false);
            name.CustomMinimumSize = new Vector2(hiddenHat ? 150 : 70, 0);
            name.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            row.AddChild(name);
            var sw = new HFlowContainer { CustomMinimumSize = new Vector2(202, 0), SizeFlagsVertical = SizeFlags.ShrinkCenter, MouseFilter = MouseFilterEnum.Ignore };
            sw.AddThemeConstantOverride("h_separation", 8);
            sw.AddThemeConstantOverride("v_separation", 8);
            sw.AddChild(MakeSwatch(MadeColour(ch, z), false, "As made", now == null, true, () => { Wardrobe.SetDye(ch, Slot, z, null); Changed(); }, over => Hover(over, "As made", c => Wardrobe.SetDye(c, Slot, z, null))));
            foreach (var d in offered.Where(d => d.Zones.Contains(z)))
            {
                var dd = d;
                var fin = Wear.DyeFinish(d.Hex);
                sw.AddChild(MakeSwatch(new Color(fin.Hex), fin.Metal, d.Name, now == d.Id, false, () => { Wardrobe.SetDye(ch, Slot, z, dd.Id); Changed(); }, over => Hover(over, dd.Name, c => Wardrobe.SetDye(c, Slot, z, dd.Id))));
            }
            row.AddChild(sw);
            var chosen = now == null ? "As made" : Wardrobe.Dye(now)?.Name ?? now;
            var cn = Style.Label(chosen, Style.Ui, 16, Kit.Ink2, false, HorizontalAlignment.Left, false);
            cn.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            row.AddChild(cn);
            v.AddChild(row);
        }
        return v;
    }

    void Hover(bool over, string name, Action<CharacterData> tweak)
    {
        if (over) { Preview(tweak); Describe(name); } else { Preview(null); Describe(null); }
    }

    void Changed() { Sound.Sfx.Page(); want = null; wantDirty = false; G.Gear((j, b) => { }); }

    /// <summary>The colour a zone has as made: the equipped item's own dye for it, else the zone's usual.</summary>
    Color MadeColour(CharacterData ch, string zone)
    {
        var worn = ch.Equipment[Wardrobe.EquipOf(Slot)];
        if (worn?.Dye != null && worn.Dye.TryGetValue(zone, out var h)) return new Color(Wear.DyeFinish(h).Hex);
        return ZoneMade.GetValueOrDefault(zone, new Color("#777777"));
    }

    static Control MakeSwatch(Color colour, bool metal, string name, bool set, bool asMade, Action press, Action<bool> hover)
    {
        var s = new DyeSwatch { Colour = colour, Metal = metal, Set = set, AsMade = asMade, TooltipText = name, CustomMinimumSize = new Vector2(Swatch, Swatch), MouseDefaultCursorShape = Control.CursorShape.PointingHand };
        s.GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) press(); };
        s.MouseEntered += () => hover(true);
        s.MouseExited += () => hover(false);
        return s;
    }
}

/// <summary>A round dye swatch in a 34 px control (a 28 px disc, 1 px light outline); the one set has a 2.5 px ember ring four px out
/// with a 2 px dark gap; metals a soft top-left highlight; "As made" a thin diagonal.</summary>
public partial class DyeSwatch : Control
{
    public Color Colour;
    public bool Set, AsMade, Metal;

    public override void _Draw()
    {
        var c = Size / 2;
        const float r = 14;
        DrawCircle(c, r, Colour);
        if (Metal)
            for (int i = 0; i < 6; i++)
            {
                float k = i / 6f;
                DrawCircle(c + new Vector2(-4, -4) * k - new Vector2(1, 1), r * 0.7f * (1 - k) + 1, new Color(1, 1, 1, 0.35f / 6f * 1.5f));
            }
        DrawArc(c, r, 0, Mathf.Tau, 40, new Color(1, 0.94f, 0.86f, 0.22f), 1, true);
        if (AsMade) DrawLine(c + new Vector2(-r * 0.7f, r * 0.7f), c + new Vector2(r * 0.7f, -r * 0.7f), new Color(0.95f, 0.92f, 0.85f, 0.9f), 1.2f, true);
        if (Set)
        {
            DrawArc(c, r + 2, 0, Mathf.Tau, 48, new Color("#120d0a"), 2, true);
            DrawArc(c, r + 4, 0, Mathf.Tau, 48, Style.Ember, 2.5f, true);
        }
    }
}

/// <summary>An 18 px tick box: a quiet frame, an ember tick when on.</summary>
public partial class TickBox : Control
{
    public bool On;

    public override void _Draw()
    {
        DrawRect(new Rect2(0.5f, 0.5f, Size.X - 1, Size.Y - 1), new Color("#111012"), true);
        DrawRect(new Rect2(0.5f, 0.5f, Size.X - 1, Size.Y - 1), On ? Style.Ember : Kit.Dim, false, 1.5f);
        if (On)
        {
            DrawLine(new Vector2(4, 9.5f), new Vector2(7.7f, 13), Style.Ember, 2.2f, true);
            DrawLine(new Vector2(7.7f, 13), new Vector2(14, 5), Style.Ember, 2.2f, true);
        }
    }
}

/// <summary>A 16 px crossed eye: the look is chosen but hidden.</summary>
public partial class EyeBadge : Control
{
    public override void _Draw()
    {
        DrawRect(new Rect2(Vector2.Zero, Size), new Color(0, 0, 0, 0.55f), true);
        var c = Size / 2; float k = Size.X / 16f;
        var pts = new List<Vector2>();
        for (int i = 0; i <= 8; i++) { float t = i / 8f * 2 - 1; pts.Add(c + new Vector2(t * 6.5f * k, -3.2f * k * (1 - t * t))); }
        for (int i = 1; i <= 8; i++) { float t = 1 - i / 8f * 2; pts.Add(c + new Vector2(t * 6.5f * k, 3.2f * k * (1 - t * t))); }
        DrawPolyline(pts.ToArray(), Kit.Ink, 1.2f, true);
        DrawCircle(c, 1.6f * k, Kit.Ink);
        DrawLine(new Vector2(2.5f, 13.5f) * k, new Vector2(13.5f, 2.5f) * k, Style.Ember, 1.6f, true);
    }
}
