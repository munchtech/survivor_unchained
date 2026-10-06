"""Bring the opening cinematics' directions into line with docs/cinematics C01-C04
and give each the cut's target length (the cinematics lead's windows)."""
import json
import re

P = "tools/vo/direction/additions.json"
text = open(P, encoding="utf-8").read()

TIME = {
    "dlg.cin_drowned_fire.bedroll.0": [2.4, 2.8],
    "dlg.cin_drowned_fire.prints.0": [6.0, 7.0],
    "dlg.cin_drowned_fire.frost.0": [2.6, 3.2],
    "dlg.cin_none_cross.call.0": [6.4, 7.6],
    "dlg.cin_none_cross.lie_down.0": [1.0, 1.4],
    "dlg.cin_none_cross.none.0": [2.6, 3.4],
    "dlg.cin_heart_goes_down.morning.0": [1.2, 1.6],
    "dlg.cin_heart_goes_down.nobodys.0": [2.4, 3.0],
    "dlg.cin_heart_goes_down.downstairs.0": [2.0, 2.6],
    "dlg.cin_heart_goes_down.grateful.0": [3.2, 4.0],
    "dlg.cin_first_light.back.0": [3.6, 4.2],
    "dlg.cin_first_light.face.0": [4.6, 5.4],
    "dlg.cin_first_light.baking.0": [2.4, 3.0],
    "dlg.cin_first_light.dawn.0": [2.4, 3.0],
}
# The narrator's notes are the story lead's and final; only the windows are added to his.
NEW = {
    "dlg.cin_drowned_fire.prints.0": {"time_note": "about 0.7 s of pause before 'None go down to it.'"},
    "dlg.cin_none_cross.call.0": {
        "emo": "sung, far off", "intent": "the Order's evening call, slowed to a dirge, heard through water", "pace": "very slow",
        "vol": "hushed", "fx": "underwater",
        "note": "Sung low, as a dirge: two phrases of about three seconds with a short breath between; the second trails off as he rises.",
        "time_note": "two phrases of about 3.0 s with 0.8 s between, the second trailing off"},
    "dlg.cin_none_cross.lie_down.0": {
        "emo": "quiet, gentle", "intent": "the Order's word for the dead, said over a grave", "pace": "very slow", "vol": "quiet",
        "note": "Not a threat: said to her as you would say it over a grave."},
    "dlg.cin_none_cross.none.0": {
        "emo": "tired, final", "intent": "the ford's rule, not a threat", "pace": "slow", "vol": "quiet",
        "note": "Every word set down like a stone; no louder than 'Lie down.' The capitals are the subtitle's, not the performance's.",
        "beats": "None. [beat] Cross. [beat] After dark."},
    "dlg.cin_heart_goes_down.morning.0": {
        "voice": "warden_man", "emo": "tired, lost", "intent": "the man under the Warden asks the lamp", "pace": "slow", "vol": "quiet",
        "note": "Not the giant's voice: a plain, tired man of sixty, the accent worn off, no boom. Quiet enough that the subtitle is the only certain thing."},
    "dlg.cin_heart_goes_down.nobodys.0": {
        "emo": "delight", "intent": "Grimtunnel finds the heart still lit", "pace": "quick", "vol": "raised",
        "note": "Delight, a child's at a pie."},
    "dlg.cin_heart_goes_down.downstairs.0": {
        "emo": "curious, the glee gone", "intent": "Grimtunnel smells her", "pace": "slow", "vol": "quiet",
        "note": "A sniff before it; the glee gone, curious. Then the laugh in the breath after.",
        "beats": "[sniff] ...You smell like downstairs. [chuckle]",
        "time_note": "the words 1.6 to 2.0 s, after the sniff"},
    "dlg.cin_heart_goes_down.grateful.0": {
        "emo": "glee, then caught short", "intent": "he takes it down", "pace": "measured", "vol": "level",
        "note": "Half over his shoulder as he dives. 'surface-m—' breaks off: he cannot finish 'meat' at her. A sniff, then the rest to himself.",
        "time_note": "broken at 'surface-m'"},
    "dlg.cin_first_light.face.0": {"time_note": "the cut then holds three seconds of silence"},
}
for lid, win in TIME.items():
    m = re.search(r'^ "' + re.escape(lid) + r'": (\{.*\}),?$', text, re.M)
    assert m, lid
    d = json.loads(m.group(1))
    d.update(NEW.get(lid, {}))
    d["time"] = win
    line = m.group(0)
    comma = "," if line.endswith(",") else ""
    text = text.replace(line, f' "{lid}": ' + json.dumps(d, ensure_ascii=False) + comma)
open(P, "w", encoding="utf-8", newline="\n").write(text)
json.loads(text)
print("ok")
