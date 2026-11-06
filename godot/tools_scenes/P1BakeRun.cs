using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Text.Json;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Tools;

/// <summary>
/// The clip bridge (tools/body/bake_clips.sh runs tools_scenes/p1_bake.gd, which runs this): A (heroine.glb, as
/// People.Heroine builds it without --body p1) plays every library clip (People.Clips) and her own (OwnClips.Her)
/// under HerPose alone (her library carriage baked in: Native 1 on her own clips, 0 on the library's; no Look, chin,
/// neck sliders or cine curls), sampled at 30 fps from 0 to the clip's length inclusive, the modifiers advanced by hand
/// (HerPose's pass called directly, the engine's off; checked once against a normal process frame); each frame taken onto B by P1Bake (the map, the girdle hold, p1_clips.json's clean)
/// and keyed on B's bones. Writes art/people/body_p1/clips.res, her_clips.res and a_skeleton.json.
/// --p1-bake-only TEXT bakes only the clips whose names hold TEXT and writes nothing (a check).
/// </summary>
public partial class P1BakeRun : Node
{
    const double Fps = 30;
    const string Out = "res://art/people/body_p1/";

    sealed partial class Grab : SkeletonModifier3D
    {
        public P1M4[]? Pose;
        public int Count;
        public override void _ProcessModificationWithDelta(double delta)
        {
            var sk = GetSkeleton();
            Pose = new P1M4[sk.GetBoneCount()];
            for (int i = 0; i < Pose.Length; i++) Pose[i] = P1Body.M(sk.GetBoneGlobalPose(i));
            Count++;
        }
    }

    static string F(double v) => v.ToString("0.#######", CultureInfo.InvariantCulture);

    public override async void _Ready()
    {
        var t0 = Time.GetTicksMsec();
        var aRoot = GD.Load<PackedScene>("res://art/people/heroine.glb").Instantiate<Node3D>();
        AddChild(aRoot);
        var a = (Skeleton3D)aRoot.FindChildren("*", "Skeleton3D", true, false)[0];
        var pose = new HerPose();
        a.AddChild(pose);
        var grab = new Grab();
        a.AddChild(grab);
        pose.Active = grab.Active = false;
        var ap = new AnimationPlayer();
        aRoot.AddChild(ap);
        ap.RootNode = "..";
        ap.CallbackModeProcess = AnimationMixer.AnimationCallbackModeProcess.Manual;
        ap.AddAnimationLibrary("", People.Clips());
        var her = OwnClips.Her.Library();
        if (her != null) ap.AddAnimationLibrary(OwnClips.Her.Name, her);

        int na = a.GetBoneCount();
        var aNames = Enumerable.Range(0, na).Select(i => a.GetBoneName(i)).ToArray();
        var aParent = Enumerable.Range(0, na).Select(i => a.GetBoneParent(i)).ToArray();
        var aRest = Enumerable.Range(0, na).Select(i => P1Body.M(a.GetBoneGlobalRest(i))).ToArray();
        WriteSkeleton(aNames, aParent, aRest);

        var bRoot = GD.Load<PackedScene>(P1Body.Dir + "body.glb").Instantiate<Node3D>();
        var bs = (Skeleton3D)bRoot.FindChildren("*", "Skeleton3D", true, false)[0];
        GD.Print($"p1-bake: A {na} bones at {aRoot.GetPathTo(a)}, B {bs.GetBoneCount()} bones at {bRoot.GetPathTo(bs)}");
        int nb = bs.GetBoneCount();
        var rig = new P1Rig(Enumerable.Range(0, nb).Select(i => bs.GetBoneName(i)).ToArray(), Enumerable.Range(0, nb).Select(i => bs.GetBoneParent(i)).ToArray(),
            Enumerable.Range(0, nb).Select(i => P1Body.M(bs.GetBoneGlobalRest(i))).ToArray(), JsonDocument.Parse(FileAccess.GetFileAsString(P1Body.Dir + "rig.json")).RootElement);
        bRoot.Free();
        var bake = new P1Bake(rig, new P1Retarget(aNames, aParent, aRest, rig));
        var cleanPath = ProjectSettings.GlobalizePath("res://") + "../tools/body/p1_clips.json";
        var cleans = System.IO.File.Exists(cleanPath) ? P1Bake.ParseCleans(System.IO.File.ReadAllText(cleanPath)) : new();
        GD.Print($"p1-bake: {cleans.Count} clip entries in p1_clips.json");

        var aIndex = new Dictionary<string, int>();
        for (int i = 0; i < na; i++) aIndex[aNames[i]] = i;
        string only = Args.Get("p1-bake-only") ?? "";
        var sha = System.Security.Cryptography.SHA256.Create();
        int totalFrames = 0, clips = 0;
        foreach (var (libName, lib, native, outFile) in new[] { ("", People.Clips(), 0f, "clips.res"), (OwnClips.Her.Name, her, 1f, "her_clips.res") })
        {
            if (lib == null) continue;
            var outLib = new AnimationLibrary();
            foreach (var name in lib.GetAnimationList())
            {
                string nm = name;
                if (only != "" && !nm.Contains(only)) continue;
                var src = lib.GetAnimation(nm);
                var key = libName == "" ? nm : $"{libName}/{nm}";
                pose.Native = native;
                // A's keyed bones (rotation or position tracks on her skeleton), and the root/pelvis position tracks
                var aKeyed = new HashSet<int>(); var aPos = new HashSet<int>();
                string skelPath = "Armature/Skeleton3D";
                var dst = new Animation { Length = src.Length, LoopMode = src.LoopMode, Step = (float)(1 / Fps) };
                for (int t = 0; t < src.GetTrackCount(); t++)
                {
                    var ty = src.TrackGetType(t);
                    var path = src.TrackGetPath(t);
                    if (ty is Animation.TrackType.Rotation3D or Animation.TrackType.Position3D or Animation.TrackType.Scale3D && path.GetSubNameCount() > 0)
                    {
                        skelPath = path.GetConcatenatedNames();
                        if (!aIndex.TryGetValue(path.GetSubName(0), out int ai)) continue;
                        if (ty == Animation.TrackType.Position3D) aPos.Add(ai);
                        if (ty != Animation.TrackType.Scale3D) aKeyed.Add(ai);
                    }
                    else src.CopyTrack(t, dst);   // (blend shapes, values, methods: as they are)
                }
                var keyed = bake.Keyed(aKeyed).OrderBy(j => j).ToList();
                cleans.TryGetValue(nm, out var clean);
                var rotTrack = new Dictionary<int, int>(); var posTrack = new Dictionary<int, int>();
                foreach (int j in keyed)
                {
                    int tr = dst.AddTrack(Animation.TrackType.Rotation3D);
                    dst.TrackSetPath(tr, $"{skelPath}:{rig.Names[j]}");
                    rotTrack[j] = tr;
                    bool pos = j == bake.Pelvis && aPos.Contains(aIndex["pelvis"]) || j == bake.Root && aIndex.ContainsKey("root") && aPos.Contains(aIndex["root"]);
                    if (pos) { int tp = dst.AddTrack(Animation.TrackType.Position3D); dst.TrackSetPath(tp, $"{skelPath}:{rig.Names[j]}"); posTrack[j] = tp; }
                }
                ap.Play(key);
                int frames = (int)Math.Floor(src.Length * Fps + 1e-6) + 1;
                if (src.Length - (frames - 1) / Fps > 1e-4) frames++;   // (the clip's last instant keyed too)
                double sumL = 0, sumR = 0, mapL = 0, mapR = 0;
                for (int f = 0; f < frames; f++)
                {
                    double time = Math.Min(f / Fps, src.Length);
                    var g = Sample(a, ap, pose, time);
                    var (L, G) = bake.Frame(g, clean);
                    var (dl, dr) = bake.ShoulderDrop(G);
                    sumL += dl; sumR += dr;
                    var (ml, mr) = bake.ShoulderDrop(bake.Map.Map(g));   // (the map alone: the clip's clavicle kept)
                    mapL += ml; mapR += mr;
                    foreach (var (j, tr) in rotTrack)
                    {
                        var q = P1Body.T(P1M4.From(P1Retarget.Rot(L[j]), new P1V(0, 0, 0))).Basis.GetRotationQuaternion().Normalized();
                        dst.RotationTrackInsertKey(tr, time, q);
                        var bytes = Encoding.ASCII.GetBytes($"{key}{j}{time:F4}{q.X:F6}{q.Y:F6}{q.Z:F6}{q.W:F6}");
                        sha.TransformBlock(bytes, 0, bytes.Length, null, 0);
                    }
                    foreach (var (j, tp) in posTrack)
                        dst.PositionTrackInsertKey(tp, time, new Vector3((float)L[j][0, 3], (float)L[j][1, 3], (float)L[j][2, 3]));
                }
                outLib.AddAnimation(nm, dst);
                totalFrames += frames; clips++;
                bool town = nm.StartsWith("idle_") || nm == "Idle_Loop" || nm == "Idle";
                GD.Print($"p1-bake: {key}: {frames} frames, {keyed.Count} keyed bones ({aKeyed.Count} on A){(clean != null ? ", cleaned" : "")}" +
                         (town ? $"; shoulder joint over pelvis vs B rest, mean L {sumL / frames * 1000:F1} R {sumR / frames * 1000:F1} mm (map alone, the clip's clavicle: L {mapL / frames * 1000:F1} R {mapR / frames * 1000:F1})" : ""));
            }
            if (only != "") continue;
            var err = ResourceSaver.Save(outLib, Out + outFile, ResourceSaver.SaverFlags.Compress);
            GD.Print($"p1-bake: wrote {outFile} ({outLib.GetAnimationList().Count} clips): {err}");
        }
        sha.TransformFinalBlock(Array.Empty<byte>(), 0, 0);
        GD.Print($"p1-bake: {clips} clips, {totalFrames} frames, keys digest {Convert.ToHexString(sha.Hash!)[..16]}, {(Time.GetTicksMsec() - t0) / 1000.0:F1} s");

        // One frame against a normal process frame (the modifiers run by the engine, not by hand).
        var test = OwnClips.Her.Has("idle_reaver_town") ? "her/idle_reaver_town" : "Idle_Loop";
        pose.Native = test.StartsWith("her/") ? 1 : 0;
        ap.Play(test);
        var manual = Sample(a, ap, pose, 0.5);
        pose.Active = grab.Active = true;
        a.ResetBonePoses();
        ap.Seek(0.5, true, true);
        int before = grab.Count;
        for (int k = 0; k < 4 && grab.Count == before; k++) await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
        double worst = 0;
        if (grab.Pose != null) for (int i = 0; i < na; i++) worst = Math.Max(worst, (grab.Pose[i].T() - manual[i].T()).Len());
        GD.Print($"p1-bake: check {test} @0.5 s manual vs process frame: worst joint {worst * 1000:F4} mm ({grab.Count - before} process updates)");
        GetTree().Quit();
    }

    /// <summary>A at a clip's instant: her bones reset, the clip applied, HerPose run by hand (the engine's modifier pass off:
    /// Skeleton3D's Manual mode with Advance ran none here), her bones' globals read.</summary>
    static P1M4[] Sample(Skeleton3D a, AnimationPlayer ap, HerPose pose, double time)
    {
        a.ResetBonePoses();
        ap.Seek(time, true, true);
        pose._ProcessModificationWithDelta(1 / Fps);
        var g = new P1M4[a.GetBoneCount()];
        for (int i = 0; i < g.Length; i++) g[i] = P1Body.M(a.GetBoneGlobalPose(i));
        return g;
    }

    static void WriteSkeleton(string[] names, int[] parent, P1M4[] rest)
    {
        var sb = new StringBuilder();
        sb.Append("{\n  \"why\": \"A's skeleton (heroine.glb): bone names, parents, global rests (4x4 row-major, skeleton space), written by the clip bridge (tools_scenes/P1BakeRun.cs) for B's runtime role map and hair rebind without loading A\",\n");
        sb.Append("  \"names\": [" + string.Join(", ", names.Select(n => $"\"{n}\"")) + "],\n");
        sb.Append("  \"parent\": [" + string.Join(", ", parent) + "],\n  \"rest\": [\n");
        for (int i = 0; i < rest.Length; i++)
        {
            var m = rest[i];
            sb.Append("    [" + string.Join(", ", Enumerable.Range(0, 4).Select(r => "[" + string.Join(", ", Enumerable.Range(0, 4).Select(c => F(m[r, c]))) + "]")) + "]" + (i < rest.Length - 1 ? ",\n" : "\n"));
        }
        sb.Append("  ]\n}\n");
        using var f = FileAccess.Open(Out + "a_skeleton.json", FileAccess.ModeFlags.Write);
        f.StoreString(sb.ToString());
    }
}
