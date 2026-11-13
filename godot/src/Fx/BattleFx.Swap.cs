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

    static Color SwapHue(string stance, float k) { var c = StanceBlock.ColorOf(stance == "" ? null : stance).SrgbToLinear(); return new Color(c.R * k, c.G * k, c.B * k); }

    /// <summary>The strike's radius from the data: the stance's, or the Warden's set I strike for set I.</summary>
    static float SwapRadius(string stance) =>
        (float)(stance == "" ? Stances.SetA("warden")?.Radius ?? 3.4 : Stances.Find(stance)?.Strike.Radius ?? 3.0);

    void Swapped(Ev.Swap e)
    {
        if (P7Off) return;
        var ground = V(e.X, Y(e.X, e.Z), e.Z);
        var ui = StanceBlock.ColorOf(e.Stance == "" ? null : e.Stance);
        Nova(e.X, e.Z, SwapRing, ui, 0.35f);
        // The glint up the weapon: a bright star at hand height, rising.
        var hand = ground + Vector3.Up * 1.0f;
        Sparks.Spawn(hand, Vector3.Up * 1.6f, 0.38f, 0.32f, SwapHue(e.Stance, 2.6f), SwapHue(e.Stance, 0.6f), 0.08f, sprite: Sprites.Of("star"), spinV: 3);
        Sparks.Spawn(hand, Vector3.Up * 0.6f, 0.2f, 0.5f, SteelWhite * 0.5f, null, 0.15f, sprite: Sprites.Of("flare"));
        Sfx.Blocked();
        if (e.Strike == "") return;

        float r = SwapRadius(e.Stance);
        var hue = SwapHue(e.Stance, 1.8f);
        Waves.Add(ground + Vector3.Up * 0.3f, r, 0.18f, StanceBlock.ColorOf(e.Stance == "" ? null : e.Stance), 1f);
        Nova(e.X, e.Z, r, ui, 0.6f);
        Cam?.AddTrauma(0.12f);
        Sfx.Bash();
        var at = ground + Vector3.Up * 0.9f;
        switch (e.Stance)
        {
            case "shield":
                // (the struck foes are not in this event, so no stars over them)
                Nova(e.X, e.Z, r * 0.55f, new Color(0.62f, 0.78f, 1f), 0.45f);
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
                if (!WgNoDust)
                    for (int i = 0; i < 10; i++)
                    {
                        float a = Mathf.Tau * i / 10f;
                        WgPuff(ground + new Vector3(Mathf.Cos(a), 0.15f, Mathf.Sin(a)) * r * 0.5f, new Vector3(Mathf.Cos(a), 0.2f, Mathf.Sin(a)) * 2.5f, 0.3f, 1.4f, 0.6f, WgDust(0.8f), 0.4f, 2f);
                    }
                break;
            default:
                // Set I: a bronze sweep of 270 degrees.
                Blades.Add(at, 0f, r * 0.9f, Mathf.Pi * 1.5f, false, 0.1f, 0.2f, hue, 0.3f);
                break;
        }
    }
}
