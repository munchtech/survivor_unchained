using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The Lamps board (docs/design/LAMPS_SCREEN_BRIEF.md §5, §6, §13, §16; the look is the mock's, tools/uiforge/lamps_mock):
/// drawn in its own rect (C's board window in the book's panel), feathered to nothing over 48 px on all four sides.
/// Three draw calls: the lamps (one MultiMesh of 574, every kind an SDF in shaders/ui_lamps_lamp.gdshader), the roads
/// (one MultiMesh of 591 anti-aliased lines) and the halos (one additive MultiMesh, lit lamps only, at most 90); under
/// them the page's warm glow and the Valley's guides (one rect); over them the labels and gate numerals (Labels).
/// Nothing is rebuilt per frame: the breathing and the running dashes are the shaders' TIME. Hover sets the focus.
/// Debug: --lamps-stop valley|road|lamp, --lamps-demo n (light n of Light my way's lamps on open), --lamps-focus id,
/// --lamps-measure (draw calls, CPU and allocation, printed as "LAMPBOARD").
/// </summary>
public partial class LampBoard : Control
{
    public const float Feather = 48;
    const int MaxHalos = 90;

    static LampBoardModel? model;
    public static LampBoardModel M => model ??= LampBoardModel.FromJson(SurvivorUnchained.Core.Json.ReadContent("lamps_v2.json"));

    static readonly StringName PWin = "win", PFeather = "feather", PValley = "valley", PFind = "find_on", PPalm = "palm",
        PSize = "size", PGlowC = "glow_c", PGlowR = "glow_r", PRingC = "ring_c", PRings = "rings";

    readonly CharacterData ch;
    readonly WorldState? w;
    readonly MultiMeshInstance2D roads = new(), halos = new(), lamps = new();
    readonly ColorRect page = new() { MouseFilter = MouseFilterEnum.Ignore, Color = Colors.White };
    readonly ShaderMaterial lampMat, roadMat, haloMat, pageMat;
    readonly BoardInk ink = new();
    readonly LampCard card = new();
    /// <summary>The page sets this off while the wick is open (§16: no card over the board then).</summary>
    public bool CardOn = true;
    /// <summary>The focus moved (-1: none).</summary>
    public event Action<int>? FocusChanged;
    Func<int, bool> gateOk = _ => true;
    List<int> path = new();
    int pathFrom = -1;
    List<LampBoardModel.Placed> placedLabels = new();
    /// <summary>The card's rect grown by 40 px: a label it still crowds is hidden (§16).</summary>
    Box? crowd;
    /// <summary>Where the card went last (for the shots' report).</summary>
    public LampBoardModel.CardSpot? CardSpot { get; private set; }

    // the board's state, as of the last Rebuild
    int n;
    int[] state = [], steps = [], slot = [];
    bool[] dim = [], onPath = [], notch = [], gateNotch = [];
    float[] radius = [], fade = [];
    (double X, double Y)[] pos = [];
    readonly HashSet<int> lit = new();
    int focus = -1, fixedFocus = -1;
    BoardView view;
    double valleyS;
    BoardStop stop;
    Vector2 builtSize;
    Rect2 winPx;

    public BoardStop Stop => stop;
    public BoardView View => view;
    public int Focus => focus;

    public LampBoard(CharacterData ch, WorldState? w)
    {
        this.ch = ch;
        this.w = w;
        MouseFilter = MouseFilterEnum.Pass;
        ClipContents = true;
        lampMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ui_lamps_lamp.gdshader") };
        roadMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ui_lamps_road.gdshader") };
        haloMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ui_lamps_halo.gdshader") };
        pageMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ui_lamps_page.gdshader") };
        if (ResourceLoader.Exists("res://art/ui/icons/glyph_color/palm.png")) lampMat.SetShaderParameter(PPalm, GD.Load<Texture2D>("res://art/ui/icons/glyph_color/palm.png"));
        page.Material = pageMat;
        AddChild(page);
        foreach (var (mmi, mat, count, centered) in new[] { (roads, roadMat, M.Edges.Length, false), (halos, haloMat, MaxHalos, true), (lamps, lampMat, M.Nodes.Length, true) })
        {
            mmi.Material = mat;
            mmi.Multimesh = new MultiMesh
            {
                TransformFormat = MultiMesh.TransformFormatEnum.Transform2D, UseColors = true, UseCustomData = true,
                Mesh = Quad(centered), InstanceCount = count, VisibleInstanceCount = 0,
            };
            AddChild(mmi);
        }
        AddChild(ink);
        AddChild(card);
        Resized += () => { if (Size.X > 8 && Size != builtSize) Rebuild(); };
    }

    /// <summary>A unit quad: centered (-0.5..0.5) for lamps and halos, from 0 to 1 along x for roads.</summary>
    static ArrayMesh Quad(bool centered)
    {
        float x0 = centered ? -0.5f : 0, x1 = centered ? 0.5f : 1;
        var arr = new Godot.Collections.Array();
        arr.Resize((int)Mesh.ArrayType.Max);
        arr[(int)Mesh.ArrayType.Vertex] = new Vector2[] { new(x0, -0.5f), new(x1, -0.5f), new(x1, 0.5f), new(x0, 0.5f) };
        arr[(int)Mesh.ArrayType.TexUV] = new Vector2[] { new(0, 0), new(1, 0), new(1, 1), new(0, 1) };
        arr[(int)Mesh.ArrayType.Index] = new int[] { 0, 1, 2, 0, 2, 3 };
        var m = new ArrayMesh();
        m.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        return m;
    }

    /* ------------------------------------------------------------- debug: a plausible build -- */

    static bool demoDone;

    static readonly string[] MockLit =
    [
        "warden.the_wardens_oath", "warden.hearth.p2", "sunderer.two_hands", "sunderer.s1", "sunderer.s2", "sunderer.s3",
        "sunderer.s4", "sunderer.the_long_cut", "sunderer.the_long_cut.second_cut", "sunderer.rite1",
        "sunderer.breaking_point", "warden.iron_hide", "warden.shield_bash", "warden.concussion", "warden.hand1",
    ];

    /// <summary>--lamps-demo n: light n of Light my way's lamps (raising her level if she runs out), once a run.</summary>
    public static void Demo(CharacterData ch, WorldState? w)
    {
        if (demoDone || SurvivorUnchained.Args.Get("lamps-demo") is not { } s || !int.TryParse(s, out var want)) return;
        demoDone = true;
        int got = 0, guard = 0;
        // a warden lights the mock's own build first (tools/uiforge/lamps_mock/mock/state.py LIT: her hearth, the
        // Sunderer's road to Breaking Point), so the frames compare with C_day and C_night lamp for lamp
        if (ch.Archetype == "warden")
            for (int pass = 0; pass < 4; pass++)
                foreach (var id in MockLit)
                {
                    if (LampBook.Now(ch).Lit.Contains(id)) continue;
                    for (int k = 0; k < 40 && LampBook.Spare(ch, w) <= 0; k++) ch.Level++;
                    if (LampBook.Light(ch, w, id)) got++;
                }
        while (LampBook.Now(ch).Lit.Count < want && guard++ < want * 4)
        {
            if (LampBook.Spare(ch, w) <= 0) { ch.Level++; continue; }
            if (LampBook.Suggest(ch, w) is not { } id || !LampBook.Light(ch, w, id)) break;
            got++;
        }
        // and leave her 3 to light, as the mock's frames do ("3 LAMPS TO LIGHT")
        for (int k = 0; k < 40 && LampBook.Spare(ch, w) < 3; k++) ch.Level++;
        // and carry the mock's five (the wick tabs as C_day's): the warden's first five where her calling can't carry one
        var five = new List<string>();
        foreach (var id in new[] { "sunder", "oathblade", "rebuke", "groundbreaker", "watch_bell" })
            if (Weapons.All.ContainsKey(id) && SkillBook.Carries(ch, id)) five.Add(id);
        foreach (var (id, _) in Weapons.All.Where(kv => kv.Value.Findable && SkillBook.Carries(ch, kv.Key)).OrderBy(kv => kv.Key, StringComparer.Ordinal))
            if (five.Count < 5 && !five.Contains(id)) five.Add(id);
        foreach (var id in five)
        {
            if (!ch.Skills.Contains(id)) ch.Skills.Add(id);
            var at = SkillBook.Attribute(id);
            if (SkillBook.Have(ch, at) < SkillBook.Need)
                switch (at)
                {
                    case "Might": ch.Attributes.Might = SkillBook.Need; break;
                    case "Finesse": ch.Attributes.Finesse = SkillBook.Need; break;
                    case "Wits": ch.Attributes.Wits = SkillBook.Need; break;
                    default: ch.Attributes.Resolve = SkillBook.Need; break;
                }
        }
        ch.Slotted.RemoveAll(five.Contains);
        ch.Slotted.InsertRange(0, five);
        GD.Print($"LAMPBOARD demo: lit {got} of {want} (level {ch.Level}, {LampBook.Now(ch).Lit.Count} lit), carries {string.Join(",", SkillBook.Carried(ch).Select(c => c.Id))}");
    }

    /* ------------------------------------------------------------- the build -- */

    static int KindIndex(string kind) => Enum.TryParse<LampKind>(kind, true, out var k) ? (int)k : (int)LampKind.Small;
    static int CallingIndex(string? c) => c switch { "reaver" => 1, "arcanist" => 2, "stalker" => 3, _ => 0 };
    static readonly Color HaloLit = new("#ffb04a"), HaloBlue = new("#5d8dff"), HaloFlare = new("#ff7a2a");

    static bool Flare(string k) => k is "ultimate" or "ultimateMod" or "flareLamp";

    float RimToward(int i, double dx, double dy)
    {
        var k = M.Nodes[i].Kind;
        double r = radius[i];
        if (k == "link" && stop != BoardStop.Valley)
        {
            double hw = r, hh = r * 14 / 22, nn = Math.Sqrt(dx * dx + dy * dy);
            if (nn < 1e-6) return (float)hh;
            double c = Math.Abs(dx) / nn;
            return (float)(c > 1e-3 ? Math.Min(hw, (hw - hh) * c + hh) : hh);
        }
        return (float)r;
    }

    float EdgeMask(double x, double y)
    {
        static double Ss(double t) { t = Math.Clamp(t / Feather, 0, 1); return t * t * (3 - 2 * t); }
        return (float)(Ss(x) * Ss(Size.X - x) * Ss(y) * Ss(Size.Y - y));
    }

    /// <summary>Read her lamps, place the view, and write every instance (on open, on a resize; never per frame).</summary>
    public void Rebuild()
    {
        var t0 = System.Diagnostics.Stopwatch.GetTimestamp();
        builtSize = Size;
        var m = M;
        n = m.Nodes.Length;
        state = new int[n]; dim = new bool[n]; onPath = new bool[n]; notch = new bool[n]; radius = new float[n]; fade = new float[n];
        pos = new (double, double)[n];
        lit.Clear();
        foreach (var id in LampBook.Now(ch).Lit) if (m.Index.TryGetValue(id, out var i)) lit.Add(i);
        var depth = new Dictionary<string, int>();
        foreach (var i in lit) if (m.Nodes[i].Road is { } r) depth[r] = depth.GetValueOrDefault(r) + 1;
        bool GateOk(int i) => m.Nodes[i].Road is not { } r || depth.GetValueOrDefault(r) >= m.Nodes[i].Gate;
        for (int i = 0; i < n; i++)
        {
            state[i] = lit.Contains(i) ? 0 : !GateOk(i) ? 3 : m.Nodes[i].Adj.Any(lit.Contains) ? 1 : 2;
            dim[i] = LampAsk.Sleeps(ch, m.Nodes[i].Id) != null;
        }
        steps = m.Steps(lit);

        // the focus and its path
        var fid = SurvivorUnchained.Args.Get("lamps-focus");
        fixedFocus = fid == "auto" ? AutoFocus(GateOk) : fid == "blue" ? AutoFocus(GateOk, "blue") : fid != null && m.Index.TryGetValue(fid, out var fi) ? fi : -1;
        focus = fixedFocus;
        gateOk = GateOk;
        FindPath();

        // the view (§16 centering; the stop by flag)
        var window = new Box(0, 0, Size.X, Size.Y);
        valleyS = m.ValleyScale(window, Feather);
        var keep = lit.Concat(path).Concat(focus >= 0 ? [focus] : Array.Empty<int>()).ToList();
        if (keep.Count == 0) keep.Add(m.Index.GetValueOrDefault(Lamps.Start(ch.Archetype)));
        var want = SurvivorUnchained.Args.Get("lamps-stop") ?? "road";
        if (want == "valley") view = new BoardView(0, 0, valleyS, Size.X / 2, Size.Y / 2);
        else if (want == "lamp")
        {
            var c = m.Center(keep, window, LampBoardModel.LampScale);
            view = c with { S = LampBoardModel.LampScale };
        }
        else view = m.Center(keep, window);
        stop = LampBoardModel.StopOf(view.S, valleyS);
        if (focus >= 0 && CardOn && want != "valley") view = Slide(view, keep);
        bool valley = stop == BoardStop.Valley;
        for (int i = 0; i < n; i++)
        {
            var nd = m.Nodes[i];
            pos[i] = view.Project(nd.X, nd.Y);
            radius[i] = (float)(LampBoardModel.Diameter(nd.Kind, view.S, valleyS) / 2 * (i == focus ? 1.1 : 1.0));
            bool litOrPath = state[i] == 0 || onPath[i] || i == focus;
            fade[i] = litOrPath ? 1f : (float)LampBoardModel.Fade(steps[i]);
        }

        // gate notches (§16): one per gated stretch, at its threshold (a blocked lamp touching a non-blocked one), near her;
        // and the focus's
        var seen = new HashSet<string>();
        foreach (var i in Enumerable.Range(0, n).Where(i => state[i] == 3 && m.Nodes[i].Adj.Any(j => state[j] != 3))
                     .OrderBy(i => steps[i]).ThenBy(i => m.Nodes[i].Id, StringComparer.Ordinal))
            if (seen.Add(m.Nodes[i].Group) && steps[i] <= 3) notch[i] = true;
        gateNotch = (bool[])notch.Clone();
        if (focus >= 0 && state[focus] == 3) notch[focus] = true;

        WriteRoads(path, pathFrom, valley);
        WriteLamps(valley);
        WritePage(valley);
        WriteLabels(valley);
        SetUniforms(valley);
        PlaceCard(open: true);
        double ms = (System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
        var g = GetGlobalRect();
        GD.Print($"LAMPBOARD rebuild: {ms:F1} ms, stop {stop} scale {view.S:F3} (valley {valleyS:F3}), lit {lit.Count}, focus {(focus >= 0 ? m.Nodes[focus].Id : "-")}, path {path.Count}, window {g.Position.X:F0},{g.Position.Y:F0}-{g.End.X:F0},{g.End.Y:F0}");
    }

    /// <summary>
    /// §16 (the mock's C2/C3): with the build dead center, is there a clean spot for the focus's card? If not, slide the
    /// build the least distance (8 px steps, up to ±240 x ±160) that gives one, every lit lamp still 96 px inside the
    /// window; with none anywhere, the offset with the least overlap (16 px steps). Labels are placed after, so only
    /// lamps and the protected count. Only an open with a fixed focus (--lamps-focus) runs it.
    /// </summary>
    BoardView Slide(BoardView v, List<int> keep)
    {
        var m = M;
        float h = LampCard.HeightOf(CardFor(focus), out _, out _, out _);
        var P = new (double X, double Y)[n];
        var R = new double[n];
        var discs = new List<(double X, double Y, double R)>(n);
        var prot = new List<(double X, double Y, double R)>();
        for (int i = 0; i < n; i++)
        {
            P[i] = v.Project(m.Nodes[i].X, m.Nodes[i].Y);
            R[i] = LampBoardModel.Diameter(m.Nodes[i].Kind, v.S, valleyS) / 2 * (i == focus ? 1.1 : 1.0);
            discs.Add((P[i].X, P[i].Y, R[i]));
        }
        foreach (var i in keep.Distinct()) prot.Add((P[i].X, P[i].Y, R[i] + 4));
        if (pathFrom >= 0)
        {
            var chain = new List<int> { pathFrom };
            chain.AddRange(path);
            for (int k = 0; k + 1 < chain.Count; k++)
            {
                var (ax, ay) = P[chain[k]];
                var (bx, by) = P[chain[k + 1]];
                for (int t = 0; t <= 12; t++) prot.Add((ax + (bx - ax) * t / 12, ay + (by - ay) * t / 12, 3));
            }
        }
        // the board stays put and the window moves the other way: one pair of grids for every offset
        var lampGrid = new LampBoardModel.DiscGrid(discs, 32);
        var protGrid = new LampBoardModel.DiscGrid(prot, 32);
        var offs = new List<(int X, int Y)>();
        for (int ox = -240; ox <= 240; ox += 8) for (int oy = -160; oy <= 160; oy += 8) offs.Add((ox, oy));
        offs.Sort((a, b) => (a.X * a.X + a.Y * a.Y).CompareTo(b.X * b.X + b.Y * b.Y));
        bool Inside(int ox, int oy)
        {
            foreach (var i in lit)
            {
                double x = P[i].X + ox, y = P[i].Y + oy, r = R[i];
                if (Math.Min(Math.Min(x - r, Size.X - x - r), Math.Min(y - r, Size.Y - y - r)) < 96) return false;
            }
            return true;
        }
        foreach (var (ox, oy) in offs)
        {
            if (!Inside(ox, oy)) continue;
            var sp = LampBoardModel.PlaceCard(P[focus].X, P[focus].Y, R[focus] + 5, LampCard.Wd, h, lampGrid, protGrid, [],
                new Box(-ox, -oy, Size.X - ox, Size.Y - oy), cleanOnly: true);
            if (sp.Score != 0) continue;
            if (ox == 0 && oy == 0) return v;
            GD.Print($"LAMPBOARD slide: build offset ({ox}, {oy}) for a clean card spot");
            return v with { Sx = v.Sx + ox, Sy = v.Sy + oy };
        }
        // no clean spot anywhere: the least overlap (16 px steps), nearest the center on a tie; above all, never a
        // card over her lit lamps or the path when a slide avoids it
        (int X, int Y, int S)? best = null;
        foreach (var (ox, oy) in offs)
        {
            if (ox % 16 != 0 || oy % 16 != 0 || !Inside(ox, oy)) continue;
            var sp = LampBoardModel.PlaceCard(P[focus].X, P[focus].Y, R[focus] + 5, LampCard.Wd, h, lampGrid, protGrid, [],
                new Box(-ox, -oy, Size.X - ox, Size.Y - oy));
            if (best is not { } b || sp.Score < b.S) best = (ox, oy, sp.Score);
        }
        if (best is not { } bb || (bb.X == 0 && bb.Y == 0)) return v;
        GD.Print($"LAMPBOARD slide: build offset ({bb.X}, {bb.Y}), no clean card spot (least overlap {bb.S})");
        return v with { Sx = v.Sx + bb.X, Sy = v.Sy + bb.Y };
    }

    /// <summary>--lamps-focus auto: a far notable worth a path preview, as the mock's C_day (a notable that feeds a skill, its
    /// road open, 2 lamps from her lit set; then 2-4 lamps; then any notable or kind lamp 2-4 out), nearest her lit lamps'
    /// middle. --lamps-focus blue: the priced blue lamp nearest her lit set (fewest lamps away, then the nearest the
    /// middle).</summary>
    int AutoFocus(Func<int, bool> gateOk, string? kind = null)
    {
        var m = M;
        if (lit.Count == 0) return -1;
        double cx = lit.Average(i => m.Nodes[i].X), cy = lit.Average(i => m.Nodes[i].Y);
        double Far(int i) => Sq(m.Nodes[i].X - cx) + Sq(m.Nodes[i].Y - cy);
        int Away(int i) => m.PathTo(lit, gateOk, i) is { } pp ? pp.Path.Count : 99;
        if (kind != null)
            // the nearest that carries a price (the card's red price line: lamps_v2 prices only the Ford's, the crossings'
            // and the Old Roads' blues), else the nearest at all
            return Enumerable.Range(0, n).Where(i => m.Nodes[i].Kind == kind && !lit.Contains(i))
                .Select(i => (i, k: Away(i)))
                .OrderBy(q => Lamps.Find(m.Nodes[q.i].Id)?.Price != null ? 0 : 1).ThenBy(q => q.k).ThenBy(q => Far(q.i))
                .Select(q => q.i).DefaultIfEmpty(-1).First();
        bool Feeds(int i) => (Lamps.Find(m.Nodes[i].Id)?.Feeds?.Length ?? 0) > 0;
        GD.Print("LAMPBOARD auto: lit " + string.Join(",", lit.Select(i => m.Nodes[i].Id)) + " | notables with feeds: " + string.Join(", ",
            Enumerable.Range(0, n).Where(i => m.Nodes[i].Kind == "notable" && Feeds(i) && steps[i] <= 6)
                .Select(i => $"{m.Nodes[i].Id} steps {steps[i]} gate {(gateOk(i) ? "ok" : "shut")} away {Away(i)}")));
        var near = Enumerable.Range(0, n).Where(i => !lit.Contains(i) && steps[i] >= 2 && steps[i] <= 4 && gateOk(i)
            && m.Nodes[i].Kind is not ("small" or "attribute")).Select(i => (i, k: Away(i))).Where(q => q.k is >= 2 and <= 4).ToList();
        foreach (var pick in new Func<(int i, int k), bool>[]
                 {
                     q => q.k == 2 && m.Nodes[q.i].Kind == "notable" && Feeds(q.i),
                     q => m.Nodes[q.i].Kind == "notable" && Feeds(q.i),
                     q => m.Nodes[q.i].Kind == "notable",
                     _ => true,
                 })
        {
            var c = near.Where(pick).OrderBy(q => q.k).ThenBy(q => Far(q.i)).Select(q => q.i).DefaultIfEmpty(-1).First();
            if (c >= 0) return c;
        }
        return -1;
    }

    void WriteRoads(List<int> path, int from, bool valley)
    {
        var m = M;
        var mm = roads.Multimesh;
        var pathEdge = new Dictionary<long, (int A, int B, double Acc)>();
        if (from >= 0)
        {
            var chain = new List<int> { from };
            chain.AddRange(path);
            double acc = 0;
            for (int k = 0; k + 1 < chain.Count; k++)
            {
                int a = chain[k], b = chain[k + 1];
                pathEdge[EKey(a, b)] = (a, b, acc);
                acc += Math.Sqrt(Sq(pos[b].X - pos[a].X) + Sq(pos[b].Y - pos[a].Y));
            }
        }
        // cold first, then fuses, lit, the path on top
        var order = Enumerable.Range(0, m.Edges.Length).Select(e =>
        {
            var (a, b) = m.Edges[e];
            int kind = pathEdge.ContainsKey(EKey(a, b)) ? 3 : state[a] == 0 && state[b] == 0 ? 1
                : !valley && ((state[a] == 0 && state[b] == 1) || (state[b] == 0 && state[a] == 1)) ? 2 : 0;
            return (e, kind);
        }).OrderBy(q => q.kind).ToList();
        int k2 = 0;
        const float Pad = 8;
        foreach (var (e, kind) in order)
        {
            var (a, b) = m.Edges[e];
            double ph = 0;
            if (kind == 3) { var pe = pathEdge[EKey(a, b)]; a = pe.A; b = pe.B; ph = pe.Acc; }
            else if (kind == 2 && state[a] != 0) (a, b) = (b, a);
            var (ax, ay) = pos[a];
            var (bx, by) = pos[b];
            if (Math.Max(ax, bx) < -40 || Math.Min(ax, bx) > Size.X + 40 || Math.Max(ay, by) < -40 || Math.Min(ay, by) > Size.Y + 40) continue;
            double dx = bx - ax, dy = by - ay, L = Math.Sqrt(dx * dx + dy * dy);
            if (L < 1e-6) continue;
            double gap = valley ? 1.5 : 2;
            double ra = RimToward(a, dx, dy) + gap, rb = RimToward(b, dx, dy) + gap;
            if (L <= ra + rb + 1) continue;
            double ux = dx / L, uy = dy / L, len = L - ra - rb;
            var start = new Vector2((float)(ax + ux * (ra - Pad)), (float)(ay + uy * (ra - Pad)));
            var xf = new Transform2D((float)Math.Atan2(uy, ux), new Vector2((float)len + 2 * Pad, 2 * Pad), 0, start);
            float f = kind == 0 ? Math.Min(fade[a], fade[b]) : 1f;
            float phase = kind == 3 ? -(float)(ph + ra) : -(float)ra;
            mm.SetInstanceTransform2D(k2, xf);
            mm.SetInstanceColor(k2, Colors.White);
            mm.SetInstanceCustomData(k2, new Color((float)len, kind, f, phase));
            k2++;
        }
        mm.VisibleInstanceCount = k2;
    }

    static long EKey(int a, int b) => a < b ? ((long)a << 32) | (uint)b : ((long)b << 32) | (uint)a;
    static double Sq(double v) => v * v;

    void WriteLamps(bool valley)
    {
        var m = M;
        var mm = lamps.Multimesh;
        // lit last, the focus on top
        var order = Enumerable.Range(0, n).OrderBy(i => (state[i] == 0 ? 1 : 0) + (i == focus ? 2 : 0)).ThenBy(i => i).ToArray();
        slot = new int[n];
        int k = 0;
        foreach (var i in order)
        {
            var (x, y) = pos[i];
            if (x < -60 || x > Size.X + 60 || y < -60 || y > Size.Y + 60) { slot[i] = -1; continue; }
            slot[i] = k;
            WriteLamp(i, k++);
        }
        mm.VisibleInstanceCount = k;
        // halos: lit and awake
        var hm = halos.Multimesh;
        int h = 0;
        foreach (var i in order)
        {
            if (h >= MaxHalos || state[i] != 0 || dim[i] || slot[i] < 0) continue;
            var kind = m.Nodes[i].Kind;
            var col = kind == "blue" ? HaloBlue : Flare(kind) ? HaloFlare : HaloLit;
            float R = radius[i];
            float H = valley ? Math.Max(R * 1.4f, 2.5f) * 3.2f : R * 1.8f * 3.2f;
            hm.SetInstanceTransform2D(h, new Transform2D(0, new Vector2(2 * H, 2 * H), 0, new Vector2((float)pos[i].X, (float)pos[i].Y)));
            hm.SetInstanceColor(h, col);
            hm.SetInstanceCustomData(h, new Color(R, Flicker(i), valley ? 1 : 0, 0));
            h++;
        }
        hm.VisibleInstanceCount = h;
    }

    /// <summary>A stable 0..1 per lamp (FNV-1a of its id; string.GetHashCode changes every run).</summary>
    static float Seed(int i)
    {
        uint h = 2166136261;
        foreach (var ch in M.Nodes[i].Id) { h ^= ch; h *= 16777619; }
        return (h % 1000u) / 1000f;
    }
    static float Flicker(int i) => 1f + (Seed(i) - 0.5f) * 0.08f;

    void WriteLamp(int i, int k)
    {
        var nd = M.Nodes[i];
        float R = radius[i];
        float H = R + 14;
        int flags = (dim[i] ? 1 : 0) | (i == focus ? 2 : 0) | (onPath[i] ? 4 : 0) | (steps[i] <= 3 || state[i] == 0 || onPath[i] || i == focus ? 8 : 0)
                    | (notch[i] ? 32 : 0) | (stop == BoardStop.Lamp && nd.Kind == "notable" && FeedGlyph(Lamps.Find(nd.Id)) != null ? 64 : 0);
        var mm = lamps.Multimesh;
        mm.SetInstanceTransform2D(k, new Transform2D(0, new Vector2(2 * H, 2 * H), 0, new Vector2((float)pos[i].X, (float)pos[i].Y)));
        mm.SetInstanceColor(k, new Color(KindIndex(nd.Kind), state[i], fade[i], flags));
        mm.SetInstanceCustomData(k, new Color(R, Seed(i), CallingIndex(nd.Calling), fade[i] * EdgeMask(pos[i].X, pos[i].Y)));
    }

    void WritePage(bool valley)
    {
        pageMat.SetShaderParameter(PSize, Size);
        page.Position = Vector2.Zero;
        page.Size = Size;
        ink.Size = Size;
        if (lit.Count > 0)
        {
            double x0 = lit.Min(i => pos[i].X), x1 = lit.Max(i => pos[i].X), y0 = lit.Min(i => pos[i].Y), y1 = lit.Max(i => pos[i].Y);
            pageMat.SetShaderParameter(PGlowC, new Vector2((float)(x0 + x1) / 2, (float)(y0 + y1) / 2));
            pageMat.SetShaderParameter(PGlowR, new Vector2((float)Math.Max(x1 - x0, 40) * 0.8f, (float)Math.Max(y1 - y0, 40) * 0.8f));
        }
        var c = view.Project(0, 0);
        pageMat.SetShaderParameter(PRingC, new Vector2((float)c.X, (float)c.Y));
        var rr = M.RingRadii();
        pageMat.SetShaderParameter(PRings, valley ? new Vector3((float)(rr[0] * view.S), (float)(rr[1] * view.S), (float)(rr[2] * view.S)) : Vector3.Zero);
    }

    static Font LabelFont(int px) => LampInk.F("cinzel-600", (int)Math.Round(px * 0.16));

    /// <summary>The placed labels, kept across opens for the same view and lit set (the Valley's search is the open's
    /// cost; the grid made it cheap, this makes a reopen free).</summary>
    static readonly Dictionary<string, List<LampBoardModel.Placed>> labelCache = new();

    /// <summary>The labels, the gate numerals and the Lamp stop's ink (each notable's feed glyph, the names under
    /// notables, blue lamps, entries and Strikes, a lit link's bound skill), all drawn by one control (BoardInk): one
    /// canvas item, not a Label per name (phase 1's went from 3 draw calls to 13).</summary>
    void WriteLabels(bool valley, Box? block = null)
    {
        int px = LampBoardModel.LabelPx(stop);
        var font = LabelFont(px);
        var discs = new List<(double, double, double)>();
        var discOf = new List<int>();
        for (int i = 0; i < n; i++)
            if (slot[i] >= 0) { discs.Add((pos[i].X, pos[i].Y, radius[i] + 5)); discOf.Add(i); }
        var allowed = new Box(40, 40, Size.X - 40, Size.Y - 40);
        string key = $"{stop}|{view}|{Size}|{block}|{string.Join(",", lit.OrderBy(i => i))}";
        if (!labelCache.TryGetValue(key, out var placed))
        {
            // her lit roads, sampled every 8 px: no label sits across them
            var roads = new List<(double, double, double)>();
            if (!valley)
                foreach (var (a, b) in M.Edges)
                {
                    if (!lit.Contains(a) || !lit.Contains(b)) continue;
                    var (ax, ay) = pos[a];
                    var (bx, by) = pos[b];
                    int k = Math.Max(1, (int)(Math.Sqrt(Sq(bx - ax) + Sq(by - ay)) / 8));
                    for (int t = 0; t <= k; t++) roads.Add((ax + (bx - ax) * t / k, ay + (by - ay) * t / k, 4));
                }
            placed = M.PlaceLabels(view, stop, discs, allowed, block is { } bk ? [bk] : [], (t, p) => LampInk.W(font, t, p), lit, discOf, roads);
            if (labelCache.Count > 16) labelCache.Clear();
            labelCache[key] = placed;
        }
        placedLabels = placed;
        WriteInk();
    }

    /// <summary>Everything BoardInk draws, from the current state (on a rebuild and on a focus change).</summary>
    void WriteInk()
    {
        bool valley = stop == BoardStop.Valley;
        int px = LampBoardModel.LabelPx(stop);
        var font = LabelFont(px);
        ink.Clear();
        float capH = (float)Math.Round(px * 0.70);
        foreach (var pl in placedLabels)
            if (crowd is not { } cr || !pl.Box.Overlaps(cr))
                ink.Labels.Add(new BoardInk.Word(font, px, pl.Text, new Vector2((float)pl.X, (float)pl.Y + capH / 2), LampInk.Body with { A = 0.75f }, 0,
                valley ? 6 : 4, 1));
        // the gate numerals in their notches
        if (!valley)
            for (int i = 0; i < n; i++)
            {
                if (!notch[i] || slot[i] < 0) continue;
                float R = radius[i];
                float cx = (float)pos[i].X + R * 0.72f + 5f, cy = (float)pos[i].Y + R * 0.72f + 4f;
                ink.Labels.Add(new BoardInk.Word(Style.UiHeavy, LampBoardModel.ChipPx, M.Nodes[i].Gate.ToString(),
                    new Vector2(cx + 0.5f, cy + LampBoardModel.ChipPx * 0.36f), LampInk.RimGold, 0, 0, fade[i] * EdgeMask(pos[i].X, pos[i].Y)));
            }
        if (stop == BoardStop.Lamp) WriteLampStopInk();
        ink.QueueRedraw();
    }

    /// <summary>§5's Lamp stop: each notable's feed glyph inside it (the shader leaves its ring and flame out: flag 64),
    /// names under notables, blue lamps, entries and Strikes (Alegreya Sans 700 14 caps at 80%, clear of every lamp,
    /// label and other name), and a lit link's bound skill's glyph beside it.</summary>
    void WriteLampStopInk()
    {
        var m = M;
        var nameFont = LampInk.F("alegreya-sans-700", 1);
        const int NamePx = 14;
        var taken = placedLabels.Select(p => p.Box).ToList();
        var discs = new List<(double X, double Y, double R)>();
        for (int i = 0; i < n; i++) if (slot[i] >= 0) discs.Add((pos[i].X, pos[i].Y, radius[i] + 2));
        var grid = new LampBoardModel.DiscGrid(discs, 32);
        for (int i = 0; i < n; i++)
        {
            if (slot[i] < 0) continue;
            var nd = m.Nodes[i];
            float a = fade[i] * EdgeMask(pos[i].X, pos[i].Y);
            if (a < 0.05f) continue;
            var d = Lamps.Find(nd.Id);
            var at = new Vector2((float)pos[i].X, (float)pos[i].Y);
            float R = radius[i];
            if (nd.Kind == "notable" && FeedGlyph(d) is { } g)
            {
                float gs = R * 1.15f;
                var col = state[i] == 0 && !dim[i] ? new Color("#4a3214") with { A = 0.9f } : new Color("#9aa4b2") with { A = 0.7f };
                ink.Glyphs.Add(new BoardInk.Mark(g, new Rect2(at - Vector2.One * gs / 2, Vector2.One * gs), col with { A = col.A * a }));
            }
            if (nd.Kind == "link" && state[i] == 0 && LampAsk.LinkPick(ch, nd.Id) is { } pick && Weapons.All.TryGetValue(pick, out var wd))
                ink.Glyphs.Add(new BoardInk.Mark(wd.Art, new Rect2(at + new Vector2(R + 6, -9), new Vector2(18, 18)), LampInk.Gold with { A = a }));
            if (d != null && nd.Kind is "notable" or "blue" or "entry" or "ultimate" && d.Name != "")
            {
                var text = d.Name.ToUpperInvariant();
                float w = LampInk.W(nameFont, text, NamePx);
                float y = at.Y + R + 8 + 10;            // the caps' baseline: 8 px under the rim
                var box = new Box(at.X - w / 2 - 3, y - 12, at.X + w / 2 + 3, y + 3);
                bool clear = box.Inside(new Box(12, 12, Size.X - 12, Size.Y - 12)) && !taken.Any(box.Overlaps)
                    && grid.Count(box, 2, q => Math.Abs(q.X - at.X) < 0.5 && Math.Abs(q.Y - at.Y) < 0.5) == 0;
                if (!clear) continue;
                taken.Add(box);
                ink.Labels.Add(new BoardInk.Word(nameFont, NamePx, text, new Vector2(at.X, y), LampInk.Body with { A = 0.80f }, 0, 3, a));
            }
        }
    }

    static string? FeedGlyph(LampDef? d) =>
        d is { Feeds.Length: > 0 } && Weapons.All.TryGetValue(d.Feeds[0], out var w) && w.Art != "" ? w.Art : null;

    /* ------------------------------------------------------------- the focus card -- */

    /// <summary>The card's words for lamp i (§7, in order).</summary>
    LampCardText CardFor(int i)
    {
        var m = M;
        var nd = m.Nodes[i];
        var d = Lamps.Find(nd.Id);
        bool pad = Play.Controls.Instance?.UsingPad == true;
        var (chip, chipC) = nd.Kind switch
        {
            "notable" => ("NOTABLE", LampInk.Chip), "blue" => ("BLUE LAMP", LampInk.Cobalt), "rite" => ("RITE", LampInk.Chip),
            "link" => ("LINK", LampInk.Chip), "ultimate" or "ultimateMod" or "flareLamp" => ("FLARE", LampInk.Fire),
            "entry" => ("ENTRY", LampInk.Chip), _ => ((string?)null, LampInk.Chip),
        };
        string place = m.Groups.TryGetValue(nd.Group, out var g) ? m.GroupName(g) : "";
        var carried = SkillBook.Carried(ch).Select(c => c.Id).ToHashSet();
        var feeds = new List<(string, bool)>();
        var names = new List<string>();
        foreach (var f in d?.Feeds ?? [])
            if (Weapons.All.TryGetValue(f, out var wd)) { feeds.Add((wd.Art, carried.Contains(f))); names.Add(wd.Name); }
        string? feedsText = names.Count > 0 ? "Feeds " + string.Join(", ", names) : null;
        string stateLine;
        var stateC = LampInk.Gold;
        var prompts = new List<(string, string)>();
        int spare = LampBook.Spare(ch, w);
        bool night = w?.Time == TimeOfDay.Night;
        if (state[i] == 0)
        {
            if (LampAsk.Sleeps(ch, nd.Id) is { } sl)
                stateLine = $"Sleeps: carry {string.Join(" or ", sl.Skills.Select(s => Weapons.All.TryGetValue(s, out var x) ? x.Name : s))} to wake it";
            else stateLine = "Lit  ·  lamps go out at a town’s lamp-post, by day";
            if (!night && LampBook.CanUnlight(ch, nd.Id) == LampNo.None)
                prompts.Add(pad ? ("X", "Hold: put out") : ("Right-click", "Hold: put out"));
        }
        else if (state[i] == 3)
        {
            stateLine = $"Opens at {nd.Gate} lit on this road  ·  {(nd.Road != null ? LampBook.Depth(ch, nd.Road) : 0)} lit";
            stateC = LampInk.Gate;
        }
        else if (state[i] == 1)
        {
            stateLine = "Light it: 1 lamp";
            if (!night) prompts.Add(pad ? ("A", "Light") : ("Click", "Light it"));
        }
        else
        {
            int k = LampAsk.PathTo(ch, w, nd.Id).Count;
            stateLine = k > 0 ? $"{k} lamps away  ·  you have {spare}" : "Out of reach";
            if (k > 0 && !night) prompts.Add(pad ? ("A", "Light the path") : ("Click", "Light the path"));
        }
        string? fires = null;
        if (nd.Kind == "link")
        {
            var pick = LampAsk.LinkPick(ch, nd.Id);
            string pn = pick != null && Weapons.All.TryGetValue(pick, out var pw) ? pw.Name : "Light my way’s pick";
            fires = $"Fires: {pn} (change: {(pad ? "A" : "Click")})";
        }
        return new LampCardText(d?.Name ?? nd.Id, chip, chipC, place, d?.Text ?? "", feeds, feedsText,
            nd.Kind == "blue" ? d?.Price : null, stateLine, stateC, fires, prompts);
    }

    /// <summary>§16's placement: beside the focus, never over her lit lamps, the path preview or the focus; its edge
    /// band clear of every lamp and label, else the least overlap; inside the board's window.</summary>
    void PlaceCard(bool open = false)
    {
        if (!CardOn || focus < 0 || slot.Length == 0 || slot[focus] < 0)
        {
            card.Visible = false; CardSpot = null;
            if (crowd != null) { crowd = null; WriteInk(); }
            return;
        }
        bool pad = Play.Controls.Instance?.UsingPad == true;
        float h = card.Show(CardFor(focus), pad);
        var discs = new List<(double X, double Y, double R)>();
        var prot = new List<(double X, double Y, double R)>();
        for (int i = 0; i < n; i++)
        {
            if (slot[i] < 0) continue;
            discs.Add((pos[i].X, pos[i].Y, radius[i]));
            if (state[i] == 0 || onPath[i] || i == focus) prot.Add((pos[i].X, pos[i].Y, radius[i] + 4));
        }
        if (pathFrom >= 0)
        {
            var chain = new List<int> { pathFrom };
            chain.AddRange(path);
            for (int k = 0; k + 1 < chain.Count; k++)
            {
                var (ax, ay) = pos[chain[k]];
                var (bx, by) = pos[chain[k + 1]];
                for (int t = 0; t <= 12; t++) prot.Add((ax + (bx - ax) * t / 12, ay + (by - ay) * t / 12, 3));
            }
        }
        var labelsBoxes = placedLabels.Select(p => p.Box).ToList();
        var (fx, fy) = pos[focus];
        var spot = LampBoardModel.PlaceCard(fx, fy, radius[focus] + 5, LampCard.Wd, h, discs, prot, labelsBoxes, new Box(0, 0, Size.X, Size.Y));
        CardSpot = spot;
        var room = spot.Rect.Grow(LampBoardModel.LabelRoom);
        // on open, a label the card crowds is placed again around it (the card's room a blocker); on a hover, it hides
        // for as long as the card is there (labels don't jump about under the pointer)
        if (open && placedLabels.Any(p => p.Box.Overlaps(room))) { crowd = null; WriteLabels(stop == BoardStop.Valley, room); }
        if (crowd != room) { crowd = room; WriteInk(); }
        card.Position = new Vector2((float)spot.Rect.X0, (float)spot.Rect.Y0);
        card.Visible = true;
        var g = GetGlobalRect().Position;
        GD.Print($"LAMPBOARD card: {spot.Side} of {M.Nodes[focus].Id}, shift {spot.Shift}, overlap {spot.Score}, at {g.X + spot.Rect.X0:F0},{g.Y + spot.Rect.Y0:F0}-{g.X + spot.Rect.X1:F0},{g.Y + spot.Rect.Y1:F0}");
    }

    void SetUniforms(bool valley)
    {
        foreach (var mat in new[] { lampMat, roadMat, haloMat })
        {
            mat.SetShaderParameter(PFeather, Feather);
            mat.SetShaderParameter(PValley, valley ? 1f : 0f);
            mat.SetShaderParameter(PFind, 0f);
        }
        pageMat.SetShaderParameter(PFeather, Feather);
        winPx = new Rect2();
        UpdateWin();
    }

    /// <summary>The feather reads the window in framebuffer px: set when the rect moves (no per-frame work otherwise).</summary>
    void UpdateWin()
    {
        var xf = GetViewport().GetFinalTransform() * GetGlobalTransformWithCanvas();
        var a = xf * Vector2.Zero;
        var b = xf * Size;
        var r = new Rect2(a, b - a);
        if (r == winPx) return;
        winPx = r;
        var v = new Vector4(a.X, a.Y, b.X, b.Y);
        lampMat.SetShaderParameter(PWin, v);
        roadMat.SetShaderParameter(PWin, v);
        haloMat.SetShaderParameter(PWin, v);
    }

    /* ------------------------------------------------------------- hover -- */

    public override void _GuiInput(InputEvent e)
    {
        if (e is not InputEventMouseMotion mm || n == 0 || fixedFocus >= 0) return;
        var (bx, by) = view.Unproject(mm.Position.X, mm.Position.Y);
        int hit = M.Hit(bx, by, i => (radius[i] + 4) / view.S);
        if (hit != focus) SetFocus(hit);
    }

    /// <summary>The focus's path preview: the fewest unlit lamps to it (none when it is lit or out of reach).</summary>
    void FindPath()
    {
        Array.Clear(onPath);
        path = new();
        pathFrom = -1;
        if (focus >= 0 && !lit.Contains(focus) && M.PathTo(lit, gateOk, focus) is { } pr) { path = pr.Path; pathFrom = pr.From; }
        foreach (var i in path) onPath[i] = true;
    }

    /// <summary>Hover or the pad moved the focus: the path preview, the lamps' marks, the ink and the card follow
    /// (the instances are rewritten, ~1200 writes; nothing else is rebuilt).</summary>
    public void SetFocus(int i)
    {
        if (i == focus || n == 0) return;
        focus = i;
        FindPath();
        bool valley = stop == BoardStop.Valley;
        for (int j = 0; j < n; j++)
        {
            radius[j] = (float)(LampBoardModel.Diameter(M.Nodes[j].Kind, view.S, valleyS) / 2 * (j == focus ? 1.1 : 1.0));
            bool litOrPath = state[j] == 0 || onPath[j] || j == focus;
            fade[j] = litOrPath ? 1f : (float)LampBoardModel.Fade(steps[j]);
            notch[j] = gateNotch[j] || (j == focus && state[j] == 3);
        }
        WriteRoads(path, pathFrom, valley);
        WriteLamps(valley);
        WriteInk();
        PlaceCard();
        FocusChanged?.Invoke(i);
    }

    /* ------------------------------------------------------------- per frame: nothing but the window check -- */

    int measureFrame = -1;
    double cpuTicks;
    long allocBytes;
    int dcOn, dcOff, dcN;
    double gpuOn, gpuOff, cpuOn, cpuOff;

    public override void _Ready()
    {
        if (SurvivorUnchained.Args.Has("lamps-measure"))
        {
            measureFrame = 0;
            RenderingServer.ViewportSetMeasureRenderTime(GetViewport().GetViewportRid(), true);
        }
    }

    public override void _Process(double delta)
    {
        long a0 = measureFrame >= 0 ? GC.GetAllocatedBytesForCurrentThread() : 0;
        long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
        if (n > 0) UpdateWin();
        if (measureFrame < 0) return;
        cpuTicks += System.Diagnostics.Stopwatch.GetTimestamp() - t0;
        allocBytes += GC.GetAllocatedBytesForCurrentThread() - a0;
        Measure();
    }

    /// <summary>--lamps-measure: after 3 s, 120 frames with the board, 120 without, 120 with; draw calls (the frame's
    /// total, so the board's is the difference), the board's _Process CPU, and the bytes it allocated.</summary>
    void Measure()
    {
        measureFrame++;
        int f = measureFrame - 180;
        if (f < 0) { cpuTicks = 0; allocBytes = 0; return; }
        long dc = (long)RenderingServer.GetRenderingInfo(RenderingServer.RenderingInfo.TotalDrawCallsInFrame);
        var vp = GetViewport().GetViewportRid();
        double gpu = RenderingServer.ViewportGetMeasuredRenderTimeGpu(vp), cpu = RenderingServer.ViewportGetMeasuredRenderTimeCpu(vp);
        if (f < 120) { gpuOn += gpu; cpuOn += cpu; }
        else if (f > 125 && f <= 245) { gpuOff += gpu; cpuOff += cpu; }
        if (f < 120) { dcOn += (int)dc; dcN++; }
        else if (f == 120) { foreach (var c in GetChildren()) if (c is CanvasItem ci) ci.Visible = false; }
        else if (f > 125 && f <= 245) dcOff += (int)dc;
        else if (f == 246)
        {
            foreach (var c in GetChildren()) if (c is CanvasItem ci && ci != card) ci.Visible = true;
            card.Visible = CardSpot != null;
            double ms = cpuTicks * 1000.0 / System.Diagnostics.Stopwatch.Frequency / 246;
            int labelsOn = ink.Labels.Count;
            GD.Print($"LAMPBOARD measure: draw calls with board {dcOn / (double)dcN:F1}, without {dcOff / 120.0:F1}, board {(dcOn / (double)dcN) - dcOff / 120.0:F1} " +
                     $"(labels+chips {labelsOn}); _Process {ms * 1000:F1} us/frame; allocated {allocBytes} B over 246 frames; " +
                     $"viewport GPU {gpuOn / 120:F3} vs {gpuOff / 120:F3} ms, render CPU {cpuOn / 120:F3} vs {cpuOff / 120:F3} ms; " +
                     $"process {Performance.GetMonitor(Performance.Monitor.TimeProcess) * 1000:F2} ms, fps {Performance.GetMonitor(Performance.Monitor.TimeFps):F0}");
            measureFrame = -1;
        }
    }
}

/// <summary>The board's type and marks in one canvas item: the labels (Cinzel with a dark halo), the gate numerals and
/// the Lamp stop's names and glyphs. LampBoard fills the lists and asks for a redraw; it never draws per frame.</summary>
public partial class BoardInk : Control
{
    /// <summary>Text with its baseline at At, centered (Align 0) or left (-1); Halo the dark outline's px; A its alpha.</summary>
    public readonly record struct Word(Font F, int Px, string Text, Vector2 At, Color C, int Align, int Halo, float A);
    public readonly record struct Mark(string Glyph, Rect2 Rect, Color C);
    public readonly List<Word> Labels = new();
    public readonly List<Mark> Glyphs = new();

    public BoardInk() { MouseFilter = MouseFilterEnum.Ignore; }

    public void Clear() { Labels.Clear(); Glyphs.Clear(); }

    public override void _Draw()
    {
        foreach (var g in Glyphs)
            DrawTextureRect(Ui.Glyphs.Texture(g.Glyph, Math.Max(16, (int)Math.Ceiling(g.Rect.Size.X * 2)), Colors.White, line: true), g.Rect, false, g.C);
        foreach (var w in Labels)
        {
            if (w.A <= 0.01f) continue;
            float tw = LampInk.W(w.F, w.Text, w.Px);
            var at = new Vector2(Mathf.Round(w.Align == 0 ? w.At.X - tw / 2 : w.At.X), Mathf.Round(w.At.Y));
            if (w.Halo > 0)
            {
                DrawStringOutline(w.F, at, w.Text, HorizontalAlignment.Left, -1, w.Px, w.Halo * 2, LampInk.Dark with { A = 0.35f * w.A });
                DrawStringOutline(w.F, at, w.Text, HorizontalAlignment.Left, -1, w.Px, w.Halo, LampInk.Dark with { A = 0.6f * w.A });
            }
            DrawString(w.F, at, w.Text, HorizontalAlignment.Left, -1, w.Px, w.C with { A = w.C.A * w.A });
        }
    }
}
