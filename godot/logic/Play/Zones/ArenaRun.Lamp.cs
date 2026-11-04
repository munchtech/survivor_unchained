using System;
using System.Collections.Generic;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Sim;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Play.Zones;

/* The lamp to hold (H1 combat teeth, docs/team/hook/H1_combat_teeth.md item 6, part B): a reason to stand somewhere.
 * A board's fold has a lamp at its middle (Maps/ArenaBoard.cs), cold till its minute. Lit, it pays her while she stands
 * in its pool: the Flare fills faster and what she kills there leaves more ember. From a later minute the people want it
 * out: some of each wave walk to it (Enemy.Goal, down Battle.GoalFlow through the gaps) and douse it, turning on her only
 * when she comes close. At no life it goes out; she lights it again by standing at it with none of them at it. Through
 * the boss it stays as it is, and no more come for it. Every number is the board's (Content/Boards.LampDef). The sound
 * and the view hear Ev.BoardLamp; the HUD reads Battle.HeldLamp. No board (a tier without one, a story night): none of it. */
public sealed partial class ArenaRun
{
    BoardLamp? lamp;
    Boards.LampDef? lampDef;
    readonly LampMark lampMark = new();
    Rng? lampRng;
    double lampLife, relightT, lampWarnAt = -1e9, lampTickAt, lampFill = 1, lampEmber = 1;
    bool lampCaught, lampLit, lampIn, dousing;

    /// <summary>There is a lamp tonight (a board with one).</summary>
    public bool HasLamp => lamp != null;
    /// <summary>The lamp has caught and burns now.</summary>
    public bool LampLit => lampLit;
    /// <summary>She stands in its pool while it burns (its reward on her).</summary>
    public bool InLampPool => lampIn;
    /// <summary>Its life left, 0 to 1.</summary>
    public double LampLife => lampDef == null ? 0 : lampLife / lampDef.Life;
    /// <summary>The night's count of its going out, and of her lighting it again.</summary>
    public int LampOuts { get; private set; }
    public int LampRelights { get; private set; }
    /// <summary>The lamp (where it stands, its pool, its numbers), or null.</summary>
    public BoardLamp? Lamp => lamp;

    void LampBegin(Battle b)
    {
        if (map.Board is not { Lamps.Count: > 0 } board) return;
        lamp = board.Lamps[0];
        lampDef = lamp.Def;
        lampLife = lampDef.Life;
        lampRng = new Rng((uint)(Spec.Seed * 7349 + 6011));
        // Cold till its minute.
        if (lamp.Light >= 0) G.Look.SetLit(lamp.Light, false);
        b.GoalFlow = new FlowField(b.Collision, (int)Math.Ceiling(board.Radius + 12));
        b.GoalFlow.Update(lamp.X, lamp.Z, true);
        lampMark.X = lamp.X; lampMark.Z = lamp.Z; lampMark.Pool = lampDef.Pool;
        b.HeldLamp = lampMark;
    }

    void LampStep(double dt)
    {
        if (lamp == null || lampDef == null || B == null) return;
        var d = lampDef;
        var p = B.Player;
        if (!lampCaught && Minute >= d.LitAt)
        {
            lampCaught = true;
            LampOn(BoardLampState.Lit);
            G.Announce(new Announcement("The old lamp in the fold catches", "Hold its light", "reward", 3));
        }
        // The snuffers at it.
        int at = 0;
        foreach (var e in B.Enemies.Living())
            if (e.Goal && e.State != EnemyState.Dying && Dist(e.X, e.Z, lamp.X, lamp.Z) <= d.AtLamp) at++;
        double her = Dist(p.X, p.Z, lamp.X, lamp.Z);
        if (lampLit && at > 0)
        {
            lampLife = Math.Max(0, lampLife - d.Douse * at * dt);
            if (!dousing || Seconds - lampTickAt >= 1)
            {
                lampTickAt = Seconds;
                B.Events.Emit(new Ev.BoardLamp { X = lamp.X, Z = lamp.Z, State = BoardLampState.Dousing, Life = LampLife });
            }
            if (!dousing && her > d.Pool && Seconds - lampWarnAt >= d.WarnEvery)
            {
                lampWarnAt = Seconds;
                G.Announce(new Announcement("They are at the lamp!", "", "danger", 2));
            }
            dousing = true;
            if (lampLife <= 0)
            {
                lampLit = false;
                dousing = false;
                LampOuts++;
                if (lamp.Light >= 0) G.Look.SetLit(lamp.Light, false);
                B.Events.Emit(new Ev.BoardLamp { X = lamp.X, Z = lamp.Z, State = BoardLampState.Out, Life = 0 });
                G.Announce(new Announcement("The lamp is out", "", "danger", 2.2));
            }
        }
        else dousing = false;
        // Out: she cups the wick, none of them at it.
        if (lampCaught && !lampLit)
        {
            relightT = her <= d.RelightR && at == 0 && p.Alive ? relightT + dt : 0;
            if (relightT >= d.Relight)
            {
                relightT = 0;
                LampRelights++;
                LampOn(BoardLampState.Relit);
                G.Announce(new Announcement("You cup the wick; it takes", "", "reward", 2.2));
            }
        }
        // Her reward: on while she stands in its lit pool, taken off cleanly the moment she does not.
        LampReward(lampLit && p.Alive && her < d.Pool);
        lampMark.Life = LampLife;
        lampMark.Lit = lampLit;
        lampMark.Caught = lampCaught;
    }

    void LampOn(BoardLampState state)
    {
        lampLit = true;
        lampLife = lampDef!.Life;
        if (lamp!.Light >= 0) G.Look.SetLit(lamp.Light, true);
        B!.Events.Emit(new Ev.BoardLamp { X = lamp.X, Z = lamp.Z, State = state, Life = 1 });
    }

    /// <summary>Her reward on or off. Multiplied in and divided out, so it stacks with whatever else sets the rules.</summary>
    void LampReward(bool on)
    {
        if (on == lampIn) return;
        lampIn = on;
        var r = B!.Rules;
        if (on)
        {
            lampFill = lampDef!.FlareFill; lampEmber = lampDef.Ember;
            r.FlareFill *= lampFill; r.KillEmber *= lampEmber;
        }
        else { r.FlareFill /= lampFill; r.KillEmber /= lampEmber; }
    }

    /// <summary>A wave come in: from the lamp's minute some of its rank and file are sent for the lamp, not for her.</summary>
    void LampSend(List<Enemy> wave)
    {
        if (lamp == null || lampDef == null || bossUp || won || Minute < lampDef.SnuffFrom) return;
        foreach (var e in wave)
        {
            var def = e.Def;
            if (e.Elite || e.Boss || def.Ranged != null || def.Aura != null || def.Behavior is Behavior.Tunneler or Behavior.Ranged or Behavior.Caster) continue;
            if (lampRng!.Next() >= lampDef.SnuffShare) continue;
            e.Goal = true;
            e.GoalX = lamp.X; e.GoalZ = lamp.Z;
            e.GoalAggro = lampDef.SnuffAggro;
        }
    }

    /// <summary>The boss is up: no more come for the lamp, and those on their way turn on her. The lamp stays as it is.</summary>
    void LampBoss()
    {
        if (lamp == null || B == null) return;
        foreach (var e in B.Enemies.Living()) if (e.Goal) { e.Goal = false; e.RetargetT = 0; }
    }

    /// <summary>A test's or a probe's hand: send this one for the lamp now (as LampSend does).</summary>
    public void SendForLamp(Enemy e)
    {
        if (lamp == null || lampDef == null) return;
        e.Goal = true;
        e.GoalX = lamp.X; e.GoalZ = lamp.Z;
        e.GoalAggro = lampDef.SnuffAggro;
    }
}
