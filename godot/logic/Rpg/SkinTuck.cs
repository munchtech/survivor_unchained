using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Rpg;

/// <summary>Her skin's tuck under a look, merged in millimetres (tuck depth as data: tools/armor/gear_tuck.py). A piece's
/// record is marks 0..1 of its ROW's full scale (ArmorPiece.TuckDepthMm, 10 unless its gear_index row says
/// "tuck_depth_mm"); a point's depth is its mark times that. A look's map (heroine_skin.gdshader tuck_map) holds, at each
/// of her points, the deepest of the worn pieces' depths, as marks of the look's deepest scale, which goes to the shader's
/// `tuck`. Every row at 10 mm: the marks and the uniform are today's, bit for bit.</summary>
public static class SkinTuck
{
    /// <summary>A record's full scale unless its row says otherwise, mm (the shader's `tuck` default).</summary>
    public const float BaseMm = 10f;
    /// <summary>What a full tuck is written as (gear_tuck.py FULL 0.98, in eight bits).</summary>
    public const float FullMark = 250f / 255f;

    /// <summary>A mark as her vertex colours hold a channel's: eight bits.</summary>
    public static float Quantise(float t) => MathF.Round(Math.Clamp(t, 0f, 1f) * 255f) / 255f;

    /// <summary>A quantised mark's depth, mm, of a row `depthMm` deep (the shader: all of it past GarmentTuck.Full).</summary>
    public static float Mm(float q, float depthMm) => depthMm * (q > GarmentTuck.Full ? 1f : q);

    /// <summary>The look's scale, mm: its deepest row's (rows with a tuck record; `under`: garment-tuck values, 10 mm
    /// marks, are in it). No row: 10.</summary>
    public static float LookMm(IEnumerable<float> rowDepths, bool under = false)
    {
        float s = under ? BaseMm : 0f;
        foreach (float d in rowDepths) s = MathF.Max(s, d);
        return s > 0 ? s : BaseMm;
    }

    /// <summary>The shader's `tuck`, m, for a look's scale (10 mm: its default, to the bit).</summary>
    public static float Uniform(float lookMm) => lookMm == BaseMm ? 0.010f : lookMm / 1000f;

    struct Pt
    {
        public float Mm, Top;
        public bool Gone;
    }

    /// <summary>The look's marks at her points (key: her bind position). `rows`: each worn piece's full scale (mm) and
    /// records (raw marks of that scale); the garment tuck's `under` values go in as a row 10 deep. Each mark is
    /// quantised, read as the shader reads it (full past 0.973, not drawn from 0.995) into millimetres, and the deepest
    /// at a point wins; a point any row marks not drawn is not drawn. Written as marks of `lookMm`:
    /// a mark of a row at the look's scale as it is (so a look all at one scale is the largest mark, as before);
    /// a shallower row's depth as depth / lookMm (FullMark where that would read as full);
    /// a point not drawn whose depth is under the look's scale as 2 - depth / lookMm (over 1: the shader discards it and
    /// moves it by its own depth, not the look's, so the triangles it shares with drawn skin stay where they were).</summary>
    public static Dictionary<long, float> Merge(IEnumerable<(float DepthMm, IEnumerable<(long Key, float T)> Records)> rows, float lookMm)
    {
        var at = new Dictionary<long, Pt>();
        foreach (var (depth, recs) in rows)
        {
            bool top = depth == lookMm;
            foreach (var (k, t) in recs)
            {
                float q = Quantise(t);
                at.TryGetValue(k, out var p);
                p.Mm = MathF.Max(p.Mm, Mm(q, depth));
                p.Gone |= q >= GarmentTuck.Gone;
                if (top) p.Top = MathF.Max(p.Top, q);
                at[k] = p;
            }
        }
        var marks = new Dictionary<long, float>(at.Count);
        foreach (var (k, p) in at) marks[k] = Mark(p, lookMm);
        return marks;
    }

    static float Mark(Pt p, float lookMm)
    {
        if (!p.Gone)
        {
            if (Mm(p.Top, lookMm) >= p.Mm) return p.Top;
            float f = p.Mm / lookMm;
            return f > GarmentTuck.Full ? FullMark : f;
        }
        if (p.Top >= GarmentTuck.Gone) return p.Top;
        float g = p.Mm / lookMm;
        return g > GarmentTuck.Full ? 1f : 2f - g;
    }

    /// <summary>What the shader does with a written mark: its depth, mm, and whether it is not drawn (the tests' and
    /// gear_wear.py's reading of a map).</summary>
    public static (float Mm, bool Gone) Read(float mark, float lookMm) =>
        (lookMm * (mark > GarmentTuck.Full ? MathF.Min(1f, 2f - mark) : mark), mark >= GarmentTuck.Gone);

    /// <summary>A piece's tuck mark as the garment tuck's footprint reads it: a mark of 10 mm (GarmentTuck.Amount: the lay
    /// amount follows the depth in millimetres, not the row's scale). A row 10 deep: the mark as it is; a mark not drawn
    /// stays so (GarmentTuck.Gone removes what is under it at any scale).</summary>
    public static float Foot(float t, float depthMm)
    {
        if (depthMm == BaseMm || t >= GarmentTuck.Gone) return t;
        return MathF.Min(Mm(Math.Clamp(t, 0f, 1f), depthMm) / BaseMm, 0.98f);
    }
}
