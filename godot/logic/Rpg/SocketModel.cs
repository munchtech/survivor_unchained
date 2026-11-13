using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Rpg;

/* bd-ui W11: the plain-C# side of the socket panel (src/Ui/ArtsScreen.cs draws it): colours by gem kind, the head note,
 * the chooser's list, the "more room" levels, a Union's halves. No Godot types, so godot/tests can check it. */

public static class SocketModel
{
    static readonly string[] Roman = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"];
    public static string RomanOf(int n) => n >= 0 && n < Roman.Length ? Roman[n] : n.ToString();

    /// <summary>A gem's colour as hex: takes any skill = clear, Shield first = sapphire, else garnet.</summary>
    public static string GemHex(SupportDef g) =>
        g.Fits.Count == 0 ? "#E6EEFF" : g.Fits[0].Equals("Shield", StringComparison.OrdinalIgnoreCase) ? "#3F7FD8" : "#C42B3A";

    /// <summary>The head's note: which ranks open the sockets while any is closed, else "both open".</summary>
    public static string Note(int rank)
    {
        var r = Supports.File.Sockets.Ranks;
        if (Supports.SocketsAt(rank) >= r.Count) return "both open";
        return $"rank {RomanOf(r[0])} opens the first, {RomanOf(r[1])} the second";
    }

    /// <summary>The rank line: her rank, and what gear adds on top.</summary>
    public static string RankLine(int baseRank, int total)
    {
        int plus = total - baseRank;
        return plus > 0 ? $"rank {RomanOf(total)} ({RomanOf(baseRank)}, and +{plus} from your gear)" : $"rank {RomanOf(total)}";
    }

    public sealed record Row(SupportDef Gem, int Owned, int Free, bool Here = false);

    /// <summary>The chooser for one socket: each owned gem that fits the skill, with copies owned and free (the copy in this
    /// socket counts as free: it can be set again), and how many owned copies do not fit.</summary>
    public static (List<Row> Rows, int DontFit) Chooser(SupportState s, string skill, int index)
    {
        var rows = new List<Row>();
        int dont = 0;
        string? here = s.Sockets.TryGetValue(skill, out var row) && index < row.Count ? row[index] : null;
        foreach (var g in Supports.All)
        {
            int owned = s.Owned.GetValueOrDefault(g.Id);
            if (owned <= 0) continue;
            if (!Supports.Fits(g, skill)) { dont += owned; continue; }
            int used = s.Sockets.Values.Sum(l => l.Count(x => x == g.Id));
            rows.Add(new Row(g, owned, Math.Max(0, owned - used), here == g.Id));
        }
        return (rows, dont);
    }

    public static string DontFitLine(int n, string skillName) => $"{n} of your gems {(n == 1 ? "doesn't" : "don't")} fit {skillName}.";

    static readonly string[] Ones = ["", "first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth",
        "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth"];
    public static string Ordinal(int n)
    {
        if (n < Ones.Length) return Ones[n];
        int t = n / 10, o = n % 10;
        string ten = t switch { 2 => "twent", 3 => "thirt", 4 => "fort", 5 => "fift", _ => "" };
        if (ten == "") return n + "th";
        return o == 0 ? ten + "ieth" : ten + "y-" + Ones[o];
    }

    /// <summary>The levels above hers where she gets room for one more skill.</summary>
    public static List<int> MoreRoom(int level, int upTo = 30)
    {
        var l = new List<int>();
        for (int x = Math.Max(2, level + 1); x <= upTo; x++) if (SkillBook.SlotsAt(x) > SkillBook.SlotsAt(x - 1)) l.Add(x);
        return l;
    }

    public static string MoreRoomLine(int level)
    {
        var l = MoreRoom(level);
        if (l.Count == 0) return "";
        var w = l.Select(x => "the " + Ordinal(x)).ToList();
        string list = w.Count == 1 ? w[0] : string.Join(", ", w.Take(w.Count - 1)) + " and " + w[^1];
        return $"More room comes at {list} level.";
    }

    /// <summary>The two halves of a Union (by its weapon's id), else null.</summary>
    public static (string A, string B)? Halves(string weaponId) =>
        Unions.All.FirstOrDefault(u => u.Into == weaponId) is { } u ? (u.A, u.B) : null;
}
