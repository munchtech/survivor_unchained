using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// The effects' sprites (Kenney's Particle Pack, CC0: art/fx/sprites.png, a
/// texture array of 256² layers, its groups in sprites.json): puffs of
/// smoke, crackling sparks, flares, stars and magic sigils, wisps and
/// tongues of flame, spattered dirt, twirls and slashes, rings, streaks.
/// A particle names its sprite by id (its layer + 1; 0 is none, a soft
/// round spot, which is also what other instanced batches drawn with the
/// same shaders get); these pick one of a kind at random.
/// </summary>
public static class Sprites
{
    static TextureLayered? array;
    static Dictionary<string, int[]>? groups;
    static readonly Random rng = new(23);

    public static TextureLayered Array => array ??= GD.Load<TextureLayered>("res://art/fx/sprites.png");

    sealed record Sheet(int Size, int Layers, Dictionary<string, int[]> Groups);

    static Dictionary<string, int[]> Groups => groups ??= Core.Json.Parse<Sheet>(FileAccess.GetFileAsString("res://art/fx/sprites.json")).Groups;

    /// <summary>A sprite of a kind (smoke, spark, flare, light, star, magic,
    /// flame, fire, dirt, twirl, slash, circle, symbol, trace, muzzle), by id.</summary>
    public static float Of(string kind)
    {
        var (first, count) = (Groups[kind][0], Groups[kind][1]);
        return first + rng.Next(count) + 1;
    }

    /// <summary>The first layer of a kind and how many there are.</summary>
    public static (int First, int Count) Range(string kind) => (Groups[kind][0], Groups[kind][1]);

    public static float Smoke() => Of("smoke");

    static Texture2D? puff;

    /// <summary>A billowing puff, whole, as a texture of its own (for the GPU
    /// particles' smoke, whose material takes one texture): smoke_07.</summary>
    public static Texture2D Puff => puff ??= GD.Load<Texture2D>("res://art/fx/puff.png");

    /// <summary>A circle of runes (magic_02, magic_03), and a spread of
    /// burning (fire_01), as textures of their own, for marks on the ground.</summary>
    public static Texture2D Runes(int which) => GD.Load<Texture2D>(which == 0 ? "res://art/fx/runes_a.png" : "res://art/fx/runes_b.png");
    public static Texture2D Burning => GD.Load<Texture2D>("res://art/fx/embers.png");
    /// <summary>The tongues of flame: the pack's muzzle flashes and its two fullest flames.</summary>
    public static float Tongue() => rng.Next(7) < 5 ? Of("muzzle") : Range("flame").First + 4 + rng.Next(2) + 1;
}
