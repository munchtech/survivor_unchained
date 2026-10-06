"""Check the StoryLint genre-word regex against the committed Verge.cs (which still says "alpha")."""
import re, subprocess
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9"
old = subprocess.run(["git", "-C", WT, "show", "HEAD:godot/logic/Play/Zones/Verge.cs"], capture_output=True, text=True, encoding="utf-8").stdout
said = re.compile(r'(?:Hist\(\s*"[^"]*",\s*|Say\(\s*\$?|Announcement\(\s*\$?)"([^"]*)"')
genre = re.compile(r"\b(alpha|warlord|ganger)s?\b", re.I)
hits = [m.group(1) for m in said.finditer(old) if genre.search(m.group(1))]
print(len(list(said.finditer(old))), "strings read;", hits)
