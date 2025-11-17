"""
Vector Store with Embeddings for Advanced RAG
Uses ChromaDB for local vector storage and sentence-transformers for embeddings
"""

import os
import json
import hashlib
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import numpy as np
import glob

# ChromaDB for vector storage
import chromadb
from chromadb.config import Settings

# Sentence transformers for embeddings
from sentence_transformers import SentenceTransformer

# For chunking
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

class VectorStore:
    """Advanced vector store with semantic search capabilities"""
    
    def __init__(self, 
                 persist_dir: str = "/home/scalp/rag_system/chroma_db",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 collection_name: str = "scalp_knowledge"):
        """
        Initialize vector store with ChromaDB and embeddings
        
        Args:
            persist_dir: Directory to persist ChromaDB
            embedding_model: Model for generating embeddings
            collection_name: Name of the ChromaDB collection
        """
        print(f"🚀 Initializing Vector Store...")
        
        # Initialize embedding model
        print(f"  📊 Loading embedding model: {embedding_model}")
        self.embedder = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB client
        print(f"  💾 Initializing ChromaDB at: {persist_dir}")
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            count = self.collection.count()
            print(f"  ✅ Loaded existing collection with {count} documents")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            print(f"  ✅ Created new collection: {collection_name}")
        
        # Initialize text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
    def add_documents(self, documents: List[Dict], batch_size: int = 100) -> int:
        """
        Add documents to vector store with intelligent chunking
        
        Args:
            documents: List of documents with 'content' and 'metadata'
            batch_size: Batch size for adding to ChromaDB
            
        Returns:
            Number of chunks added
        """
        if not documents:
            return 0
            
        print(f"\n📝 Processing {len(documents)} documents for vector store...")
        
        all_chunks = []
        all_embeddings = []
        all_metadatas = []
        all_ids = []
        
        for doc in documents:
            content = doc.get('content', '')
            metadata = self._sanitize_metadata(doc.get('metadata', {}))
            
            # Skip very short content
            if len(content) < 50:
                continue
                
            # Intelligent chunking
            chunks = self.text_splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                # Generate DETERMINISTIC unique ID using ONLY chunk content
                # This ensures re-ingestion of same content creates same ID
                # DO NOT include index or count as they may vary between runs
                chunk_id = hashlib.sha256(chunk.encode('utf-8')).hexdigest()
                
                # Enhanced metadata
                chunk_metadata = self._sanitize_metadata({
                    **metadata,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'chunk_size': len(chunk),
                    'original_doc_size': len(content)
                })
                
                all_chunks.append(chunk)
                all_metadatas.append(chunk_metadata)
                all_ids.append(chunk_id)
        
        if not all_chunks:
            print("  ⚠️  No valid chunks to add")
            return 0
            
        print(f"  🔄 Generating embeddings for {len(all_chunks)} chunks...")
        
        # Generate embeddings in batches
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i:i+batch_size]
            batch_ids = all_ids[i:i+batch_size]
            batch_metadatas = all_metadatas[i:i+batch_size]
            
            # Generate embeddings
            batch_embeddings = self.embedder.encode(
                batch_chunks,
                convert_to_numpy=True,
                show_progress_bar=False
            ).tolist()
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=batch_embeddings,
                documents=batch_chunks,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
            
            print(f"  ✅ Added batch {i//batch_size + 1}/{(len(all_chunks) + batch_size - 1)//batch_size}")
        
        print(f"  ✅ Added {len(all_chunks)} chunks to vector store")
        return len(all_chunks)

    def _sanitize_metadata(self, metadata: Dict) -> Dict:
        """Ensure metadata values are Chroma-compatible (no None)."""
        clean: Dict = {}
        for key, value in (metadata or {}).items():
            if value is None:
                continue
            if isinstance(value, (bool, int, float, str)):
                clean[key] = value
            else:
                try:
                    clean[key] = str(value)
                except Exception:
                    continue
        return clean

    def add_files(self, file_paths: List[str]) -> int:
        """Add local text/markdown files to the vector store.

        Args:
            file_paths: List of file paths (glob patterns allowed)
        Returns:
            Number of chunks added
        """
        paths: List[str] = []
        for p in file_paths:
            paths.extend(glob.glob(p))

        documents: List[Dict] = []
        for p in paths:
            try:
                path = Path(p)
                if not path.is_file():
                    continue
                if path.suffix.lower() not in {'.md', '.txt', '.log', '.py', '.ts', '.tsx', '.yaml', '.yml'}:
                    continue
                text = path.read_text(encoding='utf-8', errors='ignore')
                if len(text.strip()) < 50:
                    continue
                documents.append({
                    'content': text,
                    'metadata': self._sanitize_metadata({
                        'path': str(path),
                        'source': 'local_file'
                    })
                })
            except Exception:
                continue

        return self.add_documents(documents)
    
    def search(self, 
               query: str, 
               n_results: int = 20,
               filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Semantic search using vector similarity
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of relevant documents with scores
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query, convert_to_numpy=True).tolist()
        
        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata if filter_metadata else None
        )
        
        # Format results
        documents = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                documents.append({
                    'content': doc,
                    'score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                })
        
        return documents
    
    def hybrid_search(self,
                     query: str,
                     keyword_results: List[Dict],
                     n_results: int = 20,
                     vector_weight: float = 0.5) -> List[Dict]:
        """
        Hybrid search combining vector and keyword results
        
        Args:
            query: Search query
            keyword_results: Results from keyword search
            n_results: Number of final results
            vector_weight: Weight for vector search (0-1)
            
        Returns:
            Combined and re-ranked results
        """
        # Get vector search results
        vector_results = self.search(query, n_results=n_results)
        
        # Create a unified score system
        combined_docs = {}
        
        # Add vector results
        for doc in vector_results:
            content_hash = hashlib.md5(doc['content'][:200].encode()).hexdigest()
            combined_docs[content_hash] = {
                'content': doc['content'],
                'vector_score': doc['score'],
                'keyword_score': 0,
                'metadata': doc.get('metadata', {})
            }
        
        # Add keyword results
        for doc in keyword_results:
            content_hash = hashlib.md5(doc['content'][:200].encode()).hexdigest()
            if content_hash in combined_docs:
                combined_docs[content_hash]['keyword_score'] = doc.get('score', 0.5)
            else:
                combined_docs[content_hash] = {
                    'content': doc['content'],
                    'vector_score': 0,
                    'keyword_score': doc.get('score', 0.5),
                    'metadata': doc.get('metadata', {})
                }
        
        # Calculate hybrid scores
        results = []
        for doc_hash, doc in combined_docs.items():
            hybrid_score = (
                vector_weight * doc['vector_score'] + 
                (1 - vector_weight) * doc['keyword_score']
            )
            results.append({
                'content': doc['content'],
                'score': hybrid_score,
                'vector_score': doc['vector_score'],
                'keyword_score': doc['keyword_score'],
                'metadata': doc['metadata']
            })
        
        # Sort by hybrid score
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:n_results]
    
    def update_from_mcp(self, mcp_client) -> int:
        """
        Update vector store with latest data from MCP Memory
        
        Args:
            mcp_client: MCP Memory client instance
            
        Returns:
            Number of documents updated
        """
        print("\n🔄 Updating vector store from MCP Memory...")
        
        # Get all memories (we'll chunk them properly)
        all_memories = mcp_client.search("", limit=1000)  # Empty query gets all
        
        if not all_memories:
            print("  ⚠️  No memories found in MCP")
            return 0
        
        # Add to vector store
        added = self.add_documents(all_memories)
        
        print(f"  ✅ Vector store updated with {added} chunks from {len(all_memories)} memories")
        return added
    
    def clear(self):
        """Clear all documents from the collection"""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"}
        )
        print("  ✅ Vector store cleared")
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        return {
            'total_documents': self.collection.count(),
            'embedding_model': self.embedder.get_sentence_embedding_dimension(),
            'collection_name': self.collection.name
        }
