from typing import Dict, Any, Optional, List
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
from pathlib import Path
import json
from datetime import datetime
from ..base_agent import BaseAgent

class VectorStoreAgent(BaseAgent):
    """Agent responsible for managing vector store operations and document retrieval."""
    
    def __init__(self, name: str = "vector_store", config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config)
        self.encoder = None
        self.index = None
        self.document_store = {}
        self.store_path = Path("vector_store")
        self.store_path.mkdir(exist_ok=True)
    
    async def initialize(self) -> bool:
        """Initialize the vector store and document encoder."""
        try:
            # Initialize the sentence transformer model
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize FAISS index
            embedding_size = 384  # Size of embeddings from all-MiniLM-L6-v2
            self.index = faiss.IndexFlatL2(embedding_size)
            
            # Load existing index and documents if available
            await self._load_store()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization error: {str(e)}")
            return False
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process vector store operations."""
        try:
            operation = input_data.get("operation")
            
            if operation == "index":
                return await self._index_documents(input_data)
            elif operation == "search":
                return await self._search_documents(input_data)
            elif operation == "update":
                return await self._update_documents(input_data)
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            self.logger.error(f"Processing error: {str(e)}")
            return {"error": str(e)}
    
    async def _index_documents(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Index new documents in the vector store."""
        try:
            documents = input_data.get("documents", [])
            if not documents:
                raise ValueError("No documents provided for indexing")
            
            # Process each document
            for doc in documents:
                # Generate embedding
                text = doc.get("text", "")
                embedding = self.encoder.encode([text])[0]
                
                # Add to FAISS index
                self.index.add(np.array([embedding]))
                
                # Store document metadata
                doc_id = len(self.document_store)
                self.document_store[doc_id] = {
                    "text": text,
                    "metadata": doc.get("metadata", {}),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Save updated store
            await self._save_store()
            
            return {
                "indexed_count": len(documents),
                "total_documents": len(self.document_store)
            }
            
        except Exception as e:
            self.logger.error(f"Indexing error: {str(e)}")
            return {"error": str(e)}
    
    async def _search_documents(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search for relevant documents."""
        try:
            query = input_data.get("query")
            k = input_data.get("k", 5)
            
            if not query:
                raise ValueError("No query provided")
            
            # Generate query embedding
            query_embedding = self.encoder.encode([query])[0]
            
            # Search in FAISS index
            distances, indices = self.index.search(
                np.array([query_embedding]), k
            )
            
            # Collect results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.document_store):
                    doc = self.document_store[int(idx)]
                    results.append({
                        "text": doc["text"],
                        "metadata": doc["metadata"],
                        "score": float(1 / (1 + distances[0][i])),
                        "timestamp": doc["timestamp"]
                    })
            
            return {
                "results": results,
                "query": query,
                "total_results": len(results)
            }
            
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return {"error": str(e)}
    
    async def _update_documents(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing documents in the store."""
        try:
            updates = input_data.get("updates", [])
            if not updates:
                raise ValueError("No updates provided")
            
            updated_count = 0
            for update in updates:
                doc_id = update.get("doc_id")
                if doc_id in self.document_store:
                    # Update document metadata
                    self.document_store[doc_id]["metadata"].update(
                        update.get("metadata", {})
                    )
                    updated_count += 1
            
            # Save updated store
            await self._save_store()
            
            return {
                "updated_count": updated_count,
                "total_documents": len(self.document_store)
            }
            
        except Exception as e:
            self.logger.error(f"Update error: {str(e)}")
            return {"error": str(e)}
    
    async def _save_store(self) -> None:
        """Save the current state of the vector store."""
        try:
            # Save FAISS index
            faiss.write_index(
                self.index,
                str(self.store_path / "faiss_index.bin")
            )
            
            # Save document store
            with open(self.store_path / "documents.json", "w") as f:
                json.dump(self.document_store, f)
                
        except Exception as e:
            self.logger.error(f"Save error: {str(e)}")
            raise
    
    async def _load_store(self) -> None:
        """Load the saved state of the vector store."""
        try:
            index_path = self.store_path / "faiss_index.bin"
            docs_path = self.store_path / "documents.json"
            
            if index_path.exists() and docs_path.exists():
                # Load FAISS index
                self.index = faiss.read_index(str(index_path))
                
                # Load document store
                with open(docs_path, "r") as f:
                    self.document_store = json.load(f)
                    
        except Exception as e:
            self.logger.error(f"Load error: {str(e)}")
            # Continue with empty store if load fails
            pass
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            await self._save_store()
        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for processing."""
        if "operation" not in input_data:
            return False
            
        if input_data["operation"] == "index":
            return "documents" in input_data and isinstance(input_data["documents"], list)
        elif input_data["operation"] == "search":
            return "query" in input_data
        elif input_data["operation"] == "update":
            return "updates" in input_data and isinstance(input_data["updates"], list)
            
        return False 