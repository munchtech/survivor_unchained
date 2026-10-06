"""The story lead's words (a7ba8903f4c8261b1), verbatim: Ysolde at her table, the four rulers' things and
their marks' names, Snib on a bad result."""
from ed import sub
J = "data/content/crafting.json"
sub(J, [
    ("""   "closedLine": "The charts are not for strangers.",
   "respectPerCraft": 1,
   "respectFromCraft": 10,
   "lines": {},""",
     """   "closedLine": "I don't put my pen to a stranger's chart. Come and be introduced.",
   "respectPerCraft": 1,
   "respectFromCraft": 10,
   "lines": {
    "greet": ["Lay it flat, and your elbows off it. That ink's still deciding.", "Back from the edges? Show me where you've been.", "Sit. Mind the pens. What's the ground been saying?"],
    "first.ink.before": ["She takes a pen from the jar without looking, dips it, and writes in the margin in a hand too small to read upside down."],
    "first.ink": ["There. Sworn. I don't choose the words, mind; the ground does. I only hold the pen."],
    "ink": ["Sworn.", "There. The ground's had its say.", "Written. It'll pay for that, one way or the other."],
    "first.burn.before": ["She holds the margin to the lamp until the oaths in it brown and lift, brushes them off like crumbs, and writes it fresh."],
    "first.burn": ["Same ground, new oaths. The ground doesn't remember what it swore last time. Neither do I, much."],
    "burn": ["Burned and redrawn.", "Fresh margins. Don't get attached.", "Ask again if you don't like it. I'm paid either way."],
    "first.pin.before": ["She threads a scrap of what that ground gave you onto a long brass pin, and puts it through the margin beside the oath, the way you'd pin a moth."],
    "first.pin": ["Pinned. That one stays put when the rest go up. ...Everybody's got one of those."],
    "pin": ["Pinned.", "That one stays.", "Held. Burn round it all you like."],
    "first.scrape.before": ["She takes a penknife to the margin and scrapes the oath off a little at a time, the way a clerk takes out a name that shouldn't be in the ledger."],
    "first.scrape": ["Gone. It never quite goes, mind. Hold it to the light and you'll still see where it was."],
    "scrape": ["Scraped.", "Off it comes.", "Gone. Mostly."],
    "first.annotate.before": ["She lays the two charts side by side and copies from one to the other in a hand as small as stitching: who went in, where they lay up, what they carried out."],
    "first.annotate": ["Two charts of the one ground are worth more than twice one. People leave things out. ...I put them back in."],
    "first.annotate.after": ["The chart you gave up goes into a drawer, not the fire. She locks the drawer."],
    "annotate": ["Copied over.", "Margins full. That's how I like them.", "Nothing wasted. I'm a tidy woman."],
    "history.ink": ["Sworn in the Wayfinder's hand, day {day}"],
    "history.burn": ["Burned and redrawn at {who}'s table, day {day}"],
    "history.pin": ["An oath pinned at {who}'s table, day {day}"],
    "history.scrape": ["An oath scraped out by {who}, day {day}"],
    "history.annotate": ["Annotated from another chart in {who}'s hand, day {day}"]
   },"""),
    ("""    "steep": ["Steeped. Snib would not wear that.""",
     """    "steep.bad": ["That is not Snib's fault. That is the JAR's fault. ...Snib filled the jar."],
    "steep": ["Steeped. Snib would not wear that."""),
    ('"mark": "of_the_ravine"', '"mark": "of_the_long_chase"'),
    ('"mark": "of_the_wheel"', '"mark": "of_the_muster"'),
])
I = "data/content/items.json"
sub(I, [
    ("""   "name": "Hunt-Scored Bone",
   "kind": "trophy",
   "rarity": 1,
   "icon": "bone",
   "value": 40,
   "description": "The Pack's ruler gnawed it into a pattern. Vonnra can read the hunt in it, and inscribe it into a piece you wear.",""",
     """   "name": "Tally-Bone",
   "kind": "trophy",
   "rarity": 1,
   "icon": "bone",
   "value": 40,
   "description": "A deer's shinbone from a Pack ruler's den, scored end to end with toothmarks in close, even rows, the way a shepherd notches a stick to count. Vonnra can read the hunt in it, and mark a piece you wear with it.","""),
    ("""   "description": "From the lamplings' ruler's own lamp. The light in it fell once, and kept burning where it landed. Vonnra can inscribe it into a piece you wear.",""",
     """   "description": "A lamp's chimney-glass from a lampling ruler, cracked from top to bottom. What was lit in it fell a long way once and went on burning where it landed. It is still warm. Vonnra can mark a piece you wear with it.","""),
    ("""   "name": "Bent Gate-Nail",
   "kind": "trophy",
   "rarity": 1,
   "icon": "key",
   "value": 40,
   "description": "From the barrow-ruler's door, bent where something pushed it aside to come out. Vonnra can inscribe it into a piece you wear.",""",
     """   "name": "Bent Barrow-Nail",
   "kind": "trophy",
   "rarity": 1,
   "icon": "key",
   "value": 40,
   "description": "A square iron nail as long as your hand, from a barrow door, bent double. Somebody nailed that door shut a long time ago. It was opened from inside. Vonnra can mark a piece you wear with it.","""),
    ("""   "name": "Knotted Red Cord",
   "kind": "trophy",
   "rarity": 1,
   "icon": "kerchief",
   "value": 40,
   "description": "Knotted once for every man who stood with the Kerchiefs' ruler. Vonnra can read the crowd in it, and inscribe it into a piece you wear.",""",
     """   "name": "Muster-Cord",
   "kind": "trophy",
   "rarity": 1,
   "icon": "kerchief",
   "value": 40,
   "description": "A length of red cord, knotted once for every name at a muster. Nobody untied the knots for the ones who did not come home. Vonnra can read the crowd in it, and mark a piece you wear with it.","""),
])
sub("logic/Sim/Marks.cs", [
    ('    public const string Ravine = "of_the_ravine";', '    public const string Ravine = "of_the_long_chase";'),
    ('    public const string Gyre = "of_the_wheel";', '    public const string Gyre = "of_the_muster";'),
])
sub("logic/Rpg/Items.cs", [
    ('new() { Id = Sim.Marks.Ravine, Name = "of the Ravine",', 'new() { Id = Sim.Marks.Ravine, Name = "of the Long Chase",'),
    ('new() { Id = Sim.Marks.Gyre, Name = "of the Wheel",', 'new() { Id = Sim.Marks.Gyre, Name = "of the Muster",'),
])
# Snib on a grade lost: his own words over the jar's, except the first time (which has its own).
sub("logic/Play/JourneyCrafting.cs", [
    ("""        if (seen != null) CraftSaid = (CraftSaid ?? new Said(null, null, null)) with { After = seen };""",
     """        if (seen != null) CraftSaid = (CraftSaid ?? new Said(null, null, null)) with { After = seen };
        if (q.Verb == Verb.Steep && q.Outcome == "down" && q.Crafter != "" && CraftSaid is { Before: null } said && Crafting.Line(q.Crafter, "steep.bad") is { } bad)
            CraftSaid = said with { Line = bad };"""),
])
