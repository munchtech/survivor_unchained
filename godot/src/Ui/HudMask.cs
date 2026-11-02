using System;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>UI 24: a HUD figure's silhouette for the fade test. From the art's alpha (above 0.5, eroded by 20 px: a
/// real overlap, not a graze at the edge) a grid of 4 px cells, built once. Hit takes a point on the 1080 screen, inside the figure's rect and on a set cell:
/// her figure, the keeper and the panel fade for what is behind their art, not behind their empty corners. The grid
/// lies over the art's own space (Size, 1080 px); Hit maps the screen point in with the art's origin and scale.
/// If the art does not load the test is the rect's alone.</summary>
public sealed class HudMask
{
    const float Cell = 4, Shrink = 20, Cut = 0.5f;
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
                // (the cell's pixels in the image: all above the cut set it, so the erosion is true to the art)
                int x0 = (int)(cx * Cell / size.X * iw), x1 = Math.Min(iw, Math.Max(x0 + 1, (int)((cx + 1) * Cell / size.X * iw)));
                int y0 = (int)(cy * Cell / size.Y * ih), y1 = Math.Min(ih, Math.Max(y0 + 1, (int)((cy + 1) * Cell / size.Y * ih)));
                bool all = true;
                for (int y = y0; y < y1 && all; y++)
                    for (int x = x0; x < x1; x++)
                        if (img.GetPixel(Math.Min(x, iw - 1), Math.Min(y, ih - 1)).A <= Cut) { all = false; break; }
                solid[cy * w + cx] = all;
            }
        // (eroded by 20 px: a cell stays set only if every cell in a disc round it is set; off the grid is empty)
        int r = (int)Math.Ceiling(Shrink / Cell);
        grid = new bool[w * h];
        for (int cy = 0; cy < h; cy++)
            for (int cx = 0; cx < w; cx++)
            {
                bool keep = solid[cy * w + cx];
                for (int dy = -r; dy <= r && keep; dy++)
                    for (int dx = -r; dx <= r; dx++)
                    {
                        if (dx * dx + dy * dy > r * r) continue;
                        int x = cx + dx, y = cy + dy;
                        if (x < 0 || y < 0 || x >= w || y >= h || !solid[y * w + x]) { keep = false; break; }
                    }
                grid[cy * w + cx] = keep;
            }
    }

    // (hud24 r2: the set cells' ground points, cast once a frame for the marks' area test: no allocation per frame)
    int[]? cells;
    float[]? gx, gz;
    ulong stamp = ulong.MaxValue;

    /// <summary>The screen px2 of this art that lie over the ground inside the mark's footprint: each set cell (4 px a side
    /// in the art, 16 px2 x scale2 on the screen) is cast through the camera onto the plane y = groundY, and counted if the
    /// mark covers where it lands. Cast once per frame (frame); the art lies at origin with scale. If the art did not load: 0.</summary>
    public float Hidden(HudMark m, Camera3D cam, Vector2 origin, float scale, float groundY, ulong frame)
    {
        if (grid == null) return 0;
        if (cells == null)
        {
            int n = 0;
            for (int i = 0; i < grid.Length; i++) if (grid[i]) n++;
            cells = new int[n]; gx = new float[n]; gz = new float[n];
            n = 0;
            for (int i = 0; i < grid.Length; i++) if (grid[i]) cells[n++] = i;
        }
        if (stamp != frame)
        {
            stamp = frame;
            var o = cam.GlobalPosition;
            for (int k = 0; k < cells.Length; k++)
            {
                int c = cells[k];
                var scr = origin + new Vector2(((c % w) + 0.5f) * Cell, ((c / w) + 0.5f) * Cell) * scale;
                var d = cam.ProjectRayNormal(scr);
                float t = d.Y < -1e-4f ? (groundY - o.Y) / d.Y : -1;
                if (t > 0) { gx[k] = o.X + d.X * t; gz[k] = o.Z + d.Z * t; }
                else gx[k] = gz[k] = float.NaN;
            }
        }
        int hit = 0;
        for (int k = 0; k < cells.Length; k++)
            if (!float.IsNaN(gx![k]) && m.Covers(gx[k], gz![k])) hit++;
        return hit * Cell * Cell * scale * scale;
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
