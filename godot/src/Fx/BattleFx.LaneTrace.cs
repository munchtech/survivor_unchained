using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/* --lane-trace (dev): one line the first frame a telegraph lane is drawn, then every 30 frames while its mark lives, so a
 * capture can name which maker's lane it is and the rank and energy it was drawn at (F1: crowd lanes quieter than a
 * boss's). The sim's Id for a kit blow is a mark id, not the maker's, so the maker is the nearest living foe to ByX/ByZ. */
public partial class BattleFx
{
    static readonly bool LaneTrace = Args.Has("lane-trace");
    readonly Dictionary<int, (Mark M, string Head, long First)> laneTrace = new();

    static Enemy? MakerOf(Ev.Telegraph e, Battle b)
    {
        if (e.ByX is not double bx || e.ByZ is not double bz) return null;
        Enemy? best = null; double bd = 0.5 * 0.5;
        foreach (var x in b.Enemies.Living())
        {
            double dx = x.X - bx, dz = x.Z - bz, d = dx * dx + dz * dz;
            if (d <= bd) { bd = d; best = x; }
        }
        return best;
    }

    /// <summary>Rank used: boss (the red line), crowd (the dim crimson), none (a plain wall or ground lane).</summary>
    void LaneTraceStart(Ev.Telegraph e, Battle b, Mark lm, TelegraphRead.TeleLook look, bool fodderCharge)
    {
        if (!LaneTrace) return;
        var mk = MakerOf(e, b);
        string rank = look == TelegraphRead.TeleLook.Danger ? "boss" : look == TelegraphRead.TeleLook.Amber ? "crowd" : "none";
        double dx = (e.X1 ?? e.X) - e.X, dz = (e.Z1 ?? e.Z) - e.Z;
        string head = $"tid={e.Id} maker={mk?.Def.Id ?? "?"} elite={(mk?.Elite == true ? 1 : 0)} boss={(e.Boss || mk?.Boss == true ? 1 : 0)} tell={e.Tell ?? "-"} shape={e.Shape} kind={e.Kind} look={look} fodderCharge={(fodderCharge ? 1 : 0)} rank={rank} " +
            $"len={Math.Sqrt(dx * dx + dz * dz):F1} wid={e.Width ?? 1:F1}";
        long f = (long)Engine.GetFramesDrawn();
        laneTrace[e.Id] = (lm, head, f);
        LaneTraceLine(lm, head);
    }

    static void LaneTraceLine(Mark m, string head) =>
        GD.Print($"[lane-trace] f={Engine.GetFramesDrawn()} {head} energy={(m.Styled ? m.Energy : m.Decal.EmissionEnergy):F2} alpha={m.Decal.Modulate.A:F2} styled={(m.Danger ? "danger" : m.Amber ? "amber" : "flat")}");

    void LaneTraceTick()
    {
        if (laneTrace.Count == 0) return;
        long f = (long)Engine.GetFramesDrawn();
        List<int>? gone = null;
        foreach (var (id, t) in laneTrace)
        {
            if (!t.M.Active || t.M.Key != id) { (gone ??= new()).Add(id); continue; }
            if (f > t.First && (f - t.First) % 30 == 0) LaneTraceLine(t.M, t.Head);
        }
        if (gone != null) foreach (int id in gone) laneTrace.Remove(id);
    }
}
