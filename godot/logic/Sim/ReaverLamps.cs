using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* The reaver quarter's phase-1 rules (docs/design/CLASSES.md section 2): the Butcher's Frenzy, bleeds
 * and hurt-health mending, and the Chainbound's rules on Bound things. Sizes read through Size/SizeOn
 * (a quarter by night), prices, thresholds and defining times through Full. Red Tide's wait and the
 * Flare's rules live in Forms.cs and Flare.cs. Nothing in the game binds yet (the Chainbound's arts are
 * later work), so the Bound rules wait on a Bound thing; they are read the moment one exists. */
public sealed partial class Battle
{
    /// <summary>Frenzy stacks held (butcher.red_hands): each is a share of attack speed.</summary>
    double frenzy, frenzyIdle, frenzyGate;
    double boundScan, knotCool, boundArmorHeld = -1;
    int boundTotal;
    bool conducting;
    readonly Dictionary<string, double> soonerUsed = new();

    public double Frenzy => frenzy;

    double FrenzyCap() => Math.Max(Math.Max(Lamps.Full("frenzy", "cap", 20), Lamps.Has("frenzy.deep") ? Lamps.Full("frenzy.deep", "cap", 40) : 0), HandFrenzyCap);

    /// <summary>Butcher's Hour: Frenzy fills at once (as far as the lamps let it).</summary>
    void FillFrenzy() { if (FrenzyCap() > 0) AddFrenzy(FrenzyCap()); }

    void AddFrenzy(double n)
    {
        frenzy = Math.Min(FrenzyCap(), frenzy + n);
        frenzyIdle = 0;
    }

    /// <summary>The survivor is below the share of health Fights Best Hurt and Blood Up read (always, with Always Bleeding).</summary>
    bool BelowThird() => Lamp("always_bleeding") || Player.Hp < MaxHp * Lamps.Full("fights_best_hurt", "below", 0.3333);

    /// <summary>Per tick: Frenzy fades after a lull, and the Bound things are counted.</summary>
    void TickReaver(double dt)
    {
        var l = Lamps;
        // Frenzy fades first: the reaver's Hand fills it on an empty board too.
        if (frenzy > 0)
        {
            frenzyIdle += dt;
            // butcher.red_hands: it fades when the fight lulls (design pick: five stacks a second, once the lull is 3 s).
            // butcher.s7 (frenzy.slow_fade): half as fast.
            if (frenzyIdle > FrenzyFade()) frenzy = Math.Max(0, frenzy - 5 * (1 - Math.Min(0.9, l.Size("frenzy.slow_fade", "share"))) * dt);
        }
        if (l.Rules.Count == 0) return;
        knotCool -= dt;
        if (!l.Has("bound.armor") && !l.Has("bound.storm_reach") && !l.Has("knot")) return;
        if ((boundScan -= dt) > 0) return;
        boundScan = 0.25;
        var bound = new List<Enemy>();
        foreach (var e in Enemies.Items) if (e.Alive && e.State != EnemyState.Dying && e.Status.Has(StatusKind.Bound)) bound.Add(e);
        boundTotal = bound.Count;
        var p = Player;
        if (l.Has("bound.armor"))
        {
            // chainbound.s6: each Bound thing near gives armor, to a cap.
            double r = l.Full("bound.armor", "radius", 6), near = 0;
            foreach (var e in bound) if (Dist(e.X, e.Z, p.X, p.Z) <= r) near++;
            double v = Math.Min(l.Full("bound.armor", "cap", 10), near * l.Size("bound.armor", "per", 1));
            if (v != boundArmorHeld)
            {
                boundArmorHeld = v;
                Stats.RemoveSource("lamp:bound.armor");
                if (v > 0) Stats.Add(new StatMod(Stat.Armor, ModKind.Flat, v, "lamp:bound.armor"));
            }
        }
        // chainbound.knot: eight Bound things close together are stunned (design pick: not again for 4 s).
        if (l.Has("knot") && knotCool <= 0)
        {
            int need = (int)l.Full("knot", "count", 8);
            double kr = l.Full("knot", "radius", 3);
            foreach (var a in bound)
            {
                var pack = bound.FindAll(o => Dist(o.X, o.Z, a.X, a.Z) <= kr);
                if (pack.Count < need) continue;
                foreach (var o in pack)
                    if (!o.Boss) ApplyStatus(o, new StatusPayload(StatusKind.Stun, 1, 1, l.Full("knot", "seconds", 1)), 0);
                knotCool = 4;
                break;
            }
        }
    }

    /// <summary>Attack speed and "sooner" lamps: a multiplier on a skill's wait (Firing.CooldownOf).</summary>
    public double ReaverCooldownMul(WeaponInst w)
    {
        var l = Lamps;
        double m = 1;
        // butcher.red_hands: Frenzy is attack speed.
        if (frenzy > 0) m /= 1 + frenzy * FrenzyPer();
        // chainbound.iron_palms.palm_storm: strikes more often.
        // (Iron Palms only: the id is shared with the arcanist quarter's Swift Motes, which that quarter wires.)
        double sooner = w.Def.Id == "iron_palms" ? l.SizeOn("skill.sooner", "sooner", w.Def.Id, w.Def.Tags) : 0;
        if (sooner > 0) m /= 1 + sooner;
        return m;
    }

    /// <summary>chainbound.s7: storm skills reach further while enough things are Bound.</summary>
    public double StormReach(WeaponInst w) =>
        Lamp("bound.storm_reach") && w.Tags.Has(Tag.Storm) && boundTotal >= (int)Lamps.Full("bound.storm_reach", "at", 3) ? Lamps.Size("bound.storm_reach", "inc") : 0;

    /// <summary>chainbound.the_long_chain: melee skills reach further (metres).</summary>
    public double ChainReach(WeaponInst w) => Lamp("long_chain") && w.Tags.Has(Tag.Melee) ? Lamps.Full("long_chain", "reach", 3) : 0;

    /// <summary>chainbound.the_long_chain: the last thing a melee blow struck is hooked toward the survivor
    /// (design pick: the pull of a knockback of 0.8, backward).</summary>
    public void HookLast(WeaponInst w, Enemy last)
    {
        if (!Lamp("long_chain") || !w.Tags.Has(Tag.Melee) || !last.Alive || last.Boss || last.Def.Behavior == Behavior.Stationary) return;
        double dx = Player.X - last.X, dz = Player.Z - last.Z, d = Len(dx, dz);
        if (d < 1.5) return;
        double k = 0.8 * Stats.Get(Stat.Knockback) * 7 / Math.Max(0.5, last.Mass) * (last.Elite ? 0.35 : 1);
        last.Kbx += dx / d * k;
        last.Kbz += dz / d * k;
    }

    /// <summary>chainbound.lightning_rod: storm skills strike Bound things first.</summary>
    public List<Enemy> BoundFirst(WeaponInst w, List<Enemy> targets)
    {
        if (!Lamp("lightning_rod") || !w.Tags.Has(Tag.Storm)) return targets;
        var bound = targets.FindAll(e => e.Status.Has(StatusKind.Bound));
        return bound.Count > 0 ? bound : targets;
    }

    /// <summary>chainbound.iron_reach: Bound things beyond the palm's own reach, out to the lamp's reach.</summary>
    public List<Enemy> IronReachTargets(WeaponInst w, double ownReach)
    {
        var far = new List<Enemy>();
        if (w.Def.Id != "iron_palms" || !Lamp("iron_reach")) return far;
        var p = Player;
        foreach (var e in HostilesInRadius(p.X, p.Z, Lamps.Full("iron_reach", "reach", 6)))
            if (e.Status.Has(StatusKind.Bound) && Dist(e.X, e.Z, p.X, p.Z) > ownReach) far.Add(e);
        far.Sort((a, c) => Dist(a.X, a.Z, p.X, p.Z).CompareTo(Dist(c.X, c.Z, p.X, p.Z)));
        return far;
    }

    /// <summary>One palm thrown at a Bound thing out of its reach (chainbound.iron_reach).</summary>
    public void PalmFromAfar(WeaponInst w, Enemy t, StatusPayload? status)
    {
        var p = Player;
        double a = Math.Atan2(t.Z - p.Z, t.X - p.X), d = Dist(t.X, t.Z, p.X, p.Z);
        Events.Emit(new Ev.Slash { X = p.X, Z = p.Z, Angle = a, Arc = 0.6, Reach = d + 0.4, School = w.School, Art = w.Art, Rank = w.Rank });
        HitEnemy(t, w.Damage, w.School, w.Tags, new HitOpts { Weapon = w, Knockback = w.Num(s => s.Knockback) ?? 0, DirX = (t.X - p.X) / Math.Max(0.1, d), DirZ = (t.Z - p.Z) / Math.Max(0.1, d), Status = status, BossDamage = w.Def.BossDamage });
    }

    /// <summary>The damage rules of the reaver quarter that read the target (a multiplier).</summary>
    double ReaverDamageMul(Enemy e, School school, Tag[] tags, HitOpts o)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return 1;
        double m = 1;
        var s = e.Status;
        string id = o.Weapon?.Id ?? "";
        if (s.Has(StatusKind.Bleed))
        {
            // butcher.s1: bleeding things take more from melee.
            if (tags.Has(Tag.Melee)) m += l.Size("bleeding.melee", "more");
            // butcher.s6: thrown steel strikes bleeding things harder.
            m += l.SizeOn("tags.vs_bleeding", "more", id, tags);
        }
        if (s.Has(StatusKind.Bound))
        {
            bool storm = tags.Has(Tag.Storm) || school == School.Storm;
            // chainbound.s1: Bound things take more from storm.
            if (storm) m += l.Size("bound.storm", "more");
            // chainbound.s2: area skills strike Bound things harder.
            m += l.SizeOn("tags.vs_bound", "more", id, tags);
            // chainbound.iron_palms.palm_on_the_chain
            m += l.SizeOn("skill.vs_bound", "more", id, tags);
            // chainbound.lightning_rod: storm strikes Bound things harder.
            if (storm) m += l.Size("lightning_rod", "more");
        }
        // butcher.fights_best_hurt: blows strike harder when hurt.
        if (l.Has("fights_best_hurt") && BelowThird()) m += l.Size("fights_best_hurt", "more");
        // chainbound.the_long_chain: melee blows strike weaker (a price, kept in full).
        if (l.Has("long_chain") && tags.Has(Tag.Melee)) m *= 1 - l.Full("long_chain", "weaker", 0.2);
        return m;
    }

    /// <summary>What a blow dealt now brings: Frenzy, and the open vein.</summary>
    void ReaverOnHit(Enemy e, HitOpts o)
    {
        if (o.Dot || o.Summon || Lamps.Rules.Count == 0) return;
        var l = Lamps;
        // butcher.red_hands: each hit gives a stack (design pick: at most ten stacks a second, so a crowd in one swing is one).
        if (l.Has("frenzy") && (o.Weapon != null || o.Projectile))
        {
            if (Time >= frenzyGate) { frenzyGate = Time + 0.1; AddFrenzy(1); }
            // reaver.bridge.hook_and_hatchet: a blow on a Bound thing adds a stack more.
            if (l.Has("hook_and_hatchet") && e.Status.Has(StatusKind.Bound)) AddFrenzy(1);
        }
        // butcher.open_vein: a blow on a thing bleeding long enough bursts the bleed: what was left to bleed comes at once.
        if (l.Has("open_vein") && e.Alive && e.Status[StatusKind.Bleed] is { } bl && bl.Age >= l.Full("open_vein", "seconds", 3))
        {
            double left = bl.Power * Math.Max(0, bl.T) * Math.Max(1, bl.Stacks);
            e.Status.Remove(StatusKind.Bleed);
            if (left > 0) HitEnemy(e, left, School.Physical, DotBleed, new HitOpts { Dot = true, NoCrit = true, NoProcs = true, Depth = 2, Credit = "open_vein" });
        }
    }

    /// <summary>A kill the survivor is credited with: mending, and the Butcher's Count.</summary>
    void ReaverOnKill(Enemy e)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return;
        double mend = 0;
        // butcher.s4: below half health, kills mend a sliver.
        if (l.Has("low.kill_mend") && Player.Hp < MaxHp * l.Full("low.kill_mend", "below", 0.5)) mend += l.Size("low.kill_mend", "share");
        // butcher.fights_best_hurt: kills mend when hurt.
        if (l.Has("fights_best_hurt") && BelowThird()) mend += l.Size("fights_best_hurt", "mend");
        // butcher.red_work: killing a bleeding thing mends.
        if (l.Has("red_work") && e.Status.Has(StatusKind.Bleed)) mend += l.Size("red_work", "share");
        if (mend > 0) HealPlayer(MaxHp * mend, "lamp");
        // butcher.the_butchers_count: each kill gives damage for a while, to a cap.
        if (l.Has("butchers_count"))
            AddBuff("butchers_count", Stat.Damage, l.Size("butchers_count", "per", 0.01), ModKind.Inc, l.Full("butchers_count", "seconds", 10), (int)l.Full("butchers_count", "cap", 50));
    }

    /// <summary>butcher.axe_gyre.gyre_on_a_kill: a kill by the axes brings the next whirl sooner (once a whirl).</summary>
    void ReaverWeaponKill(WeaponInst w)
    {
        if (!Lamps.HasOn("skill.kill_sooner", w.Def.Id, w.Def.Tags)) return;
        if (soonerUsed.TryGetValue(w.Id, out double used) && used == w.ActiveT) return;
        soonerUsed[w.Id] = w.ActiveT;
        w.Timer *= 1 - Math.Min(0.9, Lamps.SizeOn("skill.kill_sooner", "sooner", w.Def.Id, w.Def.Tags));
    }

    /// <summary>How long a status lasts on this creature, with the lamps that stretch or fix it.</summary>
    double ReaverStatusDuration(Enemy e, StatusKind kind, double dur)
    {
        var l = Lamps;
        switch (kind)
        {
            case StatusKind.Bleed:
                // butcher.s2: bleeds last longer while Frenzy is high.
                if (l.Has("frenzy.bleed_longer") && frenzy >= l.Full("frenzy.bleed_longer", "at", 10)) dur *= 1 + l.Size("frenzy.bleed_longer", "inc");
                break;
            case StatusKind.Shock:
                // chainbound.s4: shock lasts longer on Bound things.
                if (e.Status.Has(StatusKind.Bound)) dur *= 1 + l.Size("bound.shock_longer", "inc");
                break;
            case StatusKind.Bound:
                // chainbound.fast_binding: Bound lasts the lamp's time.
                if (l.Has("fast_binding")) dur = l.Full("fast_binding", "seconds", 4);
                // reaver.bridge.red_chain: bleeding things stay Bound longer.
                if (e.Status.Has(StatusKind.Bleed)) dur += l.Size("red_chain", "seconds");
                break;
        }
        return dur;
    }

    /// <summary>Once a status has taken: Bound things bleed (red_chain), shock leaps along the chain (conductor).</summary>
    void ReaverAfterStatus(Enemy e, StatusPayload p, double hitDamage, int depth)
    {
        if (Lamps.Rules.Count == 0) return;
        // reaver.bridge.red_chain: Bound things bleed (design pick: a wound worth 0.6 of the blow, over 3 s).
        if (p.Kind == StatusKind.Bound && Lamp("red_chain")) ApplyStatus(e, new StatusPayload(StatusKind.Bleed, 1, 0.6, 3), hitDamage, depth + 1);
        // chainbound.conductor: shock on a Bound thing leaps to every other Bound thing.
        if (p.Kind == StatusKind.Shock && !conducting && Lamp("conductor") && e.Status.Has(StatusKind.Bound))
        {
            conducting = true;
            foreach (var o in Enemies.Items)
                if (o.Alive && o != e && o.State != EnemyState.Dying && o.Status.Has(StatusKind.Bound)) ApplyStatus(o, p, hitDamage, depth + 1);
            conducting = false;
        }
    }

    /// <summary>butcher.hamstrung: bleeding champions are slower (a multiplier on their speed).</summary>
    public double HamstrungMul(Enemy e) =>
        e.Elite && !e.Boss && Lamp("hamstrung") && e.Status.Has(StatusKind.Bleed) ? 1 - Math.Min(0.9, Lamps.Size("hamstrung", "slow", 0.2)) : 1;

    /// <summary>The prices of the reaver blue lamps on blows taken: the Butcher's Count (half the Count more,
    /// the Count counted at its full 1% a stack even by night) and the Lightning Rod (storm and fire).</summary>
    double ReaverTakenMul(School school)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return 1;
        double m = 1;
        if (l.Has("butchers_count") && Buffs.TryGetValue("butchers_count", out var count))
            m += l.Full("butchers_count", "price", 0.5) * count.Stacks * l.Size("butchers_count", "per", 0.01);
        if (l.Has("lightning_rod") && school is School.Storm or School.Fire) m += l.Full("lightning_rod", "price", 0.15);
        return m;
    }

    /// <summary>Mending's strength (reaver.nothing_spared: all mending stronger).</summary>
    double ReaverMendMul(string source)
    {
        if (!Lamp("no_draught")) return 1;
        return source == "draught" ? 0 : 1 + Lamps.Size("no_draught", "more", 0.5);
    }

    /// <summary>The most health mending can reach (butcher.always_bleeding: half, and the rest is lost).</summary>
    double MendCeiling() => Lamp("always_bleeding") ? Math.Max(Player.Hp, MaxHp * Lamps.Full("always_bleeding", "cap", 0.5)) : MaxHp;

    /// <summary>reaver.nothing_spared: the survivor has no draught.</summary>
    public bool NoDraught => Lamp("no_draught");
}
