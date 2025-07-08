"""Redis-based caching system for MadSpark workflow results and agent responses."""

import json
import hashlib
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for cache manager."""
    redis_url: str = "redis://localhost:6379/0"
    ttl_seconds: int = 3600  # 1 hour default
    max_cache_size_mb: int = 100
    enable_agent_caching: bool = True
    enable_workflow_caching: bool = True
    key_prefix: str = "madspark"


class CacheManager:
    """Manages Redis-based caching for MadSpark workflows and agent responses."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize cache manager with configuration.
        
        Args:
            config: Cache configuration. Uses defaults if not provided.
        """
        self.config = config or CacheConfig()
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Caching disabled.")
    
    async def initialize(self) -> bool:
        """Initialize Redis connection.
        
        Returns:
            True if connection successful, False otherwise.
        """
        if not REDIS_AVAILABLE:
            return False
            
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("Redis cache initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self.is_connected = False
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
    
    def _generate_cache_key(self, theme: str, constraints: str, options: Dict[str, Any]) -> str:
        """Generate a unique cache key for given inputs.
        
        Args:
            theme: Idea generation theme
            constraints: Constraints for ideas
            options: Additional options (temperature, mode, etc.)
            
        Returns:
            Cache key string
        """
        # Sort options for consistent key generation
        sorted_options = json.dumps(options, sort_keys=True)
        key_parts = [theme, constraints, sorted_options]
        key_string = "|".join(key_parts)
        
        # Create hash for compact key
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        return f"{self.config.key_prefix}:workflow:{key_hash}"
    
    def _generate_agent_key(self, agent_name: str, prompt: str) -> str:
        """Generate cache key for agent response.
        
        Args:
            agent_name: Name of the agent
            prompt: Agent prompt
            
        Returns:
            Cache key string
        """
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        return f"{self.config.key_prefix}:agent:{agent_name}:{prompt_hash}"
    
    async def cache_workflow_result(
        self, 
        theme: str, 
        constraints: str, 
        options: Dict[str, Any], 
        result: Dict[str, Any]
    ) -> bool:
        """Cache a complete workflow result.
        
        Args:
            theme: Idea generation theme
            constraints: Constraints for ideas
            options: Workflow options
            result: Complete workflow result
            
        Returns:
            True if cached successfully
        """
        if not self.is_connected or not self.config.enable_workflow_caching:
            return False
            
        try:
            key = self._generate_cache_key(theme, constraints, options)
            
            # Add metadata
            cache_data = {
                "result": result,
                "cached_at": datetime.now().isoformat(),
                "theme": theme,
                "constraints": constraints,
                "options": options
            }
            
            await self.redis_client.setex(
                key,
                self.config.ttl_seconds,
                json.dumps(cache_data)
            )
            
            # Check cache size limit
            await self._enforce_size_limit()
            
            logger.debug(f"Cached workflow result: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache workflow result: {e}")
            return False
    
    async def get_cached_workflow(
        self, 
        theme: str, 
        constraints: str, 
        options: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached workflow result.
        
        Args:
            theme: Idea generation theme
            constraints: Constraints for ideas
            options: Workflow options
            
        Returns:
            Cached result if found, None otherwise
        """
        if not self.is_connected or not self.config.enable_workflow_caching:
            return None
            
        try:
            key = self._generate_cache_key(theme, constraints, options)
            cached_data = await self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Cache hit for workflow: {key}")
                return data["result"]
            
            logger.debug(f"Cache miss for workflow: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached workflow: {e}")
            return None
    
    async def cache_agent_response(
        self, 
        agent_name: str, 
        prompt: str, 
        response: Any,
        ttl_override: Optional[int] = None
    ) -> bool:
        """Cache an individual agent response.
        
        Args:
            agent_name: Name of the agent
            prompt: Agent prompt
            response: Agent response
            ttl_override: Optional TTL override in seconds
            
        Returns:
            True if cached successfully
        """
        if not self.is_connected or not self.config.enable_agent_caching:
            return False
            
        try:
            key = self._generate_agent_key(agent_name, prompt)
            ttl = ttl_override or self.config.ttl_seconds
            
            cache_data = {
                "response": response,
                "cached_at": datetime.now().isoformat(),
                "agent": agent_name
            }
            
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(cache_data)
            )
            
            logger.debug(f"Cached agent response: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache agent response: {e}")
            return False
    
    async def get_cached_agent_response(
        self, 
        agent_name: str, 
        prompt: str
    ) -> Optional[Any]:
        """Retrieve cached agent response.
        
        Args:
            agent_name: Name of the agent
            prompt: Agent prompt
            
        Returns:
            Cached response if found, None otherwise
        """
        if not self.is_connected or not self.config.enable_agent_caching:
            return None
            
        try:
            key = self._generate_agent_key(agent_name, prompt)
            cached_data = await self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Cache hit for agent: {key}")
                return data["response"]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached agent response: {e}")
            return None
    
    async def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries matching pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "*workflow*")
            
        Returns:
            Number of keys deleted
        """
        if not self.is_connected:
            return 0
            
        try:
            if pattern:
                # Add prefix to pattern
                full_pattern = f"{self.config.key_prefix}:{pattern}"
                
                # Use SCAN instead of KEYS for better performance
                deleted_count = 0
                keys_to_delete = []
                
                async for key in self.redis_client.scan_iter(match=full_pattern):
                    keys_to_delete.append(key)
                    
                    # Delete in batches of 100 for efficiency
                    if len(keys_to_delete) >= 100:
                        deleted_count += await self.redis_client.delete(*keys_to_delete)
                        keys_to_delete = []
                
                # Delete remaining keys
                if keys_to_delete:
                    deleted_count += await self.redis_client.delete(*keys_to_delete)
                    
                logger.info(f"Invalidated {deleted_count} cache entries")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache: {e}")
            return 0
    
    async def clear_all_cache(self) -> bool:
        """Clear all cache entries.
        
        Returns:
            True if cleared successfully
        """
        if not self.is_connected:
            return False
            
        try:
            await self.redis_client.flushdb()
            logger.info("Cleared all cache entries")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.is_connected:
            return {"status": "disconnected"}
            
        try:
            info = await self.redis_client.info()
            db_size = await self.redis_client.dbsize()
            
            # Get pattern counts
            # Count workflow keys using SCAN
            workflow_count = 0
            async for _ in self.redis_client.scan_iter(match=f"{self.config.key_prefix}:workflow:*"):
                workflow_count += 1
                
            # Count agent keys using SCAN
            agent_count = 0
            async for _ in self.redis_client.scan_iter(match=f"{self.config.key_prefix}:agent:*"):
                agent_count += 1
            
            return {
                "status": "connected",
                "memory_used": info.get("used_memory_human", "0"),
                "total_keys": db_size,
                "workflow_keys": workflow_count,
                "agent_keys": agent_count,
                "connected_clients": info.get("connected_clients", 0),
                "hit_rate": self._calculate_hit_rate(info),
                "config": asdict(self.config)
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """Calculate cache hit rate from Redis info.
        
        Args:
            info: Redis info dictionary
            
        Returns:
            Hit rate as percentage
        """
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
            
        return (hits / total) * 100
    
    async def _enforce_size_limit(self):
        """Enforce cache size limit using LRU-based eviction strategy."""
        if not self.is_connected:
            return
            
        try:
            info = await self.redis_client.info()
            used_memory_mb = info.get("used_memory", 0) / (1024 * 1024)
            
            if used_memory_mb > self.config.max_cache_size_mb:
                # Use Redis SCAN for memory-efficient iteration
                pattern = f"{self.config.key_prefix}:*"
                cursor = 0
                keys_to_check = []
                
                # Scan keys in batches to avoid memory overload
                while True:
                    cursor, batch_keys = await self.redis_client.scan(
                        cursor, match=pattern, count=100
                    )
                    keys_to_check.extend(batch_keys)
                    
                    # Limit to checking first 1000 keys for efficiency
                    if cursor == 0 or len(keys_to_check) >= 1000:
                        break
                
                if not keys_to_check:
                    return
                
                # Get access times using pipeline for efficiency
                pipe = self.redis_client.pipeline()
                for key in keys_to_check:
                    pipe.object("idletime", key)
                
                idle_times = await pipe.execute()
                
                # Create list of (key, idle_time) tuples
                key_idle_pairs = [
                    (key, idle_time) 
                    for key, idle_time in zip(keys_to_check, idle_times)
                    if idle_time is not None
                ]
                
                # Sort by idle time (descending) - longest idle first
                key_idle_pairs.sort(key=lambda x: x[1], reverse=True)
                
                # Delete 10% of least recently used keys
                to_delete = max(1, len(key_idle_pairs) // 10)
                
                # Use pipeline for batch deletion
                pipe = self.redis_client.pipeline()
                for key, idle_time in key_idle_pairs[:to_delete]:
                    pipe.delete(key)
                await pipe.execute()
                
                logger.info(
                    f"Enforced size limit: deleted {to_delete} LRU keys "
                    f"(oldest idle: {key_idle_pairs[0][1] if key_idle_pairs else 0}s)"
                )
                
        except Exception as e:
            logger.error(f"Failed to enforce size limit: {e}")
    
    async def warm_cache(self, common_queries: List[Tuple[str, str]]) -> int:
        """Pre-populate cache with common queries.
        
        Args:
            common_queries: List of (theme, constraints) tuples
            
        Returns:
            Number of entries warmed
        """
        if not self.is_connected:
            return 0
            
        warmed = 0
        for theme, constraints in common_queries:
            # Generate synthetic result for warming
            # In production, this would call the actual workflow
            synthetic_result = {
                "candidates": [],
                "warmed": True,
                "timestamp": datetime.now().isoformat()
            }
            
            success = await self.cache_workflow_result(
                theme, 
                constraints, 
                {"temperature": 0.7},  # Default options
                synthetic_result
            )
            
            if success:
                warmed += 1
        
        logger.info(f"Warmed cache with {warmed} entries")
        return warmed
    
    async def batch_get(self, keys: List[str]) -> List[Optional[Dict[str, Any]]]:
        """Batch get multiple cache entries.
        
        Args:
            keys: List of cache keys
            
        Returns:
            List of cached values (None for misses)
        """
        if not self.is_connected:
            return [None] * len(keys)
            
        try:
            values = await self.redis_client.mget(keys)
            results = []
            
            for value in values:
                if value:
                    try:
                        data = json.loads(value)
                        results.append(data.get("result") or data.get("response"))
                    except json.JSONDecodeError:
                        results.append(None)
                else:
                    results.append(None)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to batch get: {e}")
            return [None] * len(keys)