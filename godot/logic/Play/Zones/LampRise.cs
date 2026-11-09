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
        p.Iframes = 3;
        p.X = x; p.Z = z;
        foreach (var e in b.Enemies.Living())
            if ((e.Elite || e.Boss || e.Named != null) && e.State != EnemyState.Dying) e.Hp = e.MaxHp;
        g.Revived(x, z);
    }

    /// <summary>A zone's lanterns as its posts stand: lit, or dark until she lights them.</summary>
    public static void ShowLamps(IZoneHost g, string zone)
    {
        foreach (var p in LampPosts.In(zone))
            if (p.Light >= 0) g.Look.SetLit(p.Light, LampBook.PostLit(g.Journey.World, p.Id));
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
        if (p.Light >= 0) g.Look.SetLit(p.Light, true);
        b?.Events.Emit(new Ev.Nova { X = p.X, Z = p.Z, Radius = 2.2, School = School.Fire, Duration = 0.9 });
        g.Toast(p.Door
            ? new Toast(ToastKind.World, $"{p.Name} kindles as you come", "Whatever waits past it, you will rise here.", Life: 4)
            : new Toast(ToastKind.World, $"{p.Name} burns again", "If you fall, you will rise here.", Life: 5));
        g.Save("post");
        return true;
    }
}
