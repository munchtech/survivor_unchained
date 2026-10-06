import os

p = os.path.join(os.getcwd(), 'docs', 'cinematics', 'README.md')
s = open(p, encoding='utf-8').read()


def rep(a, b):
    global s
    assert s.count(a) == 1, (a[:80], s.count(a))
    s = s.replace(a, b)


rep("""A line's VO id is
`<conversation>.<node>`; where a node has text variants (by calling, by
facts), each variant's id adds `#<index>` in the order written
(`cin_raid_on_the_roost.last#1`).""",
    """A line's VO id is
`<conversation>.<node>`; where a node has text variants (by calling, by
facts), each variant's id adds `#<index>` in the order written
(`cin_raid_on_the_roost.last#1`). That is the scripts' short form. The voice
system (`tools/vo`, `VoiceLines`) files the same line as
`dlg.<conversation>.<node>.<index>` (`dlg.cin_raid_on_the_roost.last.1`); a
caption written in a zone's code is filed by the hash of its words.""")

rep("""12. **Allies in a fight**:""",
    """11a. **Boss hooks on a story fight**: `ArenaSpec` has a boss and a title but
    nothing to play when the boss arrives or falls. C10 to C14 need two hooks
    (a cinematic id, or a conversation to play as barks): on the boss's spawn,
    and on its death before the reckoning. Section 9 lists each.
12. **Allies in a fight**:""")

s = s.rstrip('\n') + """

## 9. Triggers, exactly

Where each cinematic starts, what is live in the game now, and what the
cinematic player replaces. "Live now" means its lines and effects are already
in play as plain captions, barks or a conversation, so the story is whole before
any cinematic exists; when the cinematic is built it takes the place of exactly
those calls. File references are `godot/logic/Play/Zones/`.

| Id | Conversation | Starts | Live now | The production agent wires |
|---|---|---|---|---|
| C01 | `cin_drowned_fire` | `Prologue.cs`, the night's first moment (stage `Wake`, where `Begin` sets the night and the objective "Survive the night"), straight after creation | Its three narrated lines as captions, in order | The cinematic in place of the three `G.Say` calls; the world held (`WorldRate` 0) with the risen mid-rise until its last shot |
| C02 | `cin_none_cross` | `Prologue.cs`, `Go(Stage.Intro)` (the approach to the ford); `RunIntro` | "Something lies in the ford..." as a caption; the evening call, "Lie down." and "NONE CROSS AFTER DARK." as the Warden's barks | The cinematic in place of `RunIntro`'s showcase and barks; the boss bar after its last shot |
| C03 | `cin_heart_goes_down` | `Prologue.cs`, `OnWardenDown`, then `RunVictory` | "Is it morning?" as the Warden's bark; the heart's caption; Grimtunnel's three barks ("Ooh, still lit!...", "...You smell like downstairs.", "...ever so grateful.") | The cinematic in place of `RunVictory`'s showcase and barks. The heart going down the hole stays in `Prologue.cs`; the cinematic only shows it |
| C04 | `cin_first_light` | Part A: `Prologue.cs`, `Douse` (the ember goes out at dawn). Part B: the first arrival at the Waystation's south gate after `prologue.done` | Part A's caption (the ember "back into the ground"; the mother's face); the guard's bark "Dawn arrivals..." | A in place of `Douse`'s caption; B on the first entry to the Waystation |
| C05 | `greymuzzle` | `Verge.cs`, interactable `greymuzzle` (Approach, while he is neutral): `G.Talk("greymuzzle")` | The conversation, as text | The cinematic staging the same conversation's choices (it is wordless) |
| C06 | `cin_forty_one_mouths` | `Verge.cs`, `Approach`, the Roost's branch when `KerchiefsFriendly()`, the first time (zone key `verge.roost_kitchen`) | The camp in a caption, the woman at the cages, and "Them first." | The cinematic in place of those three captions, ending on `G.Talk("redcowl")` |
| C07 | `brannoc` (`nell`) | `Waystation.cs`, Brannoc's conversation when it enters `nell` (Act 1's question about toll work) | The conversation, as text | The cinematic staging the same nodes and choices |
| C08 | `cin_iron_marker` | `Waystation.cs`, interactable `burial` in the Quiet Garden: `nell.burying` (true the burial morning only, rule `nell.burial`), by day, once (zone key `waystation.burial`). After C14 it starts from the square | A caption of the garden, then the hymn as Chid's conversation | The cinematic in place of the caption and `G.Talk` |
| C09 | `vonnra` (`fortune` to `f_door`) | `Waystation.cs`, Vonnra's conversation, the choice "Tell me my fortune." (after dark, `chapter.ready`); the stinger after the `fortune` action | The conversation, as text, including the interruption at `f_below` | The cinematic staging the fortune's nodes; the stinger before `Chapter.Summary` |
| C10 | none (wordless) | `Verge.cs`, story fight `hollow_by_night`: the boss's spawn, and its death | Nothing: the title card ("Who Kept the Cold Off") comes from `ArenaSpec.BossTitle` | Both parts on the boss hooks (section 6, 11a) |
| C11 | `cin_raid_on_the_roost` | Story fight `roost_raid`: spawn (`bairns`) and death (`last`) | The outcome: the fight's `OnWin` sets `redcowl.last_words` exactly as `last` does, so Rav's "the leg held" is reachable | The two parts on the boss hooks |
| C12 | `cin_dig_boils_over` | Story fight `dig_boils`: spawn (`pump`) and death, played as a retreat (`quiet`) | Nothing yet (title "Finders Keepers") | The two parts on the boss hooks |
| C13 | `cin_behind_the_door` | The door: `Verge.cs`, interactable `night:vault`, before `G.EnterArena`. Then story fight `vault_opened`: spawn (`nondum`) and death, played as the hand at the gate (`redi`) | Nothing yet; the door's Latin is already in `vaultdoor` | The door before the arena; the two parts on the boss hooks |
| C14 | `cin_road_back` | Dusk: a new node `brannoc.road` (the choice). Night: a new story fight `road_back` on the Low Ford road; spawn (`wat`'s title) and the dawn win | The night's outcome as told: the morning report (`nell.burial`) tells his going alone | The node, the facts (`nell.road`, `nell.brought_home`), the story fight with Brannoc as an ally, the report's variant; then the cinematic's four parts |

Nothing else starts a cinematic. The explorer (`docs/cloud/story-explorer.md`)
plays every `cin_*` conversation that something starts, so as each trigger
above is wired, its lines leave the explorer's unreached list.
"""
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
