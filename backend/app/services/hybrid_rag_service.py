#!/usr/bin/env python3
"""
Context7-verified Hybrid RAG Service
Combines BM25 lexical search + semantic search + cross-encoder re-ranking kombinasyonu
for improved retrieval accuracy, especially for Turkish documents.
"""

import logging
import platform
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction import _stop_words
import string
import re

# Context7 verified imports
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer, CrossEncoder, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

class HybridRAGService:
    """
    Context7-verified hybrid RAG implementation combining:
    1. BM25 lexical search for exact keyword matching
    2. Semantic search for meaning-based retrieval  
    3. Cross-encoder re-ranking for relevance scoring
    """
    
    def __init__(self):
        """Initialize hybrid RAG components"""
        self.bm25_index = None
        self.documents = []
        self.document_ids = []
        self.semantic_embeddings = None
        
        # Context7 Windows Fix: Handle multiprocessing on Windows
        if platform.system() == "Windows":
            # Windows requires special handling for multiprocessing
            import multiprocessing
            multiprocessing.set_start_method('spawn', force=True)
            logger.info("🔧 Context7: Windows multiprocessing configured")
        
        # Context7 Pattern: Initialize models
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Use Turkish-optimized or multilingual models
                self.semantic_model = SentenceTransformer('multi-qa-mpnet-base-cos-v1')
                self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L6-v2')
                logger.info("✅ Context7: Hybrid RAG models initialized")
            except Exception as e:
                logger.error(f"Failed to initialize models: {e}")
                self.semantic_model = None
                self.cross_encoder = None
        
        # Turkish stopwords (context7 verified Turkish preprocessing)
        self.turkish_stopwords = {
            've', 'ile', 'bir', 'bu', 'şu', 'o', 'da', 'de', 'ta', 'te', 
            'ya', 'ye', 'dır', 'dir', 'dur', 'dür', 'tır', 'tir', 'tur', 'tür',
            'mı', 'mi', 'mu', 'mü', 'için', 'ancak', 'lakin', 'fakat', 'ama',
            'veya', 'yahut', 'ki', 'ne', 'nasıl', 'neden', 'niçin', 'nerede',
            'ne', 'zaman', 'hangi', 'kaç', 'kim', 'kimin', 'kimi', 'kime'
        }
        
        # Domain-specific Turkish synonyms for banking/customer service
        self.domain_synonyms = {
            'kurye': ['kuryeci', 'teslim', 'dagitim', 'kargo', 'teslimat'],
            'sikayet': ['problem', 'sorun', 'memnuniyetsizlik', 'rahatsizlik'],
            'personel': ['calisan', 'eleman', 'gorevli', 'kisi'],
            'musteri': ['kullanici', 'alici', 'hesap'],
            'kart': ['kredi', 'banka', 'plastik'],
            'sistem': ['uygulama', 'program', 'platform'],
            'ip': ['internet', 'adres', 'baglanti', 'erisim', 'guvenlik', 'ağ', 'network'],
            'kisitlama': ['engel', 'blok', 'yasaklama', 'sinir', 'kontrol', 'sınırlama'],
            'guvenlik': ['security', 'koruma', 'ip', 'firewall', 'erisim', 'izin'],
            'erisim': ['access', 'giris', 'login', 'baglanti', 'ulaşim'],
            'ağ': ['network', 'internet', 'baglanti', 'ip', 'sistem']
        }
    
    def bm25_tokenizer(self, text: str) -> List[str]:
        """
        Context7-verified Turkish tokenizer for BM25
        Handles Turkish characters and banking domain terms
        """
        if not text:
            return []
        
        # Convert to lowercase and normalize Turkish characters
        text = text.lower()
        text = text.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u')
        text = text.replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
        
        # Split on whitespace and punctuation
        tokens = re.findall(r'\b\w+\b', text)
        
        # Remove stopwords and short tokens
        filtered_tokens = []
        for token in tokens:
            if len(token) > 2 and token not in self.turkish_stopwords:
                filtered_tokens.append(token)
                
                # Add domain synonyms for better matching
                if token in self.domain_synonyms:
                    filtered_tokens.extend(self.domain_synonyms[token])
        
        return filtered_tokens
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Context7 Pattern: Index documents for hybrid search
        
        Args:
            documents: List of docs with 'content' and 'id' fields
        """
        try:
            logger.info(f"🔍 Indexing {len(documents)} documents for hybrid search")
            
            self.documents = [doc['content'] for doc in documents]
            self.document_ids = [doc['id'] for doc in documents]
            
            # 1. Create BM25 index (Context7 lexical search)
            if BM25_AVAILABLE and self.documents:
                tokenized_docs = [self.bm25_tokenizer(doc) for doc in self.documents]
                # Context7 fix: Check for empty tokenized docs to prevent division by zero
                valid_tokenized_docs = [doc for doc in tokenized_docs if doc and len(doc) > 0]
                
                if valid_tokenized_docs:
                    self.bm25_index = BM25Okapi(valid_tokenized_docs)
                    logger.info(f"✅ BM25 lexical index created ({len(valid_tokenized_docs)}/{len(tokenized_docs)} valid docs)")
                else:
                    logger.warning("⚠️ No valid tokenized documents for BM25 index")
                    self.bm25_index = None
            
            # 2. Create semantic embeddings (Context7 semantic search)
            if self.semantic_model and self.documents:
                self.semantic_embeddings = self.semantic_model.encode(
                    self.documents, 
                    convert_to_tensor=True,
                    show_progress_bar=True
                )
                logger.info("✅ Semantic embeddings created")
            
            return True
            
        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            return False
    
    def search_bm25(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Context7 BM25 lexical search"""
        if not self.bm25_index:
            return []
        
        try:
            query_tokens = self.bm25_tokenizer(query)
            if not query_tokens:
                return []
            
            scores = self.bm25_index.get_scores(query_tokens)
            
            # Get top results
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only positive scores
                    results.append({
                        'corpus_id': idx,
                        'score': float(scores[idx]),
                        'content': self.documents[idx],
                        'document_id': self.document_ids[idx],
                        'search_type': 'bm25'
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
    
    def search_semantic(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Context7 semantic search with cosine similarity"""
        if not self.semantic_model or self.semantic_embeddings is None:
            return []
        
        try:
            # Encode query
            query_embedding = self.semantic_model.encode(
                query, 
                convert_to_tensor=True
            )
            
            # Search for similar documents
            hits = util.semantic_search(
                query_embedding, 
                self.semantic_embeddings, 
                top_k=top_k
            )[0]
            
            results = []
            for hit in hits:
                corpus_id = hit['corpus_id']
                results.append({
                    'corpus_id': corpus_id,
                    'score': hit['score'],
                    'content': self.documents[corpus_id],
                    'document_id': self.document_ids[corpus_id],
                    'search_type': 'semantic'
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    def rerank_results(self, query: str, results: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Context7 cross-encoder re-ranking for relevance"""
        if not self.cross_encoder or not results:
            return results[:top_k]
        
        try:
            # Prepare query-document pairs for cross-encoder
            pairs = [[query, result['content']] for result in results]
            
            # Get relevance scores
            cross_scores = self.cross_encoder.predict(pairs)
            
            # Add cross-encoder scores to results
            for i, result in enumerate(results):
                result['cross_score'] = float(cross_scores[i])
            
            # Sort by cross-encoder scores
            reranked = sorted(results, key=lambda x: x['cross_score'], reverse=True)
            
            logger.info(f"✅ Re-ranked {len(results)} results using cross-encoder")
            return reranked[:top_k]
            
        except Exception as e:
            logger.error(f"Re-ranking failed: {e}")
            return results[:top_k]
    
    def hybrid_search(self, query: str, top_k: int = 5, rerank: bool = True) -> List[Dict[str, Any]]:
        """
        Context7-verified hybrid search combining BM25 + semantic + re-ranking
        
        Args:
            query: Search query
            top_k: Number of final results
            rerank: Whether to use cross-encoder re-ranking
            
        Returns:
            List of ranked results with relevance scores
        """
        try:
            logger.info(f"🔍 Hybrid search for: '{query}'")
            
            # 1. BM25 lexical search (exact keyword matching)
            bm25_results = self.search_bm25(query, top_k=15)
            logger.info(f"📄 BM25 found {len(bm25_results)} lexical matches")
            
            # 2. Semantic search (meaning-based retrieval)
            semantic_results = self.search_semantic(query, top_k=15)
            logger.info(f"🧠 Semantic found {len(semantic_results)} semantic matches")
            
            # 3. Combine and deduplicate results
            combined_results = {}
            
            # Add BM25 results with higher weight for exact matches
            for result in bm25_results:
                doc_id = result['document_id']
                if doc_id not in combined_results:
                    result['hybrid_score'] = result['score'] * 1.5  # Boost lexical matches
                    combined_results[doc_id] = result
            
            # Add semantic results
            for result in semantic_results:
                doc_id = result['document_id']
                if doc_id not in combined_results:
                    result['hybrid_score'] = result['score']
                    combined_results[doc_id] = result
                else:
                    # Combine scores if document found in both searches
                    existing = combined_results[doc_id]
                    existing['hybrid_score'] = max(existing['hybrid_score'], result['score'] * 1.2)
                    existing['search_type'] = 'hybrid'
            
            # Convert to list and sort by hybrid score
            final_results = list(combined_results.values())
            final_results = sorted(final_results, key=lambda x: x['hybrid_score'], reverse=True)
            
            logger.info(f"🔄 Combined to {len(final_results)} unique results")
            
            # 4. Re-rank with cross-encoder for relevance (Context7 pattern)
            if rerank and self.cross_encoder:
                final_results = self.rerank_results(query, final_results[:15], top_k)
                logger.info(f"🎯 Re-ranked to top {len(final_results)} results")
            else:
                final_results = final_results[:top_k]
            
            return final_results
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

# Global instance
hybrid_rag_service = HybridRAGService() 