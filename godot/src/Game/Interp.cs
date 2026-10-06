using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// Where what moves is drawn, between the fight's steps. The fight steps sixty
/// times a second (WorldScene.Step) and the screen draws at its own rate (the
/// owner's at 164). Drawn straight from the last step, everything that moved
/// stood still for a frame or two and then jumped a whole step, while the
/// camera followed smoothly: at a sprint she shook back and forth on screen by
/// 7 to 10 pixels, and the temporal smoothing, given a new speed for her every
/// frame, threw its history of her away and drew her raw. That was the blur in
/// motion. So each thing is drawn between where it stood a step ago and where
/// it stands now, by how far the clock has run into the next step: smooth at
/// any rate, never more than one step (17 ms) behind.
///
/// A thing that was not there a step ago (just come), or that moved further
/// than anything runs in one step (set down elsewhere), is drawn where it is.
/// </summary>
public sealed class Interp
{
    /// <summary>Off (--no-interp, or flipped by --perf-flip interp): drawn from the last step, as before.</summary>
    public static bool On = true;

    /// <summary>Further than this in one step is a move, not a stride (a dash covers about half a metre).</summary>
    const double Jump = 2.5;

    float blend = 1;
    Battle? of;
    double herX, herZ, herLeap;
    bool herSeen;
    double[] ex = [], ez = [], px = [], pz = [], py = [], kx = [], kz = [];
    bool[] eSeen = [], pSeen = [], kSeen = [];

    /// <summary>How far the clock is into the next step (0..1): what is drawn sits that far from the step before.</summary>
    public float Blend => blend;

    /// <summary>Taken just before the frame's last step: where everything stands a step before what is drawn.</summary>
    public void Before(Battle b)
    {
        if (b != of || ex.Length != b.Enemies.Capacity || px.Length != b.Projectiles.Capacity || kx.Length != b.Pickups.Capacity)
        {
            of = b;
            ex = new double[b.Enemies.Capacity]; ez = new double[ex.Length]; eSeen = new bool[ex.Length];
            px = new double[b.Projectiles.Capacity]; pz = new double[px.Length]; py = new double[px.Length]; pSeen = new bool[px.Length];
            kx = new double[b.Pickups.Capacity]; kz = new double[kx.Length]; kSeen = new bool[kx.Length];
        }
        var p = b.Player;
        herX = p.X; herZ = p.Z; herLeap = LeapK(p); herSeen = true;
        var es = b.Enemies.Items;
        for (int i = 0; i < es.Length; i++) { var e = es[i]; eSeen[i] = e.Alive; ex[i] = e.X; ez[i] = e.Z; }
        var ps = b.Projectiles.Items;
        for (int i = 0; i < ps.Length; i++) { var q = ps[i]; pSeen[i] = q.Alive; px[i] = q.X; pz[i] = q.Z; py[i] = q.Y; }
        var ks = b.Pickups.Items;
        for (int i = 0; i < ks.Length; i++) { var k = ks[i]; kSeen[i] = k.Alive; kx[i] = k.X; kz[i] = k.Z; }
    }

    /// <summary>After the frame's steps: what is left on the clock, as a share of a step.</summary>
    public void After(double left, double step) => blend = On ? (float)System.Math.Clamp(left / step, 0, 1) : 1;

    /// <summary>A new fight, or one set down anew: nothing is drawn from before it.</summary>
    public void Forget() { of = null; herSeen = false; }

    static double LeapK(PlayerState p) => p.Leap is { } l ? System.Math.Min(1, l.T / l.Dur) : -1;

    /// <summary>Where she is drawn, and how far through a leap (-1: not leaping).</summary>
    public (double X, double Z, double Leap) Her(Battle b)
    {
        var p = b.Player;
        double leap = LeapK(p);
        if (!herSeen || b != of) return (p.X, p.Z, leap);
        var (x, z) = Mix(herX, herZ, p.X, p.Z);
        // (A leap begun this step is drawn from its start; one ended, at its landing.)
        if (leap >= 0 && herLeap >= 0) leap = herLeap + (leap - herLeap) * blend;
        return (x, z, leap);
    }

    public (double X, double Z) Of(Enemy e) =>
        of != null && e.Id < eSeen.Length && eSeen[e.Id] ? Mix(ex[e.Id], ez[e.Id], e.X, e.Z) : (e.X, e.Z);

    public (double X, double Y, double Z) Of(Projectile q)
    {
        if (of == null || q.Id >= pSeen.Length || !pSeen[q.Id]) return (q.X, q.Y, q.Z);
        double x0 = px[q.Id], y0 = py[q.Id], z0 = pz[q.Id], dx = q.X - x0, dz = q.Z - z0;
        if (blend >= 1 || dx * dx + dz * dz > Jump * Jump) return (q.X, q.Y, q.Z);
        return (x0 + dx * blend, y0 + (q.Y - y0) * blend, z0 + dz * blend);
    }

    public (double X, double Z) Of(Pickup k) =>
        of != null && k.Id < kSeen.Length && kSeen[k.Id] ? Mix(kx[k.Id], kz[k.Id], k.X, k.Z) : (k.X, k.Z);

    (double, double) Mix(double x0, double z0, double x1, double z1)
    {
        double dx = x1 - x0, dz = z1 - z0;
        if (blend >= 1 || dx * dx + dz * dz > Jump * Jump) return (x1, z1);
        return (x0 + dx * blend, z0 + dz * blend);
    }
}
