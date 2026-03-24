import chromadb
import os
from pathlib import Path

# Initialize ChromaDB with local persistence
chroma_client = chromadb.PersistentClient(path="../.chromadb")

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
    # Skip if in ignored folder
    for part in path.parts:
        if part in SKIP_FOLDERS:
            return False
    # Only index supported extensions
    return path.suffix.lower() in INDEXABLE_EXTENSIONS

def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """Split text into overlapping chunks for better retrieval"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - 50):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def index_workspace(workspace_path: str) -> dict:
    """Index all files in a workspace folder"""
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
            # Read file content
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            
            if not content.strip():
                skipped += 1
                continue
            
            # Chunk the content
            chunks = chunk_text(content)
            
            # Store each chunk in ChromaDB
            for i, chunk in enumerate(chunks):
                doc_id = f"{filepath}::chunk_{i}"
                
                collection.upsert(
                    ids=[doc_id],
                    documents=[chunk],
                    metadatas=[{
                        "filepath": str(filepath),
                        "filename": filepath.name,
                        "extension": filepath.suffix,
                        "chunk_index": i
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
    """Search ChromaDB for relevant context"""
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
    """Get stats about what's been indexed"""
    count = collection.count()
    return {
        "total_chunks": count,
        "collection_name": "recall_memory"
    }