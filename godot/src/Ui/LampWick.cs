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
    float X0 = 10, Y0 = 24, X1 = 836, Y1 = 252;
    float Kx = 10 + 256, Braid = 40, Lx0 = 10 + 350, PitchX = 60, Tx = 10 + 519, Row0 = 24 + 44, PitchY = 64, Pad = 18;
    const float Rw = 11, Rt = 17;
    /// <summary>The row's text: 14 px past the node's ring (the focus ring at r + 5).</summary>
    float TextX = 10 + 519 + Rt + 5 + 14, TextR = 836 - 24;
    /// <summary>A's panel (§16): smoke at 88% fading over 24 px at its edges, no box; the mock's A layout (frames.py
    /// wick_spec), its text column as wide as the panel allows (judge r2: the Turn's state line wrapped at 214 px).</summary>
    public bool Wide { get; private set; }

    public void SetWide(Vector2 size)
    {
        Wide = true;
        X0 = 0; Y0 = 0; X1 = size.X; Y1 = size.Y;
        // (p5b: the knot clear of the left block, whose type is fitted to 142 px: the braid ran over "DAY RANK VI" and the
        // stem through the counts at Kx 140)
        Kx = 200; Braid = 36; Lx0 = 270; PitchX = 50; Tx = 420; Row0 = 56; PitchY = 76; Pad = 24;
        TextX = Tx + 31; TextR = X1 - 24;
        var sm = new ShaderMaterial { Shader = WideSmoke }; sm.SetShaderParameter("size", size); smoke.Material = sm;
        Size = size;
        Fit();
    }

    static Shader? wideSmoke;
    static Shader WideSmoke => wideSmoke ??= new Shader
    {
        Code = """
            shader_type canvas_item;
            uniform vec2 size = vec2(780.0, 282.0);
            void fragment() {
                vec2 p = UV * size;
                float e = min(min(p.x, size.x - p.x), min(p.y, size.y - p.y));
                COLOR = vec4(0.051, 0.063, 0.082, 0.88 * smoothstep(0.0, 24.0, e));
            }
            """,
    };
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
        foreach (var m in new[] { lampMat, haloMat }) { m.SetShaderParameter("win", new Vector4(-1e5f, -1e5f, 1e5f, 1e5f)); m.SetShaderParameter("feather", 1f); m.SetShaderParameter("still", LampMotion.Still ? 1f : 0f); }
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
        Resized += Fit;
    }

    void Fit() { smoke.Size = Size; under.Size = Size; over.Size = Size; }
    // (A sizes the panel before it is in the tree, where Resized does not fire)
    public override void _Ready() => Fit();

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
                float m = smoothstep(24.0, 48.0, p.y) * (1.0 - smoothstep(252.0, 276.0, p.y))
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
        // the mock's rows: the calling's strand (Light my way's) first, then shape, school, bind
        strands = Wicks.StrandsOf(skill).OrderBy(x => x.Kind switch { StrandKind.Calling => 0, StrandKind.Shape => 1, StrandKind.School => 2, _ => 3 }).Take(3).ToList();
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
        deltaOf.Clear();
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
                    mm.SetInstanceColor(k, new Color(turn ? 17 : 16, st, LampMotion.None, flags + 0.999f));
                    mm.SetInstanceCustomData(k, new Color(R, ((r * 4 + c) * 0.137f) % 1f, 0, 0));
                    k++;
                    if (lit)
                    {
                        float HH = R * 1.8f * 3.2f;
                        hm.SetInstanceTransform2D(h, new Transform2D(0, new Vector2(2 * HH, 2 * HH), 0, p));
                        hm.SetInstanceColor(h, LampBoard.HaloLit);
                        hm.SetInstanceCustomData(h, new Color(R, 1, 0, LampMotion.None));
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
        Sound.Sfx.Lamps(fc == 3 ? "wick_turn" : "wick_plan");
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
        if (Lit(r, c)) return pi >= 0 ? $"Lit · {Ord(pi + 1)} in the plan · day rank {Roman(at + 1)}" : $"Lit · day rank {Roman(at + 1)}";
        if (pi >= 0) return at >= 0 ? $"Planned · {Ord(pi + 1)} · lights at day rank {Roman(at + 1)}" : $"Planned · {Ord(pi + 1)} in the plan";
        if (c == 3 && Crossed(r)) return "One Turn a skill";
        var no = WickBook.CanPlan(ch, Skill!, id);
        if (no == WickNo.None) return "";
        return no == WickNo.Turn ? "One Turn a skill" : BoardWords.Why(no).TrimEnd('.');
    }

    void DrawUnder(Control ci)
    {
        var fs = LampInk.F("alegreya-sans-400");
        if (Listing) { DrawList(ci); DrawStem(ci, new Vector2(Lx0 - 34, Y0 + 40)); return; }
        if (Skill == null) return;
        // the left block: the seat, the name, the day rank, the counts
        var seat = new Vector2(X0 + 46, Y0 + 50);
        string art = Weapons.All.TryGetValue(Skill, out var wd) ? Glyphs.ForSkill(Skill, wd.Art) : "";
        WickTabs.Seat(ci, seat, 56, 0, art, wd != null ? ItemViews.SchoolColors[wd.School] : LampInk.Gold);
        string nm = (wd?.Name ?? Skill).ToUpperInvariant();
        var fnm = LampInk.F("cinzel-700", 1);
        int nmPx = 22;
        // (A: the left block fitted to LeftW so the stem and the braid pass clear of it; the counts on two lines)
        if (Wide) while (nmPx > 15 && LampInk.W(fnm, nm, nmPx) > LeftW) nmPx--;
        LampInk.Text(ci, fnm, nmPx, X0 + Pad, Y0 + 118, nm, LampInk.Ink);
        LampInk.Text(ci, LampInk.F("alegreya-sans-700", 2), 13, X0 + Pad, Y0 + 140, $"DAY RANK {Roman(Math.Max(1, rank))}", LampInk.Gold);
        if (Wide)
        {
            LampInk.Text(ci, fs, 14, X0 + Pad, Y0 + 160, $"{litIds.Length} of {Wicks.LampCount} lit", LampInk.Dim);
            LampInk.Text(ci, fs, 14, X0 + Pad, Y0 + 177, $"{plan.Count} planned", LampInk.Dim);
        }
        else LampInk.Text(ci, fs, 14, X0 + Pad, Y0 + 160, $"{litIds.Length} of {Wicks.LampCount} lit · {plan.Count} planned", LampInk.Dim);
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
            LampInk.Text(ci, fk, 13, Lx0 + (Wide ? -36 : -20), ry - 19, s.Kind.ToString().ToUpperInvariant() + (sug ? " · LIGHT MY WAY" : ""), LampInk.Dim with { A = 0.95f });
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
            // (M3's card line, the owner's "Yes, ship it": a chained skill says what each cut deals and how often)
            string line = $"{sum.Stat} {sum.Total:0} = " + string.Join(" · ", sum.Parts.Select(p => $"{p.What} {p.Value}"))
                + (sum.Cut is { } cut ? $" · dealt as {cut:0} every {sum.Every:0.#} s" : "");
            var fsum = LampInk.F("alegreya-sans-500");
            float shift = Math.Clamp(lastRowBottom + 8 + fsum.GetAscent(14) - (Y1 - (Wide ? 14 : 12)), 0, 6);
            LampInk.Text(ci, LampInk.F("alegreya-sans-500"), 14, Wide ? (X0 + X1) / 2 : X0 + 532, Y1 - (Wide ? 14 : 12) + shift, line, LampInk.Body with { A = 0.95f }, 0);
        }
    }

    readonly HashSet<string> overflowSaid = new();
    /// <summary>The lowest ink the last row drew (the sum line keeps 8 px under it, moving down at most 6).</summary>
    float lastRowBottom;
    void Overflow(int r, int c, string text)
    {
        if (overflowSaid.Add($"{r}/{c}/{text}")) GD.Print($"WICKROW OVERFLOW r={r} c={c} {text}");
    }

    void DrawRowText(Control ci, int r, float ry)
    {
        var fn = LampInk.F("alegreya-700");
        var fl = LampInk.F("alegreya-400");
        var fs = LampInk.F("alegreya-sans-400");
        float w = TextR - TextX;
        bool last = r == strands.Count - 1;
        float bottom;
        if (r == fr)
        {
            string line = LineOf(r, fc), delta = fc < 3 ? DeltaOf(Id(r, fc)) : "";
            string stText = StateOf(r, fc);
            var lines = LampInk.Wrap(line, fl, 14, w);
            if (lines.Count > 2) Overflow(r, fc, line);
            // the delta rides the last text line when it fits; else it takes the status slot (one line)
            string slot = "";
            if (delta != "")
            {
                if (lines.Count > 0 && LampInk.W(fl, lines[^1] + " · " + delta, 14) <= w) lines[^1] += " · " + delta;
                else slot = delta;
            }
            // the slot: the delta then the status when both fit one line; a refusal (said) or the status alone otherwise
            List<string> slotLines;
            if (slot != "" && stText == "") slotLines = new() { slot };
            else if (slot != "" && said == null && LampInk.W(fs, slot + " · " + stText, 13) <= w) slotLines = new() { slot + " · " + stText };
            else slotLines = stText == "" ? (slot == "" ? new() : new() { slot }) : LampInk.Wrap(stText, fs, 13, w);
            // measured layout: the block sits at the unfocused anchor and only rises as far as the room under needs,
            // never closer than 10 px (ink to ink) below the row above; 8 px of clear ground above what follows
            static float Asc(Font f, int px) => f.GetAscent(px);
            static float Desc(Font f, int px) => f.GetDescent(px);
            int n = lines.Count;
            float aboveBottom = float.NegativeInfinity;
            if (r > 0)
            {
                var al = LampInk.Wrap(LineOf(r - 1, 3), fl, 14, w);
                float ay = ry - PitchY;
                aboveBottom = al.Count > 0 ? ay + 16 + (al.Count - 1) * 16 + Desc(fl, 14) : ay - 2 + Desc(fn, 18);
            }
            float nameTop = ry - 2 - Asc(fn, 18);
            float maxRise = float.IsNegativeInfinity(aboveBottom) ? 16 : Math.Clamp(nameTop - (aboveBottom + 10), 0, 16);
            float lowTop = last ? Y1 - (Wide ? 14 : 12) + 6 - Asc(LampInk.F("alegreya-sans-500"), 14) : ry + PitchY - 2 - Asc(fn, 18);
            float limitBottom = lowTop - 8;
            float lastLine = ry + 16 + Math.Max(0, n - 1) * 16;
            float BottomInk(List<string> sl) => sl.Count > 0 ? lastLine + 17 + (sl.Count - 1) * 15 + Desc(fs, 13) : lastLine + Desc(fl, 14);
            float rise = 0;
            while (true)
            {
                float need = BottomInk(slotLines) - limitBottom;
                if (need <= maxRise) { rise = Math.Max(0, need); break; }
                if (slotLines.Count > 0 && said == null) { slotLines.RemoveAt(slotLines.Count - 1); continue; }
                Overflow(r, fc, string.Join(" ", slotLines.Prepend(line)));
                rise = maxRise;
                break;
            }
            float y0 = ry + 16 - rise, sy = y0 + Math.Max(0, n - 1) * 16 + 17;
            LampInk.Text(ci, fn, 18, TextX, ry - 2 - rise, NameOf(r, fc), LampInk.Ink);
            for (int j = 0; j < lines.Count; j++) LampInk.Text(ci, fl, 14, TextX, y0 + j * 16, lines[j], LampInk.Body with { A = 0.92f });
            for (int j = 0; j < slotLines.Count; j++) LampInk.Text(ci, fs, 13, TextX, sy + j * 15, slotLines[j], said != null ? LampInk.Red : LampInk.Focus);
            bottom = BottomInk(slotLines) - rise;
        }
        else
        {
            bool crossed = Crossed(r);
            string tl = crossed ? "One Turn a skill" : LineOf(r, 3);
            LampInk.Text(ci, fn, 18, TextX, ry - 2, strands[r].TurnDef.Name, crossed ? LampInk.Dim : LampInk.Ink);
            var ls = LampInk.Wrap(tl, fl, 14, w);
            if (ls.Count > 2) Overflow(r, 3, tl);
            for (int j = 0; j < ls.Count; j++)
                LampInk.Text(ci, fl, 14, TextX, ry + 16 + j * 16, ls[j], (crossed ? LampInk.Dim : LampInk.Body) with { A = 0.9f });
            bottom = ry + 16 + (Math.Max(1, ls.Count) - 1) * 16 + fl.GetDescent(14);
        }
        if (last) lastRowBottom = bottom;
    }

    /// <summary>A lamp's line under its name: the Turn's own text (Wicks.Text prefixes the Turn's name, already drawn above it).</summary>
    string LineOf(int r, int c) => c == 3 ? strands[r].TurnDef.Text : Wicks.Text(Skill!, Id(r, c));

    /// <summary>U1 §5C: the focused lamp's line with what it changes ("+10% damage · 57 → 63", WickBook.LampDelta);
    /// the line alone when nothing it names changes. Asked once a lamp until the board is read again.</summary>
    readonly Dictionary<string, string> deltaOf = new();
    string DeltaOf(string id)
    {
        if (Skill == null || id == "") return "";
        if (litIds.Contains(id)) return "";
        if (!deltaOf.TryGetValue(id, out var d))
        {
            d = WickBook.LampDelta(ch, Skill, id) is { } x ? $"{x.Before} → {x.After}" + (x.What == "Cut" ? " a cut" : "") : "";
            deltaOf[id] = d;
        }
        return d;
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
            string art = Glyphs.ForSkill(learned[i], Weapons.All[learned[i]].Art);
            var c = rc.Position + new Vector2(14, rc.Size.Y / 2);
            WickTabs.Seat(ci, c, 26, i % 6, art, ItemViews.SchoolColors[Weapons.All[learned[i]].School]);
            LampInk.Text(ci, fn, 17, c.X + 22, c.Y + 6, Weapons.All[learned[i]].Name, i == listI ? LampInk.Ink : LampInk.Body with { A = 0.85f });
            if (i == listI) ci.DrawArc(c, 16, 0, Mathf.Tau, 48, LampInk.Focus, 1.5f, true);
        }
    }

    /// <summary>The stem (skins/c.py _stem_dist): one continuous gold line up from the chosen tab, bending on a 20 px
    /// radius into the knot. From a tab right of the knot it runs left under the rows, then up.</summary>
    /// <summary>A: the left block's widest type (the stem rises at Kx - 20, 14 px clear of it).</summary>
    float LeftW => Kx - 20 - 14 - (X0 + Pad);

    /// <summary>A polyline through the corners, each rounded by r (a quadratic through the corner).</summary>
    static List<Vector2> Rounded(Vector2[] c, float r)
    {
        var o = new List<Vector2> { c[0] };
        for (int i = 1; i < c.Length - 1; i++)
        {
            var a = c[i - 1]; var v = c[i]; var b = c[i + 1];
            float ra = Math.Min(r, a.DistanceTo(v) / 2), rb = Math.Min(r, v.DistanceTo(b) / 2);
            if (ra < 0.5f || rb < 0.5f) { o.Add(v); continue; }
            var p0 = v + (a - v).Normalized() * ra; var p2 = v + (b - v).Normalized() * rb;
            for (int k = 0; k <= 8; k++) { float t = k / 8f; o.Add(p0 * (1 - t) * (1 - t) + v * 2 * t * (1 - t) + p2 * t * t); }
        }
        o.Add(c[^1]);
        return o;
    }

    void DrawStem(Control ci, Vector2 knot)
    {
        var pts = new List<Vector2>();
        float tx = TabAt.X, top = TabAt.Y - 28 - 2.5f;
        const float rad = 20;
        if (Wide)
        {
            // A: up from the seat into the smoke's foot, along under the rows to Kx - 20 (clear of the left block), up,
            // and into the knot
            float rx = knot.X - rad, ch = Y1 - 8;
            pts = Math.Abs(tx - rx) < 1
                ? Rounded([new Vector2(tx, top), new Vector2(rx, knot.Y), knot], rad)
                : Rounded([new Vector2(tx, top), new Vector2(tx, ch), new Vector2(rx, ch), new Vector2(rx, knot.Y), knot], 10);
        }
        else if (tx + rad <= knot.X)
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
                // (the Turn's number clear of its focus ring at r + 5: judge r2 saw C's "4" on the ring's line)
                float o = c == 3 ? 24 : 16;
                var p = At(r, c) + new Vector2(-o, -o + 4.5f);
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
