#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Connection Pool Manager לבוט התמימים הפיראטים
ניהול חיבורי MySQL יעיל עם pooling מתקדם
"""

import logging
import threading
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any, Tuple
import os

try:
    import mysql.connector
    from mysql.connector import Error, pooling
    from mysql.connector.pooling import MySQLConnectionPool
except ImportError:
    print("⚠️ mysql-connector-python לא מותקן. התקן עם: pip install mysql-connector-python")
    mysql = None

logger = logging.getLogger(__name__)

class DatabaseConnectionPool:
    """מנהל Connection Pool מתקדם למסד נתונים"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        אתחול Connection Pool
        
        Args:
            config: הגדרות מסד נתונים וPool
        """
        self.config = config.copy()
        self.pool: Optional[MySQLConnectionPool] = None
        self._lock = threading.RLock()
        self._pool_stats = {
            'created_connections': 0,
            'active_connections': 0,
            'failed_connections': 0,
            'total_queries': 0,
            'failed_queries': 0,
            'pool_hits': 0,
            'pool_misses': 0
        }
        
        # הגדרות ברירת מחדל
        self.pool_config = {
            'pool_name': config.get('pool_name', 'pirate_pool'),
            'pool_size': config.get('pool_size', 10),
            'pool_reset_session': config.get('pool_reset_session', True)
        }
        
        # פרמטרים תקינים עבור mysql.connector
        valid_mysql_params = {
            'host', 'port', 'user', 'password', 'database', 'charset', 'collation',
            'autocommit', 'raise_on_warnings', 'use_unicode', 'buffered',
            'connection_timeout', 'sql_mode'
        }
        
        # הסרת הגדרות pool ופרמטרים לא תקינים מהגדרות החיבור
        self.db_config = {k: v for k, v in config.items() if k in valid_mysql_params}
        
        logger.info(f"Connection Pool initialized: {self.pool_config['pool_name']}")
    
    def create_pool(self) -> bool:
        """יצירת Connection Pool"""
        if mysql is None:
            logger.error("MySQL connector not available")
            return False
        
        with self._lock:
            if self.pool is not None:
                logger.warning("Pool already exists")
                return True
            
            try:
                # מיזוג הגדרות
                pool_config = {**self.db_config, **self.pool_config}
                
                # לוג pool config בלי מידע רגיש 
                safe_pool_config = {k: ("***" if k in ["password", "passwd", "token", "secret", "key"] else v) 
                                   for k, v in self.pool_config.items()}
                logger.info(f"Creating connection pool with config: {safe_pool_config}")
                self.pool = mysql.connector.pooling.MySQLConnectionPool(**pool_config)
                
                # בדיקת חיבור ראשוני
                test_conn = self.pool.get_connection()
                if test_conn:
                    test_conn.close()
                    logger.info(f"Connection pool created successfully: {self.pool_config['pool_name']}")
                    return True
                
            except Exception as e:
                logger.error(f"Failed to create connection pool: {e}")
                self.pool = None
                return False
        
        return False
    
    @contextmanager
    def get_connection(self):
        """
        Context manager לקבלת חיבור מה-pool
        
        Usage:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                # ... use connection
        """
        connection = None
        try:
            connection = self._get_connection_from_pool()
            if connection is None:
                raise Exception("Failed to get connection from pool")
                
            self._pool_stats['pool_hits'] += 1
            yield connection
            
        except Exception as e:
            self._pool_stats['failed_connections'] += 1
            logger.error(f"Connection error: {e}")
            if connection:
                try:
                    connection.rollback()
                except Exception:
                    pass
            raise
        finally:
            if connection:
                try:
                    connection.close()  # מחזיר לpool
                except Exception:
                    pass
    
    def _get_connection_from_pool(self):
        """קבלת חיבור מה-pool עם error handling ו-timeout"""
        if self.pool is None:
            if not self.create_pool():
                return None
        
        try:
            # קבלת חיבור
            connection = self.pool.get_connection()
            
            # validation של החיבור
            if not self._validate_connection(connection):
                logger.warning("Connection validation failed, attempting to reconnect")
                try:
                    connection.reconnect(attempts=2, delay=1)
                    if not self._validate_connection(connection):
                        connection.close()
                        return None
                except Exception as reconnect_error:
                    logger.error(f"Reconnection failed: {reconnect_error}")
                    try:
                        connection.close()
                    except:
                        pass
                    return None
            
            return connection
            
        except mysql.connector.errors.PoolError as pool_error:
            logger.error(f"Pool error getting connection: {pool_error}")
            self._pool_stats['pool_misses'] += 1
            return None
        except Exception as e:
            logger.error(f"Error getting connection from pool: {e}")
            # נסיון ליצור pool חדש
            self.pool = None
            if self.create_pool():
                try:
                    return self.pool.get_connection(timeout=self.pool_config.get('pool_timeout', 5))
                except Exception:
                    pass
            return None
    
    def _validate_connection(self, connection) -> bool:
        """בדיקת תקינות חיבור"""
        if not connection:
            return False
            
        try:
            if not connection.is_connected():
                connection.reconnect(attempts=3, delay=1)
            
            # בדיקה פשוטה
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            
            return result is not None
            
        except Exception as e:
            logger.warning(f"Connection validation failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Tuple] = None, 
                     fetch_one: bool = False, fetch_all: bool = False) -> Any:
        """
        ביצוע query עם connection מה-pool
        
        Args:
            query: SQL query
            params: פרמטרים לquery
            fetch_one: האם להחזיר רשומה אחת
            fetch_all: האם להחזיר כל הרשומות
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                
                cursor.execute(query, params or ())
                self._pool_stats['total_queries'] += 1
                
                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                else:
                    result = cursor.rowcount
                
                cursor.close()
                
                # commit אוטומטי אם לא autocommit
                if not conn.autocommit:
                    conn.commit()
                
                return result
                
        except Exception as e:
            self._pool_stats['failed_queries'] += 1
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def execute_many(self, query: str, params_list: list) -> int:
        """ביצוע batch queries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.executemany(query, params_list)
                self._pool_stats['total_queries'] += len(params_list)
                
                affected_rows = cursor.rowcount
                cursor.close()
                
                if not conn.autocommit:
                    conn.commit()
                
                return affected_rows
                
        except Exception as e:
            self._pool_stats['failed_queries'] += len(params_list)
            logger.error(f"Batch execution failed: {e}")
            raise
    
    def execute_transaction(self, queries: list) -> bool:
        """
        ביצוע מספר queries בtransaction אחד
        
        Args:
            queries: רשימה של (query, params) tuples
        """
        try:
            with self.get_connection() as conn:
                conn.autocommit = False
                cursor = conn.cursor()
                
                try:
                    for query, params in queries:
                        cursor.execute(query, params or ())
                        self._pool_stats['total_queries'] += 1
                    
                    conn.commit()
                    cursor.close()
                    return True
                    
                except Exception as e:
                    conn.rollback()
                    cursor.close()
                    raise e
                
        except Exception as e:
            self._pool_stats['failed_queries'] += len(queries)
            logger.error(f"Transaction failed: {e}")
            return False
    
    def get_pool_status(self) -> Dict[str, Any]:
        """קבלת סטטוס Pool"""
        if self.pool is None:
            return {
                'pool_exists': False,
                'pool_name': self.pool_config['pool_name'],
                'status': 'not_created'
            }
        
        try:
            # נסיון לקבל מידע על Pool
            return {
                'pool_exists': True,
                'pool_name': self.pool_config['pool_name'],
                'pool_size': self.pool_config['pool_size'],
                'status': 'active',
                'stats': self._pool_stats.copy()
            }
            
        except Exception as e:
            return {
                'pool_exists': True,
                'status': f'error: {e}',
                'stats': self._pool_stats.copy()
            }
    
    def close_all_connections(self):
        """סגירת כל החיבורים וה-pool"""
        with self._lock:
            if self.pool:
                try:
                    # אין API ישיר לסגירת pool, אבל זה יקרה אוטומטית
                    logger.info(f"Closing connection pool: {self.pool_config['pool_name']}")
                    self.pool = None
                except Exception as e:
                    logger.error(f"Error closing pool: {e}")
    
    def health_check(self) -> bool:
        """בדיקת תקינות Pool"""
        try:
            with self.get_connection() as conn:
                if not conn or not conn.is_connected():
                    return False
                
                cursor = conn.cursor()
                cursor.execute("SELECT 1 as health_check")
                result = cursor.fetchone()
                cursor.close()
                
                return result is not None
                
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """קבלת מדדי ביצועים"""
        stats = self._pool_stats.copy()
        
        # חישוב מדדים נוספים
        total_connections = stats['created_connections']
        success_rate = ((stats['total_queries'] - stats['failed_queries']) / 
                       max(stats['total_queries'], 1)) * 100
        
        pool_hit_rate = (stats['pool_hits'] / 
                        max(stats['pool_hits'] + stats['pool_misses'], 1)) * 100
        
        return {
            **stats,
            'success_rate': round(success_rate, 2),
            'pool_hit_rate': round(pool_hit_rate, 2),
            'pool_config': self.pool_config
        }
    
    def reset_stats(self):
        """איפוס סטטיסטיקות"""
        with self._lock:
            self._pool_stats = {
                'created_connections': 0,
                'active_connections': 0,
                'failed_connections': 0,
                'total_queries': 0,
                'failed_queries': 0,
                'pool_hits': 0,
                'pool_misses': 0
            }
        logger.info("Pool statistics reset")


# ========================= פונקציות עזר גלובליות =========================

# Instance גלובלי של Pool
_global_pool: Optional[DatabaseConnectionPool] = None
_pool_lock = threading.RLock()

def create_global_pool(config: Dict[str, Any]) -> DatabaseConnectionPool:
    """יצירת Pool גלובלי"""
    global _global_pool
    
    with _pool_lock:
        if _global_pool is None:
            _global_pool = DatabaseConnectionPool(config)
            _global_pool.create_pool()
        
        return _global_pool

def get_global_pool() -> Optional[DatabaseConnectionPool]:
    """קבלת Pool גלובלי"""
    return _global_pool

def close_global_pool():
    """סגירת Pool גלובלי"""
    global _global_pool
    
    with _pool_lock:
        if _global_pool:
            _global_pool.close_all_connections()
            _global_pool = None

@contextmanager
def get_db_connection():
    """Context manager לחיבור מהPool הגלובלי"""
    pool = get_global_pool()
    if not pool:
        raise Exception("Global pool not initialized")
    
    with pool.get_connection() as conn:
        yield conn

def execute_query(query: str, params: Optional[Tuple] = None, **kwargs) -> Any:
    """ביצוע query עם Pool גלובלי"""
    pool = get_global_pool()
    if not pool:
        raise Exception("Global pool not initialized")
    
    return pool.execute_query(query, params, **kwargs)

def execute_many(query: str, params_list: list) -> int:
    """ביצוע batch queries עם Pool גלובלי"""
    pool = get_global_pool()
    if not pool:
        raise Exception("Global pool not initialized")
    
    return pool.execute_many(query, params_list)

def execute_transaction(queries: list) -> bool:
    """ביצוע transaction עם Pool גלובלי"""
    pool = get_global_pool()
    if not pool:
        raise Exception("Global pool not initialized")
    
    return pool.execute_transaction(queries)