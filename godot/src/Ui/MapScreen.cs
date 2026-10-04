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
        img.GenerateMipmaps();
        var tex = ImageTexture.CreateFromImage(img);
        drawings[z.Id] = tex;
        return tex;
    }

    /// <summary>
    /// The land not yet walked, as a cartographer leaves it: the same sheet,
    /// blank and older (mottled, foxed, browned toward its edge), and where
    /// what you know ends, an ink wash that has bled into the paper and dried
    /// with a darker tide line, ragged as a brush leaves it. The walked land
    /// shows through clean. Opaque wherever nothing was walked: no ink shows
    /// through. (Was a flat dark at 94%: the owner, "it needs to look better".)
    /// </summary>
    static ImageTexture Fog(string seen, int n)
    {
        const int F = 600;
        float c = F / (float)n;
        var known = new float[F * F];
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
        for (int pass = 0; pass < 3; pass++) known = Blur(known, F, 5);
        // How near the known land is, broadly: the sheet is lit round what you know and browns away from it.
        var near = Blur(Blur(known, F, 28), F, 28);
        var px = new byte[F * F * 4];
        for (int y = 0; y < F; y++)
            for (int x = 0; x < F; x++)
            {
                float u = x / (float)F, v = y / (float)F;
                // The edge of the known, made ragged by the brush: a broad wobble and a fine one.
                float rag = (Fbm(u * 5, v * 5, 3) - 0.5f) * 0.7f + (Fbm(u * 38, v * 38, 2) - 0.5f) * 0.16f;
                float k = Mathf.Clamp(known[y * F + x] + rag, 0, 1);
                float cover = 1 - Mathf.SmoothStep(0.34f, 0.5f, k);
                if (cover <= 0.001f) continue;
                // The blank sheet: mottled with age, foxed here and there, a fibre grain, browner toward its edge.
                float mottle = Fbm(u * 5 + 11, v * 5 + 3, 4);
                float lit = Mathf.SmoothStep(0f, 0.45f, near[y * F + x]);
                var paper = new Vector3(214, 198, 160).Lerp(new Vector3(178, 154, 112), Mathf.SmoothStep(0.35f, 0.8f, mottle));
                paper = paper.Lerp(paper * new Vector3(0.66f, 0.6f, 0.52f), (1 - lit) * 0.75f);
                float fox = Mathf.SmoothStep(0.74f, 0.86f, Fbm(u * 26 + 5, v * 26 + 9, 2));
                paper = paper.Lerp(new Vector3(150, 104, 58), fox * 0.45f);
                float grain = (float)(Hash(x, y) - 0.5) * 7 + (float)(Hash(x / 3, y * 2) - 0.5) * 5;
                float edge = Mathf.Min(Mathf.Min(u, 1 - u), Mathf.Min(v, 1 - v));
                paper = paper.Lerp(new Vector3(96, 62, 30), (1 - Mathf.SmoothStep(0f, 0.09f, edge)) * 0.6f);
                // The surveyor's lines across the blank: sixteen rhumbs from the middle and a circle, faint.
                float du = u - 0.5f, dv = v - 0.5f, rad = Mathf.Sqrt(du * du + dv * dv);
                float rhumb = rad * F * Mathf.Abs(Mathf.Sin(8 * Mathf.Atan2(dv, du))) / 8;
                float line = Mathf.Max(1 - Mathf.SmoothStep(0.3f, 1.1f, rhumb), 1 - Mathf.SmoothStep(0.4f, 1.3f, Mathf.Abs(rad - 0.42f) * F));
                paper = paper.Lerp(new Vector3(110, 76, 42), line * 0.22f * Mathf.SmoothStep(0.02f, 0.1f, rad));
                // The wash where knowledge ends: sepia bleeding outward, its tide line darkest.
                float tide = Mathf.Exp(-Mathf.Pow((k - 0.31f) / 0.05f, 2));
                float bleed = Mathf.SmoothStep(0.06f, 0.33f, k) * (1 - Mathf.SmoothStep(0.33f, 0.4f, k));
                paper = paper.Lerp(new Vector3(120, 84, 48), bleed * 0.35f).Lerp(new Vector3(74, 46, 22), tide * 0.55f);
                paper += new Vector3(grain, grain, grain * 0.8f);
                int o = (y * F + x) * 4;
                px[o] = (byte)Math.Clamp(paper.X, 0, 255);
                px[o + 1] = (byte)Math.Clamp(paper.Y, 0, 255);
                px[o + 2] = (byte)Math.Clamp(paper.Z, 0, 255);
                px[o + 3] = (byte)Math.Clamp(cover * 255, 0, 255);
            }
        return ImageTexture.CreateFromImage(Image.CreateFromData(F, F, false, Image.Format.Rgba8, px));
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

    /// <summary>A box blur of a square field, across then down.</summary>
    static float[] Blur(float[] a, int n, int r)
    {
        var b = new float[a.Length];
        var c = new float[a.Length];
        for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float sum = 0; int k = 0;
                for (int d = -r; d <= r; d++) { int xx = x + d; if (xx < 0 || xx >= n) continue; sum += a[y * n + xx]; k++; }
                b[y * n + x] = sum / k;
            }
        for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++)
            {
                float sum = 0; int k = 0;
                for (int d = -r; d <= r; d++) { int yy = y + d; if (yy < 0 || yy >= n) continue; sum += b[yy * n + x]; k++; }
                c[y * n + x] = sum / k;
            }
        return c;
    }

    /* --------------------------------------------------------- the atlas -- */

    /// <summary>The drawing's size at zoom 1, and the part of the screen the map shows through
    /// (the list stands over the rest).</summary>
    const int F = 1080;
    static readonly Rect2 View = new(0, 96, 1440, 984);
    float minZoom = 0.6f;
    Vector2 panTo;
    bool gliding;
    Control? ring;
    double t;
    float extent = 1;
    Vector2 youAt;

    /// <summary>A mark the list can name: where, what, and its words.</summary>
    readonly record struct Entry(double X, double Z, MarkKind Kind, string Label);

    /// <summary>The triggers zoom (or , and .); Y finds you; focus on a line of the list glides the map to it.</summary>
    public override bool Key(Act a)
    {
        switch (a)
        {
            case Act.SubNext: zoom = Math.Min(4f, zoom * 1.25f); Place(F); return true;
            case Act.SubPrev: zoom = Math.Max(minZoom, zoom / 1.25f); Place(F); return true;
            case Act.Alt2: FindMe(); return true;
        }
        return false;
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
        panTo = new Vector2(Math.Clamp(-(float)x / extent, -0.5f, 0.5f), Math.Clamp(-(float)z / extent, -0.5f, 0.5f));
        gliding = true;
        if (ring != null && IsInstanceValid(ring))
        {
            ring.Visible = mark != null;
            if (mark is { } m) ring.Position = m - ring.Size / 2;
        }
    }

    public override void _Process(double delta)
    {
        base._Process(delta);
        t += delta;
        if (gliding)
        {
            panTo = Held(panTo);
            pan = pan.Lerp(panTo, 1 - Mathf.Exp(-9 * (float)delta));
            if (pan.DistanceTo(panTo) < 0.0005f) { pan = panTo; gliding = false; }
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
        extent = Extent(scene.Data.Meta);
        var page = Page(zone.Name, zone.Region, null, G.Key(Act.Map));
        // The map is the screen: under the header band and the list, over the dark.
        var frame = new Control { Position = Vector2.Zero, Size = new Vector2(1920, 1080), ClipContents = true, MouseFilter = MouseFilterEnum.Stop };
        AddChild(frame);
        MoveChild(frame, 1);
        // Past the paper's edge, the table it lies on: dark leather, a little lit where the map lies.
        frame.AddChild(new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { Dark.Lightened(0.12f), Dark, Dark.Darkened(0.45f) }, Offsets = new[] { 0f, 0.55f, 1f } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.4f, 0.55f), FillTo = new Vector2(1.1f, 1.1f), Width = 256, Height = 256,
            },
            Size = new Vector2(1920, 1080), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
        });
        world = new Control { Size = new Vector2(F, F), MouseFilter = MouseFilterEnum.Ignore };
        frame.AddChild(world);
        // The sheet's shadow on the table.
        for (int i = 6; i >= 1; i--)
            world.AddChild(new ColorRect { Color = new Color(0, 0, 0, 0.09f), Position = new Vector2(-i * 2.5f + 4, -i * 2.5f + 8), Size = new Vector2(F + i * 5, F + i * 5), MouseFilter = MouseFilterEnum.Ignore });
        // The expand mode first: a control is never smaller than its minimum, and the drawing's own is 1600.
        world.AddChild(new TextureRect { ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, Texture = Drawing(scene.Data), Size = new Vector2(F, F), MouseFilter = MouseFilterEnum.Ignore, TextureFilter = TextureFilterEnum.LinearWithMipmaps });
        // Clipped to the paper: a tree on its edge would hang its crown into the dark past it.
        world.AddChild(new MapInk(scene, extent, F) { Size = new Vector2(F, F), MouseFilter = MouseFilterEnum.Ignore, ClipContents = true });
        var zs = G.Journey.World.Zone(zone.Id);
        var seen = zs.TryGetValue("seen", out var f) && f.Str is { } s ? s : new string('0', Journey.FogN * Journey.FogN);
        world.AddChild(new TextureRect { ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, Texture = Fog(seen, Journey.FogN), Size = new Vector2(F, F), MouseFilter = MouseFilterEnum.Ignore });
        bool Seen(double x, double z)
        {
            int i = (int)Math.Floor((x / extent + 0.5) * Journey.FogN), j = (int)Math.Floor((z / extent + 0.5) * Journey.FogN);
            return i >= 0 && j >= 0 && i < Journey.FogN && j < Journey.FogN && seen[j * Journey.FogN + i] == '1';
        }
        Vector2 Px(double x, double z) => new((float)((x / extent + 0.5) * F), (float)((z / extent + 0.5) * F));
        var entries = zone.MapMarks().Where(m => m.Kind is MarkKind.Exit or MarkKind.Quest || Seen(m.X, m.Z)).Select(m => new Entry(m.X, m.Z, m.Kind, m.Label)).ToList();
        if (G.Journey.World.Corpse is { } corpse && corpse.Zone == zone.Id) entries.Add(new Entry(corpse.X, corpse.Z, MarkKind.Danger, $"{corpse.HeroName}'s belongings"));
        foreach (var m in entries.OrderByDescending(m => m.Kind == MarkKind.Place)) Mark(world, Px(m.X, m.Z), m.Label, m.Kind);
        // The ring that marks what the list has chosen.
        ring = new Panel { Size = new Vector2(46, 46), PivotOffset = new Vector2(23, 23), MouseFilter = MouseFilterEnum.Ignore, Visible = false };
        var rs = Style.Box(new Color(0, 0, 0, 0), new Color("#a8321e"), 3, 23, 0);
        ring.AddThemeStyleboxOverride("panel", rs);
        world.AddChild(ring);
        // You.
        if (G.Battle is { } b)
        {
            youAt = Px(b.Player.X, b.Player.Z);
            world.AddChild(new Polygon2D { Polygon = new[] { new Vector2(0, -11), new Vector2(8, 8), new Vector2(0, 4), new Vector2(-8, 8) }, Color = new Color("#b8321e"), Position = youAt, Rotation = (float)(Math.PI - b.Player.Facing) });
        }
        frame.GuiInput += e => Input(e, F);
        minZoom = Math.Min(View.Size.X, View.Size.Y) / F * 0.9f;
        // Opened on what is known, whatever the zone's own focus.
        Fit(seen);
        Place(F);

        // A compass in the corner, the way the old maps had one.
        var rose = Glyphs.Icon("compass", 72, Style.Gold with { A = 0.75f });
        rose.Position = new Vector2(36, 120);
        AddChild(rose);
        var north = Style.Label("N", Style.Display, 18, Style.GoldHi, false, HorizontalAlignment.Center);
        north.Position = new Vector2(36, 96);
        north.Size = new Vector2(72, 22);
        AddChild(north);

        // The list: where to go, what has been found, what to beware of; each line glides the map to it.
        var col = Pane(page, new Rect2(1420, 0, 420, 920), Style.Column(18), Style.Gap2);
        col.AddChild(new Section("Where to go", "nearest first"));
        var list = Style.V(2);
        var p0 = G.Battle?.Player;
        bool first = true;
        void Group(string title, IEnumerable<Entry> items)
        {
            var these = items.OrderBy(e => p0 == null ? 0 : Math.Sqrt((e.X - p0.X) * (e.X - p0.X) + (e.Z - p0.Z) * (e.Z - p0.Z))).ToList();
            if (these.Count == 0) return;
            if (!first) list.AddChild(Style.Gap(Style.Gap2));
            first = false;
            list.AddChild(Style.SubLabel(title));
            foreach (var e in these) list.AddChild(Line(e, Px(e.X, e.Z)));
        }
        Group("Your road", entries.Where(e => e.Kind is MarkKind.Quest or MarkKind.Turn or MarkKind.Exit));
        Group("People", entries.Where(e => e.Kind == MarkKind.Person));
        Group("Places", entries.Where(e => e.Kind == MarkKind.Place));
        Group("Danger and the strange", entries.Where(e => e.Kind is MarkKind.Danger or MarkKind.Mystery));
        if (entries.Count == 0) list.AddChild(Style.Label("Nothing found yet. The map fills in as you walk.", Style.TextItalic, Style.Body, Style.InkDim, true));
        var scroll = Style.Scroll(list);
        col.AddChild(scroll);
        col.AddChild(Style.Rule());
        // The legend, in the marks' own look (the corner map's too).
        var legend = new GridContainer { Columns = 2, MouseFilter = MouseFilterEnum.Ignore };
        legend.AddThemeConstantOverride("h_separation", 20);
        legend.AddThemeConstantOverride("v_separation", 6);
        foreach (var (kind, text) in new[] { (MarkKind.Quest, "Someone needs you"), (MarkKind.Exit, "The way out"), (MarkKind.Danger, "Hostile"), (MarkKind.Mystery, "Unexplained") })
            legend.AddChild(Style.H(6, Minimap.Mark(kind, 18), Style.Label(text, Style.Ui, Style.Caption, Style.Ink)));
        col.AddChild(legend);
        // The prompts in the list's foot: under the map they would sit on the drawing.
        col.AddChild(Controls.Instance.UsingPad
            ? Style.Hints((Act.Up, "Choose"), (Act.Alt2, "Find me"), (Act.Cancel, "Close"))
            : Style.Label("Wheel to zoom · drag to move · a line to find it", Style.TextItalic, Style.Caption, Style.InkDim, true));

        // Zoom and find-me, at the map's foot, where the hand is.
        var tools = Style.Panel(Style.Slab(8));
        tools.Position = new Vector2(40, 1000);
        AddChild(tools);
        var tr = Style.H(Style.Gap2);
        tools.AddChild(tr);
        Button Tool(string glyph, string? pad, string text, Action go)
        {
            var bt = Style.Button("", go, false, true);
            var r = Style.H(6, pad != null && Controls.Instance.UsingPad ? Style.PadButton(pad) : Glyphs.Icon(glyph, 16, Style.GoldHi), Style.Label(text, Style.UiBold, Style.Small, Style.GoldHi));
            r.MouseFilter = MouseFilterEnum.Ignore;
            r.Position = new Vector2(10, 5);
            bt.AddChild(r);
            bt.CustomMinimumSize = new Vector2(r.GetCombinedMinimumSize().X + 22, 34);
            return Nav.Skip(bt);
        }
        tr.AddChild(Tool("crosshair", "Y", "Find me", FindMe));
        tr.AddChild(Tool("expand", "RT", "Closer", () => Key(Act.SubNext)));
        tr.AddChild(Tool("expand", "LT", "Further", () => Key(Act.SubPrev)));
        tr.AddChild(Tool("map", null, "All I know", () => { Fit(seen); gliding = false; Place(F); }));
    }

    /// <summary>
    /// Frames what the survivor knows: every walked cell and where they stand,
    /// with a margin, as large as the view allows. The map opens on the known
    /// world, not on a square of blank paper with the zone at its edge.
    /// </summary>
    void Fit(string seen)
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
        minZoom = Math.Min(View.Size.X, View.Size.Y) / F * 0.9f;
        zoom = Math.Clamp(Math.Min(View.Size.X / (su * F), View.Size.Y / (sv * F)), minZoom, 4f);
        pan = new Vector2(0.5f - cu, 0.5f - cv);
    }

    /// <summary>A line of the list: its mark, its name, how far and which way from you.</summary>
    Control Line(Entry e, Vector2 at)
    {
        var b = Style.Button("", () => { Glide(e.X, e.Z, at); zoom = Math.Max(zoom, 1.8f); Place(F); }, false, true);
        var row = Style.H(8, Minimap.Mark(e.Kind, 18), Style.Label(e.Label, Style.UiBold, Style.Small, Style.Ink));
        if (G.Battle?.Player is { } p)
        {
            double dx = e.X - p.X, dz = e.Z - p.Z, d = Math.Sqrt(dx * dx + dz * dz);
            row.AddChild(Style.Label(d < 8 ? "here" : $"{Math.Round(d / 5) * 5:0} m {Way(dx, dz)}", Style.TextItalic, Style.Caption, Style.InkDim));
        }
        row.MouseFilter = MouseFilterEnum.Ignore;
        row.Position = new Vector2(10, 6);
        b.AddChild(row);
        b.CustomMinimumSize = new Vector2(0, 36);
        b.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        Nav.Mark(b, $"mark:{e.Label}", () => { Glide(e.X, e.Z, at); zoom = Math.Max(zoom, 1.8f); Place(F); }, focus: () => Glide(e.X, e.Z, at));
        b.MouseEntered += () => Glide(e.X, e.Z, at);
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

    static void Mark(Control parent, Vector2 at, string label, MarkKind kind)
    {
        bool place = kind == MarkKind.Place;
        var (_, color) = Minimap.Look(kind);
        var node = new Control { Position = at, MouseFilter = MouseFilterEnum.Ignore };
        if (!place)
        {
            var icon = Minimap.Mark(kind, 22);
            icon.Position = new Vector2(-11, -11);
            node.AddChild(icon);
        }
        var l = Style.Label(label, place ? Style.Display : Style.TextBold, place ? 16 : 15, place ? new Color("#3a2414") : color, false, HorizontalAlignment.Center, false);
        l.AddThemeColorOverride("font_outline_color", new Color("#e4d6b6"));
        l.AddThemeConstantOverride("outline_size", 5);
        l.Size = new Vector2(240, 22);
        l.Position = new Vector2(-120, place ? -11 : 12);
        node.AddChild(l);
        parent.AddChild(node);
    }

    void Place(int frame)
    {
        if (world == null) return;
        pan = Held(pan);
        world.Scale = new Vector2(zoom, zoom);
        // The point the pan names sits at the middle of the part of the screen the map shows through.
        var centre = View.Position + View.Size / 2;
        world.Position = centre - (new Vector2(0.5f, 0.5f) - pan) * frame * zoom;
        foreach (var c in world.GetChildren()) if (c is Control mk && mk is not TextureRect && mk is not ColorRect && mk is not MapInk && mk != ring) mk.Scale = new Vector2(1 / zoom, 1 / zoom);
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
        return new Vector2(Axis(p.X, View.Size.X), Axis(p.Y, View.Size.Y));
    }

    void Input(InputEvent e, int frame)
    {
        switch (e)
        {
            case InputEventMouseButton { ButtonIndex: MouseButton.WheelUp, Pressed: true }: zoom = Math.Min(4f, zoom * 1.18f); Place(frame); break;
            case InputEventMouseButton { ButtonIndex: MouseButton.WheelDown, Pressed: true }: zoom = Math.Max(minZoom, zoom / 1.18f); Place(frame); break;
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

    public override void _Draw()
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
            DrawColoredPolygon(pts, c.Soft ? new Color(110 / 255f, 86 / 255f, 58 / 255f, 0.35f) : new Color(84 / 255f, 60 / 255f, 40 / 255f, 0.8f));
            DrawPolyline(pts.Append(pts[0]).ToArray(), new Color(48 / 255f, 32 / 255f, 20 / 255f, 0.9f), 1);
        }
        foreach (var bl in meta.Map?.Buildings ?? new())
        {
            double bx = bl.GetProperty("x").GetDouble(), bz = bl.GetProperty("z").GetDouble(), br = bl.GetProperty("r").GetDouble(), rot = bl.GetProperty("rot").GetDouble();
            var at = Px(bx, bz);
            if (!On(at)) continue;
            float r = (float)br * s;
            Vector2[] Hex(Vector2 o, float rr) => Enumerable.Range(0, 6).Select(a => o + new Vector2(Mathf.Cos((float)rot + a * Mathf.Pi / 3 + Mathf.Pi / 6), Mathf.Sin((float)rot + a * Mathf.Pi / 3 + Mathf.Pi / 6)) * rr).ToArray();
            DrawColoredPolygon(Hex(at + new Vector2(r * 0.18f, r * 0.22f), r), new Color(60 / 255f, 40 / 255f, 22 / 255f, 0.35f));
            var outer = Hex(at, r);
            DrawColoredPolygon(outer, new Color(128 / 255f, 74 / 255f, 52 / 255f, 0.95f));
            DrawPolyline(outer.Append(outer[0]).ToArray(), new Color(46 / 255f, 28 / 255f, 16 / 255f, 0.95f), 1.4f);
            DrawColoredPolygon(Hex(at, r * 0.55f), new Color(160 / 255f, 100 / 255f, 72 / 255f, 0.9f));
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
                DrawColoredPolygon(tri, new Color((70 + jit * 20) / 255f, (88 + jit * 16) / 255f, 62 / 255f, 0.85f));
                DrawPolyline(tri.Append(tri[0]).ToArray(), new Color(38 / 255f, 44 / 255f, 30 / 255f, 0.9f), 1);
            }
            else if (kind is "broadleaf" or "autumn" or "sick")
            {
                float r = (float)(2.6 * sc) * s;
                var pts = Enumerable.Range(0, 8).Select(a => p + new Vector2(Mathf.Cos(a / 7f * Mathf.Tau), Mathf.Sin(a / 7f * Mathf.Tau)) * r * (0.82f + (float)Hash(x + a, z) * 0.3f)).ToArray();
                var col = kind == "autumn" ? new Color((176 + jit * 30) / 255f, (110 + jit * 30) / 255f, 60 / 255f, 0.8f) : kind == "sick" ? new Color(140 / 255f, 150 / 255f, 90 / 255f, 0.8f) : new Color((96 + jit * 20) / 255f, (122 + jit * 20) / 255f, 70 / 255f, 0.8f);
                DrawColoredPolygon(pts[..7], col);
                DrawPolyline(pts, new Color(46 / 255f, 44 / 255f, 28 / 255f, 0.85f), 1);
            }
            else if (kind == "dead")
            {
                float r = (float)(1.8 * sc) * s;
                var ink = new Color(60 / 255f, 44 / 255f, 30 / 255f, 0.85f);
                DrawLine(p + new Vector2(0, r), p + new Vector2(0, -r * 0.2f), ink);
                DrawLine(p + new Vector2(0, -r * 0.2f), p + new Vector2(-r * 0.6f, -r), ink);
                DrawLine(p + new Vector2(0, -r * 0.2f), p + new Vector2(r * 0.6f, -r * 0.9f), ink);
            }
            else
            {
                float r = (float)((kind == "cliff" ? 4 : 2.2) * sc) * s;
                var pts = Enumerable.Range(0, 7).Select(a => p + new Vector2(Mathf.Cos(a / 6f * Mathf.Tau + jit), Mathf.Sin(a / 6f * Mathf.Tau + jit)) * r * (0.7f + (float)Hash(x, z + a) * 0.4f)).ToArray();
                DrawColoredPolygon(pts[..6], new Color(150 / 255f, 144 / 255f, 130 / 255f, 0.8f));
                DrawPolyline(pts, new Color(60 / 255f, 56 / 255f, 48 / 255f, 0.9f), 1);
            }
        }
    }
}
