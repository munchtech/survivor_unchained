using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Ribbons of light drawn as one mesh a frame (shaders/ribbon.gdshader):
/// the trail a thing leaves as it flies (fed its head each frame, by key,
/// thinning and fading behind it), and strokes laid down whole (a bolt of
/// lightning re-forking as it flickers, a beam, a thread). A trail reads as
/// speed and as the shape of a flight; the dotted sparks it replaces read as
/// litter. Each ribbon faces the camera across its length, tapers to nothing
/// at its tail and is soft across, so no end or edge is ever square.
/// </summary>
public partial class Ribbons : MeshInstance3D
{
    /// <summary>How a ribbon is drawn (the shader's styles).</summary>
    public enum Style { Glow = 0, Flame = 1, Bolt = 2, Wisp = 3, Steel = 4, Frost = 5 }

    const int MaxPts = 32;
    const int Capacity = 9000;

    sealed class Trail
    {
        public readonly Vector3[] At = new Vector3[MaxPts];
        public readonly float[] Born = new float[MaxPts];
        public int Head = -1, Count;
        public float Width, Life, Energy, Seen;
        public Color Color;
        public Style Style;
    }

    struct Stroke
    {
        public Vector3[] Pts;
        public float[] Widths;
        public float Width, Life, Age, Energy, Jag, Regen;
        public Color Color;
        public Style Style;
        public Vector3 A, B;
        public int Branches;
        public bool Bolt, Live;
        public Vector3[][]? Forks;
    }

    readonly Dictionary<long, Trail> trails = new();
    readonly List<long> gone = new();
    readonly List<Stroke> strokes = new();
    readonly Stack<Trail> spare = new();
    readonly Buffer glow = new(), shade = new();
    readonly Random rng = new(41);
    float now;

    public Ribbons()
    {
        Name = "Ribbons";
        Mesh = glow.Mesh;
        CastShadow = ShadowCastingSetting.Off;
        MaterialOverride = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ribbon.gdshader") };
        CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f));
        // The shadow under every ribbon, drawn first: a light over the pale
        // dead needs dark round it to be seen at all.
        AddChild(new MeshInstance3D
        {
            Name = "Shade", Mesh = shade.Mesh, CastShadow = ShadowCastingSetting.Off,
            MaterialOverride = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ribbon_shade.gdshader"), RenderPriority = -1 },
            CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f)),
        });
    }

    float Rf() => (float)rng.NextDouble();

    /// <summary>A trail's head this frame: `key` names it (a projectile's id,
    /// or anything that flies), `width` across at the head, its points
    /// living `life` seconds behind it.</summary>
    public void Feed(long key, Vector3 head, float width, float life, Color color, float energy, Style style = Style.Glow) =>
        Feed(key, head, width, life, color, energy, style, 0);

    /// <summary>As Feed, for a point passed `ago` seconds before now (a fast
    /// sweep fed several points a frame, so its curve stays round).</summary>
    public void Feed(long key, Vector3 head, float width, float life, Color color, float energy, Style style, float ago)
    {
        if (!trails.TryGetValue(key, out var t))
        {
            t = spare.Count > 0 ? spare.Pop() : new Trail();
            t.Head = -1; t.Count = 0;
            trails[key] = t;
        }
        t.Width = width; t.Life = life; t.Color = color; t.Energy = energy; t.Style = style; t.Seen = now;
        // A new point when the head has moved on; otherwise the head is moved.
        if (t.Count > 0 && t.At[t.Head].DistanceSquaredTo(head) < 0.0225f && t.Count > 1)
        {
            t.At[t.Head] = head;
            return;
        }
        t.Head = (t.Head + 1) % MaxPts;
        t.At[t.Head] = head;
        t.Born[t.Head] = now - ago;
        t.Count = Math.Min(MaxPts, t.Count + 1);
    }

    /// <summary>A line laid down whole (a beam, a thread, a slash's wake), fading over `life`.</summary>
    public void Line(Vector3[] pts, float width, float life, Color color, float energy, Style style = Style.Glow, float[]? widths = null)
    {
        if (pts.Length < 2) return;
        strokes.Add(new Stroke { Pts = pts, Widths = widths ?? Taper(pts.Length), Width = width, Life = Mathf.Max(0.02f, life), Energy = energy, Color = color, Style = style });
    }

    /// <summary>A line for this frame only (a shape that moves with what it
    /// belongs to, redrawn every frame).</summary>
    public void Now(Vector3[] pts, float width, Color color, float energy, Style style = Style.Glow, float[]? widths = null)
    {
        if (pts.Length < 2) return;
        strokes.Add(new Stroke { Pts = pts, Widths = widths ?? Taper(pts.Length), Width = width, Life = 1, Energy = energy, Color = color, Style = style, Live = true });
    }

    /// <summary>Lightning from `a` to `b`: a jagged line that re-forks as it
    /// flickers, with `branches` thinner forks off it, for `life` seconds.</summary>
    public void Bolt(Vector3 a, Vector3 b, float width, float life, Color color, float energy, int branches = 2, float jag = 0.28f)
    {
        var s = new Stroke { A = a, B = b, Width = width, Life = Mathf.Max(0.02f, life), Energy = energy, Color = color, Style = Style.Bolt, Jag = jag, Branches = branches, Bolt = true };
        Fork(ref s);
        strokes.Add(s);
    }

    static float[] Taper(int n)
    {
        var w = new float[n];
        for (int i = 0; i < n; i++) { float u = i / (float)(n - 1); w[i] = Mathf.Sin(u * Mathf.Pi) * 0.85f + 0.15f; }
        return w;
    }

    const int BoltPts = 17;

    /// <summary>A bolt's width along it: thinner towards its ends.</summary>
    static readonly float[] BoltWidths = MakeBoltWidths();

    static float[] MakeBoltWidths()
    {
        var w = new float[BoltPts];
        for (int i = 0; i < BoltPts; i++) { float u = i / (float)(BoltPts - 1); w[i] = 0.35f + 0.65f * Mathf.Min(1, Mathf.Min(u, 1 - u) * 6); }
        return w;
    }

    /// <summary>A bolt's shape, made afresh in the arrays it already has:
    /// midpoint displacement down to sixteen legs, the jag halving at each
    /// level, and its forks off points along it.</summary>
    void Fork(ref Stroke s)
    {
        if (s.Pts == null || s.Pts.Length != BoltPts) s.Pts = new Vector3[BoltPts];
        s.Widths = BoltWidths;
        var p = s.Pts;
        float len = s.A.DistanceTo(s.B);
        float amp = len * s.Jag;
        var dir = (s.B - s.A) / Mathf.Max(1e-3f, len);
        var side = dir.Cross(Vector3.Up);
        if (side.LengthSquared() < 1e-4f) side = Vector3.Right;
        side = side.Normalized();
        var up = side.Cross(dir).Normalized();
        p[0] = s.A;
        p[BoltPts - 1] = s.B;
        for (int step = BoltPts - 1; step > 1; step /= 2, amp *= 0.5f)
            for (int i = 0; i + step < BoltPts; i += step)
                p[i + step / 2] = (p[i] + p[i + step]) / 2 + side * (Rf() - 0.5f) * amp + up * (Rf() - 0.5f) * amp * 0.5f;
        if (s.Branches <= 0) { s.Forks = null; return; }
        if (s.Forks == null || s.Forks.Length != s.Branches)
        {
            s.Forks = new Vector3[s.Branches][];
            for (int b = 0; b < s.Branches; b++) s.Forks[b] = new Vector3[3];
        }
        for (int b = 0; b < s.Branches; b++)
        {
            var from = p[2 + (int)(Rf() * (BoltPts - 4))];
            var to = from + (dir * 0.5f + side * (Rf() - 0.5f) * 2) * len * (0.18f + Rf() * 0.2f) + up * (Rf() - 0.5f) * 0.4f;
            var fk = s.Forks[b];
            fk[0] = from;
            fk[1] = (from + to) / 2 + new Vector3(Rf() - 0.5f, Rf() - 0.5f, Rf() - 0.5f) * from.DistanceTo(to) * 0.3f;
            fk[2] = to;
        }
    }
    static readonly float[] ForkWidths = { 1f, 0.6f, 0f };

    /// <summary>The narrowest a ribbon is drawn, in pixels at its head: from the
    /// game's high camera a trail of true width is a hairline.</summary>
    public float MinPixels = 6;
    float perPxAtUnit;

    public void Step(float dt, Camera3D? cam)
    {
        now += dt;
        var eye = cam?.GlobalPosition ?? new Vector3(0, 30, 10);
        float fov = cam?.Fov ?? 34;
        float h = cam?.GetViewport()?.GetVisibleRect().Size.Y ?? 1080;
        perPxAtUnit = 2 * Mathf.Tan(Mathf.DegToRad(fov) / 2) / Mathf.Max(1, h);
        // Trails: drawn oldest to head, points dropped as they outlive the trail.
        gone.Clear();
        foreach (var (key, t) in trails)
        {
            if (now - t.Seen > t.Life + 0.05f) { gone.Add(key); continue; }
            DrawTrail(t, eye);
        }
        foreach (var k in gone) { spare.Push(trails[k]); trails.Remove(k); }
        for (int i = strokes.Count - 1; i >= 0; i--)
        {
            var s = strokes[i];
            if (s.Live)
            {
                DrawLine(s.Pts, s.Widths, s.Width, s.Color, s.Energy, s.Style, eye);
                strokes.RemoveAt(i);
                continue;
            }
            s.Age += dt;
            if (s.Age >= s.Life) { strokes.RemoveAt(i); continue; }
            if (s.Bolt)
            {
                s.Regen -= dt;
                if (s.Regen <= 0) { Fork(ref s); s.Regen = 0.045f; }
            }
            strokes[i] = s;
            float k = s.Age / s.Life;
            // A bolt is at full strength and then gone, with a flicker; the rest fade.
            float fade = s.Bolt ? (k < 0.6f ? 1 : 1 - (k - 0.6f) / 0.4f) * (0.75f + 0.25f * Rf()) : (1 - k) * (1 - k);
            DrawLine(s.Pts, s.Widths, s.Width, s.Color, s.Energy * fade, s.Style, eye);
            if (s.Forks != null)
                foreach (var fk in s.Forks) DrawLine(fk, ForkWidths, s.Width * 0.5f, s.Color, s.Energy * fade * 0.7f, s.Style, eye);
        }
        Flush();
    }

    readonly Vector3[] tp = new Vector3[MaxPts];
    readonly float[] tw = new float[MaxPts];

    void DrawTrail(Trail t, Vector3 eye)
    {
        int n = 0;
        // Oldest first.
        for (int j = t.Count - 1; j >= 0; j--)
        {
            int i = ((t.Head - j) % MaxPts + MaxPts) % MaxPts;
            float age = now - t.Born[i];
            if (age > t.Life && j > 0) continue;
            tp[n] = t.At[i];
            // Thin to nothing at the tail, and thinner as the point ages.
            tw[n] = Mathf.Clamp(1 - age / t.Life, 0, 1);
            n++;
        }
        if (n < 2) return;
        // A point just past the head at no width, so the head comes to a tip
        // (cut off at its full width, an arrow's streak and a sweep's lead
        // ended square).
        if (n < MaxPts)
        {
            var on = tp[n - 1] - tp[n - 2];
            float len = on.Length();
            if (len > 1e-4f)
            {
                tp[n] = tp[n - 1] + on / len * Mathf.Min(len * 2, t.Width * 0.8f);
                tw[n] = 0;
                n++;
            }
        }
        // A trail no longer fed fades as a whole.
        float stale = Mathf.Clamp(1 - (now - t.Seen) / Mathf.Max(0.05f, t.Life), 0, 1);
        tw[0] = 0;
        DrawLine(tp, tw, t.Width, t.Color, t.Energy * stale, t.Style, eye, n);
    }

    /// <summary>How dark the shadow under each style is: what is pale (steel,
    /// frost, a glow) needs it most to stand out from the pale dead it crosses;
    /// fire carries its own contrast.</summary>
    static float ShadeOf(Style s) => s switch
    {
        Style.Steel => 0.6f, Style.Frost => 0.5f, Style.Glow => 0.42f, Style.Wisp => 0.5f, Style.Bolt => 0.45f, _ => 0.3f,
    };

    void DrawLine(Vector3[] pts, float[] widths, float width, Color color, float energy, Style style, Vector3 eye, int count = -1)
    {
        int n = count < 0 ? pts.Length : count;
        if (n < 2 || !glow.Fits(n) || !shade.Fits(n)) return;
        // Never thinner than a few pixels where it is widest.
        width = Mathf.Max(width, MinPixels * perPxAtUnit * pts[n - 1].DistanceTo(eye));
        float dark = ShadeOf(style) * Mathf.Clamp(energy / 2, 0, 1);
        var under = new Color(color.R * 0.05f, color.G * 0.05f, color.B * 0.07f);
        int g0 = glow.Nv, s0 = shade.Nv;
        for (int i = 0; i < n; i++)
        {
            var p = pts[i];
            var tan = i == 0 ? pts[1] - pts[0] : i == n - 1 ? pts[i] - pts[i - 1] : pts[i + 1] - pts[i - 1];
            var toEye = (eye - p).Normalized();
            var side = tan.Cross(toEye);
            if (side.LengthSquared() < 1e-8f) side = Vector3.Right;
            side = side.Normalized() * (width * widths[i] * 0.5f);
            float u = i / (float)(n - 1), a = Mathf.Clamp(widths[i] * 1.5f, 0, 1);
            glow.Pair(p - side, p + side, new Color(color.R, color.G, color.B, a), u, energy, (float)style);
            // Its shadow: wider, dark, laid under it.
            shade.Pair(p - side * 1.9f, p + side * 1.9f, under with { A = a }, u, dark, (float)style);
        }
        glow.Strip(g0, n);
        shade.Strip(s0, n);
    }

    /// <summary>One mesh's worth of ribbon. Its surface is made once, at full
    /// size, and each frame only the part in use is written into it, laid out
    /// as the engine lays it out; the indices past that part are all zero, so
    /// their triangles have no area and draw nothing. Remaking the surface
    /// every frame cost new GPU buffers, a copy of every array and the
    /// renderer re-pairing the mesh with its material.</summary>
    sealed class Buffer
    {
        /// <summary>A vertex's colour, UV and UV2 as the engine stores them
        /// (Godot 4.5, checked at start): the colour as four bytes, cut down
        /// from floats as the engine cuts them, then two pairs of floats.</summary>
        [StructLayout(LayoutKind.Sequential, Pack = 1)]
        struct Attr
        {
            public uint Color;
            public Vector2 Uv, Uv2;
        }

        public readonly ArrayMesh Mesh = new();
        readonly Vector3[] verts = new Vector3[Capacity];
        readonly Attr[] attrs = new Attr[Capacity];
        readonly ushort[] idx = new ushort[Capacity * 3];
        public int Nv, Ni;
        // How many indices the GPU holds from the frame before (they are zeroed when this frame uses fewer).
        int sent;
        readonly bool inPlace;

        public Buffer()
        {
            var arr = new Godot.Collections.Array();
            arr.Resize((int)Godot.Mesh.ArrayType.Max);
            arr[(int)Godot.Mesh.ArrayType.Vertex] = verts;
            arr[(int)Godot.Mesh.ArrayType.Color] = new Color[Capacity];
            arr[(int)Godot.Mesh.ArrayType.TexUV] = new Vector2[Capacity];
            arr[(int)Godot.Mesh.ArrayType.TexUV2] = new Vector2[Capacity];
            arr[(int)Godot.Mesh.ArrayType.Index] = new int[Capacity * 3];
            Mesh.AddSurfaceFromArrays(Godot.Mesh.PrimitiveType.Triangles, arr, null, null, Godot.Mesh.ArrayFormat.FlagUseDynamicUpdate);
            // Written in place only if the engine's layout is the one Attr assumes.
            var f = (RenderingServer.ArrayFormat)(long)Mesh.SurfaceGetFormat(0);
            inPlace = RenderingServer.MeshSurfaceGetFormatVertexStride(f, Capacity) == 12
                && RenderingServer.MeshSurfaceGetFormatAttributeStride(f, Capacity) == Marshal.SizeOf<Attr>()
                && RenderingServer.MeshSurfaceGetFormatOffset(f, Capacity, (int)Godot.Mesh.ArrayType.Color) == 0
                && RenderingServer.MeshSurfaceGetFormatOffset(f, Capacity, (int)Godot.Mesh.ArrayType.TexUV) == 4
                && RenderingServer.MeshSurfaceGetFormatOffset(f, Capacity, (int)Godot.Mesh.ArrayType.TexUV2) == 12
                && RenderingServer.MeshSurfaceGetFormatIndexStride(f, Capacity) == 2;
            if (!inPlace)
            {
                GD.PushWarning("Ribbons: the engine's mesh layout is not the one expected; remaking the mesh each frame instead.");
                Mesh.ClearSurfaces();
            }
        }

        public bool Fits(int n) => Nv + n * 2 <= Capacity && Ni + (n - 1) * 6 <= idx.Length;

        /// <summary>A colour as the engine stores it: each channel times 255 in
        /// double, clamped and cut (not rounded), so the look is unchanged.</summary>
        static uint Pack(Color c) =>
            (uint)Math.Clamp(c.R * 255.0, 0, 255) | (uint)Math.Clamp(c.G * 255.0, 0, 255) << 8
            | (uint)Math.Clamp(c.B * 255.0, 0, 255) << 16 | (uint)Math.Clamp(c.A * 255.0, 0, 255) << 24;

        public void Pair(Vector3 a, Vector3 b, Color c, float u, float energy, float style)
        {
            uint packed = Pack(c);
            var e = new Vector2(energy, style);
            verts[Nv] = a; attrs[Nv] = new Attr { Color = packed, Uv = new Vector2(u, 0), Uv2 = e }; Nv++;
            verts[Nv] = b; attrs[Nv] = new Attr { Color = packed, Uv = new Vector2(u, 1), Uv2 = e }; Nv++;
        }

        public void Strip(int first, int n)
        {
            for (int i = 0; i < n - 1; i++)
            {
                int a = first + i * 2;
                idx[Ni++] = (ushort)a; idx[Ni++] = (ushort)(a + 1); idx[Ni++] = (ushort)(a + 2);
                idx[Ni++] = (ushort)(a + 1); idx[Ni++] = (ushort)(a + 3); idx[Ni++] = (ushort)(a + 2);
            }
        }

        public void Flush()
        {
            if (inPlace) Send();
            else Remake();
            Nv = Ni = 0;
        }

        void Send()
        {
            var rid = Mesh.GetRid();
            if (Nv > 0)
            {
                RenderingServer.MeshSurfaceUpdateVertexRegion(rid, 0, 0, MemoryMarshal.AsBytes(verts.AsSpan(0, Nv)));
                RenderingServer.MeshSurfaceUpdateAttributeRegion(rid, 0, 0, MemoryMarshal.AsBytes(attrs.AsSpan(0, Nv)));
            }
            // Last frame's triangles past this frame's end are zeroed in the same upload.
            int upto = Math.Max(Ni, sent);
            if (upto > 0)
            {
                if (sent > Ni) Array.Clear(idx, Ni, sent - Ni);
                RenderingServer.MeshSurfaceUpdateIndexRegion(rid, 0, 0, MemoryMarshal.AsBytes(idx.AsSpan(0, upto)));
            }
            sent = Ni;
        }

        /// <summary>The old way, kept for an engine whose layout differs.</summary>
        void Remake()
        {
            Mesh.ClearSurfaces();
            if (Ni == 0) return;
            var cols = new Color[Nv];
            var uvs = new Vector2[Nv];
            var uv2s = new Vector2[Nv];
            for (int i = 0; i < Nv; i++)
            {
                uint c = attrs[i].Color;
                // Half a step up, so the engine cuts it back to the same byte.
                cols[i] = new Color(((c & 255) + 0.5f) / 255f, ((c >> 8 & 255) + 0.5f) / 255f, ((c >> 16 & 255) + 0.5f) / 255f, ((c >> 24) + 0.5f) / 255f);
                uvs[i] = attrs[i].Uv;
                uv2s[i] = attrs[i].Uv2;
            }
            var ix = new int[Ni];
            for (int i = 0; i < Ni; i++) ix[i] = idx[i];
            var arr = new Godot.Collections.Array();
            arr.Resize((int)Godot.Mesh.ArrayType.Max);
            arr[(int)Godot.Mesh.ArrayType.Vertex] = verts.AsSpan(0, Nv).ToArray();
            arr[(int)Godot.Mesh.ArrayType.Color] = cols;
            arr[(int)Godot.Mesh.ArrayType.TexUV] = uvs;
            arr[(int)Godot.Mesh.ArrayType.TexUV2] = uv2s;
            arr[(int)Godot.Mesh.ArrayType.Index] = ix;
            Mesh.AddSurfaceFromArrays(Godot.Mesh.PrimitiveType.Triangles, arr);
        }
    }

    void Flush()
    {
        // Nothing to draw: hidden, rather than drawing a mesh of empty triangles.
        Visible = glow.Ni > 0;
        glow.Flush();
        shade.Flush();
    }
}