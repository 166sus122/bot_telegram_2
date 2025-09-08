#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cache Manager לבוט התמימים הפיראטים
מערכת מטמון מתקדמת עם TTL וניהול זיכרון
"""

import logging
import threading
import time
import json
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union
from collections import defaultdict, OrderedDict
import hashlib

logger = logging.getLogger(__name__)

class CacheEntry:
    """רשומת מטמון יחידה"""
    
    def __init__(self, key: str, value: Any, ttl: Optional[int] = None, 
                 tags: Optional[Set[str]] = None, metadata: Optional[Dict] = None):
        self.key = key
        self.value = value
        self.ttl = ttl
        self.tags = tags or set()
        self.metadata = metadata or {}
        
        self.created_at = datetime.now()
        self.expires_at = None
        if ttl:
            self.expires_at = self.created_at + timedelta(seconds=ttl)
        
        self.accessed_at = self.created_at
        self.access_count = 0
        self.size = self._calculate_size(value)
    
    def _calculate_size(self, value: Any) -> int:
        """חישוב גודל הערך בבתים"""
        try:
            return len(pickle.dumps(value))
        except:
            try:
                return len(str(value).encode('utf-8'))
            except:
                return 1024  # הערכה גסה
    
    def is_expired(self) -> bool:
        """בדיקה אם הרשומה פגה"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def update_access(self):
        """עדכון נתוני גישה"""
        self.accessed_at = datetime.now()
        self.access_count += 1
    
    def get_age_seconds(self) -> float:
        """גיל הרשומה בשניות"""
        return (datetime.now() - self.created_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """המרה למילון"""
        return {
            'key': self.key,
            'ttl': self.ttl,
            'tags': list(self.tags),
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'accessed_at': self.accessed_at.isoformat(),
            'access_count': self.access_count,
            'size': self.size,
            'age_seconds': self.get_age_seconds(),
            'is_expired': self.is_expired()
        }

class CacheManager:
    """מנהל מטמון מתקדם"""
    
    def __init__(self, default_ttl: int = 3600, max_memory_mb: int = 100):
        self.default_ttl = default_ttl
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        # אחסון ראשי
        self._cache: Dict[str, CacheEntry] = {}
        self._tags_index: Dict[str, Set[str]] = defaultdict(set)
        self._access_order = OrderedDict()
        
        # נעילה לthread safety
        self._lock = threading.RLock()
        
        # סטטיסטיקות
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'total_gets': 0,
            'total_sets': 0,
            'total_deletes': 0
        }
        
        # הגדרות ניהול זיכרון
        self.cleanup_threshold = 0.8  # 80% מהזיכרון
        self.cleanup_target = 0.6     # נקה עד 60%
        self.max_entries = 10000      # מספר מקסימלי של entries
        
        # הגדרות cleanup
        self.last_cleanup = datetime.now()
        self.cleanup_interval = 300   # 5 דקות
        
        logger.info(f"Cache Manager initialized: TTL={default_ttl}s, Memory={max_memory_mb}MB")
    
    # ========================= פעולות בסיסיות =========================
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            tags: Optional[Set[str]] = None, metadata: Optional[Dict] = None) -> bool:
        """שמירת ערך במטמון"""
        try:
            with self._lock:
                ttl = ttl or self.default_ttl
                
                # יצירת רשומה חדשה
                entry = CacheEntry(key, value, ttl, tags, metadata)
                
                # בדיקת זיכרון לפני הוספה
                if not self._has_space_for_entry(entry):
                    self._make_space_for_entry(entry)
                
                # הסרת רשומה קיימת אם יש
                if key in self._cache:
                    self._remove_entry(key)
                
                # הוספת רשומה חדשה
                self._cache[key] = entry
                self._access_order[key] = time.time()
                
                # עדכון אינדקס תגים
                if tags:
                    for tag in tags:
                        self._tags_index[tag].add(key)
                
                self._stats['total_sets'] += 1
                
                # cleanup תקופתי
                self._periodic_cleanup()
                
                return True
                
        except Exception as e:
            logger.error(f"Cache set failed for key '{key}': {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """קבלת ערך מהמטמון"""
        try:
            with self._lock:
                self._stats['total_gets'] += 1
                
                if key not in self._cache:
                    self._stats['misses'] += 1
                    return default
                
                entry = self._cache[key]
                
                # בדיקת תפוגה
                if entry.is_expired():
                    self._remove_entry(key)
                    self._stats['misses'] += 1
                    self._stats['expirations'] += 1
                    return default
                
                # עדכון גישה
                entry.update_access()
                self._access_order[key] = time.time()
                self._stats['hits'] += 1
                
                return entry.value
                
        except Exception as e:
            logger.error(f"Cache get failed for key '{key}': {e}")
            return default
    
    def delete(self, key: str) -> bool:
        """מחיקת ערך מהמטמון"""
        try:
            with self._lock:
                if key in self._cache:
                    self._remove_entry(key)
                    self._stats['total_deletes'] += 1
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache delete failed for key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """בדיקה אם ערך קיים"""
        try:
            with self._lock:
                if key not in self._cache:
                    return False
                
                entry = self._cache[key]
                if entry.is_expired():
                    self._remove_entry(key)
                    self._stats['expirations'] += 1
                    return False
                
                return True
                
        except Exception as e:
            logger.error(f"Cache exists check failed for key '{key}': {e}")
            return False
    
    def clear_all(self) -> int:
        """ניקוי כל המטמון"""
        try:
            with self._lock:
                count = len(self._cache)
                self._cache.clear()
                self._tags_index.clear()
                self._access_order.clear()
                
                logger.info(f"Cache cleared: {count} entries removed")
                return count
                
        except Exception as e:
            logger.error(f"Cache clear failed: {e}")
            return 0
    
    # ========================= פעולות מתקדמות =========================
    
    def set_with_tags(self, key: str, value: Any, tags: Set[str], 
                     ttl: Optional[int] = None, metadata: Optional[Dict] = None) -> bool:
        """שמירה עם תגים"""
        return self.set(key, value, ttl, tags, metadata)
    
    def invalidate_by_tag(self, tag: str) -> int:
        """מחיקת כל הרשומות עם תג מסוים"""
        try:
            with self._lock:
                if tag not in self._tags_index:
                    return 0
                
                keys_to_remove = list(self._tags_index[tag])
                count = 0
                
                for key in keys_to_remove:
                    if self.delete(key):
                        count += 1
                
                # ניקוי האינדקס
                del self._tags_index[tag]
                
                logger.info(f"Invalidated {count} entries with tag '{tag}'")
                return count
                
        except Exception as e:
            logger.error(f"Tag invalidation failed for tag '{tag}': {e}")
            return 0
    
    def get_or_set(self, key: str, callback: Callable[[], Any], 
                  ttl: Optional[int] = None, tags: Optional[Set[str]] = None) -> Any:
        """קבלה או יצירה עם callback"""
        try:
            # נסיון קבלה ראשון
            value = self.get(key)
            if value is not None:
                return value
            
            # ביצוע callback ושמירה
            with self._lock:
                # בדיקה נוספת בתוך הנעילה (double-checked locking)
                value = self.get(key)
                if value is not None:
                    return value
                
                # ביצוע callback
                try:
                    new_value = callback()
                    self.set(key, new_value, ttl, tags)
                    return new_value
                except Exception as e:
                    logger.error(f"Callback failed for key '{key}': {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"Get-or-set failed for key '{key}': {e}")
            raise
    
    def increment(self, key: str, amount: Union[int, float] = 1, 
                 initial_value: Union[int, float] = 0, ttl: Optional[int] = None) -> Union[int, float]:
        """הגדלת ערך מספרי"""
        try:
            with self._lock:
                current_value = self.get(key, initial_value)
                
                # וידוא שהערך מספרי
                if not isinstance(current_value, (int, float)):
                    current_value = initial_value
                
                new_value = current_value + amount
                self.set(key, new_value, ttl)
                
                return new_value
                
        except Exception as e:
            logger.error(f"Increment failed for key '{key}': {e}")
            raise
    
    def expire(self, key: str, seconds: int) -> bool:
        """הגדרת תפוגה לערך קיים"""
        try:
            with self._lock:
                if key not in self._cache:
                    return False
                
                entry = self._cache[key]
                entry.ttl = seconds
                entry.expires_at = datetime.now() + timedelta(seconds=seconds)
                
                return True
                
        except Exception as e:
            logger.error(f"Expire failed for key '{key}': {e}")
            return False
    
    # ========================= סטטיסטיקות וניטור =========================
    
    def get_stats(self) -> Dict[str, Any]:
        """קבלת סטטיסטיקות מטמון"""
        try:
            with self._lock:
                total_requests = self._stats['hits'] + self._stats['misses']
                hit_rate = (self._stats['hits'] / max(total_requests, 1)) * 100
                
                memory_usage = self._calculate_memory_usage()
                memory_usage_percent = (memory_usage / self.max_memory_bytes) * 100
                
                return {
                    'entries_count': len(self._cache),
                    'memory_usage_bytes': memory_usage,
                    'memory_usage_mb': round(memory_usage / (1024 * 1024), 2),
                    'memory_usage_percent': round(memory_usage_percent, 1),
                    'max_memory_mb': round(self.max_memory_bytes / (1024 * 1024), 1),
                    'hit_rate_percent': round(hit_rate, 1),
                    'stats': self._stats.copy(),
                    'tags_count': len(self._tags_index),
                    'expired_entries': self._count_expired_entries(),
                    'avg_entry_size': self._calculate_average_entry_size(),
                    'oldest_entry_age': self._get_oldest_entry_age(),
                    'most_accessed_key': self._get_most_accessed_key()
                }
                
        except Exception as e:
            logger.error(f"Get stats failed: {e}")
            return {}
    
    def get_hit_rate(self) -> float:
        """שיעור פגיעות במטמון"""
        total = self._stats['hits'] + self._stats['misses']
        return (self._stats['hits'] / max(total, 1)) * 100
    
    def get_memory_usage(self) -> Dict[str, Union[int, float]]:
        """שימוש בזיכרון"""
        try:
            with self._lock:
                total_bytes = self._calculate_memory_usage()
                return {
                    'used_bytes': total_bytes,
                    'used_mb': round(total_bytes / (1024 * 1024), 2),
                    'max_mb': round(self.max_memory_bytes / (1024 * 1024), 1),
                    'usage_percent': round((total_bytes / self.max_memory_bytes) * 100, 1),
                    'available_bytes': self.max_memory_bytes - total_bytes
                }
        except Exception as e:
            logger.error(f"Memory usage calculation failed: {e}")
            return {}
    
    def get_expired_keys(self) -> List[str]:
        """רשימת מפתחות שפגו"""
        try:
            with self._lock:
                expired_keys = []
                for key, entry in self._cache.items():
                    if entry.is_expired():
                        expired_keys.append(key)
                return expired_keys
        except Exception as e:
            logger.error(f"Get expired keys failed: {e}")
            return []
    
    # ========================= ניהול זיכרון =========================
    
    def cleanup_expired(self) -> int:
        """ניקוי רשומות שפגו"""
        try:
            with self._lock:
                expired_keys = self.get_expired_keys()
                count = 0
                
                for key in expired_keys:
                    if self.delete(key):
                        count += 1
                        self._stats['expirations'] += 1
                
                if count > 0:
                    logger.info(f"Cleaned up {count} expired entries")
                
                return count
                
        except Exception as e:
            logger.error(f"Cleanup expired failed: {e}")
            return 0
    
    def optimize_memory(self) -> Dict[str, int]:
        """אופטימיזציית זיכרון"""
        try:
            with self._lock:
                stats = {'expired': 0, 'evicted': 0}
                
                # ניקוי רשומות שפגו
                stats['expired'] = self.cleanup_expired()
                
                # בדיקת שימוש בזיכרון
                memory_usage = self._calculate_memory_usage()
                usage_ratio = memory_usage / self.max_memory_bytes
                
                if usage_ratio > self.cleanup_threshold:
                    stats['evicted'] = self._evict_lru_entries()
                
                logger.info(f"Memory optimization: {stats['expired']} expired, {stats['evicted']} evicted")
                return stats
                
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return {'expired': 0, 'evicted': 0}
    
    def set_memory_limit(self, limit_mb: int):
        """הגדרת מגבלת זיכרון"""
        try:
            with self._lock:
                old_limit = self.max_memory_bytes
                self.max_memory_bytes = limit_mb * 1024 * 1024
                
                logger.info(f"Memory limit changed: {old_limit / (1024*1024):.1f}MB -> {limit_mb}MB")
                
                # בדיקה אם צריך לנקות
                current_usage = self._calculate_memory_usage()
                if current_usage > self.max_memory_bytes:
                    self.optimize_memory()
                    
        except Exception as e:
            logger.error(f"Set memory limit failed: {e}")
    
    def get_largest_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """הרשומות הכי גדולות"""
        try:
            with self._lock:
                entries = []
                for key, entry in self._cache.items():
                    entries.append({
                        'key': key,
                        'size': entry.size,
                        'size_mb': round(entry.size / (1024 * 1024), 3),
                        'access_count': entry.access_count,
                        'age_minutes': round(entry.get_age_seconds() / 60, 1)
                    })
                
                # מיון לפי גודל
                entries.sort(key=lambda x: x['size'], reverse=True)
                return entries[:limit]
                
        except Exception as e:
            logger.error(f"Get largest entries failed: {e}")
            return []
    
    # ========================= פונקציות פרטיות =========================
    
    def _remove_entry(self, key: str):
        """הסרת רשומה מכל המבנים"""
        if key in self._cache:
            entry = self._cache[key]
            
            # הסרה מהמטמון הראשי
            del self._cache[key]
            
            # הסרה מסדר הגישה
            self._access_order.pop(key, None)
            
            # הסרה מאינדקס התגים
            for tag in entry.tags:
                if tag in self._tags_index:
                    self._tags_index[tag].discard(key)
                    if not self._tags_index[tag]:
                        del self._tags_index[tag]
    
    def _calculate_memory_usage(self) -> int:
        """חישוב שימוש כולל בזיכרון"""
        return sum(entry.size for entry in self._cache.values())
    
    def _has_space_for_entry(self, entry: CacheEntry) -> bool:
        """בדיקה אם יש מקום לרשומה"""
        current_usage = self._calculate_memory_usage()
        return (current_usage + entry.size) <= self.max_memory_bytes
    
    def _make_space_for_entry(self, new_entry: CacheEntry):
        """פינוי מקום לרשומה חדשה"""
        target_free = new_entry.size
        freed = 0
        
        # ראשית ניקוי רשומות שפגו
        expired_count = self.cleanup_expired()
        if expired_count > 0:
            current_usage = self._calculate_memory_usage()
            if (current_usage + new_entry.size) <= self.max_memory_bytes:
                return
        
        # אם עדיין אין מקום, evict לפי LRU
        freed += self._evict_lru_entries(target_free)
        
        if freed < target_free:
            logger.warning(f"Could not free enough space: needed {target_free}, freed {freed}")
    
    def _evict_lru_entries(self, target_bytes: Optional[int] = None) -> int:
        """פינוי רשומות לפי LRU"""
        try:
            if not target_bytes:
                # פינוי עד היעד הכללי
                current_usage = self._calculate_memory_usage()
                target_usage = self.max_memory_bytes * self.cleanup_target
                target_bytes = current_usage - target_usage
            
            if target_bytes <= 0:
                return 0
            
            # מיון לפי זמן גישה אחרון
            sorted_keys = sorted(self._access_order.items(), key=lambda x: x[1])
            
            freed_bytes = 0
            evicted_count = 0
            
            for key, _ in sorted_keys:
                if key in self._cache:
                    entry_size = self._cache[key].size
                    self._remove_entry(key)
                    freed_bytes += entry_size
                    evicted_count += 1
                    self._stats['evictions'] += 1
                    
                    if freed_bytes >= target_bytes:
                        break
            
            logger.info(f"Evicted {evicted_count} LRU entries, freed {freed_bytes} bytes")
            return freed_bytes
            
        except Exception as e:
            logger.error(f"LRU eviction failed: {e}")
            return 0
    
    def _periodic_cleanup(self):
        """ניקוי תקופתי"""
        now = datetime.now()
        if (now - self.last_cleanup).total_seconds() > self.cleanup_interval:
            self.cleanup_expired()
            self.last_cleanup = now
    
    def _count_expired_entries(self) -> int:
        """ספירת רשומות שפגו"""
        try:
            return len([1 for entry in self._cache.values() if entry.is_expired()])
        except:
            return 0
    
    def _calculate_average_entry_size(self) -> float:
        """גודל ממוצע של רשומה"""
        try:
            if not self._cache:
                return 0.0
            total_size = sum(entry.size for entry in self._cache.values())
            return total_size / len(self._cache)
        except:
            return 0.0
    
    def _get_oldest_entry_age(self) -> float:
        """גיל הרשומה הכי ישנה בדקות"""
        try:
            if not self._cache:
                return 0.0
            oldest_entry = min(self._cache.values(), key=lambda e: e.created_at)
            return oldest_entry.get_age_seconds() / 60
        except:
            return 0.0
    
    def _get_most_accessed_key(self) -> Optional[str]:
        """המפתח הכי פופולרי"""
        try:
            if not self._cache:
                return None
            most_accessed = max(self._cache.values(), key=lambda e: e.access_count)
            return most_accessed.key
        except:
            return None


# ========================= דקורטורים למטמון =========================

def cache_result(ttl: int = 3600, key_prefix: str = '', tags: Optional[Set[str]] = None):
    """דקורטור למטמון תוצאות פונקציה"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # יצירת מפתח מטמון
            cache_key = _generate_function_cache_key(func, args, kwargs, key_prefix)
            
            # ניסיון קבלה מהמטמון
            cache_manager = _get_global_cache_manager()
            if cache_manager:
                cached_result = cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            # ביצוע הפונקציה ושמירה במטמון
            result = func(*args, **kwargs)
            
            if cache_manager and result is not None:
                cache_manager.set(cache_key, result, ttl, tags)
            
            return result
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper._cache_enabled = True
        wrapper._cache_ttl = ttl
        wrapper._cache_prefix = key_prefix
        
        return wrapper
    return decorator

def invalidate_cache(tags: Union[str, Set[str]]):
    """דקורטור למחיקת מטמון לפי תגים"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # מחיקת מטמון
            cache_manager = _get_global_cache_manager()
            if cache_manager:
                if isinstance(tags, str):
                    cache_manager.invalidate_by_tag(tags)
                else:
                    for tag in tags:
                        cache_manager.invalidate_by_tag(tag)
            
            return result
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper._invalidates_tags = tags
        
        return wrapper
    return decorator

def cached_property(ttl: int = 3600):
    """דקורטור לcached property"""
    def decorator(func: Callable) -> property:
        def wrapper(self):
            cache_key = f"{self.__class__.__name__}:{id(self)}:{func.__name__}"
            
            cache_manager = _get_global_cache_manager()
            if cache_manager:
                cached_result = cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            result = func(self)
            
            if cache_manager and result is not None:
                cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return property(wrapper)
    return decorator

# ========================= פונקציות עזר למטמון =========================

def _generate_function_cache_key(func: Callable, args: tuple, kwargs: dict, 
                                prefix: str = '') -> str:
    """יצירת מפתח מטמון לפונקציה"""
    try:
        # יצירת hash מהארגומנטים
        args_str = str(args) + str(sorted(kwargs.items()))
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:12]
        
        # בניית המפתח
        func_name = f"{func.__module__}.{func.__qualname__}"
        cache_key = f"{prefix}:{func_name}:{args_hash}" if prefix else f"{func_name}:{args_hash}"
        
        return cache_key
    except Exception as e:
        logger.error(f"Cache key generation failed: {e}")
        return f"error_key_{time.time()}"

# ========================= מנהל מטמון גלובלי =========================

_global_cache_manager: Optional[CacheManager] = None

def get_global_cache_manager() -> Optional[CacheManager]:
    """קבלת מנהל המטמון הגלובלי"""
    return _global_cache_manager

def _get_global_cache_manager() -> Optional[CacheManager]:
    """פונקציה פרטית לקבלת מנהל המטמון"""
    return _global_cache_manager

def init_global_cache_manager(default_ttl: int = 3600, max_memory_mb: int = 100) -> CacheManager:
    """אתחול מנהל מטמון גלובלי"""
    global _global_cache_manager
    
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager(default_ttl, max_memory_mb)
        logger.info("Global cache manager initialized")
    
    return _global_cache_manager

def shutdown_global_cache_manager():
    """כיבוי מנהל המטמון הגלובלי"""
    global _global_cache_manager
    
    if _global_cache_manager:
        stats = _global_cache_manager.get_stats()
        _global_cache_manager.clear_all()
        _global_cache_manager = None
        logger.info(f"Global cache manager shutdown. Final stats: {stats}")

# ========================= כלי debug ואבחון =========================

def cache_debug_info(key_pattern: str = None) -> Dict[str, Any]:
    """מידע debug על המטמון"""
    try:
        cache_manager = get_global_cache_manager()
        if not cache_manager:
            return {'error': 'No global cache manager'}
        
        with cache_manager._lock:
            debug_info = {
                'general_stats': cache_manager.get_stats(),
                'memory_info': cache_manager.get_memory_usage(),
                'largest_entries': cache_manager.get_largest_entries(5),
                'expired_keys_count': len(cache_manager.get_expired_keys())
            }
            
            # מידע על מפתחות ספציפיים
            if key_pattern:
                matching_keys = []
                for key, entry in cache_manager._cache.items():
                    if key_pattern in key:
                        matching_keys.append({
                            'key': key,
                            'info': entry.to_dict()
                        })
                debug_info['matching_keys'] = matching_keys[:10]  # רק 10 הראשונים
            
            return debug_info
            
    except Exception as e:
        logger.error(f"Cache debug info failed: {e}")
        return {'error': str(e)}

def analyze_cache_performance() -> Dict[str, Any]:
    """ניתוח ביצועי המטמון"""
    try:
        cache_manager = get_global_cache_manager()
        if not cache_manager:
            return {'error': 'No global cache manager'}
        
        stats = cache_manager.get_stats()
        memory_info = cache_manager.get_memory_usage()
        
        analysis = {
            'performance_grade': 'unknown',
            'recommendations': [],
            'metrics': {
                'hit_rate': stats.get('hit_rate_percent', 0),
                'memory_efficiency': 0,
                'expiration_rate': 0
            }
        }
        
        # ניתוח hit rate
        hit_rate = stats.get('hit_rate_percent', 0)
        if hit_rate >= 80:
            analysis['performance_grade'] = 'excellent'
        elif hit_rate >= 60:
            analysis['performance_grade'] = 'good'
        elif hit_rate >= 40:
            analysis['performance_grade'] = 'fair'
        else:
            analysis['performance_grade'] = 'poor'
            analysis['recommendations'].append('Consider reviewing cache keys and TTL settings')
        
        # ניתוח זיכרון
        memory_usage = memory_info.get('usage_percent', 0)
        if memory_usage > 90:
            analysis['recommendations'].append('Memory usage is very high - consider increasing limit or reducing TTL')
        elif memory_usage > 70:
            analysis['recommendations'].append('Monitor memory usage - approaching limit')
        
        analysis['metrics']['memory_efficiency'] = min(100, (hit_rate * (100 - memory_usage)) / 100)
        
        # ניתוח תפוגות
        total_operations = stats.get('stats', {}).get('hits', 0) + stats.get('stats', {}).get('misses', 0)
        expirations = stats.get('stats', {}).get('expirations', 0)
        
        if total_operations > 0:
            expiration_rate = (expirations / total_operations) * 100
            analysis['metrics']['expiration_rate'] = expiration_rate
            
            if expiration_rate > 30:
                analysis['recommendations'].append('High expiration rate - consider longer TTL values')
        
        # המלצות כלליות
        if stats.get('entries_count', 0) == 0:
            analysis['recommendations'].append('Cache is empty - verify cache usage')
        
        expired_count = stats.get('expired_entries', 0)
        if expired_count > stats.get('entries_count', 0) * 0.2:
            analysis['recommendations'].append('Many expired entries - run cleanup more frequently')
        
        return analysis
        
    except Exception as e:
        logger.error(f"Cache performance analysis failed: {e}")
        return {'error': str(e)}

def cache_health_check() -> Dict[str, Any]:
    """בדיקת תקינות המטמון"""
    try:
        cache_manager = get_global_cache_manager()
        if not cache_manager:
            return {
                'healthy': False,
                'issues': ['No global cache manager initialized']
            }
        
        health = {
            'healthy': True,
            'issues': [],
            'warnings': []
        }
        
        stats = cache_manager.get_stats()
        
        # בדיקות קריטיות
        if stats.get('entries_count', 0) > cache_manager.max_entries:
            health['healthy'] = False
            health['issues'].append('Exceeded maximum entries limit')
        
        memory_percent = stats.get('memory_usage_percent', 0)
        if memory_percent > 95:
            health['healthy'] = False
            health['issues'].append('Memory usage critically high')
        elif memory_percent > 85:
            health['warnings'].append('Memory usage high')
        
        # בדיקת hit rate
        hit_rate = stats.get('hit_rate_percent', 0)
        if hit_rate < 20:
            health['warnings'].append('Very low hit rate - cache may not be effective')
        
        # בדיקת תפוגות
        expired_count = stats.get('expired_entries', 0)
        total_count = stats.get('entries_count', 0)
        
        if total_count > 0 and expired_count / total_count > 0.5:
            health['warnings'].append('High ratio of expired entries')
        
        return health
        
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            'healthy': False,
            'issues': [f'Health check error: {e}']
        }