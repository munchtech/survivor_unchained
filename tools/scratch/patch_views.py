import re

ROOT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a435f4dd0ac80df75\godot\src\Actors"

# ---------------------------------------------------------------- PlayerView
p = ROOT + r"\PlayerView.cs"
s = open(p, encoding="utf-8").read()
rep = [
    ("    // Hers: her own clips and carriage.\n    readonly bool her;",
     "    // Their own clips (hers, or his) and carriage.\n    readonly bool mine;\n    readonly OwnClips own = OwnClips.Her;"),
    ('        her = person.Body == "heroine" && HerClips.Library() != null;',
     "        if (person.Own is { } o) own = o;\n        mine = person.Own != null;"),
    ('                bool own = People.Clip(person, jump).StartsWith(HerClips.Prefix);\n                Full(jump, own ? 1.0',
     '                bool native = own.Owns(People.Clip(person, jump));\n                Full(jump, native ? 1.0'),
    ('                bool own = People.Clip(person, rush).StartsWith(HerClips.Prefix);\n                Full(rush, own ? 1.0',
     '                bool native = own.Owns(People.Clip(person, rush));\n                Full(rush, native ? 1.0'),
    ('tree.AddAnimationLibrary("her", HerClips.Library());', "tree.AddAnimationLibrary(own.Name, own.Library());"),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
s = s.replace("HerClips.Prefix", "own.Prefix").replace("HerClips.Has(", "own.Has(").replace("HerClips.Speed(", "own.Speed(")
for a, b in [("if (her)", "if (mine)"), ("(!her ||", "(!mine ||"), ("(her && ", "(mine && "), (" her && ", " mine && "),
             ("var swings = her ?", "var swings = mine ?"), ("&& !her)", "&& !mine)"), ("!(her && ", "!(mine && ")]:
    s = s.replace(a, b)
left = [l for l in s.splitlines() if re.search(r"[^/]*\bher\b", l.split("//")[0]) and "///" not in l]
print("PlayerView code lines still saying her:", left)
open(p, "w", encoding="utf-8").write(s)

# ---------------------------------------------------------------- PersonView
p = ROOT + r"\PersonView.cs"
s = open(p, encoding="utf-8").read()
rep = [
    ("    void Native(string name) => native = name.StartsWith(HerClips.Prefix) ? 1 : 0;",
     "    void Native(string name) => native = person.Own?.Owns(name) == true ? 1 : 0;"),
    ('        if (person.Body == "heroine" && HerClips.Has($"{person.Calling}_show")) Act(HerClips.Prefix + person.Calling + "_show");',
     '        if (person.Own is { } own && own.Has($"{person.Calling}_show")) Act(own.Prefix + person.Calling + "_show");'),
    ('        if (person.Body != "heroine" || walking || holding || actLeft > 0 || Driven) return;\n'
     '        // Only while she stands in her calling\'s idle.\n'
     '        if (!People.Clip(person, loop).StartsWith(HerClips.Prefix + "idle_")) return;',
     '        if (person.Own is not { } own || walking || holding || actLeft > 0 || Driven) return;\n'
     '        // Only while she stands in her calling\'s idle.\n'
     '        if (!People.Clip(person, loop).StartsWith(own.Prefix + "idle_")) return;'),
    ('        if (HerClips.Has(brk)) Act(HerClips.Prefix + brk);', '        if (own.Has(brk)) Act(own.Prefix + brk);'),
    ('        float natural = run.StartsWith(HerClips.Prefix) ? HerClips.Speed(run[HerClips.Prefix.Length..]) * person.Root.Scale.X : 0;',
     '        float natural = person.Own is { } own && own.Owns(run) ? own.Speed(run[own.Prefix.Length..]) * person.Root.Scale.X : 0;'),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
assert "HerClips.Prefix" not in s and "HerClips.Has" not in s
open(p, "w", encoding="utf-8").write(s)
print("ok")
