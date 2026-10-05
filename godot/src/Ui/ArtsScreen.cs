using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The arts the survivor knows (Rpg/ArtBook.cs): which is in hand, how far
/// each has come, and its facets. An art is taken in hand, and a chosen
/// facet changed, only where it is safe (out of a fight); a facet newly
/// opened by rank can be chosen anywhere. And, on its second page, the
/// skills learned for the day (Rpg/SkillBook.cs): which are carried, what
/// each asks of the survivor, and what the arenas have shown them.
/// </summary>
public partial class ArtsScreen : Overlay
{
    public override string Kind => "arts";
    public override Act? Toggle => Act.Arts;

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
        var page = Page(skills ? "Skills by Day" : "Arts",
            skills ? "What the arenas showed you, learned for the day; what you carry is banked for the night"
            : Safe ? "One art in hand. Each grows with use, and its ranks open facets" : "Out here you can choose a facet a rank has opened; change your art where it is safe");
        // The screen's two pages, turned with LT and RT.
        bool pad = Controls.Instance.UsingPad;
        var tabs = Style.H(8, pad ? Style.PadButton("LT") : Style.Key(G.Key(Act.SubPrev)),
            Nav.Skip(Style.Segment("The art in hand", !skills, () => { skills = false; Refresh(); })), Nav.Skip(Style.Segment("Skills by day", skills, () => { skills = true; Refresh(); })),
            pad ? Style.PadButton("RT") : Style.Key(G.Key(Act.SubNext)));
        tabs.Position = Vector2.Zero;
        page.AddChild(tabs);
        if (pad) PageFooter(Footer((Act.Confirm, "Choose"), (Act.SubNext, skills ? "The art in hand" : "Skills by day"), (Act.TabPrev, "Self"), (Act.TabNext, "Journal"), (Act.Cancel, "Close")));
        if (skills) { BuildSkills(page); return; }

        // Every art the calling could know, as medallions: learned first, then the rest, dim.
        var pane = Pane(page, new Rect2(0, 56, 560, 864));
        var left = Style.V(Style.Gap3);
        left.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var scroll = Style.Scroll(left);
        scroll.SizeFlagsVertical = SizeFlags.ExpandFill;
        pane.AddChild(scroll);
        left.AddChild(new Section($"Known  ·  {known.Count}"));
        left.AddChild(Medals(ch, known.Select(Abilities.ById), true));
        var rest = Abilities.All.Values.Where(a => !known.Contains(a.Id) && Abilities.Learnable(a, ch.Archetype)).ToList();
        if (rest.Count > 0)
        {
            left.AddChild(new Section("Not yet learned", "manuals teach them"));
            left.AddChild(Medals(ch, rest, false));
        }

        // The art chosen, on its altar: the great medallion, its rank, its sockets, its four facets.
        var right = Pane(page, new Rect2(590, 56, 1250, 864), null, Style.Gap4);
        if (sel != null && Abilities.Find(sel) is { } def) Altar(right, ch, def, known.Contains(def.Id));
    }

    /// <summary>A grid of arts as medallions, each with its name under it.</summary>
    Control Medals(CharacterData ch, System.Collections.Generic.IEnumerable<AbilityDef> arts, bool known)
    {
        var grid = new GridContainer { Columns = 3, MouseFilter = MouseFilterEnum.Ignore };
        grid.AddThemeConstantOverride("h_separation", 12);
        grid.AddThemeConstantOverride("v_separation", 12);
        foreach (var a in arts)
        {
            bool held = ch.Ability == a.Id, on = sel == a.Id;
            int rank = known ? ArtBook.Rank(ch, a.Id) : 0;
            var id = a.Id;
            var b = Style.Button("", () => { sel = id; Refresh(); }, false, true);
            Nav.Mark(b, $"art:{a.Id}", () => { sel = id; Refresh(); });
            b.CustomMinimumSize = new Vector2(160, 178);
            var box = OrnateBox.Make(OrnateBox.Kind.Slab, 8, held ? Style.Ember : Style.Gold);
            if (on) b.AddThemeStyleboxOverride("normal", box);
            var v = Style.V(4);
            v.MouseFilter = MouseFilterEnum.Ignore;
            v.Position = new Vector2(8, 8);
            v.Size = new Vector2(144, 160);
            var m = new Medallion(104, "", a.Icon)
            {
                Arc = known && rank < Abilities.MaxRank ? (float)ArtBook.Progress(ch, a.Id) : 0,
                Ring = held ? Style.Ember : known ? Style.Gold : Style.InkFaint,
                Ink = known ? (held ? Style.EmberHi : Style.GoldHi) : Style.InkDim with { A = 0.6f },
                Core = known ? new Color("#3a2210") : new Color("#16131a"),
                Lit = held,
            };
            var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            mc.AddChild(m);
            v.AddChild(mc);
            v.AddChild(Style.Label(a.Name, Style.UiBold, Style.Small, known ? (held ? Style.EmberHi : Style.GoldHi) : Style.InkDim, true, HorizontalAlignment.Center));
            v.AddChild(Style.Label(known ? (held ? "in hand" : $"rank {Numerals[rank - 1]}") + (ArtBook.OpenSlots(ch, a.Id) > 0 ? "  ·  a facet!" : "") : Roles[a.Role].Name,
                Style.Ui, Style.Caption, known ? Roles[a.Role].Color : Style.InkFaint, false, HorizontalAlignment.Center));
            b.AddChild(v);
            grid.AddChild(b);
        }
        return grid;
    }

    void Altar(VBoxContainer d, CharacterData ch, AbilityDef a, bool known)
    {
        int rank = known ? ArtBook.Rank(ch, a.Id) : 0;
        var role = Roles[a.Role];
        bool held = ch.Ability == a.Id;
        var head = Style.H(Style.Gap5);
        // The great medallion with its two sockets beneath: the facets' places, opened by rank.
        var shrine = Style.V(Style.Gap2);
        shrine.Alignment = BoxContainer.AlignmentMode.Center;
        var big = new Medallion(220, "", a.Icon)
        {
            Arc = known && rank < Abilities.MaxRank ? (float)ArtBook.Progress(ch, a.Id) : known ? 1 : 0,
            Ring = held ? Style.Ember : known ? Style.Gold : Style.InkFaint,
            Ink = known ? Style.GoldHi : Style.InkDim,
            Lit = held,
        };
        var bc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        bc.AddChild(big);
        shrine.AddChild(bc);
        int slots = Abilities.FacetSlots(rank), chosen = known ? ArtBook.Facets(ch, a.Id).Count : 0;
        var sockets = Style.H(Style.Gap4);
        sockets.Alignment = BoxContainer.AlignmentMode.Center;
        for (int k = 0; k < 2; k++)
        {
            bool open = k < slots, filled = k < chosen;
            var sm = new Medallion(54, open ? "" : Numerals[k == 0 ? 1 : 3], filled ? "arcane" : null)
            {
                Ring = filled ? Style.Ember : open ? Style.GoldHi : Style.InkFaint,
                Core = filled ? new Color("#4a1c0c") : new Color("#120f14"),
                Ink = filled ? Style.EmberHi : Style.InkDim,
                Lit = open && !filled,
            };
            var sv = Style.V(2, sm, Style.Label(filled ? "set" : open ? "open" : $"rank {Numerals[k == 0 ? 1 : 3]}", Style.Ui, Style.Caption, filled ? Style.EmberHi : open ? Style.GoldHi : Style.InkFaint, false, HorizontalAlignment.Center));
            sockets.AddChild(sv);
        }
        shrine.AddChild(sockets);
        head.AddChild(shrine);

        var words = Style.V(Style.Gap2);
        words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        words.AddChild(Style.Label(a.Name.ToUpperInvariant(), Style.Display, 44, held ? Style.EmberHi : Style.GoldHi));
        words.AddChild(Style.Label($"{role.Name}{(a.Movement ? "  ·  a way of moving" : $"  ·  a {Callings.Archetype(a.Calling!).Name}'s art")}  ·  {a.Cooldown:0} s{(a.Interrupts ? "  ·  breaks channels" : "")}", Style.UiBold, Style.Small, role.Color));
        words.AddChild(Style.Label(a.Description, Style.Text, Style.Lead, Style.Ink, true));
        if (!known)
        {
            words.AddChild(Style.Label("Not yet learned. A manual teaches it: the thing that rules an arena carries one, and they turn up in the packs of the dead.", Style.TextItalic, Style.Small, Style.InkDim, true));
        }
        else
        {
            double xp = ch.Arts.TryGetValue(a.Id, out var st) ? st.Xp : 0;
            string next = rank < Abilities.MaxRank ? $"{xp:0} / {Abilities.RankXp[rank]:0} to rank {Numerals[rank]}" : "Mastered";
            words.AddChild(Style.Gap(Style.Gap1));
            words.AddChild(Style.H(Style.Gap3, Style.Label($"Rank {Numerals[rank - 1]}", Style.Display, 26, Style.GoldHi), SheetScreen.Bar(rank < Abilities.MaxRank ? ArtBook.Progress(ch, a.Id) : 1, next, Style.Ember, 460)));
            words.AddChild(Style.Label($"+{(Abilities.RankPower(rank) - 1) * 100:0}% strength, {(1 - Abilities.RankHaste(rank)) * 100:0}% shorter wait.  It grows with every use, and with what dies while it is fresh.", Style.Ui, Style.Small, Style.InkDim, true));
            if (held) words.AddChild(Style.Label("IN HAND", Style.UiHeavy, Style.Body, Style.EmberHi));
            else if (Safe) words.AddChild(Style.Button($"Take {a.Name} in hand", () => G.Gear((j, b) => j.HoldArt(a.Id, b)), true));
            else words.AddChild(Style.Label("Take it in hand somewhere safe: the Waystation, a quiet road.", Style.TextItalic, Style.Small, Style.InkDim, true));
        }
        head.AddChild(words);
        d.AddChild(head);
        d.AddChild(Facets(ch, a, known));
        d.AddChild(Road(rank));
    }

    /// <summary>The road to mastery: the five ranks in a line, what each brings, this one lit.</summary>
    static Control Road(int rank)
    {
        var v = Style.V(Style.Gap2, new Section("The road to mastery", "every use, and what dies while it is fresh"));
        var row = Style.H(0);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        for (int k = 1; k <= Abilities.MaxRank; k++)
        {
            bool reached = k <= rank, here = k == rank;
            string gives = k switch { 2 => "a facet", 4 => "a second facet", 5 => "mastered", 1 => "learned", _ => "stronger" };
            var m = new Medallion(here ? 64 : 52, Numerals[k - 1])
            {
                Ring = here ? Style.Ember : reached ? Style.Gold : Style.InkFaint,
                Ink = here ? Style.EmberHi : reached ? Style.GoldHi : Style.InkDim,
                Core = reached ? new Color("#3a2210") : new Color("#120f14"),
                Lit = here,
            };
            var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(0, 66) };
            mc.AddChild(m);
            var col = Style.V(2, mc,
                Style.Label(gives, Style.UiBold, Style.Caption, reached ? Style.GoldHi : Style.InkDim, false, HorizontalAlignment.Center),
                Style.Label($"+{(Abilities.RankPower(k) - 1) * 100:0}% strength", Style.Ui, Style.Caption, Style.InkFaint, false, HorizontalAlignment.Center));
            col.CustomMinimumSize = new Vector2(150, 0);
            row.AddChild(col);
            if (k < Abilities.MaxRank)
            {
                // The road between two ranks: gold where it is walked.
                var line = new ColorRect { Color = k < rank ? Style.Gold : Style.Line, CustomMinimumSize = new Vector2(70, 2), SizeFlagsVertical = SizeFlags.ShrinkBegin, MouseFilter = MouseFilterEnum.Ignore };
                var lw = new MarginContainer { MouseFilter = MouseFilterEnum.Ignore };
                lw.AddThemeConstantOverride("margin_top", 32);
                lw.AddChild(line);
                row.AddChild(lw);
            }
        }
        v.AddChild(row);
        return v;
    }

    /// <summary>The four facets as cards, each with its socket at its head: set, to choose, or waiting on a rank.</summary>
    Control Facets(CharacterData ch, AbilityDef a, bool known)
    {
        var v = Style.V(Style.Gap2);
        int rank = known ? ArtBook.Rank(ch, a.Id) : 0;
        int slots = Abilities.FacetSlots(rank);
        var chosen = known ? ArtBook.Facets(ch, a.Id) : new();
        string opens = slots == 0 ? "rank II opens the first" : slots == 1 ? "rank IV opens the second" : "both open";
        v.AddChild(new Section("Facets", !known ? "learn the art to set them" : slots == 0 ? opens : $"{chosen.Count} of {slots} set  ·  {opens}"));
        var row = Style.H(Style.Gap3);
        foreach (var f in a.Facets)
        {
            bool on = chosen.Contains(f.Id);
            bool canPick = known && !on && chosen.Count < slots;
            bool canDrop = known && on && Safe;
            var accent = on ? Style.Ember : canPick ? Style.GoldHi : Style.InkFaint;
            var box = OrnateBox.Make(OrnateBox.Kind.Card, 14, accent);
            box.Crest = 70;
            var b = Style.Button("", canPick ? () => G.Gear((j, bt) => j.ChooseFacet(a.Id, f.Id, true, bt)) : canDrop ? () => G.Gear((j, bt) => j.ChooseFacet(a.Id, f.Id, false, bt)) : null);
            foreach (var stt in new[] { "normal", "hover", "pressed", "disabled" }) b.AddThemeStyleboxOverride(stt, box);
            b.CustomMinimumSize = new Vector2(287, 280);
            Nav.Id(b, $"facet:{f.Id}");
            b.Disabled = !canPick && !canDrop;
            var inner = Style.V(Style.Gap2);
            inner.MouseFilter = MouseFilterEnum.Ignore;
            inner.Position = new Vector2(16, 16);
            inner.Size = new Vector2(255, 248);
            var socket = new Medallion(58, "", on ? "arcane" : null)
            {
                Ring = on ? Style.Ember : canPick ? Style.GoldHi : Style.InkFaint,
                Core = on ? new Color("#4a1c0c") : new Color("#120f14"),
                Ink = Style.EmberHi,
                Lit = canPick,
            };
            var sc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            sc.AddChild(socket);
            inner.AddChild(sc);
            inner.AddChild(Style.Label(f.Name, Style.Display, 21, on ? Style.EmberHi : canPick ? Style.GoldHi : Style.Ink, true, HorizontalAlignment.Center));
            var text = Style.Label(f.Text, Style.Ui, Style.Small, on || canPick ? Style.Ink : Style.InkDim, true, HorizontalAlignment.Center);
            text.SizeFlagsVertical = SizeFlags.ExpandFill;
            inner.AddChild(text);
            inner.AddChild(Style.Label(on ? (Safe ? "SET  ·  CHOOSE AGAIN" : "SET") : canPick ? "CHOOSE" : !known ? "" : slots == 0 ? "OPENS AT RANK II" : "SOCKETS FULL",
                Style.UiHeavy, Style.Caption, on ? Style.EmberHi : canPick ? Style.GoldHi : Style.InkFaint, false, HorizontalAlignment.Center));
            b.AddChild(inner);
            if (canDrop) b.TooltipText = "Choose again (frees the socket)";
            row.AddChild(b);
        }
        v.AddChild(row);
        return v;
    }

    /* ------------------------------------------------------ skills by day -- */

    static readonly string[] Ranks = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"];
    string? selSkill;

    void BuildSkills(Control page)
    {
        var ch = G.Journey.Ch;
        var seen = ch.Discovered.Where(id => Weapons.All.TryGetValue(id, out var w) && w.Findable && !SkillBook.Knows(ch, id)).ToList();
        selSkill ??= ch.Slotted.FirstOrDefault() ?? ch.Skills.FirstOrDefault() ?? seen.FirstOrDefault();
        var left = Pane(page, new Rect2(0, 56, 560, 864));
        var list = Style.V(6);
        list.AddChild(new Section("Learned", $"carrying {SkillBook.Carried(ch).Count()} of {SkillBook.Slots(ch)}"));
        if (ch.Skills.Count == 0) list.AddChild(Style.Label("None yet. What burns in the arenas can be learned by day.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        foreach (var id in ch.Skills) list.AddChild(SkillEntry(ch, id, true));
        if (seen.Count > 0)
        {
            list.AddChild(Style.Gap(6));
            list.AddChild(new Section("Seen in the arenas", "not yet learned"));
            foreach (var id in seen) list.AddChild(SkillEntry(ch, id, false));
        }
        int unseen = Weapons.Pool.Count(id => !ch.Discovered.Contains(id));
        if (unseen > 0)
        {
            // The ones still to see, as blank medallions: the collection shows its gaps.
            list.AddChild(Style.Gap(6));
            list.AddChild(new Section("Not yet shown", $"{unseen} more burn in the arenas"));
            var blanks = new GridContainer { Columns = 6, MouseFilter = MouseFilterEnum.Ignore };
            blanks.AddThemeConstantOverride("h_separation", 12);
            blanks.AddThemeConstantOverride("v_separation", 12);
            for (int i = 0; i < unseen; i++) blanks.AddChild(new Medallion(70, "?") { Ring = Style.InkFaint, Ink = Style.InkFaint, Core = new Color("#120f14") });
            list.AddChild(blanks);
        }
        var scroll = Style.Scroll(list);
        scroll.SizeFlagsVertical = SizeFlags.ExpandFill;
        left.AddChild(scroll);
        var right = Pane(page, new Rect2(590, 56, 1250, 864), null, Style.Gap4);
        if (selSkill != null && Weapons.All.TryGetValue(selSkill, out var def)) right.AddChild(SkillDetail(ch, def));
        else HowSkillsCome(right);
    }

    /// <summary>With nothing learned yet, the page says how a skill comes to you, as three steps.</summary>
    static void HowSkillsCome(VBoxContainer d)
    {
        d.AddChild(Style.Label("HOW A SKILL COMES TO YOU", Style.Display, 32, Style.GoldHi));
        d.AddChild(Style.Label("The night's arenas burn with skills the ember lends you. By day you can keep them.", Style.Text, Style.Lead, Style.Ink, true));
        var row = Style.H(Style.Gap4);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        foreach (var (glyph, title, text) in new[]
        {
            ("flame", "Seen", "An arena shows it to you: the ember offers it in a draft, and you use it."),
            ("book", "Learned", "A tome teaches it: a story fight won, Vonnra's Curiosities; your calling may teach one as you grow."),
            ("embers", "Carried", "Carry it by day and it is banked: the ember offers it in the night's first drafts, at a higher rank."),
        })
        {
            var box = OrnateBox.Make(OrnateBox.Kind.Card, 18, Style.Gold);
            box.Crest = 80;
            var card = Style.Panel(box);
            card.CustomMinimumSize = new Vector2(360, 290);
            var v = Style.V(Style.Gap2);
            var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
            mc.AddChild(new Medallion(120, "", glyph));
            v.AddChild(mc);
            v.AddChild(Style.Label(title.ToUpperInvariant(), Style.Display, 24, Style.GoldHi, false, HorizontalAlignment.Center));
            v.AddChild(Style.Label(text, Style.Ui, Style.Small, Style.Ink, true, HorizontalAlignment.Center));
            card.AddChild(v);
            row.AddChild(card);
        }
        d.AddChild(Style.Gap(Style.Gap3));
        d.AddChild(row);
    }

    Control SkillEntry(CharacterData ch, string id, bool known)
    {
        var w = Weapons.All[id];
        bool carried = ch.Slotted.Contains(id), meets = SkillBook.Meets(ch, id), on = selSkill == id;
        var b = Style.Button("", () => { selSkill = id; Refresh(); });
        Nav.Id(b, $"skill:{id}");
        b.CustomMinimumSize = new Vector2(500, 64);
        if (on) b.AddThemeStyleboxOverride("normal", UiArt.Frame("row_on", Style.Box(new Color("#3a2614"), Style.LineHi, 2, 4)));
        var col = ItemViews.SchoolColors[w.School];
        var r = Style.H(12, Glyphs.Icon(w.Art, 28, known ? col : col with { A = 0.45f }));
        string attr = SkillBook.Attribute(id);
        string tag = $"asks {SkillBook.Need} {attr}  ·  you have {SkillBook.Have(ch, attr)}";
        var words = Style.V(0, Style.Label(w.Name + (carried ? (meets ? "  ·  carried, banked" : "  ·  idle") : ""), Style.Display, 17, known ? (carried ? Colors.White : Style.GoldHi) : Style.InkDim),
            Style.Label(tag, Style.Ui, Style.Caption, meets ? Style.Good : Style.Bad));
        words.CustomMinimumSize = new Vector2(340, 0);
        r.AddChild(words);
        r.Position = new Vector2(12, 8);
        r.MouseFilter = MouseFilterEnum.Ignore;
        b.AddChild(r);
        return b;
    }

    Control SkillDetail(CharacterData ch, WeaponDef w)
    {
        var d = Style.V(10);
        d.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        bool known = SkillBook.Knows(ch, w.Id), carried = ch.Slotted.Contains(w.Id), meets = SkillBook.Meets(ch, w.Id);
        var col = ItemViews.SchoolColors[w.School];
        var head = Style.H(Style.Gap4, new Medallion(160, "", w.Art) { Ink = col, Ring = carried ? Style.Ember : Style.Gold, Lit = carried });
        head.AddChild(Style.V(2, Style.Label(w.Name.ToUpperInvariant(), Style.Display, 40, Style.GoldHi),
            Style.Label($"{w.School.ToString().ToLowerInvariant()}  ·  {string.Join(", ", w.Tags.Select(t => t.ToString().ToLowerInvariant()))}", Style.UiBold, Style.Caption, col)));
        d.AddChild(head);
        d.AddChild(Style.Label(w.Description, Style.Text, Style.Lead, Style.Ink, true));
        string attr = SkillBook.Attribute(w.Id);
        d.AddChild(Style.Label($"It asks {SkillBook.Need} {attr} of whoever uses it. You have {SkillBook.Have(ch, attr)}.{(meets ? "" : " Until you measure up (points, a respec), it lies idle.")}",
            Style.UiBold, Style.Small, meets ? Style.Good : Style.Bad, true));
        d.AddChild(Style.Label($"By day it is rank {Ranks[SkillBook.Rank(ch)]}, and grows with you (every third level). In the night's arenas the ember starts from nothing, but what you carry by day is banked: it sleeps in you through the day, the ember offers it in its first drafts, and it comes in at rank {Ranks[SkillBook.NightRank(ch)]}" +
            (ch.Level < 10 ? " (rank III from the tenth level)." : "."), Style.Ui, Style.Caption, Style.InkDim, true));
        d.AddChild(Style.Gap(6));
        if (!known)
            d.AddChild(Style.Label("You have seen it burn. Learn it from a tome (a story fight won, Vonnra's Curiosities), or your calling may teach it as you grow.", Style.TextItalic, Style.Small, Style.InkDim, true));
        else if (!Safe)
            d.AddChild(Style.Label(carried ? "Carried. Change what you carry somewhere safe." : "Change what you carry somewhere safe: the Waystation, a quiet road.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        else if (carried)
            d.AddChild(Style.Button($"Put {w.Name} down", () => G.Gear((j, _) => SkillBook.Unslot(j.Ch, w.Id))));
        else if (ch.Slotted.Count < SkillBook.Slots(ch))
            d.AddChild(Style.Button($"Carry {w.Name}", () => G.Gear((j, _) => SkillBook.Slot(j.Ch, w.Id)), true));
        else
            d.AddChild(Style.Label("Your hands are full: put one down first. More room comes at the fourth level and the eighth.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        return d;
    }
}
