using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// P1 jiggle r2 probe (--p1-probe): each breast's apex vertex (the most forward vertex the support shapes move) on every
/// mesh skinned to B's skeleton that carries form_support_*, CPU-skinned with the live blend weights and bone poses
/// (skeleton space, mm), and the support shapes' own share at it; so bare against support 1 is a number, not a guess.
/// </summary>
public sealed class P1JiggleProbe
{
    sealed class Apex { public MeshInstance3D Mi = null!; public int Side; public Vector3 P; public int[] B = System.Array.Empty<int>(); public float[] W = System.Array.Empty<float>(); public Vector3[] D = new Vector3[3]; public int[] Shape = new int[3]; }
    readonly List<Apex> apex = new();
    static readonly string[] Names = { "form_support_lift", "form_support_press", "form_support_fill" };

    public P1JiggleProbe(Skeleton3D sk)
    {
        foreach (var mi in sk.GetParent()?.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>() ?? Enumerable.Empty<MeshInstance3D>())
        {
            if (mi.Mesh is not ArrayMesh am || mi.GetNodeOrNull<Skeleton3D>(mi.Skeleton) != sk || mi.Skin == null) continue;
            int[] sh = Names.Select(n => mi.FindBlendShapeByName(n)).ToArray();
            if (sh[0] < 0) continue;
            bool rel = am.BlendShapeMode == Mesh.BlendShapeMode.Relative;
            for (int s = 0; s < am.GetSurfaceCount(); s++)
            {
                var a = am.SurfaceGetArrays(s);
                var v = a[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                var bones = a[(int)Mesh.ArrayType.Bones].AsInt32Array(); var wts = a[(int)Mesh.ArrayType.Weights].AsFloat32Array();
                int per = v.Length > 0 ? bones.Length / v.Length : 4;
                var bs = am.SurfaceGetBlendShapeArrays(s);
                var lift = bs[sh[0]][(int)Mesh.ArrayType.Vertex].AsVector3Array();
                foreach (int side in new[] { 1, -1 })
                {
                    int best = -1;
                    for (int i = 0; i < v.Length; i++)
                    {
                        if (v[i].X * side < 0.03f) continue;
                        var d = rel ? lift[i] : lift[i] - v[i];
                        if (d.Length() < 0.004f) continue;
                        if (best < 0 || v[i].Z > v[best].Z) best = i;
                    }
                    if (best < 0) continue;
                    var ap = new Apex { Mi = mi, Side = side, P = v[best], Shape = sh };
                    ap.B = Enumerable.Range(0, per).Select(k => bones[best * per + k]).ToArray();
                    ap.W = Enumerable.Range(0, per).Select(k => wts[best * per + k]).ToArray();
                    for (int k = 0; k < 3; k++)
                        if (sh[k] >= 0) { var x = bs[sh[k]][(int)Mesh.ArrayType.Vertex].AsVector3Array()[best]; ap.D[k] = rel ? x : x - v[best]; }
                    apex.Add(ap);
                }
            }
        }
    }

    public string Line(Skeleton3D sk)
    {
        var parts = new List<string>();
        foreach (var a in apex)
        {
            var w = a.Shape.Select(k => k >= 0 ? a.Mi.GetBlendShapeValue(k) : 0f).ToArray();
            var share = a.D[0] * w[0] + a.D[1] * w[1] + a.D[2] * w[2];
            var p = a.P + share;
            var o = Vector3.Zero;
            for (int k = 0; k < a.B.Length; k++)
            {
                if (a.W[k] <= 0) continue;
                int bi = a.Mi.Skin.GetBindBone(a.B[k]);
                if (bi < 0) bi = sk.FindBone(a.Mi.Skin.GetBindName(a.B[k]));
                o += (sk.GetBoneGlobalPose(bi) * a.Mi.Skin.GetBindPose(a.B[k]) * p) * a.W[k];
            }
            parts.Add($"{a.Mi.Name}{(a.Mi.IsVisibleInTree() ? "" : "(hidden)")} {(a.Side > 0 ? "l" : "r")} w {w[0]:F2}/{w[1]:F2}/{w[2]:F2} shapes ({share.X * 1000:F1},{share.Y * 1000:F1},{share.Z * 1000:F1})mm apex ({o.X * 1000:F1},{o.Y * 1000:F1},{o.Z * 1000:F1})mm");
        }
        return "p1: apex " + string.Join("; ", parts);
    }
}
