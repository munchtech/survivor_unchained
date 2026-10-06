p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ab0b263c720bdbda8\godot\src\Game\Game.cs"
s = open(p, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in s else "\n"
a = s.index("<<<<<<< HEAD")
b = s.index(">>>>>>> origin/worktree-agent-a9a9c345a35e1fcad") + len(">>>>>>> origin/worktree-agent-a9a9c345a35e1fcad") + len(nl)
new = nl.join([
"        var spoils = SurvivorUnchained.Maps.MapSpoils.Between(mapStart ?? Journey.Ch, Journey.Ch, mapStash ?? World.Stash, World.Stash);",
"        // (pictures and probes of the atlas's pay read it from the log as well)",
"        if (Args.Has(\"shot\"))",
"            GD.Print($\"map paid: {spoils.Gear.Count} gear [{string.Join(\", \", spoils.Gear.Select(g => $\"{Inventory.RarityName(g)} {g.Def}\"))}]; \"",
"                + $\"charts {spoils.Charts.Count}; {string.Join(\", \", spoils.Materials.Select(m => $\"{m.Key} {m.Value}\"))}; gold {spoils.Gold:0}; {r.Gathered}\");",
""])
s = s[:a] + new + s[b:]
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
