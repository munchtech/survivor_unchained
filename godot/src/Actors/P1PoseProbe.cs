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
    int[] bones = System.Array.Empty<int>();
    Basis[] restInv = System.Array.Empty<Basis>();
    Vector3 crown;
    bool started;
    static bool truncated;

    public P1PoseProbe(Skeleton3D skeleton, Node3D actorRoot) { sk = skeleton; root = actorRoot; Name = "P1PoseProbe"; }

    public override void _Ready()
    {
        if (!truncated) { truncated = true; System.IO.File.WriteAllText(path, ""); }
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
    }
}
