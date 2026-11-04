using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

public partial class GameHud
{
    FoeMarks? foeMarks;
    BossPointer? bossPointer;

    /// <summary>Foe health bars and the priority ring this frame (H1: item 2 and 4). The node is made on first use, in the fight's layer.</summary>
    public void Foes(Battle? b, Camera3D cam, Func<Enemy, (double X, double Z)> at, bool bars = true)
    {
        if (b == null || !b.Combat) { foeMarks?.Show0(); bossPointer?.Hide0(); return; }
        if (foeMarks == null)
        {
            foeMarks = new FoeMarks();
            Style.Fill(foeMarks);
            combat.AddChild(foeMarks);
            combat.MoveChild(foeMarks, 0);
        }
        foeMarks.Show(b, cam, at, bars);
        if (bossPointer == null)
        {
            bossPointer = new BossPointer();
            Style.Fill(bossPointer);
            combat.AddChild(bossPointer);
        }
        bossPointer.Show(b, cam, at);
    }
}
