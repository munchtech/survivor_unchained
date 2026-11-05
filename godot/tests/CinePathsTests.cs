using System.Collections.Generic;
using System.IO;
using SurvivorUnchained.Cinema;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>A cinematic never walks her into, or hands her back in front of, something solid.</summary>
public class CinePathsTests
{
    // Found when this check was written, in Low Ford (not the Waystation lead's to move): C01 starts by her
    // campfire and log, and C02 hands back with a tree edge at the runway's side. Anything new fails.
    static readonly HashSet<string> Known = ["c01:-10.5,90.5", "c01:-10.9,88.2", "c02:4.0,-31.0", "c02w:4.0,-31.0"];

    [Fact]
    public void No_cinematic_walks_her_into_a_collider_or_hands_her_back_to_one()
    {
        var bad = new List<string>();
        foreach (var f in Directory.GetFiles(Path.Combine(DataFiles.Dir, "cinematics"), "*.json"))
        {
            if (Path.GetFileName(f).StartsWith('_')) continue;
            var cine = CineFile.Parse(File.ReadAllText(f));
            if (string.IsNullOrEmpty(cine.Zone)) continue;
            // Arena films (C13 on the Vault): the arena is built from code (ArenaGen, the place's Ground), no zone file.
            if (!File.Exists(Path.Combine(DataFiles.Dir, "zones", cine.Zone, "zone.json"))) continue;
            var zone = ZoneMeta.Load(cine.Zone);
            if (zone.Colliders.Count == 0) continue;
            foreach (var h in CinePaths.Blockers(cine, zone.Colliders))
                if (!Known.Contains($"{cine.Id}:{h.Collider.X:0.0},{h.Collider.Z:0.0}"))
                    bad.Add($"{cine.Id}: {h.Where} meets collider at ({h.Collider.X:0.0}, {h.Collider.Z:0.0}) tag {h.Collider.Tag}");
        }
        Assert.True(bad.Count == 0, string.Join("\n", bad));
    }

    static CineFile Walk() => CineFile.Parse("""
        {"id":"t","zone":"x","marks":{"a":[0,0,0],"b":[0,10,0],"end":[0,10,0]},
         "cast":{"her":{"kind":"survivor","mark":"a"}},
         "shots":[{"id":"S","dur":4,"cues":[{"do":"move","to":"b"},{"do":"move","to":{"mark":"her","off":[1,0,0]}}]}],
         "end":{"her":"end"}}
        """);

    [Fact]
    public void A_collider_on_the_walk_is_found_and_one_beside_it_is_not()
    {
        var on = new ColliderDef { Kind = ColliderKind.Box, X = 0, Z = 5, Hw = 0.5, Hd = 0.5 };
        var beside = new ColliderDef { Kind = ColliderKind.Circle, X = 3, Z = 5, R = 0.5 };
        var skipped = new List<string>();
        var hits = CinePaths.Blockers(Walk(), [on, beside], skipped);
        Assert.Single(hits);
        Assert.Same(on, hits[0].Collider);
        Assert.Equal("walk", hits[0].Where);
        Assert.Single(skipped);  // the offset-from-her form needs a scene
    }

    [Fact]
    public void A_collider_ahead_of_the_end_mark_is_found_and_one_behind_it_is_not()
    {
        // The end mark faces +z (heading 0); the walk is a point, so only the runway can hit.
        var f = Walk();
        f.Shots.Clear();
        f.Marks["end"] = [0, 0, 0];
        var ahead = new ColliderDef { Kind = ColliderKind.Circle, X = 0.5, Z = 2, R = 0.3 };
        var behind = new ColliderDef { Kind = ColliderKind.Circle, X = 0, Z = -2, R = 0.3 };
        var hits = CinePaths.Blockers(f, [ahead, behind]);
        Assert.Single(hits);
        Assert.Same(ahead, hits[0].Collider);
        Assert.Equal("runway", hits[0].Where);
    }
}
