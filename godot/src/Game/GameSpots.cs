using System;
using System.Globalization;
using Godot;

namespace SurvivorUnchained.Play;

/// <summary>
/// --spots "x,z[,c[,f]][;...]" --spots-every S --spots-from T: pictures of fixed places in one run (the look
/// bible's measured positions). She is set down at each place in turn, T seconds in and every S after (put
/// --seconds at T + 3 and --every at S, so each frame lands once the camera has settled), kept whole, and with
/// c given the close view held at that level wherever she is (1: the nearest) and the dead kept out of it, with f her facing in degrees (0: to the camera). A switch for pictures only.
/// </summary>
public partial class Game
{
    (double X, double Z, float? Close, double? Facing)[]? spotList;
    int spotAt = -1;
    double spotT;
    /// <summary>The close view the spots hold at this stop, or none.</summary>
    float? spotClose;

    void Spots(double dt)
    {
        if (Args.Get("spots") is not string spec || Battle is not { } b) return;
        spotList ??= Array.ConvertAll(spec.Split(';', StringSplitOptions.RemoveEmptyEntries), s =>
        {
            var p = s.Split(',');
            double N(int i) => double.Parse(p[i], CultureInfo.InvariantCulture);
            return (N(0), N(1), p.Length > 2 && p[2] != "" ? (float?)N(2) : null, p.Length > 3 ? N(3) * Math.PI / 180 : (double?)null);
        });
        // (On the pictures' clock, so each stop and its frame keep step however long the load took.)
        spotT = Shots.Clock;
        double from = Args.Num("spots-from", 2), every = Args.Num("spots-every", 6);
        int k = spotT < from ? -1 : Math.Min(spotList.Length - 1, (int)((spotT - from) / every));
        b.Player.Hp = b.MaxHp;
        // --spots-unshadowed: the key casts none (its frames against the shadowed ones measure how much ground its shadows cover).
        if (Args.Has("spots-unshadowed") && air.Key.ShadowEnabled) air.Key.ShadowEnabled = false;
        // At a close stop the dead are held off out of the picture (the close view of her face, not of a fight).
        // --spots-clear: the living held off at every stop, from the start (a still place: a lamp's pool, no fight in it).
        if (spotClose != null && k == spotAt || Args.Has("spots-clear"))
            foreach (var e in b.Enemies.Living())
                if (Math.Abs(e.X - b.Player.X) < 70 && Math.Abs(e.Z - b.Player.Z) < 70) { e.X = b.Player.X + 75; e.Vx = e.Vz = 0; }
        if (k == spotAt || k < 0) return;
        spotAt = k;
        var (x, z, c, f) = spotList[k];
        b.Player.X = x; b.Player.Z = z; b.Player.Vx = b.Player.Vz = 0;
        if (f is double fa) { b.Player.Facing = fa; scene?.Player?.Face((float)fa, new Vector3((float)x, (float)(scene?.HeightAt(x, z) ?? 0), (float)z)); }
        spotClose = c;
        cam.Snap((float)x, (float)(scene?.HeightAt(x, z) ?? 0), (float)z);
    }
}
