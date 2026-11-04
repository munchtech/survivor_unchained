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
        bool dying = e.State == EnemyState.Dying;
        a.K = dying ? Mathf.Max(0, a.K - fdt / AuraFadeOut) : Mathf.Min(1, a.K + fdt / AuraFadeIn);
        a.Light.Position = new Vector3((float)e.X, Y(e.X, e.Z) + (float)def.Height, (float)e.Z);
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
