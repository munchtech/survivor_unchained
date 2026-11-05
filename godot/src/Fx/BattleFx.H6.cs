using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// H6 round 1's judge, the kit's reads (fixes 2, 3, 7 and 8):
///
///   rocks take the marks   a red mark drawn by MarkPass lies only on the ground (a rock's cap is left alone), so a
///                          boulder hid a third of a pull's heart. Its decal (the pass's data) is shown again, culled
///                          to the rocks alone (MarkTakeLayer), so the rock's top carries the mark where the pass does not;
///   what knocked her       a caught charge's lane comes back full over the hit and fades over CaughtFade, a burst of
///                          dust at her feet thrown along it, and "Knocked down!" over her for 0.8 s;
///   barks off the fight    her place on the screen and points along every live kit mark, handed to Voices;
///   the gap's look         the closing's way out a lit floor strip (its two bright edges, no hatch) with a soft curtain of
///                          its cyan light rising off it.
/// </summary>
public partial class BattleFx
{
    /// <summary>The visual layer the rocks carry besides their own (ZoneView tags them, TagRocks): a red mark's decal
    /// is culled to it, so it lands on a boulder's top and never on the ground the pass already draws.</summary>
    public const uint MarkTakeLayer = 1u << 18;

    /// <summary>The app can now give every rock, boulder, stone and cliff under root the marks' layer (MarkTakeLayer),
    /// by its name or its group's ("kind:piece"). Returns how many were tagged.</summary>
    public static int TagRocks(Node root)
    {
        int n = 0;
        foreach (var c in root.FindChildren("*", "GeometryInstance3D", true, false))
        {
            var g = (GeometryInstance3D)c;
            if ((g.Layers & 1u) == 0) continue;
            bool rock = false;
            for (Node? p = g; p != null && p != root && !rock; p = p.GetParent()) rock = IsRock(p.Name);
            if (!rock && g is MeshInstance3D mi && mi.Mesh?.ResourcePath is { Length: > 0 } rp) rock = IsRock(rp);
            if (!rock && g is MultiMeshInstance3D mm && mm.Multimesh?.Mesh?.ResourcePath is { Length: > 0 } mp) rock = IsRock(mp);
            if (!rock) continue;
            g.Layers |= MarkTakeLayer;
            n++;
        }
        return n;
    }

    static bool IsRock(string s)
    {
        s = s.ToLowerInvariant();
        return s.Contains("rock") || s.Contains("boulder") || s.Contains("stone") || s.Contains("cliff") || s.Contains("crag") || s.Contains("outcrop") || s.Contains("menhir");
    }

    /// <summary>A red mark's decal as the rocks' copy of it (RedMarks, each frame): culled to the rocks, tall enough to
    /// reach a boulder's cap, shown while the pass draws the ground.</summary>
    static void OnRocks(Mark m)
    {
        var d = m.Decal;
        if (d.CullMask != MarkTakeLayer) d.CullMask = MarkTakeLayer;
        if (d.Size.Y < RockReach) d.Size = d.Size with { Y = RockReach };
        if (!d.Visible) d.Visible = true;
        if (m.Fill is { } f)
        {
            if (f.CullMask != MarkTakeLayer) f.CullMask = MarkTakeLayer;
            bool show = m.Progress;
            if (f.Visible != show) f.Visible = show;
        }
    }

    /// <summary>A red mark's rock copy's box height (m): a boulder's cap up to half of it over the mark's ground.</summary>
    const float RockReach = 6;

    /* ------------------------------------------------------- what knocked her -- */

    /// <summary>A caught lane's fade (s), and the knockdown's word's life.</summary>
    const float CaughtFade = 0.5f, KnockWordLife = 0.8f;

    void Caught(Ev.Knockdown kd)
    {
        float dx = 0, dz = 0;
        if (kd.Width > 0)
        {
            styleNext = 1;
            patternNext = MarkPass.PatternOf(null, null, "line");
            var lm = Lane(kd.FromX, kd.FromZ, kd.ToX, kd.ToZ, (float)kd.Width, Palette.TeleDanger, 10f, null, true);
            styleNext = 0;
            lm.Caught = true;
            lm.FadeFor = CaughtFade;
            lm.FadeLeft = CaughtFade;
            lm.T = HeldAt;
            double lx = kd.ToX - kd.FromX, lz = kd.ToZ - kd.FromZ, ll = Math.Sqrt(lx * lx + lz * lz);
            if (ll > 0.01) { dx = (float)(lx / ll); dz = (float)(lz / ll); }
        }
        // (the dust burst at her feet, thrown along the lane: the way the blow went)
        var at = V(kd.X, Y(kd.X, kd.Z) + 0.15, kd.Z);
        var pal = Palette.Of(School.Physical);
        float along = Mathf.Atan2(dz, dx);
        bool lane = dx != 0 || dz != 0;
        for (int i = 0; i < 12; i++)
        {
            float a = lane ? along + (R() - 0.5f) * 1.1f : R() * Mathf.Tau, v = 3.2f * (0.35f + R() * 0.65f);
            Smoke.Spawn(at, new Vector3(Mathf.Cos(a) * v, 0.4f + R() * 0.7f, Mathf.Sin(a) * v), 0.6f + R() * 0.4f, 0.35f, pal.Dim * 0.5f, pal.Dim * 0.2f, 1.1f, 0, 3, 0.5f);
        }
        Hits.Word(V(kd.X, Y(kd.X, kd.Z) + 2.4, kd.Z), "Knocked down!", new Color(2.0f, 0.55f, 0.4f), 46, KnockWordLife);
    }

    /* -------------------------------------------------------- barks off the fight -- */

    /// <summary>Her place and the live kit marks' points on the screen, for the barks (Voices.Fouls).</summary>
    void FeedBarks()
    {
        if (Lines == null || GetViewport()?.GetCamera3D() is not { } cam) return;
        Lines.FightFrame = Engine.GetProcessFrames();
        var pts = Lines.MarkPts;
        pts.Clear();
        var her = PlayerPos + Vector3.Up * 1.0f;
        Lines.HerScreen = cam.IsPositionBehind(her) ? null : cam.UnprojectPosition(her);
        foreach (var m in marks)
        {
            if (!m.Active || !(m.Danger || m.Amber || m.Color == ClosingRed)) continue;
            var d = m.Decal;
            Vector3 c = d.Position, ax = d.Basis.X.Normalized(), az = d.Basis.Z.Normalized();
            float hx = d.Size.X / 2, hz = d.Size.Z / 2;
            bool lane = m.Shape == 0 || m.Length > 0;
            if (lane)
            {
                // its two edges and its middle, a point a metre
                int n = Math.Clamp((int)(hz * 2), 2, 40);
                for (int j = 0; j <= n; j++)
                {
                    float t = -1 + 2f * j / n;
                    foreach (float s in (float[])[-0.9f, 0, 0.9f]) Pt(cam, c + ax * (hx * s) + az * (hz * t), pts);
                }
            }
            else
            {
                // its rim and two rings inside it (a band: its inner edge too), a point a metre
                float r = hx;
                int n = Math.Clamp((int)(Mathf.Tau * r), 12, 64);
                foreach (float k in (float[])[0.95f, 0.7f, 0.4f, 0f])
                    for (int j = 0; j < (k > 0 ? n : 1); j++)
                    {
                        float a = Mathf.Tau * j / n;
                        Pt(cam, c + new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * (r * k), pts);
                    }
            }
        }
    }

    static void Pt(Camera3D cam, Vector3 p, List<Vector2> into)
    {
        if (!cam.IsPositionBehind(p)) into.Add(cam.UnprojectPosition(p));
    }

    /* ------------------------------------------------------------- the gap's look -- */

    static Texture2D? gapTex;
    static Shader? curtainShader;
    readonly List<Mark> curtains = new();

    /// <summary>The closing's way out as a lit floor strip (its two bright edges, a soft glow between, no hatch) with a
    /// curtain of its light rising off it.</summary>
    void GapLook(Mark m)
    {
        gapTex ??= GroundTexture(8);
        m.Decal.TextureEmission = gapTex;
        curtainShader ??= new Shader
        {
            Code = """
                shader_type spatial;
                render_mode unshaded, blend_add, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
                uniform vec4 col : source_color = vec4(0.5, 0.8, 1.0, 1.0);
                uniform float fade = 1.0;
                varying vec3 lp;
                varying float side;
                void vertex() { lp = VERTEX; side = 1.0 - abs(NORMAL.y); }
                void fragment() {
                    float h = clamp(lp.y + 0.5, 0.0, 1.0);
                    // brightest at the strip, gone by the top; soft at its two ends and along its sides
                    float rise = pow(1.0 - h, 2.2);
                    float ends = smoothstep(0.5, 0.32, abs(lp.z));
                    // a slow breath of light climbing it
                    float wave = 0.82 + 0.18 * sin(h * 7.0 - TIME * 2.4 + lp.z * 3.0);
                    float a = rise * ends * wave * side * fade;
                    ALBEDO = col.rgb * a;
                    ALPHA = a;
                }
                """,
        };
        if (m.Curtain == null)
        {
            var mat = new ShaderMaterial { Shader = curtainShader };
            m.Curtain = new MeshInstance3D
            {
                Mesh = curtainBox ??= new BoxMesh { Size = Vector3.One },
                MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Layers = 1,
            };
            m.Curtain.AddToGroup(DangerGroup);
            AddChild(m.Curtain);
        }
        ((ShaderMaterial)m.Curtain.MaterialOverride).SetShaderParameter("col", Palette.TeleSafe * CurtainK);
        if (!curtains.Contains(m)) curtains.Add(m);
        StepCurtain(m);
    }

    static BoxMesh? curtainBox;
    /// <summary>The curtain's height (m) and its light (x the safe colour).</summary>
    const float CurtainH = 1.8f, CurtainK = 0.32f;

    void StepCurtain(Mark m)
    {
        var c = m.Curtain!;
        var d = m.Decal;
        c.Visible = m.Gap && m.Active && d.Visible;
        if (!c.Visible) return;
        c.Basis = d.Basis.Orthonormalized() * Godot.Basis.FromScale(new Vector3(d.Size.X * 0.82f, CurtainH, d.Size.Z));
        c.Position = d.Position + Vector3.Up * (CurtainH / 2 - 0.05f);
        ((ShaderMaterial)c.MaterialOverride).SetShaderParameter("fade", Mathf.Clamp(d.Modulate.A, 0, 1));
    }

    /// <summary>Each frame: the gap curtains with their marks, the barks' view of the fight.</summary>
    void StepH6()
    {
        for (int i = curtains.Count - 1; i >= 0; i--)
        {
            var m = curtains[i];
            if (m.Curtain == null) { curtains.RemoveAt(i); continue; }
            StepCurtain(m);
            if (!m.Curtain.Visible) curtains.RemoveAt(i);
        }
        FeedBarks();
    }
}
