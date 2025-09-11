"""
מנהל אחסון לבוט התמימים הפיראטים - עודכן
תומך במצב מטמון (זיכרון) או מסד נתונים MySQL עם Connection Pool
"""

import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional

# יבוא המודולים החדשים
try:
    from pirate_content_bot.database.connection_pool import create_global_pool, get_global_pool
    from pirate_content_bot.database.models import RequestModel, UserModel, RatingModel, get_all_models
    from pirate_content_bot.database.migrations import run_initial_setup
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

from pirate_content_bot.main.config import USE_DATABASE, DB_CONFIG

# יבוא MySQL רק אם נדרש
if USE_DATABASE and DATABASE_AVAILABLE:
    try:
        import mysql.connector
        from mysql.connector import Error, pooling
    except ImportError:
        print("⚠️ mysql-connector-python לא מותקן, משתמש במצב מטמון")
        USE_DATABASE = False

logger = logging.getLogger(__name__)

class StorageManager:
    """מנהל אחסון מתקדם - מסד נתונים או מטמון"""
    
    def __init__(self):
        self.use_db = USE_DATABASE and DATABASE_AVAILABLE
        self.pool = None
        
        # Thread safety locks
        self._cache_lock = threading.RLock()
        self._counter_lock = threading.Lock()
        
        # מטמון בזיכרון (תמיד זמין)
        self.cache = {
            'requests': {},      # בקשות תוכן
            'users': {},         # סטטיסטיקות משתמשים  
            'admins': {},        # סטטיסטיקות מנהלים
            'ratings': {},       # דירוגים
            'history': [],       # היסטוריה
            'settings': {}       # הגדרות מערכת
        }
        
        # מונה בקשות (thread-safe)
        self.request_counter = 1
        
        # אתחול מסד נתונים אם נדרש
        if self.use_db:
            try:
                self._init_database_with_pool()
                logger.info("Advanced Database mode enabled with Connection Pool")
            except Exception as e:
                logger.warning(f"Database initialization failed, using cache mode: {e}")
                self.use_db = False
        else:
            logger.info("Cache mode enabled")
    
    def _init_database_with_pool(self):
        """אתחול מסד נתונים עם Connection Pool"""
        if not self.use_db:
            return
        
        try:
            # יצירת Connection Pool גלובלי
            from pirate_content_bot.main.config import CONNECTION_POOL_CONFIG
            pool_config = {**DB_CONFIG, **CONNECTION_POOL_CONFIG}
            
            self.pool = create_global_pool(pool_config)
            
            if not self.pool:
                raise Exception("Failed to create connection pool")
            
            # הרצת setup ראשוני ומיגרציות
            success = run_initial_setup(self.pool)
            if not success:
                logger.warning("Database setup had issues, but continuing")
            
            logger.info("Database initialized with Connection Pool successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def get_connection(self):
        """קבלת חיבור מה-Pool הגלובלי"""
        if not self.use_db:
            return None
        
        try:
            pool = get_global_pool()
            if pool:
                return pool.get_connection()
            return None
        except Exception as e:
            logger.error(f"Error getting connection: {e}")
            return None
    
    # ========================= פונקציות בקשות מעודכנות =========================
    
    def save_request(self, request_data: Dict) -> int:
        """שמירת בקשה עם מודל חדש"""
        if self.use_db:
            return self._save_request_db_advanced(request_data)
        else:
            return self._save_request_cache(request_data)
    
    def get_request(self, request_id: int) -> Optional[Dict]:
        """קבלת בקשה עם מודל חדש"""
        if self.use_db:
            return self._get_request_db_advanced(request_id)
        else:
            return self._get_request_cache(request_id)
    
    def update_request(self, request_id: int, updates: Dict) -> bool:
        """עדכון בקשה מתקדם"""
        if self.use_db:
            return self._update_request_db_advanced(request_id, updates)
        else:
            return self._update_request_cache(request_id, updates)
    
    def get_pending_requests(self, category: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """קבלת בקשות ממתינות מתקדם"""
        if self.use_db:
            return self._get_pending_requests_db_advanced(category, limit)
        else:
            return self._get_pending_requests_cache(category, limit)
    
    def get_user_requests(self, user_id: int, limit: int = 20) -> List[Dict]:
        """קבלת בקשות משתמש מתקדם"""
        if self.use_db:
            return self._get_user_requests_db_advanced(user_id, limit)
        else:
            return self._get_user_requests_cache(user_id, limit)
    
    # ========================= מימושי מטמון (ללא שינוי) =========================
    
    def _save_request_cache(self, request_data: Dict) -> int:
        """שמירת בקשה במטמון (thread-safe)"""
        with self._counter_lock:
            request_id = self.request_counter
            self.request_counter += 1
        
        request_data['id'] = request_id
        
        with self._cache_lock:
            self.cache['requests'][request_id] = request_data
            
        return request_id
    
    def _get_request_cache(self, request_id: int) -> Optional[Dict]:
        """קבלת בקשה מהמטמון (thread-safe)"""
        with self._cache_lock:
            return self.cache['requests'].get(request_id)
    
    def _update_request_cache(self, request_id: int, updates: Dict) -> bool:
        """עדכון בקשה במטמון (thread-safe)"""
        with self._cache_lock:
            if request_id in self.cache['requests']:
                self.cache['requests'][request_id].update(updates)
                return True
            return False
    
    def _get_pending_requests_cache(self, category: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """קבלת בקשות ממתינות מהמטמון (thread-safe)"""
        pending = []
        
        with self._cache_lock:
            for req_id, req_data in self.cache['requests'].items():
                if req_data.get('status') == 'pending':
                    if not category or req_data.get('category') == category:
                        pending.append(req_data.copy())  # Copy to avoid external modifications
        
        # מיון לפי תאריך יצירה
        pending.sort(key=lambda x: x.get('created_at', datetime.now()))
        return pending[:limit]
    
    def _get_user_requests_cache(self, user_id: int, limit: int = 20) -> List[Dict]:
        """קבלת בקשות משתמש מהמטמון (thread-safe)"""
        user_requests = []
        
        with self._cache_lock:
            for req_data in self.cache['requests'].values():
                if req_data.get('user_id') == user_id:
                    user_requests.append(req_data.copy())  # Copy to avoid external modifications
        
        # מיון לפי תאריך (החדשות ביותר קודם)
        user_requests.sort(key=lambda x: x.get('created_at', datetime.now()), reverse=True)
        return user_requests[:limit]
    
    # ========================= מימושי מסד נתונים מתקדמים =========================
    
    def _save_request_db_advanced(self, request_data: Dict) -> int:
        """שמירת בקשה במסד נתונים עם Connection Pool"""
        if not self.pool:
            return self._save_request_cache(request_data)
        
        try:
            # שימוש ב-Connection Pool
            with self.pool.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                    INSERT INTO content_requests (
                        user_id, username, first_name, title, original_text,
                        category, priority, confidence, year, season, episode,
                        quality, language_pref, status, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    request_data.get('user_id'),
                    request_data.get('username'),
                    request_data.get('first_name'),
                    request_data.get('title'),
                    request_data.get('original_text'),
                    request_data.get('category', 'general'),
                    request_data.get('priority', 'medium'),
                    request_data.get('confidence', 50),
                    request_data.get('year'),
                    request_data.get('season'),
                    request_data.get('episode'),
                    request_data.get('quality'),
                    request_data.get('language', 'hebrew'),
                    request_data.get('status', 'pending'),
                    request_data.get('created_at', datetime.now())
                )
                
                cursor.execute(query, values)
                request_id = cursor.lastrowid
                
                cursor.close()
                
                # שמירה גם במטמון לביצועים
                request_data['id'] = request_id
                self.cache['requests'][request_id] = request_data.copy()
                
                logger.debug(f"Request {request_id} saved to database")
                return request_id
                
        except Exception as e:
            logger.error(f"Error saving request to DB: {e}")
            return self._save_request_cache(request_data)
    
    def _get_request_db_advanced(self, request_id: int) -> Optional[Dict]:
        """קבלת בקשה מהמסד נתונים עם Connection Pool"""
        # בדיקה במטמון קודם
        if request_id in self.cache['requests']:
            return self.cache['requests'][request_id]
        
        if not self.pool:
            return self._get_request_cache(request_id)
        
        try:
            with self.pool.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM content_requests WHERE id = %s", (request_id,))
                result = cursor.fetchone()
                cursor.close()
                
                if result:
                    # שמירה במטמון
                    self.cache['requests'][request_id] = result
                    return result
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting request from DB: {e}")
            return self._get_request_cache(request_id)
    
    def _update_request_db_advanced(self, request_id: int, updates: Dict) -> bool:
        """עדכון בקשה במסד נתונים עם Connection Pool (with cache sync)"""
        if not self.pool:
            logger.warning("Database pool not available, falling back to cache")
            return self._update_request_cache(request_id, updates)
        
        try:
            # בדיקת תקינות נתונים
            if not updates or not isinstance(request_id, int) or request_id <= 0:
                logger.error(f"Invalid update data: request_id={request_id}, updates={updates}")
                return False
            
            with self.pool.get_connection() as connection:
                cursor = connection.cursor()
                
                # הוספת updated_at אוטומטית
                updates['updated_at'] = datetime.now()
                
                # בניית query דינמי עם validation
                set_clauses = []
                values = []
                
                allowed_fields = {
                    'status', 'fulfilled_at', 'fulfilled_by', 'rejected_at', 'rejected_by',
                    'notes', 'rejection_reason', 'priority', 'updated_at'
                }
                
                for key, value in updates.items():
                    if key in allowed_fields:
                        set_clauses.append(f"{key} = %s")
                        values.append(value)
                
                if not set_clauses:
                    return False
                
                query = f"UPDATE content_requests SET {', '.join(set_clauses)} WHERE id = %s"
                values.append(request_id)
                
                cursor.execute(query, values)
                success = cursor.rowcount > 0
                cursor.close()
                
                # עדכון המטמון עם הנתונים החדשים
                if success:
                    with self._cache_lock:
                        if request_id in self.cache['requests']:
                            self.cache['requests'][request_id].update(updates)
                        else:
                            # אם הרשומה לא במטמון, טען אותה מהDB
                            fresh_data = self._get_request_db_advanced(request_id)
                            if fresh_data:
                                self.cache['requests'][request_id] = fresh_data
                
                # חשוב: אם השתנה הסטטוס, נקה מטמון רלוונטי
                if 'status' in updates:
                    self._invalidate_status_cache()
                
                return success
                
        except mysql.connector.Error as db_error:
            logger.error(f"Database error updating request {request_id}: {db_error}", exc_info=True)
            # נסיון rollback
            try:
                if connection:
                    connection.rollback()
            except Exception:
                pass
            # Fallback למטמון
            return self._update_request_cache(request_id, updates)
        except Exception as e:
            logger.error(f"Unexpected error updating request {request_id}: {e}", exc_info=True)
            return self._update_request_cache(request_id, updates)
    
    def _get_pending_requests_db_advanced(self, category: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """קבלת בקשות ממתינות מהמסד נתונים עם Connection Pool"""
        if not self.pool:
            return self._get_pending_requests_cache(category, limit)
        
        try:
            with self.pool.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = """
                SELECT *, 
                       TIMESTAMPDIFF(HOUR, created_at, NOW()) as age_hours,
                       CASE 
                           WHEN priority = 'vip' THEN 5
                           WHEN priority = 'urgent' THEN 4
                           WHEN priority = 'high' THEN 3
                           WHEN priority = 'medium' THEN 2
                           ELSE 1
                       END as priority_order
                FROM content_requests 
                WHERE status = 'pending'
                """
                
                params = []
                
                if category:
                    query += " AND category = %s"
                    params.append(category)
                
                # מיון לפי עדיפות ואז תאריך
                query += " ORDER BY priority_order DESC, created_at ASC LIMIT %s"
                params.append(limit)
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                cursor.close()
                
                # עדכון המטמון
                for result in results:
                    self.cache['requests'][result['id']] = result
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting pending requests from DB: {e}")
            return self._get_pending_requests_cache(category, limit)
    
    def _get_user_requests_db_advanced(self, user_id: int, limit: int = 20) -> List[Dict]:
        """קבלת בקשות משתמש מהמסד נתונים עם Connection Pool"""
        if not self.pool:
            return self._get_user_requests_cache(user_id, limit)
        
        try:
            with self.pool.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = """
                SELECT *,
                       TIMESTAMPDIFF(HOUR, created_at, NOW()) as age_hours
                FROM content_requests 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
                """
                
                cursor.execute(query, (user_id, limit))
                results = cursor.fetchall()
                cursor.close()
                
                # עדכון המטמון
                for result in results:
                    self.cache['requests'][result['id']] = result
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting user requests from DB: {e}")
            return self._get_user_requests_cache(user_id, limit)
    
    # ========================= פונקציות דירוגים מתקדמות =========================
    
    def save_rating(self, request_id: int, user_id: int, rating: int, comment: Optional[str] = None) -> bool:
        """שמירת דירוג עם מודל חדש"""
        if self.use_db:
            return self._save_rating_db_advanced(request_id, user_id, rating, comment)
        else:
            return self._save_rating_cache(request_id, user_id, rating, comment)
    
    def get_request_ratings(self, request_id: int) -> List[Dict]:
        """קבלת דירוגים של בקשה עם מודל חדש"""
        if self.use_db:
            return self._get_request_ratings_db_advanced(request_id)
        else:
            return self._get_request_ratings_cache(request_id)
    
    def _save_rating_db_advanced(self, request_id: int, user_id: int, rating: int, comment: Optional[str] = None) -> bool:
        """שמירת דירוג במסד נתונים עם Connection Pool"""
        if not self.pool:
            return self._save_rating_cache(request_id, user_id, rating, comment)
        
        try:
            with self.pool.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                    INSERT INTO content_ratings (request_id, user_id, rating, comment, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        rating = VALUES(rating), 
                        comment = VALUES(comment),
                        created_at = VALUES(created_at)
                """
                
                cursor.execute(query, (request_id, user_id, rating, comment, datetime.now()))
                cursor.close()
                
                # עדכון המטמון
                self._save_rating_cache(request_id, user_id, rating, comment)
                
                return True
                
        except Exception as e:
            logger.error(f"Error saving rating to DB: {e}")
            return self._save_rating_cache(request_id, user_id, rating, comment)
    
    def _get_request_ratings_db_advanced(self, request_id: int) -> List[Dict]:
        """קבלת דירוגים מהמסד נתונים עם Connection Pool"""
        if not self.pool:
            return self._get_request_ratings_cache(request_id)
        
        try:
            with self.pool.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                query = """
                SELECT cr.*, u.first_name as user_name
                FROM content_ratings cr
                LEFT JOIN users u ON cr.user_id = u.user_id
                WHERE cr.request_id = %s
                ORDER BY cr.created_at DESC
                """
                
                cursor.execute(query, (request_id,))
                results = cursor.fetchall()
                cursor.close()
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting ratings from DB: {e}")
            return self._get_request_ratings_cache(request_id)
    
    def _save_rating_cache(self, request_id: int, user_id: int, rating: int, comment: Optional[str] = None) -> bool:
        """שמירת דירוג במטמון"""
        if request_id not in self.cache['ratings']:
            self.cache['ratings'][request_id] = {}
        
        self.cache['ratings'][request_id][user_id] = {
            'rating': rating,
            'comment': comment,
            'timestamp': datetime.now()
        }
        return True
    
    def _get_request_ratings_cache(self, request_id: int) -> List[Dict]:
        """קבלת דירוגים מהמטמון"""
        if request_id not in self.cache['ratings']:
            return []
        
        ratings = []
        for user_id, rating_data in self.cache['ratings'][request_id].items():
            ratings.append({
                'user_id': user_id,
                'rating': rating_data['rating'],
                'comment': rating_data.get('comment'),
                'created_at': rating_data['timestamp']
            })
        
        return ratings
    
    # ========================= סטטיסטיקות מתקדמות =========================
    
    def get_system_stats(self) -> Dict[str, Any]:
        """קבלת סטטיסטיקות מערכת מתקדמות"""
        if self.use_db:
            return self._get_system_stats_db_advanced()
        else:
            return self._get_system_stats_cache()
    
    def _get_system_stats_db_advanced(self) -> Dict[str, Any]:
        """סטטיסטיקות מהמסד נתונים עם Connection Pool"""
        if not self.pool:
            return self._get_system_stats_cache()
        
        try:
            with self.pool.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                # סטטיסטיקות בסיסיות
                basic_query = """
                SELECT 
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                    COUNT(CASE WHEN status = 'fulfilled' THEN 1 END) as fulfilled,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected,
                    AVG(confidence) as avg_confidence,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as requests_24h,
                    COUNT(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as requests_7d
                FROM content_requests
                """
                
                cursor.execute(basic_query)
                basic_result = cursor.fetchone()
                
                # סטטיסטיקות לפי קטגוריה
                category_query = """
                SELECT 
                    category, 
                    COUNT(*) as count,
                    COUNT(CASE WHEN status = 'fulfilled' THEN 1 END) as fulfilled,
                    AVG(confidence) as avg_confidence
                FROM content_requests
                GROUP BY category
                ORDER BY count DESC
                """
                
                cursor.execute(category_query)
                category_results = cursor.fetchall()
                
                # סטטיסטיקות דירוגים
                rating_query = """
                SELECT 
                    COUNT(*) as total_ratings,
                    AVG(rating) as avg_rating,
                    COUNT(CASE WHEN rating >= 4 THEN 1 END) as high_ratings
                FROM content_ratings
                """
                
                cursor.execute(rating_query)
                rating_result = cursor.fetchone()
                
                cursor.close()
                
                # עיבוד התוצאות
                stats = {
                    'storage_mode': 'database_advanced',
                    'connection_pool_active': True,
                    'basic_stats': basic_result,
                    'category_breakdown': {cat['category']: cat['count'] for cat in category_results},
                    'category_details': category_results,
                    'rating_stats': rating_result,
                    'success_rate': 0,
                    'satisfaction_rate': 0
                }
                
                # חישוב שיעורים
                if basic_result['total_requests'] > 0:
                    stats['success_rate'] = (basic_result['fulfilled'] / basic_result['total_requests']) * 100
                
                if rating_result and rating_result['total_ratings'] > 0:
                    stats['satisfaction_rate'] = (rating_result['high_ratings'] / rating_result['total_ratings']) * 100
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting advanced stats from DB: {e}")
            return self._get_system_stats_cache()
    
    def _get_system_stats_cache(self) -> Dict[str, Any]:
        """סטטיסטיקות מהמטמון"""
        total_requests = len(self.cache['requests'])
        
        status_counts = {}
        category_counts = {}
        
        for req_data in self.cache['requests'].values():
            status = req_data.get('status', 'unknown')
            category = req_data.get('category', 'general')
            
            status_counts[status] = status_counts.get(status, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'storage_mode': 'cache',
            'connection_pool_active': False,
            'total_requests': total_requests,
            'status_breakdown': status_counts,
            'category_breakdown': category_counts,
            'active_users': len(self.cache['users']),
            'success_rate': (status_counts.get('fulfilled', 0) / max(total_requests, 1)) * 100
        }
    
    # ========================= פונקציות עזר מתקדמות =========================
    
    def get_advanced_search(self, filters: Dict[str, Any], limit: int = 50) -> List[Dict]:
        """חיפוש מתקדם עם פילטרים"""
        if not self.use_db:
            return self._basic_cache_search(filters, limit)
        
        try:
            with self.pool.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                # בניית query דינמי
                where_conditions = []
                params = []
                
                if filters.get('status'):
                    where_conditions.append("status = %s")
                    params.append(filters['status'])
                
                if filters.get('category'):
                    where_conditions.append("category = %s")
                    params.append(filters['category'])
                
                if filters.get('user_id'):
                    where_conditions.append("user_id = %s")
                    params.append(filters['user_id'])
                
                if filters.get('search_text'):
                    where_conditions.append("(title LIKE %s OR original_text LIKE %s)")
                    search_term = f"%{filters['search_text']}%"
                    params.extend([search_term, search_term])
                
                if filters.get('date_from'):
                    where_conditions.append("created_at >= %s")
                    params.append(filters['date_from'])
                
                if filters.get('date_to'):
                    where_conditions.append("created_at <= %s")
                    params.append(filters['date_to'])
                
                # בניית query
                base_query = "SELECT * FROM content_requests"
                if where_conditions:
                    base_query += " WHERE " + " AND ".join(where_conditions)
                
                base_query += " ORDER BY created_at DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(base_query, params)
                results = cursor.fetchall()
                cursor.close()
                
                return results
                
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            return []
    
    def _basic_cache_search(self, filters: Dict[str, Any], limit: int) -> List[Dict]:
        """חיפוש בסיסי במטמון"""
        results = []
        
        for req_data in self.cache['requests'].values():
            matches = True
            
            if filters.get('status') and req_data.get('status') != filters['status']:
                matches = False
            
            if filters.get('category') and req_data.get('category') != filters['category']:
                matches = False
            
            if filters.get('user_id') and req_data.get('user_id') != filters['user_id']:
                matches = False
            
            if filters.get('search_text'):
                search_term = filters['search_text'].lower()
                title = req_data.get('title', '').lower()
                text = req_data.get('original_text', '').lower()
                if search_term not in title and search_term not in text:
                    matches = False
            
            if matches:
                results.append(req_data)
        
        # מיון ומגבלה
        results.sort(key=lambda x: x.get('created_at', datetime.now()), reverse=True)
        return results[:limit]
    
    def _invalidate_status_cache(self):
        """ניקוי מטמון לפי סטטוס - למניעת inconsistency"""
        with self._cache_lock:
            # כאן אפשר להוסיף לוגיקה מתקדמת יותר
            # לעת עתה, נקה רק pending requests שנשמרו במטמון
            logger.debug("Cache invalidation due to status change")
    
    def sync_cache_with_database(self):
        """סנכרון מטמון עם מסד נתונים"""
        if not self.use_db or not self.pool:
            return
            
        try:
            with self._cache_lock:
                # סנכרון בקשות pending
                pending_from_db = self._get_pending_requests_db_advanced(limit=100)
                
                # עדכון המטמון
                for request in pending_from_db:
                    self.cache['requests'][request['id']] = request
                
                logger.info(f"Cache synchronized with database: {len(pending_from_db)} requests")
                
        except Exception as e:
            logger.error(f"Failed to sync cache with database: {e}")
    
    def clear_cache(self):
        """ניקוי מטמון משופר"""
        cache_sizes = {key: len(value) for key, value in self.cache.items() if isinstance(value, dict)}
        
        with self._cache_lock:
            self.cache = {
                'requests': {},
                'users': {},
                'admins': {},
                'ratings': {},
                'history': [],
                'settings': {}
            }
        
        logger.info(f"Cache cleared: {cache_sizes}")
    
    def get_cache_size(self) -> Dict[str, int]:
        """קבלת גודל המטמון מפורט"""
        sizes = {}
        for key, value in self.cache.items():
            if isinstance(value, dict):
                sizes[key] = len(value)
            elif isinstance(value, list):
                sizes[f"{key}_items"] = len(value)
            else:
                sizes[key] = 1
        
        sizes['total_cache_entries'] = sum(s for k, s in sizes.items() if not k.endswith('_items'))
        
        return sizes
    
    def is_database_connected(self) -> bool:
        """בדיקת חיבור למסד נתונים מתקדמת"""
        if not self.use_db:
            return False
        
        try:
            pool = get_global_pool()
            if pool:
                return pool.health_check()
            return False
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """מידע מפורט על מסד הנתונים"""
        if not self.use_db:
            return {
                'mode': 'cache',
                'database_available': False
            }
        
        try:
            pool = get_global_pool()
            if pool:
                pool_status = pool.get_pool_status()
                performance_stats = pool.get_performance_stats()
                
                return {
                    'mode': 'database_advanced',
                    'database_available': True,
                    'connection_pool': pool_status,
                    'performance': performance_stats,
                    'health_check': pool.health_check()
                }
            else:
                return {
                    'mode': 'database_advanced',
                    'database_available': False,
                    'error': 'Connection pool not initialized'
                }
        except Exception as e:
            return {
                'mode': 'database_advanced',
                'database_available': False,
                'error': str(e)
            }
    
    # ========================= פונקציות חדשות למשתמשים =========================
    
    def save_user(self, user_data: Dict) -> bool:
        """שמירת נתוני משתמש"""
        if self.use_db:
            return self._save_user_db(user_data)
        else:
            return self._save_user_cache(user_data)
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """קבלת נתוני משתמש"""
        if self.use_db:
            return self._get_user_db(user_id)
        else:
            return self._get_user_cache(user_id)
    
    def _save_user_db(self, user_data: Dict) -> bool:
        """שמירת משתמש במסד נתונים"""
        if not self.pool:
            return self._save_user_cache(user_data)
        
        try:
            with self.pool.get_connection() as connection:
                cursor = connection.cursor()
                
                query = """
                INSERT INTO users (
                    user_id, username, first_name, last_name, 
                    total_requests, fulfilled_requests, rejected_requests,
                    reputation_score, first_seen, last_seen
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    username = VALUES(username),
                    first_name = VALUES(first_name),
                    last_name = VALUES(last_name),
                    last_seen = VALUES(last_seen)
                """
                
                values = (
                    user_data.get('user_id'),
                    user_data.get('username'),
                    user_data.get('first_name'),
                    user_data.get('last_name'),
                    user_data.get('total_requests', 0),
                    user_data.get('fulfilled_requests', 0),
                    user_data.get('rejected_requests', 0),
                    user_data.get('reputation_score', 50),
                    user_data.get('first_seen', datetime.now()),
                    user_data.get('last_seen', datetime.now())
                )
                
                cursor.execute(query, values)
                cursor.close()
                
                # שמירה במטמון
                self.cache['users'][user_data.get('user_id')] = user_data
                
                return True
                
        except Exception as e:
            logger.error(f"Error saving user to DB: {e}")
            return self._save_user_cache(user_data)
    
    def _get_user_db(self, user_id: int) -> Optional[Dict]:
        """קבלת משתמש מהמסד נתונים"""
        # בדיקה במטמון קודם
        if user_id in self.cache['users']:
            return self.cache['users'][user_id]
        
        if not self.pool:
            return self._get_user_cache(user_id)
        
        try:
            with self.pool.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
                result = cursor.fetchone()
                cursor.close()
                
                if result:
                    # שמירה במטמון
                    self.cache['users'][user_id] = result
                    return result
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting user from DB: {e}")
            return self._get_user_cache(user_id)
    
    def _save_user_cache(self, user_data: Dict) -> bool:
        """שמירת משתמש במטמון"""
        user_id = user_data.get('user_id')
        if user_id:
            self.cache['users'][user_id] = user_data
            return True
        return False
    
    def _get_user_cache(self, user_id: int) -> Optional[Dict]:
        """קבלת משתמש מהמטמון"""
        return self.cache['users'].get(user_id)
    
    # ========================= פונקציות batch לביצועים =========================
    
    def batch_update_requests(self, updates_list: List[tuple[int, Dict]]) -> int:
        """עדכון מספר בקשות בבת אחת"""
        if not self.use_db:
            return self._batch_update_cache(updates_list)
        
        try:
            with self.pool.get_connection() as connection:
                cursor = connection.cursor()
                success_count = 0
                
                for request_id, updates in updates_list:
                    try:
                        # הוספת updated_at אוטומטית
                        updates['updated_at'] = datetime.now()
                        
                        set_clauses = []
                        values = []
                        
                        for key, value in updates.items():
                            if key in ['status', 'fulfilled_at', 'fulfilled_by', 'notes', 'updated_at']:
                                set_clauses.append(f"{key} = %s")
                                values.append(value)
                        
                        if set_clauses:
                            query = f"UPDATE content_requests SET {', '.join(set_clauses)} WHERE id = %s"
                            values.append(request_id)
                            
                            cursor.execute(query, values)
                            if cursor.rowcount > 0:
                                success_count += 1
                                
                                # עדכון מטמון
                                if request_id in self.cache['requests']:
                                    self.cache['requests'][request_id].update(updates)
                    
                    except Exception as e:
                        logger.error(f"Failed to update request {request_id}: {e}")
                
                cursor.close()
                return success_count
                
        except Exception as e:
            logger.error(f"Batch update failed: {e}")
            return self._batch_update_cache(updates_list)
    
    def _batch_update_cache(self, updates_list: List[tuple[int, Dict]]) -> int:
        """עדכון batch במטמון"""
        success_count = 0
        for request_id, updates in updates_list:
            if request_id in self.cache['requests']:
                self.cache['requests'][request_id].update(updates)
                success_count += 1
        return success_count
    
    # ========================= פונקציות סטטיסטיקות מתקדמות =========================
    
    def get_user_statistics(self, user_id: int) -> Dict[str, Any]:
        """סטטיסטיקות מפורטות של משתמש"""
        if self.use_db:
            return self._get_user_stats_db(user_id)
        else:
            return self._get_user_stats_cache(user_id)
    
    def _get_user_stats_db(self, user_id: int) -> Dict[str, Any]:
        """סטטיסטיקות משתמש מהמסד נתונים"""
        if not self.pool:
            return self._get_user_stats_cache(user_id)
        
        try:
            with self.pool.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                
                # סטטיסטיקות בסיסיות
                basic_query = """
                SELECT 
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                    COUNT(CASE WHEN status = 'fulfilled' THEN 1 END) as fulfilled,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected,
                    AVG(confidence) as avg_confidence,
                    MIN(created_at) as first_request,
                    MAX(created_at) as last_request
                FROM content_requests
                WHERE user_id = %s
                """
                
                cursor.execute(basic_query, (user_id,))
                basic_result = cursor.fetchone()
                
                # סטטיסטיקות לפי קטגוריה
                category_query = """
                SELECT 
                    category, 
                    COUNT(*) as count,
                    COUNT(CASE WHEN status = 'fulfilled' THEN 1 END) as fulfilled
                FROM content_requests
                WHERE user_id = %s
                GROUP BY category
                """
                
                cursor.execute(category_query, (user_id,))
                category_results = cursor.fetchall()
                
                # דירוגים שנתן
                rating_query = """
                SELECT 
                    COUNT(*) as ratings_given,
                    AVG(rating) as avg_rating_given
                FROM content_ratings
                WHERE user_id = %s
                """
                
                cursor.execute(rating_query, (user_id,))
                rating_result = cursor.fetchone()
                
                cursor.close()
                
                # עיבוד התוצאות
                stats = {
                    'user_id': user_id,
                    'basic_stats': basic_result,
                    'category_breakdown': {cat['category']: cat for cat in category_results},
                    'rating_stats': rating_result,
                    'success_rate': 0
                }
                
                if basic_result and basic_result['total_requests'] > 0:
                    stats['success_rate'] = (basic_result['fulfilled'] / basic_result['total_requests']) * 100
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting user stats from DB: {e}")
            return self._get_user_stats_cache(user_id)
    
    def _get_user_stats_cache(self, user_id: int) -> Dict[str, Any]:
        """סטטיסטיקות משתמש מהמטמון"""
        user_requests = [req for req in self.cache['requests'].values() 
                        if req.get('user_id') == user_id]
        
        total = len(user_requests)
        fulfilled = sum(1 for req in user_requests if req.get('status') == 'fulfilled')
        pending = sum(1 for req in user_requests if req.get('status') == 'pending')
        rejected = sum(1 for req in user_requests if req.get('status') == 'rejected')
        
        return {
            'user_id': user_id,
            'basic_stats': {
                'total_requests': total,
                'fulfilled': fulfilled,
                'pending': pending,
                'rejected': rejected
            },
            'success_rate': (fulfilled / max(total, 1)) * 100
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """מדדי ביצועים של המערכת"""
        metrics = {
            'storage_mode': 'database_advanced' if self.use_db else 'cache',
            'cache_size': self.get_cache_size(),
            'database_connected': self.is_database_connected()
        }
        
        if self.use_db:
            pool = get_global_pool()
            if pool:
                metrics['connection_pool_stats'] = pool.get_performance_stats()
        
        return metrics