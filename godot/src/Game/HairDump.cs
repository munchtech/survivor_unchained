using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Play;

/// <summary>--hairdump DIR (a developer's switch, Args): at creation's Look, from 2 s in and every 0.25 s, her hair as the
/// game draws it (CPU-skinned, plus heroine_hair.gdshaderinc's vertex() from each surface's current uniforms, its `air`
/// left out) and her other meshes (body, head, outfit; not eyes, teeth, tongue, lashes, brows; her skin tucked under the
/// outfit as heroine_skin.gdshader draws it, its discarded triangles left out), in world space, for
/// tools/scratch/face29/posed_clip.py to measure how far her hair passes into her. Read on the skeleton's
/// SkeletonUpdated, so her modifiers' corrections (HerPose and the rest) are in the pose.
///
/// Files (little-endian):
///   meta.txt   once: "S i kind name material nverts ntris cap tie" per surface (kind hair|body), then "B j name" per bone,
///              then "C i" per hair mesh with a chain (its order in each frame's chain block).
///   sNN.idx    once per body surface: int32 triangle indices.
///   sNN.attr   once per hair surface: per vertex float32 uv_y, uv2_x, uv2_y, colour_b, int32 dominant bone (index in the B table).
///   kNN.bin    per frame: float32 time; then per surface in meta order nverts*3 float32 world positions; then per chain
///              8*3 float32 (HairSway.ChainWorld, world).</summary>
public static class HairDump
{
    static string? dir;
    static double next = 2.0, clock;
    static int frame;
    static bool due, wired;
    static Skeleton3D? wiredOn;

    sealed class S { public MeshInstance3D Mi = null!; public int Surf; public bool Hair, Cap, Tie; public Vector2[] Uv = [], Uv2 = []; public float[] Cb = []; public float Tuck; public float[] TuckW = []; }
    static readonly List<S> surfs = new();
    static readonly List<HairSway> chains = new();
    static readonly string[] Skip = ["hair", "lash", "brow", "eye", "teeth", "tongue"];

    /// <summary>Each frame of creation (GameFront.UpdateCreate).</summary>
    public static void Tick(PersonView? figure, double dt)
    {
        if (figure == null) return;
        dir ??= Args.Get("hairdump");
        if (string.IsNullOrEmpty(dir)) return;
        var p = figure.Person;
        if (wiredOn != p.Skeleton) { wiredOn = p.Skeleton; wired = false; }
        if (!wired)
        {
            wired = true;
            p.Skeleton.SkeletonUpdated += () => { if (due) { due = false; try { Dump(p); } catch (Exception e) { GD.PrintErr("HAIRDUMP " + e); } } };
        }
        clock += dt;
        if (clock >= next) { next += 0.25; due = true; }
    }

    static void Setup(People.Person p)
    {
        Directory.CreateDirectory(dir!);
        var sk = p.Skeleton;
        var meta = new List<string>();
        foreach (var mi in p.Meshes)
        {
            bool hair = p.Hair.Contains(mi);
            var low = mi.Name.ToString().ToLowerInvariant();
            if (!hair && Skip.Any(low.Contains)) continue;
            if (!mi.IsVisibleInTree() || mi.Mesh == null) continue;
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
            {
                var a = mi.Mesh.SurfaceGetArrays(s);
                var P = a[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                var I = a[(int)Mesh.ArrayType.Index].AsInt32Array();
                var mat = mi.GetSurfaceOverrideMaterial(s) ?? mi.GetActiveMaterial(s);
                var x = new S { Mi = mi, Surf = s, Hair = hair };
                int i = surfs.Count;
                if (hair)
                {
                    if (mat is ShaderMaterial sm) { x.Cap = sm.GetShaderParameter("cap").AsBool(); x.Tie = sm.GetShaderParameter("tie").AsBool(); }
                    x.Uv = a[(int)Mesh.ArrayType.TexUV].AsVector2Array();
                    x.Uv2 = a[(int)Mesh.ArrayType.TexUV2].VariantType == Variant.Type.Nil ? new Vector2[P.Length] : a[(int)Mesh.ArrayType.TexUV2].AsVector2Array();
                    if (x.Uv.Length != P.Length) x.Uv = new Vector2[P.Length];
                    if (x.Uv2.Length != P.Length) x.Uv2 = new Vector2[P.Length];
                    var col = a[(int)Mesh.ArrayType.Color].VariantType == Variant.Type.Nil ? [] : a[(int)Mesh.ArrayType.Color].AsColorArray();
                    x.Cb = col.Length == P.Length ? col.Select(c => c.B).ToArray() : Enumerable.Repeat(1f, P.Length).ToArray();
                    var bones = a[(int)Mesh.ArrayType.Bones].AsInt32Array();
                    var wts = a[(int)Mesh.ArrayType.Weights].AsFloat32Array();
                    int st = P.Length > 0 ? bones.Length / P.Length : 0;
                    using var w = new BinaryWriter(File.Create(Path.Combine(dir!, $"s{i:D2}.attr")));
                    for (int v = 0; v < P.Length; v++)
                    {
                        int best = 0;
                        for (int q = 1; q < st; q++) if (wts[v * st + q] > wts[v * st + best]) best = q;
                        int bi = st > 0 ? bones[v * st + best] : -1;
                        int bone = bi < 0 ? -1 : mi.Skin != null ? BoneOf(sk, mi.Skin, bi) : bi;
                        w.Write(x.Uv[v].Y); w.Write(x.Uv2[v].X); w.Write(x.Uv2[v].Y); w.Write(x.Cb[v]); w.Write(bone);
                    }
                }
                else
                {
                    // Her skin under an outfit (heroine_skin.gdshader's tuck): pulled in along its normal by tuck x the
                    // channel's weight (all of it from 0.973), and the triangles where it is gone (>= 0.995) discarded.
                    var keep = I;
                    if (mat is ShaderMaterial sm && sm.GetShaderParameter("tuck_channel") is { VariantType: Variant.Type.Int } tc && tc.AsInt32() >= 0)
                    {
                        int ch = tc.AsInt32();
                        var col = a[(int)Mesh.ArrayType.Color].AsColorArray();
                        x.Tuck = sm.GetShaderParameter("tuck").VariantType == Variant.Type.Nil ? 0.010f : sm.GetShaderParameter("tuck").AsSingle();
                        x.TuckW = new float[P.Length];
                        var gone = new float[P.Length];
                        for (int v = 0; v < P.Length && v < col.Length; v++)
                        {
                            float h = ch == 0 ? col[v].R : ch == 1 ? col[v].G : ch == 2 ? col[v].B : col[v].A;
                            x.TuckW[v] = h > 0.973f ? 1f : h;
                            gone[v] = h >= 0.995f ? 1f : 0f;
                        }
                        var kept = new List<int>();
                        for (int t = 0; t + 2 < I.Length; t += 3)
                            if ((gone[I[t]] + gone[I[t + 1]] + gone[I[t + 2]]) / 3f <= 0.5f) { kept.Add(I[t]); kept.Add(I[t + 1]); kept.Add(I[t + 2]); }
                        keep = kept.ToArray();
                    }
                    using var w = new BinaryWriter(File.Create(Path.Combine(dir!, $"s{i:D2}.idx")));
                    foreach (var q in keep) w.Write(q);
                    I = keep;
                }
                surfs.Add(x);
                var mname = (mat?.ResourceName is { Length: > 0 } rn ? rn : mat?.ResourcePath is { Length: > 0 } rp ? Path.GetFileNameWithoutExtension(rp) : $"surf{s}").Replace(' ', '_');
                meta.Add($"S {i} {(hair ? "hair" : "body")} {mi.Name.ToString().Replace(' ', '_')} {mname} {P.Length} {I.Length / 3} {(x.Cap ? 1 : 0)} {(x.Tie ? 1 : 0)}");
            }
            if (hair && mi.GetChildren().OfType<HairSway>().FirstOrDefault() is { } hs && hs.ChainWorld.Length == 8)
            { meta.Add($"C {chains.Count} {mi.Name}"); chains.Add(hs); }
        }
        for (int b = 0; b < sk.GetBoneCount(); b++) meta.Add($"B {b} {sk.GetBoneName(b)}");
        File.WriteAllLines(Path.Combine(dir!, "meta.txt"), meta);
    }

    static int BoneOf(Skeleton3D sk, Skin skin, int bind)
    {
        var n = skin.GetBindName(bind);
        return n != "" ? sk.FindBone(n) : skin.GetBindBone(bind);
    }

    static Vector3 Turned(Vector4 q, Vector3 v)
    {
        var u = new Vector3(q.X, q.Y, q.Z);
        return v + 2f * u.Cross(u.Cross(v) + q.W * v);
    }

    static Vector3[] V3(ShaderMaterial m, string n, int len)
    {
        var v = m.GetShaderParameter(n);
        var a = v.VariantType == Variant.Type.Nil ? [] : v.AsVector3Array();
        return a.Length >= len ? a : new Vector3[len];
    }

    static Vector4[] V4(ShaderMaterial m, string n, int len)
    {
        var v = m.GetShaderParameter(n);
        var a = v.VariantType == Variant.Type.Nil ? [] : v.AsVector4Array();
        if (a.Length >= len) return a;
        var r = new Vector4[len]; for (int i = 0; i < len; i++) r[i] = new Vector4(0, 0, 0, 1); return r;
    }

    static void Dump(People.Person p)
    {
        if (surfs.Count == 0) Setup(p);
        var baked = new Dictionary<MeshInstance3D, ArrayMesh>();
        using var w = new BinaryWriter(File.Create(Path.Combine(dir!, $"k{frame:D2}.bin")));
        w.Write((float)(next - 0.25));
        foreach (var x in surfs)
        {
            if (!baked.TryGetValue(x.Mi, out var bm)) baked[x.Mi] = bm = x.Mi.BakeMeshFromCurrentSkeletonPose();
            var arr = bm.SurfaceGetArrays(x.Surf);
            var P = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
            if (x.Tuck > 0)
            {
                var N = arr[(int)Mesh.ArrayType.Normal].AsVector3Array();
                for (int v = 0; v < P.Length && v < N.Length; v++) P[v] -= N[v] * x.Tuck * x.TuckW[v];
            }
            var g = x.Mi.GlobalTransform;
            if (x.Hair && (x.Mi.GetSurfaceOverrideMaterial(x.Surf) as ShaderMaterial) is { } m)
            {
                var sway = m.GetShaderParameter("sway").AsVector3();
                var head = m.GetShaderParameter("head").AsVector3();
                var chain = V3(m, "chain", 8); var crest = V3(m, "chain_rest", 8); var turn = V4(m, "chain_turn", 8);
                var arms = V3(m, "arms", 4); float armR = m.GetShaderParameter("arm_r").AsSingle();
                if (x.Mi.GetChildren().OfType<HairSway>().FirstOrDefault() is { } hs0 && hs0.ChainWorld.Length == 8 && x.Uv2.Any(u => u.Y > 0))
                {
                    // (a check that the uniforms are read as the shader reads them: rest + chain, in the world, is the chain)
                    float e = 0; for (int i = 0; i < 8; i++) e = Mathf.Max(e, (g * (crest[i] + chain[i])).DistanceTo(hs0.ChainWorld[i]));
                    GD.Print($"HAIRDUMP-CHECK k{frame} s{x.Surf} chain vs uniforms {e * 1000:F2} mm");
                }
                for (int v = 0; v < P.Length; v++)
                {
                    var V = P[v];
                    float hang = Mathf.Clamp((head.Y - V.Y) / 0.35f, 0, 1);
                    float t = Mathf.Clamp(x.Uv[v].Y, 0, 1);
                    float tip = (x.Cap || x.Tie) ? 1f : t * t * (3 - 2 * t);
                    float moves = (x.Cap && x.Cb[v] < 0.5f) ? 0f : 1f;
                    if (x.Uv2[v].Y > 0)
                    {
                        float s = Mathf.Clamp(x.Uv2[v].X, 0, 1) * 7f;
                        int i = Math.Min((int)Mathf.Floor(s), 6);
                        float f = s - i;
                        var o = V - crest[i].Lerp(crest[i + 1], f);
                        var q0 = turn[i]; var q1 = turn[i + 1]; if (q0.Dot(q1) < 0) q1 = -q1;
                        var q = q0.Lerp(q1, f); float ql = q.Length();
                        q = ql > 1e-6f ? q / ql : new Vector4(0, 0, 0, 1);
                        V += (chain[i].Lerp(chain[i + 1], f) + Turned(q, o) - o) * x.Uv2[v].Y;
                    }
                    else V += sway * hang * hang * tip * moves;
                    if (armR > 0 && moves > 0)
                        for (int k = 0; k < 2; k++)
                        {
                            var a = arms[2 * k]; var ab = arms[2 * k + 1] - a;
                            var c = a + ab * Mathf.Clamp((V - a).Dot(ab) / Mathf.Max(ab.Dot(ab), 1e-6f), 0, 1);
                            var o = V - c; float d = o.Length();
                            if (d < armR && d > 1e-5f) V = c + o * (armR / d);
                        }
                    P[v] = V;
                }
            }
            foreach (var v in P) { var q = g * v; w.Write(q.X); w.Write(q.Y); w.Write(q.Z); }
        }
        foreach (var hs in chains) for (int i = 0; i < 8; i++) { var c = hs.ChainWorld[i]; w.Write(c.X); w.Write(c.Y); w.Write(c.Z); }
        frame++;
    }
}
