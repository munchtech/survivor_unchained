"""THE_EMBER_REVEAL 5.2: Keegan, who names rhetorical figures, notices Vonnra's
name is a kenning. The binders are the ash of the burned morning; nobody says it."""
import json
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7622ae77d19e31dc\godot\data\content\dialogue.json"
d = json.loads(open(P, "rb").read().decode("utf-8"))
k = d["keegan"]["nodes"]
assert "vonnra" not in k
k["vonnra"] = {
    "id": "vonnra",
    "text": "Ash-of-Morrow. A peculiar sort of surname: a kenning, almost. The ash of the morning; what is left when the morning has burned down. ...I have no opinion of her. Chapter two forbids opinions about civilians. I have several.",
    "choices": [
        {"text": "Something else.", "goto": "hub"},
        {"text": "Goodbye.", "end": True},
    ],
}
hub = k["hub"]["choices"]
i = next(i for i, c in enumerate(hub) if c["text"].startswith("What do you want, Dame Keegan"))
hub.insert(i, {"text": "What do you make of Vonnra, the toll-keeper?", "show": {"met": "vonnra"}, "once": "vonnra", "goto": "vonnra"})
open(P, "wb").write((json.dumps(d, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8"))
print("ok")
