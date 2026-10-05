using System;
using System.Collections.Generic;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Story;

/* A story fight, as written for its night (docs/design/STORY_BOSSES.md): its
 * place, three stages each ended by its goal and never by a clock, the
 * story's sight between them, and a boss on its own ground that ends the way
 * its cinematic does. The night that runs it is Play/Zones/StoryNight.cs;
 * these are the fight's own pages. */

/// <summary>What a story fight's stages and its boss may ask of the night they are in.</summary>
public interface IStoryArena : IBossArena
{
    StoryPlace Place { get; }
    /// <summary>The creature level now: the tier's, and the stage's own over it.</summary>
    int Level { get; }
    /// <summary>A named foe: a miniboss of its people, on the bar while it lives, carrying a small chest.
    /// `kicker`: over its name (the fight's own by default); `quiet`: not announced (a picket, one of three).</summary>
    Enemy? Foe(string def, double x, double z, double hpMul = 1, string? kicker = null, bool quiet = false);
    /// <summary>A few of a kind round a point (on standable ground inside the place).</summary>
    List<Enemy> Group(string def, int n, double x, double z, double spread, SpawnStyle? style = null);
    /// <summary>The hostile creatures standing (of a kind, if asked).</summary>
    int Hostiles(Func<Enemy, bool>? which = null);
    /// <summary>How hard the way in's rank and file bite, against a table night's at their level (ground they
    /// foul bites the same).</summary>
    double Teeth { get; }
    /// <summary>The place's deadfalls and braziers: lit by standing at them.</summary>
    IReadOnlyList<Deadfall> Fires { get; }
    /// <summary>A world fact holds (a bane learned by day).</summary>
    bool Fact(string key);
    /// <summary>A world fact as it stands (who is in the cages, where the crates went).</summary>
    SurvivorUnchained.World.Fact FactOf(string key);
    /// <summary>The world told what happened (the story's effects, as a dialogue's are).</summary>
    void Apply(string effectsJson);
    /// <summary>A condition on the world, as dialogue tests it (a flag on someone, a thing she knows).</summary>
    bool Test(SurvivorUnchained.World.Cond cond);
    /// <summary>She knows it (a clue, a name).</summary>
    bool Knows(string key);
    /// <summary>Something that happened tonight, in this fight (the crates fired): marked, and asked after.</summary>
    void Mark(string key);
    bool Marked(string key);
    /// <summary>Done this many seconds on (a cart dragged, a cage closing).</summary>
    void After(double seconds, Action act);
    /// <summary>Where the stage wants her (a fire to light, a foe to find): the hands go there when
    /// nothing threatens. Null: wherever the fight is.</summary>
    (double X, double Z)? Goal { get; set; }
    /// <summary>A creature the script moves (a living wall, a caller holding its howl): `tick` runs in
    /// its mind's place each step; false lets its own mind have the step.</summary>
    void Script(Enemy e, Func<Enemy, double, bool> tick);
    /// <summary>A choice put in front of her where she stands (let him go, finish it).</summary>
    void Offer(string id, double x, double z, string verb, string name, Action act);
    void Withdraw(string id);
    /// <summary>The narrator's words (the story lead's), or someone's, said aloud.</summary>
    void Line(string text, string? speaker = null);
    /// <summary>A spared ending can be chosen in this fight (its outcome is in the spec).</summary>
    bool CanSpare { get; }
    /// <summary>The prompt beside "Finish it" ("Let him go", "Spare him").</summary>
    string SpareVerb { get; }
    /// <summary>The fight ends as she chose: spared or not (its outcome told to the story first).</summary>
    void Ended(double x, double z, bool spared);
}

/// <summary>Dead wood (or a brazier) that the ember in her lights: she stands at it for two
/// seconds. It burns a while and can be lit again; what fears fire keeps out of its light.</summary>
public sealed class Deadfall
{
    public required string Id;
    public double X, Z;
    /// <summary>Seconds it has left to burn (0: out); how long she has stood at it; its light's index.</summary>
    public double Lit, Kindling;
    public int Light = -1;
    /// <summary>How far its light reaches.</summary>
    public double Reach = 5;
    /// <summary>How long a lighting burns.</summary>
    public double Burns = 20;
    /// <summary>Lit at least once this fight.</summary>
    public bool EverLit;
    public bool Burning => Lit > 0;
    public bool InLight(double x, double z, double margin = 0) => Burning && (x - X) * (x - X) + (z - Z) * (z - Z) < (Reach + margin) * (Reach + margin);
}

/// <summary>Something broken by standing at it (a cage's lock, a cage's post). Her weapons fire on their
/// own at whatever is near, so what breaks must be what she chose: the one she stands by, never the one a
/// stray shot found (STORY_BOSSES.md 0.5). Its ring fills as she works at it.</summary>
public sealed class StandBy
{
    public double X, Z;
    /// <summary>How near she must stand, and how long it takes her there.</summary>
    public double Reach = 3.5, Takes = 4;
    /// <summary>How far she has got with it (0 to 1), and whether it has given.</summary>
    public double Done;
    public bool Broken;
    double drawT;

    /// <summary>She is at it.</summary>
    public bool At(Battle b) => !Broken && (b.Player.X - X) * (b.Player.X - X) + (b.Player.Z - Z) * (b.Player.Z - Z) < Reach * Reach;

    /// <summary>A step of it (`mark`: its ring's id, drawn while she works at it): true the moment it gives.</summary>
    public bool Step(Battle b, double dt, int mark)
    {
        if (Broken) return false;
        bool at = At(b);
        if (at) Done = Math.Min(1, Done + dt / Takes);
        if (at && (drawT -= dt) <= 0)
        {
            drawT = 0.2;
            b.Events.Emit(new Ev.Telegraph { Id = mark, Shape = TelegraphShape.Ring, Kind = TelegraphKind.Safe, X = X, Z = Z, Inner = Math.Max(0.2, Reach * (1 - Done)), Radius = Reach, Duration = 0.3, Hostile = false });
        }
        if (Done < 1) return false;
        Broken = true;
        return true;
    }
}

/// <summary>One stage of the way in: a goal, the waves that make it hard, and where she gets up
/// if she falls in it (made afresh each time it is begun, so a rise replays it).</summary>
public abstract class StoryBeat
{
    protected IStoryArena A = null!;
    protected Battle B => A.B;
    /// <summary>What she is asked, for the objectives.</summary>
    public abstract string Goal { get; }
    /// <summary>The gate it opens when it is won (null: none).</summary>
    public virtual string? Gate => null;
    /// <summary>The table night's minute this stage stands for: its creatures' levels (a table's,
    /// one every two and a half minutes) and how much its crowd is softened (ArenaRun.FodderEase).</summary>
    public abstract double Minute { get; }
    /// <summary>Creature levels over the tier's base.</summary>
    public int Level => (int)(Minute / 2.5);
    /// <summary>Its crowd: the kinds (weighted), how many are kept standing, how many there are in all
    /// (finite: nothing is farmed), and the place's points they come from. The crowd is the ember's
    /// food: a story night is still a night.</summary>
    public virtual (string Def, double Weight)[] Crowd => [];
    public virtual int CrowdAlive => 0;
    public virtual int CrowdPool => 0;
    public virtual string[] CrowdFrom => [];
    /// <summary>The ember she has when it ends, at least: what its dead would have given her, so a quick
    /// stage is not a weaker night.</summary>
    public virtual int EmberFloor => 0;
    /// <summary>The place's point she begins it from (and gets up at).</summary>
    public abstract string Start { get; }
    public bool Done { get; protected set; }
    public double T { get; private set; }
    /// <summary>The bar while it is fought (its named foe's).</summary>
    public virtual BossBar? Bar => null;

    public void Begin(IStoryArena a)
    {
        A = a;
        T = 0;
        Done = false;
        Open();
    }

    protected abstract void Open();

    public void Step(double dt)
    {
        T += dt;
        if (!Done) Tick(dt);
    }

    protected abstract void Tick(double dt);
    /// <summary>The stage is over (won, or left by a rise): what it put down goes.</summary>
    public virtual void End() { }

    protected static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
    protected static bool Up(Enemy? e, double seed) => e is { Alive: true } x && x.Seed == seed && x.State != EnemyState.Dying;
}

/// <summary>A story fight's pages: its place, its stages, the story's words between them, and its boss.</summary>
public abstract class StoryFight
{
    /// <summary>The fight's spec id (StoryFights.Spec).</summary>
    public abstract string Id { get; }
    public abstract StoryPlace Place { get; }
    /// <summary>Where the ember sets her down.</summary>
    public abstract string Arrive { get; }
    /// <summary>The stages, each made afresh.</summary>
    public abstract Func<StoryBeat>[] Beats { get; }
    /// <summary>The pull, and the sight after each stage (docs/WRITING_PASS.md §21, §23).</summary>
    public abstract string Pull { get; }
    public abstract string[] Between { get; }
    /// <summary>The sight after a stage, where it reads the world (who is in the cages); by default, Between's.</summary>
    public virtual string? BetweenSight(IStoryArena a, int stage) => stage < Between.Length ? Between[stage] : null;
    /// <summary>The words over its named foes' names (its people).</summary>
    public virtual string Kicker => "";
    /// <summary>Arena art has built the place to this outline (its own ground and cover): until then the old
    /// arena's props inside it are cleared (StoryNight.Begin). Arena art sets it as each place lands.</summary>
    public virtual bool PlaceBuilt => false;
    /// <summary>The sight as the way back shuts behind her on the boss's ground.</summary>
    public virtual string? ShutSight => null;
    /// <summary>The boss's own ground: the gate that opens on it (null: the last stage's ground),
    /// where it comes from, and where she stands as it does (and gets up there).</summary>
    public virtual string? BossGate => null;
    public abstract string BossAt { get; }
    public abstract string BossStart { get; }
    /// <summary>The table night's minute the boss stands for (its level), measured against the build a
    /// story night gives: about a table night's twelfth minute (ember near thirty).</summary>
    public virtual double BossMinute => 12;
    public int BossLevel => (int)(BossMinute / 2.5);
    /// <summary>Its sign, heard before it comes.</summary>
    public abstract string Sign { get; }
    public abstract string BossDef { get; }
    /// <summary>The boss's cinematic (arrival and end), by the story's ids (docs/cinematics).</summary>
    public virtual string? Cinematic => null;
    public abstract StoryBoss Boss(IStoryArena a);
    /// <summary>The place's fires (id, point), and how long one burns.</summary>
    public virtual string[] Fires => [];
    public virtual double Burns(IStoryArena a) => 20;
}

/// <summary>The story fights whose nights are written (the rest still run as a table's night, told quicker).</summary>
public static class StoryScripts
{
    public static StoryFight? For(string specId) => specId switch
    {
        "hollow_by_night" => new HollowByNight(),
        "roost_raid" => new RaidOnTheRoost(),
        _ => null,
    };

    public static bool Has(string specId) => For(specId) != null;
}
