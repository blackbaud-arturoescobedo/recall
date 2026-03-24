from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
import os
from dotenv import load_dotenv
import httpx
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

load_dotenv("../.env")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
http_client = httpx.Client(verify=False)
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    http_client=http_client
)

class ChatRequest(BaseModel):
    message: str
    conversation_history: list = []

class ChatResponse(BaseModel):
    response: str

@app.get("/health")
def health():
    return {"status": "Recall backend is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    
    # Build messages from conversation history
    messages = []
    for turn in request.conversation_history:
        messages.append({
            "role": turn["role"],
            "content": turn["content"]
        })
    
    # Add current message
    messages.append({
        "role": "user",
        "content": request.message
    })
    
    # Call Claude API
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system="""You are Recall, a developer assistant with persistent memory 
        of the user's codebase, architecture decisions, and past conversations. 
        You help developers without requiring them to re-explain their project 
        context every session.""",
        messages=messages
    )
    
    return ChatResponse(response=response.content[0].text)