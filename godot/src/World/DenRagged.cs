using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// (den r13, 16 Nov) The den's DRAWN wall line leaves the generator's capsule in the corridors. A hall is a straight
/// segment with a slowly wandering width (MapGen's ways), so both banks of a corridor ran as ruled lines down the frame:
/// the cards' foot, the wall mesh's foot and its crest all followed it. The view's wall field is pushed OUTWARD only, by a
/// seed-salted ragged field of ArMin..ArMax metres (alcoves and bulges), outside the rooms' circles; the walkable ground and
/// every collider are the sim's and do not change (the sim never reads WallField). The ground the alcoves bare, which she
/// cannot walk on, is dressed by DungeonDress (root spills, stones, bones) from Alcove().
/// --den-ragged: the largest push, metres (0 off); --den-ragged-min the smallest.
/// </summary>
public static class DenRagged
{
    public static readonly float ArMax = SurvivorUnchained.Args.Num("den-ragged", 2f);
    public static readonly float ArMin = SurvivorUnchained.Args.Num("den-ragged-min", 0.5f);
    static readonly float Wave = SurvivorUnchained.Args.Num("den-ragged-wave", 4.5f);   // metres, the alcoves' spacing

    static float Hash(int x, int y, int s)
    {
        uint h = (uint)(x * 374761393 + y * 668265263 + s * 2147483647);
        h = (h ^ (h >> 13)) * 1274126177u;
        return ((h ^ (h >> 16)) & 0xffffff) / (float)0x1000000;
    }
    static float Sm(float a, float b, float x) { float t = Mathf.Clamp((x - a) / (b - a), 0f, 1f); return t * t * (3 - 2 * t); }
    static float Vn(float x, float z, int s)
    {
        int i = Mathf.FloorToInt(x), j = Mathf.FloorToInt(z);
        float fx = x - i, fz = z - j;
        fx = fx * fx * (3 - 2 * fx); fz = fz * fz * (3 - 2 * fz);
        return Mathf.Lerp(Mathf.Lerp(Hash(i, j, s), Hash(i + 1, j, s), fx), Mathf.Lerp(Hash(i, j + 1, s), Hash(i + 1, j + 1, s), fx), fz);
    }

    /// <summary>The push at x, z before the corridor weight: ArMin..ArMax metres, ragged (two octaves, sharpened).</summary>
    public static float Push(float x, float z, int seed)
    {
        float n = 0.65f * Vn(x / Wave, z / Wave, seed * 7 + 1) + 0.35f * Vn(x / (Wave * 0.4f), z / (Wave * 0.4f), seed * 7 + 2);
        return Mathf.Lerp(ArMin, ArMax, Sm(0.3f, 0.7f, n));
    }

    /// <summary>0 in a room's circle (+1 m), 1 in the corridors (past R + 5 m of every room that is not a bend).</summary>
    public static float Corridor(float x, float z, List<(float X, float Z, float R, string Kind)> rooms)
    {
        float w = 1f;
        foreach (var r in rooms)
        {
            if (r.Kind == "Bend") continue;
            float d = new Vector2(x - r.X, z - r.Z).Length();
            w = Mathf.Min(w, Sm(r.R + 1f, r.R + 5f, d));
        }
        return w;
    }

    /// <summary>The drawn field from the walkable one: walk + push where it is the wall or its first 1.5 m in (deeper in,
    /// unchanged). Never less than walk: the drawn floor holds all of the walkable floor.</summary>
    public static float[] Drawn(float[] walk, int res, float half, float step, int seed, List<(float X, float Z, float R, string Kind)> rooms)
    {
        var o = (float[])walk.Clone();
        if (ArMax <= 0f) return o;
        for (int j = 0; j < res; j++)
            for (int i = 0; i < res; i++)
            {
                float w = walk[j * res + i];
                if (w > 1.5f) continue;
                float x = -half + i * step, z = -half + j * step;
                float k = Corridor(x, z, rooms);
                if (k <= 0f) continue;
                o[j * res + i] = w + k * Push(x, z, seed) * (1f - Sm(0f, 1.5f, w));
            }
        return o;
    }
}
