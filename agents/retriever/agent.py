from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
import json
import logging
from datetime import datetime
import pickle

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Vector Store Retrieval Agent")

# Initialize sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

class Document(BaseModel):
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    top_k: int = 5

class IndexRequest(BaseModel):
    documents: List[Document]

class RetrievalResponse(BaseModel):
    documents: List[Document]
    scores: List[float]
    metadata: Dict[str, Any]

class VectorStore:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents = []
        self.load_index()
    
    def add_documents(self, documents: List[Document]):
        """Add documents to the vector store."""
        embeddings = []
        for doc in documents:
            if not doc.embedding:
                doc.embedding = model.encode(doc.text).tolist()
            embeddings.append(doc.embedding)
            self.documents.append(doc)
        
        if embeddings:
            self.index.add(np.array(embeddings, dtype=np.float32))
            self.save_index()
    
    def search(self, query: str, top_k: int = 5) -> tuple[List[Document], List[float]]:
        """Search for similar documents."""
        query_embedding = model.encode(query)
        distances, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32),
            top_k
        )
        
        results = []
        scores = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx != -1:  # Valid index
                results.append(self.documents[idx])
                scores.append(float(1 / (1 + distance)))  # Convert distance to similarity score
        
        return results, scores
    
    def save_index(self):
        """Save the index and documents to disk."""
        try:
            os.makedirs('data', exist_ok=True)
            faiss.write_index(self.index, 'data/faiss.index')
            with open('data/documents.pkl', 'wb') as f:
                pickle.dump(self.documents, f)
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
    
    def load_index(self):
        """Load the index and documents from disk."""
        try:
            if os.path.exists('data/faiss.index'):
                self.index = faiss.read_index('data/faiss.index')
            if os.path.exists('data/documents.pkl'):
                with open('data/documents.pkl', 'rb') as f:
                    self.documents = pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")

# Initialize vector store
vector_store = VectorStore()

@app.post("/index")
async def index_documents(request: IndexRequest):
    """Index new documents in the vector store."""
    try:
        vector_store.add_documents(request.documents)
        return {
            "status": "success",
            "message": f"Indexed {len(request.documents)} documents",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=RetrievalResponse)
async def query_documents(request: QueryRequest):
    """Query the vector store for similar documents."""
    try:
        documents, scores = vector_store.search(request.query, request.top_k)
        
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "query": request.query,
            "num_results": len(documents),
            "index_size": len(vector_store.documents)
        }
        
        return RetrievalResponse(
            documents=documents,
            scores=scores,
            metadata=metadata
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "index_size": len(vector_store.documents),
        "dimension": vector_store.dimension
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("RETRIEVER_AGENT_PORT", 8003))) 