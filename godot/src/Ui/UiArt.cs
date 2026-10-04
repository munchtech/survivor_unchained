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
    /// border it sits on); unset, three quarters of the margin inside the control.</summary>
    public sealed record Slice(string File, int L, int T, int R, int B, bool Tile = false, int Out = 0, int Clear = -1, int OutY = -1)
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
        ["well"] = new("frames/well.png", 12, 12, 12, 12, Tile: true),
        ["slab"] = new("frames/slab.png", 14, 14, 14, 14, Tile: true),
        ["header"] = new("frames/header.png", 0, 0, 0, 12, Tile: true),
        // Hammered iron repeats rather than stretches; the ember stone at the top's middle is the code's.
        ["banner"] = new("frames/banner.png", 24, 14, 24, 14, Tile: true),
        // The crested card every choice is drawn on (the arts' facets, the lamp's choices, a pillar with
        // no art of its own): neutral iron; the code tints its crest band and hairline in the rarity or
        // school of the moment. A card too low for its slice (creation's callings, 470 by 92) takes the
        // row's instead.
        ["crest_card"] = new("frames/crest_card.png", 40, 72, 40, 40, Tile: true, Out: 10),
        ["crest_row"] = new("frames/crest_row.png", 40, 36, 40, 28, Tile: true, Out: 8),
        // Self's attribute pillars (188 by 340, the medallion in the crest at the head) and
        // the HUD's console the skills sit on (130 high, 300 to 720 wide with the skill
        // count; its foot runs off the screen). Both hang from the house's brackets.
        ["pillar"] = new("frames/pillar.png", 32, 100, 32, 36, Out: 12, Clear: 14),
        ["console"] = new("frames/console.png", 48, 28, 48, 28, Tile: true, Out: 12, Clear: 0),
        ["tooltip"] = new("frames/tooltip.png", 16, 16, 16, 16, Tile: true),
        ["tooltip_worn"] = new("frames/tooltip_worn.png", 16, 16, 16, 16, Tile: true),
        // Buttons, tabs, segments, keycaps.
        ["button"] = new("frames/button.png", 12, 10, 12, 10, Tile: true),
        ["button_hover"] = new("frames/button_hover.png", 12, 10, 12, 10, Tile: true),
        ["button_pressed"] = new("frames/button_pressed.png", 12, 10, 12, 10, Tile: true),
        ["button_disabled"] = new("frames/button_disabled.png", 12, 10, 12, 10, Tile: true),
        ["button_primary"] = new("frames/button_primary.png", 12, 10, 12, 10, Tile: true),
        ["button_primary_hover"] = new("frames/button_primary_hover.png", 12, 10, 12, 10, Tile: true),
        ["button_primary_pressed"] = new("frames/button_primary_pressed.png", 12, 10, 12, 10, Tile: true),
        ["segment_on"] = new("frames/segment_on.png", 10, 8, 10, 8),
        ["tab"] = new("frames/tab.png", 14, 10, 14, 6),
        ["tab_on"] = new("frames/tab_on.png", 14, 10, 14, 6),
        ["row_on"] = new("frames/row_on.png", 12, 10, 12, 10, Tile: true),
        ["keycap"] = new("frames/keycap.png", 6, 6, 6, 6),
        ["focus"] = new("frames/focus.png", 14, 14, 14, 14),
        // Slots, by rarity (0 common to 5 relic), and the empty one.
        ["slot"] = new("frames/slot.png", 10, 10, 10, 10),
        ["slot_0"] = new("frames/slot_common.png", 10, 10, 10, 10),
        ["slot_1"] = new("frames/slot_uncommon.png", 10, 10, 10, 10),
        ["slot_2"] = new("frames/slot_rare.png", 10, 10, 10, 10),
        ["slot_3"] = new("frames/slot_epic.png", 10, 10, 10, 10),
        ["slot_4"] = new("frames/slot_legendary.png", 10, 10, 10, 10),
        ["slot_5"] = new("frames/slot_relic.png", 10, 10, 10, 10),
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
        ["chip"] = new("frames/chip.png", 8, 8, 8, 8),
        ["weapon_slot"] = new("frames/weapon_slot.png", 12, 12, 12, 12),
        ["bar_track"] = new("bars/track.png", 8, 6, 8, 6, Tile: true),
        ["bar_track_boss"] = new("bars/track_boss.png", 24, 8, 24, 8),
        // Casings over the bars (GameHud.Casing): iron round the groove, reaching past it.
        ["bar_casing"] = new("bars/casing.png", 16, 8, 16, 8, Tile: true, Out: 6),
        ["bar_casing_boss"] = new("bars/casing_boss.png", 64, 24, 64, 24, Tile: true, Out: 64, OutY: 24),
        ["map_frame"] = new("frames/map_frame.png", 20, 20, 20, 20, Tile: true, Out: 8),
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

    /// <summary>A frame by name, or the drawn one. The drawn one's content
    /// margins are kept, so nothing moves when the art arrives.</summary>
    public static StyleBox Frame(string id, StyleBox fallback)
    {
        if (!Frames.TryGetValue(id, out var s) || Tex(s.File) is not { } tex) return fallback;
        var axis = s.Tile ? StyleBoxTexture.AxisStretchMode.TileFit : StyleBoxTexture.AxisStretchMode.Stretch;
        var b = new StyleBoxTexture
        {
            Texture = tex, TextureMarginLeft = s.L, TextureMarginTop = s.T, TextureMarginRight = s.R, TextureMarginBottom = s.B,
            AxisStretchHorizontal = axis, AxisStretchVertical = axis,
            ExpandMarginLeft = s.Out, ExpandMarginTop = s.Oy, ExpandMarginRight = s.Out, ExpandMarginBottom = s.Oy,
        };
        // What is inside keeps clear of the painted border: at least three quarters of
        // the slice margin (the border lives in the outer three quarters, by the brief),
        // less the part of the margin that lies outside the control.
        var slice = new Dictionary<Side, int> { [Side.Left] = s.L - s.Out, [Side.Top] = s.T - s.Oy, [Side.Right] = s.R - s.Out, [Side.Bottom] = s.B - s.Oy };
        foreach (var side in new[] { Side.Left, Side.Top, Side.Right, Side.Bottom })
            b.SetContentMargin(side, Mathf.Max(fallback.GetContentMargin(side), s.Clear >= 0 ? s.Clear : slice[side] * 0.75f));
        return b;
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
