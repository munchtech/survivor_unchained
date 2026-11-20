using System;
using System.Text.Json;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Look;

/// <summary>(lane J art-color, 19 Nov; the owner's day and night reference, owner_ref_night_day_colors_19nov) The world's
/// colour per time of day, as data: rigs.json "palettes", named by a rig's "palette", carried on the air
/// (AtmospherePreset.Palette), blended by the clock (Atmospheres.Blend) and set as shader globals (Atmosphere.SetPalette;
/// shaders/palette.gdshaderinc). Each class is a ramp of three colours (dark, mid, lit) laid over the albedo's own value
/// (the square root of its linear luminance, from lo to hi), so a surface keeps its painted variation and takes the time's hue: autumn by day,
/// violet and teal by night. Only the world's classes take it: her skin, hair, eyes and gear never do (lane E's skin band).
/// Flattened per class: [dark r g b (linear), amount, mid r g b, lo, lit r g b, hi].</summary>
/// <summary>(lane J, night glow) A palette's light sources: cap, stem and light colours (sRGB hex), the light's energy and range (m),
/// the share of tree feet that get a cluster, the most clusters in a zone, the mushrooms a cluster [min, max], the cap radius [min, max] (m).
/// (lead 2: the woods alone put no cluster in the opening frame (one a 97 m2, most under a crown): the clusters now also line the
/// zone's walked paths, "paths" by name, one every "step" m, "side" [min, max] m off the centre line, a light on "path_light" of
/// them and on "wood_light" of the woods' ones; "alt" a second source (cap, light colours) on "alt_share" of the clusters.)</summary>
public sealed record PaletteGlow(string Cap, string Stem, string Light, double Energy, double Range, double Share, int Max, int CapsMin, int CapsMax, double SizeMin, double SizeMax,
    string[]? Paths = null, double Step = 4, double SideMin = 2.8, double SideMax = 4.4, double PathLight = 0.5, double WoodLight = 0.25,
    string AltCap = "#e8c8ff", string AltLight = "#b070ff", double AltShare = 0, double HaloRadius = 0, double HaloK = 0.5,
    double[]? Pool = null, double CapEmit = 1, double CapInk = 0.38, double[]? Spill = null, string? SpillLight = null, string? SpillAlt = null);   // (lane J lead 8: "spill" [step radii x3 (x |r|), strengths x3], "spill_light", "spill_alt": painted light, NightGlow)   // (lead 5: "pool" [radius m, inner share, inner k, outer k, rim share, rim dark], "cap_emit", "cap_ink": painted light, NightGlow)   // (lead 3: "halo" [radius m, strength], glow_halo.gdshader)

public static class Palettes
{
    public static PaletteGlow? ReadGlow(JsonElement e)
    {
        if (!e.TryGetProperty("glow", out var g) || g.ValueKind != JsonValueKind.Object) return null;
        double D(string k, double d) => g.TryGetProperty(k, out var v) ? v.GetDouble() : d;
        string S(string k, string d) => g.TryGetProperty(k, out var v) ? v.GetString()! : d;
        var caps = g.TryGetProperty("caps", out var c) ? (c[0].GetInt32(), c[1].GetInt32()) : (3, 7);
        var size = g.TryGetProperty("size", out var z) ? (z[0].GetDouble(), z[1].GetDouble()) : (0.08, 0.22);
        var side = g.TryGetProperty("side", out var sd) ? (sd[0].GetDouble(), sd[1].GetDouble()) : (2.8, 4.4);
        string[]? paths = g.TryGetProperty("paths", out var ps) ? System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(ps.EnumerateArray(), x => x.GetString()!)) : null;
        return new PaletteGlow(S("cap", "#bff8ff"), S("stem", "#5fd0e0"), S("light", "#55e0ff"), D("energy", 1.6), D("range", 3.2), D("share", 0.45), (int)D("max", 40), caps.Item1, caps.Item2, size.Item1, size.Item2,
            paths, D("step", 4), side.Item1, side.Item2, D("path_light", 0.5), D("wood_light", 0.25), S("alt_cap", "#e8c8ff"), S("alt_light", "#b070ff"), D("alt_share", 0),
            g.TryGetProperty("halo", out var hl) ? hl[0].GetDouble() : 0, g.TryGetProperty("halo", out var hk) && hk.GetArrayLength() > 1 ? hk[1].GetDouble() : 0.5,
            g.TryGetProperty("pool", out var pl) ? System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(pl.EnumerateArray(), x => x.GetDouble())) : null,
            D("cap_emit", 1), D("cap_ink", 0.38),
            g.TryGetProperty("spill", out var sp) ? System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(sp.EnumerateArray(), x => x.GetDouble())) : null,
            g.TryGetProperty("spill_light", out var sl) ? sl.GetString() : null, g.TryGetProperty("spill_alt", out var sa) ? sa.GetString() : null);
    }

    /// <summary>The classes in their order (the shader's PAL_* index).</summary>
    public static readonly string[] Classes = ["leaf", "grass", "ground", "path", "stone", "bark"];
    public const int Row = 12;
    public const int EmberAt = 6 * Row;   // (ember: near m, far m, keep, 0: within near m of her light the palette is taken back by keep, none again at far m)
    public const int ValueAt = EmberAt + 4;   // (lead 2: each class its own "value", default the palette's: [leaf, grass, ground, path], [stone, bark, 0, 0])
    // (lead 3, judge r1 fix 1: one ramp and a shift put 94% of the day's leaves at h 30-55; the reference's crowns are each
    // crimson, orange or gold) the leaf class's two more ramps, a crown's own: "alt" [[3 colours], [3 colours]] (absent: the
    // leaf ramp again), and "mix" [share of crowns on alt 1, share on alt 2, per-tree shift, sky-facing tip shift] (absent:
    // 0, 0 and lead 2's one-ramp shifts, 0.42 and 0.27); "near" [darken, from m, to m]: the leaves by the camera that much
    // darker (1 - darken at the lens, none past to m), after the ramp, so the frame's edges hold the darkest masses.
    public const int LeafAltAt = ValueAt + 8;
    public const int LeafMixAt = LeafAltAt + 2 * Row;
    // (lead 3, judge r1 fix 4: her pool kept the ground's own brown albedo, a mud core) "ember" "albedo": the ground her pool
    // falls on, sRGB, taken by the keep in place of the albedo as built (absent: the albedo as built, as before).
    public const int EmberAlbedoAt = LeafMixAt + 8;
    // (lead 4, judge r2 fix 8: the reference's stones are warm grey with ochre moss on their tops) "stone" "moss" [sRGB, share]:
    // the moss laid after the ramp on what faces up, in patches (kit.gdshader; absent: none)
    public const int StoneMossAt = EmberAlbedoAt + 4;
    // (lane J lead 5: the reference's look is a bold dark contour on every form and a few lines inside; the world had almost
    // none: terrain, grass and stones' pixels fell in ink class 2 or the figures' thin line) "ink": the world's own line
    // (InkPass.SetWorld; static pixels only, her and the foes keep theirs): {"color" sRGB, "k" the multiply at a full line,
    // "px" the contour's width at 1080p, "crease" the inner lines' width share, "thin" a shallow drop's width share, "lum" the
    // HDR luminance it fades out above, "class" [4 width scales, by ink class 0-3], "inner" [4 crease weights], "crease_deg",
    // "depth" (the drop threshold's scale)}. Absent: px 0, the figure line on the world as before.
    public const int InkAt = StoneMossAt + 4;
    // (lead 5) "bands" [leaf, grass, ground, path, stone, bark] (flat steps on each ramp; 0 smooth), "band_edge" (the step's half width)
    public const int BandAt = InkAt + 28;
    // (lead 6, judge r4 cel fix 3: 2-4 inner lines a stone, 2-3 a trunk) "lines" [stone freq /m, bark freq /m, px, k]: a form's
    // inner lines, isolines of a world-space noise at a fixed screen width, broken in places (palette.gdshaderinc pal_lines)
    public const int LineAt = BandAt + 8;
    // (lane J lead 8: the painted stroke layer, paint_stroke.gdshaderinc) "stroke": +0 brush [cell,len,wid,bend], +4 tone [hue,lift,inner,chroma], +8 cover[0..3], +12 cover[4,5] + hit amount, emit, +16 hit color, +20 hit edge
    public const int StrokeAt = LineAt + 4;
    public static int Size => StrokeAt + 48;   // (lead 10: +28..47 the ground objects, ps_ob0..4)   // (lead 9: +24 frame [deg +, deg -, cmin, cs]: the marks' hue turn in the frame, InkPass)

    public static double[] Read(string name, JsonElement e)
    {
        var r = new double[Size];
        for (int c = 0; c < Classes.Length; c++)
        {
            if (!e.TryGetProperty(Classes[c], out var k)) continue;   // (absent: amount 0, the class as built)
            var ramp = k.GetProperty("ramp");
            if (ramp.GetArrayLength() != 3) throw new FormatException($"rigs.json palette {name}.{Classes[c]}: ramp needs 3 colours");
            var range = k.TryGetProperty("range", out var rg) ? (rg[0].GetDouble(), rg[1].GetDouble()) : (0.15, 0.55);
            int o = c * Row;
            for (int i = 0; i < 3; i++)
            {
                var (R, G, B) = Atmospheres.Linear(ramp[i].GetString()!);
                r[o + i * 4] = R; r[o + i * 4 + 1] = G; r[o + i * 4 + 2] = B;
            }
            r[o + 3] = k.TryGetProperty("amount", out var am) ? am.GetDouble() : 1;
            r[o + 7] = range.Item1;
            r[o + 11] = Math.Max(range.Item2, range.Item1 + 1e-3);
        }
        if (e.TryGetProperty("ember", out var em))
        {
            r[EmberAt] = em.TryGetProperty("near", out var n) ? n.GetDouble() : 0;
            r[EmberAt + 1] = em.TryGetProperty("far", out var f) ? f.GetDouble() : 0;
            r[EmberAt + 2] = em.TryGetProperty("keep", out var kp) ? kp.GetDouble() : 0;
            if (em.TryGetProperty("albedo", out var ea))
            {
                var (R, G, B) = Atmospheres.Linear(ea.GetString()!);
                r[EmberAlbedoAt] = R; r[EmberAlbedoAt + 1] = G; r[EmberAlbedoAt + 2] = B; r[EmberAlbedoAt + 3] = 1;
            }
        }
        if (e.TryGetProperty("stone", out var sto) && sto.TryGetProperty("moss", out var mo) && mo.GetArrayLength() == 2)
        {
            var (R, G, B) = Atmospheres.Linear(mo[0].GetString()!);
            r[StoneMossAt] = R; r[StoneMossAt + 1] = G; r[StoneMossAt + 2] = B; r[StoneMossAt + 3] = mo[1].GetDouble();
        }
        if (e.TryGetProperty("ink", out var ik))
        {
            double D(string k, double d) => ik.TryGetProperty(k, out var v) ? v.GetDouble() : d;
            var (R, G, B) = Atmospheres.Linear(ik.TryGetProperty("color", out var ic) ? ic.GetString()! : "#2a1838");
            r[InkAt] = R; r[InkAt + 1] = G; r[InkAt + 2] = B; r[InkAt + 3] = D("k", 1);
            r[InkAt + 4] = D("px", 3); r[InkAt + 5] = D("crease", 0.6); r[InkAt + 6] = D("thin", 1); r[InkAt + 7] = D("lum", 8);
            for (int i = 0; i < 4; i++)
            {
                r[InkAt + 8 + i] = ik.TryGetProperty("class", out var cw) && i < cw.GetArrayLength() ? cw[i].GetDouble() : i == 2 ? 0 : 1;
                r[InkAt + 12 + i] = ik.TryGetProperty("inner", out var cr) && i < cr.GetArrayLength() ? cr[i].GetDouble() : i is 0 or 3 ? 1 : 0;
            }
            r[InkAt + 16] = Math.Cos(D("crease_deg", 40) * Math.PI / 180); r[InkAt + 17] = D("depth", 1);
            // (lead 6, judge r4 cel fix 2) "fit": the contour at most this share of the form's width across (0: no cap), "fit_px": how far it looks for the far edge
            r[InkAt + 18] = D("fit", 0); r[InkAt + 19] = D("fit_px", 24);
            // "rim" [leaf, stone, bark weights], "rim_nv" [n.v full, n.v start]: the form's own contour (kit.gdshader pal_ink), the ink colour's
            var (Rr, Rg, Rb) = Atmospheres.Linear(ik.TryGetProperty("rim_color", out var rc) ? rc.GetString()! : "#3a2848");
            for (int i = 0; i < 3; i++) r[InkAt + 20 + i] = ik.TryGetProperty("rim", out var rw) && i < rw.GetArrayLength() ? rw[i].GetDouble() : 0;
            r[InkAt + 23] = ik.TryGetProperty("rim_nv", out var rn) && rn.GetArrayLength() > 1 ? rn[1].GetDouble() : 0.35;
            r[InkAt + 24] = Rr; r[InkAt + 25] = Rg; r[InkAt + 26] = Rb;
            r[InkAt + 27] = ik.TryGetProperty("rim_nv", out var rn2) && rn2.GetArrayLength() > 0 ? rn2[0].GetDouble() : 0.25;
        }
        if (e.TryGetProperty("bands", out var bd))
            for (int i = 0; i < Math.Min(6, bd.GetArrayLength()); i++) r[BandAt + (i < 4 ? i : i + 0)] = bd[i].GetDouble();
        r[BandAt + 6] = e.TryGetProperty("band_edge", out var be) ? be.GetDouble() : 0.06;
        r[BandAt + 7] = e.TryGetProperty("leaf_form", out var lfm) ? lfm.GetDouble() : 0;   // (lead 6: a crown's ramp from its cards' facing, this share)
        if (e.TryGetProperty("lines", out var ln))
            for (int i = 0; i < Math.Min(4, ln.GetArrayLength()); i++) r[LineAt + i] = ln[i].GetDouble();
        if (e.TryGetProperty("stroke", out var st))
        {
            double S(string k, double d) => st.TryGetProperty(k, out var v) ? v.GetDouble() : d;
            r[StrokeAt] = S("cell", 0); r[StrokeAt + 1] = S("len", 0); r[StrokeAt + 2] = S("wid", 0); r[StrokeAt + 3] = S("bend", 0);
            r[StrokeAt + 4] = S("hue", 0); r[StrokeAt + 5] = S("lift", 0); r[StrokeAt + 6] = S("inner", 0); r[StrokeAt + 7] = S("chroma", 1);
            r[StrokeAt + 19] = S("cmin", 0); r[StrokeAt + 23] = S("bare", 0.36);   // (lead 10: bare patch share, ps_hite.w)   // (a mark's chroma floor, Oklab C: on a near-grey field, a stone, a hue turn alone shows nothing)
            if (st.TryGetProperty("frame", out var fr))
                for (int i = 0; i < Math.Min(4, fr.GetArrayLength()); i++) r[StrokeAt + 24 + i] = fr[i].GetDouble();
            if (st.TryGetProperty("cover", out var cv))
                for (int i = 0; i < Math.Min(6, cv.GetArrayLength()); i++) r[StrokeAt + 8 + i] = cv[i].GetDouble();
            if (st.TryGetProperty("hit", out var ht))
            {
                r[StrokeAt + 14] = ht.TryGetProperty("amount", out var ha) ? ha.GetDouble() : 0;
                r[StrokeAt + 15] = ht.TryGetProperty("emit", out var he) ? he.GetDouble() : 0;
                if (ht.TryGetProperty("color", out var hc)) { var (R, G, B) = Atmospheres.Linear(hc.GetString()!); r[StrokeAt + 16] = R; r[StrokeAt + 17] = G; r[StrokeAt + 18] = B; }
                if (ht.TryGetProperty("edge", out var hd)) { var (R, G, B) = Atmospheres.Linear(hd.GetString()!); r[StrokeAt + 20] = R; r[StrokeAt + 21] = G; r[StrokeAt + 22] = B; }
            }
            // (lead 10, frozen spec: saturated colour in objects) "objects": {"a": [hex, hex], "b": hex, "ink": hex, "kind": 0 maple | 1 moss,
            // "dens": [A, B] per cell on the path's edge, "off": density share off the edge, "size": m, "emit", "tips": 0/1}
            if (st.TryGetProperty("objects", out var ob))
            {
                double O(string k, double d) => ob.TryGetProperty(k, out var v) ? v.GetDouble() : d;
                void C(string hex, int at) { var (R, G, B) = Atmospheres.Linear(hex); r[at] = R; r[at + 1] = G; r[at + 2] = B; }
                if (ob.TryGetProperty("a", out var oa)) { C(oa[0].GetString()!, StrokeAt + 28); C(oa[oa.GetArrayLength() - 1].GetString()!, StrokeAt + 32); }
                if (ob.TryGetProperty("b", out var obb)) C(obb.GetString()!, StrokeAt + 36);
                if (ob.TryGetProperty("ink", out var oi)) C(oi.GetString()!, StrokeAt + 40);
                if (ob.TryGetProperty("dens", out var od)) { r[StrokeAt + 31] = od[0].GetDouble(); r[StrokeAt + 35] = od[1].GetDouble(); }
                r[StrokeAt + 39] = O("size", 0); r[StrokeAt + 43] = O("kind", 0);
                r[StrokeAt + 44] = O("emit", 0); r[StrokeAt + 45] = O("tips", 0); r[StrokeAt + 46] = O("off", 0.15);
            }
        }
        // (lead 3) the leaf class's crowns: two more ramps (each its dark, mid, lit; amount and range the leaf ramp's), their shares, the shifts
        for (int a = 0; a < 2; a++)
            for (int i = 0; i < Row; i++) r[LeafAltAt + a * Row + i] = r[i];
        r[LeafMixAt + 2] = 0.42; r[LeafMixAt + 3] = 0.27;
        if (e.TryGetProperty("leaf", out var lf))
        {
            if (lf.TryGetProperty("alt", out var alt))
                for (int a = 0; a < Math.Min(2, alt.GetArrayLength()); a++)
                {
                    if (alt[a].GetArrayLength() != 3) throw new FormatException($"rigs.json palette {name}.leaf.alt[{a}]: needs 3 colours");
                    for (int i = 0; i < 3; i++)
                    {
                        var (R, G, B) = Atmospheres.Linear(alt[a][i].GetString()!);
                        int o = LeafAltAt + a * Row + i * 4;
                        r[o] = R; r[o + 1] = G; r[o + 2] = B;
                    }
                }
            if (lf.TryGetProperty("mix", out var mx))
                for (int i = 0; i < Math.Min(4, mx.GetArrayLength()); i++) r[LeafMixAt + i] = mx[i].GetDouble();
            if (lf.TryGetProperty("near", out var nr))
                for (int i = 0; i < Math.Min(4, nr.GetArrayLength()); i++) r[LeafMixAt + 4 + i] = nr[i].GetDouble();
        }
        // (value: 0 the ramp's own value, 1 the albedo's own luminance kept and only the ramp's hue and chroma taken, so the
        // lanes' tuned values hold and only the colour turns; saturated albedos at the sun's full value clip to white)
        r[EmberAt + 3] = e.TryGetProperty("value", out var vk) ? vk.GetDouble() : 0;
        // (lead 2: one value for every class clipped the day's bright bushes at .4 and flattened the sand path at .8: a class
        // may name its own, e.g. the path its ramp's value (low), the leaves the albedo's (high))
        for (int c = 0; c < Classes.Length; c++)
            r[ValueAt + c] = e.TryGetProperty(Classes[c], out var kc) && kc.TryGetProperty("value", out var cv) ? cv.GetDouble() : r[EmberAt + 3];
        return r;
    }

    /// <summary>a toward b by t; a missing palette is the other's with its amounts faded (the class as built at the end).</summary>
    public static double[]? Blend(double[]? a, double[]? b, double t)
    {
        if (t <= 0) return a;
        if (t >= 1) return b;
        if (a == null && b == null) return null;
        if (a == null || b == null)
        {
            var src = a ?? b!;
            double k = a == null ? t : 1 - t;
            var r = (double[])src.Clone();
            for (int c = 0; c < Classes.Length; c++) r[c * Row + 3] *= k;
            r[EmberAt + 2] *= k;
            return r;
        }
        var m = new double[a.Length];
        for (int i = 0; i < m.Length; i++) m[i] = a[i] + (b[i] - a[i]) * t;
        return m;
    }
}
