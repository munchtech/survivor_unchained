using System;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Bosses;

/// <summary>
/// A story fight's boss (docs/design/STORY_BOSSES.md 0.4): the contract of
/// ArenaBoss, made for a longer fight at the end of a short night. Its phases
/// each change the space; their floors are 25, 30 and 25 s and their ceilings
/// 75, so an absurd build still takes about two minutes and a weak one sees
/// every move; it grows wild at four and a half minutes and comes to its end
/// at six. The horde is off: the only creatures on its ground are those it
/// calls, each with a job. Its ending is the story's, and what it put on the
/// ground goes with it (or with a rise at its opening, which begins it again).
/// </summary>
public abstract class StoryBoss : ArenaBoss
{
    protected readonly IStoryArena S;
    protected StoryBoss(IStoryArena a) : base(a) => S = a;

    protected override double SoftAt => 270;
    protected override double HardAt => 360;

    /// <summary>Its blow (what its moves' multiples are of) as a share of her calling's own health at her level
    /// (Character.OwnHealth): what she is, not what she drafted or wears, which stay her margin. A story fight
    /// is the same fight for every calling and at every tier. Measured against the creature's own level, a
    /// lunge was 29% of a reaver's health and 47% of a stalker's: half the stalkers fell to Greymuzzle against
    /// one warden in eight.</summary>
    public abstract double Teeth { get; }

    /// <summary>Its ending has begun (the knee, the let-go, the hand): no move of its own now.</summary>
    public bool Ending { get; protected set; }

    /// <summary>What the space does each step while it lives (a ring that holds, frost that closes),
    /// whether or not it is moving: its moves are Act's, its ground is this.</summary>
    public virtual void Step(double dt) { }

    /// <summary>Everything it put on the ground goes (its end, or a rise at its opening).</summary>
    public virtual void Clear() { }

    /// <summary>What says it is here again after a rise (two seconds, not its arrival again).</summary>
    public abstract string ReEntry { get; }

    /// <summary>The bar's title: what it is doing to the space now, if anything.</summary>
    public virtual string? State => null;

    /* ------------------------------------------------- between its moves -- */

    /// <summary>How close she must be for it to break off round her, and how far either side of its head she
    /// must stand to be struck as she does.</summary>
    protected const double BreakOff = 4.5, CuffArc = 50 * Math.PI / 180;
    double cuffT;

    /// <summary>Between its moves a story boss circles her at its distance, watching her. Pressed close, it breaks
    /// off round her with its head where it is going, and strikes (a cuff, a nip, a shoulder: `mul` of its blow,
    /// every `every` s) only what stands across its path, or when it is cornered and turns on her. A blade at
    /// its flank or its back is not punished: its teeth are in its marked moves, not a brawl she cannot read.
    /// (Each struck whatever stood at it, and it was a blade build's worst wound: Greymuzzle's nip and Redcowl's
    /// shoulder each did as much as all their lunges or hooks.) `vx, vz` is where it goes; `dx, dz` toward her.</summary>
    protected void Cuff(Enemy e, double dt, double vx, double vz, double dx, double dz, double d, bool cornered, double mul, double every)
    {
        double vl = Math.Max(1e-6, Math.Sqrt(vx * vx + vz * vz));
        bool off = d < BreakOff && !cornered;
        e.Facing = off ? Math.Atan2(vz, vx) : Math.Atan2(dz, dx);
        bool ahead = !off || (vx * dx + vz * dz) / vl > Math.Cos(CuffArc);
        if ((cuffT -= dt) <= 0 && d < e.Radius + B.Player.Radius + 0.7 && ahead)
        {
            cuffT = every;
            B.HurtPlayer(e.Damage * mul, School.Physical, Who, e);
        }
    }
}
