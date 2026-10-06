"""Folds the owner's 4 October answers into ASSET_PROVENANCE.md, row by row (legal lead).
Each target row is split into its cells, the named cells replaced, and the row rebuilt;
the script stops if a row's shape is not what it expects."""
import sys

P = sys.argv[1]
text = open(P, encoding='utf-8').read()
L = text.split('\n')
REC = '`docs/legal/records/BODIES_RECORD.md`'


def row(tag):
    hits = [i for i, l in enumerate(L) if l.startswith('| ' + tag + ' |')]
    assert len(hits) == 1, (tag, hits)
    return hits[0]


def set_cells(tag, n, changes):
    i = row(tag)
    cells = L[i].split(' | ')
    assert len(cells) == n, (tag, len(cells))
    for k, v in changes.items():
        if callable(v):
            cells[k] = v(cells[k])
        else:
            cells[k] = v
    L[i] = ' | '.join(cells)


# People rows: | id | path | what | source | licence | attribution | ships | risk | replacement |
set_cells('PE-06', 9, {
    3: lambda s: s + ('. **Answered (owner, 4 Oct):** the picture was made in our own ComfyUI with Krea 2 Turbo, '
                      'and the mesh by TRELLIS 2 there; no web tool, no Hunyuan. The record: ' + REC),
    4: 'Krea 2 Community License (the picture, AI-01); MIT (TRELLIS 2, the mesh)',
    5: 'No',
    7: ('low, with conditions (legal, 4 Oct): the owner signs the record and confirms no real person or '
        "others' art went into the picture; the body joins the Krea footprint (AI-01)"),
})
set_cells('PE-09', 9, {
    3: lambda s: s + ('. **Answered (owner, 4 Oct):** the picture came from Krea 2 Turbo in our ComfyUI, '
                      'probably with the Civitai LoRA in AI-15 (the log shows 256 LoRA patches); '
                      'TRELLIS 2 ran at 00:28 and the file landed at 00:38 on 4 Oct. The record: ' + REC),
    4: 'Body: Krea 2 Community License (the picture) and MIT (TRELLIS 2); head CC0; face under the Krea licence',
    5: 'No',
    6: 'Not in release builds until his base garment exists (export exclude, 8a770667)',
    7: 'low, with conditions (body, as PE-06); high, business (Krea face and picture: AI-01)',
})
set_cells('PE-05', 9, {
    7: lambda s: s + ' Excluded from release builds (8a770667), so nothing to clear',
})
# AI rows: | id | model | licence | what it made | ships | risk | notes |
set_cells('AI-04', 7, {
    3: "PE-06's and PE-09's bodies (the owner, 4 Oct; " + REC + '); the first heroine attempt (c528caf, superseded)',
    5: 'low: inputs are Krea 2 Turbo pictures made locally (AI-01)',
})
set_cells('AI-14', 7, {
    3: 'Nothing: the owner says the bodies were made in our ComfyUI (AI-01, AI-04), not in Meshy',
    4: 'No',
    5: 'none',
    6: 'Owner question 1, answered 4 Oct',
})
set_cells('AI-15', 7, {
    1: lambda s: s + ('. **Identified (legal, 4 Oct):** Civitai model 2728644, "[KREA 2] Mystic XXX" by alcaitiff, '
                      'v1.0 of 25 Jun 2026 (found by its SHA-256)'),
    2: ('MiniMax H3 Community License; Mystic XXX: Krea 2 base terms, and the creator allows commercial use of '
        'images (Image, Sell, Rent), no credit, derivatives (Civitai)'),
    3: "Probably the picture for the hero's body (PE-09); the log fits its 256 layers",
    5: 'low: allowed by its creator; flagged an adult concept LoRA, not a real person',
    6: 'Owner question 6: the owner to confirm which LoRA the hero picture used. Either is allowed',
})

text = '\n'.join(L)

# The owner questions and the top risks, answered in place.
swaps = [
    ('1. What made `234.glb` (the heroine\'s body): Meshy, TRELLIS 2, Hunyuan3D-2 or something else?',
     '1. **Answered (4 Oct):** Krea 2 Turbo made the picture and TRELLIS 2 the mesh, both in our ComfyUI (' + REC + '). '
     'Asked: what made `234.glb` (the heroine\'s body): Meshy, TRELLIS 2, Hunyuan3D-2 or something else?'),
    ('3. What picture was `ComfyUI_00008.glb` (the male hero, TRELLIS 2) made from',
     '3. **Answered (4 Oct):** a Krea 2 Turbo picture made in our ComfyUI. Asked: what picture was `ComfyUI_00008.glb` (the male hero, TRELLIS 2) made from'),
    ('5. Do you hold the rights to The Ember Watch',
     '5. **Answered (4 Oct):** the owner made it, with Claude; no third party (brief issue 5(e)). Asked: do you hold the rights to The Ember Watch'),
    ('6. Did you use the `MysticXXX_KREA2_v1` LoRA',
     '6. **Partly answered (4 Oct):** the log suggests it made the hero\'s picture; the LoRA is identified, and its creator allows commercial use (AI-15). Asked: did you use the `MysticXXX_KREA2_v1` LoRA'),
]
for a, b in swaps:
    assert text.count(a) == 1, a
    text = text.replace(a, b)

note = ('\n> **Update, 4 October 2026 (evening), by the legal lead (aab20546fe06daa89), from the owner\'s answers.** '
        'The bodies (PE-05, PE-06, PE-09) were made locally: Krea 2 Turbo pictures, TRELLIS 2 meshes, in our ComfyUI. '
        'They are now low risk with conditions, and part of the Krea footprint (AI-01). The Ember Watch (DA-02) is the owner\'s. '
        'The Mystic XXX LoRA (AI-15) is identified, and commercial use is allowed. The counts below are as audited; '
        'the rulings are in `docs/legal/LEGAL_BRIEF.md` issue 5.\n')
anchor = '## Summary\n'
assert text.count(anchor) == 1
text = text.replace(anchor, anchor + note, 1)
open(P, 'w', encoding='utf-8', newline='\n').write(text)
print('updated')
