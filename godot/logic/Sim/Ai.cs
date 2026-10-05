using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/// <summary>
/// How each creature decides what to do this tick.
///
/// Everything shares one skeleton - statuses, knockback, choosing a target,
/// wanting to be somewhere, not standing inside its neighbours, hitting what
/// it touches - and each behaviour only changes where it wants to be and
/// what it does about it. Targets are not always the survivor: creatures of
/// factions at war go for each other, allies go for whatever threatens you,
/// and something neutral minds its own business until it is hurt.
/// </summary>
public static class Ai
{
    public const double DieTime = 1.25;
    /// <summary>How long a slammer stays planted after its blow lands, and a crossbow after it looses
    /// (the clips' holds and get-ups, animation's numbers).</summary>
    public const double SlamPlant = 0.65, ShotPlant = 0.7;
    static readonly Tag[] Physical = [Tag.Physical];
    static readonly Tag[] AllyStrike = [Tag.Summon, Tag.Melee, Tag.Physical];

    struct Tgt { public double X, Z, R; public Enemy? Enemy; public bool Player; }

    public static void Update(Battle b, Enemy e, double dt)
    {
        e.AnimT += dt;
        if (e.Flash > 0) e.Flash = Math.Max(0, e.Flash - dt * 11);

        if (e.State == EnemyState.Dying)
        {
            e.DieT += dt;
            if (e.DieT >= DieTime) b.Enemies.Release(e);
            return;
        }
        if (e.LifeT > 0)
        {
            e.LifeT -= dt;
            if (e.LifeT <= 0) { b.KillEnemy(e, false, null); return; }
        }
        b.TickStatus(e, dt);
        if (!e.Alive || e.State == EnemyState.Dying) return;
        if (e.HasteT > 0) e.HasteT -= dt;
        if (e.WardT > 0) e.WardT -= dt;
        // A reflection stands where it was left, until it breaks.
        if (e.Decoy) { e.Vx = e.Vz = 0; e.Anim = EnemyAnim.Idle; return; }

        // Knockback slides, then settles.
        if (e.Kbx != 0 || e.Kbz != 0)
        {
            e.X += e.Kbx * dt;
            e.Z += e.Kbz * dt;
            // Knocked into a wall, it stops at the wall (a scripted boss's own step never resolved it, and
            // Grimtunnel was knocked out through the shut gate behind her, where she could not reach him).
            b.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
            double k = Math.Exp(-dt * 9);
            e.Kbx *= k; e.Kbz *= k;
            if (Math.Abs(e.Kbx) + Math.Abs(e.Kbz) < 0.05) e.Kbx = e.Kbz = 0;
        }

        var s = e.Status;
        if (s.Has(StatusKind.Frozen) || s.Has(StatusKind.Stun) || e.State == EnemyState.Stunned)
        {
            if (e.State == EnemyState.Stunned) { e.StateT -= dt; if (e.StateT <= 0) e.State = EnemyState.Active; }
            e.Vx = e.Vz = 0;
            e.Anim = EnemyAnim.Idle;
            b.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
            return;
        }

        // Rising from the ground: helpless for a moment. Hit them while they rise.
        if (e.State == EnemyState.Rising)
        {
            e.StateT -= dt;
            if (e.StateT <= 0) { e.State = EnemyState.Active; e.Anim = EnemyAnim.Move; }
            return;
        }

        if ((e.Boss || e.Scripted) && b.Hooks.BossTick?.Invoke(e, dt) == true)
        {
            FinishMove(b, e);
            return;
        }

        if (e.State is EnemyState.Burrowed or EnemyState.Surfacing) { Tunnel(b, e, dt); return; }

        // Choosing a target.
        e.RetargetT -= dt;
        if (e.RetargetT <= 0)
        {
            e.RetargetT = 0.45 + b.Rng.Next() * 0.35;
            e.Target = ChooseTarget(b, e);
        }
        if (!ResolveTarget(b, e, out var tgt)) { Idle(b, e, dt); return; }

        double dx = tgt.X - e.X, dz = tgt.Z - e.Z;
        double dist = Len(dx, dz);
        if (dist == 0) dist = 0.001;
        var def = e.Def;
        double speed = e.Speed * SlowFactor(e) * (e.HasteT > 0 ? e.Haste : 1);
        double wantX = dx / dist, wantZ = dz / dist;
        e.Facing = Math.Atan2(dz, dx);

        // Fear: away from the survivor.
        if (s.Has(StatusKind.Fear))
        {
            var p = b.Player;
            double a = Math.Atan2(e.Z - p.Z, e.X - p.X);
            Move(b, e, Math.Cos(a), Math.Sin(a), speed * 1.1, dt);
            return;
        }

        // Charges and lunges: plant, mark the lane, run exactly that lane.
        var lunge = def.Charge ?? def.Lunge;
        if (lunge != null)
        {
            if (e.State == EnemyState.Windup)
            {
                e.StateT -= dt;
                e.Anim = EnemyAnim.Windup;
                e.Facing = Math.Atan2(e.LungeZ, e.LungeX);
                if (e.StateT <= 0) { e.State = EnemyState.Lunging; e.StateT = lunge.Time; }
                e.Vx = e.Vz = 0;
                return;
            }
            if (e.State == EnemyState.Lunging)
            {
                e.StateT -= dt;
                e.Anim = EnemyAnim.Attack;
                e.X += e.LungeX * lunge.Speed * dt;
                e.Z += e.LungeZ * lunge.Speed * dt;
                e.Vx = e.LungeX * lunge.Speed; e.Vz = e.LungeZ * lunge.Speed;
                var p = b.Player;
                if (tgt.Player && Dist(p.X, p.Z, e.X, e.Z) < e.Radius + p.Radius + 0.2 && e.AttackT <= 0)
                {
                    b.HurtPlayer(e.Damage * 1.5, School.Physical, def.Name, e, true);
                    e.AttackT = 0.8;
                }
                else if (tgt.Enemy is { } te && Dist(te.X, te.Z, e.X, e.Z) < e.Radius + te.Radius + 0.2 && e.AttackT <= 0)
                    Strike(b, e, te, 1.5);
                e.AttackT -= dt;
                // A charge that ends in a tree ends the charger for a while.
                if (b.Collision.Resolve(ref e.X, ref e.Z, e.Radius))
                {
                    // (A lit crate run into a tree goes up there.)
                    if (def.RunBursts) { b.KillEnemy(e, false, null); return; }
                    e.ChainLeft = 0;
                    if (def.Charge != null)
                    {
                        e.State = EnemyState.Stunned;
                        e.StateT = 1.8;
                        b.Events.Emit(new Ev.Shake { Amount = 0.25 });
                        b.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = "Thud" });
                        b.ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, 1.8), 0);
                        b.HitEnemy(e, e.MaxHp * 0.12, School.Physical, Physical, new HitOpts { NoCrit = true, NoProcs = true });
                        return;
                    }
                    e.StateT = 0;
                }
                if (e.StateT <= 0)
                {
                    // Its run done: a lit crate goes up where it stops; a chain turns and runs again.
                    if (def.RunBursts) { b.KillEnemy(e, false, null); return; }
                    if (e.ChainLeft > 0 && dist > 2)
                    {
                        e.ChainLeft--;
                        Run(b, e, lunge, dx / dist, dz / dist, lunge.Windup * 0.55);
                        return;
                    }
                    e.State = EnemyState.Recover; e.StateT = 0.55;
                }
                return;
            }
            if (e.State == EnemyState.Recover)
            {
                e.StateT -= dt;
                e.Anim = EnemyAnim.Idle;
                e.Vx *= 0.8; e.Vz *= 0.8;
                if (e.StateT <= 0) { e.State = EnemyState.Active; e.RangedT = lunge.Cooldown; }
                return;
            }
            e.RangedT -= dt;
            // The charge director says when (Charges.cs): in a spike, a charger whose own clock is
            // most of the way round goes with the rest; refused, it walks on and asks again.
            if (e.RangedT <= (b.Charges.Eager ? lunge.Cooldown * 0.4 : 0) && dist < lunge.Range && dist > 2
                && b.Collision.Raycast(e.X, e.Z, tgt.X, tgt.Z, 0.3) == null && b.Charges.MayStart(b, e))
            {
                e.ChainLeft = def.Chain;
                Run(b, e, lunge, dx / dist, dz / dist, lunge.Windup);
                return;
            }
        }

        // Planted after its blow (a slam landed, a shot loosed): the blow held, then the get-up, which the view
        // plays on AnimT. Walking off at once cut the clip (animation's ask). A lunger's own recovery is above.
        if (e.State == EnemyState.Recover)
        {
            e.StateT -= dt;
            e.Vx = e.Vz = 0;
            if (e.StateT <= 0) e.State = EnemyState.Active;
            return;
        }

        // Casters raise the fallen.
        if (def.Raise is { } raise)
        {
            if (e.State == EnemyState.Casting && e.Cast is CastKind.Raise or CastKind.None)
            {
                e.StateT -= dt;
                e.Anim = EnemyAnim.Cast;
                e.Vx = e.Vz = 0;
                if (e.StateT <= 0)
                {
                    e.State = EnemyState.Active;
                    e.Cast = CastKind.None;
                    int n = 0;
                    for (int i = b.Graves.Count - 1; i >= 0 && n < raise.Count; i--)
                    {
                        var g = b.Graves[i];
                        if (Dist(g.X, g.Z, e.X, e.Z) > raise.Range) continue;
                        b.Graves.RemoveAt(i);
                        if (b.SpawnEnemy(raise.Into, g.X, g.Z, new Battle.SpawnOpts { Level = e.Level, Style = SpawnStyle.Rise, Faction = e.Faction }) is { } risen) risen.Raised = true;
                        n++;
                    }
                }
                return;
            }
            e.RaiseT -= dt;
            if (e.RaiseT <= 0)
            {
                e.RaiseT = raise.Every;
                if (GraveNear(b, e, raise.Range))
                {
                    e.State = EnemyState.Casting;
                    e.Cast = CastKind.Raise;
                    e.StateT = 1.5;
                    e.AnimT = 0;
                    b.Events.Emit(new Ev.Telegraph { Id = e.Id, Shape = TelegraphShape.Ring, X = e.X, Z = e.Z, Radius = raise.Range, Duration = 1.5, Hostile = true });
                    b.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = "Rise..." });
                    return;
                }
            }
        }

        // Aiming (a crossbow's kneel): planted on its line until it looses, then up again.
        if (e.State == EnemyState.Casting && e.Cast == CastKind.Aim && def.Ranged is { } aimed)
        {
            e.StateT -= dt;
            e.Vx = e.Vz = 0;
            e.Anim = EnemyAnim.Windup;
            e.Facing = Math.Atan2(e.LungeZ, e.LungeX);
            if (e.StateT <= 0)
            {
                e.State = EnemyState.Active;
                e.Cast = CastKind.None;
                // At the line it chose as it knelt, as far as the target then was.
                var at = tgt;
                double aimReach = Math.Max(1, e.AimReach);
                at.X = e.X + e.LungeX * aimReach; at.Z = e.Z + e.LungeZ * aimReach;
                Shoot(b, e, at);
                e.RangedT = aimed.Cooldown * (0.85 + b.Rng.Next() * 0.3);
                // The release, the kick and the rise off the knee, before it walks.
                e.State = EnemyState.Recover;
                e.StateT = ShotPlant;
            }
            b.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
            return;
        }

        // Its own verbs: a rallying pulse, a call for its kind, a blow on the ground.
        if ((def.Aura != null || def.Summon != null || def.Slam != null) && Verbs(b, e, def, tgt, dist, dt)) return;

        // Where it wants to be.
        switch (def.Behavior)
        {
            case Behavior.Pack:
                // Fan out to a slot around the target, then close together.
                if (dist > 5.5 && tgt.Player)
                {
                    double ox = tgt.X + Math.Cos(e.Slot) * 4, oz = tgt.Z + Math.Sin(e.Slot) * 4;
                    double d2 = Dist(ox, oz, e.X, e.Z);
                    if (d2 == 0) d2 = 1;
                    wantX = (ox - e.X) / d2; wantZ = (oz - e.Z) / d2;
                    speed *= 1.1;
                }
                break;
            case Behavior.Ranged:
            case Behavior.Caster:
            {
                double r = def.Ranged?.Range ?? 8;
                if (dist < r * 0.55) { wantX = -wantX; wantZ = -wantZ; speed *= 0.9; }
                else if (dist < r * 0.85)
                {
                    // Strafe, so standing and shooting at them is not free.
                    double side = e.Seed > 0.5 ? 1 : -1;
                    wantX = -dz / dist * side * 0.8; wantZ = dx / dist * side * 0.8;
                    speed *= 0.6;
                }
                break;
            }
            case Behavior.Guard:
                speed *= 0.85;
                break;
            case Behavior.Stationary:
                speed = 0;
                break;
            case Behavior.Orbit:
            {
                e.Slot += dt * 0.9;
                double ox = tgt.X + Math.Cos(e.Slot) * 6, oz = tgt.Z + Math.Sin(e.Slot) * 6;
                double d2 = Dist(ox, oz, e.X, e.Z);
                if (d2 == 0) d2 = 1;
                wantX = (ox - e.X) / d2; wantZ = (oz - e.Z) / d2;
                break;
            }
            case Behavior.Tunneler:
                e.RangedT -= dt;
                if (tgt.Player && dist > 6 && e.RangedT <= 0 && b.Charges.MayBurrow(b, e))
                {
                    e.State = EnemyState.Burrowed;
                    e.StateT = 0;
                    e.Anim = EnemyAnim.Burrow;
                    b.Events.Emit(new Ev.Spawn { Enemy = e.Id, X = e.X, Z = e.Z, Def = def.Id, Style = SpawnStyle.Burrow });
                    return;
                }
                break;
        }

        // Follow the flow field around obstacles when chasing the survivor.
        if (tgt.Player && def.Behavior != Behavior.Ranged && def.Behavior != Behavior.Caster && dist > 1.2)
        {
            if (b.Flow.Dir(e.X, e.Z, out double fx, out double fz))
            {
                double flowW = def.Behavior == Behavior.Pack && dist > 5.5 ? 0.35 : 0.85;
                wantX = wantX * (1 - flowW) + fx * flowW;
                wantZ = wantZ * (1 - flowW) + fz * flowW;
                double m = Len(wantX, wantZ);
                if (m == 0) m = 1;
                wantX /= m; wantZ /= m;
            }
        }

        // Ranged attack.
        if (def.Ranged is { } ranged)
        {
            e.RangedT -= dt;
            if (e.RangedT <= 0 && dist < ranged.Range && b.Collision.Raycast(e.X, e.Z, tgt.X, tgt.Z, 0.1) == null)
            {
                if (ranged.Aim > 0)
                {
                    // Kneel and aim: the line is fixed now, so a step off it in time is a dodge.
                    e.State = EnemyState.Casting;
                    e.Cast = CastKind.Aim;
                    e.StateT = ranged.Aim;
                    e.Anim = EnemyAnim.Windup;
                    e.AnimT = 0;
                    e.LungeX = dx / dist; e.LungeZ = dz / dist;
                    e.AimReach = dist;
                    e.Vx = e.Vz = 0;
                    return;
                }
                Shoot(b, e, tgt);
                e.RangedT = ranged.Cooldown * (0.85 + b.Rng.Next() * 0.3);
            }
        }

        // Trails left behind.
        if (def.Trail is { } trail)
        {
            e.RaiseT -= dt;
            if (e.RaiseT <= 0)
            {
                e.RaiseT = trail.Interval;
                var zn = b.SpawnZone(Side.Enemy, e.X, e.Z, trail.Radius, trail.Life, e.Damage * trail.DpsPct, trail.School);
                if (zn != null) { zn.Tags = [Tag.Zone]; zn.Art = "zone_venom"; }
            }
        }

        double reach = e.Radius + tgt.R + 0.15;
        if (dist > reach * 0.9) Move(b, e, wantX, wantZ, speed, dt);
        else { e.Vx *= 0.7; e.Vz *= 0.7; e.Anim = EnemyAnim.Idle; FinishMove(b, e); }

        // Contact.
        e.AttackT -= dt;
        if (dist <= reach + 0.25 && e.AttackT <= 0)
        {
            if (tgt.Player) b.HurtPlayer(e.Damage, School.Physical, def.Name, e);
            else if (tgt.Enemy is { } te) Strike(b, e, te, 1);
            double every = (def.AttackEvery ?? 1.0) / (e.HasteT > 0 ? e.Haste : 1);
            if (e.Disposition == Disposition.Ally) every /= b.Stats.Get(Stat.SummonHaste);
            e.AttackT = every;
            e.Anim = EnemyAnim.Attack;
            e.AnimT = 0;
        }
    }

    /// <summary>Plant and mark the lane, then run exactly it (a first run, or the next of a chain).</summary>
    static void Run(Battle b, Enemy e, LungeSpec lunge, double dirX, double dirZ, double windup)
    {
        e.State = EnemyState.Windup;
        e.StateT = windup;
        e.LungeX = dirX; e.LungeZ = dirZ;
        double reachL = lunge.Speed * lunge.Time;
        b.Events.Emit(new Ev.Telegraph
        {
            Id = e.Id, Shape = TelegraphShape.Line, X = e.X, Z = e.Z, X1 = e.X + e.LungeX * reachL, Z1 = e.Z + e.LungeZ * reachL,
            Radius = e.Radius, Width = e.Radius * 2.2, Duration = windup, Hostile = e.Disposition != Disposition.Ally,
        });
        e.Vx = e.Vz = 0;
    }

    /* ------------------------------------------------- the encounters' verbs -- */

    /// <summary>A rallying pulse, a call for its kind, a blow on the ground (docs/SKILLS_DESIGN.md,
    /// "Encounters"): each a cast with its mark and its word first, then the thing. True while
    /// it is casting (it does nothing else).</summary>
    static bool Verbs(Battle b, Enemy e, EnemyDef def, in Tgt tgt, double dist, double dt)
    {
        if (e.State == EnemyState.Casting && e.Cast is CastKind.Summon or CastKind.Slam or CastKind.Aura)
        {
            e.StateT -= dt;
            e.Anim = EnemyAnim.Cast;
            e.Vx = e.Vz = 0;
            if (e.StateT > 0) return true;
            var done = e.Cast;
            e.State = EnemyState.Active;
            e.Cast = CastKind.None;
            if (done == CastKind.Summon) Call(b, e, def.Summon!);
            else if (done == CastKind.Aura) Rally(b, e, def.Aura!);
            // (A slam's blow was laid down when it was marked: marked, it lands, now.) The blow held on the
            // ground, then the get-up, before it moves or strikes again.
            else if (done == CastKind.Slam) { e.State = EnemyState.Recover; e.StateT = SlamPlant; }
            return true;
        }
        if (e.Disposition != Disposition.Hostile) return false;
        if (def.Aura is { } aura && (e.AuraT -= dt) <= 0)
        {
            e.AuraT = aura.Every;
            Begin(e, CastKind.Aura, 0.7);
            b.Events.Emit(new Ev.Telegraph
            {
                Id = e.Id, Shape = TelegraphShape.Ring, X = e.X, Z = e.Z, Inner = Math.Max(0, aura.Radius - 0.6), Radius = aura.Radius, Duration = 0.7,
                Hostile = false, Label = aura.Word.Length > 0 ? aura.Word : null, ByX = e.X, ByZ = e.Z, Faction = e.Faction,
            });
            return true;
        }
        if (def.Summon is { } su && tgt.Player && dist < 16 && e.Summoned < su.Max && (e.SummonT -= dt) <= 0)
        {
            e.SummonT = su.Every;
            Begin(e, CastKind.Summon, su.Cast);
            e.CastX = su.AtTarget ? tgt.X : e.X; e.CastZ = su.AtTarget ? tgt.Z : e.Z;
            // Where each will come, marked on the ground; the word over the one calling.
            for (int i = 0; i < su.Count; i++)
            {
                var (x, z) = CallPoint(e, su, i);
                b.Events.Emit(new Ev.Telegraph { Id = -1, Shape = TelegraphShape.Circle, X = x, Z = z, Radius = 0.8, Duration = su.Cast, Hostile = true, Kind = TelegraphKind.Ground, Faction = e.Faction });
            }
            if (su.Word.Length > 0) b.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = su.Word });
            return true;
        }
        if (def.Slam is { } sl && (e.SlamT -= dt) <= 0)
        {
            if (dist > sl.Range || (!sl.Self && dist < 1.0)) { e.SlamT = 0.3; return false; }
            if (!b.Charges.MayStart(b, e, retry: false)) { e.SlamT = 0.5; return false; }
            e.SlamT = sl.Cooldown;
            double sx = sl.Self ? e.X : tgt.X, sz = sl.Self ? e.Z : tgt.Z;
            Begin(e, CastKind.Slam, sl.Windup);
            e.Facing = Math.Atan2(sz - e.Z, sx - e.X);
            b.Events.Emit(new Ev.Telegraph
            {
                Id = e.Id, Shape = TelegraphShape.Circle, X = sx, Z = sz, Radius = sl.Radius, Duration = sl.Windup, Hostile = true,
                Label = sl.Word.Length > 0 ? sl.Word : null, ByX = e.X, ByZ = e.Z, Faction = e.Faction,
            });
            b.EnemyStrike(sx, sz, sl.Radius, e.Damage * sl.DamagePct, sl.School, sl.Windup);
            return true;
        }
        return false;
    }

    static void Begin(Enemy e, CastKind kind, double t)
    {
        e.State = EnemyState.Casting;
        e.Cast = kind;
        e.StateT = t;
        e.Vx = e.Vz = 0;
        e.Anim = EnemyAnim.Cast;
        e.AnimT = 0;
    }

    /// <summary>Where the i-th of a call comes: round the mark, the same at the call's start
    /// and its end (so the marks shown are where they come).</summary>
    static (double X, double Z) CallPoint(Enemy e, SummonSpec su, int i)
    {
        double a = e.Seed * Math.Tau + e.Summoned * 0.7 + i * Math.Tau / su.Count;
        return (e.CastX + Math.Cos(a) * su.Range, e.CastZ + Math.Sin(a) * su.Range);
    }

    static void Call(Battle b, Enemy e, SummonSpec su)
    {
        for (int i = 0; i < su.Count; i++)
        {
            var (x, z) = CallPoint(e, su, i);
            if (b.Collision.Blocked(x, z, 0.5) || b.InBounds?.Invoke(x, z) == false) continue;
            if (b.SpawnEnemy(su.Into, x, z, new Battle.SpawnOpts { Level = e.Level, Style = su.Style, Faction = e.Faction }) is { } c)
                b.Hooks.OnCalled?.Invoke(c, e);
        }
        e.Summoned += su.Count;
    }

    /// <summary>Its kind round it quickened or warded for a while (itself too).</summary>
    static void Rally(Battle b, Enemy e, AuraSpec aura)
    {
        b.Spatial.Query(e.X, e.Z, aura.Radius, b.AiScratch);
        foreach (var id in b.AiScratch)
        {
            var o = b.Enemies.Items[id];
            if (!o.Alive || o.State == EnemyState.Dying || o.Faction != e.Faction || o.Disposition != e.Disposition || o.Boss) continue;
            if (Dist(o.X, o.Z, e.X, e.Z) > aura.Radius) continue;
            if (aura.Haste > 1) { o.HasteT = aura.Duration; o.Haste = aura.Haste; }
            if (aura.Ward > 0) { o.WardT = aura.Duration; o.Ward = aura.Ward; }
        }
    }

    /// <summary>A grave within reach. A loop, not a lambda: one capturing the
    /// creature would be allocated on every Update, for every creature.</summary>
    static bool GraveNear(Battle b, Enemy e, double range)
    {
        foreach (var g in b.Graves)
            if (Dist(g.X, g.Z, e.X, e.Z) < range) return true;
        return false;
    }

    static double SlowFactor(Enemy e)
    {
        var c = e.Status[StatusKind.Chill];
        double f = c != null ? Math.Max(0.4, 1 - 0.1 * c.Stacks) : 1;
        if (e.Status[StatusKind.Poison] is { Stacks: >= 5 }) f *= 0.9;
        return f;
    }

    static int ChooseTarget(Battle b, Enemy e)
    {
        var p = b.Player;
        if (e.Disposition == Disposition.Ally)
        {
            // Go for the Throat: the toughest thing in reach, not the nearest.
            var t = b.Boons.ContainsKey("go_for_the_throat") ? Toughest(b, e.X, e.Z, 11) : b.NearestHostile(e.X, e.Z, 11);
            // Do not wander off: only fight what is near the survivor.
            if (t != null && Dist(t.X, t.Z, p.X, p.Z) < 16) return t.Id;
            return -2;
        }
        int best = -2;
        double bd = double.PositiveInfinity;
        bool hostileToPlayer = e.Disposition == Disposition.Hostile || e.Provoked;
        // A reflection of the survivor is the first thing anything hunting them goes for.
        // Champions and bosses are not fooled by a reflection: Mirror Step saves you from the crowd, not from them.
        if (hostileToPlayer && b.Decoys.Count > 0 && !e.Elite && !e.Boss)
        {
            Enemy? decoy = null;
            double dd = 14;
            foreach (var d in b.Decoys)
            {
                if (!d.Alive || d.State == EnemyState.Dying) continue;
                double dist = Dist(d.X, d.Z, e.X, e.Z);
                if (dist < dd) { dd = dist; decoy = d; }
            }
            if (decoy != null) return decoy.Id;
        }
        if (hostileToPlayer && p.Alive && p.InvisibleT <= 0)
        {
            double d = Dist(p.X, p.Z, e.X, e.Z);
            double aggro = e.Def.AggroRange ?? 60;
            // A pack at rest notices the survivor only close by; once roused it
            // hunts them as far as its leash, and rouses its own.
            if (e.Wake > 0 && !e.Roused && d < e.Wake) b.Rouse(e);
            bool resting = e.Wake > 0 && !e.Roused;
            if (!resting && d < aggro && (e.Leash == 0 || Dist(p.X, p.Z, e.HomeX, e.HomeZ) < e.Leash * 1.6)) { best = -1; bd = d * 0.8; }
        }
        // Rivals and the survivor's allies nearby.
        b.Spatial.Query(e.X, e.Z, 9, b.AiScratch);
        foreach (var id in b.AiScratch)
        {
            var o = b.Enemies.Items[id];
            if (!o.Alive || o == e || o.State == EnemyState.Dying) continue;
            bool war = o.Disposition == Disposition.Ally ? hostileToPlayer : b.FactionsAtWar(e.Faction, o.Faction);
            if (!war) continue;
            double d = Dist(o.X, o.Z, e.X, e.Z);
            if (d < bd) { bd = d; best = o.Id; }
        }
        return best;
    }

    /// <summary>The toughest hostile within r: a boss before a champion before the rest.</summary>
    static Enemy? Toughest(Battle b, double x, double z, double r)
    {
        Enemy? best = null;
        double bv = -1;
        b.Spatial.Query(x, z, r, b.AiScratch);
        foreach (var id in b.AiScratch)
        {
            var o = b.Enemies.Items[id];
            if (!b.Targetable(o) || Dist(o.X, o.Z, x, z) > r) continue;
            double v = (o.Boss ? 2e6 : o.Elite ? 1e6 : 0) + o.MaxHp;
            if (v > bv) { bv = v; best = o; }
        }
        return best;
    }

    static bool ResolveTarget(Battle b, Enemy e, out Tgt tgt)
    {
        tgt = default;
        if (e.Target == -1)
        {
            var p = b.Player;
            if (!p.Alive || p.InvisibleT > 0) { e.Target = -2; return false; }
            tgt = new Tgt { X = p.X, Z = p.Z, R = p.Radius, Enemy = null, Player = true };
            return true;
        }
        if (e.Target >= 0)
        {
            var o = b.Enemies.Items[e.Target];
            if (!o.Alive || o.State is EnemyState.Dying or EnemyState.Burrowed) { e.Target = -2; e.RetargetT = 0; return false; }
            tgt = new Tgt { X = o.X, Z = o.Z, R = o.Radius, Enemy = o, Player = false };
            return true;
        }
        return false;
    }

    /// <summary>Nothing to fight: allies heel, neutrals graze, guards go home.</summary>
    static void Idle(Battle b, Enemy e, double dt)
    {
        var p = b.Player;
        if (e.Disposition == Disposition.Ally)
        {
            double ox = p.X + Math.Cos(e.Slot) * 2.4, oz = p.Z + Math.Sin(e.Slot) * 2.4;
            double d = Dist(ox, oz, e.X, e.Z);
            if (d > 0.8) Move(b, e, (ox - e.X) / d, (oz - e.Z) / d, e.Speed * Math.Min(1.4, d / 3), dt);
            else { e.Anim = EnemyAnim.Idle; e.Vx = e.Vz = 0; }
            return;
        }
        // Home, or a slow wander around it.
        e.StateT -= dt;
        if (e.StateT <= 0)
        {
            e.StateT = 3 + b.Rng.Next() * 4;
            double r = e.Leash != 0 ? e.Leash * 0.6 : 5;
            e.LungeX = e.HomeX + (b.Rng.Next() - 0.5) * r;
            e.LungeZ = e.HomeZ + (b.Rng.Next() - 0.5) * r;
        }
        double dd = Dist(e.LungeX, e.LungeZ, e.X, e.Z);
        if (dd > 0.6)
        {
            Move(b, e, (e.LungeX - e.X) / dd, (e.LungeZ - e.Z) / dd, e.Speed * 0.35, dt);
            e.Facing = Math.Atan2(e.LungeZ - e.Z, e.LungeX - e.X);
        }
        else
        {
            e.Vx = e.Vz = 0;
            e.Anim = EnemyAnim.Idle;
            FinishMove(b, e);
        }
    }

    static void Move(Battle b, Enemy e, double wx, double wz, double speed, double dt)
    {
        double accel = 1 - Math.Exp(-dt * 8);
        e.Vx += (wx * speed - e.Vx) * accel;
        e.Vz += (wz * speed - e.Vz) * accel;
        e.X += e.Vx * dt;
        e.Z += e.Vz * dt;
        e.Anim = e.Anim == EnemyAnim.Attack && e.AnimT < 0.45 ? EnemyAnim.Attack : EnemyAnim.Move;
        FinishMove(b, e);
    }

    /// <summary>Keep out of each other, out of the survivor, and out of the walls.</summary>
    static void FinishMove(Battle b, Enemy e)
    {
        b.Spatial.Query(e.X, e.Z, e.Radius + 1.0, b.AiScratch);
        foreach (var id in b.AiScratch)
        {
            if (id == e.Id) continue;
            var o = b.Enemies.Items[id];
            if (!o.Alive || o.State == EnemyState.Dying) continue;
            double dx = e.X - o.X, dz = e.Z - o.Z;
            double min = e.Radius + o.Radius;
            double d2 = dx * dx + dz * dz;
            if (d2 >= min * min || d2 < 1e-6) continue;
            double d = Math.Sqrt(d2);
            double push = (min - d) * (o.Mass / (o.Mass + e.Mass));
            e.X += dx / d * push * 0.8;
            e.Z += dz / d * push * 0.8;
        }
        var p = b.Player;
        if (p.Alive && e.Disposition != Disposition.Ally)
        {
            double dx = e.X - p.X, dz = e.Z - p.Z;
            double min = e.Radius + p.Radius;
            double d2 = dx * dx + dz * dz;
            if (d2 < min * min && d2 > 1e-6)
            {
                double d = Math.Sqrt(d2);
                e.X += dx / d * (min - d);
                e.Z += dz / d * (min - d);
            }
        }
        b.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
        if (e.Leash != 0 && e.Disposition != Disposition.Ally)
        {
            double hd = Dist(e.X, e.Z, e.HomeX, e.HomeZ);
            if (hd > e.Leash * 1.8)
            {
                e.Target = -2;
                e.RetargetT = 1.5;
            }
        }
    }

    /// <summary>One creature striking another. The survivor's allies strike for
    /// the survivor, so their damage runs through the survivor's pipeline.</summary>
    static void Strike(Battle b, Enemy e, Enemy o, double mult)
    {
        if (e.Disposition == Disposition.Ally)
        {
            b.HitEnemy(o, e.Damage * mult, School.Physical, AllyStrike, new HitOpts { Summon = true, Knockback = 0.3, DirX = Math.Cos(e.Facing), DirZ = Math.Sin(e.Facing), Credit = e.SummonedBy ?? e.Def.Id,
                BossDamage = e.SummonedBy != null && Content.Weapons.All.TryGetValue(e.SummonedBy, out var by) ? by.BossDamage : null });
            return;
        }
        // Rival factions: real damage, no credit, and it draws attention.
        o.Hp -= e.Damage * mult;
        o.Flash = 1;
        b.Events.Emit(new Ev.Hit { X = o.X, Z = o.Z, Amount = e.Damage * mult, Crit = false, School = School.Physical, Target = o.Id });
        if (o.Target != e.Id && b.Rng.Next() < 0.6) o.Target = e.Id;
        if (o.Hp <= 0) b.KillEnemy(o, false, null);
    }

    static void Shoot(Battle b, Enemy e, in Tgt tgt)
    {
        var r = e.Def.Ranged!;
        var p = b.Player;
        double tx = tgt.X, tz = tgt.Z;
        e.Anim = EnemyAnim.Attack;
        e.AnimT = 0;
        int n = r.Count ?? 1;
        for (int i = 0; i < n; i++)
        {
            if (r.Lob)
            {
                // Lead the target a little; lobs are slow. Several at once fan out across the
                // line to it, so the gaps between them can be stood in.
                double lead = tgt.Player ? 0.45 : 0;
                double ax = tx, az = tz;
                if (n > 1)
                {
                    double a0 = Math.Atan2(tz - e.Z, tx - e.X) + (i - (n - 1) / 2.0) * (r.Spread ?? 0.3), d0 = Dist(tx, tz, e.X, e.Z);
                    ax = e.X + Math.Cos(a0) * d0; az = e.Z + Math.Sin(a0) * d0;
                }
                double lx = ax + p.Vx * lead + (b.Rng.Next() - 0.5) * 1.2;
                double lz = az + p.Vz * lead + (b.Rng.Next() - 0.5) * 1.2;
                double d = Dist(lx, lz, e.X, e.Z);
                double life = Math.Max(0.5, d / r.Speed);
                var pr = b.SpawnProjectile(Side.Enemy, e.X, e.Z, e.Damage * (r.DamagePct ?? 1), r.School);
                if (pr == null) continue;
                pr.OwnerId = e.Id; pr.Y = 1; pr.Vx = (lx - e.X) / life; pr.Vz = (lz - e.Z) / life; pr.Speed = r.Speed;
                pr.Radius = 0.3; pr.Life = life; pr.Lob = true; pr.Art = r.Art ?? "firepot"; pr.GroundOnHit = r.Zone;
                pr.AimAlongVelocity();
                pr.LandX = lx; pr.LandZ = lz;
                b.Events.Emit(new Ev.Telegraph { Id = pr.Id, Shape = TelegraphShape.Circle, X = lx, Z = lz, Radius = 1.6, Duration = life, Hostile = true });
            }
            else
            {
                double a = Math.Atan2(tz - e.Z, tx - e.X) + (i - (n - 1) / 2.0) * (r.Spread ?? 0.15);
                var pr = b.SpawnProjectile(Side.Enemy, e.X + Math.Cos(a) * 0.5, e.Z + Math.Sin(a) * 0.5, e.Damage * (r.DamagePct ?? 1), r.School);
                if (pr == null) continue;
                pr.OwnerId = e.Id; pr.Y = 1.1; pr.Vx = Math.Cos(a) * r.Speed; pr.Vz = Math.Sin(a) * r.Speed; pr.Speed = r.Speed;
                pr.Radius = 0.28; pr.Life = r.Range * 1.3 / r.Speed; pr.Art = r.Art ?? "bolt_enemy";
                pr.Status = r.Slow is { } slow ? new StatusPayload(StatusKind.Chill, 1, 1, slow.Duration) : null;
                pr.AimAlongVelocity();
            }
        }
    }

    /// <summary>Lamplings: under the ground, then up beside you.</summary>
    static void Tunnel(Battle b, Enemy e, double dt)
    {
        var p = b.Player;
        if (e.State == EnemyState.Burrowed)
        {
            e.Anim = EnemyAnim.Burrow;
            double dx = p.X - e.X, dz = p.Z - e.Z;
            double d = Len(dx, dz);
            if (d == 0) d = 1;
            double sp = e.Speed * 1.8;
            e.X += dx / d * sp * dt;
            e.Z += dz / d * sp * dt;
            b.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
            e.StateT += dt;
            if (d < 2.4 || e.StateT > 6)
            {
                e.State = EnemyState.Surfacing;
                e.StateT = 0.55;
                b.Events.Emit(new Ev.Telegraph { Id = e.Id, Shape = TelegraphShape.Circle, X = e.X, Z = e.Z, Radius = 1.1, Duration = 0.55, Hostile = true });
            }
            return;
        }
        e.StateT -= dt;
        if (e.StateT <= 0)
        {
            e.State = EnemyState.Active;
            e.Anim = EnemyAnim.Attack;
            e.AnimT = 0;
            e.RangedT = 4 + b.Rng.Next() * 3;
            if (Dist(p.X, p.Z, e.X, e.Z) < 1.3) b.HurtPlayer(e.Damage * 1.2, School.Physical, e.Def.Name, e, true);
            b.Events.Emit(new Ev.Spawn { Enemy = e.Id, X = e.X, Z = e.Z, Def = e.Def.Id, Style = SpawnStyle.Rise });
        }
    }
}
