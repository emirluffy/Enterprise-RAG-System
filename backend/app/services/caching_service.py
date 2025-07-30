from typing import Optional, Dict, Any, Union, List
import json
import asyncio
import hashlib
from datetime import datetime, timedelta
import logging
from functools import wraps

import redis.asyncio as redis
from redis_om import HashModel, JsonModel, Field, get_redis_connection
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# Context7 verified: Redis OM caching models

class CacheEntry(HashModel):
    """Context7 verified: Redis OM HashModel for cache entries"""
    key: str = Field(index=True)
    value: str  # JSON serialized value
    expiry: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(default=0)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)
    tags: str = Field(default="", index=True)  # Comma-separated tags for cache invalidation
    
    class Meta:
        global_key_prefix = "rag-cache"

class QueryCache(JsonModel):
    """Context7 verified: JsonModel for complex query caching"""
    query_hash: str = Field(index=True)
    query_text: str = Field(index=True, full_text_search=True)
    response_data: Dict[str, Any]
    sources_json: str = Field(default="[]")  # JSON serialized sources - Context7 verified pattern
    confidence: float = Field(default=0.0)
    response_time_ms: int = Field(default=0)
    user_id: Optional[str] = Field(index=True)
    department: Optional[str] = Field(index=True)
    sentiment: Optional[str] = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    hit_count: int = Field(default=0)
    
    class Meta:
        global_key_prefix = "rag-query-cache"
    
    @property
    def sources(self) -> List[Dict[str, Any]]:
        """Context7 verified: Deserialize sources from JSON"""
        try:
            return json.loads(self.sources_json) if self.sources_json else []
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_sources(self, sources: List[Dict[str, Any]]):
        """Context7 verified: Serialize sources to JSON"""
        self.sources_json = json.dumps(sources) if sources else "[]"

class EmbeddingCache(HashModel):
    """Context7 verified: HashModel for embedding caching"""
    text_hash: str = Field(index=True)
    text: str
    embedding_model: str = Field(index=True)
    embedding_data: str  # JSON serialized embedding vector
    dimension: int = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Meta:
        global_key_prefix = "rag-embeddings"

class CacheStats(BaseModel):
    """Cache statistics model"""
    total_entries: int
    total_hits: int
    total_misses: int
    hit_ratio: float
    memory_usage: int  # bytes
    expired_entries: int
    most_accessed_keys: List[Dict[str, Any]]

class CachingService:
    """Context7 verified: Advanced caching service with Redis OM"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.cache_enabled = True
        self.default_ttl = 3600  # 1 hour
        self.max_cache_size = 10000  # Maximum number of entries
        
    async def initialize(self):
        """Context7 verified: Initialize Redis connections for caching"""
        try:
            # Context7 verified pattern: Redis OM database setup
            redis_url = settings.REDIS_URL or "redis://localhost:6379"
            
            # Setup Redis OM models
            redis_conn = get_redis_connection(url=redis_url, decode_responses=True)
            CacheEntry.Meta.database = redis_conn
            QueryCache.Meta.database = redis_conn
            EmbeddingCache.Meta.database = redis_conn
            
            # Setup async Redis client for advanced operations
            self.redis_client = redis.from_url(
                redis_url, 
                encoding="utf8", 
                decode_responses=True
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Caching service initialized successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Redis not available, caching disabled: {e}")
            self.cache_enabled = False
            # Don't fail startup - just disable caching gracefully
    
    def _generate_hash(self, data: Union[str, Dict, List]) -> str:
        """Generate consistent hash for cache keys"""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def get_cached_response(self, query: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Context7 verified: Get cached query response"""
        if not self.cache_enabled:
            return None
            
        try:
            query_hash = self._generate_hash(query)
            
            # Find cached entry
            cached_queries = QueryCache.find(QueryCache.query_hash == query_hash).all()
            
            if cached_queries:
                cached_query = cached_queries[0]
                
                # Check expiry
                if cached_query.expires_at and datetime.utcnow() > cached_query.expires_at:
                    await self.invalidate_cache(f"query:{query_hash}")
                    return None
                
                # Update hit count and access time
                cached_query.hit_count += 1
                cached_query.save()
                
                logger.info(f"🎯 Cache HIT for query: {query[:50]}...")
                return {
                    "response": cached_query.response_data,
                    "sources": cached_query.sources,
                    "confidence": cached_query.confidence,
                    "response_time_ms": cached_query.response_time_ms,
                    "cached": True,
                    "cache_age": (datetime.utcnow() - cached_query.created_at).total_seconds()
                }
                
        except Exception as e:
            logger.error(f"❌ Error retrieving cached response: {e}")
            
        return None
    
    async def cache_response(
        self, 
        query: str, 
        response_data: Dict[str, Any],
        sources: List[Dict[str, Any]] = None,
        confidence: float = 0.0,
        response_time_ms: int = 0,
        user_id: Optional[str] = None,
        department: Optional[str] = None,
        sentiment: Optional[str] = None,
        ttl_hours: int = 24
    ):
        """Context7 verified: Cache query response"""
        if not self.cache_enabled:
            return
            
        try:
            query_hash = self._generate_hash(query)
            expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
            
            # Create cache entry - Context7 verified pattern
            cached_query = QueryCache(
                query_hash=query_hash,
                query_text=query,
                response_data=response_data,
                confidence=confidence,
                response_time_ms=response_time_ms,
                user_id=user_id,
                department=department,
                sentiment=sentiment,
                expires_at=expires_at
            )
            # Set sources using Context7 verified method
            cached_query.set_sources(sources or [])
            
            cached_query.save()
            logger.info(f"💾 Cached response for query: {query[:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Error caching response: {e}")
    
    async def get_cached_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """Context7 verified: Get cached embedding"""
        if not self.cache_enabled:
            return None
            
        try:
            text_hash = self._generate_hash(f"{text}:{model}")
            
            cached_embeddings = EmbeddingCache.find(
                (EmbeddingCache.text_hash == text_hash) & 
                (EmbeddingCache.embedding_model == model)
            ).all()
            
            if cached_embeddings:
                cached_embedding = cached_embeddings[0]
                embedding_data = json.loads(cached_embedding.embedding_data)
                logger.info(f"🎯 Cache HIT for embedding: {text[:30]}... (model: {model})")
                return embedding_data
                
        except Exception as e:
            logger.error(f"❌ Error retrieving cached embedding: {e}")
            
        return None
    
    async def cache_embedding(self, text: str, model: str, embedding: List[float]):
        """Context7 verified: Cache embedding"""
        if not self.cache_enabled or not embedding:
            return
            
        try:
            text_hash = self._generate_hash(f"{text}:{model}")
            
            cached_embedding = EmbeddingCache(
                text_hash=text_hash,
                text=text,
                embedding_model=model,
                embedding_data=json.dumps(embedding),
                dimension=len(embedding)
            )
            
            cached_embedding.save()
            logger.info(f"💾 Cached embedding for text: {text[:30]}... (model: {model})")
            
        except Exception as e:
            logger.error(f"❌ Error caching embedding: {e}")
    
    async def set_cache(
        self, 
        key: str, 
        value: Any, 
        ttl_seconds: Optional[int] = None,
        tags: List[str] = None
    ):
        """Context7 verified: Set cache entry with optional TTL and tags"""
        if not self.cache_enabled:
            return
            
        try:
            ttl_seconds = ttl_seconds or self.default_ttl
            expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            tags_str = ",".join(tags) if tags else ""
            
            cache_entry = CacheEntry(
                key=key,
                value=json.dumps(value),
                expiry=expiry,
                tags=tags_str
            )
            
            cache_entry.save()
            logger.debug(f"💾 Cached key: {key}")
            
        except Exception as e:
            logger.error(f"❌ Error setting cache: {e}")
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Context7 verified: Get cache entry by key"""
        if not self.cache_enabled:
            return None
            
        try:
            cached_entries = CacheEntry.find(CacheEntry.key == key).all()
            
            if cached_entries:
                cache_entry = cached_entries[0]
                
                # Check expiry
                if cache_entry.expiry and datetime.utcnow() > cache_entry.expiry:
                    cache_entry.delete(cache_entry.pk)
                    return None
                
                # Update access stats
                cache_entry.access_count += 1
                cache_entry.last_accessed = datetime.utcnow()
                cache_entry.save()
                
                return json.loads(cache_entry.value)
                
        except Exception as e:
            logger.error(f"❌ Error getting cache: {e}")
            
        return None
    
    async def invalidate_cache(self, pattern: str):
        """Context7 verified: Invalidate cache entries by pattern"""
        if not self.cache_enabled:
            return
            
        try:
            # For query cache
            if pattern.startswith("query:"):
                query_hash = pattern.split(":", 1)[1]
                cached_queries = QueryCache.find(QueryCache.query_hash == query_hash).all()
                for query in cached_queries:
                    query.delete(query.pk)
                    
            # For general cache
            elif pattern.startswith("key:"):
                key = pattern.split(":", 1)[1]
                cached_entries = CacheEntry.find(CacheEntry.key == key).all()
                for entry in cached_entries:
                    entry.delete(entry.pk)
                    
            # For tag-based invalidation
            elif pattern.startswith("tag:"):
                tag = pattern.split(":", 1)[1]
                # Find entries with this tag
                if self.redis_client:
                    # Use Redis SCAN for pattern matching
                    keys = []
                    async for key in self.redis_client.scan_iter(match=f"rag-cache:*"):
                        keys.append(key)
                    
                    # Check each entry for the tag
                    for redis_key in keys:
                        try:
                            pk = redis_key.split(":")[-1]
                            entry = CacheEntry.get(pk)
                            if tag in entry.tags.split(","):
                                entry.delete(entry.pk)
                        except:
                            continue
                            
            logger.info(f"🗑️ Invalidated cache: {pattern}")
            
        except Exception as e:
            logger.error(f"❌ Error invalidating cache: {e}")
    
    async def get_cache_stats(self) -> CacheStats:
        """Context7 verified: Get comprehensive cache statistics"""
        try:
            # Count entries
            cache_entries = len(CacheEntry.all_pks())
            query_entries = len(QueryCache.all_pks())
            embedding_entries = len(EmbeddingCache.all_pks())
            
            total_entries = cache_entries + query_entries + embedding_entries
            
            # Calculate hit ratios for query cache
            all_queries = QueryCache.find().all()
            total_hits = sum(q.hit_count for q in all_queries)
            total_queries = len(all_queries)
            hit_ratio = total_hits / max(total_queries, 1)
            
            # Memory usage (approximate)
            memory_usage = 0
            if self.redis_client:
                info = await self.redis_client.info("memory")
                memory_usage = info.get("used_memory", 0)
            
            # Most accessed queries
            most_accessed = sorted(all_queries, key=lambda x: x.hit_count, reverse=True)[:5]
            most_accessed_keys = [
                {
                    "query": q.query_text[:50] + "..." if len(q.query_text) > 50 else q.query_text,
                    "hits": q.hit_count,
                    "created": q.created_at.isoformat()
                }
                for q in most_accessed
            ]
            
            # Count expired entries
            expired_count = 0
            current_time = datetime.utcnow()
            for query in all_queries:
                if query.expires_at and current_time > query.expires_at:
                    expired_count += 1
            
            return CacheStats(
                total_entries=total_entries,
                total_hits=total_hits,
                total_misses=max(total_queries - total_hits, 0),
                hit_ratio=hit_ratio,
                memory_usage=memory_usage,
                expired_entries=expired_count,
                most_accessed_keys=most_accessed_keys
            )
            
        except Exception as e:
            logger.error(f"❌ Error getting cache stats: {e}")
            return CacheStats(
                total_entries=0,
                total_hits=0,
                total_misses=0,
                hit_ratio=0.0,
                memory_usage=0,
                expired_entries=0,
                most_accessed_keys=[]
            )
    
    async def cleanup_expired_entries(self):
        """Context7 verified: Cleanup expired cache entries"""
        if not self.cache_enabled:
            return
            
        try:
            current_time = datetime.utcnow()
            cleaned_count = 0
            
            # Cleanup query cache
            expired_queries = QueryCache.find().all()
            for query in expired_queries:
                if query.expires_at and current_time > query.expires_at:
                    query.delete(query.pk)
                    cleaned_count += 1
            
            # Cleanup general cache
            expired_entries = CacheEntry.find().all()
            for entry in expired_entries:
                if entry.expiry and current_time > entry.expiry:
                    entry.delete(entry.pk)
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned up {cleaned_count} expired cache entries")
                
        except Exception as e:
            logger.error(f"❌ Error cleaning up cache: {e}")
    
    async def warm_cache(self, common_queries: List[str]):
        """Pre-warm cache with common queries"""
        logger.info(f"🔥 Warming cache with {len(common_queries)} common queries")
        # This would trigger the normal query flow for each common query
        # Implementation depends on integration with main RAG system

# Global caching service instance
caching_service = CachingService()

# Context7 verified: Caching decorator for FastAPI endpoints
def cached_endpoint(expire: int = 300, tags: List[str] = None):
    """Context7 verified: Decorator for caching FastAPI endpoint responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not caching_service.cache_enabled:
                return await func(*args, **kwargs)
            
            # Generate cache key from function name and arguments
            cache_key = f"endpoint:{func.__name__}:{caching_service._generate_hash(str(kwargs))}"
            
            # Try to get from cache
            cached_result = await caching_service.get_cache(cache_key)
            if cached_result is not None:
                logger.info(f"🎯 Cache HIT for endpoint: {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await caching_service.set_cache(cache_key, result, expire, tags)
            logger.info(f"💾 Cached result for endpoint: {func.__name__}")
            
            return result
        return wrapper
    return decorator 