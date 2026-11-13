using System;
using System.Runtime.CompilerServices;

namespace SurvivorUnchained.Sim;

public sealed partial class Battle
{
    /// <summary>(SU-070) What a skill card's numbers depend on, as one stamp: the fight itself, her stats, the lamps lit,
    /// and each carried skill's rank, slot, evolution, cast form and lit wick. Any build change moves it; a card cache keys
    /// on it (with the battle) so a ring equipped or a lamp lit never leaves an old number on a card.</summary>
    public long BuildStamp
    {
        get
        {
            var h = new HashCode();
            h.Add(RuntimeHelpers.GetHashCode(this));
            h.Add(Stats.Version);
            h.Add(RuntimeHelpers.GetHashCode(Lamps));
            h.Add(Lamps.Version);
            h.Add(Weapons.Count);
            foreach (var w in Weapons)
            {
                h.Add(w.Id); h.Add(w.Rank); h.Add(w.Slot); h.Add(w.Slot2); h.Add(w.Evolution?.Id); h.Add(w.Cast); h.Add(w.Hold); h.Add(w.Pressed); h.Add(w.KindledNow);
                h.Add(w.Wick is { } k ? RuntimeHelpers.GetHashCode(k) : 0);
                h.Add(w.Wick?.Lit.Length ?? 0);
            }
            return h.ToHashCode();
        }
    }
}
