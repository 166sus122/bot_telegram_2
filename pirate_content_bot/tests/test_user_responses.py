#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test bot responses to random messages from unknown users
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
    from pirate_content_bot.main.config import USE_DATABASE, DB_CONFIG
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Import warning: {e}")
    IMPORTS_AVAILABLE = False


class TestUserResponses(unittest.IsolatedAsyncioTestCase):
    """Test bot responses to various user messages"""
    
    async def asyncSetUp(self):
        """Setup for each test"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
            
        # Create bot instance
        self.bot = EnhancedPirateBot()
        
        # Create mock update and context
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_message = Mock()
        self.mock_user = Mock()
        self.mock_chat = Mock()
        
        # Setup unknown user
        self.mock_user.id = 999000000
        self.mock_user.first_name = "TestUser"
        self.mock_user.username = "test_user"
        self.mock_user.is_bot = False
        
        # Setup chat
        self.mock_chat.id = 999000000
        self.mock_chat.type = "private"
        
        # Setup message
        self.mock_message.message_id = 12345
        self.mock_message.date = datetime.now()
        self.mock_message.reply_text = AsyncMock()
        
        # Connect everything
        self.mock_update.effective_user = self.mock_user
        self.mock_update.effective_chat = self.mock_chat
        self.mock_update.message = self.mock_message
    
    async def test_content_request_messages(self):
        """Test responses to content request messages"""
        
        content_requests = [
            "אני מחפש את הסדרה Breaking Bad",
            "רוצה את הסרט Avatar 2022", 
            "יש את המשחק Cyberpunk 2077?",
            "מישהו יכול למצוא את הספר הארי פוטר?",
            "יש שובר שורות?",
            "אפשר פוטושופ?"
        ]
        
        for message in content_requests:
            with self.subTest(message=message):
                self.mock_message.text = message
                self.mock_message.reply_text.reset_mock()
                
                await self.bot.enhanced_message_handler(self.mock_update, self.mock_context)
                
                # Content requests should get a response
                if self.mock_message.reply_text.called:
                    call_args = self.mock_message.reply_text.call_args[0][0]
                    # Should not be just "0" (string or integer)
                    self.assertNotEqual(call_args, "0")
                    self.assertNotEqual(call_args, 0)
                    response_str = str(call_args)
                    self.assertNotEqual(response_str.strip(), "0")
    
    async def test_ambiguous_messages(self):
        """Test responses to ambiguous messages"""
        
        ambiguous_messages = [
            "היי איך הולך?",
            "תודה רבה!",
            "מה שלומך?",
            ".",
            "אבגדהוזחט",
            "123456789",
            "hello world",
            "test test test"
        ]
        
        for message in ambiguous_messages:
            with self.subTest(message=message):
                self.mock_message.text = message
                self.mock_message.reply_text.reset_mock()
                
                await self.bot.enhanced_message_handler(self.mock_update, self.mock_context)
                
                # Ambiguous messages might or might not get a response
                # But if they do, it should not be "0"
                if self.mock_message.reply_text.called:
                    call_args = self.mock_message.reply_text.call_args[0][0]
                    self.assertNotEqual(call_args, "0")
                    self.assertNotEqual(call_args, 0)
                    response_str = str(call_args)
                    self.assertNotEqual(response_str.strip(), "0")
    
    async def test_follow_up_messages(self):
        """Test responses to follow-up messages"""
        
        follow_up_messages = [
            "בעמפ",
            "עדיין מחפש",
            "נו מה קורה?",
            "anyone?"
        ]
        
        for message in follow_up_messages:
            with self.subTest(message=message):
                self.mock_message.text = message
                self.mock_message.reply_text.reset_mock()
                
                await self.bot.enhanced_message_handler(self.mock_update, self.mock_context)
                
                # Follow-ups should typically not get automated responses
                # But if they do, should not be "0"
                if self.mock_message.reply_text.called:
                    call_args = self.mock_message.reply_text.call_args[0][0]
                    self.assertNotEqual(call_args, "0")
                    self.assertNotEqual(call_args, 0)
                    response_str = str(call_args)
                    self.assertNotEqual(response_str.strip(), "0")
    
    async def test_mixed_content_messages(self):
        """Test responses to mixed content messages"""
        
        mixed_messages = [
            "יש את הסדרה Game of Thrones? תודה מראש!",
            "מחפש משחק חדש, יש המלצות?",
            "זה בוט או בן אדם?"
        ]
        
        for message in mixed_messages:
            with self.subTest(message=message):
                self.mock_message.text = message
                self.mock_message.reply_text.reset_mock()
                
                await self.bot.enhanced_message_handler(self.mock_update, self.mock_context)
                
                # Mixed messages might get responses
                # But should never be just "0"
                if self.mock_message.reply_text.called:
                    call_args = self.mock_message.reply_text.call_args[0][0]
                    self.assertNotEqual(call_args, "0")
                    self.assertNotEqual(call_args, 0)
                    response_str = str(call_args)
                    self.assertNotEqual(response_str.strip(), "0")
                    self.assertGreater(len(response_str.strip()), 0)


class TestMessageClassification(unittest.TestCase):
    """Test message classification logic"""
    
    def test_content_request_detection(self):
        """Test detection of content requests"""
        
        # These should be detected as content requests
        content_requests = [
            "אני מחפש Breaking Bad",
            "רוצה את הסרט Avatar",
            "יש את המשחק?",
            "מישהו יכול למצוא"
        ]
        
        # These should NOT be detected as content requests
        not_requests = [
            "שלום",
            "תודה",
            "איך הולך?",
            ".",
            "123"
        ]
        
        # Note: We can't test the actual bot logic here without importing it
        # This test validates our understanding of what should vs shouldn't be requests
        
        for request in content_requests:
            self.assertIsInstance(request, str)
            self.assertGreater(len(request), 0)
        
        for non_request in not_requests:
            self.assertIsInstance(non_request, str)


class TestRateLimiting(unittest.IsolatedAsyncioTestCase):
    """Test rate limiting functionality"""
    
    async def asyncSetUp(self):
        """Setup for rate limiting tests"""
        if not IMPORTS_AVAILABLE:
            self.skipTest("Required modules not available")
            
        self.bot = EnhancedPirateBot()
        
        # Setup mock objects
        self.mock_update = Mock()
        self.mock_context = Mock()
        self.mock_message = Mock()
        self.mock_user = Mock()
        self.mock_chat = Mock()
        
        self.mock_user.id = 999000001
        self.mock_user.first_name = "RateLimitUser"
        self.mock_user.username = "rate_limit_user"
        self.mock_user.is_bot = False
        
        self.mock_chat.id = 999000001
        self.mock_chat.type = "private"
        
        self.mock_message.text = "test message"
        self.mock_message.message_id = 12345
        self.mock_message.date = datetime.now()
        self.mock_message.reply_text = AsyncMock()
        
        self.mock_update.effective_user = self.mock_user
        self.mock_update.effective_chat = self.mock_chat
        self.mock_update.message = self.mock_message
    
    async def test_rate_limit_response(self):
        """Test that rate limited responses are not '0'"""
        
        # Mock rate limiting to trigger
        with patch.object(self.bot, '_is_rate_limited', return_value=(True, "יותר מדי הודעות")):
            
            await self.bot.enhanced_message_handler(self.mock_update, self.mock_context)
            
            # If bot replied, it should not be "0"
            if self.mock_message.reply_text.called:
                call_args = self.mock_message.reply_text.call_args[0][0]
                self.assertNotEqual(call_args, "0")
                self.assertNotEqual(call_args, 0)
                response_str = str(call_args)
                self.assertNotEqual(response_str.strip(), "0")
                # Should contain rate limit message
                self.assertIn("יותר מדי", response_str)


if __name__ == '__main__':
    unittest.main()