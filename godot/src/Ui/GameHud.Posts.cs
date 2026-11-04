using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

public partial class GameHud
{
    LampPointers? postPointers;

    /// <summary>The pointers to the Ford-Warden's lit lamp posts that are off screen this frame (the node is made on first use).</summary>
    public void Posts(List<LampPointers.Pointer> list)
    {
        if (postPointers == null)
        {
            if (list.Count == 0) return;
            postPointers = new LampPointers();
            Style.Fill(postPointers);
            var at = combat.GetParent();
            at.AddChild(postPointers);
            at.MoveChild(postPointers, combat.GetIndex() + 1);
        }
        postPointers.Show(list);
    }
}
