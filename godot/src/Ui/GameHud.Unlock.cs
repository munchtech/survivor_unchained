using System;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Ui;

/* The glue of the unlock cards (docs/design/BUILD_UNLOCKS.md): the calling's skill, which no level's card carries, shown at the
 * first quiet moment (LevelCards.CallingDue), and the lesson after a key or stance card (UnlockLessons) as a hint at the next
 * fight, taken down on its time or when she uses the thing. The rules are pure, in LevelCardModel.cs and UnlockLessons.cs. */
public partial class GameHud
{
    /// <summary>The calling's skill carded by no level, waiting for a quiet moment.</summary>
    (int Level, string Skill)? callingWait;
    double lastNearAt, lessonAt;
    UnlockLessons? lessons;
    string? lessonHint;
    double lessonUntil;
    const double LessonLife = 10;

    UnlockLessons? Lessons() =>
        lessons ??= (GetParent() as Game)?.Journey.World is { } w
            ? new UnlockLessons(id => w.Fact("lesson." + id).Truthy, id => w.Facts["lesson." + id] = true)
            : null;

    /// <summary>Each frame of a campaign fight: the calling's skill when it is quiet, the lesson when a fight is next near.</summary>
    void UnlockTick(Battle b)
    {
        if (!b.Campaign || GetParent() is not Game game) return;
        var p = b.Player;
        bool near = b.Combat && p.Alive && b.NearestHostile(p.X, p.Z, FightNear) != null;
        if (near) lastNearAt = b.Time;
        double dt = Math.Clamp(b.Time - lessonAt, 0, 0.5);
        lessonAt = b.Time;
        if (callingWait is { } w && LevelCards.CallingDue(LevelCardUp, b.Time - lastNearAt))
        {
            callingWait = null;
            LevelCard(LevelCards.NewSkill(0, w.Skill));
        }
        double now = Time.GetTicksMsec() / 1000.0;
        if (lessonHint != null && now >= lessonUntil) TakeLessonDown(game, expired: true);
        if (Lessons()?.Tick(near && game.CurrentHint == null && !HudPin.Active, dt) is { } row)
        {
            var t = row.Teach;
            game.SetHint(new Hint("unlock." + row.Id, t.Title, t.Text, t.Key != "" ? [game.KeyLabel(t.Key)] : []));
            lessonHint = "unlock." + row.Id; lessonUntil = now + LessonLife;
        }
    }

    void TakeLessonDown(Game game, bool expired)
    {
        if (game.CurrentHint?.Id == lessonHint) game.SetHint(null);
        lessonHint = null;
        if (expired) lessons?.Expired();
    }

    /// <summary>She used a skill (its id) or swapped ("stance"): its lesson is no longer owed, and its hint comes down.</summary>
    public void UnlockUsed(string id)
    {
        if (Lessons()?.Used(id) == true && GetParent() is Game game) TakeLessonDown(game, expired: false);
    }
}
