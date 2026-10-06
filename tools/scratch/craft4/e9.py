from ed import sub

sub("src/Ui/Overlay.cs", [
("""    /// <summary>How near the camera comes while this is open (1: as it was).</summary>
    public virtual float CameraNear => 1;""",
"""    /// <summary>How near the camera comes while this is open (1: as it was).</summary>
    public virtual float CameraNear => 1;

    /// <summary>A place on the ground the view looks at while this is open, instead of the survivor
    /// (a counter: the keeper, live in the world between its two panels). Null: the survivor.</summary>
    public virtual (double X, double Z)? CameraLook => null;"""),
])
sub("src/Game/GameMenus.cs", [
("""        cam.ScreenShift = o.CameraShift;
        cam.ScreenNear = o.CameraNear;
        controls.Captured = true;
        hud.Prompt(promptShown = null);
    }""",
"""        cam.ScreenShift = o.CameraShift;
        cam.ScreenNear = o.CameraNear;
        Look(o.CameraLook);
        controls.Captured = true;
        hud.Prompt(promptShown = null);
    }

    bool screenLook;

    /// <summary>The view looks where a screen asks (a counter's keeper), and back at the survivor
    /// when it closes; a cutscene's own framing is never taken from it.</summary>
    void Look((double X, double Z)? at)
    {
        if (at is { } p && scene != null) { cam.FocusOverride = new Godot.Vector3((float)p.X, (float)scene.HeightAt(p.X, p.Z) + 0.8f, (float)p.Z); screenLook = true; }
        else if (screenLook) { cam.FocusOverride = null; screenLook = false; }
    }"""),
("""        zone?.Touched();
        cam.ScreenShift = 0;
        cam.ScreenNear = 1;""",
"""        zone?.Touched();
        cam.ScreenShift = 0;
        cam.ScreenNear = 1;
        Look(null);"""),
])
sub("src/Ui/Forge.cs", [
("""    float RightX => 1920 - 40 - RightW;
""",
"""    float RightX => 1920 - 40 - RightW;

    /// <summary>The crafter live in the world between the panels: the view looks at them, near, and
    /// sets them in the gap (the counters' shape); a crafter not standing here leaves it on the survivor.</summary>
    public override (double X, double Z)? CameraLook => G.Zone?.Actors.TryGetValue(crafter, out var a) == true ? (a!.X, a.Z) : null;
    public override float CameraShift => (40 + LeftW + RightX) / 2 - 960;
    public override float CameraNear => 0.62f;
"""),
])
