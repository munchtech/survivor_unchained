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
    internal static readonly Color HaloLit = new("#ffb04a"), HaloBlue = new("#5d8dff"), HaloFlare = new("#ff7a2a");

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
        static double Ss(double t, float f) { if (f < 0.5f) return t >= 0 ? 1 : 0; t = Math.Clamp(t / f, 0, 1); return t * t * (3 - 2 * t); }
        var f = Fe.X < 0 ? new Vector4(Feather, Feather, Feather, Feather) : Fe;
        return (float)(Ss(x, f.X) * Ss(Size.X - x, f.Z) * Ss(y, f.Y) * Ss(Size.Y - y, f.W));
    }

    /* ------------------------------------------------------------- A, Open wide (§16 "Edges, A") -- */

    /// <summary>The window's feather per side (left, top, right, bottom); X < 0: Feather on all four (C).</summary>
    public Vector4 Fe = new(-1, -1, -1, -1);
    /// <summary>A: the foot's boxes in this control (labels and the card keep out); the page glow off (A's pools are its glow).</summary>
    public List<Box> Keep = new();
    public bool Wide;
    ShaderMaterial? inkMat;
    /// <summary>The view was laid again (A's pools follow her lit lamps).</summary>
    public event Action? Relaid;

    /// <summary>A's knockout on every pass (the foot's and her masks), and on the type.</summary>
    public void Knock(Texture2D hud, Texture2D? her, Vector2 vp)
    {
        inkMat ??= new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ui_lamps_ink.gdshader") };
        ink.Material = inkMat;
        foreach (var mat in new[] { lampMat, roadMat, haloMat, inkMat })
        {
            mat.SetShaderParameter("knock_on", 1f);
            mat.SetShaderParameter("knock_hud", hud);
            if (her != null) mat.SetShaderParameter("knock_her", her);
            mat.SetShaderParameter("vp_size", vp);
        }
    }

    /// <summary>Her lit lamps' places on the screen (inside the window).</summary>
    public List<Vector2> LitScreen()
    {
        var o = new List<Vector2>();
        var g = GetGlobalRect().Position;
        foreach (var i in lit)
            if (i < n && slot[i] >= 0 && InView(i, 0)) o.Add(g + new Vector2((float)pos[i].X, (float)pos[i].Y));
        return o;
    }

    public bool IsValley => stop == BoardStop.Valley;

    /// <summary>The Flare's lamps (A: the keeper's fire, focused, marks them).</summary>
    public HashSet<int> FlareLamps() => Enumerable.Range(0, M.Nodes.Length).Where(i => Flare(M.Nodes[i].Kind)).ToHashSet();

    /// <summary>Read her lamps, place the view, and write every instance (on open and on a resize).</summary>
    public void Rebuild()
    {
        var t0 = System.Diagnostics.Stopwatch.GetTimestamp();
        builtSize = Size;
        var m = M;
        n = m.Nodes.Length;
        state = new int[n]; dim = new bool[n]; onPath = new bool[n]; notch = new bool[n]; radius = new float[n]; fade = new float[n];
        found = new bool[n];
        pos = new (double, double)[n];
        lit.Clear();
        foreach (var id in LampBook.Now(ch).Lit) if (m.Index.TryGetValue(id, out var i)) lit.Add(i);
        ComputeDim();
        ComputeState();

        // the focus and its path (on a pad the focus starts at her frontier: something is always in hand)
        var fid = SurvivorUnchained.Args.Get("lamps-focus");
        fixedFocus = fid == "auto" ? AutoFocus(gateOk) : fid == "blue" ? AutoFocus(gateOk, "blue") : fid != null && m.Index.TryGetValue(fid, out var fi) ? fi : -1;
        focus = fixedFocus >= 0 ? fixedFocus : Play.Controls.Instance?.UsingPad == true ? Frontier() : -1;
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
        if (fixedFocus >= 0 && CardOn && want != "valley")
        {
            long ts = System.Diagnostics.Stopwatch.GetTimestamp();
            view = Slide(view, keep);
            GD.Print($"LAMPBOARD slide search: {(System.Diagnostics.Stopwatch.GetTimestamp() - ts) * 1000.0 / System.Diagnostics.Stopwatch.Frequency:F1} ms");
        }
        Relayout(view, settle: true, open: true);
        double ms = (System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
        var g = GetGlobalRect();
        GD.Print($"LAMPBOARD rebuild: {ms:F1} ms, stop {stop} scale {view.S:F3} (valley {valleyS:F3}), lit {lit.Count}, focus {(focus >= 0 ? m.Nodes[focus].Id : "-")}, path {path.Count}, window {g.Position.X:F0},{g.Position.Y:F0}-{g.End.X:F0},{g.End.Y:F0}");
    }

    /// <summary>Which lamps sleep (on open and when what she carries changes: a layout switch).</summary>
    void ComputeDim()
    {
        for (int i = 0; i < n; i++) dim[i] = LampAsk.Sleeps(ch, M.Nodes[i].Id) != null;
    }

    /// <summary>Each lamp's state from the lit set shown (lit, available, unlit, blocked), the road steps and the gate
    /// notches (§16: one per gated stretch, at its threshold near her, and the focus's).</summary>
    void ComputeState()
    {
        var m = M;
        var depth = new Dictionary<string, int>();
        foreach (var i in lit) if (m.Nodes[i].Road is { } r) depth[r] = depth.GetValueOrDefault(r) + 1;
        bool GateOk(int i) => m.Nodes[i].Road is not { } r || depth.GetValueOrDefault(r) >= m.Nodes[i].Gate;
        gateOk = GateOk;
        for (int i = 0; i < n; i++)
            state[i] = lit.Contains(i) ? 0 : !GateOk(i) ? 3 : m.Nodes[i].Adj.Any(lit.Contains) ? 1 : 2;
        steps = m.Steps(lit);
        Array.Clear(notch);
        var seen = new HashSet<string>();
        foreach (var i in Enumerable.Range(0, n).Where(i => state[i] == 3 && m.Nodes[i].Adj.Any(j => state[j] != 3))
                     .OrderBy(i => steps[i]).ThenBy(i => m.Nodes[i].Id, StringComparer.Ordinal))
            if (seen.Add(m.Nodes[i].Group) && steps[i] <= 3) notch[i] = true;
        gateNotch = (bool[])notch.Clone();
        if (focus >= 0 && state[focus] == 3) notch[focus] = true;
    }

    /// <summary>The lamps lit changed (a light, a put out, a switch, a step of a reveal): states, path, every instance,
    /// the labels and the card again, the view kept.</summary>
    void Restate()
    {
        ComputeState();
        FindPath();
        Relayout(view, settle: true);
    }

    /// <summary>Every lamp's screen place, size and fade for a view.</summary>
    void Geometry()
    {
        var m = M;
        for (int i = 0; i < n; i++)
        {
            var nd = m.Nodes[i];
            pos[i] = view.Project(nd.X, nd.Y);
            radius[i] = (float)(LampBoardModel.Diameter(nd.Kind, view.S, valleyS) / 2 * (i == focus ? 1.1 : 1.0));
            bool litOrPath = state[i] == 0 || onPath[i] || i == focus;
            fade[i] = litOrPath ? 1f : (float)LampBoardModel.Fade(steps[i]);
        }
    }

    /// <summary>The view moved (or settled): every instance again. In motion the labels and the card ride along with the
    /// board (labels hide while the scale changes); settled, the labels are placed and the card finds its spot.</summary>
    void Relayout(BoardView v, bool settle, bool open = false)
    {
        var old = stop;
        view = Hold(v);
        stop = LampBoardModel.StopOf(view.S, valleyS);
        bool valley = stop == BoardStop.Valley;
        Geometry();
        WriteRoads(path, pathFrom, valley);
        WriteLamps(valley);
        WritePage(valley);
        if (open || old != stop) SetUniforms(valley);
        Relaid?.Invoke();
        if (settle)
        {
            labelView = view;
            WriteLabels(valley);
            PlaceCard(open);
        }
        else
        {
            WriteInk();
            RideCard();
        }
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
        // one pass, nearest first: the first clean spot wins; else the least overlap (phase 2 ran a clean-only pass at
        // 8 px and then this one: 350-460 ms; this is the open's only search)
        (int X, int Y, int S)? best = null;
        foreach (var (ox, oy) in offs)
        {
            if (ox % 16 != 0 || oy % 16 != 0 || !Inside(ox, oy)) continue;
            var sp = LampBoardModel.PlaceCard(P[focus].X, P[focus].Y, R[focus] + 5, LampCard.Wd, h, lampGrid, protGrid, [],
                new Box(-ox, -oy, Size.X - ox, Size.Y - oy));
            if (sp.Score == 0)
            {
                if (ox == 0 && oy == 0) return v;
                GD.Print($"LAMPBOARD slide: build offset ({ox}, {oy}) for a clean card spot");
                return v with { Sx = v.Sx + ox, Sy = v.Sy + oy };
            }
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
                    | (found[i] ? 16 : 0) | (notch[i] ? 32 : 0) | (stop == BoardStop.Lamp && nd.Kind == "notable" && FeedGlyph(Lamps.Find(nd.Id)) != null ? 64 : 0);
        var mm = lamps.Multimesh;
        // denied: the focus shakes ±3 px for 0.15 s (§11)
        float sx = i == focus && shakeT > 0 ? 3f * Mathf.Sin((float)shakeT * 80f) * (float)(shakeT / 0.15) : 0;
        mm.SetInstanceTransform2D(k, new Transform2D(0, new Vector2(2 * H, 2 * H), 0, new Vector2((float)pos[i].X + sx, (float)pos[i].Y)));
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
        var allowed = Wide ? new Box(64, 40, Size.X - 64, Size.Y - 20) : new Box(40, 40, Size.X - 40, Size.Y - 40);
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
            placed = M.PlaceLabels(view, stop, discs, allowed, block is { } bk ? [.. Keep, bk] : Keep, (t, p) => LampInk.W(font, t, p), lit, discOf, roads);
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
        // in motion the labels ride with the board (placed for labelView); while the scale changes they wait for it to settle
        bool riding = Math.Abs(view.S / Math.Max(labelView.S, 1e-6) - 1) > 0.004;
        if (!riding)
            foreach (var pl in placedLabels)
            {
                if (crowd is { } cr && pl.Box.Overlaps(cr)) continue;
                var (bx, by) = labelView.Unproject(pl.X, pl.Y);
                var (x, y) = view.Project(bx, by);
                // a label fades with its lamps' feather and goes when none of them is in the window (the edge's 15%)
                float a = 1;
                if (pl.Lamps is { } ls)
                {
                    a = 0;
                    foreach (var l in ls) if (slot[l] >= 0) a = Math.Max(a, EdgeMask(pos[l].X, pos[l].Y));
                }
                a = Math.Min(a, EdgeMask(x, y) * 1.6f);
                if (a < 0.15f) continue;
                ink.Labels.Add(new BoardInk.Word(font, px, pl.Text, new Vector2((float)x, (float)y + capH / 2), LampInk.Body with { A = 0.75f }, 0,
                    valley ? 6 : 4, Math.Min(1, a) * labelFade));
            }
        // the gate numerals in their notches (they fade with their lamps, and go under 15%)
        if (!valley)
            for (int i = 0; i < n; i++)
            {
                if (!notch[i] || slot[i] < 0) continue;
                float a = fade[i] * EdgeMask(pos[i].X, pos[i].Y);
                if (a < 0.15f) continue;
                float R = radius[i];
                float cx = (float)pos[i].X + R * 0.72f + 5f, cy = (float)pos[i].Y + R * 0.72f + 4f;
                ink.Labels.Add(new BoardInk.Word(Style.UiHeavy, LampBoardModel.ChipPx, M.Nodes[i].Gate.ToString(),
                    new Vector2(cx + 0.5f, cy + LampBoardModel.ChipPx * 0.36f), LampInk.RimGold, 0, 0, a));
            }
        // the Valley's lamps are dots: the focus wears the ink's ring there (the shader draws it at the other stops)
        ink.Focus = focus >= 0 && slot.Length > 0 && slot[focus] >= 0 && valley ? new Vector3((float)pos[focus].X, (float)pos[focus].Y, radius[focus] + 5) : null;
        ink.Hold = holding && focus >= 0 && slot[focus] >= 0
            ? new Vector4((float)pos[focus].X, (float)pos[focus].Y, radius[focus] + 9, (float)Math.Clamp(holdT / holdDur, 0, 1)) : null;
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
            else if (Visit?.IsNew(nd.Id) == true) stateLine = "Lit this visit: can go out until you close";
            else if (AtPost && !night) stateLine = "Lit  ·  it can go out here";
            else stateLine = "Lit  ·  lamps go out at a town’s lamp-post, by day";
            if (!night && (AtPost || Visit?.IsNew(nd.Id) == true) && LampBook.CanUnlight(ch, nd.Id) is LampNo.None or LampNo.Holds)
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
            int k = i == focus && reveal.Count == 0 ? path.Count : LampAsk.PathTo(ch, w, nd.Id).Count;
            stateLine = k > 0 ? $"{k} lamps away  ·  you have {spare}" : "Out of reach";
            if (k > 0 && !night) prompts.Add(pad ? ("A", "Light the path") : ("Click", "Light the path"));
        }
        if (night || !Safe)
        {
            prompts.RemoveAll(p => p.Item2.StartsWith("Light"));
            if (state[i] != 0) stateLine = night ? stateLine + "  ·  by night the board is read-only" : stateLine + "  ·  lamps are lit out of a fight";
        }
        if (Said != null && i == focus) { stateLine = Said; stateC = LampInk.Gate; }
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
        var spot = LampBoardModel.PlaceCard(fx, fy, radius[focus] + 5, LampCard.Wd, h, discs, prot, labelsBoxes, new Box(0, 0, Size.X, Size.Y), hard: Keep);
        CardSpot = spot;
        var room = spot.Rect.Grow(LampBoardModel.LabelRoom);
        // on open, a label the card crowds is placed again around it (the card's room a blocker); on a hover, it hides
        // for as long as the card is there (labels don't jump about under the pointer)
        if (open && placedLabels.Any(p => p.Box.Overlaps(room))) { crowd = null; WriteLabels(stop == BoardStop.Valley, room); }
        if (crowd != room) { crowd = room; WriteInk(); }
        card.Position = new Vector2((float)spot.Rect.X0, (float)spot.Rect.Y0);
        card.Visible = true;
        cardOff = card.Position - new Vector2((float)fx, (float)fy);
        var g = GetGlobalRect().Position;
        if (open || Measuring) GD.Print($"LAMPBOARD card: {spot.Side} of {M.Nodes[focus].Id}, shift {spot.Shift}, overlap {spot.Score}, at {g.X + spot.Rect.X0:F0},{g.Y + spot.Rect.Y0:F0}-{g.X + spot.Rect.X1:F0},{g.Y + spot.Rect.Y1:F0}");
    }

    Vector2 cardOff;

    /// <summary>In motion the card rides with its lamp (it finds a new spot when the view settles).</summary>
    void RideCard()
    {
        if (!card.Visible || focus < 0) return;
        if (slot[focus] < 0 || !InView(focus, 0)) { card.Visible = false; return; }
        card.Position = new Vector2((float)pos[focus].X, (float)pos[focus].Y) + cardOff;
    }

    void SetUniforms(bool valley)
    {
        foreach (var mat in new[] { lampMat, roadMat, haloMat })
        {
            mat.SetShaderParameter("fe", Fe);
            mat.SetShaderParameter(PFeather, Feather);
            mat.SetShaderParameter(PValley, valley ? 1f : 0f);
            mat.SetShaderParameter(PFind, findOn ? 1f : 0f);
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

    /* ------------------------------------------------------------- interaction (§9, §10) -- */

    /// <summary>The visit (the page keeps it while the screen is open: §9's session undo).</summary>
    public LampSession Visit = null!;
    /// <summary>By night the board is read-only; in a fight nothing is lit; AtPost: by day at a town's lamp-post.</summary>
    public bool Night, Safe = true, AtPost;
    /// <summary>The lamps lit changed (the header's count, the tabs after a switch).</summary>
    public event Action? LampsChanged;
    /// <summary>The last refusal's words (null: none).</summary>
    public string? Said { get; private set; }

    bool[] found = [];
    bool findOn;
    BoardView labelView;
    float labelFade = 1;
    double still = 1, shakeT;
    bool settled = true, moved;
    /// <summary>A glide: board point (Bx, By) moves on screen from P0 to P1 while the scale goes S0 to S1, eased.</summary>
    (double Bx, double By, double P0x, double P0y, double P1x, double P1y, double S0, double S1, double T, double Dur)? glide;
    // the reveal: lit or put out in logic at once, shown one by one (a path 0.09 s apart, a branch from its tips, a switch)
    readonly Queue<(int I, bool On, double Wait)> reveal = new();
    double revealT;
    bool lighting;
    double lightT;
    bool holding;
    double holdT, holdDur;
    List<string> holdOrder = new();
    Func<bool>? holdHeld;
    int dragButton = -1, pressLamp = -1;
    Vector2 dragFrom, dragLast;
    bool dragMoved;
    static double bx0, bx1, by0, by1;

    double MinS => valleyS * 0.92;
    static double MaxS => LampBoardModel.LampScale * 1.12;
    bool Busy => reveal.Count > 0 || lighting;
    static double Ms(long t0) => (System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
    /// <summary>The slowest focus change this visit (ms).</summary>
    public double WorstFocusMs { get; private set; }
    static bool Measuring => SurvivorUnchained.Args.Has("lamps-measure") || SurvivorUnchained.Args.Has("lamps-moves");

    /// <summary>The view kept over the board: its center never leaves the lamps' bounds.</summary>
    BoardView Hold(BoardView v)
    {
        var m = M;
        if (bx0 == bx1) { bx0 = m.Nodes.Min(q => q.X); bx1 = m.Nodes.Max(q => q.X); by0 = m.Nodes.Min(q => q.Y); by1 = m.Nodes.Max(q => q.Y); }
        return v with { Cx = Math.Clamp(v.Cx, bx0, bx1), Cy = Math.Clamp(v.Cy, by0, by1), S = Math.Min(v.S, MaxS) };
    }

    BoardView At(double bx, double by, double px, double py, double s) => new(bx - (px - view.Sx) / s, by - (view.Sy - py) / s, s, view.Sx, view.Sy);

    void Glide(double bx, double by, double p1x, double p1y, double s1, double dur)
    {
        var (p0x, p0y) = view.Project(bx, by);
        glide = (bx, by, p0x, p0y, p1x, p1y, view.S, Math.Clamp(s1, MinS, MaxS), 0, dur);
    }

    /// <summary>The wheel: a continuous zoom about the cursor (×1.15 a notch, eased over 0.12 s).</summary>
    public void Wheel(double notches, Vector2 at)
    {
        double s1 = (glide is { } g ? g.S1 : view.S) * Math.Pow(1.15, notches);
        var (bx, by) = view.Unproject(at.X, at.Y);
        Glide(bx, by, at.X, at.Y, s1, 0.12);
    }

    /// <summary>LT / RT: the next stop out or in (Valley, Road, Lamp), 0.22 s, about the focus.</summary>
    public void ZoomStop(int dir)
    {
        double s = glide is { } g ? g.S1 : view.S;
        double[] stops = [valleyS, LampBoardModel.RoadScale, LampBoardModel.LampScale];
        double? to = dir > 0 ? stops.Where(x => x > s * 1.02).Cast<double?>().FirstOrDefault() : stops.Where(x => x < s / 1.02).Cast<double?>().LastOrDefault();
        if (to is not { } t) { Sound.Sfx.Hover(); return; }
        double px = Size.X / 2, py = Size.Y / 2;
        if (focus >= 0 && InView(focus, 0)) (px, py) = pos[focus];
        var (bx, by) = view.Unproject(px, py);
        Glide(bx, by, px, py, t, 0.22);
        Sound.Sfx.Hover();
    }

    /// <summary>A pan by screen px (a drag, the right stick, the keys).</summary>
    public void PanBy(Vector2 d)
    {
        if (d == Vector2.Zero || n == 0) return;
        glide = null;
        Relayout(view with { Cx = view.Cx - d.X / view.S, Cy = view.Cy + d.Y / view.S }, settle: false);
        moved = true;
    }

    /// <summary>The right stick let go: the focus comes to the lamp nearest the middle if it left the view.</summary>
    public void PanReleased()
    {
        if (n == 0 || (focus >= 0 && InView(focus, Feather))) return;
        var (cx, cy) = view.Unproject(Size.X / 2, Size.Y / 2);
        int best = -1;
        double bd = double.MaxValue;
        for (int i = 0; i < n; i++)
        {
            double d = Sq(M.Nodes[i].X - cx) + Sq(M.Nodes[i].Y - cy);
            if (d < bd) { bd = d; best = i; }
        }
        if (best >= 0) Focus_(best, follow: false);
    }

    bool InView(int i, double inset) => pos[i].X >= inset && pos[i].X <= Size.X - inset && pos[i].Y >= inset && pos[i].Y <= Size.Y - inset;

    /// <summary>The left stick (a screen direction, radians, y down): §10's step; none, a soft tick.</summary>
    public bool Step(double angle)
    {
        if (n == 0) return false;
        if (focus < 0) { Focus_(Frontier(), follow: true); return true; }
        int j = LampNav.Stick(M, focus, angle);
        if (j < 0) { Sound.Sfx.Hover(); return false; }
        Focus_(j, follow: true);
        return true;
    }

    /// <summary>LB / RB: the previous or next lamp she can light now, clockwise round her hearth.</summary>
    public void NextLamp(int dir)
    {
        var can = new List<int>();
        for (int i = 0; i < n; i++)
            if (state[i] == 1 && LampBook.CanLight(ch, w, M.Nodes[i].Id) is LampNo.None or LampNo.NoLamps) can.Add(i);
        int j = LampNav.Ring(M, Hearth, can, focus, dir);
        if (j < 0) { Deny("Nothing to light next to her lamps"); return; }
        Focus_(j, follow: true);
    }

    int Hearth => M.Index.GetValueOrDefault(Lamps.Start(ch.Archetype));

    /// <summary>Her frontier: Light my way's next lamp, else the first she can light, else her hearth.</summary>
    int Frontier()
    {
        if (LampBook.Suggest(ch, w) is { } id && M.Index.TryGetValue(id, out var i)) return i;
        for (int k = 0; k < n; k++) if (state[k] == 1) return k;
        return Hearth;
    }

    /// <summary>R3 / H: her hearth, or (from the hearth) her frontier, glided to the middle.</summary>
    public void Home()
    {
        if (n == 0) return;
        int h = Hearth, to = focus == h ? Frontier() : h;
        Focus_(to, follow: false);
        Glide(M.Nodes[to].X, M.Nodes[to].Y, Size.X / 2, Size.Y / 2, glide is { } g ? g.S1 : view.S, 0.25);
    }

    /// <summary>Focus a lamp from the pad or the keys (follow: the view keeps it out of the outer 22%, 0.18 s).</summary>
    public void Focus_(int i, bool follow)
    {
        if (i < 0) return;
        SetFocus(i);
        Sound.Sfx.Hover();
        if (!follow) return;
        double mx = Size.X * 0.22, my = Size.Y * 0.22;
        var (x, y) = pos[i];
        if (x >= mx && x <= Size.X - mx && y >= my && y <= Size.Y - my) return;
        // to 30% in from the edge it neared: the next step has room
        double tx = Math.Clamp(x, Size.X * 0.30, Size.X * 0.70), ty = Math.Clamp(y, Size.Y * 0.30, Size.Y * 0.70);
        Glide(M.Nodes[i].X, M.Nodes[i].Y, tx, ty, glide is { } g ? g.S1 : view.S, 0.18);
    }

    /// <summary>Find's Enter: the next of these lamps after the focus, glided to the middle.</summary>
    public bool FocusNext(IReadOnlyList<int> among)
    {
        if (among.Count == 0) return false;
        int at = -1;
        for (int k = 0; k < among.Count; k++) if (among[k] == focus) at = k;
        int j = among[(at + 1) % among.Count];
        Focus_(j, follow: false);
        Glide(M.Nodes[j].X, M.Nodes[j].Y, Size.X / 2, Size.Y / 2, glide is { } g ? g.S1 : view.S, 0.25);
        return true;
    }

    /// <summary>§6 Found: these lamps pulse white-gold and the rest drop to 45% (null: Find is off).</summary>
    public void SetFound(ICollection<int>? set)
    {
        if (n == 0) return;
        findOn = set != null;
        for (int i = 0; i < n; i++) found[i] = set != null && set.Contains(i);
        foreach (var mat in new[] { lampMat, roadMat, haloMat }) mat.SetShaderParameter(PFind, findOn ? 1f : 0f);
        WriteLamps(stop == BoardStop.Valley);
    }

    public void Deny(string? why = null)
    {
        Said = why;
        shakeT = 0.15;
        Sound.Sfx.Deny();
        if (why != null && focus >= 0 && CardOn) PlaceCard();
        if (why != null) GD.Print($"LAMPBOARD denied: {why}");
    }

    string? Refusal() => Night ? "By night the board is read-only" : !Safe ? "Lamps are lit out of a fight" : Busy ? "" : null;

    /// <summary>A or a click: light the focus; a far lamp, its whole path (as previewed) if the points allow.</summary>
    public bool LightFocus()
    {
        if (focus < 0) return false;
        if (Refusal() is { } r) { if (r != "") Deny(r); return false; }
        var id = M.Nodes[focus].Id;
        if (state[focus] == 0) { Deny(); return false; }
        var why = LampBook.CanLight(ch, w, id);
        List<string>? got = why == LampNo.None ? (Visit.Light(w, id) ? [id] : null) : why == LampNo.Dark ? Visit.LightPath(w, id) : null;
        if (got == null)
        {
            Deny(why == LampNo.NoLamps || (why == LampNo.Dark && path.Count > LampBook.Spare(ch, w)) ? "Not enough lamps to light" : null);
            return false;
        }
        Sound.Sfx.Pick();
        Show(got.Select(x => (M.Index[x], true)), 0.09);
        GD.Print($"LAMPBOARD lit {string.Join(",", got)} (spare {LampBook.Spare(ch, w)})");
        return true;
    }

    /// <summary>Y / Space: Light my way, the suggested lamps one by one, 0.09 s apart.</summary>
    public void LightMyWay()
    {
        if (Refusal() is { } r) { if (r != "") Deny(r); return; }
        if (LampBook.Suggest(ch, w) == null) { Deny(LampBook.Spare(ch, w) <= 0 ? "No lamps left to light" : "Nothing to light next to her lamps"); return; }
        lighting = true;
        lightT = 0;
    }

    /// <summary>X held or the right button held on the focus: put it out (0.35 s; 0.9 s and its branch, tips first, for a
    /// lamp others hang on). held: is the button still down.</summary>
    public void BeginOut(Func<bool> held)
    {
        if (focus < 0 || Busy) return;
        var no = Visit.CanOut(M.Nodes[focus].Id, Night, AtPost, out var order);
        if (no != OutNo.None)
        {
            Deny(no switch
            {
                OutNo.Night => "By night the board is read-only",
                OutNo.Free => "This lamp is hers for good",
                OutNo.Place => "Lamps go out by day at a town’s lamp-post",
                OutNo.Holds => AtPost ? "Others hang on it" : "Lamps lit after it hang on it: put those out first",
                _ => null,
            });
            return;
        }
        holding = true;
        holdT = 0;
        holdDur = order.Count > 1 ? 0.9 : 0.35;
        holdOrder = order;
        holdHeld = held;
        WriteInk();
    }

    void EndOut()
    {
        holding = false;
        if (!Visit.PutOut(holdOrder)) { Deny(); WriteInk(); return; }
        Sound.Sfx.Close();
        GD.Print($"LAMPBOARD out {string.Join(",", holdOrder)}");
        Show(holdOrder.Select(x => (M.Index[x], false)), holdOrder.Count > 1 ? Math.Min(0.06, 0.3 / holdOrder.Count) : 0);
    }

    /// <summary>1 2 3 or a coin: take up another layout (by day at a town's lamp-post). Out from the tips (0.25 s), in
    /// from her hearth (0.45 s).</summary>
    public bool Switch(int index, string? zone)
    {
        if (index == LampBook.State(ch).Active || Busy) return false;
        if (Night) { Deny("By night the board is read-only"); return false; }
        var before = lit.ToList();
        if (!LampBook.Switch(ch, index, w, zone)) { Deny("Layouts change by day at a town’s lamp-post"); return false; }
        var after = LampBook.Now(ch).Lit.Where(M.Index.ContainsKey).Select(x => M.Index[x]).ToHashSet();
        var outs = before.Where(i => !after.Contains(i)).OrderByDescending(i => steps[i] == int.MaxValue ? 0 : steps[i]).ToList();
        var hs = M.Steps([Hearth]);
        var ins = after.Where(i => !lit.Contains(i)).OrderBy(i => hs[i]).ToList();
        foreach (var i in outs) reveal.Enqueue((i, false, 0.25 / outs.Count));
        foreach (var i in ins) reveal.Enqueue((i, true, 0.45 / ins.Count));
        revealT = 0;
        ComputeDim();
        Sound.Sfx.Page();
        GD.Print($"LAMPBOARD switch to {index + 1}: {outs.Count} out, {ins.Count} in");
        LampsChanged?.Invoke();
        return true;
    }

    void Show(IEnumerable<(int I, bool On)> what, double every)
    {
        bool first = reveal.Count == 0;
        foreach (var (i, on) in what) reveal.Enqueue((i, on, every));
        if (first) revealT = 0;
        LampsChanged?.Invoke();
    }

    /// <summary>Each frame: the glide, the reveal, Light my way, the hold, the settle.</summary>
    void Tick(double dt)
    {
        if (n == 0) return;
        if (shakeT > 0) { shakeT = Math.Max(0, shakeT - dt); if (focus >= 0 && slot[focus] >= 0) WriteLamp(focus, slot[focus]); }
        if (glide is { } g)
        {
            g.T += dt;
            double t = Math.Min(1, g.T / g.Dur), e = 1 - Math.Pow(1 - t, 3);
            double s = g.S0 * Math.Pow(g.S1 / g.S0, e);
            glide = t >= 1 ? null : g;
            Relayout(At(g.Bx, g.By, g.P0x + (g.P1x - g.P0x) * e, g.P0y + (g.P1y - g.P0y) * e, s), settle: false);
            moved = true;
        }
        if (reveal.Count > 0)
        {
            revealT -= dt;
            bool any = false;
            while (reveal.Count > 0 && revealT <= 0)
            {
                var (i, on, wait) = reveal.Dequeue();
                if (on) lit.Add(i); else lit.Remove(i);
                revealT += wait;
                any = true;
            }
            if (reveal.Count == 0) { lit.Clear(); foreach (var id in LampBook.Now(ch).Lit) if (M.Index.TryGetValue(id, out var j)) lit.Add(j); }
            if (any) Restate();
        }
        if (lighting && reveal.Count == 0)
        {
            lightT -= dt;
            if (lightT <= 0)
            {
                lightT = 0.09;
                if (LampBook.Suggest(ch, w) is { } id && Visit.Light(w, id))
                {
                    lit.Add(M.Index[id]);
                    Sound.Sfx.Hover();
                    Restate();
                    LampsChanged?.Invoke();
                }
                else lighting = false;
            }
        }
        if (holding)
        {
            if (holdHeld?.Invoke() != true || focus < 0 || !lit.Contains(focus)) { holding = false; WriteInk(); }
            else { holdT += dt; if (holdT >= holdDur) EndOut(); else WriteInk(); }
        }
        if (labelFade < 1 && settled) { labelFade = Math.Min(1, labelFade + (float)dt / 0.12f); WriteInk(); }
        if (moved) { still = 0; settled = false; moved = false; }
        else
        {
            still += dt;
            if (!settled && still >= 0.12 && glide == null)
            {
                settled = true;
                long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
                if (Math.Abs(view.S / Math.Max(labelView.S, 1e-6) - 1) > 0.004) labelFade = 0;
                Relayout(view, settle: true);
                if (Measuring) GD.Print($"LAMPBOARD settle: {Ms(t0):F2} ms (labels {placedLabels.Count}, scale {view.S:F3}, stop {stop})");
            }
        }
    }

    /* ------------------------------------------------------------- the mouse -- */

    public override void _GuiInput(InputEvent e)
    {
        if (n == 0) return;
        switch (e)
        {
            case InputEventMouseButton { ButtonIndex: MouseButton.WheelUp or MouseButton.WheelDown, Pressed: true } wb:
                Wheel((wb.ButtonIndex == MouseButton.WheelUp ? 1 : -1) * (wb.Factor > 0 ? Math.Min(wb.Factor, 1) : 1), wb.Position);
                AcceptEvent();
                return;
            case InputEventMouseButton { ButtonIndex: MouseButton.Left or MouseButton.Middle } mb:
                if (mb.Pressed)
                {
                    pressLamp = mb.ButtonIndex == MouseButton.Left ? HitAt(mb.Position) : -1;
                    // the left button pans from empty board, the middle anywhere
                    dragButton = pressLamp < 0 ? (int)mb.ButtonIndex : -1;
                    dragFrom = dragLast = mb.Position;
                    dragMoved = false;
                }
                else
                {
                    if (mb.ButtonIndex == MouseButton.Left && pressLamp >= 0 && HitAt(mb.Position) == pressLamp)
                    {
                        if (focus != pressLamp) SetFocus(pressLamp);
                        LightFocus();
                    }
                    pressLamp = -1;
                    dragButton = -1;
                }
                AcceptEvent();
                return;
            case InputEventMouseButton { ButtonIndex: MouseButton.Right, Pressed: true } rb:
                int hit = HitAt(rb.Position);
                if (hit >= 0) { if (hit != focus) SetFocus(hit); BeginOut(() => Input.IsMouseButtonPressed(MouseButton.Right)); }
                AcceptEvent();
                return;
            case InputEventMouseMotion mm:
                if (dragButton >= 0)
                {
                    if (!dragMoved && mm.Position.DistanceTo(dragFrom) < 4) return;
                    dragMoved = true;
                    PanBy(mm.Position - dragLast);
                    dragLast = mm.Position;
                    return;
                }
                if (fixedFocus >= 0 || glide != null || holding) return;
                int h2 = HitAt(mm.Position);
                if (h2 != focus) SetFocus(h2);
                return;
        }
    }

    /// <summary>The wick opened or closed (§16 "C with the wick open"): the window takes height h (its foot at the wick
    /// band's top) and the view slides, zooming out only as far as it must, so her lit cluster sits in what is left (48 px
    /// in, 0.3 s). Closing keeps the view where it is. The focus is kept.</summary>
    public void Reframe(float h, bool wick)
    {
        CardOn = !wick;
        if (Math.Abs(h - Size.Y) < 0.5f || n == 0) { Size = new Vector2(Size.X, h); PlaceCard(); return; }
        var before = view;
        int f = focus;
        Size = new Vector2(Size.X, h);                     // (Resized: Rebuild)
        if (f >= 0 && f != focus) SetFocus(f);
        Relayout(before, settle: !wick);
        if (!wick) { PlaceCard(); return; }
        var keep = lit.Count > 0 ? lit.ToList() : new List<int> { Hearth };
        var to = M.Center(keep, new Box(0, 0, Size.X, Size.Y), Math.Min(before.S, LampBoardModel.RoadScale), 48);
        Glide(to.Cx, to.Cy, to.Sx, to.Sy, to.S, 0.3);
        GD.Print($"LAMPBOARD reframe: window {h:F0} high, scale {before.S:F3} to {Math.Clamp(to.S, MinS, MaxS):F3}, lit {lit.Count}");
    }

    /// <summary>A lamp's place in the viewport (for --lamps-moves' real mouse), or null when it is off the window.</summary>
    public Vector2? ScreenOf(string id)
    {
        if (!M.Index.TryGetValue(id, out var i) || i >= n || !InView(i, 0)) return null;
        return GetGlobalTransformWithCanvas() * new Vector2((float)pos[i].X, (float)pos[i].Y);
    }

    /// <summary>Empty board near a window point (no lamp under it), in the viewport, for a scripted drag.</summary>
    public Vector2 EmptyNear(Vector2 local)
    {
        for (int r = 0; r < 200; r += 12)
            for (int k = 0; k < 12; k++)
            {
                var q = local + new Vector2(Mathf.Cos(k * Mathf.Tau / 12), Mathf.Sin(k * Mathf.Tau / 12)) * r;
                if (q.X > 60 && q.Y > 60 && q.X < Size.X - 60 && q.Y < Size.Y - 60 && HitAt(q) < 0) return GetGlobalTransformWithCanvas() * q;
            }
        return GetGlobalTransformWithCanvas() * local;
    }

    /// <summary>The board point under a viewport point (the wheel's anchor check).</summary>
    public (double X, double Y) BoardAt(Vector2 global)
    {
        var q = GetGlobalTransformWithCanvas().AffineInverse() * global;
        return view.Unproject(q.X, q.Y);
    }

    int HitAt(Vector2 p)
    {
        var (bx, by) = view.Unproject(p.X, p.Y);
        return M.Hit(bx, by, i => (radius[i] + 4) / view.S, 40 / Math.Min(view.S, 1));
    }

    /// <summary>The focus's path preview: the fewest unlit lamps to it (none when it is lit or out of reach).</summary>
    void FindPath()
    {
        Array.Clear(onPath);
        path = new();
        pathFrom = -1;
        if (focus < 0 || lit.Contains(focus)) return;
        var m = M;
        if (reveal.Count == 0)
        {
            // the screen's own ask (LampAsk.PathTo): the preview is exactly what A or a click lights
            foreach (var id in LampAsk.PathTo(ch, w, m.Nodes[focus].Id)) if (m.Index.TryGetValue(id, out var j)) path.Add(j);
            if (path.Count > 0) pathFrom = m.Nodes[path[0]].Adj.Where(lit.Contains).DefaultIfEmpty(-1).First();
            if (pathFrom < 0) path.Clear();
        }
        else if (m.PathTo(lit, gateOk, focus) is { } pr) { path = pr.Path; pathFrom = pr.From; }
        foreach (var i in path) onPath[i] = true;
    }

    /// <summary>Hover or the pad moved the focus: the path preview, the lamps' marks, the ink and the card follow
    /// (the instances are rewritten, ~1200 writes; nothing else is rebuilt).</summary>
    public void SetFocus(int i)
    {
        if (i == focus || n == 0) return;
        long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
        focus = i;
        Said = null;
        holding = false;
        FindPath();
        bool valley = stop == BoardStop.Valley;
        for (int j = 0; j < n; j++) notch[j] = gateNotch[j] || (j == focus && state[j] == 3);
        Geometry();
        WriteRoads(path, pathFrom, valley);
        WriteLamps(valley);
        WriteInk();
        PlaceCard();
        double ms = Ms(t0);
        WorstFocusMs = Math.Max(WorstFocusMs, ms);
        if (Measuring) GD.Print($"LAMPBOARD focus: {(i >= 0 ? M.Nodes[i].Id : "-")} in {ms:F2} ms");
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
        Tick(delta);
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
    /// <summary>The Valley's focus ring (x, y, r); the put-out hold's ring (x, y, r, how far).</summary>
    public Vector3? Focus;
    public Vector4? Hold;

    public BoardInk() { MouseFilter = MouseFilterEnum.Ignore; }

    public void Clear() { Labels.Clear(); Glyphs.Clear(); }

    public override void _Draw()
    {
        foreach (var g in Glyphs)
            if (g.C.A > 0.01f) DrawTextureRect(Ui.Glyphs.Texture(g.Glyph, Math.Max(16, (int)Math.Ceiling(g.Rect.Size.X * 2)), Colors.White, line: true), g.Rect, false, g.C);
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
        if (Focus is { } f) DrawArc(new Vector2(f.X, f.Y), f.Z, 0, Mathf.Tau, 40, new Color("#e8c87a"), 1.5f, true);
        if (Hold is { } h)
        {
            // the hold: a smoke-dark track and the ember filling it clockwise from twelve
            var c = new Vector2(h.X, h.Y);
            DrawArc(c, h.Z, 0, Mathf.Tau, 48, new Color(0, 0, 0, 0.45f), 3.5f, true);
            if (h.W > 0.001f) DrawArc(c, h.Z, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * h.W, Math.Max(4, (int)(48 * h.W)), new Color("#ff9a3c"), 2.5f, true);
        }
    }
}
