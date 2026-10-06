import os, re
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:100], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

B = 'logic/Content/Boons.cs'
s = open(B, encoding='utf-8').read()

# Passives as things and habits of the valley: (id, new name, new text or None to keep).
passives = [
    ("might", "Legion Bronze", "Old-empire bronze, green at the edges and still the hardest thing in the valley: +10% damage with everything."),
    ("haste", "Trimmed Wick", "A wick trimmed short burns quick: every weapon fires 8% more often."),
    ("fleetfoot", "Toll-Runner's Boots", "Worn thin on the toll road: +10% movement speed."),
    ("greed", "Lampling's Scoop", "Ember, gold and draughts fly to you from 1.2 m farther, and every stone holds 4% more ember. The Dig will want it back."),
    ("vitality", "Morrow Pippins", "A pocketful of the valley's apples: +25 maximum health, and a heal when taken."),
    ("ironhide", "Watch Mail", "From the Watch's stores, never paid for: +3 armour. Each point helps a little less than the last."),
    ("precision", "Night-Eyes", "You see the weak places better in the dark: +7% critical strike chance."),
    ("ferocity", "Wolf-Tooth", "It bites deeper than it should: +25% critical strike damage."),
    ("expanse", "Ford Lamp", "Light thrown wide, like the lamps at the ford: +12% area. Novas, fields, orbits, storms and auras are bigger; chains, beams and blades reach farther."),
    ("duplicity", "Second Shadow", "Everything you send out has a shadow that flies beside it: +1 projectile."),
    ("fortune", "Crossroads Penny", "Left at the crossroads, and picked up again: +10% luck. A fourth card more often, rarer cards, ranks that surge, better drops."),
    ("wisdom", "Wayfinder's Chart", "Every road on it, and some that aren't there yet: +6% ember from every stone, and a redraw with every rank."),
    ("recovery", "Bitterroot", "Chewed slowly, as the hunters do: +0.6 health regenerated per second."),
    ("velocity", "Grey Fletching", "Goose-grey and cut close: projectiles fly 12% faster and land 5% harder."),
    ("perennial", "Evergreen", "+10% duration: fields, gyres, beasts and ground effects last longer."),
    ("evasion", "Fen Step", "Light on soft ground: +7% chance to avoid a blow entirely."),
    ("thorns", "Bramble Coat", None),
    ("serration", "Whetstone", None),
    ("chilling", "The Ford's Cold", "The cold of the ford never quite left you: creatures near you are slowed, more as they come closer."),
    ("searing", "Morning Light", "A holy light sears everything near you twice a second."),
    ("venom", "Ember-Slurry", "What the Dig pours into the stream: damage over time (burning, bleeding, poison, searing) is 12% stronger, and every status takes hold 10% more often."),
    ("kinship", "Pack-Bond", None),
]
# The great blessings whose names said nothing of this world.
greats = [
    ("glass_cannon", "Burn Bright", "45% more damage, and 35% less health. Burn bright, burn short."),
    ("arcane_overflow", "Ember Flood", "Each ember stone you gather has an 8% chance to fire every weapon at once."),
    ("momentum", "The Long Road", None),
    ("from_the_ashes", "Cold, Then Not", "Once a night, a blow that would end you does not. You go cold; then the ember catches, and you rise with half your health while everything near you burns."),
    ("soul_harvest", "They Get Up", "What dies near you sometimes gets up again, on your side, for 14 s (up to six at once)."),
]
for bid, name, text in passives + greats:
    pat = r'(Id = "%s", Name = ")([^"]+)(", Icon[^\n]*\n\s*Text = ")([^"]+)(")' % bid
    m = re.search(pat, s)
    assert m, bid
    s = s[:m.start()] + m.group(1) + name + m.group(3) + (text if text else m.group(4)) + m.group(5) + s[m.end():]
open(B, 'w', encoding='utf-8').write(s)

# Embers that sleep by day: what is carried through the day is banked for the night.
edit('logic/Sim/LevelUp.cs', [
    ('o.Why.Insert(0, $"Attuned: carried by day, it comes in at rank {at}");',
     'o.Why.Insert(0, $"Banked: carried through the day, it wakes at rank {at}");'),
])
s = open('src/Ui/ArtsScreen.cs', encoding='utf-8').read()
for old, new in [
    ('what you carry is attuned for the night.', 'what you carry is banked for the night.'),
    ('"  ·  carried, attuned"', '"  ·  carried, banked"'),
    ('what you carry by day is attuned: the ember offers it in its first drafts', 'what you carry by day is banked: it sleeps in you through the day, the ember offers it in its first drafts'),
]:
    assert s.count(old) == 1, old
    s = s.replace(old, new)
open('src/Ui/ArtsScreen.cs', 'w', encoding='utf-8').write(s)

# The night's hours name its great blessings.
edit('src/Game/GameMenus.cs', [
    ('"The arena begins: anyone can take any of them" : "The fifteenth minute: a second, or the first deepened"',
     '"Dusk: the ember wakes, and any of them is yours" : "Midnight: a second, or the first deepened"'),
])

# Discoveries in the valley's voice.
D = 'logic/Content/Discoveries.cs'
s = open(D, encoding='utf-8').read()
disc = [
    ("frostfire", "Frost-Kindled", None, "Old wives on the ford road say a fire lit on ice burns twice."),
    ("shadowflame", "Barrow-Fire", "Umbral bolts burst where they strike, and the burst burns.", "The carters say the barrow-men burned their dead with a black fire. Nobody asks how they know."),
    ("deadly_brew", "Numbing Draught", "Every thrown knife carries something cold that slows what it cuts.", "A knife dipped in whatever the herb-wife keeps on her coldest shelf."),
    ("tempest_pact", "Storm-Iron", None, "Iron that has been struck by lightning remembers it, the smiths say."),
    ("radiant_gyre", "Morning Wheel", "Every turn of the gyre begins with a pulse of holy light.", "The Order of the Morning Light painted wheels on its chapel doors. Spin one in the light and see."),
    ("truestrike", "Kerchief Fletching", "Arrows curve in flight to find what they were loosed at.", "The Kerchiefs fletch with something that glows. Nobody on the road asks what."),
    ("celestial", "The Moon Grove", "Moon and morning together: an extra moonbeam, and wider rings of light.", "Behind the brambles in the Verge there is a grove where the moon comes down to the ground."),
    ("butchery", "Butchery", None, "A butcher keeps a small knife for opening and a big one for finishing."),
]
for did, name, desc, hint in disc:
    pat = r'(Id = "%s", Name = ")([^"]+)(", Weapons = [^\n]*\n\s*Description = ")([^"]+)(",\s*\n\s*Hint = ")([^"]+)(")' % did
    m = re.search(pat, s)
    assert m, did
    s = s[:m.start()] + m.group(1) + name + m.group(3) + (desc or m.group(4)) + m.group(5) + hint + m.group(7) + s[m.end():]
open(D, 'w', encoding='utf-8').write(s)

# Where each path comes from, in the valley.
P = 'logic/Content/Paths.cs'
s = open(P, encoding='utf-8').read()
edit(P, [('    public string Id = "", Name = "", Text = "";',
          '    public string Id = "", Name = "", Text = "";\n    /// <summary>Who in the valley fights this way (shown in the Book; safe for Act 1).</summary>\n    public string Lore = "";')])
s = open(P, encoding='utf-8').read()
lore = {
    "steel": "The Watch's way, and the old empire's before it: close in, and finish it.",
    "hunt": "As the Kerchiefs take the road and the hunters keep the Verge: from cover, many at once.",
    "pyre": "Ember burns. It is the first thing anyone in the valley learns about it.",
    "rime": "The ford's cold, carried inland.",
    "storm": "The storms come down off the hills in autumn and leave the oaks split to the root.",
    "dawn": "The Order of the Morning Light kept lamps against the dark. One fool of a priest still does.",
    "grave": "What the barrow keeps, and what it lets go of.",
    "wild": "The Verge's brambles, its green water and its sick wolves.",
    "host": "Nothing in the valley fights alone for long: the Pack, the risen, the brambles.",
    "weave": "Moonlight and shadow, sent out to find their own way.",
}
for pid, line in lore.items():
    pat = r'(new\(\) \{ Id = "%s", Name = "[^"]+", Text = "[^"]+",)' % pid
    m = re.search(pat, s)
    assert m, pid
    s = s[:m.end()] + f'\n            Lore = "{line}",' + s[m.end():]
open(P, 'w', encoding='utf-8').write(s)
print('ok')
