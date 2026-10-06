"""Fold the story lead's batch-2 notes into tools/vo/direction (one entry per line kept)."""
import glob
import json
import os
import sys

D = sys.argv[1]
files = {p: json.load(open(p, encoding="utf-8")) for p in glob.glob(os.path.join(D, "*.json"))}


def where(k, default):
    for p, d in files.items():
        if k in d:
            return p
    return os.path.join(D, default)


NB = "Narrator plain: the narrator never shows a feeling."
U = {
 # Chid
 "dlg.chid.cb_nell.1": ("chid.json", {"emo": "quiet grief, held", "intent": "they buried Nell", "pace": "slow", "vol": "quiet",
   "wants": "to look after the one who put her down", "hides": "he knows what the irons are for, and he was at the ford the night she got up",
   "note": "'Of course, iron' fond: the half-second before it holds the sting (iron is what drowned her), so don't play the irony. Narrator plain, no sorrow; then three seconds of silence. 'She was very light' barely voiced, one catch allowed on 'light', no sob. His ordinary self comes back on 'Not on the step'; under the care he is the one who needs the company, and 'By me.' is quiet, almost asking.",
   "beats": "We buried Nell behind the shrine, next to old Ashe. [beat] Brannoc made the marker himself. Iron. [beat] Of course, iron. | [silence 3 s] She was very light. [breath] ...Sit down a minute. [beat] Not on the step. [beat] Here. [beat] By me."}),
 "dlg.chid.cb_nell.0": ("chid.json", {"emo": "quiet grief, held", "intent": "after the burial he sang at", "pace": "slow", "vol": "quiet",
   "wants": "to look after the one who put her down", "hides": "he knows what the irons are for; 'somebody' is Vonnra's alto",
   "note": "Light and offhand on the singing; 'I always have' is older than he looks, and he doesn't notice saying it. Narrator plain; three seconds of silence. 'She was very light' barely voiced, one catch on 'light', no sob. 'By me.' quiet, almost asking.",
   "beats": "I sang it flat. [beat] I always have. [breath] There's always somebody who has the tune. | [silence 3 s] She was very light. [breath] ...Sit down a minute. [beat] Not on the step. [beat] Here. [beat] By me."}),
 "dlg.chid.first.0": ("chid.json", {"emo": "overjoyed surprise", "intent": "greets a fellow of his dead Order", "pace": "quick", "vol": "raised",
   "wants": "company, a lit Order lamp, family", "hides": "what he is, how old, what the lamps burn",
   "note": "The catch of joy on 'Lit!'. No rue on 'which is fair': he likes the name, and the laugh is delight on the out-breath. 'It used to work.' cheerful and practical, like a man reporting a broken pump; the sadness belongs to the listener. Chid is never cynical and never self-pitying.",
   "beats": "Oh! [beat] A lantern of the Order! [breath] Lit! Oh, sit down, sit, sit. I'm Chid. They call me the Fool, which is fair. [laugh] This is the shrine of the Morning Light. [beat] It used to work."}),
 "dlg.chid.first.1": ("chid.json", {"emo": "delighted surprise", "intent": "greets a visitor", "pace": "quick", "vol": "level",
   "wants": "company", "hides": "what he is, how old, what the lamps burn",
   "note": "Bright 'Oh!'. He likes the name 'the Fool'; the laugh is delight. 'It used to work.' cheerful and practical.",
   "beats": "Oh! A visitor. [beat] Hello! I'm Chid. They call me the Fool, which is fair. [laugh] This is the shrine of the Morning Light. [beat] It used to work."}),
 # Maeca
 "dlg.maeca.first.0": ("maeca.json", {"emo": "quiet recognition", "intent": "finds a fellow hunter", "pace": "measured", "vol": "quiet",
   "wants": "someone who reads ground the way she does", "hides": "the Pack are hers",
   "note": "Level, a hunter's half-voice. 'Hunter?' barely a question: she is confirming what she has read, no surprise. 'They're running.' plain and certain. 'before you ask' dry, said a thousand times, not a joke she enjoys.",
   "beats": "You walk like someone who's followed a thing to its den. [beat] Hunter? [beat] Then you've seen it too, out there. They're not hunting. [beat] They're running. [breath] Maeca. [beat] Barefoot, before you ask."}),
 "dlg.maeca.first.1": ("maeca.json", {"emo": "cold contempt", "intent": "you wear wolves", "pace": "measured", "vol": "quiet",
   "wants": "you out of her Hollow", "hides": "those were her Pack",
   "note": "Quiet and final. 'and so can they' a fact, which is what makes it the threat. 'What do you want?' drops, no question lift.",
   "beats": "That cloak's made of wolves. I can smell it from here, [beat] and so can they. Maeca Barefoot. What do you want?"}),
 "dlg.maeca.first.2": ("maeca.json", {"emo": "weary contempt", "intent": "dismisses another bounty-hunter", "pace": "measured", "vol": "quiet",
   "wants": "to be taken seriously about the cause", "hides": "she is all that is left of the Ashford garrison",
   "note": "Flat contempt for the bounty; the rule about the problem said plainly. 'before you ask' dry, said a thousand times.",
   "beats": "Another blade for Holloway's bounty? [beat] The Pack aren't the problem. They're what the problem looks like from the road. [breath] Maeca. [beat] Barefoot, before you ask."}),
 "dlg.maeca.blind_walk.0": ("maeca.json", {"emo": "hushed, attentive", "intent": "the walk to the Blind", "pace": "slow", "vol": "quiet",
   "note": "Narrator plain and starlit; a beat before 'and is answered'. Maeca just above a breath, naming neighbours by their voices. " + NB,
   "beats": "...a wolf calls [beat] and is answered. | Him. [beat] And the bitch with the white foot. | She walks on.",
   "segments": [{"voice": "narrator", "text": "She goes out by the east gate without a lamp, and you follow her along the Old Road past the wreck, by starlight and the white of the frost. She walks barefoot on ground that would cut you through your boots, and doesn't make a sound. Once she stops, and you stop, and somewhere off in the Hollow a wolf calls and is answered."},
                {"voice": "maeca", "text": "Him. And the bitch with the white foot."},
                {"voice": "narrator", "text": "She walks on."}]}),
 "dlg.maeca.blind_walk.1": ("maeca.json", {"emo": "plain", "intent": "she lets you lead", "pace": "slow", "vol": "quiet",
   "note": NB + " The gift is the fact itself; don't lean on it.",
   "beats": "The Old Road, the wreck, the frost. [beat] You know the way now, and she lets you walk in front, [beat] which she has never done."}),
 "dlg.maeca.blind_dark.0": ("maeca.json", {"emo": "level, nearly funny", "intent": "you're cold", "pace": "slow", "vol": "hushed",
   "note": "The inversion (your skin colder than her feet) is nearly funny: straight and level, don't darken it. The last sentence hangs, not drops: the player's choice follows.",
   "beats": "Afterwards, in the dark under the hides, she puts her feet against your legs, [beat] and flinches: [beat] you're colder than they are. She starts to take them back—"}),
 "dlg.maeca.blind_dark.1": ("maeca.json", {"emo": "hushed, careful", "intent": "the Pack lies down round you; she asks what you were", "pace": "slow", "vol": "hushed",
   "hides": "she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven",
   "note": "Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.",
   "beats": "...listening the way she listens to the Hollow. [breath] Outside, in the frost, you hear them come: soft feet, a long way round, [beat] and then a sigh, [beat] and then another. ... [beat] She lifts her head. | They don't do that. [beat] Not for me. Not for anyone. | She lies back down, her ear where it was. | You walk quiet. You came into my Hollow and knelt to him, and he let you. [beat] You never talk about before. | Against your chest you feel her lips move, without a sound. | [silence 3 s] What were you?",
   "segments": [{"voice": "narrator", "text": "Later, with the fire down, she lies with her head on your chest, listening the way she listens to the Hollow. Outside, in the frost, you hear them come: soft feet, a long way round, and then a sigh, and then another. The Pack, lying down round the Blind in the dark. She lifts her head."},
                {"voice": "maeca", "text": "They don't do that. Not for me. Not for anyone."},
                {"voice": "narrator", "text": "She lies back down, her ear where it was."},
                {"voice": "maeca", "text": "You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk about before."},
                {"voice": "narrator", "text": "Against your chest you feel her lips move, without a sound."},
                {"voice": "maeca", "text": "What were you?"}]}),
 "dlg.maeca.blind_dark.2": ("maeca.json", {"emo": "hushed, careful", "intent": "she asks what you were", "pace": "slow", "vol": "hushed",
   "hides": "she is counting your heart between her sentences",
   "note": "As blind_dark.1 without the Pack. 'What were you?' careful, no stress on 'were', after a real count of about three seconds.",
   "beats": "...listening the way she listens to the Hollow. | You walk quiet. You never talk about before. | Against your chest you feel her lips move, without a sound. | [silence 3 s] What were you?",
   "segments": [{"voice": "narrator", "text": "Later, with the fire down, she lies with her head on your chest, listening the way she listens to the Hollow."},
                {"voice": "maeca", "text": "You walk quiet. You never talk about before."},
                {"voice": "narrator", "text": "Against your chest you feel her lips move, without a sound."},
                {"voice": "maeca", "text": "What were you?"}]}),
 # Ysolde
 "dlg.wayfinder.first.0": ("ysolde.json", {"emo": "brisk, dry, bookish", "intent": "sells her maps", "pace": "brisk", "vol": "level",
   "wants": "a customer who'll come back", "hides": "she sells the names of those who come back, to feed her brother in his cage",
   "note": "Brisk Edinburgh. The joke about the other sort is dry, a cartographer's sales line, no relish. 'barrows' a touch faster, no weight: it's her brother's. The last two sentences drier and darker.",
   "beats": "You've the look of someone who comes back. [beat] Good. The other sort only ever buy the one map. [breath] I'm Ysolde Marrow, and I draw maps of the places the road forgets: woods that eat their own paths, barrows that open after dark, ravines the Kerchiefs think are theirs. [beat] Each one sworn under an oath. Each one ruled by something that won't want you there."}),
 "dlg.wayfinder.margin.0": ("ysolde.json", {"emo": "brisk, practised", "intent": "asks your name for the margin", "pace": "brisk", "vol": "level",
   "wants": "your name", "hides": "where it goes",
   "note": "Light because practised. 'put you down' means write, and also the other thing: she never hears the second meaning. Narrator: the pen.",
   "beats": "Who came back, from where, how long they lasted, what they carried out. [beat] Name first; [beat] I'm a tidy woman. | Speaking of which. [beat] How do I put you down?"}),
 "dlg.wayfinder.margin_nobody.0": ("ysolde.json", {"emo": "deadpan", "intent": "writes Nobody", "pace": "measured", "vol": "level",
   "note": "On audio the capital N vanishes: give the second 'Nobody' the same name-shape and weight she gave it as she wrote it, with a tiny beat before it; then 'More than most' lands the joke. Deadpan, no chill added.",
   "beats": "Nobody. | You'd be surprised how often [beat] Nobody comes back. [beat] More than most."}),
 "dlg.wayfinder.margin_lark.0": ("ysolde.json", {"emo": "dry, quick", "intent": "names you Lark", "pace": "measured", "vol": "level",
   "hides": "by making a name up she chooses not to sell you: a kindness she won't own",
   "note": "Edinburgh dry and quick, not fond teasing. The kindness is in the choice, not the voice.",
   "beats": "Lark. [beat] You look like a Lark. Larks get up early, [beat] and make a great deal of noise about it."}),
 # Sella: her quoted words in the narration are hers
 "dlg.sella.free_night.1": ("sella.json", {"emo": "tender, quiet", "intent": "a night Sella gives", "pace": "slow", "vol": "hushed",
   "note": "The narrator's, hushed and unhurried: the one night that isn't work, so no patter. " + NB + " Her four words are hers, said into your shoulder.",
   "segments": [{"voice": "narrator", "text": "She doesn't talk the way she talks for money. She doesn't talk at all, at first. She undresses you as if she's never done it before, which is absurd, and she knows it's absurd, and halfway through she laughs into your neck and can't stop. Then she does stop, and the laugh goes somewhere else. She's slower than on her working nights, and less sure, and once she stops altogether with her forehead against yours and just breathes, and you wait, and she goes on. The lamp burns down on its own. Nobody turns it. In the dark, much later, she says into your shoulder,"},
                {"voice": "sella", "text": "You told me anyway,"},
                {"voice": "narrator", "text": "and nothing else, and then she sleeps."}]}),
}
changed = set()
for k, (default, v) in U.items():
    p = where(k, default)
    files.setdefault(p, {})
    old = files[p].get(k, {})
    changed.add(p)
    files[p][k] = {**{x: old[x] for x in ("room",) if x in old}, **v}
for p in changed:
    d = files[p]
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("{\n" + ",\n".join(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in d.items()) + "\n}\n")
print("updated", len(U))
