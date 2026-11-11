using System;
using System.Text.Json;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Sim;

/* Her pace while a press's cast plays, by the angle between her travel and the press's aim (A1 lead 19, main's ruling).
 * Within Cone degrees of the aim: the forward share (the block's Fwd, else the record's Walk) of her speed. At 90 degrees: at
 * most Side m/s. At 180: at most Back m/s. In between the cap is blended by smoothstep: Cone..90 from the forward speed to
 * Side, 90..180 from Side to Back. The caps are caps: final = min(forward-share speed, the cap), so a slowed base never
 * speeds up. Data: data/content/cast_move.json {"castMove": {...}} is the default; a press record's own "castMove" overrides
 * it. No block anywhere (the file's key absent, or "castMove": null): exactly the old Walk share. */

/// <summary>The cast-move block: fwd (share override; absent = the record's Walk), side and back (m/s caps), cone (degrees).</summary>
public sealed class CastMoveDef
{
    public double? Fwd;
    public double Side = 0.95, Back = 1.3, Cone = 45;
}

public sealed class CastMoveFile { public CastMoveDef? CastMove; }

public static class CastMove
{
    static CastMoveFile? file;
    /// <summary>The global default block (data/content/cast_move.json), null when absent.</summary>
    public static CastMoveDef? Default
    {
        get
        {
            if (file == null)
            {
                try { file = JsonSerializer.Deserialize<CastMoveFile>(Json.ReadContent("cast_move.json"), Json.Options) ?? new(); }
                catch (Exception) { file = new(); }
            }
            return file.CastMove;
        }
    }

    /// <summary>Test hook: replace the global default (null = absent).</summary>
    internal static void SetDefault(CastMoveDef? d) => file = new CastMoveFile { CastMove = d };

    static double Smooth(double t) { t = Math.Clamp(t, 0, 1); return t * t * (3 - 2 * t); }

    /// <summary>Her speed during a cast. (mx, mz): travel direction (any length; zero = standing: the forward speed);
    /// (ax, az): the aim direction (zero length: unknown, forward speed); baseSpeed: her speed before the cast's share;
    /// walk: the record's share; block null: baseSpeed * walk.</summary>
    public static double Speed(double mx, double mz, double ax, double az, double baseSpeed, double walk, CastMoveDef? block)
    {
        if (block?.Fwd is { } f) walk = f;
        double fwd = baseSpeed * walk;
        if (block == null) return fwd;
        double ml = Math.Sqrt(mx * mx + mz * mz), al = Math.Sqrt(ax * ax + az * az);
        if (ml < 1e-6 || al < 1e-6) return fwd;
        double ang = Math.Acos(Math.Clamp((mx * ax + mz * az) / (ml * al), -1, 1)) * 180 / Math.PI;
        if (ang <= block.Cone) return fwd;
        double cap = ang <= 90
            ? fwd + (block.Side - fwd) * Smooth((ang - block.Cone) / Math.Max(1e-6, 90 - block.Cone))
            : block.Side + (block.Back - block.Side) * Smooth((ang - 90) / 90);
        return Math.Min(fwd, cap);
    }
}
