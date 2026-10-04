using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// Small motions laid over whatever a body is doing: a nod, a long exhale,
/// a shiver (tools/anim, "layer": "gesture" in the clip's meta). Each is
/// keyed from a still pose, and only its change from its own first frame is
/// added, bone by bone in each bone's own space, so one nod serves her
/// standing, sitting on the log or kneeling on her heels. A gesture that
/// holds (an exhale's settled shoulders) stays at its last frame until let
/// go, and then eases out.
/// </summary>
public partial class Gestures : SkeletonModifier3D
{
    sealed class Playing
    {
        public required Animation Clip;
        public required int[] Bones, Tracks;
        public required Quaternion[] First;
        public double T, Speed = 1, Fade = 1;
        public bool Hold, Released;
    }

    readonly List<Playing> playing = new();
    Skeleton3D? found;

    public Gestures() { Name = "Gestures"; }

    /// <summary>Lays a gesture over the body. Holding, it keeps its last
    /// frame until Release.</summary>
    public void Play(Animation clip, double speed = 1, bool hold = false)
    {
        var sk = GetSkeleton();
        if (sk == null) return;
        var bones = new List<int>();
        var tracks = new List<int>();
        var first = new List<Quaternion>();
        for (int t = 0; t < clip.GetTrackCount(); t++)
        {
            if (clip.TrackGetType(t) != Animation.TrackType.Rotation3D) continue;
            var path = clip.TrackGetPath(t);
            int b = path.GetSubNameCount() > 0 ? sk.FindBone(path.GetSubName(0)) : -1;
            if (b < 0) continue;
            // Only the bones the gesture moves: the rest of its still pose adds nothing.
            var q0 = clip.RotationTrackInterpolate(t, 0);
            bool moves = false;
            for (double s = 0; s <= clip.Length && !moves; s += 1 / 15.0)
                moves = q0.AngleTo(clip.RotationTrackInterpolate(t, s)) > 0.002f;
            if (!moves) continue;
            bones.Add(b);
            tracks.Add(t);
            first.Add(q0);
        }
        // A gesture already playing gives way to the new one.
        foreach (var p in playing) p.Released = true;
        playing.Add(new Playing { Clip = clip, Bones = bones.ToArray(), Tracks = tracks.ToArray(), First = first.ToArray(), Speed = speed, Hold = hold });
    }

    /// <summary>Lets held gestures go (they ease back out).</summary>
    public void Release()
    {
        foreach (var p in playing) p.Released = true;
    }

    public override void _ProcessModificationWithDelta(double delta)
    {
        var sk = GetSkeleton();
        if (sk == null || playing.Count == 0) return;
        for (int i = playing.Count - 1; i >= 0; i--)
        {
            var p = playing[i];
            p.T += delta * p.Speed;
            double end = p.Clip.Length;
            // Done, unless it holds; let go, it eases out over a fifth of a second.
            if (p.Released || (!p.Hold && p.T >= end)) p.Fade -= delta / 0.2;
            if (p.Fade <= 0) { playing.RemoveAt(i); continue; }
            double t = Mathf.Min(p.T, end);
            float w = (float)Mathf.Clamp(p.Fade, 0, 1);
            for (int k = 0; k < p.Bones.Length; k++)
            {
                var d = p.First[k].Inverse() * p.Clip.RotationTrackInterpolate(p.Tracks[k], t);
                if (w < 1) d = Quaternion.Identity.Slerp(d, w);
                int b = p.Bones[k];
                sk.SetBonePoseRotation(b, (sk.GetBonePoseRotation(b) * d).Normalized());
            }
        }
    }
}
