using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The Lamps screen's rules of movement and of putting out (docs/design/LAMPS_SCREEN_BRIEF.md §9, §10), with no Godot
/// in them so the tests walk them: the left stick's step, LB/RB's ring of lamps to light, and the visit's session
/// (the lamps lit since the screen opened, which go out anywhere until it closes).
/// </summary>
public static class LampNav
{
    public const double RoadCone = 50 * Math.PI / 180, FreeCone = 35 * Math.PI / 180, FreeReach = 260;

    /// <summary>§10's left stick from lamp `from` toward a screen direction (radians, y down): the road neighbor whose
    /// direction lies nearest the stick's within ±50° (the nearer on a tie); with none, the nearest lamp in a ±35° cone
    /// within 260 board units (the angle off the stick weighed in, as LampBoardModel.Step); with none, -1 (a soft tick).</summary>
    public static int Stick(LampBoardModel m, int from, double angle, List<int>? scratch = null)
    {
        var n = m.Nodes[from];
        int best = -1;
        double bestOff = double.MaxValue, bestD = double.MaxValue;
        foreach (var j in n.Adj)
        {
            var o = m.Nodes[j];
            double off = Off(Math.Atan2(-(o.Y - n.Y), o.X - n.X), angle);
            if (off > RoadCone) continue;
            double d = Math.Sqrt((o.X - n.X) * (o.X - n.X) + (o.Y - n.Y) * (o.Y - n.Y));
            // within 4° the angles count as a tie: the nearer goes
            if (off < bestOff - 0.07 || (Math.Abs(off - bestOff) <= 0.07 && d < bestD)) { best = j; bestOff = off; bestD = d; }
        }
        if (best >= 0) return best;
        scratch ??= new List<int>();
        m.Near(n.X, n.Y, FreeReach, scratch);
        double bestScore = double.MaxValue;
        foreach (var j in scratch)
        {
            if (j == from) continue;
            var o = m.Nodes[j];
            double dx = o.X - n.X, dy = o.Y - n.Y, d = Math.Sqrt(dx * dx + dy * dy);
            if (d > FreeReach || d < 1e-6) continue;
            double off = Off(Math.Atan2(-dy, dx), angle);
            if (off > FreeCone) continue;
            double sc = d * (1 + 1.5 * off);
            if (sc < bestScore) { bestScore = sc; best = j; }
        }
        return best;
    }

    static double Off(double a, double b) => Math.Abs(Math.IEEERemainder(a - b, 2 * Math.PI));

    /// <summary>LB/RB: the lamps she can light now, clockwise (on screen) round her hearth, starting at twelve o'clock;
    /// the next (dir +1) or previous (-1) after the focus's own angle. -1 when there are none.</summary>
    public static int Ring(LampBoardModel m, int hearth, IReadOnlyList<int> canLight, int focus, int dir)
    {
        if (canLight.Count == 0) return -1;
        var h = m.Nodes[hearth];
        // clockwise from twelve: the screen angle (y down) of each lamp about the hearth, 0 at the top
        double Clock(int i)
        {
            var o = m.Nodes[i];
            double a = Math.Atan2(o.X - h.X, o.Y - h.Y);        // board y up: 0 straight up, growing clockwise
            return a < 0 ? a + 2 * Math.PI : a;
        }
        var ring = canLight.Distinct().OrderBy(Clock).ThenBy(i => i).ToList();
        if (focus < 0) return dir > 0 ? ring[0] : ring[^1];
        int at = ring.IndexOf(focus);
        if (at >= 0) return ring[(at + (dir > 0 ? 1 : ring.Count - 1)) % ring.Count];
        double fa = focus == hearth ? -1 : Clock(focus);
        if (dir > 0) return ring.FirstOrDefault(i => Clock(i) > fa, ring[0]);
        return ring.LastOrDefault(i => Clock(i) < fa, ring[^1]);
    }
}

/// <summary>Why a lamp won't go out from the board (None: it can).</summary>
public enum OutNo { None, Night, Unlit, Free, Place, Holds }

/// <summary>
/// One visit to the Lamps screen (§9's session undo; Classes confirmed it needs nothing of theirs): the lamps lit since
/// it opened, in lighting order. Those go out anywhere until it closes (only the place check is skipped; LampBook's
/// own rule that what stays lit must hang together still holds, so the newest go first, or a later lamp keeps an earlier
/// one). The Flare carried at the open is kept: putting a lamp out resets the Flare to the road's Strike when it is
/// no longer learned, and lighting it again within the visit gives it back.
/// </summary>
public sealed class LampSession
{
    readonly CharacterData ch;
    public readonly int Layout;
    public string Flare { get; private set; }
    readonly List<string> litHere = new();
    public IReadOnlyList<string> LitHere => litHere;

    public LampSession(CharacterData ch)
    {
        this.ch = ch;
        Layout = LampBook.State(ch).Active;
        Flare = LampBook.Now(ch).Flare;
    }

    public bool IsNew(string id) => litHere.Contains(id);

    /// <summary>Light one lamp (LampBook.Light) and keep it in the visit.</summary>
    public bool Light(WorldState? w, string id)
    {
        if (!LampBook.Light(ch, w, id)) return false;
        litHere.Add(id);
        KeepFlare();
        return true;
    }

    /// <summary>Light my way (LampBook.LightMyWay, SU-047): the lamps lit, in order, kept in the visit; and the held points burned.</summary>
    public (List<string> Lit, int Burned) LightMyWay(WorldState? w)
    {
        var got = LampBook.LightMyWay(ch, w);
        litHere.AddRange(got.Lit);
        KeepFlare();
        return got;
    }

    /// <summary>Carry a learned Flare (LampBook.Carry, SU-049); the visit keeps it from now on.</summary>
    public bool Carry(string flare)
    {
        if (!LampBook.Carry(ch, flare)) return false;
        Flare = flare;
        return true;
    }

    /// <summary>Light a far lamp's whole path or nothing (LampAsk.LightPath); the lamps lit, in order, else null.</summary>
    public List<string>? LightPath(WorldState? w, string id)
    {
        var before = LampBook.Now(ch).Lit.ToHashSet();
        if (!LampAsk.LightPath(ch, w, id)) return null;
        var got = LampBook.Now(ch).Lit.Where(x => !before.Contains(x)).ToList();
        litHere.AddRange(got);
        KeepFlare();
        return got;
    }

    /// <summary>Can this lamp go out here (atPost: not by night, where LampBook.LayoutsOpen), and if so, the lamps that go with it,
    /// tips first and it last (a lamp others hang on takes its branch).</summary>
    public OutNo CanOut(string id, bool night, bool atPost, out List<string> order)
    {
        order = new();
        if (night) return OutNo.Night;
        var l = LampBook.Now(ch);
        if (!l.Lit.Contains(id)) return OutNo.Unlit;
        if (LampBook.Free(ch).Contains(id)) return OutNo.Free;
        if (Branch(ch, id) is not { } br) return OutNo.Holds;
        // away from a lamp-post only the visit's own lamps go out, one at a time: a later one hanging on it blocks it
        if (!atPost && !litHere.Contains(id)) return OutNo.Place;
        if (!atPost && br.Count > 1) return OutNo.Holds;
        order = br;
        return OutNo.None;
    }

    /// <summary>Put out what CanOut allowed, in its order. False (and nothing changed) if any step refuses.</summary>
    public bool PutOut(IReadOnlyList<string> order)
    {
        var l = LampBook.Now(ch);
        var keep = l.Lit.ToList();
        var flare = l.Flare;
        foreach (var x in order)
            if (!LampBook.Unlight(ch, x)) { l.Lit.Clear(); l.Lit.AddRange(keep); l.Flare = flare; return false; }
        foreach (var x in order) litHere.Remove(x);
        KeepFlare();
        return true;
    }

    /// <summary>Undo the newest lamp of the visit (null when there is none, or the newest can't go out).</summary>
    public string? UndoNewest()
    {
        if (litHere.Count == 0) return null;
        var id = litHere[^1];
        return CanOut(id, false, false, out var o) == OutNo.None && PutOut(o) ? id : null;
    }

    void KeepFlare()
    {
        var l = LampBook.Now(ch);
        if (l.Flare != Flare && LampBook.Learned(ch).Contains(Flare)) l.Flare = Flare;
    }

    /// <summary>The lamps that go out with `id` (it and every lit lamp that would no longer hang from the hearth or meet
    /// its gate), tips first and `id` last; null when that takes a free lamp or LampBook refuses some step.</summary>
    public static List<string>? Branch(CharacterData ch, string id)
    {
        var l = LampBook.Now(ch);
        var free = LampBook.Free(ch);
        if (free.Contains(id) || !l.Lit.Contains(id)) return null;
        // what stays: reached from the free lamps without it, gates met, to a fixed point
        var stay = l.Lit.Where(x => x != id).ToHashSet();
        while (true)
        {
            var seen = new HashSet<string>(free.Where(stay.Contains));
            var q = new Queue<string>(seen);
            while (q.Count > 0) foreach (var nx in Lamps.Next(q.Dequeue())) if (stay.Contains(nx) && seen.Add(nx)) q.Enqueue(nx);
            var depth = new Dictionary<string, int>();
            foreach (var x in seen) if (Lamps.Find(x)?.Road is { } r) depth[r] = depth.GetValueOrDefault(r) + 1;
            seen.RemoveWhere(x => !free.Contains(x) && Lamps.Find(x) is { Road: { } r } d && depth.GetValueOrDefault(r) < d.Gate
                && !(Lamps.V2 && d.Calling != null && d.Calling != ch.Archetype));
            if (seen.Count == stay.Count) break;
            stay = seen;
        }
        var go = l.Lit.Where(x => !stay.Contains(x)).ToHashSet();
        if (go.Any(free.Contains)) return null;
        // tips first: try them out for real, the farthest from the hearth that LampBook lets go, then put all back
        var keep = l.Lit.ToList();
        var flare = l.Flare;
        var order = new List<string>();
        try
        {
            while (go.Count > 0)
            {
                var far = Steps(free, l.Lit);
                var next = go.Where(x => LampBook.CanUnlight(ch, x) == LampNo.None)
                    .OrderByDescending(x => far.GetValueOrDefault(x)).ThenBy(x => x == id ? 1 : 0).ThenBy(x => x, StringComparer.Ordinal)
                    .FirstOrDefault();
                if (next == null || !LampBook.Unlight(ch, next)) return null;
                order.Add(next);
                go.Remove(next);
            }
        }
        finally { l.Lit.Clear(); l.Lit.AddRange(keep); l.Flare = flare; }
        // `id` goes last when it can (it is the branch's root); LampBook's order stands otherwise
        return order;
    }

    static Dictionary<string, int> Steps(HashSet<string> free, List<string> lit)
    {
        var set = lit.ToHashSet();
        var d = new Dictionary<string, int>();
        var q = new Queue<string>();
        foreach (var f in free) if (set.Contains(f)) { d[f] = 0; q.Enqueue(f); }
        while (q.Count > 0)
        {
            var a = q.Dequeue();
            foreach (var b in Lamps.Next(a)) if (set.Contains(b) && !d.ContainsKey(b)) { d[b] = d[a] + 1; q.Enqueue(b); }
        }
        return d;
    }
}
