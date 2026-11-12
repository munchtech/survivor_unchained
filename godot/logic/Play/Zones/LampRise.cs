using System;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play.Zones;

/* The lamp-posts in play and the Ember Walker's rise (docs/design/ARPG.md section 2 'Lamp-posts', 7.2 Death): a checkpoint
 * post is lit by her hand out of a fight and becomes her last post in its zone; a fall stands her up there (else at the
 * zone's own fallback), whole, with everything she carries. Foes she killed stay dead and placed packs that are down stay
 * down; living champions and bosses heal to full. The story's toll counts each rise (the world fact toll.rises). One piece
 * for every zone that rises her (the Low Ford, the Verge). */
public static class LampRise
{
    /// <summary>The story's toll: each rise counts (PLAN.md: every rising costs a life, revealed at C41).</summary>
    public const string TollFact = "toll.rises";
    /// <summary>Lighting a post: within this of it.</summary>
    public const double Reach = 3;
    /// <summary>Out of a fight: no foe within this of the post (the day post's lock).</summary>
    public const double Calm = 9;

    public static int Toll(WorldState w) => (int)w.Fact(TollFact).Number;

    /// <summary>A rise counted on the toll; the toll after it.</summary>
    public static int CountRise(WorldState w)
    {
        int n = Toll(w) + 1;
        w.Facts[TollFact] = n;
        return n;
    }

    /// <summary>The narrator's line for the toll's nth rise: the first ever "You get up.", the rest "It takes less than it did."</summary>
    public static string Line(int toll) => toll <= 1 ? Journey.DayLines.Rise : Journey.DayLines.RiseAgain;

    /// <summary>Where she rises in a zone: her last post there, while it burns; else null (the zone's own fallback).</summary>
    public static (double X, double Z)? Post(WorldState w, string zone) => LampBook.LastPost(w, zone) is { } p ? (p.X, p.Z) : null;

    /// <summary>(M5 r3) Where she stands up beside a post: RiseOff m off it toward the road (`toward`, a direction), on free
    /// ground (`free`: the fight's collision), the nearest free bearing to it at RiseOff, then RiseOffNear and RiseOffFar;
    /// none free: the post itself. The judge: she rose on the post, its "Rest" prompt over her torso.</summary>
    public static (double X, double Z) RiseSpot(double x, double z, (double X, double Z) toward, Func<double, double, bool> free)
    {
        double a0 = Math.Atan2(toward.Z, toward.X);
        if (toward.X == 0 && toward.Z == 0) a0 = 0;
        foreach (var d in new[] { RiseOff, RiseOffNear, RiseOffFar })
            for (int i = 0; i <= 12; i++)
            {
                // (0, +30, -30, +60, -60 ... degrees from the road's way)
                double a = a0 + (i % 2 == 1 ? 1 : -1) * ((i + 1) / 2) * Math.PI / 6;
                double rx = x + Math.Cos(a) * d, rz = z + Math.Sin(a) * d;
                if (free(rx, rz)) return (rx, rz);
            }
        return (x, z);
    }
    public const double RiseOff = 1.75, RiseOffNear = 1.5, RiseOffFar = 2.0;
    /// <summary>(M5 r3) The post's prompt is held this long after she rises (s).</summary>
    public const double RisePromptHush = 2.2;

    /// <summary>(M5 r3) Where she rises in a zone, stood beside her last post toward its road (RiseSpot); else the fallback.</summary>
    public static (double X, double Z) RiseAt(WorldState w, string zone, Battle b, (double X, double Z) fallback)
    {
        if (LampBook.LastPost(w, zone) is not { } p) return fallback;
        var way = p.Rise is { Length: 2 } r ? (r[0], r[1]) : (fallback.X - p.X, fallback.Z - p.Z);
        Func<double, double, bool> free = (x, z) => !b.Collision.Blocked(x, z, 0.5) && (b.Collision.Bound <= 0 || Math.Abs(x) < b.Collision.Bound - 1 && Math.Abs(z) < b.Collision.Bound - 1);
        // (M5 r4: a bearing outside every resting pack's waking distance first, when there is one)
        var calm = RiseSpot(p.X, p.Z, way, (x, z) => free(x, z) && !InWake(b, x, z));
        return calm != (p.X, p.Z) ? calm : RiseSpot(p.X, p.Z, way, free);
    }

    /// <summary>(M5 r4) (x, z) is within a resting foe's waking distance (plus a metre).</summary>
    public static bool InWake(Battle b, double x, double z)
    {
        foreach (var e in b.Enemies.Living())
            if (e.Wake > 0 && !e.Roused && e.State != EnemyState.Dying && (e.X - x) * (e.X - x) + (e.Z - z) * (e.Z - z) < (e.Wake + 1) * (e.Wake + 1))
                return true;
        return false;
    }

    /// <summary>Hostile foes on their feet within r of a spot.</summary>
    public static int Crowd(Battle b, double x, double z, double r) =>
        b.Enemies.Living().Count(e => e.State is not (EnemyState.Dying or EnemyState.Rising) && e.Disposition == Disposition.Hostile && Math.Sqrt((e.X - x) * (e.X - x) + (e.Z - z) * (e.Z - z)) < r);

    /// <summary>She stands up at (x, z): whole, her things all hers; the living champions and bosses whole again.</summary>
    public static void Stand(IZoneHost g, Battle b, double x, double z)
    {
        b.Over = null;
        var p = b.Player;
        p.Alive = true;
        p.Hp = b.MaxHp;
        // (SU-059) a clean start: a leap, dash or cast she fell in ends, her poison, burning, slows and roots clear
        b.CleanStart();
        p.Iframes = 3;
        p.X = x; p.Z = z;
        // (M5 r3: no post prompt over her as she gets up)
        g.HushPrompts(RisePromptHush);
        // (M5 r4: no pack wakes as she gets up: n_road3 charged her mid-rise)
        b.Breather(Battle.RiseQuiet);
        foreach (var e in b.Enemies.Living())
            if ((e.Elite || e.Boss || e.Named != null) && e.State != EnemyState.Dying) e.Hp = e.MaxHp;
        g.Revived(x, z);
    }

    /// <summary>A zone's lanterns as its posts stand: lit, or dark until she lights them.</summary>
    public static void ShowLamps(IZoneHost g, string zone)
    {
        foreach (var p in LampPosts.In(zone))
        {
            if (p.Light < 0) continue;
            bool on = LampBook.PostLit(g.Journey.World, p.Id);
            g.Look.SetLit(p.Light, on);
            if (on && !p.Town) Shine(g, p.Light, LampPosts.Lit.Level);
        }
    }

    /// <summary>(M5 r2) A lit post's own light (lamp_posts.json "lit"): a cooler, whiter gold than her ember, brighter.</summary>
    static void Shine(IZoneHost g, int light, double level) => g.Look.LightLevel(light, level, LampPosts.Lit.Color);

    /// <summary>(M5 r2) Its kindling: the light flares to "flare" and falls back to its lit level over flareSeconds.</summary>
    static void Flare(IZoneHost g, int light)
    {
        var l = LampPosts.Lit;
        const int Steps = 6;
        Shine(g, light, l.Flare);
        for (int i = 1; i <= Steps; i++)
        {
            double k = i / (double)Steps, lv = l.Flare + (l.Level - l.Flare) * k;
            g.After(l.FlareSeconds * k, () => Shine(g, light, lv));
        }
    }

    /// <summary>The zone's checkpoint posts (not its towns' posts, lit from the start, nor its dark posts, which the zone
    /// relights in its own words) as prompts: "Light", within Reach, out of a fight; open (when given) says when.</summary>
    /// <summary>A boss's door post lights by itself when she comes within this of it out of a fight (Doors).</summary>
    public const double DoorReach = 6;

    /// <summary>The prompt that opens a lit post's menu (PostMenu): "lamppost-menu:" + its id.</summary>
    public const string MenuPrefix = "lamppost-menu:";

    public static void AddPosts(ZoneRuntime z, IZoneHost g, Func<Battle?> battle, Func<LampPosts.Post, bool>? open = null)
    {
        foreach (var p in LampPosts.In(z.Id).Where(p => !p.Dark && !p.Town))
            z.Interactables.Add(new()
            {
                Id = "lamppost:" + p.Id, X = p.X, Z = p.Z, R = Reach, Verb = "Light", Name = p.Name,
                When = () => !LampBook.PostLit(g.Journey.World, p.Id) && (open == null || open(p)),
                Locked = () => battle() is { } b && Crowd(b, p.X, p.Z, Calm) > 0 ? "Not with them on you" : null,
                Act = () => Light(g, battle(), p),
            });
        // Every post of the zone once it burns (a town's from the start, a dark one once relit): "Rest" opens its menu.
        foreach (var p in LampPosts.In(z.Id))
            z.Interactables.Add(new()
            {
                Id = MenuPrefix + p.Id, X = p.X, Z = p.Z, R = Reach, Verb = "Rest", Name = p.Name,
                When = () => LampBook.PostLit(g.Journey.World, p.Id),
                Act = () => g.OpenPost(p.Id),
            });
    }

    /// <summary>A boss's door posts light by themselves (each step of the zone): within DoorReach, out of a fight, and only
    /// where the zone's own prompt would offer the lighting (its When and Locked), so the rise never misses the door.</summary>
    public static void Doors(ZoneRuntime z, Battle? b)
    {
        if (b is not { Player.Alive: true }) return;
        foreach (var i in z.Interactables)
        {
            if (!i.Id.StartsWith("lamppost:") || LampPosts.Get(i.Id[9..]) is not { Door: true } p) continue;
            double dx = b.Player.X - p.X, dz = b.Player.Z - p.Z;
            if (dx * dx + dz * dz > DoorReach * DoorReach || i.When?.Invoke() == false || i.Locked?.Invoke() != null) continue;
            i.Act();
        }
    }

    /// <summary>She lights a checkpoint post: for good, her rise point in its zone, its lantern burning. A door's post says so
    /// in its own toast (placeholder words for the story lead).</summary>
    public static bool Light(IZoneHost g, Battle? b, LampPosts.Post p)
    {
        if (!LampBook.LightPost(g.Journey.World, p.Id)) return false;
        if (b != null) b.LampLitAt = b.Time;
        if (p.Light >= 0) { g.Look.SetLit(p.Light, true); Flare(g, p.Light); }
        b?.Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = 2.2, School = School.Fire, Duration = 0.9 });
        // (M5 r2: the kindling read as nothing at play distance: a second, wider ring after the first)
        b?.Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = 4.5, School = School.Fire, Duration = 1.2, Rings = 2 });
        g.Toast(p.Door
            ? new Toast(ToastKind.World, $"{p.Name} kindles as you come", "Whatever waits past it, you will rise here.", Life: 4)
            : new Toast(ToastKind.World, $"{p.Name} burns again", "If you fall, you will rise here.", Life: 5));
        g.Save("post");
        return true;
    }
}
