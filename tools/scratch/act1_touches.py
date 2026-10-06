"""Round three: the Act 1 scripts' touches. Run from the worktree root."""
import os

D = os.path.join(os.getcwd(), 'docs', 'cinematics')


def edit(name, pairs):
    p = os.path.join(D, name)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (name, a[:80], s.count(a))
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='\n').write(s)


edit('c01_drowned_fire.md', [
    ("""bedroll prop with a folded blanket; the hare, the lens on a book, the kerchief on
a strap, the lantern; water-closing and drip sounds.""",
     """bedroll prop with a folded blanket; the hare, the lens on a book, the kerchief on
a strap, the lantern; water-closing and drip sounds. The title screen's hooded
stranger by this fire is the survivor at dusk, before the water, and must read as
any survivor: hood up, back to the camera, no calling's silhouette. (Today it is a
female stalker model, which reads as one survivor in particular.)"""),
])

edit('c03_heart_goes_down.md', [
    ("the road's lamps either side of the river (lights 12, 13 and 14).",
     "the road's lamps either side of the river (lights 12, 13 and 14: more of Brannoc's ten irons, hung along the road to the ford, burning ember-blue)."),
    ("- Shot 12: lights 12, 13 and 14 dip together for 0.6 s; the river's rings.",
     "- Shot 12: lights 12, 13 and 14 dip together for 0.6 s; the river's rings. (They are ember in Brannoc's irons, so the dip is the chain's: everything burning the Morrow's light flinches at once. A Watch lamp burning oil would not.)"),
])

edit('c04_first_light.md', [
    ("| A5 | CU | 85 | Static, frontal, low sun from frame right, the birches' shade behind her | She breathes out, and her breath smokes in the cold: a long white plume in the sunlight. She sees it. She breathes again, to see it again. Then the cold reaches her: her shoulders lift, she shivers once, hard. | 5.5 |",
     "| A5 | CU | 85 | Static, frontal, low sun from frame right, the birches' shade behind her | The warmth comes into her all at once, like a lamp turned up: colour in her face, her lips no longer blue. She breathes out, and her breath smokes in the cold: a long white plume in the sunlight. She sees it. She breathes again, to see it again. Then the cold reaches her, now that she can feel it: her shoulders lift, she shivers once, hard. | 5.5 |"),
])

edit('c06_forty_one_mouths.md', [
    ("""- **The prisoners:** three in the cages (62, 84) and the two beside it: a grey
  teamster, a woman, and Jory (fair, freckled, seventeen) in the end cage.""",
     """- **The prisoners:** three in three cages at (62, 84): a grey teamster, a woman,
  and Jory (fair, freckled, seventeen) in the end cage. Beyond Jory's, a fourth
  cage, empty, its door standing open. Nobody looks at it, and no shot is built on
  it: it is at the edge of shot 4, and in the background of the conversation's
  wides. (Ewan, who "did not last"; and where the ones nobody would pay for went.
  Act 2.)"""),
    ("In the end cage, Jory watches the survivor through the bars. | 5.0 |",
     "In the end cage, Jory watches the survivor through the bars. Past him, at the frame's edge, the fourth cage stands open and empty. | 5.0 |"),
])

edit('c07_hammer_stops.md', [
    ("""  (13.4, 14.2); on the wall left of the door (12.3, 12) a rack with two black
  lamp-irons hanging from hooks.""",
     """  (13.4, 14.2); on the wall left of the door (12.3, 12) a rack with two black
  lamp-irons hanging from hooks, and on a nail beside the rack a pair of small
  boots, worn through at the toes, hung up by their laces. Never mentioned, never
  framed for: they are Nell's old boots, the ones the new boots replaced (Act 2's
  major turn: he bought the new ones with the irons money)."""),
])

edit('c08_iron_marker.md', [
    ("""it means to the player who has been paying attention: the Order's "morning" is
the thing under the ground; Nell was on toll work; and she did wake.""",
     """it means to the player who has been paying attention: the Order's "morning" is
the thing under the ground; Nell was on toll work; and she did wake. And in Act 3
it is true a third time: the morning under the ground keeps every one of the
valley's dead, and at the bottom of the stair Nell is there, saying "Da"."""),
])

edit('c09_fortune.md', [
    ("""  - Sella's buyers ("Vonnra pays for all of it"), paid in the reading of her past
    if she told Sella that past;""",
     """  - Sella's buyers ("Vonnra pays for all of it"), paid in the reading of her past
    if she told Sella that past while Sella was still selling her
    (`sella.past_sold`: not after the night Sella would not take the money);
  - the tremors (rule `tremor`, "the ground turned over in its sleep"), which stop
    Vonnra in the middle of a sentence;"""),
    ("    `sella.heard_past`, background;", "    `sella.past_sold`, background;"),
    ("""| 11 | `f_below` | A. On "Last." she looks down: not at the palm, at the table, as if through it. "And the door in the hillside..." She stops. The choices come up. Hold the 2S, the lamp between them. | A slow tilt down on her eyeline: past the parapet's lip, down the tower's face to the dark at its foot, where the wall meets the Verge, and on down to black as if the camera could look into the ground. *(Tam's knocking known:)* under the line, once, a deep dull knock, felt rather than heard. |""",
     """| 11 | `f_below` | A. On "Last." she looks down: not at the palm, at the table, as if through it. She goes on to "And the door in the hillside..." | A slow tilt down on her eyeline: past the parapet's lip, down the tower's face to the dark at its foot, where the wall meets the Verge, and on down to black as if the camera could look into the ground. *(Tam's knocking known:)* under the line, once, a deep dull knock, felt rather than heard. |
| 11a | The interruption | **The turn.** On "hillside" the roof shivers under the table. The lamp's glass rings in its frame. The flame lies over sideways, toward the east, though there is no wind. From under the town comes C03's groan, long and low, and down in the streets every dog starts barking at once. Vonnra stops in the middle of the sentence. B, then a MCU at 85: her head comes up and turns east, past the survivor, and stays there. Her thumb has come off the palm. | A 200 mm vista on her eyeline, east: the Verge, black, nothing to see. Then the groan stops, and the dogs one by one. Back on the MCU: she is still looking east, and she does not finish. The choices come up while she is looking away. Hold the 2S, the lamp's flame standing up straight again between them. (The accusation, if the survivor makes it now, lands on her off balance.) |"""),
    ("""  - turning south for what came before the ford (shot 10). There she is reciting,
    not reading, and she does not notice that her thumb has stopped.""",
     """  - turning south for what came before the ford (shot 10). There she is reciting,
    not reading, and she does not notice that her thumb has stopped;
  - the interruption (shot 11a): in forty years nobody has seen her not finish a
    sentence, and nobody says so. She does not startle. She stops, the way a clerk
    stops when a figure will not add up, and looks at the hill as if it owed her
    money. That is the only fear she shows in Act 1, and it is not for herself:
    it is for her arrangement."""),
    ("""  - The first two readings have no bell: only the pad, and the valley.""",
     """  - The first two readings have no bell: only the pad, and the valley.
  - The interruption (11a): the pad cut dead on "hillside"; the lamp's glass
    ringing; the groan (C03's, the same recording, deeper and further off); the
    town's dogs; then their silence one by one; then the pad back, a semitone
    lower, under the choices."""),
])
print('ok')
