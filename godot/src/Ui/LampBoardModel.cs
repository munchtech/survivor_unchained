using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;

namespace SurvivorUnchained.Ui;

/* The Lamps board's geometry, plain C# (no Godot types) so godot/tests can check it (docs/design/LAMPS_SCREEN_BRIEF.md
 * §5, §13, §16; the mock tools/uiforge/lamps_mock/mock/ is the visual spec). Board units are lamps_v2.json's (y up);
 * screen px are y down. LampBoard.cs draws it. Ids, kinds and positions are read, never written. */

/// <summary>A screen rect in px.</summary>
public readonly record struct Box(double X0, double Y0, double X1, double Y1)
{
    public double W => X1 - X0;
    public double H => Y1 - Y0;
    public bool Overlaps(Box o) => X0 < o.X1 && o.X0 < X1 && Y0 < o.Y1 && o.Y0 < Y1;
    public bool Inside(Box o) => X0 >= o.X0 && X1 <= o.X1 && Y0 >= o.Y0 && Y1 <= o.Y1;
    public Box Grow(double d) => new(X0 - d, Y0 - d, X1 + d, Y1 + d);
    /// <summary>Does a disc touch it?</summary>
    public bool Hits(double x, double y, double r)
    {
        double cx = Math.Clamp(x, X0, X1), cy = Math.Clamp(y, Y0, Y1);
        return (x - cx) * (x - cx) + (y - cy) * (y - cy) < r * r;
    }
}

/// <summary>Board units to screen px: the view's center (board units), px per unit, and the screen point it lands on.</summary>
public readonly record struct BoardView(double Cx, double Cy, double S, double Sx, double Sy)
{
    public (double X, double Y) Project(double x, double y) => (Sx + (x - Cx) * S, Sy - (y - Cy) * S);
    public (double X, double Y) Unproject(double px, double py) => (Cx + (px - Sx) / S, Cy - (py - Sy) / S);
}

public enum BoardStop { Valley, Road, Lamp }

public sealed class LampBoardModel
{
    /* --------------------------------------------------------------------- the board -- */

    public sealed class Node
    {
        public int I;
        public string Id = "", Kind = "", Group = "", Region = "";
        public string? Calling, Road;
        public double X, Y;
        public int Gate;
        public int[] Adj = [];
        /// <summary>The pad's neighbors (road neighbors and the nearest lamps around), nearest first.</summary>
        public int[] Pad = [];
        public double[] PadAngle = [];
    }

    public sealed record Group(string Id, string Kind, string Name, string[] Callings);

    public readonly Node[] Nodes;
    public readonly (int A, int B)[] Edges;
    public readonly Dictionary<string, int> Index;
    public readonly Dictionary<string, Group> Groups;

    public const double Cell = 64;
    readonly Dictionary<long, List<int>> grid = new();
    static long Key(int cx, int cy) => ((long)cx << 32) ^ (uint)cy;

    /// <summary>Read the board from lamps_v2.json's text (lamps and groups; nothing else).</summary>
    public static LampBoardModel FromJson(string json)
    {
        using var doc = JsonDocument.Parse(json, new JsonDocumentOptions { CommentHandling = JsonCommentHandling.Skip, AllowTrailingCommas = true });
        var root = doc.RootElement;
        var groups = new List<Group>();
        if (root.TryGetProperty("groups", out var gs))
            foreach (var g in gs.EnumerateArray())
                groups.Add(new Group(g.GetProperty("id").GetString()!, g.GetProperty("kind").GetString()!,
                    g.TryGetProperty("name", out var n) ? n.GetString() ?? "" : "",
                    g.TryGetProperty("callings", out var c) ? c.EnumerateArray().Select(x => x.GetString()!).ToArray() : []));
        var nodes = new List<Node>();
        var at = new List<string[]>();
        foreach (var l in root.GetProperty("lamps").EnumerateArray())
        {
            string? S(string k) => l.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
            nodes.Add(new Node
            {
                Id = S("id")!, Kind = S("kind")!, Group = S("group") ?? "", Region = S("region") ?? "", Calling = S("calling"), Road = S("road"),
                X = l.GetProperty("x").GetDouble(), Y = l.GetProperty("y").GetDouble(),
                Gate = l.TryGetProperty("gate", out var gt) && gt.ValueKind == JsonValueKind.Number ? gt.GetInt32() : 0,
            });
            at.Add(l.TryGetProperty("at", out var a) ? a.EnumerateArray().Select(x => x.GetString()!).ToArray() : []);
        }
        return new LampBoardModel(nodes, at, groups);
    }

    LampBoardModel(List<Node> nodes, List<string[]> at, List<Group> groups)
    {
        Nodes = nodes.ToArray();
        for (int i = 0; i < Nodes.Length; i++) Nodes[i].I = i;
        Index = Nodes.ToDictionary(n => n.Id, n => n.I);
        Groups = groups.ToDictionary(g => g.Id);
        var adj = Nodes.Select(_ => new List<int>()).ToArray();
        var edges = new List<(int, int)>();
        for (int i = 0; i < Nodes.Length; i++)
            foreach (var a in at[i])
                if (Index.TryGetValue(a, out var j) && !adj[i].Contains(j))
                {
                    adj[i].Add(j); adj[j].Add(i);
                    edges.Add((j, i));
                }
        Edges = edges.ToArray();
        for (int i = 0; i < Nodes.Length; i++) Nodes[i].Adj = adj[i].ToArray();
        foreach (var n in Nodes)
        {
            var k = Key((int)Math.Floor(n.X / Cell), (int)Math.Floor(n.Y / Cell));
            if (!grid.TryGetValue(k, out var list)) grid[k] = list = new();
            list.Add(n.I);
        }
        BuildPad();
    }

    /* ------------------------------------------------------------- the pad's moves -- */

    /// <summary>Each lamp's pad neighbors: its road neighbors and the 8 nearest lamps within 260 units, nearest first,
    /// with their screen angles (radians, y down: 0 right, +pi/2 down).</summary>
    void BuildPad()
    {
        foreach (var n in Nodes)
        {
            var set = new HashSet<int>(n.Adj);
            foreach (var j in Near(n.X, n.Y, 260).OrderBy(j => D2(n, Nodes[j])).Where(j => j != n.I).Take(8)) set.Add(j);
            n.Pad = set.OrderBy(j => D2(n, Nodes[j])).ToArray();
            n.PadAngle = n.Pad.Select(j => Math.Atan2(-(Nodes[j].Y - n.Y), Nodes[j].X - n.X)).ToArray();
        }
    }

    static double D2(Node a, Node b) => (a.X - b.X) * (a.X - b.X) + (a.Y - b.Y) * (a.Y - b.Y);

    /// <summary>The pad's next lamp from one toward a screen direction (radians, y down), within a cone (default ±50°):
    /// the nearest, with the angle off the stick weighed in. -1 when none lies that way.</summary>
    public int Step(int from, double angle, double cone = 50 * Math.PI / 180)
    {
        var n = Nodes[from];
        int best = -1;
        double bestScore = double.MaxValue;
        for (int k = 0; k < n.Pad.Length; k++)
        {
            double off = Math.Abs(Math.IEEERemainder(n.PadAngle[k] - angle, 2 * Math.PI));
            if (off > cone) continue;
            double sc = Math.Sqrt(D2(n, Nodes[n.Pad[k]])) * (1 + 1.5 * off);
            if (sc < bestScore) { bestScore = sc; best = n.Pad[k]; }
        }
        return best;
    }

    /* ------------------------------------------------------------- hit testing -- */

    /// <summary>The lamps whose 64-unit cells lie within r units of a point (no allocation: fills the list given).</summary>
    public void Near(double x, double y, double r, List<int> into)
    {
        into.Clear();
        int x0 = (int)Math.Floor((x - r) / Cell), x1 = (int)Math.Floor((x + r) / Cell);
        int y0 = (int)Math.Floor((y - r) / Cell), y1 = (int)Math.Floor((y + r) / Cell);
        for (int cx = x0; cx <= x1; cx++)
            for (int cy = y0; cy <= y1; cy++)
                if (grid.TryGetValue(Key(cx, cy), out var list)) into.AddRange(list);
    }

    List<int> Near(double x, double y, double r) { var l = new List<int>(); Near(x, y, r, l); return l; }

    readonly List<int> hitScratch = new(64);

    /// <summary>The lamp under a board point: the nearest whose disc (rUnits[i]) holds it, else -1.</summary>
    public int Hit(double x, double y, Func<int, double> rUnits, double reach = 40)
    {
        Near(x, y, reach, hitScratch);
        int best = -1;
        double bd = double.MaxValue;
        foreach (var i in hitScratch)
        {
            var n = Nodes[i];
            double d = Math.Sqrt((n.X - x) * (n.X - x) + (n.Y - y) * (n.Y - y));
            if (d <= rUnits(i) && d < bd) { bd = d; best = i; }
        }
        return best;
    }

    /* ------------------------------------------------------------- stops and sizes -- */

    public const double RoadScale = 0.80, LampScale = 1.25, ValleyScaleA = 0.337;

    /// <summary>§5's lamp diameters at the Road stop (px at 1080); the link is 22 × 14.</summary>
    public static double RoadD(string kind) => kind switch
    {
        "start" => 34, "entry" => 24, "ultimate" => 26, "ultimateMod" => 12, "flareLamp" => 16, "blue" => 28, "notable" => 20,
        "rite" => 18, "link" => 22, "hand" => 18, "form" => 14, "reflex" => 16, "reflexUp" => 12, "small" => 12, "attribute" => 10,
        _ => 12,
    };

    /// <summary>§5's Valley dots.</summary>
    public static double ValleyD(string kind) => kind switch
    {
        "start" => 14, "blue" => 10, "entry" => 9, "ultimate" => 9, "notable" => 7, "link" => 7, "rite" => 6, _ => 4,
    };

    /// <summary>A lamp's diameter at a scale: the Valley's dots at or below the Valley scale, the Road's shapes at 0.80,
    /// ×1.3 at the Lamp stop's 1.25, continuous between.</summary>
    public static double Diameter(string kind, double s, double valleyS)
    {
        if (s <= valleyS) return ValleyD(kind);
        if (s <= RoadScale)
        {
            double t = (s - valleyS) / (RoadScale - valleyS);
            return ValleyD(kind) + (RoadD(kind) - ValleyD(kind)) * t;
        }
        double u = Math.Min((s - RoadScale) / (LampScale - RoadScale), 1.5);
        return RoadD(kind) * (1 + 0.3 * u);
    }

    /// <summary>The stop a scale reads as (labels, dots, marks): the nearest of the three.</summary>
    public static BoardStop StopOf(double s, double valleyS) =>
        s < (valleyS + RoadScale) / 2 ? BoardStop.Valley : s > (RoadScale + LampScale) / 2 ? BoardStop.Lamp : BoardStop.Road;

    /// <summary>The Valley's scale for a window: the whole board (its outer ring) inside the unfeathered field, ×0.9 (§16).</summary>
    public double ValleyScale(Box window, double feather)
    {
        double ext = Nodes.Max(n => Math.Sqrt(n.X * n.X + n.Y * n.Y)) + 20;
        return Math.Min(window.W - 2 * feather, window.H - 2 * feather) / (2 * ext) * 0.9;
    }

    /// <summary>§16 A4: the three faint guides' radii (units): the hearths', the roads' and the Old Roads' median distance.</summary>
    public double[] RingRadii()
    {
        double Med(IEnumerable<Node> ns)
        {
            var d = ns.Select(n => Math.Sqrt(n.X * n.X + n.Y * n.Y)).OrderBy(v => v).ToArray();
            return d.Length == 0 ? 0 : d[d.Length / 2];
        }
        bool Old(Node n) => Groups.TryGetValue(n.Group, out var g) && g.Kind == "oldroad";
        return [Med(Nodes.Where(n => !Old(n) && n.Region == "hearth")), Med(Nodes.Where(n => !Old(n) && n.Region == "road")), Med(Nodes.Where(Old))];
    }

    /* ------------------------------------------------------------- her reach -- */

    /// <summary>Road steps from the lit lamps (0 lit; int.MaxValue unreachable).</summary>
    public int[] Steps(IReadOnlyCollection<int> lit)
    {
        var st = Enumerable.Repeat(int.MaxValue, Nodes.Length).ToArray();
        var q = new Queue<int>();
        foreach (var i in lit) { st[i] = 0; q.Enqueue(i); }
        while (q.Count > 0)
        {
            var a = q.Dequeue();
            foreach (var b in Nodes[a].Adj)
                if (st[b] == int.MaxValue) { st[b] = st[a] + 1; q.Enqueue(b); }
        }
        return st;
    }

    /// <summary>§5: unlit lamps fade with road steps: within 3 100%, 4-8 65%, past 8 40%.</summary>
    public static double Fade(int steps) => steps <= 3 ? 1.0 : steps <= 8 ? 0.65 : 0.40;

    /// <summary>The cheapest unlit lamps to light, in order, to reach a target (one a lamp, gates as of now), and the lit
    /// lamp it leaves from; null when it can't be reached.</summary>
    public (List<int> Path, int From)? PathTo(ISet<int> lit, Func<int, bool> gateOk, int target)
    {
        var dist = new Dictionary<int, int>();
        var prev = new Dictionary<int, int>();
        var q = new Queue<int>();
        foreach (var a in lit)
            foreach (var b in Nodes[a].Adj)
                if (!lit.Contains(b) && gateOk(b) && !dist.ContainsKey(b)) { dist[b] = 1; prev[b] = a; q.Enqueue(b); }
        while (q.Count > 0)
        {
            var a = q.Dequeue();
            if (a == target) break;
            foreach (var b in Nodes[a].Adj)
                if (!lit.Contains(b) && gateOk(b) && !dist.ContainsKey(b)) { dist[b] = dist[a] + 1; prev[b] = a; q.Enqueue(b); }
        }
        if (!dist.ContainsKey(target)) return null;
        var p = new List<int>();
        int c = target;
        while (!lit.Contains(c)) { p.Add(c); c = prev[c]; }
        p.Reverse();
        return (p, c);
    }

    /* ------------------------------------------------------------- centering -- */

    /// <summary>§16 centering on open: the lit lamps' bbox (and any extra, the focus's path) centered in the window, at
    /// most the Road scale, zoomed out until every one sits at least inset px inside the window's edge.</summary>
    public BoardView Center(IEnumerable<int> keep, Box window, double maxScale = RoadScale, double inset = 96)
    {
        var ids = keep.ToList();
        if (ids.Count == 0) ids.Add(0);
        double x0 = ids.Min(i => Nodes[i].X), x1 = ids.Max(i => Nodes[i].X), y0 = ids.Min(i => Nodes[i].Y), y1 = ids.Max(i => Nodes[i].Y);
        double rmax = ids.Max(i => RoadD(Nodes[i].Kind) * 1.1) / 2;
        double s = maxScale;
        if (x1 > x0) s = Math.Min(s, (window.W - 2 * inset - 2 * rmax) / (x1 - x0));
        if (y1 > y0) s = Math.Min(s, (window.H - 2 * inset - 2 * rmax) / (y1 - y0));
        return new BoardView((x0 + x1) / 2, (y0 + y1) / 2, Math.Max(s, 0.05), (window.X0 + window.X1) / 2, (window.Y0 + window.Y1) / 2);
    }

    /* ------------------------------------------------------------- labels -- */

    public sealed record LabelSpec(string Text, double Cx, double Cy, bool Hearth, int[] Lamps);
    /// <summary>A placed label; Lamps its group's lamps (it fades with their feather, and goes when none is in the window).</summary>
    public readonly record struct Placed(string Text, double X, double Y, Box Box, int[]? Lamps = null);

    /// <summary>The label text px at a stop (Cinzel 600; §5: 15, 16 at the Valley). Never under 13 (the build's check).</summary>
    public static int LabelPx(BoardStop stop) => stop == BoardStop.Valley ? 16 : 15;
    /// <summary>The gate numeral's px (Alegreya Sans 800).</summary>
    public const int ChipPx = 13;

    static readonly string[] Callings = ["warden", "reaver", "arcanist", "stalker"];

    public string GroupName(Group g) => g.Kind switch
    {
        "hearth" => $"THE {(g.Callings.FirstOrDefault() ?? "").ToUpperInvariant()}'S HEARTH",
        "ford" => "THE FORD",
        _ => g.Name.ToUpperInvariant(),
    };

    /// <summary>§5's labels by stop: the Valley names the 4 callings, the Ford and the 10 Old Roads; the Road and Lamp
    /// stops name hearths, roads, bridges, crossings and Old Roads.</summary>
    public List<LabelSpec> LabelSpecs(BoardStop stop)
    {
        var out_ = new List<LabelSpec>();
        LabelSpec Of(string text, IEnumerable<Node> ns, bool hearth = false)
        {
            var a = ns.ToArray();
            return new LabelSpec(text, a.Average(n => n.X), a.Average(n => n.Y), hearth, a.Select(n => n.I).ToArray());
        }
        if (stop == BoardStop.Valley)
        {
            foreach (var c in Callings)
            {
                var ns = Nodes.Where(n => n.Calling == c && n.Region is "hearth" or "road" or "bridge").ToList();
                if (ns.Count > 0) out_.Add(Of(c.ToUpperInvariant(), ns));
            }
            foreach (var g in Groups.Values.Where(g => g.Kind is "ford" or "oldroad"))
            {
                var ns = Nodes.Where(n => n.Group == g.Id).ToList();
                if (ns.Count > 0) out_.Add(Of(GroupName(g), ns));
            }
        }
        else
            foreach (var g in Groups.Values.Where(g => g.Kind is "hearth" or "road" or "bridge" or "crossing" or "oldroad"))
            {
                var ns = Nodes.Where(n => n.Group == g.Id).ToList();
                if (ns.Count > 0) out_.Add(Of(GroupName(g), ns, g.Kind == "hearth"));
            }
        return out_;
    }

    /// <summary>
    /// Each label beside its group's center, pushed outward from the Ford, clear of every lamp disc (screen x, y, r: the
    /// lamp's radius + 5), of every other label and of the blockers; its box (text + 6 px a side, cap height + 7 px a
    /// side) inside the allowed rect (the window less 40 px). width(text, px) is the text's advance with its tracking.
    /// Her own hearth goes first and sits above her lit hearth lamps, 10 px past the topmost (the mock's C_day: a title
    /// over the cluster, never under it across its roads), sliding sideways and up before it tries past them outward
    /// from the Ford, then beside its center, then wider. roads: extra discs no label may touch (her lit roads, sampled).
    /// The discs sit in a 32 px grid, so a candidate box checks only the discs near it (phase 1's Valley open spent
    /// 190-250 ms here).
    /// </summary>
    public List<Placed> PlaceLabels(BoardView v, BoardStop stop, IReadOnlyList<(double X, double Y, double R)> lamps, Box allowed,
        IReadOnlyList<Box> blockers, Func<string, int, double> width, ISet<int>? lit = null, IReadOnlyList<int>? lampOf = null,
        IReadOnlyList<(double X, double Y, double R)>? roads = null)
    {
        int px = LabelPx(stop);
        double h = Math.Round(px * 0.70);                  // Cinzel's cap height
        var placed = new List<Placed>();
        var grid = new DiscGrid(roads == null ? lamps : lamps.Concat(roads), 32);
        bool Free(Box b)
        {
            if (!b.Inside(allowed)) return false;
            foreach (var q in placed) if (b.Overlaps(q.Box)) return false;
            foreach (var q in blockers) if (b.Overlaps(q)) return false;
            return !grid.Any(b);
        }
        near ??= Sorted(-30, 190, 4, -64, 64, 4);
        var specs = LabelSpecs(stop);
        // her hearth first, so no road's name takes its place
        bool Her(LabelSpec sp) => sp.Hearth && lit != null && sp.Lamps.Any(lit.Contains);
        // lamps[k] is node lampOf[k] (the caller's visible discs); without lampOf, lamps[i] is node i
        Dictionary<int, int>? discOf = null;
        if (lampOf != null) { discOf = new(); for (int k = 0; k < lampOf.Count; k++) discOf[lampOf[k]] = k; }
        foreach (var sp in specs.Where(Her).Concat(specs.Where(sp => !Her(sp))))
        {
            double n = Math.Sqrt(sp.Cx * sp.Cx + sp.Cy * sp.Cy);
            double ux = n > 1e-6 ? sp.Cx / n : 0, uy = n > 1e-6 ? -sp.Cy / n : 0;
            var (X, Y) = v.Project(sp.Cx, sp.Cy);
            double w = width(sp.Text, px);
            if (X < allowed.X0 - w || X > allowed.X1 + w || Y < allowed.Y0 - 60 || Y > allowed.Y1 + 60) continue;
            Placed? best = null;
            var passes = new List<(double A0, List<(int A, int L)> C)>();
            if (Her(sp))
            {
                // above her lit hearth lamps: centered on them, its box's bottom 10 px over the topmost one's rim
                double sx = 0, top = double.MaxValue; int cnt = 0;
                foreach (var i in sp.Lamps)
                {
                    if (!lit!.Contains(i)) continue;
                    int k = discOf == null ? i : discOf.TryGetValue(i, out var kk) ? kk : -1;
                    if (k < 0 || k >= lamps.Count) continue;
                    sx += lamps[k].X; cnt++;
                    top = Math.Min(top, lamps[k].Y - lamps[k].R);
                }
                if (cnt > 0)
                {
                    double ax = sx / cnt, ay = top - 10 - 7 - h / 2;
                    above ??= Sorted(0, 160, 4, -200, 200, 8);
                    foreach (var (a, lat) in above)
                    {
                        double x = ax + lat, y = ay - a;
                        var b = new Box(x - w / 2 - 6, y - h / 2 - 7, x + w / 2 + 6, y + h / 2 + 7);
                        if (Free(b)) { best = new Placed(sp.Text, x, y, b, sp.Lamps); break; }
                    }
                    if (best is { } ab) { placed.Add(ab); continue; }
                }
                // past her lit lamps: the farthest lit disc along the outward axis (from the group's center), plus the
                // box's half depth along it and 10 px
                double reach = 0;
                foreach (var i in sp.Lamps)
                {
                    if (!lit!.Contains(i)) continue;
                    int k = discOf == null ? i : discOf.TryGetValue(i, out var kk) ? kk : -1;
                    if (k < 0 || k >= lamps.Count) continue;
                    var (lx, ly, r) = lamps[k];
                    reach = Math.Max(reach, (lx - X) * ux + (ly - Y) * uy + r);
                }
                double half = Math.Abs(ux) * (w / 2 + 6) + Math.Abs(uy) * (h / 2 + 7);
                past ??= Sorted(0, 160, 4, -160, 160, 4);
                passes.Add((reach + half + 10, past));
            }
            passes.Add((0, near));
            if (Her(sp)) passes.Add((0, wide ??= Sorted(-60, 320, 8, -200, 200, 8)));
            foreach (var (a0, cands) in passes)
            {
                foreach (var (a, lat) in cands)
                {
                    double x = X + ux * (a0 + a) - uy * lat, y = Y + uy * (a0 + a) + ux * lat;
                    var b = new Box(x - w / 2 - 6, y - h / 2 - 7, x + w / 2 + 6, y + h / 2 + 7);
                    if (Free(b)) { best = new Placed(sp.Text, x, y, b, sp.Lamps); break; }
                }
                if (best != null) break;
            }
            if (best is { } pl) placed.Add(pl);
        }
        return placed;
    }

    static List<(int A, int L)>? near, wide, past, above;
    static List<(int A, int L)> Sorted(int a0, int a1, int da, int l0, int l1, int dl)
    {
        var c = new List<(int A, int L)>();
        for (int a = a0; a <= a1; a += da) for (int l = l0; l <= l1; l += dl) c.Add((a, l));
        c.Sort((p, q) => Cost(p).CompareTo(Cost(q)));
        return c;
    }

    /// <summary>Discs in a uniform grid of screen px cells: how many touch a box?</summary>
    public sealed class DiscGrid
    {
        readonly double cell;
        readonly Dictionary<long, List<(double X, double Y, double R)>> cells = new();
        readonly double maxR;
        public DiscGrid(IEnumerable<(double X, double Y, double R)> discs, double cell)
        {
            this.cell = cell;
            foreach (var d in discs)
            {
                maxR = Math.Max(maxR, d.R);
                long k = Key((int)Math.Floor(d.X / cell), (int)Math.Floor(d.Y / cell));
                if (!cells.TryGetValue(k, out var l)) cells[k] = l = new();
                l.Add(d);
            }
        }
        static long Key(int cx, int cy) => ((long)cx << 32) ^ (uint)cy;
        public bool Any(Box b) => Count(b, 1) > 0;
        /// <summary>The discs touching b, skipping those skip says (stops counting at most).</summary>
        public int Count(Box b, int most = int.MaxValue, Func<(double X, double Y, double R), bool>? skip = null)
        {
            int n = 0;
            int x0 = (int)Math.Floor((b.X0 - maxR) / cell), x1 = (int)Math.Floor((b.X1 + maxR) / cell);
            int y0 = (int)Math.Floor((b.Y0 - maxR) / cell), y1 = (int)Math.Floor((b.Y1 + maxR) / cell);
            for (int cx = x0; cx <= x1; cx++)
                for (int cy = y0; cy <= y1; cy++)
                {
                    if (!cells.TryGetValue(Key(cx, cy), out var l)) continue;
                    foreach (var d in l)
                        if (b.Hits(d.X, d.Y, d.R) && (skip == null || !skip(d)) && ++n >= most) return n;
                }
            return n;
        }
    }

    /* ------------------------------------------------------------- the focus card -- */

    /// <summary>Where the card went: its rect, the side (right, left, above, below; "clamped" when nothing fit the
    /// window), the shift along that side and its overlap (0 is clean; each lamp or label crossing its edge band counts
    /// 1, each protected disc under the band 100).</summary>
    public readonly record struct CardSpot(Box Rect, string Side, int Shift, int Score);
    /// <summary>§16: a label keeps this many px from the card.</summary>
    public const double LabelRoom = 40;

    /// <summary>
    /// §16's card: right of the lamp, then left, above and below, each 22 px from the lamp's rim (r) and shifted in 8 px
    /// steps up to ±120 px. The first spot where no lamp disc crosses its edge band (the rect grown by 6 px), no label
    /// comes within 40 px, no protected disc (her lit lamps, the path preview's lamps and roads, the focus) touches the
    /// band, and the card stays `inset` px inside the window (the board's window: never over the header or the tabs). Else the
    /// least overlap; if nothing fits the window at all, the right spot clamped into it.
    /// </summary>
    public static CardSpot PlaceCard(double fx, double fy, double r, double w, double h,
        IReadOnlyList<(double X, double Y, double R)> lamps, IReadOnlyList<(double X, double Y, double R)> protect,
        IReadOnlyList<Box> labels, Box window, double inset = 16) =>
        PlaceCard(fx, fy, r, w, h, new DiscGrid(lamps, 32), new DiscGrid(protect, 32), labels, window, inset);

    /// <summary>The same on grids built once (the open's slide tries the window at many offsets over one board).
    /// cleanOnly: only a clean spot will do (each candidate stops at its first hit); none gives Score int.MaxValue.</summary>
    public static CardSpot PlaceCard(double fx, double fy, double r, double w, double h,
        DiscGrid lampGrid, DiscGrid protGrid, IReadOnlyList<Box> labels, Box window, double inset = 16, bool cleanOnly = false)
    {
        CardSpot? best = null;
        var shifts = new List<int> { 0 };
        for (int k = 8; k <= 120; k += 8) { shifts.Add(k); shifts.Add(-k); }
        var inner = window.Grow(-inset);
        foreach (var side in new[] { "right", "left", "above", "below" })
            foreach (var s in shifts)
            {
                double x0 = side switch { "right" => fx + r + 22, "left" => fx - r - 22 - w, _ => fx - w / 2 + s };
                double y0 = side switch { "above" => fy - r - 22 - h, "below" => fy + r + 22, _ => fy - h / 2 + s };
                x0 = Math.Round(x0); y0 = Math.Round(y0);
                var rect = new Box(x0, y0, x0 + w, y0 + h);
                if (!rect.Inside(inner)) continue;
                var band = rect.Grow(6);
                if (cleanOnly)
                {
                    if (protGrid.Any(band) || lampGrid.Count(band, 1, d => d.X - d.R >= rect.X0 && d.X + d.R <= rect.X1 && d.Y - d.R >= rect.Y0 && d.Y + d.R <= rect.Y1) > 0) continue;
                    var rm = rect.Grow(LabelRoom);
                    if (labels.Any(lb => lb.Overlaps(rm))) continue;
                    return new CardSpot(rect, side, s, 0);
                }
                // a disc wholly under the card is covered, not crossed (protect counts the ones that matter)
                int cross = lampGrid.Count(band, int.MaxValue,
                    d => d.X - d.R >= rect.X0 && d.X + d.R <= rect.X1 && d.Y - d.R >= rect.Y0 && d.Y + d.R <= rect.Y1);
                // labels keep 40 px from the card (the caller hides one it still crowds)
                var room = rect.Grow(LabelRoom);
                foreach (var lb in labels) if (lb.Overlaps(room)) cross++;
                int score = cross + 100 * protGrid.Count(band);
                if (score == 0) return new CardSpot(rect, side, s, 0);
                if (best is not { } b || score < b.Score) best = new CardSpot(rect, side, s, score);
            }
        if (cleanOnly) return new CardSpot(default, "none", 0, int.MaxValue);
        if (best is { } bb) return bb;
        double cx = Math.Clamp(fx + r + 22, inner.X0, Math.Max(inner.X0, inner.X1 - w));
        double cy = Math.Clamp(fy - h / 2, inner.Y0, Math.Max(inner.Y0, inner.Y1 - h));
        return new CardSpot(new Box(cx, cy, cx + w, cy + h), "clamped", 0, int.MaxValue);
    }

    static double Cost((int A, int L) q) => (q.A >= 0 ? q.A : -2.5 * q.A) + 1.4 * Math.Abs(q.L);
}
