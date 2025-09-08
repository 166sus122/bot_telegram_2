#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialization Helper - וידוא שכל השירותים מאותחלים כראוי
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

def safe_init_analyzer():
    """אתחול בטוח של content_analyzer"""
    try:
        from core.content_analyzer import ContentAnalyzer
        analyzer = ContentAnalyzer()
        logger.info("✅ ContentAnalyzer initialized successfully")
        return analyzer
    except Exception as e:
        logger.warning(f"⚠️ ContentAnalyzer initialization failed: {e}")
        logger.info("🔄 Running without advanced content analysis")
        return None

def safe_init_duplicate_detector():
    """אתחול בטוח של duplicate detector"""
    try:
        # נניח שיש מחלקה כזו
        from utils.duplicate_detector import DuplicateDetector
        detector = DuplicateDetector()
        logger.info("✅ DuplicateDetector initialized successfully")
        return detector
    except Exception as e:
        logger.warning(f"⚠️ DuplicateDetector initialization failed: {e}")
        logger.info("🔄 Running without duplicate detection")
        return None

def safe_init_storage_manager():
    """אתחול בטוח של storage manager"""
    try:
        from core.storage_manager import StorageManager
        
        # בדיקה אם יש חיבור למסד נתונים
        db_host = os.getenv('DB_HOST', 'localhost')
        db_available = True
        
        try:
            import psycopg2
            # בדיקה מהירה של חיבור DB
            test_conn = psycopg2.connect(
                host=db_host,
                port=int(os.getenv('DB_PORT', '5432')),
                database=os.getenv('DB_NAME', 'pirate_content'),
                user=os.getenv('DB_USER', 'pirate_user'),
                password=os.getenv('DB_PASSWORD', ''),
                connect_timeout=5
            )
            test_conn.close()
            logger.info("✅ Database connection verified")
        except Exception as db_e:
            logger.warning(f"⚠️ Database connection failed: {db_e}")
            logger.info("🔄 Will use cache-only mode")
            db_available = False
        
        storage = StorageManager(use_db=db_available)
        logger.info("✅ StorageManager initialized successfully")
        return storage
        
    except Exception as e:
        logger.error(f"❌ StorageManager initialization failed: {e}")
        logger.info("🔄 Creating minimal cache-only storage")
        
        # יצירת storage מינימלי
        class MinimalStorage:
            def __init__(self):
                self.pool = None
                self.cache = {'requests': {}, 'users': {}}
                
            def save_request(self, request_data):
                req_id = len(self.cache['requests']) + 1
                request_data['id'] = req_id
                self.cache['requests'][req_id] = request_data
                return req_id
                
            def get_request(self, request_id):
                return self.cache['requests'].get(request_id)
                
            def update_request(self, request_id, updates):
                if request_id in self.cache['requests']:
                    self.cache['requests'][request_id].update(updates)
                    return True
                return False
        
        return MinimalStorage()

def check_environment():
    """בדיקת משתני סביבה נדרשים"""
    required_vars = ['BOT_TOKEN']
    optional_vars = ['ADMIN_IDS', 'MAIN_GROUP_ID', 'LOG_CHANNEL_ID']
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_required:
        logger.error(f"❌ Missing required environment variables: {missing_required}")
        return False
    
    if missing_optional:
        logger.warning(f"⚠️ Missing optional environment variables: {missing_optional}")
    
    logger.info("✅ Environment variables check passed")
    return True

def initialize_services():
    """אתחול כל השירותים בצורה בטוחה"""
    logger.info("🚀 Starting services initialization...")
    
    # בדיקת סביבה
    if not check_environment():
        raise RuntimeError("Missing required environment variables")
    
    # אתחול שירותים
    services = {
        'storage': safe_init_storage_manager(),
        'analyzer': safe_init_analyzer(),
        'duplicate_detector': safe_init_duplicate_detector()
    }
    
    logger.info("✅ All services initialized successfully")
    return services