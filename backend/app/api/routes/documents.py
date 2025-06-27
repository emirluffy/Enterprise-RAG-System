"""
Enterprise RAG System - Document Management API (PRD compliant)
Handles PDF, DOCX, TXT uploads with drag & drop support
"""
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, status, Request
from fastapi.responses import JSONResponse
import asyncio
from sqlalchemy.orm import Session

from app.services.document_processor import document_processor
from app.services.vector_store import vector_store_service
from app.core.config import settings

from app.api.deps import get_current_user, SessionDep

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("/")
async def list_documents():
    """List documents - simplified version"""
    return {"message": "Document listing - coming soon"}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """
    Upload and process a document for RAG system (PRD compliant)
    
    Supports: PDF, DOCX, TXT files
    Max size: 50MB (from PRD)
    Features: Drag & drop, OCR, metadata extraction
    """
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file size (50MB limit from PRD)
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        size_mb = len(file_content) / (1024 * 1024)
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=413, 
            detail=f"File too large: {size_mb:.1f}MB > {max_mb}MB limit"
        )
    
    # Validate file format
    filename = file.filename.lower()
    supported_extensions = ['.pdf', '.docx', '.txt', '.pptx', '.ppt', '.xlsx']
    file_ext = next((ext for ext in supported_extensions if filename.endswith(ext)), None)
    
    if not file_ext:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported: {', '.join(supported_extensions)}"
        )
    
    try:
        # Prepare metadata (PRD requirements)
        metadata = {
            "title": title or file.filename,
            "category": category or "general",
            "description": description or "",
            "original_filename": file.filename,
            "content_type": file.content_type,
            "uploader_id": "system",  # TODO: Get from auth when implemented
            "processing_version": "1.0"
        }
        
        # Process document through RAG pipeline
        result = await document_processor.process_document(
            file_content=file_content,
            filename=file.filename,
            metadata=metadata
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Document '{file.filename}' processed successfully",
                "file_id": str(uuid.uuid4()),  # Generate unique file ID
                "details": result,
                "rag_pipeline": {
                    "text_extracted": True,
                    "chunks_created": result["chunks_created"],
                    "embeddings_generated": True,
                    "stored_in_vector_db": True
                },
                "next_steps": [
                    "Document is now searchable",
                    "You can ask questions about this document",
                    "Content is available in chat interface"
                ]
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Document processing failed: {result.get('error', 'Unknown error')}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload processing error: {str(e)}"
        )

@router.post("/upload-multiple")
async def upload_multiple_documents(
    request: Request,
    files: List[UploadFile] = File(..., description="Multiple files as UploadFile")
):
    """
    Context7 verified multiple file upload endpoint.
    Upload multiple documents simultaneously with drag-and-drop support.
    """
    print(f"🔍 DEBUG: Received files: {len(files) if files else 0}")
    print(f"🔍 DEBUG: Request method: {request.method}")
    print(f"🔍 DEBUG: Content-Type: {request.headers.get('content-type', 'None')}")
    
    # Debug form data
    try:
        form = await request.form()
        print(f"🔍 DEBUG: Form keys: {list(form.keys())}")
        for key, value in form.items():
            print(f"🔍 DEBUG: Form[{key}] = {type(value)} ({getattr(value, 'filename', 'N/A')})")
    except Exception as e:
        print(f"🔍 DEBUG: Form parsing error: {e}")
    
    for i, file in enumerate(files):
        print(f"📁 File {i+1}: {file.filename} ({file.content_type})")
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    # Check file count limit
    if len(files) > 10:  # Reasonable limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per upload"
        )
    
    results = []
    failed_uploads = []
    
    try:
        # Process files concurrently for better performance
        upload_tasks = []
        
        for file in files:
            # Validate file type
            if not file.filename:
                failed_uploads.append({
                    "filename": "unknown",
                    "error": "No filename provided"
                })
                continue
                
            # Check file size (100MB limit per file)
            content = await file.read()
            await file.seek(0)  # Reset file pointer
            
            if len(content) > 100 * 1024 * 1024:
                failed_uploads.append({
                    "filename": file.filename,
                    "error": "File too large (max 100MB)"
                })
                continue
            
            # Create upload task
            upload_tasks.append(
                process_single_file_simple(file, content)
            )
        
        # Execute all uploads concurrently
        if upload_tasks:
            upload_results = await asyncio.gather(*upload_tasks, return_exceptions=True)
            
            for i, result in enumerate(upload_results):
                if isinstance(result, Exception):
                    failed_uploads.append({
                        "filename": files[i].filename if i < len(files) else "unknown",
                        "error": str(result)
                    })
                else:
                    results.append(result)
    
    except Exception as e:
        print(f"❌ UPLOAD ERROR: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload processing failed: {str(e)}"
        )
    
    # Prepare response
    response_data = {
        "message": f"Processed {len(results)} files successfully",
        "successful_uploads": len(results),
        "failed_uploads": len(failed_uploads),
        "results": results
    }
    
    if failed_uploads:
        response_data["failures"] = failed_uploads
    
    print(f"✅ UPLOAD COMPLETE: {len(results)} success, {len(failed_uploads)} failed")
    return JSONResponse(content=response_data)

async def process_single_file_simple(file: UploadFile, content: bytes) -> dict:
    """
    Process a single file upload using existing document processor
    """
    try:
        # Validate filename
        if not file.filename:
            raise Exception("No filename provided")
            
        # Prepare metadata
        metadata = {
            "title": file.filename,
            "category": "batch_upload",
            "original_filename": file.filename,
            "content_type": file.content_type,
            "processing_method": "multi_upload",
            "processing_version": "1.0"
        }
        
        # Use existing document processor
        result = await document_processor.process_document(
            file_content=content,
            filename=file.filename,  # This is now guaranteed to be str
            metadata=metadata
        )
        
        if result["success"]:
            return {
                "filename": file.filename,
                "status": "success",
                "chunks_created": result.get("chunks_created", 0),
                "text_length": result.get("text_length", 0),
                "file_size": len(content),
                "content_type": file.content_type
            }
        else:
            raise Exception(result.get("error", "Processing failed"))
        
    except Exception as e:
        raise Exception(f"Processing failed for {file.filename or 'unknown'}: {str(e)}")

@router.get("/upload-progress/{filename}")
async def get_upload_progress(
    filename: str
):
    """
    Get upload progress for batch uploads (placeholder for future enhancement)
    """
    # This is a placeholder - in a real implementation, you'd track progress
    # in Redis or a database
    return {
        "filename": filename,
        "status": "completed",  # or "processing", "failed"
        "progress": 100,
        "message": "Upload completed successfully"
    }

@router.get("/library")
async def get_document_library(
    category: Optional[str] = None,
    limit: int = 50
):
    """
    Get document library (PRD: Document Library feature)
    
    Returns list of uploaded documents with metadata
    """
    try:
        # Get actual documents from vector store
        documents = await vector_store_service.get_all_documents(limit=limit)
        
        # Filter by category if specified
        if category and category != "all":
            documents = [doc for doc in documents if doc.get("category", "general") == category]
        
        # Get vector store statistics
        vector_stats = await vector_store_service.get_index_stats()
        
        # Extract unique categories from documents
        categories = list(set(doc.get("category", "general") for doc in documents))
        if not categories:
            categories = ["general"]
        
        return {
            "documents": documents,
            "summary": {
                "total_documents": len(documents),
                "categories": categories,
                "storage_stats": vector_stats
            },
            "supported_formats": document_processor.supported_formats,
            "processing_capabilities": await document_processor.get_processing_status()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching document library: {str(e)}"
        )

@router.get("/search")
async def search_documents(
    query: str,
    top_k: int = 10,
    category: Optional[str] = None
):
    """
    Search documents by text query (PRD: Gelişmiş arama filtreleri)
    
    Returns relevant document chunks with similarity scores
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Search query is required")
    
    try:
        # Create embedding for search query
        from app.services.embeddings import embeddings_service
        query_embedding = await embeddings_service.create_single_embedding(query)
        
        # Search with optional category filter
        filter_metadata = {"category": category} if category else None
        
        results = await vector_store_service.search_similar_documents(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        # Format search results
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content_preview": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                "source": doc["source"],
                "page": doc.get("page", "N/A"),
                "similarity_score": round(doc["score"], 3),
                "metadata": {
                    "title": doc["metadata"].get("title", doc["source"]),
                    "category": doc["metadata"].get("category", "general"),
                    "chunk_index": doc["metadata"].get("chunk_index", 0)
                }
            })
        
        return {
            "query": query,
            "results": formatted_results,
            "total_found": len(results),
            "search_parameters": {
                "top_k": top_k,
                "category_filter": category,
                "similarity_threshold": "auto"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document search error: {str(e)}"
        )

@router.get("/status")
async def get_processing_status():
    """
    Get document processing system status (PRD: System monitoring)
    
    Returns capabilities, statistics, and health information
    """
    try:
        status = await document_processor.get_processing_status()
        
        return {
            "system_status": "operational",
            "capabilities": {
                "supported_formats": status["supported_formats"],
                "max_file_size_mb": status["max_file_size_mb"],
                "ocr_available": status.get("pdf_available", False),
                "batch_upload": True,
                "drag_drop": True  # Frontend feature
            },
            "processing_settings": {
                "chunk_size": status["chunk_size"],
                "chunk_overlap": status["chunk_overlap"],
                "embeddings_model": status["embeddings_model"],
                "embeddings_dimension": status["embeddings_dimension"]
            },
            "storage": status.get("vector_store_stats", {}),
            "limits": {
                "max_file_size": f"{status['max_file_size_mb']}MB",
                "supported_extensions": status["supported_formats"],
                "max_batch_size": "10 files"
            }
        }
        
    except Exception as e:
        return {
            "system_status": "error",
            "error": str(e),
            "capabilities": {
                "supported_formats": [".txt"],  # Fallback
                "max_file_size_mb": 50,
                "ocr_available": False
            }
        }

@router.delete("/document/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the RAG system (PRD: Document management)
    
    Removes from vector store and metadata
    """
    try:
        # TODO: Implement document ID to chunk IDs mapping
        # For now, return placeholder response
        
        return {
            "success": True,
            "message": f"Document {document_id} deletion queued",
            "note": "Full deletion implementation pending - requires document ID mapping"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document deletion error: {str(e)}"
        )

@router.get("/debug/chunks")
async def debug_chunks(source: Optional[str] = None):
    """Debug endpoint to inspect chunk contents"""
    try:
        from ...services.vector_store import vector_store_service
        
        if not vector_store_service.in_memory_vectors:
            return {"error": "No chunks in memory"}
        
        # Filter by source if provided
        chunks = vector_store_service.in_memory_vectors
        if source:
            chunks = [c for c in chunks if source.lower() in c["metadata"].get("source", "").lower()]
        
        debug_info = []
        for i, chunk in enumerate(chunks[:10]):  # Limit to first 10 chunks
            debug_info.append({
                "index": i,
                "id": chunk["id"],
                "source": chunk["metadata"].get("source", ""),
                "content": chunk["metadata"].get("content", "")[:500],  # First 500 chars
                "full_length": len(chunk["metadata"].get("content", "")),
                "page": chunk["metadata"].get("page", 0)
            })
        
        return {
            "total_chunks": len(vector_store_service.in_memory_vectors),
            "filtered_chunks": len(chunks),
            "showing": len(debug_info),
            "chunks": debug_info
        }
        
    except Exception as e:
        return {"error": f"Debug failed: {str(e)}"} 