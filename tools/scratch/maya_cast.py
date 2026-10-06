"""Add a Maya1 voice description to each part in tools/vo/cast.json (the performer for placeholders)."""
import json
import sys

p = sys.argv[1]
c = json.load(open(p, encoding="utf-8"))
M = {
 "narrator": "Realistic male voice in the 50s age with british accent, an old storyteller. Low pitch, warm slightly gravelly timbre, slow even pacing, calm plain tone.",
 "rook": "Realistic female voice in the 60s age with british accent, a Yorkshire innkeeper. Low pitch, husky lived-in timbre, brisk pacing, dry bossy tone.",
 "holloway": "Realistic male voice in the 40s age with british accent, a tired northern English army captain. Low pitch, hoarse worn timbre, measured pacing, weary stern tone.",
 "maeca": "Realistic female voice in the 30s age with welsh accent, a hunter. Low pitch, quiet level timbre, measured pacing, guarded tone.",
 "wenna": "Realistic female voice in the 70s age with british accent, a West Country village herbalist. Normal pitch, creaky dry timbre, measured pacing, tart tone.",
 "tam": "Realistic male child voice, a nine-year-old boy with british accent from the West Country. High pitch, light timbre, fast pacing, earnest breathless tone.",
 "brannoc": "Realistic male voice in the 50s age with british accent, a Cornish blacksmith. Very low pitch, deep rough timbre, slow pacing, flat gruff tone.",
 "harlan": "Realistic male voice in the 50s age with british accent, a Bristol merchant. Normal pitch, warm rounded timbre, quick pacing, friendly tone.",
 "pell": "Realistic male voice in the 40s age with british accent, a precise London factor. Normal pitch, smooth slightly nasal timbre, measured pacing, polite smiling tone.",
 "rav": "Realistic male voice in the 50s age with scottish accent, a Glasgow tavern doctor. Low pitch, gravelly timbre, conversational pacing, wry tone.",
 "chid": "Realistic male voice in the 30s age with irish accent, a gentle priest. Normal pitch, light bright timbre, fast pacing, delighted tone.",
 "vonnra": "Realistic female voice in the 60s age with british accent, an old aristocrat. Low pitch, smooth airy timbre, very slow pacing, cool controlled tone.",
 "keegan": "Realistic female voice in the 20s age with british accent, a young upper-class knight. Normal pitch, clear bright timbre, measured pacing, formal earnest tone.",
 "sella": "Realistic female voice in the 20s age with british accent, a London courtesan. Low pitch, warm intimate timbre, relaxed pacing, amused knowing tone.",
 "redcowl": "Realistic male voice in the 40s age with scottish accent, a bandit chief. Low pitch, deep booming timbre, conversational pacing, rough confident tone.",
 "snib": "Goblin character, male voice with a rough london accent. High pitch, thin squeaky timbre, very fast pacing, panicky tone.",
 "grimtunnel": "Goblin character, male voice with a rough london accent. Low pitch, gravelly oily timbre, slow savouring pacing, gleeful greedy tone.",
 "lampling": "Small creature character, male voice with british accent. High pitch, dry rasping timbre, fast pacing, frightened tone, whispering.",
 "jory": "Realistic male voice in the 20s age with british accent, a seventeen-year-old Bristol boy. Normal pitch, young unsteady timbre, measured pacing, shaken tone.",
 "ysolde": "Realistic female voice in the 50s age with scottish accent, an Edinburgh cartographer. Normal pitch, crisp educated timbre, brisk pacing, dry tone.",
 "warden": "Ancient monster character, male voice with british accent. Very low pitch, vast booming timbre, very slow pacing, terrible calm tone.",
 "watchman": "Realistic male voice in the 60s age with british accent, a dead northern soldier. Low pitch, dry rasping hollow timbre, slow pacing, worn out tone.",
 "bones": "Ancient skeleton character, male voice with british accent. Low pitch, dry hollow rasping timbre, very slow pacing, quiet tone, whispering.",
 "guard": "Realistic male voice in the 30s age with british accent, a northern town guard. Low pitch, plain gruff timbre, measured pacing, bored tone.",
 "folk_f1": "Realistic female voice in the 40s age with british accent, a northern townswoman. Normal pitch, plain warm timbre, conversational pacing, gossipy tired tone.",
 "folk_f2": "Realistic female voice in the 20s age with british accent, a West Country countrywoman. Normal pitch, bright timbre, conversational pacing, sharp amused tone.",
 "folk_m1": "Realistic male voice in the 50s age with british accent, a northern townsman. Low pitch, rough gravelly timbre, conversational pacing, grumbling tone.",
 "folk_m2": "Realistic male voice in the 70s age with british accent, an old West Country countryman. Low pitch, creaky timbre, slow pacing, wry weary tone.",
 "folk_child_f": "Realistic female child voice, an eight-year-old girl with british accent from the north. High pitch, clear timbre, fast pacing, cheeky excited tone.",
 "folk_child_m": "Realistic male child voice, an eight-year-old boy with british accent from the north. High pitch, bright timbre, fast pacing, cheeky loud tone.",
 "guard_f": "Realistic female voice in the 30s age with british accent, a northern town guardswoman. Low pitch, firm gruff timbre, measured pacing, curt tone.",
 "heroine": "Realistic female voice in the 30s age with british accent from the north. Low pitch, warm slightly husky timbre, measured pacing, dry steady tone.",
 "hero": "Realistic male voice in the 30s age with british accent from the north. Low pitch, quiet slightly rough timbre, measured pacing, dry steady tone.",
 "barrow_lord": "Ancient dead soldier character, male voice with british accent. Very low pitch, hollow dry timbre, very slow pacing, final heavy tone, whispering.",
 "kerchief_woman": "Realistic female voice in the 40s age with scottish accent, a hard refugee. Low pitch, rough timbre, measured pacing, blunt weary tone.",
}
missing = [k for k in c["voices"] if k not in M]
assert not missing, missing
for k, d in M.items():
    c["voices"][k]["maya"] = d
json.dump(c, open(p, "w", encoding="utf-8", newline="\n"), indent=1, ensure_ascii=False)
open(p, "a", encoding="utf-8", newline="\n").write("\n")
print("ok", len(M))
