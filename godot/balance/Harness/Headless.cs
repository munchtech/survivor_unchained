using System;
using System.Collections.Generic;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Balance;

/// <summary>The game as an arena's runtime sees it, with nothing on screen:
/// what it announces is dropped, what it puts off happens as time passes,
/// and the arena's end is kept for the harness to read.</summary>
public sealed class HeadlessHost : IZoneHost
{
    public Journey Journey { get; }
    public Battle? Battle { get; set; }
    public IZoneLook Look { get; } = new NullLook();
    public Random Rng { get; }
    public Hint? CurrentHint => null;
    public Arena.ArenaResult? Result;
    public BossBar? Boss;
    readonly List<(double T, Action Fn)> later = new();

    public HeadlessHost(Journey j, int seed)
    {
        Journey = j;
        Rng = new Random(seed);
    }

    public void Apply(IEnumerable<Change> changes) => Journey.Apply(changes);
    public void Say(string text, string? who = null, double seconds = 4) { }
    public void Toast(Toast t) { }
    public void Announce(Announcement a) { }
    public void Talk(string npc) { }
    public void Travel(string zone, string? caption = null, string? sub = null) { }
    public void After(double seconds, Action fn) => later.Add((seconds, fn));
    public void Save(string reason) { }
    public bool GiveItem(string def, int qty = 1, int? rarity = null) => Journey.GiveItem(def, qty, rarity);
    public void ReturnItem(ItemInstance it) => Journey.ReturnItem(it);
    public void SetBoss(BossBar? bar) => Boss = bar;
    public void SetObjectives(List<Tracked> list) { }
    public void SetHint(Hint? hint) { }
    public void SetAtmosphere(AtmospherePreset p, bool rebuild = true) { }
    public void Showcase((double X, double Y, double Z)? pos, (double X, double Y, double Z) look = default) { }
    public void Capture(bool on) { }
    public void SetDraftTip(string tip) { }
    public void Revived(double x, double z) { }
    public string KeyLabel(string action) => action;
    public void AnnounceZone() { }
    public void ArenaOver(Arena.ArenaResult r) => Result = r;

    /// <summary>Run what was put off, as time passes.</summary>
    public void Pass(double dt)
    {
        if (later.Count == 0) return;
        for (int i = 0; i < later.Count; i++) later[i] = (later[i].T - dt, later[i].Fn);
        var due = later.FindAll(l => l.T <= 0);
        later.RemoveAll(l => l.T <= 0);
        foreach (var (_, fn) in due) fn();
    }
}

/// <summary>A view that draws nothing.</summary>
public sealed class NullLook : IZoneLook
{
    readonly List<bool> lit = new();
    public void SetLit(int light, bool on) { if (light < lit.Count) lit[light] = on; }
    public bool IsLit(int light) => light < lit.Count && lit[light];
    public void Show(string node, bool visible) { }
    public bool Shown(string node) => true;
    public void Stop(string node) { }
    public void AddProp(string id, double x, double z, double rot = 0, double scale = 1, double lift = 0) { }
    public int AddLight(double x, double y, double z, string color, double intensity, double distance, double flicker = 0.12, double glowSize = 0.08, string glowColor = "#ffb35a")
    {
        lit.Add(true);
        return lit.Count - 1;
    }
    public INpcView Person(NpcDef def, Spot spot) => new NullView();
    public INpcView Walker(PersonSpec spec, double scale) => new NullView();
    public void MoveLight(int light, double x, double y, double z) { }
    public double HeightAt(double x, double z) => 0;
    public void SetNight(bool on) { }
    public void Plates(List<Plate> plates) { }
    public void Bark(string text, double x, double y, double z, string? speaker = null, string? voice = null) { }
    public IBossView BossView(string kind) => new NullBoss();
    public INpcView Fallen(PersonSpec spec, Held? arms, double x, double z, double facing, string clip) => new NullView();
    public IOrb Orb(string color, double size) => new NullOrb();

    sealed class NullBoss : IBossView
    {
        public void SetPose(string pose) { }
        public void Release() { }
        public double Glow { set { } }
        public void Update(Enemy? e, double x, double y, double z, double facing, double dt) { }
        public void Hide() { }
        public void Dispose() { }
    }

    sealed class NullOrb : IOrb
    {
        public bool Visible { get; set; }
        public void Place(double x, double y, double z, double spin, double scale) { }
        public double Light { set { } }
        public void Dispose() { }
    }

    sealed class NullView : INpcView
    {
        public void Place(double x, double y, double z, double heading, bool visible) { }
        public void Loop(string clip, double blend = 0.3, double speed = 1) { }
        public void Act(string clip, double speed = 1) { }
        public void Dispose() { }
    }
}
