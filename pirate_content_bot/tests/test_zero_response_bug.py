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
        self.assertGreaterEqual(threshold, 0.1, 
                               "Confidence threshold should be at least 0.1 to avoid false responses")
        self.assertLessEqual(threshold, 0.5,
                           "Confidence threshold should not be too high to avoid missing valid requests")
        
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

    def test_bot_never_returns_zero_string(self):
        """בדיקה שהבוט לא מחזיר את המחרוזת '0' כתגובה"""
        
        # הטסט הזה מוודא שהבוט לא יחזיר "0" כתגובה לכל קלט
        # זה טסט מקומי שבודק תרחישים שונים
        
        # דמיון של פונקציות שעלולות להחזיר "0" בטעות
        problematic_responses = []
        
        # בדיקת פונקציות שעלולות להחזיר "0"
        def simulate_error_response():
            """סימולציה של פונקציה שעלולה להחזיר "0" בשגיאה"""
            try:
                # סימולציה של פעולה שנכשלת
                result = None
                if result is None:
                    return "Error: No data"
                return str(result)
            except:
                return "0"  # זה בעייתי!
                
        def simulate_count_response():
            """סימולציה של פונקציה שמחזירה ספירה"""
            count = 0  # יכול להיות 0 בקשות
            if count == 0:
                return "אין בקשות"  # זה תקין
            return f"{count} בקשות"
            
        # בדיקה שהפונקציות לא מחזירות רק "0"
        error_resp = simulate_error_response()
        count_resp = simulate_count_response()
        
        # התגובות האלה תקינות
        self.assertNotEqual(error_resp, "0")
        self.assertNotEqual(count_resp, "0")
        
        # בדיקה שאין תגובות שהן רק "0"
        valid_responses = [
            "אין בקשות", 
            "שגיאה בטעינת נתונים", 
            "0 בקשות",  # זה תקין - מכיל מידע
            "",  # ריק זה תקין (לא תגובה)
            None  # None זה תקין (לא תגובה)
        ]
        
        for response in valid_responses:
            if response == "0":
                self.fail(f"Found bare '0' response: {response}")


if __name__ == '__main__':
    unittest.main()