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
    static readonly bool Check = OS.GetEnvironment("SU_HERO_SN_CHECK") == "1";   // (NORM2: log the new bake against lead 22's diffusion per mesh)
    static readonly string Dump = OS.GetEnvironment("SU_HERO_SN_DUMP");   // (NORM2B: a folder: each mesh's welded input written once, with its bbox / edge / scale logged, for the offline compare)
    static readonly System.Collections.Concurrent.ConcurrentQueue<string> checks = new();
    static int nDump; static double tFirst = -1, tLast; static double msStall; static readonly object tLock = new();
    static readonly Dictionary<ulong, ArrayMesh?> made = new();
    static readonly HashSet<ulong> outs = new();
    static readonly Dictionary<ulong, Task<(ArrayMesh? Copy, float Ms, float CopyMs, int Verts)>> jobs = new();
    static readonly List<MeshInstance3D> hidden = new(); static readonly HashSet<ulong> hiddenIds = new(); static double msHeld;
    /// <summary>(BAKE) A mesh waiting for its bake is not drawn (server visibility only; the node is untouched), so she never shows raw normals.</summary>
    static void Hide(MeshInstance3D mi) { if (hiddenIds.Add(mi.GetInstanceId())) { hidden.Add(mi); RenderingServer.InstanceSetVisible(mi.GetInstance(), false); } }
    static readonly List<MeshInstance3D> waiting = new();
    static readonly List<MeshInstance3D> early = new();   // visited before the radius was set: baked when it is (Step)
    static readonly HashSet<ulong> earlyIds = new();
    static int nCached, nCachedVerts, nStale, nShown;   // (CACHE)
    static readonly bool Verify = OS.GetEnvironment("SU_HERO_SN_VERIFY") == "1";   // (CACHE: each cached or CUSTOM0 mesh baked again on a worker and compared, per vertex)
    /// <summary>(CACHE) The check of a mesh carrying CUSTOM0: its arrays read back, baked the runtime way from them and the
    /// stored CUSTOM0 compared per vertex (max |d| of xyz, the share over 1e-3). Readback cost: only with SU_HERO_SN_VERIFY=1.</summary>
    static void VerifyLater(MeshInstance3D mi, ArrayMesh am)
    {
        if (mi.GetActiveMaterial(0) is not ShaderMaterial { Shader: { } sh } || !ReadsBake(sh)) return;
        string name = mi.Name; bool cached = am.HasMeta(Meta); float r = Radius; int n = am.GetSurfaceCount();
        Task.Run(() =>
        {
            var arr = new Godot.Collections.Array[n];
            for (int s = 0; s < n; s++) arr[s] = am.SurfaceGetArrays(s);
            var P = new Vector3[n][]; var N = new Vector3[n][]; var T = new float[]?[n]; var I = new int[n][];
            for (int s = 0; s < n; s++)
            {
                P[s] = arr[s][(int)Mesh.ArrayType.Vertex].AsVector3Array(); N[s] = arr[s][(int)Mesh.ArrayType.Normal].AsVector3Array();
                T[s] = arr[s][(int)Mesh.ArrayType.Tangent].VariantType == Variant.Type.Nil ? null : arr[s][(int)Mesh.ArrayType.Tangent].AsFloat32Array();
                var iv = arr[s][(int)Mesh.ArrayType.Index];
                I[s] = iv.VariantType == Variant.Type.Nil ? System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Range(0, P[s].Length)) : iv.AsInt32Array();
            }
            var cs = Bake(P, N, T, I, r);
            double dmax = 0; int over = 0, nv = 0;
            for (int s = 0; s < n && cs != null; s++)
            {
                var c0 = arr[s][(int)Mesh.ArrayType.Custom0].AsFloat32Array(); var b = cs[s][0];
                for (int v = 0; v < b.Length / 4; v++, nv++)
                {
                    double d = 0; for (int k = 0; k < 3; k++) d = Math.Max(d, Math.Abs(c0[4 * v + k] - b[4 * v + k]));
                    dmax = Math.Max(dmax, d); if (d > 1e-3) over++;
                }
            }
            checks.Enqueue($"hero normals VERIFY {name} ({(cached ? "cached" : "CUSTOM0, no key")}): {nv} verts, max |d| {dmax:0.000000}, {over} over 1e-3");
        });
    }
    static int nBaked, nLeft, nVerts, nMerged; static float msBake; static readonly System.Diagnostics.Stopwatch wall = new();

    public static void Visit(MeshInstance3D mi)
    {
        if (mi.Mesh is not ArrayMesh am) return;
        if (mi.CastShadow == GeometryInstance3D.ShadowCastingSetting.ShadowsOnly) return;   // (NORM2: a shadow-only mesh shades nothing)
        if (Radius <= 0f) { if (earlyIds.Add(mi.GetInstanceId())) early.Add(mi); return; }
        ulong id = am.GetInstanceId();
        if (outs.Contains(id)) return;
        if (made.TryGetValue(id, out var copy)) { if (copy != null) mi.Mesh = copy; return; }
        if (jobs.ContainsKey(id)) { if (!waiting.Contains(mi)) waiting.Add(mi); Hide(mi); return; }
        var vt = System.Diagnostics.Stopwatch.StartNew();
        // (CACHE, lead 25) an import-time bake (tools_scenes/HeroNormalsImport.cs) whose key's parameters match: nothing to do
        // (no readback, no copy, no hold); a stale one (another radius or bake version) is baked over by the runtime path
        bool stale = false;
        if (am.HasMeta(Meta))
        {
            string key = am.GetMeta(Meta).AsString();
            if (key.EndsWith(" " + Params(Radius)))
            {
                made[id] = null; nCached++; nCachedVerts += am.GetMeta(Meta + "_verts", 0).AsInt32();
                if (Verify) VerifyLater(mi, am);
                msVisit += vt.Elapsed.TotalMilliseconds; Frame(vt.Elapsed.TotalMilliseconds); return;
            }
            stale = true; nStale++;
        }
        int n = am.GetSurfaceCount();
        var arr = new Godot.Collections.Array[n];
        for (int s = 0; s < n; s++)
        {
            if (mi.GetActiveMaterial(s) is ShaderMaterial { Shader: { } sh } && sh.ResourcePath.Contains("heroine_hair")) { made[id] = null; return; }
            if (am.SurfaceGetPrimitiveType(s) != Mesh.PrimitiveType.Triangles) { made[id] = null; return; }
            long fm = (long)am.SurfaceGetFormat(s);   // (BAKE: the format, not the arrays: the read itself is the worker's)
            if ((fm & (long)Mesh.ArrayFormat.FormatCustom0) != 0 && !stale)
            { if (Verify) VerifyLater(mi, am); made[id] = null; nLeft++; GD.Print($"hero normals: {mi.Name} left as is (a CUSTOM0 of its own on surface {s})"); return; }
            if ((fm & (long)Mesh.ArrayFormat.FormatTangent) == 0 && am.GetBlendShapeCount() > 0)
            { made[id] = null; nLeft++; GD.Print($"hero normals: {mi.Name} left as is (blend shapes without tangents on surface {s})"); return; }
        }
        // (BAKE, lead 24) only a mesh whose shader reads the bake: FxAfter's depth-only twins, eyes, teeth, lashes skip
        // (~950 ms of worker on norm2b_01); per instance, so a twin never blocks the source mesh's own bake
        bool reads = false;
        for (int s = 0; s < n && !reads; s++) reads = mi.GetActiveMaterial(s) is ShaderMaterial { Shader: { } sh2 } && ReadsBake(sh2);
        if (!reads) return;
        // (BAKE) the copy's inputs read here (the main thread); the conversion, the bake and the copy itself run on a worker
        int nShapes = am.GetBlendShapeCount(); var shapeNames = new StringName[nShapes];
        for (int k = 0; k < nShapes; k++) shapeNames[k] = am.GetBlendShapeName(k);
        var bsa = new Godot.Collections.Array<Godot.Collections.Array>[n]; var smat = new Material[n]; var snm = new string[n]; var sfm = new long[n];
        for (int s = 0; s < n; s++) { bsa[s] = nShapes > 0 ? am.SurfaceGetBlendShapeArrays(s) : new Godot.Collections.Array<Godot.Collections.Array>(); smat[s] = am.SurfaceGetMaterial(s); snm[s] = am.SurfaceGetName(s); sfm[s] = (long)am.SurfaceGetFormat(s); }
        var mode = am.BlendShapeMode; var aabb = am.CustomAabb; var shadowMesh = am.ShadowMesh; var rname = am.ResourceName;
        float r = Radius;
        if (!wall.IsRunning) wall.Start();
        if (hidden.Count == 0) msHeld = wall.Elapsed.TotalMilliseconds;
        if (mi.Name.ToString().StartsWith("her_merge")) nMerged++;
        string? dumpTo = null;
        if (!string.IsNullOrEmpty(Dump))
        {
            var mats = new List<string>();
            for (int s = 0; s < n; s++) { var m = mi.GetActiveMaterial(s); mats.Add(m == null ? "-" : (m is ShaderMaterial sm2 && sm2.Shader != null ? sm2.Shader.ResourcePath.GetFile() : m.GetClass()) + ":" + m.ResourceName + ":" + am.SurfaceGetName(s)); }
            var sc = mi.GlobalTransform.Basis.Scale;
            dumpTo = System.IO.Path.Combine(Dump, $"m{nDump++:00}_{mi.Name}");
            System.IO.Directory.CreateDirectory(Dump);
            System.IO.File.WriteAllText(dumpTo + ".txt", $"{mi.Name} scale {sc.X:0.####},{sc.Y:0.####},{sc.Z:0.####}\n" + string.Join("\n", mats) + "\n");
        }
        jobs[id] = Task.Run(() =>
        {
            double t0 = wall.Elapsed.TotalMilliseconds;
            for (int s = 0; s < n; s++) arr[s] = am.SurfaceGetArrays(s);   // (BAKE: off the main thread; the server serves it)
            var res = Make(arr, shapeNames, bsa, smat, snm, sfm, mode, aabb, shadowMesh, rname, r, dumpTo);
            lock (tLock) { if (tFirst < 0 || t0 < tFirst) tFirst = t0; tLast = Math.Max(tLast, wall.Elapsed.TotalMilliseconds); }
            return res;
        });
        Hide(mi);
        waiting.Add(mi);
        msVisit += vt.Elapsed.TotalMilliseconds; Frame(vt.Elapsed.TotalMilliseconds);
    }

    // (BAKE) the main thread's ms on the bake, per process frame: the bound is no frame over 8 ms
    /// <summary>(CACHE, lead 25) The bake's version: bump it whenever <see cref="Bake"/> or SmoothNormals changes what it
    /// writes, so every import-time cache goes stale and the runtime bake takes over until the next import.</summary>
    public const int Version = 1;
    /// <summary>(CACHE) The key's parameter part: the version, the radius and the smoothing's constants.</summary>
    public static string Params(float radius) => $"v{Version} r{radius:R} tiny{SurvivorUnchained.Look.SmoothNormals.TinyPart:R} brute{SurvivorUnchained.Look.SmoothNormals.BruteMax}";
    /// <summary>(CACHE) The mesh meta an import-time bake leaves: "hash params" (hash = the source vertex and index data).</summary>
    public const string Meta = "hero_sn";
    /// <summary>(CACHE) FNV-1a 64 over every surface's positions, normals, tangents and indices (the bake's whole input).</summary>
    public static ulong Hash(Godot.Collections.Array[] arr)
    {
        ulong h = 14695981039346656037UL;
        void F(ReadOnlySpan<byte> b) { foreach (var x in b) { h ^= x; h *= 1099511628211UL; } }
        foreach (var a in arr)
        {
            F(System.Runtime.InteropServices.MemoryMarshal.AsBytes<Vector3>(a[(int)Mesh.ArrayType.Vertex].AsVector3Array()));
            F(System.Runtime.InteropServices.MemoryMarshal.AsBytes<Vector3>(a[(int)Mesh.ArrayType.Normal].AsVector3Array()));
            if (a[(int)Mesh.ArrayType.Tangent].VariantType != Variant.Type.Nil) F(System.Runtime.InteropServices.MemoryMarshal.AsBytes<float>(a[(int)Mesh.ArrayType.Tangent].AsFloat32Array()));
            if (a[(int)Mesh.ArrayType.Index].VariantType != Variant.Type.Nil) F(System.Runtime.InteropServices.MemoryMarshal.AsBytes<int>(a[(int)Mesh.ArrayType.Index].AsInt32Array()));
        }
        return h;
    }
    /// <summary>(CACHE) The import tool's call: the baked copy of a whole mesh (its arrays read here), with the key as meta;
    /// null when the runtime would not bake it either (not triangles, a CUSTOM0 of its own, blend shapes without tangents).</summary>
    public static ArrayMesh? BakeMesh(ArrayMesh am, float radius, out int verts)
    {
        verts = 0;
        int n = am.GetSurfaceCount(); if (n == 0) return null;
        for (int s = 0; s < n; s++)
        {
            if (am.SurfaceGetPrimitiveType(s) != Mesh.PrimitiveType.Triangles) return null;
            long fm = (long)am.SurfaceGetFormat(s);
            if ((fm & (long)Mesh.ArrayFormat.FormatCustom0) != 0) return null;
            if ((fm & (long)Mesh.ArrayFormat.FormatTangent) == 0 && am.GetBlendShapeCount() > 0) return null;
        }
        int nShapes = am.GetBlendShapeCount(); var shapeNames = new StringName[nShapes];
        for (int k = 0; k < nShapes; k++) shapeNames[k] = am.GetBlendShapeName(k);
        var arr = new Godot.Collections.Array[n]; var bsa = new Godot.Collections.Array<Godot.Collections.Array>[n]; var smat = new Material[n]; var snm = new string[n]; var sfm = new long[n];
        for (int s = 0; s < n; s++) { arr[s] = am.SurfaceGetArrays(s); bsa[s] = nShapes > 0 ? am.SurfaceGetBlendShapeArrays(s) : new Godot.Collections.Array<Godot.Collections.Array>(); smat[s] = am.SurfaceGetMaterial(s); snm[s] = am.SurfaceGetName(s); sfm[s] = (long)am.SurfaceGetFormat(s); }
        ulong h = Hash(arr);
        var res = Make(arr, shapeNames, bsa, smat, snm, sfm, am.BlendShapeMode, am.CustomAabb, am.ShadowMesh, am.ResourceName, radius, null);
        if (res.Copy == null) return null;
        res.Copy.SetMeta(Meta, $"{h:x16} {Params(radius)}"); res.Copy.SetMeta(Meta + "_verts", res.Verts);
        verts = res.Verts; return res.Copy;
    }

    /// <summary>The arrays' conversion, the bake and the copy (the source's surfaces, blend shapes, materials, names plus
    /// CUSTOM0); no Godot server calls but the copy's upload. The runtime worker and the import tool both run it.</summary>
    static (ArrayMesh? Copy, float Ms, float CopyMs, int Verts) Make(Godot.Collections.Array[] arr, StringName[] shapeNames, Godot.Collections.Array<Godot.Collections.Array>[] bsa,
        Material[] smat, string[] snm, long[] sfm, Mesh.BlendShapeMode mode, Aabb aabb, ArrayMesh? shadowMesh, string rname, float r, string? dumpTo)
    {
        int n = arr.Length;
        var P = new Vector3[n][]; var N = new Vector3[n][]; var T = new float[]?[n]; var I = new int[n][];
        for (int s = 0; s < n; s++)
        {
            P[s] = arr[s][(int)Mesh.ArrayType.Vertex].AsVector3Array();
            N[s] = arr[s][(int)Mesh.ArrayType.Normal].AsVector3Array();
            T[s] = arr[s][(int)Mesh.ArrayType.Tangent].VariantType == Variant.Type.Nil ? null! : arr[s][(int)Mesh.ArrayType.Tangent].AsFloat32Array();
            var iv = arr[s][(int)Mesh.ArrayType.Index];
            I[s] = iv.VariantType == Variant.Type.Nil ? System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Range(0, P[s].Length)) : iv.AsInt32Array();
        }
        var sw = System.Diagnostics.Stopwatch.StartNew(); var cs = Bake(P, N, T, I, r, dumpTo); float ms = (float)sw.Elapsed.TotalMilliseconds;
        ArrayMesh? copy = null; float cms = 0; int verts = 0;
        if (cs != null)
        {
            var ct = System.Diagnostics.Stopwatch.StartNew();
            copy = new ArrayMesh { BlendShapeMode = mode, CustomAabb = aabb, ShadowMesh = shadowMesh, ResourceName = rname };
            foreach (var sn in shapeNames) copy.AddBlendShape(sn);
            for (int s = 0; s < n; s++)
            {
                arr[s][(int)Mesh.ArrayType.Custom0] = cs[s][0];
                if (cs[s][1] is { } ft) arr[s][(int)Mesh.ArrayType.Tangent] = ft;   // (a mesh without tangents: the frame's own fallback)
                verts += cs[s][0].Length / 4;
                long keep = sfm[s] & ((long)Mesh.ArrayFormat.FlagUse8BoneWeights | (0xFFFL << (int)Mesh.ArrayFormat.FormatCustom0Shift));
                keep &= ~((long)Mesh.ArrayFormat.FormatCustomMask << (int)Mesh.ArrayFormat.FormatCustom0Shift);
                keep |= (long)Mesh.ArrayCustomFormat.RgbaFloat << (int)Mesh.ArrayFormat.FormatCustom0Shift;
                copy.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr[s], bsa[s], null, (Mesh.ArrayFormat)keep);
                copy.SurfaceSetMaterial(s, smat[s]);
                copy.SurfaceSetName(s, snm[s]);
            }
            cms = (float)ct.Elapsed.TotalMilliseconds;
        }
        return (copy, ms, cms, verts);
    }

    static ulong lastTick; static double gapMax;   // (BAKE: the longest real frame interval while a bake is pending, every cost on the main thread included)
    static double msVisit, msCopy, msFrameNow, msFrameMax; static ulong frameNow;
    static void Frame(double ms)
    {
        ulong f = Engine.GetProcessFrames();
        if (f != frameNow) { frameNow = f; msFrameNow = 0; }
        msFrameNow += ms; msFrameMax = Math.Max(msFrameMax, msFrameNow);
    }

    static readonly Dictionary<ulong, bool> readsBake = new();
    static readonly System.Text.RegularExpressions.Regex Inc = new(@"#include\s+""([^""]+)""");

    /// <summary>(BAKE) Does this shader (its includes followed) run CEL_HERO_VERTEX, the one reader of the bake's CUSTOM0?</summary>
    public static bool ReadsBake(Shader sh)
    {
        ulong id = sh.GetInstanceId();
        if (readsBake.TryGetValue(id, out bool r)) return r;
        r = UsesIn(sh.Code, 0);
        readsBake[id] = r; return r;
    }
    static bool UsesIn(string code, int depth)
    {
        if (string.IsNullOrEmpty(code) || depth > 8) return false;
        if (SurvivorUnchained.Look.SmoothNormals.RunsBake(code)) return true;
        foreach (System.Text.RegularExpressions.Match m in Inc.Matches(code))
            if (ResourceLoader.Exists(m.Groups[1].Value) && GD.Load<ShaderInclude>(m.Groups[1].Value) is { } si && UsesIn(si.Code, depth + 1)) return true;
        return false;
    }

    /// <summary>Each frame (CelLib): a finished bake becomes the copy, worn by every mesh that waited for it.</summary>
    public static void Step()
    {
        if (Radius > 0f && early.Count > 0)
        {
            var e = new List<MeshInstance3D>(early); early.Clear(); earlyIds.Clear();
            foreach (var mi in e) if (GodotObject.IsInstanceValid(mi)) Visit(mi);
        }
        while (checks.TryDequeue(out var cl0)) GD.Print(cl0);
        if (nCached + nLeft != nShown)
        {
            nShown = nCached + nLeft;
            GD.Print($"hero normals: {nCached} meshes from the import-time cache ({nCachedVerts} verts), {nStale} stale (baked at runtime), {nLeft} left as is (a CUSTOM0 of their own, merges of cached meshes included); main thread: {msVisit:0.0} ms in Visit, worst frame {msFrameMax:0.0} ms on the bake; radius {Radius:0.###} m");
        }
        if (jobs.Count == 0) return;
        ulong now = Time.GetTicksUsec(); if (lastTick != 0 && hidden.Count > 0) gapMax = Math.Max(gapMax, (now - lastTick) / 1000.0); lastTick = now;
        // (BAKE) never wait: a finished job's copy is worn; its meshes stay hidden until every pending bake is in
        var st = System.Diagnostics.Stopwatch.StartNew();
        int done = 0;
        foreach (var id in new List<ulong>(jobs.Keys))
        {
            var job = jobs[id];
            if (!job.IsCompleted) continue;
            jobs.Remove(id); done++;
            ArrayMesh? copy = null;
            if (job.Status != TaskStatus.RanToCompletion) GD.PushError($"hero normals: a bake failed: {job.Exception?.GetBaseException().Message}");
            else if (job.Result.Copy is { } c) { copy = c; msBake += job.Result.Ms; msCopy += job.Result.CopyMs; nVerts += job.Result.Verts; outs.Add(c.GetInstanceId()); nBaked++; }
            made[id] = copy;
        }
        msStall += st.Elapsed.TotalMilliseconds; Frame(st.Elapsed.TotalMilliseconds);
        while (checks.TryDequeue(out var cl)) GD.Print(cl);
        if (done > 0)
            GD.Print($"hero normals: {nBaked} meshes baked ({nMerged} of them her_merge), {nVerts} verts, {msBake:0} ms of bake on workers, {tLast - tFirst:0} ms bake wall (first start to last end), {msStall:0} ms main-thread stall in Step, {wall.Elapsed.TotalMilliseconds:0} ms since the first visit; main thread: {msVisit:0} ms reading arrays in Visit, {msCopy:0} ms building copies, worst frame {msFrameMax:0.0} ms on the bake, longest frame interval while pending {gapMax:0.0} ms; {nLeft} left as is, {jobs.Count} still baking, {early.Count} waiting for the radius; radius {Radius:0.###} m");
        for (int i = waiting.Count - 1; i >= 0; i--)
        {
            var mi = waiting[i];
            if (!GodotObject.IsInstanceValid(mi) || mi.Mesh is not ArrayMesh am) { waiting.RemoveAt(i); continue; }
            if (made.TryGetValue(am.GetInstanceId(), out var c)) { if (c != null) mi.Mesh = c; waiting.RemoveAt(i); }
        }
        if (jobs.Count == 0 && hidden.Count > 0)
        {
            foreach (var mi in hidden) if (GodotObject.IsInstanceValid(mi)) RenderingServer.InstanceSetVisible(mi.GetInstance(), mi.IsVisibleInTree());
            GD.Print($"hero normals: {hidden.Count} meshes shown, held {wall.Elapsed.TotalMilliseconds - msHeld:0} ms after their first visit");
            hidden.Clear(); hiddenIds.Clear(); lastTick = 0;
        }
    }

    /// <summary>The smoothed normal per vertex as CUSTOM0 (frame xyz, w 1), every surface; no Godot calls (a worker).</summary>
    static float[][][]? Bake(Vector3[][] P, Vector3[][] N, float[]?[] T, int[][] I, float radius, string? dumpTo = null)
    {
        // (NORM2) the smoothed normal: SmoothNormals' Gaussian (sigma = the radius) over the mesh's surfaces as one
        int nv = 0; foreach (var ps in P) nv += ps.Length;
        var fp = new float[nv * 3]; var fn = new float[nv * 3]; var ti = new List<int>(); int at = 0;
        var baseOf = new int[P.Length];
        for (int s = 0; s < P.Length; s++)
        {
            baseOf[s] = at;
            for (int v = 0; v < P[s].Length; v++, at++) { fp[3 * at] = P[s][v].X; fp[3 * at + 1] = P[s][v].Y; fp[3 * at + 2] = P[s][v].Z; fn[3 * at] = N[s][v].X; fn[3 * at + 1] = N[s][v].Y; fn[3 * at + 2] = N[s][v].Z; }
            foreach (int i in I[s]) ti.Add(baseOf[s] + i);
        }
        if (nv == 0) return null;
        if (dumpTo != null)
        {
            using (var bw = new System.IO.BinaryWriter(System.IO.File.Create(dumpTo + ".bin")))
            {
                bw.Write(nv); bw.Write(ti.Count); bw.Write(P.Length);
                foreach (var b in baseOf) bw.Write(b);
                foreach (var f in fp) bw.Write(f);
                foreach (var f in fn) bw.Write(f);
                foreach (var i in ti) bw.Write(i);
            }
        }
        var sm = Check ? SurvivorUnchained.Look.SmoothNormals.Diffuse(fp, fn, ti.ToArray(), radius) : null;
        var sw = System.Diagnostics.Stopwatch.StartNew();
        var fs = SurvivorUnchained.Look.SmoothNormals.Smooth(fp, fn, ti.ToArray(), radius);
        float smMs = (float)sw.Elapsed.TotalMilliseconds;
        if (sm != null) { var d = SurvivorUnchained.Look.SmoothNormals.AnglesDeg(fs, sm); checks.Enqueue($"hero normals CHECK vs the old diffusion: {nv} verts, new bake {smMs:0} ms, median {d[d.Length / 2]:0.0} p90 {d[(int)(d.Length * 0.9)]:0.0} deg"); }
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
                int fv = 3 * (baseOf[s] + v); var sn = new Vector3(fs[fv], fs[fv + 1], fs[fv + 2]);
                o[4 * v] = sn.Dot(tt); o[4 * v + 1] = sn.Dot(bb); o[4 * v + 2] = sn.Dot(nn); o[4 * v + 3] = 1f;
            }
        }
        return outv;
    }
}
