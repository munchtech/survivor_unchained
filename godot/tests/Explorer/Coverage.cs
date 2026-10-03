using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Tests.Explorer;

/// <summary>What the explorer has reached, kind by kind ("node" rook.greet,
/// "fact" caravan.pell=fled, "entry" beasts/sample...), and the gates it
/// was shown on the way.</summary>
sealed class Coverage
{
    public readonly Dictionary<string, HashSet<string>> Reached = new();
    /// <summary>Choices and interactables shown refused: key, the reason given.</summary>
    public readonly Dictionary<string, string> Locked = new();
    /// <summary>Choices shown open at least once.</summary>
    public readonly HashSet<string> Open = new();
    readonly Dictionary<(string, Axis), double> best = new();

    public sealed record Need(string Npc, Axis Axis, string Op, double Value)
    {
        public bool Met(double v) => Op switch { ">=" => v >= Value, ">" => v > Value, "<=" => v <= Value, "<" => v < Value, _ => v == Value };
    }

    public sealed class Gate
    {
        public string Text = "";
        public List<Need> Needs = new();
        public bool Opened;
        public Node First = null!;
        public Step? Doing;
    }

    public readonly Dictionary<string, Gate> Gates = new();
    /// <summary>The items the choices just shown asked for and the survivor lacked.</summary>
    public HashSet<string>? Pending;
    /// <summary>Who is asking (the explorer's current state and step), for gates.</summary>
    public Func<(Node?, Step?)> Where = () => (null, null);

    public int Add(string kind, string key)
    {
        if (!Reached.TryGetValue(kind, out var set)) Reached[kind] = set = new();
        return set.Add(key) ? 1 : 0;
    }

    public HashSet<string> Of(string kind) => Reached.TryGetValue(kind, out var s) ? s : new();

    public double Best(string npc, Axis axis) => best.TryGetValue((npc, axis), out var v) ? v : 0;

    /// <summary>Everything a state holds, taken in: how much of it was new.</summary>
    public int Take(Node n, Journey j)
    {
        var w = j.World;
        int fresh = 0;
        foreach (var (id, s) in w.Npcs)
        {
            foreach (var node in s.Seen) fresh += Add("node", $"{id}.{node}");
            foreach (var axis in new[] { Axis.Trust, Axis.Affection, Axis.Respect, Axis.Fear })
                if (!best.TryGetValue((id, axis), out var b) || s[axis] > b) best[(id, axis)] = s[axis];
        }
        foreach (var (k, v) in w.Facts)
        {
            if (k.StartsWith("_") || k.StartsWith("scar.")) continue;
            fresh += Add("fact", k);
            if (v.Type is Fact.Kind.Str or Fact.Kind.Bool) fresh += Add("value", $"{k}={v}");
        }
        foreach (var (id, q) in w.Quests)
        {
            fresh += Add("status", $"{id}:{q.Status}");
            foreach (var e in q.Entries) fresh += Add("entry", $"{id}/{e}");
            if (q.Outcome != null) fresh += Add("outcome", $"{id}:{q.Outcome}");
        }
        foreach (var k in w.Knowledge.Concat(j.Ch.Knowledge)) fresh += Add("knows", k);
        foreach (var h in w.History) fresh += Add("history", h.Id);
        foreach (var t in j.Ch.Traits) fresh += Add("trait", t);
        foreach (var i in n.Held) fresh += Add("item", i);
        fresh += Add("day", $"{w.Day}{w.Time}");
        return fresh;
    }

    public void Lock(string key, string why) => Locked.TryAdd(key, why);

    /// <summary>A line on screen with its choices: the gates among them, and
    /// what the locked ones wanted.</summary>
    public void Offer(string where, Presented p, Journey j)
    {
        var list = p.Node.Choices ?? new();
        foreach (var c in p.Choices)
        {
            var key = $"{where}#{c.Index}";
            if (c.Enabled) Open.Add(key);
            var def = list[c.Index];
            var needs = new List<Need>();
            Needs(def.When, needs, false);
            if (needs.Count > 0)
            {
                if (!Gates.TryGetValue(key, out var g))
                {
                    var (node, step) = Where();
                    Gates[key] = g = new Gate { Text = c.Text, Needs = needs, First = node!, Doing = step };
                }
                g.Opened |= c.Enabled;
            }
            if (!c.Enabled) foreach (var item in Items(def.When)) if (Inventory.Count(j.Ch, item) == 0) (Pending ??= new()).Add(item);
        }
    }

    static void Needs(Cond? c, List<Need> into, bool negated)
    {
        if (c == null || negated) return;
        if (c.Rel is { } r && r.Axis is Axis.Respect or Axis.Affection)
        {
            if (r.Gte is { } a) into.Add(new(r.Npc, r.Axis, ">=", a));
            if (r.Gt is { } b) into.Add(new(r.Npc, r.Axis, ">", b));
        }
        foreach (var x in c.All ?? new()) Needs(x, into, negated);
        // Any of several is a gate only if all of them are; leave those be.
        Needs(c.Not, into, true);
    }

    static IEnumerable<string> Items(Cond? c)
    {
        if (c == null) yield break;
        if (c.HasItem != null) yield return c.HasItem;
        foreach (var x in c.All ?? new()) foreach (var i in Items(x)) yield return i;
    }

    public HashSet<string>? WantsAt(Node n, Journey j)
    {
        var w = Pending;
        Pending = null;
        return w;
    }
}
