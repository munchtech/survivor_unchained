using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Godot;
using SurvivorUnchained.Cinema;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Sound;
using SurvivorUnchained.Ui;
using SurvivorUnchained.View;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/* The cinematic player: a timeline (godot/data/cinematics/<id>.json, played
 * by logic/Cinema) put on the screen in the zone that is running. The world
 * is held under it (Battle.WorldRate), the controls captured, the HUD gone
 * behind the bars. Its cast are its own: the survivor is played by a double
 * built from her loadout (the game's own figure waits, hidden, and takes her
 * place at the end mark), the dead it raises are spawned into the fight, so
 * they are there when play begins. Its camera replaces the follow camera
 * and hands back into it. Holding interact or pause skips it to its end. */
public partial class Game
{
    Cine? cine;
    /// <summary>Started by --quick: no cinematic plays unless --cine names it.</summary>
    bool quick;

    /// <summary>A cinematic playing (null: none).</summary>
    public bool InCinematic => cine != null;
    /// <summary>The cinematic playing (its id), for --perf's windows.</summary>
    public string? CinematicId => cine != null ? cineId : null;
    string? cineId;

    /// <summary>A cinematic from the data, played now in the zone that is
    /// running; done when it hands back (or is skipped). False if it cannot
    /// play here (no scene, no such file), and the zone does without.</summary>
    public bool Cinematic(string id, Action? done = null, IReadOnlyDictionary<string, double[]>? marks = null)
    {
        if (scene?.Battle is not { } b || cine != null) return false;
        // --nocine, or a quick start: the zone's captions instead (pictures of play from the first frame).
        // --cines: a quick start that plays every cinematic as the zone reaches it (real-play checks).
        if (Args.Has("nocine") || (quick && !Args.Has("cines") && Args.Get("cine") != id && chained == null)) return false;
        CineFile file;
        try { file = CineFile.Load(id); }
        catch (Exception e) { GD.PushWarning($"cinema: {id} not played ({e.Message})"); return false; }
        // Where things really are (a boss falls where the fight leaves him).
        if (marks != null) foreach (var (k, v) in marks) file.Marks[k] = v.ToArray();
        // A timeline that cannot be laid out is not played (its schedule is built
        // before anything on screen changes), and the zone does without.
        // Run on from the one before (its end.next): the bars stay in and what it left stays.
        // Straight after a storybook (SB00 into C01): its bars, full, are this one's from the first frame.
        if (chained == null && TakeStoryBars() is { } sb) chained = new Chain(sb, (camera.Fov, camera.KeepAspect, camera.Near, camera.Attributes));
        if (chained == null) ClearKept();
        else file.Bars.In = 0;
        try { cine = new Cine(this, file, b, done); cineId = id; }
        catch (Exception e) { GD.PushError($"cinema: {id} not played: {e.Message}"); cine = null; return false; }
        finally { chained = null; }
        if (scene != null) scene.Fx.HideLoot = true;
        handoffId = id;
        // (its double taken: the next one's made now)
        doubleCheck = 0;
        return true;
    }

    /* Her double built ahead (s5). A cinematic's "survivor" is her figure made new: 250-450 ms and some 240 MB on
     * the main thread as each began (C02, C03, C04 A). One is made on a worker thread while play goes on (as
     * WalkerView makes the townsfolk), held off the tree, and the next cinematic takes it if she still looks as
     * she did (her look and arms: DoubleKey); if not, it is made there as before. Only in a place with cinematics. */
    System.Threading.Tasks.Task<PersonView>? doubleAhead;
    string? doubleKey, doubleSeen;
    double doubleCheck;
    readonly List<System.Threading.Tasks.Task<PersonView>> doublesDropped = new();
    static readonly JsonSerializerOptions DoubleJson = new() { IncludeFields = true };

    static string DoubleKey(Loadout lo) =>
        JsonSerializer.Serialize(lo.Person, DoubleJson) + "|" + lo.Arms.Right + "|" + lo.Arms.Left + "|" + lo.Arms.Forearm;

    static Dictionary<string, List<CineFile>>? cineZones;
    string? castAheadZone;

    static Dictionary<string, List<CineFile>> CineZones()
    {
        var z = new Dictionary<string, List<CineFile>>();
        foreach (var f in DirAccess.GetFilesAt("res://data/cinematics"))
            if (f.EndsWith(".json") && !f.StartsWith("_"))
                try { var cf = CineFile.Load(f[..^5]); (z.TryGetValue(cf.Zone, out var l) ? l : z[cf.Zone] = new()).Add(cf); } catch (Exception) { }
        return z;
    }

    /// <summary>The files the people a place's cinematics cast are made from (its named folk, its crowds, what they
    /// hold), loaded on a worker as the place is entered and held while it plays: C02's drowned were loaded from
    /// disk on the main thread as it began, some 650 ms.</summary>
    void CastAhead(List<CineFile> files)
    {
        var paths = new HashSet<string>();
        void Add(PersonSpec? spec, Held? arms)
        {
            if (spec != null) foreach (var f in People.Files(spec)) paths.Add(f);
            foreach (var a in new[] { arms?.Right, arms?.Left, arms?.Forearm })
                if (a != null && Arms.All.TryGetValue(a, out var w) && w.Build == null) paths.Add($"res://assets/weapons/{w.File}.glb");
        }
        foreach (var f in files)
            foreach (var c in f.Cast.Values)
            {
                if (c.Kind == "npc" && c.Def != null && Lore.Person(c.Def) is { } def) Add(def.Person ?? new PersonSpec(), def.Arms);
                else if (c.Kind == "extras")
                    foreach (var v in c.Visual is { Count: > 0 } vs ? vs : ["skeleton_minion"]) { var sp = Visuals.Of(v); Add(sp.Person ?? new PersonSpec(), sp.Arms); }
            }
        Prefetch.CastAhead(paths);
        // (and the figures themselves, s6: C02's Warden and twelve drowned were made on the main thread as it began,
        // 140 ms; each cinematic's boss and extras made on a worker, one file after another, held off the tree)
        if (Args.Get("cast-ahead") == "off") return;
        foreach (var f in files)
        {
            var specs = new List<(string Key, CineCast C, int I)>();
            foreach (var (name, c) in f.Cast)
                if (c.Kind == "boss") specs.Add((name, c, -1));
                else if (c.Kind == "extras" && c.At != null) for (int i = 0; i < c.At.Count; i++) specs.Add((name, c, i));
            if (specs.Count == 0) continue;
            var before = castChain;
            castChain = System.Threading.Tasks.Task.Run(() =>
            {
                try { before?.Wait(); } catch (Exception) { }
                var made = new Dictionary<string, Node3D>();
                foreach (var (name, c, i) in specs)
                {
                    if (i < 0) { var wv = new WardenView(); if (ExtrasShadow) wv.Body.BeginShadow(); made[name] = wv; continue; }
                    var visuals = c.Visual is { Count: > 0 } vs ? vs : ["skeleton_minion"];
                    var spec = Visuals.Of(visuals[i % visuals.Count]);
                    var pv = new PersonView(spec.Person ?? new PersonSpec(), spec.Arms, 0.8 * spec.Scale);
                    if (ExtrasShadow) pv.BeginShadow();
                    made[$"{name}.{i}"] = pv;
                }
                return made;
            });
            castAhead[f.Id] = castChain;
        }
    }

    /// <summary>(--lampdbg) Who draws: each group's (the node under the zone's world) geometry in the camera's view, and
    /// its shadow casters in each shadowing lamp's reach, as "group main N lampcasters M" (diagnostics only).</summary>
    static IEnumerable<string> Census(Game g)
    {
        var cam = g.camera!;
        var planes = cam.GetFrustum();
        var lamps = g.GetTree().Root.FindChildren("*", "OmniLight3D", true, false).OfType<OmniLight3D>()
            .Where(l => l.IsVisibleInTree() && l.ShadowEnabled).ToList();
        var tally = new SortedDictionary<string, (int Main, int Cast)>();
        var perLamp = new Dictionary<OmniLight3D, int>();
        foreach (var n in g.GetTree().Root.FindChildren("*", "GeometryInstance3D", true, false))
        {
            var gi = (GeometryInstance3D)n;
            if (!gi.IsVisibleInTree()) continue;
            var box = gi.GlobalTransform * gi.GetAabb();
            bool seen = planes.All(pl => { var c = box.GetCenter(); var e = box.Size / 2;
                return pl.DistanceTo(c) <= Math.Abs(pl.Normal.X) * e.X + Math.Abs(pl.Normal.Y) * e.Y + Math.Abs(pl.Normal.Z) * e.Z; });
            int cast = 0;
            if (gi.CastShadow != GeometryInstance3D.ShadowCastingSetting.Off)
                foreach (var l in lamps)
                    if (l.GlobalPosition.Clamp(box.Position, box.End).DistanceTo(l.GlobalPosition) <= l.OmniRange) { cast++; perLamp[l] = perLamp.GetValueOrDefault(l) + 1; }
            var path = gi.GetPath().ToString().Split('/');
            int w = Array.FindIndex(path, x => x.StartsWith("World_"));
            string key = w < 0 || w + 1 >= path.Length ? (path.Length > 3 ? path[3] : gi.Name.ToString())
                : path[w + 1].StartsWith("Zone_") && w + 2 < path.Length ? $"{path[w + 1]}/{path[w + 2]}" : path[w + 1];
            if (key.StartsWith("Cine_drowned")) key = "Cine_drowned*";
            var t = tally.GetValueOrDefault(key);
            tally[key] = (t.Main + (seen && gi.CastShadow != GeometryInstance3D.ShadowCastingSetting.ShadowsOnly ? 1 : 0), t.Cast + cast);
        }
        yield return $"lamps shadowing {lamps.Count}: " + string.Join(", ", lamps.Select(l => l.GetParent().Name + "/" + l.Name + " " + perLamp.GetValueOrDefault(l)));
        foreach (var (key, (m, c)) in tally.OrderByDescending(kv => kv.Value.Cast + kv.Value.Main)) if (m + c > 0) yield return $"{key} main {m} lampcasters {c}";
    }

    /// <summary>(E10) A crowd of extras (C02's twelve drowned) and a cinematic's boss (its Warden) cast as one shadow a
    /// figure (FolkShadow, as the town's folk do): the same geometry on the same bones, so the same shadow, in each
    /// lamp's six faces and each cascade for one draw instead of each mesh's. Their shape keys never change after they
    /// are made (no face is played on them), and nothing in a cinematic re-dresses them. Not her: her face and her
    /// fitting move her shape keys. --extras-shadow off: each mesh casts (to compare).</summary>
    static readonly bool ExtrasShadow = Args.Get("extras-shadow") != "off";

    /// <summary>The cast made ahead for each cinematic file (by its id), and the chain they are made on (one at a time).</summary>
    readonly Dictionary<string, System.Threading.Tasks.Task<Dictionary<string, Node3D>>> castAhead = new();
    System.Threading.Tasks.Task<Dictionary<string, Node3D>>? castChain;

    /// <summary>A cinematic's cast made ahead (waited for, if still being made), taken: what it does not use is freed.</summary>
    Dictionary<string, Node3D>? TakeCast(string fileId)
    {
        if (!castAhead.Remove(fileId, out var t)) return null;
        try { return t.Result; }
        catch (Exception e) { GD.PushWarning($"cinema: the cast made ahead failed ({e.Message})"); return null; }
    }

    /// <summary>What was made ahead and not taken, freed (the place left, or the game).</summary>
    void DropCast()
    {
        foreach (var t in castAhead.Values)
        {
            try { t.Wait(10000); } catch (Exception) { }
            if (t.IsCompletedSuccessfully) foreach (var n in t.Result.Values) if (IsInstanceValid(n) && !n.IsInsideTree()) n.Free();
        }
        castAhead.Clear();
        castChain = null;
    }

    /// <summary>Each frame (a look a second): her double made ahead if there is none for her as she is.</summary>
    void DoubleAhead(double dt)
    {
        for (int i = doublesDropped.Count - 1; i >= 0; i--)
            if (doublesDropped[i].IsCompleted)
            {
                if (doublesDropped[i].IsCompletedSuccessfully) doublesDropped[i].Result.Free();
                doublesDropped.RemoveAt(i);
            }
        if ((doubleCheck -= dt) > 0 || Journey == null || scene?.Battle == null || Args.Has("no-double-ahead")) return;
        doubleCheck = 1;
        if (!(cineZones ??= CineZones()).TryGetValue(scene.Data.Id, out var here)) return;
        if (castAheadZone != scene.Data.Id) { DropCast(); castAheadZone = scene.Data.Id; CastAhead(here); }
        if (doubleAhead is { IsCompleted: false }) return;
        if (HerWear.Dressing) return;
        var lo = Loadouts.Of(Journey.Ch);
        var key = DoubleKey(lo);
        if (doubleAhead != null && key == doubleKey) return;
        // (her look as it was a second ago too: not between swaps)
        bool settled = key == doubleSeen;
        doubleSeen = key;
        if (!settled) { doubleCheck = 0.5; return; }
        if (doubleAhead != null) doublesDropped.Add(doubleAhead);
        doubleKey = key;
        var spec = lo.Person;
        var held = new Held { Right = lo.Arms.Right, Left = lo.Arms.Left, Forearm = lo.Arms.Forearm };
        doubleAhead = System.Threading.Tasks.Task.Run(() => new PersonView(spec, held, 0.8) { Name = "CineSurvivor" });
    }

    /// <summary>The game goes: her double made ahead, never added, goes with it (no leak reported at exit).</summary>
    public override void _ExitTree()
    {
        if (doubleAhead is { } t) { try { t.Wait(5000); } catch (Exception) { } if (t.IsCompletedSuccessfully) t.Result.Free(); doubleAhead = null; }
        foreach (var d in doublesDropped) { try { d.Wait(5000); } catch (Exception) { } if (d.IsCompletedSuccessfully) d.Result.Free(); }
        doublesDropped.Clear();
        DropCast();
    }

    /// <summary>Her double made ahead, if it is of her as she is (waited for, if it is still being made); else null.</summary>
    PersonView? TakeDouble(Loadout lo)
    {
        if (doubleAhead is not { } t || t.IsFaulted || t.IsCanceled || doubleKey != DoubleKey(lo)) return null;
        doubleAhead = null;
        doubleKey = null;
        try { return t.Result; }
        catch (Exception e) { GD.PushWarning($"cinema: her double made ahead failed ({e.Message})"); return null; }
    }

    public bool CanCinematic(string id) =>
        scene?.Battle != null && cine == null && !Args.Has("nocine") && !(quick && !Args.Has("cines") && Args.Get("cine") != id && chained == null)
        && FileAccess.FileExists($"res://data/cinematics/{id}.json");

    /* The hand-over (docs/cinematics/README.md, 5a): from a cinematic's "play"
     * cue her own body walks the rest of it, steered by the cinematic as if a
     * player held the stick; at its end the walk carries on into play and
     * eases to a stop over CarryFade unless the player takes it. */
    (double X, double Z)? cineWalk;
    internal double? cineSat;
    /// <summary>Bodies a cinematic left in the world (end.keep), until the next one or the place goes.</summary>
    readonly List<Node3D> kept = new();

    void ClearKept()
    {
        foreach (var n in kept) if (IsInstanceValid(n)) n.QueueFree();
        kept.Clear();
    }
    /// <summary>A cinematic ended into the next (end.next): its bars and the camera
    /// it saved, taken over by the next one if the zone starts it on the cut.</summary>
    sealed record Chain(CinemaBars Bars, (float Fov, Camera3D.KeepAspectEnum Keep, float Near, CameraAttributes? Attr) Saved);
    Chain? chained;
    (double X, double Z) carry;
    double carryT;
    const double CarryFade = 0.7;

    /// <summary>The move the fight is given: the cinematic's walk, the
    /// player's own, or the walk a cinematic handed over, easing out.</summary>
    (double X, double Z) PlayMove()
    {
        if (cineWalk is { } w) return w;
        // --stroll M: a constant move at M m/s of ground speed along the --facing heading (0 = +Z; the move is (sin, cos) of it), for gait shots.
        if (Args.Has("stroll") && Battle is { } sb)
        {
            double top = Math.Max(0.1, sb.Stats.Get(Stat.MoveSpeed) * sb.Player.SlowF), k = Math.Min(1.5, Args.Num("stroll", 1) / top);
            double f = Args.Num("facing", 0) * Math.PI / 180;
            return (Math.Sin(f) * k, Math.Cos(f) * k);
        }
        if (controls.Captured) return (0, 0);
        double x = controls.MoveX, z = controls.MoveZ;
        if (x * x + z * z > 0.01) carryT = 0;
        else if (carryT > 0) { double k = carryT / CarryFade; return (carry.X * k, carry.Z * k); }
        return (x, z);
    }

    /// <summary>--handoff (with --shot NAME): a frame every tenth of a second
    /// from 1.5 s before a cinematic ends to 2.5 s into play, to judge the
    /// hand-over (ho_ID_NNN).</summary>
    double handoffLeft, handoffNext;
    int handoffN;
    string handoffId = "";

    void HandoffFrames(double dt, double? toEnd)
    {
        if (!Args.Has("handoff")) return;
        if (toEnd is double e && e <= 1.5) handoffLeft = Math.Max(handoffLeft, e + 2.5);
        if (handoffLeft <= 0) return;
        handoffLeft -= dt;
        handoffNext -= dt;
        if (handoffNext > 0) return;
        handoffNext = 0.1;
        Shots.Want($"ho_{handoffId}_{handoffN++:000}", 0);
    }

    /// <summary>The one place the shadow rules of play (E1) step aside for a cinematic and come back:
    /// the lamps all shadow at full strength (ShadowLamp.Suspended) and the sun has its old cascades
    /// and reach (Graphics.Sun), so the judged shots are unchanged. Acts only on a change.</summary>
    void CineShadows()
    {
        bool on = cine != null;
        if (ShadowLamp.Suspended == on) return;
        ShadowLamp.Suspended = on;
        Graphics.Sun(air, Graphics.Current);
    }

    /// <summary>Each frame, after the world is drawn: the camera, the cast, the cues.</summary>
    void CinemaFrame(double dt)
    {
        carryT = Math.Max(0, carryT - dt);
        HandoffFrames(dt, cine?.ToEnd);
        CineShadows();
        if (cine == null) return;
        cine.Frame(dt);
        if (cine.Over) { var c = cine; cine = null; c.Finish(); CineShadows(); }
        if (scene != null) scene.Fx.HideLoot = cine != null; // hidden across a chain, shown at the hand-back
    }

    sealed partial class Cine
    {
        readonly Game g;
        readonly CineFile file;
        readonly Battle b;
        readonly Action? done;
        readonly CinePlayer player;
        readonly CinePlaces places;
        readonly CinemaBars bars;
        readonly Dictionary<string, PersonView> people = new();
        readonly Dictionary<string, Enemy> enemies = new();
        /// <summary>The creatures it stages, by id: how far down they are drawn, and a role held from a moment (CrowdView.Staged).</summary>
        readonly Dictionary<int, (double Sink, string? Role, double T0, double? Facing)> staged = new();
        double SinkOf(Enemy e) => staged.TryGetValue(e.Id, out var st) ? st.Sink : 0;
        readonly Dictionary<string, WardenView> bosses = new();
        readonly Dictionary<string, OrbView> orbs = new();
        readonly Dictionary<string, double> orbLight = new();
        float skinSky = 1, skinEar = 1;
        /// <summary>A crowd of extras by its cast name: its members' names, in order.</summary>
        readonly Dictionary<string, List<string>> groups = new();
        /// <summary>A crowd's cue, staggered down its members: done when the clock reaches it.</summary>
        readonly List<TimedCue> later = new();
        readonly List<Tween> tweens = new();
        readonly List<Move> moves = new();
        readonly Dictionary<string, Dictionary<string, float>> faces = new();
        readonly bool seen;
        readonly Ctx ctx;
        (float Fov, Camera3D.KeepAspectEnum Keep, float Near, CameraAttributes? Attr) saved;
        CameraAttributesPractical dof = new();
        double skipHeld;
        int stillShot = -1, stillK, camShot = -1;
        readonly Dictionary<string, V3> camFixed = new();
        public bool Over { get; private set; }
        public bool ZoneHeld => file.World.ZoneHeld;
        /// <summary>Seconds to its end.</summary>
        public double ToEnd => player.S.Length - player.T;
        /// <summary>Her own body has her ("play"): the double is gone, and her
        /// moves steer the player as a stick would.</summary>
        bool handed;
        Vector3? walkTo;
        double walkSpeed;
        /// <summary>Where her double was a frame ago, and how fast it was going.</summary>
        Vector3? herWas;
        Vector3 herVel;
        bool hudIn;

        sealed record Tween(double T0, double T1, Action<double> Apply);
        /// <summary>Free: through the air or the water (an exact place), not along the ground.</summary>
        sealed record Move(string Actor, Vector3 From, Vector3 To, double T0, double T1, double Heading, bool Free = false);

        public Cine(Game g, CineFile file, Battle b, Action? done)
        {
            this.g = g;
            this.file = file;
            this.b = b;
            this.done = done;
            ctx = g.Journey.Ctx;
            var cc = CineLines.Context(g.Journey.Ch, g.Journey.World.Facts.Where(kv => kv.Value.Truthy).Select(kv => kv.Key));
            player = new CinePlayer(new CineSchedule(file, cc, id => CineLines.Seconds(CineLines.Find(id, ctx))));
            places = new CinePlaces(file, (x, z) => g.scene!.HeightAt(x, z), ActorAt);
            seen = Settings.Current.SeenCinematics.Contains(file.Id);
            var cam = g.camera;
            if (g.chained is { } ch) { bars = ch.Bars; saved = ch.Saved; }
            else { bars = new(); g.AddChild(bars); saved = (cam.Fov, cam.KeepAspect, cam.Near, cam.Attributes); }
            cam.Near = 0.04f;
            g.controls.Captured = true;
            g.hud.ShowPlay(false);
            g.hud.Prompt(g.promptShown = null);
            g.SetHint(null);
            g.scene!.CameraHeld = true;
            if (g.scene.Player != null) g.scene.Player.Hidden = true;
            b.WorldRate = file.World.Rate; b.WorldRateT = 1e9;
            long t0 = System.Diagnostics.Stopwatch.GetTimestamp();
            double Ms() => (System.Diagnostics.Stopwatch.GetTimestamp() - t0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
            made = g.TakeCast(file.Id);
            double tTake = Ms(), tWorst = 0; string worst = "";
            foreach (var (name, c) in file.Cast) { double a = Ms(); Cast(name, c); if (Ms() - a > tWorst) { tWorst = Ms() - a; worst = name; } }
            double tCast = Ms();
            if (made != null) foreach (var n in made.Values) if (!n.IsInsideTree()) n.QueueFree();
            made = null;
            SunAhead();
            double tSun = Ms();
            GD.Print($"cinema: {file.Id} ({player.S.Length:0.0} s, {player.S.Shots.Count} shots)");
            Dispatch(player.Advance(0));
            if (Perf.On) GD.Print($"perf cine begin {file.Id}: ctor-to-take {tTake:0.0} cast {tCast - tTake:0.0} (worst {worst} {tWorst:0.0}) sun {tSun - tCast:0.0} dispatch {Ms() - tSun:0.0} ms");
        }

        /* --------------------------------------------------------- the cast -- */

        /// <summary>This file's cast made ahead on a worker (Game.CastAhead), while the cast is being stood up.</summary>
        Dictionary<string, Node3D>? made;
        Node3D? Made(string key) => made != null && made.Remove(key, out var n) ? n : null;

        void Cast(string name, CineCast c)
        {
            if (c.Kind == "survivor")
            {
                var lo = Loadouts.Of(g.Journey.Ch);
                // (made ahead on a worker while play went on, if she still looks so: Game.DoubleAhead)
                var v = g.TakeDouble(lo)
                    ?? new PersonView(lo.Person, new Held { Right = lo.Arms.Right, Left = lo.Arms.Left, Forearm = lo.Arms.Forearm }, 0.8) { Name = "CineSurvivor" };
                // The townsfolk's clips too (sitting on the floor, arms folded): made on the
                // same skeleton, they stand in until her own cinematic motion comes.
                if (FolkClips.Library() is { } folk && !v.Person.Anim.HasAnimationLibrary("folk")) v.Person.Anim.AddAnimationLibrary("folk", folk);
                g.scene!.AddChild(v);
                people[name] = v;
                if (c.Mark != null) Place(name, places.Resolve(MarkEl(c.Mark)), file.Mark(c.Mark).Heading);
                // In a safe place (the same rule as play's close-up) she goes sheathed, as play does.
                if (g.zone is { Combat: false } && v.Person.Own is { } own && Sheath.HasTown(v.Person.Calling, v.Person.Kind, own.Has))
                {
                    v.Sheathed = true;
                    v.Sheathe(true);
                }
                v.Cue(lo.Arms.Idle, 0, 1, 0);
            }
            else if (c.Kind == "npc" && c.Def != null && Lore.Person(c.Def) is { } def)
            {
                var v = new PersonView(def.Person ?? new PersonSpec(), def.Arms, 0.8 * (def.Scale ?? 1)) { Name = "Cine_" + name };
                PlayerView.ToCast(v);
                g.scene!.AddChild(v);
                people[name] = v;
                if (c.Mark != null) Place(name, places.Resolve(MarkEl(c.Mark)), file.Mark(c.Mark).Heading);
                v.Cue("Idle_Loop", 0, 1, 0);
            }
            else if (c.Kind == "boss")
            {
                // The cinematic's own Warden: the zone's waits hidden, and the
                // fight's takes his place where this one is left.
                var w = Made(name) as WardenView ?? new WardenView();
                if (ExtrasShadow) w.Body.BeginShadow();   // (his one shadow, as the extras': a no-op if begun ahead)
                w.Name = "Cine_" + name;
                w.Glow = c.Glow;
                PlayerView.ToCast(w);
                g.scene!.AddChild(w);
                bosses[name] = w;
                people[name] = w.Body;
                w.Body.Cue("Sword_Idle", 0, 1, 0);
                if (c.Mark != null) Place(name, places.Resolve(MarkEl(c.Mark)), file.Mark(c.Mark).Heading);
            }
            else if (c.Kind == "extras" && c.At != null)
            {
                // A crowd seen only here (the drowned in the ford): each dressed as an
                // enemy of its visual, each at its own place, all cued by the cast's name.
                var visuals = c.Visual is { Count: > 0 } vs ? vs : ["skeleton_minion"];
                var members = new List<string>();
                for (int i = 0; i < c.At.Count; i++)
                {
                    var spec = Visuals.Of(visuals[i % visuals.Count]);
                    var v = Made($"{name}.{i}") as PersonView ?? new PersonView(spec.Person ?? new PersonSpec(), spec.Arms, 0.8 * spec.Scale);
                    if (ExtrasShadow) v.BeginShadow();   // (made here, not ahead: its one shadow begun now; a no-op if begun)
                    v.Name = $"Cine_{name}{i}";
                    PlayerView.ToCast(v);
                    g.scene!.AddChild(v);
                    string who = $"{name}.{i}";
                    people[who] = v;
                    members.Add(who);
                    Place(who, places.Resolve(c.At[i]), c.Heading);
                    // Out of step with each other, as a crowd stands.
                    v.Cue(c.Idle ?? "Zombie_Idle_Loop", i * 0.37 % 1.6, 1, 0);
                }
                groups[name] = members;
            }
            else if (c.Kind == "orb")
            {
                var o = new OrbView(c.Color ?? "#bfe6ff", c.Size) { Name = "Cine_" + name };
                g.scene!.AddChild(o);
                orbs[name] = o;
                orbLight[name] = 6 * c.Glow;
                ((IOrb)o).Light = orbLight[name];
                if (c.Mark != null) Place(name, places.Resolve(MarkEl(c.Mark)), 0, false);
            }
        }

        /// <summary>Whoever or whatever a cue moves: a person (a boss's body) or an orb.</summary>
        Node3D? NodeOf(string actor) => people.TryGetValue(actor, out var v) ? v : orbs.TryGetValue(actor, out var o) ? o : null;

        /// <summary>A crowd's cue as one member's.</summary>
        static CineCue Member(CineCue c, string who)
        {
            return new CineCue { At = c.At, Do = c.Do, When = c.When, Skip = c.Skip, Args = c.Args, Actor = who };
        }

        static JsonElement MarkEl(string mark) => JsonDocument.Parse($"{{\"mark\":\"{mark}\"}}").RootElement;

        void Place(string actor, V3 at, double heading, bool visible = true)
        {
            if (people.TryGetValue(actor, out var v)) v.Place(at.X, at.Y, at.Z, heading, visible);
            else if (orbs.TryGetValue(actor, out var o)) { o.Position = V(at); o.Visible = visible; }
        }

        /// <summary>Where someone is now, for the camera: their feet, or a bone.</summary>
        V3? ActorAt(string name, string? bone)
        {
            if (people.TryGetValue(name, out var v))
            {
                var p = v.GlobalPosition;
                if (bone != null)
                {
                    var sk = v.Person.Skeleton;
                    int i = sk.FindBone(bone switch { "head" or "eyes" => "Head", "hand_r" => "hand_r", "hand_l" => "hand_l", "chest" => "spine_03", _ => bone });
                    if (i >= 0) p = sk.GlobalTransform * sk.GetBoneGlobalPose(i).Origin;
                    if (bone == "eyes") p += new Vector3(0, 0.07f, 0);
                }
                // Handed over, she walks in her own body and the stand-in stays behind, hidden:
                // a place on her (a camera tracking her chest) goes with the body that moves.
                if (handed && name == "her" && g.scene?.Player is { } pv) p += pv.GlobalPosition - v.GlobalPosition;
                return new V3(p.X, p.Y, p.Z);
            }
            if (enemies.TryGetValue(name, out var e)) return new V3(e.X, g.scene!.HeightAt(e.X, e.Z) + (bone == "head" ? 1.6 : 0), e.Z);
            if (orbs.TryGetValue(name, out var o)) { var q = o.GlobalPosition; return new V3(q.X, q.Y, q.Z); }
            return null;
        }

        /* ------------------------------------------------------------ frame -- */

        // (env CINEDBG, shots only, off unless set: the cinematic light changed, to tell her materials' faults from
        // its own (face 30 cine): "key=0.5" the sun or moon's energy scaled, "glow=0.5" the cues' held lamps',
        // "lamps=0.5" the zone's lamps', "ambient=0.5" the sky's, "nossao", "nosunshadow", "noomnishadow", "nodof", "fill=E" a soft white spot from over the lens)
        static readonly Dictionary<string, float>? cineDbg = Args.Has("shot") && System.Environment.GetEnvironmentVariable("CINEDBG") is { Length: > 0 } cd
            ? cd.Split(',').Select(kv => kv.Split('=')).ToDictionary(a => a[0], a => a.Length > 1 ? float.Parse(a[1], System.Globalization.CultureInfo.InvariantCulture) : 1f)
            : null;
        float keyWas = -1, keySet = -1, ambSet = -1;
        void CineDbg()
        {
            if (cineDbg is not { } d) return;
            void Scale(Light3D l, float k)
            {
                // (each light scaled once: its energy as set by the cues kept in its metadata)
                if (!l.HasMeta("cdbg") || (float)l.GetMeta("cdbg_set") != l.LightEnergy) { l.SetMeta("cdbg", l.LightEnergy); l.LightEnergy *= k; l.SetMeta("cdbg_set", l.LightEnergy); }
            }
            if (d.TryGetValue("key", out var kk) && g.air.Key.LightEnergy != keySet) { keyWas = g.air.Key.LightEnergy; keySet = keyWas * kk; g.air.Key.LightEnergy = keySet; }
            if (d.TryGetValue("glow", out var gk))
                foreach (var pr in props.Values)
                    foreach (var l in pr.FindChildren("*", "OmniLight3D", true, false)) { Scale((Light3D)l, gk); if (d.ContainsKey("noomnishadow")) ((Light3D)l).ShadowEnabled = false; }
            if (d.TryGetValue("lamps", out var lk) || d.ContainsKey("noomnishadow"))
                foreach (var l in g.scene!.View.FindChildren("*", "OmniLight3D", true, false))
                {
                    if (d.ContainsKey("noomnishadow")) ((Light3D)l).ShadowEnabled = false;
                    if (d.ContainsKey("lamps")) Scale((Light3D)l, lk);
                }
            if (d.TryGetValue("ambient", out var ak) && g.air.Env.AmbientLightEnergy != ambSet) { ambSet = g.air.Env.AmbientLightEnergy * ak; g.air.Env.AmbientLightEnergy = ambSet; }
            if (d.ContainsKey("nossao")) g.air.Env.SsaoEnabled = false;
            if (d.ContainsKey("nosunshadow")) g.air.Key.ShadowEnabled = false;
            if (d.ContainsKey("nodof")) { dof.DofBlurNearEnabled = false; dof.DofBlurFarEnabled = false; }
            // ("fill=E": a soft white spot from just over the lens onto her eyes, people only, as the town close-up's key)
            if (d.TryGetValue("fill", out var fe) && ActorAt("her", "eyes") is V3 he)
            {
                if (dbgFill == null || !IsInstanceValid(dbgFill))
                {
                    dbgFill = new SpotLight3D { LightColor = new Color(1f, 0.96f, 0.9f), SpotAngle = 14, SpotRange = 8, SpotAttenuation = 0.4f, ShadowEnabled = false, LightCullMask = 2 | PlayerView.CastLayer, LightSpecular = 0.3f, LightEnergy = fe };
                    g.scene!.AddChild(dbgFill);
                }
                var eyes = new Vector3((float)he.X, (float)he.Y, (float)he.Z);
                var c0 = g.camera.GlobalTransform;
                dbgFill.GlobalPosition = c0.Origin + c0.Basis.Y * 0.25f;
                if (dbgFill.GlobalPosition.DistanceTo(eyes) > 0.05f) dbgFill.LookAt(eyes);
            }
        }
        SpotLight3D? dbgFill;

        readonly Dictionary<string, Rig> rigs = new();
        /// <summary>A zone lamp's glowing piece a "globe" cue dimmed: what it wore before (put back at the end), its own copy, its colour.</summary>
        sealed record Globe(MeshInstance3D M, int S, Material? Was, ShaderMaterial Dim, Vector3 Base) { public float Level = 1; public Vector3? Tint; }
        readonly List<Globe> globes = new();
        /// <summary>A globe cue's halos: the quad, the globe's middle, how far toward the lens it sits (so the egg does not hide its heart).</summary>
        readonly List<(Node3D Q, Vector3 At, float R)> globeHalos = new();
        /// <summary>The bosses a "hide" cue hid: their Shine shows them every frame, so they are hidden again after it (C02 s8:
        /// the Warden and his lamp-iron stood at her temple, the lamp a clipped disc at the frame's edge).</summary>
        readonly HashSet<Node3D> bossHidden = new();
        /// <summary>The river's materials a "water" cue scaled (put back to 1 at the end).</summary>
        readonly HashSet<ShaderMaterial> waters = new();
        readonly Dictionary<ShaderMaterial, float> waterFoam = new();
        bool stonesSet;
        readonly Dictionary<ShaderMaterial, float> stoneEdge = new();

        /// <summary>Each rig light where its shot puts it: off the lens, or on its place, aimed at its mark.</summary>
        void PlaceRigs()
        {
            int shot = player.Shot.Index;
            foreach (var (name, r) in rigs.ToList())
            {
                if (r.Shot >= 0 && r.Shot != shot) { r.Free(); rigs.Remove(name); continue; }
                var aim = r.Aim.ValueKind == JsonValueKind.Undefined ? (ActorAt("her", "eyes") is V3 he ? V(he) : g.camera.GlobalPosition) : V(places.Resolve(r.Aim));
                Vector3 at;
                if (r.From.ValueKind == JsonValueKind.Object && r.From.TryGetProperty("lens", out var lens))
                {
                    var c0 = g.camera.GlobalTransform;
                    float ox = (float)lens[0].GetDouble(), oy = (float)lens[1].GetDouble(), oz = lens.GetArrayLength() > 2 ? (float)lens[2].GetDouble() : 0;
                    at = c0.Origin + c0.Basis.X * ox + c0.Basis.Y * oy + c0.Basis.Z * oz;
                }
                else at = r.From.ValueKind == JsonValueKind.Undefined ? g.camera.GlobalPosition : V(places.Resolve(r.From));
                r.L.GlobalPosition = at;
                r.L.SpotRange = at.DistanceTo(aim) * 1.6f + 1;
                if (at.DistanceTo(aim) > 0.05f) r.L.LookAt(aim, Mathf.Abs((aim - at).Normalized().Y) > 0.98f ? Vector3.Forward : Vector3.Up);
            }
        }

        public void Frame(double dt)
        {
            Skipping(dt);
            if (Over) return;
            Dispatch(player.Advance(dt));
            double t = player.T;
            if (later.Count > 0)
            {
                var due = later.Where(c => c.T <= t).OrderBy(c => c.T).ToList();
                foreach (var tc in due) later.Remove(tc);
                Dispatch(due);
            }
            foreach (var tw in tweens.ToList())
            {
                double k = tw.T1 <= tw.T0 ? 1 : Math.Clamp((t - tw.T0) / (tw.T1 - tw.T0), 0, 1);
                tw.Apply(k);
                if (k >= 1) tweens.Remove(tw);
            }
            foreach (var m in moves.ToList())
            {
                double k = Math.Clamp((t - m.T0) / Math.Max(0.01, m.T1 - m.T0), 0, 1);
                var p = m.From.Lerp(m.To, (float)CineCamera.Ease("inout", k));
                if (people.TryGetValue(m.Actor, out var v)) v.Place(p.X, m.Free ? p.Y : g.scene!.HeightAt(p.X, p.Z), p.Z, m.Heading, true);
                else if (orbs.TryGetValue(m.Actor, out var o)) o.Position = p;
                if (k >= 1) moves.Remove(m);
            }
            // Her double's pace (what a hand-over at the end carries on).
            if (!handed && people.TryGetValue("her", out var herNow))
            {
                var at = herNow.GlobalPosition;
                if (herWas is Vector3 was && dt > 0) herVel = (at - was) / (float)dt;
                herWas = at;
            }
            Steer();
            // The play's HUD comes in as the bars go out, over the blend into the game's camera.
            if (!hudIn && file.End.Her != null && file.End.Next == null && player.T >= player.S.Length - Math.Max(0.4, file.Bars.Out))
            {
                hudIn = true;
                g.hud.ShowPlay(true, (float)Math.Max(0.4, file.Bars.Out));
            }
            foreach (var v in people.Values) v.Advance(dt);
            foreach (var w in bosses.Values) { w.Shine(dt); if (bossHidden.Contains(w)) w.Visible = false; }
            foreach (var o in orbs.Values) o.Turn(dt);
            Camera(dt);
            if (globeHalos.Count > 0 && g.GetViewport().GetCamera3D() is Camera3D hcam)
                foreach (var (hq, hat, hr) in globeHalos)
                    if (GodotObject.IsInstanceValid(hq)) hq.GlobalPosition = hat + (hcam.GlobalPosition - hat).Normalized() * hr;
            PlaceRigs();
            HerLight();
            if ((skinSky != 1 || skinEar != 1) && people.TryGetValue("her", out var hsk))
            { SurvivorUnchained.View.People.HerSkyShare(hsk.Person, skinSky); SurvivorUnchained.View.People.HerEarWarmth(hsk.Person, skinEar); }
            // No ember or smoke between a close lens and her (C01 s10: a drifting ember was a soft
            // orange disc across her cheek): the Look's ClearNear, to just short of her face.
            float lensToHer = people.TryGetValue("her", out var hv) && hv.Visible && ActorAt("her", "eyes") is V3 ey ? g.camera.GlobalPosition.DistanceTo(V(ey)) : 99;
            Campfire.ClearNear(lensToHer < 4 ? Math.Max(0, lensToHer - 0.3f) : 0);
            CineDbg();
            var shot = player.Shot.Shot;
            // --shot NAME --until S: each shot's standing frame saved as it passes (the previs boards).
            var span = player.Shot;
            // --stills N: N frames of each shot, evenly through it (to judge its motion), instead.
            int many = (int)Args.Num("stills", 0);
            if (span.Index != stillShot) { stillShot = span.Index; stillK = 0; }
            double nextStill = many > 0 ? span.Dur * (stillK + 0.5) / many : shot.Still ?? span.Dur * 0.6;
            if (stillK < Math.Max(1, many) && player.Local >= nextStill)
            {
                stillK++;
                Shots.Want($"{file.Id}_s{shot.Id}", 0.05);
                if (Args.Has("mouth-cam")) GD.Print($"STILL {file.Id}_s{shot.Id}_{stillK}");
                if (Args.Has("lampdbg") && g.camera != null)
                {
                    foreach (var ln in SurvivorUnchained.View.ShadowLamp.Describe(g.camera)) GD.Print($"lampdbg {file.Id} s{shot.Id} {ln}");
                    foreach (var ln in Census(g)) GD.Print($"census {file.Id} s{shot.Id} {ln}");
                }
                // --cinebones: where the cast's bones are at each still, for framing shots on them.
                if (Args.Has("cinebones"))
                    foreach (var name in people.Keys)
                        GD.Print($"cinebones {file.Id} s{shot.Id} {name} " + string.Join(" ", new[] { "head", "eyes", "chest", "hand_r", "hand_l", "foot_l", "foot_r" }
                            .Select(bn => ActorAt(name, bn) is V3 p ? $"{bn}=({p.X:0.000},{p.Y:0.000},{p.Z:0.000})" : "")));
                // --cinebones also prints where her bones land on screen, as fractions of the frame
                // (u right, v down) and the frame-height size of 10 cm at her eyes: boxes for measuring stills.
                if (Args.Has("cinebones") && people.ContainsKey("her") && g.camera != null)
                {
                    var vs = g.camera.GetViewport().GetVisibleRect().Size;
                    string Px(Vector3 w) => g.camera.IsPositionBehind(w) ? "behind" : $"({g.camera.UnprojectPosition(w).X / vs.X:0.0000},{g.camera.UnprojectPosition(w).Y / vs.Y:0.0000})";
                    var parts = new List<string>();
                    foreach (var bn in new[] { "eyes", "head", "hand_r", "hand_l", "lowerarm_r", "lowerarm_l" })
                        if (ActorAt("her", bn) is V3 bp) parts.Add($"{bn}={Px(V(bp))}");
                    if (ActorAt("her", "eyes") is V3 ep)
                    {
                        var e3 = V(ep); var r3 = g.camera.GlobalTransform.Basis.X * 0.1f;
                        float s10 = g.camera.IsPositionBehind(e3) ? 0 : (g.camera.UnprojectPosition(e3 + r3) - g.camera.UnprojectPosition(e3)).Length() / vs.Y;
                        parts.Add($"s10={s10:0.0000}");
                    }
                    foreach (var (on, o) in orbs) if (o.Visible) parts.Add($"orb_{on}={Px(o.GlobalPosition)}");
                    GD.Print($"cinepx {file.Id} s{shot.Id} k{stillK} her " + string.Join(" ", parts));
                }
                if (Args.Has("cinebones"))
                {
                    // A held blade's tip, the cast's creatures (where drawn: their feet, sunk or not) and the orbs.
                    foreach (var (name, v) in people)
                        if (v.TipOf("handslot.r") is Vector3 tp) GD.Print($"cinebones {file.Id} s{shot.Id} {name} tip_r=({tp.X:0.000},{tp.Y:0.000},{tp.Z:0.000})");
                    foreach (var (name, e) in enemies)
                        GD.Print($"cinebones {file.Id} s{shot.Id} {name} feet=({e.X:0.000},{g.scene!.HeightAt(e.X, e.Z) - SinkOf(e):0.000},{e.Z:0.000}) facing={e.Facing:0.00} state={e.State}");
                    foreach (var (name, o) in orbs)
                        GD.Print($"cinebones {file.Id} s{shot.Id} {name} orb=({o.GlobalPosition.X:0.000},{o.GlobalPosition.Y:0.000},{o.GlobalPosition.Z:0.000}) light={orbLight.GetValueOrDefault(name):0.00}");
                }
                // --cinenear X,Z,R: every visible mesh within R of a point, by path, at each
                // shot's still (what is that in the frame? Lowford's stray ring stone was found so).
                if (Args.Get("cinenear") is string near && stillK == 1)
                {
                    var q = near.Split(',');
                    var c = new Vector3(float.Parse(q[0], System.Globalization.CultureInfo.InvariantCulture), 0, float.Parse(q[1], System.Globalization.CultureInfo.InvariantCulture));
                    float rr = float.Parse(q[2], System.Globalization.CultureInfo.InvariantCulture);
                    foreach (var n in g.GetTree().Root.FindChildren("*", "GeometryInstance3D", true, false))
                        if (n is GeometryInstance3D gi && gi.IsVisibleInTree() && gi is not MultiMeshInstance3D)
                        {
                            var bb = gi.GlobalTransform * gi.GetAabb();
                            var cc = bb.GetCenter();
                            if (new Vector2(cc.X - c.X, cc.Z - c.Z).Length() < rr && bb.Size.Length() < 6)
                                GD.Print($"cinenear s{shot.Id} {gi.GetPath()} at=({cc.X:0.00},{cc.Y:0.00},{cc.Z:0.00}) size=({bb.Size.X:0.00},{bb.Size.Y:0.00},{bb.Size.Z:0.00})");
                        }
                }
                if (Args.Has("cinebones"))
                    foreach (var (name, w) in bosses)
                        GD.Print($"cinebones {file.Id} s{shot.Id} {name} lamp=({w.LampAt.X:0.00},{w.LampAt.Y:0.00},{w.LampAt.Z:0.00})");
            }
            bars.Frame((float)player.Bars, shot.Black ? 1 : 0);
            if (player.Done) Over = true;
        }

        void Skipping(double dt)
        {
            bool held = g.controls.Held(Act.Interact) || g.controls.Held(Act.Pause);
            if (held && player.CanSkip(seen)) skipHeld += dt;
            else skipHeld = Math.Max(0, skipHeld - dt * 3);
            bars.Skip((float)(skipHeld / file.Skip.Hold));
            if (skipHeld < file.Skip.Hold) return;
            // Straight to the end: what lasts is done, nothing is heard.
            Dispatch(player.SkipToEnd(), skipping: true);
            g.voice.Stop();
            Over = true;
        }

        void Camera(double dt)
        {
            // A place on someone is taken where they are as the shot begins (a camera
            // is set up on its marks), unless it says "track" (it follows them).
            if (camShot != player.Shot.Index) { camShot = player.Shot.Index; camFixed.Clear(); }
            var pose = player.Camera(e =>
            {
                if (e.ValueKind != JsonValueKind.Object || !e.TryGetProperty("actor", out _) || e.TryGetProperty("track", out _)) return places.Resolve(e);
                var key = e.GetRawText();
                return camFixed.TryGetValue(key, out var p) ? p : camFixed[key] = places.Resolve(e);
            });
            if (pose.Black || pose.Hold) return;
            var cam = g.camera;
            Vector3 pos = V(pose.Pos), at = V(pose.At);
            // A close shot draws the key's shadow from a short reach, so its first split is fine
            // enough for a face: from 70 m a jaw cast a stair-stepped edge down her neck.
            if (keyReach < 0) keyReach = g.air.Key.DirectionalShadowMaxDistance;
            g.air.Key.DirectionalShadowMaxDistance = (at - pos).Length() < 3.5f ? 14 : keyReach;
            float hfov = (float)pose.Hfov;
            if (pose.FollowK > 0 && EndPoint() is Vector3 end)
            {
                var (fp, fl) = g.cam.PoseFor(end);
                float k = (float)pose.FollowK;
                // The way it looks turns from the shot's to the game's (a point far up a
                // road, lerped toward her, kept the camera looking ahead until the last
                // moment and lost her from the frame on the way).
                // The game's look is taken from where the camera is now, not from where it lands: its
                // direction from the landing place, laid on a crane still high and wide of it, aimed at
                // empty ground and lost her from the frame halfway up (C01 s12).
                pos = pos.Lerp(fp, k);
                Vector3 d0 = (at - pos).Normalized(), d1 = (fl - pos).Normalized();
                float reach = Mathf.Lerp((at - pos).Length(), (fl - pos).Length(), k);
                // The look turns ahead of the move (its square root), so she stays in the frame.
                at = pos + (d0.Dot(d1) > 0.9999f ? d1 : d0.Slerp(d1, Mathf.Sqrt(k))) * reach;
                hfov = Mathf.Lerp(hfov, FollowHfov(), k);
            }
            if (pose.Handheld > 0)
            {
                // A hand on the camera: slow drift and a little tremor, the same at the same moment.
                float t = (float)player.T, s = (float)pose.Handheld;
                float N(float a) => Mathf.Sin(t * 1.3f + a) * 0.6f + Mathf.Sin(t * 3.7f + a * 2.1f) * 0.3f + Mathf.Sin(t * 9.1f + a * 0.7f) * 0.1f;
                pos += new Vector3(N(1), N(2), N(3)) * 0.03f * s;
                at += new Vector3(N(4), N(5), N(6)) * 0.05f * s;
            }
            var basis = Godot.Basis.LookingAt(at - pos, Vector3.Up);
            if (pose.Roll != 0) basis = basis.Rotated(basis.Z, Mathf.DegToRad((float)pose.Roll));
            cam.GlobalTransform = new Transform3D(basis, pos);
            cam.KeepAspect = Camera3D.KeepAspectEnum.Width;
            cam.Fov = hfov;
            if (pose.Focus is double f && pose.FollowK < 0.5)
            {
                // Depth of field from the lens: sharp across what f-number and distance allow, soft beyond.
                double mm = pose.Lens, n = pose.Fstop, coc = 0.03;
                double h = mm * mm / (n * coc) / 1000;
                double near = h * f / (h + f), far = h > f ? h * f / (h - f) : 1e4;
                dof.DofBlurNearEnabled = true;
                dof.DofBlurNearDistance = (float)Math.Max(0.02, near);
                dof.DofBlurNearTransition = (float)Math.Max(0.02, near * 0.5);
                dof.DofBlurFarEnabled = true;
                dof.DofBlurFarDistance = (float)Math.Min(far, 500);
                dof.DofBlurFarTransition = (float)Math.Max(0.1, (far - f) * 1.5 + f * 0.25);
                dof.DofBlurAmount = 0.12f;
                cam.Attributes = dof;
            }
            else cam.Attributes = saved.Attr;
        }

        float FollowHfov()
        {
            var size = g.GetViewport().GetVisibleRect().Size;
            return Mathf.RadToDeg(2 * Mathf.Atan(Mathf.Tan(Mathf.DegToRad(saved.Fov) / 2) * size.X / size.Y));
        }

        /// <summary>Where the game's camera takes over: on her as she really is
        /// (her own body once handed over, else her double), so the blend lands
        /// on the frame play begins with; on the end mark only if she is not there.</summary>
        Vector3? EndPoint()
        {
            if (file.End.Her is not string m) return null;
            if (handed) return new Vector3((float)b.Player.X, (float)g.scene!.HeightAt(b.Player.X, b.Player.Z), (float)b.Player.Z);
            if (!player.Skipped && people.TryGetValue("her", out var her) && her.Visible) return her.GlobalPosition;
            var p = places.Resolve(MarkEl(m));
            return new Vector3((float)p.X, (float)g.scene!.HeightAt(p.X, p.Z), (float)p.Z);
        }

        /// <summary>"play": her own body takes her double's place, where it
        /// stands and facing as it faces (put it on a cut, so no pose is seen
        /// to change). From here she is the player, steered by her moves.</summary>
        void Handover()
        {
            if (handed || !people.TryGetValue("her", out var her) || g.scene?.Player is not { } pv) return;
            handed = true;
            var p = b.Player;
            var at = her.GlobalPosition;
            p.X = at.X; p.Z = at.Z; p.Facing = her.Rotation.Y; p.Vx = p.Vz = 0;
            pv.Face(her.Rotation.Y, new Vector3(at.X, (float)g.scene.HeightAt(at.X, at.Z), at.Z));
            pv.Hidden = false;
            pv.Still = true;
            her.Visible = false;
            moves.RemoveAll(mv => mv.Actor == "her");
        }

        /// <summary>Her own body, steered to where her last move goes, at its pace; it stops there.</summary>
        void Steer()
        {
            if (!handed) return;
            if (walkTo is not Vector3 goal) { g.cineWalk = null; return; }
            var p = b.Player;
            var d = new Vector2(goal.X - (float)p.X, goal.Z - (float)p.Z);
            if (d.Length() < 0.12f) { walkTo = null; g.cineWalk = null; return; }
            double top = Math.Max(0.1, b.Stats.Get(Stat.MoveSpeed) * p.SlowF);
            // Slowing over her last half-metre, as anyone does who means to stop there.
            double k = Math.Min(1, walkSpeed / top) * Math.Clamp(d.Length() / 0.45, 0.35, 1);
            var dir = d.Normalized();
            g.cineWalk = (dir.X * k, dir.Y * k);
        }

        static Vector3 V(V3 v) => new((float)v.X, (float)v.Y, (float)v.Z);

        /* ------------------------------------------------------------- cues -- */

        void Dispatch(List<TimedCue> cues, bool skipping = false)
        {
            foreach (var tc in cues)
            {
                long q0 = System.Diagnostics.Stopwatch.GetTimestamp();
                try { Do(tc, skipping); }
                catch (Exception e) { GD.PushWarning($"cinema {file.Id} shot {tc.Shot.Shot.Id}: {tc.Cue.Do} failed: {e.Message}"); }
                double qms = (System.Diagnostics.Stopwatch.GetTimestamp() - q0) * 1000.0 / System.Diagnostics.Stopwatch.Frequency;
                if (Perf.On && qms > 2) GD.Print($"perf cue {file.Id} {tc.Cue.Do} {tc.Cue.Actor} {qms:0.0} ms");
            }
        }

        void Do(TimedCue tc, bool skipping)
        {
            var c = tc.Cue;
            double t0 = tc.T, over = c.Num("over");
            // A crowd's cue is each member's, "stagger" seconds apart down the crowd (a wave).
            if (groups.TryGetValue(c.Actor, out var members))
            {
                double stagger = c.Num("stagger");
                for (int i = 0; i < members.Count; i++)
                {
                    var one = tc with { T = tc.T + i * stagger, Cue = Member(c, members[i]) };
                    if (stagger > 0 && i > 0 && !skipping) later.Add(one);
                    else Do(one, skipping);
                }
                return;
            }
            switch (c.Do)
            {
                case "line":
                {
                    var l = CineLines.Find(c.Str("id")!, ctx);
                    if (l.Raw == "") break;
                    var take = g.voice.Say(l.VoId, l.Raw);
                    // Narration (the file says whose) reads unnamed, in italics, whoever voices it.
                    bars.Say(l.Text, file.Narrators.Contains(l.SpeakerId ?? "") ? null : l.Speaker, (take?.Sec ?? CineLines.Reading(l.Text)) + c.Num("linger", 0.7), l.Sung);
                    break;
                }
                case "music":
                {
                    var mood = c.Str("mood") ?? "silence";
                    g.sound.CineMood = mood == "game" ? null : Enum.Parse<Mood>(mood, true);
                    double from = g.sound.CineIntensity, to = c.Num("intensity", 0.5);
                    if (over > 0) tweens.Add(new Tween(t0, t0 + over, k => g.sound.CineIntensity = from + (to - from) * k));
                    else g.sound.CineIntensity = to;
                    break;
                }
                case "sfx":
                {
                    double pan = 0;
                    if (c.Has("where")) pan = Pan(places.Resolve(c.Get("where")));
                    Sfx.Cine(c.Str("name")!, c.Num("gain", 1), c.Num("pan", pan));
                    break;
                }
                case "place":
                {
                    var at = c.Has("where") ? places.Resolve(c.Get("where")) : places.Resolve(MarkEl(c.Str("mark")!));
                    double heading = c.Has("heading") ? c.Num("heading") : c.Str("mark") is string mk ? file.Mark(mk).Heading : 0;
                    Place(c.Actor, at, heading, c.Bool("visible", true));
                    // "tilt": pitched about their own across axis, degrees (lying on the back,
                    // a pose made for standing: the Warden in the river, his lamp up).
                    if (c.Has("tilt") && people.TryGetValue(c.Actor, out var tv)) tv.Rotation = new Vector3(Mathf.DegToRad((float)c.Num("tilt")), (float)heading, 0);
                    break;
                }
                case "hide":
                    if (bosses.TryGetValue(c.Actor, out var hw)) { hw.Visible = !c.Bool("hidden", true); if (hw.Visible) bossHidden.Remove(hw); else bossHidden.Add(hw); }
                    else if (NodeOf(c.Actor) is { } hv) hv.Visible = !c.Bool("hidden", true);
                    break;
                case "lamp":
                {
                    // A boss's eyes and lamp, or an orb's light: how bright, and whether it burns.
                    if (bosses.TryGetValue(c.Actor, out var w))
                    {
                        if (c.Has("lit")) w.LampLit = c.Bool("lit", true);
                        // "flame": the flame's core brightness (1 = as built), "flameColor" its hue (hex),
                        // "halo" its halo's strength: a lamp seen at night as lit glass, not a white disc.
                        if (c.Has("flame")) w.FlameLevel = (float)c.Num("flame");
                        if (c.Str("flameColor") is string fch) w.FlameColor = new Color(fch);
                        if (c.Has("halo")) w.HaloLevel = (float)c.Num("halo");
                        if (!c.Has("glow")) break;
                        double from = w.Glow, to = c.Num("glow");
                        if (over > 0 && !skipping) tweens.Add(new Tween(t0, t0 + over, k => w.Glow = from + (to - from) * k));
                        else w.Glow = to;
                    }
                    else if (orbs.TryGetValue(c.Actor, out var o))
                    {
                        if (c.Has("lit")) o.Visible = c.Bool("lit", true);
                        if (!c.Has("glow")) break;
                        double from = orbLight[c.Actor], to = 6 * c.Num("glow");
                        void Set(double l) { orbLight[c.Actor] = l; ((IOrb)o).Light = l; }
                        if (over > 0 && !skipping) tweens.Add(new Tween(t0, t0 + over, k => Set(from + (to - from) * k)));
                        else Set(to);
                    }
                    break;
                }
                case "anim":
                {
                    // A creature it stages takes one of its crowd roles and holds it (Grimtunnel's arms round the heart).
                    if (enemies.TryGetValue(c.Actor, out var ce))
                    {
                        var st = staged.GetValueOrDefault(ce.Id);
                        // "where": drawn facing it (Grimtunnel to her, not to where her own body waits).
                        double? face = st.Facing;
                        if (c.Has("where")) { var fw = places.Resolve(c.Get("where")); face = Math.Atan2(fw.Z - ce.Z, fw.X - ce.X); }
                        staged[ce.Id] = (st.Sink, c.Str("clip") ?? st.Role, t0, face);
                        CrowdView.Staged = x => staged.TryGetValue(x.Id, out var sx) ? (sx.Sink, sx.Role, player.T - sx.T0, sx.Facing) : null;
                        break;
                    }
                    if (!people.TryGetValue(c.Actor, out var v)) break;
                    var clip = c.Str("clip")!;
                    if (clip == "@idle") clip = Loadouts.Of(g.Journey.Ch).Arms.Idle;
                    v.Cue(clip, c.Num("from"), c.Num("speed", 1), c.Num("blend", 0.2));
                    break;
                }
                case "play":
                    Handover();
                    break;
                case "move":
                {
                    if (handed && c.Actor == "her")
                    {
                        // Her own body walks it, at the pace the timeline asks.
                        var goal = V(places.Resolve(c.Has("to") && c.Get("to").ValueKind != JsonValueKind.String ? c.Get("to") : MarkEl(c.Str("to")!)));
                        var p0 = b.Player;
                        walkTo = goal;
                        walkSpeed = new Vector2(goal.X - (float)p0.X, goal.Z - (float)p0.Z).Length() / Math.Max(0.1, c.Num("dur", 1));
                        break;
                    }
                    if (NodeOf(c.Actor) is not { } n) break;
                    var toEl = c.Has("to") && c.Get("to").ValueKind != JsonValueKind.String ? c.Get("to") : MarkEl(c.Str("to")!);
                    var to = places.Resolve(toEl);
                    var from = n.GlobalPosition;
                    var dest = V(to);
                    double heading = c.Has("heading") ? c.Num("heading") : Math.Atan2(dest.X - from.X, dest.Z - from.Z);
                    // An exact place ("abs") is gone to through the air or the water; anything else along the ground.
                    bool free = orbs.ContainsKey(c.Actor) || (toEl.ValueKind == JsonValueKind.Object && toEl.TryGetProperty("abs", out _));
                    moves.Add(new Move(c.Actor, from, dest, t0, t0 + c.Num("dur", 1), heading, free));
                    if (c.Str("clip") is string mc && n is PersonView v)
                    {
                        double pace = c.Num("speed", 1);
                        // Her own walk keeps its feet to the ground: the clip's metres a second against the ground covered.
                        var resolved = People.Clip(v.Person, mc, v.Sheathed);
                        if (v.Person.Own is { } own && own.Owns(resolved) && own.Speed(resolved[own.Prefix.Length..]) is float sp && sp > 0)
                        {
                            double dist = new Vector2(dest.X - from.X, dest.Z - from.Z).Length(), dur = Math.Max(0.01, c.Num("dur", 1));
                            pace = Math.Clamp(dist / dur / (sp * v.Person.Root.Scale.X), 0.5, 1.6);
                        }
                        v.Cue(mc, 0, pace, 0.25);
                    }
                    break;
                }
                case "look":
                {
                    if (!people.TryGetValue(c.Actor, out var v)) break;
                    var at = places.Resolve(c.Get("where"));
                    float from = v.Rotation.Y, to = Mathf.Atan2((float)at.X - v.GlobalPosition.X, (float)at.Z - v.GlobalPosition.Z);
                    to = from + Mathf.Wrap(to - from, -Mathf.Pi, Mathf.Pi);
                    tweens.Add(new Tween(t0, t0 + Math.Max(over, 0.01), k => v.Rotation = new Vector3(0, Mathf.Lerp(from, to, (float)CineCamera.Ease("inout", k)), 0)));
                    break;
                }
                case "face":
                {
                    if (!people.TryGetValue(c.Actor, out var v) || c.Get("keys").ValueKind != JsonValueKind.Object) break;
                    var now = faces.TryGetValue(c.Actor, out var f) ? f : faces[c.Actor] = new();
                    var start = new Dictionary<string, float>(now);
                    var want = c.Get("keys").EnumerateObject().ToDictionary(p => p.Name, p => (float)p.Value.GetDouble());
                    tweens.Add(new Tween(t0, t0 + over, k =>
                    {
                        foreach (var (name, target) in want)
                        {
                            float a = start.TryGetValue(name, out var s) ? s : 0;
                            now[name] = Mathf.Lerp(a, target, (float)CineCamera.Ease("inout", k));
                        }
                        People.HerFace(v.Person, now);
                    }));
                    break;
                }
                case "head":
                {
                    // A look with the head and neck, the body left as it is ("look" turns the body):
                    // "where" is the point looked at; "amount" 0 (or no "where") lets the head go.
                    if (!people.TryGetValue(c.Actor, out var v)) break;
                    var skel = v.Person.Skeleton;
                    var turn = skel.GetNodeOrNull<HeadTurn>("HeadTurn");
                    if (turn == null) skel.AddChild(turn = new HeadTurn());
                    // (mid-shot a new aim glides there; at a cut it is taken at once, and her hair hung afresh for the
                    // new pose: a glide across the cut showed the last shot's head for a frame, C01 s10, Cinematics 7 r2)
                    bool headCut = skipping || tc.T - tc.Shot.Start < 1e-6;
                    turn.Glide = !headCut;
                    if (headCut) foreach (var hs in skel.FindChildren("*", "", true, false).OfType<HairSway>()) hs.Settle();
                    bool letGo = !c.Has("where") || c.Num("amount", 1) <= 0;
                    if (!letGo) turn.Target = V(places.Resolve(c.Get("where")));
                    turn.Want = letGo ? 0 : (float)c.Num("amount", 1);
                    turn.Rate = (float)(1 / Math.Max(0.05, over));
                    break;
                }
                case "gaze":
                {
                    // Her eyes to "look" (iris radii, +x her left, +y down; HerFaceLife, Play/GazeShift): a saccade
                    // timed by its size, or a glide over "over" s. The head is carried only when the cue asks ("head", its
                    // share 0..1, the eyes then held to "reach", 0.5, the head taking the rest); "blink" forces or stops
                    // the blink a big jump brings; "snap": false waits for her next saccade. At a shot's first frame
                    // (the shot just cut) the look is set at once, no slide across the cut.
                    if (Life(c.Actor) is not { } life) break;
                    var look = c.Get("look");
                    Vector2? to = look.ValueKind == JsonValueKind.Array ? new Vector2((float)look[0].GetDouble(), (float)look[1].GetDouble()) : null;
                    float? wander = c.Has("wander") ? (float)c.Num("wander") : null;
                    float? reach = c.Get("reach").ValueKind == JsonValueKind.Number ? (float)c.Num("reach") : null;
                    float? head = c.Get("head").ValueKind == JsonValueKind.Number ? (float)c.Num("head") : null;
                    bool? blink = c.Get("blink").ValueKind is JsonValueKind.True or JsonValueKind.False ? c.Bool("blink") : null;
                    bool cut = skipping || tc.T - tc.Shot.Start < 1e-6;
                    life.Gaze(to, wander, c.Bool("snap", true), over, reach, head, blink, cut);
                    break;
                }
                case "eyes":
                {
                    // Her eye shader's catchlight for a shot, put back when the cinematic ends
                    // (face 34: C01 s8, looking up from the ground, the catchlight window sat in her
                    // pupils' middle, a hard white dot: judge j1).
                    if (!people.TryGetValue(c.Actor, out var v)) break;
                    foreach (var mi in v.Person.Skeleton.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>())
                        for (int s = 0; mi.Mesh != null && s < mi.Mesh.GetSurfaceCount(); s++)
                            if (mi.GetSurfaceOverrideMaterial(s) is ShaderMaterial m && m.Shader?.ResourcePath == "res://shaders/heroine_eye.gdshader")
                            {
                                foreach (var key in new[] { "catchlight", "catch_size" })
                                    if (c.Get(key).ValueKind == JsonValueKind.Number) SetEye(m, key, (float)c.Num(key));
                                var at = c.Get("catch_at");
                                if (at.ValueKind == JsonValueKind.Array) SetEye(m, "catch_at", new Vector2((float)at[0].GetDouble(), (float)at[1].GetDouble()));
                            }
                    break;
                }
                case "lids":
                {
                    if (Life(c.Actor) is not { } life) break;
                    if (c.Get("value").ValueKind != JsonValueKind.Number) { life.Lids = null; break; }
                    float from = life.Lids ?? 0, to = (float)c.Num("value");
                    tweens.Add(new Tween(t0, t0 + over, k => life.Lids = Mathf.Lerp(from, to, (float)k)));
                    break;
                }
                case "fingers":
                {
                    // Her fingers curl toward the palm (HerPose.CineCurlL/R, degrees): "side" l, r or both, eased by
                    // smoothstep from where they are to "curl" over "over" s. Visual only: dropped on a skip, and put
                    // back to 0 when the cinematic ends.
                    if (skipping || !people.TryGetValue(c.Actor, out var fv) || fv.Person.Pose is not { } hp) break;
                    string side = c.Str("side") ?? "both";
                    float to = (float)c.Num("curl", 0);
                    bool left = side != "r", right = side != "l";
                    float fromL = hp.CineCurlL, fromR = hp.CineCurlR;
                    tweens.Add(new Tween(t0, t0 + over, k =>
                    {
                        if (!IsInstanceValid(hp)) return;
                        float e = Mathf.SmoothStep(0, 1, (float)k);
                        if (left) hp.CineCurlL = Mathf.Lerp(fromL, to, e);
                        if (right) hp.CineCurlR = Mathf.Lerp(fromR, to, e);
                    }));
                    break;
                }
                case "light":
                {
                    int i = (int)c.Num("light");
                    float from = (float)c.Num("from", 1), to = (float)c.Num("level", 1), rate = (float)c.Num("rate", 1);
                    Color? col = c.Str("color") is string hex ? new Color(hex) : null;
                    if (over > 0 && !skipping) tweens.Add(new Tween(t0, t0 + over, k => g.scene!.View.SetLevel(i, Mathf.Lerp(from, to, (float)k), col, rate)));
                    else g.scene!.View.SetLevel(i, to, col, rate);
                    // "size": the light's source in metres, softening its shadows (given back at the end).
                    if (c.Has("size")) { g.scene!.View.SetSize(i, (float)c.Num("size")); sized.Add(i); }
                    break;
                }
                case "lit":
                    g.scene!.View.SetLit((int)c.Num("light"), c.Bool("on", true));
                    break;
                case "fire":
                    g.scene!.View.SetFire((int)c.Num("light"), (float)c.Num("flames", 1));
                    break;
                case "atmosphere":
                {
                    var (to, fromAir) = AirOf(c);
                    double k0 = c.Num("k0"), k1 = c.Num("k1", 1);
                    if (fromAir is { } from)
                    {
                        if (over > 0 && !skipping)
                        {
                            double last = -1;
                            tweens.Add(new Tween(t0, t0 + over, k =>
                            {
                                if (k - last <= 0.02 && k < 1) return;
                                last = k;
                                g.SetAtmosphere(Atmospheres.Blend(from, to, k0 + (k1 - k0) * k), k >= 1);
                            }));
                        }
                        else g.SetAtmosphere(k1 >= 1 ? to : Atmospheres.Blend(from, to, k1));
                    }
                    else g.SetAtmosphere(to);
                    break;
                }
                case "spawn":
                {
                    var at = places.Resolve(c.Has("where") ? c.Get("where") : MarkEl(c.Str("mark") ?? c.Actor));
                    var style = c.Str("style") switch { "rise" => SpawnStyle.Rise, "burrow" => SpawnStyle.Burrow, _ => SpawnStyle.Walk };
                    var e = b.SpawnEnemy(c.Str("def") ?? file.Cast.GetValueOrDefault(c.Actor)?.Def ?? "risen", at.X, at.Z, new Battle.SpawnOpts
                    {
                        Style = style, Level = (int)c.Num("level", 1), Tag = c.Str("tag"), Disposition = c.Bool("neutral") ? Disposition.Neutral : null,
                    });
                    if (e != null)
                    {
                        enemies[c.Actor] = e;
                        // "sink": drawn this far down into the ground or the water (Grimtunnel waist-deep in the ford).
                        if (c.Has("sink"))
                        {
                            staged[e.Id] = (c.Num("sink"), null, 0, null);
                            CrowdView.Staged = x => staged.TryGetValue(x.Id, out var st) ? (st.Sink, st.Role, player.T - st.T0, st.Facing) : null;
                        }
                    }
                    break;
                }
                case "world":
                    b.WorldRate = c.Num("rate"); b.WorldRateT = 1e9;
                    break;
                case "vfx":
                {
                    var at = c.Has("where") ? places.Resolve(c.Get("where")) : default;
                    switch (c.Str("kind"))
                    {
                        case "shake": g.cam.AddTrauma((float)c.Num("amount", 0.4)); break;
                        case "nova": b.Events.Emit(new Ev.Nova { X = at.X, Z = at.Z, Radius = c.Num("radius", 2), School = Enum.Parse<School>(c.Str("school") ?? "frost", true), Duration = c.Num("dur", 0.9), Plain = c.Has("plain") && c.Get("plain").ValueKind == System.Text.Json.JsonValueKind.True }); break;
                        case "burst": b.Events.Emit(new Ev.Explosion { X = at.X, Z = at.Z, Radius = c.Num("radius", 1.2), School = Enum.Parse<School>(c.Str("school") ?? "physical", true), Power = c.Num("power", 0.5) }); break;
                    }
                    break;
                }
                case "title":
                    g.hud.Announce(new Announcement(c.Str("title") ?? "", c.Str("sub"), c.Str("kind") ?? "danger", c.Num("seconds", 3.4)));
                    break;
                case "event":
                    g.zone?.CineEvent(c.Str("name") ?? "");
                    break;
                case "hold":
                {
                    // What a hand holds: a piece, nothing, or her own again ("@own").
                    if (!people.TryGetValue(c.Actor, out var v)) break;
                    var arms = Loadouts.Of(g.Journey.Ch).Arms;
                    foreach (var slot in c.Str("slot") is "all" or null ? new[] { "handslot.r", "handslot.l", "forearm.l" } : new[] { c.Str("slot")! })
                    {
                        string? piece = c.Str("piece") switch
                        {
                            "@own" => slot switch { "handslot.l" => arms.Left, "forearm.l" => arms.Forearm, _ => arms.Right },
                            var s => s,
                        };
                        v.Hold(slot, null, piece);
                    }
                    break;
                }
                case "prop":
                {
                    // A thing set down for the scene: her weapon leaning on the log (an Arms "piece"), or any
                    // GLB/scene by "scene": "res://..." (the letter, the dropped lamp), on the world's layer 1.
                    var arms = Loadouts.Of(g.Journey.Ch).Arms;
                    string? piece = c.Str("piece") switch { "@weapon" => arms.Right ?? arms.Left, "@shield" => arms.Forearm, var s => s };
                    string? scenePath = c.Str("scene");
                    string name = c.Str("name") ?? piece ?? scenePath ?? "prop";
                    if (props.Remove(name, out var old)) old.QueueFree();
                    if (c.Bool("remove")) break;
                    Node3D node;
                    if (scenePath != null)
                    {
                        if (GD.Load<PackedScene>(scenePath) is not PackedScene ps || ps.Instantiate() is not Node3D sn)
                        {
                            GD.PushWarning($"cinema prop: no scene at {scenePath}");
                            break;
                        }
                        node = sn;
                        WorldLayer(node);
                    }
                    else if (piece == null || !Arms.All.ContainsKey(piece)) break;
                    else node = Arms.Make(piece);
                    var at = places.Resolve(c.Get("where"));
                    node.Position = V(at);
                    var r = c.Get("rot");
                    if (r.ValueKind == JsonValueKind.Array) node.RotationDegrees = new Vector3((float)r[0].GetDouble(), (float)r[1].GetDouble(), (float)r[2].GetDouble());
                    node.Scale = Vector3.One * (float)c.Num("scale", 1);
                    g.scene!.AddChild(node);
                    props[name] = node;
                    break;
                }
                case "prints":
                {
                    // Wet bootprints along a line, left and right in turn (ground decals until the zone has its own).
                    var a = places.Resolve(c.Get("from"));
                    var z = places.Resolve(c.Get("to"));
                    double stride = c.Num("stride", 0.78), len = (z - a).Length;
                    var dir = (z - a).Unit;
                    var side = new V3(-dir.Z, 0, dir.X);
                    float yaw = Mathf.Atan2((float)dir.X, (float)dir.Z);
                    int n = (int)(len / stride);
                    for (int i = 0; i <= n; i++)
                    {
                        var p = a + dir * (i * stride) + side * ((i % 2 == 0 ? 1 : -1) * 0.12);
                        // Dark and wet against the frost: sorted over it, and glossy enough to take the moon.
                        var d = new Decal
                        {
                            TextureAlbedo = Footprint(i % 2 == 0), TextureOrm = WetOrm(), Size = new Vector3(0.15f, 1.2f, 0.34f),
                            Position = new Vector3((float)p.X, (float)g.scene!.HeightAt(p.X, p.Z) + 0.1f, (float)p.Z),
                            Rotation = new Vector3(0, yaw + Mathf.Pi, 0), AlbedoMix = (float)c.Num("dark", 0.85), CullMask = 1, SortingOffset = 1,
                        };
                        g.scene.AddChild(d);
                        prints.Add(d);
                        // Where the boot came down the frost is knocked off the grass: a soft dark
                        // patch round each print, so the trail reads from far off as a line through it.
                        var t = new Decal
                        {
                            TextureAlbedo = Trampled(), Size = new Vector3(0.34f, 1.2f, 0.62f),
                            Position = d.Position, Rotation = d.Rotation, AlbedoMix = 0.55f, CullMask = 1, SortingOffset = 0.5f,
                        };
                        g.scene.AddChild(t);
                        prints.Add(t);
                    }
                    break;
                }
                case "frost":
                {
                    if (Args.Has("cine-nofrost")) break;   // (pictures: the frost left out, env E2's fog A/B)
                    // Frost on the ground about a place, thin and patchy, and none within a fire's
                    // reach: the prints show dark in it. It stays, as the prints do.
                    // Laid in tiles, each on its own ground and only knee-deep, so it
                    // whitens the grass and the earth and never the trees.
                    var at = places.Resolve(c.Get("where"));
                    float size = (float)c.Num("size", 40), rad = (float)c.Num("radius", 3);
                    Vector2? hole = c.Has("clear") && places.Resolve(c.Get("clear")) is V3 h ? new Vector2((float)h.X, (float)h.Z) : null;
                    // "trail": the places someone walked through it; the frost is knocked off the
                    // grass along it, so the way they came reads as a dark line from far off.
                    var trail = new List<Vector2>();
                    if (c.Get("trail") is { ValueKind: JsonValueKind.Array } tr)
                        foreach (var e in tr.EnumerateArray()) { var q = places.Resolve(e); trail.Add(new Vector2((float)q.X, (float)q.Z)); }
                    int n = Math.Max(1, (int)Math.Ceiling(size / 6));
                    float tile = size / n;
                    for (int i = 0; i < n; i++)
                        for (int j = 0; j < n; j++)
                        {
                            float x0 = (float)at.X - size / 2 + i * tile, z0 = (float)at.Z - size / 2 + j * tile;
                            float cx = x0 + tile / 2, cz = z0 + tile / 2;
                            // The box spans the tile's own rise and fall: one height from its centre left
                            // the ground on a slope outside the box, and the frost stopped on a straight
                            // line along the tile's edge (square seams from the play camera).
                            // Each tile reaches FrostSeam past its edges and fades out over its
                            // neighbour's, the two summing to one: a hard border between tiles drew
                            // a grid of thin lines across the frost.
                            float ext = tile + 2 * FrostSeam, ex0 = x0 - FrostSeam, ez0 = z0 - FrostSeam;
                            float lo = float.MaxValue, hi = float.MinValue;
                            for (int u = 0; u <= 4; u++)
                                for (int w = 0; w <= 4; w++)
                                {
                                    float hgt = (float)g.scene!.HeightAt(ex0 + ext * u / 4, ez0 + ext * w / 4);
                                    lo = Math.Min(lo, hgt); hi = Math.Max(hi, hgt);
                                }
                            var d = new Decal
                            {
                                TextureAlbedo = Frost(new Vector2(ex0, ez0), ext, new Vector2((float)at.X, (float)at.Z), size, hole, rad, trail),
                                Size = new Vector3(ext, hi - lo + 1.4f, ext), Position = new Vector3(cx, (lo + hi) / 2 + 0.35f, cz),
                                AlbedoMix = (float)c.Num("amount", 0.4), CullMask = 1, UpperFade = 0.1f, LowerFade = 0.1f,
                            };
                            g.scene.AddChild(d);
                            prints.Add(d);
                            frost.Add(d);
                        }
                    break;
                }
                case "rig":
                {
                    // A shot's own light on the cast, as a film crew sets one (face 30: dead eyes
                    // with no light into the sockets, an unlit crown): a soft spot on the people's
                    // layer only, no shadow, from "from" ({"lens": [right, up, back]} in the
                    // camera's frame, or a place) onto "aim" (a place, a bone tracked), "range", "energy"
                    // faded in "over". It lasts its shot unless "hold"; "energy": 0 takes it down.
                    string name = c.Str("name") ?? "rig";
                    // ("fade": true: from the light's energy now to "energy" over "over", 0 included: C03 s8y, the heart's
                    // blue from below dying as it goes under, not cut off)
                    float e0 = 0;
                    if (rigs.Remove(name, out var was)) { e0 = was.E; was.Free(); }
                    float e = (float)c.Num("energy", 0.3);
                    bool fade = c.Bool("fade") && over > 0 && !skipping;
                    if (!fade) e0 = 0;
                    if (e <= 0 && !(fade && e0 > 0)) break;
                    var l = new SpotLight3D
                    {
                        Name = "Rig_" + name, LightColor = new Color(c.Str("color") ?? "#fff3e6"), SpotAngle = (float)c.Num("angle", 14),
                        SpotAttenuation = (float)c.Num("falloff", 0.4), ShadowEnabled = false, LightCullMask = 2 | PlayerView.CastLayer,
                        LightSpecular = (float)c.Num("spec", 0.3), LightEnergy = over > 0 && !skipping ? e0 : e, SpotRange = (float)c.Num("range", 5),
                    };
                    g.scene!.AddChild(l);
                    var rig = new Rig(l, c.Get("from").Clone(), c.Get("aim").Clone(), c.Bool("hold") ? -1 : tc.Shot.Index, l.LightEnergy);
                    rigs[name] = rig;
                    // (its authored energy: HerLight sets the light's own from it each frame, Face 48)
                    if (over > 0 && !skipping) tweens.Add(new Tween(t0, t0 + over, k => { rig.E = Mathf.Lerp(e0, e, (float)k); }));
                    PlaceRigs();
                    HerLight();
                    break;
                }
                case "skin":
                {
                    // Her skin's share of the sky's light, for the cinematic (1 as built; play's given back at its end): a scene whose
                    // key is a shot's own rig takes her off the blue ambient (C03, judge r1: cyan from s7 to s10 under the night's fill).
                    // "ear": her ears' warm shade, 1 as built (a warm ear against her cheek once the key is the rig).
                    skinSky = (float)c.Num("sky", skinSky);
                    skinEar = (float)c.Num("ear", skinEar);
                    if (people.TryGetValue("her", out var hs)) { SurvivorUnchained.View.People.HerSkyShare(hs.Person, skinSky); SurvivorUnchained.View.People.HerEarWarmth(hs.Person, skinEar); }
                    break;
                }
                case "glow":
                {
                    // A light seen far off (the ford's lamps from the camp, one lamp high up the
                    // road): a point of its colour and a halo, for this cinematic only. "clear"
                    // carries it through the mist; without it the air takes it as it takes all else.
                    string name = c.Str("name") ?? $"glow{props.Count}";
                    // "out": the flame is put out and the lamp stays, a thread of smoke going up from it.
                    if (c.Bool("out"))
                    {
                        if (props.TryGetValue(name, out var lit) && lit.GetNodeOrNull<Node3D>("Flame") is { } fl)
                        {
                            var smoke = Smoke(fl.GlobalPosition, (float)c.Num("smoke", 1.6), new Color(c.Str("smokeColor") ?? "#78746f"));
                            fl.QueueFree();
                            g.scene!.AddChild(smoke);
                            if (props.Remove(name + ".smoke", out var was)) was.QueueFree();
                            props[name + ".smoke"] = smoke;
                        }
                        break;
                    }
                    if (props.Remove(name, out var old)) old.QueueFree();
                    if (c.Bool("remove")) break;
                    var col = new Color(c.Str("color") ?? "#ffcf80");
                    float size = (float)c.Num("size", 0.3), energy = (float)c.Num("energy", 3);
                    bool clear = c.Bool("clear");
                    var root = new Node3D { Position = V(places.Resolve(c.Get("where"))) };
                    var fire = new Node3D { Name = "Flame" };
                    root.AddChild(fire);
                    // "lantern": the keeper's lamp-iron about the flame, at that scale (the
                    // tower's window lamp): the place is the flame's, the iron is built round it.
                    if (c.Has("lantern"))
                    {
                        float ls = (float)c.Num("lantern", 2);
                        var iron = LampIron.Make();
                        iron.Scale = Vector3.One * ls;
                        iron.Position = new Vector3(0, -LampIron.FlameY * ls, 0);
                        iron.RotationDegrees = new Vector3(0, (float)c.Num("turn", 0), 0);
                        root.AddChild(iron);
                    }
                    var lin = col.SrgbToLinear() * energy;
                    fire.AddChild(new MeshInstance3D
                    {
                        // In a lamp it is a flame, taller than it is wide.
                        Mesh = new SphereMesh { Radius = size, Height = size * (c.Has("lantern") ? 3.4f : 2), RadialSegments = 12, Rings = 6 },
                        CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                        MaterialOverride = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(lin.R, lin.G, lin.B), DisableFog = clear },
                    });
                    // "soft": the halo fades with no rim (a gaussian, not the cone's ramp: a far lamp's glow
                    // in the air, not a small moon); "ontop": it is drawn over what stands before the lamp
                    // (the keep it burns on), as the eye sees a light's glare spill over its own stones.
                    fire.AddChild(new MeshInstance3D
                    {
                        Mesh = new QuadMesh { Size = Vector2.One * size * (float)c.Num("spread", 9) },
                        CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                        MaterialOverride = new StandardMaterial3D
                        {
                            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
                            BlendMode = BaseMaterial3D.BlendModeEnum.Add, BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
                            AlbedoTexture = c.Bool("soft") ? SoftHalo() : Halo(), AlbedoColor = new Color(col.R, col.G, col.B, (float)c.Num("halo", 0.55)), DisableFog = clear,
                            NoDepthTest = c.Bool("ontop"),
                        },
                    });
                    // "light": it lights what is near it too (a lamp held to a face), within "range".
                    if (c.Has("light"))
                        fire.AddChild(new OmniLight3D { LightColor = col, LightEnergy = (float)c.Num("light"), OmniRange = (float)c.Num("range", 4), OmniAttenuation = 1.4f, LightSpecular = (float)c.Num("spec", 0.5) });
                    // "under": [width, height], the dark of what the light is set in (a tower against the sky).
                    if (c.Get("under") is { ValueKind: JsonValueKind.Array } u)
                    {
                        float uw = (float)u[0].GetDouble(), uh = (float)u[1].GetDouble();
                        root.AddChild(new MeshInstance3D
                        {
                            Mesh = new BoxMesh { Size = new Vector3(uw, uh, uw) }, Position = new Vector3(0, -uh / 2 - size, 0),
                            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                            MaterialOverride = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(c.Str("dark") ?? "#05070c") },
                        });
                    }
                    g.scene!.AddChild(root);
                    props[name] = root;
                    break;
                }
                case "mist":
                {
                    // Mist lying low on the ground or the water for the scene (the ford, the frost past the
                    // firelight): a fog volume "size" [w, h, d] metres about "where", thickest at its foot
                    // ("falloff"), lit by what lights the air. Without "where" the one of that name thins or
                    // thickens to "density" over "over" (gone with the scene, so faded out before play).
                    string name = "mist." + (c.Str("name") ?? "mist");
                    if (!c.Has("where"))
                    {
                        if (props.TryGetValue(name, out var mv) && mv is FogVolume { Material: FogMaterial fm })
                        {
                            float from = fm.Density, to = (float)c.Num("density");
                            if (over > 0 && !skipping) tweens.Add(new Tween(t0, t0 + over, k => fm.Density = Mathf.Lerp(from, to, (float)k)));
                            else fm.Density = to;
                        }
                        break;
                    }
                    if (props.Remove(name, out var oldMist)) oldMist.QueueFree();
                    var sz = c.Get("size");
                    var size = sz.ValueKind == JsonValueKind.Array ? new Vector3((float)sz[0].GetDouble(), (float)sz[1].GetDouble(), (float)sz[2].GetDouble()) : new Vector3(40, 1.2f, 40);
                    var noise = new FastNoiseLite { NoiseType = FastNoiseLite.NoiseTypeEnum.Perlin, Frequency = (float)c.Num("grain", 0.08), FractalOctaves = 3 };
                    var mat = new FogMaterial
                    {
                        Density = (float)c.Num("density", 0.5), Albedo = new Color(c.Str("color") ?? "#9aa8bc"), HeightFalloff = (float)c.Num("falloff", 2),
                        EdgeFade = (float)c.Num("edge", 0.5), DensityTexture = new NoiseTexture3D { Width = 64, Height = 8, Depth = 64, Seamless = true, Noise = noise, Normalize = true },
                    };
                    var foot = V(places.Resolve(c.Get("where")));
                    var vol = new FogVolume
                    {
                        Name = "Mist", Shape = RenderingServer.FogVolumeShape.Box, Size = size, Material = mat,
                        Position = foot + new Vector3(0, size.Y * 0.5f - (float)c.Num("sink", 0.2), 0),
                    };
                    g.scene!.AddChild(vol);
                    props[name] = vol;
                    break;
                }
                case "globe":
                {
                    // A zone lamp's glowing piece dimmed to "level" of its own (faded over "over"), for this
                    // cinematic only (the ford's post globes, flat eggs that clip in a close or long lens, until
                    // their flames are made); its light is left as it is. Put back as it was when the cinematic ends.
                    var gmeta = g.scene!.View.Data.Meta.Lights;
                    int gli = (int)c.Num("light");
                    if (gli < 0 || gli >= gmeta.Count) break;
                    float glv = (float)c.Num("level", 1);
                    // "color": the hue it glows in (hex), its own brightness kept (the brightest channel),
                    // so "level" still scales that (the ford's lamps blue in a long lens, not cream eggs).
                    Color? gtint = c.Str("color") is string ghex ? new Color(ghex).SrgbToLinear() : null;
                    foreach (var gname in gmeta[gli].Glow)
                    {
                        if (g.scene.View.Node(gname) is not Node3D gnode) continue;
                        var gms = gnode.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>().ToList();
                        if (gnode is MeshInstance3D gself) gms.Add(gself);
                        foreach (var gmi in gms)
                            for (int gsi = 0; gmi.Mesh != null && gsi < gmi.Mesh.GetSurfaceCount(); gsi++)
                            {
                                var gl = globes.Find(x => x.M == gmi && x.S == gsi);
                                if (gl == null)
                                {
                                    var gwas = gmi.GetSurfaceOverrideMaterial(gsi);
                                    if ((gwas ?? gmi.Mesh.SurfaceGetMaterial(gsi)) is not ShaderMaterial gsm || gsm.GetShaderParameter("color").VariantType != Godot.Variant.Type.Vector3) continue;
                                    gl = new Globe(gmi, gsi, gwas, (ShaderMaterial)gsm.Duplicate(), (Vector3)gsm.GetShaderParameter("color"));
                                    gmi.SetSurfaceOverrideMaterial(gsi, gl.Dim);
                                    globes.Add(gl);
                                }
                                var gg = gl;
                                if (gtint is Color gt && Mathf.Max(gt.R, Mathf.Max(gt.G, gt.B)) > 1e-4f)
                                    gg.Tint = new Vector3(gt.R, gt.G, gt.B) * (Mathf.Max(gg.Base.X, Mathf.Max(gg.Base.Y, gg.Base.Z)) / Mathf.Max(gt.R, Mathf.Max(gt.G, gt.B)));
                                float gfrom = gg.Level;
                                void SetG(float l) { gg.Level = l; gg.Dim.SetShaderParameter("color", (gg.Tint ?? gg.Base) * l); }
                                if (over > 0 && !skipping) tweens.Add(new Tween(t0, t0 + over, k => SetG(Mathf.Lerp(gfrom, glv, (float)k))));
                                else SetG(glv);
                            }
                        // "halo": a soft glow about the globe (its strength; 0 takes it away), "spread" metres across,
                        // in "color" (or the ford's blue): flame-lit glass, not a flat egg. It sits a little toward the lens.
                        if (!c.Has("halo")) continue;
                        string hk = $"globehalo.{gli}.{gname}";
                        if (props.Remove(hk, out var ohalo)) { globeHalos.RemoveAll(x => x.Q == ohalo); ohalo.QueueFree(); }
                        float ha = (float)c.Num("halo");
                        if (ha <= 0 || gms.Count == 0) continue;
                        var hbox = gms[0].GlobalTransform * gms[0].GetAabb();
                        foreach (var hm in gms) hbox = hbox.Merge(hm.GlobalTransform * hm.GetAabb());
                        var hcol = new Color(c.Str("color") ?? "#8ac8ff");
                        var hquad = new MeshInstance3D
                        {
                            Mesh = new QuadMesh { Size = Vector2.One * (float)c.Num("spread", 1.2) },
                            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                            MaterialOverride = new StandardMaterial3D
                            {
                                ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
                                BlendMode = BaseMaterial3D.BlendModeEnum.Add, BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
                                AlbedoTexture = Halo(), AlbedoColor = new Color(hcol.R, hcol.G, hcol.B, ha), DisableFog = true,
                            },
                        };
                        g.scene.AddChild(hquad);
                        var hat = hbox.GetCenter();
                        float hr = hbox.Size.Length() * 0.5f + 0.05f;
                        hquad.GlobalPosition = hat;
                        props[hk] = hquad;
                        globeHalos.Add((hquad, hat, hr));
                    }
                    break;
                }
                case "haze":
                {
                    // The far haze (Atmosphere.Haze): "begin"/"end" m, "curve", "amount" (0-1), "sky" (0-1, the sky's colour
                    // in it); "off" back to play's fog. Finish takes it off.
                    g.air.Haze = c.Bool("off") ? null : ((float)c.Num("begin", 40), (float)c.Num("end", 160), (float)c.Num("curve", 1), (float)c.Num("amount", 0.8), (float)c.Num("sky", 1), c.Str("color") is string hc ? new Color(hc) : null);
                    break;
                }
                case "water":
                {
                    // The river's light, all of it, scaled for this cinematic ("level" 1 as built; 0.4 about
                    // a stop and a third down: the ford's water was the brightest broad thing at night),
                    // faded over "over"; put back as built when the cinematic ends.
                    // ("foam": the foam's amount, a share of as built, held from this shot on: C03 s8's close stone
                    // ringed too white beside her face; put back as built when the cinematic ends too)
                    float wto = (float)c.Num("level", 1);
                    bool hasLevel = c.Has("level");
                    foreach (var wmi in g.scene!.View.FindChildren("*", "MeshInstance3D", true, false).OfType<MeshInstance3D>())
                    {
                        if (wmi.MaterialOverride is not ShaderMaterial wsm || wsm.Shader?.ResourcePath.EndsWith("water.gdshader") != true) continue;
                        waters.Add(wsm);
                        if (c.Has("foam"))
                        {
                            if (!waterFoam.ContainsKey(wsm)) waterFoam[wsm] = wsm.GetShaderParameter("foam_amt").VariantType == Godot.Variant.Type.Float ? (float)wsm.GetShaderParameter("foam_amt") : 1f;
                            wsm.SetShaderParameter("foam_amt", waterFoam[wsm] * (float)c.Num("foam", 1));
                        }
                        // ("streak": the lamps' streaks on the water, a share, held from this shot on: C03 s8's far lamp
                        // laid a cyan column beside the heart in the heart's own colour; 1 back as built, as is the end)
                        if (c.Has("streak")) wsm.SetShaderParameter("streak_shot", (float)c.Num("streak", 1));
                        // ("mirror_cap": the brightest the grazing mirror shows a thing (linear, its brightest channel), for this
                        // shot on: C03 s8's far ford lamp mirrored as a cyan column beside the heart; MIRROR_CAP=v tries a value)
                        if (c.Has("mirror_cap")) wsm.SetShaderParameter("mirror_cap", System.Environment.GetEnvironmentVariable("MIRROR_CAP") is { } mcs && c.Num("mirror_cap", 100) < 100 ? float.Parse(mcs, System.Globalization.CultureInfo.InvariantCulture) : (float)c.Num("mirror_cap", 100));
                        if (!hasLevel) continue;
                        float wfrom = wsm.GetShaderParameter("level").VariantType == Godot.Variant.Type.Float ? (float)wsm.GetShaderParameter("level") : 1f;
                        if (over > 0 && !skipping) tweens.Add(new Tween(t0, t0 + over, k => wsm.SetShaderParameter("level", Mathf.Lerp(wfrom, wto, (float)k))));
                        else wsm.SetShaderParameter("level", wto);
                    }
                    break;
                }
                case "stones":
                {
                    // The stepping stones' damp tops for this shot on ("top": their light, a share; 1 as built): C03 s8's near
                    // stone crown, out of focus beside her, the palest broad thing after her. Put back as the cinematic ends.
                    stonesSet = true;
                    // (STONE_TOP=v tries a value over the cue's, numbers first)
                    float top = System.Environment.GetEnvironmentVariable("STONE_TOP") is { } stt && float.TryParse(stt, System.Globalization.CultureInfo.InvariantCulture, out var stv) && c.Num("top", 1) < 1 ? stv : (float)c.Num("top", 1);
                    var sset = c.Bool("all") ? KitLook.Rocks : KitLook.Stepping;
                    // ("edge": their worn rims' light, a share of as built: s8's out-of-focus stone rim read as a pale crown)
                    if (c.Has("edge"))
                        foreach (var sm in sset)
                        {
                            if (!IsInstanceValid(sm)) continue;
                            if (!stoneEdge.ContainsKey(sm)) stoneEdge[sm] = (float)sm.GetShaderParameter("edge_light");
                            sm.SetShaderParameter("edge_light", stoneEdge[sm] * (float)c.Num("edge", 1));
                            (sm.NextPass as ShaderMaterial)?.SetShaderParameter("edge_light", stoneEdge[sm] * (float)c.Num("edge", 1));
                        }
                    foreach (var sm in sset) if (IsInstanceValid(sm)) { sm.SetShaderParameter("top_level", top); (sm.NextPass as ShaderMaterial)?.SetShaderParameter("top_level", top); }
                    if (System.Environment.GetEnvironmentVariable("CAUSEWAY_STATS") != null) GD.Print($"STONES cue: top {top} on {sset.Count} materials");
                    break;
                }
                case "grade":
                {
                    // One shot's colour grade: "sat" (1 as built) is the saturation the world eases to over
                    // "over", or cuts to without it. A fire-lit close-up's skin goes over-saturated at a
                    // 2700 K key, so that shot pulls it down and the next shot's first cue sets sat 1 again;
                    // the cinematic's end hands it back to play (the lerp in Game.cs eases to 1).
                    // Its palette too, for the cinematic (play's own given back at its end): "moonSat", "moonHue", "moonDrop", "moonTop",
                    // "moonWidth" (the grade's moon step: what it lays on the weakly coloured, and up to what lightness, as GradeSettings has it), "shade" and "shadeK" (the
                    // paint grade's colour for the darks), "shadowTint", "hiTint", "vib". (C03's night, judge r1: the moon, the lamps,
                    // the ambient and the heart one blue, so the heart wasn't special: the moon silver, the shade violet.)
                    if (new[] { "moonSat", "moonHue", "moonDrop", "moonTop", "moonWidth", "shade", "shadeK", "shadowTint", "hiTint", "vib" }.Any(c.Has))
                    {
                        double? Opt(string k) => c.Has(k) ? c.Num(k) : null;
                        double? ms = Opt("moonSat"), mh = Opt("moonHue"), md = Opt("moonDrop"), mt = Opt("moonTop"), mw = Opt("moonWidth"), sk = Opt("shadeK"), vb = Opt("vib");
                        string? sh = c.Str("shade"), st = c.Str("shadowTint"), ht = c.Str("hiTint");
                        g.air.SetCineGrade(gs => gs with
                        {
                            MoonSat = ms ?? gs.MoonSat, MoonHue = mh ?? gs.MoonHue, MoonDrop = md ?? gs.MoonDrop, MoonTop = mt ?? gs.MoonTop, MoonWidth = mw ?? gs.MoonWidth,
                            PaintShadow = sh ?? gs.PaintShadow, PaintShadowK = sk ?? gs.PaintShadowK, PaintVib = vb ?? gs.PaintVib,
                            ShadowTint = st ?? gs.ShadowTint, HighlightTint = ht ?? gs.HighlightTint,
                        });
                    }
                    double gsat = c.Num("sat", 1);
                    double gfrom = g.cineSat ?? 1;
                    if (over > 0 && !skipping) tweens.Add(new Tween(t0, t0 + over, k => { g.cineSat = gfrom + (gsat - gfrom) * k; }));
                    else { g.cineSat = gsat; g.air.Env.AdjustmentSaturation = (float)gsat; }
                    break;
                }
                case "bars" or "fade" or "wet":
                    // The bars and black follow the shots; wetness waits on its system (docs/cinematics/README.md section 6, 7).
                    break;
            }
        }

        readonly Dictionary<string, Node3D> props = new();

        /// <summary>A "prop" cue's scene on the world's visual layer 1 (the zone's light, decals and shadows), all through.</summary>
        static void WorldLayer(Node n)
        {
            if (n is VisualInstance3D vi) vi.Layers = 1;
            foreach (var ch in n.GetChildren()) WorldLayer(ch);
        }
        static GradientTexture2D? halo;

        /// <summary>A preset as a scene lights it (its night darker than play's, a close-up's own exposure): "key",
        /// "hemi", "env", "exposure", "fog" and "rim" scale the preset's own; "azimuth" and "elevation" (degrees)
        /// move the moon or sun for the shot; "keyColor", "fogColor", "hemiSky", "hemiGround" and "rimColor" replace its colours.</summary>
        /// <summary>An "atmosphere" cue's air, where it goes and where from (null: set at once), as the cue reads now.</summary>
        (AtmospherePreset To, AtmospherePreset? From) AirOf(CineCue c)
        {
            // A blend of a part of the way, "k0" to "k1" (a dawn begun in one
            // cinematic and finished in the next); a skip lands on k1. "from": "now"
            // blends from the air as it is (a scene's own night back into play's).
            // "play": the zone's own air for the time it is (the hand-back into play's look).
            var to = Tuned(c.Str("preset") switch
            {
                "now" => g.air.Current,
                "play" when g.zone != null => g.zone.AtmosphereFor(g.zone.TimeOf(g.World)),
                // "playdawn": the zone's own dawn, the air play will take up at a dawn hand-back
                // (C04 A: the dawn comes up under its lines, not a night with stars; play-1).
                "playdawn" when g.zone != null => g.zone.AtmosphereFor(TimeOfDay.Dawn),
                var n => Atmospheres.ByName(n == "play" ? "night" : n!),
            }, c);
            if (c.Str("from") is not string fromName) return (to, null);
            var src = fromName == "now" ? g.air.Current : Atmospheres.ByName(fromName);
            // The hand-back (E1): play's key direction is taken on the cue's first frame, the cut into the
            // hand-back shot, and only the light's strength and colour blend. Blended, the moon swung 122
            // degrees over C01's 3.2 s, its shadows wheeling round her (the 18 October "jarring spin").
            if (c.Str("preset") is "play" or "playdawn") src = src with { KeyAzimuth = to.KeyAzimuth, KeyElevation = to.KeyElevation };
            return (to, src);
        }

        /// <summary>The frost's thaw baked ahead, on a worker, for each sun this cinematic and the one it runs on into
        /// set as their atmosphere cues begin (GroundPaint.SunAhead): C04 A's dawn baked it on the main thread as it
        /// came up, 2.4 s.</summary>
        void SunAhead()
        {
            var files = new List<CineFile> { file };
            if (file.End.Next is string next) try { files.Add(CineFile.Load(next)); } catch (Exception) { }
            foreach (var f in files)
                foreach (var shot in f.Shots)
                    foreach (var c in shot.Cues)
                    {
                        if (c.Do != "atmosphere") continue;
                        var (to, src) = AirOf(c);
                        double k0 = c.Num("k0"), k1 = c.Num("k1", 1);
                        AtmospherePreset[] airs = src is not { } fr ? [to] : c.Num("over") > 0
                            ? new[] { Atmospheres.Blend(fr, to, k0), Atmospheres.Blend(fr, to, k1) }
                            : [k1 >= 1 ? to : Atmospheres.Blend(fr, to, k1)];
                        foreach (var p in airs)
                            if (Atmosphere.ThawSun(p) is Vector3 dir) GroundPaint.SunAhead(dir);
                    }
        }

        static AtmospherePreset Tuned(AtmospherePreset p, CineCue c) => p with
        {
            KeyIntensity = p.KeyIntensity * c.Num("key", 1), HemiIntensity = p.HemiIntensity * c.Num("hemi", 1),
            EnvIntensity = p.EnvIntensity * c.Num("env", 1), Exposure = p.Exposure * c.Num("exposure", 1),
            FogDensity = p.FogDensity * c.Num("fog", 1), RimStrength = p.RimStrength * c.Num("rim", 1),
            KeyAzimuth = c.Has("azimuth") ? c.Num("azimuth") : p.KeyAzimuth, KeyElevation = c.Has("elevation") ? c.Num("elevation") : p.KeyElevation,
            KeyColor = c.Str("keyColor") ?? p.KeyColor, FogColor = c.Str("fogColor") ?? p.FogColor,
            HemiSky = c.Str("hemiSky") ?? p.HemiSky, HemiGround = c.Str("hemiGround") ?? p.HemiGround, Rim = c.Str("rimColor") ?? p.Rim,
            Sky = c.Has("skySat") ? SkySat(p.Sky, c.Num("skySat")) : p.Sky,
        };

        /// <summary>A sky's colours taken toward their own grey ("skySat" 0.6: 40% of the colour out; 1 as it is),
        /// as a shot of a face against a cobalt night wants; "preset": "now" tunes the air as it is, so a later
        /// cue's 1/0.6 puts it back.</summary>
        static SkySettings SkySat(SkySettings s, double k)
        {
            string Sat(string hex)
            {
                var col = new Color(hex);
                float l = col.R * 0.2126f + col.G * 0.7152f + col.B * 0.0722f, f = (float)k;
                return "#" + new Color(Mathf.Clamp(l + (col.R - l) * f, 0, 1), Mathf.Clamp(l + (col.G - l) * f, 0, 1), Mathf.Clamp(l + (col.B - l) * f, 0, 1)).ToHtml(false);
            }
            return s with { Top = Sat(s.Top), Horizon = Sat(s.Horizon), Bottom = Sat(s.Bottom), Glow = Sat(s.Glow) };
        }

        /// <summary>A soft round halo, bright at the middle and gone at the edge.</summary>
        static ImageTexture? softHalo;
        /// <summary>A halo with no rim: a narrow bright core in a wide gaussian, both windowed to reach
        /// nothing at the edge with no slope left (E8 s8a: the cone's ramp read as a small moon).</summary>
        static ImageTexture SoftHalo()
        {
            if (softHalo != null) return softHalo;
            const int N = 128;
            var img = Image.CreateEmpty(N, N, true, Image.Format.Rgba8);
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float dx = (x + 0.5f) / N * 2 - 1, dy = (y + 0.5f) / N * 2 - 1, r2 = dx * dx + dy * dy;
                    float win = r2 >= 1 ? 0 : (1 - r2) * (1 - r2);
                    float a = (0.3f * Mathf.Exp(-r2 * 40f) + 0.7f * Mathf.Exp(-r2 * 5f)) * win;
                    img.SetPixel(x, y, new Color(1, 1, 1, a));
                }
            img.GenerateMipmaps();
            return softHalo = ImageTexture.CreateFromImage(img);
        }
        static GradientTexture2D Halo() => halo ??= new GradientTexture2D
        {
            Gradient = new Gradient { Colors = [new Color(1, 1, 1, 1), new Color(1, 1, 1, 0.25f), new Color(1, 1, 1, 0)], Offsets = [0, 0.18f, 1] },
            Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f), Width = 64, Height = 64,
        };
        /// <summary>A thread of smoke from a wick just put out, at the flame's place, for
        /// "seconds"; then it stops coming and the last of it thins away.</summary>
        static GpuParticles3D Smoke(Vector3 at, float seconds, Color col)
        {
            var p = Campfire.WickSmoke(col);
            p.Position = at;
            p.TreeEntered += () => p.GetTree().CreateTimer(seconds).Timeout += () => { if (GodotObject.IsInstanceValid(p)) p.Emitting = false; };
            return p;
        }
        readonly List<Decal> prints = new();
        /// <summary>The frost's tiles: the cinematic's alone. From the play camera its soft patches read as
        /// white fog over the road (the teaching pass, env E2), so it thaws as play is handed back.</summary>
        readonly List<Decal> frost = new();
        static readonly Dictionary<bool, ImageTexture> printTex = new();

        /// <summary>A boot's print, dark and wet: a sole and a heel, soft at the edges.</summary>
        static ImageTexture Footprint(bool left)
        {
            if (printTex.TryGetValue(left, out var t)) return t;
            const int W = 32, H = 96;
            var img = Image.CreateEmpty(W, H, false, Image.Format.Rgba8);
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    float u = (x + 0.5f) / W * 2 - 1, v = (y + 0.5f) / H;
                    // The sole (toe end at the top, turned a little in), then a gap, then the heel.
                    float sole = 1 - ((u - (left ? -0.08f : 0.08f) * (1 - v)) * (u - (left ? -0.08f : 0.08f) * (1 - v)) / 0.8f + (v - 0.3f) * (v - 0.3f) / 0.075f);
                    float heel = 1 - (u * u / 0.62f + (v - 0.8f) * (v - 0.8f) / 0.018f);
                    float a = Mathf.Clamp(Mathf.Max(sole, heel) * 3, 0, 1);
                    img.SetPixel(x, y, new Color(0.03f, 0.035f, 0.04f, a * 0.85f));
                }
            return printTex[left] = ImageTexture.CreateFromImage(img);
        }

        static ImageTexture? trampled;

        /// <summary>A soft dark oval: the ground round a print, the frost knocked off it.</summary>
        static ImageTexture Trampled()
        {
            if (trampled != null) return trampled;
            const int N = 48;
            var img = Image.CreateEmpty(N, N, false, Image.Format.Rgba8);
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float u = (x + 0.5f) / N * 2 - 1, v = (y + 0.5f) / N * 2 - 1;
                    float a = Mathf.Clamp(1 - Mathf.Sqrt(u * u + v * v), 0, 1);
                    img.SetPixel(x, y, new Color(0.10f, 0.11f, 0.12f, a * a * 0.8f));
                }
            return trampled = ImageTexture.CreateFromImage(img);
        }

        static ImageTexture? wetOrm;

        /// <summary>A wet print's surface: smooth (roughness low), so it glints.</summary>
        static ImageTexture WetOrm()
        {
            if (wetOrm != null) return wetOrm;
            var img = Image.CreateEmpty(4, 4, false, Image.Format.Rgba8);
            img.Fill(new Color(1, 0.12f, 0, 1));
            return wetOrm = ImageTexture.CreateFromImage(img);
        }

        static readonly FastNoiseLite frostNoise = new() { Seed = 11, Frequency = 0.3f, FractalOctaves = 4 };

        /// <summary>One tile of frost as a decal's picture (its corner and size in the
        /// world): a thin rime broken by noise, thinning to the patch's edge, and
        /// cleared in a soft ring where a fire keeps it off.</summary>
        const float FrostSeam = 0.3f;

        static ImageTexture Frost(Vector2 corner, float tile, Vector2 centre, float size, Vector2? hole, float radius, List<Vector2> trail)
        {
            const int N = 96;
            var img = Image.CreateEmpty(N, N, false, Image.Format.Rgba8);
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    var uv = new Vector2((x + 0.5f) / N, (y + 0.5f) / N) * tile;
                    var w = corner + uv;
                    float n = frostNoise.GetNoise2D(w.X, w.Y) * 0.5f + 0.5f;
                    float a = Mathf.SmoothStep(0.3f, 0.7f, n);
                    // The cross-fade over the overlap with each neighbour (linear, so the pair sums to one).
                    a *= Mathf.Clamp(Mathf.Min(uv.X, tile - uv.X) / (2 * FrostSeam), 0, 1) * Mathf.Clamp(Mathf.Min(uv.Y, tile - uv.Y) / (2 * FrostSeam), 0, 1);
                    // The patch thins out to a ragged round edge (a square one read as straight
                    // seams from the play camera above): the radius wanders with a slow noise.
                    float r = w.DistanceTo(centre) / (size / 2);
                    float wob = frostNoise.GetNoise2D(w.X * 0.12f + 311f, w.Y * 0.12f - 97f) * 0.22f;
                    a *= Mathf.SmoothStep(0f, 1f, Mathf.Clamp((0.92f + wob - r) / 0.4f, 0, 1));
                    if (hole is Vector2 hc) a *= Mathf.SmoothStep(radius * 0.7f, radius * 1.4f, w.DistanceTo(hc));
                    for (int k = 0; k + 1 < trail.Count; k++)
                    {
                        var ab = trail[k + 1] - trail[k];
                        float s = Mathf.Clamp((w - trail[k]).Dot(ab) / Mathf.Max(ab.LengthSquared(), 1e-4f), 0, 1);
                        a *= Mathf.SmoothStep(0.22f, 0.5f, w.DistanceTo(trail[k] + ab * s));
                    }
                    img.SetPixel(x, y, new Color(0.70f, 0.75f, 0.80f, a));
                }
            return ImageTexture.CreateFromImage(img);
        }

        HerFaceLife? Life(string actor) =>
            people.TryGetValue(actor, out var v) ? v.Person.Skeleton.GetNodeOrNull<HerFaceLife>("HerFaceLife") : null;

        /// <summary>Left or right of the camera, for a sound placed in the world (-1..1).</summary>
        double Pan(V3 at)
        {
            var cam = g.camera.GlobalTransform;
            var rel = cam.Basis.Inverse() * (V(at) - cam.Origin);
            return Math.Clamp(rel.X / Math.Max(1, rel.Length()) * 1.5, -1, 1);
        }

        /* --------------------------------------------------------- the end -- */

        float keyReach = -1;
        readonly HashSet<int> sized = new();

        // Eye-shader values the cinematic changed: the first original of each, put back at the end.
        readonly Dictionary<(ShaderMaterial, string), Godot.Variant> eyeWas = new();
        void SetEye(ShaderMaterial m, string key, Godot.Variant val)
        {
            if (!eyeWas.ContainsKey((m, key))) eyeWas[(m, key)] = m.GetShaderParameter(key);
            m.SetShaderParameter(key, val);
        }

        public void Finish()
        {
            g.cineSat = null;
            if (g.air.CineGrade != null) g.air.SetCineGrade(null);
            if (g.air.Haze != null) g.air.Haze = null;
            if ((skinSky != 1 || skinEar != 1) && people.TryGetValue("her", out var hs))
            { SurvivorUnchained.View.People.HerSkyShare(hs.Person, 1); SurvivorUnchained.View.People.HerEarWarmth(hs.Person, 1); }
            skinSky = 1; skinEar = 1;
            foreach (int i in sized) g.scene?.View.SetSize(i, 0);
            sized.Clear();
            foreach (var ((em, ek), was) in eyeWas) if (IsInstanceValid(em)) em.SetShaderParameter(ek, was);
            eyeWas.Clear();
            if (keyReach > 0) g.air.Key.DirectionalShadowMaxDistance = keyReach;
            // Play starts exactly where the cinematic leaves her, facing as she
            // faces, and still walking if she was (docs/cinematics/README.md, 5a).
            var p = b.Player;
            var pv = g.scene!.Player;
            pv.Still = false;
            if (handed)
            {
                // Her own body already: what she was doing carries on, easing out.
                if (g.cineWalk is { } w) { g.carry = w; g.carryT = CarryFade; }
                g.cineWalk = null;
            }
            else if (file.End.Her is string m)
            {
                var (x, _, z, heading) = file.Mark(m);
                float moving = 0;
                if (!player.Skipped && people.TryGetValue("her", out var her) && her.Visible)
                {
                    // Where her double really is, and its pace (a walk carries on).
                    var at = her.GlobalPosition;
                    x = at.X; z = at.Z; heading = her.Rotation.Y;
                    var v = new Vector2(herVel.X, herVel.Z);
                    if (v.Length() > 0.4f)
                    {
                        moving = v.Length();
                        double top = Math.Max(0.1, b.Stats.Get(Stat.MoveSpeed) * p.SlowF), k = Math.Min(1, moving / top);
                        var dir = v.Normalized();
                        g.carry = (dir.X * k, dir.Y * k);
                        g.carryT = CarryFade;
                    }
                }
                p.X = x; p.Z = z; p.Facing = heading;
                p.Vx = moving > 0 ? herVel.X : 0; p.Vz = moving > 0 ? herVel.Z : 0;
                pv?.Face((float)heading, new Vector3((float)x, (float)g.scene.HeightAt(x, z), (float)z), moving);
            }
            // Her look let go (her eyes ahead, her head's carry eased off) on whoever stays.
            foreach (var name in people.Keys) Life(name)?.Release();
            foreach (var (_, pv2) in people) if (pv2.Person.Pose is { } hp && IsInstanceValid(hp)) hp.CineCurlL = hp.CineCurlR = 0;
            // (and a head look's glide back off: play's Watch is set each frame and follows at once)
            foreach (var (_, v) in people) if (v.Person.Skeleton.GetNodeOrNull<HeadTurn>("HeadTurn") is { } ht) ht.Glide = false;
            // Who stays where it left them (a body in the river) stays, still, until the next one.
            var keep = file.End.Keep ?? new List<string>();
            foreach (var (name, v) in people) if (!bosses.ContainsKey(name)) { if (keep.Contains(name)) g.kept.Add(v); else v.QueueFree(); }
            foreach (var (name, w) in bosses) { if (keep.Contains(name)) g.kept.Add(w); else w.QueueFree(); }
            foreach (var o in orbs.Values) o.QueueFree();
            bosses.Clear(); orbs.Clear(); groups.Clear(); later.Clear();
            foreach (var n in props.Values) n.QueueFree();
            props.Clear();
            foreach (var r in rigs.Values) r.Free();
            rigs.Clear();
            HerLightEnd();
            foreach (var gl in globes) if (IsInstanceValid(gl.M)) gl.M.SetSurfaceOverrideMaterial(gl.S, gl.Was);
            globes.Clear();
            foreach (var wsm in waters) { wsm.SetShaderParameter("level", 1f); wsm.SetShaderParameter("streak_shot", 1f); wsm.SetShaderParameter("mirror_cap", 100f); }
            foreach (var (wsm, wf) in waterFoam) wsm.SetShaderParameter("foam_amt", wf);
            waters.Clear();
            waterFoam.Clear();
            if (stonesSet) foreach (var sm in KitLook.Rocks) if (IsInstanceValid(sm)) { sm.SetShaderParameter("top_level", 1f); (sm.NextPass as ShaderMaterial)?.SetShaderParameter("top_level", 1f); }
            foreach (var (sm, se) in stoneEdge) if (IsInstanceValid(sm)) { sm.SetShaderParameter("edge_light", se); (sm.NextPass as ShaderMaterial)?.SetShaderParameter("edge_light", se); }
            stoneEdge.Clear();
            stonesSet = false;
            // Her prints stay: they are in the frost whether it played or not.
            // The decals' frost goes as play takes over (under a second): the ground's own frost, by exposure, carries it
            // from here (judge 1, E3 fix 3: the decals were the brightest ground in the hand-back's frame).
            foreach (var fd in frost)
                if (IsInstanceValid(fd))
                {
                    var tw = fd.CreateTween();
                    tw.TweenProperty(fd, "albedo_mix", 0f, Args.Num("cine-thaw", 0.3f));
                    tw.TweenCallback(Callable.From(fd.QueueFree));
                }
            frost.Clear();
            people.Clear();
            if (file.End.Next != null)
            {
                // On into the next on the cut: the zone starts it from done; if it
                // does not, play is handed back here as usual.
                g.chained = new Chain(bars, saved);
                Seen();
                done?.Invoke();
                if (g.chained != null) { g.chained = null; Restore(); }
                return;
            }
            Restore();
            Seen();
            done?.Invoke();
        }

        void Seen()
        {
            if (!Settings.Current.SeenCinematics.Contains(file.Id)) { Settings.Current.SeenCinematics.Add(file.Id); Settings.Current.Save(); }
            GD.Print($"cinema: {file.Id} {(player.Skipped ? "skipped" : "done")}");
        }

        void Restore()
        {
            var p = b.Player;
            var cam = g.camera;
            cam.Fov = saved.Fov; cam.KeepAspect = saved.Keep; cam.Near = saved.Near; cam.Attributes = saved.Attr;
            Campfire.ClearNear(0);
            CrowdView.Staged = null;
            g.scene!.CameraHeld = false;
            if (g.scene.Player != null) g.scene.Player.Hidden = false;
            g.cam.Snap((float)p.X, (float)g.scene.HeightAt(p.X, p.Z), (float)p.Z);
            b.WorldRate = 1; b.WorldRateT = 0;
            g.sound.CineMood = null;
            g.controls.Captured = false;
            g.controls.ClearLatches();
            if (!hudIn) g.hud.ShowPlay(true, player.Skipped ? 0.3f : 0.6f);
            bars.QueueFree();
        }
    }
}
