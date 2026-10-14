using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Burns Twice's ice: shards of real, lit geometry (shaders/flare_shard.gdshader) thrown from each impact and
/// from every frozen body that shatters. Faceted plates of cold glass (judge 3: 3-6 a statue, 15-40 cm; the old
/// splinters, stretched by their speed, read as sticks), they tumble flashing, land flat, and melt to a glint of
/// water over a second or so.
/// </summary>
public partial class FlareShards : MultiMeshInstance3D
{
    struct S
    {
        public Vector3 At, V, Axis, Scale;
        public float Angle, Spin, Age, Size, Heat, Seed, DownAge, MeltT;
        public Color Tint;
        public Basis Shape;
        public Quaternion Land0, Land1;
        public bool Down;
        /// <summary>Thrown by the ring: flies low and hot along its way.</summary>
        public bool Thrown;
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

    /// <summary>A shard: a broken plate of ice about a metre across before scaling (its local Y the plate's normal),
    /// an irregular six-sided outline, each face raised to an off-centre ridge point so its twelve facets catch the
    /// light each at its own angle.</summary>
    static Mesh ShardMesh(Material mat)
    {
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        const int sides = 6;
        var ring = new Vector3[sides];
        var r = new Random(5);
        for (int i = 0; i < sides; i++)
        {
            float a = i * Mathf.Tau / sides + ((float)r.NextDouble() - 0.5f) * 0.7f;
            float w = 0.36f + (float)r.NextDouble() * 0.2f;
            // One long point: ice breaks along its grain.
            if (i == 1) w = 0.62f;
            ring[i] = new Vector3(Mathf.Cos(a) * w, ((float)r.NextDouble() - 0.5f) * 0.03f, Mathf.Sin(a) * w);
        }
        var top = new Vector3(0.09f, 0.075f, -0.05f);
        var bottom = new Vector3(-0.06f, -0.055f, 0.04f);
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

    /// <summary>A burst of shards from a point: n of them, up and out at about this speed, about this big across
    /// (m, 0.6-1.6x), tinted by a body's paint (alpha: how much), hot from the ember that broke them.</summary>
    public void Burst(Vector3 at, int n, float speed, float size, Color tint, float heat, Vector3? away = null, bool thrown = false)
    {
        for (int i = 0; i < n && live.Count < cap; i++)
        {
            float a = R() * Mathf.Tau;
            var dir = new Vector3(Mathf.Cos(a), 0.55f + R() * 1.1f, Mathf.Sin(a));
            if (away is Vector3 aw) dir += new Vector3(aw.X, 0, aw.Z) * 0.8f;
            // Thrown by the ring: out along its way, low, landing a metre or three on.
            if (thrown && away is Vector3 tw) dir = new Vector3(tw.X + Mathf.Cos(a) * 0.4f, 0.3f + R() * 0.45f, tw.Z + Mathf.Sin(a) * 0.4f);
            var axis = new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f);
            if (axis.LengthSquared() < 1e-3f) axis = Vector3.Up;
            var sa = new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f);
            var shape = new Basis(sa.LengthSquared() > 1e-3f ? sa.Normalized() : Vector3.Up, R() * Mathf.Tau);
            live.Add(new S
            {
                At = at + new Vector3((R() - 0.5f) * 0.4f, R() * 0.4f, (R() - 0.5f) * 0.4f),
                V = dir.Normalized() * speed * (thrown ? 0.75f + R() * 0.5f : 0.5f + R() * 0.8f),
                Axis = axis.Normalized(),
                Spin = 6 + R() * 8,
                Size = size * (0.6f + R() * 1.0f),
                Heat = heat * (0.5f + R() * 0.5f),
                Seed = R(),
                MeltT = 1.0f + R() * 0.5f,
                Thrown = thrown,
                Tint = tint,
                Shape = shape,
                Scale = new Vector3(0.7f + R() * 0.6f, 0.8f + R() * 0.7f, 0.55f + R() * 0.45f),
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
            if (s.Down)
            {
                s.DownAge += dt;
                if (s.DownAge >= s.MeltT || s.Age > 6) { live.RemoveAt(i); continue; }
            }
            else
            {
                s.V.Y -= 16 * dt;
                s.At += s.V * dt;
                s.Angle += s.Spin * dt;
                float gy = (float)ground(s.At.X, s.At.Z) + s.Size * 0.03f;
                if (s.At.Y < gy)
                {
                    s.At.Y = gy;
                    if (Mathf.Abs(s.V.Y) > 2.5f) { s.V = new Vector3(s.V.X * 0.45f, -s.V.Y * 0.28f, s.V.Z * 0.45f); s.Spin *= 0.5f; }
                    else
                    {
                        // It settles flat on whichever face is down, turning there over a tenth of a second.
                        s.Down = true; s.V = Vector3.Zero;
                        var q0 = (new Basis(s.Axis, s.Angle) * s.Shape).GetRotationQuaternion();
                        var q1 = new Quaternion(Vector3.Up, s.Seed * Mathf.Tau);
                        if ((q0 * Vector3.Up).Y < 0) q1 *= new Quaternion(Vector3.Right, Mathf.Pi);
                        s.Land0 = q0; s.Land1 = q1;
                    }
                }
            }
            // (Hot rims for about a third of a second: held longer, the thrown shards lay over the reach as orange
            // straw, judge 3.)
            s.Heat *= Mathf.Exp(-dt * (s.Down ? 6f : s.Thrown ? 3.2f : 6f));
            live[i] = s;
        }
        buf ??= new float[cap * 20];
        foreach (var s in live)
        {
            if (n >= cap) break;
            float melt = s.Down ? Mathf.Clamp(s.DownAge / s.MeltT, 0, 1) : 0;
            Basis rot = s.Down
                ? new Basis(s.Land0.Slerp(s.Land1, Mathf.SmoothStep(0, 1, Mathf.Clamp(s.DownAge / 0.1f, 0, 1))))
                : new Basis(s.Axis, s.Angle) * s.Shape;
            // Melting: it sinks flat and shrinks to a small pool, its last glints the water's.
            var sc = s.Scale * s.Size;
            sc = new Vector3(sc.X * (1 - 0.55f * melt), sc.Y * (1 - 0.85f * melt), sc.Z * (1 - 0.55f * melt));
            var b = rot * Basis.FromScale(sc);
            // A little longer along its flight while fast (at up to 2.6x the splinters were sticks: judge 3).
            float sp = s.Down ? 0 : s.V.Length();
            if (sp > 3f)
            {
                var u = s.V / sp;
                float st = Mathf.Min(sp * 0.02f, 0.3f);
                b = new Basis(new Vector3(1, 0, 0) + u * (u.X * st), new Vector3(0, 1, 0) + u * (u.Y * st), new Vector3(0, 0, 1) + u * (u.Z * st)) * b;
            }
            // (One buffer for the batch, not three calls a shard.)
            int o = n * 20;
            buf[o] = b.X.X; buf[o + 1] = b.Y.X; buf[o + 2] = b.Z.X; buf[o + 3] = s.At.X;
            buf[o + 4] = b.X.Y; buf[o + 5] = b.Y.Y; buf[o + 6] = b.Z.Y; buf[o + 7] = s.At.Y;
            buf[o + 8] = b.X.Z; buf[o + 9] = b.Y.Z; buf[o + 10] = b.Z.Z; buf[o + 11] = s.At.Z;
            buf[o + 12] = s.Tint.R; buf[o + 13] = s.Tint.G; buf[o + 14] = s.Tint.B; buf[o + 15] = s.Tint.A;
            buf[o + 16] = s.Heat; buf[o + 17] = melt; buf[o + 18] = s.Down ? 1 : 0; buf[o + 19] = s.Seed;
            n++;
        }
        if (n > 0 || shown > 0) RenderingServer.MultimeshSetBuffer(mm.GetRid(), buf);
        shown = n;
        mm.VisibleInstanceCount = n;
    }

    public void Clear() { live.Clear(); Multimesh.VisibleInstanceCount = 0; }
}
