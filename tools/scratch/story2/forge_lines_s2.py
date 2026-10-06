"""Brannoc's forge lines in his voice (crafting.json crafters.brannoc.lines), edited in the file's own layout."""
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a035208561a66c171\godot\data\content\crafting.json"
s = open(P, encoding="utf-8", newline="").read()
reps = [
    ('"greet": ["Iron for the shape. Fur for the kind.", "Put it on the anvil.", "Forge is hot. What\'ve you brought."]',
     '"greet": ["On the anvil.", "Forge is hot. Show me.", "Dry day. Iron\'ll take the heat."]'),
    ('"temper": ["Three blows. Four.", "Five blows.", "Two. Enough."]', '"temper": ["Three. ...Four.", "Five.", "Two. Enough."]'),
    ('"first.workIn": ["What a place makes, it answers. Wolf for wolves."]', '"first.workIn": ["What it came off, it guards against. Old rule."]'),
    ('"cage": ["Caged.", "It\'ll sit."]', '"cage": ["Caged. Quiet now.", "It\'ll sit."]'),
    ('"first.rekindle": ["Shards bring the heat back. Dearer every time. Don\'t ask me why."]',
     '"first.rekindle": ["Heat comes back. Costs more each time. Like anything."]'),
]
for a, b in reps:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
open(P, "w", encoding="utf-8", newline="").write(s)
print("ok")
