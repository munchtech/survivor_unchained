using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A small unlit lamp-iron on a chain at the middle of the Warden's chest: the chain runs straight from
/// the collar to the hang point, and the lantern swings from there as a damped pendulum driven by the
/// hang point's own world acceleration (spring 30, damping 4, 25 degrees at most). Points are in the
/// package's bind-pose frame (glTF: Y up, metres, front +Z), measured on the ford_warden mesh: his tabard's front
/// is 0.157-0.166 m out at 1.22-1.30 m and his beard covers the chest above 1.46 m, so the lamp hangs on the
/// tabard below the beard, its ring 2 cm proud of the cloth, its chain running up under the beard to the collar.
/// They are turned into the bone's frame through the bone's own rest as the import has it (the glTF's 18 degree
/// spine_03 tilt did not survive import as the old bone-local offsets assumed: the lamp hung at his belt).
/// </summary>
public partial class Pendant : Node3D
{
    public static readonly Vector3 Hang = new(0, 1.335f, 0.182f), Collar = new(0, 1.455f, 0.112f);
    const float Spring = 30, Damping = 4, MaxTilt = 25 * Mathf.Pi / 180, LampScale = 0.35f, Drop = 0.09f, G = 9.8f;
    static StandardMaterial3D? chainMat;
    Vector2 tilt, spin;       // world-horizontal tilt (rad) of the lantern's bottom, and its rate
    Vector3 lastAt, lastV;
    bool primed;
    readonly Node3D lamp;

    public Pendant()
    {
        Name = "Pendant";
        lamp = LampIron.MakeWarden();
        lamp.Scale = Vector3.One * LampScale;
        lamp.Position = new Vector3(0, -Drop, 0);
        AddChild(lamp);
    }

    /// <summary>Hangs a pendant from the skeleton's bone (null when the skeleton has none of the names).</summary>
    public static Pendant? Attach(Skeleton3D skel, params string[] bones)
    {
        string? bone = null;
        foreach (var b in bones) if (skel.FindBone(b) >= 0) { bone = b; break; }
        if (bone == null) { GD.PushWarning("pendant: no chest bone"); return null; }
        var at = new BoneAttachment3D { Name = "PendantAt", BoneName = bone };
        skel.AddChild(at);
        var toBone = skel.GetBoneGlobalRest(skel.FindBone(bone)).AffineInverse();
        Vector3 hang = toBone * Hang, collar = toBone * Collar;
        chainMat ??= new StandardMaterial3D { AlbedoColor = new Color("#1e1c1a"), Metallic = 0.7f, Roughness = 0.4f };
        var d = collar - hang;
        var chain = new MeshInstance3D
        {
            Mesh = new CylinderMesh { TopRadius = 0.003f, BottomRadius = 0.003f, Height = d.Length(), RadialSegments = 5, Material = chainMat },
            Position = (collar + hang) / 2, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        };
        chain.Basis = new Basis(new Quaternion(Vector3.Up, d.Normalized()));
        at.AddChild(chain);
        var p = new Pendant { Position = hang };
        at.AddChild(p);
        return p;
    }

    public override void _Process(double delta)
    {
        if (delta <= 0) return;
        var at = GlobalPosition;
        var v = (at - lastAt) / (float)delta;
        var a = primed ? (v - lastV) / (float)delta : Vector3.Zero;
        lastAt = at; lastV = v; primed = true;
        var parent = GetParent<Node3D>();
        float s = parent.GlobalTransform.Basis.Scale.X;                  // world metres per local metre
        var ah = new Vector2(a.X, a.Z) / Mathf.Max(s, 1e-3f);
        if (ah.Length() > 30) ah = ah.Normalized() * 30;                 // a teleport or a cut is not a shove
        float h = Mathf.Min((float)delta, 1f / 60);
        // theta'' = -k (theta + a/g) - c theta': the bottom lags behind the hang point's push.
        spin += (-Spring * (tilt + ah / G) - Damping * spin) * h;
        tilt += spin * h;
        if (tilt.Length() > MaxTilt) { tilt = tilt.Normalized() * MaxTilt; spin = Vector2.Zero; }
        var down = new Vector3(tilt.X, -1, tilt.Y).Normalized();
        var rot = new Basis(new Quaternion(Vector3.Down, down));
        var yaw = new Basis(Vector3.Up, parent.GlobalRotation.Y);
        GlobalTransform = new Transform3D(rot * yaw * Basis.Identity.Scaled(Vector3.One * s), at);
    }
}
