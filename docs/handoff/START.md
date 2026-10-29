# Starting a fresh coordinator (the owner's one-step restart)

When: at each new wave, after a usage reset, or when the coordinator says its context is past about 250k. The coordinator says so in one line.

How, in the Claude desktop app:
1. In the Code tab, start a new session with the folder `C:\Users\munch\Desktop\survivorsunchained`. It must be this folder, so that agents' worktrees land in the game repo.
2. Pick Opus 5.5 at high effort.
3. Paste the prompt below, then add any new notes of your own under it.

---

You are the coordinator for Survivor Unchained. Your memory loads automatically. Read docs/handoff/coordinator.md "Start here" and do only what it says at startup (it names the one other section to read). Restart the leads RESUME's top section lists, each a fresh successor, with docs/handoff/lead_brief.md. Tell me in a few lines what you're starting and why, then start. Go.

## Switching Claude accounts (the owner, 22 October)
Claude support (in-app, 22 Oct) confirmed the owner may hold up to three Claude accounts verified with one phone number (different emails; wait seven days between phone verifications). Screenshot: `survivorsunchained_inputs\owner_frames_22oct\support_multiple_accounts.png`.
- One coordinator at a time. Before switching, the current coordinator winds down fully ("Wrapping up before a fresh start" in coordinator.md: every agent stopped, nothing live) and says so.
- Then sign the desktop app in to the other account and start exactly as above: same folder, Opus 5.5 at high, the prompt above. Repo, memory (`C:\Users\munch\.claude\`), agent types and settings live on this PC, not in the account, so nothing else is needed.
