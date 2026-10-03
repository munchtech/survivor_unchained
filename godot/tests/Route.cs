using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;
using SurvivorUnchained.Play.Zones;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A survivor's journey played the way the game plays it, without a
/// screen: one Journey, its conversations run in its own context, the
/// Waystation and the Verge stood up around it when the story needs them,
/// nights slept through, and saved and loaded back whenever a route wants to
/// prove that nothing was in memory only. The route tests walk the story
/// with it (docs/WRITING_PASS.md).</summary>
sealed class Route
{
    public Journey J { get; private set; }
    public FakeHost? Host { get; private set; }
    public ZoneRuntime? Zone { get; private set; }
    public Battle? B { get; private set; }
    public ZoneMeta? Meta { get; private set; }
    readonly Random rng = new(7);
    double roll = 0.5;

    Route(Journey j) { J = j; }

    /// <summary>A survivor just up the Low Ford road: the prologue done, the
    /// dead watchman read (as the prologue reads him), in the Waystation by day.</summary>
    public static Route New(string bg = "hunter", string name = "Wren", string archetype = "warden", bool readTheBook = true)
    {
        var a = Callings.Archetype(archetype);
        var j = Journey.Begin(new CreationChoice
        {
            Name = name, Archetype = archetype, Background = bg, Palette = a.Palettes[0].Id, WeaponItem = a.Weapons[0], Ability = a.Abilities[0],
        }, 5);
        var p = new Route(j);
        if (readTheBook) p.Apply("""[{ "learn": "lore.warden", "text": "The lamps at the ford feed the Warden." }, { "quest": { "id": "lamps", "status": "active", "entry": "book" } }]""");
        p.Apply("""[{ "set": { "prologue.done": true } }, { "quest": { "id": "prologue", "status": "resolved", "outcome": "resolved" } }]""");
        j.World.Time = TimeOfDay.Day;
        j.Ch.Gold = 200;
        return p;
    }

    public WorldState W => J.World;
    public Ctx C => J.Ctx;
    public void Apply(string json) => J.Apply(json);
    public Fact F(string key) => W.Fact(key);
    public string? S(string key) => W.Fact(key).Str;
    public bool Has(string quest, string entry) => W.Quests.TryGetValue(quest, out var q) && q.Entries.Contains(entry);
    public QuestStatus Status(string quest) => W.Quests.TryGetValue(quest, out var q) ? q.Status : QuestStatus.Unknown;
    public List<string> Journal(string quest) => W.Quests.TryGetValue(quest, out var q) ? q.Entries.ToList() : new();
    public int Count(string item) => Inventory.Count(J.Ch, item);
    public void Give(string item, int qty = 1) => Inventory.AddToPack(J.Ch, Inventory.Make(J.Ch, item, qty: qty));
    public void Learn(string k) { if (!J.Ch.Knowledge.Contains(k)) J.Ch.Knowledge.Add(k); }
    public bool Knows(string k) => J.Ch.Knowledge.Contains(k);

    /* ---------------------------------------------------------- talking -- */

    static Conversation Convo(string id) => Dialogue.Find(id) ?? throw new KeyNotFoundException(id);

    /// <summary>A conversation, picking choices by a fragment of their text.
    /// The last thing said (null if it ended), and any action it asked for.</summary>
    public (Presented? Last, List<string> Actions) Talk(string npc, params string[] picks)
    {
        var r = new DialogueRunner(Convo(npc), C);
        var p = r.Start() ?? throw new InvalidOperationException($"{npc}: nobody home");
        var actions = new List<string>();
        foreach (var pick in picks)
        {
            while (p != null && p.Choices.Count == 0) p = r.Advance();
            if (p == null) throw new InvalidOperationException($"{npc}: the conversation ended before \"{pick}\"");
            var choice = p.Choices.FirstOrDefault(x => x.Text.Contains(pick, StringComparison.OrdinalIgnoreCase))
                ?? throw new InvalidOperationException($"{npc}.{p.Node.Id}: no choice \"{pick}\" in [{string.Join(" | ", p.Choices.Select(x => x.Text))}]");
            if (!choice.Enabled) throw new InvalidOperationException($"{npc}: \"{pick}\" is locked: {choice.Locked}");
            var (next, action) = r.Choose(choice.Index);
            if (action != null) { actions.Add(action); Act(npc, action); }
            p = next;
        }
        return (p, actions);
    }

    /// <summary>What the game does with a conversation's action.</summary>
    void Act(string npc, string action)
    {
        switch (action)
        {
            case "trade": case "sell": J.OpenShop(npc, rng); break;
            case "rest": Sleep(); break;
            case "stash": case "maps": case "fortune": break;
            default: J.Service(action, B); break;
        }
    }

    /// <summary>The greeting and everything said before the first question, and the question's choices.</summary>
    public (string Said, List<string> Choices) Greet(string npc)
    {
        var r = new DialogueRunner(Convo(npc), C);
        var p = r.Start() ?? throw new InvalidOperationException($"{npc}: nobody home");
        var said = new List<string> { p.Text };
        while (p.Choices.Count == 0)
        {
            p = r.Advance() ?? throw new InvalidOperationException($"{npc}: ended before a question");
            said.Add(p.Text);
        }
        return (string.Join(" ", said), p.Choices.Select(c => c.Text).ToList());
    }

    public List<string> Offered(string npc) => Greet(npc).Choices;

    /// <summary>Vonnra's fortune read through; the reading, and the last page's choices.</summary>
    public (string Read, List<string> Choices, DialogueRunner R, Presented Last) Fortune()
    {
        var r = new DialogueRunner(Convo("vonnra"), C);
        var p = r.Start()!;
        while (p.Choices.Count == 0) p = r.Advance()!;
        p = r.Choose(p.Choices.First(c => c.Text.Contains("fortune", StringComparison.OrdinalIgnoreCase)).Index).Next!;
        var read = new List<string>();
        while (p.Choices.Count == 0) { read.Add(p.Text); p = r.Advance()!; }
        read.Add(p.Text);
        return (string.Join(" ", read), p.Choices.Select(c => c.Text).ToList(), r, p);
    }

    /// <summary>The mark over someone's head right now ('!', '?' or none).</summary>
    public string? Marker(string npc) => Dialogue.MarkerOf(Convo(npc), C);

    /* ---------------------------------------------------------- the day -- */

    /// <summary>A night's sleep at the inn: the morning's report.</summary>
    public List<string> Sleep()
    {
        J.Ch.Gold = Math.Max(J.Ch.Gold, 50);
        var lines = J.Sleep(B, () => roll) ?? throw new InvalidOperationException("could not pay for a bed");
        return lines;
    }

    public string Sleeps(int nights) => string.Join(" ", Enumerable.Range(0, nights).SelectMany(_ => Sleep()));

    public void Night() => J.Nightfall();

    /// <summary>The tracker's steps for a quest, as the corner of the screen shows them.</summary>
    public List<string> Steps(string quest) => Objectives.Of(C).Find(o => o.Id == quest)?.Steps.Select(s => s.Text).ToList() ?? new();

    /* --------------------------------------------------------- the zones -- */

    /// <summary>Walk out to a zone (and leave the one you are in).</summary>
    public Route Enter(string zone, string? from = null)
    {
        Leave();
        Meta = ZoneMeta.Load(zone);
        Host = new FakeHost(J, Meta);
        Zone = zone switch
        {
            "verge" => new Verge(Host, Meta),
            "waystation" => new Waystation(Host, Meta),
            "lowford" => new Prologue(Host, Meta),
            _ => throw new ArgumentException(zone),
        };
        var at = Zone.ArrivalFrom(from ?? (zone == "verge" ? "waystation" : null));
        B = J.StartBattle(Zone.Combat, Meta.Collision(), Heightfield.Load(Meta).HeightAt, at.X, at.Z, at.Facing, 11, ember: Zone.Ember);
        B.Hooks = Zone.Hooks;
        Host.Battle = B;
        Zone.Begin(B);
        return this;
    }

    public void Leave()
    {
        if (Zone == null) return;
        J.Capture(B);
        Zone.Dispose();
        Zone = null; B = null; Host = null; Meta = null;
    }

    /// <summary>Time passing in the zone (nobody gets hurt: these are story walks, not fights).</summary>
    public void Wait(double seconds)
    {
        if (Zone == null || B == null || Host == null) return;
        for (double t = 0; t < seconds; t += 1 / 30.0)
        {
            B.Player.Hp = B.MaxHp;
            Zone.Step(1 / 30.0);
            B.Tick(1 / 30.0, 0, 0);
            B.Events.Drain();
            Zone.Frame(1 / 30.0);
            Host.Pass(1 / 30.0);
        }
    }

    /// <summary>Stand at a named place of the zone (V table) for a moment.</summary>
    public void Walk(string place, double dx = 0, double dz = 0)
    {
        var at = Meta!.Place(Zone is Waystation ? "WAY" : "V", place);
        B!.Player.X = at.X + dx; B.Player.Z = at.Z + dz;
        Wait(0.5);
    }

    public Interactable? Thing(string id) => Zone!.Interactables.SingleOrDefault(i => i.Id == id);

    /// <summary>Offered here and now: there, wanted, and not refused.</summary>
    public bool CanUse(string id) => Thing(id) is { } it && it.When?.Invoke() != false && it.Locked?.Invoke() == null;
    public bool Offers(string id) => Thing(id) is { } it && it.When?.Invoke() != false;
    public string? Refusal(string id) => Thing(id)?.Locked?.Invoke();

    public void Use(string id)
    {
        var it = Thing(id) ?? throw new InvalidOperationException($"nothing called {id} here");
        if (it.When?.Invoke() == false) throw new InvalidOperationException($"{id} is not offered");
        if (it.Locked?.Invoke() is string why) throw new InvalidOperationException($"{id} is refused: {why}");
        it.Act();
    }

    /// <summary>Every enemy of a kind (by tag) put down by the survivor.</summary>
    public void Kill(Func<Enemy, bool> which)
    {
        foreach (var e in B!.Enemies.Living().Where(which).ToList()) B.KillEnemy(e, true, null);
        Wait(0.2);
    }

    public List<MapMark> Map() => Zone!.MapMarks();

    /// <summary>One of the night's story fights (an interactable "night:..."),
    /// taken, fought and won or lost; back in the Verge afterwards.</summary>
    public Arena.ArenaSpec StoryFight(string id, bool won)
    {
        Use($"night:{id}");
        var spec = Host!.Entered ?? throw new InvalidOperationException($"{id} entered no arena");
        Leave();
        Arena.Arenas.Begin(W, spec);
        var b = J.StartBattle(true, new CollisionWorld(60), (_, _) => 0, 0, 0, 0, 3, arena: true);
        // The boss down tells the story at once; the way out is taken after.
        if (won) Arena.Arenas.Won(J, spec);
        Arena.Arenas.Finish(J, b, spec, won);
        Enter("verge");
        return spec;
    }

    /* ------------------------------------------------------ save and load -- */

    /// <summary>Saved as the game saves (to text) and loaded back as a new
    /// journey, standing where it stood; the zone is stood up again from the save.</summary>
    public Route SaveAndLoad()
    {
        string? zone = Zone?.Id;
        double x = B?.Player.X ?? 0, z = B?.Player.Z ?? 0;
        if (Zone != null) J.Capture(B);
        var text = Json.Write(J.ToSave(new SaveLocation { Zone = zone ?? "waystation", X = x, Z = z }));
        if (Zone != null) { Zone.Dispose(); Zone = null; B = null; Host = null; Meta = null; }
        J = Journey.From(Saves.Parse(text)!, 0);
        Loaded = Snapshot();
        if (zone != null)
        {
            Enter(zone);
            B!.Player.X = x; B.Player.Z = z;
        }
        return this;
    }

    /// <summary>The state as it came back from the last save, before any zone was stood up again.</summary>
    public string Loaded { get; private set; } = "";

    /// <summary>The state that matters, as text, for "nothing changed across a save".</summary>
    public string Snapshot() => Json.Write(new { W.Facts, W.Quests, W.Day, W.Time, Knowledge = J.Ch.Knowledge.OrderBy(k => k).ToList(), Pack = J.Ch.Pack.Where(p => p != null).Select(p => p!.Def).OrderBy(d => d).ToList(), J.Ch.Gold });
}
