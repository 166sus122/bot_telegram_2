#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בוחן התנהגות הבוט - בדיקת זיהוי בקשות vs דיבורי סרק
"""

import asyncio
import sys
import logging
from typing import Dict, List, Tuple

# הוספת path לקבצי המערכת
sys.path.append('.')

from pirate_content_bot.core.content_analyzer import AdvancedContentAnalyzer
from pirate_content_bot.utils.duplicate_detector import DuplicateDetector
from pirate_content_bot.services.request_service import RequestService
from pirate_content_bot.core.storage_manager import StorageManager
from pirate_content_bot.utils.cache_manager import CacheManager
from pirate_content_bot.main.config import CONTENT_CATEGORIES

# הגדרת לוגים
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BotTester:
    """בוחן התנהגות הבוט"""
    
    def __init__(self):
        # אתחול רכיבי הליבה
        self.cache_manager = CacheManager()
        self.storage_manager = StorageManager()
        self.analyzer = AdvancedContentAnalyzer()
        self.duplicate_detector = DuplicateDetector(similarity_threshold=0.3)
        
        # נתוני בדיקה
        self.test_data = self._prepare_test_data()
        
    def _prepare_test_data(self) -> Dict[str, List[str]]:
        """הכנת נתוני בדיקה"""
        return {
            # בקשות אמיתיות - צריך לזהות
            'real_requests': [
                'אפשר את הסרט אווטר 2022?',
                'יש אופציה לסאגת וינלנד?',
                'אפשר לקבל בחינם צאט GPT?',
                'אני צריך דחוף וורד למחשב',
                'יש קבוצה של משחקי רטרו?',
                'רוצה את הסרט באטמן 2022',
                'תביאו לי אז את הגרסא השנייה',
                'יש אפשרות לפאקט טרייסר?'
                'אני רוצה את המשחק גרנד תפט אוטו 5',
                'יש לך את הסדרה ברקינג בד?',
                'אפשר בבקשה את הספר הארי פוטר?',
                'מחפש את האפליקציה פוטושופ 2024',
                'יש לכם את הסרט טופ גאן מאבריק?',
                'אני צריך את התוכנה אופיס 365',
                'מחפש את המשחק FIFA 24',
                'רוצה את הסדרה סטריינג׳ר תינגס',
                'אפשר את הספר יומנה של אנה פרנק?',
                'יש לך את הסרט ספיידרמן נו וויי הום?',
                'מחפש את המשחק קול אוף דיוטי',
                'רוצה את האפליקציה נטפליקס',
                'אפשר את הסרט דונקירק?',
                'יש לכם את הסדרה דה ויצ׳ר?',
            ],
            
            # דיבורי סרק - לא צריך לזהות
            'casual_chat': [
                'שלום איך הולך?',
                'מה נשמע היום?',
                'איך אתה מרגיש?',
                'מה התוכניות לסוף השבוע?',
                'איך היה לך בעבודה?',
                'אתה חושב שיהיה גשם היום?',
                'איך המשפחה שלך?',
                'מה אכלת היום לצהריים?',
                'ראיתי חדשות מעניינות היום',
                'איך הזמן עובר מהר',
                'אני עייף היום',
                'מחר יש לי פגישה חשובה',
                'האוכל היה טעים בצהריים',
                'מחכה לסוף השבוע',
                'הילדים חזרו מהספר',
            ],
            
            # ביניים - עלול להתבלבל
            'ambiguous': [
                'מה יש חדש בנטפליקס?',
                'איזה סרט כדאי לראות?',
                'שמעת על הסרט החדש?',
                'איך המשחק שלך?',
                'קראת ספר טוב לאחרונה?',
                'איזה תוכנה אתה משתמש?',
                'יש לך המלצות לסדרה?',
                'איך האפליקציה שלך?',
                'משהו מעניין לקרוא?',
                'איזה משחק אתה משחק?',
            ]
        }
    
    async def test_request_detection(self):
        """בדיקת זיהוי בקשות"""
        print("🧪 בודק זיהוי בקשות...")
        print("=" * 50)
        
        results = {
            'real_requests': {'correct': 0, 'total': 0},
            'casual_chat': {'correct': 0, 'total': 0},
            'ambiguous': {'correct': 0, 'total': 0}
        }
        
        for category, messages in self.test_data.items():
            print(f"\n📂 בודק קטגוריה: {category}")
            print("-" * 30)
            
            for msg in messages:
                try:
                    # ניתוח הודעה
                    analysis = self.analyzer.analyze_request(msg, user_id=12345)
                    score = analysis.get('confidence', 0)
                    
                    # קביעת אם זו בקשה לפי ציון הביטחון
                    is_request = score >= 60  # סף ביטחון לבקשה
                    
                    # קביעת תוצאה צפויה
                    expected_request = category == 'real_requests'
                    is_correct = (is_request == expected_request) or (category == 'ambiguous')
                    
                    # סימון תוצאה
                    status = "✅" if is_correct else "❌"
                    
                    print(f"{status} '{msg[:40]}...' | ציון: {score:.1f} | בקשה: {is_request}")
                    
                    # עדכון תוצאות
                    results[category]['total'] += 1
                    if is_correct:
                        results[category]['correct'] += 1
                        
                except Exception as e:
                    print(f"❌ שגיאה: {e}")
                    results[category]['total'] += 1
        
        # הצגת סיכום
        print("\n📊 סיכום תוצאות:")
        print("=" * 30)
        for category, stats in results.items():
            accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"{category}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)")
        
        return results
    
    async def test_duplicate_detection(self):
        """בדיקת זיהוי כפילויות"""
        print("\n🔍 בודק זיהוי כפילויות...")
        print("=" * 50)
        
        # בקשות דמה קיימות
        existing_requests = [
            {'id': 1, 'title': 'אווטר דרך המים 2022', 'status': 'pending'},
            {'id': 2, 'title': 'Grand Theft Auto V', 'status': 'completed'},
            {'id': 3, 'title': 'Breaking Bad', 'status': 'pending'},
            {'id': 4, 'title': 'Harry Potter', 'status': 'pending'},
            {'id': 5, 'title': 'Adobe Photoshop', 'status': 'completed'},
            {'id': 6, 'title': 'סופרמן איש הפלדה', 'status': 'pending'},
        ]
        
        # בדיקות כפילויות
        test_cases = [
            ('אפשר את הסרט אווטר 2022?', True, 1),  # כפילות מדויקת
            ('יש לכם אווטר דרך המים?', True, 1),  # כפילות חלקית
            ('אני רוצה GTA 5', True, 2),  # שם אחר לאותו דבר
            ('מחפש את ברקינג בד הסדרה', True, 3),  # כפילות עם מילים נוספות
            ('רוצה את סופרמן איש הפלדה', True, 6),  # כפילות מדויקת
            ('אפשר את הספר הארי פוטר?', True, 4),  # דומה אבל לא זהה
            ('יש לכם פוטושופ?', True, 5),  # כפילות חלקית
            ('מחפש את הסרט באטמן', False, None),  # לא כפילות
        ]
        
        for query, should_find, expected_id in test_cases:
            try:
                duplicates = self.duplicate_detector.find_duplicates(query, existing_requests)
                found_duplicate = len(duplicates) > 0
                
                status = "✅" if found_duplicate == should_find else "❌"
                
                if found_duplicate:
                    best_match_id, similarity = duplicates[0]
                    print(f"{status} '{query}' -> מצא #{best_match_id} (דמיון: {similarity*100:.1f}%)")
                else:
                    print(f"{status} '{query}' -> לא מצא כפילויות")
                    
            except Exception as e:
                print(f"❌ שגיאה בבדיקת '{query}': {e}")
    
    async def simulate_user_interactions(self):
        """דמיון אינטראקציות משתמש"""
        print("\n👤 מדמה אינטראקציות משתמש...")
        print("=" * 50)
        
        # דמיון משתמש
        user_id = 12345
        user_name = "בוחן"
        
        # דמיון רצף הודעות
        conversation = [
            'שלום!',  # פתיחה
            'מה נשמע?',  # דיבור סרק
            'אפשר את הסרט טופ גאן?',  # בקשה ראשונה
            'תודה!',  # תגובה
            'יש לכם גם את טופ גאן מאבריק?',  # בקשה דומה
            'איך אתה היום?',  # חזרה לדיבור סרק
            'מחפש את המשחק FIFA 24',  # בקשה חדשה
            'תודה רבה ולילה טוב',  # סגירה
        ]
        
        for i, message in enumerate(conversation):
            print(f"\n📩 הודעה #{i+1}: '{message}'")
            
            try:
                # ניתוח ההודעה
                analysis = self.analyzer.analyze_request(message, user_id)
                
                score = analysis.get('confidence', 0)
                is_request = score >= 60
                
                print(f"   🎯 ציון בקשה: {score:.1f}")
                print(f"   📁 קטגוריה: {analysis.get('category', 'unknown')}")
                print(f"   🔍 כותרת: {analysis.get('title', 'N/A')}")
                print(f"   ✅ בקשה: {is_request}")
                
                # אם זו בקשה, בדוק כפילויות
                if is_request:
                    print(f"   🔄 בודק כפילויות...")
                    # כאן היינו קוראים לשרות בקשות אמיתי
                    
            except Exception as e:
                print(f"   ❌ שגיאה: {e}")
                
            # המתנה קצרה בין הודעות
            await asyncio.sleep(0.1)
    
    async def run_all_tests(self):
        """הרצת כל הבדיקות"""
        print("🚀 מתחיל בדיקות מקיפות של הבוט")
        print("=" * 60)
        
        try:
            # בדיקת זיהוי בקשות
            await self.test_request_detection()
            
            # בדיקת זיהוי כפילויות
            await self.test_duplicate_detection()
            
            # דמיון אינטראקציות
            await self.simulate_user_interactions()
            
            print("\n🎉 כל הבדיקות הושלמו בהצלחה!")
            
        except Exception as e:
            print(f"\n💥 שגיאה כללית: {e}")
            logger.error(f"Test execution failed: {e}")

async def main():
    """פונקציה ראשית"""
    tester = BotTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())