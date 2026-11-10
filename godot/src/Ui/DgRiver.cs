using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// What is left of the Drowned Girl's river (UI 17-18; its art, river.png, is no longer drawn since UI 23's HUD A, where
/// the plate in the middle is DgPanel): the wells and rings the seats and the dash still wear (Socket, DgSmall; from
/// art/ui/dg_river, tools/uiforge/dg_river_cut.py), each seat's well radius, and the old eddy's place, where the Flare's
/// coal stands until the keeper (the right group) takes it.
/// </summary>
public static class DgRiver
{
    const string Dir = "dg_river";
    static Godot.Collections.Dictionary? geo;
    static Godot.Collections.Dictionary Geo => geo ??= Load();

    static Godot.Collections.Dictionary Load()
    {
        string path = $"{UiArt.Root}{Dir}/river_geo.json";
        if (FileAccess.FileExists(path) && Json.ParseString(FileAccess.GetFileAsString(path)).AsGodotDictionary() is { Count: > 0 } d)
            return d;
        GD.PushError($"DgRiver: {path} did not load: the seats' wells and the coal draw wrong");
        return new Godot.Collections.Dictionary();
    }

    static Vector2 V(Variant v) => v.AsGodotArray() is { Count: >= 2 } a ? new Vector2((float)a[0].AsDouble(), (float)a[1].AsDouble()) : Vector2.Zero;

    /// <summary>The i-th well's radius (the hole in its ring), from the geo.</summary>
    public static float Hole(int i)
    {
        holes ??= Holes();
        return i >= 0 && i < holes.Length ? holes[i] : 0;
    }

    // (read from the geo once: a seat asks at each redraw, and each asking made the geo's array and dictionary wrappers)
    static float[]? holes;
    static float[] Holes()
    {
        if (!Geo.TryGetValue("seats", out var s) || s.AsGodotArray() is not { } a) return System.Array.Empty<float>();
        var o = new float[a.Count];
        for (int i = 0; i < o.Length; i++) o[i] = a[i].AsGodotDictionary().TryGetValue("hole", out var h) ? (float)h.AsDouble() : 0;
        return o;
    }

    /// <summary>The ring (seat i) and its well.</summary>
    public static Texture2D? Ring(int i) => UiArt.Art($"{Dir}/ring_{i % 6}.png");
    public static Texture2D? Well(int i) => i < 0 ? null : wells[i % 6] ??= UiArt.Art($"{Dir}/well_{i % 6}.png");
    // (kept once found: the path was made again at each redraw of a seat)
    static readonly Texture2D?[] wells = new Texture2D?[6];

    static readonly Texture2D?[] inner = new Texture2D?[6];
    /// <summary>UI 23: the ring cut to the well's radius r (DgPanel.WellR): its inner edge, the well's own rim shading,
    /// inside the plate's baked bezel (mock7.py seat_layer(): today's well cut at r 31.5, feathered 0.9 px). Made once.</summary>
    public static Texture2D? RingInner(int i, float r)
    {
        i %= 6;
        if (inner[i] != null) return inner[i];
        if (Ring(i) is not { } t || t.GetImage() is not { } img || img.IsEmpty()) return null;
        if (img.IsCompressed()) img.Decompress();
        img.Convert(Image.Format.Rgba8);
        int w = img.GetWidth(), h = img.GetHeight();
        float k = w / t.GetSize().X;       // texels per HUD px (the art is twice its size)
        float cx = w / 2f, cy = h / 2f;
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float d = new Vector2(x + 0.5f - cx, y + 0.5f - cy).Length() / k;
                float m = Mathf.Clamp((r - d) / 0.9f + 0.5f, 0, 1);
                if (m >= 1) continue;
                var c = img.GetPixel(x, y);
                img.SetPixel(x, y, c with { A = c.A * m });
            }
        var tex = ImageTexture.CreateFromImage(img);
        tex.SetSizeOverride(new Vector2I((int)t.GetSize().X, (int)t.GetSize().Y));
        return inner[i] = tex;
    }
}
