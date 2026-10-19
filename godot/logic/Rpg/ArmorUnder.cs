using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Rpg;

/// <summary>What of a worn piece another slot's piece covers, left undrawn while that slot is filled (armor 4 r3, F5:
/// the plate top's shoulder strap came through the warden's pauldron in her heavy swing). A piece's row names, for each
/// covering slot, the points hidden under each known piece of it (by id) and under any other ("*": what all the known
/// ones cover), as files of bind positions (tools/armor/under.py). A triangle is dropped when all three of its points
/// are hidden, so the strap ends a few millimetres inside the pauldron's rim and draws whole when no pauldron is worn.</summary>
public static class ArmorUnder
{
    /// <summary>The files of points to hide on `row` for `look` (visual slot to piece id): one a covering slot that holds a
    /// piece other than `row` itself, that piece's own file or else the slot's "*".</summary>
    public static List<string> Files(ArmorPiece row, IReadOnlyDictionary<string, string> look)
    {
        var out_ = new List<string>();
        if (row.Under == null) return out_;
        foreach (var (slot, byPiece) in row.Under)
        {
            if (slot == row.Slot || !look.TryGetValue(slot, out var id) || string.IsNullOrEmpty(id) || id == row.Id) continue;
            if (byPiece.TryGetValue(id, out var f) || byPiece.TryGetValue("*", out f)) out_.Add(f);
        }
        return out_;
    }

    /// <summary>A bind position's key (glTF metres x 1e5, rounded), as the tuck records key her points.</summary>
    public static long Key(long x, long y, long z) => ((x + (1 << 20)) << 42) | ((y + (1 << 20)) << 21) | (z + (1 << 20));

    public static long Key(double x, double y, double z) => Key((long)Math.Round(x * 1e5), (long)Math.Round(y * 1e5), (long)Math.Round(z * 1e5));

    /// <summary>A file's keys: u32 count, then count x i32 x, y, z.</summary>
    public static HashSet<long> Read(byte[] b)
    {
        var s = new HashSet<long>();
        if (b.Length < 4) return s;
        int n = BitConverter.ToInt32(b, 0);
        for (int i = 0; i < n && 4 + i * 12 + 12 <= b.Length; i++)
        {
            int o = 4 + i * 12;
            s.Add(Key(BitConverter.ToInt32(b, o), BitConverter.ToInt32(b, o + 4), BitConverter.ToInt32(b, o + 8)));
        }
        return s;
    }

    /// <summary>The triangle list `index` (three a triangle) without the triangles whose three points' keys are all hidden;
    /// null when none is dropped.</summary>
    public static int[]? Keep(int[] index, long[] keys, HashSet<long> hidden)
    {
        if (hidden.Count == 0) return null;
        var kept = new List<int>(index.Length);
        for (int t = 0; t + 2 < index.Length; t += 3)
        {
            if (hidden.Contains(keys[index[t]]) && hidden.Contains(keys[index[t + 1]]) && hidden.Contains(keys[index[t + 2]])) continue;
            kept.Add(index[t]); kept.Add(index[t + 1]); kept.Add(index[t + 2]);
        }
        return kept.Count == index.Length ? null : kept.ToArray();
    }
}
