using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Sound;

/// <summary>Which of her blows cut through the crowd (ARPG_FUN 15): the one place the rule lives. Heavy = a crit, or a hit of at least
/// 35% of the target's life, landed with her weapon (not a status tick, not a Flare). Synth's crowd sidechain does the rest.</summary>
public static class LeadRule
{
    public const double HeavyShare = 0.35;
    public static bool Heavy(Ev.Hit h) => h.Weapon != null && !h.ByFlare && !h.Dot && (h.Crit || h.Amount >= HeavyShare * h.MaxHp);
}
