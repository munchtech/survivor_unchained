using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Sound;
using SurvivorUnchained.Ui;
using SurvivorUnchained.View;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/// <summary>
/// The game: the one thing that knows about everything else (the web game's
/// game/game.ts). It keeps the journey (the character and the world), decides
/// which place is loaded and starts its fight from the survivor's gear, sends
/// what the fight says to the interface and to the world's memory, runs the
/// prompt for what is near, the conversations and the level-up draft, the
/// screens over the game, the fade between places and the fall, and saves.
///
/// Modes: the title (a fire on the Low Ford road, a stranger by it), making
/// a survivor by the same fire, and play. This file is the host the zones
/// talk to and the frame; GameFront.cs the title and creation, GameMenus.cs
/// the screens, the draft and conversations.
///
/// Options (after `--`): --quick CALLING [--zone ID --time T --at X,Z] (--zone arena: one of the Wayfinder's)
/// starts a stock survivor straight away; --continue the last journey;
/// --auto a crude player (Autopilot.cs); --log S a line every S seconds.
/// </summary>
public partial class Game : Node, IZoneHost
{
    public Journey Journey { get; private set; } = null!;
    public Battle? Battle => scene?.Battle;
    public IZoneLook Look => scene!;
    public Random Rng { get; } = new();
    public Hint? CurrentHint { get; private set; }
    public ZoneRuntime? Zone => zone;
    public WorldScene? Scene => scene;
    public GameHud Hud => hud;
    public Saves Saves => saves;
    public bool InTransit => inTransit;
    /// <summary>What has the screen: the draft, a conversation, or an overlay (null: play).</summary>
    public string? Overlay => hudMode ?? screens.Current?.Kind;
    public string Mode { get; private set; } = "title";

    Controls controls = null!;
    GameHud hud = null!;
    Screens screens = null!;
    Synth synth = null!;
    SoundBridge sound = null!;
    VoiceOver voice = null!;
    bool bossUp;
    Atmosphere air = null!;
    Camera3D camera = null!;
    FollowCamera cam = null!;
    WorldScene? scene;
    ZoneRuntime? zone;
    Saves saves = null!;
    Interactable? near;
    /// <summary>What the prompt is for now (the autopilot waits for the right one before it presses).</summary>
    public string? Prompted => near?.Id;
    PromptView? promptShown;
    string? hudMode;
    readonly List<(double T, Action Fn)> later = new();
    bool inTransit;
    double autosaveT, fogT, hudT, draftWait, reportT;
    Autopilot? auto;

    public override void _Ready()
    {
        // The colour sheets as Godot should have them, before any model loads.
        SurvivorUnchained.View.Textures.Mend();
        // --icons: every item photographed afresh (user://icons), then quit.
        if (Args.Has("icons"))
        {
            SetProcess(false);
            ItemPhotos.Open(this, quitAfter: true);
            return;
        }
        ItemPhotos.Open(this);
        controls = new Controls();
        AddChild(controls);
        camera = new Camera3D { Fov = 34, Near = 0.5f, Far = 1400, Current = true };
        AddChild(camera);
        cam = new FollowCamera(camera);
        // --cam D: the camera this far off (closer pictures of the crowd).
        if (Args.Has("cam")) cam.Distance = cam.TargetDistance = (float)Args.Num("cam", 23);
        camHome = (cam.Pitch, cam.TargetDistance);
        air = new Atmosphere();
        AddChild(air);
        hud = new GameHud();
        AddChild(hud);
        screens = new Screens();
        AddChild(screens);
        AddChild(new Shots());
        synth = new Synth();
        AddChild(synth);
        if (Perf.On) MeasureWith(new Perf());
        sound = new SoundBridge(synth);
        voice = new VoiceOver();
        AddChild(voice);
        // The interface: every button ticks under the pointer and clicks.
        GetTree().NodeAdded += n => { if (n is BaseButton bb) Sounded(bb); };
        saves = new Saves(ProjectSettings.GlobalizePath("user://saves"));
        controls.On(OnAction);
        // Prompts follow the device in hand: a screen, the HUD, the draft redraw with its keys.
        controls.DeviceChanged += () => { screens.Current?.Refresh(); hud.DeviceChanged(); };
        UiArt.Cursors();
        if (Args.Has("auto")) auto = new Autopilot(this) { Idle = Args.Get("auto") == "idle" };
        Settings.Current.ApplyWindow();
        ApplySettings();
        if (Args.Has("continue") && saves.LastSlot() is int slot) Continue(slot);
        else if (Args.Has("quick") || Args.Has("zone")) Quick();
        else
        {
            ShowTitle();
            // --new: straight to making a survivor (pictures of it).
            if (Args.Has("new")) NewJourney();
        }
    }

    /// <summary>A stock survivor straight into the game (tools and tests).</summary>
    void Quick()
    {
        quick = true;
        var arch = Args.Get("quick") is string q && q is "warden" or "reaver" or "arcanist" or "stalker" ? q : "warden";
        var a = Callings.Archetype(arch);
        Begin(new CreationChoice
        {
            // --palette ID: the calling's colours (its first, undyed, by default).
            Name = Args.Get("name") ?? "Wren", Archetype = arch, Background = Args.Get("bg") ?? "hunter",
            Palette = a.Palettes.Any(p => p.Id == Args.Get("palette")) ? Args.Get("palette")! : a.Palettes[0].Id,
            WeaponItem = Args.Get("weapon") ?? a.Weapons[0], Ability = a.Abilities[0],
            // --sex female [--hair STYLE --figure F --skin ID]: a woman survivor.
            Sex = Args.Get("sex") == "female" ? Sex.Female : null, HairStyle = Args.Get("hair"), Skin = Args.Get("skin"),
            Figure = Args.Has("figure") ? Args.Num("figure", 1) : null,
        });
        // --art ID[:FACET+FACET]: that art in hand, learned and (with facets) mastered.
        if (Args.Get("art") is string art)
        {
            var parts = art.Split(':');
            var ch = Journey.Ch;
            ArtBook.Learn(ch, parts[0]);
            ArtBook.Hold(ch, parts[0]);
            if (parts.Length > 1)
            {
                ArtBook.Grow(ch, parts[0], Content.Abilities.RankXp[^1]);
                foreach (var f in parts[1].Split('+')) ArtBook.Choose(ch, parts[0], f);
            }
        }
        // --items A,B[:RARITY],C*N: those things in the pack from the start, N of them for a
        // stack (pictures of the pack, the shop, the forge with a stocked pouch).
        if (Args.Get("items") is string items)
            foreach (var spec in items.Split(','))
            {
                var parts = spec.Split(':');
                var idq = parts[0].Split('*');
                int qty = idq.Length > 1 && int.TryParse(idq[1], out var nq) ? nq : 1;
                Journey.GiveItem(idq[0], qty, parts.Length > 1 && int.TryParse(parts[1], out var r) ? r : null);
            }
        // --gold N: that much gold in the purse (pictures of a counter with money to spend).
        if (Args.Has("gold")) Journey.Ch.Gold = Args.Num("gold", 0);
        // --xp N: that much experience at once (pictures of the self with points to spend).
        if (Args.Has("xp")) Character.GainXp(Journey.Ch, Args.Num("xp", 0));
        var z = Args.Get("zone") ?? "lowford";
        Arrival? at = null;
        if (Args.Get("at") is string s)
        {
            var p = s.Split(',');
            at = new Arrival(double.Parse(p[0], System.Globalization.CultureInfo.InvariantCulture), double.Parse(p[1], System.Globalization.CultureInfo.InvariantCulture));
        }
        // --zone arena [--offer 0|1|2 --people ID --oaths A,B --tier T]: straight into one of the
        // Wayfinder's arenas (and back to the table after).
        if (z == "arena")
        {
            var o = SurvivorUnchained.Maps.MapOffers.Today(World.Day, 1, 0)[(int)Args.Num("offer", 0)];
            if (Args.Get("people") is string pe) o = o with { People = pe };
            if (Args.Get("oaths") is string oa) o.Spec.Oaths = oa.Split(',', StringSplitOptions.RemoveEmptyEntries).ToList();
            if (Args.Has("tier")) o.Spec.Tier = (int)Args.Num("tier", 1);
            var at0 = Waystation.AtTable;
            var spec = Arenas.FromTable(o, "waystation", at0.X, at0.Z, at0.Facing);
            // --boss DEF[:NAME]: a story's foe at the half hour (pictures of Grimtunnel, of Greymuzzle).
            if (Args.Get("boss") is string bo) { var bp = bo.Split(':'); spec.Boss = bp[0]; if (bp.Length > 1) spec.BossName = bp[1].Replace('_', ' '); }
            // --spare: the story lets it go (Greymuzzle spared).
            spec.Spare = Args.Has("spare");
            // --story: told as a story's night (twenty minutes, over at its boss's fall), for pictures of its end.
            if (Args.Has("story")) { spec.Story = true; spec.Minutes = 20; }
            Arenas.Begin(World, spec);
        }
        if (z != "lowford")
        {
            // Skipping ahead: the prologue counts as done.
            World.Facts["prologue.done"] = true;
            World.Time = Enum.TryParse<TimeOfDay>(Args.Get("time") ?? "day", true, out var t) ? t : TimeOfDay.Day;
            EnterZone(z, "lowford", at);
        }
        else EnterZone(z, null, at);
        hud.Fade(0, 0.5);
        // --cine ID: that cinematic played here at once (pictures of it, its previs).
        if (Args.Get("cine") is string cid && cine == null) Cinematic(cid);
        Save("new");
        // --pull T: the table's first arena taken T seconds in (pictures of the pull).
        if (Args.Has("pull")) Wait(Args.Num("pull", 1), () => SetOut(SurvivorUnchained.Maps.MapOffers.Today(World.Day, 1, 0)[0]));
    }

    /// <summary>A journey begun: the character, the world, a slot to keep it in.</summary>
    void Begin(CreationChoice c)
    {
        Journey = Journey.Begin(c, (uint)Rng.Next());
        Journey.Slot = FreeSlot();
        Hook();
    }

    int FreeSlot()
    {
        var used = saves.Slots().Select(s => s.Slot).ToHashSet();
        for (int i = 0; i < Saves.SlotCount; i++) if (!used.Contains(i)) return i;
        return saves.Slots().OrderBy(s => s.SavedAt).First().Slot;
    }

    void Hook()
    {
        Journey.OnToast = Toast;
        Journey.OnAnnounce = Announce;
        Journey.OnTouch = () => screens.Current?.Refresh();
    }

    /// <summary>What the player has set, applied now.</summary>
    public void ApplySettings()
    {
        var s = Settings.Current;
        s.ApplyWindow();
        cam.ShakeScale = s.ShakeLevel;
        if (scene != null) { scene.Fx.Gore.Level = s.GoreLevel; scene.Hitstop = s.Hitstop; }
        Graphics.Apply(s, air, GetViewport(), scene);
        AudioServer.SetBusVolumeDb(0, s.Volume <= 0 ? -80 : Mathf.LinearToDb(s.Volume));
        voice?.Apply();
    }

    public string Key(Act a) => controls.KeyLabel(a);

    static void Sounded(BaseButton b)
    {
        b.MouseEntered += () => { if (!b.Disabled) Sfx.Hover(); };
        b.Pressed += Sfx.Click;
        b.GuiInput += e => { if (b.Disabled && e is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Left }) Sfx.Deny(); };
    }

    /* ------------------------------------------------------------ zones -- */

    SurvivorUnchained.Maps.MapBuild? currentMap;
    (float Pitch, float Distance) camHome;

    /// <summary>One of the Wayfinder's maps taken: its arena, and back to the table after.</summary>
    public void SetOut(SurvivorUnchained.Maps.MapOffer o)
    {
        // The table draws fresh maps once one is taken.
        World.Facts["map.drawn"] = World.Fact("map.drawn").Number + 1;
        var p = Battle?.Player;
        EnterArena(Arenas.FromTable(o, zone?.Id ?? "waystation", p?.X ?? 0, p?.Z ?? 0, p?.Facing ?? 0));
    }

    /// <summary>A lost story fight, taken again from the table.</summary>
    public void Rematch(ArenaSpec spec)
    {
        var p = Battle?.Player;
        EnterArena(Arenas.Again(spec, zone?.Id ?? "waystation", p?.X ?? 0, p?.Z ?? 0, p?.Facing ?? 0));
    }

    /// <summary>Pulled into an ember arena. The journey is saved first, where
    /// the survivor stands: an arena left by quitting is as if never begun.</summary>
    public void EnterArena(ArenaSpec spec)
    {
        if (inTransit || zone is ArenaRun) return;
        CloseOverlay();
        Save("arena");
        Arenas.Begin(World, spec);
        Travel("arena", spec.Name, spec.Sub != "" ? spec.Sub : "Ember arena", null, pull: true);
    }

    /// <summary>The arena is over: what came of it, and then back to the story.</summary>
    public void ArenaOver(ArenaResult result)
    {
        if (scene == null) return;
        hudMode = null;
        hud.Draft(null);
        screens.Show(new ArenaResultScreen(this, result));
        scene.SimPaused = true;
        controls.Captured = true;
        hud.Prompt(promptShown = null);
    }

    /// <summary>Out of the arena, to where the story left off.</summary>
    public void LeaveArena(ArenaResult result)
    {
        var s = result.Spec;
        // A tome left blank is written with the first of what it offered.
        if (result.Inscribed == null && result.TomeChoices.Count > 0) Arenas.Inscribe(Journey, result, result.TomeChoices[0]);
        // The result stays up until the fade has gone dark: closed first, the emptied field showed
        // between it and the road.
        bool leaving = !inTransit;
        Travel(s.ReturnZone, null, null, new Arrival(s.ReturnX, s.ReturnZ, s.ReturnFacing));
        if (leaving) Wait(0.8, () => screens.Close());
    }

    ZoneRuntime Make(string id, ZoneMeta meta) => id switch
    {
        "lowford" => new Prologue(this, meta),
        "waystation" => new Waystation(this, meta),
        "verge" => new Verge(this, meta),
        "arena" => new ArenaRun(this, currentMap!, World.Arena!),
        _ => throw new ArgumentException($"no zone {id}"),
    };

    void LeaveZone()
    {
        later.Clear();
        // A chest opening does not outlive its place.
        chestsWaiting.Clear();
        if (chestShown != null) { chestShown.QueueFree(); chestShown = null; if (hudMode == "chest") hudMode = null; }
        // A cinematic does not outlive its place.
        if (cine != null) { var c = cine; cine = null; c.Finish(); }
        zone?.Dispose();
        zone = null;
        if (scene != null) { scene.QueueFree(); RemoveChild(scene); }
        scene = null;
        figure = null;
        near = null;
        hud.Prompt(promptShown = null);
        SetBoss(null);
        hud.Hint(CurrentHint = null);
        hud.Objectives(new());
        cam.FocusOverride = null;
    }

    /// <summary>A place to look at (the title's fire), with nothing happening in it yet.</summary>
    WorldScene Stage(string id)
    {
        LeaveZone();
        // An arena is made from its seed each time it is entered.
        ZoneData data;
        if (id == "arena") { currentMap = SurvivorUnchained.Maps.MapGen.Generate(World.Arena!.Map); data = new ZoneData(currentMap); }
        else { currentMap = null; data = new ZoneData(id); }
        scene = new WorldScene(data, cam);
        AddChild(scene);
        scene.Move = () => auto?.Move ?? (controls.Captured ? (0, 0) : (controls.MoveX, controls.MoveZ));
        scene.Pressed = a => (auto?.Take(a) ?? false) || (!controls.Captured && controls.Pressed(a));
        scene.OnStep = dt => { if (cine is not { ZoneHeld: true }) zone?.Step(dt); };
        scene.OnEvents = OnEvents;
        ApplySettings();
        return scene;
    }

    public void EnterZone(string id, string? from, Arrival? at = null)
    {
        // The title's stage is the prologue's place: begun there, it is kept.
        // An arena is only ever entered from the story: one left behind is over.
        if (id != "arena") World.Arena = null;
        else if (World.Arena == null) { id = "waystation"; at = Waystation.AtTable; }
        ulong t0 = Time.GetTicksUsec();
        if (scene == null || scene.Data.Id != id || scene.Battle != null) Stage(id);
        else RemoveFigure();
        Perf.Lap("the rest of the stage (lights, fires)");
        zone = Make(id, scene!.Data.Meta);
        var time = zone.TimeOf(World);
        air.Set(zone.AtmosphereFor(time));
        scene.View.SetNight(time == TimeOfDay.Night);
        Perf.Lap("the zone's runtime and its air");
        EnterPlay(zone, from, at);
        Perf.Lap("play: the crowd's kinds made ready (bakes)");
        // --perf: how long the place took to stand up (the frame it happens in holds that long).
        if (Perf.On) GD.Print($"perf zone {id} built in {(Time.GetTicksUsec() - t0) / 1000.0:0} ms (at {Time.GetTicksMsec() / 1000.0:0.0}s since launch)");
    }

    void EnterPlay(ZoneRuntime z, string? from, Arrival? at)
    {
        Mode = "play";
        hudMode = null;
        screens.Close();
        hud.ShowPlay(true);
        scene!.SimPaused = false;
        showing = false;
        scene.Showcase = null;
        var start = at ?? z.ArrivalFrom(from);
        var meta = scene.Data.Meta;
        var b = Journey.StartBattle(z.Combat, meta.Collision(), scene.HeightAt, start.X, start.Z, start.Facing, (uint)Rng.Next(), arena: z is ArenaRun, ember: z.Ember);
        Perf.Lap("play: the fight begun");
        // An arena is seen from higher and further out: the whole of the fight.
        var (pitch, dist) = z.Camera is var (cp, cd) ? (Mathf.DegToRad((float)cp), (float)cd) : camHome;
        // --cam still wins: it is for close pictures, arenas included.
        if (Args.Has("cam")) dist = (float)Args.Num("cam", dist);
        cam.Pitch = pitch;
        cam.Distance = cam.TargetDistance = dist;
        scene.StartBattle(b, Loadouts.Of(Journey.Ch));
        Perf.Lap("play: the survivor stood up");
        HookBattle(b);
        z.Begin(b);
        Perf.Lap("play: the zone begun (its people, its pieces)");
        scene.Crowd.Prepare(z.Creatures.Select(c => Content.Enemies.Get(c).Visual));
        hud.ZoneInfo(z.Name, z.Region, World.Day, z.TimeOf(World));
        World.Facts["player.zone"] = z.Id;
    }

    void HookBattle(Battle b)
    {
        // The zone's hooks as they are when called (its boss's are set only when the boss comes).
        var zh = zone!.Hooks;
        var h = BattleHooks.Following(zh);
        h.OnKill = (e, byPlayer) => { Journey.Killed(e, byPlayer); zh.OnKill?.Invoke(e, byPlayer); };
        h.OnPickup = p => (zh.OnPickup == null || zh.OnPickup(p)) && Journey.PickedUp(p);
        h.OnPlayerDeath = killer =>
        {
            if (zh.OnPlayerDeath?.Invoke(killer) == true) return true;
            OnDeath(killer?.Named?.Title ?? killer?.Def.Name ?? "the dark");
            return false;
        };
        b.Hooks = h;
    }

    /// <summary>Travel: fade, build the next place, arrive.</summary>
    public void Travel(string to, string? caption = null, string? sub = null) => Travel(to, caption, sub, null);

    /// <summary>Travel; pulled (into an arena), the world swirls in and burns
    /// away instead of fading.</summary>
    void Travel(string to, string? caption, string? sub, Arrival? at, bool pull = false)
    {
        // One journey, one new place, one save: a second press at the gate waits.
        if (inTransit) return;
        inTransit = true;
        var from = zone?.Id;
        Journey.Capture(Battle);
        if (scene != null) scene.SimPaused = true;
        controls.Captured = true;
        if (pull) { hud.Pull(1.1, caption, sub); Sfx.Stinger("pull"); }
        else hud.Fade(1, 0.8, caption, sub);
        Wait(pull ? 1.15 : 0.85, () =>
        {
            EnterZone(to, from, at);
            Save("travel");
            Wait(caption != null ? 1.4 : 0.2, () =>
            {
                hud.Fade(0, 1.4);
                controls.Captured = false;
                controls.ClearLatches();
                inTransit = false;
            });
        });
    }

    /// <summary>Later, in real time (a fade, the fall).</summary>
    void Wait(double seconds, Action fn) => GetTree().CreateTimer(seconds, true, false, true).Timeout += fn;

    void OnDeath(string killer)
    {
        LastFall = (killer, Battle?.Time ?? 0);
        Journey.Ch.Stats.Deaths++;
        if (zone!.OnDeath(killer)) return;
        var b = Battle;
        Journey.Fell(zone.Id, zone.Name, killer, b?.Player, Rng);
        inTransit = true;
        Wait(1.5, () =>
        {
            hud.Fade(1, 1.8, "You fell", $"Taken by {killer}");
            Wait(2.4, () =>
            {
                EnterZone("waystation", "death");
                Save("death");
                Wait(1.4, () =>
                {
                    hud.Fade(0, 2);
                    inTransit = false;
                    Wait(1.6, () => Talk("chid"));
                });
            });
        });
    }

    /* --------------------------------------------------- what zones ask -- */

    public void Apply(IEnumerable<Change> changes) => Journey.Apply(changes);
    /// <summary>The narrator (or a voice the zone names), read aloud where
    /// there is a take; the words stay up at least as long as the voice.</summary>
    public void Say(string text, string? who = null, double seconds = 4)
    {
        var take = voice.Narrate(text);
        hud.Say(text, who, take != null ? Math.Max(seconds, take.Sec + 0.8) : seconds);
    }
    public void Toast(Toast t) { hud.Toast(t); sound.Toast(t); }
    public void Announce(Announcement a)
    {
        hud.Announce(a);
        sound.Announce(a, bossUp);
        if (Shots.On("boss")) Shots.Want("say_" + a.Title, 0.6);
    }
    public void After(double seconds, Action fn) => later.Add((seconds, fn));
    public bool GiveItem(string def, int qty = 1, int? rarity = null) => Journey.GiveItem(def, qty, rarity);
    public void ReturnItem(ItemInstance it) => Journey.ReturnItem(it);
    public void SetBoss(BossBar? bar) { hud.Boss(bar); bossUp = bar is { IsBoss: true }; }
    public void SetObjectives(List<Tracked> list) => hud.Objectives(list);
    public void SetHint(Hint? hint) => hud.Hint(CurrentHint = hint);
    public void SetAtmosphere(AtmospherePreset p, bool rebuild = true) => air.Set(p, rebuild);
    public void Capture(bool on) => controls.Captured = on;
    string? draftTip;
    public void SetDraftTip(string tip) => draftTip = tip;
    public void AnnounceZone() { if (zone != null) Announce(new Announcement(zone.Name, zone.Region, "zone", 4.2)); }

    public void Revived(double x, double z)
    {
        scene?.Player?.Revive();
        cam.Snap((float)x, (float)(scene?.HeightAt(x, z) ?? 0), (float)z);
    }

    /// <summary>The key for an action as the device in hand has it (a pad's button
    /// when a pad was touched last), for hints and the words that name keys.</summary>
    public string KeyLabel(string action) =>
        Enum.TryParse<Act>(action, true, out var a) ? controls.PromptLabel(a) : action.ToUpperInvariant();

    (Vector3 Pos, Vector3 Look) showT, showNow;
    bool showing;
    float showFov = 34, showBreath = 1;

    public void Showcase((double X, double Y, double Z)? pos, (double X, double Y, double Z) look = default)
    {
        if (scene == null) return;
        if (pos is not var (x, y, z)) { showing = false; scene.Showcase = null; return; }
        Pose(new Vector3((float)x, (float)y, (float)z), new Vector3((float)look.X, (float)look.Y, (float)look.Z));
    }

    /// <summary>A held camera, drifting to its mark (snap: there at once); its
    /// field of view (narrower for a close portrait), and how much it breathes.</summary>
    void Pose(Vector3 pos, Vector3 look, bool snap = false, float fov = 34, float breath = 1)
    {
        showFov = fov;
        showBreath = breath;
        showT = (pos, look);
        if (snap) showNow = showT;
        else if (!showing) showNow = (camera.GlobalPosition, look);
        showing = true;
        if (scene != null) scene.Showcase = showNow;
    }

    public void Save(string reason)
    {
        // Nothing is kept of an arena until it is over (the save made on the way in stands).
        if (zone == null || Mode != "play" || zone is ArenaRun) return;
        var b = Battle;
        if (b != null) Journey.Capture(b);
        var p = b?.Player;
        saves.Write(Journey.Slot, Journey.ToSave(new SaveLocation { Zone = zone.Id, X = p?.X ?? 0, Z = p?.Z ?? 0, Facing = p?.Facing ?? 0 }));
    }

    /* ------------------------------------------------------ interaction -- */

    void UpdateInteraction()
    {
        var b = Battle;
        if (b == null || zone == null || Overlay != null || !b.Player.Alive || inTransit || cine != null)
        {
            near = null;
            if (promptShown != null) hud.Prompt(promptShown = null);
            return;
        }
        var p = b.Player;
        Interactable? best = null;
        double bd = 1e9;
        foreach (var it in zone.Interactables)
        {
            if (it.When != null && !it.When()) continue;
            double d = Math.Sqrt((it.X - p.X) * (it.X - p.X) + (it.Z - p.Z) * (it.Z - p.Z));
            if (d < it.R && d < bd) { bd = d; best = it; }
        }
        near = best;
        var view = best != null ? new PromptView(controls.KeyLabel(Act.Interact), best.Verb, best.Name, best.Hint?.Invoke(), best.Locked?.Invoke()) : null;
        if (view != promptShown) hud.Prompt(promptShown = view);
    }

    /* ------------------------------------------------------------ frame -- */

    void OnEvents(List<CombatEvent> evs)
    {
        Journey.BankArt(Battle);
        Journey.BankGold(Battle);
        sound.Events(evs, Battle);
        zone?.Events(evs);
        foreach (var e in evs)
        {
            if (Shots.On("boss")) BossShot(e);
            switch (e)
            {
                case Ev.Announce an:
                    Announce(new Announcement(an.Title, an.Subtitle, an.Tone?.ToString().ToLowerInvariant() ?? "info", an.Subtitle is { Length: > 60 } ? 5 : 3.6, an.Kicker));
                    break;
                case Ev.Discovery d:
                    if (!World.Codex.Contains(d.Id)) World.Codex.Add(d.Id);
                    if (Content.Discoveries.All.FirstOrDefault(x => x.Id == d.Id) is { } pair) Toast(new Toast(ToastKind.Lore, $"Discovery: {pair.Name}", pair.Description, null, null, 9));
                    break;
                case Ev.Evolve ev:
                    // It clicked: its place on the bar crowned; drafted, the world slows for a breath
                    // as the new thing fires its first (a chest's waits for the chest to close).
                    if (ev.Chest) break;
                    hud.Crown(ev.Weapon);
                    scene?.Slow(0.6);
                    break;
                case Ev.Bark bk:
                    scene?.Voices.Bark(bk.Text, new Vector3((float)bk.X, (float)scene.HeightAt(bk.X, bk.Z), (float)bk.Z), bk.Speaker, bk.Speaker == null);
                    // A named voice in a fight (the Warden, Grimtunnel) is heard over everything.
                    if (bk.Speaker != null) voice.Shout(bk.Text);
                    break;
                case Ev.PlayerHit ph when ph.Dodged && Battle is { } b:
                    scene?.Voices.Bark("Dodged", new Vector3((float)b.Player.X, (float)scene.HeightAt(b.Player.X, b.Player.Z), (float)b.Player.Z), null, true);
                    break;
                case Ev.Focus f when scene != null && Battle is { } fb:
                    // A boss's arrival or fall: the camera turns to frame it with the survivor, then comes back.
                    cam.FocusOverride = new Vector3((float)(f.X + fb.Player.X) / 2, (float)scene.HeightAt(f.X, f.Z) + 1, (float)(f.Z + fb.Player.Z) / 2);
                    focusT = f.Duration;
                    break;
            }
        }
    }

    /// <summary>--on boss: a frame of each boss move as it is marked, its Break, its
    /// stagger, its arrival and what is announced (Shots.Want).</summary>
    static void BossShot(CombatEvent e)
    {
        switch (e)
        {
            case Ev.Telegraph t when t.Boss && t.Label is { Length: > 0 } l: Shots.Want(l, Math.Min(0.7, t.Duration * 0.6)); break;
            case Ev.Break: Shots.Want("break", 0.3); break;
            case Ev.Focus: Shots.Want("focus", 1.0); break;
            // The fall, as a run of frames through its slow motion and after.
            case Ev.Victory: for (int i = 0; i < 12; i++) Shots.Want("fall", 0.05 + i * 0.25); break;
        }
    }

    WorldState World => Journey.World;
    /// <summary>How long the camera stays turned to a boss (Ev.Focus).</summary>
    double focusT;

    public override void _Process(double delta)
    {
        // Something over the game has the buttons: pad buttons mean their menu meaning first.
        controls.MenuMode = screens.Current != null || hudMode != null;
        // --pad (pictures of pad play): the pad stays in hand whatever the window's mouse does.
        if (Args.Has("pad") && keyI > 0) controls.UsingPad = true;
        if (scene == null) return;
        double dt = Math.Min(delta, 0.1);
        if (focusT > 0 && (focusT -= dt) <= 0 && hudMode == null) cam.FocusOverride = null;
        if (Mode == "play" && zone != null)
        {
            auto?.Drive(dt);
            Journey.Playtime += dt;
            UpdateInteraction();
            // The ground walked, on the map's fog.
            fogT -= dt;
            if (fogT <= 0 && Battle is { } fb)
            {
                fogT = 0.4;
                double extent = scene.Data.Meta.Map?.Extent is { ValueKind: System.Text.Json.JsonValueKind.Number } ex ? ex.GetDouble() : scene.Data.Meta.Bound * 2;
                Journey.Walk(zone.Id, extent, fb.Player.X, fb.Player.Z);
                foreach (var k in zone.MapKnown) Journey.Walk(zone.Id, extent, k.X, k.Z, k.R);
            }
            autosaveT += dt;
            if (autosaveT > 90 && Overlay == null && !inTransit) { autosaveT = 0; Save("auto"); }
            Perf.Begin(Perf.Part.Zone);
            zone.Frame(dt);
            Perf.End(Perf.Part.Zone);
            // An arena's camera breathes with its night (unless a conversation has it, or --cam fixed it).
            if (zone is ArenaRun ar && hudMode == null && camSaved == null && !Args.Has("cam")) cam.TargetDistance = (float)ar.CameraDistance;
            RunLater(dt);
        }
        else if (auto != null && Mode != "play") AutoFront();
        // --keys on the title or at the fire (pictures of their focus): pressed in turn, two seconds in.
        else if (Mode != "play" && Args.Get("keys") is string fk && keyI < fk.Split(',').Length)
        {
            tourT -= dt;
            if (tourT <= 0)
            {
                tourT = 0.35;
                if (Args.Has("pad")) { controls.UsingPad = true; Ui.Nav.KeyMode = true; }
                if (Enum.TryParse<Act>(fk.Split(',')[keyI++], true, out var fa)) controls.Press(fa);
            }
        }
        // The figure being made: turned, and framed as near as asked.
        if (Mode == "create") UpdateCreate(dt);
        // A held camera drifts toward its mark, breathing a little.
        if (showing)
        {
            float breathe = Mathf.Sin((float)scene.Time * 0.35f) * 0.08f * showBreath;
            var target = showT.Pos + new Vector3(breathe, breathe * 0.5f, 0);
            float k1 = 1 - Mathf.Exp(-1.8f * (float)dt), k2 = 1 - Mathf.Exp(-2.2f * (float)dt);
            showNow = (showNow.Pos.Lerp(target, k1), showNow.Look.Lerp(showT.Look, k2));
            scene.Showcase = showNow;
            camera.Fov = Mathf.Lerp(camera.Fov, showFov, k1);
        }
        else if (camera.Fov != 34) camera.Fov = 34;
        scene.Update(dt);
        CinemaFrame(dt);
        // The survivor's place on screen, for the health drawn under them; the prompt's thing; what matters off screen.
        if (Mode == "play" && Battle is { } fb2)
        {
            var at = new Vector3((float)fb2.Player.X, (float)scene.HeightAt(fb2.Player.X, fb2.Player.Z), (float)fb2.Player.Z);
            hud.Follow(camera.IsPositionBehind(at) ? null : camera.UnprojectPosition(at));
            if (near != null)
            {
                var np = new Vector3((float)near.X, (float)scene.HeightAt(near.X, near.Z) + 2.4f, (float)near.Z);
                hud.PromptAt(camera.IsPositionBehind(np) ? null : camera.UnprojectPosition(np));
            }
            else hud.PromptAt(null);
            hud.Beyond(Overlay == null ? Offscreen(fb2) : new());
        }
        {
            var sb = Battle;
            var at = sb != null ? new Vector3((float)sb.Player.X, 0, (float)sb.Player.Z) : showNow.Look;
            var time = Journey is { } jn ? zone?.TimeOf(jn.World) ?? jn.World.Time : TimeOfDay.Night;
            Perf.Begin(Perf.Part.Sound);
            sound.Update(dt, new SoundState(Mode, zone?.Id, time, at.X, at.Z, sb, bossUp, Mode == "play" ? Overlay : screens.Current?.Kind,
                zone != null ? zone.Ambience : null, zone != null ? zone.MusicMood : null));
            Perf.End(Perf.Part.Sound);
        }
        if (Mode != "play") return;
        UpdateChest();
        UpdateDraft(dt);
        hudT -= dt;
        if (hudT <= 0)
        {
            using var _ = new Perf.Span(Perf.Part.Hud);
            hudT = 1.0 / 12;
            var ch = Journey.Ch;
            hud.Frame(Battle, ch.Gold, Inventory.Count(ch, "health_draught"), (ch.Level, ch.Xp / Character.XpForLevel(ch.Level)));
            hud.MapFrame(MiniView());
            if (zone is ArenaRun ar && Battle is { } cb2)
            {
                double end = ar.Spec.Minutes * 60, left = end - cb2.Time;
                var (phase, tone) = Phase(cb2.Time / end, ar.Won, left);
                hud.ArenaClock(ar.Won ? -(cb2.Time - end) : left > 0 ? left : 0, phase, tone);
            }
            else hud.ArenaClock(null, "");
        }
        hud.SetBruise(scene.Bruise);
        scene.Voices.Quiet = hudMode == "dialogue" || screens.Current != null;
        // Fallen: the world loses its colour.
        air.Env.AdjustmentSaturation = Mathf.Lerp(air.Env.AdjustmentSaturation, Battle?.Player.Alive == false ? 0.2f : 1f, 1 - Mathf.Exp(-2 * (float)dt));
        Report(dt);
        Tour(dt);
    }

    /// <summary>The night's phases, named on the clock (docs/feel S-21), as shares of the arena's length.</summary>
    static (string, Color) Phase(double k, bool won, double left)
    {
        if (won) return ("BEYOND  ·  PAST WHAT RULED IT", new Color("#c8b0ff"));
        if (left <= 0) return ("IT HAS COME", Style.BloodHi);
        return k switch
        {
            < 1 / 6.0 => ("DUSK  ·  BEFORE WHAT RULES IT COMES", new Color("#e8b878")),
            < 1 / 3.0 => ("GLOAMING  ·  BEFORE WHAT RULES IT COMES", new Color("#ff9a50")),
            < 2 / 3.0 => ("THE WITCHING  ·  BEFORE WHAT RULES IT COMES", new Color("#ff7a3a")),
            < 28 / 30.0 => ("ASHFALL  ·  BEFORE WHAT RULES IT COMES", new Color("#ff5a3a")),
            _ => ("THE COMING", Style.BloodHi),
        };
    }

    /// <summary>What last brought the survivor down, and when (the arena's end tells it).</summary>
    public (string Name, double At)? LastFall { get; private set; }

    /// <summary>What matters and is off the screen: what rules the fight, the nearest elites, chests.</summary>
    List<Ui.Beyond> Offscreen(Battle b)
    {
        var o = new List<Ui.Beyond>();
        if (scene == null) return o;
        var view = new Rect2(Vector2.Zero, GetViewport().GetVisibleRect().Size).Grow(-30);
        double px = b.Player.X, pz = b.Player.Z;
        void Add(double x, double z, string glyph, Color c)
        {
            var w = new Vector3((float)x, (float)scene.HeightAt(x, z) + 1, (float)z);
            var sp = camera.UnprojectPosition(w);
            bool behind = camera.IsPositionBehind(w);
            if (!behind && view.HasPoint(sp)) return;
            if (behind) sp = view.GetCenter() - (sp - view.GetCenter());
            double d = Math.Sqrt((x - px) * (x - px) + (z - pz) * (z - pz));
            o.Add(new Ui.Beyond(sp, glyph, c, (float)Math.Clamp(1 - (d - 20) / 60, 0, 1)));
        }
        foreach (var e in b.Enemies.Living().Where(e => e.Boss)) Add(e.X, e.Z, "horns", Style.BloodHi);
        foreach (var e in b.Enemies.Living().Where(e => e.Elite && !e.Boss).OrderBy(e => (e.X - px) * (e.X - px) + (e.Z - pz) * (e.Z - pz)).Take(3))
            Add(e.X, e.Z, "skull", Style.EmberHi);
        foreach (var p in b.Pickups.Living().Where(p => p.Kind == PickupKind.Chest).OrderBy(p => (p.X - px) * (p.X - px) + (p.Z - pz) * (p.Z - pz)).Take(2))
            Add(p.X, p.Z, "relic", Style.GoldHi);
        return o;
    }

    /// <summary>What the corner map shows now: by day and on the story's roads, not in an arena.</summary>
    MinimapView? MiniView()
    {
        if (zone == null || scene == null || zone is ArenaRun || Battle is not { } b || inTransit) return null;
        float extent = MapScreen.Extent(scene.Data.Meta);
        var seen = World.Zone(zone.Id).TryGetValue("seen", out var f) && f.Str is { Length: Journey.FogN * Journey.FogN } s ? s : new string('0', Journey.FogN * Journey.FogN);
        bool Seen(double x, double z)
        {
            int i = (int)Math.Floor((x / extent + 0.5) * Journey.FogN), j = (int)Math.Floor((z / extent + 0.5) * Journey.FogN);
            return i >= 0 && j >= 0 && i < Journey.FogN && j < Journey.FogN && seen[j * Journey.FogN + i] == '1';
        }
        var marks = zone.MapMarks().Where(m => m.Kind != MarkKind.Place && (m.Kind is MarkKind.Exit or MarkKind.Quest || Seen(m.X, m.Z)))
            .Select(m => new MiniMark(m.X, m.Z, m.Kind, m.Label)).ToList();
        if (World.Corpse is { } corpse && corpse.Zone == zone.Id) marks.Add(new MiniMark(corpse.X, corpse.Z, MarkKind.Danger, "Your belongings"));
        return new MinimapView(zone.Id, MapScreen.Drawing(scene.Data), extent, seen, Journey.FogN, marks, b.Player.X, b.Player.Z, b.Player.Facing, zone.TimeOf(World) == TimeOfDay.Night);
    }

    double tourT = 2;
    int keyI;
    int tourI;

    /// <summary>--open KIND (or 'all'): the screens opened in turn, for
    /// pictures and for runs that check each builds (--bare hides the world).</summary>
    bool hordeDone, dropsDone, castDone, giveDone, minuteDone, dieDone, chestDone;
    double blastT = 0.5, marksT = 1;

    void Tour(double dt)
    {
        if (Args.Has("bare") && scene != null) scene.Visible = false;
        // --horde N[:KIND][,N[:KIND]...]: that many of them round the survivor at once (a stress test, a picture).
        if (!hordeDone && Args.Get("horde") is string h && Battle is { } hb)
        {
            hordeDone = true;
            foreach (var group in h.Split(','))
            {
                var parts = group.Split(':');
                int n = int.TryParse(parts[0], out var v) ? v : 100;
                // A kind ending in ! comes as elites (pictures of the edge marks, elite fights).
                string kind = parts.Length > 1 ? parts[1].TrimEnd('!') : "risen";
                bool elite = parts.Length > 1 && parts[1].EndsWith('!');
                for (int i = 0; i < n; i++)
                {
                    double a = Rng.NextDouble() * Math.Tau, d = Args.Num("dist", 9) + Rng.NextDouble() * Args.Num("spread", 20);
                    hb.SpawnEnemy(kind, hb.Player.X + Math.Cos(a) * d, hb.Player.Z + Math.Sin(a) * d, elite ? new Battle.SpawnOpts { Elite = true } : null);
                }
            }
        }
        // --drops: one of every kind of thing that lies on the ground, in a ring round the survivor, left
        // where they lie (a pickup is not drawn in until it has settled) and worth next to nothing (a picture).
        if (!dropsDone && Args.Has("drops") && Battle is { } db)
        {
            dropsDone = true;
            var kinds = new[] { PickupKind.Ember, PickupKind.Ember, PickupKind.Ember, PickupKind.Gold, PickupKind.Heal, PickupKind.Magnet, PickupKind.Item, PickupKind.Chest, PickupKind.Material, PickupKind.Quest };
            for (int i = 0; i < kinds.Length; i++)
            {
                double a = i * Math.Tau / kinds.Length;
                var k = db.SpawnPickup(kinds[i], db.Player.X + Math.Cos(a) * 2.2, db.Player.Z + Math.Sin(a) * 2.2, 0.01);
                if (k != null) { k.Tier = kinds[i] == PickupKind.Ember ? i : 2; k.Vx = k.Vz = 0; k.Age = -600; }
            }
        }
        // --give A,B[:RANK][@EVOLUTION],+PASSIVE[:RANK]: a build in hand from the start
        // (pictures of weapons, of the draft with an arsenal), the arena's opening blessing passed over.
        // --minute M: the arena's clock set to M minutes (pictures of its boss: --minute 29.9).
        if (!minuteDone && Args.Has("minute") && zone is ArenaRun mr && Battle != null)
        {
            minuteDone = true;
            mr.SkipTo(Args.Num("minute", 29.9f) * 60);
        }
        // --chest 1,3,5! [--chest-at T]: chests of those sizes opened at her feet T seconds in, one
        // after another (! a boss's hoard), for pictures of the opening.
        if (!chestDone && Args.Get("chest") is string chs && zone is ArenaRun car && Battle != null && Journey.Playtime >= Args.Num("chest-at", 3))
        {
            chestDone = true;
            foreach (var one in chs.Split(','))
                if (int.TryParse(one.TrimEnd('!'), out var cn)) car.ChestAt(cn, one.EndsWith('!'));
        }
        if (!giveDone && Args.Get("give") is string give && Battle is { } gb)
        {
            giveDone = true;
            foreach (var w in give.Split(','))
            {
                var evo = w.Split('@');
                var parts = evo[0].Split(':');
                int r = parts.Length > 1 && int.TryParse(parts[1], out var rv) ? rv : 1;
                if (parts[0].StartsWith('+')) { for (int i = 0; i < r; i++) gb.AddBoon(parts[0][1..]); continue; }
                // One already in hand (the calling's own) is ranked up to it instead.
                if (gb.Weapons.Find(x => x.Id == parts[0]) is { } held) held.Rank = Math.Max(held.Rank, r);
                else gb.AddWeapon(parts[0], r);
                if (evo.Length > 1) gb.Evolve(parts[0], evo[1]);
            }
            gb.GreatOwed = 0;
            // --lab: the skills given and nothing else (the calling's own is put away), so a
            // picture shows one skill at a time.
            if (Args.Has("lab"))
            {
                var keep = give.Split(',').Select(w => w.Split('@')[0].Split(':')[0]).ToHashSet();
                foreach (var w in gb.Weapons.Select(x => x.Id).ToList()) if (!keep.Contains(w)) gb.RemoveWeapon(w);
            }
        }
        // --lab: no drafts and no dying, so a run of pictures is all the skill in hand.
        if (Args.Has("lab") && Battle is { } lb)
        {
            lb.PendingLevels = 0;
            lb.PendingBlessings.Clear();
            lb.GreatOwed = 0;
            lb.EmberXp = 0;
            lb.EmberNext = 1e9;
            lb.Player.Hp = lb.MaxHp;
        }
        // --blast SCHOOL[:R]: that school's burst a few paces ahead, every second and a half (pictures of it).
        if (Args.Get("blast") is string bl && Battle is { } bb && scene != null)
        {
            blastT -= dt;
            if (blastT <= 0)
            {
                blastT = 1.5;
                var parts = bl.Split(':');
                var school = Enum.Parse<School>(parts[0], true);
                float r = parts.Length > 1 ? float.Parse(parts[1], System.Globalization.CultureInfo.InvariantCulture) : 2.5f;
                scene.Fx.Blast(bb.Player.X + 2, bb.Player.Z - 1, school, r);
            }
        }
        // --marks: every telegraph the bosses use, round the survivor every four seconds, harmless
        // and named for where it points (a picture that checks the drawing: is the cone east?).
        if (Args.Has("marks") && Battle is { } mb)
        {
            marksT -= dt;
            if (marksT <= 0)
            {
                marksT = 4;
                double px = mb.Player.X, pz = mb.Player.Z;
                Battle.EnemyBlow Mark(Battle.EnemyBlow b) { b.Delay = 3.5; return mb.Blow(b); }
                Mark(new Battle.EnemyBlow { Shape = TelegraphShape.Cone, X = px + 2, Z = pz, Radius = 6, Angle = 0, Arc = Math.PI / 2, Label = "cone +x" });
                Mark(new Battle.EnemyBlow { Shape = TelegraphShape.Cone, X = px - 2, Z = pz, Radius = 5, Angle = Math.PI / 2, Arc = Math.PI / 3, Label = "cone +z" });
                Mark(new Battle.EnemyBlow { Shape = TelegraphShape.Line, X = px - 9, Z = pz - 6, X1 = px + 9, Z1 = pz - 6, Width = 2, Label = "lane" });
                Mark(new Battle.EnemyBlow { Shape = TelegraphShape.Ring, X = px, Z = pz, Inner = 9, Radius = 11, Label = "band" });
                Mark(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, X = px - 7, Z = pz + 5, Radius = 2, Label = "blow" });
                Mark(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Ground, X = px + 7, Z = pz + 5, Radius = 2, Label = "ground" });
                Mark(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Safe, X = px - 7, Z = pz - 1, Radius = 2, Label = "safe" });
                Mark(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Wall, X = px + 7, Z = pz - 1, Radius = 2, Label = "wall" });
            }
        }
        // --cast T: the art in hand used once, T seconds in (a picture of it);
        // --still: used standing, with no push (a vault then springs back).
        if (!castDone && Args.Has("cast") && Battle is { } cb && Journey.Playtime >= Args.Num("cast", 1))
        {
            castDone = true;
            cb.Aim = null;
            cb.UseAbility(Args.Has("still") ? 0 : 1, 0);
        }
        // --die T: T seconds in, a risen at arm's length before her (--behind:
        // at her back) fells her where she stands (a picture of her fall).
        if (!dieDone && Args.Has("die") && Battle is { } kb && Journey.Playtime >= Args.Num("die", 1))
        {
            dieDone = true;
            var killer = kb.SpawnEnemy("risen", kb.Player.X, kb.Player.Z + (Args.Has("behind") ? -1.2 : 1.2));
            kb.HurtPlayerRaw(kb.Player.Hp + 1e6, School.Physical, "test", killer);
        }
        if (Args.Get("open") is not string want) return;
        tourT -= dt;
        if (tourT > 0) return;
        string[] all = { "inventory", "character", "journal", "map", "pause", "rest", "stash", "shop:harlan", "chapter" };
        var list = want == "all" ? all : want.Split(',');
        if (tourI >= list.Length)
        {
            // --keys A,B,...: actions pressed in turn once the screen is up (--pad: as from a pad), for pictures of focus.
            if (Args.Get("keys") is string keys && keyI < keys.Split(',').Length)
            {
                tourT = 0.35;
                if (Args.Has("pad")) { controls.UsingPad = true; Ui.Nav.KeyMode = true; }
                if (Enum.TryParse<Act>(keys.Split(',')[keyI++], true, out var ka)) controls.Press(ka);
            }
            return;
        }
        if (Args.Has("pad")) { controls.UsingPad = true; Ui.Nav.KeyMode = true; }
        tourT = Args.Num("every", 1.5f);
        if (list[tourI].StartsWith("shop:")) Journey.OpenShop(list[tourI][5..], Rng);
        GD.Print($"open {list[tourI]}");
        CloseOverlay();
        var next = list[tourI++];
        if (next.StartsWith("talk:")) TalkTo(next[5..]);
        else if (next == "draft" && Battle is { } b) { b.GainEmber(b.EmberNext); }
        // A won arena's end, with a sample tally (pictures of the result screen; in an arena).
        else if (next == "result" && World.Arena is { } spec && Battle is { } rb)
            ArenaOver(new ArenaResult(spec, true, 2134, rb.KillCount + 1840, Math.Max(rb.EmberLevel, 27), 1460, 212, Content.Weapons.Pool.Take(2).ToList(), 1, true)
            {
                // --fell: the same night, fallen past the half hour: half of it spilled.
                Carried = Args.Has("fell") ? new() { ["ember_shard"] = 3, ["wolf_pelt"] = 2, ["boar_hide"] = 1 } : new() { ["ember_shard"] = 7, ["wolf_pelt"] = 4, ["boar_hide"] = 3 },
                Spilled = Args.Has("fell") ? new() { ["ember_shard"] = 4, ["wolf_pelt"] = 2, ["boar_hide"] = 2 } : new(),
            });
        else Open(next);
    }

    /// <summary>--open talk:ID>words>+: a conversation, each choice after it
    /// taken by a fragment of its words and each + a click on (pictures of a
    /// line deep in a conversation: the fortune's pages, a long answer).</summary>
    void TalkTo(string what)
    {
        var parts = what.Split('>');
        Talk(parts[0]);
        foreach (var pick in parts.Skip(1))
        {
            if (runner?.Present() is not { } p) break;
            if (pick == "+") { Advance(); continue; }
            var c = p.Choices.FirstOrDefault(x => x.Enabled && x.Text.Contains(pick, StringComparison.OrdinalIgnoreCase));
            if (c == null) { GD.Print($"talk: no choice \"{pick}\""); break; }
            Choose(c.Index);
        }
    }

    /// <summary>--log S: a line every S seconds of how it is going (for runs
    /// without a screen: Godot's --headless, --quit-after).</summary>
    ulong costFrom;
    int costFrames;

    /// <summary>Average wall time per frame since the last report (a headless
    /// run's frames follow each other at once: this is what a frame costs).</summary>
    string FrameCost()
    {
        ulong now = Time.GetTicksUsec();
        string s = costFrames > 0 ? $" | frame {(now - costFrom) / 1000.0 / costFrames:0.0}ms" : "";
        costFrom = now;
        costFrames = 0;
        return s;
    }

    void Report(double dt)
    {
        costFrames++;
        if (!Args.Has("log")) return;
        reportT -= dt;
        if (reportT > 0) return;
        reportT = Args.Num("log", 5);
        var b = Battle;
        var p = b?.Player;
        int foes = b?.Enemies.Count ?? 0;
        var dbg = zone?.Debug() is { Count: > 0 } d ? string.Join(" ", d.Take(4).Select(kv => $"{kv.Key}={kv.Value}")) : "";
        var (drawn, dead) = scene!.Crowd.Counts;
        var (gibs, splats) = scene.Fx.Gore.Counts;
        GD.Print($"[{scene.Time,6:0.0}s] {zone?.Id} hp {p?.Hp:0}/{b?.MaxHp:0} ember {b?.EmberLevel} kills {b?.KillCount} foes {foes} (drawn {drawn}, lying {dead}, gibs {gibs}, blood {splats}) at {p?.X:0},{p?.Z:0} {Overlay} {dbg}{FrameCost()}{(synth.Live ? $" | sound {sound.Music.Mood} voices {synth.Voices} mix {synth.MixCost / Math.Max(1e-9, synth.Mixed) * 100:0}% heard {synth.Mixed:0}s skips {synth.Skips} queue {synth.Queue / synth.Rate * 1000:0}ms" : "")}");
    }

    /// <summary>--perf: the frame measured (Perf.cs), with the game's own
    /// numbers beside it: the horde, the dead, the gore, the sound's voices.</summary>
    void MeasureWith(Perf perf)
    {
        AddChild(perf);
        Perf.CounterNames = ["foes", "drawn", "lying", "gibs", "blood", "voices"];
        Perf.Counters = a =>
        {
            a[0] = Battle?.Enemies.Count ?? 0;
            if (scene != null)
            {
                var (drawn, dead) = scene.Crowd.Counts;
                var (gibs, splats) = scene.Fx.Gore.Counts;
                a[1] = drawn; a[2] = dead; a[3] = gibs; a[4] = splats;
            }
            a[5] = synth.Live ? synth.Voices : 0;
        };
        Perf.Note = () => $"{zone?.Id} foes {Battle?.Enemies.Count ?? 0} ember {Battle?.EmberLevel} kills {Battle?.KillCount} " +
                          (zone?.Debug() is { Count: > 0 } d ? string.Join(" ", d.Take(3).Select(kv => $"{kv.Key}={kv.Value}")) : "");
        // --perf-off A,B: things taken out of the picture, to see what each costs
        // by the difference (never for play): her, crowd, grass, flora, props,
        // landmarks, ground, water, fires, fx, hud, lamps, lampshadows,
        // sunshadows, ssao, volfog, fog, glow, taa, msaa, fxaa.
        if (Args.Get("perf-off") is not string off) return;
        var what = off.Split(',').ToHashSet();
        perf.Each = () =>
        {
            if (scene == null) return;
            if (what.Contains("her") && scene.Player != null) scene.Player.Visible = false;
            if (what.Contains("crowd")) scene.Crowd.Visible = false;
            if (what.Contains("fx")) scene.Fx.Visible = false;
            if (what.Contains("hud")) hud.Visible = false;
            foreach (var c in scene.View.GetChildren())
            {
                if (c is not Node3D n) continue;
                string nm = n.Name;
                bool named = nm is "Grass" or "Flora" or "Props" or "Landmarks" or "Ground" or "Water" or "Fires" or "Lights";
                if (what.Contains("grass") && nm == "Grass" || what.Contains("flora") && nm == "Flora" || what.Contains("props") && nm == "Props" ||
                    what.Contains("landmarks") && nm == "Landmarks" || what.Contains("ground") && nm == "Ground" || what.Contains("water") && nm == "Water" ||
                    what.Contains("fires") && nm == "Fires" || what.Contains("lamps") && nm == "Lights" ||
                    // The pieces set down one by one (an arena's cover, a runtime's props).
                    what.Contains("pieces") && !named)
                    n.Visible = false;
                if (what.Contains("lampshadows") && nm == "Lights")
                    foreach (var l in n.GetChildren()) if (l is OmniLight3D o) o.ShadowEnabled = false;
            }
            if (what.Contains("sunshadows")) air.Key.ShadowEnabled = false;
            if (what.Contains("ssao")) air.Env.SsaoEnabled = false;
            if (what.Contains("volfog")) air.Env.VolumetricFogEnabled = false;
            if (what.Contains("fog")) air.Env.FogEnabled = false;
            if (what.Contains("glow")) air.Env.GlowEnabled = false;
            var vp = GetViewport();
            if (what.Contains("taa")) vp.UseTaa = false;
            if (what.Contains("msaa")) vp.Msaa3D = Viewport.Msaa.Disabled;
            if (what.Contains("fxaa")) vp.ScreenSpaceAA = Viewport.ScreenSpaceAAEnum.Disabled;
        };
    }

    /// <summary>What was put off, in game time: it waits while a menu, a
    /// conversation or a fade holds the world still.</summary>
    void RunLater(double dt)
    {
        if (later.Count == 0 || scene == null || scene.SimPaused) return;
        for (int i = 0; i < later.Count; i++) later[i] = (later[i].T - dt, later[i].Fn);
        var due = later.Where(l => l.T <= 0).ToList();
        if (due.Count == 0) return;
        later.RemoveAll(l => l.T <= 0);
        foreach (var (_, fn) in due) fn();
    }
}
