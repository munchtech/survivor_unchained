using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

/* Every lamp-post as data (data/content/lamp_posts.json; docs/design/ARPG.md section 2 'Lamp-posts' and 7.2): her checkpoints
 * (where she rises), the boss doors' posts, the towns' posts, and the acts' dark posts off the road. It is the one source of
 * truth for the posts: Lamps v2's board points (Lamps.Posts) are its board posts. What she has lit is LampBook's (world facts). */
public static class LampPosts
{
    public sealed class Post
    {
        public string Id = "", Zone = "", Name = "Lamp-post";
        public int Act;
        public double X, Z;
        /// <summary>"checkpoint" (lit by her hand; no board point) or "dark" (relit for a lamp-board point).</summary>
        public string Kind = "checkpoint";
        /// <summary>It stands at a boss's door.</summary>
        public bool Door;
        /// <summary>Relighting it gives a lamp-board point (dark posts only).</summary>
        public bool Board;
        /// <summary>A town's post: lit from the start.</summary>
        public bool Town;
        /// <summary>Where it stands is still a placeholder.</summary>
        public bool Draft;
        /// <summary>The zone light that is its lantern (dark until lit), or -1.</summary>
        public int Light = -1;

        public bool Dark => Kind == "dark";

        /// <summary>Where it stands once the zone holds a feature (the ground lead moves it onto real ground, and sets the
        /// light index when it places the lamp): without that feature X, Z and Light above hold.</summary>
        public Move? Moved;
        double baseX, baseZ; int baseLight; bool kept;

        /// <summary>Where it stands, and its lantern, given the zone's features.</summary>
        public (double X, double Z, int Light) At(IReadOnlyCollection<string>? features)
        {
            if (!kept) { baseX = X; baseZ = Z; baseLight = Light; kept = true; }
            return Moved is { } m && features?.Contains(m.Needs) == true ? (m.X, m.Z, m.Light) : (baseX, baseZ, baseLight);
        }

        internal void Resolve(IReadOnlyCollection<string>? features) => (X, Z, Light) = At(features);
    }

    public sealed class Move { public string Needs = "", About = ""; public double X, Z; public int Light = -1; }

    sealed class File { public List<Post> Posts = new(); }

    static List<Post>? all;
    static List<Post> F => all ??= Load();

    static List<Post> Load()
    {
        var f = Json.Parse<File>(Json.ReadContent("lamp_posts.json"));
        var ids = new HashSet<string>();
        foreach (var p in f.Posts)
        {
            if (!ids.Add(p.Id)) throw new InvalidOperationException($"lamp-post {p.Id} twice");
            if (p.Kind is not ("checkpoint" or "dark")) throw new InvalidOperationException($"lamp-post {p.Id}: kind {p.Kind}");
            if (p.Board != p.Dark) throw new InvalidOperationException($"lamp-post {p.Id}: board points are the dark posts' alone");
            if (p.Town && p.Dark) throw new InvalidOperationException($"lamp-post {p.Id}: a town post is a checkpoint");
        }
        return f.Posts;
    }

    public static void Reload() => all = null;

    /// <summary>A zone is loaded with these features: its posts stand where they say (Post.Moved). Every post reads X, Z and
    /// Light as resolved, so this runs once as the zone is made (a zone without the feature puts them back).</summary>
    public static void Resolve(string zone, IReadOnlyCollection<string>? features)
    {
        foreach (var p in F) if (p.Zone == zone) p.Resolve(features);
    }

    public static IReadOnlyList<Post> All => F;
    public static Post? Get(string id) => F.FirstOrDefault(p => p.Id == id);
    /// <summary>A zone's posts, placeholders left out.</summary>
    public static IEnumerable<Post> In(string zone) => F.Where(p => p.Zone == zone && !p.Draft);
    /// <summary>The posts whose relighting gives a lamp-board point (Lamps v2's posts).</summary>
    public static IEnumerable<Post> Board => F.Where(p => p.Board);
}
