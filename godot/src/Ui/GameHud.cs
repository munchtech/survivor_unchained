using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>What is near and can be used, as the prompt shows it.</summary>
public sealed record PromptView(string Key, string Verb, string Target, string? Hint, string? Locked);

/// <summary>
/// The heads-up display (the web game's ui/hud): arranged so the eye never
/// has to hunt. What can kill you (health, the boss) is where the eye
/// already rests; what you choose (ember, the next level) at the top edge;
/// what fires by itself (the weapons) a quiet row at the bottom that lights
/// up when something happens to it; what your hands do (dash, the skill,
/// a draught) under your right thumb. Everything else (the place, the
/// quest, the loot) comes and goes at the edges. The web game's sizes are
/// for a 900-pixel-tall screen; here they are for 1080 (×1.2).
/// </summary>
public partial class GameHud : CanvasLayer
{
    const float K = 1.2f;
    Control root = null!, play = null!, combat = null!;
    ColorRect bruise = null!;
    TextureRect emberFill = null!;
    Label emberLevel = null!, tallyTime = null!, tallyKills = null!, tallyGold = null!;
    int shownLevel;
    double levelPop;
    TextureRect hpFill = null!;
    ColorRect hpTrail = null!, hpShield = null!, hpLow = null!;
    Label hpText = null!;
    HBoxContainer statuses = null!;
    Control heart = null!;
    float hpShown = 1, trailShown = 1, trailWait;
    HBoxContainer boons = null!, weapons = null!;
    readonly Dictionary<string, WeaponSlot> slots = new();
    HBoxContainer dashPips = null!;
    static readonly StyleBoxFlat PipOn = Style.Box(new Color("#7ab0ff"), new Color("#cfe4ff"), 1, 3, 0), PipOff = Style.Box(new Color("#14121a"), Style.Line, 1, 3, 0);
    Control quick = null!;
    Label quickQty = null!;
    Ring abilityRing = null!;
    TextureRect abilityGlyph = null!;
    Label abilityCd = null!, abilityName = null!;
    Label zoneName = null!;
    HBoxContainer zoneSub = null!;
    VBoxContainer objectives = null!, toasts = null!;
    PanelContainer promptBox = null!, hintBox = null!;
    Control subtitle = null!, announce = null!, bossBox = null!;
    Label sayWho = null!, sayText = null!, annKicker = null!, annTitle = null!, annSub = null!;
    Label bossName = null!, bossTitle = null!, bossChannel = null!;
    ColorRect bossFill = null!, bossTrail = null!, bossChannelFill = null!;
    Control bossTrack = null!, bossChannelBox = null!;
    double sayT, annT, annLife;
    ColorRect fade = null!;
    Label fadeCaption = null!, fadeSub = null!;
    double fadeFrom = 1, fadeTo = 1, fadeT = 1, fadeDur = 1;
    DraftPanel? draft;
    TalkPanel? talk;
    public float FadeAmount => fade.Color.A;

    static Color Hex(string h) => new(h);

    public override void _Ready()
    {
        Layer = 10;
        root = new Control { MouseFilter = Control.MouseFilterEnum.Ignore };
        Style.Fill(root);
        AddChild(root);
        bruise = new ColorRect { MouseFilter = Control.MouseFilterEnum.Ignore, Material = VignetteMaterial() };
        Style.Fill(bruise);
        root.AddChild(bruise);
        play = new Control { MouseFilter = Control.MouseFilterEnum.Ignore };
        Style.Fill(play);
        root.AddChild(play);
        combat = new Control { MouseFilter = Control.MouseFilterEnum.Ignore };
        Style.Fill(combat);
        play.AddChild(combat);
        BuildEmber();
        BuildVitals();
        BuildArsenal();
        BuildHands();
        BuildCorner();
        BuildEdges();
        BuildBoss();
        var top = new CanvasLayer { Layer = 30 };
        AddChild(top);
        fade = new ColorRect { Color = new Color(0, 0, 0, 1), MouseFilter = Control.MouseFilterEnum.Ignore };
        Style.Fill(fade);
        top.AddChild(fade);
        fadeCaption = Style.Label("", Style.Display, 54, Style.GoldHi, false, HorizontalAlignment.Center);
        fadeCaption.Position = new Vector2(0, 470); fadeCaption.Size = new Vector2(1920, 80);
        top.AddChild(fadeCaption);
        fadeSub = Style.Label("", Style.TextItalic, 24, Style.Ink, false, HorizontalAlignment.Center);
        fadeSub.Position = new Vector2(0, 550); fadeSub.Size = new Vector2(1920, 40);
        top.AddChild(fadeSub);
    }

    static Control Box(Control parent, float x, float y, float w, float h)
    {
        var c = new Control { Position = new Vector2(x, y), Size = new Vector2(w, h), MouseFilter = Control.MouseFilterEnum.Ignore };
        parent.AddChild(c);
        return c;
    }

    static TextureRect GradientRect(Color[] colors, float[]? stops = null, bool vertical = false)
    {
        var g = new Gradient { Colors = colors, Offsets = stops ?? Enumerable.Range(0, colors.Length).Select(i => i / (float)(colors.Length - 1)).ToArray() };
        return new TextureRect
        {
            Texture = new GradientTexture2D { Gradient = g, Width = vertical ? 4 : 256, Height = vertical ? 256 : 4, FillTo = vertical ? new Vector2(0, 1) : new Vector2(1, 0) },
            StretchMode = TextureRect.StretchModeEnum.Scale, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, MouseFilter = Control.MouseFilterEnum.Ignore,
        };
    }

    /// <summary>A round medallion rimmed in gold (the ember's, the heart's).</summary>
    static Panel Medal(Control parent, Vector2 at, float size, Color inner)
    {
        var p = new Panel { Position = at, Size = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Ignore };
        var s = Style.Box(inner, Style.GoldDim, 3, (int)(size / 2), 0);
        s.ShadowColor = new Color(1f, 0.55f, 0.2f, 0.35f);
        s.ShadowSize = 10;
        p.AddThemeStyleboxOverride("panel", s);
        parent.AddChild(p);
        return p;
    }

    void BuildEmber()
    {
        float w = 760 * K, x = (1920 - w) / 2;
        var track = new Panel { Position = new Vector2(x + 30, 23), Size = new Vector2(w - 30, 12), MouseFilter = Control.MouseFilterEnum.Ignore, ClipContents = true };
        track.AddThemeStyleboxOverride("panel", Style.Box(Hex("#120c0a"), new Color(0.85f, 0.71f, 0.42f, 0.28f), 1, 5, 0));
        combat.AddChild(track);
        emberFill = GradientRect([Hex("#6a1e04"), Hex("#c24a0a"), Hex("#ff8a2a"), Hex("#ffd070")], [0, 0.45f, 0.85f, 1]);
        emberFill.Position = new Vector2(1, 1);
        emberFill.Size = new Vector2(0, 10);
        track.AddChild(emberFill);
        for (int i = 1; i < 10; i++) track.AddChild(new ColorRect { Color = new Color(0, 0, 0, 0.55f), Position = new Vector2((w - 30) * i / 10f, 0), Size = new Vector2(1, 12), MouseFilter = Control.MouseFilterEnum.Ignore });
        var medal = Medal(combat, new Vector2(x, 6), 46, Hex("#3a2210"));
        emberLevel = Style.Label("1", Style.Display, 20, Style.EmberHi, false, HorizontalAlignment.Center);
        emberLevel.Size = new Vector2(46, 46);
        emberLevel.PivotOffset = new Vector2(23, 23);
        emberLevel.VerticalAlignment = VerticalAlignment.Center;
        medal.AddChild(emberLevel);
        tallyTime = Style.Label("0:00", Style.Display, 23, Hex("#efe3c8"), false, HorizontalAlignment.Center);
        tallyTime.Position = new Vector2(860, 50); tallyTime.Size = new Vector2(200, 28);
        combat.AddChild(tallyTime);
        var row = Style.H(16);
        tallyKills = Style.Label("0", Style.UiBold, 16, Hex("#cfc3ad"));
        tallyGold = Style.Label("0", Style.UiBold, 16, Style.GoldHi);
        row.AddChild(Style.H(4, Glyphs.Icon("skull", 16, Hex("#cfc3ad")), tallyKills));
        row.AddChild(Style.H(4, Glyphs.Icon("coin", 16, Style.GoldHi), tallyGold));
        row.Alignment = BoxContainer.AlignmentMode.Center;
        row.Position = new Vector2(860, 80); row.Size = new Vector2(200, 20);
        combat.AddChild(row);
    }

    void BuildVitals()
    {
        var v = Box(play, 34, 1080 - 36 - 70, 396, 70);
        statuses = Style.H(6);
        statuses.Position = new Vector2(43, 0);
        v.AddChild(statuses);
        var bar = new Panel { Position = new Vector2(34, 38), Size = new Vector2(362, 26), ClipContents = true, MouseFilter = Control.MouseFilterEnum.Ignore };
        bar.AddThemeStyleboxOverride("panel", Style.Box(Hex("#160a0a"), new Color(0.85f, 0.71f, 0.42f, 0.32f), 1, 4, 0));
        v.AddChild(bar);
        hpTrail = new ColorRect { Color = Hex("#e8c07a") with { A = 0.85f }, Position = new Vector2(1, 1), Size = new Vector2(360, 24), MouseFilter = Control.MouseFilterEnum.Ignore };
        bar.AddChild(hpTrail);
        hpFill = GradientRect([Hex("#ff6a5a"), Hex("#d2262c"), Hex("#8a0e16")], [0, 0.35f, 1], true);
        hpFill.Position = new Vector2(1, 1); hpFill.Size = new Vector2(360, 24);
        bar.AddChild(hpFill);
        hpShield = new ColorRect { Color = Hex("#9ad4ff"), Position = new Vector2(1, 1), Size = new Vector2(0, 7), MouseFilter = Control.MouseFilterEnum.Ignore };
        bar.AddChild(hpShield);
        for (int i = 1; i < 4; i++) bar.AddChild(new ColorRect { Color = new Color(0, 0, 0, 0.4f), Position = new Vector2(362 * i / 4f, 0), Size = new Vector2(1, 26), MouseFilter = Control.MouseFilterEnum.Ignore });
        hpLow = new ColorRect { Color = new Color(1, 0.24f, 0.24f, 0), Size = new Vector2(362, 26), MouseFilter = Control.MouseFilterEnum.Ignore };
        bar.AddChild(hpLow);
        hpText = Style.Label("", Style.UiHeavy, 16, Hex("#fff4ea"), false, HorizontalAlignment.Center);
        hpText.Size = new Vector2(362, 26);
        hpText.VerticalAlignment = VerticalAlignment.Center;
        bar.AddChild(hpText);
        var h = Medal(v, new Vector2(0, 30), 41, Hex("#3a0c10"));
        heart = h;
        h.PivotOffset = new Vector2(20.5f, 20.5f);
        var g = Glyphs.Icon("heart", 22, Hex("#ffb0a8"));
        g.Position = new Vector2(9.5f, 9.5f); g.Size = new Vector2(22, 22);
        h.AddChild(g);
    }

    void BuildArsenal()
    {
        var col = Style.V(12);
        col.Alignment = BoxContainer.AlignmentMode.End;
        col.Position = new Vector2(460, 1080 - 26 - 140);
        col.Size = new Vector2(1000, 140);
        combat.AddChild(col);
        boons = Style.H(5);
        boons.Alignment = BoxContainer.AlignmentMode.Center;
        col.AddChild(boons);
        weapons = Style.H(10);
        weapons.Alignment = BoxContainer.AlignmentMode.Center;
        col.AddChild(weapons);
    }

    void BuildHands()
    {
        var h = Style.H(19);
        h.Alignment = BoxContainer.AlignmentMode.End;
        h.Position = new Vector2(1920 - 36 - 420, 1080 - 19 - 130);
        h.Size = new Vector2(420, 130);
        combat.AddChild(h);
        Control Hand(Control art, Act key, string label, out Label name)
        {
            var v = Style.V(8);
            v.Alignment = BoxContainer.AlignmentMode.End;
            var c = new CenterContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
            c.AddChild(art);
            v.AddChild(c);
            name = Style.Label(label, Style.UiBold, 14, Style.Ink);
            var row = Style.H(5, Style.Key(Controls.Instance.KeyLabel(key)), name);
            row.Alignment = BoxContainer.AlignmentMode.Center;
            v.AddChild(row);
            h.AddChild(v);
            return v;
        }
        dashPips = Style.H(5);
        Hand(dashPips, Act.Dash, "Dash", out _);
        var q = new Panel { CustomMinimumSize = new Vector2(60, 60), MouseFilter = Control.MouseFilterEnum.Ignore };
        q.AddThemeStyleboxOverride("panel", Style.Box(Hex("#1a1620"), Style.Line, 1, 9, 0));
        var qi = ItemPhotos.Icon("potion", 50, Hex("#ff8a80"));
        qi.Position = new Vector2(5, 3); qi.Size = new Vector2(50, 50);
        q.AddChild(qi);
        quickQty = Style.Label("", Style.UiHeavy, 14, Colors.White);
        quickQty.Position = new Vector2(44, 40);
        q.AddChild(quickQty);
        quick = Hand(q, Act.Ultimate, "Draught", out _);
        var ab = new Control { CustomMinimumSize = new Vector2(89, 89), MouseFilter = Control.MouseFilterEnum.Ignore };
        abilityRing = new Ring { Size = new Vector2(89, 89), MouseFilter = Control.MouseFilterEnum.Ignore };
        ab.AddChild(abilityRing);
        abilityGlyph = Glyphs.Icon("shield", 41);
        abilityGlyph.Position = new Vector2(24, 24); abilityGlyph.Size = new Vector2(41, 41);
        ab.AddChild(abilityGlyph);
        abilityCd = Style.Label("", Style.Display, 22, Colors.White, false, HorizontalAlignment.Center);
        abilityCd.Size = new Vector2(89, 89);
        abilityCd.VerticalAlignment = VerticalAlignment.Center;
        ab.AddChild(abilityCd);
        Hand(ab, Act.Ability, "", out abilityName);
    }

    static readonly string[] Numerals = ["I", "II", "III", "IV", "V"];

    void BuildCorner()
    {
        var c = Style.V(3);
        c.Position = new Vector2(1920 - 31 - 400, 22);
        c.Size = new Vector2(400, 0);
        play.AddChild(c);
        zoneName = Style.Label("", Style.Display, 29, Style.GoldHi, false, HorizontalAlignment.Right);
        c.AddChild(zoneName);
        zoneSub = Style.H(6);
        zoneSub.Alignment = BoxContainer.AlignmentMode.End;
        c.AddChild(zoneSub);
        c.AddChild(Style.Gap(10));
        objectives = Style.V(3);
        c.AddChild(objectives);
    }

    void BuildEdges()
    {
        toasts = Style.V(7);
        toasts.Position = new Vector2(31, 1080 * 0.34f);
        toasts.Size = new Vector2(408, 0);
        play.AddChild(toasts);
        hintBox = Style.Panel(Style.Box(Hex("#e6d6b0"), new Color(0.35f, 0.24f, 0.08f, 0.45f), 1, 4, 14));
        // Pinned by its foot above the vitals; grows upward with its words.
        hintBox.AnchorTop = hintBox.AnchorBottom = 1;
        hintBox.OffsetLeft = 34; hintBox.OffsetBottom = -134;
        hintBox.GrowVertical = Control.GrowDirection.Begin;
        hintBox.CustomMinimumSize = new Vector2(396, 0);
        hintBox.Visible = false;
        play.AddChild(hintBox);
        subtitle = Style.V(2);
        subtitle.Position = new Vector2(504, 1080 - 228 - 90);
        subtitle.Size = new Vector2(912, 90);
        ((VBoxContainer)subtitle).Alignment = BoxContainer.AlignmentMode.End;
        sayWho = Style.Label("", Style.Display, 16, Style.Gold, false, HorizontalAlignment.Center);
        sayText = Style.Label("", Style.Text, 24, Hex("#f4ecdc"), true, HorizontalAlignment.Center);
        subtitle.AddChild(sayWho);
        subtitle.AddChild(sayText);
        subtitle.Modulate = Colors.Transparent;
        play.AddChild(subtitle);
        promptBox = Style.Panel(Style.Box(new Color(0.08f, 0.07f, 0.09f, 0.92f), Style.Line, 1, 24, 10));
        promptBox.Visible = false;
        play.AddChild(promptBox);
        var ann = Style.V(4);
        ann.Position = new Vector2(360, 1080 * 0.2f);
        ann.Size = new Vector2(1200, 200);
        annKicker = Style.Label("", Style.UiHeavy, 16, Hex("#ffcf8a"), false, HorizontalAlignment.Center);
        annTitle = Style.Label("", Style.Display, 50, Hex("#f0c878"), true, HorizontalAlignment.Center);
        annSub = Style.Label("", Style.TextItalic, 24, Hex("#e8dcc6"), true, HorizontalAlignment.Center);
        ann.AddChild(annKicker);
        ann.AddChild(Rule());
        ann.AddChild(annTitle);
        ann.AddChild(annSub);
        ann.AddChild(Rule());
        ann.Modulate = Colors.Transparent;
        announce = ann;
        root.AddChild(announce);
    }

    static Control Rule()
    {
        var r = GradientRect([new Color(0.95f, 0.85f, 0.63f, 0), new Color(0.95f, 0.85f, 0.63f, 0.8f), new Color(0.95f, 0.85f, 0.63f, 0)]);
        r.CustomMinimumSize = new Vector2(720, 1);
        r.SizeFlagsHorizontal = Control.SizeFlags.ShrinkCenter;
        return r;
    }

    void BuildBoss()
    {
        float w = 744, x = (1920 - w) / 2;
        bossBox = Box(play, x, 115, w, 110);
        bossBox.Visible = false;
        bossName = Style.Label("", Style.Display, 26, Hex("#ffe0c0"), false, HorizontalAlignment.Center);
        bossName.Size = new Vector2(w, 32);
        bossBox.AddChild(bossName);
        bossTitle = Style.Label("", Style.TextItalic, 16, Style.InkDim, false, HorizontalAlignment.Center);
        bossTitle.Position = new Vector2(0, 32); bossTitle.Size = new Vector2(w, 20);
        bossBox.AddChild(bossTitle);
        var track = new Panel { Position = new Vector2(0, 58), Size = new Vector2(w, 16), ClipContents = true, MouseFilter = Control.MouseFilterEnum.Ignore };
        track.AddThemeStyleboxOverride("panel", Style.Box(Hex("#140808"), Style.GoldDim, 1, 3, 0));
        bossBox.AddChild(track);
        bossTrack = track;
        bossTrail = new ColorRect { Color = Hex("#e8c07a"), Position = new Vector2(1, 1), Size = new Vector2(w - 2, 14), MouseFilter = Control.MouseFilterEnum.Ignore };
        track.AddChild(bossTrail);
        bossFill = new ColorRect { Color = Hex("#b0222a"), Position = new Vector2(1, 1), Size = new Vector2(w - 2, 14), MouseFilter = Control.MouseFilterEnum.Ignore };
        track.AddChild(bossFill);
        bossChannelBox = new Panel { Position = new Vector2(w * 0.2f, 82), Size = new Vector2(w * 0.6f, 20), ClipContents = true, MouseFilter = Control.MouseFilterEnum.Ignore };
        bossChannelBox.AddThemeStyleboxOverride("panel", Style.Box(Hex("#0e0c12"), Hex("#ffcf8a") with { A = 0.6f }, 1, 3, 0));
        bossBox.AddChild(bossChannelBox);
        bossChannelFill = new ColorRect { Color = Hex("#ffb050") with { A = 0.6f }, Size = new Vector2(0, 20), MouseFilter = Control.MouseFilterEnum.Ignore };
        bossChannelBox.AddChild(bossChannelFill);
        bossChannel = Style.Label("", Style.UiHeavy, 13, Colors.White, false, HorizontalAlignment.Center);
        bossChannel.Size = new Vector2(w * 0.6f, 20);
        bossChannel.VerticalAlignment = VerticalAlignment.Center;
        bossChannelBox.AddChild(bossChannel);
    }

    static ShaderMaterial VignetteMaterial() => new()
    {
        Shader = new Shader
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
        },
    };

    /* ------------------------------------------------------------- state -- */

    /// <summary>The play HUD shown or not (the title and creation have none).</summary>
    public void ShowPlay(bool on) => play.Visible = on;

    public void SetBruise(float v) => ((ShaderMaterial)bruise.Material).SetShaderParameter("amount", v);

    static readonly Dictionary<ToastKind, (string Glyph, Color Color)> ToastLook = new()
    {
        [ToastKind.Quest] = ("quest", Hex("#f3d9a0")), [ToastKind.World] = ("eye", Hex("#9ab0d8")), [ToastKind.Relation] = ("talk", Hex("#d89ab0")),
        [ToastKind.Warning] = ("skull", Hex("#ff5a5a")), [ToastKind.Lore] = ("scroll", Hex("#c8b890")), [ToastKind.Level] = ("arcane", Hex("#ffd07a")),
        [ToastKind.Gold] = ("coin", Hex("#f3d9a0")), [ToastKind.Loot] = ("hand", Hex("#d9b56a")),
    };

    /// <summary>The fight, as the HUD shows it (a dozen times a second).</summary>
    public void Frame(Battle? b, double gold, int draughts)
    {
        if (b == null) return;
        combat.Visible = b.Combat;
        var p = b.Player;
        double max = b.MaxHp;
        float k = (float)Math.Clamp(p.Hp / max, 0, 1);
        hpShown = k;
        hpFill.Size = new Vector2(360 * k, 24);
        hpShield.Size = new Vector2(360 * (float)Math.Clamp(p.Shield / max, 0, 1), 7);
        hpText.Text = $"{Math.Ceiling(Math.Max(p.Hp, 0))}  /  {Math.Round(max)}";
        foreach (var c in statuses.GetChildren()) c.QueueFree();
        void Status(string glyph, double left, bool good)
        {
            var col = good ? Hex("#9ad4ff") : Hex("#ff8a6a");
            var chip = Style.Panel(Style.Box(new Color(0.04f, 0.03f, 0.05f, 0.8f), col, 1, 13, 5), Style.H(3, Glyphs.Icon(glyph, 17, col), Style.Label($"{Math.Ceiling(left)}", Style.UiBold, 13, col)));
            chip.MouseFilter = Control.MouseFilterEnum.Ignore;
            statuses.AddChild(chip);
        }
        if (p.BurnT > 0) Status("flame", p.BurnT, false);
        if (p.PoisonT > 0) Status("plague", p.PoisonT, false);
        if (p.SlowT > 0 && p.SlowF < 1) Status("boot", p.SlowT, false);
        if (p.Shield > 0) Status("aegis", p.ShieldT, true);
        if (p.BulwarkT > 0) Status("shield", p.BulwarkT, true);
        if (p.InvisibleT > 0) Status("smoke", p.InvisibleT, true);
        if (b.WorldRate < 1) Status("hourglass", b.WorldRateT, true);
        foreach (var (id, bf) in b.Buffs) Status(id == "warcry" ? "howl" : "arcane", bf.T, true);
        if (!b.Combat) return;

        float e = (float)Math.Clamp(b.EmberXp / Math.Max(1, b.EmberNext), 0, 1);
        emberFill.Size = new Vector2((760 * K - 32) * e, 10);
        if (b.EmberLevel != shownLevel) { shownLevel = b.EmberLevel; emberLevel.Text = shownLevel.ToString(); levelPop = 1; }
        int m = (int)(b.Time / 60), s = (int)(b.Time % 60);
        tallyTime.Text = $"{m}:{s:00}";
        tallyKills.Text = b.KillCount.ToString();
        tallyGold.Text = $"{Math.Floor(gold + b.GoldGained - b.GoldBanked)}";

        var alive = new HashSet<string>();
        int i = 0;
        foreach (var w in b.Weapons)
        {
            alive.Add(w.Id);
            if (!slots.TryGetValue(w.Id, out var slot)) { slot = new WeaponSlot(); slots[w.Id] = slot; weapons.AddChild(slot); }
            weapons.MoveChild(slot, i++);
            bool canEvolve = w.Evolution == null && w.Rank >= Weapons.MaxRank && LevelUp.EarnedBranches(b, w.Id).Count > 0;
            slot.Show(w.Art, ItemViews.SchoolColors[w.School], b.WeaponReady(w), w.Rank, Weapons.MaxRank, w.Evolution != null, canEvolve);
        }
        foreach (var id in slots.Keys.Where(x => !alive.Contains(x)).ToList()) { slots[id].QueueFree(); slots.Remove(id); }
        int empties = weapons.GetChildren().OfType<EmptySlot>().Count(), want = Math.Max(0, 6 - b.Weapons.Count);
        for (int j = empties; j < want; j++) weapons.AddChild(new EmptySlot());
        foreach (var c in weapons.GetChildren().OfType<EmptySlot>().Skip(want)) c.QueueFree();

        foreach (var c in boons.GetChildren()) c.QueueFree();
        foreach (var (id, rank) in b.Boons)
        {
            if (rank <= 0 || Boons.Find(id) is not { } bd) continue;
            var col = Style.RarityOf((int)bd.Rarity);
            var chip = new Panel { CustomMinimumSize = new Vector2(34, 34), MouseFilter = Control.MouseFilterEnum.Ignore };
            chip.AddThemeStyleboxOverride("panel", Style.Box(Hex("#1a1720"), col with { A = 0.55f }, 1, bd.Kind == BoonKind.Blessing ? 6 : 17, 0));
            var gl = Glyphs.Icon(bd.Icon, 20, col);
            gl.Position = new Vector2(7, 7); gl.Size = new Vector2(20, 20);
            chip.AddChild(gl);
            if (bd.Max > 1)
            {
                var r = Style.Label($"{rank}", Style.UiHeavy, 11, Colors.White);
                r.Position = new Vector2(24, 20);
                chip.AddChild(r);
            }
            boons.AddChild(chip);
        }

        int maxDash = (int)Math.Round(b.Stats.Get(Stat.DashCharges));
        if (dashPips.GetChildCount() != maxDash)
        {
            foreach (var c in dashPips.GetChildren()) { dashPips.RemoveChild(c); c.QueueFree(); }
            for (int j = 0; j < maxDash; j++)
            {
                var pip = new Panel { CustomMinimumSize = new Vector2(14, 34), MouseFilter = Control.MouseFilterEnum.Ignore, ClipContents = true };
                pip.AddChild(new ColorRect { Color = new Color(0.47f, 0.67f, 1f, 0.35f), MouseFilter = Control.MouseFilterEnum.Ignore });
                dashPips.AddChild(pip);
            }
        }
        for (int j = 0; j < maxDash; j++)
        {
            bool on = j < p.DashCharges;
            var pip = dashPips.GetChild<Panel>(j);
            pip.AddThemeStyleboxOverride("panel", on ? PipOn : PipOff);
            var fillRect = pip.GetChild<ColorRect>(0);
            float fill = j == p.DashCharges ? (float)Math.Clamp(p.DashRecharge / Abilities.Dash.Recharge, 0, 1) : 0;
            fillRect.Position = new Vector2(0, 34 * (1 - fill));
            fillRect.Size = new Vector2(14, 34 * fill);
        }
        quick.Visible = draughts > 0;
        quickQty.Text = draughts.ToString();
        if (b.Ability is AbilityKind ak)
        {
            var def = Abilities.All[ak];
            string rank = b.ArtRank > 1 ? $"  {Numerals[Math.Min(b.ArtRank, Numerals.Length) - 1]}" : "";
            if (b.Art.EchoT > 0)
            {
                // An echo waits: the art is the way back into it.
                abilityRing.Progress = (float)Math.Clamp(b.Art.EchoT / (b.Has("long_echo") ? 7 : 4), 0, 1);
                abilityRing.Charged = true;
                abilityGlyph.Texture = Glyphs.Texture(def.Icon, 82, Hex("#d8b8ff"));
                abilityCd.Text = "";
                abilityName.Text = "Step back";
                return;
            }
            double ready = 1 - p.AbilityCd / Math.Max(Math.Max(0.01, b.Art.CdFull), p.AbilityCd);
            abilityRing.Progress = (float)Math.Clamp(ready, 0, 1);
            abilityRing.Charged = ready >= 1;
            abilityGlyph.Texture = Glyphs.Texture(def.Icon, 82, ready >= 1 ? Hex("#ffe6b0") : Hex("#8a7f70"));
            abilityCd.Text = ready >= 1 ? "" : p.AbilityCd >= 1 ? $"{Math.Ceiling(p.AbilityCd)}" : $"{p.AbilityCd:0.0}";
            abilityName.Text = def.Name + rank;
        }
    }

    public void ZoneInfo(string name, string? region, int day, TimeOfDay time)
    {
        zoneName.Text = name.ToUpperInvariant();
        foreach (var c in zoneSub.GetChildren()) c.QueueFree();
        zoneSub.AddChild(Glyphs.Icon(time == TimeOfDay.Night ? "moon" : "sun", 15, time == TimeOfDay.Night ? Hex("#b8ccff") : Hex("#ffd890")));
        zoneSub.AddChild(Style.Label($"{time}  ·  Day {day}" + (region != null ? $"  ·  {region}" : ""), Style.Ui, 17, Style.Ink with { A = 0.85f }));
    }

    public void Objectives(List<Tracked> list)
    {
        foreach (var c in objectives.GetChildren()) c.QueueFree();
        foreach (var t in list)
        {
            var head = Style.H(6, Style.Label(t.Title, Style.Display, 18, t.Tone == TrackTone.Tutorial ? Style.Ink : Style.GoldHi));
            head.Alignment = BoxContainer.AlignmentMode.End;
            objectives.AddChild(head);
            foreach (var s in t.Steps)
            {
                var col = s.Done ? Style.InkDim with { A = 0.6f } : s.Optional ? Style.InkDim : Style.Ink;
                var box = new Panel { CustomMinimumSize = new Vector2(10, 10), MouseFilter = Control.MouseFilterEnum.Ignore };
                box.AddThemeStyleboxOverride("panel", Style.Box(s.Done ? Style.Gold : new Color(0, 0, 0, 0.4f), col, 1, s.Optional ? 5 : 1, 0));
                var l = Style.Label(s.Text, s.Optional ? Style.TextItalic : Style.Ui, 16, col, true, HorizontalAlignment.Right);
                l.CustomMinimumSize = new Vector2(370, 0);
                var mark = new CenterContainer { CustomMinimumSize = new Vector2(12, 20), MouseFilter = Control.MouseFilterEnum.Ignore };
                mark.AddChild(box);
                var row = Style.H(7, l, mark);
                row.Alignment = BoxContainer.AlignmentMode.End;
                objectives.AddChild(row);
            }
            objectives.AddChild(Style.Gap(6));
        }
    }

    public void Prompt(PromptView? p)
    {
        promptBox.Visible = p != null;
        if (p == null) return;
        foreach (var c in promptBox.GetChildren()) { promptBox.RemoveChild(c); c.QueueFree(); }
        var key = Style.Panel(Style.Box(Hex("#0d0c10"), Style.GoldDim, 1, 17, 0), Style.Label(p.Key, Style.UiBold, 16, Style.GoldHi, false, HorizontalAlignment.Center));
        key.CustomMinimumSize = new Vector2(34, 34);
        bool locked = p.Locked != null;
        var row = Style.H(11, key, Style.Label(p.Verb, Style.UiHeavy, 18, locked ? Colors.White with { A = 0.55f } : Colors.White),
            Style.Label(p.Target, Style.Display, 18, locked ? Style.GoldHi with { A = 0.55f } : Style.GoldHi));
        if (locked) row.AddChild(Style.Label(p.Locked!, Style.UiBold, 16, Hex("#ff9a80")));
        else if (p.Hint != null) row.AddChild(Style.Label(p.Hint, Style.TextItalic, 16, Style.InkDim));
        promptBox.AddChild(row);
        promptBox.ResetSize();
        var size = promptBox.GetCombinedMinimumSize();
        promptBox.Position = new Vector2((1920 - size.X) / 2, 1080 - 180 - size.Y);
    }

    public void Say(string text, string? who, double seconds)
    {
        sayWho.Text = who?.ToUpperInvariant() ?? "";
        sayWho.Visible = who != null;
        sayText.Text = text;
        sayT = seconds;
    }

    public void Toast(Toast t)
    {
        var (glyph, color) = ToastLook.GetValueOrDefault(t.Kind, ("arcane", Style.Gold));
        if (t.Rarity is int r) color = Style.RarityOf(r);
        var box = new PanelContainer { MouseFilter = Control.MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(408, 0) };
        var s = Style.Box(new Color(0.047f, 0.04f, 0.055f, 0.82f), color, 0, 4, 8);
        s.BorderWidthLeft = 3;
        box.AddThemeStyleboxOverride("panel", s);
        var row = Style.H(10, t.Icon != null ? ItemPhotos.Icon(t.Icon, 40, color) : Glyphs.Icon(glyph, 22, color));
        var words = Style.V(0, Style.Label(t.Text, t.Kind == ToastKind.Quest ? Style.Display : Style.UiBold, 17, t.Kind == ToastKind.Quest ? Style.GoldHi : t.Rarity != null ? color : Hex("#f0e6d2"), true));
        if (!string.IsNullOrEmpty(t.Sub)) words.AddChild(Style.Label(t.Sub, Style.TextItalic, 15, Hex("#b8ab96"), true));
        words.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
        row.AddChild(words);
        box.AddChild(row);
        box.SetMeta("t", 0.0);
        box.SetMeta("life", t.Life ?? 5.0);
        toasts.AddChild(box);
        while (toasts.GetChildCount() > 6) toasts.GetChild(0).Free();
    }

    public void Announce(Announcement a)
    {
        annKicker.Text = a.Kicker?.ToUpperInvariant() ?? "";
        annKicker.Visible = a.Kicker != null;
        annTitle.Text = a.Title.ToUpperInvariant();
        annTitle.AddThemeFontSizeOverride("font_size", a.Kind == "zone" ? 60 : a.Title.Length > 30 ? 31 : a.Title.Length > 20 ? 38 : a.Kind == "story" ? 41 : 50);
        annTitle.AddThemeColorOverride("font_color", a.Kind switch { "danger" => Hex("#ff7a5a"), "boon" => Hex("#ffd46a"), "story" => Hex("#e2dac8"), _ => Hex("#f0c878") });
        annSub.Text = a.Sub ?? "";
        announce.Position = new Vector2(360, 1080 * (a.Kind == "zone" ? 0.16f : 0.2f));
        annT = 0;
        annLife = a.Seconds;
    }

    public void Boss(BossBar? bar)
    {
        bossBox.Visible = bar != null;
        if (bar == null) return;
        bossName.Text = bar.Name.ToUpperInvariant();
        bossTitle.Text = bar.Title;
        float w = 742;
        float k = (float)Math.Clamp(bar.Hp / Math.Max(1, bar.MaxHp), 0, 1);
        bossFill.Size = new Vector2(w * k, 14);
        bossFill.Color = bar.Shielded ? Hex("#8a8a9a") : Hex("#b0222a");
        bossTrail.Size = new Vector2(Math.Max(bossTrail.Size.X - 2, w * k), 14);
        foreach (var c in bossTrack.GetChildren()) if (c.HasMeta("phase")) c.QueueFree();
        foreach (var ph in bar.Phases ?? Array.Empty<double>())
        {
            var mark = new ColorRect { Color = Style.GoldHi, Position = new Vector2(w * (float)ph, 0), Size = new Vector2(2, 16), MouseFilter = Control.MouseFilterEnum.Ignore };
            mark.SetMeta("phase", true);
            bossTrack.AddChild(mark);
        }
        bossChannelBox.Visible = bar.Channel != null;
        if (bar.Channel is var (label, prog))
        {
            bossChannelFill.Size = new Vector2(bossChannelBox.Size.X * (float)Math.Clamp(prog, 0, 1), 20);
            bossChannel.Text = label;
        }
    }

    public void Hint(Hint? h)
    {
        hintBox.Visible = h != null;
        foreach (var c in hintBox.GetChildren()) { hintBox.RemoveChild(c); c.QueueFree(); }
        if (h == null) return;
        var ink = Style.ParchmentInk;
        var v = Style.V(5, Style.H(6, Glyphs.Icon("scroll", 17, Hex("#6a3a14")), Style.Label(h.Title.ToUpperInvariant(), Style.Display, 15, Hex("#6a3a14"), false, HorizontalAlignment.Left, false)),
            Style.Label(h.Text, Style.Text, 19, ink, true, HorizontalAlignment.Left, false));
        // A known width, so the words wrap before the box is measured.
        v.GetChild<Control>(1).CustomMinimumSize = new Vector2(396 - 28, 0);
        if (h.Keys.Count > 0) v.AddChild(Style.H(6, h.Keys.Select(Style.Key).ToArray()));
        hintBox.AddChild(v);
        hintBox.OffsetTop = hintBox.OffsetBottom;
    }

    /// <summary>Fade to black (1) or back (0) over some seconds, with words over the black.</summary>
    public void Fade(float to, double seconds, string? caption = null, string? sub = null)
    {
        fadeFrom = fade.Color.A;
        fadeTo = to;
        fadeT = 0;
        fadeDur = Math.Max(0.01, seconds);
        if (to > 0.5f) { fadeCaption.Text = caption ?? ""; fadeSub.Text = sub ?? ""; }
    }

    /* ------------------------------------------------- the draft, a talk -- */

    public void Draft(DraftView? d)
    {
        draft?.QueueFree();
        draft = null;
        if (d == null) return;
        draft = new DraftPanel(d);
        root.AddChild(draft);
    }

    public void Dialogue(DialogueView? d)
    {
        talk?.QueueFree();
        talk = null;
        play.Modulate = d == null ? Colors.White : new Color(1, 1, 1, 0.35f);
        if (d == null) return;
        talk = new TalkPanel(d);
        root.AddChild(talk);
    }

    /// <summary>A key for the draft or the conversation, if one is up.</summary>
    public bool Key(Act a) => draft?.Key(a) ?? talk?.Key(a) ?? false;

    /* ------------------------------------------------------------- frame -- */

    public override void _Process(double delta)
    {
        float dt = (float)delta;
        if (sayT > 0)
        {
            sayT -= delta;
            subtitle.Modulate = Colors.White with { A = (float)Math.Clamp(sayT / 0.6, 0, 1) };
        }
        else subtitle.Modulate = Colors.Transparent;
        if (annT < annLife)
        {
            annT += delta;
            float a = (float)Math.Clamp(Math.Min(annT / (annLife * 0.1), (annLife - annT) / (annLife * 0.2)), 0, 1);
            announce.Modulate = Colors.White with { A = a };
        }
        else announce.Modulate = Colors.Transparent;
        // Nothing big over a choice being made.
        if (draft != null || talk != null) { announce.Modulate = Colors.Transparent; subtitle.Modulate = Colors.Transparent; }
        foreach (var c in toasts.GetChildren())
        {
            if (c is not Control box) continue;
            double t = (double)box.GetMeta("t") + delta, life = (double)box.GetMeta("life");
            box.SetMeta("t", t);
            float k = (float)(t / life);
            box.Modulate = Colors.White with { A = k < 0.05f ? k / 0.05f : k > 0.88f ? (1 - k) / 0.12f : 1 };
            if (t >= life) box.QueueFree();
        }
        // The trail behind health catches up after a moment.
        float trail = hpTrail.Size.X / 360;
        if (trail > hpShown) { trailWait += dt; trailShown = trailWait > 0.35f ? Mathf.MoveToward(trail, hpShown, dt * 1.6f) : trail; }
        else { trailWait = 0; trailShown = hpShown; }
        hpTrail.Size = new Vector2(360 * trailShown, 24);
        bool low = hpShown < 0.35f && combat.Visible;
        float now = Time.GetTicksMsec() / 1000f;
        float beat = low ? 1 + 0.12f * Mathf.Max(0, Mathf.Sin(now * 7)) : 1;
        heart.Scale = new Vector2(beat, beat);
        hpLow.Color = new Color(1, 0.24f, 0.24f, low ? 0.15f + 0.15f * Mathf.Sin(now * 7) : 0);
        if (levelPop > 0) { levelPop = Math.Max(0, levelPop - delta / 0.6); float sc = 1 + 0.9f * (float)(levelPop * levelPop); emberLevel.Scale = new Vector2(sc, sc); }
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

/// <summary>A weapon on the HUD: its glyph in its school's colour, a shade
/// that sweeps off as it readies, a flash when it fires, rank as pips.</summary>
public partial class WeaponSlot : Panel
{
    readonly TextureRect art;
    readonly ColorRect sweep;
    readonly HBoxContainer pips;
    double lastReady = 1, flash;
    string key = "";

    public WeaponSlot()
    {
        CustomMinimumSize = new Vector2(67, 67);
        MouseFilter = MouseFilterEnum.Ignore;
        art = new TextureRect { Position = new Vector2(15, 15), Size = new Vector2(37, 37), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered, MouseFilter = MouseFilterEnum.Ignore };
        AddChild(art);
        sweep = new ColorRect { Color = new Color(0.016f, 0.012f, 0.03f, 0.62f), Position = new Vector2(1, 1), Size = new Vector2(65, 0), MouseFilter = MouseFilterEnum.Ignore };
        AddChild(sweep);
        pips = Style.H(3);
        pips.Alignment = BoxContainer.AlignmentMode.Center;
        pips.Position = new Vector2(0, 62);
        pips.Size = new Vector2(67, 7);
        AddChild(pips);
    }

    public void Show(string glyph, Color school, double ready, int rank, int max, bool evolved, bool canEvolve)
    {
        var k = $"{glyph}|{school.ToHtml()}|{rank}|{evolved}|{canEvolve}";
        if (k != key)
        {
            key = k;
            art.Texture = Glyphs.Texture(glyph, 74, school);
            foreach (var c in pips.GetChildren()) c.QueueFree();
            for (int i = 0; i < max; i++)
                pips.AddChild(new ColorRect { Color = i < rank ? school : new Color("#15121a"), CustomMinimumSize = new Vector2(5, 5), MouseFilter = MouseFilterEnum.Ignore });
            AddThemeStyleboxOverride("panel", Style.Box(new Color(0.1f, 0.09f, 0.12f).Lerp(school, 0.1f), evolved ? Style.Gold : canEvolve ? Style.GoldHi : Style.Line, evolved || canEvolve ? 2 : 1, 7, 0));
        }
        if (ready < lastReady - 0.4) flash = 1;
        lastReady = ready;
        sweep.Size = new Vector2(65, ready < 0.98 ? 65 * (float)(1 - ready) : 0);
        art.Modulate = ready >= 0.98 ? new Color(1.3f, 1.3f, 1.3f) : Colors.White;
        flash = Math.Max(0, flash - 0.05);
        SelfModulate = Colors.White.Lerp(new Color(1.6f, 1.4f, 1.1f), (float)flash);
    }
}

/// <summary>An empty place for a weapon yet to come.</summary>
public partial class EmptySlot : Panel
{
    public EmptySlot()
    {
        CustomMinimumSize = new Vector2(67, 67);
        MouseFilter = MouseFilterEnum.Ignore;
        AddThemeStyleboxOverride("panel", Style.Box(new Color(0.08f, 0.07f, 0.09f, 0.55f), Style.Line with { A = 0.12f }, 1, 7, 0));
    }
}

/// <summary>The skill's ring: gold round as far as it has readied.</summary>
public partial class Ring : Control
{
    float progress = 1;
    bool ready = true;
    public float Progress { get => progress; set { if (Math.Abs(progress - value) > 0.002f) { progress = value; QueueRedraw(); } } }
    public bool Charged { get => ready; set { if (ready != value) { ready = value; QueueRedraw(); } } }

    public override void _Draw()
    {
        var c = Size / 2;
        float r = Size.X / 2 - 4;
        DrawCircle(c, r + 3, new Color("#0e0c11"));
        DrawArc(c, r, 0, Mathf.Tau, 64, new Color(1, 1, 1, 0.06f), 5, true);
        DrawArc(c, r, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * progress, 64, ready ? new Color("#f3d9a0") : new Color("#d9b56a"), 5, true);
        DrawCircle(c, r - 6, ready ? new Color("#2a1a10") : new Color("#16131a"));
    }
}
