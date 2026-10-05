using System.Collections.Generic;

namespace SurvivorUnchained.Sim;

/* What the simulation tells the rest of the game each tick. The view turns
 * these into light and sound, the HUD into numbers, and the world layer
 * into history ("killed 40 wolves tonight", "was killed by X"). The
 * simulation never waits on a consumer; events are a one-way stream. */

public abstract class CombatEvent { }

public enum TelegraphShape { Circle, Line, Cone, Ring }

/// <summary>What a telegraph says (docs/bosses/MECHANICS.md section 2), in colour and
/// edge both: a blow is coming here (amber, filled), this ground stays bad
/// (violet, hatched), stand here (pale blue, dashed), this will be solid (grey,
/// a hard edge).</summary>
public enum TelegraphKind { Blow, Ground, Safe, Wall }
public enum SpawnStyle { Rise, Burrow, Walk, Drop }
public enum Tone { Danger, Info, Boon, Story }

public static class Ev
{
    /* Art and Rank on the survivor's own blows say which skill made them and
     * how far it has been ranked, so the view can draw each skill its own way
     * and grow it as it ranks up (the view only; nothing here reads them). */

    public sealed class Hit : CombatEvent
    {
        public double X, Z, Amount; public bool Crit; public School School; public int Target;
        public bool Dot, Blocked; public Family? Family; public string? Def; public double MaxHp, Dx, Dz;
        public string? Art; public int Rank;
    }

    /// <summary>Burst: the killing blow was far more than it had left (the body
    /// comes apart); Dx, Dz: which way it was going; Scale: its size.</summary>
    public sealed class Kill : CombatEvent
    {
        public double X, Z; public int Enemy; public string Def = ""; public Family Family; public School School;
        public bool Elite, Boss, ByPlayer, Burst; public double Dx, Dz, Scale = 1;
    }

    public sealed class PlayerHit : CombatEvent
    {
        public double X, Z, Amount; public School School; public string Source = ""; public bool Dodged, Blocked;
        /// <summary>The marked blow that landed, by its label (a boss's Lunge, the Pack's turn), if it was one.</summary>
        public string? Label;
        /// <summary>Damage over time (poison, burning), said once a second: quieter than a blow.</summary>
        public bool Dot;
    }

    /// <summary>A ward took the blow (or some of it); Broke: and is gone.</summary>
    public sealed class ShieldHit : CombatEvent { public double X, Z, Absorbed; public bool Broke; }
    public sealed class PlayerHeal : CombatEvent { public double Amount; }
    public sealed class PlayerDeath : CombatEvent { public double X, Z; public string Killer = ""; public int KillerId; }
    public sealed class Status : CombatEvent { public int Target; public StatusKind Kind; public double X, Z; }
    public sealed class Nova : CombatEvent { public double X, Z, Radius; public School School; public double Duration; public int? Rings; public string? Art; public int Rank; }
    public sealed class Explosion : CombatEvent { public double X, Z, Radius; public School School; public double Power; public string? Art; public int Rank; }
    public sealed class Chain : CombatEvent { public double[] Points = System.Array.Empty<double>(); public School School; public string? Art; public int Rank; }
    public sealed class Beam : CombatEvent { public double X0, Z0, X1, Z1, Width; public School School; public double Duration; public string? Art; public int Rank; }
    public sealed class Strike : CombatEvent { public double X, Z, Radius; public School School; public double Delay; public string? Art; public int Rank; }
    public sealed class Slash : CombatEvent { public double X, Z, Angle, Arc, Reach; public School School; public string? Art; public int Rank; }
    public sealed class Muzzle : CombatEvent { public double X, Z, Angle; public School School; public string Weapon = ""; public string? Art; public int Rank; }

    public sealed class Telegraph : CombatEvent
    {
        public int Id; public TelegraphShape Shape; public double X, Z; public double? X1, Z1; public double Radius;
        public double? Width, Angle, Arc; public double Duration; public bool Hostile;
        public TelegraphKind Kind;
        /// <summary>A ring's inner edge (a band, not a disc).</summary>
        public double Inner;
        /// <summary>A boss's: drawn above the survivor's own effects, and named over the boss.</summary>
        public bool Boss; public string? Label;
        /// <summary>Who marked it, where it stood (its name is said over it, not over the survivor).</summary>
        public double? ByX, ByZ;
        /// <summary>The people whose mark it is (a rally's ring in its colour, a call, a slam).</summary>
        public Faction? Faction;
    }

    public sealed class Spawn : CombatEvent { public int Enemy; public double X, Z; public string Def = ""; public SpawnStyle Style; }
    public sealed class Pickup : CombatEvent { public PickupKind Kind; public double Amount, X, Z; }
    public sealed class LevelUp : CombatEvent { public int Level; }
    /// <summary>A weapon evolved; out of a chest, the chest's opening shows it, not this.</summary>
    public sealed class Evolve : CombatEvent { public string Weapon = "", Into = ""; public bool Chest; }
    public sealed class Discovery : CombatEvent { public string Id = ""; }
    public sealed class Dash : CombatEvent { public double X0, Z0, X1, Z1; }
    /// <summary>A telegraphed blow slipped at the last moment (Battle.PerfectDodge).</summary>
    public sealed class PerfectDodge : CombatEvent { public double X, Z; }
    /// <summary>A killing blow that did not end her (Battle.HurtPlayer): Ember, the ember's
    /// Cold, Then Not, burning everything within Radius; else the art Not Yet. Grace is how
    /// long she is untouchable after; Delay, how long after this its fire burns (the cold's beat).</summary>
    public sealed class Rise : CombatEvent { public double X, Z, Radius, Grace, Delay; public bool Ember; public int Rank; }
    /// <summary>An art used, or a moment of one. X1, Z1: its other end (a
    /// chain's bite, a step's landing, a drain's thread).</summary>
    public sealed class Ability : CombatEvent { public string Id = ""; public double X, Z, X1, Z1, Angle, Radius; public bool Wide; public int Who = -1; }
    public sealed class Bark : CombatEvent { public double X, Z; public string Text = ""; public string? Speaker; }
    public sealed class Announce : CombatEvent { public string Title = ""; public string? Subtitle, Kicker; public Tone? Tone; }
    public sealed class Shake : CombatEvent { public double Amount; }
    /// <summary>The camera turned to something for a moment (a boss's arrival, its fall).</summary>
    public sealed class Focus : CombatEvent { public double X, Z, Duration; }
    /// <summary>What ruled the night has fallen where it stood: the night's peak (the view
    /// slows the world, turns to it and lets it land; the people break and run).</summary>
    public sealed class Victory : CombatEvent { public double X, Z; }
    /// <summary>A boss's phase broken: the damage past its mark, shown as one number.</summary>
    public sealed class Break : CombatEvent { public double X, Z, Amount; public int Enemy; }
    public sealed class Sound : CombatEvent { public string Id = ""; public double? X, Z, Volume; }
}

public sealed class EventStream
{
    readonly List<CombatEvent> events = new();
    public IReadOnlyList<CombatEvent> Pending => events;
    public void Emit(CombatEvent e) => events.Add(e);
    /// <summary>Unsay what was emitted after a mark (a build replayed at a checkpoint is not news).</summary>
    public void Since(int mark) { if (mark < events.Count) events.RemoveRange(mark, events.Count - mark); }

    public List<CombatEvent> Drain()
    {
        var o = new List<CombatEvent>(events);
        events.Clear();
        return o;
    }
}
