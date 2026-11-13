using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.View;

/// <summary>
/// The armor-inside-her-skin measure (--wear-inside FILE; off without the flag; her only). Every N frames
/// (--wear-inside-every, default 6) after every layer (Skeleton3D.SkeletonUpdated) it skins her body (the Heroine mesh) and
/// her worn pieces in the chosen slots (--wear-inside-slots, default skirt,pauldrons) on the CPU, counts the piece vertices
/// that lie inside her posed skin (Play/InsideTest), and appends one JSON line: the frame, the clip and time of
/// --clip-tour (PlayerView.TourClip/TourTime), and per slot the vertices, the inside count, the deepest mm, by region and by side.
/// At the end of a tour or on exit a summary line gives each clip worst sample per slot. Meshes are read once; a sample only skins and queries.
/// </summary>
public partial class WearInside : Node
{
    const float InsideMm = 0.5f;   // inside = signed distance below -0.5 mm
    readonly Skeleton3D sk;
    readonly string path = Args.Get("wear-inside") ?? "";
    readonly int every = Math.Max(1, (int)Args.Num("wear-inside-every", 6));
    readonly HashSet<string> slots = new((Args.Get("wear-inside-slots") ?? "skirt,pauldrons").Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries));
    static WearInside? instance;
    static bool truncated, summarized;
    MeshData? body;
    readonly Dictionary<ulong, MeshData?> pieces = new();
    readonly Dictionary<MeshData, string> slotOf = new();
    string[] region = Array.Empty<string>();   // by body vertex
    ulong lastFrame = ulong.MaxValue;
    readonly Dictionary<string, Dictionary<string, Worst>> worst = new();   // clip -> slot -> its worst sample

    record struct Worst(int Inside, double T, int N, int IL, int IR, int NL, int NR);

    sealed class Stat
    {
        public int N, Inside, IL, IR, NL, NR;
        public float Deep;
        public Dictionary<string, int> Region = new() { ["thigh"] = 0, ["arm"] = 0, ["torso"] = 0 };
    }

    public WearInside(Skeleton3D skeleton) { sk = skeleton; Name = "WearInside"; }

    public override void _Ready()
    {
        instance = this;
        if (!truncated) { truncated = true; System.IO.File.WriteAllText(path, ""); }
        sk.SkeletonUpdated += Sample;
    }

    public override void _ExitTree()
    {
        sk.SkeletonUpdated -= Sample;
        Finish();
    }

    /// <summary>Writes the summary line, once (the tour end, or the exit).</summary>
    public static void Finish() => instance?.WriteSummary();

    void WriteSummary()
    {
        if (summarized || worst.Count == 0) return;
        summarized = true;
        var sb = new StringBuilder("{\"summary\":{");
        sb.Append(string.Join(",", worst.Select(c => $"\"{c.Key}\":{{" + string.Join(",", c.Value.Select(s =>
        {
            var w = s.Value;
            return string.Format(CultureInfo.InvariantCulture,
                "\"{0}\":{{\"worst_inside\":{1},\"worst_t\":{2:0.###},\"worst_pct\":{3:0.##},\"worst_l_pct\":{4:0.##},\"worst_r_pct\":{5:0.##}}}",
                s.Key, w.Inside, w.T, Pct(w.Inside, w.N), Pct(w.IL, w.NL), Pct(w.IR, w.NR));
        })) + "}")));
        sb.Append("}}\n");
        System.IO.File.AppendAllText(path, sb.ToString());
    }

    static double Pct(int a, int n) => n == 0 ? 0 : a * 100.0 / n;

    /// <summary>One mesh read once: base positions and normals, influences (padded to K per vertex), blend shapes
    /// (absolute positions), triangles, and the vertices skinned at the skeleton rest.</summary>
    sealed class MeshData
    {
        public MeshInstance3D Mi = null!;
        public Vector3[] Pos = Array.Empty<Vector3>(), Nrm = Array.Empty<Vector3>(), Rest = Array.Empty<Vector3>();
        public int[] Bones = Array.Empty<int>(), Tris = Array.Empty<int>(), BindBone = Array.Empty<int>();
        public float[] Weights = Array.Empty<float>();
        public int K;
        public Vector3[][] ShapePos = Array.Empty<Vector3[]>(), ShapeNrm = Array.Empty<Vector3[]>();
        public Transform3D[] Bind = Array.Empty<Transform3D>();
    }

    MeshData? Read(MeshInstance3D mi)
    {
        if (mi.Mesh == null || mi.Skin == null) return null;
        var skin = mi.Skin;
        var m = new MeshData { Mi = mi };
        int nb = skin.GetBindCount();
        m.BindBone = Enumerable.Range(0, nb).Select(b => skin.GetBindName(b) is var n && n != "" ? sk.FindBone(n) : skin.GetBindBone(b)).ToArray();
        m.Bind = Enumerable.Range(0, nb).Select(b => skin.GetBindPose(b)).ToArray();
        var pos = new List<Vector3>(); var nrm = new List<Vector3>(); var tris = new List<int>();
        var bones = new List<int>(); var weights = new List<float>();
        var done = new List<(int surf, int off)>();
        int kmax = 4;
        for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
        {
            var arr = mi.Mesh.SurfaceGetArrays(s);
            var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
            if (v.Length > 0 && arr[(int)Mesh.ArrayType.Bones].VariantType != Variant.Type.Nil)
                kmax = Math.Max(kmax, arr[(int)Mesh.ArrayType.Bones].AsInt32Array().Length / v.Length);
        }
        m.K = kmax;
        for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
        {
            var arr = mi.Mesh.SurfaceGetArrays(s);
            var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
            if (v.Length == 0 || arr[(int)Mesh.ArrayType.Bones].VariantType == Variant.Type.Nil || arr[(int)Mesh.ArrayType.Weights].VariantType == Variant.Type.Nil) continue;
            int off = pos.Count;
            done.Add((s, off));
            pos.AddRange(v);
            nrm.AddRange(arr[(int)Mesh.ArrayType.Normal].VariantType == Variant.Type.Nil ? new Vector3[v.Length] : arr[(int)Mesh.ArrayType.Normal].AsVector3Array());
            var bo = arr[(int)Mesh.ArrayType.Bones].AsInt32Array(); var w = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
            int k = bo.Length / v.Length;
            for (int i = 0; i < v.Length; i++)
                for (int j = 0; j < kmax; j++) { bones.Add(j < k ? bo[i * k + j] : 0); weights.Add(j < k ? w[i * k + j] : 0); }
            if (arr[(int)Mesh.ArrayType.Index].VariantType == Variant.Type.Nil) for (int i = 0; i < v.Length; i++) tris.Add(off + i);
            else tris.AddRange(arr[(int)Mesh.ArrayType.Index].AsInt32Array().Select(i => off + i));
        }
        if (pos.Count == 0) return null;
        m.Pos = pos.ToArray(); m.Nrm = nrm.ToArray(); m.Bones = bones.ToArray(); m.Weights = weights.ToArray(); m.Tris = tris.ToArray();
        int bs = mi.GetBlendShapeCount();
        m.ShapePos = new Vector3[bs][]; m.ShapeNrm = new Vector3[bs][];
        for (int b = 0; b < bs; b++) { m.ShapePos[b] = (Vector3[])m.Pos.Clone(); m.ShapeNrm[b] = (Vector3[])m.Nrm.Clone(); }
        foreach (var (s, off) in done)
        {
            var shapes = mi.Mesh.SurfaceGetBlendShapeArrays(s);
            for (int b = 0; b < Math.Min(bs, shapes.Count); b++)
            {
                var sp = shapes[b][(int)Mesh.ArrayType.Vertex];
                if (sp.VariantType != Variant.Type.Nil) { var a = sp.AsVector3Array(); Array.Copy(a, 0, m.ShapePos[b], off, a.Length); }
                var sn = shapes[b][(int)Mesh.ArrayType.Normal];
                if (sn.VariantType != Variant.Type.Nil) { var a = sn.AsVector3Array(); Array.Copy(a, 0, m.ShapeNrm[b], off, a.Length); }
            }
        }
        var restT = m.BindBone.Select((bone, b) => bone >= 0 ? sk.GetBoneGlobalRest(bone) * m.Bind[b] : Transform3D.Identity).ToArray();
        m.Rest = new Vector3[m.Pos.Length];
        Skin(m, restT, m.Rest, null);
        return m;
    }

    /// <summary>The mesh vertices (and normals) with its blend shapes at the instance values (base + sum w*(shape - base)),
    /// linear-blend skinned by the bone transforms t (skeleton space).</summary>
    static void Skin(MeshData m, Transform3D[] t, Vector3[] outPos, Vector3[]? outNrm)
    {
        var p = m.Pos; var n = m.Nrm;
        var live = Enumerable.Range(0, m.ShapePos.Length).Select(b => (b, w: m.Mi.GetBlendShapeValue(b))).Where(x => Math.Abs(x.w) > 1e-6f).ToArray();
        if (live.Length > 0)
        {
            p = (Vector3[])p.Clone(); n = (Vector3[])n.Clone();
            foreach (var (b, w) in live)
                for (int i = 0; i < p.Length; i++)
                {
                    p[i] += w * (m.ShapePos[b][i] - m.Pos[i]);
                    n[i] += w * (m.ShapeNrm[b][i] - m.Nrm[i]);
                }
        }
        int k = m.K;
        var pp = p; var nn0 = n;
        Parallel.For(0, pp.Length, i =>
        {
            Vector3 a = Vector3.Zero, nn = Vector3.Zero;
            for (int j = 0; j < k; j++)
            {
                float w = m.Weights[i * k + j];
                if (w <= 0) continue;
                int b = m.Bones[i * k + j];
                if (b < 0 || b >= t.Length) continue;
                a += w * (t[b] * pp[i]);
                if (outNrm != null) nn += w * (t[b].Basis * nn0[i]);
            }
            outPos[i] = a;
            if (outNrm != null) outNrm[i] = nn.LengthSquared() > 0 ? nn.Normalized() : Vector3.Up;
        });
    }

    Transform3D[] Matrices(MeshData m) =>
        m.BindBone.Select((bone, b) => bone >= 0 ? sk.GetBoneGlobalPose(bone) * m.Bind[b] : Transform3D.Identity).ToArray();

    static string Region(string bone)
    {
        if (bone.StartsWith("thigh", StringComparison.OrdinalIgnoreCase) || bone.StartsWith("glute", StringComparison.OrdinalIgnoreCase) || bone.StartsWith("calf", StringComparison.OrdinalIgnoreCase)) return "thigh";
        foreach (var a in new[] { "upperarm", "delt", "clavicle", "trap", "lowerarm" })
            if (bone.StartsWith(a, StringComparison.OrdinalIgnoreCase)) return "arm";
        return "torso";
    }

    static System.Numerics.Vector3 N(Vector3 v) => new(v.X, v.Y, v.Z);

    void Sample()
    {
        ulong f = Engine.GetProcessFrames();
        if (f == lastFrame || f % (ulong)every != 0) return;
        var clock = Stopwatch.StartNew();
        if (body == null)
        {
            var bm = sk.GetChildren().OfType<MeshInstance3D>().FirstOrDefault(m => m.Name == "Heroine");
            if (bm == null || Read(bm) is not { } bd) return;
            body = bd;
            // each body vertex dominant bone, by name: the region its hits are counted in
            int k = body.K;
            var names = body.BindBone.Select(b => b >= 0 ? Region(sk.GetBoneName(b)) : "torso").ToArray();
            region = new string[body.Pos.Length];
            for (int i = 0; i < region.Length; i++)
            {
                int best = 0;
                for (int j = 1; j < k; j++) if (body.Weights[i * k + j] > body.Weights[i * k + best]) best = j;
                int bind = body.Bones[i * k + best];
                region[i] = bind >= 0 && bind < names.Length ? names[bind] : "torso";
            }
        }
        lastFrame = f;
        // the chosen slots pieces, worn now, shown or not: found each sample as HerWear adds and drops them
        foreach (var mi in sk.GetChildren().OfType<MeshInstance3D>())
        {
            if (!mi.HasMeta("her_wear") || pieces.ContainsKey(mi.GetInstanceId())) continue;
            string nm = mi.Name.ToString();
            MeshData? md = null;
            if (!(nm.StartsWith("lod_") || nm.StartsWith("her_merge") || nm.Contains("_lod1_") || nm.EndsWith("_shadow")))
            {
                string slot = ArmorIndex.Shared.SlotOf(mi.GetMeta("her_wear").AsString());
                if (slots.Contains(slot) && Read(mi) is { } r) { md = r; slotOf[r] = slot; }
            }
            pieces[mi.GetInstanceId()] = md;
        }
        var bp = new Vector3[body.Pos.Length]; var bn = new Vector3[body.Pos.Length];
        Skin(body, Matrices(body), bp, bn);
        var test = new InsideTest(bp.Select(N).ToArray(), bn.Select(N).ToArray(), body.Tris);
        var stats = new Dictionary<string, Stat>();
        foreach (var kv in pieces.ToArray())
        {
            if (kv.Value is not { } pm) continue;
            if (!GodotObject.IsInstanceValid(pm.Mi)) { pieces.Remove(kv.Key); continue; }
            var pp = new Vector3[pm.Pos.Length];
            Skin(pm, Matrices(pm), pp, null);
            var d = new float[pp.Length]; var vert = new int[pp.Length];
            Parallel.For(0, pp.Length, i => { var (dist, v) = test.Query(N(pp[i])); d[i] = dist; vert[i] = v; });
            string slot = slotOf[pm];
            if (!stats.TryGetValue(slot, out var st)) stats[slot] = st = new Stat();
            for (int i = 0; i < pp.Length; i++)
            {
                bool left = pm.Rest[i].X > 0;
                st.N++; if (left) st.NL++; else st.NR++;
                if (vert[i] < 0 || d[i] >= -InsideMm / 1000f) continue;
                st.Inside++; if (left) st.IL++; else st.IR++;
                st.Deep = Math.Max(st.Deep, -d[i] * 1000f);
                st.Region[region[vert[i]]]++;
            }
        }
        double ms = clock.Elapsed.TotalMilliseconds;
        string? clip = PlayerView.TourClip; double t = PlayerView.TourTime;
        var sb = new StringBuilder();
        sb.Append(string.Format(CultureInfo.InvariantCulture, "{{\"frame\":{0},\"clip\":{1},\"t\":{2:0.###},\"slots\":{{", f, clip == null ? "null" : $"\"{clip}\"", t));
        sb.Append(string.Join(",", stats.Select(s => string.Format(CultureInfo.InvariantCulture,
            "\"{0}\":{{\"n\":{1},\"inside\":{2},\"deep_mm\":{3:0.##},\"by_region\":{{\"thigh\":{4},\"arm\":{5},\"torso\":{6}}},\"by_side\":{{\"l\":{7},\"r\":{8}}},\"n_side\":{{\"l\":{9},\"r\":{10}}}}}",
            s.Key, s.Value.N, s.Value.Inside, s.Value.Deep, s.Value.Region["thigh"], s.Value.Region["arm"], s.Value.Region["torso"], s.Value.IL, s.Value.IR, s.Value.NL, s.Value.NR))));
        sb.Append(string.Format(CultureInfo.InvariantCulture, "}},\"ms\":{0:0.#}}}\n", ms));
        System.IO.File.AppendAllText(path, sb.ToString());
        GD.Print($"wear-inside: frame {f} {clip ?? "-"} {t:0.##}s {ms:0.#} ms");
        string key = clip ?? "(none)";
        if (!worst.TryGetValue(key, out var byslot)) worst[key] = byslot = new();
        foreach (var (slot, s) in stats)
            if (!byslot.TryGetValue(slot, out var w) || s.Inside > w.Inside)
                byslot[slot] = new Worst(s.Inside, t, s.N, s.IL, s.IR, s.NL, s.NR);
    }
}