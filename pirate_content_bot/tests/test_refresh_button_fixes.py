#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים לתיקוני כפתורי רענון ובקשות שלי
- תיקון כפתור רענון סטטיסטיקות
- תיקון טיפול בשגיאות כפתורי מנהל
- בדיקת ניתוב נכון של כפתור הבקשות שלי
"""

import unittest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
sys.path.insert(0, project_root)

try:
    from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
    from pirate_content_bot.main.config import ADMIN_IDS, MAIN_GROUP_ID
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Import warning: {e}")
    IMPORTS_AVAILABLE = False


class TestRefreshButtonFixes(unittest.IsolatedAsyncioTestCase):
    """Test refresh button fixes"""
    
    async def asyncSetUp(self):
        """Setup for each test"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
            
        self.bot = Mock(spec=EnhancedPirateBot)
        self.bot._is_admin = Mock(return_value=True)
        self.bot.logger = Mock()
        
        # Mock services
        self.bot.request_service = Mock()
        self.bot.request_service.get_pending_requests = AsyncMock()
        self.bot.request_service._get_basic_request_stats = AsyncMock()
        
        # Mock Telegram objects
        self.mock_query = Mock()
        self.mock_query.edit_message_text = AsyncMock()
        self.mock_query.from_user = Mock()
        self.mock_query.from_user.id = 6039349310  # Admin ID
        self.mock_query.from_user.first_name = "TestAdmin"
    
    async def test_stats_refresh_button_works(self):
        """Test stats refresh button works correctly"""
        
        # Mock stats data
        mock_stats = {
            'total_requests': 10,
            'pending': 2, 
            'fulfilled': 7,
            'rejected': 1,
            'unique_users': 5,
            'avg_confidence': 75.5
        }
        
        self.bot.request_service._get_basic_request_stats.return_value = mock_stats
        
        # Import and bind the function
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        admin_func = EnhancedPirateBot._handle_admin_button.__get__(self.bot)
        
        await admin_func(self.mock_query, "admin:statistics")
        
        # Verify function was called correctly
        self.bot.request_service._get_basic_request_stats.assert_called_once()
        
        # Verify message was edited with stats data
        self.mock_query.edit_message_text.assert_called_once()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        
        # Verify content shows actual stats
        self.assertIn("סה\"כ בקשות: 10", call_args)
        self.assertIn("ממתינות: 2", call_args)
        self.assertIn("מולאו: 7", call_args)
        self.assertIn("נדחו: 1", call_args)
        self.assertIn("משתמשים ייחודיים: 5", call_args)
        self.assertIn("ביטחון ממוצע: 75.5%", call_args)
    
    async def test_pending_refresh_button_works(self):
        """Test pending refresh button works correctly"""
        
        # Mock pending requests data
        mock_pending = [
            {
                'id': 1,
                'title': 'Test Pending Request',
                'user_first_name': 'TestUser',
                'category': 'series',
                'created_at': '2025-09-09T10:00:00Z'
            }
        ]
        
        self.bot.request_service.get_pending_requests.return_value = mock_pending
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        admin_func = EnhancedPirateBot._handle_admin_button.__get__(self.bot)
        
        await admin_func(self.mock_query, "admin:pending")
        
        # Verify function was called correctly
        self.bot.request_service.get_pending_requests.assert_called_once_with(limit=10)
        
        # Verify message content
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("בקשות ממתינות", call_args)
        self.assertIn("#1", call_args)
        self.assertIn("Test Pending Request", call_args)
        self.assertIn("TestUser", call_args)
    
    async def test_admin_button_error_handling_with_details(self):
        """Test admin button error handling shows specific error details"""
        
        # Mock service to raise exception
        self.bot.request_service._get_basic_request_stats.side_effect = Exception("Database connection failed")
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        admin_func = EnhancedPirateBot._handle_admin_button.__get__(self.bot)
        
        await admin_func(self.mock_query, "admin:statistics")
        
        # Should show detailed error message
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("שגיאה בעיבוד פעולת המנהל: statistics", call_args)
        self.assertIn("Database connection failed", call_args)
    
    async def test_action_stats_routes_to_admin_statistics(self):
        """Test action:stats button routes to admin statistics"""
        
        # Mock stats data
        mock_stats = {
            'total_requests': 5,
            'pending': 1, 
            'fulfilled': 3,
            'rejected': 1
        }
        
        self.bot.request_service._get_basic_request_stats.return_value = mock_stats
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        
        # Create a bot instance to test the routing
        class TestBot(Mock):
            def __init__(self):
                super().__init__()
                self._is_admin = Mock(return_value=True)
                self.request_service = Mock()
                self.request_service._get_basic_request_stats = AsyncMock(return_value=mock_stats)
            
            async def _handle_admin_button(self, query, data):
                await self.request_service._get_basic_request_stats(datetime.now())
                await query.edit_message_text("Stats displayed")
        
        test_bot = TestBot()
        
        # Import and bind the function
        action_func = EnhancedPirateBot._handle_action_button.__get__(test_bot)
        
        # Test the routing - this should call _handle_admin_button with "admin:statistics"
        await action_func(self.mock_query, "action:stats")
        
        # Verify the stats function was called (meaning routing worked)
        test_bot.request_service._get_basic_request_stats.assert_called_once()
    
    async def test_non_admin_stats_access_denied(self):
        """Test non-admin users can't access stats"""
        
        self.bot._is_admin.return_value = False
        self.mock_query.from_user.id = 999999999  # Non-admin user
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        action_func = EnhancedPirateBot._handle_action_button.__get__(self.bot)
        
        await action_func(self.mock_query, "action:stats")
        
        # Should deny access
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("אין לך הרשאות לצפייה בסטטיסטיקות", call_args)
    
    async def test_my_requests_button_routing(self):
        """Test my requests button routes correctly"""
        
        # This test verifies the routing is correct, actual functionality
        # is tested in test_button_fixes.py
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        
        # Mock the _handle_my_requests_button function
        test_bot = Mock()
        test_bot._handle_my_requests_button = AsyncMock()
        
        action_func = EnhancedPirateBot._handle_action_button.__get__(test_bot)
        
        await action_func(self.mock_query, "action:my_requests")
        
        # Verify the my requests handler was called
        test_bot._handle_my_requests_button.assert_called_once_with(self.mock_query)


class TestErrorHandlingImprovements(unittest.TestCase):
    """Test error handling improvements"""
    
    def test_imports_available(self):
        """Test that required modules can be imported"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
        
        # Should be able to import without errors
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        self.assertTrue(hasattr(EnhancedPirateBot, '_handle_admin_button'))
        self.assertTrue(hasattr(EnhancedPirateBot, '_handle_my_requests_button'))


if __name__ == '__main__':
    unittest.main()