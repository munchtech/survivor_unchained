using System;
using System.Linq;
using System.Text.Json;
using Godot;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Tools;

/// <summary>
/// P4 clips packed for the game (tools/anim/p4_pack.sh runs tools_scenes/p4_pack.gd, which runs this): every
/// art/people/body_p1/p4/*.json (tools/anim/p4.py build: local rotations of B's keyed bones as Godot quaternions
/// [x, y, z, w], root and pelvis local positions, frames at fps, a loop's last frame its first) into
/// art/people/body_p1/p4_clips.res, an AnimationLibrary: a rotation track per keyed bone, position tracks for root and
/// pelvis, the loop mode from the clip, length (frames-1)/fps, step 1/fps. The skeleton track path is the bridge clips'
/// own (read from her_clips.res, as P1BakeRun writes it), so P4 clips drop into the same tree. P1Body.HerClips lays
/// them over the bridge clips.
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
        var outLib = new AnimationLibrary();
        var files = DirAccess.GetFilesAt(dir).Where(f => f.EndsWith(".json")).OrderBy(f => f).ToArray();
        foreach (var file in files)
        {
            using var d = JsonDocument.Parse(FileAccess.GetFileAsString(dir + file));
            var r = d.RootElement;
            string name = r.GetProperty("name").GetString()!;
            double fps = r.GetProperty("fps").GetDouble();
            int frames = r.GetProperty("frames").GetInt32();
            bool loop = r.GetProperty("loop").GetBoolean();
            var anim = new Animation { Length = (float)((frames - 1) / fps), LoopMode = loop ? Animation.LoopModeEnum.Linear : Animation.LoopModeEnum.None, Step = (float)(1 / fps) };
            int bones = 0;
            foreach (var b in r.GetProperty("rot").EnumerateObject())
            {
                int tr = anim.AddTrack(Animation.TrackType.Rotation3D);
                anim.TrackSetPath(tr, $"{skelPath}:{b.Name}");
                int f = 0;
                foreach (var q in b.Value.EnumerateArray())
                {
                    var v = q.EnumerateArray().Select(x => (float)x.GetDouble()).ToArray();
                    anim.RotationTrackInsertKey(tr, f++ / fps, new Quaternion(v[0], v[1], v[2], v[3]).Normalized());
                }
                bones++;
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
            outLib.AddAnimation(name, anim);
            GD.Print($"p4-pack: {name}: {frames} frames, {bones} bones, {(loop ? "loop" : "once")}, {anim.Length:F3} s");
        }
        var err = ResourceSaver.Save(outLib, P1Body.Dir + "p4_clips.res", ResourceSaver.SaverFlags.Compress);
        GD.Print($"p4-pack: wrote p4_clips.res ({files.Length} clips, track path {skelPath}): {err}");
        GetTree().Quit();
    }
}
