import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"
p = os.path.join(G, r"src\Game\GameCinema.cs")
s = open(p, encoding="utf-8").read()
old = '''            if (span.Index != stillShot && player.Local >= (shot.Still ?? span.Dur * 0.6))
            {
                stillShot = span.Index;
                Shots.Want($"{file.Id}_s{shot.Id}", 0.05);'''
new = '''            // --stills N: N frames of each shot, evenly through it (to judge its motion), instead.
            int many = (int)Args.Num("stills", 0);
            if (span.Index != stillShot) { stillShot = span.Index; stillK = 0; }
            double nextStill = many > 0 ? span.Dur * (stillK + 0.5) / many : shot.Still ?? span.Dur * 0.6;
            if (stillK < Math.Max(1, many) && player.Local >= nextStill)
            {
                stillK++;
                Shots.Want($"{file.Id}_s{shot.Id}", 0.05);'''
assert s.count(old) == 1
s = s.replace(old, new)
old = '''        int stillShot = -1, camShot = -1;'''
new = '''        int stillShot = -1, stillK, camShot = -1;'''
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")
