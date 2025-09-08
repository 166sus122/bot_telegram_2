#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Migrations לבוט התמימים הפיראטים
מערכת ניהול שינויי מסד נתונים עם versioning
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)

# ========================= Base Migration Class =========================

class Migration(ABC):
    """מחלקת בסיס למיגרציות"""
    
    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
        self.executed_at: Optional[datetime] = None
        
    @abstractmethod
    def up(self, connection_pool) -> bool:
        """יישום השינוי"""
        pass
    
    @abstractmethod
    def down(self, connection_pool) -> bool:
        """ביטול השינוי"""
        pass
    
    def __str__(self):
        return f"Migration {self.version}: {self.description}"

# ========================= ניהול טבלת מיגרציות =========================

class MigrationManager:
    """מנהל מיגרציות מסד נתונים"""
    
    def __init__(self, connection_pool):
        self.pool = connection_pool
        self.migrations: List[Migration] = []
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """וידוא שטבלת המיגרציות קיימת"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(50) PRIMARY KEY,
            description TEXT NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            execution_time_ms INT DEFAULT 0,
            checksum VARCHAR(64) NULL,
            
            INDEX executed_idx (executed_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        try:
            self.pool.execute_query(create_table_sql)
            logger.info("Migration table ensured")
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")
            raise
    
    def register_migration(self, migration: Migration):
        """רישום מיגרציה"""
        self.migrations.append(migration)
        # מיון לפי version
        self.migrations.sort(key=lambda m: m.version)
        logger.debug(f"Registered migration: {migration.version}")
    
    def get_current_version(self) -> Optional[str]:
        """קבלת הגרסה הנוכחית"""
        try:
            query = """
            SELECT version FROM schema_migrations 
            ORDER BY executed_at DESC 
            LIMIT 1
            """
            result = self.pool.execute_query(query, fetch_one=True)
            return result['version'] if result else None
        except Exception as e:
            logger.error(f"Failed to get current version: {e}")
            return None
    
    def get_executed_migrations(self) -> List[str]:
        """קבלת רשימת מיגרציות שהורצו"""
        try:
            query = "SELECT version FROM schema_migrations ORDER BY executed_at"
            results = self.pool.execute_query(query, fetch_all=True)
            return [row['version'] for row in results]
        except Exception as e:
            logger.error(f"Failed to get executed migrations: {e}")
            return []
    
    def get_pending_migrations(self, target_version: Optional[str] = None) -> List[Migration]:
        """קבלת מיגרציות ממתינות"""
        executed = set(self.get_executed_migrations())
        pending = []
        
        for migration in self.migrations:
            if migration.version not in executed:
                if target_version is None or migration.version <= target_version:
                    pending.append(migration)
        
        return pending
    
    def run_migrations(self, target_version: Optional[str] = None) -> bool:
        """הרצת מיגרציות"""
        pending = self.get_pending_migrations(target_version)
        
        if not pending:
            logger.info("No pending migrations")
            return True
        
        logger.info(f"Running {len(pending)} migrations")
        
        success_count = 0
        for migration in pending:
            if self._execute_migration(migration, 'up'):
                success_count += 1
            else:
                logger.error(f"Migration {migration.version} failed, stopping")
                break
        
        logger.info(f"Executed {success_count}/{len(pending)} migrations successfully")
        return success_count == len(pending)
    
    def rollback_to_version(self, target_version: str) -> bool:
        """rollback לגרסה ספציפית"""
        executed = self.get_executed_migrations()
        current_version = self.get_current_version()
        
        if not current_version or current_version <= target_version:
            logger.info("No rollback needed")
            return True
        
        # מיגרציות לביטול (בסדר הפוך)
        to_rollback = []
        for version in reversed(executed):
            if version > target_version:
                migration = self._find_migration(version)
                if migration:
                    to_rollback.append(migration)
        
        logger.info(f"Rolling back {len(to_rollback)} migrations")
        
        success_count = 0
        for migration in to_rollback:
            if self._execute_migration(migration, 'down'):
                success_count += 1
            else:
                logger.error(f"Rollback of {migration.version} failed, stopping")
                break
        
        logger.info(f"Rolled back {success_count}/{len(to_rollback)} migrations")
        return success_count == len(to_rollback)
    
    def _execute_migration(self, migration: Migration, direction: str) -> bool:
        """ביצוע מיגרציה יחידה"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing {direction}: {migration}")
            
            if direction == 'up':
                success = migration.up(self.pool)
                if success:
                    self._record_migration(migration, start_time)
            else:  # down
                success = migration.down(self.pool)
                if success:
                    self._remove_migration_record(migration.version)
            
            if success:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                logger.info(f"Migration {migration.version} {direction} completed in {execution_time:.0f}ms")
            
            return success
            
        except Exception as e:
            logger.error(f"Migration {migration.version} {direction} failed: {e}")
            return False
    
    def _record_migration(self, migration: Migration, start_time: datetime):
        """רישום מיגרציה שהורצה"""
        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        query = """
        INSERT INTO schema_migrations (version, description, executed_at, execution_time_ms)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            executed_at = VALUES(executed_at),
            execution_time_ms = VALUES(execution_time_ms)
        """
        
        self.pool.execute_query(query, (
            migration.version,
            migration.description,
            start_time,
            execution_time
        ))
    
    def _remove_migration_record(self, version: str):
        """הסרת רישום מיגרציה"""
        query = "DELETE FROM schema_migrations WHERE version = %s"
        self.pool.execute_query(query, (version,))
    
    def _find_migration(self, version: str) -> Optional[Migration]:
        """חיפוש מיגרציה לפי גרסה"""
        for migration in self.migrations:
            if migration.version == version:
                return migration
        return None
    
    def get_migration_status(self) -> Dict:
        """קבלת סטטוס מיגרציות"""
        executed = self.get_executed_migrations()
        pending = self.get_pending_migrations()
        current = self.get_current_version()
        
        return {
            'current_version': current,
            'total_migrations': len(self.migrations),
            'executed_count': len(executed),
            'pending_count': len(pending),
            'executed_versions': executed,
            'pending_versions': [m.version for m in pending],
            'all_versions': [m.version for m in self.migrations]
        }

# ========================= מיגרציות ספציפיות =========================

class CreateBasicTables(Migration):
    """יצירת טבלאות בסיסיות"""
    
    def __init__(self):
        super().__init__('001_create_basic_tables', 'Create basic content tables')
    
    def up(self, pool) -> bool:
        """יצירת טבלאות בסיסיות"""
        from pirate_content_bot.database.models import RequestModel, UserModel, RatingModel
        
        try:
            # יצירת טבלת בקשות
            pool.execute_query(RequestModel.get_create_sql())
            
            # יצירת טבלת משתמשים  
            pool.execute_query(UserModel.get_create_sql())
            
            # יצירת טבלת דירוגים
            pool.execute_query(RatingModel.get_create_sql())
            
            return True
        except Exception as e:
            logger.error(f"Failed to create basic tables: {e}")
            return False
    
    def down(self, pool) -> bool:
        """מחיקת טבלאות בסיסיות"""
        try:
            pool.execute_query("DROP TABLE IF EXISTS content_ratings")
            pool.execute_query("DROP TABLE IF EXISTS users") 
            pool.execute_query("DROP TABLE IF EXISTS content_requests")
            return True
        except Exception as e:
            logger.error(f"Failed to drop basic tables: {e}")
            return False

class CreateExtendedTables(Migration):
    """יצירת טבלאות מורחבות"""
    
    def __init__(self):
        super().__init__('002_create_extended_tables', 'Create extended system tables')
    
    def up(self, pool) -> bool:
        """יצירת טבלאות מורחבות"""
        from pirate_content_bot.database.models import (UserWarningModel, AdminActionModel, 
                                   NotificationModel, SystemLogModel)
        
        try:
            # טבלת אזהרות
            pool.execute_query(UserWarningModel.get_create_sql())
            
            # טבלת פעולות מנהלים
            pool.execute_query(AdminActionModel.get_create_sql())
            
            # טבלת התראות
            pool.execute_query(NotificationModel.get_create_sql())
            
            # טבלת לוגים
            pool.execute_query(SystemLogModel.get_create_sql())
            
            return True
        except Exception as e:
            logger.error(f"Failed to create extended tables: {e}")
            return False
    
    def down(self, pool) -> bool:
        """מחיקת טבלאות מורחבות"""
        try:
            pool.execute_query("DROP TABLE IF EXISTS system_logs")
            pool.execute_query("DROP TABLE IF EXISTS notifications")
            pool.execute_query("DROP TABLE IF EXISTS admin_actions")
            pool.execute_query("DROP TABLE IF EXISTS user_warnings")
            return True
        except Exception as e:
            logger.error(f"Failed to drop extended tables: {e}")
            return False

class CreateCacheTable(Migration):
    """יצירת טבלת מטמון"""
    
    def __init__(self):
        super().__init__('003_create_cache_table', 'Create cache storage table')
    
    def up(self, pool) -> bool:
        """יצירת טבלת מטמון"""
        from pirate_content_bot.database.models import CacheEntryModel
        
        try:
            pool.execute_query(CacheEntryModel.get_create_sql())
            return True
        except Exception as e:
            logger.error(f"Failed to create cache table: {e}")
            return False
    
    def down(self, pool) -> bool:
        """מחיקת טבלת מטמון"""
        try:
            pool.execute_query("DROP TABLE IF EXISTS cache_entries")
            return True
        except Exception as e:
            logger.error(f"Failed to drop cache table: {e}")
            return False

class AddPerformanceIndexes(Migration):
    """הוספת אינדקסים לביצועים"""
    
    def __init__(self):
        super().__init__('004_add_performance_indexes', 'Add performance indexes')
    
    def up(self, pool) -> bool:
        """הוספת אינדקסים"""
        try:
            indexes = [
                # אינדקסים מורכבים לבקשות
                "CREATE INDEX idx_requests_status_created ON content_requests(status, created_at)",
                "CREATE INDEX idx_requests_user_status ON content_requests(user_id, status)",
                "CREATE INDEX idx_requests_category_status ON content_requests(category, status)",
                
                # אינדקסים למשתמשים
                "CREATE INDEX idx_users_active ON users(last_request_date, is_banned)",
                "CREATE INDEX idx_users_reputation ON users(reputation_score, total_requests)",
                
                # אינדקסים לדירוגים
                "CREATE INDEX idx_ratings_request_rating ON content_ratings(request_id, rating)",
                
                # אינדקסים לאזהרות
                "CREATE INDEX idx_warnings_user_active ON user_warnings(user_id, is_active)",
                "CREATE INDEX idx_warnings_severity ON user_warnings(severity, created_at)",
                
                # אינדקסים להתראות  
                "CREATE INDEX idx_notifications_recipient_read ON notifications(recipient_id, is_read)",
                "CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_for, is_sent)",
            ]
            
            for index_sql in indexes:
                try:
                    pool.execute_query(index_sql)
                except Exception as e:
                    # אינדקס כבר קיים - זה בסדר
                    if "Duplicate key name" not in str(e):
                        logger.warning(f"Failed to create index: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to add performance indexes: {e}")
            return False
    
    def down(self, pool) -> bool:
        """הסרת אינדקסים"""
        try:
            indexes_to_drop = [
                "DROP INDEX idx_requests_status_created ON content_requests",
                "DROP INDEX idx_requests_user_status ON content_requests", 
                "DROP INDEX idx_requests_category_status ON content_requests",
                "DROP INDEX idx_users_active ON users",
                "DROP INDEX idx_users_reputation ON users",
                "DROP INDEX idx_ratings_request_rating ON content_ratings",
                "DROP INDEX idx_warnings_user_active ON user_warnings",
                "DROP INDEX idx_warnings_severity ON user_warnings",
                "DROP INDEX idx_notifications_recipient_read ON notifications",
                "DROP INDEX idx_notifications_scheduled ON notifications",
            ]
            
            for drop_sql in indexes_to_drop:
                try:
                    pool.execute_query(drop_sql)
                except:
                    pass  # אינדקס לא קיים - זה בסדר
            
            return True
        except Exception as e:
            logger.error(f"Failed to drop performance indexes: {e}")
            return False

class AddFullTextSearch(Migration):
    """הוספת Full Text Search"""
    
    def __init__(self):
        super().__init__('005_add_fulltext_search', 'Add full text search capabilities')
    
    def up(self, pool) -> bool:
        """הוספת Full Text Search"""
        try:
            # בדיקה אם אינדקס כבר קיים
            check_query = """
            SELECT COUNT(*) as count FROM information_schema.statistics 
            WHERE table_name = 'content_requests' 
            AND index_name = 'ft_title_content'
            AND table_schema = DATABASE()
            """
            
            result = pool.execute_query(check_query, fetch_one=True)
            if result and result['count'] > 0:
                logger.info("Full text index already exists")
                return True
            
            # יצירת אינדקס Full Text
            fulltext_sql = """
            ALTER TABLE content_requests 
            ADD FULLTEXT ft_title_content (title, original_text)
            """
            
            pool.execute_query(fulltext_sql)
            logger.info("Full text search index created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add full text search: {e}")
            return False
    
    def down(self, pool) -> bool:
        """הסרת Full Text Search"""
        try:
            pool.execute_query("ALTER TABLE content_requests DROP INDEX ft_title_content")
            return True
        except Exception as e:
            logger.error(f"Failed to drop full text search: {e}")
            return False

class MigrateExistingData(Migration):
    """מיגרציית נתונים קיימים"""
    
    def __init__(self):
        super().__init__('006_migrate_existing_data', 'Migrate existing data to new schema')
    
    def up(self, pool) -> bool:
        """מיגרציית נתונים קיימים"""
        try:
            # בדיקה אם יש נתונים קיימים במבנה הישן
            check_old_data = """
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_name = 'old_requests' 
            AND table_schema = DATABASE()
            """
            
            result = pool.execute_query(check_old_data, fetch_one=True)
            if not result or result['count'] == 0:
                logger.info("No old data to migrate")
                return True
            
            # מיגרציית בקשות מהמבנה הישן
            migrate_requests = """
            INSERT INTO content_requests (
                user_id, username, first_name, title, original_text, 
                category, status, created_at
            )
            SELECT 
                user_id, username, first_name, title, request_text,
                COALESCE(category, 'general'), COALESCE(status, 'pending'), created_at
            FROM old_requests
            WHERE NOT EXISTS (
                SELECT 1 FROM content_requests 
                WHERE content_requests.user_id = old_requests.user_id 
                AND content_requests.title = old_requests.title
            )
            """
            
            pool.execute_query(migrate_requests)
            logger.info("Migrated existing requests")
            
            # מיגרציית סטטיסטיקות משתמשים
            migrate_users = """
            INSERT INTO users (
                user_id, username, first_name, total_requests, 
                fulfilled_requests, first_seen, last_seen
            )
            SELECT 
                user_id, username, first_name,
                COUNT(*) as total_requests,
                SUM(CASE WHEN status = 'fulfilled' THEN 1 ELSE 0 END) as fulfilled,
                MIN(created_at) as first_seen,
                MAX(created_at) as last_seen
            FROM old_requests
            GROUP BY user_id, username, first_name
            ON DUPLICATE KEY UPDATE
                total_requests = VALUES(total_requests),
                fulfilled_requests = VALUES(fulfilled_requests)
            """
            
            pool.execute_query(migrate_users)
            logger.info("Migrated user statistics")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate existing data: {e}")
            return False
    
    def down(self, pool) -> bool:
        """ביטול מיגרציית נתונים - זהירות!"""
        try:
            # מחיקת נתונים שמוגרטו
            pool.execute_query("DELETE FROM users WHERE first_seen >= '2024-01-01'")
            pool.execute_query("DELETE FROM content_requests WHERE created_at >= '2024-01-01'")
            
            logger.warning("Rolled back migrated data")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback migrated data: {e}")
            return False

class OptimizeDatabase(Migration):
    """אופטימיזציית מסד נתונים"""
    
    def __init__(self):
        super().__init__('007_optimize_database', 'Database optimization and cleanup')
    
    def up(self, pool) -> bool:
        """אופטימיזציית מסד נתונים"""
        try:
            optimizations = [
                # אופטימיזציית טבלאות
                "OPTIMIZE TABLE content_requests",
                "OPTIMIZE TABLE users", 
                "OPTIMIZE TABLE content_ratings",
                "OPTIMIZE TABLE user_warnings",
                "OPTIMIZE TABLE notifications",
                
                # ניתוח טבלאות לאינדקסים
                "ANALYZE TABLE content_requests",
                "ANALYZE TABLE users",
                "ANALYZE TABLE content_ratings",
            ]
            
            for optimization in optimizations:
                try:
                    pool.execute_query(optimization)
                except Exception as e:
                    logger.warning(f"Optimization failed: {optimization} - {e}")
            
            logger.info("Database optimization completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
            return False
    
    def down(self, pool) -> bool:
        """אין צורך בביטול אופטימיזציה"""
        return True

class FixExistingSchema(Migration):
    """תיקון סכימת הטבלאות הקיימות"""
    
    def __init__(self):
        super().__init__('008_fix_existing_schema', 'Fix existing table schemas')
    
    def _column_exists(self, pool, table_name: str, column_name: str) -> bool:
        """בדיקה אם עמודה קיימת בטבלה"""
        try:
            check_query = """
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s AND table_schema = DATABASE()
            """
            result = pool.execute_query(check_query, (table_name, column_name), fetch_one=True)
            return result and result['count'] > 0
        except:
            return False
    
    def up(self, pool) -> bool:
        """הוספת עמודות חסרות לטבלאות קיימות"""
        try:
            # בדיקה ותיקון טבלת users
            users_columns = [
                ("first_seen", "ALTER TABLE users ADD COLUMN first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("last_seen", "ALTER TABLE users ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                ("ban_until", "ALTER TABLE users ADD COLUMN ban_until TIMESTAMP NULL"),
                ("warnings_count", "ALTER TABLE users ADD COLUMN warnings_count INT DEFAULT 0"),
                ("last_name", "ALTER TABLE users ADD COLUMN last_name VARCHAR(255) NULL"),
            ]
            
            # בדיקה ותיקון טבלת content_requests
            requests_columns = [
                ("admin_id", "ALTER TABLE content_requests ADD COLUMN admin_id BIGINT NULL"),
                ("year", "ALTER TABLE content_requests ADD COLUMN year INT NULL"),
                ("notes", "ALTER TABLE content_requests ADD COLUMN notes TEXT NULL"),
                ("quality_score", "ALTER TABLE content_requests ADD COLUMN quality_score INT DEFAULT NULL"),
            ]
            
            # בדיקה ותוספת עמודות למשתמשים
            for column_name, sql_command in users_columns:
                if not self._column_exists(pool, 'users', column_name):
                    try:
                        pool.execute_query(sql_command)
                        logger.info(f"Added column {column_name} to users table")
                    except Exception as e:
                        logger.warning(f"Failed to add {column_name}: {e}")
            
            # בדיקה ותוספת עמודות לבקשות
            for column_name, sql_command in requests_columns:
                if not self._column_exists(pool, 'content_requests', column_name):
                    try:
                        pool.execute_query(sql_command)
                        logger.info(f"Added column {column_name} to content_requests table")
                    except Exception as e:
                        logger.warning(f"Failed to add {column_name}: {e}")
            
            logger.info("Schema fixes applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fix schema: {e}")
            return False
    
    def down(self, pool) -> bool:
        """הסרת העמודות שנוספו"""
        try:
            drop_columns = [
                "ALTER TABLE users DROP COLUMN IF EXISTS first_seen",
                "ALTER TABLE users DROP COLUMN IF EXISTS last_seen", 
                "ALTER TABLE users DROP COLUMN IF EXISTS ban_until",
                "ALTER TABLE users DROP COLUMN IF EXISTS warnings_count",
                "ALTER TABLE users DROP COLUMN IF EXISTS last_name",
                "ALTER TABLE content_requests DROP COLUMN IF EXISTS admin_id",
                "ALTER TABLE content_requests DROP COLUMN IF EXISTS year",
                "ALTER TABLE content_requests DROP COLUMN IF EXISTS notes",
                "ALTER TABLE content_requests DROP COLUMN IF EXISTS quality_score",
            ]
            
            for drop_sql in drop_columns:
                try:
                    pool.execute_query(drop_sql)
                except:
                    pass  # עמודה לא קיימת
            
            return True
        except Exception as e:
            logger.error(f"Failed to rollback schema fixes: {e}")
            return False

class FixSchemaColumnsV2(Migration):
    """תיקון עמודות הסכימה - גירסה 2"""
    
    def __init__(self):
        super().__init__('009_fix_schema_columns_v2', 'Fix schema columns v2')
    
    def _column_exists(self, pool, table_name: str, column_name: str) -> bool:
        """בדיקה אם עמודה קיימת בטבלה"""
        try:
            check_query = """
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s AND table_schema = DATABASE()
            """
            result = pool.execute_query(check_query, (table_name, column_name), fetch_one=True)
            return result and result['count'] > 0
        except:
            return False
    
    def up(self, pool) -> bool:
        """הוספת עמודות חסרות"""
        try:
            # הוספת עמודות למשתמשים
            if not self._column_exists(pool, 'users', 'first_seen'):
                pool.execute_query("ALTER TABLE users ADD COLUMN first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                logger.info("Added first_seen to users")
                
            if not self._column_exists(pool, 'users', 'last_seen'):
                pool.execute_query("ALTER TABLE users ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
                logger.info("Added last_seen to users")
                
            if not self._column_exists(pool, 'users', 'ban_until'):
                pool.execute_query("ALTER TABLE users ADD COLUMN ban_until TIMESTAMP NULL")
                logger.info("Added ban_until to users")
                
            if not self._column_exists(pool, 'users', 'warnings_count'):
                pool.execute_query("ALTER TABLE users ADD COLUMN warnings_count INT DEFAULT 0")
                logger.info("Added warnings_count to users")
                
            # הוספת עמודות לבקשות
            if not self._column_exists(pool, 'content_requests', 'admin_id'):
                pool.execute_query("ALTER TABLE content_requests ADD COLUMN admin_id BIGINT NULL")
                logger.info("Added admin_id to content_requests")
                
            if not self._column_exists(pool, 'content_requests', 'year'):
                pool.execute_query("ALTER TABLE content_requests ADD COLUMN year INT NULL")
                logger.info("Added year to content_requests")
                
            if not self._column_exists(pool, 'content_requests', 'notes'):
                pool.execute_query("ALTER TABLE content_requests ADD COLUMN notes TEXT NULL")
                logger.info("Added notes to content_requests")
                
            if not self._column_exists(pool, 'content_requests', 'season'):
                pool.execute_query("ALTER TABLE content_requests ADD COLUMN season INT NULL")
                logger.info("Added season to content_requests")
                
            logger.info("Schema columns fixed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fix schema columns: {e}")
            return False
    
    def down(self, pool) -> bool:
        """הסרת העמודות שנוספו"""
        return True

class AddSeasonColumn(Migration):
    """הוספת עמודת season"""
    
    def __init__(self):
        super().__init__('010_add_season_column', 'Add season column')
    
    def up(self, pool) -> bool:
        """הוספת עמודת season"""
        try:
            # בדיקה אם עמודה קיימת
            check_query = """
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'content_requests' AND column_name = 'season' AND table_schema = DATABASE()
            """
            result = pool.execute_query(check_query, fetch_one=True)
            
            if not result or result['count'] == 0:
                pool.execute_query("ALTER TABLE content_requests ADD COLUMN season INT NULL")
                logger.info("Added season column to content_requests")
            else:
                logger.info("Season column already exists")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to add season column: {e}")
            return False
    
    def down(self, pool) -> bool:
        """הסרת עמודת season"""
        return True

class AddEpisodeColumn(Migration):
    """הוספת עמודת episode"""
    
    def __init__(self):
        super().__init__('011_add_episode_column', 'Add episode column')
    
    def up(self, pool) -> bool:
        """הוספת עמודת episode"""
        try:
            # בדיקה אם עמודה קיימת
            check_query = """
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'content_requests' AND column_name = 'episode' AND table_schema = DATABASE()
            """
            result = pool.execute_query(check_query, fetch_one=True)
            
            if not result or result['count'] == 0:
                pool.execute_query("ALTER TABLE content_requests ADD COLUMN episode INT NULL")
                logger.info("Added episode column to content_requests")
            else:
                logger.info("Episode column already exists")
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to add episode column: {e}")
            return False
    
    def down(self, pool) -> bool:
        """הסרת עמודת episode"""
        return True

# ========================= פונקציות עזר למיגרציות =========================

def create_migration_manager(connection_pool) -> MigrationManager:
    """יצירת מנהל מיגרציות עם כל המיגרציות"""
    manager = MigrationManager(connection_pool)
    
    # רישום כל המיגרציות בסדר
    migrations = [
        CreateBasicTables(),
        CreateExtendedTables(),
        CreateCacheTable(),
        AddPerformanceIndexes(),
        AddFullTextSearch(),
        MigrateExistingData(),
        OptimizeDatabase(),
        FixExistingSchema(),
        FixSchemaColumnsV2(),
        AddSeasonColumn(),
        AddEpisodeColumn()
    ]
    
    for migration in migrations:
        manager.register_migration(migration)
    
    return manager

def run_initial_setup(connection_pool) -> bool:
    """הרצת התקנה ראשונית"""
    try:
        manager = create_migration_manager(connection_pool)
        
        # הרצת כל המיגרציות
        success = manager.run_migrations()
        
        if success:
            logger.info("Initial database setup completed successfully")
            
            # הצגת סטטוס
            status = manager.get_migration_status()
            logger.info(f"Database version: {status['current_version']}")
            logger.info(f"Executed migrations: {status['executed_count']}/{status['total_migrations']}")
        
        return success
        
    except Exception as e:
        logger.error(f"Initial setup failed: {e}")
        return False

def upgrade_database(connection_pool, target_version: Optional[str] = None) -> bool:
    """שדרוג מסד נתונים לגרסה עדכנית"""
    try:
        manager = create_migration_manager(connection_pool)
        
        current = manager.get_current_version()
        logger.info(f"Current database version: {current}")
        
        pending = manager.get_pending_migrations(target_version)
        if not pending:
            logger.info("Database is up to date")
            return True
        
        logger.info(f"Upgrading database with {len(pending)} migrations")
        success = manager.run_migrations(target_version)
        
        if success:
            new_version = manager.get_current_version()
            logger.info(f"Database upgraded successfully to version: {new_version}")
        
        return success
        
    except Exception as e:
        logger.error(f"Database upgrade failed: {e}")
        return False

def rollback_database(connection_pool, target_version: str) -> bool:
    """rollback מסד נתונים לגרסה קודמת"""
    try:
        manager = create_migration_manager(connection_pool)
        
        current = manager.get_current_version()
        logger.warning(f"Rolling back database from {current} to {target_version}")
        
        success = manager.rollback_to_version(target_version)
        
        if success:
            new_version = manager.get_current_version()
            logger.info(f"Database rolled back to version: {new_version}")
        
        return success
        
    except Exception as e:
        logger.error(f"Database rollback failed: {e}")
        return False

def get_migration_info(connection_pool) -> Dict:
    """קבלת מידע מפורט על מיגרציות"""
    try:
        manager = create_migration_manager(connection_pool)
        status = manager.get_migration_status()
        
        # מידע נוסף על כל מיגרציה
        migration_details = []
        for migration in manager.migrations:
            is_executed = migration.version in status['executed_versions']
            migration_details.append({
                'version': migration.version,
                'description': migration.description,
                'executed': is_executed,
                'class_name': migration.__class__.__name__
            })
        
        return {
            **status,
            'migration_details': migration_details
        }
        
    except Exception as e:
        logger.error(f"Failed to get migration info: {e}")
        return {}

def validate_database_schema(connection_pool) -> Dict[str, any]:
    """בדיקת תקינות מבנה מסד נתונים"""
    try:
        from pirate_content_bot.database.models import get_all_models
        
        validation_results = {
            'valid': True,
            'missing_tables': [],
            'table_issues': [],
            'recommendations': []
        }
        
        # בדיקת טבלאות
        models = get_all_models()
        for model_class in models:
            table_name = model_class.get_table_name()
            
            # בדיקה אם טבלה קיימת
            check_query = """
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_name = %s AND table_schema = DATABASE()
            """
            
            result = connection_pool.execute_query(check_query, (table_name,), fetch_one=True)
            
            if not result or result['count'] == 0:
                validation_results['missing_tables'].append(table_name)
                validation_results['valid'] = False
        
        # המלצות
        if validation_results['missing_tables']:
            validation_results['recommendations'].append(
                "Run initial setup or migrations to create missing tables"
            )
        
        # בדיקת אינדקסים חשובים
        important_indexes = [
            ('content_requests', 'user_idx'),
            ('content_requests', 'status_idx'),
            ('users', 'username_idx'),
        ]
        
        for table_name, index_name in important_indexes:
            check_index = """
            SELECT COUNT(*) as count 
            FROM information_schema.statistics 
            WHERE table_name = %s AND index_name = %s 
            AND table_schema = DATABASE()
            """
            
            result = connection_pool.execute_query(check_index, (table_name, index_name), fetch_one=True)
            
            if not result or result['count'] == 0:
                validation_results['table_issues'].append(f"Missing index: {index_name} on {table_name}")
                validation_results['recommendations'].append(
                    f"Create index {index_name} on table {table_name} for better performance"
                )
        
        return validation_results
        
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return {'valid': False, 'error': str(e)}

# ========================= CLI Tools =========================

def main():
    """כלי CLI למיגרציות"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrations.py [setup|upgrade|rollback|status|validate]")
        return
    
    command = sys.argv[1]
    
    # יצירת connection pool (צריך להגדיר config)
    try:
        from pirate_content_bot.database.connection_pool import create_global_pool
        from pirate_content_bot.main.config import DB_CONFIG, CONNECTION_POOL_CONFIG
        
        config = {**DB_CONFIG, **CONNECTION_POOL_CONFIG}
        pool = create_global_pool(config)
        
        if command == 'setup':
            success = run_initial_setup(pool)
            print(f"Setup {'successful' if success else 'failed'}")
            
        elif command == 'upgrade':
            target = sys.argv[2] if len(sys.argv) > 2 else None
            success = upgrade_database(pool, target)
            print(f"Upgrade {'successful' if success else 'failed'}")
            
        elif command == 'rollback':
            if len(sys.argv) < 3:
                print("Usage: python migrations.py rollback <target_version>")
                return
            success = rollback_database(pool, sys.argv[2])
            print(f"Rollback {'successful' if success else 'failed'}")
            
        elif command == 'status':
            info = get_migration_info(pool)
            print(f"Current version: {info.get('current_version', 'None')}")
            print(f"Total migrations: {info.get('total_migrations', 0)}")
            print(f"Executed: {info.get('executed_count', 0)}")
            print(f"Pending: {info.get('pending_count', 0)}")
            
        elif command == 'validate':
            validation = validate_database_schema(pool)
            print(f"Schema valid: {validation['valid']}")
            if validation.get('missing_tables'):
                print(f"Missing tables: {', '.join(validation['missing_tables'])}")
            if validation.get('recommendations'):
                print("Recommendations:")
                for rec in validation['recommendations']:
                    print(f"  - {rec}")
        
        else:
            print("Unknown command")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()