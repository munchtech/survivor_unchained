using System;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>(lane J lead 8, the owner 19 Nov: "Hit paint") Her hits leave a crescent of colour on the ground for a moment
/// (shaders/paint_stroke.gdshaderinc, terrain only). A ring of 8 stamps: ps_hp&lt;k&gt;a = (x, z, angle, size m; size 0 = empty),
/// ps_hp&lt;k&gt;b = (erode, seed, crit, 0). The mark lies across the blow. It dies by stepping (FX_LANGUAGE §4: never an alpha
/// fade): holes open and it thins in three steps, then it is gone. Time is the game's (BattleFx's clock), so --fixed-fps shots repeat.</summary>
public static class HitPaint
{
    const int N = 8;
    static readonly float[] X = new float[N], Z = new float[N], Ang = new float[N], Seed = new float[N];
    static readonly bool[] Crit = new bool[N];
    static readonly double[] Born = new double[N];
    static readonly bool[] Live = new bool[N];
    static double lastAdd = -1e9;
    static uint counter;
    static readonly bool Off = SurvivorUnchained.Args.Get("hitpaint") == "off";

    /// <summary>A hit at (at) with the blow going away along (away) (xz): one stamp, rate limited.</summary>
    public static void Add(Vector3 at, Vector3 away, bool crit, double now)
    {
        if (Off) return;
        if (now - lastAdd < 0.08) return;
        for (int i = 0; i < N; i++)
            if (Live[i] && now - Born[i] < 0.3 && (X[i] - at.X) * (X[i] - at.X) + (Z[i] - at.Z) * (Z[i] - at.Z) < 0.25f) return;
        int k = -1;
        for (int i = 0; i < N && k < 0; i++) if (!Live[i]) k = i;
        if (k < 0) { k = 0; for (int i = 1; i < N; i++) if (Born[i] < Born[k]) k = i; }
        var d = new Vector2(away.X, away.Z);
        if (d.LengthSquared() < 1e-4f) d = new Vector2(0, -1);
        // across the blow: the perpendicular of away, in the shader's convention (ax = (cos a, sin a) in (x, z))
        d = d.Normalized();
        float px = -d.Y, pz = d.X;
        // (lead 8: laid 0.2 m past the contact along the blow: 0.6 m back it lay under her feet and was hidden; her contact is ~0.6 m from her)
        X[k] = at.X + d.X * 0.2f; Z[k] = at.Z + d.Y * 0.2f; Ang[k] = MathF.Atan2(pz, px); Crit[k] = crit; Born[k] = now; Live[k] = true;
        counter++;
        uint h = counter * 2654435761u; h ^= h >> 15; h *= 2246822519u; h ^= h >> 13;
        Seed[k] = (h & 0xFFFFu) / 65535f;
        lastAdd = now;
    }

    /// <summary>Each frame: the stamps' erosion by age and the 16 globals.</summary>
    public static void Tick(double now)
    {
        for (int i = 0; i < N; i++)
        {
            float size = 0, erode = 0;
            if (Live[i])
            {
                double age = now - Born[i];
                if (age >= 2.7 || age < 0) Live[i] = false;
                else
                {
                    size = Crit[i] ? 2.0f : 1.6f;
                    erode = age < 0.6 ? 0f : age < 1.3 ? 0.3f : age < 2.0 ? 0.55f : 0.8f;
                }
            }
            RenderingServer.GlobalShaderParameterSet($"ps_hp{i}a", new Vector4(X[i], Z[i], Ang[i], size));
            RenderingServer.GlobalShaderParameterSet($"ps_hp{i}b", new Vector4(erode, Seed[i], Crit[i] ? 1f : 0f, 0));
        }
    }
}
