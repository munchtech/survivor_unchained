"""Notes and beats that quoted words since rewritten, put back on the words the lines now say
(Chid, Pell, Redcowl, Snib, Keegan, Jory, Ysolde): before the story lead reads those packets."""
import glob
import json
import re


def patch(lid, upd, drop=()):
    hit = [p for p in sorted(glob.glob("tools/vo/direction/*.json")) if f'"{lid}"' in open(p, encoding="utf-8").read()][-1]
    t = open(hit, encoding="utf-8").read()
    m = re.search(r'^ "' + re.escape(lid) + r'": (\{.*\}),?$', t, re.M)
    d = json.loads(m.group(1))
    d.update(upd)
    for k in drop:
        d.pop(k, None)
    line = m.group(0)
    t = t.replace(line, f' "{lid}": ' + json.dumps(d, ensure_ascii=False) + ("," if line.endswith(",") else ""))
    json.loads(t)
    open(hit, "w", encoding="utf-8", newline="\n").write(t)
    print("patched", lid, "in", hit)


patch("dlg.chid.woke.0", {"emo": "fond, practised", "intent": "you woke again", "pace": "measured", "vol": "quiet",
      "note": "Not the first time: 'Up again.' easy, fond. Narrator: the kettle already on. 'The carter sends his regards.' the lie, "
              "dry and practised now, a joke he hopes you'll take. Then plain and practical for the warning."})
patch("dlg.chid.woke.1", {"note": "Gentle. Narrator: he isn't looking at you. '...Well. Someone did.' the lie slipping, an "
      "embarrassed little laugh in it. Serious and quiet for the warning."})
patch("dlg.chid.cb_nell.0", {
    "note": "Light and offhand on the singing; 'I always have' is older than he looks, and he doesn't notice saying it. Narrator "
            "plain; three seconds of silence. 'She was very light' barely voiced, one catch on 'light', no sob. '...Sit down a "
            "minute.' quiet, almost asking: he is the one who needs the company.",
    "beats": "I sang it flat. [beat] I always have. [breath] There's always somebody who has the tune. | [silence 3 s] She was "
             "very light. [breath] ...Sit down a minute."})
patch("dlg.chid.cb_nell.1", {
    "note": "'Of course, iron' fond: the half-second before it holds the sting (iron is what drowned her), so don't play the "
            "irony. Narrator plain, no sorrow; then three seconds of silence. 'She was very light' barely voiced, one catch allowed "
            "on 'light', no sob. '...Sit down a minute.' quiet, almost asking: under the care he is the one who needs the company.",
    "beats": "We buried Nell behind the shrine, next to old Ashe. [beat] Brannoc made the marker himself. Iron. [beat] Of course, "
             "iron. | [silence 3 s] She was very light. [breath] ...Sit down a minute."})
patch("dlg.pell.first.0", {"note": "Precise and pleased with himself. The sympathy for Coyle practised: 'Terrible business' "
      "smooth, and the last 'Terrible.' a touch too relished."})
patch("dlg.redcowl.first.4", {"note": "Coarse joke at his sentries' expense. 'Which is it?' a hard edge under the amusement: "
      "he means to find out."})
patch("dlg.redcowl.cages.0", {"note": "A hard man's arithmetic. 'worth-nothings' bitter, 'lass'. A pause; then defensive, "
      "almost wounded: '...Ask them if they're hungry.'"})
patch("dlg.snib.first.0", {"note": "'Oi! OI!' squeaky shouting. Self-important 'Foreman's orders!'. A pause; proud: 'Snib is "
      "the foreman.' Fussy. 'Snib does not know who.' then, deflating, 'Snib knows exactly who.' Then 'What do you want? Quick.'"})
patch("bark.keegan.said.0", {"note": "Muttering 'Chapter four' twice, then a startled, proper 'Good day.'"})
patch("bark.jory.day.2", {"note": "'Were.' alone, chilling."})
patch("dlg.wayfinder.first.0", {
    "note": "Brisk Edinburgh. 'Most only ever buy the one.' dry, a cartographer's sales line, no relish. 'barrows' a touch "
            "faster, no weight: it's her brother's. The last two sentences drier and darker.",
    "beats": "You've the look of someone who'll want a second map. [beat] Good. Most only ever buy the one. [breath] I'm Ysolde "
             "Marrow, and I draw maps of the places the road forgets: woods that eat their own paths, barrows that open after "
             "dark, ravines the Kerchiefs think are theirs. [beat] Each one sworn under an oath. Each one ruled by something that "
             "won't want you there."})
