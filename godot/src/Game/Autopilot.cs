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
    readonly Dictionary<string, double> lampTried = new();
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
    int answered;
    double standDiag;

    public Autopilot(Game game) { g = game; }

    readonly Picker picker = Picker.Make(Args.Get("draft") ?? "greedy");
    readonly SurvivorUnchained.Core.Rng rng = new(7);

    /// <summary>A press the survivor makes this step (taken once).</summary>
    public bool Take(Act a) => pressed.Remove(a);
    void Press(Act a) => pressed.Add(a);

    double draftFor;
    static readonly double DraftHold = Args.Num("draft-hold", 0);
    static readonly bool DayRush = Args.Has("day-rush");

    public void Drive(double dt)
    {
        t += dt;
        Move = (0, 0);
        // A callout is read: a freeze answered 1.2 s (real) after it shows, with its answer or the key
        // that goes on, and a panel's words left up as long before a card is taken. (With --shot, not
        // before its frame is taken.)
        // The dawn's card is read as a freeze is, then clicked through (with --shot, after its frame).
        if (g.DawnUp) { if (g.DawnFor >= 1.2 && !Shots.Pending("dawn_card")) Controls.Instance.Press(Act.Confirm); return; }
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
        // (--draft-hold S: a human's pause over the cards, H8's N35 repro: a draft open as a boss arrives)
        if (g.Overlay == "draft") draftFor += dt; else draftFor = 0;
        if (g.Overlay == "draft" && draftFor < DraftHold) return;
        if (g.Overlay == "draft" && g.Battle is { } db) { g.Pick(Math.Clamp(picker.Choose(db, g.Offers.ToList(), rng), 0, Math.Max(0, g.Offers.Count - 1))); return; }
        // A line is read at a reader's pace (pictures of conversations need the line on screen).
        // A line with choices is answered (Advance would end the talk): --answers 0,1 picks among the enabled ones in turn, else the first.
        if (g.Overlay == "dialogue")
        {
            if ((lineT += dt) > 2.4)
            {
                lineT = 0;
                var opts = g.LineChoices;
                if (opts.Count == 0) g.Advance();
                else
                {
                    var said = (Args.Get("answers") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries);
                    int k = answered < said.Length && int.TryParse(said[answered], out var ai) ? ai : 0;
                    answered++;
                    g.Choose(opts[Math.Clamp(k, 0, opts.Count - 1)].Index);
                }
            }
            return;
        }
        lineT = 0;
        // A chest opening is watched to its end (pictures of it).
        if (g.Overlay == "chest") { if (legendSeen && !cardShot) { cardShot = true; Frame("legendary_card", 1.2); } return; }
        // (M5 r2: the watch-post's menu, opened once, framed, then closed)
        if (g.Overlay == "post" && menuT >= 0) { if ((menuT += dt) > 2.2 && !Shots.Pending("post_menu_watch")) { menuT = -1; g.CloseOverlay(); } return; }
        // A night's result is read, then left as a player leaves it (closing it as a screen
        // stranded the survivor on the empty field).
        if (g.Overlay == "arena")
        {
            if (!resultSeen) { resultSeen = true; nightsEnded++; if (GoalsOn) Frame($"loop_result_{Math.Max(1, arenasEntered)}", 4); }
            if ((resultT += dt) > 5) { resultT = 0; Controls.Instance.Press(Act.Confirm); }
            return;
        }
        resultSeen = false;
        // The Wayfinder's table: a picture of it, then the night's offer taken (--offer N), as a player does.
        // (the zone ends at the town: a run begun in the Low Ford never works the table, M5 r2)
        if (g.Overlay == "maps" && GoalsOn && !(fromLowford && g.Zone?.Id == "waystation")) { Table(dt); return; }
        tableOpen = false;
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
        if (z?.Id == "lowford") fromLowford = true;
        if (GoalsOn) Track(dt, b, z);
        if (b != null && z != null) Hooks(b, z);
        // (--auto toward: walking down the screen, toward the camera, her face
        // to it: pictures of her face at play zoom)
        if (Toward && b != null && b.Player.Alive && !g.InTransit) { Move = (0, 1); return; }
        if (Away && b != null && b.Player.Alive && !g.InTransit) { Move = (0, -1); return; }
        if (Across && b != null && b.Player.Alive && !g.InTransit) { Move = ((int)(t / 6) % 2 == 0 ? 1 : -1, 0); return; }
        // (never during a film: j08 r2's walked her to the road's boars under C04 A, and its hand-back cut on a fight's pose)
        // (idle in the Prologue walks the road like the pilot until the Ambush's trap springs, then stands:
        // the worst player in its first real fight, MR5 item 11); under --spots (pictures of fixed places) it stands where it is set down)
        // --stand-at-boss (with --auto idle): she walks up to a hostile boss and stands in reach of him, as a standing player does
        // (the court clip: Corvane is tuned for a player in his reach; idle far off simply dies).
        if (Idle && Args.Has("stand-at-boss") && b != null && b.Player.Alive && !g.InTransit && !g.InCinematic
            && b.Enemies.Living().FirstOrDefault(e => e.Boss && e.Disposition == Disposition.Hostile) is { } boss)
        {
            double bx = boss.X - b.Player.X, bz = boss.Z - b.Player.Z;
            if ((standDiag += dt) > 2) { standDiag = 0; Godot.GD.Print($"stand t={b.Time:0.0} her ({b.Player.X:0.0},{b.Player.Z:0.0}) hp {b.Player.Hp:0}/{b.MaxHp:0} him ({boss.X:0.0},{boss.Z:0.0}) hp {boss.Hp:0}/{boss.MaxHp:0} d {Math.Sqrt(bx * bx + bz * bz):0.0}"); }
            if (Math.Sqrt(bx * bx + bz * bz) > 2.0) Move = (Math.Abs(bx) < 0.3 ? 0 : Math.Sign(bx), Math.Abs(bz) < 0.3 ? 0 : Math.Sign(bz));
            return;
        }
        // (the court clip: she holds where the ember set her down until Corvane has talked and she has raised her weapon, so
        // the arrival's frame is the court as a player first sees it, P6 r7)
        if (Args.Has("clip") && z is Zones.StoryNight { Beat: Story.Doorway { Raised: false } }) return;
        if (b == null || z == null || !b.Player.Alive || g.InTransit || g.InCinematic || Idle && (spots || !(z is Zones.Prologue { Sprung: false }))) return;
        if (Talk && !z.Combat) { WalkUp(dt, b, z); return; }
        if (fromLowford && z.Id == "waystation") { TownStop(dt, b); return; }
        if (GoalsOn && GoalWalk(dt, b, z)) return;
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
            var nightDiag = d.GetValueOrDefault("night");
            Godot.GD.Print($"autodiag t={b.Time:0.0} stage={stage} p=({p.X:0.0},{p.Z:0.0}) wp={wp} postT={postT:0.0} knight={(kn == null ? "-" : $"({kn.X:0.0},{kn.Z:0.0}) {kn.State} hp={kn.Hp:0}/{kn.HpFloor:0}")} night={nightDiag}");
        }
        var meta = g.Scene!.Data.Meta;
        XZ Place(string n) => meta.Place("LOWFORD", n);
        double tx = p.X, tz = p.Z;
        switch (stage)
        {
            // (M5: the Rising is placed beats now, n_lone and n_three up the road; it walks to them as the default does)
            // (the Ambush, once its trap has sprung, is fought as the default does: its nearest foe, where it stands; orbiting
            // the wagon kept her off its bowmen for good, m5 clip r1)
            case "Wake" or "Ambush" or "Rising" when Idle || stage == "Wake" || stage == "Ambush" && z is not Zones.Prologue { Sprung: true }:
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
            // (M5 r2) The watch-post's lamp once the Knight is down (its prompt offered then): walked to and lit, as a player
            // does, foes near it or not (Locked waits them out; the blows land as she stands there).
            case "Post" or "Barrow" when !Idle && WatchLamp(z) is { } wl && watchT < 40:
            {
                watchT += dt;
                tx = wl.X + 1.0; tz = wl.Z + 1.0;
                LightAt(wl, p);
                break;
            }
            case "Barrow" when b.Enemies.Living().FirstOrDefault(e => e.Tag == "caller") is { } caller:
            {
                // The Grave-Caller holds the stage until it falls: close on it (it stood off down the road before).
                orbit += dt * 0.5;
                tx = caller.X + Math.Cos(orbit) * 3; tz = caller.Z + Math.Sin(orbit) * 3;
                break;
            }
            // The Warden's fight as ZoneSim's bot plays it: a lit lamp between her and him (his charge breaks it, her blows
            // reach it), then him (he holds at his floor until two lamps are broken: circling the ford, she never won, m5 clip r2).
            case "Boss" when !Idle && z is Zones.Prologue pb && b.Enemies.Living().FirstOrDefault(e => e.Tag == "warden" && e.State != EnemyState.Dying) is { } w:
            {
                var lit = pb.LampPosts.Where(l => l.Lit).OrderBy(l => (l.X - p.X) * (l.X - p.X) + (l.Z - p.Z) * (l.Z - p.Z)).ToList();
                if (lit.Count > 0)
                {
                    var l = lit[0];
                    double dx = l.X - w.X, dz = l.Z - w.Z, dl = Math.Max(0.1, Math.Sqrt(dx * dx + dz * dz));
                    tx = l.X + dx / dl * 1.6; tz = l.Z + dz / dl * 1.6;
                }
                else { tx = w.X; tz = w.Z; }
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
            // (M5 r2) The Warden's Legendary is taken before the day's road (it lay at the ford all day).
            case "Dawn" or "Exit" when !Idle && b.Pickups.Living().FirstOrDefault(k => k.Loot is (int)Rpg.LootTier.Legendary or (int)Rpg.LootTier.Storied) is { } lg && legendWalkT < 25:
                legendWalkT += dt;
                tx = lg.X; tz = lg.Z;
                break;
            case "Dawn" or "Exit" when z is Zones.Prologue pd && pd.DayGoal() is { } dg:
            {
                // The road by day (H4 item 10): its fights where they wake, the strongbox, the dark lamp, then the gate.
                if (pickChampion) PickChampion(b);
                tx = dg.X; tz = dg.Z;
                dayFight = pd.DayFighting; dayRoad = true;
                // (--day-rush: straight up the road to the gate, past every fight: the owner's run on demo-rc2, N22)
                if (DayRush) { tx = 0.3; tz = -110; dayFight = false; }
                interactT -= dt;
                if (dg.Press != null && g.Prompted == dg.Press && interactT <= 0) { interactT = 1.5; Controls.Instance.Press(Act.Interact); }
                break;
            }
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
                // The night's beats as ZoneSim's goal walks them (ported; --auto idle keeps the plain road): the next undone
                // beat's ground, a waking pack's foe where it stands; the beats done, down the road and to the ford.
                if (!Idle && z is Zones.Prologue pn && pn.Night is { } nn)
                {
                    var gn = nn.Goal(_ => true, _ => null, Place("gate").X);
                    if (gn.For != null || nn.Fighting) { tx = gn.X; tz = gn.Z; }
                    else if (p.Z < Place("ford").Z + 25) { tx = Place("ford").X; tz = Place("ford").Z + 12; }
                }
                break;
            }
        }
        // A lamp-post she passes, out of a fight, is lit as a player does it: walked to, then the interact key at its prompt
        // (the Low Ford only; not the idle/toward/across/away/talk modes, not the Warden's fight).
        if (!Idle && stage is not ("Boss" or "Intro" or "Victory" or "Wake" or "Rising" or "Ambush"))
        {
            interactT -= dt;
            bool inFight = b.Enemies.Living().Any(e => e.Roused && e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && Math.Sqrt((e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z)) < 24);
            if (!inFight)
                foreach (var i in z.Interactables)
                    if (i.Id.StartsWith("lamppost:") && (i.When?.Invoke() ?? true) && i.Locked?.Invoke() == null
                        && Math.Sqrt((i.X - p.X) * (i.X - p.X) + (i.Z - p.Z) * (i.Z - p.Z)) is var di && di < 14)
                    {
                        double since = lampTried.TryGetValue(i.Id, out var pt) ? pt : lampTried[i.Id] = t;
                        if (t - since >= 20) continue;
                        tx = i.X; tz = i.Z;
                        LightAt(i, p);
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
        // (a day fight is fought where it stands, as a player would: pulled to its foe at least as hard as five metres
        // off, so the crowd's push does not walk her out of the camp and down to the river, j08 r2)
        double pullX = tx - p.X, pullZ = tz - p.Z, pullD = Math.Sqrt(pullX * pullX + pullZ * pullZ);
        if (dayFight && pullD > 0.01 && pullD < 5) { pullX *= 5 / pullD; pullZ *= 5 / pullD; }
        dayFight = false;
        // (the day road, r3: out of a marked lane or ring before it lands, dashing if it is close, as the charge's lesson
        // teaches; j08 r3 stood in the boars' lanes and fell to 6%)
        if (dayRoad)
            foreach (var bl in b.Blows)
            {
                if (bl.T > 0.9 || !bl.Hit(p.X, p.Z, p.Radius + 0.6)) continue;
                double ox, oz;
                double lx = bl.X1 - bl.X, lz = bl.Z1 - bl.Z, ll = Math.Sqrt(lx * lx + lz * lz);
                if (bl.Shape == TelegraphShape.Line && ll > 0.1)
                {
                    double nx = -lz / ll, nz = lx / ll;
                    double sd = (p.X - bl.X) * nx + (p.Z - bl.Z) * nz;
                    ox = nx * (sd >= 0 ? 1 : -1); oz = nz * (sd >= 0 ? 1 : -1);
                }
                else { double ax = p.X - bl.X, az = p.Z - bl.Z, al = Math.Max(1e-3, Math.Sqrt(ax * ax + az * az)); ox = ax / al; oz = az / al; }
                pullX = ox * 10; pullZ = oz * 10; rx = rz = 0;
                if (bl.T < 0.5 && dashT <= 0) { Press(Act.Dash); dashT = 1.2; }
                break;
            }
        dayRoad = false;
        Steer(dt, pullX + rx * 1.4, pullZ + rz * 1.4, p, tx, tz);
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
        if (pickChampion) PickChampion(b);
        if (holdLamp && g.Zone is ArenaRun ar && ar.Lamp != null && g.CurrentMap != null)
        {
            if (lampHoldFor != ar) { lampHoldFor = ar; lampHold = LampHold.For(ar, g.CurrentMap, b, 0, "deft"); }
            lampHold?.Tick(dt);
        }
        else lampHold = null;
        var script = g.Zone switch { ArenaRun a => a.BossScript, MapRun m => m.BossScript, StoryNight sn => sn.BossScript, _ => null };
        var boss = script is { } s && s.E is { Alive: true } be && be.State != EnemyState.Dying ? s : null;
        // A story night's stage says where it wants her (a fire to light, a foe to find).
        (double X, double Z)? goal = g.Zone is StoryNight night ? night.Goal : lampHold?.Goal(b);
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
        // Holding the lamp: not out past its pool's edge unless something is at her throat.
        if (goal == null && lampHold != null && close == 0 && lampHold.Leaving(b, mx, mz) && g.Zone is ArenaRun { Lamp: { } lp }) { mx = lp.X - p.X; mz = lp.Z - p.Z; }
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

    // ---- The goals (data/content/goals.json): the loop of a night, followed as a new player would ----

    /// <summary>Follow the goals under --auto (not in the idle/toward/away/across/talk modes), unless --no-goals.</summary>
    static readonly bool holdLamp = Args.Get("hold-lamp") != "no";
    static readonly bool pickChampion = Args.Get("pick") == "champion";
    LampHold? lampHold;
    ArenaRun? lampHoldFor;

    /// <summary>--pick champion: her priority foe (Battle.Priority, as Game.Priority() sets it for a player) is the nearest live
    /// champion (elite, not the boss) within 14 m, kept until it dies or goes past 20 m.</summary>
    void PickChampion(Battle b)
    {
        var p = b.Player;
        if (b.Priority >= 0 && b.Priority < b.Enemies.Items.Length)
        {
            var cur = b.Enemies.Items[b.Priority];
            double cd = Math.Sqrt((cur.X - p.X) * (cur.X - p.X) + (cur.Z - p.Z) * (cur.Z - p.Z));
            if (b.Targetable(cur) && cur.Elite && !cur.Boss && cd <= 20) return;
            b.Priority = -1;
        }
        Enemy? best = null; double bd = 14;
        foreach (var e in b.Enemies.Living())
        {
            if (!e.Elite || e.Boss || e.State == EnemyState.Dying || !b.Targetable(e) || !b.HostileToPlayer(e)) continue;
            double d = Math.Sqrt((e.X - p.X) * (e.X - p.X) + (e.Z - p.Z) * (e.Z - p.Z));
            if (d <= bd) { bd = d; best = e; }
        }
        if (best != null) b.Priority = best.Id;
    }

    bool GoalsOn => !Idle && !Toward && !Away && !Across && !Talk && !Args.Has("no-goals");
    bool resultSeen, tableOpen, townShot, leaving, tableEnded;
    int nightsEnded, arenasEntered, backFor;
    double tableT, wonT = -1, leaveT, interactT, printT;
    string lastZone = "";

    /* ---- (M5 r2) capture hooks for the judge: named frames at the moments that matter, a line or two each ---- */
    readonly HashSet<double> woke = new();
    readonly Dictionary<double, int> tells = new();
    readonly HashSet<object> blowsSeen = new();
    readonly HashSet<string> lampShots = new();
    double watchT, legendWalkT, menuT = -1, litAt = -1;
    bool legendSeen, cardShot, menuDone, fell, wasDown;
    static readonly bool FallOnce = Args.Has("fall-once");
    static readonly bool JudgeHooks = Args.Has("judge-hooks");  // (the watch-post's menu dwell: only for the judge's capture, never the pacing run)

    static string Slug(Enemy e) => new string((e.Named?.Title ?? e.Def.Id).Split(',')[0].Where(char.IsLetterOrDigit).ToArray()).ToLowerInvariant();

    Interactable? WatchLamp(ZoneRuntime z) => z.Interactables.FirstOrDefault(i => i.Id == "lamppost:lowford.watch" && (i.When?.Invoke() ?? true));

    /// <summary>At a post's Light prompt: its frame first, then the key; a frame after the lighting.</summary>
    void LightAt(Interactable i, PlayerState p)
    {
        if (Math.Sqrt((i.X - p.X) * (i.X - p.X) + (i.Z - p.Z) * (i.Z - p.Z)) >= i.R || g.Prompted != i.Id || interactT > 0) return;
        string id = i.Id[9..].Replace('.', '_');
        if (lampShots.Add("p" + id)) { Frame($"light_prompt_{id}", 0.2); interactT = 0.6; return; }
        if (Shots.Pending($"light_prompt_{id}")) return;
        interactT = 1.5;
        Controls.Instance.Press(Act.Interact);
        if (lampShots.Add("l" + id)) { Frame($"light_lit_{id}", 0.5); Frame($"light_lit_{id}_b", 1.6); }
    }

    void Hooks(Battle b, ZoneRuntime z)
    {
        foreach (var e in b.Enemies.Living())
        {
            if (e.Rank == 0 || e.State == EnemyState.Dying) continue;
            if (e.Roused && woke.Add(e.Seed)) Frame($"wake_{(e.Rank == 2 ? "champ" : "capt")}_{Slug(e)}", 1.5);
        }
        foreach (var bl in b.Blows)
            if (bl.From is { Rank: 2 } ch && blowsSeen.Add(bl) && tells.GetValueOrDefault(ch.Seed) < 3)
            {
                int n = tells[ch.Seed] = tells.GetValueOrDefault(ch.Seed) + 1;
                Frame($"tell_{Slug(ch)}_{n}", Math.Min(0.4, bl.Delay * 0.5));
            }
        if (blowsSeen.Count > 512) blowsSeen.Clear();
        if (!legendSeen && b.Pickups.Living().FirstOrDefault(k => k.Loot is (int)Rpg.LootTier.Legendary or (int)Rpg.LootTier.Storied) is { } lg)
        {
            legendSeen = true;
            Frame("legendary_ground", 0.6); Frame("legendary_ground_b", 2.0);
        }
        if (litAt < 0 && z.Id == "lowford" && Rpg.LampBook.PostLit(g.Journey.World, "lowford.watch")) litAt = t;
        // The post's menu, once, 3 s after the watch-post burns, while she stands by it.
        if (JudgeHooks && litAt >= 0 && !menuDone && t - litAt > 3)
        {
            menuDone = true; menuT = 0;
            g.OpenPost("lowford.watch");
            Frame("post_menu_watch", 0.8);
        }
        // --fall-once: her life to nothing once, after the watch-post burns and its menu is closed; the fall and the rise framed.
        if (FallOnce && !fell && (menuDone || !JudgeHooks) && menuT < 0 && b.Player.Alive && t - litAt > 8)
        {
            fell = true;
            Godot.GD.Print($"auto: fall-once t={b.Time:0.0}");
            b.HurtPlayerRaw(b.Player.Hp + b.MaxHp * 10, School.Physical, "fall-once", null);
            Frame("fall", 0.8);
        }
        if (fell && !b.Player.Alive) wasDown = true;
        if (wasDown && b.Player.Alive) { wasDown = false; Frame("rise", 0.4); Frame("rise_b", 2.0); }
    }

    void Frame(string tag, double seconds)
    {
        Godot.GD.Print($"auto: {tag} (frame in {seconds} s)");
        Shots.Want(tag, seconds);
    }

    /// <summary>A step of the loop kept as a save (town steps only: an arena keeps nothing until it is over), so a
    /// replay can start from it: tools/experience/demo_run.py copies the saves folder on each "auto: saved" line.</summary>
    void Keep(string tag) => g.After(4, () => { g.Save("loop"); Godot.GD.Print($"auto: saved {tag}"); });

    /// <summary>Where the loop is: entering the town and the arenas, and an arena won.</summary>
    void Track(double dt, Battle? b, ZoneRuntime? z)
    {
        if (b == null || z == null || g.InTransit) return;
        if (z.Id != lastZone)
        {
            lastZone = z.Id;
            if (z.Id == "waystation")
            {
                if (!townShot) { townShot = true; Frame("loop_town", 3); Keep("loop_town"); }
                if (nightsEnded > 0 && backFor < nightsEnded) { backFor = nightsEnded; Frame($"loop_back_{nightsEnded}", 3); Keep($"loop_back_{nightsEnded}"); }
            }
            else if (z is ArenaRun or MapRun)
            {
                arenasEntered++;
                wonT = -1; leaving = false; leaveT = 0; printT = 0;
                Frame($"loop_arena_{arenasEntered}", 10);
            }
        }
        bool won = z switch { ArenaRun a => a.Won, MapRun m => m.Cleared, _ => false };
        if (!won) return;
        if (wonT < 0)
        {
            wonT = 0;
            Frame($"loop_won_{arenasEntered}", 3);
            Frame($"loop_wayline_{arenasEntered}", 6);
        }
        else wonT += dt;
        // The first moment she is free again after the win (the hoard's chest and its words closed): what the player sees then.
        if (freeFor != arenasEntered && g.Overlay == null && g.Teaching == null)
        {
            freeFor = arenasEntered;
            Frame($"loop_free_{arenasEntered}", 1);
            Frame($"loop_free_{arenasEntered}_b", 8);
            Frame($"loop_free_{arenasEntered}_c", 16);
        }
    }

    /// <summary>The table open: a picture, then the offer taken; after the last night (--nights N) it stays open.</summary>
    void Table(double dt)
    {
        int n = arenasEntered + 1, last = (int)Args.Num("nights", 0);
        bool done = last > 0 && nightsEnded >= last;
        if (!tableOpen)
        {
            tableOpen = true; tableT = 0;
            Frame($"loop_table_open_{n}", 2);
            if (done) Frame("loop_table_after", 2);
        }
        tableT += dt;
        if (done)
        {
            if (!tableEnded) { tableEnded = true; Shots.EndIn(4); }
            return;
        }
        if (tableT < 3) return;
        var w = g.Journey.World;
        var offers = SurvivorUnchained.Maps.MapOffers.Today(w.Day, Math.Max(1, (int)w.Fact("arena.best").Number), (int)w.Fact("map.drawn").Number);
        int pick = Math.Clamp((int)Args.Num("offer", 0), 0, offers.Count - 1);
        Godot.GD.Print($"auto: night {n}: taking offer {pick}");
        tableOpen = false;
        g.SetOut(offers[pick]);
    }

    /// <summary>(M5 r2) The zone ends at the town: a run begun in the Low Ford, once through its gate into the Waystation
    /// (prologue.done), walks to the square's lamp-post and stands there. No table, no map, no arena loop (the Wayfinder's
    /// table is the arena's door, not the campaign's hand-off). Runs started elsewhere (--zone waystation --nights N) loop as before.</summary>
    bool fromLowford, townStood;
    void TownStop(double dt, Battle b)
    {
        var p = b.Player;
        var post = SurvivorUnchained.Content.LampPosts.Get("waystation.square");
        if (post == null) return;
        double dx = post.X - p.X, dz = post.Z - p.Z, d = Math.Sqrt(dx * dx + dz * dz);
        if (d < 1.8)
        {
            if (!townStood) { townStood = true; Godot.GD.Print($"auto: town stop at the square's lamp t={t:0.0} prologue.done={g.Journey.World.Fact("prologue.done").Truthy}"); Frame("town_stop", 1.5); }
            return;
        }
        routeT -= dt;
        if (route == null || routeT <= 0 || routeFor != (post.X, post.Z))
        {
            routeT = 3; routeFor = (post.X, post.Z);
            route = SurvivorUnchained.Sim.GroundPath.Find(b.Collision, p.X, p.Z, post.X, post.Z);
        }
        while (route is { Count: > 1 } && Math.Sqrt((route[0].X - p.X) * (route[0].X - p.X) + (route[0].Z - p.Z) * (route[0].Z - p.Z)) < 0.8) route.RemoveAt(0);
        double sx = dx / d, sz = dz / d;
        if (route is { Count: > 0 })
        {
            double wx = route[0].X - p.X, wz = route[0].Z - p.Z, wd = Math.Max(0.01, Math.Sqrt(wx * wx + wz * wz));
            sx = wx / wd; sz = wz / wd;
        }
        Steer(dt, sx, sz, p, post.X, post.Z);
    }

    /// <summary>Walk to the goal and use it: in the town, the first one standing; in a won arena, the way out
    /// once --leave-after S (20) have passed since it was won. True when it has the step.</summary>
    int freeFor;
    List<(double X, double Z)>? route;
    bool dayFight, dayRoad;
    double routeT;
    (double, double) routeFor;

    bool GoalWalk(double dt, Battle b, ZoneRuntime z)
    {
        var pins = g.GoalPins();
        ActiveGoal? pin;
        bool crowd = false;
        if (!z.Combat) pin = pins.FirstOrDefault();
        else
        {
            if (wonT < 0 || wonT < Args.Num("leave-after", 20)) return false;
            pin = pins.FirstOrDefault(a => a.Def.Pin == "way_out");
            crowd = true;
            if (pin != null && !leaving)
            {
                leaving = true; leaveT = 0;
                Frame($"loop_leaving_{arenasEntered}", 0.5);
                Frame($"loop_leaving_{arenasEntered}_b", 5);
            }
        }
        if (pin == null) return false;
        var p = b.Player;
        double dx = pin.X - p.X, dz = pin.Z - p.Z, d = Math.Sqrt(dx * dx + dz * dz);
        interactT -= dt;
        if (d < pin.R * 0.7)
        {
            if (interactT <= 0) { interactT = 1.5; Controls.Instance.Press(Act.Interact); }
            return true;
        }
        if ((printT -= dt) <= 0) { printT = 5; Godot.GD.Print($"auto: to {pin.Def.Pin} {d:0.0} m"); }
        double rx = 0, rz = 0;
        int close = 0;
        if (crowd)
            foreach (var e in b.Enemies.Living())
            {
                if (e.State is EnemyState.Dying or EnemyState.Burrowed || !b.HostileToPlayer(e)) continue;
                double ex = p.X - e.X, ez = p.Z - e.Z, ed = Math.Max(0.01, Math.Sqrt(ex * ex + ez * ez));
                if (ed < 3) close++;
                if (ed < 7) { double w = Math.Max(0, 7 - ed) / 7; rx += ex / ed * w; rz += ez / ed * w; }
            }
        // Round what is solid, not into it (GroundPath): the route is found again every 3 s, or when the goal moves.
        routeT -= dt;
        if (route == null || routeT <= 0 || routeFor != (pin.X, pin.Z))
        {
            routeT = 3; routeFor = (pin.X, pin.Z);
            route = SurvivorUnchained.Sim.GroundPath.Find(b.Collision, p.X, p.Z, pin.X, pin.Z);
            if (route == null) Godot.GD.Print($"auto: no route to {pin.Def.Pin} from ({p.X:0.0},{p.Z:0.0})");
        }
        while (route is { Count: > 1 } && Math.Sqrt((route[0].X - p.X) * (route[0].X - p.X) + (route[0].Z - p.Z) * (route[0].Z - p.Z)) < 0.8) route.RemoveAt(0);
        double sx = dx / d, sz = dz / d;
        if (route is { Count: > 0 })
        {
            double wx = route[0].X - p.X, wz = route[0].Z - p.Z, wd = Math.Max(0.01, Math.Sqrt(wx * wx + wz * wz));
            sx = wx / wd; sz = wz / wd;
        }
        Steer(dt, sx + rx * 0.5, sz + rz * 0.5, p, pin.X, pin.Z);
        dashT -= dt;
        if (close >= 4 && dashT <= 0 && p.DashCharges > 0) { Press(Act.Dash); dashT = 0.8; }
        return true;
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
