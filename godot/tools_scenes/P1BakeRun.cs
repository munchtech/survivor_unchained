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
/// under the layers that make A's final role-bone pose in the game (HerPose: her library carriage baked in, Native 1 on her
/// own clips, 0 on the library's, no chin, neck sliders or cine curls; then HerShrug, her clavicle lift over 60 deg),
/// sampled at 30 fps from 0 to the clip's length inclusive, the modifiers advanced by hand
/// (their passes called directly, the engine's off; checked once against a normal process frame); each frame taken onto B by P1Bake (the map, the girdle, p1_clips.json's clean)
/// and keyed on B's bones. Writes art/people/body_p1/clips.res, her_clips.res and a_skeleton.json.
/// Each her idle_{calling}_town is baked a second time as idle_{calling}_look: A's Look, HerPose's Look arms at full weight as GameFront sets them.
/// The clips with a tools/body/p1_clips.json entry also dump A's and B's posed globals per frame to tools/body/out/clips/
/// NAME.json (git-ignored; tools/body/clipcheck.py measures them); --p1-bake-only dumps too.
/// --p1-bake-raw (with --p1-bake-only) skips the clean and the foot lock: clipcheck's baseline.
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
        var shrug = new HerShrug();
        a.AddChild(shrug);
        pose.Active = shrug.Active = grab.Active = false;
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
            // (name, source clip, the Look's arms)
            var jobs = lib.GetAnimationList().Select(x => ((string)x, (string)x, false)).ToList();
            jobs.AddRange(jobs.Where(x => libName != "" && x.Item1.StartsWith("idle_") && x.Item1.EndsWith("_town")).Select(x => (x.Item1[..^5] + "_look", x.Item1, true)).ToList());
            foreach (var (nm, srcName, lookArms) in jobs)
            {
                if (only != "" && !nm.Contains(only)) continue;
                var src = lib.GetAnimation(srcName);
                var key = libName == "" ? srcName : $"{libName}/{srcName}";
                pose.Native = native;
                pose.LookOn = lookArms;
                pose.LookArmsDownR = lookArms ? HerPose.LookDownR : 0;
                pose.LookSwivelL = lookArms ? HerPose.LookSwivel : 0;
                a.ResetBonePoses();
                pose._ProcessModificationWithDelta(10);   // (the Look's weight straight to its end, or back to none)
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
                bool raw = Args.Has("p1-bake-raw");   // (a measuring baseline: the map and the girdle hold only, no clean, no foot lock)
                var cleanUsed = raw && clean != null ? new P1Bake.Clean() : clean;
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
                // the keys dump (tools/body/clipcheck.py): the clips with a p1_clips.json entry, A's and B's globals per frame
                var dump = clean != null ? new StringBuilder() : null;
                dump?.Append($"{{\"name\": \"{nm}\", \"fps\": {F(Fps)}, \"length\": {F(src.Length)}, \"loop\": {(src.LoopMode != Animation.LoopModeEnum.None ? "true" : "false")}, \"frames\": {frames},\n" +
                    $"\"b_names\": [{string.Join(", ", rig.Names.Select(x => $"\"{x}\""))}],\n\"b_parent\": [{string.Join(", ", rig.Parent)}],\n\"b_rest\": {Mats(rig.Rest)},\n" +
                    $"\"keyed\": [{string.Join(", ", keyed.Select(j => $"\"{rig.Names[j]}\""))}],\n\"a_names\": [{string.Join(", ", aNames.Select(x => $"\"{x}\""))}],\n\"a_parent\": [{string.Join(", ", aParent)}],\n\"a_rest\": {Mats(aRest)},\n\"A\": [");
                var dumpB = new StringBuilder();
                var Ls = new List<P1M4[]>(); var Gs = new List<P1M4[]>();
                var aBall = new[] { new List<P1V>(), new List<P1V>() }; var aFoot = new[] { new List<P1V>(), new List<P1V>() };
                for (int f = 0; f < frames; f++)
                {
                    double time = Math.Min(f / Fps, src.Length);
                    var g = Sample(a, ap, pose, shrug, time);
                    var (L, G) = bake.Frame(g, cleanUsed, aKeyed);
                    var (dl, dr) = bake.ShoulderDrop(G);
                    sumL += dl; sumR += dr;
                    var (ml, mr) = bake.ShoulderDrop(bake.Map.Map(g));   // (the map alone: the clip's clavicle kept)
                    mapL += ml; mapR += mr;
                    if (dump != null) dump.Append((f > 0 ? ",\n" : "\n") + Mats(g));
                    Ls.Add(L); Gs.Add(G);
                    if (aIndex.TryGetValue("ball_l", out int bl) && aIndex.TryGetValue("ball_r", out int br)) { aBall[0].Add(g[bl].T()); aBall[1].Add(g[br].T()); aFoot[0].Add(g[aIndex["foot_l"]].T()); aFoot[1].Add(g[aIndex["foot_r"]].T()); }
                }
                var locks = !raw && aBall[0].Count == frames ? bake.FootLock(Ls, Gs, aBall, aFoot, src.LoopMode != Animation.LoopModeEnum.None, Fps, new HashSet<int>(keyed), clean?.LockEase ?? P1Bake.LockEase) : new int[2];
                for (int f = 0; f < frames; f++)
                {
                    double time = Math.Min(f / Fps, src.Length);
                    var L = Ls[f];
                    dumpB.Append((f > 0 ? ",\n" : "\n") + (dump != null ? Mats(Gs[f]) : ""));
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
                if (dump != null)
                {
                    dump.Append("],\n\"B\": [").Append(dumpB).Append("]}\n");
                    var dir = ProjectSettings.GlobalizePath("res://") + "../tools/body/out/clips/";
                    System.IO.Directory.CreateDirectory(dir);
                    System.IO.File.WriteAllText(dir + nm + ".json", dump.ToString());
                }
                outLib.AddAnimation(nm, dst);
                totalFrames += frames; clips++;
                bool town = nm.StartsWith("idle_") || nm == "Idle_Loop" || nm == "Idle";
                var unkeyed = string.Join(",", bake.Map.Unkeyed(aKeyed));
                GD.Print($"p1-bake: {key}: {frames} frames, {keyed.Count} keyed bones ({aKeyed.Count} on A){(clean != null ? ", cleaned" : "")}{(locks.Sum() > 0 ? $", feet locked {locks[0]}/{locks[1]}" : "")}; trunk {(bake.Map.JointsMatched ? "matched" : "length-fraction")}{(unkeyed != "" ? $" (unkeyed {unkeyed})" : "")}" +
                         (town ? $"; shoulder joint over pelvis vs B rest, mean L {sumL / frames * 1000:F1} R {sumR / frames * 1000:F1} mm (map alone, the clip's clavicle: L {mapL / frames * 1000:F1} R {mapR / frames * 1000:F1})" : ""));
            }
            if (only != "" || Args.Has("p1-bake-raw")) continue;   // (a check or the raw baseline: nothing written)
            var err = ResourceSaver.Save(outLib, Out + outFile, ResourceSaver.SaverFlags.Compress);
            GD.Print($"p1-bake: wrote {outFile} ({outLib.GetAnimationList().Count} clips): {err}");
        }
        sha.TransformFinalBlock(Array.Empty<byte>(), 0, 0);
        GD.Print($"p1-bake: {clips} clips, {totalFrames} frames, keys digest {Convert.ToHexString(sha.Hash!)[..16]}, {(Time.GetTicksMsec() - t0) / 1000.0:F1} s");

        // One frame against a normal process frame (the modifiers run by the engine, not by hand).
        var test = OwnClips.Her.Has("idle_reaver_town") ? "her/idle_reaver_town" : "Idle_Loop";
        pose.Native = test.StartsWith("her/") ? 1 : 0;
        ap.Play(test);
        pose.LookOn = false; pose.LookArmsDownR = pose.LookSwivelL = 0;
        a.ResetBonePoses();
        pose._ProcessModificationWithDelta(10);
        var manual = Sample(a, ap, pose, shrug, 0.5);
        pose.Active = shrug.Active = grab.Active = true;
        a.ResetBonePoses();
        ap.Seek(0.5, true, true);
        int before = grab.Count;
        for (int k = 0; k < 4 && grab.Count == before; k++) await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
        double worst = 0;
        if (grab.Pose != null) for (int i = 0; i < na; i++) worst = Math.Max(worst, (grab.Pose[i].T() - manual[i].T()).Len());
        GD.Print($"p1-bake: check {test} @0.5 s manual vs process frame: worst joint {worst * 1000:F4} mm ({grab.Count - before} process updates)");
        GetTree().Quit();
    }

    /// <summary>A at a clip's instant: her bones reset, the clip applied, HerPose and HerShrug run by hand (the engine's modifier pass off:
    /// Skeleton3D's Manual mode with Advance ran none here), her bones' globals read.</summary>
    static P1M4[] Sample(Skeleton3D a, AnimationPlayer ap, HerPose pose, HerShrug shrug, double time)
    {
        a.ResetBonePoses();
        ap.Seek(time, true, true);
        pose._ProcessModificationWithDelta(1 / Fps);
        shrug._ProcessModificationWithDelta(1 / Fps);
        var g = new P1M4[a.GetBoneCount()];
        for (int i = 0; i < g.Length; i++) g[i] = P1Body.M(a.GetBoneGlobalPose(i));
        return g;
    }

    /// <summary>Matrices as JSON: [[12 floats: the 3x4 rows]...], 5 decimals.</summary>
    static string Mats(P1M4[] m) => "[" + string.Join(",", m.Select(x => "[" + string.Join(",", Enumerable.Range(0, 12).Select(k => x[k / 4, k % 4].ToString("0.#####", CultureInfo.InvariantCulture))) + "]")) + "]";

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
