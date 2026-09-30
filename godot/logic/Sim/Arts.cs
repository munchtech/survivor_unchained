using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/// <summary>The art in hand while it runs: how long each part has left,
/// what it has already struck, the reflections it left.</summary>
public sealed class ArtRun
{
    public double SprintT, WraithT, CinderT, EchoT, EchoX, EchoZ, EchoHp, EchoFacing;
    /// <summary>A charge or a haul on a chain: the survivor carried along a line.</summary>
    public AbilityKind? Rush;
    public double RushT, RushDX, RushDZ, RushSpeed, RushX0, RushZ0;
    public Enemy? Hooked;
    public double HookedAt = -99, Barrier;
    /// <summary>The wait the last use began, for the ring round the art.</summary>
    public double CdFull = 1;
    /// <summary>Fresh: kills in this window grow the art.</summary>
    public double HotT;
    public int HotKills, Drains;
    public double CinderLastX, CinderLastZ, ImageStrikeT;
    public bool BulwarkUp;
    public readonly HashSet<int> Struck = new();
    public readonly List<int> Trail = new();
    public Enemy? Echo;

    public void Clear()
    {
        SprintT = WraithT = CinderT = EchoT = RushT = HotT = 0;
        Rush = null; Hooked = null; Echo = null;
        Struck.Clear(); Trail.Clear();
    }
}

public sealed partial class Battle
{
    public readonly ArtRun Art = new();
    /// <summary>The facets chosen for the art in hand.</summary>
    public readonly HashSet<string> Facets = new();
    public int ArtRank = 1;
    /// <summary>What the art has grown by in this fight, not yet written to the survivor.</summary>
    public double ArtXp;
    /// <summary>Reflections and echoes: what the horde turns on instead of you.</summary>
    public readonly List<Enemy> Decoys = new();

    public bool Has(string facet) => Facets.Contains(facet);
    double ArtPower => Stats.Get(Stat.AbilityPower) * Abilities.RankPower(ArtRank);

    static readonly Tag[] RushTags = [Tag.Melee, Tag.Physical], FrostTags = [Tag.Spell, Tag.Frost, Tag.Area],
        ShadowTags = [Tag.Spell, Tag.Shadow], ArcaneTags = [Tag.Spell, Tag.Arcane, Tag.Area], FireTags = [Tag.Fire, Tag.Area, Tag.Zone],
        SnareTags = [Tag.Trap, Tag.Physical, Tag.Zone], KnifeTags = [Tag.Projectile, Tag.Thrown, Tag.Physical, Tag.Steel],
        SlamTags = [Tag.Melee, Tag.Area, Tag.Physical], HolyTags = [Tag.Spell, Tag.Holy, Tag.Area];

    /// <summary>Change the art in hand (between fights, or a facet newly opened).</summary>
    public void SetArt(AbilityKind? kind, int rank, IEnumerable<string> facets)
    {
        Ability = kind;
        ArtRank = Math.Clamp(rank, 1, Abilities.MaxRank);
        Facets.Clear();
        Facets.UnionWith(facets);
    }

    /// <summary>Q: the art in hand.</summary>
    public bool UseAbility(double dirX, double dirZ)
    {
        var p = Player;
        if (!Combat || !p.Alive || Ability is not { } kind || p.Leap != null || Art.Rush != null) return false;
        // The second press of an echo steps back into it.
        if (kind == AbilityKind.EchoStep && Art.EchoT > 0) { Recall(); return true; }
        if (p.AbilityCd > 0) return false;
        var def = Abilities.All[kind];
        double ax = dirX, az = dirZ;
        if (Aim is { } aim) { ax = aim.X - p.X; az = aim.Z - p.Z; }
        if (Len(ax, az) < 0.1) { ax = Math.Sin(p.Facing); az = Math.Cos(p.Facing); }
        double m = Len(ax, az);
        ax /= m; az /= m;
        double angle = Math.Atan2(az, ax);
        double power = ArtPower;
        p.AbilityCd = def.Cooldown * Stats.Get(Stat.AbilityCooldown) * Abilities.RankHaste(ArtRank);
        Art.Struck.Clear();
        bool used = kind switch
        {
            AbilityKind.ShieldBash => ShieldBash(def, angle, power),
            AbilityKind.Bulwark => Bulwark(def, angle),
            AbilityKind.Leap => Leap(def, ax, az, angle),
            AbilityKind.Warcry => Warcry(def, angle, power),
            AbilityKind.Blink => Blink(def, ax, az, angle, power),
            AbilityKind.TimeSlip => TimeSlip(def, angle, power),
            AbilityKind.MarkPrey => MarkPrey(def, angle),
            AbilityKind.SmokeBomb => SmokeBomb(def, angle, power),
            AbilityKind.Sprint => Sprint(def, angle),
            AbilityKind.MirrorStep => MirrorStep(def, ax, az, angle),
            AbilityKind.BullRush => BullRush(def, ax, az, angle),
            AbilityKind.WraithWalk => WraithWalk(def, angle),
            AbilityKind.CinderTrail => CinderTrail(def, angle),
            AbilityKind.Grapple => Grapple(def, ax, az, angle),
            AbilityKind.EchoStep => EchoStep(def, angle),
            AbilityKind.Vault => Vault(def, dirX, dirZ, ax, az, angle, power),
            _ => false,
        };
        if (!used) return false;
        Art.CdFull = Math.Max(0.1, p.AbilityCd);
        ArtXp += 1;
        Art.HotT = 3;
        Art.HotKills = 0;
        Fire(TriggerEvent.Ability, new ProcCtx { X = p.X, Z = p.Z });
        return true;
    }

    /* ------------------------------------------------------ the callings -- */

    bool ShieldBash(AbilityDef def, double angle, double power)
    {
        var p = Player;
        bool wide = Has("wide_arc");
        Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Angle = angle, Radius = 3.4, Wide = wide });
        int struck = 0;
        ForEachHostileInRadius(p.X, p.Z, 3.4, (e, d) =>
        {
            double da = Wrap(Math.Atan2(e.Z - p.Z, e.X - p.X) - angle);
            if (!wide && Math.Abs(da) > 1.2) return;
            double dd = d == 0 ? 1 : d;
            HitEnemy(e, 22 * power * (wide ? 0.8 : 1), School.Physical, [Tag.Melee, Tag.Physical], new HitOpts { Knockback = 2.4, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd });
            ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, (e.Boss ? 0.6 : 1.5) + (Has("concussion") ? 1 : 0)), 0);
            Interrupt(e);
            struck++;
        });
        if (Has("shield_wall") && struck > 0) Barrier(MaxHp * Math.Min(0.4, 0.08 * struck), 5);
        if (Has("rebound")) p.AbilityCd = Math.Max(0.5, p.AbilityCd - 0.5 * struck);
        Events.Emit(new Ev.Shake { Amount = 0.35 });
        return true;
    }

    bool Bulwark(AbilityDef def, double angle)
    {
        var p = Player;
        p.BulwarkT = 3;
        Art.BulwarkUp = true;
        Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Angle = angle, Radius = 2 });
        return true;
    }

    bool Leap(AbilityDef def, double ax, double az, double angle)
    {
        var p = Player;
        double reach = Has("long_leap") ? 11 : 7;
        double dist = Math.Min(reach, Aim is { } a ? Dist(a.X, a.Z, p.X, p.Z) : reach);
        double x1 = p.X + ax * dist, z1 = p.Z + az * dist;
        p.Leap = new Leap { T = 0, Dur = 0.42, X0 = p.X, Z0 = p.Z, X1 = x1, Z1 = z1 };
        Events.Emit(new Ev.Ability { Id = def.Id, X = x1, Z = z1, Angle = angle, Radius = 3 });
        return true;
    }

    bool Warcry(AbilityDef def, double angle, double power)
    {
        var p = Player;
        Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Angle = angle, Radius = 8 });
        bool terror = Has("terror");
        ForEachHostileInRadius(p.X, p.Z, 8, (e, _) =>
        {
            if (!e.Elite && !e.Boss) ApplyStatus(e, new StatusPayload(StatusKind.Fear, 1, 1, 2.5), 0);
            else if (terror && !e.Boss) ApplyStatus(e, new StatusPayload(StatusKind.Fear, 1, 1, 1), 0);
            Interrupt(e);
        });
        double t = Has("echoing") ? 10 : 6;
        AddBuff("warcry", Stat.Damage, 0.25 * power, ModKind.Inc, t, 1);
        if (Has("bloodlust")) AddBuff("bloodlust", Stat.MoveSpeed, 0.2, ModKind.Inc, t, 1);
        if (Has("battle_trance")) HealPlayer(MaxHp * 0.15, "war cry");
        return true;
    }

    bool Blink(AbilityDef def, double ax, double az, double angle, double power)
    {
        var p = Player;
        double x0 = p.X, z0 = p.Z;
        double reach = Has("far_step") ? 9 : 6;
        StepTo(x0 + ax * reach, z0 + az * reach);
        p.Iframes = Math.Max(p.Iframes, 0.3);
        Events.Emit(new Ev.Ability { Id = def.Id, X = x0, Z = z0, X1 = p.X, Z1 = p.Z, Angle = angle, Radius = 3 });
        Events.Emit(new Ev.Dash { X0 = x0, Z0 = z0, X1 = p.X, Z1 = p.Z });
        int caught = FrostBurst(x0, z0, power);
        if (Has("arrival"))
        {
            caught += FrostBurst(p.X, p.Z, power);
            Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Angle = angle, Radius = 3 });
        }
        if (Has("quickening") && caught > 0) p.AbilityCd *= 0.6;
        return true;
    }

    int FrostBurst(double x, double z, double power)
    {
        int n = 0;
        bool freeze = Has("winters_wake");
        ForEachHostileInRadius(x, z, 3.2, (e, _) =>
        {
            HitEnemy(e, 14 * power, School.Frost, FrostTags, new HitOpts { Status = new StatusPayload(StatusKind.Chill, 1, 3, 3) });
            if (freeze) Freeze(e, 1.5);
            n++;
        });
        return n;
    }

    /// <summary>Held fast in ice (bosses shrug it off).</summary>
    void Freeze(Enemy e, double seconds)
    {
        if (!e.Alive || e.State == EnemyState.Dying || e.Boss) return;
        e.Status.Remove(StatusKind.Chill);
        e.Status[StatusKind.Frozen] = new StatusSlot(e.Elite ? seconds * 0.55 : seconds, 1, 0, 0);
        Events.Emit(new Ev.Status { Target = e.Id, Kind = StatusKind.Frozen, X = e.X, Z = e.Z });
    }

    bool TimeSlip(AbilityDef def, double angle, double power)
    {
        var p = Player;
        WorldRate = Has("deep_slip") ? 0.2 : 1.0 / 3;
        WorldRateT = (Has("long_slip") ? 5.5 : 3.5) * power;
        Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Angle = angle, Radius = 30 });
        foreach (var e in Enemies.Items) if (e.Alive) Interrupt(e);
        return true;
    }

    bool MarkPrey(AbilityDef def, double angle)
    {
        var p = Player;
        var marked = HostilesInRadius(p.X, p.Z, 16).Where(e => !e.Decoy).OrderByDescending(e => e.MaxHp).Take(Has("twin_marks") ? 2 : 1).ToList();
        if (marked.Count == 0) { p.AbilityCd = 0.5; return false; }
        foreach (var e in marked)
        {
            ApplyStatus(e, new StatusPayload(StatusKind.Mark, 1, 2, 8), 0);
            e.Prey = true;
            if (Has("blood_trail")) ApplyStatus(e, new StatusPayload(StatusKind.Bleed, 1, 0.6, 8), 30 * ArtPower);
            Events.Emit(new Ev.Ability { Id = def.Id, X = e.X, Z = e.Z, Angle = angle, Radius = 1 });
        }
        return true;
    }

    bool SmokeBomb(AbilityDef def, double angle, double power)
    {
        var p = Player;
        double hide = Has("thick_smoke") ? 5 : 3;
        p.InvisibleT = hide;
        p.SureCritT = hide + 0.5 + (Has("ambush") ? 2 : 0);
        if (Has("ambush")) AddBuff("ambush", Stat.CritDamage, 0.5, ModKind.More, p.SureCritT, 1);
        if (Has("mist_step")) AddBuff("mist_step", Stat.MoveSpeed, 0.3, ModKind.Inc, hide, 1);
        if (Has("choking"))
        {
            var zn = SpawnZone(Side.Player, p.X, p.Z, 3.5, 5, 6 * power, School.Nature);
            if (zn != null) { zn.Tags = [Tag.Nature, Tag.Zone, Tag.Area]; zn.Art = "venom_smoke"; zn.Status = new StatusPayload(StatusKind.Poison, 0.6, 0.5, 3); }
        }
        Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Angle = angle, Radius = 4 });
        foreach (var e in Enemies.Items) if (e.Alive && e.Target == -1) { e.Target = -2; e.RetargetT = hide; }
        return true;
    }

    /* ----------------------------------------------------- ways of moving -- */

    bool Sprint(AbilityDef def, double angle)
    {
        var p = Player;
        Art.SprintT = 4;
        AddBuff("sprint", Stat.MoveSpeed, 0.7, ModKind.Inc, Art.SprintT, 1);
        p.SlowT = 0; p.SlowF = 1;
        Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Angle = angle, Radius = 2 });
        return true;
    }

    bool MirrorStep(AbilityDef def, double ax, double az, double angle)
    {
        var p = Player;
        double x0 = p.X, z0 = p.Z;
        StepTo(x0 + ax * 5, z0 + az * 5);
        p.Iframes = Math.Max(p.Iframes, 0.25);
        int n = Has("three_mirrors") ? 3 : 2;
        // Side by side across the way you went, facing what you left.
        double sx = -az, sz = ax;
        for (int i = 0; i < n; i++)
        {
            double off = n == 2 ? (i == 0 ? -1.1 : 1.1) : (i - 1) * 1.3;
            double back = n == 3 && i == 1 ? -0.4 : 0;
            Reflect(x0 + sx * off - ax * back, z0 + sz * off - az * back, 5, Math.Atan2(-az, -ax));
        }
        Events.Emit(new Ev.Ability { Id = def.Id, X = x0, Z = z0, X1 = p.X, Z1 = p.Z, Angle = angle, Radius = 2 });
        Events.Emit(new Ev.Dash { X0 = x0, Z0 = z0, X1 = p.X, Z1 = p.Z });
        return true;
    }

    /// <summary>A reflection of the survivor that draws the horde, and breaks.</summary>
    Enemy? Reflect(double x, double z, double life, double facing)
    {
        if (Collision.Blocked(x, z, 0.4)) { x = Player.X; z = Player.Z; }
        var e = SpawnEnemy("mirror", x, z, new SpawnOpts { Disposition = Disposition.Ally, Faction = Faction.Ally });
        if (e == null) return null;
        e.MaxHp = e.Hp = MaxHp * 0.25;
        e.LifeT = life;
        e.Decoy = true;
        e.Facing = facing;
        Decoys.Add(e);
        // What was coming for you comes for them.
        ForEachHostileInRadius(x, z, 14, (h, _) => { if (h.Target == -1) { h.Target = e.Id; h.RetargetT = 1.5; } });
        return e;
    }

    /// <summary>A reflection gone: it bursts (an echo that was stepped into does not).</summary>
    void BreakDecoy(Enemy e)
    {
        Decoys.Remove(e);
        if (e == Art.Echo) { Art.Echo = null; if (Art.EchoT <= 0 || e.Tag == "recalled") return; }
        double power = ArtPower;
        Events.Emit(new Ev.Ability { Id = "mirror_break", X = e.X, Z = e.Z, Radius = 2.5 });
        bool cold = Has("cold_glass");
        ForEachHostileInRadius(e.X, e.Z, 2.5, (h, _) =>
            HitEnemy(h, 16 * power, School.Arcane, ArcaneTags, new HitOpts { Status = cold ? new StatusPayload(StatusKind.Chill, 1, 3, 3) : null, NoProcs = true }));
        if (Has("glass_heart")) HealPlayer(MaxHp * 0.04, "glass heart");
    }

    bool BullRush(AbilityDef def, double ax, double az, double angle)
    {
        var p = Player;
        Art.Barrier = MaxHp * (Has("iron_hide") ? 0.30 : 0.18);
        Barrier(Art.Barrier, 4);
        StartRush(AbilityKind.BullRush, ax, az, 9, 0.4);
        p.SlowT = 0; p.SlowF = 1;
        Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Angle = angle, Radius = 1.2 });
        return true;
    }

    void StartRush(AbilityKind kind, double dx, double dz, double dist, double time)
    {
        var p = Player;
        Art.Rush = kind;
        Art.RushDX = dx; Art.RushDZ = dz;
        Art.RushT = time;
        Art.RushSpeed = dist / time;
        Art.RushX0 = p.X; Art.RushZ0 = p.Z;
        p.Facing = Math.Atan2(dx, dz);
    }

    bool WraithWalk(AbilityDef def, double angle)
    {
        var p = Player;
        Art.WraithT = Has("long_night") ? 4 : 2.5;
        Art.Drains = 0;
        AddBuff("wraith", Stat.MoveSpeed, 0.25, ModKind.Inc, Art.WraithT, 1);
        Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Angle = angle, Radius = 2.4 });
        return true;
    }

    bool CinderTrail(AbilityDef def, double angle)
    {
        var p = Player;
        Art.CinderT = 4;
        Art.Trail.Clear();
        Art.CinderLastX = p.X; Art.CinderLastZ = p.Z;
        AddBuff("cinder", Stat.MoveSpeed, 0.35, ModKind.Inc, Art.CinderT, 1);
        DropCinder();
        Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Angle = angle, Radius = 2 });
        return true;
    }

    void DropCinder()
    {
        var p = Player;
        bool wild = Has("wildfire");
        var zn = SpawnZone(Side.Player, p.X, p.Z, wild ? 1.5 : 1.1, wild ? 4.5 : 3, 9 * ArtPower, School.Fire);
        if (zn == null) return;
        zn.Tags = FireTags;
        zn.Art = "cinder";
        zn.Tick = 0.4;
        zn.Status = new StatusPayload(StatusKind.Burn, 0.25, 0.4, 2);
        if (Has("hobbling")) zn.Slow = 0.35;
        Art.Trail.Add(zn.Id);
        Art.CinderLastX = p.X; Art.CinderLastZ = p.Z;
    }

    bool Grapple(AbilityDef def, double ax, double az, double angle)
    {
        var p = Player;
        const double reach = 12;
        // The first thing along the line the chain can bite.
        Enemy? hook = null;
        double best = reach;
        foreach (var e in HostilesInRadius(p.X, p.Z, reach))
        {
            double rx = e.X - p.X, rz = e.Z - p.Z;
            double along = rx * ax + rz * az;
            if (along <= 0 || along > best) continue;
            double side = Math.Abs(rx * az - rz * ax);
            if (side > 0.9 + e.Radius) continue;
            best = along; hook = e;
        }
        if (hook != null)
        {
            Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, X1 = hook.X, Z1 = hook.Z, Angle = angle, Radius = best });
            Art.Hooked = hook;
            Art.HookedAt = Time;
            if (Has("reel") && !hook.Elite && !hook.Boss && hook.Mass < 3)
            {
                // Dragged in and held.
                double d = Dist(hook.X, hook.Z, p.X, p.Z);
                double pull = Math.Max(0, d - (p.Radius + hook.Radius + 0.4)) * 9;
                hook.Kbx = -(hook.X - p.X) / d * pull;
                hook.Kbz = -(hook.Z - p.Z) / d * pull;
                HitEnemy(hook, 12 * ArtPower, School.Physical, RushTags, new HitOpts { NoProcs = true });
                ApplyStatus(hook, new StatusPayload(StatusKind.Stun, 1, 1, 1.8), 0);
                Interrupt(hook);
                return true;
            }
            double gap = Math.Max(0, best - (p.Radius + hook.Radius + 0.3));
            StartRush(AbilityKind.Grapple, ax, az, gap, Math.Max(0.08, gap / 28));
            return true;
        }
        // Or the first tree, rock or wall: haul yourself to it.
        for (double s = 1; s <= reach; s += 0.5)
        {
            if (!Collision.Blocked(p.X + ax * s, p.Z + az * s, 0.2)) continue;
            double gap = Math.Max(0, s - p.Radius - 0.4);
            if (gap < 1.5) break;
            Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, X1 = p.X + ax * s, Z1 = p.Z + az * s, Angle = angle, Radius = s });
            Art.Hooked = null;
            StartRush(AbilityKind.Grapple, ax, az, gap, gap / 28);
            return true;
        }
        // Nothing to bite: the chain falls short, and is quickly back.
        Events.Emit(new Ev.Ability { Id = "grapple_miss", X = p.X, Z = p.Z, X1 = p.X + ax * reach, Z1 = p.Z + az * reach, Angle = angle, Radius = reach });
        p.AbilityCd = 1;
        return true;
    }

    bool EchoStep(AbilityDef def, double angle)
    {
        var p = Player;
        Art.EchoT = Has("long_echo") ? 7 : 4;
        Art.EchoX = p.X; Art.EchoZ = p.Z; Art.EchoHp = p.Hp; Art.EchoFacing = p.Facing;
        Art.Echo = Has("decoy_echo") ? Reflect(p.X, p.Z, Art.EchoT, Math.PI / 2 - p.Facing) : null;
        Events.Emit(new Ev.Ability { Id = def.Id, X = p.X, Z = p.Z, Angle = angle, Radius = 1.5 });
        return true;
    }

    /// <summary>Step back into the echo: where you were, and some of what you had.</summary>
    void Recall()
    {
        var p = Player;
        double x0 = p.X, z0 = p.Z;
        double lost = Art.EchoHp - p.Hp;
        Art.EchoT = 0;
        if (Art.Echo is { Alive: true } echo)
        {
            echo.Tag = "recalled";
            KillEnemy(echo, false, null);
        }
        Art.Echo = null;
        p.X = Art.EchoX; p.Z = Art.EchoZ;
        Collision.Resolve(ref p.X, ref p.Z, p.Radius, true);
        p.Iframes = Math.Max(p.Iframes, 0.3);
        Events.Emit(new Ev.Ability { Id = "echo_recall", X = p.X, Z = p.Z, X1 = x0, Z1 = z0, Radius = 3 });
        Events.Emit(new Ev.Dash { X0 = x0, Z0 = z0, X1 = p.X, Z1 = p.Z });
        if (lost > 0) HealPlayer(lost * (Has("full_echo") ? 1 : 0.5), "echo");
        if (Has("resonance"))
        {
            double power = ArtPower;
            foreach (var (x, z) in new[] { (x0, z0), (p.X, p.Z) })
            {
                Events.Emit(new Ev.Explosion { X = x, Z = z, Radius = 3, School = School.Arcane, Power = 1 });
                ForEachHostileInRadius(x, z, 3, (e, _) => HitEnemy(e, 18 * power, School.Arcane, ArcaneTags));
            }
        }
    }

    bool Vault(AbilityDef def, double mx, double mz, double ax, double az, double angle, double power)
    {
        var p = Player;
        // Back, away from where you aim; with no pointer, the way you are pushing.
        double vx = -ax, vz = -az;
        if (Aim == null && Len(mx, mz) > 0.1) { double l = Len(mx, mz); vx = mx / l; vz = mz / l; }
        double x0 = p.X, z0 = p.Z;
        double dist = 0;
        for (int k = 1; k <= 12; k++) if (!Collision.Blocked(x0 + vx * 0.5 * k, z0 + vz * 0.5 * k, p.Radius)) dist = 0.5 * k; else break;
        p.Leap = new Leap { T = 0, Dur = 0.32, X0 = x0, Z0 = z0, X1 = x0 + vx * dist, Z1 = z0 + vz * dist, Kind = AbilityKind.Vault };
        if (Has("nimble")) p.AbilityCd *= 0.67;
        var zn = SpawnZone(Side.Player, x0, z0, 2.4, 4, 5 * power, School.Physical);
        if (zn != null)
        {
            zn.Tags = SnareTags; zn.Art = Has("snare_line") ? "snare_hold" : "snare"; zn.Slow = 0.5;
            zn.Status = new StatusPayload(StatusKind.Bleed, 0.5, 0.6, 3);
        }
        Art.Struck.Clear();
        if (Has("volley"))
        {
            double back = Math.Atan2(-vz, -vx);
            for (int i = 0; i < 5; i++)
            {
                double a = back + (i - 2) * 0.16;
                var pr = SpawnProjectile(Side.Player, p.X, p.Z, 10 * power, School.Physical);
                if (pr == null) continue;
                pr.Vx = Math.Cos(a) * 26; pr.Vz = Math.Sin(a) * 26; pr.Speed = 26;
                pr.Life = 0.6; pr.Art = "dagger"; pr.Tags = KnifeTags; pr.Radius = 0.3;
            }
        }
        Events.Emit(new Ev.Ability { Id = def.Id, X = x0, Z = z0, X1 = p.Leap.X1, Z1 = p.Leap.Z1, Angle = angle, Radius = 2.4 });
        return true;
    }

    /* --------------------------------------------------------- landings -- */

    void LandLeap(Leap leap)
    {
        var p = Player;
        if (leap.Kind == AbilityKind.Vault)
        {
            if (Has("light_feet"))
            {
                p.DashCharges = Math.Min(RoundInt(Stats.Get(Stat.DashCharges)), p.DashCharges + 1);
                AddBuff("light_feet", Stat.MoveSpeed, 0.4, ModKind.Inc, 2, 1);
            }
            return;
        }
        double power = ArtPower;
        Events.Emit(new Ev.Explosion { X = p.X, Z = p.Z, Radius = 3, School = School.Physical, Power = 1 });
        Events.Emit(new Ev.Shake { Amount = 0.5 });
        bool quake = Has("quake");
        ForEachHostileInRadius(p.X, p.Z, 3, (e, d) =>
        {
            double dd = d == 0 ? 1 : d;
            HitEnemy(e, 34 * power, School.Physical, SlamTags, new HitOpts { Knockback = 2, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd });
            if (quake) ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, e.Boss ? 0.3 : 1), 0);
            Interrupt(e);
        });
        if (Has("aftershock")) strikes.Add(new StrikeSpec(p.X, p.Z, 4.5, 20 * power, School.Physical, SlamTags, 0.5, null, Side.Player, 1));
        if (Has("wind_at_back"))
        {
            p.DashCharges = Math.Min(RoundInt(Stats.Get(Stat.DashCharges)), p.DashCharges + 1);
            AddBuff("wind_at_back", Stat.MoveSpeed, 0.3, ModKind.Inc, 3, 1);
        }
    }

    /* ------------------------------------------------------------- tick -- */

    /// <summary>The art while it runs. True while it carries the survivor
    /// (a charge, a haul): the walk does not happen.</summary>
    bool TickArt(double dt)
    {
        var p = Player;
        var a = Art;
        a.HotT = Math.Max(0, a.HotT - dt);

        // Bulwark: mending behind it, a burst when it drops.
        if (p.BulwarkT > 0 && Has("rallying")) HealPlayer(MaxHp * 0.04 * dt, "rallying", true);
        if (a.BulwarkUp && p.BulwarkT <= 0)
        {
            a.BulwarkUp = false;
            if (Has("retribution"))
            {
                double power = ArtPower;
                Events.Emit(new Ev.Explosion { X = p.X, Z = p.Z, Radius = 5, School = School.Holy, Power = 1.2 });
                ForEachHostileInRadius(p.X, p.Z, 5, (e, _) => HitEnemy(e, 30 * power, School.Holy, HolyTags));
            }
        }
        if (WorldRateT > 0 && Ability == AbilityKind.TimeSlip && Has("stolen_moments")) HealPlayer(MaxHp * 0.03 * dt, "stolen moments", true);

        if (a.SprintT > 0)
        {
            a.SprintT -= dt;
            p.SlowF = 1;
            if (Has("second_wind")) HealPlayer(MaxHp * 0.03 * dt, "second wind", true);
            if (Has("trample")) Trample(p.Vx, p.Vz, 12, 1.8);
        }

        if (a.WraithT > 0)
        {
            a.WraithT -= dt;
            double power = ArtPower;
            ForEachHostileInRadius(p.X, p.Z, p.Radius + 0.35, (e, _) =>
            {
                if (!a.Struck.Add(e.Id)) return;
                e.DrainedAt = Time;
                HitEnemy(e, 12 * power, School.Shadow, ShadowTags, new HitOpts { NoProcs = true });
                // A crowd feeds a wraith, but only so far: ten drains mend, the rest only hurt.
                if (a.Drains++ < 10) HealPlayer(MaxHp * (Has("hunger") ? 0.035 : 0.02), "wraith walk", true);
                if (Has("grave_chill") && !e.Elite && !e.Boss) ApplyStatus(e, new StatusPayload(StatusKind.Fear, 1, 1, 1.5), 0);
                Events.Emit(new Ev.Ability { Id = "drain", X = e.X, Z = e.Z, X1 = p.X, Z1 = p.Z, Radius = 0.6 });
            });
        }

        if (a.CinderT > 0)
        {
            a.CinderT -= dt;
            if (Dist(p.X, p.Z, a.CinderLastX, a.CinderLastZ) > 0.9) DropCinder();
            if (a.CinderT <= 0 && Has("backdraft"))
            {
                // The whole trail goes up, from where you started to where you stand.
                double power = ArtPower;
                int k = 0;
                foreach (var id in a.Trail)
                {
                    var z = Zones.Items[id];
                    if (!z.Alive || z.Art != "cinder") continue;
                    strikes.Add(new StrikeSpec(z.X, z.Z, z.Radius + 0.6, 14 * power, School.Fire, [Tag.Fire, Tag.Explosion, Tag.Area], 0.04 * k++, null, Side.Player, 1));
                    z.Life = Math.Min(z.Life, z.Age + 0.04 * k);
                }
                a.Trail.Clear();
            }
        }

        if (a.EchoT > 0) a.EchoT -= dt;

        // Reflections that fight back.
        if (Decoys.Count > 0 && Has("fighting_reflections"))
        {
            a.ImageStrikeT -= dt;
            if (a.ImageStrikeT <= 0)
            {
                a.ImageStrikeT = 0.7;
                double power = ArtPower;
                foreach (var d in Decoys.ToArray())
                {
                    if (!d.Alive || d.State == EnemyState.Dying) continue;
                    var t = NearestHostile(d.X, d.Z, 2);
                    if (t == null) continue;
                    d.Facing = Math.Atan2(t.Z - d.Z, t.X - d.X);
                    Events.Emit(new Ev.Ability { Id = "mirror_strike", X = d.X, Z = d.Z, X1 = t.X, Z1 = t.Z, Angle = d.Facing, Radius = 1.9, Who = d.Id });
                    ForEachHostileInRadius(d.X, d.Z, 1.9, (e, _) => HitEnemy(e, 8 * power, School.Physical, RushTags, new HitOpts { NoProcs = true }));
                }
            }
        }

        return a.Rush != null && TickRush(dt);
    }

    /// <summary>Things run through are struck once and thrown aside.</summary>
    void Trample(double vx, double vz, double dmg, double knock)
    {
        var p = Player;
        double sp = Len(vx, vz);
        if (sp < 0.5) return;
        double dx = vx / sp, dz = vz / sp;
        double power = ArtPower;
        ForEachHostileInRadius(p.X, p.Z, p.Radius + 0.5, (e, _) =>
        {
            if (!Art.Struck.Add(e.Id)) return;
            // Aside: away from the line you are running.
            double side = (e.X - p.X) * dz - (e.Z - p.Z) * dx;
            double sx = side >= 0 ? dz : -dz, sz = side >= 0 ? -dx : dx;
            HitEnemy(e, dmg * power, School.Physical, RushTags, new HitOpts { Knockback = knock, DirX = sx * 0.8 + dx * 0.4, DirZ = sz * 0.8 + dz * 0.4 });
        });
    }

    bool TickRush(double dt)
    {
        var p = Player;
        var a = Art;
        double step = Math.Min(dt, a.RushT);
        double ex = p.X + a.RushDX * a.RushSpeed * step, ez = p.Z + a.RushDZ * a.RushSpeed * step;
        double bx = ex, bz = ez;
        Collision.Resolve(ref bx, ref bz, p.Radius, true);
        bool walled = Dist(bx, bz, ex, ez) > 0.05;
        p.X = bx; p.Z = bz;
        p.Moving = true;
        p.Vx = a.RushDX * a.RushSpeed * 0.35; p.Vz = a.RushDZ * a.RushSpeed * 0.35;
        a.RushT -= dt;
        bool done = a.RushT <= 0 || walled;
        if (a.Rush == AbilityKind.BullRush)
        {
            p.SlowF = 1;
            double power = ArtPower;
            bool gore = Has("gore"), unbroken = Has("unbroken");
            Enemy? stopper = null;
            ForEachHostileInRadius(p.X, p.Z, p.Radius + 0.6, (e, _) =>
            {
                if (stopper != null || !a.Struck.Add(e.Id)) return;
                var bleed = gore ? new StatusPayload(StatusKind.Bleed, 1, 0.8, 4) : null;
                if (e.Elite || e.Boss)
                {
                    stopper = e;
                    HitEnemy(e, 18 * power * (gore ? 1.5 : 1), School.Physical, RushTags, new HitOpts { Status = bleed });
                    ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, e.Boss ? 0.4 : 1.2), 0);
                    Interrupt(e);
                    return;
                }
                double side = (e.X - p.X) * a.RushDZ - (e.Z - p.Z) * a.RushDX;
                double sx = side >= 0 ? a.RushDZ : -a.RushDZ, sz = side >= 0 ? -a.RushDX : a.RushDX;
                HitEnemy(e, 18 * power, School.Physical, RushTags, new HitOpts { Knockback = 2.2, DirX = sx * 0.85 + a.RushDX * 0.5, DirZ = sz * 0.85 + a.RushDZ * 0.5, Status = bleed });
                if (unbroken && p.Shield < a.Barrier + MaxHp * 0.2) { p.Shield += MaxHp * 0.02; p.ShieldT = Math.Max(p.ShieldT, 3); }
            });
            if (stopper != null) { done = true; Events.Emit(new Ev.Shake { Amount = 0.4 }); }
            if (done)
            {
                a.Rush = null;
                if (Has("pile_driver"))
                {
                    Events.Emit(new Ev.Explosion { X = p.X, Z = p.Z, Radius = 3, School = School.Physical, Power = 1.1 });
                    Events.Emit(new Ev.Shake { Amount = 0.5 });
                    ForEachHostileInRadius(p.X, p.Z, 3, (e, d) =>
                    {
                        double dd = d == 0 ? 1 : d;
                        HitEnemy(e, 28 * power, School.Physical, SlamTags, new HitOpts { Knockback = 1.4, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd });
                        ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 1, e.Boss ? 0.3 : 1), 0);
                    });
                }
            }
            return true;
        }
        // A haul on the chain: untouchable on the way, a blow on arrival.
        p.Iframes = Math.Max(p.Iframes, 0.08);
        if (done)
        {
            a.Rush = null;
            if (a.Hooked is { Alive: true } h && h.State != EnemyState.Dying)
            {
                double power = ArtPower;
                Events.Emit(new Ev.Shake { Amount = 0.3 });
                HitEnemy(h, 20 * power, School.Physical, RushTags, new HitOpts { Knockback = 0.8, DirX = a.RushDX, DirZ = a.RushDZ });
                ApplyStatus(h, new StatusPayload(StatusKind.Stun, 1, 1, h.Boss ? 0.3 : 0.8), 0);
                Interrupt(h);
                if (Has("whirling_chain"))
                {
                    Events.Emit(new Ev.Ability { Id = "chain_whirl", X = p.X, Z = p.Z, Radius = 3 });
                    ForEachHostileInRadius(p.X, p.Z, 3, (e, d) =>
                    {
                        double dd = d == 0 ? 1 : d;
                        HitEnemy(e, 14 * power, School.Physical, SlamTags, new HitOpts { Knockback = 1.2, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd });
                    });
                }
            }
            if (Has("anchor")) Barrier(MaxHp * 0.12, 4);
        }
        return true;
    }

    /// <summary>A barrier over the survivor's health, for a while.</summary>
    public void Barrier(double amount, double seconds)
    {
        var p = Player;
        p.Shield = Math.Min(MaxHp, Math.Max(p.Shield, 0) + amount);
        p.ShieldT = Math.Max(p.ShieldT, seconds);
    }

    /// <summary>Step along a line as far as the ground is open.</summary>
    void StepTo(double tx, double tz)
    {
        var p = Player;
        double x0 = p.X, z0 = p.Z;
        int best = 0;
        for (int k = 1; k <= 12; k++)
        {
            double x = x0 + (tx - x0) * (k / 12.0), z = z0 + (tz - z0) * (k / 12.0);
            if (!Collision.Blocked(x, z, p.Radius)) best = k;
        }
        p.X = x0 + (tx - x0) * (best / 12.0);
        p.Z = z0 + (tz - z0) * (best / 12.0);
    }

    /* ------------------------------------------------ what the art sees -- */

    /// <summary>A kill: the art grows if it is fresh, and some arts answer it.</summary>
    void ArtOnKill(Enemy e, bool credited)
    {
        var p = Player;
        if (e.Decoy) { BreakDecoy(e); return; }
        if (!credited || e.Disposition == Disposition.Ally) return;
        if (Art.HotT > 0 && Art.HotKills < 15) { Art.HotKills++; ArtXp += 0.2; }
        if (e.Prey)
        {
            e.Prey = false;
            if (Ability == AbilityKind.MarkPrey)
            {
                bool quarry = Has("quarry");
                p.AbilityCd *= quarry ? 0 : 0.5;
                if (quarry) HealPlayer(MaxHp * 0.1, "quarry");
            }
        }
        if (Art.SprintT > 0 && Has("long_road") && Art.SprintT < 8)
        {
            Art.SprintT += 0.5;
            if (Buffs.TryGetValue("sprint", out var b)) b.T = Art.SprintT;
        }
        if (Has("soul_tithe") && Time - e.DrainedAt < 3) HealPlayer(MaxHp * 0.05, "soul tithe");
        if (Art.Hooked == e && Has("second_hook") && Time - Art.HookedAt < 3) { p.AbilityCd *= 0.5; Art.Hooked = null; }
    }

    /// <summary>A marked prey below the line dies outright (not a boss).</summary>
    void ArtOnHit(Enemy e)
    {
        if (!e.Prey || e.Boss || e.Hp <= 0 || !e.Status.Has(StatusKind.Mark)) return;
        if (e.Hp < e.MaxHp * (Has("executioner") ? 0.3 : 0.2))
        {
            Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = "Executed" });
            KillEnemy(e, true, null);
        }
    }

    /// <summary>How fast dashes come back while the art runs.</summary>
    double DashHaste()
    {
        double h = 1;
        if (Art.SprintT > 0 && Has("tailwind")) h *= 2;
        if (WorldRateT > 0 && Ability == AbilityKind.TimeSlip && Has("borrowed_time")) h *= 3;
        return h;
    }
}
