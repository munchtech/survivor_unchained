using System;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* The warden quarter's phase-1 rules (docs/design/CLASSES.md section 2): the shield's block, the
 * stones it lays, the rebuke at ten, and the crossings' small rules (Bound, Marked, burning ground).
 * The old Warding light (Stat.Block rank) is untouched; the lamps' block is a chance on top of it. */
public sealed partial class Battle
{
    /// <summary>The last blow was turned by a lamp's block (the missile's site reads it for turned_arrows).</summary>
    bool lampBlocked;
    /// <summary>Stones laid by blocks, the lull since the last, and what the Bearer has stored.</summary>
    int stones;
    double stoneLull, stoneDrop, bearerStore;
    bool leaping;

    public int Stones => stones;
    /// <summary>Counters for measurement: blocks (any), rebukes, the most stones held at once.</summary>
    public int Blocks, Rebukes, StonesPeak;

    /// <summary>The chance a lamp-lit shield turns this blow (0 when none is lit).</summary>
    double LampBlockChance(Enemy? from)
    {
        var l = Lamps;
        double c = l.Full("shield_arm", "block");
        if (Player.StillT > 0.25) c += l.Size("block.still", "add");
        if (from != null && (from.Boss || from.Elite)) c += l.Size("block.champions", "add");
        if (c <= 0) return 0;
        if (l.Has("wall_holds"))
        {
            if (Player.Moving) return 0;
            return Math.Min(l.Full("wall_holds", "cap", 0.75), c * 2);
        }
        return Math.Min(0.75, c);
    }

    /// <summary>A lamp's block, rolled after dodge. True when the blow is turned (and everything it brings is done).</summary>
    bool TryLampBlock(double amount, School school, string source, Enemy? from)
    {
        lampBlocked = false;
        double chance = LampBlockChance(from);
        if (chance <= 0 || Rng.Next() >= chance) return false;
        var p = Player;
        lampBlocked = true;
        p.Iframes = Math.Max(p.Iframes, 0.25);
        FlareOnBlock(from);
        Events.Emit(new Ev.PlayerHit { X = p.X, Z = p.Z, Amount = 0, School = school, Source = source, Blocked = true });
        Fire(TriggerEvent.Block, new ProcCtx { X = p.X, Z = p.Z });
        OnBlocked(amount, from);
        return true;
    }

    /// <summary>Everything a block brings, lamp's or Warding light's: a stone, and what the lamps hang on it.</summary>
    void OnBlocked(double amount, Enemy? from)
    {
        var p = Player;
        Blocks++;
        var l = Lamps;
        // bulwark.block.mend: each block mends a sliver while above half.
        if (l.Has("block.mend") && p.Hp > MaxHp * l.Full("block.mend", "above", 0.5)) HealPlayer(MaxHp * l.Size("block.mend", "share") * BearerMend(), "block");
        // bulwark.mortar: each block gives a barrier.
        if (l.Has("mortar")) Barrier(MaxHp * l.Size("mortar", "barrier"), 8);
        // bulwark.bearer_of_blows: what is blocked is stored for the rebuke.
        if (l.Has("bearer_of_blows")) bearerStore += amount;
        // bulwark.heavy_shield: a champion's blow turned stuns it.
        if (l.Has("heavy_shield") && from is { Alive: true, Elite: true, Boss: false })
            ApplyStatus(from, new StatusPayload(StatusKind.Stun, 1, 1, l.Full("heavy_shield", "seconds", 0.5)), 0);
        // duelists_road.return_cut / block.opening: an Opening, the blows strike true.
        double opening = l.Full("return_cut", "seconds") + l.Full("block.opening", "seconds");
        if (opening > 0) p.SureCritT = Math.Max(p.SureCritT, opening);
        // bulwark.oathblade.shield_and_edge: Oathblade swings at once.
        if (l.Has("oathblade.shield_and_edge") && WeaponById("oathblade") is { } edge) edge.Timer = 0;
        AddStone();
    }

    /// <summary>bulwark.shield_arm: a blow the shield didn't turn still lands on the wall and lays a stone ("let them
    /// hit you, and they break on it"). From blocks alone a rebuke came once in three minutes, under 1% of the night's
    /// damage; from every blow, at six stones and 8 m, every 22 s at tier 1 to 12 s at tier 4 and 3.6-7.9% (the owner,
    /// 11 October: "a little more").</summary>
    void LampsOnBlowLanded()
    {
        if (Lamps.Full("shield_arm", "struck") > 0) AddStone();
    }

    double BearerMend() => Lamps.Has("bearer_of_blows") ? 1 - Lamps.Full("bearer_of_blows", "less", 0.3) : 1;

    /// <summary>A stone laid (a blow taken or blocked, or a parry; or the warden's Hand, `hand`); at six the wall answers.</summary>
    void AddStone(bool hand = false)
    {
        if (!hand && !Lamps.Has("shield_arm") && !Lamps.Has("parry") && !Lamps.Has("mortar")) return;
        stoneLull = 0;
        // Unlit Shield Arm, the warden's Hand's wall answers on its own numbers (and a Parry's stones join it); with no Hand, none does.
        int cap = (int)WallArg("stones", 6, Content.Hands.Warden.Stones);
        // Parry without Shield Arm lays stones the wall can't answer (no cap, no reach).
        if (cap <= 0) return;
        stoneDrop = 0;
        if (++stones >= cap) { stones = 0; Rebuke(); }
        else StonesPeak = Math.Max(StonesPeak, stones);
    }

    /// <summary>bulwark.shield_arm: the rebuke of holy light all around, at six stones.</summary>
    void Rebuke()
    {
        var p = Player;
        var l = Lamps;
        double r = WallArg("radius", 8, Content.Hands.Warden.Radius) * Math.Sqrt(Stats.Get(Stat.Area));
        double dmg = RebukePower() + bearerStore;
        Rebukes++;
        bearerStore = 0;
        Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = r, School = School.Holy, Duration = 0.3, Rings = 1 });
        ForEachHostileInRadius(p.X, p.Z, r, (e, d) =>
        {
            double dd = d == 0 ? 1 : d;
            double m = e.Elite || e.Boss ? 1 + l.Size("rebuke.champions", "more") : 1;
            // A boss takes a share: the wall breaks the crowd; against a lord of the night it mustn't rival the Flare.
            if (e.Boss) m *= WallArg("boss", 1, Content.Hands.Warden.Boss);
            HitEnemy(e, dmg * m, School.Holy, [Tag.Holy, Tag.Area, Tag.Shield], new HitOpts { Knockback = 1.2, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, NoProcs = true, Credit = "rebuke" });
        });
    }

    /// <summary>The rebuke's blow before the build's damage: as hard as the wall is thick (a share of max health), grown by
    /// the level as the Flare's power is (8% a level; the ember's level by night, the survivor's by day). CLASSES.md 2.8.</summary>
    public double RebukePower()
    {
        int level = EmberOn ? EmberLevel : Level;
        return MaxHp * WallArg("rebuke", 10, Content.Hands.Warden.Rebuke) * (1 + WallArg("per_level", 0.08, Content.Hands.Warden.PerLevel) * Math.Max(0, level - 1));
    }

    /// <summary>The lull is in the fight: no blow taken or blocked and no hostile within 3 m for `lull` seconds, then stones
    /// fall one a second; the mortar holds them.</summary>
    void TickStones(double dt)
    {
        if (stones == 0) return;
        if (Lamps.Has("mortar")) return;
        double lull = WallArg("lull", 6, Content.Hands.Warden.Lull);
        bool near = false;
        ForEachHostileInRadius(Player.X, Player.Z, 3, (e, d) => near = true);
        if (near) stoneLull = 0; else stoneLull += dt;
        if (stoneLull <= lull) return;
        stoneDrop += dt;
        while (stoneDrop >= 1 && stones > 0) { stoneDrop -= 1; stones--; }
        if (stones == 0) stoneDrop = 0;
    }

    /// <summary>Barrier made stronger while five stones or more are held (bulwark.stones.barrier).</summary>
    double StonesBarrier(double amount) =>
        Lamps.Has("stones.barrier") && stones >= (int)Lamps.Full("stones.barrier", "at", 3) ? amount * (1 + Lamps.Size("stones.barrier", "more")) : amount;

    /// <summary>A perfect dash's lamps: a barrier (perfect.barrier) and a stone (parry).</summary>
    void LampsOnPerfect()
    {
        if (Lamps.Has("perfect.barrier")) Barrier(MaxHp * Lamps.Size("perfect.barrier", "share"), 5);
        if (Lamps.Has("parry")) AddStone();
    }

    /// <summary>Player burning ground lies here (firebreak: fire_arrows, traps.burning_longer).</summary>
    bool OnBurningGround(double x, double z)
    {
        foreach (var g in Zones.Items)
            if (g.Alive && g.Owner == Side.Player && g.School == School.Fire && Dist(g.X, g.Z, x, z) < g.Radius) return true;
        return false;
    }

    /// <summary>The damage rules that read the target: the lamps' "harder at" sums.</summary>
    double LampDamageMul(Enemy e, School school, Tag[] tags, HitOpts o)
    {
        var l = Lamps;
        double m = 1;
        var s = e.Status;
        // shambles.tags.vs_bleeding_champions
        if (e.Elite && !e.Boss && s.Has(StatusKind.Bleed)) m += l.SizeOn("tags.vs_bleeding_champions", "more", o.Weapon?.Id ?? "", tags);
        // night_road.bound_marked.more: storm and arcane strike Bound marked things harder.
        if ((tags.Has(Tag.Storm) || school == School.Arcane) && s.Has(StatusKind.Bound) && s.Has(StatusKind.Mark)) m += l.Size("bound_marked.more", "more");
        // firebreak.projectiles.vs_burning
        if ((o.Projectile || tags.Has(Tag.Projectile)) && s.Has(StatusKind.Burn)) m += l.Size("projectiles.vs_burning", "more");
        // bulwark.faith_in_the_wall: holy hits harder while the barrier stands above a fifth.
        if (school == School.Holy && l.Has("faith_in_the_wall") && Player.Shield > MaxHp * l.Full("faith_in_the_wall", "at", 0.2)) m += l.Size("faith_in_the_wall", "inc");
        return m;
    }

    /// <summary>night_road.lightning_leaps_the_chain: a storm that strikes a Bound thing runs to everything Bound.</summary>
    void LightningLeaps(Enemy from, double baseDamage, School school, Tag[] tags, HitOpts o)
    {
        if (leaping || o.Dot || !tags.Has(Tag.Storm) || !Lamp("lightning_leaps") || !from.Status.Has(StatusKind.Bound)) return;
        leaping = true;
        var o2 = o; o2.NoProcs = true;
        foreach (var e in Enemies.Items)
            if (e.Alive && e != from && e.Status.Has(StatusKind.Bound)) HitEnemy(e, baseDamage, school, tags, o2);
        leaping = false;
    }

    /// <summary>night_road.moon_on_the_chain: a marked Bound thing marks everything Bound.</summary>
    void MoonOnTheChain(Enemy src)
    {
        if (!Lamp("moon_on_the_chain") || !src.Status.Has(StatusKind.Mark) || !src.Status.Has(StatusKind.Bound)) return;
        var m = src.Status[StatusKind.Mark]!;
        foreach (var e in Enemies.Items)
            if (e.Alive && e != src && e.Status.Has(StatusKind.Bound) && !e.Status.Has(StatusKind.Mark))
                e.Status[StatusKind.Mark] = new StatusSlot(m.T, 1, m.Power, 0.5);
    }
}
