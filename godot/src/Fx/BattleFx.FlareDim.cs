using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The fight's own lingering light under a Flare's stop (H7 r2, judge r1 fix 6: "her rune circles stayed bright on the
/// indigo"): every effect of the fight's under BattleFx (her rune circles and grounds, auras, shockwaves, ribbons, blades,
/// flipbooks, smoke, scars, skill and loot lights) falls by FlareFx's grade (flare_family.json grade.fx), as the world's
/// materials fall by its value. The Flare's own layers, the numbers and sparks (the hush has them), the blood (the decal
/// grade) and every danger mark are never touched: a node of the danger language joins the group "fx_danger" (FLARE_LOOK
/// §1.6: danger marks draw over everything, at full). Inherited: the hush's Sparks.Transparency (BattleFx.cs) and
/// FlareFx.Family's GradeLightsTake (lights by their colour, so flickering scripts keep the energy).
/// </summary>
public partial class BattleFx
{
    public const string DangerGroup = "fx_danger";
    /// <summary>The fight's own light x now (1 none): skill grounds' decals read it (FlareDimmed).</summary>
    public float FlareDim { get; private set; } = 1;
    readonly List<(GeometryInstance3D G, float T)> dimGeo = new();
    readonly List<(Light3D L, Color C)> dimLights = new();

    void FlareDimSet(float k)
    {
        if (k >= 1)
        {
            foreach (var (g, t0) in dimGeo) if (IsInstanceValid(g)) g.Transparency = t0;
            foreach (var (l, c) in dimLights) if (IsInstanceValid(l)) l.LightColor = c;
            dimGeo.Clear(); dimLights.Clear();
            FlareDim = 1;
            return;
        }
        if (FlareDim >= 1) FlareDimTake();
        FlareDim = k;
        foreach (var (g, t0) in dimGeo) if (IsInstanceValid(g)) g.Transparency = 1 - (1 - t0) * k;
        foreach (var (l, c) in dimLights) if (IsInstanceValid(l)) l.LightColor = new Color(c.R * k, c.G * k, c.B * k, c.A);
    }

    void FlareDimTake()
    {
        dimGeo.Clear(); dimLights.Clear();
        var stack = new Stack<Node>();
        foreach (var c in GetChildren()) stack.Push(c);
        while (stack.Count > 0)
        {
            var n = stack.Pop();
            if (n == Flare || n == Sparks || n == Hits || n == Gore || n.IsInGroup(DangerGroup)) continue;
            if (n is GeometryInstance3D g) dimGeo.Add((g, g.Transparency));
            else if (n is Light3D l) dimLights.Add((l, l.LightColor));
            foreach (var c in n.GetChildren()) stack.Push(c);
        }
        if (Args.Has("clip")) GD.Print($"flare dim: {dimGeo.Count} effects, {dimLights.Count} effect lights dimmed with the grade");
    }
}
