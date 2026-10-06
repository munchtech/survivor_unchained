"""The two banes learned by day, as conversation (the story fights read them): Maeca's fed fires
and Chid's pole. New hub choices go just before each hub's "Goodbye."; new nodes at the end.
Round-trip format checked before writing."""
import json, sys
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9\godot\data\content\dialogue.json"
raw = open(p, "rb").read()
d = json.loads(raw.decode("utf-8"))
def dump(x):
    return (json.dumps(x, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n").encode("utf-8")
if dump(d) != raw:
    sys.exit("round trip differs; not writing")
back = [{"text": "Something else.", "goto": "hub"}, {"text": "Goodbye.", "end": True}]
adds = {
    "maeca": (
        {"text": "If I go into the Hollow after dark?",
         "show": {"all": [{"not": {"fact": "beasts.outcome", "exists": True}}, {"not": {"fact": "greymuzzle", "exists": True}}]},
         "once": "fire", "goto": "fire"},
        {"id": "fire",
         "text": "(She looks at you for a long time.) If you're going in there with a blade, I'll not help you. ...Take fire, and feed it. They won't come near a fire that's fed. That's not for your sake. It's so they don't have to.",
         "effects": [{"set": {"bane.fires": True}}], "choices": back},
    ),
    "chid": (
        {"text": "The old empire. Who were they?",
         "show": {"quest": {"id": "vault", "entry": "chid_empire"}},
         "once": "legion", "goto": "legion"},
        {"id": "legion",
         "text": "Soldiers! The Seventh, the Order's books called them. Very tidy, very old, very... thorough. Oh, and this is the part I liked: they never followed a man. Never. They followed the pole. A bronze hand on a pole, a standard, and wherever it went they went, and if it went down they stood about like a choir that's lost its place. ...I don't know why I'm telling you that. It's a very old book.",
         "effects": [{"set": {"bane.pole": True}}], "choices": back},
    ),
}
for c, (choice, node) in adds.items():
    nodes = d[c]["nodes"]
    if node["id"] in nodes:
        sys.exit(f"{c}.{node['id']} exists")
    ch = nodes["hub"]["choices"]
    at = next(i for i, x in enumerate(ch) if x.get("text") == "Goodbye.")
    ch.insert(at, choice)
    nodes[node["id"]] = node
    print(f"{c}: choice at {at}, node {node['id']}")
open(p, "wb").write(dump(d))
