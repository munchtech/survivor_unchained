using System;
using System.Collections.Generic;
using System.Text.Json;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* Resolve: the Warden's resource (docs/design/ARPG.md 3.1), and the campaign's press path around it.
 *
 * API for M4 (the UI): Battle.Resolve (a ResolveMeter), read every sim step:
 *   On          bool    the meter counts: the campaign (Battle.Campaign) and the warden's calling. Off, every cost reads
 *                       as nothing and the bar is not drawn.
 *   Value, Max  double  0..Max (Max 100).
 *   Rate        double  signed Resolve a second over the last 1 s (fill +, spend, drain and fade -).
 *   LastReason  ResolveReason  Landed (her blows), Taken (blows on her), Blocked, Spent (a press's cost), Drained (a
 *                       channel: Bladestorm), Faded (out of a fight).
 *   LastDelta, LastAt   the last change and when (the battle's clock).
 *   SpentInStorm        Resolve the current (or last) storm drained: its break grows with it.
 *   Spent       double  (M3) Resolve spent and drained this fight, in all (the harness's spent a minute).
 *   Cap, TakenPer, BlockGain, FadeRate, FadeAfter, FightRadius, SelfAt   the numbers below, read from data/content/resolve.json.
 * Ev.Resolve is emitted when Value has moved a whole point or more since the last one told, or reached 0 or Max (never
 * every tick): Value, Max, Delta (since the last told), Reason (the change that crossed it).
 *
 * The rules:
 *   - Fill: a landed swing of a builder (PressDef.Builds; the swing struck at least one foe) gives Builds, plus
 *     BuildsEach for each foe past the first (at most BuildsMost), times HeavyMul on a heavy swing. Blows taken (1 for
 *     each 2% of max health lost, after armor) and blocks (4 each) fill too, but never past a third of the fill: a taken
 *     or block gain is allowed only up to 0.5 * LandedFill - TakenFill this fight. She fills by going in, never by standing.
 *   - Fade: out of a fight (no hostile within 12 m and no blow given or taken for 3 s) it falls 10 a second; never in one.
 *   - Spend: Battle.CostOf, read by Firing.Press and the kindled spenders. A channel with a Drain drains it while held
 *     and ends at 0. (M3) A kindled spender whose key heaves (press "now") fires itself only at SelfAt of the cap (full)
 *     and spends all of it; its key heaves at full strength from its cost and with what she has from half its cost.
 */
/// <summary>The meter's numbers (data/content/resolve.json).</summary>
public sealed class ResolveDef
{
    public double Cap = 100, TakenPer = 0.02, BlockGain = 4, FadeRate = 10, FadeAfter = 3, FightRadius = 12, SelfAt = 1;
    static ResolveDef? def;
    public static ResolveDef Data => def ??= JsonSerializer.Deserialize<ResolveDef>(Json.ReadContent("resolve.json"), Json.Options)!;
}

public enum ResolveReason { Landed, Taken, Blocked, Spent, Drained, Faded }

public sealed class ResolveMeter
{
    readonly Battle b;
    internal ResolveMeter(Battle battle) => b = battle;

    /// <summary>The numbers, from data/content/resolve.json (M3: were constants; the same names, types and values).</summary>
    public static readonly double Cap = ResolveDef.Data.Cap, TakenPer = ResolveDef.Data.TakenPer, BlockGain = ResolveDef.Data.BlockGain,
        FadeRate = ResolveDef.Data.FadeRate, FadeAfter = ResolveDef.Data.FadeAfter, FightRadius = ResolveDef.Data.FightRadius,
        SelfAt = ResolveDef.Data.SelfAt;

    public bool On => b.Campaign && b.Calling == "warden";
    public double Value { get; private set; }
    public double Max => Cap;
    public double Rate { get { Trim(); double s = 0; foreach (var (_, d) in recent) s += d; return s; } }
    public ResolveReason LastReason { get; private set; }
    public double LastDelta { get; private set; }
    public double LastAt { get; private set; } = double.NegativeInfinity;
    /// <summary>Running totals this fight: the landed fill, and the taken-and-blocked fill (held to half the landed).</summary>
    public double LandedFill { get; private set; }
    public double TakenFill { get; private set; }
    public double SpentInStorm;
    /// <summary>(M3) Resolve spent and drained this fight, in all.</summary>
    public double Spent { get; private set; }

    readonly Queue<(double T, double D)> recent = new();
    double told;

    void Trim() { while (recent.Count > 0 && recent.Peek().T < b.Time - 1) recent.Dequeue(); }

    /// <summary>Set it outright (tests, a checkpoint): no reason, nothing told.</summary>
    public void Set(double v) { Value = Math.Clamp(v, 0, Max); told = Value; }

    void Add(double d, ResolveReason why)
    {
        if (!On || d == 0) return;
        double v = Math.Clamp(Value + d, 0, Max), real = v - Value;
        if (real == 0) return;
        Value = v;
        if (why is ResolveReason.Spent or ResolveReason.Drained) Spent -= real;
        LastReason = why; LastDelta = real; LastAt = b.Time;
        recent.Enqueue((b.Time, real));
        Trim();
        if (Math.Abs(Value - told) >= 1 || (Value == 0 && told != 0) || (Value == Max && told != Max))
        {
            b.Events.Emit(new Ev.Resolve { Value = Value, Max = Max, Delta = Value - told, Reason = why });
            told = Value;
        }
    }

    /// <summary>A builder's swing struck `foes` (at least one).</summary>
    internal void Landed(PressDef r, int foes, bool heavy)
    {
        if (!On || foes <= 0) return;
        double g = (r.Builds ?? 0) + Math.Min(r.BuildsMost ?? 9, (r.BuildsEach ?? 3) * (foes - 1));
        if (heavy) g *= r.HeavyMul ?? 1.5;
        LandedFill += g;
        Add(g, ResolveReason.Landed);
    }

    /// <summary>A blow's or a block's gain, held to a third of the fill.</summary>
    void Defended(double g, ResolveReason why)
    {
        if (!On || g <= 0) return;
        g = Math.Min(g, Math.Max(0, 0.5 * LandedFill - TakenFill));
        if (g <= 0) return;
        TakenFill += g;
        Add(g, why);
    }

    internal void Taken(double hp) { if (hp > 0) Defended(hp / (TakenPer * b.MaxHp), ResolveReason.Taken); }
    internal void Blocked() => Defended(BlockGain, ResolveReason.Blocked);
    public void Spend(double cost) => Add(-Math.Min(cost, Value), ResolveReason.Spent);
    internal void Drain(double x)
    {
        double d = Math.Min(x, Value);
        SpentInStorm += d;
        Add(-d, ResolveReason.Drained);
    }

    /// <summary>Each step: out of a fight it fades.</summary>
    internal void Tick(double dt)
    {
        if (!On || Value <= 0) return;
        if (b.Time - b.FightAt < FadeAfter) return;
        var p = b.Player;
        if (b.NearestHostile(p.X, p.Z, FightRadius) != null) return;
        Add(-FadeRate * dt, ResolveReason.Faded);
    }
}

public sealed partial class Battle
{
    /// <summary>The campaign (BattleSetup.Campaign: Journey.StartBattle's fights that are combat and not the arena): skills
    /// are set off by their press records and the warden runs on Resolve. Off (the arena, the harness's probes, a bare
    /// `new Battle`), the fight is what it always was: every skill keeps its self-firing rule.</summary>
    public bool Campaign { get; private set; }

    ResolveMeter? resolve;
    /// <summary>The warden's Resolve (Sim/Resolve.cs, the API at the top). Always there; On says if it counts.</summary>
    public ResolveMeter Resolve => resolve ??= new ResolveMeter(this);

    /// <summary>The last blow she gave or took (the battle's clock): Resolve fades only 3 s after it.</summary>
    internal double FightAt = double.NegativeInfinity;

    /// <summary>(M3) Her held swing's landed cuts, as seconds (each cut that struck a foe adds its own wait): what the story's
    /// stand clock reads to tell a fighter's plant from a stand (PackKit.Stand, Teeth.Director.StandSwing).</summary>
    public double SwingLanded { get; internal set; }
    /// <summary>(M3) How long the story's stand clock has counted her standing where she is (s; PackKit sets it each step;
    /// 0 with no clock): what a hand that has learnt the clock plants under (Pilot's feet).</summary>
    public double StoodFor { get; internal set; }
    /// <summary>(M3) The spot the story's stand clock measures her from (she has moved once she is its `standMoved` off;
    /// null with no clock running): what her feet's step must clear (Pilot's feet), not where the hands think she planted.</summary>
    public (double X, double Z)? StandSpot { get; internal set; }

    /// <summary>A builder's swing now being counted, and what it has struck (Firing.CastOnce; HitEnemy adds).</summary>
    internal WeaponInst? StruckBy;
    internal readonly HashSet<int> Struck = new();

    /// <summary>Where the press now firing aims (campaign only; Firing.Press sets it round the cast): the point, and the
    /// hover foe if one is under it. Null: the behaviors pick as they always did.</summary>
    internal (double X, double Z, Enemy? Foe)? CastAt;

    /// <summary>A press's Resolve cost, if Resolve counts (0 otherwise: a cost never blocks a skill with no resource).</summary>
    internal double CostOf(WeaponInst w) => Resolve.On ? (w.Press?.Resolve ?? 0) * RulePayMul(w) : 0;

    /// <summary>Her riposte is readied until (Rebuke's kindled press): the next blow that reaches her is blocked and answered.</summary>
    public double RiposteUntil = double.NegativeInfinity;
    /// <summary>Ripostes taken this fight (tests, the harness).</summary>
    public int Ripostes;

    /// <summary>The cursor's point each step (WorldScene; on a pad, her facing times the skill's reach): what a held skill
    /// aims at as it repeats.</summary>
    public void AimSkills(double x, double z) => SkillAim = (x, z);

    /// <summary>The aim a campaign press fires at (null: no record, no aim, or a self skill): hover, the foe nearest the
    /// aim point within 1.5 m of it and within reach of her, else the point clamped to reach; point, the point clamped.</summary>
    internal (double X, double Z, Enemy? Foe)? AimFor(WeaponInst w)
    {
        if (w.Press is not { } r || SkillAim is not { } a || r.Aim == PressAim.Self) return null;
        var p = Player;
        double reach = r.Reach ?? w.AimRange;
        if (r.Aim != PressAim.Point)
        {
            Enemy? best = null;
            double bd = HoverRadius;
            foreach (var e in HostilesInRadius(a.X, a.Z, HoverRadius + 2))
            {
                double d = Math.Max(0, Dist(e.X, e.Z, a.X, a.Z) - e.Radius);
                if (d > bd || Dist(e.X, e.Z, p.X, p.Z) > reach + e.Radius) continue;
                bd = d; best = e;
            }
            if (best != null) return (best.X, best.Z, best);
        }
        double dx = a.X - p.X, dz = a.Z - p.Z, l = Len(dx, dz);
        if (l > reach && l > 0) { dx *= reach / l; dz *= reach / l; }
        return (p.X + dx, p.Z + dz, null);
    }

    /// <summary>How near the aim point a foe must stand (its edge) to be the hover target.</summary>
    public const double HoverRadius = 1.5;

    /// <summary>A held skill ready again (Firing.TickPressed): it presses itself at the current aim.</summary>
    internal void PressHeld(WeaponInst w)
    {
        if (!Combat || !Player.Alive || FlareHold > 0) return;
        Firing.Press(this, w);
    }

    /// <summary>No press holds her feet longer than this (ARPG.md 3.1: "never rooted").</summary>
    public const double MaxPlant = 0.3;

    /// <summary>The cast pose (campaign): her walk at the record's pace for its cast time, and on a heavy commit (a plant
    /// in the record: Sunder's own heavy swing only, Groundbreaker and Iron Vow every time) her feet held for it, at most
    /// MaxPlant. Told as Ev.Cast for the view.</summary>
    internal void CastPose(WeaponInst w)
    {
        if (w.Press is not { } r) return;
        var p = Player;
        double walk = Math.Clamp(r.Walk ?? 0.7, 0, 1), t = Math.Max(0, r.CastTime ?? 0.35);
        double plant = Math.Clamp(r.Plant ?? 0, 0, MaxPlant);
        if (plant > 0 && Firing.HeavyEveryOf(this, w) > 0 && !w.WasOwnHeavy) plant = 0;
        if (w.Cast == CastMode.Channel) t = plant = 0;
        if (t > 0) { p.CastWalk = p.CastT > 0 ? Math.Min(p.CastWalk, walk) : walk; p.CastT = Math.Max(p.CastT, t); }
        p.PlantT = Math.Max(p.PlantT, plant);
        var at = CastAt ?? (SkillAim is { } s ? (s.X, s.Z, null) : (p.X, p.Z, null));
        Events.Emit(new Ev.Cast { Weapon = w.Id, Slot = w.Slot, Walk = walk, Time = t, Plant = plant, Heavy = w.WasOwnHeavy, X = at.X, Z = at.Z });
    }

    public const double RiposteFor = 2, FlareFor = 3, FlareDamage = 1.25, FlareArea = 1.3;

    /// <summary>A kindled skill's key (campaign): now fires it (its condition skipped; a spender with what she has, at
    /// least half its cost, its damage scaled by Value/cost and capped at 1, spending that); riposte readies one for 2 s;
    /// flare an aura's x1.3 radius and x1.25 damage for 3 s; command a summon's (the hook: the warden has none). The
    /// riposte, flare and command then wait their key's wait (the kindled record's Wait, else the skill's cooldown).</summary>
    internal bool KindledPress(WeaponInst w)
    {
        if (w.DisabledT > 0) return false;
        var mode = w.KindleKey;
        double keyWait = w.Press?.Kindled?.Wait ?? w.Def.Base.Cooldown ?? 1;
        switch (mode)
        {
            case KindlePress.Now:
            {
                if (w.Timer > 0 && !w.Relooking || BlowPending(w)) return false;
                double cost = CostOf(w), mul = 1;
                if (cost > 0)
                {
                    if (Resolve.Value < cost / 2) return false;
                    mul = Math.Min(1, Resolve.Value / cost);
                }
                var (aim0, fm) = (CastAt, w.FireMul);
                CastAt = AimFor(w);
                w.FireMul = fm * mul;
                bool fired;
                // (campaign: the heave lands on its clip's contact, at this press's strength: Sim/Contact.cs)
                try { fired = DeferBlow(w, mul) || Firing.CastNow(this, w); }
                finally { (CastAt, w.FireMul) = (aim0, fm); }
                if (!fired) return false;
                if (cost > 0) Resolve.Spend(Math.Min(cost, Resolve.Value));
                CastPose(w);
                Events.Emit(new Ev.KindlePress { Weapon = w.Id, Slot = w.Slot, Mode = mode, Until = Time });
                return true;
            }
            case KindlePress.Riposte:
                if (w.PressWait > 0) return false;
                RiposteUntil = Time + RiposteFor;
                w.PressWait = keyWait;
                Events.Emit(new Ev.KindlePress { Weapon = w.Id, Slot = w.Slot, Mode = mode, Until = RiposteUntil });
                return true;
            case KindlePress.Flare:
                if (w.PressWait > 0) return false;
                w.FlareUntil = Time + FlareFor;
                w.AuraMul = FlareDamage;
                w.AuraArea = FlareArea;
                w.PressWait = keyWait;
                // It goes off on its next steps if its condition holds: the flare is seen at once.
                if (w.Timer > 0.05) w.Timer = 0.05;
                Events.Emit(new Ev.KindlePress { Weapon = w.Id, Slot = w.Slot, Mode = mode, Until = w.FlareUntil });
                return true;
            case KindlePress.Command:
                if (w.PressWait > 0 || !CommandSummons(w)) return false;
                w.PressWait = keyWait;
                Events.Emit(new Ev.KindlePress { Weapon = w.Id, Slot = w.Slot, Mode = mode, Until = Time });
                return true;
        }
        return false;
    }

    /// <summary>A summon's key (kindled press "command"): the hook for the callings that raise things (the warden has
    /// none yet). False: nothing to command.</summary>
    internal bool CommandSummons(WeaponInst w) => false;

    /// <summary>A blow reaching her inside a readied riposte (HurtPlayer, after the dodge's checks): it is blocked (a block
    /// for Rebuke and Resolve) and Rebuke answers it at once. True when it took the blow.</summary>
    bool TryRiposte(double amount, School school, string source, Enemy? from)
    {
        if (Time > RiposteUntil) return false;
        RiposteUntil = double.NegativeInfinity;
        var p = Player;
        p.Iframes = Math.Max(p.Iframes, 0.25);
        Ripostes++;
        Events.Emit(new Ev.PlayerHit { X = p.X, Z = p.Z, Amount = 0, School = school, Source = source, Blocked = true });
        Fire(TriggerEvent.Block, new ProcCtx { X = p.X, Z = p.Z });
        RebukeAnswerNow();
        OnBlocked(amount, from);
        return true;
    }

    /// <summary>The taught build's form for a carried skill (taught_builds.json "cast"; campaign only). False: not
    /// carried, no record, or a form its record does not allow.</summary>
    public bool SetForm(string id, string cast) => WeaponById(id) is { } w && w.SetForm(cast);
}
