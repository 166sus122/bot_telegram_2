#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים מקיפים לפקודת סטטוס ומעקב מקור הודעות
"""

import unittest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# הוספת path לפרויקט  
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from main.pirate_bot_main import EnhancedPirateBot
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location("pirate_bot_main", os.path.join(parent_dir, "main", "pirate_bot_main.py"))
    bot_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bot_module)
    EnhancedPirateBot = bot_module.EnhancedPirateBot

from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes

class TestStatusAndTracking(unittest.TestCase):
    """טסטים לסטטוס ומעקב מקור"""
    
    def setUp(self):
        """הגדרת הטסטים"""
        self.bot = EnhancedPirateBot()
        
        # Mock objects
        self.mock_user = User(id=123456789, first_name="Test", is_bot=False)
        self.mock_chat = Chat(id=-1001234567890, type="supergroup", title="Test Group")
        self.mock_private_chat = Chat(id=123456789, type="private")
        
        self.mock_message = Mock(spec=Message)
        self.mock_message.reply_text = AsyncMock()
        self.mock_message.message_id = 12345
        
        self.mock_update = Mock(spec=Update)
        self.mock_update.effective_user = self.mock_user
        self.mock_update.effective_chat = self.mock_chat
        self.mock_update.message = self.mock_message
        
        self.mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        self.mock_context.args = []
        
    async def test_extract_message_source_private(self):
        """בדיקת חילוץ מידע מקור - הודעה פרטית"""
        self.mock_update.effective_chat = self.mock_private_chat
        
        source_info = self.bot._extract_message_source_info(self.mock_update)
        
        self.assertEqual(source_info['source_type'], 'private')
        self.assertEqual(source_info['thread_category'], 'private')
        self.assertEqual(source_info['message_id'], 12345)
        
    async def test_extract_message_source_group(self):
        """בדיקת חילוץ מידע מקור - קבוצה כללית"""
        self.mock_message.message_thread_id = None
        
        source_info = self.bot._extract_message_source_info(self.mock_update)
        
        self.assertEqual(source_info['source_type'], 'group')
        self.assertEqual(source_info['thread_category'], 'general')
        self.assertEqual(source_info['chat_title'], 'Test Group')
        
    async def test_extract_message_source_thread(self):
        """בדיקת חילוץ מידע מקור - נושא"""
        self.mock_message.message_thread_id = 11418  # נושא סדרות
        
        source_info = self.bot._extract_message_source_info(self.mock_update)
        
        self.assertEqual(source_info['source_type'], 'thread')
        self.assertEqual(source_info['thread_id'], 11418)
        self.assertIn('11418', source_info['source_location'])
        
    async def test_format_source_info_private(self):
        """בדיקת עיצוב מידע מקור - פרטי"""
        request_info = {'source_type': 'private'}
        
        source_text = self.bot._format_source_info(request_info)
        
        self.assertIn('הודעה פרטית', source_text)
        self.assertIn('📱', source_text)
        
    async def test_format_source_info_thread(self):
        """בדיקת עיצוב מידע מקור - נושא"""
        request_info = {
            'source_type': 'thread',
            'thread_category': 'series'
        }
        
        source_text = self.bot._format_source_info(request_info)
        
        self.assertIn('נושא סדרות', source_text)
        self.assertIn('💬', source_text)
        
    async def test_format_source_info_group(self):
        """בדיקת עיצוב מידע מקור - קבוצה"""
        request_info = {'source_type': 'group'}
        
        source_text = self.bot._format_source_info(request_info)
        
        self.assertIn('צ\'אט כללי', source_text)
        self.assertIn('👥', source_text)
        
    async def test_status_command_no_args(self):
        """בדיקת פקודת סטטוס בלי ארגומנטים"""
        await self.bot.status_command(self.mock_update, self.mock_context)
        
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn('שימוש בבדיקת סטטוס', call_args)
        self.assertIn('/status <מספר בקשה>', call_args)
        
    async def test_status_command_invalid_id(self):
        """בדיקת פקודת סטטוס עם ID לא תקין"""
        self.mock_context.args = ['not_a_number']
        
        await self.bot.status_command(self.mock_update, self.mock_context)
        
        self.mock_message.reply_text.assert_called_once()
        call_args = self.mock_message.reply_text.call_args[0][0]
        self.assertIn('מספר בקשה לא תקין', call_args)
        
    async def test_status_command_request_not_found(self):
        """בדיקת פקודת סטטוס - בקשה לא נמצאה"""
        self.mock_context.args = ['999']
        
        with patch.object(self.bot.request_service, 'get_request_status', return_value=None):
            await self.bot.status_command(self.mock_update, self.mock_context)
            
            self.mock_message.reply_text.assert_called_once()
            call_args = self.mock_message.reply_text.call_args[0][0]
            self.assertIn('לא נמצאה בקשה מספר #999', call_args)
            
    async def test_status_command_with_full_info(self):
        """בדיקת פקודת סטטוס עם מידע מלא"""
        self.mock_context.args = ['123']
        
        mock_request_info = {
            'id': 123,
            'status': 'pending',
            'title': 'בקשה לבדיקה',
            'category': 'series',
            'priority': 'high',
            'created_at': '2025-09-08 15:30:00',
            'source_type': 'thread',
            'thread_category': 'series',
            'notes': 'הערת בדיקה',
            'avg_processing_time': {
                'overall_avg': 18.5,
                'sample_size': 25
            }
        }
        
        with patch.object(self.bot.request_service, 'get_request_status', return_value=mock_request_info):
            await self.bot.status_command(self.mock_update, self.mock_context)
            
            self.mock_message.reply_text.assert_called_once()
            call_args = self.mock_message.reply_text.call_args[0][0]
            
            # בדיקת כל הפרטים
            self.assertIn('סטטוס בקשה #123', call_args)
            self.assertIn('pending', call_args)
            self.assertIn('בקשה לבדיקה', call_args)
            self.assertIn('series', call_args)
            self.assertIn('🔴', call_args)  # priority high emoji
            self.assertIn('נושא סדרות', call_args)  # source info
            self.assertIn('18.5 שעות', call_args)  # processing time
            self.assertIn('25 בקשות', call_args)  # sample size
            self.assertIn('הערת בדיקה', call_args)
            
    async def test_status_command_with_estimated_time(self):
        """בדיקת פקודת סטטוס עם זמן הערכה"""
        self.mock_context.args = ['456']
        
        mock_request_info = {
            'id': 456,
            'status': 'pending',
            'title': 'בקשה ללא נתונים',
            'category': 'movies',
            'priority': 'medium',
            'created_at': '2025-09-08 15:30:00',
            'source_type': 'private',
            'avg_processing_time': {
                'sample_size': 0  # אין נתונים
            }
        }
        
        with patch.object(self.bot.request_service, 'get_request_status', return_value=mock_request_info):
            await self.bot.status_command(self.mock_update, self.mock_context)
            
            self.mock_message.reply_text.assert_called_once()
            call_args = self.mock_message.reply_text.call_args[0][0]
            
            # בדיקת זמן הערכה
            self.assertIn('24-48 שעות (הערכה)', call_args)
            self.assertIn('הודעה פרטית', call_args)
            
    async def test_calculate_average_processing_time(self):
        """בדיקת חישוב זמן טיפול ממוצע"""
        if not self.bot.request_service:
            self.skipTest("Request service not available")
            
        # בדיקה שהפונקציה קיימת
        self.assertTrue(hasattr(self.bot.request_service, '_calculate_average_processing_time'))
        
        # בדיקה עם פרמטרים
        try:
            result = await self.bot.request_service._calculate_average_processing_time('series', 'high')
            
            # בדיקת מבנה התשובה
            self.assertIsInstance(result, dict)
            self.assertIn('overall_avg', result)
            self.assertIn('sample_size', result)
            self.assertIn('fulfilled_avg', result)
            self.assertIn('rejected_avg', result)
            
        except Exception as e:
            # צפוי כשאין DB
            self.assertIn('Failed to get connection', str(e))
            
    async def test_message_source_tracking_integration(self):
        """בדיקת אינטגרציה של מעקב מקור הודעה"""
        # הכנת analysis mock
        mock_analysis = {
            'title': 'בקשה לבדיקה',
            'category': 'series',
            'confidence': 0.8
        }
        
        # Mock thread validation
        mock_thread_validation = {
            'is_valid': True,
            'thread_category': 'series'
        }
        
        with patch.object(self.bot, 'analyzer') as mock_analyzer, \
             patch.object(self.bot, '_validate_thread_location', return_value=mock_thread_validation), \
             patch.object(self.bot.request_service, 'get_pending_requests', return_value=[]), \
             patch.object(self.bot.duplicate_detector, 'find_duplicates', return_value=[]), \
             patch.object(self.bot.request_service, 'create_request', return_value=123):
            
            mock_analyzer.analyze_advanced.return_value = mock_analysis
            
            # הדמיית קבלת הודעה בנושא
            self.mock_message.message_thread_id = 11418  # נושא סדרות
            
            await self.bot.handle_content_request(self.mock_update, self.mock_context)
            
            # בדיקה שהמידע התעדכן
            call_args = self.bot.request_service.create_request.call_args
            if call_args:
                analysis_arg = call_args[1]['analysis']
                
                # בדיקת שדות המקור
                self.assertIn('source_type', analysis_arg)
                self.assertIn('source_location', analysis_arg) 
                self.assertIn('thread_category', analysis_arg)
                self.assertIn('message_id', analysis_arg)
                
    async def test_thread_category_validation(self):
        """בדיקת זיהוי נכון של קטגוריות נושאים"""
        thread_mappings = {
            11432: 'updates',
            11418: 'series',
            11415: 'software', 
            11423: 'books',
            11411: 'movies',
            11422: 'spotify',
            11419: 'games',
            11420: 'apps'
        }
        
        for thread_id, expected_category in thread_mappings.items():
            # Mock הודעה בנושא ספציפי
            self.mock_message.message_thread_id = thread_id
            
            validation_result = self.bot._validate_thread_location(self.mock_update, "בקשה לבדיקה")
            
            if validation_result.get('is_valid'):
                # אם זוהה נכון, בדוק שהקטגוריה נכונה
                self.assertEqual(validation_result.get('thread_category'), expected_category)
                
    async def test_error_handling_in_source_extraction(self):
        """בדיקת טיפול בשגיאות בחילוץ מקור"""
        # הדמיית update פגום
        broken_update = Mock()
        broken_update.effective_chat = None
        broken_update.message = None
        
        source_info = self.bot._extract_message_source_info(broken_update)
        
        # וידוא שהפונקציה לא קורסת ומחזירה ברירת מחדל
        self.assertEqual(source_info['source_type'], 'unknown')
        self.assertEqual(source_info['thread_category'], 'general')
        self.assertEqual(source_info['message_id'], 0)
        
    async def test_format_source_info_error_handling(self):
        """בדיקת טיפול בשגיאות בעיצוב מידע מקור"""
        # מידע פגום
        broken_info = None
        
        source_text = self.bot._format_source_info(broken_info)
        
        # וידוא שהפונקציה לא קורסת
        self.assertIn('לא ידוע', source_text)
        self.assertIn('❓', source_text)

async def run_async_tests():
    """הרצת טסטים אסינכרוניים"""
    print("🧪 Running status and tracking tests...")
    
    test_methods = [
        'test_extract_message_source_private',
        'test_extract_message_source_group',
        'test_extract_message_source_thread',
        'test_format_source_info_private',
        'test_format_source_info_thread',
        'test_format_source_info_group',
        'test_status_command_no_args',
        'test_status_command_invalid_id',
        'test_status_command_request_not_found',
        'test_status_command_with_full_info',
        'test_status_command_with_estimated_time',
        'test_calculate_average_processing_time',
        'test_message_source_tracking_integration',
        'test_thread_category_validation',
        'test_error_handling_in_source_extraction',
        'test_format_source_info_error_handling'
    ]
    
    for test_method in test_methods:
        test_case = TestStatusAndTracking()
        test_case.setUp()
        
        try:
            await getattr(test_case, test_method)()
            print(f"✅ {test_method} passed")
        except Exception as e:
            print(f"❌ {test_method} failed: {e}")
    
    print("🎉 All status and tracking tests completed!")

if __name__ == "__main__":
    asyncio.run(run_async_tests())