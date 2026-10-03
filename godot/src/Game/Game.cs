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
    bool bossUp;
    Atmosphere air = null!;
    Camera3D camera = null!;
    FollowCamera cam = null!;
    WorldScene? scene;
    ZoneRuntime? zone;
    Saves saves = null!;
    Interactable? near;
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
        sound = new SoundBridge(synth);
        AddChild(new VoiceOver());
        // The interface: every button ticks under the pointer and clicks.
        GetTree().NodeAdded += n => { if (n is BaseButton bb) Sounded(bb); };
        saves = new Saves(ProjectSettings.GlobalizePath("user://saves"));
        controls.On(OnAction);
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
        var arch = Args.Get("quick") is string q && q is "warden" or "reaver" or "arcanist" or "stalker" ? q : "warden";
        var a = Callings.Archetype(arch);
        Begin(new CreationChoice
        {
            // --palette ID: the calling's colours (its first, undyed, by default).
            Name = Args.Get("name") ?? "Ashe", Archetype = arch, Background = Args.Get("bg") ?? "hunter",
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
            Arenas.Begin(World, Arenas.FromTable(o, "waystation", at0.X, at0.Z, at0.Facing));
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
        air.Quality(s.Quality);
        AudioServer.SetBusVolumeDb(0, s.Volume <= 0 ? -80 : Mathf.LinearToDb(s.Volume));
        VoiceOver.Instance?.Volume(s.VoiceVolume);
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
        screens.Close();
        Travel(s.ReturnZone, null, null, new Arrival(s.ReturnX, s.ReturnZ, s.ReturnFacing));
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
        scene.OnStep = dt => zone?.Step(dt);
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
        if (scene == null || scene.Data.Id != id || scene.Battle != null) Stage(id);
        else RemoveFigure();
        zone = Make(id, scene!.Data.Meta);
        var time = zone.TimeOf(World);
        air.Set(zone.AtmosphereFor(time));
        scene.View.SetNight(time == TimeOfDay.Night);
        EnterPlay(zone, from, at);
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
        // An arena is seen from higher and further out: the whole of the fight.
        var (pitch, dist) = z.Camera is var (cp, cd) ? (Mathf.DegToRad((float)cp), (float)cd) : camHome;
        // --cam still wins: it is for close pictures, arenas included.
        if (Args.Has("cam")) dist = (float)Args.Num("cam", dist);
        cam.Pitch = pitch;
        cam.Distance = cam.TargetDistance = dist;
        scene.StartBattle(b, Loadouts.Of(Journey.Ch));
        HookBattle(b);
        z.Begin(b);
        scene.Crowd.Prepare(z.Creatures.Select(c => Content.Enemies.Get(c).Visual));
        hud.ZoneInfo(z.Name, z.Region, World.Day, z.TimeOf(World));
        World.Facts["player.zone"] = z.Id;
    }

    void HookBattle(Battle b)
    {
        var zh = zone!.Hooks;
        b.Hooks = new BattleHooks
        {
            OnLoot = zh.OnLoot, BossTick = zh.BossTick, OnHitProp = zh.OnHitProp,
            OnKill = (e, byPlayer) => { Journey.Killed(e, byPlayer); zh.OnKill?.Invoke(e, byPlayer); },
            OnPickup = p => (zh.OnPickup == null || zh.OnPickup(p)) && Journey.PickedUp(p),
            OnPlayerDeath = killer =>
            {
                if (zh.OnPlayerDeath?.Invoke(killer) == true) return true;
                OnDeath(killer?.Named?.Title ?? killer?.Def.Name ?? "the dark");
                return false;
            },
        };
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
    public void Say(string text, string? who = null, double seconds = 4) { hud.Say(text, who, seconds); VoiceOver.Instance?.Narrate(text); }
    public void Toast(Toast t) { hud.Toast(t); sound.Toast(t); }
    public void Announce(Announcement a) { hud.Announce(a); sound.Announce(a, bossUp); }
    public void After(double seconds, Action fn) => later.Add((seconds, fn));
    public bool GiveItem(string def, int qty = 1, int? rarity = null) => Journey.GiveItem(def, qty, rarity);
    public void ReturnItem(ItemInstance it) => Journey.ReturnItem(it);
    public void SetBoss(BossBar? bar) { hud.Boss(bar); bossUp = bar != null; }
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

    public string KeyLabel(string action) =>
        Enum.TryParse<Act>(action, true, out var a) ? controls.KeyLabel(a) : action.ToUpperInvariant();

    (Vector3 Pos, Vector3 Look) showT, showNow;
    bool showing;

    public void Showcase((double X, double Y, double Z)? pos, (double X, double Y, double Z) look = default)
    {
        if (scene == null) return;
        if (pos is not var (x, y, z)) { showing = false; scene.Showcase = null; return; }
        Pose(new Vector3((float)x, (float)y, (float)z), new Vector3((float)look.X, (float)look.Y, (float)look.Z));
    }

    /// <summary>A held camera, drifting to its mark (snap: there at once).</summary>
    void Pose(Vector3 pos, Vector3 look, bool snap = false)
    {
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
        if (b == null || zone == null || Overlay != null || !b.Player.Alive || inTransit)
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
            switch (e)
            {
                case Ev.Announce an:
                    Announce(new Announcement(an.Title, an.Subtitle, an.Tone?.ToString().ToLowerInvariant() ?? "info", an.Subtitle is { Length: > 60 } ? 5 : 3.6, an.Kicker));
                    break;
                case Ev.Discovery d:
                    if (!World.Codex.Contains(d.Id)) World.Codex.Add(d.Id);
                    if (Content.Discoveries.All.FirstOrDefault(x => x.Id == d.Id) is { } pair) Toast(new Toast(ToastKind.Lore, pair.Name, "A new discovery, remembered in the codex", null, null, 9));
                    break;
                case Ev.Bark bk:
                    scene?.Voices.Bark(bk.Text, new Vector3((float)bk.X, (float)scene.HeightAt(bk.X, bk.Z), (float)bk.Z), bk.Speaker, bk.Speaker == null);
                    if (scene != null && bk.Speaker != null) VoiceOver.Instance?.Bark(scene, bk.Text, new Vector3((float)bk.X, (float)scene.HeightAt(bk.X, bk.Z), (float)bk.Z), null);
                    break;
                case Ev.PlayerHit ph when ph.Dodged && Battle is { } b:
                    scene?.Voices.Bark("Dodged", new Vector3((float)b.Player.X, (float)scene.HeightAt(b.Player.X, b.Player.Z), (float)b.Player.Z), null, true);
                    break;
            }
        }
    }

    WorldState World => Journey.World;

    public override void _Process(double delta)
    {
        if (scene == null) return;
        double dt = Math.Min(delta, 0.1);
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
            zone.Frame(dt);
            RunLater(dt);
        }
        else if (auto != null && Mode != "play") AutoFront();
        // A held camera drifts toward its mark, breathing a little.
        if (showing)
        {
            float breathe = Mathf.Sin((float)scene.Time * 0.35f) * 0.08f;
            var target = showT.Pos + new Vector3(breathe, breathe * 0.5f, 0);
            float k1 = 1 - Mathf.Exp(-1.8f * (float)dt), k2 = 1 - Mathf.Exp(-2.2f * (float)dt);
            showNow = (showNow.Pos.Lerp(target, k1), showNow.Look.Lerp(showT.Look, k2));
            scene.Showcase = showNow;
        }
        scene.Update(dt);
        {
            var sb = Battle;
            var at = sb != null ? new Vector3((float)sb.Player.X, 0, (float)sb.Player.Z) : showNow.Look;
            var time = Journey is { } jn ? zone?.TimeOf(jn.World) ?? jn.World.Time : TimeOfDay.Night;
            sound.Update(dt, new SoundState(Mode, zone?.Id, time, at.X, at.Z, sb, bossUp, Mode == "play" ? Overlay : screens.Current?.Kind,
                zone != null ? zone.Ambience : null, zone != null ? zone.MusicMood : null));
        }
        if (Mode != "play") return;
        UpdateDraft(dt);
        hudT -= dt;
        if (hudT <= 0)
        {
            hudT = 1.0 / 12;
            var ch = Journey.Ch;
            hud.Frame(Battle, ch.Gold, Inventory.Count(ch, "health_draught"), (ch.Level, ch.Xp / Character.XpForLevel(ch.Level)));
        }
        hud.SetBruise(scene.Bruise);
        scene.Voices.Quiet = hudMode == "dialogue" || screens.Current != null;
        // Fallen: the world loses its colour.
        air.Env.AdjustmentSaturation = Mathf.Lerp(air.Env.AdjustmentSaturation, Battle?.Player.Alive == false ? 0.2f : 1f, 1 - Mathf.Exp(-2 * (float)dt));
        Report(dt);
        Tour(dt);
    }

    double tourT = 2;
    int tourI;

    /// <summary>--open KIND (or 'all'): the screens opened in turn, for
    /// pictures and for runs that check each builds (--bare hides the world).</summary>
    bool hordeDone, dropsDone, castDone, giveDone;
    double blastT = 0.5;

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
                for (int i = 0; i < n; i++)
                {
                    double a = Rng.NextDouble() * Math.Tau, d = Args.Num("dist", 9) + Rng.NextDouble() * Args.Num("spread", 20);
                    hb.SpawnEnemy(parts.Length > 1 ? parts[1] : "risen", hb.Player.X + Math.Cos(a) * d, hb.Player.Z + Math.Sin(a) * d);
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
        // --give A,B[:RANK]: those ember weapons in hand from the start (pictures of them).
        if (!giveDone && Args.Get("give") is string give && Battle is { } gb)
        {
            giveDone = true;
            foreach (var w in give.Split(','))
            {
                var parts = w.Split(':');
                gb.AddWeapon(parts[0], parts.Length > 1 && int.TryParse(parts[1], out var r) ? r : 1);
            }
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
        // --cast T: the art in hand used once, T seconds in (a picture of it).
        if (!castDone && Args.Has("cast") && Battle is { } cb && Journey.Playtime >= Args.Num("cast", 1))
        {
            castDone = true;
            cb.Aim = null;
            cb.UseAbility(1, 0);
        }
        if (Args.Get("open") is not string want) return;
        tourT -= dt;
        if (tourT > 0) return;
        string[] all = { "inventory", "character", "journal", "map", "pause", "rest", "stash", "shop:harlan", "chapter" };
        var list = want == "all" ? all : want.Split(',');
        if (tourI >= list.Length) return;
        tourT = Args.Num("every", 1.5f);
        if (list[tourI].StartsWith("shop:")) Journey.OpenShop(list[tourI][5..], Rng);
        GD.Print($"open {list[tourI]}");
        CloseOverlay();
        var next = list[tourI++];
        if (next.StartsWith("talk:")) TalkTo(next[5..]);
        else if (next == "draft" && Battle is { } b) { b.GainEmber(b.EmberNext); }
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
