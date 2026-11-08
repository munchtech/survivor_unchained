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
        int totalFrames = 0, clips = 0, subTotal = 0;
        var saves = new List<(AnimationLibrary Lib, string File)>();
        // The blend base (P1Body.BlendBase): Godot's mixer blends each bone's turn from the skeleton's rest, R * prod_i
        // slerp(1, R^-1 q_i, w_i) (a scratch test: a RESET clip is not read), so a blend, a fade or a partial layer is A's
        // on A's rest and, played on B's own rest, not B's map of it: each B bone's local is A's turned by fixed frames on
        // either side (q = K_p^-1 a K_j) and a blend about a common base commutes with that only if B's base is the map
        // of A's rest, M = K_p^-1 R_A K_j. Off it, the 0.05 s fade into a blow left A's: fight_close's sword hand 22.7 mm,
        // the forearm 4.7 deg at frames 232/358 (P1 R1 pose 4). So B's keys are laid as R_B M^-1 q (B's mixer then blends
        // from M: R_B prod slerp(1, M^-1 q_i, w_i)) and P1BlendBase, first of B's modifiers, turns each such bone by
        // M R_B^-1: a clip alone plays as baked, every blend as A's mapped, a bone a clip leaves unkeyed lands on M (A's
        // own lands on A's rest).
        var (baseL, _) = bake.Frame(aRest);
        var keyTurn = new Quaternion[rig.Names.Length];
        var baseTurn = new Dictionary<string, Quaternion>();
        for (int j = 0; j < rig.Names.Length; j++)
        {
            var m = QOf(baseL[j]); var rb = QOf(bake.RestLocal(j));
            keyTurn[j] = (rb * m.Inverse()).Normalized();
            if (Ang(keyTurn[j], Quaternion.Identity) < 1e-3) keyTurn[j] = Quaternion.Identity;
            else baseTurn[rig.Names[j]] = (m * rb.Inverse()).Normalized();
        }
        var everRot = new HashSet<int>();
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
                    // (a shrug-driven B: A sampled before her HerShrug, which B runs at runtime as A does: P1 R1 arm chain)
                    var g = Sample(a, ap, pose, rig.ShrugDriven ? null : shrug, time);
                    var (L, G) = bake.Frame(g, cleanUsed, aKeyed);
                    var (dl, dr) = bake.ShoulderDrop(G);
                    sumL += dl; sumR += dr;
                    var (ml, mr) = bake.ShoulderDrop(bake.Map.Map(g));   // (the map alone: the clip's clavicle kept)
                    mapL += ml; mapR += mr;
                    if (dump != null) dump.Append((f > 0 ? ",\n" : "\n") + Mats(g));
                    Ls.Add(L); Gs.Add(G);
                    if (aIndex.TryGetValue("ball_l", out int bl) && aIndex.TryGetValue("ball_r", out int br)) { aBall[0].Add(g[bl].T()); aBall[1].Add(g[br].T()); aFoot[0].Add(g[aIndex["foot_l"]].T()); aFoot[1].Add(g[aIndex["foot_r"]].T()); }
                }
                var preLock = Ls.Select(x => x.ToArray()).ToList();   // (the sub keys skip the bones the foot lock moved)
                var locks = !raw && aBall[0].Count == frames ? bake.FootLock(Ls, Gs, aBall, aFoot, src.LoopMode != Animation.LoopModeEnum.None, Fps, new HashSet<int>(keyed), clean?.LockEase ?? P1Bake.LockEase) : new int[2];
                for (int f = 0; f < frames; f++)
                {
                    double time = Math.Min(f / Fps, src.Length);
                    var L = Ls[f];
                    dumpB.Append((f > 0 ? ",\n" : "\n") + (dump != null ? Mats(Gs[f]) : ""));
                    foreach (var (j, tr) in rotTrack)
                    {
                        var q = P1Body.T(P1M4.From(P1Retarget.Rot(L[j]), new P1V(0, 0, 0))).Basis.GetRotationQuaternion().Normalized();
                        dst.RotationTrackInsertKey(tr, time, (keyTurn[j] * q).Normalized());
                        var bytes = Encoding.ASCII.GetBytes($"{key}{j}{time:F4}{q.X:F6}{q.Y:F6}{q.Z:F6}{q.W:F6}");
                        sha.TransformBlock(bytes, 0, bytes.Length, null, 0);
                    }
                    foreach (var (j, tp) in posTrack)
                        dst.PositionTrackInsertKey(tp, time, new Vector3((float)L[j][0, 3], (float)L[j][1, 3], (float)L[j][2, 3]));
                }
                everRot.UnionWith(rotTrack.Keys);
                int subKeys = raw ? 0 : SubKeys(dst, a, ap, pose, rig.ShrugDriven ? null : shrug, bake, cleanUsed, aKeyed, rotTrack, Ls, preLock, src.Length, sha, key, keyTurn);
                subTotal += subKeys;
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
                GD.Print($"p1-bake: {key}: {frames} frames, {keyed.Count} keyed bones ({aKeyed.Count} on A){(subKeys > 0 ? $", {subKeys} sub keys" : "")}{(clean != null ? ", cleaned" : "")}{(locks.Sum() > 0 ? $", feet locked {locks[0]}/{locks[1]}" : "")}; trunk {(bake.Map.JointsMatched ? "matched" : "length-fraction")}{(unkeyed != "" ? $" (unkeyed {unkeyed})" : "")}" +
                         (town ? $"; shoulder joint over pelvis vs B rest, mean L {sumL / frames * 1000:F1} R {sumR / frames * 1000:F1} mm (map alone, the clip's clavicle: L {mapL / frames * 1000:F1} R {mapR / frames * 1000:F1})" : ""));
            }
            saves.Add((outLib, outFile));
        }
        if (only == "" && !Args.Has("p1-bake-raw") && saves.Count > 0)
        {
            var keyed = baseTurn.Where(kv => everRot.Contains(rig.Index[kv.Key])).OrderBy(kv => rig.Index[kv.Key]).ToList();
            var bb = new StringBuilder("{\"why\": \"P1BakeRun: B's blend base. Per bone some clip keys: the turn P1BlendBase lays on B's pose (left, local), M R_B^-1 (M: B's map of A's rest local, R_B: B's rest local); the clips' keys are R_B M^-1 q.\",\n\"bones\": {");
            bb.Append(string.Join(",", keyed.Select(kv => $"\n  \"{kv.Key}\": [{F(kv.Value.X)}, {F(kv.Value.Y)}, {F(kv.Value.Z)}, {F(kv.Value.W)}]")));
            bb.Append("\n}}\n");
            System.IO.File.WriteAllText(ProjectSettings.GlobalizePath(Out + "blend_base.json"), bb.ToString());
            GD.Print($"p1-bake: blend base: {keyed.Count} keyed bones turned (largest {keyed.Select(kv => Ang(kv.Value, Quaternion.Identity)).DefaultIfEmpty(0).Max():F1} deg)");
            foreach (var (outLib, outFile) in saves)
            {
                var err = ResourceSaver.Save(outLib, Out + outFile, ResourceSaver.SaverFlags.Compress);
                GD.Print($"p1-bake: wrote {outFile} ({outLib.GetAnimationList().Count} clips): {err}");
            }
        }
        sha.TransformFinalBlock(Array.Empty<byte>(), 0, 0);
        GD.Print($"p1-bake: {clips} clips, {totalFrames} frames, {subTotal} sub keys, keys digest {Convert.ToHexString(sha.Hash!)[..16]}, {(Time.GetTicksMsec() - t0) / 1000.0:F1} s");

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

    /// <summary>Sub keys' tolerance, degrees: a B bone's local turn between two of its keys (Godot slerps it) stays within
    /// this of B's own map of A at that instant. A plays its clips' 30 fps keys slerped per bone on A's skeleton; B's keys are
    /// A's map at the same instants, and the map does not commute with a slerp (B's girdle lays the clavicle on A's line,
    /// the upper arm keeps its mapped world turn under it, B's spine shares A's turn over more bones), so where A turns
    /// fast B left A's path between keys: fight_close's sword tip 94 mm off at frame 358 where A's sword turned 111 deg in
    /// 2 frames, 0.08 deg p95 on slow frames (P1 R1 pose 4). Five bones of 0.1 deg each put a 1.2 m reach (the sword's tip
    /// from the chest) within 10 mm.</summary>
    const double SubTol = 0.1;
    /// <summary>Finest sub key grid: 1/SubGrid of a 30 fps step (480 fps).</summary>
    const int SubGrid = 16;

    static Quaternion QOf(P1M4 m) => P1Body.T(P1M4.From(P1Retarget.Rot(m), new P1V(0, 0, 0))).Basis.GetRotationQuaternion().Normalized();

    static double Ang(Quaternion a, Quaternion b) => 2 * Math.Acos(Math.Min(1.0, Math.Abs((double)a.Dot(b)))) * 180 / Math.PI;

    /// <summary>Keys between the 30 fps keys where B's slerp leaves B's map of A (SubTol): per 30 fps step, A sampled at its
    /// midpoint; where any bone is off by over half the tolerance, A at SubGrid points over the step, and each bone keyed at
    /// the coarsest of 2, 4, 8, 16 even sub steps whose slerp holds every sample within SubTol (the bone's own keys only:
    /// a calm bone gets none). Bones the foot lock moved on either end keep the 30 fps keys (the lock is solved per frame).
    /// Returns the keys added.</summary>
    static int SubKeys(Animation dst, Skeleton3D a, AnimationPlayer ap, HerPose pose, HerShrug? shrug, P1Bake bake, P1Bake.Clean? clean,
        HashSet<int> aKeyed, Dictionary<int, int> rotTrack, List<P1M4[]> Ls, List<P1M4[]> preLock, double length,
        System.Security.Cryptography.SHA256 sha, string key, Quaternion[] keyTurn)
    {
        int frames = Ls.Count, added = 0;
        Quaternion Q(P1M4 m) => P1Body.T(P1M4.From(P1Retarget.Rot(m), new P1V(0, 0, 0))).Basis.GetRotationQuaternion().Normalized();
        bool Locked(int f, int j) => Ang(Q(Ls[f][j]), Q(preLock[f][j])) > 1e-4 || (Ls[f][j].T() - preLock[f][j].T()).Len() > 1e-7;
        var bones = rotTrack.Keys.ToArray();
        for (int f = 0; f + 1 < frames; f++)
        {
            double t0 = Math.Min(f / Fps, length), t1 = Math.Min((f + 1) / Fps, length);
            if (t1 - t0 < 1e-5) continue;
            var free = bones.Where(j => !Locked(f, j) && !Locked(f + 1, j)).ToArray();
            if (free.Length == 0) continue;
            var q0 = free.Select(j => Q(Ls[f][j])).ToArray();
            var q1 = free.Select(j => Q(Ls[f + 1][j])).ToArray();
            P1M4[] At(double t) => bake.Frame(Sample(a, ap, pose, shrug, t), clean, aKeyed).Local;
            var mid = At((t0 + t1) / 2);
            double worst = 0;
            for (int i = 0; i < free.Length; i++) worst = Math.Max(worst, Ang(Q(mid[free[i]]), q0[i].Slerp(q1[i], 0.5f)));
            if (worst < SubTol / 2) continue;
            // the grid: k = 0..SubGrid, its ends the 30 fps keys
            var grid = new Quaternion[SubGrid + 1][];
            grid[0] = q0; grid[SubGrid] = q1;
            for (int k = 1; k < SubGrid; k++)
            {
                var l = k == SubGrid / 2 ? mid : At(t0 + (t1 - t0) * k / SubGrid);
                grid[k] = free.Select(j => Q(l[j])).ToArray();
            }
            for (int i = 0; i < free.Length; i++)
            {
                int step = SubGrid;
                for (; step > 1; step /= 2)
                {
                    bool ok = true;
                    for (int k = 1; k < SubGrid && ok; k++)
                    {
                        int k0 = k / step * step;
                        if (k0 == k) continue;
                        ok = Ang(grid[k][i], grid[k0][i].Slerp(grid[k0 + step][i], (float)(k - k0) / step)) <= SubTol;
                    }
                    if (ok) break;
                }
                if (step == SubGrid) continue;
                for (int k = step; k < SubGrid; k += step)
                {
                    double t = t0 + (t1 - t0) * k / SubGrid;
                    var q = grid[k][i];
                    dst.RotationTrackInsertKey(rotTrack[free[i]], t, (keyTurn[free[i]] * q).Normalized());
                    var bytes = Encoding.ASCII.GetBytes($"{key}{free[i]}{t:F5}{q.X:F6}{q.Y:F6}{q.Z:F6}{q.W:F6}");
                    sha.TransformBlock(bytes, 0, bytes.Length, null, 0);
                    added++;
                }
            }
        }
        return added;
    }

    /// <summary>A at a clip's instant: her bones reset, the clip applied, HerPose and HerShrug run by hand (the engine's modifier pass off:
    /// Skeleton3D's Manual mode with Advance ran none here), her bones' globals read.</summary>
    static P1M4[] Sample(Skeleton3D a, AnimationPlayer ap, HerPose pose, HerShrug? shrug, double time)
    {
        a.ResetBonePoses();
        ap.Seek(time, true, true);
        pose._ProcessModificationWithDelta(1 / Fps);
        shrug?._ProcessModificationWithDelta(1 / Fps);
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
