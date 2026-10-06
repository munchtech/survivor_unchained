from ed import sub
from js import load, save
sub('tests/Explorer/Playthrough.cs', [
("""            case "craft": return false;
            case "sellpelts": case "bounty": return J.Service(a, B);""",
"""            case "craft": case "still": return false;
            case "sellpelts": case "bounty": case "slurry": return J.Service(a, B);"""),
])
g = load("dialogue")
f = g["snib"]["nodes"]["first"]["choices"]
g["snib"]["nodes"]["first"]["choices"] = [c for c in f if c.get("action") != "slurry"]
save("dialogue", g)
