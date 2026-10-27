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
/// The heads-up display (docs/design/UI_RESEARCH.md, "The HUD"). Her state is one instrument along
/// the foot (<see cref="Instrument"/>): her life and the art in her hand in two cuffs, the draught and
/// the dash beside them, what fires by itself between, the ember as heat along the chain that joins
/// them. The top edge is kept for what can end her (a boss's bar, its banner); the night's tally (the
/// clock, the slain, the gold) waits in the lower right corner; the place, the quest and the minimap in
/// the upper right; what comes and goes (toasts, tips) on the world itself.
/// </summary>
public partial class GameHud : CanvasLayer
{
    Control root = null!, play = null!, combat = null!;
    ColorRect bruise = null!;
    Label tallyTime = null!, tallyKills = null!, tallyGold = null!;
    int shownLevel;
    bool shownEmber = true;
    /// <summary>Her irons along the foot.</summary>
    Instrument irons = null!;
    float hpShown = 1, trailShown = 1, trailWait;
    // Names made once: a string given where a name is wanted is a new one each
    // call, and the HUD's twelve frames a second left them to the collector.
    internal static readonly StringName FontColor = "font_color", PanelName = "panel";
    /// <summary>The art's readiness last frame: crossing to ready, the vessel flares once.</summary>
    double artReadyWas = 1, artPing;
    Label zoneName = null!;
    DayDial dial = null!;
    HBoxContainer zoneSub = null!;
    VBoxContainer objectives = null!, toasts = null!;
    PanelContainer promptBox = null!, hintBox = null!;
    Control subtitle = null!, announce = null!, bossBox = null!;
    Label sayWho = null!, sayText = null!, annKicker = null!, annTitle = null!, annSub = null!;
    TextureRect sayShade = null!;
    Label bossName = null!, bossTitle = null!, bossChannel = null!;
    ColorRect bossFill = null!, bossTrail = null!, bossChannelFill = null!;
    Control bossTrack = null!, bossChannelBox = null!;
    double sayT, annT, annLife;
    ColorRect fade = null!, pull = null!;
    ShaderMaterial pullMat = null!;
    double pullT = -1, pullDur = 1;
    Label fadeCaption = null!, fadeSub = null!;
    TextureRect fadeGlow = null!;
    Control fadeRule = null!;
    double fadeFrom = 1, fadeTo = 1, fadeT = 1, fadeDur = 1;
    DraftPanel? draft;
    TalkPanel? talk;
    public float FadeAmount => fade.Color.A;
    PromptView? promptView;
    Hint? hintView;
    Control killsChip = null!, tally = null!;
    // The survivor's own health, drawn under them in a night's fight (UI 15 fix 1: HerLight.Bar in every HUD,
    // the same life the HUD shows, pins included; the old flat red ColorRect bar is retired).
    float underAlpha;
    bool underWanted;
    // Her bar in every HUD; the variant "her life" (--hud-life her, HerLight.On) adds her light and the edges.
    HerLight her = null!;
    static readonly double herBleed = Args.Num("hurt-bleed", 0), herBleedFrom = Args.Num("hurt-from", 0);
    double bleedAt, bleedHp;
    Vector2? herAt;
    // The corner: the minimap over the place's name and the objectives.
    Minimap minimap = null!;
    VBoxContainer corner = null!;
    // Discoveries in a burst become one toast that grows.
    (Notice Box, ToastKind Kind, List<string> Names, double At)? lastToast;
    TipLine? tipLine;
    // The chain's heat eased every frame toward its true value (docs/feel S-06): shown, wanted.
    float barShown, barWant;
    bool barEmber = true;
    int barLevel = 1;
    double killPop;
    int killsShown;
    // What matters off the screen; where the prompt's thing is on it; the arena's clock and its word.
    EdgeMarks edges = null!;
    GroundLabels ground = null!;
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
        // Loot's names on the ground, under everything else the fight shows (docs/design/LOOT_DESIGN.md §8.1).
        ground = new GroundLabels();
        Style.Fill(ground);
        combat.AddChild(ground);
        edges = new EdgeMarks();
        Style.Fill(edges);
        combat.AddChild(edges);
        // Her irons, by day and by night, at peace and in a fight: the keystone stays where it is.
        irons = new Instrument();
        play.AddChild(irons);
        // the life lamp's light on the ground: over the world, under everything on the HUD
        root.AddChild(irons.Life.Pool);
        root.MoveChild(irons.Life.Pool, 0);
        if (HerLight.On) BuildHer();
        else if (LifeLamp.Orb != null)
        {
            // (UI 16: the orb keeps the "her life" HUD's low-life edge pulse, over the world, under the HUD)
            play.AddChild(her.Edge);
            play.MoveChild(her.Edge, 0);
        }
        BuildTally();
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
        // Over the black, for a dawn: first light low along the foot, rising as the words come up.
        fadeGlow = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Offsets = new[] { 0f, 0.4f, 1f }, Colors = new[] { Colors.White, Colors.White with { A = 0.3f }, Colors.White with { A = 0 } } },
                FillFrom = new Vector2(0.5f, 1), FillTo = new Vector2(0.5f, 0.15f), Width = 8, Height = 128,
            },
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale,
            MouseFilter = Control.MouseFilterEnum.Ignore, Visible = false,
        };
        Style.Fill(fadeGlow);
        top.AddChild(fadeGlow);
        fadeCaption = Style.Label("", Style.Display, 54, Style.GoldHi, false, HorizontalAlignment.Center);
        fadeCaption.Position = new Vector2(0, 470); fadeCaption.Size = new Vector2(1920, 80);
        top.AddChild(fadeCaption);
        // The house's rule between the words, as under the name on the title.
        fadeRule = new Plaque("", 14, 150) { Position = new Vector2(960 - 178, 536), Size = new Vector2(356, 18) };
        top.AddChild(fadeRule);
        fadeSub = Style.Label("", Style.TextItalic, 24, Style.Ink, false, HorizontalAlignment.Center);
        fadeSub.Position = new Vector2(0, 560); fadeSub.Size = new Vector2(1920, 40);
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

    /// <summary>The night's tally in the lower right corner (the owner: "the clock, kills, gold move to a
    /// lower corner, out of the top centre"): what rules the night in a word, the clock under it, then the
    /// slain and the gold, set to the right margin with its last line level with the cuffs' foot.</summary>
    void BuildTally()
    {
        const float w = 440, right = 1920 - 40, foot = 1080 - 24;
        var col = Style.V(0);
        col.Alignment = BoxContainer.AlignmentMode.End;
        col.Position = new Vector2(right - w, foot - 120);
        col.Size = new Vector2(w, 120);
        col.MouseFilter = Control.MouseFilterEnum.Ignore;
        // No box: a soft dark falloff behind the type (about 55% at its middle, nothing at its edge; 40% barely showed at dawn), so the
        // tally reads on the hub's brightest planks as on night grass (UI note 8, 26 Oct).
        var g = new Gradient { Colors = new[] { new Color(0.02f, 0.015f, 0.025f, 0.55f), new Color(0.02f, 0.015f, 0.025f, 0.34f), new Color(0.02f, 0.015f, 0.025f, 0) }, Offsets = new[] { 0f, 0.45f, 1f } };
        combat.AddChild(new TextureRect
        {
            Texture = new GradientTexture2D { Gradient = g, Width = 128, Height = 128, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f) },
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = Control.MouseFilterEnum.Ignore,
            Position = new Vector2(right - 300, foot - 170), Size = new Vector2(420, 230),
        });
        // (on the play layer, not the fight's: in town only its gold line shows, the purse)
        play.AddChild(col);
        tally = col;
        tallyWord = Style.Label("", Style.UiHeavy, Style.Badge, Style.Ember, false, HorizontalAlignment.Right);
        tallyWord.PivotOffset = new Vector2(w, 9);
        col.AddChild(tallyWord);
        tallyTime = Style.Label("0:00", Style.Display, 34, Hex("#efe3c8"), false, HorizontalAlignment.Right);
        col.AddChild(tallyTime);
        var row = Style.H(18);
        row.Alignment = BoxContainer.AlignmentMode.End;
        tallyKills = Style.Label("0", Style.UiBold, 18, Hex("#cfc3ad"));
        tallyGold = Style.Label("0", Style.UiBold, 18, Style.GoldHi);
        killsChip = Style.H(5, Glyphs.Icon("skull", 18, Hex("#cfc3ad")), tallyKills);
        row.AddChild(killsChip);
        row.AddChild(Style.H(5, Glyphs.Icon("coin", 18, Style.GoldHi), tallyGold));
        col.AddChild(row);
        foreach (var l in new[] { tallyWord, tallyTime, tallyKills, tallyGold }) Rimmed(l);
    }

    /// <summary>A 1 px dark rim round the type, over its drop shadow: corner words that stand on the world
    /// with no box read on the brightest ground (UI note 8).</summary>
    static Label Rimmed(Label l)
    {
        l.AddThemeConstantOverride("outline_size", 2);
        l.AddThemeColorOverride("font_outline_color", new Color(0.02f, 0.015f, 0.01f, 0.8f));
        return l;
    }
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

    /// <summary>The survivor's health under their feet, where the eye already is in a night's fight (the
    /// survivors-likes' answer: docs/UI_RESEARCH.md 4.1): HerLight's forged bar, in every HUD.</summary>
    void BuildUnder()
    {
        her = new HerLight();
        combat.AddChild(her);
        combat.AddChild(her.Under);
    }

    /// <summary>HUD variant "her life" (--hud-life her): the lamp hidden (its number and pool go with it), the
    /// chain's left end in a forged ring where the lamp's eye held it, what is on her (statuses) where the lamp
    /// stood; her bar, her light on the ground and the low-life edges (HerLight).</summary>
    void BuildHer()
    {
        irons.Life.Visible = false;
        // the chain's forged left end: its ring under the chain, its upper right quarter over it
        var end = new ChainEnd();
        irons.AddChild(end);
        irons.MoveChild(end, irons.Chain.GetIndex());
        irons.AddChild(new ChainEnd(front: true));
        irons.Statuses.Position = new Vector2(Instrument.LifeAt.X - 150, Instrument.SmallY - 15);
        root.AddChild(her.Pool);
        root.MoveChild(her.Pool, 0);
        play.AddChild(her.Edge);
        play.MoveChild(her.Edge, 0);
        if (Args.Get("hurt-mul") is string hm) SurvivorUnchained.Sim.Battle.HurtMul = Args.Num("hurt-mul", 1);
    }

    /// <summary>The minimap's top: low enough that the day's path over its bezel clears the screen's edge.</summary>
    const float MapY = 44;

    /// <summary>The upper right: the minimap in its bezel, under it the place's name, the time and the
    /// day, then what is being done, all set to the same right margin as the bezel's iron.</summary>
    void BuildCorner()
    {
        minimap = new Minimap { Position = new Vector2(1920 - 40 - Minimap.Diameter, MapY), Visible = false };
        play.AddChild(minimap);
        var c = Style.V(3);
        corner = c;
        c.Position = new Vector2(1920 - 31 - 400, 22);
        c.Size = new Vector2(400, 0);
        play.AddChild(c);
        zoneName = Rimmed(Style.Label("", Style.Display, 29, Style.GoldHi, false, HorizontalAlignment.Right));
        c.AddChild(zoneName);
        zoneSub = Style.H(6);
        zoneSub.Alignment = BoxContainer.AlignmentMode.End;
        c.AddChild(zoneSub);
        dial = new DayDial { Visible = false, SizeFlagsVertical = Control.SizeFlags.ShrinkEnd };
        zoneSub.AddChild(dial);
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
        sayWho = Style.Label("", Style.Display, 17, Style.GoldHi, false, HorizontalAlignment.Center);
        sayText = Style.Label("", Style.Text, 24, Hex("#f4ecdc"), true, HorizontalAlignment.Center);
        subtitle.AddChild(sayWho);
        subtitle.AddChild(sayText);
        // A soft smoke behind the words, drawn behind the line and sized to it: on daylit stone a
        // pale line with only a shadow was hard to read.
        sayShade = new TextureRect
        {
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Offsets = new[] { 0f, 0.55f, 1f }, Colors = new[] { new Color(0.02f, 0.015f, 0.03f, 0.72f), new Color(0.02f, 0.015f, 0.03f, 0.48f), new Color(0.02f, 0.015f, 0.03f, 0) } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f), Width = 128, Height = 64,
            },
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale,
            MouseFilter = Control.MouseFilterEnum.Ignore, ShowBehindParent = true,
            AnchorLeft = 0.5f, AnchorRight = 0.5f, AnchorTop = 0, AnchorBottom = 1,
        };
        sayText.AddChild(sayShade);
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

    /// <summary>A boss's bar along the top edge, where the ember's used to be (the owner: "ember on the
    /// bottom sliding the boss stuff up"), so it never meets a tip or the boss's own banner under it: its
    /// name over the bar, the bar in a plain forged groove (hud/boss_groove.png when UI art has made
    /// it), the stagger as a thin line along its foot, its title and Break under that, a channel's bar
    /// last.</summary>
    void BuildBoss()
    {
        float w = BossW, x = (1920 - w) / 2;
        bossBox = Box(play, x, 14, w, 118);
        bossBox.Visible = false;
        bossName = Style.Label("", Style.Display, 26, Hex("#ffe0c0"), false, HorizontalAlignment.Center);
        bossName.Size = new Vector2(w, 32);
        bossBox.AddChild(bossName);
        var track = new Panel { Position = new Vector2(0, 38), Size = new Vector2(w, 16), ClipContents = true, MouseFilter = Control.MouseFilterEnum.Ignore };
        // The groove: near black, edged in the cuffs' iron, a hair of light along its top.
        var groove = Style.Box(Hex("#0d0606"), Cuff.Iron(0.38f), 2, 2, 0);
        groove.ShadowColor = new Color(0, 0, 0, 0.6f);
        groove.ShadowSize = 6;
        track.AddThemeStyleboxOverride(PanelName, UiArt.Frame("boss_groove", groove));
        bossBox.AddChild(track);
        bossTrack = track;
        bossTrail = new ColorRect { Color = Hex("#e8c07a"), Position = new Vector2(2, 2), Size = new Vector2(w - 4, 12), MouseFilter = Control.MouseFilterEnum.Ignore };
        track.AddChild(bossTrail);
        bossFill = new ColorRect { Color = Hex("#b0222a"), Position = new Vector2(2, 2), Size = new Vector2(w - 4, 12), MouseFilter = Control.MouseFilterEnum.Ignore };
        track.AddChild(bossFill);
        // (the bar's light: a pale line along its top and a shade along its foot, over the fill)
        track.AddChild(new ColorRect { Color = new Color(1, 0.9f, 0.85f, 0.16f), Position = new Vector2(2, 2), Size = new Vector2(w - 4, 1), MouseFilter = Control.MouseFilterEnum.Ignore });
        track.AddChild(new ColorRect { Color = new Color(0, 0, 0, 0.28f), Position = new Vector2(2, 10), Size = new Vector2(w - 4, 4), MouseFilter = Control.MouseFilterEnum.Ignore });
        // An iron clamp over each end, the groove held between them (UI art's boss_groove.png has its own).
        if (!UiArt.Has("boss_groove"))
            foreach (float cx in new[] { -6f, w - 6 })
            {
                var clamp = new Panel { Position = new Vector2(cx, 34), Size = new Vector2(12, 24), MouseFilter = Control.MouseFilterEnum.Ignore };
                var cs = Style.Box(Cuff.Iron(0.3f), new Color(0, 0, 0, 0.9f), 1, 2, 0);
                cs.ShadowColor = new Color(0, 0, 0, 0.5f);
                cs.ShadowSize = 3;
                clamp.AddThemeStyleboxOverride(PanelName, cs);
                clamp.AddChild(new ColorRect { Color = new Color(1, 0.94f, 0.82f, 0.22f), Position = new Vector2(2, 1), Size = new Vector2(8, 1), MouseFilter = Control.MouseFilterEnum.Ignore });
                bossBox.AddChild(clamp);
            }
        bossTitle = Style.Label("", Style.TextItalic, 16, Style.InkDim, false, HorizontalAlignment.Center);
        bossTitle.Position = new Vector2(0, 64); bossTitle.Size = new Vector2(w, 20);
        bossBox.AddChild(bossTitle);
        bossChannelBox = new Panel { Position = new Vector2(w * 0.2f, 92), Size = new Vector2(w * 0.6f, 20), ClipContents = true, MouseFilter = Control.MouseFilterEnum.Ignore };
        bossChannelBox.AddThemeStyleboxOverride(PanelName, Style.Box(Hex("#0e0c12"), Hex("#ffcf8a") with { A = 0.6f }, 1, 2, 0));
        bossBox.AddChild(bossChannelBox);
        bossChannelFill = new ColorRect { Color = Hex("#ffb050") with { A = 0.6f }, Size = new Vector2(0, 20), MouseFilter = Control.MouseFilterEnum.Ignore };
        bossChannelBox.AddChild(bossChannelFill);
        bossChannel = Style.Label("", Style.UiHeavy, 13, Colors.White, false, HorizontalAlignment.Center);
        bossChannel.Size = new Vector2(w * 0.6f, 20);
        bossChannel.VerticalAlignment = VerticalAlignment.Center;
        bossChannelBox.AddChild(bossChannel);
    }

    /// <summary>The boss's bar's width: the instrument's own, so the top and the foot share their measure.</summary>
    const float BossW = 2 * (Instrument.Reach + Instrument.R + Instrument.Band);
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
    Tween? playFade;

    /// <summary>The play's HUD shown or hidden; shown with a fade (seconds),
    /// it comes in over a cinematic's blend into play rather than at once.</summary>
    public void ShowPlay(bool on, float fade = 0)
    {
        playFade?.Kill();
        playFade = null;
        if (!on || fade <= 0 || play.Visible)
        {
            play.Visible = on;
            play.Modulate = Colors.White;
            return;
        }
        play.Visible = true;
        play.Modulate = new Color(1, 1, 1, 0);
        playFade = play.CreateTween();
        playFade.TweenProperty(play, "modulate:a", 1f, fade).SetTrans(Tween.TransitionType.Sine).SetEase(Tween.EaseType.InOut);
    }

    float calm = 1;

    /// <summary>The idle close view of her (GameCloseUp): the play HUD steps away over half a second, and is
    /// back at once when it ends. (A fade in from ShowPlay is left to finish.)</summary>
    public void Calm(bool away, double dt)
    {
        if (!away)
        {
            // (only its own step away is undone: a conversation's or the fall's dimming is theirs)
            if (calm < 1) { calm = 1; play.Modulate = Colors.White; }
            return;
        }
        if (calm >= 1) { playFade?.Kill(); playFade = null; }
        calm = Mathf.Max(0, calm - (float)dt / 0.5f);
        play.Modulate = new Color(1, 1, 1, calm);
    }

    float labelsAlpha = 1;

    /// <summary>A Flare's BOOM hides the ground names and any tip text until its fire has gone (k 0 to 1).</summary>
    public void LabelsAlpha(float k)
    {
        if (k == labelsAlpha) return;
        labelsAlpha = k;
        ground.Modulate = new Color(1, 1, 1, k);
        ground.Visible = k > 0;
        if (tipLine != null && IsInstanceValid(tipLine)) tipLine.Fade = k;
    }

    float flareDim;
    ulong tipHoldUntil;
    Hint? tipHeld;
    bool tipWaiting;

    /// <summary>A Flare holds the frame (FLARE_LOOK §1.5): the play HUD dims to 35% (k 1) but her irons (her health and
    /// the Flare's lamp) and a boss's bar; back at k 0.</summary>
    public void FlareDim(float k)
    {
        if (k == flareDim) return;
        // A tip waits from the press until three seconds after the Flare hands the screen back (judge 3: "THE MAP"
        // over the BOOM). Real time: the Flare's hitstop must not stretch it.
        tipHoldUntil = k > 0 ? ulong.MaxValue : Time.GetTicksMsec() + 3000;
        if (k > 0 && hintView != null)
        {
            // One already up goes and comes back after.
            tipHeld = hintView; tipWaiting = true; hintView = null; hintBox.Visible = false;
            if (tipLine != null && IsInstanceValid(tipLine)) tipLine.QueueFree();
            tipLine = null;
        }
        flareDim = k;
        foreach (var n in play.GetChildren())
            if (n is CanvasItem c && c != irons && c != bossBox) c.Modulate = new Color(1, 1, 1, 1 - 0.65f * k);
    }

    public void SetBruise(float v) => ((ShaderMaterial)bruise.Material).SetShaderParameter("amount", v);

    static readonly Dictionary<ToastKind, (string Glyph, Color Color)> ToastLook = new()
    {
        [ToastKind.Quest] = ("quest", Hex("#f3d9a0")), [ToastKind.World] = ("eye", Hex("#9ab0d8")), [ToastKind.Relation] = ("talk", Hex("#d89ab0")),
        [ToastKind.Warning] = ("skull", Hex("#ff5a5a")), [ToastKind.Lore] = ("scroll", Hex("#c8b890")), [ToastKind.Level] = ("arcane", Hex("#ffd07a")),
        [ToastKind.Gold] = ("coin", Hex("#f3d9a0")), [ToastKind.Loot] = ("hand", Hex("#d9b56a")),
    };

    /// <summary>The fight (or a walk at peace), as the HUD shows it (a dozen times a second).</summary>
    /// <param name="level">The survivor's own level, and how far into it (shown when the ember is out).</param>
    public void Frame(Battle? b, double gold, int draughts, (int Level, double K) level = default)
    {
        if (b == null) return;
        combat.Visible = b.Combat;
        var p = b.Player;
        double max = b.MaxHp;
        pinMax = max;
        // (--hurt-bleed F, a shot of her life falling for real: F of her life a second taken as a blow, down to
        // 12%, from the fight's second --hurt-from on, on top of its own blows (--hurt-mul); HUD variant "her life" only)
        if (herBleed > 0 && b.Combat && p.Alive)
        {
            double t = Time.GetTicksMsec() / 1000.0;
            if (bleedAt > 0 && b.Time >= herBleedFrom && p.Hp / max > 0.12)
            {
                // (and no healing while it bleeds: the draught's lesson and pickups would undo the fall)
                if (bleedHp > 0 && p.Hp > bleedHp) p.Hp = bleedHp;
                b.HurtPlayerRaw(Math.Min(t - bleedAt, 0.25) * herBleed * max, School.Physical, "debug", null, true);
                bleedHp = p.Hp;
            }
            bleedAt = t;
        }
        float k = (float)Math.Clamp(p.Hp / max, 0, 1);
        hpShown = k;
        var life = irons.Life;
        life.Level = k;
        life.Shield = (float)Math.Clamp(p.Shield / max, 0, 1);
        double hpNum = Math.Ceiling(Math.Max(p.Hp, 0));
        if (hpNum != globeNum) { globeNum = hpNum; life.Number = $"{hpNum}"; }
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

        // The chain: the ember while it burns; by day, the survivor's own growing.
        bool ember = b.EmberOn;
        float e = (float)Math.Clamp(ember ? b.EmberXp / Math.Max(1, b.EmberNext) : level.K, 0, 1);
        // The heat is eased every frame (_Process); a new level flares the chain and drains to what carried over.
        if (ember != barEmber) { barEmber = ember; barShown = e; }
        barWant = e;
        int lv = ember ? b.EmberLevel : Math.Max(1, level.Level);
        if (lv != shownLevel || ember != shownEmber)
        {
            if (lv > shownLevel && ember == shownEmber && shownLevel > 0) { barShown = 1; irons.Chain.Rise(); irons.River?.Thread.Rise(); }
            shownLevel = lv; shownEmber = ember;
            barLevel = lv;
        }
        underWanted = b.Combat && ember && p.Alive && Settings.Current.UnderBar;

        // The six places: what fires by itself, in the order it came; the rest quiet.
        var socks = irons.Sockets;
        int i = 0;
        foreach (var w in b.Weapons)
        {
            if (i >= socks.Length) break;
            bool canEvolve = w.Evolution == null && w.Rank >= Weapons.MaxRank && LevelUp.EarnedBranches(b, w.Id).Count > 0;
            socks[i++].Show(w.Id, w.Art, ItemViews.SchoolColors[w.School], b.WeaponReady(w), w.Rank, Weapons.MaxRank, w.Evolution != null, canEvolve);
        }
        for (; i < socks.Length; i++) socks[i].Empty();
        irons.Lay(b.Weapons.Count, all: ember);

        boonWant.Clear();
        foreach (var (id, rank) in b.Boons)
            if (rank > 0 && Boons.Find(id) != null) boonWant.Add((id, rank));
        if (!Same(boonWant, boonHave))
        {
            boonHave.Clear();
            boonHave.AddRange(boonWant);
            foreach (var c in irons.Passives.GetChildren()) c.QueueFree();
            foreach (var (id, rank) in boonWant) irons.Passives.AddChild(Passive(Boons.Find(id)!, rank));
        }

        // The dash's charges round its glass; the draughts left.
        var dash = irons.Dash;
        dash.Max = (int)Math.Round(b.Stats.Get(Stat.DashCharges));
        dash.Count = p.DashCharges;
        dash.Recharge = (float)Math.Clamp(p.DashRecharge / Abilities.Dash.Recharge, 0, 1);
        dash.Form = b.Ability is AbilityKind fk && Abilities.All[fk].Movement
            ? b.FormReady ? 1 : (float)Math.Clamp(1 - p.AbilityCd / Math.Max(0.1, b.FormWait(fk)), 0, 0.99) : -1;
        if (b.Ability != formGlyphOf)
        {
            formGlyphOf = b.Ability;
            dash.FormGlyph = b.Ability is AbilityKind gk ? Glyphs.Texture(Abilities.All[gk].Icon, 48, Hex("#fff3dc"), line: true) : null;
        }
        irons.Draught.Count = draughts;

        // The art slot now shows the Flare (docs/design/CLASSES.md §3): its meter, a plain readout until phase 3's HUD.
        var art = irons.Art;
        if (b.Flare is { } fl)
        {
            double full = Battle.FlareFull;
            double per = Math.Clamp(b.FlareMeter % full == 0 && b.FlareMeter > 0 ? 1 : b.FlareMeter % full / full, 0, 1);
            art.Liquid(new Color("#ffc66a"), new Color("#8a3a08"));
            if (b.FlareReady && per < 1) per = 1;
            if (per >= 1 && artReadyWas < 1) artPing = 1;
            artReadyWas = per;
            art.Level = (float)per;
            // The Flare's own glyph (its data's icon), never the calling's art's: the Warden's bull is the
            // dash form's badge only (UI note 3, 26 Oct: the Q orb wore the bull of Bull Rush).
            art.Glyph = Glyphs.Texture(fl.Icon is { Length: > 0 } fi ? fi : fl.Id, 96, Hex("#fff3dc"), line: true);
            art.GlyphTint = b.FlareReady ? Colors.White : new Color(0.62f, 0.58f, 0.54f, 0.85f);
            art.Number = "";   // (HUD v2: no percent; the level is the reading)
            // (the dash form's state is the dash's own ring now, Round.Form: under the Flare's orb it taught the wrong key)
            var line = new System.Text.StringBuilder();
            foreach (var r in b.Reflexes)
                line.Append(line.Length > 0 ? " | " : "").Append($"{r.Def.Art} {(r.Cd > 0 ? Math.Ceiling(r.Cd).ToString() : "ready")}");
            irons.ArtNote.Text = line.ToString();
        }
        else { art.Level = 0; art.Glyph = null; art.Number = ""; irons.ArtWord.Text = ""; irons.ArtNote.Text = ""; }

        ApplyPin(true, ember);
        // Outside a fight (the town, where the shops are) only the gold line of the tally shows.
        tallyWord.Visible = b.Combat;
        if (!b.Combat)
        {
            tallyTime.Visible = false;
            killsChip.Visible = false;
            tallyGold.Text = $"{Math.Floor(gold + b.GoldGained - b.GoldBanked)}";
            GroundLabels.Drawn.Clear();
            return;
        }
        // The fight's clock and its count belong to the night; by day they would only be noise.
        tallyTime.Visible = ember;
        killsChip.Visible = ember;
        // In an arena the clock counts down to what rules it; after, how long past the half hour.
        double shown = arenaLeft is double left && left > 0 ? left : arenaLeft is double past ? -past : b.Time;
        int m = (int)(shown / 60), s = (int)(shown % 60);
        tallyTime.Text = arenaLeft is double l2 && l2 <= 0 ? $"+{m}:{s:00}" : $"{m}:{s:00}";
        tallyTime.AddThemeColorOverride(FontColor, arenaLeft is double l3 && l3 > 0 && l3 < 60 ? Style.EmberHi : Hex("#efe3c8"));
        tallyKills.Text = b.KillCount.ToString();
        // The count pops when it climbs, at most ten times a second.
        if (b.KillCount > killsShown && killPop <= 0.05) killPop = 0.15;
        killsShown = b.KillCount;
        tallyGold.Text = $"{Math.Floor(gold + b.GoldGained - b.GoldBanked)}";
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

    double pinMax = 100;

    /// <summary>Debug (--hud-pin, HudPin.cs): what the instrument shows held at the pinned values, never the
    /// fight. Nothing when no pin is given.</summary>
    void ApplyPin(bool withSeats, bool night)
    {
        if (!HudPin.Active) return;
        var life = irons.Life;
        if (HudPin.Life is float l)
        {
            life.Level = life.Trail = hpShown = trailShown = l;
            globeNum = double.NaN;
            life.Number = $"{Math.Ceiling(l * pinMax)}";
        }
        if (HudPin.Shield is float sh) life.Shield = sh;
        if (HudPin.Ember is float em) barShown = barWant = em;
        irons.Chain.PinHeat = HudPin.LockHeat ?? -1;
        if (HudPin.Draught is int dr) irons.Draught.Count = dr;
        if (HudPin.Art is float ar) { irons.Art.Level = ar; irons.Art.Number = ""; }
        if (withSeats && HudPin.Seats is { } seats) irons.PinSeats(seats, night);
    }

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
        var row = irons.Statuses;
        foreach (var c in row.GetChildren()) c.QueueFree();
        for (int i = 0; i < statusWant.Count; i++)
        {
            var (glyph, good) = statusWant[i];
            double n = Countdown(statusLeft[i]);
            var col = good ? Hex("#9ad4ff") : Hex("#ff8a6a");
            // What is on her as its mark and its seconds, on the world over her life (no chip round it).
            var text = Style.Label(n < 0 ? "" : $"{n}", Style.UiHeavy, Style.Badge, col);
            var mark = Style.H(3, Glyphs.Icon(glyph, 20, col, line: true), text);
            mark.MouseFilter = Control.MouseFilterEnum.Ignore;
            row.AddChild(mark);
            statusText.Add(text);
            statusShown.Add(n);
        }
    }

    /// <summary>A passive over the six places: its glyph in its rarity's colour, its rank at its foot if
    /// it has ranks, on the world (no chip round it).</summary>
    static Control Passive(BoonDef bd, int rank)
    {
        var col = Style.RarityOf((int)bd.Rarity);
        var holder = new Control { CustomMinimumSize = new Vector2(26, 26), MouseFilter = Control.MouseFilterEnum.Ignore };
        var gl = Glyphs.Icon(bd.Icon, 22, col, line: true);
        gl.Position = new Vector2(2, 0);
        gl.Size = new Vector2(22, 22);
        holder.AddChild(gl);
        if (bd.Max > 1)
        {
            var r = Style.Label($"{rank}", Style.UiHeavy, 12, Colors.White);
            r.Position = new Vector2(18, 12);
            holder.AddChild(r);
        }
        return holder;
    }
    /// <summary>What the header shows now (the game asks every frame; it is redrawn only when this changes).</summary>
    (string Name, string? Region, int Day, TimeOfDay Time)? zoneShown;

    /// <summary>The place's name and, under it, the time of day (its word and its sun or moon), the day and the
    /// region. Called on every frame of play with the zone's time as it is now, so the header follows the time
    /// live (UI note 2, 26 Oct: it said Night under a moon at the Prologue's dawn, set only when the zone loaded).</summary>
    public void ZoneInfo(string name, string? region, int day, TimeOfDay time)
    {
        if (zoneShown == (name, region, day, time)) return;
        zoneShown = (name, region, day, time);
        zoneName.Text = name.ToUpperInvariant();
        foreach (var c in zoneSub.GetChildren()) if (c != dial) c.QueueFree();
        // The sun or moon always stands by the time word (the dial, where there is one, sits beside it).
        zoneSub.AddChild(Glyphs.Icon(time == TimeOfDay.Night ? "moon" : "sun", 15, time == TimeOfDay.Night ? Hex("#b8ccff") : Hex("#ffd890")));
        zoneSub.AddChild(Rimmed(Style.Label($"{time}  ·  Day {day}" + (region != null ? $"  ·  {region}" : ""), Style.Ui, 17, Style.Ink with { A = 0.85f })));
    }

    FallChoices? fall;

    /// <summary>The fall's two choices over the darkened world (null clears them).</summary>
    public void Fall(int? risesLeft, Action? rise = null, Action? letGo = null)
    {
        if (fall != null && IsInstanceValid(fall)) fall.QueueFree();
        fall = null;
        // The play's HUD steps back while the choice waits, as under a conversation: the two
        // choices are the brightest things on the screen (the bars and the ember sat over them).
        play.Modulate = risesLeft != null ? new Color(1, 1, 1, 0.4f) : Colors.White;
        if (risesLeft is not int n || rise == null || letGo == null) return;
        fall = new FallChoices(n, rise, letGo);
        root.AddChild(fall);
    }

    StoryChoices? choice;

    /// <summary>A choice the story puts to her, over the live world: each answer on its key (null clears it).</summary>
    public void Choice(StoryChoice? c, Act[] keys, Action<int> pick)
    {
        if (choice != null && IsInstanceValid(choice)) choice.QueueFree();
        choice = null;
        if (c == null) return;
        choice = new StoryChoices(c, keys, pick);
        root.AddChild(choice);
    }

    /// <summary>The answer whose key is held (-1: none), and how far to choosing it (0 to 1).</summary>
    public void ChoiceHeld(int i, double k)
    {
        if (choice != null && IsInstanceValid(choice)) choice.Held(i, (float)Math.Clamp(k, 0, 1));
    }

    /// <summary>The day's clock on its dial by the place's name (null: where the clock does not run).</summary>
    public void Clock(double? clock, bool running)
    {
        clockNow = (clock, running);
        // On the map's bezel where there is a map (the day's path over its top); by the place's name
        // where there is none.
        minimap.Clock(clock, running);
        bool onDial = clock != null && !minimap.Visible;
        if (onDial != dial.Visible) dial.Visible = onDial;
        if (onDial && clock is double c) dial.Set(c, running);
    }

    (double? Clock, bool Running) clockNow;

    public void Objectives(List<Tracked> list)
    {
        foreach (var c in objectives.GetChildren()) c.QueueFree();
        foreach (var t in list)
        {
            var head = Style.H(6, Rimmed(Style.Label(t.Title, Style.Display, 18, t.Tone == TrackTone.Tutorial ? Style.Ink : Style.GoldHi)));
            head.Alignment = BoxContainer.AlignmentMode.End;
            objectives.AddChild(head);
            foreach (var s in t.Steps)
            {
                var col = s.Done ? Style.InkDim with { A = 0.6f } : s.Optional ? Style.InkDim : Style.Ink;
                // The step's mark: the house's diamond, open while it waits and filled in gold once done; a
                // small ring for what may be left (no checkbox: no box).
                var mark = new StepMark(s.Done, s.Optional, col);
                HBoxContainer row;
                // "Answer the night: hold [[answer]]": the key itself, as the device in hand shows it.
                var key = System.Text.RegularExpressions.Regex.Match(s.Text, @"\[\[(\w+)\]\]");
                if (key.Success && Enum.TryParse<Act>(key.Groups[1].Value, true, out var act))
                {
                    var font = s.Optional ? Style.TextItalic : Style.Ui;
                    row = Style.H(5, Rimmed(Style.Label(s.Text[..key.Index].TrimEnd(), font, 16, col)), Style.Prompt(act));
                    if (s.Text[(key.Index + key.Length)..].Trim() is { Length: > 0 } after) row.AddChild(Rimmed(Style.Label(after, font, 16, col)));
                    row.AddChild(mark);
                }
                else
                {
                    // The objectives stand on the world like the tally: rimmed, so a dim italic line never ghosts over a tree.
                    var l = Rimmed(Style.Label(s.Text, s.Optional ? Style.TextItalic : Style.Ui, 16, col, true, HorizontalAlignment.Right));
                    l.CustomMinimumSize = new Vector2(370, 0);
                    row = Style.H(7, l, mark);
                }
                row.Alignment = BoxContainer.AlignmentMode.End;
                objectives.AddChild(row);
            }
            objectives.AddChild(Style.Gap(6));
        }
    }

    readonly HashSet<string> tipShot = new(), promptShot = new();

    public void Prompt(PromptView? p)
    {
        promptView = p;
        promptBox.Visible = p != null;
        if (p == null) return;
        // (--shot: the first time each prompt kind is shown whole)
        if (Args.Has("shot") && promptShot.Add(p.Verb.ToLowerInvariant().Replace(' ', '_'))) Shots.Want($"prompt_{p.Verb.ToLowerInvariant().Replace(' ', '_')}", 0.3);
        foreach (var c in promptBox.GetChildren()) { promptBox.RemoveChild(c); c.QueueFree(); }
        // The key as the device in hand has it: a keycap, or the pad's button.
        var key = Controls.Instance.UsingPad ? Style.PadButton(Controls.Instance.PadLabels(p.For).FirstOrDefault() ?? "B")
            : Style.KeyCap(p.Key, 1.1f);
        if (Controls.Instance.UsingPad) key.CustomMinimumSize = new Vector2(34, 34);
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
        // The narrator in italic, a speaker upright, as the cinematics set them.
        sayText.AddThemeFontOverride("font", who == null ? Style.TextItalic : Style.Text);
        // The smoke as wide as the line (wrapped lines are the box's width), reaching up over the name.
        float w = Mathf.Min(sayText.Size.X > 0 ? sayText.Size.X : 912, Style.Text.GetStringSize(text, HorizontalAlignment.Left, -1, 24).X);
        sayShade.OffsetLeft = -w / 2 - 150;
        sayShade.OffsetRight = w / 2 + 150;
        sayShade.OffsetTop = who != null ? -50 : -26;
        sayShade.OffsetBottom = 26;
    }

    public void Toast(Toast t)
    {
        // Discoveries and loot in a burst gather into one toast that grows, not a column of them.
        double now = Time.GetTicksMsec() / 1000.0;
        if (lastToast is { } lt && lt.Kind == t.Kind && t.Kind is ToastKind.Lore or ToastKind.Loot && t.Rarity == null && t.Icon == null
            && now - lt.At < 2.5 && IsInstanceValid(lt.Box) && lt.Names.Count < 5)
        {
            lt.Names.Add(t.Text);
            lt.Box.Title.Text = string.Join(", ", lt.Names);
            lt.Box.T = Math.Min(lt.Box.T, 0.5);
            lastToast = lt with { At = now };
            return;
        }
        // Words on the world, no box (the owner: "the item toasts could be transparent and stylized"):
        // the icon small, the name in its colour, the count after it.
        var (glyph, color) = ToastLook.GetValueOrDefault(t.Kind, ("arcane", Style.Gold));
        if (t.Rarity is int r) color = Style.RarityOf(r);
        if (t.Kind == ToastKind.Quest) color = Style.GoldHi;
        else if (t.Rarity == null && t.Kind is not (ToastKind.Warning or ToastKind.Level or ToastKind.Gold)) color = Hex("#f0e6d2");
        bool grand = t.Rarity >= 4, noted = grand || t.Rarity >= 2 || t.Kind is ToastKind.Quest or ToastKind.Level;
        Control icon = t.Icon != null ? ItemPhotos.Icon(t.Icon, grand ? 40 : 30, color) : Glyphs.Icon(glyph, 18, color);
        icon.CustomMinimumSize = t.Icon != null ? new Vector2(grand ? 40 : 30, grand ? 40 : 30) : new Vector2(18, 18);
        var box = new Notice(icon, t.Text, t.Sub, color, noted, grand, t.Life ?? (grand ? 8 : t.Kind == ToastKind.Quest ? 6 : 4.5));
        toasts.AddChild(box);
        // The newest first, the rest stepping down under it.
        toasts.MoveChild(box, 0);
        lastToast = (box, t.Kind, new List<string> { t.Text }, now);
        // (five at most: the column keeps clear of the health orb)
        while (toasts.GetChildCount() > 5) toasts.GetChild(toasts.GetChildCount() - 1).Free();
    }

    /// <summary>Where the banner's words stand on the screen while it shows (the lines said over
    /// heads keep out of it: a howl's caption printed beside the banner's own line read as one).</summary>
    public static Rect2? Banner { get; private set; }

    /// <summary>The top-right block on the screen (the minimap over the place's name and the objectives), while
    /// it shows: the name plates over people's heads give way under it.</summary>
    public static Rect2? Header { get; private set; }

    /// <summary>How far down the top of the screen is the HUD's (the ember, the clock, a boss's bar).</summary>
    public static float TopClear { get; private set; } = 118;
    /// <summary>The live tip's bottom edge on the screen (0: none); barks keep 24 px under it.</summary>
    public static float TipBottom { get; private set; }

    /// <summary>The toasts wait (unseen, their time not running) while this is set.</summary>
    public bool HoldToasts;

    Rect2 BannerRect()
    {
        float w = Math.Max(annTitle.GetCombinedMinimumSize().X, Math.Max(annSub.GetCombinedMinimumSize().X, annKicker.Visible ? annKicker.GetCombinedMinimumSize().X : 0));
        w = Math.Min(1200, w + 40);
        return new Rect2(960 - w / 2, announce.Position.Y, w, announce.GetCombinedMinimumSize().Y);
    }

    public void Announce(Announcement a)
    {
        // --clean: no title cards over the picture (previs stills taken as storyboard staging).
        if (Args.Has("clean")) return;
        annKicker.Text = a.Kicker?.ToUpperInvariant() ?? "";
        annKicker.Visible = a.Kicker != null;
        annTitle.Text = a.Title.ToUpperInvariant();
        annTitle.AddThemeFontSizeOverride("font_size", a.Kind == "zone" ? 60 : a.Title.Length > 30 ? 31 : a.Title.Length > 20 ? 38 : a.Kind == "story" ? 41 : 50);
        annTitle.AddThemeColorOverride(FontColor, a.Kind switch { "danger" => Hex("#ff7a5a"), "boon" => Hex("#ffd46a"), "story" => Hex("#e2dac8"), _ => Hex("#f0c878") });
        annSub.Text = a.Sub ?? "";
        announce.Position = new Vector2(360, 1080 * (a.Kind == "zone" ? 0.16f : 0.2f));
        annT = 0;
        annLife = a.Seconds;
    }

    string bossMarks = "";
    ColorRect? bossStagger, bossStaggerGroove;

    /// <summary>The boss whose bar is up (its world plate stands down meanwhile), or null.</summary>
    public static string? BossName { get; private set; }

    public void Boss(BossBar? bar)
    {
        bossBox.Visible = bar != null;
        BossName = bar?.Name;
        if (bar == null) return;
        bossName.Text = bar.Name.ToUpperInvariant();
        // A boss's Break (the damage past its phase marks) beside its title.
        bossTitle.Text = bar.Break >= 1 ? $"{bar.Title}   ·   Break {Math.Round(bar.Break):N0}" : bar.Title;
        float w = BossW - 4;
        float k = (float)Math.Clamp(bar.Hp / Math.Max(1, bar.MaxHp), 0, 1);
        bossFill.Size = new Vector2(w * k, 12);
        bossFill.Color = bar.Shielded ? Hex("#8a8a9a") : Hex("#b0222a");
        bossTrail.Size = new Vector2(Math.Max(bossTrail.Size.X - 2, w * k), 12);
        // The phase marks, built when they change rather than every frame.
        string marks = bar.Phases == null ? "" : string.Join(",", bar.Phases);
        if (marks != bossMarks)
        {
            bossMarks = marks;
            foreach (var c in bossTrack.GetChildren()) if (c.HasMeta("phase")) c.QueueFree();
            foreach (var ph in bar.Phases ?? Array.Empty<double>())
            {
                var mark = new ColorRect { Color = Style.GoldHi, Position = new Vector2(2 + w * (float)ph - 1, 0), Size = new Vector2(2, 16), MouseFilter = Control.MouseFilterEnum.Ignore };
                mark.SetMeta("phase", true);
                bossTrack.AddChild(mark);
            }
        }
        // The stagger: a thin line along the bar's foot, filled by what would lock a lesser creature.
        // Its groove shows from the first second, so the player learns it is there.
        if (bossStagger == null)
        {
            bossStaggerGroove = new ColorRect { Color = Hex("#1a1410") with { A = 0.85f }, Position = new Vector2(2, 56), Size = new Vector2(w, 4), MouseFilter = Control.MouseFilterEnum.Ignore };
            bossBox.AddChild(bossStaggerGroove);
            bossStagger = new ColorRect { Color = Hex("#e8c860"), Position = new Vector2(2, 56), Size = new Vector2(0, 4), MouseFilter = Control.MouseFilterEnum.Ignore };
            bossBox.AddChild(bossStagger);
        }
        bossStaggerGroove!.Visible = bar.IsBoss;
        bossStagger.Visible = bar.IsBoss && bar.Stagger > 0;
        bossStagger.Size = new Vector2(w * (float)Math.Clamp(bar.Stagger, 0, 1), 4);
        bossStagger.Color = bar.Stagger >= 1 ? Hex("#fff0a0") : Hex("#e8c860");
        bossChannelBox.Visible = bar.Channel != null;
        if (bar.Channel is var (label, prog))
        {
            bossChannelFill.Size = new Vector2(bossChannelBox.Size.X * (float)Math.Clamp(prog, 0, 1), 20);
            bossChannel.Text = label;
        }
    }

    /// <summary>Where a tip stands: in the upper third, centred, and always below a boss's bar.</summary>
    static float TipY => Math.Max(1080 * 0.17f, TopClear + 30);

    public void Hint(Hint? h)
    {
        if (Args.Has("clean")) h = null;
        if (Time.GetTicksMsec() < tipHoldUntil && h != null && !(hintView != null && hintView.Id == h.Id)) { tipHeld = h; tipWaiting = true; return; }
        if (h == null) { tipHeld = null; tipWaiting = false; }
        bool same = hintView != null && h != null && hintView.Id == h.Id;
        hintView = h;
        hintBox.Visible = false;
        // The tip, centred in the upper third and set on the world itself (the owner: "a centered
        // attention grabbing thing that is also not on a cheap looking backdrop"), at its full size from
        // the first (the owner: no shrinking from big to small, "more distracting not less").
        if (same && tipLine != null && IsInstanceValid(tipLine)) return;
        if (tipLine != null && IsInstanceValid(tipLine)) tipLine.QueueFree();
        tipLine = null;
        if (h == null) return;
        Control? keys = h.Keys.Count > 0 ? Style.H(6, HintKeys(h.Keys).ToArray()) : null;
        tipLine = new TipLine(h.Title, h.Text, keys) { Position = new Vector2(960, TipY), Fade = labelsAlpha };
        play.AddChild(tipLine);
    }

    static readonly string[] PadNames = ["A", "B", "X", "Y", "LB", "RB", "LT", "RT", "View", "Menu"];

    /// <summary>A hint's keys as the device in hand has them: W A S D become the stick on a pad.</summary>
    static IEnumerable<Control> HintKeys(List<string> keys)
    {
        bool pad = Controls.Instance.UsingPad;
        bool wasd = keys.Count == 4 && string.Concat(keys) == "WASD";
        if (pad && wasd) { yield return Style.PadButton("Left stick"); yield break; }
        // (the tip's keys in the keycap the callouts use: the HUD's dark key was too dark to read on the night, UI note 4)
        foreach (var k in keys) yield return pad && !wasd && PadNames.Contains(k) ? Style.PadButton(k) : Style.KeyCap(k, 1.1f);
    }

    /// <summary>The device in hand changed: every key shown redraws as its keys or buttons.</summary>
    public void DeviceChanged()
    {
        irons.Keys();
        Prompt(promptView);
        Hint(hintView);
        draft?.Prompts();
        talk?.Prompts();
    }

    /// <summary>Where the survivor stands on screen, each frame (null: not on it).</summary>
    /// <summary>The Drowned Girl (--hud drowned): the part of her figure above the bar line, on the HUD (null in the
    /// other HUDs); Game tells her when a foe or the survivor stands behind it, and she fades.</summary>
    public Rect2? FigureRect => LifeLamp.Drowned ? irons.Life.FadeRect : null;
    public void FigureBehind(bool behind) => irons.Life.Behind = behind;

    public void Follow(Vector2? at)
    {
        herAt = at;
        underWanted &= at != null;
    }

    /// <summary>In an arena: seconds until what rules it comes (negative: past it), the night's phase and its colour; null elsewhere.</summary>
    public void ArenaClock(double? left, string word, Color? tone = null)
    {
        arenaLeft = left;
        // A new phase pops in (docs/feel S-21: escalation as a story).
        if (left != null && word != tallyWord.Text) { tallyWord.PivotOffset = new Vector2(200, 9); tallyWord.Scale = new Vector2(1.35f, 1.35f); }
        tallyWord.Text = left == null ? "" : word;
        tallyWord.AddThemeColorOverride(FontColor, tone ?? Style.Ember);
    }

    /// <summary>What matters off the screen, each frame.</summary>
    public void Beyond(List<Beyond> list) => edges.Show(list);

    /// <summary>Loot's names on the ground, each frame.</summary>
    public void Ground(List<GroundLabel> list)
    {
        // The HUD's own words own their ground: labels give way under them.
        ground.KeepOut.Clear();
        if (tipLine != null && IsInstanceValid(tipLine)) ground.KeepOut.Add(tipLine.Area.Grow(12));
        if (corner.IsVisibleInTree()) ground.KeepOut.Add(corner.GetGlobalRect().Grow(8));
        // (and the instrument along the foot, and the night's tally in its corner)
        ground.KeepOut.Add(Instrument.Bounds);
        if (tally.IsVisibleInTree()) ground.KeepOut.Add(tally.GetGlobalRect().Grow(8));
        if (toasts.GetChildCount() > 0) ground.KeepOut.Add(toasts.GetGlobalRect().Grow(8));
        if (announce.Modulate.A > 0.05f) ground.KeepOut.Add(announce.GetGlobalRect());
        ground.Show(list);
    }

    /// <summary>Where the thing the prompt is for stands on screen (null: the prompt keeps its place).</summary>
    public void PromptAt(Vector2? at) => promptAnchor = at;

    /// <summary>The corner map, a few times a second; null hides it (an arena, the title).</summary>
    public void MapFrame(MinimapView? m)
    {
        bool on = m != null;
        if (minimap.Visible != on)
        {
            minimap.Visible = on;
            corner.Position = corner.Position with { Y = on ? MapY + Minimap.Diameter + 18 : 22 };
            // (the day's clock moves between the map's bezel and the dial by the name)
            Clock(clockNow.Clock, clockNow.Running);
        }
        if (m == null) return;
        minimap.Zone(m.Zone, m.Drawing, m.Extent);
        minimap.Show(m.Seen, m.N, m.Marks, m.X, m.Z, m.Facing, m.Night);
    }

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

    /// <summary>Fade to black (1) or back (0) over some seconds, with words over the black; a glow,
    /// if given, rises along the foot with them (first light, for a dawn).</summary>
    public void Fade(float to, double seconds, string? caption = null, string? sub = null, Color? glow = null)
    {
        fadeFrom = fade.Color.A;
        fadeTo = to;
        fadeT = 0;
        fadeDur = Math.Max(0.01, seconds);
        if (to > 0.5f)
        {
            fadeCaption.Text = caption ?? "";
            fadeSub.Text = sub ?? "";
            fadeGlow.Visible = glow != null;
            if (glow is Color g) fadeGlow.SelfModulate = g;
        }
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

    /// <summary>A combat skill has evolved: its place on the instrument is crowned.</summary>
    public void Crown(string weaponId) { foreach (var s in irons.Sockets) if (s.Id == weaponId) s.Crown(); }

    /// <summary>Something staged over the play (a chest opening), above the bars and under the screens.</summary>
    public void Over(Control c) => root.AddChild(c);

    /// <summary>Where a held thing lives on screen: a combat skill's place among the six, else the
    /// middle of the passives' row (a chest's things fly home to them).</summary>
    public Vector2 PlaceOf(string id)
    {
        foreach (var s in irons.Sockets) if (s.Id == id && s.IsInsideTree()) return s.GetGlobalRect().GetCenter();
        return irons.Passives.GetGlobalRect().GetCenter();
    }

    /* ------------------------------------------- the tutorial's callouts -- */

    /// <summary>Whether a narrated line, a banner, the interact prompt or a tip is on the screen now
    /// (a callout waits for them: Teach.cs).</summary>
    public bool SayUp => sayT > 0;
    public bool BannerUp => annT < annLife;
    public bool PromptUp => promptBox.Visible;
    public bool TipUp => tipLine != null && IsInstanceValid(tipLine) && !tipLine.Held;
    /// <summary>A callout is up: a tip waits under it.</summary>
    public bool HoldTip;
    /// <summary>A callout points at the banner: it stays up, whole, until let go.</summary>
    public bool HoldBanner;
    /// <summary>Where the banner's words are (the callout's target), while it shows.</summary>
    public Rect2 BannerArea => BannerRect();
    /// <summary>(The callouts' aim, au1 item 14: where each part they teach stands, while it shows. Repoint
    /// these when the HUD moves; the callouts follow.) The interact prompt.</summary>
    public Rect2? PromptArea => promptBox.Visible ? promptBox.GetGlobalRect() : null;
    /// <summary>The corner map.</summary>
    public Rect2? MinimapArea => minimap.IsVisibleInTree() ? new Rect2(minimap.GlobalPosition, new Vector2(Minimap.Diameter, Minimap.Diameter)) : null;
    /// <summary>The tally: the night's clock, and the slain and gold under it (in town, only the gold shows: none).</summary>
    public Rect2? TallyArea => killsChip.IsVisibleInTree() && tallyGold.GetParent() is Control gold
        ? killsChip.GetGlobalRect().Merge(gold.GetGlobalRect()).Merge(tallyTime.GetGlobalRect() is var tt && tallyTime.IsVisibleInTree() ? new Rect2(tt.End.X - tallyTime.GetMinimumSize().X, tt.Position.Y, tallyTime.GetMinimumSize().X, tt.Size.Y) : gold.GetGlobalRect()) : null;
    /// <summary>The lock at the chain's middle, the ember's level stamped on it (EmberChain.Lock: from the
    /// chain's sag at its middle, shackle to foot).</summary>
    public Rect2? EmberLockArea => irons.River is { } river ? (river.Thread.IsVisibleInTree() ? new Rect2(DgRiver.BossAt - Vector2.One * DgRiver.BossR, Vector2.One * 2 * DgRiver.BossR) : null)
        : irons.Chain.IsVisibleInTree() ? new Rect2(960 - 16, Instrument.EyeL.Y + 4, 32, 38) : null;
    /// <summary>The draft on the screen, if one is.</summary>
    public DraftPanel? DraftShown => draft != null && IsInstanceValid(draft) ? draft : null;
    /// <summary>A combat skill's place among the six, if it is on the instrument now.</summary>
    public Vector2? SocketOf(string id)
    {
        foreach (var s in irons.Sockets) if (s.Id == id && s.IsVisibleInTree()) return s.GetGlobalRect().GetCenter();
        return null;
    }
    /// <summary>A combat skill's place among the six, as a square, if it is on the instrument now.</summary>
    public Rect2? SocketRect(string id)
    {
        foreach (var s in irons.Sockets) if (s.Id == id && s.IsVisibleInTree()) return s.GetGlobalRect();
        return null;
    }

    string? spotKeep;
    AbilityKind? formGlyphOf;
    /// <summary>Whether the dash's form is lit (its flames and badge showing).</summary>
    public bool DashLit => irons.Dash.Form >= 1;
    bool spotUp, spotDim, spotSlots, spotWas;
    float spotK, slotK;

    /// <summary>A callout is up (keep: the HUD part it teaches; null and false: it came down). On a freeze
    /// the HUD dims but for that part (the world's dim is under the HUD, so the part is never pooled
    /// with the ground round it); on the chain's the six places fade; toasts and the art's word wait.</summary>
    public void Spotlight(string? keep, bool dim, bool slots)
    {
        spotUp = dim || slots || keep != null;
        if (keep != null || dim) spotKeep = keep;
        spotDim = dim;
        spotSlots = slots;
    }

    void Spot(float dt)
    {
        spotK = Mathf.MoveToward(spotK, spotDim ? 1 : 0, dt / 0.26f);
        slotK = Mathf.MoveToward(slotK, spotSlots ? 1 : 0, dt / 0.2f);
        irons.ArtNote.Visible = irons.ArtWord.Visible = !spotUp;
        // (an interact prompt waits under a freeze on a thing in the world)
        promptBox.Modulate = spotDim ? Colors.Transparent : Colors.White;
        bool on = spotK > 0 || slotK > 0;
        if (!on && !spotWas) return;
        spotWas = on;
        // (the HUD stays whole under a freeze: only the world dims; the part taught is ringed)
        var dimC = Colors.White;
        foreach (var ch in play.GetChildren())
            if (ch is CanvasItem ci && ch != irons && ch != toasts && ch != subtitle && ch != tipLine && ch != hintBox && ch != promptBox)
                ci.Modulate = dimC;
        irons.Spot(spotK > 0 || slotK > 0 ? spotKeep : null, dimC, 1 - 0.8f * slotK, slotK);
    }

    CanvasLayer? calloutLayer;
    /// <summary>The callouts' layer: over the HUD and the draft, under the fades.</summary>
    public void Callout(Control c)
    {
        if (calloutLayer == null) { calloutLayer = new CanvasLayer { Layer = 20 }; AddChild(calloutLayer); }
        calloutLayer.AddChild(c);
    }

    /// <summary>A key for the draft or the conversation, if one is up.</summary>
    public bool Key(Act a) => draft?.Key(a) ?? talk?.Key(a) ?? false;

    /* ------------------------------------------------------------- frame -- */

    public override void _Process(double delta)
    {
        using var _ = new Perf.Span(Perf.Part.Hud);
        if (tipWaiting && Time.GetTicksMsec() >= tipHoldUntil) { tipWaiting = false; var th = tipHeld; tipHeld = null; Hint(th); }
        float dt = (float)delta;
        if (sayT > 0)
        {
            sayT -= delta;
            subtitle.Modulate = Colors.White with { A = (float)Math.Clamp(sayT / 0.6, 0, 1) };
        }
        else subtitle.Modulate = Colors.Transparent;
        // (held under a callout: whole, its time not running)
        if (HoldBanner && annLife > 0) annT = Math.Min(annT, annLife * 0.5);
        if (annT < annLife)
        {
            annT += delta;
            float a = (float)Math.Clamp(Math.Min(annT / (annLife * 0.1), (annLife - annT) / (annLife * 0.2)), 0, 1);
            announce.Modulate = Colors.White with { A = a };
        }
        else announce.Modulate = Colors.Transparent;
        // Nothing big over a choice being made.
        if (draft != null || talk != null) { announce.Modulate = Colors.Transparent; subtitle.Modulate = Colors.Transparent; }
        Banner = announce.Modulate.A > 0.05f ? BannerRect() : null;
        TopClear = bossBox.Visible ? bossBox.GetGlobalRect().End.Y + 8 : 24;
        Rect2? header = null;
        if (minimap.IsVisibleInTree()) header = minimap.GetGlobalRect();
        if (corner.IsVisibleInTree()) header = header is Rect2 h0 ? h0.Merge(corner.GetGlobalRect()) : corner.GetGlobalRect();
        Header = header;
        foreach (var c in toasts.GetChildren())
        {
            if (c is not Notice n) continue;
            // Held while a chest's opening says the same things over the world; told after it, whole.
            // (and while a callout is up: nothing else speaks over it; told after it, whole)
            bool held = HoldToasts || spotUp;
            n.Modulate = held ? Colors.Transparent : Colors.White;
            if (!held && !n.Step(delta)) n.QueueFree();
        }
        Spot(dt);
        // A tip waits while a banner is up (the two share the upper third and must never meet), then
        // comes in whole; below a boss's bar whenever there is one.
        if (tipLine != null && IsInstanceValid(tipLine))
        {
            tipLine.Held = Banner != null || HoldTip;
            tipLine.Position = new Vector2(960, TipY);
            // (--shot: a tip's picture once it is drawn at full strength, after it has waited for any banner; once per tip)
            if (!tipLine.Held && tipLine.T >= 0.55 && hintView != null && Args.Has("shot") && tipShot.Add(hintView.Id)) Shots.Want("tip_" + hintView.Id, 0.1);
        }
        TipBottom = TipUp ? tipLine!.Area.End.Y : 0;
        // The chain's heat flows toward its value; a new level has already flared it and filled it,
        // and it drains back to what carried over.
        barShown = barShown > barWant + 0.5f ? Mathf.MoveToward(barShown, barWant, dt * 4) : barShown + (barWant - barShown) * (1 - Mathf.Exp(-18 * dt));
        irons.Chain.Set(barShown, barEmber, barLevel);
        irons.River?.Thread.Set(barShown, barEmber, barLevel);
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
        // The trail behind her life catches up after a moment.
        if (trailShown > hpShown) { trailWait += dt; if (trailWait > 0.35f) trailShown = Mathf.MoveToward(trailShown, hpShown, dt * 1.6f); }
        else { trailWait = 0; trailShown = hpShown; }
        var life = irons.Life;
        life.Trail = trailShown;
        float now = Time.GetTicksMsec() / 1000f;
        // Low, her life's glass beats on its own (Vessel, HUD v2: at 30% and under, never scaled); only in the fight.
        life.Pulse = combat.Visible ? 1 : 0;
        ApplyPin(false, barEmber);
        her.Tick(dt, hpShown, trailShown, life.Shield, combat.IsVisibleInTree(), herAt, HerLight.On ? 1 : underAlpha);
        // The art readied: its glass flares once and settles to its ready glow.
        artPing = Math.Max(0, artPing - delta / 0.5);
        var art = irons.Art;
        bool armed = art.Level >= 1 && irons.ArtWord.Text == "";
        art.Glow = armed ? 0.55f + 0.45f * (float)artPing + 0.08f * Mathf.Sin(now * 2.4f) : irons.ArtWord.Text != "" ? 0.6f : 0;
        art.Scale = Vector2.One * (1 + 0.05f * (float)(artPing * artPing));
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
        fadeRule.Modulate = Colors.White with { A = fadeCaption.Text != "" ? cap : 0 };
        // (the glow stays as the black lifts, so the morning comes up out of it)
        fadeGlow.Modulate = Colors.White with { A = Mathf.Clamp(fade.Color.A * 1.4f - 0.2f, 0, 1) };
    }
}

/// <summary>A quest step's mark in the corner: the house's diamond, open while the step waits and filled in
/// gold once it is done; a small ring for a step that may be left. Drawn, so it is crisp at every size.</summary>
public partial class StepMark : Control
{
    readonly bool done, optional;
    readonly Color ink;

    public StepMark(bool done, bool optional, Color ink)
    {
        this.done = done; this.optional = optional; this.ink = ink;
        CustomMinimumSize = new Vector2(12, 20);
        MouseFilter = MouseFilterEnum.Ignore;
    }

    public override void _Draw()
    {
        var c = new Vector2(6, 10.5f);
        if (optional && !done)
        {
            DrawArc(c, 3.6f, 0, Mathf.Tau, 20, new Color(0, 0, 0, 0.6f), 3, true);
            DrawArc(c, 3.6f, 0, Mathf.Tau, 20, ink, 1.3f, true);
            return;
        }
        var d = new[] { c + new Vector2(0, -5), c + new Vector2(5, 0), c + new Vector2(0, 5), c + new Vector2(-5, 0), c + new Vector2(0, -5) };
        if (done) DrawColoredPolygon(d[..4], Style.Gold);
        DrawPolyline(d, new Color(0, 0, 0, 0.6f), 3, true);
        DrawPolyline(d, done ? Style.GoldHi : ink, 1.3f, true);
    }
}
