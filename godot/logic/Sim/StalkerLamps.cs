using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* The stalker quarter's phase-1 rules (docs/design/CLASSES.md section 2): the Road-Knife's Opening and
 * poison, the Verge-Hunter's reach and arrows, and the crossing blues. "Strikes true" is a sure
 * critical strike. Sizes read through Size/SizeOn (a quarter by night); prices, thresholds and defining
 * times through Full; counts are at most one more by night (CountCap). Already wired elsewhere:
 * flare.perfect_fill / low_unseen / banked (Flare.cs), light_step (Battle.DashLength; its third charge is
 * the lamp's stat), tags.projectile_speed (ArcanistSpeedMul reads it for every tag), the skill.status of
 * Volley and Knifestorm for a hit (below; Weapons.StatusWith serves the cone skills). */
public sealed partial class Battle
{
    double openingUntil, stalkScan, herdUntil;
    bool poisonNear, trueArrow;
    readonly HashSet<int> dashCut = new();
    /// <summary>The stalker's own skills that the skill lamps (skill.projectiles / pierce / status) reach.</summary>
    static bool StalkerSkill(WeaponInst w) => w.Def.Id is "volley" or "knifestorm";

    /// <summary>A count a lamp adds, at its full number (the night's cap is CountCap's).</summary>
    double RawCount(string rule, string arg) => Lamps.Size(rule, arg) / (Lamps.Night ? Content.Lamps.NightSize : 1);

    /// <summary>A poison (design pick: 0.4 of the blow over 3 s per stack, a modest venom).</summary>
    static readonly StatusPayload Venom = new(StatusKind.Poison, 1, 0.4, 3);

    /// <summary>A blow of the survivor's own: not damage over time, not a summon's.</summary>
    static bool Blow(in HitOpts o) => !o.Dot && !o.Summon && (o.Weapon != null || o.Projectile);

    /// <summary>The stack cap on a poison: ten, or none while the Adder's Patience is lit.</summary>
    public int StalkerPoisonCap => Lamp("adders_patience") ? 1000 : 10;

    /// <summary>roadknife.adders_patience: the survivor cannot strike true.</summary>
    public bool StalkerNoTrue => Lamps.Rules.Count > 0 && Lamp("adders_patience");

    /// <summary>Per tick: poison near (for the dash), and the dash that cuts what it passes through.</summary>
    void TickStalker(double dt)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return;
        var p = Player;
        if ((stalkScan -= dt) <= 0)
        {
            stalkScan = 0.25;
            poisonNear = false;
            if (l.Has("poison.dash_faster"))
            {
                double r = l.Full("poison.dash_faster", "radius", 4);
                poisonNear = HostilesInRadius(p.X, p.Z, r).Exists(e => e.Status[StatusKind.Poison] is { T: > 0 });
            }
        }
        // roadknife.through_not_around: dashing through things cuts them (design pick: 12 blow, as the perfect dash's crack),
        // and each one cut gives back a share of a dash.
        if (p.DashT > 0 && l.Has("through_not_around"))
        {
            double power = Stats.Get(Stat.AbilityPower), share = l.Size("through_not_around", "share");
            ForEachHostileInRadius(p.X, p.Z, 1.1, (e, d) =>
            {
                if (!dashCut.Add(e.Id)) return;
                HitEnemy(e, 12 * power, School.Physical, [Tag.Physical], new HitOpts { DirX = p.DashDX, DirZ = p.DashDZ, NoProcs = true, Credit = "dash" });
                p.DashRecharge = Math.Min(Abilities.Dash.Recharge, p.DashRecharge + Abilities.Dash.Recharge * share);
            });
        }
    }

    /// <summary>A dash begins: the Opening, the true arrow, the quick hands.</summary>
    void StalkerOnDash()
    {
        var l = Lamps;
        dashCut.Clear();
        if (l.Rules.Count == 0) return;
        var p = Player;
        // roadknife.opening / wide_opening: for 2 s (3 s wide) after a dash the blows strike true.
        double open = Math.Max(l.Full("opening", "seconds"), l.Full("opening.wide", "seconds"));
        if (open > 0)
        {
            openingUntil = Time + Abilities.Dash.Time + open;
            p.SureCritT = Math.Max(p.SureCritT, Abilities.Dash.Time + open);
        }
        // stalker.bridge.s2: after a dash, the next arrow strikes true.
        trueArrow = l.Has("dash.true_arrow");
        // stalker.bridge.quick_hands: after a dash, the next Volley looses at once.
        if (l.Has("quick_hands") && WeaponById("volley") is { } v) v.Timer = 0;
    }

    /// <summary>The chance a blow strikes true beyond its usual: the Far Eye, and the arrow after a dash.</summary>
    double StalkerCritAdd(Enemy e, Tag[] tags, HitOpts o)
    {
        var l = Lamps;
        if (l.Rules.Count == 0 || !Blow(o)) return 0;
        double c = 0;
        // verge_hunter.far_eye: from beyond 8 m, one time in four.
        if (l.Has("far_eye") && Dist(e.X, e.Z, Player.X, Player.Z) > l.Full("far_eye", "range", 8)) c += l.Full("far_eye", "chance", 0.25);
        // stalker.bridge.s2 (dash.true_arrow): the next arrow only.
        if (trueArrow && tags.Has(Tag.Ranged) && (o.Projectile || tags.Has(Tag.Projectile))) { trueArrow = false; c += 1; }
        return c;
    }

    /// <summary>The wait on a skill: standing still, projectiles come sooner.</summary>
    public double StalkerCooldownMul(WeaponInst w)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return 1;
        // verge_hunter.s6: standing still, projectiles come sooner.
        if (w.Tags.Has(Tag.Projectile) && Player.StillT > 0.25 && l.Has("still.projectiles_sooner"))
            return 1 / (1 + l.Size("still.projectiles_sooner", "sooner"));
        return 1;
    }

    /// <summary>How fast dashes come back: near poison (roadknife.s4), and Never Still (roadknife.never_still).</summary>
    double StalkerDashHaste()
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return 1;
        double h = 1;
        if (poisonNear) h *= 1 + l.Size("poison.dash_faster", "inc");
        if (l.Has("never_still")) h *= 1 + l.Size("never_still", "faster");
        return h;
    }

    /// <summary>roadknife.slip_the_blow: the perfect dash's window is longer.</summary>
    double StalkerDodgeWindow() => 1 + Lamps.Size("slip_the_blow", "inc");

    /// <summary>Projectiles Volley and Knifestorm loose beyond their own (fan_out, wide_volley): one more by night.</summary>
    public int StalkerProjectiles(WeaponInst w) =>
        Lamps.Rules.Count == 0 || !StalkerSkill(w) ? 0 : CountCap(RawCount("skill.projectiles", "add", w));

    double RawCount(string rule, string arg, WeaponInst w) =>
        Lamps.SizeOn(rule, arg, w.Def.Id, w.Tags) / (Lamps.Night ? Content.Lamps.NightSize : 1);

    /// <summary>A projectile's pierce: twice_fletched (one more by night), and the Hunter's Stillness.</summary>
    public int StalkerPierce(WeaponInst w, int n)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return n;
        if (StalkerSkill(w)) n += CountCap(RawCount("skill.pierce", "add", w));
        // verge_hunter.hunters_stillness: after a second still every arrow pierces everything; moving, none does.
        if (l.Has("hunters_stillness") && w.Tags.Has(Tag.Ranged) && w.Tags.Has(Tag.Projectile))
        {
            if (Player.Moving) return 0;
            if (Player.StillT > l.Full("hunters_stillness", "after", 1)) return 99;
        }
        return n;
    }

    /// <summary>A projectile of the stalker's launched: the Knifestorm's knives come back.</summary>
    public void StalkerLaunched(Projectile pr, WeaponInst w)
    {
        // roadknife.knifestorm.knives_return: the knives turn and come back through the crowd (design pick: twice the flight).
        if (w.Def.Id == "knifestorm" && Lamp("knifestorm.return")) { pr.Chakram = true; pr.Life *= 2; }
    }

    /// <summary>A hunt on the Spirit Herd's beasts goes to the strongest (run_it_down).</summary>
    public Seek? StalkerSeek(WeaponInst w, Seek? seek) =>
        w.Def.Id == "spirit_herd" && Time < herdUntil ? Seek.Strongest : seek;

    /// <summary>The damage rules of the stalker quarter (a multiplier).</summary>
    double StalkerDamageMul(Enemy e, School school, Tag[] tags, HitOpts o)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return 1;
        double m = 1;
        bool proj = o.Projectile || tags.Has(Tag.Projectile);
        // roadknife.s1: poisoned things take more from steel.
        if (tags.Has(Tag.Steel) && e.Status.Has(StatusKind.Poison)) m *= 1 + l.Size("poisoned.steel", "more");
        // roadknife.s6: thrown steel strikes harder within the Opening.
        if (tags.Has(Tag.Thrown) && Time < openingUntil) m *= 1 + l.Size("opening.thrown", "more");
        // verge_hunter.s1: projectiles strike harder at rooted or slowed things.
        if (proj && (e.Status.Has(StatusKind.Bound) || e.Status.Has(StatusKind.Chill) || e.Status.Has(StatusKind.Frozen))) m *= 1 + l.Size("projectiles.vs_held", "more");
        // verge_hunter.s4: the prey takes more from projectiles.
        if (proj && e.Prey) m *= 1 + l.Size("prey.projectiles", "more");
        // verge_hunter.s7: traps strike harder at things beyond 8 m.
        if (tags.Has(Tag.Trap) && Dist(e.X, e.Z, Player.X, Player.Z) > l.Full("tags.far", "range", 8)) m *= 1 + l.SizeOn("tags.far", "more", o.Weapon?.Id ?? "", tags);
        if (!Blow(o)) return m;
        double d = Dist(e.X, e.Z, Player.X, Player.Z);
        // verge_hunter.hold_the_distance / long_sight: blows from beyond 8 m strike harder; long_sight's price is within 4 m.
        if (l.Has("hold_the_distance") && d > l.Full("hold_the_distance", "range", 8)) m *= 1 + l.Size("hold_the_distance", "more");
        if (l.Has("long_sight"))
        {
            if (d > l.Full("long_sight", "range", 8)) m *= 1 + l.Size("long_sight", "more");
            else if (d < l.Full("long_sight", "near", 4)) m *= 1 - l.Full("long_sight", "weaker", 0.3);
        }
        // stalker.bridge.close_and_far: blades close, arrows far; in between both weaker (a price, in full).
        if (l.Has("close_and_far"))
        {
            double near = l.Full("close_and_far", "near", 4), far = l.Full("close_and_far", "far", 8);
            bool blade = tags.Has(Tag.Melee) || tags.Has(Tag.Steel), arrow = tags.Has(Tag.Ranged);
            if (blade && d < near || arrow && d > far) m *= 1 + l.Size("close_and_far", "more");
            else if ((blade || arrow) && d >= near && d <= far) m *= 1 - l.Full("close_and_far", "weaker", 0.15);
        }
        // roadknife.never_still: standing still for a second halves the blows until you move (a price, in full).
        if (l.Has("never_still") && Player.StillT > 1) m *= 1 - l.Full("never_still", "weaker", 0.5);
        return m;
    }

    /// <summary>What a blow dealt now brings: the true strike's poison, the skill's own status, the patient poison kept.</summary>
    void StalkerOnHit(Enemy e, HitOpts o, double dmg)
    {
        var l = Lamps;
        if (l.Rules.Count == 0 || !e.Alive || !Blow(o)) return;
        // roadknife.s2 / venom_edge: a true strike poisons (one stack; the Edge adds two, one by night).
        if (e.LastCrit)
        {
            int n = (l.Has("true.poison") ? (int)l.Full("true.poison", "stacks", 1) : 0) + (l.Has("venom_edge") ? CountCap(RawCount("venom_edge", "stacks")) : 0);
            for (int i = 0; i < n; i++) ApplyStatus(e, Venom, dmg, o.Depth + 1);
        }
        // roadknife.knifestorm.poisoned_steel / verge_hunter.volley.barbed: the skill's arrows and knives carry the lamp's status.
        if (o.Projectile && o.Weapon is { } w && StalkerSkill(w) && l.HasOn("skill.status", w.Def.Id, w.Tags)
            && l.Each["skill.status"].Find(x => x.Status != null && x.Skill == w.Def.Id) is { Status: { } k })
            ApplyStatus(e, k == StatusKind.Poison ? Venom : new StatusPayload(k, 1, 1, 3), dmg, o.Depth + 1);
        // roadknife.adders_patience: the poison never fades while you keep striking.
        if (l.Has("adders_patience") && e.Status[StatusKind.Poison] is { } ps) ps.T = Math.Max(ps.T, 3);
    }

    /// <summary>A status landed: roadknife.adders_kiss, ten poisons burst (not while the Patience lifts the cap).</summary>
    void StalkerAfterStatus(Enemy e, StatusPayload p, double hit, int depth)
    {
        if (p.Kind != StatusKind.Poison || !Lamp("adders_kiss") || Lamp("adders_patience")) return;
        if (e.Status[StatusKind.Poison] is not { } s || s.Stacks < Lamps.Full("adders_kiss", "cap", 10) || depth > 2) return;
        // The poison still to come is paid at once, in a ring round it (design pick: 2.5 m, nature).
        double payout = s.Power * Math.Max(0.5, s.T) * s.Stacks;
        e.Status.Remove(StatusKind.Poison);
        Explode(e.X, e.Z, 2.5, payout, School.Nature, [Tag.Nature, Tag.Area], null, depth + 1);
    }

    /// <summary>How long a status lasts on this thing: poison on champions (roadknife.s7).</summary>
    double StalkerStatusDuration(Enemy e, StatusKind kind, double dur) =>
        kind == StatusKind.Poison && e.Elite && !e.Boss && Lamp("poison.champions_longer")
            ? dur * (1 + Lamps.Size("poison.champions_longer", "inc")) : dur;

    /// <summary>A death: verge_hunter.run_it_down, the prey's death sends the Herd's beasts after the strongest.</summary>
    void StalkerOnDeath(Enemy e)
    {
        if (!e.Prey || !Lamp("run_it_down")) return;
        herdUntil = Time + 6; // design pick: for 6 s
        foreach (var pr in Projectiles.Items)
            if (pr.Alive && pr.Owner == Side.Player && pr.Weapon == "spirit_herd") { pr.Seek = Seek.Strongest; pr.Target = -2; pr.Homing = Math.Max(pr.Homing, 4); }
    }

    /// <summary>verge_hunter.spring_back: Vault springs back from the aim, even as the dash's form.</summary>
    void StalkerVaultAim(ref double ax, ref double az)
    {
        if (!Lamp("spring_back") || Aim is not { } a) return;
        double dx = a.X - Player.X, dz = a.Z - Player.Z, len = Len(dx, dz);
        if (len > 0.1) { ax = dx / len; az = dz / len; }
    }

    /// <summary>verge_hunter.spring_back: landing from a Vault looses a Volley.</summary>
    void StalkerVaultLanded()
    {
        if (Lamp("spring_back") && WeaponById("volley") is { } v) Firing.Echo(this, v);
    }
}
