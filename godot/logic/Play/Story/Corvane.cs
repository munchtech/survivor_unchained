using System;
using System.Collections.Generic;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Story;

/// <summary>
/// Corvane in the doorway (vault_opened's first stage, phase 1 of the night; P6): the court before the Sealed Door. He
/// stands in it with the keeper's lamp held up, and talks (door_night from go_home). Lowered, she walks away and the night
/// lets her go. Raised, he turns, and the fight is his one signature (CorvaneStory) until he goes down; then the door's
/// film plays (c13_door), or its lines are said (gets_up, the sigil's cue, gone), his lamp is left lit where he stood,
/// and the door opens on the hall. Lost here, he carries her home (corvane.carried; the Vault is not shut). Every number
/// is teeth.json story.corvane.
/// </summary>
public sealed class Doorway : StoryBeat
{
    /// <summary>The result's last lines (the lead's drafts; the story lead may amend them).</summary>
    public const string WalkAway = "You go back down the hill the way you came. Behind you the violet lamp does not move.";
    public const string Carried = "The last thing you know is violet light, held low, and being carried, carefully, a long way.";
    /// <summary>The night's mark that she raised her weapon (a rise replays the fight, not the talk).</summary>
    public const string RaisedMark = "doorway.raised";

    readonly Content.Teeth.Corvane t = Content.Teeth.OfCorvane;
    Enemy? corvane;
    double seed, talkT;
    CorvaneStory? script;
    bool raised, talking, fallen, closed;

    public override string Goal => raised ? "Bring down Corvane" : "Corvane stands in the door";
    public override string? Gate => "door";
    public override double Minute => 0;
    public override string Start => "court_in";
    public override int EmberFloor => t.EmberFloor;
    public override string? OnLose => """[{ "set": { "corvane.carried": true } }]""";
    public override string? EndLost => Carried;
    public override ArenaBoss? Script => script is { Down: false } ? script : null;
    public override BossBar? Bar => script is { Down: false } && Up(corvane, seed) ? script.Bar("Corvane", "") : null;
    /// <summary>For the harness: he has gone down, and when (the fight's seconds from the raise).</summary>
    public bool Fell => fallen;
    public double? KillSeconds { get; private set; }
    public CorvaneStory? Boss => script;
    public Enemy? Him => corvane;

    protected override void Open()
    {
        var (x, z) = A.Place["corvane"];
        corvane = A.Spawn("corvane", x, z, true, SpawnStyle.Walk);
        if (corvane == null) { Done = true; return; }
        seed = corvane.Seed;
        var e = corvane;
        e.Disposition = Disposition.Neutral;
        e.Provoked = false;
        e.MaxHp = e.Hp = e.MaxHp * t.HpMul / A.BossEase;
        A.Script(e, Still);
        // A rise replays the fight, not the talk.
        if (A.Marked(RaisedMark)) Raise(rise: true);
    }

    /// <summary>Before the raise: he stands in the door facing her, the lamp up.</summary>
    bool Still(Enemy e, double dt)
    {
        var p = B.Player;
        e.Vx = e.Vz = 0;
        e.Facing = Math.Atan2(p.Z - e.Z, p.X - e.X);
        e.State = EnemyState.Idle;
        e.Anim = EnemyAnim.Idle;
        return true;
    }

    protected override void Tick(double dt)
    {
        if (closed) return;
        if (!raised)
        {
            if (talking || corvane == null) return;
            if ((talkT += dt) < t.TalkAfter || !A.Settled) return;
            talking = true;
            A.Converse("door_night", "go_home", Answered);
            return;
        }
        if (fallen) return;
        if (script is { Down: true } || !Up(corvane, seed)) { Fallen(); return; }
        A.Goal = (corvane!.X, corvane.Z);
    }

    void Answered(string? end)
    {
        talking = false;
        if (end == "go") { closed = true; A.LetNightGo(null, WalkAway); return; }
        Raise(rise: false);
    }

    /// <summary>She raised her weapon: he turns, and his script starts (and holds its hand first).</summary>
    void Raise(bool rise)
    {
        var e = corvane!;
        raised = true;
        A.Mark(RaisedMark);
        e.Disposition = Disposition.Hostile;
        e.Boss = true;
        e.Named = new Named { Title = "Corvane" };
        script = new CorvaneStory(A, t, A.Place["corvane"], A.Place["door"]);
        e.Damage = script.Teeth * A.OwnHealth;
        script.Begin(e);
        A.Script(e, (en, dt) => { script.Tick(en, dt); return true; });
        if (rise) A.Bark(e.X, e.Z, script.ReEntry, null);
    }

    /// <summary>He is down: the story told at once, his body where it fell, then the door's film or its lines.</summary>
    void Fallen()
    {
        fallen = true;
        var e = corvane!;
        KillSeconds = script?.FightT;
        A.Apply("""[{ "set": { "corvane.rose": true } }]""");
        A.Goal = null;
        var p = B.Player;
        // Marks for the film where things really are: [x, z, facing], both facings as hers is kept (atan2(dx, dz)).
        var marks = new Dictionary<string, double[]>
        {
            ["corvane"] = [e.X, e.Z, Math.PI / 2 - e.Facing],
            ["her"] = [p.X, p.Z, p.Facing],
        };
        if (!A.Cinematic("door", Close, marks))
            A.Converse("door_night", "gets_up", _ =>
            {
                B.Events.Emit(new Ev.Cue { Id = "door_sigil" });
                A.Converse("door_night", "gone", _ => Close());
            });
    }

    /// <summary>He is gone: his lamp set down where he stood, still lit, and the door opens.</summary>
    void Close()
    {
        if (closed) return;
        closed = true;
        if (corvane is { Alive: true } e && e.Seed == seed) B.Enemies.Release(e);
        var (x, z) = A.Place["corvane"];
        var lamp = A.Piece("halloween/lantern_standing", 1);
        lamp.Place(x, A.HeightAt(x, z), z, 0, 1);
        lamp.Visible = true;
        A.Look.AddLight(x, 0.9, z, "#a77bff", 2.6, 9, 0.08, 0.1, "#c9a8ff");
        Done = true;
    }
}
