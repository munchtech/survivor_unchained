using SurvivorUnchained.Play.Pilots;
using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>One arena to play: who, how they draft, where, how long; the
/// survivor's character level (points in the calling's own attribute), and
/// whether the hands are deft (they read lunges, pots and burning ground as a
/// player who knows the fight does: a death is then the game's, not the bot's).</summary>
public sealed record RunSpec(int Seed, string Calling, string Policy, int Tier = 1, string People = "pack", string[]? Oaths = null,
    double Cap = 40, double Beyond = 0, int Weapon = 0, int Art = 0, int Level = 1, bool Deft = false, double Minutes = 30,
    string Type = "", string Lamps = "empty", string For = "", string Flare = "", string Bot = "",
    [property: System.Text.Json.Serialization.JsonIgnore(Condition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingDefault)] bool OneBuild = false)
{
    public string Key => $"{Calling}/{Policy}/t{Tier}/{People}/s{Seed}/w{Weapon}" + (Level > 1 ? $"/L{Level}" : "") + (Deft ? "/deft" : "") +
        (Oaths is { Length: > 0 } ? $"/{string.Join("+", Oaths)}" : "") + (Minutes != 30 ? $"/m{Minutes:0}" : "") +
        (Type != "" ? $"/{Type}" : "") + (Lamps != "empty" ? $"/lamps-{Lamps}" : "") + (For != "" ? $"/for-{For}" : "") + (Flare != "" ? $"/flare-{Flare}" : "") + (Bot != "" ? $"/{Bot}" : "") + (OneBuild ? "/onebuild" : "");
}

/// <summary>A minute of the fight, as the harness saw it.</summary>
public sealed class Minute
{
    public int Ember, Kills, Alive, Drafts;
    public double Damage, Taken, LowHp = 1, TtkFodder, TtkFodder90, TtkElite;
    /// <summary>The horde's charges: runs started, the most at once, seconds with three or
    /// more at once, and spikes (Sim/Charges.cs).</summary>
    public int Charges, ChargePeak, Spikes;
    public double Overlap;
}

public sealed class RunResult
{
    public RunSpec Spec = null!;
    public double? WonAt;
    public bool Died;
    public double Minutes;
    public int Kills, Ember, Cards, Respites, Rerolls, Banishes, Skips;
    public string KilledBy = "", Build = "", Path = "";
    public double DamageTaken, LowHp = 1;
    /// <summary>The late hands' threats met and read (Harness/Human.cs); her life at the end (of her most); her hits a
    /// fodder and a champion took to fall, the median over the first ten ember levels (H1: 2-4 and 8-12 at tier 1).</summary>
    public int ThreatsMet, ThreatsRead;
    public double HpEnd = 1, HitsFodder = double.NaN, HitsElite = double.NaN;
    public double? BossTtk;
    public List<double> HeraldTtk = new();
    public List<Minute> ByMinute = new();
    public Dictionary<string, double> DamageBy = new();
    /// <summary>Her damage uncapped by the creatures' health (Battle.DamageRaw).</summary>
    [System.Text.Json.Serialization.JsonIgnore] public double DamageRaw;
    public Dictionary<string, int> Offered = new(), Taken = new();
    /// <summary>Evolutions, with the minute each came.</summary>
    public List<(string Id, double At)> Evolved = new();
    /// <summary>The minute the arsenal was full and every combat skill evolved, if it was.</summary>
    public double? CompleteAt;
    /// <summary>Normal drafts with a card that ranks or evolves something carried; drafts in all.</summary>
    public int Advancing, NormalDrafts;
    public List<string> Greats = new();
    /// <summary>Every card taken, with the minute it was taken (for comparing runs that took a card early).</summary>
    public List<(string Card, double Minute)> Picks = new();
    /// <summary>What was left of the boss when the survivor fell to it (-1: it was not up).</summary>
    public double BossLeft = -1;
    public int Quaffs;
    /// <summary>The boss's fight: its telegraphed blows marked and landed, its Break (of its
    /// health), its staggers, the phase it reached, and whether it grew wild (three minutes).</summary>
    public int BossMarked, BossLanded, BossStaggers, BossPhase = -1;
    /// <summary>The telegraph kit (Sim/Tells.cs): its blows marked, and those that caught her as they landed.</summary>
    public int KitMarked, KitCaught;
    public double BossBreak;
    /// <summary>Each boss phase as it ended: [the Flare's cut, seconds, seconds to its mark or -1] (the last as the fight ended).</summary>
    public List<double[]> BossPhases = new();
    public bool BossSoft;
    /// <summary>The long night: the boss's returns that came, and the dark's oaths sworn.</summary>
    public int Returns, Dark;
    /// <summary>The Kindling's ember-core broken within its minute (null: it never came).</summary>
    public bool? CoreBroken;
    /// <summary>The minibosses met (by def) and those killed: how long each took, and the minute.</summary>
    public List<string> MinibossesMet = new();
    public List<(string Def, double Ttk, double At)> Minibosses = new();
    /// <summary>What the night pays (for the crafting economy, docs/CRAFTING_DESIGN.md):
    /// the gold picked up, the champions slain, and the slain by family.</summary>
    public double Gold;
    public int Champions;
    public Dictionary<string, int> KillsBy = new();
    /// <summary>The survivor's type (road) and the lamps lit (free ones too) at the start.</summary>
    public string Road = "";
    public int LampsLit;
    /// <summary>--onebuild: the skills carried from minute 0 (docs/design/ONE_BUILD.md). Null, and left out of the line, without the flag,
    /// so a run without it writes the same bytes as before the switch.</summary>
    [System.Text.Json.Serialization.JsonIgnore(Condition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull)]
    public string[]? Kit;
    /// <summary>The lit lamp ids (a measuring aid: which lamps a board carries).</summary>
    public string LampIds = "";
    /// <summary>The Flare: casts, the first cast's minute, the mean gap between casts (s), casts while a boss was up,
    /// its share of the damage done to bosses, clutch casts, and the meter's fill by source.</summary>
    public int FlareCasts, FlareBossCasts, FlareClutches;
    /// <summary>A board's lamp (H1 item 6B; Harness/LampHold.cs): null with no lamp tonight; else whether the hands held
    /// it, seconds she stood in its lit pool, its outs and relights, blows landed on her in its pool and out of it after
    /// it caught (with the seconds of each), and her Flare meter (in casts) as the boss came.</summary>
    public bool? LampHeld;
    /// <summary>H6: times surrounded (foes within 4 m in three or more of six sectors, held 2 s) and at what minutes;
    /// seconds so; marks laid on her from 0:45 to the boss, and the longest stretch without one.</summary>
    public int Surrounds, MarksOnHer;
    /// <summary>Times she stood inside a closing's walled ring as it rose (ringed by the pack, the gap her way out).</summary>
    public int Ringed;
    public double SurroundSec, MarkGapMax;
    /// <summary>Kit marks laid on her in each minute of the night (from 0:00, to the night's end).</summary>
    public List<int> MarksPerMin = new();
    public List<double> SurroundAt = new();
    /// <summary>Life she got back, by source (Battle.HealBy), and the damage that landed on her, by source.</summary>
    public Dictionary<string, double> HealBy = new(), HurtBy = new();
    public double LampPoolSec, LampOutSec, FlareAtBoss = double.NaN;
    public int LampOuts, LampRelights, LampHitsIn, LampHitsOut;
    /// <summary>The crowd's director (H6, ArenaRun.Director): pincers sent, surrounds closed on her, stand charges, stuck foes recalled.</summary>
    public int Flanks, SurroundCloses, StandCharges, Recalls, IronSpawns, IronSlams, Feeds;
    /// <summary>Casts whose blows reached a boss; the Flare's damage to bosses, and all damage to bosses.</summary>
    public int FlareCastsOnBoss;
    public int FlareFullBankShots;
    /// <summary>What each Flare did to the crowd round her (Battle.FlareCrowd's rows).</summary>
    public List<double[]> FlareCrowd = new();
    public double FlareBossDamage, BossDamage;
    /// <summary>The Flare's share of what was truly taken off bosses (health, and a gate's Break up to a tenth).</summary>
    public double FlareBossTook = double.NaN;
    /// <summary>Health taken off bosses (as FlareBossTook counts it), by source: each skill's share of a boss.</summary>
    public Dictionary<string, double> BossTookBy = new();
    /// <summary>A Stand's uplift on a boss: health taken off bosses while it held, and its seconds on a boss (Battle).</summary>
    public double StandTook, StandSeconds;
    /// <summary>The Bulwark's wall: blocks, rebukes, the most stones held at once.</summary>
    public int Blocks, Rebukes, StonesPeak;
    /// <summary>The Rebuke skill's strikes, the Watch Bell's tolls, and the barrier the bell gave.</summary>
    public int RebukeStrikes, Tolls;
    public double BellBarrier, MaxHpEnd;
    public double FlareFirst = double.NaN, FlareGap = double.NaN, FlareBossShare = double.NaN;
    public Dictionary<string, double> FlareFills = new();

    /// <summary>Won at the half hour and still standing for the boss: the target.</summary>
    public bool Won => WonAt != null;
}

/// <summary>An ember arena played through headless, as the game runs it
/// (Play/Zones/ArenaRun.cs on a map from MapGen), by the Pilot's hands and a
/// Picker's taste in cards.</summary>
public static class ArenaSim
{
    public const double Dt = 1 / 60.0;
    /// <summary>--charges 0: every charger on its own clock, as before the charge director.</summary>
    public static bool Director = true;
    /// <summary>Lamps lit past the board (--light; "{calling}" is the survivor's calling): a measuring aid,
    /// for a lamp Light my way never lights (Banked Flame).</summary>
    public static List<string> Light = new();
    /// <summary>--grant id[:rank],... and --grant-union id: what every arena starts carrying (DevGrants).</summary>
    public static string? Grant, GrantUnion;
    static int grantSaid;
    /// <summary>--dark: lamps put out after the board is lit (a Flare's modifiers one at a time on the full board; their points stay unspent).</summary>
    public static List<string> Dark = new();

    /// <summary>A measuring aid for the Hand pair (--pair): this fight's Hand on or off, the draft replayed
    /// from its twin (the cards it took, at the minutes it took them, so a Hand can't change the build), no
    /// falls (a fall stands her up at full health: low health still comes, the run's length doesn't change),
    /// and a fixed span of minutes. Null in every other run: the harness as it always was.</summary>
    public sealed class Fixed
    {
        public bool? Hand;
        public bool NoFall;
        /// <summary>A calibration: all her damage More by this (0: none), to read a metric's answer to a known x.</summary>
        public double DamageMore;
        /// <summary>Minutes to play, then stop (0: the run's own end).</summary>
        public double Span;
        /// <summary>The build to play at its times instead of drafting and opening chests (a twin's Took).</summary>
        public List<(double T, Action<Battle> Do)>? Replay;
        /// <summary>Filled: what built her (the cards taken, the chests' gifts), at the battle's time.</summary>
        public readonly List<(double T, Action<Battle> Do)> Took = new();
        /// <summary>Filled: falls stood up from, seconds below half health.</summary>
        public int Falls;
        public double LowSeconds;
        /// <summary>The Turn pair (--pair turn:ID): this skill carried from the start at SkillRank (added if the
        /// calling's kit hasn't it, ranked up if it has), its wick lit along WickPath.</summary>
        public string? Skill;
        public int SkillRank = 1;
        public string[]? WickPath;
        /// <summary>Filled for the Turn pair: the skill's damage, on champions and on bosses; its Turns at work and dark.</summary>
        public double SkillDmg, SkillElite, SkillBoss;
        public string[] TurnsOn = [], TurnsDark = [];
        public Dictionary<string, double>? DamageBy;
        /// <summary>The board pair's off run: no wicks in this fight, whatever WickBook.Lights says.</summary>
        public bool NoWicks;
        /// <summary>The board pair's ablation (--nowick, --noturn): these skills light no wick; these light their wick
        /// without its Turn (the Turn's slot goes to the next lead-in, as the Turn pair's off run).</summary>
        public string[] NoWick = [], NoTurn = [];
    }

    public static string Card(Offer o) => o.Kind switch
    {
        OfferKind.Weapon => $"w:{o.Id}",
        OfferKind.Rank => $"r:{o.Id}",
        OfferKind.Evolve => $"e:{o.Branch}",
        OfferKind.Boon when o.Great => $"g:{o.Id}",
        OfferKind.Boon when o.Blessing => $"b:{o.Id}",
        OfferKind.Boon => $"p:{o.Id}",
        OfferKind.Hone => $"h:{o.Id}",
        OfferKind.Union => $"u:{o.Id}",
        OfferKind.Heal => "heal",
        _ => "gold",
    };

    /// <summary>Settle every draft owed, the policy's way (banish, reroll,
    /// skip and choose through the same calls the game makes).</summary>
    public static void Drafts(Battle b, Picker pick, Rng rng, RunResult r, Minute? m, List<(double T, Action<Battle> Do)>? took = null)
    {
        int guard = 0;
        while (b.DraftOwed && guard++ < 200)
        {
            bool normal = LevelUp.SkillNext(b);
            var offers = LevelUp.Draft(b);
            if (offers.Count == 0) break;
            int ban = b.Banishes > 0 ? pick.Banish(b, offers) : -1;
            if (ban >= 0 && LevelUp.Banish(b, offers[ban]) is { } afterBan) { offers = afterBan; r.Banishes++; }
            if (b.Rerolls > 0 && pick.Reroll(b, offers) && LevelUp.Reroll(b) is { } again) { offers = again; r.Rerolls++; }
            foreach (var o in offers) r.Offered[Card(o)] = r.Offered.GetValueOrDefault(Card(o)) + 1;
            if (normal)
            {
                r.NormalDrafts++;
                if (offers.Any(o => o.Kind is OfferKind.Rank or OfferKind.Evolve or OfferKind.Hone || (o.Kind == OfferKind.Boon && o.From > 0))) r.Advancing++;
                if (offers.All(o => o.Kind is OfferKind.Heal or OfferKind.Gold)) r.Respites++;
                if (pick.Skip(b, offers) && LevelUp.Skip(b)) { r.Skips++; continue; }
            }
            var take = offers[Math.Clamp(pick.Choose(b, offers, rng), 0, offers.Count - 1)];
            r.Taken[Card(take)] = r.Taken.GetValueOrDefault(Card(take)) + 1;
            if (take.Great) r.Greats.Add(take.Id);
            r.Picks.Add((Card(take), b.Time / 60));
            if (take.Kind == OfferKind.Evolve) r.Evolved.Add((take.Branch!, b.Time / 60));
            took?.Add((b.Time, bb => LevelUp.Choose(bb, take)));
            LevelUp.Choose(b, take);
            r.Cards++;
            if (m != null) m.Drafts++;
        }
    }

    public static RunResult Play(RunSpec spec, Fixed? fx = null)
    {
        var a = Callings.Archetype(spec.Calling);
        var j = Journey.Begin(new CreationChoice
        {
            Name = "Bot", Archetype = spec.Calling, Background = "hunter", Palette = a.Palettes[0].Id,
            WeaponItem = a.Weapons[Math.Min(spec.Weapon, a.Weapons.Count - 1)], Ability = a.Abilities[Math.Min(spec.Art, a.Abilities.Count - 1)],
            // The type (road), picked at creation as a player picks it (docs/design/CLASSES.md section 2).
            Type = spec.Type,
        }, (uint)spec.Seed);
        // A survivor further on: the levels, and the points put into the calling's own.
        while (j.Ch.Level < spec.Level) Character.GainXp(j.Ch, Character.XpForLevel(j.Ch.Level) - j.Ch.Xp + 1);
        switch (spec.Calling) { case "arcanist": j.Ch.Attributes.Wits += j.Ch.Points; break; case "stalker": j.Ch.Attributes.Finesse += j.Ch.Points; break; default: j.Ch.Attributes.Might += j.Ch.Points; break; }
        j.Ch.Points = 0;
        // The lamps lit.
        if (spec.Lamps == "full")
        {
            foreach (var id in Lamps.StoryFights) j.World.Facts[$"arena.{id}"] = "won";
            j.World.Facts["lamps.atlas"] = LampBook.AtlasLamps;
        }
        if (spec.Lamps is "suggested" or "full")
        {
            // An arena board is past Act 1: Light my way's whole path (§7's early rule is for the story).
            bool had = j.World.Facts.ContainsKey("chapter.done");
            if (!had) j.World.Facts["chapter.done"] = true;
            LampBook.LightSuggested(j.Ch, j.World);
            if (!had) j.World.Facts.Remove("chapter.done");
        }
        foreach (var id in Light.Select(x => x.Replace("{calling}", spec.Calling)))
            if (!LampBook.Now(j.Ch).Lit.Contains(id)) LampBook.Now(j.Ch).Lit.Add(id);
        foreach (var id in Dark) LampBook.Now(j.Ch).Lit.Remove(id);
        // --flare stand: carry the road's Stand (its lamp lit past its gate if the board hasn't reached it; a measuring aid).
        if (spec.Flare == "stand")
        {
            var road = Lamps.Road(LampBook.Now(j.Ch).Type);
            if (Lamps.FlareLamp(road.Stand) is { } fl && !LampBook.Now(j.Ch).Lit.Contains(fl)) LampBook.Now(j.Ch).Lit.Add(fl);
            if (!LampBook.Carry(j.Ch, road.Stand)) throw new InvalidOperationException($"can't carry {road.Stand}");
        }
        // (A night shorter than the table's is a story's: it ends on its boss.)
        var arena = new ArenaSpec { Id = "table:bot", Name = "The Harness", Seed = spec.Seed, Tier = spec.Tier, People = spec.People, Oaths = (spec.Oaths ?? []).ToList(),
            Minutes = spec.Minutes, Story = spec.Minutes != Arenas.TableMinutes(spec.Tier) };
        Arenas.Begin(j.World, arena);
        var map = MapGen.Generate(arena.Map);
        var host = new HeadlessHost(j, spec.Seed);
        var zone = new ArenaRun(host, map, arena);
        var at = zone.ArrivalFrom(null);
        string[]? onebuildKit = null;
        var b = j.StartBattle(true, map.Meta.Collision(), map.Ground.HeightAt, at.X, at.Z, at.Facing, (uint)spec.Seed, arena: true);
        if (fx?.Hand is bool handOn) b.HandsOn = handOn;
        // --grant / --grant-union (the game's dev grants, Sim/DevGrants.cs): carried from the start.
        if (Grant != null || GrantUnion != null)
            foreach (var line in DevGrants.Apply(b, Grant, GrantUnion, null)) if (System.Threading.Interlocked.Increment(ref grantSaid) <= 3 || line.Contains("not ")) Console.WriteLine($"{spec.Key}: {line}");
        if (fx is { NoWicks: true }) { b.WickPaths.Clear(); foreach (var w in b.Weapons) w.Wick = null; }
        foreach (var nw in fx?.NoWick ?? []) { b.WickPaths.Remove(nw); foreach (var w in b.Weapons) if (w.Id == nw) w.Wick = null; }
        foreach (var nw in fx?.NoTurn ?? [])
            if (b.WickPaths.TryGetValue(nw, out var wp)) b.SetWickPath(nw, wp.Where(id => !SurvivorUnchained.Content.Wicks.IsTurn(nw, id)).ToArray());
        if (fx?.Skill is { } forced)
        {
            if (fx.WickPath != null) b.SetWickPath(forced, fx.WickPath);
            if (b.Weapons.Find(w => w.Id == forced) is null && b.AddWeapon(forced, fx.SkillRank) is null)
                throw new InvalidOperationException($"{spec.Key}: can't add {forced}");
            while (b.Weapons.Find(w => w.Id == forced) is { } fw && fw.Rank < fx.SkillRank) b.RankWeapon(forced);
        }
        if (spec.OneBuild)
        {
            // docs/design/ONE_BUILD.md 1-2, approximated: the whole build at full power from minute 0, sizes in full, and the
            // draft offering only ranks and hones on the skills carried.
            string[] order = spec.Calling switch
            {
                "warden" => ["grip", "sunder", "groundbreaker", "dawnpulse", "rebuke", "watch_bell", "oathblade", "judgement_disc"],
                "reaver" => ["grip", "axe_gyre", "cleaver", "iron_palms", "reaving_arc", "umbral_bolt", "arcweb"],
                "arcanist" => ["grip", "cinderfall", "rimeshard", "hoarfrost", "seeking_motes", "firepot", "dawnpulse"],
                _ => ["grip", "knifestorm", "volley", "gale_chakram", "firepot", "judgement_disc", "thornbloom"],
            };
            string grip = b.Weapons.Count > 0 ? b.Weapons[0].Id : "";
            var kit = order.Select(id => id == "grip" ? grip : id).Where(id => id != "").Distinct()
                .Where(id => SurvivorUnchained.Content.Weapons.CanCarry(spec.Calling, id)).Take(SkillBook.SlotsAt(spec.Level)).ToList();
            int kr = Math.Min(8, 1 + (spec.Level - 1) / 3);
            foreach (var id in kit)
            {
                if (b.Weapons.Find(w => w.Id == id) is null && b.AddWeapon(id, kr) is null)
                    throw new InvalidOperationException($"{spec.Key}: can't add {id}");
                while (b.Weapons.Find(w => w.Id == id) is { } kw && kw.Rank < kr) b.RankWeapon(id);
            }
            foreach (var id in SurvivorUnchained.Content.Boons.All.Keys) b.BannedCards.Add(id);
            foreach (var id in SurvivorUnchained.Content.Weapons.All.Keys) if (!kit.Contains(id)) b.BannedCards.Add(id);
            b.Lamps.Night = false;
            onebuildKit = kit.ToArray();
        }
        if (fx?.Replay != null) b.ChestsInert = true;
        if (fx is { DamageMore: > 0 }) b.AddBuff("calibration", Stat.Damage, fx.DamageMore, ModKind.More, 1e9, 1);
        else if (fx != null)
            host.Opened = c =>
            {
                foreach (var it in c.Items)
                {
                    string id = it.Id;
                    switch (it.Kind)
                    {
                        case ChestItemKind.Evolution:
                            string branch = b.Weapons.Find(w => w.Id == id)?.Evolution?.Id ?? "";
                            fx.Took.Add((b.Time, bb => bb.Evolve(id, branch, chest: true))); break;
                        case ChestItemKind.Rank: fx.Took.Add((b.Time, bb => bb.RankWeapon(id))); break;
                        case ChestItemKind.Passive: fx.Took.Add((b.Time, bb => bb.AddBoon(id))); break;
                        case ChestItemKind.Gold: fx.Took.Add((b.Time, bb => { bb.HealPlayer(bb.MaxHp * 0.3, "chest"); bb.GoldGained += it.To; })); break;
                    }
                }
            };
        b.Hooks = zone.Hooks;
        if (fx is { NoFall: true })
            b.Hooks.OnPlayerDeath = _ => { fx.Falls++; b.Player.Hp = b.MaxHp; b.Player.Iframes = Math.Max(b.Player.Iframes, 2); return true; };
        host.Battle = b;
        zone.Begin(b);
        b.Charges.On = Director;
        int lastStarted = 0, lastSpikes = 0;

        var pick = Picker.Make(spec.Policy);
        var rng = new Rng((uint)(spec.Seed * 7919 + 13));
        var r = new RunResult { Spec = spec, Path = pick.Path?.Id ?? "" };
        var firstHit = new Dictionary<int, double>();
        var hitCount = new Dictionary<int, int>();
        var hitsFodder = new List<double>();
        var hitsElite = new List<double>();
        var fodder = new List<double>();
        var elite = new List<double>();
        double bossAt = -1, bossUp = -1;
        var p = b.Player;
        var m = new Minute();
        double lastDamage = 0, lastTaken = 0;
        int lastKills = 0;
        double t = 0;
        var trace = Environment.GetEnvironmentVariable("ARENA_TRACE") is { } tr && tr.Split('@')[0] == spec.Key ? tr : null;
        double traceFrom = trace != null && trace.Contains('@') ? double.Parse(trace.Split('@')[1], System.Globalization.CultureInfo.InvariantCulture) * 60 : 0;
        int replayed = 0;
        // --bot human|careless: a player's hands, late (Harness/Human.cs).
        var human = spec.Bot is "human" or "careless" or "idler" ? new Human(spec.Seed, spec.Bot == "careless") { Idle = spec.Bot == "idler" } : null;
        var hold = LampHold.For(zone, map, b, spec.Seed, spec.Bot is "camper" or "idler" ? "deft" : spec.Bot != "" ? spec.Bot : spec.Deft ? "deft" : "plain");
        // H6's hands (Harness/Bots.cs): standing, camper, kiter.
        bool simple = Bots.Is(spec.Bot);
        double boardR = zone.Board?.Radius ?? 60;
        // H6's measures: surrounded (foes within 4 m in three or more of six sectors, held 2 s), and the marks laid
        // on her (a hostile telegraph that covers where she stands as it is made).
        double ringFor = 0; bool ringCounted = false;
        var marksOn = new List<double>();
        void Surround()
        {
            int mask = 0;
            foreach (var e in b.HostilesInRadius(p.X, p.Z, 4))
            {
                if (e.State == EnemyState.Dying) continue;
                double a = Math.Atan2(e.Z - p.Z, e.X - p.X) + Math.PI;
                mask |= 1 << Math.Min(5, (int)(a / (Math.PI / 3)));
            }
            int sectors = 0; for (int i = 0; i < 6; i++) if ((mask >> i & 1) != 0) sectors++;
            if (sectors >= 3)
            {
                ringFor += Dt; r.SurroundSec += Dt;
                if (ringFor >= 2 && !ringCounted) { ringCounted = true; r.Surrounds++; r.SurroundAt.Add(Math.Round(t / 60, 2)); }
            }
            else { ringFor = 0; ringCounted = false; }
        }
        while (t < spec.Cap * 60 && p.Alive && host.Result == null && (fx == null || fx.Span <= 0 || t < fx.Span * 60 - 1e-9))
        {
            var goal = hold?.Goal(b);
            if (simple)
            {
                var (sx, sz) = Bots.Steer(spec.Bot, b, goal, boardR);
                if (Bots.Act(spec.Bot, b, j, sx, sz, zone.BossScript)) r.Quaffs++;
                zone.Step(Dt); zone.Frame(Dt); b.Tick(Dt, sx, sz);
                Surround(); goto Drain;
            }
            var (mx, mz) = human != null ? human.Steer(b, zone.BossScript, goal) : Pilot.Steer(b, spec.Deft, zone.BossScript, goal: goal);
            // A holder near the pool's edge turns back in rather than step out of it (not while dodging: the boss's
            // marks and the kit's are read inside Steer, and a goal does not overrule them).
            if (goal == null && hold != null && hold.Leaving(b, mx, mz) && b.Blows.Count == 0 && b.ActiveTells.Count == 0)
                (mx, mz) = human != null ? human.Steer(b, zone.BossScript, (zone.Lamp!.X, zone.Lamp.Z)) : Pilot.Steer(b, spec.Deft, zone.BossScript, goal: (zone.Lamp!.X, zone.Lamp.Z));
            if (human != null ? human.Act(b, j, mx, mz, zone.BossScript) : Pilot.Act(b, j, mx, mz, zone.BossScript, presses: spec.Deft)) r.Quaffs++;
            zone.Step(Dt);
            zone.Frame(Dt);
            b.Tick(Dt, mx, mz);
            Surround();
            Drain:
            foreach (var ev in b.Events.Drain())
            {
                if (ev is Ev.ClosingWall { Up: true } cw && Math.Sqrt((p.X - cw.X) * (p.X - cw.X) + (p.Z - cw.Z) * (p.Z - cw.Z)) < cw.Inner) r.Ringed++;
                if (ev is Ev.PlayerHit { Amount: > 0 } hb) r.HurtBy[hb.Source] = Math.Round(r.HurtBy.GetValueOrDefault(hb.Source) + hb.Amount);
                if (ev is Ev.Telegraph { Hostile: true, Phase: TellPhase.Warn } onHer && Covers(onHer, p.X, p.Z, p.Radius)) marksOn.Add(t);
                if (hold != null && ev is Ev.PlayerHit { Amount: > 0, Dodged: false } && b.HeldLamp is { Caught: true }) { if (zone.InLampPool) r.LampHitsIn++; else r.LampHitsOut++; }
                if (ev is Ev.Telegraph { Tell: not null } kt) { if (kt.Phase == TellPhase.Warn) r.KitMarked++; else if (kt.Caught) r.KitCaught++; }
                switch (ev)
                {
                    case Ev.Spawn s:
                        firstHit.Remove(s.Enemy);
                        hitCount.Remove(s.Enemy);
                        if (Enemies.Get(s.Def).Miniboss) r.MinibossesMet.Add(s.Def);
                        break;
                    case Ev.Hit h when h.Amount > 0:
                        if (!firstHit.ContainsKey(h.Target)) firstHit[h.Target] = t;
                        hitCount[h.Target] = hitCount.GetValueOrDefault(h.Target) + 1;
                        break;
                    case Ev.Kill k when k.ByPlayer:
                        if (b.EmberLevel <= 10 && hitCount.TryGetValue(k.Enemy, out var hc) && !k.Boss) (k.Elite ? hitsElite : hitsFodder).Add(hc);
                        hitCount.Remove(k.Enemy);
                        r.KillsBy[k.Family.ToString()] = r.KillsBy.GetValueOrDefault(k.Family.ToString()) + 1;
                        if (k.Elite && !k.Boss) r.Champions++;
                        if (firstHit.TryGetValue(k.Enemy, out var t0))
                        {
                            double ttk = t - t0;
                            if (k.Boss) r.BossTtk = ttk;
                            else if (k.Elite)
                            {
                                elite.Add(ttk);
                                if (Enemies.Get(k.Def).Miniboss) r.Minibosses.Add((k.Def, ttk, t / 60));
                                if (b.Enemies.Items[k.Enemy].Named?.Title?.StartsWith("Herald") == true) r.HeraldTtk.Add(ttk);
                            }
                            else fodder.Add(ttk);
                        }
                        firstHit.Remove(k.Enemy);
                        break;
                    case Ev.Kill k2: firstHit.Remove(k2.Enemy); hitCount.Remove(k2.Enemy); break;
                    case Ev.Telegraph tg when tg.Boss && tg.Kind == TelegraphKind.Blow && tg.Phase == TellPhase.Warn: r.BossMarked++; break;
                    case Ev.Announce an when an.Title == "Staggered": r.BossStaggers++; break;
                    // ARENA_TRACE=KEY@MINUTE: the blows that land on the survivor, from that minute (why a run fell).
                    case Ev.PlayerHit ph when trace != null && t >= traceFrom:
                        Console.Error.WriteLine($"{t / 60:0.000} {ph.Source,-22} {ph.Amount,6:0} {(ph.Dodged ? "dodged" : ph.Blocked ? "blocked" : "")} hp {p.Hp:0}/{b.MaxHp:0} shield {p.Shield:0}");
                        break;
                }
            }
            host.Pass(Dt);
            if (fx?.Replay is { } replay)
            {
                b.PendingLevels = 0; b.PendingBlessings.Clear(); b.GreatOwed = 0;
                while (replayed < replay.Count && replay[replayed].T <= b.Time + 1e-9) replay[replayed++].Do(b);
            }
            else Drafts(b, pick, rng, r, m, fx?.Took);
            if (fx != null && p.Hp < 0.5 * b.MaxHp) fx.LowSeconds += Dt;
            m.LowHp = Math.Min(m.LowHp, p.Hp / b.MaxHp);
            m.ChargePeak = Math.Max(m.ChargePeak, b.Charges.Live);
            if (b.Charges.Live >= 3) m.Overlap += Dt;
            t += Dt;
            if (hold != null && b.HeldLamp is { Caught: true }) { if (zone.InLampPool) r.LampPoolSec += Dt; else r.LampOutSec += Dt; }
            if (bossUp < 0 && (int)Math.Round(t * 60) % 30 == 0 && b.Enemies.Living().Any(e => e.Boss)) { bossUp = b.Time; if (hold != null) r.FlareAtBoss = b.FlareMeter / Battle.FlareFull; }
            if (r.WonAt == null && zone.Won)
            {
                r.WonAt = t / 60;
                bossAt = t;
            }
            if (r.CompleteAt == null && b.SlotsUsed == Weapons.MaxWeapons && b.Weapons.All(w => w.Evolution != null || Weapons.IsUnion(w.Id))) r.CompleteAt = t / 60;
            if ((int)(t / 60) != (int)((t - Dt) / 60))
            {
                double dealt = b.DamageBy.Values.Sum();
                m.Ember = b.EmberLevel;
                m.Kills = b.KillCount - lastKills;
                m.Damage = dealt - lastDamage;
                m.Taken = b.DamageTaken - lastTaken;
                m.Alive = b.Enemies.Items.Count(e => e.Alive && e.Disposition == Disposition.Hostile);
                m.TtkFodder = Median(fodder);
                m.TtkFodder90 = fodder.Count == 0 ? double.NaN : fodder.OrderBy(x => x).ElementAt((int)(fodder.Count * 0.9));
                m.TtkElite = Median(elite);
                m.Charges = b.Charges.Started - lastStarted;
                m.Spikes = b.Charges.SpikesRun - lastSpikes;
                lastStarted = b.Charges.Started; lastSpikes = b.Charges.SpikesRun;
                r.ByMinute.Add(m);
                lastKills = b.KillCount; lastDamage = dealt; lastTaken = b.DamageTaken;
                fodder.Clear(); elite.Clear();
                m = new Minute();
            }
            // Past the win, only as long as asked.
            if (bossAt > 0 && t - bossAt > spec.Beyond * 60) break;
        }
        r.Died = !p.Alive;
        r.Minutes = t / 60;
        if (r.Died && r.WonAt == null && host.Boss is { } bar && t >= arena.Minutes * 60) r.BossLeft = bar.Hp / Math.Max(1, bar.MaxHp);
        // What rules the horde comes at the half hour (an elite, not a Boss, by its kind).
        if (r.WonAt is double won) r.BossTtk = won * 60 - arena.Minutes * 60;
        if (zone.BossScript is { } bs)
        {
            r.BossLanded = b.BossBlowsTaken;
            r.BossBreak = bs.BreakSum / Math.Max(1, bs.MaxHp);
            r.BossPhase = bs.PhaseIx;
            r.BossSoft = bs.Soft;
            r.BossPhases = bs.PhaseLog.Select(x => new[] { x.Cut, x.Seconds, x.MarkAt }).Append(new[] { bs.FlareCut, bs.PhaseT, -1 }).ToList();
        }
        r.Returns = zone.Returns;
        r.CoreBroken = zone.CoreBroken;
        r.Dark = zone.DarkSworn;
        r.Kills = b.KillCount;
        r.Gold = b.GoldGained;
        r.Ember = b.EmberLevel;
        r.DamageTaken = b.DamageTaken;
        r.LowHp = r.ByMinute.Count > 0 ? r.ByMinute.Min(x => x.LowHp) : 1;
        r.KilledBy = r.Died ? p.FellTo ?? p.LastKiller?.Def.Id ?? "?" : "";
        r.DamageBy = new Dictionary<string, double>(b.DamageBy);
        foreach (var (k, v) in b.HealBy) r.HealBy[k] = Math.Round(v);
        if (fx?.Skill is { } sk)
        {
            fx.DamageBy = r.DamageBy;
            // The skill, and any union it went into (which carries its Turn).
            var ids = Unions.All.Where(u => u.A == sk || u.B == sk).Select(u => u.Into).Append(sk).ToHashSet();
            fx.SkillDmg = ids.Sum(id => b.DamageBy.GetValueOrDefault(id));
            fx.SkillElite = ids.Sum(id => b.EliteDamageBy.GetValueOrDefault(id));
            fx.SkillBoss = ids.Sum(id => b.BossDamageBy.GetValueOrDefault(id));
            var sw = b.Weapons.Find(w => ids.Contains(w.Id));
            fx.TurnsOn = sw?.Wick?.Turns.ToArray() ?? [];
            fx.TurnsDark = sw?.Wick?.Dark.ToArray() ?? [];
        }
        r.DamageRaw = b.DamageRaw;
        if (human != null) { r.ThreatsMet = human.Met; r.ThreatsRead = human.Read; }
        r.HpEnd = p.Hp / Math.Max(1, b.MaxHp);
        // The marks laid on her before the boss came (or the night's end): how many, and the longest stretch from
        // 0:45 without one (H6's rule: something to dodge every 45-60 s).
        double until = bossUp >= 0 ? bossUp : t;
        var on = marksOn.Where(x => x >= 45 && x < until).ToList();
        r.MarksOnHer = on.Count;
        double last = 45, gap = 0;
        foreach (var x in on) { gap = Math.Max(gap, x - last); last = x; }
        r.MarkGapMax = Math.Max(gap, until - last);
        for (int mi = 0; mi * 60 < t; mi++) r.MarksPerMin.Add(marksOn.Count(x => x >= mi * 60 && x < mi * 60 + 60));
        r.HitsFodder = hitsFodder.Count == 0 ? double.NaN : Median(hitsFodder);
        r.HitsElite = hitsElite.Count == 0 ? double.NaN : Median(hitsElite);
        r.Build = Describe(b);
        r.Kit = onebuildKit;
        r.Road = LampBook.Now(j.Ch).Type;
        r.LampsLit = LampBook.Now(j.Ch).Lit.Count;
        r.LampIds = string.Join(",", LampBook.Now(j.Ch).Lit);
        r.FlareCasts = b.FlareCasts;
        if (hold != null) { r.LampHeld = hold.Holds; r.LampOuts = zone.LampOuts; r.LampRelights = zone.LampRelights; }
        r.Flanks = zone.Flanks; r.SurroundCloses = zone.SurroundCloses; r.StandCharges = zone.StandCharges; r.Recalls = zone.Recalls; r.IronSpawns = zone.IronSpawns; r.IronSlams = zone.IronSlams; r.Feeds = zone.Feeds;
        r.Blocks = b.Blocks; r.Rebukes = b.Rebukes; r.StonesPeak = b.StonesPeak;
        r.RebukeStrikes = b.RebukeStrikes; r.Tolls = b.Tolls; r.BellBarrier = b.BellBarrier; r.MaxHpEnd = b.MaxHp;
        r.FlareClutches = b.FlareClutches;
        r.FlareFills = new Dictionary<string, double>(b.FlareFills);
        if (b.FlareTimes.Count > 0) r.FlareFirst = b.FlareTimes[0] / 60;
        if (b.FlareTimes.Count > 1) r.FlareGap = (b.FlareTimes[^1] - b.FlareTimes[0]) / (b.FlareTimes.Count - 1);
        if (bossUp >= 0) r.FlareBossCasts = b.FlareTimes.Count(x => x >= bossUp);
        double bossDmg = b.BossDamageBy.Values.Sum();
        r.FlareCastsOnBoss = b.FlareCastsOnBoss;
        r.FlareFullBankShots = b.FlareFullBankShots;
        r.FlareCrowd = b.FlareCrowd.ToList();
        r.BossDamage = bossDmg;
        r.FlareBossDamage = b.BossDamageBy.GetValueOrDefault("flare");
        double took = b.BossHealthBy.Values.Sum();
        if (took > 0) r.FlareBossTook = b.BossHealthBy.GetValueOrDefault("flare") / took;
        r.BossTookBy = new Dictionary<string, double>(b.BossHealthBy);
        r.StandTook = b.BossTookInStand; r.StandSeconds = b.StandOnBossSeconds;
        if (bossDmg > 0) r.FlareBossShare = b.BossDamageBy.GetValueOrDefault("flare") / bossDmg;
        return r;
    }

    public static string Describe(Battle b) =>
        string.Join(" ", b.Weapons.Select(w => $"{w.Evolution?.Id ?? w.Id}{w.Rank}")) + " | " +
        string.Join(" ", b.Boons.Select(kv => $"{kv.Key}{kv.Value}"));

    /// <summary>Whether a telegraph made now covers her (a circle or ring's disc, a line's lane, a cone's wedge), with a
    /// metre's grace.</summary>
    internal static bool Covers(Ev.Telegraph t, double x, double z, double r)
    {
        double dx = x - t.X, dz = z - t.Z, d = Math.Sqrt(dx * dx + dz * dz);
        switch (t.Shape)
        {
            case TelegraphShape.Line when t.X1 is { } x1 && t.Z1 is { } z1:
            {
                double lx = x1 - t.X, lz = z1 - t.Z, ll = lx * lx + lz * lz;
                double u = ll < 1e-9 ? 0 : Math.Clamp((dx * lx + dz * lz) / ll, 0, 1);
                double ex = t.X + lx * u - x, ez = t.Z + lz * u - z;
                return Math.Sqrt(ex * ex + ez * ez) <= (t.Width ?? 1.5) / 2 + r + 1;
            }
            case TelegraphShape.Cone:
            {
                if (d > t.Radius + r + 1) return false;
                double half = (t.Arc ?? Math.PI / 2) / 2, a = Math.Atan2(dz, dx) - (t.Angle ?? 0);
                a = Math.Atan2(Math.Sin(a), Math.Cos(a));
                return d < 1.5 || Math.Abs(a) <= half + 0.2;
            }
            case TelegraphShape.Ring: return d <= t.Radius + r + 1 && d >= t.Inner - r - 1;
            default: return d <= t.Radius + r + 1;
        }
    }

    public static double Median(List<double> xs)
    {
        if (xs.Count == 0) return double.NaN;
        var s = xs.OrderBy(x => x).ToList();
        return s[s.Count / 2];
    }
}
