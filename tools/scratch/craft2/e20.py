from js import load, save
d = load("dialogue")
b = d["brannoc"]["nodes"]
fang = next(c for c in b["hub"]["choices"] if c.get("goto") == "fang")
first = b["first"]["choices"]
if not any(c.get("goto") == "fang" for c in first):
    i = next(k for k, c in enumerate(first) if c.get("text") == "Will you work my gear?")
    first.insert(i + 1, dict(fang))
save("dialogue", d)
