#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test specific user requests that weren't being detected
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_request_scoring():
    """Test the scoring algorithm for specific requests"""
    
    try:
        from pirate_content_bot.main.pirate_bot_main import EnhancedPirateBot
        
        # Create a bot instance to use its scoring method
        bot = EnhancedPirateBot()
        
        # Test cases from user feedback
        test_cases = [
            ("יש שובר שורות?", True, "Should be detected - contains 'יש' + 'שובר שורות' content name"),
            ("אפשר פוטושופ?", True, "Should be detected - contains 'אפשר' + 'photoshop' software name"),
            ("היי איך הולך?", False, "Should NOT be detected - casual conversation"),
            ("תודה רבה!", False, "Should NOT be detected - thanks message"),
            ("מישהו יש את הסרט Avatar?", True, "Should be detected - clear request pattern"),
            ("איפה הסדרה Breaking Bad?", True, "Should be detected - location + content"),
        ]
        
        logger.info("Testing request scoring with new threshold (15%)...")
        logger.info("=" * 60)
        
        for text, should_detect, reason in test_cases:
            # Test the scoring function
            text_lower = text.lower()
            clean_text = text
            
            score = bot._calculate_request_score(text_lower, clean_text)
            threshold = 15  # New threshold
            will_detect = score >= threshold
            
            status = "✅ PASS" if will_detect == should_detect else "❌ FAIL" 
            
            logger.info(f"{status} | Text: '{text}'")
            logger.info(f"      | Score: {score} (threshold: {threshold})")
            logger.info(f"      | Expected: {'DETECT' if should_detect else 'IGNORE'}, Got: {'DETECT' if will_detect else 'IGNORE'}")
            logger.info(f"      | Reason: {reason}")
            logger.info("-" * 60)
        
        logger.info("✅ Test completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_request_scoring()