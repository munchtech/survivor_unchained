Spawning: not allowed
Context budget: 150k

## Doc-archiving worker (9 Nov, owner: "re-reading is a big portion of usage"): make the files every lead reads hold only what is current

Main checkout, integration branch, no code changes, nothing edited, only moved.
1. `docs/team/OWNER_NOTES.md`: keep blocks dated 1 Nov 2026 or later; move older blocks verbatim to `docs/team/OWNER_NOTES_HISTORY.md` (title + "moved 9 Nov 2026, nothing edited"); add one pointer line at the bottom of OWNER_NOTES ("Older decisions: OWNER_NOTES_HISTORY.md; grep by keyword, never read whole").
2. Every `docs/handoff/*.md` except lead_brief.md: keep the title/intro and the TOP TWO `## ` blocks; move older blocks verbatim to `docs/handoff/history/<same name>`; one pointer line after the second block. Files with two or fewer blocks untouched.
3. Do not touch lead_brief.md, RESUME.md, PIPELINE.md, docs/design.
4. Two commits (OWNER_NOTES; handoffs), Co-Authored-By line, push. Report files, blocks moved, shas, before/after line counts.

Then (the coordinator, Fable, ~20k, not the worker): condense `docs/handoff/lead_brief.md` to a <=2,500-token "Rules" top (junction rule, delete rule, kill by PID, usage rules, report shape, half-size pictures, handoff at 200k) with the rest under "## Appendix (read only when a brief points at a line)". And per area, the handoff's top block IS the start pack: one file a successor reads, nothing else.
