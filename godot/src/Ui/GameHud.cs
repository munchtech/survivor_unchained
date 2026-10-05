using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>What the corner map shows: the zone's drawing, the fog, the marks, the survivor.</summary>
public sealed record MinimapView(string Zone, Texture2D Drawing, float Extent, string Seen, int N, List<MiniMark> Marks, double X, double Z, double Facing, bool Night);

/// <summary>What is near and can be used, as the prompt shows it.</summary>
/// <summary>A prompt on the screen; `For` is the action whose pad button it shows (the use key's, mostly).</summary>
public sealed record PromptView(string Key, string Verb, string Target, string? Hint, string? Locked, Act For = Act.Interact);

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
    TextureRect emberFill = null!, growFill = null!;
    Label emberLevel = null!, tallyTime = null!, tallyKills = null!, tallyGold = null!;
    int shownLevel;
    bool shownEmber = true;
    double levelPop;
    // Health as a globe at the console's left end (docs/UI_DESIGN.md, "HUD").
    Globe globe = null!;
    HBoxContainer statuses = null!;
    Control heart = null!;
    /// <summary>The console's span: as wide as the skills it holds (six places by night, what is carried by day),
    /// the globe at its left end, the art's ring at its right.</summary>
    float consoleX = 600, consoleW = 720;
    int consolePlaces;
    Control consolePlate = null!, arsenal = null!, hands = null!;
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
    ColorRect fade = null!, pull = null!;
    ShaderMaterial pullMat = null!;
    double pullT = -1, pullDur = 1;
    Label fadeCaption = null!, fadeSub = null!;
    double fadeFrom = 1, fadeTo = 1, fadeT = 1, fadeDur = 1;
    DraftPanel? draft;
    TalkPanel? talk;
    public float FadeAmount => fade.Color.A;
    // What changes with the device in hand: the hands' keys, the prompt, the hint.
    readonly List<(Act Act, HBoxContainer Row)> handKeys = new();
    PromptView? promptView;
    Hint? hintView;
    // The bar's word (ember or experience) and its bright leading edge.
    Label barWord = null!;
    ColorRect barTip = null!;
    Control killsChip = null!;
    // The survivor's own health, drawn under them in a night's fight.
    Control under = null!;
    ColorRect underFill = null!, underShield = null!;
    float underK = 1, underShieldK, underAlpha;
    bool underWanted;
    // The corner: the minimap over the place's name and the objectives.
    Minimap minimap = null!;
    VBoxContainer corner = null!;
    // Discoveries in a burst become one toast that grows.
    (PanelContainer Box, ToastKind Kind, List<string> Names, double At)? lastToast;
    // The bar eased every frame toward its true value (docs/feel S-06): shown, wanted, the level's flash.
    float barShown, barWant, barFlash;
    bool barEmber = true;
    ColorRect barGlow = null!;
    double killPop;
    int killsShown;
    // What matters off the screen; where the prompt's thing is on it; the arena's clock and its word.
    EdgeMarks edges = null!;
    Vector2? promptAnchor;
    Label tallyWord = null!;
    double? arenaLeft;

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
        BuildBackings();
        BuildUnder();
        edges = new EdgeMarks();
        Style.Fill(edges);
        combat.AddChild(edges);
        BuildEmber();
        BuildVitals();
        BuildArsenal();
        BuildHands();
        BuildCorner();
        BuildEdges();
        BuildBoss();
        var top = new CanvasLayer { Layer = 30 };
        AddChild(top);
        pullMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/pull.gdshader") };
        pull = new ColorRect { Material = pullMat, Visible = false, MouseFilter = Control.MouseFilterEnum.Ignore };
        Style.Fill(pull);
        top.AddChild(pull);
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

    /// <summary>A round medallion rimmed in gold (the ember's, the heart's);
    /// painted (hud/NAME.png, drawn larger than the medallion, centred on it) when there is art.</summary>
    /// <summary>A painted casing laid over a bar (bars/casing.png, casing_boss.png): forged iron
    /// round the groove, reaching a little past it, its middle open so the fill shows. Added
    /// after the bar so it sits over the fill's edge; nothing when there is no art.</summary>
    static void Casing(Control parent, Control bar, string id)
    {
        if (!UiArt.Has(id)) return;
        var c = new Panel { Position = bar.Position, Size = bar.Size, MouseFilter = Control.MouseFilterEnum.Ignore };
        c.AddThemeStyleboxOverride("panel", UiArt.Frame(id, new StyleBoxEmpty()));
        parent.AddChild(c);
    }

    static Panel Medal(Control parent, Vector2 at, float size, Color inner, string? art = null)
    {
        var p = new Panel { Position = at, Size = new Vector2(size, size), MouseFilter = Control.MouseFilterEnum.Ignore };
        var s = Style.Box(inner, Style.GoldDim, 3, (int)(size / 2), 0);
        s.ShadowColor = new Color(1f, 0.55f, 0.2f, 0.35f);
        s.ShadowSize = 10;
        if (art != null && UiArt.Art($"hud/{art}.png") is { } tex)
        {
            p.AddThemeStyleboxOverride("panel", new StyleBoxEmpty());
            var r = new TextureRect { Texture = tex, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, MouseFilter = Control.MouseFilterEnum.Ignore, ShowBehindParent = true };
            r.Size = tex.GetSize();
            r.Position = (new Vector2(size, size) - r.Size) / 2;
            p.AddChild(r);
        }
        else p.AddThemeStyleboxOverride("panel", s);
        parent.AddChild(p);
        return p;
    }

    /// <summary>A bar's fill: painted (bars/NAME.png, a strip that tiles along the bar, so it
    /// is never squashed as the bar fills) or the drawn gradient.</summary>
    static TextureRect Fill(string art, Color[] colors, float[] stops, bool vertical = false)
    {
        var r = GradientRect(colors, stops, vertical);
        if (UiArt.Art($"bars/{art}.png") is { } tex) { r.Texture = tex; r.StretchMode = TextureRect.StretchModeEnum.Tile; }
        return r;
    }

    void BuildEmber()
    {
        float w = 760 * K, x = (1920 - w) / 2;
        var track = new Panel { Position = new Vector2(x + 30, 23), Size = new Vector2(w - 30, 12), MouseFilter = Control.MouseFilterEnum.Ignore, ClipContents = true };
        track.AddThemeStyleboxOverride("panel", UiArt.Frame("bar_track", Style.Box(Hex("#120c0a"), new Color(0.85f, 0.71f, 0.42f, 0.28f), 1, 5, 0)));
        combat.AddChild(track);
        Casing(combat, track, "bar_casing");
        emberFill = Fill("ember_fill", [Hex("#6a1e04"), Hex("#c24a0a"), Hex("#ff8a2a"), Hex("#ffd070")], [0, 0.45f, 0.85f, 1]);
        emberFill.Position = new Vector2(1, 1);
        emberFill.Size = new Vector2(0, 10);
        track.AddChild(emberFill);
        // By day the same bar is the survivor's own experience, cooler and slower.
        growFill = Fill("experience_fill", [Hex("#16222e"), Hex("#34587a"), Hex("#86b0d8"), Hex("#e6f2ff")], [0, 0.45f, 0.85f, 1]);
        growFill.Position = new Vector2(1, 1);
        growFill.Size = new Vector2(0, 10);
        track.AddChild(growFill);
        for (int i = 1; i < 10; i++) track.AddChild(new ColorRect { Color = new Color(0, 0, 0, 0.55f), Position = new Vector2((w - 30) * i / 10f, 0), Size = new Vector2(1, 12), MouseFilter = Control.MouseFilterEnum.Ignore });
        // The leading edge burns brighter as the next level nears (the goal in sight).
        barTip = new ColorRect { Color = Colors.White, Size = new Vector2(4, 10), Position = new Vector2(1, 1), MouseFilter = Control.MouseFilterEnum.Ignore };
        track.AddChild(barTip);
        // Near the level the whole bar breathes.
        barGlow = new ColorRect { Color = Style.EmberHi with { A = 0 }, Position = new Vector2(1, 1), Size = new Vector2(0, 10), MouseFilter = Control.MouseFilterEnum.Ignore };
        track.AddChild(barGlow);
        // What the bar is, in a word under its start: ember by night, experience by day.
        barWord = Style.Label("EMBER", Style.UiHeavy, 13, Style.Ember with { A = 0.85f });
        barWord.Position = new Vector2(x + 52, 37);
        combat.AddChild(barWord);
        var medal = Medal(combat, new Vector2(x, 6), 46, Hex("#3a2210"), "medal_level");
        emberLevel = Style.Label("1", Style.Display, 20, Style.EmberHi, false, HorizontalAlignment.Center);
        emberLevel.Size = new Vector2(46, 46);
        emberLevel.PivotOffset = new Vector2(23, 23);
        emberLevel.VerticalAlignment = VerticalAlignment.Center;
        medal.AddChild(emberLevel);
        tallyTime = Style.Label("0:00", Style.Display, 24, Hex("#efe3c8"), false, HorizontalAlignment.Center);
        tallyTime.Position = new Vector2(860, 50); tallyTime.Size = new Vector2(200, 28);
        combat.AddChild(tallyTime);
        var row = Style.H(16);
        tallyKills = Style.Label("0", Style.UiBold, 17, Hex("#cfc3ad"));
        tallyGold = Style.Label("0", Style.UiBold, 17, Style.GoldHi);
        killsChip = Style.H(4, Glyphs.Icon("skull", 17, Hex("#cfc3ad")), tallyKills);
        row.AddChild(killsChip);
        row.AddChild(Style.H(4, Glyphs.Icon("coin", 17, Style.GoldHi), tallyGold));
        row.Alignment = BoxContainer.AlignmentMode.Center;
        row.Position = new Vector2(860, 80); row.Size = new Vector2(200, 20);
        combat.AddChild(row);
        // Under the clock in an arena: what it counts to.
        tallyWord = Style.Label("", Style.UiHeavy, Style.Badge, Style.Ember, false, HorizontalAlignment.Center);
        tallyWord.Position = new Vector2(760, 104); tallyWord.Size = new Vector2(400, 18);
        combat.AddChild(tallyWord);
    }

    void BuildVitals()
    {
        // The console: a forged plate along the foot, under the skills, the globe and the ring at its ends.
        var plate = new Panel { Position = new Vector2(consoleX, 1080 - 98), Size = new Vector2(consoleW, 130), MouseFilter = Control.MouseFilterEnum.Ignore };
        plate.AddThemeStyleboxOverride("panel", UiArt.Frame("console", OrnateBox.Make(OrnateBox.Kind.Plate, 0)));
        combat.AddChild(plate);
        consolePlate = plate;
        globe = new Globe(66) { Position = new Vector2(consoleX - 150, 1080 - 156) };
        globe.PivotOffset = globe.Size / 2;
        heart = globe;
        play.AddChild(globe);
        // What is on you (burning, shielded, quickened), over the globe.
        statuses = Style.H(6);
        statuses.Position = new Vector2(consoleX - 150, 1080 - 156 - 40);
        play.AddChild(statuses);
    }

    void BuildArsenal()
    {
        var col = Style.V(12);
        col.Alignment = BoxContainer.AlignmentMode.End;
        col.Position = new Vector2(consoleX, 1080 - 14 - 150);
        col.Size = new Vector2(consoleW, 150);
        arsenal = col;
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
        // The art's ring at the console's right end, the draught and the dash beside it.
        var h = Style.H(22);
        h.Alignment = BoxContainer.AlignmentMode.Begin;
        h.Position = new Vector2(consoleX + consoleW + 14, 1080 - 14 - 150);
        h.Size = new Vector2(460, 150);
        combat.AddChild(h);
        hands = h;
        Control Hand(Control art, Act key, string label, out Label name)
        {
            var v = Style.V(8);
            v.Alignment = BoxContainer.AlignmentMode.End;
            var c = new CenterContainer { MouseFilter = Control.MouseFilterEnum.Ignore };
            c.AddChild(art);
            v.AddChild(c);
            name = Style.Label(label, Style.UiBold, Style.Caption, Style.Ink);
            var row = Style.H(5, Style.Prompt(key), name);
            row.Alignment = BoxContainer.AlignmentMode.Center;
            handKeys.Add((key, row));
            v.AddChild(row);
            h.AddChild(v);
            return v;
        }
        const float R = 116;
        var ab = new Control { CustomMinimumSize = new Vector2(R, R), MouseFilter = Control.MouseFilterEnum.Ignore };
        abilityRing = new Ring { Size = new Vector2(R, R), MouseFilter = Control.MouseFilterEnum.Ignore };
        ab.AddChild(abilityRing);
        // The art's ring painted over the drawn one (hud/ring_art.png, a ring with an empty middle).
        if (UiArt.Art("hud/ring_art.png") is { } ringArt)
        {
            var rr = new TextureRect { Texture = ringArt, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, MouseFilter = Control.MouseFilterEnum.Ignore, Size = ringArt.GetSize() * (R / 89f) };
            rr.Position = (new Vector2(R, R) - rr.Size) / 2;
            ab.AddChild(rr);
        }
        abilityGlyph = Glyphs.Icon("shield", 54);
        abilityGlyph.Position = new Vector2((R - 54) / 2, (R - 54) / 2); abilityGlyph.Size = new Vector2(54, 54);
        ab.AddChild(abilityGlyph);
        abilityCd = Style.Label("", Style.Display, 28, Colors.White, false, HorizontalAlignment.Center);
        abilityCd.Size = new Vector2(R, R);
        abilityCd.VerticalAlignment = VerticalAlignment.Center;
        ab.AddChild(abilityCd);
        Hand(ab, Act.Ability, "", out abilityName);
        var q = new Panel { CustomMinimumSize = new Vector2(60, 60), MouseFilter = Control.MouseFilterEnum.Ignore };
        q.AddThemeStyleboxOverride("panel", OrnateBox.Make(OrnateBox.Kind.Slab, 0));
        var qi = ItemPhotos.Icon("potion", 50, Hex("#ff8a80"));
        qi.Position = new Vector2(5, 3); qi.Size = new Vector2(50, 50);
        q.AddChild(qi);
        quickQty = Style.Label("", Style.UiHeavy, 14, Colors.White);
        quickQty.Position = new Vector2(44, 40);
        q.AddChild(quickQty);
        quick = Hand(q, Act.Ultimate, "Draught", out _);
        dashPips = Style.H(5);
        Hand(dashPips, Act.Dash, "Dash", out _);
    }

    static readonly string[] Numerals = ["I", "II", "III", "IV", "V"];

    /// <summary>Soft shade behind the top-right corner and along the bottom, so
    /// the HUD's words read over bright cobbles as well as night grass.</summary>
    void BuildBackings()
    {
        TextureRect Shade(Vector2 from, Vector2 to, float alpha, bool radial)
        {
            var g = new Gradient { Colors = new[] { new Color(0.02f, 0.015f, 0.025f, alpha), new Color(0.02f, 0.015f, 0.025f, 0) }, Offsets = new[] { 0f, 1f } };
            return new TextureRect
            {
                Texture = new GradientTexture2D { Gradient = g, Width = 128, Height = 128, Fill = radial ? GradientTexture2D.FillEnum.Radial : GradientTexture2D.FillEnum.Linear, FillFrom = from, FillTo = to },
                ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = Control.MouseFilterEnum.Ignore,
            };
        }
        var corner = Shade(new Vector2(1, 0), new Vector2(0.25f, 0.9f), 0.5f, true);
        corner.Position = new Vector2(1920 - 760, 0);
        corner.Size = new Vector2(760, 520);
        play.AddChild(corner);
        var foot = Shade(new Vector2(0.5f, 1), new Vector2(0.5f, 0), 0.42f, false);
        foot.Position = new Vector2(0, 1080 - 190);
        foot.Size = new Vector2(1920, 190);
        play.AddChild(foot);
    }

    /// <summary>The survivor's health under their feet, where the eye already is
    /// in a night's fight (the survivors-likes' answer: docs/UI_RESEARCH.md 4.1).</summary>
    void BuildUnder()
    {
        under = new Control { Size = new Vector2(76, 9), MouseFilter = Control.MouseFilterEnum.Ignore, Modulate = Colors.Transparent };
        var back = new Panel { Size = new Vector2(76, 9), MouseFilter = Control.MouseFilterEnum.Ignore, ClipContents = true };
        back.AddThemeStyleboxOverride("panel", Style.Box(new Color(0.05f, 0.02f, 0.02f, 0.85f), new Color(0, 0, 0, 0.9f), 1, 3, 0));
        under.AddChild(back);
        underFill = new ColorRect { Color = Hex("#e8383a"), Position = new Vector2(1, 1), Size = new Vector2(74, 7), MouseFilter = Control.MouseFilterEnum.Ignore };
        back.AddChild(underFill);
        underShield = new ColorRect { Color = Style.Shield, Position = new Vector2(1, 1), Size = new Vector2(0, 3), MouseFilter = Control.MouseFilterEnum.Ignore };
        back.AddChild(underShield);
        combat.AddChild(under);
    }

    void BuildCorner()
    {
        minimap = new Minimap { Position = new Vector2(1920 - 36 - Minimap.Diameter, 28), Visible = false };
        play.AddChild(minimap);
        var c = Style.V(3);
        corner = c;
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
        hintBox = Style.Panel(UiArt.Frame("hint", Style.Box(Hex("#e6d6b0"), new Color(0.35f, 0.24f, 0.08f, 0.45f), 1, 4, 14)));
        // Pinned by its foot above the vitals; grows upward with its words.
        hintBox.AnchorTop = hintBox.AnchorBottom = 1;
        hintBox.OffsetLeft = 34; hintBox.OffsetBottom = -196;
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
        promptBox = Style.Panel(UiArt.Frame("prompt", Style.Box(new Color(0.08f, 0.07f, 0.09f, 0.92f), Style.Line, 1, 24, 10)));
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
        track.AddThemeStyleboxOverride("panel", UiArt.Frame("bar_track_boss", Style.Box(Hex("#140808"), Style.GoldDim, 1, 3, 0)));
        bossBox.AddChild(track);
        Casing(bossBox, track, "bar_casing_boss");
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
    /// <param name="level">The survivor's own level, and how far into it (shown when the ember is out).</param>
    public void Frame(Battle? b, double gold, int draughts, (int Level, double K) level = default)
    {
        if (b == null) return;
        combat.Visible = b.Combat;
        // In a fight the globe is the console's left end; at peace, with no console, it keeps to the corner.
        var at = b.Combat ? new Vector2(consoleX - 150, 1080 - 156) : new Vector2(30, 1080 - 30 - globe.Size.Y);
        if (globe.Position != at) { globe.Position = at; statuses.Position = at + new Vector2(0, -40); }
        var p = b.Player;
        double max = b.MaxHp;
        float k = (float)Math.Clamp(p.Hp / max, 0, 1);
        hpShown = k;
        globe.Level = k;
        globe.Shield = (float)Math.Clamp(p.Shield / max, 0, 1);
        double hpNum = Math.Ceiling(Math.Max(p.Hp, 0));
        if (hpNum != globeNum) { globeNum = hpNum; globe.Number = $"{hpNum}"; }
        globe.Changed();
        statusWant.Clear();
        statusLeft.Clear();
        void Status(string glyph, double left, bool good) { statusWant.Add((glyph, good)); statusLeft.Add(left); }
        if (p.BurnT > 0) Status("flame", p.BurnT, false);
        if (p.PoisonT > 0) Status("plague", p.PoisonT, false);
        if (p.SlowT > 0 && p.SlowF < 1) Status("boot", p.SlowT, false);
        if (p.Shield > 0) Status("aegis", p.ShieldT, true);
        if (p.BulwarkT > 0) Status("shield", p.BulwarkT, true);
        if (p.InvisibleT > 0) Status("smoke", p.InvisibleT, true);
        if (b.WorldRate < 1) Status("hourglass", b.WorldRateT, true);
        foreach (var (id, bf) in b.Buffs) Status(id == "warcry" ? "howl" : "arcane", bf.T, true);
        Statuses();
        underWanted = false;
        if (!b.Combat) return;

        // The ember while it burns; by day, the survivor's own growing.
        bool ember = b.EmberOn;
        float e = (float)Math.Clamp(ember ? b.EmberXp / Math.Max(1, b.EmberNext) : level.K, 0, 1);
        emberFill.Visible = ember;
        growFill.Visible = !ember;
        // The fill is eased every frame (_Process); a new level fills it, flashes, and drains to what carried over.
        if (ember != barEmber) { barEmber = ember; barShown = e; }
        barWant = e;
        barWord.Text = ember ? "EMBER" : "EXPERIENCE";
        barWord.AddThemeColorOverride("font_color", (ember ? Style.Ember : Style.Day) with { A = 0.85f });
        // The fight's clock and its count belong to the night; by day they would only be noise.
        tallyTime.Visible = ember;
        killsChip.Visible = ember;
        underK = k;
        underShieldK = (float)Math.Clamp(p.Shield / max, 0, 1);
        underWanted = ember && p.Alive && Settings.Current.UnderBar;
        int lv = ember ? b.EmberLevel : Math.Max(1, level.Level);
        if (lv != shownLevel || ember != shownEmber)
        {
            if (lv > shownLevel && ember == shownEmber) { levelPop = 1; barShown = 1; barFlash = 1; }
            shownLevel = lv; shownEmber = ember;
            emberLevel.Text = lv.ToString();
            emberLevel.AddThemeColorOverride("font_color", ember ? Style.EmberHi : Hex("#d8ecff"));
        }
        // In an arena the clock counts down to what rules it; after, how long past the half hour.
        double shown = arenaLeft is double left && left > 0 ? left : arenaLeft is double past ? -past : b.Time;
        int m = (int)(shown / 60), s = (int)(shown % 60);
        tallyTime.Text = arenaLeft is double l2 && l2 <= 0 ? $"+{m}:{s:00}" : $"{m}:{s:00}";
        tallyTime.AddThemeColorOverride("font_color", arenaLeft is double l3 && l3 > 0 && l3 < 60 ? Style.EmberHi : Hex("#efe3c8"));
        tallyKills.Text = b.KillCount.ToString();
        // The count pops when it climbs, at most ten times a second.
        if (b.KillCount > killsShown && killPop <= 0.05) killPop = 0.15;
        killsShown = b.KillCount;
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
        // At night the empty places promise six; by day there are only what is carried, and the console fits them.
        int empties = weapons.GetChildren().OfType<EmptySlot>().Count(), want = ember ? Math.Max(0, 6 - b.Weapons.Count) : 0;
        int places = Math.Max(2, b.Weapons.Count + want);
        if (places != consolePlaces)
        {
            consolePlaces = places;
            consoleW = Math.Max(300, places * 77 + 70);
            consoleX = (1920 - consoleW) / 2;
            consolePlate.Position = new Vector2(consoleX, 1080 - 98);
            consolePlate.Size = new Vector2(consoleW, 130);
            arsenal.Position = new Vector2(consoleX, 1080 - 14 - 150);
            arsenal.Size = new Vector2(consoleW, 150);
            hands.Position = new Vector2(consoleX + consoleW + 14, 1080 - 14 - 150);
            globe.Position = new Vector2(consoleX - 150, 1080 - 156);
            statuses.Position = globe.Position + new Vector2(0, -40);
        }
        for (int j = empties; j < want; j++) weapons.AddChild(new EmptySlot());
        foreach (var c in weapons.GetChildren().OfType<EmptySlot>().Skip(want)) c.QueueFree();

        boonWant.Clear();
        foreach (var (id, rank) in b.Boons)
            if (rank > 0 && Boons.Find(id) != null) boonWant.Add((id, rank));
        if (!Same(boonWant, boonHave))
        {
            boonHave.Clear();
            boonHave.AddRange(boonWant);
            foreach (var c in boons.GetChildren()) c.QueueFree();
            foreach (var (id, rank) in boonWant) boons.AddChild(BoonChip(Boons.Find(id)!, rank));
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

    // The chips over the globe and in the boons' row, as last built. They were
    // all remade on every call (twelve a second); now only when which there are
    // changes, a countdown set in place, so nothing shifts in between.
    readonly List<(string Glyph, bool Good)> statusWant = new(), statusHave = new();
    readonly List<double> statusLeft = new(), statusShown = new();
    readonly List<Label> statusText = new();
    readonly List<(string Id, int Rank)> boonWant = new(), boonHave = new();
    double globeNum = double.NaN;

    static bool Same<T>(List<T> a, List<T> b)
    {
        if (a.Count != b.Count) return false;
        var eq = EqualityComparer<T>.Default;
        for (int i = 0; i < a.Count; i++) if (!eq.Equals(a[i], b[i])) return false;
        return true;
    }

    /// <summary>A status's countdown as shown: whole seconds, none for what lasts.</summary>
    static double Countdown(double left) => left > 600 ? -1 : Math.Ceiling(left);

    void Statuses()
    {
        if (Same(statusWant, statusHave))
        {
            for (int i = 0; i < statusText.Count; i++)
            {
                double n = Countdown(statusLeft[i]);
                if (n == statusShown[i]) continue;
                statusShown[i] = n;
                statusText[i].Text = n < 0 ? "" : $"{n}";
            }
            return;
        }
        statusHave.Clear();
        statusHave.AddRange(statusWant);
        statusText.Clear();
        statusShown.Clear();
        foreach (var c in statuses.GetChildren()) c.QueueFree();
        for (int i = 0; i < statusWant.Count; i++)
        {
            var (glyph, good) = statusWant[i];
            double n = Countdown(statusLeft[i]);
            var col = good ? Hex("#9ad4ff") : Hex("#ff8a6a");
            var text = Style.Label(n < 0 ? "" : $"{n}", Style.UiBold, Style.Badge, col);
            var chip = Style.Panel(UiArt.Frame("chip", Style.Box(new Color(0.04f, 0.03f, 0.05f, 0.8f), col, 1, 13, 5)), Style.H(3, Glyphs.Icon(glyph, 17, col), text));
            chip.MouseFilter = Control.MouseFilterEnum.Ignore;
            statuses.AddChild(chip);
            statusText.Add(text);
            statusShown.Add(n);
        }
    }

    static Panel BoonChip(BoonDef bd, int rank)
    {
        var col = Style.RarityOf((int)bd.Rarity);
        var chip = new Panel { CustomMinimumSize = new Vector2(34, 34), MouseFilter = Control.MouseFilterEnum.Ignore };
        chip.AddThemeStyleboxOverride("panel", UiArt.Frame("chip", Style.Box(Hex("#1a1720"), col with { A = 0.55f }, 1, bd.Kind == BoonKind.Blessing ? 6 : 17, 0)));
        var gl = Glyphs.Icon(bd.Icon, 20, col);
        gl.Position = new Vector2(7, 7); gl.Size = new Vector2(20, 20);
        chip.AddChild(gl);
        if (bd.Max > 1)
        {
            var r = Style.Label($"{rank}", Style.UiHeavy, Style.Badge, Colors.White);
            r.Position = new Vector2(23, 17);
            chip.AddChild(r);
        }
        return chip;
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
        promptView = p;
        promptBox.Visible = p != null;
        if (p == null) return;
        foreach (var c in promptBox.GetChildren()) { promptBox.RemoveChild(c); c.QueueFree(); }
        // The key as the device in hand has it: a keycap, or the pad's button.
        var key = Controls.Instance.UsingPad ? Style.PadButton(Controls.Instance.PadLabels(p.For).FirstOrDefault() ?? "B")
            : Style.Panel(Style.Box(Hex("#0d0c10"), Style.GoldDim, 1, 17, 0), Style.Label(p.Key, Style.UiBold, 16, Style.GoldHi, false, HorizontalAlignment.Center));
        key.CustomMinimumSize = new Vector2(34, 34);
        bool locked = p.Locked != null;
        var row = Style.H(11, key, Style.Label(p.Verb, Style.UiHeavy, 18, locked ? Colors.White with { A = 0.55f } : Colors.White),
            Style.Label(p.Target, Style.Display, 18, locked ? Style.GoldHi with { A = 0.55f } : Style.GoldHi));
        if (locked) row.AddChild(Style.H(4, Glyphs.Icon("lock", 15, Hex("#ff9a80")), Style.Label(p.Locked!, Style.UiBold, Style.Small, Hex("#ff9a80"))));
        else if (p.Hint != null) row.AddChild(Style.Label(p.Hint, Style.TextItalic, Style.Small, Style.InkDim));
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
        // Discoveries and loot in a burst gather into one toast that grows, not a column of them.
        double now = Time.GetTicksMsec() / 1000.0;
        if (lastToast is { } lt && lt.Kind == t.Kind && t.Kind is ToastKind.Lore or ToastKind.Loot && t.Rarity == null && t.Icon == null
            && now - lt.At < 2.5 && IsInstanceValid(lt.Box) && lt.Names.Count < 5)
        {
            lt.Names.Add(t.Text);
            if (lt.Box.FindChild("Title", true, false) is Label title) title.Text = string.Join(", ", lt.Names);
            lt.Box.SetMeta("t", 0.06);
            lastToast = lt with { At = now };
            return;
        }
        var (glyph, color) = ToastLook.GetValueOrDefault(t.Kind, ("arcane", Style.Gold));
        if (t.Rarity is int r) color = Style.RarityOf(r);
        var box = new PanelContainer { MouseFilter = Control.MouseFilterEnum.Ignore, CustomMinimumSize = new Vector2(408, 0) };
        var s = Style.Box(new Color(0.047f, 0.04f, 0.055f, 0.82f), color, 0, 4, 8);
        s.BorderWidthLeft = 3;
        box.AddThemeStyleboxOverride("panel", UiArt.Frame("toast", s));
        var row = Style.H(10, t.Icon != null ? ItemPhotos.Icon(t.Icon, 40, color) : Glyphs.Icon(glyph, 22, color));
        var head = Style.Label(t.Text, t.Kind == ToastKind.Quest ? Style.Display : Style.UiBold, 17, t.Kind == ToastKind.Quest ? Style.GoldHi : t.Rarity != null ? color : Hex("#f0e6d2"), true);
        head.Name = "Title";
        var words = Style.V(0, head);
        if (!string.IsNullOrEmpty(t.Sub)) words.AddChild(Style.Label(t.Sub, Style.TextItalic, Style.Caption, Hex("#b8ab96"), true));
        words.SizeFlagsHorizontal = Control.SizeFlags.ExpandFill;
        row.AddChild(words);
        box.AddChild(row);
        box.SetMeta("t", 0.0);
        box.SetMeta("life", t.Life ?? 5.0);
        toasts.AddChild(box);
        lastToast = (box, t.Kind, new List<string> { t.Text }, now);
        while (toasts.GetChildCount() > 6) toasts.GetChild(0).Free();
    }

    public void Announce(Announcement a)
    {
        // --clean: no title cards over the picture (previs stills taken as storyboard staging).
        if (Args.Has("clean")) return;
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

    string bossMarks = "";
    ColorRect? bossStagger, bossStaggerGroove;

    public void Boss(BossBar? bar)
    {
        bossBox.Visible = bar != null;
        if (bar == null) return;
        bossName.Text = bar.Name.ToUpperInvariant();
        // A boss's Break (the damage past its phase marks) beside its title.
        bossTitle.Text = bar.Break >= 1 ? $"{bar.Title}   ·   Break {Math.Round(bar.Break):N0}" : bar.Title;
        float w = 742;
        float k = (float)Math.Clamp(bar.Hp / Math.Max(1, bar.MaxHp), 0, 1);
        bossFill.Size = new Vector2(w * k, 14);
        bossFill.Color = bar.Shielded ? Hex("#8a8a9a") : Hex("#b0222a");
        bossTrail.Size = new Vector2(Math.Max(bossTrail.Size.X - 2, w * k), 14);
        // The phase marks, built when they change rather than every frame.
        string marks = bar.Phases == null ? "" : string.Join(",", bar.Phases);
        if (marks != bossMarks)
        {
            bossMarks = marks;
            foreach (var c in bossTrack.GetChildren()) if (c.HasMeta("phase")) c.QueueFree();
            foreach (var ph in bar.Phases ?? Array.Empty<double>())
            {
                var mark = new ColorRect { Color = Style.GoldHi, Position = new Vector2(w * (float)ph, 0), Size = new Vector2(2, 16), MouseFilter = Control.MouseFilterEnum.Ignore };
                mark.SetMeta("phase", true);
                bossTrack.AddChild(mark);
            }
        }
        // The stagger bar: a thin line under the health, filled by what would lock a lesser
        // creature. Its groove shows from the first second, so the player learns it is there.
        // (It sat inside the health track, which clips, and was never seen.)
        if (bossStagger == null)
        {
            bossStaggerGroove = new ColorRect { Color = Hex("#1a1410") with { A = 0.85f }, Position = new Vector2(1, 76), Size = new Vector2(w, 5), MouseFilter = Control.MouseFilterEnum.Ignore };
            bossBox.AddChild(bossStaggerGroove);
            bossStagger = new ColorRect { Color = Hex("#e8c860"), Position = new Vector2(1, 76), Size = new Vector2(0, 5), MouseFilter = Control.MouseFilterEnum.Ignore };
            bossBox.AddChild(bossStagger);
        }
        bossStaggerGroove!.Visible = bar.IsBoss;
        bossStagger.Visible = bar.IsBoss && bar.Stagger > 0;
        bossStagger.Size = new Vector2(w * (float)Math.Clamp(bar.Stagger, 0, 1), 5);
        bossStagger.Color = bar.Stagger >= 1 ? Hex("#fff0a0") : Hex("#e8c860");
        bossChannelBox.Visible = bar.Channel != null;
        if (bar.Channel is var (label, prog))
        {
            bossChannelFill.Size = new Vector2(bossChannelBox.Size.X * (float)Math.Clamp(prog, 0, 1), 20);
            bossChannel.Text = label;
        }
    }

    public void Hint(Hint? h)
    {
        hintView = h;
        hintBox.Visible = h != null;
        foreach (var c in hintBox.GetChildren()) { hintBox.RemoveChild(c); c.QueueFree(); }
        if (h == null) return;
        var ink = Style.ParchmentInk;
        var v = Style.V(5, Style.H(6, Glyphs.Icon("scroll", 17, Hex("#6a3a14")), Style.Label(h.Title.ToUpperInvariant(), Style.Display, 15, Hex("#6a3a14"), false, HorizontalAlignment.Left, false)),
            Style.Label(h.Text, Style.Text, 19, ink, true, HorizontalAlignment.Left, false));
        // A known width, so the words wrap before the box is measured.
        v.GetChild<Control>(1).CustomMinimumSize = new Vector2(396 - 28, 0);
        if (h.Keys.Count > 0) v.AddChild(Style.H(6, HintKeys(h.Keys).ToArray()));
        hintBox.AddChild(v);
        hintBox.OffsetTop = hintBox.OffsetBottom;
    }

    static readonly string[] PadNames = ["A", "B", "X", "Y", "LB", "RB", "LT", "RT", "View", "Menu"];

    /// <summary>A hint's keys as the device in hand has them: W A S D become the stick on a pad.</summary>
    static IEnumerable<Control> HintKeys(List<string> keys)
    {
        bool pad = Controls.Instance.UsingPad;
        bool wasd = keys.Count == 4 && string.Concat(keys) == "WASD";
        if (pad && wasd) { yield return Style.PadButton("Left stick"); yield break; }
        foreach (var k in keys) yield return pad && !wasd && PadNames.Contains(k) ? Style.PadButton(k) : Style.Key(k);
    }

    /// <summary>The device in hand changed: every key shown redraws as its keys or buttons.</summary>
    public void DeviceChanged()
    {
        foreach (var (act, row) in handKeys)
        {
            var old = row.GetChild(0);
            row.RemoveChild(old);
            old.QueueFree();
            var k = Style.Prompt(act);
            row.AddChild(k);
            row.MoveChild(k, 0);
        }
        Prompt(promptView);
        Hint(hintView);
        draft?.Prompts();
        talk?.Prompts();
    }

    /// <summary>Where the survivor stands on screen, each frame (null: not on it).</summary>
    public void Follow(Vector2? at)
    {
        if (at is { } p) under.Position = p + new Vector2(-38, 22);
        underWanted &= at != null;
    }

    /// <summary>In an arena: seconds until what rules it comes (negative: past it), the night's phase and its colour; null elsewhere.</summary>
    public void ArenaClock(double? left, string word, Color? tone = null)
    {
        arenaLeft = left;
        // A new phase pops in (docs/feel S-21: escalation as a story).
        if (left != null && word != tallyWord.Text) { tallyWord.PivotOffset = new Vector2(200, 9); tallyWord.Scale = new Vector2(1.35f, 1.35f); }
        tallyWord.Text = left == null ? "" : word;
        tallyWord.AddThemeColorOverride("font_color", tone ?? Style.Ember);
    }

    /// <summary>What matters off the screen, each frame.</summary>
    public void Beyond(List<Beyond> list) => edges.Show(list);

    /// <summary>Where the thing the prompt is for stands on screen (null: the prompt keeps its place).</summary>
    public void PromptAt(Vector2? at) => promptAnchor = at;

    /// <summary>The corner map, a few times a second; null hides it (an arena, the title).</summary>
    public void MapFrame(MinimapView? m)
    {
        bool on = m != null;
        if (minimap.Visible != on)
        {
            minimap.Visible = on;
            corner.Position = corner.Position with { Y = on ? 28 + Minimap.Diameter + 16 : 22 };
        }
        if (m == null) return;
        minimap.Zone(m.Zone, m.Drawing, m.Extent);
        minimap.Show(m.Seen, m.N, m.Marks, m.X, m.Z, m.Facing, m.Night);
    }

    /// <summary>Fade to black (1) or back (0) over some seconds, with words over the black.</summary>
    /// <summary>Pulled into an arena: the world swirls in and burns away to the
    /// dark, where the caption comes up (shaders/pull.gdshader).</summary>
    public void Pull(double seconds, string? caption = null, string? sub = null)
    {
        pullT = 0;
        pullDur = Math.Max(0.1, seconds);
        pull.Visible = true;
        pullMat.SetShaderParameter("progress", 0f);
        fadeCaption.Text = caption ?? "";
        fadeSub.Text = sub ?? "";
    }

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

    /// <summary>A combat skill has evolved: its place on the bar is crowned.</summary>
    public void Crown(string weaponId) { if (slots.TryGetValue(weaponId, out var s)) s.Crown(); }

    /// <summary>Something staged over the play (a chest opening), above the bars and under the screens.</summary>
    public void Over(Control c) => root.AddChild(c);

    /// <summary>Where a held thing lives on screen: a combat skill's place in the arsenal, else the
    /// middle of the passives' row (a chest's things fly home to them).</summary>
    public Vector2 PlaceOf(string id) =>
        slots.TryGetValue(id, out var s) && s.IsInsideTree() ? s.GetGlobalRect().GetCenter() : boons.GetGlobalRect().GetCenter();

    /// <summary>A key for the draft or the conversation, if one is up.</summary>
    public bool Key(Act a) => draft?.Key(a) ?? talk?.Key(a) ?? false;

    /* ------------------------------------------------------------- frame -- */

    public override void _Process(double delta)
    {
        using var _ = new Perf.Span(Perf.Part.Hud);
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
        // The bar flows toward its value; a level's flash fades over a tenth of a second.
        barShown = barShown > barWant + 0.5f ? Mathf.MoveToward(barShown, barWant, dt * 6) : barShown + (barWant - barShown) * (1 - Mathf.Exp(-18 * dt));
        float fw = (760 * K - 32) * Mathf.Clamp(barShown, 0, 1);
        (barEmber ? emberFill : growFill).Size = new Vector2(fw, 10);
        barFlash = Mathf.MoveToward(barFlash, 0, dt / 0.08f);
        (barEmber ? emberFill : growFill).Modulate = Colors.White.Lerp(new Color(3, 3, 3), barFlash);
        barTip.Position = new Vector2(Math.Max(1, fw - 3), 1);
        barTip.Color = (barEmber ? Style.EmberHi : Style.DayHi) with { A = 0.3f + 0.7f * Mathf.SmoothStep(0.6f, 1f, barShown) };
        barTip.Visible = barShown > 0.01f;
        float t2 = Time.GetTicksMsec() / 1000f;
        barGlow.Size = new Vector2(fw, 10);
        barGlow.Color = (barEmber ? Style.EmberHi : Style.DayHi) with { A = barShown >= 0.85f ? 0.25f + 0.25f * Mathf.Sin(t2 * 8) : 0 };
        killPop = Math.Max(0, killPop - delta);
        tallyWord.Scale = tallyWord.Scale.Lerp(Vector2.One, 1 - Mathf.Exp(-8 * dt));
        float kp = 1 + (float)(killPop / 0.15) * 0.15f;
        killsChip.PivotOffset = killsChip.Size / 2;
        killsChip.Scale = new Vector2(kp, kp);
        // The prompt over the thing it is for, where the eye already is; at the bottom when that is off screen.
        if (promptBox.Visible)
        {
            var size = promptBox.GetCombinedMinimumSize();
            var at = promptAnchor is { } pa && pa.X > 0 && pa.X < 1920 && pa.Y > 140 && pa.Y < 1080 - 200
                ? new Vector2(Mathf.Clamp(pa.X - size.X / 2, 20, 1900 - size.X), Mathf.Clamp(pa.Y - size.Y - 6, 120, 1080 - 200 - size.Y))
                : new Vector2((1920 - size.X) / 2, 1080 - 180 - size.Y);
            promptBox.Position = promptBox.Position.Lerp(at, promptBox.Position.DistanceTo(at) > 400 ? 1 : 1 - Mathf.Exp(-18 * dt));
        }
        // The health under the survivor eases in and out with the night's fight.
        underAlpha = Mathf.MoveToward(underAlpha, underWanted ? 1 : 0, dt * 4);
        under.Modulate = Colors.White with { A = underAlpha };
        underFill.Size = new Vector2(74 * underK, 7);
        underFill.Color = underK < 0.35f ? Hex("#ff5a4a").Lerp(Colors.White, 0.25f * Mathf.Max(0, Mathf.Sin(Time.GetTicksMsec() / 1000f * 7))) : Hex("#e8383a");
        underShield.Size = new Vector2(74 * underShieldK, 3);
        // The trail behind health catches up after a moment.
        float trail = globe.Trail;
        if (trail > hpShown) { trailWait += dt; trailShown = trailWait > 0.35f ? Mathf.MoveToward(trail, hpShown, dt * 1.6f) : trail; }
        else { trailWait = 0; trailShown = hpShown; }
        globe.Trail = trailShown;
        bool low = hpShown < 0.35f && combat.Visible;
        float now = Time.GetTicksMsec() / 1000f;
        // Low, the globe beats like a heart and its glass flushes.
        float beat = low ? 1 + 0.06f * Mathf.Max(0, Mathf.Sin(now * 7)) : 1;
        heart.Scale = new Vector2(beat, beat);
        globe.Pulse = low ? 0.5f + 0.5f * Mathf.Sin(now * 7) : 0;
        globe.Changed();
        if (levelPop > 0) { levelPop = Math.Max(0, levelPop - delta / 0.6); float sc = 1 + 0.9f * (float)(levelPop * levelPop); emberLevel.Scale = new Vector2(sc, sc); }
        if (pullT >= 0)
        {
            pullT += delta;
            var vs = GetViewport().GetVisibleRect().Size;
            pullMat.SetShaderParameter("aspect", vs.X / Math.Max(1, vs.Y));
            pullMat.SetShaderParameter("progress", (float)(pullT / pullDur));
            if (pullT >= pullDur)
            {
                // Burned through: the dark holds, and the caption with it.
                pullT = -1;
                pull.Visible = false;
                fadeFrom = fadeTo = 1;
                fadeT = fadeDur = 1;
                fade.Color = new Color(0, 0, 0, 1);
            }
        }
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
/// that sweeps off as it readies, a flash when it fires. Its rank is a
/// number on a badge (read at a glance) over a strip of segments (how far
/// to the top); at the top with what it evolves with, its rim pulses gold
/// and the badge says so.</summary>
public partial class WeaponSlot : Panel
{
    readonly TextureRect art;
    readonly ColorRect sweep;
    readonly HBoxContainer strip;
    readonly PanelContainer badge;
    readonly Label rankText;
    double lastReady = 1, flash, t;
    bool ripe;
    string key = "";

    public WeaponSlot()
    {
        CustomMinimumSize = new Vector2(67, 67);
        MouseFilter = MouseFilterEnum.Ignore;
        art = new TextureRect { Position = new Vector2(14, 12), Size = new Vector2(39, 39), ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.KeepAspectCentered, MouseFilter = MouseFilterEnum.Ignore };
        AddChild(art);
        sweep = new ColorRect { Color = new Color(0.016f, 0.012f, 0.03f, 0.62f), Position = new Vector2(1, 1), Size = new Vector2(65, 0), MouseFilter = MouseFilterEnum.Ignore };
        AddChild(sweep);
        strip = Style.H(2);
        strip.Alignment = BoxContainer.AlignmentMode.Center;
        strip.Position = new Vector2(4, 59);
        strip.Size = new Vector2(59, 4);
        AddChild(strip);
        badge = new PanelContainer { MouseFilter = MouseFilterEnum.Ignore, Position = new Vector2(44, -7) };
        badge.AddThemeStyleboxOverride("panel", Style.Box(new Color("#0d0c10"), Style.GoldDim, 1, 9, 4));
        rankText = Style.Label("1", Style.UiHeavy, Style.Badge, Style.GoldHi, false, HorizontalAlignment.Center);
        rankText.CustomMinimumSize = new Vector2(12, 0);
        badge.AddChild(rankText);
        AddChild(badge);
    }

    double crown = -1;

    /// <summary>It has evolved: the slot swells and burns gold, settling over a second, so the
    /// eye goes from the moment in the world to where the new thing lives.</summary>
    public void Crown() => crown = 0;

    public override void _Process(double delta)
    {
        if (crown < 0) return;
        crown += delta;
        float k = (float)Math.Clamp(crown / 1.3, 0, 1), e = (1 - k) * (1 - k);
        PivotOffset = Size / 2;
        Scale = Vector2.One * (1 + 0.5f * e * (0.75f + 0.25f * Mathf.Cos((float)crown * 18)));
        Modulate = Colors.White.Lerp(new Color(2.4f, 1.9f, 1.0f), e);
        if (crown >= 1.3) { crown = -1; Scale = Vector2.One; Modulate = Colors.White; }
    }

    public void Show(string glyph, Color school, double ready, int rank, int max, bool evolved, bool canEvolve)
    {
        var k = $"{glyph}|{school.ToHtml()}|{rank}|{evolved}|{canEvolve}";
        if (k != key)
        {
            key = k;
            ripe = canEvolve;
            art.Texture = Glyphs.Texture(glyph, 78, school);
            foreach (var c in strip.GetChildren()) c.QueueFree();
            float seg = (59f - 2 * (max - 1)) / Math.Max(1, max);
            for (int i = 0; i < max; i++)
                strip.AddChild(new ColorRect { Color = i < rank ? school : new Color("#15121a"), CustomMinimumSize = new Vector2(seg, 3), MouseFilter = MouseFilterEnum.Ignore });
            // The rank, gold on ember when it has evolved or is ready to (the rim says which: steady or breathing).
            rankText.Text = rank.ToString();
            rankText.AddThemeColorOverride("font_color", evolved || canEvolve ? Style.EmberHi : Style.GoldHi);
            badge.AddThemeStyleboxOverride("panel", Style.Box(new Color("#0d0c10"), evolved || canEvolve ? Style.Gold : Style.GoldDim, 1, 9, 4));
            AddThemeStyleboxOverride("panel", UiArt.Frame("weapon_slot", Style.Box(new Color(0.1f, 0.09f, 0.12f).Lerp(school, 0.1f), evolved ? Style.Gold : canEvolve ? Style.GoldHi : Style.Line, evolved || canEvolve ? 2 : 1, 7, 0)));
        }
        if (ready < lastReady - 0.4) flash = 1;
        lastReady = ready;
        sweep.Size = new Vector2(65, ready < 0.98 ? 65 * (float)(1 - ready) : 0);
        art.Modulate = ready >= 0.98 ? new Color(1.3f, 1.3f, 1.3f) : Colors.White;
        flash = Math.Max(0, flash - 0.05);
        // Ready to evolve: the slot breathes gold until the draft offers it.
        t += 1.0 / 12;
        float glow = ripe ? 0.35f * (0.5f + 0.5f * Mathf.Sin((float)t * 5)) : 0;
        SelfModulate = Colors.White.Lerp(new Color(1.6f, 1.4f, 1.1f), Math.Max((float)flash, glow));
    }
}

/// <summary>An empty place for a weapon yet to come.</summary>
public partial class EmptySlot : Panel
{
    public EmptySlot()
    {
        CustomMinimumSize = new Vector2(67, 67);
        MouseFilter = MouseFilterEnum.Ignore;
        // A place to come: the empty well (frames/slot.png) when painted, quieter than a held skill.
        AddThemeStyleboxOverride("panel", UiArt.Frame("slot", Style.Box(new Color(0.08f, 0.07f, 0.09f, 0.55f), Style.Line with { A = 0.12f }, 1, 7, 0)));
        if (UiArt.Has("slot")) SelfModulate = new Color(1, 1, 1, 0.7f);
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
