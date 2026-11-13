using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The map (the web game's overlays/Map.tsx and ui/mapArt.ts): the zone as
/// the survivor has walked it. The drawing is made from the zone itself: its
/// heights become hill shading and contour lines, what is painted on the
/// ground tints the paper, water is washed blue-grey, every tree and rock is
/// an ink mark where it stands, every wall and house its footprint. Fog is
/// plain paper where you have not been; places are named once seen (the way
/// out and what the journal told you always are). The wheel zooms, a drag
/// pans, M or Escape puts it away. Beside it, a list of where to go, the
/// places found and what to beware of, nearest first, each with how far and
/// which way: a line chosen (hovered, focused) glides the map to it and
/// rings it. With a pad the list is walked with the D-pad, the triggers zoom
/// and Y finds you.
/// </summary>
public partial class MapScreen : Overlay
{
    public override string Kind => "map";
    public override Act? Toggle => Act.Map;
    const int W = 1600;
    static readonly Dictionary<string, ImageTexture> drawings = new();
    float zoom = 1;
    Vector2 pan;
    bool dragging;
    Vector2 dragFrom, panFrom;
    Control? world;

    public MapScreen(Game g) : base(g)
    {
        // (--map-wide: opened wide, for pictures)
        if (Args.Has("map-wide")) wide = true;
        if (g.Zone?.MapFocus is var (x, z, zm) && g.Scene != null)
        {
            zoom = (float)zm;
            float ext = Extent(g.Scene.Data.Meta);
            pan = new Vector2(-(float)x / ext, -(float)z / ext);
        }
    }

    public static float Extent(World.ZoneMeta m) => m.Map?.Extent is { ValueKind: JsonValueKind.Number } e ? (float)e.GetDouble() : (float)m.Bound * 2;

    static double Hash(double x, double y) { double s = Math.Sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.Floor(s); }

    /// <summary>The zone drawn on paper, once per zone (the map and the corner map share it).</summary>
    public static ImageTexture Drawing(ZoneData z)
    {
        if (drawings.TryGetValue(z.Id, out var hit)) return hit;
        InkSheet(z);
        // (drawn on a worker since the place was staged: waited for, the rest of it only)
        var img = drawn.TryRemove(z.Id, out var ahead) ? ahead : soon.TryRemove(z.Id, out var task) ? task.Result : Draw(z);
        var tex = ImageTexture.CreateFromImage(img);
        drawings[z.Id] = tex;
        return tex;
    }

    static readonly Dictionary<string, ImageTexture> inkSheets = new();
    /// <summary>(L1 l26 mini) The zone's own ink (ZoneInk: props, buildings, yards) as a sheet over the drawing, made with it.</summary>
    public static ImageTexture? InkSheetFor(string id) => inkSheets.TryGetValue(id, out var t) ? t : null;

    /// <summary>The sheet's pixels across (about 0.3 m each on the Waystation's 120 m: half a minimap pixel).</summary>
    public const int InkN = 400;

    static ImageTexture InkSheet(ZoneData z)
    {
        if (inkSheets.TryGetValue(z.Id, out var hit)) return hit;
        var sw = System.Diagnostics.Stopwatch.StartNew();
        float extent = Extent(z.Meta);
        int sr = z.Splat.GetWidth();
        Color At(double x, double zz) => z.Splat.GetPixel(Math.Clamp((int)((x / z.Size + 0.5) * sr), 0, sr - 1), Math.Clamp((int)((zz / z.Size + 0.5) * sr), 0, sr - 1));
        // as the drawing mixes it: the dirt (R, x1.2) under the stone (G) and the leaf litter (A, x0.8)
        static float Dirt(Color p) => Math.Min(1, p.R * 1.2f) * (1 - p.G) * (1 - p.A * 0.8f);
        var shapes = ZoneInk.From(z.Meta);
        var px = ZoneInk.Build(shapes, InkN, extent, (x, zz) => Dirt(At(x, zz)) > 0.5f, (x, zz) => { var p = At(x, zz); return p.G > 0.5f || Dirt(p) > 0.5f; });
        var tex = ImageTexture.CreateFromImage(Image.CreateFromData(InkN, InkN, false, Image.Format.Rgba8, px));
        inkSheets[z.Id] = tex;
        GD.Print($"map: zone ink for {z.Id}: {shapes.Count} shapes, {InkN} px over {extent:0} m, {sw.Elapsed.TotalMilliseconds:F1} ms");
        return tex;
    }

    /// <summary>The zone drawn ahead of its place being built, on a worker thread (Game.Prepare): only the picture,
    /// made a texture when the map first shows it (it took a whole frame of 1.3 s, the Waystation's first).</summary>
    public static void DrawAhead(ZoneData z)
    {
        if (!drawings.ContainsKey(z.Id) && !drawn.ContainsKey(z.Id) && !soon.ContainsKey(z.Id)) drawn[z.Id] = Draw(z);
        _ = Sheet.Value;
    }

    static readonly System.Collections.Concurrent.ConcurrentDictionary<string, Image> drawn = new();
    static readonly System.Collections.Concurrent.ConcurrentDictionary<string, System.Threading.Tasks.Task<Image>> soon = new();

    /// <summary>A place staged where it stands (an arena, a quick start: not built ahead): its drawing made on a
    /// worker from now, and the fog's sheet with it, so the map's first open does not draw them on the frame
    /// (N25: 1.4 s for the arena's drawing and 0.95 s for its fog, the sim held still behind it, "my game froze").</summary>
    public static void DrawSoon(ZoneData z)
    {
        if (drawings.ContainsKey(z.Id) || drawn.ContainsKey(z.Id) || soon.ContainsKey(z.Id)) return;
        soon[z.Id] = System.Threading.Tasks.Task.Run(() => { var img = Draw(z); _ = Sheet.Value; return img; });
    }

    /// <summary>The drawing itself (any thread: it reads only the zone's data).</summary>
    static Image Draw(ZoneData z)
    {
        var meta = z.Meta;
        float extent = Extent(meta);
        const int G = 300;
        var h = new float[G * G];
        var tint = new Vector3[G * G];
        var wet = new float[G * G];
        int sr = z.Splat.GetWidth();
        Color Splat(float u, float v)
        {
            float x = Math.Clamp(u * sr - 0.5f, 0, sr - 1.001f), y = Math.Clamp(v * sr - 0.5f, 0, sr - 1.001f);
            int x0 = (int)x, y0 = (int)y;
            float tx = x - x0, ty = y - y0;
            return z.Splat.GetPixel(x0, y0).Lerp(z.Splat.GetPixel(x0 + 1, y0), tx).Lerp(z.Splat.GetPixel(x0, y0 + 1).Lerp(z.Splat.GetPixel(x0 + 1, y0 + 1), tx), ty);
        }
        for (int j = 0; j < G; j++)
            for (int i = 0; i < G; i++)
            {
                float x = (i / (G - 1f) - 0.5f) * extent, zz = (j / (G - 1f) - 0.5f) * extent;
                int k = j * G + i;
                h[k] = z.HeightAt(x, zz);
                var p = Splat(x / z.Size + 0.5f, zz / z.Size + 0.5f);
                var c = new Vector3(222, 208, 172);
                void Mix(float r, float g, float b, float a) => c = c.Lerp(new Vector3(r, g, b), Mathf.Clamp(a, 0, 1));
                Mix(196, 196, 150, 0.35f);
                Mix(186, 150, 104, p.R * 1.2f);
                Mix(160, 154, 142, p.G);
                Mix(140, 116, 84, p.A * 0.8f);
                Mix(150, 170, 90, p.B);
                tint[k] = c;
                wet[k] = meta.WaterAt(x, zz) ? 1 : 0;
            }
        float S(float[] a, float fx, float fy)
        {
            float x = Math.Clamp(fx, 0, G - 1.001f), y = Math.Clamp(fy, 0, G - 1.001f);
            int x0 = (int)x, y0 = (int)y;
            float tx = x - x0, ty = y - y0;
            return Mathf.Lerp(Mathf.Lerp(a[y0 * G + x0], a[y0 * G + x0 + 1], tx), Mathf.Lerp(a[(y0 + 1) * G + x0], a[(y0 + 1) * G + x0 + 1], tx), ty);
        }
        Vector3 T(float fx, float fy)
        {
            float x = Math.Clamp(fx, 0, G - 1.001f), y = Math.Clamp(fy, 0, G - 1.001f);
            int x0 = (int)x, y0 = (int)y;
            float tx = x - x0, ty = y - y0;
            return tint[y0 * G + x0].Lerp(tint[y0 * G + x0 + 1], tx).Lerp(tint[(y0 + 1) * G + x0].Lerp(tint[(y0 + 1) * G + x0 + 1], tx), ty);
        }
        var px8 = new byte[W * W * 3];
        float cell = extent / (G - 1);
        const float contour = 1.5f;
        for (int py = 0; py < W; py++)
            for (int px = 0; px < W; px++)
            {
                float fx = px / (float)W * (G - 1), fy = py / (float)W * (G - 1);
                float y = S(h, fx, fy);
                // Hill shading, lit from the north-west.
                float dx = (S(h, fx + 1, fy) - S(h, fx - 1, fy)) / (2 * cell), dz = (S(h, fx, fy + 1) - S(h, fx, fy - 1)) / (2 * cell);
                float shade = Math.Clamp(1 + (-dx * 0.7f - dz * 0.7f) * 0.55f, 0.55f, 1.25f);
                var c = T(fx, fy);
                float w = S(wet, fx, fy);
                if (w > 0.05f) c = c.Lerp(new Vector3(118, 146, 150), Math.Min(1, w * 1.4f));
                c *= shade;
                // Contours: thin ink where the height crosses a line, every fifth heavier.
                float band = y / contour, next = S(h, fx + 0.34f, fy + 0.34f) / contour;
                if (Mathf.Floor(band) != Mathf.Floor(next) && w < 0.3f)
                {
                    bool major = (int)Mathf.Floor(Math.Max(band, next)) % 5 == 0;
                    c = c.Lerp(new Vector3(92, 70, 46), major ? 0.42f : 0.2f);
                }
                // The grain of the paper, and its age at the edges.
                float n = (float)((Hash(px, py) - 0.5) * 12 + (Hash(px / 12, py / 12) - 0.5) * 10);
                float r = new Vector2(px - W / 2f, py - W / 2f).Length() / W;
                float age = Mathf.SmoothStep(0.3f, 0.72f, r) * 0.5f;
                c = c.Lerp(new Vector3(70, 40, 14), age) + new Vector3(n, n, n * 0.8f);
                int o = (py * W + px) * 3;
                px8[o] = (byte)Math.Clamp(c.X, 0, 255);
                px8[o + 1] = (byte)Math.Clamp(c.Y, 0, 255);
                px8[o + 2] = (byte)Math.Clamp(c.Z, 0, 255);
            }
        var img = Image.CreateFromData(W, W, false, Image.Format.Rgb8, px8);
        // (made the GPU's own format here, on the worker: an RGB image is widened to RGBA as it is uploaded, on the frame)
        img.Convert(Image.Format.Rgba8);
        img.GenerateMipmaps();
        return img;
    }

    /// <summary>
    /// The land not yet walked, as a cartographer leaves it: the same sheet,
    /// blank and older (mottled, foxed, browned toward its edge), and where
    /// what you know ends, an ink wash that has bled into the paper and dried
    /// with a darker tide line, ragged as a brush leaves it. The walked land
    /// shows through clean. Opaque wherever nothing was walked: no ink shows
    /// through. (Was a flat dark at 94%: the owner, "it needs to look better".)
    /// </summary>
    /// <summary>The last fog made, and what it was made of: opened again with nothing new walked, it is the same.</summary>
    static (string Seen, ImageTexture Tex)? lastFog;

    static ImageTexture Fog(string seen, int n)
    {
        if (lastFog is { } lf && lf.Seen == seen) return lf.Tex;
        var made = FogFor(seen, n);
        lastFog = (seen, made);
        return made;
    }

    static ImageTexture FogFor(string seen, int n)
    {
        const int F = 600;
        float c = F / (float)n;
        var known = new float[F * F];
        var fsw = System.Diagnostics.Stopwatch.StartNew();
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                if (j * n + i >= seen.Length || seen[j * n + i] != '1') continue;
                float cx = (i + 0.5f) * c, cy = (j + 0.5f) * c, rr = c * 1.3f;
                for (int y = (int)(cy - rr); y <= (int)(cy + rr); y++)
                    for (int x = (int)(cx - rr); x <= (int)(cx + rr); x++)
                    {
                        if (x < 0 || y < 0 || x >= F || y >= F) continue;
                        float d = new Vector2(x - cx, y - cy).Length() / rr;
                        known[y * F + x] = Math.Max(known[y * F + x], 1 - Mathf.SmoothStep(0.5f, 1f, d));
                    }
            }
        double tStamp = fsw.Elapsed.TotalMilliseconds;
        for (int pass = 0; pass < 3; pass++) known = Blur(known, F, 5);
        // How near the known land is, broadly: the sheet is lit round what you know and browns away from it.
        var near = Blur(Blur(known, F, 28), F, 28);
        double tBlur = fsw.Elapsed.TotalMilliseconds;
        var sh = Sheet.Value;
        double tSheet = fsw.Elapsed.TotalMilliseconds;
        var px = new byte[F * F * 4];
        var browned = new Vector3(0.66f, 0.6f, 0.52f);
        System.Threading.Tasks.Parallel.For(0, F, y =>
        {
            for (int x = 0; x < F; x++)
            {
                int q = y * F + x;
                float k = Mathf.Clamp(known[q] + sh.Rag[q], 0, 1);
                float cover = 1 - Mathf.SmoothStep(0.34f, 0.5f, k);
                if (cover <= 0.001f) continue;
                // The blank sheet (its mottle, foxing, edge and the surveyor's lines: SheetFor), browned away from what you know.
                float lit = Mathf.SmoothStep(0f, 0.45f, near[q]);
                var paper = sh.Paper[q];
                paper = paper.Lerp(paper * browned, (1 - lit) * 0.75f);
                paper = paper * sh.Keep[q] + sh.Over[q];
                // The wash where knowledge ends: sepia bleeding outward, its tide line darkest.
                float tide = Mathf.Exp(-Mathf.Pow((k - 0.31f) / 0.05f, 2));
                float bleed = Mathf.SmoothStep(0.06f, 0.33f, k) * (1 - Mathf.SmoothStep(0.33f, 0.4f, k));
                paper = paper.Lerp(new Vector3(120, 84, 48), bleed * 0.35f).Lerp(new Vector3(74, 46, 22), tide * 0.55f);
                float grain = sh.Grain[q];
                paper += new Vector3(grain, grain, grain * 0.8f);
                int o = q * 4;
                px[o] = (byte)Math.Clamp(paper.X, 0, 255);
                px[o + 1] = (byte)Math.Clamp(paper.Y, 0, 255);
                px[o + 2] = (byte)Math.Clamp(paper.Z, 0, 255);
                px[o + 3] = (byte)Math.Clamp(cover * 255, 0, 255);
            }
        });
        double tPx = fsw.Elapsed.TotalMilliseconds;
        var fogTex = ImageTexture.CreateFromImage(Image.CreateFromData(F, F, false, Image.Format.Rgba8, px));
        if (measure) GD.Print($"MAPMEASURE fog: stamp {tStamp:F1} ms, blurs {tBlur - tStamp:F1} ms, sheet {tSheet - tBlur:F1} ms, pixels {tPx - tSheet:F1} ms, texture {fsw.Elapsed.TotalMilliseconds - tPx:F1} ms");
        return fogTex;
    }

    /// <summary>What the fog's sheet is whatever was walked, per pixel, made once: the brush's ragged edge, the
    /// paper mottled, and what lies over it (foxing, the browned edge, the surveyor's lines) as paper * Keep + Over,
    /// and its grain. (Made on every open, these and the blurs were 0.95 s of the frame, N25.)</summary>
    sealed record FogSheet(float[] Rag, Vector3[] Paper, float[] Keep, Vector3[] Over, float[] Grain);

    static readonly Lazy<FogSheet> Sheet = new(SheetFor, System.Threading.LazyThreadSafetyMode.ExecutionAndPublication);

    static FogSheet SheetFor()
    {
        const int F = 600;
        var rag = new float[F * F]; var paper = new Vector3[F * F]; var keep = new float[F * F]; var over = new Vector3[F * F]; var grain = new float[F * F];
        System.Threading.Tasks.Parallel.For(0, F, y =>
        {
            for (int x = 0; x < F; x++)
            {
                int q = y * F + x;
                float u = x / (float)F, v = y / (float)F;
                // The edge of the known, made ragged by the brush: a broad wobble and a fine one.
                rag[q] = (Fbm(u * 5, v * 5, 3) - 0.5f) * 0.7f + (Fbm(u * 38, v * 38, 2) - 0.5f) * 0.16f;
                // The blank sheet: mottled with age, foxed here and there, a fibre grain, browner toward its edge.
                float mottle = Fbm(u * 5 + 11, v * 5 + 3, 4);
                paper[q] = new Vector3(214, 198, 160).Lerp(new Vector3(178, 154, 112), Mathf.SmoothStep(0.35f, 0.8f, mottle));
                float fox = Mathf.SmoothStep(0.74f, 0.86f, Fbm(u * 26 + 5, v * 26 + 9, 2)) * 0.45f;
                grain[q] = (float)(Hash(x, y) - 0.5) * 7 + (float)(Hash(x / 3, y * 2) - 0.5) * 5;
                float edge = Mathf.Min(Mathf.Min(u, 1 - u), Mathf.Min(v, 1 - v));
                float brown = (1 - Mathf.SmoothStep(0f, 0.09f, edge)) * 0.6f;
                // The surveyor's lines across the blank: sixteen rhumbs from the middle and a circle, faint.
                float du = u - 0.5f, dv = v - 0.5f, rad = Mathf.Sqrt(du * du + dv * dv);
                float rhumb = rad * F * Mathf.Abs(Mathf.Sin(8 * Mathf.Atan2(dv, du))) / 8;
                float line = Mathf.Max(1 - Mathf.SmoothStep(0.3f, 1.1f, rhumb), 1 - Mathf.SmoothStep(0.4f, 1.3f, Mathf.Abs(rad - 0.42f) * F)) * 0.22f * Mathf.SmoothStep(0.02f, 0.1f, rad);
                // The three lerps toward fixed inks, folded: p -> p * keep + over.
                keep[q] = (1 - fox) * (1 - brown) * (1 - line);
                over[q] = (new Vector3(150, 104, 58) * fox * (1 - brown) + new Vector3(96, 62, 30) * brown) * (1 - line) + new Vector3(110, 76, 42) * line;
            }
        });
        return new FogSheet(rag, paper, keep, over, grain);
    }

    /// <summary>Smooth value noise, summed over octaves (0 to 1).</summary>
    static float Fbm(float x, float y, int octaves)
    {
        float sum = 0, amp = 0.5f, norm = 0;
        for (int o = 0; o < octaves; o++)
        {
            int x0 = (int)Mathf.Floor(x), y0 = (int)Mathf.Floor(y);
            float tx = x - x0, ty = y - y0;
            tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty);
            float a = (float)Hash(x0, y0), b = (float)Hash(x0 + 1, y0), c = (float)Hash(x0, y0 + 1), d = (float)Hash(x0 + 1, y0 + 1);
            sum += amp * Mathf.Lerp(Mathf.Lerp(a, b, tx), Mathf.Lerp(c, d, tx), ty);
            norm += amp;
            amp *= 0.5f; x *= 2.03f; y *= 2.03f;
        }
        return sum / norm;
    }

    /// <summary>The table the sheet lies on, past the paper's edge: dark leather, lit a little in the middle.</summary>
    static readonly Color Dark = new(0.075f, 0.058f, 0.048f);

    /// <summary>A box blur of a square field, across then down (each pixel the mean of the 2r+1 inside the field):
    /// a running sum, so its cost does not grow with r (at r 28 it was most of the fog's 0.95 s, N25).</summary>
    internal static float[] Blur(float[] a, int n, int r)
    {
        var b = new float[a.Length];
        var c = new float[a.Length];
        System.Threading.Tasks.Parallel.For(0, n, y =>
        {
            var pre = new double[n + 1];
            for (int x = 0; x < n; x++) pre[x + 1] = pre[x] + a[y * n + x];
            for (int x = 0; x < n; x++) { int lo = Math.Max(0, x - r), hi = Math.Min(n - 1, x + r); b[y * n + x] = (float)((pre[hi + 1] - pre[lo]) / (hi - lo + 1)); }
        });
        System.Threading.Tasks.Parallel.For(0, n, x =>
        {
            var pre = new double[n + 1];
            for (int y = 0; y < n; y++) pre[y + 1] = pre[y] + b[y * n + x];
            for (int y = 0; y < n; y++) { int lo = Math.Max(0, y - r), hi = Math.Min(n - 1, y + r); c[y * n + x] = (float)((pre[hi + 1] - pre[lo]) / (hi - lo + 1)); }
        });
        return c;
    }

    /* --------------------------------------------------------- the atlas -- */

    /// <summary>The drawing's size at zoom 1.</summary>
    const int F = 1080;
    /// <summary>Opened wide (the owner: the Journal and the Map keep to the book's half-window panel,
    /// "with an option to expand"); kept for the session, so the map opens as it was left.</summary>
    static bool wide;
    /// <summary>The map's window: in the panel, its width by most of its height; opened wide, the panel's
    /// width less the list's column beside it.</summary>
    Vector2 viewSize = new(844, 600);
    const float ListW = 440, Between = 32;
    float minZoom = 0.6f;
    Vector2 panTo;
    bool gliding;
    // (M4 lead 14, r3c M4: a line chosen frames her with it: the zoom eases with the pan; the first frame after the
    // open is set, not glided, so the map never opens sliding onto bare paper)
    float zoomTo = -1, openZoom = 1;
    double builtAt = -1;
    // (M4 lead 14, r3d look) a row hovered only once the mouse has moved since the map opened: a cursor resting where a
    // row appears is not a choice, and it would pull the opening view off her and the goal
    bool moved;
    public override void _Input(InputEvent e)
    {
        base._Input(e);
        if (e is InputEventMouseMotion m && m.Relative.LengthSquared() > 4) moved = true;
    }
    Control? ring;
    double t;
    float extent = 1;
    Vector2 youAt;
    Polygon2D? you;   // her arrow: a mark the names keep clear of (r3d S3: "YOUR CAMP" was printed through it)

    // In the panel she stands in the world beside it, near enough that her face reads (as for the rest
    // of the book); opened wide, the view is the map's.
    public override float CameraShift => wide ? 0 : -330;
    public override float CameraNear => wide ? 1 : 0.56f;
    public override (float Pitch, float Distance, float Height)? CameraFrame => wide ? null : BookFrame;

    /// <summary>A mark the list can name: where, what, and its words.</summary>
    readonly record struct Entry(double X, double Z, MarkKind Kind, string Label, bool Objective = false);

    /// <summary>The triggers zoom (or , and .); Y finds you; Z (R3) opens it wide or folds it back; focus
    /// on a line of the list glides the map to it.</summary>
    public override bool Key(Act a)
    {
        switch (a)
        {
            case Act.SubNext: zoom = Math.Min(4f, zoom * 1.25f); zoomTo = -1; Place(F); return true;
            case Act.SubPrev: zoom = Math.Max(minZoom, zoom / 1.25f); zoomTo = -1; Place(F); return true;
            case Act.Alt2: FindMe(); return true;
            case Act.Expand: Widen(); return true;
        }
        return false;
    }

    void Widen()
    {
        wide = !wide;
        Sound.Sfx.Page();
        Refresh();
    }

    void FindMe()
    {
        if (G.Battle is not { } b) return;
        Glide(b.Player.X, b.Player.Z, null);
        Sound.Sfx.Hover();
    }

    /// <summary>The map moves to a place, and a ring marks it (none: just move).</summary>
    void Glide(double x, double z, Vector2? mark)
    {
        zoomTo = -1;
        panTo = new Vector2(Math.Clamp(-(float)x / extent, -0.5f, 0.5f), Math.Clamp(-(float)z / extent, -0.5f, 0.5f));
        gliding = true;
        if (ring != null && IsInstanceValid(ring))
        {
            ring.Visible = mark != null;
            if (mark is { } m) ring.Position = m - ring.Size / 2;
        }
    }

    /// <summary>M4 lead 14 (judge r3c M4): a line chosen frames her and its mark together, 80 px clear of the window's
    /// edge, at the zoom the map opened on or wider (at minZoom the whole zone shows, so the two always fit); right
    /// after the open it is set at once.</summary>
    void FrameWith(double x, double z, Vector2 at)
    {
        if (G.Battle is not { } b) { Glide(x, z, at); return; }
        double px = b.Player.X, pz = b.Player.Z;
        float du = (float)(Math.Abs(x - px) / extent) * F, dv = (float)(Math.Abs(z - pz) / extent) * F;
        float k = Math.Min((viewSize.X - 160) / Math.Max(du, 1), (viewSize.Y - 160) / Math.Max(dv, 1));
        float zt = Math.Clamp(Math.Min(k, openZoom), minZoom, 4f);
        Glide((x + px) / 2, (z + pz) / 2, at);
        if (builtAt >= 0 && t - builtAt < 0.35) { zoom = zt; pan = panTo; gliding = false; Place(F); return; }
        zoomTo = zt;
    }

    // (--map-measure: what the open cost, and every frame over 50 ms while it is up, the arena's freeze check)
    static readonly bool measure = Args.Has("map-measure");
    ulong lastTick;
    int frames;
    double worst;
    public override void _Process(double delta)
    {
        base._Process(delta);
        if (measure)
        {
            ulong now = Time.GetTicksUsec();
            double d = lastTick == 0 ? 0 : (now - lastTick) / 1000.0;
            lastTick = now;
            frames++;
            if (frames > 2) worst = Math.Max(worst, d);
            if (d > 50) GD.Print($"MAPMEASURE frame {frames}: {d:F1} ms");
            if (frames % 60 == 0) GD.Print($"MAPMEASURE {frames} frames open, worst after the first two {worst:F1} ms");
        }
        t += delta;
        if (gliding)
        {
            panTo = Held(panTo);
            float ke = 1 - Mathf.Exp(-9 * (float)delta);
            if (zoomTo > 0) zoom = Mathf.Abs(zoom - zoomTo) < 0.002f ? zoomTo : Mathf.Lerp(zoom, zoomTo, ke);
            pan = pan.Lerp(Held(panTo), ke);
            if (pan.DistanceTo(Held(panTo)) < 0.0005f && (zoomTo < 0 || zoom == zoomTo)) { pan = Held(panTo); gliding = false; zoomTo = -1; }
            Place(F);
        }
        if (ring != null && IsInstanceValid(ring) && ring.Visible)
        {
            float k = 1 + 0.18f * Mathf.Sin((float)t * 6);
            ring.Scale = new Vector2(k, k) / zoom;
        }
    }

    protected override void Build()
    {
        var scene = G.Scene!;
        var zone = G.Zone!;
        var sw = System.Diagnostics.Stopwatch.StartNew();
        extent = Extent(scene.Data.Meta);
        names.Clear();
        // The book's own panel, or the same panel opened across the screen; the place's name over its map.
        float pw = wide ? 1920 - 32 : BookW, inner = pw - 2 * Margin;
        var v = BookPanel(null, width: pw, expand: Widen, wide: wide);
        var head = Style.V(0, new Title(zone.Name, 30, false));
        if (zone.Region is string region && region != "") head.AddChild(Style.Label(region, Style.TextItalic, 15, Kit.Dim, false, HorizontalAlignment.Center));
        v.AddChild(head);
        viewSize = wide ? new Vector2(inner - ListW - Between, 830) : new Vector2(inner, 600);
        var body = Style.H((int)Between);
        v.AddChild(body);
        // The map in its window: the sheet on the table, cut cleanly at the window's edge.
        var frame = new Control { CustomMinimumSize = viewSize, Size = viewSize, ClipContents = true, MouseFilter = MouseFilterEnum.Stop };
        body.AddChild(frame);
        // Past the paper's edge, the table it lies on: dark leather, a little lit where the map lies.
        frame.AddChild(new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { Dark.Lightened(0.12f), Dark, Dark.Darkened(0.45f) }, Offsets = new[] { 0f, 0.55f, 1f } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.4f, 0.55f), FillTo = new Vector2(1.1f, 1.1f), Width = 256, Height = 256,
            },
            Size = viewSize, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
        });
        world = new Control { Size = new Vector2(F, F), MouseFilter = MouseFilterEnum.Ignore };
        frame.AddChild(world);
        // The sheet's shadow on the table.
        for (int i = 6; i >= 1; i--)
            world.AddChild(new ColorRect { Color = new Color(0, 0, 0, 0.09f), Position = new Vector2(-i * 2.5f + 4, -i * 2.5f + 8), Size = new Vector2(F + i * 5, F + i * 5), MouseFilter = MouseFilterEnum.Ignore });
        // The expand mode first: a control is never smaller than its minimum, and the drawing's own is 1600.
        var drawing = Drawing(scene.Data);
        double drawMs = sw.Elapsed.TotalMilliseconds;
        world.AddChild(new TextureRect { ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, Texture = drawing, Size = new Vector2(F, F), MouseFilter = MouseFilterEnum.Ignore, TextureFilter = TextureFilterEnum.LinearWithMipmaps });
        // Clipped to the paper: a tree on its edge would hang its crown into the dark past it.
        world.AddChild(new MapInk(scene, extent, F) { Size = new Vector2(F, F), MouseFilter = MouseFilterEnum.Ignore, ClipContents = true });
        var zs = G.Journey.World.Zone(zone.Id);
        var seen = zs.TryGetValue("seen", out var f) && f.Str is { } s ? s : new string('0', Journey.FogN * Journey.FogN);
        double fog0 = sw.Elapsed.TotalMilliseconds;
        world.AddChild(new TextureRect { ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, Texture = Fog(seen, Journey.FogN), Size = new Vector2(F, F), MouseFilter = MouseFilterEnum.Ignore });
        double fogMs = sw.Elapsed.TotalMilliseconds - fog0;
        bool Seen(double x, double z)
        {
            int i = (int)Math.Floor((x / extent + 0.5) * Journey.FogN), j = (int)Math.Floor((z / extent + 0.5) * Journey.FogN);
            return i >= 0 && j >= 0 && i < Journey.FogN && j < Journey.FogN && seen[j * Journey.FogN + i] == '1';
        }
        Vector2 Px(double x, double z) => new((float)((x / extent + 0.5) * F), (float)((z / extent + 0.5) * F));
        double mark0 = sw.Elapsed.TotalMilliseconds;
        var entries = zone.MapMarks().Where(m => m.Kind is MarkKind.Exit or MarkKind.Quest || Seen(m.X, m.Z)).Select(m => new Entry(m.X, m.Z, m.Kind, m.Label, m.Objective)).ToList();
        foreach (var gp in G.GoalPins()) entries.Add(new Entry(gp.X, gp.Z, MarkKind.Goal, gp.Def.Label));
        int marksAt = world.GetChildCount();
        foreach (var m in entries.OrderByDescending(m => m.Kind == MarkKind.Place)) Mark(world, Px(m.X, m.Z), m.Label, m.Kind, m.Objective);
        if (measure) GD.Print($"MAPMEASURE build: drawing {drawMs:F1} ms, fog {fogMs:F1} ms, {entries.Count} marks {sw.Elapsed.TotalMilliseconds - mark0:F1} ms, extent {extent:F0}, zone {zone.Id}");
        // The ring that marks what the list has chosen.
        ring = new Panel { Size = new Vector2(46, 46), PivotOffset = new Vector2(23, 23), MouseFilter = MouseFilterEnum.Ignore, Visible = false };
        // (M4 lead 14, r3c M4: in the drawing's own ink; the red on the map is hers alone)
        var rs = Style.Box(new Color(0, 0, 0, 0), new Color("#3a2414"), 3, 23, 0);
        ring.AddThemeStyleboxOverride("panel", rs);
        world.AddChild(ring);
        // (M4 lead 14, r3d look: the ring under the marks, so a name's parchment outline knocks the ring out where they cross,
        // as a printed map's label knocks out a line, and never an ink circle struck through the name)
        world.MoveChild(ring, marksAt);
        // You.
        if (G.Battle is { } b)
        {
            youAt = Px(b.Player.X, b.Player.Z);
            world.AddChild(you = new Polygon2D { Polygon = new[] { new Vector2(0, -11), new Vector2(8, 8), new Vector2(0, 4), new Vector2(-8, 8) }, Color = new Color("#b8321e"), Position = youAt, Rotation = (float)(Math.PI - b.Player.Facing) });
        }
        frame.GuiInput += e => Input(e, F);
        minZoom = Math.Min(viewSize.X, viewSize.Y) / F * 0.9f;
        // Opened on what is known, whatever the zone's own focus.
        Fit(seen);
        openZoom = zoom;
        builtAt = t;
        moved = false;
        Place(F);
        // A compass in the window's corner, the way the old maps had one.
        var rose = Glyphs.Icon("compass", 56, Style.Gold with { A = 0.75f });
        rose.Position = new Vector2(20, 38);
        frame.AddChild(rose);
        var north = Style.Label("N", Style.Display, 18, Style.GoldHi, false, HorizontalAlignment.Center);
        north.Position = new Vector2(20, 14);
        north.Size = new Vector2(56, 22);
        frame.AddChild(north);

        var p0 = G.Battle?.Player;
        IEnumerable<Entry> Near(IEnumerable<Entry> items) => items.OrderBy(e => p0 == null ? 0 : Math.Sqrt((e.X - p0.X) * (e.X - p0.X) + (e.Z - p0.Z) * (e.Z - p0.Z)));
        // (M4 lead 14, r3d look) opened on her and the first step of her road (the list's first row, ringed), in every input
        // mode: Nav runs a row's focus at a build only in key mode, so with the mouse the map opened on the explored ground alone
        if (Near(entries.Where(e => e.Kind is MarkKind.Quest or MarkKind.Turn or MarkKind.Exit or MarkKind.Goal)).Select(e => (Entry?)e).FirstOrDefault() is { } road0)
            FrameWith(road0.X, road0.Z, Px(road0.X, road0.Z));
        // The legend, in the marks' own look (the corner map's too).
        Control Legend(int columns, bool road = false)
        {
            var legend = new GridContainer { Columns = columns, MouseFilter = MouseFilterEnum.Ignore };
            legend.AddThemeConstantOverride("h_separation", 22);
            legend.AddThemeConstantOverride("v_separation", 6);
            // (M4 lead 14, r3c S5: opened wide, the diamond is named too)
            if (road && entries.Any(e => e.Objective))
                legend.AddChild(Style.H(6, new Minimap.GoalDiamond { CustomMinimumSize = new Vector2(18, 18), Size = new Vector2(18, 18) }, Style.Label("Your road", Style.Ui, Style.Caption, Style.Ink)));
            foreach (var (kind, text) in new[] { (MarkKind.Quest, "Someone needs you"), (MarkKind.Exit, "The way out"), (MarkKind.Danger, "Hostile"), (MarkKind.Mystery, "Unexplained") })
                legend.AddChild(Style.H(6, Minimap.Mark(kind, 18), Style.Label(text, Style.Ui, Style.Caption, Style.Ink)));
            return legend;
        }
        // Zoom and find-me as words (they were a slab of buttons on the drawing).
        Control Tools()
        {
            var tools = Style.H(Style.Gap4);
            Control Tool(string? pad, string text, Action go)
            {
                var wd = Kit.Word(text, go, Style.GoldHi, 15);
                if (pad == null || !Controls.Instance.UsingPad) return Nav.Skip(wd);
                var r = Style.H(6, Style.PadButton(pad), Nav.Skip(wd));
                foreach (var c in r.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
                return r;
            }
            tools.AddChild(Tool("Y", "Find me", FindMe));
            tools.AddChild(Tool("RT", "Closer", () => Key(Act.SubNext)));
            tools.AddChild(Tool("LT", "Further", () => Key(Act.SubPrev)));
            tools.AddChild(Tool(null, "All I know", () => { Fit(seen, cover: false); gliding = false; Place(F); }));
            return tools;
        }
        Control Hints() => Controls.Instance.UsingPad
            ? Style.Hints((Act.Up, "Choose"), (Act.Alt2, "Find me"), (Act.Expand, wide ? "Fold" : "Open wide"), (Act.Cancel, "Close"))
            : Style.Label("Wheel to zoom · drag to move · a line to find it", Style.TextItalic, Style.Caption, Style.InkDim);

        if (!wide)
        {
            // In the panel: under the map, the road she is on (the way out, who needs her), nearest first,
            // in two columns; then the legend and the tools. The rest of the list is the wide map's.
            var road = Near(entries.Where(e => e.Kind is MarkKind.Quest or MarkKind.Turn or MarkKind.Exit or MarkKind.Goal)).Take(4).ToList();
            if (road.Count > 0)
            {
                v.AddChild(Kit.Head("Your road", "nearest first"));
                var cols = new GridContainer { Columns = 2, MouseFilter = MouseFilterEnum.Ignore };
                cols.AddThemeConstantOverride("h_separation", (int)Between);
                cols.AddThemeConstantOverride("v_separation", 0);
                foreach (var e in road)
                {
                    var line = Line(e, Px(e.X, e.Z));
                    line.CustomMinimumSize = new Vector2((inner - Between) / 2, 34);
                    cols.AddChild(line);
                }
                v.AddChild(cols);
            }
            var foot = Style.H(Style.Gap5, Legend(4));
            foot.Alignment = BoxContainer.AlignmentMode.Center;
            v.AddChild(foot);
            var tools = Style.H(Style.Gap5, Tools(), Hints());
            tools.Alignment = BoxContainer.AlignmentMode.Center;
            foreach (var c in tools.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            v.AddChild(tools);
            return;
        }

        // Opened wide: the list beside the map, as type (its lines were boxes): where to go, what has been
        // found, what to beware of; each line glides the map to it.
        var col = Style.V(Style.Gap3);
        col.CustomMinimumSize = new Vector2(ListW, 0);
        body.AddChild(col);
        col.AddChild(Kit.Head("Where to go", "nearest first"));
        var list = Style.V(0);
        bool first = true;
        void Group(string title, IEnumerable<Entry> items)
        {
            var these = Near(items).ToList();
            if (these.Count == 0) return;
            if (!first) list.AddChild(Style.Gap(Style.Gap4));
            first = false;
            list.AddChild(Style.Label(title.ToUpperInvariant(), Style.UiHeavy, 12, Kit.HeadInk, false, HorizontalAlignment.Left, false));
            foreach (var e in these) list.AddChild(Line(e, Px(e.X, e.Z)));
        }
        Group("Your road", entries.Where(e => e.Kind is MarkKind.Quest or MarkKind.Turn or MarkKind.Exit or MarkKind.Goal));
        Group("People", entries.Where(e => e.Kind == MarkKind.Person));
        Group("Places", entries.Where(e => e.Kind == MarkKind.Place));
        Group("Danger and the strange", entries.Where(e => e.Kind is MarkKind.Danger or MarkKind.Mystery));
        if (entries.Count == 0) list.AddChild(Style.Label("Nothing found yet. The map fills in as you walk.", Style.TextItalic, Style.Body, Style.InkDim, true));
        // The list hugs its lines, and scrolls only past the room the column has.
        var scroll = Style.Scroll(list);
        scroll.SizeFlagsVertical = SizeFlags.Fill;
        col.AddChild(scroll);
        col.AddChild(Kit.RuleH());
        col.AddChild(Legend(2, road: true));
        col.AddChild(Tools());
        col.AddChild(Hints());
        // (none of the list's words wrap, so its height is known before it is laid out)
        float room = viewSize.Y - col.GetCombinedMinimumSize().Y;
        scroll.CustomMinimumSize = new Vector2(0, Math.Min(list.GetCombinedMinimumSize().Y, Math.Max(120, room)));
    }
    /// <summary>
    /// Frames what the survivor knows: every walked cell and where they stand,
    /// with a margin, as large as the view allows. The map opens on the known
    /// world, not on a square of blank paper with the zone at its edge.
    /// </summary>
    void Fit(string seen, bool cover = true)
    {
        int n = Journey.FogN;
        float u0 = 1, v0 = 1, u1 = 0, v1 = 0;
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                if (j * n + i >= seen.Length || seen[j * n + i] != '1') continue;
                u0 = Math.Min(u0, i / (float)n); v0 = Math.Min(v0, j / (float)n);
                u1 = Math.Max(u1, (i + 1) / (float)n); v1 = Math.Max(v1, (j + 1) / (float)n);
            }
        if (G.Battle is { } b)
        {
            float pu = (float)(b.Player.X / extent + 0.5), pv = (float)(b.Player.Z / extent + 0.5);
            u0 = Math.Min(u0, pu - 0.04f); v0 = Math.Min(v0, pv - 0.04f);
            u1 = Math.Max(u1, pu + 0.04f); v1 = Math.Max(v1, pv + 0.04f);
        }
        if (u1 <= u0 || v1 <= v0) { u0 = v0 = 0; u1 = v1 = 1; }
        // A margin, and never closer than a quarter of the zone.
        float cu = (u0 + u1) / 2, cv = (v0 + v1) / 2;
        float su = Math.Max(0.25f, (u1 - u0) * 1.15f), sv = Math.Max(0.25f, (v1 - v0) * 1.15f);
        minZoom = Math.Min(viewSize.X, viewSize.Y) / F * 0.9f;
        // Opened, it fills its window with the known world (cover: a square town in a wide window would
        // leave bands of bare table either side; what is cut off is reached by the list or a drag); "All I
        // know" shows the whole of it at once (contain).
        float kx = viewSize.X / (su * F), ky = viewSize.Y / (sv * F);
        zoom = Math.Clamp(cover ? Math.Max(kx, ky) : Math.Min(kx, ky), minZoom, 4f);
        pan = new Vector2(0.5f - cu, 0.5f - cv);
    }

    /// <summary>A line of the list as type over a fine rule (no box): its mark and its name, and in
    /// a column at the right how far and which way from you, so the distances line up and are
    /// scanned. The pointer lights the name in ember and glides the map to it.</summary>
    Control Line(Entry e, Vector2 at)
    {
        void Go() { Glide(e.X, e.Z, at); zoom = Math.Max(zoom, 1.8f); Place(F); }
        void Frame() => FrameWith(e.X, e.Z, at);
        var b = new Button { Flat = true, FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand, CustomMinimumSize = new Vector2(0, 34), SizeFlagsHorizontal = SizeFlags.ExpandFill };
        foreach (var s in new[] { "normal", "hover", "pressed" }) b.AddThemeStyleboxOverride(s, new LineUnder());
        b.AddThemeStyleboxOverride("focus", new StyleBoxEmpty());
        var name = Style.Label(e.Label, Style.UiBold, Style.Small, Style.Ink);
        name.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        name.TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis;
        // (M4 lead 14, r3c S5: the one place sought wears the diamond the map and the corner map give it)
        Control icon = e.Objective ? new Minimap.GoalDiamond { CustomMinimumSize = new Vector2(18, 18), Size = new Vector2(18, 18) } : Minimap.Mark(e.Kind, 18);
        var row = Style.H(10, icon, name);
        if (G.Battle?.Player is { } p)
        {
            double dx = e.X - p.X, dz = e.Z - p.Z, d = Math.Sqrt(dx * dx + dz * dz);
            row.AddChild(Style.Label(d < 8 ? "here" : $"{Math.Round(d / 5) * 5:0} m {Way(dx, dz)}", Style.TextItalic, Style.Caption, Style.InkDim, false, HorizontalAlignment.Right));
        }
        foreach (var c in row.GetChildren().OfType<Control>()) c.SizeFlagsVertical = SizeFlags.ShrinkCenter;
        row.MouseFilter = MouseFilterEnum.Ignore;
        row.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
        b.AddChild(row);
        b.Pressed += Go;
        Nav.Mark(b, $"mark:{e.Label}", Go, focus: Frame);
        b.MouseEntered += () => { if (!moved) return; name.AddThemeColorOverride("font_color", Style.EmberHi); Frame(); };
        b.MouseExited += () => name.AddThemeColorOverride("font_color", Style.Ink);
        return b;
    }

    /// <summary>Which way, in the eight words of a compass (north is up the map).</summary>
    static string Way(double dx, double dz)
    {
        string[] w = { "north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west" };
        double a = Math.Atan2(dx, -dz);
        int i = (int)Math.Round(a / (Math.PI / 4));
        return w[(i % 8 + 8) % 8];
    }

    /// <summary>Each mark's name on the drawing: where its mark stands, the words, what it is, how wide.</summary>
    readonly List<(Control Node, Label Text, MarkKind Kind, float W)> names = new();

    void Mark(Control parent, Vector2 at, string label, MarkKind kind, bool objective = false)
    {
        bool place = kind == MarkKind.Place;
        var (_, color) = Minimap.Look(kind);
        var node = new Control { Position = at, MouseFilter = MouseFilterEnum.Ignore };
        if (!place)
        {
            // (M4 lead 13, r3b: the one place sought wears the minimap's and the tracker's diamond here too, not quest.png)
            Control icon = objective ? new Minimap.GoalDiamond() : Minimap.Mark(kind, 22);
            icon.Position = -icon.Size / 2;
            node.AddChild(icon);
        }
        var font = place ? Style.Display : Style.TextBold;
        int size = place ? 16 : 15;
        var l = Style.Label(label, font, size, place ? new Color("#3a2414") : color, false, HorizontalAlignment.Center, false);
        l.AddThemeColorOverride("font_outline_color", new Color("#e4d6b6"));
        l.AddThemeConstantOverride("outline_size", 5);
        node.AddChild(l);
        parent.AddChild(node);
        // (M4 lead 14, r3e S1: the width the label really draws at, its theme's padding and outline included;
        // the string alone was ~32 px short, so names grew to the right of their marks and their keep-clear rects fell short)
        float w = Mathf.Max(font.GetStringSize(label, HorizontalAlignment.Left, -1, size).X + 8, l.GetMinimumSize().X);
        l.Size = new Vector2(w, 22);
        l.Position = new Vector2(-w / 2, place ? -11 : 12);
        names.Add((node, l, kind, w));
    }

    /// <summary>
    /// The names set clear of one another and of every mark, at the size they are read (two names
    /// printed over each other read as neither: "WENI Old Wenna"). A place keeps its name on its
    /// roof if it can, above or below it if not; then the way out and who needs you, then people,
    /// each under its mark, or above it, or to a side; a name with nowhere to go is left to the list.
    /// </summary>
    void Declutter()
    {
        var taken = new List<Rect2>();
        foreach (var (node, _, kind, _) in names)
            if (kind != MarkKind.Place) taken.Add(new Rect2(node.GlobalPosition - new Vector2(11, 11), new Vector2(22, 22)));
        if (you != null && IsInstanceValid(you)) { float h = 12 * you.GlobalScale.X; taken.Add(new Rect2(you.GlobalPosition - new Vector2(h, h), new Vector2(2 * h, 2 * h))); }
        static int Order(MarkKind k) => k == MarkKind.Place ? 0 : k is MarkKind.Quest or MarkKind.Exit or MarkKind.Goal ? 1 : k == MarkKind.Person ? 2 : 3;
        foreach (var (node, text, kind, w) in names.OrderBy(n => Order(n.Kind)))
        {
            Vector2[] spots = kind == MarkKind.Place
                ? [new(-w / 2, -11), new(-w / 2, -33), new(-w / 2, 11)]
                : [new(-w / 2, 12), new(-w / 2, -34), new(15, -11), new(-w - 15, -11)];
            text.Visible = false;
            foreach (var at in spots)
            {
                var r = new Rect2(node.GlobalPosition + at + new Vector2(2, 3), new Vector2(w - 4, 16));
                if (taken.Any(t => t.Intersects(r))) continue;
                taken.Add(r);
                text.Position = at;
                text.Visible = true;
                break;
            }
        }
    }

    void Place(int frame)
    {
        if (world == null) return;
        pan = Held(pan);
        world.Scale = new Vector2(zoom, zoom);
        // The point the pan names sits at the middle of the map's window.
        var centre = viewSize / 2;
        world.Position = centre - (new Vector2(0.5f, 0.5f) - pan) * frame * zoom;
        foreach (var c in world.GetChildren()) if (c is Control mk && mk is not TextureRect && mk is not ColorRect && mk is not MapInk && mk != ring) mk.Scale = new Vector2(1 / zoom, 1 / zoom);
        Declutter();
    }

    /// <summary>
    /// The pan kept so the drawing covers the view on each side where it is
    /// large enough to: the zone's edge never leaves a band of nothing beside
    /// the known world (opened at the Verge's west edge, a third of the view
    /// was past it). Where the drawing is smaller than the view, it is centred.
    /// </summary>
    Vector2 Held(Vector2 p)
    {
        float Axis(float v, float view)
        {
            float s = F * zoom;
            if (s <= view) return 0;
            float lim = 0.5f - view / (2 * s);
            return Math.Clamp(v, -lim, lim);
        }
        return new Vector2(Axis(p.X, viewSize.X), Axis(p.Y, viewSize.Y));
    }

    void Input(InputEvent e, int frame)
    {
        switch (e)
        {
            case InputEventMouseButton { ButtonIndex: MouseButton.WheelUp, Pressed: true }: zoom = Math.Min(4f, zoom * 1.18f); zoomTo = -1; Place(frame); break;
            case InputEventMouseButton { ButtonIndex: MouseButton.WheelDown, Pressed: true }: zoom = Math.Max(minZoom, zoom / 1.18f); zoomTo = -1; Place(frame); break;
            case InputEventMouseButton { ButtonIndex: MouseButton.Left } mb:
                dragging = mb.Pressed;
                dragFrom = mb.Position;
                panFrom = pan;
                gliding = false;
                break;
            case InputEventMouseMotion mm when dragging:
                var d = (mm.Position - dragFrom) / (frame * zoom);
                pan = new Vector2(Math.Clamp(panFrom.X + d.X, -0.5f, 0.5f), Math.Clamp(panFrom.Y + d.Y, -0.5f, 0.5f));
                Place(frame);
                break;
        }
    }
}

/// <summary>The map's ink: every wall and house, each tree and rock.</summary>
public partial class MapInk : Control
{
    readonly WorldScene scene;
    readonly float extent, size;

    public MapInk(WorldScene scene, float extent, float size) { this.scene = scene; this.extent = extent; this.size = size; }

    static double Hash(double x, double y) { double s = Math.Sin(x * 127.1 + y * 311.7) * 43758.5453; return s - Math.Floor(s); }

    /// <summary>The ink of each place, made once: its shapes as triangles (and the dead trees' hairlines), in the
    /// order they were drawn, a few calls in all. (A call a shape, thousands of them in an arena, was 50-60 ms of
    /// the frame after every open, N25.)</summary>
    sealed class Batch
    {
        public bool Thin;
        public readonly List<Vector2> Pts = new();
        public readonly List<Color> Cols = new();
        public readonly List<int> Idx = new();
    }
    static readonly Dictionary<string, List<Batch>> inks = new();
    List<Batch> batches = new();

    Batch Into(bool thin)
    {
        if (batches.Count == 0 || batches[^1].Thin != thin) batches.Add(new Batch { Thin = thin });
        return batches[^1];
    }

    /// <summary>A filled shape (each drawn here is convex, or star-shaped round its middle: a fan from the middle).</summary>
    void InkPoly(Vector2[] pts, Color col)
    {
        var b = Into(false);
        var mid = Vector2.Zero;
        foreach (var p in pts) mid += p;
        mid /= pts.Length;
        int o = b.Pts.Count;
        b.Pts.Add(mid); b.Cols.Add(col);
        foreach (var p in pts) { b.Pts.Add(p); b.Cols.Add(col); }
        for (int i = 0; i < pts.Length; i++) { b.Idx.Add(o); b.Idx.Add(o + 1 + i); b.Idx.Add(o + 1 + (i + 1) % pts.Length); }
    }

    /// <summary>An outline of a width (scaled with the map, as the canvas's own), each stretch a quad squared off at its ends.</summary>
    void InkLine(Vector2[] pts, Color col, float w)
    {
        var b = Into(false);
        for (int i = 0; i + 1 < pts.Length; i++)
        {
            Vector2 a = pts[i], c = pts[i + 1], d = c - a;
            if (d.LengthSquared() < 1e-8f) continue;
            d = d.Normalized() * (w / 2);
            var n = new Vector2(-d.Y, d.X);
            int o = b.Pts.Count;
            b.Pts.Add(a - d + n); b.Pts.Add(c + d + n); b.Pts.Add(c + d - n); b.Pts.Add(a - d - n);
            for (int k = 0; k < 4; k++) b.Cols.Add(col);
            b.Idx.Add(o); b.Idx.Add(o + 1); b.Idx.Add(o + 2); b.Idx.Add(o); b.Idx.Add(o + 2); b.Idx.Add(o + 3);
        }
    }

    /// <summary>A hairline (a pixel whatever the zoom, as the canvas's own).</summary>
    void InkHair(Vector2 a, Vector2 c, Color col)
    {
        var b = Into(true);
        b.Pts.Add(a); b.Pts.Add(c); b.Cols.Add(col);
    }

    public override void _Draw()
    {
        var isw = System.Diagnostics.Stopwatch.StartNew();
        string key = $"{scene.Data.Id}:{extent}:{size}";
        if (!inks.TryGetValue(key, out var made)) { batches = new(); Ink(); inks[key] = made = batches; }
        var item = GetCanvasItem();
        foreach (var b in made)
        {
            if (b.Thin) RenderingServer.CanvasItemAddMultiline(item, b.Pts.ToArray(), b.Cols.ToArray());
            else if (b.Idx.Count > 0) RenderingServer.CanvasItemAddTriangleArray(item, b.Idx.ToArray(), b.Pts.ToArray(), b.Cols.ToArray());
        }
        if (Args.Has("map-measure")) GD.Print($"MAPMEASURE ink drawn in {isw.Elapsed.TotalMilliseconds:F1} ms ({made.Sum(b => b.Thin ? b.Pts.Count / 2 : b.Idx.Count / 3)} pieces, {made.Count} calls)");
    }

    void Ink()
    {
        var meta = scene.Data.Meta;
        float s = size / extent;
        Vector2 Px(double x, double z) => new((float)((x / extent + 0.5) * size), (float)((z / extent + 0.5) * size));
        // Only what lies on the paper: past its edge there is no fog to hide it.
        bool On(Vector2 p) => p.X >= 0 && p.Y >= 0 && p.X <= size && p.Y <= size;
        foreach (var c in meta.Collision().All())
        {
            if (c.Kind != ColliderKind.Box || c.PlayerOnly || c.Hw * c.Hd < 0.6) continue;
            var at = Px(c.X, c.Z);
            if (!On(at)) continue;
            float rot = -(float)c.Rot;
            Vector2 R(double x, double z) => at + new Vector2((float)x * s, (float)z * s).Rotated(rot);
            var pts = new[] { R(-c.Hw, -c.Hd), R(c.Hw, -c.Hd), R(c.Hw, c.Hd), R(-c.Hw, c.Hd) };
            InkPoly(pts, c.Soft ? new Color(110 / 255f, 86 / 255f, 58 / 255f, 0.35f) : new Color(84 / 255f, 60 / 255f, 40 / 255f, 0.8f));
            InkLine(pts.Append(pts[0]).ToArray(), new Color(48 / 255f, 32 / 255f, 20 / 255f, 0.9f), 1);
        }
        foreach (var bl in meta.Map?.Buildings ?? new())
        {
            double bx = bl.GetProperty("x").GetDouble(), bz = bl.GetProperty("z").GetDouble(), br = bl.GetProperty("r").GetDouble(), rot = bl.GetProperty("rot").GetDouble();
            var at = Px(bx, bz);
            if (!On(at)) continue;
            float r = (float)br * s;
            Vector2[] Hex(Vector2 o, float rr) => Enumerable.Range(0, 6).Select(a => o + new Vector2(Mathf.Cos((float)rot + a * Mathf.Pi / 3 + Mathf.Pi / 6), Mathf.Sin((float)rot + a * Mathf.Pi / 3 + Mathf.Pi / 6)) * rr).ToArray();
            InkPoly(Hex(at + new Vector2(r * 0.18f, r * 0.22f), r), new Color(60 / 255f, 40 / 255f, 22 / 255f, 0.35f));
            var outer = Hex(at, r);
            InkPoly(outer, new Color(128 / 255f, 74 / 255f, 52 / 255f, 0.95f));
            InkLine(outer.Append(outer[0]).ToArray(), new Color(46 / 255f, 28 / 255f, 16 / 255f, 0.95f), 1.4f);
            InkPoly(Hex(at, r * 0.55f), new Color(160 / 255f, 100 / 255f, 72 / 255f, 0.9f));
        }
        foreach (var f in meta.Map?.Flora ?? new())
        {
            if (f.ValueKind != System.Text.Json.JsonValueKind.Array || f.GetArrayLength() < 4) continue;
            string kind = f[0].GetString() ?? "";
            double x = f[1].GetDouble(), z = f[2].GetDouble(), sc = f[3].GetDouble();
            var p = Px(x, z);
            if (!On(p)) continue;
            float jit = (float)Hash(x, z);
            if (kind == "pine")
            {
                float r = (float)(2.2 * sc) * s;
                var tri = new[] { p + new Vector2(0, -r * 1.3f), p + new Vector2(r * 0.8f, r * 0.7f), p + new Vector2(-r * 0.8f, r * 0.7f) };
                InkPoly(tri, new Color((70 + jit * 20) / 255f, (88 + jit * 16) / 255f, 62 / 255f, 0.85f));
                InkLine(tri.Append(tri[0]).ToArray(), new Color(38 / 255f, 44 / 255f, 30 / 255f, 0.9f), 1);
            }
            else if (kind is "broadleaf" or "autumn" or "sick")
            {
                float r = (float)(2.6 * sc) * s;
                var pts = Enumerable.Range(0, 8).Select(a => p + new Vector2(Mathf.Cos(a / 7f * Mathf.Tau), Mathf.Sin(a / 7f * Mathf.Tau)) * r * (0.82f + (float)Hash(x + a, z) * 0.3f)).ToArray();
                var col = kind == "autumn" ? new Color((176 + jit * 30) / 255f, (110 + jit * 30) / 255f, 60 / 255f, 0.8f) : kind == "sick" ? new Color(140 / 255f, 150 / 255f, 90 / 255f, 0.8f) : new Color((96 + jit * 20) / 255f, (122 + jit * 20) / 255f, 70 / 255f, 0.8f);
                InkPoly(pts[..7], col);
                InkLine(pts, new Color(46 / 255f, 44 / 255f, 28 / 255f, 0.85f), 1);
            }
            else if (kind == "dead")
            {
                float r = (float)(1.8 * sc) * s;
                var ink = new Color(60 / 255f, 44 / 255f, 30 / 255f, 0.85f);
                InkHair(p + new Vector2(0, r), p + new Vector2(0, -r * 0.2f), ink);
                InkHair(p + new Vector2(0, -r * 0.2f), p + new Vector2(-r * 0.6f, -r), ink);
                InkHair(p + new Vector2(0, -r * 0.2f), p + new Vector2(r * 0.6f, -r * 0.9f), ink);
            }
            else
            {
                float r = (float)((kind == "cliff" ? 4 : 2.2) * sc) * s;
                var pts = Enumerable.Range(0, 7).Select(a => p + new Vector2(Mathf.Cos(a / 6f * Mathf.Tau + jit), Mathf.Sin(a / 6f * Mathf.Tau + jit)) * r * (0.7f + (float)Hash(x, z + a) * 0.4f)).ToArray();
                InkPoly(pts[..6], new Color(150 / 255f, 144 / 255f, 130 / 255f, 0.8f));
                InkLine(pts, new Color(60 / 255f, 56 / 255f, 48 / 255f, 0.9f), 1);
            }
        }
    }
}
