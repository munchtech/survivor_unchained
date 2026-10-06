import json
B = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af7a79bc783cca7bc\docs\cinematics\shoot\boards"
NEW = {
 "c02": {
  "3": "a single panel, extreme close-up insert: one ancient armoured gauntlet, black with river slime and hung with weed, rising out of dark water and gripping a lamp that is a square cage of clean new black forged iron with sharp unrusted edges and a small cold pale blue flame inside; the water surface below trembling in rings; nothing else in frame",
  "7": "profile two-shot by a misty river ford at night showing their huge difference in size: {warden} is a giant nearly three times her height, bending far down from above over {her} who stands only as tall as his waist; he lifts his square black iron lamp with its cold pale blue flame down to her upturned face to look at her; she holds her round shield up between them and does not step back",
  "8": "extreme close-up of a young woman's face filling the frame, eyes and nose and lips only, lit by a cold pale blue lamp held very close: a tiny blue flame reflected in each of her eyes, wet dark red hair across her brow, a strand of green river weed caught in the blue light; her lips parted and no breath showing at all; faint warm red on the other cheek",
  "12": "medium wide shot pulling up and back over a misty river ford at night: {warden}, a giant nearly three times her height, setting his greatsword in guard in the water, the single square black iron lamp with its cold pale blue flame in his left fist; {her} small before him with her round shield raised; blue lamp posts and mist around them"
 },
 "c03": {
  "7": "over the shoulder from behind one young woman with long dark red hair and steel pauldrons, her back and shoulder in the near foreground: in the misty air before her a fist-sized glowing stone of cold white-blue light drifts toward her like a thing finding its way, and her own bare hand rises into frame toward it; dark river behind",
  "9": "medium shot on a dark river ford at night: the mud of the riverbed bursting upward in a spray of earth, gravel and water, and {grim} erupting out of it up to his waist, snatching a glowing fist-sized stone of cold white-blue light out of the air with both long arms and hugging it to his chest with glee; a woman's armoured arm and reaching hand at the frame edge",
  "11": "medium shot on a dark river ford: {grim} diving head first down into a hole in the churned mud of the riverbed, only his back, legs and kicking feet still showing, the glowing white-blue stone clutched under him lighting the mud from below as he goes down; his little orange lamps swinging",
  "13": "medium shot of one young woman alone, {her}, standing knee deep in a shallow misty river ford in the grey before dawn, sword lowered, looking down at the water; the camera pulling up and back; mist on the water"
 }
}
for k, shots in NEW.items():
    p = rf"{B}\{k}.json"
    d = json.load(open(p, encoding="utf-8"))
    d["shots"].update(shots)
    open(p, "w", encoding="utf-8", newline="\n").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
    print(k, list(shots))
