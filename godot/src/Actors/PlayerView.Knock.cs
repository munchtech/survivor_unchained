using Godot;

namespace SurvivorUnchained.View;

/// <summary>The kit charge's knockdown (H6, Ev.Knockdown): she goes over onto her back (her own death_back, played fast
/// as the knock) and is up again (get_up_back) as the sim lets her go; a dash ends it (its roll takes over).</summary>
public partial class PlayerView
{
    /// <summary>The fall's and the get-up's clocks (time; -1: not knocked).</summary>
    double knockUpAt = -1, knockEnd = -1;
    float knockUpSpeed = 1;

    /// <summary>Knocked down for `seconds` (the sim's root): the fall at once, the get-up timed to end ~0.2 s after.</summary>
    public void OnKnockdown(double seconds)
    {
        if (!mine || dead || fallen || seconds <= 0 || !own.Has("death_back") || !own.Has("get_up_back")) return;
        // (death_back is 1.33 s, get_up_back 1.67 s; a knock is 0.9 s at most: both run fast, the fall the faster)
        double fall = Mathf.Clamp(0.55 * seconds, 0.25, 0.5), up = Mathf.Clamp(seconds - fall + 0.2, 0.35, 0.8);
        FullHer("death_back", 1.333 / fall, false);
        if (carriage != null) carriage.Aim = carriage.Bank = carriage.Tilt = carriage.HeadLevel = 0;
        aim = 0;
        knockUpAt = time + fall;
        knockEnd = knockUpAt + up;
        knockUpSpeed = (float)(1.667 / up);
        // (no flinch laid over the fall)
        hurtSeen = Mathf.Max(hurtSeen, knockEnd - time);
    }

    /// <summary>Knocked down now (her swings are not drawn over the fall).</summary>
    bool Knocked => knockEnd >= 0 && time < knockEnd;

    /// <summary>Each frame, before the dash: a dash ends the knock; else the get-up at its time (soft: a step takes it).</summary>
    void StepKnock(double dashT)
    {
        if (knockEnd < 0) return;
        if (dashT > 0 || dead || fallen) { knockUpAt = knockEnd = -1; return; }
        if (knockUpAt >= 0 && time >= knockUpAt)
        {
            knockUpAt = -1;
            FullHer("get_up_back", knockUpSpeed, true);
        }
        if (time >= knockEnd) knockEnd = -1;
    }

    /// <summary>A swing begun while she is down: seen (so it is not drawn late), not drawn.</summary>
    bool KnockSkip(double t)
    {
        if (!Knocked) return false;
        lastAttack = t;
        return true;
    }
}
