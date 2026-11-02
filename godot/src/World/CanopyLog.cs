using System.Collections.Generic;
using System.Linq;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>--canopy-log (a developer's switch, off by default): the canopy fade (kit.gdshader OWN_FOLIAGE, vertex())
/// mirrored on the CPU for each of our trees in the zone, so the environment lead can be told which trees block the
/// fight lanes: at the zone's end each tree that was faded past half, its place (world x, z), its species, the seconds
/// it was, and how near her path came to its trunk. (The crown's stretch and leader hashes are the shader's, in
/// single floats, handed to the shader in each copy's custom data a (Hashes), so a crown here is the drawn one.)</summary>
public static class CanopyLog
{
    public static readonly bool On = SurvivorUnchained.Args.Has("canopy-log");

    internal sealed class Tree
    {
        public Vector3 At, Up, Lean;
        public string Species = "";
        public float Lo, Top, R, Secs, F, Taper = 1, Near = float.MaxValue;
        /// <summary>(CanopyFader) the copy's top (its lod0 mesh's, stretched as drawn), local m; its draws; the packed
        /// piece's custom r; the eased fade (0..1, linear in time) and the value last written (eased); the targets.</summary>
        public float Tip, CustR, CustA, Ease, Shown;
        public bool Want, ForHer, ForLens;
        public int Stamp;
        public double HerAt = -99;
        public (MultiMesh Mm, int I)[] Inst = [];
    }

    static float Hash(Vector3 ip, float a, float b, float k)
    {
        float x = Mathf.Sin(ip.X * a + ip.Z * b) * k;
        return x - Mathf.Floor(x);
    }

    /// <summary>(Env 23 r2) A copy's stretch, leader, lean and lean-direction hashes (0..1, in 64 steps) and their packing
    /// for its custom data's a (1 + four 6-bit values; kit.gdshader decodes it): the shader's sin hashes of a large angle differ
    /// on the GPU from the CPU's, so the CPU hands it the values instead.</summary>
    public static (float St, float Hl, float La, float Ld, float Packed) Hashes(Vector3 ip)
    {
        int q1 = Mathf.RoundToInt(Hash(ip, 17.17f, 63.41f, 19417.83f) * 63), q2 = Mathf.RoundToInt(Hash(ip, 51.3f, 27.9f, 37281.41f) * 63),
            q3 = Mathf.RoundToInt(Hash(ip, 39.35f, 11.13f, 24634.63f) * 63), q4 = Mathf.RoundToInt(Hash(ip, 7.77f, 93.51f, 51721.17f) * 63);
        return (q1 / 63f, q2 / 63f, q3 / 63f, q4 / 63f, 1 + q1 + 64 * q2 + 4096 * q3 + 262144 * q4);
    }

    static float P(FloraSpecies.Species sp, string k, float d) =>
        sp.Shader.TryGetValue(k, out var v) && v.ValueKind == System.Text.Json.JsonValueKind.Number ? v.GetSingle() : d;

    /// <summary>The trees of one species drawn under root (Dressing.OwnFlora's copies, refs their draws, tipY the lod0 mesh's
    /// top): kept by the zone's CanopyFader (always), and tallied by --canopy-log's CanopyLogger.</summary>
    public static void Register(Node3D root, FloraSpecies.Species sp, List<Transform3D> at, List<(MultiMesh Mm, int I)>[] refs, float tipY)
    {
        float hi = P(sp, "crown_hi", 0);
        if (hi <= 0) return;
        if (root.GetNodeOrNull<CanopyFader>("CanopyFader") is not { } fader) root.AddChild(fader = new CanopyFader { Name = "CanopyFader" });
        if (On && root.GetNodeOrNull<CanopyLogger>("CanopyLog") is not { } log) root.AddChild(log = new CanopyLogger { Name = "CanopyLog", Fader = fader });
        float lo = P(sp, "crown_lo", 0), r = P(sp, "crown_r", 2), slo = P(sp, "stretch_lo", 1), shi = P(sp, "stretch_hi", 1),
            lf = P(sp, "leader_from", 6), tp = P(sp, "crown_taper", 1), llo = P(sp, "leader_lo", 1), lhi = P(sp, "leader_hi", 1),
            lean = P(sp, "lean", 0), leanH = P(sp, "lean_h", 8);
        for (int k = 0; k < at.Count; k++)
        {
            var t = at[k];
            var ip = t.Origin;
            var hs = Hashes(ip);
            float st = Mathf.Lerp(slo, shi, hs.St);
            float hl = Mathf.Lerp(llo, lhi, hs.Hl);
            float top = (hi > lf ? lf + (hi - lf) * hl : hi) * st;
            float tip = (tipY > lf ? lf + (tipY - lf) * hl : tipY) * st;
            var cd = refs[k].Count > 0 ? refs[k][0].Mm.GetInstanceCustomData(refs[k][0].I) : new Color(0, 0, 0, 0);
            // (the shader's lean: VERTEX.xz += (cos ld, sin ld) tan(la) / (2 lean_h) h^2, in the copy's own space)
            var lw = Vector3.Zero;
            if (lean > 0)
            {
                float la = Mathf.DegToRad(lean) * (hs.La * 2 - 1), ld = hs.Ld * Mathf.Tau;
                lw = t.Basis * (new Vector3(Mathf.Cos(ld), 0, Mathf.Sin(ld)) * (Mathf.Tan(la) / (2 * leanH)));
            }
            fader.Add(new Tree { At = ip, Up = t.Basis.Y, Lean = lw, Species = sp.Name, Lo = lo * st, Top = top, R = r, Taper = tp, Tip = Mathf.Max(tip, top), CustR = cd.R, CustA = cd.A, Inst = refs[k].ToArray() });
        }
    }
}
