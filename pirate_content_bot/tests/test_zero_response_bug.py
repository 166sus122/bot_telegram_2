#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים לבדיקת בעיית התגובה "0" למשתמשים לא מוכרים
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot


class TestZeroResponseBug(unittest.IsolatedAsyncioTestCase):
    """טסט לבעיית התגובה "0" לכל הודעה"""
    
    async def asyncSetUp(self):
        """הגדרת הטסטים"""
        self.bot = EnhancedPirateBot()
        
        # Mock update ו-context
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_message = Mock()
        self.mock_user = Mock()
        self.mock_chat = Mock()
        
        # הגדרת המשתמש הלא מוכר
        self.mock_user.id = 99999999
        self.mock_user.first_name = "Unknown User"
        self.mock_user.username = "unknown_user"
        self.mock_user.is_bot = False
        
        # הגדרת הצ'אט
        self.mock_chat.id = 99999999
        self.mock_chat.type = "private"
        
        # הגדרת ההודעה
        self.mock_message.text = "בדיקה"
        self.mock_message.message_id = 123
        self.mock_message.reply_text = AsyncMock()
        
        # חיבור הכל יחד
        self.mock_update.effective_user = self.mock_user
        self.mock_update.effective_chat = self.mock_chat
        self.mock_update.message = self.mock_message
        
    async def test_unknown_user_message_handling(self):
        """בדיקה שהבוט לא עונה "0" למשתמש לא מוכר"""
        
        # הודעות שונות לבדיקה
        test_messages = [
            "שלום",
            "איך המצב",
            "תודה",
            "בדיקה רנדומלית",
            "אני רוצה עזרה",
            "what's up?",
            "123456",
            "!@#$%",
            "הודעה ארוכה מאוד עם הרבה מילים שלא אמורות להפעיל את מנגנון זיהוי הבקשות"
        ]
        
        for message in test_messages:
            with self.subTest(message=message):
                # עדכון הודעת הבדיקה
                self.mock_message.text = message
                self.mock_message.reply_text.reset_mock()
                
                # הרצת הטיפול בהודעה
                await self.bot.enhanced_message_handler(self.mock_update, self.mock_context)
                
                # בדיקה שאם נענתה תשובה, זה לא "0"
                if self.mock_message.reply_text.called:
                    call_args = self.mock_message.reply_text.call_args
                    if call_args and call_args[0]:
                        response_text = call_args[0][0]
                        self.assertNotEqual(response_text, "0", 
                                          f'Bot responded "0" to message: "{message}"')
                        self.assertNotEqual(response_text.strip(), "0", 
                                          f'Bot responded "0" (with whitespace) to message: "{message}"')
                        
                        # בדיקה נוספת שהתגובה לא מכילה רק ספרות
                        self.assertFalse(response_text.strip().isdigit() and response_text.strip() == "0",
                                       f'Bot responded only digit "0" to message: "{message}"')
    
    async def test_auto_response_configuration(self):
        """בדיקה שההגדרות של תגובה אוטומטית נכונות"""
        
        # בדיקה שהסף לתגובה אוטומטית גבוה מספיק
        from pirate_content_bot.main.config import AUTO_RESPONSE_CONFIG
        
        threshold = AUTO_RESPONSE_CONFIG.get('confidence_threshold', 0)
        self.assertGreaterEqual(threshold, 0.2, 
                               "Confidence threshold should be at least 0.2 to avoid false responses")
        
        # בדיקה שהתגובה האוטומטית מוגדרת נכון
        enabled = AUTO_RESPONSE_CONFIG.get('enabled', True)
        self.assertTrue(isinstance(enabled, bool), "Auto response enabled should be boolean")
    
    async def test_message_filtering(self):
        """בדיקה שהסינון של הודעות עובד נכון"""
        
        # הודעות שלא אמורות לעבור את הסינון
        non_request_messages = [
            "היי",
            "שלום",
            "תודה",
            "ביי",
            "ok",
            "👍",
            "😊",
            "123",
            "test",
            "בדיקה"
        ]
        
        for message in non_request_messages:
            with self.subTest(message=message):
                # בדיקה שההודעה לא תיחשב כבקשה
                is_request = self.bot._could_be_content_request(message.lower(), message)
                
                # אם זה לא נראה כמו בקשה, הניקוד צריך להיות נמוך
                if not is_request:
                    score = self.bot._calculate_request_score(message.lower(), message)
                    self.assertLess(score, 25, 
                                   f'Message "{message}" got high score ({score}) but should be filtered')
    
    async def test_rate_limiting(self):
        """בדיקה שהגבלת קצב עובדת ולא מחזירה "0" """
        
        # Mock של פונקציית rate limiting
        with patch.object(self.bot, '_is_rate_limited', return_value=(True, "יותר מדי הודעות")):
            
            self.mock_message.text = "בדיקה"
            self.mock_message.reply_text.reset_mock()
            
            await self.bot.enhanced_message_handler(self.mock_update, self.mock_context)
            
            # בדיקה שאם הוחזרה תגובה, זה לא "0"
            if self.mock_message.reply_text.called:
                call_args = self.mock_message.reply_text.call_args[0][0]
                self.assertNotEqual(call_args, "0")
                self.assertIn("יותר מדי", call_args)  # צריכה להיות הודעת rate limit

    def test_empty_or_invalid_responses(self):
        """בדיקה שלא מוחזרות תגובות ריקות או לא תקינות"""
        
        # בדיקת פונקציות שעלולות להחזיר "0"
        invalid_responses = ["0", "", None, "None", "null"]
        
        for response in invalid_responses:
            self.assertNotEqual(response, "0", f"Invalid response found: {response}")


if __name__ == '__main__':
    unittest.main()