using System;
using System.Collections.Generic;
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

    const int MaxPts = 24;
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
    readonly ArrayMesh mesh = new();
    readonly Vector3[] verts = new Vector3[Capacity];
    readonly Color[] cols = new Color[Capacity];
    readonly Vector2[] uvs = new Vector2[Capacity];
    readonly Vector2[] uv2s = new Vector2[Capacity];
    readonly int[] idx = new int[Capacity * 3];
    readonly ShaderMaterial mat;
    readonly Random rng = new(41);
    float now;
    int nv, ni;

    public Ribbons()
    {
        Name = "Ribbons";
        Mesh = mesh;
        CastShadow = ShadowCastingSetting.Off;
        mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ribbon.gdshader") };
        MaterialOverride = mat;
        CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f));
    }

    float Rf() => (float)rng.NextDouble();

    /// <summary>A trail's head this frame: `key` names it (a projectile's id,
    /// or anything that flies), `width` across at the head, its points
    /// living `life` seconds behind it.</summary>
    public void Feed(long key, Vector3 head, float width, float life, Color color, float energy, Style style = Style.Glow)
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
        t.Born[t.Head] = now;
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

    /// <summary>A bolt's shape, made afresh: midpoint displacement down to
    /// short legs, the jag scaled to its length, thinner towards its ends.</summary>
    void Fork(ref Stroke s)
    {
        var pts = new List<Vector3> { s.A, s.B };
        float len = s.A.DistanceTo(s.B);
        float amp = len * s.Jag;
        var dir = (s.B - s.A) / Mathf.Max(1e-3f, len);
        var side = dir.Cross(Vector3.Up);
        if (side.LengthSquared() < 1e-4f) side = Vector3.Right;
        side = side.Normalized();
        var up = side.Cross(dir).Normalized();
        while (pts.Count < 17 && amp > 0.04f)
        {
            var next = new List<Vector3>(pts.Count * 2);
            for (int i = 0; i < pts.Count - 1; i++)
            {
                next.Add(pts[i]);
                next.Add((pts[i] + pts[i + 1]) / 2 + side * (Rf() - 0.5f) * amp + up * (Rf() - 0.5f) * amp * 0.5f);
            }
            next.Add(pts[^1]);
            pts = next;
            amp *= 0.5f;
        }
        s.Pts = pts.ToArray();
        var w = new float[s.Pts.Length];
        for (int i = 0; i < w.Length; i++) { float u = i / (float)(w.Length - 1); w[i] = 0.35f + 0.65f * Mathf.Min(1, Mathf.Min(u, 1 - u) * 6); }
        s.Widths = w;
        if (s.Branches <= 0 || s.Pts.Length < 6) { s.Forks = null; return; }
        // Forks off points along it, short and thin, made afresh with it.
        s.Forks = new Vector3[s.Branches][];
        for (int b = 0; b < s.Branches; b++)
        {
            int at = 2 + (int)(Rf() * (s.Pts.Length - 4));
            var from = s.Pts[at];
            var off = side * (Rf() - 0.5f) * 2;
            var to = from + (dir * 0.5f + off) * len * (0.18f + Rf() * 0.2f) + up * (Rf() - 0.5f) * 0.4f;
            var mid = (from + to) / 2 + new Vector3(Rf() - 0.5f, Rf() - 0.5f, Rf() - 0.5f) * from.DistanceTo(to) * 0.3f;
            s.Forks[b] = new[] { from, mid, to };
        }
    }

    static readonly float[] ForkWidths = { 1f, 0.6f, 0f };

    public void Step(float dt, Camera3D? cam)
    {
        now += dt;
        nv = ni = 0;
        var eye = cam?.GlobalPosition ?? new Vector3(0, 30, 10);
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
        // A trail no longer fed fades as a whole.
        float stale = Mathf.Clamp(1 - (now - t.Seen) / Mathf.Max(0.05f, t.Life), 0, 1);
        tw[0] = 0;
        DrawLine(tp, tw, t.Width, t.Color, t.Energy * stale, t.Style, eye, n);
    }

    void DrawLine(Vector3[] pts, float[] widths, float width, Color color, float energy, Style style, Vector3 eye, int count = -1)
    {
        int n = count < 0 ? pts.Length : count;
        if (n < 2 || nv + n * 2 > Capacity || ni + (n - 1) * 6 > idx.Length) return;
        int first = nv;
        for (int i = 0; i < n; i++)
        {
            var p = pts[i];
            var tan = i == 0 ? pts[1] - pts[0] : i == n - 1 ? pts[i] - pts[i - 1] : pts[i + 1] - pts[i - 1];
            var toEye = (eye - p).Normalized();
            var side = tan.Cross(toEye);
            if (side.LengthSquared() < 1e-8f) side = Vector3.Right;
            side = side.Normalized() * (width * widths[i] * 0.5f);
            float u = i / (float)(n - 1);
            var c = new Color(color.R, color.G, color.B, Mathf.Clamp(widths[i] * 1.5f, 0, 1));
            verts[nv] = p - side; cols[nv] = c; uvs[nv] = new Vector2(u, 0); uv2s[nv] = new Vector2(energy, (float)style); nv++;
            verts[nv] = p + side; cols[nv] = c; uvs[nv] = new Vector2(u, 1); uv2s[nv] = new Vector2(energy, (float)style); nv++;
        }
        for (int i = 0; i < n - 1; i++)
        {
            int a = first + i * 2;
            idx[ni++] = a; idx[ni++] = a + 1; idx[ni++] = a + 2;
            idx[ni++] = a + 1; idx[ni++] = a + 3; idx[ni++] = a + 2;
        }
    }

    void Flush()
    {
        mesh.ClearSurfaces();
        if (ni == 0) return;
        var arr = new Godot.Collections.Array();
        arr.Resize((int)Mesh.ArrayType.Max);
        arr[(int)Mesh.ArrayType.Vertex] = verts.AsSpan(0, nv).ToArray();
        arr[(int)Mesh.ArrayType.Color] = cols.AsSpan(0, nv).ToArray();
        arr[(int)Mesh.ArrayType.TexUV] = uvs.AsSpan(0, nv).ToArray();
        arr[(int)Mesh.ArrayType.TexUV2] = uv2s.AsSpan(0, nv).ToArray();
        arr[(int)Mesh.ArrayType.Index] = idx.AsSpan(0, ni).ToArray();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
    }
}
