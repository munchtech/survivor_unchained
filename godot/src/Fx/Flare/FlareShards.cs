using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Burns Twice's ice: shards of real, lit geometry (shaders/flare_shard.gdshader) thrown from each impact and
/// from every frozen body that shatters. They tumble, land, skid, lie a moment and melt away.
/// </summary>
public partial class FlareShards : MultiMeshInstance3D
{
    struct S
    {
        public Vector3 At, V, Spin, Axis;
        public float Angle, Life, Age, Size, Heat;
        public Color Tint;
        public Basis Shape;
        public bool Down;
    }

    readonly List<S> live = new();
    float[]? buf;
    int shown;
    readonly int cap;
    readonly Random rng = new(31);

    public FlareShards(int capacity)
    {
        cap = capacity;
        Name = "FlareShards";
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/flare_shard.gdshader") };
        Multimesh = new MultiMesh
        {
            TransformFormat = MultiMesh.TransformFormatEnum.Transform3D,
            UseColors = true,
            UseCustomData = true,
            Mesh = ShardMesh(mat),
            InstanceCount = cap,
            VisibleInstanceCount = 0,
        };
        CastShadow = ShadowCastingSetting.Off;
        CustomAabb = new Aabb(new Vector3(-500, -50, -500), new Vector3(1000, 200, 1000));
    }

    /// <summary>A shard: a six-sided splinter, pointed both ends, one end longer (ice breaks along its grain).</summary>
    static Mesh ShardMesh(Material mat)
    {
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        const int sides = 5;
        var ring = new Vector3[sides];
        var r = new Random(5);
        for (int i = 0; i < sides; i++)
        {
            float a = i * Mathf.Tau / sides + (float)r.NextDouble() * 0.5f;
            float w = 0.22f + (float)r.NextDouble() * 0.16f;
            ring[i] = new Vector3(Mathf.Cos(a) * w, (float)r.NextDouble() * 0.15f - 0.05f, Mathf.Sin(a) * w * 0.6f);
        }
        var top = new Vector3(0.04f, 1f, 0.02f);
        var bottom = new Vector3(-0.03f, -0.45f, 0);
        void Tri(Vector3 a, Vector3 b, Vector3 c)
        {
            var n = (b - a).Cross(c - a).Normalized();
            // Godot takes clockwise as the front: wound the other way, every shard was drawn inside out (its far
            // faces, lit from behind, their rims full on: the white "paper flakes" of t1 to t8).
            st.SetNormal(n); st.AddVertex(a);
            st.SetNormal(n); st.AddVertex(c);
            st.SetNormal(n); st.AddVertex(b);
        }
        for (int i = 0; i < sides; i++)
        {
            var a = ring[i];
            var b = ring[(i + 1) % sides];
            Tri(top, b, a);
            Tri(bottom, a, b);
        }
        st.SetMaterial(mat);
        return st.Commit();
    }

    float R() => (float)rng.NextDouble();

    /// <summary>A burst of shards from a point: n of them, up and out at about this speed, this big (m),
    /// tinted by a body's paint (alpha: how much), hot from the ember that broke them.</summary>
    public void Burst(Vector3 at, int n, float speed, float size, Color tint, float heat, Vector3? away = null)
    {
        for (int i = 0; i < n && live.Count < cap; i++)
        {
            float a = R() * Mathf.Tau;
            var dir = new Vector3(Mathf.Cos(a), 0.55f + R() * 1.1f, Mathf.Sin(a));
            if (away is Vector3 aw) dir += new Vector3(aw.X, 0, aw.Z) * 0.8f;
            var axis = new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f);
            if (axis.LengthSquared() < 1e-3f) axis = Vector3.Up;
            var shape = new Basis(new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f).Normalized() is var ax && ax.LengthSquared() > 0.5f ? ax : Vector3.Up, R() * Mathf.Tau);
            float s = size * (0.45f + R() * R() * 1.2f);
            live.Add(new S
            {
                At = at + new Vector3((R() - 0.5f) * 0.4f, R() * 0.4f, (R() - 0.5f) * 0.4f),
                V = dir.Normalized() * speed * (0.5f + R() * 0.8f),
                Axis = axis.Normalized(),
                Spin = new Vector3(R() * 14 - 7, R() * 14 - 7, R() * 14 - 7),
                Life = 0.8f + R() * 0.9f,
                Size = s,
                Heat = heat * (0.5f + R() * 0.5f),
                Tint = tint,
                Shape = shape.Scaled(new Vector3(0.7f + R() * 0.6f, 0.8f + R() * 0.8f, 0.7f + R() * 0.6f)),
            });
        }
    }

    public void Step(float dt, Func<double, double, double> ground)
    {
        var mm = Multimesh;
        int n = 0;
        for (int i = live.Count - 1; i >= 0; i--)
        {
            var s = live[i];
            s.Age += dt;
            if (s.Age >= s.Life) { live.RemoveAt(i); continue; }
            if (!s.Down)
            {
                s.V.Y -= 16 * dt;
                s.At += s.V * dt;
                s.Angle += s.Spin.Length() * dt;
                float gy = (float)ground(s.At.X, s.At.Z) + s.Size * 0.15f;
                if (s.At.Y < gy)
                {
                    s.At.Y = gy;
                    if (Mathf.Abs(s.V.Y) > 2.5f) { s.V = new Vector3(s.V.X * 0.45f, -s.V.Y * 0.28f, s.V.Z * 0.45f); s.Spin *= 0.5f; }
                    else { s.Down = true; s.V = Vector3.Zero; }
                }
            }
            s.Heat *= Mathf.Exp(-dt * 6f);
            live[i] = s;
        }
        buf ??= new float[cap * 20];
        foreach (var s in live)
        {
            if (n >= cap) break;
            float k = s.Age / s.Life;
            float melt = Mathf.SmoothStep(0.55f, 1f, k);
            var b = (new Basis(s.Axis, s.Angle) * s.Shape).Scaled(Vector3.One * s.Size);
            // (One buffer for the batch, not three calls a shard.)
            int o = n * 20;
            buf[o] = b.X.X; buf[o + 1] = b.Y.X; buf[o + 2] = b.Z.X; buf[o + 3] = s.At.X;
            buf[o + 4] = b.X.Y; buf[o + 5] = b.Y.Y; buf[o + 6] = b.Z.Y; buf[o + 7] = s.At.Y;
            buf[o + 8] = b.X.Z; buf[o + 9] = b.Y.Z; buf[o + 10] = b.Z.Z; buf[o + 11] = s.At.Z;
            buf[o + 12] = s.Tint.R; buf[o + 13] = s.Tint.G; buf[o + 14] = s.Tint.B; buf[o + 15] = s.Tint.A;
            buf[o + 16] = s.Heat; buf[o + 17] = melt; buf[o + 18] = 0; buf[o + 19] = 0;
            n++;
        }
        if (n > 0 || shown > 0) RenderingServer.MultimeshSetBuffer(mm.GetRid(), buf);
        shown = n;
        mm.VisibleInstanceCount = n;
    }

    public void Clear() { live.Clear(); Multimesh.VisibleInstanceCount = 0; }
}
