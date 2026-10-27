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
public sealed class Prologue : ZoneRuntime
{
    public enum Stage { Wake, Rising, Road, Ambush, Road2, Post, Barrow, ToFord, Intro, Boss, Victory, Dawn, Exit }

    public override string Id => "lowford";
    public override string Name => "The Low Ford Road";
    public override string? Region => "Thornhollow, south";
    public override bool Combat => true;
    /// <summary>The night's: the ember burns until the dawn puts it out.</summary>
    public override bool Ember => !F("prologue.done").Truthy;
    public override IReadOnlyList<string> Creatures { get; } = ["risen", "risen_warrior", "risen_archer", "barrow_knight", "grave_caller", "grimtunnel", "ford_warden"];

    sealed class WardenAI
    {
        public string Mode = "sleep";
        public double T, CleaveCd = 3, ChargeCd = 6, ChannelCd = 30, DirX, DirZ = 1, Travelled, ChannelHp, RaiseT, ContactT, HitX, HitZ;
        public List<double> Thresholds = [0.7, 0.4];
    }

    static readonly double[] Ward = [1, 0.7, 0.55, 0.4];
    const string Draft = "Each time the ember rises, choose one: a combat skill (they fire on their own) or a passive skill. A combat skill at rank 8, with one rank of the passive it names, evolves.";

    public Stage Now { get; private set; } = Stage.Wake;
    double stageT, spawnT = 2, cutT, dawnK, envT, deadT = -1;
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
    bool knightPlanted, knightRan;
    readonly List<(double X, double Z, int Light, string Flame)> pylons = new();
    readonly double[] lampY;
    readonly bool[] litPylons;
    readonly double[] pylonHp;
    Enemy? warden, caller, knight, grim;
    bool wardenGone, chestOpened, finished, coreShown, doused;
    /// <summary>A cinematic is playing the Warden with its own body (C02, C03): ours waits, hidden.</summary>
    bool wardenInCine;
    readonly XZ wardenHome;
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
        wardenPos = (wardenHome.X, wardenHome.Z, 0);
        Hooks = new BattleHooks
        {
            BossTick = (e, dt) => e.Tag == "warden" && WardenTick(e, dt),
            OnKill = OnKill,
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
                G.After(0.6, () => Tip("pack", "Your pack", $"What you find, you keep.{NL}The ember won't outlast the night; gear, gold and what you learn will.{NL}Press {{key:{Key("inventory")}}} to open your *pack* and wear the jerkin.", null, 11));
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
    }

    /* ------------------------------------------------------------- helpers -- */

    void Objective((string Text, bool Done, bool Optional)[] steps) =>
        G.SetObjectives([new Tracked("pro", "The Low Ford", TrackTone.Tutorial, steps.Select(s => new Step(s.Text, s.Optional, s.Done)).ToList())]);

    void Tip(string id, string title, string text, List<string>? keys = null, double life = 9)
    {
        if (!shown.Add(id)) return;
        G.SetHint(new Hint(id, title, text, keys ?? new()));
        if (life > 0) G.After(life, () => { if (G.CurrentHint?.Id == id) G.SetHint(null); });
    }

    string Key(string action) => G.KeyLabel(action);

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

    void Teach(string id, CalloutKind kind, string title, string line, Aim aim, string? answer = null, string? after = null, double gap = Teacher.Gap, bool overHint = false) =>
        G.Teach(new Callout(id, kind, title, line, aim, answer) { After = after, Gap = gap, OverHint = overHint });

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
        if (knight is { Alive: true, State: not EnemyState.Windup } kw && !G.Taught("red_line")
            && G.Teaching != null)
            kw.RangedT = Math.Max(kw.RangedT, 0.25);
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

    /// <summary>The Barrow Knight's lane while it is marked (its windup), a beat after it was: points along
    /// it, those clear of her first (the ring marks the lane, never her figure), the lane's middle first.</summary>
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
            .Select(q => Up(q.X, q.Z, 0.1)).ToList();
    }

    void Callouts()
    {
        if (B == null) return;
        var p = B.Player;
        KnightWatch();
        if (B.FlareGreatsHeld && (G.Taught("art") || Now >= Stage.ToFord)) B.FlareGreatsHeld = false;
        // F1: the first ember on the ground (one well inside the screen: it waits for one).
        if (Now == Stage.Rising && B.EmbersLying > 0)
            Teach("ember_ground", CalloutKind.Freeze, "Ember", "The light the dead carry. Come close and it comes to you.", new Aim { World = NearEmbers, Safe = true });
        // F2: straight after F1 (before the first rise), else the first ember gathered.
        if (B.EmberXp > 0 || B.EmberLevel > 1 || G.Taught("ember_ground"))
            Teach("ember_bar", CalloutKind.Arrow, "Rising", "Ember fills this. When it's full, the ember rises.", Aim.At("chain"), after: "ember_ground", gap: 0.6, overHint: true);
        // (and the journal remembers what the valley believes, once an ember is gathered)
        if (B.EmberXp > 0 || B.EmberLevel > 1)
        {
            if (shown.Add("lore.ember"))
                G.Apply("""[{ "learn": "lore.ember", "text": "Ember: light that seeps up from under the valley. After dark the dead get up full of it, and it spills when they fall. At first light, what's in them sinks back into the ground." }]""");
        }
        // F4: the first skill draft, the ember's first rise (on the panel, at the first combat-skill card).
        if (B.EmberLevel >= 2 && B.DraftOwed && B.GreatOwed == 0)
            Teach("first_draft", CalloutKind.Panel, "A skill", "The ember lends you skills as it rises. Choose one.", Aim.At("cards"));
        // F5: the first combat skill on the console.
        if (startWeapons >= 0 && B.Weapons.Count > startWeapons)
        {
            var w = B.Weapons[startWeapons];
            Teach("first_skill", CalloutKind.Arrow, w.Def.Name, "It fires on its own, like your weapon. First light takes it back.", Aim.At("socket:" + w.Id), after: "first_draft");
        }
        // F6: after the blessing, six risen at her (or 58 s in), else on the road (au1 item 2: it was the sixth
        // lesson in 12 s).
        if (Now is Stage.Rising or Stage.Road or Stage.Ambush or Stage.Road2 && (Now != Stage.Rising || G.Taught("great_blessing") && (stageT > 58 || Crowd(p.X, p.Z, 3) >= 6)))
            Teach("dash", CalloutKind.Freeze, "Dash", $"{Key("dash")}: a roll nothing can touch. Two charges; they come back.", Aim.At("dash"), "dash");
        // F6b: her calling's art rides the dash (Forms.cs); in the Ambush, lit, with the dead close round her.
        // The Warden's channel later asks for it by name (au1 item 4).
        if (Now == Stage.Ambush && stageT > 4 && B.FormReady && Crowd(p.X, p.Z, 6) >= 4 && B.Ability is AbilityKind fk && FormWords(fk) is string fw)
            Teach("form", CalloutKind.Freeze, Abilities.All[fk].Name, $"When your dash is aflame, it's {fw}", Aim.At("dash"), "dash", after: "dash");
        // F7: the Barrow Knight's first red line.
        if (KnightLane().Count > 0)
            Teach("red_line", CalloutKind.Freeze, "Red line", "The Knight is about to strike along this line. Get off it.", new Aim
            {
                World = KnightLane, Safe = true, Open = true,
                Seen = () => knight is { Alive: true } kn ? [Up(kn.X, kn.Z, 0), Up(kn.X, kn.Z, 0.45 * (kn.Def.Scale ?? 1)), Up(kn.X, kn.Z, 0.95 * (kn.Def.Scale ?? 1)), Up(kn.X, kn.Z, 1.4 * (kn.Def.Scale ?? 1))] : [],
            });
        // F8: the Grave-Caller near and what Q casts ready. Q is the art until the Flare lands; once it
        // has (B.Flare), Q is the Flare and its ring shows the meter, so it waits for the meter full and
        // names the Flare (the art then rides the dash).
        if (Now == Stage.Barrow && G.CurrentHint?.Id != "pack" && caller is { Alive: true } gc && Dist(gc.X, gc.Z, p.X, p.Z) < 16 && (B.Flare != null ? B.FlareReady : B.Ability is AbilityKind && p.AbilityCd <= 0))
        {
            var aim = new Aim { Hud = "art", World = () => caller is { Alive: true } c ? [Up(c.X, c.Z, 1.4)] : [] };
            if (B.Flare is { } fl)
                Teach("art", CalloutKind.Freeze, fl.Name, $"{Key("flare")}: your Flare, the ember's great blow.\nIt's full: spend it on the Grave-Caller\nbefore it raises more.", aim, "flare");
            else if (B.Ability is AbilityKind ak)
            {
                var ab = Abilities.All[ak];
                Teach("art", CalloutKind.Freeze, ab.Name, ab.Interrupts
                        ? $"{Key("flare")}: your art. It breaks the Grave-Caller's channel."
                        : $"{Key("flare")}: your art. Kill the Grave-Caller before it raises more.", aim, "flare");
            }
        }
        // F9: the lamps, 3 s after C02 hands back.
        if (Now == Stage.Boss && stageT > 3 && warden is { Alive: true } && LitCount > 0)
            Teach("lamps", CalloutKind.Freeze, "The lamps", "Three lamps guard the Warden. While they burn, he barely feels a blow.\nPut them out: break them, or lure his charge into one.",
                new Aim { World = () => pylons.Select((l, i) => (l, i)).Where(q => litPylons[q.i]).Select(q => (q.l.X, lampY[q.i], q.l.Z)).ToList(), Each = true, Radius = 0.25,
                    Cold = true, WordsNear = (0.24, 0.7), ShunBig = true });
        // F10: her health under 40% for the first time, with a draught to drink.
        if (p.Alive && p.Hp < B.MaxHp * 0.4 && G.Journey.Draughts > 0)
            Teach("draught", CalloutKind.Freeze, "Draught", $"Drink a draught to mend: {Key("draught")}.", new Aim { Hud = "draught", HerSeen = true }, "draught");
        // F12: the first character level, after her dawn line, at its banner (shown again under it).
        if (levelDue && levelAnn != null && !finished)
            G.Teach(new Callout("level", CalloutKind.Freeze, "What the night taught you", LevelLine(), new Aim { Hud = "banner", Banner = levelAnn }) { Mark = "traits" });
        // F13 waits for the Flare on Q (docs/design/CLASSES.md): its meter first full. Not fired yet:
        // Teach("flare", CalloutKind.Freeze, "Flare", $"{Key("flare")}: your Flare. It fills fastest when you're in trouble.", Aim.At("art"), "flare");
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

    /// <summary>Some of the dead, somewhere around the survivor. `ahead` biases north.</summary>
    void SpawnAround(string def, int n, double rMin, double rMax, double ahead = 0, int level = 1)
    {
        if (B == null) return;
        var p = B.Player;
        for (int i = 0; i < n; i++)
            for (int tries = 0; tries < 8; tries++)
            {
                double a = B.Rng.Next() * Math.PI * 2;
                if (ahead > 0 && B.Rng.Next() < ahead) a = -Math.PI / 2 + (B.Rng.Next() - 0.5) * 1.8;
                double d = rMin + B.Rng.Next() * (rMax - rMin);
                double x = p.X + Math.Cos(a) * d, z = p.Z + Math.Sin(a) * d;
                if (!OpenGround(x, z)) continue;
                B.SpawnEnemy(def, x, z, new Battle.SpawnOpts { Style = def is "risen" or "risen_warrior" ? SpawnStyle.Rise : SpawnStyle.Walk, Level = level });
                break;
            }
    }

    int Hostiles() => B?.Enemies.Living().Count(e => e.State != EnemyState.Dying && e.Disposition == Disposition.Hostile) ?? 0;

    void ClearAround(double x, double z, double r)
    {
        if (B == null) return;
        foreach (var e in B.Enemies.Living().ToList())
            if (!e.Boss && e != grim && Dist(e.X, e.Z, x, z) < r) B.KillEnemy(e, false, null);
    }

    /* ---------------------------------------------------- the Ford-Warden -- */

    public int LitCount => litPylons.Count(l => l);

    void Snuff(int i, string how)
    {
        if (!litPylons[i] || B == null) return;
        litPylons[i] = false;
        var p = pylons[i];
        G.Look.SetLit(p.Light, false);
        B.Events.Emit(new Ev.Explosion { X = p.X, Z = p.Z, Radius = 3.2, School = School.Frost, Power = 1.4 });
        B.Events.Emit(new Ev.Shake { Amount = 0.6 });
        B.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z, Text = how == "charge" ? "The lamp shatters!" : "The lamp goes dark" });
        int left = LitCount;
        if (left > 0) G.Toast(new Toast(ToastKind.World, $"A lamp goes out — {left} still burn{(left == 1 ? "s" : "")}"));
        else G.Announce(new Announcement("The lamps are dark", "The Warden is laid bare", "boon", 3.2));
    }

    void Relight()
    {
        int i = Array.IndexOf(litPylons, false);
        if (i < 0) return;
        litPylons[i] = true;
        pylonHp[i] = 200;
        G.Look.SetLit(pylons[i].Light, true);
        B?.Events.Emit(new Ev.Nova { X = pylons[i].X, Z = pylons[i].Z, Radius = 4, School = School.Frost, Duration = 0.8 });
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
        // The ward: the lamps take most of every blow.
        double mul = Ward[LitCount];
        if (ai.Mode == "stun") mul *= 1.5;
        e.TakenMul = mul;
        ai.CleaveCd -= dt; ai.ChargeCd -= dt; ai.ChannelCd -= dt;
        // Interrupted mid-channel (Battle.Interrupt sets this).
        if (ai.Mode == "channel" && e.State == EnemyState.Stunned)
        {
            ai.Mode = "stun"; ai.T = 0; e.StateT = 0;
            wardenView.SetPose("stunned");
            B.Events.Emit(new Ev.Announce { Title = "Channel broken", Tone = Tone.Boon });
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
                // Channel at thresholds, or when it has been a while.
                double? th = ai.Thresholds.Count > 0 ? ai.Thresholds[0] : null;
                if ((th is double t0 && hpK < t0) || ai.ChannelCd <= 0)
                {
                    if (th is double t1 && hpK < t1) ai.Thresholds.RemoveAt(0);
                    ai.Mode = "channel"; ai.T = 0; ai.ChannelHp = e.Hp; ai.ChannelCd = 34; ai.RaiseT = 0.6;
                    wardenView.SetPose("channel");
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
                    B.Events.Emit(new Ev.Telegraph { Id = e.Id * 10 + 1, Shape = TelegraphShape.Circle, X = ai.HitX, Z = ai.HitZ, Radius = 3.4, Duration = 1.05, Hostile = true });
                    wardenView.SetPose("windup");
                    return true;
                }
                if (dist > 6.5 && ai.ChargeCd <= 0)
                {
                    ai.Mode = "chargeWind"; ai.T = 0; ai.DirX = dx / dist; ai.DirZ = dz / dist;
                    double len = Math.Min(24, dist + 8);
                    B.Events.Emit(new Ev.Telegraph { Id = e.Id * 10 + 2, Shape = TelegraphShape.Line, X = e.X, Z = e.Z, X1 = e.X + ai.DirX * len, Z1 = e.Z + ai.DirZ * len, Radius = 0, Width = 3, Duration = 1.3, Hostile = true });
                    ai.Travelled = len;
                    wardenView.SetPose("charge-windup");
                    B.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = "It lowers its head..." });
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
                        B.Events.Emit(new Ev.Bark { X = e.X, Z = e.Z, Text = "The Warden reels!" });
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
                if (ai.ChannelHp - e.Hp > e.MaxHp * 0.09)
                {
                    ai.Mode = "stun"; ai.T = 0;
                    wardenView.SetPose("stunned");
                    B.Events.Emit(new Ev.Announce { Title = "Channel broken", Tone = Tone.Boon });
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
        spawnT -= dt;
        int n = Hostiles();
        Callouts();
        switch (Now)
        {
            case Stage.Wake:
                if (stageT > 1.2) Tip("move", "Move", "Keep *moving*. Your weapon strikes on its own.", ["W", "A", "S", "D"], 11);
                if (stageT > 3) { Go(Stage.Rising); spawnT = 0; }
                break;
            case Stage.Rising:
            {
                // Keep the clearing full: more of them the longer it goes on.
                double want = Math.Min(40, 16 + stageT * 0.3);
                if (spawnT <= 0 && n < want) { SpawnAround("risen", 2 + (stageT > 40 ? 1 : 0), 9, 14); spawnT = stageT > 30 ? 0.8 : 1.1; }
                // A great blessing on its own panel, half a minute after the first skill (au1 item 2: it came
                // with the first card, two picks and six lessons in 12 s); never on top of a level's draft.
                if (B.EmberLevel >= 2 && stageT > 40 && !B.DraftOwed && (G.Taught("first_draft") || stageT > 60) && shown.Add("great"))
                {
                    B.GreatOwed++;
                    // F3 says it on the panel (the general draft tip waits for the panels after it).
                    Teach("great_blessing", CalloutKind.Panel, "A great blessing", "The ember lends you a blessing. It changes how you fight until dawn.", Aim.At("cards"));
                }
                if ((B.EmberLevel >= 4 && stageT > 70) || stageT > 110)
                {
                    Go(Stage.Road);
                    checkpoint = new XZ(p.X, p.Z);
                    G.Say("The ground goes still. For now. The road runs north, toward the Waystation.", null, 5);
                    Objective([("Survive the night", true, false), ("Follow the road north", false, false)]);
                    Tip("road", "The road north", "Follow the *road*. The dead keep coming; let them come to your weapons, and keep your feet moving.");
                }
                break;
            }
            case Stage.Road:
            case Stage.Road2:
            {
                if (spawnT <= 0 && n < 24)
                {
                    var def = Now == Stage.Road2 && B.Rng.Next() < 0.2 ? "risen_warrior" : B.Rng.Next() < 0.12 ? "risen_archer" : "risen";
                    SpawnAround(def, 1 + (B.Rng.Next() < 0.5 ? 1 : 0), 10, 15, 0.55, Now == Stage.Road2 ? 2 : 1);
                    spawnT = 1.3;
                    if (def == "risen_warrior") Tip("shield", "Shieldmen", "Bolts and arrows glance off a *raised shield*. Get to its side, or hit it with something that is not a projectile.");
                }
                var cart = L("cart"); var post = L("post");
                if (Now == Stage.Road && p.Z < cart.Z + 7)
                {
                    Go(Stage.Ambush);
                    checkpoint = new XZ(cart.X - 3, cart.Z + 8);
                    G.Say("A wagon on its side, and the ditch beside it full of the drowned. One of them is still holding the reins. They were waiting.", null, 5);
                    Objective([("Follow the road north", true, false), ("Survive the ambush at the wagon", false, false)]);
                    for (int i = 0; i < 10; i++) SpawnAround(i % 4 == 0 ? "risen_warrior" : "risen", 1, 5, 9, 0, 2);
                }
                if (Now == Stage.Road2 && Dist(p.X, p.Z, post.X, post.Z) < 18)
                {
                    Go(Stage.Post);
                    checkpoint = new XZ(post.X - 6, post.Z + 4);
                    knight = B.SpawnEnemy("barrow_knight", post.X - 1, post.Z - 1.5, new Battle.SpawnOpts { Level = 1, Tag = "knight", Style = SpawnStyle.Rise });
                    // Its first red line comes once the narrator's line is over (F7 freezes on it), and it
                    // does not go down before it has run one: the elite shows what it does first.
                    knight.RangedT = 8;
                    knight.HpFloor = knight.MaxHp * 0.2;
                    for (int i = 0; i < 4; i++) SpawnAround("risen", 1, 5, 9, 0, 2);
                    G.Say("Something in old armor is standing guard over the dead watchman. It turns to look at you.", null, 5);
                    Objective([("Survive the ambush at the wagon", true, false), ("Put down the Barrow Knight", false, false), ("Search the old Watch-post", false, false)]);
                    Tip("elite", "Elites", "Bigger, tougher, and worth it: elites carry better things.", null, 12);
                }
                break;
            }
            case Stage.Ambush:
            {
                double want = Math.Min(46, 26 + stageT * 0.5);
                if (spawnT <= 0 && n < want)
                {
                    double r = B.Rng.Next();
                    SpawnAround(r < 0.22 ? "risen_warrior" : r < 0.32 ? "risen_archer" : "risen", 3 + (B.Rng.Next() < 0.5 ? 1 : 0), 8, 14, 0, 2);
                    spawnT = 1.05;
                }
                if (stageT > 48)
                {
                    Go(Stage.Road2);
                    checkpoint = new XZ(p.X, p.Z);
                    G.Say("The last of them falls back into the ditch and stays there. The one with the reins was a girl, twelve at most: red hair under the weed, and new boots.", null, 5);
                    Objective([("Survive the ambush at the wagon", true, false), ("Follow the road north", false, false)]);
                }
                break;
            }
            case Stage.Post:
                if (knight is { Alive: true } kn && !knightRan)
                {
                    if (kn.State == EnemyState.Windup) knightPlanted = true;
                    // (and it stands until its red line was frozen on, F7, or a while has passed)
                    else if ((knightPlanted && (G.Taught("red_line") || stageT > 40)) || stageT > 48) { knightRan = true; kn.HpFloor = 0; }
                }
                if (stageT > 8 && spawnT <= 0 && n < 16) { SpawnAround("risen", 1, 12, 16, 0.3, 2); spawnT = 2.5; }
                if (knight == null && !chestOpened)
                {
                    Tip("chest", "The Watch-post", "The *watchman's chest* is unguarded now.", [Key("interact")]);
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
                if (caller is { HpFloor: > 0 } cf && (G.Taught("art") || B.Time - callerAt > 30)) cf.HpFloor = 0;
                if (caller != null)
                {
                    if (spawnT <= 0 && n < 16 && stageT > 8) { SpawnAround("risen", 1, 11, 15, 0, 2); spawnT = 2.5; }
                }
                else if (stageT > 1)
                {
                    Go(Stage.ToFord);
                    var barrow = L("barrow");
                    checkpoint = new XZ(barrow.X + 10, barrow.Z - 6);
                    Objective([("Put down the Grave-Caller", true, false), ("Cross at the Low Ford", false, false)]);
                    G.Say("The dead go quiet. Somewhere ahead, water, and a cold blue light.", null, 5);
                }
                break;
            case Stage.ToFord:
                if (spawnT <= 0 && n < 18) { SpawnAround(B.Rng.Next() < 0.25 ? "risen_archer" : "risen", 1, 11, 15, 0.5, 2); spawnT = 2.4; }
                if (p.Z < L("ford").Z + 17) StartIntro();
                break;
            case Stage.Intro:
                RunIntro(dt);
                break;
            case Stage.Boss:
                if (warden is { Alive: true })
                {
                    int lit = LitCount;
                    Bar(new BossBar("The Ford-Warden", "Keeper of the Low Crossing", warden.Hp, warden.MaxHp, [0.7, 0.4], bar?.Channel, lit > 0));
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
                if (p.Z < ExitZ && !finished) { finished = true; Finish(); }
                break;
        }
    }

    void StartBarrow()
    {
        if (B == null) return;
        Objective([("Search the old Watch-post", true, false), ("Put down the Grave-Caller", false, false)]);
        var barrow = L("barrow");
        caller = B.SpawnEnemy("grave_caller", barrow.X - 3, barrow.Z, new Battle.SpawnOpts { Level = 2, Tag = "caller", Elite = true });
        // It can't fall before F8 has pointed at it (or a while has passed): the art is taught on it.
        if (!G.Taught("art")) { caller.HpFloor = caller.MaxHp * 0.2; callerAt = B.Time; }
        for (int i = 0; i < 5; i++)
        {
            double a = i / 5.0 * Math.PI * 2;
            B.SpawnEnemy(i % 3 == 0 ? "risen_warrior" : "risen", barrow.X + Math.Cos(a) * 4, barrow.Z + Math.Sin(a) * 4, new Battle.SpawnOpts { Style = SpawnStyle.Rise, Level = 2 });
        }
        G.Say("Past the fence, a figure in a tall hat is talking to the graves. The graves are listening.", null, 6);
    }

    /* ------------------------------------------------------------- intro -- */

    void StartIntro()
    {
        if (B == null) return;
        Go(Stage.Intro);
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

    /// <summary>C02's end: the Warden up and facing her an arm's length off, the fight on.</summary>
    void WardenUp()
    {
        if (B == null || warden != null) return;
        wardenInCine = false;
        var p = B.Player;
        // Where the cinematic leaves him (its mark warden_end), facing her.
        var (wx, _, wz, _) = CineFile.Load("c02").Mark("warden_end");
        warden = B.SpawnEnemy("ford_warden", wx, wz, new Battle.SpawnOpts { Level = 1, Tag = "warden" });
        if (warden != null)
        {
            warden.Facing = Math.Atan2(p.Z - wz, p.X - wx); ai.Mode = "walk"; ai.T = 0;
            // A beat after the bars go before his first blow: play opens 1.9 m from him (cinematics 3, k13).
            ai.ContactT = 1.0; ai.CleaveCd = Math.Max(ai.CleaveCd, 1.0);
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
        ai.Mode = "dead";
        wardenView.SetPose("dead");
        wardenPos = (e.X, e.Z, Math.PI / 2 - e.Facing);
        Bar(null);
        B.Events.Emit(new Ev.Shake { Amount = 0.9 });
        G.Announce(new Announcement("The Ford-Warden falls", null, "boon", 3.2));
        for (int i = 0; i < pylons.Count; i++) if (litPylons[i]) { litPylons[i] = false; G.Look.SetLit(pylons[i].Light, false); }
        ClearAround(e.X, e.Z, 40);
        // What it leaves.
        B.SpawnPickup(PickupKind.Item, e.X + 1.5, e.Z + 1, 1, "wardens_lampiron");
        B.SpawnPickup(PickupKind.Item, e.X - 1.2, e.Z + 1.6, 3, "ember_shard");
        for (int i = 0; i < 12; i++) B.SpawnPickup(PickupKind.Gold, e.X + (B.Rng.Next() - 0.5) * 4, e.Z + (B.Rng.Next() - 0.5) * 4, 4);
        Go(Stage.Victory);
        cutT = 0;
        Objective([("Cross at the Low Ford", true, false)]);
        // C03 (docs/cinematics/shoot/c03.md), where he fell: he kneels where he
        // is, facing south, and she is put 4 m before him on the cut after the
        // blow. What it sets is set at the hand-back, so a skip sets it too.
        var marks = new Dictionary<string, double[]> { ["w"] = [e.X, e.Z, 0], ["her"] = [e.X, e.Z + 4, Math.PI] };
        if (G.Cinematic("c03", HeartGone, marks)) { victoryByCine = true; wardenInCine = true; }
    }

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
        cutT += dt;
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
        Objective([("Walk up the road to the Waystation", false, false)]);
        W.Time = TimeOfDay.Dawn;
    }

    /// <summary>The dawn puts the ember out: the cards, the blessing, all it
    /// built. What the survivor carries, and what they learned, stay.</summary>
    /// <summary>C04 A: the ember goes out in it (its "douse" event), and the narrator says what Douse's caption did.</summary>
    void FirstLight(bool south, bool onward = false)
    {
        doused = true;
        W.Facts["prologue.dawn_south"] = south;
        if (!G.Cinematic("c04a", () =>
            {
                dawnK = 1; G.SetAtmosphere(Atmospheres.LowFordDawn); G.Look.SetNight(false); if (!dousedByCine) Douse(false);
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

    void Douse(bool caption = true)
    {
        if (B == null) return;
        var p = B.Player;
        B.Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = 3.4, School = School.Fire, Duration = 1.4 });
        B.Events.Emit(new Ev.Shake { Amount = 0.25 });
        int taught = G.Journey.Douse(B);
        G.Announce(new Announcement("The ember goes out", "First light takes back what it lent", "zone", 4.2, "Dawn"));
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
        // Without C04 A the narrator's words are a caption; with it, they were said in it.
        if (caption) G.After(1.2, () => G.Say("As the sun clears the trees, the ember goes out of you and back into the ground, and everything it gave you goes with it. What you carry, and what you have learned, are still yours. When the dark comes again, it will burn again. You try to call up your mother's face, and find it is not quite where you left it. Her voice is still there. \"Lamp's lit, Spark. Stay where it reaches.\"", null, 14));
        // F12 once her dawn line is over (the caption's 14 s; with C04 A it was said in it), and the
        // day's tip after that (game time: a freeze holds it back).
        if (taught > 0) G.After(caption ? 15.4 : 5.2, () => levelDue = true);
        G.After(caption ? 24.5 : 18.5, () => Tip("day", "By day", $"By day the ember sleeps: you fight with what you carry, your art and your feet, and every fight teaches you ({Key("character")}). The ember is for the night.", [Key("character")], 14));
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
        var gate = L("gate"); var camp = L("camp");
        // Back down the road from the Waystation: arrive at the north end, by the gate.
        return from == "waystation" ? new(gate.X + 0.5, ExitZ + 9, 0) : new(camp.X + 1.5, camp.Z - 1.5, Math.PI);
    }

    public override TimeOfDay TimeOf(WorldState w) => Now is Stage.Dawn or Stage.Exit ? TimeOfDay.Dawn : TimeOfDay.Night;
    public override AtmospherePreset AtmosphereFor(TimeOfDay t) => t == TimeOfDay.Dawn ? Atmospheres.LowFordDawn : Atmospheres.LowFordNight;

    public override void Begin(Battle b)
    {
        base.Begin(b);
        wardenView = G.Look.BossView("ford_warden");
        wardenView.SetPose("sleep");
        core = G.Look.Orb("#bfe6ff", 0.42);
        core.Visible = false;
        // The dead watchman at the post, where he fell: the fall played out and held.
        var man = L("watchman");
        watchman = G.Look.Fallen(new PersonSpec
        {
            Sex = Sex.Male, Outfit = Lore.OutfitFor(Sex.Male, "ranger", true, true), Beard = true, HairColor = "#4a3a2a", Skin = "#c8b0a0",
            Dye = new Dye { Cloth = "#4a5064" },
        }, new Held { Forearm = "shield_round" }, man.X, man.Z, 2.2, "Death_A");
        G.SetDraftTip(Draft);
        startWeapons = b.Weapons.Count;
        // (no great blessing offers to grow a Flare she hasn't met: F8 teaches it, au1 item 3)
        b.FlareGreatsHeld = !G.Taught("art");
        if (F("prologue.done").Truthy)
        {
            // Loaded after the prologue: the road at dawn, the dead at rest.
            Now = Stage.Exit; stageT = 0; dawnK = 1; doused = true;
            G.SetAtmosphere(Atmospheres.LowFordDawn);
            // (the host set the night from the time before the stage was known: the post's own torch burned on at dawn, E7b r3)
            G.Look.SetNight(false);
            b.Collision.RemoveTagged("gate");
            foreach (var p in pylons) G.Look.SetLit(p.Light, false);
            ai.Mode = "dead"; wardenGone = true;
            wardenView.Hide();
            return;
        }
        G.SetAtmosphere(Atmospheres.LowFordNight);
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
        // C03's Grimtunnel comes up while the zone's director waits: his surfacing is kept here.
        if (grimByCine && grim is { Alive: true, State: EnemyState.Surfacing } gs) { gs.StateT -= dt; if (gs.StateT <= 0) gs.State = EnemyState.Active; }
        if (wardenGone) return;
        if (wardenInCine) { wardenView.Hide(); return; }
        if (warden is { Alive: true } && warden.State != EnemyState.Dying) wardenPos = (warden.X, warden.Z, Math.PI / 2 - warden.Facing);
        double wy = Math.Max(G.Look.HeightAt(wardenPos.X, wardenPos.Z), waterY - 0.25);
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
        // The ember is not done with you. Up again where you were last safe.
        if (B == null) return true;
        var battle = B;
        G.After(2.6, () =>
        {
            G.Say("The ember will not let you go so easily.", null, 3.5);
            battle.Over = null;
            var p = battle.Player;
            p.Alive = true;
            p.Hp = battle.MaxHp;
            p.Iframes = 3;
            p.X = checkpoint.X; p.Z = checkpoint.Z;
            ClearAround(p.X, p.Z, 16);
            G.Revived(p.X, p.Z);
            if (warden is { Alive: true } && Now == Stage.Boss)
            {
                warden.Hp = Math.Min(warden.MaxHp, warden.Hp + warden.MaxHp * 0.25);
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
        ["stage"] = Now.ToString(), ["stageT"] = stageT, ["chestOpened"] = chestOpened, ["lit"] = LitCount, ["wardenHp"] = warden?.Hp,
        ["wardenMode"] = ai.Mode, ["checkpoint"] = $"{checkpoint.X:0.0},{checkpoint.Z:0.0}",
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
