using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// Weapons worth holding (res://assets/weapons: Sketchfab CC-BY/CC0, see
/// public/assets/CREDITS.md), each turned and scaled to one convention so
/// any hand can take any of them, as the web game does (src/render/arms.ts):
/// +Y the shaft from the grip out, the grip at the origin; +X the blade's
/// width; +Z its thickness. The model's principal axes say which way it
/// lies; what they cannot (which end is the grip, where the hand goes, its
/// length in life) is written per weapon.
/// </summary>
public static class Arms
{
    /// <summary>A weapon: its file (and the node in it, where a file holds
    /// several), its length in life, where along it the hand grips (0 the
    /// butt, 1 the tip); held pistol-fashion (a crossbow) or not.</summary>
    /// Or made in code (Build), not read from a file.
    /// Lean: degrees its shaft leans in a diagonal grip, from square to the
    /// fingers toward them (a sword's grip runs from the root of the
    /// forefinger to the heel of the hand), for those whose own clips are
    /// keyed to it (tools/anim/keyed.py GRIP), not the library's.
    public sealed record Spec(string File, float Length, float Grip, bool Flip = false, float Roll = 0, string? Node = null, bool Pistol = false, Func<Node3D>? Build = null, float Lean = 0, WeaponKind Kind = WeaponKind.None);

    public static readonly Dictionary<string, Spec> All = new()
    {
        ["chevalier_sword"] = new("chevalier_sword", 1.0f, 0.1f, Lean: 35, Kind: WeaponKind.Blade1H),
        ["viking_sword"] = new("viking_sword", 0.92f, 0.13f, Lean: 35, Kind: WeaponKind.Blade1H),
        ["longsword"] = new("longsword", 1.05f, 0.22f, Flip: true, Lean: 35, Kind: WeaponKind.Blade1H),
        ["zweihander"] = new("zweihander", 1.6f, 0.2f, Kind: WeaponKind.Blade2H),
        ["mace"] = new("mace", 0.75f, 0.12f, Lean: 30, Kind: WeaponKind.Blunt),
        ["viking_axe"] = new("viking_axe", 0.8f, 0.15f, Roll: Mathf.Pi, Lean: 30, Kind: WeaponKind.Axe),
        ["snake_axe"] = new("snake_axe", 1.3f, 0.22f, Lean: 30, Kind: WeaponKind.Axe2H),
        ["mage_staff"] = new("mage_staff", 1.75f, 0.45f, Kind: WeaponKind.Staff),
        ["short_staff"] = new("mage_staff", 1.1f, 0.3f, Kind: WeaponKind.Staff),
        ["crossbow"] = new("crossbow", 0.85f, 0.3f, Pistol: true, Kind: WeaponKind.Crossbow),
        ["wand"] = new("", 0.38f, 0.12f, Build: Made.Wand, Lean: 30, Kind: WeaponKind.Wand),
        ["shield_round"] = new("shield_round", 0.66f, 0.5f, Kind: WeaponKind.Shield),
        ["daggers"] = new("daggers", 0.4f, 0.2f, Node: "Cube_004", Lean: 30, Kind: WeaponKind.Dagger),
        ["dagger_b"] = new("daggers", 0.4f, 0.2f, Node: "Cube_004_01", Lean: 30, Kind: WeaponKind.Dagger),
    };

    /// <summary>A weapon, normalised (a new node each call).</summary>
    public static Node3D Make(string id)
    {
        var spec = All[id];
        var model = spec.Build?.Invoke() ?? GD.Load<PackedScene>($"res://assets/weapons/{spec.File}.glb").Instantiate<Node3D>();
        if (spec.Node != null)
        {
            // One weapon of several in the file: the rest go (the meshes
            // not under the node named, however deep).
            void Keep(Node n, bool wanted)
            {
                foreach (var c in n.GetChildren())
                {
                    bool mine = wanted || c.Name == spec.Node;
                    if (c is MeshInstance3D m && !mine) { m.QueueFree(); m.GetParent().RemoveChild(m); continue; }
                    Keep(c, mine);
                }
            }
            Keep(model, false);
        }
        var pts = new List<Vector3>();
        Transform3D? aGrip = null, aSheath = null;
        var tag = WeaponKind.None;
        void Walk(Node n, Transform3D at)
        {
            foreach (var c in n.GetChildren())
            {
                var t = c is Node3D c3 ? at * c3.Transform : at;
                // Anchors (Marionette exports carry them) and a kind tag (a glTF extra "kind", or a node named kind_<kind>).
                if (c is Node3D)
                {
                    if (c.Name.ToString().StartsWith("anchor_grip")) aGrip = t;
                    else if (c.Name.ToString().StartsWith("anchor_sheath")) aSheath = t;
                    else if (c.Name.ToString().StartsWith("kind", StringComparison.OrdinalIgnoreCase)) tag = WeaponSockets.Parse(c.Name);
                }
                if (c.HasMeta("extras") && c.GetMeta("extras").Obj is Godot.Collections.Dictionary ex && ex.ContainsKey("kind"))
                    tag = WeaponSockets.Parse(ex["kind"].ToString());
                if (c is MeshInstance3D mi && mi.Mesh != null)
                    for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                        foreach (var v in (Vector3[])mi.Mesh.SurfaceGetArrays(s)[(int)Mesh.ArrayType.Vertex]) pts.Add(t * v);
                Walk(c, t);
            }
        }
        Walk(model, Transform3D.Identity);
        var (axes, mean) = Principal(pts);
        var (lng, mid) = (axes[0], axes[1]);
        // An anchor's -Y runs down the blade or haft toward the tip: it is the shaft itself (not just which way is out),
        // over the bounds' axis, which leans with whatever else the mesh carries, and over the Spec's Flip.
        if ((aGrip ?? aSheath) is { } tipAnchor)
        {
            static System.Numerics.Vector3 N(Vector3 v) => new(v.X, v.Y, v.Z);
            var (l, m) = WeaponSockets.ShaftAxes(N(lng), N(mid), N(-tipAnchor.Basis.Y));
            (lng, mid) = (new Vector3(l.X, l.Y, l.Z), new Vector3(m.X, m.Y, m.Z));
        }
        else if (spec.Flip) lng = -lng;
        var shrt = mid.Cross(lng);
        // Extent along each new axis, and its middle.
        var basis = new[] { mid, lng, shrt };
        var lo = new float[] { float.MaxValue, float.MaxValue, float.MaxValue };
        var hi = new float[] { float.MinValue, float.MinValue, float.MinValue };
        foreach (var p in pts)
            for (int a = 0; a < 3; a++) { var d = p.Dot(basis[a]); lo[a] = Mathf.Min(lo[a], d); hi[a] = Mathf.Max(hi[a], d); }
        var centre = Vector3.Zero;
        for (int a = 0; a < 3; a++) centre += basis[a] * (lo[a] + hi[a]) / 2;
        // Rows of the turn: model axes -> (X = mid, Y = long, Z = short).
        var turn = new Basis(mid, lng, shrt).Transposed();
        if ((aGrip ?? aSheath) is { } faceAnchor)
        {
            // An anchor's +Z is the edge or face direction: turned about the shaft to land on the piece's +Z.
            var f = turn * faceAnchor.Basis.Z;
            if (Mathf.Abs(f.X) + Mathf.Abs(f.Z) > 1e-4f) turn = new Basis(Vector3.Up, Mathf.Atan2(-f.X, f.Z)) * turn;
        }
        else if (spec.Roll != 0) turn = new Basis(Vector3.Up, spec.Roll) * turn;
        float k = spec.Length / (hi[1] - lo[1]);
        var inner = new Node3D { Name = "inner" };
        model.Position = -centre;
        inner.AddChild(model);
        inner.Basis = turn.Scaled(Vector3.One * k);
        // The grip is the origin: the anchor if the asset has one, else the Spec's Grip along the long axis.
        inner.Position = aGrip is { } g ? -(turn * (g.Origin - centre)) * k : new Vector3(0, spec.Length * (0.5f - spec.Grip), 0);
        var holder = new Node3D { Name = $"arm:{id}" };
        holder.AddChild(inner);
        // The sheath point (where the piece hangs from; the grip when there is no anchor for it) and the tip's height on the shaft.
        holder.SetMeta("sheath", aSheath is { } sa ? turn * (sa.Origin - centre) * k + inner.Position : Vector3.Zero);
        holder.SetMeta("tip", inner.Position.Y + spec.Length / 2);
        holder.SetMeta("kind", (int)(tag != WeaponKind.None ? tag : spec.Kind));
        if (aGrip != null) holder.SetMeta("anchored", true);
        return holder;
    }

    /// <summary>Principal axes of a point cloud, longest spread first, each
    /// signed to agree with the file axis it lies nearest.</summary>
    static (Vector3[] Axes, Vector3 Mean) Principal(List<Vector3> pts)
    {
        var mean = Vector3.Zero;
        foreach (var p in pts) mean += p / pts.Count;
        var c = new double[3, 3];
        foreach (var p in pts)
        {
            var d = p - mean;
            double[] v = { d.X, d.Y, d.Z };
            for (int a = 0; a < 3; a++) for (int b = 0; b < 3; b++) c[a, b] += v[a] * v[b] / pts.Count;
        }
        var (values, vectors) = Jacobi(c);
        var order = new[] { 0, 1, 2 };
        Array.Sort(order, (a, b) => values[b].CompareTo(values[a]));
        var axes = new Vector3[3];
        for (int i = 0; i < 3; i++)
        {
            int k = order[i];
            var e = new Vector3((float)vectors[0, k], (float)vectors[1, k], (float)vectors[2, k]).Normalized();
            var big = new[] { Mathf.Abs(e.X), Mathf.Abs(e.Y), Mathf.Abs(e.Z) };
            int at = Array.IndexOf(big, Mathf.Max(big[0], Mathf.Max(big[1], big[2])));
            if (e[at] < 0) e = -e;
            axes[i] = e;
        }
        return (axes, mean);
    }

    /// <summary>Eigen-decomposition of a symmetric 3x3 (cyclic Jacobi);
    /// eigenvectors in the columns.</summary>
    static (double[] Values, double[,] Vectors) Jacobi(double[,] a0)
    {
        var a = (double[,])a0.Clone();
        var vec = new double[,] { { 1, 0, 0 }, { 0, 1, 0 }, { 0, 0, 1 } };
        var pairs = new[] { (0, 1), (0, 2), (1, 2) };
        for (int sweep = 0; sweep < 32; sweep++)
        {
            if (a[0, 1] * a[0, 1] + a[0, 2] * a[0, 2] + a[1, 2] * a[1, 2] < 1e-18) break;
            foreach (var (p, q) in pairs)
            {
                if (Math.Abs(a[p, q]) < 1e-14) continue;
                double theta = (a[q, q] - a[p, p]) / (2 * a[p, q]);
                double t = Math.Sign(theta == 0 ? 1 : theta) / (Math.Abs(theta) + Math.Sqrt(theta * theta + 1));
                double cs = 1 / Math.Sqrt(t * t + 1), sn = t * cs;
                for (int k = 0; k < 3; k++) { double akp = a[k, p], akq = a[k, q]; a[k, p] = cs * akp - sn * akq; a[k, q] = sn * akp + cs * akq; }
                for (int k = 0; k < 3; k++) { double apk = a[p, k], aqk = a[q, k]; a[p, k] = cs * apk - sn * aqk; a[q, k] = sn * apk + cs * aqk; }
                for (int k = 0; k < 3; k++) { double vkp = vec[k, p], vkq = vec[k, q]; vec[k, p] = cs * vkp - sn * vkq; vec[k, q] = sn * vkp + cs * vkq; }
            }
        }
        return (new[] { a[0, 0], a[1, 1], a[2, 2] }, vec);
    }

    /// <summary>Mount a weapon in a person's hand (or a shield on the
    /// forearm), the way the web game's sockets hold them: in the hand's
    /// space the fingers run +Y and the thumb side is +Z.</summary>
    public static Node3D Hold(People.Person person, string id, string bone = "hand_r")
    {
        var att = new BoneAttachment3D { BoneName = bone };
        person.Skeleton.AddChild(att);
        var mount = new Node3D { Name = $"mount:{bone}" };
        att.AddChild(mount);
        mount.Transform = MountTransform(id, bone, person.Own != null);
        var w = Make(id);
        w.Transform = Seat(w, id, bone);
        mount.AddChild(w);
        return mount;
    }

    /// <summary>A held piece's place inside its mount (Hold's and ArmsDump's): PieceTransform, and for a piece with an
    /// anchor_grip in her right hand the fist's seat (WeaponSockets.FistSeat): its grip point on the fist's pocket and its
    /// shaft along the fist's line, so the anchor rule stays "origin on the shaft where the fist grips, -Y down the shaft".
    /// Not for a pistol-held piece (its stock sits on the fist) or the forearm. hand_l: its pocket isn't measured yet (the
    /// left mount isn't mirrored either), so a left-hand piece keeps the plain mount.</summary>
    public static Transform3D Seat(Node3D piece, string id, string bone)
    {
        var t = PieceTransform(id);
        if (bone != "hand_r" || All[id].Pistol || !piece.HasMeta("anchored")) return t;
        var m0 = MountTransform(id, bone, false);
        static System.Numerics.Vector3 N(Vector3 v) => new(v.X, v.Y, v.Z);
        var (q, at) = WeaponSockets.FistSeat(N(m0.Basis.X), N(m0.Basis.Y), N(m0.Basis.Z), N(m0.Origin));
        return new Transform3D(new Basis(new Quaternion(q.X, q.Y, q.Z, q.W)), new Vector3(at.X, at.Y, at.Z)) * t;
    }

    /// <summary>Where the mount sits in its bone's space (Hold's, and
    /// tools_scenes/ArmsDump.cs's, so the two cannot drift). `own`: her
    /// or the hero, who hold the diagonal grip their clips are keyed to.</summary>
    public static Transform3D MountTransform(string id, string bone, bool own)
    {
        bool forearm = bone.StartsWith("lowerarm");
        var x = new Vector3(0, 1, 0);
        var y = forearm ? new Vector3(0, 0, -1) : new Vector3(0, 0, 1);
        var basis = new Basis(x, y, x.Cross(y));
        // Her and the hero hold it in the diagonal grip their clips are keyed
        // to: the shaft turned about the hand's across axis toward the fingers.
        if (!forearm && own && All[id].Lean != 0)
            basis = new Basis(Vector3.Right, Mathf.DegToRad(-All[id].Lean)) * basis;
        // Her and the hero: the shield sits on the back of the forearm, not on its axis.
        var at = forearm ? new Vector3(own ? -ShieldOff : 0, own ? ShieldAlong : 0.14f, 0) : new Vector3(-0.025f, 0.075f, 0);
        return new Transform3D(basis, at);
    }

    /* ------------------------------------------------------------ sheathed -- */

    /// <summary>Where her pieces ride when she is sheathed (in town), by KIND of weapon (Spec.Kind, or an asset's own
    /// tag), never by item: a new asset needs only its Spec row. One table of named sockets (WeaponSockets.SocketOf says
    /// which kind rides in which), tuned from the sheets (tools_scenes/anim_review.gd, SHEATH=1). Each row is written in
    /// skeleton space at rest (+Y up, +Z her front, +X her left) as a mount would stand: the piece's SHEATH POINT (its
    /// anchor_sheath node, else its grip) at `At`, the shaft (the piece's +Y, toward the tip) along `Shaft`, its thickness
    /// (the piece's +Z: the shield's face, an edge's side, a scabbard's outer side) toward `Thick`. A pistol-fashion
    /// piece (the crossbow) is given by its stock instead (the piece's +Y turned to the mount's +X, see PieceTransform):
    /// `Shaft` the stock's run, `Thick` its top. `Normal` is the way out of her body there: the socket is pushed out along it
    /// by the worn outfit's thickness (art/anim/socket_clearance.json, filled by tools/anim/armscheck.py --sockets).
    /// Mirrors: a piece in her left hand rides on the other side (a pair of daggers, a sword in the left).
    /// Sheathed() turns the row into the bone's space.</summary>
    sealed record Socket(string Bone, Vector3 At, Vector3 Shaft, Vector3 Thick, Vector3 Normal, bool Mirrors = false);

    static readonly Dictionary<string, Socket> Sockets = new()
    {
        // Shield: across the back, its boss centred between the shoulder blades 0.14 m behind spine_03, face out
        // (back), its top rim under the neck (66 cm across).
        [WeaponSockets.Back] = new("spine_03", new(0, 1.22f, -0.20f), new(0, 1, 0), new(0, 0, -1), new(0, 0, -1)),
        // One-handed blade: left hip, in the scabbard (MakeSheathed), hilt forward and up, blade down and back about
        // 30 degrees off vertical, flat to her side (thickness out).
        [WeaponSockets.HipBlade] = new("pelvis", new(0.21f, 1.20f, 0.10f), new(0.08f, -0.87f, -0.50f), new(1, 0, 0), new(1, 0, 0), Mirrors: true),
        // Blunt and axe: right hip loop, head up, the haft down along the outside of the thigh (left hand: mirrored).
        [WeaponSockets.HipLoop] = new("pelvis", new(-0.19f, 0.50f, 0.0f), new(0.06f, 1, 0), new(-1, 0, 0), new(-1, 0, 0), Mirrors: true),
        // Wand: right hip, tucked in the belt, crystal up, leaning in and forward.
        [WeaponSockets.HipBelt] = new("pelvis", new(-0.18f, 1.14f, 0.05f), new(0.15f, 0.95f, 0.25f), new(-1, 0, 0), new(-1, 0, 0), Mirrors: true),
        // Dagger: the back of the belt, flat, one each side of the spine, hilts out and blades crossing.
        [WeaponSockets.BeltBack] = new("pelvis", new(-0.17f, 1.12f, -0.13f), new(1, 0, 0), new(0, 0, -1), new(0, 0, -1), Mirrors: true),
        // Crossbow: slung across the back, stock rising to her right shoulder, its top out of the back.
        [WeaponSockets.Sling] = new("spine_03", new(0.10f, 1.16f, -0.17f), new(-0.6f, 0.8f, 0), new(0, 0, -1), new(0, 0, -1)),
        // Two-handed blade or axe: diagonal across the back like the sling, hilt or haft over her right shoulder (the
        // grip high on the right), the tip down toward her left hip, flat to her back.
        [WeaponSockets.BackDiag] = new("spine_03", new(-0.07f, 1.30f, -0.20f), new(0.25f, -0.97f, 0), new(0, 0, -1), new(0, 0, -1)),
    };

    static WeaponSockets.Clearance? clearance;

    /// <summary>The clearance file, read once (art/anim/socket_clearance.json); absent: no clearance anywhere.</summary>
    static WeaponSockets.Clearance Clearance => clearance ??= WeaponSockets.Clearance.Parse(
        FileAccess.FileExists("res://art/anim/socket_clearance.json") ? FileAccess.GetFileAsString("res://art/anim/socket_clearance.json") : null);

    /// <summary>What a piece is: its tag in the asset if it has one, else the Spec's Kind.</summary>
    public static WeaponKind KindOf(string id) => (WeaponKind)Info(id).Kind;

    sealed record Facts(int Kind, Vector3 Sheath, float Tip);
    static readonly Dictionary<string, Facts> facts = new();

    static Facts Info(string id)
    {
        if (!facts.TryGetValue(id, out var m))
        {
            var w = Make(id);
            facts[id] = m = new Facts((int)w.GetMeta("kind"), (Vector3)w.GetMeta("sheath"), (float)w.GetMeta("tip"));
            w.Free();
        }
        return m;
    }

    /// <summary>The bones' rest poses in skeleton space (heroine, tools/anim/data/heroine_skeleton.json): the
    /// origin and the turn about X; the hero's pelvis and spine differ by a few degrees.</summary>
    static Transform3D RestOf(string bone) => bone == "pelvis"
        ? new Transform3D(new Basis(Vector3.Right, Mathf.DegToRad(20.6f)), new Vector3(0, 1.0723f, 0))
        : new Transform3D(new Basis(Vector3.Right, Mathf.DegToRad(-18.4f)), new Vector3(0, 1.3335f, 0.0364f));

    /// <summary>Where her piece rides sheathed: the bone and the mount's transform in its space (as
    /// MountTransform's), or null if it stays in her hand. `left`: it was in her left hand.</summary>
    public static (string Bone, Transform3D At)? Sheathed(string id, bool left = false, string? outfit = null)
    {
        if (WeaponSockets.SocketOf(KindOf(id)) is not { } name) return null;
        var k = Sockets[name];
        var at = k.At; var shaft = k.Shaft; var thick = k.Thick; var normal = k.Normal;
        if (left && k.Mirrors) { at.X = -at.X; shaft.X = -shaft.X; thick.X = -thick.X; normal.X = -normal.X; }
        // Out of her body by the worn outfit's thickness (outfit null: the bare socket, as ArmsDump and armscheck want it).
        if (outfit != null) at += normal * Clearance.Metres(outfit, name);
        shaft = shaft.Normalized();
        thick = (thick - shaft * thick.Dot(shaft)).Normalized();
        var third = shaft.Cross(thick);
        // (Pistol-fashion: the mount's X runs the stock, its Y the top.)
        var basis = All[id].Pistol
            ? new Basis(shaft, thick, shaft.Cross(thick))
            : new Basis(third, shaft, thick);
        return (k.Bone, RestOf(k.Bone).AffineInverse() * new Transform3D(basis, at));
    }

    /// <summary>The socket a piece rides in and the way out of her body there, in the socket bone's space (what
    /// tools_scenes/ArmsDump.cs writes for armscheck.py --sockets), or null if it stays in her hand.</summary>
    public static (string Socket, Vector3 Normal)? SocketFacing(string id, bool left = false)
    {
        if (WeaponSockets.SocketOf(KindOf(id)) is not { } name) return null;
        var k = Sockets[name];
        var n = k.Normal;
        if (left && k.Mirrors) n.X = -n.X;
        return (name, RestOf(k.Bone).AffineInverse().Basis * n);
    }

    /// <summary>Mount a weapon at its sheathed socket (a sword with its scabbard), or null if it has none.</summary>
    public static Node3D? HoldSheathed(People.Person person, string id, bool left) => HoldSheathed(person.Skeleton, id, left, person.Calling);

    /// <summary>The same on a bare skeleton, for an outfit's calling ("" none): what tools_scenes/SheathedReview.cs
    /// mounts for the review sheets (anim_review.gd, SHEATH=1), so the sheets show the game's piece.</summary>
    public static Node3D? HoldSheathed(Skeleton3D skeleton, string id, bool left, string? calling)
    {
        if (Sheathed(id, left, calling ?? "") is not { } sock) return null;
        var (bone, at) = sock;
        var att = new BoneAttachment3D { BoneName = bone };
        skeleton.AddChild(att);
        var mount = new Node3D { Name = $"sheathed:{bone}" };
        att.AddChild(mount);
        mount.Transform = at;
        mount.AddChild(MakeSheathed(id));
        return mount;
    }

    /// <summary>A piece as it rides sheathed, in its mount's space, its sheath point (anchor_sheath, else the grip) at
    /// the origin: the weapon, and for a one-handed blade its scabbard from the guard round the blade to a thumb past
    /// its tip (WeaponSockets.BladeLength; also what ArmsDump writes).</summary>
    public static Node3D MakeSheathed(string id)
    {
        var root = new Node3D { Name = "sheathed" };
        var info = Info(id);
        var w = Make(id);
        w.Transform = PieceTransform(id);
        root.AddChild(w);
        if (Scabbarded(KindOf(id)))
        {
            const float guard = 0.10f;
            var sc = Made.Scabbard(WeaponSockets.BladeLength(info.Tip, info.Sheath.Y, guard));
            sc.Position = new Vector3(0, info.Sheath.Y + guard, 0);
            root.AddChild(sc);
        }
        var off = PieceTransform(id) * info.Sheath - PieceTransform(id).Origin;
        if (off != Vector3.Zero)
            foreach (var c in root.GetChildren())
                if (c is Node3D n) n.Position -= off;
        return root;
    }

    /// <summary>Which kinds ride in a scabbard: the one-handed blades (by kind, never by item).</summary>
    public static bool Scabbarded(WeaponKind kind) => kind == WeaponKind.Blade1H;

    /// <summary>How far the shield mount sits off the forearm bone, toward the back of the arm (m).</summary>
    const float ShieldOff = 0.115f;  // 0.08 -> 0.11 (judge 45), -> 0.115 (13 Oct: the rim grazed her own upper arm 1.6-1.8 mm in every Warden idle and stop; the arm runs along the disc)

    /// <summary>How far down the forearm the shield is strapped (m): its boss over her wrist, so the rim sits under her shoulder armour with air.</summary>
    const float ShieldAlong = 0.23f;

    /// <summary>The piece's own turn inside its mount: held pistol-fashion
    /// (a crossbow) the stock runs along the fingers, its top out of the
    /// thumb side, sitting on the fist rather than through it.</summary>
    public static Transform3D PieceTransform(string id) => All[id].Pistol
        ? new Transform3D(new Basis(new Vector3(0, 0, 1), new Vector3(1, 0, 0), new Vector3(0, 1, 0)), new Vector3(0, 0.05f, 0))
        : Transform3D.Identity;
}
