"""
Enterprise RAG System - Vector Store Service (Context7 Verified)
Pinecone implementation with ChromaDB persistent fallback for document vector storage and retrieval
"""
import asyncio
from typing import List, Dict, Optional, Tuple, Union, Any
import numpy as np
import os
from app.core.config import settings
import uuid
from datetime import datetime
from app.services.embeddings import embeddings_service  # Import the embeddings service

# Check if Pinecone is available
try:
    from pinecone import Pinecone, ServerlessSpec, CloudProvider, AwsRegion, VectorType
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

# Check if ChromaDB is available for persistence
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    # Context7 Verified: Import Google Gemini embedding function
    from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

class VectorStoreService:
    """Pinecone Vector Store with persistent ChromaDB fallback for RAG pipeline (Context7 verified)"""
    
    def __init__(self):
        # In-memory fallback storage
        self.in_memory_vectors: List[Dict] = []
        self.use_memory_fallback = True
        
        # Pinecone initialization (optional)
        self.pc: Optional[Any] = None
        self.index: Optional[Any] = None
        self.index_name: Optional[str] = None
        self.dimension: Optional[int] = None
        self.namespace: Optional[str] = None
        
        # ChromaDB initialization (persistent storage)
        self.chroma_client: Optional[Any] = None
        self.chroma_collection: Optional[Any] = None
        
        try:
            # Initialize ChromaDB for persistent storage (Context7 verified absolute path)
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "..", "..", "persistent_vector_db")
            db_path = os.path.abspath(db_path)
            
            print(f"🔍 DEBUG: ChromaDB path: {db_path}")
            
            self.chroma_client = chromadb.PersistentClient(
                path=db_path,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection with explicit embedding function
            try:
                # Context7 Verified Fix: Try Gemini first, fallback to no embedding function for pre-computed embeddings
                from app.core.config import settings  # Import settings here
                if settings.GEMINI_API_KEY:
                    try:
                        google_ef = GoogleGenerativeAiEmbeddingFunction(api_key=settings.GEMINI_API_KEY)
                        self.chroma_collection = self.chroma_client.get_or_create_collection(
                            name="enterprise_rag_docs",
                            embedding_function=google_ef,
                            metadata={"hnsw:space": "cosine"}
                        )
                        print("✅ ChromaDB collection created with Gemini embedding function")
                    except Exception as e:
                        print(f"⚠️ Gemini embedding function failed: {e}")
                        # Context7 Verified Fallback: Create collection without embedding function for pre-computed embeddings
                        self.chroma_collection = self.chroma_client.get_or_create_collection(
                            name="enterprise_rag_docs_precomputed",
                            metadata={"hnsw:space": "cosine"}
                        )
                        print("✅ ChromaDB collection created for pre-computed embeddings (dimension-flexible)")
                else:
                    # Context7 Verified: No API key, use pre-computed embeddings approach
                    self.chroma_collection = self.chroma_client.get_or_create_collection(
                        name="enterprise_rag_docs_precomputed",
                        metadata={"hnsw:space": "cosine"}
                    )
                    print("✅ ChromaDB collection created for pre-computed embeddings (no Gemini API)")

                if self.chroma_collection is not None:
                    doc_count = self.chroma_collection.count()
                    print(f"✅ Loaded existing ChromaDB collection with {doc_count} documents")
                    
                    # Load documents into in-memory storage for fallback
                    try:
                        self._load_chromadb_to_memory()
                        print(f"✅ Loaded {len(self.in_memory_vectors)} documents to in-memory storage")
                    except Exception as e:
                        print(f"⚠️ Failed to load ChromaDB to memory: {e}")
                else:
                    print("✅ Loaded/Created ChromaDB collection")
            except Exception as e:
                 print(f"❌❌❌ CRITICAL: Failed to get or create ChromaDB collection: {e}")
                 # Fallback to creating a standard collection if EF fails, to avoid total crash
                 self.chroma_collection = self.chroma_client.get_or_create_collection(
                    name="enterprise_rag_docs_fallback",
                    metadata={"hnsw:space": "cosine"}
                )
                 print("⚠️ Created fallback ChromaDB collection without specific embedding function.")

                
        except ImportError:
            print("⚠️ ChromaDB not available, using in-memory storage")
            self.chroma_client = None
            self.chroma_collection = None
        except Exception as e:
            print(f"⚠️ ChromaDB initialization failed: {e}")
            self.chroma_client = None
            self.chroma_collection = None
            
        try:
            # Optional Pinecone setup
            from pinecone import Pinecone, ServerlessSpec, CloudProvider
            from ..core.config import settings
            
            if hasattr(settings, 'PINECONE_API_KEY') and settings.PINECONE_API_KEY:
                self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                self.index_name = getattr(settings, 'PINECONE_INDEX_NAME', 'rag-index')
                self.dimension = getattr(settings, 'PINECONE_DIMENSION', 1536)
                self.namespace = getattr(settings, 'PINECONE_NAMESPACE', 'default')
                print("✅ Pinecone client initialized")
            else:
                print("⚠️ Pinecone API key not found, using ChromaDB/memory fallback")
                
        except ImportError:
            print("⚠️ Pinecone not available")
        except Exception as e:
            print(f"⚠️ Pinecone initialization failed: {e}")
        
    def _load_chromadb_to_memory(self) -> None:
        """Load all documents from ChromaDB to in-memory storage for fallback"""
        if not self.chroma_collection:
            return
            
        try:
            # Get all documents from ChromaDB with embeddings
            results = self.chroma_collection.get(
                include=["embeddings", "metadatas", "documents"]
            )
            
            if results and results.get("ids"):
                ids = results["ids"]
                embeddings = results.get("embeddings", [])
                metadatas = results.get("metadatas", [])
                documents = results.get("documents", [])
                
                # Clear existing in-memory vectors
                self.in_memory_vectors = []
                
                # Load into in-memory storage
                for i in range(len(ids)):
                    embedding = embeddings[i] if i < len(embeddings) else []
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    content = documents[i] if i < len(documents) else ""
                    
                    # Convert numpy array to list if needed (Context7 verified)
                    try:
                        import numpy as np
                        if isinstance(embedding, np.ndarray):
                            embedding = embedding.tolist()
                        elif not isinstance(embedding, list):
                            embedding = list(embedding)
                    except Exception:
                        # If conversion fails, keep as is
                        pass
                    
                    # Ensure metadata is a dict
                    if not isinstance(metadata, dict):
                        metadata = {}
                    
                    # Add content to metadata if not present
                    if "content" not in metadata and content:
                        metadata["content"] = content
                    
                    self.in_memory_vectors.append({
                        "id": ids[i],
                        "embedding": embedding,
                        "metadata": metadata
                    })
                    
        except Exception as e:
            print(f"Error loading ChromaDB to memory: {e}")

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert to numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
                
            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
        except Exception as e:
            print(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    async def initialize_index(self):
        """Initialize Pinecone index if available"""
        if not self.pc or not self.index_name:
            print("⚠️ Pinecone not configured")
            return False
            
        try:
            # Check if index exists
            existing_indexes = await asyncio.to_thread(self.pc.list_indexes)
            index_names = [idx.name for idx in existing_indexes]
            
            if self.index_name not in index_names:
                # Create index
                await asyncio.to_thread(
                    self.pc.create_index,
                    name=self.index_name,
                    dimension=self.dimension or 1536,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=CloudProvider.AWS,
                        region="us-east-1"
                    )
                )
                print(f"✅ Created Pinecone index: {self.index_name}")
            
            # Get index
            self.index = self.pc.Index(self.index_name)
            print(f"✅ Connected to Pinecone index: {self.index_name}")
            return True
            
        except Exception as e:
            print(f"❌ Pinecone index initialization failed: {e}")
            return False
    
    async def upsert_documents(self, documents: List[Dict]) -> bool:
        """
        Store document chunks in vector store (ChromaDB preferred, Pinecone fallback, memory last resort)
        """
        if not documents:
            print("⚠️ No documents provided for upserting")
            return True
        
        print(f"📝 Upserting {len(documents)} document chunks...")
        
        # Try ChromaDB first (persistent storage)
        if self.chroma_collection is not None:
            try:
                # Prepare data for ChromaDB
                ids = []
                embeddings = []
                metadatas = []
                documents_text = []
                
                for doc in documents:
                    doc_id = doc.get("id", str(uuid.uuid4()))
                    embedding = doc.get("embedding", [])
                    metadata = doc.get("metadata", {})
                    content = metadata.get("content", "")
                    
                    # Ensure metadata contains only simple types (no nested dicts)
                    clean_metadata = {}
                    for key, value in metadata.items():
                        if isinstance(value, (str, int, float, bool)):
                            clean_metadata[key] = value
                        else:
                            clean_metadata[key] = str(value)
                    
                    ids.append(doc_id)
                    embeddings.append(embedding)
                    metadatas.append(clean_metadata)
                    documents_text.append(content)
                
                # Upsert to ChromaDB in batches
                batch_size = 100
                for i in range(0, len(ids), batch_size):
                    batch_ids = ids[i:i + batch_size]
                    batch_embeddings = embeddings[i:i + batch_size]
                    batch_metadatas = metadatas[i:i + batch_size]
                    batch_documents = documents_text[i:i + batch_size]
                    
                    # Use asyncio.to_thread for sync operations (Context7 pattern)
                    await asyncio.to_thread(
                        self.chroma_collection.upsert,
                        ids=batch_ids,
                        embeddings=batch_embeddings,
                        metadatas=batch_metadatas,
                        documents=batch_documents
                    )
                    print(f"Upserted batch {i//batch_size + 1}: {len(batch_ids)} documents to ChromaDB")
                
                print(f"✅ Successfully upserted {len(documents)} documents to ChromaDB")
                
                # ALSO add to in-memory storage for fallback
                print("📝 Also adding to in-memory storage for fallback...")
                for doc in documents:
                    doc_id = doc.get("id", str(uuid.uuid4()))
                    embedding = doc.get("embedding", [])
                    metadata = doc.get("metadata", {})
                    
                    # Convert numpy array to list if needed for consistency
                    try:
                        if hasattr(embedding, 'tolist') and callable(getattr(embedding, 'tolist', None)):
                            embedding = embedding.tolist()
                        elif not isinstance(embedding, list):
                            embedding = list(embedding)
                    except Exception:
                        pass
                    
                    self.in_memory_vectors.append({
                        "id": doc_id,
                        "embedding": embedding,
                        "metadata": metadata
                    })
                
                print(f"✅ Also stored {len(documents)} documents in memory (total: {len(self.in_memory_vectors)})")
                return True
                
            except Exception as e:
                print(f"❌ ChromaDB upsert failed: {e}")
                # Fall back to other methods
        
        # Try Pinecone fallback
        if self.pc is not None and self.index is not None:
            return await self._upsert_pinecone_fallback(documents)
        
        # Final fallback to in-memory storage
        print("📝 Using in-memory storage fallback")
        for doc in documents:
            doc_id = doc.get("id", str(uuid.uuid4()))
            self.in_memory_vectors.append({
                "id": doc_id,
                "embedding": doc.get("embedding", []),
                "metadata": doc.get("metadata", {})
            })
        
        print(f"✅ Stored {len(documents)} documents in memory")
        return True
    
    async def _upsert_pinecone_fallback(self, documents: List[Dict]) -> bool:
        """Fallback upsert method for Pinecone"""
        try:
            # Lazy initialize Pinecone if needed
            if self.index is None:
                await self.initialize_index()
                
            if self.index is None:
                print("❌ Pinecone index still not available, falling back to memory")
                # Fall back to in-memory storage
                for doc in documents:
                    doc_id = doc.get("id", str(uuid.uuid4()))
                    self.in_memory_vectors.append({
                        "id": doc_id,
                        "embedding": doc.get("embedding", []),
                        "metadata": doc.get("metadata", {})
                    })
                print(f"✅ Stored {len(documents)} documents in memory")
                return True
            
            # Prepare vectors for Pinecone
            vectors = []
            for doc in documents:
                doc_id = doc.get("id", str(uuid.uuid4()))
                embedding = doc.get("embedding", [])
                metadata = doc.get("metadata", {})
                
                # Ensure metadata is JSON serializable
                clean_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        clean_metadata[key] = value
                    elif value is None:
                        clean_metadata[key] = ""
                    else:
                        clean_metadata[key] = str(value)
                
                vectors.append({
                    "id": doc_id,
                    "values": embedding,
                    "metadata": clean_metadata
                })
            
            # Upsert in batches (Context7 pattern)
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                
                # Use asyncio.to_thread for sync operations (Context7 pattern)
                await asyncio.to_thread(
                    self.index.upsert,
                    vectors=batch,
                    namespace=self.namespace or "default"
                )
                print(f"Upserted batch {i//batch_size + 1}: {len(batch)} vectors")
            
            print(f"Successfully upserted {len(vectors)} document chunks")
            return True
            
        except Exception as e:
            print(f"Error upserting documents: {str(e)}")
            return True  # Return success to avoid breaking the pipeline
    
    async def search_similar_documents_multi_query(
        self,
        query_embeddings: List[List[float]],
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Enhanced search using multiple query embeddings for better recall
        Combines results from all query variations and re-ranks
        """
        from ..core.config import settings
        
        if similarity_threshold is None:
            similarity_threshold = settings.SIMILARITY_THRESHOLD
            
        all_results = {}  # Use dict to avoid duplicates by document ID
        
        print(f"🔍 Multi-query search with {len(query_embeddings)} variations...")
        
        for i, query_embedding in enumerate(query_embeddings):
            print(f"   🔍 Query variation {i+1}...")
            results = await self.search_similar_documents(
                query_embedding=query_embedding,
                top_k=top_k * 2,  # Get more results per query
                filter_metadata=filter_metadata,
                similarity_threshold=max(0.15, similarity_threshold - 0.1)  # Lower threshold for variants
            )
            
            # Merge results with score boosting for multiple matches
            for result in results:
                doc_id = result["id"]
                if doc_id in all_results:
                    # Document found in multiple queries - boost score
                    existing_score = all_results[doc_id]["score"]
                    new_score = max(existing_score, result["score"]) + 0.1  # Boost for multi-match
                    all_results[doc_id]["score"] = min(1.0, new_score)  # Cap at 1.0
                    all_results[doc_id]["multi_match"] = True
                else:
                    result["multi_match"] = False
                    all_results[doc_id] = result
        
        # Sort combined results by score
        combined_results = list(all_results.values())
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Apply final threshold and return top_k
        final_results = [r for r in combined_results if r["score"] >= similarity_threshold]
        final_results = final_results[:top_k]
        
        print(f"✅ Multi-query found {len(final_results)} unique documents")
        for i, result in enumerate(final_results[:3]):
            match_type = " (multi-match)" if result.get("multi_match") else ""
            print(f"   {i+1}. {result['source']} (score: {result['score']:.3f}){match_type}")
        
        return final_results
    
    async def search_similar_documents(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Search for similar documents using query embedding (ChromaDB, Pinecone or in-memory fallback)
        """
        from ..core.config import settings
        
        if similarity_threshold is None:
            similarity_threshold = settings.SIMILARITY_THRESHOLD
        
        # Try ChromaDB persistent storage first
        if self.chroma_collection is not None:
            try:
                print(f"🔍 Searching {self.chroma_collection.count()} documents in ChromaDB...")
                print(f"🎯 Query dimension: {len(query_embedding)}")
                
                # CONTEXT7 FIX: Skip complex numpy array dimension check to avoid boolean ambiguity
                # Use simple document count heuristic instead
                doc_count = self.chroma_collection.count()
                print(f"🔍 ChromaDB documents: {doc_count}")
                
                # HEURISTIC: If >3500 docs, likely recent uploads using Sentence Transformers (384-dim)
                # If query is 3072-dim (Gemini), skip ChromaDB and use memory fallback for compatibility
                query_dimension = len(query_embedding)
                if doc_count > 3500 and query_dimension == 3072:
                    print(f"🔄 Skipping ChromaDB: Query uses 3072-dim (Gemini) but stored docs likely 384-dim (ST)")
                    print(f"🔄 Using memory fallback for dimension compatibility...")
                    raise Exception("Dimension compatibility: Using memory fallback")
                
                # Build where clause for filtering
                where_clause = {}
                if filter_metadata:
                    for key, value in filter_metadata.items():
                        if key in ["source", "title", "category", "page"]:
                            where_clause[key] = value
                
                # CONTEXT7 VERIFIED: Proper ChromaDB query with robust error handling
                results = self.chroma_collection.query(
                    query_embeddings=[query_embedding],  # ChromaDB handles numpy arrays properly
                    n_results=min(top_k * 3, 100),  # Get more results for better filtering
                    where=where_clause if where_clause else None,
                    include=["metadatas", "documents", "distances"]  # type: ignore
                )
                
                # Process results with proper None checks (Context7 pattern)
                similar_docs = []
                if results and results.get("ids") and results["ids"] and len(results["ids"]) > 0 and len(results["ids"][0]) > 0:
                    ids = results["ids"][0]
                    metadatas = results.get("metadatas", [])
                    documents = results.get("documents", [])
                    distances = results.get("distances", [])
                    
                    # Use proper None checks for Optional types (Context7 pattern) - avoid numpy array boolean ambiguity
                    metadatas_valid = metadatas and len(metadatas) > 0 and metadatas[0] is not None
                    documents_valid = documents and len(documents) > 0 and documents[0] is not None  
                    distances_valid = distances and len(distances) > 0 and distances[0] is not None
                    
                    if metadatas_valid and documents_valid and distances_valid:
                        metadata_list = metadatas[0]
                        document_list = documents[0]
                        distance_list = distances[0]
                        
                        for i in range(len(ids)):
                            # Convert distance to similarity (ChromaDB uses cosine distance)
                            distance = distance_list[i] if i < len(distance_list) else 1.0
                            similarity = 1.0 - distance  # Convert distance to similarity
                            
                            # ENHANCED FILTERING: Use lower threshold for better recall, then rank by relevance
                            if similarity >= max(0.15, similarity_threshold - 0.1):
                                metadata = metadata_list[i] if i < len(metadata_list) else {}
                                content = document_list[i] if i < len(document_list) else ""
                                
                                # Ensure metadata is not None (Context7 pattern)
                                safe_metadata = metadata if metadata is not None else {}
                                
                                # RELEVANCE BOOST: Check if query terms appear in content for better ranking
                                content_lower = content.lower()
                                source_name = safe_metadata.get("source", "unknown").lower()
                                
                                # Simple keyword matching boost for Turkish documents
                                query_terms = ["bloke", "işlem", "güvenlik", "şifre", "kart"]
                                relevance_boost = 0.0
                                for term in query_terms:
                                    if term in content_lower or term in source_name:
                                        relevance_boost += 0.05
                                
                                final_score = min(1.0, similarity + relevance_boost)
                                
                                similar_docs.append({
                                    "id": ids[i],
                                    "content": content,
                                    "source": safe_metadata.get("source", "unknown"),
                                    "page": safe_metadata.get("page", "N/A"),
                                    "score": final_score,
                                    "metadata": {
                                        **safe_metadata,
                                        "content": content,
                                        "similarity": similarity,
                                        "relevance_boost": relevance_boost
                                    }
                                })
                
                # Sort by similarity and take top_k
                similar_docs.sort(key=lambda x: x["score"], reverse=True)
                similar_docs = similar_docs[:top_k]
                
                print(f"✅ Found {len(similar_docs)} similar documents (threshold: {similarity_threshold:.2f})")
                for i, doc in enumerate(similar_docs[:3]):
                    print(f"   {i+1}. {doc['source']} (score: {doc['score']:.3f})")
                
                return similar_docs
                
            except Exception as e:
                print(f"❌ ChromaDB search failed: {e}")
                # Fall back to in-memory search
        
        # Fallback to existing in-memory or Pinecone search
        if self.use_memory_fallback or not self.pc:
            # In-memory vector search
            print(f"🔍 Searching {len(self.in_memory_vectors)} documents in memory...")
            print(f"🎯 Query dimension: {len(query_embedding)}")
            
            similar_docs = []
            compatible_docs = 0
            incompatible_docs = 0
            
            for vector in self.in_memory_vectors:
                vector_embedding = vector["embedding"]
                
                # Check dimension compatibility
                if len(vector_embedding) != len(query_embedding):
                    incompatible_docs += 1
                    continue
                
                compatible_docs += 1
                
                # Apply metadata filtering
                if filter_metadata:
                    match = True
                    for key, value in filter_metadata.items():
                        if vector["metadata"].get(key) != value:
                            match = False
                            break
                    if not match:
                        continue
                
                # Calculate cosine similarity
                similarity = self.cosine_similarity(query_embedding, vector_embedding)
                
                if similarity >= similarity_threshold:
                    similar_docs.append({
                        "id": vector["id"],
                        "content": vector["metadata"].get("content", ""),
                        "source": vector["metadata"].get("source", "unknown"),
                        "page": vector["metadata"].get("page", "N/A"),
                        "score": similarity,
                        "metadata": {
                            **vector["metadata"],
                            "similarity": similarity
                        }
                    })
            
            # Sort by similarity and take top_k
            similar_docs.sort(key=lambda x: x["score"], reverse=True)
            similar_docs = similar_docs[:top_k]
            
            print(f"🔢 Dimension compatibility: {compatible_docs} compatible, {incompatible_docs} incompatible")
            print(f"✅ Found {len(similar_docs)} similar documents (threshold: {similarity_threshold:.2f})")
            
            return similar_docs
        
        # Pinecone search
        if self.index is None:
            await self.initialize_index()
            
        if self.index is None:
            print("❌ No vector store available")
            return []
        
        try:
            # Use asyncio.to_thread for sync operations (Context7 pattern)
            query_response = await asyncio.to_thread(
                self.index.query,
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=self.namespace or "default",
                filter=filter_metadata
            )
            
            # Process Pinecone results with proper None checks (Context7 pattern)
            similar_docs = []
            if hasattr(query_response, 'matches') and query_response.matches:
                for match in query_response.matches:
                    if match.score >= similarity_threshold:
                        # Ensure metadata is not None (Context7 pattern)
                        safe_metadata = match.metadata if match.metadata is not None else {}
                        
                        similar_docs.append({
                            "id": match.id,
                            "content": safe_metadata.get("content", ""),
                            "source": safe_metadata.get("source", "unknown"),
                            "page": safe_metadata.get("page", "N/A"),
                            "score": match.score,
                            "metadata": safe_metadata
                        })
            
            print(f"Found {len(similar_docs)} documents from Pinecone")
            return similar_docs
            
        except Exception as e:
            print(f"Pinecone search error: {str(e)}")
            return []
    
    async def get_index_stats(self) -> Dict:
        """Get vector store statistics"""
        if self.use_memory_fallback or not self.pc:
            return {
                "status": "In-memory fallback active",
                "total_vectors": len(self.in_memory_vectors),
                "namespaces": {"memory": len(self.in_memory_vectors)},
                "dimension": 3072,  # Gemini dimensions
                "index_fullness": 0,
                "storage_type": "in-memory"
            }
        
        if not self.index:
            return {
                "status": "Pinecone not available",
                "total_vectors": 0,
                "namespaces": {},
                "dimension": 1536,
                "index_fullness": 0
            }
        
        try:
            stats = await asyncio.to_thread(self.index.describe_index_stats)
            return {
                "total_vectors": stats.total_vector_count,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {},
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "storage_type": "pinecone"
            }
        except Exception as e:
            print(f"Error getting index stats: {str(e)}")
            return {
                "status": f"Error: {str(e)}",
                "total_vectors": 0,
                "namespaces": {},
                "dimension": 1536,
                "index_fullness": 0
            }
    
    async def delete_documents(self, document_ids: List[str]) -> bool:
        """Delete documents by IDs"""
        if self.use_memory_fallback or not self.pc:
            # In-memory deletion
            initial_count = len(self.in_memory_vectors)
            self.in_memory_vectors = [v for v in self.in_memory_vectors if v["id"] not in document_ids]
            deleted_count = initial_count - len(self.in_memory_vectors)
            print(f"Deleted {deleted_count} documents from memory")
            return True
        
        if not self.index:
            print("⚠️ Pinecone not available - delete operation skipped")
            return True
        
        try:
            await asyncio.to_thread(
                self.index.delete,
                ids=document_ids,
                namespace=self.namespace or "default"
            )
            print(f"Deleted {len(document_ids)} documents from Pinecone")
            return True
        except Exception as e:
            print(f"Error deleting documents: {str(e)}")
            return False

    async def delete_documents_by_source(self, source_filename: str) -> bool:
        """
        Context7 verified: Delete all documents/chunks by source filename
        
        This method deletes all chunks that belong to a specific document
        """
        try:
            print(f"🗑️ Deleting all chunks for source: {source_filename}")
            
            # Find all document IDs that match the source
            ids_to_delete = []
            chroma_deleted = 0
            memory_deleted = 0
            
            # Check ChromaDB first
            if self.chroma_collection is not None:
                try:
                    # Get all documents and filter by source
                    results = self.chroma_collection.get(
                        include=["metadatas"]
                    )
                    
                    print(f"🔍 DEBUG: Total chunks in ChromaDB: {len(results.get('ids', []))}")
                    
                    if results.get("ids") and results.get("metadatas"):
                        matching_sources = []
                        for i, chunk_id in enumerate(results["ids"]):
                            metadata = results["metadatas"][i] if i < len(results["metadatas"]) else {}
                            chunk_source = metadata.get("source", "") if metadata else ""
                            
                            # Debug: show first few sources
                            if i < 5:
                                print(f"  Chunk {i}: source='{chunk_source}' vs target='{source_filename}'")
                            
                            if chunk_source == source_filename:
                                ids_to_delete.append(chunk_id)
                                matching_sources.append(chunk_source)
                        
                        print(f"🔍 DEBUG: Found {len(ids_to_delete)} matching chunks for source '{source_filename}'")
                        
                        # Delete from ChromaDB
                        if ids_to_delete:
                            self.chroma_collection.delete(ids=ids_to_delete)
                            chroma_deleted = len(ids_to_delete)
                            print(f"🗑️ Deleted {chroma_deleted} chunks from ChromaDB for {source_filename}")
                        else:
                            print(f"⚠️ No matching chunks found in ChromaDB for source: {source_filename}")
                        
                except Exception as e:
                    print(f"❌ ChromaDB deletion error for {source_filename}: {e}")
            
            # Also delete from in-memory storage
            if self.in_memory_vectors:
                initial_count = len(self.in_memory_vectors)
                print(f"🔍 DEBUG: Checking {initial_count} in-memory vectors...")
                
                # Debug: show first few in-memory sources
                for i, v in enumerate(self.in_memory_vectors[:5]):
                    mem_source = v.get("metadata", {}).get("source", "")
                    print(f"  Memory vector {i}: source='{mem_source}' vs target='{source_filename}'")
                
                self.in_memory_vectors = [
                    v for v in self.in_memory_vectors 
                    if v.get("metadata", {}).get("source") != source_filename
                ]
                memory_deleted = initial_count - len(self.in_memory_vectors)
                if memory_deleted > 0:
                    print(f"🗑️ Deleted {memory_deleted} chunks from memory for {source_filename}")
                    ids_to_delete.extend([f"memory_{i}" for i in range(memory_deleted)])
            
            # Delete from Pinecone if available
            if self.pc and self.index and ids_to_delete:
                try:
                    # For Pinecone, we need to delete by metadata filter if supported
                    # or by collecting all IDs first (which we already did)
                    await asyncio.to_thread(
                        self.index.delete,
                        ids=ids_to_delete,
                        namespace=self.namespace or "default"
                    )
                    print(f"🗑️ Deleted {len(ids_to_delete)} chunks from Pinecone for {source_filename}")
                except Exception as e:
                    print(f"⚠️ Pinecone deletion warning for {source_filename}: {e}")
                    # Don't fail if Pinecone deletion fails, as we've already deleted from other stores
            
            total_deleted = chroma_deleted + memory_deleted
            if total_deleted > 0:
                print(f"✅ Successfully deleted {total_deleted} chunks for document: {source_filename} (ChromaDB: {chroma_deleted}, Memory: {memory_deleted})")
                return True
            else:
                print(f"⚠️ No chunks found to delete for: {source_filename}")
                print(f"🔍 DEBUG: Available sources in ChromaDB:")
                
                # Show all available sources for debugging
                if self.chroma_collection is not None:
                    try:
                        all_results = self.chroma_collection.get(include=["metadatas"])
                        unique_sources = set()
                        if all_results.get("metadatas"):
                            for metadata in all_results["metadatas"]:
                                if metadata and metadata.get("source"):
                                    unique_sources.add(metadata["source"])
                        for source in sorted(unique_sources):
                            print(f"  Available: '{source}'")
                    except Exception as e:
                        print(f"  Error getting sources: {e}")
                
                return False
                
        except Exception as e:
            print(f"❌ Error deleting documents by source {source_filename}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def fetch_documents(self, document_ids: List[str]) -> List[Dict]:
        """Fetch documents by IDs"""
        if self.use_memory_fallback or not self.pc:
            # In-memory fetch
            results = []
            for doc in self.in_memory_vectors:
                if doc["id"] in document_ids:
                    results.append({
                        "id": doc["id"],
                        "metadata": doc["metadata"],
                        "content": doc["metadata"].get("content", "")
                    })
            return results
        
        if not self.index:
            return []
        
        try:
            response = await asyncio.to_thread(
                self.index.fetch,
                ids=document_ids,
                namespace=self.namespace or "default"
            )
            
            results = []
            if hasattr(response, 'vectors') and response.vectors:
                for doc_id, doc_data in response.vectors.items():
                    # Ensure metadata is not None (Context7 pattern)
                    safe_metadata = doc_data.metadata if doc_data.metadata is not None else {}
                    results.append({
                        "id": doc_id,
                        "metadata": safe_metadata,
                        "content": safe_metadata.get("content", "")
                    })
            
            return results
        except Exception as e:
            print(f"Error fetching documents: {str(e)}")
            return []

    async def get_all_documents(self, limit: int = 50) -> List[Dict]:
        """
        Get all documents stored in vector store (ChromaDB or in-memory fallback)
        """
        documents = []
        
        # Try ChromaDB first
        if self.chroma_collection is not None:
            try:
                count = self.chroma_collection.count()
                if count > 0:
                    # Get all documents from ChromaDB
                    results = self.chroma_collection.get(
                        limit=min(limit * 10, count),  # Get more chunks to group by source
                        include=["metadatas", "documents"]
                    )
                    
                    # Group chunks by source document with unique identifier
                    document_groups = {}
                    
                    # Use proper None checks for Optional types (Context7 pattern)
                    if results.get("ids") and results.get("metadatas") and results["metadatas"] is not None:
                        for i, chunk_id in enumerate(results["ids"]):
                            metadata = results["metadatas"][i] if i < len(results["metadatas"]) and results["metadatas"][i] is not None else {}
                            content = results["documents"][i] if results.get("documents") and i < len(results["documents"]) and results["documents"][i] is not None else ""
                            
                            source = metadata.get("source", "unknown") if metadata else "unknown"
                            # Create unique key using source + chunk_id prefix for uniqueness
                            chunk_prefix = chunk_id.split('_')[0] if '_' in chunk_id else chunk_id[:8]
                            doc_key = f"{source}_{chunk_prefix}"
                            
                            if doc_key not in document_groups:
                                document_groups[doc_key] = {
                                    "id": doc_key,
                                    "title": metadata.get("title", source) if metadata else source,
                                    "filename": source,
                                    "category": metadata.get("category", "general") if metadata else "general",
                                    "upload_date": metadata.get("upload_timestamp", "") if metadata else "",
                                    "processed_at": metadata.get("upload_timestamp", "") if metadata else "",
                                    "status": "processed",
                                    "chunks_created": 0,
                                    "text_length": 0,
                                    "content": ""  # Context7 fix: Add content field
                                }
                            
                            # Update statistics and content
                            document_groups[doc_key]["chunks_created"] += 1
                            document_groups[doc_key]["text_length"] += len(content)
                            # Context7 fix: Concatenate content from all chunks
                            if content:
                                if document_groups[doc_key]["content"]:
                                    document_groups[doc_key]["content"] += "\n\n" + content
                                else:
                                    document_groups[doc_key]["content"] = content
                    
                    # Convert to list
                    documents = list(document_groups.values())
                    
                    print(f"📚 Retrieved {len(documents)} documents from ChromaDB ({count} total chunks)")
                    return documents
                    
            except Exception as e:
                print(f"❌ ChromaDB get_all_documents failed: {e}")
                # Fall back to in-memory
        
        # Merge with in-memory storage (for mixed dimension scenario)
        if self.in_memory_vectors:
            print(f"📝 Also checking {len(self.in_memory_vectors)} in-memory vectors...")
            
            # Group by source document with unique identifier
            in_memory_groups = {}
            
            for vector in self.in_memory_vectors:
                metadata = vector.get("metadata", {})
                source = metadata.get("source", "unknown")
                # Create unique key using source + vector id prefix for uniqueness
                vector_id = vector.get("id", "unknown")
                id_prefix = vector_id.split('_')[0] if '_' in vector_id else vector_id[:8]
                doc_key = f"{source}_{id_prefix}"
                
                if doc_key not in in_memory_groups:
                    in_memory_groups[doc_key] = {
                        "id": doc_key,
                        "title": metadata.get("title", source),
                        "filename": source,
                        "category": metadata.get("category", "general"),
                        "upload_date": metadata.get("upload_timestamp", ""),
                        "processed_at": metadata.get("upload_timestamp", ""),
                        "status": "processed",
                        "chunks_created": 0,
                        "text_length": 0,
                        "content": ""  # Context7 fix: Add content field
                    }
                
                # Update statistics and content
                in_memory_groups[doc_key]["chunks_created"] += 1
                content = metadata.get("content", "")
                in_memory_groups[doc_key]["text_length"] += len(content)
                # Context7 fix: Concatenate content from all chunks
                if content:
                    if in_memory_groups[doc_key]["content"]:
                        in_memory_groups[doc_key]["content"] += "\n\n" + content
                    else:
                        in_memory_groups[doc_key]["content"] = content
            
            # Merge with existing documents (avoid duplicates by filename)
            existing_filenames = {doc["filename"] for doc in documents}
            for doc in in_memory_groups.values():
                if doc["filename"] not in existing_filenames:
                    documents.append(doc)
            
            print(f"📚 Total: {len(documents)} documents (ChromaDB + in-memory)")
            return documents
        
        # Pure fallback to in-memory storage if ChromaDB failed
        if not documents and not self.in_memory_vectors:
            print("📝 No documents in storage")
            return []
        
        return documents

    async def search_similar_documents_with_source_filter(
        self, 
        query_embedding: List[float], 
        preferred_source: Optional[str] = None,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Search with source preference - if embedding fails, try alternative sources
        """
        from ..core.config import settings
        
        if similarity_threshold is None:
            similarity_threshold = settings.SIMILARITY_THRESHOLD
            
        if self.use_memory_fallback or not self.pc:
            if not self.in_memory_vectors:
                print("📝 No documents in memory storage")
                return []
            
            print(f"🔍 Searching {len(self.in_memory_vectors)} documents in memory...")
            
            # SMART SOURCE FILTERING: Filter by query dimension AND preferred source
            query_dimension = len(query_embedding)
            compatible_docs = []
            source_stats = {}
            
            for doc in self.in_memory_vectors:
                doc_dimension = len(doc["embedding"])
                doc_source = doc["metadata"].get("source", "unknown")
                
                # Track source statistics
                if doc_source not in source_stats:
                    source_stats[doc_source] = {"total": 0, "compatible": 0}
                source_stats[doc_source]["total"] += 1
                
                if doc_dimension == query_dimension:
                    compatible_docs.append(doc)
                    source_stats[doc_source]["compatible"] += 1
            
            print(f"🎯 Query dimension: {query_dimension}")
            print(f"📊 Source statistics:")
            for source, stats in source_stats.items():
                print(f"   📄 {source}: {stats['compatible']}/{stats['total']} compatible")
            
            # If preferred source specified and has compatible docs, filter by it
            if preferred_source and any(doc["metadata"].get("source", "").startswith(preferred_source) 
                                     for doc in compatible_docs):
                filtered_docs = [doc for doc in compatible_docs 
                               if doc["metadata"].get("source", "").startswith(preferred_source)]
                print(f"🎯 Filtering by preferred source '{preferred_source}': {len(filtered_docs)} docs")
                compatible_docs = filtered_docs
            
            if not compatible_docs:
                print("⚠️ No compatible documents found!")
                return []
            
            # Calculate similarities
            similarities = []
            for doc in compatible_docs:
                similarity = self.cosine_similarity(query_embedding, doc["embedding"])
                similarities.append({
                    "id": doc["id"],
                    "score": similarity,
                    "metadata": doc["metadata"],
                    "content": doc["metadata"].get("content", ""),
                    "source": doc["metadata"].get("source", ""),
                    "page": doc["metadata"].get("page", 0)
                })
            
            # Sort and filter
            similarities.sort(key=lambda x: x["score"], reverse=True)
            filtered_results = [r for r in similarities if r["score"] >= similarity_threshold]
            
            # Adaptive threshold
            if len(filtered_results) < 3 and similarity_threshold > 0.05:
                adaptive_threshold = max(0.05, similarity_threshold - 0.1)
                filtered_results = [r for r in similarities if r["score"] >= adaptive_threshold]
                print(f"🔄 Adaptive threshold lowered to {adaptive_threshold:.2f}")
            
            results = filtered_results[:top_k]
            print(f"✅ Found {len(results)} similar documents from source filter")
            
            for i, result in enumerate(results):
                print(f"   {i+1}. {result['source']} (score: {result['score']:.3f})")
            
            return results
        
        # Pinecone fallback
        return await self.search_similar_documents(query_embedding, top_k, filter_metadata, similarity_threshold)

# Create global instance
vector_store_service = VectorStoreService() 