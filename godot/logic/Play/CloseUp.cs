using System;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play;

/// <summary>
/// The play camera's close view of her (the owner, 12 October 2026: "allow for mousewheel to view our character
/// like that when in town or when we go idle - its a great way to keep sex appeal when we get to endgame"). How near
/// the view is asked to come, 0 (play's own distance) to 1 (her from the waist up), decided here without the engine;
/// FollowCamera.Close turns the number into a pitch, a distance and a height on her.
///   - The wheel (and the right stick) brings it near only where it is safe (the town): Manual.
///   - Left alone long enough (IdleAfter, a setting) with nothing hostile near or after her, the view eases in on
///     its own (Idling), anywhere but a fight, a cinematic, a conversation, a screen or a night's arena.
///   - Any input, or anything hostile drawing near, ends the idle view at once; the wheel's own level stays.
///   - Moving, the view holds no nearer than MoveCap, so the street ahead stays in view.
/// Her pose (the owner, 17 October 2026: "would prefer to be able to stare at the butt"): the wheel never turns her;
/// she turns to the view and takes her idle pose only in the idle view (a true idle, a minute by default) or while
/// a framed screen (her book, the pack) is open where screens are her rest: the town and the ember's arenas, not
/// the field, whose world goes on. PoseFor is the one place that picks it (more poses and emotes later go there).
/// </summary>
public sealed class CloseUp
{
    /// <summary>One notch of the wheel.</summary>
    public const double Step = 0.1;
    /// <summary>The nearest a moving view holds: her whole figure large, the ground ahead still in frame.</summary>
    public const double MoveCap = 0.6;
    /// <summary>How near the idle view comes (her from the hips up).</summary>
    public const double IdleLevel = 0.92;
    /// <summary>Anything hostile this near ends the idle view, aware of her or not (metres).</summary>
    public const double NearRadius = 22;
    /// <summary>Anything hostile and roused (not standing idle) this near ends it too.</summary>
    public const double RousedRadius = 45;

    /// <summary>Seconds without input before the view eases in (the setting; a minute by default).</summary>
    public double IdleAfter = 60;
    /// <summary>The idle view at all (the setting).</summary>
    public bool IdleOn = true;

    /// <summary>The wheel's level (0..1): kept while she stays in a safe place, 0 anywhere else.</summary>
    public double Manual { get; private set; }
    /// <summary>The view came in on its own.</summary>
    public bool Idling { get; private set; }
    /// <summary>Seconds since the last input (or since the last thing that stopped the idle view).</summary>
    public double Quiet { get; private set; }

    /// <summary>What the game is doing this frame.</summary>
    public readonly record struct Situation(
        /// <summary>A safe place (a zone without combat: the town).</summary>
        bool Safe,
        /// <summary>Not free play: a cinematic, a conversation, a screen, a held camera, a night's arena or boss.</summary>
        bool Held,
        /// <summary>Anything hostile near or after her (Threat).</summary>
        bool Threat,
        /// <summary>She is moving.</summary>
        bool Moving);

    /// <summary>The wheel or the stick turned by so many notches (up, nearer: positive), from the level shown now
    /// (so a wheel during the idle view carries on from where it is rather than jumping). Only where it is safe;
    /// elsewhere it is only an input (it ends the idle view).</summary>
    public void Wheel(double notches, double shown, in Situation s)
    {
        if (notches == 0) return;
        bool wasIdle = Idling;
        Input();
        if (!s.Safe || s.Held) return;
        double from = wasIdle ? Math.Max(Manual, shown) : Manual;
        Manual = Math.Clamp(from + notches * Step, 0, 1);
        // (a hair from play's distance is play's distance: ten turns in and ten out come back to it exactly)
        if (Manual < 0.02) Manual = 0;
    }

    /// <summary>Any input at all (a key, a button, a click, the mouse moved, a stick): the idle view ends.</summary>
    public void Input()
    {
        Quiet = 0;
        Idling = false;
    }

    /// <summary>Forgotten: a new place, the wheel's level back to play's distance.</summary>
    public void Reset()
    {
        Manual = 0;
        Input();
    }

    /// <summary>A frame: how near the view is asked to be now (0..1).</summary>
    public double Update(double dt, in Situation s)
    {
        if (!s.Safe) Manual = 0;
        if (s.Held || s.Threat || s.Moving) { Quiet = 0; Idling = false; }
        else Quiet += dt;
        if (s.Held) return 0;
        if (IdleOn && !Idling && Quiet >= IdleAfter) Idling = true;
        if (!IdleOn) Idling = false;
        double level = Idling ? Math.Max(Manual, IdleLevel) : Manual;
        return s.Moving ? Math.Min(level, MoveCap) : level;
    }

    /// <summary>How fast the view goes to it (FollowCamera's damping, per second): the idle view drifts in slowly
    /// and leaves at once; the wheel is quick.</summary>
    public double Rate(double target, double shown) => Idling && target > shown ? 0.45 : 4.0;

    /// <summary>How she stands: her own (her facing and stance as play left them) or turned to the view in her
    /// idle pose. (One place: emotes and more poses come in here later.)</summary>
    public enum Pose { Own, ToTheView }

    /// <summary>Her pose now: to the view only in the idle view, or with a framed screen open (framed) in the town
    /// (safe) or an ember's arena (ember); never for the wheel alone, never for a screen in the field.</summary>
    public Pose PoseFor(bool framed, bool safe, bool ember) =>
        framed ? (safe || ember ? Pose.ToTheView : Pose.Own)
        : Idling ? Pose.ToTheView : Pose.Own;

    /// <summary>Anything hostile near her, or roused and coming (CloseUp.NearRadius, RousedRadius).</summary>
    public static bool Threat(Battle b)
    {
        var p = b.Player;
        foreach (var e in b.Enemies.Living())
        {
            if (!b.HostileToPlayer(e)) continue;
            double dx = e.X - p.X, dz = e.Z - p.Z, d2 = dx * dx + dz * dz;
            if (d2 < NearRadius * NearRadius) return true;
            if (e.State != EnemyState.Idle && d2 < RousedRadius * RousedRadius) return true;
        }
        return false;
    }

    /// <summary>By night, someone the close view frames carrying a lit light (a torch) is keyed by it: the close key, its hair
    /// and gear twins and the fill come down to CarriedKeyShare (the rig's key at full was brighter than his torch and blew his
    /// face out, NPC 18), warmed CarriedKeyWarm of the way to the torch's colour, from the torch's side and height.</summary>
    public const double CarriedKeyShare = 0.35, CarriedKeyWarm = 0.6;
    /// <summary>The carried key's height held within these degrees: a torch at his chest keys from level, never from under his chin.</summary>
    public const double CarriedElMin = 0, CarriedElMax = 40;

    /// <summary>The close key's (and fill's) share: CarriedKeyShare by night with a lit light carried, else 1.</summary>
    public static double CarriedShare(bool night, bool carries) => night && carries ? CarriedKeyShare : 1;

    /// <summary>Where the key stands for a carried light at (dx, dy, dz) from the framed chest: its bearing (atan2(x, z), as the
    /// rig's) and its height in radians, held within CarriedElMin..CarriedElMax degrees.</summary>
    public static (double Az, double El) CarriedAim(double dx, double dy, double dz)
    {
        double el = Math.Atan2(dy, Math.Sqrt(dx * dx + dz * dz)), lo = CarriedElMin * Math.PI / 180, hi = CarriedElMax * Math.PI / 180;
        return (Math.Atan2(dx, dz), Math.Clamp(el, lo, hi));
    }
}
