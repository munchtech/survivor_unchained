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
    double autosaveT, fogT, hudT, draftWait, reportT, shareT;
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
        // A crowd melting past a threshold: a kick of the camera and a tick in the hands, a step
        // bigger at each (S-08), never on an ordinary kill.
        sound.Swelled = tier => { cam.AddTrauma(0.08f + 0.04f * tier); Haptics.Add(0.2f * (tier + 1), 0.2f, 0.04f); };
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
        // --charts N: N Wayfinder's charts in the pack, the first plain, the rest finer and higher
        // (pictures of the atlas); --lit PEOPLE:TIER+...: those pairs of the atlas cleared, and
        // their points (e.g. --lit pack:1 for the beta's first tier and point).
        if (Args.Has("charts"))
        {
            var cr = new SurvivorUnchained.Core.Rng(11);
            for (int i = 0; i < (int)Args.Num("charts", 1); i++)
                Journey.GiveChart(SurvivorUnchained.Maps.Charts.Roll(cr, 1 + i / 2, SurvivorUnchained.Maps.MapOffers.Peoples[i % SurvivorUnchained.Maps.MapOffers.Peoples.Length].Id, 1 + i));
        }
        if (Args.Get("lit") is string lit)
            foreach (var pair in lit.Split('+'))
                if (pair.Split(':') is [var pid, var tier] && int.TryParse(tier, out var tn))
                    SurvivorUnchained.Maps.Atlas.Complete(World, new SurvivorUnchained.Maps.Chart { People = pid, Tier = tn });
        // --items A,B[:RARITY],C*N: those things in the pack from the start, N of them for a
        // stack (pictures of the pack, the shop, the forge with a stocked pouch).
        if (Args.Get("items") is string items)
            foreach (var spec in items.Split(','))
            {
                var parts = spec.Split(':');
                var idq = parts[0].Split('*');
                int qty = idq.Length > 1 && int.TryParse(idq[1], out var nq) ? nq : 1;
                int? rar = parts.Length > 1 && int.TryParse(parts[1], out var r) ? r : null;
                // iron_helm:3:of_the_wolf@1+of_the_lantern@2 : a piece with just those affixes, at those grades;
                // a fourth part marks it (iron_helm:3:hale@4+fevered@0:slurried : steeped, and so set).
                if (parts.Length > 2)
                {
                    var affixes = parts[2].Split('+', StringSplitOptions.RemoveEmptyEntries).Select(a => a.Split('@')).Select(a => new AffixRoll { Id = a[0], Tier = a.Length > 1 && int.TryParse(a[1], out var t) ? t : 0 }).ToList();
                    var made = Inventory.Make(Journey.Ch, idq[0], rarity: rar, affixes: affixes);
                    if (parts.Length > 3)
                    {
                        made.Marks = parts[3].Split('+', StringSplitOptions.RemoveEmptyEntries).ToList();
                        if (Crafting.Slurried(made)) made.Heat = 0;
                    }
                    Inventory.AddToPack(Journey.Ch, made);
                }
                else Journey.GiveItem(idq[0], qty, rar);
            }
        // --facts k=v,k=v: the world as a later day would have it (pictures: --facts stream.clear=true);
        // a number or true/false is read as one, anything else as words; --met a,b: those people known.
        if (Args.Get("facts") is string facts)
            foreach (var kv in facts.Split(',').Select(f => f.Split('=', 2)).Where(f => f.Length == 2))
                World.Facts[kv[0]] = kv[1] is "true" or "false" ? kv[1] == "true"
                    : double.TryParse(kv[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var fn) ? fn : kv[1];
        if (Args.Get("met") is string met) foreach (var n in met.Split(',')) World.Npc(n).Flags["met"] = true;
        // --gold N: that much gold in the purse (pictures of a counter with money to spend).
        if (Args.Has("gold")) Journey.Ch.Gold = Args.Num("gold", 0);
        // --xp N: that much experience at once (pictures of the self with points to spend).
        if (Args.Has("xp")) Character.GainXp(Journey.Ch, Args.Num("xp", 0));
        var z = Args.Get("zone") ?? "lowford";
        Arrival? at = null;
        if (Args.Get("at") is string s && s != "boss")
        {
            var p = s.Split(',');
            at = new Arrival(double.Parse(p[0], System.Globalization.CultureInfo.InvariantCulture), double.Parse(p[1], System.Globalization.CultureInfo.InvariantCulture));
        }
        // --zone arena [--offer 0|1|2 --people ID --oaths A,B --tier T]: straight into one of the
        // Wayfinder's arenas (and back to the table after).
        if (z == "arena")
        {
            var o = SurvivorUnchained.Maps.MapOffers.Today(World.Day, 1, 0)[(int)Args.Num("offer", 0)];
            if (Args.Get("people") is string pe) { o = o with { People = pe }; o.Spec.Name = SurvivorUnchained.Maps.MapOffers.Renamed(o.Spec.Name, pe, o.Spec.Seed); }
            if (Args.Get("oaths") is string oa) o.Spec.Oaths = oa.Split(',', StringSplitOptions.RemoveEmptyEntries).ToList();
            if (Args.Has("tier")) o.Spec.Tier = (int)Args.Num("tier", 1);
            // --theme ID --seed N: that ground (pictures of each arena's look, the same place each time).
            if (Args.Get("theme") is string th) o.Spec.Theme = th;
            if (Args.Has("seed")) o.Spec.Seed = (int)Args.Num("seed", 1);
            if (Args.Get("mood") is string mo) o.Spec.Mood = mo;
            var at0 = Waystation.AtTable;
            var spec = Arenas.FromTable(o, "waystation", at0.X, at0.Z, at0.Facing);
            // --boss DEF[:NAME]: a story's foe at the half hour (pictures of Grimtunnel, of Greymuzzle).
            if (Args.Get("boss") is string bo) { var bp = bo.Split(':'); spec.Boss = bp[0]; if (bp.Length > 1) spec.BossName = bp[1].Replace('_', ' '); }
            // --spare: the story lets it go (Greymuzzle spared).
            spec.Spare = Args.Has("spare");
            // --story: told as a story's night (twenty minutes, over at its boss's fall), for pictures of its end.
            if (Args.Has("story")) { spec.Story = true; spec.Minutes = 20; }
            // --night hollow|roost|dig|vault: that story fight's own night (pictures of its place; --stage N for later stages).
            if (Args.Get("night") is string nt) spec = SurvivorUnchained.Play.StoryFights.Spec(nt, Journey.Ctx, "waystation", at0.X, at0.Z, at0.Facing);
            Arenas.Begin(World, spec);
        }
        // --zone map [--tier T --people ID --mods a+b --seed N]: straight into a Wayfinder's map.
        if (z == "map")
            World.Map = new SurvivorUnchained.Maps.Chart
            {
                Tier = (int)Args.Num("tier", 1), People = Args.Get("people") ?? "pack", Seed = (int)Args.Num("seed", 1234),
                Mods = (Args.Get("mods") ?? "").Split('+', StringSplitOptions.RemoveEmptyEntries).ToList(), Name = "The Test Map",
            };
        // --at boss: on a map, at the edge of its ruler's clearing (pictures of the ruler's fight).
        if (z == "map" && Args.Get("at") == "boss")
        {
            var bc = SurvivorUnchained.Maps.MapGen.Generate(World.Map!.Map).Boss;
            at = new Arrival(bc.X, bc.Z - bc.R + 1);
        }
        // --night ID: straight into a story fight by night (a StoryFights id: hollow, roost, dig, vault),
        // back to the Verge at its place after (pictures of a story night, its falls and its loss).
        if (Args.Get("night") is string nid && StoryFights.Get(nid) is { } nf)
        {
            var spot = ZoneMeta.Load("verge").Place("V", nf.Spot);
            Arenas.Begin(World, StoryFights.Spec(nid, Journey.Ctx, "verge", spot.X, spot.Z, 0));
            z = "arena";
        }
        if (z != "lowford")
        {
            // Skipping ahead: the prologue counts as done.
            World.Facts["prologue.done"] = true;
            World.Time = Enum.TryParse<TimeOfDay>(Args.Get("time") ?? "day", true, out var t) ? t : TimeOfDay.Day;
            // --clock S: the day's clock running, S seconds past dawn (pictures of its turns: 590 is ten
            // seconds before dusk, 710 before nightfall, 890 before the nudge, 1070 before the night passes;
            // run with --fixed-fps 60, or the first frame's load is counted as play).
            if (Args.Has("clock"))
            {
                World.Facts["clock.started"] = true;
                World.Clock = Args.Num("clock", 0);
                World.Time = SurvivorUnchained.World.DayClock.At(World.Clock);
            }
            EnterZone(z, "lowford", at);
        }
        else EnterZone(z, null, at);
        // --near ID: stood a few steps from that person (pictures of what shows over their head).
        if (Args.Get("near") is string nearId && zone != null && zone.Actors.TryGetValue(nearId, out var na) && Battle is { } nb)
        {
            nb.Player.X = na.X + 2.2;
            nb.Player.Z = na.Z + 3.2;
        }
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
        if (inTransit || zone is ArenaRun or StoryNight) return;
        CloseOverlay();
        Save("arena");
        Arenas.Begin(World, spec);
        Travel("arena", spec.Name, spec.Sub != "" ? spec.Sub : "Ember arena", null, pull: true);
    }

    /// <summary>Into a Wayfinder's map: the chart is used up as it opens (docs/SKILLS_DESIGN.md §17).</summary>
    public void EnterMap(SurvivorUnchained.Maps.Chart chart)
    {
        if (inTransit || zone is MapRun || zone is ArenaRun or StoryNight) return;
        CloseOverlay();
        Save("map");
        World.Map = chart;
        Travel("map", chart.Name, "A Wayfinder's map");
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
        if (result.WakesInTown)
        {
            // A story night lost (the owner: "having to die for a time"): carried home in the dark,
            // she wakes on Chid's bench in the shrine a day on, as from any fall, and he tells her
            // what it cost; the town's morning comes after him.
            var lines = Journey.WakeAfterLoss(s, null, Rng.NextDouble);
            Travel("waystation", "The shrine", $"Day {World.Day}", null, from: "death");
            if (leaving) Wait(0.8, () => screens.Close());
            Wait(3.9, () => { talkDone = () => { Morning(lines); Shots.Want("morning", 1.5); }; Talk("chid"); Shots.Want("chid", 0.8); });
            return;
        }
        // Back into the same night, with time to hear the town or go straight on to another fight.
        Journey.BackFromFight();
        Travel(s.ReturnZone, null, null, new Arrival(s.ReturnX, s.ReturnZ, s.ReturnFacing));
        if (leaving) Wait(0.8, () => screens.Close());
    }

    ZoneRuntime Make(string id, ZoneMeta meta) => id switch
    {
        "lowford" => new Prologue(this, meta),
        "waystation" => new Waystation(this, meta),
        "verge" => new Verge(this, meta),
        // A story fight with its own stages and boss is a story night; the rest are the table's.
        "arena" => World.Arena!.Story && SurvivorUnchained.Play.Story.StoryScripts.For(World.Arena.Id) is { } fight
            ? new StoryNight(this, currentMap!, World.Arena, fight) : new ArenaRun(this, currentMap!, World.Arena!),
        "map" => StartMap(),
        _ => throw new ArgumentException($"no zone {id}"),
    };

    /// <summary>The survivor as the map opened: what it paid is read against this at its end.</summary>
    CharacterData? mapStart;

    MapRun StartMap()
    {
        mapStart = SurvivorUnchained.Core.Json.Clone(Journey.Ch);
        return new MapRun(this, currentMap!, World.Map!);
    }

    /// <summary>A map is over: what it paid on its own page, the world held behind it.</summary>
    public void MapOver(MapResult r, bool alive)
    {
        var spoils = SurvivorUnchained.Maps.MapSpoils.Between(mapStart ?? Journey.Ch, Journey.Ch);
        Wait(alive ? 1.0 : 2.2, () =>
        {
            if (scene == null || zone is not MapRun) return;
            hudMode = null;
            screens.Show(new MapResultScreen(this, r, spoils));
            scene.SimPaused = true;
            controls.Captured = true;
            hud.Prompt(promptShown = null);
        });
    }

    /// <summary>Out of the map, back to the Waystation; the page stays up until the fade is dark.</summary>
    public void LeaveMap(MapResult r)
    {
        bool leaving = !inTransit;
        Travel("waystation", r.Chart.Name, r.Cleared ? "Cleared" : "The map closes");
        if (leaving) Wait(0.8, () => screens.Close());
    }

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
        objectivesBase = new();
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
        else if (id == "map") { currentMap = SurvivorUnchained.Maps.MapGen.Generate(World.Map!.Map); data = new ZoneData(currentMap); }
        else { currentMap = null; data = new ZoneData(id); }
        // The kit's textures it is built from, decoded side by side first.
        Perf.Lap("prefetch", true);
        Prefetch.Zone(data, Journey != null ? Loadouts.Of(Journey.Ch).Person : null, folk: id != "arena");
        Perf.Lap("its textures, decoded on worker threads");
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
        StopBlend();
        var time = zone.TimeOf(World);
        air.Set(zone.AtmosphereFor(time));
        air.Air(scene!.Data.Place?.Air);
        scene.View.SetNight(time == TimeOfDay.Night);
        scene.View.SetDusk(time == TimeOfDay.Dusk);
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
        var b = Journey.StartBattle(z.Combat, meta.Collision(), scene.HeightAt, start.X, start.Z, start.Facing, (uint)Rng.Next(), arena: z is ArenaRun or StoryNight, ember: z.Ember);
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
            OnDeath(killer == null ? "the dark" : Content.Enemies.Called(killer.Named?.Title, killer.Def.Name));
            return false;
        };
        b.Hooks = h;
    }

    /// <summary>Travel: fade, build the next place, arrive.</summary>
    public void Travel(string to, string? caption = null, string? sub = null) => Travel(to, caption, sub, null);

    /// <summary>Travel; pulled (into an arena), the world swirls in and burns
    /// away instead of fading.</summary>
    void Travel(string to, string? caption, string? sub, Arrival? at, bool pull = false, string? from = null)
    {
        // One journey, one new place, one save: a second press at the gate waits.
        if (inTransit) return;
        inTransit = true;
        from ??= zone?.Id;
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
    public void SetObjectives(List<Tracked> list) { objectivesBase = list; RefreshObjectives(); }
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
        if (zone == null || Mode != "play" || zone is ArenaRun or StoryNight) return;
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

    /// <summary>The pad's rumble (S-14).</summary>
    public readonly Haptics Haptics = new();
    double critFeltAt, kickedAt;

    /// <summary>What of the fight is felt through the pad: weight on the low motor (a blow taken, a
    /// champion or boss down), snap on the high (a critical, a dodge slipped at the last moment).</summary>
    void Feel(CombatEvent e, ref int crits)
    {
        var b = Battle;
        // Her own heavy blows lean the view toward where they landed (S-17): her arts' impacts,
        // a big blast, a critical that takes a third of something big. Never on the crowd's
        // small deaths (late in a night every critical kills), and not oftener than a third of a second.
        double now = Time.GetTicksMsec() / 1000.0;
        if (b != null && now - kickedAt > 0.33)
        {
            Vector3? toward = e switch
            {
                Ev.Ability { Id: "leap" or "bull_rush" or "shield_bash" } a => new Vector3((float)(a.X - b.Player.X), 0, (float)(a.Z - b.Player.Z)) is var d && d.LengthSquared() > 0.01f ? d : new Vector3(Mathf.Cos((float)a.Angle), 0, Mathf.Sin((float)a.Angle)),
                Ev.Explosion x when x.Power > 1 => new Vector3((float)(x.X - b.Player.X), 0, (float)(x.Z - b.Player.Z)),
                Ev.Hit h when h.Crit && !h.Dot && h.MaxHp > b.MaxHp * 2 && h.Amount >= h.MaxHp * 0.35 => new Vector3((float)(h.X - b.Player.X), 0, (float)(h.Z - b.Player.Z)),
                _ => null,
            };
            if (toward is { } tw) { cam.Kick(tw, e is Ev.Ability ? 0.3f : 0.22f); kickedAt = now; }
        }
        switch (e)
        {
            case Ev.Hit h when h.Crit && !h.Dot && crits++ == 0 && Time.GetTicksMsec() / 1000.0 - critFeltAt > 0.25:
                critFeltAt = Time.GetTicksMsec() / 1000.0;
                Haptics.Add(0, 0.2f, 0.03f);
                break;
            case Ev.PerfectDodge: Haptics.Add(0.3f, 0.5f, 0.06f); break;
            case Ev.PlayerHit ph when !ph.Dodged && !ph.Blocked && !ph.Dot && b != null:
                Haptics.Add(0.25f + 0.45f * (float)Math.Min(1, ph.Amount / (b.MaxHp * 0.15)), 0.3f, 0.12f, blow: true);
                break;
            case Ev.LevelUp:
                Haptics.Add(0.4f, 0, 0.08f);
                Haptics.After(0.14, 0.5f, 0, 0.08f);
                break;
            case Ev.Kill k when k.ByPlayer && k.Elite && !k.Boss: Haptics.Add(0.7f, 0, 0.15f); break;
            case Ev.Victory: Haptics.Add(1, 0.4f, 0.4f, peak: true); break;
            case Ev.PlayerDeath: Haptics.Add(1, 0, 0.4f, blow: true, peak: true); break;
            case Ev.Evolve { Chest: false }: Haptics.Add(0.6f, 0.4f, 0.25f); break;
            case Ev.Rise: Haptics.Add(0.9f, 0.2f, 0.3f, blow: true, peak: true); break;
        }
    }

    void OnEvents(List<CombatEvent> evs)
    {
        Journey.BankArt(Battle);
        Journey.BankGold(Battle);
        sound.Events(evs, Battle);
        zone?.Events(evs);
        int crits = 0;
        foreach (var e in evs)
        {
            if (Shots.On("boss") || Shots.On("casts")) BossShot(e);
            Feel(e, ref crits);
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
                    Shots.Want("evolve", 0.25);
                    Shots.Want("evolve", 0.9);
                    break;
                case Ev.Rise:
                    // The blow that should have ended her, held: the world slows while she goes
                    // cold and gets up (BattleFx.Rise draws it).
                    scene?.Slow(1.1);
                    foreach (var s in new[] { 0.1, 0.5, 0.9, 1.08, 1.16, 1.24, 1.32, 1.45, 2.0, 3.0 }) Shots.Want("rise", s);
                    break;
                case Ev.Bark bk:
                    // A named voice in a fight (the Warden, Grimtunnel) is heard over everything, when its line shows
                    // (one of theirs at a time: the next waits for the last to be said).
                    var said = bk.Text;
                    scene?.Voices.Bark(bk.Text, new Vector3((float)bk.X, (float)scene.HeightAt(bk.X, bk.Z), (float)bk.Z), bk.Speaker, bk.Speaker == null,
                        shown: bk.Speaker != null ? () => voice.Shout(said)?.Sec ?? 0 : null);
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
    /// stagger, its arrival and what is announced (Shots.Want). --on casts: a run of
    /// frames, fifteen a second, through each creature's marked cast and a second after
    /// it (judging a slam or a call as the player sees it).</summary>
    static void BossShot(CombatEvent e)
    {
        switch (e)
        {
            case Ev.Telegraph t when Shots.On("casts") && t.Id >= 0 && t.Hostile:
                for (int i = 0; i * (1 / 15.0) < t.Duration + 1; i++) Shots.Want($"cast{t.Id}", i / 15.0);
                break;
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
            // Booked to its kind of play: the story's share is measured, not guessed.
            Journey.Clock(dt, zone switch
            {
                ArenaRun run => run.Spec.Story ? "story night" : "table night",
                StoryNight => "story night",
                _ => zone.Id switch { "lowford" => "prologue", "waystation" => "town", "map" => "map", _ => "wild" },
            });
            // The day's own clock: free play moves it, and each turn is staged (GameClock).
            TickDay(dt);
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
            if (zone is StoryNight sn && hudMode == null && camSaved == null && !Args.Has("cam")) cam.TargetDistance = (float)sn.CameraDistance;
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
            Haptics.Update(dt, Settings.Current.Rumble, controls.UsingPad);
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
            hud.Frame(Battle, ch.Gold, Journey.Draughts, (ch.Level, ch.Xp / Character.XpForLevel(ch.Level)));
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
        // Names over heads and barks have no place in a cinematic's picture either.
        scene.Voices.Quiet = hudMode == "dialogue" || screens.Current != null || cine != null;
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
        if (zone == null || scene == null || zone is ArenaRun or StoryNight || Battle is not { } b || inTransit) return null;
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
    bool hordeDone, dropsDone, lootDone, castDone, giveDone, minuteDone, chestDone, barksDone, answerDone, fallDone, litDone;
    int dieIx;
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
        // --loot [--loot-at T]: one of every tier of loot falling round the survivor T seconds in (3 by
        // default), each landing as shown loot does (Ev.Drop), for pictures of their light.
        if (!lootDone && Args.Has("loot") && Battle is { } lootB && Journey.Playtime >= Args.Num("loot-at", 3))
        {
            lootDone = true;
            var tiers = new[] { LootTier.Common, LootTier.Uncommon, LootTier.Rare, LootTier.Epic, LootTier.Set, LootTier.Legendary, LootTier.Storied, LootTier.Chart, LootTier.Quest, LootTier.Rare, LootTier.Epic };
            for (int i = 0; i < tiers.Length; i++)
            {
                double a = i * Math.Tau / tiers.Length + 0.3, d = 3.2 + (i % 3) * 1.1;
                var k = lootB.SpawnPickup(tiers[i] is LootTier.Quest ? PickupKind.Quest : PickupKind.Item, lootB.Player.X + Math.Cos(a) * d, lootB.Player.Z + Math.Sin(a) * d, 0.01);
                if (k == null) continue;
                k.Loot = (int)tiers[i]; k.Tier = Math.Min(5, (int)tiers[i]); k.Vx = k.Vz = 0; k.Age = -600;
                lootB.Events.Emit(new Ev.Drop { Tier = k.Loot, X = k.X, Z = k.Z, Kind = k.Kind });
            }
        }
        // --give A,B[:RANK][@EVOLUTION],+PASSIVE[:RANK]: a build in hand from the start
        // (pictures of weapons, of the draft with an arsenal), the arena's opening blessing passed over.
        // --minute M: the arena's clock set to M minutes (pictures of its boss: --minute 29.9); --won: and the night won.
        if (!minuteDone && Args.Has("minute") && zone is ArenaRun mr && Battle != null)
        {
            minuteDone = true;
            mr.SkipTo(Args.Num("minute", 29.9f) * 60);
            if (Args.Has("won")) mr.WinNow();
        }
        // --stage N: a story night begun at its Nth stage (from 0; its stage count is the boss), the
        // ground behind opened and the build the stages before would have left her (pictures and play of a
        // stage or the boss: --stage 3).
        if (!minuteDone && Args.Has("stage") && zone is StoryNight sn2 && Battle != null)
        {
            minuteDone = true;
            sn2.SkipTo((int)Args.Num("stage", 0), floors: true);
        }
        // --lit: a story night's deadfalls all burning (pictures of them alight).
        if (!litDone && Args.Has("lit") && zone is StoryNight sn3 && Battle != null)
        {
            litDone = true;
            foreach (var f in sn3.Fires) { f.Lit = 9999; f.EverLit = true; scene.SetLit(f.Light, true); }
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
        // --fall-at T: a killing blow at T seconds, for pictures of her rise (give her
        // +from_the_ashes for Cold, Then Not; otherwise she has Not Yet for it).
        if (!fallDone && Args.Has("fall-at") && Battle is { } fb && Journey.Playtime >= Args.Num("fall-at", 3))
        {
            fallDone = true;
            if (fb.Player.Ashes == 0) fb.Player.Revives = Math.Max(fb.Player.Revives, 1);
            fb.Player.Iframes = 0;
            fb.Player.Hp = 1;
            fb.HurtPlayer(fb.MaxHp * 9, School.Physical, "a test", null);
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
        // --die T1,T2: again at each time listed (a story night's falls: the rise, then the loss).
        var dies = (Args.Get("die") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries);
        if (dieIx < dies.Length && Battle is { } kb && kb.Player.Alive
            && Journey.Playtime >= double.Parse(dies[dieIx] == "" ? "1" : dies[dieIx], System.Globalization.CultureInfo.InvariantCulture))
        {
            dieIx++;
            var killer = kb.SpawnEnemy("risen", kb.Player.X, kb.Player.Z + (Args.Has("behind") ? -1.2 : 1.2));
            kb.HurtPlayerRaw(kb.Player.Hp + 1e6, School.Physical, "test", killer);
        }
        // --answer T: the night answered T seconds in, as if the key were held (pictures of the pull).
        if (!answerDone && Args.Has("answer") && Journey.Playtime >= Args.Num("answer", 1) && World.Time == TimeOfDay.Night && zone is { ClockRuns: true })
        {
            answerDone = true;
            AnswerNight();
        }
        // --barks T: T seconds in, a crowd of lines at once by her (pictures of them waiting their
        // turns and standing clear of each other): one voice's three, two others close by, an alert.
        if (!barksDone && Args.Has("barks") && Battle is { } wb && Journey.Playtime >= Args.Num("barks", 1))
        {
            barksDone = true;
            double x = wb.Player.X, z = wb.Player.Z;
            foreach (var t in new[] { "Lamps are lit... stay where they reach...", "Lie down.", "NONE CROSS AFTER DARK." })
                wb.Events.Emit(new Ev.Bark { X = x + 2, Z = z - 1, Text = t, Speaker = "The Ford-Warden" });
            wb.Events.Emit(new Ev.Bark { X = x - 1.5, Z = z - 0.5, Text = "Something moves in the reeds." });
            wb.Events.Emit(new Ev.Bark { X = x - 0.5, Z = z - 1.2, Text = "Hold the line!", Speaker = "Brannoc" });
            wb.Events.Emit(new Ev.Bark { X = x, Z = z, Text = "Blocked" });
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
            // --clicks X:Y,rX:Y,...: then the mouse goes there and clicks (r: the right button), in turn,
            // through the same input a hand would give (pictures of a page worked by mouse).
            else if (Args.Get("clicks") is string clicks && clickI < clicks.Split(',').Length)
            {
                tourT = Args.Num("click-every", 0.8f);
                ClickAt(clicks.Split(',')[clickI++]);
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
        // A map's end, with sample spoils (pictures of the map's result; on a map; --fell: closed at the third fall).
        else if (next == "mapresult" && World.Map is { } chart && zone is MapRun)
        {
            var ch = Journey.Ch;
            var gear = new[] { ("copper_ring", 1), ("leather_cap", 1), ("chain_shirt", 2), ("bone_amulet", 2), ("iron_helm", 3) }
                .Select(g => Inventory.Make(ch, g.Item1, rarity: g.Item2)).ToList();
            var next1 = Inventory.Make(ch, SurvivorUnchained.Maps.Charts.Item, 1, 2);
            next1.Chart = SurvivorUnchained.Maps.Charts.Roll(new SurvivorUnchained.Core.Rng(7), chart.Tier + 1, chart.People, 3);
            bool fell = Args.Has("fell");
            var r = new MapResult(chart, !fell, fell ? 486 : 641, fell ? 503 : 812, fell ? MapRun.FallsAllowed : 1, fell ? 9 : 14, 16, fell ? null : 62, !fell,
                fell ? new() { ["wolf_pelt"] = 3, ["ember_shard"] = 2 } : new());
            var spoils = new SurvivorUnchained.Maps.MapSpoils(fell ? gear.Take(2).ToList() : gear, fell ? new() : new() { next1 },
                fell ? new() { ["wolf_pelt"] = 3 } : new() { ["wolf_pelt"] = 6, ["ember_shard"] = 4 }, fell ? 120 : 488);
            hudMode = null;
            screens.Show(new MapResultScreen(this, r, spoils));
            if (scene != null) scene.SimPaused = true;
        }
        else Open(next);
    }

    int clickI;

    /// <summary>A click as the mouse gives it: moved there, pressed, released ("r640:480" for the right button).</summary>
    void ClickAt(string spec)
    {
        bool right = spec.StartsWith('r');
        var xy = spec.TrimStart('r').Split(':');
        if (xy.Length != 2 || !float.TryParse(xy[0], System.Globalization.CultureInfo.InvariantCulture, out var x)
            || !float.TryParse(xy[1], System.Globalization.CultureInfo.InvariantCulture, out var y)) return;
        var at = new Vector2(x, y);
        controls.UsingPad = false;
        Ui.Nav.KeyMode = false;
        var vp = GetViewport();
        vp.PushInput(new InputEventMouseMotion { Position = at, GlobalPosition = at });
        var button = right ? MouseButton.Right : MouseButton.Left;
        vp.PushInput(new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = button, Pressed = true });
        vp.PushInput(new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = button, Pressed = false });
        GD.Print($"click {spec}");
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
        // The story's share of the play so far, once a minute (Journey.StoryShare).
        if ((shareT -= Args.Num("log", 5)) <= 0 && Journey.World.TimeIn.Count > 0)
        {
            shareT = 60;
            var (town, strict) = Journey.StoryShare;
            GD.Print($"time: story {town * 100:0}% (without the town {strict * 100:0}%): {string.Join(", ", Journey.World.TimeIn.Select(kv => $"{kv.Key} {(int)kv.Value / 60}:{(int)kv.Value % 60:00}"))}");
        }
        reportT = Args.Num("log", 5);
        var b = Battle;
        var p = b?.Player;
        int foes = b?.Enemies.Count ?? 0;
        var dbg = zone?.Debug() is { Count: > 0 } d ? string.Join(" ", d.Take(6).Select(kv => $"{kv.Key}={kv.Value}")) : "";
        var (drawn, dead) = scene!.Crowd.Counts;
        var (gibs, splats) = scene.Fx.Gore.Counts;
        GD.Print($"[{scene.Time,6:0.0}s] {zone?.Id} hp {p?.Hp:0}/{b?.MaxHp:0} ember {b?.EmberLevel} kills {b?.KillCount} foes {foes} (drawn {drawn}, lying {dead}, gibs {gibs}, blood {splats}) at {p?.X:0},{p?.Z:0} {Overlay} clock {World.Time} {World.Clock:0.0}s day {World.Day} {dbg}{FrameCost()}{(synth.Live ? $" | sound {sound.Music.Mood} voices {synth.Voices} mix {synth.MixCost / Math.Max(1e-9, synth.Mixed) * 100:0}% heard {synth.Mixed:0}s skips {synth.Skips} queue {synth.Queue / synth.Rate * 1000:0}ms" : "")}");
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
        // --perf-flip A,B [--perf-flip-every S]: these taken out every other S
        // seconds (default 1) and put back, the frame's "flip" counter 1 while
        // out. One run measures both ways under the same load from the GPU's
        // other users (it is shared): her, furshadow (her fur's shadows), crowd,
        // grass, sunshadows, ssao, msaa;
        // or quality:Q, scale:S (that quality or resolution while out).
        if (Args.Get("perf-flip") is string flips)
        {
            var flipped = flips.Split(',').ToHashSet();
            double every = Args.Num("perf-flip-every", 1);
            var clock = System.Diagnostics.Stopwatch.StartNew();
            bool outNow = false, wasOut = false;
            string q0 = Settings.Current.Quality, s0 = Settings.Current.Scale;
            string? qOut = flipped.FirstOrDefault(f => f.StartsWith("quality:"))?[8..], sOut = flipped.FirstOrDefault(f => f.StartsWith("scale:"))?[6..];
            Perf.CounterNames = [.. Perf.CounterNames, "flip"];
            var counters = Perf.Counters;
            Perf.Counters = a => { counters(a); a[^1] = outNow ? 1 : 0; };
            perf.Each = () =>
            {
                if (scene == null) return;
                outNow = (int)(clock.Elapsed.TotalSeconds / every) % 2 == 1;
                bool on = !outNow;
                if ((qOut ?? sOut) != null && outNow != wasOut)
                {
                    Settings.Current.Quality = outNow ? qOut ?? q0 : q0;
                    Settings.Current.Scale = outNow ? sOut ?? s0 : s0;
                    Graphics.Apply(Settings.Current, air, GetViewport(), scene);
                }
                wasOut = outNow;
                if (flipped.Contains("her") && scene.Player != null) scene.Player.Visible = on;
                if (flipped.Contains("furshadow") && scene.Player != null)
                    foreach (var n in scene.Player.FindChildren("*fur*", "MeshInstance3D", true, false))
                        ((MeshInstance3D)n).CastShadow = on ? GeometryInstance3D.ShadowCastingSetting.On : GeometryInstance3D.ShadowCastingSetting.Off;
                if (flipped.Contains("crowd")) scene.Crowd.Visible = on;
                if (flipped.Contains("grass") && scene.View.GetNodeOrNull<Node3D>("Grass") is { } g) g.Visible = on;
                var t = Graphics.Current;
                if (flipped.Contains("sunshadows")) air.Key.ShadowEnabled = on;
                if (flipped.Contains("ssao")) air.Env.SsaoEnabled = on && t.Ssao;
                if (flipped.Contains("msaa")) GetViewport().Msaa3D = on ? t.Msaa : Viewport.Msaa.Disabled;
            };
            return;
        }
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
