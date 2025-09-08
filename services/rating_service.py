#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rating Service לבוט התמימים הפיראטים
ניהול מערכת דירוגים ומדדי שביעות רצון
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from statistics import mean, median
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class RatingService:
    """שירות ניהול דירוגים ושביעות רצון"""
    
    def __init__(self, storage_manager):
        self.storage = storage_manager
        
        # מטמון לביצועים
        self._rating_cache = {}
        self._stats_cache = {}
        self._cache_timeout = 300  # 5 דקות
        
        # הגדרות מערכת דירוג
        self.min_rating = 1
        self.max_rating = 5
        self.default_rating = 5
        
        # הגדרות אנליטיקס
        self.satisfaction_threshold = 4.0  # מעל 4 נחשב מרוצה
        self.poor_rating_threshold = 2.0   # מתחת ל-2 נחשב גרוע
        
        logger.info("Rating Service initialized")
    
    # ========================= ניהול דירוגים בסיסי =========================
    
    async def save_rating(self, request_id: int, user_id: int, rating: int, 
                         comment: Optional[str] = None, metadata: Dict = None) -> bool:
        """
        שמירת דירוג חדש או עדכון קיים
        
        Args:
            request_id: ID של הבקשה
            user_id: ID של המשתמש המדרג
            rating: דירוג 1-5
            comment: הערה אופציונלית
            metadata: מטא-דאטא נוספת
        """
        try:
            # בדיקת תקינות
            validation_errors = self._validate_rating_data(request_id, user_id, rating, comment)
            if validation_errors:
                logger.warning(f"Rating validation failed: {validation_errors}")
                return False
            
            # בדיקה אם המשתמש כבר דירג את הבקשה הזו
            existing_rating = await self.get_user_rating_for_request(request_id, user_id)
            
            # שמירת הדירוג
            success = self.storage.save_rating(request_id, user_id, rating, comment)
            
            if success:
                # עדכון מטמון
                self._clear_rating_cache(request_id)
                self._clear_stats_cache()
                
                # לוג הפעילות
                action = "updated" if existing_rating else "created"
                await self._log_rating_activity(request_id, user_id, rating, action, metadata)
                
                # עדכון סטטיסטיקות
                await self._update_rating_statistics(request_id, user_id, rating, existing_rating)
                
                logger.info(f"Rating {action} successfully: request {request_id}, user {user_id}, rating {rating}")
                
                # התראה למנהלים על דירוג נמוך
                if rating <= self.poor_rating_threshold:
                    await self._notify_poor_rating(request_id, user_id, rating, comment)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save rating: {e}")
            return False
    
    async def get_request_ratings(self, request_id: int, include_comments: bool = True) -> List[Dict]:
        """קבלת כל הדירוגים של בקשה"""
        try:
            # בדיקת מטמון
            cache_key = f"ratings_{request_id}_{include_comments}"
            if cache_key in self._rating_cache:
                cached_data, timestamp = self._rating_cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self._cache_timeout):
                    return cached_data
            
            # קבלה מהמסד נתונים
            ratings = self.storage.get_request_ratings(request_id)
            
            if not include_comments:
                # הסרת הערות אם לא נדרש
                ratings = [{k: v for k, v in rating.items() if k != 'comment'} 
                          for rating in ratings]
            
            # העשרת נתונים
            enriched_ratings = []
            for rating in ratings:
                enriched = await self._enrich_rating_data(rating)
                enriched_ratings.append(enriched)
            
            # שמירה במטמון
            self._rating_cache[cache_key] = (enriched_ratings, datetime.now())
            
            return enriched_ratings
            
        except Exception as e:
            logger.error(f"Failed to get request ratings: {e}")
            return []
    
    async def get_user_rating_for_request(self, request_id: int, user_id: int) -> Optional[Dict]:
        """קבלת דירוג של משתמש ספציפי לבקשה ספציפית"""
        try:
            ratings = await self.get_request_ratings(request_id)
            
            for rating in ratings:
                if rating.get('user_id') == user_id:
                    return rating
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user rating: {e}")
            return None
    
    async def get_user_ratings_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """קבלת היסטוריית דירוגים של משתמש"""
        try:
            query = """
            SELECT cr.*, req.title, req.category, req.fulfilled_at
            FROM content_ratings cr
            JOIN content_requests req ON cr.request_id = req.id
            WHERE cr.user_id = %s
            ORDER BY cr.created_at DESC
            LIMIT %s
            """
            
            ratings = self.storage.pool.execute_query(query, (user_id, limit), fetch_all=True)
            
            # העשרת נתונים
            enriched_ratings = []
            for rating in ratings:
                enriched = await self._enrich_rating_data(rating)
                enriched_ratings.append(enriched)
            
            return enriched_ratings
            
        except Exception as e:
            logger.error(f"Failed to get user ratings history: {e}")
            return []
    
    # ========================= חישוב מדדים =========================
    
    async def calculate_request_metrics(self, request_id: int) -> Dict[str, Any]:
        """חישוב מדדי דירוג לבקשה"""
        try:
            ratings = await self.get_request_ratings(request_id, include_comments=False)
            
            if not ratings:
                return {
                    'request_id': request_id,
                    'total_ratings': 0,
                    'average_rating': None,
                    'median_rating': None,
                    'rating_distribution': {},
                    'satisfaction_rate': 0.0,
                    'recommendation_score': 'insufficient_data'
                }
            
            # חילוץ ציונים
            scores = [r['rating'] for r in ratings]
            
            # חישובים בסיסיים
            average_rating = mean(scores)
            median_rating = median(scores)
            
            # התפלגות דירוגים
            rating_distribution = dict(Counter(scores))
            
            # שיעור שביעות רצון
            satisfied_count = sum(1 for score in scores if score >= self.satisfaction_threshold)
            satisfaction_rate = (satisfied_count / len(scores)) * 100
            
            # ציון המלצה
            recommendation_score = self._calculate_recommendation_score(average_rating, len(scores))
            
            return {
                'request_id': request_id,
                'total_ratings': len(ratings),
                'average_rating': round(average_rating, 2),
                'median_rating': median_rating,
                'rating_distribution': rating_distribution,
                'satisfaction_rate': round(satisfaction_rate, 1),
                'recommendation_score': recommendation_score,
                'latest_rating_date': max(r['created_at'] for r in ratings).isoformat() if ratings else None
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate request metrics: {e}")
            return {}
    
    def _calculate_recommendation_score(self, average_rating: float, total_ratings: int) -> str:
        """חישוב ציון המלצה כולל"""
        if total_ratings < 3:
            return 'insufficient_data'
        elif average_rating >= 4.5:
            return 'excellent'
        elif average_rating >= 4.0:
            return 'very_good'
        elif average_rating >= 3.5:
            return 'good'
        elif average_rating >= 3.0:
            return 'average'
        elif average_rating >= 2.5:
            return 'below_average'
        else:
            return 'poor'
    
    # ========================= אנליטיקס מתקדם =========================
    
    async def get_satisfaction_metrics(self, period_days: int = 30) -> Dict[str, Any]:
        """מדדי שביעות רצון כלליים"""
        try:
            # בדיקת מטמון
            cache_key = f"satisfaction_metrics_{period_days}"
            if cache_key in self._stats_cache:
                cached_data, timestamp = self._stats_cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=self._cache_timeout):
                    return cached_data
            
            start_date = datetime.now() - timedelta(days=period_days)
            
            # שאילתת מדדים בסיסיים
            query = """
            SELECT 
                COUNT(*) as total_ratings,
                AVG(rating) as average_rating,
                COUNT(CASE WHEN rating >= 4 THEN 1 END) as satisfied_count,
                COUNT(CASE WHEN rating <= 2 THEN 1 END) as poor_count,
                COUNT(DISTINCT request_id) as rated_requests,
                COUNT(DISTINCT user_id) as rating_users
            FROM content_ratings
            WHERE created_at >= %s
            """
            
            result = self.storage.pool.execute_query(query, (start_date,), fetch_one=True)
            
            if not result or result['total_ratings'] == 0:
                return {'period_days': period_days, 'no_data': True}
            
            # חישוב מדדים נוספים
            total_ratings = result['total_ratings']
            satisfied_count = result['satisfied_count']
            poor_count = result['poor_count']
            
            satisfaction_rate = (satisfied_count / total_ratings) * 100
            poor_rating_rate = (poor_count / total_ratings) * 100
            
            # התפלגות דירוגים
            distribution_query = """
            SELECT rating, COUNT(*) as count
            FROM content_ratings
            WHERE created_at >= %s
            GROUP BY rating
            ORDER BY rating
            """
            
            distribution_results = self.storage.pool.execute_query(distribution_query, (start_date,), fetch_all=True)
            rating_distribution = {str(r['rating']): r['count'] for r in distribution_results}
            
            # מגמות יומיות
            daily_trends = await self._get_daily_rating_trends(start_date)
            
            # השוואה לתקופה הקודמת
            previous_period = await self._get_previous_period_comparison(start_date, period_days)
            
            metrics = {
                'period_days': period_days,
                'start_date': start_date.isoformat(),
                'total_ratings': total_ratings,
                'average_rating': round(result['average_rating'], 2),
                'satisfaction_rate': round(satisfaction_rate, 1),
                'poor_rating_rate': round(poor_rating_rate, 1),
                'rated_requests': result['rated_requests'],
                'rating_users': result['rating_users'],
                'rating_distribution': rating_distribution,
                'daily_trends': daily_trends,
                'comparison_to_previous': previous_period,
                'recommendation_summary': self._generate_recommendation_summary(result['average_rating'], satisfaction_rate)
            }
            
            # שמירה במטמון
            self._stats_cache[cache_key] = (metrics, datetime.now())
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get satisfaction metrics: {e}")
            return {}
    
    async def get_admin_performance(self, admin_id: Optional[int] = None, period_days: int = 30) -> Dict[str, Any]:
        """מדדי ביצועים של מנהלים"""
        try:
            start_date = datetime.now() - timedelta(days=period_days)
            
            # שאילתת ביצועים
            if admin_id:
                # ביצועי מנהל ספציפי
                query = """
                SELECT 
                    cr.rating,
                    cr.comment,
                    cr.created_at,
                    req.fulfilled_by,
                    req.title,
                    req.category,
                    req.fulfilled_at,
                    req.created_at as request_created
                FROM content_ratings cr
                JOIN content_requests req ON cr.request_id = req.id
                WHERE req.fulfilled_by = %s 
                    AND req.status = 'fulfilled'
                    AND cr.created_at >= %s
                ORDER BY cr.created_at DESC
                """
                params = (admin_id, start_date)
            else:
                # ביצועים של כל המנהלים
                query = """
                SELECT 
                    req.fulfilled_by,
                    COUNT(cr.rating) as total_ratings,
                    AVG(cr.rating) as average_rating,
                    COUNT(CASE WHEN cr.rating >= 4 THEN 1 END) as satisfied_ratings,
                    COUNT(CASE WHEN cr.rating <= 2 THEN 1 END) as poor_ratings,
                    COUNT(req.id) as total_fulfilled
                FROM content_requests req
                LEFT JOIN content_ratings cr ON req.id = cr.request_id
                WHERE req.status = 'fulfilled' 
                    AND req.fulfilled_at >= %s
                    AND req.fulfilled_by IS NOT NULL
                GROUP BY req.fulfilled_by
                ORDER BY average_rating DESC, total_ratings DESC
                """
                params = (start_date,)
            
            results = self.storage.pool.execute_query(query, params, fetch_all=True)
            
            if admin_id:
                # עיבוד נתונים למנהל יחיד
                return await self._process_single_admin_performance(admin_id, results, start_date)
            else:
                # עיבוד נתונים לכל המנהלים
                return await self._process_all_admins_performance(results, start_date)
                
        except Exception as e:
            logger.error(f"Failed to get admin performance: {e}")
            return {}
    
    async def _process_single_admin_performance(self, admin_id: int, ratings_data: List[Dict], start_date: datetime) -> Dict:
        """עיבוד ביצועי מנהל יחיד"""
        if not ratings_data:
            return {
                'admin_id': admin_id,
                'period_days': (datetime.now() - start_date).days,
                'no_ratings': True
            }
        
        scores = [r['rating'] for r in ratings_data]
        
        # מדדים בסיסיים
        total_ratings = len(scores)
        average_rating = mean(scores)
        satisfied_count = sum(1 for score in scores if score >= 4)
        poor_count = sum(1 for score in scores if score <= 2)
        
        # זמני תגובה
        response_times = []
        for rating_data in ratings_data:
            if rating_data['request_created'] and rating_data['fulfilled_at']:
                request_created = rating_data['request_created']
                fulfilled_at = rating_data['fulfilled_at']
                
                if isinstance(request_created, str):
                    request_created = datetime.fromisoformat(request_created.replace('Z', '+00:00'))
                if isinstance(fulfilled_at, str):
                    fulfilled_at = datetime.fromisoformat(fulfilled_at.replace('Z', '+00:00'))
                
                response_time_hours = (fulfilled_at - request_created).total_seconds() / 3600
                response_times.append(response_time_hours)
        
        # הערות שליליות
        negative_comments = [r for r in ratings_data if r['comment'] and r['rating'] <= 3]
        
        return {
            'admin_id': admin_id,
            'period_days': (datetime.now() - start_date).days,
            'total_ratings': total_ratings,
            'average_rating': round(average_rating, 2),
            'satisfaction_rate': round((satisfied_count / total_ratings) * 100, 1),
            'poor_rating_rate': round((poor_count / total_ratings) * 100, 1),
            'average_response_time_hours': round(mean(response_times), 1) if response_times else None,
            'median_response_time_hours': round(median(response_times), 1) if response_times else None,
            'negative_comments_count': len(negative_comments),
            'performance_grade': self._calculate_performance_grade(average_rating, satisfied_count / total_ratings),
            'improvement_suggestions': self._generate_improvement_suggestions(average_rating, poor_count / total_ratings)
        }
    
    async def get_category_satisfaction(self, period_days: int = 30) -> List[Dict]:
        """שביעות רצון לפי קטגוריות"""
        try:
            start_date = datetime.now() - timedelta(days=period_days)
            
            query = """
            SELECT 
                req.category,
                COUNT(cr.rating) as total_ratings,
                AVG(cr.rating) as average_rating,
                COUNT(CASE WHEN cr.rating >= 4 THEN 1 END) as satisfied_count,
                COUNT(CASE WHEN cr.rating <= 2 THEN 1 END) as poor_count
            FROM content_ratings cr
            JOIN content_requests req ON cr.request_id = req.id
            WHERE cr.created_at >= %s
            GROUP BY req.category
            ORDER BY average_rating DESC, total_ratings DESC
            """
            
            results = self.storage.pool.execute_query(query, (start_date,), fetch_all=True)
            
            category_stats = []
            for result in results:
                total_ratings = result['total_ratings']
                satisfied_count = result['satisfied_count']
                poor_count = result['poor_count']
                
                category_stats.append({
                    'category': result['category'],
                    'display_name': self._get_category_display_name(result['category']),
                    'total_ratings': total_ratings,
                    'average_rating': round(result['average_rating'], 2),
                    'satisfaction_rate': round((satisfied_count / total_ratings) * 100, 1),
                    'poor_rating_rate': round((poor_count / total_ratings) * 100, 1),
                    'performance_indicator': self._get_performance_indicator(result['average_rating'])
                })
            
            return category_stats
            
        except Exception as e:
            logger.error(f"Failed to get category satisfaction: {e}")
            return []
    
    async def get_trending_ratings(self, days: int = 7, min_ratings: int = 3) -> Dict[str, List[Dict]]:
        """מדדי דירוגים פופולריים"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # בקשות עם הכי הרבה דירוגים
            most_rated_query = """
            SELECT 
                req.id, req.title, req.category,
                COUNT(cr.rating) as rating_count,
                AVG(cr.rating) as average_rating
            FROM content_requests req
            JOIN content_ratings cr ON req.id = cr.request_id
            WHERE cr.created_at >= %s
            GROUP BY req.id, req.title, req.category
            HAVING rating_count >= %s
            ORDER BY rating_count DESC, average_rating DESC
            LIMIT 10
            """
            
            most_rated = self.storage.pool.execute_query(most_rated_query, (start_date, min_ratings), fetch_all=True)
            
            # בקשות עם הדירוג הגבוה ביותר
            highest_rated_query = """
            SELECT 
                req.id, req.title, req.category,
                COUNT(cr.rating) as rating_count,
                AVG(cr.rating) as average_rating
            FROM content_requests req
            JOIN content_ratings cr ON req.id = cr.request_id
            WHERE cr.created_at >= %s
            GROUP BY req.id, req.title, req.category
            HAVING rating_count >= %s AND average_rating >= 4.5
            ORDER BY average_rating DESC, rating_count DESC
            LIMIT 10
            """
            
            highest_rated = self.storage.pool.execute_query(highest_rated_query, (start_date, min_ratings), fetch_all=True)
            
            # בקשות שצריכות תשומת לב (דירוג נמוך)
            needs_attention_query = """
            SELECT 
                req.id, req.title, req.category,
                COUNT(cr.rating) as rating_count,
                AVG(cr.rating) as average_rating
            FROM content_requests req
            JOIN content_ratings cr ON req.id = cr.request_id
            WHERE cr.created_at >= %s
            GROUP BY req.id, req.title, req.category
            HAVING rating_count >= %s AND average_rating <= 3.0
            ORDER BY average_rating ASC, rating_count DESC
            LIMIT 10
            """
            
            needs_attention = self.storage.pool.execute_query(needs_attention_query, (start_date, min_ratings), fetch_all=True)
            
            # עיבוד התוצאות
            trending_data = {
                'most_rated': [self._format_trending_item(item) for item in most_rated],
                'highest_rated': [self._format_trending_item(item) for item in highest_rated],
                'needs_attention': [self._format_trending_item(item) for item in needs_attention],
                'period_days': days,
                'min_ratings_threshold': min_ratings
            }
            
            return trending_data
            
        except Exception as e:
            logger.error(f"Failed to get trending ratings: {e}")
            return {}
    
    # ========================= דוחות ומומחיות =========================
    
    async def generate_satisfaction_report(self, period: str = 'month') -> Dict[str, Any]:
        """יצירת דוח שביעות רצון מקיף"""
        try:
            # קביעת תקופה
            period_days = {
                'week': 7,
                'month': 30,
                'quarter': 90,
                'year': 365
            }.get(period, 30)
            
            # איסוף כל הנתונים
            satisfaction_metrics = await self.get_satisfaction_metrics(period_days)
            category_satisfaction = await self.get_category_satisfaction(period_days)
            admin_performance = await self.get_admin_performance(period_days=period_days)
            trending_ratings = await self.get_trending_ratings(days=min(period_days, 14))
            
            # ניתוח מסקנות
            insights = self._generate_satisfaction_insights(satisfaction_metrics, category_satisfaction)
            recommendations = self._generate_satisfaction_recommendations(satisfaction_metrics, category_satisfaction, admin_performance)
            
            report = {
                'report_type': 'satisfaction_analysis',
                'period': period,
                'period_days': period_days,
                'generated_at': datetime.now().isoformat(),
                'overview': satisfaction_metrics,
                'category_breakdown': category_satisfaction,
                'admin_performance_summary': self._summarize_admin_performance(admin_performance),
                'trending_content': trending_ratings,
                'key_insights': insights,
                'recommendations': recommendations,
                'executive_summary': self._create_executive_summary(satisfaction_metrics, insights)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate satisfaction report: {e}")
            return {}
    
    async def get_low_rated_requests(self, threshold: float = 2.5, period_days: int = 30) -> List[Dict]:
        """קבלת בקשות עם דירוג נמוך לטיפול"""
        try:
            start_date = datetime.now() - timedelta(days=period_days)
            
            query = """
            SELECT 
                req.id, req.title, req.category, req.fulfilled_by,
                req.fulfilled_at, req.created_at,
                COUNT(cr.rating) as rating_count,
                AVG(cr.rating) as average_rating,
                GROUP_CONCAT(cr.comment SEPARATOR '|||') as comments
            FROM content_requests req
            JOIN content_ratings cr ON req.id = cr.request_id
            WHERE cr.created_at >= %s AND req.status = 'fulfilled'
            GROUP BY req.id
            HAVING average_rating <= %s AND rating_count >= 2
            ORDER BY average_rating ASC, rating_count DESC
            """
            
            results = self.storage.pool.execute_query(query, (start_date, threshold), fetch_all=True)
            
            low_rated_requests = []
            for result in results:
                # עיבוד הערות
                comments = []
                if result['comments']:
                    raw_comments = result['comments'].split('|||')
                    comments = [c.strip() for c in raw_comments if c.strip()]
                
                low_rated_requests.append({
                    'request_id': result['id'],
                    'title': result['title'],
                    'category': result['category'],
                    'fulfilled_by': result['fulfilled_by'],
                    'fulfilled_at': result['fulfilled_at'],
                    'rating_count': result['rating_count'],
                    'average_rating': round(result['average_rating'], 2),
                    'comments': comments[:3],  # רק 3 הערות ראשונות
                    'urgency_level': self._calculate_issue_urgency(result['average_rating'], result['rating_count'])
                })
            
            return low_rated_requests
            
        except Exception as e:
            logger.error(f"Failed to get low rated requests: {e}")
            return []
    
    # ========================= פונקציות עזר =========================
    
    def _validate_rating_data(self, request_id: int, user_id: int, rating: int, comment: Optional[str]) -> List[str]:
        """בדיקת תקינות נתוני דירוג"""
        errors = []
        
        if not request_id or request_id <= 0:
            errors.append("Invalid request ID")
        
        if not user_id or user_id <= 0:
            errors.append("Invalid user ID")
        
        if not isinstance(rating, int) or rating < self.min_rating or rating > self.max_rating:
            errors.append(f"Rating must be between {self.min_rating} and {self.max_rating}")
        
        if comment and len(comment) > 500:
            errors.append("Comment too long (max 500 characters)")
        
        return errors
    
    async def _enrich_rating_data(self, rating: Dict) -> Dict:
        """העשרת נתוני דירוג"""
        try:
            # הוספת מידע על זמן
            created_at = rating.get('created_at')
            if created_at and isinstance(created_at, datetime):
                age_hours = (datetime.now() - created_at).total_seconds() / 3600
                rating['age_hours'] = int(age_hours)
            
            # הוספת קטגורית דירוג
            rating_value = rating.get('rating', 0)
            rating['rating_category'] = self._get_rating_category(rating_value)
            
            # הוספת מחוון ביצועים
            rating['performance_indicator'] = self._get_performance_indicator(rating_value)
            
            return rating
            
        except Exception as e:
            logger.error(f"Failed to enrich rating data: {e}")
            return rating
    
    def _get_rating_category(self, rating: int) -> str:
        """קטגורית דירוג"""
        if rating >= 5:
            return 'excellent'
        elif rating >= 4:
            return 'good'
        elif rating >= 3:
            return 'average'
        elif rating >= 2:
            return 'poor'
        else:
            return 'very_poor'
    
    def _get_performance_indicator(self, rating: float) -> str:
        """מחוון ביצועים"""
        if rating >= 4.5:
            return '🟢'  # ירוק
        elif rating >= 3.5:
            return '🟡'  # צהוב
        else:
            return '🔴'  # אדום
    
    def _calculate_performance_grade(self, average_rating: float, satisfaction_rate: float) -> str:
        """חישוב ציון ביצועים"""
        score = (average_rating / 5.0) * 0.6 + satisfaction_rate * 0.4
        
        if score >= 0.9:
            return 'A+'
        elif score >= 0.85:
            return 'A'
        elif score >= 0.8:
            return 'A-'
        elif score >= 0.75:
            return 'B+'
        elif score >= 0.7:
            return 'B'
        elif score >= 0.65:
            return 'B-'
        elif score >= 0.6:
            return 'C+'
        elif score >= 0.55:
            return 'C'
        else:
            return 'D'
    
    def _generate_improvement_suggestions(self, average_rating: float, poor_rate: float) -> List[str]:
        """הצעות לשיפור"""
        suggestions = []
        
        if average_rating < 3.5:
            suggestions.append("Focus on understanding user expectations before fulfilling requests")
        
        if poor_rate > 0.2:
            suggestions.append("Review fulfillment process to reduce poor ratings")
        
        if average_rating < 4.0:
            suggestions.append("Consider following up with users after fulfillment")
            suggestions.append("Improve communication about request status and timeline")
        
        return suggestions
    
    def _clear_rating_cache(self, request_id: int):
        """ניקוי מטמון דירוגים"""
        keys_to_remove = [key for key in self._rating_cache.keys() if f"ratings_{request_id}" in key]
        for key in keys_to_remove:
            del self._rating_cache[key]
    
    def _clear_stats_cache(self):
        """ניקוי מטמון סטטיסטיקות"""
        self._stats_cache.clear()
    
    async def _log_rating_activity(self, request_id: int, user_id: int, rating: int, action: str, metadata: Dict = None):
        """לוג פעילות דירוגים"""
        try:
            # כרגע placeholder - ניתן להרחיב
            logger.info(f"Rating {action}: request {request_id}, user {user_id}, rating {rating}")
            
        except Exception as e:
            logger.error(f"Failed to log rating activity: {e}")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """סטטיסטיקות השירות"""
        return {
            'rating_cache_size': len(self._rating_cache),
            'stats_cache_size': len(self._stats_cache),
            'cache_timeout': self._cache_timeout,
            'min_rating': self.min_rating,
            'max_rating': self.max_rating,
            'satisfaction_threshold': self.satisfaction_threshold,
            'poor_rating_threshold': self.poor_rating_threshold
        }