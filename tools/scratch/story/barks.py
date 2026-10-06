"""Stage 3b: barks and the town's mutterings in the same voices."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from js import *

N = load("npcs.json")
n = N["npcs"]
n["rook"]["barks"] = ["Beds are dry and the stew's hot. That's more than most can say.", "Wipe your boots.", "If you're bleeding, bleed outside.", "Rooms upstairs by the night. By the hour, ask Sella."]
n["holloway"]["barks"] = ["Five a pelt. Fifty for the old grey one.", "Keep to the road, and keep your blade where I can see it.", "Three caravans this month. Three."]
n["holloway"]["nightBarks"] = ["Curfew's not law. Yet.", "Two on the walls, one on each gate. It's not enough.", "Go to bed, traveller.", "Every night I bury somebody's son. Go home."]
n["maeca"]["barks"] = ["They're not hunting. They're running.", "Something's got the whole wood on edge.", "Mind the east road after dark."]
n["maeca"]["nightBarks"] = ["Hear that? No. Neither do I. That's what worries me.", "One more, then I sleep.", "The Pack's loud tonight."]
n["chid"]["barks"] = ["It used to work, you know. The shrine.", "The light's patient. I'm trying to be.", "Morning comes. It always has. I should know."]
n["chid"]["nightBarks"] = ["Even in the dark, the morning's on its way.", "I leave a candle lit. Somebody might need it.", "Can't sleep either?"]
n["rav"]["barks"] = ["I'm a doctor. Don't make me prove it.", "Red cloth's a hard habit to break.", "Buy me a drink and I'll tell you a lie worth hearing.", "Drop your trousers or don't. The leeches aren't fussy.", "Half my patients die. The other half pay."]
n["rav"]["nightBarks"] = ["Night surgery's double. Night anything's double.", "The best stories come after the third cup.", "Pull up a stool. Mind the blood."]
n["harlan"]["barks"] = ["Late. Jory's never late.", "Salt, iron, cloth. Whatever you need, when the wagons come.", "Somebody knows something."]
n["harlan"]["nightBarks"] = ["I keep the books by candlelight. Helps me not think.", "Every wagon on that road's his, in the dark.", "Can't sleep. Won't."]
n["pell"]["barks"] = ["Everything has a price. Most things have two.", "Terrible business, Coyle's caravan. Terrible.", "My warehouse is closed to the public."]
n["pell"]["nightBarks"] = ["Closed. Closed! Come back in daylight.", "A man can't count in peace in this town.", "Who's there?"]
n["wenna"]["barks"] = ["The animals were never like this. Never.", "Bitterroot, bitterroot. Always need more.", "The water tastes wrong this year."]
n["wenna"]["nightBarks"] = ["Moon's up. Good for picking. Bad for knees.", "Mind the nettles in the dark.", "Night air's full of things. Some of them are herbs."]
n["tam"]["barks"] = ["They drank from the stream and fell down.", "Pa says stay in town.", "I told the Watch. The Watch laughed."]
n["brannoc"]["barks"] = ["Good steel's not cheap. Nor's a good pelt.", "Mind the sparks.", "Bring me hides. I'll make you something worth wearing.", "Hit a man with this and he stays hit."]
n["brannoc"]["nightBarks"] = ["Forge is banked. First light.", "Arm aches worse at night. Old iron does.", "Fire keeps me company."]
n["keegan"]["barks"] = ["None pass north. Not yet.", "You are not ready for what is beyond there.", "Probationary. It is a real title."]
n["keegan"]["nightBarks"] = ["Night watch. Probationary night watch.", "Something moved out there. Probably.", "Stand back from the gate, please."]
N["outsiders"]["jory"]["barks"] = ["I thought I'd die in that cage.", "Uncle keeps hugging me. It's a lot."]
save("npcs.json", N)

F = load("folk.json")
for l in F["lines"]:
    if l["text"] == "Pell's been generous lately. With you, mostly.":
        l["text"] = "Pell's been generous lately. With you, especially."
# A trusted face that has not changed in fifty years.
F["lines"].append({"text": "Chid's not aged a day since my mam was a girl. Says it's clean living. Have you SEEN where he lives?"})
save("folk.json", F)

Q = load("quests.json")
Q["beasts"]["entries"]["tam_plea"] = "Tam saw wolves drink from the stream and fall down. \"Something's killing them,\" he says. Nobody believes a child."
save("quests.json", Q)
print("barks ok")
