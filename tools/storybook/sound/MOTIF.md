# The motif: the Order's evening call

The melody the Warden sings under the water, and the score's one tune. It was read off the existing take `godot/art/vo/warden/dlg.cin_none_cross.call.0.ogg` with `pitch.py` (YIN), then snapped to the game's key: D minor, rooted on D3 = 146.83 Hz (`godot/src/Audio/Music.cs`), A4 = 440.

## What the take gives

The take is a low, half-spoken dirge with heavy water processing. About half of it has no steady pitch (breath and consonants). What has pitch:

| Take time (s) | Word | Measured | Snapped to D minor |
|---|---|---|---|
| 0.08-0.14 | **Lamps** | B2 -40 c (about 120 Hz) | **Bb** |
| 0.37-0.53 | **are** | glides from B2 -30 c down to G2 +54 c, centred near A2 | **A**, reached by a fall from Bb |
| 1.60-1.70 | **lit** | D2 +60 c (about 76 Hz) | **D** (the tonic) |
| 4.14-4.70 | **stay** | B2 +30 c, falling to G2 | **Bb falling to G** |
| 4.77-4.96 | **where** | rises from Bb2 -40 c to B2 -10 c | **Bb** |
| 5.17-5.47 | **they** | B2 -30 c falling to A2 +20 c | **Bb falling to A** |
| 5.58-5.70 | **reach** | F2 +15 c | **F** |
| 5.81-6.05 | (reach, held) | B2 +30 c falling to A2 +45 c | **Bb falling to A** |
| 6.14-6.29 | (trailing off) | B2 -15 c, short and breathy | not used |

His "Bb" sits between Bb and B, nearer B in places. B natural isn't in D natural minor, and Bb is the darker, older note that the rest of the take supports, so it's Bb. The high G4 the tracker reports at 1.95-2.1 s is the "t" of "lit" (a formant, not a sung note) and isn't used.

**Measured vs added:** phrase 1 is wholly measured. Phrase 2 is measured up to the last fall to A. **The take trails off without a last note, so phrase 2's final D is added** (mirroring phrase 1's close on the tonic) to make the call end at home.

## The motif

The take's octave is the singer's (Bb2 to D2). The bowed solo plays it an octave up (Bb3 to D3, cello and viola register). The river's voice in P8 and P10 sings it at the take's octave.

**Phrase 1, "Lamps are lit"** (usable alone: the score uses it on its own in P1, P9 and at the drowning):

```
 Bb    A      D
 Lamps are    lit
 1     1.5    2.5+  (beats; the A slides down from the Bb)
```

**Phrase 2, "stay where they reach"**:

```
 Bb  ->G   Bb     Bb->A   F      Bb->A   D
 stay      where  they    reach  (-)     (-)
 1.5       0.75   0.75    0.5    1       2+
```

In score pitch: Bb3 A3 D3 | Bb3(to G3) Bb3 Bb3(to A3) F3 Bb3(to A3) D3. The range is D3 to Bb3, a minor sixth inside the octave. Both phrases end on the tonic. The falls (Bb to A, Bb to G) are the take's own glides and part of the tune: a sigh down onto each word's end.

**Tempo:** the take sings phrase 1 in about 2.1 s and phrase 2 in about 2.5 s with 1.7 s between. The score runs from about the take's tempo (P9, P2) to half of it (P1, P6).

## Harmony used in the score

From the Night mood's chords (`Music.cs`: Dm, Bb, G, Am):

- Lamps (Bb): Bb major. are (A): F major. lit (D): D minor.
- stay (Bb to G): G minor. where (Bb): Bb major. they (Bb to A): F major. reach (F): Bb major (in P6) or D minor (P3). (A): A minor. last (D): D minor.

## For the final recordings

A singer or player matching this should keep the Bb as the reciting note, let "are", "stay", "they" and the held "reach" fall off it, and land "lit" and the end on a low D. The words sit one syllable to a note except the held "reach" (two notes, F then the Bb-to-A fall).
