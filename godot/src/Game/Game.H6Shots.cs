using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play;

/// <summary>--on h6: frames of H6's new mechanics as they happen (a closing's wall standing, the knockdown, a pull's slam,
/// the Ironback, a pack feeding, the director's barks and callouts, a stuck foe's recall), each tagged with the fight's
/// second. A recall is found by its jump (no event carries it): printed with whether each end was on screen.</summary>
public partial class Game
{
    readonly Dictionary<int, (double Seed, double X, double Z)> h6Was = new();
    string? h6Callout;

    string H6Tag(string what) => $"{what}_{Battle?.Time ?? 0:0}s";

    void H6Shot(CombatEvent e)
    {
        switch (e)
        {
            case Ev.Telegraph t when t.Tell == "closing" && t.Phase == TellPhase.Land:
                foreach (var s in (double[])[0.7, 1.6, 2.8, 3.6]) Shots.Want(H6Tag("wall"), s);
                break;
            case Ev.ClosingWall w:
                GD.Print($"h6 wall {(w.Up ? "up" : "down")} id {w.Id} at {Battle?.Time:0.00}");
                if (!w.Up) Shots.Want(H6Tag("walldown"), 0.1);
                break;
            case Ev.Knockdown k:
                GD.Print($"h6 knockdown {k.Seconds:0.00}s at {Battle?.Time:0.00}");
                foreach (var s in (double[])[0.08, 0.3, k.Seconds * 0.85, k.Seconds + 0.3]) Shots.Want(H6Tag("knock"), s);
                break;
            case Ev.Telegraph t when t.Tell == "pull" && t.Phase == TellPhase.Land:
                foreach (var s in (double[])[0.2, 0.5]) Shots.Want(H6Tag("slam"), s);
                break;
            case Ev.Spawn sp when sp.Def == "boar_ironback":
                GD.Print($"h6 ironback at {Battle?.Time:0.00}");
                foreach (var s in (double[])[0.4, 2.0]) Shots.Want(H6Tag("iron"), s);
                break;
            case Ev.Telegraph t when t.Tell == "ring" && t.Phase == TellPhase.Warn && Battle != null
                && System.Linq.Enumerable.Any(Battle.Enemies.Living(), x => x.Def.Id == "boar_ironback" && System.Math.Abs(x.X - t.X) < 0.5 && System.Math.Abs(x.Z - t.Z) < 0.5):
                foreach (var s in (double[])[t.Duration * 0.5, t.Duration * 0.9]) Shots.Want(H6Tag("ironslam"), s);
                break;
            case Ev.Sound snd when snd.Id == "pack.feed":
                GD.Print($"h6 feed at {Battle?.Time:0.00}");
                foreach (var s in (double[])[0.3, 1.0, 1.8]) Shots.Want(H6Tag("feed"), s);
                break;
            case Ev.Bark b:
                GD.Print($"h6 bark '{b.Text}' at {Battle?.Time:0.00}");
                foreach (var s in (double[])[0.3, 1.2]) Shots.Want(H6Tag("bark"), s);
                break;
        }
    }

    /// <summary>Each frame: a callout's first frames, and a foe's jump of 6 m+ in a frame (the director's recall).</summary>
    void H6Frame(Battle b)
    {
        if (Teaching is { } c && c.Id != h6Callout) { h6Callout = c.Id; Shots.Want(H6Tag("callout_" + c.Id), 0.4); }
        else if (Teaching == null) h6Callout = null;
        var rect = camera.GetViewport().GetVisibleRect();
        bool On(double x, double z)
        {
            var w = new Vector3((float)x, (float)scene.HeightAt(x, z) + 1, (float)z);
            return !camera.IsPositionBehind(w) && rect.HasPoint(camera.UnprojectPosition(w));
        }
        foreach (var e in b.Enemies.Living())
        {
            if (h6Was.TryGetValue(e.Id, out var was) && was.Seed == e.Seed)
            {
                double dx = e.X - was.X, dz = e.Z - was.Z;
                if (dx * dx + dz * dz > 36)
                {
                    GD.Print($"h6 recall {e.Def.Id} #{e.Id} at {b.Time:0.00}: from ({was.X:0.0}, {was.Z:0.0}) on screen {On(was.X, was.Z)} to ({e.X:0.0}, {e.Z:0.0}) on screen {On(e.X, e.Z)}");
                    Shots.Want(H6Tag("recall"), 0.05);
                }
            }
            h6Was[e.Id] = (e.Seed, e.X, e.Z);
        }
    }
}
