"""Two small rewrites in Chid's gift: the book is seen before he speaks of it, and his hand goes
over hers on the cover."""
from jsonio_s6 import load, save

d = load("dialogue.json")
N = d["chid"]["nodes"]
N["office"]["text"] = "You've been up the Tower. (He doesn't ask what she told you. He has a small book in both hands, held the way you hold a bird.) I want you to have this. It's only an old office: the watch-hours, what the keepers said at night. Nobody's said them in a long while. (He opens it at the last page, and doesn't look at it.) There's a bit at the end. You'll know it when you need it. ...Not now. It reads better in the dark."
N["office_end"]["text"] = "(He puts his hand over yours, flat on the cover.) Not now, I said! ...It's the end of the watch. One keeper asks, and the other one answers, so nobody has to sit up the whole night on their own. That's what an office is, really. Somebody answering."
save("dialogue.json", d)
print("done")
