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
            edges.GetParent().AddChild(goalMarks);
        }
        goalMarks.Show(list);
    }
}
