using Godot;
using System.Collections.Generic;

// Den r15 I: kit pieces (sticks, branch clusters, logs) the dressing placed that stand between the camera and her fade
// (GeometryInstance3D.Transparency, eased, no pop) while they overlap a screen disc round her and are nearer the camera.
public partial class DenOcclude : Node
{
    public static readonly float On = SurvivorUnchained.Args.Num("den-kit-occlude", 1f);
    static readonly float Fade = SurvivorUnchained.Args.Num("den-kit-occlude-a", 0.8f);

    class Piece { public MeshInstance3D M; public Aabb Box; public float T; public bool Ready; }
    readonly List<Piece> _p = new();
    static readonly StringName Param = "survivor";

    public static void Register(Node root, Node3D placed)
    {
        if (On < 0.5f || root == null || placed == null) return;
        var d = root.GetNodeOrNull<DenOcclude>("DenOcclude");
        if (d == null) { d = new DenOcclude { Name = "DenOcclude" }; root.AddChild(d); }
        d.Add(placed);
    }

    void Add(Node n)
    {
        if (n is MeshInstance3D mi && mi.Mesh != null && mi.CastShadow != GeometryInstance3D.ShadowCastingSetting.ShadowsOnly)
            _p.Add(new Piece { M = mi, Box = default });
        foreach (var ch in n.GetChildren()) Add(ch);
    }

    public override void _Process(double delta)
    {
        var cam = GetViewport()?.GetCamera3D();
        foreach (var q in _p) if (!q.Ready && q.M.IsInsideTree()) { q.Box = q.M.GlobalTransform * q.M.Mesh.GetAabb(); q.Ready = true; }   // (placed pieces are static; world box once the tree has them)
        if (cam == null || _p.Count == 0) return;
        var v = SurvivorUnchained.View.HouseFade.Her;
        bool here = v.W > 0.5f;
        var her = new Vector3(v.X, v.Y - 1.1f, v.Z);
        var camPos = cam.GlobalPosition;
        float dHer = camPos.DistanceTo(her);
        float k = 1f - Mathf.Exp(-(float)delta / 0.05f);   // ~0.15 s to settle
        // her screen disc: her height (about 1.8 m) plus a margin
        Vector2 sHer = Vector2.Zero; float rad = 0;
        bool ok = here && !cam.IsPositionBehind(her);
        if (ok)
        {
            sHer = cam.UnprojectPosition(her + new Vector3(0, 0.9f, 0));
            var top = cam.UnprojectPosition(her + new Vector3(0, 1.9f, 0));
            rad = Mathf.Max(60f, sHer.DistanceTo(top) * 1.15f);
        }
        foreach (var p in _p)
        {
            if (!p.Ready || !GodotObject.IsInstanceValid(p.M)) continue;
            float want = 0f;
            if (ok)
            {
                var b = p.Box;
                var cen = b.GetCenter();
                float ext = b.Size.Length() * 0.5f;
                // early-out: far from her in the world (a piece in front of her lies near the camera-her line)
                if (Mathf.Abs(cen.X - her.X) < 14f + ext && Mathf.Abs(cen.Z - her.Z) < 14f + ext
                    && camPos.DistanceTo(cen) - ext < dHer && !cam.IsPositionBehind(cen))
                {
                    var s = cam.UnprojectPosition(cen);
                    // screen radius of the piece: project one extent sideways
                    var s2 = cam.UnprojectPosition(cen + cam.GlobalBasis.X * ext);
                    float r = s.DistanceTo(s2);
                    if (s.DistanceTo(sHer) < rad + r) want = Fade;
                }
            }
            if (Mathf.Abs(p.T - want) < 0.002f && p.T == want) continue;
            p.T = Mathf.Abs(p.T - want) < 0.01f ? want : Mathf.Lerp(p.T, want, k);
            p.M.Transparency = p.T;
        }
    }
}
