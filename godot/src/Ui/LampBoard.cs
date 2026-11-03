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
    const int MaxHalos = 90, MaxLabels = 64, MaxChips = 24;

    static LampBoardModel? model;
    public static LampBoardModel M => model ??= LampBoardModel.FromJson(SurvivorUnchained.Core.Json.ReadContent("lamps_v2.json"));

    static readonly StringName PWin = "win", PFeather = "feather", PValley = "valley", PFind = "find_on", PPalm = "palm",
        PSize = "size", PGlowC = "glow_c", PGlowR = "glow_r", PRingC = "ring_c", PRings = "rings";

    readonly CharacterData ch;
    readonly WorldState? w;
    readonly MultiMeshInstance2D roads = new(), halos = new(), lamps = new();
    readonly ColorRect page = new() { MouseFilter = MouseFilterEnum.Ignore, Color = Colors.White };
    readonly ShaderMaterial lampMat, roadMat, haloMat, pageMat;
    readonly Label[] labels = new Label[MaxLabels], chips = new Label[MaxChips];
    LabelSettings? labelRoad, labelValley, chipSet;

    // the board's state, as of the last Rebuild
    int n;
    int[] state = [], steps = [], slot = [];
    bool[] dim = [], onPath = [], notch = [];
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
        for (int i = 0; i < MaxLabels; i++) AddChild(labels[i] = new Label { Visible = false, MouseFilter = MouseFilterEnum.Ignore });
        for (int i = 0; i < MaxChips; i++) AddChild(chips[i] = new Label { Visible = false, MouseFilter = MouseFilterEnum.Ignore });
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

    /// <summary>--lamps-demo n: light n of Light my way's lamps (raising her level if she runs out), once a run.</summary>
    public static void Demo(CharacterData ch, WorldState? w)
    {
        if (demoDone || SurvivorUnchained.Args.Get("lamps-demo") is not { } s || !int.TryParse(s, out var want)) return;
        demoDone = true;
        int got = 0, guard = 0;
        while (got < want && guard++ < want * 4)
        {
            if (LampBook.Spare(ch, w) <= 0) { ch.Level++; continue; }
            if (LampBook.Suggest(ch, w) is not { } id || !LampBook.Light(ch, w, id)) break;
            got++;
        }
        GD.Print($"LAMPBOARD demo: lit {got} of {want} (level {ch.Level}, {LampBook.Now(ch).Lit.Count} lit)");
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
        fixedFocus = fid == "auto" ? AutoFocus(GateOk) : fid != null && m.Index.TryGetValue(fid, out var fi) ? fi : -1;
        focus = fixedFocus;
        List<int> path = new();
        int pathFrom = -1;
        if (focus >= 0 && !lit.Contains(focus) && m.PathTo(lit, GateOk, focus) is { } pr) { path = pr.Path; pathFrom = pr.From; }
        foreach (var i in path) onPath[i] = true;

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
        if (focus >= 0 && state[focus] == 3) notch[focus] = true;

        WriteRoads(path, pathFrom, valley);
        WriteLamps(valley);
        WritePage(valley);
        WriteLabels(valley);
        SetUniforms(valley);
        double ms = (System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
        var g = GetGlobalRect();
        GD.Print($"LAMPBOARD rebuild: {ms:F1} ms, stop {stop} scale {view.S:F3} (valley {valleyS:F3}), lit {lit.Count}, focus {(focus >= 0 ? m.Nodes[focus].Id : "-")}, path {path.Count}, window {g.Position.X:F0},{g.Position.Y:F0}-{g.End.X:F0},{g.End.Y:F0}");
    }

    /// <summary>--lamps-focus auto: a far lamp worth a path preview (a notable or blue 3 steps out, its road open, nearest
    /// her lit lamps' middle).</summary>
    int AutoFocus(Func<int, bool> gateOk)
    {
        var m = M;
        if (lit.Count == 0) return -1;
        double cx = lit.Average(i => m.Nodes[i].X), cy = lit.Average(i => m.Nodes[i].Y);
        return Enumerable.Range(0, n).Where(i => steps[i] >= 2 && steps[i] <= 4 && gateOk(i) && m.Nodes[i].Kind is not ("small" or "attribute"))
            .Where(i => m.PathTo(lit, gateOk, i) is { Path.Count: >= 2 })
            .OrderBy(i => Sq(m.Nodes[i].X - cx) + Sq(m.Nodes[i].Y - cy)).DefaultIfEmpty(-1).First();
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
                    | (notch[i] ? 32 : 0);
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

    static Font LabelFont(int px)
    {
        return new FontVariation { BaseFont = Style.DisplayLight, SpacingGlyph = (int)Math.Round(px * 0.16) };
    }

    void WriteLabels(bool valley)
    {
        int px = LampBoardModel.LabelPx(stop);
        var dark = new Color("#07080b");
        labelRoad ??= new LabelSettings { Font = LabelFont(15), FontSize = 15, FontColor = new Color("#d8cfbd") with { A = 0.75f },
            OutlineSize = 4, OutlineColor = dark with { A = 0.55f }, ShadowSize = 8, ShadowColor = dark with { A = 0.6f }, ShadowOffset = Vector2.Zero };
        labelValley ??= new LabelSettings { Font = LabelFont(16), FontSize = 16, FontColor = new Color("#d8cfbd") with { A = 0.75f },
            OutlineSize = 6, OutlineColor = dark with { A = 0.6f }, ShadowSize = 8, ShadowColor = dark with { A = 0.6f }, ShadowOffset = Vector2.Zero };
        chipSet ??= new LabelSettings { Font = Style.UiHeavy, FontSize = LampBoardModel.ChipPx, FontColor = new Color("#cdae72") };
        var set = valley ? labelValley : labelRoad;
        var font = set.Font;
        var discs = new List<(double, double, double)>();
        for (int i = 0; i < n; i++)
            if (slot[i] >= 0) discs.Add((pos[i].X, pos[i].Y, radius[i] + 5));
        var allowed = new Box(40, 40, Size.X - 40, Size.Y - 40);
        var placed = M.PlaceLabels(view, stop, discs, allowed, [], (t, p) => font.GetStringSize(t, HorizontalAlignment.Left, -1, p).X, lit);
        float asc = font.GetAscent(px), capH = (float)Math.Round(px * 0.70);
        for (int k = 0; k < MaxLabels; k++)
        {
            var lb = labels[k];
            if (k >= placed.Count) { lb.Visible = false; continue; }
            var pl = placed[k];
            float tw = font.GetStringSize(pl.Text, HorizontalAlignment.Left, -1, px).X;
            lb.LabelSettings = set;
            lb.Text = pl.Text;
            lb.Position = new Vector2((float)pl.X - tw / 2, (float)pl.Y + capH / 2 - asc);
            lb.Size = Vector2.Zero;
            lb.Visible = true;
        }
        // the gate numerals in their notches
        int c = 0;
        for (int i = 0; i < n && c < MaxChips; i++)
        {
            if (!notch[i] || slot[i] < 0 || stop == BoardStop.Valley) continue;
            var lb = chips[c++];
            float R = radius[i];
            var txt = M.Nodes[i].Gate.ToString();
            float tw = Style.UiHeavy.GetStringSize(txt, HorizontalAlignment.Left, -1, LampBoardModel.ChipPx).X;
            float cx = (float)pos[i].X + R * 0.72f + 5f, cy = (float)pos[i].Y + R * 0.72f + 4f;
            lb.LabelSettings = chipSet;
            lb.Text = txt;
            lb.Position = new Vector2(cx - tw / 2 + 0.5f, cy + LampBoardModel.ChipPx * 0.36f - Style.UiHeavy.GetAscent(LampBoardModel.ChipPx));
            lb.Size = Vector2.Zero;
            lb.Modulate = Colors.White with { A = fade[i] * EdgeMask(pos[i].X, pos[i].Y) };
            lb.Visible = true;
        }
        for (; c < MaxChips; c++) chips[c].Visible = false;
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

    void SetFocus(int i)
    {
        int old = focus;
        focus = i;
        foreach (var j in new[] { old, i })
        {
            if (j < 0 || slot[j] < 0) continue;
            radius[j] = (float)(LampBoardModel.Diameter(M.Nodes[j].Kind, view.S, valleyS) / 2 * (j == focus ? 1.1 : 1.0));
            WriteLamp(j, slot[j]);
        }
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
            foreach (var c in GetChildren()) if (c is CanvasItem ci && ci is not Label) ci.Visible = true;
            WriteLabels(stop == BoardStop.Valley);
            double ms = cpuTicks * 1000.0 / System.Diagnostics.Stopwatch.Frequency / 246;
            int labelsOn = labels.Count(l => l.Visible) + chips.Count(l => l.Visible);
            GD.Print($"LAMPBOARD measure: draw calls with board {dcOn / (double)dcN:F1}, without {dcOff / 120.0:F1}, board {(dcOn / (double)dcN) - dcOff / 120.0:F1} " +
                     $"(labels+chips {labelsOn}); _Process {ms * 1000:F1} us/frame; allocated {allocBytes} B over 246 frames; " +
                     $"viewport GPU {gpuOn / 120:F3} vs {gpuOff / 120:F3} ms, render CPU {cpuOn / 120:F3} vs {cpuOff / 120:F3} ms; " +
                     $"process {Performance.GetMonitor(Performance.Monitor.TimeProcess) * 1000:F2} ms, fps {Performance.GetMonitor(Performance.Monitor.TimeFps):F0}");
            measureFrame = -1;
        }
    }
}
