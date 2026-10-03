using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Tests.Explorer;

/// <summary>The game as a zone sees it, for the story explorer: like
/// FakeHost, but the journey can be swapped for a copy of itself (so one
/// zone can try many things from the same moment), and what the zone asks
/// the game to do (talk, travel, open the Wayfinder's table, pull into an
/// arena) is written down for the explorer to carry out.</summary>
sealed class ExplorerHost : IZoneHost
{
    public Journey Journey { get; set; }
    public Battle? Battle { get; set; }
    public FakeLook FakeLook { get; }
    public IZoneLook Look => FakeLook;
    public Random Rng { get; } = new(5);
    public Hint? CurrentHint { get; private set; }

    public string? Talked, Opened;
    public (string Zone, string? Caption)? Travelled;
    public Arena.ArenaSpec? Entered;
    public readonly List<string> Said = new();
    readonly List<(double T, Action Fn)> later = new();

    public ExplorerHost(Journey j, ZoneMeta meta, Heightfield ground)
    {
        Journey = j;
        FakeLook = new FakeLook(meta, ground);
    }

    /// <summary>What the zone asked for since the last look, forgotten.</summary>
    public void Clear() { Talked = Opened = null; Travelled = null; Entered = null; }

    public bool Asked => Talked != null || Opened != null || Travelled != null || Entered != null;
    public bool Pending => later.Count > 0;

    public void Apply(IEnumerable<Change> changes) => Journey.Apply(changes);
    public void Say(string text, string? who = null, double seconds = 4) => Said.Add(text);
    public void Toast(Toast t) { }
    public void Announce(Announcement a) { }
    public void Talk(string npc) => Talked ??= npc;
    public void Travel(string zone, string? caption = null, string? sub = null) => Travelled ??= (zone, caption);
    public void Open(string overlay) => Opened ??= overlay;
    public void ArenaOver(Arena.ArenaResult r) { }
    public void EnterArena(Arena.ArenaSpec spec) => Entered ??= spec;
    public void After(double seconds, Action fn) => later.Add((seconds, fn));
    public void Save(string reason) { }
    public bool GiveItem(string def, int qty = 1, int? rarity = null) => Journey.GiveItem(def, qty, rarity);
    public void ReturnItem(ItemInstance it) => Journey.ReturnItem(it);
    public void SetBoss(BossBar? bar) { }
    public void SetObjectives(List<Tracked> list) { }
    public void SetHint(Hint? hint) => CurrentHint = hint;
    public void SetAtmosphere(AtmospherePreset p, bool rebuild = true) { }
    public void Showcase((double X, double Y, double Z)? pos, (double X, double Y, double Z) look = default) { }
    public void Capture(bool on) { }
    public void SetDraftTip(string tip) { }
    public void Revived(double x, double z) { }
    public string KeyLabel(string action) => action.ToUpperInvariant()[..1];
    public void AnnounceZone() { }

    /// <summary>Run what was put off, as time passes.</summary>
    public void Pass(double dt)
    {
        for (int i = 0; i < later.Count; i++) later[i] = (later[i].T - dt, later[i].Fn);
        var due = later.Where(l => l.T <= 0).ToList();
        later.RemoveAll(l => l.T <= 0);
        foreach (var (_, fn) in due) fn();
    }
}
