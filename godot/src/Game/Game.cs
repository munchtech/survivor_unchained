using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
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
/// fade between places and the fall, and saves.
///
/// Until the title and creation screens come over, it starts a journey
/// straight away (or continues the last one):
///   --quick warden|reaver|arcanist|stalker   a new survivor of that calling
///   --zone lowford|waystation|verge          where (past the prologue: it counts as done)
///   --time day|night|dusk|dawn               the hour, past the prologue
///   --at X,Z                                 where in it
///   --continue                               the last journey saved
///   --auto                                   a crude player drives (Autopilot.cs)
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
    public bool InTransit => inTransit;
    /// <summary>A menu, a conversation or the draft has the screen.</summary>
    public string? Overlay { get; private set; }

    Controls controls = null!;
    GameHud hud = null!;
    Atmosphere air = null!;
    Camera3D camera = null!;
    FollowCamera cam = null!;
    WorldScene? scene;
    ZoneRuntime? zone;
    Saves saves = null!;
    Interactable? near;
    string? promptShown;
    readonly List<(double T, Action Fn)> later = new();
    bool inTransit;
    double autosaveT, fogT, hudT, draftWait;
    Autopilot? auto;
    public Autopilot? Pilot => auto;

    public override void _Ready()
    {
        controls = new Controls();
        AddChild(controls);
        camera = new Camera3D { Fov = 34, Near = 0.5f, Far = 1400, Current = true };
        AddChild(camera);
        cam = new FollowCamera(camera);
        air = new Atmosphere();
        AddChild(air);
        hud = new GameHud();
        AddChild(hud);
        AddChild(new Shots());
        saves = new Saves(ProjectSettings.GlobalizePath("user://saves"));
        controls.On(OnAction);
        if (Args.Has("auto")) auto = new Autopilot(this) { Idle = Args.Get("auto") == "idle" };
        Start();
    }

    /* ------------------------------------------------------------ start -- */

    void Start()
    {
        if (Args.Has("continue") && saves.LastSlot() is int slot && saves.Read(slot) is SaveData d)
        {
            Journey = Journey.From(d, slot);
            Hook();
            EnterZone(d.Location.Zone, null, new Arrival(d.Location.X, d.Location.Z, d.Location.Facing));
            hud.Fade(0, 1.2);
            return;
        }
        var arch = Args.Get("quick") is string q && q is "warden" or "reaver" or "arcanist" or "stalker" ? q : "warden";
        var a = Callings.Archetype(arch);
        Journey = Journey.Begin(new CreationChoice
        {
            Name = Args.Get("name") ?? "Ashe", Archetype = arch, Background = Args.Get("bg") ?? "hunter", Palette = a.Palettes[0].Id,
            WeaponItem = Args.Get("weapon") ?? a.Weapons[0], Ability = a.Abilities[0], StartBoon = Args.Get("blessing") ?? Content.Boons.StartBlessings[0],
        }, (uint)Rng.Next());
        Journey.Slot = FreeSlot();
        Hook();
        var z = Args.Get("zone") ?? "lowford";
        Arrival? at = null;
        if (Args.Get("at") is string s)
        {
            var p = s.Split(',');
            at = new Arrival(double.Parse(p[0], System.Globalization.CultureInfo.InvariantCulture), double.Parse(p[1], System.Globalization.CultureInfo.InvariantCulture));
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
    }

    int FreeSlot()
    {
        var used = saves.Slots().Select(s => s.Slot).ToHashSet();
        for (int i = 0; i < Saves.SlotCount; i++) if (!used.Contains(i)) return i;
        return saves.Slots().OrderBy(s => s.SavedAt).First().Slot;
    }

    void Hook()
    {
        Journey.OnToast = t => hud.Toast(t);
        Journey.OnAnnounce = a => hud.Announce(a);
    }

    /* ------------------------------------------------------------ zones -- */

    ZoneRuntime Make(string id, ZoneMeta meta) => id switch
    {
        "lowford" => new Prologue(this, meta),
        "waystation" => new Waystation(this, meta),
        "verge" => new Verge(this, meta),
        _ => throw new ArgumentException($"no zone {id}"),
    };

    void LeaveZone()
    {
        later.Clear();
        zone?.Dispose();
        zone = null;
        if (scene != null) { scene.QueueFree(); RemoveChild(scene); }
        scene = null;
        near = null;
        hud.Prompt(promptShown = null);
        hud.Boss(null);
        hud.Hint(CurrentHint = null);
        cam.FocusOverride = null;
    }

    public void EnterZone(string id, string? from, Arrival? at = null)
    {
        LeaveZone();
        var data = new ZoneData(id);
        scene = new WorldScene(data, cam);
        AddChild(scene);
        scene.Move = () => auto?.Move ?? (controls.Captured ? (0, 0) : (controls.MoveX, controls.MoveZ));
        scene.Pressed = a => (auto?.Take(a) ?? false) || (!controls.Captured && controls.Pressed(a));
        scene.OnStep = dt => zone?.Step(dt);
        scene.OnEvents = OnEvents;
        zone = Make(id, data.Meta);
        var time = zone.TimeOf(World);
        air.Set(zone.AtmosphereFor(time));
        scene.View.SetNight(time == TimeOfDay.Night);
        EnterPlay(zone, from, at);
    }

    void EnterPlay(ZoneRuntime z, string? from, Arrival? at)
    {
        Overlay = null;
        scene!.SimPaused = false;
        var start = at ?? z.ArrivalFrom(from);
        var meta = scene.Data.Meta;
        var b = Journey.StartBattle(z.Combat, meta.Collision(), scene.HeightAt, start.X, start.Z, start.Facing, (uint)Rng.Next());
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
    public void Travel(string to, string? caption = null, string? sub = null)
    {
        // One journey, one new place, one save: a second press at the gate waits.
        if (inTransit) return;
        inTransit = true;
        var from = zone?.Id;
        Journey.Capture(Battle);
        if (scene != null) scene.SimPaused = true;
        controls.Captured = true;
        hud.Fade(1, 0.8, caption, sub);
        Wait(0.85, () =>
        {
            EnterZone(to, from);
            Save("travel");
            Wait(caption != null ? 1.4 : 0.2, () =>
            {
                hud.Fade(0, 1.4);
                controls.Captured = false;
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
    public void Say(string text, string? who = null, double seconds = 4) => hud.Say(text, who, seconds);
    public void Toast(Toast t) => hud.Toast(t);
    public void Announce(Announcement a) => hud.Announce(a);
    public void After(double seconds, Action fn) => later.Add((seconds, fn));
    public bool GiveItem(string def, int qty = 1, int? rarity = null) => Journey.GiveItem(def, qty, rarity);
    public void ReturnItem(ItemInstance it) => Journey.ReturnItem(it);
    public void SetBoss(BossBar? bar) => hud.Boss(bar);
    public void SetObjectives(List<Tracked> list) => hud.Objectives(list);
    public void SetHint(Hint? hint) => hud.Hint(CurrentHint = hint);
    public void SetAtmosphere(AtmospherePreset p, bool rebuild = true) => air.Set(p, rebuild);
    public void Capture(bool on) => controls.Captured = on;
    string? draftTip;
    public void SetDraftTip(string tip) => draftTip = tip;
    public void AnnounceZone() { if (zone != null) hud.Announce(new Announcement(zone.Name, zone.Region, "zone", 4.2)); }

    public void Revived(double x, double z)
    {
        scene?.Player?.Revive();
        cam.Snap((float)x, (float)(scene?.HeightAt(x, z) ?? 0), (float)z);
    }

    public string KeyLabel(string action) =>
        Enum.TryParse<Act>(action, true, out var a) ? controls.KeyLabel(a) : action == "ultimate" ? controls.KeyLabel(Act.Ultimate) : action.ToUpperInvariant();

    (Vector3 Pos, Vector3 Look) showT, showNow;
    bool showing;

    public void Showcase((double X, double Y, double Z)? pos, (double X, double Y, double Z) look = default)
    {
        if (scene == null) return;
        if (pos is not var (x, y, z)) { showing = false; scene.Showcase = null; return; }
        showT = (new Vector3((float)x, (float)y, (float)z), new Vector3((float)look.X, (float)look.Y, (float)look.Z));
        if (!showing) showNow = (camera.GlobalPosition, showT.Look);
        showing = true;
    }

    public void Save(string reason)
    {
        if (zone == null) return;
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
        string? text = null;
        if (best != null)
        {
            var locked = best.Locked?.Invoke();
            var hint = best.Hint?.Invoke();
            text = $"[{controls.KeyLabel(Act.Interact)}]  {best.Verb}  {best.Name}" + (hint != null ? $"  ·  {hint}" : "") + (locked != null ? $"  ({locked})" : "");
        }
        if (text != promptShown) hud.Prompt(promptShown = text);
    }

    bool OnAction(Act a)
    {
        if (scene == null || inTransit) return false;
        if (Overlay == "draft") return DraftKey(a);
        if (Overlay == "dialogue") return DialogueKey(a);
        if (Overlay == "pause")
        {
            if (a is Act.Pause or Act.Cancel or Act.Confirm) { ClosePause(); return true; }
            return false;
        }
        if (a == Act.Pause) { OpenPause(); return true; }
        if (a == Act.Interact && near != null)
        {
            var locked = near.Locked?.Invoke();
            if (locked != null) hud.Toast(new Toast(ToastKind.Warning, locked));
            else near.Act();
            return true;
        }
        if (a == Act.Ultimate) { Journey.Quaff(Battle); return true; }
        return false;
    }

    void OpenPause()
    {
        Overlay = "pause";
        scene!.SimPaused = true;
        hud.Fade(0.55f, 0.2, "Paused", $"{Journey.Ch.Name}  ·  Day {World.Day}  ·  {Journey.Ch.Stats.Kills} slain   [Esc] to go on");
    }

    void ClosePause()
    {
        Overlay = null;
        scene!.SimPaused = false;
        hud.Fade(0, 0.2);
        Save("pause");
    }

    /* ------------------------------------------------------------ draft -- */

    List<Offer> offers = new();
    bool banishing;

    void UpdateDraft(double dt)
    {
        var b = Battle;
        if (b != null && b.DraftOwed && Overlay == null && b.Player.Alive && !inTransit)
        {
            // A beat after the flare, then time stops.
            draftWait += dt;
            if (draftWait > 0.35) { draftWait = 0; OpenDraft(); }
        }
        else draftWait = 0;
    }

    void OpenDraft()
    {
        var b = Battle!;
        scene!.SimPaused = true;
        Overlay = "draft";
        Present(LevelUp.Draft(b, b.Stats.Get(Stat.Luck) >= 1.5 ? 4 : 3));
    }

    void Present(List<Offer> list)
    {
        var b = Battle!;
        offers = list;
        banishing = false;
        var tip = draftTip;
        draftTip = null;
        hud.Draft(new DraftView(LevelUp.DraftLevel(b), LevelUp.BlessingNext(b), list, b.Rerolls, b.Banishes, b.PendingLevels + b.PendingBlessings.Count - 1, tip,
            Pick, Reroll, Banish));
    }

    public void Pick(int i)
    {
        var b = Battle;
        if (b == null || Overlay != "draft" || i < 0 || i >= offers.Count) return;
        var o = offers[i];
        LevelUp.Choose(b, o);
        if (o.Kind == OfferKind.Weapon) hud.Toast(new Toast(ToastKind.Level, $"{o.Title} joins your arsenal"));
        if (b.DraftOwed) Present(LevelUp.Draft(b, offers.Count));
        else CloseDraft();
    }

    void Reroll()
    {
        var b = Battle!;
        if (b.Rerolls <= 0) return;
        b.Rerolls--;
        Present(LevelUp.Draft(b, offers.Count));
    }

    void Banish(int i)
    {
        var b = Battle!;
        if (i < 0 || i >= offers.Count || b.Banishes <= 0 || offers[i].Kind == OfferKind.Evolve) return;
        b.Banishes--;
        b.BannedCards.Add(offers[i].Id);
        Present(LevelUp.Draft(b, offers.Count));
    }

    void CloseDraft()
    {
        hud.Draft(null);
        Overlay = null;
        scene!.SimPaused = false;
        controls.ClearLatches();
    }

    bool DraftKey(Act a)
    {
        int pick = a switch { Act.Pick1 => 0, Act.Pick2 => 1, Act.Pick3 => 2, Act.Pick4 => 3, _ => -1 };
        if (pick >= 0)
        {
            if (banishing) Banish(pick); else Pick(pick);
            return true;
        }
        if (a == Act.Reroll) { Reroll(); return true; }
        if (a == Act.Banish) { banishing = !banishing; if (banishing) hud.Toast(new Toast(ToastKind.Warning, "Banish which? (1-4)")); return true; }
        return a is Act.Confirm or Act.Cancel or Act.Pause;
    }

    /* --------------------------------------------------------- dialogue -- */

    DialogueRunner? runner;
    string? talkNpc;
    float? camSaved;
    Presented? shown;

    public void Talk(string id)
    {
        var convo = SurvivorUnchained.World.Dialogue.Find(id);
        if (convo == null || scene == null) return;
        var r = new DialogueRunner(convo, Journey.Ctx);
        var p = r.Start();
        if (p == null) return;
        runner = r;
        talkNpc = id;
        var b = Battle;
        if (zone!.Actors.TryGetValue(id, out var actor) && b != null)
        {
            actor.Talking = true;
            actor.Gesture();
            var y = (float)scene.HeightAt(actor.X, actor.Z);
            cam.FocusOverride = new Vector3((float)(actor.X + b.Player.X) / 2, y + 1, (float)(actor.Z + b.Player.Z) / 2);
            camSaved = cam.TargetDistance;
            cam.TargetDistance = 12.5f;
            b.Player.Facing = Math.Atan2(actor.X - b.Player.X, actor.Z - b.Player.Z);
        }
        Overlay = "dialogue";
        scene.SimPaused = true;
        scene.Voices.Quiet = true;
        hud.Prompt(promptShown = null);
        ShowLine(p);
    }

    void ShowLine(Presented p)
    {
        shown = p;
        var id = talkNpc!;
        var d = Lore.Person(id);
        Lore.Speakers.TryGetValue(id, out var sp);
        var s = World.Npc(id);
        hud.Dialogue(new DialogueView(d?.Name ?? sp?.Name ?? id, d?.Title ?? sp?.Title ?? "", d != null ? Rules.Attitude(s) : "",
            p.Speaker == "player" ? "player" : p.Speaker == "narrator" ? "narrator" : "npc", p.Text, p.Choices, p.Choices.Count == 0, Choose, Advance));
    }

    public void Choose(int index)
    {
        var r = runner;
        if (r == null) return;
        var (next, action) = r.Choose(index);
        Journey.OnTouch();
        if (action != null && !DialogueAction(action)) { EndDialogue(); return; }
        if (next != null) ShowLine(next);
        else if (action == null) EndDialogue();
        else if (r.Node != null && r.Present() is Presented again) ShowLine(again);
        else EndDialogue();
    }

    public void Advance()
    {
        var r = runner;
        if (r == null) return;
        var p = r.Advance();
        if (p != null) ShowLine(p); else EndDialogue();
    }

    void EndDialogue()
    {
        if (talkNpc != null && zone?.Actors.TryGetValue(talkNpc, out var actor) == true) actor.Talking = false;
        cam.FocusOverride = null;
        if (camSaved is float d) { cam.TargetDistance = d; camSaved = null; }
        runner = null;
        talkNpc = null;
        shown = null;
        hud.Dialogue(null);
        if (Overlay == "dialogue") Overlay = null;
        if (scene != null) { scene.SimPaused = false; scene.Voices.Quiet = false; }
        controls.ClearLatches();
        Save("talk");
    }

    bool DialogueKey(Act a)
    {
        if (shown == null) return false;
        int pick = a switch { Act.Pick1 => 0, Act.Pick2 => 1, Act.Pick3 => 2, Act.Pick4 => 3, _ => -1 };
        if (shown.Choices.Count == 0)
        {
            if (a is Act.Confirm or Act.Interact or Act.Dash || pick == 0) { Advance(); return true; }
            return true;
        }
        if (pick >= 0 && pick < shown.Choices.Count && shown.Choices[pick].Enabled) { Choose(shown.Choices[pick].Index); return true; }
        return true;
    }

    /// <summary>What a conversation opens. True to stay in it.</summary>
    bool DialogueAction(string a)
    {
        switch (a)
        {
            case "trade": case "sell": case "stash": case "fortune":
                // The shop, the storeroom and the chapter's end come with the rest of the interface.
                hud.Toast(new Toast(ToastKind.World, a == "fortune" ? "Vonnra's fortune is not in this build yet" : "Trading is not in this build yet", "It comes with the rest of the interface"));
                return false;
            case "rest":
                Rest();
                return false;
        }
        return Journey.Service(a, Battle);
    }

    /// <summary>A night's sleep at the inn: the world moves on a day.</summary>
    void Rest()
    {
        var b = Battle;
        bool hadEmber = Journey.Expedition != null || (b?.EmberLevel ?? 1) > 1;
        var lines = Journey.Sleep(b, hadEmber, Rng.NextDouble);
        if (lines == null) { hud.Toast(new Toast(ToastKind.Warning, $"A bed costs {Journey.RestCost} gold")); return; }
        hud.Fade(1, 0.9, $"Day {World.Day}", "You sleep");
        Wait(1.2, () =>
        {
            air.Set(zone!.AtmosphereFor(TimeOfDay.Day));
            scene?.View.SetNight(false);
            hud.ZoneInfo(zone.Name, zone.Region, World.Day, TimeOfDay.Day);
            foreach (var l in lines) hud.Toast(new Toast(ToastKind.World, l, null, null, null, 10));
            Save("rest");
            hud.Fade(0, 1.4);
        });
    }

    /* ------------------------------------------------------------ frame -- */

    void OnEvents(List<CombatEvent> evs)
    {
        zone?.Events(evs);
        foreach (var e in evs)
        {
            switch (e)
            {
                case Ev.Announce an:
                    hud.Announce(new Announcement(an.Title, an.Subtitle, an.Tone?.ToString().ToLowerInvariant() ?? "info", an.Subtitle is { Length: > 60 } ? 5 : 3.6, an.Kicker));
                    break;
                case Ev.Discovery d:
                    if (!World.Codex.Contains(d.Id)) World.Codex.Add(d.Id);
                    if (Content.Discoveries.All.FirstOrDefault(x => x.Id == d.Id) is { } pair) hud.Toast(new Toast(ToastKind.Lore, pair.Name, "A new discovery, remembered in the codex", null, null, 9));
                    break;
                case Ev.Bark bk:
                    scene?.Voices.Bark(bk.Text, new Vector3((float)bk.X, (float)scene.HeightAt(bk.X, bk.Z), (float)bk.Z), bk.Speaker, bk.Speaker == null);
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
        if (scene == null || zone == null) return;
        double dt = Math.Min(delta, 0.1);
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
        // A held camera drifts toward its mark, breathing a little.
        if (showing)
        {
            float breathe = Mathf.Sin((float)scene.Time * 0.35f) * 0.08f;
            var target = showT.Pos + new Vector3(breathe, breathe * 0.5f, 0);
            float k1 = 1 - Mathf.Exp(-1.8f * (float)dt), k2 = 1 - Mathf.Exp(-2.2f * (float)dt);
            showNow = (showNow.Pos.Lerp(target, k1), showNow.Look.Lerp(showT.Look, k2));
            scene.Showcase = showNow;
        }
        zone.Frame(dt);
        RunLater(dt);
        scene.Update(dt);
        UpdateDraft(dt);
        hudT -= dt;
        if (hudT <= 0)
        {
            hudT = 1.0 / 12;
            hud.Bars(Battle, Journey.Ch.Gold, Inventory.Count(Journey.Ch, "health_draught"));
        }
        hud.SetBruise(scene.Bruise);
        Report(dt);
        // Fallen: the world loses its colour.
        air.Env.AdjustmentSaturation = Mathf.Lerp(air.Env.AdjustmentSaturation, Battle?.Player.Alive == false ? 0.2f : 1f, 1 - Mathf.Exp(-2 * (float)dt));
    }

    double reportT;

    /// <summary>--log S: a line every S seconds of how it is going (for runs
    /// without a screen: Godot's --headless, --quit-after).</summary>
    void Report(double dt)
    {
        if (!Args.Has("log")) return;
        reportT -= dt;
        if (reportT > 0) return;
        reportT = Args.Num("log", 5);
        var b = Battle;
        var p = b?.Player;
        int foes = b?.Enemies.Count ?? 0;
        var dbg = zone?.Debug() is { Count: > 0 } d ? string.Join(" ", d.Take(4).Select(kv => $"{kv.Key}={kv.Value}")) : "";
        GD.Print($"[{scene!.Time,6:0.0}s] {zone?.Id} hp {p?.Hp:0}/{b?.MaxHp:0} ember {b?.EmberLevel} kills {b?.KillCount} foes {foes} at {p?.X:0},{p?.Z:0} {Overlay} {dbg}");
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
