using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* A place the survivor can be, as the game runs it (the web game's
 * game/zone.ts and its zones/*.ts). The build is the look and the colliders
 * (exported: World/Zone.cs); the runtime is what happens there: who stands
 * where, what can be used, what the night sends, what the place remembers.
 * Runtimes read and write the world through the logic context, reach the
 * game through IZoneHost and the view through IZoneLook, so they run and
 * are tested without a screen. */

public sealed class Interactable
{
    public string Id = "", Verb = "", Name = "";
    public double X, Z;
    /// <summary>How close the survivor must be.</summary>
    public double R;
    /// <summary>Height of the prompt anchor.</summary>
    public double? Y;
    public Func<string?>? Hint;
    /// <summary>Not offered at all unless this holds.</summary>
    public Func<bool>? When;
    /// <summary>Offered but refused, with the reason ("Locked").</summary>
    public Func<string?>? Locked;
    public Action Act = () => { };
}

public readonly record struct Arrival(double X, double Z, double Facing = 0);

public enum MarkKind { Place, Quest, Turn, Exit, Danger, Person, Mystery }
public sealed record MapMark(double X, double Z, string Label, MarkKind Kind);

/// <summary>The bar over a fight worth one: where its phases turn, what it
/// is calling up (break it!), whether something is shielding it.</summary>
public sealed record BossBar(string Name, string Title, double Hp, double MaxHp, double[]? Phases = null,
    (string Label, double Progress)? Channel = null, bool Shielded = false);

/// <summary>A tip on screen: its keys, as the player has them bound.</summary>
public sealed record Hint(string Id, string Title, string Text, List<string> Keys);

/// <summary>What the place sounds like where the survivor is (0..1 each).</summary>
public sealed class AmbienceMix
{
    public double Wind, Leaves, Fire, Water, Hum, Birds, Crickets, Owl, Town, Crowd, Drip, Smithy;
}

/// <summary>The game, as a zone sees it.</summary>
public interface IZoneHost
{
    Journey Journey { get; }
    WorldState World => Journey.World;
    Ctx Ctx => Journey.Ctx;
    /// <summary>The fight (or walk) running here.</summary>
    Battle? Battle { get; }
    IZoneLook Look { get; }
    /// <summary>Chance, where the web game rolls Math.random().</summary>
    Random Rng { get; }

    void Apply(IEnumerable<Change> changes);
    void Apply(string changesJson) => Apply(Json.Parse<List<Change>>(changesJson));
    /// <summary>A line under the picture (who says it, if anyone).</summary>
    void Say(string text, string? who = null, double seconds = 4);
    void Toast(Toast t);
    void Announce(Announcement a);
    void Talk(string npc);
    void Travel(string zone, string? caption = null, string? sub = null);
    /// <summary>Later, in game time (forgotten if the zone is left first).</summary>
    void After(double seconds, Action fn);
    void Save(string reason);
    bool GiveItem(string def, int qty = 1, int? rarity = null);
    void ReturnItem(Rpg.ItemInstance it);
    void SetBoss(BossBar? bar);
    void SetObjectives(List<Tracked> list);
    void SetHint(Hint? hint);
    Hint? CurrentHint { get; }
    /// <summary>The air (rebuild: the sky's lighting too; not every frame of a blend).</summary>
    void SetAtmosphere(AtmospherePreset p, bool rebuild = true);
    /// <summary>A held camera (a cutscene), or null to go back to the survivor.</summary>
    void Showcase((double X, double Y, double Z)? pos, (double X, double Y, double Z) look = default);
    /// <summary>The survivor's controls held (a cutscene), or given back.</summary>
    void Capture(bool on);
    /// <summary>What the level-up draft says, the first times it opens.</summary>
    void SetDraftTip(string tip);
    /// <summary>The survivor is up again here (the prologue's forgiveness).</summary>
    void Revived(double x, double z);
    /// <summary>The key or button bound to an action, as the player would name it.</summary>
    string KeyLabel(string action);
    void AnnounceZone();
    /// <summary>A screen over the game ('maps': the Wayfinder's table).</summary>
    void Open(string overlay) { }
}

/// <summary>The zone's look, as a runtime reaches into it.</summary>
public interface IZoneLook
{
    /// <summary>A light on or off, its glowing bits and its fire with it.</summary>
    void SetLit(int light, bool on);
    bool IsLit(int light);
    /// <summary>Show or hide a named piece of the landmarks.</summary>
    void Show(string node, bool visible);
    bool Shown(string node);
    /// <summary>A named piece that turns (a pump's wheel) stops.</summary>
    void Stop(string node);
    /// <summary>A kit piece set down now (a grave marker); lift raises it off the ground (onto a table).</summary>
    void AddProp(string id, double x, double z, double rot = 0, double scale = 1, double lift = 0);
    /// <summary>A light set down now, with a small flame that glows with it.
    /// Returns its index (for SetLit).</summary>
    int AddLight(double x, double y, double z, string color, double intensity, double distance, double flicker = 0.12, double glowSize = 0.08, string glowColor = "#ffb35a");
    /// <summary>A person standing in the world.</summary>
    INpcView Person(NpcDef def, Spot spot);
    /// <summary>Someone from the town, made up (Folk): a person as a spec.</summary>
    INpcView Walker(PersonSpec spec, double scale);
    /// <summary>A light that goes where something carries it (a torch).</summary>
    void MoveLight(int light, double x, double y, double z);
    /// <summary>The ground's height.</summary>
    double HeightAt(double x, double z);
    /// <summary>After dark or not (night-only pieces, moths, smoke).</summary>
    void SetNight(bool on);
    /// <summary>Names over heads (and a mark when someone has something for you).</summary>
    void Plates(List<Plate> plates);
    /// <summary>Words said to the air, over someone's head.</summary>
    void Bark(string text, double x, double y, double z, string? speaker = null);
    /// <summary>A boss drawn by its own view (the Ford-Warden), not the crowd's.</summary>
    IBossView BossView(string kind);
    /// <summary>A body lying where it fell: a person, a clip played out and held.</summary>
    INpcView Fallen(PersonSpec spec, Held? arms, double x, double z, double facing, string clip);
    /// <summary>A bright thing with a light of its own (the Warden's heart).</summary>
    IOrb Orb(string color, double size);
}

/// <summary>A boss's own view: a pose (sleep, wake, walk, windup, cleave,
/// charge-windup, charge, stunned, channel, dead), released back to its
/// walk; how brightly its lamp burns; where it is.</summary>
public interface IBossView
{
    void SetPose(string pose);
    void Release();
    double Glow { set; }
    void Update(Enemy? e, double x, double y, double z, double facing, double dt);
    void Hide();
    void Dispose();
}

public interface IOrb
{
    bool Visible { get; set; }
    void Place(double x, double y, double z, double spin, double scale);
    double Light { set; }
    void Dispose();
}

public sealed record Plate(string Id, double X, double Y, double Z, string Name, string? Role = null, char? Marker = null);

/// <summary>How a person is drawn: moved, turned, posed.</summary>
public interface INpcView
{
    void Place(double x, double y, double z, double heading, bool visible);
    /// <summary>A looping pose (an idle, sitting, hammering), blended in.</summary>
    void Loop(string clip, double blend = 0.3, double speed = 1);
    /// <summary>A gesture once, then back to the loop.</summary>
    void Act(string clip, double speed = 1);
    /// <summary>Walking, at this speed (m/s): idle, walk or run, blended.</summary>
    void Locomotion(double speed) { }
    /// <summary>Something in a hand ('handslot.r'): a kit piece, or nothing.</summary>
    void Hold(string slot, string? pack, string? piece) { }
    void Dispose();
}

/// <summary>A person standing in the world (the web game's NpcActor): they
/// keep to their spot and pose, turn to look at the survivor when they come
/// near, and now and then say something to the air.</summary>
public sealed class NpcActor
{
    public readonly NpcDef Def;
    readonly IZoneLook look;
    readonly INpcView view;
    readonly Random rng;
    public double X, Z, Facing, Heading;
    public bool Talking, Hidden;
    /// <summary>After dark: they say different things.</summary>
    public bool Night;
    string pose;
    double barkT;

    public NpcActor(NpcDef def, IZoneLook look, Random rng, Spot? at = null)
    {
        Def = def;
        this.look = look;
        this.rng = rng;
        var spot = at ?? def.Spot;
        X = spot.X; Z = spot.Z; Facing = Heading = spot.Facing;
        view = look.Person(def, spot);
        pose = def.Idle;
        view.Loop(def.Idle, 0, def.Idle == "1H_Melee_Attack_Chop" ? 0.55 : 1);
        barkT = 6 + rng.NextDouble() * 14;
    }

    public bool Seated => pose.StartsWith("Sit");
    public string Pose => pose;

    /// <summary>Somewhere else now (a routine, a change in their circumstances).</summary>
    public void Place(Spot spot, string? idle = null)
    {
        idle ??= Def.Idle;
        X = spot.X; Z = spot.Z; Facing = Heading = spot.Facing;
        if (idle != pose)
        {
            pose = idle;
            view.Loop(idle, 0.3, idle == "1H_Melee_Attack_Chop" ? 0.55 : 1);
        }
    }

    public void Update(double dt, double px, double pz)
    {
        if (Hidden) { view.Place(X, 0, Z, Heading, false); return; }
        double y = look.HeightAt(X, Z) + (pose == "Sit_Chair_Idle" ? 0.05 : 0);
        double d = Math.Sqrt((px - X) * (px - X) + (pz - Z) * (pz - Z));
        double toPlayer = Math.Atan2(px - X, pz - Z);
        // Look at whoever comes close; seated people only turn a little.
        double want = Facing;
        if (Talking || d < 5.5)
        {
            want = toPlayer;
            if (Seated) want = Facing + Math.Clamp(Math.Atan2(Math.Sin(toPlayer - Facing), Math.Cos(toPlayer - Facing)), -0.7, 0.7);
        }
        Heading = MathX.DampAngle(Heading, want, 4, dt);
        view.Place(X, y, Z, Heading, true);
        // A hammering smith stops to talk.
        if (Talking && pose == "1H_Melee_Attack_Chop") { view.Loop("Idle", 0.3); pose = "Idle:talk"; }
        if (!Talking && pose == "Idle:talk") { view.Loop(Def.Idle, 0.4, 0.55); pose = Def.Idle; }
        // Things said to nobody.
        barkT -= dt;
        if (barkT <= 0 && !Talking && d < 9 && d > 2.5)
        {
            barkT = 30 + rng.NextDouble() * 30;
            var pool = Night && Def.NightBarks is { Count: > 0 } nb ? nb : Def.Barks;
            if (pool.Count > 0) look.Bark(pool[rng.Next(pool.Count)], X, y + (Def.Scale ?? 1) * 0.4 - 0.2, Z);
        }
    }

    /// <summary>A gesture while speaking.</summary>
    public void Gesture()
    {
        if (Seated || pose == "Spellcasting") return;
        view.Act(rng.Next(2) == 0 ? "Interact" : "Cheer", 0.9);
    }

    public void Dispose() => view.Dispose();
}

/// <summary>What a zone's runtime is: the web game's ZoneRuntime.</summary>
public abstract class ZoneRuntime
{
    public abstract string Id { get; }
    public abstract string Name { get; }
    public virtual string? Region => null;
    public abstract bool Combat { get; }
    /// <summary>Every creature that can appear here (their looks are readied
    /// behind the fade, not the first time one walks on).</summary>
    public virtual IReadOnlyList<string> Creatures => Array.Empty<string>();
    public readonly List<Interactable> Interactables = new();
    /// <summary>People standing here, by id.</summary>
    public readonly Dictionary<string, NpcActor> Actors = new();
    public BattleHooks Hooks = new();

    protected readonly IZoneHost G;
    protected readonly ZoneMeta Meta;
    protected Battle? B;

    protected ZoneRuntime(IZoneHost host, ZoneMeta meta)
    {
        G = host;
        Meta = meta;
    }

    protected WorldState W => G.Journey.World;
    protected Ctx C => G.Journey.Ctx;
    protected Fact F(string key) => W.Fact(key);
    static readonly Dictionary<string, Cond> conds = new();
    /// <summary>A condition, as the web game writes one (JSON; read once).</summary>
    protected bool Test(string condJson)
    {
        if (!conds.TryGetValue(condJson, out var c)) conds[condJson] = c = Json.Parse<Cond>(condJson);
        return Rules.Test(c, C);
    }
    protected bool Knows(string k) => Rules.Test(new Cond { Knows = k }, C);
    protected bool HasItem(string def) => Rules.Test(new Cond { HasItem = def }, C);
    protected bool Quest(string id, string entry) => Rules.Test(new Cond { Quest = new QuestCond { Id = id, Entry = entry } }, C);
    protected XZ P(string table, string name) => Meta.Place(table, name);

    /// <summary>Where you stand arriving from another zone (null: a fresh load).</summary>
    public abstract Arrival ArrivalFrom(string? from);
    /// <summary>The Battle exists: set hooks, stand the residents up.</summary>
    public virtual void Begin(Battle b) => B = b;
    /// <summary>Each fixed step of the simulation.</summary>
    public virtual void Step(double dt) { }
    /// <summary>Each rendered frame.</summary>
    public virtual void Frame(double dt) { }
    public virtual void Events(IReadOnlyList<CombatEvent> evs) { }
    /// <summary>The time of day the zone shows, from the world.</summary>
    public virtual TimeOfDay TimeOf(WorldState w) => w.Time;
    /// <summary>A death here: true if the zone handled it (the prologue does).</summary>
    public virtual bool OnDeath(string killer) => false;
    public virtual List<MapMark> MapMarks() => new();
    /// <summary>Ground you know without walking it (a town seen whole from its gate).</summary>
    public virtual List<(double X, double Z, double R)> MapKnown => new();
    /// <summary>Where the map opens, and how close, if not the whole zone.</summary>
    public virtual (double X, double Z, double Zoom)? MapFocus => null;
    /// <summary>The sky and light for an hour of the day, if the place has its own.</summary>
    public virtual AtmospherePreset AtmosphereFor(TimeOfDay t) => t switch
    {
        TimeOfDay.Night => Atmospheres.Night, TimeOfDay.Dusk => Atmospheres.Dusk, TimeOfDay.Dawn => Atmospheres.Dawn, _ => Atmospheres.Day,
    };
    /// <summary>A place that wants its own music (a mystery, a shrine).</summary>
    public virtual string? MusicMood(double x, double z) => null;
    public virtual AmbienceMix Ambience(double x, double z) => new();
    public virtual Dictionary<string, object?> Debug() => new();
    public virtual void Dispose()
    {
        foreach (var a in Actors.Values) a.Dispose();
        Actors.Clear();
    }

    /// <summary>How close a lit fire is, 0..1: for the crackle in the ambience.</summary>
    protected double Warmth(double x, double z, double reach = 13)
    {
        double k = 0;
        for (int i = 0; i < Meta.Lights.Count; i++)
        {
            var s = Meta.Lights[i];
            var (r, _, b) = Atmospheres.Linear(s.Color);
            if (!G.Look.IsLit(i) || s.Flicker < 0.18 || r < b) continue;
            double d = Dist(s.X, s.Z, x, z);
            if (d < reach) k = Math.Max(k, Math.Pow(1 - d / reach, 2) * Math.Min(1, s.Intensity / 6));
        }
        return k;
    }

    /// <summary>A history change, as the web game's hist() writes one.</summary>
    protected static string Hist(string id, string text, string[] tags, int spread, string? sentiment = null, string? reactions = null) =>
        $$"""{ "history": { "id": "{{id}}", "text": "{{Esc(text)}}", "tags": [{{string.Join(", ", Array.ConvertAll(tags, t => $"\"{t}\""))}}], "spread": {{spread}}{{(sentiment != null ? $", \"sentiment\": {sentiment}" : "")}}{{(reactions != null ? $", \"reactions\": {reactions}" : "")}} } }""";

    protected static string Esc(string s) => s.Replace("\\", "\\\\").Replace("\"", "\\\"");

    protected static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
}
