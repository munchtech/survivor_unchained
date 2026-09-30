using System.Collections.Generic;

namespace SurvivorUnchained.Sim;

/* What the simulation tells the rest of the game each tick. The view turns
 * these into light and sound, the HUD into numbers, and the world layer
 * into history ("killed 40 wolves tonight", "was killed by X"). The
 * simulation never waits on a consumer; events are a one-way stream. */

public abstract class CombatEvent { }

public enum TelegraphShape { Circle, Line, Cone, Ring }
public enum SpawnStyle { Rise, Burrow, Walk, Drop }
public enum Tone { Danger, Info, Boon, Story }

public static class Ev
{
    public sealed class Hit : CombatEvent
    {
        public double X, Z, Amount; public bool Crit; public School School; public int Target;
        public bool Dot, Blocked; public Family? Family; public string? Def; public double MaxHp, Dx, Dz;
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
    }

    /// <summary>A ward took the blow (or some of it); Broke: and is gone.</summary>
    public sealed class ShieldHit : CombatEvent { public double X, Z, Absorbed; public bool Broke; }
    public sealed class PlayerHeal : CombatEvent { public double Amount; }
    public sealed class PlayerDeath : CombatEvent { public double X, Z; public string Killer = ""; public int KillerId; }
    public sealed class Status : CombatEvent { public int Target; public StatusKind Kind; public double X, Z; }
    public sealed class Nova : CombatEvent { public double X, Z, Radius; public School School; public double Duration; public int? Rings; }
    public sealed class Explosion : CombatEvent { public double X, Z, Radius; public School School; public double Power; }
    public sealed class Chain : CombatEvent { public double[] Points = System.Array.Empty<double>(); public School School; }
    public sealed class Beam : CombatEvent { public double X0, Z0, X1, Z1, Width; public School School; public double Duration; }
    public sealed class Strike : CombatEvent { public double X, Z, Radius; public School School; public double Delay; }
    public sealed class Slash : CombatEvent { public double X, Z, Angle, Arc, Reach; public School School; }
    public sealed class Muzzle : CombatEvent { public double X, Z, Angle; public School School; public string Weapon = ""; }

    public sealed class Telegraph : CombatEvent
    {
        public int Id; public TelegraphShape Shape; public double X, Z; public double? X1, Z1; public double Radius;
        public double? Width, Angle, Arc; public double Duration; public bool Hostile;
    }

    public sealed class Spawn : CombatEvent { public int Enemy; public double X, Z; public string Def = ""; public SpawnStyle Style; }
    public sealed class Pickup : CombatEvent { public PickupKind Kind; public double Amount, X, Z; }
    public sealed class LevelUp : CombatEvent { public int Level; }
    public sealed class Evolve : CombatEvent { public string Weapon = "", Into = ""; }
    public sealed class Discovery : CombatEvent { public string Id = ""; }
    public sealed class Dash : CombatEvent { public double X0, Z0, X1, Z1; }
    /// <summary>A telegraphed blow slipped at the last moment (Battle.PerfectDodge).</summary>
    public sealed class PerfectDodge : CombatEvent { public double X, Z; }
    public sealed class Ability : CombatEvent { public string Id = ""; public double X, Z, Angle, Radius; }
    public sealed class Bark : CombatEvent { public double X, Z; public string Text = ""; public string? Speaker; }
    public sealed class Announce : CombatEvent { public string Title = ""; public string? Subtitle, Kicker; public Tone? Tone; }
    public sealed class Shake : CombatEvent { public double Amount; }
    public sealed class Sound : CombatEvent { public string Id = ""; public double? X, Z, Volume; }
}

public sealed class EventStream
{
    readonly List<CombatEvent> events = new();
    public IReadOnlyList<CombatEvent> Pending => events;
    public void Emit(CombatEvent e) => events.Add(e);

    public List<CombatEvent> Drain()
    {
        var o = new List<CombatEvent>(events);
        events.Clear();
        return o;
    }
}
