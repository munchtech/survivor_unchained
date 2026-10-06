import sys
sys.path.insert(0, r'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\uid3')
from edlib import edit

edit('tools/assets/creation_portraits.py', [
    ("""# Her shoulders bare in the face's pictures (the stalker's outfit shows none of itself so high, and
# her head is up in its idle); the hair's go lower, so she wears the warden's mail there.
OUTFIT = 'stalker'
HAIR_OUTFIT = 'warden'""", """# She is always dressed in one of her callings' own outfits (People.HerOutfit's names: warden,
# reaver, arcanist, ranger; any other name builds her bare). The face's pictures: the ranger's,
# which leaves her neck clear and holds her head up in its idle. The hair's go lower: the warden's.
OUTFIT = 'ranger'
HAIR_OUTFIT = 'warden'"""),
])
edit('godot/tools_scenes/Portraits.cs', [
    ('''        string fit = job.ContainsKey("outfit") ? (string)job["outfit"] : "reaver";''', '''        // (one of her callings' own outfits, always: another name would build her bare)
        string fit = job.ContainsKey("outfit") && (string)job["outfit"] is "warden" or "reaver" or "arcanist" or "ranger" ? (string)job["outfit"] : "ranger";'''),
])
