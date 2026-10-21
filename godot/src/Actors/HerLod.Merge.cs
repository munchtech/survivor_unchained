using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Her play draws (docs/handoff/armor.md section 00, look bible page 11: about 20): at equip time what draws of her
/// outfit at the play camera (each piece's gameplay meshes where it has them, else its full meshes) is merged into one
/// skinned mesh a material (one surface each, on her skeleton with one Skin of the pieces' binds), and what casts
/// her outfit's shadow there into one shadow mesh. The merged meshes switch with the gameplay model and wear the first
/// full mesh's materials each frame, as a gameplay mesh does. Her full meshes stay as they are (they draw near the
/// camera: the tuck map, her jiggle and fur all on them as before). Left unmerged, as their own draws: fur, sheer and
/// any multi-pass surface, meshes with a blend shape not at rest, and meshes off her skeleton's frame.
/// --merge off: none (to compare).
/// </summary>
public partial class HerLod
{
    static readonly bool MergeOff = Args.Get("merge") == "off";
    static readonly string[] Arrays = { "uv", "uv2", "color", "tangent" };

    /// <summary>A material's look as a key: its shader and every uniform's value (textures by instance): two surfaces
    /// with one key draw the same.</summary>
    static string? MatKey(Material? m)
    {
        if (m is not ShaderMaterial sm || sm.Shader == null || sm.NextPass != null) return null;
        var sb = new System.Text.StringBuilder().Append(sm.Shader.GetInstanceId()).Append(sm.RenderPriority);
        foreach (var u in sm.Shader.GetShaderUniformList())
        {
            var name = (string)u.AsGodotDictionary()["name"];
            var v = sm.GetShaderParameter(name);
            sb.Append('|').Append(name).Append('=').Append(v.VariantType == Variant.Type.Object ? v.AsGodotObject()?.GetInstanceId().ToString() ?? "" : v.ToString());
        }
        return sb.ToString();
    }

    /// <summary>Which arrays a surface has and its weights a vertex (surfaces merge only with their like).</summary>
    static string? Sig(Mesh mesh, int s, out Godot.Collections.Array arr)
    {
        arr = mesh.SurfaceGetArrays(s);
        if (mesh is not ArrayMesh am || am.SurfaceGetPrimitiveType(s) != Mesh.PrimitiveType.Triangles) return null;
        int n = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array().Length;
        if (n == 0 || arr[(int)Mesh.ArrayType.Normal].VariantType == Variant.Type.Nil || arr[(int)Mesh.ArrayType.Bones].VariantType == Variant.Type.Nil) return null;
        int per = arr[(int)Mesh.ArrayType.Bones].AsInt32Array().Length / n;
        var t = new[] { Mesh.ArrayType.TexUV, Mesh.ArrayType.TexUV2, Mesh.ArrayType.Color, Mesh.ArrayType.Tangent };
        var got = arr;
        var sig = $"w{per}" + string.Concat(t.Select((a, i) => got[(int)a].VariantType == Variant.Type.Nil ? "" : Arrays[i]));
        // (a custom array, by its format: TEXCOORD_2 and on come in as CUSTOM0..3)
        long fmt = (long)am.SurfaceGetFormat(s);
        for (int c = 0; c < 4; c++)
            if (arr[(int)Mesh.ArrayType.Custom0 + c].VariantType != Variant.Type.Nil)
                sig += $"c{c}:{(fmt >> ((int)Mesh.ArrayFormat.FormatCustom0Shift + c * (int)Mesh.ArrayFormat.FormatCustomBits)) & (long)Mesh.ArrayFormat.FormatCustomMask}";
        return sig;
    }

    sealed class Part { public required MeshInstance3D Full, Src; public required int Surface, FullSurface; public required Godot.Collections.Array Arr; }

    /// <summary>Its blend shapes, if any, all at rest (the warden's bracers' elbow points: nothing drives them), so its
    /// base vertices are what it draws.</summary>
    static bool AtRest(MeshInstance3D mi) =>
        mi.Mesh is ArrayMesh am && Enumerable.Range(0, am.GetBlendShapeCount()).All(i => mi.GetBlendShapeValue(i) == 0);

    /// <summary>One source surface's arrays as plain C# arrays (taken on the main thread), for the join on a worker.</summary>
    sealed class Ps
    {
        public Vector3[] V = null!, N = null!; public float[]? Tan; public Color[]? Col; public Vector2[]? Uv, Uv2;
        public float[]?[] Cf = new float[]?[4]; public byte[]?[] Cb = new byte[]?[4];
        public int[] Bones = null!; public float[] W = null!; public int[]? Ix; public int[] Map = null!;
    }

    /// <summary>The joined arrays (null: none of that array).</summary>
    sealed class Joined
    {
        public Vector3[] V = null!, N = null!; public float[]? Tan; public Color[]? Col; public Vector2[]? Uv, Uv2;
        public float[]?[] Cf = new float[]?[4]; public byte[]?[] Cb = new byte[]?[4];
        public int[] Bones = null!; public float[] W = null!; public int[] Ix = null!;
    }

    static T[]? Cat<T>(Ps[] src, System.Func<Ps, T[]?> get)
    {
        int n = 0;
        foreach (var p in src) n += get(p)?.Length ?? 0;
        if (n == 0) return null;
        var o = new T[n]; int at = 0;
        foreach (var p in src) { var a = get(p); if (a == null) continue; System.Array.Copy(a, 0, o, at, a.Length); at += a.Length; }
        return o;
    }

    /// <summary>The surfaces' arrays end to end (no Godot calls: runs on a worker). Bone indices remapped through each
    /// source's map, indices offset by the vertices before (a surface with none: its vertices in order).</summary>
    static Joined Join(Ps[] src, bool shadow)
    {
        var j = new Joined { V = Cat(src, p => p.V)!, N = Cat(src, p => p.N)!, W = Cat(src, p => p.W)! };
        if (!shadow)
        {
            j.Tan = Cat(src, p => p.Tan); j.Col = Cat(src, p => p.Col); j.Uv = Cat(src, p => p.Uv); j.Uv2 = Cat(src, p => p.Uv2);
            for (int c = 0; c < 4; c++) { int cc = c; j.Cf[c] = Cat(src, p => p.Cf[cc]); j.Cb[c] = Cat(src, p => p.Cb[cc]); }
        }
        int nb = 0, ni = 0;
        foreach (var p in src) { nb += p.Bones.Length; ni += p.Ix?.Length ?? p.V.Length; }
        j.Bones = new int[nb]; j.Ix = new int[ni];
        int ab = 0, ai = 0, baseV = 0;
        foreach (var p in src)
        {
            var map = p.Map; var bs = p.Bones;
            for (int i = 0; i < bs.Length; i++) j.Bones[ab + i] = map[bs[i]];
            ab += bs.Length;
            if (p.Ix != null) { var ix = p.Ix; for (int i = 0; i < ix.Length; i++) j.Ix[ai + i] = ix[i] + baseV; ai += ix.Length; }
            else { int n = p.V.Length; for (int i = 0; i < n; i++) j.Ix[ai + i] = baseV + i; ai += n; }
            baseV += p.V.Length;
        }
        return j;
    }

    /// <summary>On the main thread: the binds of these sources into one skin's list (a bind shared when its bone and
    /// pose are the same) and each source's arrays as plain arrays.</summary>
    Ps[] Take(List<(Godot.Collections.Array Arr, Skin Skin)> src, List<(string Bone, Transform3D Pose)> binds, bool shadow)
    {
        var o = new Ps[src.Count];
        for (int i = 0; i < o.Length; i++)
        {
            var (a, sk) = src[i];
            var map = new int[sk.GetBindCount()];
            for (int b = 0; b < map.Length; b++)
            {
                string bone = sk.GetBindName(b).ToString();
                if (bone.Length == 0) bone = skel.GetBoneName(sk.GetBindBone(b));
                var pose = sk.GetBindPose(b);
                int at = binds.FindIndex(x => x.Bone == bone && x.Pose.IsEqualApprox(pose));
                if (at < 0) { at = binds.Count; binds.Add((bone, pose)); }
                map[b] = at;
            }
            var p = new Ps { Map = map, V = a[(int)Mesh.ArrayType.Vertex].AsVector3Array(), N = a[(int)Mesh.ArrayType.Normal].AsVector3Array(),
                Bones = a[(int)Mesh.ArrayType.Bones].AsInt32Array(), W = a[(int)Mesh.ArrayType.Weights].AsFloat32Array() };
            if (a[(int)Mesh.ArrayType.Index].VariantType != Variant.Type.Nil) p.Ix = a[(int)Mesh.ArrayType.Index].AsInt32Array();
            if (!shadow)
            {
                if (a[(int)Mesh.ArrayType.Tangent].VariantType != Variant.Type.Nil) p.Tan = a[(int)Mesh.ArrayType.Tangent].AsFloat32Array();
                if (a[(int)Mesh.ArrayType.Color].VariantType != Variant.Type.Nil) p.Col = a[(int)Mesh.ArrayType.Color].AsColorArray();
                if (a[(int)Mesh.ArrayType.TexUV].VariantType != Variant.Type.Nil) p.Uv = a[(int)Mesh.ArrayType.TexUV].AsVector2Array();
                if (a[(int)Mesh.ArrayType.TexUV2].VariantType != Variant.Type.Nil) p.Uv2 = a[(int)Mesh.ArrayType.TexUV2].AsVector2Array();
                for (int c = 0; c < 4; c++)
                {
                    var cv = a[(int)Mesh.ArrayType.Custom0 + c];
                    if (cv.VariantType == Variant.Type.PackedFloat32Array) p.Cf[c] = cv.AsFloat32Array();
                    else if (cv.VariantType == Variant.Type.PackedByteArray) p.Cb[c] = cv.AsByteArray();
                }
            }
            o[i] = p;
        }
        return o;
    }

    /// <summary>On the main thread: the joined arrays as a Godot Array, and the skin's binds.</summary>
    static Godot.Collections.Array Pack(Joined j, List<(string Bone, Transform3D Pose)> binds, Skin skin)
    {
        foreach (var (bone, pose) in binds) skin.AddNamedBind(bone, pose);
        var o = new Godot.Collections.Array();
        o.Resize((int)Mesh.ArrayType.Max);
        o[(int)Mesh.ArrayType.Vertex] = j.V;
        o[(int)Mesh.ArrayType.Normal] = j.N;
        if (j.Tan != null) o[(int)Mesh.ArrayType.Tangent] = j.Tan;
        if (j.Col != null) o[(int)Mesh.ArrayType.Color] = j.Col;
        if (j.Uv != null) o[(int)Mesh.ArrayType.TexUV] = j.Uv;
        if (j.Uv2 != null) o[(int)Mesh.ArrayType.TexUV2] = j.Uv2;
        for (int c = 0; c < 4; c++)
            if (j.Cf[c] != null) o[(int)Mesh.ArrayType.Custom0 + c] = j.Cf[c]!;
            else if (j.Cb[c] != null) o[(int)Mesh.ArrayType.Custom0 + c] = j.Cb[c]!;
        o[(int)Mesh.ArrayType.Bones] = j.Bones;
        o[(int)Mesh.ArrayType.Weights] = j.W;
        o[(int)Mesh.ArrayType.Index] = j.Ix;
        return o;
    }

    /// <summary>Merges the play-camera draws of these full meshes (her outfit's, as laid) by material.</summary>
    internal void Merge(IEnumerable<MeshInstance3D> candidates)
    {
        foreach (var t in MergeSteps(candidates)) t?.Wait();
    }

    /// <summary>Merge as steps: a yielded task is waited for, null is where a frame may end. Only the joins run on a
    /// worker; every Godot call, and every change to the piece lists, is on the main thread.</summary>
    internal IEnumerable<System.Threading.Tasks.Task?> MergeSteps(IEnumerable<MeshInstance3D> candidates)
    {
        if (MergeOff) yield break;
        bool prof = Args.Get("tuck-prof") != null;
        var mp = System.Diagnostics.Stopwatch.StartNew();
        var step = System.Diagnostics.Stopwatch.StartNew();
        double sum0 = SumMs, maxStep = 0, mainSum = 0;
        void Lap() { double ms = step.Elapsed.TotalMilliseconds - (SumMs - sum0); mainSum += ms; if (ms > maxStep) maxStep = ms; }
        void Restart() { step.Restart(); sum0 = SumMs; }
        double tKey = 0, tSig = 0;
        var cache = new Dictionary<(ulong, int), (string? Sig, Godot.Collections.Array Arr)>();
        (string? Sig, Godot.Collections.Array Arr) Read(Mesh m, int s)
        {
            var ck = (m.GetInstanceId(), s);
            if (!cache.TryGetValue(ck, out var r)) cache[ck] = r = (Sig(m, s, out var arr), arr);
            return r;
        }
        var groups = new Dictionary<string, List<Part>>();
        var order = new List<string>();
        var taken = new List<MeshInstance3D>();
        foreach (var f in candidates.Distinct())
        {
            if (!IsInstanceValid(skel)) yield break;
            if (!IsInstanceValid(f) || f.Mesh is not ArrayMesh fm || f.Skin == null || !AtRest(f)) continue;
            if (!f.Transform.IsEqualApprox(Transform3D.Identity) || f.CastShadow != GeometryInstance3D.ShadowCastingSetting.On) continue;
            // (its gameplay mesh, if it stands for it alone: a lod_MAT of an outfit file is already one a material)
            var mine = pairs.Where(q => q.Full == f).ToList();
            if (mine.Count > 1 || (mine.Count == 1 && pairs.Count(q => q.Lod == mine[0].Lod) > 1)) continue;
            var src = mine.Count == 1 ? mine[0].Lod : f;
            if (src.Skin == null || src.Mesh is not ArrayMesh sm || !AtRest(src) || !src.Transform.IsEqualApprox(Transform3D.Identity)) continue;
            var parts = new List<(string, Part)>();
            bool ok = true;
            for (int s = 0; s < sm.GetSurfaceCount() && ok; s++)
            {
                int fs = mine.Count == 1 ? mine[0].Map[s] : s;
                if (mine.Count == 1 && (mine[0].Own[s] || f.GetSurfaceOverrideMaterial(fs) == null)) { ok = false; break; }
                double k0 = mp.Elapsed.TotalMilliseconds;
                var key = MatKey(f.GetSurfaceOverrideMaterial(fs) ?? fm.SurfaceGetMaterial(fs));
                double k1 = mp.Elapsed.TotalMilliseconds;
                var (sig, arr) = Read(sm, s);
                tKey += k1 - k0; tSig += mp.Elapsed.TotalMilliseconds - k1;
                if (key == null || sig == null) { ok = false; break; }
                parts.Add((sig + "#" + key, new Part { Full = f, Src = src, Surface = s, FullSurface = fs, Arr = arr }));
            }
            if (ok)
            {
                taken.Add(f);
                foreach (var (k, part) in parts)
                {
                    if (!groups.TryGetValue(k, out var g)) { groups[k] = g = new(); order.Add(k); }
                    g.Add(part);
                }
            }
            Lap(); yield return null; Restart();
        }
        if (taken.Count == 0) yield break;
        if (!IsInstanceValid(skel)) yield break;
        var set = taken.ToHashSet();

        // Their old gameplay meshes and piece shadows give way to the merged ones.
        var shadowSrc = new List<MeshInstance3D>();
        foreach (var f in taken) if (!pairs.Any(q => q.Full == f)) shadowSrc.Add(f);
        foreach (var (sh, like) in pieceShadows.Where(q => set.Contains(q.Like)).ToList())
        {
            if (sh.Skin != null && sh.Mesh is ArrayMesh sm && AtRest(sh) && sh.Transform.IsEqualApprox(Transform3D.Identity)
                && Enumerable.Range(0, sm.GetSurfaceCount()).All(s => Read(sm, s).Sig != null)) { shadowSrc.Add(sh); pieceShadows.Remove((sh, like)); }
        }
        var gone = new List<MeshInstance3D>();
        foreach (var q in pairs.Where(q => set.Contains(q.Full)).ToList()) { pairs.Remove(q); gone.Add(q.Lod); }

        double tPre = mp.Elapsed.TotalMilliseconds, tCat = 0;
        int made = 0, from = 0;
        Lap(); yield return null; Restart();
        foreach (var k in order)
        {
            if (!IsInstanceValid(skel)) yield break;
            var g = groups[k];
            var skin = new Skin();
            var mesh = new ArrayMesh();
            double c0 = mp.Elapsed.TotalMilliseconds;
            var binds = new List<(string Bone, Transform3D Pose)>();
            var ps = Take(g.Select(p => (p.Arr, p.Src.Skin!)).ToList(), binds, false);
            Lap();
            var job = System.Threading.Tasks.Task.Run(() => Join(ps, false));
            yield return job;
            Restart();
            if (!IsInstanceValid(skel)) yield break;
            var cat = Pack(job.Result, binds, skin);
            tCat += mp.Elapsed.TotalMilliseconds - c0;
            mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, cat, null, null, Flags(g[0].Src.Mesh, g[0].Surface, false));
            var mi = Add($"her_merge_{made}", mesh, skin, GeometryInstance3D.ShadowCastingSetting.Off);
            Sum(mi.Name, cat, skin);
            var first = g[0];
            pairs.Add((first.Full, mi, new[] { first.FullSurface }, new[] { false }, true));
            foreach (var p in g.Skip(1)) pairs.Add((p.Full, mi, new[] { p.FullSurface }, new[] { false }, false));
            made++; from += g.Count;
            Lap(); yield return null; Restart();
        }
        foreach (var f in taken) if (!fulls.Contains(f)) fulls.Add(f);
        double tMain = mp.Elapsed.TotalMilliseconds;
        // Her outfit's shadow at the play camera, one mesh a weight count (its geometry alone: the outfit is opaque).
        int shadows = 0;
        var sgroups = new Dictionary<string, List<(MeshInstance3D m, int s, Godot.Collections.Array arr)>>();
        var sorder = new List<string>();
        foreach (var m in shadowSrc)
            for (int s = 0, n = m.Mesh.GetSurfaceCount(); s < n; s++)
            {
                var (sig, arr) = Read(m.Mesh, s);
                if (sig == null) continue;
                var gk = sig[..2];   // (w4 or w8)
                if (!sgroups.TryGetValue(gk, out var sl)) { sgroups[gk] = sl = new(); sorder.Add(gk); }
                sl.Add((m, s, arr));
            }
        foreach (var gk in sorder)
        {
            if (!IsInstanceValid(skel)) yield break;
            var skin = new Skin();
            var mesh = new ArrayMesh();
            var list = sgroups[gk];
            var binds = new List<(string Bone, Transform3D Pose)>();
            var ps = Take(list.Select(x => (x.arr, x.m.Skin!)).ToList(), binds, true);
            Lap();
            var job = System.Threading.Tasks.Task.Run(() => Join(ps, true));
            yield return job;
            Restart();
            if (!IsInstanceValid(skel)) yield break;
            var scat = Pack(job.Result, binds, skin);
            mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, scat, null, null, Flags(list[0].m.Mesh, list[0].s, true));
            var sh = Add($"her_merge_shadow_{shadows++}", mesh, skin, GeometryInstance3D.ShadowCastingSetting.ShadowsOnly);
            Sum(sh.Name, scat, skin);
            pieceShadows.Add((sh, taken[0]));
            Lap(); yield return null; Restart();
        }
        foreach (var l in gone.Concat(shadowSrc.Where(m => !set.Contains(m))).Distinct())
        {
            l.GetParent()?.RemoveChild(l);
            l.QueueFree();
        }
        on = null;   // (switch afresh next frame)
        Lap();
        if (prof) GD.Print($"merge prof: keys {tKey:F1} sigs {tSig:F1} pre {tPre:F1} concat {tCat:F1} main {tMain:F1} all {mp.Elapsed.TotalMilliseconds:F1} ms (main thread steps {mainSum:F1} ms, largest {maxStep:F1} ms)");
        GD.Print($"her merge: {taken.Count} meshes, {from} surfaces into {made} by material, {shadowSrc.Count} shadow casters into {shadows}");
    }

    static double SumMs;   // (time spent hashing, left out of the prof timings)

    /// <summary>--tuck-prof: a hash of every array of a merged mesh and its skin's binds (to compare merges).</summary>
    static void Sum(string name, Godot.Collections.Array o, Skin skin)
    {
        if (Args.Get("tuck-prof") == null) return;
        var sw = System.Diagnostics.Stopwatch.StartNew();
        using var h = System.Security.Cryptography.SHA256.Create();
        void Feed(byte[] b) { h.TransformBlock(b, 0, b.Length, null, 0); }
        for (int i = 0; i < (int)Mesh.ArrayType.Max; i++)
        {
            var v = o[i];
            Feed(System.BitConverter.GetBytes(i));
            switch (v.VariantType)
            {
                case Variant.Type.PackedVector3Array: foreach (var x in v.AsVector3Array()) { Feed(System.BitConverter.GetBytes(x.X)); Feed(System.BitConverter.GetBytes(x.Y)); Feed(System.BitConverter.GetBytes(x.Z)); } break;
                case Variant.Type.PackedVector2Array: foreach (var x in v.AsVector2Array()) { Feed(System.BitConverter.GetBytes(x.X)); Feed(System.BitConverter.GetBytes(x.Y)); } break;
                case Variant.Type.PackedColorArray: foreach (var x in v.AsColorArray()) { Feed(System.BitConverter.GetBytes(x.R)); Feed(System.BitConverter.GetBytes(x.G)); Feed(System.BitConverter.GetBytes(x.B)); Feed(System.BitConverter.GetBytes(x.A)); } break;
                case Variant.Type.PackedFloat32Array: foreach (var x in v.AsFloat32Array()) Feed(System.BitConverter.GetBytes(x)); break;
                case Variant.Type.PackedInt32Array: foreach (var x in v.AsInt32Array()) Feed(System.BitConverter.GetBytes(x)); break;
                case Variant.Type.PackedByteArray: Feed(v.AsByteArray()); break;
            }
        }
        for (int b = 0; b < skin.GetBindCount(); b++)
        {
            Feed(System.Text.Encoding.UTF8.GetBytes(skin.GetBindName(b).ToString()));
            var t = skin.GetBindPose(b);
            foreach (var f in new[] { t.Basis.Column0.X, t.Basis.Column0.Y, t.Basis.Column0.Z, t.Basis.Column1.X, t.Basis.Column1.Y, t.Basis.Column1.Z, t.Basis.Column2.X, t.Basis.Column2.Y, t.Basis.Column2.Z, t.Origin.X, t.Origin.Y, t.Origin.Z })
                Feed(System.BitConverter.GetBytes(f));
        }
        h.TransformFinalBlock(System.Array.Empty<byte>(), 0, 0);
        GD.Print($"merge sum {name}: {System.Convert.ToHexString(h.Hash!)}");
        SumMs += sw.Elapsed.TotalMilliseconds;
    }

    MeshInstance3D Add(string name, ArrayMesh mesh, Skin skin, GeometryInstance3D.ShadowCastingSetting cast)
    {
        var mi = new MeshInstance3D { Name = name, Mesh = mesh, Skin = skin, Layers = 2, CastShadow = cast, Visible = false };
        skel.AddChild(mi);
        mi.Skeleton = "..";
        return mi;
    }

    /// <summary>A merged surface's flags from its first source's: eight weights a vertex, and (not for a shadow) its
    /// custom arrays' formats.</summary>
    static Mesh.ArrayFormat Flags(Mesh mesh, int s, bool shadow)
    {
        long fmt = (long)((ArrayMesh)mesh).SurfaceGetFormat(s);
        long keep = (long)Mesh.ArrayFormat.FlagUse8BoneWeights;
        if (!shadow) keep |= 0xFFFL << (int)Mesh.ArrayFormat.FormatCustom0Shift;
        return (Mesh.ArrayFormat)(fmt & keep);
    }
}
