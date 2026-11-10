using Godot;
using SurvivorUnchained.Look;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>(L1 lead 22, mirror; pictures only) A skeleton's current pose reflected across her own sagittal plane, the
/// left and right bones swapped (MirrorPairs by name): each bone takes its twin's turn from rest, reflected, in skeleton
/// space (G'_b = M G_p R_p^-1 M R_b, R the global rests, M the reflection), so a rest pose mirrors to itself even where
/// the two sides' rests are not exact mirrors and the bones' own local axes need not be. The plane is found once from
/// the paired rests (its normal the mean left-minus-right, through the pairs' mid points). Positions stay each bone's own
/// unless the pose moves it off its rest (the root and the hips' travel), so bone lengths hold. Then a held piece rides
/// the hand that grips after the mirror: <see cref="Piece"/> moves it from one hand to the other, reflected through its
/// own thinnest axis (a blade's flat) so it stays a proper turn of the same piece.</summary>
public sealed class PoseMirror
{
    readonly Skeleton3D sk;
    readonly int[] pair, parent;
    readonly Transform3D[] rest;
    readonly Transform3D m;
    public readonly int Paired;
    public readonly Vector3 Normal;

    public PoseMirror(Skeleton3D skeleton)
    {
        sk = skeleton;
        int n = sk.GetBoneCount();
        pair = new int[n]; parent = new int[n]; rest = new Transform3D[n];
        var sum = Vector3.Zero; var mid = Vector3.Zero; int k = 0;
        for (int b = 0; b < n; b++)
        {
            parent[b] = sk.GetBoneParent(b);
            rest[b] = sk.GetBoneGlobalRest(b);
            int p = sk.FindBone(MirrorPairs.Pair(sk.GetBoneName(b)));
            pair[b] = p >= 0 ? p : b;
        }
        for (int b = 0; b < n; b++)
        {
            if (pair[b] == b) continue;
            Paired++;
            string name = sk.GetBoneName(b);
            if (name != MirrorPairs.Pair(MirrorPairs.Pair(name))) continue;
            // left minus right, whichever this one is: summed once per pair (from its left bone)
            if (IsLeft(name)) { sum += rest[b].Origin - rest[pair[b]].Origin; mid += (rest[b].Origin + rest[pair[b]].Origin) * 0.5f; k++; }
        }
        Normal = sum.LengthSquared() > 1e-12f ? sum.Normalized() : Vector3.Right;
        var c = k > 0 ? mid / k : Vector3.Zero;
        var nn = Normal;
        var basis = new Basis(
            new Vector3(1 - 2 * nn.X * nn.X, -2 * nn.Y * nn.X, -2 * nn.Z * nn.X),
            new Vector3(-2 * nn.X * nn.Y, 1 - 2 * nn.Y * nn.Y, -2 * nn.Z * nn.Y),
            new Vector3(-2 * nn.X * nn.Z, -2 * nn.Y * nn.Z, 1 - 2 * nn.Z * nn.Z));
        m = new Transform3D(basis, 2 * c.Dot(nn) * nn);
    }

    static bool IsLeft(string name) =>
        name.EndsWith("_l") || name.EndsWith("_L") || name.EndsWith(".l") || name.EndsWith(".L")
        || name.Contains("_l_") || name.Contains("_L_") || name.Contains(".l.") || name.Contains(".L.")
        || name.Contains("Left") || name.Contains("left") || name.Contains("LEFT");

    /// <summary>The reflection, in skeleton space.</summary>
    public Transform3D M => m;

    /// <summary>Reflects the skeleton's current pose (call after the clip is applied, before the modifiers run).</summary>
    public void Apply()
    {
        int n = pair.Length;
        var g = new Transform3D[n];
        var loc = new Transform3D[n];
        for (int b = 0; b < n; b++)
        {
            loc[b] = new Transform3D(new Basis(sk.GetBonePoseRotation(b)) * Basis.FromScale(sk.GetBonePoseScale(b)), sk.GetBonePosePosition(b));
            g[b] = parent[b] >= 0 ? g[parent[b]] * loc[b] : loc[b];
        }
        var gm = new Transform3D[n];
        for (int b = 0; b < n; b++)
        {
            int p = pair[b];
            gm[b] = m * g[p] * rest[p].AffineInverse() * m * rest[b];
        }
        for (int b = 0; b < n; b++)
        {
            var l = parent[b] >= 0 ? gm[parent[b]].AffineInverse() * gm[b] : gm[b];
            sk.SetBonePoseRotation(b, l.Basis.Orthonormalized().GetRotationQuaternion());
            if ((sk.GetBonePosePosition(b) - sk.GetBoneRest(b).Origin).Length() > 0.001f) sk.SetBonePosePosition(b, l.Origin);
        }
    }

    Node3D? holder;
    Transform3D seat, flip;

    /// <summary>Moves the piece held at `fromBone` (Arms.Hold's mount, a BoneAttachment3D's child) to `toBone`,
    /// reflected: its offset from the new hand is R_to^-1 M R_from (mount)(seat)(flip), the pose mirror's own
    /// relation of the two hands, so the piece sits in the mirrored fist as it sat in the other. Called every held
    /// frame (the mount's place is re-read: B's mounts follow their bones); false when there is nothing to move.</summary>
    public bool Piece(string fromBone, string toBone)
    {
        int fb = sk.FindBone(fromBone), tb = sk.FindBone(toBone);
        if (fb < 0 || tb < 0) return false;
        Node3D? mount = null;
        foreach (var c in sk.GetChildren())
            if (c is BoneAttachment3D a && a.BoneName == fromBone)
                foreach (var cc in a.GetChildren())
                    if (cc is Node3D mn && mn.Name.ToString().StartsWith(GripSlide.MountPrefix)) mount = mn;
        if (mount == null) return false;
        if (holder == null || !GodotObject.IsInstanceValid(holder))
        {
            if (mount.GetChildCount() == 0 || mount.GetChild(0) is not Node3D piece) return false;
            seat = piece.Transform;
            flip = Flip(piece);
            var att = new BoneAttachment3D { BoneName = toBone, Name = "MirrorHold" };
            sk.AddChild(att);
            holder = new Node3D { Name = "MirrorHolder" };
            att.AddChild(holder);
            piece.Reparent(holder, false);
            piece.Transform = Transform3D.Identity;
        }
        holder.Transform = rest[tb].AffineInverse() * m * rest[fb] * mount.Transform * seat * flip;
        return true;
    }

    /// <summary>The piece's reflection through its own thinnest axis, about its box's centre (a blade's flat): the
    /// pose mirror's reflection and this one make a proper turn, and a symmetric blade maps onto itself.</summary>
    static Transform3D Flip(Node3D piece)
    {
        Aabb box = default; bool any = false;
        void Walk(Node n, Transform3D t)
        {
            foreach (var c in n.GetChildren())
            {
                if (c is not Node3D c3) continue;
                var ct = t * c3.Transform;
                if (c3 is MeshInstance3D mi && mi.Mesh != null)
                {
                    var bb = ct * mi.Mesh.GetAabb();
                    box = any ? box.Merge(bb) : bb; any = true;
                }
                Walk(c3, ct);
            }
        }
        if (piece is MeshInstance3D self && self.Mesh != null) { box = self.Mesh.GetAabb(); any = true; }
        Walk(piece, Transform3D.Identity);
        var s = any ? box.Size : Vector3.One;
        int axis = s.X <= s.Y && s.X <= s.Z ? 0 : s.Y <= s.Z ? 1 : 2;
        var c0 = any ? box.GetCenter() : Vector3.Zero;
        var d = Vector3.One; d[axis] = -1;
        var o = Vector3.Zero; o[axis] = 2 * c0[axis];
        return new Transform3D(Basis.FromScale(d), o);
    }
}
