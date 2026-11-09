using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/// <summary>Mods from discoveries and items: multipliers and additions.</summary>
public sealed class WeaponMods
{
    public double Damage = 1, Area = 1, Cooldown = 1, Speed = 1, Duration = 1, Homing;
    public int Projectiles, Pierce;
}

/// <summary>
/// A weapon in the hand: its definition, how far it has been ranked, what it
/// evolved into, and the behaviour that turns all of that into things on the
/// field. Nothing here aims or fires on input - the survivor's whole job is
/// where they stand.
/// </summary>
public sealed class WeaponInst
{
    public readonly string Id;
    public readonly WeaponDef Def;
    public int Rank;
    Evolution? evolution;
    public double Timer;
    /// <summary>(M3) The timer is only a kindled skill's look-again (its condition did not hold, or nothing was in range),
    /// not a wait: her key may still heave it (Battle.KindledPress, the press plan).</summary>
    public bool Relooking;
    public readonly WeaponMods Mods = new();
    /// <summary>Burst shots still to go, and when.</summary>
    public int BurstLeft;
    /// <summary>The strength (CastMul) of the cast whose burst is still firing.</summary>
    public double BurstMul = 1;
    public double BurstT;
    public int BurstTarget = -2;
    /// <summary>Statistics for the damage meter and for mastery.</summary>
    public double DamageDealt;
    public int Kills;
    /// <summary>The skill slot it sits in (key Slot+1), and a union's second (its other part's; -1 for one slot).
    /// Slots are stable: a weapon keeps its key while it is carried (Battle.AddWeapon takes the lowest free).</summary>
    public int Slot, Slot2 = -1;
    /// <summary>A channel (CastMode.Channel) is running, and for how long so far; the next firing in it.</summary>
    public bool Channeling;
    public double ChannelT, ChannelNext;
    /// <summary>Its key is held (Battle.HoldSkill, each sim step): a channel keeps on while it is.</summary>
    public bool Held;
    /// <summary>A spin (Bladestorm): its ticks this storm, the Sunder lines it has thrown and holds pending (split by its
    /// break, else faded), and the time it may still be broken after the spin ended (-1: not).</summary>
    public int SpinTicks;
    public readonly List<SpinLineRec> Lines = new();
    public double BreakUntil = -1;
    /// <summary>A spin's storm: when the last began (the battle's clock), and the seconds the last one ran (the break grows
    /// with it). A spin union's second key held (Held2), and its other part (Sunder, at the union's rank, on its own cooldown,
    /// never in Weapons): what that key swings outside a storm (Battle.PressSkill, Firing.TickPressed).</summary>
    public double StormAt = double.NegativeInfinity, StormT;
    public bool Held2;
    public WeaponInst? Half;
    /// <summary>For beams and orbits: active until.</summary>
    public double ActiveT;
    /// <summary>Times it has been honed (finished, in the endless dark).</summary>
    public int Honed;
    /// <summary>Taken from the hand for a while (the Red Hand's toll): it does not fire.</summary>
    public double DisabledT;
    public int Swing;
    /// <summary>The strength of the cast now in hand (the Ledger, the Crowded Sky, the Echo): a multiplier on its projectiles.</summary>
    public double CastMul = 1;
    /// <summary>Firings so far, and the Melee or Thrown ones the warden's Hand counts toward its heavy blow (Sim/Hands.cs).</summary>
    public int Casts, HandBlows;
    /// <summary>Lamps v2 (Sim/BoardRules.cs): a heavy rite's own count of firings, and the firing a bind rite last bound in.</summary>
    public int RiteBlows, RiteBound = -1;
    /// <summary>The last firing was heavy: its burst shots still to come are too.</summary>
    public bool HeavyCast;
    /// <summary>Its own heavy count (WeaponStats.HeavyEvery: Sunder's every 4th swing): firings so far, and whether the
    /// firing now is its own heavy one (only within a cast: a Pulse's follow-up or an echo never is).</summary>
    public int OwnBlows;
    public bool OwnHeavy;
    /// <summary>A Pulse Turn's follow-ups still to go, and when.</summary>
    public int PulseLeft;
    public double PulseT;
    /// <summary>An On-kill Turn may echo again from this time (its internal gap).</summary>
    public double OnKillT = double.NegativeInfinity;
    /// <summary>The strength of the firing now (an On-kill echo's), on all its damage; 1 otherwise.</summary>
    public double FireMul = 1;
    Tag[]? tags;
    WickFx? wick;

    /// <summary>Its lit wick's numbers (Sim/Turns.cs); null, no wick, and it fights as it always did.</summary>
    public WickFx? Wick
    {
        get => wick;
        set { wick = value; tags = null; }
    }

    public WeaponInst(string id, int rank, int slot)
    {
        Id = id;
        Def = Content.Weapons.Get(id);
        Rank = rank;
        Slot = slot;
        Timer = 0.4 + slot * 0.17;
    }

    public Evolution? Evolution
    {
        get => evolution;
        set { evolution = value; tags = null; }
    }

    public WeaponBehavior Behavior => evolution?.Behavior ?? Def.Behavior;
    /// <summary>How it is set off: the evolution's own, else its skill's (a union's weapon is its own skill).</summary>
    public CastMode Cast => CastSet ?? CampaignCast ?? evolution?.Cast ?? Def.Cast;
    /// <summary>Set by hand over data (a test, later a toggle): press or kindle this one regardless of its skill.</summary>
    public CastMode? CastSet;
    /// <summary>An auto skill's kindle condition (the evolution's, else the skill's): null fires on the wait alone. In its
    /// kindled form in the campaign, its record's kindled condition first.</summary>
    public KindleDef? Kindle => Unkindled ? null : (KindledNow ? Press!.Kindled?.Condition() : null) ?? evolution?.Kindle ?? Def.Kindle;

    /// <summary>Its press record (WeaponDef.Press), set only in the campaign (Battle.AddWeapon when Battle.Campaign): null
    /// everywhere else, and the skill is set off as "cast" says.</summary>
    public PressDef? Press;
    /// <summary>The campaign slot runs its kindled option (WeaponInst.SetForm "kindle"): it fires itself on its kindled
    /// condition, and its key does the kindled press.</summary>
    public bool KindledForm;
    /// <summary>Kindled now: a kind-kindle skill, or one set to its kindled form (campaign only).</summary>
    public bool KindledNow => Press != null && (KindledForm || Press.Kind == PressKind.Kindle);
    /// <summary>How the record sets it off in the campaign: kindled, by itself; else hold and press on the key, channel held.</summary>
    CastMode? CampaignCast => Press == null ? null : KindledNow ? CastMode.Auto : Press.Kind == PressKind.Channel ? CastMode.Channel : CastMode.Press;
    /// <summary>A hold skill (the grips): fires whenever ready while its key is held, at the moving aim.</summary>
    public bool Hold => Press?.Kind == PressKind.Hold && !KindledNow;
    /// <summary>Its key does something: pressed, or kindled with a live press (campaign).</summary>
    public bool Keyed => Pressed || KindledNow;
    /// <summary>What a kindled skill's key does (its record's; now if unsaid).</summary>
    public KindlePress KindleKey => Press?.Kindled?.Press ?? KindlePress.Now;
    /// <summary>The skill is offered kindled: kind kindle, or a kindled option.</summary>
    public static bool OfferedKindled(WeaponDef d) => d.Press is { } r && (r.Kind == PressKind.Kindle || r.Kindled != null);
    /// <summary>The cast forms a record allows (taught_builds.json "cast"): its kind, and kindle when offered kindled.</summary>
    public static bool Allows(WeaponDef d, string cast)
    {
        if (d.Press is not { } r) return cast == "auto";
        string kind = (r.Kind ?? PressKind.Press).ToString().ToLowerInvariant();
        return cast == kind || (cast == "kindle" && OfferedKindled(d));
    }
    /// <summary>Runs the slot as the record's kind or its kindled option ("kindle"; any other its kind): false when the
    /// record does not allow it (nothing changes).</summary>
    public bool SetForm(string cast)
    {
        if (Press == null || !Allows(Def, cast)) return false;
        KindledForm = cast == "kindle" && Press.Kind != PressKind.Kindle;
        return true;
    }
    /// <summary>A kindled key's own wait (riposte, flare, command), and an aura's flare: until when, and its multipliers.</summary>
    public double PressWait, FlareUntil = -1, AuraMul = 1, AuraArea = 1;
    /// <summary>The last cast was its own heavy one (read by the cast pose after CastOnce).</summary>
    public bool WasOwnHeavy;
    /// <summary>Fires on its wait alone whatever its data says (tests that fire a skill by hand).</summary>
    public bool Unkindled;
    /// <summary>Waits for a press (or a hold) instead of firing itself.</summary>
    public bool Pressed => Cast != CastMode.Auto;
    /// <summary>A channel's longest hold, and the seconds between its firings while held.</summary>
    public double ChannelMax => Num(s => s.ChannelTime) ?? 3;
    public double ChannelEvery => Math.Max(0.05, Num(s => s.ChannelGap) ?? Num(s => s.TickRate) ?? 0.4);
    /// <summary>How far ahead a press with no cursor aims (her facing times this): its range, else its reach.</summary>
    public double AimRange => Num(s => s.Range) ?? Num(s => s.Reach) ?? 14;
    /// <summary>On a slot (either of a union's two).</summary>
    public bool On(int slot) => slot >= 0 && (Slot == slot || Slot2 == slot);
    /// <summary>A school Turn's school first: the Turn is what she chose for it.</summary>
    public School School => wick?.School ?? evolution?.School ?? Def.School;
    public string Art => evolution?.Art ?? Def.Art;

    /// <summary>What it is: its own tags, what the evolution adds, and its school.</summary>
    public Tag[] Tags
    {
        get
        {
            if (tags != null) return tags;
            var t = new List<Tag>(Def.Tags);
            if (evolution?.AddTags is { } add) foreach (var a in add) if (!t.Contains(a)) t.Add(a);
            // A school Turn takes the old school's tag away (physical stays: the steel is still steel).
            if (wick?.School != null && wick.From != School.Physical) t.Remove(wick.From.AsTag());
            var s = School.AsTag();
            if (!t.Contains(s)) t.Add(s);
            return tags = t.ToArray();
        }
    }

    /// <summary>A number from the evolution's overrides, else the base.</summary>
    public double? Num(Func<WeaponStats, double?> f) => (evolution?.Set is { } s ? f(s) : null) ?? f(Def.Base);
    public int? Int(Func<WeaponStats, int?> f) => (evolution?.Set is { } s ? f(s) : null) ?? f(Def.Base);
    public bool Flag(Func<WeaponStats, bool?> f) => ((evolution?.Set is { } s ? f(s) : null) ?? f(Def.Base)) == true;
    public StatusPayload? StatusOf => WickStatus(evolution?.Set?.Status ?? Def.Base.Status);
    public GroundSpec? GroundOf => evolution?.Set?.GroundOnHit ?? Def.Base.GroundOnHit ?? wick?.Ground;

    /// <summary>A school Turn: the old school's own status becomes the new school's (a frost bolt turned fire burns).</summary>
    StatusPayload? WickStatus(StatusPayload? p) =>
        p != null && wick is { School: not null, Status: { } to } && p.Kind == Turns.NativeStatus(wick.From) ? to with { Chance = p.Chance } : p;

    public double Damage
    {
        get
        {
            double d = (Def.Base.Damage ?? 0) * (1 + Def.Growth * (Rank - 1)) * Mods.Damage;
            if (evolution != null) d *= evolution.Mods.Damage ?? 1;
            if (wick != null) d *= wick.Damage;
            return d * FireMul * AuraMul;
        }
    }

    public double BossDamage => Def.BossDamage ?? 1;

    /// <summary>Critical strike chance its own blows add (Starseeker's sure strikes).</summary>
    public double CritBonus => Num(s => s.Crit) ?? 0;
}

/// <summary>A pending line a spin threw (Ev.SpinLine): its ends and width.</summary>
public sealed record SpinLineRec(int Id, double X0, double Z0, double X1, double Z1, double Width);

/// <summary>How each behaviour turns a weapon into things on the field.</summary>
public static partial class Firing
{
    public static double CooldownOf(Battle b, WeaponInst w)
    {
        double c = BaseCooldown(b, w) * b.Stats.Get(Stat.Cooldown) * w.Mods.Cooldown * b.ReaverCooldownMul(w) * b.ArcanistCooldownMul(w) * b.StalkerCooldownMul(w) * b.FlareCooldownMul(w) * b.RuleCooldownMul(w);
        if (b.Lamps.Board) c *= b.BoardCooldownMul(w);
        if (w.Evolution != null) c *= w.Evolution.Mods.Cooldown ?? 1;
        if (w.Wick != null) c *= w.Wick.Cooldown;
        return Math.Max(0.08, Math.Min(20, c));
    }

    /// <summary>Its cooldown before the multipliers: the campaign record's wait for a pressed skill (a spender's only
    /// while a resource pays for it), else its base cooldown. (M3) A kindled spender whose key heaves (Groundbreaker, the
    /// Disc) waits its record's wait too while Resolve pays: its cost is its gate, as the pressed form's is.</summary>
    static double BaseCooldown(Battle b, WeaponInst w) =>
        w.Press is { Wait: { } wait } r && (w.Pressed && (b.Resolve.On || (r.Resolve ?? 0) <= 0 && (r.Drain ?? 0) <= 0)
            || w.KindledNow && w.KindleKey == KindlePress.Now && b.Resolve.On && (r.Resolve ?? 0) > 0) ? wait : w.Def.Base.Cooldown ?? 1;

    public static double AreaOf(Battle b, WeaponInst w, double baseValue)
    {
        double a = baseValue * b.Stats.Get(Stat.Area) * (1 + Content.Weapons.AreaStep * (w.Rank - 1)) * w.Mods.Area;
        if (w.Evolution != null) a *= w.Evolution.Mods.Area ?? 1;
        if (w.Wick != null) a *= w.Wick.Area;
        // sunderer.skill.area / tags.area: the skill's lamps and its tags' lamps reach wider.
        a *= 1 + b.Lamps.SizeOn("skill.area", "inc", w.Def.Id, w.Def.Tags) + b.Lamps.SizeOn("tags.area", "inc", w.Def.Id, w.Def.Tags) + b.StormReach(w);
        // The reaver's Hand: hurt below half, her areas reach wider.
        a *= b.HandAreaMul(w);
        return a * w.AuraArea;
    }

    /// <summary>bulwark.skill.reach: metres of reach a skill's lamp adds (Oathblade, 1.5).</summary>
    static double ReachAdd(Battle b, WeaponInst w) => b.Lamps.SizeOn("skill.reach", "add", w.Def.Id, w.Def.Tags) + b.ChainReach(w);

    /// <summary>The status a skill strikes with: its own, or the one its lamp gives (sunderer.skill.status).</summary>
    public static StatusPayload? StatusWith(Battle b, WeaponInst w) =>
        b.RuleStatus(w) ?? w.StatusOf ?? (b.Lamps.HasOn("skill.status", w.Def.Id, w.Def.Tags) && b.Lamps.Each["skill.status"].Find(e => e.Status != null && (e.Skill == w.Def.Id)) is { Status: { } k } ? new StatusPayload(k, 1, 1, 3) : null);

    public static double DurationOf(Battle b, WeaponInst w, double baseValue)
    {
        double d = baseValue * b.Stats.Get(Stat.Duration) * (1 + Content.Weapons.DurationStep * (w.Rank - 1)) * w.Mods.Duration * (1 + b.ZoneLonger(w));
        if (w.Evolution != null) d *= w.Evolution.Mods.Duration ?? 1;
        if (b.Lamps.Board) d *= b.BoardDurationMul(w);
        return d;
    }

    public static int CountOf(Battle b, WeaponInst w, int? baseCount = null)
    {
        int n = baseCount ?? w.Def.Base.Projectiles ?? 1;
        if (w.Rank >= Content.Weapons.ProjRankA) n++;
        if (w.Rank >= Content.Weapons.ProjRankB) n++;
        n += RoundInt(b.Stats.Get(Stat.Projectiles)) + w.Mods.Projectiles + b.ArcanistProjectiles(w) + b.StalkerProjectiles(w);
        if (w.Evolution != null) n += w.Evolution.Mods.Projectiles ?? 0;
        // Split: three smaller, of everything it would throw.
        if (w.Wick is { Projectiles: not 1 } wk) n = (int)Math.Round(n * wk.Projectiles);
        return Math.Max(1, n);
    }

    public static double SpeedOf(Battle b, WeaponInst w)
    {
        double s = (w.Def.Base.Speed ?? 9) * b.Stats.Get(Stat.ProjectileSpeed) * w.Mods.Speed * b.ArcanistSpeedMul(w);
        if (w.Evolution != null) s *= w.Evolution.Mods.Speed ?? 1;
        if (w.Wick != null) s *= w.Wick.Speed;
        return s;
    }

    static int PierceOf(Battle b, WeaponInst w) =>
        b.StalkerPierce(w, (int)(w.Num(s => s.Pierce) ?? 0) + RoundInt(b.Stats.Get(Stat.Pierce)) + w.Mods.Pierce + (w.Evolution?.Mods.Pierce ?? 0)) + b.HandPierce(w);

    static double RangeOf(WeaponInst w) => w.Num(s => s.Range) ?? 14;

    /* ------------------------------------------------------------- firing -- */

    public static void Tick(Battle b, WeaponInst w, double dt)
    {
        if (w.DisabledT > 0) { w.DisabledT -= dt; return; }
        // A kindled key's own wait, and an aura's flare running out (campaign only: both stay at rest elsewhere).
        if (w.PressWait > 0) w.PressWait = Math.Max(0, w.PressWait - dt);
        if (w.FlareUntil >= 0 && b.Time > w.FlareUntil) { w.FlareUntil = -1; w.AuraMul = w.AuraArea = 1; }
        // Rebuke never fires on its timer: a blow that reaches her strikes it (Battle.RebukeOnBlow).
        if (w.Behavior == WeaponBehavior.Reactive) return;
        // Oath and Bell: a stagger owed the bell a toll; it goes off now, its own timer untouched.
        if (w.Behavior == WeaponBehavior.Toll && b.BellOwed) b.TollOwed(w);
        w.Timer -= dt;
        if (w.BurstLeft > 0)
        {
            w.BurstT -= dt;
            if (w.BurstT <= 0)
            {
                w.BurstLeft--;
                w.BurstT = 0.07;
                var hb0 = b.HeavyBy;
                b.HeavyBy = w.HeavyCast ? w : null;
                FireBurstShot(b, w);
                b.HeavyBy = hb0;
            }
        }
        // Pulse: the cast goes off again, the same firing, heavy if the cast was (as burst shots are); not a new blow.
        if (w.PulseLeft > 0)
        {
            w.PulseT -= dt;
            if (w.PulseT <= 0)
            {
                w.PulseLeft--;
                w.PulseT = w.Wick?.PulseGap ?? 0.3;
                var (hb0, rf0) = (b.HeavyBy, b.Refiring);
                b.HeavyBy = w.HeavyCast ? w : null;
                b.Refiring = true;
                Fire(b, w);
                (b.HeavyBy, b.Refiring) = (hb0, rf0);
            }
        }
        // A pressed skill counts its wait down and never fires on its own (Battle.PressSkill sets it off).
        if (w.Pressed) { TickPressed(b, w, dt); return; }
        if (w.Timer > 0) return;
        // Kindled: wait over is not enough; look again in a tenth of a second (read only when ready, so a crowd costs nothing).
        // A kindled spender (campaign, Resolve): it waits for the whole cost too (ready all the while: its key may heave
        // with less), and spends it on firing. (M3) One whose key heaves (kindled press "now": Groundbreaker, the Disc)
        // fires itself only when Resolve is full (ResolveMeter.SelfAt of the cap) and the heave takes all of it: her key
        // heaves from its cost (from half, at what she has), so a hand that presses spends ~2.5x as often as one that waits.
        double cost = b.CostOf(w);
        bool selfHeave = cost > 0 && w.KindledNow && w.KindleKey == KindlePress.Now;
        if (cost > 0 && b.Resolve.Value < (selfHeave ? ResolveMeter.SelfAt * b.Resolve.Max : cost)) { w.Timer = 0; return; }
        if (w.Kindle is { } kd && !b.Kindled(kd)) { w.Timer = 0.1; w.Relooking = true; return; }
        int kills0 = w.Kills;
        bool fired = CastOnce(b, w);
        if (fired && cost > 0) b.Resolve.Spend(selfHeave ? b.Resolve.Value : cost);
        // Nothing in range: look again soon rather than waiting a whole cooldown.
        Rearm(b, w, fired, kills0);
    }

    /// <summary>One cast of the skill, as its own timer would fire it (the Hand's blow, its own heavy, its Pulse,
    /// the arcanist's and the board's after-cast): true when it fired. The timer is the caller's.</summary>
    static bool CastOnce(Battle b, WeaponInst w)
    {
        b.ArcanistBeforeCast(w);
        // The warden's Hand: every few blows one is heavy, and every hit of it (HitEnemy reads HeavyBy).
        bool heavy = b.HandBeginCast(w);
        // Its own count (Sunder's): a firing heavy for either reason is just heavy; its own count also drives its line.
        int own = HeavyEveryOf(b, w);
        w.OwnHeavy = own > 0 && (w.OwnBlows + 1) % own == 0;
        heavy |= w.OwnHeavy;
        var hb = b.HeavyBy;
        b.HeavyBy = heavy ? w : null;
        // A builder in the campaign (Resolve on): count what this swing struck (Battle.HitEnemy adds to StruckBy's set).
        bool builds = b.Resolve.On && w.Press?.Builds is > 0 && b.StruckBy == null;
        if (builds) { b.StruckBy = w; b.Struck.Clear(); }
        bool fired = Fire(b, w);
        if (builds) { b.StruckBy = null; if (fired && b.Struck.Count > 0) b.Resolve.Landed(w.Press!, b.Struck.Count, heavy); }
        b.HeavyBy = hb;
        w.WasOwnHeavy = fired && w.OwnHeavy;
        w.OwnHeavy = false;
        if (fired && own > 0) w.OwnBlows++;
        b.HandEndCast(w, fired);
        if (fired) w.HeavyCast = heavy;
        if (fired && w.Wick is { Pulses: > 1 } pw) { w.PulseLeft = pw.Pulses - 1; w.PulseT = pw.PulseGap; }
        b.ArcanistAfterCast(w, fired);
        if (b.Lamps.Board) b.BoardAfterFire(w, fired);
        return fired;
    }

    /// <summary>The wait after a cast: its cooldown, or a quarter second when it found nothing.</summary>
    static void Rearm(Battle b, WeaponInst w, bool fired, int kills0)
    {
        w.Timer = fired ? CooldownOf(b, w) : 0.25;
        w.Relooking = !fired;
        // sunderer.momentum: a melee swing that kills enough brings the skill's next swing sooner.
        if (fired && w.Tags.Has(Tag.Melee) && b.Lamp("momentum") && w.Kills - kills0 >= b.Lamps.Full("momentum", "kills", 3))
            w.Timer *= 1 - Math.Min(0.9, b.Lamps.Size("momentum", "sooner"));
        b.RuleRearm(w, fired);
    }

    /* A pressed skill's own clock: its wait runs down to ready and stays there; a channel fires on its gap while
     * its key is held, and ends on release or at its longest hold, its cooldown starting then. */
    static void TickPressed(Battle b, WeaponInst w, double dt)
    {
        if (w.Behavior == WeaponBehavior.Spin && w.Slot2 >= 0) TickHalf(b, w, dt);
        if (!w.Channeling)
        {
            if (w.Timer < 0) w.Timer = 0;
            if (w.Lines.Count > 0 && b.Time > w.BreakUntil) FadeLines(b, w);
            // Hold to repeat (campaign, the grips): ready while held, it fires again at the current aim.
            if (w.Hold && w.Held && w.Timer <= 0 && w.DisabledT <= 0) b.PressHeld(w);
            return;
        }
        w.Timer = 0;
        w.ChannelT += dt;
        // Drained (campaign, Resolve): it runs while held and Resolve lasts, no cap; at 0 the storm ends.
        double drain = b.Resolve.On ? (w.Press?.Drain ?? 0) * b.RulePayMul(w) : 0;
        if (drain > 0 && w.Held) b.Resolve.Drain(drain * dt);
        if (!w.Held || (drain > 0 ? b.Resolve.Value <= 0 : w.ChannelT >= w.ChannelMax)) { EndChannel(b, w); return; }
        w.ChannelNext -= dt;
        if (w.ChannelNext > 0) return;
        w.ChannelNext += w.ChannelEvery;
        if (w.ChannelNext <= 0) w.ChannelNext = w.ChannelEvery;
        CastOnce(b, w);
    }

    static void EndChannel(Battle b, WeaponInst w)
    {
        w.StormT = w.ChannelT;
        w.Channeling = false;
        w.Timer = CooldownOf(b, w);
        b.Events.Emit(new Ev.Channel { Weapon = w.Id, Slot = w.Slot, On = false, X = b.Player.X, Z = b.Player.Z });
        if (w.Behavior == WeaponBehavior.Spin) SpinEnded(b, w);
    }

    /// <summary>Its key pressed (Battle.PressSkill): a press skill fires once if ready; a channel starts (its first
    /// firing now) if ready and not already running. True when it went off.</summary>
    public static bool Press(Battle b, WeaponInst w)
    {
        if (!w.Pressed || w.DisabledT > 0 || w.Timer > 0 || w.Channeling || b.BlowPending(w)) return false;
        // A spender (campaign, Resolve) fires only with its whole cost, and spends it on firing.
        double cost = b.CostOf(w);
        if (cost > 0 && b.Resolve.Value < cost) return false;
        if (w.Cast == CastMode.Channel)
        {
            // A drained channel needs a breath of Resolve to start (one gap's worth).
            if (b.Resolve.On && w.Press?.Drain is double dr && dr > 0 && b.Resolve.Value < dr * w.ChannelEvery) return false;
            if (cost > 0) b.Resolve.Spend(cost);
            b.Resolve.SpentInStorm = 0;
            b.CastPose(w);
            w.Channeling = true;
            w.ChannelT = 0;
            w.ChannelNext = w.ChannelEvery;
            w.SpinTicks = 0;
            w.StormAt = b.Time;
            b.Events.Emit(new Ev.Channel { Weapon = w.Id, Slot = w.Slot, On = true, X = b.Player.X, Z = b.Player.Z });
            CastOnce(b, w);
            return true;
        }
        int kills0 = w.Kills;
        var aim0 = b.CastAt;
        b.CastAt = b.AimFor(w);
        bool fired;
        // (campaign: a blow with a clip lands on its contact, Sim/Contact.cs; the press spends and poses her now)
        bool later = false;
        try { later = b.DeferBlow(w); fired = later || CastOnce(b, w); }
        finally { b.CastAt = aim0; }
        if (later)
        {
            if (cost > 0) b.Resolve.Spend(cost);
            b.CastPose(w);
            return true;
        }
        // (A press that found nothing stays ready: the buffer tries again for a breath.)
        if (fired)
        {
            Rearm(b, w, true, kills0);
            if (cost > 0) b.Resolve.Spend(cost);
            b.CastPose(w);
        }
        return fired;
    }

    /// <summary>A kindled skill's "now" (Battle.KindledPress): one cast as its timer would fire it, its condition skipped,
    /// then its wait. True when it went off.</summary>
    internal static bool CastNow(Battle b, WeaponInst w)
    {
        int kills0 = w.Kills;
        bool fired = CastOnce(b, w);
        if (fired) Rearm(b, w, true, kills0);
        return fired;
    }

    /// <summary>Where the skill fires from: her, or the corpse an On-kill echo rises from (Battle.FireFrom).</summary>
    static (double X, double Z) At(Battle b) => b.FireFrom ?? (b.Player.X, b.Player.Z);

    /// <summary>On-kill: the skill fires once more from a corpse, at the Turn's strength. Not a cast: no Hand blow,
    /// no heavy, no attack pose on her, no burst restarted; its kills never echo again (Battle.Echoing).</summary>
    public static bool OnKillEcho(Battle b, WeaponInst w, double x, double z)
    {
        var (from, rf, ech, hb, mul) = (b.FireFrom, b.Refiring, b.Echoing, b.HeavyBy, w.FireMul);
        b.FireFrom = (x, z); b.Refiring = true; b.Echoing = true; b.HeavyBy = null;
        w.FireMul = w.Wick?.OnKillDamage ?? 1;
        try { return Fire(b, w); }
        finally { (b.FireFrom, b.Refiring, b.Echoing, b.HeavyBy, w.FireMul) = (from, rf, ech, hb, mul); }
    }

    /// <summary>moonweaver.the_echo: the spell fires again.</summary>
    public static bool Echo(Battle b, WeaponInst w) => Fire(b, w);

    static bool Fire(Battle b, WeaponInst w) => w.Behavior switch
    {
        WeaponBehavior.Aimed => FireAimed(b, w),
        WeaponBehavior.Spray => FireSpray(b, w),
        WeaponBehavior.Ring => FireRing(b, w),
        WeaponBehavior.Nova => FireNova(b, w),
        WeaponBehavior.Zone => FireZone(b, w),
        WeaponBehavior.Chain => FireChain(b, w),
        WeaponBehavior.Orbit => FireOrbit(b, w),
        WeaponBehavior.Storm => FireStorm(b, w),
        WeaponBehavior.Bounce => FireBounce(b, w),
        WeaponBehavior.Beam => FireBeam(b, w),
        WeaponBehavior.Palm => FirePalm(b, w),
        WeaponBehavior.Herd => FireHerd(b, w),
        WeaponBehavior.Chakram => FireChakram(b, w),
        WeaponBehavior.Slash => FireSlash(b, w),
        WeaponBehavior.Raise => FireRaise(b, w),
        WeaponBehavior.Crack => FireCrack(b, w),
        WeaponBehavior.Reactive => FireReactive(b, w),
        WeaponBehavior.Toll => FireToll(b, w),
        WeaponBehavior.Leap => b.SkillLeap(w),
        WeaponBehavior.Charge => b.SkillCharge(w),
        WeaponBehavior.Spin => FireSpin(b, w),
        WeaponBehavior.Brace => b.SkillBrace(w),
        _ => false,
    };

    static bool FireAimed(Battle b, WeaponInst w)
    {
        // A skill that hunts the strongest is aimed at it from the hand, not only in flight.
        var o = At(b);
        var target = SeekOf(w) is Seek.Elite or Seek.Strongest ? b.Prioritized(o.X, o.Z, RangeOf(w)) ?? Toughest(b, RangeOf(w)) : b.NearestHostile(o.X, o.Z, RangeOf(w));
        if (target == null) return false;
        int n = CountOf(b, w);
        // (A Pulse's follow-up or an On-kill echo looses its shots at once, leaving the cast's burst as it is.)
        if (w.Flag(s => s.Burst) && !b.Refiring)
        {
            // A burst still firing (the Echo comes 0.5 s after the cast, a long burst runs past a short wait)
            // is let go at once, at its own strength, not cut short by this one.
            while (w.BurstLeft > 0) { w.BurstLeft--; FireBurstShot(b, w); }
            w.BurstMul = w.CastMul;
            w.BurstLeft = n - 1;
            w.BurstT = 0.07;
            w.BurstTarget = target.Id;
            FireAimedOne(b, w, target.Id);
        }
        else
            for (int i = 0; i < n; i++) FireAimedOne(b, w, target.Id, (i - (n - 1) / 2.0) * 0.14);
        return true;
    }

    static void FireBurstShot(Battle b, WeaponInst w)
    {
        double keep = w.CastMul;
        w.CastMul = w.BurstMul;
        FireAimedOne(b, w, w.BurstTarget);
        w.CastMul = keep;
    }

    static void FireAimedOne(Battle b, WeaponInst w, int targetId, double angleOffset = 0)
    {
        var p = At(b);
        Enemy? t = targetId >= 0 ? b.Enemies.Items[targetId] : null;
        if (t == null || !t.Alive || t.State == EnemyState.Dying) t = b.NearestHostile(p.X, p.Z, RangeOf(w));
        if (t == null) return;
        double homing = w.Num(s => s.Homing) ?? 0;
        double a = Math.Atan2(t.Z - p.Z, t.X - p.X) + angleOffset + (homing != 0 ? (b.Rng.Next() - 0.5) * 0.9 : 0);
        Launch(b, w, a, target: t.Id);
    }

    static Projectile? Launch(Battle b, WeaponInst w, double angle, int? target = null, double? x = null, double? z = null,
        double speedMul = 1, double? life = null, bool chakram = false, bool herd = false)
    {
        var p = At(b);
        double sp = SpeedOf(b, w) * speedMul;
        var pr = b.SpawnProjectile(Side.Player, x ?? p.X + Math.Cos(angle) * 0.5, z ?? p.Z + Math.Sin(angle) * 0.5, DamageFor(w) * w.CastMul, w.School);
        if (pr != null)
        {
            pr.Y = 1.1;
            pr.Vx = Math.Cos(angle) * sp; pr.Vz = Math.Sin(angle) * sp; pr.Speed = sp;
            pr.Tags = w.Tags;
            pr.Radius = (w.Num(s => s.Radius) ?? 0.2) * Math.Sqrt(b.Stats.Get(Stat.Area));
            pr.Pierce = PierceOf(b, w);
            if (b.HandPierce(w) > 0) b.HandPierced(pr);
            pr.Bounces = (int)(w.Num(s => s.Bounces) ?? 0) + (w.Evolution?.Mods.Bounces ?? 0) + (w.Wick?.Bounces ?? 0);
            pr.Life = life ?? DurationOf(b, w, w.Num(s => s.Life) ?? 2.0) / (1 + Content.Weapons.DurationStep * (w.Rank - 1));
            pr.Homing = (w.Num(s => s.Homing) ?? 0) + w.Mods.Homing;
            pr.Seek = b.StalkerSeek(w, b.ArcanistSeek(w, SeekOf(w)));
            // A hunter of the strongest or the marked picks its own prey in flight.
            pr.Target = pr.Seek is Seek.Strongest or Seek.Elite or Seek.Marked ? -2 : target ?? -2;
            pr.Weapon = w.Id;
            b.ArcanistLaunched(pr, w);
            b.StalkerLaunched(pr, w);
            pr.Art = w.Art;
            pr.Status = w.StatusOf;
            var splash = w.Num(s => s.Splash);
            pr.Splash = splash is { } sv && sv != 0 ? AreaOf(b, w, sv) : 0;
            pr.SplitOnHit = w.Int(s => s.SplitOnHit) ?? 0;
            pr.Heal = w.Num(s => s.Heal) ?? 0;
            pr.Knockback = b.Pulsing ? 0 : w.Num(s => s.Knockback) ?? 0;
            pr.Chakram = chakram;
            pr.GroundOnHit = w.GroundOf;
            // The Falling Star (a Mark): the cinder's blast leaves the ground burning.
            if (pr.GroundOnHit == null && w.Id == "cinderfall" && b.Marked(Marks.FallingStar, out double star))
                pr.GroundOnHit = new GroundSpec(1.8, Marks.Lerp(2, 5, star), 0.25);
            pr.Rank = w.Rank;
            pr.BossDamage = w.BossDamage;
            pr.AimAlongVelocity();
            if (herd) pr.Rehit = 0.6;
        }
        b.Events.Emit(new Ev.Muzzle { X = p.X, Z = p.Z, Angle = angle, School = w.School, Weapon = w.Id, Art = w.Art, Rank = w.Rank });
        return pr;
    }

    static double DamageFor(WeaponInst w) => w.Damage;

    /// <summary>What its projectiles hunt: the evolution's choice, else the weapon's, else the nearest.</summary>
    static Seek? SeekOf(WeaponInst w) => w.Evolution?.Set?.Seek ?? w.Def.Base.Seek;

    /// <summary>The toughest thing in reach: a boss, then a champion, then the most health.</summary>
    static Enemy? Toughest(Battle b, double range)
    {
        Enemy? best = null;
        var o = At(b);
        foreach (var e in b.HostilesInRadius(o.X, o.Z, range))
            if (best == null || (e.Boss ? 2e6 : e.Elite ? 1e6 : 0) + e.MaxHp > (best.Boss ? 2e6 : best.Elite ? 1e6 : 0) + best.MaxHp) best = e;
        return best;
    }

    static bool FireSpray(Battle b, WeaponInst w)
    {
        var p = At(b);
        var t = b.NearestHostile(p.X, p.Z, RangeOf(w));
        if (t == null) return false;
        int n = CountOf(b, w);
        double spread = w.Num(s => s.Spread) ?? 0.16;
        double a0 = Math.Atan2(t.Z - p.Z, t.X - p.X);
        for (int i = 0; i < n; i++) Launch(b, w, a0 + (i - (n - 1) / 2.0) * spread, target: t.Id);
        // The Ravine (a Mark): a second volley at the farthest in reach, a part as strong.
        if (w.Id == "volley" && b.Marked(Marks.Ravine, out double ravine) && b.FarthestHostile(p.X, p.Z, RangeOf(w)) is { } far && far != t)
        {
            double af = Math.Atan2(far.Z - p.Z, far.X - p.X), k = Marks.Lerp(0.35, 0.9, ravine);
            for (int i = 0; i < n; i++)
                if (Launch(b, w, af + (i - (n - 1) / 2.0) * spread, target: far.Id) is { } pr) pr.Damage *= k;
        }
        // Arrowfall: the volley also rains on the densest knot of the crowd.
        if (w.Num(s => s.Strikes) is { } strikes && strikes != 0)
            StormAt(b, w, (int)strikes, w.Num(s => s.StormRadius) ?? 5, 1.3, w.Damage * 0.6);
        return true;
    }

    static bool FireRing(Battle b, WeaponInst w)
    {
        var o = At(b);
        if (b.NearestHostile(o.X, o.Z, 9) == null) return false;
        int n = CountOf(b, w);
        double rot = b.Time * 1.7;
        for (int i = 0; i < n; i++) Launch(b, w, rot + (double)i / n * Tau);
        return true;
    }

    static bool FireNova(Battle b, WeaponInst w)
    {
        var p = At(b);
        double r = AreaOf(b, w, w.Num(s => s.Radius) ?? 3.5) + ReachAdd(b, w);
        if (b.NearestHostile(p.X, p.Z, r + 1) == null) return false;
        int rings = 1 + (w.Rank >= Content.Weapons.ProjRankA ? 1 : 0) + (w.Rank >= Content.Weapons.ProjRankB ? 1 : 0);
        b.Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = r, School = w.School, Duration = w.Num(s => s.ExpandTime) ?? 0.35, Rings = rings, Art = w.Art, Rank = w.Rank });
        double dmg = w.Damage;
        // A Pulse's follow-ups don't throw back: the cast's push would carry the crowd out of the smaller ring.
        double kb = b.Pulsing ? 0 : w.Num(s => s.Knockback) ?? 0;
        double heal = w.Num(s => s.Heal) ?? 0;
        var novaStatus = StatusWith(b, w);
        bool hitAny = false;
        b.ForEachHostileInRadius(p.X, p.Z, r, (e, d) =>
        {
            hitAny = true;
            double dd = d == 0 ? 1 : d;
            b.HitEnemy(e, dmg, w.School, w.Tags, new HitOpts
            {
                Weapon = w, Knockback = kb, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, Status = novaStatus, BossDamage = w.Def.BossDamage,
            });
        });
        if (heal != 0 && hitAny) b.HealPlayer(heal, "weapon");
        if (w.GroundOf is { } g)
        {
            var zn = b.SpawnZone(Side.Player, p.X, p.Z, AreaOf(b, w, g.Radius), DurationOf(b, w, g.Duration), dmg * g.DpsPct, w.School);
            if (zn != null) { zn.Tags = w.Tags; zn.Art = w.Art + "_ground"; zn.Weapon = w.Id; }
        }
        return true;
    }

    static bool FireZone(Battle b, WeaponInst w)
    {
        var p = At(b);
        double r = AreaOf(b, w, w.Num(s => s.Radius) ?? 3);
        double x = p.X, z = p.Z;
        bool atTarget = w.Flag(s => s.AtTarget);
        if (atTarget)
        {
            // Every other one goes under a champion or worse, when one is near:
            // a field that only ever finds the crowd never brings down what leads it.
            var big = (w.Swing++ & 1) == 1 ? b.NearestHostile(p.X, p.Z, 11, e => e.Elite || e.Boss) : null;
            var t = big ?? b.DensestHostile(p.X, p.Z, 11, r);
            if (t == null) return false;
            x = t.X; z = t.Z;
        }
        else if (b.NearestHostile(p.X, p.Z, r + 2) == null) return false;
        double tick = w.Num(s => s.TickRate) ?? 0.5;
        var zn = b.SpawnZone(Side.Player, x, z, r, DurationOf(b, w, w.Num(s => s.Duration) ?? 4), w.Damage / tick, w.School);
        if (zn != null)
        {
            zn.Tick = tick; zn.Tags = w.Tags; zn.Slow = w.Num(s => s.Slow) ?? 0; zn.Status = w.StatusOf;
            zn.Art = w.Art; zn.Weapon = w.Id; zn.Follow = !atTarget && b.FireFrom == null; zn.Armor = w.Evolution?.Id == "sanctified_earth" ? 6 : 0;
            zn.BossDamage = w.BossDamage;
        }
        return true;
    }

    static bool FireChain(Battle b, WeaponInst w)
    {
        var p = At(b);
        var first = b.Prioritized(p.X, p.Z, RangeOf(w)) ?? (b.Lamps.Board ? b.RodTarget(w, p.X, p.Z, RangeOf(w)) : null) ?? b.NearestHostile(p.X, p.Z, RangeOf(w));
        if (first == null) return false;
        int jumps = CountOf(b, w, (int)(w.Num(s => s.Chains) ?? 5) - 1) + (w.Evolution?.Mods.Chains ?? 0) + (w.Wick?.Chains ?? 0);
        double reach = AreaOf(b, w, w.Num(s => s.ChainRange) ?? 6);
        bool fork = w.Flag(s => s.Fork);
        ChainFrom(b, p.X, p.Z, first, jumps, reach, w.Damage, w.School, w.Tags, w, fork);
        return true;
    }

    public static void ChainFrom(Battle b, double x0, double z0, Enemy first, int jumps, double reach, double dmg,
        School school, Tag[] tags, WeaponInst? w, bool fork = false, bool sky = false, int depth = 0)
    {
        var hit = new HashSet<int>();
        var points = new List<double> { x0, z0 };
        Enemy? cur = first;
        var queue = new List<Enemy>();
        for (int j = 0; j <= jumps && cur != null; j++)
        {
            hit.Add(cur.Id);
            points.Add(cur.X); points.Add(cur.Z);
            b.HitEnemy(cur, dmg * Math.Pow(0.92, j), school, tags, new HitOpts
            {
                Weapon = w, Status = w?.StatusOf, Depth = depth, BossDamage = w?.Def.BossDamage,
            });
            if (sky) b.Events.Emit(new Ev.Strike { X = cur.X, Z = cur.Z, Radius = 0.9, School = school, Delay = 0, Art = "arc_sky", Rank = w?.Rank ?? 1 });
            var next = b.NearestHostile(cur.X, cur.Z, reach, e => !hit.Contains(e.Id));
            if (fork && next != null && j < jumps - 1)
            {
                var second = b.NearestHostile(cur.X, cur.Z, reach, e => !hit.Contains(e.Id) && e.Id != next.Id);
                if (second != null) queue.Add(second);
            }
            cur = next;
        }
        b.Events.Emit(new Ev.Chain { Points = points.ToArray(), School = school, Art = w?.Art, Rank = w?.Rank ?? 1 });
        // Forks run a shorter chain of their own from where they split.
        for (int i = 0; i < Math.Min(3, queue.Count); i++)
        {
            var f = queue[i];
            if (hit.Contains(f.Id)) continue;
            var pts = new[] { points[^2], points[^1], f.X, f.Z };
            b.HitEnemy(f, dmg * 0.7, school, tags, new HitOpts { Weapon = w, Depth = depth });
            b.Events.Emit(new Ev.Chain { Points = pts, School = school, Art = w?.Art, Rank = w?.Rank ?? 1 });
        }
    }

    static bool FireOrbit(Battle b, WeaponInst w)
    {
        // Only one gyre at a time: the next begins when the last one ends.
        if (b.Time < w.ActiveT) return false;
        if (b.NearestHostile(b.Player.X, b.Player.Z, 10) == null) return false;
        int n = CountOf(b, w);
        // The Gyre (a Mark): an axe more for every few close by, to three more.
        if (w.Id == "axe_gyre" && b.Marked(Marks.Gyre, out double gyre))
            n += Math.Min(3, (int)(b.HostilesInRadius(b.Player.X, b.Player.Z, 5).Count / Marks.Lerp(6, 3, gyre)));
        double life = DurationOf(b, w, w.Num(s => s.Duration) ?? 3);
        double radius = AreaOf(b, w, w.Num(s => s.OrbitRadius) ?? 2) + ReachAdd(b, w);
        double speed = w.Num(s => s.OrbitSpeed) ?? 4;
        for (int i = 0; i < n; i++)
        {
            var pr = b.SpawnProjectile(Side.Player, b.Player.X, b.Player.Z, w.Damage, w.School);
            if (pr == null) continue;
            pr.Y = 1; pr.Tags = w.Tags; pr.Radius = (w.Num(s => s.Radius) ?? 0.5) * Math.Sqrt(b.Stats.Get(Stat.Area));
            pr.Pierce = 999; pr.Life = life; pr.Weapon = w.Id; pr.Art = w.Art; pr.Status = StatusWith(b, w);
            pr.Knockback = 0.25; pr.Rank = w.Rank; pr.BossDamage = w.BossDamage;
            pr.OrbitR = radius;
            pr.OrbitW = speed;
            pr.OrbitA = (double)i / n * Tau;
            pr.Rehit = 0.45;
            pr.SlotId = w.Slot;
        }
        w.ActiveT = b.Time + life;
        return true;
    }

    static bool StormAt(Battle b, WeaponInst w, int strikes, double area, double splash, double dmg)
    {
        var p = At(b);
        var targets = b.HostilesInRadius(p.X, p.Z, area * b.Stats.Get(Stat.Area) + 3);
        if (targets.Count == 0) return false;
        targets = b.BoundFirst(w, targets); // chainbound.lightning_rod
        // blue.lightning_rod: the first strike falls on the nearest champion.
        var rod = b.Lamps.Board ? b.RodTarget(w, p.X, p.Z, area * b.Stats.Get(Stat.Area) + 3) : null;
        for (int i = 0; i < strikes; i++)
        {
            var t = i == 0 && rod != null ? rod : targets[b.Rng.Int(0, targets.Count - 1)];
            double x = t.X + (b.Rng.Next() - 0.5) * 1.2, z = t.Z + (b.Rng.Next() - 0.5) * 1.2;
            b.ScheduleStrike(x, z, AreaOf(b, w, splash), dmg, w.School, w.Tags, 0.28 + i * 0.05, w);
        }
        return true;
    }

    static bool FireStorm(Battle b, WeaponInst w)
    {
        int strikes = (int)(w.Num(s => s.Strikes) ?? 5) + (w.Evolution?.Mods.Strikes ?? 0) + RoundInt(b.Stats.Get(Stat.Projectiles));
        return StormAt(b, w, strikes, w.Num(s => s.StormRadius) ?? 6, w.Num(s => s.Splash) ?? 1.5, w.Damage);
    }

    static bool FireBounce(Battle b, WeaponInst w)
    {
        var p = At(b);
        // A campaign press: thrown at the hover foe, else toward the point (it hunts from there).
        var t = b.CastAt is { } ca ? ca.Foe : b.NearestHostile(p.X, p.Z, RangeOf(w));
        if (t == null && b.CastAt == null) return false;
        int n = CountOf(b, w);
        double a0 = t != null ? Math.Atan2(t.Z - p.Z, t.X - p.X) : AimAngle(b, b.CastAt!.Value.X, b.CastAt.Value.Z);
        for (int i = 0; i < n; i++)
        {
            var pr = Launch(b, w, a0 + (i - (n - 1) / 2.0) * 0.3, target: t?.Id);
            if (pr != null) pr.Homing = 7;
        }
        return true;
    }

    static bool FireBeam(Battle b, WeaponInst w)
    {
        var p = At(b);
        var t = b.NearestHostile(p.X, p.Z, RangeOf(w));
        if (t == null) return false;
        double a = Math.Atan2(t.Z - p.Z, t.X - p.X);
        double len = RangeOf(w) * (1 + 0.04 * (w.Rank - 1));
        double width = AreaOf(b, w, w.Num(s => s.BeamWidth) ?? 0.6);
        double x1 = p.X + Math.Cos(a) * len, z1 = p.Z + Math.Sin(a) * len;
        b.Events.Emit(new Ev.Beam { X0 = p.X, Z0 = p.Z, X1 = x1, Z1 = z1, Width = width, School = w.School, Duration = 0.35, Art = w.Art, Rank = w.Rank });
        double dmg = w.Damage;
        b.ForEachHostileNearSegment(p.X, p.Z, x1, z1, width, e =>
            b.HitEnemy(e, dmg, w.School, w.Tags, new HitOpts { Weapon = w, Status = w.StatusOf, BossDamage = w.Def.BossDamage }));
        return true;
    }

    static bool FirePalm(Battle b, WeaponInst w)
    {
        var p = At(b);
        double reach = AreaOf(b, w, w.Num(s => s.Reach) ?? 2.9) + ReachAdd(b, w);
        var targets = b.HostilesInRadius(p.X, p.Z, reach + 0.6);
        var far = b.IronReachTargets(w, reach + 0.6); // chainbound.iron_reach: Bound things out of the palm's own reach
        // A campaign press: the palms go first at what is nearest its aim, and with nothing in reach strike at the aim.
        if (b.CastAt is { } ca)
        {
            if (targets.Count == 0 && far.Count == 0) return ConeHit(b, w, AimAngle(b, ca.X, ca.Z), w.Num(s => s.Arc) ?? 1.25, reach, w.Damage) || true;
            targets.Sort((a, c) => ((a.X - ca.X) * (a.X - ca.X) + (a.Z - ca.Z) * (a.Z - ca.Z)).CompareTo((c.X - ca.X) * (c.X - ca.X) + (c.Z - ca.Z) * (c.Z - ca.Z)));
        }
        else
        {
        if (targets.Count == 0 && far.Count == 0) return false;
        targets.Sort((a, c) => ((a.X - p.X) * (a.X - p.X) + (a.Z - p.Z) * (a.Z - p.Z)).CompareTo((c.X - p.X) * (c.X - p.X) + (c.Z - p.Z) * (c.Z - p.Z)));
        }
        int n = CountOf(b, w);
        double arc = w.Num(s => s.Arc) ?? 1.25;
        for (int i = 0; i < n && targets.Count > 0; i++)
        {
            var t = targets[i % targets.Count];
            double a = Math.Atan2(t.Z - p.Z, t.X - p.X) + (i >= targets.Count ? (i - targets.Count + 1) * 0.6 : 0);
            ConeHit(b, w, a, arc, reach, w.Damage);
        }
        for (int i = 0; i < n && i < far.Count; i++) b.PalmFromAfar(w, far[i], StatusWith(b, w));
        return true;
    }

    /// <summary>The angle (the behaviors' own: atan2(dz, dx)) from where it fires to an aim point; her facing if it is
    /// under her feet.</summary>
    static double AimAngle(Battle b, double x, double z)
    {
        var p = At(b);
        double dx = x - p.X, dz = z - p.Z;
        return dx * dx + dz * dz > 0.01 ? Math.Atan2(dz, dx) : Math.Atan2(Math.Cos(b.Player.Facing), Math.Sin(b.Player.Facing));
    }

    static bool ConeHit(Battle b, WeaponInst w, double a, double arc, double reach, double dmg)
    {
        var p = At(b);
        b.Events.Emit(new Ev.Slash { X = p.X, Z = p.Z, Angle = a, Arc = arc, Reach = reach, School = w.School, Art = w.Art, Rank = w.Rank, Held = w.Hold });
        double kb = w.Num(s => s.Knockback) ?? 0;
        bool any = false;
        Enemy? last = null;
        var hitStatus = StatusWith(b, w);
        b.ForEachHostileInRadius(p.X, p.Z, reach, (e, d) =>
        {
            double da = Wrap(Math.Atan2(e.Z - p.Z, e.X - p.X) - a);
            if (Math.Abs(da) > arc / 2 + Math.Atan2(e.Radius, Math.Max(d, 0.1))) return;
            any = true;
            last = e;
            double dd = d == 0 ? 1 : d;
            b.HitEnemy(e, dmg, w.School, w.Tags, new HitOpts
            {
                Weapon = w, Knockback = kb, DirX = (e.X - p.X) / dd, DirZ = (e.Z - p.Z) / dd, Status = hitStatus, BossDamage = w.Def.BossDamage,
                Heavy = b.RuleBeforeCut(w, e),
            });
            b.RuleAfterCut(w, e, p.X, p.Z);
        });
        if (last != null) b.HookLast(w, last); // chainbound.the_long_chain
        return any;
    }

    static bool FireSlash(Battle b, WeaponInst w)
    {
        // An On-kill echo swings from the corpse, at the nearest creature to the corpse within the swing's reach (the
        // same rule as her swing, measured from where it fell); none near, and the echo doesn't go off.
        var p = At(b);
        double reach = AreaOf(b, w, b.RuleReach(w, w.Num(s => s.Reach) ?? 2.6)) * b.SkillStillReach(w) + ReachAdd(b, w);
        double a;
        // A campaign press swings toward its aim (the hover foe, else the point), struck or not: every press is seen.
        if (b.CastAt is { } ca) a = AimAngle(b, ca.X, ca.Z);
        else
        {
            var t = b.NearestHostile(p.X, p.Z, reach + 1.2);
            if (t == null) return false;
            a = Math.Atan2(t.Z - p.Z, t.X - p.X);
        }
        double arc = b.SkillArc(w, w.Num(s => s.Arc) ?? 2.2);
        int n = CountOf(b, w, 1);
        b.RuleChopBegin(w);
        for (int i = 0; i < n; i++)
        {
            double ai = a + (i == 0 ? 0 : (i % 2 == 1 ? 1 : -1) * Math.Ceiling(i / 2.0) * arc * 0.85);
            ConeHit(b, w, ai, arc, reach, w.Damage * b.RuleCutMul(w));
            b.RuleCrossCut(w, ai, arc, reach);
        }
        // Blades hit things as well as creatures: barrels, brambles, a boss's lamps.
        foreach (var c in b.Collision.Within(p.X, p.Z, reach))
        {
            if (c.Tag == null) continue;
            double da = Wrap(Math.Atan2(c.Z - p.Z, c.X - p.X) - a);
            if (Math.Abs(da) <= arc / 2 + 0.3) b.Hooks.OnHitProp?.Invoke(c.Tag, c.Id, w.School, w.Damage, c.X, c.Z);
        }
        // Its own heavy swing splits the ground ahead (Sunder's line).
        if (w.OwnHeavy && w.Num(s => s.Line) is { } line) HeavyLine(b, w, p.X, p.Z, a, line);
        // Linger: the swing leaves its ground where the arc's middle fell.
        if (w.Wick?.Ground is { } g)
        {
            double gx = p.X + Math.Cos(a) * reach * 0.55, gz = p.Z + Math.Sin(a) * reach * 0.55;
            var zn = b.SpawnZone(Side.Player, gx, gz, AreaOf(b, w, g.Radius), DurationOf(b, w, g.Duration), w.Damage * g.DpsPct, w.School);
            if (zn != null) { zn.Tags = w.Tags; zn.Art = w.Art + "_ground"; zn.Weapon = w.Id; }
        }
        w.Swing++;
        if (!b.Refiring && !b.Landing) b.Player.AttackAnim = new AttackAnim(w.Id, a, b.Time, arc > 3);
        // Oathkeeper: every swing throws a crescent onward.
        if (w.Evolution?.Id == "oathkeeper")
        {
            var pr = Launch(b, w, a, speedMul: 1, life: 0.9);
            // (The crescent pierces everything: a Linger ground at each would carpet the field. The swing's is enough.)
            if (pr != null) { pr.Pierce = 99; pr.Radius = 1.1; pr.Art = "crescent_holy"; pr.School = School.Holy; if (w.Wick?.Ground is { } wg && ReferenceEquals(pr.GroundOnHit, wg)) pr.GroundOnHit = null; }
        }
        if (w.Evolution?.Id == "bonesplitter")
            b.ScheduleStrike(p.X + Math.Cos(a) * reach * 1.4, p.Z + Math.Sin(a) * reach * 1.4, 1.8, w.Damage * 0.8, School.Physical, w.Tags, 0.12, w);
        return true;
    }

    static bool FireHerd(Battle b, WeaponInst w)
    {
        var p = At(b);
        var t = b.NearestHostile(p.X, p.Z, RangeOf(w));
        if (t == null) return false;
        int n = CountOf(b, w);
        double a = Math.Atan2(t.Z - p.Z, t.X - p.X);
        for (int i = 0; i < n; i++)
        {
            double off = (i - (n - 1) / 2.0) * 1.1;
            double sx = p.X - Math.Cos(a) * 3 + Math.Cos(a + Math.PI / 2) * off;
            double sz = p.Z - Math.Sin(a) * 3 + Math.Sin(a + Math.PI / 2) * off;
            Launch(b, w, a, x: sx, z: sz, herd: true, life: DurationOf(b, w, w.Num(s => s.Life) ?? 1.8));
        }
        return true;
    }

    /// <summary>The dead get up for you: allies of its kind, up to its count at
    /// once, for its duration, striking as hard as the skill is ranked.</summary>
    static bool FireRaise(Battle b, WeaponInst w)
    {
        var p = b.Player;
        if (b.NearestHostile(p.X, p.Z, 15) == null) return false;
        string kind = w.Evolution?.Set?.Raises ?? w.Def.Base.Raises ?? "ghoul_ally";
        b.RaiseFor(w, kind, DurationOf(b, w, w.Num(s => s.Duration) ?? 12), CountOf(b, w));
        return true;
    }

    static bool FireChakram(Battle b, WeaponInst w)
    {
        var p = At(b);
        double a0;
        if (b.CastAt is { } ca) a0 = AimAngle(b, ca.X, ca.Z);
        else
        {
            var t = b.NearestHostile(p.X, p.Z, RangeOf(w) + 2);
            if (t == null) return false;
            a0 = Math.Atan2(t.Z - p.Z, t.X - p.X);
        }
        int n = CountOf(b, w);
        for (int i = 0; i < n; i++)
        {
            var pr = Launch(b, w, a0 + (i - (n - 1) / 2.0) * 0.5, chakram: true, life: DurationOf(b, w, w.Num(s => s.Life) ?? 2.6));
            if (pr != null) { pr.Pierce = 999; pr.Rehit = 0.5; }
        }
        return true;
    }

    /// <summary>What a weapon card should say it does at its rank.</summary>
    public static (int Damage, double Cooldown, int Count) DescribeRank(Battle b, WeaponInst w) =>
        (RoundInt(w.Damage * b.Stats.DamageMult(w.School, w.Tags)), CooldownOf(b, w), CountOf(b, w));
}
