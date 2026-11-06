using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/* The lights the bosses carry (H1 item 5, EnemyDef.CarriedLight): one OmniLight3D for each live foe whose def has one (only
 * the bosses: a handful at most), following it at its height, fading in as it comes and out as it dies. Off the crowd's
 * batched path, no shadows. */
public partial class BattleFx
{
    sealed class AuraLight
    {
        public OmniLight3D Light = null!;
        /// <summary>Its pool on the ground (EnemyLight.Pool) and its glass's halo (EnemyLight.Halo), if it has them.</summary>
        public OmniLight3D? Pool;
        public MeshInstance3D? Halo, Core;
        public double Seed;
        public float K, Energy;
        public bool Seen;
    }

    readonly Dictionary<int, AuraLight> auras = new();
    readonly List<int> aurasGone = new();
    const float AuraFadeIn = 0.6f, AuraFadeOut = 1.2f;

    /// <summary>A foe with a light this frame: keep its light on it (a new one for a new foe in a pooled slot).</summary>
    void Aura(Enemy e, float fdt)
    {
        var def = e.Def.CarriedLight!;
        if (!auras.TryGetValue(e.Id, out var a) || a.Seed != e.Seed)
        {
            if (a != null) { a.Light.QueueFree(); a.Pool?.QueueFree(); a.Halo?.QueueFree(); a.Core?.QueueFree(); }
            a = new AuraLight
            {
                Seed = e.Seed, Energy = (float)def.Energy,
                Light = new OmniLight3D
                {
                    LightColor = new Color(def.Color), OmniRange = (float)def.Range, OmniAttenuation = (float)def.Decay,
                    LightEnergy = 0, ShadowEnabled = false, LightSpecular = 0.4f,
                },
            };
            AddChild(a.Light);
            auras[e.Id] = a;
        }
        if (def.Pool > 0 && a.Pool == null)
        {
            a.Pool = new OmniLight3D { LightColor = new Color(def.Color), OmniAttenuation = 1.2f, LightEnergy = 0, ShadowEnabled = false, LightSpecular = 0.1f };
            AddChild(a.Pool);
        }
        if (def.Halo > 0 && a.Halo == null)
        {
            a.Halo = new MeshInstance3D { Mesh = new QuadMesh { Size = Vector2.One }, MaterialOverride = HaloMat(def.Color), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            AddChild(a.Halo);
            // (its core: a small, whiter disc over the glass, so the glass itself reads lit; drawn over what stands before it,
            // so the raised lamp's roof and his own head, between the glass and the camera, do not leave a dark box: r8)
            a.Core = new MeshInstance3D { Mesh = new QuadMesh { Size = Vector2.One }, MaterialOverride = CoreMat(), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            AddChild(a.Core);
        }
        a.Seen = true;
        // (read each frame: a boss's light may burn brighter as it goes on, its def swapped: Corvane's lamp below half)
        a.Energy = (float)def.Energy;
        a.Light.OmniRange = (float)def.Range;
        bool dying = e.State == EnemyState.Dying;
        a.K = dying ? Mathf.Max(0, a.K - fdt / AuraFadeOut) : Mathf.Min(1, a.K + fdt / AuraFadeIn);
        // Held where it is carried (EnemyLight Forward/Left: a lamp held out, not a light in his middle), on his drawn
        // facing; a story's body held down (EnemyAnim.Die while alive: Corvane lying where he fell) has it set on the ground
        // beside him.
        bool lying = (e.Laid || e.Anim == EnemyAnim.Die) && !dying;
        double fx = Math.Cos(e.Facing), fz = Math.Sin(e.Facing), lx = fz, lz = -fx;
        double ox = lying ? fx * 0.6 + lx * 0.5 : fx * def.Forward + lx * def.Left, oz = lying ? fz * 0.6 + lz * 0.5 : fz * def.Forward + lz * def.Left;
        double px = e.X + ox, pz = e.Z + oz;
        a.Light.Position = new Vector3((float)px, Y(px, pz) + (float)(lying ? def.LieHeight : def.Height), (float)pz);
        // On the glass itself where the body is drawn with one (CrowdView.GlassOn: the baked lamp's glass this frame, its
        // carry and its raise in it), in every pose: r7's light by his facing with an offset floated 60-170 px off it.
        bool onGlass = CrowdView.GlassOn.TryGetValue(e.Id, out var gl) && gl.Seed == e.Seed && Engine.GetProcessFrames() - gl.Frame <= 2;
        if (onGlass) { a.Light.Position = gl.At; px = gl.At.X; pz = gl.At.Z; }
        // Its script's moment (Corvane's tell: up to 3x as the lamp is raised, LightLift), and its waver (a flicker of two
        // slow beats and a quick one, never below 70% of itself).
        float fl = def.Flicker > 0 ? (float)(1 - def.Flicker * (0.5 + 0.25 * Math.Sin(time * 7.3 + e.Seed) + 0.15 * Math.Sin(time * 13.1 + e.Seed * 2) + 0.1 * Math.Sin(time * 31))) : 1f;
        float mul = (float)e.LightMul * fl;
        if (!onGlass && !lying && e.LightLift > 0) a.Light.Position += new Vector3(0, (float)e.LightLift, 0);
        a.Light.LightEnergy = a.Energy * a.K * mul;
        a.Light.Visible = a.K > 0.001f;
        if (a.Pool != null)
        {
            // (low over the ground where the lamp hangs, its reach its own: the pool the high light alone did not make)
            a.Pool.Position = new Vector3((float)px, Y(px, pz) + 0.55f, (float)pz);
            a.Pool.OmniRange = (float)def.PoolRange * (0.85f + 0.15f * (float)e.LightMul);
            a.Pool.LightEnergy = (float)def.Pool * a.K * mul;
            a.Pool.Visible = a.K > 0.001f && def.Pool > 0;
        }
        if (a.Halo != null)
        {
            // The glass's glow: a soft violet disc at the lamp, facing the camera, wider and brighter as the light is.
            float hs = (float)def.Halo * Mathf.Sqrt(Mathf.Max(0.2f, mul));
            // (drawn a little toward the camera, so the glass's own faces do not cut the glow off it: on it, not behind it)
            var toCam = GetViewport()?.GetCamera3D() is { } c3 ? (c3.GlobalPosition - a.Light.Position).Normalized() * 0.3f : Vector3.Zero;
            var on = onGlass ? a.Light.Position : a.Light.Position + new Vector3(0, -0.15f, 0);
            a.Halo.Position = on + toCam;
            a.Halo.Scale = new Vector3(hs, hs, hs);
            if (a.Halo.MaterialOverride is StandardMaterial3D hm) hm.AlbedoColor = new Color(def.Color) with { A = Mathf.Clamp(0.55f * a.K * Mathf.Min(1.6f, mul), 0, 1) };
            a.Halo.Visible = a.K > 0.001f && def.Halo > 0 && (!lying || onGlass);
            if (a.Core != null)
            {
                // (whiter by Core, brighter as the light is: the raised lamp's glass is the brightest thing on him)
                float cs = hs * 0.38f;
                a.Core.Position = on + toCam * 1.05f;
                a.Core.Scale = new Vector3(cs, cs, cs);
                if (a.Core.MaterialOverride is StandardMaterial3D cm)
                    cm.AlbedoColor = new Color(def.Color).Lerp(Colors.White, (float)def.Core) with { A = Mathf.Clamp(0.7f * a.K * Mathf.Min(1.8f, mul), 0, 1) };
                a.Core.Visible = a.Halo.Visible && def.Core > 0;
            }
        }
    }

    static GradientTexture2D? haloTex;
    static StandardMaterial3D CoreMat()
    {
        var m = HaloMat("#ffffff");
        m.NoDepthTest = true;
        m.RenderPriority = 1;
        return m;
    }
    /// <summary>An additive, unshaded, camera-facing disc with a soft edge (a lamp's glass glow).</summary>
    static StandardMaterial3D HaloMat(string color)
    {
        haloTex ??= new GradientTexture2D
        {
            Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f),
            Gradient = new Gradient { Offsets = [0f, 0.25f, 1f], Colors = [new Color(1, 1, 1, 1), new Color(1, 1, 1, 0.45f), new Color(1, 1, 1, 0)] },
        };
        return new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
            BlendMode = BaseMaterial3D.BlendModeEnum.Add, BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
            AlbedoTexture = haloTex, AlbedoColor = new Color(color), NoDepthTest = false,
        };
    }

    /// <summary>After the frame's foes: a light whose foe is gone fades out where it last stood, then goes.</summary>
    void StepAuras(float fdt)
    {
        aurasGone.Clear();
        foreach (var (id, a) in auras)
        {
            if (a.Seen) { a.Seen = false; continue; }
            a.K = Mathf.Max(0, a.K - fdt / AuraFadeOut);
            a.Light.LightEnergy = a.Energy * a.K;
            if (a.Pool != null) a.Pool.LightEnergy *= 0.9f;
            if (a.Halo != null) a.Halo.Visible = false;
            if (a.Core != null) a.Core.Visible = false;
            if (a.K <= 0) { a.Light.QueueFree(); a.Pool?.QueueFree(); a.Halo?.QueueFree(); a.Core?.QueueFree(); aurasGone.Add(id); }
        }
        foreach (var id in aurasGone) auras.Remove(id);
    }
}
