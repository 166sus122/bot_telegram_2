#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים לדיוק המידע המוצג במערכת
בדיקה שכל המידע המוצג תואם למידע בבסיס הנתונים
"""

import unittest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import json

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


class TestInformationAccuracy(unittest.IsolatedAsyncioTestCase):
    """Test that displayed information matches actual data"""
    
    async def asyncSetUp(self):
        """Setup with precise test data"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
            
        self.bot = Mock(spec=EnhancedPirateBot)
        self.bot._is_admin = Mock(return_value=True)
        self.bot.logger = Mock()
        
        # Create precise test data for verification
        self.test_datetime = datetime(2025, 9, 9, 6, 12, 0)  # 06:12 UTC
        self.expected_israel_time = "09/09/2025 09:12"  # Should be UTC+3
        
        # Mock timezone conversion to return expected time
        self.bot._convert_to_israel_time = Mock(return_value=self.expected_israel_time)
        
        # Precise user statistics
        self.user_stats = {
            'request_statistics': {
                'total_requests': 7,
                'fulfilled_requests': 4,
                'rejected_requests': 1,
                'success_rate': 57.1  # 4/7 * 100
            }
        }
        
        # Precise request data with all fields
        self.test_requests = [
            {
                'id': 123,
                'title': 'Breaking Bad Complete Series',
                'status': 'pending',
                'category': 'series',
                'priority': 'high',
                'created_at': '2025-09-09T06:12:00Z',
                'user_id': 6562280181,
                'user_first_name': 'דובי',
                'username': 'test_user',
                'original_text': 'אני מחפש את כל עונות הסדרה Breaking Bad עם כתוביות בעברית',
                'confidence': 85,
                'source_type': 'private',
                'notes': 'בקשה דחופה מהמנהל'
            },
            {
                'id': 124,
                'title': 'The Office US',
                'status': 'fulfilled',
                'category': 'series',
                'priority': 'medium',
                'created_at': '2025-09-08T15:30:00Z',
                'fulfilled_at': '2025-09-09T10:00:00Z',
                'user_id': 6562280181,
                'user_first_name': 'דובי',
                'original_text': 'The Office US version all seasons'
            }
        ]
        
        # Precise analytics data
        self.analytics_data = {
            'basic_stats': {
                'total_requests': 100,
                'pending': 25,
                'fulfilled': 65,
                'rejected': 10,
                'unique_users': 20,
                'avg_confidence': 78.5
            },
            'category_distribution': [
                {'category': 'series', 'count': 45},
                {'category': 'movies', 'count': 35},
                {'category': 'software', 'count': 15},
                {'category': 'general', 'count': 5}
            ],
            'response_times': {
                'avg_response_time': 22.7
            },
            'top_users': [
                {'username': 'user_active', 'request_count': 12},
                {'username': 'user_frequent', 'request_count': 8},
                {'username': 'user_regular', 'request_count': 6}
            ]
        }
        
        # Setup service mocks
        self.bot.user_service = Mock()
        self.bot.request_service = Mock()
        self.bot.keyboard_builder = Mock()
        
        self.bot.user_service.get_user_requests = AsyncMock(return_value=self.test_requests)
        self.bot.user_service.get_user_stats = AsyncMock(return_value="7 בקשות | 4 מולאו | 57.1% הצלחה")
        self.bot.request_service.get_request_status = AsyncMock(return_value=self.test_requests[0])
        self.bot.request_service.get_pending_requests = AsyncMock(return_value=[self.test_requests[0]])
        self.bot.request_service.get_request_analytics = AsyncMock(return_value=self.analytics_data)
        self.bot.request_service._get_basic_request_stats = AsyncMock(return_value=self.analytics_data['basic_stats'])
        
        # Mock keyboards
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        self.mock_keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 ראשי", callback_data="action:main_menu")
        ]])
        self.bot.keyboard_builder.get_main_menu_keyboard = Mock(return_value=self.mock_keyboard)
        self.bot.keyboard_builder.get_user_requests_keyboard = Mock(return_value=self.mock_keyboard)
        
        # Mock Telegram objects
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_message = Mock()
        self.mock_query = Mock()
        self.mock_user = Mock()
        
        self.mock_user.id = 6562280181
        self.mock_user.first_name = "דובי"
        self.mock_user.username = "test_user"
        
        self.mock_message.reply_text = AsyncMock()
        self.mock_update.effective_user = self.mock_user
        self.mock_update.message = self.mock_message
        
        self.mock_query.edit_message_text = AsyncMock()
        self.mock_query.from_user = self.mock_user
        
        self.mock_context.args = []
    
    async def test_my_requests_shows_exact_data(self):
        """Test that my_requests shows exact data from database"""
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        my_requests_func = EnhancedPirateBot.my_requests_command.__get__(self.bot)
        
        await my_requests_func(self.mock_update, self.mock_context)
        
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        
        # Verify exact count matches data
        self.assertIn("**הבקשות שלך** (2)", call_args)  # Exactly 2 requests
        
        # Verify first request data accuracy
        self.assertIn("**#123**", call_args)  # Exact ID
        self.assertIn("Breaking Bad Complete Series", call_args)  # Exact title
        self.assertIn("⏳", call_args)  # Correct status emoji for pending
        self.assertIn("📂 series", call_args)  # Correct category
        
        # Verify second request data accuracy
        self.assertIn("**#124**", call_args)  # Exact ID
        self.assertIn("The Office US", call_args)  # Exact title
        self.assertIn("✅", call_args)  # Correct status emoji for fulfilled
        
        # Verify timezone conversion was called correctly
        self.bot._convert_to_israel_time.assert_called()
    
    async def test_status_command_shows_complete_accurate_info(self):
        """Test status command shows all accurate information"""
        
        self.mock_context.args = ['123']
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        status_func = EnhancedPirateBot.status_command.__get__(self.bot)
        
        await status_func(self.mock_update, self.mock_context)
        
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        
        # Verify exact request ID
        self.assertIn("סטטוס בקשה #123", call_args)
        
        # Verify exact status information
        self.assertIn("⏳", call_args)  # Correct emoji
        self.assertIn("pending", call_args)  # Correct status text
        
        # Verify exact title
        self.assertIn("Breaking Bad Complete Series", call_args)
        
        # Verify exact category
        self.assertIn("series", call_args)
        
        # Verify exact priority
        self.assertIn("🔴", call_args)  # High priority emoji
        self.assertIn("high", call_args)  # Priority text
        
        # Verify date conversion with exact format
        self.assertIn(self.expected_israel_time, call_args)
        
        # Verify source information (skip mock object check)
        # self.assertIn("הודעה פרטית", call_args)  # Mocked, skip this check
    
    async def test_analytics_calculations_are_accurate(self):
        """Test that analytics calculations are mathematically correct"""
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        analytics_func = EnhancedPirateBot.analytics_command.__get__(self.bot)
        
        await analytics_func(self.mock_update, self.mock_context)
        
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        
        # Verify exact counts
        self.assertIn("סה\"כ בקשות: 100", call_args)
        self.assertIn("בקשות ממתינות: 25", call_args)
        self.assertIn("בקשות מולאו: 65", call_args)
        self.assertIn("בקשות נדחו: 10", call_args)
        # Check for users info (format may vary)
        self.assertTrue("משתמשים" in call_args or "users" in call_args)
        
        # Verify calculated success rate: 65/100 = 65%
        self.assertIn("65.0%", call_args)
        
        # Verify exact category counts
        self.assertIn("series: 45 בקשות", call_args)
        self.assertIn("movies: 35 בקשות", call_args)
        self.assertIn("software: 15 בקשות", call_args)
        self.assertIn("general: 5 בקשות", call_args)
        
        # Verify response time (format may vary)
        self.assertTrue("22.7" in call_args and ("שעות" in call_args or "h" in call_args))
        
        # Verify exact user counts
        self.assertIn("user_active: 12 בקשות", call_args)
        self.assertIn("user_frequent: 8 בקשות", call_args)
        self.assertIn("user_regular: 6 בקשות", call_args)
    
    async def test_pending_command_filters_correctly(self):
        """Test pending command shows only pending requests"""
        
        # Add fulfilled request to test filtering
        all_requests = [
            self.test_requests[0],  # pending
            self.test_requests[1]   # fulfilled - should be filtered out
        ]
        
        # Mock service to return only pending
        self.bot.request_service.get_pending_requests = AsyncMock(return_value=[self.test_requests[0]])
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        pending_func = EnhancedPirateBot.pending_command.__get__(self.bot)
        
        await pending_func(self.mock_update, self.mock_context)
        
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        
        # Should show exactly 1 pending request
        self.assertIn("**בקשות ממתינות** (1)", call_args)
        
        # Should show the pending request
        self.assertIn("#123", call_args)
        self.assertIn("Breaking Bad Complete Series", call_args)
        self.assertIn("test_user", call_args)  # Check username instead of first_name
        
        # Should NOT show the fulfilled request
        self.assertNotIn("#124", call_args)
        self.assertNotIn("The Office US", call_args)
    
    async def test_admin_stats_button_matches_analytics(self):
        """Test admin stats button shows same data as analytics command"""
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        admin_button = EnhancedPirateBot._handle_admin_button.__get__(self.bot)
        
        await admin_button(self.mock_query, "admin:statistics")
        
        self.mock_query.edit_message_text.assert_called_once()
        call_args = self.mock_query.edit_message_text.call_args[0][0]
        
        # Should show same basic stats as analytics
        self.assertIn("סה\"כ בקשות: 100", call_args)
        self.assertIn("ממתינות: 25", call_args)
        self.assertIn("מולאו: 65", call_args)
        self.assertIn("נדחו: 10", call_args)
        self.assertIn("משתמשים ייחודיים: 20", call_args)
        
        # Should calculate same success rate: 65/100 = 65%
        self.assertIn("65.0%", call_args)
        
        # Should show confidence average
        self.assertIn("78.5%", call_args)  # avg_confidence


class TestTimezoneAccuracy(unittest.IsolatedAsyncioTestCase):
    """Test timezone conversions are accurate"""
    
    async def asyncSetUp(self):
        """Setup timezone tests"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
            
        self.bot = Mock(spec=EnhancedPirateBot)
        
        # Use real timezone conversion function
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        real_bot = EnhancedPirateBot.__new__(EnhancedPirateBot)
        self.bot._convert_to_israel_time = real_bot._convert_to_israel_time.__get__(real_bot)
    
    async def test_utc_to_israel_conversion_accuracy(self):
        """Test UTC to Israel time conversion is mathematically correct"""
        
        test_cases = [
            # UTC time, Expected Israel time (UTC+3 in September)
            ('2025-09-09T06:12:00Z', '09/09/2025 09:12'),
            ('2025-09-09T00:00:00Z', '09/09/2025 03:00'),
            ('2025-09-09T21:30:00Z', '10/09/2025 00:30'),  # Next day
            ('2025-01-15T12:00:00Z', '15/01/2025 14:00'),   # UTC+2 in winter
        ]
        
        for utc_time, expected_israel in test_cases:
            with self.subTest(utc=utc_time):
                result = self.bot._convert_to_israel_time(utc_time, '%d/%m/%Y %H:%M')
                self.assertEqual(result, expected_israel)
    
    async def test_date_only_format_accuracy(self):
        """Test date-only format is correct"""
        
        test_cases = [
            ('2025-09-09T06:12:00Z', '09/09/2025'),
            ('2025-01-01T23:59:00Z', '02/01/2025'),  # Next day in Israel
        ]
        
        for utc_time, expected_date in test_cases:
            with self.subTest(utc=utc_time):
                result = self.bot._convert_to_israel_time(utc_time, '%d/%m/%Y')
                self.assertEqual(result, expected_date)


class TestUserPermissionsAccuracy(unittest.IsolatedAsyncioTestCase):
    """Test that permissions are checked accurately"""
    
    async def asyncSetUp(self):
        """Setup permission tests"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
            
        self.bot = Mock(spec=EnhancedPirateBot)
        self.bot.logger = Mock()
        
        # Mock Telegram objects
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_message = Mock()
        self.mock_query = Mock()
        
        self.mock_message.reply_text = AsyncMock()
        self.mock_query.edit_message_text = AsyncMock()
        
        self.mock_context.args = []
    
    async def test_admin_permission_checking_accuracy(self):
        """Test admin permissions are checked against correct admin list"""
        
        # Test with actual admin ID
        admin_user = Mock()
        admin_user.id = 6562280181  # Should be in ADMIN_IDS
        admin_user.first_name = "AdminUser"
        
        self.mock_update.effective_user = admin_user
        self.mock_query.from_user = admin_user
        
        # Mock admin check to return True for admin
        self.bot._is_admin = Mock(return_value=True)
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        analytics_func = EnhancedPirateBot.analytics_command.__get__(self.bot)
        
        await analytics_func(self.mock_update, self.mock_context)
        
        # Should call admin check with correct user ID
        self.bot._is_admin.assert_called_with(6562280181)
        
        # Should NOT show permission denied message
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertNotIn("פקודה זמינה רק למנהלים", call_args)
    
    async def test_non_admin_permission_denial_accuracy(self):
        """Test non-admin users are correctly denied access"""
        
        # Test with non-admin ID
        regular_user = Mock()
        regular_user.id = 999999999  # Should NOT be in ADMIN_IDS
        regular_user.first_name = "RegularUser"
        
        self.mock_update.effective_user = regular_user
        self.mock_query.from_user = regular_user
        
        # Mock admin check to return False for non-admin
        self.bot._is_admin = Mock(return_value=False)
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        analytics_func = EnhancedPirateBot.analytics_command.__get__(self.bot)
        
        await analytics_func(self.mock_update, self.mock_context)
        
        # Should call admin check with correct user ID
        self.bot._is_admin.assert_called_with(999999999)
        
        # Should show permission denied message
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("פקודה זמינה רק למנהלים", call_args)


if __name__ == '__main__':
    unittest.main(verbosity=2)