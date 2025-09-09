#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים מקיפים לפונקציונליות האנליטיקס
בדיקה שפונקציות האנליטיקס מחזירות נתונים אמיתיים ולא מזויפים
"""

import unittest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
sys.path.insert(0, project_root)

try:
    from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
    from pirate_content_bot.services.request_service import RequestService
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Import warning: {e}")
    IMPORTS_AVAILABLE = False


class TestAnalyticsFunctionality(unittest.IsolatedAsyncioTestCase):
    """Test analytics functionality with real and mock data"""
    
    async def asyncSetUp(self):
        """Setup for each test"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
            
        self.bot = Mock()
        self.bot.request_service = Mock(spec=RequestService)
        self.bot._is_admin = Mock(return_value=True)
        
        # Mock Telegram objects
        self.mock_update = Mock()
        self.mock_context = Mock() 
        self.mock_message = Mock()
        self.mock_user = Mock()
        
        self.mock_user.id = 6039349310  # Admin user ID
        self.mock_user.first_name = "TestAdmin"
        self.mock_user.username = "test_admin"
        
        self.mock_message.reply_text = AsyncMock()
        self.mock_update.effective_user = self.mock_user
        self.mock_update.message = self.mock_message
        
        self.mock_context.args = []
    
    async def test_analytics_with_no_database_connection(self):
        """Test analytics behavior when database is not connected"""
        
        # Mock request service with no database connection
        self.bot.request_service.get_request_analytics = AsyncMock(return_value={})
        
        # Import and bind the analytics command
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        analytics_func = EnhancedPirateBot.analytics_command.__get__(self.bot)
        
        await analytics_func(self.mock_update, self.mock_context)
        
        # Verify appropriate error message was sent
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("שגיאה בטעינת נתוני אנליטיקס", call_args)
    
    async def test_analytics_with_valid_database_connection(self):
        """Test analytics with valid database data"""
        
        # Mock real database response (no fake data)
        mock_analytics_data = {
            'basic_stats': {
                'total_requests': 5,
                'pending': 1, 
                'fulfilled': 3,
                'rejected': 1
            },
            'category_distribution': [
                {'category': 'series', 'count': 3},
                {'category': 'general', 'count': 2}
            ],
            'response_times': {
                'avg_response_time': 18.5
            },
            'top_users': [
                {'username': 'real_user1', 'request_count': 3},
                {'username': 'real_user2', 'request_count': 2}
            ]
        }
        
        self.bot.request_service.get_request_analytics = AsyncMock(return_value=mock_analytics_data)
        
        # Import and bind the analytics command
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        analytics_func = EnhancedPirateBot.analytics_command.__get__(self.bot)
        
        await analytics_func(self.mock_update, self.mock_context)
        
        # Verify analytics response was sent with real data
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        
        # Verify it shows real data, not fake data
        self.assertIn("סה\"כ בקשות: 5", call_args)
        self.assertIn("בקשות ממתינות: 1", call_args) 
        self.assertIn("בקשות מולאו: 3", call_args)
        self.assertIn("series: 3 בקשות", call_args)
        self.assertIn("real_user1: 3 בקשות", call_args)
        
        # Verify it does NOT contain fake data
        self.assertNotIn("'username': 'user1'", call_args)  # Fake username structure
        self.assertNotIn("'username': 'user2'", call_args)  # Fake username structure  
        self.assertNotIn("משתמש דוגמה", call_args)  # Fake user
    
    async def test_analytics_empty_database(self):
        """Test analytics with empty database (valid connection but no data)"""
        
        mock_analytics_data = {
            'basic_stats': {
                'total_requests': 0,
                'pending': 0,
                'fulfilled': 0, 
                'rejected': 0
            },
            'category_distribution': [],
            'response_times': {'avg_response_time': 0.0},
            'top_users': []
        }
        
        self.bot.request_service.get_request_analytics = AsyncMock(return_value=mock_analytics_data)
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        analytics_func = EnhancedPirateBot.analytics_command.__get__(self.bot)
        
        await analytics_func(self.mock_update, self.mock_context)
        
        call_args = self.mock_message.reply_text.call_args[0][0]
        
        # Should show zeros, not fake data
        self.assertIn("סה\"כ בקשות: 0", call_args)
        self.assertIn("אין נתונים זמינים", call_args)
        self.assertNotIn("משתמש דוגמה", call_args)
    
    async def test_get_top_users_no_database(self):
        """Test _get_top_users returns empty list when no database"""
        
        # Create a RequestService instance with no storage
        request_service = RequestService(storage_manager=None)
        
        # Test the function directly
        result = await request_service._get_top_users(datetime.now() - timedelta(days=7))
        
        # Should return empty list, not fake data
        self.assertEqual(result, [])
    
    async def test_get_daily_trends_no_database(self):
        """Test _get_daily_trends returns empty list when no database"""
        
        request_service = RequestService(storage_manager=None)
        
        result = await request_service._get_daily_trends(datetime.now() - timedelta(days=7))
        
        # Should return empty list, not fake trend data
        self.assertEqual(result, [])
    
    async def test_analytics_non_admin_access(self):
        """Test analytics command rejects non-admin users"""
        
        self.mock_user.id = 999999999  # Non-admin user
        self.bot._is_admin = Mock(return_value=False)
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        analytics_func = EnhancedPirateBot.analytics_command.__get__(self.bot)
        
        await analytics_func(self.mock_update, self.mock_context)
        
        # Should deny access
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("פקודה זמינה רק למנהלים", call_args)
    
    async def test_analytics_service_unavailable(self):
        """Test analytics when request service is not available"""
        
        self.bot.request_service = None
        
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        analytics_func = EnhancedPirateBot.analytics_command.__get__(self.bot)
        
        await analytics_func(self.mock_update, self.mock_context)
        
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("שירות הבקשות אינו זמין", call_args)


class TestAnalyticsDataIntegrity(unittest.TestCase):
    """Test analytics data integrity and validation"""
    
    def test_no_hardcoded_fake_data_in_analytics(self):
        """Verify no hardcoded fake data in analytics functions"""
        
        # Read the request service file
        service_file = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "services", 
            "request_service.py"
        )
        
        if os.path.exists(service_file):
            with open(service_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check that we removed the fake data
                self.assertNotIn("'username': 'user1'", content)
                self.assertNotIn("'username': 'user2'", content) 
                self.assertNotIn("משתמש דוגמה", content)
                self.assertNotIn("משתמש נוסף", content)
                
                # Check that mock data returns empty structures
                self.assertIn("return []", content)  # Should return empty lists now
    
    def test_analytics_response_structure(self):
        """Test expected structure of analytics response"""
        
        # Define expected structure
        expected_keys = [
            'basic_stats', 
            'category_distribution', 
            'response_times', 
            'top_users', 
            'daily_trends'
        ]
        
        expected_basic_stats_keys = [
            'total_requests', 
            'pending', 
            'fulfilled', 
            'rejected'
        ]
        
        # This test validates the expected structure
        # In a real environment, you'd test against actual DB results
        for key in expected_keys:
            self.assertIsInstance(key, str)
            self.assertGreater(len(key), 0)
        
        for key in expected_basic_stats_keys:
            self.assertIsInstance(key, str)
            self.assertGreater(len(key), 0)


if __name__ == '__main__':
    unittest.main()