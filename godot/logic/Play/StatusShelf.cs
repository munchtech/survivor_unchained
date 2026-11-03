using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Play;

/// <summary>UI 28: what is on her (buffs and debuffs) as the HUD's status shelf shows it, without Godot: each
/// status's timer as a fraction of the longest it has been since it last came on (the max seen, reset when its
/// time goes up), its place by priority (nearest the anchor first; within a class, first seen first), and the
/// overflow (at most Cap slots a side: past that, Cap - 1 and a "+N" slot).</summary>
public sealed class StatusShelf
{
    public const int Cap = 7;
    /// <summary>A time past this is permanent (a full ring, no drain).</summary>
    public const double Forever = 1e6;
    /// <summary>The last seconds, when the ring pulses.</summary>
    public const double PulseAt = 1.5;

    /// <summary>A status now: Key names it across frames (two of one glyph have two keys); Max, when over 0, is its
    /// starting duration given (a pin), else the shelf tracks the max seen.</summary>
    public readonly record struct Entry(string Key, string Glyph, bool Good, double Left, int Stacks = 0, double Max = 0);

    /// <summary>A slot as drawn. More > 0: the overflow's "+N" slot (no glyph).</summary>
    public readonly record struct Slot(string Key, string Glyph, bool Good, float Fraction, bool Pulse, bool Permanent, int Stacks, int More);

    readonly Dictionary<string, double> max = new();
    readonly Dictionary<string, double> last = new();
    readonly Dictionary<string, long> seen = new();
    long order;
    public readonly List<Slot> Buffs = new(), Debuffs = new();

    /// <summary>The priority class: nearest the anchor first. Debuffs: control (slow, stun, root, chill) 0, damage
    /// over time (burn, poison, bleed) 1, the rest 2. Buffs: the barrier 0, defensive 1, offensive 2, the world 3.</summary>
    public static int Rank(string glyph, bool good) => good
        ? glyph switch { "aegis" => 0, "shield" or "smoke" => 1, "hourglass" => 3, _ => 2 }
        : glyph switch { "boot" or "stun" or "root" or "chain" or "frost" => 0, "flame" or "plague" or "drop" or "blood" => 1, _ => 2 };

    readonly List<(Entry E, int Rank, long Seen)> sort = new();
    readonly HashSet<string> live = new();

    /// <summary>This frame's statuses into Buffs and Debuffs, each nearest the anchor first.</summary>
    public void Update(IReadOnlyList<Entry> now)
    {
        live.Clear();
        sort.Clear();
        foreach (var e in now)
        {
            if (!live.Add(e.Key)) continue;
            if (!seen.ContainsKey(e.Key)) seen[e.Key] = order++;
            // (refreshed, its time gone up since the last frame: a new start)
            bool up = !last.TryGetValue(e.Key, out var before) || e.Left > before + 1e-6;
            double m = e.Max > 0 ? e.Max : up || !max.TryGetValue(e.Key, out var was) ? e.Left : was;
            max[e.Key] = m;
            last[e.Key] = e.Left;
            sort.Add((e, Rank(e.Glyph, e.Good), seen[e.Key]));
        }
        // gone this frame: forgotten (on again later, it starts its ring full and takes a new place)
        if (seen.Count > live.Count)
            foreach (var k in new List<string>(seen.Keys))
                if (!live.Contains(k)) { seen.Remove(k); max.Remove(k); last.Remove(k); }
        sort.Sort((a, b) => a.Rank != b.Rank ? a.Rank.CompareTo(b.Rank) : a.Seen.CompareTo(b.Seen));
        Buffs.Clear();
        Debuffs.Clear();
        foreach (var (e, _, _) in sort)
        {
            bool forever = e.Left > Forever;
            double m = max[e.Key];
            float f = forever ? 1 : (float)Math.Clamp(m > 0 ? e.Left / m : 0, 0, 1);
            (e.Good ? Buffs : Debuffs).Add(new Slot(e.Key, e.Glyph, e.Good, f, !forever && e.Left <= PulseAt, forever, e.Stacks, 0));
        }
        Overflow(Buffs, true);
        Overflow(Debuffs, false);
    }

    static void Overflow(List<Slot> side, bool good)
    {
        if (side.Count <= Cap) return;
        int more = side.Count - (Cap - 1);
        side.RemoveRange(Cap - 1, side.Count - (Cap - 1));
        side.Add(new Slot(good ? "+b" : "+d", "", good, 1, false, true, 0, more));
    }

    /// <summary>The pin's statuses (HudPin status=): entries "b|d:glyph:left:max[:stacks]" joined by '+'.</summary>
    public static List<Entry> Parse(string spec)
    {
        var list = new List<Entry>();
        var inv = System.Globalization.CultureInfo.InvariantCulture;
        int i = 0;
        foreach (var raw in spec.Split('+', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            var p = raw.Split(':');
            if (p.Length < 4) continue;
            double.TryParse(p[2], System.Globalization.NumberStyles.Float, inv, out var left);
            double.TryParse(p[3], System.Globalization.NumberStyles.Float, inv, out var mx);
            int st = p.Length > 4 && int.TryParse(p[4], out var s) ? s : 0;
            list.Add(new Entry($"pin{i++}", p[1], p[0] == "b", left, st, mx));
        }
        return list;
    }
}
