using SurvivorUnchained.Play.Pilots;
using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>One map to play: who, how hard, with what character, under which mods.</summary>
public sealed record MapRunSpec(int Seed, string Calling, int Tier, string People, int Level, int GearRarity, string[] Mods, string Bot, double Cap = 25, string Dungeon = "", bool AtBoss = false)
{
    /// <summary>(M3) The hands: human, deft, careless, standing, idler (the press plan's) or plain (the old self-firing Pilot).</summary>
    public bool Deft => Bot == "deft";
    public string Key => $"{Calling}/t{Tier}/{People}/{Bot}/s{Seed}/L{Level}/g{GearRarity}{(Mods.Length > 0 ? "/" + string.Join("+", Mods) : "")}{(Dungeon != "" ? "/dg:" + Dungeon : "")}{(AtBoss ? "/boss" : "")}";
}

public sealed class MapRunResult
{
    public MapRunSpec Spec = null!;
    public bool Cleared, Closed;
    public double Minutes, LowHp = 1, DamageTaken;
    /// <summary>(M3) What her feet did in the fights (Pilot.Meter).</summary>
    public Pilot.FeetMeter Feet = new();
    public int Falls, Kills, Packs, PacksCleared, Quaffs, Items, Charts, Gold;
    /// <summary>(Ledge kills) Her credited kills in the run, and how many of them were foes forced over an edge.</summary>
    public int AllKills, LedgeKills;
    /// <summary>What crafting reads (docs/CRAFTING_DESIGN.md 20.1): the people's own material and the
    /// ember shards picked up, the old iron the gear would break down to, and the rulers' Marks.</summary>
    public int Material, Shards, Iron, Marks;
    public double? BossTtk;
    public int BossPhase;
    /// <summary>What was left of the ruler when the map closed (-1: never met).</summary>
    public double BossLeft = -1;
    /// <summary>Seconds between kills, and between packs put down (the experience lead's rhythm:
    /// a kill or find every 10-20 s, a pack every 20-40 s).</summary>
    public double KillGap, PackGap;
    public string Build = "", KilledBy = "";
    public double MaxHp;
    /// <summary>(M3) The press plan's hands (presses by skill) and the numbers round's measures (RunMeter).</summary>
    public PressHands? Hands;
    public RunMeasures Measures = new();
    /// <summary>(dungeon-fights) XP paid in the run, the level at its start and end, the minute of each level-up.</summary>
    public double XpGained;
    public int LevelStart, LevelEnd;
    public List<double> LevelUpAt = new();
    /// <summary>Gear picked up, by rarity (0 plain .. 5).</summary>
    public int[] DropsByRarity = new int[6];
    /// <summary>Seconds with a roused foe within 24 m, in the rooms' fights and in the ruler's; marks laid on her in each;
    /// the longest stretch of fight time with none (whole fight clock, from its first second).</summary>
    public double FightSec, FightRoomSec, FightBossSec, GapAll, GapRoom, GapBoss;
    public int MarksRoom, MarksBoss;
    /// <summary>Heavy marks (the telegraph kit's, a boss's or a named one: the blows that bite when stood in): counts in rooms and at the ruler, and the longest fight stretch with none.</summary>
    public int HeavyRoom, HeavyBoss;
    public double HeavyGapRoom, HeavyGapBoss;
    /// <summary>What the campaign taught her in the run: "minute level skill" for each (Ev.Taught) and each level reached.</summary>
    public List<string> Taught = new();
    /// <summary>Where she fell: the room's role and plan (or hall), the killer, the ruler's phase (-1: ruler not up), the fight clock.</summary>
    public string DeathRoom = "", DeathPlan = "";
    public int DeathBossPhase = -1;
    /// <summary>Per room role: seconds in it, fight seconds, marks laid on her, rooms entered, entered rooms with no mark, damage taken (max lives).</summary>
    public Dictionary<string, RoleStat> Roles = new();
    /// <summary>The ruler's fight alone: damage to it by source (% of its life lost), and how long it was up.</summary>
    public Dictionary<string, double> BossShare = new();
    public double BossUpSec;
}

public sealed class RoleStat { public double Sec, FightSec, Dmg; public int Marks, Visits, QuietVisits; }

/// <summary>A Wayfinder's map played through headless (Play/Zones/MapRun.cs on MapGen's winding
/// way): the survivor's own build, kept for good, walked along the way by the Pilot's hands,
/// fighting what wakes, to the ruler at the end.</summary>
public static class MapSim
{
    const double Dt = 1 / 60.0;

    /// <summary>A listener on every frame of a run (the run clock, its drained events, the battle, whether a ruler is up): the sound
    /// lane's den log (tests/DenSoundRunTests.cs). Null: none. Per thread, so a parallel test's runs never reach it.</summary>
    [ThreadStatic] public static Action<double, IReadOnlyList<CombatEvent>, Battle, bool>? Tap;
    /// <summary>(P3) The run's zone, once begun (DenFeel reads its packs). Per thread, as Tap.</summary>
    [ThreadStatic] public static Action<MapRun>? ZoneTap;
    /// <summary>(P3, measuring only) Called each step before the hands act (DenFeel's opener variant presses there). Null: none.</summary>
    [ThreadStatic] public static Action<Battle>? PreAct;

    /// <summary>A survivor at a level, as a player would have dressed them by then: the calling's own
    /// path's skills at the day's rank, as many as the level's slots hold, the points in the calling's attribute, and plain gear
    /// at a rarity in every slot.</summary>
    public static Journey Survivor(string calling, int level, int gearRarity, int seed)
    {
        var a = Callings.Archetype(calling);
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = calling, Background = "hunter", Palette = a.Palettes[0].Id,
            WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, (uint)seed);
        // (M3) The dressing is Play/DevVeteran.cs's, shared with the game's --veteran: one build under the same arguments.
        // MAP_BARE=1 (a measuring aid): the game's old `--xp` veteran instead, the level alone (points unspent, no gear,
        // the journey's one draught), to show what a clip of it was measuring.
        if (Bare) { var ch = j.Ch; while (ch.Level < level) Character.GainXp(ch, Character.XpForLevel(ch.Level) - ch.Xp + 1); }
        else DevVeteran.Dress(j.Ch, level, gearRarity, seed);
        return j;
    }

    public static MapRunResult Play(MapRunSpec spec)
    {
        var j = Survivor(spec.Calling, spec.Level, spec.GearRarity, spec.Seed);
        if (!Bare) DevVeteran.Belt(j.Ch);
        // (bd-sockets) --drop a,b: those skills off her bar (to measure what one adds)
        foreach (var d in VergeZoneSim.Drop) SkillBook.Unslot(j.Ch, d);
        var chart = new Chart { Tier = spec.Tier, People = spec.People, Seed = spec.Seed * 7919 + spec.Tier, Mods = spec.Mods.ToList(), Rarity = spec.Mods.Length == 0 ? 0 : spec.Mods.Length <= 2 ? 1 : 2, Name = "The Harness Map" };
        if (spec.Dungeon != "") chart = Chart.ForDungeon(DungeonGen.Get(spec.Dungeon)!, spec.Seed * 7919 + 1, spec.Level);
        var map = MapGen.Generate(chart.Map);
        if (Environment.GetEnvironmentVariable("MAP_PROBE") is { Length: > 0 } pr)
        {
            // MAP_PROBE=x,z,r: the solid pieces within r m of a point (what an enemy or she is held by there).
            var q = pr.Split(',').Select(v => double.Parse(v, System.Globalization.CultureInfo.InvariantCulture)).ToArray();
            foreach (var c in map.Meta.Colliders) if (MathX.Dist(c.X, c.Z, q[0], q[1]) < q[2] + c.R + Math.Max(c.Hw, c.Hd))
                Console.Error.WriteLine($"PROBE collider {c.Kind} {c.Tag} at ({c.X:0.0},{c.Z:0.0}) r {c.R:0.0} hw {c.Hw:0.0} hd {c.Hd:0.0} rot {c.Rot:0.00} soft {c.Soft} playerOnly {c.PlayerOnly}");
            foreach (var pp in map.Props) if (MathX.Dist(pp.X, pp.Z, q[0], q[1]) < q[2] + 3) Console.Error.WriteLine($"PROBE prop {pp.Id} at ({pp.X:0.0},{pp.Z:0.0}) scale {pp.Scale:0.00}");
            if (map.Dungeon != null) foreach (var rm in map.Dungeon.Rooms) { double d = rm.Dist(q[0], q[1]); if (d > -6) Console.Error.WriteLine($"PROBE room {rm.Role} {rm.Plan.Id} dist {d:0.0} holes {rm.Holes.Length}"); }
        }
        if (Environment.GetEnvironmentVariable("MAP_SIG") == "1") Console.Error.WriteLine(Signature(spec, map));
        var host = new HeadlessHost(j, spec.Seed);
        var zone = new MapRun(host, map, chart);
        var at = zone.ArrivalFrom(null);
        // (dungeon-fights) --at boss, as the game's: on the edge of the ruler's clearing, nothing else met.
        if (spec.AtBoss) { var (ax, az) = map.BossEdge(map.Meta.Collision()); at = new Arrival(ax, az, 0); }
        // (worldTier false, as the game starts a map: Game.cs; its press is the chart tier's row, set in MapRun.Begin)
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)spec.Seed, worldTier: false);
        // As the game wires it: what is picked up goes into the pack (charts and materials); gear is
        // counted and stashed, so the pack never fills and leaves a piece lying under the hands.
        var zh = zone.Hooks;
        b.Hooks = BattleHooks.Following(zh);
        // MAP_LEDGE=0: the ledge-kill rule off (what it changes, measured against the same seeds).
        if (Environment.GetEnvironmentVariable("MAP_LEDGE") == "0") b.LedgeKills = false;
        // (dungeon-fights) As the game wires it (Game.cs HookBattle): a kill teaches her first, then the zone sees it. Dungeons only: the old map numbers stay.
        if (spec.Dungeon != "") b.Hooks.OnKill = (e, byPlayer) => { j.Killed(e, byPlayer); zh.OnKill?.Invoke(e, byPlayer); };
        int gear = 0, iron = 0, marks = 0;
        var r0Drops = new int[6];
        b.Hooks.OnPickup = pk =>
        {
            if (zh.OnPickup != null && !zh.OnPickup(pk)) return false;
            if (pk.Kind == PickupKind.Item && pk.Ref != null && Crafting.MarkOf(pk.Ref) != null) { marks++; return true; }
            if (pk.Kind == PickupKind.Item && pk.Ref != null && Charts.FromRef(pk.Ref) == null)
            {
                gear++;
                int rarity = pk.Payload is ItemInstance it ? it.Rarity : (int)pk.Tier;
                r0Drops[Math.Clamp(rarity, 0, 5)]++;
                iron += Crafting.Rules.BreakDown[Math.Clamp(rarity, 0, Crafting.Rules.BreakDown.Count - 1)];
                return true;
            }
            j.PickedUp(pk);
            return true;
        };
        host.Battle = b;
        zone.Begin(b);
        if (ForceLamps != null) LightForced(b);
        ZoneTap?.Invoke(zone);
        // (M3) --grant / --grant-union / --dash-steps: the game's dev grants (Sim/DevGrants.cs), carried from the start. A grant
        // the keys cannot hold takes the last key that is not the grip's nor the union's part.
        if (Grant != null || GrantUnion != null) GiveGrants(b, spec);
        // (her, one line, as the game's --auto --clip prints it: the same line, the same build)
        if (System.Threading.Interlocked.Increment(ref herSaid) <= 2) Console.WriteLine($"{spec.Key}: {DevVeteran.Line(b, j)}");
        var r = new MapRunResult { Spec = spec, Packs = zone.PackCount, MaxHp = b.MaxHp, Build = string.Join(" ", b.Weapons.Select(w => $"{w.Id}{w.Rank}")) };
        var nav = new NavField(map, b, map.Boss.X, map.Boss.Z);
        double along = 0;
        var p = b.Player;
        double t = 0, lastKill = 0, lastPack = 0, stuck = 0, bestToGo = double.MaxValue, clearedAt = -1;
        int holds = 0;
        int lastCleared = 0;
        var kills = new List<double>();
        bool trace = Environment.GetEnvironmentVariable("MAP_TRACE") == "1", blows = Environment.GetEnvironmentVariable("MAP_BLOWS") == "1", hits = Environment.GetEnvironmentVariable("MAP_HITS") == "1";
        // MAP_HITS=1: every blow that lands on her (all fights, not the ruler's only); MAP_TRACE_EVERY=s: seconds between trace lines (default 10).
        double traceEvery = double.TryParse(Environment.GetEnvironmentVariable("MAP_TRACE_EVERY"), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var te) && te > 0 ? te : 10;
        var foeWin = Environment.GetEnvironmentVariable("MAP_FOE") is { Length: > 0 } fw ? fw.Split(',').Select(v => double.Parse(v, System.Globalization.CultureInfo.InvariantCulture)).ToArray() : null;
        var packs = new List<double>();
        // (M3) The hands on the one press plan (Sim/PressPlan.cs), as ZoneSim's.
        var human = spec.Bot is "human" or "careless" or "idler" ? new Human(spec.Seed, spec.Bot == "careless") { Idle = spec.Bot == "idler" } : null;
        if (human == null && spec.Bot is not ("deft" or "plain" or "standing")) throw new ArgumentException($"map sim: unknown bot {spec.Bot}");
        uint hs = (uint)spec.Seed;
        var hands = spec.Bot switch
        {
            "deft" => PressHands.Deft(hs),
            "human" => PressHands.Human(hs, human!.React),
            "careless" => PressHands.Careless(hs, human!.React),
            "standing" or "idler" => PressHands.Grip(hs),
            _ => null,
        };
        if (human != null) human.Hands = hands;
        r.Hands = hands;
        var meter = new RunMeter();
        // (dungeon-fights) the fight clock, the marks and the rooms.
        double TotalXp(CharacterData c) { double x = c.Xp; for (int l = 1; l < c.Level; l++) x += Character.XpForLevel(l); return x; }
        double xp0 = TotalXp(j.Ch); int lv0 = j.Ch.Level, lvNow = lv0;
        r.LevelStart = lv0;
        double fRoom = 0, fBoss = 0, lastMk = 0, lastMkRoom = 0, lastMkBoss = 0, bossUp = 0, lastHvRoom = 0, lastHvBoss = 0;
        var dg = map.Dungeon;
        DungeonRoom? inRoom = null; RoleStat? rs = null; bool visitMarked = false;
        int step = 0;
        while (t < spec.Cap * 60 && !zone.Over)
        {
            if (dg != null && step++ % 15 == 0)
            {
                DungeonRoom? best = null; double bd = 0;
                foreach (var rm in dg.Rooms) { double d = rm.Dist(p.X, p.Z); if (d < bd) { bd = d; best = rm; } }
                if (best != inRoom)
                {
                    if (rs != null && !visitMarked) rs.QuietVisits++;
                    inRoom = best; visitMarked = false;
                    rs = null;
                    if (best != null)
                    {
                        string key = best.Role.ToString();
                        if (!r.Roles.TryGetValue(key, out rs)) r.Roles[key] = rs = new RoleStat();
                        rs.Visits++;
                    }
                    else { if (!r.Roles.TryGetValue("Hall", out rs)) r.Roles["Hall"] = rs = new RoleStat(); rs.Visits++; }
                }
            }
            // Onward: downhill on the way's distance to the ruler, a few metres ahead, by a line
            // that is clear of what stands on the ground.
            var onward = nav.Onward(p.X, p.Z);
            along = nav.ToGo(p.X, p.Z);
            double reach = Math.Max(1.5, Pilot.Reach(b));
            bool inReach = b.Enemies.Living().Any(e => e.Disposition == Disposition.Hostile && e.State != EnemyState.Dying && Dist(e.X, e.Z, p.X, p.Z) < reach);
            var (mx, mz) = spec.Bot switch
            {
                "idler" => human!.Steer(b, zone.BossScript, goal: inReach ? null : onward),
                "human" or "careless" => human!.Steer(b, zone.BossScript, onward: onward),
                "standing" => inReach ? (0, 0) : Pilot.Steer(b, false, null, goal: onward, naive: true),
                _ => Pilot.Steer(b, spec.Deft, zone.BossScript, onward),
            };
            // No nearer the ruler in twenty seconds with the ruler not up (a pickup out of reach, a
            // corner, a tunneller under the ground the hands wait on): walk on, longer each time.
            if ((int)(t / 20) != (int)((t + Dt) / 20))
            {
                if (zone.Boss == null && !double.IsNaN(along) && along > bestToGo - 3)
                {
                    holds++;
                    stuck = 4 * Math.Pow(2, Math.Min(3, holds - 1));
                }
                else holds = 0;
                if (!double.IsNaN(along)) bestToGo = Math.Min(bestToGo, along);
            }
            if (stuck > 0)
            {
                stuck -= Dt;
                (mx, mz) = (onward.X - p.X, onward.Z - p.Z);
                double ml = Math.Max(1e-6, Math.Sqrt(mx * mx + mz * mz));
                (mx, mz) = (mx / ml, mz / ml);
            }
            PreAct?.Invoke(b);
            bool quaff = human != null ? human.Act(b, j, mx, mz, zone.BossScript)
                : spec.Bot == "standing" ? Pilot.Act(b, j, mx, mz, null, lunges: false, aimsFlare: true, rooted: false, crush: false, hands: hands)
                : Pilot.Act(b, j, mx, mz, hands: hands);
            if (quaff) r.Quaffs++;
            zone.Step(Dt);
            zone.Frame(Dt);
            b.Tick(Dt, mx, mz);
            var evs = b.Events.Drain();
            Tap?.Invoke(t, evs, b, zone.Boss != null);
            bool fighting = RunMeter.Fighting(b);
            meter.Step(b, t, Dt, evs, fighting);
            fighting |= zone.Boss != null;
            {
                bool bossNow = zone.Boss != null;
                if (bossNow) bossUp += Dt;
                if (rs != null) { rs.Sec += Dt; if (fighting) rs.FightSec += Dt; }
                if (fighting) { if (bossNow) fBoss += Dt; else fRoom += Dt; }
                double fAll = fRoom + fBoss;
                foreach (var ev in evs)
                {
                    if (ev is Ev.Telegraph { Hostile: true, Phase: TellPhase.Warn } tg && ArenaSim.Covers(tg, p.X, p.Z, p.Radius))
                    {
                        r.GapAll = Math.Max(r.GapAll, fAll - lastMk); lastMk = fAll;
                        if (bossNow) { r.MarksBoss++; r.GapBoss = Math.Max(r.GapBoss, fBoss - lastMkBoss); lastMkBoss = fBoss; }
                        else { r.MarksRoom++; r.GapRoom = Math.Max(r.GapRoom, fRoom - lastMkRoom); lastMkRoom = fRoom; }
                        if (rs != null) { rs.Marks++; visitMarked = true; }
                        if (tg.Boss || tg.Tell != null || tg.Label != null)
                        {
                            if (bossNow) { r.HeavyBoss++; r.HeavyGapBoss = Math.Max(r.HeavyGapBoss, fBoss - lastHvBoss); lastHvBoss = fBoss; }
                            else { r.HeavyRoom++; r.HeavyGapRoom = Math.Max(r.HeavyGapRoom, fRoom - lastHvRoom); lastHvRoom = fRoom; }
                        }
                    }
                    else if (ev is Ev.Taught tt) r.Taught.Add($"{t / 60:0.0}m L{j.Ch.Level} {tt.Skill}->{(tt.Slot < 0 ? "carried" : "slot " + tt.Slot)}");
                    else if (ev is Ev.LevelUp lu) r.Taught.Add($"{t / 60:0.0}m reached L{lu.Level}");
                    else if (ev is Ev.PlayerHit ph && rs != null && ph.Amount > 0) rs.Dmg += ph.Amount / Math.Max(1, b.MaxHp);
                    else if (ev is Ev.PlayerDeath)
                    {
                        r.DeathRoom = inRoom != null ? inRoom.Role.ToString() : dg != null ? "Hall" : "";
                        r.DeathPlan = inRoom?.Plan.Id ?? "";
                        r.DeathBossPhase = bossNow ? (zone.BossScript?.PhaseIx ?? 0) : -1;
                    }
                }
                if (j.Ch.Level > lvNow) { for (; lvNow < j.Ch.Level; lvNow++) r.LevelUpAt.Add(t / 60); }
            }
            foreach (var ev in evs)
                switch (ev)
                {
                    case Ev.Kill k when k.ByPlayer: kills.Add(t - lastKill); lastKill = t; break;
                    case Ev.PlayerDeath d: r.KilledBy = d.Killer; break;
                    // MAP_BLOWS=1: the blows that land in the ruler's fight (why its fight was lost).
                    case Ev.PlayerHit ph when (blows && zone.Boss != null) || hits:
                        Console.Error.WriteLine($"{t / 60:0.000} {ph.Source,-22} {ph.Amount,6:0} {(ph.Dodged ? "dodged" : "")} hp {p.Hp:0}/{b.MaxHp:0} phase {zone.BossScript?.PhaseIx}");
                        break;
                }
            host.Pass(Dt);
            r.LowHp = Math.Min(r.LowHp, p.Hp / b.MaxHp);
            if (zone.PacksCleared > lastCleared) { packs.Add(t - lastPack); lastPack = t; lastCleared = zone.PacksCleared; }
            // Cleared: what the ruler left picked up (a few seconds), then the way out.
            if (zone.Cleared && clearedAt < 0) clearedAt = t;
            if (zone.Cleared && !zone.Over && t - clearedAt > 8) zone.Leave();
            if (!p.Alive) break;
            // MAP_FOE=from,to (minutes): every tick the ruler's place, speed and whether it overlaps solid (why a foe sits where it does).
            if (foeWin != null && t / 60 >= foeWin[0] && t / 60 <= foeWin[1] && zone.Boss is { } fb)
                Console.Error.WriteLine($"FOE {t / 60:0.0000} ({fb.X:0.000},{fb.Z:0.000}) r {fb.Radius:0.00} v ({fb.Vx:0.00},{fb.Vz:0.00}) kb ({fb.Kbx:0.0},{fb.Kbz:0.0}) {fb.State} {fb.Anim} blocked {b.Collision.Blocked(fb.X, fb.Z, fb.Radius)} flow {(b.Flow.Dir(fb.X, fb.Z, out var ffx, out var ffz) ? $"({ffx:0.00},{ffz:0.00})" : "none")} her ({p.X:0.00},{p.Z:0.00})");
            // MAP_TRACE=1: where the hands are every ten seconds (why a map was not finished).
            if (trace && (int)(t / traceEvery) != (int)((t + Dt) / traceEvery))
                Console.Error.WriteLine($"{t / 60:0.00} at ({p.X:0.0},{p.Z:0.0}) m ({mx:0.00},{mz:0.00}) v ({p.Vx:0.0},{p.Vz:0.0}) blocked {b.Collision.Blocked(p.X, p.Z, p.Radius)} leap {p.Leap != null} dash {p.DashT:0.00} slow {p.SlowF:0.00} spd {b.Stats.Get(Stat.MoveSpeed):0.0} over {b.Over} stuck {stuck:0.0} to go {along:0} m onward ({onward.X:0},{onward.Z:0}) roused {b.Enemies.Living().Count(e => e.Disposition == Disposition.Hostile && (e.Wake == 0 || e.Roused))} hp {p.Hp:0}/{b.MaxHp:0} packs {zone.PacksCleared}/{zone.PacksPlaced}" + Near(b, p));
            t += Dt;
        }
        {
            double fAll = fRoom + fBoss;
            r.GapAll = Math.Max(r.GapAll, fAll - lastMk); r.GapRoom = Math.Max(r.GapRoom, fRoom - lastMkRoom); r.GapBoss = Math.Max(r.GapBoss, fBoss - lastMkBoss);
            r.HeavyGapRoom = Math.Max(r.HeavyGapRoom, fRoom - lastHvRoom); r.HeavyGapBoss = Math.Max(r.HeavyGapBoss, fBoss - lastHvBoss);
            (r.FightSec, r.FightRoomSec, r.FightBossSec, r.BossUpSec) = (fAll, fRoom, fBoss, bossUp);
            if (rs != null && !visitMarked) rs.QuietVisits++;
            r.XpGained = TotalXp(j.Ch) - xp0; r.LevelEnd = j.Ch.Level;
            Array.Copy(r0Drops, r.DropsByRarity, 6);
            double bl = b.BossHealthBy.Values.Sum();
            if (bl > 0) foreach (var (k, v) in b.BossHealthBy) r.BossShare[k] = 100 * v / bl;
        }
        r.Cleared = zone.Cleared;
        r.Closed = !zone.Cleared && (zone.Falls >= MapRun.FallsAllowed || !p.Alive);
        r.Minutes = (clearedAt >= 0 ? clearedAt : t) / 60;
        r.Falls = zone.Falls;
        r.Kills = zone.Kills;
        r.AllKills = b.KillCount; r.LedgeKills = b.LedgeKillCount;
        r.PacksCleared = zone.PacksCleared;
        r.BossTtk = zone.Result?.BossTtk;
        r.BossPhase = zone.BossScript?.PhaseIx ?? -1;
        if (zone.Boss is { } zb && zone.BossScript != null) r.BossLeft = zb.Hp / zone.BossScript.MaxHp;
        r.DamageTaken = b.DamageTaken;
        r.KillGap = Median(kills);
        r.PackGap = Median(packs);
        r.Items = gear;
        r.Charts = j.Ch.Pack.Count(i => i?.Chart != null) + j.Ch.Satchel.Count(i => i.Chart != null);
        r.Gold = (int)j.Ch.Gold;
        r.Shards = j.Ch.Materials.GetValueOrDefault(Crafting.Shard);
        r.Iron = iron + j.Ch.Materials.GetValueOrDefault(Crafting.Iron);
        r.Material = j.Ch.Materials.Where(m => m.Key != Crafting.Shard && m.Key != Crafting.Iron).Sum(m => m.Value);
        r.Marks = marks;
        meter.Finish(b, t, r.Measures, hands);
        r.Feet = Pilot.Meter(b);
        r.Feet.StandCharges = zone.StandCharges;
        return r;
    }

    /// <summary>(M3) --grant id[:rank],... / --grant-union id: what every map starts carrying (as ArenaSim's).</summary>
    public static string? Grant, GrantUnion;
    /// <summary>--lamps "sunder.stroke.1-4,leap.x.1": lamps lit before the fight (harness only; null = the default build).</summary>
    public static string? ForceLamps;

    static void LightForced(Battle b)
    {
        var bySkill = new Dictionary<string, List<string>>();
        foreach (var item in ForceLamps!.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            var parts = item.Split('.');
            if (parts.Length < 3) throw new ArgumentException($"--lamps {item}: skill.strand.n or skill.strand.a-b");
            var range = parts[^1].Split('-');
            int lo = int.Parse(range[0]), hi = range.Length > 1 ? int.Parse(range[1]) : lo;
            string skill = parts[0], strand = string.Join('.', parts[1..^1]);
            if (!bySkill.TryGetValue(skill, out var l)) bySkill[skill] = l = new();
            for (int n = lo; n <= hi; n++) l.Add($"{skill}.{strand}.{n}");
        }
        foreach (var (skill, ids) in bySkill)
        {
            var path = SurvivorUnchained.Rpg.WickBook.Path(ids, skill);
            var w = b.Weapons.Find(x => x.Id == skill) ?? throw new ArgumentException($"--lamps: {skill} is not on her bar");
            b.LightHeld(skill, Math.Max(w.Rank, ids.Count), path);
        }
    }
    static int grantSaid, herSaid;
    /// <summary>MAP_SIG=1: one line per map that changes if its rooms, its walkable cells, its packs or its solid pieces change (to compare two builds of the generator).</summary>
    static string Signature(MapRunSpec spec, MapBuild map)
    {
        static uint H(uint h, string x) { foreach (char c in x) h = (h ^ c) * 16777619u; return h; }
        uint rooms = 2166136261u, walk = 2166136261u, packs = 2166136261u, cols = 2166136261u, props = 2166136261u;
        int cells = 0;
        if (map.Dungeon != null) foreach (var r in map.Dungeon.Rooms) rooms = H(rooms, $"{r.Area} {r.Plan.Id} {r.X:0.00} {r.Z:0.00} {r.Rot:0.00} {r.Scale:0.00} {r.Holes.Length}");
        for (int i = 0; i < map.Walkable.Length; i++) { if (map.Walkable[i]) cells++; walk = H(walk, map.Walkable[i] ? "1" : "0"); }
        foreach (var k in map.Packs) packs = H(packs, $"{k.Area} {k.X:0.0} {k.Z:0.0} {k.Size:0.00}");
        foreach (var c in map.Meta.Colliders) cols = H(cols, c.ToString());
        foreach (var q in map.Props) props = H(props, $"{q.Id} {q.X:0.0} {q.Z:0.0}");
        return $"SIG {spec.Dungeon} s{spec.Seed}: rooms {map.Dungeon?.Rooms.Count} #{rooms:x8} | walkable {cells} #{walk:x8} | packs {map.Packs.Count} #{packs:x8} | colliders {map.Meta.Colliders.Count} #{cols:x8} | props {map.Props.Count} #{props:x8}";
    }

    /// <summary>MAP_TRACE: the nearest roused hostile (kind, distance, life, state, whether a wall stands between).</summary>
    static string Near(Battle b, PlayerState p)
    {
        Enemy? best = null; double bd = 1e9;
        foreach (var e in b.Enemies.Living()) if (e.Disposition == Disposition.Hostile && (e.Wake == 0 || e.Roused)) { double d = MathX.Dist(e.X, e.Z, p.X, p.Z); if (d < bd) { bd = d; best = e; } }
        return best == null ? "" : $" | near {best.Def.Name} {bd:0.0} m hp {best.Hp:0}/{best.MaxHp:0} at ({best.X:0.0},{best.Z:0.0}) {best.State} {best.Anim} solid {b.Collision.Blocked(best.X, best.Z, best.Radius)}";
    }

    static readonly bool Bare = Environment.GetEnvironmentVariable("MAP_BARE") == "1";

    static void GiveGrants(Battle b, MapRunSpec spec)
    {
        // (the rule is the game's now, Sim/DevGrants.MakeRoom; the grip kept here is the taught build's, as it was)
        var said = DevGrants.MakeRoom(b, Grant, GrantUnion, TaughtBuilds.Of(spec.Calling) is { } t ? new[] { t.Grip } : Array.Empty<string>());
        said.AddRange(DevGrants.Apply(b, Grant, GrantUnion, null, makeRoom: false));
        foreach (var line in said) if (System.Threading.Interlocked.Increment(ref grantSaid) <= 4 || line.Contains("not ")) Console.WriteLine($"{spec.Key}: {line}");
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));

    static double Median(List<double> xs)
    {
        if (xs.Count == 0) return double.NaN;
        var s = xs.OrderBy(x => x).ToList();
        return s[s.Count / 2];
    }

    public static string Report(List<MapRunResult> rs)
    {
        var sb = new System.Text.StringBuilder();
        sb.AppendLine("| group | runs | cleared | closed | falls/run | minutes | boss TTK (s) | kill gap (s) | pack gap (s) | lowest | items | charts | gold | material | shards | iron | marks |");
        sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|");
        void Row(string name, List<MapRunResult> l)
        {
            if (l.Count == 0) return;
            double M(IEnumerable<double> xs) { var a = xs.Where(x => !double.IsNaN(x)).OrderBy(x => x).ToList(); return a.Count == 0 ? double.NaN : a[a.Count / 2]; }
            sb.AppendLine($"| {name} | {l.Count} | {100 * l.Count(x => x.Cleared) / l.Count}% | {100 * l.Count(x => x.Closed) / l.Count}% | {l.Average(x => x.Falls):0.00} | {M(l.Where(x => x.Cleared).Select(x => x.Minutes)):0.0} | {M(l.Where(x => x.BossTtk != null).Select(x => x.BossTtk!.Value)):0} | {M(l.Select(x => x.KillGap)):0.0} | {M(l.Select(x => x.PackGap)):0} | {M(l.Select(x => x.LowHp)):0.00} | {M(l.Select(x => (double)x.Items)):0} | {M(l.Select(x => (double)x.Charts)):0} | {M(l.Select(x => (double)x.Gold)):0} | {M(l.Select(x => (double)x.Material)):0} | {M(l.Select(x => (double)x.Shards)):0} | {M(l.Select(x => (double)x.Iron)):0} | {l.Average(x => x.Marks):0.0} |");
        }
        Row("all", rs);
        foreach (var g in rs.GroupBy(x => $"tier {x.Spec.Tier}").OrderBy(g => g.Key)) Row(g.Key, g.ToList());
        foreach (var g in rs.GroupBy(x => x.Spec.Calling).OrderBy(g => g.Key)) Row(g.Key, g.ToList());
        foreach (var g in rs.GroupBy(x => x.Spec.People).OrderBy(g => g.Key)) Row(g.Key, g.ToList());
        foreach (var g in rs.GroupBy(x => x.Spec.Bot).OrderBy(g => g.Key)) Row(g.Key, g.ToList());
        // (M3) The press measures, per bot and tier.
        sb.AppendLine();
        sb.AppendLine(RunMeasures.Header);
        foreach (var g in rs.GroupBy(x => (x.Spec.Tier, x.Spec.Bot)).OrderBy(g => g.Key)) sb.AppendLine(RunMeasures.Row($"T{g.Key.Tier} {g.Key.Bot}", g.Select(x => x.Measures).ToList()));
        return sb.ToString();
    }
}
