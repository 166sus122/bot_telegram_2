#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run database migrations
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

try:
    # Import configuration
    from pirate_content_bot.main.config import DB_CONFIG, USE_DATABASE
    from pirate_content_bot.database.connection_pool import DatabaseConnectionPool
    from pirate_content_bot.database.migrations import create_migration_manager
    
    logger.info("Starting migration process...")
    
    if USE_DATABASE:
        # Connect with localhost for external execution
        db_config = DB_CONFIG.copy()
        db_config['host'] = 'localhost'
        
        # Create connection pool
        pool = DatabaseConnectionPool(db_config)
        success = pool.create_pool()
        
        if success:
            logger.info("✅ Database connection successful!")
            
            # Add missing columns manually
            logger.info("Checking for missing columns...")
            
            # Check for quality column
            check_quality = """
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'content_requests' AND column_name = 'quality' AND table_schema = DATABASE()
            """
            result = pool.execute_query(check_quality, fetch_one=True)
            
            if result['count'] == 0:
                logger.info("Adding missing quality column...")
                pool.execute_query("ALTER TABLE content_requests ADD COLUMN quality VARCHAR(20) NULL")
                logger.info("✅ Added quality column")
            else:
                logger.info("Quality column already exists")
                
            # Check for episode column  
            check_episode = """
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'content_requests' AND column_name = 'episode' AND table_schema = DATABASE()
            """
            result = pool.execute_query(check_episode, fetch_one=True)
            
            if result['count'] == 0:
                logger.info("Adding missing episode column...")
                pool.execute_query("ALTER TABLE content_requests ADD COLUMN episode INT NULL")
                logger.info("✅ Added episode column")
            else:
                logger.info("Episode column already exists")
            
            # Check for language_pref column
            check_lang = """
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'content_requests' AND column_name = 'language_pref' AND table_schema = DATABASE()
            """
            result = pool.execute_query(check_lang, fetch_one=True)
            
            if result['count'] == 0:
                logger.info("Adding missing language_pref column...")
                pool.execute_query("ALTER TABLE content_requests ADD COLUMN language_pref VARCHAR(10) DEFAULT 'hebrew'")
                logger.info("✅ Added language_pref column")
            else:
                logger.info("Language_pref column already exists")
                
            # Check for rejected_by column
            check_rejected = """
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'content_requests' AND column_name = 'rejected_by' AND table_schema = DATABASE()
            """
            result = pool.execute_query(check_rejected, fetch_one=True)
            
            if result['count'] == 0:
                logger.info("Adding missing rejected_by column...")
                pool.execute_query("ALTER TABLE content_requests ADD COLUMN rejected_by BIGINT NULL")
                logger.info("✅ Added rejected_by column")
            else:
                logger.info("Rejected_by column already exists")
            
            logger.info("✅ Database migration completed successfully!")
            
        else:
            logger.error("❌ Failed to create database connection")
    else:
        logger.info("Database is disabled")

except Exception as e:
    logger.error(f"❌ Migration failed: {e}")
    import traceback
    traceback.print_exc()