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
/// opened by rank can be chosen anywhere.
/// </summary>
public partial class ArtsScreen : Overlay
{
    public override string Kind => "arts";
    public override Act? Toggle => Act.Arts;

    static readonly string[] Numerals = ["I", "II", "III", "IV", "V"];
    static readonly System.Collections.Generic.Dictionary<ArtRole, (string Name, Color Color)> Roles = new()
    {
        [ArtRole.Tank] = ("Holds the line", new Color("#d8b870")), [ArtRole.Damage] = ("Deals death", new Color("#e8866a")),
        [ArtRole.Healing] = ("Mends", new Color("#8ad48a")), [ArtRole.Utility] = ("Gets you out", new Color("#8ac0e8")),
        [ArtRole.Control] = ("Holds them", new Color("#c8a0f0")),
    };

    string? sel;

    public ArtsScreen(Game g) : base(g) { }

    bool Safe => G.Battle is not { Combat: true };

    protected override void Build()
    {
        var ch = G.Journey.Ch;
        var known = ArtBook.Known(ch);
        sel ??= ch.Ability != "" ? ch.Ability : known.FirstOrDefault();
        var v = Frame("Arts", new Vector2(1340, 760), G.Key(Act.Arts),
            Safe ? "One art in hand. Each grows with use, and its ranks open facets." : "Out here you can choose a facet a rank has opened. Change your art where it is safe.");
        var row = Style.H(26);
        v.AddChild(row);

        // Every art the calling could know: learned ones first, then the rest, dim.
        var list = Style.V(6);
        list.CustomMinimumSize = new Vector2(430, 0);
        list.AddChild(Style.SubLabel($"Known  ·  {known.Count}"));
        foreach (var id in known) list.AddChild(Entry(ch, Abilities.ById(id), true));
        var rest = Abilities.All.Values.Where(a => !known.Contains(a.Id) && Abilities.Learnable(a, ch.Archetype)).ToList();
        if (rest.Count > 0)
        {
            list.AddChild(Style.Gap(6));
            list.AddChild(Style.SubLabel("Not yet learned  ·  from manuals"));
            foreach (var a in rest) list.AddChild(Entry(ch, a, false));
        }
        var scroll = Style.Scroll(list);
        scroll.CustomMinimumSize = new Vector2(450, 640);
        row.AddChild(scroll);

        if (sel != null && Abilities.Find(sel) is { } def) row.AddChild(Detail(ch, def, known.Contains(def.Id)));
    }

    Control Entry(CharacterData ch, AbilityDef a, bool known)
    {
        bool held = ch.Ability == a.Id, on = sel == a.Id;
        int rank = ArtBook.Rank(ch, a.Id);
        var b = Style.Button("", () => { sel = a.Id; Refresh(); });
        b.CustomMinimumSize = new Vector2(420, 62);
        if (on) b.AddThemeStyleboxOverride("normal", Style.Box(new Color("#3a2614"), Style.LineHi, 2, 4));
        var tint = !known ? Style.InkDim with { A = 0.5f } : held ? Style.EmberHi : Style.Gold;
        var r = Style.H(12, Glyphs.Icon(a.Icon, 28, tint));
        var role = Roles[a.Role];
        string tag = known ? $"{role.Name}  ·  rank {Numerals[rank - 1]}" + (ArtBook.OpenSlots(ch, a.Id) > 0 ? "  ·  a facet to choose" : "") : role.Name;
        var words = Style.V(0, Style.Label(a.Name + (held ? "  ·  in hand" : ""), Style.Display, 17, known ? (held ? Colors.White : Style.GoldHi) : Style.InkDim),
            Style.Label(tag, Style.Ui, 13, known ? role.Color : Style.InkDim with { A = 0.6f }));
        words.CustomMinimumSize = new Vector2(340, 0);
        r.AddChild(words);
        r.Position = new Vector2(12, 8);
        r.MouseFilter = MouseFilterEnum.Ignore;
        b.AddChild(r);
        return b;
    }

    Control Detail(CharacterData ch, AbilityDef a, bool known)
    {
        var d = Style.V(10);
        d.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        int rank = ArtBook.Rank(ch, a.Id);
        var role = Roles[a.Role];
        var head = Style.H(16, Glyphs.Icon(a.Icon, 64, Style.GoldHi));
        var names = Style.V(2, Style.Label(a.Name, Style.Display, 32, Style.GoldHi),
            Style.Label($"{role.Name}{(a.Movement ? "  ·  a way of moving" : $"  ·  a {Callings.Archetype(a.Calling!).Name}'s art")}  ·  {a.Cooldown:0} s{(a.Interrupts ? "  ·  breaks channels" : "")}", Style.UiBold, 14, role.Color));
        head.AddChild(names);
        d.AddChild(head);
        d.AddChild(Style.Label(a.Description, Style.Text, 17, Style.Ink, true));
        if (!known)
        {
            d.AddChild(Style.Gap(8));
            d.AddChild(Style.Label($"Not yet learned. A manual teaches it: they are found in map hoards, altars' caches and the packs of the dead.", Style.TextItalic, 15, Style.InkDim, true));
            d.AddChild(Facets(ch, a, false));
            return d;
        }

        // How far it has come.
        double xp = ch.Arts.TryGetValue(a.Id, out var st) ? st.Xp : 0;
        var bar = new ProgressBar { MinValue = 0, MaxValue = 1, Value = ArtBook.Progress(ch, a.Id), ShowPercentage = false, CustomMinimumSize = new Vector2(0, 10) };
        bar.AddThemeStyleboxOverride("background", Style.Box(new Color(0.1f, 0.08f, 0.07f), Style.Line, 1, 3, 0));
        bar.AddThemeStyleboxOverride("fill", Style.Box(Style.Ember, Style.Ember, 0, 3, 0));
        string next = rank < Abilities.MaxRank ? $"{xp:0} / {Abilities.RankXp[rank]:0} to rank {Numerals[rank]}" : "Mastered";
        d.AddChild(Style.H(10, Style.Label($"Rank {Numerals[rank - 1]}", Style.UiBold, 16, Style.GoldHi), Style.Label(next, Style.Ui, 14, Style.InkDim)));
        d.AddChild(bar);
        d.AddChild(Style.Label($"+{(Abilities.RankPower(rank) - 1) * 100:0}% strength, {(1 - Abilities.RankHaste(rank)) * 100:0}% shorter wait.  It grows with every use, and with what dies while it is fresh.", Style.Ui, 13, Style.InkDim, true));

        if (ch.Ability == a.Id) d.AddChild(Style.Label("In hand", Style.UiBold, 16, Style.EmberHi));
        else if (Safe) d.AddChild(Style.Button($"Take {a.Name} in hand", () => G.Gear((j, b) => j.HoldArt(a.Id, b)), true));
        else d.AddChild(Style.Label("Take it in hand somewhere safe: the Waystation, a quiet road.", Style.TextItalic, 14, Style.InkDim, true));
        d.AddChild(Facets(ch, a, true));
        return d;
    }

    Control Facets(CharacterData ch, AbilityDef a, bool known)
    {
        var v = Style.V(8);
        int rank = known ? ArtBook.Rank(ch, a.Id) : 0;
        int slots = Abilities.FacetSlots(rank);
        var chosen = known ? ArtBook.Facets(ch, a.Id) : new();
        string opens = slots == 0 ? "rank II opens the first" : slots == 1 ? "rank IV opens the second" : "";
        v.AddChild(Style.Gap(4));
        v.AddChild(Style.H(8, Style.SubLabel("Facets"), Style.Label(known ? $"{chosen.Count} of {slots} chosen{(opens != "" ? $"  ·  {opens}" : "")}" : "", Style.Ui, 13, Style.InkDim)));
        var grid = new GridContainer { Columns = 2 };
        grid.AddThemeConstantOverride("h_separation", 10);
        grid.AddThemeConstantOverride("v_separation", 10);
        foreach (var f in a.Facets)
        {
            bool on = chosen.Contains(f.Id);
            bool canPick = known && !on && chosen.Count < slots;
            bool canDrop = known && on && Safe;
            var b = Style.Button("", canPick ? () => G.Gear((j, bt) => j.ChooseFacet(a.Id, f.Id, true, bt)) : canDrop ? () => G.Gear((j, bt) => j.ChooseFacet(a.Id, f.Id, false, bt)) : null);
            b.CustomMinimumSize = new Vector2(390, 84);
            if (on) b.AddThemeStyleboxOverride("normal", Style.Box(new Color("#3a2614"), Style.EmberHi, 2, 4));
            b.Disabled = !canPick && !canDrop;
            var words = Style.V(2, Style.Label(f.Name + (on ? "  ✓" : ""), Style.UiBold, 16, on ? Style.EmberHi : canPick ? Style.GoldHi : Style.Ink),
                Style.Label(f.Text, Style.Ui, 13, on || canPick ? Style.Ink : Style.InkDim, true));
            words.Position = new Vector2(12, 8);
            words.Size = new Vector2(366, 70);
            words.MouseFilter = MouseFilterEnum.Ignore;
            b.AddChild(words);
            if (canDrop) b.TooltipText = "Choose again (frees the slot)";
            grid.AddChild(b);
        }
        v.AddChild(grid);
        return v;
    }
}
