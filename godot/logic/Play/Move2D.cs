using System;
using System.Globalization;

namespace SurvivorUnchained.Play;

/// <summary>
/// Her 2D move node's input (A1 motion lead 19): her velocity in HER FACING frame, and the --act-walk argument.
/// Convention: x = to her RIGHT (negative: her left), y = forward, both m/s. Yaw is Godot's node yaw: she faces
/// (sin yaw, cos yaw) in the world's (x, z), so yaw 0 faces +Z and her left is +X.
/// The 2D node's points (PlayerView): idle (0,0); walk (0,+Vwalk); back (0,-Vwalk); left (-Vwalk,0); right (+Vwalk,0);
/// run (0,+Vrun); sprint (0,+Vsprint).
/// </summary>
public static class Move2D
{
    /// <summary>The world velocity (vx, vz) in the frame of her yaw: (right, forward).</summary>
    public static (float X, float Y) Local(float vx, float vz, float yaw)
    {
        float s = MathF.Sin(yaw), c = MathF.Cos(yaw);
        return (-vx * c + vz * s, vx * s + vz * c);
    }

    /// <summary>The inverse: a local (right, forward) velocity as the world's (vx, vz) for her yaw.</summary>
    public static (float X, float Z) World(float right, float forward, float yaw)
    {
        float s = MathF.Sin(yaw), c = MathF.Cos(yaw);
        return (right * -c + forward * s, right * s + forward * c);
    }

    /// <summary>--act-walk DEG,SPEED: DEG from her facing (0 forward, 180 back, 90 her left, -90 her right), SPEED m/s.
    /// Null when absent or not two numbers (or a negative speed).</summary>
    public static (double Deg, double Speed)? ParseActWalk(string? s)
    {
        if (string.IsNullOrWhiteSpace(s)) return null;
        var p = s.Split(',');
        if (p.Length != 2) return null;
        if (!double.TryParse(p[0], NumberStyles.Float, CultureInfo.InvariantCulture, out var d)
            || !double.TryParse(p[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var v) || v < 0
            || double.IsNaN(d) || double.IsNaN(v) || double.IsInfinity(d) || double.IsInfinity(v)) return null;
        return (d, v);
    }

    /// <summary>The world velocity an --act-walk asks, for her yaw (the facing stays put).</summary>
    public static (float X, float Z) ActWalkWorld((double Deg, double Speed) w, float yaw)
    {
        double r = w.Deg * Math.PI / 180;
        // local: left is -x (right is +x), so 90 deg (her left) is (-speed, 0)
        return World((float)(-Math.Sin(r) * w.Speed), (float)(Math.Cos(r) * w.Speed), yaw);
    }
}
