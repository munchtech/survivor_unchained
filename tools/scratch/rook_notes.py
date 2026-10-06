"""The story lead's Rook notes (round five) into the direction files, and Rook's wants and hides into cast.json."""
import json
import os

D = "tools/vo/direction"
files = {f: json.load(open(os.path.join(D, f), encoding="utf-8")) for f in os.listdir(D) if f.endswith(".json")}


def where(k):
    return next((f for f, d in files.items() if k in d), "rook.json")


U = {
 "dlg.rook.first.0": {"note": "'Well.' a beat, looking you over: partly for Vonnra's money, and the kindness is real as well. On the Chid sentence she watches your face for how you take 'blue lights going out'. A dry edge on 'bleeding on my step'. No laugh at the end: a breath, and the warmth is in the order itself."},
 "dlg.rook.ford.0": {"emo": "candid, unrepentant", "note": "Lower after the pause, honest. 'Don't look like that, pet' brisk and unrepentant on top, and she changes the subject fast.", "beats": "Not many, this last year. The ford's been bad since the winter. ...Vonnra pays me to tell her who comes up that road, and when. [beat] Don't look like that, pet; she pays everyone for something. I'd told her about you before you'd finished your stew."},
 "dlg.rook.ford2.0": {"note": "'She's never paid me double for anything.' is more than she meant to say. Then she's busy with a cup."},
 "dlg.rook.cb_shrine_lit.0": {"emo": "amused, then brusque", "note": "Amused at Chid. No catch: Rook never cries in front of anyone. A pause after 'My mother's lamp's got a sister again.', then brisk: 'Don't make a habit of it.'", "beats": "Chid came running in this morning without his shoes on. The shrine lamp, he says. My mother's lamp's got a sister again. [beat] ...Your bowl's on the house tonight. Don't make a habit of it."},
 "dlg.rook.valley.0": {"note": "No warmth to spare. 'Ashford was.' on its own. The 'pet' is habit, not softness. The don'ts flat, each one a door closing, with no build.", "beats": "Ashford was. [beat] Half of it went to the Morrow in one night, pet, and the other half the year after, coughing. [breath] Don't ask Holloway about it. Don't ask Maeca. Don't ask a Kerchief, if you meet one. [beat] And don't ask me twice."},
}
changed = set()
for k, v in U.items():
    f = where(k)
    files[f].setdefault(k, {}).update(v)
    changed.add(f)
for f in changed:
    with open(os.path.join(D, f), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("{\n" + ",\n".join(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in files[f].items()) + "\n}\n")
c = json.load(open("tools/vo/cast.json", encoding="utf-8"))
c["voices"]["rook"]["wants"] = "the inn kept and everyone fed"
c["voices"]["rook"]["hides"] = "she has sold every traveller on the ford road to Vonnra, and watched the carters go down it and not come back"
with open("tools/vo/cast.json", "w", encoding="utf-8", newline="\n") as fh:
    json.dump(c, fh, indent=1, ensure_ascii=False)
    fh.write("\n")
print("ok", sorted(changed))
