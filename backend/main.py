from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import anthropic
import os
import httpx
import json
import warnings
from dotenv import load_dotenv
from indexer import (
    index_workspace,
    search_memory,
    get_collection_stats,
    save_memory,
    get_memories,
    delete_memory,
    delete_memories_by_type,
    format_git_context
)

warnings.filterwarnings("ignore", message="Unverified HTTPS request")
load_dotenv("../.env")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

http_client = httpx.Client(verify=False)
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    http_client=http_client
)

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []
    workspace_path: str = ""

class ChatResponse(BaseModel):
    response: str
    context_used: list = []

class IndexRequest(BaseModel):
    workspace_path: str

class MemoryRequest(BaseModel):
    content: str
    memory_type: str = "remember"

class DeleteMemoryRequest(BaseModel):
    memory_id: str = ""
    memory_type: str = ""

@app.get("/health")
def health():
    return {"status": "Recall backend is running"}

@app.get("/stats")
def stats():
    return get_collection_stats()

@app.post("/index")
def index(request: IndexRequest):
    result = index_workspace(request.workspace_path)
    return result

@app.post("/memory")
def add_memory(request: MemoryRequest):
    memory_id = save_memory(
        content=request.content,
        memory_type=request.memory_type
    )
    return {"saved": True, "id": memory_id}

@app.get("/memories")
def list_memories(memory_type: str = None):
    memories = get_memories(memory_type=memory_type)
    return {"memories": memories, "count": len(memories)}

@app.delete("/memory")
def remove_memory(request: DeleteMemoryRequest):
    if request.memory_id:
        success = delete_memory(request.memory_id)
        return {"deleted": success}
    elif request.memory_type:
        success = delete_memories_by_type(request.memory_type)
        return {"deleted": success}
    return {"deleted": False, "error": "provide memory_id or memory_type"}

@app.post("/chat")
async def chat(request: ChatRequest):
    
    message = request.message.strip()

    # Handle multi-line command blocks (pasted from Copilot/Claude export)
    command_prefixes = ("#remember", "#note", "#status", "#forget")
    lines = [l.strip() for l in message.splitlines() if l.strip()]
    if len(lines) > 1 and all(l.lower().startswith(command_prefixes) for l in lines):
        results = []
        for line in lines:
            lower = line.lower()
            if lower.startswith("#remember"):
                content = line[9:].strip()
                if content:
                    save_memory(content=content, memory_type="remember")
                    results.append(f"💾 **Remembered:** {content}")
            elif lower.startswith("#note"):
                content = line[5:].strip()
                if content:
                    save_memory(content=content, memory_type="note")
                    results.append(f"📝 **Note:** {content}")
            elif lower.startswith("#status"):
                content = line[7:].strip()
                if content:
                    save_memory(content=content, memory_type="status")
                    results.append(f"📍 **Status:** {content}")
            elif lower.startswith("#forget"):
                content = line[7:].strip()
                if content:
                    memories = get_memories(limit=100)
                    deleted = [m["content"][:50] for m in memories if content.lower() in m["content"].lower() and delete_memory(m["id"])]
                    results.append(f"🗑️ **Forgot** '{content}' ({len(deleted)} removed)")
        return ChatResponse(
            response=f"✅ Saved {len(results)} memories:\n\n" + "\n".join(results),
            context_used=[]
        )

    # Handle #done command — session wrap-up
    if message.lower().startswith("#done"):
        recent_memories = get_memories(limit=10)
        memory_text = ""
        if recent_memories:
            memory_text = "\n\nSaved context from this project:\n"
            for m in recent_memories:
                emoji = "💾" if m["type"] == "remember" else "📝" if m["type"] == "note" else "📍"
                memory_text += f"{emoji} ({m['date']}): {m['content']}\n"

        history_text = ""
        if request.conversation_history:
            history_text = "\n\nThis session's conversation:\n"
            for turn in request.conversation_history[-10:]:
                role = "Dev" if turn["role"] == "user" else "Recall"
                content = turn["content"][:150] + "..." if len(turn["content"]) > 150 else turn["content"]
                history_text += f"{role}: {content}\n"

        summary_response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            system="You are Recall, a developer assistant. Generate a concise, actionable session wrap-up.",
            messages=[{
                "role": "user",
                "content": f"Generate a session summary with three short sections:\n## What was worked on\n## Key decisions made\n## Pick up next time\n\nKeep each section to 2-3 bullet points.{memory_text}{history_text}"
            }]
        )

        summary = summary_response.content[0].text
        save_memory(content=f"Session wrap-up: {summary[:400]}", memory_type="status")
        return ChatResponse(
            response=f"## 📋 Session Wrap-up\n\n{summary}\n\n---\n*Summary saved to memory.*",
            context_used=[]
        )

    # Handle #remember command
    if message.lower().startswith("#remember"):
        content = message[9:].strip()
        if content:
            memory_id = save_memory(content=content, memory_type="remember")
            return ChatResponse(
                response=f"✅ Got it — I'll remember that.\n\n**Stored:** {content}",
                context_used=[]
            )
        else:
            return ChatResponse(
                response="Please add something after #remember. Example:\n`#remember PR #142 auth refactor done, used JWT`",
                context_used=[]
            )
    
    # Handle #note command
    if message.lower().startswith("#note"):
        content = message[5:].strip()
        if content:
            memory_id = save_memory(content=content, memory_type="note")
            return ChatResponse(
                response=f"📝 Note saved.\n\n**Note:** {content}",
                context_used=[]
            )
        else:
            return ChatResponse(
                response="Please add something after #note. Example:\n`#note decided to drop Redis`",
                context_used=[]
            )
    
    # Handle #status command
    if message.lower().startswith("#status"):
        content = message[7:].strip()
        if content:
            memory_id = save_memory(content=content, memory_type="status")
            return ChatResponse(
                response=f"📍 Status updated.\n\n**Status:** {content}",
                context_used=[]
            )
        else:
            return ChatResponse(
                response="Please add something after #status. Example:\n`#status working on AuthService.test.ts`",
                context_used=[]
            )
    
    # Handle #memories command
    if message.lower().startswith("#memories"):
        memories = get_memories(limit=20)
        if not memories:
            return ChatResponse(
                response="No memories stored yet. Use `#remember`, `#note`, or `#status` to save something.",
                context_used=[]
            )
        
        response_text = "## 🧠 Recall's Memory\n\n"
        for m in memories:
            emoji = "💾" if m["type"] == "remember" else "📝" if m["type"] == "note" else "📍"
            response_text += f"{emoji} **{m['date']}** ({m['type']})\n{m['content']}\n\n"
        
        return ChatResponse(response=response_text, context_used=[])
    
    # Handle #forget command
    if message.lower().startswith("#forget"):
        content = message[7:].strip()
        if content:
            memories = get_memories(limit=100)
            deleted = []
            for m in memories:
                if content.lower() in m["content"].lower():
                    delete_memory(m["id"])
                    deleted.append(m["content"][:50])
            
            if deleted:
                return ChatResponse(
                    response=f"🗑️ Deleted {len(deleted)} memory/memories matching '{content}':\n" +
                            "\n".join([f"- {d}..." for d in deleted]),
                    context_used=[]
                )
            else:
                return ChatResponse(
                    response=f"No memories found matching '{content}'",
                    context_used=[]
                )
        else:
            return ChatResponse(
                response="Please specify what to forget. Example:\n`#forget auth refactor`",
                context_used=[]
            )
    
    # Handle #git command
    if message.lower().startswith("#git"):
        if request.workspace_path:
            git_context = format_git_context(request.workspace_path)
            if git_context:
                return ChatResponse(
                    response=f"## 🔀 Git Activity\n\n{git_context}",
                    context_used=[]
                )
            else:
                return ChatResponse(
                    response="No git history found. Make sure this is a git repository.",
                    context_used=[]
                )
        else:
            return ChatResponse(
                response="No workspace path detected. Open a folder in VS Code first.",
                context_used=[]
            )
    
    # Regular chat — retrieve relevant context from ChromaDB
    context_chunks = search_memory(request.message, n_results=5)
    
    # Build context string to inject
    context_text = ""
    
    # Add git context if workspace provided
    git_context = ""
    if request.workspace_path:
        git_context = format_git_context(request.workspace_path)
    
    if context_chunks:
        context_text = "\n\n## Relevant context from your codebase and memory:\n"
        for chunk in context_chunks:
            # Truncate each chunk to 600 chars to keep total context under control
            snippet = chunk['content'][:600] + ("..." if len(chunk['content']) > 600 else "")
            context_text += f"\n### From {chunk['filename']}:\n{snippet}\n"
    
    # Build messages from conversation history — cap at last 8 turns to stay under 30k TPM
    messages = []
    for turn in request.conversation_history[-8:]:
        messages.append({
            "role": turn["role"],
            "content": turn["content"]
        })
    
    # Add current message with context injected
    user_message = request.message
    if context_text:
        user_message = f"{request.message}\n{context_text}"
    if git_context:
        user_message = f"{user_message}\n\n{git_context}"
    
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    context_filepaths = [c["filepath"] for c in context_chunks]

    def stream_response():
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system="""You are Recall, a developer assistant with persistent memory 
            of the user's codebase, architecture decisions, and past conversations. 
            You help developers without requiring them to re-explain their project 
            context every session. When relevant context from the codebase or git 
            history is provided, use it to give accurate and specific answers.
            When asked about recent work or file changes, reference the git history
            provided rather than guessing.""",
            messages=messages
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps({'token': text})}\n\n"
        yield f"data: {json.dumps({'done': True, 'context_used': context_filepaths})}\n\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")