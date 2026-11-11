using System;
using System.Linq;
using System.Text.Json;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Tools;

/// <summary>
/// P4 clips packed for the game (tools/anim/p4_pack.sh runs tools_scenes/p4_pack.gd, which runs this): every JUDGED
/// (P4Gate: p4.py judged) art/people/body_p1/p4/*.json; the unjudged are skipped so they cannot replace a shipped bridge
/// clip, and a review pack (p4_pack.sh --review: unjudged included, for shots and judges, never to commit) takes all: (tools/anim/p4.py build: local rotations of B's keyed bones as Godot quaternions
/// [x, y, z, w], root and pelvis local positions, frames at fps, a loop's last frame its first) into
/// art/people/body_p1/p4_clips.res, an AnimationLibrary: a rotation track per keyed bone, position tracks for root and
/// pelvis, the loop mode from the clip, length (frames-1)/fps, step 1/fps. The skeleton track path is the bridge clips'
/// own (read from her_clips.res, as P1BakeRun writes it), so P4 clips drop into the same tree. P1Body.HerClips lays
/// them over the bridge clips. A clip's top-level "beats" go to data/anim/her_events.json (HerEvents).
/// </summary>
public partial class P4Pack : Node
{
    public override void _Ready()
    {
        var dir = P1Body.Dir + "p4/";
        string skelPath = "Armature/Skeleton3D";
        var her = P1Body.Dir + "her_clips.res";
        if (ResourceLoader.Exists(her))
        {
            var lib0 = GD.Load<AnimationLibrary>(her);
            var a0 = lib0.GetAnimation(lib0.GetAnimationList()[0]);
            for (int t = 0; t < a0.GetTrackCount(); t++)
                if (a0.TrackGetType(t) == Animation.TrackType.Rotation3D) { skelPath = a0.TrackGetPath(t).GetConcatenatedNames(); break; }
        }
        // B's blend base (P1BlendBase, first of B's modifiers, turns each of its bones by t on the mixer's pose, for the
        // bridge clips' keys R_B M^-1 q): a P4 clip is keyed in B's own locals, so its keys on those bones are written
        // t^-1 q, and t (t^-1 q) = q: the clip plays exactly as built while the bridge clips need the base.
        var baseTurn = P1Body.BlendBase().ToDictionary(x => x.Bone, x => x.Turn);
        var outLib = new AnimationLibrary();
        var (review, reviewNames) = P4Gate.ReviewOf(OS.GetCmdlineUserArgs());
        if (review || reviewNames.Count > 0)
        {
            outLib.SetMeta("review", true);
            GD.Print("p4-pack: REVIEW PACK: " + (review ? "unjudged clips included" : $"unjudged taken by name: {string.Join(", ", reviewNames.OrderBy(n => n))}") +
                     ". For shots and judges in this worktree only; never commit or hand its her_events.json on");
        }
        var builtNames = new HashSet<string>();
        int skipped = 0;
        var events = new Dictionary<string, HerEvents.Beats>();
        var files = DirAccess.GetFilesAt(dir).Where(f => f.EndsWith(".json")).OrderBy(f => f).ToArray();
        foreach (var file in files)
        {
            using var d = JsonDocument.Parse(FileAccess.GetFileAsString(dir + file));
            var r = d.RootElement;
            string name = r.GetProperty("name").GetString()!;
            builtNames.Add(name);
            if (!P4Gate.Takes(r, name, review, reviewNames))
            {
                skipped++;
                GD.Print($"p4-pack: SKIPPED {name}: not judged (the bridge clip keeps playing; a review pack takes it: p4_pack.sh --review)");
                continue;
            }
            double fps = r.GetProperty("fps").GetDouble();
            int frames = r.GetProperty("frames").GetInt32();
            bool loop = r.GetProperty("loop").GetBoolean();
            var anim = new Animation { Length = (float)((frames - 1) / fps), LoopMode = loop ? Animation.LoopModeEnum.Linear : Animation.LoopModeEnum.None, Step = (float)(1 / fps) };
            int bones = 0, based = 0;
            foreach (var b in r.GetProperty("rot").EnumerateObject())
            {
                int tr = anim.AddTrack(Animation.TrackType.Rotation3D);
                anim.TrackSetPath(tr, $"{skelPath}:{b.Name}");
                var pre = baseTurn.TryGetValue(b.Name, out var t) ? t.Inverse() : Quaternion.Identity;
                int f = 0;
                foreach (var q in b.Value.EnumerateArray())
                {
                    var v = q.EnumerateArray().Select(x => (float)x.GetDouble()).ToArray();
                    anim.RotationTrackInsertKey(tr, f++ / fps, (pre * new Quaternion(v[0], v[1], v[2], v[3]).Normalized()).Normalized());
                }
                bones++;
                if (baseTurn.ContainsKey(b.Name)) based++;
            }
            foreach (var b in r.GetProperty("pos").EnumerateObject())
            {
                int tp = anim.AddTrack(Animation.TrackType.Position3D);
                anim.TrackSetPath(tp, $"{skelPath}:{b.Name}");
                int f = 0;
                foreach (var p in b.Value.EnumerateArray())
                {
                    var v = p.EnumerateArray().Select(x => (float)x.GetDouble()).ToArray();
                    anim.PositionTrackInsertKey(tp, f++ / fps, new Vector3(v[0], v[1], v[2]));
                }
            }
            // A gait's ground speed at 1.0x (its locked stance's, m/s of B's skeleton): the game plays it at this on B.
            if (r.TryGetProperty("speed_mps", out var sp) && sp.ValueKind == System.Text.Json.JsonValueKind.Number) anim.SetMeta("speed", sp.GetDouble());
            // The json's top-level "meta" object, key by key onto the clip (stance, layer, pelvis_mean...): strings, bools,
            // numbers and number arrays (OwnClips and PelvisCounter read them back).
            if (r.TryGetProperty("meta", out var mt) && mt.ValueKind == System.Text.Json.JsonValueKind.Object)
                foreach (var kv in mt.EnumerateObject())
                    switch (kv.Value.ValueKind)
                    {
                        case System.Text.Json.JsonValueKind.String: anim.SetMeta(kv.Name, kv.Value.GetString()!); break;
                        case System.Text.Json.JsonValueKind.True: anim.SetMeta(kv.Name, true); break;
                        case System.Text.Json.JsonValueKind.False: anim.SetMeta(kv.Name, false); break;
                        case System.Text.Json.JsonValueKind.Number: anim.SetMeta(kv.Name, kv.Value.GetDouble()); break;
                        case System.Text.Json.JsonValueKind.Array when kv.Value.EnumerateArray().All(e => e.ValueKind == System.Text.Json.JsonValueKind.Number):
                            anim.SetMeta(kv.Name, kv.Value.EnumerateArray().Select(e => e.GetDouble()).ToArray()); break;
                    }
            outLib.AddAnimation(name, anim);
            if (HerEvents.FromClip(r) is { } beats) events[name] = beats;
            var missing = baseTurn.Keys.Where(k => !r.GetProperty("rot").TryGetProperty(k, out _)).ToArray();
            GD.Print($"p4-pack: {name}: {frames} frames, {bones} bones ({based} under the blend base, pre-turned), {(loop ? "loop" : "once")}, {anim.Length:F3} s" +
                     (missing.Length > 0 ? $"; NOT KEYED under the blend base (they land on t): {string.Join(" ", missing)}" : ""));
        }
        var unknown = reviewNames.Where(n => !builtNames.Contains(n)).OrderBy(n => n).ToArray();
        if (unknown.Length > 0) GD.Print($"p4-pack: --review names with no built clip: {string.Join(", ", unknown)}");
        var err = ResourceSaver.Save(outLib, P1Body.Dir + "p4_clips.res", ResourceSaver.SaverFlags.Compress);
        GD.Print($"p4-pack: wrote p4_clips.res ({files.Length - skipped} packed, {skipped} skipped, track path {skelPath}): {err}");
        // The clips' beats as data (a clip's top-level "beats", clip seconds -> frames at 60 fps). The pack owns the
        // entries of the clips it packs (each replaced, or dropped when the clip has no beats now); every other clip's
        // entry is kept as it stands (M3's measured contacts of the bridge swings: tools/anim/contact_measure.py).
        var evPath = ProjectSettings.GlobalizePath("res://data/anim/her_events.json");
        DirAccess.MakeDirRecursiveAbsolute(evPath.GetBaseDir());
        var kept = HerEvents.Load(FileAccess.FileExists(evPath) ? FileAccess.GetFileAsString(evPath) : "");
        var all = HerEvents.Merge(kept, events, outLib.GetAnimationList().Select(n => n.ToString()));
        using (var ef = FileAccess.Open(evPath, FileAccess.ModeFlags.Write)) ef.StoreString(HerEvents.Serialize(all));
        GD.Print($"p4-pack: wrote data/anim/her_events.json ({events.Count} packed clips with beats, {all.Count - events.Count} other clips kept)");
        GetTree().Quit();
    }
}
