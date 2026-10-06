"""The fall darkens the world, not the HUD's choices (run from godot/)."""
p = "src/Game/GameFall.cs"
s = open(p, encoding="utf-8").read()
reps = [
("""using System;
using SurvivorUnchained.Ui;""", """using System;
using Godot;
using SurvivorUnchained.Ui;"""),
("""    Action? fallRise, fallLetGo;
""", """    Action? fallRise, fallLetGo;
    /// <summary>The world darkened under the fall's choices: its own layer, between the world and
    /// the HUD, so the choices stay bright (the screen's fade sat over them).</summary>
    CanvasLayer? fallLayer;
    TextureRect? fallShade;

    void ShadeWorld(float to, double seconds)
    {
        if (fallShade == null)
        {
            fallLayer = new CanvasLayer { Layer = 5 };
            AddChild(fallLayer);
            // Dark at the edges, a little light left round her: the eye goes to where she lies.
            fallShade = new TextureRect
            {
                ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = Control.MouseFilterEnum.Ignore,
                Texture = new GradientTexture2D
                {
                    Gradient = new Gradient { Colors = [new Color(0.02f, 0.01f, 0.02f, 0.35f), new Color(0.02f, 0.01f, 0.02f, 0.55f), new Color(0.01f, 0.0f, 0.01f, 0.88f)], Offsets = [0f, 0.3f, 1f] },
                    Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1.05f, 0.5f), Width = 256, Height = 256,
                },
                Size = new Vector2(1920, 1080), Modulate = Colors.Transparent,
            };
            fallLayer.AddChild(fallShade);
        }
        var tw = CreateTween();
        tw.TweenProperty(fallShade, "modulate:a", to, Math.Max(0.01, seconds));
    }
"""),
("""        hud.Prompt(promptShown = null);
        hud.Fade(0.55f, 0.9);
        if (risesLeft <= 0)
        {
            // No rise left: the night is lost, and the fall says so on its own.
            Wait(1.6, () => { hud.Fade(0, 0.6); letGo(); });
            return;
        }""", """        hud.Prompt(promptShown = null);
        ShadeWorld(1, 0.9);
        if (risesLeft <= 0)
        {
            // No rise left: the night is lost, and the fall says so on its own.
            Wait(1.6, () => { ShadeWorld(0, 0.6); letGo(); });
            return;
        }"""),
("""        else if (a is Act.Cancel) { var l = fallLetGo; EndFall(); hud.Fade(0, 0.6); l?.Invoke(); }""",
 """        else if (a is Act.Cancel) { var l = fallLetGo; EndFall(); ShadeWorld(0, 0.6); l?.Invoke(); }"""),
("""        hud.Fade(1, 0.45);
        Wait(0.5, () =>
        {
            rise();
            hud.Fade(0, 1.0);
        });""", """        hud.Fade(1, 0.45);
        Wait(0.5, () =>
        {
            ShadeWorld(0, 0.01);
            rise();
            hud.Fade(0, 1.0);
        });"""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
