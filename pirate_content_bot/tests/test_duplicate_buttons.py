#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים מקיפים לכפתורי הכפילויות
"""

import unittest
import asyncio
import os
import sys
import json
from unittest.mock import Mock, AsyncMock, patch
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

class TestDuplicateButtons(unittest.TestCase):
    """טסטים לכפתורי כפילויות"""
    
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
        
    async def test_create_duplicate_button_valid(self):
        """בדיקת כפתור יצירת כפילות עם נתונים תקינים"""
        user_id = self.mock_user.id
        
        # הכנת נתונים זמניים במטמון
        pending_data = {
            'original_text': 'בקשה לבדיקה',
            'analysis': {
                'title': 'בקשה לבדיקה',
                'category': 'general',
                'confidence': 0.9
            }
        }
        
        # Mock cache
        with patch.object(self.bot.cache_manager, 'get', return_value=pending_data), \
             patch.object(self.bot.cache_manager, 'delete'), \
             patch.object(self.bot.request_service, 'create_request', return_value=123):
            
            await self.bot._handle_create_duplicate_button(self.mock_callback_query, "create_duplicate:456")
            
            # וידוא שהפונקציה התבצעה
            self.mock_callback_query.edit_message_text.assert_called_once()
            call_args = self.mock_callback_query.edit_message_text.call_args[0][0]
            self.assertIn('בקשה נוצרה בהצלחה', call_args)
            self.assertIn('#123', call_args)
            
    async def test_create_duplicate_button_no_cache(self):
        """בדיקת כפתור יצירת כפילות ללא נתונים במטמון"""
        with patch.object(self.bot.cache_manager, 'get', return_value=None):
            
            await self.bot._handle_create_duplicate_button(self.mock_callback_query, "create_duplicate:456")
            
            # וידוא שהתקבלה הודעת שגיאה
            self.mock_callback_query.edit_message_text.assert_called_once()
            call_args = self.mock_callback_query.edit_message_text.call_args[0][0]
            self.assertIn('הבקשה לא נמצאה במטמון', call_args)
            
    async def test_create_duplicate_button_service_failure(self):
        """בדיקת כפתור יצירת כפילות כשהשירות נכשל"""
        pending_data = {
            'original_text': 'בקשה לבדיקה',
            'analysis': {'title': 'בקשה לבדיקה'}
        }
        
        with patch.object(self.bot.cache_manager, 'get', return_value=pending_data), \
             patch.object(self.bot.request_service, 'create_request', return_value=None):
            
            await self.bot._handle_create_duplicate_button(self.mock_callback_query, "create_duplicate:456")
            
            # וידוא שהתקבלה הודעת שגיאה
            self.mock_callback_query.edit_message_text.assert_called_once()
            call_args = self.mock_callback_query.edit_message_text.call_args[0][0]
            self.assertIn('שגיאה ביצירת הבקשה', call_args)
            
    async def test_view_request_button_valid_id(self):
        """בדיקת כפתור הצגת בקשה עם ID תקין"""
        request_data = {
            'id': 123,
            'title': 'בקשה לבדיקה',
            'status': 'pending',
            'priority': 'medium',
            'category': 'general',
            'first_name': 'משתמש',
            'created_at': '2025-09-08 15:00:00',
            'original_text': 'תוכן הבקשה המלא'
        }
        
        with patch.object(self.bot.request_service, 'get_request_by_id', return_value=request_data):
            
            await self.bot._handle_view_request_button(self.mock_callback_query, "view_request:123")
            
            # וידוא שהפונקציה התבצעה
            self.mock_callback_query.edit_message_text.assert_called_once()
            call_args = self.mock_callback_query.edit_message_text.call_args
            
            # בדיקת התוכן
            text = call_args[0][0]
            self.assertIn('פרטי בקשה #123', text)
            self.assertIn('בקשה לבדיקה', text)
            self.assertIn('pending', text)
            
            # בדיקת keyboard
            self.assertIn('reply_markup', call_args[1])
            
    async def test_view_request_button_not_found(self):
        """בדיקת כפתור הצגת בקשה - בקשה לא נמצאה"""
        with patch.object(self.bot.request_service, 'get_request_by_id', return_value={}):
            
            await self.bot._handle_view_request_button(self.mock_callback_query, "view_request:999")
            
            # וידוא שהתקבלה הודעת שגיאה
            self.mock_callback_query.edit_message_text.assert_called_once()
            call_args = self.mock_callback_query.edit_message_text.call_args[0][0]
            self.assertIn('בקשה #999 לא נמצאה', call_args)
            
    async def test_view_request_button_invalid_id(self):
        """בדיקת כפתור הצגת בקשה עם ID לא תקין"""
        await self.bot._handle_view_request_button(self.mock_callback_query, "view_request:")
        
        # וידוא שהתקבלה הודעת שגיאה
        self.mock_callback_query.edit_message_text.assert_called_once()
        call_args = self.mock_callback_query.edit_message_text.call_args[0][0]
        self.assertIn('מספר בקשה לא תקין', call_args)
        
    async def test_view_request_button_no_service(self):
        """בדיקת כפתור הצגת בקשה כשאין שירות"""
        # זמנית מבטל את השירות
        original_service = self.bot.request_service
        self.bot.request_service = None
        
        try:
            await self.bot._handle_view_request_button(self.mock_callback_query, "view_request:123")
            
            # וידוא שהתקבלה הודעת שגיאה
            self.mock_callback_query.edit_message_text.assert_called_once()
            call_args = self.mock_callback_query.edit_message_text.call_args[0][0]
            self.assertIn('שירות הבקשות אינו זמין', call_args)
        finally:
            self.bot.request_service = original_service
            
    async def test_duplicate_button_routing(self):
        """בדיקת ניתוב נכון לכפתורי כפילויות"""
        # Mock הפונקציות
        self.bot._handle_create_duplicate_button = AsyncMock()
        self.bot._handle_view_request_button = AsyncMock()
        
        # בדיקת create_duplicate
        self.mock_callback_query.data = "create_duplicate:123"
        await self.bot.enhanced_button_callback(self.mock_update, self.mock_context)
        self.bot._handle_create_duplicate_button.assert_called_once()
        
        # איפוס
        self.bot._handle_create_duplicate_button.reset_mock()
        self.bot._handle_view_request_button.reset_mock()
        
        # בדיקת view_request
        self.mock_callback_query.data = "view_request:456"
        await self.bot.enhanced_button_callback(self.mock_update, self.mock_context)
        self.bot._handle_view_request_button.assert_called_once()
        
    async def test_duplicate_notification_to_admins(self):
        """בדיקת התראה למנהלים על כפילות מכוונת"""
        user_id = self.mock_user.id
        
        pending_data = {
            'original_text': 'בקשה לבדיקה',
            'analysis': {'title': 'בקשה לבדיקה'}
        }
        
        # Mock notification service
        mock_notification = AsyncMock()
        self.bot.notification_service = Mock()
        self.bot.notification_service.notify_admins_new_request = mock_notification
        
        with patch.object(self.bot.cache_manager, 'get', return_value=pending_data), \
             patch.object(self.bot.cache_manager, 'delete'), \
             patch.object(self.bot.request_service, 'create_request', return_value=789):
            
            await self.bot._handle_create_duplicate_button(self.mock_callback_query, "create_duplicate:456")
            
            # וידוא שנשלחה התראה למנהלים
            mock_notification.assert_called_once()
            call_args = mock_notification.call_args
            self.assertEqual(call_args[0][0], 789)  # request_id
            self.assertEqual(call_args[1]['is_duplicate'], True)
            self.assertEqual(call_args[1]['original_id'], "456")
            
    async def test_force_duplicate_flag(self):
        """בדיקת סימון force_duplicate באנליזה"""
        user_id = self.mock_user.id
        
        pending_data = {
            'original_text': 'בקשה לבדיקה',
            'analysis': {'title': 'בקשה לבדיקה'}
        }
        
        mock_create_request = AsyncMock(return_value=999)
        
        with patch.object(self.bot.cache_manager, 'get', return_value=pending_data), \
             patch.object(self.bot.cache_manager, 'delete'), \
             patch.object(self.bot.request_service, 'create_request', mock_create_request):
            
            await self.bot._handle_create_duplicate_button(self.mock_callback_query, "create_duplicate:456")
            
            # בדיקה שהאנליזה כללה force_duplicate
            call_args = mock_create_request.call_args
            analysis = call_args[1]['analysis']
            self.assertTrue(analysis.get('force_duplicate', False))
            
    async def test_error_handling_in_duplicate_buttons(self):
        """בדיקת טיפול בשגיאות בכפתורי כפילויות"""
        
        # שגיאה בעיבוד כפתור create_duplicate
        with patch.object(self.bot.cache_manager, 'get', side_effect=Exception("Cache error")):
            await self.bot._handle_create_duplicate_button(self.mock_callback_query, "create_duplicate:123")
            
            self.mock_callback_query.edit_message_text.assert_called()
            call_args = self.mock_callback_query.edit_message_text.call_args[0][0]
            self.assertIn('שגיאה ביצירת בקשה כפולה', call_args)
            
        # איפוס
        self.mock_callback_query.edit_message_text.reset_mock()
        
        # שגיאה בעיבוד כפתור view_request  
        with patch.object(self.bot, 'request_service', side_effect=Exception("Service error")):
            await self.bot._handle_view_request_button(self.mock_callback_query, "view_request:123")
            
            self.mock_callback_query.edit_message_text.assert_called()
            call_args = self.mock_callback_query.edit_message_text.call_args[0][0]
            self.assertIn('שגיאה בהצגת הבקשה', call_args)
            
    async def test_get_request_by_id_functionality(self):
        """בדיקת פונקציית get_request_by_id"""
        if not self.bot.request_service:
            self.skipTest("Request service not available")
            
        # בדיקה שהפונקציה קיימת
        self.assertTrue(hasattr(self.bot.request_service, 'get_request_by_id'))
        self.assertTrue(callable(getattr(self.bot.request_service, 'get_request_by_id')))
        
        # בדיקה עם ID לא קיים
        try:
            result = await self.bot.request_service.get_request_by_id(99999)
            self.assertIsInstance(result, dict)
        except Exception as e:
            # צפוי כשאין DB
            self.assertIn('Failed to get connection', str(e))

async def run_async_tests():
    """הרצת טסטים אסינכרוניים"""
    print("🧪 Running duplicate button tests...")
    
    test_methods = [
        'test_create_duplicate_button_valid',
        'test_create_duplicate_button_no_cache',
        'test_create_duplicate_button_service_failure',
        'test_view_request_button_valid_id',
        'test_view_request_button_not_found',
        'test_view_request_button_invalid_id',
        'test_view_request_button_no_service',
        'test_duplicate_button_routing',
        'test_duplicate_notification_to_admins',
        'test_force_duplicate_flag',
        'test_error_handling_in_duplicate_buttons',
        'test_get_request_by_id_functionality'
    ]
    
    for test_method in test_methods:
        test_case = TestDuplicateButtons()
        test_case.setUp()
        
        try:
            await getattr(test_case, test_method)()
            print(f"✅ {test_method} passed")
        except Exception as e:
            print(f"❌ {test_method} failed: {e}")
    
    print("🎉 All duplicate button tests completed!")

if __name__ == "__main__":
    asyncio.run(run_async_tests())