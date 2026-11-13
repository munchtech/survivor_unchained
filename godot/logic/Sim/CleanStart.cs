namespace SurvivorUnchained.Sim;

public sealed partial class Battle
{
    /// <summary>(Codex audit SU-059) She gets up at a post with a clean start: whatever carried or held her as she fell
    /// ends (a leap's arc, a dash, a charge or haul, a cast's pose and plant, a brace), and what hurts or holds her is
    /// cleared (poison, burning, slows, roots, a drag). Her grace (Iframes) is the caller's to set.</summary>
    public void CleanStart()
    {
        var p = Player;
        p.Leap = null;
        p.DashT = 0; p.DashDX = p.DashDZ = 0; p.DodgeWindow = 0; p.PerfectThisDash = false;
        p.CastT = 0; p.PlantT = 0; p.CastWalk = 1; p.CastAimX = p.CastAimZ = 0; p.CastMoveB = null; p.AttackAnim = null;
        p.Vx = p.Vz = 0; p.Moving = false;
        Art.Rush = null; Art.RushT = 0; Art.Charge = null;
        Braced = null;
        p.BurnT = p.BurnDps = p.PoisonT = p.PoisonDps = 0;
        p.BurnSum = p.PoisonSum = p.DotT = 0;
        p.SlowT = 0; p.SlowF = 1;
        p.RootT = 0;
        p.DriftX = p.DriftZ = 0;
    }
}
