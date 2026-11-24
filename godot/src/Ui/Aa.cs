using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// Antialiased canvas line width compensation. Godot 4.6+ draws antialiased lines thinner than 4.5.1:
/// before drawing, the engine replaces width w with comp(w) = w/2 (w &lt;= 2.5), 0.2*w*w - 0.25*w + 0.625
/// (2.5 &lt; w &lt;= 5), w - 0.625 (above 5); source: servers/rendering/renderer_canvas_cull.cpp,
/// canvas_item_get_compensated_antialiasing_width. The HUD was tuned on 4.5.1, so W returns the inverse.
/// To remove the compensation later, make W return its argument.
/// </summary>
public static class Aa
{
    static readonly bool Active = Check();

    static bool Check()
    {
        var v = Engine.GetVersionInfo();
        int major = (int)v["major"];
        int minor = (int)v["minor"];
        return major > 4 || minor >= 6;
    }

    public static float W(float width)
    {
        if (!Active || width <= 0f) return width;
        if (width <= 1.25f) return 2f * width;
        if (width <= 4.375f) return (0.25f + Mathf.Sqrt(0.8f * width - 0.4375f)) / 0.4f;
        return width + 0.625f;
    }
}
