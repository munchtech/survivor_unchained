using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Bosses;

/// <summary>What a boss script may ask of the arena it fights in.</summary>
public interface IBossArena
{
    Battle B { get; }
    int Tier { get; }
    /// <summary>Who it is here (the Pack's ruler is Greymuzzle in his Hollow, the Pack-Mother at the table).</summary>
    string BossName { get; }
    /// <summary>The story lets it go at the end rather than die.</summary>
    bool Spare { get; }
    bool Sworn(string oath);
    double R();
    Enemy? Spawn(string def, double x, double z, bool elite = false, SpawnStyle? style = null);
    bool CanStand(double x, double z);
    void Say(string title, string? sub, string tone);
    void Bark(double x, double z, string text, string? speaker = null);
    /// <summary>The share of its number the horde is kept at while the boss lives.</summary>
    double HordeShare { set; }
    /// <summary>The horde comes back when the boss grows wild (the table's); a map or a story night keeps it off,
    /// so the words must not promise it.</summary>
    bool HordeReturns => true;
    /// <summary>The fight is won (Grimtunnel goes back down rather than dying).</summary>
    void Won(double x, double z);
}

/// <summary>
/// The contract every arena boss keeps (docs/bosses/SURVIVORS_BOSSES.md section 0;
/// docs/SKILLS_DESIGN.md, "Bosses"):
///
///   - phases are gates: each ends at its health mark or its time ceiling,
///     never before its floor; damage past the mark is the Break, shown as one
///     number when the phase turns, and a short stagger is the transition;
///     marks crossed together queue (health stops at the current mark);
///   - a soft enrage at three minutes (its moves come a quarter faster, the
///     horde back to its full number) and a hard one at five (its signature
///     move on a loop): escalate, never execute;
///   - a boss is never locked or executed: what would lock it fills its
///     stagger bar (Battle.AddStagger);
///   - a weakness, named when the arena opens: one hit of its school breaks
///     its channel.
///
/// A script moves the boss only while a move is running (Act returns true);
/// between moves the creature's own behaviour carries it.
/// </summary>
public abstract class ArenaBoss
{
    public sealed record Phase(string Name, double Mark, double Floor, double Ceiling);

    protected readonly IBossArena A;
    protected Battle B => A.B;
    public Enemy E { get; private set; } = null!;
    protected abstract Phase[] Phases { get; }
    /// <summary>Its weakness: the school that breaks its channel.</summary>
    public abstract School Weakness { get; }
    /// <summary>What the arena's opening card and the bestiary say of it.</summary>
    public abstract string WeaknessText { get; }

    public int PhaseIx { get; private set; }
    public double PhaseT { get; private set; }
    public double FightT { get; private set; }
    public double BreakSum { get; private set; }
    public double TransitionT { get; private set; }
    public bool Soft { get; private set; }
    public bool Hard { get; private set; }
    /// <summary>A channel the bar shows ("The moon-howl: break it!"), and how far along.</summary>
    public string? Channel;
    public double ChannelProgress;
    /// <summary>Blows the survivor took from the boss's telegraphed moves (an unscathed fight pays).</summary>
    public int TelegraphedTaken;
    /// <summary>Its last move: health held at 1 (Grimtunnel goes down the hole, the Barrow Lord must be laid down).</summary>
    protected virtual bool DiesAtZero => true;

    protected ArenaBoss(IBossArena arena) => A = arena;

    /// <summary>Its health over its people's champion's: set so a par build takes a minute and a half.</summary>
    public virtual double HealthMul(int tier) => 12 + 2 * tier;
    public virtual double DamageMul => 1.3;

    /// <summary>Its health as it came (the creature it was is pooled: once it is gone the
    /// same body is soon a wolf, and its numbers are the wolf's).</summary>
    public double MaxHp { get; private set; }

    /* The oaths on the boss (docs/bosses/SURVIVORS_BOSSES.md 0.12; SKILLS_DESIGN 16.8): one visible
     * change each, in the direction it changes the horde, said on its card. The deep dark's levels,
     * the hunt's pace, the swarm's adds and the champions' lieutenant come from the arena; these
     * are the boss's own. */
    bool winter, embers, blight, ruin;
    double blightT;

    /// <summary>What the oaths sworn do to it, for its card ("its heavy blows chill").</summary>
    public string Sworn()
    {
        var o = new List<string>();
        if (A.Sworn("winter")) o.Add("its heavy blows chill");
        if (A.Sworn("embers")) o.Add("its blows leave fire");
        if (A.Sworn("blight")) o.Add("it leaves blight where it walks");
        if (A.Sworn("ruin")) o.Add("it bursts as each phase turns");
        if (A.Sworn("vigil")) o.Add("its phases come quicker");
        if (A.Sworn("iron")) o.Add("it staggers slower");
        return string.Join(", ", o);
    }

    public void Begin(Enemy e)
    {
        E = e;
        MaxHp = e.MaxHp;
        winter = A.Sworn("winter"); embers = A.Sworn("embers"); blight = A.Sworn("blight"); ruin = A.Sworn("ruin");
        // The long vigil: its floors a third shorter and its moves a fifth quicker.
        if (A.Sworn("vigil")) { FloorScale *= 2 / 3.0; cadenceMul = 0.8; }
        PhaseIx = 0;
        PhaseT = 0;
        e.HpFloor = Phases[0].Mark * e.MaxHp;
        Enter(0);
    }

    double cadenceMul = 1;
    protected double Cadence => (Soft ? 0.75 : 1) * cadenceMul;
    protected Phase Current => Phases[PhaseIx];
    protected bool Last => PhaseIx == Phases.Length - 1;
    /// <summary>Brought to its end (held at one) and past the last phase's floor: a boss that ends
    /// otherwise than dying starts its end only now, or a strong build skipped the last floor
    /// (the Barrow Lord was laid down in about 35 s).</summary>
    protected bool Spent(Enemy e) => Last && e.Hp <= 1.5 && PhaseT >= Current.Floor * FloorScale;
    /// <summary>The floors over the night's: a map is ten minutes, not thirty, so its ruler's
    /// gates are shorter there (docs/SKILLS_DESIGN.md §17.3).</summary>
    public double FloorScale = 1;

    /// <summary>The boss's tick: the gate, the enrages, then its moves.</summary>
    public bool Tick(Enemy e, double dt)
    {
        if (e != E) return false;
        FightT += dt;
        if (TransitionT > 0)
        {
            TransitionT -= dt;
            e.TakenMul = 0;
            e.Vx = e.Vz = 0;
            e.State = EnemyState.Active;
            if (TransitionT <= 0) { e.TakenMul = 1; PhaseT = 0; Enter(PhaseIx); }
            return true;
        }
        PhaseT += dt;
        // The blight: where it walks the ground goes bad for a while behind it.
        if (blight && (blightT -= dt) <= 0 && Math.Abs(e.Vx) + Math.Abs(e.Vz) > 0.5)
        {
            blightT = 0.5;
            var z = B.SpawnZone(Side.Enemy, e.X, e.Z, 1.4, 2, e.Damage * 0.1, School.Nature);
            if (z != null) z.Tags = [Tag.Zone, Tag.Nature];
        }
        var ph = Current;
        if (!Last)
        {
            e.HpFloor = Math.Max(1, ph.Mark * e.MaxHp);
            bool atMark = e.Hp <= e.HpFloor + 0.5;
            if ((atMark && PhaseT >= ph.Floor * FloorScale) || (ph.Ceiling > 0 && PhaseT >= ph.Ceiling)) { Turn(e); return true; }
        }
        // The last phase keeps its floor too; then it dies (or holds at one, for a boss that ends otherwise).
        else e.HpFloor = DiesAtZero && PhaseT >= ph.Floor * FloorScale ? 0 : 1;
        if (!Soft && FightT >= SoftAt)
        {
            Soft = true;
            A.HordeShare = 1;
            var (title, sub) = SoftWords(e);
            A.Say(title, sub, "danger");
            OnSoft();
        }
        if (!Hard && FightT >= HardAt)
        {
            Hard = true;
            A.Say(HardName, HardSub, "danger");
            OnHard();
        }
        return Act(e, dt);
    }

    /// <summary>A phase turns: the Break lands, the boss staggers (it cannot be hurt
    /// in it), and the next phase begins.</summary>
    void Turn(Enemy e)
    {
        double over = e.Overflow;
        BreakSum += over;
        e.Overflow = 0;
        if (over > 0) B.Events.Emit(new Ev.Break { X = e.X, Z = e.Z, Amount = over, Enemy = e.Id });
        PhaseIx++;
        e.HpFloor = Math.Max(1, Current.Mark * e.MaxHp);
        TransitionT = 2.5 + Math.Min(2.5, over / Math.Max(1, e.MaxHp) * 25);
        e.TakenMul = 0;
        Channel = null;
        // Whatever it was winding up is dropped, quietly: the turn is the news, not an
        // "Interrupted!" over it, and an old move must not finish in the new phase.
        move = null;
        e.State = EnemyState.Active;
        B.Events.Emit(new Ev.Shake { Amount = 0.35 });
        A.Say(Current.Name, over > 0 ? $"Break: {Math.Round(over):N0}" : null, "danger");
        // Ruin: it bursts as the phase turns (out of it in the turn's moment).
        if (ruin) Circle(e.X, e.Z, 4.5, 1.5, 1.2, "It bursts", School.Fire);
    }

    /// <summary>What the bar shows.</summary>
    public BossBar Bar(string name, string title) => new(name, title, E.Hp, E.MaxHp,
        Phases.Take(Phases.Length - 1).Select(p => p.Mark).ToArray(),
        Channel is { } c ? (c, ChannelProgress) : null,
        TransitionT > 0, IsBoss: true, Break: BreakSum + E.Overflow, Stagger: E.StaggeredT > 0 ? 1 : E.Stagger);

    protected abstract string HardName { get; }
    /// <summary>What is said as it grows wild (docs/WRITING_PASS.md 23.4): a boss whose wildness is its own
    /// says so in its own words.</summary>
    protected virtual (string Title, string Sub) SoftWords(Enemy e) =>
        ($"{e.Named?.Title ?? e.Def.Name} grows wild", A.HordeReturns ? "Its moves quicken, and the horde comes back" : "Its moves quicken");
    /// <summary>What is said under its end's name.</summary>
    protected virtual string HardSub => "The end of it, one way or the other";
    /// <summary>When it grows wild, and when its end comes on a loop: three and five minutes at the
    /// table; a story's boss is a longer fight (docs/design/STORY_BOSSES.md 0.4).</summary>
    protected virtual double SoftAt => 180;
    protected virtual double HardAt => 300;
    /// <summary>A phase begins (and the fight, for phase 0).</summary>
    protected abstract void Enter(int phase);
    /// <summary>Its moves; true while one moves it.</summary>
    protected abstract bool Act(Enemy e, double dt);
    protected virtual void OnSoft() { }
    protected virtual void OnHard() { }
    /// <summary>Hit by its weakness: by default, its channel breaks and it is held.</summary>
    public virtual void OnHit(Enemy e, School school, double dmg)
    {
        if (school == Weakness && Channel != null) BreakChannel(e, $"{school} breaks it");
    }
    public virtual void OnStagger(Enemy e) { if (Channel != null) BreakChannel(e, "Staggered"); }
    /// <summary>The fight is over (won): what the boss leaves.</summary>
    public virtual void Fell(Enemy e) { }

    protected void BreakChannel(Enemy e, string why)
    {
        Channel = null;
        ChannelProgress = 0;
        move = null;
        e.State = EnemyState.Stunned;
        e.StateT = 3;
        B.Events.Emit(new Ev.Announce { Title = "Channel broken", Subtitle = why, Tone = Tone.Boon });
    }

    /* ---------------------------------------------------------- the moves -- */

    /// <summary>A move under way: its wind-up and what it does as it ends.</summary>
    sealed class Move
    {
        public double T, Dur;
        public Func<double, bool>? Each;
        public Action? Done;
        public double DashX, DashZ, DashFromX, DashFromZ;
        public bool Dash;
    }
    Move? move;

    /// <summary>Hold still for `seconds` (a wind-up, a channel), calling `each` every tick
    /// (false ends it early) and `done` at the end.</summary>
    protected void Hold(double seconds, Action? done = null, Func<double, bool>? each = null) =>
        move = new Move { Dur = seconds, Done = done, Each = each };

    /// <summary>Run to a point over `seconds` (a scripted lunge or charge).</summary>
    protected void DashTo(double x, double z, double seconds, Action? done = null)
    {
        if (B.InBounds != null && !B.InBounds(x, z)) (x, z) = (E.X + (x - E.X) * 0.5, E.Z + (z - E.Z) * 0.5);
        move = new Move { Dur = seconds, Done = done, Dash = true, DashFromX = E.X, DashFromZ = E.Z, DashX = x, DashZ = z };
    }

    protected bool Busy => move != null;
    /// <summary>Its runs carry it over gaps in the ground (Grimtunnel under it).</summary>
    protected virtual bool OverGaps => false;

    /// <summary>Runs the move under way; true while there is one.</summary>
    protected bool Running(Enemy e, double dt)
    {
        if (move == null) return false;
        move.T += dt;
        e.Vx = e.Vz = 0;
        if (move.Dash)
        {
            double k = Math.Min(1, move.T / Math.Max(0.05, move.Dur));
            double nx = move.DashFromX + (move.DashX - move.DashFromX) * k, nz = move.DashFromZ + (move.DashZ - move.DashFromZ) * k;
            e.Vx = (nx - e.X) / Math.Max(dt, 1e-4); e.Vz = (nz - e.Z) / Math.Max(dt, 1e-4);
            e.X = nx; e.Z = nz;
            B.Collision.Resolve(ref e.X, ref e.Z, e.Radius, overGaps: OverGaps);
            e.Facing = Math.Atan2(move.DashZ - move.DashFromZ, move.DashX - move.DashFromX);
            e.State = EnemyState.Active;
            e.Anim = EnemyAnim.Move;
        }
        else
        {
            e.State = Channel != null ? EnemyState.Casting : EnemyState.Windup;
            e.Anim = EnemyAnim.Windup;
        }
        bool go = move.Each?.Invoke(move.T) ?? true;
        // The move ended itself (a channel broken from inside it): nothing is left to finish.
        if (move == null) return true;
        if (!go || move.T >= move.Dur)
        {
            var m = move;
            move = null;
            e.State = EnemyState.Active;
            m.Done?.Invoke();
        }
        return true;
    }

    /* ------------------------------------------------- the shapes it marks -- */

    protected (double X, double Z, double D) ToPlayer()
    {
        var p = B.Player;
        double dx = p.X - E.X, dz = p.Z - E.Z, d = Math.Max(0.001, Math.Sqrt(dx * dx + dz * dz));
        return (dx / d, dz / d, d);
    }

    protected Battle.EnemyBlow Circle(double x, double z, double r, double delay, double mul, string label = "", School school = School.Physical) =>
        Oathed(B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, X = x, Z = z, Radius = r, Delay = delay, Damage = E.Damage * mul, School = school, Source = Who, From = E, Label = label == "" ? null : label }), mul, x, z, r * 0.6);

    protected Battle.EnemyBlow Lane(double x0, double z0, double x1, double z1, double width, double delay, double mul, string label = "", School school = School.Physical) =>
        Oathed(B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Line, X = x0, Z = z0, X1 = x1, Z1 = z1, Width = width, Delay = delay, Damage = E.Damage * mul, School = school, Source = Who, From = E, Label = label == "" ? null : label }), mul, x1, z1, width * 0.7);

    protected Battle.EnemyBlow Cone(double radius, double arcDeg, double delay, double mul, string label = "", School school = School.Physical)
    {
        var (dx, dz, _) = ToPlayer();
        return Oathed(B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Cone, X = E.X, Z = E.Z, Radius = radius, Angle = Math.Atan2(dz, dx), Arc = arcDeg * Math.PI / 180, Delay = delay, Damage = E.Damage * mul, School = school, Source = Who, From = E, Label = label == "" ? null : label }),
            mul, E.X + dx * radius * 0.6, E.Z + dz * radius * 0.6, radius * 0.35);
    }

    protected Battle.EnemyBlow Band(double x, double z, double inner, double outer, double delay, double mul, string label = "", School school = School.Physical, TelegraphKind kind = TelegraphKind.Blow) =>
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Ring, Kind = kind, X = x, Z = z, Inner = inner, Radius = outer, Delay = delay, Damage = E.Damage * mul, School = school, Source = Who, From = E, Label = label == "" ? null : label });

    /// <summary>A marked blow under the oaths: the winter's chill on a heavy one, the embers' fire
    /// left where it lands (a little patch, so the clear ground round it stays clear).</summary>
    Battle.EnemyBlow Oathed(Battle.EnemyBlow b, double mul, double x, double z, double r)
    {
        if (winter && mul >= 1.5 && b.Slow == 0) { b.Slow = 0.55; b.SlowFor = 1.5; }
        if (embers && b.Kind == TelegraphKind.Blow && b.After == null)
        {
            double dmg = E.Damage * 0.15;
            b.After = bb => { var zn = bb.SpawnZone(Side.Enemy, x, z, Math.Clamp(r, 1, 2.2), 3, dmg, School.Fire); if (zn != null) zn.Tags = [Tag.Zone, Tag.Fire]; };
        }
        return b;
    }

    protected string Who => E.Named?.Title ?? E.Def.Name;

    /// <summary>Its own kind round it, `n` of them in a ring of `r`.</summary>
    protected void Ring(string def, int n, double cx, double cz, double r, SpawnStyle style = SpawnStyle.Walk)
    {
        for (int k = 0; k < n; k++)
        {
            double a = k * Math.PI * 2 / n;
            double x = cx + Math.Cos(a) * r, z = cz + Math.Sin(a) * r;
            if (A.CanStand(x, z)) A.Spawn(def, x, z, false, style);
        }
    }

    protected int Near(string def, double r)
    {
        int n = 0;
        foreach (var o in B.Enemies.Items)
            if (o.Alive && o != E && o.State != EnemyState.Dying && o.Def.Id == def && (o.X - E.X) * (o.X - E.X) + (o.Z - E.Z) * (o.Z - E.Z) < r * r) n++;
        return n;
    }
}
