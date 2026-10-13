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
        foreach (var (id, bone) in Pairs)
        {
            var piece = Arms.Make(id);
            piece.Transform = Arms.PieceTransform(id);
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
        sb.Append("\n}\n");
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
