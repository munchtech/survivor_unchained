using System;

namespace SurvivorUnchained.Sim;

/// <summary>How a hostile telegraph is read on screen. An elite's or a boss's blow is the red line (Danger);
/// the crowd's blows stay dim amber; a champion's full ring with no inner edge is its raising of the dead,
/// drawn amber and never danger. A boss's marks must set Boss: their Ids are not the enemy's Id
/// (the Ford-Warden's are e.Id*10+1 and +2), so the champion lookup by Id cannot find them.</summary>
public static class TelegraphRead
{
    public enum TeleLook { Plain, Danger, Amber }

    /// <summary>A boss's mark, or one whose Id is a living elite's or boss's.</summary>
    public static bool Champion(Ev.Telegraph e, Func<int, bool> isChampion) => e.Boss || isChampion(e.Id);

    public static (TeleLook Look, bool Raising) Of(Ev.Telegraph e, Func<int, bool> isChampion)
    {
        bool raising = e.Shape == TelegraphShape.Ring && e.Inner <= 0.01 && !e.Boss && e.Label == null;
        bool danger = e.Hostile && e.Kind == TelegraphKind.Blow && e.Faction == null && !raising && Champion(e, isChampion);
        bool amber = !danger && e.Hostile && e.Kind == TelegraphKind.Blow && e.Faction == null && e.Label == null;
        return (danger ? TeleLook.Danger : amber ? TeleLook.Amber : TeleLook.Plain, raising);
    }
}
