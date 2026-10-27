using System;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play;

/// <summary>
/// The close view's room (FollowCamera.Place, GameCloseUp's ray): what may push the near camera in toward her. Only
/// something the line from her to the lens truly passes through: a wall, a house, a stall's roof. A post, a lamp, a
/// trunk or a barrel (a footprint no wider than ThinR) is seen past as it slides by, unless the lens itself would stand
/// in it; anything whose drawn top lies below the line where it crosses (a crate, a cart, a fence, a heap) is passed
/// over. The room then glides (Step): in log distance, eased and with a top speed, so no frame jumps.
/// </summary>
public static class CameraRoom
{
    /// <summary>A footprint this narrow or less (a circle's radius, a box's half width) is a post, not a wall (m).</summary>
    public const double ThinR = 0.75;
    /// <summary>How far above a thing's top the line must pass to clear it (m).</summary>
    public const double Clear = 0.3;

    /// <summary>Is the collider in the way at fraction t of the line from her (aimY) to the lens (lensY)?
    /// top: its drawn top (world y), null where nothing drawn was found (then it is a wall, as before).</summary>
    public static bool Blocks(Collider c, double t, double aimY, double lensY, double? top)
    {
        bool thin = c.Kind == ColliderKind.Circle ? c.R <= ThinR : Math.Min(c.Hw, c.Hd) <= ThinR && Math.Max(c.Hw, c.Hd) <= ThinR;
        if (thin && t < 0.999) return false;
        if (top is not double y) return true;
        return aimY + (lensY - aimY) * t < y + Clear;
    }

    /// <summary>In toward a nearer room: eased at InRate, at most InMax of log distance a second; back out slower.</summary>
    public const float InRate = 8, InMax = 2f, OutRate = 2.5f, OutMax = 1f;

    /// <summary>The room (a fraction of the wanted distance, 0..1] one frame on toward free.</summary>
    public static float Step(float room, float free, float dt)
    {
        double lr = Math.Log(Math.Max(room, 1e-3)), lf = Math.Log(Math.Clamp(free, 1e-3, 1));
        bool inward = lf < lr;
        double step = (lf - lr) * (1 - Math.Exp(-(inward ? InRate : OutRate) * dt)), cap = (inward ? InMax : OutMax) * dt;
        return (float)Math.Exp(lr + Math.Clamp(step, -cap, cap));
    }
}
