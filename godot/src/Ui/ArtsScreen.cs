using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The arts the survivor knows (Rpg/ArtBook.cs), on the day's book's panel at the right with her in
/// the world beside it, as Self and the Pack are (approved: the book is one panel; no boxes). Its two
/// pages turn under the book's tabs: the art in hand, and the skills.
///
/// The art in hand: the arts known in a row of marks, the rest of the calling's faint with how they
/// are learned (Hades II's locked silhouettes); the art chosen, named large, its rank as a line of
/// nodes (the road to mastery), its facets as ruled lines of type, each set, to choose, or waiting
/// on a rank. An art is taken in hand, and a set facet changed, only where it is safe (out of a
/// fight); a facet newly opened by rank can be chosen anywhere. Skills: what is learned and
/// carried, each a line, and the one chosen read out beside the list.
/// </summary>
public partial class ArtsScreen : Overlay
{
    public override string Kind => "arts";
    public override Act? Toggle => Act.Arts;
    public override float CameraShift => -330;
    public override float CameraNear => 0.56f;
    public override (float Pitch, float Distance, float Height)? CameraFrame => BookFrame;

    public static readonly string[] Numerals = ["I", "II", "III", "IV", "V"];
    static readonly System.Collections.Generic.Dictionary<ArtRole, (string Name, Color Color)> Roles = new()
    {
        [ArtRole.Tank] = ("Holds the line", new Color("#d8b870")), [ArtRole.Damage] = ("Deals death", new Color("#e8866a")),
        [ArtRole.Healing] = ("Mends", new Color("#8ad48a")), [ArtRole.Utility] = ("Gets you out", new Color("#8ac0e8")),
        [ArtRole.Control] = ("Holds them", new Color("#c8a0f0")),
    };

    string? sel;
    int page;
    bool skills => page == 1;

    /// <summary>The functional Lamps board and Wick screen: launch with --board, or set SU_BOARD=1.</summary>
    public static bool BoardOn => SurvivorUnchained.Args.Has("board") || SurvivorUnchained.Args.Dev && System.Environment.GetEnvironmentVariable("SU_BOARD") == "1";
    /// <summary>v2's Lamps are their own tab on the book's chain (LampsScreen); --board keeps the functional pages here.</summary>
    static int Pages => BoardOn ? 4 : 2;
    static readonly string[] PageNames = ["The art in hand", "Skills", "Lamps", "Wicks"];

    public ArtsScreen(Game g) : base(g)
    {
        // --arts-skill ID[:index] (pictures): the Skills page with that skill chosen, and that socket's chooser open.
        if (Args.Get("arts-skill") is string a)
        {
            var p = a.Split(':');
            page = 1; selSkill = p[0];
            if (p.Length > 1 && int.TryParse(p[1], out var i)) { sockSkill = p[0]; sockIdx = i; }
        }
    }

    /// <summary>The Arts window on every Skills page: from y 16 to y 1046.</summary>
    const float SkillsH = 1030;

    bool Safe => G.Battle is not { Combat: true };

    /// <summary>Its two pages turn with LT and RT (, and .).</summary>
    public override bool Key(Act a)
    {
        if (a is not (Act.SubNext or Act.SubPrev)) return false;
        page = (page + (a == Act.SubNext ? 1 : Pages - 1)) % Pages;
        Sound.Sfx.Page();
        Refresh();
        return true;
    }

    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var known = ArtBook.Known(ch);
        sel ??= ch.Ability != "" ? ch.Ability : known.FirstOrDefault();
        var v = BookPanel(null);
        var pages = Kit.Tabs(PageNames[..Pages], page, k => { page = k; Refresh(); }, 16, 28);
        pages.Alignment = BoxContainer.AlignmentMode.Center;
        v.AddChild(pages);
        if (page >= Pages) page = 0;
        v.AddChild(Style.Label(page == 2 ? "Light lamps with the points you have earned; put them out where it is safe."
            : page == 3 ? "Plan the order a skill's lamps light; its rank is how many are lit."
            : skills ? "What the arenas showed you, learned for the day; what you carry is banked for the night."
            : Safe ? "One art in hand. Each grows with use, and its ranks open facets." : "Out here you can choose a facet a rank has opened; change your art where it is safe.",
            Style.TextItalic, 15, Kit.Dim, true, HorizontalAlignment.Center));
        if (page == 2) BuildLamps(v);
        else if (page == 3) BuildWicks(v);
        else if (skills) BuildSkills(v);
        else
        {
            // The arts known, as a row of marks; then the calling's others, faint, with how they come.
            v.AddChild(Kit.Head("Known", $"{known.Count}"));
            v.AddChild(Marks(ch, known.Select(Abilities.ById), true));
            var rest = Abilities.All.Values.Where(a => !known.Contains(a.Id) && Abilities.Learnable(a, ch.Archetype)).ToList();
            if (rest.Count > 0)
            {
                // The rest of the calling's arts, small and faint on one line, named on hover: a promise, not a wall.
                v.AddChild(Kit.Head("Not yet learned", $"{rest.Count}, taught by manuals"));
                v.AddChild(Marks(ch, rest, false));
            }
            if (sel != null && Abilities.Find(sel) is { } def) Chosen(v, ch, def, known.Contains(def.Id));
        }
        bool pad = Controls.Instance.UsingPad;
        var p = pad
            ? Kit.Prompts(Kit.Prompt(Act.Confirm, "Choose"), Kit.Prompt(Act.SubNext, PageNames[(page + 1) % Pages]), Kit.Prompt(Act.TabNext, "Turn"), Kit.Prompt(Act.Cancel, "Close"))
            : Kit.Prompts(Kit.Prompt("Click", "Choose"), Kit.Prompt(G.Key(Act.SubPrev) + " " + G.Key(Act.SubNext), PageNames[(page + 1) % Pages]), Kit.Prompt("[ ]", "Turn"), Kit.Prompt(G.Key(Act.Arts), "Close"));
        p.CustomMinimumSize = new Vector2(0, 30);
        if (skills)
        {
            // the Skills pages are one fixed height (bottom edge at y 1046), whatever the chooser holds
            v.AddChild(new Control { SizeFlagsVertical = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
            if (v.GetParent() is Control pc) pc.CustomMinimumSize = new Vector2(pc.CustomMinimumSize.X, SkillsH);
        }
        v.AddChild(p);
    }

    /// <summary>Arts as a row of marks, each its medallion and its name under it; the chosen one
    /// underlined in ember, the one in hand ringed in ember; unlearned ones faint.</summary>
    Control Marks(CharacterData ch, System.Collections.Generic.IEnumerable<AbilityDef> arts, bool known)
    {
        var row = new HFlowContainer { MouseFilter = MouseFilterEnum.Ignore };
        row.AddThemeConstantOverride("h_separation", 10);
        row.AddThemeConstantOverride("v_separation", 8);
        foreach (var a in arts)
        {
            bool held = ch.Ability == a.Id, on = sel == a.Id;
            int rank = known ? ArtBook.Rank(ch, a.Id) : 0;
            var id = a.Id;
            var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = CursorShape.PointingHand, CustomMinimumSize = known ? new Vector2(112, 100) : new Vector2(54, 54) };
            if (!known) b.TooltipText = $"{a.Name}: {Roles[a.Role].Name.ToLowerInvariant()}. A manual teaches it.";
            foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
            if (on) b.AddThemeStyleboxOverride("normal", new StyleBoxFlat { BgColor = Colors.Transparent, BorderColor = Style.Ember, BorderWidthBottom = 2 });
            b.Pressed += () => { sel = id; Sound.Sfx.Click(); Refresh(); };
            Nav.Mark(b, $"art:{a.Id}", () => { sel = id; Refresh(); });
            var m = new Medallion(known ? 60 : 44, "", a.Icon)
            {
                Arc = known && rank < Abilities.MaxRank ? (float)ArtBook.Progress(ch, a.Id) : 0,
                Ring = held ? Style.Ember : known ? Style.Gold : Kit.Faint,
                Ink = known ? (held ? Style.EmberHi : Style.GoldHi) : Kit.Dim with { A = 0.55f },
                Core = known ? new Color("#2a1a10") : new Color("#16131a"),
                Lit = held,
            };
            var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            mc.AddChild(m);
            var col = Style.V(2, mc);
            if (known)
            {
                col.AddChild(Style.Label(a.Name, Style.UiBold, 14, held ? Style.EmberHi : Kit.Ink, false, HorizontalAlignment.Center));
                col.AddChild(Style.Label((held ? "in hand" : $"rank {Numerals[rank - 1]}") + (ArtBook.OpenSlots(ch, a.Id) > 0 ? " · a facet!" : ""), Style.Ui, 13, Roles[a.Role].Color, false, HorizontalAlignment.Center));
            }
            col.MouseFilter = MouseFilterEnum.Ignore;
            col.Position = new Vector2(0, known ? 2 : 4);
            col.Size = known ? new Vector2(112, 96) : new Vector2(54, 50);
            b.AddChild(col);
            row.AddChild(b);
        }
        return row;
    }

    /// <summary>The art chosen: its name and what it is, its rank on the road to mastery, its facets.</summary>
    void Chosen(VBoxContainer v, CharacterData ch, AbilityDef a, bool known)
    {
        int rank = known ? ArtBook.Rank(ch, a.Id) : 0;
        var role = Roles[a.Role];
        bool held = ch.Ability == a.Id;
        v.AddChild(Kit.RuleH());
        var head = Style.H(Style.Gap5);
        var big = new Medallion(88, "", a.Icon)
        {
            Arc = known && rank < Abilities.MaxRank ? (float)ArtBook.Progress(ch, a.Id) : known ? 1 : 0,
            Ring = held ? Style.Ember : known ? Style.Gold : Kit.Faint,
            Ink = known ? Style.GoldHi : Kit.Dim,
            Lit = held,
        };
        big.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        head.AddChild(big);
        var words = Style.V(Style.Gap1);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var nameRow = Style.H(16, Style.Label(a.Name.ToUpperInvariant(), Style.Display, 30, held ? Style.EmberHi : Kit.Ink));
        words.AddChild(nameRow);
        words.AddChild(Style.Label($"{role.Name}{(a.Movement ? "  ·  a way of moving" : $"  ·  a {Callings.Archetype(a.Calling!).Name}'s art")}  ·  {a.Cooldown:0} s{(a.Interrupts ? "  ·  breaks channels" : "")}", Style.UiBold, 15, role.Color));
        words.AddChild(Style.Label(a.Description, Style.Text, 17, Kit.Ink2, true));
        if (!known)
            words.AddChild(Style.Label("Not yet learned. A manual teaches it: the thing that rules an arena carries one, and they turn up in the packs of the dead.", Style.TextItalic, 15, Kit.Dim, true));
        // (in hand, or the way to take it in hand, on the name's line: one line less)
        else if (held) nameRow.AddChild(Style.Label("in hand", Style.TextItalic, 17, Style.EmberHi));
        else if (!a.Movement && a.Id != "cold_then_not") words.AddChild(Style.Label("Fires itself: see the Lamps.", Style.TextItalic, 15, Kit.Dim, true));
        else if (Safe) nameRow.AddChild(Nav.Id(Kit.Word("Take it in hand", () => G.Gear((j, b) => j.HoldArt(a.Id, b)), Style.EmberHi, 16), "hold"));
        else words.AddChild(Style.Label("Take it in hand somewhere safe: the Waystation, a quiet road.", Style.TextItalic, 15, Kit.Dim, true));
        head.AddChild(words);
        v.AddChild(head);
        if (known)
        {
            v.AddChild(Kit.Head("Its rank", $"+{(Abilities.RankPower(rank) - 1) * 100:0}% strength, {(1 - Abilities.RankHaste(rank)) * 100:0}% shorter wait"));
            v.AddChild(new RoadTrack(rank, 0));
        }
        Facets(v, ch, a, known);
    }

    /// <summary>The four facets as ruled lines of type: a socket mark, the name and what it does, and
    /// at the line's end whether it is set, to choose, or waiting on a rank.</summary>
    void Facets(VBoxContainer v, CharacterData ch, AbilityDef a, bool known)
    {
        int rank = known ? ArtBook.Rank(ch, a.Id) : 0;
        int slots = Abilities.FacetSlots(rank);
        var chosen = known ? ArtBook.Facets(ch, a.Id) : new();
        string opens = slots == 0 ? "rank II opens the first" : slots == 1 ? "rank IV opens the second" : "both open";
        v.AddChild(Kit.Head("Facets", !known ? "learn the art to set them" : slots == 0 ? opens : $"{chosen.Count} of {slots} set  ·  {opens}"));
        foreach (var f in a.Facets)
        {
            bool on = chosen.Contains(f.Id);
            bool canPick = known && !on && chosen.Count < slots;
            bool canDrop = known && on && Safe;
            var socket = new FacetMark(on, canPick) { SizeFlagsVertical = SizeFlags.ShrinkBegin };
            var text = Style.V(1, Style.Label(f.Name, Style.DisplayLight, 18, on ? Style.EmberHi : canPick ? Kit.Ink : Kit.Ink2),
                Style.Label(f.Text, Style.Ui, 15, on || canPick ? Kit.Ink2 : Kit.Dim, true));
            text.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            Control state;
            if (canPick) state = Nav.Id(Kit.Word("Set it", () => G.Gear((j, bt) => j.ChooseFacet(a.Id, f.Id, true, bt)), Style.EmberHi, 16), $"facet:{f.Id}");
            else if (canDrop) state = Nav.Id(Kit.Word("Choose again", () => G.Gear((j, bt) => j.ChooseFacet(a.Id, f.Id, false, bt)), Kit.Dim, 15), $"facet:{f.Id}");
            else state = Style.Label(on ? "set" : !known ? "" : slots == 0 ? "opens at rank II" : "sockets full", Style.TextItalic, 15, on ? Style.EmberHi : Kit.Faint);
            state.SizeFlagsVertical = SizeFlags.ShrinkBegin;
            var line = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore };
            line.AddThemeStyleboxOverride("panel", new LineUnder { ContentMarginBottom = 8 });
            line.AddChild(Style.H(14, socket, text, state));
            v.AddChild(line);
        }
    }

    /* ------------------------------------------------- lamps and wicks (--board) -- */

    string status = "";
    string? wickSkill;

    static Button Row(System.Action press, float h = 0)
    {
        var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = CursorShape.PointingHand, CustomMinimumSize = new Vector2(0, h) };
        foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
        b.Pressed += () => { Sound.Sfx.Click(); press(); };
        return b;
    }

    Label Status() => Style.Label(status, Style.TextItalic, 15, Style.EmberHi, true);

    void BuildLamps(VBoxContainer page)
    {
        var ch = G.Journey.Ch;
        var w = G.Journey.World;
        var layout = LampBook.Now(ch);
        var road = Lamps.Roads.TryGetValue(layout.Type, out var r) ? r : null;
        page.AddChild(Style.Label($"{road?.Name ?? layout.Type}  ·  {road?.Line}", Style.DisplayLight, 20, Kit.Ink, true));
        var chips = Style.H(10, Style.Label("Road", Style.UiBold, 15, Kit.Dim));
        foreach (var rd in Lamps.RoadsOf(ch.Archetype))
        {
            var id = rd.Id;
            var name = rd.Name;
            chips.AddChild(Kit.Word(name, () =>
            {
                if (id == layout.Type) status = "You already walk this road.";
                else if (!Safe) status = "Change your road somewhere safe.";
                else { G.Gear((j, _) => LampBook.SetType(j.Ch, id)); status = $"You walk {name}; every lamp went out."; }
                Refresh();
            }, id == layout.Type ? Style.EmberHi : Kit.Ink2));
        }
        chips.AddChild(Style.Label("  Layout", Style.UiBold, 15, Kit.Dim));
        var st = LampBook.State(ch);
        for (int i = 0; i < st.Layouts.Count; i++)
        {
            int k = i;
            chips.AddChild(Kit.Word($"{i + 1}", () =>
            {
                bool done = false;
                if (Safe) G.Gear((j, _) => done = LampBook.Switch(j.Ch, k, j.World, G.Zone?.Id));
                status = done || k == st.Active ? "" : "Change layouts at a lamp-post.";
                Refresh();
            }, i == st.Active ? Style.EmberHi : Kit.Ink2));
        }
        page.AddChild(chips);
        var acts = Style.H(18, Style.Label($"Earned {LampBook.Earned(ch, w)}  ·  spent {LampBook.Spent(ch)}  ·  spare {LampBook.Spare(ch, w)}", Style.UiBold, 16, Kit.Ink));
        acts.AddChild(Kit.Word("Light suggested", () =>
        {
            if (!Safe) { status = "Light lamps somewhere safe."; Refresh(); return; }
            int n = 0;
            G.Gear((j, _) => n = LampBook.LightSuggested(j.Ch, j.World));
            status = n == 0 ? "Nothing to light." : $"Lit {n}.";
            Refresh();
        }, Style.EmberHi, 16));
        acts.AddChild(Kit.Word("Clear", () =>
        {
            if (!Safe) status = "Put lamps out somewhere safe.";
            else { G.Gear((j, _) => LampBook.Clear(j.Ch)); status = "Every lamp is out but the free ones."; }
            Refresh();
        }, Kit.Ink2, 16));
        page.AddChild(acts);
        page.AddChild(Status());

        var list = Style.V(2);
        foreach (var reg in Lamps.All.Values.Where(l => l.Calling == null || l.Calling == ch.Archetype).GroupBy(l => l.Region))
        {
            list.AddChild(Kit.Head(reg.Key.ToString()));
            foreach (var grp in reg.GroupBy(l => l.Road ?? ""))
            {
                string rn = grp.Key == "" ? "" : Lamps.Roads.TryGetValue(grp.Key, out var gr) ? gr.Name : Style.Cap1(grp.Key.Replace('.', ' ').Replace('_', ' '));
                if (rn != "") list.AddChild(Style.Label($"{rn}  ·  {LampBook.Depth(ch, grp.Key)} lit", Style.UiBold, 14, Kit.Dim));
                foreach (var l in grp) list.AddChild(LampRow(ch, w, l));
            }
        }
        // The book panel sizes to what it holds, so the list is given its height (left at 0 it showed nothing).
        var scroll = Style.Scroll(list);
        scroll.CustomMinimumSize = new Vector2(0, 620);
        page.AddChild(scroll);
    }

    Control LampRow(CharacterData ch, SurvivorUnchained.World.WorldState w, LampDef l)
    {
        bool lit = LampBook.IsLit(ch, l.Id);
        var id = l.Id;
        var b = Row(() =>
        {
            if (!Safe) { status = "Change your lamps somewhere safe."; Refresh(); return; }
            if (lit) { var no = LampBook.CanUnlight(ch, id); status = BoardWords.Why(no); if (no == LampNo.None) G.Gear((j, _) => LampBook.Unlight(j.Ch, id)); }
            else { var no = LampBook.CanLight(ch, w, id); status = BoardWords.Why(no); if (no == LampNo.None) G.Gear((j, _) => LampBook.Light(j.Ch, j.World, id)); }
            Refresh();
        }, 34);
        bool open = lit || LampBook.CanLight(ch, w, id) == LampNo.None;
        var gate = l.Gate > 0 ? $"  ·  needs {l.Gate} on the road" : "";
        var t = Style.Label(l.Text, Style.Ui, 14, open ? Kit.Ink2 : Kit.Faint, false);
        t.ClipText = true;
        // One line a lamp; the whole rule on hover (most v1 rules are longer than the line).
        b.TooltipText = l.Text;
        t.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var row = Style.H(10, Style.Label(lit ? "●" : "○", Style.UiBold, 16, lit ? Style.EmberHi : Kit.Faint),
            Style.Label(l.Name + gate, Style.DisplayLight, 16, lit ? Style.EmberHi : open ? Kit.Ink : Kit.Dim), t);
        row.MouseFilter = MouseFilterEnum.Ignore;
        b.AddChild(row);
        row.SetAnchorsPreset(LayoutPreset.FullRect);
        return b;
    }

    void BuildWicks(VBoxContainer page)
    {
        var ch = G.Journey.Ch;
        if (wickSkill == null || !ch.Skills.Contains(wickSkill)) wickSkill = ch.Skills.FirstOrDefault(s => Wicks.Of(s) != null);
        var row = Style.H(0);
        var list = Style.V(4);
        list.CustomMinimumSize = new Vector2(180, 0);
        list.AddChild(Kit.Head("Learned skills"));
        if (ch.Skills.Count == 0) list.AddChild(Style.Label("None yet.", Style.TextItalic, 15, Kit.Dim, true));
        foreach (var id in ch.Skills)
        {
            var sid = id;
            bool has = Wicks.Of(id) != null;
            string name = Weapons.All.TryGetValue(id, out var wd) ? wd.Name : id;
            var b = Row(() => { wickSkill = sid; status = ""; Refresh(); }, 34);
            if (wickSkill == id) b.AddThemeStyleboxOverride("normal", new StyleBoxFlat { BgColor = Colors.Transparent, BorderColor = Style.Ember, BorderWidthLeft = 2 });
            var l = Style.Label(name, Style.DisplayLight, 16, !has ? Kit.Faint : wickSkill == id ? Style.EmberHi : Kit.Ink);
            l.Position = new Vector2(10, 4);
            l.MouseFilter = MouseFilterEnum.Ignore;
            b.AddChild(l);
            list.AddChild(b);
        }
        row.AddChild(list);
        row.AddChild(new LedgerRule { CustomMinimumSize = new Vector2(49, 0), SizeFlagsVertical = SizeFlags.Fill });
        var right = Style.V(Style.Gap3);
        right.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        if (wickSkill != null && Wicks.Of(wickSkill) != null) WickDetail(right, ch, wickSkill);
        else right.AddChild(Style.Label("Choose a skill that has a wick.", Style.TextItalic, 16, Kit.Dim, true));
        row.AddChild(right);
        page.AddChild(row);
    }

    void WickDetail(VBoxContainer d, CharacterData ch, string skill)
    {
        int rank = SkillBook.Rank(ch);
        var wick = Wicks.Of(skill)!;
        var plan = WickBook.PlanOf(ch, skill);
        var path = WickBook.Path(ch, skill);
        var lit = WickBook.Lit(ch, skill, rank);
        string name = Weapons.All.TryGetValue(skill, out var wd) ? wd.Name : skill;
        d.AddChild(Style.Label(name.ToUpperInvariant(), Style.Display, 26, Kit.Ink));
        d.AddChild(Style.Label($"Day rank {Ranks[rank]}: lights {rank} of {Wicks.LampCount} lamps.{(Safe ? "" : " Change the plan somewhere safe.")}", Style.UiBold, 15, Kit.Ink2, true));
        var cols = Style.H(10);
        foreach (var s in Wicks.StrandsOf(skill))
        {
            var col = Style.V(2);
            col.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            // Three strands share what the 900 px panel leaves beside the skill list (at 250 each the third ran off its edge).
            col.CustomMinimumSize = new Vector2(190, 0);
            col.SizeFlagsStretchRatio = 1;
            col.AddChild(Style.Label(s.Kind.ToString().ToUpperInvariant() + (s.Id == wick.Suggested ? "  ·  Light my way" : ""), Style.UiBold, 14, s.Id == wick.Suggested ? Style.EmberHi : Kit.Dim, true));
            col.AddChild(Style.Label(s.TurnDef.Name, Style.DisplayLight, 18, Kit.Ink, true));
            for (int n = 1; n <= Wicks.PerStrand; n++)
            {
                string lamp = s.LampId(n);
                int at = IndexOf(plan, lamp);
                bool isLit = lit.Contains(lamp);
                string mark = at >= 0 ? $"{at + 1}." : isLit ? "●" : "○";
                var b = Row(() =>
                {
                    if (!Safe) { status = "Change the plan somewhere safe."; Refresh(); return; }
                    var no = at >= 0 ? WickBook.CanUnplan(ch, skill, lamp) : WickBook.CanPlan(ch, skill, lamp);
                    status = BoardWords.Why(no);
                    if (no == WickNo.None) G.Gear((j, _) => { if (at >= 0) WickBook.Unplan(j.Ch, skill, lamp); else WickBook.Plan(j.Ch, skill, lamp); });
                    Refresh();
                }, n == Wicks.PerStrand ? 90 : 62);
                var t = Style.Label(Wicks.Text(skill, lamp), Style.Ui, 14, isLit ? Kit.Ink : Kit.Ink2, true);
                t.SizeFlagsHorizontal = SizeFlags.ExpandFill;
                var inner = Style.H(8, Style.Label(mark + (at >= 0 && isLit ? " ●" : ""), Style.UiBold, 15, at >= 0 ? Style.EmberHi : isLit ? Style.GoldHi : Kit.Faint), t);
                inner.MouseFilter = MouseFilterEnum.Ignore;
                b.AddChild(inner);
                inner.SetAnchorsPreset(LayoutPreset.FullRect);
                col.AddChild(b);
            }
            cols.AddChild(col);
        }
        d.AddChild(cols);
        d.AddChild(Status());
        d.AddChild(Style.Label($"Order: {(path.Length == 0 ? "none" : string.Join(", ", path.Select(PathName(skill))))}  ·  {lit.Length} lit", Style.Ui, 14, Kit.Dim, true));
        d.AddChild(Kit.Word("Reset", () =>
        {
            if (!Safe) status = "Change the plan somewhere safe.";
            else { G.Gear((j, _) => WickBook.Reset(j.Ch, skill)); status = "Plan cleared; Light my way follows."; }
            Refresh();
        }, Kit.Ink2, 16));
    }

    static int IndexOf(System.Collections.Generic.IReadOnlyList<string> l, string x)
    {
        for (int i = 0; i < l.Count; i++) if (l[i] == x) return i;
        return -1;
    }

    static System.Func<string, string> PathName(string skill) => id =>
        Wicks.Lamp(skill, id) is { } ln ? (ln.N == Wicks.PerStrand ? $"{ln.Strand.TurnDef.Name} (Turn)" : $"{ln.Strand.TurnDef.Name} {Ranks[ln.N]}") : id;

    /* --------------------------------------------------------------- skills -- */

    static readonly string[] Ranks = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"];
    string? selSkill;

    void BuildSkills(VBoxContainer page)
    {
        var ch = G.Journey.Ch;
        var seen = ch.Discovered.Where(id => Weapons.All.TryGetValue(id, out var w) && w.Findable && !SkillBook.Knows(ch, id)).ToList();
        selSkill ??= ch.Slotted.FirstOrDefault() ?? ch.Skills.FirstOrDefault() ?? seen.FirstOrDefault();
        var row = Style.H(0);
        var list = Style.V(4);
        list.CustomMinimumSize = new Vector2(330, 0);
        list.AddChild(Kit.Head("Learned", $"carrying {SkillBook.Carried(ch).Count()} of {SkillBook.Slots(ch)}"));
        if (ch.Skills.Count == 0) list.AddChild(Style.Label("None yet. Your calling teaches the first as you grow.", Style.TextItalic, 15, Kit.Dim, true));
        foreach (var id in ch.Skills) list.AddChild(SkillEntry(ch, id, true));
        // (bd-ui W11c: her joined Unions follow her skills)
        foreach (var id in UnionJoin.Joined(ch).Where(u => Weapons.All.ContainsKey(u))) list.AddChild(SkillEntry(ch, id, true));
        if (seen.Count > 0)
        {
            list.AddChild(Kit.Head("Seen in the arenas", "not yet learned"));
            foreach (var id in seen) list.AddChild(SkillEntry(ch, id, false));
        }
        int unseen = Weapons.Pool.Count(id => !ch.Discovered.Contains(id) && SkillBook.Carries(ch, id));
        if (unseen > 0) list.AddChild(Style.Label($"{unseen} more burn in the arenas, not yet shown to you.", Style.TextItalic, 15, Kit.Faint, true));
        row.AddChild(list);
        row.AddChild(new LedgerRule { CustomMinimumSize = new Vector2(49, 0), SizeFlagsVertical = SizeFlags.Fill });
        var right = Style.V(Style.Gap3);
        right.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        if (selSkill != null && Weapons.All.TryGetValue(selSkill, out var def)) right.AddChild(SkillDetail(ch, def));
        else HowSkillsCome(right);
        row.AddChild(right);
        page.AddChild(row);
    }

    /// <summary>With nothing learned yet, the page says how a skill comes to you, as three steps.</summary>
    static void HowSkillsCome(VBoxContainer d)
    {
        d.AddChild(Style.Label("HOW A SKILL COMES TO YOU", Style.Display, 24, Kit.Ink));
        d.AddChild(Style.Label("Your calling teaches you skills as you grow, and tomes teach the rest. What you put on a key is yours in every fight.", Style.Text, 17, Kit.Ink2, true));
        foreach (var (glyph, title, text) in new[]
        {
            ("flame", "Seen", "An arena's ember may show you one you have not learned: use it there, and look for its tome."),
            ("book", "Learned", "A tome teaches it: a story fight won, Vonnra's Curiosities; your calling may teach one as you grow."),
            ("embers", "Carried", "Put it on a key and it is yours in every fight."),
        })
        {
            var icon = Glyphs.Icon(glyph, 26, Style.Gold);
            icon.SizeFlagsVertical = SizeFlags.ShrinkBegin;
            var tv = Style.V(0, Style.Label(title.ToUpperInvariant(), Style.DisplayLight, 17, Kit.HeadInk), Style.Label(text, Style.Ui, 15, Kit.Ink2, true));
            // (the words take the column's width, not the narrowest a word allows)
            tv.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            d.AddChild(Style.H(12, icon, tv));
        }
    }

    Control SkillEntry(CharacterData ch, string id, bool known)
    {
        var w = Weapons.All[id];
        bool union = Weapons.IsUnion(id);
        bool carried = !union && ch.Slotted.Contains(id), meets = union || SkillBook.Meets(ch, id), on = selSkill == id;
        var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = CursorShape.PointingHand, CustomMinimumSize = new Vector2(0, 50) };
        foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
        if (on) b.AddThemeStyleboxOverride("normal", new StyleBoxFlat { BgColor = Colors.Transparent, BorderColor = Style.Ember, BorderWidthLeft = 2 });
        b.Pressed += () => { selSkill = id; Sound.Sfx.Click(); Refresh(); };
        Nav.Id(b, $"skill:{id}");
        var col = ItemViews.SchoolColors[w.School];
        var r = Style.H(12, Glyphs.Icon(Glyphs.ForSkill(w.Id, w.Art), 26, known ? col : col with { A = 0.45f }));
        string attr = SkillBook.Attribute(id);
        var words = Style.V(0, Style.Label(w.Name + (carried ? (meets ? "  ·  carried" : "  ·  idle") : ""), Style.DisplayLight, 16, known ? (carried ? Kit.Ink : Kit.Ink2) : Kit.Dim),
            Style.Label(union ? SocketModel.UnionLine(id) : $"asks {SkillBook.Need} {attr}  ·  you have {SkillBook.Have(ch, attr)}", Style.Ui, 13, union ? Kit.Dim : meets ? Style.Good : Style.Bad));
        r.AddChild(words);
        r.Position = new Vector2(10, 4);
        r.MouseFilter = MouseFilterEnum.Ignore;
        b.AddChild(r);
        return b;
    }

    // The socket block (bd-ui W11): which socket's chooser is open (one at a time).
    string? sockSkill;
    int sockIdx = -1;

    static SupportDef? Held(CharacterData ch, string skill, int i) =>
        ch.Gems.Sockets.TryGetValue(skill, out var row) && i < row.Count && row[i] != null ? Supports.Find(row[i]!) : null;

    /// <summary>The skill's sockets: two wells and, on a click, the chooser of the gems she owns that fit it.</summary>
    void SocketBlock(VBoxContainer d, CharacterData ch, WeaponDef w)
    {
        if (SocketModel.Halves(w.Id) is { } halves) { UnionSockets(d, ch, halves, w.Id); return; }
        int rank = SkillBook.RankOf(ch, w.Id), open = Supports.SocketsAt(rank), n = Supports.File.Sockets.Ranks.Count;
        d.AddChild(Kit.Head("Sockets", SocketModel.Note(rank)));
        int ownedAny = ch.Gems.Owned.Values.Count(v => v > 0);
        var wells = Style.H(8);
        for (int i = 0; i < n; i++)
        {
            int idx = i;
            var gem = Held(ch, w.Id, i);
            bool isOpen = i < open;
            var look = !isOpen ? GemSocket.Look.Closed : gem != null ? GemSocket.Look.Filled : GemSocket.Look.Empty;
            var well = new GemSocket(look, gem);
            var col = Style.V(4, well);
            col.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
            col.CustomMinimumSize = new Vector2(150, 0); // a fixed column, so the wells sit in the same places in every state
            if (isOpen)
            {
                well.Clickable();
                well.Selected = sockSkill == w.Id && sockIdx == i;
                well.Pressed += () => { bool same = sockSkill == w.Id && sockIdx == idx; sockSkill = same ? null : w.Id; sockIdx = same ? -1 : idx; Sound.Sfx.Click(); Refresh(); };
                Nav.Mark(well, $"socket:{i}", well.Press);
                col.AddChild(gem != null ? Style.Label(gem.Name, Style.UiBold, 14, Kit.Ink, false, HorizontalAlignment.Center)
                    : Style.Label("empty", Style.Ui, 13, Kit.Dim, false, HorizontalAlignment.Center));
                col.AddChild(new WellCaret { CustomMinimumSize = new Vector2(0, 6), MouseFilter = MouseFilterEnum.Ignore, On = well.Selected });
            }
            else
            {
                string at = SocketModel.RomanOf(Supports.File.Sockets.Ranks[i]);
                // (a kept gem's note says the rank once: name #8C847A regular, then one line)
                if (gem == null) col.AddChild(Style.Label($"at rank {at}", Style.Ui, 13, Kit.Dim, false, HorizontalAlignment.Center));
                else
                {
                    col.AddChild(Style.Label(gem.Name, Style.Ui, 14, new Color("#8C847A"), false, HorizontalAlignment.Center));
                    col.AddChild(Style.Label($"kept · wakes at rank {at}", Style.TextItalic, 13, Kit.Dim, false, HorizontalAlignment.Center));
                }
            }
            wells.AddChild(col);
        }
        d.AddChild(wells);
        if (ownedAny == 0) d.AddChild(Style.Label(SocketModel.NoGemsLine(), Style.TextItalic, 14, Kit.Dim, true));
        if (SocketModel.JoinedUnion(w.Id, UnionJoin.Joined(ch)) is { } uid && Weapons.All.TryGetValue(uid, out var udef))
        {
            var lk = new LinkButton { Text = udef.Name, Underline = LinkButton.UnderlineMode.OnHover, FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand };
            Style.Font(lk, Style.TextItalic, 14, Style.Ember, false);
            lk.AddThemeColorOverride("font_hover_color", Style.EmberHi);
            lk.Pressed += () => { selSkill = uid; sockSkill = null; sockIdx = -1; Refresh(); };
            Nav.Id(lk, $"union:{uid}");
            d.AddChild(Style.H(0, Style.Label("Joined in ", Style.TextItalic, 14, Kit.Dim), lk, Style.Label(": these gems feed it too.", Style.TextItalic, 14, Kit.Dim)));
        }
        if (sockSkill == w.Id && sockIdx >= 0 && sockIdx < open) Chooser(d, ch, w);
    }

    void Chooser(VBoxContainer d, CharacterData ch, WeaponDef w)
    {
        int idx = sockIdx;
        var (rows, dont) = SocketModel.Chooser(ch.Gems, w.Id, idx);
        void Set(string? gem)
        {
            sockSkill = null; sockIdx = -1;
            G.Gear((j, _) => Supports.Socket(j.Ch.Gems, w.Id, SkillBook.RankOf(j.Ch, w.Id), idx, gem));
            if (gem != null) Sound.Sfx.Equip(); else Sound.Sfx.Click();
        }
        var held = Held(ch, w.Id, idx);
        // W24: the head is 20 px under the wells' labels (the caret inside that) and 8 px over the first row: it and the rows are one
        // block with no gap of its own, the page's 6 px between blocks.
        var block = Style.V(0);
        block.AddChild(Style.Label(SocketModel.ChooserHead(idx, held?.Name), Style.UiHeavy, 13, Kit.HeadInk, false, HorizontalAlignment.Left, false));
        var list = Style.V(0); // rows 46 px apart: no gap between them
        foreach (var r in rows)
        {
            var g = r.Gem;
            bool free = r.Free > 0 && !r.Here;
            var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, CustomMinimumSize = new Vector2(0, 46), MouseDefaultCursorShape = free ? CursorShape.PointingHand : CursorShape.Arrow };
            foreach (var st in new[] { "normal", "pressed", "focus" }) b.AddThemeStyleboxOverride(st, new StyleBoxEmpty());
            b.AddThemeStyleboxOverride("hover", free ? new StyleBoxFlat { BgColor = new Color(1, 1, 1, 0.06f) } : new StyleBoxEmpty());
            if (free) b.Pressed += () => Set(g.Id);
            Nav.Id(b, $"gem:{g.Id}");
            var pic = ItemPhotos.StoneIcon(Items.Get(Supports.ItemId(g.Id)).Icon, 30, 24, 32, GemLook.Of(g).Lightened(0.25f));
            // the stone 30 x 24 in a 32 px box (the picture is wider than the box, centred on it)
            var box = new Control { CustomMinimumSize = new Vector2(32, 32), SizeFlagsVertical = SizeFlags.ShrinkCenter, MouseFilter = MouseFilterEnum.Ignore };
            pic.Position = Vector2.Zero;
            box.AddChild(pic);
            var count = Style.Label(r.Here ? $"set here · {r.Owned} owned · {r.Free} free" : free ? $"{r.Owned} owned · {r.Free} free" : "all set elsewhere", Style.Ui, 14, r.Here ? Style.Ember : Kit.Dim, false, HorizontalAlignment.Right);
            var nm = Style.Label(g.Name, Style.DisplayLight, 16, Kit.Ink);
            nm.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            var nameLine = Style.H(12, nm, count);
            var words = Style.V(0, nameLine, Style.Label(g.Text, Style.Text, 14, Kit.Ink2, false));
            words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            words.SizeFlagsVertical = SizeFlags.ShrinkBegin;
            var h = Style.H(12, box, words);
            h.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
            h.OffsetLeft = 8; h.OffsetRight = -8;
            h.MouseFilter = MouseFilterEnum.Ignore;
            b.AddChild(h);
            if (!free && !r.Here) b.Modulate = new Color(1, 1, 1, 0.45f);
            list.AddChild(b);
        }
        // "Take X out" a row right under the last gem, with a 14 px x mark
        if (held != null)
        {
            var o = new Button { FocusMode = FocusModeEnum.None, Flat = true, CustomMinimumSize = new Vector2(0, 46), MouseDefaultCursorShape = CursorShape.PointingHand };
            foreach (var st in new[] { "normal", "pressed", "focus" }) o.AddThemeStyleboxOverride(st, new StyleBoxEmpty());
            o.AddThemeStyleboxOverride("hover", new StyleBoxFlat { BgColor = new Color(1, 1, 1, 0.06f) });
            var lab = Style.Label($"Take {held.Name} out", Style.TextItalic, 14, Kit.Ink2, false);
            var xm = new XMark { CustomMinimumSize = new Vector2(32, 14), SizeFlagsVertical = SizeFlags.ShrinkCenter };
            var oh = Style.H(12, xm, lab);
            oh.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
            oh.OffsetLeft = 8; oh.OffsetRight = -8;
            oh.MouseFilter = MouseFilterEnum.Ignore;
            lab.SizeFlagsVertical = SizeFlags.ShrinkCenter;
            o.AddChild(oh);
            o.Pressed += () => Set(null);
            Nav.Id(o, "gem:out");
            list.AddChild(o);
        }
        block.AddChild(list);
        d.AddChild(block);
        foreach (var line in SocketModel.DontFitLines(ch.Gems, w.Id)) d.AddChild(Style.Label(line, Style.TextItalic, 14, Kit.Dim, true));
    }


    /// <summary>A Union has no sockets of its own: it takes both halves' gems, shown read-only under each half's name.</summary>
    void UnionSockets(VBoxContainer d, CharacterData ch, (string A, string B) halves, string sockUnion)
    {
        d.AddChild(Kit.Head("Sockets"));
        var got = new List<string>();
        foreach (var id in new[] { halves.A, halves.B })
            for (int i = 0; i < Supports.File.Sockets.Ranks.Count; i++)
                if (i < Supports.SocketsAt(SkillBook.RankOf(ch, id)) && Held(ch, id, i) is { } hg) got.Add(hg.Name);
        string unionName = Weapons.All.TryGetValue(sockUnion, out var uw) ? uw.Name : "The Union";
        d.AddChild(Style.Label($"{unionName} gets: {(got.Count == 0 ? "nothing yet" : string.Join(", ", got))}.", Style.TextItalic, 14, Kit.Dim, true));
        var cols = Style.H(30);
        foreach (var id in new[] { halves.A, halves.B })
        {
            if (!Weapons.All.TryGetValue(id, out var half)) continue;
            int rank = SkillBook.RankOf(ch, id), open = Supports.SocketsAt(rank);
            var wells = Style.H(18);
            for (int i = 0; i < Supports.File.Sockets.Ranks.Count; i++)
            {
                var gem = Held(ch, id, i);
                wells.AddChild(new GemSocket(i >= open ? GemSocket.Look.Closed : gem != null ? GemSocket.Look.Filled : GemSocket.Look.Empty, gem, 44).ReadOnly());
            }
            string hid = id;
            var link = new LinkButton { Text = half.Name + " ›", Underline = LinkButton.UnderlineMode.OnHover, FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand };
            Style.Font(link, Style.UiBold, 16, Style.Ember, false);
            link.AddThemeColorOverride("font_hover_color", Style.EmberHi);
            link.Pressed += () => { selSkill = hid; sockSkill = null; sockIdx = -1; Refresh(); };
            Nav.Id(link, $"half:{id}");
            cols.AddChild(Style.V(4, link, wells));
        }
        d.AddChild(cols);
    }

    Control SkillDetail(CharacterData ch, WeaponDef w)
    {
        var d = Style.V(6); // (6, so all eight gems fit the fixed window)
        d.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        bool known = SkillBook.Knows(ch, w.Id), carried = ch.Slotted.Contains(w.Id), meets = SkillBook.Meets(ch, w.Id);
        var col = ItemViews.SchoolColors[w.School];
        var m = new Medallion(88, "", Glyphs.ForSkill(w.Id, w.Art)) { Ink = col, Ring = carried ? Style.Ember : Style.Gold, Lit = carried };
        m.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        d.AddChild(Style.H(Style.Gap4, m, Style.V(2, Style.Label(w.Name.ToUpperInvariant(), Style.Display, 28, Kit.Ink),
            Style.Label($"{w.School.ToString().ToLowerInvariant()}  ·  {string.Join(", ", w.Tags.Select(t => t.ToString().ToLowerInvariant()))}", Style.UiBold, 14, col))));
        d.AddChild(Style.Label(w.Description, Style.Text, 17, Kit.Ink2, true));
        if (Weapons.IsUnion(w.Id)) { SocketBlock(d, ch, w); return d; }
        // What her calling's Hand does to it, in her hands in every fight (plain text; the look is the UI lead's).
        if (Content.Hands.Line(ch.Archetype, w) is { } hand) d.AddChild(Style.Label(hand, Style.Text, 16, Kit.Ink2, true));
        string attr = SkillBook.Attribute(w.Id);
        d.AddChild(Style.Label($"It asks {SkillBook.Need} {attr} of whoever uses it. You have {SkillBook.Have(ch, attr)}.{(meets ? "" : " Until you measure up (points, a respec), it lies idle.")}",
            Style.UiBold, 15, meets ? Style.Good : Style.Bad, true));
        d.AddChild(Style.Label($"It is {SocketModel.RankLine(SkillBook.Rank(ch), SkillBook.RankOf(ch, w.Id))}, and grows with you (every second level). In the arenas the ember starts from nothing, but what you carry is banked: it comes in at rank {Ranks[SkillBook.NightRank(ch)]}" +
            (ch.Level < 10 ? " (rank III from the tenth level)." : "."), Style.Ui, 14, Kit.Dim, true));
        if (known) SocketBlock(d, ch, w);
        if (!known)
            d.AddChild(Style.Label("You have seen it burn. Learn it from a tome (a story fight won, Vonnra's Curiosities), or your calling may teach it as you grow.", Style.TextItalic, 15, Kit.Dim, true));
        else if (!Safe)
            d.AddChild(Style.Label(carried ? "Carried. Change what you carry somewhere safe." : "Change what you carry somewhere safe: the Waystation, a quiet road.", Style.TextItalic, 14, Kit.Dim, true));
        else if (carried)
            d.AddChild(Nav.Id(Kit.Word($"Put {w.Name} down", () => G.Gear((j, _) => SkillBook.Unslot(j.Ch, w.Id)), Kit.Ink2, 17), "carry"));
        else if (ch.Slotted.Count < SkillBook.Slots(ch))
            d.AddChild(Nav.Id(Kit.Word($"Carry {w.Name}", () => G.Gear((j, _) => SkillBook.Slot(j.Ch, w.Id)), Style.EmberHi, 17), "carry"));
        else
            d.AddChild(Style.Label($"Your hands are full: put one down first. {SocketModel.MoreRoomLine(ch.Level)}", Style.TextItalic, 14, Kit.Dim, true));
        return d;
    }
}

/// <summary>A facet's socket as a small mark: an ember-filled ring when set, a lit ring when one can
/// be set, a faint ring otherwise.</summary>
public partial class FacetMark : Control
{
    readonly bool on, open;
    public FacetMark(bool on, bool open) { this.on = on; this.open = open; CustomMinimumSize = new Vector2(24, 24); MouseFilter = MouseFilterEnum.Ignore; }

    public override void _Draw()
    {
        var c = new Vector2(12, 12);
        if (on) { DrawCircle(c, 10, Style.Ember with { A = 0.25f }); DrawCircle(c, 5, Style.Ember); }
        DrawArc(c, 8, 0, Mathf.Tau, 24, on ? Style.EmberHi : open ? Style.GoldHi : Kit.Faint, 2, true);
    }
}

/// <summary>The road to mastery: the five ranks as nodes on a line (UI_RESEARCH 11), those reached
/// filled, this one lit in ember, the way to the next drawn as far as it has come, what each brings
/// under it.</summary>
public partial class RoadTrack : Control
{
    readonly int rank;
    readonly float toNext;
    static readonly string[] Gives = ["learned", "a facet", "stronger", "a second facet", "mastered"];

    public RoadTrack(int rank, float toNext)
    {
        this.rank = rank;
        this.toNext = toNext;
        CustomMinimumSize = new Vector2(0, 66);
        SizeFlagsHorizontal = SizeFlags.ExpandFill;
        MouseFilter = MouseFilterEnum.Ignore;
    }

    public override void _Draw()
    {
        float x0 = 40, x1 = Size.X - 40, y = 20, step = (x1 - x0) / 4;
        DrawLine(new Vector2(x0, y), new Vector2(x1, y), Kit.Rule.Lightened(0.15f), 1.5f, true);
        if (rank >= 1) DrawLine(new Vector2(x0, y), new Vector2(x0 + step * (rank - 1 + (rank < 5 ? toNext : 0)), y), Style.Ember with { A = 0.8f }, 2.5f, true);
        var font = Style.Display;
        for (int k = 1; k <= 5; k++)
        {
            var p = new Vector2(x0 + step * (k - 1), y);
            bool reached = k <= rank, here = k == rank;
            if (here) DrawCircle(p, 20, Style.Ember with { A = 0.15f });
            DrawCircle(p, 15, reached ? new Color("#2a1a10") : new Color("#16131a"));
            DrawArc(p, 15, 0, Mathf.Tau, 32, here ? Style.Ember : reached ? Style.Gold : Kit.Faint, here ? 2.5f : 1.5f, true);
            string n = ArtsScreen.Numerals[k - 1];
            var sz = font.GetStringSize(n, HorizontalAlignment.Left, -1, 14);
            DrawString(font, p + new Vector2(-sz.X / 2, 5), n, HorizontalAlignment.Left, -1, 14, here ? Style.EmberHi : reached ? Style.GoldHi : Kit.Faint);
            var g = Style.Ui;
            var gs = g.GetStringSize(Gives[k - 1], HorizontalAlignment.Left, -1, 13);
            DrawString(g, new Vector2(p.X - gs.X / 2, y + 36), Gives[k - 1], HorizontalAlignment.Left, -1, 13, reached ? Kit.Ink2 : Kit.Faint);
        }
    }
}

/// <summary>A small x mark (two strokes), for "take it out".</summary>
public partial class XMark : Control
{
    public override void _Draw()
    {
        var c = new Vector2(7, Size.Y / 2f);
        var ink = Kit.Ink2;
        DrawLine(c + new Vector2(-6, -6), c + new Vector2(6, 6), ink, 1.5f, true);
        DrawLine(c + new Vector2(6, -6), c + new Vector2(-6, 6), ink, 1.5f, true);
    }
}

/// <summary>A 6 px ember caret (an upward triangle) centred under the selected well's label; the space is kept when it is not drawn,
/// so the wells sit in the same places in every state (bd-ui W24).</summary>
public partial class WellCaret : Control
{
    public bool On;
    public override void _Draw()
    {
        if (!On) return;
        float cx = Size.X / 2f;
        DrawColoredPolygon([new Vector2(cx, 0), new Vector2(cx + 5, Size.Y), new Vector2(cx - 5, Size.Y)], Style.Ember);
    }
}
