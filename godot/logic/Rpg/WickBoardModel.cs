using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Rpg;

public enum WickLampState { Lit = 0, Planned = 1, Unlit = 2 }

/// <summary>The wick panel's existing lamp states, read from the same weapon as its stats and tooltip.</summary>
public sealed class WickBoardModel
{
    public static readonly WickBoardModel Empty = new("", 0, [], [], [], []);

    readonly string skill;
    public int Rank { get; }
    public IReadOnlyList<string> Plan { get; }
    public string[] Path { get; }
    public string[] Lit { get; }
    public string[] Held { get; }
    public bool NoWick { get; }

    WickBoardModel(string skill, int rank, IReadOnlyList<string> plan, string[] path, string[] lit, string[] held, bool noWick = false)
    {
        this.skill = skill;
        Rank = rank;
        Plan = plan;
        Path = path;
        Lit = lit;
        Held = held;
        NoWick = noWick;
    }

    public static WickBoardModel Read(CharacterData ch, string skill, bool night = false)
    {
        var panel = WickBook.Panel(ch, skill, night);
        return new(skill, panel.Rank, WickBook.PlanOf(ch, skill).ToArray(), panel.Path, panel.Lit, panel.Held, panel.NoWick);
    }

    public bool IsLit(string id) => Lit.Contains(id);
    public bool IsPlanned(string id) => Plan.Contains(id);
    public bool TurnTaken => Plan.Any(id => Wicks.IsTurn(skill, id)) || Lit.Any(id => Wicks.IsTurn(skill, id));
    public bool Crossed(string id) => TurnTaken && !IsPlanned(id) && !IsLit(id);
    public WickLampState StateOf(string id) => IsLit(id) ? WickLampState.Lit : IsPlanned(id) ? WickLampState.Planned : WickLampState.Unlit;
}
