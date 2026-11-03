using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// C's wick panel (docs/design/LAMPS_SCREEN_BRIEF.md §8, §16 "The wick panel has no box", "No floating card inside the
/// wick panel", "C with the wick open"; the mock is tools/uiforge/lamps_mock/mock/frames_c.py WICK_RECT and WICK_LAY,
/// skins/a.py wick(), braid(), skins/c.py tab_ring()). A smoked band over the page's foot, no box, no rim: on the left
/// the skill (its seat art, name, day rank, counts); the stem rising from the chosen tab bends into the three-ply braid,
/// whose strands part into the three rows (the strand's kind, three lead-ins, the flame-crowned Turn). The focused
/// node's row carries its name, line and state; the others their Turn. The nodes are the board's own glass
/// (shaders/ui_lamps_lamp.gdshader, kinds 16 wick and 17 Turn) and halos. "All learned" shows a short list instead.
/// Laid out in the page's C coordinates (the content rect's origin, (1030, 152) at 1080) less Top.
/// </summary>
public partial class LampWick : Control
{
    /// <summary>Where the control starts in the page's C coordinates, and its height (the band, its feather, the stem).</summary>
    public const float Top = 458, H = 276;
    /// <summary>The wick band's top in C coordinates (the board's window ends here while the wick is open).</summary>
    public const float BandTop = 482;
    // WICK_RECT (1040, 634)-(1866, 862) and WICK_LAY, here
    const float X0 = 10, Y0 = 24, X1 = 836, Y1 = 252;
    const float Kx = X0 + 256, Braid = 40, Lx0 = X0 + 350, PitchX = 60, Tx = X0 + 519, Row0 = Y0 + 44, PitchY = 64;
    const float Rw = 11, Rt = 17;
    /// <summary>The row's text: 14 px past the node's ring (the focus ring at r + 5).</summary>
    const float TextX = Tx + Rt + 5 + 14, TextR = X1 - 24;
    static readonly Color StrandGold = new("#f2c06b"), StrandPlan = new("#e2b066"), StrandSilver = new("#a7b1c2"),
        LitRim = new("#ffd98a"), Ember = new("#ffb04a");

    readonly CharacterData ch;
    readonly MultiMeshInstance2D lamps = new(), halos = new();
    readonly ShaderMaterial lampMat, haloMat;
    readonly WickLayer under, over;
    readonly ColorRect smoke;
    public string? Skill { get; private set; }
    /// <summary>All learned: the list of her learned skills she doesn't carry.</summary>
    public bool Listing { get; private set; }
    public bool Safe = true;
    /// <summary>The chosen tab's center and the first tab's x, in this control (the stem rises from it).</summary>
    public Vector2 TabAt;
    int fr, fc, listI;
    string? said;
    List<StrandDef> strands = new();
    List<string> learned = new();
    IReadOnlyList<string> plan = Array.Empty<string>();
    string[] path = [], litIds = [];
    int rank;
    /// <summary>A skill was picked from All learned (its wick opens).</summary>
    public event Action<string>? Picked;
    /// <summary>The plan changed.</summary>
    public event Action? Changed;

    public LampWick(CharacterData ch)
    {
        this.ch = ch;
        MouseFilter = MouseFilterEnum.Stop;
        smoke = new ColorRect { MouseFilter = MouseFilterEnum.Ignore, Color = Colors.White, Material = new ShaderMaterial { Shader = SmokeShader } };
        AddChild(smoke);
        AddChild(under = new WickLayer(DrawUnder));
        lampMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ui_lamps_lamp.gdshader") };
        haloMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ui_lamps_halo.gdshader") };
        foreach (var m in new[] { lampMat, haloMat }) { m.SetShaderParameter("win", new Vector4(-1e5f, -1e5f, 1e5f, 1e5f)); m.SetShaderParameter("feather", 1f); }
        foreach (var (mmi, mat) in new[] { (halos, haloMat), (lamps, lampMat) })
        {
            mmi.Material = mat;
            mmi.Multimesh = new MultiMesh
            {
                TransformFormat = MultiMesh.TransformFormatEnum.Transform2D, UseColors = true, UseCustomData = true,
                Mesh = Quad(), InstanceCount = 12, VisibleInstanceCount = 0,
            };
            AddChild(mmi);
        }
        AddChild(over = new WickLayer(DrawOver));
        Resized += () => { smoke.Size = Size; under.Size = Size; over.Size = Size; };
    }

    static ArrayMesh Quad()
    {
        var arr = new Godot.Collections.Array();
        arr.Resize((int)Mesh.ArrayType.Max);
        arr[(int)Mesh.ArrayType.Vertex] = new Vector2[] { new(-0.5f, -0.5f), new(0.5f, -0.5f), new(0.5f, 0.5f), new(-0.5f, 0.5f) };
        arr[(int)Mesh.ArrayType.TexUV] = new Vector2[] { new(0, 0), new(1, 0), new(1, 1), new(0, 1) };
        arr[(int)Mesh.ArrayType.Index] = new int[] { 0, 1, 2, 0, 2, 3 };
        var m = new ArrayMesh();
        m.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        return m;
    }

    /// <summary>C5: the band, the panel's ground ×0.65 (black at 35%), feathered 24 px at its top and foot and at the
    /// board window's sides.</summary>
    static Shader? smokeShader;
    static Shader SmokeShader => smokeShader ??= new Shader
    {
        Code = $$"""
            shader_type canvas_item;
            uniform vec2 size = vec2(846.0, 276.0);
            void fragment() {
                vec2 p = UV * size;
                float m = smoothstep({{Y0:F1}}, {{Y0 + 24:F1}}, p.y) * (1.0 - smoothstep({{Y1:F1}}, {{Y1 + 24:F1}}, p.y))
                    * smoothstep(0.0, 24.0, p.x) * smoothstep(0.0, 24.0, size.x - p.x);
                COLOR = vec4(0.0, 0.0, 0.0, 0.35 * m);
            }
            """,
    };

    /* ------------------------------------------------------------- what it shows -- */

    /// <summary>Open a skill's wick (focus: the first node the plan would take next, else the first lamp).</summary>
    public void Open(string skill)
    {
        Skill = skill;
        Listing = false;
        said = null;
        strands = Wicks.StrandsOf(skill).Take(3).ToList();
        Read();
        (fr, fc) = (0, 0);
        for (int r = 0; r < strands.Count; r++)
            for (int c = 0; c < 4; c++)
                if (!plan.Contains(Id(r, c)) && !litIds.Contains(Id(r, c)) && WickBook.CanPlan(ch, skill, Id(r, c)) == WickNo.None) { (fr, fc) = (r, c); goto found; }
        found:
        Visible = true;
        Write();
        GD.Print($"LAMPBOARD wick open {skill}: {strands.Count} strands, plan {plan.Count}, lit {litIds.Length}, focus {Id(fr, fc)}");
    }

    /// <summary>All learned: her learned skills with a wick that she doesn't carry.</summary>
    public void OpenList()
    {
        var carried = SkillBook.Carried(ch).Select(c => c.Id).ToHashSet();
        learned = ch.Skills.Where(s => !carried.Contains(s) && Wicks.Of(s) != null && Weapons.All.ContainsKey(s)).ToList();
        Skill = null;
        Listing = true;
        listI = 0;
        Visible = true;
        Write();
        GD.Print($"LAMPBOARD wick list: {learned.Count} learned, not carried");
    }

    void Read()
    {
        if (Skill == null) return;
        plan = WickBook.PlanOf(ch, Skill).ToList();
        path = WickBook.Path(ch, Skill);
        rank = SkillBook.Rank(ch);
        litIds = path.Take(Math.Max(0, rank)).ToArray();
    }

    string Id(int r, int c) => r < strands.Count ? strands[r].LampId(c + 1) : "";
    bool Lit(int r, int c) => litIds.Contains(Id(r, c));
    bool Planned(int r, int c) => plan.Contains(Id(r, c));
    bool TurnTaken => Skill != null && (plan.Any(id => Wicks.IsTurn(Skill, id)) || litIds.Any(id => Wicks.IsTurn(Skill, id)));
    bool Crossed(int r) => TurnTaken && !Planned(r, 3) && !Lit(r, 3);
    Vector2 At(int r, int c) => new(c < 3 ? Lx0 + c * PitchX : Tx, Row0 + r * PitchY);

    void Write()
    {
        var mm = lamps.Multimesh;
        var hm = halos.Multimesh;
        int k = 0, h = 0;
        if (!Listing)
            for (int r = 0; r < strands.Count; r++)
                for (int c = 0; c < 4; c++)
                {
                    bool turn = c == 3, lit = Lit(r, c), planned = Planned(r, c), crossed = turn && Crossed(r);
                    float R = turn ? Rt : Rw, Hh = R + 14;
                    var p = At(r, c);
                    int st = lit ? 0 : planned ? 1 : 2;
                    int flags = (crossed ? 1 : 0) | (r == fr && c == fc ? 2 : 0) | 8;
                    mm.SetInstanceTransform2D(k, new Transform2D(0, new Vector2(2 * Hh, 2 * Hh), 0, p));
                    mm.SetInstanceColor(k, new Color(turn ? 17 : 16, st, 1, flags));
                    mm.SetInstanceCustomData(k, new Color(R, ((r * 4 + c) * 0.137f) % 1f, 0, 0));
                    k++;
                    if (lit)
                    {
                        float HH = R * 1.8f * 3.2f;
                        hm.SetInstanceTransform2D(h, new Transform2D(0, new Vector2(2 * HH, 2 * HH), 0, p));
                        hm.SetInstanceColor(h, LampBoard.HaloLit);
                        hm.SetInstanceCustomData(h, new Color(R, 1, 0, 0));
                        h++;
                    }
                }
        mm.VisibleInstanceCount = k;
        hm.VisibleInstanceCount = h;
        under.QueueRedraw();
        over.QueueRedraw();
    }

    /* ------------------------------------------------------------- the hand -- */

    /// <summary>The stick, the D-pad or the arrows: walk the rows and the pitch (the list: up and down).</summary>
    public void Move(int dx, int dy)
    {
        if (Listing) { if (learned.Count > 0) { listI = Math.Clamp(listI + dy + dx, 0, learned.Count - 1); Sound.Sfx.Hover(); Write(); } return; }
        if (strands.Count == 0) return;
        int r = Math.Clamp(fr + dy, 0, strands.Count - 1), c = Math.Clamp(fc + dx, 0, 3);
        if (r == fr && c == fc) { Sound.Sfx.Hover(); return; }
        (fr, fc) = (r, c);
        said = null;
        Sound.Sfx.Hover();
        Write();
    }

    /// <summary>A / a click: plan the focused lamp, or take it out of the plan (the list: open the skill's wick).</summary>
    public bool Press()
    {
        if (Listing)
        {
            if (listI < 0 || listI >= learned.Count) return false;
            Sound.Sfx.Pick();
            Picked?.Invoke(learned[listI]);
            return true;
        }
        if (Skill == null || strands.Count == 0) return false;
        if (!Safe) return Deny("Change the plan somewhere safe");
        var id = Id(fr, fc);
        if (Planned(fr, fc))
        {
            var no = WickBook.Unplan(ch, Skill, id);
            if (no != WickNo.None) return Deny(BoardWords.Why(no).TrimEnd('.'));
        }
        else
        {
            if (Lit(fr, fc)) return Deny("Lit: Light my way chose it, the ember lit it");
            var no = WickBook.Plan(ch, Skill, id);
            if (no != WickNo.None) return Deny(no == WickNo.Turn ? "One Turn a skill" : BoardWords.Why(no).TrimEnd('.'));
        }
        Sound.Sfx.Pick();
        said = null;
        Read();
        Write();
        Changed?.Invoke();
        GD.Print($"LAMPBOARD wick {(Planned(fr, fc) ? "plan" : "unplan")} {id}: plan {string.Join(",", plan)}");
        return true;
    }

    /// <summary>Y / Space: lay Light my way's suggested strand into the plan, lamp by lamp, as far as the rules let it.</summary>
    public bool LightMyWay()
    {
        if (Skill == null || Wicks.Of(Skill) is not { } wk) return false;
        if (!Safe) return Deny("Change the plan somewhere safe");
        var s = Wicks.StrandsOf(Skill).FirstOrDefault(x => x.Id == wk.Suggested);
        if (s == null) return Deny("Light my way has no strand here");
        int added = 0;
        for (int n = 1; n <= Wicks.PerStrand; n++)
            if (WickBook.Plan(ch, Skill, s.LampId(n)) == WickNo.None) added++;
        if (added == 0) return Deny(TurnTaken && !plan.Contains(s.LampId(4)) ? "One Turn a skill" : "Light my way's strand is in the plan");
        Sound.Sfx.Pick();
        Read();
        Write();
        Changed?.Invoke();
        GD.Print($"LAMPBOARD wick light my way {s.Id}: +{added}, plan {string.Join(",", plan)}");
        return true;
    }

    bool Deny(string why)
    {
        said = why;
        Sound.Sfx.Deny();
        GD.Print($"LAMPBOARD wick no: {why}");
        over.QueueRedraw();
        under.QueueRedraw();
        return false;
    }

    public override void _GuiInput(InputEvent e)
    {
        switch (e)
        {
            case InputEventMouseMotion mm:
                if (Hit(mm.Position) is { } h && h != (Listing ? (listI, 0) : (fr, fc)))
                {
                    if (Listing) listI = h.R; else (fr, fc) = h;
                    said = null;
                    Write();
                }
                break;
            case InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left } mb:
                if (Hit(mb.Position) is { } hit)
                {
                    if (Listing) listI = hit.R; else (fr, fc) = hit;
                    Press();
                    AcceptEvent();
                }
                break;
        }
    }

    (int R, int C)? Hit(Vector2 p)
    {
        if (Listing)
        {
            for (int i = 0; i < learned.Count; i++) if (ListRect(i).HasPoint(p)) return (i, 0);
            return null;
        }
        for (int r = 0; r < strands.Count; r++)
            for (int c = 0; c < 4; c++)
                if (p.DistanceTo(At(r, c)) <= (c == 3 ? Rt : Rw) + 6) return (r, c);
        return null;
    }

    Rect2 ListRect(int i) => new(new Vector2(Lx0 - 20 + (i / 4) * 230, Y0 + 40 + (i % 4) * 34 - 20), new Vector2(220, 30));

    /// <summary>The focused node's id (the shots' report).</summary>
    public string FocusId => Listing ? (listI < learned.Count ? learned[listI] : "-") : Id(fr, fc);
    public int PlanCount => plan.Count;

    /* ------------------------------------------------------------- drawing -- */

    static string Roman(int n) => n switch { 1 => "I", 2 => "II", 3 => "III", 4 => "IV", 5 => "V", 6 => "VI", 7 => "VII", 8 => "VIII", 9 => "IX", 10 => "X", 11 => "XI", 12 => "XII", _ => n.ToString() };
    static string Ord(int n) => n + (n % 100 is 11 or 12 or 13 ? "th" : (n % 10) switch { 1 => "st", 2 => "nd", 3 => "rd", _ => "th" });

    string NameOf(int r, int c) => c == 3 ? strands[r].TurnDef.Name : $"{strands[r].TurnDef.Name} {Roman(c + 1)}";

    string StateOf(int r, int c)
    {
        if (said != null && r == fr && c == fc) return said;
        var id = Id(r, c);
        int pi = plan.ToList().IndexOf(id), at = Array.IndexOf(path, id);
        bool pad = Play.Controls.Instance?.UsingPad == true;
        if (Lit(r, c)) return pi >= 0 ? $"Lit · {Ord(pi + 1)} in the plan · the ember lit it at day rank {Roman(at + 1)}" : $"Lit · Light my way chose it · day rank {Roman(at + 1)}";
        if (pi >= 0) return at >= 0 ? $"Planned · {Ord(pi + 1)} · the ember lights it at day rank {Roman(at + 1)}" : $"Planned · {Ord(pi + 1)} in the plan";
        if (c == 3 && Crossed(r)) return "One Turn a skill";
        var no = WickBook.CanPlan(ch, Skill!, id);
        if (no == WickNo.None) return pad ? "A: plan it next" : "Click: plan it next";
        return no == WickNo.Turn ? "One Turn a skill" : BoardWords.Why(no).TrimEnd('.');
    }

    void DrawUnder(Control ci)
    {
        var fs = LampInk.F("alegreya-sans-400");
        if (Listing) { DrawList(ci); DrawStem(ci, new Vector2(Lx0 - 34, Y0 + 40)); return; }
        if (Skill == null) return;
        // the left block: the seat, the name, the day rank, the counts
        var seat = new Vector2(X0 + 46, Y0 + 50);
        string art = Weapons.All.TryGetValue(Skill, out var wd) ? wd.Art : "";
        WickTabs.Seat(ci, seat, 56, 0, art, wd != null ? ItemViews.SchoolColors[wd.School] : LampInk.Gold);
        LampInk.Text(ci, LampInk.F("cinzel-700", 1), 22, X0 + 18, Y0 + 118, (wd?.Name ?? Skill).ToUpperInvariant(), LampInk.Ink);
        LampInk.Text(ci, LampInk.F("alegreya-sans-700", 2), 13, X0 + 18, Y0 + 140, $"DAY RANK {Roman(Math.Max(1, rank))}", LampInk.Gold);
        LampInk.Text(ci, fs, 14, X0 + 18, Y0 + 160, $"{litIds.Length} of {Wicks.LampCount} lit · {plan.Count} planned", LampInk.Dim);
        // the stem: up from the chosen tab, a 20 px bend, into the braid's knot
        var knot = new Vector2(Kx, Row0 + PitchY);
        DrawStem(ci, knot);
        // the braid and its parting
        var kinds = Enumerable.Range(0, 3).Select(r => r < strands.Count && Lit(r, 0) ? 0 : r < strands.Count && Planned(r, 0) ? 1 : 2).ToArray();
        DrawBraid(ci, knot, kinds);
        // the rows
        var fk = LampInk.F("alegreya-sans-700", 1);
        for (int r = 0; r < strands.Count; r++)
        {
            float ry = Row0 + r * PitchY;
            var s = strands[r];
            bool sug = Wicks.Of(Skill)?.Suggested == s.Id;
            LampInk.Text(ci, fk, 13, Lx0 - 20, ry - 19, s.Kind.ToString().ToUpperInvariant() + (sug ? " · LIGHT MY WAY" : ""), LampInk.Dim with { A = 0.95f });
            for (int c = 0; c < 3; c++)
            {
                var a = At(r, c); var b = At(r, c + 1);
                float ra = Rw + 2, rb = (c == 2 ? Rt : Rw) + 2;
                bool la = Lit(r, c), lb = Lit(r, c + 1), pa = Planned(r, c), pb = Planned(r, c + 1);
                int kind = la && lb ? 0 : (la || pa) && pb ? 1 : 2;
                Road(ci, a + new Vector2(ra, 0), b - new Vector2(rb, 0), kind);
            }
            DrawRowText(ci, r, ry);
        }
        if (LampAsk.Sum(ch, Skill, false) is { } sum)
        {
            string line = $"{sum.Stat} {sum.Total:0} = " + string.Join(" · ", sum.Parts.Select(p => $"{p.What} {p.Value}"));
            LampInk.Text(ci, LampInk.F("alegreya-sans-500"), 14, X0 + 532, Y1 - 12, line, LampInk.Body with { A = 0.95f }, 0);
        }
    }

    void DrawRowText(Control ci, int r, float ry)
    {
        var fn = LampInk.F("alegreya-700");
        var fl = LampInk.F("alegreya-400");
        var fs = LampInk.F("alegreya-sans-400");
        float w = TextR - TextX;
        if (r == fr)
        {
            string line = Wicks.Text(Skill!, Id(r, fc));
            var lines = LampInk.Wrap(line, fl, 14, w);
            if (lines.Count > 2) { lines = lines.Take(2).ToList(); lines[1] = Ellipsize(lines[1] + "…", fl, 14, w); }
            LampInk.Text(ci, fn, 18, TextX, ry - 16, NameOf(r, fc), LampInk.Ink);
            for (int j = 0; j < lines.Count; j++) LampInk.Text(ci, fl, 14, TextX, ry + 1 + j * 16, lines[j], LampInk.Body with { A = 0.92f });
            float sy = ry + 1 + (lines.Count - 1) * 16 + 17;
            var st = LampInk.Wrap(StateOf(r, fc), fs, 13, w);
            for (int j = 0; j < Math.Min(2, st.Count); j++) LampInk.Text(ci, fs, 13, TextX, sy + j * 15, st[j], said != null ? LampInk.Red : LampInk.Focus);
            return;
        }
        bool crossed = Crossed(r);
        string tl = crossed ? "One Turn a skill" : Wicks.Text(Skill!, Id(r, 3));
        LampInk.Text(ci, fn, 18, TextX, ry - 2, strands[r].TurnDef.Name, crossed ? LampInk.Dim : LampInk.Ink);
        var ls = LampInk.Wrap(tl, fl, 14, w);
        if (ls.Count > 0) LampInk.Text(ci, fl, 14, TextX, ry + 16, ls.Count > 1 ? Ellipsize(ls[0] + "…", fl, 14, w) : ls[0], (crossed ? LampInk.Dim : LampInk.Body) with { A = 0.9f });
    }

    static string Ellipsize(string s, Font f, int px, float maxw)
    {
        if (LampInk.W(f, s, px) <= maxw) return s;
        s = s.TrimEnd('…');
        while (s.Length > 1 && LampInk.W(f, s + "…", px) > maxw) s = s[..^1];
        return s.TrimEnd(' ', ',', ';', '·') + "…";
    }

    void DrawList(Control ci)
    {
        var fn = LampInk.F("alegreya-700");
        LampInk.Text(ci, LampInk.F("alegreya-sans-700", 1), 13, Lx0 - 20, Y0 + 14, "LEARNED, NOT CARRIED", LampInk.Dim);
        if (learned.Count == 0)
        {
            LampInk.Text(ci, LampInk.F("alegreya-400-italic"), 15, Lx0 - 20, Y0 + 50, "Every skill she has learned is in her hands.", LampInk.Dim);
            return;
        }
        for (int i = 0; i < learned.Count; i++)
        {
            var rc = ListRect(i);
            string art = Weapons.All[learned[i]].Art;
            var c = rc.Position + new Vector2(14, rc.Size.Y / 2);
            WickTabs.Seat(ci, c, 26, i % 6, art, ItemViews.SchoolColors[Weapons.All[learned[i]].School]);
            LampInk.Text(ci, fn, 17, c.X + 22, c.Y + 6, Weapons.All[learned[i]].Name, i == listI ? LampInk.Ink : LampInk.Body with { A = 0.85f });
            if (i == listI) ci.DrawArc(c, 16, 0, Mathf.Tau, 48, LampInk.Focus, 1.5f, true);
        }
    }

    /// <summary>The stem (skins/c.py _stem_dist): one continuous gold line up from the chosen tab, bending on a 20 px
    /// radius into the knot. From a tab right of the knot it runs left under the rows, then up.</summary>
    void DrawStem(Control ci, Vector2 knot)
    {
        var pts = new List<Vector2>();
        float tx = TabAt.X, top = TabAt.Y - 28 - 2.5f;
        const float rad = 20;
        if (tx + rad <= knot.X)
        {
            pts.Add(new Vector2(tx, top));
            Arc(pts, new Vector2(tx + rad, knot.Y + rad), rad, Mathf.Pi, 1.5f * Mathf.Pi);
            pts.Add(knot);
        }
        else
        {
            // under the rows: up from the tab, left along the band's foot, up beside the left block, into the knot
            float ch = Y1 + 3, rx = knot.X - 30, r2 = Math.Min(8, (top - ch) / 2);
            pts.Add(new Vector2(tx, top));
            Arc(pts, new Vector2(tx - r2, ch + r2), r2, 0, -0.5f * Mathf.Pi);
            Arc(pts, new Vector2(rx + r2, ch - r2), r2, 0.5f * Mathf.Pi, Mathf.Pi);
            Arc(pts, new Vector2(rx + rad, knot.Y + rad), rad, Mathf.Pi, 1.5f * Mathf.Pi);
            pts.Add(knot);
        }
        var arr = pts.ToArray();
        ci.DrawPolyline(arr, Ember with { A = 0.10f }, 8, true);
        ci.DrawPolyline(arr, Ember with { A = 0.22f }, 4.5f, true);
        ci.DrawPolyline(arr, LampInk.Focus, 2, true);
    }

    static void Arc(List<Vector2> pts, Vector2 c, float r, float a0, float a1)
    {
        for (int k = 0; k <= 10; k++) { float a = Mathf.Lerp(a0, a1, k / 10f); pts.Add(c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r); }
    }

    /// <summary>The three-ply braid (skins/a.py braid()): a plait out of the knot for 40 px, a herringbone of strand
    /// pieces, each outer one over the middle; then the three strands part into the rows.</summary>
    void DrawBraid(Control ci, Vector2 knot, int[] kinds)
    {
        Color Col(int k) => k == 0 ? StrandGold : k == 1 ? StrandPlan : StrandSilver with { A = 0.8f };
        float x0b = knot.X + 1, x1b = knot.X + Braid, xEnd = Lx0 - 13;
        float[] exits = [knot.Y - 2.6f, knot.Y, knot.Y + 2.6f];
        for (int r = 0; r < 3; r++)
        {
            float ry = Row0 + r * PitchY;
            var a = new Vector2(x1b - 2, exits[r]); var b = new Vector2(x1b + (xEnd - x1b) * 0.45f, exits[r]);
            var c = new Vector2(xEnd - (xEnd - x1b) * 0.55f, ry); var d = new Vector2(xEnd, ry);
            var pts = new Vector2[33];
            for (int k = 0; k <= 32; k++)
            {
                float t = k / 32f, u = 1 - t;
                pts[k] = u * u * u * a + 3 * u * u * t * b + 3 * u * t * t * c + t * t * t * d;
            }
            if (kinds[r] == 0) ci.DrawPolyline(pts, Ember with { A = 0.16f }, 6, true);
            ci.DrawPolyline(pts, Col(kinds[r]) with { A = kinds[r] == 2 ? 0.75f : 0.95f }, 2, true);
        }
        const float A = 3.9f, step = 3.6f, plen = 8f, sw = 3f;
        int n = (int)((x1b - plen - x0b) / step) + 1;
        for (int k = 0; k < n; k++)
        {
            float x = x0b + k * step;
            bool up = k % 2 == 0;
            var pa = new Vector2(x, up ? knot.Y - A : knot.Y + A);
            var pb = new Vector2(x + plen, up ? knot.Y + 1.4f : knot.Y - 1.4f);
            var col = Col(kinds[new[] { 0, 2, 1 }[k % 3]]);
            ci.DrawLine(pa, pb, LampInk.Dark with { A = 0.9f }, sw + 1.6f, true);
            ci.DrawLine(pa, pb, col * new Color(0.78f, 0.78f, 0.78f), sw, true);
            ci.DrawLine(pa.Lerp(pb, 0.25f), pa.Lerp(pb, 0.75f), col.Lightened(0.25f), 1.1f, true);
        }
        ci.DrawCircle(knot, 3.4f, LitRim, true, -1, true);
        ci.DrawArc(knot, 3.4f, 0, Mathf.Tau, 24, new Color("#7a5a26") with { A = 0.6f }, 0.8f, true);
    }

    /// <summary>A road between two nodes: lit (gold, glowing), the plan's (gold dashes) or cold (thin silver).</summary>
    static void Road(Control ci, Vector2 a, Vector2 b, int kind)
    {
        if (kind == 0)
        {
            ci.DrawLine(a, b, Ember with { A = 0.18f }, 7, true);
            ci.DrawLine(a, b, StrandGold, 2.6f, true);
        }
        else if (kind == 1)
        {
            float len = a.DistanceTo(b);
            var u = (b - a) / Math.Max(len, 1);
            for (float t = 0; t < len; t += 9) ci.DrawLine(a + u * t, a + u * Math.Min(len, t + 5), StrandPlan, 2.4f, true);
        }
        else ci.DrawLine(a, b, StrandSilver with { A = 0.38f }, 1.4f, true);
    }

    void DrawOver(Control ci)
    {
        if (Listing || Skill == null) return;
        var f = LampInk.F("alegreya-sans-800");
        for (int r = 0; r < strands.Count; r++)
            for (int c = 0; c < 4; c++)
            {
                int pi = plan.ToList().IndexOf(Id(r, c));
                if (pi < 0) continue;
                var p = At(r, c) + new Vector2(-16, -16 + 4.5f);
                LampInk.Text(ci, f, 12, p.X, p.Y, (pi + 1).ToString(), LampInk.Gold, 0, 3, 1f);
            }
    }
}

/// <summary>A canvas layer drawn by a callback (the wick band's type under the glass, the plan numbers over it).</summary>
public partial class WickLayer : Control
{
    readonly Action<Control> draw;
    public WickLayer(Action<Control> draw) { this.draw = draw; MouseFilter = MouseFilterEnum.Ignore; }
    public override void _Draw() => draw(this);
}
