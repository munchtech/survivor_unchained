using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>--canopy-log (a developer's switch, off by default): the canopy fade (kit.gdshader OWN_FOLIAGE, vertex())
/// mirrored on the CPU for each of our trees in the zone, so the environment lead can be told which trees block the
/// fight lanes: at the zone's end each tree that was faded past half, its place (world x, z), its species, the seconds
/// it was, and how near her path came to its trunk. (The crown's stretch and leader hashes are the shader's, in
/// single floats; a GPU's sin may differ in the last digits, so a crown's top here is within a few cm of the drawn.)</summary>
public static class CanopyLog
{
    public static readonly bool On = SurvivorUnchained.Args.Has("canopy-log");

    internal sealed class Tree
    {
        public Vector3 At, Up;
        public string Species = "";
        public float Lo, Top, R, Secs, F, Near = float.MaxValue;
    }

    static float Hash(Vector3 ip, float a, float b, float k)
    {
        float x = Mathf.Sin(ip.X * a + ip.Z * b) * k;
        return x - Mathf.Floor(x);
    }

    static float P(FloraSpecies.Species sp, string k, float d) =>
        sp.Shader.TryGetValue(k, out var v) && v.ValueKind == System.Text.Json.JsonValueKind.Number ? v.GetSingle() : d;

    /// <summary>The trees of one species drawn under root (Dressing.OwnFlora's copies).</summary>
    public static void Register(Node3D root, FloraSpecies.Species sp, List<Transform3D> at)
    {
        float hi = P(sp, "crown_hi", 0);
        if (!On || hi <= 0) return;
        if (root.GetNodeOrNull<CanopyLogger>("CanopyLog") is not { } log) root.AddChild(log = new CanopyLogger { Name = "CanopyLog" });
        float lo = P(sp, "crown_lo", 0), r = P(sp, "crown_r", 2), slo = P(sp, "stretch_lo", 1), shi = P(sp, "stretch_hi", 1),
            lf = P(sp, "leader_from", 6), llo = P(sp, "leader_lo", 1), lhi = P(sp, "leader_hi", 1);
        foreach (var t in at)
        {
            var ip = t.Origin;
            float st = Mathf.Lerp(slo, shi, Hash(ip, 17.17f, 63.41f, 19417.83f));
            float hl = Mathf.Lerp(llo, lhi, Hash(ip, 51.3f, 27.9f, 37281.41f));
            float top = (hi > lf ? lf + (hi - lf) * hl : hi) * st;
            log.Trees.Add(new Tree { At = ip, Up = t.Basis.Y, Species = sp.Name, Lo = lo * st, Top = top, R = r });
        }
    }
}
