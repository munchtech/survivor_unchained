import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"


def edit(rel, pairs):
    p = os.path.join(G, rel)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, (rel, s.count(old), old[:70])
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)


edit(r"src\Game\GameCinema.cs", [
# the entry point takes marks
('''    public bool Cinematic(string id, Action? done = null)
    {''',
'''    public bool Cinematic(string id, Action? done = null, IReadOnlyDictionary<string, double[]>? marks = null)
    {'''),
('''        catch (Exception e) { GD.PushWarning($"cinema: {id} not played ({e.Message})"); return false; }
''',
'''        catch (Exception e) { GD.PushWarning($"cinema: {id} not played ({e.Message})"); return false; }
        // Where things really are (a boss falls where the fight leaves him).
        if (marks != null) foreach (var (k, v) in marks) file.Marks[k] = v.ToArray();
'''),
# fields
('''        readonly Dictionary<string, Enemy> enemies = new();
''',
'''        readonly Dictionary<string, Enemy> enemies = new();
        readonly Dictionary<string, WardenView> bosses = new();
        readonly Dictionary<string, OrbView> orbs = new();
        readonly Dictionary<string, double> orbLight = new();
        /// <summary>A crowd of extras by its cast name: its members' names, in order.</summary>
        readonly Dictionary<string, List<string>> groups = new();
        /// <summary>A crowd's cue, staggered down its members: done when the clock reaches it.</summary>
        readonly List<TimedCue> later = new();
'''),
('''        sealed record Move(string Actor, Vector3 From, Vector3 To, double T0, double T1, double Heading);''',
'''        /// <summary>Free: through the air or the water (an exact place), not along the ground.</summary>
        sealed record Move(string Actor, Vector3 From, Vector3 To, double T0, double T1, double Heading, bool Free = false);'''),
# cast kinds
('''            else if (c.Kind == "npc" && c.Def != null && Lore.Person(c.Def) is { } def)
            {
                var v = new PersonView(def.Person ?? new PersonSpec(), def.Arms, 0.8 * (def.Scale ?? 1)) { Name = "Cine_" + name };
                g.scene!.AddChild(v);
                people[name] = v;
                if (c.Mark != null) Place(name, places.Resolve(MarkEl(c.Mark)), file.Mark(c.Mark).Heading);
                v.Cue("Idle_Loop", 0, 1, 0);
            }
        }''',
'''            else if (c.Kind == "npc" && c.Def != null && Lore.Person(c.Def) is { } def)
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
            var args = new Dictionary<string, JsonElement>(c.Args ?? new()) { ["actor"] = JsonSerializer.SerializeToElement(who) };
            return new CineCue { At = c.At, Do = c.Do, When = c.When, Skip = c.Skip, Args = args };
        }'''),
('''        void Place(string actor, V3 at, double heading, bool visible = true)
        {
            if (people.TryGetValue(actor, out var v)) v.Place(at.X, at.Y, at.Z, heading, visible);
        }''',
'''        void Place(string actor, V3 at, double heading, bool visible = true)
        {
            if (people.TryGetValue(actor, out var v)) v.Place(at.X, at.Y, at.Z, heading, visible);
            else if (orbs.TryGetValue(actor, out var o)) { o.Position = V(at); o.Visible = visible; }
        }'''),
('''            if (enemies.TryGetValue(name, out var e)) return new V3(e.X, g.scene!.HeightAt(e.X, e.Z) + (bone == "head" ? 1.6 : 0), e.Z);
            return null;''',
'''            if (enemies.TryGetValue(name, out var e)) return new V3(e.X, g.scene!.HeightAt(e.X, e.Z) + (bone == "head" ? 1.6 : 0), e.Z);
            if (orbs.TryGetValue(name, out var o)) { var q = o.GlobalPosition; return new V3(q.X, q.Y, q.Z); }
            return null;'''),
# frame
('''            Dispatch(player.Advance(dt));
            double t = player.T;''',
'''            Dispatch(player.Advance(dt));
            double t = player.T;
            if (later.Count > 0)
            {
                var due = later.Where(c => c.T <= t).OrderBy(c => c.T).ToList();
                foreach (var tc in due) later.Remove(tc);
                Dispatch(due);
            }'''),
('''                if (people.TryGetValue(m.Actor, out var v)) v.Place(p.X, g.scene!.HeightAt(p.X, p.Z), p.Z, m.Heading, true);
                if (k >= 1) moves.Remove(m);
            }
            foreach (var v in people.Values) v.Advance(dt);''',
'''                if (people.TryGetValue(m.Actor, out var v)) v.Place(p.X, m.Free ? p.Y : g.scene!.HeightAt(p.X, p.Z), p.Z, m.Heading, true);
                else if (orbs.TryGetValue(m.Actor, out var o)) o.Position = p;
                if (k >= 1) moves.Remove(m);
            }
            foreach (var v in people.Values) v.Advance(dt);
            foreach (var w in bosses.Values) w.Shine(dt);
            foreach (var o in orbs.Values) o.Turn(dt);'''),
# group expansion at the top of Do
('''        void Do(TimedCue tc, bool skipping)
        {
            var c = tc.Cue;
            double t0 = tc.T, over = c.Num("over");
            switch (c.Do)
            {''',
'''        void Do(TimedCue tc, bool skipping)
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
            {'''),
# hide covers bosses and orbs
('''                case "hide":
                    if (people.TryGetValue(c.Actor, out var hv)) hv.Visible = !c.Bool("hidden", true);
                    break;''',
'''                case "hide":
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
                }'''),
# move: free through the air or the water; orbs
('''                case "move":
                {
                    if (!people.TryGetValue(c.Actor, out var v)) break;
                    var to = places.Resolve(c.Has("to") && c.Get("to").ValueKind != JsonValueKind.String ? c.Get("to") : MarkEl(c.Str("to")!));
                    var from = v.GlobalPosition;
                    var dest = V(to);
                    double heading = c.Has("heading") ? c.Num("heading") : Math.Atan2(dest.X - from.X, dest.Z - from.Z);
                    moves.Add(new Move(c.Actor, from, dest, t0, t0 + c.Num("dur", 1), heading));
                    if (c.Str("clip") is string mc) v.Cue(mc, 0, c.Num("speed", 1), 0.25);
                    break;
                }''',
'''                case "move":
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
                }'''),
# spawn options
('''                    var e = b.SpawnEnemy(c.Str("def") ?? file.Cast.GetValueOrDefault(c.Actor)?.Def ?? "risen", at.X, at.Z, new Battle.SpawnOpts { Style = style, Level = (int)c.Num("level", 1) });''',
'''                    var e = b.SpawnEnemy(c.Str("def") ?? file.Cast.GetValueOrDefault(c.Actor)?.Def ?? "risen", at.X, at.Z, new Battle.SpawnOpts
                    {
                        Style = style, Level = (int)c.Num("level", 1), Tag = c.Str("tag"), Disposition = c.Bool("neutral") ? Disposition.Neutral : null,
                    });'''),
# finish frees bosses and orbs
('''            foreach (var v in people.Values) v.QueueFree();
            foreach (var n in props.Values) n.QueueFree();''',
'''            foreach (var (name, v) in people) if (!bosses.ContainsKey(name)) v.QueueFree();
            foreach (var w in bosses.Values) w.QueueFree();
            foreach (var o in orbs.Values) o.QueueFree();
            bosses.Clear(); orbs.Clear(); groups.Clear(); later.Clear();
            foreach (var n in props.Values) n.QueueFree();'''),
])

edit(r"src\Actors\BossViews.cs", [(
'''    public double Light { set => light.LightEnergy = (float)(value / Math.PI); }
    void IOrb.Dispose() => QueueFree();''',
'''    public double Light { set => light.LightEnergy = (float)(value / Math.PI); }

    /// <summary>Turning slowly where it hangs (a cinematic's frame).</summary>
    public void Turn(double dt) => ball.RotateY((float)(dt * 1.4));
    void IOrb.Dispose() => QueueFree();'''),
])
print("ok")
