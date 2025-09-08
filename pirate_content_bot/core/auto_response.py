"""
מנהל תגובות אוטומטיות חכם לבוט התמימים הפיראטים
מזהה ומגיב אוטומטית להודעות תודה, bump ועוד
"""

import re
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from pirate_content_bot.main.config import THANKS_KEYWORDS, BUMP_KEYWORDS

class AdvancedAutoResponseManager:
    """מנהל תגובות אוטומטיות חכם ומתקדם"""
    
    def __init__(self):
        self.response_templates = self._load_response_templates()
        self.user_interaction_history = {}
        self.last_responses = {}
        
        # הגדרות התנהגות
        self.max_responses_per_hour = 3
        self.min_response_delay = 30  # שניות
    
    def _load_response_templates(self) -> Dict[str, List[Dict]]:
        """טעינת תבניות תגובות עם משקלים"""
        return {
            'thanks': [
                {"text": "🙏 תודה רבה על המילים הטובות!", "weight": 1},
                {"text": "❤️ שמח שעזרנו לך!", "weight": 2},
                {"text": "🎉 בכיף חבר! זה בשביל זה אנחנו כאן", "weight": 1},
                {"text": "💙 תמיד לשירותכם, התמימים הפיראטים! 🏴‍☠️", "weight": 3},
                {"text": "⭐ המשוב שלך חשוב לנו!", "weight": 1},
                {"text": "🤗 אין בעד מה, נשמח לעזור שוב!", "weight": 2},
                {"text": "🎬 תיהנה מהתוכן!", "weight": 2},
                {"text": "👍 זה מה שאנחנו הכי אוהבים לשמוע!", "weight": 1}
            ],
            'bump': [
                {"text": "👀 ראינו את הבקשה שלך, המנהלים עובדים על זה...", "weight": 3},
                {"text": "⏳ סבלנות... טוב דברים בא למי שמחכה", "weight": 2},
                {"text": "🔍 המנהלים מחפשים בארכיון הגדול...", "weight": 2},
                {"text": "📋 הבקשה שלך ברשימה שלנו ובטיפול", "weight": 3},
                {"text": "🎯 זוכרים אותך! עוד מעט...", "weight": 1},
                {"text": "⚡ בדיוק עכשיו בודקים את זה בשבילך", "weight": 2},
                {"text": "🏃‍♂️ רצים לחפש...", "weight": 1},
                {"text": "🔥 הבקשה שלך חמה ובטיפול מיידי!", "weight": 1}
            ],
            'greeting': [
                {"text": "👋 שלום ומברוכים הבאים לקהילת התמימים הפיראטים!", "weight": 2},
                {"text": "🏴‍☠️ יאהוי! מה נשמע?", "weight": 3},
                {"text": "🎬 מוכנים לצלול לעולם התוכן?", "weight": 2},
                {"text": "⭐ היי! איך אפשר לעזור לך היום?", "weight": 1}
            ],
            'help_offer': [
                {"text": "🤔 נראה שאתה מבולבל. צריך עזרה? /help", "weight": 2},
                {"text": "💡 רוצה טיפים איך לבקש תוכן? תכתוב /help", "weight": 2},
                {"text": "🆘 יש לך שאלות? אני כאן לעזור!", "weight": 1},
                {"text": "📚 המדריך המלא ב-/help", "weight": 1}
            ],
            'quality_compliment': [
                {"text": "👌 בקשה מעוצבת יפה! כך אוהבים", "weight": 2},
                {"text": "⭐ בקשה מפורטת = תוצאות מהירות יותר!", "weight": 3},
                {"text": "🎯 בקשה מושלמת! המנהלים יאהבו אותה", "weight": 1},
                {"text": "💯 איכות מעולה של בקשה!", "weight": 1}
            ],
            'encouragement': [
                {"text": "💪 לא מוצאים עדיין, אבל לא נוותר!", "weight": 2},
                {"text": "🔍 ממשיכים לחפש בשבילך...", "weight": 2},
                {"text": "⏰ לפעמים זה לוקח זמן, אבל שווה את ההמתנה", "weight": 1},
                {"text": "🏆 הכי קשה למצוא = הכי מיוחד כשמוצאים!", "weight": 1}
            ]
        }
    
    def should_auto_respond(self, text: str, user_id: int, context: Optional[Dict] = None) -> Tuple[bool, str, str]:
        """בדיקה מתקדמת אם צריך להגיב אוטומטית"""
        text_clean = text.lower().strip()
        
        # מניעת הצפה - בדיקת הגבלות
        if self._should_throttle_response(user_id):
            return False, '', ''
        
        # זיהוי הודעות תודה מתקדם
        thanks_score = self._calculate_thanks_score(text_clean)
        if thanks_score > 0.7:
            response = self._get_weighted_response('thanks')
            self._record_response(user_id, 'thanks')
            return True, 'thanks', response
        
        # זיהוי bump מתקדם
        bump_score = self._calculate_bump_score(text_clean)
        if bump_score > 0.8:
            response = self._get_weighted_response('bump')
            self._record_response(user_id, 'bump')
            return True, 'bump', response
        
        # זיהוי ברכות וקידומים
        if self._is_greeting(text_clean) and len(text) < 25:
            response = self._get_weighted_response('greeting')
            self._record_response(user_id, 'greeting')
            return True, 'greeting', response
        
        # זיהוי בקשת עזרה
        if self._needs_help(text_clean):
            response = self._get_weighted_response('help_offer')
            self._record_response(user_id, 'help_offer')
            return True, 'help_offer', response
        
        # החמאה על בקשה איכותית (אם יש context)
        if context and context.get('confidence', 0) > 85:
            # רק אם זה לא קרה לאחרונה
            last_time = self.last_responses.get(user_id, {}).get('quality_compliment', datetime.min)
            if datetime.now() - last_time > timedelta(hours=6):
                response = self._get_weighted_response('quality_compliment')
                self._record_response(user_id, 'quality_compliment')
                return True, 'quality_compliment', response
        
        return False, '', ''
    
    def _calculate_thanks_score(self, text: str) -> float:
        """חישוב ציון הודעת תודה"""
        score = 0.0
        
        # בדיקת מילות מפתח בסיסיות
        for keyword in THANKS_KEYWORDS:
            if keyword.lower() in text:
                score += 0.3
        
        # בדיקות מתקדמות
        thanks_patterns = [
            r'\b(תודה|thanks?|thx)\b',
            r'\b(אלופ|מלכ|חמוד|יפ)\w*',
            r'\b(perfect|great|awesome|amazing)\b',
            r'❤️|♥️|💙|🙏|👏|👍'
        ]
        
        for pattern in thanks_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.2
        
        # בונוס למשפטים חיוביים
        positive_indicators = ['עזרת', 'מעולה', 'אחלה', 'רהוט']
        for indicator in positive_indicators:
            if indicator in text:
                score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_bump_score(self, text: str) -> float:
        """חישוב ציון הודעת bump"""
        score = 0.0
        
        # בדיקת מילות מפתח בסיסיות
        for keyword in BUMP_KEYWORDS:
            if keyword.lower() in text:
                score += 0.4
        
        # בדיקות מיוחדות
        bump_patterns = [
            r'^\.+$',  # רק נקודות
            r'^\?+$',  # רק סימני שאלה
            r'\b(עדכון|update|status)\b',
            r'\b(נו|אז|מה קורה)\b',
            r'🔥|⏳|👀'
        ]
        
        for pattern in bump_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.3
        
        # בונוס להודעות קצרות (bump טיפוסי)
        if len(text.strip()) <= 5:
            score += 0.2
        
        return min(score, 1.0)
    
    def _is_greeting(self, text: str) -> bool:
        """זיהוי ברכות"""
        greeting_patterns = [
            r'\b(שלום|היי|הי|hello|hi)\b',
            r'\b(בוקר טוב|ערב טוב|לילה טוב)\b',
            r'\b(מה נשמע|מה קורה|איך אתה)\b',
            r'👋|🤚|✋'
        ]
        
        for pattern in greeting_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _needs_help(self, text: str) -> bool:
        """זיהוי בקשת עזרה"""
        help_patterns = [
            r'\b(עזרה|help|מבולבל|לא מבין)\b',
            r'\b(איך|how|מה זה|what)\b.*\b(עושים|לעשות|do)\b',
            r'\?(.*\?){2,}',  # הרבה סימני שאלה
            r'🤔|😕|😔|❓|🆘'
        ]
        
        for pattern in help_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def _should_throttle_response(self, user_id: int) -> bool:
        """בדיקת הגבלות תגובה"""
        now = datetime.now()
        
        # בדיקת היסטוריית תגובות
        if user_id not in self.user_interaction_history:
            self.user_interaction_history[user_id] = []
        
        # ניקוי רשומות ישנות (מעל שעה)
        self.user_interaction_history[user_id] = [
            timestamp for timestamp in self.user_interaction_history[user_id]
            if now - timestamp < timedelta(hours=1)
        ]
        
        # בדיקת מגבלת תגובות לשעה
        if len(self.user_interaction_history[user_id]) >= self.max_responses_per_hour:
            return True
        
        # בדיקת מגבלת זמן מינימלי
        if self.user_interaction_history[user_id]:
            last_response = max(self.user_interaction_history[user_id])
            if now - last_response < timedelta(seconds=self.min_response_delay):
                return True
        
        return False
    
    def _get_weighted_response(self, response_type: str) -> str:
        """בחירת תגובה לפי משקלים"""
        if response_type not in self.response_templates:
            return "👋 היי!"
        
        templates = self.response_templates[response_type]
        
        # יצירת רשימה משוקללת
        weighted_list = []
        for template in templates:
            weighted_list.extend([template['text']] * template['weight'])
        
        return random.choice(weighted_list)
    
    def _record_response(self, user_id: int, response_type: str):
        """תיעוד תגובה שנשלחה"""
        now = datetime.now()
        
        # עדכון היסטוריה כללית
        if user_id not in self.user_interaction_history:
            self.user_interaction_history[user_id] = []
        self.user_interaction_history[user_id].append(now)
        
        # עדכון תגובות ספציפיות
        if user_id not in self.last_responses:
            self.last_responses[user_id] = {}
        self.last_responses[user_id][response_type] = now
    
    async def get_response(self, text: str, user_id: int, context: Optional[Dict] = None) -> Optional[Dict]:
        """מתודה אסינכרונית לקבלת תגובה אוטומטית"""
        should_respond, response_type, response_text = self.should_auto_respond(text, user_id, context)
        
        if should_respond:
            # חישוב עיכוב דינמי לפי סוג התגובה
            delay_map = {
                'thanks': 1,
                'bump': 2,
                'greeting': 0.5,
                'help_offer': 1.5,
                'quality_compliment': 1,
                'encouragement': 2
            }
            
            return {
                'message': response_text,
                'type': response_type,
                'delay': delay_map.get(response_type, 1)
            }
        
        return None

    def get_response_stats(self) -> Dict[str, any]:
        """קבלת סטטיסטיקות תגובות"""
        total_users = len(self.user_interaction_history)
        total_responses = sum(
            len(responses) for responses in self.user_interaction_history.values()
        )
        
        # ספירת תגובות לפי סוג
        response_type_counts = {}
        for user_responses in self.last_responses.values():
            for response_type in user_responses.keys():
                response_type_counts[response_type] = response_type_counts.get(response_type, 0) + 1
        
        return {
            'total_users_interacted': total_users,
            'total_auto_responses': total_responses,
            'responses_by_type': response_type_counts,
            'most_common_response': max(response_type_counts.items(), key=lambda x: x[1])[0] if response_type_counts else None
        }
    
    def clear_old_history(self, hours: int = 24):
        """ניקוי היסטוריה ישנה"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # ניקוי היסטוריית אינטראקציות
        for user_id in list(self.user_interaction_history.keys()):
            self.user_interaction_history[user_id] = [
                timestamp for timestamp in self.user_interaction_history[user_id]
                if timestamp > cutoff
            ]
            
            # מחיקת משתמשים ללא היסטוריה
            if not self.user_interaction_history[user_id]:
                del self.user_interaction_history[user_id]
        
        # ניקוי תגובות אחרונות
        for user_id in list(self.last_responses.keys()):
            self.last_responses[user_id] = {
                response_type: timestamp
                for response_type, timestamp in self.last_responses[user_id].items()
                if timestamp > cutoff
            }
            
            # מחיקת משתמשים ללא תגובות אחרונות
            if not self.last_responses[user_id]:
                del self.last_responses[user_id]