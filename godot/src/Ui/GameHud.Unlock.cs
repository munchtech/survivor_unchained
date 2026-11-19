using System;
using System.Collections.Generic;
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

    readonly List<(Vector3 A, Vector3 B, float R)> spanBuf = new();
    readonly List<Rect2> underBuf = new();

    /// <summary>Each frame: the level card's keep-clear rects (her, feet to 1.8 m up, and every live telegraph mark's ground circle or
    /// lane, projected to the screen) and its cover for the edge marks (boss and elite skulls, the boss pointer, the lamp pointers, the
    /// loot names), which hide where the card is, as the goal pins do.</summary>
    public void CardUnder(Battle? b, Camera3D cam, SurvivorUnchained.View.BattleFx fx)
    {
        var cover = LevelCardArea;
        edges.Cover = cover; ground.Cover = cover;
        if (bossPointer != null) bossPointer.Cover = cover;
        if (postPointers != null) postPointers.Cover = cover;
        if (levelCard == null) return;
        levelCard.Under = () => underBuf;
        underBuf.Clear();
        levelCard.HerIn = false;
        if (cover == null || b == null || !b.Combat) return;
        var p = b.Player;
        float py = (float)fx.GroundAt(p.X, p.Z);
        levelCard.Clock = b.Time;
        Grow(cam, new Vector3((float)p.X, py, (float)p.Z), 0.45f, 1.8f);
        levelCard.HerIn = underBuf.Count > 0;
        spanBuf.Clear();
        fx.TelegraphSpans(spanBuf);
        foreach (var (a, c, r) in spanBuf)
        {
            var box = Bound(cam, a, r);
            if (box is { } b0) { var b1 = Bound(cam, c, r); underBuf.Add(b1 is { } bb ? b0.Merge(bb) : b0); }
        }
    }

    void Grow(Camera3D cam, Vector3 feet, float r, float height)
    {
        var f = Bound(cam, feet, r);
        var h = Bound(cam, feet + new Vector3(0, height, 0), r);
        if (f is { } fr) underBuf.Add(h is { } hr ? fr.Merge(hr) : fr);
    }

    /// <summary>The screen box of the horizontal circle round a point (its centre and eight on the rim); null when behind the lens.</summary>
    static Rect2? Bound(Camera3D cam, Vector3 c, float r)
    {
        if (cam.IsPositionBehind(c)) return null;
        var first = cam.UnprojectPosition(c);
        var box = new Rect2(first, Vector2.Zero);
        for (int i = 0; i < 8; i++)
        {
            float a = i * Mathf.Pi / 4;
            var q = c + new Vector3(Mathf.Cos(a) * r, 0, Mathf.Sin(a) * r);
            if (!cam.IsPositionBehind(q)) box = box.Expand(cam.UnprojectPosition(q));
        }
        return box;
    }

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
        // (den r19 lead, shots only) --no-lessons: no lesson or Lamps prompt over a judged frame
        if (Args.Has("no-lessons")) return;
        if (lessonHint != null && now >= lessonUntil) TakeLessonDown(game, expired: true);
        // (a lesson waits for its card to leave: the card says what opened, the lesson then says how, never both at once)
        if (Lessons()?.Tick(near && !LevelCardUp && game.CurrentHint == null && !HudPin.Active, dt) is { } row)
        {
            var t = row.Teach;
            game.SetHint(new Hint("unlock." + row.Id, t.Title, UnlockLessons.TextFor(row, game.KeyLabel), t.Key != "" ? [game.KeyLabel(t.Key)] : []));
            lessonHint = "unlock." + row.Id; lessonUntil = now + LessonLife;
        }
        // (the one prompt that the Lamps tree exists: the first held point, once per save; never over a card, a choice, another hint)
        else if (game.CurrentHint == null && !LevelCardUp && !HudPin.Active && LampsTeach.Take(game.Journey.Ch, game.Journey.World, choice != null))
        {
            game.SetHint(new Hint("unlock." + LampsTeach.Id, LampsTeach.Title, LampsTeach.TextFor(game.KeyLabel, SurvivorUnchained.Rpg.LampBook.Spare(game.Journey.Ch, game.Journey.World)), [game.KeyLabel(LampsTeach.Key)]));
            lessonHint = "unlock." + LampsTeach.Id; lessonUntil = now + LessonLife;
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
        // (--lesson-keep, shots only: the shown lesson stays up through the bot's own use of the key, so its frame can be taken)
        if (Args.Has("lesson-keep")) return;
        if (Lessons()?.Used(id) == true && GetParent() is Game game) TakeLessonDown(game, expired: false);
    }
}
