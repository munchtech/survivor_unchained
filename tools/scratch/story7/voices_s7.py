"""VOICES.md, VO_CAST.md and the packet tool, to the approved rewrite."""
import os
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a38d66ae66583ace1"

def edit(rel, pairs):
    p = os.path.join(WT, rel)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert old in s, (rel, old[:60])
        s = s.replace(old, new)
    open(p, "w", encoding="utf-8", newline="").write(s)

edit("docs/VOICES.md", [
    ("""**The narrator.** Present tense, second person, plain nouns and working
verbs; one image per line, never two adjectives where one will do. Says
what happens and what can be seen, never what it means. Never theatrical,
never cute, never names a feeling the scene has already shown. *Casting:*
50s, neutral RP, low and close; a winter's tale told by the fire, slight
gravel, unhurried.""",
     """**The narrator.** Present tense, second person, plain nouns and working
verbs; one image per line, never two adjectives where one will do. Says
what happens and what can be seen, never what it means. Never theatrical,
never cute, never names a feeling the scene has already shown. Never enters
a bedroom: at a love scene the voice stops at the door. Says less from Act
2's turn on (shorter dawns, a line missing here and there), and the player
should take it for style. *Casting (the owner, 6 October):* a woman of about
sixty, plain and dry, level, a woman who has told people bad news before;
the valley's accent, lightly (northern, not RP). No warmth, no "winter's
tale": she lets warmth in once in the whole game, at "There you are." The
quoted words of the survivor's mother ("Lamp's lit, Spark.") are said exactly
as plainly as the rest; she does no voice for anyone."""),
    ("""the surface. Says "proof", never "evidence". Never says sorry; the nearest
he gets is paying for something. Goes very quiet whenever Ashford or Maeca
comes up. *Casting:* 45, Lancashire flattened by the army; hoarse from
shouting.""",
     """the surface. Says "proof", never "evidence". Never says sorry (it is written
once, in his daybook, found after his death); the nearest he gets is paying
for something. Never talks about boots. **Drunk, he talks like his own
ledger:** entries, no subjects, numbers without nouns ("Ninety-one up. Lid
down. Three days."), and nobody else talks like that. Sober, Ashford is "the
report"; drunk, at the gate, it is the truth. Laughs once in the whole
game, in the hole at the Penhale farm. *Casting:* 45, Lancashire flattened by
the army; hoarse from shouting."""),
    ("""**Maeca Barefoot** (the Ashford Garrison). Few words, all of them about
ground, tracks, weather and animals. Level, quiet, present tense. Calls the
wolves "the Pack" or "them", never "beasts" or "monsters". Contempt is
quiet and final. Never raises her voice; never talks about Ashford except
in three words or fewer. *Casting:* 30s, Welsh borders, a hunter's
half-voice with a hard edge.""",
     """**Maeca** (the Ashford Garrison). Just Maeca: no other name. Few words, all
of them about ground, tracks, weather and animals. Level, quiet, present
tense. Calls the wolves "the Pack" or "them", never "beasts" or "monsters".
Contempt is quiet and final. Never raises her voice; about Ashford she says
three words, "The cave mouths.", and nothing else. Signature: "I track for
the Watch, before you ask. Not wolves." Every kindness she does Holloway is
true, and is a hunter waiting. *Casting:* 30s, Welsh borders, a hunter's
half-voice with a hard edge."""),
    ("""talk about weather. Never small talk, never thanks anyone in words (once:
when he is told his daughter's end was quick).""",
     """talk about weather. Never small talk, except his girl: the one thing he
talks about unasked, and the only time he sounds happy ("Irons on it. Mine.
Ten. Best I've done."). Never thanks anyone in words (once: when he is told
his daughter's end was quick)."""),
])

edit("docs/VO_CAST.md", [
    ("| The narrator (`narrator`) | 55 m, neutral southern English (RP) |",
     "| The narrator (`narrator`) | 60 f, plain and dry, light northern valley accent (recast 6 October; not yet cast) |"),
    ("| Maeca Barefoot (`maeca`) |", "| Maeca (`maeca`) |"),
])

edit("tools/vo/elevenlabs.py", [
    ('"maeca": "Maeca Barefoot",', '"maeca": "Maeca",'),
    ('HOLD_VOICES: dict = {"narrator": "the owner has asked whether Vonnra should be the narrator (the voice that calls the survivor to town in the prologue), given her twist; the story lead is deciding"}',
     'HOLD_VOICES: dict = {\n'
     '    "narrator": "recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording",\n'
     '    "holloway": "the story rewrite changes most of his lines (docs/voice/RERECORD.md)",\n'
     '    "brannoc": "the story rewrite changes most of his lines (docs/voice/RERECORD.md)",\n'
     '    "maeca": "the story rewrite changes most of her lines (docs/voice/RERECORD.md)",\n'
     '    "vonnra": "the story rewrite changes the fortune (docs/voice/RERECORD.md)",\n'
     '    "harlan": "the story rewrite changes some of his lines (docs/voice/RERECORD.md)",\n'
     '}'),
])
print("ok")
