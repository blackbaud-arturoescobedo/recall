# Recall — Copilot Instructions

This workspace uses **Recall** for persistent memory. Recall stores architectural decisions, notes, and working status across sessions via a local ChromaDB vector database exposed through MCP tools.

## Using Recall in Every Session

When answering questions about this codebase, **search Recall first** using the `search` tool to pull in relevant context the developer has explicitly saved — decisions, trade-offs, open questions, and current focus.

Specifically:
- Before answering architecture or design questions, call `search` with the key topic
- Before asking clarifying questions the developer may have already answered, call `search` first
- When you notice a decision being made mid-conversation, offer to `remember` it

## Available Recall Tools (MCP)

| Tool | When to use |
|------|-------------|
| `search(query)` | Pull relevant memories before answering a question |
| `remember(content)` | Save a decision, choice, or fact the developer just made |
| `note(content)` | Save an observation, open question, or to-do |
| `set_status(content)` | Update what's actively being worked on |
| `list_memories()` | Show all saved context at session start |
| `forget(keyword)` | Remove outdated or incorrect memories |

## Example Flows

**Starting a session:** Call `list_memories()` and `search("current status")` to orient yourself before the first response.

**Mid-conversation decision:** Developer says "let's use Zod for validation" → offer to call `remember("chose Zod for runtime schema validation")`

**Ending a session:** Offer to call `/Export-to-Recall` or call `set_status` with what was left in-progress.
