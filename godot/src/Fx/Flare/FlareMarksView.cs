using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The ultimate's marks (H7: "no indicator of what it's hitting"): a soft pool of light on the ground under every foe in
/// Battle.FlareMarks, in Palette.Of(the Flare's school) (shaders/flare_mark.gdshader), all one MultiMesh, with the light up
/// its body (the marks' rim and lift, vat.gdshaderinc). At the press they ripple out from her by distance. r2 (judge r1
/// fixes 3 and 5): no stroke, no pop. A pool stays through the blow and tightens, brighter, from the release up to the
/// moment the band reaches its foe (FlareFx.BandReachesRt), then hands over to the band's rim; one hit by an earlier blow
/// (no band yet) hands over at once; one never hit fades when the cast ends. The Main (the hovered target) is twice the
/// pool, size and light, with a hot core and a slow breath (no ray). A line Flare's path (FlareMarkShape Line) lies as a
/// faint strip unless its data draws a crack (the Long Cut: Line(), for FlareFx.LongCut's foreshadow). Every number is
/// data/content/flare_family.json "marks". Runs on real time.
/// </summary>
public partial class FlareMarksView : MultiMeshInstance3D
{
    public Func<double, double, double> HeightAt = (_, _) => 0;
    /// <summary>The band's hooks (FlareFx.Blow): real seconds until the band reaches a point (0 passed; huge before the
    /// blow), the main blow's real time (-1 none yet), the stop's release (real time, -1 none yet).</summary>
    public Func<float, float, double> BandRt = (_, _) => 1e9;
    public Func<double> BlowRt = () => -1, ReleaseRt = () => -1;

    sealed class M
    {
        public double X, Z, R, Born, Delay, End = -1, Seed, Hand = -1;
        public bool Main, Hit, Gone;
    }

    readonly Dictionary<int, M> marks = new();
    /// <summary>When each foe's mark was first drawn this cast (real time), for the decision hold (FlareFx.Blow).</summary>
    readonly Dictionary<int, double> shown = new();

    /// <summary>The real time this foe's mark was first drawn this cast; -1 never (not yet).</summary>
    public double ShownAt(int enemy) => shown.TryGetValue(enemy, out var r) ? r : -1;
    readonly List<int> drop = new();
    readonly List<FlareMarkShape> lines = new(), lastLines = new();
    double lineEnd = -1, pressRt, lineBorn, lastRt;
    Color glow;
    bool night;
    Vector3 her;
    Action<int> cue = _ => { };
    bool live, logged;

    /// <summary>Whether a cast's marks are up (press to its last hit).</summary>
    public bool Live => live;
    /// <summary>Whether anything is still drawn (a pop, a fade).</summary>
    public bool Showing => marks.Count > 0 || lastLines.Count > 0;

    public override void _Ready()
    {
        CastShadow = ShadowCastingSetting.Off;
        Multimesh = new MultiMesh
        {
            TransformFormat = MultiMesh.TransformFormatEnum.Transform3D, UseColors = true, UseCustomData = true,
            InstanceCount = 192, VisibleInstanceCount = 0, Mesh = new QuadMesh { Size = Vector2.One },
        };
        // (one premultiplied pass: the light, its cap and its shade together, so no shade outlives its light)
        MaterialOverride = mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/flare_mark.gdshader") };
        // (the rings span the field: the batch's own box is the arena, no per-instance culling)
        CustomAabb = new Aabb(new Vector3(-400, -50, -400), new Vector3(800, 100, 800));
        Visible = false;
    }

    ShaderMaterial? mat;

    /// <summary>The marks' look from the data (flare_mark.gdshaderinc's uniforms), at each press.</summary>
    void Look()
    {
        if (mat == null) return;
        var mr = FlareFamily.Marks;
        mat.SetShaderParameter("cap", (float)mr.Of(night).Cap);
        mat.SetShaderParameter("pool_k", (float)mr.Falloff);
        mat.SetShaderParameter("core", (float)mr.Core);
        mat.SetShaderParameter("core_gain", (float)mr.CoreGain);
        mat.SetShaderParameter("warm", (float)mr.Warm);
        mat.SetShaderParameter("seam_core", (float)(mr.SeamCore / SeamHalf));
        mat.SetShaderParameter("seam_glow", (float)(mr.SeamGlow / SeamHalf));
    }

    /// <summary>The path seam's strip half-width (m): its glow's falloff fits inside.</summary>
    static double SeamHalf => Math.Max(0.3, FlareFamily.Marks.SeamGlow * 3);

    /// <summary>Whether this cast draws its line's strip (false: the Flare draws its own crack, FlareFamily Own.Path).</summary>
    bool strip = true;

    /// <summary>The line Flare's path as the marks have it (the Long Cut's foreshadow): false none.</summary>
    public bool Line(out FlareMarkShape s)
    {
        s = default!;
        if (lastLines.Count == 0) return false;
        s = lastLines[0];
        return true;
    }

    public void Press(Battle b, School school, bool isNight, Vector3 at, double rt, Action<int> onCue, bool drawStrip = true)
    {
        strip = drawStrip;
        marks.Clear();
        shown.Clear();
        lines.Clear();
        lastLines.Clear();
        lineEnd = -1;
        var g = Palette.Of(school).Glow;
        float m = Mathf.Max(g.R, Mathf.Max(g.G, g.B));
        glow = m > 0 ? new Color(g.R / m, g.G / m, g.B / m) : Colors.White;
        night = isNight;
        Look();
        her = at;
        cue = onCue;
        pressRt = lineBorn = lastRt = rt;
        live = true;
        logged = false;
        pxStandSum = 0; pxStandN = 0; pxTight = -1; tightSeen = 1; tightLogged = false;
        Take(b, rt, true);
    }

    /// <summary>The marks as the sim has them now: new ones in (rippled out at the press, at once after: a decision's mark
    /// shows the frame it is made), the hit ones popped, and at the cast's end the rest faded.</summary>
    void Take(Battle b, double rt, bool press)
    {
        var mr = FlareFamily.Marks;
        double far = 1;
        if (press) foreach (var k in b.FlareMarks) far = Math.Max(far, Dist(k.X, k.Z));
        int fresh = 0;
        foreach (var k in b.FlareMarks)
        {
            if (marks.TryGetValue(k.Id, out var o) && !o.Gone)
            {
                o.X = k.X; o.Z = k.Z; o.R = k.Radius; o.Main = k.Main;
                continue;
            }
            marks[k.Id] = new M { X = k.X, Z = k.Z, R = k.Radius, Main = k.Main, Born = rt, Delay = press ? mr.Ripple * Dist(k.X, k.Z) / far : 0, Seed = k.Id * 0.6180339887 % 1 };
            fresh++;
        }
        // One cue a ripple, never one a foe (the audio pass makes the sound: Cue("mark", her, count)).
        if (fresh > 0) cue(fresh);
        bool liveNow = b.FlareMarksLive;
        foreach (var (id, o) in marks)
        {
            if (o.Gone) continue;
            bool listed = false;
            if (liveNow) foreach (var k in b.FlareMarks) if (k.Id == id) { listed = true; break; }
            if (listed) continue;
            // Gone from the list: hit (a flash and a pop) or, never hit, a fade.
            o.Gone = true; o.End = rt; o.Hit = b.FlareWasHit(id);
        }
        // The path: a line Flare's shapes while live, then faded.
        lines.Clear();
        if (liveNow) foreach (var s in b.FlareMarkShapes) if (s.Kind == FlareMarkShapeKind.Line) lines.Add(s);
        if (lines.Count > 0) { lineEnd = -1; lastLines.Clear(); lastLines.AddRange(lines); }
        else if (lastLines.Count > 0 && lineEnd < 0) lineEnd = rt;
        live = liveNow;
    }

    double Dist(double x, double z) => Math.Sqrt((x - her.X) * (x - her.X) + (z - her.Z) * (z - her.Z));

    /// <summary>The marks' rim (and its uplight) on a foe while it stands in its pool (CrowdView, through FlareFx.MarkRim):
    /// 0 none. It brightens with the pool's tightening and goes with the hand-over (the band's rim then).</summary>
    public float RimOf(int enemy)
    {
        if (!marks.TryGetValue(enemy, out var o)) return 0;
        var mr = FlareFamily.Marks;
        if (o.Hand >= 0 || (o.Gone && !o.Hit)) return 0;
        var (_, lk) = Tighten(o, lastRt);
        return (float)mr.Rim * Mathf.Clamp((float)((lastRt - o.Born - o.Delay) / 0.05), 0, 1) * (o.Main ? 1.4f : 1) * Mathf.Min(lk, 1.5f);
    }

    /// <summary>A pool's tightening now: its size x and its light x (1, 1 standing; Tight, TightLight as the band reaches it).
    /// From the release it eases a PreTight share of the way; from the main blow the rest, all of it as the band reaches
    /// its foe.</summary>
    (float Size, float Light) Tighten(M o, double rt)
    {
        var mr = FlareFamily.Marks;
        double k = 0, rel = ReleaseRt(), blow = BlowRt();
        if (rel >= 0) k = mr.PreTight * (1 - Math.Exp(-Math.Max(0, rt - rel) / Math.Max(mr.PreTime, 1e-3)));
        if (blow >= 0)
        {
            double left = BandRt((float)o.X, (float)o.Z);
            double run = Math.Max(1e-3, rt - blow + left);
            double kb = Math.Clamp((rt - blow) / run, 0, 1);
            k += (1 - k) * kb;
            if (left <= 0) k = 1;
        }
        float kk = Mathf.SmoothStep(0, 1, (float)k);
        return (Mathf.Lerp(1, (float)mr.Tight, kk), Mathf.Lerp(1, (float)mr.TightLight, kk));
    }

    public void Step(double dt, double rt, Battle? b, string? flare)
    {
        lastRt = rt;
        if (b != null && live) Take(b, rt, false);
        if (marks.Count == 0 && lastLines.Count == 0) { if (Visible) Visible = false; return; }
        var mr = FlareFamily.Marks;
        var ml = mr.Of(night);
        drop.Clear();
        int n = 0, cap = Multimesh.InstanceCount;
        int need = marks.Count * 2 + lastLines.Count + 1;
        if (need > cap) Multimesh.InstanceCount = Math.Max(need, cap * 2);
        int drawnLive = 0;
        float pulse = (float)((rt - pressRt) * mr.Pulse % 1);
        double blowRt = BlowRt();
        foreach (var (id, o) in marks)
        {
            double age = rt - o.Born - o.Delay;
            if (age < 0) continue;
            shown.TryAdd(id, rt);
            float alpha = Mathf.SmoothStep(0, 1, (float)Math.Min(1, age / 0.05));
            // The hand-over: as the band reaches its foe (after the main blow), or at once for one hit by an earlier blow
            // (no band yet); a foe the sim still lists is handed over too once the band has passed it.
            if (o.Hand < 0 && blowRt >= 0 && BandRt((float)o.X, (float)o.Z) <= 0 && (!o.Gone || o.Hit)) o.Hand = rt;
            // (two frames' grace: the main blow's own hits arrive with its event, which may land a frame after the sim's)
            if (o.Hand < 0 && o.Gone && o.Hit && blowRt < 0 && rt - o.End > 0.034) o.Hand = rt;
            var (size, lit) = Tighten(o, rt);
            if (o.Hand >= 0)
            {
                float p = (float)((rt - o.Hand) / Math.Max(mr.Hand, 1e-3));
                if (p >= 1) { drop.Add(id); continue; }
                alpha *= 1 - p;
            }
            else if (o.Gone && !o.Hit)
            {
                float p = (float)((rt - o.End) / Math.Max(mr.Fade, 1e-3));
                if (p >= 1) { drop.Add(id); continue; }
                alpha *= 1 - Mathf.SmoothStep(0, 1, p);
            }
            else drawnLive++;
            // (a fresh pool comes in a touch bright, then settles)
            float flash = 1 + 0.25f * Mathf.Max(0, 1 - (float)age / 0.12f);
            float gain = (float)ml.Gain * flash * lit * (o.Main ? (float)mr.Main : 1) * alpha;
            // (the quad's half is 2.2 sigma of the pool's falloff, ~1.87x its radius at a quarter light)
            float half = (float)(mr.Size * Math.Max(o.R, 0.3) * 1.87 * size * (o.Main ? mr.Main : 1));
            var at = new Vector3((float)o.X, (float)(HeightAt(o.X, o.Z) + mr.Above), (float)o.Z);
            Put(n++, new Transform3D(new Godot.Basis(new Vector3(2 * half, 0, 0), new Vector3(0, 0, 2 * half), new Vector3(0, 1, 0)), at),
                new Color(glow.R * gain, glow.G * gain, glow.B * gain, (float)ml.Dark * alpha), new Color(o.Main ? 1 : 0, 0, pulse, (float)o.Seed));
            if (!o.Main && o.Hand < 0) PxNote(o, half, size, blowRt >= 0);
        }
        foreach (var id in drop) marks.Remove(id);
        // The path of a line Flare: faint, in with the ripple, out over the fade.
        float la = !strip ? 0 : lineEnd < 0 ? Mathf.SmoothStep(0, 1, (float)Math.Min(1, (rt - lineBorn) / Math.Max(mr.Ripple, 0.05)))
            : 1 - (float)((rt - lineEnd) / Math.Max(mr.Fade, 1e-3));
        if (!strip) { if (lineEnd >= 0 && rt - lineEnd > mr.Fade) { lineEnd = -1; lastLines.Clear(); } }
        else if (la <= 0) { lineEnd = -1; lastLines.Clear(); }
        else foreach (var s in lastLines)
        {
            var along = new Vector3((float)Math.Cos(s.Angle), 0, (float)Math.Sin(s.Angle));
            var across = new Vector3(-along.Z, 0, along.X);
            float len = (float)s.Length, w = (float)(SeamHalf * 2);
            double mx = s.X + along.X * len / 2, mz = s.Z + along.Z * len / 2;
            var mid = new Vector3((float)mx, (float)HeightAt(mx, mz) + 0.05f, (float)mz);
            float g = (float)ml.Strip * la;
            Put(n++, new Transform3D(new Godot.Basis(across * w, -along * len, Vector3.Up), mid), new Color(glow.R * g, glow.G * g, glow.B * g, 0),
                new Color(2, 0, (float)((rt - pressRt) * mr.SeamShimmer % 1), len));
        }
        Multimesh.VisibleInstanceCount = n;
        Visible = n > 0;
        // (step 5d: the rings drawn against the sim's marks, once in the stop)
        if (!logged && live && b != null && rt - pressRt >= 0.2 && Args.Has("clip"))
        {
            logged = true;
            int mains = 0;
            foreach (var k in b.FlareMarks) if (k.Main) mains++;
            GD.Print($"flare marks {flare}: drawn {drawnLive} of FlareMarks.Count {b.FlareMarks.Count} (main {mains}), lines {lastLines.Count}, decision {b.FlareDecisionMarks}, late {b.FlareLateMarks}; pools {(pxStandN > 0 ? pxStandSum / pxStandN : 0):0} px across standing");
        }
        if (!tightLogged && BlowRt() >= 0 && drawnLive == 0 && Args.Has("clip"))
        {
            tightLogged = true;
            GD.Print($"flare marks {flare}: tightest {tightSeen:0.00}x ({pxTight:0} px across) before the hand-over, {(rt - BlowRt()):0.000} s real after the blow");
        }
    }

    // (for the pictures' log: an ordinary pool's quarter-light width at 1080p, standing in the stop and at its tightest)
    double pxStandSum, pxTight = -1; int pxStandN; float tightSeen = 1; bool tightLogged;
    void PxNote(M o, float half, float size, bool afterBlow)
    {
        if (!Args.Has("clip") || GetViewport()?.GetCamera3D() is not { } cam) return;
        float rq = half / 1.87f;
        var at = new Vector3((float)o.X, (float)HeightAt(o.X, o.Z), (float)o.Z);
        var right = cam.GlobalBasis.X.Normalized();
        float px = cam.UnprojectPosition(at + right * rq).DistanceTo(cam.UnprojectPosition(at - right * rq)) * 1080f / Mathf.Max(1, GetViewport().GetVisibleRect().Size.Y);
        if (!afterBlow) { pxStandSum += px; pxStandN++; }
        else if (size < tightSeen) { tightSeen = size; pxTight = px; }
    }

    void Put(int i, Transform3D t, Color c, Color custom)
    {
        Multimesh.SetInstanceTransform(i, t);
        Multimesh.SetInstanceColor(i, c);
        Multimesh.SetInstanceCustomData(i, custom);
    }
}
