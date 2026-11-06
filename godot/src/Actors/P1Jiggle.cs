using System.Linq;
using System.Text.Json;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// B's soft tissue (P1 R1 jiggle): Play/P1Springs on B's skeleton, from data (res://data/body/springs.json, the body
/// "p1"; the breast surface samples p1_spring_samples.json, tools/body/spring_samples.py). After P1Laws, before
/// HerFaceLife (P1Laws.Reorder keeps it there); replaces HerJiggle on B only (A keeps HerJiggle). Driven by her motion
/// in the world: the skeleton's global transform each frame carries her root motion, so a run, a stop, a dash's
/// landing and an attack's twist all reach the springs, each side on its own.
/// Armor: Support (0 bare .. 1 push-up) is the worn top's (HerWear sets it from ArmorHold.support, or derived from its
/// hold amount); SupportBottom the worn bottom's (TODO P2 gear: no bottom carries a hold yet, so it stays 0).
/// Support also drives B's shape: blend shapes form_support_lift / _press / _fill (build_topo stage 8) on every mesh
/// skinned to this skeleton that has them (absent: skipped silently); each defaults to the support value, a hold row
/// may set "lift"/"press"/"fill" per piece. Shot flag --p1-support X (0..1): the support starts at X (springs and
/// shapes) and armor gear does not override it.
/// </summary>
public partial class P1Jiggle : SkeletonModifier3D
{
    /// <summary>The worn top's support: 0 bare .. 1 push-up (stiffer, better damped, shorter reach; still moves).</summary>
    public float Support { get => (float)(springs?.Support["top"] ?? support); set { if (Flag != null) return; SetTop(value); } }
    void SetTop(float value) { support = value; if (springs != null) springs.Support["top"] = value; }
    /// <summary>The --p1-support shot flag (0..1), null when not given; pins the support against armor gear.</summary>
    public static readonly float? Flag = float.TryParse(SurvivorUnchained.Args.Get("p1-support"), System.Globalization.NumberStyles.Float,
        System.Globalization.CultureInfo.InvariantCulture, out var fl) ? Mathf.Clamp(fl, 0f, 1f) : null;
    float lift, press, fill;
    /// <summary>--p1-springs off (diagnostic shots): the springs held at their rest offsets, no swing, no squash.</summary>
    public static readonly bool FrozenFlag = SurvivorUnchained.Args.Get("p1-springs") == "off";
    /// <summary>The worn bottom's support for the glutes (TODO P2 gear: set where bottoms are equipped).</summary>
    public float SupportBottom { get => (float)(springs?.Support["bottom"] ?? supportBottom); set { supportBottom = value; if (springs != null) springs.Support["bottom"] = value; } }
    /// <summary>Overall strength (1 as tuned) and the squash and stretch along the bone (0 under formed plate).</summary>
    public float Amount = 1, Squash = 1;

    float support, supportBottom;
    P1Springs? springs;
    P1JiggleProbe? probe;
    P1M4[] g = System.Array.Empty<P1M4>();
    bool failed;

    public P1Jiggle() { Name = "P1Jiggle"; }

    /// <summary>One call for the armor code: the support on her skeleton's springs, if B's springs are there.</summary>
    public static void SetSupport(Skeleton3D sk, float top, float? bottom = null) => SetSupport(sk, top, bottom, top, top, top);

    /// <summary>Same, with the shape drivers apart from the springs' support (a piece's lift, press, fill; push-up 1/1/1).</summary>
    public static void SetSupport(Skeleton3D sk, float top, float? bottom, float lift, float press, float fill)
    {
        if (sk.GetNodeOrNull<P1Jiggle>("P1Jiggle") is not P1Jiggle j || Flag != null) return;
        j.Support = top;
        if (bottom is float b) j.SupportBottom = b;
        j.lift = lift; j.press = press; j.fill = fill;
        j.ApplyShapes(sk);
    }

    /// <summary>Set form_support_lift/_press/_fill on every mesh skinned to sk that has them.</summary>
    void ApplyShapes(Skeleton3D sk)
    {
        foreach (var mi in sk.GetParent()?.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>() ?? Enumerable.Empty<MeshInstance3D>())
        {
            if (mi.Mesh == null || mi.GetNodeOrNull<Skeleton3D>(mi.Skeleton) != sk) continue;
            int l = mi.FindBlendShapeByName("form_support_lift"), p = mi.FindBlendShapeByName("form_support_press"), f = mi.FindBlendShapeByName("form_support_fill");
            if (l >= 0) mi.SetBlendShapeValue(l, lift);
            if (p >= 0) mi.SetBlendShapeValue(p, press);
            if (f >= 0) mi.SetBlendShapeValue(f, fill);
        }
    }

    void Build(Skeleton3D sk)
    {
        try
        {
            using var doc = JsonDocument.Parse(FileAccess.GetFileAsString("res://data/body/springs.json"));
            var springsDoc = doc.RootElement.Clone();
            string samplesFile = springsDoc.GetProperty("bodies").GetProperty("p1").GetProperty("samples").GetString()!;
            JsonElement? samples = FileAccess.FileExists("res://data/body/" + samplesFile)
                ? JsonDocument.Parse(FileAccess.GetFileAsString("res://data/body/" + samplesFile)).RootElement : null;
            int n = sk.GetBoneCount();
            springs = new P1Springs(springsDoc, "p1", samples,
                Enumerable.Range(0, n).Select(i => sk.GetBoneName(i).ToString()).ToArray(),
                Enumerable.Range(0, n).Select(i => sk.GetBoneParent(i)).ToArray(),
                Enumerable.Range(0, n).Select(i => P1Body.M(sk.GetBoneGlobalRest(i))).ToArray());
            if (Flag is float fx) { SetTop(fx); SupportBottom = supportBottom; lift = press = fill = fx; }
            springs.Support["top"] = support; springs.Support["bottom"] = supportBottom;
            ApplyShapes(sk);
            g = Enumerable.Range(0, n).Select(_ => P1M4.Id).ToArray();
            if (Args.Has("p1-probe"))
            {
                probe = new P1JiggleProbe(sk);
                foreach (var sp in springs.Springs.Where(x => !x.Shift))
                {
                    var r = sk.GetBoneGlobalRest(sp.Bone).Basis.Orthonormalized();
                    GD.Print($"p1: rest {sp.Name} x {r.Column0:F2} y {r.Column1:F2} z {r.Column2:F2} tip {sp.Tip.X * 1000:F0},{sp.Tip.Y * 1000:F0},{sp.Tip.Z * 1000:F0}mm");
                }
            }
            if (Args.Has("p1-probe")) GD.Print($"p1: springs {string.Join(" ", springs.Springs.Select(s => $"{s.Name} {s.Freq:F2}Hz z{s.Zeta:F2} reach {s.Reach * 1000:F0}mm"))}; samples {(samples != null ? "on" : "off")}");
        }
        catch (System.Exception e)
        {
            failed = true;
            GD.PushError($"p1: springs off ({e.GetType().Name}: {e.Message})");
        }
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null || failed) return;
        if (springs == null) { Build(sk); if (springs == null) return; }
        springs.Amount = Amount; springs.Squash = Squash; springs.Frozen = FrozenFlag;
        foreach (int j in springs.Needed) g[j] = P1Body.M(sk.GetBoneGlobalPose(j));
        springs.Step(P1Body.M(sk.GlobalTransform), g, delta);
        foreach (var s in springs.Springs)
        {
            var L = springs.Local(s, g);
            var lin = L.Lin();
            sk.SetBonePosePosition(s.Bone, new Vector3((float)L[0, 3], (float)L[1, 3], (float)L[2, 3]));
            sk.SetBonePoseRotation(s.Bone, P1Body.T(P1M4.From(P1Retarget.Rot(L), new P1V(0, 0, 0))).Basis.GetRotationQuaternion());
            sk.SetBonePoseScale(s.Bone, new Vector3((float)lin.Col(0).Len(), (float)lin.Col(1).Len(), (float)lin.Col(2).Len()));
        }
        if (Args.Has("p1-clip"))
        {
            // every frame (r2): each spring's offset from rest |x-eq|, its up share and |x| (mm); the breasts in the arms
            var sb = new System.Text.StringBuilder($"p1: clip f {Engine.GetProcessFrames()}");
            foreach (var s in springs.Springs)
                sb.Append(System.FormattableString.Invariant($" {s.Name} {(s.X - s.Eq).Len() * 1000:F1}/{s.Rel.Y * 1000:F1}/{s.X.Len() * 1000:F1}"));
            foreach (double side in springs.Arms)
            {
                var c = springs.ArmClip(side, g);
                sb.Append(System.FormattableString.Invariant($" arm{(side > 0 ? "L" : "R")}breast {c.Depth * 1000:F1}mm/{c.N} own {c.Own * 1000:F1}/{c.OwnN} add {c.Added * 1000:F1}"));
            }
            GD.Print(sb.ToString());
        }
        if (Args.Has("p1-probe") && Engine.GetProcessFrames() % 120 == 0)
            GD.Print($"p1: springs frame {Engine.GetProcessFrames()} support {springs.Support["top"]:F2}: " +
                     string.Join(" ", springs.Springs.Select(s => $"{s.Name} {(s.X - s.Eq).Len() * 1000:F1}mm")) + " | " + probe?.Line(sk));
    }

    /// <summary>A push the springs feel at once (a landing, a blow), metres per second in the world.</summary>
    public void Kick(Vector3 velocity)
    {
        if (springs == null) return;
        foreach (var s in springs.Springs) s.V += new P1V(velocity.X, velocity.Y, velocity.Z);
    }
}
