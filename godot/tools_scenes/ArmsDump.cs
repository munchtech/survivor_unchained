using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Tools;

/// <summary>
/// Every weapon and shield her loadouts hold, as the game mounts them
/// (Arms.Make, Arms.MountTransform, Arms.PieceTransform), written as triangles
/// in the holding bone's own space (metres) to tools/anim/data/arms_local.json
/// for tools/anim/armscheck.py; and her skeleton's rest globals of the three
/// bones that hold them (tools/anim/data/arms_rest_godot.json), to check the
/// Python side agrees. tools_scenes/arms_dump.gd runs it.
/// </summary>
public partial class ArmsDump : Node
{
    // Her sets (logic/Play/Loadout.cs): Right on hand_r, Left on hand_l, Forearm on lowerarm_l.
    static readonly (string Id, string Bone)[] Pairs =
    {
        ("chevalier_sword", "hand_r"), ("viking_sword", "hand_r"), ("viking_axe", "hand_r"), ("viking_axe", "hand_l"),
        ("wand", "hand_r"), ("mage_staff", "hand_r"), ("crossbow", "hand_r"), ("daggers", "hand_r"), ("dagger_b", "hand_l"),
        ("shield_round", "lowerarm_l"),
    };

    static string F(float v) => Math.Round(v, 4).ToString("0.####", CultureInfo.InvariantCulture);

    static void Collect(Node n, Transform3D at, Transform3D to, List<Vector3> v, List<int[]> t)
    {
        foreach (var c in n.GetChildren())
        {
            var m = c is Node3D c3 ? at * c3.Transform : at;
            if (c is MeshInstance3D mi && mi.Mesh != null)
                for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                {
                    var arr = mi.Mesh.SurfaceGetArrays(s);
                    var vs = (Vector3[])arr[(int)Mesh.ArrayType.Vertex];
                    var ix = arr[(int)Mesh.ArrayType.Index].VariantType == Variant.Type.Nil ? null : (int[])arr[(int)Mesh.ArrayType.Index];
                    int off = v.Count;
                    foreach (var p in vs) v.Add(to * (m * p));
                    if (ix == null) { for (int i = 0; i + 2 < vs.Length; i += 3) t.Add(new[] { off + i, off + i + 1, off + i + 2 }); }
                    else for (int i = 0; i + 2 < ix.Length; i += 3) t.Add(new[] { off + ix[i], off + ix[i + 1], off + ix[i + 2] });
                }
            Collect(c, m, to, v, t);
        }
    }

    public override void _Ready()
    {
        var root = ProjectSettings.GlobalizePath("res://").Replace("\\", "/");
        var dir = Path.GetFullPath(Path.Combine(root, "../tools/anim/data"));
        var sb = new StringBuilder("{\n");
        bool first = true;
        // Weapons that are data (art/weapons/weapons.json) are held in hand_r too, for fistfit.
        var held = new List<(string Id, string Bone)>(Pairs);
        if (Godot.FileAccess.FileExists(ArmsData.Path))
            foreach (var r in SurvivorUnchained.Play.WeaponsData.Parse(Godot.FileAccess.GetFileAsString(ArmsData.Path)))
                if (!held.Exists(p => p.Id == r.Id)) held.Add((r.Id, "hand_r"));
        foreach (var (id, bone) in held)
        {
            var piece = Arms.Make(id);
            piece.Transform = Arms.Seat(piece, id, bone);
            var v = new List<Vector3>();
            var t = new List<int[]>();
            Collect(piece, piece.Transform, Arms.MountTransform(id, bone, true), v, t);
            if (!first) sb.Append(",\n");
            first = false;
            sb.Append($"\"{id}@{bone}\": {{\"v\": [");
            sb.Append(string.Join(",", v.ConvertAll(p => $"[{F(p.X)},{F(p.Y)},{F(p.Z)}]")));
            sb.Append("], \"t\": [");
            sb.Append(string.Join(",", t.ConvertAll(a => $"[{a[0]},{a[1]},{a[2]}]")));
            sb.Append("]}");
            GD.Print($"{id}@{bone}: {v.Count} vertices, {t.Count} triangles");
            piece.QueueFree();
        }
        // Where each rides sheathed (Arms.Sheathed): the socket's bone and mount, and the piece (a sword with its
        // scabbard) in that bone's space, for tools_scenes/anim_review.gd with SHEATH=1. A piece with no socket
        // stays in hand and is not here. (armscheck.py reads only the entries with vertices at the top level.)
        sb.Append(",\n\"sheathed\": {");
        bool firstS = true;
        // Every kind has a piece here (the pieces no loadout holds yet too: armscheck.py --sockets measures each kind).
        var all = new List<(string Id, string Bone)>(Pairs);
        foreach (var id in Arms.All.Keys)
            if (!all.Exists(p => p.Id == id) && Arms.KindOf(id) != SurvivorUnchained.Play.WeaponKind.Staff) all.Add((id, "hand_r"));
        foreach (var (id, bone) in all)
        {
            if (Arms.Sheathed(id, bone == "hand_l") is not { } sock || Arms.SocketFacing(id, bone == "hand_l") is not { } face) continue;
            var piece = Arms.MakeSheathed(id, bone == "hand_l");
            var v = new List<Vector3>();
            var t = new List<int[]>();
            Collect(piece, Transform3D.Identity, sock.At, v, t);
            if (!firstS) sb.Append(",");
            firstS = false;
            var b = sock.At.Basis; var o = sock.At.Origin;
            sb.Append($"\n\"{id}@{bone}\": {{\"bone\": \"{sock.Bone}\", \"kind\": \"{Arms.KindOf(id)}\", \"socket\": \"{face.Socket}\", \"normal\": [{F(face.Normal.X)},{F(face.Normal.Y)},{F(face.Normal.Z)}], \"mount\": [[{F(b.X.X)},{F(b.Y.X)},{F(b.Z.X)},{F(o.X)}],[{F(b.X.Y)},{F(b.Y.Y)},{F(b.Z.Y)},{F(o.Y)}],[{F(b.X.Z)},{F(b.Y.Z)},{F(b.Z.Z)},{F(o.Z)}]], \"v\": [");
            sb.Append(string.Join(",", v.ConvertAll(p => $"[{F(p.X)},{F(p.Y)},{F(p.Z)}]")));
            sb.Append("], \"t\": [");
            sb.Append(string.Join(",", t.ConvertAll(a => $"[{a[0]},{a[1]},{a[2]}]")));
            sb.Append("]}");
            GD.Print($"sheathed {id}@{bone}: {sock.Bone}, {v.Count} vertices");
            piece.QueueFree();
        }
        sb.Append("\n}\n}\n");
        File.WriteAllText(Path.Combine(dir, "arms_local.json"), sb.ToString());

        // Her skeleton, as the game loads her (art/people/heroine.glb).
        var her = GD.Load<PackedScene>("res://art/people/heroine.glb").Instantiate<Node3D>();
        var skel = (Skeleton3D)her.FindChildren("*", "Skeleton3D", true, false)[0];
        var rb = new StringBuilder("{\n");
        string[] bones = { "hand_r", "hand_l", "lowerarm_l" };
        for (int i = 0; i < bones.Length; i++)
        {
            int j = skel.FindBone(bones[i]);
            var g = skel.GetBoneGlobalRest(j);
            var b = g.Basis;
            rb.Append($"\"{bones[i]}\": [[{F(b.X.X)},{F(b.Y.X)},{F(b.Z.X)},{F(g.Origin.X)}],[{F(b.X.Y)},{F(b.Y.Y)},{F(b.Z.Y)},{F(g.Origin.Y)}],[{F(b.X.Z)},{F(b.Y.Z)},{F(b.Z.Z)},{F(g.Origin.Z)}]]");
            rb.Append(i < bones.Length - 1 ? ",\n" : "\n");
        }
        rb.Append("}\n");
        File.WriteAllText(Path.Combine(dir, "arms_rest_godot.json"), rb.ToString());
        GD.Print("done");
        GetTree().Quit();
    }
}
