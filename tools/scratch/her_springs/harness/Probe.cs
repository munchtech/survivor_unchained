using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using System.Threading.Tasks;
using SurvivorUnchained.Play;

namespace H;

/// <summary>The in-game probe (View/WearInside) replayed: skin with blend shapes, InsideTest, counts by region.</summary>
public static class Probe
{
    public const float InsideMm = 0.5f;

    public static string Region(string bone)
    {
        if (bone.StartsWith("thigh", StringComparison.OrdinalIgnoreCase) || bone.StartsWith("glute", StringComparison.OrdinalIgnoreCase) || bone.StartsWith("calf", StringComparison.OrdinalIgnoreCase)) return "thigh";
        foreach (var a in new[] { "upperarm", "delt", "clavicle", "trap", "lowerarm" })
            if (bone.StartsWith(a, StringComparison.OrdinalIgnoreCase)) return "arm";
        return "torso";
    }

    /// <summary>Base positions/normals with the blend shapes at w applied.</summary>
    public static (Vector3[] P, Vector3[] N) Shaped(MeshD m, float[] w)
    {
        var p = m.Pos; var n = m.Nrm;
        bool any = false;
        for (int s = 0; s < w.Length; s++) if (Math.Abs(w[s]) > 1e-6f) { any = true; break; }
        if (!any) return (p, n);
        p = (Vector3[])p.Clone(); n = (Vector3[])n.Clone();
        for (int s = 0; s < w.Length; s++)
        {
            if (Math.Abs(w[s]) <= 1e-6f) continue;
            var sh = m.Shapes[s];
            for (int i = 0; i < sh.Idx.Length; i++) { p[sh.Idx[i]] += w[s] * sh.DP[i]; n[sh.Idx[i]] += w[s] * sh.DN[i]; }
        }
        return (p, n);
    }

    /// <summary>Linear blend skinning by the bind matrices t (skeleton space), as WearInside.Skin.</summary>
    public static void Skin(Vector3[] p, Vector3[] n, int[] bones, float[] weights, int k, Aff[] t, Vector3[] outP, Vector3[]? outN)
    {
        Parallel.For(0, p.Length, i =>
        {
            Vector3 a = Vector3.Zero, nn = Vector3.Zero;
            for (int j = 0; j < k; j++)
            {
                float w = weights[i * k + j];
                if (w <= 0) continue;
                int b = bones[i * k + j];
                if (b < 0 || b >= t.Length) continue;
                a += w * t[b].Apply(p[i]);
                if (outN != null) nn += w * t[b].Basis(n[i]);
            }
            outP[i] = a;
            if (outN != null) outN[i] = nn.LengthSquared() > 0 ? Vector3.Normalize(nn) : Vector3.UnitY;
        });
    }

    public sealed class Stat { public int N, Inside, Thigh, Arm, Torso; public float Deep; public int[]? PerVertexInside; }

    /// <summary>Counts of points inside the body; region by the body vertex's dominant bone.</summary>
    public static Stat Count(InsideTest test, string[] region, Vector3[] pts, bool[]? mask = null, float[]? depthOut = null)
    {
        var d = new float[pts.Length]; var vert = new int[pts.Length];
        Parallel.For(0, pts.Length, i =>
        {
            if (mask != null && !mask[i]) { d[i] = 1; vert[i] = -1; return; }
            var (dist, v) = test.Query(pts[i]); d[i] = dist; vert[i] = v;
        });
        var st = new Stat();
        for (int i = 0; i < pts.Length; i++)
        {
            if (mask != null && !mask[i]) continue;
            st.N++;
            if (depthOut != null) depthOut[i] = vert[i] < 0 ? 0 : Math.Max(0, -d[i]);
            if (vert[i] < 0 || d[i] >= -InsideMm / 1000f) continue;
            st.Inside++;
            st.Deep = Math.Max(st.Deep, -d[i] * 1000f);
            switch (region[vert[i]]) { case "thigh": st.Thigh++; break; case "arm": st.Arm++; break; default: st.Torso++; break; }
        }
        return st;
    }
}
