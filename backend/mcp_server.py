"""
Recall MCP Server
Exposes Recall's memory tools to Copilot agent mode and other MCP clients.
Run via stdio — configured in .vscode/mcp.json.
"""

from mcp.server.fastmcp import FastMCP
from indexer import save_memory, get_memories, search_memory, delete_memory

mcp = FastMCP("Recall")


@mcp.tool()
def remember(content: str) -> str:
    """Save an important fact, architectural decision, or technical choice to Recall's permanent memory."""
    memory_id = save_memory(content=content, memory_type="remember")
    return f"Remembered: {content}"


@mcp.tool()
def note(content: str) -> str:
    """Save an observation, open question, or thing to revisit to Recall's memory."""
    memory_id = save_memory(content=content, memory_type="note")
    return f"Note saved: {content}"


@mcp.tool()
def set_status(content: str) -> str:
    """Save the current working status — what is actively being worked on right now."""
    memory_id = save_memory(content=content, memory_type="status")
    return f"Status updated: {content}"


@mcp.tool()
def list_memories(limit: int = 20) -> str:
    """List all memories saved in Recall."""
    memories = get_memories(limit=limit)
    if not memories:
        return "No memories stored yet."
    lines = []
    for m in memories:
        emoji = "💾" if m["type"] == "remember" else "📝" if m["type"] == "note" else "📍"
        lines.append(f"{emoji} [{m['date']}] ({m['type']}): {m['content']}")
    return "\n".join(lines)


@mcp.tool()
def search(query: str) -> str:
    """Search Recall's memory for context relevant to a query."""
    results = search_memory(query, n_results=5)
    if not results:
        return "No relevant memories found."
    lines = []
    for r in results:
        lines.append(f"[{r['filename']}]: {r['content'][:200]}")
    return "\n\n".join(lines)


@mcp.tool()
def forget(keyword: str) -> str:
    """Delete memories from Recall that match a keyword."""
    memories = get_memories(limit=100)
    deleted = []
    for m in memories:
        if keyword.lower() in m["content"].lower():
            delete_memory(m["id"])
            deleted.append(m["content"][:60])
    if deleted:
        return f"Deleted {len(deleted)} memories matching '{keyword}':\n" + "\n".join(f"- {d}" for d in deleted)
    return f"No memories found matching '{keyword}'"


if __name__ == "__main__":
    mcp.run()
