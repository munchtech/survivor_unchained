using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Ui;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* The goals (data/content/goals.json, logic/World/Goals.cs) on this side of the screen: the
 * tracker's lines, the minimap and map pins, and the waypoint and edge arrow on the ground. */
public partial class Game
{
    string goalSet = "";

    /// <summary>The goals that stand now, in this zone (none while the world is not up).</summary>
    public List<ActiveGoal> GoalPins()
    {
        if (zone == null || inTransit || Battle == null || Journey == null) return new();
        return Goals.Active(Goals.All, Journey.Ctx, zone.Id, zone.Interactables);
    }

    /// <summary>The tracker with the goals' lines in it.</summary>
    List<Tracked> WithGoals(List<Tracked> list)
    {
        var pins = GoalPins();
        goalSet = GoalKey(pins);
        return pins.Count == 0 ? list : Goals.Merge(list, pins, k => zone?.Word(k));
    }

    static string GoalKey(List<ActiveGoal> pins) => string.Join(",", pins.Select(p => p.Def.Id + (p.Line ? "+" : "-")));

    /// <summary>Corner-map marks for the goals.</summary>
    List<MiniMark> GoalMiniMarks() => GoalPins().Select(p => new MiniMark(p.X, p.Z, MarkKind.Quest, p.Def.Label)).ToList();

    /// <summary>The waypoints and edge arrows for this frame; the tracker is redone when a goal comes or goes.</summary>
    List<GoalMark> GoalScreen()
    {
        var o = new List<GoalMark>();
        if (scene == null || Battle is not { } b) return o;
        var pins = GoalPins();
        if (GoalKey(pins) != goalSet) RefreshObjectives();
        var size = GetViewport().GetVisibleRect().Size;
        var view = new Rect2(Vector2.Zero, size).Grow(-30);
        foreach (var p in pins)
        {
            double d = Math.Sqrt((p.X - b.Player.X) * (p.X - b.Player.X) + (p.Z - b.Player.Z) * (p.Z - b.Player.Z));
            var w = new Vector3((float)p.X, (float)scene.HeightAt(p.X, p.Z) + 1.8f, (float)p.Z);
            var sp = camera.UnprojectPosition(w);
            bool behind = camera.IsPositionBehind(w);
            bool on = !behind && view.HasPoint(sp);
            if (on ? d < p.Def.Near : !p.Def.Edge) continue;
            if (behind) sp = view.GetCenter() - (sp - view.GetCenter());
            Color c;
            try { c = new Color(p.Def.Color); } catch { c = Colors.White; }
            o.Add(new GoalMark(sp, on, p.Def.Glyph, c, p.Def.Label, (float)d));
        }
        return o;
    }
}
