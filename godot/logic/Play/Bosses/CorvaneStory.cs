using System;
using SurvivorUnchained.Play.Story;
using SurvivorUnchained.Sim;
using CorvaneTeeth = SurvivorUnchained.Content.Teeth.Corvane;

namespace SurvivorUnchained.Play.Bosses;

/// <summary>
/// Corvane in the doorway (vault_opened's first stage, Play/Story/Corvane.cs): a lesson the Ford-Warden's length under
/// H1's boss rules. One signature, "Lie down.", behind its 0.7 s tell: he stops, raises the lamp and says it, and the
/// kit's pull opens round him (violet), dragging her in to its heart's slam, which knocks her down. Between them he
/// holds the doorway: within his tether of his mark, side-stepping to stay between her and the door, facing her; he
/// strikes only what stands across his path (a lamp swing, StoryBoss.Cuff) and never chases her across the court.
/// He does not strike first (no move of his for HoldAfterRaise s after she raises her weapon). Below LowAt of his life
/// the pull comes quicker and wider, and the only sign of it is the lamp burning brighter. One phase, no banner, one
/// bar; brought to one and past his floor (the Flare cuts it) and his backstop (MinSeconds), he goes down and lies
/// where he fell: the stage tells the rest. Every number is teeth.json story.corvane.
/// </summary>
public sealed class CorvaneStory : StoryBoss
{
    readonly CorvaneTeeth t;
    readonly (double X, double Z) mark, door;
    double holdT, sigT;
    bool low;

    public CorvaneStory(IStoryArena a, CorvaneTeeth teeth, (double X, double Z) mark, (double X, double Z) door) : base(a)
    {
        t = teeth;
        this.mark = mark;
        this.door = door;
    }

    protected override Phase[] Phases => phases ??= [new Phase("Corvane", 0, t.Floor, 0)];
    Phase[]? phases;
    public override School Weakness => School.Holy;
    public override string WeaknessText => "";
    protected override string HardName => "Lie down.";
    public override string ReEntry => "He is still in the door, the lamp held up.";
    public override double HealthMul(int tier) => t.HpMul;
    public override double Teeth => t.Teeth;
    protected override bool DiesAtZero => false;

    /// <summary>He has gone down (brought to one past his floors): he lies where he fell, and does nothing more.</summary>
    public bool Down => Ending;
    /// <summary>The pull's reach now (wider below LowAt).</summary>
    public double Reach => low ? t.ReachLow : t.Reach;
    /// <summary>Below LowAt of his life: the pull quicker and wider, the lamp brighter.</summary>
    public bool Low => low;

    protected override void Enter(int phase)
    {
        holdT = t.HoldAfterRaise;
        sigT = t.FirstAfter;
    }

    protected override bool Act(Enemy e, double dt)
    {
        if (Ending) return Lie(e);
        // Held at his backstop until he has fought MinSeconds (the Ford-Warden's lesson length): no build lays him down
        // sooner, whatever his floor (the Flare cuts that).
        if (FightT < t.MinSeconds) e.HpFloor = Math.Max(e.HpFloor, t.Backstop * MaxHp);
        if (Spent(e)) { Ending = true; return Lie(e); }
        if (!low && e.Hp <= e.MaxHp * t.LowAt) Brighten(e);
        if (Running(e, dt)) return true;
        var (dx, dz, d) = ToPlayer();
        // He does not strike first: she raised her weapon, so hers land first.
        if (holdT > 0)
        {
            holdT -= dt;
            Stand(e, dx, dz);
            return true;
        }
        sigT -= dt;
        // (nothing new is cast on her while she is down or getting up: the kit's grace)
        if (sigT <= 0 && B.KnockGraceLeft <= 0)
        {
            sigT = (low ? t.EveryLow : t.Every) * Cadence;
            Signature("Lie down.", SignatureLead, Cast, "chid");
            return true;
        }
        return Keep(e, dt, dx, dz, d);
    }

    /// <summary>The lamp raised: the kit's pull round him, his heart's slam knocking her down.</summary>
    void Cast()
    {
        var e = E;
        var k = Content.Telegraphs.Get("pull");
        double core = k is { Core: > 0 } ? k.Core : 2.4;
        var bl = B.Tell("pull", e, e.X, e.Z, t.Slam / core, reach: Reach, damageMul: t.PullDamage, knocks: true);
        if (bl == null) return;
        // He holds the lamp up through the drag and the slam.
        Hold((k?.Windup ?? 1.6) + (k?.Follow ?? 0.7) + 0.1, null, _ =>
        {
            E.State = EnemyState.Casting;
            E.Cast = CastKind.None;
            E.Anim = EnemyAnim.Cast;
            return true;
        });
    }

    /// <summary>The lamp burns brighter (his light's energy and his glow): the only sign the pull has quickened.</summary>
    void Brighten(Enemy e)
    {
        low = true;
        var def = e.Def.Clone();
        if (def.CarriedLight is { } cl) def.CarriedLight = cl with { Energy = t.LampEnergyLow, Range = cl.Range * 1.2 };
        def.Glow = t.GlowLow;
        e.Def = def;
    }

    void Stand(Enemy e, double dx, double dz)
    {
        e.Vx = e.Vz = 0;
        e.Facing = Math.Atan2(dz, dx);
        e.State = EnemyState.Active;
        e.Anim = EnemyAnim.Idle;
    }

    /// <summary>Between signatures he holds the doorway: toward her from his mark as far as his tether (and never into
    /// her), on her line to the door, facing her. Walked into across his path, he swings the lamp (StoryBoss.Cuff).</summary>
    bool Keep(Enemy e, double dt, double dx, double dz, double d)
    {
        var p = B.Player;
        // Her line to the door: he stands on it, a step out from his mark toward her, at most his tether.
        double ux = p.X - door.X, uz = p.Z - door.Z, ul = Math.Max(0.01, Math.Sqrt(ux * ux + uz * uz));
        double across = Dist(mark.X, mark.Z, door.X, door.Z);
        double gx = door.X + ux / ul * across, gz = door.Z + uz / ul * across;
        double mx = p.X - mark.X, mz = p.Z - mark.Z, ml = Math.Max(0.01, Math.Sqrt(mx * mx + mz * mz));
        double step = Math.Clamp(ml - 2.5, 0, t.Tether);
        gx += mx / ml * step; gz += mz / ml * step;
        double ox = gx - mark.X, oz = gz - mark.Z, ol = Math.Sqrt(ox * ox + oz * oz);
        if (ol > t.Tether) { gx = mark.X + ox / ol * t.Tether; gz = mark.Z + oz / ol * t.Tether; }
        double vx = gx - e.X, vz = gz - e.Z, vl = Math.Sqrt(vx * vx + vz * vz);
        if (vl < 0.25)
        {
            // (standing his ground, he swings at nothing: only what stands across his path is struck)
            Stand(e, dx, dz);
            return true;
        }
        double sp = Math.Min(e.Speed * 0.8, vl / Math.Max(dt, 1e-4));
        e.X += vx / vl * sp * dt;
        e.Z += vz / vl * sp * dt;
        B.Collision.Resolve(ref e.X, ref e.Z, e.Radius);
        e.Vx = vx / vl * sp; e.Vz = vz / vl * sp;
        e.State = EnemyState.Active;
        e.Anim = EnemyAnim.Move;
        // (facing her as he side-steps: Cuff turns him to her when she is not close, and to his step when she is)
        Cuff(e, dt, vx, vz, dx, dz, d, false, t.CuffMul, t.CuffEvery);
        return true;
    }

    /// <summary>Down: where he fell, still, nothing reaching him and nothing of his reaching her.</summary>
    bool Lie(Enemy e)
    {
        e.Vx = e.Vz = 0;
        e.TakenMul = 0;
        e.HpFloor = 1;
        e.Disposition = Disposition.Neutral;
        e.Provoked = false;
        e.State = EnemyState.Idle;
        e.Anim = EnemyAnim.Die;
        return true;
    }

    static double Dist(double ax, double az, double bx, double bz) => Math.Sqrt((ax - bx) * (ax - bx) + (az - bz) * (az - bz));
}
