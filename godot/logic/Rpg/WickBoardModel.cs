using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Rpg;

public enum WickLampState { Lit = 0, Planned = 1, Unlit = 2 }

/// <summary>The wick panel's existing lamp states, read from the same day weapon as its stats and tooltip.</summary>
public sealed class WickBoardModel
{
    public static readonly WickBoardModel Empty = new("", 0, [], [], []);

    readonly string skill;
    public int Rank { get; }
    public IReadOnlyList<string> Plan { get; }
    public string[] Path { get; }
    public string[] Lit { get; }

    WickBoardModel(string skill, int rank, IReadOnlyList<string> plan, string[] path, string[] lit)
    {
        this.skill = skill;
        Rank = rank;
        Plan = plan;
        Path = path;
        Lit = lit;
    }

    public static WickBoardModel Read(CharacterData ch, string skill)
    {
        var path = WickBook.Path(ch, skill);
        int rank = SkillBook.Rank(ch);
        var weapon = WickBook.Weapon(ch, skill, WickBook.RankIn(ch, skill, false));
        return new(skill, rank, WickBook.PlanOf(ch, skill).ToArray(), path, weapon.Wick?.Lit ?? Array.Empty<string>());
    }

    public bool IsLit(string id) => Lit.Contains(id);
    public bool IsPlanned(string id) => Plan.Contains(id);
    public bool TurnTaken => Plan.Any(id => Wicks.IsTurn(skill, id)) || Lit.Any(id => Wicks.IsTurn(skill, id));
    public bool Crossed(string id) => TurnTaken && !IsPlanned(id) && !IsLit(id);
    public WickLampState StateOf(string id) => IsLit(id) ? WickLampState.Lit : IsPlanned(id) ? WickLampState.Planned : WickLampState.Unlit;
}
