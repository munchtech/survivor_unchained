using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The Flares' own particles (shaders/flare_bits.gdshader): motes, molten streaks, tongues of flame, puffs of
/// steam and smoke, threads of light and soot, drawn from shape and our noise (no sprite sheet). One batch adds
/// light; the other (lit, mixed) is the dark bed under it. Simulated here on the Flare's own clock.
/// </summary>
public partial class FlareBits : MultiMeshInstance3D
{
    public enum Kind { Mote = 0, Streak = 1, Tongue = 2, Puff = 3, Thread = 4, Soot = 5, Fire = 6, Scar = 7, Smoke = 8 }

    public struct P
    {
        public Vector3 At, V;
        public float Life, Age, Size, SizeEnd, Gravity, Drag, Lift;
        public Color Color, ColorEnd;
        public Kind Kind;
        /// <summary>Drawn toward this point (a thread or mote drawn up into her staff): its pull, m/s².</summary>
        public Vector3? Home;
        public float Pull;
        /// <summary>Steam's air: Swirl, the eddies' push (m/s²), a slow churn so a column billows and breaks up
        /// instead of rising as a contrail; Wind, a steady push (m/s²) so the column leans more the higher it is;
        /// Seed, the column's own eddies (a little of each puff's own).</summary>
        public float Swirl, Seed;
        public Vector3 Wind;
    }

    readonly List<P> live = new();
    float[]? buf;
    int shown;
    readonly int cap;
    readonly bool mixed;
    static Shader? addShader, mixShader;

    public int Count => live.Count;

    public FlareBits(int capacity, bool mixedBatch)
    {
        cap = capacity;
        mixed = mixedBatch;
        Name = mixed ? "FlareBitsMix" : "FlareBitsAdd";
        var code = FileAccess.GetFileAsString("res://shaders/flare_bits.gdshader");
        Shader sh;
        if (mixed) sh = mixShader ??= new Shader { Code = code.Replace("render_mode unshaded, ", "render_mode ").Replace("blend_add", "blend_mix") };
        else sh = addShader ??= GD.Load<Shader>("res://shaders/flare_bits.gdshader");
        var mat = new ShaderMaterial { Shader = sh, RenderPriority = mixed ? -2 : 2 };
        Multimesh = new MultiMesh
        {
            TransformFormat = MultiMesh.TransformFormatEnum.Transform3D,
            UseColors = true,
            UseCustomData = true,
            Mesh = new QuadMesh { Size = Vector2.One, Material = mat },
            InstanceCount = cap,
            VisibleInstanceCount = 0,
        };
        CastShadow = ShadowCastingSetting.Off;
        CustomAabb = new Aabb(new Vector3(-500, -50, -500), new Vector3(1000, 200, 1000));
    }

    public void Spawn(in P p)
    {
        if (live.Count >= cap) return;
        live.Add(p);
    }

    public void Spawn(Kind kind, Vector3 at, Vector3 v, float life, float size, Color color, Color? end = null, float sizeEnd = -1,
        float gravity = 0, float drag = 0, float lift = 0) =>
        Spawn(new P { Kind = kind, At = at, V = v, Life = life, Size = size, SizeEnd = sizeEnd < 0 ? size : sizeEnd, Color = color, ColorEnd = end ?? color, Gravity = gravity, Drag = drag, Lift = lift });

    /// <summary>A step on the Flare's clock, and the batch written.</summary>
    public void Step(float dt, Func<double, double, double>? ground = null)
    {
        var mm = Multimesh;
        int n = 0;
        buf ??= new float[cap * 20];
        for (int i = live.Count - 1; i >= 0; i--)
        {
            var p = live[i];
            p.Age += dt;
            if (p.Age >= p.Life) { live.RemoveAt(i); continue; }
            if (p.Home is Vector3 h)
            {
                var to = h - p.At;
                float d = to.Length();
                if (d < 0.25f) { live.RemoveAt(i); continue; }
                p.V += to / d * p.Pull * dt;
                // Drawn in, not orbiting: what runs across the line to her is bled off.
                var along = to / d * p.V.Dot(to / d);
                p.V = along + (p.V - along) * Mathf.Exp(-6 * dt);
            }
            if (p.Swirl > 0)
            {
                // Eddies keyed to height and age: neighbours in a column share them (it snakes), the seed sets each
                // column's own, and they grow as the puff rises (steam leaves the crater tight and breaks up above).
                float y = p.At.Y, a = p.Age, s = p.Seed * 6.283f, grow = 0.35f + Mathf.Min(1.6f, a * 0.6f);
                var turb = new Vector3(
                    Mathf.Sin(y * 1.1f + a * 1.3f + s) + 0.6f * Mathf.Sin(y * 2.7f - a * 2.1f + s * 2.7f),
                    0.45f * Mathf.Sin(a * 2.4f + s * 1.9f + y * 1.7f),
                    Mathf.Cos(y * 0.9f + a * 1.6f + s * 0.7f) + 0.6f * Mathf.Cos(y * 2.3f + a * 1.9f + s * 1.8f));
                p.V += (turb * p.Swirl * grow + p.Wind) * dt;
            }
            p.V.Y += (p.Lift - p.Gravity) * dt;
            if (p.Drag > 0) p.V *= Mathf.Exp(-p.Drag * dt);
            p.At += p.V * dt;
            if (ground != null && p.Gravity > 0)
            {
                float gy = (float)ground(p.At.X, p.At.Z);
                if (p.At.Y < gy + 0.02f) { p.At.Y = gy + 0.02f; p.V = new Vector3(p.V.X * 0.3f, -p.V.Y * 0.2f, p.V.Z * 0.3f); }
            }
            live[i] = p;
        }
        foreach (var p in live)
        {
            if (n >= cap) break;
            float k = p.Age / p.Life;
            float s = Mathf.Lerp(p.Size, p.SizeEnd, k);
            var c = p.Color.Lerp(p.ColorEnd, k);
            // Fade in over the first tenth, out over the last third (a puff thins as it spreads; a scar is burnt
            // in at once).
            float fade = Mathf.Clamp(k / (p.Kind == Kind.Scar ? 0.005f : 0.08f), 0, 1) * (1 - Mathf.SmoothStep(0.62f, 1, k));
            c.A *= fade;
            // (One buffer for the whole batch: thousands of calls a frame, one per instance and field, cost
            // milliseconds.)
            int o = n * 20;
            float sz = Mathf.Max(0.001f, s);
            buf[o] = sz; buf[o + 1] = 0; buf[o + 2] = 0; buf[o + 3] = p.At.X;
            buf[o + 4] = 0; buf[o + 5] = sz; buf[o + 6] = 0; buf[o + 7] = p.At.Y;
            buf[o + 8] = 0; buf[o + 9] = 0; buf[o + 10] = sz; buf[o + 11] = p.At.Z;
            buf[o + 12] = c.R; buf[o + 13] = c.G; buf[o + 14] = c.B; buf[o + 15] = c.A;
            buf[o + 16] = p.V.X; buf[o + 17] = p.V.Y; buf[o + 18] = p.V.Z; buf[o + 19] = (int)p.Kind + Mathf.Min(k, 0.999f);
            n++;
        }
        if (n > 0 || shown > 0) RenderingServer.MultimeshSetBuffer(mm.GetRid(), buf);
        shown = n;
        mm.VisibleInstanceCount = n;
    }

    public void Clear()
    {
        live.Clear();
        Multimesh.VisibleInstanceCount = 0;
    }
}
