using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// P1's body B (tools/body; published by tools/body/publish_p1.py into art/people/body_p1) in the game behind
/// --body p1; A (heroine.glb) stays the default and is untouched. Under the flag A is still loaded and still plays
/// every clip and layer (HerPose .. HerShoulder), its meshes left off; B's skeleton sits beside A's at the same place
/// and follows it each frame (P1Retarget's global match, then P1Rig's helpers and correctives: B's own laws, rig.json),
/// once A's pose is final (A's SkeletonUpdated). B's meshes are children of A's skeleton (every system that finds her
/// meshes there finds B's: face keys, blinks, paint), skinned by B's. Anything else laid on A's skeleton (hair, a hat)
/// is rebound to B with the transform that keeps it exactly where A draws it at rest: each bind's pose taken to
/// inverse(B rest) A rest pose (headbake.py's rule, for the meshes that were authored on A's +7% Head). Play tier:
/// play.glb's body beside it, drawn by HerLod's rule (in play beyond Far, --lod on/off), on a skeleton of its own
/// (play.glb's rest differs), driven the same way by play_rig.json. Derivation: (a) the owner's rule (A default, B
/// only behind a flag) and the gate's need; (c) inherited: HerLod's switch, headbake's transform.
/// </summary>
public static class P1Body
{
    public const string Dir = "res://art/people/body_p1/";
    /// <summary>--body p1, and a published B to load.</summary>
    public static bool On => Args.Get("body") == "p1" && ResourceLoader.Exists(Dir + "body.glb");
    static PackedScene? close, play;
    static readonly Dictionary<string, JsonDocument> rigs = new();

    static JsonElement Rig(string file)
    {
        if (!rigs.TryGetValue(file, out var d))
            rigs[file] = d = JsonDocument.Parse(FileAccess.GetFileAsString(Dir + file));
        return d.RootElement;
    }

    /// <summary>A's meshes off her skeleton, B's on (before People.Heroine lays her materials on what it finds).</summary>
    public static void Swap(Skeleton3D a)
    {
        foreach (var mi in a.GetChildren().OfType<MeshInstance3D>().ToList()) { a.RemoveChild(mi); mi.QueueFree(); }
        close ??= GD.Load<PackedScene>(Dir + "body.glb");
        var bc = Take(close, a, "P1Skeleton", null);
        P1Follow? playFollow = null;
        if (ResourceLoader.Exists(Dir + "play.glb"))
        {
            play ??= GD.Load<PackedScene>(Dir + "play.glb");
            var bp = Take(play, a, "P1PlaySkeleton", "Heroine");
            playFollow = new P1Follow(a, bp.Skel, Rig("play_rig.json"), bp.Meshes) { Name = "P1PlayFollow" };
        }
        var follow = new P1Follow(a, bc.Skel, Rig("rig.json"), bc.Meshes) { Name = "P1Follow", Play = playFollow };
        a.AddChild(follow);
        if (playFollow != null) a.AddChild(playFollow);
        GD.Print($"p1: B on her ({bc.Meshes.Count} meshes, {bc.Skel.GetBoneCount()} bones; play tier {(playFollow != null ? "on" : "none")})");
    }

    /// <summary>A B scene's skeleton laid beside A's (its own name, at A's place) and its meshes on A's skeleton,
    /// skinned by it; only: the one mesh kept (the play tier's body, renamed lod_p1_body, hidden till HerLod's rule).</summary>
    static (Skeleton3D Skel, List<MeshInstance3D> Meshes) Take(PackedScene ps, Skeleton3D a, string name, string? only)
    {
        var scene = ps.Instantiate<Node3D>();
        var b = (Skeleton3D)scene.FindChildren("*", "Skeleton3D", true, false)[0];
        var meshes = b.GetChildren().OfType<MeshInstance3D>().ToList();
        b.GetParent().RemoveChild(b);
        b.Owner = null;
        b.Name = name;
        a.AddChild(b);
        b.Transform = Transform3D.Identity;
        var kept = new List<MeshInstance3D>();
        foreach (var mi in meshes)
        {
            b.RemoveChild(mi);
            if (only != null && mi.Name != only) { mi.QueueFree(); continue; }
            mi.Owner = null;
            if (only != null) { mi.Name = "lod_p1_body"; mi.Visible = false; }
            a.AddChild(mi);
            mi.Skeleton = $"../{name}";
            mi.Layers = 2;
            kept.Add(mi);
        }
        scene.Free();
        return (b, kept);
    }

    public static P1M4 M(Transform3D t)
    {
        var m = P1M4.Id;
        var c = new[] { t.Basis.Column0, t.Basis.Column1, t.Basis.Column2 };
        for (int k = 0; k < 3; k++) { m[0, k] = c[k].X; m[1, k] = c[k].Y; m[2, k] = c[k].Z; }
        m[0, 3] = t.Origin.X; m[1, 3] = t.Origin.Y; m[2, 3] = t.Origin.Z;
        return m;
    }

    public static Transform3D T(P1M4 m) => new(
        new Basis(new Vector3((float)m[0, 0], (float)m[1, 0], (float)m[2, 0]), new Vector3((float)m[0, 1], (float)m[1, 1], (float)m[2, 1]),
                  new Vector3((float)m[0, 2], (float)m[1, 2], (float)m[2, 2])),
        new Vector3((float)m[0, 3], (float)m[1, 3], (float)m[2, 3]));
}

/// <summary>One B skeleton following A's (P1Body): the retarget, B's rig, its pose and shape weights written; and,
/// on the close one, whatever else is skinned to A (hair, hats) rebound to B, and the play tier's switch.</summary>
public partial class P1Follow : Node
{
    readonly Skeleton3D a, b;
    readonly P1Rig rig;
    readonly P1Retarget map;
    readonly List<MeshInstance3D> meshes;
    readonly P1M4[] aRest;
    readonly string[] aNames;
    public P1Follow? Play;
    MeshInstance3D? body;
    bool? playOn;
    static readonly string LodMode = Args.Get("lod") ?? "auto";
    /// <summary>The last frame's numbers (the probe): the pose write's worst shear residual (m-ish, the local
    /// recomposed against the driven world), and the shape weights.</summary>
    public double Residual;
    P1M4[]? restB;
    public Dictionary<string, double> Weights = new();

    public P1Follow(Skeleton3D a, Skeleton3D b, JsonElement rigJson, List<MeshInstance3D> meshes)
    {
        this.a = a; this.b = b; this.meshes = meshes;
        int nb = b.GetBoneCount(), na = a.GetBoneCount();
        var names = Enumerable.Range(0, nb).Select(i => b.GetBoneName(i)).ToArray();
        var parent = Enumerable.Range(0, nb).Select(i => b.GetBoneParent(i)).ToArray();
        var rest = Enumerable.Range(0, nb).Select(i => P1Body.M(b.GetBoneGlobalRest(i))).ToArray();
        rig = new P1Rig(names, parent, rest, rigJson);
        aNames = Enumerable.Range(0, na).Select(i => a.GetBoneName(i)).ToArray();
        aRest = Enumerable.Range(0, na).Select(i => P1Body.M(a.GetBoneGlobalRest(i))).ToArray();
        map = new P1Retarget(aNames, Enumerable.Range(0, na).Select(i => a.GetBoneParent(i)).ToArray(), aRest, rig);
        body = meshes.FirstOrDefault(m => m.Name == "Heroine" || m.Name == "lod_p1_body");
    }

    public override void _Ready()
    {
        a.SkeletonUpdated += Follow;
        Follow();
    }

    public override void _ExitTree() { a.SkeletonUpdated -= Follow; }

    void Follow()
    {
        if (Name == "P1PlayFollow" && body is { Visible: false }) return;   // (the play tier only while it draws)
        int na = aNames.Length;
        var aPose = new P1M4[na];
        for (int i = 0; i < na; i++) aPose[i] = P1Body.M(a.GetBoneGlobalPose(i));
        var (G, w) = rig.Drive(map.Map(aPose));
        double worst = 0;
        for (int j = 0; j < G.Length; j++)
        {
            int p = rig.Parent[j];
            var L = p < 0 ? G[j] : G[p].Inverse() * G[j];
            var lin = L.Lin();
            var sc = new Vector3((float)lin.Col(0).Len(), (float)lin.Col(1).Len(), (float)lin.Col(2).Len());
            var rot = P1Body.T(P1M4.From(P1Retarget.Rot(L), new P1V(0, 0, 0))).Basis.GetRotationQuaternion();
            b.SetBonePosePosition(j, new Vector3((float)L[0, 3], (float)L[1, 3], (float)L[2, 3]));
            b.SetBonePoseRotation(j, rot);
            b.SetBonePoseScale(j, sc);
            if (Args.Has("p1-probe"))
            {
                var back = new Basis(rot).Scaled(sc);
                var want = P1Body.T(L).Basis;
                worst = System.Math.Max(worst, (back.Column0 - want.Column0).Length() + (back.Column1 - want.Column1).Length() + (back.Column2 - want.Column2).Length());
            }
        }
        Residual = worst;
        Weights = w;
        foreach (var mi in meshes)
            foreach (var kv in w)
                if (mi.FindBlendShapeByName(kv.Key) is int k and >= 0) mi.SetBlendShapeValue(k, (float)kv.Value);
        if (Name != "P1Follow") return;
        if (Args.Has("p1-probe") && Engine.GetProcessFrames() % 120 == 0) Joints(aPose, G);
        Rebind();
        PlaySwitch();
    }

    /// <summary>Every mesh on A's skeleton still skinned by A (her hair, laid again at each restyle; a hat) taken onto
    /// B: each bind pose to inverse(B rest) A rest pose, so at rest it is exactly where A draws it, and it moves with the
    /// B bone that plays its A bone's part (P1Retarget.BFor; A's bones B lacks: the nearest ancestor B has).</summary>
    bool listed;

    void Rebind()
    {
        if (Args.Has("p1-probe") && !listed && Engine.GetProcessFrames() > 30)
        {
            listed = true;
            GD.Print("p1: on A's skeleton: " + string.Join(", ", a.GetChildren().OfType<MeshInstance3D>().Select(m => $"{m.Name}[{m.Skeleton}{(m.Visible ? "" : ",hidden")}]")));
        }
        foreach (var mi in a.GetChildren().OfType<MeshInstance3D>())
        {
            if (mi.Skeleton != new NodePath("..") || mi.Skin is not Skin skin) continue;
            // (only her hair and a head piece: whatever else is A's is cut from A's surface (her outfit's layers, the ink,
            // their merged draws) and is left off B until P1's outfit refit)
            bool hair = mi.GetChildren().OfType<HairSway>().Any(), head = mi.Name.ToString().Contains("_head_");
            if (!hair && !head) { if (mi.Visible) { mi.Visible = false; if (Args.Has("p1-probe")) GD.Print($"p1: {mi.Name} (A's) left off B"); } continue; }
            var nw = new Skin();
            for (int i = 0; i < skin.GetBindCount(); i++)
            {
                string nm = skin.GetBindName(i);
                int ai = nm != "" ? a.FindBone(nm) : skin.GetBindBone(i);
                int bi = -1, up = ai;
                while (up >= 0 && (bi = map.BFor[up]) < 0) up = a.GetBoneParent(up);
                if (ai < 0 || bi < 0) { nw.AddNamedBind(b.GetBoneName(0), skin.GetBindPose(i)); continue; }
                var pose = P1Body.T(rig.Rest[bi].Inverse() * aRest[ai] * P1Body.M(skin.GetBindPose(i)));
                nw.AddNamedBind(b.GetBoneName(bi), pose);
            }
            if (Args.Has("p1-probe")) HairFit(mi, skin, nw);
            mi.Skin = nw;
            mi.Skeleton = $"../{b.Name}";
            if (Args.Has("p1-probe")) GD.Print($"p1: {mi.Name} rebound to B ({skin.GetBindCount()} binds)");
        }
    }

    /// <summary>(--p1-probe) A mesh's rest world as A draws it (old skin, A's rest) against B (new skin, B's rest):
    /// the bounding boxes' corners and the worst vertex, mm.</summary>
    void HairFit(MeshInstance3D mi, Skin was, Skin now)
    {
        var arr = mi.Mesh.SurfaceGetArrays(0);
        var v = arr[(int)Mesh.ArrayType.Vertex].AsVector3Array();
        var bo = arr[(int)Mesh.ArrayType.Bones].AsInt32Array();
        var we = arr[(int)Mesh.ArrayType.Weights].AsFloat32Array();
        int per = bo.Length / v.Length;
        Vector3 Skinned(Skin sk, Skeleton3D on, int i)
        {
            var acc = Vector3.Zero;
            for (int k = 0; k < per; k++)
            {
                float wk = we[i * per + k];
                if (wk == 0) continue;
                int bind = bo[i * per + k];
                int bone = on.FindBone(sk.GetBindName(bind));
                if (bone < 0) bone = sk.GetBindBone(bind);
                acc += wk * (on.GetBoneGlobalRest(bone) * sk.GetBindPose(bind) * v[i]);
            }
            return acc;
        }
        Vector3 lo1 = Vector3.One * 1e9f, hi1 = -lo1, lo2 = lo1, hi2 = hi1;
        float worst = 0;
        for (int i = 0; i < v.Length; i++)
        {
            var p1 = Skinned(was, a, i); var p2 = Skinned(now, b, i);
            lo1 = lo1.Min(p1); hi1 = hi1.Max(p1); lo2 = lo2.Min(p2); hi2 = hi2.Max(p2);
            worst = Mathf.Max(worst, p1.DistanceTo(p2));
        }
        float box = Mathf.Max((lo1 - lo2).Abs().MaxAxisIndex() >= 0 ? (lo1 - lo2).Abs()[(int)(lo1 - lo2).Abs().MaxAxisIndex()] : 0,
                              (hi1 - hi2).Abs()[(int)(hi1 - hi2).Abs().MaxAxisIndex()]);
        GD.Print($"p1: hair fit {mi.Name}: {v.Length} verts, A box {hi1 - lo1} m, bbox corners off {box * 1000:F4} mm, worst vertex {worst * 1000:F4} mm");
    }

    /// <summary>(--p1-probe) B's joints against A's as posed, the A bones B has by name (limbs, hands, feet), mm:
    /// p95 and max, beside the same at rest (the bodies' own proportion difference).</summary>
    void Joints(P1M4[] aPose, P1M4[] G)
    {
        restB ??= rig.Drive(map.Map(aRest)).G;   // (B stood in A's rest: the bodies' own proportion difference)
        var posed = new List<double>(); var rest = new List<double>();
        foreach (var nm in new[] { "pelvis", "upperarm_l", "lowerarm_l", "hand_l", "calf_l", "foot_l" })
        {
            int ia = System.Array.IndexOf(aNames, nm), jb = rig.Index[nm];
            GD.Print($"p1: {nm} A rest {aRest[ia].T()} A pose {aPose[ia].T()} | B rest {rig.Rest[jb].T()} B@Arest {restB[jb].T()} B pose {G[jb].T()}");
        }
        for (int i = 0; i < aNames.Length; i++)
        {
            if (!rig.Index.TryGetValue(aNames[i], out int j) || rig.Helpers.Contains(j) || aNames[i].Contains("spine") || aNames[i].Contains("neck")) continue;
            posed.Add((G[j].T() - aPose[i].T()).Len() * 1000);
            rest.Add((restB![j].T() - aRest[i].T()).Len() * 1000);
        }
        double P(List<double> x, double q) { var s = x.OrderBy(t => t).ToList(); return s[(int)System.Math.Min(s.Count - 1, q * s.Count)]; }
        string top = string.Join(", ", Enumerable.Range(0, aNames.Length).Where(i => rig.Index.ContainsKey(aNames[i]) && !rig.Helpers.Contains(rig.Index[aNames[i]]))
            .OrderByDescending(i => (G[rig.Index[aNames[i]]].T() - aPose[i].T()).Len() - (restB[rig.Index[aNames[i]]].T() - aRest[i].T()).Len()).Take(4)
            .Select(i => $"{aNames[i]} {(G[rig.Index[aNames[i]]].T() - aPose[i].T()).Len() * 1000:F0}/{(restB[rig.Index[aNames[i]]].T() - aRest[i].T()).Len() * 1000:F0}"));
        GD.Print($"p1: joints t={Time.GetTicksMsec() / 1000.0:F1}s {posed.Count} bones: posed p95 {P(posed, 0.95):F1} max {posed.Max():F1} mm; rest p95 {P(rest, 0.95):F1} max {rest.Max():F1} mm; " +
                 $"worst grown (posed/rest mm): {top}; shear residual {Residual:E1}; weights {string.Join(" ", Weights.Where(k => k.Value > 0.001).Select(k => $"{k.Key}={k.Value:F2}"))}");
    }

    /// <summary>HerLod's rule for the play tier: in play (no held camera) beyond Far, back within Near; --lod on|off.</summary>
    void PlaySwitch()
    {
        if (Play?.body is not MeshInstance3D lod || body == null) return;
        bool want = LodMode == "on";
        if (LodMode == "auto" && (HerLod.InPlay || HerLod.FilmFollows) && GetViewport()?.GetCamera3D() is Camera3D cam)
        {
            float d = cam.GlobalPosition.DistanceTo(a.GlobalPosition + Vector3.Up);
            want = playOn == true ? d > HerLod.Near : d > HerLod.Far;
        }
        if (want != playOn)
        {
            playOn = want;
            lod.Visible = want;
            body.Visible = !want;
            if (Args.Has("p1-probe")) GD.Print($"p1: {(want ? "play" : "close")} tier");
        }
        if (want)
            for (int s = 0; s < lod.Mesh.GetSurfaceCount() && s < body.Mesh.GetSurfaceCount(); s++)
                if (lod.GetSurfaceOverrideMaterial(s) != body.GetSurfaceOverrideMaterial(s)) lod.SetSurfaceOverrideMaterial(s, body.GetSurfaceOverrideMaterial(s));
    }
}
