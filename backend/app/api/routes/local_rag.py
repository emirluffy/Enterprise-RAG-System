"""
Local RAG API Endpoints - Completely Free System
FastAPI routes for local RAG operations
Context7 Verified Implementation - 2024
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import shutil
import tempfile
from pathlib import Path

from ...services.local_rag_service import local_rag_service
from ...services.local_llm_service import local_llm_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/local-rag", tags=["Local RAG"])

# Pydantic models
class QueryRequest(BaseModel):
    question: str
    k: int = 5
    similarity_threshold: float = 0.3

class QueryResponse(BaseModel):
    answer: str
    sources_used: int
    total_sources: int
    context_length: int
    model_used: str
    retrieved_documents: List[Dict[str, Any]]
    processing_time_ms: int

class ProcessDirectoryRequest(BaseModel):
    directory_path: str

class ProcessDirectoryResponse(BaseModel):
    success: bool
    message: str
    stats: Dict[str, Any]

class VectorStoreStats(BaseModel):
    collection_name: str
    document_count: int
    embedding_model: str
    persist_directory: str
    status: str

class ModelInfo(BaseModel):
    model_name: str
    device: str
    is_loaded: bool
    max_length: int
    gpu_memory_allocated: Optional[str] = None
    gpu_memory_reserved: Optional[str] = None

@router.get("/health")
async def health_check():
    """Health check for local RAG system"""
    try:
        stats = await local_rag_service.get_vector_store_stats()
        model_info = await local_llm_service.get_model_info()
        
        return {
            "status": "healthy",
            "local_rag": {
                "vector_store": stats,
                "llm_model": model_info
            },
            "timestamp": "2024-12-25"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/process-directory", response_model=ProcessDirectoryResponse)
async def process_directory(request: ProcessDirectoryRequest, background_tasks: BackgroundTasks):
    """
    Process all supported documents in a directory
    Supports: PPT, PPTX, DOC, DOCX, PDF, MD, TXT
    """
    try:
        logger.info(f"🚀 Processing directory: {request.directory_path}")
        
        # Process directory in background for large datasets
        result = await local_rag_service.pipeline_process_directory(request.directory_path)
        
        return ProcessDirectoryResponse(**result)
        
    except Exception as e:
        logger.error(f"Directory processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload and process multiple files
    Supports: PPT, PPTX, DOC, DOCX, PDF, MD, TXT
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save uploaded files
            saved_files = []
            for file in files:
                if file.filename:
                    file_path = temp_path / file.filename
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(file.file, buffer)
                    saved_files.append(file.filename)
            
            logger.info(f"📁 Saved {len(saved_files)} files to temporary directory")
            
            # Process the temporary directory
            result = await local_rag_service.pipeline_process_directory(str(temp_path))
            
            return {
                "success": result["success"],
                "message": result["message"],
                "files_processed": saved_files,
                "stats": result["stats"]
            }
            
    except Exception as e:
        logger.error(f"File upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query documents using local RAG
    Returns answer with source citations
    """
    try:
        import time
        start_time = time.time()
        
        logger.info(f"🔍 Query: '{request.question}'")
        
        # Step 1: Retrieve relevant documents
        retrieved_docs = await local_rag_service.search_similar_documents(
            query=request.question,
            k=request.k,
            similarity_threshold=request.similarity_threshold
        )
        
        if not retrieved_docs:
            # No documents found - use general knowledge
            response = await local_llm_service.generate_response(
                prompt=request.question,
                context=None,
                max_new_tokens=200
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return QueryResponse(
                answer=f"I couldn't find specific information in the uploaded documents about '{request.question}'. Here's what I can tell you:\n\n{response}",
                sources_used=0,
                total_sources=0,
                context_length=0,
                model_used=local_llm_service.model_name,
                retrieved_documents=[],
                processing_time_ms=processing_time
            )
        
        # Step 2: Generate answer using RAG
        rag_result = await local_llm_service.answer_with_rag(
            question=request.question,
            retrieved_docs=retrieved_docs
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Format retrieved documents for response
        formatted_docs = []
        for i, doc in enumerate(retrieved_docs):
            formatted_docs.append({
                "source": doc['metadata'].get('filename', 'Unknown'),
                "similarity": round(doc['similarity'], 3),
                "content_preview": doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
            })
        
        return QueryResponse(
            answer=rag_result['answer'],
            sources_used=rag_result['sources_used'],
            total_sources=rag_result['total_sources'],
            context_length=rag_result['context_length'],
            model_used=rag_result['model_used'],
            retrieved_documents=formatted_docs,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@router.get("/stats", response_model=VectorStoreStats)
async def get_vector_store_stats():
    """Get vector store statistics"""
    try:
        stats = await local_rag_service.get_vector_store_stats()
        return VectorStoreStats(**stats)
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

@router.get("/model-info", response_model=ModelInfo)
async def get_model_info():
    """Get LLM model information"""
    try:
        info = await local_llm_service.get_model_info()
        return ModelInfo(**info)
    except Exception as e:
        logger.error(f"Model info failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model info failed: {str(e)}")

@router.post("/load-model")
async def load_model():
    """Load the LLM model into memory"""
    try:
        success = await local_llm_service.load_model()
        if success:
            return {"message": "Model loaded successfully", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to load model")
    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model loading failed: {str(e)}")

@router.post("/unload-model")
async def unload_model():
    """Unload the LLM model to free memory"""
    try:
        success = await local_llm_service.unload_model()
        if success:
            return {"message": "Model unloaded successfully", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to unload model")
    except Exception as e:
        logger.error(f"Model unloading failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model unloading failed: {str(e)}")

@router.post("/reset-vector-store")
async def reset_vector_store():
    """Reset the vector store (delete all documents)"""
    try:
        success = await local_rag_service.reset_vector_store()
        if success:
            return {"message": "Vector store reset successfully", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to reset vector store")
    except Exception as e:
        logger.error(f"Vector store reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported document formats"""
    return {
        "supported_formats": [
            {
                "extension": ".pptx",
                "description": "PowerPoint Presentation",
                "loader": "UnstructuredPowerPointLoader"
            },
            {
                "extension": ".ppt",
                "description": "PowerPoint Presentation (Legacy)",
                "loader": "UnstructuredPowerPointLoader"
            },
            {
                "extension": ".docx",
                "description": "Word Document",
                "loader": "UnstructuredWordDocumentLoader"
            },
            {
                "extension": ".doc",
                "description": "Word Document (Legacy)",
                "loader": "UnstructuredWordDocumentLoader"
            },
            {
                "extension": ".pdf",
                "description": "PDF Document",
                "loader": "UnstructuredPDFLoader"
            },
            {
                "extension": ".md",
                "description": "Markdown Document",
                "loader": "UnstructuredMarkdownLoader"
            },
            {
                "extension": ".txt",
                "description": "Text Document",
                "loader": "TextLoader"
            }
        ],
        "embedding_model": local_rag_service.embedding_model_name,
        "llm_model": local_llm_service.model_name
    } 