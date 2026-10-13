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
    public enum Kind { Mote = 0, Streak = 1, Tongue = 2, Puff = 3, Thread = 4, Soot = 5, Fire = 6 }

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
            // Fade in over the first tenth, out over the last third (a puff thins as it spreads).
            float fade = Mathf.Clamp(k / 0.08f, 0, 1) * (1 - Mathf.SmoothStep(0.62f, 1, k));
            c.A *= fade;
            mm.SetInstanceTransform(n, new Transform3D(Basis.Identity.Scaled(Vector3.One * Mathf.Max(0.001f, s)), p.At));
            mm.SetInstanceColor(n, c);
            mm.SetInstanceCustomData(n, new Color(p.V.X, p.V.Y, p.V.Z, (int)p.Kind + Mathf.Min(k, 0.999f)));
            n++;
        }
        mm.VisibleInstanceCount = n;
    }

    public void Clear()
    {
        live.Clear();
        Multimesh.VisibleInstanceCount = 0;
    }
}
