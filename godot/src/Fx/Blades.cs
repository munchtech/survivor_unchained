using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Blades' swings drawn as the crescents their edges cut (shaders/blade.gdshader):
/// one instance a swing in a single MultiMesh, so a whirl of them is one draw.
/// The blade crosses its arc fast and eases through the follow; its smear
/// drains after it and breaks up as it goes. Kept on the fight's clock, so
/// hit-stop holds a swing mid-cut.
/// </summary>
public partial class Blades : MultiMeshInstance3D
{
    struct Swing
    {
        public Transform3D At;
        public float Span, Sweep, Drain, Age, Depth, Seed, CutTotal, CutLeft;
        public Color Hue;
    }

    const int Max = 48;
    const int Stride = 12 + 4 + 4;
    readonly List<Swing> live = new();
    readonly float[] buffer = new float[Max * Stride];
    readonly Random rng = new(5);
    readonly bool oath;

    /// <summary>`lit`: the crescent only adds light (no dark bed under it), a hot edge and a smear in its hue
    /// (her Oathblade's gold sweep: it lights the ground, never darkens it).</summary>
    /// <summary>`oath`: her Oathblade's sweep (shaders/oath_sweep.gdshader): revealed along the arc over its
    /// `sweep`, eaten from its tail over its `drain`; `reach` is its outer radius and `depth` its inner
    /// radius as a share of it (Add's other arguments as ever).</summary>
    public Blades(bool lit = false, bool oath = false)
    {
        this.oath = oath;
        Multimesh = new MultiMesh
        {
            TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseColors = true, UseCustomData = true,
            InstanceCount = Max, VisibleInstanceCount = 0, Mesh = oath ? Grid(96, 8) : Grid(64, 6),
        };
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>(oath ? "res://shaders/oath_sweep.gdshader" : "res://shaders/blade.gdshader") };
        if (oath) mat.SetShaderParameter("streaks", GD.Load<Texture2D>("res://art/fx/oath_streaks.png"));
        else mat.SetShaderParameter("lit", lit);
        MaterialOverride = mat;
        CastShadow = ShadowCastingSetting.Off;
        CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f));
    }

    /// <summary>A swing round `centre` (the hand's height), its middle facing
    /// `facing` (radians about up, 0 facing +Z), out to `reach`, through
    /// `span` radians, the other way round when `mirror`. The blade crosses
    /// it in `sweep` seconds and its smear drains over `drain` more; `hue` is
    /// its colour (linear, bright), `depth` how deep its smear reaches in
    /// from the edge as a share of the reach.</summary>
    public void Add(Vector3 centre, float facing, float reach, float span, bool mirror, float sweep, float drain, Color hue, float depth, float delay = 0)
    {
        if (live.Count >= Max) live.RemoveAt(0);
        // The mirror is the swing's own (its local X), applied before the turn: Basis.Scaled scales in the
        // world's axes, so a mirrored swing was flipped across the world's X and drawn on the far side of
        // her from its hits whenever it faced along X (vfx9 aa: "a gold crescent 2 m to her left").
        var basis = new Basis(Vector3.Up, facing) * Basis.FromScale(new Vector3(mirror ? -reach : reach, reach, reach));
        var sw = new Swing
        {
            At = new Transform3D(basis, centre), Span = span, Sweep = Mathf.Max(0.02f, sweep), Drain = Mathf.Max(0.02f, drain),
            Age = -delay, Depth = Mathf.Clamp(depth, 0.05f, 0.62f), Hue = hue, Seed = 1 + rng.Next(900),
        };
        if (cutWindow > 0) Fade(ref sw, cutWithin);
        live.Add(sw);
    }

    /// <summary>Every swing in flight gone (the Long Cut's press: the Flare has the frame).</summary>
    public void Clear() => live.Clear();

    float cutWindow, cutWithin;

    /// <summary>Every live swing fades to nothing within `within` seconds from now (a mass kill: the nova must not
    /// out-shout the bodies). Swings added in the next two frames fade the same way. Sweep and drain shapes are
    /// untouched; only a fade multiplier on the colour and its life fade.</summary>
    public int Cut(float within)
    {
        within = Mathf.Max(0.01f, within);
        cutWindow = 2 / 60f; cutWithin = within;
        for (int i = 0; i < live.Count; i++) { var s = live[i]; Fade(ref s, within); live[i] = s; }
        return live.Count;
    }

    static void Fade(ref Swing s, float within)
    {
        if (s.CutTotal > 0 && s.CutLeft <= within) return;
        s.CutTotal = within; s.CutLeft = within;
    }

    public void Step(float dt)
    {
        int n = 0;
        if (cutWindow > 0) cutWindow -= dt;
        for (int i = live.Count - 1; i >= 0; i--)
        {
            var s = live[i];
            s.Age += dt;
            float fade = 1;
            if (s.CutTotal > 0) { s.CutLeft -= dt; fade = Mathf.Max(0, s.CutLeft / s.CutTotal); }
            if (s.Age >= s.Sweep + s.Drain || (s.CutTotal > 0 && s.CutLeft <= 0)) { live.RemoveAt(i); continue; }
            live[i] = s;
            if (s.Age < 0) continue;
            float k = Mathf.Min(1, s.Age / s.Sweep);
            if (oath)
            {
                // Revealed with the swing (eased out), then eaten from the tail.
                float hd = 1 - (1 - k) * (1 - k);
                float er = Mathf.Clamp((s.Age - s.Sweep) / s.Drain, 0, 1);
                int q = n++ * Stride;
                var ob = s.At.Basis;
                buffer[q] = ob.X.X; buffer[q + 1] = ob.Y.X; buffer[q + 2] = ob.Z.X; buffer[q + 3] = s.At.Origin.X;
                buffer[q + 4] = ob.X.Y; buffer[q + 5] = ob.Y.Y; buffer[q + 6] = ob.Z.Y; buffer[q + 7] = s.At.Origin.Y;
                buffer[q + 8] = ob.X.Z; buffer[q + 9] = ob.Y.Z; buffer[q + 10] = ob.Z.Z; buffer[q + 11] = s.At.Origin.Z;
                buffer[q + 12] = s.Hue.R * fade; buffer[q + 13] = s.Hue.G * fade; buffer[q + 14] = s.Hue.B * fade; buffer[q + 15] = s.Depth;
                buffer[q + 16] = hd; buffer[q + 17] = er; buffer[q + 18] = s.Span; buffer[q + 19] = s.Seed;
                continue;
            }
            // Fast out of the wind-up, slowing through the follow.
            float head = 1 - Mathf.Pow(1 - k, 2.2f);
            const float Tail = 0.75f;
            float back = Mathf.Max(0, head - Tail);
            if (s.Age > s.Sweep)
            {
                float d = (s.Age - s.Sweep) / s.Drain;
                back = Mathf.Lerp(1 - Tail, 1, 1 - (1 - d) * (1 - d));
            }
            float life = s.Age / (s.Sweep + s.Drain);
            float left = (1 - Mathf.SmoothStep(0.45f, 1, life)) * fade;
            int o = n++ * Stride;
            var b = s.At.Basis;
            buffer[o] = b.X.X; buffer[o + 1] = b.Y.X; buffer[o + 2] = b.Z.X; buffer[o + 3] = s.At.Origin.X;
            buffer[o + 4] = b.X.Y; buffer[o + 5] = b.Y.Y; buffer[o + 6] = b.Z.Y; buffer[o + 7] = s.At.Origin.Y;
            buffer[o + 8] = b.X.Z; buffer[o + 9] = b.Y.Z; buffer[o + 10] = b.Z.Z; buffer[o + 11] = s.At.Origin.Z;
            buffer[o + 12] = s.Hue.R * fade; buffer[o + 13] = s.Hue.G * fade; buffer[o + 14] = s.Hue.B * fade; buffer[o + 15] = s.Depth;
            buffer[o + 16] = head; buffer[o + 17] = back; buffer[o + 18] = s.Span; buffer[o + 19] = s.Seed + Mathf.Clamp(left, 0.001f, 0.999f);
        }
        if (n > 0) Multimesh.Buffer = buffer;
        Multimesh.VisibleInstanceCount = n;
    }

    /// <summary>A flat grid of `along` by `across` cells in XZ, its UV running 0 to 1 both ways.</summary>
    static ArrayMesh Grid(int along, int across)
    {
        var verts = new Vector3[(along + 1) * (across + 1)];
        var uvs = new Vector2[verts.Length];
        var idx = new int[along * across * 6];
        for (int i = 0; i <= along; i++)
            for (int j = 0; j <= across; j++)
            {
                int v = i * (across + 1) + j;
                verts[v] = new Vector3(i / (float)along, 0, j / (float)across);
                uvs[v] = new Vector2(i / (float)along, j / (float)across);
            }
        int k = 0;
        for (int i = 0; i < along; i++)
            for (int j = 0; j < across; j++)
            {
                int a = i * (across + 1) + j, b = a + across + 1;
                idx[k++] = a; idx[k++] = b; idx[k++] = a + 1;
                idx[k++] = a + 1; idx[k++] = b; idx[k++] = b + 1;
            }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts;
        arrays[(int)Mesh.ArrayType.TexUV] = uvs;
        arrays[(int)Mesh.ArrayType.Index] = idx;
        var m = new ArrayMesh();
        m.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        return m;
    }
}
