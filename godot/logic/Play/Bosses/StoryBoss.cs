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
}
