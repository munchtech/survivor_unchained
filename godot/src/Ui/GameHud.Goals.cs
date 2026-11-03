using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

public partial class GameHud
{
    GoalMarks? goalMarks;

    /// <summary>The goals' waypoints and edge arrows this frame (the node is made on first use).</summary>
    public void Goals(List<GoalMark> list)
    {
        if (goalMarks == null)
        {
            if (list.Count == 0) return;
            goalMarks = new GoalMarks();
            Style.Fill(goalMarks);
            // Beside the fight's layer, not in it: the fight's layer is hidden in town, and the town has goals too.
            var at = combat.GetParent();
            at.AddChild(goalMarks);
            at.MoveChild(goalMarks, combat.GetIndex() + 1);
        }
        // The arrows keep off the corner's words: the place, the tracker and the map in the upper right.
        var words = objectives.GetGlobalRect();
        goalMarks.Avoid = list.Count == 0 ? null : new Rect2(words.Position.X - 24, 0, goalMarks.GetViewportRect().Size.X - words.Position.X + 24, words.End.Y + 16);
        goalMarks.Show(list);
    }
}
