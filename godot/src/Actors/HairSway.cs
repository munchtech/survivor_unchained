using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Her hair's swing, given to her hair's shader (shaders/heroine_hair.gdshader).
/// A style that hangs (a tail, a braid, long hair down her back) has a chain
/// (heroine_hair_&lt;style&gt;.chain.json, from tools/assets/heroine_hair.py):
/// a line of points down the middle of what hangs. Here it is a rope of
/// masses, pinned at its root, carried by its bone, falling under its own
/// weight, holding its length, drawn gently back toward how it hangs at rest,
/// and kept out of her head, neck and back; how far each point has swung
/// from where it would hang goes to the shader, which moves the hair along
/// it with it. So a stride, a stop or a turn sets it swinging, and when she
/// leans into a run it falls away from her back rather than through it.
/// A style without one (short hair) has a single mass on a spring below her
/// head, its lag moving the ends a little.
/// </summary>
public partial class HairSway : Node
{
    /// <summary>Her hairstyle (its chain's file).</summary>
    [Export] public string Style = "";
    /// <summary>Overall strength: 0 still, 1 as tuned.</summary>
    [Export] public float Amount = 1f;

    // The single mass: about one and a half swings a second, dying away over
    // two or three (hair is heavier and slower than flesh).
    const float Stiffness = 90f, Damping = 4.5f, Reach = 0.12f;
    // Where it hangs from her head, in her skeleton's space at rest (she
    // faces +Z): a hand below it and a little behind.
    static readonly Vector3 Hang = new(0, -0.25f, -0.08f);

    sealed class Ball { public int Bone; public Vector3 At; public float R; }

    MeshInstance3D? mesh;
    Skeleton3D? sk;
    int head = -1;
    Vector3 p, v;
    bool live;
    // The chain: its bone, its points at rest (skeleton space), now and a
    // step ago (world), its links' lengths, what it is kept out of.
    int bone = -1;
    float stiff;
    Vector3[] rest = [], x = [], xp = [];
    float[] link = [];
    Ball[] balls = [];

    public HairSway() { Name = "HairSway"; }

    public override void _Ready()
    {
        mesh = GetParent() as MeshInstance3D;
        sk = mesh?.GetParent() as Skeleton3D;
        if (sk == null) return;
        head = sk.FindBone("Head");
        var file = $"res://art/people/heroine_hair_{Style}.chain.json";
        if (Style == "" || !FileAccess.FileExists(file)) return;
        var d = Json.ParseString(FileAccess.GetFileAsString(file)).AsGodotDictionary();
        bone = sk.FindBone((string)d["bone"]);
        stiff = (float)d["stiff"];
        var pts = d["points"].AsGodotArray();
        rest = new Vector3[pts.Count];
        for (int i = 0; i < rest.Length; i++) rest[i] = Vec(pts[i]);
        link = new float[rest.Length];
        for (int i = 1; i < rest.Length; i++) link[i] = rest[i].DistanceTo(rest[i - 1]);
        var bs = d["spheres"].AsGodotArray();
        balls = new Ball[bs.Count];
        for (int i = 0; i < balls.Length; i++)
        {
            var b = bs[i].AsGodotDictionary();
            balls[i] = new Ball { Bone = sk.FindBone((string)b["bone"]), At = Vec(b["at"]), R = (float)b["r"] };
        }
    }

    static Vector3 Vec(Variant v)
    {
        var a = v.AsGodotArray();
        return new Vector3((float)a[0], (float)a[1], (float)a[2]);
    }

    /// <summary>A bone's move from rest, in the skeleton's space.</summary>
    Transform3D Moved(int b) => sk!.GetBoneGlobalPose(b) * sk.GetBoneGlobalRest(b).AffineInverse();

    public override void _Process(double delta)
    {
        if (mesh == null || sk == null || head < 0) return;
        float dt = Mathf.Clamp((float)delta, 0f, 1f / 20);
        var local = mesh.GlobalTransform.AffineInverse();
        var world = sk.GlobalTransform;
        var pose = sk.GetBoneGlobalPose(head);
        var sway = Vector3.Zero;
        var swung = new Vector3[8];
        if (bone >= 0 && rest.Length == 8)
        {
            var moved = world * Moved(bone);
            var target = new Vector3[8];
            for (int i = 0; i < 8; i++) target[i] = moved * rest[i];
            var at = new Vector3[balls.Length];
            for (int i = 0; i < balls.Length; i++) at[i] = world * (Moved(balls[i].Bone) * balls[i].At);
            if (!live || dt <= 0) { x = (Vector3[])target.Clone(); xp = (Vector3[])target.Clone(); live = true; }
            const int steps = 4;
            float h = dt / steps;
            var fall = new Vector3(0, -9.8f, 0) * h * h;
            for (int s = 0; s < steps; s++)
            {
                for (int i = 1; i < 8; i++)
                {
                    var was = x[i];
                    x[i] += (x[i] - xp[i]) * 0.985f + fall;
                    xp[i] = was;
                }
                x[0] = target[0];
                for (int k = 0; k < 3; k++)
                    for (int i = 1; i < 8; i++)
                    {
                        x[i] += (target[i] - x[i]) * stiff;
                        x[i] = x[i - 1] + (x[i] - x[i - 1]).Normalized() * link[i];
                        for (int b = 0; b < balls.Length; b++)
                        {
                            var off = x[i] - at[b];
                            float r = balls[b].R;
                            if (off.LengthSquared() < r * r) x[i] = at[b] + off.Normalized() * r;
                        }
                    }
            }
            for (int i = 0; i < 8; i++) swung[i] = local.Basis * (x[i] - target[i]) * Amount;
            if (OS.HasEnvironment("HAIRDEBUG") && Engine.GetProcessFrames() % 20 == 0)
            {
                float inside = 0;
                for (int i = 1; i < 8; i++)
                    for (int b = 0; b < balls.Length; b++)
                        inside = Mathf.Max(inside, balls[b].R - target[i].DistanceTo(at[b]));
                GD.Print($"HAIR swung {swung[7]} max-in {inside:F3} tgt7 {target[7]} x7 {x[7]}");
            }
        }
        else
        {
            var turned = pose.Basis * sk.GetBoneGlobalRest(head).Basis.Inverse();
            var target = world * (pose.Origin + turned * Hang);
            if (!live || dt <= 0) { p = target; v = Vector3.Zero; live = true; }
            const int steps = 4;
            float h = dt / steps;
            for (int i = 0; i < steps; i++)
            {
                v += (Stiffness * (target - p) - Damping * v) * h;
                p += v * h;
            }
            var off = p - target;
            if (off.Length() > Reach) { off = off.Normalized() * Reach; p = target + off; }
            sway = local.Basis * off * Amount;
        }
        var headAt = local * (world * pose.Origin);
        for (int s = 0; s < mesh.Mesh.GetSurfaceCount(); s++)
            if (mesh.GetSurfaceOverrideMaterial(s) is ShaderMaterial m)
            {
                m.SetShaderParameter(SwayName, sway);
                m.SetShaderParameter(HeadName, headAt);
                m.SetShaderParameter(ChainName, swung);
            }
    }

    // The parameters' names made once: a string given where a name is wanted
    // is a new name each call, and every frame's left for the collector.
    static readonly StringName SwayName = "sway", HeadName = "head", ChainName = "chain";
}
