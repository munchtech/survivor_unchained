using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// Loot's light (docs/design/LOOT_DESIGN.md §8.1-8.2): light standing on what fell, its height how
/// rare, its colour the band, so a horde's worth of the common and the uncommon can be ignored and
/// the rare few cannot.
///
///   Common and Uncommon: no light, their names only (a horde's worth of them must not glow);
///   Rare      a low blue glow;
///   Epic      violet, thinner and taller, breathing slowly;
///   Set       two strands of verdigris twisting about each other (never Uncommon's green line);
///   Legendary amber, Storied ember red: a pillar rising straight up past the top of the screen,
///             embers rising round its foot, and its light thrown on what stands near it, until
///             taken. As it falls its light comes down the screen onto it, and the pillar stands up
///             out of that.
///
/// Every light is drawn upright on the screen, not in the world (shaders/loot_beam.gdshader): under
/// a camera pitched 56 degrees a world-upright pillar leans away from the screen's middle and swells
/// as it climbs toward the camera, and the Legendary's read as a huge slanted cream bar. Each light
/// grows up out of the ground as its thing lands (by the pickup's own age, so it follows it as it
/// slides to rest), with no ring or hoop: light, never geometry. What the item filter hides is drawn
/// by the caller small and dark, with no light at all.
/// </summary>
public partial class BattleFx
{
    Batch? lootLight;
    readonly OmniLight3D[] lootLamps = new OmniLight3D[2];
    int lampsLit;
    // The Legendaries whose light has struck the ground (by pickup id), so the burst comes once.
    readonly HashSet<int> struck = new();
    /// <summary>How long a Legendary's light takes to fall onto it and stand up into its pillar.</summary>
    const float StrikeLife = 0.9f;
    /// <summary>How long a lesser light takes to grow up out of the ground as its thing lands.</summary>
    const float Arrive = 0.35f;

    static readonly Color Verdigris = new(0.16f, 0.8f, 0.66f), LegendAmber = new(1.0f, 0.52f, 0.12f), StoriedRed = new(1.0f, 0.28f, 0.1f);
    static readonly Color ChartPale = new(0.92f, 0.82f, 0.6f), QuestGold = new(1.0f, 0.76f, 0.3f);

    enum Lit { Rare = 1, Epic = 2, Set = 3, Pillar = 4, Strike = 5, Glow = 6, Shaft = 7 }

    // A moment's columns of light (Pillar): where, how tall and wide, in what colour, since when, how long.
    readonly List<(Vector3 At, float Height, float Width, Color Colour, double Born, float Life)> shafts = new();

    /// <summary>A column of light from the ground for a moment (a strike from the sky, a level gained,
    /// an evolution, a chest, the night won), drawn as loot's light is: upright on the screen, soft,
    /// held below the tone curve's knee. (On a world-upright tube, the night's 34 m column and its
    /// white core read as a huge slanted cream bar.) `radius` is its core's reach; its glow spreads
    /// four times wider.</summary>
    void Pillar(Vector3 at, float height, float radius, Color color, float life)
    {
        // Its hue kept, its brightness held to the knee.
        float top = Mathf.Max(color.R, Mathf.Max(color.G, color.B));
        var c = top > 1.1f ? new Color(color.R / top * 1.1f, color.G / top * 1.1f, color.B / top * 1.1f) : color;
        shafts.Add((at, height, Mathf.Max(0.5f, radius * 4), c, time, Mathf.Max(0.05f, life)));
    }

    void EnsureLoot()
    {
        if (lootLight != null) return;
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/loot_beam.gdshader") };
        lootLight = Add(new Batch(new QuadMesh { Size = Vector2.One }, 300, mat));
        for (int i = 0; i < lootLamps.Length; i++)
        {
            lootLamps[i] = new OmniLight3D { LightEnergy = 0, OmniRange = 7, OmniAttenuation = 1.4f, ShadowEnabled = false, Visible = false };
            AddChild(lootLamps[i]);
        }
    }

    void BeginLoot() { EnsureLoot(); lootLight!.Begin(); lampsLit = 0; }

    void EndLoot()
    {
        for (int i = shafts.Count - 1; i >= 0; i--)
        {
            var s = shafts[i];
            float k = (float)((time - s.Born) / s.Life);
            if (k >= 1 || k < 0) { shafts.RemoveAt(i); continue; }
            // Up fast out of the ground, then thinning away.
            float grow = Mathf.SmoothStep(0, 0.12f, k), fade = (1 - k) * (1 - k);
            Light(s.At.X, s.At.Y - 0.04f, s.At.Z, Lit.Shaft, 0, s.Width * (0.8f + 0.2f * grow), s.Height * (0.4f + 0.6f * grow), s.Colour, fade);
        }
        lootLight!.End();
        for (int i = lampsLit; i < lootLamps.Length; i++) lootLamps[i].Visible = false;
    }

    /// <summary>One light on the ground at (x, z): its kind and parameter ride in the basis's z scale,
    /// its half-width (and pool's reach) in x, its height in y.</summary>
    void Light(double x, float gy, double z, Lit kind, float param, float halfWidth, float height, Color colour, float strength) =>
        lootLight!.Add(new Transform3D(new Godot.Basis(new Vector3(halfWidth, 0, 0), new Vector3(0, Mathf.Max(0.05f, height), 0), new Vector3(0, 0, (int)kind + Mathf.Clamp(param, 0, 0.98f))), V(x, gy + 0.04, z)),
            colour with { A = strength });

    /// <summary>The light on a piece of loot rolled whole (p.Loot), or on what came without a tier.</summary>
    void LootLight(Pickup p, float gy, double now, Color fallback)
    {
        float t = (float)now;
        var tier = p.Loot >= 0 ? (LootTier)p.Loot
            : p.Kind == PickupKind.Quest ? LootTier.Quest
            : p.Kind is PickupKind.Item or PickupKind.Relic && p.Tier >= 2 ? (LootTier)Math.Min(p.Tier, (int)LootTier.Storied)
            : p.Kind == PickupKind.Chest ? LootTier.Book
            : LootTier.Common;
        // Landing, it grows up out of the ground, a little brighter for a moment (a thing laid down
        // long ago has an age far below zero: it is simply there).
        float age = (float)p.Age;
        float grow = age < 0 ? 1 : Mathf.SmoothStep(0, Arrive, age);
        float flare = age < 0 ? 1 : 1 + 0.6f * (1 - Mathf.SmoothStep(Arrive * 0.5f, Arrive * 2.5f, age));
        switch (tier)
        {
            case LootTier.Rare:
                Light(p.X, gy, p.Z, Lit.Rare, 0, 0.6f, 1.4f * grow, Palette.Rarity[2], 0.9f * flare);
                break;
            case LootTier.Epic:
            {
                // Breathing, slowly: the one in a field of blues that is not still.
                float breath = 0.72f + 0.28f * (0.5f + 0.5f * Mathf.Sin(t * 2.0f + p.Id));
                Light(p.X, gy, p.Z, Lit.Epic, 0, 0.7f, 2.3f * grow, Palette.Rarity[3], 0.95f * breath * flare);
                break;
            }
            case LootTier.Set:
                Light(p.X, gy, p.Z, Lit.Set, 0, 0.6f, 2.8f * grow, Verdigris, 0.95f * flare);
                break;
            case LootTier.Legendary or LootTier.Storied:
                Pillar(p, gy, t, tier == LootTier.Legendary ? LegendAmber : StoriedRed, tier == LootTier.Storied);
                break;
            case LootTier.Chart:
                Light(p.X, gy, p.Z, Lit.Glow, 0, 0.5f, 1.3f * grow, ChartPale, 0.6f);
                break;
            case LootTier.Quest:
                Light(p.X, gy, p.Z, Lit.Glow, 0, 0.5f, 1.2f * grow, QuestGold, 0.8f);
                break;
            case LootTier.Book:
                // (a chest, or a book: a short glow in its colour to find it by)
                Light(p.X, gy, p.Z, Lit.Glow, 0, 0.55f, 1.2f * grow, fallback, 0.6f);
                break;
        }
    }

    /// <summary>The hoard stone's light (Battle.Hoard): a short red one to find it by.</summary>
    void HoardLight(double x, float gy, double z) => Light(x, gy, z, Lit.Glow, 0, 0.6f, 2.2f, StoriedRed, 0.9f);

    /// <summary>A Legendary's (or a Storied thing's) pillar: light rising from it straight up the
    /// screen and past its top, a hot core in a wide soft glow, its light pooled on the ground and
    /// embers rising round its foot (Storied: more of them); its light on what stands near it. It
    /// stays until taken. As it falls, its light comes down the screen onto it first.</summary>
    void Pillar(Pickup p, float gy, float t, Color colour, bool storied)
    {
        float flicker = 0.93f + 0.07f * Mathf.Sin(t * 7.3f + p.Id) * Mathf.Sin(t * 3.1f);
        float age = (float)p.Age, stand = 1;
        if (age >= 0 && age < StrikeLife)
        {
            float k = age / StrikeLife;
            Light(p.X, gy, p.Z, Lit.Strike, k, 1.8f, 1f, colour, 1f);
            stand = Mathf.SmoothStep(0.38f, 0.75f, k);
            if (k < 0.45f) struck.Remove(p.Id);
            else if (struck.Add(p.Id)) Struck(V(p.X, gy, p.Z), colour);
        }
        if (stand > 0.01f) Light(p.X, gy, p.Z, Lit.Pillar, 0, 1.8f, 1f, colour, flicker * stand);
        if (frameDt > 0 && R() < (storied ? 26 : 14) * frameDt * stand)
        {
            float a = R() * Mathf.Tau, d = 0.35f + R() * 0.9f;
            double x = p.X + Mathf.Cos(a) * d, z = p.Z + Mathf.Sin(a) * d;
            Sparks.Spawn(V(x, Y(x, z) + 0.1, z), new Vector3(0, 1.0f + R() * 1.4f, 0), 0.9f + R() * 0.7f, 0.035f + R() * 0.03f, Ember, EmberDeep, 0.01f, -0.4f, 1.2f);
        }
        // Its light on what stands near it (two at most: the nearest of the rest go unlit).
        if (lampsLit < lootLamps.Length && stand > 0.01f)
        {
            var lamp = lootLamps[lampsLit++];
            var at = V(p.X, gy + 1.4, p.Z);
            float near = new Vector2(at.X - PlayerPos.X, at.Z - PlayerPos.Z).Length();
            lamp.Position = at;
            lamp.LightColor = colour;
            // Held off her as every light is that is not hers (she is lit by her own moments).
            lamp.LightEnergy = 1.5f * flicker * stand * Mathf.Lerp(0.35f, 1, Mathf.SmoothStep(1, 3.5f, near));
            lamp.Visible = true;
        }
    }

    /// <summary>A Legendary's light reaching the ground: embers thrown up and out, the camera
    /// jolted. (The flash on the ground is the strike's own, in the shader.)</summary>
    void Struck(Vector3 ground, Color colour)
    {
        for (int i = 0; i < 22; i++)
        {
            float a = R() * Mathf.Tau, v = 1.5f + R() * 2.5f;
            Sparks.Spawn(ground + Vector3.Up * 0.3f, new Vector3(Mathf.Cos(a) * v, 2.5f + R() * 3, Mathf.Sin(a) * v), 0.8f + R() * 0.5f, 0.045f, Ember, EmberDeep, 0.01f, 6, 1.2f);
        }
        Cam?.AddTrauma(0.15f);
    }

    /// <summary>Shown loot landing (Ev.Drop): a glint for the rare, the epic and the set. Their
    /// light grows up out of the ground on its own (LootLight); a Legendary's comes down onto it
    /// (Pillar).</summary>
    void Dropped(Ev.Drop d)
    {
        if (d.Quiet) return;
        var ground = V(d.X, Y(d.X, d.Z), d.Z);
        var c = (LootTier)d.Tier switch
        {
            LootTier.Rare => Palette.Rarity[2],
            LootTier.Epic => Palette.Rarity[3],
            LootTier.Set => Verdigris,
            _ => (Color?)null,
        };
        if (c is { } glint)
            Sparks.Spawn(ground + Vector3.Up * 0.5f, Vector3.Zero, 0.28f, d.Tier == (int)LootTier.Rare ? 0.5f : 0.7f, glint * 1.1f, null, 0.12f, sprite: Sprites.Of("star"), spinV: 3);
    }
}
