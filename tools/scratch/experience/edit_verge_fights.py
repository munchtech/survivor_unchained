"""Replace the Verge's story-fight specs with StoryFights (one-off edit)."""
import re, sys

path = sys.argv[1]
src = open(path, encoding="utf-8").read()
start = src.index("    ArenaSpec Story(string id, string name, string people, int seed")
end = src.index("    /* ------------------------------------------------------ ember scars -- */")
new = '''    /// <summary>The story's fights, where each stands in the wood (StoryFights says when each is
    /// open and what its arena is; the night calls them from anywhere).</summary>
    void MakeStoryFights()
    {
        foreach (var f in StoryFights.All)
            StoryFight(f.Id, V(f.Spot), f.Reach, f.Verb, f.Place, () => f.Open(C),
                () => { var p = B!.Player; return StoryFights.Spec(f.Id, C, "verge", p.X, p.Z, p.Facing); });
    }

'''
src = src[:start] + new + src[end:]
open(path, "w", encoding="utf-8", newline="").write(src)
print("ok", len(src))
