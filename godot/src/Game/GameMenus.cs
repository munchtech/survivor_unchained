using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Ui;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* What takes the screen from the fight: the screens over the game (the
 * pack, the self, the journal, the map, a shop, the storeroom, a night's
 * rest, the pause menu, the chapter's end), the level-up draft and
 * conversations. Each holds the world still while it is up. */
public partial class Game
{
    /* ---------------------------------------------------------- actions -- */

    bool OnAction(Act a)
    {
        if (scene == null) return false;
        // A screen hears the keys first.
        if (screens.Current is Overlay o)
        {
            if (o.Handle(a)) return true;
            if (inTransit) return true;
            if (o.Dismissable && (a is Act.Cancel or Act.Pause || a == o.Toggle)) { CloseOverlay(); return true; }
            return true;
        }
        if (inTransit || Mode != "play") return false;
        // A cinematic hears only the held skip (GameCinema), never a menu.
        if (cine != null) return true;
        if (hudMode is "draft" or "dialogue") return hud.Key(a);
        switch (a)
        {
            case Act.Pause: Open("pause"); return true;
            case Act.Inventory: Open("inventory"); return true;
            case Act.Character: Open("character"); return true;
            case Act.Arts: Open("arts"); return true;
            case Act.Journal: Open("journal"); return true;
            case Act.Map: Open("map"); return true;
            case Act.Interact when near != null:
                var locked = near.Locked?.Invoke();
                if (locked != null) Toast(new Toast(ToastKind.Warning, locked));
                else { near.Act(); zone?.Touched(); }
                return true;
            case Act.Ultimate: Journey.Quaff(Battle); return true;
        }
        return false;
    }

    /// <summary>A screen over the game, by what it is ('shop:harlan' for a shop).</summary>
    public void Open(string kind)
    {
        if (scene == null || Mode != "play") return;
        Overlay o = kind switch
        {
            "inventory" => new InventoryScreen(this),
            "character" => new SheetScreen(this),
            "journal" => new JournalScreen(this),
            "map" => new MapScreen(this),
            "stash" => new StashScreen(this),
            "rest" => new RestScreen(this),
            "maps" => new MapTableScreen(this),
            "arts" => new ArtsScreen(this),
            "chapter" => new ChapterScreen(this),
            _ when kind.StartsWith("shop:") => new ShopScreen(this, kind[5..]),
            _ when kind.StartsWith("forge:") => new ForgeScreen(this, kind[6..]),
            _ => new PauseScreen(this),
        };
        if (o is MapScreen && zone != null && Battle is { } b)
        {
            // What is round the survivor now, on the fog.
            double extent = scene.Data.Meta.Map?.Extent is { ValueKind: System.Text.Json.JsonValueKind.Number } ex ? ex.GetDouble() : scene.Data.Meta.Bound * 2;
            Journey.Walk(zone.Id, extent, b.Player.X, b.Player.Z);
        }
        screens.Show(o);
        // The pause menu stops the world; any other screen only in a fight (an arena, the night's
        // road), where the horde would not wait. Elsewhere the world goes on behind it (the owner).
        scene.SimPaused = o is PauseScreen || zone?.Combat == true;
        cam.ScreenShift = o.CameraShift;
        controls.Captured = true;
        hud.Prompt(promptShown = null);
    }

    public void CloseOverlay()
    {
        if (screens.Current is RestScreen { Reporting: true }) { FinishRest(); return; }
        screens.Close();
        // A shop, the pack or a rest may have changed what people's markers say.
        zone?.Touched();
        cam.ScreenShift = 0;
        if (scene != null && hudMode == null) scene.SimPaused = false;
        controls.Captured = false;
        controls.ClearLatches();
    }

    /// <summary>Gear changed: into the fight at once, and onto the figure.</summary>
    public void Gear(Action<Journey, Battle?> change)
    {
        change(Journey, Battle);
        scene?.SetLoadout(Loadouts.Of(Journey.Ch));
        screens.Current?.Refresh();
    }

    /* -------------------------------------------------------------- rest -- */

    /// <summary>A night at the inn: sleep until morning, or wait for dark.</summary>
    public void Rest(bool untilNight)
    {
        var w = World;
        if (untilNight)
        {
            Journey.Nightfall();
            CloseOverlay();
            hud.Fade(1, 0.8, "Nightfall", $"Day {w.Day}");
            Wait(1.4, () =>
            {
                air.Set(zone!.AtmosphereFor(TimeOfDay.Night));
                scene?.View.SetNight(true);
                hud.ZoneInfo(zone.Name, zone.Region, w.Day, TimeOfDay.Night);
                hud.Fade(0, 1.2);
                Save("night");
            });
            return;
        }
        var b = Battle;
        var lines = Journey.Sleep(b, Rng.NextDouble);
        if (lines == null) return;
        var screen = screens.Current as RestScreen;
        hud.Fade(1, 0.9);
        Wait(0.95, () =>
        {
            screen?.Report(lines);
            air.Set(zone!.AtmosphereFor(TimeOfDay.Day));
            scene?.View.SetNight(false);
            hud.ZoneInfo(zone.Name, zone.Region, w.Day, TimeOfDay.Day);
            Save("rest");
            hud.Fade(0, 0.6);
        });
    }

    public void FinishRest()
    {
        screens.Close();
        if (scene != null) scene.SimPaused = false;
        controls.Captured = false;
        controls.ClearLatches();
    }

    /* ------------------------------------------------------------ draft -- */

    List<Offer> offers = new();

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
        hudMode = "draft";
        Present(LevelUp.Draft(b));
    }

    void Present(List<Offer> list)
    {
        var b = Battle!;
        offers = list;
        var tip = draftTip;
        draftTip = null;
        string? great = LevelUp.GreatNext(b) ? b.Time < 60 ? "Dusk: the ember wakes, and any of them is yours" : "Midnight: a second, or the first deepened" : null;
        hud.Draft(new DraftView(LevelUp.DraftLevel(b), LevelUp.BlessingNext(b), list, b.Rerolls, b.Banishes, LevelUp.Queued(b), tip,
            LevelUp.BuildTags(b), Pick, Reroll, Banish, great, b, LevelUp.CanSkip(b) ? Skip : null));
    }

    public void Pick(int i)
    {
        var b = Battle;
        if (b == null || hudMode != "draft" || i < 0 || i >= offers.Count) return;
        var o = offers[i];
        LevelUp.Choose(b, o);
        if (o.Kind == OfferKind.Weapon) Toast(new Toast(ToastKind.Level, $"{o.Title} joins your arsenal"));
        if (b.DraftOwed) Present(LevelUp.Draft(b));
        else CloseDraft();
    }

    void Reroll()
    {
        if (LevelUp.Reroll(Battle!) is { } again) Present(again);
    }

    void Banish(int i)
    {
        if (i < 0 || i >= offers.Count || LevelUp.Banish(Battle!, offers[i]) is not { } again) return;
        Present(again);
    }

    void Skip()
    {
        var b = Battle!;
        if (!LevelUp.Skip(b)) return;
        if (b.DraftOwed) Present(LevelUp.Draft(b));
        else CloseDraft();
    }

    void CloseDraft()
    {
        hud.Draft(null);
        hudMode = null;
        scene!.SimPaused = false;
        controls.ClearLatches();
    }


    /* --------------------------------------------------------- dialogue -- */

    DialogueRunner? runner;
    string? talkNpc;
    float? camSaved;
    // The line on screen and its choices, for what the next line recalls.
    Presented? lastLine;
    string? before;

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
        hudMode = "dialogue";
        scene.SimPaused = true;
        hud.Prompt(promptShown = null);
        lastLine = null;
        before = null;
        ShowLine(p);
    }

    void ShowLine(Presented p)
    {
        sound.Line();
        var id = talkNpc!;
        var d = Lore.Person(id);
        Lore.Speakers.TryGetValue(id, out var sp);
        var s = World.Npc(id);
        // Read aloud, where the line has been recorded (the last line stops).
        var take = voice.Say(p.Line, p.Raw, Journey.Ch.Name);
        hud.Dialogue(new DialogueView(d?.Name ?? sp?.Name ?? id, d?.Title ?? sp?.Title ?? "", d != null || id is "greymuzzle" or "snib" ? Rules.Attitude(s) : "",
            p.Speaker == "player" ? "player" : p.Speaker == "narrator" ? "narrator" : "npc", p.Text, p.Choices, p.Choices.Count == 0,
            d?.Person, d?.Arms, d?.Scale ?? 1, sp?.Glyph, Journey.Ch.Name, Choose, Advance, before) { Voice = take });
        lastLine = p;
    }

    /// <summary>A line, shortened, to recall above the next.</summary>
    static string Short(string s) => s.Length <= 140 ? s : s[..s.LastIndexOf(' ', 137)] + "...";

    public void Choose(int index)
    {
        var r = runner;
        if (r == null) return;
        if (lastLine?.Choices.FirstOrDefault(c => c.Index == index) is { } said) before = $"You: \u201c{Short(said.Text)}\u201d";
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
        if (lastLine != null) before = lastLine.Speaker == "narrator" ? Short(lastLine.Text) : $"{(lastLine.Speaker == "player" ? "You" : Lore.NameOf(talkNpc ?? ""))}: \u201c{Short(lastLine.Text)}\u201d";
        var p = r.Advance();
        if (p != null) ShowLine(p); else EndDialogue();
    }

    string? afterTalk;

    void EndDialogue()
    {
        if (talkNpc != null && zone?.Actors.TryGetValue(talkNpc, out var actor) == true) actor.Talking = false;
        // What it changed shows over people's heads at once (their markers).
        zone?.Touched();
        cam.FocusOverride = null;
        if (camSaved is float d) { cam.TargetDistance = d; camSaved = null; }
        runner = null;
        talkNpc = null;
        voice.Stop();
        hud.Dialogue(null);
        hudMode = null;
        if (scene != null) scene.SimPaused = false;
        controls.ClearLatches();
        Save("talk");
        // A conversation that opened a shop, the storeroom, a bed.
        if (afterTalk is string next) { afterTalk = null; Open(next); }
    }


    /// <summary>What a conversation opens. True to stay in it.</summary>
    bool DialogueAction(string a)
    {
        switch (a)
        {
            case "trade": case "sell":
                if (talkNpc is string npc && Journey.OpenShop(npc, Rng) != null) afterTalk = $"shop:{npc}";
                else Toast(new Toast(ToastKind.World, "They have nothing to sell you"));
                return false;
            case "stash": afterTalk = "stash"; return false;
            // A crafter's bench (docs/CRAFTING_DESIGN.md): the one who was talked to.
            case "craft": if (talkNpc is string who) afterTalk = $"forge:{who}"; return false;
            case "maps": afterTalk = "maps"; return false;
            case "rest": afterTalk = "rest"; return false;
            case "fortune": Save("chapter"); afterTalk = "chapter"; return false;
        }
        bool stay = Journey.Service(a, Battle);
        scene?.SetLoadout(Loadouts.Of(Journey.Ch));
        return stay;
    }
}
