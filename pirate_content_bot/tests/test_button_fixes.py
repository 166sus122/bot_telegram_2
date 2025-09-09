#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים לתיקונים האחרונים:
- כפתור "הבקשות שלי" 
- כפתורי רענון מנהל
- פקודת ברודקאסט לטופיק עדכונים
- תיקון ספירת מנהלים באנליטיקס
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


class TestButtonFixes(unittest.IsolatedAsyncioTestCase):
    """Test recent button fixes"""
    
    async def asyncSetUp(self):
        """Setup for each test"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
            
        self.bot = Mock(spec=EnhancedPirateBot)
        self.bot._is_admin = Mock(return_value=True)
        self.bot._convert_to_israel_time = Mock(return_value="09/09/2025")
        self.bot.logger = Mock()
        
        # Mock services
        self.bot.user_service = Mock()
        self.bot.user_service.get_user_requests = AsyncMock()
        self.bot.request_service = Mock() 
        self.bot.request_service.get_pending_requests = AsyncMock()
        self.bot.request_service.get_request_analytics = AsyncMock()
        
        # Mock Telegram objects
        self.mock_query = Mock()
        self.mock_query.edit_message_text = AsyncMock()
        self.mock_query.from_user = Mock()
        self.mock_query.from_user.id = 6039349310  # Admin ID
        self.mock_query.from_user.first_name = "TestAdmin"
        
        # Mock context
        self.mock_context = Mock()
        self.mock_context.bot = Mock()
        self.mock_context.bot.send_message = AsyncMock()
        self.mock_context.args = []
        
        # Mock update
        self.mock_update = Mock()
        self.mock_update.effective_user = self.mock_query.from_user
        self.mock_update.message = Mock()
        self.mock_update.message.reply_text = AsyncMock()
    
    async def test_my_requests_button_with_requests(self):
        """Test my requests button shows actual user requests"""
        
        # Mock user requests data
        mock_requests = [
            {
                'id': 1,
                'title': 'Test Request 1',
                'status': 'pending',
                'created_at': '2025-09-09T10:00:00Z',
                'category': 'series'
            },
            {
                'id': 2, 
                'title': 'Test Request 2',
                'status': 'fulfilled',
                'created_at': '2025-09-08T15:30:00Z',
                'category': 'movies'
            }
        ]
        
        self.bot.user_service.get_user_requests.return_value = mock_requests
        
        # Import and bind the function
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        handle_func = EnhancedPirateBot._handle_my_requests_button.__get__(self.bot)
        
        await handle_func(self.mock_query)
        
        # Verify function was called correctly
        self.bot.user_service.get_user_requests.assert_called_once_with(
            self.mock_query.from_user.id, limit=10
        )
        
        # Verify message was edited with requests data
        self.mock_query.edit_message_text.assert_called_once()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        
        # Verify content shows actual requests
        self.assertIn("**הבקשות שלך** (2)", call_args)
        self.assertIn("Test Request 1", call_args)
        self.assertIn("Test Request 2", call_args)
        self.assertIn("⏳", call_args)  # pending status
        self.assertIn("✅", call_args)  # fulfilled status
        self.assertIn("#1", call_args)
        self.assertIn("#2", call_args)
    
    async def test_my_requests_button_no_requests(self):
        """Test my requests button when user has no requests"""
        
        self.bot.user_service.get_user_requests.return_value = []
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        handle_func = EnhancedPirateBot._handle_my_requests_button.__get__(self.bot)
        
        await handle_func(self.mock_query)
        
        # Verify empty state message
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("עדיין לא יש לך בקשות במערכת", call_args)
        self.assertIn("כתוב מה אתה מחפש והבוט יטפל בשאר", call_args)
    
    async def test_broadcast_command_sends_to_updates_thread(self):
        """Test broadcast command sends to updates thread"""
        
        self.mock_context.args = ["הודעת", "בדיקה", "לטופיק"]
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        broadcast_func = EnhancedPirateBot.broadcast_command.__get__(self.bot)
        
        await broadcast_func(self.mock_update, self.mock_context)
        
        # Verify send_message was called with correct parameters
        self.mock_context.bot.send_message.assert_called_once()
        call_args = self.mock_context.bot.send_message.call_args
        
        # Check chat_id is main group
        self.assertEqual(call_args[1]['chat_id'], MAIN_GROUP_ID)
        
        # Check message_thread_id is 11432 (updates thread)
        self.assertEqual(call_args[1]['message_thread_id'], 11432)
        
        # Check message content
        message_text = call_args[1]['text']
        self.assertIn("הודעת שידור", message_text)
        self.assertIn("הודעת בדיקה לטופיק", message_text)
        self.assertIn("נשלח על ידי מנהל", message_text)
    
    async def test_admin_pending_button(self):
        """Test admin pending requests button"""
        
        mock_pending = [
            {
                'id': 1,
                'title': 'Pending Request 1',
                'user_first_name': 'TestUser',
                'category': 'series',
                'created_at': '2025-09-09T10:00:00Z'
            }
        ]
        
        self.bot.request_service.get_pending_requests.return_value = mock_pending
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        admin_func = EnhancedPirateBot._handle_admin_button.__get__(self.bot)
        
        await admin_func(self.mock_query, "admin:pending")
        
        # Verify service was called
        self.bot.request_service.get_pending_requests.assert_called_once_with(limit=10)
        
        # Verify message content
        call_args = self.mock_query.edit_message_text.call_args[0][0] 
        self.assertIn("בקשות ממתינות", call_args)
        self.assertIn("#1", call_args)
        self.assertIn("Pending Request 1", call_args)
    
    async def test_analytics_command_shows_correct_admin_count(self):
        """Test analytics shows correct number of admins"""
        
        # Mock analytics data
        mock_analytics = {
            'basic_stats': {'total_requests': 5, 'pending': 1},
            'category_distribution': [],
            'top_users': [],
            'response_times': {'avg_response_time': 0}
        }
        
        self.bot.request_service.get_request_analytics.return_value = mock_analytics
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        analytics_func = EnhancedPirateBot.analytics_command.__get__(self.bot)
        
        await analytics_func(self.mock_update, self.mock_context)
        
        # Should not show 0 admins anymore
        call_args = self.mock_update.message.reply_text.call_args[0][0]
        self.assertNotIn("מספר מנהלים: 0", call_args)
    
    async def test_my_requests_button_error_handling(self):
        """Test my requests button handles errors gracefully"""
        
        # Mock service to raise exception
        self.bot.user_service.get_user_requests.side_effect = Exception("DB Error")
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        handle_func = EnhancedPirateBot._handle_my_requests_button.__get__(self.bot)
        
        await handle_func(self.mock_query)
        
        # Should show error message, not crash
        self.mock_query.edit_message_text.assert_called()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("שגיאה בטעינת הבקשות", call_args)
    
    async def test_admin_button_non_admin_access(self):
        """Test admin buttons reject non-admin users"""
        
        self.bot._is_admin.return_value = False
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        admin_func = EnhancedPirateBot._handle_admin_button.__get__(self.bot)
        
        await admin_func(self.mock_query, "admin:pending")
        
        # Should reject access
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        self.assertIn("אין לך הרשאות מנהל", call_args)
    
    async def test_broadcast_command_non_admin_access(self):
        """Test broadcast command rejects non-admin users"""
        
        self.bot._is_admin.return_value = False
        self.mock_context.args = ["test", "message"]
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        broadcast_func = EnhancedPirateBot.broadcast_command.__get__(self.bot)
        
        await broadcast_func(self.mock_update, self.mock_context)
        
        # Should reject access
        call_args = self.mock_update.message.reply_text.call_args[0][0]
        self.assertIn("פקודה זמינה רק למנהלים", call_args)


class TestConfigurationIntegrity(unittest.TestCase):
    """Test configuration integrity"""
    
    def test_admin_ids_configured(self):
        """Test that admin IDs are properly configured"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
            
        # Should have the 3 admin IDs we configured
        expected_admins = [6039349310, 6562280181, 1667741867]
        
        self.assertEqual(len(ADMIN_IDS), 3)
        for admin_id in expected_admins:
            self.assertIn(admin_id, ADMIN_IDS)
    
    def test_main_group_configured(self):
        """Test that main group ID is configured"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
            
        self.assertIsNotNone(MAIN_GROUP_ID)
        self.assertIsInstance(MAIN_GROUP_ID, int)


if __name__ == '__main__':
    unittest.main()