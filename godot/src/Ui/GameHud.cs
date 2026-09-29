using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>What the level-up draft shows, and what picking does.</summary>
public sealed record DraftView(int Level, bool Blessing, List<Offer> Offers, int Rerolls, int Banishes, int Queued, string? Tip,
    Action<int> Pick, Action Reroll, Action<int> Banish);

/// <summary>A conversation as the panel shows it.</summary>
public sealed record DialogueView(string Name, string Title, string Mood, string Speaker, string Text, List<PresentedChoice> Choices,
    bool CanContinue, Action<int> Choose, Action Advance);

/// <summary>
/// The interface over the game (the web game's ui/hud, in its hand):
/// health low on the left, the ember bar with the level on its medallion
/// across the top, the place top right with what to do next under it, the
/// prompt for what is near, words said, the feed of what was found and
/// learned, the title cards, a boss's bar, the level-up draft and the
/// conversation panel, and the fade between places. Cinzel for names,
/// Alegreya Sans for the rest; the web game's golds, embers and blood.
/// </summary>
public partial class GameHud : CanvasLayer
{
    public static readonly Color Gold = new("#d9b56a"), GoldHi = new("#f3d9a0"), GoldDim = new("#8a6f3e");
    public static readonly Color Ember = new("#ff8a3a"), EmberHi = new("#ffd07a"), Blood = new("#c8323a"), Ink = new("#e8dcc4"), InkDim = new("#a89c88");
    static readonly Color PanelBg = new(0.05f, 0.04f, 0.06f, 0.78f);
    static readonly Dictionary<Rarity, Color> RarityColors = new()
    {
        [Rarity.Common] = new("#c8c0b0"), [Rarity.Uncommon] = new("#6fd46a"), [Rarity.Rare] = new("#5aa8ff"), [Rarity.Epic] = new("#c070ff"), [Rarity.Legendary] = new("#ffb040"),
    };

    public static Font Display = null!, UiFont = null!, UiBold = null!;
    Control root = null!, play = null!;
    ColorRect hpFill = null!, shieldFill = null!, emberFill = null!, bruise = null!, fade = null!;
    Label hpText = null!, level = null!, gold = null!, kills = null!, zoneName = null!, zoneSub = null!, dash = null!, ability = null!, weapons = null!;
    Label promptLabel = null!, sayLabel = null!, announceTitle = null!, announceSub = null!, announceKicker = null!, fadeCaption = null!, fadeSub = null!;
    Panel promptPanel = null!, bossPanel = null!, hintPanel = null!;
    ColorRect bossFill = null!;
    Label bossName = null!, bossTitle = null!, bossChannel = null!, hintTitle = null!, hintText = null!;
    VBoxContainer toasts = null!, objectives = null!;
    Control draft = null!, dialogue = null!;
    double sayT, announceT, announceLife, fadeFrom, fadeTo, fadeT, fadeDur = 1, hudAcc;
    public bool Fading => fadeT < fadeDur;
    public float FadeAmount => fade.Color.A;

    public override void _Ready()
    {
        Layer = 10;
        Display = GD.Load<Font>("res://art/fonts/cinzel-600.woff2");
        UiFont = GD.Load<Font>("res://art/fonts/alegreya-sans-500.woff2");
        UiBold = GD.Load<Font>("res://art/fonts/alegreya-sans-700.woff2");
        root = Full(this);
        root.MouseFilter = Control.MouseFilterEnum.Ignore;

        // The picture's edges bruise when the survivor is hurt.
        bruise = new ColorRect { MouseFilter = Control.MouseFilterEnum.Ignore, Material = VignetteMaterial() };
        Fill(bruise);
        root.AddChild(bruise);

        play = Full(root);
        // The ember bar across the top, the level on its medallion.
        var bar = Frame(play, new Rect2(640, 26, 860, 16));
        emberFill = new ColorRect { Color = Ember, Size = new Vector2(0, 12), Position = new Vector2(2, 2) };
        bar.AddChild(emberFill);
        var medal = new Panel { Position = new Vector2(606, 14), Size = new Vector2(44, 44) };
        medal.AddThemeStyleboxOverride("panel", Box(new Color("#2a1a12"), Gold, 2, 22));
        play.AddChild(medal);
        level = Text(medal, "1", Display, 20, GoldHi, new Rect2(0, 6, 44, 30), HorizontalAlignment.Center);
        kills = Text(play, "", UiFont, 18, InkDim, new Rect2(900, 46, 120, 26), HorizontalAlignment.Center);
        weapons = Text(play, "", UiFont, 17, Ink with { A = 0.85f }, new Rect2(640, 66, 860, 24), HorizontalAlignment.Center);

        // Health, low on the left; gold, the dash and the skill beside it.
        var hp = Frame(play, new Rect2(30, 1020, 400, 28));
        hpFill = new ColorRect { Color = Blood, Size = new Vector2(396, 24), Position = new Vector2(2, 2) };
        hp.AddChild(hpFill);
        shieldFill = new ColorRect { Color = new Color(0.9f, 0.85f, 0.6f, 0.55f), Size = new Vector2(0, 8), Position = new Vector2(2, 2) };
        hp.AddChild(shieldFill);
        hpText = Text(hp, "", UiBold, 17, Ink, new Rect2(0, 1, 400, 26), HorizontalAlignment.Center);
        gold = Text(play, "", UiBold, 19, GoldHi, new Rect2(30, 986, 200, 28), HorizontalAlignment.Left);
        dash = Text(play, "", UiFont, 17, Ink, new Rect2(446, 1022, 200, 26), HorizontalAlignment.Left);
        ability = Text(play, "", UiFont, 17, Ink, new Rect2(446, 994, 300, 26), HorizontalAlignment.Left);

        // The place, top right, and what to do next under it.
        zoneName = Text(play, "", Display, 26, GoldHi, new Rect2(1380, 18, 510, 36), HorizontalAlignment.Right);
        zoneSub = Text(play, "", UiFont, 18, Ink with { A = 0.8f }, new Rect2(1380, 54, 510, 26), HorizontalAlignment.Right);
        objectives = new VBoxContainer { Position = new Vector2(1480, 96), Size = new Vector2(410, 300), MouseFilter = Control.MouseFilterEnum.Ignore };
        objectives.AddThemeConstantOverride("separation", 2);
        play.AddChild(objectives);

        // The feed, lower right.
        toasts = new VBoxContainer { Position = new Vector2(1480, 560), Size = new Vector2(410, 420), Alignment = BoxContainer.AlignmentMode.End, MouseFilter = Control.MouseFilterEnum.Ignore };
        toasts.AddThemeConstantOverride("separation", 6);
        play.AddChild(toasts);

        // What is near, low in the middle; words said above it.
        promptPanel = Frame(play, new Rect2(760, 900, 400, 44));
        promptLabel = Text(promptPanel, "", UiBold, 20, Ink, new Rect2(0, 0, 400, 44), HorizontalAlignment.Center);
        promptPanel.Visible = false;
        sayLabel = Text(play, "", UiFont, 26, Ink, new Rect2(360, 800, 1200, 80), HorizontalAlignment.Center);
        sayLabel.AutowrapMode = TextServer.AutowrapMode.WordSmart;

        // A tip, left.
        hintPanel = Frame(play, new Rect2(30, 380, 380, 130));
        hintTitle = Text(hintPanel, "", Display, 18, GoldHi, new Rect2(14, 8, 352, 26), HorizontalAlignment.Left);
        hintText = Text(hintPanel, "", UiFont, 17, Ink, new Rect2(14, 36, 352, 90), HorizontalAlignment.Left);
        hintText.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        hintText.VerticalAlignment = VerticalAlignment.Top;
        hintPanel.Visible = false;

        // A boss's bar, top middle under the ember.
        bossPanel = new Panel { Position = new Vector2(560, 110), Size = new Vector2(800, 64), MouseFilter = Control.MouseFilterEnum.Ignore };
        bossPanel.AddThemeStyleboxOverride("panel", new StyleBoxEmpty());
        play.AddChild(bossPanel);
        bossName = Text(bossPanel, "", Display, 24, GoldHi, new Rect2(0, 0, 800, 30), HorizontalAlignment.Center);
        var bb = Frame(bossPanel, new Rect2(0, 32, 800, 16));
        bossFill = new ColorRect { Color = new Color("#9a2a24"), Size = new Vector2(796, 12), Position = new Vector2(2, 2) };
        bb.AddChild(bossFill);
        bossTitle = Text(bossPanel, "", UiFont, 16, InkDim, new Rect2(0, 48, 800, 20), HorizontalAlignment.Center);
        bossChannel = Text(bossPanel, "", UiBold, 18, EmberHi, new Rect2(0, 68, 800, 24), HorizontalAlignment.Center);
        bossPanel.Visible = false;

        // Title cards, in the middle.
        announceKicker = Text(root, "", UiBold, 20, Gold, new Rect2(0, 300, 1920, 30), HorizontalAlignment.Center);
        announceTitle = Text(root, "", Display, 64, GoldHi, new Rect2(0, 330, 1920, 90), HorizontalAlignment.Center);
        announceSub = Text(root, "", UiFont, 26, Ink, new Rect2(0, 420, 1920, 40), HorizontalAlignment.Center);

        draft = Full(root);
        draft.Visible = false;
        dialogue = Full(root);
        dialogue.Visible = false;

        // The fade between places, over everything.
        fade = new ColorRect { Color = new Color(0, 0, 0, 1), MouseFilter = Control.MouseFilterEnum.Ignore };
        Fill(fade);
        root.AddChild(fade);
        fadeCaption = Text(root, "", Display, 54, GoldHi, new Rect2(0, 470, 1920, 80), HorizontalAlignment.Center);
        fadeSub = Text(root, "", UiFont, 24, Ink, new Rect2(0, 550, 1920, 40), HorizontalAlignment.Center);
        fadeT = fadeDur = 1;
        fadeFrom = fadeTo = 1;
    }

    /* ----------------------------------------------------------- helpers -- */

    static Control Full(Node parent)
    {
        var c = new Control { MouseFilter = Control.MouseFilterEnum.Ignore };
        Fill(c);
        parent.AddChild(c);
        return c;
    }

    static void Fill(Control c)
    {
        c.AnchorRight = 1;
        c.AnchorBottom = 1;
        c.OffsetLeft = c.OffsetTop = c.OffsetRight = c.OffsetBottom = 0;
    }

    public static StyleBoxFlat Box(Color bg, Color border, int width = 1, int radius = 3) => new()
    {
        BgColor = bg, BorderColor = border, BorderWidthLeft = width, BorderWidthRight = width, BorderWidthTop = width, BorderWidthBottom = width,
        CornerRadiusTopLeft = radius, CornerRadiusTopRight = radius, CornerRadiusBottomLeft = radius, CornerRadiusBottomRight = radius,
        ContentMarginLeft = 12, ContentMarginRight = 12, ContentMarginTop = 8, ContentMarginBottom = 8,
    };

    static Panel Frame(Control parent, Rect2 at)
    {
        var p = new Panel { Position = at.Position, Size = at.Size, MouseFilter = Control.MouseFilterEnum.Ignore };
        p.AddThemeStyleboxOverride("panel", Box(PanelBg, GoldDim));
        parent.AddChild(p);
        return p;
    }

    public static Label Text(Control parent, string s, Font font, int size, Color color, Rect2 at, HorizontalAlignment align)
    {
        var l = new Label { Text = s, Position = at.Position, Size = at.Size, HorizontalAlignment = align, VerticalAlignment = VerticalAlignment.Center, MouseFilter = Control.MouseFilterEnum.Ignore };
        Style(l, font, size, color);
        parent.AddChild(l);
        return l;
    }

    public static void Style(Control l, Font font, int size, Color color)
    {
        l.AddThemeFontOverride("font", font);
        l.AddThemeFontSizeOverride("font_size", size);
        l.AddThemeColorOverride("font_color", color);
        l.AddThemeColorOverride("font_shadow_color", new Color(0, 0, 0, 0.85f));
        l.AddThemeConstantOverride("shadow_offset_y", 2);
        l.AddThemeConstantOverride("shadow_offset_x", 1);
    }

    static ShaderMaterial VignetteMaterial()
    {
        var sh = new Shader
        {
            Code = """
                shader_type canvas_item;
                uniform float amount = 0.0;
                void fragment() {
                    vec2 d = UV - 0.5;
                    float r = length(d * vec2(1.0, 0.75)) * 1.6;
                    COLOR = vec4(0.45, 0.02, 0.02, smoothstep(0.55, 1.1, r) * amount * 0.85);
                }
                """,
        };
        return new ShaderMaterial { Shader = sh };
    }

    /* ------------------------------------------------------------- state -- */

    /// <summary>The play HUD (bars, feed, names) shown or not (the title has none).</summary>
    public void ShowPlay(bool on) => play.Visible = on;

    public void Bars(Battle? b, double gold, int draughts)
    {
        if (b == null) return;
        var p = b.Player;
        double max = b.MaxHp;
        hpFill.Size = new Vector2(396 * (float)Math.Clamp(p.Hp / max, 0, 1), 24);
        shieldFill.Size = new Vector2(396 * (float)Math.Clamp(p.Shield / max, 0, 1), 8);
        hpText.Text = $"{Math.Ceiling(Math.Max(p.Hp, 0))} / {Math.Round(max)}";
        float ember = (float)Math.Clamp(b.EmberXp / Math.Max(1, b.EmberNext), 0, 1);
        emberFill.Size = new Vector2(856 * ember, 12);
        emberFill.Color = ember > 0.9f ? EmberHi : Ember;
        level.Text = b.EmberLevel.ToString();
        kills.Text = b.KillCount > 0 ? $"{b.KillCount} fallen" : "";
        this.gold.Text = $"{Math.Floor(gold + b.GoldGained)} gold" + (draughts > 0 ? $"    {draughts} draught{(draughts == 1 ? "" : "s")} (R)" : "");
        int charges = p.DashCharges, maxDash = (int)Math.Round(b.Stats.Get(Stat.DashCharges));
        dash.Text = $"Dash {new string('●', Math.Max(0, charges))}{new string('○', Math.Max(0, maxDash - charges))}";
        if (b.Ability is AbilityKind ak)
        {
            var def = Content.Abilities.All[ak];
            ability.Text = p.AbilityCd > 0 ? $"{def.Name}  {Math.Ceiling(p.AbilityCd)}s" : $"{def.Name}  ready (Q)";
        }
        else ability.Text = "";
        weapons.Text = string.Join("   ·   ", b.Weapons.Select(w => $"{w.Evolution?.Name ?? w.Def.Name} {Roman(w.Rank)}"));
        bruise.Visible = b.Combat;
    }

    static string Roman(int n) => n switch { 1 => "I", 2 => "II", 3 => "III", 4 => "IV", 5 => "V", 6 => "VI", 7 => "VII", 8 => "VIII", _ => n.ToString() };

    public void SetBruise(float v) => ((ShaderMaterial)bruise.Material).SetShaderParameter("amount", v);

    public void ZoneInfo(string name, string? region, int day, TimeOfDay time)
    {
        zoneName.Text = name.ToUpperInvariant();
        zoneSub.Text = $"{time.ToString()}  ·  Day {day}" + (region != null ? $"  ·  {region}" : "");
    }

    public void Prompt(string? text)
    {
        promptPanel.Visible = text != null;
        if (text == null) return;
        promptLabel.Text = text;
        var w = UiBold.GetStringSize(text, HorizontalAlignment.Left, -1, 20).X + 48;
        promptPanel.Size = new Vector2(w, 44);
        promptPanel.Position = new Vector2(960 - w / 2, 900);
        promptLabel.Size = promptPanel.Size;
    }

    public void Say(string text, string? who, double seconds)
    {
        sayLabel.Text = who != null ? $"{who}: {text}" : text;
        sayT = seconds;
        sayLabel.Modulate = Colors.White;
    }

    public void Toast(Toast t)
    {
        var box = new PanelContainer { MouseFilter = Control.MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(410, 0) };
        var accent = t.Kind switch
        {
            ToastKind.Loot => t.Rarity is int r ? new[] { "#c8c0b0", "#6fd46a", "#5aa8ff", "#c070ff", "#ffb040", "#ff6a3a" }[Math.Clamp(r, 0, 5)] : "#c8c0b0",
            ToastKind.Gold => "#f3d9a0", ToastKind.Quest => "#d9b56a", ToastKind.Warning => "#c8323a", ToastKind.Level => "#ffd07a", ToastKind.Relation => "#c890b0",
            _ => "#8a9aa8",
        };
        var style = Box(PanelBg, new Color(accent) with { A = 0.7f });
        style.BorderWidthLeft = 4;
        box.AddThemeStyleboxOverride("panel", style);
        var v = new VBoxContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
        box.AddChild(v);
        var title = new Label { Text = t.Text, AutowrapMode = TextServer.AutowrapMode.WordSmart };
        Style(title, UiBold, 19, new Color(accent).Lightened(0.2f));
        v.AddChild(title);
        if (!string.IsNullOrEmpty(t.Sub))
        {
            var sub = new Label { Text = t.Sub, AutowrapMode = TextServer.AutowrapMode.WordSmart };
            Style(sub, UiFont, 16, InkDim);
            v.AddChild(sub);
        }
        box.SetMeta("life", t.Life ?? 5);
        box.SetMeta("t", 0.0);
        toasts.AddChild(box);
        while (toasts.GetChildCount() > 6) toasts.GetChild(0).Free();
    }

    public void Announce(Announcement a)
    {
        announceTitle.Text = a.Title;
        announceSub.Text = a.Sub ?? "";
        announceKicker.Text = a.Kicker?.ToUpperInvariant() ?? "";
        announceTitle.AddThemeColorOverride("font_color", a.Kind switch { "danger" => new Color("#ff8a6a"), "boon" => EmberHi, _ => GoldHi });
        announceT = 0;
        announceLife = a.Seconds;
    }

    public void Boss(BossBar? bar)
    {
        bossPanel.Visible = bar != null;
        if (bar == null) return;
        bossName.Text = bar.Name;
        bossTitle.Text = bar.Title + (bar.Shielded ? "  ·  shielded" : "");
        bossFill.Size = new Vector2(796 * (float)Math.Clamp(bar.Hp / Math.Max(1, bar.MaxHp), 0, 1), 12);
        bossFill.Color = bar.Shielded ? new Color("#8a8a9a") : new Color("#9a2a24");
        bossChannel.Text = bar.Channel is var (label, prog) ? $"{label}  {Math.Round(prog * 100)}%" : "";
    }

    public void Objectives(List<Tracked> list)
    {
        foreach (var c in objectives.GetChildren()) c.QueueFree();
        foreach (var t in list)
        {
            var title = new Label { Text = t.Title, HorizontalAlignment = HorizontalAlignment.Right };
            Style(title, Display, 18, t.Tone == TrackTone.Tutorial ? Ink : GoldHi);
            objectives.AddChild(title);
            foreach (var s in t.Steps)
            {
                var l = new Label { Text = (s.Done ? "✓ " : s.Optional ? "◦ " : "• ") + s.Text, HorizontalAlignment = HorizontalAlignment.Right, AutowrapMode = TextServer.AutowrapMode.WordSmart, CustomMinimumSize = new Vector2(410, 0) };
                Style(l, UiFont, 16, s.Done ? InkDim with { A = 0.6f } : s.Optional ? InkDim : Ink);
                objectives.AddChild(l);
            }
        }
    }

    public void Hint(Hint? h)
    {
        hintPanel.Visible = h != null;
        if (h == null) return;
        hintTitle.Text = h.Title;
        hintText.Text = h.Text + (h.Keys.Count > 0 ? $"\n[{string.Join("] [", h.Keys)}]" : "");
    }

    /// <summary>Fade to black (1) or back (0) over some seconds, with words over the black.</summary>
    public void Fade(float to, double seconds, string? caption = null, string? sub = null)
    {
        fadeFrom = fade.Color.A;
        fadeTo = to;
        fadeT = 0;
        fadeDur = Math.Max(0.01, seconds);
        if (to > 0.5f)
        {
            fadeCaption.Text = caption ?? "";
            fadeSub.Text = sub ?? "";
        }
    }

    /* -------------------------------------------------------------- draft -- */

    public void Draft(DraftView? d)
    {
        foreach (var c in draft.GetChildren()) c.QueueFree();
        draft.Visible = d != null;
        if (d == null) return;
        var dim = new ColorRect { Color = new Color(0, 0, 0, 0.55f), MouseFilter = Control.MouseFilterEnum.Stop };
        Fill(dim);
        draft.AddChild(dim);
        Text(draft, d.Blessing ? "A BLESSING" : "THE EMBER RISES", UiBold, 20, Gold, new Rect2(0, 190, 1920, 30), HorizontalAlignment.Center);
        Text(draft, d.Blessing ? "Choose what the light keeps" : $"Level {d.Level}", Display, 52, GoldHi, new Rect2(0, 220, 1920, 70), HorizontalAlignment.Center);
        if (d.Tip != null) Text(draft, d.Tip, UiFont, 20, Ink, new Rect2(360, 290, 1200, 40), HorizontalAlignment.Center);
        int n = d.Offers.Count;
        float w = 340, gap = 30, x0 = 960 - (n * w + (n - 1) * gap) / 2;
        for (int i = 0; i < n; i++)
        {
            var o = d.Offers[i];
            int index = i;
            var card = new Button { Position = new Vector2(x0 + i * (w + gap), 340), Size = new Vector2(w, 420), FocusMode = Control.FocusModeEnum.None };
            var col = RarityColors.GetValueOrDefault(o.Rarity, Ink);
            card.AddThemeStyleboxOverride("normal", Box(new Color(0.07f, 0.055f, 0.07f, 0.95f), col with { A = 0.8f }, 2, 6));
            card.AddThemeStyleboxOverride("hover", Box(new Color(0.12f, 0.09f, 0.08f, 0.97f), col, 3, 6));
            card.AddThemeStyleboxOverride("pressed", Box(new Color(0.16f, 0.11f, 0.08f, 0.97f), col, 3, 6));
            card.Pressed += () => d.Pick(index);
            draft.AddChild(card);
            var kind = o.Kind switch { OfferKind.Weapon => "New weapon", OfferKind.Rank => $"Rank {o.From} → {o.To}", OfferKind.Evolve => "Evolution", OfferKind.Heal => "Mend", OfferKind.Gold => "Gold", _ => o.Blessing ? "Blessing" : "Skill" };
            Text(card, $"{i + 1}", Display, 22, GoldDim, new Rect2(16, 10, 40, 30), HorizontalAlignment.Left);
            Text(card, kind.ToUpperInvariant(), UiBold, 15, col, new Rect2(0, 18, w, 22), HorizontalAlignment.Center);
            var title = Text(card, o.Title, Display, 26, GoldHi, new Rect2(16, 50, w - 32, 80), HorizontalAlignment.Center);
            title.AutowrapMode = TextServer.AutowrapMode.WordSmart;
            var body = Text(card, o.Text, UiFont, 19, Ink, new Rect2(22, 140, w - 44, 230), HorizontalAlignment.Center);
            body.AutowrapMode = TextServer.AutowrapMode.WordSmart;
            body.VerticalAlignment = VerticalAlignment.Top;
            Text(card, o.Rarity.ToString(), UiFont, 15, col with { A = 0.8f }, new Rect2(0, 384, w, 24), HorizontalAlignment.Center);
        }
        var foot = $"[1-{n}] choose     [X] reroll ({d.Rerolls})     [B] then a number: banish ({d.Banishes})" + (d.Queued > 0 ? $"     {d.Queued} more to come" : "");
        Text(draft, foot, UiFont, 19, InkDim, new Rect2(0, 790, 1920, 30), HorizontalAlignment.Center);
    }

    /* ---------------------------------------------------------- dialogue -- */

    public void Dialogue(DialogueView? d)
    {
        foreach (var c in dialogue.GetChildren()) c.QueueFree();
        dialogue.Visible = d != null;
        if (d == null) return;
        var panel = new Panel { Position = new Vector2(360, 640), Size = new Vector2(1200, 400) };
        panel.AddThemeStyleboxOverride("panel", Box(new Color(0.045f, 0.036f, 0.05f, 0.93f), GoldDim, 1, 6));
        dialogue.AddChild(panel);
        bool player = d.Speaker == "player", narrator = d.Speaker == "narrator";
        Text(panel, d.Name, Display, 28, GoldHi, new Rect2(28, 14, 800, 36), HorizontalAlignment.Left);
        Text(panel, d.Title + (d.Mood != "" ? $"  ·  {d.Mood}" : ""), UiFont, 17, InkDim, new Rect2(28, 48, 800, 24), HorizontalAlignment.Left);
        var text = Text(panel, d.Text, narrator ? UiFont : UiFont, 22, player ? new Color("#c8d8e8") : narrator ? InkDim : Ink, new Rect2(28, 82, 1144, 120), HorizontalAlignment.Left);
        text.AutowrapMode = TextServer.AutowrapMode.WordSmart;
        text.VerticalAlignment = VerticalAlignment.Top;
        if (d.CanContinue)
        {
            var go = Choice(panel, "Continue", 0, 1, true, null);
            go.Pressed += d.Advance;
            return;
        }
        for (int i = 0; i < d.Choices.Count; i++)
        {
            var c = d.Choices[i];
            var b = Choice(panel, $"{i + 1}.  {c.Text}" + (c.Badge != null ? $"   [{c.Badge}]" : "") + (c.Locked != null ? $"   ({c.Locked})" : ""), i, d.Choices.Count, c.Enabled, c.Ends ? "ends" : null);
            int index = c.Index;
            if (c.Enabled) b.Pressed += () => d.Choose(index);
        }
    }

    static Button Choice(Panel panel, string text, int i, int n, bool enabled, string? tag)
    {
        var b = new Button { Text = text, Position = new Vector2(28, 212 + i * 42), Size = new Vector2(1144, 38), Alignment = HorizontalAlignment.Left, Disabled = !enabled, FocusMode = Control.FocusModeEnum.None };
        Style(b, UiBold, 19, enabled ? GoldHi : InkDim);
        b.AddThemeColorOverride("font_hover_color", EmberHi);
        b.AddThemeColorOverride("font_disabled_color", InkDim with { A = 0.6f });
        b.AddThemeStyleboxOverride("normal", new StyleBoxEmpty());
        b.AddThemeStyleboxOverride("hover", Box(new Color(1, 0.8f, 0.5f, 0.07f), new Color(0, 0, 0, 0), 0));
        b.AddThemeStyleboxOverride("pressed", Box(new Color(1, 0.8f, 0.5f, 0.12f), new Color(0, 0, 0, 0), 0));
        b.AddThemeStyleboxOverride("disabled", new StyleBoxEmpty());
        panel.AddChild(b);
        return b;
    }

    /* ------------------------------------------------------------- frame -- */

    public override void _Process(double delta)
    {
        // Words said fade after their time.
        if (sayT > 0)
        {
            sayT -= delta;
            sayLabel.Modulate = Colors.White with { A = (float)Math.Clamp(sayT / 0.6, 0, 1) };
            if (sayT <= 0) sayLabel.Text = "";
        }
        // Title cards: in, held, out.
        if (announceT < announceLife)
        {
            announceT += delta;
            float a = (float)Math.Clamp(Math.Min(announceT / 0.4, (announceLife - announceT) / 0.8), 0, 1);
            foreach (var l in new[] { announceTitle, announceSub, announceKicker }) l.Modulate = Colors.White with { A = a };
        }
        else foreach (var l in new[] { announceTitle, announceSub, announceKicker }) l.Modulate = Colors.White with { A = 0 };
        // The feed: each goes after its life.
        foreach (var c in toasts.GetChildren())
        {
            if (c is not Control box) continue;
            double t = (double)box.GetMeta("t") + delta, life = (double)box.GetMeta("life");
            box.SetMeta("t", t);
            box.Modulate = Colors.White with { A = (float)Math.Clamp(Math.Min(t / 0.25, (life - t) / 0.6), 0, 1) };
            if (t >= life) box.QueueFree();
        }
        // The fade.
        if (fadeT < fadeDur)
        {
            fadeT += delta;
            float k = (float)Math.Clamp(fadeT / fadeDur, 0, 1);
            k = k * k * (3 - 2 * k);
            fade.Color = new Color(0, 0, 0, Mathf.Lerp((float)fadeFrom, (float)fadeTo, k));
        }
        float cap = Mathf.Clamp((fade.Color.A - 0.6f) / 0.4f, 0, 1);
        fadeCaption.Modulate = Colors.White with { A = cap };
        fadeSub.Modulate = Colors.White with { A = cap };
    }
}
