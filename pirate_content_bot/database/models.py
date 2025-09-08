#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Models לבוט התמימים הפיראטים
מודלים של טבלאות וORM פשוט
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

# ========================= Base Model Class =========================

class BaseModel:
    """מחלקת בסיס לכל המודלים"""
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict:
        """המרה למילון"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result
    
    def to_json(self) -> str:
        """המרה ל-JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict):
        """יצירה ממילון"""
        return cls(**data)
    
    def __repr__(self):
        class_name = self.__class__.__name__
        attrs = ', '.join(f'{k}={v}' for k, v in self.__dict__.items())
        return f"{class_name}({attrs})"

# ========================= Content Request Model =========================

class RequestModel(BaseModel):
    """מודל בקשת תוכן"""
    
    def __init__(self, **kwargs):
        # שדות חובה
        self.id: Optional[int] = kwargs.get('id')
        self.user_id: int = kwargs.get('user_id', 0)
        self.username: Optional[str] = kwargs.get('username')
        self.first_name: Optional[str] = kwargs.get('first_name')
        self.title: str = kwargs.get('title', '')
        self.original_text: str = kwargs.get('original_text', '')
        
        # שדות אופציונליים
        self.category: str = kwargs.get('category', 'general')
        self.priority: str = kwargs.get('priority', 'medium')
        self.status: str = kwargs.get('status', 'pending')
        self.confidence: int = kwargs.get('confidence', 50)
        
        # מטא-דאטא
        self.year: Optional[int] = kwargs.get('year')
        self.season: Optional[int] = kwargs.get('season')
        self.episode: Optional[int] = kwargs.get('episode')
        self.quality: Optional[str] = kwargs.get('quality')
        self.language_pref: str = kwargs.get('language_pref', 'hebrew')
        
        # זמנים
        self.created_at: datetime = kwargs.get('created_at', datetime.now())
        self.updated_at: Optional[datetime] = kwargs.get('updated_at')
        self.fulfilled_at: Optional[datetime] = kwargs.get('fulfilled_at')
        
        # מידע על מילוי/דחייה
        self.fulfilled_by: Optional[int] = kwargs.get('fulfilled_by')
        self.rejected_by: Optional[int] = kwargs.get('rejected_by')
        self.notes: Optional[str] = kwargs.get('notes')
        self.rejection_reason: Optional[str] = kwargs.get('rejection_reason')
    
    @classmethod
    def get_table_name(cls) -> str:
        return 'content_requests'
    
    @classmethod
    def get_create_sql(cls) -> str:
        """SQL ליצירת הטבלה"""
        return """
        CREATE TABLE IF NOT EXISTS content_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            username VARCHAR(255),
            first_name VARCHAR(255),
            title VARCHAR(500) NOT NULL,
            original_text TEXT NOT NULL,
            category VARCHAR(50) DEFAULT 'general',
            priority VARCHAR(20) DEFAULT 'medium',
            status VARCHAR(20) DEFAULT 'pending',
            confidence INT DEFAULT 50,
            year INT NULL,
            season INT NULL,
            episode INT NULL,
            quality VARCHAR(20) NULL,
            language_pref VARCHAR(10) DEFAULT 'hebrew',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            fulfilled_at TIMESTAMP NULL,
            fulfilled_by BIGINT NULL,
            rejected_by BIGINT NULL,
            notes TEXT NULL,
            rejection_reason TEXT NULL,
            
            INDEX user_idx (user_id),
            INDEX status_idx (status),
            INDEX category_idx (category),
            INDEX created_idx (created_at),
            INDEX title_idx (title(100)),
            FULLTEXT(title, original_text)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    
    def is_pending(self) -> bool:
        return self.status == 'pending'
    
    def is_fulfilled(self) -> bool:
        return self.status == 'fulfilled'
    
    def is_rejected(self) -> bool:
        return self.status == 'rejected'
    
    def get_age_hours(self) -> int:
        """גיל הבקשה בשעות"""
        if not self.created_at:
            return 0
        delta = datetime.now() - self.created_at
        return int(delta.total_seconds() / 3600)
    
    def get_priority_value(self) -> int:
        """ערך מספרי של עדיפות"""
        priority_values = {
            'low': 1, 'medium': 2, 'high': 3, 
            'urgent': 4, 'vip': 5
        }
        return priority_values.get(self.priority, 2)

# ========================= User Model =========================

class UserModel(BaseModel):
    """מודל משתמש"""
    
    def __init__(self, **kwargs):
        self.user_id: int = kwargs.get('user_id', 0)
        self.username: Optional[str] = kwargs.get('username')
        self.first_name: Optional[str] = kwargs.get('first_name')
        self.last_name: Optional[str] = kwargs.get('last_name')
        
        # סטטיסטיקות
        self.total_requests: int = kwargs.get('total_requests', 0)
        self.fulfilled_requests: int = kwargs.get('fulfilled_requests', 0)
        self.rejected_requests: int = kwargs.get('rejected_requests', 0)
        self.reputation_score: int = kwargs.get('reputation_score', 50)
        
        # מידע נוסף
        self.is_banned: bool = kwargs.get('is_banned', False)
        self.ban_reason: Optional[str] = kwargs.get('ban_reason')
        self.ban_until: Optional[datetime] = kwargs.get('ban_until')
        self.warnings_count: int = kwargs.get('warnings_count', 0)
        
        # זמנים
        self.first_seen: datetime = kwargs.get('first_seen', datetime.now())
        self.last_seen: datetime = kwargs.get('last_seen', datetime.now())
        self.last_request_at: Optional[datetime] = kwargs.get('last_request_at')
    
    @classmethod
    def get_table_name(cls) -> str:
        return 'users'
    
    @classmethod
    def get_create_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            total_requests INT DEFAULT 0,
            fulfilled_requests INT DEFAULT 0,
            rejected_requests INT DEFAULT 0,
            reputation_score INT DEFAULT 50,
            is_banned BOOLEAN DEFAULT FALSE,
            ban_reason TEXT NULL,
            ban_until TIMESTAMP NULL,
            warnings_count INT DEFAULT 0,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            last_request_at TIMESTAMP NULL,
            
            INDEX username_idx (username),
            INDEX reputation_idx (reputation_score),
            INDEX banned_idx (is_banned),
            INDEX last_seen_idx (last_seen)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    
    def get_success_rate(self) -> float:
        """שיעור הצלחת בקשות"""
        if self.total_requests == 0:
            return 0.0
        return (self.fulfilled_requests / self.total_requests) * 100
    
    def is_active_user(self) -> bool:
        """האם משתמש פעיל (בקשה בחודש האחרון)"""
        if not self.last_request_at:
            return False
        delta = datetime.now() - self.last_request_at
        return delta.days <= 30
    
    def needs_warning(self) -> bool:
        """האם צריך אזהרה (יותר מדי בקשות נדחות)"""
        if self.total_requests < 5:
            return False
        reject_rate = (self.rejected_requests / self.total_requests) * 100
        return reject_rate > 70

# ========================= Rating Model =========================

class RatingModel(BaseModel):
    """מודל דירוג"""
    
    def __init__(self, **kwargs):
        self.id: Optional[int] = kwargs.get('id')
        self.request_id: int = kwargs.get('request_id', 0)
        self.user_id: int = kwargs.get('user_id', 0)
        self.rating: int = kwargs.get('rating', 5)  # 1-5
        self.comment: Optional[str] = kwargs.get('comment')
        self.created_at: datetime = kwargs.get('created_at', datetime.now())
    
    @classmethod
    def get_table_name(cls) -> str:
        return 'content_ratings'
    
    @classmethod
    def get_create_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS content_ratings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            request_id INT NOT NULL,
            user_id BIGINT NOT NULL,
            rating TINYINT CHECK (rating BETWEEN 1 AND 5),
            comment TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE KEY unique_rating (request_id, user_id),
            INDEX request_idx (request_id),
            INDEX user_idx (user_id),
            INDEX rating_idx (rating)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

# ========================= User Warning Model =========================

class UserWarningModel(BaseModel):
    """מודל אזהרות משתמש"""
    
    def __init__(self, **kwargs):
        self.id: Optional[int] = kwargs.get('id')
        self.user_id: int = kwargs.get('user_id', 0)
        self.admin_id: int = kwargs.get('admin_id', 0)
        self.reason: str = kwargs.get('reason', '')
        self.severity: str = kwargs.get('severity', 'warning')  # warning, serious, final
        self.is_active: bool = kwargs.get('is_active', True)
        self.expires_at: Optional[datetime] = kwargs.get('expires_at')
        self.created_at: datetime = kwargs.get('created_at', datetime.now())
        self.resolved_at: Optional[datetime] = kwargs.get('resolved_at')
        self.resolved_by: Optional[int] = kwargs.get('resolved_by')
    
    @classmethod
    def get_table_name(cls) -> str:
        return 'user_warnings'
    
    @classmethod
    def get_create_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS user_warnings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            admin_id BIGINT NOT NULL,
            reason TEXT NOT NULL,
            severity ENUM('warning', 'serious', 'final') DEFAULT 'warning',
            is_active BOOLEAN DEFAULT TRUE,
            expires_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP NULL,
            resolved_by BIGINT NULL,
            
            INDEX user_idx (user_id),
            INDEX admin_idx (admin_id),
            INDEX active_idx (is_active),
            INDEX severity_idx (severity),
            INDEX created_idx (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    
    def is_expired(self) -> bool:
        """האם האזהרה פגה"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def get_severity_level(self) -> int:
        """רמת חומרה מספרית"""
        levels = {'warning': 1, 'serious': 2, 'final': 3}
        return levels.get(self.severity, 1)

# ========================= Admin Action Model =========================

class AdminActionModel(BaseModel):
    """מודל פעולות מנהלים"""
    
    def __init__(self, **kwargs):
        self.id: Optional[int] = kwargs.get('id')
        self.admin_id: int = kwargs.get('admin_id', 0)
        self.action_type: str = kwargs.get('action_type', '')  # fulfill, reject, warn, ban
        self.target_type: str = kwargs.get('target_type', '')  # request, user
        self.target_id: int = kwargs.get('target_id', 0)
        self.details: Optional[str] = kwargs.get('details')
        self.metadata: Optional[Dict] = kwargs.get('metadata')
        self.created_at: datetime = kwargs.get('created_at', datetime.now())
    
    @classmethod
    def get_table_name(cls) -> str:
        return 'admin_actions'
    
    @classmethod
    def get_create_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS admin_actions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            admin_id BIGINT NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            target_type VARCHAR(50) NOT NULL,
            target_id BIGINT NOT NULL,
            details TEXT NULL,
            metadata JSON NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX admin_idx (admin_id),
            INDEX action_idx (action_type),
            INDEX target_idx (target_type, target_id),
            INDEX created_idx (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

# ========================= Notification Model =========================

class NotificationModel(BaseModel):
    """מודל התראות"""
    
    def __init__(self, **kwargs):
        self.id: Optional[int] = kwargs.get('id')
        self.recipient_id: int = kwargs.get('recipient_id', 0)
        self.sender_id: Optional[int] = kwargs.get('sender_id')
        self.notification_type: str = kwargs.get('notification_type', 'info')  # info, warning, success, error
        self.title: str = kwargs.get('title', '')
        self.message: str = kwargs.get('message', '')
        self.data: Optional[Dict] = kwargs.get('data')  # JSON data
        self.is_read: bool = kwargs.get('is_read', False)
        self.is_sent: bool = kwargs.get('is_sent', False)
        self.scheduled_for: Optional[datetime] = kwargs.get('scheduled_for')
        self.sent_at: Optional[datetime] = kwargs.get('sent_at')
        self.created_at: datetime = kwargs.get('created_at', datetime.now())
    
    @classmethod
    def get_table_name(cls) -> str:
        return 'notifications'
    
    @classmethod
    def get_create_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            recipient_id BIGINT NOT NULL,
            sender_id BIGINT NULL,
            notification_type VARCHAR(20) DEFAULT 'info',
            title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            data JSON NULL,
            is_read BOOLEAN DEFAULT FALSE,
            is_sent BOOLEAN DEFAULT FALSE,
            scheduled_for TIMESTAMP NULL,
            sent_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX recipient_idx (recipient_id),
            INDEX sender_idx (sender_id),
            INDEX type_idx (notification_type),
            INDEX read_idx (is_read),
            INDEX sent_idx (is_sent),
            INDEX scheduled_idx (scheduled_for),
            INDEX created_idx (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    
    def is_due(self) -> bool:
        """האם ההתראה צריכה להישלח"""
        if self.is_sent or not self.scheduled_for:
            return False
        return datetime.now() >= self.scheduled_for

# ========================= Cache Entry Model =========================

class CacheEntryModel(BaseModel):
    """מודל ערכי מטמון"""
    
    def __init__(self, **kwargs):
        self.key: str = kwargs.get('key', '')
        self.value: str = kwargs.get('value', '')  # JSON serialized
        self.tags: Optional[str] = kwargs.get('tags')  # comma separated
        self.expires_at: Optional[datetime] = kwargs.get('expires_at')
        self.created_at: datetime = kwargs.get('created_at', datetime.now())
        self.accessed_at: datetime = kwargs.get('accessed_at', datetime.now())
        self.access_count: int = kwargs.get('access_count', 0)
    
    @classmethod
    def get_table_name(cls) -> str:
        return 'cache_entries'
    
    @classmethod
    def get_create_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS cache_entries (
            cache_key VARCHAR(255) PRIMARY KEY,
            cache_value LONGTEXT NOT NULL,
            tags VARCHAR(500) NULL,
            expires_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            access_count INT DEFAULT 0,
            
            INDEX tags_idx (tags(100)),
            INDEX expires_idx (expires_at),
            INDEX accessed_idx (accessed_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    
    def is_expired(self) -> bool:
        """האם הערך פג"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    def get_tags_list(self) -> List[str]:
        """קבלת רשימת תגים"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',')]

# ========================= System Log Model =========================

class SystemLogModel(BaseModel):
    """מודל לוגי מערכת"""
    
    def __init__(self, **kwargs):
        self.id: Optional[int] = kwargs.get('id')
        self.level: str = kwargs.get('level', 'INFO')  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        self.module: str = kwargs.get('module', '')
        self.message: str = kwargs.get('message', '')
        self.user_id: Optional[int] = kwargs.get('user_id')
        self.request_id: Optional[int] = kwargs.get('request_id')
        self.metadata: Optional[Dict] = kwargs.get('metadata')
        self.created_at: datetime = kwargs.get('created_at', datetime.now())
    
    @classmethod
    def get_table_name(cls) -> str:
        return 'system_logs'
    
    @classmethod
    def get_create_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS system_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') DEFAULT 'INFO',
            module VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            user_id BIGINT NULL,
            request_id INT NULL,
            metadata JSON NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            INDEX level_idx (level),
            INDEX module_idx (module),
            INDEX user_idx (user_id),
            INDEX request_idx (request_id),
            INDEX created_idx (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

# ========================= פונקציות עזר למודלים =========================

def get_all_models() -> List[type]:
    """קבלת כל המודלים"""
    return [
        RequestModel,
        UserModel, 
        RatingModel,
        UserWarningModel,
        AdminActionModel,
        NotificationModel,
        CacheEntryModel,
        SystemLogModel,
        UserActivityLogModel
    ]

def create_all_tables(connection_pool) -> bool:
    """יצירת כל הטבלאות"""
    models = get_all_models()
    
    try:
        for model_class in models:
            create_sql = model_class.get_create_sql()
            connection_pool.execute_query(create_sql)
            logger.info(f"Created table: {model_class.get_table_name()}")
        
        logger.info(f"Successfully created {len(models)} tables")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False

def drop_all_tables(connection_pool) -> bool:
    """מחיקת כל הטבלאות (זהירות!)"""
    models = get_all_models()
    
    try:
        # מחיקה בסדר הפוך בגלל foreign keys
        for model_class in reversed(models):
            table_name = model_class.get_table_name()
            connection_pool.execute_query(f"DROP TABLE IF EXISTS {table_name}")
            logger.info(f"Dropped table: {table_name}")
        
        logger.info(f"Successfully dropped {len(models)} tables")
        return True
        
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        return False

def get_table_info(connection_pool, table_name: str) -> Dict:
    """קבלת מידע על טבלה"""
    try:
        # מידע בסיסי על טבלה
        info_query = "SHOW TABLE STATUS WHERE Name = %s"
        table_info = connection_pool.execute_query(info_query, (table_name,), fetch_one=True)
        
        # מידע על עמודות
        columns_query = "SHOW COLUMNS FROM {}".format(table_name)
        columns = connection_pool.execute_query(columns_query, fetch_all=True)
        
        # מידע על אינדקסים
        indexes_query = "SHOW INDEXES FROM {}".format(table_name)
        indexes = connection_pool.execute_query(indexes_query, fetch_all=True)
        
        return {
            'table_info': table_info,
            'columns': columns,
            'indexes': indexes
        }
        
    except Exception as e:
        logger.error(f"Failed to get table info for {table_name}: {e}")
        return {}

def validate_model_data(model_instance: BaseModel) -> List[str]:
    """בדיקת תקינות נתוני מודל"""
    errors = []
    
    # בדיקות ספציפיות לפי סוג המודל
    if isinstance(model_instance, RequestModel):
        if not model_instance.title.strip():
            errors.append("Title cannot be empty")
        if not model_instance.original_text.strip():
            errors.append("Original text cannot be empty")
        if model_instance.user_id <= 0:
            errors.append("Invalid user ID")
    
    elif isinstance(model_instance, UserModel):
        if model_instance.user_id <= 0:
            errors.append("Invalid user ID")
        if not model_instance.first_name:
            errors.append("First name is required")
    
    elif isinstance(model_instance, RatingModel):
        if not 1 <= model_instance.rating <= 5:
            errors.append("Rating must be between 1 and 5")
        if model_instance.request_id <= 0:
            errors.append("Invalid request ID")
        if model_instance.user_id <= 0:
            errors.append("Invalid user ID")
    
    return errors

# ========================= מחלקת עזר לעבודה עם מודלים =========================

class ModelManager:
    """מנהל מודלים - עזר לעבודה עם המודלים"""
    
    def __init__(self, connection_pool):
        self.pool = connection_pool
        self.models = {model.get_table_name(): model for model in get_all_models()}
    
    def create_model_instance(self, table_name: str, **kwargs) -> Optional[BaseModel]:
        """יצירת instance של מודל"""
        model_class = self.models.get(table_name)
        if not model_class:
            return None
        
        return model_class(**kwargs)
    
    def save_model(self, model_instance: BaseModel) -> bool:
        """שמירת מודל למסד נתונים"""
        # זה ידרוש מימוש נפרד לכל מודל
        # כרגע זה placeholder
        return True
    
    def find_by_id(self, table_name: str, id_value: int) -> Optional[BaseModel]:
        """חיפוש לפי ID"""
        model_class = self.models.get(table_name)
        if not model_class:
            return None
        
        query = f"SELECT * FROM {table_name} WHERE id = %s"
        result = self.pool.execute_query(query, (id_value,), fetch_one=True)
        
        if result:
            return model_class(**result)
        return None
    
    def get_model_stats(self) -> Dict[str, Any]:
        """סטטיסטיקות על כל המודלים"""
        stats = {}
        
        for table_name in self.models.keys():
            try:
                count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                result = self.pool.execute_query(count_query, fetch_one=True)
                stats[table_name] = result['count'] if result else 0
            except:
                stats[table_name] = 0
        
        return stats


# ========================= User Activity Log Model =========================

class UserActivityLogModel(BaseModel):
    """מודל לוג פעילות משתמש"""
    
    def __init__(self, **kwargs):
        self.id: Optional[int] = kwargs.get('id')
        self.user_id: int = kwargs.get('user_id', 0)
        self.action_type: str = kwargs.get('action_type', '')
        self.created_at: datetime = kwargs.get('created_at', datetime.now())
    
    @classmethod
    def get_table_name(cls) -> str:
        return 'user_activity_log'
    
    @classmethod
    def get_create_sql(cls) -> str:
        return """
        CREATE TABLE IF NOT EXISTS user_activity_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id BIGINT NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            created_at DATETIME NOT NULL,
            
            INDEX idx_user_id (user_id),
            INDEX idx_created_at (created_at),
            INDEX idx_action_type (action_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """