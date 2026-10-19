using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Ui;

namespace SurvivorUnchained.Play;

/* The tutorial's callouts, as the game runs them (logic/Play/Teach.cs keeps the line; Callout.cs
 * draws them). A freeze stops the fight until the player answers; Esc skips it. The profile
 * remembers what was seen (Settings.SeenTips); the Tips setting turns them all off. */
public partial class Game
{
    sealed class ProfileMemory : ITeachMemory
    {
        public bool Tips => Settings.Current.Tips;
        public bool Seen(string id) => Settings.Current.SeenTips.Contains(id);
        public void Mark(string id) { if (!Seen(id)) { Settings.Current.SeenTips.Add(id); Settings.Current.Save(); } }
    }

    Teacher? teacher;
    ICalloutView? calloutShown;
    double teachClock;
    bool teachFroze;
    /// <summary>The draft's offers while one is being presented (the callout's card, before the panel is drawn).</summary>
    List<Offer>? teachOffers;

    Teacher Teacher => teacher ??= MakeTeacher();

    Teacher MakeTeacher()
    {
        // --teach-reset: every callout unseen again (test runs may overwrite the owner's profile).
        if (Args.Has("teach-reset")) { Settings.Current.SeenTips.Clear(); Settings.Current.Save(); }
        return new Teacher(new ProfileMemory()) { Log = TeachLog };
    }

    /// <summary>A zone's callout at its moment.</summary>
    public void Teach(Callout c) => Teacher.Offer(c, teachClock, TeachBusy());

    /// <summary>The callout on the screen now (the autopilot answers a freeze).</summary>
    public Callout? Teaching => teacher?.Current;
    /// <summary>Whether a callout waits in the line (the autopilot holds its draught for F10's).</summary>
    public bool TeachWaiting(string id) => teacher?.Queued(id) == true;
    /// <summary>Real seconds it has been up.</summary>
    public double TeachingFor => teacher?.Current != null ? RealNow - teacher.ShownAt : 0;
    static double RealNow => Time.GetTicksMsec() / 1000.0;

    void TeachLog(string what, Callout c, string how)
    {
        if (!Args.Dev) return;
        string real = what is "queued" || (what == "dropped" && teacher?.Current != c) ? "-" : $"{(RealNow - (teacher?.ShownAt ?? RealNow)) * 1000:0}";
        if (what == "shown") real = "0";
        var at = Primary(c);
        string waited = what is "queued" or "shown" or "dropped" ? $" waited={(teacher?.LogWaited is { Length: > 0 } w ? w : "-")}" : "";
        GD.Print($"teach {c.Id} {what} t={Battle?.Time ?? 0:0.0} real={real} kind={c.Kind.ToString().ToLowerInvariant()} target={(at is Vector2 v ? $"{v.X:0},{v.Y:0}" : "-")}{(how != "" ? " how=" + how : "")}{waited}");
    }

    /// <summary>What has the screen, for the line of callouts.</summary>
    Busy TeachBusy()
    {
        var b = Busy.None;
        if (cine != null) b |= Busy.Cinematic;
        if (inTransit || hud.FadeAmount > 0.02f) b |= Busy.Transit;
        if (hudMode == "fall" || Battle?.Player.Alive == false) b |= Busy.Fall;
        if (screens.Current != null || hudMode is "dialogue" or "chest" or "fall" || zone?.Choice != null) b |= Busy.Overlay;
        if (hudMode == "draft") b |= Busy.Draft;
        if (hud.BannerUp && !hud.HoldBanner) b |= Busy.Banner;
        if (hud.SayUp) b |= Busy.Say;
        if (hud.PromptUp) b |= Busy.Prompt;
        if (hud.TipUp) b |= Busy.Hint;
        if (Battle?.DraftOwed == true && hudMode != "draft") b |= Busy.Owed;
        return b;
    }

    /// <summary>A world point on the HUD's canvas, if it is on the screen.</summary>
    Vector2? OnScreen((double X, double Y, double Z) p)
    {
        var w = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
        if (camera.IsPositionBehind(w)) return null;
        var s = camera.UnprojectPosition(w);
        return s.X is > 40 and < 1880 && s.Y is > 40 and < 1040 ? s : null;
    }

    /// <summary>Where a callout points now: its points and areas on the HUD's canvas (none: not there).</summary>
    (List<Vector2> Points, List<Rect2> Areas, bool Gone, int WorldOn) Resolve(Callout c)
    {
        var pts = new List<Vector2>();
        var areas = new List<Rect2>();
        bool gone = false;
        int worldOn = 0;
        var t = c.Target;
        switch (t.Hud)
        {
            case null: break;
            case "chain": pts.Add(new Vector2(960, (Instrument.EyeL.Y + Instrument.EyeR.Y) / 2 + 14)); break;
            case "dash": pts.Add(Instrument.DashAt); break;
            case "draught": pts.Add(Instrument.DraughtAt); break;
            case "art": pts.Add(Instrument.ArtAt); break;
            case "banner": if (hud.BannerUp) areas.Add(hud.BannerArea); break;
            case "cards":
                if (hud.DraftShown is { } dp && dp.CardAreas().ToList() is { Count: > 0 } all)
                    areas.Add(all.Select(x => x.Rect).Aggregate((a, b) => a.Merge(b)));
                break;
            case "card:weapon":
                if (hud.DraftShown is { } dw && dw.CardAreas().FirstOrDefault(x => x.Offer.Kind == OfferKind.Weapon) is { Rect.Size.X: > 0 } wc)
                    areas.Add(wc.Rect);
                break;
            case var s when s.StartsWith("socket:"):
                if (hud.SocketOf(s[7..]) is Vector2 sp) pts.Add(sp);
                break;
        }
        if (t.World != null)
        {
            var world = t.World();
            if (world.Count == 0) gone = true;
            foreach (var w in world) if (OnScreen(w) is Vector2 v) { pts.Add(v); worldOn++; }
        }
        return (pts, areas, gone, worldOn);
    }

    Vector2? Primary(Callout c)
    {
        if (scene == null) return null;
        var (pts, areas, _, _) = Resolve(c);
        return pts.Count > 0 ? pts[0] : areas.Count > 0 ? areas[0].GetCenter() : null;
    }

    Presence Where(Callout c)
    {
        var t = c.Target;
        if (t.Hud == "card:weapon") return teachOffers?.Any(o => o.Kind == OfferKind.Weapon) == true ? Presence.Here : Presence.NotYet;
        if (t.Hud == "cards") return teachOffers is { Count: > 0 } ? Presence.Here : Presence.NotYet;
        if (t.Hud is string s && s.StartsWith("socket:") && hud.SocketOf(s[7..]) == null) return Presence.NotYet;
        if (t.World != null)
        {
            // (several things: here when one of the world's is on the screen; a HUD part alone doesn't count)
            var (_, _, gone, worldOn) = Resolve(c);
            if (gone) return Presence.Gone;
            if (worldOn == 0) return Presence.NotYet;
        }
        return Presence.Here;
    }

    /// <summary>Each frame in play: the line moves on, and what is up is aimed.</summary>
    void UpdateTeach(double dt)
    {
        if (scene == null || Mode != "play") return;
        if (!scene.SimPaused) teachClock += dt;
        TeachHurt(dt);
        var t = Teacher;
        if (hudMode == "draft") teachOffers = offers; else teachOffers = null;
        var was = t.Current;
        var now = t.Update(teachClock, RealNow, TeachBusy(), Where);
        if (was != null && t.Current != was) TeachDown(was);
        if (now != null) TeachUp(now);
        AimCallout();
    }

    double hurtT;
    bool hurtDone;

    /// <summary>--teach-hurt (a scripted run): her health down to 35% once, 10 s of play into the
    /// Prologue's boss, so the draught's callout (F10) is seen.</summary>
    void TeachHurt(double dt)
    {
        if (hurtDone || !Args.Has("teach-hurt") || scene!.SimPaused) return;
        if (zone is not Zones.Prologue { Now: Zones.Prologue.Stage.Boss } || Battle is not { } b || !b.Player.Alive) return;
        hurtT += dt;
        if (hurtT < 10) return;
        hurtDone = true;
        b.Player.Hp = Math.Min(b.Player.Hp, b.MaxHp * 0.35);
        if (Args.Dev) GD.Print($"teach hurt t={b.Time:0.0} hp={b.Player.Hp:0}/{b.MaxHp:0} draughts={Journey.Draughts}");
    }

    void TeachUp(Callout c)
    {
        Act? answer = c.Answer != null && Enum.TryParse<Act>(c.Answer, true, out var a) ? a : null;
        if (c.Kind == CalloutKind.Freeze)
        {
            scene!.SimPaused = true;
            teachFroze = true;
            controls.ClearLatches();
            if (c.Target.Banner is { } ban) { hud.Announce(ban); hud.HoldBanner = true; }
        }
        hud.HoldTip = true;
        var view = new Ui.Callout();
        hud.Callout(view);
        view.Show(new CalloutLook(c.Title, c.Line, c.Kind, answer, c.Kind == CalloutKind.Freeze ? answer ?? Act.Interact : null,
            answer != null ? c.Title.ToLowerInvariant() switch { "dash" => "to dash", "draught" => "to drink", _ => "to use it" } : "to go on"));
        calloutShown = view;
        AimCallout();
        // (--shot: a frame of each, and a freeze holds until it is taken)
        if (Args.Has("shot")) Shots.Want("teach_" + c.Id, 0.9);
    }

    void TeachDown(Callout c)
    {
        calloutShown?.TakeDown();
        calloutShown = null;
        hud.HoldTip = false;
        hud.HoldBanner = false;
        if (teachFroze)
        {
            teachFroze = false;
            if (scene != null && hudMode == null && screens.Current == null && cine == null) scene.SimPaused = false;
        }
    }

    void AimCallout()
    {
        if (calloutShown == null || teacher?.Current is not { } c) return;
        var (pts, areas, _, _) = Resolve(c);
        calloutShown.Aim(new CalloutAim(pts, areas, c.Kind == CalloutKind.Panel ? hud.DraftShown?.TipArea : null));
    }

    /// <summary>A key while a freeze is up: its answer goes on (and happens), any other key but
    /// moving goes on from one that asks nothing, Esc skips it. True: the key is spent.</summary>
    bool TeachKey(Act a)
    {
        if (teacher?.Current is not { Kind: CalloutKind.Freeze } c) return false;
        double real = RealNow;
        if (a is Act.Pause or Act.Cancel) { teacher.Close("skip", real); TeachDown(c); controls.ClearLatches(); return true; }
        if (!teacher.CanContinue(real)) return true;
        Act? answer = c.Answer != null && Enum.TryParse<Act>(c.Answer, true, out var an) ? an : null;
        if (answer is Act want)
        {
            if (a != want) return true;
            teacher.Close("key", real);
            TeachDown(c);
            // The press goes through: the dash rolls (its latch is kept), the draught is drunk, the art cast.
            return false;
        }
        if (a is Act.Up or Act.Down or Act.Left or Act.Right) return true;
        teacher.Close("key", real);
        TeachDown(c);
        controls.ClearLatches();
        return true;
    }

    /// <summary>The draft is presented: a panel callout on it ends with the panel it was on, and the
    /// next can come up on this one. True: one speaks on this panel (the tip's place is its).</summary>
    bool TeachPanel(List<Offer> list)
    {
        if (teacher == null || scene == null) return false;
        if (teacher.Current is { Kind: CalloutKind.Panel } up) { teacher.Close("picked", RealNow); TeachDown(up); }
        teachOffers = list;
        var was = teacher.Current;
        var now = teacher.Update(teachClock, RealNow, TeachBusy() | Busy.Draft, Where);
        if (was != null && teacher.Current != was) TeachDown(was);
        if (now != null) TeachUp(now);
        return teacher.Current is { Kind: CalloutKind.Panel };
    }

    /// <summary>The place is left: what waits is let go, what is up comes down.</summary>
    void TeachLeave()
    {
        if (teacher == null) return;
        var up = teacher.Current;
        teacher.Clear(teachClock);
        if (up != null) TeachDown(up);
    }
}
