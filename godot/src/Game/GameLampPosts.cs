using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Ui;

namespace SurvivorUnchained.Play;

/* The Ford-Warden's lamp posts on this side of the screen: the pointers to the lit ones that are off screen
 * (drawn by Ui/LampPointers.cs, fed from the same camera projection as the goal arrows), and the --lampcheck
 * measurement. */
public partial class Game
{
    double lampCheckAt = -1;

    /// <summary>A lit post whose lamp is more than 70 px outside the view (or behind the camera) gets a pointer on the
    /// edge of a rectangle 90 px in from the view's sides, kept above the hotbar and below the corner's words (as the goal arrows are).</summary>
    List<LampPointers.Pointer> PostPointers()
    {
        var o = new List<LampPointers.Pointer>();
        if (scene == null || zone is not Zones.Prologue pro) return o;
        var size = GetViewport().GetVisibleRect().Size;
        var seen = new Rect2(Vector2.Zero, size).Grow(70);
        var box = new Rect2(90, 160, size.X - 180, size.Y - 160 - 210);
        var mid = size / 2;
        int i = 0;
        foreach (var p in pro.LampPosts)
        {
            int id = i++;
            if (!p.Lit) continue;
            var w = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
            bool behind = camera.IsPositionBehind(w);
            var sp = camera.UnprojectPosition(w);
            if (!behind && seen.HasPoint(sp)) continue;
            var d = sp - mid;
            if (behind) d = -d;
            if (d.LengthSquared() < 1) d = Vector2.Down;
            float tx = d.X != 0 ? ((d.X > 0 ? box.End.X : box.Position.X) - mid.X) / d.X : float.MaxValue;
            float ty = d.Y != 0 ? ((d.Y > 0 ? box.End.Y : box.Position.Y) - mid.Y) / d.Y : float.MaxValue;
            o.Add(new LampPointers.Pointer(id, mid + d * Mathf.Min(tx, ty), d.Normalized()));
        }
        return o;
    }

    /// <summary>--lampcheck: every 0.5 s of the Warden fight, how many lit posts (and posts, and she) are in the frame.</summary>
    void LampCheck(double battleTime)
    {
        if (!Args.Has("lampcheck") || zone is not Zones.Prologue pro) return;
        var posts = pro.LampPosts.ToList();
        if (posts.Count == 0) { lampCheckAt = -1; return; }
        if (lampCheckAt >= 0 && battleTime < lampCheckAt + 0.5) return;
        lampCheckAt = battleTime;
        var size = GetViewport().GetVisibleRect().Size;
        var view = new Rect2(Vector2.Zero, size).Grow(-40);
        bool In(Vector3 w) => !camera.IsPositionBehind(w) && view.HasPoint(camera.UnprojectPosition(w));
        bool InPost((double X, double Y, double Z, bool Lit) p) => In(new Vector3((float)p.X, (float)p.Y, (float)p.Z));
        int lit = posts.Count(p => p.Lit), inframe = posts.Count(p => p.Lit && InPost(p)), all = posts.Count(InPost);
        int her = In(scene!.HerDrawn + new Vector3(0, 1.1f, 0)) ? 1 : 0;
        GD.Print($"LAMPCHECK t={battleTime:0.0} lit={lit} inframe={inframe} all={all} her={her}");
    }
}
