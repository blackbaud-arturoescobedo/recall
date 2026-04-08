---
description: "Start a session with full Recall context — pulls all saved memories and current status so Copilot knows exactly where you left off"
name: "Recall Briefing"
argument-hint: "Optional: a topic to focus the search on"
agent: "agent"
---

Pull context from Recall to orient this session.

Steps:
1. Call `list_memories()` to get all saved memories
2. Call `search("current status working on")` to find the most recent focus
3. If the user provided a specific topic as an argument, also call `search` with that topic

Then respond with a concise briefing in this format:

**Where you left off:**
[Most recent status entry]

**Key decisions on record:**
[Bullet list of the most relevant `remember` entries — max 5]

**Open questions / notes:**
[Bullet list of `note` entries — max 3, most recent first]

Keep the briefing short. End with: "Ready — what are we working on?"
