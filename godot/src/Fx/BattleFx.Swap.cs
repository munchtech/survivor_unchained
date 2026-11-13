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

    /// <summary>One gradient ring on the ground, rebuilt each frame (its widths are in screen pixels, so its texture follows the radius).</summary>
    sealed class SwapRingRig
    {
        public Decal D = null!; public Image Img = null!; public ImageTexture Tex = null!; public byte[] Buf = null!;
        public float T, Life, R0, R1, CorePx, OutPx; public Color Core, Edge; public Vector3 At;
    }
    const int SwapN = 256;
    readonly List<SwapRingRig> swapRings = new();
    readonly List<(Vector3 At, float T, Color Edge)> swapGlints = new();

    void SwapRingAdd(Vector3 at, float r0, float r1, float life, float corePx, float outPx, (Color Core, Color Edge) cols)
    {
        var rig = new SwapRingRig { T = 0, Life = life, R0 = r0, R1 = r1, CorePx = corePx, OutPx = outPx, Core = cols.Core, Edge = cols.Edge, At = at };
        rig.Buf = new byte[SwapN * SwapN * 4];
        rig.Img = Image.CreateFromData(SwapN, SwapN, false, Image.Format.Rgba8, rig.Buf);
        rig.Tex = ImageTexture.CreateFromImage(rig.Img);
        rig.D = new Decal { UpperFade = 0.3f, LowerFade = 0.3f, CullMask = 1, TextureEmission = rig.Tex, AlbedoMix = 0, NormalFade = MarkNormalFade, SortingOffset = DecalLayer.HerGround, Visible = false };
        AddChild(rig.D);
        swapRings.Add(rig);
        SwapRingDraw(rig);
    }

    /// <summary>Gradient ring: a bright core band at the leading edge (CorePx wide), an outer glow (OutPx), and a fade to nothing 14 px inward.
    /// Radius eases out (70% of the way in the first 40% of the time).</summary>
    void SwapRingDraw(SwapRingRig g)
    {
        float k = Mathf.Clamp(g.T / g.Life, 0, 1);
        float r = Mathf.Lerp(g.R0, g.R1, 1 - Mathf.Pow(1 - k, 2.357f));
        float ppm = PxPerM(g.At);
        float half = r + (g.OutPx + 3) / ppm;
        float fade = k < 0.7f ? 1 : 1 - (k - 0.7f) / 0.3f;
        const int L = 256;
        var lut = new float[L];
        var lc = new Color[L];
        for (int i = 0; i < L; i++)
        {
            float d = (r - (i + 0.5f) / L * half) * ppm;      // px inside the leading edge (negative: outside it)
            float ch = g.CorePx * 0.5f, a;
            if (d < -ch) a = Mathf.Pow(Mathf.Max(0, 1 + (d + ch) / Mathf.Max(g.OutPx, 0.01f)), 2f) * 0.6f;
            else if (d <= ch) a = 1;
            else a = Mathf.Pow(Mathf.Max(0, 1 - (d - ch) / 14f), 1.6f) * 0.8f;
            lut[i] = a;
            lc[i] = g.Edge.Lerp(g.Core, Mathf.Clamp((d - ch) / 14f, 0, 1));
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
        g.D.Visible = true;
        g.D.Position = g.At;
        g.D.Size = new Vector3(half * 2, 0.8f, half * 2);
        g.D.Modulate = new Color(1, 1, 1, fade);
        g.D.EmissionEnergy = 1.7f;
    }

    /// <summary>Each frame: grows the swap rings and shows the glints.</summary>
    void SwapTick()
    {
        for (int i = swapRings.Count - 1; i >= 0; i--)
        {
            var g = swapRings[i];
            g.T += frameDt;
            if (g.T >= g.Life) { g.D.QueueFree(); swapRings.RemoveAt(i); continue; }
            SwapRingDraw(g);
        }
        // The glint: a 28 px four-point star, 0.15 s in and 0.2 s out.
        for (int i = swapGlints.Count - 1; i >= 0; i--)
        {
            var (at, t, edge) = swapGlints[i];
            t += frameDt;
            if (t >= 0.35f) { swapGlints.RemoveAt(i); continue; }
            swapGlints[i] = (at, t, edge);
            float s = t < 0.15f ? Mathf.SmoothStep(0, 1, t / 0.15f) : 1 - Mathf.SmoothStep(0, 1, (t - 0.15f) / 0.2f);
            float size = 28f / PxPerM(at) * Mathf.Max(s, 0.05f);
            var c = edge.SrgbToLinear() * 2.4f;
            Sparks.Spawn(new Sparks.P { At = at, Life = frameDt * 1.5f, Size = size, SizeEnd = size, Color = c, ColorEnd = c, Sprite = Sprites.Of("star"), Spin = 0.2f });
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
        SwapRingAdd(ground, 0.6f, 1.6f, 0.25f, 4, 10, cols);
        var side = GetViewport()?.GetCamera3D() is { } cam ? cam.GlobalBasis.X : Vector3.Right;
        swapGlints.Add((ground + Vector3.Up * 1.0f + side * 0.3f, 0, cols.Edge));
        Sfx.Blocked();
        if (e.Strike == "") return;

        float r = SwapRadius(e.Stance);
        var hue = SwapHue(e.Stance, 1.8f);
        Waves.Add(ground + Vector3.Up * 0.3f, r, 0.18f, cols.Core, 1f);
        SwapRingAdd(ground, 0.9f, r, 0.5f, 3, 2, cols);
        // A white-hot flash at the impact centre and a ring of dust and chips thrown outward.
        Ground(e.X, e.Z, 1.0f, glowTex!, Colors.White, 0.08f, 4f);
        for (int i = 0; i < 10; i++)
        {
            float a = Mathf.Tau * (i + R() * 0.6f) / 10f;
            var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            if (i % 5 == 4) Sparks.Spawn(ground + dir * 0.9f + Vector3.Up * 0.15f, dir * (3f + R() * 2f) + Vector3.Up * 2f, 0.5f, 0.05f, WgDust(1.1f), WgDust(0.7f), 0.03f, 9, 0.5f);
            else WgPuff(ground + dir * 0.9f + Vector3.Up * 0.15f, dir * (3f + R() * 1.5f) + Vector3.Up * 0.3f, 0.3f, 1.5f, 0.5f, WgDust(0.8f), 0.5f, 2.2f);
        }
        Cam?.AddTrauma(0.12f);
        Sfx.Bash();
        var at = ground + Vector3.Up * 0.9f;
        switch (e.Stance)
        {
            case "shield":
                // (the struck foes are not in this event, so no stars over them)
                SwapRingAdd(ground, 0.6f, r * 0.55f, 0.4f, 3, 2, cols);
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
