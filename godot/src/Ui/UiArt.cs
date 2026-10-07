using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The interface's painted art, where there is any (docs/UI_ART_BRIEF.md).
/// Every frame, bar, prompt and icon the interface draws asks here first by
/// name; a file under art/ui/ replaces the drawn look, and with no file the
/// drawn look stays. So art can arrive one piece at a time and the game is
/// whole at every step.
///
/// Art is made at twice the size it is shown (for 4K) and shown at half: a
/// frame's nine-slice margins below are in shown pixels, half the file's.
/// A file the editor has imported loads as a resource; one dropped in
/// without importing still loads straight from disk while developing (run
/// `godot --headless --path godot --import` before a build so it ships).
/// </summary>
public static class UiArt
{
    public const string Root = "res://art/ui/";

    /// <summary>A nine-slice frame: the file under art/ui/ and its margins
    /// (left, top, right, bottom) in shown pixels; Tile repeats the edges and
    /// the centre instead of stretching them (for textured iron: hammer work
    /// stretched four times over looks smeared, repeated it looks forged);
    /// Out is how far the painted frame reaches past the control on each side
    /// (shown pixels, part of the margins), so corner pieces can be bold without
    /// crowding what is inside: the content still keeps clear of the border
    /// only, so nothing moves when the art arrives. Clear, when set, is how far
    /// the content keeps from the control's edge (shown pixels) where the
    /// painted border is narrower than the slice (a corner piece wider than the
    /// border it sits on); unset, three quarters of the margin inside the control.
    /// Ground, when set, is a material (a tileable texture under art/ui/) laid at 1:1
    /// inside the control under the slice, tinted by Tint: the slice then carries only
    /// the edge's light and shade, and the material's grain never stretches with it
    /// (tools/uiforge/kit.py).</summary>
    public sealed record Slice(string File, int L, int T, int R, int B, bool Tile = false, int Out = 0, int Clear = -1, int OutY = -1,
        string? Ground = null, Color? Tint = null)
    {
        /// <summary>How far past the control above and below (Out unless OutY is set).</summary>
        public int Oy => OutY >= 0 ? OutY : Out;
    }

    /// <summary>Every frame the interface can wear, by the name the code asks for.</summary>
    public static readonly Dictionary<string, Slice> Frames = new()
    {
        // Plates and paper: the screens' backs.
        // The strap repeats along a plate of any size; the coins at the corners reach
        // 12 past it; what is inside keeps 21 from the edge, as before the art.
        ["plate"] = new("frames/plate.png", 64, 64, 64, 64, Tile: true, Out: 12, Clear: 21),
        ["paper"] = new("frames/paper.png", 32, 32, 32, 32, Tile: true),
        // Inside a plate: the sunk well a grid or list lies in, the raised slab a group
        // stands on, the band across a page's head, the banner a verdict or name is cut in.
        ["well"] = new("frames/well.png", 10, 10, 10, 10, Tile: true, Ground: "page/morocco.png", Tint: new Color(0.45f, 0.42f, 0.45f, 0.75f)),
        ["slab"] = new("frames/slab.png", 14, 14, 14, 14, Tile: true, Out: 6, Ground: "page/morocco.png", Tint: new Color(1f, 1f, 1f, 0.88f)),
        ["header"] = new("frames/header.png", 0, 0, 0, 12, Tile: true),
        // Its match along the page's foot, the prompts set on its leather.
        ["footer"] = new("frames/footer.png", 0, 12, 0, 0, Tile: true),
        // The page's pieces (tools/uiforge/pages.py): the rail between a page's columns (its stone is
        // drawn at the middle by Overlay), the plate round the survivor's figure on the pack and the
        // self, and the light card for tooltips and the result's cards.
        ["column_divider"] = new("frames/column_divider.png", 0, 28, 0, 28, Tile: true),
        // A page's column ruled in gilt (Style.Column): stretched, so the rules' fade follows its height.
        ["column"] = new("frames/column.png", 12, 16, 12, 8),
        ["hero_plate"] = new("frames/hero_plate.png", 14, 14, 14, 14, Tile: true, Out: 6, Ground: "page/morocco.png", Tint: new Color(0.8f, 0.8f, 0.8f, 0.7f)),
        ["card_light"] = new("frames/card_light.png", 20, 20, 20, 20, Tile: true),
        // Hammered iron repeats rather than stretches; the ember stone at the top's middle is the code's.
        ["banner"] = new("frames/banner.png", 24, 14, 24, 14, Tile: true),
        // The crested card every choice is drawn on (the arts' facets, the lamp's choices, a pillar with
        // no art of its own): neutral iron; the code tints its crest band and hairline in the rarity or
        // school of the moment. A card too low for its slice (creation's callings, 470 by 92) takes the
        // row's instead.
        ["crest_card"] = new("frames/crest_card.png", 40, 72, 40, 40, Tile: true, Out: 10),
        ["crest_row"] = new("frames/crest_row.png", 40, 36, 40, 28, Tile: true, Out: 8),
        // Self's attribute pillars (188 by 340, the medallion in the crest at the head).
        ["pillar"] = new("frames/pillar.png", 14, 14, 14, 14, Tile: true, Out: 6, Ground: "page/morocco.png", Tint: new Color(1f, 1f, 1f, 0.88f)),
        ["tooltip"] = new("frames/tooltip.png", 14, 14, 14, 14, Tile: true, Out: 6, Ground: "page/morocco.png", Tint: new Color(1f, 1f, 1f, 0.97f)),
        ["tooltip_worn"] = new("frames/tooltip_worn.png", 16, 16, 16, 16, Tile: true),
        // Buttons, tabs, segments, keycaps.
        ["button"] = new("frames/button.png", 12, 10, 12, 10, Tile: true, Ground: "page/morocco.png", Tint: new Color(1.15f, 1.12f, 1.1f, 0.92f)),
        ["button_hover"] = new("frames/button_hover.png", 12, 10, 12, 10, Tile: true, Ground: "page/morocco.png", Tint: new Color(1.4f, 1.34f, 1.3f, 0.95f)),
        ["button_pressed"] = new("frames/button_pressed.png", 12, 10, 12, 10, Tile: true, Ground: "page/morocco.png", Tint: new Color(0.75f, 0.72f, 0.72f, 0.92f)),
        ["button_disabled"] = new("frames/button_disabled.png", 12, 10, 12, 10, Tile: true, Ground: "page/morocco.png", Tint: new Color(0.7f, 0.7f, 0.7f, 0.5f)),
        ["button_primary"] = new("frames/button_primary.png", 12, 10, 12, 10, Tile: true, Ground: "page/morocco.png", Tint: new Color(1.3f, 1.1f, 1f, 0.95f)),
        ["button_primary_hover"] = new("frames/button_primary_hover.png", 12, 10, 12, 10, Tile: true, Ground: "page/morocco.png", Tint: new Color(1.5f, 1.25f, 1.1f, 0.97f)),
        ["button_primary_pressed"] = new("frames/button_primary_pressed.png", 12, 10, 12, 10, Tile: true, Ground: "page/morocco.png", Tint: new Color(0.9f, 0.78f, 0.72f, 0.95f)),
        ["segment_on"] = new("frames/segment_on.png", 10, 8, 10, 8),
        ["tab"] = new("frames/tab.png", 14, 10, 14, 6),
        ["tab_on"] = new("frames/tab_on.png", 18, 10, 18, 6, Tile: true),
        ["row_on"] = new("frames/row_on.png", 10, 10, 10, 10, Tile: true, Ground: "page/morocco.png", Tint: new Color(0.8f, 0.74f, 0.72f, 0.9f)),
        ["keycap"] = new("frames/keycap.png", 6, 6, 6, 6, Ground: "page/morocco.png", Tint: new Color(0.55f, 0.52f, 0.55f, 0.9f)),
        ["focus"] = new("frames/focus.png", 14, 14, 14, 14),
        // Slots, by rarity (0 common to 5 relic), and the empty one.
        ["slot"] = new("frames/slot.png", 10, 10, 10, 10, Ground: "page/morocco.png", Tint: new Color(0.66f, 0.63f, 0.66f, 0.86f)),
        ["slot_0"] = new("frames/slot_common.png", 10, 10, 10, 10, Ground: "page/morocco.png", Tint: new Color(0.55f, 0.52f, 0.55f, 0.85f)),
        ["slot_1"] = new("frames/slot_uncommon.png", 10, 10, 10, 10, Ground: "page/morocco.png", Tint: new Color(0.55f, 0.52f, 0.55f, 0.85f)),
        ["slot_2"] = new("frames/slot_rare.png", 10, 10, 10, 10, Ground: "page/morocco.png", Tint: new Color(0.55f, 0.52f, 0.55f, 0.85f)),
        ["slot_3"] = new("frames/slot_epic.png", 10, 10, 10, 10, Ground: "page/morocco.png", Tint: new Color(0.55f, 0.52f, 0.55f, 0.85f)),
        ["slot_4"] = new("frames/slot_legendary.png", 10, 10, 10, 10, Ground: "page/morocco.png", Tint: new Color(0.55f, 0.52f, 0.55f, 0.85f)),
        ["slot_5"] = new("frames/slot_relic.png", 10, 10, 10, 10, Ground: "page/morocco.png", Tint: new Color(0.55f, 0.52f, 0.55f, 0.85f)),
        // The draft's cards, by rarity, and the evolution's.
        // Drawn one to one (368 by 500 with the 24 that may reach past the card): the
        // brackets the card hangs from and the coins at its foot overhang it.
        ["card_0"] = new("frames/card_common.png", 64, 80, 64, 64, Out: 24),
        ["card_1"] = new("frames/card_uncommon.png", 64, 80, 64, 64, Out: 24),
        ["card_2"] = new("frames/card_rare.png", 64, 80, 64, 64, Out: 24),
        ["card_3"] = new("frames/card_epic.png", 64, 80, 64, 64, Out: 24),
        ["card_4"] = new("frames/card_legendary.png", 64, 80, 64, 64, Out: 24),
        ["card_evolve"] = new("frames/card_evolution.png", 64, 80, 64, 64, Out: 24),
        // What comes and goes on the HUD.
        ["toast"] = new("frames/toast.png", 14, 10, 10, 10, Tile: true),
        ["prompt"] = new("frames/prompt.png", 22, 12, 22, 12, Tile: true),
        // The note: its nail and its drop of wax in corners wider than the text keeps from.
        ["hint"] = new("frames/hint.png", 40, 40, 40, 40, Tile: true, Clear: 14),
        ["chip"] = new("frames/chip.png", 8, 8, 8, 8, Ground: "page/morocco.png", Tint: new Color(1.1f, 1.08f, 1.05f, 0.85f)),
        ["bar_track"] = new("bars/track.png", 8, 6, 8, 6, Tile: true),
        // A boss's bar along the top (GameHud.BuildBoss, 850 by 16): its forged groove, the iron clamps at
        // its ends reaching 8 past it; its middle open where the fill shows (docs/team/ui_design.md).
        ["boss_groove"] = new("hud/boss_groove.png", 16, 8, 16, 8, Tile: true, Out: 8),
        ["map_frame"] = new("frames/map_frame.png", 20, 20, 20, 20, Tile: true, Out: 8),
        // The reduced kit's own pieces (tools/uiforge/kit.py).
        ["panel"] = new("frames/panel.png", 14, 14, 14, 14, Tile: true, Out: 6, Ground: "page/morocco.png", Tint: new Color(1f, 1f, 1f, 0.88f)),
        ["tab_hover"] = new("frames/tab_hover.png", 18, 10, 18, 6, Tile: true),
        ["tab_pressed"] = new("frames/tab_pressed.png", 18, 10, 18, 6, Tile: true),
        ["side"] = new("frames/side.png", 48, 48, 48, 48, Tile: true, Out: 8, Ground: "page/vellum.png", Tint: new Color(1f, 1f, 1f, 0.9f)),
        ["price"] = new("frames/price.png", 6, 6, 6, 6, Ground: "page/morocco.png", Tint: new Color(0.5f, 0.48f, 0.5f, 0.92f)),
        ["row"] = new("frames/row.png", 10, 10, 10, 10, Tile: true, Ground: "page/morocco.png", Tint: new Color(0.7f, 0.68f, 0.7f, 0.85f)),
        ["rule_h"] = new("frames/rule_h.png", 28, 0, 28, 0, Tile: true),
        ["rule_v"] = new("frames/rule_v.png", 0, 28, 0, 28, Tile: true),
    };

    static readonly Dictionary<string, Texture2D?> cache = new();

    /// <summary>A texture under art/ui/, or null. Halved: made at twice the
    /// size it is shown, it reports its shown size and draws crisp at 4K.</summary>
    public static Texture2D? Tex(string rel, bool halve = true)
    {
        var key = $"{rel}|{halve}";
        if (cache.TryGetValue(key, out var hit)) return hit;
        var path = Root + rel;
        Image? img = null;
        if (ResourceLoader.Exists(path))
        {
            var t = GD.Load<Texture2D>(path);
            if (!halve) return cache[key] = t;
            img = t?.GetImage();
        }
        else if (FileAccess.FileExists(path)) img = Image.LoadFromFile(ProjectSettings.GlobalizePath(path));
        if (img == null || img.IsEmpty()) return cache[key] = null;
        if (img.IsCompressed()) img.Decompress();
        var tex = ImageTexture.CreateFromImage(img);
        if (halve) tex.SetSizeOverride(new Vector2I(Mathf.Max(1, img.GetWidth() / 2), Mathf.Max(1, img.GetHeight() / 2)));
        return cache[key] = tex;
    }

    public static bool Has(string id) => Frames.TryGetValue(id, out var s) && Tex(s.File) != null;

    /// <summary>Every frame's texture read ahead (once, as the game starts), so no panel reads one as it opens.</summary>
    public static void Warm()
    {
        foreach (var s in Frames.Values) Tex(s.File);
    }

    /// <summary>A frame by name, or the drawn one. The drawn one's content
    /// margins are kept, so nothing moves when the art arrives.</summary>
    public static StyleBox Frame(string id, StyleBox fallback)
    {
        if (!Frames.TryGetValue(id, out var s) || Tex(s.File) is not { } tex) return fallback;
        StyleBox b;
        if (s.Ground != null && Tex(s.Ground) is { } ground)
            b = new GroundBox { Slice = s, Edge = tex, Ground = ground };
        else
        {
            var axis = s.Tile ? StyleBoxTexture.AxisStretchMode.TileFit : StyleBoxTexture.AxisStretchMode.Stretch;
            b = new StyleBoxTexture
            {
                Texture = tex, TextureMarginLeft = s.L, TextureMarginTop = s.T, TextureMarginRight = s.R, TextureMarginBottom = s.B,
                AxisStretchHorizontal = axis, AxisStretchVertical = axis,
                ExpandMarginLeft = s.Out, ExpandMarginTop = s.Oy, ExpandMarginRight = s.Out, ExpandMarginBottom = s.Oy,
            };
        }
        // What is inside keeps clear of the painted border: at least three quarters of
        // the slice margin (the border lives in the outer three quarters, by the brief),
        // less the part of the margin that lies outside the control.
        var slice = new Dictionary<Side, int> { [Side.Left] = s.L - s.Out, [Side.Top] = s.T - s.Oy, [Side.Right] = s.R - s.Out, [Side.Bottom] = s.B - s.Oy };
        foreach (var side in new[] { Side.Left, Side.Top, Side.Right, Side.Bottom })
            b.SetContentMargin(side, Mathf.Max(fallback.GetContentMargin(side), s.Clear >= 0 ? s.Clear : slice[side] * 0.75f));
        return b;
    }

    /// <summary>
    /// Draws a slice with a Ground: the material first, at 1:1 inside the control, then the
    /// slice's edge over it. Used by Frame and by the drawn boxes that wear art by name.
    /// </summary>
    public static void DrawSlice(Rid ci, Rect2 r, Slice s, Texture2D edge, Texture2D? ground)
    {
        if (ground != null) DrawGround(ci, r, ground, s.Tint ?? Colors.White);
        var at = r.GrowIndividual(s.Out, s.Oy, s.Out, s.Oy);
        var mode = s.Tile ? RenderingServer.NinePatchAxisMode.TileFit : RenderingServer.NinePatchAxisMode.Stretch;
        RenderingServer.CanvasItemAddNinePatch(ci, at, new Rect2(Vector2.Zero, edge.GetSize()), edge.GetRid(),
            new Vector2(s.L, s.T), new Vector2(s.R, s.B), mode, mode, true, Colors.White);
    }

    /// <summary>A material repeated at its own size over a rect, cut at the rect's edges (drawn
    /// tile by tile, so it needs no texture repeat). Where in the material a rect begins comes
    /// from its size, so like rects beside each other rarely show the same patch of it.</summary>
    public static void DrawGround(Rid ci, Rect2 r, Texture2D ground, Color tint)
    {
        var ts = ground.GetSize();
        if (ts.X < 1 || ts.Y < 1 || r.Size.X < 1 || r.Size.Y < 1) return;
        float px = Mathf.PosMod(r.Size.X * 7.31f + r.Size.Y * 3.17f, ts.X), py = Mathf.PosMod(r.Size.Y * 5.71f + r.Size.X * 1.37f, ts.Y);
        px = Mathf.Floor(px);
        py = Mathf.Floor(py);
        for (float y = 0; y < r.Size.Y;)
        {
            float sy = (y == 0 ? py : 0), h = Mathf.Min(ts.Y - sy, r.Size.Y - y);
            for (float x = 0; x < r.Size.X;)
            {
                float sx = (x == 0 ? px : 0), w = Mathf.Min(ts.X - sx, r.Size.X - x);
                RenderingServer.CanvasItemAddTextureRectRegion(ci, new Rect2(r.Position + new Vector2(x, y), new Vector2(w, h)),
                    ground.GetRid(), new Rect2(sx, sy, w, h), tint);
                x += w;
            }
            y += h;
        }
    }

    /// <summary>A painted icon for a set ('glyph', 'item', 'map', 'prompt', 'hud'), or null.</summary>
    public static Texture2D? Icon(string set, string key) => Tex($"icons/{set}/{key}.png", false);

    /// <summary>Anything else by its path under art/ui/ (the logo, a bar's fill), or null.</summary>
    public static Texture2D? Art(string rel) => Tex(rel);

    /// <summary>The pointer, if one is painted (32 by 32, shown as drawn, not
    /// halved: the system draws cursors): cursors/pointer.png, its tip at
    /// (3, 2); hand.png over something to press, the fingertip at (11, 2);
    /// forbidden.png over what cannot be done, centred at (16, 16).</summary>
    public static void Cursors()
    {
        void Set(string file, Input.CursorShape shape, Vector2 hot)
        {
            if (Tex($"cursors/{file}", false) is { } t) Input.SetCustomMouseCursor(t, shape, hot);
        }
        Set("pointer.png", Input.CursorShape.Arrow, new Vector2(3, 2));
        Set("hand.png", Input.CursorShape.PointingHand, new Vector2(11, 2));
        Set("forbidden.png", Input.CursorShape.Forbidden, new Vector2(16, 16));
    }
}

/// <summary>A frame whose material is laid at 1:1 under its slice (see UiArt.Slice.Ground).</summary>
public partial class GroundBox : StyleBox
{
    public UiArt.Slice Slice = null!;
    public Texture2D Edge = null!;
    public Texture2D? Ground;

    public override void _Draw(Rid ci, Rect2 r) => UiArt.DrawSlice(ci, r, Slice, Edge, Ground);
}
