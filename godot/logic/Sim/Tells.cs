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
 * H6 (the owner, after demo-rc2: standing in the marks did not kill), each only where its data asks: a caught charge
 * knocks her down (Knock), a pull's landing marks a slam on its heart (Follow), a closing's band is a wall but for its
 * gap and crushes her inside it (Crush), and every kit damage scales by the night's tier (KitDamageMul, TierDamage).
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
        /// <summary>A closing's rush still running (s): its ring's foes that reach her hit her once each (Kind.Hit).</summary>
        public double RushLeft;
        internal readonly HashSet<double> Bit = new();
        /// <summary>A closing's wall and crush still running past its landing (s; Kind.CrushAfter + CrushFor).</summary>
        public double WallLeft;
        internal bool Wall, WallShown;
        internal double Since, CrushNext;
        /// <summary>A closing's band stands as a wall now (Kind.Crush): she cannot cross it outside its gap.</summary>
        public bool Walled
        {
            get
            {
                if (!Wall || Foes.Count == 0 || (Landed && WallLeft <= 0)) return false;
                int live = 0;
                foreach (var (e, seed) in Foes) if (Same(e, seed)) live++;
                return live >= K.WallShare * Foes.Count - 1e-9;
            }
        }
    }

    readonly List<TellOn> tells = new();

    /// <summary>The closing bites and opens (its Hit and Gap, H1 round 2B): set by a zone whose nights carry the kit
    /// (ArenaRun, the kit's tiers). Off, a closing is as it was: a gapless crowd, draw for draw.</summary>
    public bool ClosingTeeth;
    /// <summary>A pack's far foe held up against cover on its way to its slot round her (the straight line to its slot
    /// blocked, looked at twice a second) follows the flow field wholly for two seconds (Enemy.FlowUntil): N34's wolves
    /// stuck behind a rock. Set by the arena's director (H6, ArenaRun.Director.cs); off: as it was.</summary>
    public bool PackRoundCover;

    /// <summary>Every kit damage times this (H6: the night's tier, the waves' TierDamage; set by the zone with ClosingTeeth).
    /// 1: as it was.</summary>
    public double KitDamageMul = 1;

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
            Tell = kind, From = from, Source = from?.Def.Name ?? kind, Label = null, Delay = k.Windup, Damage = k.Damage * MaxHp * KitDamageMul,
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
            // Its way out: a gap at a seeded bearing whose outside is open ground (the first of eight turns from it).
            if (ClosingTeeth && k.Gap > 0)
            {
                double a0 = Rng.Next() * Math.Tau, ro = b.Radius + 2;
                b.GapAngle = a0;
                if (GapOnScreen(x, z, (b.Inner + b.Radius) / 2, ro) is double on) b.GapAngle = on;
                else
                    for (int i = 0; i < 8; i++)
                    {
                        double a = a0 + i * Math.Tau / 8, gx = x + Math.Cos(a) * ro, gz = z + Math.Sin(a) * ro;
                        if (!Collision.Blocked(gx, gz, 0.6) && (InBounds == null || InBounds(gx, gz))) { b.GapAngle = a; break; }
                    }
                b.GapWidth = k.Gap * scale;
                // Its wall (H6): the band stands but for the gap while its ring lives.
                t.Wall = k.Crush > 0;
            }
        }
        else
        {
            b.Shape = TelegraphShape.Circle;
            b.X = x; b.Z = z; b.Radius = (k.Core > 0 ? k.Core : k.Radius) * scale;
        }
        if (k.Pull > 0) { t.Reach = k.Radius * scale; t.Pull = k.Pull; }
        b.After = bt => bt.TellLands(t);
        Blow(b);
        landings.Add((Time + k.Windup, b));
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

    /// <summary>The play camera as the sim sees it (H6 r1 fix 1): its distance (m, the zone's own; ArenaRun sets it each
    /// frame), pitch (degrees), vertical lens (degrees) and aspect. The camera never yaws and looks from +Z at her (and a
    /// little ahead of her run), so a closing's gap can be put where the player sees it. ViewDistance 0: not known.</summary>
    public double ViewDistance, ViewPitch = 64, ViewFov = 34, ViewAspect = 16.0 / 9;
    /// <summary>The share of the screen a gap must sit in (NDC, y up): x 120-1800, y 120-860 at 1920x1080, clear of the
    /// HUD's statues along the bottom.</summary>
    const double SafeX = 0.875, SafeTop = 0.778, SafeBottom = 0.593;

    /// <summary>The app can now tell whether a ground point (gx, gz) is inside the play camera's safe area (the camera
    /// following her with its lead). True when the view is not known.</summary>
    public bool OnScreen(double gx, double gz)
    {
        if (ViewDistance <= 0) return true;
        var p = Player;
        double th = ViewPitch * Math.PI / 180, cp = Math.Cos(th), sp = Math.Sin(th);
        // (FollowCamera: the look is 0.8 m up on her plus a lead of her speed x Lead x 0.2)
        double lx = p.X + p.Vx * 0.44, ly = 0.8, lz = p.Z + p.Vz * 0.44;
        double cx = lx, cy = ly + sp * ViewDistance, cz = lz + cp * ViewDistance;
        double dx = gx - cx, dy = -cy, dz = gz - cz;
        double fwd = dy * -sp + dz * -cp, right = dx, up = dy * cp + dz * -sp;
        if (fwd <= 0.1) return false;
        double tv = Math.Tan(ViewFov * Math.PI / 360), th2 = tv * ViewAspect;
        double nx = right / (fwd * th2), ny = up / (fwd * tv);
        return Math.Abs(nx) <= SafeX && ny <= SafeTop && ny >= -SafeBottom;
    }

    /// <summary>A closing's gap bearing whose middle (at radius r) is on screen and whose outside (at ro) is open ground,
    /// nearest the way she is going (her run; standing, her facing). Null: none (the old seeded search then).</summary>
    double? GapOnScreen(double x, double z, double r, double ro)
    {
        if (ViewDistance <= 0) return null;
        var p = Player;
        double head = Len(p.Vx, p.Vz) > 0.5 ? Math.Atan2(p.Vz, p.Vx) : p.Facing, best = double.MaxValue;
        double? pick = null;
        for (int i = 0; i < 72; i++)
        {
            double a = i * Math.Tau / 72, gx = x + Math.Cos(a) * r, gz = z + Math.Sin(a) * r;
            if (!OnScreen(gx, gz)) continue;
            double ox = x + Math.Cos(a) * ro, oz = z + Math.Sin(a) * ro;
            if (Collision.Blocked(ox, oz, 0.6) || (InBounds != null && !InBounds(ox, oz))) continue;
            double off = Math.Abs(Math.IEEERemainder(a - head, Math.Tau));
            if (off < best) { best = off; pick = a; }
        }
        return pick;
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
        double r = (b.Inner + b.Radius) / 2, gapHalf = b.GapWidth > 0 ? (b.GapWidth / 2 + 0.5) / r : -1;
        for (int i = 0; i < n; i++)
        {
            double a = (double)i / Math.Max(1, n) * Math.Tau;
            // (none in the way out)
            if (gapHalf > 0 && Math.Abs(Math.IEEERemainder(a - b.GapAngle, Math.Tau)) < gapHalf) continue;
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

    /// <summary>The app can now space the kit (H1 round 2B): how long a cast of this kind should wait (s): to land Spacing after (or before) every kit blow landing near her,
    /// and (a fodder's charge) until fewer than FodderLanes fodder lanes are alive near her. 0: now.</summary>
    public double KitWait(string kind, Enemy? from)
    {
        var w = Telegraphs.Waves;
        var p = Player;
        double now = Time, land = now + (Telegraphs.Get(kind)?.Windup ?? 0), wait = 0;
        // (H6 r1 fix 4: nothing new is cast on her while she is down or in her get-up grace; marks already running run on)
        if (now < knockGraceUntil) wait = knockGraceUntil - now;
        landings.RemoveAll(l => l.At < now - w.Spacing);
        foreach (var (at, bl) in landings)
            if (Near(bl, p.X, p.Z) <= w.SpacingNear && Math.Abs(land + wait - at) < w.Spacing) wait = Math.Max(wait, at + w.Spacing - land);
        if (kind == "charge" && from is { Elite: false, Boss: false })
        {
            int lanes = 0;
            double first = double.MaxValue;
            foreach (var t in tells)
                if (t.Kind == "charge" && !t.Landed && t.Blow.From is { Elite: false, Boss: false } && Near(t.Blow, p.X, p.Z) <= w.SpacingNear) { lanes++; first = Math.Min(first, t.Blow.T); }
            if (lanes >= w.FodderLanes) wait = Math.Max(wait, first + ChargeRun + 0.05);
        }
        return wait;
    }

    /// <summary>How far (x, z) is outside a blow's ground (0 inside it; a band: inside it counts as in).</summary>
    static double Near(EnemyBlow b, double x, double z)
    {
        if (b.Shape == TelegraphShape.Line)
        {
            double lx = b.X1 - b.X, lz = b.Z1 - b.Z, ll = Math.Max(1e-6, lx * lx + lz * lz);
            double u = Math.Clamp(((x - b.X) * lx + (z - b.Z) * lz) / ll, 0, 1);
            return Math.Max(0, Dist(x, z, b.X + lx * u, b.Z + lz * u) - b.Width / 2);
        }
        return Math.Max(0, Dist(x, z, b.X, b.Z) - b.Radius);
    }

    /// <summary>Every kit blow cast, and when it lands (KitWait reads them; kept Spacing past its landing).</summary>
    readonly List<(double At, EnemyBlow B)> landings = new();

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
            if (t.Landed)
            {
                if (t.WallLeft > 0) Crush(t, dt);
                if (t.RushLeft > 0) Rush(t, dt); else RunCharge(t, dt);
                if (t.RunLeft <= 0 && t.RushLeft <= 0 && t.WallLeft <= 0) { ShowWall(t, false); tells.RemoveAt(i); }
                continue;
            }
            if (!blows.Contains(bl)) { tells.RemoveAt(i); continue; }
            // A charger felled in its windup: its lane is called off.
            if (t.From != null && t.K.Length > 0 && !Same(t.From, t.FromSeed))
            {
                blows.Remove(bl);
                EndMark(bl.MarkId);
                tells.RemoveAt(i);
                continue;
            }
            // A closing whose ring is all down in its windup (a Flare's save): its band is called off and fades (H4 r3 judge:
            // the band and its streaks outlived the wolves by 2 s).
            if (t.K.Inner > 0 && t.Foes.Count > 0 && !t.Foes.Exists(f => Same(f.E, f.Seed)))
            {
                blows.Remove(bl);
                ShowWall(t, false);
                Events.Emit(new Ev.Telegraph { Id = bl.MarkId, Tell = bl.Tell, Phase = TellPhase.Off, Shape = bl.Shape, Kind = bl.Kind, X = bl.X, Z = bl.Z, Radius = bl.Radius, Inner = bl.Inner, Hostile = true });
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
        if (ClosingTeeth && t.K.Hit > 0 && t.Foes.Count > 0) t.RushLeft = Math.Max(0.1, t.K.RushFor);
        var p = Player;
        // A caught charge (one that hurt her) knocks her down (H6).
        if (t.K.Knock > 0 && t.K.Length > 0 && t.Blow.Dealt > 0 && p.Alive) KnockPlayer(t.K.Knock, t.Blow);
        // A pull's slam (H6): its heart is marked the moment the drag ends, and lands Follow s later.
        if (t.K.Follow > 0 && Over == null)
        {
            var bl = t.Blow;
            var f = new EnemyBlow
            {
                Tell = t.Kind, From = t.From != null && Same(t.From, t.FromSeed) ? t.From : null, Source = bl.Source, Label = null,
                Shape = TelegraphShape.Circle, X = bl.X, Z = bl.Z, Radius = bl.Radius, Delay = t.K.Follow, Damage = t.K.FollowDamage * MaxHp * KitDamageMul,
            };
            Blow(f);
            landings.Add((Time + t.K.Follow, f));
        }
        // A closing's wall and crush run on past its landing (H6).
        if (t.Wall && t.Foes.Count > 0) { t.WallLeft = t.K.CrushAfter + t.K.CrushFor; t.Since = 0; t.CrushNext = t.K.CrushAfter; }
        if (t.RunLeft <= 0 && t.RushLeft <= 0 && t.WallLeft <= 0) { ShowWall(t, false); tells.Remove(t); }
    }

    /// <summary>After a knockdown she is up for this long before another can take her (H6).</summary>
    public const double KnockGrace = 2.5;
    double knockGraceUntil = -1;
    /// <summary>Seconds left of her knockdown and its get-up grace (0: none): no new kit mark is cast on her in it (KitWait).</summary>
    public double KnockGraceLeft => Math.Max(0, knockGraceUntil - Time);

    /// <summary>The app can now knock her down (the kit's charge, H6): held where she lies for a while (less for the
    /// tenacious; a dash ends it, as a root does), with Ev.Knockdown for the view.</summary>
    public void KnockPlayer(double seconds, EnemyBlow? by = null)
    {
        var p = Player;
        if (!p.Alive || Art.SprintT > 0 || Art.Rush != null || p.Leap != null) return;
        double s = seconds * (1 - Clamp(Stats.Get(Stat.Tenacity), 0, 0.8));
        if (s <= 0) return;
        // (a get-up grace: no second knockdown until KnockGrace s after she is up; 4 Nov, lead 2: a stand charge on her
        // as she rose chained ten knockdowns 1.5 s apart, 24 s held down)
        if (Time < knockGraceUntil) return;
        knockGraceUntil = Time + s + KnockGrace;
        p.RootT = Math.Max(p.RootT, s);
        p.Vx = p.Vz = 0;
        var kd = new Ev.Knockdown { X = p.X, Z = p.Z, Seconds = s };
        if (by is { Shape: TelegraphShape.Line }) { kd.FromX = by.X; kd.FromZ = by.Z; kd.ToX = by.X1; kd.ToZ = by.Z1; kd.Width = by.Width; }
        Events.Emit(kd);
    }

    /// <summary>A closing's crush (H6): from CrushAfter past its landing, for CrushFor, while its wall stands and she is
    /// inside its band's inner edge, a blow of Crush x 0.5 each half second (a blow's grace delays it, never skips it).</summary>
    void Crush(TellOn t, double dt)
    {
        t.WallLeft -= dt;
        t.Since += dt;
        var p = Player;
        var bl = t.Blow;
        if (!p.Alive || t.Since < t.CrushNext || t.Since > t.K.CrushAfter + t.K.CrushFor || !t.Walled) return;
        if (Dist(p.X, p.Z, bl.X, bl.Z) >= bl.Inner) return;
        if (p.Iframes > 0 || p.Leap != null) return;
        t.CrushNext = t.Since + 0.5;
        HurtPlayer(t.K.Crush * 0.5 * MaxHp * KitDamageMul, School.Physical, "closing", null, telegraphed: true);
    }

    /// <summary>The closings' walls (H6), after she has moved from (px, pz): outside a standing wall's gap she does not
    /// cross its band, in or out (walking, dragged or dashing: she stops at its edge and slides along it).</summary>
    void Walls(double px, double pz)
    {
        var p = Player;
        foreach (var t in tells)
        {
            bool up = t.Walled;
            ShowWall(t, up);
            if (!up || !p.Alive) continue;
            var bl = t.Blow;
            double r0 = Dist(px, pz, bl.X, bl.Z), dx = p.X - bl.X, dz = p.Z - bl.Z, r1 = Len(dx, dz);
            if (r1 < 1e-6) continue;
            double mid = (bl.Inner + bl.Radius) / 2;
            if (bl.GapWidth > 0 && Math.Abs(Math.IEEERemainder(Math.Atan2(dz, dx) - bl.GapAngle, Math.Tau)) * mid <= bl.GapWidth / 2) continue;
            double inEdge = bl.Inner - p.Radius, outEdge = bl.Radius + p.Radius, to;
            int side;
            if (r0 < bl.Inner && r1 > (to = Math.Max(inEdge, r0))) side = 1;
            else if (r0 > bl.Radius && r1 < (to = Math.Min(outEdge, r0))) side = -1;
            else continue;
            double nx = dx / r1, nz = dz / r1;
            p.X = bl.X + nx * to; p.Z = bl.Z + nz * to;
            Collision.Resolve(ref p.X, ref p.Z, p.Radius, true);
            double vr = p.Vx * nx + p.Vz * nz;
            if (vr * side > 0) { p.Vx -= vr * nx; p.Vz -= vr * nz; }
        }
    }

    /// <summary>A closing's wall shown standing or fallen (Ev.ClosingWall, once each way).</summary>
    void ShowWall(TellOn t, bool up)
    {
        if (t.WallShown == up) return;
        t.WallShown = up;
        var bl = t.Blow;
        Events.Emit(new Ev.ClosingWall { Id = bl.MarkId, X = bl.X, Z = bl.Z, Inner = bl.Inner, Radius = bl.Radius, GapAngle = bl.GapAngle, GapWidth = bl.GapWidth, Up = up });
    }

    /// <summary>A closing's rush: each of its ring's foes that reaches her hits her once (a dash's frames let it by).</summary>
    void Rush(TellOn t, double dt)
    {
        t.RushLeft -= dt;
        var p = Player;
        if (!p.Alive || p.Iframes > 0 || p.Leap != null) return;
        foreach (var (f, seed) in t.Foes)
        {
            if (!Same(f, seed) || t.Bit.Contains(seed) || Dist(f.X, f.Z, p.X, p.Z) > f.Radius + p.Radius + 0.35) continue;
            t.Bit.Add(seed);
            HurtPlayer(t.K.Hit * MaxHp * KitDamageMul, School.Physical, f.Def.Name, f, telegraphed: true);
            if (!p.Alive) return;
        }
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
            ShowWall(t, false);
            if (t.From != null && Same(t.From, t.FromSeed)) t.From.HoldUntil = 0;
            foreach (var (f, seed) in t.Foes) if (Same(f, seed)) f.HoldUntil = 0;
        }
        tells.Clear();
        Player.RootT = 0;
        Player.DriftX = Player.DriftZ = 0;
    }
}
