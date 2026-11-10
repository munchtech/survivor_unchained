using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* The arsenal. Every weapon fires on its own; what the survivor does is
 * choose them, rank them and decide what they become.
 *
 *   - Tags and a school on everything, so gear and boons can say "your
 *     projectiles" or "your fire" and mean it.
 *   - Evolution BRANCHES. A rank-8 weapon does not have one destiny; it
 *     becomes whatever the rest of the build pulls it toward. Each branch
 *     names the passive skill that evolves it (a rank of it is enough), and
 *     a weapon with both passives asks which it should become.
 *
 * The skills themselves are data (data/content/skills.json, read by
 * SkillsJson); these are their types and the rank rules.
 *
 * Rank growth (applied by the runtime): +20% damage per rank, +4% area per
 * rank, +6% duration per rank, one more projectile at ranks 4 and 7. */

/// <summary>How a skill fires (Sim/Weapons.cs Firing.Fire). Appended only: older keys keep their places.</summary>
public enum WeaponBehavior { Aimed, Spray, Ring, Nova, Zone, Chain, Orbit, Storm, Bounce, Beam, Palm, Herd, Chakram, Slash, Raise, Crack, Reactive, Toll, Leap, Charge, Spin, Brace }

/// <summary>How a skill is set off (skills.json "cast"): by itself on its cooldown (auto, every skill so far),
/// once on a press when ready (press), or from a press for as long as it is held, to its ChannelTime, its cooldown
/// starting when it ends (channel). Sim/Weapons.cs Firing.Tick and Battle.PressSkill / HoldSkill run them.</summary>
public enum CastMode { Auto, Press, Channel }

/// <summary>A weapon's numbers; unset ones fall back (in an evolution's Set,
/// to the base).</summary>
public sealed class WeaponStats
{
    public double? Cooldown, Damage, Speed, Pierce, Range, Radius, Life, Homing, Splash, Spread, Duration, TickRate;
    public double? Chains, ChainRange, Bounces, OrbitRadius, OrbitSpeed, Strikes, StormRadius, BeamWidth, Reach, Arc;
    public double? Knockback, ExpandTime, Heal, Slow;
    public int? Projectiles;
    public bool? AtTarget;
    public StatusPayload? Status;
    /// <summary>A burst of shots in quick succession instead of all at once.</summary>
    public bool? Burst;
    /// <summary>Also leaves burning / hallowed / blighted ground where it hits.</summary>
    public GroundSpec? GroundOnHit;
    /// <summary>Projectiles split into smaller ones on hit.</summary>
    public int? SplitOnHit;
    /// <summary>Chains fork into two at each jump.</summary>
    public bool? Fork;
    /// <summary>What its projectiles hunt, if not the nearest.</summary>
    public Seek? Seek;
    /// <summary>Critical strike chance its blows have on top of the survivor's.</summary>
    public double? Crit;
    /// <summary>What a raising weapon calls up (an ally's kind).</summary>
    public string? Raises;
    /// <summary>Its own count: every this many firings is heavy (the warden's Hand's heavy blow, whatever the Hand
    /// counts), and a heavy one strikes its Line too (Sunder's). Absent, only the Hand makes it heavy.</summary>
    public double? HeavyEvery;
    /// <summary>A heavy firing also strikes a line this long straight ahead, BeamWidth wide, at its full damage.</summary>
    public double? Line;
    /// <summary>A crack's path (Crack): the share of its damage what lies along it takes.</summary>
    public double? Trail;
    /// <summary>Seconds a blow stuns what it strikes (not a boss): Groundbreaker's heave.</summary>
    public double? Stun;
    /// <summary>Reactive (Rebuke): carried, her block chance at rank 1, and more a rank after.</summary>
    public double? Block, BlockStep;
    /// <summary>Reactive: how many creatures it strikes beside the blocker (the nearest it, within Radius).</summary>
    public double? Others;
    /// <summary>Reactive: seconds before the same champion (elite or boss) is struck again. A champion pinning her
    /// struck her every half second and stood beside her for every other blow: at one strike a cooldown Rebuke dealt
    /// a champion 2,369 a second, three times the rest of the dawn build together (the path probe, P6); every 5 s at
    /// bossDamage 0.5, 246 (Dawnpulse 146, the wall 201). The crowd's numbers are untouched.</summary>
    public double? ChampionGap;
    /// <summary>Toll (Watch Bell): the barrier, a share of max health, for each thing drawn; at most DrawMost of them count.</summary>
    public double? Barrier, DrawMost;
    /// <summary>Toll: the bell tops her barrier up to this share of max health and no further.</summary>
    public double? BarrierCap;
    /// <summary>A channel's longest hold in seconds (CastMode.Channel; 3 if unset), and the seconds between its
    /// firings while held (its TickRate, else 0.4).</summary>
    public double? ChannelTime, ChannelGap;
    /// <summary>Leap (Heroic Leap): seconds in the air (untouchable), and the shortest jump (an aim nearer lands this far
    /// along it). Its Range is the longest, its Radius the ring it lands in, its Stun what a lesser foe is knocked down
    /// for, Stagger the shorter stun a champion takes.</summary>
    public double? Air, MinRange, Stagger;
    /// <summary>Charge (Shield Charge): seconds the run takes (Range metres); Barrier her barrier's share of max health,
    /// held Duration seconds; Stun the champion or boss that stops her. Slam: the evolution's end-slam, times the damage.</summary>
    public double? RushTime, Slam;
    /// <summary>Spin (Bladestorm): her pace while it spins (a share), the line a heavy tick throws (Line long, BeamWidth
    /// wide) held pending, at most MaxLines; the break (its second key) a heavy blow of BreakRadius for BreakDamage,
    /// stunning BreakStun and throwing BreakKnockback, each pending line splitting for LineDamage; BreakWindow seconds after
    /// the spin ends it may still be broken. The damages are base numbers, grown with the skill's rank as its Damage is.</summary>
    public double? Pace, MaxLines, LineDamage, BreakDamage, BreakRadius, BreakStun, BreakKnockback, BreakWindow;
    /// <summary>Spin: the break grows with the storm she spent, from x1 at BreakFrom seconds to BreakGrow at its longest
    /// (ChannelTime), linearly, on its damage and its radius.</summary>
    public double? BreakFrom, BreakGrow;
    /// <summary>Spin, in the campaign with Resolve: the break grows with the Resolve the storm spent instead, x1 at none to
    /// BreakGrow at BreakSpent (100), linearly.</summary>
    public double? BreakSpent;
    /// <summary>Brace (Iron Vow): she plants Plant seconds (no walking), then braces Brace seconds; blows on her while it
    /// holds land at Halve, and Store of each (before the halving) is stored; it ends in a burst of Radius for Damage plus
    /// the store times StoreMul, Knockback outward, a lesser foe stunned Stun seconds.</summary>
    public double? Brace, Plant, Store, StoreMul, Halve;
}

/// <summary>Multiplicative on damage, cooldown, area, speed, duration; additive on counts.</summary>
public sealed class EvoMods
{
    public double? Damage, Cooldown, Area, Speed, Duration;
    public int? Projectiles, Pierce, Bounces, Chains, Strikes;
}

/// <summary>When a kindled (auto) skill fires itself, beside its wait being over (skills.json "kindle"). `when` is
/// windup (a telegraphed blow or an enemy windup lands on her or within `radius` m within `within` s; a brute's or elite's
/// only when `big`), crowd (`count` hostiles within `radius` m), hurt (her life below `below`, a share) or block (she
/// blocked in the last 0.2 s); or `any` lists several, the first that holds. Sim/Kindle.cs reads it.</summary>
public sealed class KindleDef
{
    public string? When;
    public bool? Big;
    public double? Radius, Within, Below;
    public int? Count;
    public KindleDef[]? Any;
}

/// <summary>The ARPG press record (skills.json "press"; ARPG.md 3.1): how a skill is set off in the campaign
/// (Battle.Campaign; the arena keeps "cast"/"kindle" and never reads this). Every field optional:
///   kind: hold (fires whenever ready while its key is held: the grips), press (once a press; the default), channel
///     (runs while held), kindle (fires itself on its kindle condition; its key does `kindled.press`);
///   kindled: the kindled OPTION (a slot may run the skill in either form, WeaponInst.SetForm): its condition (KindleDef
///     fields; none, the skill's own "kindle") and what its key does then (now | riposte | flare | command);
///   aim: hover (the foe nearest the aim point within 1.5 m of it and within reach; else the point clamped to reach; the
///     default), point (the point clamped to reach), self; reach (m; absent, the skill's range/reach); pad: stick | facing (M4);
///   walk: her pace while the cast plays (0.7), castTime (s, 0.35), plant (s she stands, at most 0.3: the heavy commits);
///   wait: its cooldown in the campaign (absent: its base cooldown; a spender whose calling has no resource to pay
///     keeps its base cooldown and channel cap, since its wait assumed the cost as the limit);
///   resolve: Resolve a press costs (spenders); drain: Resolve a second while it channels (Bladestorm);
///   builds: Resolve a landed swing gives (it struck at least one foe), plus buildsEach for each foe past the first (at
///     most buildsMost), times heavyMul on a heavy swing (Sim/Resolve.cs).</summary>
public sealed class PressDef
{
    public PressKind? Kind;
    public PressKindled? Kindled;
    public PressAim? Aim;
    public double? Reach;
    public PadAim? Pad;
    public double? Walk, CastTime, Plant, Wait, Resolve, Drain, Builds, BuildsEach, BuildsMost, HeavyMul;
    /// <summary>Her clips for a press of it (M3, campaign): `clip` alternated swing to swing, `clipHeavy` for a heavy blow,
    /// each played at its rate (clipRate, clipHeavyRate; absent: 1.6 and 1.5, the view's old pace). The blow's hits land on
    /// the clip's contact frame (data/anim/her_events.json, Content/HerEvents.cs) after the press; the view plays the
    /// same clip at the same rate from the press (AttackAnim.Clip). Absent: the blow lands at the press, as before.</summary>
    public string[]? Clip;
    public string? ClipHeavy;
    public double? ClipRate, ClipHeavyRate;
    /// <summary>The held swing as a chain (M3 MR 3, campaign; Sim/SwingChain.cs): absent, every press is its own swing, as
    /// before. Present, its cuts are one chain: each cut's clip fills the cut's period (the skill's wait), the blow lands
    /// on the clip's contact beat, sides alternate, and she recovers only on release.</summary>
    public ChainDef? Chain;

    /// <summary>This record with another chain block (a copy: the skill's own record is shared data).</summary>
    public PressDef WithChain(ChainDef? chain) { var r = (PressDef)MemberwiseClone(); r.Chain = chain; return r; }
}

/// <summary>A chain's own numbers (skills.json press "chain"): grace, the seconds the chain's index and side live after
/// a release (0.40); recover, the release recover's length in frames at 60 fps (18), told on Ev.SwingRelease; period,
/// the cut's seconds (absent, the skill's own wait: each cut is a whole blow). With a period a cut is a SHARE of the
/// written blow, period over the skill's wait (WeaponInst.BlowWeight): per second nothing changes.</summary>
public sealed class ChainDef
{
    public double? Grace, Recover, Period;
}

/// <summary>A skill's kindled option (PressDef.Kindled): the condition (KindleDef's fields; none set, the skill's own
/// "kindle", else its wait alone) and its key's live press.</summary>
public sealed class PressKindled
{
    public string? When;
    public bool? Big;
    public double? Radius, Within, Below;
    public int? Count;
    public KindleDef[]? Any;
    public KindlePress? Press;
    /// <summary>Its key's own wait in the kindled form (riposte, flare, command; absent: the skill's base cooldown).</summary>
    public double? Wait;

    /// <summary>The condition as a KindleDef, or null when it names none.</summary>
    public KindleDef? Condition() => When == null && Any is not { Length: > 0 } ? null
        : new KindleDef { When = When, Big = Big, Radius = Radius, Within = Within, Below = Below, Count = Count, Any = Any };
}

public enum PressKind { Press, Hold, Channel, Kindle }
public enum PressAim { Hover, Point, Self }
public enum PadAim { Stick, Facing }
/// <summary>A kindled skill's key: fire now (its condition skipped), ready a riposte (2 s), flare an aura (3 s), command a summon.</summary>
public enum KindlePress { Now, Riposte, Flare, Command }

public sealed class Evolution
{
    public string Id = "", Name = "", Description = "";
    /// <summary>The passive skills that evolve it: at rank 8 with a rank in any.</summary>
    public string[] Catalysts = System.Array.Empty<string>();
    public EvoMods Mods = new();
    public WeaponStats? Set;
    public WeaponBehavior? Behavior;
    public School? School;
    public Tag[]? AddTags;
    public string? Art;
    /// <summary>How it is set off, if not as its skill is.</summary>
    public CastMode? Cast;
    /// <summary>Its kindle condition, if it has its own (else its skill's).</summary>
    public KindleDef? Kindle;
    /// <summary>Rules it adds to the fight, the weapon's own (what it does
    /// beyond numbers: an execute, a bolt from the sky, a raised dead).</summary>
    public TriggerDef[] Triggers = System.Array.Empty<TriggerDef>();
}

public sealed class WeaponDef
{
    public string Id = "", Name = "";
    public School School;
    public WeaponBehavior Behavior;
    /// <summary>How it is set off: by itself (auto, the default), on a press, or held as a channel.</summary>
    public CastMode Cast;
    /// <summary>An auto skill fires itself only when this holds too (absent: on its wait alone).</summary>
    public KindleDef? Kindle;
    /// <summary>How it is set off in the campaign (ARPG.md 3.1): null, as "cast" says everywhere.</summary>
    public PressDef? Press;
    public Tag[] Tags = System.Array.Empty<Tag>();
    /// <summary>The callings that may carry it (a kindred pair); absent, everyone
    /// (the valley's). A union's is never set: it is its parts' in common.</summary>
    public string[]? Access;
    public WeaponStats Base = new();
    public string Art = "";
    /// <summary>Bosses and elites: crowd weapons hit one big target softly.</summary>
    public double? BossDamage;
    public string Description = "";
    /// <summary>A note for whoever tunes it (skills.json "_doc"): never read by the game, kept by the round trip.</summary>
    [System.Text.Json.Serialization.JsonPropertyName("_doc")]
    public string Doc = "";
    public Evolution[] Evolutions = System.Array.Empty<Evolution>();
    /// <summary>Offered in the level-up pool (and so discoverable, and learnable by day).</summary>
    public bool Findable;
    /// <summary>Damage each rank adds (of the base). A single bolt grows more
    /// with its ranks than a field that already strikes a crowd does.</summary>
    public double Growth = Weapons.DamageStep;
    /// <summary>Rules it brings into the fight while carried (a union's own).</summary>
    public TriggerDef[] Triggers = System.Array.Empty<TriggerDef>();
}

public static class Weapons
{
    public const int MaxRank = 8;
    /// <summary>Skill slots (keys 1-6), not weapons: a union holds two (SlotCost).</summary>
    public const int MaxWeapons = 6;
    public const double DamageStep = 0.2, AreaStep = 0.04, DurationStep = 0.06;
    public const int ProjRankA = 4, ProjRankB = 7;

    /// <summary>Every combat skill, by id, in the order data/content/skills.json
    /// lists them (the draft's pool keeps that order).</summary>
    public static readonly Dictionary<string, WeaponDef> All = SkillsJson.File.Skills.ToDictionary(w => w.Id);

    /// <summary>The weapons the level-up draft can offer.</summary>
    public static readonly string[] Pool = All.Values.Where(w => w.Findable).Select(w => w.Id).ToArray();

    /* Which skill an evolution belongs to: it is carried by whoever may carry its skill. */
    static readonly Dictionary<string, string> EvolutionOf = All.Values
        .SelectMany(w => w.Evolutions.Select(e => (e.Id, w.Id))).ToDictionary(p => p.Item1, p => p.Item2);

    /// <summary>The callings that may carry a skill, an evolution or a union (null:
    /// everyone). A union's is the intersection of its two parts', computed so
    /// it can never drift from them.</summary>
    public static IReadOnlyCollection<string>? AccessOf(string id)
    {
        if (Unions.All.FirstOrDefault(u => u.Id == id || u.Into == id) is { } un)
        {
            var a = AccessOf(un.A);
            var b = AccessOf(un.B);
            return a == null ? b : b == null ? a : a.Intersect(b).ToArray();
        }
        if (!All.TryGetValue(id, out var d) && EvolutionOf.TryGetValue(id, out var parent)) d = All[parent];
        return d?.Access is { Length: > 0 } acc ? acc : null;
    }

    /// <summary>May this calling carry the skill (or evolution, or union)? The one
    /// truth every draft, lesson, tome and piece of gear asks. No calling (a bare
    /// test battle) carries anything.</summary>
    public static bool CanCarry(string? calling, string id) =>
        string.IsNullOrEmpty(calling) || AccessOf(id) is not { } acc || acc.Contains(calling);

    /// <summary>A union's weapon (some UnionDef's Into): it holds both its parts' slots.</summary>
    public static bool IsUnion(string id) => Unions.All.Any(u => u.Into == id);

    /// <summary>The skill slots a weapon takes: two for a union (the owner, 8 Nov: "unions are 2 skills combined but
    /// still take up both skill slots"), one otherwise. MaxWeapons counts slots, not weapons.</summary>
    public static int SlotCost(string id) => IsUnion(id) ? 2 : 1;

    /// <summary>The slots a list of weapons takes.</summary>
    public static int SlotsOf(IEnumerable<string> ids) => ids.Sum(SlotCost);

    public static WeaponDef Get(string id) => All.TryGetValue(id, out var d) ? d : throw new KeyNotFoundException($"unknown weapon {id}");
}
