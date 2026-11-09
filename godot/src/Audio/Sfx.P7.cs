using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Sound;

public static partial class Sfx
{
    /// <summary>Shield Charge's sounds by phase (Ev.Charge): recorded only; the Slam's comes from its Ev.Explosion burst.</summary>
    public static void ShieldCharge(ChargePhase phase, Where w)
    {
        switch (phase)
        {
            case ChargePhase.Start: Cue("art.shield_charge.start", w); break;
            case ChargePhase.Impact: Cue("art.shield_charge.hit", w); break;
            case ChargePhase.Stop: Cue("art.shield_charge.stop", w); break;
        }
    }
}
