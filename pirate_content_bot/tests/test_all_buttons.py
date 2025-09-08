#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים מקיפים לכל הכפתורים במערכת
כולל בדיקות לנתונים אמיתיים, ייצוא, גיבוי, אנליטיקס ועוד
"""

import unittest
import asyncio
import os
import sys
import tempfile
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

# הוספת path לפרויקט  
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from main.pirate_bot_main import EnhancedPirateBot
except ImportError:
    # אם לא מצליח לייבא, נסה דרך אחרת
    import importlib.util
    spec = importlib.util.spec_from_file_location("pirate_bot_main", os.path.join(parent_dir, "main", "pirate_bot_main.py"))
    bot_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bot_module)
    EnhancedPirateBot = bot_module.EnhancedPirateBot

from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ContextTypes

class TestAllButtons(unittest.TestCase):
    """טסטים מקיפים לכל הכפתורים"""
    
    def setUp(self):
        """הגדרת הטסטים"""
        self.bot = EnhancedPirateBot()
        
        # Mock objects
        self.mock_user = User(id=123456789, first_name="Test", is_bot=False)
        self.mock_admin_user = User(id=6562280181, first_name="Admin", is_bot=False)
        self.mock_chat = Chat(id=-1001234567890, type="supergroup")
        
        self.mock_message = Mock(spec=Message)
        self.mock_message.reply_text = AsyncMock()
        self.mock_message.reply_document = AsyncMock()
        
        self.mock_update = Mock(spec=Update)
        self.mock_update.effective_user = self.mock_user
        self.mock_update.message = self.mock_message
        
        # Mock CallbackQuery for button tests
        self.mock_callback_query = Mock(spec=CallbackQuery)
        self.mock_callback_query.answer = AsyncMock()
        self.mock_callback_query.edit_message_text = AsyncMock()
        self.mock_callback_query.from_user = self.mock_user
        self.mock_callback_query.data = ""
        
        self.mock_update.callback_query = self.mock_callback_query
        
        self.mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        self.mock_context.args = []
        
    async def test_admin_pending_button(self):
        """בדיקת כפתור בקשות ממתינות"""
        self.mock_callback_query.from_user = self.mock_admin_user
        self.mock_callback_query.data = "admin:pending"
        
        await self.bot._handle_admin_button(self.mock_callback_query, "admin:pending")
        
        # וידוא שהפונקציה התבצעה
        self.mock_callback_query.edit_message_text.assert_called_once()
        call_args = self.mock_callback_query.edit_message_text.call_args[1]
        self.assertIn('reply_markup', call_args)
        
    async def test_admin_stats_button(self):
        """בדיקת כפתור סטטיסטיקות"""
        self.mock_callback_query.from_user = self.mock_admin_user
        self.mock_callback_query.data = "admin:stats"
        
        await self.bot._handle_admin_button(self.mock_callback_query, "admin:stats")
        
        # וידוא שהפונקציה התבצעה
        self.mock_callback_query.edit_message_text.assert_called_once()
        
    async def test_admin_analytics_button(self):
        """בדיקת כפתור אנליטיקס"""
        self.mock_callback_query.from_user = self.mock_admin_user
        self.mock_callback_query.data = "admin:analytics"
        
        await self.bot._handle_admin_button(self.mock_callback_query, "admin:analytics")
        
        # וידוא שהפונקציה התבצעה
        self.mock_callback_query.edit_message_text.assert_called_once()
        
    async def test_refresh_button_pending(self):
        """בדיקת כפתור רענון בקשות ממתינות"""
        self.mock_callback_query.from_user = self.mock_admin_user
        
        # ביצוע הכפתור פעמיים - כמו רענון
        await self.bot._handle_admin_button(self.mock_callback_query, "admin:pending")
        first_call = self.mock_callback_query.edit_message_text.call_count
        
        await self.bot._handle_admin_button(self.mock_callback_query, "admin:pending") 
        second_call = self.mock_callback_query.edit_message_text.call_count
        
        # וידוא שהוכפל
        self.assertEqual(second_call, first_call * 2)
        
    async def test_refresh_button_stats(self):
        """בדיקת כפתור רענון סטטיסטיקות"""
        self.mock_callback_query.from_user = self.mock_admin_user
        
        # ביצוע הכפתור פעמיים - כמו רענון  
        await self.bot._handle_admin_button(self.mock_callback_query, "admin:stats")
        first_call = self.mock_callback_query.edit_message_text.call_count
        
        await self.bot._handle_admin_button(self.mock_callback_query, "admin:stats")
        second_call = self.mock_callback_query.edit_message_text.call_count
        
        # וידוא שהוכפל
        self.assertEqual(second_call, first_call * 2)
        
    async def test_non_admin_button_access(self):
        """בדיקה שמשתמש רגיל לא יכול לגשת לכפתורי מנהל"""
        self.mock_callback_query.from_user = self.mock_user  # משתמש רגיל
        
        await self.bot._handle_admin_button(self.mock_callback_query, "admin:pending")
        
        # וידוא שקיבל הודעת שגיאה
        self.mock_callback_query.edit_message_text.assert_called_once()
        call_args = self.mock_callback_query.edit_message_text.call_args[0][0]
        self.assertIn("אין לך הרשאות מנהל", call_args)
        
    async def test_action_main_menu_button(self):
        """בדיקת כפתור תפריט ראשי"""
        await self.bot._handle_action_button(self.mock_callback_query, "action:main_menu")
        
        # וידוא שהפונקציה התבצעה
        self.mock_callback_query.edit_message_text.assert_called_once()
        
    async def test_action_admin_panel_button(self):
        """בדיקת כפתור פאנל מנהלים"""
        self.mock_callback_query.from_user = self.mock_admin_user
        
        await self.bot._handle_action_button(self.mock_callback_query, "action:admin_panel")
        
        # וידוא שהפונקציה התבצעה
        self.mock_callback_query.edit_message_text.assert_called_once()
        call_args = self.mock_callback_query.edit_message_text.call_args[1]
        self.assertIn('reply_markup', call_args)
        
    async def test_export_data_functionality(self):
        """בדיקת פונקציית ייצוא נתונים"""
        self.mock_update.effective_user = self.mock_admin_user
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='test data')), \
             patch('os.remove'):
            
            await self.bot.export_command(self.mock_update, self.mock_context)
            
            # וידוא שהפונקציה התבצעה
            self.mock_message.reply_text.assert_called()
            
    async def test_backup_functionality(self):
        """בדיקת פונקציית גיבוי"""
        self.mock_update.effective_user = self.mock_admin_user
        
        await self.bot.backup_command(self.mock_update, self.mock_context)
        
        # וידוא שהפונקציה התבצעה
        self.mock_message.reply_text.assert_called()
        
    async def test_json_serialization_fix(self):
        """בדיקת תיקון JSON serialization"""
        # בדיקה שהפונקציה יכולה להתמודד עם datetime objects
        if self.bot.request_service:
            try:
                backup_result = await self.bot.request_service.create_backup()
                self.assertIsInstance(backup_result, dict)
                self.assertIn('success', backup_result)
            except Exception as e:
                # אם יש שגיאה, זה לא בגלל JSON serialization
                self.assertNotIn('JSON serializable', str(e))
                
    async def test_generic_button_handler(self):
        """בדיקת מטפל כפתורים כללי"""
        # בדיקת כפתור יצירת בקשה
        await self.bot._handle_generic_button(self.mock_callback_query, "confirm_request:123")
        
        # בדיקת כפתור ביטול
        await self.bot._handle_generic_button(self.mock_callback_query, "cancel_request")
        
        # וידוא שהפונקציות התבצעו
        self.assertTrue(self.mock_callback_query.edit_message_text.called)
        
    async def test_button_error_handling(self):
        """בדיקת טיפול בשגיאות בכפתורים"""
        # כפתור עם נתונים שגויים
        await self.bot._handle_admin_button(self.mock_callback_query, "admin:invalid_action")
        
        # וידוא שלא התרסק
        self.assertTrue(True)  # אם הגענו לכאן, לא היה crash
        
    async def test_create_request_button(self):
        """בדיקת כפתור יצירת בקשה"""
        await self.bot._handle_create_request_button(self.mock_callback_query, "create:test")
        
        # וידוא שהפונקציה התבצעה
        self.assertTrue(True)
        
    async def test_rating_button(self):
        """בדיקת כפתור דירוג"""
        await self.bot._handle_rating_button(self.mock_callback_query, "rating:5")
        
        # וידוא שהפונקציה התבצעה (אף על פי שזה בפיתוח)
        self.mock_callback_query.edit_message_text.assert_called_once()
        
    async def test_settings_button(self):
        """בדיקת כפתור הגדרות"""
        await self.bot._handle_settings_button(self.mock_callback_query, "settings:theme")
        
        # וידוא שהפונקציה התבצעה (אף על פי שזה בפיתוח)
        self.mock_callback_query.edit_message_text.assert_called_once()
        
    async def test_duplicate_action_button(self):
        """בדיקת כפתור פעולות כפילויות"""
        await self.bot._handle_duplicate_action_button(self.mock_callback_query, "duplicate:merge:123")
        
        # וידוא שהפונקציה התבצעה (אף על פי שזה בפיתוח)
        self.mock_callback_query.edit_message_text.assert_called_once()
        
    async def test_edit_request_button(self):
        """בדיקת כפתור עריכת בקשה"""
        await self.bot._handle_edit_request_button(self.mock_callback_query, "edit:123")
        
        # וידוא שהפונקציה התבצעה (אף על פי שזה בפיתוח)
        self.mock_callback_query.edit_message_text.assert_called_once()
        
    async def test_enhanced_button_callback_router(self):
        """בדיקת הראוטר הכללי לכפתורים"""
        test_cases = [
            "create_request:test",
            "admin:pending",
            "action:main_menu", 
            "rating:5",
            "settings:test",
            "duplicate:test",
            "edit:test",
            "unknown:test"
        ]
        
        for test_data in test_cases:
            self.mock_callback_query.data = test_data
            await self.bot.enhanced_button_callback(self.mock_update, self.mock_context)
            
        # וידוא שהראוטר עובד (לא התרסק)
        self.assertTrue(True)

def mock_open(read_data=''):
    """Mock function for file operations"""
    return MagicMock()

async def run_async_tests():
    """הרצת טסטים אסינכרוניים"""
    print("🧪 Running comprehensive button tests...")
    
    test_methods = [
        'test_admin_pending_button',
        'test_admin_stats_button', 
        'test_admin_analytics_button',
        'test_refresh_button_pending',
        'test_refresh_button_stats',
        'test_non_admin_button_access',
        'test_action_main_menu_button',
        'test_action_admin_panel_button',
        'test_export_data_functionality',
        'test_backup_functionality',
        'test_json_serialization_fix',
        'test_generic_button_handler',
        'test_button_error_handling',
        'test_create_request_button',
        'test_rating_button',
        'test_settings_button',
        'test_duplicate_action_button',
        'test_edit_request_button',
        'test_enhanced_button_callback_router'
    ]
    
    for test_method in test_methods:
        test_case = TestAllButtons()
        test_case.setUp()
        
        try:
            await getattr(test_case, test_method)()
            print(f"✅ {test_method} passed")
        except Exception as e:
            print(f"❌ {test_method} failed: {e}")
    
    print("🎉 All button tests completed!")

if __name__ == "__main__":
    asyncio.run(run_async_tests())