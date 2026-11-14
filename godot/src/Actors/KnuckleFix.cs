using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// A package rig's finger roots laid back on their fingers. The Marionette wrap's skeleton fit (every package to 13 Nov)
/// put the right hand's index, middle and ring _01 heads 13-17 cm off the hand, out past the back of it, while their _02
/// joints, the bones' own axes and the mesh's weights are where a hand has them: so any bend of those knuckles (a clip's,
/// NpcHands' curl and fist) swung the finger about a point in the air, and a closed fist drew as an open hand. A root is
/// out of place when it lies further from its _02 than 2.5 times _02 to _03 (a sound hand: 1.0 to 1.6). It is laid where
/// the other hand's root sits, mirrored across the hand's X (the rigs' hands are mirror frames), when that hand is sound
/// and its _02 mirrors onto this one's; else back from its _02 along its own axis by the other hand's length (1.25 x _02
/// to _03 without one). Its children keep their places; each skin bound to it at the old place is bound at the new
/// (Rebind), so the rest draws as before and the knuckle turns about the knuckle.
/// </summary>
public static class KnuckleFix
{
    static readonly string[] Fingers = { "index", "middle", "ring", "pinky" };
    static readonly Vector3 Mirror = new(-1, 1, 1);
    static readonly Dictionary<(Skin, string), Skin> rebound = new();

    /// <summary>A finger's chain on a side (_01, _02, _03), or null.</summary>
    static (int B1, int B2, int B3)? Chain(Skeleton3D sk, string f, string s)
    {
        int b1 = sk.FindBone($"{f}_01_{s}"), b2 = sk.FindBone($"{f}_02_{s}"), b3 = sk.FindBone($"{f}_03_{s}");
        return b1 >= 0 && b2 >= 0 && b3 >= 0 && sk.GetBoneParent(b2) == b1 && sk.GetBoneParent(b3) == b2 ? (b1, b2, b3) : null;
    }

    static bool Sound(Skeleton3D sk, (int B1, int B2, int B3) c)
    {
        Vector3 p1 = sk.GetBoneGlobalRest(c.B1).Origin, p2 = sk.GetBoneGlobalRest(c.B2).Origin, p3 = sk.GetBoneGlobalRest(c.B3).Origin;
        return p1.DistanceTo(p2) <= 2.5f * p2.DistanceTo(p3);
    }

    /// <summary>Lays every out-of-place finger root back on its finger (rest and pose); returns each moved bone's old global
    /// rest, for Rebind.</summary>
    public static Dictionary<int, Transform3D> Repair(Skeleton3D sk)
    {
        var moved = new Dictionary<int, Transform3D>();
        foreach (var (s, o) in new[] { ("l", "r"), ("r", "l") })
        {
            int h = sk.FindBone($"hand_{s}"), ho = sk.FindBone($"hand_{o}");
            if (h < 0) continue;
            var hand = sk.GetBoneGlobalRest(h);
            foreach (var f in Fingers)
            {
                if (Chain(sk, f, s) is not { } c || Sound(sk, c)) continue;
                var g1 = sk.GetBoneGlobalRest(c.B1);
                Vector3 p2 = sk.GetBoneGlobalRest(c.B2).Origin, p3 = sk.GetBoneGlobalRest(c.B3).Origin;
                Vector3 at;
                if (ho >= 0 && Chain(sk, f, o) is { } oc && Sound(sk, oc)
                    && (hand.AffineInverse() * p2 - Mirror * (sk.GetBoneGlobalRest(ho).AffineInverse() * sk.GetBoneGlobalRest(oc.B2).Origin)).Length() < 0.006f)
                    at = hand * (Mirror * (sk.GetBoneGlobalRest(ho).AffineInverse() * sk.GetBoneGlobalRest(oc.B1).Origin));
                else
                {
                    float len = ho >= 0 && Chain(sk, f, o) is { } oc2 && Sound(sk, oc2)
                        ? sk.GetBoneGlobalRest(oc2.B1).Origin.DistanceTo(sk.GetBoneGlobalRest(oc2.B2).Origin) : 1.25f * p2.DistanceTo(p3);
                    at = p2 - g1.Basis.Y.Normalized() * len;
                }
                // (its children's global rests, kept)
                var kids = sk.GetBoneChildren(c.B1).Select(k => (k, sk.GetBoneGlobalRest(k))).ToList();
                var parent = sk.GetBoneGlobalRest(sk.GetBoneParent(c.B1));
                var local = sk.GetBoneRest(c.B1);
                local.Origin = parent.AffineInverse() * at;
                sk.SetBoneRest(c.B1, local);
                sk.SetBonePosePosition(c.B1, local.Origin);
                var g1New = parent * local;
                foreach (var (k, gk) in kids)
                {
                    var kl = sk.GetBoneRest(k);
                    kl.Origin = g1New.AffineInverse() * gk.Origin;
                    sk.SetBoneRest(k, kl);
                    sk.SetBonePosePosition(k, kl.Origin);
                }
                moved[c.B1] = g1;
            }
        }
        return moved;
    }

    /// <summary>Every skin under the skeleton bound to a moved root at its old place, bound at its new (a copy per source
    /// skin, shared by every figure of the package). A bind made at another place (a piece fitted to a sound rig) is kept.</summary>
    public static void Rebind(Skeleton3D sk, Dictionary<int, Transform3D> moved, string what)
    {
        if (moved.Count == 0) return;
        var key = string.Join(",", moved.Keys.OrderBy(k => k));
        int fixedBinds = 0;
        foreach (var mi in sk.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>())
        {
            if (mi.Skin is not { } skin) continue;
            if (rebound.TryGetValue((skin, key), out var done)) { mi.Skin = done; continue; }
            Skin? copy = null;
            for (int i = 0; i < skin.GetBindCount(); i++)
            {
                string bn = skin.GetBindName(i);
                int b = bn != "" ? sk.FindBone(bn) : skin.GetBindBone(i);
                if (b < 0 || !moved.TryGetValue(b, out var old)) continue;
                var bind = skin.GetBindPose(i);
                if ((bind.AffineInverse().Origin - old.Origin).Length() > 0.01f) continue;
                copy ??= (Skin)skin.Duplicate();
                copy.SetBindPose(i, sk.GetBoneGlobalRest(b).AffineInverse() * old * bind);
                fixedBinds++;
            }
            if (copy != null) { rebound[(skin, key)] = copy; mi.Skin = copy; }
        }
        GD.Print($"npc: {what} finger roots laid back on the hand ({string.Join(", ", moved.Select(kv => $"{sk.GetBoneName(kv.Key)} {(kv.Value.Origin.DistanceTo(sk.GetBoneGlobalRest(kv.Key).Origin) * 1000):0} mm"))}; {fixedBinds} binds)");
    }
}
