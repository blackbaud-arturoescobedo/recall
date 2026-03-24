from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import os
import httpx
import warnings
from dotenv import load_dotenv
from indexer import index_workspace, search_memory, get_collection_stats

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

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    
    # Retrieve relevant context from ChromaDB
    context_chunks = search_memory(request.message, n_results=5)
    
    # Build context string to inject
    context_text = ""
    if context_chunks:
        context_text = "\n\n## Relevant context from your codebase:\n"
        for chunk in context_chunks:
            context_text += f"\n### From {chunk['filename']}:\n{chunk['content']}\n"
    
    # Build messages from conversation history
    messages = []
    for turn in request.conversation_history:
        messages.append({
            "role": turn["role"],
            "content": turn["content"]
        })
    
    # Add current message with context injected
    user_message = request.message
    if context_text:
        user_message = f"{request.message}\n{context_text}"
    
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    # Call Claude API
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system="""You are Recall, a developer assistant with persistent memory 
        of the user's codebase, architecture decisions, and past conversations. 
        You help developers without requiring them to re-explain their project 
        context every session. When relevant context from the codebase is provided,
        use it to give more accurate and specific answers.""",
        messages=messages
    )
    
    return ChatResponse(
        response=response.content[0].text,
        context_used=[c["filepath"] for c in context_chunks]
    )