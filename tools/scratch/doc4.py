import sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
rows = {
"| Arena champion, captain, keeper | 1 at 60% | 1 at 45% | the people's material ×1–2, or old iron (30%) | – |":
"| Arena champion, captain, keeper | 1 at 60% | 1 at 45% | the people's material (10%), old iron (20%): to the night's end tally | – |",
"| Arena miniboss | 1 at 60% | 1 | + 1 material | Uncommon; Rare+ ×1.5 |":
"| Arena miniboss | 1 at 60% | 1 | – (crafting's tally pays +2 at the end) | Uncommon; Rare+ ×1.5 |",
"| Arena herald, lieutenant | 1 at 60% | 1 | + 1–2 materials | Uncommon; Rare+ ×1.5 |":
"| Arena herald, lieutenant | 1 at 60% | 1 | – | Uncommon; Rare+ ×1.5 |",
"| Arena or story boss's hoard | 2 + tier/2 | 2, 3 from tier 3 | + 2–3 materials | first roll Rare; Rare+ ×2; Legendary ×4 |":
"| Arena or story boss's hoard | 2 + tier/2 | 2, 3 from tier 3 | + 1 material, to the tally | first roll Rare; Rare+ ×2; Legendary ×4 |",
"| Verge elite | 1 | 1 at 70% | the people's material | – |":
"| Verge elite | 1 | 1 at 70% | the people's material (10%), old iron (20%), on the ground | – |",
"| Map pack carrier (grade 1 / 2) | 1 / 2 | 1 at 55% / 1 + 40% | material | – / Rare+ ×1.3 |":
"| Map pack carrier (grade 1 / 2) | 1 / 2 | 1 at 55% / 2 at 70% | material (10%), iron (20%); the map's per-kill materials as before | – / Rare+ ×1.3 |",
"| Map keeper (grade 3) | 2+ | 2 | + material | first Uncommon; Rare+ ×1.4 |":
"| Map keeper (grade 3) | 2+ | 2 | the map's per-kill materials | first Uncommon; Rare+ ×1.4 |",
"| Map ruler | 3–5 | 3 + quantity | + 3 materials | first Rare; Rare+ ×2; Legendary ×4 |":
"| Map ruler | 3–5 | 3 + quantity | the map's per-kill materials (5) | first Rare; Rare+ ×2; Legendary ×4 |",
"   A carrier that drops no gear drops the people's material or old iron instead.":
"   A carrier that drops no gear now and then leaves its people's material or old iron, at rates\n   crafting measured; in the night's arenas these join the tally at the night's end.",
"About a third fewer gear drops than today, each one likelier to be Rare or better.":
"""About a third fewer gear drops than today, each one likelier to be Rare or better. The materials in
gear's place are crafting's measured rates (`CraftingEconomy`): a tenth the people's material, a
fifth old iron, which leaves Act 1's stores about where they were; more piled up and meant nothing.
In the night's arenas they are not dropped but join the night's end tally (crafting decision 7: no
confetti, the tally is the moment), and a fall spills half of them as it does the rest.""",
}
for a, b in rows.items():
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print("ok")
