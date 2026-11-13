using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sound;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Ui;

namespace SurvivorUnchained.View;

/// <summary>
/// (bd-ui2) A stance swap seen in the world (Ev.Swap): every swap is a small ring at her feet and a glint up her weapon in the
/// stance's color (StanceBlock.ColorOf, so the HUD and the ground agree); when the swap strike LANDED (Strike != "") a big ring
/// at the strike's radius (from stances.json) and the stance's own accent follow, so a big ring always means "it landed".
/// Built from the neighbours' primitives: Nova's ground ring, Waves, Sparks, Blades crescents, Scars, WgPuff. --p7fx-off: none.
/// </summary>
public partial class BattleFx
{
    const float SwapRing = 1.1f;

    /// <summary>The world's colours for a stance's swap: its core and its leading edge (sRGB). Set I bronze (the HUD's own bronze is
    /// butter-cream, which is the gift's colour), Bulwark a steel at about 70% saturation (the HUD's icy cyan read as a Frost Nova),
    /// the rest the StanceBlock colour with the edge halfway to white.</summary>
    static (Color Core, Color Edge) SwapCols(string stance)
    {
        if (stance == "") return (new Color("#C07A35"), new Color("#F0B866"));
        if (stance == "shield")
        {
            static Color Muted(Color c) { float l = c.R * 0.3f + c.G * 0.59f + c.B * 0.11f; return new Color(Mathf.Lerp(l, c.R, 0.7f), Mathf.Lerp(l, c.G, 0.7f), Mathf.Lerp(l, c.B, 0.7f)); }
            return (Muted(new Color("#7FA3C8")), Muted(new Color("#D6E4F0")));
        }
        var ui = StanceBlock.ColorOf(stance);
        return (ui, ui.Lerp(Colors.White, 0.5f));
    }

    static Color SwapHue(string stance, float k) { var c = SwapCols(stance).Core.SrgbToLinear(); return new Color(c.R * k, c.G * k, c.B * k); }

    /// <summary>Screen pixels (at 1080p) per metre across the ground at a point, from the play camera.</summary>
    float PxPerM(Vector3 g)
    {
        if (GetViewport()?.GetCamera3D() is not { } cam) return 70;
        float v = cam.UnprojectPosition(g).DistanceTo(cam.UnprojectPosition(g + cam.GlobalBasis.X));
        return Mathf.Max(20, v * 1080f / Mathf.Max(1, GetViewport().GetVisibleRect().Size.Y));
    }

    /// <summary>One gradient ring on the ground, rebuilt each frame (its widths are in screen pixels, so its texture follows the radius).
    /// Drawn as a flat quad in front of the grass (not a decal: grass tips poked through a decal as olive specks), hidden only where
    /// something well nearer the camera (a body, a canopy) stands over it.</summary>
    sealed class SwapRingRig
    {
        public MeshInstance3D M = null!; public ShaderMaterial Mat = null!; public Image Img = null!; public ImageTexture Tex = null!; public byte[] Buf = null!;
        public float T, Life, R0, R1, CorePx, OutPx, InPx = 14, Inner, Body = 0.8f; public bool HardEdge; public Color Core, Edge; public Vector3 At;
    }
    const int SwapN = 256;
    readonly List<SwapRingRig> swapRings = new();
    readonly List<(Vector3 At, float T, Color Edge, StarQuad Star)> swapGlints = new();
    static Shader? ringShader, starShader;

    SwapRingRig RingNew(Vector3 at, float corePx, float outPx, (Color Core, Color Edge) cols)
    {
        ringShader ??= new Shader { Code = """
            shader_type spatial;
            render_mode unshaded, depth_test_disabled, depth_draw_never, cull_disabled, blend_add, shadows_disabled, fog_disabled;
            uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
            uniform sampler2D ring : source_color, filter_linear;
            uniform float energy = 1.7;
            uniform float fade = 1.0;
            void fragment() {
                float d = texture(depth_tex, SCREEN_UV).r;
                vec4 v = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, d, 1.0);
                float scene = -v.z / v.w;
                float occ = 1.0 - smoothstep(0.25, 0.5, -VERTEX.z - scene);
                vec4 t = texture(ring, UV);
                ALBEDO = t.rgb * energy;
                ALPHA = fade * occ;
            }
            """ };
        var rig = new SwapRingRig { CorePx = corePx, OutPx = outPx, Core = cols.Core, Edge = cols.Edge, At = at };
        rig.Buf = new byte[SwapN * SwapN * 4];
        rig.Img = Image.CreateFromData(SwapN, SwapN, false, Image.Format.Rgba8, rig.Buf);
        rig.Tex = ImageTexture.CreateFromImage(rig.Img);
        rig.Mat = new ShaderMaterial { Shader = ringShader, RenderPriority = 1 };
        rig.Mat.SetShaderParameter("ring", rig.Tex);
        rig.M = new MeshInstance3D { Mesh = new PlaneMesh { Size = Vector2.One }, MaterialOverride = rig.Mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Visible = false };
        AddChild(rig.M);
        return rig;
    }

    void SwapRingAdd(Vector3 at, float r0, float r1, float life, float corePx, float outPx, (Color Core, Color Edge) cols, bool bronze = false)
    {
        var rig = RingNew(at, corePx, outPx, cols);
        rig.T = 0; rig.Life = life; rig.R0 = r0; rig.R1 = r1;
        // Set A: a cream 3 px leading edge over a dark bronze body at 60% (so it does not merge with her persistent orange rings).
        if (bronze) { rig.HardEdge = true; rig.Body = 0.6f; }
        swapRings.Add(rig);
        SwapRingStep(rig);
    }

    void SwapRingStep(SwapRingRig g)
    {
        float k = Mathf.Clamp(g.T / g.Life, 0, 1);
        RingDraw(g, Mathf.Lerp(g.R0, g.R1, 1 - Mathf.Pow(1 - k, 2.357f)), k < 0.7f ? 1 : 1 - (k - 0.7f) / 0.3f);
    }

    /// <summary>Gradient ring at radius r: a bright core band at the leading edge (CorePx wide), an outer glow (OutPx), and the body fading to
    /// Inner over InPx inward. Radius eases out (70% of the way in the first 40% of the time).</summary>
    void RingDraw(SwapRingRig g, float r, float fade)
    {
        float ppm = PxPerM(g.At);
        float half = r + (g.OutPx + 3) / ppm;
        const int L = 256;
        var lut = new float[L];
        var lc = new Color[L];
        for (int i = 0; i < L; i++)
        {
            float d = (r - (i + 0.5f) / L * half) * ppm;      // px inside the leading edge (negative: outside it)
            float ch = g.CorePx * 0.5f, a;
            Color c;
            if (d < -ch) { a = Mathf.Pow(Mathf.Max(0, 1 + (d + ch) / Mathf.Max(g.OutPx, 0.01f)), 2f) * 0.6f; c = g.Edge; }
            else if (d <= ch) { a = 1; c = g.Edge; }
            else
            {
                float f = g.InPx > 0 ? Mathf.Max(0, 1 - (d - ch) / g.InPx) : 0;
                a = Mathf.Max(g.Inner, Mathf.Pow(f, 1.6f) * g.Body);
                c = g.HardEdge ? g.Core : g.Edge.Lerp(g.Core, g.InPx > 0 ? Mathf.Clamp((d - ch) / g.InPx, 0, 1) : 1);
            }
            lut[i] = a;
            lc[i] = c;
        }
        var b = g.Buf;
        for (int y = 0; y < SwapN; y++)
            for (int x = 0; x < SwapN; x++)
            {
                float u = (x + 0.5f) / SwapN * 2 - 1, v = (y + 0.5f) / SwapN * 2 - 1;
                float rr = Mathf.Sqrt(u * u + v * v);
                int o = (y * SwapN + x) * 4;
                if (rr >= 1) { b[o] = b[o + 1] = b[o + 2] = b[o + 3] = 0; continue; }
                int i = (int)(rr * L);
                float a = lut[i];
                var c = lc[i];
                b[o] = (byte)(c.R * a * 255); b[o + 1] = (byte)(c.G * a * 255); b[o + 2] = (byte)(c.B * a * 255); b[o + 3] = (byte)(a * 255);
            }
        g.Img.SetData(SwapN, SwapN, false, Image.Format.Rgba8, b);
        g.Tex.Update(g.Img);
        g.M.Visible = true;
        g.M.Position = g.At + Vector3.Up * 0.06f;
        g.M.Scale = new Vector3(half * 2, 1, half * 2);
        g.Mat.SetShaderParameter("fade", fade);
    }

    /// <summary>A crisp four-point star drawn as a camera-facing quad in screen pixels (arms a few px wide, a white core), over everything.</summary>
    sealed class StarQuad { public MeshInstance3D M = null!; public QuadMesh Q = null!; public ShaderMaterial Mat = null!; }

    StarQuad StarNew(Color arms, int priority)
    {
        starShader ??= new Shader { Code = """
            shader_type spatial;
            render_mode unshaded, depth_test_disabled, depth_draw_never, cull_disabled, blend_add, shadows_disabled, fog_disabled;
            uniform vec4 arms_col : source_color = vec4(1.0);
            uniform float total_px = 40.0;
            uniform float arm_px = 28.0;
            uniform float w_px = 2.0;
            uniform float core_px = 4.0;
            uniform float spin = 0.0;
            uniform float energy = 1.0;
            void vertex() {
                MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
            }
            void fragment() {
                vec2 p = (UV - 0.5) * total_px;
                float c = cos(spin), s = sin(spin);
                p = vec2(c * p.x - s * p.y, s * p.x + c * p.y);
                float h = arm_px * 0.5;
                vec2 q = abs(p);
                float hwx = max(0.6, w_px * 0.5 * (1.0 - 0.3 * q.x / h));
                float hwy = max(0.6, w_px * 0.5 * (1.0 - 0.3 * q.y / h));
                float ax = clamp(hwx + 0.5 - q.y, 0.0, 1.0) * clamp(h + 0.5 - q.x, 0.0, 1.0);
                float ay = clamp(hwy + 0.5 - q.x, 0.0, 1.0) * clamp(h + 0.5 - q.y, 0.0, 1.0);
                float arm = max(ax, ay);
                float core = clamp(core_px * 0.5 + 0.5 - length(p), 0.0, 1.0);
                ALBEDO = mix(arms_col.rgb * arm, vec3(1.0), core) * energy;
                ALPHA = max(arm, core);
            }
            """ };
        var st = new StarQuad { Q = new QuadMesh { Size = Vector2.One }, Mat = new ShaderMaterial { Shader = starShader, RenderPriority = priority } };
        st.Mat.SetShaderParameter("arms_col", arms);
        st.M = new MeshInstance3D { Mesh = st.Q, MaterialOverride = st.Mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, ExtraCullMargin = 4 };
        AddChild(st.M);
        return st;
    }

    void StarSet(StarQuad s, Vector3 at, float armPx, float wPx, float corePx, float spin, float energy = 1)
    {
        float total = armPx + 8;
        s.M.GlobalPosition = at;
        s.Q.Size = Vector2.One * total / PxPerM(at);
        s.Mat.SetShaderParameter("total_px", total);
        s.Mat.SetShaderParameter("arm_px", armPx);
        s.Mat.SetShaderParameter("w_px", wPx);
        s.Mat.SetShaderParameter("core_px", corePx);
        s.Mat.SetShaderParameter("spin", spin);
        s.Mat.SetShaderParameter("energy", energy);
    }

    /// <summary>Each frame: grows the swap rings and shows the glints.</summary>
    void SwapTick()
    {
        for (int i = swapRings.Count - 1; i >= 0; i--)
        {
            var g = swapRings[i];
            g.T += frameDt;
            if (g.T >= g.Life) { g.M.QueueFree(); swapRings.RemoveAt(i); continue; }
            SwapRingStep(g);
        }
        // The glint: a 28 px four-point star (2 px arms, a 4 px white core): 0.15 s in, 0.10 s held, 0.20 s out.
        for (int i = swapGlints.Count - 1; i >= 0; i--)
        {
            var (at, t, edge, star) = swapGlints[i];
            t += frameDt;
            if (t >= 0.45f) { star.M.QueueFree(); swapGlints.RemoveAt(i); continue; }
            swapGlints[i] = (at, t, edge, star);
            float s = t < 0.15f ? Mathf.SmoothStep(0, 1, t / 0.15f) : t < 0.25f ? 1 : 1 - Mathf.SmoothStep(0, 1, (t - 0.25f) / 0.2f);
            StarSet(star, at, 28f * Mathf.Max(s, 0.15f), 2.4f, 4f * Mathf.Max(s, 0.5f), 0);
        }
    }

    /// <summary>The strike's radius from the data: the stance's, or the Warden's set I strike for set I.</summary>
    static float SwapRadius(string stance) =>
        (float)(stance == "" ? Stances.SetA("warden")?.Radius ?? 3.4 : Stances.Find(stance)?.Strike.Radius ?? 3.0);

    void Swapped(Ev.Swap e)
    {
        if (P7Off) return;
        var ground = V(e.X, Y(e.X, e.Z), e.Z);
        var cols = SwapCols(e.Stance);
        // The small ring (every swap): 4 px core, 10 px glow, out from 0.6 m to 1.6 m, past her persistent rings.
        bool bronze = e.Stance == "";
        var rc = bronze ? (new Color("#8A5424"), new Color("#FFE2A8")) : cols;
        SwapRingAdd(ground, 0.6f, 1.6f, 0.25f, bronze ? 3 : 4, 10, rc, bronze);
        var side = GetViewport()?.GetCamera3D() is { } cam ? cam.GlobalBasis.X : Vector3.Right;
        swapGlints.Add((ground + Vector3.Up * 1.0f + side * 0.3f, 0, cols.Edge, StarNew(cols.Edge, 4)));
        Sfx.Blocked();
        if (e.Strike == "") return;

        float r = SwapRadius(e.Stance);
        var hue = SwapHue(e.Stance, 1.8f);
        Waves.Add(ground + Vector3.Up * 0.3f, r, 0.18f, cols.Core, 1f);
        SwapRingAdd(ground, 0.9f, r, 0.5f, 3, 2, rc, bronze);
        // A white-hot flash at the impact centre and a ring of dust and chips thrown outward.
        Ground(e.X, e.Z, 1.0f, glowTex!, Colors.White, 0.08f, 4f);
        // Dust (>= 20 px puffs, #6B5A44, 0.5 s) and chips (6 px, #3A2E22) thrown outward; solid, mixed over the grass, not light.
        float ppm = PxPerM(ground);
        var dust = new Color("#6B5A44").SrgbToLinear();
        var chip = new Color("#3A2E22").SrgbToLinear();
        for (int i = 0; i < 10; i++)
        {
            float a = Mathf.Tau * (i + R() * 0.6f) / 10f;
            var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            if (i % 5 == 4) Smoke.Spawn(new Sparks.P { At = ground + dir * 0.9f + Vector3.Up * 0.15f, V = dir * (3f + R() * 2f) + Vector3.Up * 2f, Gravity = 9, Drag = 0.5f, Life = 0.5f, Size = 6f / ppm, SizeEnd = 6f / ppm, Color = chip, ColorEnd = chip, Alpha = 1f, Sprite = SolidPuff(), Core = true });
            else WgPuff(ground + dir * 0.9f + Vector3.Up * 0.15f, dir * (3f + R() * 1.5f) + Vector3.Up * 0.3f, 24f / ppm, 1.4f, 0.5f, dust, 0.8f, 2.2f);
        }
        Cam?.AddTrauma(0.12f);
        Sfx.Bash();
        var at = ground + Vector3.Up * 0.9f;
        switch (e.Stance)
        {
            case "shield":
                // (the struck foes are not in this event, so no stars over them)
                SwapRingAdd(ground, 0.6f, r * 0.55f, 0.4f, 3, 2, rc, bronze);
                break;
            case "twin_blades":
                Blades.Add(at, 0.8f, r * 0.8f, 1.5f, false, 0.06f, 0.14f, hue, 0.3f);
                Blades.Add(at, -0.8f, r * 0.8f, 1.5f, true, 0.06f, 0.14f, hue, 0.3f, 0.05f);
                for (int i = 0; i < 6; i++)
                {
                    float a = R() * Mathf.Tau, d = R() * r * 0.6f;
                    Sparks.Spawn(ground + new Vector3(Mathf.Cos(a) * d, 0.8f + R() * 0.4f, Mathf.Sin(a) * d), new Vector3((R() - 0.5f), 0.3f, (R() - 0.5f)), 0.5f + R() * 0.3f, 0.05f, Blood, BloodDim, 0.02f, 9, 0.5f);
                }
                break;
            case "mace":
                Scars.Add("crack", ground, r * 0.9f, 6f, 0);
                break;
            default:
                // Set I: a bronze sweep of 270 degrees.
                Blades.Add(at, 0f, r * 0.9f, Mathf.Pi * 1.5f, false, 0.1f, 0.2f, hue, 0.3f);
                break;
        }
    }
}
