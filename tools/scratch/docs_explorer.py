import os

W = os.path.join(os.getcwd(), 'docs', 'WRITING_PASS.md')
s = open(W, encoding='utf-8').read().rstrip('\n')
s += """

## 16. The story explorer's findings (3 October)

The explorer (`docs/cloud/story-explorer.md`) found no softlock, dead end or
contradiction. It raised four things; each is settled here.

- **Wenna's mask** (`wenna.first` and `wenna.hub`, "That beaked mask on the
  wall..."). It wanted affection 20, which only two bitterroot deliveries (or
  one and the teamsters freed) could reach. A survivor who cured the stream
  first could never earn it, though curing it is the thing Wenna cares about
  most ("The stream's clean, child. Clean."). **Now:** affection 20, *or* the
  stream cleared by the survivor (history `stream_cleared`) and not sold to
  Pell (`beasts.outcome` not `exploited`). The curer's mask has her own line:
  "You cleaned my stream, child. Take it. ...Something down there's still
  cooking, and I'm too old to go where it's needed." (Act 2's bad air.) [DATA,
  done; `CinematicTests.Wenna_gives_her_mask_to_whoever_cleaned_her_stream`]
- **Keegan's supper** (`keegan.hub`, "It's late. Have you eaten?"). It is the
  romance's Act 1 beat (`docs/romance/`), so it should be reachable by the
  survivor who listens to her. **Now:** respect 25 and affection 10, at night,
  after the first dinner. The road, all in her own conversation:
  - tell her about the Ford-Warden (the dead watchman's book teaches
    `lore.warden`; `keegan.warden`, respect +15);
  - ask her about Ashe (Rook's first lamp teaches `lore.ashe`; `keegan.ashe`,
    respect +10);
  - accept the dinner ("Does the handbook say anything about dinner?",
    `keegan.dinner`, affection +10);
  - then come back after dark.
  Deeds that raise everyone's regard (the teamsters freed) can stand in for one
  of the first two. [DATA, done;
  `CinematicTests.Keegan_sups_with_whoever_listened_to_her`]
- **The cinematics' conversations** (`cin_*`). Nothing started them. Each
  trigger is now in `docs/cinematics/README.md` section 9, exactly. What could
  live without the cinematic player is live now [CODE, done]:
  - the opening's prints in the frost (C01);
  - the Warden's evening call, "Lie down." and "Is it morning?" (C02, C03);
  - Grimtunnel's "You smell like downstairs" and "ever so grateful" (C03);
  - the ember going "back into the ground" (C04);
  - "Them first." at the Roost (C06);
  - Nell's burial in the Quiet Garden on its morning, as a conversation (C08;
    the rule `nell.burial` sets `nell.burying` for that day only);
  - Redcowl's last words as the Roost raid's outcome (C11), so Rav's "the leg
    held" is reachable.
  The night fights' scenes (C10 to C14) wait for boss hooks on `ArenaSpec`.
- **`dig.pump = running`** was asked about and never written. **Now** a rule
  (`dig.pump.running`) writes it at the first dawn, as the state the Dig is in
  until someone moves, breaks or blows the pump; Act 2 reads it ("still
  running at the act's end"). [DATA, done; `CinematicTests.The_pump_runs_until_someone_stops_it_and_the_burial_is_one_morning`]
"""
open(W, 'w', encoding='utf-8', newline='\n').write(s + '\n')

B = os.path.join(os.getcwd(), 'docs', 'STORY_BIBLE.md')
b = open(B, encoding='utf-8').read()
anchor = "\n## 10. The consequence ledger"
assert b.count(anchor) == 1
b = b.replace(anchor, """
### The nights: what a fight may change

The systems are the systems agent's (`docs/bosses/`, `docs/bestiary/`). This is
the story's view of them, so that the nights tell the story the days write.

- **What an arena is.** The survivor is the brightest thing in the dark, and the
  light in her is the valley's dead. Everything that has lost a light comes to
  it; the more she carries, the more come. The arena's rising horde is that,
  and nothing about it needs saying before Act 3. **The Dawn as every arena's
  end** is the world's own rule (the ember drains at sunrise) and is right; after
  C43 every dawn is the night's dead going home.
- **Bosses speak as themselves.** A story boss's lines are its cinematic's
  (C10 to C14): Greymuzzle wordless, Redcowl's bairns and his last words,
  Grimtunnel's faith, the Barrow Lord's two words, Wat's silence. No generic
  taunts. Titles are the valley's words: *Who Kept the Cold Off*, *Of the
  Kerchiefs*, *Finders Keepers*, *Of the Seventh Legion*, *Over the Ford by
  Dark*.
- **Grimtunnel never dies in an arena.** Confirmed: he is at the bottom of the
  stair in Act 3 with the heart. Every fight with him ends with him driven back
  down the hole, delighted. A table arena may field a lampling foreman, never
  him, and never his name.
- **Keegan's duel is at first light,** not by night. Her handbook's seventh
  article says the return is made "at dawn, when it is weakest", and she does it
  by the book: the ember has gone out of the survivor, who is ordinary and
  warm, her breath smoking, and fights with what she carries. It is a day fight
  without ember, which is the point: the knight chose the hour the book chose,
  and it is the hour the survivor is most nearly alive.
- **New outcomes from fights,** taken or trimmed:
  - *Greymuzzle let go:* yes, narrowly. Only if she knelt and promised (C05) and
    the stream already runs clear. At the end of the Hollow by night he goes
    down, and does not die: he gets up, slowly, and goes to the den among his
    sick, and she lets him. `greymuzzle` = `spared`; `beasts.outcome` stays
    `cured`; Maeca hears of it, and it is the one fight that raises her regard.
    C10 gains that variant (his eye on the den, then on her, and he walks).
  - *The crates blown in the Roost fight:* yes, as the value that already exists:
    `be.crates` = `burned`, with its consequences (Act 2's breakthrough is
    narrower; the army has no powder). No new value.
  - *The pump broken or blown by how the Slurry Engine ends:* yes, as
    `dig.pump` = `broken` or `blown`. No new value.
  - *Edric lost if the Keeper escapes* (Silverstair): yes. `edric.freed` stays
    unset, and Ysolde's ends narrow to "dies at Silverstair" or "keeps
    selling".
- **Banes learned by day** (Maeca's fed fires, Chid's standard, Grimtunnel's own
  lamp): yes. They are story knowledge, earned in conversation, and the day half
  arming the night is the shape of the game.
- **Thieves:** a lampling that takes ember stones off the ground is true to the
  lamplings, who carry their dead down on purpose ("Nobody's!"). Never what the
  survivor holds. Name it in their words (a carrier), not a genre's.
- **Two peoples at war in one arena:** the Kerchiefs against the lamplings is
  Act 2's truth (Redcowl fights the Dig); it fits from Act 2, not before.
- **The ending decides the nights** (section 8): after re-forging, the scars
  open and the player knows what they are; after breaking the chain they never
  open again; after taking the light, the survivor is the boss in every one.
""" + anchor)
open(B, 'w', encoding='utf-8', newline='\n').write(b)
print('ok')
