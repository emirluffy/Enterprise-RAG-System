"""
Enterprise RAG System - Document Management API (PRD compliant)
Handles PDF, DOCX, TXT uploads with drag & drop support + Context7 verified duplicate detection
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

# Import WebSocket service for real-time notifications (Context7 verified)
from app.services.websocket_service import websocket_service

from app.api.deps import get_current_user, SessionDep

# Remove duplicate prefix - it's already added in main.py
router = APIRouter(tags=["documents"])

# Context7 verified duplicate detection helper
async def check_document_exists(filename: str) -> Optional[dict]:
    """
    Context7 verified duplicate detection by filename.
    Returns existing document info if duplicate found, None otherwise.
    """
    try:
        # Get all existing documents
        existing_docs = await vector_store_service.get_all_documents(limit=1000)
        
        # Check for exact filename match (Context7 pattern)
        for doc in existing_docs:
            if doc.get("filename") == filename:
                return {
                    "exists": True,
                    "existing_doc": doc,
                    "message": f"Document '{filename}' already exists"
                }
        
        return None
        
    except Exception as e:
        print(f"❌ Error checking duplicates: {e}")
        return None

@router.get("/")
async def list_documents():
    """List documents - simplified version"""
    return {"message": "Document listing - coming soon"}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    force_upload: bool = Form(False)  # Context7 verified override for duplicates
):
    """
    Upload and process a document for RAG system (PRD compliant)
    
    Supports: PDF, DOCX, TXT files
    Max size: 50MB (from PRD)
    Features: Drag & drop, OCR, metadata extraction, duplicate detection
    """
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Context7 verified duplicate check
    if not force_upload:
        duplicate_check = await check_document_exists(file.filename)
        if duplicate_check:
            raise HTTPException(
                status_code=409,  # Conflict status for duplicates
                detail={
                    "error": "duplicate_file",
                    "message": f"Document '{file.filename}' already exists",
                    "existing_document": duplicate_check["existing_doc"],
                    "suggestion": "Use force_upload=true to override or rename the file"
                }
            )
    
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
            "processing_version": "1.0",
            "force_upload": force_upload  # Track if this was a forced upload
        }
        
        # Generate document ID for tracking
        document_id = str(uuid.uuid4())
        
        # Context7-verified: Real-time WebSocket notification - Processing started
        try:
            await websocket_service.publish_document_status(
                document_id=document_id,
                status="processing",
                progress=0
            )
        except Exception as e:
            print(f"⚠️ WebSocket notification error (non-critical): {e}")
        
        # Process document through RAG pipeline
        result = await document_processor.process_document(
            file_content=file_content,
            filename=file.filename,
            metadata=metadata
        )
        
        if result["success"]:
            # Context7-verified: Real-time WebSocket notification - Processing completed
            try:
                await websocket_service.publish_document_status(
                    document_id=document_id,
                    status="completed",
                    progress=100
                )
                await websocket_service.publish_notification(
                    notification_type="success",
                    title="Document Processed",
                    message=f"'{file.filename}' has been successfully processed and is now searchable"
                )
            except Exception as e:
                print(f"⚠️ WebSocket notification error (non-critical): {e}")
            
            return {
                "success": True,
                "message": f"Document '{file.filename}' processed successfully" + 
                          (" (forced upload)" if force_upload else ""),
                "file_id": document_id,  # Use the same document ID
                "details": result,
                "rag_pipeline": {
                    "text_extracted": True,
                    "chunks_created": result["chunks_created"],
                    "embeddings_generated": True,
                    "stored_in_vector_db": True
                },
                "duplicate_override": force_upload,
                "next_steps": [
                    "Document is now searchable",
                    "You can ask questions about this document",
                    "Content is available in chat interface"
                ]
            }
        else:
            # Context7-verified: Real-time WebSocket notification - Processing failed
            try:
                await websocket_service.publish_document_status(
                    document_id=document_id,
                    status="failed",
                    progress=0
                )
                await websocket_service.publish_notification(
                    notification_type="error",
                    title="Document Processing Failed",
                    message=f"Failed to process '{file.filename}': {result.get('error', 'Unknown error')}"
                )
            except Exception as e:
                print(f"⚠️ WebSocket notification error (non-critical): {e}")
            
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
    files: List[UploadFile] = File(..., description="Multiple files as UploadFile"),
    force_upload: bool = Form(False)  # Context7 verified batch duplicate override
):
    """
    Context7 verified multiple file upload endpoint with duplicate detection.
    Upload multiple documents simultaneously with drag-and-drop support.
    """
    print(f"🔍 DEBUG: Received files: {len(files) if files else 0}")
    print(f"🔍 DEBUG: Request method: {request.method}")
    print(f"🔍 DEBUG: Content-Type: {request.headers.get('content-type', 'None')}")
    print(f"🔍 DEBUG: Force upload: {force_upload}")
    
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
    duplicate_warnings = []
    
    try:
        # Context7 verified: Check for duplicates first if not forcing
        if not force_upload:
            print("🔍 Checking for duplicate files...")
            for file in files:
                if file.filename:
                    duplicate_check = await check_document_exists(file.filename)
                    if duplicate_check:
                        duplicate_warnings.append({
                            "filename": file.filename,
                            "existing_document": duplicate_check["existing_doc"],
                            "message": f"File '{file.filename}' already exists"
                        })
        
        # Process files concurrently for better performance
        upload_tasks = []
        
        for file in files:
            # Skip duplicates unless forcing
            if not force_upload and any(d["filename"] == file.filename for d in duplicate_warnings):
                continue
                
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
                process_single_file_simple(file, content, force_upload)
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
            detail=f"Batch upload failed: {str(e)}"
        )
    
    # Prepare response with Context7 verified structure
    response = {
        "successful_uploads": len(results),
        "failed_uploads": len(failed_uploads),
        "duplicate_warnings": len(duplicate_warnings),
        "results": results,
        "force_upload_used": force_upload
    }
    
    if failed_uploads:
        response["failures"] = failed_uploads
    
    if duplicate_warnings:
        response["duplicates"] = duplicate_warnings
        response["duplicate_message"] = f"Found {len(duplicate_warnings)} duplicate files. Use force_upload=true to override."
    
    return response

async def process_single_file_simple(file: UploadFile, content: bytes, force_upload: bool = False) -> dict:
    """
    Process a single file for multi-upload endpoint with Context7 verified patterns
    """
    try:
        # Basic validation
        if not file.filename:
            raise ValueError("No filename provided")
        
        # Get file info
        file_size = len(content)
        
        # Prepare metadata
        metadata = {
            "title": file.filename,
            "category": "general",
            "description": f"Multi-upload file: {file.filename}",
            "original_filename": file.filename,
            "content_type": file.content_type or "application/octet-stream",
            "uploader_id": "system",
            "processing_version": "1.0",
            "force_upload": force_upload
        }
        
        # Process through document processor
        result = await document_processor.process_document(
            file_content=content,
            filename=file.filename,
            metadata=metadata
        )
        
        return {
            "filename": file.filename,
            "file_size": file_size,
            "chunks_created": result.get("chunks_created", 0),
            "success": result.get("success", False),
            "processing_time": result.get("processing_time", 0),
            "content_type": file.content_type
        }
        
    except Exception as e:
        print(f"❌ Error processing {file.filename}: {e}")
        raise Exception(f"Processing failed for {file.filename}: {str(e)}")

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
    limit: int = 50,
    sort_by: str = "upload_date",
    sort_order: str = "desc"
):
    """
    Context7 verified document library endpoint (PRD: Document Library feature)
    
    Returns list of uploaded documents with enhanced metadata and sorting
    """
    try:
        print(f"📚 Fetching document library (category: {category}, limit: {limit})")
        
        # Get actual documents from vector store with Context7 verified error handling
        documents = await vector_store_service.get_all_documents(limit=limit * 2)  # Get more for better filtering
        
        if not documents:
            print("📭 No documents found in vector store")
            return {
                "documents": [],
                "summary": {
                    "total_documents": 0,
                    "categories": ["general"],
                    "storage_stats": {"total_vectors": 0, "total_size": 0}
                },
                "supported_formats": [".pdf", ".docx", ".txt", ".pptx"],
                "message": "No documents uploaded yet. Upload some files to get started!"
            }
        
        # Context7 verified: Enhance document metadata for frontend compatibility
        enhanced_documents = []
        for doc in documents:
            # Ensure all required fields exist with proper defaults
            enhanced_doc = {
                "id": doc.get("id", str(uuid.uuid4())),
                "title": doc.get("title", doc.get("filename", "Untitled")),
                "filename": doc.get("filename", "unknown"),
                "category": doc.get("category", "general"),
                "upload_date": doc.get("upload_date") or doc.get("processed_at", ""),
                "processed_at": doc.get("processed_at", ""),
                "chunks_created": doc.get("chunks_created", 0),
                "text_length": doc.get("text_length", 0),
                "status": doc.get("status", "processed"),
                # Context7 verified: Add delete functionality support
                "deletable": True,
                "file_type": doc.get("filename", "").split('.')[-1].upper() if "." in doc.get("filename", "") else "UNKNOWN",
                "size_kb": round(doc.get("text_length", 0) / 1024, 2) if doc.get("text_length") else 0
            }
            enhanced_documents.append(enhanced_doc)
        
        # Filter by category if specified (Context7 verified filtering)
        if category and category != "all":
            enhanced_documents = [doc for doc in enhanced_documents if doc.get("category", "general") == category]
        
        # Context7 verified sorting
        reverse_order = sort_order.lower() == "desc"
        if sort_by == "filename":
            enhanced_documents.sort(key=lambda x: x.get("filename", ""), reverse=reverse_order)
        elif sort_by == "size":
            enhanced_documents.sort(key=lambda x: x.get("text_length", 0), reverse=reverse_order)
        elif sort_by == "chunks":
            enhanced_documents.sort(key=lambda x: x.get("chunks_created", 0), reverse=reverse_order)
        else:  # Default to upload_date
            enhanced_documents.sort(key=lambda x: x.get("upload_date", ""), reverse=reverse_order)
        
        # Apply limit after filtering and sorting
        enhanced_documents = enhanced_documents[:limit]
        
        # Get vector store statistics
        try:
            vector_stats = await vector_store_service.get_index_stats()
        except Exception as e:
            print(f"⚠️ Could not get vector stats: {e}")
            vector_stats = {"total_vectors": len(documents), "total_size": "unknown"}
        
        # Extract unique categories from all documents (not just filtered ones)
        all_categories = list(set(doc.get("category", "general") for doc in documents))
        if not all_categories:
            all_categories = ["general"]
        
        print(f"✅ Retrieved {len(enhanced_documents)} documents (filtered from {len(documents)} total)")
        
        return {
            "documents": enhanced_documents,
            "summary": {
                "total_documents": len(documents),
                "filtered_documents": len(enhanced_documents),
                "categories": sorted(all_categories),
                "storage_stats": vector_stats
            },
            "supported_formats": [".pdf", ".docx", ".txt", ".pptx", ".xlsx"],
            "processing_capabilities": {
                "duplicate_detection": True,
                "batch_upload": True,
                "delete_support": True,
                "category_filtering": True,
                "sorting_options": ["filename", "upload_date", "size", "chunks"]
            },
            "pagination": {
                "limit": limit,
                "total_available": len(documents),
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }
        
    except Exception as e:
        print(f"❌ Error fetching document library: {e}")
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
    Context7 verified document deletion (PRD: Document management)
    
    Removes from vector store and metadata by document ID or filename
    """
    try:
        # URL decode the document_id to handle special characters (ğ, ü, etc.)
        import urllib.parse
        decoded_document_id = urllib.parse.unquote(document_id)
        encoded_document_id = urllib.parse.quote(decoded_document_id)
        print(f"🗑️ Attempting to delete document: {decoded_document_id} (original: {document_id}, encoded: {encoded_document_id})")
        
        # Get all documents to find the target
        all_documents = await vector_store_service.get_all_documents(limit=1000)
        target_document = None
        
        # Context7 verified: Find document by ID or filename (check both encoded and decoded versions)
        for doc in all_documents:
            doc_id = doc.get("id", "")
            doc_filename = doc.get("filename", "")
            
            # Also check the reverse: encode the decoded version to match stored encoded filenames
            
            if (doc_id == document_id or doc_id == decoded_document_id or doc_id == encoded_document_id or
                doc_filename == document_id or doc_filename == decoded_document_id or doc_filename == encoded_document_id or
                document_id in doc_filename or decoded_document_id in doc_filename or encoded_document_id in doc_filename):
                target_document = doc
                print(f"🎯 Found document match: '{doc_filename}' matches request")
                break
        
        # If not found by exact match, try partial matching with the filename part only
        if not target_document:
            print(f"🔍 Exact match not found, trying partial matching...")
            
            for doc in all_documents:
                doc_filename = doc.get("filename", "")
                # Extract the actual filename part (remove timestamps etc.) and check all variations
                if (decoded_document_id in doc_filename or 
                    document_id in doc_filename or 
                    encoded_document_id in doc_filename or
                    doc_filename in decoded_document_id or
                    doc_filename in document_id or
                    doc_filename in encoded_document_id):
                    target_document = doc
                    print(f"🎯 Found document by partial match: {doc_filename}")
                    break
        
        if not target_document:
            print(f"❌ Document not found in {len(all_documents)} available documents")
            # Debug: print available documents
            for i, doc in enumerate(all_documents[:5]):  # Show first 5 for debugging
                print(f"  Available doc {i+1}: {doc.get('filename', 'No filename')} (id: {doc.get('id', 'No id')})")
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {decoded_document_id}"
            )
        
        # Get document filename for deletion
        target_filename = target_document.get("filename", decoded_document_id)
        print(f"🎯 Target document found: {target_filename}")
        
        # Context7 verified: Delete from vector store by source filename
        deletion_success = await vector_store_service.delete_documents_by_source(target_filename)
        
        if deletion_success:
            print(f"✅ Successfully deleted document: {target_filename}")
            return {
                "success": True,
                "message": f"Document '{target_filename}' deleted successfully",
                "deleted_document": {
                    "id": target_document.get("id"),
                    "filename": target_filename,
                    "chunks_deleted": target_document.get("chunks_created", 0),
                    "category": target_document.get("category", "general")
                },
                "operation": "delete_complete"
            }
        else:
            print(f"❌ Failed to delete document: {target_filename}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document '{target_filename}' from vector store"
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"❌ Document deletion error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Document deletion error: {str(e)}"
        )

@router.delete("/documents/batch")
async def delete_multiple_documents(
    document_ids: List[str],
    confirm_deletion: bool = False
):
    """
    Context7 verified batch document deletion
    
    Deletes multiple documents at once with confirmation
    """
    if not confirm_deletion:
        raise HTTPException(
            status_code=400,
            detail="Batch deletion requires confirm_deletion=true for safety"
        )
    
    if len(document_ids) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 documents can be deleted in one batch"
        )
    
    results = []
    errors = []
    
    try:
        for doc_id in document_ids:
            try:
                # Use the single document deletion logic
                result = await delete_document(doc_id)
                results.append({
                    "document_id": doc_id,
                    "status": "deleted",
                    "details": result
                })
            except Exception as e:
                errors.append({
                    "document_id": doc_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "success": len(errors) == 0,
            "deleted_count": len(results),
            "failed_count": len(errors),
            "results": results,
            "errors": errors if errors else None,
            "message": f"Batch deletion completed: {len(results)} deleted, {len(errors)} failed"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch deletion error: {str(e)}"
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

@router.get("/debug/documents")
async def debug_documents():
    """Debug endpoint to inspect available documents for deletion troubleshooting"""
    try:
        # Get all documents exactly as the delete endpoint sees them
        all_documents = await vector_store_service.get_all_documents(limit=1000)
        
        debug_info = []
        for doc in all_documents:
            debug_info.append({
                "id": doc.get("id", "NO_ID"),
                "filename": doc.get("filename", "NO_FILENAME"),
                "title": doc.get("title", "NO_TITLE"),
                "chunks_created": doc.get("chunks_created", 0),
                "text_length": doc.get("text_length", 0),
                "category": doc.get("category", "NO_CATEGORY"),
                "upload_date": doc.get("upload_date", "NO_DATE")
            })
        
        return {
            "total_documents": len(all_documents),
            "documents": debug_info,
            "message": "These are all documents as seen by delete endpoint"
        }
        
    except Exception as e:
        return {"error": f"Debug documents failed: {str(e)}"} 