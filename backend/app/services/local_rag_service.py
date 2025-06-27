"""
Local RAG Service - Completely Free & Local
Uses Sentence Transformers + ChromaDB + HuggingFace Models
Context7 Verified Implementation - 2024
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPDFLoader,
    UnstructuredMarkdownLoader,
    TextLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from sentence_transformers import SentenceTransformer
import torch

logger = logging.getLogger(__name__)

class LocalRAGService:
    """
    Local RAG Service using completely free components:
    - Sentence Transformers for embeddings (offline)
    - ChromaDB for vector storage (local)
    - HuggingFace models for LLM (local/free)
    """
    
    def __init__(self, persist_dir: str = "local_vector_db"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(exist_ok=True)
        
        # Initialize ChromaDB with persistent storage
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        
        # Best free embedding model for multilingual support (Context7 verified)
        self.embedding_model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embedding_model_name,
            model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # Initialize vector store
        self.vector_store = None
        self.collection_name = "local_rag_collection"
        self._init_vector_store()
        
        # Document loaders mapping
        self.loaders = {
            '.pptx': UnstructuredPowerPointLoader,
            '.ppt': UnstructuredPowerPointLoader,
            '.docx': UnstructuredWordDocumentLoader,
            '.doc': UnstructuredWordDocumentLoader,
            '.pdf': UnstructuredPDFLoader,
            '.md': UnstructuredMarkdownLoader,
            '.txt': TextLoader
        }
        
        # Text splitter (Context7 optimized)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        logger.info(f"✅ Local RAG Service initialized with {self.embedding_model_name}")
        logger.info(f"📁 Vector DB: {self.persist_dir}")
        logger.info(f"🔧 Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    
    def _init_vector_store(self):
        """Initialize ChromaDB vector store"""
        try:
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                client=self.chroma_client,
                persist_directory=str(self.persist_dir)
            )
            logger.info(f"✅ ChromaDB vector store initialized: {self.collection_name}")
        except Exception as e:
            logger.error(f"❌ Vector store initialization failed: {e}")
            raise
    
    async def load_documents_from_directory(self, directory_path: str) -> List[Document]:
        """
        Load all supported documents from directory
        Supports: PPT, PPTX, DOC, DOCX, PDF, MD, TXT
        """
        documents = []
        directory = Path(directory_path)
        
        if not directory.exists():
            logger.error(f"❌ Directory not found: {directory_path}")
            return documents
        
        supported_files = []
        for ext in self.loaders.keys():
            supported_files.extend(directory.glob(f"**/*{ext}"))
            supported_files.extend(directory.glob(f"**/*{ext.upper()}"))
        
        logger.info(f"📂 Found {len(supported_files)} supported files")
        
        for file_path in supported_files:
            try:
                ext = file_path.suffix.lower()
                if ext in self.loaders:
                    loader_class = self.loaders[ext]
                    loader = loader_class(str(file_path))
                    
                    # Load document
                    docs = await asyncio.to_thread(loader.load)
                    
                    # Add metadata
                    for doc in docs:
                        doc.metadata.update({
                            'source': str(file_path),
                            'filename': file_path.name,
                            'file_type': ext,
                            'file_size': file_path.stat().st_size
                        })
                    
                    documents.extend(docs)
                    logger.info(f"✅ Loaded: {file_path.name} ({len(docs)} chunks)")
                    
            except Exception as e:
                logger.error(f"❌ Failed to load {file_path}: {e}")
                continue
        
        logger.info(f"📊 Total documents loaded: {len(documents)}")
        return documents
    
    async def process_documents(self, documents: List[Document]) -> List[Document]:
        """Process and chunk documents for better RAG performance"""
        if not documents:
            return []
        
        logger.info(f"🔧 Processing {len(documents)} documents...")
        
        # Split documents into chunks
        chunked_docs = await asyncio.to_thread(
            self.text_splitter.split_documents, 
            documents
        )
        
        # Add chunk metadata
        for i, doc in enumerate(chunked_docs):
            doc.metadata['chunk_id'] = i
            doc.metadata['chunk_length'] = len(doc.page_content)
        
        logger.info(f"✅ Created {len(chunked_docs)} chunks")
        return chunked_docs
    
    async def add_documents_to_vector_store(self, documents: List[Document]) -> bool:
        """Add documents to ChromaDB vector store"""
        if not documents:
            logger.warning("⚠️ No documents to add")
            return False
        
        try:
            logger.info(f"🔄 Adding {len(documents)} documents to vector store...")
            
            # Add documents to vector store
            await asyncio.to_thread(
                self.vector_store.add_documents,
                documents
            )
            
            logger.info(f"✅ Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add documents: {e}")
            return False
    
    async def search_similar_documents(
        self, 
        query: str, 
        k: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search for similar documents using semantic similarity"""
        try:
            logger.info(f"🔍 Searching for: '{query}' (top {k})")
            
            # Perform similarity search
            results = await asyncio.to_thread(
                self.vector_store.similarity_search_with_score,
                query,
                k=k
            )
            
            # Filter by similarity threshold and format results
            filtered_results = []
            for doc, score in results:
                # Convert distance to similarity (ChromaDB uses distance)
                similarity = 1 - score if score <= 1 else 1 / (1 + score)
                
                if similarity >= similarity_threshold:
                    filtered_results.append({
                        'content': doc.page_content,
                        'metadata': doc.metadata,
                        'similarity': similarity,
                        'score': score
                    })
            
            logger.info(f"✅ Found {len(filtered_results)} relevant documents")
            
            # Log top results for debugging
            for i, result in enumerate(filtered_results[:3]):
                logger.info(f"  {i+1}. {result['metadata'].get('filename', 'Unknown')} "
                          f"(similarity: {result['similarity']:.3f})")
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            return []
    
    async def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        try:
            collection = self.chroma_client.get_collection(self.collection_name)
            count = collection.count()
            
            return {
                'collection_name': self.collection_name,
                'document_count': count,
                'embedding_model': self.embedding_model_name,
                'persist_directory': str(self.persist_dir),
                'status': 'active'
            }
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {
                'collection_name': self.collection_name,
                'document_count': 0,
                'status': 'error',
                'error': str(e)
            }
    
    async def reset_vector_store(self) -> bool:
        """Reset the vector store (delete all documents)"""
        try:
            logger.warning("🗑️ Resetting vector store...")
            
            # Delete collection
            try:
                self.chroma_client.delete_collection(self.collection_name)
            except:
                pass  # Collection might not exist
            
            # Reinitialize
            self._init_vector_store()
            
            logger.info("✅ Vector store reset complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Reset failed: {e}")
            return False
    
    async def pipeline_process_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Complete pipeline: Load documents -> Process -> Add to vector store
        """
        logger.info(f"🚀 Starting pipeline for directory: {directory_path}")
        
        try:
            # Step 1: Load documents
            documents = await self.load_documents_from_directory(directory_path)
            if not documents:
                return {
                    'success': False,
                    'message': 'No documents found or loaded',
                    'stats': {'documents': 0, 'chunks': 0}
                }
            
            # Step 2: Process documents (chunking)
            processed_docs = await self.process_documents(documents)
            
            # Step 3: Add to vector store
            success = await self.add_documents_to_vector_store(processed_docs)
            
            # Get final stats
            stats = await self.get_vector_store_stats()
            
            return {
                'success': success,
                'message': f'Processed {len(documents)} documents into {len(processed_docs)} chunks',
                'stats': {
                    'documents': len(documents),
                    'chunks': len(processed_docs),
                    'total_in_db': stats.get('document_count', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            return {
                'success': False,
                'message': f'Pipeline failed: {str(e)}',
                'stats': {'documents': 0, 'chunks': 0}
            }

# Global instance
local_rag_service = LocalRAGService() 