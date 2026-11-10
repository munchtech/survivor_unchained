using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The engine's side of the engine-against-poser check (tools/armor/engine_check.py; --pose-probe-skin DIR with
/// --pose-probe-full, checks only, nothing without the flag): once, at the first sampled frame from --pose-probe-skin-at
/// (default 200), her drawn body (Heroine) and every drawn piece of B's built gear as the ENGINE holds them: each surface's
/// vertices, normals, bone indices and weights (4 or 8 a vertex), indices, the blend-shape arrays of the shapes that are on
/// (and the mesh's blend mode), the instance's shape values, its skin's binds (bone name, bind pose), and the body's tuck as
/// its material got it (the `tuck` uniform, the tuck_map's values, its width and the instance's offset). DIR/meshes.json
/// indexes one DIR/NAME.mesh.bin a mesh (float32 / int32, offsets and counts in the index). The check skins these with the
/// same frame's bones (--pose-probe-full) and lays them on the poser's: an import that lost a weight, a shape or a tier, or
/// a tuck map that is not the look's, shows as millimetres.
/// </summary>
public static class P1MeshDump
{
    static string X(Transform3D t) => string.Format(CultureInfo.InvariantCulture, "[{0:R},{1:R},{2:R},{3:R},{4:R},{5:R},{6:R},{7:R},{8:R},{9:R},{10:R},{11:R}]",
        t.Basis.Column0.X, t.Basis.Column0.Y, t.Basis.Column0.Z, t.Basis.Column1.X, t.Basis.Column1.Y, t.Basis.Column1.Z, t.Basis.Column2.X, t.Basis.Column2.Y, t.Basis.Column2.Z, t.Origin.X, t.Origin.Y, t.Origin.Z);

    public static void Write(Skeleton3D sk, string dir, long frame)
    {
        Directory.CreateDirectory(dir);
        var inv = CultureInfo.InvariantCulture;
        var index = new StringBuilder($"{{\"frame\":{frame},\"meshes\":[");
        bool first = true;
        foreach (var mi in sk.GetChildren().OfType<MeshInstance3D>().Where(m => m.Mesh is ArrayMesh && m.IsVisibleInTree() && (m.Name == "Heroine" || m.HasMeta(P1Body.GearMeta))))
        {
            var am = (ArrayMesh)mi.Mesh;
            string file = $"{mi.Name}.mesh.bin";
            using var w = new BinaryWriter(File.Create(Path.Combine(dir, file)));
            string Vec(Vector3[] a) { long at = w.BaseStream.Position; foreach (var v in a) { w.Write(v.X); w.Write(v.Y); w.Write(v.Z); } return $"[{at},{a.Length * 3}]"; }
            string Flt(float[] a) { long at = w.BaseStream.Position; foreach (float v in a) w.Write(v); return $"[{at},{a.Length}]"; }
            string Int(int[] a) { long at = w.BaseStream.Position; foreach (int v in a) w.Write(v); return $"[{at},{a.Length}]"; }
            var sb = new StringBuilder($"{(first ? "" : ",")}{{\"name\":\"{mi.Name}\",\"file\":\"{file}\",\"blend_mode\":{(int)am.BlendShapeMode},\"xform\":{X(mi.Transform)},\"shapes\":[");
            first = false;
            int nsh = am.GetBlendShapeCount();
            for (int i = 0; i < nsh; i++) sb.Append($"{(i > 0 ? "," : "")}[\"{am.GetBlendShapeName(i)}\",{mi.GetBlendShapeValue(i).ToString("R", inv)}]");
            sb.Append("],\"binds\":[");
            if (mi.Skin is Skin skin)
                for (int i = 0; i < skin.GetBindCount(); i++)
                {
                    string bn = skin.GetBindName(i).ToString();
                    int bb = bn != "" ? sk.FindBone(bn) : skin.GetBindBone(i);
                    sb.Append($"{(i > 0 ? "," : "")}{{\"bone\":\"{(bb >= 0 ? sk.GetBoneName(bb) : "")}\",\"pose\":{X(skin.GetBindPose(i))}}}");
                }
            sb.Append("],\"surfaces\":[");
            for (int s = 0; s < am.GetSurfaceCount(); s++)
            {
                var arr = am.SurfaceGetArrays(s);
                var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                var bones = arr[(int)Mesh.ArrayType.Bones].AsInt32Array();
                sb.Append($"{(s > 0 ? "," : "")}{{\"verts\":{v.Length},\"per\":{(v.Length > 0 ? bones.Length / v.Length : 0)},\"vertex\":{Vec(v)},\"normal\":{Vec(arr[(int)Mesh.ArrayType.Normal].AsVector3Array())}");
                sb.Append($",\"bones\":{Int(bones)},\"weights\":{Flt(arr[(int)Mesh.ArrayType.Weights].AsFloat32Array())},\"index\":{Int(arr[(int)Mesh.ArrayType.Index].AsInt32Array())},\"shapes\":{{");
                bool f2 = true;
                if (nsh > 0)
                {
                    var bs = am.SurfaceGetBlendShapeArrays(s);
                    for (int i = 0; i < nsh && i < bs.Count; i++)
                    {
                        if (Mathf.Abs(mi.GetBlendShapeValue(i)) < 1e-5f) continue;
                        sb.Append($"{(f2 ? "" : ",")}\"{am.GetBlendShapeName(i)}\":{Vec(bs[i][(int)Mesh.ArrayType.Vertex].AsVector3Array())}");
                        f2 = false;
                    }
                }
                sb.Append('}');
                if (s < mi.GetSurfaceOverrideMaterialCount() && mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m
                    && m.GetShaderParameter("tuck_channel") is { VariantType: Variant.Type.Int } ch)
                {
                    sb.Append($",\"tuck_channel\":{ch.AsInt32()},\"tuck\":{m.GetShaderParameter("tuck").AsSingle().ToString("R", inv)}");
                    if (ch.AsInt32() == -2 && m.GetShaderParameter("tuck_map").As<Texture2D>() is { } tex && tex.GetImage() is { } img)
                    {
                        var data = img.GetData();
                        var map = new float[data.Length / 4];
                        System.Buffer.BlockCopy(data, 0, map, 0, map.Length * 4);
                        var off = mi.GetInstanceShaderParameter("tuck_offset");
                        sb.Append($",\"tuck_format\":\"{img.GetFormat()}\",\"tuck_width\":{m.GetShaderParameter("tuck_map_width").AsInt32()},\"tuck_offset\":{(off.VariantType == Variant.Type.Int ? off.AsInt32() : 0)},\"tuck_map\":{Flt(map)}");
                    }
                }
                sb.Append('}');
            }
            sb.Append("]}");
            index.Append(sb);
        }
        index.Append("]}");
        File.WriteAllText(Path.Combine(dir, "meshes.json"), index.ToString());
        GD.Print($"p1: mesh dump at frame {frame} -> {dir}");
    }
}
