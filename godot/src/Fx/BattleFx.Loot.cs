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

    enum Lit { Rare = 1, Epic = 2, Set = 3, Pillar = 4, Strike = 5, Glow = 6, Shaft = 7, Band = 8, Stars = 9 }

    // A moment's columns of light (Pillar): where, how tall and wide, in what colour, since when, how
    // long, and how thick the motes riding up it.
    readonly List<(Vector3 At, float Height, float Width, Color Colour, double Born, float Life, float Motes)> shafts = new();

    /// <summary>A column of light from the ground for a moment (a strike from the sky, a level gained,
    /// an evolution, a chest, the night won), drawn as loot's light is: upright on the screen, soft,
    /// held below the tone curve's knee. (On a world-upright tube, the night's 34 m column and its
    /// white core read as a huge slanted cream bar.) `radius` is its core's reach; its glow spreads
    /// four times wider. `motes`: light riding up it (0 to 1).</summary>
    void Pillar(Vector3 at, float height, float radius, Color color, float life, float motes = 0)
    {
        // Its hue kept, its brightness held to the knee.
        float top = Mathf.Max(color.R, Mathf.Max(color.G, color.B));
        var c = top > 1.1f ? new Color(color.R / top * 1.1f, color.G / top * 1.1f, color.B / top * 1.1f) : color;
        shafts.Add((at, height, Mathf.Max(0.5f, radius * 4), c, time, Mathf.Max(0.05f, life), motes));
    }

    void EnsureLoot()
    {
        if (lootLight != null) return;
        var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/loot_beam.gdshader") };
        lootLight = Add(new Batch(new QuadMesh { Size = Vector2.One }, 300, mat));
        for (int i = 0; i < lootLamps.Length; i++)
        {
            // Low and short: at 1.4 m up with a 7 m reach, by night it warmed the ground 300 px across,
            // lighting the clearing; this marks the spot and what stands on it (about 180 px).
            lootLamps[i] = new OmniLight3D { LightEnergy = 0, OmniRange = 2.8f, OmniAttenuation = 1.4f, ShadowEnabled = false, Visible = false };
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
            Light(s.At.X, s.At.Y - 0.04f, s.At.Z, Lit.Shaft, s.Motes, s.Width * (0.8f + 0.2f * grow), s.Height * (0.4f + 0.6f * grow), s.Colour, fade);
        }
        StoryLights();
        lootLight!.End();
        for (int i = lampsLit; i < lootLamps.Length; i++) lootLamps[i].Visible = false;
    }

    /// <summary>One light on the ground at (x, z): its kind and parameter ride in the basis's z scale,
    /// its half-width (and pool's reach) in x, its height in y.</summary>
    void Light(double x, float gy, double z, Lit kind, float param, float halfWidth, float height, Color colour, float strength) =>
        lootLight!.Add(new Transform3D(new Godot.Basis(new Vector3(halfWidth, 0, 0), new Vector3(0, Mathf.Max(0.05f, height), 0), new Vector3(0, 0, (int)kind + Mathf.Clamp(param, 0, 0.98f))), V(x, gy + 0.04, z)),
            colour with { A = strength });

    /// <summary>The light on a piece of loot rolled whole (p.Loot), or on what came without a tier.</summary>
    /// <summary>--clean: stills with no loot lights, beams or names over the picture.</summary>
    static readonly bool CleanShots = Args.Has("clean");

    readonly HashSet<int> gemLanded = new();

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
                if (tier == LootTier.Legendary && GiftSchool(p) is { } gs) GiftLook(p, gy, t, age, gs);
                Pillar(p, gy, t, tier == LootTier.Legendary ? LegendAmber : StoriedRed, tier == LootTier.Storied);
                break;
            case LootTier.Gem:
            {
                // A cut stone in its own colour: a soft additive pool of its light 1.0 m across (35% in the centre, fading to nothing)
                // with four feathered rays 0.25 m wide at 20%, turning slowly, and nine star motes (7 px, 70%) rising 1.2 s each.
                // It flashes once as it lands, then every 1.7 s catches the light: a four-point star 0.9 m across for 0.45 s.
                var gc = Ui.ItemViews.GemGround(p.Payload as ItemInstance) ?? fallback;
                // W24: the pool sits on the ground under the landing spot (the item's own ground height, never the stone's bob), at its
                // full extent (a quad grown from nothing cut the pool with a hard line at the foot), hidden until the stone is down
                // (Arrive) and then fading in over 0.25 s.
                float poolIn = age < 0 ? 1 : Mathf.Clamp((age - Arrive) / 0.25f, 0, 1);
                if (poolIn > 0.001f) Light(p.X, Y(p.X, p.Z), p.Z, Lit.Stars, 0, 1.0f, 1.8f, gc, 1.0f * poolIn);
                var star = gc.Lerp(Colors.White, 0.4f) * 2.2f;
                if (age >= 0 && age < 0.5f && gemLanded.Add(p.Id))
                    Sparks.Spawn(V(p.X, gy + 0.3, p.Z), Vector3.Zero, 0.45f, 0.9f, star, null, 0.12f, sprite: Sprites.Of("star"), spinV: 3);
                else if (age >= 0.5f) gemLanded.Add(p.Id);
                if (age >= 0 && frameDt > 0 && (t + p.Id * 0.37f) % 1.7f < frameDt)
                    Sparks.Spawn(V(p.X, gy + 0.3, p.Z), Vector3.Zero, 0.45f, 0.9f, star, null, 0.12f, sprite: Sprites.Of("star"), spinV: 3);
                break;
            }
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

    /// <summary>(bd-ui2) The calling of the battle being drawn (set by Pickups), so a drop can tell whether it is a gift.</summary>
    string? lootCalling;

    /// <summary>The school of the skill a Legendary on the ground grants that her calling is not taught (a gift), else null.</summary>
    Color? GiftSchool(Pickup p) =>
        lootCalling is { } c && p.Payload is Rpg.ItemInstance it && Rpg.Drops.GiftSkill(it, c) is { } sk && Content.Weapons.All.TryGetValue(sk, out var wd)
            ? Ui.ItemViews.SchoolColors[wd.School] : null;

    static readonly Color GiftCore = Hdr("#fff4d6", 2.4f), GiftSheath = new("#FFF4D6");
    sealed class GiftRig { public required SwapRingRig Ring; public required StarQuad Star; public required OmniLight3D Lamp; public long Frame; public float Acc; }
    readonly Dictionary<int, GiftRig> giftRigs = new();

    /// <summary>Per frame: hides the gift rigs not drawn last frame (a gift taken or gone), and runs the swap rings.</summary>
    void GiftSweep()
    {
        SwapTick();
        long now = (long)Engine.GetProcessFrames();
        List<int>? gone = null;
        foreach (var (id, r) in giftRigs) if (now - r.Frame > 2) (gone ??= new()).Add(id);
        if (gone != null) foreach (var id in gone) { var r = giftRigs[id]; r.Ring.M.QueueFree(); r.Star.M.QueueFree(); r.Lamp.QueueFree(); giftRigs.Remove(id); }
    }

    /// <summary>(bd-ui2) A gift's light, on top of the Legendary's pillar: white-gold, never the school's color, so it reads on any ground.
    /// ONE gradient ring (a 3 px rim with an 8 px glow, an interior at most 10%) pulsing 0.7 to 0.9 m and 0.8 to 0.2 alpha every 1.6 s; a warm
    /// light (2.5 m, no shadows) so the grass reads lit; a white-gold sheath 2.2x the amber core's width at 35% alpha, shimmering up on a 0.6 s
    /// period (shorter than the pillar, which runs off the screen); a crisp 48 px four-point star at the foot that stays (2.5 px arms, a 6 px white
    /// core), turning 15 degrees a second and twinkling every 0.8 s; and 14 round motes (3.5 px) rising 1.5 m over 1.2 s, staggered.</summary>
    void GiftLook(Pickup p, float gy, float t, float age, Color school)
    {
        if (age >= StrikeLife)
        {
            float sh = 0.75f + 0.25f * Mathf.Sin(t * Mathf.Tau / 0.6f);
            Light(p.X, gy, p.Z, Lit.Shaft, 0, 1.1f, 4.5f, GiftSheath, 0.35f * sh);
        }
        if (age < 0 || frameDt <= 0) return;
        float poolIn = Mathf.Clamp((age - Arrive) / 0.25f, 0, 1);
        var g = V(p.X, Y(p.X, p.Z), p.Z);
        if (!giftRigs.TryGetValue(p.Id, out var rig))
        {
            var lamp = new OmniLight3D { LightColor = new Color("#FFE6B0"), LightEnergy = 0, OmniRange = 2.5f, ShadowEnabled = false, Visible = false };
            AddChild(lamp);
            var ring = RingNew(g, 3, 8, (new Color("#E8C987"), new Color("#FFF4D6")));
            ring.InPx = 0; ring.Inner = 0.08f;
            giftRigs[p.Id] = rig = new GiftRig { Ring = ring, Star = StarNew(new Color("#FFF4D6"), 5), Lamp = lamp };
        }
        rig.Frame = (long)Engine.GetProcessFrames();
        float k = ((t + p.Id * 0.37f) % 1.6f) / 1.6f;
        rig.Ring.At = g;
        RingDraw(rig.Ring, Mathf.Lerp(0.7f, 0.9f, k), (0.8f - 0.6f * k) * poolIn);
        rig.Lamp.Position = g + Vector3.Up * 0.5f;
        rig.Lamp.LightEnergy = 1.5f * poolIn;
        rig.Lamp.Visible = poolIn > 0.01f;
        rig.Star.M.Visible = poolIn >= 0.5f;
        if (poolIn < 0.5f) return;
        var at = V(p.X, gy + 0.3, p.Z);
        float ppm = PxPerM(g);
        // The star: always there, crisp at 48 px, turning 15 degrees a second; every 0.8 s it twinkles brighter for 0.2 s.
        float ph = (t + p.Id * 0.37f) % 0.8f;
        float tw = ph < 0.2f ? Mathf.Sin(ph / 0.2f * Mathf.Pi) : 0;
        StarSet(rig.Star, at, 48, 2.5f, 6, Mathf.DegToRad(15) * t, 1f + 0.5f * tw);
        // Motes: 14 alive at once, round 3.5 px dots (no stretch), 1.5 m up over 1.2 s, staggered.
        rig.Acc += frameDt * 14f / 1.2f;
        for (; rig.Acc >= 1; rig.Acc -= 1)
        {
            float a = R() * Mathf.Tau;
            Sparks.Spawn(at + new Vector3(Mathf.Cos(a) * 0.35f, 0, Mathf.Sin(a) * 0.35f), new Vector3(0, 1.25f, 0), 1.2f, 3.5f / ppm, GiftCore, null, 3.5f / ppm, sprite: -1);
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
            var at = V(p.X, gy + 1.0, p.Z);
            float near = new Vector2(at.X - PlayerPos.X, at.Z - PlayerPos.Z).Length();
            lamp.Position = at;
            lamp.LightColor = colour;
            // Held off her as every light is that is not hers (she is lit by her own moments).
            lamp.LightEnergy = 1.1f * flicker * stand * Mathf.Lerp(0.35f, 1, Mathf.SmoothStep(1, 3.5f, near));
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
