using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.World;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Tools;

/// <summary>
/// A kit townsperson as the town builds them (PersonView: People.Build, Arms.Hold with the folk's plain mounts), playing a
/// clip, skinned on the CPU at N times across it: every body and outfit vertex (world metres, its normal and its top
/// bone) and every vertex of what it holds (by holding bone), plus its arm and foot joints, to JSON for
/// tools/anim/folkhold.py (clearance, tip and foot heights, elbow bend). tools_scenes/folk_hold.gd runs it.
///   Godot --headless --path godot -s res://tools_scenes/folk_hold.gd -- OUT.json WHO CLIP N
///   WHO: watch (a gate Watchman), def.ID (npcs.json, e.g. def.keegan); CLIP: a game name played through People.Clip
///   (Idle_Shield_Loop, Idle_Watch) or a library name (folk/m_idle_watch).
/// </summary>
public partial class FolkHold : Node
{
    PersonView view = null!;
    string outPath = "", clip = "";
    int n, k = -1, wait;
    float len;
    readonly List<string> frames = new();

    static string F(float v) => Math.Round(v, 4).ToString("0.####", CultureInfo.InvariantCulture);
    static string V(Vector3 v) => $"[{F(v.X)},{F(v.Y)},{F(v.Z)}]";
    static string M(Transform3D t) => $"[{F(t.Basis.Column0.X)},{F(t.Basis.Column0.Y)},{F(t.Basis.Column0.Z)},{F(t.Basis.Column1.X)},{F(t.Basis.Column1.Y)},{F(t.Basis.Column1.Z)},{F(t.Basis.Column2.X)},{F(t.Basis.Column2.Y)},{F(t.Basis.Column2.Z)},{F(t.Origin.X)},{F(t.Origin.Y)},{F(t.Origin.Z)}]";

    public override void _Ready()
    {
        var a = OS.GetCmdlineUserArgs();
        outPath = a[0];
        var who = a[1];
        clip = a[2];
        n = int.Parse(a[3]);
        var rng = new Random(1);
        PersonSpec spec; Held? arms = null; double scale = 1;
        if (who == "watch") { spec = Folk.Person(FolkRole.Watch, Lore.WatchLook, rng); arms = new Held { Right = "viking_sword", Forearm = "shield_round" }; }
        else if (who.StartsWith("def.") && Lore.Person(who[4..]) is { } def) { spec = def.Person ?? new PersonSpec { Sex = Rpg.Sex.Male }; arms = def.Arms; scale = def.Scale ?? 1; }
        else throw new ArgumentException($"who? {who}");
        view = new PersonView(spec, arms, 0.8 * scale);
        AddChild(view);
        var p = view.Person;
        var name = clip.StartsWith(FolkClips.Prefix) ? clip : People.Clip(p, clip);
        GD.Print($"folk_hold: {who} {clip} -> {name}");
        clip = name;
        p.Anim.Play(name);
        p.Anim.SpeedScale = 0;
        len = (float)p.Anim.CurrentAnimationLength;
    }

    public override void _Process(double delta)
    {
        if (wait > 0) { if (--wait == 0) Grab(); return; }
        k++;
        if (k >= n)
        {
            File.WriteAllText(outPath, "{\"clip\":\"" + clip + "\",\"length\":" + F(len) + ",\"frames\":[\n" + string.Join(",\n", frames) + "]}");
            GD.Print($"folk_hold: wrote {outPath}");
            GetTree().Quit();
            return;
        }
        view.Person.Anim.Seek(len * k / n, true);
        wait = 3;
    }

    void Grab()
    {
        var p = view.Person;
        var skel = p.Skeleton;
        var SG = skel.GlobalTransform;
        var sb = new StringBuilder();
        sb.Append("{\"t\":").Append(F(len * k / n)).Append(",\"bones\":{");
        sb.Append(string.Join(",", new[] { "upperarm_l", "lowerarm_l", "hand_l", "upperarm_r", "lowerarm_r", "hand_r", "foot_l", "foot_r", "ball_l", "ball_r", "pelvis", "thigh_l", "thigh_r" }
            .Select(b => $"\"{b}\":{V(SG * skel.GetBoneGlobalPose(skel.FindBone(b)).Origin)}")));
        // Every bone's pose in the skeleton's space (basis columns, then origin), and the skeleton's own, for
        // folkhold.py's quick model (the town's own bone lengths and scales, posed by another clip's turns).
        sb.Append("},\"skel\":").Append(M(SG)).Append(",\"pose\":{");
        sb.Append(string.Join(",", Enumerable.Range(0, skel.GetBoneCount()).Select(b => $"\"{skel.GetBoneName(b)}\":{M(skel.GetBoneGlobalPose(b))}")));
        sb.Append("},\"body\":{\"v\":[");
        var bv = new List<string>(); var bn = new List<string>(); var bb = new List<string>();
        var boneNames = new List<string>();
        var boneIx = new Dictionary<string, int>();
        foreach (var mi in skel.GetChildren().OfType<MeshInstance3D>())
        {
            if (mi.Mesh == null || mi.Skin == null || !mi.Visible) continue;
            var skin = mi.Skin;
            var M = new Transform3D[skin.GetBindCount()];
            var names = new string[M.Length];
            for (int bi = 0; bi < M.Length; bi++)
            {
                var bname = skin.GetBindName(bi);
                int b = bname != "" ? skel.FindBone(bname) : skin.GetBindBone(bi);
                M[bi] = SG * skel.GetBoneGlobalPose(b) * skin.GetBindPose(bi);
                names[bi] = skel.GetBoneName(b);
            }
            for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
            {
                var arr = mi.Mesh.SurfaceGetArrays(s);
                var pv = (Vector3[])arr[(int)Mesh.ArrayType.Vertex];
                var nv = (Vector3[])arr[(int)Mesh.ArrayType.Normal];
                if (arr[(int)Mesh.ArrayType.Bones].VariantType == Godot.Variant.Type.Nil) continue;
                var bones = (int[])arr[(int)Mesh.ArrayType.Bones];
                var ws = (float[])arr[(int)Mesh.ArrayType.Weights];
                int per = bones.Length / pv.Length;
                for (int i = 0; i < pv.Length; i++)
                {
                    int best = 0; var g = Vector3.Zero; var gn = Vector3.Zero;
                    for (int j = 0; j < per; j++)
                    {
                        float w = ws[i * per + j];
                        if (w > ws[i * per + best]) best = j;
                        if (w > 0) { var m = M[bones[i * per + j]]; g += (m * pv[i]) * w; gn += (m.Basis * nv[i]) * w; }
                    }
                    var top = names[bones[i * per + best]];
                    if (!boneIx.TryGetValue(top, out var ix)) { ix = boneNames.Count; boneIx[top] = ix; boneNames.Add(top); }
                    bv.Add(V(g)); bn.Add(V(gn.Normalized())); bb.Add(ix.ToString(CultureInfo.InvariantCulture));
                }
            }
        }
        sb.Append(string.Join(",", bv)).Append("],\"n\":[").Append(string.Join(",", bn)).Append("],\"bone\":[").Append(string.Join(",", bb));
        sb.Append("],\"bones\":[").Append(string.Join(",", boneNames.Select(b => $"\"{b}\""))).Append("]},\"held\":{");
        var held = new List<string>();
        foreach (var att in skel.GetChildren().OfType<BoneAttachment3D>())
        {
            var pts = new List<string>();
            foreach (var mi in att.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>())
            {
                if (mi.Mesh == null) continue;
                var gt = mi.GlobalTransform;
                for (int s = 0; s < mi.Mesh.GetSurfaceCount(); s++)
                    foreach (var v in (Vector3[])mi.Mesh.SurfaceGetArrays(s)[(int)Mesh.ArrayType.Vertex]) pts.Add(V(gt * v));
            }
            if (pts.Count > 0) held.Add($"\"{att.BoneName}\":[{string.Join(",", pts)}]");
        }
        sb.Append(string.Join(",", held)).Append("}}");
        frames.Add(sb.ToString());
        GD.Print($"folk_hold: t {len * k / n:0.00} s: {bv.Count} body vertices, {held.Count} held");
    }
}
