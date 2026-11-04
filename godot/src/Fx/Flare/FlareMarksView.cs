using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The ultimate's marks (H7: "no indicator of what it's hitting"): a lit ring on the ground under every foe in
/// Battle.FlareMarks, in Palette.Of(the Flare's school), as light on the ground (shaders/flare_mark.gdshader), all one
/// MultiMesh. At the press they ripple out from her by distance; a ring stays until its foe is hit, then flashes and pops;
/// one never hit fades when the cast ends. The Main (the hovered target) is twice the light, with an inner ring, a slow
/// breath and a thin light up its body. A line Flare's path (FlareMarkShape Line) lies as a faint strip. Every number is
/// data/content/flare_family.json "marks". Runs on real time.
/// </summary>
public partial class FlareMarksView : MultiMeshInstance3D
{
    public Func<double, double, double> HeightAt = (_, _) => 0;

    sealed class M
    {
        public double X, Z, R, Born, Delay, End = -1, Seed;
        public bool Main, Hit, Gone;
    }

    readonly Dictionary<int, M> marks = new();
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
        // (the soft shade first, the light over it: two passes of one batch)
        MaterialOverride = new ShaderMaterial
        {
            Shader = GD.Load<Shader>("res://shaders/flare_mark_shade.gdshader"),
            NextPass = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/flare_mark.gdshader") },
        };
        // (the rings span the field: the batch's own box is the arena, no per-instance culling)
        CustomAabb = new Aabb(new Vector3(-400, -50, -400), new Vector3(800, 100, 800));
        Visible = false;
    }

    public void Press(Battle b, School school, bool isNight, Vector3 at, double rt, Action<int> onCue)
    {
        marks.Clear();
        lines.Clear();
        lastLines.Clear();
        lineEnd = -1;
        var g = Palette.Of(school).Glow;
        float m = Mathf.Max(g.R, Mathf.Max(g.G, g.B));
        glow = m > 0 ? new Color(g.R / m, g.G / m, g.B / m) : Colors.White;
        night = isNight;
        her = at;
        cue = onCue;
        pressRt = lineBorn = lastRt = rt;
        live = true;
        logged = false;
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

    /// <summary>The marks' rim on a foe while it is marked (CrowdView, through FlareFx.MarkRim): 0 none.</summary>
    public float RimOf(int enemy)
    {
        if (!marks.TryGetValue(enemy, out var o)) return 0;
        var mr = FlareFamily.Marks;
        float r = (float)mr.Rim;
        if (o.Gone) return o.Hit ? r * 1.5f * Mathf.Max(0, 1 - (float)((lastRt - o.End) / Math.Max(mr.Pop, 1e-3))) : 0;
        return r * Mathf.Clamp((float)((lastRt - o.Born - o.Delay) / 0.05), 0, 1) * (o.Main ? 1.4f : 1);
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
        foreach (var (id, o) in marks)
        {
            double age = rt - o.Born - o.Delay;
            if (age < 0) continue;
            float alpha = Mathf.SmoothStep(0, 1, (float)Math.Min(1, age / 0.05));
            float pop = 0, flash = 1;
            if (o.Gone)
            {
                double k = rt - o.End;
                float p = (float)(k / Math.Max(o.Hit ? mr.Pop : mr.Fade, 1e-3));
                if (p >= 1) { drop.Add(id); continue; }
                if (o.Hit)
                {
                    pop = Mathf.SmoothStep(0, 1, p);
                    flash = 1 + 2.2f * (1 - p) * (1 - p);
                    alpha *= 1 - Mathf.SmoothStep(0.3f, 1, p);
                }
                else alpha *= 1 - p;
            }
            else drawnLive++;
            // (a fresh ring comes in a touch bright, then settles)
            flash *= 1 + 0.4f * Mathf.Max(0, 1 - (float)age / 0.12f);
            float gain = (float)ml.Gain * flash * (o.Main ? (float)mr.Main : 1) * alpha;
            float half = (float)(mr.Scale * Math.Max(o.R, 0.3) / 0.66);
            var at = new Vector3((float)o.X, (float)HeightAt(o.X, o.Z) + 0.06f, (float)o.Z);
            Put(n++, new Transform3D(new Godot.Basis(new Vector3(2 * half, 0, 0), new Vector3(0, 0, 2 * half), new Vector3(0, 1, 0)), at),
                new Color(glow.R * gain, glow.G * gain, glow.B * gain, (float)ml.Dark * alpha), new Color(o.Main ? 1 : 0, pop, pulse, (float)o.Seed));
            if (o.Main && !o.Gone)
            {
                // The Main's thin light up its body.
                float h = (float)(mr.Pillar * Math.Clamp(o.R / 0.45, 0.8, 3));
                float pg = gain * 0.5f;
                Put(n++, new Transform3D(new Godot.Basis(new Vector3(0.35f * h / 2.4f, 0, 0), new Vector3(0, h, 0), new Vector3(0, 0, 1)), at),
                    new Color(glow.R * pg, glow.G * pg, glow.B * pg, 0), new Color(3, 0, pulse, 0));
            }
        }
        foreach (var id in drop) marks.Remove(id);
        // The path of a line Flare: faint, in with the ripple, out over the fade.
        float la = lineEnd < 0 ? Mathf.SmoothStep(0, 1, (float)Math.Min(1, (rt - lineBorn) / Math.Max(mr.Ripple, 0.05)))
            : 1 - (float)((rt - lineEnd) / Math.Max(mr.Fade, 1e-3));
        if (la <= 0) { lineEnd = -1; lastLines.Clear(); }
        else foreach (var s in lastLines)
        {
            var along = new Vector3((float)Math.Cos(s.Angle), 0, (float)Math.Sin(s.Angle));
            var across = new Vector3(-along.Z, 0, along.X);
            float len = (float)s.Length, w = (float)(s.Radius * 2 * 1.6);
            double mx = s.X + along.X * len / 2, mz = s.Z + along.Z * len / 2;
            var mid = new Vector3((float)mx, (float)HeightAt(mx, mz) + 0.05f, (float)mz);
            float g = (float)ml.Strip * la;
            Put(n++, new Transform3D(new Godot.Basis(across * w, -along * len, Vector3.Up), mid), new Color(glow.R * g, glow.G * g, glow.B * g, 0),
                new Color(2, 0, (float)((rt - pressRt) * 0.6 % 1), len * 0.8f));
        }
        Multimesh.VisibleInstanceCount = n;
        Visible = n > 0;
        // (step 5d: the rings drawn against the sim's marks, once in the stop)
        if (!logged && live && b != null && rt - pressRt >= 0.2 && Args.Has("clip"))
        {
            logged = true;
            int mains = 0;
            foreach (var k in b.FlareMarks) if (k.Main) mains++;
            GD.Print($"flare marks {flare}: drawn {drawnLive} of FlareMarks.Count {b.FlareMarks.Count} (main {mains}), lines {lastLines.Count}, decision {b.FlareDecisionMarks}, late {b.FlareLateMarks}");
        }
    }

    void Put(int i, Transform3D t, Color c, Color custom)
    {
        Multimesh.SetInstanceTransform(i, t);
        Multimesh.SetInstanceColor(i, c);
        Multimesh.SetInstanceCustomData(i, custom);
    }
}
