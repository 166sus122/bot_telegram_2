#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים לפקודות שתוקנו: search, analytics, broadcast
"""

import unittest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch

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
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes

class TestFixedCommands(unittest.TestCase):
    """טסטים לפקודות שתוקנו"""
    
    def setUp(self):
        """הגדרת הטסטים"""
        self.bot = EnhancedPirateBot()
        
        # Mock objects
        self.mock_user = User(id=123456789, first_name="Test", is_bot=False)  # משתמש רגיל
        self.mock_admin_user = User(id=6562280181, first_name="Admin", is_bot=False)  # מנהל אמיתי
        self.mock_chat = Chat(id=-1001234567890, type="supergroup")
        self.mock_message = Mock(spec=Message)
        self.mock_message.reply_text = AsyncMock()
        
        self.mock_update = Mock(spec=Update)
        self.mock_update.effective_user = self.mock_user
        self.mock_update.message = self.mock_message
        
        self.mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        self.mock_context.args = []
        
    def test_is_admin_function_safety(self):
        """בדיקה שפונקצית _is_admin לא קורסת"""
        # משתמש רגיל (לא מנהל)
        self.assertFalse(self.bot._is_admin(123456789))
        
        # מנהל אמיתי
        self.assertTrue(self.bot._is_admin(6562280181))
        
        # בדיקה עם None
        self.assertFalse(self.bot._is_admin(None))
        
    async def test_search_command_no_args(self):
        """בדיקה שפקודת חיפוש בלי ארגומנטים מחזירה הוראות (מנהל)"""
        # הגדרת משתמש מנהל
        self.mock_update.effective_user = self.mock_admin_user
        
        await self.bot.search_command(self.mock_update, self.mock_context)
        
        # בדיקה שנשלחה הודעה
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("שימוש בחיפוש", call_args)
        
    async def test_search_command_with_args(self):
        """בדיקה שפקודת חיפוש עם ארגומנטים עובדת (מנהל)"""
        # הגדרת משתמש מנהל
        self.mock_update.effective_user = self.mock_admin_user
        self.mock_context.args = ["Breaking", "Bad"]
        
        await self.bot.search_command(self.mock_update, self.mock_context)
        
        # בדיקה שנשלחו הודעות (אמור להיות 2: הוראות + תוצאה)
        self.assertTrue(self.mock_message.reply_text.call_count >= 1)
        
    async def test_analytics_command_non_admin(self):
        """בדיקה שפקודת אנליטיקס דוחה משתמש רגיל"""
        # יצירת משתמש שלא מנהל
        from telegram import User
        non_admin_user = User(id=999999999, first_name="NonAdmin", is_bot=False)
        self.mock_update.effective_user = non_admin_user
        
        await self.bot.analytics_command(self.mock_update, self.mock_context)
        
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("פקודה זמינה רק למנהלים", call_args)
        
    async def test_analytics_command_admin_no_service(self):
        """בדיקה שפקודת אנליטיקס מטפלת בחוסר שירות"""
        self.mock_update.effective_user = self.mock_admin_user
        
        # בטל זמנית את ה-request_service
        original_service = self.bot.request_service
        self.bot.request_service = None
        
        try:
            await self.bot.analytics_command(self.mock_update, self.mock_context)
            
            self.mock_message.reply_text.assert_called_once()
            call_args = self.mock_message.reply_text.call_args[0][0]
            self.assertIn("שירות הבקשות אינו זמין", call_args)
        finally:
            self.bot.request_service = original_service
            
    async def test_broadcast_command_non_admin(self):
        """בדיקה שפקודת שידור דוחה משתמש רגיל"""
        # הבטחה שהמשתמש אינו מנהל
        from telegram import User
        non_admin_user = User(id=999999999, first_name="NonAdmin", is_bot=False)
        self.mock_update.effective_user = non_admin_user
        
        await self.bot.broadcast_command(self.mock_update, self.mock_context)
        
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("פקודה זמינה רק למנהלים", call_args)
        
    async def test_broadcast_command_admin_no_args(self):
        """בדיקה שפקודת שידור מציגה הוראות בלי ארגומנטים"""
        self.mock_update.effective_user = self.mock_admin_user
        
        await self.bot.broadcast_command(self.mock_update, self.mock_context)
        
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn("שימוש בשידור", call_args)
        
    async def test_broadcast_command_admin_no_notification_service(self):
        """בדיקה שפקודת שידור מטפלת בחוסר שירות התראות"""
        self.mock_update.effective_user = self.mock_admin_user
        self.mock_context.args = ["test", "message"]
        
        # בטל זמנית את ה-notification_service
        original_service = self.bot.notification_service
        self.bot.notification_service = None
        
        try:
            await self.bot.broadcast_command(self.mock_update, self.mock_context)
            
            self.mock_message.reply_text.assert_called_once()
            call_args = self.mock_message.reply_text.call_args[0][0]
            self.assertIn("שירות השידורים אינו זמין", call_args)
        finally:
            self.bot.notification_service = original_service

async def run_async_tests():
    """הרצת טסטים אסינכרוניים"""
    print("🧪 Running tests for fixed commands...")
    
    # טסט 1
    test_case = TestFixedCommands()
    test_case.setUp()
    test_case.test_is_admin_function_safety()
    print("✅ Admin function safety test passed")
    
    # טסט 2
    test_case = TestFixedCommands()
    test_case.setUp()
    await test_case.test_search_command_no_args()
    print("✅ Search command (no args) test passed")
    
    # טסט 3
    test_case = TestFixedCommands()
    test_case.setUp()
    await test_case.test_search_command_with_args()
    print("✅ Search command (with args) test passed")
    
    # טסט 4
    test_case = TestFixedCommands()
    test_case.setUp()
    await test_case.test_analytics_command_non_admin()
    print("✅ Analytics command (non-admin) test passed")
    
    # טסט 5
    test_case = TestFixedCommands()
    test_case.setUp()
    await test_case.test_analytics_command_admin_no_service()
    print("✅ Analytics command (admin, no service) test passed")
    
    # טסט 6
    test_case = TestFixedCommands()
    test_case.setUp()
    await test_case.test_broadcast_command_non_admin()
    print("✅ Broadcast command (non-admin) test passed")
    
    # טסט 7
    test_case = TestFixedCommands()
    test_case.setUp()
    await test_case.test_broadcast_command_admin_no_args()
    print("✅ Broadcast command (admin, no args) test passed")
    
    # טסט 8
    test_case = TestFixedCommands()
    test_case.setUp()
    await test_case.test_broadcast_command_admin_no_notification_service()
    print("✅ Broadcast command (admin, no service) test passed")
    
    print("🎉 All tests passed!")

if __name__ == "__main__":
    asyncio.run(run_async_tests())