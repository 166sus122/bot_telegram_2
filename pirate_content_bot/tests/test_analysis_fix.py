#!/usr/bin/env python3
"""
Quick test to verify analysis fixes
"""

import os
import sys
import logging
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_analysis():
    try:
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        
        bot = EnhancedPirateBot()
        
        # Test the analysis function that was failing
        test_cases = [
            "יש שובר שורות?",
            "אפשר פוטושופ?",
            "אפשר בבקשה בדיקה?"
        ]
        
        logger.info("Testing analysis with fixed thresholds...")
        
        for text in test_cases:
            text_lower = text.lower()
            score = bot._calculate_request_score(text_lower, text)
            analysis = bot._analyze_high_score_request(text_lower, text, score)
            
            logger.info(f"Text: '{text}'")
            logger.info(f"  Score: {score}")
            logger.info(f"  Category: {analysis['category']}")
            logger.info(f"  is_clear: {analysis['is_clear_request']}")
            logger.info(f"  might_be: {analysis['might_be_request']}")
            logger.info(f"  Should process: {analysis['is_clear_request'] or analysis['might_be_request']}")
            logger.info("-" * 50)
        
        logger.info("✅ Analysis test completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analysis()