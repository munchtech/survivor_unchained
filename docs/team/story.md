# Story and writing: status

The writer: owner of the canon, the words and the story data. Agent
a38d66ae66583ace1 (the eighth story lead), branch
`worktree-agent-a38d66ae66583ace1`. Works with the story editor, a fresh one
started for each act's draft (`docs/story/notes/`). A successor starts from
`docs/handoff/story.md`.

## State (6 October)

- **The treatment is approved** (`docs/story/TREATMENT.md` §0 lists the
  owner's choices and the editor's notes as applied).
- **Act 1 is rewritten in the data** (first pass, pushed). Key scenes, for the
  owner and the editor:
  - `scene_gate_dawn`, `scene_in_my_count`, `scene_knocking` (the confession,
    mid Act 1), `scene_did_he`, `scene_his_cup` (dialogue.json);
  - Brannoc's C07, reordered: `brannoc.dusk_call`, `nell` to `nell_lantern`;
    the road in rules.json `nell.burial_with`;
  - Rook's kind lie: `rook.mother` to `mother_room`; the grave
    (`Waystation.cs` `mother_grave`); the mystery page Home;
  - the fortune: `vonnra.f_ford`, `f_did`, the readable ledger in `f_chart`;
  - the dawns: rules `dawn.voice`, `dawn.word`; the first dawn's "Lamp's lit,
    Spark."; the dusk call's first hearing (`DayLines.DuskHeard`).
- **Love scenes:** both versions in `docs/story/LOVE_SCENES.md`, for the owner.
- **Voice:** `docs/voice/RERECORD.md` keeps every changed line by character;
  Sella's and Rook's lists are ready. Holloway, Brannoc, Maeca, Vonnra, Harlan
  and the narrator are on HOLD in their packets.
- **Next:** Act 2 (the rope with the player's hands on it, Holloway at his gate
  on the fourth dusk, the woman with the lamp), then Act 3 (the voice).

## Key decisions (why)

- **Scenes on the trunk:** the beats that carry Act 1 play by themselves at a
  morning or a dusk in the town (`Journey.TakeScene`, set by overnight rules),
  so no kind or careless road misses them.
- **"Spark", not "Wick":** read aloud, "Flame" doubles the fire and carries "old
  flame"; "Spark" is dry and a child's name. The lamplings are Stub and Old
  Gutter.
- **The confession never points at a survivor:** "Does anyone else know?" names
  Pell; the decoy is red, or a ledger.
- **No cost at the bench for either answer to Brannoc** (the owner): the truth
  costs a slower hammer and a dark road, heard, never paid.
- **The ledger's line 26 is "Rook's lodger.":** innocent until Act 2's end.

## Staging changes for cinematics (paused; none built)

- **C03:** after "Is it morning?" the shot holds on the lamp at her face for her
  answer: `warden_answer` (Nod / Say nothing; fact `warden.answer`). Either way
  he lets go. Show her taking the lamp-iron out of the shallows afterwards.
- **C04 A7:** the line is longer now (the mother's words added); hold the 3 s
  of silence after it. Cast it in the recast narrator's plain voice.
- **C04 B:** Holloway on the gate after his night: he puts his coat round her
  shoulders without a word and walks off; a guard to his mate, "That's his
  only coat." (a new line for C04 B2). There is one coat: she leaves it on his
  stool at the gate that evening; he wears it from then on; after the rope
  Maeca takes it off the empty stool, and wears it at the war. Rook at her door looks at the survivor's face one beat too long, then
  at the tower. On the stones at the water's edge, a dropped lamp, gone out.
- **The prologue:** the last of the drowned at the water's edge is a woman who
  lifts a dead lamp to the survivor's face and does not strike; the narrator
  says nothing while the player cuts her down (combat and experience).
- **C07:** the forge at dusk; the camera on his thumb finding the mark; no
  music; the bar from orange to grey at the very end; the lantern taken down.
- **C14:** one action, held: under the last iron he closes his bare hand round
  the light. No "reads his own bracket". No irons laid in the road.
- **C08:** cut Rook turning toward the mother's marker. The marker is just
  there, a few stones along.
- **C09:** the ledger readable, framed on the last page: twenty-six lines
  struck, "Nell, the smith's girl. With Wat.", "Rook's lodger.", and
  "From the ford. Got up." not struck.
- **The gate scenes** (`scene_*`) play as conversations today. Holloway sits
  the night in the south gateway (`Waystation.cs` routine). A staged version
  would want: Maeca on the step with the crossbow, the bottle poured out.

## For other areas

- **Combat:** the lamplings renamed (Stub, Old Gutter), done in `Enemies.cs`,
  `Dig.cs`, `Journey.cs`. The prologue's woman with the dead lamp (above).
- **Crafting (paused):** the lie to Brannoc costs no prices, commissions or
  masterworks (the owner overrode "full prices"); his warmth goes, in words
  only. Snib does not take his forge work. Nothing to build.
- **Voice (paused):** the narrator recast as a woman of about sixty, plain and
  dry, light valley accent (`VOICES.md`, `VO_CAST.md`).
