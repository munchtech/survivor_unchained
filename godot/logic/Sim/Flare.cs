using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/* The Flare (docs/design/CLASSES.md §3): the calling's ultimate on Q / right-click / pad Y.
 * Its meter fills fastest when she is in trouble and slowest from killing (§3.2), so a
 * half-full Flare is ready just as she is nearly dead; cast below a quarter of health it
 * mends and reaches further (§3.3), which makes every Flare a life-saver by design.
 *
 * Phase 1 is the logic: the meter, the window and the clutch, each Flare played as its
 * kind's plain form (a Strike's blows over its length, a Stand's pulses) with lamps.json's
 * numbers. Phase 2 stages each one over the shared beat (§3.5), reading the events. */
public sealed partial class Battle
{
    public const double FlareFull = 100;
    /// <summary>The press's freeze (§3.5): 0.22 s of real time at 8%; the view runs it, scaled by the setting.</summary>
    public const double FlareFreeze = 0.22, FlareFreezeRate = 0.08;
    /// <summary>The players' setting to shorten the freeze (0..1); the view multiplies FlareFreeze by it.</summary>
    public static double FlareFreezeScale = 1;
    /// <summary>The clutch: cast below this share of health, it mends 20% over a second and reaches 25% further.</summary>
    public const double FlareClutch = 0.25, FlareMend = 0.2, FlareReachClutch = 1.25;
    /// <summary>At the key pose, enemy missiles this close are burned away.</summary>
    public const double FlareBurn = 6;
    /// <summary>A Strike holds the controls at most this long, and is untouchable this long after its last blow.</summary>
    public const double StrikeMax = 1.2, StrikeAfter = 0.4, StandGrace = 1.5;

    /// <summary>The Flare carried this fight (null: none learned).</summary>
    public FlareDef? Flare;
    /// <summary>The meter, 0..100 a charge (Banked Flame holds two: 0..200).</summary>
    public double FlareMeter;
    /// <summary>The survivor's level, for the Flare's damage by day and in maps (the ember's by night).</summary>
    public int Level = 1;
    /// <summary>When the long night began (endless): every five minutes past it the Flare grows a rank.</summary>
    public double? EndlessFrom;

    /// <summary>The Flare while it plays.</summary>
    public double FlareT, FlareHold;
    double flareLen, flareReach, flarePower, flareMendT, flareUnseenAfter, flareKey;
    /// <summary>A Strike's blows, by time from the press (its beat, or even over its length).</summary>
    double[] flareAt = [];
    int flareBlow;
    bool flareClutch, flareReleased, flareKilledBoss;
    /// <summary>For the harness and the toll: casts, their times, clutch casts (falls the Flare kept from happening).</summary>
    public int FlareCasts, FlareClutches;
    /// <summary>For the harness: casts whose blows reached a boss.</summary>
    public int FlareCastsOnBoss;
    bool flareStruckBoss;
    public readonly List<double> FlareTimes = new();
    double emberAnsweredAt = -99;
    /// <summary>The horde can't spam it: each of its sources draws on a purse that refills at its rate a second.</summary>
    readonly double[] purse = new double[4], purseAt = new double[4];
    double Draw(int i, double want, double rate, double most)
    {
        purse[i] = Math.Min(most, purse[i] + (Time - purseAt[i]) * rate + (purseAt[i] == 0 && purse[i] == 0 ? most : 0));
        purseAt[i] = Math.Max(Time, 1e-9);
        double got = Math.Min(want, purse[i]);
        purse[i] -= got;
        return got;
    }
    /// <summary>The fill table, tuned by the harness (CLASSES.md §3.2).</summary>
    public const double FlareStartNight = 25;
    /// <summary>The Flare's power grows by this share for every lamp lit.</summary>
    public const double FlareLampGlow = 0.02;
    public const double FillHurt = 0.40, FillAnswer = 35, FillPerfect = 10, FillBlock = 6, FillBoss = 1.8,
        FillChampion = 2, FillChampionRate = 0.6, FillKill = 0.1, FillKillRate = 0.65;
    bool answeredTwice;

    public int FlareCharges => Lamp("flare.banked") ? (int)Lamps.Full("flare.banked", "charges", 2) : 1;
    public bool FlareReady => Flare != null && FlareMeter >= FlareFull;
    /// <summary>The Flare's rank in the long night (0 before it).</summary>
    public int FlareRank => EndlessFrom is { } t && Time > t ? (int)((Time - t) / 300) : 0;

    /// <summary>How fast it fills: Short Wick, Banked Flame's price, a Smothered map.</summary>
    double FlareFillMul()
    {
        double m = Rules.FlareFill;
        if (Boons.ContainsKey("short_wick")) m *= 1.35;
        // Banked Flame's price: the first charge at "slower", the second (the one held back) at "second".
        if (Lamp("flare.banked"))
        {
            double slower = Lamps.Full("flare.banked", "slower", 0.3);
            m *= 1 - (FlareMeter >= FlareFull ? Lamps.Full("flare.banked", "second", slower) : slower);
        }
        return m;
    }

    /// <summary>The meter rises (why: what filled it, for the harness's tally).</summary>
    public void FillFlare(double amount, string why)
    {
        if (Flare == null || amount <= 0 || !Player.Alive) return;
        double cap = FlareFull * FlareCharges;
        double was = FlareMeter;
        FlareMeter = Math.Min(cap, FlareMeter + amount * FlareFillMul());
        FlareFills[why] = FlareFills.GetValueOrDefault(why) + (FlareMeter - was);
        if (Math.Floor(was / FlareFull) < Math.Floor(FlareMeter / FlareFull))
            Events.Emit(new Ev.Flare { Phase = FlarePhase.Ready, Id = Flare.Id, X = Player.X, Z = Player.Z });
    }

    public readonly Dictionary<string, double> FlareFills = new();

    /* ------------------------------------------------------- how it fills -- */

    /// <summary>A blow reached her: +0.55 for each 1% of health lost, doubled below a third; the first drop
    /// below a quarter, the ember answers (+35, once in 45 s).</summary>
    void FlareOnHurt(double dmg, double hpBefore, string source)
    {
        if (Flare == null) return;
        // Always Bleeding's own bleeding never counts (§3.2).
        if (source == "always bleeding") return;
        var p = Player;
        double pct = dmg / MaxHp * 100;
        double fill = FillHurt * pct * (p.Hp < MaxHp / 3 ? 2 : 1);
        if (Lamp("flare.hurt_fill")) fill *= 1 + Lamps.Full("flare.hurt_fill", "more", 0.2);
        FillFlare(fill, "hurt");
        if (hpBefore >= MaxHp * FlareClutch && p.Hp < MaxHp * FlareClutch && p.Hp > 0)
        {
            if (Boons.ContainsKey("ember_answers_twice") && !answeredTwice)
            {
                answeredTwice = true;
                FillFlare(Math.Max(0, FlareFull - FlareMeter % FlareFull) / FlareFillMul(), "answers");
            }
            else if (Time - emberAnsweredAt >= 45)
            {
                emberAnsweredAt = Time;
                FillFlare(FillAnswer, "answers");
            }
        }
    }

    void FlareOnPerfect() =>
        FillFlare(FillPerfect * (Lamp("flare.perfect_fill") ? 1 + Lamps.Full("flare.perfect_fill", "more", 0.5) : 1), "perfect");

    void FlareOnBlock(Enemy? from)
    {
        if (from is { } e && (e.Elite || e.Boss)) FillFlare(FillBlock, "block");
    }

    /// <summary>Damage she dealt: a boss +1.8 for each 1% of its health (the Flare's own never refills it).</summary>
    void FlareOnDealt(Enemy e, double dealt, string by)
    {
        if (Flare == null || by == "flare" || dealt <= 0 || e.MaxHp <= 0) return;
        if (e.Boss) FillFlare(FillBoss * dealt / e.MaxHp * 100, "boss");
    }

    /// <summary>A kill: a champion's +2, at most +0.6 a second; the horde's +0.1 each, at most +0.65 a second; a bleed's kill with Blood for the Flare.</summary>
    void FlareOnKill(Enemy e, bool byBleed)
    {
        if (Flare == null) return;
        if (e.Boss) return;
        if (e.Elite) { FillFlare(Draw(0, FillChampion, FillChampionRate, FillChampion), "champion"); return; }
        FillFlare(Draw(1, FillKill, FillKillRate, FillKillRate), "kills");
        if (byBleed && Lamp("flare.bleed_kill")) FillFlare(Draw(2, Lamps.Full("flare.bleed_kill", "fill", 0.2), FillKillRate, FillKillRate), "bleed");
    }

    /// <summary>A spell of hers struck this many at once (Kindling: three or more fill it a little).</summary>
    public void FlareOnSpell(int struck)
    {
        if (struck >= (int)Lamps.Full("flare.spell_fill", "count", 3) && Lamp("flare.spell_fill"))
            FillFlare(Draw(3, Lamps.Full("flare.spell_fill", "fill", 0.5), FillKillRate, 1), "spells");
    }

    /* ----------------------------------------------------------- the cast -- */

    /// <summary>Q / right-click: the Flare, when the meter is full.</summary>
    public bool UseFlare(double dirX, double dirZ)
    {
        var p = Player;
        if (!Combat || !p.Alive || Flare is not { } f || FlareMeter < FlareFull || FlareT > 0) return false;
        bool fromFullBank = FlareCharges > 1 && FlareMeter >= FlareFull * FlareCharges;
        FlareMeter -= FlareFull;
        FlareCasts++;
        FlareTimes.Add(Time);
        double ax = dirX, az = dirZ;
        if (Aim is { } aim) { ax = aim.X - p.X; az = aim.Z - p.Z; }
        if (Len(ax, az) < 0.1) { ax = Math.Sin(p.Facing); az = Math.Cos(p.Facing); }
        double angle = Math.Atan2(az, ax);
        flareClutch = p.Hp < MaxHp * FlareClutch;
        int rank = FlareRank;
        // Its size grows with the long night until it fills the screen, then stops; its damage has no cap (§5).
        flareReach = f.Radius * (flareClutch ? FlareReachClutch : 1) * (Boons.ContainsKey("bright_hour") ? 1.4 : 1) * Math.Min(2.5, 1 + 0.1 * rank);
        // The board's lamps feed the skills by their tags, so the Flare grows with the board too, or a full
        // board's Flare fell to a tenth of a boss's damage (the harness, 12 October).
        flarePower = Content.Lamps.FlarePower(f, EmberOn ? EmberLevel : Level) * (1 + 0.25 * rank) * (1 + FlareLampGlow * Lamps.Lit);
        // Banked Flame's gift beyond the second charge: every Flare "harder", one spent from a full bank "held" more.
        if (Lamp("flare.banked"))
            flarePower *= 1 + Lamps.Full("flare.banked", "harder", 0) + (fromFullBank ? Lamps.Full("flare.banked", "held", 0) : 0);
        bool stand = f.Kind == FlareKind.Stand;
        flareAt = FlareSchedule(f);
        // A staged Strike runs to its last blow and a breath after (the Fourth Toll), never past the 1.2 s.
        flareLen = stand ? f.Length : Math.Min(StrikeMax, Math.Max(f.Length, f.Beat.ContainsKey("first") && flareAt.Length > 0 ? flareAt[^1] + 0.1 : 0));
        FlareT = flareLen;
        flareBlow = 0;
        flareStruckBoss = false;
        flareKilledBoss = false;
        flareReleased = false;
        flareKey = f.BeatAt("key", flareAt.Length > 0 ? flareAt[0] : 0);
        // A Strike holds the controls and is untouchable through it and a breath after; a Stand gives
        // them back at once, untouchable for its first moments.
        FlareHold = stand ? 0 : flareLen;
        p.Iframes = Math.Max(p.Iframes, stand ? StandGrace : flareLen + StrikeAfter);
        if (!stand) { p.DashT = 0; p.Vx = p.Vz = 0; }
        Events.Emit(new Ev.Flare { Phase = FlarePhase.Press, Id = f.Id, X = p.X, Z = p.Z, Radius = flareReach, Angle = angle, Clutch = flareClutch, Stand = stand });
        // The flare burns the air: what was loosed at her close by is gone.
        foreach (var pr in Projectiles.Items)
            if (pr.Alive && pr.Owner == Side.Enemy && Dist(pr.X, pr.Z, p.X, p.Z) < FlareBurn) ExpireProjectile(pr);
        // A boss's channel breaks and it staggers a little; never stunned outright.
        ForEachHostileInRadius(p.X, p.Z, flareReach, (e, _) => { if (e.Boss || e.Elite) { Interrupt(e); AddStagger(e, e.Boss ? 15 : 30); } });
        if (flareClutch)
        {
            FlareClutches++;
            if (Rules.FlareMends) flareMendT = 1;
        }
        // The hearth's lamps for a Flare at the edge (below a third).
        if (p.Hp < MaxHp * Lamps.Full("flare.low_barrier", "below", 0.3333) && Lamp("flare.low_barrier"))
            Barrier(MaxHp * Lamps.Full("flare.low_barrier", "barrier", 0.3), 6);
        if (p.Hp < MaxHp * Lamps.Full("flare.low_mirrors", "below", 0.3333) && Lamp("flare.low_mirrors"))
            for (int i = 0; i < (int)Lamps.Full("flare.low_mirrors", "count", 2); i++)
                Reflect(p.X + (i == 0 ? -1.2 : 1.2), p.Z, 5, angle);
        flareUnseenAfter = p.Hp < MaxHp * Lamps.Full("flare.low_unseen", "below", 0.3333) && Lamp("flare.low_unseen")
            ? Lamps.Full("flare.low_unseen", "seconds", 2) : 0;
        FlareStagedPress(f);
        if (stand && f.Blows > 0) FlareBlow();
        return true;
    }

    /// <summary>One blow (a Strike's) or one pulse (a Stand's): the four staged Flares by their briefs (FlareStaged.cs),
    /// the rest in their kind's plain form, everything in reach, until phase 6 stages them.</summary>
    void FlareBlow()
    {
        var f = Flare!;
        flareBlow++;
        bool last = f.Kind == FlareKind.Strike && flareBlow == flareAt.Length;
        var was = credit;
        credit = "flare";
        switch (f.Staged ? f.Id : "")
        {
            case "bell_of_the_morning": BellToll(f, last); break;
            case "burns_twice": BurnsTwiceBlow(f, last); break;
            case "the_roads_toll": TollCut(f, last); break;
            default:
                var p = Player;
                ForEachHostileInRadius(p.X, p.Z, flareReach, (e, d) => FlareHit(e, 1, f.School, 1.2, p.X, p.Z));
                FlareBlowEvent(f, f.Kind == FlareKind.Stand ? "pulse" : "blow", last, p.X, p.Z, null, flareReach);
                break;
        }
        credit = was;
    }

    void TickFlare(double dt)
    {
        var p = Player;
        TickVenom();
        if (flareMendT > 0)
        {
            double step = Math.Min(dt, flareMendT);
            flareMendT -= step;
            double more = Lamp("flare.low_mend") ? 1 + Lamps.Full("flare.low_mend", "more", 0.5) : 1;
            HealPlayer(MaxHp * FlareMend * more * step, "flare", true);
        }
        if (FlareT <= 0 || Flare is not { } f) return;
        if (f.Kind == FlareKind.Stand && Time - lastBossHit < 1) StandOnBossSeconds += Math.Min(dt, FlareT);
        FlareT -= dt;
        FlareHold = Math.Max(0, FlareHold - dt);
        if (FlareHold > 0) { p.Vx = p.Vz = 0; }
        double elapsed = flareLen - FlareT;
        // The key pose ends: time returns and the camera eases back (§3.5, the release).
        if (!flareReleased && elapsed >= flareKey - 1e-9)
        {
            flareReleased = true;
            Events.Emit(new Ev.Flare { Phase = FlarePhase.Release, Id = f.Id, X = p.X, Z = p.Z, Radius = flareReach, Clutch = flareClutch, Stand = f.Kind == FlareKind.Stand });
        }
        if (f.Kind == FlareKind.Strike)
        {
            while (flareBlow < flareAt.Length && elapsed >= flareAt[flareBlow] - 1e-9) FlareBlow();
        }
        else
        {
            if (f.Blows > 0)
            {
                double every = 1.0 / f.Blows;
                while (elapsed >= every * flareBlow && FlareT > 0) FlareBlow();
            }
            if (f.Guard == "mend") HealPlayer(MaxHp * f.GuardValue * dt, "flare", true);
            FlareStagedTick(f, dt);
        }
        if (FlareT <= 0)
        {
            FlareT = 0;
            FlareHold = 0;
            if (FlareMod("toll.gone") && f.Id == "the_roads_toll") flareUnseenAfter = Math.Max(flareUnseenAfter, f.Arg("gone", 3));
            if (flareUnseenAfter > 0) p.InvisibleT = Math.Max(p.InvisibleT, flareUnseenAfter);
            Events.Emit(new Ev.Flare { Phase = FlarePhase.End, Id = f.Id, X = p.X, Z = p.Z, Clutch = flareClutch, Stand = f.Kind == FlareKind.Stand });
        }
    }

    /// <summary>A Stand that guards: blows cut while it holds.</summary>
    double FlareGuard(double dmg) =>
        FlareT > 0 && Flare is { Kind: FlareKind.Stand, Guard: "cut" } f ? dmg * (1 - f.GuardValue) : dmg;
}
