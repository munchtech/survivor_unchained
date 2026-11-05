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
            if (a != null) a.Light.QueueFree();
            a = new AuraLight
            {
                Seed = e.Seed, Energy = (float)def.Energy,
                Light = new OmniLight3D
                {
                    LightColor = new Color(def.Color), OmniRange = (float)def.Range, OmniAttenuation = 1.4f,
                    LightEnergy = 0, ShadowEnabled = false, LightSpecular = 0.4f,
                },
            };
            AddChild(a.Light);
            auras[e.Id] = a;
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
        bool lying = e.Anim == EnemyAnim.Die && !dying;
        double fx = Math.Cos(e.Facing), fz = Math.Sin(e.Facing), lx = fz, lz = -fx;
        double ox = lying ? fx * 0.6 + lx * 0.5 : fx * def.Forward + lx * def.Left, oz = lying ? fz * 0.6 + lz * 0.5 : fz * def.Forward + lz * def.Left;
        double px = e.X + ox, pz = e.Z + oz;
        a.Light.Position = new Vector3((float)px, Y(px, pz) + (float)(lying ? def.LieHeight : def.Height), (float)pz);
        a.Light.LightEnergy = a.Energy * a.K;
        a.Light.Visible = a.K > 0.001f;
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
            if (a.K <= 0) { a.Light.QueueFree(); aurasGone.Add(id); }
        }
        foreach (var id in aurasGone) auras.Remove(id);
    }
}
