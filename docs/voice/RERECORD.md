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

**Locked for recording (11 October):** the narrator's prologue lines and C01 to C04, Vonnra's far voice in the prologue, the Warden's, Grimtunnel's, the dead Watchman's and the gate guard's prologue lines, and Rook's and Brannoc's Act 1 lines (with the narrator's parts inside them). Each is marked **LOCKED FOR RECORDING** in its packet (`tools/vo/locked.json`; `python tools/vo/lock.py --list`). The rest of the narrator, Vonnra and Brannoc stays on hold. A locked line whose words change later shows **HOLD** again until the story lead re-locks it.

**28 October: the love scenes and the romance routes are removed (the owner).** Sella's blue room keeps the stairs, the paid sleep and its mornings; her free night is now the night she sits with you (`free_door`, `free_what`, `free_sit`, `free_m_who`). Maeca's Blind keeps the walk, the fire, the watch nights (`watch_only`, `blind_dark`) and the gray lights. The nodes `sella.stairs_room`, `stairs_rules`, `night`, `morning`, `stop_paid`, `rest_night_paid`, `free_night`, `free_bolt`, `free_sleep`, `free_sleep_bed`, `free_want`, `free_stop`, `free_morning`, `free_m_downstairs`, `free_m_kiss`, `maeca.blind`, `blind2_feet`, `blind2_let`, `watch_morning`, `say_sella*`, `keegan.dinner`, `supper_hand` and `rav.back_room_kiss` are gone; any take saved for them is unused. The door rule (the narrator never recorded behind the door) is retired with them.

---

## Sella (ready)

Two lines change, two takes only need renaming, and two barks are new. The
love scenes are B (the owner, 6 October: the lovers' own lines), so the blue
room's lines are new takes too: see "The love scenes (B)" below.

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
| `dlg.sella.night.1.p1.wav` ("Don't,") | `dlg.sella.night.0.p1.wav` | The cold-bath night is the first variant now; the old packet had the old order. (removed 28 October) |
| `dlg.sella.free_night.1.p1.wav` ("You told me anyway,") | `dlg.sella.free_night.0.p1.wav` | As above. (removed 28 October) |

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

### The love scenes (B)

**Removed 28 October; history only.** The narrator stops at the blue room's door, and the room is Sella's alone:
the nights on a dark screen, the mornings lit. Every line below is a new take
(the old "Don't," and "You told me anyway," inside the narration fold into
`night.0` and `free_night.0`; the narrator's asides in the mornings became her
own directions, so those lines are one take now, not parts). Record them only
when each shows **LOCKED FOR RECORDING** in `sella.md`; the directions are
there (`tools/vo/direction/love_b.json`). In the dark: low and close, nearly
a whisper, never breathy; each "..." a real silence of two to four seconds
(the importer keeps up to four for these); a laugh that sounds made is cut.
The room's sounds (water, buckles, coins, the step, the bolt) are the game's.

`sella.stairs_room.4`, `sella.stairs_room.5`, `sella.stairs_room.6`, `sella.stairs_room.7`, `sella.stairs_room.0`, `sella.stairs_room.1`, `sella.stairs_room.2`, `sella.stairs_room.3`, `sella.stairs_rules.0`, `sella.stairs_rules.1`, `sella.rest_bed.0`, `sella.night.2`, `sella.night.1`, `sella.night.0`, `sella.stop_paid.0`, `sella.rest_night_paid.0`, `sella.rest_dark.0`, `sella.free_door.0`, `sella.free_door.1`, `sella.free_want.0`, `sella.free_stop.0`, `sella.free_sit.0`, `sella.free_sleep.0`, `sella.free_sleep_bed.0`, `sella.free_bolt.0`, `sella.free_night.0`, `sella.free_night.1`, `sella.morning.0`, `sella.rest_morning.0`, `sella.rest_morning.1`, `sella.free_morning.0`, `sella.free_m_downstairs.0`, `sella.free_m_who.0`, `sella.free_m_kiss.0`, `sella.sleeptalk.0`, `sella.door.0`, `sella.door_years.0`, `sella.door_south.0`, `sella.past.0`, `sella.past.1`, `sella.past.2`, `sella.past.3`, `sella.past.4`, `sella.past.5`, `sella.past.6`, `sella.past.7` (46 takes; the ids drop `dlg.`). `stairs_rules.1` and `rest_bed.0` keep their words but are on the dark screen now, so any old take of them is too loud: take them again.

---

## Maeca (the Blind, B: locked 11 October; the rest of her waits)

Her love scenes are B too: under the hides she speaks for herself, and the
narrator only opens the gray light outside. These are locked for recording
(each shows **LOCKED FOR RECORDING** in `maeca.md`), ahead of the rest of
her; the directions are in `love_b.json`, as for Sella's.

`maeca.blind.0`, `maeca.blind.1`, `maeca.blind_morning.1`, `maeca.blind_dark.0`, `maeca.blind2_feet.0`, `maeca.blind2_let.0`, `maeca.blind_dark.1`, `maeca.blind_dark.2`, `maeca.blind_dark.3`, `maeca.told_true.0`, `maeca.told_true.1`, `maeca.told_true.2`, `maeca.told_true.3`, `maeca.told_little.0`, `maeca.blind3_morning.0` (15 takes).

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

## Brannoc (Act 1 locked)

One bark changes; every other Act 1 line of his is locked as written.

### Changed

| Id | Old | New | Why |
|---|---|---|---|
| `bark.brannoc.day.2` | Bring me hides. I'll make you something worth wearing. | Five pelts. That's a cloak. Bring five. | The old bark was any smith's; he counts, the way he counts his irons. |

---

## The narrator (recast; the prologue and C01 to C04 locked)

Recast as a woman of about sixty, plain and dry, a light valley accent
(`docs/VOICES.md`). Nothing of the narrator's is recorded in ElevenLabs yet.
The old placeholder take of `dlg.cin_first_light.face.0` is dropped (its words
changed: "Her voice is still there. 'Lamp's lit, Spark. Stay where it
reaches.'"); every other placeholder of hers goes when she is cast. Her prologue and C01 to C04 lines are locked (above): cast her from the brief in her packet and record those first.
