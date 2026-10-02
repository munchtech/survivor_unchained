using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>Rings of thrown air racing out from a blast, bending what is
/// behind them (shaders/shockwave.gdshader). One instanced batch.</summary>
public partial class Shockwaves : MultiMeshInstance3D
{
    struct Wave { public Vector3 At; public float Radius, Life, Age, Strength; public Color Tint; }

    readonly List<Wave> waves = new();
    float[] buffer = new float[32 * Stride];
    const int Stride = 20;

    public Shockwaves()
    {
        Name = "Shockwaves";
        CastShadow = ShadowCastingSetting.Off;
        CustomAabb = new Aabb(new Vector3(-1e4f, -1e4f, -1e4f), new Vector3(2e4f, 2e4f, 2e4f));
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/shockwave.gdshader") };
        Multimesh = new MultiMesh
        {
            TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseColors = true, UseCustomData = true,
            InstanceCount = 32, VisibleInstanceCount = 0,
            Mesh = new PlaneMesh { Size = new Vector2(2, 2), Material = mat },
        };
    }

    /// <summary>A ring out to `radius` over `life` seconds, its lip tinted.</summary>
    public void Add(Vector3 at, float radius, float life, Color tint, float strength = 1)
    {
        if (waves.Count >= 64) return;
        waves.Add(new Wave { At = at, Radius = radius, Life = Mathf.Max(0.05f, life), Tint = tint, Strength = strength });
    }

    public void Step(float dt)
    {
        int n = 0;
        for (int i = 0; i < waves.Count; i++)
        {
            var w = waves[i];
            w.Age += dt;
            if (w.Age < w.Life) waves[n++] = w;
        }
        waves.RemoveRange(n, waves.Count - n);
        if (n > Multimesh.InstanceCount)
        {
            Multimesh.InstanceCount = Mathf.NearestPo2(n);
            buffer = new float[Multimesh.InstanceCount * Stride];
        }
        for (int i = 0; i < n; i++)
        {
            var w = waves[i];
            float s = w.Radius;
            int o = i * Stride;
            buffer[o] = s; buffer[o + 1] = 0; buffer[o + 2] = 0; buffer[o + 3] = w.At.X;
            buffer[o + 4] = 0; buffer[o + 5] = 1; buffer[o + 6] = 0; buffer[o + 7] = w.At.Y;
            buffer[o + 8] = 0; buffer[o + 9] = 0; buffer[o + 10] = s; buffer[o + 11] = w.At.Z;
            buffer[o + 12] = w.Tint.R; buffer[o + 13] = w.Tint.G; buffer[o + 14] = w.Tint.B; buffer[o + 15] = w.Strength;
            buffer[o + 16] = w.Age / w.Life; buffer[o + 17] = 0; buffer[o + 18] = 0; buffer[o + 19] = 0;
        }
        if (n > 0) Multimesh.Buffer = buffer;
        Multimesh.VisibleInstanceCount = n;
    }
}
