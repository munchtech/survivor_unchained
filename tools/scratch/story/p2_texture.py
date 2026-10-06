"""Second pass, texture: one memory, habit or want per main person, and the town at night."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from js import *

D = load("dialogue.json")


def texture(npc, ask, answer, show=None, home="hub", hub="hub"):
    """A question asked once from someone's greeting, with its answer."""
    key = "t_" + npc
    cs = D[npc]["nodes"][hub]["choices"]
    cs.insert(len(cs) - 1, ch(ask, show=show, once=key, goto=key))
    D[npc]["nodes"][key] = node(answer, [ch("Something else.", goto=home), ch("Goodbye.", end=True)])


texture("rook", "Was there ever a Mister Rook?",
        "There was. Drank with the Watch, sang flat, and went up the north road with the last lot that went. I kept his chair by the hearth. I sit in it now. It's a good chair; that's the only reason.")
texture("holloway", "What do you want, Captain? For yourself.",
        "A posting with walls somebody else has to count. A dog. Eight hours' sleep in one go. In that order. ...Don't tell the men about the dog.")
texture("maeca", "What did you hunt, before the wolves?",
        "Men, for the garrison. Deer, for me. Men are easier. They keep to paths and they talk while they walk.")
texture("wenna", "Is there anyone, Wenna? Family?",
        "Three husbands. Buried two, lost one at cards. The one I lost at cards was the best of them, and I've never forgiven the man who won him.")
texture("harlan", "How did Jory come to drive for you?",
        "His mother was my sister. She went with the fever year, and he came to me at eight with a bundle and a cough, and the first thing he ever said to me was \"Do you have a horse?\" ...I had six. He named all of them wrong.")
texture("pell", "Why do you count everything?",
        "My sister kept the books in Ashford. I came up to collect them, after. There wasn't an Ashford to collect them from. So I count. Somebody ought to know what things cost.",
        show=flag("pell", "once:books"))
texture("rav", "Ever think of going back to the Kerchiefs?",
        "Every night, round the fourth cup. Then I remember the latrines, and the lice, and the man who sharpened his teeth for a joke and then couldn't stop, and I have a fifth.")
texture("chid", "What was the Order like?",
        "Loud! Everybody thinks priests are quiet. We sang at breakfast. Brother Aumery could sing bread warm. ...They're all gone now. I keep thinking I'll get used to that. I keep not.")
texture("brannoc", "Who taught you iron?",
        "Mother. Better smith than me. Worse temper. Hammer's hers.")
texture("keegan", "What do you want, Dame Keegan?",
        "To be confirmed. To kneel, and have a knight I respect touch my shoulder with a sword and say \"Dame Keegan\" without the bracket. ...And a bath. The Vigil frowns on baths. Chapter nine. I have underlined it in protest.")
texture("sella", "What do you want, Sella? For yourself.",
        "A house in the south with a door that locks from the inside, and somebody who knocks. Man, woman, I'm not fussy. Just somebody who knocks.")
texture("wayfinder", "Do you ever go in yourself?",
        "Once. A barrow in the Morrow hills, twelve years back. I came out. My brother didn't. I've drawn it eleven times since and I still can't get the corners right.")
texture("tam", "Did your Pa ever find the goat?",
        "No. Her name was Clover and she ate a whole hat once. Pa says the wolves got her. I think she ran off to be a wild goat. I think she's happy.", home="again", hub="again")
save("dialogue.json", D)

N = load("npcs.json")
n = N["npcs"]
n["rook"]["nightBarks"].append("Going up to Sella's? Wipe your boots twice. She's particular about her floor and nothing else.")
n["holloway"]["nightBarks"].append("Quiet on the wall. I hate it quiet.")
n["maeca"]["nightBarks"].append("Somewhere out there an old wolf's coughing. Listen.")
n["harlan"]["nightBarks"].append("Jory hated the dark. Hated it. Slept with a candle till he was fourteen.")
n["pell"]["nightBarks"].append("The numbers don't sleep. Why should I?")
n["rav"]["nightBarks"].append("Last orders were an hour ago. I'm the only one who heard them.")
n["chid"]["nightBarks"].append("The dark's only the part of the day that hasn't happened yet. ...It's taking its time tonight.")
n["vonnra"]["nightBarks"].append("The ford is quiet tonight. It will not stay quiet.")
n["wenna"]["nightBarks"].append("Nightshade's out. So are the idiots.")
n["brannoc"]["nightBarks"].append("Banked. Go away.")
n["keegan"]["nightBarks"].append("I am not frightened of the dark. I am merely monitoring it very closely.")
save("npcs.json", N)
print("texture ok")
