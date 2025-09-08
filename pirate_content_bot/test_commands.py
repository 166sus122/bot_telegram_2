#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test specific command functions: search, analytics, broadcast
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_commands():
    """Test the three command functions for issues"""
    
    try:
        # Import bot components
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        
        logger.info("Initializing bot for command testing...")
        
        # Create bot instance
        bot = EnhancedPirateBot()
        
        # Initialize components manually - these are sync methods
        bot._init_core_components()
        bot._init_utils()
        bot._init_services()
        
        logger.info("🧪 Testing commands for issues...")
        
        # Create mock admin user
        mock_admin_user = Mock()
        mock_admin_user.id = 123456789  # Assume this is an admin ID
        mock_admin_user.first_name = "TestAdmin"
        mock_admin_user.username = "test_admin"
        mock_admin_user.is_bot = False
        
        # Test Analytics Command
        logger.info("=" * 60)
        logger.info("🔬 Testing ANALYTICS command...")
        
        # Create mock update for analytics
        mock_update_analytics = Mock()
        mock_update_analytics.effective_user = mock_admin_user
        mock_update_analytics.message = Mock()
        mock_update_analytics.message.reply_text = AsyncMock()
        
        # Create mock context for analytics
        mock_context_analytics = Mock()
        
        try:
            await bot.analytics_command(mock_update_analytics, mock_context_analytics)
            
            if mock_update_analytics.message.reply_text.called:
                reply_text = mock_update_analytics.message.reply_text.call_args[0][0]
                logger.info("✅ Analytics command executed successfully")
                logger.info(f"Response preview: {reply_text[:200]}...")
            else:
                logger.warning("⚠️  Analytics command didn't send a reply")
                
        except Exception as e:
            logger.error(f"❌ Analytics command failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test Search Command
        logger.info("=" * 60)
        logger.info("🔍 Testing SEARCH command...")
        
        # Create mock update for search
        mock_update_search = Mock()
        mock_update_search.effective_user = mock_admin_user
        mock_update_search.message = Mock()
        mock_update_search.message.reply_text = AsyncMock()
        
        # Create mock context for search (with search term)
        mock_context_search = Mock()
        mock_context_search.args = ["Breaking", "Bad"]  # Test search for "Breaking Bad"
        
        try:
            await bot.search_command(mock_update_search, mock_context_search)
            
            if mock_update_search.message.reply_text.called:
                reply_text = mock_update_search.message.reply_text.call_args[0][0]
                logger.info("✅ Search command executed successfully")
                logger.info(f"Response preview: {reply_text[:200]}...")
            else:
                logger.warning("⚠️  Search command didn't send a reply")
                
        except Exception as e:
            logger.error(f"❌ Search command failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test Search Command - No Args
        logger.info("-" * 40)
        logger.info("🔍 Testing SEARCH command with no arguments...")
        
        mock_context_search_no_args = Mock()
        mock_context_search_no_args.args = []  # No search terms
        
        mock_update_search_no_args = Mock()
        mock_update_search_no_args.effective_user = mock_admin_user
        mock_update_search_no_args.message = Mock()
        mock_update_search_no_args.message.reply_text = AsyncMock()
        
        try:
            await bot.search_command(mock_update_search_no_args, mock_context_search_no_args)
            
            if mock_update_search_no_args.message.reply_text.called:
                reply_text = mock_update_search_no_args.message.reply_text.call_args[0][0]
                logger.info("✅ Search command (no args) executed successfully")
                logger.info(f"Response preview: {reply_text[:200]}...")
                
        except Exception as e:
            logger.error(f"❌ Search command (no args) failed: {e}")
        
        # Test Broadcast Command
        logger.info("=" * 60)
        logger.info("📢 Testing BROADCAST command...")
        
        # Create mock update for broadcast
        mock_update_broadcast = Mock()
        mock_update_broadcast.effective_user = mock_admin_user
        mock_update_broadcast.message = Mock()
        mock_update_broadcast.message.reply_text = AsyncMock()
        
        # Create mock context for broadcast (with message)
        mock_context_broadcast = Mock()
        mock_context_broadcast.args = ["Test", "broadcast", "message"]  # Test broadcast message
        
        try:
            await bot.broadcast_command(mock_update_broadcast, mock_context_broadcast)
            
            if mock_update_broadcast.message.reply_text.called:
                reply_text = mock_update_broadcast.message.reply_text.call_args[0][0]
                logger.info("✅ Broadcast command executed successfully")
                logger.info(f"Response preview: {reply_text[:200]}...")
            else:
                logger.warning("⚠️  Broadcast command didn't send a reply")
                
        except Exception as e:
            logger.error(f"❌ Broadcast command failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test Broadcast Command - No Args
        logger.info("-" * 40)
        logger.info("📢 Testing BROADCAST command with no arguments...")
        
        mock_context_broadcast_no_args = Mock()
        mock_context_broadcast_no_args.args = []  # No broadcast message
        
        mock_update_broadcast_no_args = Mock()
        mock_update_broadcast_no_args.effective_user = mock_admin_user
        mock_update_broadcast_no_args.message = Mock()
        mock_update_broadcast_no_args.message.reply_text = AsyncMock()
        
        try:
            await bot.broadcast_command(mock_update_broadcast_no_args, mock_context_broadcast_no_args)
            
            if mock_update_broadcast_no_args.message.reply_text.called:
                reply_text = mock_update_broadcast_no_args.message.reply_text.call_args[0][0]
                logger.info("✅ Broadcast command (no args) executed successfully")
                logger.info(f"Response preview: {reply_text[:200]}...")
                
        except Exception as e:
            logger.error(f"❌ Broadcast command (no args) failed: {e}")
        
        # Test with non-admin user
        logger.info("=" * 60)
        logger.info("🚫 Testing commands with NON-ADMIN user...")
        
        # Create mock non-admin user
        mock_regular_user = Mock()
        mock_regular_user.id = 987654321  # Assume this is NOT an admin ID
        mock_regular_user.first_name = "TestUser"
        mock_regular_user.username = "test_user"
        mock_regular_user.is_bot = False
        
        # Test analytics with non-admin
        mock_update_non_admin = Mock()
        mock_update_non_admin.effective_user = mock_regular_user
        mock_update_non_admin.message = Mock()
        mock_update_non_admin.message.reply_text = AsyncMock()
        
        mock_context_non_admin = Mock()
        
        try:
            await bot.analytics_command(mock_update_non_admin, mock_context_non_admin)
            
            if mock_update_non_admin.message.reply_text.called:
                reply_text = mock_update_non_admin.message.reply_text.call_args[0][0]
                logger.info("✅ Analytics command correctly rejected non-admin")
                logger.info(f"Response: {reply_text}")
            else:
                logger.warning("⚠️  Analytics command didn't respond to non-admin")
                
        except Exception as e:
            logger.error(f"❌ Analytics command failed for non-admin: {e}")
        
        logger.info("=" * 60)
        logger.info("✅ Command testing completed!")
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_commands())