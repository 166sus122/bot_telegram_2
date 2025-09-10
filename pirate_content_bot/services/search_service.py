#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search Service לבוט התמימים הפiראטים
חיפוש מתקדם בבקשות עם filtering ו-analytics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
import re
from collections import defaultdict, Counter
import json
from pirate_content_bot.utils.json_helpers import safe_json_dumps

logger = logging.getLogger(__name__)

class SearchService:
    """שירות חיפוש מתקדם"""
    
    def __init__(self, storage_manager, cache_manager=None):
        self.storage = storage_manager
        self.cache = cache_manager
        
        # מטמון חיפושים
        self._search_cache = {}
        self._popular_searches = Counter()
        self._search_history = []
        self._cache_timeout = 300  # 5 דקות
        
        # הגדרות חיפוש
        self.max_search_results = 100
        self.min_search_length = 2
        self.fuzzy_threshold = 0.6
        self.max_suggestions = 10
        
        # מילות עצירה בעברית ואנגלית
        self.stop_words = {
            'hebrew': {'את', 'של', 'על', 'עם', 'אל', 'מן', 'או', 'אבל', 'כי', 'אם', 'גם', 'כל', 'יש', 'לא', 'זה', 'היא', 'הוא'},
            'english': {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        }
        
        logger.info("Search Service initialized")
    
    # ========================= חיפוש בסיסי =========================
    
    async def search_requests(self, query: str, filters: Optional[Dict] = None, 
                            limit: int = 20, offset: int = 0) -> Tuple[List[Dict], int, Dict]:
        """
        חיפוש בקשות עם פילטרים
        
        Returns:
            (תוצאות, סה"כ תוצאות, metadata)
        """
        try:
            # ניקוי וvalidation של query
            cleaned_query = self._clean_search_query(query)
            if len(cleaned_query) < self.min_search_length:
                return [], 0, {'error': 'Search query too short'}
            
            # בדיקת מטמון
            cache_key = self._generate_search_cache_key(cleaned_query, filters, limit, offset)
            if cache_key in self._search_cache:
                cached_result, timestamp = self._search_cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self._cache_timeout):
                    return cached_result
            
            # רישום החיפוש
            self._track_search(cleaned_query)
            
            # בניית שאילתת חיפוש
            search_sql, search_params = self._build_search_query(cleaned_query, filters, limit, offset)
            count_sql, count_params = self._build_count_query(cleaned_query, filters)
            
            # ביצוע חיפוש
            search_results = self.storage.pool.execute_query(search_sql, search_params, fetch_all=True)
            count_result = self.storage.pool.execute_query(count_sql, count_params, fetch_one=True)
            total_count = count_result['total'] if count_result else 0
            
            # דירוג תוצאות
            ranked_results = self._rank_search_results(search_results, cleaned_query)
            
            # העשרת נתונים
            enriched_results = []
            for result in ranked_results:
                enriched = await self._enrich_search_result(result, cleaned_query)
                enriched_results.append(enriched)
            
            # מטא-דאטא
            metadata = {
                'query': query,
                'cleaned_query': cleaned_query,
                'total_results': total_count,
                'search_time_ms': 0,  # TODO: מדידת זמן
                'filters_applied': filters or {},
                'suggestions': await self._get_search_suggestions(cleaned_query)
            }
            
            # שמירה במטמון
            result_tuple = (enriched_results, total_count, metadata)
            self._search_cache[cache_key] = (result_tuple, datetime.now())
            
            return result_tuple
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return [], 0, {'error': str(e)}
    
    def _clean_search_query(self, query: str) -> str:
        """ניקוי שאילתת חיפוש"""
        if not query:
            return ""
        
        # הסרת תווים מיוחדים מסוכנים
        cleaned = re.sub(r'[<>"\']', '', query)
        
        # ניקוי רווחים מיותרים
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def _build_search_query(self, query: str, filters: Optional[Dict], 
                           limit: int, offset: int) -> Tuple[str, Tuple]:
        """בניית שאילתת SQL לחיפוש"""
        # בניית WHERE conditions
        where_conditions = []
        query_params = []
        
        # חיפוש בטקסט (full-text או LIKE)
        if self._has_fulltext_search():
            where_conditions.append("MATCH(title, original_text) AGAINST(%s IN NATURAL LANGUAGE MODE)")
            query_params.append(query)
        else:
            # fallback ל-LIKE search
            where_conditions.append("(title LIKE %s OR original_text LIKE %s)")
            like_query = f"%{query}%"
            query_params.extend([like_query, like_query])
        
        # פילטרים נוספים
        if filters:
            if filters.get('status'):
                if isinstance(filters['status'], list):
                    placeholders = ','.join(['%s'] * len(filters['status']))
                    where_conditions.append(f"status IN ({placeholders})")
                    query_params.extend(filters['status'])
                else:
                    where_conditions.append("status = %s")
                    query_params.append(filters['status'])
            
            if filters.get('category'):
                where_conditions.append("category = %s")
                query_params.append(filters['category'])
            
            if filters.get('user_id'):
                where_conditions.append("user_id = %s")
                query_params.append(filters['user_id'])
            
            if filters.get('date_from'):
                where_conditions.append("created_at >= %s")
                query_params.append(filters['date_from'])
            
            if filters.get('date_to'):
                where_conditions.append("created_at <= %s")
                query_params.append(filters['date_to'])
            
            if filters.get('priority'):
                where_conditions.append("priority = %s")
                query_params.append(filters['priority'])
            
            if filters.get('min_confidence'):
                where_conditions.append("confidence >= %s")
                query_params.append(filters['min_confidence'])
        
        # בניית השאילתה המלאה
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        search_query = f"""
        SELECT 
            id, user_id, username, first_name, title, original_text, 
            category, priority, status, confidence, created_at, updated_at,
            fulfilled_at, fulfilled_by, notes
        FROM content_requests 
        WHERE {where_clause}
        ORDER BY 
            CASE 
                WHEN status = 'pending' THEN 1
                WHEN status = 'fulfilled' THEN 2 
                ELSE 3 
            END,
            created_at DESC
        LIMIT %s OFFSET %s
        """
        
        query_params.extend([limit, offset])
        
        return search_query, tuple(query_params)
    
    def _build_count_query(self, query: str, filters: Optional[Dict]) -> Tuple[str, Tuple]:
        """בניית שאילתת ספירה"""
        where_conditions = []
        query_params = []
        
        # אותה לוגיקת חיפוש כמו בshearch_query
        if self._has_fulltext_search():
            where_conditions.append("MATCH(title, original_text) AGAINST(%s IN NATURAL LANGUAGE MODE)")
            query_params.append(query)
        else:
            where_conditions.append("(title LIKE %s OR original_text LIKE %s)")
            like_query = f"%{query}%"
            query_params.extend([like_query, like_query])
        
        # פילטרים (אותה לוגיקה כמו למעלה)
        if filters:
            if filters.get('status'):
                if isinstance(filters['status'], list):
                    placeholders = ','.join(['%s'] * len(filters['status']))
                    where_conditions.append(f"status IN ({placeholders})")
                    query_params.extend(filters['status'])
                else:
                    where_conditions.append("status = %s")
                    query_params.append(filters['status'])
            
            if filters.get('category'):
                where_conditions.append("category = %s")
                query_params.append(filters['category'])
            
            if filters.get('user_id'):
                where_conditions.append("user_id = %s")
                query_params.append(filters['user_id'])
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        count_query = f"SELECT COUNT(*) as total FROM content_requests WHERE {where_clause}"
        
        return count_query, tuple(query_params)
    
    def _has_fulltext_search(self) -> bool:
        """בדיקה אם יש full-text search זמין"""
        try:
            # בדיקה אם יש אינדקס full-text
            check_query = """
            SELECT COUNT(*) as count 
            FROM information_schema.statistics 
            WHERE table_name = 'content_requests' 
            AND index_type = 'FULLTEXT'
            AND table_schema = DATABASE()
            """
            
            result = self.storage.pool.execute_query(check_query, fetch_one=True)
            return result and result['count'] > 0
            
        except Exception as e:
            logger.debug(f"Full-text search check failed: {e}")
            return False
    
    # ========================= דירוג תוצאות =========================
    
    def _rank_search_results(self, results: List[Dict], query: str) -> List[Dict]:
        """דירוג תוצאות חיפוש לפי רלוונטיות"""
        if not results:
            return results
        
        query_words = set(self._extract_keywords(query.lower()))
        
        scored_results = []
        for result in results:
            score = self._calculate_relevance_score(result, query, query_words)
            result['search_score'] = score
            scored_results.append(result)
        
        # מיון לפי ציון (גבוה לנמוך)
        scored_results.sort(key=lambda x: x['search_score'], reverse=True)
        
        return scored_results
    
    def _calculate_relevance_score(self, result: Dict, query: str, query_words: Set[str]) -> float:
        """חישוב ציון רלוונטיות"""
        score = 0.0
        
        title = result.get('title', '').lower()
        text = result.get('original_text', '').lower()
        query_lower = query.lower()
        
        # התאמה מדויקת של כל השאילתה
        if query_lower in title:
            score += 100.0
        elif query_lower in text:
            score += 50.0
        
        # התאמת מילים בכותרת (משקל גבוה)
        title_words = set(self._extract_keywords(title))
        common_title_words = query_words.intersection(title_words)
        score += len(common_title_words) * 20.0
        
        # התאמת מילים בטקסט (משקל נמוך יותר)
        text_words = set(self._extract_keywords(text))
        common_text_words = query_words.intersection(text_words)
        score += len(common_text_words) * 5.0
        
        # בונוס לבקשות פופולריות (עם הרבה דירוגים)
        # if result.get('ratings_count', 0) > 3:
        #     score += 10.0
        
        # בונוס לבקשות חדשות
        created_at = result.get('created_at')
        if created_at:
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except (ValueError, TypeError) as e:
                    logger.debug(f"Invalid datetime format, using current time: {e}")
                    created_at = datetime.now()
            
            age_days = (datetime.now() - created_at).days
            if age_days < 7:
                score += 5.0
            elif age_days < 30:
                score += 2.0
        
        # בונוס לפי סטטוס
        status = result.get('status', '')
        if status == 'pending':
            score += 15.0  # בקשות ממתינות חשובות יותר
        elif status == 'fulfilled':
            score += 10.0
        
        # בונוס לפי עדיפות
        priority = result.get('priority', 'medium')
        priority_bonus = {
            'vip': 25.0, 'urgent': 20.0, 'high': 15.0, 
            'medium': 10.0, 'low': 5.0
        }
        score += priority_bonus.get(priority, 0)
        
        # בונוס לפי confidence
        confidence = result.get('confidence', 50)
        score += (confidence / 100) * 10.0
        
        return score
    
    def _extract_keywords(self, text: str) -> List[str]:
        """חילוץ מילות מפתח מטקסט"""
        # ניקוי טקסט
        words = re.findall(r'\b\w+\b', text)
        
        # סינון מילות עצירה
        filtered_words = []
        for word in words:
            word_lower = word.lower()
            if (len(word) >= 3 and 
                word_lower not in self.stop_words['hebrew'] and 
                word_lower not in self.stop_words['english']):
                filtered_words.append(word_lower)
        
        return filtered_words
    
    # ========================= חיפוש מתקדם =========================
    
    async def full_text_search(self, query: str, limit: int = 50) -> List[Dict]:
        """חיפוש full-text מתקדם"""
        try:
            if not self._has_fulltext_search():
                # fallback לחיפוש רגיל
                results, _, _ = await self.search_requests(query, limit=limit)
                return results
            
            # חיפוש full-text מתקדם
            search_query = """
            SELECT 
                *,
                MATCH(title, original_text) AGAINST(%s IN NATURAL LANGUAGE MODE) as relevance_score
            FROM content_requests 
            WHERE MATCH(title, original_text) AGAINST(%s IN NATURAL LANGUAGE MODE)
            ORDER BY relevance_score DESC, created_at DESC
            LIMIT %s
            """
            
            results = self.storage.pool.execute_query(search_query, (query, query, limit), fetch_all=True)
            
            # העשרת תוצאות
            enriched_results = []
            for result in results:
                enriched = await self._enrich_search_result(result, query)
                enriched_results.append(enriched)
            
            return enriched_results
            
        except Exception as e:
            logger.error(f"Full-text search failed: {e}")
            return []
    
    async def fuzzy_search(self, query: str, threshold: float = None, 
                          limit: int = 20) -> List[Dict]:
        """חיפוש fuzzy (דמיון חלקי)"""
        try:
            threshold = threshold or self.fuzzy_threshold
            
            # קבלת כל הכותרות לבדיקת דמיון
            all_requests_query = "SELECT id, title, original_text, category, status FROM content_requests"
            all_requests = self.storage.pool.execute_query(all_requests_query, fetch_all=True)
            
            # חישוב דמיון לכל בקשה
            fuzzy_matches = []
            for request in all_requests:
                title = request.get('title', '')
                similarity = self._calculate_fuzzy_similarity(query, title)
                
                if similarity >= threshold:
                    request['fuzzy_score'] = similarity
                    fuzzy_matches.append(request)
            
            # מיון לפי ציון דמיון
            fuzzy_matches.sort(key=lambda x: x['fuzzy_score'], reverse=True)
            
            # קבלת פרטים מלאים לתוצאות הטובות ביותר
            top_matches = fuzzy_matches[:limit]
            if not top_matches:
                return []
            
            # שליפת פרטים מלאים
            ids = [match['id'] for match in top_matches]
            placeholders = ','.join(['%s'] * len(ids))
            
            detailed_query = f"""
            SELECT * FROM content_requests 
            WHERE id IN ({placeholders})
            """
            
            detailed_results = self.storage.pool.execute_query(detailed_query, tuple(ids), fetch_all=True)
            
            # שמירת ציון הדמיון
            score_map = {match['id']: match['fuzzy_score'] for match in top_matches}
            for result in detailed_results:
                result['fuzzy_score'] = score_map.get(result['id'], 0)
            
            # מיון מחדש
            detailed_results.sort(key=lambda x: x.get('fuzzy_score', 0), reverse=True)
            
            return detailed_results
            
        except Exception as e:
            logger.error(f"Fuzzy search failed: {e}")
            return []
    
    def _calculate_fuzzy_similarity(self, text1: str, text2: str) -> float:
        """חישוב דמיון fuzzy בין שני טקסטים"""
        try:
            import difflib
            return difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        except ImportError:
            # fallback פשוט
            return self._simple_similarity(text1, text2)
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """חישוב דמיון פשוט"""
        words1 = set(self._extract_keywords(text1.lower()))
        words2 = set(self._extract_keywords(text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    # ========================= חיפוש לפי קריטריונים =========================
    
    async def search_by_user(self, user_id: int, query: Optional[str] = None, 
                           limit: int = 20) -> List[Dict]:
        """חיפוש בקשות של משתמש ספציפי"""
        filters = {'user_id': user_id}
        
        if query:
            results, _, _ = await self.search_requests(query, filters, limit)
        else:
            # כל הבקשות של המשתמש
            search_query = """
            SELECT * FROM content_requests 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
            """
            
            results = self.storage.pool.execute_query(search_query, (user_id, limit), fetch_all=True)
        
        return results
    
    async def search_by_category(self, category: str, query: Optional[str] = None, 
                               limit: int = 20) -> List[Dict]:
        """חיפוש בקטגוריה ספציפית"""
        filters = {'category': category}
        
        if query:
            results, _, _ = await self.search_requests(query, filters, limit)
        else:
            # כל הבקשות בקטגוריה
            search_query = """
            SELECT * FROM content_requests 
            WHERE category = %s 
            ORDER BY created_at DESC 
            LIMIT %s
            """
            
            results = self.storage.pool.execute_query(search_query, (category, limit), fetch_all=True)
        
        return results
    
    async def search_by_status(self, status: str, query: Optional[str] = None, 
                             limit: int = 20) -> List[Dict]:
        """חיפוש לפי סטטוס"""
        filters = {'status': status}
        
        if query:
            results, _, _ = await self.search_requests(query, filters, limit)
        else:
            # כל הבקשות עם הסטטוס
            search_query = """
            SELECT * FROM content_requests 
            WHERE status = %s 
            ORDER BY created_at DESC 
            LIMIT %s
            """
            
            results = self.storage.pool.execute_query(search_query, (status, limit), fetch_all=True)
        
        return results
    
    async def search_similar_requests(self, request_id: int, limit: int = 10) -> List[Dict]:
        """חיפוש בקשות דומות לבקשה נתונה"""
        try:
            # קבלת הבקשה המקורית
            original_request = self.storage.get_request(request_id)
            if not original_request:
                return []
            
            original_title = original_request.get('title', '') if isinstance(original_request, dict) else getattr(original_request, 'title', '')
            original_category = original_request.get('category', 'general') if isinstance(original_request, dict) else getattr(original_request, 'category', 'general')
            
            # חיפוש בקשות דומות
            similar_results = await self.fuzzy_search(original_title, threshold=0.4, limit=limit * 2)
            
            # סינון הבקשה המקורית ובקשות מאותה קטגוריה
            filtered_results = []
            for result in similar_results:
                if (result['id'] != request_id and 
                    result.get('category') == original_category):
                    filtered_results.append(result)
                
                if len(filtered_results) >= limit:
                    break
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Similar requests search failed: {e}")
            return []
    
    # ========================= הצעות חיפוש =========================
    
    async def _get_search_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """הצעות לשיפור החיפוש"""
        try:
            suggestions = []
            
            # הצעות מבוססות על חיפושים פופולריים
            popular_suggestions = await self._get_popular_search_suggestions(query, limit // 2)
            suggestions.extend(popular_suggestions)
            
            # הצעות מבוססות על כותרות קיימות
            title_suggestions = await self._get_title_based_suggestions(query, limit - len(suggestions))
            suggestions.extend(title_suggestions)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get search suggestions: {e}")
            return []
    
    async def _get_popular_search_suggestions(self, query: str, limit: int) -> List[str]:
        """הצעות מחיפושים פופולריים"""
        suggestions = []
        query_words = set(self._extract_keywords(query.lower()))
        
        for search_term, count in self._popular_searches.most_common(20):
            if search_term != query:
                search_words = set(self._extract_keywords(search_term.lower()))
                
                # אם יש חפיפה במילים
                if query_words.intersection(search_words):
                    suggestions.append(search_term)
                    
                    if len(suggestions) >= limit:
                        break
        
        return suggestions
    
    async def _get_title_based_suggestions(self, query: str, limit: int) -> List[str]:
        """הצעות מבוססות על כותרות"""
        try:
            # חיפוש כותרות שמתחילות או מכילות את השאילתה
            suggestion_query = """
            SELECT DISTINCT title, created_at
            FROM content_requests 
            WHERE title LIKE %s 
            ORDER BY created_at DESC 
            LIMIT %s
            """
            
            like_pattern = f"%{query}%"
            results = self.storage.pool.execute_query(suggestion_query, (like_pattern, limit * 2), fetch_all=True)
            
            suggestions = []
            for result in results:
                title = result['title']
                if title.lower() != query.lower() and len(title) > len(query):
                    suggestions.append(title)
                    
                    if len(suggestions) >= limit:
                        break
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Title-based suggestions failed: {e}")
            return []
    
    # ========================= מעקב וסטטיסטיקות =========================
    
    def _track_search(self, query: str):
        """מעקב אחר חיפושים"""
        self._popular_searches[query] += 1
        self._search_history.append({
            'query': query,
            'timestamp': datetime.now()
        })
        
        # שמירה של היסטוריה מוגבלת
        if len(self._search_history) > 1000:
            self._search_history = self._search_history[-500:]
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """קבלת החיפושים הפופולריים"""
        popular = []
        for query, count in self._popular_searches.most_common(limit):
            popular.append({
                'query': query,
                'search_count': count
            })
        
        return popular
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """סטטיסטיקות חיפוש"""
        total_searches = sum(self._popular_searches.values())
        unique_queries = len(self._popular_searches)
        
        # ניתוח לפי זמן
        recent_searches = [s for s in self._search_history 
                         if datetime.now() - s['timestamp'] < timedelta(hours=24)]
        
        return {
            'total_searches': total_searches,
            'unique_queries': unique_queries,
            'searches_last_24h': len(recent_searches),
            'cache_size': len(self._search_cache),
            'popular_searches': self.get_popular_searches(5),
            'avg_searches_per_query': total_searches / max(unique_queries, 1)
        }
    
    # ========================= פונקציות עזר =========================
    
    def _generate_search_cache_key(self, query: str, filters: Optional[Dict], 
                                 limit: int, offset: int) -> str:
        """יצירת מפתח מטמון לחיפוש"""
        filters_str = safe_json_dumps(filters, sort_keys=True, indent=None) if filters else ""
        return f"search:{query}:{filters_str}:{limit}:{offset}"
    
    async def _enrich_search_result(self, result: Dict, query: str) -> Dict:
        """העשרת תוצאת חיפוש"""
        try:
            # הוספת highlights
            result['highlights'] = self._generate_highlights(result, query)
            
            # הוספת גיל בקשה
            created_at = result.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except Exception as e:
                        logger.debug(f"Invalid datetime format: {e}")
                        created_at = datetime.now()
                
                age_hours = (datetime.now() - created_at).total_seconds() / 3600
                result['age_hours'] = int(age_hours)
                result['age_days'] = int(age_hours / 24)
            
            # הוספת מידע על קטגוריה
            category = result.get('category', 'general')
            result['category_display'] = self._get_category_display_name(category)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to enrich search result: {e}")
            return result
    
    def _generate_highlights(self, result: Dict, query: str) -> Dict[str, str]:
        """יצירת highlights בתוצאות חיפוש"""
        highlights = {}
        query_words = self._extract_keywords(query.lower())
        
        # highlight בכותרת
        title = result.get('title', '')
        highlights['title'] = self._highlight_text(title, query_words)
        
        # highlight בטקסט (רק קטע קצר)
        text = result.get('original_text', '')
        if text:
            # חיפוש המקום הטוב ביותר להציג
            best_snippet = self._find_best_snippet(text, query_words)
            highlights['snippet'] = self._highlight_text(best_snippet, query_words)
        
        return highlights
    
    def _highlight_text(self, text: str, query_words: List[str]) -> str:
        """הוספת הדגשות לטקסט"""
        highlighted = text
        
        for word in query_words:
            if len(word) >= 3:  # רק מילים של 3+ תווים
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                highlighted = pattern.sub(f"**{word}**", highlighted)
        
        return highlighted
    
    def _find_best_snippet(self, text: str, query_words: List[str], max_length: int = 150) -> str:
        """חיפוש הקטע הטוב ביותר להצגה"""
        if len(text) <= max_length:
            return text
        
        # חיפוש המיקום עם הכי הרבה מילות מפתח
        words = text.split()
        best_score = 0
        best_start = 0
        
        window_size = 20  # חלון של 20 מילים
        
        for i in range(len(words) - window_size + 1):
            window_text = ' '.join(words[i:i + window_size]).lower()
            score = sum(1 for word in query_words if word in window_text)
            
            if score > best_score:
                best_score = score
                best_start = i
        
        # יצירת הקטע
        snippet_words = words[best_start:best_start + window_size]
        snippet = ' '.join(snippet_words)
        
        if len(snippet) > max_length:
            snippet = snippet[:max_length - 3] + "..."
        
        return snippet
    
    def _get_category_display_name(self, category: str) -> str:
        """שם תצוגה לקטגוריה"""
        try:
            from main.config import CONTENT_CATEGORIES
            return CONTENT_CATEGORIES.get(category, {}).get('name', category.title())
        except Exception as e:
            logger.debug(f"Could not load content categories: {e}")
            return category.title()
    
    def clear_search_cache(self):
        """ניקוי מטמון החיפושים"""
        self._search_cache.clear()
        logger.info("Search cache cleared")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """סטטיסטיקות השירות"""
        return {
            'cache_size': len(self._search_cache),
            'cache_timeout': self._cache_timeout,
            'popular_searches_count': len(self._popular_searches),
            'search_history_size': len(self._search_history),
            'max_search_results': self.max_search_results,
            'min_search_length': self.min_search_length,
            'fuzzy_threshold': self.fuzzy_threshold,
            'has_fulltext': self._has_fulltext_search()
        }