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
/// <summary>A kit telegraph's moment (data/content/telegraphs.json): Warn as it is marked (Duration = its windup),
/// Land as it lands (Duration 0, Caught = she was in it). Draw only Warn; sound both (H3's bank: telegraph.&lt;tell&gt;.windup/.land).
/// Off: called off before it landed (a closing whose ring is all down): its mark fades, no sound.</summary>
public enum TellPhase { Warn, Land, Off }
/// <summary>Ev.BoardLamp's moments.</summary>
public enum BoardLampState { Lit, Dousing, Out, Relit }
public enum SpawnStyle { Rise, Burrow, Walk, Drop }
public enum Tone { Danger, Info, Boon, Story }
/// <summary>The Flare's moments (CLASSES.md §3.5): Ready (a charge full), Press (t = 0: the freeze, the grade, the push),
/// Release (the key pose ends: time returns, the camera eases back), Blow (each toll, cut, ember or pulse; carries its
/// hitstop), Kill (a blow of it, or anything while a Stand holds, killed a boss: the last blow's slow orbit), End.</summary>
public enum FlarePhase { Ready, Press, Blow, End, Release, Kill }
/// <summary>The pressed Warden skills' event phases (Ev.Leap, Ev.Charge, Ev.Spin, Ev.SpinLine).</summary>
public enum LeapPhase { Takeoff, Land }
public enum ChargePhase { Start, Impact, Stop, End, Slam }
public enum SpinPhase { Start, Tick, End, Break }
public enum SpinLinePhase { Thrown, Split, Faded }
/// <summary>Iron Vow's phases (Ev.Brace).</summary>
public enum BracePhase { Start, Store, Burst }

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
        /// <summary>Landed by the Flare (the view stages the Flare's own hits and deaths).</summary>
        public bool ByFlare;
    }

    /// <summary>A calling's Hand at work (HandKind); Target is the creature it touched, -1 for none.</summary>
    public sealed class Hand : CombatEvent { public HandKind Kind; public double X, Z; public int Target = -1; }

    /// <summary>Burst: the killing blow was far more than it had left (the body
    /// comes apart); Dx, Dz: which way it was going; Scale: its size.</summary>
    public sealed class Kill : CombatEvent
    {
        public double X, Z; public int Enemy; public string Def = ""; public Family Family; public School School;
        public bool Elite, Boss, ByPlayer, Burst, ByFlare; public double Dx, Dz, Scale = 1;
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
    /// <summary>She gained a barrier (Watch Bell's toll, Rebuke's Shield of Morning): where she stands, how much was added, and the skill's id.</summary>
    public sealed class Barrier : CombatEvent { public double X, Z, Amount; public string Source = ""; }
    public sealed class PlayerHeal : CombatEvent { public double Amount; }
    public sealed class PlayerDeath : CombatEvent { public double X, Z; public string Killer = ""; public int KillerId; }
    public sealed class Status : CombatEvent { public int Target; public StatusKind Kind; public double X, Z; }
    public sealed class Nova : CombatEvent { public double X, Z, Radius; public School School; public double Duration; public int? Rings; public string? Art; public int Rank; /** A flat ring on the ground only, no standing blast (a cinematic's ember going into the ground). */ public bool Plain; }
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
        /// <summary>The pattern inside a red mark, by name (MarkPass.PatternIds: a skill may name its own), and the blow's
        /// school (its pattern by school, godot/data/mark_look.json); none: by its shape.</summary>
        public string? Pattern; public School? School;
        /// <summary>The telegraph kit's kind (data/content/telegraphs.json: ring, charge, pull, closing); null = a mark
        /// outside the kit. Phase: Warn (marked) or Land (landed: nothing to draw).</summary>
        public string? Tell; public TellPhase Phase; public bool Caught;
        /// <summary>A closing's way out (H1 round 2B): the bearing (radians, atan2(z, x) from its center) of a gap GapWidth m
        /// wide along the band's middle where no foe of its ring stands, drawn lit. GapWidth 0: no gap.</summary>
        public double GapAngle, GapWidth;
    }

    public sealed class Spawn : CombatEvent { public int Enemy; public double X, Z; public string Def = ""; public SpawnStyle Style; }
    public sealed class Pickup : CombatEvent { public PickupKind Kind; public double Amount, X, Z; }
    /// <summary>Loot landed where the filter lets it be seen: Tier is Rpg.LootTier (its beam and its sound).</summary>
    public sealed class Drop : CombatEvent { public int Tier; public double X, Z; public bool Emphasised, Quiet; public PickupKind Kind; }
    public sealed class LevelUp : CombatEvent { public int Level; }
    /// <summary>(M3) Her calling taught a slot of its build (taught_builds.json) at a level reached in the campaign: the
    /// skill, the slot it went to (-1: carried by day but not in this fight), its cast form.</summary>
    public sealed class Taught : CombatEvent { public string Skill = "", Cast = ""; public int Slot = -1, Level; }
    /// <summary>A weapon evolved; out of a chest, the chest's opening shows it, not this.</summary>
    public sealed class Evolve : CombatEvent { public string Weapon = "", Into = ""; public bool Chest; }

    /// <summary>A wick lamp lit at night as the ember ranks the skill (Sim/Turns.cs); Turn: the lamp is its Turn.</summary>
    public sealed class Wick : CombatEvent { public string Skill = "", Lamp = ""; public bool Turn; }

    public sealed class Discovery : CombatEvent { public string Id = ""; }
    public sealed class Dash : CombatEvent { public double X0, Z0, X1, Z1; }
    /// <summary>A step of the dash's growth taken (Content/DashSteps.cs): the view announces it by its Id.</summary>
    public sealed class DashStep : CombatEvent { public string Id = ""; }
    /// <summary>Hard Landing: a dash ended and shoved the lesser things round her aside.</summary>
    public sealed class HardLanding : CombatEvent { public double X, Z, Radius; }
    /// <summary>A channelled skill (CastMode.Channel) began (On) or ended, on its slot.</summary>
    /// <summary>Resolve moved a whole point or more since the last told (Sim/Resolve.cs: M4's bar).</summary>
    public sealed class Resolve : CombatEvent { public double Value, Max, Delta; public ResolveReason Reason; }
    /// <summary>A campaign press went off (Battle.CastPose): her walk at Walk for Time seconds, her feet planted Plant
    /// seconds first (a heavy commit), aimed at (X, Z); Heavy, its own heavy swing.</summary>
    public sealed class Cast : CombatEvent { public string Weapon = ""; public int Slot; public double Walk, Time, Plant, X, Z; public bool Heavy; }
    /// <summary>A kindled skill's key pressed (Battle.KindledPress): what it did (now, riposte, flare, command) and until when.</summary>
    public sealed class KindlePress : CombatEvent { public string Weapon = ""; public int Slot; public Content.KindlePress Mode; public double Until; }
    public sealed class Channel : CombatEvent { public string Weapon = ""; public int Slot; public bool On; public double X, Z; }
    /// <summary>Heroic Leap (Sim/PressedWarden.cs). Takeoff: she leaves (X0, Z0) for (X1, Z1), Dur seconds in the air,
    /// and lands in a ring of Radius there (the view draws the ring at once: everything in it at landing is struck, and
    /// nothing outside). Land: she is down at (X1, Z1) and the ring strikes (Hit things struck; a heave and a shake
    /// come with it).</summary>
    public sealed class Leap : CombatEvent { public LeapPhase Phase; public double X0, Z0, X1, Z1, Dur, Radius; public int Hit; }
    /// <summary>Shield Charge (Sim/PressedWarden.cs). Start: from (X, Z) along (DX, DZ) to (X1, Z1) (where it would end
    /// unstopped), Dur seconds. Impact: Target struck and thrown aside at (X, Z). Stop: Target (a champion or boss) stopped
    /// her and is stunned. End: she is done at (X, Z). Slam: the Turn's slam, Radius round (X, Z).</summary>
    public sealed class Charge : CombatEvent { public ChargePhase Phase; public double X, Z, DX, DZ, X1, Z1, Dur, Radius; public int Target = -1; }
    /// <summary>Bladestorm's spin (Sim/PressedWarden.cs). Start, then a Tick each blow of the storm (Heavy: the Hand's or
    /// its own heavy count; a heavy tick throws a line), End (released or out of time: it may still be broken for a breath),
    /// Break (the second key: a heavy blow of Radius round her, the storm over; Grow: what the storm spent made of it, x1
    /// at half a second to x1.6 at its longest, on its damage and its Radius).</summary>
    public sealed class Spin : CombatEvent { public SpinPhase Phase; public double X, Z, Radius; public bool Heavy; public double Grow = 1; }
    /// <summary>A Sunder line Bladestorm threw (Id: the same line through its life): Thrown pending on the ground, Split at
    /// the break (it strikes all along it), Faded unbroken (it deals nothing).</summary>
    public sealed class SpinLine : CombatEvent { public SpinLinePhase Phase; public int Id; public double X0, Z0, X1, Z1, Width; }
    /// <summary>Iron Vow (Sim/PressedWarden.cs). Start: she plants at (X, Z) and braces (Radius: the ring it will burst in).
    /// Store: a blow on her in the brace, halved, a share kept (Stored: the store so far; at most one each 0.15 s). Burst: the
    /// brace is over and the store comes out in a ring of Radius round (X, Z) (Stored: the final store; Hit: how many it struck).</summary>
    public sealed class Brace : CombatEvent { public BracePhase Phase; public double X, Z, Radius, Stored; public int Hit; }
    /// <summary>She is knocked down (the kit's charge caught her, Battle.KnockPlayer): held for Seconds (after her tenacity).</summary>
    public sealed class Knockdown : CombatEvent
    {
        public double X, Z, Seconds;
        /// <summary>The lane that caught her (a charge's, from its foe to its end, its width; Width 0: none).</summary>
        public double FromX, FromZ, ToX, ToZ, Width;
    }
    /// <summary>A closing's band stands as a wall (Up) or falls (H6, Sim/Tells.cs): she cannot cross it outside its gap.
    /// Id is the band's mark (Ev.Telegraph.Id); the band runs Inner to Radius round (X, Z), its gap at GapAngle, GapWidth m wide.</summary>
    public sealed class ClosingWall : CombatEvent { public int Id; public double X, Z, Inner, Radius, GapAngle, GapWidth; public bool Up; }
    /// <summary>A telegraphed blow slipped at the last moment (Battle.PerfectDodge).</summary>
    public sealed class PerfectDodge : CombatEvent { public double X, Z; }
    /// <summary>A killing blow that did not end her (Battle.HurtPlayer): Ember, the ember's
    /// Cold, Then Not, burning everything within Radius; else the art Not Yet. Grace is how
    /// long she is untouchable after; Delay, how long after this its fire burns (the cold's beat).</summary>
    public sealed class Rise : CombatEvent { public double X, Z, Radius, Grace, Delay; public bool Ember; public int Rank; }
    /// <summary>An art used, or a moment of one. X1, Z1: its other end (a
    /// chain's bite, a step's landing, a drain's thread).</summary>
    public sealed class Ability : CombatEvent { public string Id = ""; public double X, Z, X1, Z1, Angle, Radius; public bool Wide; public int Who = -1; }
    /// <summary>A reflex fired itself (its art's own Ability event says what it did).</summary>
    public sealed class Reflex : CombatEvent { public string Art = ""; public double X, Z; }
    /// <summary>A link lamp fired its skill (Lamps v2, docs/design/LAMPS_V2_RULES.md "Links"): the lamp, the skill, where she stood.</summary>
    public sealed class Link : CombatEvent { public string Lamp = "", Skill = ""; public double X, Z; }
    /// <summary>The Flare (docs/design/CLASSES.md §3): Ready when the meter fills, Press at the cast (the
    /// shared beat's freeze and push begin here), Blow for each blow or pulse, End when it lets go.
    /// Clutch: cast below a quarter of health (it mends): a fall the Flare kept from happening, for
    /// whatever counts the survivor's rises (the toll, docs/story/TOLL_SPEC.md).</summary>
    /// <summary>A Flare's moment. Blow: Part names what landed ("toll", "blast", "frost", "ember", "cut", "execute", "pulse"),
    /// Last marks its final blow, TX/TZ where it landed (a cut's target, an ember's fall; her own place for a toll),
    /// Target the enemy struck (0 for none), Hitstop the frames the view holds (from the Flare's beat).</summary>
    public sealed class Flare : CombatEvent
    {
        public FlarePhase Phase; public string Id = ""; public double X, Z, Radius, Angle; public bool Clutch, Stand; public int Blow;
        public string Part = ""; public bool Last; public double TX, TZ; public int Target, Hitstop;
    }
    /// <summary>A board's lamp (H1 item 6B, Play/Zones/ArenaRun.Lamp.cs), for the sound (H3) and the view: its contract.
    /// State: Lit (it catches at its minute), Dousing (snuffers at it: once as it starts, then once a second while it
    /// goes on), Out (its life gone; its light off), Relit (she cupped the wick). Life: its life left, 0 to 1.</summary>
    public sealed class BoardLamp : CombatEvent { public double X, Z; public BoardLampState State; public double Life; }
    /// <summary>A speaker's line taken down now (Corvane's "Lie down." as its slam lands: the bark is the tell, not a caption).</summary>
    public sealed class Hush : CombatEvent { public string Speaker = ""; }
    public sealed class Bark : CombatEvent { public double X, Z; public string Text = ""; public string? Speaker;
        /// <summary>A boss's (IBossArena.Bark): shown in a fixed slot under the boss's bar, wherever the boss is.</summary>
        public bool Boss;
        /// <summary>A boss's signature line naming its own next mark (ArenaBoss.Signature): it keeps its slot over the speaker
        /// while that mark is live (not sent to the fight's band above the HUD), lifted a little clear of the mark's rim.</summary>
        public bool Signature; }
    public sealed class Announce : CombatEvent { public string Title = ""; public string? Subtitle, Kicker; public Tone? Tone; }
    public sealed class Shake : CombatEvent { public double Amount; }
    /// <summary>A story beat's cue for the set (the films lead's: "door_sigil" lights the door's sigil as Corvane's
    /// body gets up and goes): a name the set reads, nothing more.</summary>
    public sealed class Cue : CombatEvent { public string Id = ""; }
    /// <summary>A cut through black (a story beat's fallback for a film: Corvane's body taken away under it): the view
    /// fades to black over Seconds, holds it Hold seconds, and fades back over Seconds.</summary>
    public sealed class Fade : CombatEvent { public double Seconds = 0.25, Hold = 0.5; }
    /// <summary>The camera turned to something for a moment (a boss's arrival, its fall).</summary>
    public sealed class Focus : CombatEvent { public double X, Z, Duration; }
    /// <summary>What ruled the night has fallen where it stood: the night's peak (the view
    /// slows the world, turns to it and lets it land; the people break and run).</summary>
    public sealed class Victory : CombatEvent { public double X, Z; }
    /// <summary>The way out of a won night or cleared map is shown (with its banner): the one moment the
    /// player is told where to leave, so the sound is raised on it (SoundHooks "ui.way_out").</summary>
    public sealed class WayOutOpen : CombatEvent { public double X, Z; }
    /// <summary>A boss's phase broken: the damage past its mark, shown as one number.</summary>
    public sealed class Break : CombatEvent { public double X, Z, Amount; public int Enemy; }
    public sealed class Sound : CombatEvent { public string Id = ""; public double? X, Z, Volume; }
}

/// <summary>What a calling's Hand did (Sim/Hands.cs), for the view to show: a heavy blow landed, a Stone laid,
/// Frenzy gained, ground left, a projectile loosed with the extra pierce, a blow struck true, a mark passed.</summary>
public enum HandKind { Heavy, Stone, Frenzy, Ground, Pierce, True, Mark }

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
