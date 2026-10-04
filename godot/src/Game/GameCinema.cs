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

    /// <summary>A cinematic from the data, played now in the zone that is
    /// running; done when it hands back (or is skipped). False if it cannot
    /// play here (no scene, no such file), and the zone does without.</summary>
    public bool Cinematic(string id, Action? done = null, IReadOnlyDictionary<string, double[]>? marks = null)
    {
        if (scene?.Battle is not { } b || cine != null) return false;
        // --nocine, or a quick start: the zone's captions instead (pictures of play from the first frame).
        if (Args.Has("nocine") || (quick && Args.Get("cine") != id)) return false;
        CineFile file;
        try { file = CineFile.Load(id); }
        catch (Exception e) { GD.PushWarning($"cinema: {id} not played ({e.Message})"); return false; }
        // Where things really are (a boss falls where the fight leaves him).
        if (marks != null) foreach (var (k, v) in marks) file.Marks[k] = v.ToArray();
        // A timeline that cannot be laid out is not played (its schedule is built
        // before anything on screen changes), and the zone does without.
        try { cine = new Cine(this, file, b, done); }
        catch (Exception e) { GD.PushError($"cinema: {id} not played: {e.Message}"); cine = null; return false; }
        return true;
    }

    public bool CanCinematic(string id) =>
        scene?.Battle != null && cine == null && !Args.Has("nocine") && !(quick && Args.Get("cine") != id)
        && FileAccess.FileExists($"res://data/cinematics/{id}.json");

    /// <summary>Each frame, after the world is drawn: the camera, the cast, the cues.</summary>
    void CinemaFrame(double dt)
    {
        if (cine == null) return;
        cine.Frame(dt);
        if (cine.Over) { var c = cine; cine = null; c.Finish(); }
    }

    sealed class Cine
    {
        readonly Game g;
        readonly CineFile file;
        readonly Battle b;
        readonly Action? done;
        readonly CinePlayer player;
        readonly CinePlaces places;
        readonly CinemaBars bars = new();
        readonly Dictionary<string, PersonView> people = new();
        readonly Dictionary<string, Enemy> enemies = new();
        readonly Dictionary<string, WardenView> bosses = new();
        readonly Dictionary<string, OrbView> orbs = new();
        readonly Dictionary<string, double> orbLight = new();
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
            g.AddChild(bars);
            var cam = g.camera;
            saved = (cam.Fov, cam.KeepAspect, cam.Near, cam.Attributes);
            cam.Near = 0.04f;
            g.controls.Captured = true;
            g.hud.ShowPlay(false);
            g.hud.Prompt(g.promptShown = null);
            g.SetHint(null);
            g.scene!.CameraHeld = true;
            if (g.scene.Player != null) g.scene.Player.Hidden = true;
            b.WorldRate = file.World.Rate; b.WorldRateT = 1e9;
            foreach (var (name, c) in file.Cast) Cast(name, c);
            GD.Print($"cinema: {file.Id} ({player.S.Length:0.0} s, {player.S.Shots.Count} shots)");
            Dispatch(player.Advance(0));
        }

        /* --------------------------------------------------------- the cast -- */

        void Cast(string name, CineCast c)
        {
            if (c.Kind == "survivor")
            {
                var lo = Loadouts.Of(g.Journey.Ch);
                var v = new PersonView(lo.Person, new Held { Right = lo.Arms.Right, Left = lo.Arms.Left, Forearm = lo.Arms.Forearm }, 0.8) { Name = "CineSurvivor" };
                // The townsfolk's clips too (sitting on the floor, arms folded): made on the
                // same skeleton, they stand in until her own cinematic motion comes.
                if (FolkClips.Library() is { } folk && !v.Person.Anim.HasAnimationLibrary("folk")) v.Person.Anim.AddAnimationLibrary("folk", folk);
                g.scene!.AddChild(v);
                people[name] = v;
                if (c.Mark != null) Place(name, places.Resolve(MarkEl(c.Mark)), file.Mark(c.Mark).Heading);
                v.Cue(lo.Arms.Idle, 0, 1, 0);
            }
            else if (c.Kind == "npc" && c.Def != null && Lore.Person(c.Def) is { } def)
            {
                var v = new PersonView(def.Person ?? new PersonSpec(), def.Arms, 0.8 * (def.Scale ?? 1)) { Name = "Cine_" + name };
                g.scene!.AddChild(v);
                people[name] = v;
                if (c.Mark != null) Place(name, places.Resolve(MarkEl(c.Mark)), file.Mark(c.Mark).Heading);
                v.Cue("Idle_Loop", 0, 1, 0);
            }
            else if (c.Kind == "boss")
            {
                // The cinematic's own Warden: the zone's waits hidden, and the
                // fight's takes his place where this one is left.
                var w = new WardenView { Name = "Cine_" + name, Glow = c.Glow };
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
                    var v = new PersonView(spec.Person ?? new PersonSpec(), spec.Arms, 0.8 * spec.Scale) { Name = $"Cine_{name}{i}" };
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
                orbLight[name] = 16 * c.Glow;
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
                return new V3(p.X, p.Y, p.Z);
            }
            if (enemies.TryGetValue(name, out var e)) return new V3(e.X, g.scene!.HeightAt(e.X, e.Z) + (bone == "head" ? 1.6 : 0), e.Z);
            if (orbs.TryGetValue(name, out var o)) { var q = o.GlobalPosition; return new V3(q.X, q.Y, q.Z); }
            return null;
        }

        /* ------------------------------------------------------------ frame -- */

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
            foreach (var v in people.Values) v.Advance(dt);
            foreach (var w in bosses.Values) w.Shine(dt);
            foreach (var o in orbs.Values) o.Turn(dt);
            Camera(dt);
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
                // --cinebones: where the cast's bones are at each still, for framing shots on them.
                if (Args.Has("cinebones"))
                    foreach (var name in people.Keys)
                        GD.Print($"cinebones {file.Id} s{shot.Id} {name} " + string.Join(" ", new[] { "head", "eyes", "chest", "hand_r", "hand_l", "foot_l", "foot_r" }
                            .Select(bn => ActorAt(name, bn) is V3 p ? $"{bn}=({p.X:0.00},{p.Y:0.00},{p.Z:0.00})" : "")));
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
            float hfov = (float)pose.Hfov;
            if (pose.FollowK > 0 && EndPoint() is Vector3 end)
            {
                var (fp, fl) = g.cam.PoseFor(end);
                float k = (float)pose.FollowK;
                pos = pos.Lerp(fp, k);
                at = at.Lerp(fl, k);
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

        Vector3? EndPoint()
        {
            if (file.End.Her is not string m) return null;
            var p = places.Resolve(MarkEl(m));
            return new Vector3((float)p.X, (float)g.scene!.HeightAt(p.X, p.Z), (float)p.Z);
        }

        static Vector3 V(V3 v) => new((float)v.X, (float)v.Y, (float)v.Z);

        /* ------------------------------------------------------------- cues -- */

        void Dispatch(List<TimedCue> cues, bool skipping = false)
        {
            foreach (var tc in cues)
            {
                try { Do(tc, skipping); }
                catch (Exception e) { GD.PushWarning($"cinema {file.Id} shot {tc.Shot.Shot.Id}: {tc.Cue.Do} failed: {e.Message}"); }
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
                    if (bosses.TryGetValue(c.Actor, out var hw)) hw.Visible = !c.Bool("hidden", true);
                    else if (NodeOf(c.Actor) is { } hv) hv.Visible = !c.Bool("hidden", true);
                    break;
                case "lamp":
                {
                    // A boss's eyes and lamp, or an orb's light: how bright, and whether it burns.
                    if (bosses.TryGetValue(c.Actor, out var w))
                    {
                        if (c.Has("lit")) w.LampLit = c.Bool("lit", true);
                        if (!c.Has("glow")) break;
                        double from = w.Glow, to = c.Num("glow");
                        if (over > 0 && !skipping) tweens.Add(new Tween(t0, t0 + over, k => w.Glow = from + (to - from) * k));
                        else w.Glow = to;
                    }
                    else if (orbs.TryGetValue(c.Actor, out var o))
                    {
                        if (c.Has("lit")) o.Visible = c.Bool("lit", true);
                        if (!c.Has("glow")) break;
                        double from = orbLight[c.Actor], to = 16 * c.Num("glow");
                        void Set(double l) { orbLight[c.Actor] = l; ((IOrb)o).Light = l; }
                        if (over > 0 && !skipping) tweens.Add(new Tween(t0, t0 + over, k => Set(from + (to - from) * k)));
                        else Set(to);
                    }
                    break;
                }
                case "anim":
                {
                    if (!people.TryGetValue(c.Actor, out var v)) break;
                    var clip = c.Str("clip")!;
                    if (clip == "@idle") clip = Loadouts.Of(g.Journey.Ch).Arms.Idle;
                    v.Cue(clip, c.Num("from"), c.Num("speed", 1), c.Num("blend", 0.2));
                    break;
                }
                case "move":
                {
                    if (NodeOf(c.Actor) is not { } n) break;
                    var toEl = c.Has("to") && c.Get("to").ValueKind != JsonValueKind.String ? c.Get("to") : MarkEl(c.Str("to")!);
                    var to = places.Resolve(toEl);
                    var from = n.GlobalPosition;
                    var dest = V(to);
                    double heading = c.Has("heading") ? c.Num("heading") : Math.Atan2(dest.X - from.X, dest.Z - from.Z);
                    // An exact place ("abs") is gone to through the air or the water; anything else along the ground.
                    bool free = orbs.ContainsKey(c.Actor) || (toEl.ValueKind == JsonValueKind.Object && toEl.TryGetProperty("abs", out _));
                    moves.Add(new Move(c.Actor, from, dest, t0, t0 + c.Num("dur", 1), heading, free));
                    if (c.Str("clip") is string mc && n is PersonView v) v.Cue(mc, 0, c.Num("speed", 1), 0.25);
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
                case "gaze":
                {
                    if (Life(c.Actor) is not { } life) break;
                    var look = c.Get("look");
                    if (look.ValueKind == JsonValueKind.Array) life.Look = new Vector2((float)look[0].GetDouble(), (float)look[1].GetDouble());
                    if (c.Has("wander")) life.Wander = (float)c.Num("wander");
                    if (c.Bool("snap", true)) life.Snap();
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
                case "light":
                {
                    int i = (int)c.Num("light");
                    float from = (float)c.Num("from", 1), to = (float)c.Num("level", 1), rate = (float)c.Num("rate", 1);
                    Color? col = c.Str("color") is string hex ? new Color(hex) : null;
                    if (over > 0 && !skipping) tweens.Add(new Tween(t0, t0 + over, k => g.scene!.View.SetLevel(i, Mathf.Lerp(from, to, (float)k), col, rate)));
                    else g.scene!.View.SetLevel(i, to, col, rate);
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
                    var to = Atmospheres.ByName(c.Str("preset")!);
                    if (over > 0 && !skipping && c.Str("from") is string fromName)
                    {
                        var from = Atmospheres.ByName(fromName);
                        double last = -1;
                        tweens.Add(new Tween(t0, t0 + over, k => { if (k - last > 0.02 || k >= 1) { last = k; g.SetAtmosphere(Atmospheres.Blend(from, to, k), k >= 1); } }));
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
                    if (e != null) enemies[c.Actor] = e;
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
                        case "nova": b.Events.Emit(new Ev.Nova { X = at.X, Z = at.Z, Radius = c.Num("radius", 2), School = Enum.Parse<School>(c.Str("school") ?? "frost", true), Duration = c.Num("dur", 0.9) }); break;
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
                    // A thing set down for the scene: her weapon leaning on the log.
                    var arms = Loadouts.Of(g.Journey.Ch).Arms;
                    string? piece = c.Str("piece") switch { "@weapon" => arms.Right ?? arms.Left, "@shield" => arms.Forearm, var s => s };
                    string name = c.Str("name") ?? piece ?? "prop";
                    if (props.Remove(name, out var old)) old.QueueFree();
                    if (piece == null || !Arms.All.ContainsKey(piece) || c.Bool("remove")) break;
                    var node = Arms.Make(piece);
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
                            var d = new Decal
                            {
                                TextureAlbedo = Frost(new Vector2(x0, z0), tile, new Vector2((float)at.X, (float)at.Z), size, hole, rad, trail),
                                Size = new Vector3(tile, 1.4f, tile), Position = new Vector3(cx, (float)g.scene!.HeightAt(cx, cz) + 0.35f, cz),
                                AlbedoMix = (float)c.Num("amount", 0.4), CullMask = 1, UpperFade = 0.1f, LowerFade = 0.1f,
                            };
                            g.scene.AddChild(d);
                            prints.Add(d);
                        }
                    break;
                }
                case "glow":
                {
                    // A light seen far off (the ford's lamps from the camp, one lamp high up the
                    // road): a point of its colour and a halo, for this cinematic only. "clear"
                    // carries it through the mist; without it the air takes it as it takes all else.
                    string name = c.Str("name") ?? $"glow{props.Count}";
                    if (props.Remove(name, out var old)) old.QueueFree();
                    if (c.Bool("remove")) break;
                    var col = new Color(c.Str("color") ?? "#ffcf80");
                    float size = (float)c.Num("size", 0.3), energy = (float)c.Num("energy", 3);
                    bool clear = c.Bool("clear");
                    var root = new Node3D { Position = V(places.Resolve(c.Get("where"))) };
                    var lin = col.SrgbToLinear() * energy;
                    root.AddChild(new MeshInstance3D
                    {
                        Mesh = new SphereMesh { Radius = size, Height = size * 2, RadialSegments = 12, Rings = 6 },
                        CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                        MaterialOverride = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(lin.R, lin.G, lin.B), DisableFog = clear },
                    });
                    root.AddChild(new MeshInstance3D
                    {
                        Mesh = new QuadMesh { Size = Vector2.One * size * (float)c.Num("spread", 9) },
                        CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                        MaterialOverride = new StandardMaterial3D
                        {
                            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
                            BlendMode = BaseMaterial3D.BlendModeEnum.Add, BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
                            AlbedoTexture = Halo(), AlbedoColor = new Color(col.R, col.G, col.B, (float)c.Num("halo", 0.55)), DisableFog = clear,
                        },
                    });
                    // "light": it lights what is near it too (a lamp held to a face), within "range".
                    if (c.Has("light"))
                        root.AddChild(new OmniLight3D { LightColor = col, LightEnergy = (float)c.Num("light"), OmniRange = (float)c.Num("range", 4), OmniAttenuation = 1.4f });
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
                case "bars" or "fade" or "wet":
                    // The bars and black follow the shots; wetness waits on its system (docs/cinematics/README.md section 6, 7).
                    break;
            }
        }

        readonly Dictionary<string, Node3D> props = new();
        static GradientTexture2D? halo;

        /// <summary>A soft round halo, bright at the middle and gone at the edge.</summary>
        static GradientTexture2D Halo() => halo ??= new GradientTexture2D
        {
            Gradient = new Gradient { Colors = [new Color(1, 1, 1, 1), new Color(1, 1, 1, 0.25f), new Color(1, 1, 1, 0)], Offsets = [0, 0.18f, 1] },
            Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f), Width = 64, Height = 64,
        };
        readonly List<Decal> prints = new();
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
        static ImageTexture Frost(Vector2 corner, float tile, Vector2 centre, float size, Vector2? hole, float radius, List<Vector2> trail)
        {
            const int N = 96;
            var img = Image.CreateEmpty(N, N, false, Image.Format.Rgba8);
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    var w = corner + new Vector2((x + 0.5f) / N, (y + 0.5f) / N) * tile;
                    float n = frostNoise.GetNoise2D(w.X, w.Y) * 0.5f + 0.5f;
                    float a = Mathf.SmoothStep(0.3f, 0.7f, n);
                    var off = (w - centre).Abs() / (size / 2);
                    a *= Mathf.Clamp((1 - Mathf.Max(off.X, off.Y)) / 0.2f, 0, 1);
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

        public void Finish()
        {
            var p = b.Player;
            if (file.End.Her is string m)
            {
                var (x, _, z, heading) = file.Mark(m);
                p.X = x; p.Z = z; p.Facing = heading; p.Vx = p.Vz = 0;
            }
            foreach (var (name, v) in people) if (!bosses.ContainsKey(name)) v.QueueFree();
            foreach (var w in bosses.Values) w.QueueFree();
            foreach (var o in orbs.Values) o.QueueFree();
            bosses.Clear(); orbs.Clear(); groups.Clear(); later.Clear();
            foreach (var n in props.Values) n.QueueFree();
            props.Clear();
            // Her prints stay: they are in the frost whether it played or not.
            people.Clear();
            var cam = g.camera;
            cam.Fov = saved.Fov; cam.KeepAspect = saved.Keep; cam.Near = saved.Near; cam.Attributes = saved.Attr;
            g.scene!.CameraHeld = false;
            if (g.scene.Player != null) g.scene.Player.Hidden = false;
            g.cam.Snap((float)p.X, (float)g.scene.HeightAt(p.X, p.Z), (float)p.Z);
            b.WorldRate = 1; b.WorldRateT = 0;
            g.sound.CineMood = null;
            g.controls.Captured = false;
            g.controls.ClearLatches();
            g.hud.ShowPlay(true);
            bars.QueueFree();
            if (!Settings.Current.SeenCinematics.Contains(file.Id)) { Settings.Current.SeenCinematics.Add(file.Id); Settings.Current.Save(); }
            GD.Print($"cinema: {file.Id} {(player.Skipped ? "skipped" : "done")}");
            done?.Invoke();
        }
    }
}
