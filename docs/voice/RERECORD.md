# Lines to re-record

The writer keeps this list as the approved story rewrite lands (the owner's
choices on `docs/story/TREATMENT.md`, 5 to 6 October). One section per
character, in the order the owner records them. For every line that changes
or is new: its id, the old text, the new text (or NEW), and why, in one line.
The packets in `docs/voice/elevenlabs/` are marked to match: a changed line
carries **RE-RECORD** under its heading.

Ids are the take names without `.wav` (`dlg.<conversation>.<node>.<variant>`,
with `.pN` for a part inside narration).

**Hold these characters' recording until their section says "ready":**
Captain Holloway, Brannoc, Maeca, Vonnra, Harlan and the narrator. The
rewrite changes most of their Act 1 lines (Holloway's past and his drunk
syntax, Brannoc's pride and his iron, Maeca's name and her secret, the
fortune's "You did this", Harlan's "I did.", and the narrator's recast as a
woman of about sixty).

---

## Sella (ready)

Two lines change, two takes only need renaming, and two barks are new. Five
more are new **only if the owner chooses the lovers' own lines** for the love
scenes (see `docs/story/LOVE_SCENES.md`); with the other version (the
narration as unvoiced text) Sella records nothing more.

The packet the owner recorded from was a little behind the game's data
(regenerated now, 6 October): one line had been reworded on 4 October, two
takes were named for the wrong variant, and two barks were missing from it.
The importer would have refused those, so they are listed here too.

### Changed

| Id | Old | New | Why |
|---|---|---|---|
| `dlg.sella.say_maeca.0` | Maeca Barefoot came in this morning humming. Maeca. Humming. I've a professional interest, love: who's my competition? | Maeca came in this morning humming. Maeca. Humming. I've a professional interest, love: who's my competition? | "Barefoot" is cut from Maeca everywhere (the owner). |
| `dlg.sella.say_calling.2` | Your hands are warm. Not in a nice way. Are you on fire? Your hands are a little bit on fire. | Something on you's smouldering, love. Are you on fire? You're a little bit on fire. | Changed on 4 October, after the packet was made: by night an Unchained is cold, so nobody may call her warm. |

### Renamed only (the same words; rename the file, no new take)

| Take saved as | Rename to | Why |
|---|---|---|
| `dlg.sella.night.1.p1.wav` ("Don't,") | `dlg.sella.night.0.p1.wav` | The cold-bath night is the first variant now; the old packet had the old order. |
| `dlg.sella.free_night.1.p1.wav` ("You told me anyway,") | `dlg.sella.free_night.0.p1.wav` | As above. |

### New barks (missing from the old packet)

| Id | Old | New | Why |
|---|---|---|---|
| `bark.sella.said.0` | NEW | Tell me about last night, love. I pay better than the Wayfinder. | The morning after a night in the dark (added 4 October). |
| `bark.sella.said.1` | NEW | Back, and all your bits still on. Pity to waste them on sleep. | As above. |

Checked and kept as recorded: every other Sella line. Her "Don't tell
Rook" stays hers (the editor gives that aside to her alone); her stalker's
remark ("You came up behind me without a sound") stays, and the other
speakers' copies of it are rewritten instead; "Holloway's drinking more than
he's paying" stays, and now plants that someone else pays for his drink.

### New, only if the owner chooses the lovers' own lines

In this version the narrator stops at the blue room's door, and the night
plays on a dark screen in Sella's voice alone. Each line replaces the
narration of one night. The two short takes already recorded inside the
narration ("Don't," and "You told me anyway,") are folded into the new
lines, so they would be re-recorded as part of them.

| Id | Old | New | Why |
|---|---|---|---|
| `dlg.sella.night.2` (the first night) | narration | NEW: Bath's warm. Was warm. ...Leave it, love. Come here. There. Now, any hand of mine that's not welcome, you say, and I'll find it somewhere it is. ...That's it. Slow. Nobody's paying me to hurry. ...Listen. Can't hear the road from up here. Can't hear the river. That's what the fifteen's for. | The lovers' own lines, in place of the narrator in the room. |
| `dlg.sella.night.1` (three nights or more) | narration | NEW: That's the floor, then. ...Not with my shift, you great— give it here. ...Right. I'll tell you what I'm going to do, love, and then I'm going to do it. First I'm going to— ...First. ...You know. Come here. | As above; the gaps she doesn't finish are the scene. |
| `dlg.sella.night.0` (the cold bath) | narration, with "Don't," | NEW: Water's gone cold. ...Leave it. I'm not walking three steps for a bed; bring the quilt. ...Easy. Easy, love. ...Don't. ...Don't look at me. ...I'm not getting dressed. Don't ask me why. | As above; replaces the "Don't," take. |
| `dlg.sella.free_night.0` (she was told knowing) | narration, with "You told me anyway," | NEW: Hold still. My hands don't know what they're doing. ...Seven years, love, and I can't undo a lace. Don't you laugh. Don't you dare— ...Wait. ...All right. All right. ...You told me anyway. | As above; replaces the "You told me anyway," take. |
| `dlg.sella.free_night.1` | narration | NEW: No talking. I talk for money. ...Stay like that. Let me look. ...I'm not making a joke of it. Don't you make one. ...Yes. | As above. |

Directions for these five, if they are recorded: low and close, a dark room,
nearly a whisper but never breathy; she laughs on the first two and does not
on the last three. Each "..." is a real silence of two to four seconds, cut
in the edit.

---

## Mother Rook (ready for Act 1)

One line changes, six are new (the kind lie about the survivor's mother, Act
1's new trunk beat), and three barks were missing from the old packet. Every
other Rook line stands as recorded. (Her arcanist remark, "do it outside",
stays: the other three fire jokes are the ones rewritten.) Act 2 will add
her kitchen scene; that comes in its own list.

### Changed

| Id | Old | New | Why |
|---|---|---|---|
| `dlg.rook.hub.1` | There you are. I kept a bowl back. Don't tell the others. | There you are. I kept a bowl back. The others can whistle. | "Don't tell..." is Sella's aside alone now (the editor: it had stopped marking anyone). |

### New

The lines inside narration are parts: Rook says only the quoted words; the
narrator's parts wait for the narrator's recast.

| Id | Old | New | Why |
|---|---|---|---|
| `dlg.rook.mother.0.p1` | NEW | ...Sit down, pet. | Day 1: the survivor asks after her mother. Rook knows how she died. |
| `dlg.rook.mother2.0.p0` | NEW | She went in her sleep, pet. A week since. | The kind lie (Act 2 turns it). Played steady, and too quickly. |
| `dlg.rook.mother2.0.p2` | NEW | Chid brought her down and saw to her. I sat with her, after. | As above; the second half is true. |
| `dlg.rook.mother_where.0` | NEW | Quiet Garden, behind the shrine. There's a marker. No name on it yet; you can tell Chid what to cut. | Where the grave is. Practical, brisk: a woman getting through it. |
| `dlg.rook.mother_short.0.p1` | NEW | You came, pet. That's the part that counts. | If she says she was a day short. Kind, and the kindness costs her. |
| `dlg.rook.mother_room.0.p1` | NEW | Back room's yours, if you want it. It's been free a week. | The survivor sleeps in her mother's last bed (the re-read). Plain. |

### New barks (missing from the old packet)

| Id | Old | New | Why |
|---|---|---|---|
| `bark.rook.said.2` | NEW | Lamp burned all night for you, pet. A night's ember. It's on your slate. | Added 4 October (the night's last line). |
| `bark.rook.said.3` | NEW | Face like a wet week. Eat first. It'll still be there after. | As above. |
| `bark.rook.said.4` | NEW | Sit down before you fall down. Again. | As above. |

---

## The narrator (on hold: recast)

Recast as a woman of about sixty, plain and dry, a light valley accent
(`docs/VOICES.md`). Nothing of the narrator's is recorded in ElevenLabs yet.
The old placeholder take of `dlg.cin_first_light.face.0` is dropped (its words
changed: "Her voice is still there. 'Lamp's lit, Spark. Stay where it
reaches.'"); every other placeholder of hers goes when she is cast.
