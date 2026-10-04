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
        public float Span, Sweep, Drain, Age, Depth, Seed;
        public Color Hue;
    }

    const int Max = 48;
    const int Stride = 12 + 4 + 4;
    readonly List<Swing> live = new();
    readonly float[] buffer = new float[Max * Stride];
    readonly Random rng = new(5);

    public Blades()
    {
        Multimesh = new MultiMesh
        {
            TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseColors = true, UseCustomData = true,
            InstanceCount = Max, VisibleInstanceCount = 0, Mesh = Grid(64, 6),
        };
        MaterialOverride = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/blade.gdshader") };
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
        var basis = new Basis(Vector3.Up, facing).Scaled(new Vector3(mirror ? -reach : reach, reach, reach));
        live.Add(new Swing
        {
            At = new Transform3D(basis, centre), Span = span, Sweep = Mathf.Max(0.02f, sweep), Drain = Mathf.Max(0.02f, drain),
            Age = -delay, Depth = Mathf.Clamp(depth, 0.05f, 0.62f), Hue = hue, Seed = 1 + rng.Next(900),
        });
    }

    public void Step(float dt)
    {
        int n = 0;
        for (int i = live.Count - 1; i >= 0; i--)
        {
            var s = live[i];
            s.Age += dt;
            if (s.Age >= s.Sweep + s.Drain) { live.RemoveAt(i); continue; }
            live[i] = s;
            if (s.Age < 0) continue;
            // Fast out of the wind-up, slowing through the follow.
            float k = Mathf.Min(1, s.Age / s.Sweep);
            float head = 1 - Mathf.Pow(1 - k, 2.2f);
            const float Tail = 0.75f;
            float back = Mathf.Max(0, head - Tail);
            if (s.Age > s.Sweep)
            {
                float d = (s.Age - s.Sweep) / s.Drain;
                back = Mathf.Lerp(1 - Tail, 1, 1 - (1 - d) * (1 - d));
            }
            float life = s.Age / (s.Sweep + s.Drain);
            float left = 1 - Mathf.SmoothStep(0.45f, 1, life);
            int o = n++ * Stride;
            var b = s.At.Basis;
            buffer[o] = b.X.X; buffer[o + 1] = b.Y.X; buffer[o + 2] = b.Z.X; buffer[o + 3] = s.At.Origin.X;
            buffer[o + 4] = b.X.Y; buffer[o + 5] = b.Y.Y; buffer[o + 6] = b.Z.Y; buffer[o + 7] = s.At.Origin.Y;
            buffer[o + 8] = b.X.Z; buffer[o + 9] = b.Y.Z; buffer[o + 10] = b.Z.Z; buffer[o + 11] = s.At.Origin.Z;
            buffer[o + 12] = s.Hue.R; buffer[o + 13] = s.Hue.G; buffer[o + 14] = s.Hue.B; buffer[o + 15] = s.Depth;
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
