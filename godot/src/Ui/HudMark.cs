using System;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/// <summary>hud24 r2: a hostile marked attack still to land, with what is needed to ask "is this ground inside its damage
/// footprint?" (the HUD statues fade for the area of them it hides, not for a graze). Circle: within Radius; Ring:
/// between Inner and Radius; Cone: within Radius and Arc/2 of Angle; Line: within half Width of the segment.</summary>
public sealed class HudMark
{
    public TelegraphShape Shape;
    public double X, Z, X1, Z1, Radius, Inner, Width, Angle, Arc, Until;
    public string Name = "";

    public HudMark(Ev.Telegraph t, double until)
    {
        Shape = t.Shape; X = t.X; Z = t.Z; X1 = t.X1 ?? t.X; Z1 = t.Z1 ?? t.Z; Radius = t.Radius; Inner = t.Inner;
        Width = t.Width ?? 1; Angle = t.Angle ?? 0; Arc = t.Arc ?? Math.PI / 2; Until = until;
        Name = t.Label ?? t.Shape.ToString().ToLowerInvariant();
    }

    /// <summary>Is the ground point (x, z) inside the blow's damage footprint?</summary>
    public bool Covers(double x, double z)
    {
        double dx = x - X, dz = z - Z;
        switch (Shape)
        {
            case TelegraphShape.Line:
            {
                double sx = X1 - X, sz = Z1 - Z, l2 = sx * sx + sz * sz;
                double t = l2 < 1e-9 ? 0 : Math.Clamp((dx * sx + dz * sz) / l2, 0, 1);
                double px = dx - sx * t, pz = dz - sz * t;
                double hw = Width / 2;
                return px * px + pz * pz <= hw * hw;
            }
            case TelegraphShape.Cone:
            {
                if (dx * dx + dz * dz > Radius * Radius) return false;
                double da = Math.Atan2(dz, dx) - Angle;
                da -= 2 * Math.PI * Math.Floor((da + Math.PI) / (2 * Math.PI));
                return Math.Abs(da) <= Arc / 2;
            }
            default:
            {
                double d2 = dx * dx + dz * dz;
                return d2 <= Radius * Radius && (Shape != TelegraphShape.Ring || d2 >= Inner * Inner);
            }
        }
    }
}
