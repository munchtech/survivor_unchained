using System;
using Godot;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// Loot's light (docs/design/LOOT_DESIGN.md §8.1-8.2): a column on what fell, its height how
/// rare, its colour the band, drawn so a horde's worth of the common and the uncommon can be
/// ignored and the rare few cannot.
///
///   Common and Uncommon: no light, their names only (a horde's worth of them must not glow);
///   Rare      a blue column, two and a half metres;
///   Epic      violet, five metres, breathing slowly;
///   Set       two strands of verdigris twisting about each other (never Uncommon's green line);
///   Legendary amber, Storied ember red: a pillar off the top of the screen, a ring of embers on
///             the ground round it, and its light thrown on what stands near it, until taken.
///
/// What the item filter hides is drawn by the caller small and dark, with no light at all.
/// Every column is held below the tone curve's knee (shaders/loot_beam.gdshader).
/// </summary>
public partial class BattleFx
{
    Batch? lootLight;
    readonly OmniLight3D[] lootLamps = new OmniLight3D[2];
    int lampsLit;

    static readonly Color Verdigris = new(0.18f, 0.78f, 0.68f), LegendAmber = new(1.0f, 0.5f, 0.1f), StoriedRed = new(1.0f, 0.26f, 0.1f);

    void EnsureLoot()
    {
        if (lootLight != null) return;
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/loot_beam.gdshader") };
        lootLight = Add(new Batch(new CylinderMesh { TopRadius = 1, BottomRadius = 1, Height = 1, RadialSegments = 20, Rings = 1, CapTop = false, CapBottom = false }, 300, mat));
        for (int i = 0; i < lootLamps.Length; i++)
        {
            lootLamps[i] = new OmniLight3D { LightEnergy = 0, OmniRange = 7, OmniAttenuation = 1.4f, ShadowEnabled = false, Visible = false };
            AddChild(lootLamps[i]);
        }
    }

    void BeginLoot() { EnsureLoot(); lootLight!.Begin(); lampsLit = 0; }

    void EndLoot()
    {
        lootLight!.End();
        for (int i = lampsLit; i < lootLamps.Length; i++) lootLamps[i].Visible = false;
    }

    void Column(double x, float gy, double z, float height, float radius, Color colour, float strength) =>
        lootLight!.Add(new Transform3D(Godot.Basis.Identity.Scaled(new Vector3(radius, height, radius)), V(x, gy + height / 2, z)), colour with { A = strength });

    /// <summary>The light on a piece of loot rolled whole (p.Loot), or on gear and what else is
    /// worth carrying that came without a tier.</summary>
    void LootLight(Pickup p, float gy, double now, Color fallback)
    {
        if (p.Loot < 0)
        {
            Column(p.X, gy, p.Z, p.Kind is PickupKind.Material ? 1.2f : 2.5f, 0.16f, fallback, 0.55f);
            return;
        }
        float t = (float)now;
        switch ((LootTier)p.Loot)
        {
            case LootTier.Rare:
                Column(p.X, gy, p.Z, 2.5f, 0.2f, Palette.Rarity[2], 0.5f);
                break;
            case LootTier.Epic:
            {
                // Breathing, slowly: the one in a field of blues that is not still.
                float breath = 0.68f + 0.32f * (0.5f + 0.5f * Mathf.Sin(t * 2.2f + p.Id));
                Column(p.X, gy, p.Z, 5f, 0.26f, Palette.Rarity[3], 0.75f * breath);
                break;
            }
            case LootTier.Set:
            {
                // Two strands of verdigris twisting about each other up six metres, a faint core
                // between them: read by its twist, never as a single green line.
                const float H = 6f;
                const int N = 24;
                for (int k = 0; k < 2; k++)
                {
                    var pts = new Vector3[N + 1];
                    var w = new float[N + 1];
                    for (int j = 0; j <= N; j++)
                    {
                        float u = j / (float)N, a = t * 1.4f + k * Mathf.Pi + u * Mathf.Tau * 2.2f, rr = 0.3f * (1 - 0.35f * u);
                        pts[j] = V(p.X + Mathf.Cos(a) * rr, gy + 0.05 + u * H, p.Z + Mathf.Sin(a) * rr);
                        w[j] = Mathf.Min(1, u * 8) * (1 - u);
                    }
                    Ribbons.Now(pts, 0.09f, Verdigris, 1.6f, Ribbons.Style.Glow, w);
                }
                Column(p.X, gy, p.Z, H, 0.1f, Verdigris, 0.3f);
                break;
            }
            case LootTier.Legendary or LootTier.Storied:
                Pillar(p, gy, t, p.Loot == (int)LootTier.Legendary ? LegendAmber : StoriedRed);
                break;
            case LootTier.Chart:
                Column(p.X, gy, p.Z, 2f, 0.15f, new Color(0.9f, 0.82f, 0.62f), 0.45f);
                break;
            case LootTier.Quest:
                Column(p.X, gy, p.Z, 1.5f, 0.15f, new Color(1.0f, 0.78f, 0.35f), 0.55f);
                break;
            case LootTier.Book:
                Column(p.X, gy, p.Z, 1.5f, 0.15f, fallback, 0.45f);
                break;
        }
    }

    /// <summary>A Legendary's (or a Storied thing's) pillar: forty metres, off the top of the
    /// screen from the camera, a hot narrow core in a wide glow; a ring of embers round its foot
    /// on the ground, rising; its light on what stands near it. It stays until taken.</summary>
    void Pillar(Pickup p, float gy, float t, Color colour)
    {
        const float H = 40f;
        float flicker = 0.92f + 0.08f * Mathf.Sin(t * 7.3f + p.Id) * Mathf.Sin(t * 3.1f);
        Column(p.X, gy, p.Z, H, 0.6f, colour, 0.6f * flicker);
        Column(p.X, gy, p.Z, H, 0.2f, new Color(colour.R, colour.G * 1.2f, colour.B * 1.4f), 0.6f * flicker);
        // The ring of embers on the ground round it.
        const int N = 40;
        var ring = new Vector3[N + 1];
        for (int j = 0; j <= N; j++)
        {
            float a = j / (float)N * Mathf.Tau;
            double x = p.X + Mathf.Cos(a) * 1.15, z = p.Z + Mathf.Sin(a) * 1.15;
            ring[j] = V(x, Y(x, z) + 0.06, z);
        }
        Ribbons.Now(ring, 0.08f, colour * 0.8f, 1.1f * flicker, Ribbons.Style.Flame);
        if (frameDt > 0 && R() < 30 * frameDt)
        {
            float a = R() * Mathf.Tau, d = 1.0f + R() * 0.3f;
            double x = p.X + Mathf.Cos(a) * d, z = p.Z + Mathf.Sin(a) * d;
            Sparks.Spawn(V(x, Y(x, z) + 0.1, z), new Vector3(0, 1.2f + R() * 1.4f, 0), 0.9f + R() * 0.6f, 0.04f + R() * 0.03f, Ember, EmberDeep, 0.01f, -0.4f, 1.2f);
        }
        // Its light on what stands near it (two at most: the nearest of the rest go unlit).
        if (lampsLit < lootLamps.Length)
        {
            var lamp = lootLamps[lampsLit++];
            var at = V(p.X, gy + 1.6, p.Z);
            float near = new Vector2(at.X - PlayerPos.X, at.Z - PlayerPos.Z).Length();
            lamp.Position = at;
            lamp.LightColor = colour;
            // Held off her as every light is that is not hers (she is lit by her own moments).
            lamp.LightEnergy = 1.6f * flicker * Mathf.Lerp(0.35f, 1, Mathf.SmoothStep(1, 3.5f, near));
            lamp.Visible = true;
        }
    }

    /// <summary>Shown loot landing (Ev.Drop): a glint for the rare, a ring for the epic, and for a
    /// Legendary a column of its light falling down onto it and the ground thrown back.</summary>
    void Dropped(Ev.Drop d)
    {
        if (d.Quiet) return;
        float gy = Y(d.X, d.Z);
        var ground = V(d.X, gy, d.Z);
        switch ((LootTier)d.Tier)
        {
            case LootTier.Rare:
                Sparks.Spawn(ground + Vector3.Up * 0.6f, Vector3.Zero, 0.25f, 0.6f, Palette.Rarity[2] * 1.2f, null, 0.1f, sprite: Sprites.Of("star"), spinV: 3);
                break;
            case LootTier.Epic or LootTier.Set:
            {
                var c = d.Tier == (int)LootTier.Set ? Verdigris : Palette.Rarity[3];
                AddFront(ground, 1.6f, 0.45f, 0.08f, c, 1.4f, Ribbons.Style.Glow, 0.1f);
                Sparks.Spawn(ground + Vector3.Up * 0.7f, Vector3.Zero, 0.3f, 0.9f, c * 1.2f, null, 0.15f, sprite: Sprites.Of("star"), spinV: 3);
                break;
            }
            case LootTier.Legendary or LootTier.Storied:
            {
                var c = d.Tier == (int)LootTier.Legendary ? LegendAmber : StoriedRed;
                // Its light comes down out of the sky onto it.
                Band(ground + Vector3.Up * 30f, ground + Vector3.Up * 0.2f, 0.35f, c * 1.3f, 0.35f);
                AddFront(ground, 3f, 0.6f, 0.14f, c, 1.6f, Ribbons.Style.Flame, 0.1f);
                Waves.Add(ground + Vector3.Up * 0.3f, 3.5f, 0.5f, c, 0.7f);
                for (int i = 0; i < 26; i++)
                {
                    float a = R() * Mathf.Tau, v = 2 + R() * 3;
                    Sparks.Spawn(ground + Vector3.Up * 0.3f, new Vector3(Mathf.Cos(a) * v, 2.5f + R() * 3, Mathf.Sin(a) * v), 0.8f + R() * 0.5f, 0.05f, Ember, EmberDeep, 0.01f, 6, 1.2f);
                }
                Cam?.AddTrauma(0.15f);
                break;
            }
        }
    }
}
