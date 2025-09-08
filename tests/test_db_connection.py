#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test database connection
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
    from pirate_content_bot.database.connection_pool import DatabaseConnectionPool, create_global_pool
    from pirate_content_bot.database.models import create_all_tables
    
    logger.info("Successfully imported modules")
    logger.info(f"USE_DATABASE: {USE_DATABASE}")
    logger.info(f"DB_CONFIG: {DB_CONFIG}")
    
    if USE_DATABASE:
        logger.info("Testing database connection...")
        
        # Create connection pool
        pool = DatabaseConnectionPool(DB_CONFIG)
        success = pool.create_pool()
        
        if success:
            logger.info("✅ Database connection successful!")
            
            # Test health check
            health_ok = pool.health_check()
            logger.info(f"Health check: {'✅ OK' if health_ok else '❌ FAILED'}")
            
            # Test a simple query
            try:
                result = pool.execute_query("SELECT 1 as test", fetch_one=True)
                logger.info(f"Test query result: {result}")
            except Exception as e:
                logger.error(f"Test query failed: {e}")
            
            # Get pool status
            status = pool.get_pool_status()
            logger.info(f"Pool status: {status}")
            
            # Test table creation
            try:
                logger.info("Testing table creation...")
                table_creation_success = create_all_tables(pool)
                logger.info(f"Table creation: {'✅ SUCCESS' if table_creation_success else '❌ FAILED'}")
            except Exception as e:
                logger.error(f"Table creation failed: {e}")
            
        else:
            logger.error("❌ Failed to create database connection pool")
    else:
        logger.info("Database is disabled in configuration")

except ImportError as e:
    logger.error(f"❌ Import error: {e}")
except Exception as e:
    logger.error(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()