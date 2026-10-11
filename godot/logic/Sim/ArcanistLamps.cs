using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* The arcanist quarter's phase-1 rules (docs/design/CLASSES.md section 2): the Kindler's fire and frost
 * (shatter, burning ground, Cinderfall), the Moonweaver's marks and motes, and the crossing blues
 * (the Echo, the Crowded Sky, the Ledger, Frostfire, Ash-Walker, Unbound Casting). Sizes read through
 * Size/SizeOn (a quarter by night); prices, thresholds, defining times through Full; counts are at most
 * one more by night. Already wired elsewhere: spellward.thick (Forms.cs), flare.spell_fill /
 * flare.low_mirrors / flare.banked (Flare.cs), skill.area (Weapons.cs AreaOf). */
public sealed partial class Battle
{
    bool shattering, inYourFire, inYourGround;
    double arcScan, standHeld;
    int lastSide, pendingSide, volleyId;
    WeaponInst? castingW, statusWeapon;
    readonly List<(double Due, WeaponInst W)> echoes = new();
    readonly Dictionary<int, (double T, HashSet<int> Hit)> volleyHit = new();
    readonly Dictionary<string, (int Id, double T, int N)> volleyOf = new();
    static readonly Tag[] ShatterTags = [Tag.Explosion, Tag.Frost];

    /// <summary>A count a lamp adds: whole numbers by day, at most one by night (Lamps.Night).</summary>
    int CountCap(double raw)
    {
        int n = (int)Math.Floor(Math.Max(0, raw) + 1e-9);
        return Lamps.Night ? Math.Min(1, n) : n;
    }

    /// <summary>A skill's or tag's count lamp at its full number (the night's cap is CountCap's).</summary>
    double RawOn(string rule, string arg, WeaponInst w) =>
        Lamps.SizeOn(rule, arg, w.Def.Id, w.Tags) / (Lamps.Night ? Content.Lamps.NightSize : 1);

    /// <summary>Spells with projectiles, while the Crowded Sky is lit.</summary>
    bool CrowdOn(WeaponInst w) => Lamp("crowded_sky") && w.Tags.Has(Tag.Spell) && w.Tags.Has(Tag.Projectile);

    /// <summary>How much of the Crowded Sky's gift the cast really has: the night caps counts
    /// (a lit Many Lights may already hold the one extra), and its price, "each weaker", is
    /// owed only for the projectiles it truly looses (a price on a gift withheld would be pure loss).</summary>
    double CrowdShare(WeaponInst w)
    {
        double add = Lamps.Full("crowded_sky", "add", 2);
        if (add <= 0) return 1;
        double others = RawOn("tags.projectiles", "add", w) + (w.Def.Id == "cinderfall" && Lamps.Has("cinderfall.two") ? 1 : 0);
        int gained = CountCap(others + add) - CountCap(others);
        return Math.Clamp(gained / add, 0, 1);
    }

    /// <summary>Per tick: where the survivor stands (her burning or frozen ground), the echoes due, the volleys forgotten.</summary>
    void TickArcanist(double dt)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) { if (echoes.Count > 0) echoes.Clear(); return; }
        for (int i = echoes.Count - 1; i >= 0; i--)
            if (Time >= echoes[i].Due)
            {
                var w = echoes[i].W;
                echoes.RemoveAt(i);
                // the_echo: the spell fires again, at the strength the lamp gives.
                BeforeCast(w, true);
                Firing.Echo(this, w);
                castingW = null;
            }
        if ((arcScan -= dt) > 0) return;
        arcScan = 0.25;
        var p = Player;
        inYourFire = false; bool frost = false;
        foreach (var g in Zones.Items)
        {
            if (!g.Alive || g.Owner != Side.Player || Dist(g.X, g.Z, p.X, p.Z) >= g.Radius) continue;
            if (g.School == School.Fire) inYourFire = true;
            else if (g.School == School.Frost) frost = true;
        }
        inYourGround = inYourFire || frost;
        // kindler.stand_in_your_fire: armor while standing in her burning ground.
        double v = inYourFire && l.Has("stand_in_fire") ? l.Size("stand_in_fire", "armor") : 0;
        if (v != standHeld)
        {
            standHeld = v;
            Stats.RemoveSource("lamp:stand_in_fire");
            if (v > 0) Stats.Add(new StatMod(Stat.Armor, ModKind.Inc, v, "lamp:stand_in_fire"));
        }
        if (volleyHit.Count > 32)
            foreach (var k in new List<int>(volleyHit.Keys)) if (Time - volleyHit[k].T > 6) volleyHit.Remove(k);
    }

    /* ------------------------------------------------------------- casting -- */

    static int SideOf(School s) => s is School.Fire or School.Frost ? 1 : s is School.Arcane or School.Shadow ? 2 : 0;

    /// <summary>Before a spell is cast: the strength this cast carries (Ledger, Crowded Sky, Echo).</summary>
    public void ArcanistBeforeCast(WeaponInst w) => BeforeCast(w, false);

    void BeforeCast(WeaponInst w, bool echo)
    {
        double m = 1;
        castingW = w;
        // Each cast is its own volley (a burst still firing must not run into the next cast's: the
        // 0.3 s window alone chained quick casters into one volley that hit each enemy only once).
        volleyOf.Remove(w.Id);
        if (Lamps.Rules.Count > 0 && w.Tags.Has(Tag.Spell))
        {
            // moonweaver.the_echo: the second cast is at a share of the first.
            if (echo) m *= Math.Min(1, Lamps.Size("the_echo", "share", 0.5));
            // moonweaver.crowded_sky: every projectile is weaker (a price, kept in full).
            if (CrowdOn(w)) m *= 1 - Lamps.Full("crowded_sky", "weaker", 0.35) * CrowdShare(w);
            // arcanist.bridge.the_ledger: fire/frost and moon/shadow take turns.
            if (!echo && Lamp("the_ledger") && SideOf(w.School) is var side and > 0)
            {
                if (pendingSide == side) m *= 1 + Lamps.Size("the_ledger", "more");
                if (lastSide == side) m *= 1 - Lamps.Full("the_ledger", "weaker", 0.15);
            }
        }
        w.CastMul = m;
    }

    /// <summary>After a spell is cast: the Ledger turns, and the Echo is set.</summary>
    public void ArcanistAfterCast(WeaponInst w, bool fired)
    {
        castingW = null;
        if (!fired || Lamps.Rules.Count == 0 || !w.Tags.Has(Tag.Spell)) return;
        if (Lamp("the_ledger") && SideOf(w.School) is var side and > 0) { lastSide = side; pendingSide = 3 - side; }
        if (Lamp("the_echo")) echoes.Add((Time + Lamps.Full("the_echo", "delay", 0.5), w));
    }

    /// <summary>The wait on a skill: Unbound Casting, Stand in Your Fire, the Echo's price, Swift Motes.</summary>
    public double ArcanistCooldownMul(WeaponInst w)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return 1;
        double m = 1;
        if (w.Tags.Has(Tag.Spell))
        {
            // arcanist.unbound_casting: spells wait less.
            if (l.Has("unbound_casting")) m *= 1 - Math.Min(0.9, l.Size("unbound_casting", "sooner"));
            // kindler.stand_in_your_fire: spells come sooner in her burning ground.
            if (inYourFire && l.Has("stand_in_fire")) m *= 1 - Math.Min(0.9, l.Size("stand_in_fire", "sooner"));
            // moonweaver.the_echo: spells wait longer (a price).
            if (l.Has("the_echo")) m *= 1 + l.Full("the_echo", "longer", 0.25);
        }
        // moonweaver.seeking_motes.swift_motes (skill.sooner; Iron Palms' side is ReaverCooldownMul's).
        if (w.Def.Id == "seeking_motes" && l.SizeOn("skill.sooner", "sooner", w.Def.Id, w.Tags) is var sooner and > 0) m /= 1 + sooner;
        return m;
    }

    /// <summary>Projectiles a spell looses beyond its own: Many Lights, Cinderfall's second, the Crowded Sky (one by night).</summary>
    public int ArcanistProjectiles(WeaponInst w)
    {
        var l = Lamps;
        if (l.Rules.Count == 0 || !w.Tags.Has(Tag.Projectile)) return 0;
        // moonweaver.many_lights (tags.projectiles on spells)
        double raw = RawOn("tags.projectiles", "add", w);
        // kindler.cinderfall.two_cinders
        if (w.Def.Id == "cinderfall" && l.Has("cinderfall.two")) raw += 1;
        // moonweaver.crowded_sky
        if (CrowdOn(w)) raw += l.Full("crowded_sky", "add", 2);
        return CountCap(raw);
    }

    /// <summary>Projectile speed: arcane flies faster (tags.projectile_speed), Heavy Motes fly slower.</summary>
    public double ArcanistSpeedMul(WeaponInst w)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return 1;
        double m = 1 + l.SizeOn("tags.projectile_speed", "inc", w.Def.Id, w.Tags);
        // moonweaver.seeking_motes.heavy_motes: "fly slower" (design pick: 15%, a price kept in full).
        if (w.Def.Id == "seeking_motes" && l.HasOn("skill.harder", w.Def.Id, w.Tags)) m *= 0.85;
        return m;
    }

    /// <summary>moonweaver.moon_drawn: Seeking Motes seek the marked first (unless the skill hunts something else).</summary>
    public Seek? ArcanistSeek(WeaponInst w, Seek? seek) =>
        seek == null && w.Def.Id == "seeking_motes" && Lamp("moon_drawn") ? Seek.Marked : seek;

    /// <summary>moonweaver.crowded_sky: each projectile seeks, and takes its own mark of the sky.</summary>
    public void ArcanistLaunched(Projectile pr, WeaponInst w)
    {
        if (!CrowdOn(w)) return;
        pr.Homing = Math.Max(pr.Homing, 5.5);
        if (!volleyOf.TryGetValue(w.Id, out var v) || Time - v.T > 0.3) v = (++volleyId, Time, 0);
        v = (v.Id, Time, v.N + 1);
        volleyOf[w.Id] = v;
        pr.Volley = v.Id;
        pr.VolleyHard = CrowdShare(w) >= 1;
        volleyHit.TryAdd(v.Id, (Time, new HashSet<int>()));
        // Each looses at a different thing: the k-th nearest.
        var near = HostilesInRadius(Player.X, Player.Z, 14);
        if (near.Count == 0 || pr.Seek is Seek.Elite or Seek.Strongest or Seek.Marked) return;
        near.Sort((a, c) => Dist(a.X, a.Z, Player.X, Player.Z).CompareTo(Dist(c.X, c.Z, Player.X, Player.Z)));
        pr.Target = near[(v.N - 1) % near.Count].Id;
    }

    /// <summary>moonweaver.crowded_sky: no two of a volley strike the same thing.</summary>
    bool VolleyTaken(Projectile pr, int enemy) => pr.Volley != 0 && volleyHit.TryGetValue(pr.Volley, out var v) && v.Hit.Contains(enemy);

    /// <summary>A player projectile struck: the volley remembers it, and Split Motes split on a kill.</summary>
    void ArcanistOnProjectileHit(Projectile pr, Enemy e, WeaponInst? weapon)
    {
        if (pr.Volley != 0 && volleyHit.TryGetValue(pr.Volley, out var v)) v.Hit.Add(e.Id);
        // moonweaver.seeking_motes.split_motes: a mote that kills splits in two (design pick: each at half).
        if (weapon?.Def.Id != "seeking_motes" || !Lamp("motes.split") || e.State != EnemyState.Dying || pr.Depth >= 1) return;
        for (int i = 0; i < 2; i++)
        {
            double a = Math.Atan2(pr.Vz, pr.Vx) + (i - 0.5) * 0.9, sp = pr.Speed * 0.85;
            var c = SpawnProjectile(pr.Owner, pr.X, pr.Z, pr.Damage * 0.5, pr.School);
            if (c == null) continue;
            c.Y = pr.Y; c.Vx = Math.Cos(a) * sp; c.Vz = Math.Sin(a) * sp; c.Speed = sp; c.Tags = pr.Tags; c.Radius = pr.Radius * 0.7;
            c.Pierce = 0; c.Life = 0.9; c.Homing = Math.Max(pr.Homing, 3); c.Weapon = pr.Weapon; c.Art = pr.Art; c.Status = pr.Status;
            c.Depth = pr.Depth + 1; c.Rank = pr.Rank;
            c.AimAlongVelocity();
            c.Hits.Add(e.Id); c.HitTimes.Add(Time);
        }
    }

    /* -------------------------------------------------------------- damage -- */

    /// <summary>The damage rules of the arcanist quarter that read the target (a multiplier).</summary>
    double ArcanistDamageMul(Enemy e, School school, Tag[] tags, HitOpts o)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return 1;
        double m = 1;
        var s = e.Status;
        string id = o.Weapon?.Id ?? "";
        if (s.Has(StatusKind.Mark))
        {
            // moonweaver.s1: marked things take more from projectiles.
            if (o.Projectile || tags.Has(Tag.Projectile)) m += l.Size("marked.projectiles", "more");
            // moonweaver.s6: arcane strikes champions harder while they are marked.
            if (school == School.Arcane && e.Elite && !e.Boss) m += l.Size("marked.arcane_champions", "more");
            // moonweaver.silvered: the marked take more.
            m += l.Size("silvered", "more");
        }
        // kindler.s1 / s7: burning takes more from frost, frozen more from fire.
        if (school == School.Frost && s.Has(StatusKind.Burn)) m += l.Size("burning.frost", "more");
        if (school == School.Fire && s.Has(StatusKind.Frozen)) m += l.Size("frozen.fire", "more");
        // kindler.s6: shatters strike champions harder.
        if (shattering && e.Elite && !e.Boss) m += l.Size("shatter.champions", "more");
        // moonweaver.seeking_motes.heavy_motes
        if (id == "seeking_motes") m += l.SizeOn("skill.harder", "more", id, tags);
        // The cast's own strength (Ledger, Crowded Sky, Echo) on what a spell strikes at once; projectiles carry it from the hand.
        if (castingW != null && o.Weapon == castingW && !o.Projectile && !o.Dot) m *= castingW.CastMul;
        // kindler.ash_walker: outside her ground, spells are weaker (a price, kept in full).
        if (l.Has("ash_walker") && !inYourGround && !o.Dot && tags.Has(Tag.Spell)) m *= 1 - l.Full("ash_walker", "weaker", 0.15);
        return m;
    }

    /// <summary>What a blow dealt now brings: the Motes' marks and chill, Frostfire, and the shatter of fire on ice.</summary>
    void ArcanistOnHit(Enemy e, School school, Tag[] tags, HitOpts o, double dmg)
    {
        var l = Lamps;
        if (o.Dot || o.Summon || l.Rules.Count == 0 || !e.Alive) return;
        if (o.Weapon?.Def.Id == "seeking_motes")
        {
            // moonweaver.moonmarked (design pick: a mark of 4 s, as Moonbrand's).
            if (l.Has("moonmarked")) ApplyStatus(e, new StatusPayload(StatusKind.Mark, 1, 1, 4), dmg, o.Depth + 1);
            // arcanist.bridge.cold_moon (design pick: half a chill's worth, 2.5 s).
            if (l.Has("cold_moon")) ApplyStatus(e, new StatusPayload(StatusKind.Chill, 1, 0.5, 2.5), dmg, o.Depth + 1);
        }
        // kindler.frostfire: fire chills and frost burns, each weaker (the price, in full). Burn and chill never cancelled here.
        if (l.Has("frostfire") && (o.Weapon != null || o.Projectile))
        {
            double k = 1 - l.Full("frostfire", "weaker", 0.3);
            if (school == School.Fire) ApplyStatus(e, new StatusPayload(StatusKind.Chill, 1, 1 * k, 2.5), dmg, o.Depth + 1);
            else if (school == School.Frost) ApplyStatus(e, new StatusPayload(StatusKind.Burn, 1, 0.25 * k, 3), dmg, o.Depth + 1);
        }
        // kindler.fire_on_ice / thermal_shock: fire on a frozen thing shatters it.
        if (!shattering && school == School.Fire && e.Status.Has(StatusKind.Frozen) && (l.Has("fire_on_ice") || l.Has("thermal_shock")))
        {
            double r = Math.Max(l.Full("fire_on_ice", "radius", 2), l.Full("thermal_shock", "radius", 3));
            double share = Math.Max(l.Size("fire_on_ice", "share", 0.5), l.Size("thermal_shock", "share", 1));
            e.Status.Remove(StatusKind.Frozen);
            e.ThawT = e.Elite ? 5 : 3;
            shattering = true;
            Explode(e.X, e.Z, r, dmg * share, School.Frost, ShatterTags, null, o.Depth + 1);
            shattering = false;
        }
    }

    /// <summary>A death: the mark passes on, and a marked thing's death mends.</summary>
    void ArcanistOnDeath(Enemy e, bool credited)
    {
        var l = Lamps;
        if (l.Rules.Count == 0 || e.Status[StatusKind.Mark] is not { } mark) return;
        // moonweaver.s4: a marked thing's death mends a sliver.
        if (credited && l.Has("marked.kill_mend")) HealPlayer(MaxHp * l.Size("marked.kill_mend", "share"), "lamp");
        // moonmarked / silvered / cold_moon: the mark passes (design pick: to the nearest unmarked within 6 m).
        int n = l.Has("moonmarked") ? (int)l.Full("moonmarked", "passes", 1) : l.Has("cold_moon") && e.Status.Has(StatusKind.Frozen) ? 1 : 0;
        if (n > 0 && l.Has("silvered")) n += CountCap(l.Full("silvered", "passes", 2) - 1);
        if (n == 0) return;
        var near = HostilesInRadius(e.X, e.Z, 6).FindAll(o => o != e && !o.Status.Has(StatusKind.Mark));
        near.Sort((a, c) => Dist(a.X, a.Z, e.X, e.Z).CompareTo(Dist(c.X, c.Z, e.X, e.Z)));
        for (int i = 0; i < Math.Min(n, near.Count); i++)
        {
            ApplyStatus(near[i], new StatusPayload(StatusKind.Mark, 1, mark.Power != 0 ? mark.Power : 1, 4), 0, 2);
            Events.Emit(new Ev.Chain { Points = [e.X, e.Z, near[i].X, near[i].Z], School = School.Arcane });
            // moonweaver.moonfire: the new bearer burns (a share of the dead one's health over 3 s; burning is fire here).
            if (l.Has("moonfire")) ApplyStatus(near[i], new StatusPayload(StatusKind.Burn, 1, l.Size("moonfire", "share", 0.2), 3), e.MaxHp, 2);
        }
    }

    /// <summary>How long a status lasts, with the arcanist lamps that stretch it.</summary>
    double ArcanistStatusDuration(StatusKind kind, double dur)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return dur;
        // moonweaver.s7: marks last longer.
        if (kind == StatusKind.Mark) dur *= 1 + l.Size("marks.longer", "inc");
        // kindler.cinderfall.slow_burning: the skill's burn lasts longer (the rate holds, the time stretches).
        if (kind == StatusKind.Burn && statusWeapon != null) dur *= 1 + l.SizeOn("skill.burn_longer", "inc", statusWeapon.Def.Id, statusWeapon.Tags);
        return dur;
    }

    /// <summary>Chill builds faster: on things in her fire (kindler.s2), and on the marked (bridge s2).</summary>
    double ArcanistChillMul(Enemy e)
    {
        var l = Lamps;
        if (l.Rules.Count == 0) return 1;
        double m = 1;
        if (l.Has("fire.chill_faster") && OnBurningGround(e.X, e.Z)) m += l.Size("fire.chill_faster", "inc");
        if (e.Status.Has(StatusKind.Mark)) m += l.Size("marked.freeze_sooner", "inc");
        return m;
    }

    /// <summary>Ground she lays: kindler.ashen_ground (burning ground lasts longer).</summary>
    void ArcanistZoneSpawned(GroundZone zn)
    {
        if (zn.Owner == Side.Player && zn.School == School.Fire && Lamp("ashen_ground")) zn.Life *= 1 + Lamps.Size("ashen_ground", "inc");
    }

    /// <summary>kindler.s4: zone spells last longer while she stands in one of her zones.</summary>
    public double ZoneLonger(WeaponInst w)
    {
        if (!w.Tags.Has(Tag.Zone) || !Lamp("zone.longer")) return 0;
        var p = Player;
        foreach (var g in Zones.Items)
            if (g.Alive && g.Owner == Side.Player && Dist(g.X, g.Z, p.X, p.Z) < g.Radius) return Lamps.Size("zone.longer", "inc");
        return 0;
    }

    /// <summary>kindler.ash_walker: in her burning or frozen ground she takes less.</summary>
    double ArcanistTakenMul() =>
        Lamp("ash_walker") && inYourGround ? 1 - Math.Min(0.9, Lamps.Size("ash_walker", "less")) : 1;
}
