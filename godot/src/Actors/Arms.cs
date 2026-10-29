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
    /// Seated: its Grip has been measured against her fitted fist (Seat lays it on her fist's pocket for its kind,
    /// WeaponSockets.Pocket: her right fist's, and her left's where that is fitted); an unseated piece without an anchor
    /// keeps the plain mount (its hilt not yet checked against the fist: the viking sword's guard would sit 25 mm into her forefinger at its Grip).
    public sealed record Spec(string File, float Length, float Grip, bool Flip = false, float Roll = 0, string? Node = null, bool Pistol = false, Func<Node3D>? Build = null, float Lean = 0, WeaponKind Kind = WeaponKind.None, bool Seated = false);

    public static readonly Dictionary<string, Spec> All = new()
    {
        ["chevalier_sword"] = new("chevalier_sword", 1.0f, 0.1f, Lean: 35, Kind: WeaponKind.Blade1H, Seated: true),
        ["viking_sword"] = new("viking_sword", 0.92f, 0.13f, Lean: 35, Kind: WeaponKind.Blade1H),  // grip conformed (grip_conform.py --seat --round): its anchor_grip seats it; Seated, and fistfit viking_sword passes 13/13 (391f685c, grip_conform --cylinder)
        ["longsword"] = new("longsword", 1.05f, 0.22f, Flip: true, Lean: 35, Kind: WeaponKind.Blade1H),
        ["zweihander"] = new("zweihander", 1.6f, 0.2f, Kind: WeaponKind.Blade2H),
        // The Ford-Warden's old Watch blade (tools/assets/watch_blade.py, concept A): straight, corroded, the zweihander's size and grip.
        ["watch_blade"] = new("", 1.6f, 0.2f, Build: LampIron.WatchBlade, Kind: WeaponKind.Blade2H),
        ["mace"] = new("mace", 0.75f, 0.12f, Lean: 30, Kind: WeaponKind.Blunt),
        ["viking_axe"] = new("viking_axe", 0.7702f, 0.15f, Roll: Mathf.Pi, Lean: 35, Kind: WeaponKind.Axe, Seated: true),  // haft conformed to her one-handed fist (anim-40: tapered haft, an oval wrap 34.7 x 21.7 mm over the fist, anchor_grip on the haft's line); seated on BladeAtR (PocketR Axe), Length keeps the old scale; fistfit axe
        ["snake_axe"] = new("snake_axe", 1.3f, 0.22f, Lean: 30, Kind: WeaponKind.Axe2H),
        ["mage_staff"] = new("mage_staff", 1.75f, 0.45f, Kind: WeaponKind.Staff),
        ["short_staff"] = new("mage_staff", 1.1f, 0.3f, Kind: WeaponKind.Staff),
        // The crossbow: its stock 0.693 m (the size it had while Make took its 0.85 m bow for its length, before its
        // anchor_grip said the stock is the shaft), held by its pistol grip (tools/assets/crossbow_grip.py, Seat).
        ["crossbow"] = new("crossbow", 0.693f, 0.3f, Pistol: true, Kind: WeaponKind.Crossbow),
        ["wand"] = new("", 0.38f, 0.12f, Build: Made.Wand, Lean: 35, Kind: WeaponKind.Wand, Seated: true),  // her one-handed fist (anim-40): Made.Wand's grip is the Blade1H's, seated on BladeAtR; fistfit wand
        ["shield_round"] = new("shield_round", 0.66f, 0.5f, Kind: WeaponKind.Shield),
        ["daggers"] = new("daggers", 0.4f, 0.2f, Node: "Cube_004", Lean: 30, Kind: WeaponKind.Dagger, Seated: true),
        ["dagger_b"] = new("daggers", 0.4f, 0.2f, Node: "Cube_004_01", Lean: 30, Kind: WeaponKind.Dagger, Seated: true),  // grip conformed (grip_conform.py --no-anchor); its left fist: fistfit.py daggers --side l
    };

    static Arms() => ArmsData.Merge(All);  // art/weapons/weapons.json: weapons of a known kind as data

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
        var path = new List<string>();
        void Walk(Node n, Transform3D at)
        {
            foreach (var c in n.GetChildren())
            {
                var t = c is Node3D c3 ? at * c3.Transform : at;
                // Anchors (Marionette exports carry them) and a kind tag (a glTF extra "kind", or a node named kind_<kind>).
                // In a file of several pieces only the anchors under the piece's own node (WeaponSockets.AnchorIsPiece).
                if (c is Node3D)
                {
                    bool own = WeaponSockets.AnchorIsPiece(spec.Node, path);
                    if (c.Name.ToString().StartsWith("anchor_grip")) { if (own) aGrip = t; }
                    else if (c.Name.ToString().StartsWith("anchor_sheath")) { if (own) aSheath = t; }
                    else if (c.Name.ToString().StartsWith("kind", StringComparison.OrdinalIgnoreCase)) tag = WeaponSockets.Parse(c.Name);
                }
                if (c.HasMeta("extras") && c.GetMeta("extras").Obj is Godot.Collections.Dictionary ex && ex.ContainsKey("kind"))
                    tag = WeaponSockets.Parse(ex["kind"].ToString());
                if (c is MeshInstance3D mi && mi.Mesh != null)
                    for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                        foreach (var v in (Vector3[])mi.Mesh.SurfaceGetArrays(s)[(int)Mesh.ArrayType.Vertex]) pts.Add(t * v);
                path.Add(c.Name.ToString());
                Walk(c, t);
                path.RemoveAt(path.Count - 1);
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
        var mount = new Node3D { Name = GripSlide.MountPrefix + bone };
        att.AddChild(mount);
        mount.Transform = MountTransform(id, bone, person.Own != null);
        var w = Make(id);
        w.Transform = Seat(w, id, bone, person.Own != null);
        mount.AddChild(w);
        return mount;
    }

    /// <summary>A held piece's place inside its mount (Hold's and ArmsDump's): PieceTransform, and in her right hand, for a
    /// kind with a fitted pocket (WeaponSockets.PocketR: the staff, the one-handed blade), the fist's seat
    /// (WeaponSockets.FistSeat): its grip point (an anchor_grip's origin, else Spec.Grip along its long axis) on the fist's
    /// pocket and its shaft along the fist's line, so the anchor rule stays "origin on the shaft where the fist grips, -Y
    /// down the shaft". An unanchored piece is seated only when its Spec says its Grip was measured on the fist
    /// (Seated) and only in her and the hero's hands (`own`: the fist was fitted on her hand, the grip keyed to its
    /// Lean); the folk keep the plain mount. A pistol-held piece (the crossbow) is seated by its pistol grip
    /// (WeaponSockets.PistolSeat: its anchor_grip on the fist's pocket, the grip along the fist's line, the stock along
    /// the hand's +Y, the bow forward) when it has the grip (an anchor_grip), else it keeps the plain pistol mount (its
    /// stock on the fist). Not for the forearm. hand_l: the same seat on its left pocket (WeaponSockets.PocketL, the right's mirrored: only the
    /// dagger's so far), the mount itself unmirrored (the seat lays the grip point and the shaft's line, so only the
    /// piece's roll about its shaft is the plain mount's: a flat hilt's faces toward the palm and the back either way).
    /// Every other kind in the left hand keeps the plain mount.</summary>
    public static Transform3D Seat(Node3D piece, string id, string bone, bool own = true)
    {
        var t = PieceTransform(id);
        var spec = All[id];
        var kind = piece.HasMeta("kind") ? (WeaponKind)(int)piece.GetMeta("kind") : spec.Kind;
        if (WeaponSockets.Pocket(kind, bone) is not { } pocket) return t;
        static System.Numerics.Vector3 N(Vector3 v) => new(v.X, v.Y, v.Z);
        if (spec.Pistol)
        {
            if (!piece.HasMeta("anchored")) return t;
            var pm = MountTransform(id, bone, own);
            var (pq, pat) = WeaponSockets.PistolSeat(N(pm.Basis.X), N(pm.Basis.Y), N(pm.Basis.Z), N(pm.Origin), pocket.At, pocket.Dir);
            return new Transform3D(new Basis(new Quaternion(pq.X, pq.Y, pq.Z, pq.W)), new Vector3(pat.X, pat.Y, pat.Z));
        }
        if (!piece.HasMeta("anchored") && !(own && spec.Seated)) return t;
        var m = MountTransform(id, bone, own);
        var (q, at) = WeaponSockets.FistSeat(N(m.Basis.X), N(m.Basis.Y), N(m.Basis.Z), N(m.Origin), pocket.At, pocket.Dir);
        return new Transform3D(new Basis(new Quaternion(q.X, q.Y, q.Z, q.W)), new Vector3(at.X, at.Y, at.Z)) * t;
    }

    /// <summary>A piece's place inside its mount seated on an explicit pocket (`at`, `dir` in its hand's space): Seat's fist
    /// seat, for a pocket the piece is only moved onto for a while (animation 58: a left grip tilt's mirrored pocket,
    /// WeaponSockets.TiltPocketL, PersonView.Slide).</summary>
    public static Transform3D SeatOn(string id, string bone, bool own, System.Numerics.Vector3 at, System.Numerics.Vector3 dir)
    {
        static System.Numerics.Vector3 N(Vector3 v) => new(v.X, v.Y, v.Z);
        var m = MountTransform(id, bone, own);
        var (q, a) = WeaponSockets.FistSeat(N(m.Basis.X), N(m.Basis.Y), N(m.Basis.Z), N(m.Origin), at, dir);
        return new Transform3D(new Basis(new Quaternion(q.X, q.Y, q.Z, q.W)), new Vector3(a.X, a.Y, a.Z)) * PieceTransform(id);
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
    /// Mirrors: a piece in her left hand rides on the other side (a pair of daggers, a sword in the left). The row's
    /// At, Shaft, Thick and Normal are mirrored, which mirrors the flat and so turns the edge (Shaft x Thick) the other
    /// way; MirrorEdge: the edge is mirrored instead (Thick flipped), so a pair (gyre's axes) rides as true mirror images
    /// (the piece symmetric through its flat, it looks the same).
    /// Sheathed() turns the row into the bone's space.</summary>
    /// Hang (Body 16): a piece hung from her belt (a scabbard, an axe in its loop) is turned about this belt point (skeleton
    /// space at rest, mirrored as At is) as a hung weight (View/SheathSway, Play/SheathHang) instead of riding the bone
    /// rigidly; null: it rides rigidly (strapped across her back, tucked in the belt).
    /// Frog (Body 17): a hafted piece hangs in a leather frog (Made.Frog, MakeSheathed).
    sealed record Socket(string Bone, Vector3 At, Vector3 Shaft, Vector3 Thick, Vector3 Normal, bool Mirrors = false, bool MirrorEdge = false, Vector3? Hang = null, bool Frog = false);

    static readonly Dictionary<string, Socket> Sockets = new()
    {
        // Shield: across the back, its boss centred between the shoulder blades 0.14 m behind spine_03, face out
        // (back), its top rim under the neck (66 cm across).
        // (armor 5 solver, 19 October: 4 mm back and the top a hair to her left, so the rim clears her elbows in the run.)
        [WeaponSockets.Back] = new("spine_03", new(0.002f, 1.219f, -0.204f), new(0.006f, 1, -0.001f), new(-0.001f, -0.001f, -1), new(0, 0, -1)),
        // One-handed blade: left hip, in the scabbard (MakeSheathed), hilt forward and up, blade down and back about
        // 30 degrees off vertical, flat to her side (thickness out).
        // Hung from its sheath point (Body 16) in walk and idle; RIGID, riding the pelvis, in the clips where her hand
        // holds the hilt (Body 17, 27 Oct: run_warden_town and sprint_warden_town, SheathHang.HiltHeld), where hung
        // it swung into that hand (10.0 / 11.6 mm; tools/scratch/body16/hang.py), eased over 0.2 s at the cuts.
        [WeaponSockets.HipBlade] = new("pelvis", new(0.21f, 1.20f, 0.10f), new(0.08f, -0.87f, -0.50f), new(1, 0, 0), new(1, 0, 0), Mirrors: true,
            Hang: new(0.21f, 1.20f, 0.10f)),
        // Blunt and axe: the hip loop behind her right hip (left hand: mirrored, MirrorEdge, so gyre's two ride as mirror
        // images), at about 5 o'clock (12 her front): the head on the belt (the haft's top 1.06 m up, 22 cm out from her
        // axis), the haft down along the back of her thigh, its foot leaning 20 deg out and 10 deg to her side so the thigh
        // clears it as it swings back in the run, the blade straight back. `At` is the axe's sheath point near the haft's
        // foot. (Animation 44, solver idle 2, 20 October: her hands had rested on the heads at her side; now the nearest
        // hand is 20 cm off a head in the town idle and 39 cm in the run and sprint, 0 mm into her: socktry.py.)
        // Hung from the head on the belt (the haft's top, 1.06 m up and 22 cm out; Body 16).
        // (Body 17, 27 October: the judge read the haft "propped out" 20-25 deg from plumb front and back: now 11 deg out
        // and 14 back at rest, 9-13 out in the walk (was 17-21), the head 4.5 cm farther out and 6 cm farther back so her
        // right forearm (walk) and kicked-back foot (sprint) still clear it: 0 mm into her skin and outfit in every reaver
        // town clip, both hands (the walk's forearm 9 mm off the head, the sprint's boot 7 mm off the foot), the nearest
        // hand 80 mm (tools/scratch/body17/axe/row.py). The head now hangs off her belt in a leather frog (Made.Frog).)
        // (Body 17, 27 October, judge: in the side walk the head hung 8-10 cm behind her buttock, unattached: the top now
        // 3 cm higher, 5.5 cm in and 6 cm forward, leaning 12.5 deg out and 30 back at rest, so in the walk the poll rides
        // 3-9 mm off her outfit (8.8 cm before), 0 mm into her skin and outfit in every reaver town clip, both hands (the
        // walk's forearm 1.2 mm off the head, the sprint's calf 0.6 mm off the foot); walk splay 10-15 deg (the sprint's
        // heel wants the foot that far out). The frog's strap on the head's outer face: tools/scratch/body17/axe/row2.py.)
        [WeaponSockets.HipLoop] = new("pelvis", new(-0.206f, 0.614f, -0.465f), new(0.189f, 0.850f, 0.491f), new(0.971f, -0.236f, 0.035f), new(-0.5f, 0, -0.866f), Mirrors: true, MirrorEdge: true,
            Hang: new(-0.10f, 1.09f, -0.19f), Frog: true),
        // Wand: tucked in the belt behind her right hip at about 5 o'clock, the grip at the leotard's hip line (1.08 m),
        // the crystal down and back about 30 deg (animation 44, solver idle 2: crystal up, it stood beside her breast and
        // her forearm passed through it in the run).
        [WeaponSockets.HipBelt] = new("pelvis", new(-0.090f, 1.080f, -0.156f), new(-0.082f, -0.841f, -0.534f), new(0.531f, -0.490f, 0.691f), new(-0.5f, 0, -0.866f), Mirrors: true),
        // Dagger: the back of the belt, flat, one each side of the spine, hilts out and blades crossing.
        [WeaponSockets.BeltBack] = new("pelvis", new(-0.17f, 1.12f, -0.13f), new(1, 0, 0), new(0, 0, -1), new(0, 0, -1), Mirrors: true),
        // Crossbow: slung across the back by the stock's middle (its anchor_sheath), stock rising to her right shoulder,
        // the bow flat across her back, its top in to the back so the pistol grip and the lever stand out from her, not
        // into her (18 October: before the grip's anchor the bow was taken for the stock and ran up the diagonal).
        // (armor 5 solver, 19 October: 2 cm farther back, off her shoulder blades and clear of her left arm in the run.)
        [WeaponSockets.Sling] = new("spine_03", new(0.099f, 1.164f, -0.191f), new(-0.602f, 0.799f, -0.002f), new(0, 0.002f, 1), new(0, 0, -1)),
        // Two-handed blade or axe: diagonal across the back like the sling, hilt or haft over her right shoulder (the
        // grip high on the right), the tip down toward her left hip, flat to her back.
        // (armor 5 solver, 19 October: the tip turned 11 degrees out from her back, off her calves.)
        [WeaponSockets.BackDiag] = new("spine_03", new(-0.07f, 1.30f, -0.201f), new(0.281f, -0.944f, -0.185f), new(0.003f, 0.193f, -0.981f), new(0, 0, -1)),
        // Staff (animation 45, 20 October; judge round 1 turn): slung across her back on a steep diagonal (29 deg off
        // vertical), the head (the piece's +Y) up behind and outside her right shoulder, the foot down outside her left
        // calf. The crescent's face looks out along her back-left/front-right diagonal, so from the three-quarter front
        // it shows edge-on behind her head and its short inner horn lies toward her shoulder blade. The turn swings that
        // horn in toward her head, so the row sits 18 cm lower, 9 cm farther out and 5 cm farther back than the first
        // fit: past the arcanist's wide hat brim 6.4 cm (the sprint's lean), her braid 6.9 cm, her upper back 7 cm, the
        // run's kicked-back calf 8 cm, 0 mm into her skin and outfit, both hands 32 cm or more off it
        // (tools/scratch/anim45/staffcheck.py). `At` is the grip (no anchor_sheath); its clearance is the 5 mm air alone.
        // The bead charms are stripped while it rides (StripCharms). Unused: the slung staff failed under the arcanist's hat (animation 45); for a hatless outfit, unjudged.
        [WeaponSockets.BackStaff] = new("spine_03", new(-0.0518f, 0.9148f, -0.3175f), new(-0.4657f, 0.8782f, -0.1086f), new(0.6607f, 0.2634f, -0.7029f), new(0, 0, -1)),
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
        // (locked: her cinematic double is made on a worker thread, Game.DoubleAhead)
        lock (facts)
        {
            if (!facts.TryGetValue(id, out var m))
            {
                var w = Make(id);
                facts[id] = m = new Facts((int)w.GetMeta("kind"), (Vector3)w.GetMeta("sheath"), (float)w.GetMeta("tip"));
                w.Free();
            }
            return m;
        }
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
        if (left && k.Mirrors) { at.X = -at.X; shaft.X = -shaft.X; thick.X = -thick.X; normal.X = -normal.X; if (k.MirrorEdge) thick = -thick; }
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

    /// <summary>The belt point a hung piece turns about, in the socket bone's space (pushed out by the outfit as the
    /// mount is), or null if it rides rigidly or has no socket.</summary>
    public static Vector3? HangPoint(string id, bool left = false, string? outfit = null)
    {
        if (WeaponSockets.SocketOf(KindOf(id)) is not { } name || Sockets[name].Hang is not { } p) return null;
        var k = Sockets[name];
        var normal = k.Normal;
        if (left && k.Mirrors) { p.X = -p.X; normal.X = -normal.X; }
        if (outfit != null) p += normal * Clearance.Metres(outfit, name);
        return RestOf(k.Bone).AffineInverse() * p;
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
        mount.AddChild(MakeSheathed(id, left));
        if (HangPoint(id, left, calling ?? "") is { } pivot)
            SheathSway.Attach(skeleton, mount, bone, pivot, hilt: WeaponSockets.SocketOf(KindOf(id)) == WeaponSockets.HipBlade);
        return mount;
    }

    /// <summary>A piece as it rides sheathed, in its mount's space, its sheath point (anchor_sheath, else the grip) at
    /// the origin: the weapon, and for a one-handed blade its scabbard from the guard round the blade to a thumb past
    /// its tip (WeaponSockets.BladeLength; also what ArmsDump writes).</summary>
    public static Node3D MakeSheathed(string id, bool left = false)
    {
        var root = new Node3D { Name = "sheathed" };
        var info = Info(id);
        var w = Make(id);
        w.Transform = PieceTransform(id);
        if (KindOf(id) == WeaponKind.Staff) StripCharms(w);
        root.AddChild(w);
        if (Scabbarded(KindOf(id)))
        {
            const float guard = 0.10f;
            var sc = Made.Scabbard(WeaponSockets.BladeLength(info.Tip, info.Sheath.Y, guard));
            sc.Position = new Vector3(0, info.Sheath.Y + guard, 0);
            root.AddChild(sc);
        }
        if (WeaponSockets.SocketOf(KindOf(id)) is { } sock && Sockets[sock].Frog && Sheathed(id, left) is { } mount && SocketFacing(id, left) is { } face)
        {
            // Toward her belt in the piece's space: the way into her body there, across the haft.
            var inward = mount.At.Basis.Inverse() * -face.Normal;
            inward = new Vector3(inward.X, 0, inward.Z).Normalized();
            var (top, half, poll, cheek) = HaftOf(id, w, inward);
            var frog = Made.Frog(half.X, half.Y, inward, poll, cheek);
            frog.Position = top;
            root.AddChild(frog);
        }
        var off = PieceTransform(id) * info.Sheath - PieceTransform(id).Origin;
        if (off != Vector3.Zero)
            foreach (var c in root.GetChildren())
                if (c is Node3D n) n.Position -= off;
        return root;
    }

    static readonly Dictionary<(string, bool), (Vector3, Vector2, float, float)> hafts = new();

    /// <summary>Where a hafted piece's head begins, in its sheathed root's space (Body 17, for the frog): the haft's axis at
    /// the head's foot, the haft's half-widths across X and Z just under it, and how far the head stands off the axis over
    /// its first 12 cm along X toward `inward` (unit, XZ; the poll, facing her) and along Z away from it (its outer cheek). Read from the piece's own surface (its vertices and points 1 cm
    /// apart along its edges: a haft is often one long quad). The haft's axis and radius are read at the grip (the
    /// piece's origin, +-4 cm, wider if the grip has no vertices there); going up, the head begins at the lowest point
    /// standing off the axis by more than 1.5 haft radii + 5 mm but within 10 cm of it (a beard hanging lower and farther
    /// out, as the viking axe's, is not the head's foot: the band sits beside it, under the eye). None (a plain club):
    /// 12 cm under the top.</summary>
    static (Vector3 Top, Vector2 Half, float Poll, float Cheek) HaftOf(string id, Node3D piece, Vector3 inward)
    {
        lock (hafts)
        {
            var key = (id, inward.Z > 0);
            if (hafts.TryGetValue(key, out var hit)) return hit;
            var q = new List<Vector3>();
            void Walk(Node n, Transform3D at)
            {
                foreach (var c in n.GetChildren())
                {
                    var t = c is Node3D c3 ? at * c3.Transform : at;
                    if (c is MeshInstance3D mi && mi.Mesh != null)
                        for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                        {
                            var a = mi.Mesh.SurfaceGetArrays(s);
                            var v = a[(int)Mesh.ArrayType.Vertex].AsVector3Array();
                            foreach (var p in v) q.Add(t * p);
                            if (a[(int)Mesh.ArrayType.Index].VariantType == Variant.Type.Nil) continue;
                            var idx = a[(int)Mesh.ArrayType.Index].AsInt32Array();
                            for (int i = 0; i + 2 < idx.Length; i += 3)
                                for (int e = 0; e < 3; e++)
                                {
                                    Vector3 p0 = t * v[idx[i + e]], p1 = t * v[idx[i + (e + 1) % 3]];
                                    int m = (int)(p0.DistanceTo(p1) / 0.01f);
                                    for (int j = 1; j < m; j++) q.Add(p0.Lerp(p1, (float)j / m));
                                }
                        }
                    Walk(c, t);
                }
            }
            Walk(piece, piece.Transform);
            var g = piece.Transform.Origin;
            float tip = float.MinValue;
            foreach (var p in q) tip = MathF.Max(tip, p.Y);
            float x0 = 0, x1 = 0, z0 = 0, z1 = 0;
            for (float win = 0.04f; win < 1f; win *= 2)
            {
                (x0, x1, z0, z1) = (float.MaxValue, float.MinValue, float.MaxValue, float.MinValue);
                int n = 0;
                foreach (var p in q)
                    if (MathF.Abs(p.Y - g.Y) < win) { n++; x0 = MathF.Min(x0, p.X); x1 = MathF.Max(x1, p.X); z0 = MathF.Min(z0, p.Z); z1 = MathF.Max(z1, p.Z); }
                if (n >= 8) break;
            }
            float cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, r = MathF.Max(x1 - x0, z1 - z0) / 2, rim = 1.5f * r + 0.005f;
            float D(Vector3 p) => MathF.Sqrt((p.X - cx) * (p.X - cx) + (p.Z - cz) * (p.Z - cz));
            float top = tip - 0.12f;
            bool found = false;
            foreach (var p in q)
                if (p.Y > g.Y + 0.10f && D(p) > rim && D(p) < 0.10f && (!found || p.Y < top)) { top = p.Y; found = true; }
            float u = 0, w = 0, poll = 0, cheek = 0, fx = inward.X < 0 ? -1 : 1, oz = inward.Z > 0 ? -1 : 1;
            foreach (var p in q)
            {
                if (p.Y >= top - 0.06f && p.Y <= top - 0.003f && D(p) <= rim) { u = MathF.Max(u, MathF.Abs(p.X - cx)); w = MathF.Max(w, MathF.Abs(p.Z - cz)); }
                if (p.Y >= top && p.Y <= top + 0.12f && D(p) < 0.12f) { poll = MathF.Max(poll, (p.X - cx) * fx); cheek = MathF.Max(cheek, (p.Z - cz) * oz); }
            }
            if (u == 0) (u, w) = (r, r);
            return hafts[key] = (new Vector3(cx, top, cz), new Vector2(u, w), poll, cheek);
        }
    }

    static readonly Dictionary<ArrayMesh, ArrayMesh> Uncharmed = new();

    /// <summary>The staff slung on her back (animation 45): its two bead charms hang plumb from the crescent only while
    /// it is held upright, so slung at 24 deg they lean with the shaft (an earring at the close-up). They go while it
    /// rides: the detached pieces of the head no wider than 5.2 cm and of 30 welded vertices or more (the beads and
    /// links; the loose single-face trim stays) whose centre hangs off the shaft (|x| > 5 cm) between 1.40 and 1.90 m.</summary>
    // Unused: the slung staff failed under the arcanist's hat (animation 45); for a hatless outfit, unjudged.
    static void StripCharms(Node n)
    {
        if (n is MeshInstance3D mi && mi.Mesh is ArrayMesh am)
        {
            if (!Uncharmed.TryGetValue(am, out var cut)) Uncharmed[am] = cut = Uncharm(am);
            mi.Mesh = cut;
        }
        foreach (var c in n.GetChildren()) StripCharms(c);
    }

    static ArrayMesh Uncharm(ArrayMesh am)
    {
        var o = new ArrayMesh();
        for (int si = 0; si < am.GetSurfaceCount(); si++)
        {
            var a = am.SurfaceGetArrays(si);
            var v = a[(int)Mesh.ArrayType.Vertex].AsVector3Array();
            var idx = a[(int)Mesh.ArrayType.Index].VariantType == Variant.Type.Nil ? null : a[(int)Mesh.ArrayType.Index].AsInt32Array();
            if (idx == null || am.SurfaceGetPrimitiveType(si) != Mesh.PrimitiveType.Triangles) { CopySurface(am, si, o, a); continue; }
            // Weld by position (0.1 mm), then join each triangle's corners.
            var weld = new Dictionary<(int, int, int), int>();
            var wid = new int[v.Length];
            for (int i = 0; i < v.Length; i++)
            {
                var k = ((int)MathF.Round(v[i].X * 1e4f), (int)MathF.Round(v[i].Y * 1e4f), (int)MathF.Round(v[i].Z * 1e4f));
                if (!weld.TryGetValue(k, out wid[i])) weld[k] = wid[i] = weld.Count;
            }
            var up = new int[weld.Count];
            for (int i = 0; i < up.Length; i++) up[i] = i;
            int Find(int x) { while (up[x] != x) x = up[x] = up[up[x]]; return x; }
            for (int t = 0; t + 2 < idx.Length; t += 3)
            {
                int r0 = Find(wid[idx[t]]);
                up[Find(wid[idx[t + 1]])] = r0;
                up[Find(wid[idx[t + 2]])] = r0;
            }
            var lo = new Dictionary<int, Vector3>(); var hi = new Dictionary<int, Vector3>(); var cnt = new Dictionary<int, int>();
            var seen = new bool[weld.Count];
            for (int i = 0; i < v.Length; i++)
            {
                int r = Find(wid[i]);
                if (!lo.ContainsKey(r)) { lo[r] = v[i]; hi[r] = v[i]; cnt[r] = 0; }
                lo[r] = lo[r].Min(v[i]); hi[r] = hi[r].Max(v[i]);
                if (!seen[wid[i]]) { seen[wid[i]] = true; cnt[r]++; }
            }
            bool Charm(int r)
            {
                var e = hi[r] - lo[r]; var m = (hi[r] + lo[r]) / 2;
                return Mathf.Max(e.X, Mathf.Max(e.Y, e.Z)) <= 0.052f && cnt[r] >= 30 && MathF.Abs(m.X) > 0.05f && m.Y > 1.40f && m.Y < 1.90f;
            }
            var keep = new List<int>(idx.Length);
            for (int t = 0; t + 2 < idx.Length; t += 3)
                if (!Charm(Find(wid[idx[t]]))) { keep.Add(idx[t]); keep.Add(idx[t + 1]); keep.Add(idx[t + 2]); }
            a[(int)Mesh.ArrayType.Index] = keep.ToArray();
            CopySurface(am, si, o, a);
        }
        return o;
    }

    static void CopySurface(ArrayMesh from, int si, ArrayMesh to, Godot.Collections.Array a)
    {
        to.AddSurfaceFromArrays(from.SurfaceGetPrimitiveType(si), a);
        to.SurfaceSetMaterial(to.GetSurfaceCount() - 1, from.SurfaceGetMaterial(si));
    }

    /// <summary>Which kinds ride in a scabbard: the one-handed blades (by kind, never by item).</summary>
    public static bool Scabbarded(WeaponKind kind) => kind == WeaponKind.Blade1H;

    /// <summary>How far the shield mount sits off the forearm bone, toward the back of the arm (m).</summary>
    const float ShieldOff = 0.115f;  // 0.08 -> 0.11 (judge 45), -> 0.115 (13 Oct: the rim grazed her own upper arm 1.6-1.8 mm in every Warden idle and stop; the arm runs along the disc)

    /// <summary>How far down the forearm the shield is strapped (m): its boss over her wrist, so the rim sits under her shoulder armour with air.</summary>
    const float ShieldAlong = 0.23f;

    /// <summary>The piece's own turn inside its mount: held pistol-fashion
    /// (a crossbow) the stock runs along the fingers, its top out of the
    /// thumb side, sitting on the fist rather than through it (the plain
    /// pistol mount: a piece with a pistol grip is seated on it instead, Seat).</summary>
    public static Transform3D PieceTransform(string id) => All[id].Pistol
        ? new Transform3D(new Basis(new Vector3(0, 0, 1), new Vector3(1, 0, 0), new Vector3(0, 1, 0)), new Vector3(0, 0.05f, 0))
        : Transform3D.Identity;
}
