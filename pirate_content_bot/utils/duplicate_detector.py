#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Duplicate Detector לבוט התמימים הפיראטים
זיהוי כפילויות מתקדם עם Fuzzy Matching
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Set
from collections import Counter
import string

logger = logging.getLogger(__name__)

class DuplicateDetector:
    """זיהוי כפילויות חכם"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        
        # משקלים לאלגוריתמי דמיון שונים
        self.algorithm_weights = {
            'levenshtein': 0.4,
            'jaccard': 0.3,
            'semantic': 0.3
        }
        
        # מילות עצירה לסינון
        self.stop_words = {
            'hebrew': {
                'את', 'של', 'על', 'עם', 'אל', 'מן', 'או', 'אבל', 'כי', 'אם', 'גם', 'כל', 
                'יש', 'לא', 'זה', 'היא', 'הוא', 'מה', 'איך', 'למה', 'איפה', 'מתי', 'כמה',
                'הסדרה', 'הסרט', 'המשחק', 'הספר', 'האפליקציה', 'התוכנה'
            },
            'english': {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
                'with', 'by', 'is', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does', 'did',
                'series', 'movie', 'film', 'game', 'book', 'app', 'application', 'software'
            }
        }
        
        # דפוסים לניקוי טקסט
        self.cleanup_patterns = [
            (r'\b(the|a|an)\s+', ''),  # הסרת מאמרים באנגלית
            (r'\b(ה|ו|ב|ל|מ|כ|ש)\w*\b', lambda m: m.group(0)[1:] if len(m.group(0)) > 2 else m.group(0)),  # הסרת קידומות עבריות
            (r'[^\w\s]', ' '),  # החלפת סימני פיסוק ברווחים
            (r'\s+', ' ')  # איחוד רווחים מרובים
        ]
        
        # דפוסים לזיהוי מידע נוסף
        self.info_patterns = {
            'year': r'\b(19|20)\d{2}\b',
            'season': r'\b(?:season|עונה|s)\s*(\d+)\b',
            'episode': r'\b(?:episode|פרק|e|ep)\s*(\d+)\b',
            'quality': r'\b(HD|4K|1080p|720p|480p|BluRay|DVD|WEB|HDTV)\b'
        }
        
        logger.info(f"Duplicate Detector initialized with threshold: {similarity_threshold}")
    
    # ========================= זיהוי כפילויות ראשי =========================
    
    def find_duplicates(self, title: str, existing_requests: List[Dict], 
                       threshold: Optional[float] = None) -> List[Tuple[int, float]]:
        """
        חיפוש כפילויות בין כותרת לרשימת בקשות קיימות
        
        Returns:
            רשימה של (request_id, similarity_score) ממויינת לפי דמיון
        """
        try:
            threshold = threshold or self.similarity_threshold
            
            if not title or not existing_requests:
                return []
            
            # נרמול כותרת החיפוש
            normalized_title = self.normalize_text(title)
            title_keywords = self.extract_keywords(normalized_title)
            
            duplicates = []
            
            for request in existing_requests:
                existing_title = request.get('title', '')
                if not existing_title:
                    continue
                
                # חישוב דמיון
                similarity = self.calculate_similarity(title, existing_title)
                
                if similarity >= threshold:
                    request_id = request.get('id')
                    duplicates.append((request_id, similarity))
            
            # מיון לפי דמיון (גבוה לנמוך)
            duplicates.sort(key=lambda x: x[1], reverse=True)
            
            logger.debug(f"Found {len(duplicates)} potential duplicates for '{title}'")
            return duplicates
            
        except Exception as e:
            logger.error(f"Failed to find duplicates: {e}")
            return []
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """חישוב דמיון מורכב בין שני טקסטים"""
        try:
            if not text1 or not text2:
                return 0.0
            
            # נרמול טקסטים
            norm_text1 = self.normalize_text(text1)
            norm_text2 = self.normalize_text(text2)
            
            # אם הטקסטים זהים לחלוטין אחרי נרמול
            if norm_text1 == norm_text2:
                return 1.0
            
            # חישוב דמיון עם מספר אלגוריתמים
            similarities = {}
            
            # Levenshtein similarity
            similarities['levenshtein'] = self.levenshtein_similarity(norm_text1, norm_text2)
            
            # Jaccard similarity (מבוסס על מילים)
            similarities['jaccard'] = self.jaccard_similarity(norm_text1, norm_text2)
            
            # Semantic similarity (מבוסס על מילות מפתח)
            similarities['semantic'] = self.semantic_similarity(norm_text1, norm_text2)
            
            # חישוב ציון משוקלל
            weighted_score = sum(
                similarities[alg] * weight 
                for alg, weight in self.algorithm_weights.items()
            )
            
            return min(max(weighted_score, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    # ========================= אלגוריתמי דמיון =========================
    
    def levenshtein_similarity(self, s1: str, s2: str) -> float:
        """חישוב דמיון Levenshtein (מרחק עריכה)"""
        try:
            if s1 == s2:
                return 1.0
            
            len_s1, len_s2 = len(s1), len(s2)
            
            if len_s1 == 0:
                return 0.0 if len_s2 > 0 else 1.0
            if len_s2 == 0:
                return 0.0
            
            # מטריצת מרחקים
            distances = [[0] * (len_s2 + 1) for _ in range(len_s1 + 1)]
            
            # אתחול
            for i in range(len_s1 + 1):
                distances[i][0] = i
            for j in range(len_s2 + 1):
                distances[0][j] = j
            
            # חישוב מרחקים
            for i in range(1, len_s1 + 1):
                for j in range(1, len_s2 + 1):
                    cost = 0 if s1[i-1] == s2[j-1] else 1
                    distances[i][j] = min(
                        distances[i-1][j] + 1,      # deletion
                        distances[i][j-1] + 1,      # insertion
                        distances[i-1][j-1] + cost  # substitution
                    )
            
            # המרה לדמיון (0-1)
            max_len = max(len_s1, len_s2)
            return 1.0 - (distances[len_s1][len_s2] / max_len)
            
        except Exception as e:
            logger.error(f"Levenshtein calculation failed: {e}")
            return 0.0
    
    def jaccard_similarity(self, s1: str, s2: str) -> float:
        """חישוב דמיון Jaccard (מבוסס על מילים)"""
        try:
            words1 = set(self.extract_keywords(s1))
            words2 = set(self.extract_keywords(s2))
            
            if not words1 and not words2:
                return 1.0
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Jaccard calculation failed: {e}")
            return 0.0
    
    def semantic_similarity(self, s1: str, s2: str) -> float:
        """חישוב דמיון סמנטי (מבוסס על מילות מפתח משוקללות)"""
        try:
            keywords1 = self.extract_keywords(s1)
            keywords2 = self.extract_keywords(s2)
            
            if not keywords1 or not keywords2:
                return 0.0
            
            # חישוב משקל לכל מילה (לפי תדירות)
            counter1 = Counter(keywords1)
            counter2 = Counter(keywords2)
            
            # חישוב קוסינוס similarity
            common_words = set(counter1.keys()).intersection(set(counter2.keys()))
            
            if not common_words:
                return 0.0
            
            # מכפלה פנימית
            dot_product = sum(counter1[word] * counter2[word] for word in common_words)
            
            # נורמות
            norm1 = sum(count ** 2 for count in counter1.values()) ** 0.5
            norm2 = sum(count ** 2 for count in counter2.values()) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    # ========================= עיבוד טקסט =========================
    
    def normalize_text(self, text: str) -> str:
        """נרמול טקסט לחיפוש"""
        try:
            if not text:
                return ""
            
            # המרה לאותיות קטנות
            normalized = text.lower().strip()
            
            # יישום דפוסי ניקוי
            for pattern, replacement in self.cleanup_patterns:
                if callable(replacement):
                    normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
                else:
                    normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
            
            # ניקוי רווחים מיותרים
            normalized = ' '.join(normalized.split())
            
            return normalized
            
        except Exception as e:
            logger.error(f"Text normalization failed: {e}")
            return text.lower()
    
    def extract_keywords(self, text: str) -> List[str]:
        """חילוץ מילות מפתח מטקסט"""
        try:
            if not text:
                return []
            
            # פיצול למילים
            words = re.findall(r'\b\w+\b', text.lower())
            
            # סינון מילות עצירה ומילים קצרות
            keywords = []
            for word in words:
                if (len(word) >= 2 and 
                    word not in self.stop_words['hebrew'] and 
                    word not in self.stop_words['english']):
                    keywords.append(word)
            
            return keywords
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []
    
    def remove_noise_words(self, text: str) -> str:
        """הסרת מילות רעש"""
        try:
            words = text.split()
            cleaned_words = []
            
            for word in words:
                word_lower = word.lower()
                if (word_lower not in self.stop_words['hebrew'] and 
                    word_lower not in self.stop_words['english'] and
                    len(word) >= 2):
                    cleaned_words.append(word)
            
            return ' '.join(cleaned_words)
            
        except Exception as e:
            logger.error(f"Noise removal failed: {e}")
            return text
    
    def standardize_title(self, title: str) -> str:
        """תקינון כותרת לפורמט אחיד"""
        try:
            if not title:
                return ""
            
            # נרמול בסיסי
            standardized = self.normalize_text(title)
            
            # חילוץ מידע מובנה
            extracted_info = self.extract_metadata(standardized)
            
            # בניית כותרת מתוקנת
            clean_title = standardized
            
            # הסרת מידע שחולץ כבר
            for info_type, pattern in self.info_patterns.items():
                clean_title = re.sub(pattern, '', clean_title, flags=re.IGNORECASE)
            
            # ניקוי סופי
            clean_title = ' '.join(clean_title.split())
            
            # הוספת מידע מחדש בפורמט אחיד
            if extracted_info.get('year'):
                clean_title += f" {extracted_info['year']}"
            
            return clean_title.strip()
            
        except Exception as e:
            logger.error(f"Title standardization failed: {e}")
            return title
    
    def extract_metadata(self, text: str) -> Dict[str, any]:
        """חילוץ מטא-דאטא מטקסט"""
        try:
            metadata = {}
            
            for info_type, pattern in self.info_patterns.items():
                matches = re.findall(pattern, text, flags=re.IGNORECASE)
                if matches:
                    if info_type in ['season', 'episode']:
                        # המרה למספר
                        try:
                            metadata[info_type] = int(matches[0])
                        except (ValueError, TypeError) as e:
                            logger.debug(f"Could not convert {matches[0]} to int: {e}")
                            metadata[info_type] = matches[0]
                    elif info_type == 'year':
                        try:
                            year = int(matches[0])
                            if 1900 <= year <= 2030:  # שנים הגיוניות
                                metadata[info_type] = year
                        except (ValueError, TypeError) as e:
                            logger.debug(f"Invalid year format: {matches[0]} - {e}")
                    else:
                        metadata[info_type] = matches[0].upper()
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return {}
    
    # ========================= חיפוש מתקדם =========================
    
    def fuzzy_match(self, query: str, candidates: List[str], 
                   threshold: Optional[float] = None) -> List[Tuple[str, float]]:
        """חיפוש fuzzy במועמדים"""
        try:
            threshold = threshold or self.similarity_threshold
            matches = []
            
            for candidate in candidates:
                similarity = self.calculate_similarity(query, candidate)
                if similarity >= threshold:
                    matches.append((candidate, similarity))
            
            # מיון לפי דמיון
            matches.sort(key=lambda x: x[1], reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"Fuzzy matching failed: {e}")
            return []
    
    def find_similar_titles(self, title: str, title_list: List[str], 
                          limit: int = 5, min_threshold: float = 0.3) -> List[Dict[str, any]]:
        """חיפוש כותרות דומות"""
        try:
            if not title or not title_list:
                return []
            
            similarities = []
            
            for existing_title in title_list:
                similarity = self.calculate_similarity(title, existing_title)
                
                if similarity >= min_threshold:
                    similarities.append({
                        'title': existing_title,
                        'similarity': similarity,
                        'match_type': self._classify_match_type(similarity),
                        'normalized_title': self.normalize_text(existing_title)
                    })
            
            # מיון ומגבלה
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Similar titles search failed: {e}")
            return []
    
    def _classify_match_type(self, similarity: float) -> str:
        """סיווג סוג ההתאמה"""
        if similarity >= 0.95:
            return 'exact'
        elif similarity >= 0.85:
            return 'very_high'
        elif similarity >= 0.7:
            return 'high'
        elif similarity >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    # ========================= הגדרות מתקדמות =========================
    
    def set_threshold(self, threshold: float):
        """עדכון רף הדמיון"""
        if 0.0 <= threshold <= 1.0:
            self.similarity_threshold = threshold
            logger.info(f"Similarity threshold updated to: {threshold}")
        else:
            logger.warning(f"Invalid threshold: {threshold}. Must be between 0.0 and 1.0")
    
    def add_custom_stopwords(self, words: List[str], language: str = 'hebrew'):
        """הוספת מילות עצירה מותאמות אישית"""
        if language in self.stop_words:
            self.stop_words[language].update(word.lower() for word in words)
            logger.info(f"Added {len(words)} custom stopwords to {language}")
        else:
            logger.warning(f"Unsupported language: {language}")
    
    def update_algorithm_weights(self, weights: Dict[str, float]):
        """עדכון משקלי האלגוריתמים"""
        try:
            # בדיקת תקינות
            total_weight = sum(weights.values())
            if abs(total_weight - 1.0) > 0.01:
                logger.warning(f"Algorithm weights sum to {total_weight}, not 1.0")
            
            # עדכון משקלים רק עבור אלגוריתמים קיימים
            for alg, weight in weights.items():
                if alg in self.algorithm_weights:
                    self.algorithm_weights[alg] = weight
                else:
                    logger.warning(f"Unknown algorithm: {alg}")
            
            logger.info(f"Updated algorithm weights: {self.algorithm_weights}")
            
        except Exception as e:
            logger.error(f"Failed to update algorithm weights: {e}")
    
    # ========================= סטטיסטיקות ואבחון =========================
    
    def get_detection_stats(self) -> Dict[str, any]:
        """קבלת סטטיסטיקות זיהוי"""
        return {
            'similarity_threshold': self.similarity_threshold,
            'algorithm_weights': self.algorithm_weights.copy(),
            'stop_words_count': {
                lang: len(words) for lang, words in self.stop_words.items()
            },
            'cleanup_patterns_count': len(self.cleanup_patterns),
            'info_patterns': list(self.info_patterns.keys())
        }
    
    def test_similarity_algorithms(self, text1: str, text2: str) -> Dict[str, float]:
        """בדיקת כל אלגוריתמי הדמיון"""
        try:
            norm_text1 = self.normalize_text(text1)
            norm_text2 = self.normalize_text(text2)
            
            results = {
                'levenshtein': self.levenshtein_similarity(norm_text1, norm_text2),
                'jaccard': self.jaccard_similarity(norm_text1, norm_text2),
                'semantic': self.semantic_similarity(norm_text1, norm_text2),
                'combined': self.calculate_similarity(text1, text2)
            }
            
            results['normalized_text1'] = norm_text1
            results['normalized_text2'] = norm_text2
            results['keywords1'] = self.extract_keywords(norm_text1)
            results['keywords2'] = self.extract_keywords(norm_text2)
            
            return results
            
        except Exception as e:
            logger.error(f"Algorithm testing failed: {e}")
            return {}
    
    def analyze_text_features(self, text: str) -> Dict[str, any]:
        """ניתוח מאפייני טקסט"""
        try:
            normalized = self.normalize_text(text)
            keywords = self.extract_keywords(normalized)
            metadata = self.extract_metadata(text)
            
            return {
                'original_text': text,
                'normalized_text': normalized,
                'keywords': keywords,
                'keyword_count': len(keywords),
                'metadata': metadata,
                'length': len(text),
                'word_count': len(text.split()),
                'has_numbers': bool(re.search(r'\d', text)),
                'has_special_chars': bool(re.search(r'[^\w\s]', text)),
                'estimated_language': self._detect_language_hints(text)
            }
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return {}
    
    def _detect_language_hints(self, text: str) -> str:
        """זיהוי רמזים לשפה"""
        hebrew_chars = len(re.findall(r'[\u0590-\u05FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if hebrew_chars > english_chars:
            return 'hebrew'
        elif english_chars > hebrew_chars:
            return 'english'
        else:
            return 'mixed'
    
    async def cleanup_cache(self):
        """ניקוי מטמון כפילויות"""
        try:
            if hasattr(self, 'cache') and self.cache:
                # ניקוי ערכים ישנים
                self.cache.clear()
                logger.debug("🧹 Duplicate cache cleaned")
            else:
                logger.debug("🧹 No duplicate cache to clean")
        except Exception as e:
            logger.error(f"Failed to clean duplicate cache: {e}")