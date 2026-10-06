import os, re
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"


def edit(rel, pairs, regex=()):
    p = os.path.join(G, rel)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, (rel, s.count(old), old[:70])
        s = s.replace(old, new, 1)
    for pat, rep in regex:
        s = re.sub(pat, rep, s)
    open(p, "w", encoding="utf-8", newline="").write(s)


edit(r"logic\Cinema\CineFile.cs", [(
'''    public string Actor => Str("actor") ?? "her";''',
'''    /// <summary>Whom it is done to (a cast name; a crowd's name is each of them).
    /// Filled from "actor" by the JSON: a key a property claims never reaches Args.</summary>
    public string Actor { get; set; } = "her";''')])

edit(r"src\Game\GameCinema.cs", [(
'''            var args = new Dictionary<string, JsonElement>(c.Args ?? new()) { ["actor"] = JsonSerializer.SerializeToElement(who) };
            return new CineCue { At = c.At, Do = c.Do, When = c.When, Skip = c.Skip, Args = args };''',
'''            return new CineCue { At = c.At, Do = c.Do, When = c.When, Skip = c.Skip, Args = c.Args, Actor = who };''')],
    regex=[(r'\n                    GD\.Print\(\$"DBG place[^\n]*', '')])
print("ok")
