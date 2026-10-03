using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>What the level-up draft shows, and what picking does: the cards,
/// the tools (reroll, banish, skip), the paths the build walks and its arsenal
/// with what each skill needs to evolve or unite.</summary>
public sealed record DraftView(int Level, bool Blessing, List<Offer> Offers, int Rerolls, int Banishes, int Queued, string? Tip, HashSet<Tag> Build,
    Action<int> Pick, Action Reroll, Action<int> Banish, string? Great = null, Action? Skip = null,
    List<LevelUp.ArsenalLine>? Arsenal = null, List<string>? Paths = null);

/// <summary>A conversation as the panel shows it: who, and what they look like.</summary>
public sealed record DialogueView(string Name, string Title, string Mood, string Speaker, string Text, List<PresentedChoice> Choices,
    bool CanContinue, PersonSpec? Person, Held? Arms, double Scale, string? Glyph, string PlayerName, Action<int> Choose, Action Advance);

/// <summary>
/// The ember draft (the web game's overlays/LevelUp.tsx). Time stops; the
/// cards rise out of the dark. Each says in one glance what it is (a new
/// skill, a rank, a blessing), what it touches (its school's colour, tags
/// lit where the build already has them), how rare it is (the frame), the
/// path it belongs to and why the ember dealt it (attuned, evolves
/// something, on your path), and for a combat skill what it becomes. Under
/// the cards, the arsenal: each skill carried, its rank, and what it still
/// needs. Keys 1-4 take a card, the arrows and Enter too, X rerolls, B then
/// a number banishes, V skips; for a moment after the cards appear they
/// cannot be taken, so a key still held from the fight does not spend a
/// level by accident.
/// </summary>
public partial class DraftPanel : Control
{
    readonly DraftView v;
    int focus;
    bool armed, banishing;
    int? chosen;
    double t;
    readonly List<Button> cards = new();

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

    static string Kicker(Offer o) => o.Kind switch
    {
        OfferKind.Weapon => o.To is int r && r > 1 ? $"New combat skill · rank {r}" : "New combat skill",
        OfferKind.Rank => $"Combat skill · rank {o.From} to {o.To}",
        OfferKind.Evolve => "Evolution",
        OfferKind.Union => "Union",
        OfferKind.Hone => $"Honing · {o.To} of {LevelUp.MaxHone}",
        OfferKind.Boon when o.Great => o.From is int g && g > 0 ? $"Great blessing · rank {g} to {o.To}" : "Great blessing",
        OfferKind.Boon when Boons.Find(o.Id)?.Kind == BoonKind.Blessing => o.From is int f && f > 0 ? $"Blessing · rank {f} to {o.To}" : "Blessing",
        OfferKind.Boon => o.From is int f2 && f2 > 0 ? $"Passive skill · rank {f2} to {o.To}" : "New passive skill",
        _ => "Respite",
    };

    public override void _Ready()
    {
        AddChild(Style.Scrim(null, 0.74f));
        var col = Style.V(8);
        col.Position = new Vector2(0, 70);
        col.Size = new Vector2(1920, 960);
        AddChild(col);
        string kicker = v.Great ?? (v.Blessing ? $"Ember {v.Level}: a milestone" : "The ember rises");
        string head = v.Great != null ? "A Great Blessing" : v.Blessing ? "A Blessing" : $"Ember {v.Level}";
        col.AddChild(Style.Label(kicker, Style.TextItalic, 17, v.Great != null || v.Blessing ? new Color("#ffd88a") : new Color("#e8b878"), false, HorizontalAlignment.Center));
        col.AddChild(Style.Label(head.ToUpperInvariant(), Style.Display, 48, new Color("#ffe6b8"), false, HorizontalAlignment.Center));
        if (v.Queued > 0) col.AddChild(Style.Label($"{v.Queued} more to choose", Style.UiBold, 16, Style.InkDim, false, HorizontalAlignment.Center));
        if (v.Paths is { Count: > 0 } paths)
            col.AddChild(Style.Label($"Walking {string.Join(" and ", paths)}", Style.TextItalic, 17, Style.EmberHi, false, HorizontalAlignment.Center));
        if (v.Tip != null) col.AddChild(Style.Label(v.Tip, Style.TextItalic, 18, Style.Ink, true, HorizontalAlignment.Center));
        col.AddChild(Style.Gap(14));
        var row = Style.H(26);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        col.AddChild(row);
        for (int i = 0; i < v.Offers.Count; i++) row.AddChild(Card(v.Offers[i], i));
        col.AddChild(Style.Gap(18));
        var foot = Style.H(12);
        foot.Alignment = BoxContainer.AlignmentMode.Center;
        var reroll = Style.Button($"{Controls.Instance.KeyLabel(Act.Reroll)}   Reroll  {v.Rerolls}", () => { if (armed && v.Rerolls > 0 && chosen == null) v.Reroll(); }, false, true);
        reroll.Disabled = v.Rerolls <= 0;
        reroll.TooltipText = "Look again: what was just shown is far less likely to come back. A milestone hands one back.";
        var banish = Style.Button($"{Controls.Instance.KeyLabel(Act.Banish)}   Banish  {v.Banishes}", () => { banishing = !banishing; Mark(); }, false, true);
        banish.Disabled = v.Banishes <= 0;
        banish.TooltipText = "Then a card: it never comes again in this arena.";
        foot.AddChild(reroll);
        foot.AddChild(banish);
        if (v.Skip != null)
        {
            var skip = Style.Button($"{Controls.Instance.KeyLabel(Act.Skip)}   Skip", () => { if (armed && chosen == null) v.Skip(); }, false, true);
            skip.TooltipText = $"Take none: {LevelUp.SkipRefund * 100:0}% of the level's ember comes back, so the next level comes sooner.";
            foot.AddChild(skip);
        }
        col.AddChild(foot);
        if (v.Arsenal is { Count: > 0 } arsenal) col.AddChild(Arsenal(arsenal));
        Mark();
    }

    /// <summary>The arsenal under the cards: each skill carried, its rank, and
    /// what it still needs (the passive that evolves it, the skill it joins).</summary>
    static Control Arsenal(List<LevelUp.ArsenalLine> lines)
    {
        var row = Style.H(14);
        row.Alignment = BoxContainer.AlignmentMode.Center;
        foreach (var l in lines)
        {
            var col = ItemViews.SchoolColors[l.School];
            var pips = Style.H(2);
            for (int k = 0; k < Weapons.MaxRank; k++)
                pips.AddChild(new ColorRect { CustomMinimumSize = new Vector2(7, 4), MouseFilter = MouseFilterEnum.Ignore, Color = k < l.Rank ? col : new Color("#2a2631") });
            var words = Style.V(1,
                Style.Label(l.Name, Style.UiBold, 14, l.Evolved ? Style.GoldHi : Style.Ink),
                pips,
                Style.Label(l.Note, Style.Ui, 12, l.Ready ? Style.EmberHi : Style.InkDim, true));
            words.CustomMinimumSize = new Vector2(196, 0);
            var item = Style.H(8, Glyphs.Icon(l.Icon, 30, l.Evolved ? Style.GoldHi : col), words);
            var plate = Style.Panel(Style.Box(new Color(0.05f, 0.045f, 0.06f, 0.85f), l.Ready ? Style.EmberHi with { A = 0.7f } : Style.Line, 1, 6, 8), item);
            plate.MouseFilter = MouseFilterEnum.Ignore;
            row.AddChild(plate);
        }
        return row;
    }

    Button Card(Offer o, int i)
    {
        bool crown = o.Kind is OfferKind.Evolve or OfferKind.Union;
        var r = crown ? 4 : (int)o.Rarity;
        var rc = Style.RarityOf(r);
        var school = SchoolOf(o);
        var color = crown ? new Color("#ffd88a") : school is School s ? ItemViews.SchoolColors[s] : rc;
        var b = new Button { CustomMinimumSize = new Vector2(320, 560), FocusMode = FocusModeEnum.None, MouseDefaultCursorShape = CursorShape.PointingHand };
        foreach (var state in new[] { "normal", "hover", "pressed", "disabled" }) b.AddThemeStyleboxOverride(state, new StyleBoxEmpty());
        var panel = new Panel { MouseFilter = MouseFilterEnum.Ignore };
        Style.Fill(panel);
        b.AddChild(panel);
        panel.SetMeta("rc", rc);
        var v2 = Style.V(6);
        v2.Position = new Vector2(20, 18);
        v2.Size = new Vector2(280, 524);
        b.AddChild(v2);
        var kick = Style.Panel(Style.Box(new Color(0, 0, 0, 0.45f), rc with { A = 0.4f }, 1, 12, 5), Style.Label(Kicker(o).ToUpperInvariant(), Style.UiHeavy, 12, rc.Lightened(0.2f), false, HorizontalAlignment.Center));
        kick.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        v2.AddChild(kick);
        var art = new CenterContainer { CustomMinimumSize = new Vector2(280, 108), MouseFilter = MouseFilterEnum.Ignore };
        art.AddChild(Glyphs.Icon(o.Icon, 72, color));
        v2.AddChild(art);
        v2.AddChild(Style.Label(o.Title, Style.Display, 23, Style.GoldHi, true, HorizontalAlignment.Center));
        if (o.Kind == OfferKind.Evolve && Weapons.All.TryGetValue(o.Id, out var from))
            v2.AddChild(Style.Label($"{from.Name}  to  {o.Title}", Style.UiBold, 14, new Color("#ffd88a"), true, HorizontalAlignment.Center));
        int maxR = o.Kind == OfferKind.Rank ? Weapons.MaxRank : o.Kind == OfferKind.Boon ? Boons.Find(o.Id)?.Max ?? 1 : 0;
        if (maxR > 1)
        {
            var pips = Style.H(4);
            pips.Alignment = BoxContainer.AlignmentMode.Center;
            for (int k = 0; k < maxR; k++)
                pips.AddChild(new ColorRect { CustomMinimumSize = new Vector2(8, 8), MouseFilter = MouseFilterEnum.Ignore, Color = k < (o.From ?? 0) ? color with { A = 0.55f } : k < (o.To ?? 0) ? color : new Color("#15121a") });
            v2.AddChild(pips);
        }
        var text = o.Kind == OfferKind.Evolve && o.Text.Contains(" becomes ") && o.Text.IndexOf(". ") is int dot && dot > 0 ? o.Text[(dot + 2)..] : o.Text;
        var body = Style.Label(text, Style.Text, 17, Style.Ink, true, HorizontalAlignment.Center);
        body.SizeFlagsVertical = SizeFlags.ExpandFill;
        v2.AddChild(body);
        // Why the ember dealt it: attuned, on your path, evolves something; a surge.
        foreach (var why in o.Why.Where(w => o.Path == null || !w.StartsWith("On your path")).Take(2))
            v2.AddChild(Style.Label(why, Style.UiBold, 14, why.StartsWith("Little") ? Style.InkDim : Style.EmberHi, true, HorizontalAlignment.Center));
        // What a combat skill becomes.
        if (o.Recipe is { Length: > 0 } recipe)
            v2.AddChild(Style.Label(recipe, Style.TextItalic, 13, Style.InkDim, true, HorizontalAlignment.Center));
        var tags = Style.H(5);
        tags.Alignment = BoxContainer.AlignmentMode.Center;
        bool fits = false;
        foreach (var tg in o.Tags.Where(x => school == null || !(SchoolTags.TryGetValue(school.Value, out var st) && x == st)).Take(4))
        {
            bool fit = o.Kind is not (OfferKind.Rank or OfferKind.Evolve) && v.Build.Contains(tg);
            fits |= fit;
            tags.AddChild(Style.Label(tg.ToString().ToLowerInvariant(), Style.UiBold, 13, fit ? Style.EmberHi : Style.InkFaint));
        }
        v2.AddChild(tags);
        if (o.Path is { } pid && Content.Paths.Find(pid) is { } path) v2.AddChild(Style.Label(path.Name, Style.DisplayLight, 14, Style.Gold, false, HorizontalAlignment.Center));
        else if (fits) v2.AddChild(Style.Label("Fits your build", Style.UiBold, 13, Style.EmberHi, false, HorizontalAlignment.Center));
        var foot = Style.H(8, Style.Label(crown ? "Legendary" : o.Rarity.ToString(), Style.UiBold, 14, rc));
        foot.AddChild(new Control { SizeFlagsHorizontal = SizeFlags.ExpandFill });
        foot.AddChild(Style.Key($"{i + 1}"));
        v2.AddChild(foot);
        var ban = Style.Label("BANISH", Style.Display, 26, new Color("#ff8a6a"), false, HorizontalAlignment.Center);
        ban.Position = new Vector2(0, 240); ban.Size = new Vector2(320, 40);
        ban.Visible = false;
        ban.Name = "Ban";
        b.AddChild(ban);
        b.MouseEntered += () => { focus = i; Mark(); };
        b.Pressed += () => Take(i);
        cards.Add(b);
        return b;
    }

    /// <summary>The focused card lifted, the banish mark shown, a chosen card glowing.</summary>
    void Mark()
    {
        for (int i = 0; i < cards.Count; i++)
        {
            var b = cards[i];
            var panel = b.GetChild<Panel>(0);
            var rc = (Color)panel.GetMeta("rc");
            bool on = i == focus, ch = chosen == i;
            var s = Style.Box(new Color(0.09f, 0.075f, 0.1f, 0.98f).Lerp(rc, 0.04f), ch ? Style.GoldHi : rc with { A = on ? 0.95f : 0.6f }, ch ? 3 : on ? 2 : 1, 10, 0);
            s.ShadowColor = on ? rc with { A = 0.35f } : new Color(0, 0, 0, 0.7f);
            s.ShadowSize = on ? 26 : 18;
            panel.AddThemeStyleboxOverride("panel", s);
            b.GetNode<Label>("Ban").Visible = banishing;
            b.Position = b.Position with { Y = on && chosen == null ? -10 : 0 };
            b.Modulate = chosen != null && !ch ? new Color(1, 1, 1, 0) : Colors.White;
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
        GetTree().CreateTimer(0.3, true, false, true).Timeout += () => v.Pick(i);
    }

    public bool Key(Act a)
    {
        switch (a)
        {
            case Act.Pick1: Take(0); break;
            case Act.Pick2: Take(1); break;
            case Act.Pick3: Take(2); break;
            case Act.Pick4: Take(3); break;
            case Act.Left: focus = (focus + v.Offers.Count - 1) % v.Offers.Count; Mark(); break;
            case Act.Right: focus = (focus + 1) % v.Offers.Count; Mark(); break;
            case Act.Confirm or Act.Dash: Take(focus); break;
            case Act.Reroll: if (armed && v.Rerolls > 0 && chosen == null) v.Reroll(); break;
            case Act.Banish: if (v.Banishes > 0) { banishing = !banishing; Mark(); } break;
            case Act.Skip: if (armed && chosen == null) v.Skip?.Invoke(); break;
            case Act.Cancel: banishing = false; Mark(); break;
        }
        return true;
    }

    public override void _Process(double delta)
    {
        t += delta;
        if (!armed && t > 0.38) armed = true;
        // The cards rise in, one after another.
        for (int i = 0; i < cards.Count; i++)
        {
            float k = Mathf.Clamp((float)((t - 0.06 - i * 0.08) / 0.5), 0, 1);
            float e = 1 - (1 - k) * (1 - k) * (1 - k);
            if (chosen == null) cards[i].Modulate = Colors.White with { A = e };
            cards[i].GetChild<Control>(1).Position = new Vector2(20, 20 + (1 - e) * 60);
        }
    }
}

/// <summary>
/// A conversation (the web game's overlays/Dialogue.tsx): the person on
/// the left as they look to you, what they say arriving at the pace of
/// speech (a key or a click hurries it), what you can say back. Choices a
/// background or kit opens carry a badge; ones you cannot take are shown
/// anyway, greyed, with the reason, so the player learns there was another
/// way.
/// </summary>
public partial class TalkPanel : Control
{
    readonly DialogueView d;
    Label text = null!;
    int shown;
    double tick;
    VBoxContainer choices = null!;

    static readonly Dictionary<string, Color> BadgeTone = new()
    {
        ["Beastlore"] = new("#8ae05a"), ["Hunter"] = new("#8ae05a"), ["Arcana"] = new("#cf94ff"), ["Scholar"] = new("#cf94ff"),
        ["Underworld"] = new("#ff8a6a"), ["Outcast"] = new("#ff8a6a"), ["Faith"] = new("#ffd36a"), ["Devout"] = new("#ffd36a"),
    };

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
        var box = Style.Panel(Style.Plate(22));
        box.Position = new Vector2(240, 1080 - 40 - 420);
        box.Size = new Vector2(1440, 420);
        AddChild(box);
        var row = Style.H(28);
        box.AddChild(row);
        // Who.
        var who = Style.V(4);
        who.CustomMinimumSize = new Vector2(230, 0);
        var frame = Style.Panel(Style.Box(new Color(0.03f, 0.025f, 0.04f), Style.Line, 1, 6, 0));
        frame.CustomMinimumSize = new Vector2(228, 274);
        if (d.Person != null) frame.AddChild(new Portrait(new Vector2I(228, 274), Portrait.Framing.Bust).Of(d.Person, d.Arms, d.Scale));
        else
        {
            var c = new CenterContainer();
            c.AddChild(Glyphs.Icon(d.Glyph ?? "talk", 110, new Color("#e8c890")));
            frame.AddChild(c);
        }
        who.AddChild(frame);
        who.AddChild(Style.Label(d.Name, Style.Display, 22, Style.GoldHi, true, HorizontalAlignment.Center));
        if (d.Title != "") who.AddChild(Style.Label(d.Title, Style.TextItalic, 15, Style.InkDim, true, HorizontalAlignment.Center));
        if (d.Mood != "") who.AddChild(Style.H(4, Glyphs.Icon("eye", 13, Style.Gold), Style.Label(d.Mood, Style.Ui, 14, Style.Gold)));
        row.AddChild(who);
        // What is said, and what can be said back.
        var main = Style.V(10);
        main.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        if (d.Speaker == "player") main.AddChild(Style.Label(d.PlayerName.ToUpperInvariant(), Style.Display, 15, new Color("#9ab8d8")));
        text = Style.Label("", d.Speaker == "narrator" ? Style.TextItalic : Style.Text, 23, d.Speaker == "player" ? new Color("#c8d8e8") : d.Speaker == "narrator" ? Style.InkDim : Style.Ink, true);
        text.VisibleCharactersBehavior = TextServer.VisibleCharactersBehavior.CharsAfterShaping;
        text.Text = d.Text;
        text.VisibleCharacters = 0;
        main.AddChild(text);
        main.AddChild(Style.Gap(4));
        choices = Style.V(4);
        choices.Modulate = new Color(1, 1, 1, 0.35f);
        main.AddChild(choices);
        for (int i = 0; i < d.Choices.Count; i++)
        {
            var c = d.Choices[i];
            var key = Style.Key($"{i + 1}");
            key.SizeFlagsVertical = SizeFlags.ShrinkBegin;
            var line = Style.H(8, key);
            if (c.Badge != null)
            {
                var badge = Style.Panel(Style.Box(new Color(0, 0, 0, 0.5f), BadgeTone.GetValueOrDefault(c.Badge, Style.Gold), 1, 8, 5), Style.Label(c.Badge.ToUpperInvariant(), Style.UiHeavy, 11, BadgeTone.GetValueOrDefault(c.Badge, Style.Gold)));
                badge.SizeFlagsVertical = SizeFlags.ShrinkBegin;
                line.AddChild(badge);
            }
            var words = Style.Label(c.Text, Style.UiBold, 18, !c.Enabled ? Style.InkDim with { A = 0.6f } : c.Ends ? Style.InkDim : c.Action != null ? Style.EmberHi : Style.GoldHi, true);
            words.SizeFlagsHorizontal = SizeFlags.ExpandFill;
            line.AddChild(words);
            if (c.Locked != null)
            {
                var why = Style.H(4, Glyphs.Icon("lock", 13, Style.InkDim), Style.Label(c.Locked, Style.TextItalic, 14, Style.InkDim));
                why.SizeFlagsVertical = SizeFlags.ShrinkCenter;
                line.AddChild(why);
            }
            // A row that grows with its words; lit under the pointer.
            var rest = Style.Box(new Color(0, 0, 0, 0), new Color(0, 0, 0, 0), 0, 4, 0);
            var lit = Style.Box(new Color(1, 0.8f, 0.5f, 0.07f), new Color(0, 0, 0, 0), 0, 4, 0);
            foreach (var sb in new[] { rest, lit }) { sb.ContentMarginLeft = sb.ContentMarginRight = 6; sb.ContentMarginTop = sb.ContentMarginBottom = 5; }
            var b = Style.Panel(rest, line);
            b.MouseFilter = MouseFilterEnum.Stop;
            b.MouseDefaultCursorShape = c.Enabled ? CursorShape.PointingHand : CursorShape.Arrow;
            if (c.Enabled)
            {
                b.MouseEntered += () => { b.AddThemeStyleboxOverride("panel", lit); Sound.Sfx.Hover(); };
                b.MouseExited += () => b.AddThemeStyleboxOverride("panel", rest);
            }
            int index = c.Index;
            bool enabled = c.Enabled;
            b.GuiInput += e =>
            {
                if (e is not InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) return;
                if (!Full) { Finish(); return; }
                if (enabled) d.Choose(index);
            };
            choices.AddChild(b);
        }
        if (d.CanContinue)
        {
            var b = Style.Button($"{Controls.Instance.KeyLabel(Act.Confirm)}    Continue", () => { if (!Full) Finish(); else d.Advance(); }, false, true);
            b.SizeFlagsHorizontal = SizeFlags.ShrinkBegin;
            choices.AddChild(b);
        }
        row.AddChild(main);
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
        tick += delta;
        while (tick >= 0.022 && !Full) { tick -= 0.022; shown = Math.Min(d.Text.Length, shown + 2); }
        text.VisibleCharacters = shown;
        if (Full) Finish();
    }

    public bool Key(Act a)
    {
        int n = a switch { Act.Pick1 => 0, Act.Pick2 => 1, Act.Pick3 => 2, Act.Pick4 => 3, _ => -1 };
        if (n < 0 && a is not (Act.Confirm or Act.Interact or Act.Dash))
        {
            if (a is Act.Cancel or Act.Pause)
            {
                // Escape takes the way out, where there is one.
                var leave = d.Choices.FirstOrDefault(c => c.Ends && c.Enabled);
                if (leave != null) d.Choose(leave.Index);
            }
            return true;
        }
        if (!Full) { Finish(); return true; }
        if (n >= 0) { if (n < d.Choices.Count && d.Choices[n].Enabled) d.Choose(d.Choices[n].Index); return true; }
        if (d.CanContinue) d.Advance();
        else if (d.Choices.Count(c => c.Enabled) == 1) d.Choose(d.Choices.First(c => c.Enabled).Index);
        return true;
    }
}
