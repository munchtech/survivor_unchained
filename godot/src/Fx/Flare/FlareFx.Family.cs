using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// The ultimate's family (H7, docs/team/hook/H7_flare_ultimate.md; data/content/flare_family.json): what every Strike Flare
/// does before its blow, over each Flare's own layers.
/// - The stop: the world's clock held from the press to the release (WorldRate, the data's worldRate), she at full speed.
/// - The hush: the ordinary damage numbers and hit sparks already up fade out at the press (Hush, then HushDone).
/// - The grade: the world's materials fall to moon indigo (flare_grade, flare_world.gdshaderinc flare_drain), the world's
///   own lamps, fires and windows dim (their colour scaled, put back after), blood decals with them (DecalGrade). Her, her
///   ember and the Flare's own light are left alone, so she is the one warm thing.
/// - The marks: FlareMarksView, one lit ring under every foe in Battle.FlareMarks, and the marked foe's rim.
/// </summary>
public partial class FlareFx
{
    /// <summary>The numbers' and sparks' fade at the press (1 shown .. 0 gone); HushDone retires what was up.</summary>
    public Action<float> Hush = _ => { };
    public Action HushDone = () => { };
    /// <summary>Blood decals' colour under the grade (white: none).</summary>
    public Action<Color> DecalGrade = _ => { };

    FlareMarksView? marksView;
    float gradeNow, hushNow = 1;
    bool hushing, familyOn;
    readonly List<(Light3D L, Color C)> gradeLights = new();
    Node? gradeRoot;
    static readonly StringName GradeParam = "flare_grade", GradeTintParam = "flare_grade_tint", MarkRimParam = "flare_mark_rim";

    /// <summary>The marks' rim on a foe (CrowdView.FlareMarkRim): 0 none.</summary>
    public float MarkRim(int enemy) => marksView?.RimOf(enemy) ?? 0;

    void FamilyPress(Ev.Flare e, Battle b, string calling)
    {
        familyOn = false;
        if (e.Stand) return;
        familyOn = true;
        hushing = true; hushNow = 1;
        gradeRoot = GetParent()?.GetParent();
        GradeLightsTake();
        if (marksView == null) { marksView = new FlareMarksView { HeightAt = HeightAt }; AddChild(marksView); }
        var def = Content.Lamps.Flare(e.Id);
        var school = def?.School ?? School.Holy;
        marksView.Press(b, school, Night, Her, rt, n => Cue("mark", Her, n));
        var g = Palette.Of(school).Glow;
        float gm = Mathf.Max(g.R, Mathf.Max(g.G, g.B));
        RenderingServer.GlobalShaderParameterSet(MarkRimParam, new Vector4(g.R / gm, g.G / gm, g.B / gm, 1));
    }

    /// <summary>A real-time step of the family: the hush, the grade and its lights, the marks.</summary>
    void FamilyTick(double dt, Battle? b)
    {
        // The hush: over the data's seconds from the press, then what was up is retired.
        if (hushing)
        {
            float h = (float)FlareFamily.Stop.Hush;
            hushNow = Mathf.Max(0, 1 - (float)t / Mathf.Max(h, 1e-3f));
            Hush(hushNow);
            if (hushNow <= 0) { hushing = false; HushDone(); Hush(1); }
        }
        // The grade: in over the data's frames from the press, held to the first blow (or a little past the release), then out.
        float g = 0;
        if (Active && familyOn)
        {
            var gr = FlareFamily.Grades;
            double from = spendAt >= 0 ? spendAt : lastAt >= 0 ? lastAt : releaseAt >= 0 ? releaseAt + 0.2 : double.MaxValue;
            float up = Mathf.SmoothStep(0, 1, (float)Math.Min(1, t / Math.Max(gr.In, 1e-3)));
            float down = t <= from ? 1 : 1 - Mathf.SmoothStep(0, 1, (float)Math.Min(1, (t - from) / Math.Max(gr.Out, 1e-3)));
            g = up * down;
        }
        if (g != gradeNow || g > 0) GradeSet(g);
        if (marksView != null) { marksView.Step(dt, rt, b, Active ? id : null); if (!marksView.Live && !marksView.Showing) RenderingServer.GlobalShaderParameterSet(MarkRimParam, Vector4.Zero); }
    }

    void GradeSet(float g)
    {
        var gr = FlareFamily.Grades.Of(Night);
        var tint = new Color(gr.Tint).SrgbToLinear();
        float tl = tint.R * 0.2126f + tint.G * 0.7152f + tint.B * 0.0722f;
        if (tl > 1e-4f) tint = new Color(tint.R / tl, tint.G / tl, tint.B / tl);
        RenderingServer.GlobalShaderParameterSet(GradeParam, new Vector4(g, (float)gr.Value, (float)gr.Keep, (float)gr.Emit));
        RenderingServer.GlobalShaderParameterSet(GradeTintParam, new Vector4(tint.R, tint.G, tint.B, 0));
        // The world's own lights (lamps, lamp-posts, fires, windows), by their colour: scripts that flicker drive the energy.
        float lk = Mathf.Lerp(1, (float)gr.Lights, g);
        foreach (var (l, c) in gradeLights)
            if (IsInstanceValid(l)) l.LightColor = new Color(c.R * lk, c.G * lk, c.B * lk, c.A);
        // Blood on the ground: the same fall, as a multiply (a decal has no albedo hook).
        float v = Mathf.Lerp(1, (float)gr.Value, g), keep = Mathf.Lerp(1, (float)gr.Keep, g);
        DecalGrade(new Color(v * Mathf.Lerp(tint.R, 1, keep), v * Mathf.Lerp(tint.G, 1, keep), v * Mathf.Lerp(tint.B, 1, keep)));
        if (g <= 0) GradeLightsGive();
        gradeNow = g;
    }

    /// <summary>The world's point and spot lights at the press (not hers, not the fight's effects', not the Flare's own).</summary>
    void GradeLightsTake()
    {
        GradeLightsGive();
        if (gradeRoot == null) return;
        var fx = GetParent();
        foreach (var n in gradeRoot.FindChildren("*", "Light3D", true, false))
        {
            if (n is not (OmniLight3D or SpotLight3D) || n is not Light3D l || !l.Visible) continue;
            bool skip = false;
            for (Node? p = l.GetParent(); p != null && p != gradeRoot; p = p.GetParent())
                if (p == fx || p is PlayerView) { skip = true; break; }
            if (!skip) gradeLights.Add((l, l.LightColor));
        }
        if (Args.Has("clip")) GD.Print($"flare grade: {gradeLights.Count} world lights dimmed");
    }

    void GradeLightsGive()
    {
        foreach (var (l, c) in gradeLights) if (IsInstanceValid(l)) l.LightColor = c;
        gradeLights.Clear();
    }

    void FamilyClear()
    {
        familyOn = false;
        if (hushing) { hushing = false; HushDone(); Hush(1); }
        if (gradeNow > 0) GradeSet(0);
        GradeLightsGive();
        DecalGrade(Colors.White);
        RenderingServer.GlobalShaderParameterSet(GradeParam, new Vector4(0, 1, 1, 1));
    }
}
