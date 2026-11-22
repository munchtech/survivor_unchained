# The den's story beat: script and staging ("They lie down around you")

**Status: script draft, 22 Nov 2026, for the owner to read. Nothing is wired.** This is pitch 2 from `docs/design/SLICE_STORY_BEAT.md`, picked on 22 Nov by the coordinator on the owner's word. The script has 18 lines of spoken or shown text, against a cap of 40. The owner was asleep, so the author lead made the open choices inside the brief; each is marked **[Decision]** with its reason. The owner can overrule any of them before the wiring session, and only this page would change. Labels: **[O]** observed in code or data; **[C]** computed from the camera numbers, not measured in a frame; **[U]** unknown, not checked.

The owner: "I want a rich story with genuine emotional impact." and "Do not assume expensive close-up cinematics are necessary."

## What you should be able to say the next day (D7)

"Halfway down the den, three wolves were lying around a dead one, and they didn't get up. When I killed the Pack-Mother, the last wolves walked right past her body and lay down around me. Two of them followed me out to the camp. The old herbalist took my wrist like she was feeling for a pulse, held it far too long, and told me to get by the lamp. Every time I went back down, one more was waiting."

If you can say that, the beat reads. Nothing on screen says why.

## The script (18 lines)

Who speaks:
- **N**, the narrator: the lower-third caption, in the house voice. She says what happens and what can be seen, never what it means (`docs/STORY_BIBLE.md` 187-192).
- **W**, Old Wenna: a caption with her name card, or world text over her head where marked.
- **S**, the survivor: her one choice.

**Before the first run, at the camp**

1. W (world text, once, when the survivor first comes within 6 m): "Root's best where the water's worst. Never picked better."
2. W (world text called after her, once, as she heads for the den's mouth): "If you find them lying round one of their own, leave them be. That's a wake."
3. W (only if she talks to Wenna before her first clear): "You're for the den. Course you are. They're sick down there, the lot of them. It's the stream. Sick things don't run off, child, and they don't stop."
4. S (the dialogue's usual close): "Goodbye."

**The wake (the first time she comes on it)**

5. N: "Three of them lie around a fourth. The fourth is dead."
6. N: "They lift their heads to your light. They do not get up."

**The ring (the first clear)**

7. N: "They walk past her."
8. N: "They lie down around you."
9. The existing banner, held until the ring is down: "The Pack-Mother is dead" / "The way out is open, past where it kept"

**The camp, after the first clear**

10. N: "Two of them have followed you out. They lie at the edge of the light and watch you."
11. N: "She takes your wrist, two fingers on the inside of it, and holds it a long time."
12. W: "Get by the lamp, child."

**The camp, clears 2 to 6**

13. N (clear 2, on arrival): "There is one more of them than last time."
14. W (clear 2): "Light's better here for sorting. Don't look at me like that."
15. W (clear 3): "They don't want the root. They don't want me. ...Eat something."
16. W (clear 4): "I wasn't asleep. I was resting my eyes on them."
17. W (clear 5): "That one's yours. Don't make a thing of it."
18. N (clear 6): "She takes your hand. This time she only holds it."

Lines 4 and 9 are text the game already has; they are counted to be safe. Each line plays once. After that, the pictures repeat on every clear without words. Talking to Wenna after a clear repeats her latest line, so it adds no text.

## Staging

Everything plays at the game camera: perspective FOV 34, 62 degrees down, 24 m away, with the survivor about 70 px tall at 1080p. There is no close-up and no camera move (no `Ev.Focus`, no `HoldOn`), and the player's controls are never taken.

[C] At that camera the frame covers about 26 m across and 16-17 m of ground top to bottom. Anything within about 12 m to her sides, or 7 m above or below her, is in frame. Approximate sizes on screen:
- a wolf lying with its head up: about 20 px tall and 60-100 px long;
- the Pack-Mother's body (model scale 2.7, `Content/Enemies.cs` 474): about 250-300 px long;
- a 4 m ring around her: about 550 px across.

### A. The camp before the first run

- **The setting.** It is night and the lamp-post is lit. **[Decision]** The camp plays at night for two reasons:
  - Line 11 only means something at night, when the survivor is "cold as stone, the heart slow" (bible 120-126).
  - "The edge of the light" needs a lit lamp.

  The camp itself is not built yet (it is A3's camp screen). This beat asks it for:
  - the den's mouth at the top of the frame and the lamp-post in the middle;
  - Wenna's fire and pot 3-4 m to one side of the post, and a seat log;
  - the post's light ending 6-8 m out.
- **Wenna.** She stands at her fire stirring root (her "work" loop).
  - Line 1 shows as world text over her the first time the survivor comes within 6 m.
  - Line 2 plays once, when the survivor walks toward the den's mouth (within 8 m of it), whether or not she has talked to Wenna.
  - Talking to Wenna gives line 3, then the close, line 4.
- **[Decision] Line 2 is new; the pitch did not have it.** It tells the player what a wake is before they see one, so the wake and the ring become one picture: what the wolves do for their dead, they then do for her. It says what, never why. It also tells the player not to swing at the mourners.
- **Sound.** The fire, the lamp's hiss and the wind, with the game's Night mood (`Music.cs`) playing quietly.

### B. The wake (a room in the den's first half)

- **The room.** It is the first fight room on the route past the route's first third. It is never the altar room or the boss room. The room holds the wake and no other pack, and no pack wakes within 20 m of it, so nothing fights beside it.
- **What lies there.** A dead wolf lies on its side, 5-9 m to one side of the line she walks through the room. It sits nearest the bottom of the frame, so nothing hides it. Three wolves lie around it, 1.2-1.5 m out, with their chins down toward its flank. [C] The group is about 3.5 m (about 250 px) across.
- **Timing**, from the moment she comes within 14 m:
  - The den's exploration track (the owner's recording) ducks to about a fifth over 2 s.
  - At 12 m, line 5 plays.
  - At 8 m, the three lift their heads (0.6 s) and line 6 plays.
  - While she is within 14 m, they turn slowly in place to keep facing her (at most 60 degrees a second). They never get up.
  - Once she is past 14 m, their heads go back down to the flank (1.5 s). At 20 m the music comes back over 4 s.
- **Sound.** One low whine from one of them as their heads lift. After that, nothing but her steps.
- **They are not foes.** They get no health bar and no hostile marking. Her weapons, auras and ground fire pass through them: the game already treats neutral creatures this way (`Sim/Battle.cs` 803-815 and 1014-1020). If something provokes them anyway, they fight as wolves, and nothing scripted punishes it.
- **Clears 2 to 6.** The wake is there on every run, in whatever room the den lays out, with no words.

### C. The ring (the Pack-Mother's death)

Times are in seconds from the killing blow.
- **0.0.** She goes down onto her side (the existing death). The boss track stops and nothing replaces it. Her marks on the ground are cleared. Every foe still alive in the room (her Drive's wolves, "The last of the Pack") stops where it is, still standing, and is no longer a foe.
- **0.0 to 1.5.** Nothing moves. There is only the room's own sound.
- **1.5.** The surviving wolves start toward the survivor. They walk, not run: the model's own walk cycle, at about 1.3 m/s. Every other wolf in the den came at her running.
- **2.0 to 4.0.** If fewer than eight are alive, the rest walk in out of the dark at the room's far side, one every half second. They start beyond her body, so their way to the survivor runs past it.
- **About 4 to 6.** The first wolf passes within 2 m of the body without stopping, and line 7 plays. None of them stops at her.
- **About 8 to 12.** Each wolf reaches its place on a ring 3.5-4 m around the survivor, turns to face her and lies down with its head up (1 s). When the fourth is down, line 8 plays. Each one makes a soft settling sound; no wolf makes a voice.
- **About 12 to 16.** Stillness. If she moves, the ring stays down and turns in place to face her. There are gaps of about 1.5 m between them, so she can walk out whenever she likes.
- **About 14 to 16, once the last is down.** The banner (line 9) shows, the loot spills at the body, and the way out lights. The owner's death sting ("Falls", 6 s) plays now, not at the blow. After it the den is quiet, as it is today.
- **When she leaves** through the way out, they stay down and turn to watch her go.
- **[Decision] The banner, loot, way out and sting wait 14-16 s.** The silence is the beat, and a player handed the loot and the exit at once will leave before the wolves arrive. The owner's sting is moved, not cut. You judge whether it still fits after the silence when you hear it.
- **[Decision] Eight wolves, 3.5-4 m out.** A ring reads at her size where a loose cluster would not, and eight leaves her room to walk out.
- **[Decision] They walk past the body,** so nobody reads it as the Pack mourning its mother. The mother is right there, and they walk past her to you.
- **Clears 2 to 6.** The same ring, the same silence and the same held release, with no words.

### D. The camp after the first clear

- **On arrival.** The survivor comes out of the den's mouth at the top of the frame. Two wolves lie at the edge of the lamp's light, 6-8 m from the post on the den's side.
  - They lie on either side of the way down, heads up and facing her, with about 3 m between them where she walks.
  - As she moves, they turn in place to keep facing her. They never get up, never come closer and never leave while she is at the camp.
  - 1 s after she appears, line 10 plays.
  - The music stays silent from her arrival until after line 12. The fire, the lamp and the wind go on.
- **Wenna** stands at the edge of her fire, looking at the wolves rather than working, her back half turned to the survivor. She does not turn to greet her as she normally would.
- **The wrist**, the first time the survivor comes within 4 m of her:
  - Wenna turns (0.5 s), takes two steps to her (1.2 s) and reaches out (0.4 s).
  - She holds the survivor's wrist for 3 s. Line 11 plays as the hold starts.
  - She lets go and steps back (0.6 s), and line 12 plays with her name card.
  - She turns back to the wolves, and the Night mood comes back over 8 s.
- **[O] No clip exists for two people touching.** Wenna's clips are walk, idle, talk, folded arms, sitting, cheer, wave, work and pick up (`src/Actors/FolkClips.cs` 46-58). What shows at the camera is her "work" reach, held toward the survivor at arm's length; line 11 tells what her hands are doing. **[Decision]** The narrator carries the touch, under her own rule: it is something that can be seen, just at a size the camera cannot show.
- **If the survivor walks away during the hold,** Wenna lets go and calls line 12 after her. If the survivor never goes near Wenna, the moment waits for the next visit, after any clear.
- **Why it lands, unsaid.** At night the survivor's wrist is cold and her heart slow. Wenna nursed the fever year; she holds on longer than finding a pulse should take, then sends her to the light. Everyone who sleeps near the survivor notices this "in their own trade's words", and none of them knows what it means until Act 2 (bible 120-126). Nobody here says it.

### E. The camp on clears 2 to 6

| Clear | Wolves at the light's edge | Wenna | Text |
|---|---|---|---|
| 2 | 3 | Has moved her seat and pot into the lamp's light, 2 m from the post, and sits sorting root | Line 13 on arrival; line 14 the first time the survivor comes within 4 m (she stays seated) |
| 3 | 4 | Sits by the post facing the wolves, her staff leaned beside her | Line 15 |
| 4 | 5 | Sits by the post with her head down, asleep. If a seated head-down pose can't be made, plain sitting is enough | Line 16, as the survivor comes near and she looks up |
| 5 | 6 | Has set a second seat beside hers in the light, empty | Line 17 |
| 6 | 6 | Stands as the survivor comes near and takes her hand. This time she does not reach for the wrist, and she lets go only when the survivor walks away or after 8 s | Line 18 as the hold starts; Wenna says nothing |
| 7 on | 6 | Sits by the post, the second seat beside her | none |

- **[Decision] The edge stops at six, reached on clear 5.** The pitch said "up to about six", and six still fit in the frame from the post. Each clear brings one change you can see from the post: one more wolf, and Wenna nearer the light.
- **[Decision] Clear 6 closes the arc.** On clear 1 she checks the wrist; on clear 6 she only holds the hand. She keeps the same watch the wolves keep. If players stop before clear 6, nothing is lost: clears 1 and 2 carry the whole beat.

## Other decisions

- **Wenna's gate passed [O].** Her model is built and committed: `godot/art/npc/npc_wenna` (body.glb, lod.glb, manifest.json), and her `npcs.json` entry "wenna" has `person.body` "npc:npc_wenna". Her dialogue tree is built (`dialogue.json` "wenna", 18 nodes). Standing a named NPC up outside the town with a talk prompt already works: Maeca at the Blind (`Play/Zones/Verge.cs` 946-953). What is not built is the camp itself.
- **18 lines, not 40.** Everything the camera can show is left to the picture. Words go only where it cannot: what a wake is, the wrist, the count.
- **Text once, pictures every time.** Captions repeated on every clear would go stale. On later clears the pictures, the silence and the count carry it.
- **Wenna's voice** comes from her built lines: rude, practical, calling everyone "child", and ducking into a chore ("...I've roots on the boil."; "Sit. No, don't sit"). She says "round", in her dialect as built ("Course Tam saw it"); the narrator says "around".
- **The survivor says nothing** except the dialogue's usual "Goodbye." The beat happens to her.
- **A fallback for line 6 [U].** I have not checked whether she carries a visible light in the den. If she does not, line 6 becomes "They lift their heads to you. They do not get up." The line count stays the same.

## Checked against the bible

- **Not the toll.** No death in the valley, no ledger, no rising. The bible is unchanged.
- **Nothing a later act keeps is said.** Three things are only shown:
  - what she is (Act 2): the wake turned on her, and the wrist;
  - what she carries (Act 3);
  - that more come for it (Act 3; bible 1288-1290: "Everything that has lost a light comes to it; the more she carries, the more come"): one more wolf each clear.

  The narrator says only what can be seen.
- **No romance.** The 18+ tone is not used.
- **Avoided on purpose:**
  - "kept the cold off" (Greymuzzle's title);
  - "Is it morning?" (the prologue's line);
  - Greymuzzle on screen;
  - anything that hangs on the miniboss;
  - any voice from the light;
  - the mother's word.
- **"Lie down"** is used as plain description. It rhymes with the Order's word for the dead (C02, and the hymn in C08) without being it.
- **Wenna's built seeds are not reused.** "Hot stone on you, child..." (`npcs.json`) and "They died, child." (`wenna.fever`) stay where they are.

## Wiring list (for the build session; nothing here is built)

Wire this after P3, the den roster re-cut (`docs/design/DEN_ROSTER.md`), has merged. Items marked **P3** touch the same code.

**Saved facts** (journey facts, set the way `Verge.cs` sets `tip.verge_map`):
- `den.clears` (int): goes up by one when the ring is down on a den clear.
- `den.camp_said` (int): the last clear whose camp moment has played. Clear N's moment plays once, the first time she is near Wenna after that clear.
- `den.warned`, `den.wake_seen`, `den.ring_seen` (bool): lines 2, 5-6 and 7-8 have played.

**The wolf's poses.** These are the beat's one art item: judge them at the game camera before the beat is judged.
- [O] There is no live lying pose today:
  - `EnemyAnim` is Move, Idle, Attack, Hit, Die, Rise, Windup, Cast, Burrow (`Sim/Entities.cs` 21).
  - The wolf's roles are run, idle, creep and three deaths (`src/Actors/Beasts.cs` 47-111).
  - Greymuzzle's ring "lies down where it stands" only in its text. In code those wolves go Idle and stay standing (`Play/Bosses/Greymuzzle.cs` 570-586).
- Add two composed poses, built the way `die2` is (perhaps over the model's unused `Wolf_seat_` clip):
  - "lie": chest down, forelegs forward, hind legs folded, head up;
  - "lie_low": the same with the chin down.
- Add "walk", from the model's unused `Wolf_Walk_cycle_` clip.
- Add the matching `EnemyAnim` values and their role mapping.
- A lying wolf must not read as dead. The raised head and the slow turn to face her are the difference.

**The wake:**
- **P3** Packs are set down in `Play/Zones/MapRun.cs` `Place` (302), and P3 replaces its mixing with recipes. For the den only (`Chart.Dungeon == "hollow"`), the wake takes the place of one room's pack.
  - The room comes from `DungeonLayout.Route`: the first fight room past a third of it.
  - The spot comes from the room's `Plan.Packs` through `DungeonGen.Xf` (`Maps/DungeonGen.cs` 407-414, 671).
- Spawn the three as neutral, scripted wolves: `Battle.SpawnOpts` with `Disposition = Disposition.Neutral`, the way `Verge.cs` 958-966 spawns the Pack as allies. Give each a script tick, as Greymuzzle's `S.Script` does: lie_low, then lie within 8 m, then turn to face her within 14 m.
- The dead wolf lies on its side for the whole run. It drops no loot, counts no kill, cannot be struck and never fades. [O] The crowd keeps only so many bodies (`src/Actors/CrowdView.cs` 34), so a wolf killed the normal way may fade. A neutral, scripted wolf held in the `die` pose, with `TakenMul = 0` and no health bar, might serve; the build session picks.
- **P3** The den has one fewer fight pack, so the pack counts in `MapTests` and `DungeonFightTests` shift a little, and so does the stand-still bot's fall rate.
- The music duck: the den's score is the owner's recordings (`src/Audio/DenAudio.cs`, `src/Audio/DenSound.cs` 188-205). Duck the exploration track near the wake; do not cut it.

**The ring:**
- **P3** The hook is the den's ruler death: `MapRun.RulerDown` (614-642) and `IBossArena.Won` (607-612, which spills the loot at once). For the den only:
  - Start the ring script.
  - Hold `Ev.Victory`, the "is dead" announcement, the way out's light and prompt, and the loot spill until the ring is down, then release them together.
  - `PackMother` (`Play/Bosses/ArenaBosses.cs` 32) is shared with Greymuzzle's story night, and P3 already needs a den-only switch there (DEN_ROSTER, "Build cost"). Use the same switch, and leave the arena and story-night paths as they are.
- At the blow:
  - Call `B.CancelBlows()`, as `Greymuzzle.cs` 568 does.
  - Make every living foe in the room neutral and scripted, as `Greymuzzle.cs` 573-586 does.
  - Wolves take ring places. Anything else walks off into the dark and is released (`B.Enemies.Release`, `Greymuzzle.cs` 534). Wolves beyond eight lie down where they stand.
- **P3** Where the surviving wolves come from: her last phase calls "The last of the Pack", 12 wolves at 14 m (`ArenaBosses.cs` 92-98). DEN_ROSTER 61 takes away her chained lunges and does not name this ring. My reading is that the ring stays. The beat must not depend on it either way: it tops the ring up to eight with walkers spawned at the room's far side (`IBossArena.CanStand`), whatever P3 leaves.
- Music: `DenSound.MusicRule.Update` (197-204) plays the Falls sting as soon as the boss is down. Give it a hold, so the boss track stops at the blow and Falls starts when the ring is down.
- Sound: add a "last" moment to the Pack-Mother's voice (`voice.packmother.*`, `ArenaBosses.cs` 59-60), a long breath out, and a soft settle for each wolf. If neither exists, silence does the job.
- No `Ev.Focus` and no `HoldOn` anywhere in the beat: both exist, and both move the camera.

**The camp** (the camp screen is its own build). The beat needs:
- Night; a lit lamp-post whose light ends 6-8 m out; the den's mouth at the top of the frame; Wenna's fire 3-4 m from the post; a seat log (`src/World/Camp.cs` has the camp's pieces); and a second seat from clear 5.
- Wenna stood up the way Maeca is (`Verge.cs` 946-953): `new NpcActor(Lore.Npcs["wenna"], G.Look, G.Rng, new Spot {...})`, with a talk prompt. `NpcActor` turns to greet the survivor (`Play/Zone.cs` 362-376); it needs a hold on that turn while she watches the wolves.
- The wolves at the edge: spawned at load, neutral and scripted, in the lie pose, in an arc on either side of the way down from the mouth. From clear 1 there are `min(den.clears + 1, 6)` of them.
- Wenna's moments, read from `den.clears` and `den.camp_said`: the wrist on clear 1, her seat and pose on clears 2-5, the hand on clear 6. Her reach is the "work" clip, held.
- Music: silent from her arrival after a clear until Wenna's moment ends (or 30 s), then the Night mood. The mood is picked in `src/Audio/SoundBridge.cs` 265-280, and the camp needs its own override there.

**Dialogue data:**
- Add a new tree, "wenna_camp", in `godot/data/content/dialogue.json` (npc "wenna"), so her town tree stays as it is. It holds:
  - node `camp_first`: line 3, closed by line 4;
  - one node per clear, carrying her latest line, for the talk prompt;
  - entry rules keyed on `den.clears`.

  Open it with `Converse` (`Play/Zone.cs` 102-105), or route the camp's talk prompt to it.
- Show lines 1-2 as world text over her (`Ev.Bark` with her as speaker). Show the narrator's lines and lines 12 and 14-17 through the lower-third caption (`Say(text, who, seconds)`, `Play/Zone.cs` 81).
- Run StoryLint on the new text.

**Tests for the build session:**
- The den's layout puts the wake in a fight room past a third of the route, with no fight pack within 20 m.
- After the Pack-Mother dies in the den, eight neutral wolves lie within 4.5 m of the survivor within 15 s, and the loot, the banner and the way out come after.
- The camp shows the right count for `den.clears`, and each line plays once.

## Not done, not checked

- Nothing is built or wired, and no frame was rendered. Every pixel size above is computed from the camera numbers.
- [U] Whether she carries a visible light in the den (line 6's fallback covers this).
- [U] Whether a seated head-down pose can be made for Wenna (clear 4 works without it).
- [U] How the owner's Falls sting sounds after 14 s of silence.
- The camp screen is not built. This page asks for its time of day, light reach and layout; nothing elsewhere has decided them.
- If the built beat does not land: one rewrite of this page, then the narrator fallback (decision 12).
