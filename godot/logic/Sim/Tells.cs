using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* The telegraph kit in the fight (H1 combat teeth, docs/team/hook/H1_combat_teeth.md item 3; numbers in
 * data/content/telegraphs.json, read by Content/Telegraphs.cs). One call marks a named blow that must be dashed:
 *   ring     an expanding circle: its fill slows her, its heart roots her (a dash ends it), then the whole circle lands;
 *   charge   a foe plants (held: no step, no blow), its lane is marked, then it lands down the lane and runs it;
 *   pull     a vortex drags her toward its heart, then the heart lands;
 *   closing  the horde as a ring round her: the zone spawns its foes on the ring's points (TellClosing), they are
 *            held for the windup, then rush in (the Flare is the answer).
 * Every one emits Ev.Telegraph with its Tell (the kind) at Warn and at Land (Caught: she was in it), the keys of H3's
 * sound bank. Nothing here runs until a zone casts one: with none cast the fight is as it was, draw for draw. */
public sealed partial class Battle
{
    /// <summary>A kit telegraph on the ground (or a charger still running its lane): what the hands and the view
    /// can read of it while it lives (Battle.ActiveTells).</summary>
    public sealed class TellOn
    {
        /// <summary>The kit's kind (ring, charge, pull, closing).</summary>
        public string Kind = "";
        /// <summary>Its marked blow (in Battle.Blows until it lands).</summary>
        public EnemyBlow Blow = null!;
        /// <summary>The cast's scale (a boss's bigger version), already in the blow's sizes.</summary>
        public double Scale = 1;
        /// <summary>A pull's reach (m) and drag (m/s), centered on the blow; 0 for every other kind.</summary>
        public double Reach, Pull;
        /// <summary>Landed: only a charger's run is left.</summary>
        public bool Landed;
        internal Telegraphs.Kind K = null!;
        internal Enemy? From;
        internal double FromSeed;
        internal bool RootTried;
        internal double RunLeft, RunX, RunZ;
        internal readonly List<(Enemy E, double Seed)> Foes = new();
    }

    readonly List<TellOn> tells = new();

    /// <summary>The kit telegraphs alive now (their windups, a charger's run): the hands read a pull's reach here.</summary>
    public IReadOnlyList<TellOn> ActiveTells => tells;

    /// <summary>How long a charger takes to run its lane once its blow has landed.</summary>
    public const double ChargeRun = 0.25;

    /// <summary>
    /// The app can now cast a named telegraph from the kit (data/content/telegraphs.json) with one call, from any zone:
    /// a ring on (x, z), a charge from `from` through (x, z), a pull centered on (x, z), or a closing round (x, z)
    /// (TellClosing gives its points). It marks the blow (Ev.Telegraph, Tell = kind), runs its windup (the ring's slow and
    /// root, the charger held, the pull's drag) and its landing (damage as a share of her max life, the charger's run).
    /// `scale` multiplies its sizes (a boss's bigger version). Null: a kind the kit does not have, or a charge with no foe.
    /// </summary>
    public EnemyBlow? Tell(string kind, Enemy? from, double x, double z, double scale = 1)
    {
        var k = Telegraphs.Get(kind);
        if (k == null || Over != null || (k.Length > 0 && from == null)) return null;
        var b = new EnemyBlow
        {
            Tell = kind, From = from, Source = from?.Def.Name ?? kind, Label = null, Delay = k.Windup, Damage = k.Damage * MaxHp,
        };
        var t = new TellOn { Kind = kind, Blow = b, Scale = scale, K = k, From = from, FromSeed = from?.Seed ?? 0 };
        if (k.Length > 0)
        {
            // The lane: from the foe through the point, its full length (a point on the foe: the way it faces).
            double dx = x - from!.X, dz = z - from.Z, l = Len(dx, dz);
            if (l < 0.01) { dx = Math.Cos(from.Facing); dz = Math.Sin(from.Facing); l = 1; }
            dx /= l; dz /= l;
            b.Shape = TelegraphShape.Line;
            b.X = from.X; b.Z = from.Z;
            b.X1 = from.X + dx * k.Length * scale; b.Z1 = from.Z + dz * k.Length * scale;
            b.Width = k.Width * scale; b.Angle = Math.Atan2(dz, dx);
            from.HoldUntil = Time + k.Windup;
            from.Vx = from.Vz = 0;
            from.Facing = b.Angle;
        }
        else if (k.Inner > 0)
        {
            // A band (the closing): drawn as ground, not a blow to step out of (its danger is the crowd on it).
            b.Shape = TelegraphShape.Ring; b.Kind = TelegraphKind.Ground;
            b.X = x; b.Z = z; b.Inner = k.Inner * scale; b.Radius = k.Radius * scale;
        }
        else
        {
            b.Shape = TelegraphShape.Circle;
            b.X = x; b.Z = z; b.Radius = (k.Core > 0 ? k.Core : k.Radius) * scale;
        }
        if (k.Pull > 0) { t.Reach = k.Radius * scale; t.Pull = k.Pull; }
        b.After = bt => bt.TellLands(t);
        Blow(b);
        // A pull's reach, so where it drags reads: a ground band at its edge (no Tell: the blow's own mark carries the sound).
        if (t.Reach > 0)
            Events.Emit(new Ev.Telegraph
            {
                Id = 900000 + blowIds++, Shape = TelegraphShape.Ring, Kind = TelegraphKind.Ground, X = x, Z = z, Inner = t.Reach - 0.6 * scale, Radius = t.Reach,
                Duration = k.Windup, Hostile = true, Boss = from?.Boss == true,
            });
        tells.Add(t);
        return b;
    }

    /// <summary>
    /// The app can now close the horde round a point as a named telegraph: it marks the closing band round (x, z) and
    /// returns n points evenly round its middle, for the zone to spawn its own foes on (it hardens and counts them)
    /// and hand each to Closes, which holds it for the windup and then sends it in at the kit's rush.
    /// </summary>
    public List<(double X, double Z)> TellClosing(double x, double z, int n)
    {
        var pts = new List<(double X, double Z)>();
        if (Tell("closing", null, x, z) is not { } b) return pts;
        double r = (b.Inner + b.Radius) / 2;
        for (int i = 0; i < n; i++)
        {
            double a = (double)i / Math.Max(1, n) * Math.Tau;
            pts.Add((x + Math.Cos(a) * r, z + Math.Sin(a) * r));
        }
        return pts;
    }

    /// <summary>The app can now make a foe one of the last closing's ring: held where it stands until the closing
    /// lands, then rushing in. False: no closing is on the ground.</summary>
    public bool Closes(Enemy e)
    {
        for (int i = tells.Count - 1; i >= 0; i--)
        {
            var t = tells[i];
            if (t.Landed || t.K.Inner <= 0) continue;
            t.Foes.Add((e, e.Seed));
            e.HoldUntil = Time + t.Blow.T;
            e.Vx = e.Vz = 0;
            return true;
        }
        return false;
    }

    /// <summary>The app can now root her: no walking for a while (less for the tenacious); a dash ends it.</summary>
    public void RootPlayer(double seconds)
    {
        var p = Player;
        if (Art.SprintT > 0 || Art.Rush != null) return;
        double ten = Clamp(Stats.Get(Stat.Tenacity), 0, 0.8);
        p.RootT = Math.Max(p.RootT, seconds * (1 - ten));
    }

    static bool Same(Enemy e, double seed) => e.Alive && e.State != EnemyState.Dying && e.Seed == seed;

    /// <summary>The windups at work, before she moves: the ring's fill and root, the pull's drag, a charger's run.</summary>
    void UpdateTells(double dt)
    {
        var p = Player;
        p.DriftX = p.DriftZ = 0;
        for (int i = tells.Count - 1; i >= 0; i--)
        {
            var t = tells[i];
            var bl = t.Blow;
            if (t.Landed) { RunCharge(t, dt); if (t.RunLeft <= 0) tells.RemoveAt(i); continue; }
            if (!blows.Contains(bl)) { tells.RemoveAt(i); continue; }
            // A charger felled in its windup: its lane is called off.
            if (t.From != null && t.K.Length > 0 && !Same(t.From, t.FromSeed))
            {
                blows.Remove(bl);
                EndMark(bl.MarkId);
                tells.RemoveAt(i);
                continue;
            }
            if (!p.Alive || dt <= 0) continue;
            double share = Math.Clamp((bl.Delay - bl.T) / Math.Max(1e-6, bl.Delay), 0, 1);
            double d = Dist(p.X, p.Z, bl.X, bl.Z);
            // The ring's fill grows from its heart to its edge: inside it, she wades.
            if (t.K.Slow > 0 && d <= bl.Radius * share + p.Radius * 0.5) SlowPlayer(1 - t.K.Slow, 0.15);
            // At its moment, its heart roots her (unless she is dashing through it).
            if (t.K.Root > 0 && !t.RootTried && share >= t.K.RootAt)
            {
                t.RootTried = true;
                if (d <= t.K.RootRadius * t.Scale + p.Radius * 0.5 && p.DashT <= 0 && p.Leap == null) RootPlayer(t.K.Root);
            }
            // The pull drags her toward its heart (never past it).
            if (t.Pull > 0 && d <= t.Reach && d > 1e-3)
            {
                double s = Math.Min(t.Pull, d / dt);
                p.DriftX += (bl.X - p.X) / d * s;
                p.DriftZ += (bl.Z - p.Z) / d * s;
            }
        }
    }

    /// <summary>A kit blow has landed: a charger runs its lane, a closing's ring rushes in.</summary>
    void TellLands(TellOn t)
    {
        t.Landed = true;
        if (t.K.Length > 0 && t.From is { } e && Same(e, t.FromSeed))
        {
            var b = t.Blow;
            t.RunX = b.X1; t.RunZ = b.Z1;
            t.RunLeft = Dist(e.X, e.Z, b.X1, b.Z1);
            e.HoldUntil = Time + ChargeRun + 0.05;
        }
        foreach (var (f, seed) in t.Foes)
        {
            if (!Same(f, seed)) continue;
            f.HoldUntil = 0;
            if (t.K.RushFor > 0) { f.Haste = t.K.Rush; f.HasteT = t.K.RushFor; }
        }
        if (t.RunLeft <= 0) tells.Remove(t);
    }

    /// <summary>A charger runs its lane to its end in ChargeRun seconds, stopping at whatever stands in it.</summary>
    void RunCharge(TellOn t, double dt)
    {
        if (t.From is not { } e || !Same(e, t.FromSeed)) { t.RunLeft = 0; return; }
        double full = t.K.Length * t.Scale, step = Math.Min(t.RunLeft, full / ChargeRun * dt);
        double dx = t.RunX - e.X, dz = t.RunZ - e.Z, l = Len(dx, dz);
        if (l < 1e-6) { t.RunLeft = 0; return; }
        // Walls stop it: in short steps, each resolved (a step the walls moved is its last).
        for (double done = 0; done < step - 1e-9;)
        {
            double s = Math.Min(0.4, step - done);
            double nx = e.X + dx / l * s, nz = e.Z + dz / l * s;
            if (Collision.Resolve(ref nx, ref nz, e.Radius)) { e.X = nx; e.Z = nz; t.RunLeft = 0; break; }
            e.X = nx; e.Z = nz;
            done += s;
            t.RunLeft -= s;
        }
        e.Vx = e.Vz = 0;
        e.HoldUntil = t.RunLeft > 1e-9 ? Time + 0.05 : 0;
        if (t.RunLeft <= 1e-9) t.RunLeft = 0;
    }

    /// <summary>Every kit windup is called off with the blows (she got up at a checkpoint): its held foes go free.</summary>
    void CancelTells()
    {
        foreach (var t in tells)
        {
            if (t.From != null && Same(t.From, t.FromSeed)) t.From.HoldUntil = 0;
            foreach (var (f, seed) in t.Foes) if (Same(f, seed)) f.HoldUntil = 0;
        }
        tells.Clear();
        Player.RootT = 0;
        Player.DriftX = Player.DriftZ = 0;
    }
}
