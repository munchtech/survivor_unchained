using System;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Particles spawned one at a time from code (the web game's
/// render/particles.ts): each with its own velocity, gravity, drag, life,
/// size and colour over life, simulated here and drawn as one instanced
/// batch of camera-facing sprites. Additive for light, mixed for smoke.
/// Each draws a sprite (Sprites: a layer of the effects' texture array),
/// turned and turning; or, with none, a soft round spot. Smoke with none
/// named is a puff of the pack's smoke.
/// </summary>
public partial class Sparks : MultiMeshInstance3D
{
    public struct P
    {
        public Vector3 At, V;
        public float Gravity, Drag, Life, Age, Size, SizeEnd;
        public Color Color, ColorEnd;
        public float Alpha;
        /// <summary>The sprite (Sprites: its id), 0 for the batch's own, below 0 for a soft spot.</summary>
        public float Sprite;
        public float Spin, SpinV;
    }

    readonly P[] parts;
    readonly float[] buffer;
    readonly bool smoke;
    int count;
    const int Stride = 20;
    static readonly Random rng = new(11);

    public Sparks(int capacity, bool additive)
    {
        parts = new P[capacity];
        buffer = new float[capacity * Stride];
        smoke = !additive;
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>(additive ? "res://shaders/spark.gdshader" : "res://shaders/smoke.gdshader") };
        mat.SetShaderParameter("sprites", Sprites.Array);
        Multimesh = new MultiMesh
        {
            TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseColors = true, UseCustomData = true, InstanceCount = capacity, VisibleInstanceCount = 0,
            Mesh = new QuadMesh { Size = Vector2.One, Material = mat },
        };
        CastShadow = ShadowCastingSetting.Off;
        // They go everywhere: never culled as a whole.
        CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f));
    }

    public static float R() => (float)rng.NextDouble();

    public void Spawn(in P p)
    {
        if (count >= parts.Length) return;
        var q = p;
        if (q.ColorEnd.A == 0 && q.ColorEnd.R == 0 && q.ColorEnd.G == 0 && q.ColorEnd.B == 0) q.ColorEnd = q.Color;
        if (q.Alpha == 0) q.Alpha = 1;
        if (q.Sprite == 0) q.Sprite = smoke ? Sprites.Smoke() : -1;
        if (q.Sprite > 0 && q.Spin == 0) { q.Spin = R() * Mathf.Tau; if (q.SpinV == 0) q.SpinV = (R() - 0.5f) * 1.2f; }
        q.Age = 0;
        parts[count++] = q;
    }

    /// <param name="sprite">A sprite (Sprites); 0 for the batch's own (a
    /// soft spot, or for smoke a puff), below 0 for a soft spot always.</param>
    public void Spawn(Vector3 at, Vector3 v, float life, float size, Color color, Color? end = null, float sizeEnd = -1, float gravity = 0, float drag = 0, float alpha = 1, float sprite = 0, float spinV = 0) =>
        Spawn(new P { At = at, V = v, Life = life, Size = size, SizeEnd = sizeEnd < 0 ? size : sizeEnd, Color = color, ColorEnd = end ?? color, Gravity = gravity, Drag = drag, Alpha = alpha, Sprite = sprite, SpinV = spinV });

    public void Step(float dt)
    {
        int n = 0;
        for (int i = 0; i < count; i++)
        {
            var p = parts[i];
            p.Age += dt;
            if (p.Age >= p.Life) continue;
            p.V.Y -= p.Gravity * dt;
            if (p.Drag > 0) p.V *= Mathf.Exp(-p.Drag * dt);
            p.At += p.V * dt;
            p.Spin += p.SpinV * dt;
            parts[n++] = p;
        }
        count = n;
        for (int i = 0; i < count; i++)
        {
            ref var p = ref parts[i];
            float k = p.Age / p.Life;
            float s = Mathf.Lerp(p.Size, p.SizeEnd, k);
            var c = p.Color.Lerp(p.ColorEnd, k);
            float a = p.Alpha * (k < 0.8f ? 1 : 1 - (k - 0.8f) / 0.2f);
            int o = i * Stride;
            buffer[o] = s; buffer[o + 1] = 0; buffer[o + 2] = 0; buffer[o + 3] = p.At.X;
            buffer[o + 4] = 0; buffer[o + 5] = s; buffer[o + 6] = 0; buffer[o + 7] = p.At.Y;
            buffer[o + 8] = 0; buffer[o + 9] = 0; buffer[o + 10] = s; buffer[o + 11] = p.At.Z;
            buffer[o + 12] = c.R; buffer[o + 13] = c.G; buffer[o + 14] = c.B; buffer[o + 15] = a;
            buffer[o + 16] = Mathf.Max(0, p.Sprite); buffer[o + 17] = p.Spin; buffer[o + 18] = k; buffer[o + 19] = 0;
        }
        Multimesh.Buffer = buffer;
        Multimesh.VisibleInstanceCount = count;
    }

    public void Clear() { count = 0; Multimesh.VisibleInstanceCount = 0; }
}

/// <summary>An instanced batch of one mesh placed from code each frame
/// (projectiles in flight, stones on the ground).</summary>
public partial class Batch : MultiMeshInstance3D
{
    readonly float[] buffer;
    int count;

    public Batch(Mesh mesh, int capacity, Material mat, bool shadow = false)
    {
        buffer = new float[capacity * 16];
        MaterialOverride = mat;
        Multimesh = new MultiMesh { TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseColors = true, InstanceCount = capacity, VisibleInstanceCount = 0, Mesh = mesh };
        CastShadow = shadow ? ShadowCastingSetting.On : ShadowCastingSetting.Off;
        CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f));
    }

    public void Begin() => count = 0;

    public void Add(Transform3D t, Color c)
    {
        if (count * 16 >= buffer.Length) return;
        int o = count++ * 16;
        var b = t.Basis;
        buffer[o] = b.X.X; buffer[o + 1] = b.Y.X; buffer[o + 2] = b.Z.X; buffer[o + 3] = t.Origin.X;
        buffer[o + 4] = b.X.Y; buffer[o + 5] = b.Y.Y; buffer[o + 6] = b.Z.Y; buffer[o + 7] = t.Origin.Y;
        buffer[o + 8] = b.X.Z; buffer[o + 9] = b.Y.Z; buffer[o + 10] = b.Z.Z; buffer[o + 11] = t.Origin.Z;
        buffer[o + 12] = c.R; buffer[o + 13] = c.G; buffer[o + 14] = c.B; buffer[o + 15] = c.A;
    }

    public void End()
    {
        Multimesh.Buffer = buffer;
        Multimesh.VisibleInstanceCount = count;
    }
}
