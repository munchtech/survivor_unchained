using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>The card over the game's opening (lane K; the owner, 19 Nov 2026: "lets add a compiling shaders load bar when we
/// open the game so that it dosn't lag while playing.  lets also make the title screen much faster."): drawn from the first
/// frame, a bar that moves while the title's place is built behind it, the creator's figure is dressed, and (on a first launch
/// on this machine, or a new build) the renderer's pipelines are compiled for what play shows first; then it fades onto the
/// title. Its steps are the caller's: each yield is one frame drawn with that label and share (0..1) done.</summary>
public sealed partial class BootLoad : CanvasLayer
{
    public readonly record struct Step(string Label, float Done);

    const string MarkFile = "user://warm.json";

    readonly IEnumerator<Step> steps;
    readonly Action done;
    ColorRect back = null!, fill = null!;
    Label line = null!;
    float shown, target, fade = -1;
    ulong startedUsec;

    public BootLoad(IEnumerable<Step> steps, Action done)
    {
        this.steps = steps.GetEnumerator();
        this.done = done;
        Layer = 120;
        ProcessMode = ProcessModeEnum.Always;
    }

    /// <summary>The pipelines this build has not compiled on this machine yet: no mark, or a mark of another build or card.</summary>
    public static bool FirstLaunch => !FileAccess.FileExists(MarkFile) || FileAccess.GetFileAsString(MarkFile) != MarkText();

    public static void MarkWarm()
    {
        using var f = FileAccess.Open(MarkFile, FileAccess.ModeFlags.Write);
        f?.StoreString(MarkText());
    }

    static string MarkText()
    {
        string sha = FileAccess.FileExists("res://data/build.json") ? FileAccess.GetFileAsString("res://data/build.json").Trim() : "dev";
        return $"{{ \"build\": {sha}, \"adapter\": \"{RenderingServer.GetVideoAdapterName()}\", \"api\": \"{RenderingServer.GetVideoAdapterApiVersion()}\" }}";
    }

    public override void _Ready()
    {
        startedUsec = Time.GetTicksUsec();
        GD.Print($"load: the opening card up {Time.GetTicksMsec() / 1000.0:0.00} s since the engine began");
        back = new ColorRect { Color = new Color(0.035f, 0.03f, 0.045f, 1), MouseFilter = Control.MouseFilterEnum.Stop };
        back.SetAnchorsPreset(Control.LayoutPreset.FullRect);
        AddChild(back);
        var title = new Label { Text = "SURVIVOR UNCHAINED", HorizontalAlignment = HorizontalAlignment.Center };
        title.AddThemeFontOverride("font", Style.Display);
        title.AddThemeFontSizeOverride("font_size", Style.Heading);
        title.AddThemeColorOverride("font_color", Style.Gold);
        title.SetAnchorsPreset(Control.LayoutPreset.Center);
        title.AnchorLeft = 0; title.AnchorRight = 1; title.OffsetLeft = 0; title.OffsetRight = 0;
        title.OffsetTop = -78; title.OffsetBottom = -30;
        back.AddChild(title);
        // the bar: a hairline track and its fill, 420 px at 1080p
        var track = new ColorRect { Color = new Color(Style.GoldDim, 0.35f) };
        track.SetAnchorsPreset(Control.LayoutPreset.Center);
        track.OffsetLeft = -210; track.OffsetRight = 210; track.OffsetTop = -1; track.OffsetBottom = 2;
        back.AddChild(track);
        fill = new ColorRect { Color = Style.GoldHi, Size = new Vector2(0, 3) };
        track.AddChild(fill);
        line = new Label { HorizontalAlignment = HorizontalAlignment.Center };
        line.AddThemeFontOverride("font", Style.Text);
        line.AddThemeFontSizeOverride("font_size", Style.Small);
        line.AddThemeColorOverride("font_color", Style.InkDim);
        line.SetAnchorsPreset(Control.LayoutPreset.Center);
        line.AnchorLeft = 0; line.AnchorRight = 1; line.OffsetLeft = 0; line.OffsetRight = 0;
        line.OffsetTop = 16; line.OffsetBottom = 44;
        back.AddChild(line);
    }

    public override void _Process(double delta)
    {
        if (fade >= 0)
        {
            fade += (float)delta;
            back.Modulate = new Color(1, 1, 1, Mathf.Clamp(1 - fade / 0.5f, 0, 1));
            if (fade >= 0.5f) QueueFree();
            return;
        }
        shown = Mathf.MoveToward(shown, target, (float)delta * 1.6f);
        if (shown < target) shown = Mathf.Lerp(shown, target, 1 - Mathf.Exp(-12 * (float)delta));
        fill.Size = new Vector2(420 * shown, 3);
        // (one step a frame: the card is drawn between them, so the bar moves while the work behind it is done)
        if (!steps.MoveNext())
        {
            GD.Print($"load: the opening card done in {(Time.GetTicksUsec() - startedUsec) / 1e6:0.00} s ({Time.GetTicksMsec() / 1000.0:0.00} s since the engine began)");
            fill.Size = new Vector2(420, 3);
            fade = 0;
            done();
            return;
        }
        var s = steps.Current;
        if (s.Label != "") line.Text = s.Label;
        target = Mathf.Clamp(s.Done, target, 1);
    }
}
