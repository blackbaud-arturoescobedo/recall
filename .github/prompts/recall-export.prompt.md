---
description: "Export this session to Recall — saves decisions, notes, and status directly into Recall's permanent memory using MCP tools"
name: "Export to Recall"
argument-hint: "Saves session context directly into Recall"
agent: "agent"
---

Summarize this session and save it directly to Recall using the available Recall MCP tools.

Use these tools based on what was discussed:
- `remember` — for architectural decisions, technical choices, or important facts that should persist long-term
- `note` — for observations, open questions, or things to revisit
- `set_status` — for what was actively being worked on at the end of this session (call once only)

Rules:
- Call a maximum of 6 tools total
- Be specific: include file names, function names, and PR numbers where relevant
- Call `set_status` once with the most recent active task
- After saving, confirm with a single line: "Saved X memories to Recall."
