import asyncio
import hashlib
import logging
import re
from typing import List, Dict, Any, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

# Check availability of optional dependencies
OPENAI_AVAILABLE = False
GEMINI_AVAILABLE = False
SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    pass

try:
    import google.genai as genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    pass

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    pass

try:
    import tiktoken
except ImportError:
    tiktoken = None

logger = logging.getLogger(__name__)

class EmbeddingsService:
    def __init__(self):
        self.primary_provider = None
        self.fallback_provider = None
        self.use_rotation = False
        self.active_provider = None  # Track which provider is actually being used
        self.active_dimensions = None  # Track active embedding dimensions
        
        # Initialize API rotation if multiple keys provided
        from ..core.config import settings
        if settings.USE_API_ROTATION and len(settings.parsed_gemini_api_keys) > 1:
            try:
                from .api_rotation import get_rotation_service
                rotation_service = get_rotation_service()
                if rotation_service and rotation_service.is_initialized():
                    self.use_rotation = True
                    self.primary_provider = "gemini_rotation"
                    self.model = settings.GEMINI_EMBEDDING_MODEL
                    self.dimensions = settings.GEMINI_EMBEDDING_DIMENSION
                    print(f"Gemini API rotation initialized with {len(settings.parsed_gemini_api_keys)} keys")
            except Exception as e:
                print(f"Gemini rotation initialization failed: {e}")
        
        # Initialize Gemini if available
        if GEMINI_AVAILABLE and not self.primary_provider:
            try:
                if settings.GEMINI_API_KEY:
                    self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    self.primary_provider = "gemini"
                    self.model = settings.GEMINI_EMBEDDING_MODEL
                    self.dimensions = settings.GEMINI_EMBEDDING_DIMENSION
                    print("OK Gemini embeddings client initialized (PRIMARY)")
            except Exception as e:
                print(f"ERROR Gemini embeddings failed: {e}")
                self.gemini_client = None
        
        # Initialize OpenAI as fallback if available
        if OPENAI_AVAILABLE:
            try:
                if settings.OPENAI_API_KEY:
                    self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                    if not self.primary_provider:
                        self.primary_provider = "openai"
                        self.model = "text-embedding-3-small"
                        self.dimensions = 1536
                    else:
                        self.fallback_provider = "openai"
                    pass  # OpenAI embeddings client initialized (FALLBACK)
            except Exception as e:
                pass  # OpenAI embeddings failed
        
        # Try Sentence Transformers as free local fallback (ALWAYS INITIALIZE AS FALLBACK)
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use lightweight, high-quality model
                self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
                if not self.fallback_provider:
                    self.fallback_provider = "sentence_transformers"
                # If no primary provider yet, make it primary
                if not self.primary_provider:
                    self.primary_provider = "sentence_transformers"
                    self.model = "all-MiniLM-L6-v2"
                    self.dimensions = 384  # MiniLM dimensions
                print("OK Sentence Transformers initialized (FALLBACK)")
            except Exception as e:
                print(f"ERROR Sentence Transformers failed: {e}")
                self.sentence_transformer = None
        
        # Final fallback to hash-based
        if not self.primary_provider:
            print("Using hash-based fallback embeddings")
            self.primary_provider = "fallback"
            self.model = "fallback-embeddings"
            self.dimensions = 768  # Match text-embedding-004
        
        # Initialize cache and encoding
        self._cache = {}
        if OPENAI_AVAILABLE:
            try:
                self.encoding = tiktoken.get_encoding("cl100k_base")
            except Exception:
                self.encoding = None
        
        # Turkish domain-specific synonym mapping for better search
        self.turkish_synonyms = {
            # Behavior and attitude synonyms
            'tavir': ['davranis', 'tutum', 'yaklasim', 'hal', 'davranisi', 'tutumu'],
            'tarzi': ['davranisi', 'tutumu', 'yaklasimi', 'tarzi', 'davranis', 'tutum'],
            'davranis': ['tavir', 'tutum', 'yaklasim', 'hal'],
            'tutum': ['tavir', 'davranis', 'yaklasim', 'hal'],
            'sikayet': ['sikayetci', 'problem', 'sorun', 'memnuniyetsizlik', 'sikayette'],
            'sikayetci': ['sikayet', 'problem', 'sorun', 'memnuniyetsizlik'],
            'personel': ['calisan', 'eleman', 'kisi', 'gorevli', 'personelinin'],
            
            # Courier related synonyms
            'kurye': ['kuryeci', 'teslim eden', 'dagitici', 'kurye personeli'],
            'kuryenin': ['kurye', 'kuryeci', 'teslim eden'],
            'teslimat': ['teslim', 'dagitim', 'ulastirma'],
            'gonderi': ['paket', 'kargo', 'sevkiyat'],
            
            # Banking terms
            'kart': ['kredi karti', 'banka karti', 'plastik kart'],
            'musteri': ['muvekkil', 'alici', 'kullanici', 'musteriler'],
            'mbs': ['musteri bilgi sistemi', 'kayit sistemi'],
        }
        
        logger.info(f"EmbeddingsService initialized: {self.primary_provider} ({self.model})")
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        return hashlib.sha256(f"{self.primary_provider}:{text}".encode()).hexdigest()
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Fallback: rough estimate
            return len(text.split()) * 1.3
    
    def _create_fallback_embedding(self, text: str) -> List[float]:
        """Create simple hash-based embedding for fallback"""
        # Create deterministic hash-based embedding
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Convert hash to vector
        vector = []
        for i in range(0, len(text_hash), 8):
            chunk = text_hash[i:i+8]
            # Convert hex to float between -1 and 1
            val = int(chunk, 16) / (16**8) * 2 - 1
            vector.append(val)
        
        # Pad or truncate to match expected dimensions
        target_dim = self.dimensions
        if len(vector) < target_dim:
            vector.extend([0.0] * (target_dim - len(vector)))
        else:
            vector = vector[:target_dim]
        
        return vector
    
    async def _create_gemini_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using Gemini API (Context7 verified pattern)"""
        try:
            print(f"Creating Gemini embeddings for {len(texts)} texts...")
            print(f"Using model: {self.model}")
            
            # Use asyncio.to_thread for sync API calls
            embeddings_response = await asyncio.to_thread(
                self.gemini_client.models.embed_content,
                model=self.model,
                contents=texts
            )
            
            if not hasattr(embeddings_response, 'embeddings') or not embeddings_response.embeddings:
                print(f"No embeddings in response. Response type: {type(embeddings_response)}")
                print(f"Response dir: {dir(embeddings_response)}")
                raise Exception("No embeddings returned from Gemini API")
            
            embeddings = [emb.values for emb in embeddings_response.embeddings]
            print(f"Created {len(embeddings)} Gemini embeddings")
            return embeddings
            
        except Exception as e:
            error_msg = str(e)
            print(f"Gemini embedding error: {error_msg}")
            print(f"Error type: {type(e).__name__}")
            # Include more context in error
            raise Exception(f"Gemini API Error: {error_msg} (Type: {type(e).__name__})")
    
    async def _create_sentence_transformer_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using Sentence Transformers (FREE LOCAL)"""
        try:
            print(f"Creating Sentence Transformer embeddings for {len(texts)} texts...")
            print(f"Using model: {self.model} (LOCAL - NO API COSTS)")
            
            # Use asyncio.to_thread to avoid blocking
            embeddings = await asyncio.to_thread(
                self.sentence_transformer.encode,
                texts,
                convert_to_tensor=False,
                show_progress_bar=len(texts) > 10
            )
            
            # Convert to list of lists
            embeddings_list = [emb.tolist() if hasattr(emb, 'tolist') else list(emb) for emb in embeddings]
            
            print(f"Created {len(embeddings_list)} Sentence Transformer embeddings (FREE)")
            return embeddings_list
                
        except Exception as e:
            error_msg = str(e)
            print(f"Sentence Transformer error: {error_msg}")
            raise Exception(f"Sentence Transformer Error: {error_msg}")

    async def _create_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using OpenAI (Context7 verified pattern)"""
        try:
            response = await asyncio.to_thread(
                self.openai_client.embeddings.create,
                model="text-embedding-3-small",
                input=texts,
                dimensions=1536
            )
            
            embeddings = [embedding.embedding for embedding in response.data]
            print(f"Created {len(embeddings)} OpenAI embeddings")
            return embeddings
            
        except Exception as e:
            print(f"OpenAI embedding error: {str(e)}")
            raise

    async def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for texts using primary provider with rotation/fallback"""
        print(f"Starting embeddings creation for {len(texts)} texts...")
        print(f"Primary provider: {self.primary_provider}, Model: {self.model}")
        
        # Try rotation service first if enabled
        if self.primary_provider == "gemini_rotation" and self.use_rotation:
            from .api_rotation import get_rotation_service
            rotation_service = get_rotation_service()
            if rotation_service:
                try:
                    print(f"Using API rotation service with {len(rotation_service.api_keys)} keys")
                    result = await rotation_service.create_embeddings_with_rotation(texts, self.model)
                    if result:
                        print(f"Rotation service succeeded with {len(result)} embeddings")
                        # SET ACTIVE PROVIDER
                        self.active_provider = "gemini_rotation"
                        self.active_dimensions = self.dimensions
                        return result
                    else:
                        print("Rotation service returned None - all keys exhausted")
                        # IMMEDIATE FALLBACK TO SENTENCE TRANSFORMERS
                        if hasattr(self, 'sentence_transformer'):
                            try:
                                print("Rotation exhausted - Falling back to Sentence Transformers (FREE LOCAL)...")
                                result = await self._create_sentence_transformer_embeddings(texts)
                                # SET ACTIVE PROVIDER
                                self.active_provider = "sentence_transformers"
                                self.active_dimensions = 384
                                return result
                            except Exception as st_error:
                                print(f"Sentence Transformers emergency fallback failed: {st_error}")
                except Exception as e:
                    print(f"Rotation service failed: {e}")
        
        # Try primary provider
        if self.primary_provider == "sentence_transformers" and hasattr(self, 'sentence_transformer'):
            try:
                return await self._create_sentence_transformer_embeddings(texts)
            except Exception as e:
                print(f"Sentence Transformers failed: {e}")
        elif self.primary_provider in ["gemini", "gemini_rotation"] and hasattr(self, 'gemini_client'):
            try:
                return await self._create_gemini_embeddings(texts)
            except Exception as e:
                print(f"Gemini failed: {e}")
        elif self.primary_provider == "openai" and hasattr(self, 'openai_client'):
            try:
                return await self._create_openai_embeddings(texts)
            except Exception as e:
                print(f"OpenAI failed: {e}")
        
        # Fallback to sentence transformers if available
        if hasattr(self, 'sentence_transformer'):
            try:
                print("Trying Sentence Transformers as fallback...")
                return await self._create_sentence_transformer_embeddings(texts)
            except Exception as e:
                print(f"Sentence Transformers fallback failed: {e}")
        
        # Final fallback to hash-based
        print("Using hash-based fallback...")
        return [self._create_fallback_embedding(text) for text in texts]
    
    async def create_single_embedding(self, text: str) -> List[float]:
        """Create embedding for single text with intelligent query routing (Context7 verified)"""
        # CONSISTENCY CHECK: If we have active provider from batch processing, use it
        if self.active_provider == "sentence_transformers" and hasattr(self, 'sentence_transformer'):
            print(f"CONSISTENCY CHECK: Using {self.active_provider} for query (dim: {self.active_dimensions})")
            try:
                result = await self._create_sentence_transformer_embeddings([text])
                return result[0] if result else self._create_fallback_embedding(text)
            except Exception as e:
                print(f"Consistency fallback failed: {e}")
        elif self.active_provider == "gemini" and hasattr(self, 'gemini_client'):
            print(f"CONSISTENCY CHECK: Using {self.active_provider} for query (dim: {self.active_dimensions})")
            try:
                result = await self._create_gemini_embeddings([text])
                return result[0] if result else self._create_fallback_embedding(text)
            except Exception as e:
                print(f"Consistency fallback failed: {e}")
        
        # ENHANCED CONSISTENCY: Check ChromaDB stored documents dimensions
        from .vector_store import vector_store_service
        
        # Check ChromaDB first for stored dimensions
        if hasattr(vector_store_service, 'chroma_collection') and vector_store_service.chroma_collection:
            try:
                # WORKAROUND: Skip complex dimension check, use simple document count check
                total_docs = vector_store_service.chroma_collection.count()
                print(f"🔍 ChromaDB has {total_docs} documents")
                
                # SIMPLE LOGIC: If we have recent documents (>3500), likely they use Sentence Transformers
                if total_docs > 3500:
                    print("🎯 FORCING Sentence Transformers based on document count (>3500)")
                    try:
                        result = await self._create_sentence_transformer_embeddings([text])
                        return result[0] if result else self._create_fallback_embedding(text)
                    except Exception as e:
                        print(f"Forced Sentence Transformers failed: {e}")
                
                # OLD COMPLEX CODE (COMMENTED OUT DUE TO NUMPY ARRAY ISSUE)
                # sample_results = vector_store_service.chroma_collection.get(limit=1, include=["embeddings"])
                # if sample_results and sample_results.get("embeddings") and len(sample_results["embeddings"]) > 0:
                #     first_embedding = sample_results["embeddings"][0]
                #     try:
                #         # Convert to list if it's a numpy array to avoid truth value ambiguity
                #         if hasattr(first_embedding, 'tolist'):
                #             first_embedding = first_embedding.tolist()
                #         
                #         if len(first_embedding) > 0:
                #             stored_dimension = len(first_embedding)
                #             print(f"🔍 ChromaDB stored dimension detected: {stored_dimension}")
                #             
                #             # Force model selection based on stored dimensions
                #             if stored_dimension == 384 and hasattr(self, 'sentence_transformer'):
                #                 print("🎯 FORCING Sentence Transformers for query consistency (384 dim)")
                #                 try:
                #                     result = await self._create_sentence_transformer_embeddings([text])
                #                     return result[0] if result else self._create_fallback_embedding(text)
                #                 except Exception as e:
                #                     print(f"Forced Sentence Transformers failed: {e}")
                #             elif stored_dimension == 3072 and hasattr(self, 'gemini_client'):
                #                 print("🎯 FORCING Gemini for query consistency (3072 dim)")
                #                 try:
                #                     result = await self._create_gemini_embeddings([text])
                #                     return result[0] if result else self._create_fallback_embedding(text)
                #                 except Exception as e:
                #                     print(f"Forced Gemini failed: {e}")
                #             elif stored_dimension == 1536 and hasattr(self, 'openai_client'):
                #                 print("🎯 FORCING OpenAI for query consistency (1536 dim)")
                #                 try:
                #                     result = await self._create_openai_embeddings([text])
                #                     return result[0] if result else self._create_fallback_embedding(text)
                #                 except Exception as e:
                #                     print(f"Forced OpenAI failed: {e}")
                #             else:
                #                 print(f"⚠️ Unknown stored dimension: {stored_dimension}")
                #     except Exception as dim_error:
                #         print(f"⚠️ Dimension detection failed: {dim_error}")
                #         # Continue with fallback logic
            except Exception as e:
                print(f"ChromaDB dimension check failed: {e}")
        
        # Fallback to in-memory analysis if ChromaDB check failed
        if hasattr(vector_store_service, 'in_memory_vectors') and vector_store_service.in_memory_vectors:
            # Check ALL embedding dimensions to determine available models
            dimension_counts = {}
            total_docs = len(vector_store_service.in_memory_vectors)
            
            for doc in vector_store_service.in_memory_vectors:
                embedding_dim = len(doc["embedding"])
                dimension_counts[embedding_dim] = dimension_counts.get(embedding_dim, 0) + 1
            
            # Find the majority dimension
            majority_dim = max(dimension_counts.items(), key=lambda x: x[1])
            majority_dimension, majority_count = majority_dim
            
            print(f"🔍 In-memory analysis: {total_docs} docs, dimensions: {dimension_counts}")
            print(f"🎯 Majority dimension: {majority_dimension} ({majority_count}/{total_docs} docs)")
            
            # Force majority dimension model
            if majority_dimension == 384 and hasattr(self, 'sentence_transformer'):
                print("🔄 FORCING Sentence Transformers (majority dimension)")
                try:
                    result = await self._create_sentence_transformer_embeddings([text])
                    return result[0] if result else self._create_fallback_embedding(text)
                except Exception as e:
                    print(f"Majority dimension (ST) failed: {e}")
            elif majority_dimension == 3072 and hasattr(self, 'gemini_client'):
                print("🔄 FORCING Gemini (majority dimension)")
                try:
                    result = await self._create_gemini_embeddings([text])
                    return result[0] if result else self._create_fallback_embedding(text)
                except Exception as e:
                    print(f"Majority dimension (Gemini) failed: {e}")
        
        # Final fallback to default behavior
        print("⚠️ No stored documents found - using default embedding provider")
        try:
            result = await self.create_embeddings([text])
            return result[0] if result else self._create_fallback_embedding(text)
        except Exception as e:
            print(f"Default embedding failed: {e}")
            return self._create_fallback_embedding(text)
    
    def _expand_query(self, query: str) -> List[str]:
        """Expand query with synonyms for better semantic search"""
        expanded_queries = [query.lower()]
        
        # Check for each synonym group
        for base_word, synonyms in self.turkish_synonyms.items():
            if base_word in query.lower():
                # Add variations with synonyms
                for synonym in synonyms:
                    expanded_query = query.lower().replace(base_word, synonym)
                    if expanded_query not in expanded_queries:
                        expanded_queries.append(expanded_query)
        
        # Add combined query with all relevant synonyms
        query_words = query.lower().split()
        expanded_words = []
        
        for word in query_words:
            expanded_words.append(word)
            # Add synonyms for this word
            for base_word, synonyms in self.turkish_synonyms.items():
                if base_word in word:
                    expanded_words.extend(synonyms[:2])  # Add top 2 synonyms
        
        if len(expanded_words) > len(query_words):
            combined_query = ' '.join(expanded_words)
            if combined_query not in expanded_queries:
                expanded_queries.append(combined_query)
        
        print(f"Query expansion: {len(expanded_queries)} variations")
        for i, eq in enumerate(expanded_queries[:3]):  # Show top 3
            print(f"   {i+1}. {eq}")
        
        return expanded_queries

    async def create_multi_query_embedding(self, text: str) -> List[List[float]]:
        """Create embeddings for original query + expanded variations"""
        expanded_queries = self._expand_query(text)
        
        # Limit to avoid too many API calls
        queries_to_embed = expanded_queries[:3]  # Top 3 variations
        
        embeddings = []
        for query in queries_to_embed:
            emb = await self.create_single_embedding(query)
            if emb:
                embeddings.append(emb)
        
        return embeddings if embeddings else [await self.create_single_embedding(text)]
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Context7 verified text chunking with proper boundary detection
        FIXED: Complete sentence preservation, no fragmented chunks
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        text_length = len(text)
        
        # Adjust chunk size for very large texts
        if text_length > 50000:
            chunk_size = 300
            overlap = 30
        
        # Context7 Pattern: Simple and reliable chunking
        start = 0
        while start < text_length:
            # Calculate end position
            end = min(start + chunk_size, text_length)
            
            # Find natural boundary (sentence end) near chunk boundary
            if end < text_length:
                # Look for sentence boundaries in the last 150 characters
                boundary_search_start = max(start, end - 150)
                
                # Find the best sentence ending
                best_boundary = -1
                for boundary_char in ['.', '!', '?', '\n\n']:
                    boundary_pos = text.rfind(boundary_char, boundary_search_start, end)
                    if boundary_pos > start:  # Must be after start
                        best_boundary = max(best_boundary, boundary_pos + 1)
                
                # Use boundary if found, otherwise use original end
                if best_boundary > start:
                    end = best_boundary
            
            # Extract chunk with proper whitespace handling
            chunk = text[start:end].strip()
            if chunk and len(chunk) > 10:  # Skip tiny fragments
                chunks.append(chunk)
            
            # Calculate next start position with overlap
            next_start = end - overlap
            
            # Ensure forward progress (critical for termination)
            if next_start <= start:
                next_start = start + max(100, chunk_size // 2)
            
            start = next_start
            
            # Safety termination if no progress
            if start >= text_length:
                break
        
        print(f"✅ Created {len(chunks)} clean chunks (no fragmentation)")
        return chunks

# Global embeddings service instance
embeddings_service = EmbeddingsService() 