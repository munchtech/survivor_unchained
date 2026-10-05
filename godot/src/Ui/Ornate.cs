using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The house's frame, drawn (docs/UI_DESIGN.md, "The frame language"):
/// forged iron in a gradient from a lit top to a dark foot, a bevel, an inset
/// gold hairline, bracketed corners each with a stone, a soft shadow beneath.
/// Wells are the same iron sunk in; cards carry their rarity in the hairline
/// and a crest band; paper is parchment with a darkened edge. Painted art
/// (UiArt) replaces any of them by name; this is what shows until it does,
/// and it already says "Survivor Unchained" rather than "a rectangle".
/// </summary>
public partial class OrnateBox : StyleBox
{
    public enum Kind { Plate, Well, Card, Paper, Banner, Slab }

    public Kind Look = Kind.Plate;
    /// <summary>The hairline and corners' colour (gold; a rarity on a card).</summary>
    public Color Accent = Style.Gold;
    /// <summary>The iron's lit top and dark foot.</summary>
    public Color Top = new("#25212b"), Foot = new("#100e13");
    /// <summary>A card's crest band at the top, in its accent (0: none).</summary>
    public float Crest;
    public bool Corners = true, Shadow = true;
    /// <summary>Glow round the frame (a lifted card, a chosen thing), in the accent.</summary>
    public float Glow;

    public OrnateBox() { }

    public static OrnateBox Make(Kind look, int pad = 18, Color? accent = null)
    {
        var b = new OrnateBox { Look = look };
        if (accent is { } a) b.Accent = a;
        switch (look)
        {
            case Kind.Well: b.Top = new Color("#08070a"); b.Foot = new Color("#141118"); b.Corners = false; b.Shadow = false; b.Accent = Style.GoldDim with { A = 0.5f }; break;
            case Kind.Paper: b.Top = new Color("#e8dbbd"); b.Foot = new Color("#d8c59c"); b.Corners = false; b.Accent = new Color(0.35f, 0.22f, 0.08f, 0.55f); break;
            case Kind.Banner: b.Top = new Color("#3e2412"); b.Foot = new Color("#1c0f08"); break;
            case Kind.Slab: b.Top = new Color("#1a171e"); b.Foot = new Color("#0c0a0e"); b.Corners = false; break;
        }
        b.ContentMarginLeft = b.ContentMarginRight = pad;
        b.ContentMarginTop = b.ContentMarginBottom = pad * 0.8f;
        return b;
    }

    public override void _Draw(Rid ci, Rect2 r)
    {
        var rs = RenderingServer.Singleton;
        float x0 = r.Position.X, y0 = r.Position.Y, x1 = r.End.X, y1 = r.End.Y;
        // A soft shadow under it.
        if (Shadow)
            for (int i = 1; i <= 6; i++)
            {
                float g = i * 3;
                RenderingServer.CanvasItemAddRect(ci, new Rect2(x0 - g + 2, y0 - g + 6, r.Size.X + g * 2 - 4, r.Size.Y + g * 2), new Color(0, 0, 0, 0.07f));
            }
        if (Glow > 0)
            for (int i = 1; i <= 8; i++)
            {
                float g = i * 3;
                RenderingServer.CanvasItemAddRect(ci, new Rect2(x0 - g, y0 - g, r.Size.X + g * 2, r.Size.Y + g * 2), Accent with { A = 0.05f * Glow * (1 - i / 9f) });
            }
        if (Painted(ci, r)) return;
        // The iron: lit at the top, dark at the foot.
        RenderingServer.CanvasItemAddPolygon(ci, new[] { new Vector2(x0, y0), new Vector2(x1, y0), new Vector2(x1, y1), new Vector2(x0, y1) },
            new[] { Top, Top, Foot, Foot });
        if (Look == Kind.Well)
        {
            // Sunk in: a shadow along the top, a faint light along the foot.
            for (int i = 0; i < 8; i++) RenderingServer.CanvasItemAddLine(ci, new Vector2(x0, y0 + i), new Vector2(x1, y0 + i), new Color(0, 0, 0, 0.35f - i * 0.04f));
            RenderingServer.CanvasItemAddLine(ci, new Vector2(x0, y1 - 1), new Vector2(x1, y1 - 1), new Color(1, 0.85f, 0.6f, 0.08f));
            Outline(ci, x0, y0, x1, y1, Accent, 1);
            return;
        }
        if (Look == Kind.Paper)
        {
            // Parchment darkened toward its edge.
            for (int i = 0; i < 14; i++)
                Outline(ci, x0 + i, y0 + i, x1 - i, y1 - i, new Color(0.4f, 0.26f, 0.1f, 0.13f * (1 - i / 14f)), 1);
            Outline(ci, x0, y0, x1, y1, Accent, 1);
            return;
        }
        if (Crest > 0)
        {
            // A card's crest band, its rarity's light fading downward.
            float h = Math.Min(Crest, r.Size.Y * 0.3f);
            RenderingServer.CanvasItemAddPolygon(ci, new[] { new Vector2(x0, y0), new Vector2(x1, y0), new Vector2(x1, y0 + h), new Vector2(x0, y0 + h) },
                new[] { Accent with { A = 0.32f }, Accent with { A = 0.32f }, Accent with { A = 0 }, Accent with { A = 0 } });
        }
        // The bevel: light on the top edge, dark on the foot.
        RenderingServer.CanvasItemAddLine(ci, new Vector2(x0 + 1, y0 + 1), new Vector2(x1 - 1, y0 + 1), new Color(1, 0.9f, 0.75f, 0.14f));
        RenderingServer.CanvasItemAddLine(ci, new Vector2(x0 + 1, y1 - 1), new Vector2(x1 - 1, y1 - 1), new Color(0, 0, 0, 0.6f));
        Outline(ci, x0, y0, x1, y1, new Color(0.02f, 0.015f, 0.025f, 1), 2);
        // The inset hairline.
        float inset = Look == Kind.Slab ? 3 : 6;
        Outline(ci, x0 + inset, y0 + inset, x1 - inset, y1 - inset, Accent with { A = Accent.A * (Look == Kind.Slab ? 0.35f : 0.55f) }, 1);
        if (!Corners) return;
        // Bracketed corners, each with a stone.
        float c = Math.Min(26, Math.Min(r.Size.X, r.Size.Y) * 0.22f);
        var hi = Accent.Lightened(0.25f);
        foreach (var (cx, cy, sx, sy) in new[] { (x0, y0, 1f, 1f), (x1, y0, -1f, 1f), (x0, y1, 1f, -1f), (x1, y1, -1f, -1f) })
        {
            var o = new Vector2(cx + 3 * sx, cy + 3 * sy);
            RenderingServer.CanvasItemAddLine(ci, o, o + new Vector2(c * sx, 0), Accent, 2.5f, true);
            RenderingServer.CanvasItemAddLine(ci, o, o + new Vector2(0, c * sy), Accent, 2.5f, true);
            RenderingServer.CanvasItemAddLine(ci, o + new Vector2(c * sx, 0), o + new Vector2(c * sx - 5 * sx, 4 * sy), Accent, 1.5f, true);
            RenderingServer.CanvasItemAddLine(ci, o + new Vector2(0, c * sy), o + new Vector2(4 * sx, c * sy - 5 * sy), Accent, 1.5f, true);
            Stone(ci, o + new Vector2(2 * sx, 2 * sy), 4.5f, hi);
        }
        if (Look == Kind.Banner || Look == Kind.Card && Crest > 0)
        {
            // A stone at the top's middle.
            Stone(ci, new Vector2((x0 + x1) / 2, y0 + 1), 6, Look == Kind.Card ? Accent.Lightened(0.35f) : Style.Ember);
        }
    }

    /// <summary>The art's name for each look (UiArt.Frames).</summary>
    static string ArtId(Kind k) => k switch
    {
        Kind.Plate => "plate", Kind.Well => "well", Kind.Card => "crest_card", Kind.Paper => "paper", Kind.Banner => "banner", _ => "slab",
    };

    /// <summary>
    /// The painted piece in place of the drawn one, when there is one: the art
    /// is the material, and the code keeps only what the art cannot know, the
    /// accent of the moment (a card's rarity or school in its crest band and a
    /// hairline, an ember edge when points wait). Returns false to draw it.
    /// </summary>
    bool Painted(Rid ci, Rect2 r)
    {
        if (!UiArt.Frames.TryGetValue(ArtId(Look), out var sl)) return false;
        // A card lower than its slice's top and foot (a row of a list) wears the row's slice.
        if (Look == Kind.Card && r.Size.Y < sl.T + sl.B - 2 * sl.Oy && UiArt.Frames.TryGetValue("crest_row", out var row)) sl = row;
        if (UiArt.Tex(sl.File) is not { } tex) return false;
        var at = r.GrowIndividual(sl.Out, sl.Oy, sl.Out, sl.Oy);
        var mode = sl.Tile ? RenderingServer.NinePatchAxisMode.TileFit : RenderingServer.NinePatchAxisMode.Stretch;
        RenderingServer.CanvasItemAddNinePatch(ci, at, new Rect2(Vector2.Zero, tex.GetSize()), tex.GetRid(), new Vector2(sl.L, sl.T), new Vector2(sl.R, sl.B), mode, mode, true, Colors.White);
        if (Look == Kind.Card)
        {
            float h = Math.Min(Crest, r.Size.Y * 0.3f);
            if (h > 0)
                RenderingServer.CanvasItemAddPolygon(ci, new[] { r.Position, new Vector2(r.End.X, r.Position.Y), new Vector2(r.End.X, r.Position.Y + h), new Vector2(r.Position.X, r.Position.Y + h) },
                    new[] { Accent with { A = 0.22f }, Accent with { A = 0.22f }, Accent with { A = 0 }, Accent with { A = 0 } });
            var inner = r.Grow(-Math.Max(4, Math.Min(sl.L - sl.Out, sl.T - sl.Oy) * 0.6f));
            Outline(ci, inner.Position.X, inner.Position.Y, inner.End.X, inner.End.Y, Accent with { A = Accent.A * 0.5f }, 1);
        }
        // The banner's ember stone at the top's middle: one stone, so the code's, not the nine-slice's.
        if (Look == Kind.Banner) Stone(ci, new Vector2(r.GetCenter().X, r.Position.Y + 1), 6, Style.Ember);
        return true;
    }

    static void Outline(Rid ci, float x0, float y0, float x1, float y1, Color c, float w)
    {
        var pts = new[] { new Vector2(x0, y0), new Vector2(x1, y0), new Vector2(x1, y1), new Vector2(x0, y1), new Vector2(x0, y0) };
        RenderingServer.CanvasItemAddPolyline(ci, pts, new[] { c }, w);
    }

    /// <summary>A small cut stone (a diamond), lit on its upper half.</summary>
    public static void Stone(Rid ci, Vector2 at, float s, Color c)
    {
        RenderingServer.CanvasItemAddPolygon(ci, new[] { at + new Vector2(0, -s), at + new Vector2(s, 0), at + new Vector2(0, s), at + new Vector2(-s, 0) },
            new[] { c.Lightened(0.4f), c, c.Darkened(0.4f), c });
    }
}

/// <summary>A heading between two gold rules ending in ember stones: the house's title plaque.</summary>
public partial class Plaque : Control
{
    readonly Label label;
    readonly float tw;

    public Plaque(string text, int size = 40, float rule = 160, Color? color = null)
    {
        MouseFilter = MouseFilterEnum.Ignore;
        var up = text.ToUpperInvariant();
        label = Style.Label(up, Style.Display, size, color ?? Style.GoldHi, false, HorizontalAlignment.Center);
        AddChild(label);
        // Measured from the face itself: a label not yet in the tree does not know its size.
        var ts = Style.Display.GetStringSize(up, HorizontalAlignment.Left, -1, size);
        tw = ts.X;
        CustomMinimumSize = new Vector2(ts.X + rule * 2 + 56, size * 1.35f);
        label.Size = new Vector2(ts.X, size * 1.35f);
        Resized += () => { label.Position = new Vector2((Size.X - tw) / 2, 0); QueueRedraw(); };
        label.Position = new Vector2(rule + 28, 0);
    }

    public override void _Draw()
    {
        // The title in the middle however wide the plaque is stretched; the rules run out from it.
        float y = Size.Y * 0.55f, w = Size.X;
        if (tw <= 0)
        {
            // No title (the house's rule under the name): one rule with its stone at the middle,
            // the painted one where there is one, not two halves round an empty gap.
            if (UiArt.Art("ornaments/rule.png") is { } art)
            {
                float h = art.GetHeight();
                DrawTextureRect(art, new Rect2(0, y - h / 2, w, h), false);
                return;
            }
            DrawLine(new Vector2(8, y), new Vector2(w - 8, y), Style.Gold with { A = 0.8f }, 1.5f, true);
            foreach (var x in new[] { 8f, w - 8 })
                DrawColoredPolygon(new[] { new Vector2(x, y - 3), new Vector2(x + 3, y), new Vector2(x, y + 3), new Vector2(x - 3, y) }, Style.Gold);
            DrawColoredPolygon(new[] { new Vector2(w / 2, y - 6), new Vector2(w / 2 + 6, y), new Vector2(w / 2, y + 6), new Vector2(w / 2 - 6, y) }, Style.Ember);
            return;
        }
        float x0 = (w - tw) / 2;
        float l = x0 - 14, r = x0 + tw + 14;
        // Painted rules (ornaments/plaque_rule.png: the ember stone at its left end, the gold running
        // out to its right): to the right of the title as drawn, to the left mirrored. A negative
        // width flips the picture but keeps the rect's corner, so the mirrored one starts len to the left.
        if (UiArt.Art("ornaments/plaque_rule.png") is { } rule)
        {
            float h = rule.GetHeight(), len = Mathf.Max(0, l - 4);
            DrawTextureRect(rule, new Rect2(r, y - h / 2, len, h), false);
            DrawTextureRect(rule, new Rect2(l - len, y - h / 2, -len, h), false);
            return;
        }
        DrawLine(new Vector2(8, y), new Vector2(l - 10, y), Style.Gold with { A = 0.8f }, 1.5f, true);
        DrawLine(new Vector2(r + 10, y), new Vector2(w - 8, y), Style.Gold with { A = 0.8f }, 1.5f, true);
        foreach (var x in new[] { 8f, l - 10, r + 10, w - 8 })
            DrawColoredPolygon(new[] { new Vector2(x, y - 3), new Vector2(x + 3, y), new Vector2(x, y + 3), new Vector2(x - 3, y) }, Style.Gold);
        foreach (var x in new[] { l, r })
            DrawColoredPolygon(new[] { new Vector2(x, y - 6), new Vector2(x + 6, y), new Vector2(x, y + 6), new Vector2(x - 6, y) }, Style.Ember);
    }
}

/// <summary>A section's name: small gold capitals, a stone, and a rule running on.</summary>
public partial class Section : Control
{
    public Section(string text, string? note = null)
    {
        MouseFilter = MouseFilterEnum.Ignore;
        var h = Style.H(8, Style.Label(text.ToUpperInvariant(), Style.UiHeavy, 14, Style.Gold));
        if (note != null) h.AddChild(Style.Label(note, Style.TextItalic, Style.Caption, Style.InkDim));
        h.Position = new Vector2(16, 0);
        AddChild(h);
        CustomMinimumSize = new Vector2(0, 24);
        SizeFlagsHorizontal = SizeFlags.ExpandFill;
        Resized += QueueRedraw;
    }

    public override void _Draw()
    {
        // The painted mark (ornaments/section_mark.png, an ember set in gold) where there is one.
        if (UiArt.Art("ornaments/section_mark.png") is { } mark)
        {
            var s = mark.GetSize();
            DrawTextureRect(mark, new Rect2(new Vector2(5, 12) - s / 2, s), false);
        }
        else DrawColoredPolygon(new[] { new Vector2(5, 7), new Vector2(10, 12), new Vector2(5, 17), new Vector2(0, 12) }, Style.Ember);
        var label = GetChild<HBoxContainer>(0);
        float x = 16 + label.GetCombinedMinimumSize().X + 12;
        if (x < Size.X - 4) DrawLine(new Vector2(x, 12), new Vector2(Size.X, 12), Style.Line, 1);
    }
}

/// <summary>A round medallion: an iron disc in a gold ring, a number or a glyph on it.</summary>
public partial class Medallion : Control
{
    public string Text = "";
    public string? Glyph;
    public Color Ring = Style.Gold, Ink = Style.GoldHi, Core = new("#3a2210");
    /// <summary>How far round its progress arc is drawn (0: none).</summary>
    public float Arc;
    public Color ArcColor = Style.Ember;
    /// <summary>Lit: an ember glow behind it (the art in hand, a socket waiting to be set).</summary>
    public bool Lit;
    readonly int size;

    public Medallion(int size, string text = "", string? glyph = null)
    {
        this.size = size;
        Text = text;
        Glyph = glyph;
        CustomMinimumSize = new Vector2(size, size);
        MouseFilter = MouseFilterEnum.Ignore;
    }

    public override void _Draw()
    {
        var c = new Vector2(size / 2f, size / 2f);
        float r = size / 2f - 3;
        if (Lit)
            for (int i = 6; i >= 1; i--) DrawCircle(c, r + i * size * 0.035f, new Color(1, 0.45f, 0.15f, 0.05f));
        DrawCircle(c + new Vector2(0, 3), r + 2, new Color(0, 0, 0, 0.5f));
        DrawCircle(c, r + 1, new Color("#060508"));
        // The core: lit from the upper left.
        DrawCircle(c, r - 4, Core.Darkened(0.35f));
        DrawCircle(c - new Vector2(r * 0.15f, r * 0.15f), r * 0.72f, Core);
        if (UiArt.Art("medallion/ring.png") is { } ring)
        {
            // The painted ring over the box, its middle open on the core; its school or rarity
            // kept as a hairline just inside it.
            DrawArc(c, r * 0.76f, 0, Mathf.Tau, 64, Ring with { A = 0.8f }, 2, true);
            DrawTextureRect(ring, new Rect2(Vector2.Zero, new Vector2(size, size)), false);
            if (Arc > 0) DrawArc(c, r * 0.88f, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * Mathf.Clamp(Arc, 0, 1), 64, ArcColor, 4, true);
        }
        else
        {
            DrawArc(c, r - 2, 0, Mathf.Tau, 64, Ring, 3.5f, true);
            DrawArc(c, r - 8, 0, Mathf.Tau, 64, Ring with { A = 0.35f }, 1, true);
            if (Arc > 0) DrawArc(c, r - 2, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * Mathf.Clamp(Arc, 0, 1), 64, ArcColor, 5, true);
            // Four studs on the ring.
            for (int i = 0; i < 4; i++)
            {
                var d = new Vector2(Mathf.Cos(i * Mathf.Pi / 2 + Mathf.Pi / 4), Mathf.Sin(i * Mathf.Pi / 2 + Mathf.Pi / 4)) * (r - 2);
                DrawCircle(c + d, 2.5f, Ring.Lightened(0.3f));
            }
        }
        if (Glyph != null)
        {
            var t = Glyphs.Texture(Glyph, size * 2, Ink);
            float g = size * 0.5f;
            DrawTextureRect(t, new Rect2(c - new Vector2(g / 2, g / 2), new Vector2(g, g)), false);
        }
        if (Text != "")
        {
            var f = Style.Display;
            int fs = (int)(size * (Text.Length > 2 ? 0.32f : 0.44f));
            var ts = f.GetStringSize(Text, HorizontalAlignment.Left, -1, fs);
            // A long number shrinks to stay inside the ring.
            while (ts.X > size * 0.7f && fs > 8) { fs--; ts = f.GetStringSize(Text, HorizontalAlignment.Left, -1, fs); }
            DrawString(f, c + new Vector2(-ts.X / 2 + 1, fs * 0.36f + 1), Text, HorizontalAlignment.Left, -1, fs, new Color(0, 0, 0, 0.8f));
            DrawString(f, c + new Vector2(-ts.X / 2, fs * 0.36f), Text, HorizontalAlignment.Left, -1, fs, Ink);
        }
    }
}

/// <summary>A globe of liquid in a gold ring (health): its level, a pale trail behind a fall, a shield's arc, its number.</summary>
public partial class Globe : Control
{
    public float Level = 1, Trail = 1, Shield;
    public Color Liquid = new("#c8262c");
    public string Number = "";
    public float Pulse;
    readonly float r;
    // What was last drawn: the HUD asks every frame, and a redraw rebuilt every polygon.
    (float, float, float, string, float, Color) drawn = (float.NaN, 0, 0, "", 0, default);

    /// <summary>Redrawn only if what it shows has changed since it was last drawn.</summary>
    public void Changed()
    {
        var now = (Level, Trail, Shield, Number, Pulse, Liquid);
        if (now == drawn) return;
        drawn = now;
        QueueRedraw();
    }

    public Globe(float radius)
    {
        r = radius;
        CustomMinimumSize = new Vector2(radius * 2 + 12, radius * 2 + 12);
        Size = CustomMinimumSize;
        MouseFilter = MouseFilterEnum.Ignore;
    }

    static Vector2[] Below(Vector2 c, float r, float level)
    {
        // The part of the circle under the liquid's surface.
        float y = c.Y + r - 2 * r * Mathf.Clamp(level, 0, 1);
        var pts = new List<Vector2>();
        float a0 = Mathf.Asin(Mathf.Clamp((y - c.Y) / r, -1, 1));
        for (int i = 0; i <= 40; i++)
        {
            float a = Mathf.Lerp(a0, Mathf.Pi - a0, i / 40f);
            pts.Add(c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r);
        }
        return pts.ToArray();
    }

    public override void _Draw()
    {
        var c = Size / 2;
        DrawCircle(c + new Vector2(0, 4), r + 6, new Color(0, 0, 0, 0.55f));
        DrawCircle(c, r + 5, new Color("#060508"));
        DrawCircle(c, r, new Color("#140608"));
        if (Trail > Level + 0.002f) { var t = Below(c, r, Trail); if (t.Length > 2) DrawColoredPolygon(t, new Color("#e8c07a") with { A = 0.75f }); }
        if (Level > 0.002f)
        {
            var p = Below(c, r, Level);
            if (p.Length > 2)
            {
                var cols = new Color[p.Length];
                for (int i = 0; i < p.Length; i++) cols[i] = Liquid.Lerp(Liquid.Darkened(0.55f), Mathf.Clamp((p[i].Y - (c.Y - r)) / (2 * r), 0, 1));
                DrawPolygon(p, cols);
            }
        }
        if (Pulse > 0) DrawCircle(c, r, new Color(1, 0.3f, 0.25f, Pulse * 0.25f));
        // The glass's light, and its rim: painted (hud/globe_glass.png over the liquid, hud/globe_rim.png
        // round it, both filling the globe's box with their middles open) or drawn.
        if (UiArt.Art("hud/globe_glass.png") is { } glass) DrawTextureRect(glass, new Rect2(Vector2.Zero, Size), false);
        else DrawCircle(c + new Vector2(-r * 0.32f, -r * 0.42f), r * 0.26f, new Color(1, 1, 1, 0.08f));
        if (UiArt.Art("hud/globe_rim.png") is { } rim) DrawTextureRect(rim, new Rect2(Vector2.Zero, Size), false);
        else
        {
            DrawArc(c, r + 1, 0, Mathf.Tau, 72, Style.Gold, 4, true);
            DrawArc(c, r - 5, 0, Mathf.Tau, 72, new Color(0, 0, 0, 0.5f), 3, true);
        }
        if (Shield > 0) DrawArc(c, r + 6, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * Mathf.Clamp(Shield, 0, 1), 72, Style.Shield, 4, true);
        if (Number != "")
        {
            var f = Style.UiHeavy;
            int fs = (int)(r * 0.36f);
            var ts = f.GetStringSize(Number, HorizontalAlignment.Left, -1, fs);
            var at = c + new Vector2(-ts.X / 2, fs * 0.36f);
            DrawString(f, at + new Vector2(1, 2), Number, HorizontalAlignment.Left, -1, fs, new Color(0, 0, 0, 0.9f));
            DrawString(f, at, Number, HorizontalAlignment.Left, -1, fs, new Color("#fff4ea"));
        }
    }
}

/// <summary>A long reading whose ends melt away instead of being cut: what it holds (a scroll,
/// filling it) is drawn through its own alpha, clear in the middle and fading to nothing over the
/// top and foot, so a line half under the edge is a line going, not a sliver.</summary>
public partial class FadeEnds : Control
{
    readonly float top, foot;

    public FadeEnds(Control inside, float top = 26, float foot = 44)
    {
        this.top = top;
        this.foot = foot;
        ClipChildren = ClipChildrenMode.Only;
        MouseFilter = MouseFilterEnum.Pass;
        SizeFlagsHorizontal = SizeFlagsVertical = SizeFlags.ExpandFill;
        Style.Fill(inside);
        AddChild(inside);
        Resized += QueueRedraw;
    }

    public override void _Draw()
    {
        float w = Size.X, h = Size.Y, a = Mathf.Min(top, h / 3), b = Mathf.Max(h - foot, h * 2 / 3);
        var clear = new Color(1, 1, 1, 0);
        void Band(float y0, float y1, Color c0, Color c1) =>
            DrawPolygon(new[] { new Vector2(0, y0), new Vector2(w, y0), new Vector2(w, y1), new Vector2(0, y1) }, new[] { c0, c0, c1, c1 });
        Band(0, a, clear, Colors.White);
        Band(a, b, Colors.White, Colors.White);
        Band(b, h, Colors.White, clear);
    }
}

/// <summary>Behind a full-screen page: the world dark at the edges, faint in the middle, an ember glow along the foot.</summary>
public partial class Backdrop : Control
{
    public float Strength = 0.88f;
    static Shader? blur;

    public Backdrop(Action? onClick = null, float strength = 0.88f)
    {
        Strength = strength;
        Style.Fill(this);
        MouseFilter = MouseFilterEnum.Stop;
        if (onClick != null) GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) onClick(); };
        // The world behind, out of focus and darkened (shaders/ui_backdrop.gdshader): the page
        // sits in the place the survivor stands, never on flat black.
        blur ??= GD.Load<Shader>("res://shaders/ui_backdrop.gdshader");
        var world = new ColorRect { Material = new ShaderMaterial { Shader = blur }, MouseFilter = MouseFilterEnum.Ignore };
        ((ShaderMaterial)world.Material).SetShaderParameter("dim", Mathf.Lerp(1.1f, 0.62f, strength));
        Style.Fill(world);
        AddChild(world);
        // The painted layers over it (tools/uiforge/pages.py): soot and wear gathered at the edges,
        // then a fine grain over all, so the dark between columns is a surface, not an empty screen.
        if (UiArt.Tex("page/backdrop_edges.png", false) is { } edges)
        {
            var e = new TextureRect { Texture = edges, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore };
            Style.Fill(e);
            AddChild(e);
        }
        if (UiArt.Art("page/backdrop_grain.png") is { } grain)
        {
            var g = new TextureRect { Texture = grain, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Tile, MouseFilter = MouseFilterEnum.Ignore };
            Style.Fill(g);
            AddChild(g);
        }
        var dark = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                // (the blurred world is already dim: the shade only deepens toward the edges, where it frames the page)
                Gradient = new Gradient { Colors = new[] { new Color(0.03f, 0.02f, 0.04f, strength * 0.12f), new Color(0.02f, 0.015f, 0.03f, strength * 0.7f) }, Offsets = new[] { 0.2f, 1f } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.45f), FillTo = new Vector2(1.05f, 1.05f), Width = 256, Height = 256,
            },
            StretchMode = TextureRect.StretchModeEnum.Scale, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, MouseFilter = MouseFilterEnum.Ignore,
        };
        Style.Fill(dark);
        AddChild(dark);
        var ember = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(1, 0.42f, 0.12f, 0.08f), new Color(1, 0.42f, 0.12f, 0) }, Offsets = new[] { 0f, 1f } },
                FillFrom = new Vector2(0.5f, 1), FillTo = new Vector2(0.5f, 0.6f), Width = 16, Height = 128,
            },
            StretchMode = TextureRect.StretchModeEnum.Scale, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, MouseFilter = MouseFilterEnum.Ignore,
        };
        Style.Fill(ember);
        AddChild(ember);
    }
}

/// <summary>
/// The journal as a book lying open (docs/UI_DESIGN.md, "Journal"): a
/// tooled leather cover, two parchment pages darkening into the spine, the
/// thickness of the leaves at their edges. Painted art at
/// art/ui/book/open.png takes its place when it lands; either way the pages'
/// content sits in <see cref="Left"/> and <see cref="Right"/>.
/// </summary>
public partial class OpenBook : Control
{
    public readonly Control Left = new() { MouseFilter = MouseFilterEnum.Ignore };
    public readonly Control Right = new() { MouseFilter = MouseFilterEnum.Ignore };
    /// <summary>The cover's margin round the pages, and the pages' margin round their words.</summary>
    const float Cover = 26, Margin = 52, Gutter = 34;
    static readonly Color Leather = new("#3b1d14"), LeatherDeep = new("#1e0d08"), Gold = new("#b8893a"), Paper = new("#e9ddc1"), PaperDeep = new("#c7b28a");

    public OpenBook(Vector2 size)
    {
        CustomMinimumSize = size;
        Size = size;
        MouseFilter = MouseFilterEnum.Ignore;
        float half = size.X / 2;
        Left.Position = new Vector2(Cover + Margin, Cover + Margin * 0.8f);
        Left.Size = new Vector2(half - Cover - Margin - Gutter, size.Y - Cover * 2 - Margin * 1.6f);
        Right.Position = new Vector2(half + Gutter, Cover + Margin * 0.8f);
        Right.Size = Left.Size;
        AddChild(Left);
        AddChild(Right);
    }

    public override void _Draw()
    {
        var s = Size;
        if (UiArt.Art("book/open.png") is { } art) { DrawTextureRect(art, new Rect2(Vector2.Zero, s), false); return; }
        // The shadow it casts on the table.
        for (int i = 6; i >= 1; i--)
            DrawRect(new Rect2(new Vector2(-i * 3, i * 4), s + new Vector2(i * 6, i * 2)), new Color(0, 0, 0, 0.07f));
        // The cover: leather, lit from above, tooled with a gold line and capped at the corners.
        DrawPolygon(new[] { Vector2.Zero, new Vector2(s.X, 0), s, new Vector2(0, s.Y) }, new[] { Leather.Lightened(0.08f), Leather.Lightened(0.08f), LeatherDeep, LeatherDeep });
        DrawRect(new Rect2(new Vector2(9, 9), s - new Vector2(18, 18)), Gold with { A = 0.55f }, false, 1.5f);
        DrawRect(new Rect2(new Vector2(13, 13), s - new Vector2(26, 26)), Gold with { A = 0.25f }, false, 1f);
        foreach (var (c, dx, dy) in new[] { (Vector2.Zero, 1, 1), (new Vector2(s.X, 0), -1, 1), (s, -1, -1), (new Vector2(0, s.Y), 1, -1) })
        {
            DrawColoredPolygon(new[] { c, c + new Vector2(dx * 46, 0), c + new Vector2(0, dy * 46) }, Gold.Darkened(0.25f));
            DrawPolyline(new[] { c + new Vector2(dx * 46, 0), c + new Vector2(0, dy * 46) }, Gold.Lightened(0.2f), 1.5f);
            OrnateBox.Stone(GetCanvasItem(), c + new Vector2(dx * 14, dy * 14), 5, Style.Ember);
        }
        float half = s.X / 2, top = Cover, foot = s.Y - Cover;
        // The leaves' thickness under each page, then the pages themselves.
        for (int i = 4; i >= 1; i--)
        {
            var edge = Paper.Darkened(0.12f + i * 0.05f);
            DrawRect(new Rect2(Cover - i * 2, top + i * 2, half - Cover + i * 2, foot - top), edge);
            DrawRect(new Rect2(half, top + i * 2, half - Cover + i * 2, foot - top), edge);
        }
        Page(new Rect2(Cover, top, half - Cover, foot - top), true);
        Page(new Rect2(half, top, half - Cover, foot - top), false);
        // The spine's fold.
        DrawPolygon(new[] { new Vector2(half - 3, top), new Vector2(half + 3, top), new Vector2(half + 3, foot), new Vector2(half - 3, foot) },
            new[] { new Color(0.2f, 0.12f, 0.06f, 0.7f), new Color(0.2f, 0.12f, 0.06f, 0.7f), new Color(0.2f, 0.12f, 0.06f, 0.7f), new Color(0.2f, 0.12f, 0.06f, 0.7f) });
    }

    /// <summary>A page: parchment, darker into the spine and at its outer edge, with a grain.</summary>
    void Page(Rect2 r, bool left)
    {
        var deep = PaperDeep;
        var inner = left ? r.End.X : r.Position.X;
        DrawRect(r, Paper);
        // Into the spine: the curve of the page.
        const float fold = 90;
        var fx = left ? inner - fold : inner;
        var a = left ? Paper with { A = 0 } : deep;
        var b = left ? deep : Paper with { A = 0 };
        DrawPolygon(new[] { new Vector2(fx, r.Position.Y), new Vector2(fx + fold, r.Position.Y), new Vector2(fx + fold, r.End.Y), new Vector2(fx, r.End.Y) }, new[] { a, b, b, a });
        // The outer edge, aged.
        const float age = 40;
        var ox = left ? r.Position.X : r.End.X - age;
        var c0 = left ? deep with { A = 0.6f } : Paper with { A = 0 };
        var c1 = left ? Paper with { A = 0 } : deep with { A = 0.6f };
        DrawPolygon(new[] { new Vector2(ox, r.Position.Y), new Vector2(ox + age, r.Position.Y), new Vector2(ox + age, r.End.Y), new Vector2(ox, r.End.Y) }, new[] { c0, c1, c1, c0 });
        // Top and foot, a little darker.
        DrawPolygon(new[] { r.Position, new Vector2(r.End.X, r.Position.Y), new Vector2(r.End.X, r.Position.Y + 24), new Vector2(r.Position.X, r.Position.Y + 24) },
            new[] { deep with { A = 0.45f }, deep with { A = 0.45f }, deep with { A = 0 }, deep with { A = 0 } });
        DrawPolygon(new[] { new Vector2(r.Position.X, r.End.Y - 24), new Vector2(r.End.X, r.End.Y - 24), r.End, new Vector2(r.Position.X, r.End.Y) },
            new[] { deep with { A = 0 }, deep with { A = 0 }, deep with { A = 0.45f }, deep with { A = 0.45f } });
        // The grain: faint flecks, fixed so the page does not shimmer.
        var rng = new RandomNumberGenerator { Seed = left ? 11UL : 23UL };
        for (int i = 0; i < 260; i++)
        {
            var p = r.Position + new Vector2(rng.Randf() * r.Size.X, rng.Randf() * r.Size.Y);
            DrawRect(new Rect2(p, new Vector2(rng.RandfRange(1, 3), 1)), new Color(0.45f, 0.32f, 0.16f, rng.RandfRange(0.04f, 0.12f)));
        }
    }
}

/// <summary>A silk ribbon bookmark: a band with a notched tail, its colour its section.</summary>
public partial class RibbonBox : StyleBox
{
    public Color Silk = new("#8a2a1a");
    public bool Raised;

    public RibbonBox() { ContentMarginLeft = ContentMarginRight = 10; ContentMarginTop = 6; ContentMarginBottom = 26; }

    public override void _Draw(Rid ci, Rect2 r)
    {
        var c = Raised ? Silk.Lightened(0.12f) : Silk;
        // Painted silk (book/ribbon.png, pale, its tail notched), dyed the section's colour by the code.
        if (UiArt.Art("book/ribbon.png") is { } silk)
        {
            RenderingServer.CanvasItemAddTextureRect(ci, new Rect2(r.Position + new Vector2(3, 3), r.Size), silk.GetRid(), false, new Color(0, 0, 0, 0.3f));
            RenderingServer.CanvasItemAddTextureRect(ci, r, silk.GetRid(), false, c.Lightened(0.25f));
            return;
        }
        float notch = 12;
        var pts = new[] { r.Position, new Vector2(r.End.X, r.Position.Y), r.End, new Vector2(r.Position.X + r.Size.X / 2, r.End.Y - notch), new Vector2(r.Position.X, r.End.Y) };
        // A shadow on the page, then the silk with its sheen down the middle.
        RenderingServer.CanvasItemAddPolygon(ci, Array.ConvertAll(pts, p => p + new Vector2(3, 3)), new[] { new Color(0, 0, 0, 0.3f) });
        RenderingServer.CanvasItemAddPolygon(ci, pts, new[] { c.Lightened(0.15f), c.Lightened(0.15f), c.Darkened(0.3f), c.Darkened(0.1f), c.Darkened(0.3f) });
        RenderingServer.CanvasItemAddLine(ci, r.Position + new Vector2(r.Size.X * 0.3f, 0), new Vector2(r.Position.X + r.Size.X * 0.3f, r.End.Y - notch * 1.4f), c.Lightened(0.35f) with { A = 0.35f }, 2);
        RenderingServer.CanvasItemAddLine(ci, r.Position + new Vector2(3, 0), new Vector2(r.Position.X + 3, r.End.Y - 2), c.Darkened(0.4f) with { A = 0.5f }, 1);
        RenderingServer.CanvasItemAddLine(ci, new Vector2(r.End.X - 3, r.Position.Y), new Vector2(r.End.X - 3, r.End.Y - 2), c.Darkened(0.4f) with { A = 0.5f }, 1);
    }
}
