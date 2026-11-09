using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Cinema;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play.Zones;

/* The prologue: one night on the Low Ford road (the web game's
 * game/zones/prologue.ts).
 *
 * It is a tutorial that never stops to be one. Each thing the game needs
 * you to know arrives as the road puts it in front of you:
 *
 *   wake      the dead climb out of the ground around your fire     (move)
 *   rising    their stones hold light; the ember rises     (ember, the draft)
 *   road      up the road; shieldmen, bowmen             (build, positioning)
 *   ambush    the dead rise out of the ditch by a broken cart     (the horde)
 *   post      a Barrow Knight over a dead watchman's chest (elites, equipment)
 *   barrow    a Grave-Caller raising the dead                     (ability)
 *   ford      the Ford-Warden                                        (boss)
 *   dawn      what took the Warden's heart; the sun comes up and the ember
 *             goes out, and all it built with it: it burns only in the dark
 *             (the story is walked by day; the ember is for the night's
 *             arenas); the gate opens                               (the world)
 *
 * Dying here is forgiven: the ember is not done with you, and you get up
 * again at the last place you were safe. That is the only place in the game
 * where that is true. */
public sealed partial class Prologue : ZoneRuntime
{
    public enum Stage { Wake, Rising, Road, Ambush, Road2, Post, Barrow, ToFord, Intro, Boss, Victory, Dawn, Exit }

    public override string Id => "lowford";
    public override string Name => "The Low Ford Road";
    public override string? Region => "Thornhollow, south";
    public override bool Combat => true;
    /// <summary>The night's: the ember burns until the dawn puts it out (only while the draft runs: with it off, the
    /// night's kills teach plain experience, as the day's do, ARPG.md 5).</summary>
    public override bool Ember => Draft && !F("prologue.done").Truthy;
    /// <summary>(M5) The ember-card draft in the night: encounters.json's lowford "draft" (false since the ARPG pick,
    /// ARPG.md 5). Off: no cards, no great blessing, no draft tip, and the dawn takes and pays nothing the night did
    /// not lend (the callouts that only speak of the draft, F2-F5 and F12, are skipped). Set before the battle starts.</summary>
    public bool Draft { get; set; } = Encounters.For("lowford")?.Draft ?? true;
    /// <summary>(M5) The night's placed beats (encounters.json, when: night), from the fire to the ford.</summary>
    Encounters? night;
    public Encounters? Night => night;
    /// <summary>The Barrow Knight, placed at the post at nightfall on its escort's ground (n_post), and its seed: it is
    /// the Post's knight once she reaches the post.</summary>
    Enemy? knightRest;
    double knightRestSeed;
    bool wagonQueued;
    public override IReadOnlyList<string> Creatures { get; } = ["risen", "risen_warrior", "risen_archer", "barrow_knight", "grave_caller", "grimtunnel", "ford_warden", "boar", "footpad", "pillager", "kerchief_captain", "wolf"];

    sealed class WardenAI
    {
        public string Mode = "sleep";
        public double Hold, T, CleaveCd = 3, ChargeCd = 6, ChannelCd = 30, DirX, DirZ = 1, Travelled, ChannelHp, ChannelOver, RaiseT, ContactT, HitX, HitZ;
        public List<double> Thresholds = [0.7, 0.4];
    }

    static readonly double[] Ward = [1, 0.7, 0.55, 0.4];
    const string DraftTip = "Each time the ember rises, choose one: a combat skill (they fire on their own) or a passive skill. A combat skill at rank 8, with one rank of the passive it names, evolves.";

    public Stage Now { get; private set; } = Stage.Wake;
    double stageT, cutT, dawnK, envT, deadT = -1;
    XZ checkpoint;
    readonly HashSet<string> shown = new();
    /// <summary>Combat skills held at the start (the first one more is the first drafted).</summary>
    int startWeapons = -1;
    /// <summary>The first character level, at dawn: its banner, and whether its callout is due (after her dawn line).</summary>
    Announcement? levelAnn;
    /// <summary>The character levels the night paid at dawn, and the traits they left to choose (F12's words).</summary>
    int levelsTaught, traitsDue;
    bool levelDue;
    /// <summary>The Barrow Knight's first lane: planted (its windup seen), and run (the floor under it let go).</summary>
    bool knightRan, knightWinding, barrowLineSaid;
    /// <summary>Windups the Knight has finished (his floor holds for two), when F7 ended (stage time), when the tips showed (game time).</summary>
    int knightWindups;
    double redEndAt = -1, eliteAt = -1, packAt = -1;
    /// <summary>The Ambush's trap: when the ditch rose (stage time; none yet: the wagon is still quiet), and the
    /// bowmen it put up, whose first volley comes all at once and teaches the dash (au i15).</summary>
    double sprungAt = -1;
    double ambDiagAt = -9;
    /// <summary>The wagon's trap has sprung (the pacing log, a shot of it).</summary>
    public bool Sprung => sprungAt >= 0;
    bool wagonSaid;
    /// <summary>When the wagon's line was over (stage time): the ditch waits 0.8 s of silence.</summary>
    double wagonDoneAt = -1;
    readonly List<Enemy> bowmen = new();
    readonly List<(double X, double Z, int Light, string Flame)> pylons = new();
    readonly double[] lampY;
    readonly bool[] litPylons;
    readonly double[] pylonHp;
    Enemy? warden, caller, knight, grim;
    /// <summary>The Ford-Warden while the boss fight runs (the play camera keeps him in frame with her).</summary>
    public Enemy? BossInFrame => Now == Stage.Boss && warden is { Alive: true } w && w.State != EnemyState.Dying ? w : null;
    /// <summary>The day road's last stretch (H4 r3 judge: the player never saw home at the ring): from 28 m short of the
    /// town gate, on the road, the look leans toward it, so the gate stands at the frame's head through the wolves' ring
    /// and the walk in (the play camera sees about 11 m past her unleaned).</summary>
    public (double X, double Z)? GateInFrame => Now == Stage.Exit && !finished && B?.Player is { Alive: true } p
        && L("gate") is var g && p.Z < g.Z + 28 && Math.Abs(p.X - g.X) < 22 ? (g.X, g.Z) : null;
    bool wardenGone, chestOpened, finished, coreShown, doused;
    /// <summary>A cinematic is playing the Warden with its own body (C02, C03): ours waits, hidden.</summary>
    bool wardenInCine;
    readonly XZ wardenHome;
    /// <summary>Metres east of his fight's home where he lies asleep, clear of the causeway.</summary>
    public const double SleepEast = 5.5;
    /// <summary>Metres he lies below the waterline asleep (his chest and face just break the surface).</summary>
    public const double SleepSink = 0.3;
    (double X, double Z, double Facing) wardenPos;
    readonly WardenAI ai = new();
    IBossView wardenView = null!;
    IOrb core = null!;
    INpcView? watchman;
    readonly double waterY;
    double coreY, coreSpin;
    (double X, double Z) corePos;

    XZ L(string place) => P("LOWFORD", place);
    double ExitZ => Meta.Places["LOWFORD"].GetProperty("exitZ").GetDouble();

    /// <summary>Where the river runs (the web game's riverZ).</summary>
    public static double RiverZ(double x) => -44 + Math.Sin(x * 0.032) * 4.5 + Math.Sin(x * 0.011 + 1) * 3;

    public Prologue(IZoneHost host, ZoneMeta meta) : base(host, meta)
    {
        SurvivorUnchained.Content.LampPosts.Resolve(meta.Id, meta.Features);
        if (Encounters.For(meta.Id) is { } es) Encounters.SyncPosts(es);
        foreach (var p in meta.Refs.GetProperty("pylons").EnumerateArray())
            pylons.Add((p.GetProperty("x").GetDouble(), p.GetProperty("z").GetDouble(), p.GetProperty("light").GetInt32(), p.GetProperty("flame").GetString()!));
        litPylons = pylons.Select(_ => true).ToArray();
        // (each lamp's flame, where its light hangs: its top and the light's height over it)
        lampY = meta.Refs.GetProperty("pylons").EnumerateArray().Select(p => p.TryGetProperty("top", out var t) ? t.GetDouble() + 0.8 : 3.2).ToArray();
        pylonHp = pylons.Select(_ => 260.0).ToArray();
        waterY = meta.Places["WATER_Y"].GetDouble();
        var camp = L("camp");
        checkpoint = new XZ(camp.X + 1.5, camp.Z - 1.5);
        var ford = L("ford");
        wardenHome = new XZ(ford.X + 1, ford.Z - 2);
        // Lying where he fell before the fight: in the water east of the causeway, never across its stepping
        // stones (they run x -2.7..2.7 through the ford; at the fight's home the stones came up through his legs).
        wardenPos = (wardenHome.X + SleepEast, wardenHome.Z, 0);
        Hooks = new BattleHooks
        {
            BossTick = (e, dt) => e.Tag == "warden" && WardenTick(e, dt),
            OnKill = OnKill,
            // (M5-B, ARPG 7.1: a pack's captain is its carrier, a champion carries more; Encounters.Carried)
            OnLoot = e => [.. night?.Carried(e, G.Journey.Drops) ?? [], .. day?.Carried(e, G.Journey.Drops) ?? []],
            OnPickup = OnDayPickup,
            OnHitProp = (tag, _, _, dmg, _, _) =>
            {
                if (!tag.StartsWith("pylon:") || Now != Stage.Boss || !int.TryParse(tag[6..], out int i) || !litPylons[i]) return;
                pylonHp[i] -= dmg;
                if (pylonHp[i] <= 0) Snuff(i, "broken");
            },
        };
        var chest = L("chest"); var man = L("watchman"); var fire = L("fire");
        Interactables.Add(new()
        {
            Id = "chest", X = chest.X, Z = chest.Z, R = 2.6, Verb = "Open", Name = "Watch Chest",
            When = () => !chestOpened,
            Locked = () => knight != null ? "The Barrow Knight stands over it" : null,
            Act = () =>
            {
                chestOpened = true;
                G.Apply("""[{ "give": "padded_jerkin", "rarity": 1 }, { "give": "health_draught", "qty": 2 }, { "gold": 15 }]""");
                G.SetHint(null);
                // (said where it's found; F8 waits for it to go, au1 item 10: the two stacked at the Post)
                G.After(0.6, () => PacedTip("pack", "Your pack", $"What you find, you keep.{NL}The ember won't outlast the night; gear, gold and what you learn will.{NL}Press {{key:{Key("inventory")}}} to open your *pack* and wear the jerkin.", null, 11));
                Objective([("Search the old Watch-post", true, false), ("Wear what you found", false, true), ("Follow the road north", false, false)]);
            },
        });
        Interactables.Add(new()
        {
            Id = "watchman", X = man.X, Z = man.Z, R = 2.4, Verb = "Examine", Name = "Dead Watchman",
            Act = () =>
            {
                G.Say("A Watchman, gray-bearded and a long time dead, sitting against the post as if he had only stopped for breath. Something has had his eyes. In his belt-book, three lines in a hand that worsens as it goes: \"Lamps at the Low Ford lit again, and not by us. Not oil. Wrong color.\" \"Sent Dannet for the captain. Dannet not back.\" \"The Warden is walking. I can hear it singing in the water.\"", null, 10);
                // The book is the first page of the lamps' mystery.
                G.Apply("""[{ "learn": "lore.warden", "text": "The lamps at the ford burn ember, and the Warden drinks it." }, { "quest": { "id": "lamps", "status": "active", "entry": "book" } }]""");
                // The devout hear the dead, a little.
                if (G.Journey.Ch.Knowledge.Contains("faith"))
                {
                    G.After(10.2, () => G.Say("...and for you alone, the dead man's jaw moves.", null, 3));
                    G.After(13.4, () => G.Say("It broke its own lamps, coming for me. Twice.", "The dead Watchman", 5));
                }
            },
        });
        Interactables.Add(new()
        {
            Id = "fire", X = fire.X, Z = fire.Z, R = 2.2, Verb = "Warm your hands", Name = "Campfire",
            When = () => Now is Stage.Rising or Stage.Wake,
            Act = () => G.Say("The fire is almost out. It will not hold them back.", null, 3.5),
        });
        AddDay();
        AddPosts();
    }

    /* ------------------------------------------------------------- helpers -- */

    void Objective((string Text, bool Done, bool Optional)[] steps) =>
        G.SetObjectives([new Tracked("pro", "The Low Ford", TrackTone.Tutorial, steps.Select(s => new Step(s.Text, s.Optional, s.Done)).ToList())]);

    /// <summary>When a lamp last went out or was relit (H4 r2): the lamp tips wait 1.5 s after it.</summary>
    double lampEventAt = -99;
    readonly HashSet<string> lampTipWaiting = new();

    void Tip(string id, string title, string text, List<string>? keys = null, double life = 9)
    {
        if ((id == "lamps2" || id == "channel") && B != null && B.Time - lampEventAt < 1.5)
        {
            if (!shown.Contains(id) && lampTipWaiting.Add(id))
                G.After(1.5 - (B.Time - lampEventAt) + 0.02, () => { lampTipWaiting.Remove(id); Tip(id, title, text, keys, life); });
            return;
        }
        // (M5 r3: no card on a champion's wake: it waits while one is awake near her or its pack is about to wake)
        if (B != null && !shown.Contains(id) && ChampionGate.Due(B))
        {
            if (champTipWaiting.Add(id)) G.After(0.5, () => { champTipWaiting.Remove(id); Tip(id, title, text, keys, life); });
            return;
        }
        if (!shown.Add(id)) return;
        tipUp = (id, title, text, keys, life, B?.Time ?? 0);
        if (id == "pack") packAt = B?.Time ?? 0;
        if (id == "elite") eliteAt = B?.Time ?? 0;
        G.SetHint(new Hint(id, title, text, keys ?? new()));
        double at = B?.Time ?? 0;
        if (life > 0) G.After(life, () => { if (G.CurrentHint?.Id == id && (tipUp == null || tipUp.Value.At == at)) G.SetHint(null); });
    }

    string Key(string action) => G.KeyLabel(action);

    readonly HashSet<string> champTipWaiting = new();
    /// <summary>(M5 r3) The card Tip last put up, and when.</summary>
    (string Id, string Title, string Text, List<string>? Keys, double Life, double At)? tipUp;
    /// <summary>A card up for less than this when a champion wakes is shown again after the fight; longer, it was read.</summary>
    const double TipRead = 5;

    /// <summary>(M5 r3) A card up as a champion comes awake (or its pack 1.5 s from waking) is taken down; asked again
    /// (after the fight, ChampionGate) if it was up less than TipRead.</summary>
    void ChampionTipWatch()
    {
        if (B == null || tipUp is not { } t) return;
        if (G.CurrentHint?.Id != t.Id) { tipUp = null; return; }
        if (!ChampionGate.Due(B, 1.5)) return;
        G.SetHint(null);
        tipUp = null;
        if (B.Time - t.At < TipRead) { shown.Remove(t.Id); Tip(t.Id, t.Title, t.Text, t.Keys, t.Life); }
    }

    /* The road's words in a line (au i15): the narration and the tips between the Rising and the ford, each
     * read before the next. One comes once no line is being narrated and no callout is up, and 4 s of play
     * after the one before it (2 s after a callout): at the Post the Road2 line was cut off by the Knight's
     * 4 s later, the chest, pack and Barrow came in 5 s, and the Barrow's last callout and the ford's line
     * 0.3 s apart. */
    readonly Queue<(Action Do, Func<bool>? Still)> words = new();
    double wordsFree;
    const double WordsGap = 4, WordsAfterCallout = 2;
    /// <summary>A lesson's distance from any other callout, line or tip (au1 item 14), both ways.</summary>
    const double LessonQuiet = 4;
    /// <summary>The lessons the road's words wait for while they wait their turn.</summary>
    static readonly string[] Lessons = ["tally"];

    /// <summary>Words for the road's line: said in their turn (dropped if `still` says their moment has gone).</summary>
    void Words(Action say, Func<bool>? still = null) => words.Enqueue((say, still));

    /// <summary>A tip in the road's line: once (asked every frame is fine), shown in its turn while `still` holds.</summary>
    void PacedTip(string id, string title, string text, List<string>? keys = null, double life = 9, Func<bool>? still = null)
    {
        if (shown.Contains(id) || words.Any(w => w.Do.Target is TipAsk t && t.Id == id)) return;
        words.Enqueue((new TipAsk(this, id, title, text, keys, life).Show, still));
    }

    sealed record TipAsk(Prologue Z, string Id, string Title, string Text, List<string>? Keys, double Life)
    {
        public void Show() => Z.Tip(Id, Title, Text, Keys, Life);
    }

    void PaceWords()
    {
        if (B == null) return;
        if (G.Teaching != null) wordsFree = Math.Max(wordsFree, B.Time + (G.Teaching.Quiet > 0 ? LessonQuiet : WordsAfterCallout));
        if (Lessons.Any(G.TeachWaiting)) return;
        // (by day, the road's words wait behind its fights: H4 item 10)
        if (Now is Stage.Dawn or Stage.Exit && !DayCalm()) { wordsFree = Math.Max(wordsFree, B.Time + 0.5); return; }
        if (G.Saying) wordsFree = Math.Max(wordsFree, B.Time + 1.5);
        while (words.Count > 0 && words.Peek().Still is { } still && !still()) words.Dequeue();
        if (words.Count == 0 || G.Saying || G.Teaching != null || B.Time < wordsFree) return;
        words.Dequeue().Do();
        wordsFree = B.Time + WordsGap;
    }

    /// <summary>Seconds until the Warden's "RISE" cry, held while the channel's tip settles.</summary>
    double riseBarkIn;

    void RiseBark(Enemy e) => B.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = "RISE, YOU WHO DROWNED HERE.", Speaker = "The Ford-Warden" });

    /// <summary>The channel's tip, as a channel begins: once a profile, and only with an answer in hand (the
    /// form lit or the Flare full), naming only what's ready (round 2 judge: it came before either was
    /// usable). True when it showed.</summary>
    bool ChannelTip()
    {
        if (shown.Contains("channel")) return false;
        // (what breaks it: her art where it rides the dash and interrupts, the Flare, or a hard enough
        // beating; Act.Ability became the Flare on 11 Oct, so no key is called "ability")
        var form = B.Ability is AbilityKind k && Abilities.All[k] is { Interrupts: true, Movement: true } d && B.FormReady ? d : null;
        var ways = new List<string>();
        var keys = new List<string>();
        if (form != null) { ways.Add($"{form.Name} into him"); keys.Add(Key("dash")); }
        if (B.Flare != null && B.FlareReady) { ways.Add("use your Flare"); keys.Add(Key("flare")); }
        if (ways.Count == 0) return false;
        Tip("channel", "Break his spell", $"The Warden is raising the drowned.{NL}Break it: {string.Join(", or ", ways)}.{NL}If he finishes, a lamp lights again.", keys, 10);
        return true;
    }

    /* --------------------------------------------- the callouts (Teach.cs) -- */
    // The words are docs/story/TUTORIAL_COPY.md's, at the moments its table names. Each is asked
    // for every frame its moment holds; the game shows it once a profile, when the screen is clear.

    void Teach(string id, CalloutKind kind, string title, string line, Aim aim, string? answer = null, string? after = null, double gap = Teacher.Gap, bool overHint = false, double patience = 8, bool urgent = false, string? markInk = null) =>
        G.Teach(new Callout(id, kind, title, line, aim, answer) { After = after, Gap = gap, OverHint = overHint, Patience = patience, Urgent = urgent, MarkInk = markInk });

    /// <summary>A point on the ground, lifted a little (what an arrow points at).</summary>
    (double X, double Y, double Z) Up(double x, double z, double lift) => (x, G.Look.HeightAt(x, z) + lift, z);

    /// <summary>The ember stones near her on the ground, nearest first (none: there is none near); the
    /// callout points at the first one well inside the screen (Aim.Safe).</summary>
    IReadOnlyList<(double X, double Y, double Z)> NearEmbers()
    {
        if (B == null) return [];
        var p = B.Player;
        return B.Pickups.Living()
            .Where(k => k.Kind == PickupKind.Ember && k != B.HoardStone && !k.Pulled && Dist(k.X, k.Z, p.X, p.Z) <= 14)
            .OrderBy(k => Dist(k.X, k.Z, p.X, p.Z)).Take(12).Select(k => Up(k.X, k.Z, 0.3)).ToList();
    }

    /// <summary>When the Grave-Caller rose (game seconds): its floor holds 30 s at most.</summary>
    double callerAt;
    /// <summary>When the Knight's present windup began (game seconds).</summary>
    double knightWound = -1;
    /// <summary>Its windup was held once already for F7 waiting in the line.</summary>
    bool knightHeld;
    /// <summary>When the lamps' lure was last said (stage time): again every 30 s while all three burn, never every frame
    /// (asked each frame, its 10 s life ran out a frame at a time and it flickered).</summary>
    double lamps2At = -99;
    /// <summary>F7 freezes a beat into the windup, once its red lane is down and on the screen.</summary>
    const double LaneBeat = 0.3;

    /// <summary>The Knight's windups as they begin: the first is drawn out by the beat F7 freezes into
    /// it (its lane marked again for the longer wait), so the read never costs her the time to move.</summary>
    void KnightWatch()
    {
        if (B == null) return;
        // Until F7 is seen, its first red line waits for a moment it can be taught in (au1 item 10: the
        // first was drawn off the screen's middle, under another callout, and went untaught): it isn't
        // begun while another callout has the screen (a gate on her distance kept a kiting run from ever seeing it, m3).
        // i14 (F7 never showed in real runs, f7a): the first windup came under the Knight's own narrated line
        // (a freeze waits for a Say: dropped as gone when it ended), and the next with its head behind the
        // cracked wall (the freeze waits to see it: gone again). So none begins under a line, a draft or a
        // callout, nor while the Knight stands behind something tall.
        // The holds are bounded (f7 fix): out of the open it is held 4 s in all, and every hold together 10 s, so a Knight
        // behind something tall still attacks (v5: it stood 40 s and never wound up).
        double dt = Math.Clamp(B.Time - knightWatchT, 0, 0.5);
        knightWatchT = B.Time;
        bool holding = false;
        if (knight is { Alive: true, State: not EnemyState.Windup } kw && !G.Taught("red_line") && knightHeldAll < KnightHoldAll)
        {
            bool shut = !KnightOpen(kw);
            holding = G.Teaching != null || G.Saying || B.DraftOwed || (shut && knightHeldShut < KnightHoldShut);
            if (holding)
            {
                if (kw.RangedT <= 0.25) { knightHeldAll += dt; if (shut) knightHeldShut += dt; }
                kw.RangedT = Math.Max(kw.RangedT, 0.25);
            }
        }
        // (n1, MR5 item 12: wedged in a gap of the post's wall it stood 95 s on one spot, never a clear line to
        // her, never a windup: the nav grid's gaps are cut for a man (0.42 m), his bulk is 0.8. Stuck 1.5 s out
        // of her sight, he squeezes to a man's girth until he sees her or stands close, then fills out again.)
        if (knight is { Alive: true } ks)
        {
            if (B.Time - knightStuckAt >= 1.5)
            {
                bool clear = B.Collision.Raycast(ks.X, ks.Z, B.Player.X, B.Player.Z, 0.3) == null;
                double near = Dist(ks.X, ks.Z, B.Player.X, B.Player.Z);
                if (ks.State == EnemyState.Active && !clear && near > 2.5 && Dist(ks.X, ks.Z, knightStuckX, knightStuckZ) < 0.3)
                {
                    if (ks.Radius > 0.45) PaceNotes.Enqueue($"pace knight squeeze t={B.Time:0.0} at=({ks.X:0.0},{ks.Z:0.0})");
                    ks.Radius = 0.42;
                }
                else if (clear || near <= 2.5) ks.Radius = ks.Def.Radius;
                knightStuckAt = B.Time; knightStuckX = ks.X; knightStuckZ = ks.Z;
            }
        }
        // (until F7 is taught, with no hold on it, it may begin its run from close: it stood in melee reach for 10 to 20 s and never lunged)
        if (knight is { Alive: true } kl) kl.LungeMin = !G.Taught("red_line") && !knightRan && !holding ? 0.3 : 2;
        if (knight is { Alive: true } kd && B.Time - knightDiagAt >= 3)
        {
            knightDiagAt = B.Time;
            PaceNotes.Enqueue($"pace knight watch t={B.Time:0.0} state={kd.State} rangedT={kd.RangedT:0.0} dist={Dist(kd.X, kd.Z, B.Player.X, B.Player.Z):0.0} los={B.Collision.Raycast(kd.X, kd.Z, B.Player.X, B.Player.Z, 0.3) == null} held={knightHeldAll:0.0}/{knightHeldShut:0.0} open={KnightOpen(kd)} lungeMin={kd.LungeMin:0.0}{(knightHeldAll >= KnightHoldAll && B.Collision.Raycast(kd.X, kd.Z, B.Player.X, B.Player.Z, 0.3) != null ? " NO_CLEAR_RAY" : "")}");
        }
        if (knight is not { Alive: true, State: EnemyState.Windup } k) { knightWound = -1; knightHeld = false; return; }
        // (asked and waiting all the same: the windup is held, once, a beat and a half longer, its lane marked again)
        if (knightWound >= 0 && !knightHeld && !G.Taught("red_line") && G.TeachWaiting("red_line") && (k.Def.Charge ?? k.Def.Lunge) is { } held)
        {
            knightHeld = true;
            k.StateT += 1.5;
            double r = held.Speed * held.Time;
            B.Events.Emit(new Ev.Telegraph
            {
                Id = k.Id, Shape = TelegraphShape.Line, X = k.X, Z = k.Z, X1 = k.X + k.LungeX * r, Z1 = k.Z + k.LungeZ * r,
                Radius = k.Radius, Width = k.Radius * 2.2, Duration = k.StateT, Hostile = true,
            });
        }
        if (knightWound >= 0) return;
        knightWound = B.Time;
        PaceNotes.Enqueue($"pace knight windup t={B.Time:0.0} held={knightHeldAll:0.0} open={KnightOpen(k)}");
        // (every windup until F7 is seen: the one it freezes in is the one drawn out)
        if (G.Taught("red_line") || (k.Def.Charge ?? k.Def.Lunge) is not { } lunge) return;
        k.StateT += LaneBeat;
        double reach = lunge.Speed * lunge.Time;
        B.Events.Emit(new Ev.Telegraph
        {
            Id = k.Id, Shape = TelegraphShape.Line, X = k.X, Z = k.Z, X1 = k.X + k.LungeX * reach, Z1 = k.Z + k.LungeZ * reach,
            Radius = k.Radius, Width = k.Radius * 2.2, Duration = k.StateT, Hostile = true,
        });
    }

    /// <summary>Seconds the Knight has been held (ready to wind up) for standing out of the open, and for any hold at all.</summary>
    double knightDiagAt = -9;
    double knightStuckAt = -9, knightStuckX, knightStuckZ;
    double knightHeldShut, knightHeldAll, knightWatchT;
    /// <summary>The most it is held for being out of the open, and for everything together.</summary>
    const double KnightHoldShut = 4, KnightHoldAll = 10;
    /// <summary>Lines for the --pace log, taken by the game each frame (this layer has no console).</summary>
    public readonly Queue<string> PaceNotes = new();

    double knightOpenAt = -9;
    bool knightOpen;
    /// <summary>Whether the Knight stands in the open from the camera, foot to crown (asked 4 times a second).</summary>
    bool KnightOpen(Enemy k)
    {
        if (B!.Time - knightOpenAt < 0.25) return knightOpen;
        knightOpenAt = B.Time;
        return knightOpen = G.OpenGround(k.X, k.Z, 1.62 * (k.Def.Scale ?? 1));
    }

    /// <summary>The Barrow Knight's lane while it is marked (its windup), a beat after it was: points along
    /// it, those clear of her first (the arrow lands on the lane, never her figure), then nearest her.</summary>
    IReadOnlyList<(double X, double Y, double Z)> KnightLane()
    {
        if (knight is not { Alive: true, State: EnemyState.Windup } k || (k.LungeX == 0 && k.LungeZ == 0) || knightWound < 0 || B!.Time - knightWound < LaneBeat)
            return [];
        double reach = (k.Def.Charge ?? k.Def.Lunge) is { } l ? l.Speed * l.Time : 6;
        var p = B.Player;
        // (and clear of the chest: a ring by it reads as the chest's, judge 1)
        var chest = L("chest");
        return new[] { 0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8 }
            .Select(f => (X: k.X + k.LungeX * reach * f, Z: k.Z + k.LungeZ * reach * f))
            .OrderBy(q => Dist(q.X, q.Z, p.X, p.Z) < 2.4 ? 1 : 0)
            .ThenBy(q => Dist(q.X, q.Z, chest.X, chest.Z) < 3 ? 1 : 0)
            .ThenBy(q => Dist(q.X, q.Z, p.X, p.Z))
            .Select(q => Up(q.X, q.Z, 0.1)).ToList();
    }

    /// <summary>Whether the Grave-Caller's coming has filled her Flare (once, for F8).</summary>
    bool callerFilled;

    /// <summary>When a callout was last up (game seconds): F8 asks 4 s clear of the other lessons.</summary>
    double lessonUpAt = -99;

    /// <summary>F8: patient while the Grave-Caller lives; 4 s clear of the other lessons (asked so), and
    /// straight after the Barrow's line (a line is not a lesson: n1, a lesson's quiet held it 4 s past the
    /// line, 17 s into a short fight, the Grave-Caller already beaten down).</summary>
    void ArtLesson(string title, string line, Aim aim) =>
        G.Teach(new Callout("art", CalloutKind.Freeze, title, line, aim, "flare")
        { Gap = 1, Patience = 25, Still = () => Now == Stage.Barrow && caller is { Alive: true } });

    void Callouts()
    {
        if (B == null) return;
        var p = B.Player;
        KnightWatch();
        if (B.FlareGreatsHeld && (G.Taught("art") || Now >= Stage.ToFord)) B.FlareGreatsHeld = false;
        // F1: the first ember on the ground near her (one well inside the screen: it waits for one). Asked only
        // while one lies near (asked at any ember on the field, it was let go as gone at once and F2 came first,
        // 43.6 s against 49.2, i14), and never after F2 (the explanation reads in order or not at all).
        if (Now == Stage.Rising && B.EmbersLying > 0 && !G.Taught("ember_bar") && NearEmbers().Count > 0)
            Teach("ember_ground", CalloutKind.Freeze, "Ember", "The light the dead carry. Come close and it comes to you.", new Aim { World = NearEmbers, Safe = true });
        // F2: straight after F1 (before the first rise); without F1 only once the Rising is 30 s old.
        if (Draft && (G.Taught("ember_ground") || (B.EmberXp > 0 || B.EmberLevel > 1) && (Now != Stage.Rising || stageT > 30)))
            Teach("ember_bar", CalloutKind.Arrow, "Rising", "Ember fills this. When it's full, the ember rises.", Aim.At("chain_fill"), after: "ember_ground", gap: 0.6, overHint: true);
        // (and the journal remembers what the valley believes, once an ember is gathered)
        if (B.EmberXp > 0 || B.EmberLevel > 1)
        {
            // (never in the boss fight: it stood over a lamp's burst, H4 r3; it comes when the fight is done)
            if (Now is not (Stage.Intro or Stage.Boss or Stage.Victory) && shown.Add("lore.ember"))
                G.Apply("""[{ "learn": "lore.ember", "text": "Ember: light that seeps up from under the valley. After dark the dead get up full of it, and it spills when they fall. At first light, what's in them sinks back into the ground." }]""");
        }
        // F4: the first skill draft, the ember's first rise (on the panel, at the first combat-skill card).
        if (Draft && B.EmberLevel >= 2 && B.DraftOwed && B.GreatOwed == 0)
            Teach("first_draft", CalloutKind.Panel, "A skill", "The ember lends you skills as it rises. Choose one.", Aim.At("cards"));
        // F5: the first combat skill on the console.
        if (Draft && startWeapons >= 0 && B.Weapons.Count > startWeapons)
        {
            var w = B.Weapons[startWeapons];
            Teach("first_skill", CalloutKind.Arrow, w.Def.Name, "It fires on its own, like your weapon. First light takes it back.", Aim.At("socket:" + w.Id), after: "first_draft");
        }
        // The lock (au1 item 14: the "4" on it was never taught; MR5: it moves to the second rise): once the ember
        // has risen a second time (level 3) and that draft is picked and closed, in the Rising or the Road,
        // 4 s clear of anything else (Experience 9: no crowd gate; the Rising stays crowded after the 2nd rise, so
        // v6 never asked it until the Road; the arrow sits on the HUD, off the fight). Dropped unseen ("passed") once the Ambush begins.
        if (Draft && B.EmberLevel >= 3 && !B.DraftOwed && Now is Stage.Rising or Stage.Road)
            G.Teach(new Callout("ember_lock", CalloutKind.Arrow, "The ember's count", $"Hold {Key("experience")} to see the ember's level, and how far it is to the next.", Aim.At("card"))
                { Quiet = LessonQuiet, Mark = "level", Patience = 30, Still = () => Now is Stage.Rising or Stage.Road });
        // The tally (the slain and the gold): with the first gold in hand (the wagon's spilled coins), before
        // the ditch rises (the trap waits for it) or in a calm later, never in a fight. The road's words wait for it (PaceWords).
        if (B.GoldGained > 0 && TallyCalm())
            G.Teach(new Callout("tally", CalloutKind.Arrow, "The tally", "How long you've lasted, the dead you've put down, and your gold.", Aim.At("tally"))
                { Quiet = LessonQuiet, Mark = "gold", Patience = 30, Still = TallyCalm });
        // F6: the ditch's first volley in the air at her, so the roll answers a real danger (au i15: it was
        // taught in the Rising with nothing to dodge, her health full until 2:46). Only while the bolts fly (a
        // short patience: never late, after they land; the next volley asks again); 20 s on, or past the
        // Ambush, it comes all the same.
        if (dashAt == double.MaxValue && G.Taught("dash")) dashAt = B.Time;
        bool volley = Now == Stage.Ambush && sprungAt >= 0 && VolleyIn();
        if (volley || (Now == Stage.Ambush && sprungAt >= 0 && stageT - sprungAt > 20) || Now is Stage.Road2 or Stage.Post)
            Teach("dash", CalloutKind.Freeze, "Dash",
                volley ? $"{Key("dash")}: roll through the bolts; nothing touches you mid-roll. Two charges; they come back." : $"{Key("dash")}: a roll nothing can touch. Two charges; they come back.",
                volley ? new Aim { Hud = "dash", World = Bolts, Each = true } : Aim.At("dash"), "dash",
                overHint: volley, patience: volley ? 0.5 : 8);
        // F6b: her calling's art rides the dash (Forms.cs); in the Ambush, lit, with the dead close round her,
        // 10 s after F6 at the soonest (two freezes on the dash, so each is read). The Warden's channel later
        // asks for it by name (au1 item 4).
        if (Now == Stage.Ambush && sprungAt >= 0 && G.Taught("dash") && B.Time - dashAt > 10 && B.FormReady && Crowd(p.X, p.Z, 6) >= 4 && B.Ability is AbilityKind fk && FormWords(fk) is string fw)
            Teach("form", CalloutKind.Freeze, Abilities.All[fk].Name, $"When your dash is aflame, it's {fw}", Aim.At("dash"), "dash", after: "dash");
        // F7: the Barrow Knight's first red line.
        if (KnightLane().Count > 0)
            Teach("red_line", CalloutKind.Freeze, "Red line", "The Knight is about to strike along this line. Get off it.", new Aim
            {
                // (MR5 item 5: the Knight himself ringed, the arrow on his lane where she stands. Hidden behind
                // something tall, the lane alone: its point must be in the open, nothing more (item 12: asking
                // every lane point to be in the open let a lane half behind the wall wait out the windup))
                World = KnightLane, Safe = true, Open = true,
                Seen = () => knight is { Alive: true } kn && KnightOpen(kn) ? [Up(kn.X, kn.Z, 1.25 * (kn.Def.Scale ?? 1)), Up(kn.X, kn.Z, 1.62 * (kn.Def.Scale ?? 1))] : [],
                Ring = () => knight is { Alive: true } kn && KnightOpen(kn) ? [Up(kn.X, kn.Z, 0.95 * (kn.Def.Scale ?? 1))] : [],
                RingRadius = 0.75 * 1.45,
            }, markInk: "#ff3b3b"); // scarlet, lifted from the telegraph's #ff0612 to read on the panel (5.6:1 vs 5.0:1)
        // F8: the Grave-Caller near and what Q casts ready. Q is the art until the Flare lands; once it
        // has (B.Flare), Q is the Flare and its ring shows the meter, so it waits for the meter full and
        // names the Flare (the art then rides the dash).
        // (MR5 item 10: in real play she has the Flare by the Barrow and its meter was never full while the
        // Grave-Caller stood (v4, v5: never shown; f7c/d: shown as the last of the dead fell). So the ember
        // answers the Grave-Caller: the first time it is up and near, her Flare fills, once, and the lesson
        // asks while it lives, with the quiet of a lesson (4 s clear of the rest).)
        bool callerUp = Now == Stage.Barrow && caller is { Alive: true, State: not (EnemyState.Rising or EnemyState.Dying) } cu && Dist(cu.X, cu.Z, p.X, p.Z) < 16;
        if (callerUp && !G.Taught("art") && !callerFilled && B.Flare != null)
        {
            callerFilled = true;
            B.FlareMeter = Math.Max(B.FlareMeter, Battle.FlareFull);
            PaceNotes.Enqueue($"pace art fill t={B.Time:0.0} meter={B.FlareMeter:0}");
        }
        if (G.Teaching != null) lessonUpAt = B.Time;
        if (callerUp && G.CurrentHint?.Id != "pack" && B.Time - lessonUpAt >= LessonQuiet && (B.Flare != null ? B.FlareReady : B.Ability is AbilityKind && p.AbilityCd <= 0))
        {
            var aim = new Aim { Hud = "art", World = () => caller is { Alive: true } c ? [Up(c.X, c.Z, 1.4)] : [] };
            if (B.Flare is { } fl)
                ArtLesson(fl.Name, $"{Key("flare")}: your Flare, the ember's great blow.\nIt's full: spend it on the Grave-Caller\nbefore it raises more.", aim);
            else if (B.Ability is AbilityKind ak)
            {
                var ab = Abilities.All[ak];
                ArtLesson(ab.Name, ab.Interrupts
                        ? $"{Key("flare")}: your art. It breaks the Grave-Caller's channel."
                        : $"{Key("flare")}: your art. Kill the Grave-Caller before it raises more.", aim);
            }
        }
        // F9: the lamps, 3 s after C02 hands back.
        if (Now == Stage.Boss && stageT > 3 && warden is { Alive: true } && LitCount > 0)
            Teach("lamps", CalloutKind.Freeze, "The lamps", "Three lamps guard the Warden. While they burn, he barely feels a blow.\nPut them out: break them, or lure his charge into one.",
                new Aim { World = () => pylons.Select((l, i) => (l, i)).Where(q => litPylons[q.i]).Select(q => (q.l.X, lampY[q.i], q.l.Z)).ToList(), Each = true, Radius = 0.25,
                    Cold = true, WordsNear = (0.24, 0.7), ShunBig = true });
        // F10: her health under 70% for the first time (MR5: it was half), with a draught to drink (au i15: under 40% a real
        // run never came, 42% at the lowest; the ambush's volley and the Knight bring it down before the ford).
        // (MR5 item 11: it never waits to see her clear of roofs and canopies. Its target is the HUD's draught slot and
        // the freeze shows her anyway; a queued ask keeps the Aim it was first asked with, so amb5's, asked at 70%,
        // waited out its patience for "notyet" and came at 16%. Its gap after another freeze or a draft is 3 s, not 5:
        // urgent, its moment is now, and it still leaves a beat of play between two freezes.)
        if (p.Alive && p.Hp < B.MaxHp * 0.7 && G.Journey.Draughts > 0)
        {
            // (MR5 judge r2: never on the Knight's windup, nor 1.5 s after his windup/lunge ends. The ask is withheld, and
            // a queued one is let go by Still the tick he winds up; asked again every tick, it requeues once the hold ends.)
            if (knight is { Alive: true } kd && kd.State is EnemyState.Windup or EnemyState.Lunging) knightBusyAt = B.Time;
            if (!KnightHolds())
                G.Teach(new Callout("draught", CalloutKind.Freeze, "Draught", $"Drink a draught to mend: {Key("draught")}.", new Aim { Hud = "draught" }, "draught")
                    { Gap = 3, Urgent = true, Still = () => !KnightHolds() });
        }
        // F12: the first character level, after her dawn line, at its banner (shown again under it).
        if (levelDue && levelAnn != null && !finished && DayCalm())
            G.Teach(new Callout("level", CalloutKind.Freeze, "What the night taught you", LevelLine(), new Aim { Hud = "banner", Banner = levelAnn }) { Mark = "traits" });
        // F13 waits for the Flare on Q (docs/design/CLASSES.md): its meter first full. Not fired yet:
        // Teach("flare", CalloutKind.Freeze, "Flare", $"{Key("flare")}: your Flare. It fills fastest when you're in trouble.", Aim.At("art"), "flare");
        DayCallouts();
    }

    /// <summary>A calm for the tally's lesson: the road before the trap springs, the walks between fights,
    /// the dawn; nothing hostile within 8 m.</summary>
    bool TallyCalm() => B != null && (Now is Stage.Road or Stage.Road2 or Stage.ToFord or Stage.Dawn || Now == Stage.Ambush && sprungAt < 0)
        && Crowd(B.Player.X, B.Player.Z, 8) == 0;
    /// <summary>When the tally's lesson was last waiting or up (Ambush stage time): the trap springs 2 s after it.</summary>
    double tallyHeldAt = -99;

    /// <summary>When F6 was first seen taught (game seconds): F6b keeps its distance from it.</summary>
    double dashAt = double.MaxValue;

    /// <summary>The bowmen's bolts in flight (F6's world marks).</summary>
    IReadOnlyList<(double X, double Y, double Z)> Bolts() =>
        B == null ? [] : B.Projectiles.Living().Where(pr => pr.Owner == Side.Enemy && bowmen.Any(e => e.Id == pr.OwnerId))
            .Select(pr => (pr.X, pr.Y, pr.Z)).ToList();

    /// <summary>A bolt of the bowmen's in the air, within 4 m of her and coming at her.</summary>
    bool VolleyIn()
    {
        if (B == null || bowmen.Count == 0) return false;
        var p = B.Player;
        foreach (var pr in B.Projectiles.Living())
        {
            if (pr.Owner != Side.Enemy || !bowmen.Any(e => e.Id == pr.OwnerId)) continue;
            double dx = p.X - pr.X, dz = p.Z - pr.Z;
            if (dx * dx + dz * dz < 16 && dx * pr.Vx + dz * pr.Vz > 0) return true;
        }
        return false;
    }

    /// <summary>The wagon's trap springs (au i15): the drowned up out of the ditch around her, and a file of bowmen
    /// on its far side, ahead of her and in the open, who loose together once they stand.</summary>
    void Spring()
    {
        if (B == null) return;
        sprungAt = stageT;
        takenAtSpring = B.DamageTaken;
        Objective([("Follow the road north", true, false), ("Survive the ambush at the wagon", false, false)]);
        // (M5: the wagon's ditch is the night's n_cart beat, sprung round her; its bowmen loose one volley together, a
        // second after they stand, their first bolts AmbushBolt harder, and its risen_warrior's charge is the dash's lane)
        if (night?.S.Get("n_cart") is not { } nc) return;
        night.Spring(nc);
        foreach (var e in night.Standing("n_cart"))
        {
            if (e.Def.Id != "risen_archer") continue;
            e.RangedT = 1.0;
            e.Damage *= AmbushBolt;
            bowmen.Add(e);
        }
    }

    /// <summary>What the calling's art does when it rides the dash, in F6b's words (none: no callout).</summary>
    static string? FormWords(AbilityKind k) => k switch
    {
        AbilityKind.BullRush => "a charge\nthat throws the dead aside.\nBig ones stop it, but they're stunned,\nand their spell breaks.",
        AbilityKind.Grapple => "a hooked chain.\nIt hauls you to the first thing\nin its way, and stuns it.",
        AbilityKind.MirrorStep => "a step\nthat leaves two reflections.\nWhat hunts you turns on them.",
        AbilityKind.Vault => "a spring\nback through the air.\nIt leaves snares where you stood.",
        _ => null,
    };

    const string NL = "\n";
    static readonly string[] Numbers = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"];
    static string Count(int n) => n >= 0 && n < Numbers.Length ? Numbers[n] : n.ToString();

    /// <summary>F12 (au1 item 13: the first level the player sees reads "Level 5", four earned unseen, and a
    /// trait was never told from a skill): what the night paid, that it's kept, and what to do with it.</summary>
    string LevelLine()
    {
        string levels = levelsTaught == 1 ? "a level" : $"{Count(levelsTaught)} levels";
        string choose = traitsDue > 1 ? $"Press {Key("character")} to choose {Count(traitsDue)}." : traitsDue == 1 ? $"Press {Key("character")} to choose one." : $"Press {Key("character")} to spend them.";
        return $"You gained {levels} tonight, and they're yours to keep.{NL}The ember's skills were only lent; traits stay.{NL}{choose}";
    }

    /// <summary>How many of the hostile dead stand within r of a point.</summary>
    int Crowd(double x, double z, double r) => B?.Enemies.Living().Count(e => e.State is not (EnemyState.Dying or EnemyState.Rising) && e.Disposition == Disposition.Hostile && Dist(e.X, e.Z, x, z) < r) ?? 0;
    void Go(Stage s) { Now = s; stageT = 0; }

    bool OpenGround(double x, double z)
    {
        if (B == null || B.Collision.Blocked(x, z, 0.6)) return false;
        if (Math.Abs(z - RiverZ(x)) < 9 && Math.Abs(x) > 14) return false;
        return Math.Abs(x) < 72 && Math.Abs(z) < 122;
    }

    /// <summary>The ditch's bowmen's opening volley: how much harder its bolts hit than the road's.</summary>
    const double AmbushBolt = 1.5;
    /// <summary>Seconds into the wagon's fight after which its last two stragglers no longer hold the road.</summary>
    const double AmbushStragglers = 30;
    /// <summary>What she had taken when the trap sprang (Battle.DamageTaken).</summary>
    double takenAtSpring;
    /// <summary>The Knight is winding up or lunging, or did within 1.5 s (the draught lesson waits).</summary>
    // (Experience 9, v8: also while F7 is still to come, above 40% HP: the draught freeze landed 1.5 s before F7's.)
    bool KnightHolds() => knight is { Alive: true } k && (k.State is EnemyState.Windup or EnemyState.Lunging || B != null && B.Time - knightBusyAt < 1.5
        || !G.Taught("red_line") && B != null && B.Player.Hp >= B.MaxHp * 0.4);
    double knightBusyAt = -99;

    /// <summary>The bowmen who have loosed their opening volley (their bolts back to the road's).</summary>
    readonly HashSet<int> boltsSpent = new();

    int Hostiles() => B?.Enemies.Living().Count(e => e.State != EnemyState.Dying && e.Disposition == Disposition.Hostile) ?? 0;

    void ClearAround(double x, double z, double r)
    {
        if (B == null) return;
        foreach (var e in B.Enemies.Living().ToList())
            if (!e.Boss && e != grim && Dist(e.X, e.Z, x, z) < r) B.KillEnemy(e, false, null);
    }

    /* ---------------------------------------------------- the Ford-Warden -- */

    public int LitCount => litPylons.Count(l => l);

    /// <summary>The lamp posts (x, lamp height, z) and whether each burns; only while the boss fight is on (the HUD points at the lit ones off screen).</summary>
    public IEnumerable<(double X, double Y, double Z, bool Lit)> LampPosts =>
        Now != Stage.Boss ? Enumerable.Empty<(double, double, double, bool)>()
        : pylons.Select((p, i) => (p.X, lampY[i], p.Z, litPylons[i]));

    /// <summary>His life by H6's teeth (Teeth.Ford's hpMul), on each spawn.</summary>
    void Toothed(Enemy? e)
    {
        if (e == null || Teeth.Ford is not { HpMul: > 0 } fw || fw.HpMul == 1) return;
        e.MaxHp *= fw.HpMul; e.Hp = e.MaxHp;
    }

    /// <summary>When a floor last turned a blow (game seconds): "Warded" says so at most every WardedEvery s.</summary>
    double wardedAt = -99, overSeen, floorHeldT, wardLogAt = -99;
    int wardCracks, lampsBroken;
    const double WardedEvery = 4;

    /// <summary>The lamps' floor under his life (never above it: a relit lamp does not heal him), and the backstop
    /// until he has fought MinSeconds; a blow the floor turns says "Warded" over him.</summary>
    void WardFloor(Enemy e, Teeth.FordWarden? fw, double dt)
    {
        if (B != null && Now == Stage.Boss && B.Time - wardLogAt >= 1 && PaceNotes.Count < 64)
        {
            wardLogAt = B.Time;
            PaceNotes.Enqueue($"ford wardlog t={B.Time:0.0} fought={stageT:0.0} fw={(fw == null ? "null" : "set")} hp={e.Hp:0}/{e.MaxHp:0} floor={e.HpFloor:0} taken={e.TakenMul:0.00} pylons={pylons.Count} broken={lampsBroken} cracks={wardCracks} lit={LitCount} over={e.Overflow:0} mode={ai.Mode} state={e.State}");
        }
        if (fw == null || B == null) { e.HpFloor = 0; return; }
        // (by the lamps broken this fight, never taken back by a relight: H8's b_path had his channels relight them
        // six times over 338 s; the ward, what a blow does, stays by the lamps lit)
        double k = fw.Floors is { Length: 4 } fl ? fl[Math.Clamp(pylons.Count - lampsBroken - wardCracks, 0, 3)] : 0;
        if (Now == Stage.Boss && stageT < fw.MinSeconds) k = Math.Max(k, fw.Backstop);
        double floor = k * e.MaxHp;
        // (a floor of 0 is none; a floor over his life now is his life: a relight never heals him)
        e.HpFloor = floor <= 0 ? 0 : Math.Min(floor, Math.Max(e.Hp, 1));
        // Held at a floor too long: it cracks a step, said over him.
        if (e.HpFloor > 0 && e.Hp <= e.HpFloor + 1 && Now == Stage.Boss)
        {
            floorHeldT += dt;
            if (fw.CrackAfter > 0 && floorHeldT > fw.CrackAfter && pylons.Count - lampsBroken - wardCracks > 0)
            {
                wardCracks++; floorHeldT = 0;
                B.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = "The ward cracks", Boss = true });
                PaceNotes.Enqueue($"ford ward cracks t={B.Time:0.0} fought={stageT:0.0} lit={LitCount} cracks={wardCracks}");
            }
        }
        if (e.Overflow > overSeen + 1)
        {
            if (B.Time - wardedAt > WardedEvery)
            {
                wardedAt = B.Time;
                B.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = LitCount > 0 ? "Warded: the lamps hold him" : "Warded" });
                PaceNotes.Enqueue($"ford warded t={B.Time:0.0} fought={stageT:0.0} lit={LitCount} hp={e.Hp / e.MaxHp:0.00}");
            }
        }
        overSeen = e.Overflow;
    }

    void Snuff(int i, string how)
    {
        if (!litPylons[i] || B == null) return;
        litPylons[i] = false;
        if (Now == Stage.Boss) lampsBroken++;
        lampEventAt = B.Time;
        var p = pylons[i];
        G.Look.SetLit(p.Light, false);
        B.Events.Emit(new Ev.Explosion { X = p.X, Z = p.Z, Radius = 3.2, School = School.Frost, Power = 1.4 });
        B.Events.Emit(new Ev.Shake { Amount = 0.6 });
        // (one line a lamp event: "The Warden reels!" stacked on it at the burst, H4 r3; the tip up steps aside for the burst)
        B.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z, Text = how == "charge" ? "The lamp shatters!" : "The lamp goes dark" });
        // (H4 r3 judge: the lamps tip taught the move she just made: a charge into a lamp clears it, and it stays down 30 s)
        if (how == "charge" && (G.CurrentHint?.Id == "lamps2" || lampTipWaiting.Contains("lamps2")))
        {
            if (G.CurrentHint?.Id == "lamps2") G.SetHint(null);
            shown.Add("lamps2"); lamps2At = stageT;
        }
        else G.DuckTip(1.3);
        B.Events.Emit(new Ev.Sound { Id = how == "charge" ? "ford.lamp_shatter" : "ford.lamp_out", X = p.X, Z = p.Z });
        int left = LitCount;
        if (left > 0) G.Toast(new Toast(ToastKind.World, $"A lamp goes out — {left} still burn{(left == 1 ? "s" : "")}"));
        else G.Announce(new Announcement("The lamps are dark", "The Warden is laid bare", "boon", 3.2));
    }

    void Relight()
    {
        int i = Array.IndexOf(litPylons, false);
        if (i < 0) return;
        litPylons[i] = true;
        if (B != null) lampEventAt = B.Time;
        pylonHp[i] = 200;
        G.Look.SetLit(pylons[i].Light, true);
        B?.Events.Emit(new Ev.Nova { X = pylons[i].X, Z = pylons[i].Z, Radius = 4, School = School.Frost, Duration = 0.8 });
        G.DuckTip(1.3);
        G.Toast(new Toast(ToastKind.Warning, "The drowned rekindle a lamp"));
    }

    BossBar? bar;
    void Bar(BossBar? b) { bar = b; G.SetBoss(b); }

    bool WardenTick(Enemy e, double dt)
    {
        if (B == null) return true;
        var p = B.Player;
        ai.T += dt;
        e.Vx = e.Vz = 0;
        double dx = p.X - e.X, dz = p.Z - e.Z;
        double dist = Math.Sqrt(dx * dx + dz * dz);
        if (dist == 0) dist = 0.001;
        double hpK = e.Hp / e.MaxHp;
        // The ward: the lamps take most of every blow; and (H8, N20) while two or three burn he can't be brought under
        // their floor, so the crash is the way through (Teeth.Ford, H6's numbers).
        var fw = Teeth.Ford;
        double mul = (fw?.Ward is { Length: 4 } wd ? wd : Ward)[LitCount];
        WardFloor(e, fw, dt);
        if (ai.Mode == "stun") mul *= 1.5;
        e.TakenMul = mul;
        ai.CleaveCd -= dt; ai.ChargeCd -= dt; ai.ChannelCd -= dt;
        // Interrupted mid-channel (Battle.Interrupt sets this).
        if (ai.Mode == "channel" && e.State == EnemyState.Stunned)
        {
            ai.Mode = "stun"; ai.T = 0; e.StateT = 0;
            wardenView.SetPose("stunned");
            B.Events.Emit(new Ev.Announce { Title = "Channel broken", Tone = Tone.Boon });
            B.Events.Emit(new Ev.Sound { Id = "ford.channel_broken" });
        }
        e.State = ai.Mode == "channel" ? EnemyState.Casting : ai.Mode is "windup" or "chargeWind" ? EnemyState.Windup : EnemyState.Active;

        switch (ai.Mode)
        {
            case "sleep":
            case "wake":
                return true;
            case "walk":
            {
                e.Facing = Math.Atan2(dz, dx);
                if (ai.Hold > 0) { ai.Hold -= dt; e.Vx = e.Vz = 0; ai.ContactT -= dt; return true; }
                // Channel at thresholds, or when it has been a while.
                double? th = ai.Thresholds.Count > 0 ? ai.Thresholds[0] : null;
                if ((th is double t0 && hpK < t0) || ai.ChannelCd <= 0)
                {
                    if (th is double t1 && hpK < t1) ai.Thresholds.RemoveAt(0);
                    ai.Mode = "channel"; ai.T = 0; ai.ChannelHp = e.Hp; ai.ChannelOver = e.Overflow; ai.ChannelCd = 34; ai.RaiseT = 0.6;
                    wardenView.SetPose("channel");
                    B.Events.Emit(new Ev.Sound { Id = "ford.channel", X = e.X, Z = e.Z });
                    // (the tip comes first when it shows, and his cry a beat after it settles, so the two never
                    // land together: round 2 judge)
                    riseBarkIn = ChannelTip() ? 1.3 : 0;
                    if (riseBarkIn <= 0) RiseBark(e);
                    return true;
                }
                if (dist < 5.2 && ai.CleaveCd <= 0)
                {
                    ai.Mode = "windup"; ai.T = 0; ai.DirX = dx / dist; ai.DirZ = dz / dist;
                    ai.HitX = e.X + ai.DirX * 3; ai.HitZ = e.Z + ai.DirZ * 3;
                    B.Events.Emit(new Ev.Telegraph { Id = e.Id * 10 + 1, Shape = TelegraphShape.Circle, X = ai.HitX, Z = ai.HitZ, Radius = 3.4, Duration = 1.05, Hostile = true, Boss = true });
                    wardenView.SetPose("windup");
                    return true;
                }
                if (dist > 6.5 && ai.ChargeCd <= 0)
                {
                    ai.Mode = "chargeWind"; ai.T = 0; ai.DirX = dx / dist; ai.DirZ = dz / dist;
                    double len = Math.Min(24, dist + 8);
                    B.Events.Emit(new Ev.Telegraph { Id = e.Id * 10 + 2, Shape = TelegraphShape.Line, X = e.X, Z = e.Z, X1 = e.X + ai.DirX * len, Z1 = e.Z + ai.DirZ * len, Radius = 0, Width = 3, Duration = 1.3, Hostile = true, Boss = true });
                    ai.Travelled = len;
                    wardenView.SetPose("charge-windup");
                    B.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = "It lowers its head...", Boss = true });
                    return true;
                }
                if (dist > e.Radius + 1.2)
                {
                    double sp = e.Speed * (LitCount == 0 ? 1.25 : 1);
                    e.Vx = dx / dist * sp; e.Vz = dz / dist * sp;
                    e.X += e.Vx * dt; e.Z += e.Vz * dt;
                    B.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
                }
                wardenView.SetPose("walk");
                // Contact.
                ai.ContactT -= dt;
                if (dist < e.Radius + p.Radius + 0.4 && ai.ContactT <= 0)
                {
                    ai.ContactT = 1.2;
                    B.HurtPlayer(e.Damage * 0.6, School.Physical, "The Ford-Warden", e);
                }
                return true;
            }
            case "windup":
                if (ai.T >= 1.05)
                {
                    ai.Mode = "cleave"; ai.T = 0;
                    wardenView.SetPose("cleave");
                    if (Dist(p.X, p.Z, ai.HitX, ai.HitZ) < 3.4 + p.Radius) B.HurtPlayer(e.Damage * 1.5, School.Physical, "The Ford-Warden", e);
                    B.Events.Emit(new Ev.Explosion { X = ai.HitX, Z = ai.HitZ, Radius = 3.4, School = School.Physical, Power = 1.2 });
                    B.Events.Emit(new Ev.Shake { Amount = 0.55 });
                }
                return true;
            case "cleave":
                if (ai.T > 0.8) { ai.Mode = "walk"; ai.CleaveCd = 3.2; wardenView.Release(); }
                return true;
            case "chargeWind":
                e.Facing = Math.Atan2(ai.DirZ, ai.DirX);
                if (ai.T >= 1.3) { ai.Mode = "charge"; ai.T = 0; wardenView.SetPose("charge"); }
                return true;
            case "charge":
            {
                const double sp = 17;
                double step = Math.Min(sp * dt, ai.Travelled);
                double x0 = e.X, z0 = e.Z;
                e.X += ai.DirX * step; e.Z += ai.DirZ * step;
                e.Vx = ai.DirX * sp; e.Vz = ai.DirZ * sp;
                ai.Travelled -= step;
                // A lamp in the way: it goes through it, and it hurts.
                for (int i = 0; i < pylons.Count; i++)
                {
                    var py = pylons[i];
                    if (litPylons[i] && Dist(py.X, py.Z, e.X, e.Z) < e.Radius + 0.9)
                    {
                        Snuff(i, "charge");
                        ai.Mode = "stun"; ai.T = -1.5;
                        wardenView.SetPose("stunned");
                        return true;
                    }
                }
                // Anything else solid stops it short.
                B.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
                double moved = Dist(e.X, e.Z, x0, z0);
                if (moved < step * 0.4)
                {
                    ai.Mode = "stun"; ai.T = 0.8;
                    wardenView.SetPose("stunned");
                    B.Events.Emit(new Ev.Shake { Amount = 0.5 });
                }
                else if (Dist(p.X, p.Z, e.X, e.Z) < e.Radius + p.Radius + 0.3 && p.Iframes <= 0)
                    B.HurtPlayer(e.Damage * 1.4, School.Physical, "The Ford-Warden", e);
                if (ai.Travelled <= 0.01 && ai.Mode == "charge") { ai.Mode = "walk"; ai.ChargeCd = 8 + B.Rng.Next() * 3; wardenView.Release(); }
                return true;
            }
            case "stun":
                if (ai.T >= 2.5) { ai.Mode = "walk"; ai.ChargeCd = Math.Max(ai.ChargeCd, 5); ai.CleaveCd = 1.5; wardenView.Release(); }
                return true;
            case "channel":
            {
                double k = ai.T / 6;
                if (riseBarkIn > 0 && (riseBarkIn -= dt) <= 0) RiseBark(e);
                if (bar != null) Bar(bar with { Channel = ("Raising the drowned: break it!", Math.Min(1, k)) });
                ai.RaiseT -= dt;
                if (ai.RaiseT <= 0)
                {
                    ai.RaiseT = 0.9;
                    for (int i = 0; i < 2; i++)
                    {
                        double a = B.Rng.Next() * Math.PI * 2, d = 4 + B.Rng.Next() * 6;
                        double x = e.X + Math.Cos(a) * d, z = e.Z + Math.Sin(a) * d;
                        if (OpenGround(x, z)) B.SpawnEnemy("risen", x, z, new Battle.SpawnOpts { Style = SpawnStyle.Rise, Level = 2 });
                    }
                }
                // Hurt it badly enough and the channel breaks.
                // (what a floor held back counts: at a floor his life does not move)
                if (ai.ChannelHp - e.Hp + e.Overflow - ai.ChannelOver > e.MaxHp * 0.09)
                {
                    ai.Mode = "stun"; ai.T = 0;
                    wardenView.SetPose("stunned");
                    B.Events.Emit(new Ev.Announce { Title = "Channel broken", Tone = Tone.Boon });
                    B.Events.Emit(new Ev.Sound { Id = "ford.channel_broken" });
            B.Events.Emit(new Ev.Sound { Id = "ford.channel_broken" });
                }
                else if (ai.T >= 6)
                {
                    e.Hp = Math.Min(e.MaxHp, e.Hp + e.MaxHp * 0.06);
                    Relight();
                    ai.Mode = "walk";
                    wardenView.Release();
                }
                if (ai.Mode != "channel" && bar != null) Bar(bar with { Channel = null });
                return true;
            }
            default:
                return true;
        }
    }

    /* ------------------------------------------------------------- stages -- */

    void Director(double dt)
    {
        if (B == null) return;
        var p = B.Player;
        stageT += dt;
        // (M5: the night's placed packs, from the fire to the ford; no top-ups: the stages advance on its beats)
        if (night != null && Now < Stage.Intro) { night.Tick(dt); Ranks(night); }
        if (Draft) GreatBlessing();
        Callouts();
        ChampionTipWatch();
        PaceWords();
        if (Now is Stage.Dawn or Stage.Exit) DayTick(dt);
        switch (Now)
        {
            case Stage.Wake:
                if (stageT > 1.2) Tip("move", "Move", "Keep *moving*. Your weapon strikes on its own.", ["W", "A", "S", "D"], 11);
                if (stageT > 3) { Go(Stage.Rising); risingAt = B.Time; }
                break;
            case Stage.Rising:
            {
                // (M5: the Rising is over once the lone one and the three on the road are down, or she is 20 m up the road)
                if (night == null || night.Done("n_lone") && night.Done("n_three") || p.Z < L("camp").Z - 1.5 - RisingRoad)
                {
                    Go(Stage.Road);
                    checkpoint = new XZ(p.X, p.Z);
                    G.Say("The ground goes still. For now. The road runs north, toward the Waystation.", null, 5);
                    Objective([("Survive the night", true, false), ("Follow the road north", false, false)]);
                    // The Road's beat (au i15): what spilled from the wagon lies in the road at its tail, bait she walks
                    // to before the trap (M5: the placed packs stay where they rest; nothing is cleared).
                    var wag = L("cart");
                    for (int i = 0; i < 3; i++)
                        B.SpawnPickup(PickupKind.Gold, wag.X - 1.5 + i * 1.4 + (B.Rng.Next() - 0.5), wag.Z + B.Rng.Next() * 1.5, 2 + i);
                    // (the road tip is folded in: it came with this line, and said what it and the objective say, au i15)
                    wordsFree = B.Time + WordsGap;
                }
                break;
            }
            case Stage.Road:
            case Stage.Road2:
            {
                var cart = L("cart"); var post = L("post");
                if (Now == Stage.Road && p.Z < cart.Z + 7)
                {
                    Go(Stage.Ambush);
                    checkpoint = new XZ(cart.X - 3, cart.Z + 8);
                    // (the wagon is quiet while its line is read; the ditch rises after, Spring, and the objective with it;
                    // M5: the line waits for the first pack at the wagon's approach to be down, Stage.Ambush)
                }
                if (Now == Stage.Road2 && Dist(p.X, p.Z, post.X, post.Z) < 18)
                {
                    Go(Stage.Post);
                    checkpoint = new XZ(post.X - 6, post.Z + 4);
                    // (M5: placed at nightfall, resting with its escort, n_post, until she comes near)
                    knight = knightRest is { Alive: true } kr && kr.Seed == knightRestSeed && kr.State != EnemyState.Dying ? kr : null;
                    // Its first red line comes once the narrator's line is over (F7 freezes on it), and it
                    // does not go down before it has run one: the elite shows what it does first.
                    if (knight != null)
                    {
                        knight.RangedT = 8;
                        knight.HpFloor = knight.MaxHp * 0.2;
                    }
                    Words(() => G.Say("Something in old armor is standing guard over the dead watchman. It turns to look at you.", null, 5));
                    Objective([("Survive the ambush at the wagon", true, false), ("Put down the Barrow Knight", false, false), ("Search the old Watch-post", false, false)]);
                }
                break;
            }
            case Stage.Ambush:
            {
                if (sprungAt < 0)
                {
                    // (the ditch rises once the wagon's line is read)
                    // (M5: the wagon's line once the first pack is down, or calm, or 20 s on)
                    if (!wagonQueued && (night == null || night.Done("n_first") || !night.Fighting || stageT > 20))
                    {
                        wagonQueued = true;
                        Words(() => { G.Say("A wagon on its side, and the ditch beside it full of the drowned. One of them is still holding the reins. They were waiting.", null, 5); wagonSaid = true; });
                    }
                    if (wagonSaid && !G.Saying && wagonDoneAt < 0) wagonDoneAt = stageT;
                    // (and the tally's lesson, if the coins were taken, 2 s gone: i14)
                    if (G.Teaching?.Id == "tally" || G.TeachWaiting("tally")) tallyHeldAt = stageT;
                    if ((wagonDoneAt >= 0 && stageT - wagonDoneAt >= 0.8 && stageT - tallyHeldAt >= 2 && night?.Fighting != true) || stageT > 40) Spring();
                    break;
                }
                double fought = stageT - sprungAt;
                // (--pace: her health each second of the fight's first 40 s, for the stakes' measure, MR5 item 11)
                if (fought < 50 && B.Time - ambDiagAt >= 1)
                {
                    ambDiagAt = B.Time;
                    PaceNotes.Enqueue($"pace amb t={B.Time:0.0} fought={fought:0.0} hp={p.Hp:0}/{B.MaxHp:0} ember={B.EmberLevel} foes={Hostiles()} bowmen={bowmen.Count(e => e.Alive)} taken={B.DamageTaken - takenAtSpring:0}");
                }
                // (MR5 item 11 round 2: the bolts are doubled for the opening volley only. A bowman who has loosed it
                // (his reload is up again) shoots the road's bolts after: amb5, five bowmen never killed, kept loosing
                // doubled bolts and an idle player lost 78% in 28 s, amb4 42%.)
                foreach (var bw in bowmen)
                    if (bw.Alive && bw.Def.Id == "risen_archer" && bw.RangedT > 1.5 && boltsSpent.Add(bw.Id)) bw.Damage /= AmbushBolt;
                // (the shield tip lands when shieldmen first stand, ~20 s into the fight)
                if (fought > 18) PacedTip("shield", "Shieldmen", "Their *raised shields* stop your shots. Strike from the side, or up close.");
                // (M5: over when the ditch's dead are down, n_cart; or, AmbushStragglers s into the fight, when no more
                // than two of them stand: they go back into the ditch, as the line says. m5 clip r1: two bowmen kept their
                // range off her for good, and the night stood at the wagon for nine minutes.)
                if (night != null && !night.Done("n_cart") && fought > AmbushStragglers && night.Standing("n_cart") is { Count: <= 2 } left)
                    foreach (var e in left) B.KillEnemy(e, false, null);
                if (night == null || night.Done("n_cart") || night.S.Get("n_cart") == null)
                {
                    Go(Stage.Road2);
                    checkpoint = new XZ(p.X, p.Z);
                    Words(() => G.Say("The last of them falls back into the ditch and stays there. The one with the reins was a girl, twelve at most: red hair under the weed, and new boots.", null, 5));
                    Objective([("Survive the ambush at the wagon", true, false), ("Follow the road north", false, false)]);
                }
                break;
            }
            case Stage.Post:
                // (F7 ended: the clock for the elite tip's 4 s without a red line on the ground)
                if (redEndAt < 0 && G.Taught("red_line") && G.Teaching?.Id != "red_line") redEndAt = stageT;
                bool knightDown = knight is not { Alive: true };
                bool lineOnGround = knight is { Alive: true } kw && kw.State == EnemyState.Windup;
                // (the elite tip: at the Knight's fall, or 4 s after F7 with no red line on the ground, whichever first)
                if (knightDown || (redEndAt >= 0 && stageT - redEndAt >= 4 && !lineOnGround))
                    PacedTip("elite", "Elites", "Bigger, tougher, and worth it: elites carry better things.", null, 12);
                if (knight is { Alive: true } kn && !knightRan)
                {
                    // (two windups finished, or a while has passed: then it may fall)
                    bool winding = kn.State == EnemyState.Windup;
                    if (knightWinding && !winding) knightWindups++;
                    knightWinding = winding;
                    if (knightWindups >= 2 || stageT > 48) { knightRan = true; kn.HpFloor = 0; }
                }
                // (the chest tip comes 4 s after the elite one; the E belongs to the prompt)
                if (knight == null && !chestOpened && eliteAt >= 0 && B.Time - eliteAt >= 4)
                    PacedTip("chest", "The Watch-post", "The *watchman's chest* is unguarded now.", null, 9, still: () => !chestOpened);
                if (knight == null && !chestOpened)
                {
                    Objective([("Put down the Barrow Knight", true, false), ("Search the old Watch-post", false, false)]);
                }
                if (p.Z < 21 && knight == null)
                {
                    Go(Stage.Barrow);
                    checkpoint = new XZ(p.X, p.Z);
                    StartBarrow();
                }
                break;
            case Stage.Barrow:
                // (the narrated line waits for the pack tip to have been up 8 s; with no chest opened, it doesn't wait)
                if (!barrowLineSaid && (!chestOpened || (packAt >= 0 && B.Time - packAt >= 8) || stageT > 30))
                {
                    barrowLineSaid = true;
                    Words(() => G.Say("Past the fence, a figure in a tall hat is talking to the graves. The graves are listening.", null, 6));
                }
                if (caller is { HpFloor: > 0 } cf && (G.Taught("art") || B.Time - callerAt > 30)) cf.HpFloor = 0;
                // (M5: no top-up; its own Raise does the raising. It rests till she comes, and its F8 hold counts from then.)
                if (caller is { Roused: false }) callerAt = B.Time;
                if (caller == null && stageT > 1)
                {
                    Go(Stage.ToFord);
                    var barrow = L("barrow");
                    checkpoint = new XZ(barrow.X + 10, barrow.Z - 6);
                    Objective([("Put down the Grave-Caller", true, false), ("Cross at the Low Ford", false, false)]);
                    Words(() => G.Say("The dead go quiet. Somewhere ahead, water, and a cold blue light.", null, 5));
                }
                break;
            case Stage.ToFord:
                // (no spawns: "the dead go quiet" is true)
                if (p.Z < L("ford").Z + 17) StartIntro();
                break;
            case Stage.Intro:
                RunIntro(dt);
                break;
            case Stage.Boss:
                if (warden is { Alive: true })
                {
                    int lit = LitCount;
                    Bar(new BossBar("The Ford-Warden", "Keeper of the Low Crossing", warden.Hp, warden.MaxHp, Teeth.Ford is { Floors: [_, _, > 0 and var f2, > 0 and var f3] } ? [f3, f2] : [0.7, 0.4], bar?.Channel, lit > 0, Lamps: pylons.Count, LampsLit: lit));
                    if (stageT > 40 && lit == 3 && stageT - lamps2At > 30) { lamps2At = stageT; shown.Remove("lamps2"); Tip("lamps2", "The lamps", "Lure its charge into a lamp: stand before one, and step aside at the last moment.", [Key("dash")], 10); }
                }
                break;
            case Stage.Victory:
                RunVictory(dt);
                break;
            case Stage.Dawn:
            {
                // C04 A (docs/cinematics/shoot/c04a.md): the sun waits for her on the
                // north bank (or 25 s, if she stays to loot the ford), and comes up in it.
                if (!doused && G.CanCinematic("c04a"))
                {
                    if (p.Z < -50 || stageT > 25) FirstLight(p.Z >= -50);
                    break;
                }
                dawnK = Math.Min(1, dawnK + dt / 10);
                // The sun clears the trees, and the ember goes out.
                if (!doused && dawnK > 0.3) { doused = true; Douse(); }
                envT -= dt;
                G.SetAtmosphere(Atmospheres.Dawning(dawnK * dawnK * (3 - 2 * dawnK)), envT <= 0);
                if (envT <= 0) envT = 1.2;
                if (dawnK >= 1 && stageT > 10) Go(Stage.Exit);
                break;
            }
            case Stage.Exit:
                MorningClimbs();
                // (and not while the wolf ring's second wave holds it, Encounters.GateOpen)
                // (through the gate, not anywhere along the wall's line: the day stretch runs 44 m either side of the road)
                // (H8 N22: and the portcullis all the way up: she may wait at it beyond the exit line, and sees it rise)
                if (p.Z < ExitZ && Math.Abs(p.X - L("gate").X) < 9 && day?.GateOpen != false && gateBar == null && gateDown <= 0 && !finished) { finished = true; Finish(); }
                break;
        }
    }

    const double BarrowWake = 12, RisingRoad = 20;
    double risingAt;

    /// <summary>A great blessing on its own panel, half a minute after the first skill (au1 item 2: it came with the
    /// first card, two picks and six lessons in 12 s); never on top of a level's draft. (M5: on the night's clock from
    /// the Rising, in the Rising or the road after it, so a short Rising does not lose it; the draft's only.)</summary>
    void GreatBlessing()
    {
        if (B == null || Now is not (Stage.Rising or Stage.Road or Stage.Road2)) return;
        double t = B.Time - risingAt;
        if (B.EmberLevel >= 2 && t > 40 && !B.DraftOwed && (G.Taught("first_draft") || t > 60) && shown.Add("great"))
        {
            B.GreatOwed++;
            // F3 says it on the panel (the general draft tip waits for the panels after it).
            Teach("great_blessing", CalloutKind.Panel, "A great blessing", "The ember lends you a blessing. It changes how you fight until dawn.", Aim.At("cards"));
        }
    }

    /// <summary>(M5) Each pack's captain wears its rank's body (Champions.Look: a step below a champion's) and its
    /// plate (FoeMarks); a crowned captain is a champion already.</summary>
    static void Ranks(Encounters enc)
    {
        foreach (var (e, seed) in enc.Captains.Values)
            if (e.Alive && e.Seed == seed && e.Rank == 0 && e.Named == null) Content.Champions.Look(e, 1);
    }

    /// <summary>The night laid out at nightfall (M5, encounters.json when: night): its packs resting on the road, the
    /// Barrow Knight at the post on its escort's ground.</summary>
    void StartNight(Battle b)
    {
        if (night != null || Encounters.For(Id) is not { } spec) return;
        night = new Encounters(spec, b, new Dictionary<string, Fact>(), G.Journey.Ch.Level, W.Day, "night", Meta.Features) { Held = () => G.Teaching != null, Tier = WorldTiers.Of(W) };
        night.Woke = bt => PaceNotes.Enqueue($"night woke {bt.Id} t={b.Time:0.0} hp={b.Player.Hp:0}/{b.MaxHp:0} at=({b.Player.X:0.0},{b.Player.Z:0.0})");
        night.Down = bt => PaceNotes.Enqueue($"night down {bt.Id} t={b.Time:0.0} hp={b.Player.Hp:0}/{b.MaxHp:0}");
        night.Place();
        var post = L("post");
        var np = spec.Get("n_post");
        knightRest = b.SpawnEnemy("barrow_knight", post.X - 1, post.Z - 1.5, new Battle.SpawnOpts
        {
            Level = 1, Tag = "knight", Style = SpawnStyle.Walk,
            Home = np != null ? (np.X, np.Z, np.Leash) : null, Wake = np?.Wake ?? 8,
        });
        if (knightRest != null) { knightRestSeed = knightRest.Seed; knightRest.Facing = Math.PI / 2; night.Crown(knightRest, "knight"); }
    }

    void StartBarrow()
    {
        if (B == null) return;
        Objective([("Search the old Watch-post", true, false), ("Put down the Grave-Caller", false, false)]);
        var barrow = L("barrow");
        // (M5: it and its dead rest at the barrow till she comes, BarrowWake: the road's packs lie between)
        var home = (barrow.X, barrow.Z, 20.0);
        caller = B.SpawnEnemy("grave_caller", barrow.X - 3, barrow.Z, new Battle.SpawnOpts { Level = 2, Tag = "caller", Elite = true, Home = home, Wake = BarrowWake });
        if (caller != null) night?.Crown(caller, "caller");
        // It can't fall before F8 has pointed at it (or a while has passed): the art is taught on it.
        if (!G.Taught("art")) { caller.HpFloor = caller.MaxHp * 0.2; callerAt = B.Time; }
        for (int i = 0; i < 5; i++)
        {
            double a = i / 5.0 * Math.PI * 2;
            B.SpawnEnemy(i % 3 == 0 ? "risen_warrior" : "risen", barrow.X + Math.Cos(a) * 4, barrow.Z + Math.Sin(a) * 4, new Battle.SpawnOpts { Style = SpawnStyle.Rise, Level = 2, Home = home, Wake = BarrowWake });
        }
    }

    /* ------------------------------------------------------------- intro -- */

    void StartIntro()
    {
        if (B == null) return;
        Go(Stage.Intro);
        words.Clear();
        cutT = 0;
        checkpoint = new XZ(0, L("ford").Z + 19);
        G.Capture(true);
        var ford = L("ford");
        ClearAround(ford.X, ford.Z, 30);
        B.WorldRate = 0.001; B.WorldRateT = 1e9;
        G.SetHint(null);
        // C02 (docs/cinematics/shoot/c02.md): its last cue spawns him where it
        // leaves him (CineEvent "warden_up"); without it, the captions and barks.
        if (G.Cinematic("c02", () => { if (Now == Stage.Intro) WardenUp(); })) { introByCine = true; return; }
        G.Showcase((wardenHome.X + 9, G.Look.HeightAt(wardenHome.X, wardenHome.Z) + 7, wardenHome.Z + 15), (wardenHome.X, 0.4, wardenHome.Z));
    }

    bool introByCine;
    /// <summary>After C02 he holds where the film leaves him this long (the hand-back and the HUD's fade), then moves.</summary>
    const double WakeHold = 1.0;

    /// <summary>C02's end: the Warden up and facing her an arm's length off, the fight on.</summary>
    void WardenUp()
    {
        if (B == null || warden != null) return;
        wardenInCine = false;
        var p = B.Player;
        // Where the cinematic leaves him (its mark warden_end), facing her.
        var (wx, _, wz, _) = CineFile.Load("c02").Mark("warden_end");
        warden = B.SpawnEnemy("ford_warden", wx, wz, new Battle.SpawnOpts { Level = 1, Tag = "warden" });
        Toothed(warden);
        if (warden != null)
        {
            warden.Facing = Math.Atan2(p.Z - wz, p.X - wx); ai.Mode = "walk"; ai.T = 0;
            // A beat after the bars go before his first blow: play opens 1.9 m from him (cinematics 3, k13).
            // (H4 r3: he stands in the film's last pose until the HUD is up, then comes on; was a step at her on the control frame)
            ai.Hold = WakeHold; ai.ContactT = WakeHold + 0.6; ai.CleaveCd = Math.Max(ai.CleaveCd, WakeHold + 0.6);
        }
        wardenPos = (wx, wz, Math.PI / 2 - (warden?.Facing ?? 0));
        wardenView.Release();
        Go(Stage.Boss);
        Objective([("Cross at the Low Ford", false, false), ("Put out the lamps", false, true)]);
    }



    void RunIntro(double dt)
    {
        if (B == null || introByCine) return;
        cutT += dt;
        if (cutT > 0.8 && shown.Add("intro1")) G.Say("Something lies in the ford, larger than any man, with a lamp in its fist.", null, 3.6);
        if (cutT > 1.4 && shown.Add("intro1b")) B.Events.Emit(new Ev.Bark { X = wardenPos.X, Z = wardenPos.Z, Text = "Lamps are lit... stay where they reach...", Speaker = "The Ford-Warden" });
        if (cutT > 3.4 && shown.Add("intro2b")) B.Events.Emit(new Ev.Bark { X = wardenPos.X, Z = wardenPos.Z, Text = "Lie down.", Speaker = "The Ford-Warden" });
        if (cutT > 2.6 && shown.Add("intro2"))
        {
            wardenView.SetPose("wake");
            B.Events.Emit(new Ev.Shake { Amount = 0.5 });
            foreach (var py in pylons) B.Events.Emit(new Ev.Nova { X = py.X, Z = py.Z, Radius = 3, School = School.Frost, Duration = 0.9 });
        }
        if (cutT > 4.2 && shown.Add("intro3"))
        {
            G.Announce(new Announcement("The Ford-Warden", "Keeper of the Low Crossing", "danger", 3.4));
            B.Events.Emit(new Ev.Bark { X = wardenPos.X, Z = wardenPos.Z, Text = "NONE. CROSS. AFTER DARK.", Speaker = "The Ford-Warden" });
        }
        if (cutT > 6.4)
        {
            G.Showcase(null);
            G.Capture(false);
            B.WorldRate = 1; B.WorldRateT = 0;
            warden = B.SpawnEnemy("ford_warden", wardenPos.X, wardenPos.Z, new Battle.SpawnOpts { Level = 1, Tag = "warden" });
            Toothed(warden);
            if (warden != null) { warden.Facing = Math.PI / 2; ai.Mode = "walk"; ai.T = 0; }
            wardenView.Release();
            Go(Stage.Boss);
            Objective([("Cross at the Low Ford", false, false), ("Put out the lamps", false, true)]);
        }
    }

    /* ----------------------------------------------------------- victory -- */

    void OnWardenDown(Enemy e)
    {
        if (B == null) return;
        PaceNotes.Enqueue($"ford down t={B.Time:0.0} fought={stageT:0.0} hp={e.Hp:0}/{e.MaxHp:0} floor={e.HpFloor:0} taken={e.TakenMul:0.00} over={e.Overflow:0} school={e.LastSchool} weapon={e.LastWeapon ?? "-"} blow={e.LastBlow:0.00} lit={LitCount} broken={lampsBroken} state={e.State}");
        ai.Mode = "dead";
        wardenView.SetPose("dead");
        wardenPos = (e.X, e.Z, Math.PI / 2 - e.Facing);
        Bar(null);
        B.Events.Emit(new Ev.Shake { Amount = 0.9 });
        G.Announce(new Announcement("The Ford-Warden falls", null, "boon", 2.2, Through: true));
        for (int i = 0; i < pylons.Count; i++) if (litPylons[i]) { litPylons[i] = false; G.Look.SetLit(pylons[i].Light, false); }
        ClearAround(e.X, e.Z, 40);
        // What it leaves: by the film, all at once; in play, staged (Legendary, RunVictory).
        legendFrom = (e.Level, e.Def.Family, e.X, e.Z);
        vicT = 0; legendAt = -1; legendName = null;
        Go(Stage.Victory);
        cutT = 0;
        Objective([("Cross at the Low Ford", true, false)]);
        // C03 (docs/cinematics/shoot/c03.md), where he fell: he kneels where he
        // is, facing south, and she is put 4 m before him on the cut after the
        // blow. What it sets is set at the hand-back, so a skip sets it too.
        var marks = new Dictionary<string, double[]> { ["w"] = [e.X, e.Z, 0], ["her"] = [e.X, e.Z + 4, Math.PI] };
        if (G.Cinematic("c03", HeartGone, marks)) { victoryByCine = true; wardenInCine = true; }
        if (victoryByCine) { WardenSpoils(); Legendary(false); }
        else G.HoldBanners(LegendNarrate + 0.6);
    }

    /// <summary>The Warden's plain spoils (its lamp-iron, the shards, the coin), on the corpse's east side: the west is the
    /// Legendary's own ground (M5 r2).</summary>
    void WardenSpoils()
    {
        if (B == null) return;
        var (_, _, x, z) = legendFrom;
        B.SpawnPickup(PickupKind.Item, x + 1.5, z + 1, 1, "wardens_lampiron");
        B.SpawnPickup(PickupKind.Item, x + 0.6, z + 1.9, 3, "ember_shard");
        for (int i = 0; i < 12; i++) B.SpawnPickup(PickupKind.Gold, x + 0.6 + B.Rng.Next() * 3, z - 0.8 + B.Rng.Next() * 3.2, 4);
    }

    // (M5 r2, the first Legendary's moment, judge frame 56: ten texts piled in the centre.) In order: the dying line; the
    // Legendary's beam and label alone (LegendAt); its banner (LegendBanner, the Rest/Light prompt hushed under it); the
    // narration and the rest of the spoils (LegendNarrate). Banners asked for meanwhile (a level-up) wait (HoldBanners).
    const double LegendAt = 1.6, LegendBanner = 3.7, LegendNarrate = 7.2, LegendBannerSecs = 3.2;
    (int Level, Family Family, double X, double Z) legendFrom;
    double vicT, legendAt = -1;
    string? legendName;

    void StageLegendary(double dt)
    {
        vicT += dt;
        if (vicT >= LegendAt && legendAt < 0) { legendAt = vicT; legendName = Legendary(true); }
        if (vicT >= LegendBanner && shown.Add("legend.banner") && legendName != null)
        {
            // PLACEHOLDER copy for the story lead (Drops.NamedFalls over the item's name, its rarity under it).
            G.HushPrompts(LegendBannerSecs + 0.2);
            G.Announce(new Announcement(legendName, "Legendary", "reward", LegendBannerSecs, Drops.NamedFalls, Through: true));
        }
        if (vicT >= LegendNarrate && shown.Add("legend.spoils")) WardenSpoils();
    }

    /// <summary>The Warden's drop roll at its corpse (WardenLegendary); hush: its Legendary's line is said by the staging.</summary>
    string? Legendary(bool hush)
    {
        var (lv, fam, x, z) = legendFrom;
        return WardenLegendary(lv, fam, x, z, hush);
    }

    /// <summary>ARPG 7.1: the first time she kills the Ford-Warden he leaves one Legendary for certain (a world fact);
    /// later kills roll the plain Boss source.</summary>
    public void WardenLegendary(Enemy e) => WardenLegendary(e.Level, e.Def.Family, e.X, e.Z, false);

    /// <summary>(M5 r2) The roll at (x, z): a Legendary 2.8 m west of the corpse on its own ground, the rest on the east
    /// side with the plain spoils. Its Legendary's name (null: none fell); hush: the HUD's line is left to the caller.</summary>
    public string? WardenLegendary(int level, Family family, double x, double z, bool hush)
    {
        if (B == null) return null;
        bool first = !W.Fact(WardenLegendaryFact).Truthy;
        var loot = G.Journey.Drops(new DropCtx
        {
            Source = DropSource.Boss, Level = level, People = Drops.PeopleOf(family), Floor = first ? (int)LootTier.Legendary : 0,
            Luck = B.Stats.Get(Stat.Luck), R = B.Rng.Next, Hush = hush,
        });
        if (first) W.Facts[WardenLegendaryFact] = true;
        string? name = null;
        int west = 0;
        foreach (var l in loot)
        {
            bool legend = l.Tier is int t && (LootTier)t is LootTier.Legendary or LootTier.Storied;
            double a, d;
            if (legend) { a = Math.PI + west++ * 0.5; d = 2.8; name ??= (l.Payload as ItemInstance)?.Name ?? Items.Find(l.Ref ?? "")?.Name ?? "A Legendary"; }
            else { a = (B.Rng.Next() - 0.5) * 1.6; d = 1.5 + B.Rng.Next() * 1.5; }
            B.Spill(l with { Persistent = true }, x + Math.Cos(a) * d, z + Math.Sin(a) * d);
        }
        return name;
    }

    public const string WardenLegendaryFact = "lowford.warden_legendary";

    bool victoryByCine;

    /// <summary>C03's events: Grimtunnel coming up under her hand, and going down with the heart.</summary>
    void GrimUp()
    {
        if (B == null) return;
        grim = B.Enemies.Living().FirstOrDefault(x => x.Tag == "grim");
        if (grim == null) return;
        grim.State = EnemyState.Surfacing; grim.StateT = 0.55;
        grimByCine = true;
        grim.Facing = Math.Atan2(B.Player.Z - grim.Z, B.Player.X - grim.X);
        B.Events.Emit(new Ev.Spawn { Enemy = grim.Id, X = grim.X, Z = grim.Z, Def = "grimtunnel", Style = SpawnStyle.Burrow });
    }

    bool grimByCine;

    /// <summary>Gone down the hole: nothing of him left above the mud.</summary>
    void GrimGone()
    {
        GrimDown();
        if (grim != null) { if (grim.Alive) B?.Enemies.Release(grim); grim = null; }
    }

    void GrimDown()
    {
        if (B == null || (grim ??= B.Enemies.Living().FirstOrDefault(x => x.Tag == "grim")) is not { Alive: true } g) return;
        g.State = EnemyState.Burrowed;
        B.Events.Emit(new Ev.Spawn { Enemy = g.Id, X = g.X, Z = g.Z, Def = "grimtunnel", Style = SpawnStyle.Burrow });
        B.Events.Emit(new Ev.Shake { Amount = 0.4 });
    }

    /// <summary>C03 handed back (or skipped): the heart is gone, and the dawn is coming.</summary>
    void HeartGone()
    {
        wardenInCine = false;
        GrimGone();
        shown.Add("grimGone");
        // C03 runs on into C04 A on the cut (the owner, 17 October: no three seconds
        // of wading between two cinematics): the crossing is in the cut, and play
        // comes back on the road once the ember has gone into the ground.
        bool onward = G.CanCinematic("c04a");
        Taken(toast: !onward);
        // The cinematic began the dawn (a fifth of the way); the road holds there until C04 finishes it.
        dawnK = 0.287;
        Dawnbreak(said: !onward);
        if (onward) FirstLight(false, onward: true);
    }

    void RunVictory(double dt)
    {
        if (B == null || victoryByCine) return;
        StageLegendary(dt);
        cutT += dt;
        // (the narration waits for the Legendary's beat: the dying line stays at 0.3)
        if (vicT < LegendNarrate) cutT = Math.Min(cutT, 1.5);
        double cx = wardenPos.X, cz = wardenPos.Z;
        // C03 (cin_heart_goes_down): a tired man's voice, the Order's question at the end of a watch.
        if (cutT > 0.3 && shown.Add("morning")) B.Events.Emit(new Ev.Bark { X = cx, Z = cz, Text = "Is it morning?", Speaker = "The Ford-Warden" });
        double cy = Math.Max(G.Look.HeightAt(cx, cz), waterY);
        if (cutT > 1.6 && !coreShown)
        {
            coreShown = true;
            core.Visible = true;
            corePos = (cx, cz); coreY = cy + 0.8;
            core.Light = 18;
            G.Say("Where the Warden fell, its heart is still burning: a stone the size of a fist, full of cold light.", null, 5);
            G.Showcase((cx + 6, cy + 6, cz + 11), (cx, cy + 1, cz));
            G.Capture(true);
        }
        if (core.Visible)
        {
            coreSpin += dt * 1.4;
            double pulse = 1 + Math.Sin(cutT * 5) * 0.08;
            if (grim == null) coreY = Math.Min(cy + 1.6, coreY + dt * 0.3);
            core.Place(corePos.X, coreY, corePos.Z, coreSpin, pulse);
            core.Light = 16 + Math.Sin(cutT * 7) * 3;
        }
        if (cutT > 4.2 && grim == null && !shown.Contains("grimGone"))
        {
            B.Events.Emit(new Ev.Shake { Amount = 0.7 });
            grim = B.SpawnEnemy("grimtunnel", cx + 2.2, cz + 1.2, new Battle.SpawnOpts { Style = SpawnStyle.Burrow, Disposition = Disposition.Neutral, Tag = "grim" });
            if (grim != null) { grim.State = EnemyState.Surfacing; grim.StateT = 0.55; }
            B.Events.Emit(new Ev.Spawn { Enemy = grim?.Id ?? -1, X = cx + 2.2, Z = cz + 1.2, Def = "grimtunnel", Style = SpawnStyle.Burrow });
        }
        if (grim is { Alive: true })
        {
            grim.Facing = Math.Atan2(cz - grim.Z, cx - grim.X);
            if (grim.State == EnemyState.Surfacing) { grim.StateT -= dt; if (grim.StateT <= 0) grim.State = EnemyState.Active; }
        }
        if (cutT > 5.4 && shown.Add("grim1")) B.Events.Emit(new Ev.Bark { X = cx + 2.2, Z = cz + 1.2, Text = "Ooh, still lit! Nobody's, is it? Nobody's!", Speaker = "Grimtunnel" });
        if (cutT > 6.9 && shown.Add("grim1b")) B.Events.Emit(new Ev.Bark { X = cx + 2.2, Z = cz + 1.2, Text = "...You smell like downstairs.", Speaker = "Grimtunnel" });
        if (cutT > 8.4 && shown.Add("grim2")) B.Events.Emit(new Ev.Bark { X = cx + 2.2, Z = cz + 1.2, Text = "Finders keepers, surface-m— (a sniff) ...Downstairs'll be ever so grateful.", Speaker = "Grimtunnel" });
        if (core.Visible && grim != null && cutT > 9.6)
        {
            double k = Math.Min(1, dt * 4);
            corePos = (corePos.X + (grim.X - corePos.X) * k, corePos.Z + (grim.Z - corePos.Z) * k);
            coreY += (cy + 1.2 - coreY) * k;
        }
        if (cutT > 11 && grim is { Alive: true } && grim.State != EnemyState.Burrowed)
        {
            grim.State = EnemyState.Burrowed;
            B.Events.Emit(new Ev.Spawn { Enemy = grim.Id, X = grim.X, Z = grim.Z, Def = "grimtunnel", Style = SpawnStyle.Burrow });
            B.Events.Emit(new Ev.Shake { Amount = 0.4 });
            core.Visible = false;
            core.Light = 0;
        }
        if (cutT > 12 && grim != null)
        {
            if (grim.Alive) B.Enemies.Release(grim);
            grim = null;
            shown.Add("grimGone");
            Taken();
        }
        if (cutT > 13)
        {
            G.Showcase(null);
            G.Capture(false);
            dawnK = 0;
            Dawnbreak();
        }
    }

    /// <summary>What the night's end leaves: the Warden's heart is Grimtunnel's, and you know it.</summary>
    void Taken(bool toast = true)
    {
        G.Apply("""
            [
              { "learn": "grimtunnel", "text": "You have seen Grimtunnel. The lamplings are digging for something." },
              { "history": { "id": "ford_warden_slain", "text": "put down the Ford-Warden at the Low Ford", "tags": ["deed", "undead"], "spread": 2, "sentiment": { "respect": 10 } } },
              { "history": { "id": "core_stolen", "text": "let a lampling steal the Warden's heart", "tags": ["lampling"], "spread": 1 } },
              { "give": "grimtunnels_lamp" }
            ]
            """);
        if (toast) TakenToast();
    }

    void TakenToast() =>
        G.Toast(new Toast(ToastKind.Lore, "Grimtunnel took the Warden's heart", "They went down, not away. In the churned mud where he went: a lamp on a snapped strap, still warm. His.", Life: 8));

    /// <summary>The gate opens and the night is over: the walk to the Waystation.</summary>
    void Dawnbreak(bool said = true)
    {
        if (B == null) return;
        Go(Stage.Dawn);
        // The Waystation, where the road goes from here, built ahead while C04 A plays and she walks out.
        G.Prepare("waystation");
        B.Collision.RemoveTagged("gate");
        // Chid, who has watched the ford all night (TWIST_OPTIONS A); the narrator says it as plainly as the rest.
        // When C04 A follows on the cut, it says the reeds as she climbs out, and shows the gate.
        if (said)
        {
            W.Facts["prologue.reeds_said"] = true;
            G.Say("In the reeds on the far bank, someone is standing very still.", null, 4);
            G.After(4.4, () => G.Say("Gray light, then gold. Up the road, the Waystation's gate is opening.", null, 6));
        }
        W.Time = TimeOfDay.Dawn;
        StartDay();
        DayObjective();
    }

    /// <summary>The dawn puts the ember out: the cards, the blessing, all it
    /// built. What the survivor carries, and what they learned, stay.</summary>
    /// <summary>C04 A: the ember goes out in it (its "douse" event), the narrator says it, and the dawn's card follows its hand-back.</summary>
    void FirstLight(bool south, bool onward = false)
    {
        doused = true;
        W.Facts["prologue.dawn_south"] = south;
        if (!G.Cinematic("c04a", () =>
            {
                dawnK = 1; G.SetAtmosphere(Atmospheres.LowFordDawn); G.Look.SetNight(false); if (!dousedByCine) Douse(false);
                DayObjective();
                // As the film hands back: the dawn's card, the world held under it (N24).
                DawnCardUp();
                // On from C03, she never waded back for what he left: it is hers on the road.
                if (onward && B != null) { B.Gather(B.Player.X, B.Player.Z); G.After(1.0, TakenToast); }
            }))
        {
            Douse();
            if (onward) TakenToast();
            return;
        }
    }

    bool dousedByCine;

    public override void CineEvent(string name)
    {
        switch (name)
        {
            // The cinematic's Warden is on: ours hides until it hands him back.
            case "warden_cine": wardenInCine = true; break;
            case "warden_up": WardenUp(); break;
            case "grim_up": GrimUp(); break;
            case "grim_down": GrimDown(); break;
            case "grim_gone": GrimGone(); break;
            case "douse": dousedByCine = true; Douse(false); break;
            // The ford after the night: nothing of the Warden left in it (already so in play).
            case "ford_clear": wardenView.Hide(); wardenGone = true; core.Visible = false; break;
        }
    }

    /// <summary>The ember goes out: what it built is taken (Journey.Douse), the night's lessons paid. Out of a
    /// film (`card`), the dawn's card follows a breath later; in C04 A it waits for the film's hand-back.</summary>
    void Douse(bool card = true)
    {
        if (B == null) return;
        // (M5: the draft off, the night lent nothing: nothing is stripped or paid, and no card says so; the day's tip follows)
        if (!Draft)
        {
            dawnTaught = 0;
            if (card) G.After(1.2, DawnCardClosed);
            return;
        }
        var p = B.Player;
        B.Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = 3.4, School = School.Fire, Duration = 1.4 });
        B.Events.Emit(new Ev.Shake { Amount = 0.25 });
        // What the night gave, by name, read before the dawn takes it.
        var skills = DawnCard.NightSkills(B, Character.Kit(G.Journey.Ch).Weapons.Select(w => w.Id));
        int taught = G.Journey.Douse(B);
        dawnTaught = taught;
        dawnCard = DawnCard.Build(skills, taught > 0 ? G.Journey.Ch.Level : null);
        if (card) G.After(1.2, DawnCardUp);
    }

    DawnCard? dawnCard;
    int dawnTaught;
    bool dawnCardShown;

    /// <summary>The dawn's card (N24, in place of the narrator's caption and "The ember goes out" banner): what
    /// the ember takes and what she keeps, held until a click. Once it closes, the level the night taught, its
    /// traits, and the day's tip follow in their order (game time: a freeze holds them).</summary>
    void DawnCardUp()
    {
        if (dawnCard == null || dawnCardShown) return;
        dawnCardShown = true;
        G.DawnCard(dawnCard, DawnCardClosed);
    }

    void DawnCardClosed()
    {
        int taught = dawnTaught;
        // What the night taught her, paid now the ember has gone: the first character level, on
        // its own, where it can be understood.
        if (taught > 0)
            G.After(4.6, () =>
            {
                var ch = G.Journey.Ch;
                levelAnn = new Announcement($"Level {ch.Level}", ch.TraitPicks > 1 ? $"{Count(ch.TraitPicks)} new traits to choose ({Key("character")})" : ch.TraitPicks == 1 ? $"A new trait to choose ({Key("character")})" : $"Attribute points to spend ({Key("character")})", "boon", 4.5, "What the night taught you");
                levelsTaught = taught; traitsDue = ch.TraitPicks;
                G.Announce(levelAnn);
                G.Journey.Grew();
            });
        // F12 just after, and the day's tip after that.
        if (taught > 0) G.After(5.2, () => levelDue = true);
        // (M5 r3: in the dawn's breather before the boars, once the level's callout is answered; it came 2.5 s before
        // Red Tolly's wake at 18.5 s; ChampionGate holds it off any champion's wake)
        G.After(taught > 0 ? 5.6 : 1.0, () => DayTip(taught > 0, 0));
    }

    void DayTip(bool afterLevel, int tries)
    {
        if (afterLevel && !G.Taught("level") && tries < 40) { G.After(0.5, () => DayTip(afterLevel, tries + 1)); return; }
        PacedTip("day", "By day", $"By day the ember sleeps: you fight with what you carry, your art and your feet, and every fight teaches you ({Key("character")}). The ember is for the night.", [Key("character")], 14);
    }

    void Finish()
    {
        G.Apply("""[{ "set": { "prologue.done": true } }, { "quest": { "id": "prologue", "status": "resolved", "outcome": "resolved" } }]""");
        G.SetHint(null);
        G.SetObjectives(new());
        G.Travel("waystation", "The Waystation", "Where the three roads meet");
    }

    void OnKill(Enemy e, bool byPlayer)
    {
        // Pooled creatures are reused: forget them the moment they die.
        if (e.Tag == "warden") { OnWardenDown(e); warden = null; }
        if (e.Tag == "caller") { caller = null; G.Toast(new Toast(ToastKind.World, "The Grave-Caller is still", "The graves have stopped listening.")); }
        if (e.Tag == "knight" && B != null)
        {
            knight = null;
            B.SpawnPickup(PickupKind.Item, e.X, e.Z, 2, "ember_shard");
            B.SpawnPickup(PickupKind.Item, e.X + 1, e.Z - 0.5, 1, "bone_amulet");
            for (int i = 0; i < 6; i++) B.SpawnPickup(PickupKind.Gold, e.X + (G.Rng.NextDouble() - 0.5) * 3, e.Z + (G.Rng.NextDouble() - 0.5) * 3, 3);
        }
    }

    /* ------------------------------------------------------------ runtime -- */

    public override Arrival ArrivalFrom(string? from)
    {
        cameFrom = from;
        var gate = L("gate"); var camp = L("camp");
        // Back down the road from the Waystation: arrive at the north end, by the gate.
        return from == "waystation" ? new(gate.X + 0.5, ExitZ + 9, 0) : new(camp.X + 1.5, camp.Z - 1.5, Math.PI);
    }

    public override TimeOfDay TimeOf(WorldState w) => Now is Stage.Dawn or Stage.Exit ? TimeOfDay.Dawn : TimeOfDay.Night;
    public override AtmospherePreset AtmosphereFor(TimeOfDay t) => t == TimeOfDay.Dawn ? Atmospheres.Morning(morningK) : Atmospheres.LowFordNight;

    /// <summary>The day stretch's sun climbs (H4 item 10): from the dawn C04 A hands back into, MorningFrom s into the
    /// road (the hand-back's frame and its ease untouched) and over MorningOver s, to LowFordMorning (Atmospheres), so
    /// the wallow, the camp and the gate are in morning sun, not the low dawn's long shade. Eased (smoothstep: at
    /// most 0.17% of the way a tenth of a second), set each 0.2% of the way, the grade unchanged (the dawn's).</summary>
    void MorningClimbs()
    {
        double k = Math.Clamp((stageT - MorningFrom) / MorningOver, 0, 1);
        k = k * k * (3 - 2 * k);
        if (k <= morningK || k - morningK < 0.002 && k < 1) return;
        morningK = k;
        G.SetAtmosphere(Atmospheres.Morning(k), false);
    }

    const double MorningFrom = 5, MorningOver = 100;
    double morningK;

    public override void Begin(Battle b)
    {
        base.Begin(b);
        LampRise.ShowLamps(G, Id);
        // (the ford's risen come close and many: each its own pace and weave, not a file of clones, NPC 17)
        b.VaryPacks = true;
        // (and they steer round the camp: the fire and its ring of logs, not walked through or stood on, judge r2)
        var fireAt = L("fire");
        b.Avoid.Add((fireAt.X, fireAt.Z, 2.4));
        wardenView = G.Look.BossView("ford_warden");
        wardenView.SetPose("sleep");
        core = G.Look.Orb("#bfe6ff", 0.42);
        core.Visible = false;
        // The dead watchman at the post, where he fell: the fall played out and held.
        var man = L("watchman");
        watchman = G.Look.Fallen(Lore.PackageFolk ? new PersonSpec { Sex = Sex.Male, Body = "npc:" + (Lore.FolkPackages!.GetValueOrDefault("watch") ?? "npc_watch_m") } : new PersonSpec
        {
            Sex = Sex.Male, Outfit = Lore.OutfitFor(Sex.Male, "ranger", true, true), Beard = true, HairColor = "#4a3a2a", Skin = "#c8b0a0",
            Dye = new Dye { Cloth = "#4a5064" },
        }, new Held { Forearm = "shield_round" }, man.X, man.Z, 2.2, "Death_A");
        if (Draft) G.SetDraftTip(DraftTip);
        startWeapons = b.Weapons.Count;
        // (no great blessing offers to grow a Flare she hasn't met: F8 teaches it, au1 item 3)
        b.FlareGreatsHeld = !G.Taught("art");
        if (DayStart && !F("prologue.done").Truthy) { BeginDay(b); return; }
        if (F("prologue.done").Truthy)
        {
            // Loaded after the prologue: the road at dawn, the dead at rest.
            Now = Stage.Exit; stageT = 0; dawnK = 1; doused = true;
            // (the morning's sun, climbed: the road by day after the prologue, MorningClimbs)
            morningK = 1;
            G.SetAtmosphere(Atmospheres.Morning(1));
            // (the host set the night from the time before the stage was known: the post's own torch burned on at dawn, E7b r3)
            G.Look.SetNight(false);
            b.Collision.RemoveTagged("gate");
            foreach (var p in pylons) G.Look.SetLit(p.Light, false);
            ai.Mode = "dead"; wardenGone = true;
            wardenView.Hide();
            // The road by day, as today has it (ZoneReset: its packs back each day, the lamp lit for good).
            StartDay();
            DayObjective();
            return;
        }
        G.SetAtmosphere(Atmospheres.LowFordNight);
        // (M5) The night's placed beats, resting on the road from nightfall. With the draft off the ember lends no cards:
        // she fights the night as the day, under the night's rules, the Flare at half as a story fight starts it.
        if (!Draft)
        {
            b.Night = true;
            if (b.Flare != null) b.FlareMeter = Math.Max(b.FlareMeter, Battle.FlareFull / 2);
        }
        StartNight(b);
        // C01, the opening (docs/cinematics/shoot/c01.md), once a journey: it
        // wakes her by the fire and hands back as the dead come up. Where no
        // cinematic can play (the tests, a quick start), its lines are captions.
        bool woke = F("prologue.woke").Truthy;
        W.Facts["prologue.woke"] = true;
        if (!woke && G.Cinematic("c01", Woken)) return;
        Woken();
        if (woke) return;
        G.Say("Your bedroll has not been slept in.", null, 3);
        G.After(3.2, () => G.Say("Prints in the frost, your own. They come up from the river. None go down to it.", null, 5));
        G.After(8.4, () => G.Say("Far up the road one lamp burns high in the dark, and a voice comes down to you over the frost, close as if she stood at your shoulder.", null, 5.5));
        // Vonnra, unnamed: the fortune opens on the same words (docs/STORY_BIBLE.md, "Who tells it").
        G.After(14.1, () => G.Say("Come up, traveler. ...No charge, this once.", "A voice up the road", 4));
        G.After(18.3, () => G.Say("Past the firelight, the frost is breaking.", null, 3.5));
    }

    /// <summary>Awake by the fire, the dead coming up: the night begins.</summary>
    void Woken()
    {
        Objective([("Survive the night", false, false)]);
        G.AnnounceZone();
    }

    public override void Step(double dt) => Director(dt);

    public override void Frame(double dt)
    {
        // (a freeze holds the director too: the road's next words keep their distance from it, seen here)
        if (B != null && G.Teaching != null) wordsFree = Math.Max(wordsFree, B.Time + WordsAfterCallout);
        // C03's Grimtunnel comes up while the zone's director waits: his surfacing is kept here.
        if (grimByCine && grim is { Alive: true, State: EnemyState.Surfacing } gs) { gs.StateT -= dt; if (gs.StateT <= 0) gs.State = EnemyState.Active; }
        if (wardenGone) return;
        if (wardenInCine) { wardenView.Hide(); return; }
        if (warden is { Alive: true } && warden.State != EnemyState.Dying) wardenPos = (warden.X, warden.Z, Math.PI / 2 - warden.Facing);
        double wy = Math.Max(G.Look.HeightAt(wardenPos.X, wardenPos.Z), waterY - 0.25);
        // Asleep he lies half under the ford's water, not on top of it (Env 22's triage: he lay ON the water).
        if (ai.Mode == "sleep") wy -= SleepSink;
        wardenView.Glow = Math.Clamp(0.3 + LitCount * 0.25, 0, 1);
        wardenView.Update(warden is { Alive: true } ? warden : null, wardenPos.X, wy, wardenPos.Z, wardenPos.Facing, dt);
        if (ai.Mode == "dead")
        {
            if (deadT < 0) deadT = 0;
            deadT += dt;
            if (deadT > 9) { wardenView.Hide(); wardenGone = true; }
        }
    }

    public override bool OnDeath(string killer)
    {
        // The ember is not done with you (ARPG 7.2): up again at the last lamp-post she lit here, else where she was last
        // safe (the stage's checkpoint, before the first post). What she killed stays dead; champions and the Warden heal.
        if (B == null) return true;
        var battle = B;
        int toll = LampRise.CountRise(W);
        string line = day == null && nightRises++ == 0 ? "The ember will not let you go so easily." : LampRise.Line(toll);
        G.After(2.6, () =>
        {
            G.Say(line, null, 3.5);
            var at = LampRise.RiseAt(W, Id, battle, (checkpoint.X, checkpoint.Z));
            LampRise.Stand(G, battle, at.X, at.Z);
            if (warden is { Alive: true } && Now == Stage.Boss)
            {
                warden.Hp = warden.MaxHp;
                warden.X = wardenHome.X; warden.Z = wardenHome.Z;
                ai.Mode = "walk";
                if (bar != null) Bar(bar with { Channel = null });
            }
        });
        return true;
    }

    public override List<MapMark> MapMarks()
    {
        XZ at(string k) => L(k);
        return
        [
            new(at("camp").X, at("camp").Z, "Your camp", MarkKind.Place), new(at("cart").X, at("cart").Z, "Broken cart", MarkKind.Place),
            new(at("post").X, at("post").Z, "Watch-post", MarkKind.Place), new(at("barrow").X, at("barrow").Z, "The Barrow", MarkKind.Place),
            new(at("ford").X, at("ford").Z, "The Low Ford", wardenGone ? MarkKind.Place : MarkKind.Danger),
            new(at("gate").X, at("gate").Z + 4, "North, to the Waystation", MarkKind.Exit),
        ];
    }

    public override AmbienceMix Ambience(double x, double z)
    {
        bool dawn = Now is Stage.Dawn or Stage.Exit;
        return new AmbienceMix
        {
            Wind = 0.55, Leaves = 0.35, Fire = Warmth(x, z), Water = Math.Clamp(1 - Math.Abs(z - RiverZ(x)) / 26, 0, 1),
            Crickets = dawn ? 0.15 : 0.75, Owl = dawn ? 0 : 0.6, Birds = dawn ? 0.7 : 0,
        };
    }

    public override Dictionary<string, object?> Debug() => new()
    {
        ["infire"] = B == null ? 0 : B.Enemies.Living().Count(e => Dist(e.X, e.Z, L("fire").X, L("fire").Z) < 1.2),
        ["stage"] = Now.ToString(), ["stageT"] = stageT, ["chestOpened"] = chestOpened, ["lit"] = LitCount, ["wardenHp"] = warden?.Hp,
        ["wardenMode"] = ai.Mode, ["day"] = day == null ? null : string.Join(",", day.S.In("day", day.Features).Select(bt => $"{bt.Id}:{(day.Done(bt.Id) || bt.Kind == "post" && LampBook.PostLit(W, bt.Post!) ? "done" : day.WokeAt.ContainsKey(bt.Id) ? "on" : "-")}")), ["checkpoint"] = $"{checkpoint.X:0.0},{checkpoint.Z:0.0}",
        ["night"] = night == null || B == null ? null : $"sprung={sprungAt:0.0} wq={wagonQueued} ws={wagonSaid} wd={wagonDoneAt:0.0} th={tallyHeldAt:0.0} fight={night.Fighting} saying={G.Saying} teach={G.Teaching?.Id} words={words.Count} wf={wordsFree:0.0} | "
            + string.Join(" ", night.Packs.Select(kv => $"{kv.Key}:{(night.DownAt.ContainsKey(kv.Key) ? "down" : night.WokeAt.ContainsKey(kv.Key) ? "on" : "-")}[" + string.Join(",", night.Standing(kv.Key).Select(e => $"{e.Def.Id}@{e.X:0},{e.Z:0}/{e.State}")) + "]")),
    };

    public override void Dispose()
    {
        base.Dispose();
        watchman?.Dispose();
        wardenView?.Dispose();
        core?.Dispose();
        G.SetHint(null);
        G.SetBoss(null);
    }
}
