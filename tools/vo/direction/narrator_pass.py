"""The story lead's narrator pass (WRITING_PASS.md 18): the narrator never
shows a feeling. Every one of his own lines is played plain; its note says
only what the line does, its pace and where the pauses fall; pauses are "…"
in the text to record; and he whispers only four times. Run once; kept as
the record of the pass.

    python tools/vo/direction/narrator_pass.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import lines as lines_mod  # noqa: E402

# His four hushes: the jaw, the Warden, "Praying.", the skull.
WHISPER = {"say.178e6dd0ad78", "say.f67dd9f6e97c", "say.b76e3053dc5f", "say.8591ecfe4019"}
# Where a pause falls: (before, after) a phrase.
PAUSE = {
    "dlg.cin_drowned_fire.prints.0": ("None go down to it.", None),
    "say.2d8b284f0b0e": ("None go down to it.", None),
    "say.4d8a46e7502e": (None, "For now."),
    "say.2b72fa1dd85e": ("They were waiting.", None),
    "say.f67dd9f6e97c": (None, "in the ford"),
    "say.8c74ea2b0476": ("You try to call up your mother's face", None),
    "say.060466d9cefd": ("You watch it long enough", None),
    "say.b76e3053dc5f": (None, "Not breathing."),
    "say.384c340b6b6d": ("The door is listening.", None),
    "say.6e1fab16785e": ("None coming away.", None),
}
NOTE = {
    "dlg.cin_drowned_fire.bedroll.0": "One plain fact, close.",
    "dlg.cin_drowned_fire.prints.0": "Two plain facts; a pause, then 'None go down to it.' on its own.",
    "dlg.cin_drowned_fire.frost.0": "Plain.",
    "say.dabd6c78b40d": "The book's three lines read as written words, plainly, one after another.",
    "say.178e6dd0ad78": "A hush: one of his four whispers.",
    "say.3dcd3f3caa00": "Two plain sentences; the second as plain as the first.",
    "say.4d8a46e7502e": "'For now.' on its own, then a pause; the road north plainly.",
    "say.2b72fa1dd85e": "Three images, each given its own room; a pause before 'They were waiting.'",
    "say.77eb67f9e183": "Even; the last sentence slower: it turns to look at you.",
    "say.0663505a2971": "Plain, the same pace throughout; the facts do the grief. No catch before 'twelve at most'; 'and new boots' no softer than the rest.",
    "say.1e2fc7986134": "The fight is over: a breath before it. Then water, and a cold blue light, plainly.",
    "say.f1f67faea5fb": "Plain; 'The graves are listening.' said as simple fact.",
    "say.f67dd9f6e97c": "A hush: one of his four whispers. A pause after 'in the ford'; 'with a lamp in its fist' plain.",
    "say.33579e176a7e": "After the fight, unhurried; 'full of cold light' plain.",
    "say.3eba0841cd10": "Dawn, plainly; 'then gold' given room, no warmer than the rest.",
    "say.8c74ea2b0476": "The rules plainly; 'from nothing.' level. A pause before the mother's face, and that sentence no softer than the rest.",
    "say.24c69afd4e5e": "One plain fact.",
    "say.2d8b284f0b0e": "A pause before 'None go down to it.'",
    "say.c4d495431666": "Low and level, not triumphant.",
    "dlg.cin_first_light.back.0": "Plain and slow.",
    "dlg.cin_first_light.face.0": "Plain and slow; the strangeness is in the words.",
    "dlg.cin_first_light.baking.0": "Dawn, plainly.",
    "say.ac8270282f9f": "Still and level.",
    "say.3ff82d4e2ac7": "The second sentence a shade quicker: every wolf is on its feet.",
    "say.3869640818fe": "Plain; the second sentence is fact, not reproach.",
    "say.6ea507a14576": "Low and level.",
    "say.f45eec417fcc": "Plain; the ordinary details do it.",
    "say.2133e8a51219": "Plain; no comment in the voice.",
    "say.060466d9cefd": "The size given slowly, a phrase at a time. A pause before 'You watch it long enough'; the end flat.",
    "say.b76e3053dc5f": "A hush: one of his four whispers. 'slow, patient, enormous' each its own beat; a long pause after 'Not breathing.'; 'Praying.' barely voiced.",
    "say.0b5e75f9dfa0": "Plain; 'Wolves do not drive wagons.' as simple fact.",
    "say.e6c4fb3a8998": "Short observations; a pause before 'Under the seat'.",
    "say.20dc615919d1": "Short; 'Toward the ravine.' a shade lower.",
    "say.cfa493798ba7": "Plain and slow.",
    "say.8e845892b699": "A list, plainly; the last sentence slower.",
    "say.52d0f1dfa274": "Plain.",
    "say.7197a1b189a3": "Three senses, unhurried.",
    "say.84f6c2c74004": "Short observations; a slight lift on 'the drag-marks of lamps' (a clue).",
    "say.48cdd82e6c0b": "Low and close, as if not to wake them. A pause before 'the way they have waited for everyone'.",
    "say.4acad56ca838": "'One at a time' slow; 'not go off' flat and quiet.",
    "say.769a1c759f88": "Tight and quick; 'Run.' short, not shouted.",
    "say.384c340b6b6d": "'like an eye opening' slower; a pause before 'The door is listening.'",
    "say.9757e1dab88e": "Plain; the last clause level.",
    "say.66cdbe61b828": "The inscription read slowly as old written words; 'all empty' quiet.",
    "say.20b15596c09c": "The Latin said slowly, as old words.",
    "say.82b1e8294244": "Plain.",
    "say.8591ecfe4019": "A hush: one of his four whispers.",
    "say.6e1fab16785e": "The token a careful find; a pause before 'None coming away.'",
    "say.b40ac14379d8": "Slow; 'cold as snow' no softer than the rest.",
    "say.1a95cdeef839": "Plain; the nails are the detail.",
    "say.75abd0854536": "Plain.",
    "say.fccd00002739": "Plain.",
    "say.f1bc8c3f22ed": "Each stopping its own short sentence.",
    "say.a4755c96100b": "Level and quiet throughout, 'Most of them do not crawl far.' included.",
    "say.26621b48a47e": "Level; a pause before 'and then there is only the fire', said low.",
    "say.0622cbb5851c": "Quick on the fire, slower on the glade.",
    "say.005625eee2b8": "The effort, then slower on the glade.",
    "say.cc4a3505429e": "Still and slow.",
    "say.e08ae8c1e46c": "Plain; 'most of them' level.",
    "say.6947705bd0e4": "Read 'M. + J.' as letters: 'em and jay'.",
    "say.8b004f74544d": "Plain; the ledger line level.",
    "say.ff981a5b72be": "Quiet and careful.",
    "say.546ec60933f6": "Three strokes, each its own beat; 'and steps back, and back.' level.",
    "say.a5b99f61e011": "The note read as written words: 'Keep the lights lit.' Then the initial: 'C.'",
    "say.8c1f7c369819": "A list of sensations, unhurried; 'News travels fast here.' plain.",
    "say.a49e30d2ba1e": "Plain; a slight lift on 'places the road forgets'.",
    "dlg.chid.relight.0": "The Order's words said with care; the kettle line plain.",
    "dlg.tam.fetch.0": "Plain; 'But he comes.' short.",
    "dlg.maeca.blind.1": "Low and close, unhurried; he is not in the bed. Her words are hers.",
    "dlg.maeca.blind.2": "Low and close, unhurried; the boots one action at a time.",
    "dlg.maeca.blind_fire.0": "One action at a time; the look across the fire held.",
    "dlg.maeca.watch_only.0": "Plain and slow.",
    "dlg.maeca.blind2_feet.0": "The scars described plainly; her words are hers.",
    "dlg.maeca.blind2_let.0": "Plain.",
    "dlg.maeca.blind_dark.3": "Plain.",
    "dlg.sella.night.1": "Low and close, discreet; 'She is dressed, and counting.' plain. Her word is hers.",
    "dlg.sella.night.2": "Low and close, discreet.",
    "dlg.sella.night.3": "Low and close, discreet.",
    "dlg.sella.free_night.2": "Low and close, slower; the look given room.",
    "dlg.sella.stairs.0": "Plain.",
    "dlg.sella.stairs_room.0": "Plain; her words are hers.",
    "dlg.sella.stairs_room.2": "Plain; 'cellar floor' level.",
    "dlg.sella.stairs.1": "Plain.",
    "dlg.sella.stairs.2": "Plain and brisk.",
    "dlg.sella.rest_dark.0": "Low and close; the watching very quiet.",
    "dlg.sella.free_stairs.0": "The creak 'loud as a shout' given its beat; then quieter.",
    "dlg.sella.free_sit.0": "Plain and slow.",
    "dlg.sella.free_sleep_bed.0": "Low and close.",
    "dlg.sella.free_bolt.0": "Plain; her word is hers.",
    "dlg.sella.free_m_kiss.0": "Plain; her words are hers.",
    "dlg.rav.back_room.0": "Plain; the moving jar and the trophy needle as plain facts.",
    "dlg.keegan.supper_table.0": "Plain and slow.",
    "dlg.greymuzzle.first.0": "Still; a long pause after 'for a long time'; the last image very quiet.",
    "dlg.greymuzzle.show.0": "Plain and close; 'and cannot' after a small pause. It ends on him waiting.",
    "dlg.greymuzzle.show.1": "As show.0; the lip lifting given its beat.",
    "dlg.greymuzzle.ally.0": "'He is not coming.' on its own. 'They are his answer.' plain.",
    "dlg.greymuzzle.again.0": "Flat and final.",
    "dlg.greymuzzle.again.1": "Plain.",
    "dlg.greymuzzle.again.2": "Plain.",
    "dlg.greymuzzle.again.3": "Plain.",
}


def with_pauses(text: str, before: str | None, after: str | None) -> str:
    if before and before in text:
        text = text.replace(before, "[beat] " + before, 1)
    if after and after in text:
        text = text.replace(after, after + " [beat]", 1)
    return text


def main():
    man = {l["id"]: l for l in lines_mod.build()}
    files = {f: json.load(open(os.path.join(HERE, f), encoding="utf-8")) for f in os.listdir(HERE) if f.endswith(".json")}
    changed = set()
    for f, d in files.items():
        for k, v in d.items():
            line = man.get(k)
            if not line or line.get("voice") != "narrator" or line.get("skip"):
                continue
            v["emo"] = "plain"
            if k in NOTE:
                v["note"] = NOTE[k]
            if v.get("vol") == "hushed" and k not in WHISPER:
                v["vol"] = "quiet"
            if k in WHISPER:
                v["vol"] = "hushed"
                v["whisper"] = True
            if k in PAUSE and len(line.get("segments", [])) == 1:
                v["beats"] = with_pauses(line["segments"][0]["text"], *PAUSE[k])
            changed.add(f)
    for f in changed:
        with open(os.path.join(HERE, f), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("{\n" + ",\n".join(f" {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in files[f].items()) + "\n}\n")
    print("narrator pass:", ", ".join(sorted(changed)))


if __name__ == "__main__":
    main()
