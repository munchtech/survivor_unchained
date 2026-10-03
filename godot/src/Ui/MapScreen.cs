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
/// pans, M or Escape puts it away; with a pad, the stick or the D-pad pans
/// and the triggers zoom.
/// </summary>
public partial class MapScreen : Overlay
{
    public override string Kind => "map";
    public override Act? Toggle => Act.Map;
    const int W = 900;
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
        for (int j = 0; j < G; j++)
            for (int i = 0; i < G; i++)
            {
                float x = (i / (G - 1f) - 0.5f) * extent, zz = (j / (G - 1f) - 0.5f) * extent;
                int k = j * G + i;
                h[k] = z.HeightAt(x, zz);
                int px = Math.Clamp((int)((x / z.Size + 0.5f) * sr), 0, sr - 1), py = Math.Clamp((int)((zz / z.Size + 0.5f) * sr), 0, sr - 1);
                var p = z.Splat.GetPixel(px, py);
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
        var img = Image.CreateEmpty(W, W, false, Image.Format.Rgb8);
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
                float band = y / contour, next = S(h, fx + 0.6f, fy + 0.6f) / contour;
                if (Mathf.Floor(band) != Mathf.Floor(next) && w < 0.3f)
                {
                    bool major = (int)Mathf.Floor(Math.Max(band, next)) % 5 == 0;
                    c = c.Lerp(new Vector3(92, 70, 46), major ? 0.42f : 0.2f);
                }
                // The grain of the paper, and its age at the edges.
                float n = (float)((Hash(px, py) - 0.5) * 14 + (Hash(px / 7, py / 7) - 0.5) * 10);
                float r = new Vector2(px - W / 2f, py - W / 2f).Length() / W;
                float age = Mathf.SmoothStep(0.3f, 0.72f, r) * 0.5f;
                c = c.Lerp(new Vector3(70, 40, 14), age) + new Vector3(n, n, n * 0.8f);
                img.SetPixel(px, py, new Color(c.X / 255, c.Y / 255, c.Z / 255));
            }
        var tex = ImageTexture.CreateFromImage(img);
        drawings[z.Id] = tex;
        return tex;
    }

    /// <summary>Paper over what has not been walked, with holes where you went.</summary>
    static ImageTexture Fog(string seen, int n)
    {
        const int F = 300;
        var img = Image.CreateEmpty(F, F, false, Image.Format.Rgba8);
        float c = F / (float)n;
        var alpha = new float[F * F];
        Array.Fill(alpha, 1f);
        for (int j = 0; j < n; j++)
            for (int i = 0; i < n; i++)
            {
                if (j * n + i >= seen.Length || seen[j * n + i] != '1') continue;
                float cx = (i + 0.5f) * c, cy = (j + 0.5f) * c, rr = c * 1.35f;
                for (int y = (int)(cy - rr); y <= (int)(cy + rr); y++)
                    for (int x = (int)(cx - rr); x <= (int)(cx + rr); x++)
                    {
                        if (x < 0 || y < 0 || x >= F || y >= F) continue;
                        float d = new Vector2(x - cx, y - cy).Length() / rr;
                        float hole = 1 - Mathf.SmoothStep(0.3f, 1f, d);
                        alpha[y * F + x] = Math.Min(alpha[y * F + x], 1 - hole);
                    }
            }
        for (int y = 0; y < F; y++)
            for (int x = 0; x < F; x++)
            {
                float g = (float)(Hash(x, y) * 0.05);
                img.SetPixel(x, y, new Color(0.85f - g, 0.796f - g, 0.66f - g, alpha[y * F + x]));
            }
        return ImageTexture.CreateFromImage(img);
    }

    /// <summary>Pan with the D-pad or the stick, zoom with the triggers (or , and .).</summary>
    public override bool Key(Act a)
    {
        const int F = 740;
        switch (a)
        {
            case Act.Up or Act.Down or Act.Left or Act.Right:
                var d = a switch { Act.Up => new Vector2(0, 1), Act.Down => new Vector2(0, -1), Act.Left => new Vector2(1, 0), _ => new Vector2(-1, 0) } * (0.06f / zoom);
                pan = new Vector2(Math.Clamp(pan.X + d.X, -0.5f, 0.5f), Math.Clamp(pan.Y + d.Y, -0.5f, 0.5f));
                Place(F);
                return true;
            case Act.SubNext: zoom = Math.Min(3.5f, zoom * 1.25f); Place(F); return true;
            case Act.SubPrev: zoom = Math.Max(1, zoom / 1.25f); Place(F); return true;
        }
        return false;
    }

    protected override void Build()
    {
        var scene = G.Scene!;
        var zone = G.Zone!;
        var meta = scene.Data.Meta;
        float extent = Extent(meta);
        AddChild(Style.Scrim(G.CloseOverlay, 0.7f));
        var sheet = Style.Centered(Style.V(6), new Vector2(760, 880));
        AddChild(sheet);
        BookTabs(new Vector2((1920 - 760) / 2, (1080 - 880) / 2 - 40));
        sheet.AddChild(Style.Label(zone.Name, Style.Display, 30, Style.GoldHi, false, HorizontalAlignment.Center));
        if (zone.Region != null) sheet.AddChild(Style.Label(zone.Region, Style.TextItalic, Style.Small, Style.InkDim, false, HorizontalAlignment.Center));
        const int Frame = 740;
        // Exactly its size: a frame stretched wider shows the ink past the fog's edge.
        var frame = new Panel { CustomMinimumSize = new Vector2(Frame, Frame), SizeFlagsHorizontal = SizeFlags.ShrinkCenter, ClipContents = true, MouseFilter = MouseFilterEnum.Stop };
        frame.AddThemeStyleboxOverride("panel", Style.Box(new Color("#d9cba8"), new Color("#5a3e24"), 2, 3, 0));
        sheet.AddChild(frame);
        world = new Control { Size = new Vector2(Frame, Frame), MouseFilter = MouseFilterEnum.Ignore };
        frame.AddChild(world);
        world.AddChild(new TextureRect { Texture = Drawing(scene.Data), Size = new Vector2(Frame, Frame), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore });
        var ink = new MapInk(scene, extent, Frame) { Size = new Vector2(Frame, Frame), MouseFilter = MouseFilterEnum.Ignore };
        world.AddChild(ink);
        var zs = G.Journey.World.Zone(zone.Id);
        var seen = zs.TryGetValue("seen", out var f) && f.Str is { } s ? s : new string('0', Journey.FogN * Journey.FogN);
        world.AddChild(new TextureRect { Texture = Fog(seen, Journey.FogN), Size = new Vector2(Frame, Frame), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore });
        // What is known: marks, named once seen.
        bool Seen(double x, double z)
        {
            int i = (int)Math.Floor((x / extent + 0.5) * Journey.FogN), j = (int)Math.Floor((z / extent + 0.5) * Journey.FogN);
            return i >= 0 && j >= 0 && i < Journey.FogN && j < Journey.FogN && seen[j * Journey.FogN + i] == '1';
        }
        Vector2 Px(double x, double z) => new((float)((x / extent + 0.5) * Frame), (float)((z / extent + 0.5) * Frame));
        var marks = world;
        foreach (var m in zone.MapMarks().Where(m => m.Kind is MarkKind.Exit or MarkKind.Quest || Seen(m.X, m.Z)).OrderByDescending(m => m.Kind == MarkKind.Place))
            Mark(marks, Px(m.X, m.Z), m.Label, m.Kind);
        if (G.Journey.World.Corpse is { } corpse && corpse.Zone == zone.Id) Mark(marks, Px(corpse.X, corpse.Z), $"{corpse.HeroName}'s belongings", MarkKind.Danger);
        // You.
        if (G.Battle is { } b)
        {
            var you = new Polygon2D { Polygon = new[] { new Vector2(0, -9), new Vector2(7, 7), new Vector2(0, 3), new Vector2(-7, 7) }, Color = new Color("#b8321e"), Position = Px(b.Player.X, b.Player.Z), Rotation = (float)(Math.PI - b.Player.Facing) };
            marks.AddChild(you);
        }
        // The legend, in the marks' own look (the corner map's too).
        var foot = Style.H(16);
        foreach (var (kind, text) in new[] { (MarkKind.Quest, "Someone needs you"), (MarkKind.Danger, "Hostile"), (MarkKind.Mystery, "Unexplained"), (MarkKind.Exit, "The way out") })
            foot.AddChild(Style.H(5, Minimap.Mark(kind, 18), Style.Label(text, Style.Ui, Style.Caption, Style.Ink)));
        foot.Alignment = BoxContainer.AlignmentMode.Center;
        sheet.AddChild(foot);
        sheet.AddChild(Controls.Instance.UsingPad
            ? Footer((Act.Up, "Move"), (Act.SubNext, "Closer"), (Act.SubPrev, "Further"), (Act.Cancel, "Close"))
            : MouseFooter($"{G.Key(Act.Map)} to close", "wheel to zoom", "drag to move"));
        frame.GuiInput += e => Input(e, Frame);
        Place(Frame);
    }

    static void Mark(Control parent, Vector2 at, string label, MarkKind kind)
    {
        bool place = kind == MarkKind.Place;
        var (_, color) = Minimap.Look(kind);
        var node = new Control { Position = at, MouseFilter = MouseFilterEnum.Ignore };
        if (!place)
        {
            var icon = Minimap.Mark(kind, 20);
            icon.Position = new Vector2(-10, -10);
            node.AddChild(icon);
        }
        var l = Style.Label(label, place ? Style.Display : Style.TextBold, place ? 15 : 14, place ? new Color("#3a2414") : color, false, HorizontalAlignment.Center, false);
        l.AddThemeColorOverride("font_outline_color", new Color("#e4d6b6"));
        l.AddThemeConstantOverride("outline_size", 4);
        l.Size = new Vector2(220, 20);
        l.Position = new Vector2(-110, place ? -10 : 11);
        node.AddChild(l);
        parent.AddChild(node);
    }

    void Place(int frame)
    {
        if (world == null) return;
        world.Scale = new Vector2(zoom, zoom);
        // The map's middle at the frame's middle, moved by the pan.
        world.Position = new Vector2(frame / 2f, frame / 2f) - new Vector2(frame / 2f, frame / 2f) * zoom + pan * frame * zoom;
        foreach (var c in world.GetChildren()) if (c is Control mk && mk is not TextureRect && mk is not MapInk) mk.Scale = new Vector2(1 / zoom, 1 / zoom);
    }

    void Input(InputEvent e, int frame)
    {
        switch (e)
        {
            case InputEventMouseButton { ButtonIndex: MouseButton.WheelUp, Pressed: true }: zoom = Math.Min(3.5f, zoom * 1.18f); Place(frame); break;
            case InputEventMouseButton { ButtonIndex: MouseButton.WheelDown, Pressed: true }: zoom = Math.Max(1, zoom / 1.18f); Place(frame); break;
            case InputEventMouseButton { ButtonIndex: MouseButton.Left } mb:
                dragging = mb.Pressed;
                dragFrom = mb.Position;
                panFrom = pan;
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
        foreach (var c in meta.Collision().All())
        {
            if (c.Kind != ColliderKind.Box || c.PlayerOnly || c.Hw * c.Hd < 0.6) continue;
            var at = Px(c.X, c.Z);
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
