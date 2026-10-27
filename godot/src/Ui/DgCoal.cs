using System;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 17, The Drowned Girl (--hud drowned), piece 4: the Flare as a live coal held in the river's eddy, in place
/// of the art's glass (Vessel.Coal). A painted coal (art/ui/dg_river/coal_map.png, tools/uiforge/dg_coal.py) under
/// shaders/hud_dg_coal.gdshader: the heat rises from its foot as the meter fills; full, it blazes and breathes;
/// a press (the meter falling from full) flares it out, white-hot with a ring of light thrown over the river, and
/// it goes dark to refill. Its rect is the coal's and the room its light needs (Ext coal radii each way).
/// </summary>
public partial class DgCoal : ColorRect
{
    public const float Ext = 2.6f;
    static readonly StringName ULevel = "level", UBurst = "burst";
    readonly ShaderMaterial mat;
    /// <summary>The meter, 0 to 1 (the art's level).</summary>
    public float Level;
    float shown = -1, burst = -1, held;

    public DgCoal()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        ProcessMode = ProcessModeEnum.Always;
        float r = DgRiver.FlareR;
        Size = Vector2.One * 2 * r * Ext;
        mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_dg_coal.gdshader") };
        if (UiArt.Tex("dg_river/coal_map.png") is { } map) mat.SetShaderParameter("coal", map);
        else GD.PushError("DgCoal: dg_river/coal_map.png did not load: the coal draws blank");
        mat.SetShaderParameter("ext", Ext);
        mat.SetShaderParameter("px", r);
        Material = mat;
        Color = Colors.White;
    }

    public override void _Process(double delta)
    {
        float dt = Math.Min((float)delta, 0.1f);
        // a press: the meter drops from full (held full for a moment first, so a pin or a load does not count)
        if (held > 0.2f && Level < shown - 0.3f) burst = 0;
        held = Level >= 0.98f ? held + dt : 0;
        if (burst >= 0) { burst += dt; if (burst > 2.2f) burst = -1; mat.SetShaderParameter(UBurst, burst); }
        if (Level != shown) { shown = Level; mat.SetShaderParameter(ULevel, Level); }
    }
}
