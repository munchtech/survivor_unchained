using Godot;

namespace SurvivorUnchained.Play;

/// <summary>(aim-move) The facing mode's dev key (F7) and the cursor point her view faces.</summary>
public partial class Game
{
    const Godot.Key FacingKey = Godot.Key.F7;

    public override void _UnhandledKeyInput(InputEvent e)
    {
        if (e is InputEventKey { Pressed: true, Echo: false, Keycode: FacingKey })
        {
            var name = Facing.Toggle();
            hud?.Toast(new Toast(ToastKind.World, "FACING MODE " + name.ToUpperInvariant(), name == "always" ? "she faces the cursor" : "she faces her travel; the cursor on a skill", null, null, 1.6));
            GetViewport().SetInputAsHandled();
        }
    }

    /// <summary>What her view faces: the cursor's ground point. None under the autopilot (bots behave as before), and none in a
    /// tool's run unless the script gives one (--press, --dirrun): a shot has no real mouse.</summary>
    (double X, double Z)? FacePointer()
    {
        if (auto != null || scene == null) return null;
        if (Args.Tool && !Args.Has("press") && !Args.Has("dirrun")) return null;
        return scene.Pointer();
    }
}
