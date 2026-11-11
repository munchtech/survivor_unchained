using System;
using Godot;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sound;
using SurvivorUnchained.Storybook;
using SurvivorUnchained.Ui;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* The storybook in the game (docs/storybook/README.md, "Running it"): SB00
 * opens a new journey between creation and C01, and --storybook ID plays one
 * alone over black for pictures and captures. */
public partial class Game
{
    StoryPlayer? storybook;
    /// <summary>The zone (or scene) a storybook was asked in, while it fades in (SU-032): it owns the pause from
    /// the ask, not from when its player exists. Null: none pending.</summary>
    object? storyAsked;
    /// <summary>A storybook up or fading in holds the world's pause (InputOwner).</summary>
    bool StoryHolds => storybook != null || storyAsked != null;
    /// <summary>The bars a storybook ended under, full and black, for the cinematic
    /// that follows it on the cut (C01) to take over, so nothing moves at the seam.</summary>
    CinemaBars? storyBars;
    bool beginning, storyEnded, quickStoried;
    /// <summary>When the storybook ended (wall seconds; 0: none pending), to cut the silence C01 opens on by the load.</summary>
    double storyDoneAt;

    /// <summary>C01 starting on a storybook's bars: its opening black shot loses the time the zone took to stand up
    /// under the black (only after SB00 played to its end: its "durs" for sb00.ended), so the seam stays the doc's.</summary>
    void CutStorySeam(SurvivorUnchained.Cinema.CineFile file)
    {
        if (storyDoneAt <= 0 || !World.Facts.ContainsKey("sb00.ended")) { storyDoneAt = 0; return; }
        double load = Time.GetTicksMsec() / 1000.0 - storyDoneAt;
        storyDoneAt = 0;
        if (file.Shots.Count == 0) return;
        double cut = StoryTimeline.CutSeam(file.Shots[0], load, 1.3);
        GD.Print($"storybook: the zone stood up in {load:0.00}s under the black; {file.Id} shot {file.Shots[0].Id} cut by {cut:0.00}s");
    }

    /// <summary>At a storybook's end, into the Low Ford, the time noted for C01's seam (CutStorySeam).</summary>
    void WhenStoryBuilt(Action fn)
    {
        storyDoneAt = Time.GetTicksMsec() / 1000.0;
        fn();
    }

    public bool InStorybook => storybook != null;

    static bool StoryExists(string id) => FileAccess.FileExists($"res://data/storybook/{id}.json");

    /// <summary>A new journey opens on SB00 when there is one; --nocine and quick starts go without, as they go without C01.</summary>
    static bool OpensOnStory => StoryExists("sb00") && StoryLive("sb00") && !Args.Has("nocine");

    /// <summary>Whether the storybook says it is live (false on any error).</summary>
    static bool StoryLive(string id)
    {
        try { return StoryFile.Load(id).Live; }
        catch { return false; }
    }

    /// <summary>The storybook's lines read the same for every survivor: a blank one will do.</summary>
    static Ctx StoryCtx() => new(WorldState.Fresh(1), new CharacterData());

    StoryHost Host() => new(voice, sound, () => controls.Held(Act.Interact) || controls.Held(Act.Pause), StoryCtx());

    /// <summary>--storybook ID [--sb-from S] [--sb-shots T1,T2]: that storybook at once over black, and quit at its end.</summary>
    void StoryAlone(string id)
    {
        StoryFile f;
        try { f = StoryFile.Load(id); }
        catch (Exception e) { GD.PushError($"storybook: {id} not played ({e.Message})"); QuitPath.Request(GetTree(), 1, "storybook not played"); return; }
        storybook = new StoryPlayer(f, Host(), _ => { storybook = null; QuitPath.Request(GetTree()); }, null, Args.Num("sb-from", 0));
        AddChild(storybook);
        // The HUD's fade starts black; the storybook draws its own.
        hud.Fade(0, 0);
    }

    /// <summary>The score with no place under it (a storybook played alone): its own mood, no air.</summary>
    void StorySound(double dt) =>
        sound.Update(dt, new SoundState("storybook", null, TimeOfDay.Night, 0, 0, null, false, null, null, null));

    /// <summary>
    /// Creation confirmed, SB00 first (docs/story/storybook/sb00_stay_where_they_reach.md,
    /// "Handover to C01"): creation's last frame holds 0.5 s and goes to black over
    /// 0.8 s with the title music; the storybook plays from black; at its end the zone
    /// is entered under the black and C01 takes the bars, and plays without its
    /// drowning (fact sb00.ended) unless the storybook was skipped.
    /// </summary>
    void BeginWithStory(CreationChoice c)
    {
        beginning = true;
        screens.Close();
        Wait(0.5, () =>
        {
            hud.Fade(1, 0.8);
            sound.CineMood = Mood.Silence;
            sound.CineIntensity = 0;
        });
        Wait(1.32, () =>
        {
            StoryFile f;
            try { f = StoryFile.Load("sb00"); }
            catch (Exception e) { GD.PushError($"storybook: sb00 not played ({e.Message})"); AfterStory(c, true, null); return; }
            var bars = new CinemaBars();
            AddChild(bars);
            bars.Frame(1, 1);
            // Nothing of the world is drawn under it.
            GetViewport().Disable3D = true;
            storybook = new StoryPlayer(f, Host(), skipped => { storybook = null; WhenStoryBuilt(() => AfterStory(c, skipped, bars)); }, bars, Args.Num("sb-from", 0));
            AddChild(storybook);
            hud.Fade(0, 0);
        });
    }

    void AfterStory(CreationChoice c, bool skipped, CinemaBars? bars)
    {
        storybook = null;
        GD.Print($"storybook: into the Low Ford at wall {Time.GetTicksMsec() / 1000.0:0.00}s");
        GetViewport().Disable3D = false;
        EndCreate();
        storyEnded = !skipped;
        Begin(c);
        draft = null;
        screens.Close();
        storyBars = bars;
        EnterZone("lowford", null, new Arrival(Fire.X + 1.4, Fire.Y + 1.0, Math.PI * 0.08));
        Save("new");
        beginning = false;
        Unbar();
    }

    /// <summary>--cines on a quick start into the prologue: the storybook over black first, then the
    /// quick start under its black, C01 taking the bars.</summary>
    bool QuickStory()
    {
        if (quickStoried || !Args.Has("cines") || (Args.Get("zone") ?? "lowford") != "lowford" || !OpensOnStory || Args.Has("load")) return false;
        quickStoried = true;
        StoryFile f;
        try { f = StoryFile.Load("sb00"); }
        catch (Exception e) { GD.PushError($"storybook: sb00 not played ({e.Message})"); return false; }
        var bars = new CinemaBars();
        AddChild(bars);
        bars.Frame(1, 1);
        storybook = new StoryPlayer(f, Host(), skipped =>
        {
            storybook = null;
            WhenStoryBuilt(() =>
            {
                storyEnded = !skipped;
                storyBars = bars;
                GD.Print($"storybook: into the quick start at wall {Time.GetTicksMsec() / 1000.0:0.00}s");
                Quick();
                Unbar();
            });
        }, bars, Args.Num("sb-from", 0));
        AddChild(storybook);
        hud.Fade(0, 0);
        return true;
    }

    /// <summary>C01 did not take the bars (it could not play): out of the black into play.</summary>
    void Unbar()
    {
        if (storyBars != null)
        {
            storyBars.QueueFree();
            storyBars = null;
            hud.Fade(1, 0);
            hud.Fade(0, 0.8);
            sound.CineMood = null;
        }
    }

    /// <summary>The bars a storybook left, for the cinematic starting now (null: none).</summary>
    /// <summary>IZoneHost (M6): a storybook mid-zone (sb_dawn, the Low Ford's dawn page): the world held and faded under
    /// it, the page over its own bars (fading in from black and out to it), then the world back and `then`. Where no
    /// storybook can play (--nocine, a quick start without --cines, one already up, a cinematic, no such file) it goes on.</summary>
    public void Storybook(string id, Action then)
    {
        if (scene == null || StoryHolds || cine != null || Args.Has("nocine") || (quick && !Args.Has("cines")) || !StoryExists(id)) { then(); return; }
        StoryFile f;
        try { f = StoryFile.Load(id); }
        catch (Exception e) { GD.PushWarning($"storybook: {id} not played ({e.Message})"); then(); return; }
        if (!f.Live) { then(); return; }
        if (Shots.On("teach")) { Shots.Want("story_" + id + "_a", 2.0); Shots.Want("story_" + id + "_b", 6.0); }
        // (M6 A3) A storybook pays the experience stones still on their way to her.
        scene.Battle?.PayXpStones();
        scene.SimPaused = true;
        scene.Hold = 1;
        hud.HoldToasts = true;
        hud.HoldTip = true;
        hud.ClearBanner();
        hud.Prompt(promptShown = null);
        controls.ClearLatches();
        hud.Fade(1, 0.6);
        GD.Print($"storybook: {id} mid-zone at wall {Time.GetTicksMsec() / 1000.0:0.00}s");
        object askedIn = (object?)zone ?? scene;
        storyAsked = askedIn;
        Wait(0.6, () =>
        {
            // (SU-032) The zone left during the fade (LeaveZone let the ask go): no page, and no `then`, which drives
            // that zone (the Prologue's dawn: the Flare taken, the lamp given, the dawn and C04 A on a place gone).
            if (!ReferenceEquals(storyAsked, askedIn) || !InputOwner.PageStillWanted(askedIn, (object?)zone ?? scene))
            {
                GD.Print($"storybook: {id} dropped, its zone left during the fade");
                return;
            }
            storyAsked = null;
            // (M6) The page plays over bars of its own, full and black, as SB00 does: the HUD's black (above every
            // page) goes the moment they are up. Left up, it hid the page, the film after and the whole day (run m6r1).
            // The player is handed them (it opens their black over its page): its own bars under these hid it (m6r2).
            var bars = new CinemaBars();
            AddChild(bars);
            bars.Frame(1, 1);
            storybook = new StoryPlayer(f, Host(), _ =>
            {
                storybook = null;
                if (scene != null)
                {
                    scene.Hold = 0;
                    if (screens.Current == null && cine == null && teacher?.Current is not { Kind: CalloutKind.Freeze }) scene.SimPaused = false;
                }
                hud.HoldToasts = false;
                hud.HoldTip = false;
                controls.ClearLatches();
                storyBars = bars;
                then();
                // (a cinematic `then` started took the bars as its own; else they go and the world fades back in)
                Unbar();
            }, bars);
            AddChild(storybook);
            hud.Fade(0, 0);
        });
    }

    CinemaBars? TakeStoryBars()
    {
        var b = storyBars;
        storyBars = null;
        return b;
    }
}
