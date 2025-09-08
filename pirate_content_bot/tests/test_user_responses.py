#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test bot responses to random messages from unknown users
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Test messages to simulate various user inputs
TEST_MESSAGES = [
    # Normal content requests
    "אני מחפש את הסדרה Breaking Bad",
    "רוצה את הסרט Avatar 2022", 
    "יש את המשחק Cyberpunk 2077?",
    "מישהו יכול למצוא את הספר הארי פוטר?",
    
    # User reported issues - should be detected as requests
    "יש שובר שורות?",
    "אפשר פוטושופ?",
    
    # Ambiguous messages
    "היי איך הולך?",
    "תודה רבה!",
    "מה שלומך?",
    ".",
    
    # Random/spam messages
    "אבגדהוזחט",
    "123456789",
    "hello world",
    "test test test",
    
    # Bumps and follow-ups
    "בעמפ",
    "עדיין מחפש",
    "נו מה קורה?",
    "anyone?",
    
    # System messages
    "/help",
    "/start",
    "/stats",
    
    # Mixed content
    "יש את הסדרה Game of Thrones? תודה מראש!",
    "מחפש משחק חדש, יש המלצות?",
    "זה בוט או בן אדם?",
]

async def simulate_user_message(bot_instance, message_text: str, user_id: int = 123456789):
    """Simulate a message from a user"""
    
    # Create mock user
    mock_user = Mock()
    mock_user.id = user_id
    mock_user.first_name = "TestUser"
    mock_user.username = "test_user"
    mock_user.is_bot = False
    
    # Create mock message
    mock_message = Mock()
    mock_message.text = message_text
    mock_message.from_user = mock_user
    mock_message.chat = Mock()
    mock_message.chat.id = user_id
    mock_message.chat.type = "private"
    mock_message.message_id = 12345
    mock_message.date = datetime.now()
    
    # Mock reply method
    mock_message.reply_text = AsyncMock()
    
    # Create mock update
    mock_update = Mock()
    mock_update.effective_user = mock_user
    mock_update.effective_chat = mock_message.chat
    mock_update.message = mock_message
    
    # Create mock context
    mock_context = Mock()
    
    logger.info(f"Testing message: '{message_text}'")
    
    try:
        # Call the bot's message handler
        await bot_instance.enhanced_message_handler(mock_update, mock_context)
        
        # Check if reply was called
        if mock_message.reply_text.called:
            call_args = mock_message.reply_text.call_args
            reply_text = call_args[0][0] if call_args and call_args[0] else "No text"
            logger.info(f"  Bot replied: {reply_text[:100]}...")
        else:
            logger.info("  Bot did not reply")
            
    except Exception as e:
        logger.error(f"  Error processing message: {e}")
    
    print("-" * 60)

async def test_bot_responses():
    """Test various message types with the bot"""
    
    try:
        # Import bot components
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        from pirate_content_bot.main.config import USE_DATABASE, DB_CONFIG
        
        logger.info("Initializing bot for testing...")
        
        # Create bot instance without actually starting it
        bot = EnhancedPirateBot()
        
        # Initialize components manually
        await bot._init_components()
        
        logger.info("Running message tests...")
        print("=" * 60)
        
        # Test each message type
        for i, message in enumerate(TEST_MESSAGES, 1):
            logger.info(f"\n🧪 Test {i}/{len(TEST_MESSAGES)}")
            await simulate_user_message(bot, message, user_id=999000000 + i)
            await asyncio.sleep(0.1)  # Small delay between tests
        
        logger.info("✅ All tests completed!")
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bot_responses())