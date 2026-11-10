using System;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// M4 §4, the level-up card (docs/design/M4_HUD.md): one card over the world, rising from the level coin, centred on
/// x 960, its foot clear of the beads and statuses. The panel language: an ink ground at 82%, a 1 px bronze rule top and
/// bottom, no border. A new key: the skill's gold glyph in a 40 px well, its name (display serif 26, cream), its key cap
/// chip (the seat caps' own KeyTag, held at the seats' on-screen size), one line of what it does (UI sans 16, parchment
/// 80%). A lamp lit: the glyph, the name, "a blow 42 → 47" (before dim, after bright). A new skill (the calling's, on
/// no key yet): the glyph, the name, its one line, no key cap; its prompt row names the skills screen. Plain: the header and the prompt
/// row. The prompt row: a key chip and words; the card then holds 3 s. In 0.18 s, hold 2.2 s, out 0.3 s folding toward
/// the seat that opened (its ring flashes). Words built once a card; drawn once a card; per frame only its transform.
/// </summary>
public partial class LevelCard : Control
{
    static readonly Color Ground = new(0.043f, 0.035f, 0.024f, 0.82f), Rule = new("#8a6a3a"), Bone = new("#e9dfcc"),
        Cream = new("#f3e7cc"), Parch = new Color("#e8dcc0") with { A = 0.8f }, Dim = new Color("#e8dcc0") with { A = 0.5f },
        WellInk = new(0, 0, 0, 0.55f), GlyphGold = new("#e9c27a");
    const float W = 420, Pad = 18, WellD = 40, NameX = Pad + WellD + 14;
    const int HeadSize = 14, NameSize = 26, LineSize = 16, PromptSize = 15;

    public readonly LevelCardQueue Queue = new();
    /// <summary>True while the card must wait (banners held, a screen open): GameHud sets it once.</summary>
    public Func<bool> Held = () => false;
    /// <summary>Where the card folds to (the opened seat's middle, else the coin), asked when the out begins.</summary>
    public Func<LevelCardSpec, Vector2?> FoldTo = _ => null;
    /// <summary>The fold began toward the seat of this slot (GameHud flashes its ring).</summary>
    public Action<LevelCardSpec> OnFold = _ => { };
    /// <summary>The y the card's foot must stay above (the beads' and statuses' top), asked when a card begins.</summary>
    public Func<float, float> FootFor = _ => 960;
    /// <summary>Where it rises from (the coin's middle).</summary>
    public Vector2 From = new(960, 1042);

    string header = "", name = "", line = "", before = "", after = "", measure = "", arrow = " → ", prompt = "";
    Texture2D? glyph;
    float h = 110, w = W;
    Vector2 rest, fold;
    readonly Control capHost = new() { MouseFilter = MouseFilterEnum.Ignore };
    readonly Control promptHost = new() { MouseFilter = MouseFilterEnum.Ignore };
    KeyTag? cap, promptCap;
    LevelCardSpec? shown;

    public LevelCard()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Visible = false;
        ZIndex = 4;
        AddChild(capHost);
        AddChild(promptHost);
        // (the seats' caps are drawn under the bottom HUD's scale: held at that size here, so the chip matches its seat)
        capHost.Scale = promptHost.Scale = new Vector2(HudBottom.Scale, HudBottom.Scale);
    }

    /// <summary>A card to show (in turn, after any showing).</summary>
    public void Add(LevelCardSpec s) => Queue.Add(s);

    static float TextW(Font f, string s, int size) => f.GetStringSize(s, HorizontalAlignment.Left, -1, size).X;

    /// <summary>A card begins: its words, glyph, chips and size, once.</summary>
    void Begin(LevelCardSpec s)
    {
        shown = s;
        header = LevelCards.Header(s);
        // (the level's stinger, once the card shows: Journey's "Level N" banner, which carried it, is gone in the campaign;
        // a new skill's card that follows its level's key card is the same level-up: it does not ring twice)
        if (s.Kind != LevelCardKind.NewSkill || s.Level > 0) SurvivorUnchained.Sound.Sfx.Stinger("triumph");
        bool body = s.Kind != LevelCardKind.Plain;
        name = line = before = after = measure = "";
        glyph = null;
        if (body && Content.Weapons.All.TryGetValue(s.Skill, out var wd))
        {
            name = wd.Name;
            glyph = Glyphs.Texture(Glyphs.ForSkill(s.Skill, wd.Art), 80, GlyphGold, line: true);
            if (s.Kind != LevelCardKind.LampLit) line = s.Line ?? LevelCards.Line(wd.Description);
        }
        else if (body) name = s.Skill;
        if (s.Kind == LevelCardKind.LampLit) { measure = s.Measure + " "; before = LevelCards.Num(s.Before); after = LevelCards.Num(s.After); }
        prompt = s.HasPrompt ? s.PromptText! : "";

        // the skill's key chip (a new key only), after its name
        float need = W;
        if (s.Kind == LevelCardKind.NewKey && s.Slot >= 0 && s.Slot < KeyMap.Skills.Length)
        {
            cap?.QueueFree();
            cap = new KeyTag(KeyMap.Skills[s.Slot]) { Chip = true };
            capHost.AddChild(cap);
            cap.Refresh();
        }
        else if (cap != null) { cap.QueueFree(); cap = null; }
        float nameW = TextW(Style.Display, name, NameSize);
        if (body)
        {
            float capW = cap != null ? cap.ChipBox().Size.X * HudBottom.Scale + 12 : 0;
            float lineW = s.Kind == LevelCardKind.LampLit
                ? TextW(Style.Ui, measure + before + arrow + after, LineSize)
                : TextW(Style.Ui, line, LineSize);
            need = Math.Max(need, NameX + Math.Max(nameW + capW, lineW) + Pad);
        }
        float headW = TextW(Style.Display, header, HeadSize) + 2 * Pad;
        if (s.HasPrompt)
        {
            promptCap?.QueueFree();
            // On a pad the book's pages have no button of their own (KeyMap.Pad): View opens the book and the bumpers
            // turn to the page, so the cap is View's, never a keyboard's "C" in a pad player's hands (M4 lead 7).
            var pk = s.PromptKey!.Value;
            if (Controls.Instance is { UsingPad: true } ctl && !System.Linq.Enumerable.Any(ctl.PadLabels(pk))) pk = Act.Inventory;
            promptCap = new KeyTag(pk) { Chip = true };
            promptHost.AddChild(promptCap);
            promptCap.Refresh();
            need = Math.Max(need, Pad + promptCap.ChipBox().Size.X * HudBottom.Scale + 10 + TextW(Style.Ui, prompt, PromptSize) + Pad);
        }
        else if (promptCap != null) { promptCap.QueueFree(); promptCap = null; }
        w = Mathf.Ceil(Math.Max(need, headW));
        float bodyTop = 32, promptTop = body ? 88 : 36;
        h = s.HasPrompt ? promptTop + 24 : body ? 86 : 44;
        Size = new Vector2(w, h);
        PivotOffset = Size / 2;
        // the chips, placed in their hosts' (scaled) space: the name's cap on the name's middle, the prompt's on its row
        float k = HudBottom.Scale;
        if (cap != null)
        {
            float cw = cap.ChipBox().Size.X * k;
            cap.Place((NameX + nameW + 12 + cw / 2) / k, (bodyTop + 13 - Instrument.TagH * k / 2) / k);
        }
        if (promptCap != null)
        {
            float pw = promptCap.ChipBox().Size.X * k;
            promptCap.Place((Pad + pw / 2) / k, (promptTop + 9 - Instrument.TagH * k / 2) / k);
        }
        float foot = FootFor(w);
        rest = new Vector2(Mathf.Round(960 - w / 2), Mathf.Round(foot - h));
        GD.Print($"level card: {header} rect ({rest.X:0},{rest.Y:0} {w:0}x{h:0}) foot {foot:0}{(prompt != "" ? $", prompt \"{prompt}\"" : "")}");
        QueueRedraw();
    }

    public override void _Process(double delta)
    {
        bool held = Held();
        Queue.Tick(delta, held);
        if (Queue.Began && Queue.Current != null) Begin(Queue.Current);
        if (Queue.Current == null) { if (Visible) Visible = false; return; }
        if (held) { if (Visible) Visible = false; return; }
        if (Queue.Folding) { fold = FoldTo(Queue.Current) ?? From; OnFold(Queue.Current); }
        Visible = true;
        float kk = (float)Queue.K;
        switch (Queue.Now)
        {
            case LevelCardQueue.Phase.In:
            {
                // rising from the coin: up from 18 px lower, eased out, fading in
                float e = 1 - (1 - kk) * (1 - kk);
                Position = rest + new Vector2(0, 18 * (1 - e));
                Scale = Vector2.One;
                Modulate = Colors.White with { A = e };
                break;
            }
            case LevelCardQueue.Phase.Hold:
                Position = rest; Scale = Vector2.One; Modulate = Colors.White;
                break;
            case LevelCardQueue.Phase.Out:
            {
                // folding toward the seat that opened: drawn in toward it, smaller, gone
                float e = kk * kk;
                var mid = rest + Size / 2;
                Position = rest + (fold - mid) * e;
                Scale = new Vector2(1 - 0.75f * e, 1 - 0.85f * e);
                Modulate = Colors.White with { A = 1 - e };
                break;
            }
        }
    }

    public override void _Draw()
    {
        if (shown == null) return;
        var s = shown;
        // the ground and its two rules (the panel ends cleanly: square, no border, no ornament)
        DrawRect(new Rect2(0, 0, w, h), Ground);
        DrawRect(new Rect2(0, 0, w, 1), Rule);
        DrawRect(new Rect2(0, h - 1, w, 1), Rule);
        // the header, small caps, bone
        DrawString(Style.Display, new Vector2(Pad, 22), header, HorizontalAlignment.Left, -1, HeadSize, Bone);
        if (s.Kind != LevelCardKind.Plain)
        {
            const float top = 32;
            var well = new Rect2(Pad, top + 2, WellD, WellD);
            DrawRect(well, WellInk);
            DrawRect(well, Rule with { A = 0.7f }, false, 1);
            if (glyph != null) DrawTextureRect(glyph, well.Grow(-5), false);
            DrawString(Style.Display, new Vector2(NameX, top + 22), name, HorizontalAlignment.Left, -1, NameSize, Cream);
            if (s.Kind != LevelCardKind.LampLit)
                DrawString(Style.Ui, new Vector2(NameX, top + 44), line, HorizontalAlignment.Left, -1, LineSize, Parch);
            else
            {
                float x = NameX;
                DrawString(Style.Ui, new Vector2(x, top + 44), measure, HorizontalAlignment.Left, -1, LineSize, Parch);
                x += TextW(Style.Ui, measure, LineSize);
                DrawString(Style.Ui, new Vector2(x, top + 44), before, HorizontalAlignment.Left, -1, LineSize, Dim);
                x += TextW(Style.Ui, before, LineSize);
                DrawString(Style.Ui, new Vector2(x, top + 44), arrow, HorizontalAlignment.Left, -1, LineSize, Dim);
                x += TextW(Style.Ui, arrow, LineSize);
                DrawString(Style.UiBold, new Vector2(x, top + 44), after, HorizontalAlignment.Left, -1, LineSize, Cream);
            }
        }
        if (prompt != "" && promptCap != null)
        {
            float promptTop = s.Kind != LevelCardKind.Plain ? 88 : 36;
            float px = Pad + promptCap.ChipBox().Size.X * HudBottom.Scale + 10;
            DrawString(Style.Ui, new Vector2(px, promptTop + 14), prompt, HorizontalAlignment.Left, -1, PromptSize, Parch);
        }
    }
}
