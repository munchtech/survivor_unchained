using System;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>UI 24: a HUD figure's silhouette for the fade test. From the art's alpha (above 0.3, grown by 12 px) a
/// grid of 4 px cells, built once. Hit takes a point on the 1080 screen, inside the figure's rect and on a set cell:
/// her figure, the keeper and the panel fade for what is behind their art, not behind their empty corners. The grid
/// lies over the art's own space (Size, 1080 px); Hit maps the screen point in with the art's origin and scale.
/// If the art does not load the test is the rect's alone.</summary>
public sealed class HudMask
{
    const float Cell = 4, Grow = 12, Cut = 0.3f;
    readonly bool[]? grid;
    readonly int w, h;

    /// <summary>Her figure: lamp_cold.png over her quad (LifeLamp.Canvas).</summary>
    public static readonly HudMask Lamp = new("lamp_life/drowned/lamp_cold.png", false, LifeLamp.Canvas);
    /// <summary>The keeper, and the panel (the river's band), over their rects.</summary>
    public static readonly HudMask Keeper = new("dg_keeper/keeper.png", true, DgPanel.KeeperRect.Size);
    public static readonly HudMask Panel = new("dg_panel/panel.png", true, DgPanel.BandRect.Size);

    HudMask(string rel, bool halve, Vector2 size)
    {
        w = Math.Max(1, (int)Math.Ceiling(size.X / Cell));
        h = Math.Max(1, (int)Math.Ceiling(size.Y / Cell));
        Image? img = null;
        try
        {
            img = UiArt.Tex(rel, halve)?.GetImage();
            if (img != null && !img.IsEmpty() && img.IsCompressed()) img.Decompress();
        }
        catch (Exception) { img = null; }
        if (img == null || img.IsEmpty()) { GD.PushError($"HudMask: {rel} did not load: the fade tests its rect"); return; }
        int iw = img.GetWidth(), ih = img.GetHeight();
        var solid = new bool[w * h];
        for (int cy = 0; cy < h; cy++)
            for (int cx = 0; cx < w; cx++)
            {
                // (the cell's pixels in the image: any above the cut sets it)
                int x0 = (int)(cx * Cell / size.X * iw), x1 = Math.Min(iw, Math.Max(x0 + 1, (int)((cx + 1) * Cell / size.X * iw)));
                int y0 = (int)(cy * Cell / size.Y * ih), y1 = Math.Min(ih, Math.Max(y0 + 1, (int)((cy + 1) * Cell / size.Y * ih)));
                for (int y = y0; y < y1 && !solid[cy * w + cx]; y++)
                    for (int x = x0; x < x1; x++)
                        if (img.GetPixel(Math.Min(x, iw - 1), Math.Min(y, ih - 1)).A > Cut) { solid[cy * w + cx] = true; break; }
            }
        // (grown by 12 px: a disc of cells round each set one)
        int r = (int)Math.Ceiling(Grow / Cell);
        grid = new bool[w * h];
        for (int cy = 0; cy < h; cy++)
            for (int cx = 0; cx < w; cx++)
            {
                if (!solid[cy * w + cx]) continue;
                for (int dy = -r; dy <= r; dy++)
                    for (int dx = -r; dx <= r; dx++)
                    {
                        int x = cx + dx, y = cy + dy;
                        if (x >= 0 && y >= 0 && x < w && y < h && dx * dx + dy * dy <= r * r) grid[y * w + x] = true;
                    }
            }
    }

    /// <summary>Is the screen point inside the rect and on the art? origin: where the art's top left is on the screen,
    /// scale: its group scale (1 for the keeper and the panel).</summary>
    public bool Hit(Vector2 screen, Rect2 rect, Vector2 origin, float scale)
    {
        if (!rect.HasPoint(screen)) return false;
        if (grid == null) return true;
        var l = (screen - origin) / scale;
        int cx = (int)Math.Floor(l.X / Cell), cy = (int)Math.Floor(l.Y / Cell);
        return cx >= 0 && cy >= 0 && cx < w && cy < h && grid[cy * w + cx];
    }
}
