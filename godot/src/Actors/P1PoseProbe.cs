using System.Globalization;
using System.Linq;
using System.Text;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The pose ruler (--pose-probe FILE [--pose-probe-every N, default 5 frames]; A and B alike, off without the flag): after every
/// layer (Skeleton3D.SkeletonUpdated) appends one JSON line per sampled frame to FILE: the role bones' world positions by
/// role name (A's names; on B through P1Body.BoneName), each one's rest-relative turn applied to the skeleton's axes
/// (fwd: +Z at rest, up: +Y at rest), the actor's ground height and the crown (the body mesh's top vertex carried by Head).
/// tools/body/pose_probe.py reads two such files and prints the table.
/// --pose-probe-full FILE: the posed-fit ruler (tools/body/posed_fit.py): the same sampled frames, one JSON line each: the skeleton's world
/// transform, the camera, the meshes' nonzero blend-shape weights, every bone's skeleton-space pose as 12 numbers (basis columns, origin).
/// --pose-probe-skin DIR (with --pose-probe-full): once, at the first sampled frame from --pose-probe-skin-at (default 200), her drawn
/// body's and gear's meshes as the engine holds them (P1MeshDump; tools/armor/engine_check.py lays them on the poser's).
/// </summary>
public partial class P1PoseProbe : Node
{
    static readonly string[] Roles =
    {
        "pelvis", "spine_01", "spine_03", "neck_01", "Head", "clavicle_l", "clavicle_r", "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r",
        "hand_l", "hand_r", "middle_01_l", "middle_01_r", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r",
    };
    readonly Skeleton3D sk;
    readonly Node3D root;
    readonly string path = Args.Get("pose-probe") ?? "";
    readonly int every = (int)Args.Num("pose-probe-every", 5);
    readonly string fullPath = Args.Get("pose-probe-full") ?? "";
    readonly string skinDir = Args.Get("pose-probe-skin") ?? "";
    readonly int skinAt = (int)Args.Num("pose-probe-skin-at", 200);
    bool skinDone;
    int[] bones = System.Array.Empty<int>();
    Basis[] restInv = System.Array.Empty<Basis>();
    Vector3 crown;
    bool started;
    static bool truncated;

    public P1PoseProbe(Skeleton3D skeleton, Node3D actorRoot) { sk = skeleton; root = actorRoot; Name = "P1PoseProbe"; }

    public override void _Ready()
    {
        if (!truncated)
        {
            truncated = true;
            System.IO.File.WriteAllText(path, "");
            if (fullPath != "") System.IO.File.WriteAllText(fullPath, "");
        }
        sk.SkeletonUpdated += Sample;
    }

    public override void _ExitTree() => sk.SkeletonUpdated -= Sample;

    static string V(Vector3 v) => string.Format(CultureInfo.InvariantCulture, "[{0:0.#####},{1:0.#####},{2:0.#####}]", v.X, v.Y, v.Z);

    void Start()
    {
        started = true;
        bones = Roles.Select(r => sk.FindBone(P1Body.BoneName(sk, r))).ToArray();
        restInv = bones.Select(b => b < 0 ? Basis.Identity : sk.GetBoneGlobalRest(b).Basis.Orthonormalized().Inverse()).ToArray();
        int head = sk.FindBone("Head");
        // the crown: the top vertex of her head (whichever of her skinned meshes carries it, hair and hidden pieces out), carried by Head
        float top = float.MinValue; var at = Vector3.Zero;
        var names = new StringBuilder();
        foreach (var mi in sk.GetChildren().OfType<MeshInstance3D>().Where(m => m.Mesh != null))
        {
            bool hair = mi.GetChildren().OfType<HairSway>().Any();
            names.Append($" {mi.Name}{(hair ? "(hair)" : "")}{(mi.Visible ? "" : "(hidden)")}");
            string nm = mi.Name.ToString();
            if (hair || nm == "lod_p1_body" || nm.Contains("lash") || nm.Contains("brow") || nm.Contains("teeth") || nm.Contains("eye")) continue;
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                foreach (var v in mi.Mesh.SurfaceGetArrays(s)[(int)Mesh.ArrayType.Vertex].AsVector3Array())
                    if (v.Y > top) { top = v.Y; at = v; }
        }
        crown = head >= 0 ? at - sk.GetBoneGlobalRest(head).Origin : Vector3.Zero;
        var rest = new StringBuilder();
        for (int i = 0; i < Roles.Length; i++)
            if (bones[i] >= 0) rest.Append($"{(rest.Length > 0 ? "," : "")}\"{Roles[i]}\":{V(sk.GetBoneGlobalRest(bones[i]).Origin)}");
        System.IO.File.AppendAllText(path, $"{{\"rest\":{{{rest}}},\"crown_rest\":{V(at)},\"meshes\":\"{names}\"}}\n");
    }

    void Sample()
    {
        long f = (long)Engine.GetProcessFrames();
        if (every > 1 && f % every != 0) return;
        if (!sk.IsInsideTree() || !sk.IsVisibleInTree()) return;
        if (!started) Start();
        var w = sk.GlobalTransform;
        var sb = new StringBuilder();
        sb.Append($"{{\"frame\":{f},\"ground\":{root.GlobalPosition.Y.ToString("0.#####", CultureInfo.InvariantCulture)},\"bones\":{{");
        bool first = true;
        for (int i = 0; i < Roles.Length; i++)
        {
            if (bones[i] < 0) continue;
            var g = sk.GetBoneGlobalPose(bones[i]);
            var r = w.Basis.Orthonormalized() * g.Basis.Orthonormalized() * restInv[i];
            sb.Append($"{(first ? "" : ",")}\"{Roles[i]}\":{{\"p\":{V(w * g.Origin)},\"fwd\":{V(r * Vector3.Back)},\"up\":{V(r * Vector3.Up)}}}");
            first = false;
            if (Roles[i] == "Head") sb.Append($",\"crown\":{{\"p\":{V(w * (g.Origin + r * crown))}}}");
        }
        sb.Append("}}\n");
        System.IO.File.AppendAllText(path, sb.ToString());
        if (fullPath != "") Full(f);
    }

    static string X(Transform3D t) => string.Format(CultureInfo.InvariantCulture, "[{0:0.######},{1:0.######},{2:0.######},{3:0.######},{4:0.######},{5:0.######},{6:0.######},{7:0.######},{8:0.######},{9:0.######},{10:0.######},{11:0.######}]",
        t.Basis.Column0.X, t.Basis.Column0.Y, t.Basis.Column0.Z, t.Basis.Column1.X, t.Basis.Column1.Y, t.Basis.Column1.Z, t.Basis.Column2.X, t.Basis.Column2.Y, t.Basis.Column2.Z, t.Origin.X, t.Origin.Y, t.Origin.Z);

    static readonly System.Collections.Generic.Dictionary<Node3D, string> boxes = new();

    /// <summary>The piece's meshes' bounding box in the piece's own space, [min..., max...] (cached per piece).</summary>
    static string Box(Node3D piece)
    {
        if (boxes.TryGetValue(piece, out var s)) return s;
        var inv = piece.GlobalTransform.AffineInverse();
        Aabb? box = null;
        foreach (var mi in Walk(piece).OfType<MeshInstance3D>().Where(m => m.Mesh != null))
        {
            var a = (inv * mi.GlobalTransform) * mi.Mesh.GetAabb();
            box = box is { } bb ? bb.Merge(a) : a;
        }
        var x = box ?? new Aabb();
        s = $"[{V(x.Position)[1..^1]},{V(x.End)[1..^1]}]";
        boxes[piece] = s;
        return s;
    }

    static System.Collections.Generic.IEnumerable<Node> Walk(Node n)
    {
        yield return n;
        foreach (var c in n.GetChildren()) foreach (var d in Walk(c)) yield return d;
    }

    void Full(long f)
    {
        var sb = new StringBuilder();
        var cam = sk.GetViewport().GetCamera3D();
        var size = sk.GetViewport().GetVisibleRect().Size;
        sb.Append($"{{\"frame\":{f},\"skeleton\":{X(sk.GlobalTransform)}");
        if (cam != null)
            sb.Append($",\"camera\":{{\"x\":{X(cam.GlobalTransform)},\"fov\":{cam.Fov.ToString("0.####", CultureInfo.InvariantCulture)},\"size\":[{size.X.ToString("0", CultureInfo.InvariantCulture)},{size.Y.ToString("0", CultureInfo.InvariantCulture)}]}}");
        sb.Append(",\"meshes\":{");
        bool first = true;
        foreach (var mi in sk.GetChildren().OfType<MeshInstance3D>().Where(m => m.Mesh is ArrayMesh))
        {
            sb.Append($"{(first ? "" : ",")}\"{mi.Name}\":{{\"visible\":{(mi.IsVisibleInTree() ? "true" : "false")},\"shapes\":{{");
            first = false;
            var am = (ArrayMesh)mi.Mesh;
            bool f2 = true;
            for (int i = 0; i < am.GetBlendShapeCount(); i++)
            {
                float v = mi.GetBlendShapeValue(i);
                if (Mathf.Abs(v) < 1e-5f) continue;
                sb.Append($"{(f2 ? "" : ",")}\"{am.GetBlendShapeName(i)}\":{v.ToString("0.######", CultureInfo.InvariantCulture)}");
                f2 = false;
            }
            sb.Append("}}");
        }
        sb.Append("},\"bones\":{");
        for (int i = 0; i < sk.GetBoneCount(); i++)
            sb.Append($"{(i > 0 ? "," : "")}\"{sk.GetBoneName(i)}\":{X(sk.GetBoneGlobalPose(i))}");
        sb.Append('}');
        // Held pieces (Arms.Hold's mounts on BoneAttachment3Ds): each piece's skeleton-space transform (its bone's pose, the mount,
        // the piece) and its meshes' box in the piece's space, keyed by the mount's name and the piece's.
        sb.Append(",\"pieces\":{");
        bool fp = true;
        foreach (var att in sk.GetChildren().OfType<BoneAttachment3D>())
        {
            int b = sk.FindBone(att.BoneName);
            if (b < 0) continue;
            foreach (var mount in att.GetChildren().OfType<Node3D>().Where(m => m.Name.ToString().StartsWith(Play.GripSlide.MountPrefix)))
                foreach (var piece in mount.GetChildren().OfType<Node3D>())
                {
                    var t = sk.GetBoneGlobalPose(b) * mount.Transform * piece.Transform;
                    sb.Append($"{(fp ? "" : ",")}\"{mount.Name}/{piece.Name}\":{{\"x\":{X(t)},\"box\":{Box(piece)}}}");
                    fp = false;
                }
        }
        sb.Append("}}" + (char)10);
        System.IO.File.AppendAllText(fullPath, sb.ToString());
        if (skinDir != "" && !skinDone && f >= skinAt) { skinDone = true; P1MeshDump.Write(sk, skinDir, f); }
    }
}
