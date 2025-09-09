#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים לבדיקת פונקציונליות המרת זמנים לאזור הזמן הישראלי
"""

import unittest
import os
import sys
from datetime import datetime, timezone
from unittest.mock import Mock, patch

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(parent_dir)
sys.path.insert(0, project_root)

try:
    from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Import warning: {e}")
    IMPORTS_AVAILABLE = False


class TestTimezoneConversion(unittest.TestCase):
    """Test timezone conversion to Israel time"""
    
    def setUp(self):
        """Setup for each test"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
        
        self.bot = Mock()
        self.bot._convert_to_israel_time = EnhancedPirateBot._convert_to_israel_time.__get__(self.bot)
    
    def test_convert_utc_string_to_israel_time(self):
        """Test conversion of UTC string to Israel time"""
        # UTC time: 2024-01-15 12:00:00 
        # Israel time in winter (UTC+2): 2024-01-15 14:00:00
        # Israel time in summer (UTC+3): 2024-01-15 15:00:00
        utc_string = "2024-01-15T12:00:00Z"
        result = self.bot._convert_to_israel_time(utc_string, '%d/%m/%Y %H:%M')
        
        # The result should be in Israel time
        self.assertIsInstance(result, str)
        self.assertIn("15/01/2024", result)  # Date should be correct
        # Time should be 14:00 (winter) or 15:00 (summer) depending on DST
        self.assertTrue("14:00" in result or "15:00" in result)
    
    def test_convert_datetime_object_to_israel_time(self):
        """Test conversion of datetime object to Israel time"""
        import pytz
        utc_dt = datetime(2024, 6, 15, 12, 0, 0, tzinfo=pytz.UTC)  # Summer time
        result = self.bot._convert_to_israel_time(utc_dt, '%d/%m/%Y %H:%M')
        
        self.assertIsInstance(result, str)
        self.assertIn("15/06/2024", result)  # Date should be correct
        self.assertIn("15:00", result)  # Summer time: UTC+3
    
    def test_convert_naive_datetime_to_israel_time(self):
        """Test conversion of naive datetime (assumed UTC) to Israel time"""
        naive_dt = datetime(2024, 1, 15, 12, 0, 0)  # No timezone info
        result = self.bot._convert_to_israel_time(naive_dt, '%d/%m/%Y %H:%M')
        
        self.assertIsInstance(result, str)
        self.assertIn("15/01/2024", result)
        # Should assume UTC and convert to Israel time
        self.assertTrue("14:00" in result or "15:00" in result)
    
    def test_convert_with_custom_format(self):
        """Test conversion with custom format string"""
        utc_string = "2024-01-15T12:00:00Z"
        result = self.bot._convert_to_israel_time(utc_string, '%d/%m/%Y')
        
        # Should return only date, no time
        self.assertEqual(result, "15/01/2024")
    
    def test_handle_none_input(self):
        """Test handling of None input"""
        result = self.bot._convert_to_israel_time(None)
        self.assertEqual(result, "לא ידוע")
    
    def test_handle_invalid_string(self):
        """Test handling of invalid string input"""
        result = self.bot._convert_to_israel_time("invalid-date-string")
        
        # Should fallback gracefully
        self.assertIsInstance(result, str)
        # Should return something meaningful, not crash
        self.assertNotEqual(result, "")
    
    def test_summer_vs_winter_time(self):
        """Test that summer/winter time conversion works correctly"""
        # Winter time test (January - UTC+2)
        winter_utc = "2024-01-15T10:00:00Z"
        winter_result = self.bot._convert_to_israel_time(winter_utc, '%H:%M')
        
        # Summer time test (July - UTC+3)  
        summer_utc = "2024-07-15T10:00:00Z"
        summer_result = self.bot._convert_to_israel_time(summer_utc, '%H:%M')
        
        # Winter should be UTC+2 (12:00), summer should be UTC+3 (13:00)
        self.assertEqual(winter_result, "12:00")
        self.assertEqual(summer_result, "13:00")


class TestStatusCommandTimezone(unittest.IsolatedAsyncioTestCase):
    """Test that status command shows Israel time"""
    
    async def asyncSetUp(self):
        """Setup for async tests"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
        
        # Create a mock bot with the conversion method
        self.bot = Mock()
        self.bot._convert_to_israel_time = EnhancedPirateBot._convert_to_israel_time.__get__(self.bot)
    
    def test_status_command_uses_israel_time(self):
        """Test that status command formats time correctly for Israel"""
        # Mock request info with UTC time
        request_info = {
            'id': 123,
            'status': 'pending',
            'title': 'Test Request',
            'category': 'movies',
            'created_at': '2024-01-15T12:00:00Z'
        }
        
        # Test the conversion that status command would use
        date_str = self.bot._convert_to_israel_time(request_info['created_at'], '%d/%m/%Y %H:%M')
        
        # Should show Israel time, not UTC
        self.assertIn("15/01/2024", date_str)
        self.assertTrue("14:00" in date_str or "15:00" in date_str)  # UTC+2 or UTC+3
        # Should NOT show 12:00 (which would be UTC time)
        self.assertNotIn("12:00", date_str)


class TestAllCommandsTimezone(unittest.TestCase):
    """Test that all commands that show time use Israel timezone"""
    
    def setUp(self):
        """Setup for timezone tests"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
        
        self.bot = Mock()
        self.bot._convert_to_israel_time = EnhancedPirateBot._convert_to_israel_time.__get__(self.bot)
    
    def test_consistent_timezone_usage(self):
        """Test that all time displays are consistent with Israel timezone"""
        test_utc_time = "2024-06-15T09:00:00Z"  # 9 AM UTC in summer
        
        # Test different format strings used in different commands
        status_format = self.bot._convert_to_israel_time(test_utc_time, '%d/%m/%Y %H:%M')
        search_format = self.bot._convert_to_israel_time(test_utc_time, '%d/%m/%Y')
        myreq_format = self.bot._convert_to_israel_time(test_utc_time, '%d/%m/%Y')
        
        # All should show same date
        self.assertIn("15/06/2024", status_format)
        self.assertEqual(search_format, "15/06/2024")
        self.assertEqual(myreq_format, "15/06/2024")
        
        # Status format should show 12:00 (9 AM UTC + 3 hours for summer time)
        self.assertIn("12:00", status_format)


if __name__ == '__main__':
    # Install pytz if not available for tests
    try:
        import pytz
    except ImportError:
        print("⚠️ pytz not available, timezone tests may fail")
    
    unittest.main()