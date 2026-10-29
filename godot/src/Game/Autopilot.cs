using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/// <summary>
/// A crude player, for testing and for pictures (the web game's
/// game/autopilot.ts): walks the prologue from the fire down the road, fights
/// on the way, opens the watchman's chest, drafts as the harness's sensible
/// player does (--draft first for the old first card), and out in a fight
/// circles a patch of ground keeping the crowd in front of it. It is not good
/// at the game; it shows the game runs.
/// </summary>
public sealed class Autopilot
{
    /// <summary>--no-drink: the autopilot never drinks a draught (a shot of her life falling).</summary>
    static readonly bool noDrink = Args.Has("no-drink");
    static readonly bool spots = Args.Has("spots");
    readonly Game g;
    readonly HashSet<Act> pressed = new();
    int wp = 1;
    double diagT, t, orbit, dashT, abilityT, drinkT, stuckT, sideT, lastX, lastZ, postT, resultT, choiceT;
    int side = 1;
    (double X, double Z, double R)? territory;
    /// <summary>Take the drafts and otherwise stand still (--auto idle): the worst player. (In the Prologue
    /// it walks the road until the Ambush springs, then stands.)</summary>
    public bool Idle;
    /// <summary>Walk down the screen, toward the camera (--auto toward): her face to it.</summary>
    public bool Toward;
    /// <summary>Run across the screen, turning back every few seconds (--auto across): her in
    /// profile at a run, for pictures and measures of her in motion.</summary>
    public bool Across;
    /// <summary>Walk up the screen, away from the camera (--auto away): her back and hair to it.</summary>
    public bool Away;
    /// <summary>In a town, walk to the nearest one who can be talked to and stand there, never pressing
    /// (--auto talk): pictures of the talk prompt and its lesson (au1 item 14).</summary>
    public bool Talk;
    double talkT;
    public (double X, double Z) Move { get; private set; }
    public readonly List<string> Log = new();
    string lastStage = "";
    double lineT;

    public Autopilot(Game game) { g = game; }

    readonly Picker picker = Picker.Make(Args.Get("draft") ?? "greedy");
    readonly SurvivorUnchained.Core.Rng rng = new(7);

    /// <summary>A press the survivor makes this step (taken once).</summary>
    public bool Take(Act a) => pressed.Remove(a);
    void Press(Act a) => pressed.Add(a);

    public void Drive(double dt)
    {
        t += dt;
        Move = (0, 0);
        // A callout is read: a freeze answered 1.2 s (real) after it shows, with its answer or the key
        // that goes on, and a panel's words left up as long before a card is taken. (With --shot, not
        // before its frame is taken.)
        if (g.Teaching is { } tc && (tc.Kind == CalloutKind.Freeze || tc.Kind == CalloutKind.Panel && g.Overlay == "draft"))
        {
            if (g.TeachingFor < 1.2 || Shots.Pending("teach_" + tc.Id)) return;
            if (tc.Kind == CalloutKind.Freeze)
            {
                Controls.Instance.Press(tc.Answer != null && Enum.TryParse<Act>(tc.Answer, true, out var ans) ? ans : Act.Confirm);
                return;
            }
        }
        // Drafted as a player would (the harness's greedy taste), or --draft first|random|path:ID.
        if (g.Overlay == "draft" && g.Battle is { } db) { g.Pick(Math.Clamp(picker.Choose(db, g.Offers.ToList(), rng), 0, Math.Max(0, g.Offers.Count - 1))); return; }
        // A line is read at a reader's pace (pictures of conversations need the line on screen).
        if (g.Overlay == "dialogue") { if ((lineT += dt) > 2.4) { lineT = 0; g.Advance(); } return; }
        lineT = 0;
        // A chest opening is watched to its end (pictures of it).
        if (g.Overlay == "chest") return;
        // A night's result is read, then left as a player leaves it (closing it as a screen
        // stranded the survivor on the empty field).
        if (g.Overlay == "arena") { if ((resultT += dt) > 5) { resultT = 0; Controls.Instance.Press(Act.Confirm); } return; }
        if (g.Overlay != null) { g.CloseOverlay(); return; }
        // A choice the story puts to her is read a while (pictures of it), then answered as --knee says
        // (spare, finish), or with its first answer: a run never stalls at his knee.
        if (g.Zone?.Choice is { } choice)
        {
            if ((choiceT += dt) < 3.5) return;
            choiceT = 0;
            string want = Args.Get("knee") == "finish" ? "finish" : "let_go";
            g.AnswerChoice(Math.Max(0, choice.Answers.ToList().FindIndex(a => a.Id == want)));
            return;
        }
        choiceT = 0;
        var b = g.Battle;
        var z = g.Zone;
        // (--auto toward: walking down the screen, toward the camera, her face
        // to it: pictures of her face at play zoom)
        if (Toward && b != null && b.Player.Alive && !g.InTransit) { Move = (0, 1); return; }
        if (Away && b != null && b.Player.Alive && !g.InTransit) { Move = (0, -1); return; }
        if (Across && b != null && b.Player.Alive && !g.InTransit) { Move = ((int)(t / 6) % 2 == 0 ? 1 : -1, 0); return; }
        // (idle in the Prologue walks the road like the pilot until the Ambush's trap springs, then stands:
        // the worst player in its first real fight, MR5 item 11); under --spots (pictures of fixed places) it stands where it is set down)
        if (b == null || z == null || !b.Player.Alive || g.InTransit || Idle && (spots || !(z is Zones.Prologue { Sprung: false }))) return;
        if (Talk && !z.Combat) { WalkUp(dt, b, z); return; }
        if (z.Id != "lowford") { Field(dt, b); return; }
        Prologue(dt, b, z);
    }

    void Prologue(double dt, Battle b, ZoneRuntime z)
    {
        var d = z.Debug();
        var stage = d.GetValueOrDefault("stage")?.ToString() ?? "";
        if (stage != lastStage) { Log.Add($"{t:0}s {stage} lvl{b.EmberLevel} hp{Math.Round(b.Player.Hp)} kills{b.KillCount}"); lastStage = stage; }
        var p = b.Player;
        if ((diagT += dt) > 3 && Godot.OS.GetCmdlineUserArgs().Contains("--teach-diag"))
        {
            diagT = 0;
            var kn = b.Enemies.Living().FirstOrDefault(e => e.Tag == "knight");
            Godot.GD.Print($"autodiag t={b.Time:0.0} stage={stage} p=({p.X:0.0},{p.Z:0.0}) wp={wp} postT={postT:0.0} knight={(kn == null ? "-" : $"({kn.X:0.0},{kn.Z:0.0}) {kn.State} hp={kn.Hp:0}/{kn.HpFloor:0}")}");
        }
        var meta = g.Scene!.Data.Meta;
        XZ Place(string n) => meta.Place("LOWFORD", n);
        double tx = p.X, tz = p.Z;
        switch (stage)
        {
            case "Wake" or "Rising" or "Ambush":
            {
                var c = stage == "Ambush" ? Place("cart") : Place("camp");
                orbit += dt * 0.35;
                tx = c.X + Math.Cos(orbit) * 7 - (stage == "Ambush" ? 4 : 0);
                tz = c.Z + Math.Sin(orbit) * 6 + (stage == "Ambush" ? 6 : 0);
                break;
            }
            case "Post" when b.Enemies.Living().FirstOrDefault(e => e.Tag == "knight" && e.State != EnemyState.Dying) is { } knight:
            {
                // The Barrow Knight stands between her and the chest (locked while it stands) and the road
                // on (the Barrow waits for it): never left (walked off down the road, she outran it, it
                // went home and the run stood still). Until its red line is read (F7, which waits for the
                // lane and the Knight's head and chest in the open), she draws it out onto open ground
                // near the post, clear of the walls and the trees, and circles there; then closes on it.
                if (!g.Taught("red_line"))
                {
                    var (ax, az) = knightGround ??= OpenNear(knight.X, knight.Z, 1.62 * (knight.Def.Scale ?? 1));
                    orbit += dt * 0.45;
                    tx = ax + Math.Cos(orbit) * 2.5; tz = az + Math.Sin(orbit) * 2.5;
                }
                else
                {
                    orbit += dt * 0.5;
                    tx = knight.X + Math.Cos(orbit) * 3; tz = knight.Z + Math.Sin(orbit) * 3;
                }
                break;
            }
            case "Post" when d.GetValueOrDefault("chestOpened") is false && postT < 25:
            {
                // From the chest's far side from the dead watchman, so the prompt is the chest's
                // (standing between them, the watchman's book was read over and over).
                postT += dt;
                var c = Place("chest");
                var m = Place("watchman");
                double ax = c.X - m.X, az = c.Z - m.Z, al = Math.Max(0.01, Math.Sqrt(ax * ax + az * az));
                tx = c.X + ax / al * 1.2; tz = c.Z + az / al * 1.2;
                if (Math.Sqrt((p.X - tx) * (p.X - tx) + (p.Z - tz) * (p.Z - tz)) < 1.0 && g.Prompted == "chest") Controls.Instance.Press(Act.Interact);
                break;
            }
            case "Barrow" when b.Enemies.Living().FirstOrDefault(e => e.Tag == "caller") is { } caller:
            {
                // The Grave-Caller holds the stage until it falls: close on it (it stood off down the road before).
                orbit += dt * 0.5;
                tx = caller.X + Math.Cos(orbit) * 3; tz = caller.Z + Math.Sin(orbit) * 3;
                break;
            }
            case "Boss" or "Intro":
            {
                var f = Place("ford");
                orbit += dt * 0.3;
                tx = f.X + Math.Cos(orbit) * 9; tz = f.Z + 10 + Math.Sin(orbit) * 5;
                break;
            }
            case "Victory":
                break;
            case "Dawn":
            {
                // The night is over: up the road to the Waystation, as the objective says (a run went on standing
                // at the top of the road for good, and never reached Act 1).
                var gt = Place("gate");
                tx = gt.X; tz = gt.Z - 8;
                break;
            }
            default:
            {
                // Down the road.
                var road = meta.Paths.GetValueOrDefault("ROAD") ?? Array.Empty<double[]>();
                while (wp < road.Length - 1 && road[wp][1] > p.Z - 3) wp++;
                if (road.Length > 0) { tx = road[Math.Min(wp, road.Length - 1)][0]; tz = road[Math.Min(wp, road.Length - 1)][1]; }
                break;
            }
        }
        // Keep off the crowd.
        double rx = 0, rz = 0;
        int near = 0;
        foreach (var e in b.Enemies.Living())
        {
            if (e.State == EnemyState.Dying || e.Disposition != Disposition.Hostile) continue;
            double dx = p.X - e.X, dz = p.Z - e.Z, dd = Math.Sqrt(dx * dx + dz * dz);
            if (dd < 4.5 && dd > 0.01) { rx += dx / dd * (4.5 - dd); rz += dz / dd * (4.5 - dd); }
            if (dd < 2.2) near++;
        }
        Steer(dt, tx - p.X + rx * 1.4, tz - p.Z + rz * 1.4, p, tx, tz);
        dashT -= dt; abilityT -= dt; drinkT -= dt;
        if (near >= 5 && dashT <= 0) { Press(Act.Dash); dashT = 1.2; }
        if (near >= 3 && abilityT <= 0 && !g.HoldFlare) { Press(Act.Flare); abilityT = 2; }
        if (p.Hp < b.MaxHp * 0.35 && !noDrink && drinkT <= 0 && !g.TeachWaiting("draught")) { Controls.Instance.Press(Act.Draught); drinkT = 1.5; }
    }

    /// <summary>Out in a fight with no script: circle a patch of ground, keep
    /// the crowd in front and moving, step out of marked ground and lunges,
    /// pick up ember when nothing is close, bash when mobbed, drink when low.
    /// An arena's boss up, it circles the boss instead and reads its fight as a
    /// practised player does (BossSense), so pictures show a fight fought.</summary>
    void Field(double dt, Battle b)
    {
        var p = b.Player;
        var script = g.Zone switch { ArenaRun a => a.BossScript, MapRun m => m.BossScript, StoryNight sn => sn.BossScript, _ => null };
        var boss = script is { } s && s.E is { Alive: true } be && be.State != EnemyState.Dying ? s : null;
        // A story night's stage says where it wants her (a fire to light, a foe to find).
        (double X, double Z)? goal = g.Zone is StoryNight night ? night.Goal : null;
        (double X, double Z, double R) home = boss != null ? (boss.E.X, boss.E.Z, 10.0) : goal is var (gx, gz) ? (gx, gz, 4.0) : territory ??= (p.X, p.Z, 18);
        double rx = 0, rz = 0;
        int close = 0;
        var sectors = new bool[8];
        foreach (var e in b.Enemies.Living())
        {
            if (e.State is EnemyState.Dying or EnemyState.Burrowed || !b.HostileToPlayer(e)) continue;
            double dx = p.X - e.X, dz = p.Z - e.Z, dd = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz));
            if (dd > 14) continue;
            if (dd < 3) close++;
            if (dd < 7) sectors[(int)((Math.Atan2(dz, dx) + Math.PI) / (Math.PI * 2) * 8) % 8] = true;
            double w = (e.Boss ? 0.8 : e.Elite ? 2.2 : 1) * Math.Max(0, 7 - dd) / 7;
            rx += dx / dd * w; rz += dz / dd * w;
            if (e.State is EnemyState.Windup or EnemyState.Lunging && dd < 6) { rx += -dz / dd * 2.5; rz += dx / dd * 2.5; }
        }
        int ring = sectors.Count(s => s);
        foreach (var zn in b.Zones.Living())
        {
            if (zn.Owner is Side.Player or Side.Ally) continue;
            double dx = p.X - zn.X, dz = p.Z - zn.Z, dd = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz));
            if (dd < zn.Radius + 0.8) { rx += dx / dd * 3; rz += dz / dd * 3; }
        }
        orbit += dt * 0.32;
        double tx = home.X + Math.Cos(orbit) * home.R * 0.6, tz = home.Z + Math.Sin(orbit) * home.R * 0.6;
        bool fetching = false;
        if (close == 0 && p.Hp > b.MaxHp * 0.4)
        {
            double best = 9;
            foreach (var k in b.Pickups.Living())
            {
                double dd = Math.Sqrt((k.X - p.X) * (k.X - p.X) + (k.Z - p.Z) * (k.Z - p.Z));
                if (dd < best && Math.Sqrt((k.X - home.X) * (k.X - home.X) + (k.Z - home.Z) * (k.Z - home.Z)) < home.R * 1.4) { best = dd; tx = k.X; tz = k.Z; fetching = true; }
            }
        }
        // Going to something on the ground, all the way onto it (gear is not pulled to her: eased
        // as the orbit is, she stopped a metre short and stood by a Legendary for good).
        double pull = fetching ? 1.5 : 0.25;
        double mx = (tx - p.X) * pull + rx * 1.6, mz = (tz - p.Z) * pull + rz * 1.6;
        double hd = Math.Sqrt((p.X - home.X) * (p.X - home.X) + (p.Z - home.Z) * (p.Z - home.Z));
        if (hd > home.R * 1.5) { mx += (home.X - p.X) / hd * 2; mz += (home.Z - p.Z) / hd * 2; }
        if (boss != null) BossSense.Steer(b, boss, true, 5, ref mx, ref mz);
        Steer(dt, mx, mz, p, tx, tz);
        dashT -= dt; abilityT -= dt; drinkT -= dt;
        if ((ring >= 6 || close >= 4) && dashT <= 0 && p.DashCharges > 0) { Press(Act.Dash); dashT = 0.8; }
        if (close >= 3 && abilityT <= 0 && !g.HoldFlare) { Press(Act.Flare); abilityT = 1.5; }
        if (p.Hp < b.MaxHp * 0.33 && !noDrink && drinkT <= 0 && !g.TeachWaiting("draught")) { Controls.Instance.Press(Act.Draught); drinkT = 1.5; }
    }

    (double X, double Z)? knightGround;

    /// <summary>The nearest ground round a point (rings of 5, 8 and 11 m) where a figure `up` metres tall
    /// stands in the open from the camera, with the ground 3 and 6 m round it open too (a lane drawn there
    /// is seen); none: the point itself.</summary>
    (double X, double Z) OpenNear(double x, double z, double up)
    {
        foreach (double r in new[] { 5.0, 8.0, 11.0 })
            for (int i = 0; i < 12; i++)
            {
                double a = i * Math.PI / 6, cx = x + Math.Cos(a) * r, cz = z + Math.Sin(a) * r;
                if (!g.OpenGround(cx, cz, up)) continue;
                bool clear = true;
                for (int k = 0; k < 8 && clear; k++)
                {
                    double ka = k * Math.PI / 4;
                    clear = g.OpenGround(cx + Math.Cos(ka) * 3, cz + Math.Sin(ka) * 3, up) && g.OpenGround(cx + Math.Cos(ka) * 6, cz + Math.Sin(ka) * 6, 0.2);
                }
                if (clear)
                {
                    if (Godot.OS.GetCmdlineUserArgs().Contains("--teach-diag")) Godot.GD.Print($"autodiag knight ground ({cx:0.0},{cz:0.0}) from ({x:0.0},{z:0.0})");
                    return (cx, cz);
                }
            }
        return (x, z);
    }

    /// <summary>Go that way; wedged on something, sidestep for a moment.</summary>
    void WalkUp(double dt, Battle b, ZoneRuntime z)
    {
        var p = b.Player;
        // (a few seconds' look round first: the town's first lesson, the map, comes with her standing)
        if ((talkT += dt) < 8) return;
        var to = z.Interactables.Where(i => i.Id.StartsWith("talk:") && (i.When == null || i.When()))
            .OrderBy(i => (i.X - p.X) * (i.X - p.X) + (i.Z - p.Z) * (i.Z - p.Z)).FirstOrDefault();
        if (to == null) return;
        double dx = to.X - p.X, dz = to.Z - p.Z;
        if (Math.Sqrt(dx * dx + dz * dz) < Math.Min(1.6, to.R * 0.6)) return;
        Steer(dt, dx, dz, p, to.X, to.Z);
    }

    void Steer(double dt, double mx, double mz, PlayerState p, double tx, double tz)
    {
        stuckT += dt;
        if (stuckT > 2.5)
        {
            if (Math.Sqrt((p.X - lastX) * (p.X - lastX) + (p.Z - lastZ) * (p.Z - lastZ)) < 0.8 && Math.Sqrt((tx - p.X) * (tx - p.X) + (tz - p.Z) * (tz - p.Z)) > 2) { sideT = 1.3; side = -side; }
            stuckT = 0; lastX = p.X; lastZ = p.Z;
        }
        if (sideT > 0)
        {
            sideT -= dt;
            double l = Math.Max(1e-6, Math.Sqrt(mx * mx + mz * mz)), ox = mx / l, oz = mz / l;
            mx = ox - oz * 1.5 * side; mz = oz + ox * 1.5 * side;
        }
        double m = Math.Sqrt(mx * mx + mz * mz);
        Move = m > 0.3 ? (mx / m, mz / m) : (0, 0);
    }
}
