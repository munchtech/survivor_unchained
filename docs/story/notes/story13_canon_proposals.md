# The WTF pass: three canon proposals for the owner (Story 13, 29 October 2026)

The editor scored the eight beats on one question, "would a player say what the
fuck out loud, as the game is now": "You did this" 5, "Ninety-two" 7, the woman
with the lamp 8 on paper and 5 as built, the voice 7, "It takes less than it did"
7, "Not yet" 7, "Count's right" 8, the act endings 6. The shapes are right. What
leaks is mostly build (Acts 2-3 aren't in the data; the toll isn't built), and
three places where canon can be sharpened cheaply. Line-level fixes are done on
the branch; these three change what happens, so they're yours. **Yes/no per
item is enough.** P1 and P2 are already drafted in the data on `story-wtf`, not
in MR1; a yes makes MR2, a no takes them out in a minute.

## P1. Rook gives the word on day one (Act 1, one new line)

**Now:** with reveal A the narrator never says "Lamp's lit, Spark" before the
stair, so the only place a player can learn the word is an optional Chid choice
on day 3 (the journal). A player who skips it reaches C43 and hears a name they
never heard. **Change:** right after Rook's lie ("She went in her sleep, pet... I
sat with her, after."), Rook adds, in her own voice: *"She'd sit at my back
window at dusk, the week she was here, and say it to the road. 'Lamp's lit,
Spark. Stay where it reaches.' (She picks the cup up again.) I took it for a
prayer."* New canon fact: in her last week the mother said the call every dusk
at Rook's window, and Rook heard it. **Buys:** every player holds the exact words
and the name from the first ten minutes, in a mouth that isn't the narrator's;
the Watch's gate call stays the plural ("Lamps are lit. Stay where they reach."),
so the one-lamp version is hers alone; at C43 the shock is the VOICE saying the
line Rook quoted. Re-read: Rook had the mother's last words and sold her date.
**Kept out on purpose:** the lamp and the river bank (the player has just cut
down the woman with the lamp; "went down to the bank every dusk" would hand them
C32 on day one). **Cost:** one Rook line (`rook.mother_word`, unrecorded; Rook's
other lines untouched), the bible's §1 sentence, nothing built. Editor: agree.

## P2. The letter keeps one line the player can read

**Now:** the letter in her coat is ink run to blue water, "no word is left"; the
player knows there was a letter only because the quest summary says so. Chid's
knife at C42/C43 ("He'd written that I'd be at the water, so you'd see me")
lands on an object the player never read. **Change:** one line survives the
water: **"Come home by the Low Ford."** Seen in the C04 A insert (the letter
moves there from C01 in the new opening) as an object only, no narrator line
about the hand; kept in the journal (`home` quest, entry `letter`: *"The letter
that brought you home, run to blue water. One line still reads: 'Come home by
the Low Ford.'"*). **Buys:** the player walked to the ford on a sentence they
carried in their own coat; at C32 (Rook: she took it to the carrier) and C42-43
(Chid chose its words) the knife is in their pocket. **Risk:** none before Act 3
(the editor checked; the lamp and the hand stay unseen). **Cost:** the journal
entry (in the data), a legible line on the letter prop for Cinematics' C04 A
insert, one bible sentence.

## P3. The kill and the count are split (Act 2, treatment only; nothing is built)

**Now (§4.5, §7):** at the lip of the hole Holloway grins "Count's right" and
climbs into Maeca's knife; the rope runs; then Maeca, flat, to nobody:
"Ninety-two." The two reveals land in one beat, and the number explains the grin
on the spot. **Change:** nobody says a number at the kill. The grin, the cut,
the lamp going down the dark, the silence; the Pack walks away; Tolley's lips
move and stop (no spoken count). Four dusks later at the gate (C20b, already
canon), the risen Holloway counts aloud to ninety-two, Maeca at the well looking
at her hands, and the player does the sum themselves; her "...He counted me."
moves to his table (C22, the daybook's "92." and "Sorry."). **Buys:** the kill
is pure what-the-hell (a grin that makes no sense yet, the owner's HOLY SHIT
with nothing softening it); the gate is the click, giddy and knife at once (he
knew for ten years); "Both numbers are right" (`scene_knocking.saved`) stays as
the setup that makes "Count's right" a count. **Loses:** Maeca's one answer to
the grin at the hole; her silence there reads as ten years. **Cost:** TREATMENT
§4.5 step 7, §4.6, §7's two Act 2 rows; Act 2 isn't in the data. Editor: agree,
with the Tolley fix above.

## Done without a gate (line level, on the branch)

The dropped-lamp plant the treatment lists as "on the trunk" wasn't in the data:
`cin_first_light.lamp_out`, the dawn's first line, *"On the stones at the
water's edge, a lamp lies on its side. It has gone out."* (Cinematics adds the
prop and the cue to c04a.json.) The narrator's figures that didn't resolve are
plain now (greymuzzle, Sella's stairs, Pell's door). Routed, not mine: the toll
("It takes less than it did", `TOLL_SPEC.md`) is the one canon twist with no
data presence at all (only the rise line in `Journey.Day.cs`); the drowned woman
lifting a dead lamp at the ford isn't staged in `Prologue.cs`. Both need a build
slot (combat/story-code; prologue staging) before Act 1's knives can land.
