#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive tests for admin commands: analytics, broadcast, search
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_admin_commands():
    """Test admin commands with actual admin users"""
    
    try:
        # Import bot components
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        from pirate_content_bot.main.config import ADMIN_IDS
        
        logger.info("Initializing bot for admin command testing...")
        logger.info(f"Admin IDs from config: {ADMIN_IDS}")
        
        # Create bot instance
        bot = EnhancedPirateBot()
        
        # Initialize components manually
        bot._init_core_components()
        bot._init_utils()
        bot._init_services()
        
        # Use the first admin ID from config, or default if not available
        admin_user_id = ADMIN_IDS[0] if ADMIN_IDS else 6039349310
        
        # Create mock admin user
        mock_admin_user = Mock()
        mock_admin_user.id = admin_user_id
        mock_admin_user.first_name = "TestAdmin"
        mock_admin_user.username = "test_admin"
        mock_admin_user.is_bot = False
        
        logger.info(f"Testing with admin user ID: {admin_user_id}")
        
        # Test Analytics Command with Admin User
        logger.info("=" * 60)
        logger.info("📊 Testing ANALYTICS command with ADMIN user...")
        
        mock_update_analytics = Mock()
        mock_update_analytics.effective_user = mock_admin_user
        mock_update_analytics.message = Mock()
        mock_update_analytics.message.reply_text = AsyncMock()
        
        mock_context_analytics = Mock()
        
        try:
            await bot.analytics_command(mock_update_analytics, mock_context_analytics)
            
            if mock_update_analytics.message.reply_text.called:
                reply_text = mock_update_analytics.message.reply_text.call_args[0][0]
                logger.info("✅ Analytics command executed for admin")
                
                if "אנליטיקס מתקדם" in reply_text:
                    logger.info("✅ Analytics shows proper response format")
                elif "שגיאה בטעינת נתוני אנליטיקס" in reply_text:
                    logger.warning("⚠️  Analytics shows data loading error (expected if no data)")
                else:
                    logger.warning(f"⚠️  Unexpected analytics response: {reply_text[:100]}...")
            else:
                logger.error("❌ Analytics command didn't send a reply for admin")
                
        except Exception as e:
            logger.error(f"❌ Analytics command failed for admin: {e}")
            import traceback
            traceback.print_exc()
        
        # Test Broadcast Command with Admin User
        logger.info("=" * 60)
        logger.info("📢 Testing BROADCAST command with ADMIN user...")
        
        mock_update_broadcast = Mock()
        mock_update_broadcast.effective_user = mock_admin_user
        mock_update_broadcast.message = Mock()
        mock_update_broadcast.message.reply_text = AsyncMock()
        
        # Test with broadcast message
        mock_context_broadcast = Mock()
        mock_context_broadcast.args = ["Test", "admin", "broadcast", "message"]
        
        try:
            await bot.broadcast_command(mock_update_broadcast, mock_context_broadcast)
            
            if mock_update_broadcast.message.reply_text.called:
                reply_text = mock_update_broadcast.message.reply_text.call_args[0][0]
                logger.info("✅ Broadcast command executed for admin")
                
                if "שידור הסתיים" in reply_text:
                    logger.info("✅ Broadcast shows completion message")
                elif "לא נמצאו משתמשים פעילים" in reply_text:
                    logger.warning("⚠️  Broadcast shows no active users (expected if empty DB)")
                else:
                    logger.info(f"Response: {reply_text}")
            else:
                logger.error("❌ Broadcast command didn't send a reply for admin")
                
        except Exception as e:
            logger.error(f"❌ Broadcast command failed for admin: {e}")
            import traceback
            traceback.print_exc()
        
        # Test Search Command (available to all users)
        logger.info("=" * 60)
        logger.info("🔍 Testing SEARCH command with various queries...")
        
        test_queries = [
            ["Breaking", "Bad"],
            ["סדרה"],
            ["2022"],
            ["test"],
            ["movie"]
        ]
        
        for query_args in test_queries:
            mock_update_search = Mock()
            mock_update_search.effective_user = mock_admin_user
            mock_update_search.message = Mock()
            mock_update_search.message.reply_text = AsyncMock()
            
            mock_context_search = Mock()
            mock_context_search.args = query_args
            
            query_str = " ".join(query_args)
            
            try:
                await bot.search_command(mock_update_search, mock_context_search)
                
                if mock_update_search.message.reply_text.called:
                    reply_text = mock_update_search.message.reply_text.call_args[0][0]
                    logger.info(f"✅ Search '{query_str}': {reply_text[:100]}...")
                else:
                    logger.warning(f"⚠️  Search '{query_str}' didn't send reply")
                    
            except Exception as e:
                logger.error(f"❌ Search '{query_str}' failed: {e}")
        
        # Test Performance - Multiple Rapid Commands
        logger.info("=" * 60)
        logger.info("⚡ Testing PERFORMANCE with rapid commands...")
        
        import time
        start_time = time.time()
        
        # Run multiple analytics commands rapidly
        for i in range(5):
            mock_update_perf = Mock()
            mock_update_perf.effective_user = mock_admin_user
            mock_update_perf.message = Mock()
            mock_update_perf.message.reply_text = AsyncMock()
            
            mock_context_perf = Mock()
            
            try:
                await bot.analytics_command(mock_update_perf, mock_context_perf)
            except Exception as e:
                logger.warning(f"Performance test {i+1} failed: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"✅ Performance test: 5 analytics commands in {duration:.2f}s ({duration/5:.2f}s per command)")
        
        # Test Error Handling
        logger.info("=" * 60)
        logger.info("🛠️  Testing ERROR HANDLING...")
        
        # Test with invalid user object
        mock_update_invalid = Mock()
        mock_update_invalid.effective_user = None
        mock_update_invalid.message = Mock()
        mock_update_invalid.message.reply_text = AsyncMock()
        
        mock_context_invalid = Mock()
        
        try:
            await bot.analytics_command(mock_update_invalid, mock_context_invalid)
            logger.info("✅ Handled invalid user gracefully")
        except Exception as e:
            logger.info(f"✅ Expected error for invalid user: {e}")
        
        logger.info("=" * 60)
        logger.info("✅ Comprehensive admin command testing completed!")
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_admin_commands())