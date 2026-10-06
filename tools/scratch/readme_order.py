"""The recording order in docs/voice/elevenlabs/README.md: the narrator on hold, the finals named."""
P = "docs/voice/elevenlabs/README.md"
t = open(P, encoding="utf-8").read()
a = t.index("1. **The narrator** ([packet](narrator.md))")
b = t.index("## The packets")
new = """**Record now** (final, signed by the story lead): Mother Rook, Captain
Holloway, Brannoc and Sella, in that order.

1. **The narrator** ([packet](narrator.md)): **on hold. Do not record him
   yet.** The owner has asked whether Vonnra should be the narrator (the
   voice that calls the survivor to town in the prologue), given her twist,
   and the story lead is deciding. His lines keep their placeholders until
   then.
2. **Mother Rook** ([packet](rook.md)): the first conversation, and the hub
   the player returns to.
3. **Captain Holloway** ([packet](holloway.md)), **Brannoc**
   ([packet](brannoc.md)), **Sella** ([packet](sella.md)): final. Then
   **Vonnra** and **Harlan**, once the story lead signs them off.
4. **Chid**, **Maeca**, **Ysolde**: after the story editor's review.
5. The rest: Pell, Rav, Keegan, Wenna, Tam, Jory, Redcowl, the watch, the
   townsfolk, the creatures and the dead.

"""
open(P, "w", encoding="utf-8", newline="\n").write(t[:a] + new + t[b:])
print("ok")
