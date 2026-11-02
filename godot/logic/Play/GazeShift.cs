using System;
using System.Numerics;

namespace SurvivorUnchained.Play;

/// <summary>
/// Where her eyes and head point as she looks somewhere (Cinematics 7: "the opening cinematic when her eyes dart is
/// comically not good", the owner). Her eyes used to slide the whole way to every look in a fixed twentieth of a
/// second, the head still and the lids where they were: a big look whipped the iris up under a still lid, white
/// showing over it, and read as a cartoon. A person's eyes move like this instead:
///
/// A jump (a saccade) takes longer the further it goes (the main sequence: about 21 ms plus 2.2 ms a degree), and is
/// fast at the start and slow to settle (its speed peaks a third of the way in). A look can also glide, eased over a
/// given time (a drowsy look, or following something).
///
/// The eyes turn only so far in the head (Reach). What a look asks past that, and a share of any big look (the
/// head's share, 0.6 unless a cue says), the head carries: it starts 50 ms after the eyes and eases in over a quarter
/// second and more, and the eyes roll back as it comes (the vestibulo-ocular reflex), so the look itself holds still
/// on its target: eye + head = where she looks, once the head has arrived and whenever the eyes are inside their reach.
///
/// The upper lid rides on the eye: lower as she looks down, a little higher as she looks up, on top of blinks and held
/// lids. A big jump of the eye in her head comes with a blink, as most big glances do (it also hides the whip).
///
/// Units are her iris's radius (the eye shader's gaze: +x her left, +y down). Calibration: on heroine.glb's
/// HeroineEyes (two balls of radius 15 mm), the angle from each ball's centre between the iris's painted centre
/// (iris_a, iris_b) and the points one radius (0.117 UV) out is 24 deg at 0.6-1.0 radii and 28 deg near the centre
/// (a least-squares sphere per eye; the UV's distance from the iris centre in radii against the angle about the ball;
/// 0.8 radii toward each UV direction gives 18-21 deg). So one radius is taken as 25 deg of eye (and of head) turn.
/// Engine-free; View/HerFaceLife runs it and View/GazeCarry turns the head.
/// </summary>
public sealed class GazeShift
{
    /// <summary>Degrees of eye turn per iris radius (her eye's own, measured as above).</summary>
    public const float DegPerRadius = 25f;
    /// <summary>How far the eyes turn in the head, at most, unless a cue says (radii: 12.5 deg).</summary>
    public const float DefaultReach = 0.5f;
    /// <summary>A shift under this leaves the head where it is (the eyes alone glance); over it the head takes AutoHead.</summary>
    public const float SmallShift = 0.3f, AutoHead = 0.6f;
    /// <summary>An eye-in-head jump this big comes with a blink.</summary>
    public const float BlinkJump = 0.4f;
    /// <summary>A look this close to straight ahead lets the head go back to where the body has it.</summary>
    public const float NearCentre = 0.1f;
    /// <summary>The head follows the eyes this late (s).</summary>
    public const double HeadLag = 0.05;
    /// <summary>The upper lid's follow of the eye, as a share of its travel from rest to shut, per radius down (and up).</summary>
    public const float LidDown = 0.45f, LidUp = 0.2f;

    /// <summary>A saccade's length in seconds for a jump of <paramref name="radii"/> (the main sequence).</summary>
    public static double SaccadeTime(float radii) => 0.021 + 0.0022 * Math.Abs(radii) * DegPerRadius;

    /// <summary>How far through its jump a saccade is at <paramref name="x"/> (0..1 of its time): the integral of a
    /// speed x(1-x)^2, peaking a third of the way in (fast in, slow out); 0 at 0, exactly 1 at 1, never back.</summary>
    public static float Skewed(float x)
    {
        if (x <= 0) return 0;
        if (x >= 1) return 1;
        return x * x * (6 - 8 * x + 3 * x * x);
    }

    /// <summary>The ease of a glide and of the head (smoothstep).</summary>
    public static float Smooth(float x)
    {
        x = Math.Clamp(x, 0, 1);
        return x * x * (3 - 2 * x);
    }

    /// <summary>An eye-in-head turn held inside <paramref name="reach"/>.</summary>
    public static Vector2 Clamp(Vector2 v, float reach)
    {
        float l = v.Length();
        return l > reach && l > 0 ? v * (reach / l) : v;
    }

    /// <summary>Where the head should carry a new look to. Near straight ahead it goes back to none; a scripted head
    /// look (owned) leaves it none too. A small shift with no share given keeps the head where it is, moving it only by
    /// what the eyes can't reach; otherwise the head takes its share of the whole look, and whatever is past the eyes' reach.</summary>
    public static Vector2 HeadFor(Vector2 look, Vector2 headNow, float shift, float? share, float reach, bool owned = false)
    {
        if (owned || look.Length() < NearCentre) return Vector2.Zero;
        if (share is null && shift < SmallShift) return look - Clamp(look - headNow, reach);
        float s = Math.Clamp(share ?? AutoHead, 0, 1);
        return look - Clamp((1 - s) * look, reach);
    }

    /// <summary>The head's time to carry a change of <paramref name="radii"/>.</summary>
    public static double HeadTime(float radii) => 0.25 + 0.25 * Math.Abs(radii);

    /// <summary>Her upper lid (0 wide to 1 shut) from its rest, a blink's or a held lid's <paramref name="shut"/> (0 open at
    /// rest, 1 shut) and the eye's vertical turn in her head (+ down): looking down it lowers LidDown of its travel per
    /// radius, looking up it lifts LidUp, never past wide open; the follow fades as a blink closes, so a blink still shuts.</summary>
    public static float Lid(float rest, float shut, float eyeY)
    {
        float travel = 1 - rest;
        float follow = (eyeY > 0 ? LidDown : LidUp) * travel * eyeY;
        return Math.Clamp(rest + travel * shut + follow * (1 - shut), 0, 1);
    }

    /// <summary>Whether a jump of the eye in the head comes with a blink: a cue may force one or stop one; held lids never blink.</summary>
    public static bool BlinkOn(float jump, bool? force, bool held) => !held && (force ?? jump >= BlinkJump);

    /// <summary>How far the eyes turn in the head, at most (radii).</summary>
    public float Reach = DefaultReach;
    /// <summary>The eyes' turn in the head now, and the head's carry (radii; +x her left, +y down).</summary>
    public Vector2 Eye { get; private set; }
    public Vector2 Head { get; private set; }
    /// <summary>Where she is looking now (eye and head), and where to.</summary>
    public Vector2 Net => Eye + Head;
    public Vector2 Point { get; private set; }
    /// <summary>Where the head is going.</summary>
    public Vector2 HeadGoal => h1;

    Vector2 e0, h0, h1;
    double sAt = -1, sDur, hAt = -1, hDur;
    bool glide;

    /// <summary>A move of the look to <paramref name="point"/> at <paramref name="now"/>: a saccade, or a glide over
    /// <paramref name="over"/> seconds; <paramref name="headTo"/> sends the head too (HeadFor), from HeadLag after.
    /// Returns the eyes' own jump in the head (radii), for a blink.</summary>
    public float Move(double now, Vector2 point, double over = 0, Vector2? headTo = null)
    {
        Point = point;
        e0 = Eye;
        float jump = (Clamp(point - Head, Reach) - Eye).Length();
        glide = over > 0;
        sDur = glide ? over : SaccadeTime(jump);
        sAt = now;
        if (headTo is Vector2 h) HeadTo(now + HeadLag, h, glide ? over : 0);
        return jump;
    }

    /// <summary>The head sent to <paramref name="to"/> from <paramref name="at"/>, eased over its time (or <paramref name="over"/>, if longer).</summary>
    public void HeadTo(double at, Vector2 to, double over = 0)
    {
        if (Vector2.Distance(to, h1) < 1e-5f && (hAt >= 0 || Vector2.Distance(Head, to) < 1e-5f)) return;
        h0 = Head;
        h1 = to;
        hAt = at;
        hDur = Math.Max(HeadTime((to - Head).Length()), over);
    }

    /// <summary>The look set at once (at a cut): no jump, no glide, the head already there.</summary>
    public void Set(Vector2 point, Vector2 head)
    {
        Point = point;
        Head = h0 = h1 = head;
        Eye = Clamp(point - head, Reach);
        sAt = hAt = -1;
    }

    /// <summary>The eyes and head at <paramref name="now"/>: the head along its ease, the eyes on their jump toward where
    /// the look is less what the head carries (inside their reach), and after it, there each frame (rolling back as the head comes).</summary>
    public void Step(double now)
    {
        if (hAt >= 0 && now >= hAt)
        {
            float k = hDur > 0 ? (float)((now - hAt) / hDur) : 1;
            Head = Vector2.Lerp(h0, h1, Smooth(k));
            if (k >= 1) hAt = -1;
        }
        var want = Clamp(Point - Head, Reach);
        if (sAt >= 0)
        {
            float x = sDur > 0 ? (float)((now - sAt) / sDur) : 1;
            Eye = Vector2.Lerp(e0, want, glide ? Smooth(x) : Skewed(x));
            if (x >= 1) sAt = -1;
        }
        else Eye = want;
    }
}
