using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// Her pectoral's pull on each breast as that arm rises (Armor 16): past about
/// horizontal the breast bone turns up and out toward the same side's armpit,
/// lifts a little and stretches along that line, narrowing in projection so
/// the volume holds. Per side, from the upper arm's elevation in her chest's
/// frame (Play/RaiseRamp). Runs before HerJiggle, so the springs follow the
/// raised pose and plate's hold still works; under plate (HerJiggle.Squash 0)
/// the cup moves rigidly and never stretches. Every top carries her skin
/// weights, so all of them follow. Arms down nothing changes.
/// Knobs: --raise-off, --raise-start/-full (deg), --raise-pitch/-yaw (deg),
/// --raise-up/-out/-back (m), --raise-sup/-sside (stretch), --raise-rigid (lift under plate), --raise-log;
/// the pec fold morphs (tools/assets/axilla_fold_post.py): --fold K, --crease K (strengths), --fold-off.
/// </summary>
public partial class HerRaise : SkeletonModifier3D
{
    public float Start = Args.Num("raise-start", -10f);
    public float Full = Args.Num("raise-full", 70f);
    public float Pitch = Args.Num("raise-pitch", 20f);
    public float Yaw = Args.Num("raise-yaw", 12f);
    public float Up = Args.Num("raise-up", 0.034f);
    public float Out = Args.Num("raise-out", 0.010f);
    public float Back = Args.Num("raise-back", 0.006f);
    public float StretchUp = Args.Num("raise-sup", 0.22f);
    public float StretchSide = Args.Num("raise-sside", 0.03f);
    /// <summary>How much of the lift a held top (plate) still makes.</summary>
    public float Rigid = Args.Num("raise-rigid", 0f);   // (0: steel cups are one rigid piece with the centre; at 0.5 a gap opened at full raise)
    readonly bool off = Args.Has("raise-off"), log = Args.Has("raise-log");

    int chest = -1;
    readonly int[] breast = { -1, -1 }, upper = { -1, -1 }, lower = { -1, -1 };
    double logT;

    public HerRaise() { Name = "HerRaise"; }

    readonly bool foldOff = Args.Has("fold-off");
    readonly float foldK = Args.Num("fold", 1f), creaseK = Args.Num("crease", 1f);
    // each mesh carrying the morphs (her body, and the cloth tops that follow it): its axilla_fold_l/r and
    // raise_crease_l/r indices (-1: none)
    System.Collections.Generic.List<(MeshInstance3D Mi, int[] Ix)>? folds;
    static readonly string[] FoldShapes = { "axilla_fold_l", "axilla_fold_r", "raise_crease_l", "raise_crease_r" };
    readonly float[] foldLast = { -1, -1, -1, -1 };
    double foldScan;

    /// <summary>One side's pec fold (w, on under steel too) and its crease (w times the lift's share).</summary>
    void SetFold(Skeleton3D sk, int side, float fold, float crease)
    {
        if (folds == null)
        {
            folds = new();
            foreach (var c in sk.GetChildren())
                if (c is MeshInstance3D mi && mi.Mesh != null && mi.FindBlendShapeByName("axilla_fold_l") >= 0)
                    folds.Add((mi, System.Array.ConvertAll(FoldShapes, n => mi.FindBlendShapeByName(n))));
            if (log) GD.Print($"raise: fold on {folds.Count} meshes: {string.Join(" ", folds.ConvertAll(f => f.Mi.Name.ToString()))}");
        }
        Set(side, foldOff ? 0 : fold * foldK);
        Set(side + 2, foldOff ? 0 : crease * creaseK);

        void Set(int k, float v)
        {
            if (v == foldLast[k]) return;
            foldLast[k] = v;
            foreach (var (mi, ix) in folds!)
                if (GodotObject.IsInstanceValid(mi) && ix[k] >= 0) mi.SetBlendShapeValue(ix[k], v);
        }
    }

    // --pose-dump PATH: every bone's skeleton-space pose after all her modifiers, rewritten each half second
    // (tools/assets/axilla_fold_post.py poses her body and tops with it to measure the fold and poke-through).
    readonly string? dumpPath = Args.Get("pose-dump");
    double dumpT;

    public override void _Ready()
    {
        if (dumpPath == null || GetSkeleton() is not Skeleton3D sk) return;
        sk.SkeletonUpdated += () =>
        {
            if ((dumpT += GetProcessDeltaTime()) < 0.5) return;
            dumpT = 0;
            var sb = new System.Text.StringBuilder("{");
            for (int b = 0; b < sk.GetBoneCount(); b++)
            {
                var t = sk.GetBoneGlobalPose(b);
                var c = System.Globalization.CultureInfo.InvariantCulture;
                string f(float v) => v.ToString("R", c);
                sb.Append(b > 0 ? "," : "").Append($"\"{sk.GetBoneName(b)}\":[{f(t.Basis.X.X)},{f(t.Basis.X.Y)},{f(t.Basis.X.Z)},{f(t.Basis.Y.X)},{f(t.Basis.Y.Y)},{f(t.Basis.Y.Z)},{f(t.Basis.Z.X)},{f(t.Basis.Z.Y)},{f(t.Basis.Z.Z)},{f(t.Origin.X)},{f(t.Origin.Y)},{f(t.Origin.Z)}]");
            }
            System.IO.File.WriteAllText(dumpPath, sb.Append('}').ToString());
        };
    }

    // her shoulder and armpit pose-space correctives (tools/assets/shoulder_psd_post.py, Play/ShoulderPsd): five shapes
    // per side from the upper arm's direction in her torso frame. --psd-off, --psd K (strength), --psd-log.
    readonly bool psdOff = Args.Has("psd-off"), psdLog = Args.Has("psd-log");
    readonly float psdK = Args.Num("psd", 1f);
    System.Collections.Generic.List<(MeshInstance3D Mi, int[] Ix)>? psd;
    static readonly int NS = ShoulderPsd.Shapes.Length;
    readonly float[] psdLast = new float[2 * NS];
    readonly float[] psdW = new float[NS];
    readonly int[] clav = { -1, -1 };
    readonly float[] clavRest = new float[2];
    int pelvis = -1, neck = -1;
    double psdLogT;

    void Psd(Skeleton3D sk, double delta)
    {
        if (pelvis < 0)
        {
            pelvis = sk.FindBone("pelvis"); neck = sk.FindBone("neck_01");
            clav[0] = sk.FindBone("clavicle_l"); clav[1] = sk.FindBone("clavicle_r");
            if (pelvis < 0 || neck < 0) return;
            // her clavicles' elevation at rest, in her rest torso frame (the shrug is read against it)
            var rdown = sk.GetBoneGlobalRest(pelvis).Origin - sk.GetBoneGlobalRest(neck).Origin;
            for (int i = 0; i < 2; i++)
                if (clav[i] >= 0 && upper[i] >= 0)
                {
                    var v = sk.GetBoneGlobalRest(upper[i]).Origin - sk.GetBoneGlobalRest(clav[i]).Origin;
                    clavRest[i] = ShoulderPsd.Elevation((v.X, v.Y, v.Z), (rdown.X, rdown.Y, rdown.Z));
                }
        }
        if (pelvis < 0 || neck < 0 || chest < 0) return;
        if (psd == null)
        {
            psd = new();
            var names = new string[2 * NS];
            for (int i = 0; i < NS; i++) { names[i] = ShoulderPsd.Shapes[i] + "_l"; names[NS + i] = ShoulderPsd.Shapes[i] + "_r"; }
            foreach (var c in sk.GetChildren())
                if (c is MeshInstance3D mi && mi.Mesh != null && mi.FindBlendShapeByName(names[0]) >= 0)
                    psd.Add((mi, System.Array.ConvertAll(names, n => mi.FindBlendShapeByName(n))));
            System.Array.Fill(psdLast, -1f);
            if (psdLog) GD.Print($"psd: on {psd.Count} meshes: {string.Join(" ", psd.ConvertAll(f => f.Mi.Name.ToString()))}");
        }
        var down = (sk.GetBoneGlobalPose(pelvis).Origin - sk.GetBoneGlobalPose(neck).Origin).Normalized();
        var left = sk.GetBoneGlobalPose(chest).Basis.X;
        var fwd = down.Cross(left);
        bool print = psdLog && (psdLogT += delta) > 0.1;
        if (print) psdLogT = 0;
        for (int i = 0; i < 2; i++)
        {
            if (upper[i] < 0 || lower[i] < 0) continue;
            var d = sk.GetBoneGlobalPose(lower[i]).Origin - sk.GetBoneGlobalPose(upper[i]).Origin;
            var lat = i == 0 ? left : -left;
            var (a, az) = ShoulderPsd.Angles((d.X, d.Y, d.Z), (down.X, down.Y, down.Z), (lat.X, lat.Y, lat.Z), (fwd.X, fwd.Y, fwd.Z));
            float rise = 0;
            if (clav[i] >= 0)
            {
                var c = sk.GetBoneGlobalPose(upper[i]).Origin - sk.GetBoneGlobalPose(clav[i]).Origin;
                rise = ShoulderPsd.Elevation((c.X, c.Y, c.Z), (down.X, down.Y, down.Z)) - clavRest[i];
            }
            ShoulderPsd.Weights(a, az, rise, psdW);
            if (print) GD.Print($"psd {(i == 0 ? "l" : "r")} A {a:0.0} az {az:0.0} rise {rise:0.0} w {string.Join(" ", System.Array.ConvertAll(psdW, x => x.ToString("0.00")))}");
            for (int k = 0; k < NS; k++)
            {
                float v = psdOff ? 0 : psdW[k] * psdK;
                int slot = NS * i + k;
                if (v == psdLast[slot]) continue;
                psdLast[slot] = v;
                foreach (var (mi, ix) in psd)
                    if (GodotObject.IsInstanceValid(mi) && ix[slot] >= 0) mi.SetBlendShapeValue(ix[slot], v);
            }
        }
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        if (chest < 0)
        {
            chest = sk.FindBone("spine_03");
            string[] s = { "l", "r" };
            for (int i = 0; i < 2; i++)
            {
                breast[i] = sk.FindBone("breast_" + s[i]);
                upper[i] = sk.FindBone("upperarm_" + s[i]);
                lower[i] = sk.FindBone("lowerarm_" + s[i]);
            }
        }
        if (chest < 0) return;
        if ((foldScan += delta) > 1) { foldScan = 0; folds = null; psd = null; System.Array.Fill(foldLast, -1f); }
        // (before the lift: the arms' direction is the clip's, which the lift doesn't move)
        Psd(sk, delta);
        if (off) return;
        // (her meshes change as tops are worn: the fold's and psd's meshes looked up again each second, above)
        float squash = sk.GetNodeOrNull<HerJiggle>("HerJiggle") is HerJiggle j ? j.Squash : 1f;
        var inv = sk.GetBoneGlobalPose(chest).AffineInverse();
        bool print = log && (logT += delta) > 0.1;
        if (print) logT = 0;
        for (int i = 0; i < 2; i++)
        {
            if (breast[i] < 0 || upper[i] < 0 || lower[i] < 0) continue;
            var dir = (inv * sk.GetBoneGlobalPose(lower[i]).Origin - inv * sk.GetBoneGlobalPose(upper[i]).Origin).Normalized();
            float el = RaiseRamp.Elevation(dir.Y);
            float w = RaiseRamp.Weight(el, Start, Full);
            if (print) GD.Print($"raise {(i == 0 ? "l" : "r")} el {el:0.0} w {w:0.00} squash {squash:0.00}");
            // her pec fold (heroine.glb's axilla_fold_l/r, tools/assets/axilla_fold_post.py), on under steel too
            SetFold(sk, i, w, w * Mathf.Lerp(Rigid, 1f, squash));
            if (w <= 0) continue;
            // Left is +X in her chest's frame. Breast bones are children of
            // spine_03, so their pose is already in the chest's frame.
            float side = i == 0 ? 1 : -1;
            // Under a held top (plate, Squash 0) the cups are one shell: they
            // lift a little with the pec but never splay apart.
            float held = Mathf.Lerp(Rigid, 1f, squash), splay = squash;
            var turn = new Quaternion(Vector3.Up, Mathf.DegToRad(Yaw * side * w * splay))
                     * new Quaternion(Vector3.Right, Mathf.DegToRad(-Pitch * w * held));
            int b = breast[i];
            sk.SetBonePosePosition(b, sk.GetBonePosePosition(b) + new Vector3(Out * side * splay, Up * held, -Back * held) * w);
            sk.SetBonePoseRotation(b, (turn * sk.GetBonePoseRotation(b)).Normalized());
            // Bone axes (build_heroine.py): X across, Y out along the breast, Z down the chest.
            var (sx, sy, sz) = RaiseRamp.Stretch(w * squash, StretchUp, StretchSide);
            sk.SetBonePoseScale(b, sk.GetBonePoseScale(b) * new Vector3(sx, sy, sz));
        }
    }
}
