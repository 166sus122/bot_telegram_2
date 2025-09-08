"""
מנתח תוכן חכם לבוט התמימים הפיראטים
מזהה ומנתח בקשות תוכן באופן אוטומטי
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from pirate_content_bot.main.config import CONTENT_CATEGORIES, URGENT_KEYWORDS, HIGH_PRIORITY_KEYWORDS as HIGH_KEYWORDS, VIP_KEYWORDS

class AdvancedContentAnalyzer:
    """מנתח תוכן חכם ומתקדם"""
    
    def __init__(self):
        # ביטויים רגולריים לזיהוי תוכן
        self.patterns = {
            'series_with_year': r'(?:סדרה|סדרת|series)\s*(?::|\s)+(.+?)\s*\(?(\d{4})\)?',
            'movie_with_year': r'(?:סרט|הסרט|movie|film)\s*(?::|\s)+(.+?)\s*\(?(\d{4})\)?',
            'season_episode': r'(?:עונה|season)\s*(\d+)(?:\s*(?:פרק|episode)\s*(\d+))?',
            'episode_only': r'(?:פרק|episode|ep)\s*(\d+)',
            'year_pattern': r'\b(19[5-9]\d|20[0-2]\d)\b',
            'quality_pattern': r'\b(4K|UHD|HD|720p|1080p|2160p|BluRay|WEB-DL|HDTV)\b',
            'language_pattern': r'\b(עברית|אנגלית|כתוביות|דובב|subtitles|dubbed)\b'
        }
        
        # מילות מפתח מתקדמות לקטגוריזציה
        self.advanced_keywords = {
            'series': {
                'strong': ['סדרה', 'סדרת', 'עונה', 'פרק', 'season', 'episode'],
                'medium': ['series', 'show', 'tv'],
                'weak': ['Netflix', 'HBO', 'Disney+']
            },
            'movies': {
                'strong': ['סרט', 'הסרט', 'movie', 'film'],
                'medium': ['cinema', 'במאי', 'שחקן'],
                'weak': ['trailer', 'imdb']
            },
            'anime': {
                'strong': ['אנימה', 'anime', 'מנגה', 'manga'],
                'medium': ['crunchyroll', 'funimation'],
                'weak': ['יפני', 'japanese']
            }
        }
    
    def analyze_request(self, text: str, user_id: int) -> Dict[str, Any]:
        """ניתוח מקיף של בקשת תוכן"""
        analysis = {
            'content_type': 'general',
            'category': 'general',
            'title': '',
            'year': None,
            'season': None,
            'episode': None,
            'quality': None,
            'language': 'hebrew',
            'priority': 'medium',
            'confidence': 0,
            'tags': []
        }
        
        text_clean = text.strip()
        
        # זיהוי קטגוריה
        analysis['category'] = self._detect_category(text_clean)
        analysis['content_type'] = analysis['category']
        
        # חילוץ כותרת ופרטים
        title_info = self._extract_title_and_details(text_clean, analysis['category'])
        analysis.update(title_info)
        
        # זיהוי עדיפות
        analysis['priority'] = self._detect_priority(text_clean)
        
        # יצירת תגים
        analysis['tags'] = self._generate_tags(text_clean, analysis)
        
        # חישוב רמת ביטחון
        analysis['confidence'] = self._calculate_confidence(text_clean, analysis)
        
        return analysis
    
    def analyze_advanced(self, text: str, user_id: int, context: Optional[Dict] = None) -> Dict[str, Any]:
        """ניתוח מתקדם של בקשת תוכן עם קונטקסט נוסף"""
        # ניתוח בסיסי
        basic_analysis = self.analyze_request(text, user_id)
        
        # יצירת advanced_features קודם
        advanced_features = {
            'sentiment': self._analyze_sentiment(text),
            'urgency_score': self._calculate_urgency_score(text),
            'similarity_to_existing': 0.0,  # יחושב מול בקשות קיימות
            'user_pattern_match': 0.0,      # יחושב בהתבסס על היסטוריה
            'spam_likelihood': self._detect_spam_likelihood(text, user_id)
        }
        
        # הוספת ניתוח מתקדם
        advanced_analysis = {
            **basic_analysis,
            'advanced_features': advanced_features
        }
        
        # עכשיו יצירת tags ו-recommendations עם הנתונים המלאים
        advanced_analysis['enhanced_tags'] = self._generate_advanced_tags(text, advanced_analysis, context)
        advanced_analysis['recommendations'] = self._generate_recommendations(advanced_analysis, context)
        
        # עדכון רמת ביטחון עם נתונים מתקדמים
        advanced_analysis['confidence'] = self._calculate_advanced_confidence(
            text, advanced_analysis, context
        )
        
        return advanced_analysis
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """ניתוח סנטימנט בסיסי"""
        positive_words = ['בבקשה', 'תודה', 'מעולה', 'אהבתי', 'נהדר', 'מומלץ']
        negative_words = ['לא', 'רע', 'לא טוב', 'נורא', 'גרוע']
        urgent_words = ['דחוף', 'מהר', 'צריך עכשיו', '!!']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        urgent_count = sum(1 for word in urgent_words if word in text_lower)
        
        sentiment_score = (positive_count - negative_count) / max(len(text.split()), 1)
        
        return {
            'score': sentiment_score,
            'polarity': 'positive' if sentiment_score > 0.1 else 'negative' if sentiment_score < -0.1 else 'neutral',
            'urgency_indicators': urgent_count,
            'politeness_score': positive_count * 0.2
        }
    
    def _calculate_urgency_score(self, text: str) -> float:
        """חישוב ציון דחיפות"""
        urgency_indicators = {
            'דחוף': 0.8,
            'מהר': 0.6,
            'צריך עכשיו': 0.9,
            '!!!': 0.7,
            '!!': 0.5,
            'חירום': 0.9,
            'בעיה': 0.4,
            'לא עובד': 0.6
        }
        
        text_lower = text.lower()
        urgency_score = 0.0
        
        for indicator, score in urgency_indicators.items():
            if indicator in text_lower:
                urgency_score = max(urgency_score, score)
        
        return min(urgency_score, 1.0)
    
    def _detect_spam_likelihood(self, text: str, user_id: int) -> float:
        """זיהוי סבירות ספאם"""
        spam_indicators = [
            (r'(.)\1{4,}', 0.3),  # תווים חוזרים
            (r'[!?]{3,}', 0.2),   # סימני קריאה/שאלה מרובים
            (r'\b(free|חינם|בחינם)\b', 0.1),  # מילות חינם
            (r'[A-Z]{10,}', 0.2), # אותיות גדולות רצופות
            (r'https?://', 0.4),  # קישורים
        ]
        
        spam_score = 0.0
        text_lower = text.lower()
        
        for pattern, score in spam_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                spam_score += score
        
        # בדיקת אורך לא סביר
        if len(text) < 5 or len(text) > 1000:
            spam_score += 0.2
        
        return min(spam_score, 1.0)
    
    def _generate_advanced_tags(self, text: str, analysis: Dict, context: Optional[Dict]) -> List[str]:
        """יצירת תגים מתקדמים"""
        advanced_tags = analysis.get('tags', []).copy()
        
        # תגי רמת דחיפות
        urgency = analysis['advanced_features']['urgency_score']
        if urgency > 0.7:
            advanced_tags.append('urgency:critical')
        elif urgency > 0.4:
            advanced_tags.append('urgency:high')
        
        # תגי סנטימנט
        sentiment = analysis['advanced_features']['sentiment']
        advanced_tags.append(f"sentiment:{sentiment['polarity']}")
        
        if sentiment['politeness_score'] > 0.5:
            advanced_tags.append('tone:polite')
        
        # תגי זיהוי תבנית
        if context and context.get('user_history'):
            # ניתוח דפוס משתמש (מפושט)
            advanced_tags.append('pattern:recognized')
        
        return advanced_tags
    
    def _generate_recommendations(self, analysis: Dict, context: Optional[Dict]) -> List[str]:
        """יצירת המלצות לשיפור הבקשה"""
        recommendations = []
        
        if analysis['confidence'] < 50:
            recommendations.append("הבקשה לא ברורה - נסה להיות יותר ספציפי")
        
        if not analysis.get('year'):
            recommendations.append("הוסף שנת יציאה לדיוק רב יותר")
        
        if analysis['category'] == 'series' and not analysis.get('season'):
            recommendations.append("ציין מספר עונה ופרק לסדרות")
        
        if analysis.get('title') and len(analysis['title']) < 3:
            recommendations.append("שם התוכן קצר מדי - הוסף פרטים נוספים")
        
        return recommendations
    
    def _calculate_advanced_confidence(self, text: str, analysis: Dict, context: Optional[Dict]) -> int:
        """חישוב רמת ביטחון מתקדמת"""
        base_confidence = analysis.get('confidence', 0)
        
        # התאמות בהתבסס על ניתוח מתקדם
        adjustments = 0
        
        # בונוס לסנטימנט חיובי
        sentiment = analysis['advanced_features']['sentiment']
        if sentiment['polarity'] == 'positive':
            adjustments += 5
        
        # קנס לספאם
        spam_likelihood = analysis['advanced_features']['spam_likelihood']
        if spam_likelihood > 0.5:
            adjustments -= 20
        elif spam_likelihood > 0.3:
            adjustments -= 10
        
        # בונוס לקונטקסט משתמש
        if context and context.get('user_reputation', 0) > 70:
            adjustments += 10
        
        return max(0, min(100, base_confidence + adjustments))
    
    def _detect_category(self, text: str) -> str:
        """זיהוי קטגוריית התוכן"""
        text_lower = text.lower()
        category_scores = {}
        
        # ציון בסיסי לכל קטגוריה
        for category, data in CONTENT_CATEGORIES.items():
            if category == 'general':
                continue
            
            score = 0
            
            # בדיקת מילות מפתח בסיסיות
            for keyword in data['keywords']:
                # השתמש בביטויים רגולריים עם word boundaries למילים של 3 תווים ויותר
                if len(keyword) >= 3:
                    pattern = rf'\b{re.escape(keyword.lower())}\b'
                    if re.search(pattern, text_lower):
                        score += 3
                else:
                    # למילים קצרות, השתמש במצב הרגיל אבל בדוק שזה לא חלק ממילה אחרת
                    if keyword.lower() in text_lower:
                        # וודא שזה לא חלק ממילה גדולה יותר
                        index = text_lower.find(keyword.lower())
                        while index != -1:
                            # בדוק שיש רווח או תחילת טקסט לפני ואחרי
                            before_ok = index == 0 or not text_lower[index-1].isalnum()
                            after_ok = index + len(keyword) >= len(text_lower) or not text_lower[index + len(keyword)].isalnum()
                            if before_ok and after_ok:
                                score += 3
                                break
                            index = text_lower.find(keyword.lower(), index + 1)
            
            # בדיקת מילות מפתח מתקדמות
            if category in self.advanced_keywords:
                for strength, keywords in self.advanced_keywords[category].items():
                    multiplier = {'strong': 5, 'medium': 3, 'weak': 1}[strength]
                    for keyword in keywords:
                        # השתמש בביטויים רגולריים עם word boundaries למילים של 3 תווים ויותר
                        if len(keyword) >= 3:
                            pattern = rf'\b{re.escape(keyword.lower())}\b'
                            if re.search(pattern, text_lower):
                                score += multiplier
                        else:
                            # למילים קצרות, השתמש במצב הרגיל אבל בדוק שזה לא חלק ממילה אחרת
                            if keyword.lower() in text_lower:
                                # וודא שזה לא חלק ממילה גדולה יותר
                                index = text_lower.find(keyword.lower())
                                while index != -1:
                                    # בדוק שיש רווח או תחילת טקסט לפני ואחרי
                                    before_ok = index == 0 or not text_lower[index-1].isalnum()
                                    after_ok = index + len(keyword) >= len(text_lower) or not text_lower[index + len(keyword)].isalnum()
                                    if before_ok and after_ok:
                                        score += multiplier
                                        break
                                    index = text_lower.find(keyword.lower(), index + 1)
            
            category_scores[category] = score
        
        # אם לא נמצאו מילות מפתח ברורות, נשתמש בהכרה חכמה נוספת
        if not any(score > 0 for score in category_scores.values()):
            # חיפוש דפוסים שמאפיינים סרטים (כותרת + שנה)
            year_pattern = r'\b(19|20)\d{2}\b'
            has_year = re.search(year_pattern, text)
            if has_year:
                # אם יש שנה, סביר שזה סרט או סדרה
                # בואו נבדוק אם יש מילים שמרמזות על כותרת
                potential_title_words = len([w for w in text.split() if len(w) >= 3 and not w.isdigit()])
                if potential_title_words >= 2:  # יש לפחות 2 מילות כותרת
                    # נבדוק האם זה נראה יותר כסרט או סדרה
                    series_indicators = ['עונה', 'פרק', 'season', 'episode', 's0', 'e0']
                    is_series = any(indicator in text_lower for indicator in series_indicators)
                    if is_series:
                        return 'series'
                    else:
                        # ברירת מחדל לסרט כשיש שנה וכותרת
                        return 'movies'
        
        # בחירת הקטגוריה הטובה ביותר
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0:
                return best_category
        
        return 'general'
    
    def _extract_title_and_details(self, text: str, category: str) -> Dict[str, Any]:
        """חילוץ כותרת ופרטים"""
        result = {
            'title': '',
            'year': None,
            'season': None,
            'episode': None,
            'quality': None
        }
        
        # ניסוי לחלץ כותרת עם שנה
        for pattern_name, pattern in self.patterns.items():
            if pattern_name.endswith('_with_year'):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result['title'] = match.group(1).strip()
                    result['year'] = int(match.group(2))
                    break
        
        # אם לא נמצאה כותרת עם שנה, חפש כותרת כללית
        if not result['title']:
            result['title'] = self._extract_general_title(text, category)
        
        # חילוץ שנה נפרדת
        if not result['year']:
            year_match = re.search(self.patterns['year_pattern'], text)
            if year_match:
                result['year'] = int(year_match.group(1))
        
        # חילוץ עונה ופרק
        season_match = re.search(self.patterns['season_episode'], text, re.IGNORECASE)
        if season_match:
            result['season'] = int(season_match.group(1))
            if season_match.group(2):
                result['episode'] = int(season_match.group(2))
        
        # חילוץ פרק נפרד
        if not result['episode']:
            episode_match = re.search(self.patterns['episode_only'], text, re.IGNORECASE)
            if episode_match:
                result['episode'] = int(episode_match.group(1))
        
        # חילוץ איכות
        quality_match = re.search(self.patterns['quality_pattern'], text, re.IGNORECASE)
        if quality_match:
            result['quality'] = quality_match.group(1).upper()
        
        return result
    
    def _extract_general_title(self, text: str, category: str) -> str:
        """חילוץ כותרת כללית"""
        text_clean = text.strip()
        
        # הסרת מילות מפתח בתחילת המשפט
        category_keywords = CONTENT_CATEGORIES.get(category, {}).get('keywords', [])
        for keyword in category_keywords:
            pattern = rf'\b{re.escape(keyword)}\b\s*:?\s*'
            text_clean = re.sub(pattern, '', text_clean, flags=re.IGNORECASE).strip()
        
        # הסרת מילות עזר נפוצות - אבל באופן חכם יותר
        stop_words = ['את', 'של', 'על', 'עם', 'אני רוצה', 'אפשר', 'יש', 'תן לי', 'תביא לי']
        for word in stop_words:
            # השתמש בביטויים רגולריים כדי להסיר רק מילים מלאות
            pattern = rf'\b{re.escape(word)}\b\s*'
            text_clean = re.sub(pattern, ' ', text_clean, flags=re.IGNORECASE).strip()
        
        # ניקוי רווחים כפולים
        text_clean = re.sub(r'\s+', ' ', text_clean)
        
        # לקיחת עד 10 מילים ראשונות
        words = text_clean.split()[:10]
        return ' '.join(words).strip()
    
    def _detect_priority(self, text: str) -> str:
        """זיהוי עדיפות הבקשה"""
        text_lower = text.lower()
        
        # בדיקת VIP
        for keyword in VIP_KEYWORDS:
            if keyword.lower() in text_lower:
                return 'vip'
        
        # בדיקת דחוף
        for keyword in URGENT_KEYWORDS:
            if keyword.lower() in text_lower:
                return 'urgent'
        
        # בדיקת עדיפות גבוהה
        for keyword in HIGH_KEYWORDS:
            if keyword.lower() in text_lower:
                return 'high'
        
        # בדיקות נוספות לעדיפות
        priority_indicators = {
            'urgent': ['!!', 'חירום', 'בעיה', 'לא עובד'],
            'high': ['בבקשה', 'זקוק', 'מחפש הרבה זמן', 'חשוב לי'],
            'low': ['אם אפשר', 'כשיהיה זמן', 'לא דחוף']
        }
        
        for priority, indicators in priority_indicators.items():
            for indicator in indicators:
                if indicator.lower() in text_lower:
                    return priority
        
        return 'medium'
    
    def _generate_tags(self, text: str, analysis: Dict) -> List[str]:
        """יצירת תגים לבקשה"""
        tags = []
        text_lower = text.lower()
        
        # תגי איכות
        if analysis.get('quality'):
            tags.append(f"quality:{analysis['quality']}")
        
        # תגי עונה ופרק
        if analysis.get('season'):
            tags.append(f"season:{analysis['season']}")
        if analysis.get('episode'):
            tags.append(f"episode:{analysis['episode']}")
        
        # תגי שנה
        if analysis.get('year'):
            decade = (analysis['year'] // 10) * 10
            tags.append(f"year:{analysis['year']}")
            tags.append(f"decade:{decade}s")
        
        # תגי שפה
        if 'עברית' in text_lower or 'כתוביות' in text_lower:
            tags.append('language:hebrew')
        if 'אנגלית' in text_lower or 'english' in text_lower:
            tags.append('language:english')
        
        # תגי פלטפורמות
        platforms = ['netflix', 'amazon', 'hbo', 'disney', 'apple tv', 'hulu']
        for platform in platforms:
            if platform in text_lower:
                tags.append(f"platform:{platform}")
        
        # תגי ז'אנרים
        genres = {
            'אקשן': 'action', 'קומדיה': 'comedy', 'דרמה': 'drama',
            'מדע בדיוני': 'sci-fi', 'אימה': 'horror', 'רומנטי': 'romance',
            'מתח': 'thriller', 'פנטזיה': 'fantasy', 'דוקומנטרי': 'documentary'
        }
        
        for hebrew_genre, english_genre in genres.items():
            if hebrew_genre in text_lower or english_genre in text_lower:
                tags.append(f"genre:{english_genre}")
        
        return tags
    
    def _calculate_confidence(self, text: str, analysis: Dict) -> int:
        """חישוב רמת ביטחון"""
        confidence = 0
        
        # ציון בסיסי גבוה יותר לפי קטגוריה
        if analysis['category'] != 'general':
            confidence += 35
        
        # בונוס גבוה יותר לכותרת ברורה
        if analysis['title'] and len(analysis['title']) > 2:
            confidence += 30
            # בונוס נוסף לכותרת ארוכה וברורה
            if len(analysis['title']) > 5:
                confidence += 10
        
        # בונוס לשנה
        if analysis['year']:
            confidence += 20
        
        # בונוס לפרטים נוספים
        if analysis['season']:
            confidence += 10
        if analysis['episode']:
            confidence += 10
        if analysis['quality']:
            confidence += 10
        
        # בונוס למילות מפתח חזקות - מורחב
        text_lower = text.lower()
        strong_indicators = ['הסדרה', 'הסרט', 'המשחק', 'האפליקציה', 'את', 'אפשר', 'רוצה', 'מחפש']
        for indicator in strong_indicators:
            if indicator in text_lower:
                confidence += 5
        
        # בונוס לשמות פרטיים (שמות של סדרות/סרטים מפורסמים)
        famous_titles = ['breaking bad', 'game of thrones', 'friends', 'the office', 'stranger things', 
                        'marvel', 'dc', 'batman', 'superman', 'spider-man', 'avatar', 'titanic']
        for title in famous_titles:
            if title in text_lower:
                confidence += 15
                break
        
        # הפחתה קטנה יותר לטקסט קצר
        if len(text.strip()) < 8:
            confidence -= 10
        
        # הפחתה להודעות לא קשורות
        unrelated_patterns = [
            r'^\b(תודה|thanks|אלוף|מלך)\b$',  # רק אם זה כל ההודעה
            r'^\?+$|^\.+$',
            r'^\b(בעמפ|bump|up)\b$'  # רק אם זה כל ההודעה
        ]
        
        for pattern in unrelated_patterns:
            if re.search(pattern, text_lower):
                confidence -= 40
                break
        
        return max(0, min(100, confidence))
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """סטטיסטיקות מנתח התוכן"""
        return {
            'categories_supported': len(CONTENT_CATEGORIES),
            'patterns_count': len(self.patterns),
            'advanced_keywords_count': sum(
                len(keywords) for cat_keywords in self.advanced_keywords.values() 
                for keywords in cat_keywords.values()
            )
        }
    
    def validate_analysis(self, analysis: Dict) -> Dict[str, List[str]]:
        """בדיקת תקינות ניתוח"""
        issues = {
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # בדיקת שגיאות
        if not analysis.get('title'):
            issues['errors'].append("לא נמצאה כותרת")
        
        if analysis.get('confidence', 0) < 30:
            issues['errors'].append("רמת ביטחון נמוכה מדי")
        
        # בדיקת אזהרות
        if analysis.get('year') and analysis['year'] < 1950:
            issues['warnings'].append("השנה נראית לא סבירה")
        
        if analysis.get('season') and analysis['season'] > 20:
            issues['warnings'].append("מספר עונה גבוה מאוד")
        
        # הצעות שיפור
        if not analysis.get('year'):
            issues['suggestions'].append("הוסף שנת יציאה לדיוק רב יותר")
        
        if analysis['category'] == 'series' and not analysis.get('season'):
            issues['suggestions'].append("ציין עונה ופרק לסדרות")
        
        return issues