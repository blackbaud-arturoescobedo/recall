# Recall
### Persistent Memory for Your AI Developer Tools

> Your AI pair programmer finally has a memory.

Recall is a VS Code extension that gives your AI tools persistent memory — locally, privately, and without changing how you work. It combines a sidebar chat powered by Claude with an MCP server that Copilot can query directly, so every session starts with full context automatically.

---

## The Problem

Every AI coding tool today loses context when the session ends. You re-explain your architecture, your decisions, your conventions — every single time. Copilot Memory expires in 28 days and requires IT approval. Chronicle sends your git history to GitHub's servers. Recall solves this locally, permanently, and without changing how you work.

---

## Setup & Run Instructions

### Prerequisites
- VS Code 1.85 or higher
- Python 3.11 or higher (3.14 works but 3.11 recommended for package compatibility)
- Node.js 18 or higher
- An Anthropic API key (console.anthropic.com)

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/blackbaud-arturoescobedo/recall.git
cd recall
```

**2. Set up environment**

Create a `.env` file in the root folder:
```
ANTHROPIC_API_KEY=your_api_key_here
```

**3. Install Python dependencies**
```bash
cd backend
python -m pip install fastapi uvicorn chromadb anthropic python-dotenv fastmcp
```

**4. Start the backend**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**5. Install the VS Code extension**

Install `recall-0.0.1.vsix` directly in VS Code:
```
Extensions → ... → Install from VSIX → select recall-0.0.1.vsix
```

**6. Open a project folder in VS Code**
```
File → Open Folder → select your project
```

**7. Index your workspace**

Go to `http://localhost:8000/docs`

Run `POST /index` with your workspace path:
```json
{ "workspace_path": "C:\\your\\project\\path" }
```

### Copilot MCP Integration (optional)

Copy `mcp.json` to your VS Code user settings folder:
```
Windows: C:\Users\USERNAME\AppData\Roaming\Code\User\mcp.json
```

Copy the prompt files to your Copilot prompts folder:
```
Windows: C:\Users\USERNAME\AppData\Roaming\Code\User\prompts\
```

Restart VS Code. You should now see `/Recall-briefing` and `/Export-to-Recall` available in Copilot Chat.

---

## Architecture & Tech Stack

### Overview
```
VS Code Extension (TypeScript)
        ↕ HTTP/SSE localhost:8000
Python FastAPI Backend
        ↕                        ↕
ChromaDB (local SQLite)    Claude API (Anthropic)
        ↕
Recall MCP Server (FastMCP)
        ↕
VS Code MCP Protocol Layer
        ↕
Copilot Chat
```

### Components

**VS Code Extension (TypeScript)**
- Sidebar webview panel with markdown rendering
- Streaming SSE token-by-token responses
- Conversation history (last 20 messages per session)
- Status bar showing backend state (Ready / Backend not running)
- Workspace path detection for automatic git and codebase context

**Python FastAPI Backend**
- `/chat` — streaming chat with RAG context injection
- `/index` — workspace file indexer
- `/memory` — save/retrieve/delete memories
- `/memories` — list stored memories
- `/health` — backend status check
- Command routing — `#remember` `#note` `#status` `#done` `#git` `#memories` `#forget`

**ChromaDB**
- Local vector database stored in `.chromadb` (SQLite)
- Cosine similarity semantic search
- Separate metadata tagging for code chunks vs user memories
- Persistent across VS Code restarts

**RAG Pipeline**
- Files chunked into 500-word overlapping pieces
- Chunks stored as embeddings in ChromaDB
- Every chat query retrieves top 5 relevant chunks
- Chunks injected into Claude API prompt automatically
- Git history injected via subprocess `git log`

**Recall MCP Server (FastMCP)**
- 6 tools: `remember`, `note`, `set_status`, `list_memories`, `search`, `forget`
- Connects to same ChromaDB instance as main backend
- Configured via `mcp.json` at workspace and user level
- Powers `/Recall-briefing` and `/Export-to-Recall` Copilot prompts

### Tech Stack
| Technology | Usage |
|------------|-------|
| TypeScript | VS Code Extension API, Webview UI |
| Python 3.11 | FastAPI, ChromaDB, FastMCP, Anthropic SDK |
| ChromaDB | Local vector database, cosine similarity search |
| Claude Sonnet 4.6 | AI responses via Anthropic API |
| FastMCP | MCP server framework |
| SSE | Server-sent events for streaming responses |
| SQLite | Underlying ChromaDB storage |
| Git subprocess | Local git history retrieval |

---

## Memory Commands

| Command | Description |
|---------|-------------|
| `#remember [text]` | Save a permanent memory |
| `#note [text]` | Save an observation or open question |
| `#status [text]` | Save current working status |
| `#done` | Generate and save a structured session summary |
| `#git` | Show recent git commit history |
| `#memories` | List all saved memories |
| `#forget [keyword]` | Delete memories matching the keyword |

## Copilot Commands

| Command | Description |
|---------|-------------|
| `/Recall-briefing` | Load full project context at the start of a Copilot session |
| `/Export-to-Recall` | Summarize and save the current Copilot session to Recall memory |

---

## Known Limitations & Next Steps

### Known Limitations
- Backend must be started manually before using the extension
- Indexing requires running the `/index` endpoint manually via FastAPI docs page
- SSL certificate issues on some Windows machines require `verify=False` workaround for Anthropic API calls
- Python 3.14 has some package compatibility issues — Python 3.11 recommended
- MCP server requires manual `mcp.json` configuration
- No team shared memory — ChromaDB is currently per-developer only
- Git context injected on every regular chat message regardless of relevance — adds some latency
- No authentication on local backend endpoints — localhost only

### Next Steps
- Auto-start backend when extension activates — no manual uvicorn command
- In-extension indexing command — no need to use FastAPI docs page
- CLI version — same memory layer for terminal workflows, direct alternative to Chronicle
- ADO integration — read boards, PRs, and work items directly into memory
- Team shared ChromaDB instance for shared institutional knowledge
- Keyword detection to only inject git context when query is about recent work
- Proper SSL certificate handling for Windows corporate environments
- Settings UI for API key and configuration inside VS Code

---

## What Was Built During the Hackathon vs What Existed Before

### Built During the Hackathon (48 hours)
- VS Code extension with sidebar chat UI and webview
- Streaming SSE responses token by token
- Markdown rendering in webview
- Python FastAPI backend with all endpoints
- ChromaDB integration and workspace file indexer
- Full RAG pipeline — chunking, embedding, retrieval, context injection
- All memory commands — `#remember` `#note` `#status` `#done` `#git` `#memories` `#forget`
- Recall MCP server (`mcp_server.py`) with 6 tools
- `/Recall-briefing` and `/Export-to-Recall` Copilot prompts
- `mcp.json` workspace and user level MCP configuration
- `copilot-instructions.md` Copilot integration instructions
- Status bar backend health indicator
- VSIX packaging
- README and all submission documentation

### Existed Before the Hackathon
- Nothing — this project was built entirely from scratch during Off the Grid 2026
- General familiarity with VS Code as a development environment
- Existing Blackbaud project codebases used for testing and demo only

---

## Impact Notes

### For Blackbaud Developers
- Eliminates context re-explanation overhead — estimated 15-30 minutes saved per developer per day
- Accelerates onboarding — new developers can query institutional knowledge immediately
- Preserves architectural decisions — context survives contributor turnover
- Works today with no IT approval, no procurement, no infrastructure changes required

### For Blackbaud Customers
- Same RAG architecture extends naturally to nonprofit and education workflows
- Grant writers, fundraisers, and program managers can benefit from AI that remembers their history
- Privacy-first design aligns with data handling requirements for sensitive nonprofit and education client data

### Estimated Value
| Scenario | Calculation | Annual Value |
|----------|-------------|--------------|
| 10 developers × 20 min/day saved | 10 × 20min × 250 days = 833 hrs | ~$83,300 |
| 50 developers × 20 min/day saved | 50 × 20min × 250 days = 4,167 hrs | ~$416,700 |
| 100 developers × 20 min/day saved | 100 × 20min × 250 days = 8,333 hrs | ~$833,000 |

*Based on fully loaded developer cost of $100/hour*

---

## Data & Compliance Notes

### Data Handling
- All project data, codebase chunks, and memories stored locally in `.chromadb` SQLite file on the developer's machine
- No data transmitted to any cloud service except the Anthropic API for chat responses
- Only the specific context chunks relevant to the current question are sent to Anthropic — not the full codebase
- RAG retrieves only the top 5 relevant chunks per query — full codebase is never transmitted
- Git history read locally via subprocess — never transmitted to any external service
- No telemetry, no analytics, no external logging of any kind

### Anthropic API
- Anthropic does not use API inputs for model training by default
- Only chat messages and retrieved context chunks are transmitted per query
- API key stored in local `.env` file — excluded from git via `.gitignore`

### Licenses
| Package | License |
|---------|---------|
| ChromaDB | Apache 2.0 |
| FastAPI | MIT |
| FastMCP | MIT |
| Anthropic SDK | MIT |
| VS Code Extension API | MIT |

---

## AI Usage Disclosure

### Tools Used
- **GitHub Copilot** — used throughout development for code completion, debugging, and implementation suggestions
- **Claude (claude.ai)** — used extensively for architecture design, problem solving, code review, and documentation
- **Claude API (Anthropic)** — powers all Recall chat responses at runtime via `claude-sonnet-4-6`

### How AI Was Applied
- **Architecture decisions** — discussed and refined through Claude.ai conversations across multiple sessions
- **TypeScript extension boilerplate** — generated with `yo code` generator, refined with Copilot
- **Python backend structure** — initial scaffold with Copilot, refined iteratively through testing
- **ChromaDB integration** — implemented with Copilot assistance using ChromaDB documentation
- **RAG pipeline design** — architecture designed through Claude.ai, implemented with Copilot
- **MCP server** — built with Copilot using FastMCP documentation as reference
- **Debugging** — SSL certificate issues, TypeScript type errors, and webview rendering issues resolved with Copilot and Claude
- **Documentation** — README and submission materials drafted with Claude.ai assistance

### Safeguards
- All AI-generated code was reviewed, tested, and understood before use
- No sensitive Blackbaud production data was shared with any AI tool during development
- Only the Recall project codebase itself was used for testing — no production codebases shared with external AI services

---

## Copilot Prompt Log

Representative prompts that materially shaped the code or content:

**Architecture design**
```
I want to build a VS Code extension that gives AI tools persistent memory 
using RAG and ChromaDB. The extension should have a sidebar chat powered 
by Claude API and an MCP server that Copilot can query directly. 
What should the architecture look like?
```

**ChromaDB integration**
```
Write a Python function that indexes all TypeScript, JavaScript, and 
Python files in a workspace into ChromaDB using 500-word overlapping chunks. 
Tag each chunk with filepath, filename, extension, and type metadata. 
Skip node_modules, .git, dist, and __pycache__ folders.
```

**RAG pipeline**
```
Write a FastAPI endpoint that takes a chat message, searches ChromaDB 
for the 5 most relevant chunks using cosine similarity, injects those 
chunks into a Claude API prompt, and returns a streaming SSE response.
```

**MCP server**
```
Build a FastMCP server with 6 tools: remember, note, set_status, 
list_memories, search, and forget. Each tool should read from and write 
to the same ChromaDB instance used by the main FastAPI backend.
```

**Webview HTML**
```
Create a VS Code webview sidebar chat UI with markdown rendering, 
streaming token display, conversation history, a clear button, 
and a status indicator. Use VS Code CSS variables for theming 
so it matches the user's current VS Code theme automatically.
```

**Copilot session prompts**
```
Write a GitHub Copilot chat prompt called /Recall-briefing that calls 
the Recall MCP server tools list_memories and search to retrieve current 
project context and returns a structured briefing with decisions made, 
current status, and open questions.
```

**Session summary command**
```
Write a #done command handler in Python that takes the current 
conversation history, sends it to Claude API with instructions to 
summarize into three sections — decisions made, open questions, 
and current status — and saves the result to ChromaDB as a memory.
```

**Git integration**
```
Write a Python function that runs git log and git status via subprocess, 
formats the output into a readable markdown string, and injects it 
into the Claude API prompt so the AI can answer questions about 
recent work without the developer having to explain it manually.
```

---

*Built during Blackbaud Off the Grid 2026*  
*Arturo Escobedo*
