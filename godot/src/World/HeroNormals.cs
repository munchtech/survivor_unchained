using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>(L1 lead 22, P1NORM) SMOOTH SHADING NORMALS for any hero-scale figure: the cel steps of a hero material
/// (cel.gdshaderinc CEL_HERO_VERTEX) read a normal diffused over the figure's welded surface, so at the play camera the
/// lit / mid / terminator steps turn its forms (limbs, breasts, belly, thighs) instead of tracing the mesh's bumps.
/// At load, per mesh under her (CelLib.Hero), once per source mesh and shared by every holder: positions welded at
/// 0.1 mm, the mesh's own normals averaged there, then diffused over the edge graph (self + neighbours, renormalized)
/// for K = 2 (radius / mean edge)^2 passes (hero_pool value 60, m), stored in CUSTOM0 as xyz in the vertex's own
/// frame (tangent made square to the normal, cross(normal, it), normal; w 1) so the skinning's frame carries it. The
/// copy is the source's surfaces, blend shapes, materials and names plus CUSTOM0; no source data or texture changes.
/// Hair (heroine_hair) and meshes with a CUSTOM0 of their own are left as they are; a mesh without tangents gets the
/// frame's own fallback tangent (the one CEL_HERO_VERTEX builds) in its copy. A mesh visited before the rig set the radius
/// waits and is baked as soon as it is set (Step), so the order of the rig and the hero's load never matters.
/// Radius 0 (a row without value 60): nothing is baked. When the bakes drain the log says how many meshes, verts, ms.</summary>
public static class HeroNormals
{
    public static float Radius;
    static readonly Dictionary<ulong, ArrayMesh?> made = new();
    static readonly HashSet<ulong> outs = new();
    static readonly Dictionary<ulong, (ArrayMesh Src, Godot.Collections.Array[] Arr, Task<(float[][][]? Out, float Ms)> Job)> jobs = new();
    static readonly List<MeshInstance3D> waiting = new();
    static readonly List<MeshInstance3D> early = new();   // visited before the radius was set: baked when it is (Step)
    static readonly HashSet<ulong> earlyIds = new();
    static int nBaked, nLeft, nVerts, nMerged; static float msBake; static readonly System.Diagnostics.Stopwatch wall = new();

    public static void Visit(MeshInstance3D mi)
    {
        if (mi.Mesh is not ArrayMesh am) return;
        if (Radius <= 0f) { if (earlyIds.Add(mi.GetInstanceId())) early.Add(mi); return; }
        ulong id = am.GetInstanceId();
        if (outs.Contains(id)) return;
        if (made.TryGetValue(id, out var copy)) { if (copy != null) mi.Mesh = copy; return; }
        if (jobs.ContainsKey(id)) { if (!waiting.Contains(mi)) waiting.Add(mi); return; }
        int n = am.GetSurfaceCount();
        var arr = new Godot.Collections.Array[n];
        for (int s = 0; s < n; s++)
        {
            if (mi.GetActiveMaterial(s) is ShaderMaterial { Shader: { } sh } && sh.ResourcePath.Contains("heroine_hair")) { made[id] = null; return; }
            if (am.SurfaceGetPrimitiveType(s) != Mesh.PrimitiveType.Triangles) { made[id] = null; return; }
            arr[s] = am.SurfaceGetArrays(s);
            if (arr[s][(int)Mesh.ArrayType.Custom0].VariantType != Variant.Type.Nil)
            { made[id] = null; nLeft++; GD.Print($"hero normals: {mi.Name} left as is (a CUSTOM0 of its own on surface {s})"); return; }
            if (arr[s][(int)Mesh.ArrayType.Tangent].VariantType == Variant.Type.Nil && am.GetBlendShapeCount() > 0)
            { made[id] = null; nLeft++; GD.Print($"hero normals: {mi.Name} left as is (blend shapes without tangents on surface {s})"); return; }
        }
        var P = new Vector3[n][]; var N = new Vector3[n][]; var T = new float[]?[n]; var I = new int[n][];
        for (int s = 0; s < n; s++)
        {
            P[s] = arr[s][(int)Mesh.ArrayType.Vertex].AsVector3Array();
            N[s] = arr[s][(int)Mesh.ArrayType.Normal].AsVector3Array();
            T[s] = arr[s][(int)Mesh.ArrayType.Tangent].VariantType == Variant.Type.Nil ? null! : arr[s][(int)Mesh.ArrayType.Tangent].AsFloat32Array();
            var iv = arr[s][(int)Mesh.ArrayType.Index];
            I[s] = iv.VariantType == Variant.Type.Nil ? System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Range(0, P[s].Length)) : iv.AsInt32Array();
        }
        float r = Radius;
        if (!wall.IsRunning) wall.Start();
        if (mi.Name.ToString().StartsWith("her_merge")) nMerged++;
        jobs[id] = (am, arr, Task.Run(() => { var sw = System.Diagnostics.Stopwatch.StartNew(); var o = Bake(P, N, T, I, r); return (o, (float)sw.Elapsed.TotalMilliseconds); }));
        waiting.Add(mi);
    }

    /// <summary>Each frame (CelLib): a finished bake becomes the copy, worn by every mesh that waited for it.</summary>
    public static void Step()
    {
        if (Radius > 0f && early.Count > 0)
        {
            var e = new List<MeshInstance3D>(early); early.Clear(); earlyIds.Clear();
            foreach (var mi in e) if (GodotObject.IsInstanceValid(mi)) Visit(mi);
        }
        if (jobs.Count == 0) return;
        int done = 0;
        foreach (var id in new List<ulong>(jobs.Keys))
        {
            var (src, arr, job) = jobs[id];
            if (!job.IsCompleted) continue;
            jobs.Remove(id); done++;
            ArrayMesh? copy = null;
            if (job.Status != TaskStatus.RanToCompletion) GD.PushError($"hero normals: {src.ResourceName} bake failed: {job.Exception?.GetBaseException().Message}");
            if (job.Status == TaskStatus.RanToCompletion && job.Result.Out is { } cs && GodotObject.IsInstanceValid(src))
            {
                msBake += job.Result.Ms;
                copy = new ArrayMesh { BlendShapeMode = src.BlendShapeMode, CustomAabb = src.CustomAabb, ShadowMesh = src.ShadowMesh, ResourceName = src.ResourceName };
                bool shapes = src.GetBlendShapeCount() > 0;
                if (shapes) for (int k = 0; k < src.GetBlendShapeCount(); k++) copy.AddBlendShape(src.GetBlendShapeName(k));
                for (int s = 0; s < arr.Length; s++)
                {
                    arr[s][(int)Mesh.ArrayType.Custom0] = cs[s][0];
                    if (cs[s][1] is { } ft) arr[s][(int)Mesh.ArrayType.Tangent] = ft;   // (a mesh without tangents: the frame's own fallback)
                    nVerts += cs[s][0].Length / 4;
                    long keep = (long)src.SurfaceGetFormat(s) & ((long)Mesh.ArrayFormat.FlagUse8BoneWeights | (0xFFFL << (int)Mesh.ArrayFormat.FormatCustom0Shift));
                    keep &= ~((long)Mesh.ArrayFormat.FormatCustomMask << (int)Mesh.ArrayFormat.FormatCustom0Shift);
                    keep |= (long)Mesh.ArrayCustomFormat.RgbaFloat << (int)Mesh.ArrayFormat.FormatCustom0Shift;
                    copy.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr[s], shapes ? src.SurfaceGetBlendShapeArrays(s) : new Godot.Collections.Array<Godot.Collections.Array>(), null, (Mesh.ArrayFormat)keep);
                    copy.SurfaceSetMaterial(s, src.SurfaceGetMaterial(s));
                    copy.SurfaceSetName(s, src.SurfaceGetName(s));
                }
                outs.Add(copy.GetInstanceId());
                nBaked++;
            }
            made[id] = copy;
        }
        if (done > 0)
            GD.Print($"hero normals: {nBaked} meshes baked ({nMerged} of them her_merge), {nVerts} verts, {msBake:0} ms of bake on workers, {wall.Elapsed.TotalMilliseconds:0} ms wall; {nLeft} left as is, {jobs.Count} still baking, {early.Count} waiting for the radius; radius {Radius:0.###} m");
        for (int i = waiting.Count - 1; i >= 0; i--)
        {
            var mi = waiting[i];
            if (!GodotObject.IsInstanceValid(mi) || mi.Mesh is not ArrayMesh am) { waiting.RemoveAt(i); continue; }
            if (made.TryGetValue(am.GetInstanceId(), out var c)) { if (c != null) mi.Mesh = c; waiting.RemoveAt(i); }
        }
    }

    /// <summary>The smoothed normal per vertex as CUSTOM0 (frame xyz, w 1), every surface; no Godot calls (a worker).</summary>
    static float[][][]? Bake(Vector3[][] P, Vector3[][] N, float[]?[] T, int[][] I, float radius)
    {
        var weld = new Dictionary<(long, long, long), int>();
        var wid = new int[P.Length][];
        var sum = new List<Vector3>();
        for (int s = 0; s < P.Length; s++)
        {
            wid[s] = new int[P[s].Length];
            for (int v = 0; v < P[s].Length; v++)
            {
                var p = P[s][v];
                var k = ((long)MathF.Round(p.X * 1e4f), (long)MathF.Round(p.Y * 1e4f), (long)MathF.Round(p.Z * 1e4f));
                if (!weld.TryGetValue(k, out int w)) { weld[k] = w = sum.Count; sum.Add(Vector3.Zero); }
                wid[s][v] = w;
                sum[w] += N[s][v];
            }
        }
        int W = sum.Count;
        if (W == 0) return null;
        var edges = new HashSet<long>();
        double el = 0; long ec = 0;
        var pos = new Vector3[W];
        for (int s = 0; s < P.Length; s++) for (int v = 0; v < P[s].Length; v++) pos[wid[s][v]] = P[s][v];
        for (int s = 0; s < P.Length; s++)
            for (int t = 0; t + 2 < I[s].Length; t += 3)
                for (int e = 0; e < 3; e++)
                {
                    int a = wid[s][I[s][t + e]], b = wid[s][I[s][t + (e + 1) % 3]];
                    if (a == b) continue;
                    if (edges.Add(((long)Math.Min(a, b) << 32) | (uint)Math.Max(a, b))) { el += pos[a].DistanceTo(pos[b]); ec++; }
                }
        var deg = new int[W + 1];
        foreach (var e in edges) { deg[(int)(e >> 32) + 1]++; deg[(int)(e & 0xFFFFFFFF) + 1]++; }
        for (int i = 0; i < W; i++) deg[i + 1] += deg[i];
        var adj = new int[deg[W]]; var fill = (int[])deg.Clone();
        foreach (var e in edges) { int a = (int)(e >> 32), b = (int)(e & 0xFFFFFFFF); adj[fill[a]++] = b; adj[fill[b]++] = a; }
        var n0 = new Vector3[W]; var n1 = new Vector3[W];
        for (int i = 0; i < W; i++) n0[i] = sum[i].LengthSquared() > 1e-12f ? sum[i].Normalized() : Vector3.Up;
        float mean = ec > 0 ? (float)(el / ec) : 0.01f;
        int K = Math.Clamp((int)MathF.Round(2f * (radius / Math.Max(mean, 1e-4f)) * (radius / Math.Max(mean, 1e-4f))), 1, 400);
        for (int it = 0; it < K; it++)
        {
            for (int i = 0; i < W; i++)
            {
                var a = n0[i];
                for (int j = deg[i]; j < deg[i + 1]; j++) a += n0[adj[j]];
                n1[i] = a.LengthSquared() > 1e-12f ? a.Normalized() : n0[i];
            }
            (n0, n1) = (n1, n0);
        }
        var outv = new float[P.Length][][];
        for (int s = 0; s < P.Length; s++)
        {
            var o = new float[P[s].Length * 4];
            var ts = T[s];
            var ft = ts == null ? new float[P[s].Length * 4] : null;
            outv[s] = new[] { o, ft! };
            for (int v = 0; v < P[s].Length; v++)
            {
                var nn = N[s][v].Normalized();
                var tt = ts == null ? Vector3.Zero : new Vector3(ts[4 * v], ts[4 * v + 1], ts[4 * v + 2]);
                tt -= nn * nn.Dot(tt);
                tt = tt.LengthSquared() > 1e-8f ? tt.Normalized() : nn.Cross(MathF.Abs(nn.Y) < 0.99f ? Vector3.Up : Vector3.Right).Normalized();
                if (ft != null) { ft[4 * v] = tt.X; ft[4 * v + 1] = tt.Y; ft[4 * v + 2] = tt.Z; ft[4 * v + 3] = 1f; }
                var bb = nn.Cross(tt);
                var sn = n0[wid[s][v]];
                o[4 * v] = sn.Dot(tt); o[4 * v + 1] = sn.Dot(bb); o[4 * v + 2] = sn.Dot(nn); o[4 * v + 3] = 1f;
            }
        }
        return outv;
    }
}
