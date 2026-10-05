using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Story;

/* The levy (docs/design/STORY_BOSSES.md 2): pikes in a locked line, marching
 * in step at her, the way they were taught for a town that is gone. Locked
 * shields are not targets (a living wall: 0.5). The men at its two ends are,
 * and breaking one makes the next an end, so area and a blade work it from
 * the ends in. Its front is pikes levelled: walk into it and it shoves her
 * back. It wavers when whoever it follows is hurt hard, and breaks when he
 * falls: the men in it become what they are without it, and back off.
 *
 * The camp's yard (the Pike-Captain behind it) and Redcowl's second phase (his
 * own levy, out of the carts under the old red standard) both use it. */
public sealed class Levy
{
    readonly IStoryArena A;
    Battle B => A.B;

    sealed class Man
    {
        public required Enemy E;
        public double Seed;
        public int Slot;
    }
    readonly List<Man> men = new();

    /// <summary>The line's middle, and the way it faces (and marches).</summary>
    public double X, Z, Fx, Fz;
    /// <summary>Across the line, its right hand.</summary>
    double Sx => -Fz;
    double Sz => Fx;
    int slots;
    const double Spacing = 1.5, StepEvery = 1.3, StepLength = 1.1, Front = 1.8;
    double stepT = 2.2, waverT, shoveT, biteGrace, drawT;
    readonly string? caller;
    int steps;
    /// <summary>Its front's mark (one id a line, so the view moves it rather than adds one).</summary>
    readonly int mark = 890000 + next++ % 9000;
    static int next;

    /// <summary>How quickly it wheels to follow her (radians a second): it stops while it wavers.</summary>
    public double Wheel = 0.35;
    public bool Broken { get; private set; }
    public int Standing => men.Count(Here);
    public int Formed { get; }

    /// <param name="caller">Who calls the step ("Level! ...Step! ...Step!"), if anyone is named.</param>
    public Levy(IStoryArena a, double x, double z, double toX, double toZ, int n, string def = "levy_pike", string? caller = null)
    {
        A = a;
        this.caller = caller;
        X = x; Z = z;
        double dx = toX - x, dz = toZ - z, d = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz));
        Fx = dx / d; Fz = dz / d;
        slots = n;
        for (int k = 0; k < n; k++)
        {
            var (sx, sz) = SlotAt(k);
            var e = A.Spawn(def, sx, sz, false, SpawnStyle.Walk);
            if (e == null) continue;
            var m = new Man { E = e, Seed = e.Seed, Slot = k };
            men.Add(m);
            e.Scripted = true;
            e.Disposition = Disposition.Neutral;
            A.Script(e, (_, dt) => Keep(m, dt));
        }
        Formed = men.Count;
        Ends();
    }

    (double X, double Z) SlotAt(int k)
    {
        double off = (k - (slots - 1) / 2.0) * Spacing;
        return (X + Sx * off, Z + Sz * off);
    }

    static bool Here(Man m) => m.E.Alive && m.E.Seed == m.Seed && m.E.State != EnemyState.Dying;

    /// <summary>The men at its two ends are targets; the rest are locked.</summary>
    void Ends()
    {
        var up = men.Where(Here).ToList();
        if (up.Count == 0) return;
        int lo = up.Min(m => m.Slot), hi = up.Max(m => m.Slot);
        foreach (var m in up)
        {
            bool end = m.Slot == lo || m.Slot == hi;
            if (end && m.E.Disposition != Disposition.Hostile) { m.E.Disposition = Disposition.Hostile; m.E.Target = -1; }
            else if (!end) { m.E.Disposition = Disposition.Neutral; m.E.Provoked = false; }
        }
    }

    /// <summary>A man of the line at his place in it, facing where it marches.</summary>
    bool Keep(Man m, double dt)
    {
        if (Broken) return false;
        var e = m.E;
        var (tx, tz) = SlotAt(m.Slot);
        double dx = tx - e.X, dz = tz - e.Z, d = Math.Sqrt(dx * dx + dz * dz);
        double step = Math.Min(d, 4.5 * dt);
        if (d > 0.05) { e.X += dx / d * step; e.Z += dz / d * step; }
        e.Vx = e.Vz = 0;
        e.Facing = Math.Atan2(Fz, Fx);
        e.Anim = d > 0.3 ? EnemyAnim.Move : EnemyAnim.Idle;
        if (e.State is not (EnemyState.Stunned or EnemyState.Dying)) e.State = EnemyState.Active;
        return true;
    }

    /// <summary>Each step of the fight: the step itself, the wheel toward her, and the front's pikes.</summary>
    public void Step(double dt)
    {
        if (Broken) return;
        men.RemoveAll(m => !Here(m));
        if (men.Count <= 1) { Break(); return; }
        Ends();
        var p = B.Player;
        // It wheels to follow her, slowly: a line turns as one man.
        double want = Math.Atan2(p.Z - Z, p.X - X), now = Math.Atan2(Fz, Fx);
        double turn = waverT > 0 ? 0 : Math.Clamp(Wrap(want - now), -Wheel * dt, Wheel * dt);
        Fx = Math.Cos(now + turn); Fz = Math.Sin(now + turn);
        waverT -= dt;
        if (waverT <= 0 && (stepT -= dt) <= 0)
        {
            stepT = StepEvery;
            double nx = X + Fx * StepLength, nz = Z + Fz * StepLength;
            // It halts at the place's edge (and at her: it pushes, it does not trample).
            double toHer = (p.X - X) * Fx + (p.Z - Z) * Fz;
            if (A.Place.Inside(nx, nz, 1.5) && toHer > Front + 0.5) { X = nx; Z = nz; }
            if (caller != null && steps++ % 4 == 0) A.Bark(X - Fx * 2, Z - Fz * 2, steps == 1 ? "Level! ...Step! ...Step!" : "Step!", caller);
        }
        // The front: pikes levelled. Walked into, it shoves her back, and bites now and then.
        double rx = p.X - X, rz = p.Z - Z, along = rx * Fx + rz * Fz, across = rx * Sx + rz * Sz;
        double half = (slots - 1) / 2.0 * Spacing + 0.6;
        shoveT -= dt;
        biteGrace -= dt;
        if (Math.Abs(across) <= half && along > -0.6 && along < Front && shoveT <= 0)
        {
            shoveT = 0.5;
            var pike = men[0].E;
            B.ShovePlayer(Fx, Fz, 2.2, biteGrace <= 0 ? pike.Damage * 0.8 : 0, "the levy's pikes");
            if (biteGrace <= 0) biteGrace = 1.5;
        }
        if ((drawT -= dt) <= 0)
        {
            drawT = 0.5;
            double ex = X + Fx * Front * 0.6, ez = Z + Fz * Front * 0.6;
            B.Events.Emit(new Ev.Telegraph { Id = mark, Shape = TelegraphShape.Line, Kind = TelegraphKind.Wall,
                X = ex - Sx * half, Z = ez - Sz * half, X1 = ex + Sx * half, Z1 = ez + Sz * half, Width = Front, Duration = 0.6, Hostile = true });
        }
    }

    /// <summary>Whoever it follows is hurt hard: it stops a moment, and its men look to him.</summary>
    public void Waver(double seconds)
    {
        if (Broken || waverT > 0.5) return;
        waverT = seconds;
        A.Bark(X, Z, "The line wavers.", null);
    }

    /// <summary>Broken: the men in it become what they are without it, and back off a moment.</summary>
    public void Break()
    {
        if (Broken) return;
        Broken = true;
        foreach (var m in men.Where(Here))
        {
            m.E.Scripted = false;
            m.E.Disposition = Disposition.Hostile;
            m.E.Target = -1;
            m.E.Status[StatusKind.Fear] = new StatusSlot(2.5, 1, 1, 0);
        }
    }

    /// <summary>Does the way from one point to another cross the line (its men's span)?</summary>
    public bool Between(double ax, double az, double bx, double bz)
    {
        if (Broken || men.Count == 0) return false;
        double half = (slots - 1) / 2.0 * Spacing + 0.6;
        double a = (ax - X) * Fx + (az - Z) * Fz, b = (bx - X) * Fx + (bz - Z) * Fz;
        if (Math.Sign(a) == Math.Sign(b)) return false;
        double t = a / (a - b);
        double cx = ax + (bx - ax) * t, cz = az + (bz - az) * t;
        return Math.Abs((cx - X) * Sx + (cz - Z) * Sz) <= half;
    }

    /// <summary>The way round it: past its nearer end, a little behind it.</summary>
    public (double X, double Z) Round(double px, double pz)
    {
        double half = (slots - 1) / 2.0 * Spacing + 2.5;
        double side = (px - X) * Sx + (pz - Z) * Sz >= 0 ? 1 : -1;
        return (X + Sx * half * side - Fx * 1.5, Z + Sz * half * side - Fz * 1.5);
    }

    /// <summary>Where a man behind it stands (its captain): the middle, a few paces back.</summary>
    public (double X, double Z) Behind(double back = 2.8) => (X - Fx * back, Z - Fz * back);

    /// <summary>Gone from the field (the fight's end, or a rise).</summary>
    public void Clear()
    {
        foreach (var m in men.Where(Here)) B.Enemies.Release(m.E);
        men.Clear();
        Broken = true;
    }

    static double Wrap(double a)
    {
        while (a > Math.PI) a -= Math.PI * 2;
        while (a < -Math.PI) a += Math.PI * 2;
        return a;
    }
}
