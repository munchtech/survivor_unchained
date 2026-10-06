using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The arts the survivor knows (Rpg/ArtBook.cs), on the day's book's panel at the right with her in
/// the world beside it, as Self and the Pack are (approved: the book is one panel; no boxes). Its two
/// pages turn under the book's tabs: the art in hand, and the skills by day.
///
/// The art in hand: the arts known in a row of marks, the rest of the calling's faint with how they
/// are learned (Hades II's locked silhouettes); the art chosen, named large, its rank as a line of
/// nodes (the road to mastery), its facets as ruled lines of type, each set, to choose, or waiting
/// on a rank. An art is taken in hand, and a set facet changed, only where it is safe (out of a
/// fight); a facet newly opened by rank can be chosen anywhere. Skills by day: what is learned and
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
    bool skills;

    public ArtsScreen(Game g) : base(g) { }

    bool Safe => G.Battle is not { Combat: true };

    /// <summary>Its two pages turn with LT and RT (, and .).</summary>
    public override bool Key(Act a)
    {
        if (a is not (Act.SubNext or Act.SubPrev)) return false;
        skills = !skills;
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
        var pages = Kit.Tabs(new[] { "The art in hand", "Skills by day" }, skills ? 1 : 0, k => { skills = k == 1; Refresh(); }, 16, 28);
        pages.Alignment = BoxContainer.AlignmentMode.Center;
        v.AddChild(pages);
        v.AddChild(Style.Label(skills ? "What the arenas showed you, learned for the day; what you carry is banked for the night."
            : Safe ? "One art in hand. Each grows with use, and its ranks open facets." : "Out here you can choose a facet a rank has opened; change your art where it is safe.",
            Style.TextItalic, 15, Kit.Dim, true, HorizontalAlignment.Center));
        if (skills) BuildSkills(v);
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
            ? Kit.Prompts(Kit.Prompt(Act.Confirm, "Choose"), Kit.Prompt(Act.SubNext, skills ? "The art in hand" : "Skills by day"), Kit.Prompt(Act.TabNext, "Turn"), Kit.Prompt(Act.Cancel, "Close"))
            : Kit.Prompts(Kit.Prompt("Click", "Choose"), Kit.Prompt(G.Key(Act.SubPrev) + " " + G.Key(Act.SubNext), skills ? "The art in hand" : "Skills by day"), Kit.Prompt("[ ]", "Turn"), Kit.Prompt(G.Key(Act.Arts), "Close"));
        p.CustomMinimumSize = new Vector2(0, 30);
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
        else if (Safe) nameRow.AddChild(Nav.Id(Kit.Word("Take it in hand", () => G.Gear((j, b) => j.HoldArt(a.Id, b)), Style.EmberHi, 16), "hold"));
        else words.AddChild(Style.Label("Take it in hand somewhere safe: the Waystation, a quiet road.", Style.TextItalic, 15, Kit.Dim, true));
        head.AddChild(words);
        v.AddChild(head);
        if (known)
        {
            double xp = ch.Arts.TryGetValue(a.Id, out var st) ? st.Xp : 0;
            string next = rank < Abilities.MaxRank ? $"{xp:0} of {Abilities.RankXp[rank]:0} to rank {Numerals[rank]}" : "mastered";
            v.AddChild(Kit.Head("The road to mastery", $"+{(Abilities.RankPower(rank) - 1) * 100:0}% strength, {(1 - Abilities.RankHaste(rank)) * 100:0}% shorter wait  ·  {next}"));
            v.AddChild(new RoadTrack(rank, rank < Abilities.MaxRank ? (float)ArtBook.Progress(ch, a.Id) : 1));
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

    /* ------------------------------------------------------ skills by day -- */

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
        if (ch.Skills.Count == 0) list.AddChild(Style.Label("None yet. What burns in the arenas can be learned by day.", Style.TextItalic, 15, Kit.Dim, true));
        foreach (var id in ch.Skills) list.AddChild(SkillEntry(ch, id, true));
        if (seen.Count > 0)
        {
            list.AddChild(Kit.Head("Seen in the arenas", "not yet learned"));
            foreach (var id in seen) list.AddChild(SkillEntry(ch, id, false));
        }
        int unseen = Weapons.Pool.Count(id => !ch.Discovered.Contains(id));
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
        d.AddChild(Style.Label("The night's arenas burn with skills the ember lends you. By day you can keep them.", Style.Text, 17, Kit.Ink2, true));
        foreach (var (glyph, title, text) in new[]
        {
            ("flame", "Seen", "An arena shows it to you: the ember offers it in a draft, and you use it."),
            ("book", "Learned", "A tome teaches it: a story fight won, Vonnra's Curiosities; your calling may teach one as you grow."),
            ("embers", "Carried", "Carry it by day and it is banked: the ember offers it in the night's first drafts, at a higher rank."),
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
        bool carried = ch.Slotted.Contains(id), meets = SkillBook.Meets(ch, id), on = selSkill == id;
        var b = new Button { FocusMode = FocusModeEnum.None, Flat = true, MouseDefaultCursorShape = CursorShape.PointingHand, CustomMinimumSize = new Vector2(0, 50) };
        foreach (var s in new[] { "normal", "hover", "pressed", "focus" }) b.AddThemeStyleboxOverride(s, new StyleBoxEmpty());
        if (on) b.AddThemeStyleboxOverride("normal", new StyleBoxFlat { BgColor = Colors.Transparent, BorderColor = Style.Ember, BorderWidthLeft = 2 });
        b.Pressed += () => { selSkill = id; Sound.Sfx.Click(); Refresh(); };
        Nav.Id(b, $"skill:{id}");
        var col = ItemViews.SchoolColors[w.School];
        var r = Style.H(12, Glyphs.Icon(w.Art, 26, known ? col : col with { A = 0.45f }));
        string attr = SkillBook.Attribute(id);
        var words = Style.V(0, Style.Label(w.Name + (carried ? (meets ? "  ·  carried" : "  ·  idle") : ""), Style.DisplayLight, 16, known ? (carried ? Kit.Ink : Kit.Ink2) : Kit.Dim),
            Style.Label($"asks {SkillBook.Need} {attr}  ·  you have {SkillBook.Have(ch, attr)}", Style.Ui, 13, meets ? Style.Good : Style.Bad));
        r.AddChild(words);
        r.Position = new Vector2(10, 4);
        r.MouseFilter = MouseFilterEnum.Ignore;
        b.AddChild(r);
        return b;
    }

    Control SkillDetail(CharacterData ch, WeaponDef w)
    {
        var d = Style.V(8);
        d.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        bool known = SkillBook.Knows(ch, w.Id), carried = ch.Slotted.Contains(w.Id), meets = SkillBook.Meets(ch, w.Id);
        var col = ItemViews.SchoolColors[w.School];
        var m = new Medallion(88, "", w.Art) { Ink = col, Ring = carried ? Style.Ember : Style.Gold, Lit = carried };
        m.SizeFlagsVertical = SizeFlags.ShrinkBegin;
        d.AddChild(Style.H(Style.Gap4, m, Style.V(2, Style.Label(w.Name.ToUpperInvariant(), Style.Display, 28, Kit.Ink),
            Style.Label($"{w.School.ToString().ToLowerInvariant()}  ·  {string.Join(", ", w.Tags.Select(t => t.ToString().ToLowerInvariant()))}", Style.UiBold, 14, col))));
        d.AddChild(Style.Label(w.Description, Style.Text, 17, Kit.Ink2, true));
        string attr = SkillBook.Attribute(w.Id);
        d.AddChild(Style.Label($"It asks {SkillBook.Need} {attr} of whoever uses it. You have {SkillBook.Have(ch, attr)}.{(meets ? "" : " Until you measure up (points, a respec), it lies idle.")}",
            Style.UiBold, 15, meets ? Style.Good : Style.Bad, true));
        d.AddChild(Style.Label($"By day it is rank {Ranks[SkillBook.Rank(ch)]}, and grows with you (every third level). In the night's arenas the ember starts from nothing, but what you carry by day is banked: it comes in at rank {Ranks[SkillBook.NightRank(ch)]}" +
            (ch.Level < 10 ? " (rank III from the tenth level)." : "."), Style.Ui, 14, Kit.Dim, true));
        if (!known)
            d.AddChild(Style.Label("You have seen it burn. Learn it from a tome (a story fight won, Vonnra's Curiosities), or your calling may teach it as you grow.", Style.TextItalic, 15, Kit.Dim, true));
        else if (!Safe)
            d.AddChild(Style.Label(carried ? "Carried. Change what you carry somewhere safe." : "Change what you carry somewhere safe: the Waystation, a quiet road.", Style.TextItalic, 14, Kit.Dim, true));
        else if (carried)
            d.AddChild(Nav.Id(Kit.Word($"Put {w.Name} down", () => G.Gear((j, _) => SkillBook.Unslot(j.Ch, w.Id)), Kit.Ink2, 17), "carry"));
        else if (ch.Slotted.Count < SkillBook.Slots(ch))
            d.AddChild(Nav.Id(Kit.Word($"Carry {w.Name}", () => G.Gear((j, _) => SkillBook.Slot(j.Ch, w.Id)), Style.EmberHi, 17), "carry"));
        else
            d.AddChild(Style.Label("Your hands are full: put one down first. More room comes at the fourth level and the eighth.", Style.TextItalic, 14, Kit.Dim, true));
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
