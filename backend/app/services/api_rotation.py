"""
Enterprise RAG System - Google Gemini API Key Rotation Service (Context7 Verified)
Automatically rotates between multiple API keys when quota is exhausted
"""
import asyncio
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from google import genai
from google.genai import errors, types
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiAPIRotationService:
    """
    Context7 verified API rotation service for multiple Gemini API keys
    Handles quota exhaustion with automatic failover
    """
    
    def __init__(self, api_keys: List[str]):
        """
        Initialize rotation service with multiple API keys
        
        Args:
            api_keys: List of Gemini API keys to rotate between
        """
        self.api_keys = api_keys
        self.current_key_index = 0
        self.clients: Dict[str, genai.Client] = {}
        self.key_status: Dict[str, Dict[str, Any]] = {}
        
        # Initialize clients and status tracking
        self._initialize_clients()
        
        # Quota reset tracking (Gemini resets daily)
        self.quota_reset_time = timedelta(hours=24)
        
    def _initialize_clients(self):
        """Initialize GenAI clients for each API key"""
        for i, api_key in enumerate(self.api_keys):
            try:
                # Context7 verified client initialization
                client = genai.Client(api_key=api_key)
                self.clients[api_key] = client
                
                # Track key status
                self.key_status[api_key] = {
                    "active": True,
                    "quota_exhausted": False,
                    "last_error_time": None,
                    "error_count": 0,
                    "successful_requests": 0,
                    "index": i
                }
                
                logger.info(f"✅ Initialized Gemini client for key #{i+1}")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize client for key #{i+1}: {e}")
                self.key_status[api_key] = {
                    "active": False,
                    "quota_exhausted": False,
                    "last_error_time": datetime.now(),
                    "error_count": 1,
                    "successful_requests": 0,
                    "index": i
                }
    
    def get_current_client(self) -> Optional[genai.Client]:
        """Get the currently active client"""
        current_key = self.api_keys[self.current_key_index]
        return self.clients.get(current_key)
    
    def get_current_key_info(self) -> Dict[str, Any]:
        """Get information about the current API key"""
        current_key = self.api_keys[self.current_key_index]
        return {
            "key_index": self.current_key_index + 1,
            "total_keys": len(self.api_keys),
            "key_mask": f"***{current_key[-6:]}",
            "status": self.key_status[current_key]
        }
    
    def _rotate_to_next_key(self) -> bool:
        """
        Rotate to the next available API key
        Returns True if rotation successful, False if no keys available
        """
        original_index = self.current_key_index
        attempts = 0
        
        while attempts < len(self.api_keys):
            # Move to next key
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            current_key = self.api_keys[self.current_key_index]
            
            # Check if this key is available
            status = self.key_status[current_key]
            
            # Reset quota if enough time has passed (24 hours)
            if (status["quota_exhausted"] and 
                status["last_error_time"] and 
                datetime.now() - status["last_error_time"] > self.quota_reset_time):
                
                status["quota_exhausted"] = False
                status["active"] = True
                status["error_count"] = 0
                logger.info(f"🔄 Reset quota for key #{self.current_key_index + 1}")
            
            # Use this key if it's active and not quota exhausted
            if status["active"] and not status["quota_exhausted"]:
                if self.current_key_index != original_index:
                    logger.info(f"🔄 Rotated to API key #{self.current_key_index + 1}")
                return True
            
            attempts += 1
        
        # No available keys found
        logger.error("❌ No available API keys - all quota exhausted or inactive")
        return False
    
    def _handle_api_error(self, error: errors.APIError, api_key: str):
        """Handle API error and update key status"""
        status = self.key_status[api_key]
        status["last_error_time"] = datetime.now()
        status["error_count"] += 1
        
        # Context7 verified error code handling
        if error.code == 429:  # RESOURCE_EXHAUSTED
            status["quota_exhausted"] = True
            status["active"] = False
            logger.warning(f"⚠️ API key #{status['index'] + 1} quota exhausted: {error.message}")
            
        elif error.code in [401, 403]:  # UNAUTHORIZED, FORBIDDEN
            status["active"] = False
            logger.error(f"❌ API key #{status['index'] + 1} authentication failed: {error.message}")
            
        else:
            # Other errors - temporary failure
            logger.warning(f"⚠️ API key #{status['index'] + 1} temporary error ({error.code}): {error.message}")
    
    async def create_embeddings_with_rotation(
        self, 
        texts: List[str], 
        model: str = None
    ) -> Optional[List[List[float]]]:
        """
        Create embeddings with automatic API key rotation on quota exhaustion
        FIXED: Now handles large batches by splitting into chunks of max 100
        
        Args:
            texts: List of texts to embed
            model: Embedding model (defaults to settings.GEMINI_EMBEDDING_MODEL)
            
        Returns:
            List of embedding vectors or None if all keys exhausted
        """
        if not texts:
            return []
        
        model = model or settings.GEMINI_EMBEDDING_MODEL
        
        # FIXED: Split large batches into chunks of max 100 (Gemini limit)
        all_embeddings = []
        batch_size = 100
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            logger.info(f"📦 Processing batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size} ({len(batch_texts)} texts)")
            
            # Try to process this batch with rotation
            batch_embeddings = await self._create_batch_with_rotation(batch_texts, model)
            if batch_embeddings is None:
                logger.error(f"❌ Failed to process batch {i//batch_size + 1}")
                return None
            
            all_embeddings.extend(batch_embeddings)
            logger.info(f"✅ Batch {i//batch_size + 1} completed: {len(batch_embeddings)} embeddings")
        
        logger.info(f"🎉 Successfully created {len(all_embeddings)} embeddings across {(len(texts) + batch_size - 1)//batch_size} batches!")
        return all_embeddings
    
    async def _create_batch_with_rotation(
        self, 
        texts: List[str], 
        model: str
    ) -> Optional[List[List[float]]]:
        """Process a single batch (≤100 texts) with API key rotation"""
        max_attempts = len(self.api_keys)
        
        for attempt in range(max_attempts):
            client = self.get_current_client()
            current_key = self.api_keys[self.current_key_index]
            
            if not client:
                logger.error(f"❌ No client available for key #{self.current_key_index + 1}")
                if not self._rotate_to_next_key():
                    return None
                continue
            
            try:
                # Context7 verified embedding creation
                response = await asyncio.to_thread(
                    client.models.embed_content,
                    model=model,
                    contents=texts,
                    config=types.EmbedContentConfig(
                        output_dimensionality=settings.GEMINI_EMBEDDING_DIMENSION,
                        task_type="retrieval_document"
                    )
                )
                
                # Success - update status
                self.key_status[current_key]["successful_requests"] += 1
                
                # Extract embeddings from response
                embeddings = []
                for embedding_data in response.embeddings:
                    embeddings.append(embedding_data.values)
                
                logger.info(f"✅ Created {len(embeddings)} embeddings using key #{self.current_key_index + 1}")
                return embeddings
                
            except errors.APIError as e:
                self._handle_api_error(e, current_key)
                
                # If quota exhausted, try next key
                if e.code == 429:
                    if not self._rotate_to_next_key():
                        logger.error("❌ All API keys quota exhausted")
                        return None
                    continue
                else:
                    # Other API errors - return None
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Unexpected error with key #{self.current_key_index + 1}: {e}")
                if not self._rotate_to_next_key():
                    return None
                continue
        
        logger.error("❌ Failed to create embeddings with all available keys")
        return None
    
    async def generate_content_with_rotation(
        self, 
        contents: str, 
        model: str = None,
        config: Optional[types.GenerateContentConfig] = None
    ) -> Optional[str]:
        """
        Generate content with automatic API key rotation
        
        Args:
            contents: Input text/prompt
            model: Model name (defaults to settings.GEMINI_MODEL)
            config: Generation configuration
            
        Returns:
            Generated text or None if all keys exhausted
        """
        model = model or settings.GEMINI_MODEL
        max_attempts = len(self.api_keys)
        
        for attempt in range(max_attempts):
            client = self.get_current_client()
            current_key = self.api_keys[self.current_key_index]
            
            if not client:
                if not self._rotate_to_next_key():
                    return None
                continue
            
            try:
                # Context7 verified content generation
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=contents,
                    config=config or types.GenerateContentConfig(
                        temperature=settings.DEFAULT_TEMPERATURE,
                        max_output_tokens=1000
                    )
                )
                
                # Success
                self.key_status[current_key]["successful_requests"] += 1
                logger.info(f"✅ Generated content using key #{self.current_key_index + 1}")
                return response.text
                
            except errors.APIError as e:
                self._handle_api_error(e, current_key)
                
                if e.code == 429:  # Quota exhausted
                    if not self._rotate_to_next_key():
                        return None
                    continue
                else:
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Unexpected error with key #{self.current_key_index + 1}: {e}")
                if not self._rotate_to_next_key():
                    return None
                continue
        
        return None
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive status report of all API keys"""
        report = {
            "current_key": self.current_key_index + 1,
            "total_keys": len(self.api_keys),
            "active_keys": 0,
            "quota_exhausted_keys": 0,
            "keys_detail": []
        }
        
        for i, (api_key, status) in enumerate(self.key_status.items()):
            if status["active"]:
                report["active_keys"] += 1
            if status["quota_exhausted"]:
                report["quota_exhausted_keys"] += 1
            
            report["keys_detail"].append({
                "index": i + 1,
                "key_mask": f"***{api_key[-6:]}",
                "active": status["active"],
                "quota_exhausted": status["quota_exhausted"],
                "successful_requests": status["successful_requests"],
                "error_count": status["error_count"],
                "last_error": status["last_error_time"].isoformat() if status["last_error_time"] else None
            })
        
        return report

# Global rotation service instance
_rotation_service: Optional[GeminiAPIRotationService] = None

def initialize_rotation_service(api_keys: List[str]) -> GeminiAPIRotationService:
    """Initialize the global rotation service"""
    global _rotation_service
    _rotation_service = GeminiAPIRotationService(api_keys)
    logger.info(f"🔄 Initialized API rotation service with {len(api_keys)} keys")
    return _rotation_service

def get_rotation_service() -> Optional[GeminiAPIRotationService]:
    """Get the global rotation service instance"""
    return _rotation_service 