p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\tools\creatures\boar_build.py"
s = open(p, encoding="utf-8").read()
a = s.index("# How the sculpt sits, read off its pictures")
b = s.index("def save(name):")
s = s[:a] + '''from boar_config import CONFIG, override  # noqa: E402

override(argv[1:])


''' + s[b:]
open(p, "w", encoding="utf-8").write(s)
print("ok")
