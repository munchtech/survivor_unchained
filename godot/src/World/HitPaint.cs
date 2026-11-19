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
    static readonly float[] Power = new float[N];
    static readonly double[] Born = new double[N];
    static readonly bool[] Live = new bool[N];
    static double lastAdd = -1e9;
    static int lastK = -1;
    static uint counter;
    static readonly bool Off = SurvivorUnchained.Args.Get("hitpaint") == "off";

    // (lead 9, the owner 19 Nov: "basically disolving by the time it hits the ground, unless its a particular dense / frequent
    // splatter area") The spray lives in the air (BattleFx.PaintSpray); the ground keeps paint only where hits come dense: 3+ hits
    // within 1.3 m in 1.6 s (a combo on one spot), or 2+ foes struck by one blow. A splat already there takes the next hits as
    // more power (more, farther droplets) and lives on from the latest. A single hit leaves nothing on the ground.
    const int RecentN = 16;
    static readonly double[] RT = new double[RecentN];
    static readonly float[] RX = new float[RecentN], RZ = new float[RecentN];
    static int rn;
    static Vector3 pendAt, pendAway; static bool pendCrit; static double pendT = -1e9;
    /// <summary>The hit paint's two colours (linear, the palette's "hit"), for the spray in the air.</summary>
    public static Color Body = new(0.43f, 0.005f, 0.045f), Edge = new(1f, 0.64f, 0.05f);

    /// <summary>A hit at (at) with the blow going away along (away) (xz): paint on the ground if the hits there are dense.</summary>
    public static void Add(Vector3 at, Vector3 away, bool crit, double now)
    {
        if (Off) return;
        RT[rn] = now; RX[rn] = at.X; RZ[rn] = at.Z; rn = (rn + 1) % RecentN;
        // one blow, a second foe: the cluster throws more (from the splat laid, or from the blow's first hit, laid now)
        if (now - lastAdd < 0.08)
        {
            if (lastK >= 0 && Live[lastK]) Power[lastK] = MathF.Min(Power[lastK] + 0.4f, 2.5f);
            else if (now - pendT < 0.08) { Lay(pendAt, pendAway, pendCrit ? 1.8f : 1.4f, now); pendT = -1e9; }
            return;
        }
        lastAdd = now; lastK = -1;
        int count = 0;
        for (int i = 0; i < RecentN; i++)
            if (now - RT[i] < 1.6 && now >= RT[i] && (RX[i] - at.X) * (RX[i] - at.X) + (RZ[i] - at.Z) * (RZ[i] - at.Z) < 1.69f) count++;
        if (count < 3) { pendAt = at; pendAway = away; pendCrit = crit; pendT = now; return; }
        // a live splat near: it builds up and lives on
        for (int i = 0; i < N; i++)
            if (Live[i] && (X[i] - at.X) * (X[i] - at.X) + (Z[i] - at.Z) * (Z[i] - at.Z) < 0.64f)
            { Power[i] = MathF.Min(Power[i] + 0.35f, 2.5f); Born[i] = now; lastK = i; return; }
        Lay(at, away, MathF.Min(1f + 0.25f * (count - 3) + (crit ? 0.5f : 0f), 2.5f), now);
    }

    static void Lay(Vector3 at, Vector3 away, float power, double now)
    {
        int k = -1;
        for (int i = 0; i < N && k < 0; i++) if (!Live[i]) k = i;
        if (k < 0) { k = 0; for (int i = 1; i < N; i++) if (Born[i] < Born[k]) k = i; }
        var d = new Vector2(away.X, away.Z);
        if (d.LengthSquared() < 1e-4f) d = new Vector2(0, -1);
        // (lead 9) thrown along the blow, in the shader's convention (ax = (cos a, sin a) in (x, z))
        d = d.Normalized();
        // (lead 8: laid 0.2 m past the contact along the blow: 0.6 m back it lay under her feet and was hidden)
        X[k] = at.X + d.X * 0.2f; Z[k] = at.Z + d.Y * 0.2f; Ang[k] = MathF.Atan2(d.Y, d.X); Power[k] = power; lastK = k; Born[k] = now; Live[k] = true;
        counter++;
        uint h = counter * 2654435761u; h ^= h >> 15; h *= 2246822519u; h ^= h >> 13;
        Seed[k] = (h & 0xFFFFu) / 65535f;
    }

    // (lead 9, perf) names made once; a stamp's globals are set only when they change; ps_hpb = one circle round every live stamp
    static readonly StringName[] NameA = new StringName[N], NameB = new StringName[N];
    static readonly StringName NameBound = new("ps_hpb");
    static readonly Vector4[] LastA = new Vector4[N], LastB = new Vector4[N];
    static Vector4 lastBound = new(0, 0, 0, -1);

    /// <summary>Each frame: the stamps' erosion by age and the globals.</summary>
    public static void Tick(double now)
    {
        if (NameA[0] == null) for (int i = 0; i < N; i++) { NameA[i] = new StringName($"ps_hp{i}a"); NameB[i] = new StringName($"ps_hp{i}b"); LastA[i] = new Vector4(float.NaN, 0, 0, 0); }
        int live = 0; float bx = 0, bz = 0, br = 0;
        Span<float> sz = stackalloc float[N];
        for (int i = 0; i < N; i++)
        {
            float size = 0, erode = 0;
            if (Live[i])
            {
                double age = now - Born[i];
                if (age >= 2.7 || age < 0) Live[i] = false;
                else
                {
                    size = 0.9f;   // (lead 9: the splat's scale, m; power throws farther)
                    erode = age < 0.7 ? 0f : age < 1.4 ? 0.34f : age < 2.1 ? 0.67f : 0.9f;
                }
            }
            sz[i] = size;
            if (size > 0) { live++; bx += X[i]; bz += Z[i]; sz[i] = size * (0.55f + 0.8f * MathF.Max(Power[i], 1f)); }
            var a = new Vector4(X[i], Z[i], Ang[i], size);
            var b = new Vector4(erode, Seed[i], Power[i], 0);
            if (a != LastA[i]) { RenderingServer.GlobalShaderParameterSet(NameA[i], a); LastA[i] = a; }
            if (b != LastB[i]) { RenderingServer.GlobalShaderParameterSet(NameB[i], b); LastB[i] = b; }
        }
        if (live > 0)
        {
            bx /= live; bz /= live;
            for (int i = 0; i < N; i++) if (sz[i] > 0) br = MathF.Max(br, MathF.Sqrt((X[i] - bx) * (X[i] - bx) + (Z[i] - bz) * (Z[i] - bz)) + sz[i]);
        }
        var bound = new Vector4(bx, bz, br, live);
        if (bound != lastBound) { RenderingServer.GlobalShaderParameterSet(NameBound, bound); lastBound = bound; }
    }
}
