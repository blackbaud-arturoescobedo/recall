import chromadb
import os
import subprocess
from pathlib import Path

# Initialize ChromaDB with local persistence — absolute path relative to this file
_BACKEND_DIR = Path(__file__).parent
chroma_client = chromadb.PersistentClient(path=str(_BACKEND_DIR.parent / ".chromadb"))

# Get or create our collection
collection = chroma_client.get_or_create_collection(
    name="recall_memory",
    metadata={"hnsw:space": "cosine"}
)

# File types we want to index
INDEXABLE_EXTENSIONS = [
    ".ts", ".js", ".py", ".cs", ".java",
    ".md", ".txt", ".json", ".html", ".css",
    ".jsx", ".tsx", ".vue", ".yaml", ".yml"
]

# Folders to always skip
SKIP_FOLDERS = [
    "node_modules", ".git", "__pycache__",
    "dist", "bin", "obj", ".chromadb",
    "out", ".vscode"
]

def should_index_file(filepath: str) -> bool:
    path = Path(filepath)
    for part in path.parts:
        if part in SKIP_FOLDERS:
            return False
    return path.suffix.lower() in INDEXABLE_EXTENSIONS

def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - 50):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def index_workspace(workspace_path: str) -> dict:
    workspace = Path(workspace_path)
    
    if not workspace.exists():
        return {"error": f"Workspace path does not exist: {workspace_path}"}
    
    indexed = 0
    skipped = 0
    errors = 0
    
    for filepath in workspace.rglob("*"):
        if not filepath.is_file():
            continue
            
        if not should_index_file(str(filepath)):
            skipped += 1
            continue
        
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            
            if not content.strip():
                skipped += 1
                continue
            
            chunks = chunk_text(content)
            
            for i, chunk in enumerate(chunks):
                doc_id = f"{filepath}::chunk_{i}"
                
                collection.upsert(
                    ids=[doc_id],
                    documents=[chunk],
                    metadatas=[{
                        "filepath": str(filepath),
                        "filename": filepath.name,
                        "extension": filepath.suffix,
                        "chunk_index": i,
                        "type": "code"
                    }]
                )
            
            indexed += 1
            
        except Exception as e:
            errors += 1
            print(f"Error indexing {filepath}: {e}")
    
    return {
        "indexed": indexed,
        "skipped": skipped,
        "errors": errors,
        "workspace": str(workspace)
    }

def search_memory(query: str, n_results: int = 5) -> list[dict]:
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        contexts = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                contexts.append({
                    "content": doc,
                    "filepath": results["metadatas"][0][i].get("filepath", "unknown"),
                    "filename": results["metadatas"][0][i].get("filename", "unknown"),
                    "distance": results["distances"][0][i] if results.get("distances") else None
                })
        
        return contexts
        
    except Exception as e:
        print(f"Search error: {e}")
        return []

def get_collection_stats() -> dict:
    count = collection.count()
    return {
        "total_chunks": count,
        "collection_name": "recall_memory"
    }

def save_memory(content: str, memory_type: str = "remember", metadata: dict = {}) -> str:
    from datetime import datetime
    
    timestamp = datetime.now().isoformat()
    date = datetime.now().strftime("%Y-%m-%d")
    
    memory_id = f"memory_{timestamp}_{memory_type}"
    
    full_metadata = {
        "type": memory_type,
        "date": date,
        "timestamp": timestamp,
        **metadata
    }
    
    collection.upsert(
        ids=[memory_id],
        documents=[content],
        metadatas=[full_metadata]
    )
    
    return memory_id

def get_memories(memory_type: str = None, limit: int = 20) -> list[dict]:
    try:
        user_types = ["remember", "note", "status"]
        
        if memory_type and memory_type in user_types:
            where = {"type": memory_type}
        else:
            where = {"type": {"$in": user_types}}
        
        results = collection.get(
            where=where,
            limit=limit,
            include=["documents", "metadatas"]
        )
        
        memories = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"]):
                memories.append({
                    "id": results["ids"][i],
                    "content": doc,
                    "date": results["metadatas"][i].get("date", "unknown"),
                    "type": results["metadatas"][i].get("type", "unknown"),
                    "timestamp": results["metadatas"][i].get("timestamp", "")
                })
        
        memories.sort(key=lambda x: x["timestamp"], reverse=True)
        return memories
        
    except Exception as e:
        print(f"Error retrieving memories: {e}")
        return []

def delete_memory(memory_id: str) -> bool:
    try:
        collection.delete(ids=[memory_id])
        return True
    except Exception as e:
        print(f"Error deleting memory: {e}")
        return False

def delete_memories_by_type(memory_type: str) -> bool:
    try:
        collection.delete(where={"type": memory_type})
        return True
    except Exception as e:
        print(f"Error deleting memories: {e}")
        return False

def get_git_log(workspace_path: str, num_commits: int = 20) -> list[dict]:
    try:
        result = subprocess.run(
            [
                "git", "log",
                f"-{num_commits}",
                "--pretty=format:%H|%an|%ad|%s",
                "--date=short",
                "--name-only"
            ],
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return []
        
        commits = []
        current_commit = None
        
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                if current_commit:
                    commits.append(current_commit)
                    current_commit = None
                continue
            
            if "|" in line and len(line.split("|")) == 4:
                if current_commit:
                    commits.append(current_commit)
                parts = line.split("|")
                current_commit = {
                    "hash": parts[0][:7],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3],
                    "files": []
                }
            elif current_commit and line:
                current_commit["files"].append(line)
        
        if current_commit:
            commits.append(current_commit)
        
        return commits
        
    except Exception as e:
        print(f"Git log error: {e}")
        return []

def get_git_status(workspace_path: str) -> dict:
    try:
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        
        status_result = subprocess.run(
            ["git", "status", "--short"],
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        
        diff_result = subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            cwd=workspace_path,
            capture_output=True,
            text=True
        )
        
        return {
            "branch": branch_result.stdout.strip(),
            "uncommitted": status_result.stdout.strip(),
            "diff_summary": diff_result.stdout.strip()
        }
        
    except Exception as e:
        print(f"Git status error: {e}")
        return {}

def format_git_context(workspace_path: str) -> str:
    if not workspace_path:
        return ""
    
    context = "## Recent Git Activity\n\n"
    
    status = get_git_status(workspace_path)
    if status:
        context += f"**Current branch:** {status.get('branch', 'unknown')}\n"
        if status.get('uncommitted'):
            context += f"**Uncommitted changes:**\n{status['uncommitted']}\n"
        context += "\n"
    
    commits = get_git_log(workspace_path, num_commits=10)
    if commits:
        context += "**Recent commits:**\n"
        for commit in commits:
            context += f"\n📝 `{commit['hash']}` — {commit['date']}\n"
            context += f"   {commit['message']}\n"
            if commit['files']:
                files = commit['files'][:5]
                context += f"   Files: {', '.join(files)}"
                if len(commit['files']) > 5:
                    context += f" (+{len(commit['files']) - 5} more)"
                context += "\n"
    
    return context