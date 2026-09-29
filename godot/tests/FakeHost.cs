using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Tests;

/// <summary>The game and the view as a zone's runtime sees them, without a
/// screen: what was said, shown and lit is written down to look at.</summary>
sealed class FakeHost : IZoneHost
{
    public Journey Journey { get; }
    public Battle? Battle { get; set; }
    public FakeLook FakeLook { get; }
    public IZoneLook Look => FakeLook;
    public Random Rng { get; } = new(5);
    public readonly List<string> Said = new(), Talked = new(), Saved = new();
    public readonly List<Toast> Toasts = new();
    public readonly List<Announcement> Announced = new();
    public (string Zone, string? Caption)? Travelled;
    public BossBar? Boss;
    public List<Tracked> Tracked = new();
    public Hint? CurrentHint { get; private set; }
    public AtmospherePreset? Air;
    readonly List<(double T, Action Fn)> later = new();

    public FakeHost(Journey j, ZoneMeta meta)
    {
        Journey = j;
        j.OnToast = Toasts.Add;
        FakeLook = new FakeLook(meta);
    }

    public void Apply(IEnumerable<Change> changes) => Journey.Apply(changes);
    public void Say(string text, string? who = null, double seconds = 4) => Said.Add(text);
    public void Toast(Toast t) => Toasts.Add(t);
    public void Announce(Announcement a) => Announced.Add(a);
    public void Talk(string npc) => Talked.Add(npc);
    public void Travel(string zone, string? caption = null, string? sub = null) => Travelled = (zone, caption);
    public void After(double seconds, Action fn) => later.Add((seconds, fn));
    public void Save(string reason) => Saved.Add(reason);
    public bool GiveItem(string def, int qty = 1, int? rarity = null) => Journey.GiveItem(def, qty, rarity);
    public void ReturnItem(ItemInstance it) => Journey.ReturnItem(it);
    public void SetBoss(BossBar? bar) => Boss = bar;
    public void SetObjectives(List<Tracked> list) => Tracked = list;
    public void SetHint(Hint? hint) => CurrentHint = hint;
    public void SetAtmosphere(AtmospherePreset p) => Air = p;
    public string KeyLabel(string action) => action.ToUpperInvariant()[..1];
    public void AnnounceZone() => Announced.Add(new Announcement("zone", null, "zone", 1));

    /// <summary>Run what was put off, as time passes.</summary>
    public void Pass(double dt)
    {
        for (int i = 0; i < later.Count; i++) later[i] = (later[i].T - dt, later[i].Fn);
        var due = later.Where(l => l.T <= 0).ToList();
        later.RemoveAll(l => l.T <= 0);
        foreach (var (_, fn) in due) fn();
    }
}

sealed class FakeLook : IZoneLook
{
    readonly ZoneMeta meta;
    readonly Heightfield ground;
    readonly List<bool> lit;
    public readonly HashSet<string> Hidden = new(), Stopped = new();
    public readonly List<string> Props = new(), Barks = new();
    public List<Plate> LastPlates = new();
    public bool Night;

    public FakeLook(ZoneMeta meta)
    {
        this.meta = meta;
        ground = Heightfield.Load(meta);
        lit = meta.Lights.Select(l => l.On).ToList();
        Hidden.UnionWith(meta.HiddenNodes);
    }

    public void SetLit(int light, bool on) => lit[light] = on;
    public bool IsLit(int light) => lit[light];
    public void Show(string node, bool visible) { if (visible) Hidden.Remove(node); else Hidden.Add(node); }
    public bool Shown(string node) => !Hidden.Contains(node);
    public void Stop(string node) => Stopped.Add(node);
    public void AddProp(string id, double x, double z, double rot = 0, double scale = 1) => Props.Add(id);
    public int AddLight(double x, double y, double z, string color, double intensity, double distance, double flicker = 0.12, double glowSize = 0.08, string glowColor = "#ffb35a")
    {
        lit.Add(true);
        return lit.Count - 1;
    }
    public INpcView Person(NpcDef def, Spot spot) => new FakeView();
    public INpcView Walker(PersonSpec spec, double scale) { Walkers++; return new FakeView(); }
    public int Walkers;
    public void MoveLight(int light, double x, double y, double z) { }
    public double HeightAt(double x, double z) => ground.HeightAt(x, z);
    public void SetNight(bool on) => Night = on;
    public void Plates(List<Plate> plates) => LastPlates = plates;
    public void Bark(string text, double x, double y, double z, string? speaker = null) => Barks.Add(text);

    sealed class FakeView : INpcView
    {
        public void Place(double x, double y, double z, double heading, bool visible) { }
        public void Loop(string clip, double blend = 0.3, double speed = 1) { }
        public void Act(string clip, double speed = 1) { }
        public void Dispose() { }
    }
}
