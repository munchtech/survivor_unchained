using System;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Ui;

namespace SurvivorUnchained.Play;

/* A lit lamp-post's menu on this side of the screen (Play/PostMenu.cs has its options and gates; Ui/PostScreen.cs shows it):
 * opening it, travel to another lit post (in the zone: a fade and a move; to another zone: Travel, arriving at the post), the
 * world tier picked, and the Lamps opened at the post as the respec bench. */
public partial class Game
{
    /// <summary>The next arrival is a lamp-post's travel: EnterPlay still tells the zone where she came from (ArrivalFrom),
    /// so its 'leave' reset is as any entry from that zone, then stands her at the post.</summary>
    bool toPost;

    /// <summary>IZoneHost: the post's menu, as Open does a screen.</summary>
    public void OpenPost(string postId)
    {
        if (scene == null || Mode != "play" || inTransit || LampPosts.Get(postId) is not { } p) return;
        var o = new PostScreen(this, p);
        screens.Show(o);
        scene.SimPaused = zone?.Ember == true;
        Reframe(o);
        LookFor(o.CameraLook);
        controls.Captured = true;
        hud.Prompt(promptShown = null);
    }

    /// <summary>From one lit post to another (refused in a fight); she stands at it, and it is her last post in its zone.</summary>
    public void PostTravel(LampPosts.Post from, LampPosts.Post to)
    {
        CloseOverlay();
        if (inTransit || zone == null || scene == null) return;
        if (PostMenu.TravelRefused(Battle, from) is { } no) { Toast(new Toast(ToastKind.Warning, no)); return; }
        LampBook.SetLastPost(World, to.Zone, to.Id);
        if (to.Zone != zone.Id)
        {
            toPost = true;
            Travel(to.Zone, PostMenu.ZoneName(to.Zone), to.Name, new Arrival(to.X, to.Z), from: zone.Id);
            return;
        }
        var b = Battle;
        inTransit = true;
        scene.SimPaused = true;
        controls.Captured = true;
        hud.Fade(1, 0.5, null, to.Name);
        Wait(0.55, () =>
        {
            if (b != null && b == Battle)
            {
                b.Player.X = to.X; b.Player.Z = to.Z; b.Player.Vx = b.Player.Vz = 0;
                cam.Snap((float)to.X, (float)(scene?.HeightAt(to.X, to.Z) ?? 0), (float)to.Z);
            }
            Save("travel");
            if (scene != null) scene.SimPaused = false;
            hud.Fade(0, 0.8);
            controls.Captured = false;
            controls.ClearLatches();
            inTransit = false;
        });
    }

    /// <summary>(M5 r3) Rest at a post: her rise point there, mended; the menu closes.</summary>
    public void PostRest(LampPosts.Post at)
    {
        if (!PostMenu.Rest(World, Battle, at)) { Toast(new Toast(ToastKind.Warning, "Not with them on you")); return; }
        CloseOverlay();
        Toast(new Toast(ToastKind.World, "Rested", $"{at.Name}. Fall, and you rise here.", Life: 4)); // (M6, TUTORIAL_COPY.md)
        Save("post");
    }

    /// <summary>The world tier picked at a post: the live fight re-scaled (PostMenu.SetTier), and saved.</summary>
    public void PostTier(int n)
    {
        if (!PostMenu.SetTier(World, Battle, Journey.WorldTierOn, n)) return;
        Toast(new Toast(ToastKind.World, $"World tier {WorldTiers.Get(n).Name}", PostMenu.Numbers(WorldTiers.Get(n)), Life: 4));
        Save("tier");
    }

    /// <summary>(bd-sockets) A Union joined or unjoined at the post (PostMenu.ToggleUnion: the first join pays), and saved.
    /// The fight takes it up when its kit is next worn (UnionJoin.Apply, hooked after bd-keys).</summary>
    public void PostUnion(LampPosts.Post at, string id)
    {
        if (PostMenu.ToggleUnion(World, Battle, at, Journey.Ch, id) is { } no) { Toast(new Toast(ToastKind.Warning, no)); return; }
        bool joined = UnionJoin.Joined(Journey.Ch).Contains(id);
        Toast(new Toast(ToastKind.World, joined ? "Union joined" : "Union unjoined", Content.Unions.Find(id)?.Name ?? id, Life: 4));
        Save("union");
        screens.Current?.Refresh();
    }

    /// <summary>The Lamps at the post, layouts open there while she stays by it, out of a fight (LampBook.Bench).</summary>
    public void PostLamps(LampPosts.Post p)
    {
        var b = Battle;
        var w = World;
        LampBook.Bench = world => world == w && b != null && b == Battle && PostMenu.AtBench(world, b, p) ? p.Id : null;
        CloseOverlay();
        Open(LampsScreen.On ? "lamps" : "arts");
    }
}
