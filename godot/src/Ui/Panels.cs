using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>What the level-up draft shows, and what picking does; the fight, for the build beside the cards;
/// a skip, when one is allowed (docs/SKILLS_DESIGN.md, "The offer").</summary>
public sealed record DraftView(int Level, bool Blessing, List<Offer> Offers, int Rerolls, int Banishes, int Queued, string? Tip, HashSet<Tag> Build,
    Action<int> Pick, Action Reroll, Action<int> Banish, string? Great = null, Battle? Battle = null, Action? Skip = null);

/// <summary>A conversation as the panel shows it: who, and what they look like.</summary>
public sealed record DialogueView(string Name, string Title, string Mood, string Speaker, string Text, List<PresentedChoice> Choices,
    bool CanContinue, PersonSpec? Person, Held? Arms, double Scale, string? Glyph, string PlayerName, Action<int> Choose, Action Advance, string? Before = null)
{
    /// <summary>The recording reading this line, if there is one: the words follow it.</summary>
    public VoTake? Voice { get; init; }
}

/// <summary>
/// The ember draft (docs/UI_DESIGN.md, "The draft"). Time stops; the cards
/// rise out of the dark. Each says in one glance what it is (a new skill, a
/// rank, a blessing, an evolution), what it touches (its school's colour,
/// tags lit where the build already has them) and how rare it is (the
/// frame's colour, its name and a count of diamonds). Under the cards, the
/// build as it stands: the skill a card would raise lights up, so a rank is
/// never a guess. 1-4 or a click takes a card, the arrows or the D-pad move
/// along them and Enter or A takes the one lifted; for a moment after the
/// cards appear none can be taken, so a key still held from the fight does
/// not spend a level by accident. The skill system's words ride on each card
/// (docs/SKILLS_DESIGN.md): why the ember dealt it (banked, on your path,
/// your calling's own), what a combat skill becomes, the path it belongs to;
/// a great blessing says what it is for; V (or R3) skips for ember back.
/// </summary>
public partial class DraftPanel : Control
{
    const float CardW = 320, CardH = 500;
    readonly DraftView v;
    int focus;
    bool armed, banishing;
    int? chosen;
    double t;
    readonly List<Button> cards = new();
    readonly Dictionary<string, Control> buildChips = new();
    HBoxContainer foot = null!;
    Label banner = null!;

    public DraftPanel(DraftView v)
    {
        this.v = v;
        Style.Fill(this);
        MouseFilter = MouseFilterEnum.Stop;
    }

    static readonly Dictionary<School, Tag> SchoolTags = new() { [School.Physical] = Tag.Physical, [School.Fire] = Tag.Fire, [School.Frost] = Tag.Frost, [School.Storm] = Tag.Storm, [School.Nature] = Tag.Nature, [School.Arcane] = Tag.Arcane, [School.Holy] = Tag.Holy, [School.Shadow] = Tag.Shadow };

    static School? SchoolOf(Offer o)
    {
        foreach (var tg in o.Tags) foreach (var (s, st) in SchoolTags) if (st == tg) return s;
        if (o.Kind is OfferKind.Weapon or OfferKind.Rank && Weapons.All.TryGetValue(o.Id, out var w)) return w.School;
        return null;
    }

    static string Role(string id) => Boons.GreatRoles.TryGetValue(id, out var r) ? r switch
    {
        Boons.GreatRole.Ward => "ward",
        Boons.GreatRole.Answer => "answer",
        Boons.GreatRole.Tempo => "quickening",
        _ => "power",
    } : "great";

    static string Kicker(Offer o) => o.Kind switch
    {
        OfferKind.Weapon => o.To is int r && r > 1 ? $"New combat skill · rank {r}" : "New combat skill",
        OfferKind.Rank => $"Combat skill · rank {o.From} to {o.To}",
        OfferKind.Evolve => "Evolution",
        OfferKind.Union => "Union",
        OfferKind.Hone => $"Honing · {o.To} of {LevelUp.MaxHone}",
        // A great blessing says what it is for: power, ward, answer, quickening.
        OfferKind.Boon when o.Great => o.From is int g && g > 0 ? $"{Role(o.Id)} · rank {g} to {o.To}" : $"Great blessing · {Role(o.Id)}",
        OfferKind.Boon when Boons.Find(o.Id)?.Kind == BoonKind.Blessing => o.From is int f && f > 0 ? $"Blessing · rank {f} to {o.To}" : "Blessing",
        OfferKind.Boon => o.From is int f2 && f2 > 0 ? $"Passive skill · rank {f2} to {o.To}" : "New passive skill",
        _ => "Respite",
    };

    /// <summary>The held skill this card would let evolve (a passive it needs), if any: the
    /// survivors' "needed to evolve", said on the card and lit in the build.</summary>
    WeaponInst? Evolves(Offer o)
    {
        if (o.Kind != OfferKind.Boon || v.Battle == null) return null;
        foreach (var w in v.Battle.Weapons)
            if (w.Evolution == null && LevelUp.EvolvesWith(w.Id).Any(e => e.Passives.Contains(o.Id))) return w;
        return null;
    }

    /// <summary>New to the build (said on the card: the survivors' "New!").</summary>
    static bool Fresh(Offer o) => o.Kind == OfferKind.Weapon || o.Kind == OfferKind.Boon && (o.From ?? 0) == 0;

    public override void _Ready()
    {
        AddChild(new Backdrop(null, 0.8f));
        var fire = new TextureRect
        {
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(1, 0.42f, 0.12f, 0.26f), new Color(0.8f, 0.2f, 0.05f, 0.1f), new Color(0.6f, 0.1f, 0.02f, 0) }, Offsets = new[] { 0f, 0.5f, 1f } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f), Width = 256, Height = 256,
            },
            Position = new Vector2(160, 160), Size = new Vector2(1600, 900),
        };
        AddChild(fire);
        var col = Style.V(Style.Gap2);
        col.Position = new Vector2(0, 128);
        col.Size = new Vector2(1920, 900);
        AddChild(col);
        string kicker = v.Great ?? (v.Blessing ? $"Ember {v.Level}: a milestone" : "The ember rises");
        string head = v.Great != null ? "A Great Blessing" : v.Blessing ? "A Blessing" : $"Ember {v.Level}";
        col.AddChild(Style.Label(kicker, Style.TextItalic, Style.Lead, v.Great != null || v.Blessing ? new Color("#ffd88a") : new Color("#e8b878"), false, HorizontalAlignment.Center));
        var plaque = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        plaque.AddChild(new Plaque(head, 46, 170, new Color("#ffe6b8")));
        col.AddChild(plaque);
        if (v.Queued > 0) col.AddChild(Style.Label($"{v.Queued} more to choose after this", Style.UiBold, Style.Small, Style.InkDim, false, HorizontalAlignment.Center));
        if (v.Battle != null && LevelUp.BuildPaths(v.Battle) is { Count: > 0 } paths)
            col.AddChild(Style.Label($"Walking {string.Join(" and ", paths.Select(p => p.Name))}", Style.TextItalic, Style.Small, Style.EmberHi, false, HorizontalAlignment.Center));
        if (v.Tip != null)
        {
            var tip = Style.Label(v.Tip, Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center);
            tip.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
            tip.CustomMinimumSize = new Vector2(900, 0);
            col.AddChild(tip);
        }
        col.AddChild(Style.Gap(Style.Gap5));
        var row = Style.H(28);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        row.CustomMinimumSize = new Vector2(0, CardH + 16);
        col.AddChild(row);
        for (int i = 0; i < v.Offers.Count; i++) row.AddChild(Card(v.Offers[i], i));
        col.AddChild(Style.Gap(Style.Gap3));
        banner = Style.Label("", Style.UiHeavy, Style.Lead, new Color("#ff8a6a"), false, HorizontalAlignment.Center);
        col.AddChild(banner);
        if (v.Battle != null) col.AddChild(BuildStrip(v.Battle));
        col.AddChild(Style.Gap(Style.Gap2));
        foot = Style.H(Style.Gap5);
        foot.Alignment = BoxContainer.AlignmentMode.Center;
        col.AddChild(foot);
        Prompts();
        Mark();
    }

    /// <summary>The footer's keys and buttons, as the device in hand has them.</summary>
    public void Prompts()
    {
        if (foot == null) return;
        foreach (var c in foot.GetChildren()) { foot.RemoveChild(c); c.QueueFree(); }
        bool pad = Controls.Instance.UsingPad;
        foot.AddChild(Style.H(6, pad ? Style.PadButton("D-pad") : Style.Key("1-4"), Style.Label("Choose", Style.Ui, Style.Caption, Style.InkDim)));
        foot.AddChild(Style.Hint(Act.Confirm, banishing ? "Banish it" : "Take it"));
        var reroll = Style.Button("", () => { if (armed && v.Rerolls > 0 && chosen == null) v.Reroll(); }, false, true);
        Nav.Id(reroll, "reroll");
        var rr = Style.H(6, Style.Prompt(pad ? Act.Alt : Act.Reroll), Style.Label($"Reroll  {v.Rerolls}", Style.UiBold, Style.Caption, Style.GoldHi));
        Inside(reroll, rr);
        reroll.Disabled = v.Rerolls <= 0;
        foot.AddChild(reroll);
        var banish = Style.Button("", () => { if (v.Banishes > 0) { banishing = !banishing; Mark(); Prompts(); } }, false, true);
        var bb = Style.H(6, Style.Prompt(pad ? Act.Alt2 : Act.Banish), Style.Label(banishing ? "Stop banishing" : $"Banish  {v.Banishes}", Style.UiBold, Style.Caption, banishing ? new Color("#ff8a6a") : Style.GoldHi));
        Inside(banish, bb);
        banish.Disabled = v.Banishes <= 0;
        foot.AddChild(banish);
        if (v.Skip != null)
        {
            var skip = Style.Button("", () => { if (armed && chosen == null) v.Skip(); }, false, true);
            Inside(skip, Style.H(6, Style.Prompt(Act.Skip), Style.Label("Skip", Style.UiBold, Style.Caption, Style.GoldHi)));
            skip.TooltipText = $"Take none: {LevelUp.SkipRefund * 100:0}% of the level's ember comes back, so the next level comes sooner.";
            foot.AddChild(skip);
        }
    }

    /// <summary>A row inside a button, sized to it.</summary>
    static void Inside(Button b, Control row)
    {
        row.MouseFilter = MouseFilterEnum.Ignore;
        row.Position = new Vector2(12, 5);
        b.AddChild(row);
        b.CustomMinimumSize = new Vector2(row.GetCombinedMinimumSize().X + 24, 34);
    }

    /// <summary>The build as it stands: the combat skills (six places) and what blesses them.</summary>
    Control BuildStrip(Battle b)
    {
        var strip = Style.H(Style.Gap2);
        strip.Alignment = BoxContainer.AlignmentMode.Center;
        var slab = Style.Panel(Style.Slab(12), strip);
        slab.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        strip.AddChild(Style.Label("YOUR BUILD", Style.UiHeavy, Style.Caption, Style.Gold));
        foreach (var w in b.Weapons)
        {
            var chip = Chip(w.Art, ItemViews.SchoolColors[w.School], $"{w.Rank}", w.Evolution != null);
            buildChips[w.Id] = chip;
            strip.AddChild(chip);
        }
        for (int i = b.Weapons.Count; i < 6; i++)
        {
            var empty = Chip(null, Style.Line, "", false);
            if (i == b.Weapons.Count) buildChips["~new"] = empty;
            strip.AddChild(empty);
        }
        var held = b.Boons.Where(kv => kv.Value > 0 && Boons.Find(kv.Key) != null).ToList();
        if (held.Count > 0)
        {
            var sep = new ColorRect { Color = Style.Line, CustomMinimumSize = new Vector2(1, 30), MouseFilter = MouseFilterEnum.Ignore };
            strip.AddChild(sep);
        }
        foreach (var (id, rank) in held)
        {
            var bd = Boons.Find(id)!;
            var chip = Chip(bd.Icon, Style.RarityOf((int)bd.Rarity), bd.Max > 1 ? $"{rank}" : "", false, bd.Kind == BoonKind.Blessing);
            buildChips[id] = chip;
            strip.AddChild(chip);
        }
        return slab;
    }

    static Control Chip(string? glyph, Color c, string rank, bool evolved, bool round = false)
    {
        var p = new Panel { CustomMinimumSize = new Vector2(44, 44), MouseFilter = MouseFilterEnum.Ignore };
        p.AddThemeStyleboxOverride("panel", Style.Box(new Color(0.07f, 0.06f, 0.08f, 0.95f), glyph == null ? c with { A = 0.15f } : c with { A = 0.55f }, 1, round ? 22 : 6, 0));
        if (glyph != null)
        {
            var g = Glyphs.Icon(glyph, 28, c);
            g.Position = new Vector2(8, 8);
            g.Size = new Vector2(28, 28);
            p.AddChild(g);
        }
        if (rank != "")
        {
            var r = Style.Label(rank, Style.UiHeavy, Style.Badge, evolved ? Style.EmberHi : Colors.White);
            r.Position = new Vector2(31, 26);
            p.AddChild(r);
        }
        return p;
    }

    Button Card(Offer o, int i)
    {
        bool crown = o.Kind is OfferKind.Evolve or OfferKind.Union;
        var r = crown ? 4 : (int)o.Rarity;
        var rc = Style.RarityOf(r);
        var school = SchoolOf(o);
        var color = crown ? new Color("#ffd88a") : school is School s ? ItemViews.SchoolColors[s] : rc;
        var b = new Button { CustomMinimumSize = new Vector2(CardW, CardH), FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand };
        foreach (var state in new[] { "normal", "hover", "pressed", "disabled", "focus" }) b.AddThemeStyleboxOverride(state, new StyleBoxEmpty());
        var panel = new Panel { MouseFilter = MouseFilterEnum.Ignore };
        Style.Fill(panel);
        b.AddChild(panel);
        panel.SetMeta("rc", rc);
        panel.SetMeta("frame", crown ? "card_evolve" : $"card_{Math.Min(r, 4)}");
        var v2 = Style.V(Style.Gap2);
        v2.Position = new Vector2(22, 20);
        v2.Size = new Vector2(CardW - 44, CardH - 36);
        b.AddChild(v2);
        // What it is, on a ribbon; NEW when it is new to the build.
        var ribbon = Style.H(6);
        ribbon.Alignment = BoxContainer.AlignmentMode.Center;
        ribbon.AddChild(Style.Panel(Style.Box(new Color(0, 0, 0, 0.45f), rc with { A = 0.5f }, 1, 12, 6), Style.Label(Kicker(o).ToUpperInvariant(), Style.UiHeavy, Style.Badge, rc.Lightened(0.25f), false, HorizontalAlignment.Center)));
        if (Fresh(o)) ribbon.AddChild(Style.Panel(Style.Box(Style.Ember with { A = 0.9f }, Style.EmberHi, 1, 12, 6), Style.Label("NEW", Style.UiHeavy, Style.Badge, new Color("#2a1206"), false, HorizontalAlignment.Center, false)));
        v2.AddChild(ribbon);
        // The icon on a disc of its colour.
        var art = new CenterContainer { CustomMinimumSize = new Vector2(CardW - 44, 132), MouseFilter = MouseFilterEnum.Ignore };
        var medal = new Medallion(124, "", o.Icon) { Ring = color, Ink = color.Lightened(0.15f), Core = color.Darkened(0.82f), Name = "Medal" };
        art.AddChild(medal);
        v2.AddChild(art);
        v2.AddChild(Style.Label(o.Title, Style.Display, Style.Title, Style.GoldHi, true, HorizontalAlignment.Center));
        if (o.Kind == OfferKind.Evolve && Weapons.All.TryGetValue(o.Id, out var from))
            v2.AddChild(Style.Label($"{from.Name} becomes {o.Title}", Style.UiBold, Style.Caption, new Color("#ffd88a"), true, HorizontalAlignment.Center));
        if (Evolves(o) is { } ev)
        {
            // It is what a held skill needs to evolve: said plainly, in gold.
            var badge = Style.Panel(Style.Box(new Color("#2a1c08"), Style.Gold, 1, 10, 6),
                Style.H(5, Glyphs.Icon("expand", 14, Style.EmberHi), Style.Label($"Evolves {ev.Def.Name} at rank {Weapons.MaxRank}", Style.UiBold, Style.Caption, Style.EmberHi)));
            badge.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
            v2.AddChild(badge);
        }
        int maxR = o.Kind == OfferKind.Rank ? Weapons.MaxRank : o.Kind == OfferKind.Boon ? Boons.Find(o.Id)?.Max ?? 1 : 0;
        if (maxR > 1)
        {
            // The ranks as a strip: those held dim, the one this gives bright, the rest dark.
            var pips = Style.H(4);
            pips.Alignment = BoxContainer.AlignmentMode.Center;
            for (int k = 0; k < maxR; k++)
                pips.AddChild(new ColorRect { CustomMinimumSize = new Vector2(maxR > 4 ? 16 : 26, 6), MouseFilter = MouseFilterEnum.Ignore, Color = k < (o.From ?? 0) ? color with { A = 0.45f } : k < (o.To ?? 0) ? color : new Color("#221d28") });
            v2.AddChild(pips);
        }
        var text = o.Kind == OfferKind.Evolve && o.Text.Contains(" becomes ") && o.Text.IndexOf(". ") is int dot && dot > 0 ? o.Text[(dot + 2)..] : o.Text;
        var body = Style.Label(text, Style.Text, Style.Body, Style.Ink, true, HorizontalAlignment.Center);
        body.SizeFlagsVertical = SizeFlags.ExpandFill;
        v2.AddChild(body);
        // Why the ember dealt it: banked from the day, on your path, your calling's own, a duo; a trap said plainly.
        foreach (var why in o.Why.Where(w => o.Path == null || !w.StartsWith("On your path")).Take(2))
            v2.AddChild(Style.Label(why, Style.UiBold, Style.Caption, why.StartsWith("Little") ? Style.InkDim : Style.EmberHi, true, HorizontalAlignment.Center));
        // What a combat skill becomes, and with what.
        if (o.Recipe is { Length: > 0 } recipe)
            v2.AddChild(Style.Label(recipe, Style.TextItalic, Style.Badge, Style.InkDim, true, HorizontalAlignment.Center));
        var tags = Style.H(10);
        tags.Alignment = BoxContainer.AlignmentMode.Center;
        bool fits = false;
        foreach (var tg in o.Tags.Where(x => school == null || !(SchoolTags.TryGetValue(school.Value, out var st) && x == st)).Take(4))
        {
            bool fit = o.Kind is not (OfferKind.Rank or OfferKind.Evolve) && v.Build.Contains(tg);
            fits |= fit;
            tags.AddChild(Style.Label(tg.ToString().ToLowerInvariant(), Style.UiBold, Style.Caption, fit ? Style.EmberHi : Style.InkFaint));
        }
        v2.AddChild(tags);
        // The path it belongs to, or (if none) that it fits what the build already does.
        if (o.Path is { } pid && Content.Paths.Find(pid) is { } path)
            v2.AddChild(Style.Label(path.Name, Style.DisplayLight, Style.Small, Style.Gold, false, HorizontalAlignment.Center));
        else if (fits)
        {
            var fl = Style.H(4, Glyphs.Icon("flame", 15, Style.EmberHi), Style.Label("Fits your build", Style.UiBold, Style.Caption, Style.EmberHi));
            fl.Alignment = BoxContainer.AlignmentMode.Center;
            v2.AddChild(fl);
        }
        // Its rarity, in words and diamonds as well as colour; its key.
        var foot = Style.H(Style.Gap2, Style.Label(crown ? "Legendary" : o.Rarity.ToString(), Style.UiBold, Style.Caption, rc), Style.Gems(r, 6));
        foot.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill, MouseFilter = MouseFilterEnum.Ignore });
        var key = new Control { CustomMinimumSize = new Vector2(30, 26), MouseFilter = MouseFilterEnum.Ignore, Name = "Key" };
        foot.AddChild(key);
        v2.AddChild(foot);
        var ban = Style.Label("BANISH", Style.Display, 30, new Color("#ff8a6a"), false, HorizontalAlignment.Center);
        ban.Position = new Vector2(0, 186); ban.Size = new Vector2(CardW, 40);
        ban.Visible = false;
        ban.Name = "Ban";
        b.AddChild(ban);
        b.MouseEntered += () => { if (focus != i) { focus = i; Mark(); Sound.Sfx.Hover(); } };
        b.Pressed += () => Take(i);
        cards.Add(b);
        return b;
    }

    /// <summary>The focused card lifted, the banish mark shown, a chosen card glowing; its skill lit in the build.</summary>
    void Mark()
    {
        bool pad = Controls.Instance.UsingPad;
        for (int i = 0; i < cards.Count; i++)
        {
            var b = cards[i];
            var panel = b.GetChild<Panel>(0);
            var rc = (Color)panel.GetMeta("rc");
            bool on = i == focus, ch = chosen == i;
            var edge = banishing && on ? new Color("#ff6a4a") : ch ? Style.GoldHi : rc;
            // A crested card: its rarity in the crest and the corners, a glow when lifted.
            var s = OrnateBox.Make(OrnateBox.Kind.Card, 0, edge);
            s.Crest = 120;
            s.Glow = on ? 1.4f : 0;
            s.Top = new Color("#211c26").Lerp(rc, 0.05f);
            panel.AddThemeStyleboxOverride("panel", UiArt.Has((string)panel.GetMeta("frame")) ? UiArt.Frame((string)panel.GetMeta("frame"), s) : s);
            if (b.FindChild("Medal", true, false) is Medallion m) { m.Lit = on; m.QueueRedraw(); }
            panel.SelfModulate = banishing && on ? new Color(1.15f, 0.8f, 0.75f) : Colors.White;
            b.GetNode<Label>("Ban").Visible = banishing && on;
            b.Position = b.Position with { Y = on && chosen == null ? -12 : 0 };
            if (chosen != null) b.Modulate = ch ? Colors.White : new Color(1, 1, 1, 0);
            // The card's key: its number on a keyboard, A on the lifted one with a pad.
            if (b.FindChild("Key", true, false) is Control key)
            {
                foreach (var c in key.GetChildren()) c.QueueFree();
                if (!pad) key.AddChild(Style.Key($"{i + 1}"));
                else if (on) key.AddChild(Style.PadButton("A"));
            }
        }
        banner.Text = banishing ? "Banish which? It will not be offered again this night." : "";
        // The skill the lifted card would raise, or the place a new one would take, lit in the build.
        foreach (var (_, chip) in buildChips) chip.Modulate = Colors.White with { A = 0.6f };
        if (focus >= 0 && focus < v.Offers.Count)
        {
            var o = v.Offers[focus];
            string? id = o.Kind is OfferKind.Rank or OfferKind.Evolve ? o.Id : o.Kind == OfferKind.Weapon ? "~new" : o.Kind == OfferKind.Boon && (o.From ?? 0) > 0 ? o.Id : null;
            if (id != null && buildChips.TryGetValue(id, out var lit)) lit.Modulate = new Color(1.5f, 1.35f, 1.1f);
            // A passive that would evolve a held skill lights that skill too.
            if (Evolves(o) is { } ev && buildChips.TryGetValue(ev.Id, out var evo)) evo.Modulate = new Color(1.6f, 1.3f, 0.9f);
        }
    }

    void Take(int i)
    {
        if (!armed || chosen != null || i < 0 || i >= v.Offers.Count) return;
        if (banishing)
        {
            if (v.Banishes > 0) v.Banish(i);
            banishing = false;
            Mark();
            return;
        }
        chosen = i;
        Mark();
        Sound.Sfx.Pick();
        GetTree().CreateTimer(0.34, true, false, true).Timeout += () => v.Pick(i);
    }

    public bool Key(Act a)
    {
        switch (a)
        {
            case Act.Pick1: Take(0); break;
            case Act.Pick2: Take(1); break;
            case Act.Pick3: Take(2); break;
            case Act.Pick4: Take(3); break;
            case Act.Left: focus = (focus + v.Offers.Count - 1) % v.Offers.Count; Mark(); Sound.Sfx.Hover(); break;
            case Act.Right: focus = (focus + 1) % v.Offers.Count; Mark(); Sound.Sfx.Hover(); break;
            case Act.Confirm or Act.Dash: Take(focus); break;
            case Act.Reroll or Act.Alt: if (armed && v.Rerolls > 0 && chosen == null) v.Reroll(); else Sound.Sfx.Deny(); break;
            case Act.Banish or Act.Alt2: if (v.Banishes > 0) { banishing = !banishing; Mark(); Prompts(); } else Sound.Sfx.Deny(); break;
            case Act.Cancel: if (banishing) { banishing = false; Mark(); Prompts(); } break;
            case Act.Skip: if (armed && chosen == null && v.Skip != null) v.Skip(); else Sound.Sfx.Deny(); break;
        }
        return true;
    }

    public override void _Process(double delta)
    {
        t += delta;
        if (!armed && t > 0.38) armed = true;
        // The cards rise in, one after another; the chosen one swells as the rest fall away.
        for (int i = 0; i < cards.Count; i++)
        {
            float k = Mathf.Clamp((float)((t - 0.06 - i * 0.08) / 0.5), 0, 1);
            float e = 1 - (1 - k) * (1 - k) * (1 - k);
            if (chosen == null) cards[i].Modulate = Colors.White with { A = e };
            cards[i].GetChild<Control>(1).Position = new Vector2(22, 20 + (1 - e) * 60);
            cards[i].PivotOffset = new Vector2(CardW / 2, CardH / 2);
            float target = chosen == i ? 1.06f : 1;
            cards[i].Scale = cards[i].Scale.Lerp(new Vector2(target, target), 1 - Mathf.Exp(-14 * (float)delta));
        }
    }
}

/// <summary>
/// A conversation (the web game's overlays/Dialogue.tsx): the person on
/// the left as they look to you, what they say arriving at the pace of
/// speech (a key or a click hurries it), what you can say back. Choices a
/// background or kit opens carry a badge; ones you cannot take are shown
/// anyway, greyed, with the reason, so the player learns there was another
/// way. A line is chosen with its number, a click, or by moving to it
/// (arrows, D-pad) and pressing Enter or A.
/// </summary>
public partial class TalkPanel : Control
{
    readonly DialogueView d;
    Label text = null!;
    int shown;
    double tick;
    VBoxContainer choices = null!;
    readonly List<(PanelContainer Row, Control Key, int Index, bool Enabled)> lines = new();
    int focus = -1;
    Button? more;

    static readonly Dictionary<string, Color> BadgeTone = new()
    {
        ["Beastlore"] = new("#8ae05a"), ["Hunter"] = new("#8ae05a"), ["Arcana"] = new("#cf94ff"), ["Scholar"] = new("#cf94ff"),
        ["Underworld"] = new("#ff8a6a"), ["Outcast"] = new("#ff8a6a"), ["Faith"] = new("#ffd36a"), ["Devout"] = new("#ffd36a"),
    };

    static readonly StyleBoxFlat Rest = Pad(new Color(0, 0, 0, 0)), Lit = Pad(new Color(1, 0.8f, 0.5f, 0.09f));
    static StyleBoxFlat Pad(Color c)
    {
        var sb = Style.Box(c, new Color(0, 0, 0, 0), 0, 4, 0);
        sb.ContentMarginLeft = sb.ContentMarginRight = 8; sb.ContentMarginTop = sb.ContentMarginBottom = 6;
        return sb;
    }

    public TalkPanel(DialogueView d)
    {
        this.d = d;
        Style.Fill(this);
        MouseFilter = MouseFilterEnum.Stop;
        GuiInput += e => { if (e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left } && !Full) Finish(); };
    }

    bool Full => shown >= d.Text.Length;

    public override void _Ready()
    {
        var shade = new TextureRect
        {
            Texture = new GradientTexture2D { Gradient = new Gradient { Offsets = new[] { 0f, 0.5f, 1f }, Colors = new[] { new Color(0, 0, 0, 0), new Color(0.02f, 0.015f, 0.03f, 0.55f), new Color(0.02f, 0.015f, 0.03f, 0.9f) } }, Width = 4, Height = 256, FillTo = new Vector2(0, 1) },
            StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
        };
        Style.Fill(shade);
        AddChild(shade);
        // The words on a plate across the foot of the screen; the person stands in front of its
        // left end, large, as they would across a table (docs/UI_DESIGN.md, "Conversation").
        var box = Style.Panel(Style.Plate(22));
        box.Position = new Vector2(420, 1080 - 36 - 404);
        box.Size = new Vector2(1460, 404);
        AddChild(box);
        var inset = new MarginContainer { MouseFilter = MouseFilterEnum.Ignore };
        inset.AddThemeConstantOverride("margin_left", 190);
        inset.AddThemeConstantOverride("margin_top", 26);
        box.AddChild(inset);
        var glow = new TextureRect
        {
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(1, 0.5f, 0.2f, 0.2f), new Color(1, 0.5f, 0.2f, 0) }, Offsets = new[] { 0f, 1f } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.55f), FillTo = new Vector2(1f, 0.55f), Width = 128, Height = 128,
            },
            Position = new Vector2(-40, 300), Size = new Vector2(720, 780),
        };
        AddChild(glow);
        if (d.Person != null)
        {
            var fig = new Portrait(new Vector2I(560, 760), Portrait.Framing.Half).Of(d.Person, d.Arms, d.Scale);
            fig.Position = new Vector2(30, 1080 - 760);
            AddChild(fig);
        }
        else
        {
            var m = new Medallion(240, "", d.Glyph ?? "talk") { Ink = new Color("#e8c890"), Lit = true };
            m.Position = new Vector2(190, 1080 - 36 - 404 - 40);
            AddChild(m);
        }
        // Their name on a banner over the plate's edge, what they are and how they feel about you beside it.
        var banner = Style.Panel(OrnateBox.Make(OrnateBox.Kind.Banner, 18), Style.Label(d.Name.ToUpperInvariant(), Style.Display, 26, Style.GoldHi));
        banner.Position = new Vector2(610, 1080 - 36 - 404 - 26);
        AddChild(banner);
        // What is said, and what can be said back.
        var main = Style.V(10);
        main.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        var about = Style.H(Style.Gap3);
        if (d.Title != "") about.AddChild(Style.Label(d.Title, Style.TextItalic, Style.Small, Style.InkDim));
        if (d.Mood != "") about.AddChild(Style.H(4, Glyphs.Icon("eye", 14, Style.Gold), Style.Label(d.Mood, Style.Ui, Style.Small, Style.Gold)));
        if (about.GetChildCount() > 0) main.AddChild(about);
        // What was said just before, quietly, so the thread is never lost to the pace of speech.
        if (d.Before != null) main.AddChild(Style.Label(d.Before, Style.TextItalic, Style.Small, Style.InkFaint, true));
        if (d.Speaker == "player") main.AddChild(Style.Label(d.PlayerName.ToUpperInvariant(), Style.Display, Style.Caption, new Color("#9ab8d8")));
        text = Style.Label("", d.Speaker == "narrator" ? Style.TextItalic : Style.Text, 23, d.Speaker == "player" ? new Color("#c8d8e8") : d.Speaker == "narrator" ? Style.InkDim : Style.Ink, true);
        text.VisibleCharactersBehavior = TextServer.VisibleCharactersBehavior.CharsAfterShaping;
        text.Text = d.Text;
        text.VisibleCharacters = 0;
        main.AddChild(text);
        main.AddChild(Style.Gap(4));
        choices = Style.V(2);
        choices.Modulate = new Color(1, 1, 1, 0.35f);
        main.AddChild(choices);
        for (int i = 0; i < d.Choices.Count; i++)
        {
            var c = d.Choices[i];
            var key = new Control { CustomMinimumSize = new Vector2(28, 24), MouseFilter = MouseFilterEnum.Ignore };
            key.SizeFlagsVertical = SizeFlags.ShrinkBegin;
            var line = Style.H(8, key);
            if (c.Badge != null)
            {
                var badge = Style.Panel(Style.Box(new Color(0, 0, 0, 0.5f), BadgeTone.GetValueOrDefault(c.Badge, Style.Gold), 1, 8, 5), Style.Label(c.Badge.ToUpperInvariant(), Style.UiHeavy, Style.Badge, BadgeTone.GetValueOrDefault(c.Badge, Style.Gold)));
                badge.SizeFlagsVertical = SizeFlags.ShrinkBegin;
                line.AddChild(badge);
            }
            var words = Style.Label(c.Text, Style.UiBold, Style.Body, !c.Enabled ? Style.InkDim with { A = 0.6f } : c.Ends ? Style.InkDim : c.Action != null ? Style.EmberHi : Style.GoldHi, true);
            words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            line.AddChild(words);
            if (c.Locked != null)
            {
                var why = Style.H(4, Glyphs.Icon("lock", 14, Style.InkDim), Style.Label(c.Locked, Style.TextItalic, Style.Caption, Style.InkDim));
                why.SizeFlagsVertical = SizeFlags.ShrinkCenter;
                line.AddChild(why);
            }
            // A row that grows with its words; lit under the pointer or the focus.
            var b = Style.Panel(Rest, line);
            b.MouseFilter = MouseFilterEnum.Stop;
            b.MouseDefaultCursorShape = c.Enabled ? CursorShape.PointingHand : CursorShape.Arrow;
            int at = lines.Count;
            if (c.Enabled) b.MouseEntered += () => { if (focus != at) { focus = at; Mark(); Sound.Sfx.Hover(); } };
            int index = c.Index;
            bool enabled = c.Enabled;
            b.GuiInput += e =>
            {
                if (e is not InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) return;
                if (!Full) { Finish(); return; }
                if (enabled) d.Choose(index); else Sound.Sfx.Deny();
            };
            lines.Add((b, key, index, enabled));
            choices.AddChild(b);
        }
        if (d.CanContinue)
        {
            more = Style.Button("", () => { if (!Full) Finish(); else d.Advance(); }, false, true);
            more.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
            choices.AddChild(more);
        }
        focus = lines.FindIndex(l => l.Enabled);
        Prompts();
        inset.AddChild(main);
    }

    /// <summary>The keys beside the lines: numbers on a keyboard, A on the focused line with a pad.</summary>
    public void Prompts()
    {
        if (choices == null) return;
        if (more != null)
        {
            foreach (var c in more.GetChildren()) c.QueueFree();
            var r = Style.H(8, Style.Prompt(Act.Confirm), Style.Label("Continue", Style.UiBold, Style.Small, Style.GoldHi));
            r.MouseFilter = MouseFilterEnum.Ignore;
            r.Position = new Vector2(12, 5);
            more.AddChild(r);
            more.CustomMinimumSize = new Vector2(r.GetCombinedMinimumSize().X + 24, 36);
        }
        Mark();
    }

    void Mark()
    {
        bool pad = Controls.Instance.UsingPad;
        for (int i = 0; i < lines.Count; i++)
        {
            var (row, key, _, _) = lines[i];
            row.AddThemeStyleboxOverride("panel", i == focus ? Lit : Rest);
            foreach (var c in key.GetChildren()) c.QueueFree();
            if (!pad) key.AddChild(Style.Key($"{i + 1}"));
            else if (i == focus) key.AddChild(Style.PadButton("A"));
        }
    }

    void Finish()
    {
        shown = d.Text.Length;
        text.VisibleCharacters = -1;
        choices.Modulate = Colors.White;
    }

    public override void _Process(double delta)
    {
        if (Full) return;
        // A line read aloud shows its words as they are said; the rest arrive
        // at the pace of reading.
        if (d.Voice != null && Sound.VoiceOver.Instance?.Reveal(d.Voice) is double f)
            shown = Math.Max(shown, (int)Math.Round(f * d.Text.Length));
        else
        {
            tick += delta;
            while (tick >= 0.022 && !Full) { tick -= 0.022; shown = Math.Min(d.Text.Length, shown + 2); }
        }
        text.VisibleCharacters = shown;
        if (Full) Finish();
    }

    void MoveFocus(int dir)
    {
        if (lines.Count == 0) return;
        for (int k = 1; k <= lines.Count; k++)
        {
            int i = ((focus < 0 ? 0 : focus) + dir * k + lines.Count * 4) % lines.Count;
            if (!lines[i].Enabled) continue;
            focus = i;
            Mark();
            Sound.Sfx.Hover();
            return;
        }
    }

    public bool Key(Act a)
    {
        if (a is Act.Up or Act.Down) { MoveFocus(a == Act.Up ? -1 : 1); return true; }
        int n = a switch { Act.Pick1 => 0, Act.Pick2 => 1, Act.Pick3 => 2, Act.Pick4 => 3, _ => -1 };
        if (n < 0 && a is not (Act.Confirm or Act.Interact or Act.Dash))
        {
            if (a is Act.Cancel or Act.Pause)
            {
                // Escape (or B) takes the way out, where there is one.
                var leave = d.Choices.FirstOrDefault(c => c.Ends && c.Enabled);
                if (leave != null) d.Choose(leave.Index);
            }
            return true;
        }
        if (!Full) { Finish(); return true; }
        if (n >= 0) { if (n < d.Choices.Count && d.Choices[n].Enabled) d.Choose(d.Choices[n].Index); else Sound.Sfx.Deny(); return true; }
        if (d.CanContinue) d.Advance();
        // Enter or A says the lit line; the use key (pressed to start talking) only when there is one thing to say.
        else if (a == Act.Confirm && focus >= 0 && focus < lines.Count && lines[focus].Enabled) d.Choose(lines[focus].Index);
        else if (d.Choices.Count(c => c.Enabled) == 1) d.Choose(d.Choices.First(c => c.Enabled).Index);
        return true;
    }
}
