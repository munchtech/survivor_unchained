using System;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 27: the bottom HUD's size knob (data/content/hud.json "bottomScale", 1 = the art's 1080 px; a run's
/// --hud-scale S overrides it for pictures). The whole bottom HUD (Instrument: her figure, the bar, the seats, the
/// coin, the keeper and the Flare's glass, the chips, tags and numbers) draws scaled by it about the screen's bottom
/// middle (Pivot). Everything placed by the art's geo is in the unscaled 1080 px (DgPanel, Instrument); what reads
/// them in screen px (callouts, the threat fade's behind-tests, the numbers' and barks' HUD top, the ground's keep-out)
/// goes through Map, and a screen point back through Unmap.
/// </summary>
public static class HudBottom
{
    static float? scale;
    public static float Scale => scale ??= Load();
    public static readonly Vector2 Pivot = new(960, 1080);
    public static bool Scaled => Math.Abs(Scale - 1) > 1e-4f;

    static float Load()
    {
        float s = 1;
        try
        {
            using var d = System.Text.Json.JsonDocument.Parse(SurvivorUnchained.Core.Json.ReadContent("hud.json"));
            if (d.RootElement.TryGetProperty("bottomScale", out var v) && v.TryGetSingle(out var f)) s = f;
        }
        catch (Exception e) { GD.PushWarning($"HudBottom: hud.json bottomScale unread ({e.Message}): 1"); }
        s = Args.Num("hud-scale", s);
        return Math.Clamp(s, 0.5f, 1.5f);
    }

    /// <summary>The node transform that draws the 1080 px bottom HUD at Scale about Pivot.</summary>
    public static void Apply(Control c)
    {
        c.Scale = new Vector2(Scale, Scale);
        c.Position = Pivot * (1 - Scale);
    }
    public static Vector2 Map(Vector2 p) => Pivot + (p - Pivot) * Scale;
    public static Rect2 Map(Rect2 r) => new(Map(r.Position), r.Size * Scale);
    public static float MapY(float y) => Pivot.Y + (y - Pivot.Y) * Scale;
    public static float MapX(float x) => Pivot.X + (x - Pivot.X) * Scale;
    public static Vector2 Unmap(Vector2 p) => Pivot + (p - Pivot) / Scale;
    public static float UnmapX(float x) => Pivot.X + (x - Pivot.X) / Scale;
    /// <summary>A control's rect on the screen with every parent's scale (GetGlobalRect keeps the unscaled size).</summary>
    public static Rect2 GlobalRect(Control c) => c.GetGlobalTransform() * new Rect2(Vector2.Zero, c.Size);
}
