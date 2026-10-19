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

    /// <summary>Merges the play-camera draws of these full meshes (her outfit's, as laid) by material.</summary>
    internal void Merge(IEnumerable<MeshInstance3D> candidates)
    {
        if (MergeOff) return;
        var groups = new Dictionary<string, List<Part>>();
        var order = new List<string>();
        var taken = new List<MeshInstance3D>();
        foreach (var f in candidates.Distinct())
        {
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
                var key = MatKey(f.GetSurfaceOverrideMaterial(fs) ?? fm.SurfaceGetMaterial(fs));
                var sig = Sig(sm, s, out var arr);
                if (key == null || sig == null) { ok = false; break; }
                parts.Add((sig + "#" + key, new Part { Full = f, Src = src, Surface = s, FullSurface = fs, Arr = arr }));
            }
            if (!ok) continue;
            taken.Add(f);
            foreach (var (k, part) in parts)
            {
                if (!groups.TryGetValue(k, out var g)) { groups[k] = g = new(); order.Add(k); }
                g.Add(part);
            }
        }
        if (taken.Count == 0) return;
        var set = taken.ToHashSet();

        // Their old gameplay meshes and piece shadows give way to the merged ones.
        var shadowSrc = new List<MeshInstance3D>();
        foreach (var f in taken) if (!pairs.Any(q => q.Full == f)) shadowSrc.Add(f);
        foreach (var (sh, like) in pieceShadows.Where(q => set.Contains(q.Like)).ToList())
        {
            if (sh.Skin != null && sh.Mesh is ArrayMesh sm && AtRest(sh) && sh.Transform.IsEqualApprox(Transform3D.Identity)
                && Enumerable.Range(0, sm.GetSurfaceCount()).All(s => Sig(sm, s, out _) != null)) { shadowSrc.Add(sh); pieceShadows.Remove((sh, like)); }
        }
        var gone = new List<MeshInstance3D>();
        foreach (var q in pairs.Where(q => set.Contains(q.Full)).ToList()) { pairs.Remove(q); gone.Add(q.Lod); }

        int made = 0, from = 0;
        foreach (var k in order)
        {
            var g = groups[k];
            var skin = new Skin();
            var mesh = new ArrayMesh();
            mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, Concat(g.Select(p => (p.Arr, p.Src.Skin!)).ToList(), skin, false), null, null, Flags(g[0].Src.Mesh, g[0].Surface, false));
            var mi = Add($"her_merge_{made}", mesh, skin, GeometryInstance3D.ShadowCastingSetting.Off);
            var first = g[0];
            pairs.Add((first.Full, mi, new[] { first.FullSurface }, new[] { false }, true));
            foreach (var p in g.Skip(1)) pairs.Add((p.Full, mi, new[] { p.FullSurface }, new[] { false }, false));
            made++; from += g.Count;
        }
        foreach (var f in taken) if (!fulls.Contains(f)) fulls.Add(f);
        // Her outfit's shadow at the play camera, one mesh a weight count (its geometry alone: the outfit is opaque).
        int shadows = 0;
        foreach (var g in shadowSrc.SelectMany(m => Enumerable.Range(0, m.Mesh.GetSurfaceCount()).Select(s => (m, s)))
                     .Select(x => (x.m, x.s, sig: Sig(x.m.Mesh, x.s, out var arr), arr)).Where(x => x.sig != null)
                     .GroupBy(x => x.sig![..2]))   // (w4 or w8)
        {
            var skin = new Skin();
            var mesh = new ArrayMesh();
            var list = g.ToList();
            mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, Concat(list.Select(x => (x.arr, x.m.Skin!)).ToList(), skin, true), null, null, Flags(list[0].m.Mesh, list[0].s, true));
            var sh = Add($"her_merge_shadow_{shadows++}", mesh, skin, GeometryInstance3D.ShadowCastingSetting.ShadowsOnly);
            pieceShadows.Add((sh, taken[0]));
        }
        foreach (var l in gone.Concat(shadowSrc.Where(m => !set.Contains(m))).Distinct())
        {
            l.GetParent()?.RemoveChild(l);
            l.QueueFree();
        }
        on = null;   // (switch afresh next frame)
        GD.Print($"her merge: {taken.Count} meshes, {from} surfaces into {made} by material, {shadowSrc.Count} shadow casters into {shadows}");
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

    /// <summary>The surfaces' arrays end to end, their bone indices remapped into one skin of all their binds
    /// (a bind shared when its bone and pose are the same). Shadow: positions, normals and weights only.</summary>
    Godot.Collections.Array Concat(List<(Godot.Collections.Array Arr, Skin Skin)> src, Skin skin, bool shadow)
    {
        var binds = new List<(string Bone, Transform3D Pose)>();
        var v = new List<Vector3>(); var nrm = new List<Vector3>(); var tan = new List<float>(); var col = new List<Color>();
        var custom = new List<float>[4]; var customB = new List<byte>[4];
        for (int c = 0; c < 4; c++) { custom[c] = new(); customB[c] = new(); }
        var uv = new List<Vector2>(); var uv2 = new List<Vector2>(); var bones = new List<int>(); var w = new List<float>(); var ix = new List<int>();
        foreach (var (a, sk) in src)
        {
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
            int baseV = v.Count;
            var vs = a[(int)Mesh.ArrayType.Vertex].AsVector3Array();
            v.AddRange(vs);
            nrm.AddRange(a[(int)Mesh.ArrayType.Normal].AsVector3Array());
            if (!shadow)
            {
                if (a[(int)Mesh.ArrayType.Tangent].VariantType != Variant.Type.Nil) tan.AddRange(a[(int)Mesh.ArrayType.Tangent].AsFloat32Array());
                if (a[(int)Mesh.ArrayType.Color].VariantType != Variant.Type.Nil) col.AddRange(a[(int)Mesh.ArrayType.Color].AsColorArray());
                if (a[(int)Mesh.ArrayType.TexUV].VariantType != Variant.Type.Nil) uv.AddRange(a[(int)Mesh.ArrayType.TexUV].AsVector2Array());
                if (a[(int)Mesh.ArrayType.TexUV2].VariantType != Variant.Type.Nil) uv2.AddRange(a[(int)Mesh.ArrayType.TexUV2].AsVector2Array());
                for (int c = 0; c < 4; c++)
                {
                    var cv = a[(int)Mesh.ArrayType.Custom0 + c];
                    if (cv.VariantType == Variant.Type.PackedFloat32Array) custom[c].AddRange(cv.AsFloat32Array());
                    else if (cv.VariantType == Variant.Type.PackedByteArray) customB[c].AddRange(cv.AsByteArray());
                }
            }
            bones.AddRange(a[(int)Mesh.ArrayType.Bones].AsInt32Array().Select(b => map[b]));
            w.AddRange(a[(int)Mesh.ArrayType.Weights].AsFloat32Array());
            if (a[(int)Mesh.ArrayType.Index].VariantType != Variant.Type.Nil) ix.AddRange(a[(int)Mesh.ArrayType.Index].AsInt32Array().Select(i => i + baseV));
            else ix.AddRange(Enumerable.Range(baseV, vs.Length));
        }
        foreach (var (bone, pose) in binds) skin.AddNamedBind(bone, pose);
        var o = new Godot.Collections.Array();
        o.Resize((int)Mesh.ArrayType.Max);
        o[(int)Mesh.ArrayType.Vertex] = v.ToArray();
        o[(int)Mesh.ArrayType.Normal] = nrm.ToArray();
        if (tan.Count > 0) o[(int)Mesh.ArrayType.Tangent] = tan.ToArray();
        if (col.Count > 0) o[(int)Mesh.ArrayType.Color] = col.ToArray();
        if (uv.Count > 0) o[(int)Mesh.ArrayType.TexUV] = uv.ToArray();
        if (uv2.Count > 0) o[(int)Mesh.ArrayType.TexUV2] = uv2.ToArray();
        for (int c = 0; c < 4; c++)
            if (custom[c].Count > 0) o[(int)Mesh.ArrayType.Custom0 + c] = custom[c].ToArray();
            else if (customB[c].Count > 0) o[(int)Mesh.ArrayType.Custom0 + c] = customB[c].ToArray();
        o[(int)Mesh.ArrayType.Bones] = bones.ToArray();
        o[(int)Mesh.ArrayType.Weights] = w.ToArray();
        o[(int)Mesh.ArrayType.Index] = ix.ToArray();
        return o;
    }
}
