using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* Phase 6a: the reaver's two Strikes (docs/design/CLASSES.md §3.6, §7's phase-6 plan).
 * Drag Them Under (chainbound, Clear): hooks bite up to 24 things in reach, the farthest and the champions first, and
 * haul them to one knot at her feet (the pull: the Flare's own displacement, a slide that walls stop); the slam there
 * stuns and breaks it. A boss is dragged 3 m, its channel broken, its stagger filled (a boss is never locked).
 * Events: "hook" per bite (TX/TZ the bitten thing or, with nothing near, a ground point at her reach; Target), "knot"
 * (TX/TZ the knot, Radius the slam's), "grind" (Grinder), "slam" (the knot, Radius; Last, the big hitstop).
 * The Butcher's Bill (butcher, Single with a save in it): she leaps on the strongest within 10 m and chops it, one chop
 * for each tenth of health she is missing (at least four, at most ten), each mending 2% and bleeding what stands 2 m
 * round; if it falls, the chops left vault with her to the next strongest within 6 m (Running Tab: twice).
 * Events: "leap" (X/Z where she left, TX/TZ where she lands, Target), "chop" per chop (TX/TZ, Target; the last the
 * overhead, Last), "vault" (as "leap"). With nothing near she leaps 6 m along her aim and chops the ground; no mend. */
public sealed partial class Battle
{
    /* ------------------------------------------------------------ Drag Them Under -- */

    readonly List<(Enemy E, int Id)> dragHooked = new();
    double knotX, knotZ;

    /// <summary>The bite (first blow), the knot, Grinder's shreds, and the slam (the last).</summary>
    void DragBlow(FlareDef f, bool last)
    {
        var p = Player;
        double slamR = f.Arg("slamRadius", 4) * FlareGrow(f);
        if (flareBlow == 1)
        {
            dragHooked.Clear();
            double dx = Math.Cos(flareAngle), dz = Math.Sin(flareAngle);
            knotX = p.X + dx * f.Arg("knotAhead", 1.5);
            knotZ = p.Z + dz * f.Arg("knotAhead", 1.5);
            double reach = flareReach * (FlareMod("drag.deeper") ? f.Arg("deeper", 1.5) : 1);
            var near = HostilesInRadius(p.X, p.Z, reach).Where(e => e.Alive && e.State != EnemyState.Dying && (!e.Boss || FlareCanHurt(e))).ToList();
            // What the slam takes where it stands needs no hook: the hooks go to the boss, the champions, then the farthest.
            var hooks = near.Where(e => e.Boss || Dist(e.X, e.Z, knotX, knotZ) > slamR * 0.8)
                .OrderByDescending(e => e.Boss).ThenByDescending(e => e.Elite).ThenByDescending(e => Dist(e.X, e.Z, p.X, p.Z))
                .Take((int)f.Arg("hooks", 24)).ToList();
            int hitstop = FlareHitstop(f, false);
            int i = 0;
            foreach (var e in hooks)
            {
                FlareBlowEvent(f, "hook", false, e.X, e.Z, e, 0, hitstop: hitstop);
                hitstop = 0;
                FlareHit(e, f.Arg("hook", 0.5), f.School, 0, p.X, p.Z);
                if (!e.Alive || e.State == EnemyState.Dying) continue;
                dragHooked.Add((e, e.Id));
                // The haul: a slide to the knot (knockback settles at 9 a second, so v = 9 x the distance), each to its
                // place round it; a boss only 3 m, a fixed thing not at all.
                double kx = knotX - e.X, kz = knotZ - e.Z, kd = Len(kx, kz);
                if (kd < 1e-6 || e.Def.Behavior == Behavior.Stationary) continue;
                double room = f.Arg("knotSpread", 1.2) + e.Radius + 0.4 * (i++ % 3);
                double pull = e.Boss ? Math.Min(f.Arg("bossDrag", 3), Math.Max(0, kd - room)) : Math.Max(0, kd - room);
                e.Kbx = kx / kd * pull * 9;
                e.Kbz = kz / kd * pull * 9;
                if (e.Boss || e.Elite) Interrupt(e);
            }
            if (hooks.Count == 0)
            {
                // Nothing near: the hooks bite the ground round her reach and haul the earth to her feet.
                int n = (int)f.Arg("emptyHooks", 8);
                for (int k = 0; k < n; k++)
                {
                    double a = flareAngle + Math.PI * 2 * k / n;
                    FlareBlowEvent(f, "hook", false, p.X + Math.Cos(a) * reach, p.Z + Math.Sin(a) * reach, null, 0, hitstop: hitstop);
                    hitstop = 0;
                }
            }
            return;
        }
        if (!last && flareBlow == 2)
        {
            FlareBlowEvent(f, "knot", false, knotX, knotZ, null, slamR, hitstop: 0);
            return;
        }
        if (!last)
        {
            // Grinder: the knot shredded for a breath.
            ForEachHostileInRadius(knotX, knotZ, slamR, (e, d) => FlareHit(e, f.Arg("grind", 0.25), f.School, 0, knotX, knotZ));
            FlareBlowEvent(f, "grind", false, knotX, knotZ, null, slamR, hitstop: 0);
            return;
        }
        // The slam: what is in the knot and every thing still on a hook.
        var struck = HostilesInRadius(knotX, knotZ, slamR).Where(e => !e.Boss || FlareCanHurt(e)).ToList();
        foreach (var (e, id) in dragHooked)
            if (e.Id == id && e.Alive && e.State != EnemyState.Dying && !struck.Contains(e)) struck.Add(e);
        foreach (var e in struck)
        {
            if (!e.Alive || e.State == EnemyState.Dying) continue;
            FlareHit(e, f.Arg("slam", 1.75), f.School, 0.5, knotX, knotZ);
            if (!e.Alive || e.State == EnemyState.Dying) continue;
            if (e.Boss)
            {
                Interrupt(e);
                ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, f.Arg("bossStun", 1.5)), 0);
                if (FlareMod("drag.hold_him")) ApplyStatus(e, new StatusPayload(StatusKind.Bound, 1, 1, f.Arg("hold", 3)), 0);
            }
            else ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, f.Arg("stun", 1)), 0);
        }
        dragHooked.Clear();
        FlareBlowEvent(f, "slam", true, knotX, knotZ, null, slamR);
    }

    /* --------------------------------------------------------- The Butcher's Bill -- */

    Enemy? billOn;
    int billOnId = -1, billVaults;
    double billX, billZ;

    /// <summary>The leap (at "leap", before the landing): the strongest within reach, or 6 m along her aim with nothing near.
    /// Event "leap": X/Z where she springs from, TX/TZ where she means to land, Target.</summary>
    void BillAim(FlareDef f)
    {
        var p = Player;
        billVaults = 0;
        billOn = BillPick(p.X, p.Z, flareReach);
        billOnId = billOn?.Id ?? -1;
        billX = p.X + Math.Cos(flareAngle) * f.Arg("emptyLeap", 6);
        billZ = p.Z + Math.Sin(flareAngle) * f.Arg("emptyLeap", 6);
        if (billOn != null) { billX = billOn.X; billZ = billOn.Z; }
        Events.Emit(new Ev.Flare { Phase = FlarePhase.Blow, Id = f.Id, X = p.X, Z = p.Z, TX = billX, TZ = billZ, Target = billOn?.Id ?? 0, Part = "leap", Clutch = flareClutch });
    }

    /// <summary>The Bill's chops: one per tenth of health missing at the press (at least "minChops", at most "maxChops").</summary>
    int BillChops(FlareDef f) =>
        (int)Math.Clamp(Math.Floor((1 - Player.Hp / Math.Max(1, MaxHp)) * 10 + 1e-9), f.Arg("minChops", 4), f.Arg("maxChops", 10));

    /// <summary>The strongest she can reach from (x, z): a boss she can hurt, then champions, then the most health.</summary>
    Enemy? BillPick(double x, double z, double r, Enemy? not = null) =>
        HostilesInRadius(x, z, r).Where(e => e != not && e.Alive && e.State != EnemyState.Dying && FlareCanHurt(e) && Targetable(e))
            .OrderByDescending(e => e.Boss).ThenByDescending(e => e.Elite).ThenByDescending(e => e.Hp).FirstOrDefault();

    /// <summary>Lands her beside the thing, on the far side from where she came (behind it), inside its reach.</summary>
    void BillLand(FlareDef f, Enemy? on, double tx, double tz, string part)
    {
        var p = Player;
        double x0 = p.X, z0 = p.Z;
        if (on != null)
        {
            double dx = on.X - p.X, dz = on.Z - p.Z, d = Len(dx, dz);
            if (d < 1e-6) { dx = Math.Cos(flareAngle); dz = Math.Sin(flareAngle); d = 1; }
            double off = on.Radius + p.Radius + 0.3;
            tx = on.X + dx / d * off;
            tz = on.Z + dz / d * off;
        }
        p.X = tx; p.Z = tz;
        Collision.Resolve(ref p.X, ref p.Z, p.Radius, true);
        p.Vx = p.Vz = 0;
        if (on != null) p.Facing = Math.Atan2(on.X - p.X, on.Z - p.Z);
        Events.Emit(new Ev.Flare { Phase = FlarePhase.Blow, Id = f.Id, X = x0, Z = z0, TX = p.X, TZ = p.Z, Target = on?.Id ?? 0, Part = part, Blow = flareBlow, Clutch = flareClutch });
    }

    /// <summary>Each blow of the Bill: at the first she leaps on the strongest and chops; each chop on what she stands on.</summary>
    void BillBlow(FlareDef f, bool last)
    {
        var p = Player;
        // She lands with the first chop (beside it where it stands now; on open ground where she aimed).
        if (flareBlow == 1)
        {
            var at = billOn != null && billOn.Id == billOnId && billOn.Alive && billOn.State != EnemyState.Dying ? billOn : BillPick(billX, billZ, f.Arg("vault", 6) * FlareGrow(f));
            if (at != billOn) { billOn = at; billOnId = at?.Id ?? -1; }
            BillLand(f, billOn, billX, billZ, "land");
        }
        var on = billOn != null && billOn.Id == billOnId && billOn.Alive && billOn.State != EnemyState.Dying ? billOn : null;
        if (on == null && billOn != null)
        {
            // It fell: the chops left go with her to the next strongest near it (Running Tab: twice).
            if (billVaults < (FlareMod("bill.running_tab") ? 2 : 1) && BillPick(p.X, p.Z, f.Arg("vault", 6) * FlareGrow(f)) is { } next)
            {
                billVaults++;
                billOn = on = next;
                billOnId = next.Id;
                BillLand(f, next, 0, 0, "vault");
            }
            else billOn = null;
        }
        double cx = on?.X ?? p.X + Math.Cos(flareAngle) * 0.9, cz = on?.Z ?? p.Z + Math.Sin(flareAngle) * 0.9;
        if (on != null)
        {
            double dealt = FlareHit(on, f.Arg("chop", 1.5) * (last ? f.Arg("lastChop", 1.5) : 1), f.School, last ? 1.5 : 0, p.X, p.Z);
            HealPlayer(MaxHp * f.Arg("mend", 0.02), "flare", true);
            // The splash: what stands 2 m round bleeds (Wide Chops: struck too).
            double r = f.Arg("splash", 2) * FlareGrow(f);
            ForEachHostileInRadius(cx, cz, r, (e, d) =>
            {
                if (e != on && FlareMod("bill.wide_chops") && !e.Boss) FlareHit(e, f.Arg("chop", 1.5) * f.Arg("wide", 0.6), f.School, 0.6, cx, cz);
                if (e.Alive && e.State != EnemyState.Dying && dealt > 0)
                    ApplyStatus(e, new StatusPayload(StatusKind.Bleed, 1, f.Arg("bleed", 0.4), f.Arg("bleedSeconds", 3)), dealt);
            });
        }
        FlareBlowEvent(f, "chop", last, cx, cz, on, on != null ? f.Arg("splash", 2) * FlareGrow(f) : 0);
    }

    /// <summary>The Bill's kills: Feast mends 10% for each while it plays.</summary>
    void BillOnKilled(Enemy e, bool credited)
    {
        if (credited && credit == "flare" && FlareT > 0 && Flare is { Id: "the_butchers_bill", Staged: true } f && FlareMod("bill.feast"))
            HealPlayer(MaxHp * f.Arg("feast", 0.1), "flare", true);
    }
}
