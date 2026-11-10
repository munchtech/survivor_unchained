using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Pilots;

/// <summary>A plain-minded survivor's hands (the tests' ArenaPlay bot, kept
/// as it was so the numbers mean the same): give ground when pressed, go to
/// the fight or the ember lying about when it is quiet, keep off the arena's
/// edge, dash out of a crush, use the art on a crowd, drink when low.</summary>
public static class Pilot
{
    /// <summary>How far its weapons reach, the median of them: a build of blades
    /// and rings fights close, one of bolts and arrows from further off.</summary>
    public static double Reach(Battle b)
    {
        if (b.Weapons.Count == 0) return 10;
        var r = b.Weapons.Select(w => w.Behavior switch
        {
            Content.WeaponBehavior.Slash or Content.WeaponBehavior.Palm => (w.Num(s => s.Reach) ?? 2.6) * Math.Sqrt(b.Stats.Get(Stat.Area)),
            Content.WeaponBehavior.Nova => w.Num(s => s.Radius) ?? 3.5,
            Content.WeaponBehavior.Orbit => (w.Num(s => s.OrbitRadius) ?? 2) + 0.5,
            Content.WeaponBehavior.Zone when !w.Flag(s => s.AtTarget) => w.Num(s => s.Radius) ?? 3,
            _ => w.Num(s => s.Range) ?? 12,
        }).OrderBy(x => x).ToList();
        return r[(r.Count - 1) / 2];
    }

    /// <param name="onward">On a map: where the way goes on. Resting packs are left to rest, what
    /// lies about is picked up, and with nothing roused near, the hands walk on.</param>
    /// <param name="goal">A story night's stage: where it wants her (a fire to light, a foe to find). With no
    /// crush round her, the hands go there.</param>
    /// <param name="strikes">Read the crowd's own marked circles too (a story night's way in: its named foes'
    /// slams are its lessons, and a relaxed player steps out of a brute's marked circle as of a boss's).</param>
    /// <param name="first">The boss met for the first time (BossSense.Meeting): its new moves answered less.</param>
    public static (double X, double Z) Steer(Battle b, bool deft = false, ArenaBoss? boss = null, (double X, double Z)? onward = null, (double X, double Z)? goal = null, bool naive = false, bool strikes = false, BossSense.Meeting? first = null)
    {
        var p = b.Player;
        double mx, mz;
        // Close fighters stand in the press and give ground only to a crush; the wall gives none.
        bool wall = Wall(b);
        double reach = Reach(b);
        bool close = wall || reach < 4.5;
        var press = b.HostilesInRadius(p.X, p.Z, close ? 2.0 : 3.4);
        int crowded = close ? 4 : 2;
        double engage = wall ? 1.8 : close ? Math.Max(1.6, reach * 0.7) : 6;
        Enemy? nearest = null;
        double nd = double.MaxValue;
        foreach (var e in b.Enemies.Items)
        {
            if (!e.Alive || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying) continue;
            if (onward != null && (e.Wake > 0 && !e.Roused || e.State == EnemyState.Burrowed)) continue;
            double d = (e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z);
            if (d < nd) { nd = d; nearest = e; }
        }
        Pickup? stone = null;
        double sd = 144;
        foreach (var k in b.Pickups.Items)
        {
            if (!k.Alive || !(k.Kind == PickupKind.Ember || onward != null && k.Kind is PickupKind.Item or PickupKind.Material or PickupKind.Gold or PickupKind.Chest)) continue;
            if (Leaves != null && Leaves(k)) continue;
            double d = (k.X - p.X) * (k.X - p.X) + (k.Z - p.Z) * (k.Z - p.Z);
            if (d < sd) { sd = d; stone = k; }
        }
        double near = nearest == null ? double.MaxValue : Math.Sqrt(nd);
        // On a map, one that has wandered far off is not followed into the trees.
        if (onward != null && near > 22) { nearest = null; near = double.MaxValue; }
        // A champion or the boss at arm's length: give ground round it, as anyone does who
        // has been hit by one twice (a ranged build kites it; a blade fights it only with
        // the health to). Without this the bot stood in a boss's combo and fell.
        Enemy? big = null;
        double bigD = close ? 2.2 : 4.5;
        foreach (var e in b.HostilesInRadius(p.X, p.Z, bigD))
            if ((e.Boss || e.Elite) && (!close || p.Hp < b.MaxHp * 0.5)) { big = e; break; }
        // (M3, the campaign: a fighter's feet. With a foe in her reach she plants and swings, then takes one short step,
        // the side changing each time, and plants again: the owner's "running in circles" was the strafe below, a full
        // turn round the foe every four seconds and never a stand. The plant is kept under the story's stand clock.)
        var meter = b.Campaign ? State(b) : null;
        var feet = StepsAndStands ? meter : null;
        bool inReach = nearest != null && near - (b.Campaign ? nearest.Radius : 0) <= engage;
        bool plant = false;
        if (feet != null && !wall && (inReach || press.Count >= crowded)) plant = feet.Plant(b);
        string took;
        if (big != null)
        {
            double cx = big.X - p.X, cz = big.Z - p.Z;
            double cl = Math.Max(0.01, Math.Sqrt(cx * cx + cz * cz));
            mx = -cx / cl * 0.8 - cz / cl * 0.6; mz = -cz / cl * 0.8 + cx / cl * 0.6;
            took = "big";
        }
        else if (press.Count >= crowded && !wall)
        {
            double cx = press.Average(e => e.X) - p.X, cz = press.Average(e => e.Z) - p.Z;
            double cl = Math.Max(0.01, Math.Sqrt(cx * cx + cz * cz));
            // Away and round: a quarter turn off straight back.
            mx = -cx / cl * 0.7 - cz / cl * 0.7; mz = -cz / cl * 0.7 + cx / cl * 0.7;
            took = "crush";
            // (M3, the campaign) With the health to, she holds her ground in the crush and swings, and gives it a step at
            // a time, to either hand; under CrushRun of her health she runs from it as before.
            if (feet != null && p.Hp >= b.MaxHp * CrushRun)
            {
                if (plant) { mx = 0; mz = 0; took = "crush-plant"; }
                else { mx = -cx / cl * 0.7 - cz / cl * 0.7 * feet.Side; mz = -cz / cl * 0.7 + cx / cl * 0.7 * feet.Side; took = "crush-step"; }
            }
        }
        // The stage's goal when nothing is at her throat: a player with a thing to do does it, and lets
        // the weapons fire on the way (a fire takes two seconds of standing to light).
        else if (goal is var (gx, gz))
        {
            if (Dist(gx, gz, p.X, p.Z) > 1.2) { mx = gx - p.X; mz = gz - p.Z; } else { mx = 0; mz = 0; }
            took = "goal";
        }
        else if (stone != null && near > engage + 1) { mx = stone.X - p.X; mz = stone.Z - p.Z; took = "stone"; }
        // (M3: in the campaign the engage distance is to its edge: a boss's girth is not walked into, where his touch hurts;
        // the arena keeps the center, byte-same)
        else if (nearest != null && !inReach) { mx = nearest.X - p.X; mz = nearest.Z - p.Z; took = "close"; }
        // In the press the wall stands: still, where Planted and The Wall Holds pay and every blow is a chance at a stone.
        else if (nearest != null && wall) { mx = 0; mz = 0; took = "wall"; }
        else if (nearest != null && feet != null)
        {
            if (plant) { mx = 0; mz = 0; took = "plant"; }
            else
            {
                // The step: across her foe, a quarter turn; the other hand where this one is walled.
                mx = -(nearest.Z - p.Z) * feet.Side; mz = (nearest.X - p.X) * feet.Side;
                double sl = Math.Max(0.01, Math.Sqrt(mx * mx + mz * mz));
                if (b.Collision.Blocked(p.X + mx / sl * 0.6, p.Z + mz / sl * 0.6, p.Radius)) { feet.Side = -feet.Side; mx = -mx; mz = -mz; }
                took = "step";
            }
        }
        else if (nearest != null) { mx = -(nearest.Z - p.Z); mz = nearest.X - p.X; took = "strafe"; }
        else if (onward is var (ox, oz)) { mx = ox - p.X; mz = oz - p.Z; took = "onward"; }
        else { mx = -p.X; mz = -p.Z; took = "home"; }
        double far = Math.Sqrt(p.X * p.X + p.Z * p.Z);
        if (far > 60 && onward == null && goal == null) { mx = mx * 0.3 - p.X / far; mz = mz * 0.3 - p.Z / far; }
        if (deft) Deft(b, press.Count >= 2 || stone != null, ref mx, ref mz);
        if (b.Collision.Blocked(p.X + mx * 0.1, p.Z + mz * 0.1, p.Radius))
        {
            // On a story night's way: the nearest turn that is clear, either hand, or straight on and
            // let the wall slide her (a quarter turn left, always, pressed her into a wall's corner).
            if (goal != null) (mx, mz) = Clearest(b, mx, mz);
            else (mx, mz) = (-mz, mx);
        }
        // The boss's own fight, read last: it overrules the crowd.
        // Naive hands read only a boss's marks: the way in's (a drive's lane) they walk into, as a first-timer does.
        double hx = mx, hz = mz;
        if (ReadsBosses && (boss != null || (b.Blows.Count > 0 || strikes && (b.EnemyStrikes().Any() || BossSense.Underfoot(b))) && !naive)) Boss(b, boss, deft, ref mx, ref mz, goal, strikes && !naive, first);
        // The kit's pull (Sim/Tells.cs), seen: out of its reach, straight away from its heart (its drag is not on the ground's marks).
        lastDeft = deft;
        if (!naive && b.ActiveTells.Count > 0) OutOfPull(b, deft, ref mx, ref mz);
        if (!naive && b.ActiveTells.Count > 0) OutOfClosing(b, deft, ref mx, ref mz);
        if (Debug) Console.Error.WriteLine($"   PILOT near {(nearest == null ? "-" : $"{nearest.Def.Id} {near:0.0}")} big {big != null} press {press.Count} goal {goal} stone {stone != null} hands ({hx:0.00},{hz:0.00}) after boss ({mx:0.00},{mz:0.00})");
        double ml = Math.Sqrt(mx * mx + mz * mz);
        if (ml > 1e-6) { mx /= ml; mz /= ml; }
        meter?.Measure(b, nearest, inReach, ml > 1e-6, took);
        return (mx, mz);
    }

    /// <summary>(M3) The fighter's feet, in the campaign's fights (the arena's hands circle as they did, byte-same).
    /// Off: the strafe everywhere, for the numbers before (the harness's --strafe).</summary>
    public static bool StepsAndStands = true;
    /// <summary>The plant, as a share of the story's stand clock (world_tiers.json `stand.standFor`; PlantFor s with no clock
    /// on). The step ends once it has carried her StepClear x the clock's `standMoved` from where she was planted (StepWide m
    /// with no clock), or after StepMax s (walled, held, slowed). A player who has learnt how long she may stand: the clock
    /// sees a stand only when something holds her past the plant.</summary>
    public static double PlantShare = 0.65, PlantFor = 0.7, StepClear = 1.6, StepWide = 1.0, StepMax = 0.45;
    /// <summary>The longest plant under a clock that counts (StandSwing): a chain and a breath, whatever the count says.</summary>
    public static double PlantMost = 4;
    /// <summary>Under this share of her health a crush is run from (the arena's away-and-round), not stood in.</summary>
    public static double CrushRun = 0.5;

    static readonly System.Runtime.CompilerServices.ConditionalWeakTable<Battle, Feet> feetOf = new();
    static Feet State(Battle b) => feetOf.GetOrCreateValue(b);
    /// <summary>(M3) What her feet did in this battle's fights (the campaign under the Pilot or the Human; zeros elsewhere):
    /// the number for "does she circle", read by the harness's reports and the game's --clip trace.</summary>
    public static FeetMeter Meter(Battle b) => State(b).M;

    public sealed class FeetMeter
    {
        /// <summary>Seconds with a foe in her reach; of them, seconds her feet were still; the angle she swept round that
        /// foe (radians, summed without sign, and with it); plants begun; seconds by the rule that moved her.</summary>
        public double InReach, Stood, AbsTurn, NetTurn;
        public int Plants;
        /// <summary>The story stand clock's charges on her (set by the harness at a run's end): what the plant is kept under.</summary>
        public int StandCharges;
        /// <summary>The rules that moved her over the last steps, newest last (a trace).</summary>
        public string Last = "";
        public readonly System.Collections.Generic.Dictionary<string, double> By = new();
        /// <summary>Full turns round her foe each ten seconds in reach (the strafe: 2.2-2.3).</summary>
        public double TurnsPer10 => InReach > 0 ? AbsTurn / (2 * Math.PI) / InReach * 10 : 0;
        public double NetPer10 => InReach > 0 ? NetTurn / (2 * Math.PI) / InReach * 10 : 0;
        public double StoodShare => InReach > 0 ? Stood / InReach : 0;
        public override string ToString() => $"in reach {InReach:0.0} s, stood {StoodShare * 100:0}%, {TurnsPer10:0.00} turns per 10 s (net {NetPer10:0.00}), {Plants} plants; "
            + string.Join(" ", By.OrderByDescending(kv => kv.Value).Select(kv => $"{kv.Key} {kv.Value:0.0}"));
    }

    sealed class Feet
    {
        public int Side = 1;
        public readonly FeetMeter M = new();
        double seen = -9, plantUntil, stepUntil, plantX, plantZ, stepWide, lastT = -1, lastA;
        bool planted;
        Enemy? lastFoe;

        /// <summary>Whether she is planted now. Come into reach: a plant; the plant over: a step; the step over: the
        /// other hand next, and a plant. Out of reach for half a second (the foe fell, she walked on) begins again.</summary>
        public bool Plant(Battle b)
        {
            double now = b.Time;
            var p = b.Player;
            bool fresh = now - seen > 0.5;
            // The step is over once it has carried her clear of where she stood; one that has not in StepMax s (walled,
            // held by a heave, slowed) is tried to the other hand, never stood through: the clock would see the stand.
            bool clear = Math.Sqrt((p.X - plantX) * (p.X - plantX) + (p.Z - plantZ) * (p.Z - plantZ)) >= stepWide;
            var clock = b.StoryStand is { Stand: true } d ? d : null;
            // (the clock that knows a fighter's plant, StandSwing: she plants while it has counted her standing under
            // PlantShare of its StandFor, a chain's length while her cuts land, and at most PlantMost s)
            bool counted = clock is { StandSwing: > 0 };
            if (counted && !fresh && planted && (b.StoodFor >= clock!.StandFor * PlantShare || now >= plantUntil))
                { planted = false; plantUntil = now; stepUntil = now + StepMax; }
            if (!fresh && !planted && now >= stepUntil && !clear) { Side = -Side; stepUntil = now + StepMax; }
            else if (fresh || !planted && now >= plantUntil && clear)
            {
                if (!fresh) Side = -Side;
                plantUntil = now + (counted ? PlantMost : clock != null ? clock.StandFor * PlantShare : PlantFor);
                stepUntil = plantUntil + StepMax;
                stepWide = clock != null ? clock.StandMoved * StepClear : StepWide;
                plantX = p.X; plantZ = p.Z;
                planted = true;
                M.Plants++;
            }
            if (!counted && now >= plantUntil) planted = false;
            seen = now;
            return planted;
        }

        public void Measure(Battle b, Enemy? foe, bool inReach, bool moved, string took)
        {
            double now = b.Time, dt = lastT < 0 ? 0 : Math.Clamp(now - lastT, 0, 0.1);
            lastT = now;
            M.By[took] = M.By.GetValueOrDefault(took) + dt;
            if (!M.Last.EndsWith(took)) M.Last = (M.Last.Length > 60 ? M.Last[^60..] : M.Last) + ">" + took;
            if (foe == null || !inReach) { lastFoe = null; return; }
            var p = b.Player;
            double a = Math.Atan2(p.Z - foe.Z, p.X - foe.X);
            M.InReach += dt;
            if (!moved) M.Stood += dt;
            if (lastFoe == foe)
            {
                double da = Math.Atan2(Math.Sin(a - lastA), Math.Cos(a - lastA));
                M.AbsTurn += Math.Abs(da); M.NetTurn += da;
            }
            lastFoe = foe; lastA = a;
        }
    }

    /// <summary>The hands that are not the feet: a dash out of a crush, the art
    /// on a crowd, a draught when low.</summary>
    /// <returns>Whether a draught was drunk.</returns>
    /// <param name="drinks">Off: the hands never drink (the game's --no-drink, a draught's lesson waiting).</param>
    /// <param name="rooted">Read the kit's telegraphs (Sim/Tells.cs): rooted in a marked blow, dash out; dragged into a
    /// pull's heart past walking out, dash out. A caller with hands that did not see it passes false.</param>
    public static bool Act(Battle b, Journey j, double mx, double mz, SurvivorUnchained.Play.Bosses.ArenaBoss? boss = null, bool lunges = true, bool aimsFlare = true, bool rooted = true, bool crush = true, bool presses = false, PressHands? hands = null, bool drinks = true)
    {
        var p = b.Player;
        if (rooted && b.ActiveTells.Count > 0) KitDash(b, mx, mz);
        if (rooted && b.ActiveTells.Count > 0) ClosingDash(b, presses || hands is { GripOnly: false });
        // The campaign's grips (ARPG.md 3.1): anyone holds the swing on what is near; a pressing hand presses the rest.
        // (M3: a hand on the one press plan, data/content/press_plan.json, grips and presses through it)
        if (hands != null) PressPlan.Run(b, hands, rooted);
        else
        {
            if (b.Campaign) Grips(b);
            if (presses) PressSkills(b, rooted);
        }
        // A champion winding up a lunge close by: dash across its line, as anyone with a dash learns to.
        // (Not a boss: its blows are marked on the ground, and Boss reads them by their shape.)
        if (p.DashCharges > 0 && lunges)
            foreach (var e in b.HostilesInRadius(p.X, p.Z, 7))
                if (e.Elite && (!e.Boss || !ReadsBosses) && e.State == EnemyState.Windup)
                {
                    double dx = p.X - e.X, dz = p.Z - e.Z, l = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz));
                    b.Dash(-dz / l, dx / l);
                    break;
                }
        // Out of a crush (the wall stays in it: the crush is what it came for).
        if (crush && p.DashCharges > 0 && !Wall(b) && b.HostilesInRadius(p.X, p.Z, 2.2).Count >= 3) b.Dash(mx, mz);
        // The Flare: a boss within ten metres, a crowd of eight within its reach, or health below a quarter;
        // and nobody sits on a full meter: after eight seconds ready, four within its reach will do.
        // (A crowd of eight within six metres kept a kiting caster's meter full for minutes.)
        if (b.FlareReady && UsesFlare)
        {
            double reach = Math.Max(6, b.Flare?.Radius ?? 6);
            int near = b.HostilesInRadius(p.X, p.Z, reach).Count;
            bool low = p.Hp < b.MaxHp * 0.25;
            // A boss in its phase transition can't be hurt (TakenMul 0): spare the Flare unless health is low.
            bool bossNear = (AimsFlare && aimsFlare || low) && b.HostilesInRadius(p.X, p.Z, 10).Any(e => e.Boss && (low || e.TakenMul > 0));
            // A phase-aware banker (judge 3: it beat firing both at once for every calling; --phaseaware 0 for the old hands): with two charges, a phase the Flare has already cut by a
            // quarter keeps the next for the next phase (a cut stops at half; the second Flare's would be wasted).
            if (PhaseAware && bossNear && !low && b.FlareCharges > 1 && boss is { } bs && bs.FlareCut >= 0.25) bossNear = false;
            // Banked Flame holds two: a player who lit it keeps one for a boss or the edge, and spends on
            // the crowd only from a full bank (before it learned, the pilot paid the price without the gift).
            bool keeps = Banks && b.FlareCharges > 1 && b.FlareMeter < Battle.FlareFull * b.FlareCharges;
            if (keeps) readyIn = null;
            else if (readyIn != b) { readyIn = b; readyAt = b.Time; }
            // A kiting caster with a small Stand (the Drowned Moon, 5 m) rarely has four inside it: after
            // fifteen seconds, four within ten metres will do (the Stand follows her in).
            if (low || bossNear || (!keeps && (near >= 8 || (near >= 4 && b.Time - readyAt >= 8) ||
                (b.Time - readyAt >= 15 && b.HostilesInRadius(p.X, p.Z, 10).Count >= 4))))
            {
                // A line Flare (the Long Cut, One Arrow) is aimed, as a player aims it: down the line through the most,
                // or at the boss when one is near. The aim is the pointer's only for the press.
                var aimWas = b.Aim;
                if (b.Flare is { } fl && fl.Args.ContainsKey("line") && LineAim(b, fl.Arg("line", 24), fl.Arg("lineWidth", 1.5)) is { } la) b.Aim = la;
                b.UseFlare(mx, mz);
                b.Aim = aimWas;
                readyIn = null;
            }
        }
        else readyIn = null;
        if (!drinks || p.Hp >= b.MaxHp * 0.33) return false;
        double before = p.Hp;
        j.Quaff(b);
        return p.Hp > before;
    }

    /// <summary>What a player who knows the fight does over the plain hands'
    /// choice, the worst danger first (from the balance lab's deft bot, which
    /// the tests' ArenaPlay shares): off the line of a marked lunge, dashing
    /// across it if late; out from under a lobbed pot and off burning ground;
    /// and, with nothing pressing and no ember near, in on the nearest thrower.</summary>
    public static void Deft(Battle b, bool busy, ref double mx, ref double mz)
    {
        var p = b.Player;
        foreach (var e in b.Enemies.Living())
        {
            if (e.State != EnemyState.Windup || e.Disposition != Disposition.Hostile) continue;
            var lunge = e.Def.Charge ?? e.Def.Lunge;
            if (lunge == null) continue;
            double reach = lunge.Speed * lunge.Time + e.Radius + 1;
            double rx = p.X - e.X, rz = p.Z - e.Z;
            double along = rx * e.LungeX + rz * e.LungeZ;
            double across = rx * -e.LungeZ + rz * e.LungeX;
            if (along < -1 || along > reach || Math.Abs(across) > e.Radius * 1.1 + p.Radius + 0.9) continue;
            double side = across >= 0 ? 1 : -1;
            mx = -e.LungeZ * side; mz = e.LungeX * side;
            if (e.StateT < 0.3 && p.DashCharges > 0) b.Dash(mx, mz);
            return;
        }
        // A crossbow knelt and aiming down its fixed line: off the line, as from a lunge.
        foreach (var e in b.Enemies.Living())
        {
            if (e.State != EnemyState.Casting || e.Cast != CastKind.Aim || e.Disposition != Disposition.Hostile) continue;
            double rx = p.X - e.X, rz = p.Z - e.Z;
            double along = rx * e.LungeX + rz * e.LungeZ;
            double across = rx * -e.LungeZ + rz * e.LungeX;
            if (along < 0 || along > e.AimReach + 3 || Math.Abs(across) > 1.2 + along * 0.2) continue;
            double side = across >= 0 ? 1 : -1;
            mx = -e.LungeZ * side; mz = e.LungeX * side;
            return;
        }
        foreach (var pr in b.Projectiles.Living())
        {
            if (!pr.Lob || pr.Owner != Side.Enemy) continue;
            double d = Dist(pr.LandX, pr.LandZ, p.X, p.Z);
            if (d < 2.2) { mx = (p.X - pr.LandX) / Math.Max(0.1, d); mz = (p.Z - pr.LandZ) / Math.Max(0.1, d); return; }
        }
        foreach (var z in b.Zones.Living())
        {
            if (z.Owner is not (Side.Enemy or Side.World)) continue;
            double d = Dist(z.X, z.Z, p.X, p.Z);
            if (d < z.Radius + p.Radius) { mx = (p.X - z.X) / Math.Max(0.1, d); mz = (p.Z - z.Z) / Math.Max(0.1, d); return; }
        }
        if (busy) return;
        Enemy? shooter = null;
        double sd = 11;
        foreach (var e in b.Enemies.Living())
        {
            if (e.Def.Ranged == null || e.Elite || e.Disposition != Disposition.Hostile || e.State == EnemyState.Dying || e.Wake > 0 && !e.Roused) continue;
            double d = Dist(e.X, e.Z, p.X, p.Z);
            if (d < sd) { sd = d; shooter = e; }
        }
        if (shooter != null && sd > 1.8 && b.HostilesInRadius(p.X, p.Z, 4.5).Count < 3) { mx = shooter.X - p.X; mz = shooter.Z - p.Z; return; }
        // The Kindling's core: stood beside, as anyone does who has read what breaking it gives.
        foreach (var e in b.Enemies.Living())
            if (e.Def.Id == "ember_core" && e.State != EnemyState.Dying && Dist(e.X, e.Z, p.X, p.Z) > 2.5) { mx = e.X - p.X; mz = e.Z - p.Z; return; }
    }

    /// <summary>The Bulwark's stance (docs/design/CLASSES.md 2.8, "walk in, let them hit you, and they break on it"): a player
    /// on the shield road walks into the press and holds it, since the road pays for blows taken (a stone for each one turned,
    /// Planted and The Wall Holds for standing). They give ground when low, under two-fifths of health, until mended to
    /// two-thirds; a champion at arm's length is given ground below half, as by any blade. Every other road keeps the plain hands.</summary>
    public static bool Wall(Battle b)
    {
        if (b.Lamps.Type != "bulwark") return false;
        var p = b.Player;
        if (steppedBack == b)
        {
            if (p.Hp < b.MaxHp * WallBack) return false;
            steppedBack = null;
        }
        if (p.Hp < b.MaxHp * WallLow) { steppedBack = b; return false; }
        return true;
    }
    public static double WallLow = 0.4, WallBack = 0.67;
    /// <summary>The run in which the wall stepped back to mend (each run plays on one thread).</summary>
    [ThreadStatic] static Battle? steppedBack;

    /// <summary>A trace of the hands' choices, each step (one traced run, single-threaded).</summary>
    [ThreadStatic] public static bool Debug;

    /// <summary>Off (--bossread 0) for the numbers of the hands before they knew the bosses.</summary>
    public static bool ReadsBosses = true;
    /// <summary>Off (--bank 0) for the hands before they banked a second Flare.</summary>
    public static bool Banks = true;
    /// <summary>Off (--flareboss 0): hands that never save the Flare for a boss (it goes on the crowd or at the edge), the
    /// player who doesn't time it: a fight without good Flare use.</summary>
    public static bool AimsFlare = true;
    /// <summary>Off (--flareuse 0): hands that never press the Flare (today's game measured as before the Flare).</summary>
    public static bool UsesFlare = true;
    public static bool PhaseAware = true;
    /// <summary>The game's (src/Game/Autopilot.cs; never set by the harness, whose pack never fills and whose filter hides nothing):
    /// a thing lying that her hands cannot take (hidden by the loot filter, refused by a full pack) is not walked to.
    /// Without it she stood on one, in the quiet of a map, until the twenty seconds' rule walked her off.</summary>
    public static Func<Pickup, bool>? Leaves;
    /// <summary>Whether the last Steer was deft (Act reads the kit's telegraphs with the same eyes).</summary>
    [ThreadStatic] static bool lastDeft;

    /// <summary>A pull seen (BossSense.Threat: marked long enough, noticed): walk straight out of its reach.</summary>
    static void OutOfPull(Battle b, bool deft, ref double mx, ref double mz)
    {
        var p = b.Player;
        foreach (var t in b.ActiveTells)
        {
            if (t.Pull <= 0 || t.Landed || !BossSense.Threat(t.Blow, deft)) continue;
            double dx = p.X - t.Blow.X, dz = p.Z - t.Blow.Z, d = Math.Sqrt(dx * dx + dz * dz);
            if (d > t.Reach + 0.5) continue;
            if (d < 0.05) { dx = mx; dz = mz; d = Math.Max(1e-6, Math.Sqrt(dx * dx + dz * dz)); }
            mx = dx / d; mz = dz / d;
            return;
        }
    }

    /// <summary>A closing round her with a way out (Sim/Tells.cs, its gap), seen: the mouth of the gap she is inside of,
    /// a little past its outer edge (null: none, or she is out).</summary>
    static (double X, double Z)? GapOut(Battle b, bool deft)
    {
        var p = b.Player;
        foreach (var t in b.ActiveTells)
        {
            var bl = t.Blow;
            if (t.Kind != "closing" || bl.GapWidth <= 0 || t.Landed && t.RushLeft <= 0 && !t.Walled) continue;
            if (!t.Landed && bl.Delay - bl.T < (deft ? BossSense.ReactDeft : BossSense.ReactPlain)) continue;
            double dx = p.X - bl.X, dz = p.Z - bl.Z, d = Math.Sqrt(dx * dx + dz * dz);
            if (d > bl.Radius + 0.5) continue;
            // Its wall (H6) lets her out only by the gap: from inside the inner edge and off the gap's bearing, first to the
            // gap's mouth (a chord, inside the wall), then out; on the band itself, straight off it.
            double mid = (bl.Inner + bl.Radius) / 2, off = d > 1e-3 ? Math.Abs(Math.IEEERemainder(Math.Atan2(dz, dx) - bl.GapAngle, Math.Tau)) * mid : 0;
            if (t.Walled && d < bl.Inner && off > bl.GapWidth / 2 - p.Radius)
                return (bl.X + Math.Cos(bl.GapAngle) * (bl.Inner - 1), bl.Z + Math.Sin(bl.GapAngle) * (bl.Inner - 1));
            if (t.Walled && d >= bl.Inner && off > bl.GapWidth / 2) return (bl.X + dx / d * (bl.Radius + 3), bl.Z + dz / d * (bl.Radius + 3));
            return (bl.X + Math.Cos(bl.GapAngle) * (bl.Radius + 3), bl.Z + Math.Sin(bl.GapAngle) * (bl.Radius + 3));
        }
        return null;
    }

    /// <summary>Inside a closing: walk for its way out.</summary>
    static void OutOfClosing(Battle b, bool deft, ref double mx, ref double mz)
    {
        if (GapOut(b, deft) is not var (gx, gz)) return;
        var p = b.Player;
        mx = gx - p.X; mz = gz - p.Z;
    }

    /// <summary>Inside a closing, near its way out: dash through it.</summary>
    static void ClosingDash(Battle b, bool leaps = false)
    {
        var p = b.Player;
        if (p.DashT > 0 || GapOut(b, lastDeft) is not var (gx, gz)) return;
        double dx = gx - p.X, dz = gz - p.Z;
        if (dx * dx + dz * dz >= 8.5 * 8.5) return;
        if (p.DashCharges > 0) { b.Dash(dx, dz); return; }
        // No dash left: a carried Heroic Leap goes out the same way.
        if (leaps && b.Weapons.Find(w => w.Behavior == WeaponBehavior.Leap && w.Timer <= 0) is { } lw)
        {
            double l = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz));
            b.PressSkill(lw.Slot, p.X + dx / l * 9, p.Z + dz / l * 9);
        }
    }

    /// <summary>The pressed skills a player carries (P7: Heroic Leap, Shield Charge, Bladestorm), pressed as one who
    /// knows them would: the leap at a pack of five or more within 9 m (its center), the charge into four or more in
    /// the 8 m line ahead, the storm held while four or more stand within 3.5 m and broken once two lines are pending,
    /// with half a second left, or as the crowd thins with a line down (out of a storm, Sunder's key swung at what is near); Iron Vow when three or more stand within 3 m, or
    /// (one who reads the marks: sees) a marked blow about to land on her.</summary>
    /// <summary>The campaign's held swings (a hold record: Sunder, Oathblade): held at the nearest foe within its reach and
    /// a step, released with none.</summary>
    static void Grips(Battle b)
    {
        var p = b.Player;
        foreach (var w in b.Weapons)
        {
            if (!w.Hold) continue;
            double reach = (w.Num(s => s.Reach) ?? 2.6) + 1.5;
            var near = b.NearestHostile(p.X, p.Z, reach);
            if (near == null) b.HoldSkill(w.Slot, false);
            else b.HoldSkill(w.Slot, true, near.X, near.Z);
        }
    }

    /// <summary>A campaign press the hand knows no better rule for (a spender, a wait): at the nearest foe in its reach
    /// when ready and paid for.</summary>
    static bool PressPlain(Battle b, WeaponInst w)
    {
        if (w.Press == null || w.Hold || w.Cast != CastMode.Press || w.Timer > 0) return false;
        if (b.Resolve.On && b.Resolve.Value < (w.Press.Resolve ?? 0)) return false;
        var p = b.Player;
        double reach = w.Press.Aim == PressAim.Self ? (w.Num(s => s.Radius) ?? 3.5) : w.Press.Reach ?? w.AimRange;
        var near = b.NearestHostile(p.X, p.Z, reach);
        return near != null && b.PressSkill(w.Slot, near.X, near.Z);
    }

    static void PressSkills(Battle b, bool sees = true)
    {
        var p = b.Player;
        if (p.Leap != null || b.Art.Rush != null || p.DashT > 0) return;
        foreach (var w in b.Weapons)
        {
            if (!w.Pressed || w.DisabledT > 0) continue;
            if (w.Behavior == WeaponBehavior.Leap && w.Timer <= 0)
            {
                var near = b.HostilesInRadius(p.X, p.Z, 9);
                if (near.Count < 5) continue;
                Enemy? best = null; int most = 0;
                foreach (var e in near)
                {
                    int n = 0;
                    foreach (var o in near) if ((o.X - e.X) * (o.X - e.X) + (o.Z - e.Z) * (o.Z - e.Z) <= 3.5 * 3.5) n++;
                    if (n > most) { most = n; best = e; }
                }
                if (best == null || most < 5) continue;
                double cx = 0, cz = 0; int k = 0;
                foreach (var o in near) if ((o.X - best.X) * (o.X - best.X) + (o.Z - best.Z) * (o.Z - best.Z) <= 3.5 * 3.5) { cx += o.X; cz += o.Z; k++; }
                b.PressSkill(w.Slot, cx / k, cz / k);
                return;
            }
            if (w.Behavior == WeaponBehavior.Charge && w.Timer <= 0)
            {
                double fx = Math.Sin(p.Facing), fz = Math.Cos(p.Facing);
                int n = 0;
                foreach (var e in b.HostilesInRadius(p.X + fx * 4, p.Z + fz * 4, 4.6))
                {
                    double ax = e.X - p.X, az = e.Z - p.Z, along = ax * fx + az * fz, side = Math.Abs(ax * fz - az * fx);
                    if (along > 0 && along <= 8 && side <= 1.2 + e.Radius) n++;
                }
                if (n >= 4) { b.PressSkill(w.Slot, p.X + fx * 8, p.Z + fz * 8); return; }
                continue;
            }
            if (w.Behavior == WeaponBehavior.Brace)
            {
                if (w.Timer > 0 || b.Bracing) continue;
                bool crowd = b.HostilesInRadius(p.X, p.Z, 3).Count >= 3;
                bool blow = false;
                if (sees) foreach (var bl in b.Blows) if (bl.Kind == TelegraphKind.Blow && bl.T <= 0.6 && bl.Hit(p.X, p.Z, p.Radius + 0.3)) { blow = true; break; }
                if (crowd || blow) { b.PressSkill(w.Slot, p.X, p.Z); return; }
                continue;
            }
            if (w.Behavior == WeaponBehavior.Spin)
            {
                int n = b.HostilesInRadius(p.X, p.Z, 3.5).Count;
                if (w.Channeling)
                {
                    bool late = w.ChannelMax - w.ChannelT <= 0.5;
                    if (w.Slot2 >= 0 && (w.Lines.Count >= 2 || late || (n < 4 && w.Lines.Count > 0))) { b.HoldSkill(w.Slot, false); b.PressSkill(w.Slot2, p.X, p.Z); }
                    else b.HoldSkill(w.Slot, n >= 4);
                }
                else if (w.Timer <= 0 && n >= 4) { b.HoldSkill(w.Slot, true); b.PressSkill(w.Slot, p.X + Math.Sin(p.Facing) * 2, p.Z + Math.Cos(p.Facing) * 2); }
                else
                {
                    b.HoldSkill(w.Slot, false);
                    // Out of a storm (on its cooldown, or too few for one), Sunder's key swings Sunder at what is in reach.
                    if (w.Slot2 >= 0 && !Firing.InStorm(b, w) && b.HostilesInRadius(p.X, p.Z, 3.5).Count > 0) b.PressSkill(w.Slot2, p.X, p.Z);
                }
                continue;
            }
            if (w.Behavior is not (WeaponBehavior.Leap or WeaponBehavior.Charge or WeaponBehavior.Brace) && PressPlain(b, w)) return;
        }
    }


    /// <summary>The kit's telegraphs that only a dash answers: rooted inside a marked blow, or dragged into a pull's
    /// heart faster than she can walk out of it before it lands. Out, away from its heart (seen as Steer saw it).</summary>
    static void KitDash(Battle b, double mx, double mz)
    {
        var p = b.Player;
        if (p.DashCharges <= 0 || p.DashT > 0) return;
        foreach (var t in b.ActiveTells)
        {
            var bl = t.Blow;
            if (t.Landed || bl.Kind != TelegraphKind.Blow || !BossSense.Threat(bl, lastDeft)) continue;
            double dx = p.X - bl.X, dz = p.Z - bl.Z, d = Math.Sqrt(dx * dx + dz * dz);
            bool dash;
            if (p.RootT > 0) dash = bl.Hit(p.X, p.Z, p.Radius + 0.3);
            else if (t.Pull > 0 && d <= t.Reach)
            {
                double walk = Math.Max(1, b.Stats.Get(Stat.MoveSpeed) * p.SlowF) - t.Pull;
                double need = bl.Radius + p.Radius + 0.5 - d;
                dash = need > 0 && (walk <= 0.1 || need / walk > bl.T);
            }
            else continue;
            if (!dash) continue;
            // A lane: across it. A circle: away from its heart.
            if (bl.Shape == TelegraphShape.Line) { double lx = bl.X1 - bl.X, lz = bl.Z1 - bl.Z; (dx, dz) = (-lz, lx); if (dx * (p.X - bl.X) + dz * (p.Z - bl.Z) < 0) { dx = -dx; dz = -dz; } }
            else if (d < 0.05) { dx = mx; dz = mz; }
            b.Dash(dx, dz);
            return;
        }
    }

    /// <summary>When this run's Flare came ready (each run plays on one thread).</summary>
    [ThreadStatic] static Battle? readyIn;
    [ThreadStatic] static double readyAt;

    /// <summary>The boss read as a player who has died to it once (Play/Bosses/BossSense.cs,
    /// shared with the game's autopilot).</summary>
    public static void Boss(Battle b, ArenaBoss? boss, bool deft, ref double mx, ref double mz, (double X, double Z)? goal = null, bool strikes = false, BossSense.Meeting? first = null) =>
        BossSense.Steer(b, boss, deft, Reach(b), ref mx, ref mz, goal, strikes, first);

    /// <summary>The way on nearest the one wanted that a step down it is clear; straight on if none is.</summary>
    static (double X, double Z) Clearest(Battle b, double mx, double mz)
    {
        var p = b.Player;
        double ml = Math.Max(1e-6, Math.Sqrt(mx * mx + mz * mz));
        mx /= ml; mz /= ml;
        foreach (double deg in (double[])[30, -30, 60, -60, 90, -90])
        {
            double a = deg * Math.PI / 180, c = Math.Cos(a), s = Math.Sin(a);
            double rx = mx * c - mz * s, rz = mx * s + mz * c;
            if (!b.Collision.Blocked(p.X + rx * 0.25, p.Z + rz * 0.25, p.Radius * 0.9)) return (rx, rz);
        }
        return (mx, mz);
    }

    /// <summary>Where a player points a line Flare: at a boss she can hurt within its length, else along the line through
    /// the most (a champion counts three).</summary>
    static (double X, double Z)? LineAim(Battle b, double len, double half)
    {
        var p = b.Player;
        var near = b.HostilesInRadius(p.X, p.Z, len).Where(e => e.Alive && e.State != EnemyState.Dying).ToList();
        if (near.Count == 0) return null;
        if (near.Where(e => e.Boss && e.TakenMul > 0).OrderBy(e => Dist(e.X, e.Z, p.X, p.Z)).FirstOrDefault() is { } boss) return (boss.X, boss.Z);
        (double X, double Z)? best = null;
        double bestN = -1;
        int step = Math.Max(1, near.Count / 48);
        for (int i = 0; i < near.Count; i += step)
        {
            var t = near[i];
            double l = Math.Max(0.1, Dist(t.X, t.Z, p.X, p.Z)), dx = (t.X - p.X) / l, dz = (t.Z - p.Z) / l, n = 0;
            foreach (var o in near)
            {
                double rx = o.X - p.X, rz = o.Z - p.Z, along = rx * dx + rz * dz;
                if (along >= 0 && along <= len && Math.Abs(-rx * dz + rz * dx) <= half + o.Radius) n += o.Elite ? 3 : 1;
            }
            if (n > bestN) { bestN = n; best = (t.X, t.Z); }
        }
        return best;
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
}
