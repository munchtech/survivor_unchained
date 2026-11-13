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
    // (the head tab leans on a little more: its hat and head are centred in x 0-967 by what the camera sees, HeadTarget)
    public override float CameraShift => slot == 0 && headShift is float hs ? hs : WardFrame.Shift;
    float? headShift;
    public override float CameraNear => 0.56f;
    // Head has its own frame (a tall hat keeps its tip in view, her chin near the middle); Body and Feet keep WardFrame. The screen
    // re-applies it when the tab changes (Game.Reframe).
    public override (float Pitch, float Distance, float Height)? CameraFrame => slot == 0 ? headNow ?? HeadFrame : (WardFrame.Pitch, WardFrame.Distance, WardFrame.Height);
    // The head tab's frame, worked out from what she wears (HeadTarget) and eased to (250 ms): the hat's bounds plus head to collarbone fill 62% of the
    // height, the brim no wider than 860 px; headgear off, head to collarbone by the same rule.
    (float Pitch, float Distance, float Height)? headNow;
    static (float Pitch, float Distance, float Height) HeadFrame => Args.Get("head-frame") is string f && f.Split(',') is [var p, var d, var h]
        ? (Pf(p), Pf(d), Pf(h)) : (8, 1.5f, 1.65f);
    protected override string CloseWord => "Back";

    static (float Pitch, float Distance, float Height, float Shift) WardFrame => Args.Get("ward-frame") is string f && f.Split(',') is [var p, var d, var h, var sh]
        ? (Pf(p), Pf(d), Pf(h), Pf(sh)) : (12, 3.9f, 0.95f, -477);
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

    bool opened;
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
        if (slot == 0 && HeadTarget() is { } tg)
        {
            var cur = headNow ?? HeadFrame;
            float k = 1 - Mathf.Exp(-(float)delta * 12f);
            var next = (Mathf.Lerp(cur.Pitch, tg.Pitch, k), Mathf.Lerp(cur.Distance, tg.Distance, k), Mathf.Lerp(cur.Height, tg.Height, k));
            headShift = Mathf.Lerp(headShift ?? WardFrame.Shift, tg.Shift, k);
            if (headNow == null || Mathf.Abs(next.Item2 - cur.Distance) > 0.0005f || Mathf.Abs(next.Item3 - cur.Height) > 0.0005f) { headNow = next; G.Reframe(this); }
            else if (Mathf.Abs(tg.Shift - (headShift ?? 0)) > 0.5f) G.Reframe(this);
        }
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

    /// <summary>The head frame for what she wears now, from the world's her: the highest mesh (hat tip, else hair) to her collarbone is 62% of the frame's
    /// height, and the widest of what sits at the head (a brim) is at most 860 px of it; the aim is the middle of that span. Null until she stands in the world.</summary>
    (float Pitch, float Distance, float Height, float Shift)? HeadTarget()
    {
        if (G.Scene?.Player is not { } pv || !IsInstanceValid(pv) || !pv.IsInsideTree() || GetViewport()?.GetCamera3D() is not { } cam) return null;
        var sk = pv.Person.Skeleton;
        if (sk == null) return null;
        int hi = sk.FindBone("Head"), ci = sk.FindBone("clavicle_l"), ni = sk.FindBone("Neck");
        if (hi < 0) return null;
        float Y(int i) => (sk.GlobalTransform * sk.GetBoneGlobalPose(i).Origin).Y;
        float headY = Y(hi);
        // (her collarbone: the neck's root; the clavicle bone's own origin sits down at the shoulder)
        float collar = ci >= 0 ? Y(ci) + 0.12f : ni >= 0 ? Y(ni) - 0.02f : headY - 0.25f;
        // (measured on the screen as the camera sees it now, and the distance scaled by how far off it is: the size on screen goes
        // as one over the distance, so this settles where the larger of the two is exactly at its mark; a prediction from the
        // meshes' sizes alone put the brim at 910 px, the hat nearer the lens than the aim)
        float rows = GetViewport().GetVisibleRect().Size.Y / 1080f;
        float tip = headY + 0.15f, top = float.MaxValue, x0 = float.MaxValue, x1 = float.MinValue;
        Aabb? group = null;
        foreach (var n in pv.FindChildren("*", "MeshInstance3D", true, false))
        {
            if (n is not MeshInstance3D { Mesh: not null } mi || !mi.IsVisibleInTree()) continue;
            var box = mi.GlobalTransform * mi.GetAabb();
            tip = Mathf.Max(tip, box.End.Y);
            if (box.Position.Y < headY - 0.12f) continue;
            group = group is { } g ? g.Merge(box) : box;
            for (int c = 0; c < 8; c++)
            {
                var q = box.GetEndpoint(c);
                if (cam.IsPositionBehind(q)) continue;
                var sp = cam.UnprojectPosition(q) / rows;
                top = Mathf.Min(top, sp.Y); x0 = Mathf.Min(x0, sp.X); x1 = Mathf.Max(x1, sp.X);
            }
        }
        var headP = sk.GlobalTransform * sk.GetBoneGlobalPose(hi).Origin;
        float bottom = cam.UnprojectPosition(new Vector3(headP.X, collar, headP.Z)).Y / rows;
        float cur = (headNow ?? HeadFrame).Distance;
        float off = top < bottom && x1 > x0 ? Mathf.Max((bottom - top) / ((group is { } hg && hg.End.Y > headY + 0.3f ? 0.62f : 0.45f) * 1080f), (x1 - x0) / 835f) : 1f;
        // (bare-headed, head to collarbone at 62% was a face filling the frame: 45%, her shoulders in)
        float d = Mathf.Clamp(cur * off, 0.8f, 4.5f);
        float centre = (tip + collar) / 2 - pv.GlobalPosition.Y;
        // (the height corrected from where the middle of the tip-to-collarbone span lands on the screen now: aim y540, the middle of the frame; the
        // error in metres at that depth is taken off the camera's height each frame, so it settles with the ease and holds in both states)
        {
            var spanMid = new Vector3(headP.X, (tip + collar) / 2, headP.Z);
            float depthM = -(cam.GlobalTransform.AffineInverse() * spanMid).Z;
            float perPxM = 2 * depthM * Mathf.Tan(Mathf.DegToRad(cam.Fov) / 2) / GetViewport().GetVisibleRect().Size.Y;
            float errPx = cam.UnprojectPosition(spanMid).Y / rows - 540f;
            float curH = (headNow ?? HeadFrame).Height;
            if (depthM > 0.1f && !float.IsNaN(errPx)) centre = curH - errPx * rows * perPxM;
        }
        // (the shift that puts the head's middle at x 483.5, the middle of the free ground: where it is on screen now, less the camera's own
        // sideways offset, tells where it would be with none; no feedback on the camera's easing)
        float shift = WardFrame.Shift;
        if (group is { } gb)
        {
            var mid = gb.GetCenter();
            float depth = -(cam.GlobalTransform.AffineInverse() * mid).Z;
            float perPx = 2 * depth * Mathf.Tan(Mathf.DegToRad(cam.Fov) / 2) / GetViewport().GetVisibleRect().Size.Y;
            float zeroX = (cam.UnprojectPosition(mid).X + cam.HOffset / perPx) / rows;
            shift = 483.5f - zeroX;
        }
        return (8, d, centre, shift);
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
        LookThumbs.Prefetch(ch, Tile - 4);
        var v = Page();
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
        v.AddChild(Kit.Tabs(names, slot, k => { slot = k; want = null; wantDirty = false; ApplyWorld(null, true); G.Reframe(this); Refresh(); }, 16, 22));
        // The shown look's name is the page's title; under it, what it is worn over.
        var shownDef = Wardrobe.ShownDef(ch, Slot);
        var own = ch.Equipment[Wardrobe.EquipOf(Slot)];
        var ownName = own != null ? Items.Get(own.Def).Name : null;
        bool ownLook = Wardrobe.OwnHasLook(ch, Slot);
        // (a piece with no look of its own draws her calling's kit: the title is what is drawn, the found look that draws the same)
        var drawnName = shownDef == null && own != null && !ownLook ? Wardrobe.OwnLook(ch, Slot)?.Name : null;
        v.AddChild(Style.Label((shownDef?.Name ?? drawnName ?? ownName ?? "Nothing worn").ToUpperInvariant(), Style.Display, 28, shownDef != null ? Style.EmberHi : Kit.Ink, false, HorizontalAlignment.Left, false));
        v.AddChild(Style.Label(shownDef == null
            ? (ownName == null || ownLook ? "your own piece, as it is" : drawnName != null ? $"your own: {ownName} (no look of its own)" : "your own piece (no look of its own)")
            : ownName == null ? "over nothing" : ownLook ? $"over: {ownName}" : $"over: {ownName} (no look of its own)", Style.TextItalic, 14, Kit.Dim, false, HorizontalAlignment.Left, false));
        status = Style.Label("", Style.TextItalic, 15, Kit.Ink2, false, HorizontalAlignment.Left, false);
        status.CustomMinimumSize = new Vector2(0, 22);
        v.AddChild(status);
        // (two rows of tiles and the tick's row are always kept, so the dyes begin at the same y on every tab)
        var tiles = Style.V(0);
        tiles.CustomMinimumSize = new Vector2(0, Tile * 2 + 10);
        tiles.AddChild(Looks(ch));
        v.AddChild(tiles);
        var tick = Style.V(0);
        tick.CustomMinimumSize = new Vector2(0, 28);
        if (Slot == "head")
        {
            bool on = ch.Headgear != false;
            tick.AddChild(Nav.Skip(TickRow("Show headgear", on, () => { ch.Headgear = !on; Sound.Sfx.Page(); G.Gear((j, b) => { }); })));
        }
        v.AddChild(tick);
        v.AddChild(Style.Gap(8));
        v.AddChild(Kit.Head("Dyes"));
        v.AddChild(DyeRows(ch));
        // (the footer is pinned to the foot of the panel)
        v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        v.AddChild(Style.Label("Every piece you find adds its look here. Looks change how you look, never what your gear does.", Style.TextItalic, 15, Kit.Dim, true, HorizontalAlignment.Center));
        bool pad = Controls.Instance.UsingPad;
        var p = pad ? Kit.Prompts(Kit.Prompt(Act.Confirm, "Choose"), Kit.Prompt(Act.Cancel, "Back"))
            : Kit.Prompts(Kit.Prompt("Click", "Choose"), Kit.Prompt("Hover", "Preview"), Kit.Prompt("Esc", "Back"));
        p.CustomMinimumSize = new Vector2(0, 30);
        v.AddChild(Style.Gap(6));
        v.AddChild(p);
        v.AddChild(Style.Gap(PanelFoot - Margin));
        Describe(null);
        // On open her sword and shield go away at once (a swap dressed over frames would leave them in view for a while).
        ApplyWorld(null, !opened);
        opened = true;
    }

    /// <summary>The one panel, the same rect on every tab and look (x967-1872, y120-960), and behind it a black gradient from nothing at x900 to half
    /// at the right edge, so the panel sits on calm ground. Returns its column.</summary>
    VBoxContainer Page()
    {
        HideHud();
        var shade = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(0, 0, 0, 0), new Color(0, 0, 0, 0.5f) }, Offsets = new[] { 0f, 1f } },
                Width = 256, Height = 4,
            },
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
            Position = new Vector2(900, 0), Size = new Vector2(1020, 1080),
        };
        AddChild(shade);
        var panel = Style.Panel(Kit.Window(Margin, Margin, Margin));
        panel.Position = new Vector2(PanelX, PanelY);
        panel.CustomMinimumSize = new Vector2(PanelW, PanelH);
        panel.Size = new Vector2(PanelW, PanelH);
        panel.MouseFilter = MouseFilterEnum.Stop;
        panel.SelfModulate = Colors.White with { A = GroundAlpha };
        AddChild(panel);
        var v = Style.V(Style.Gap3);
        panel.AddChild(v);
        if (Args.Get("ward-log") != null) panel.Resized += () => GD.Print($"WARD panel rect {panel.GlobalPosition.X},{panel.GlobalPosition.Y} {panel.Size.X}x{panel.Size.Y}");
        return v;
    }

    const float PanelX = 967, PanelY = 120, PanelW = 905, PanelH = 840;
    // The footer's foot is this far above the panel's bottom (the margin inside it, and the rest).
    const float PanelFoot = 45;

    /* ---------------------------------------------------------- her, world -- */

    /// <summary>Her, in the world, as she would be with `tweak` applied to the wardrobe (a hover); null puts back what is set.</summary>
    void ApplyWorld(Action<CharacterData>? tweak, bool now = false)
    {
        if (G.Scene is not { } sc || !IsInstanceValid(sc)) return;
        var ch = Ch;
        if (tweak == null) { sc.SetLoadout(Loadouts.Of(ch), now); return; }
        var shown = new Dictionary<string, string>(ch.Shown);
        var dyes = ch.Dyes.ToDictionary(kv => kv.Key, kv => new Dictionary<string, string>(kv.Value));
        tweak(ch);
        var lo = Loadouts.Of(ch);
        ch.Shown = shown; ch.Dyes = dyes;
        sc.SetLoadout(lo, now);
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
        // Your own first: what is equipped, or an empty place. A look has no level and no rarity. When a found look draws exactly what her own does
        // (a piece with no look of its own draws her calling's kit, the same as a look of that kit), the two are one tile: the look's, with the band.
        var worn = ch.Equipment[Wardrobe.EquipOf(Slot)];
        var ownDef = worn != null ? Items.Get(worn.Def) : null;
        var merged = Wardrobe.OwnLook(ch, Slot);
        var sig = LookThumbs.DyeSig(ch, Slot);
        void OwnHover(bool over) { if (over) { Preview(c => Wardrobe.SetShown(c, Slot, null)); Describe(worn != null ? $"Your own: {ownDef!.Name}" : "Nothing worn"); } else { Preview(null); Describe(null); } }
        if (merged != null)
        {
            bool sel = shownDef == null || shownDef.Id == merged.Id;
            grid.AddChild(LookTile(merged, Slot, "Your own", sel, true, hidden && sel, false, () => Set(null), OwnHover, "look:own", ownDef?.Name ?? "Your own", sel ? sig : ""));
        }
        else
            grid.AddChild(LookTile(ownDef, Slot, worn != null ? "Your own" : "Nothing worn", shownDef == null, true, hidden && shownDef == null, true,
                () => Set(null), OwnHover, "look:own", worn != null ? "Your own" : "Nothing worn", shownDef == null ? sig : ""));
        // Then the found looks, then the ones not yet found.
        foreach (var def in Wardrobe.All(ch, Slot).Where(d => d.Id != merged?.Id).OrderBy(d => ch.Looks.Contains(d.Id) ? 0 : 1))
        {
            bool have = ch.Looks.Contains(def.Id);
            var id = def.Id;
            bool sel = have && shownDef?.Id == id;
            grid.AddChild(LookTile(def, Slot, null, sel, have, hidden && sel, false, have ? () => Set(id) : null,
                have ? over => { if (over) { Preview(c => Wardrobe.SetShown(c, Slot, id)); Describe(def.Name); } else { Preview(null); Describe(null); } } : null,
                have ? $"look:{id}" : null, have ? def.Name : $"{def.Name}: not found yet", sel ? sig : ""));
        }
        return grid;
    }

    /// <summary>A look's tile, 96 px: a dark neutral fill, a 1 px quiet line, the look worn (LookThumbs); no level, rarity, badge or
    /// count. Selected is an ember frame, hover a 6% white fill; not found is the same picture dim and desaturated with a lock.</summary>
    static Control LookTile(ItemDef? def, string slot, string? caption, bool selected, bool found, bool crossed, bool own, Action? press, Action<bool>? hover, string? navId, string? tip, string dyes = "")
    {
        var box = new Panel { CustomMinimumSize = new Vector2(Tile, Tile), MouseFilter = Control.MouseFilterEnum.Stop };
        var sb = new StyleBoxFlat { BgColor = Kit.Tile };
        sb.SetCornerRadiusAll(4);
        sb.SetBorderWidthAll(selected ? 2 : 1);
        sb.BorderColor = selected ? Style.Ember : Kit.Rule;
        box.AddThemeStyleboxOverride("panel", sb);
        if (def != null || own)
        {
            Control pic = own ? LookThumbs.For(def?.Id ?? "none", slot, Tile - 4, false, true, dyes) : LookThumbs.For(def!.Id, slot, Tile - 4, !found, false, dyes);
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
        // (a not-found look's lock is drawn by its picture)
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
        // (three rows of swatches high on every tab and look, so the block never changes the page)
        v.CustomMinimumSize = new Vector2(0, Swatch * 3 + 20);
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
            // (a fixed label column: the swatches begin at the same x on every row and in every state)
            var name = Style.Label(ZoneNames.GetValueOrDefault(z, z), Style.Ui, 16, Kit.Ink2, false, HorizontalAlignment.Left, false);
            name.CustomMinimumSize = new Vector2(70, 0);
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
            var chosen = (now == null ? "As made" : Wardrobe.Dye(now)?.Name ?? now) + (hiddenHat ? " (hidden)" : "");
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
