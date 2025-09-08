#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AdminPanel - פאנל ניהול מתקדם למנהלי הבוט
ממשק מתקדם לניהול בקשות, משתמשים ומערכת
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class AdminAction:
    """פעולת מנהל"""
    action_id: str
    admin_id: int
    action_type: str
    target_id: Optional[int]
    details: Dict[str, Any]
    timestamp: datetime
    result: Optional[str] = None

class AdminPanel:
    """פאנל ניהול מתקדם"""
    
    def __init__(self, storage_manager, all_services):
        self.storage = storage_manager
        self.services = all_services
        
        # שירותים ספציפיים
        self.request_service = all_services.get('request_service')
        self.user_service = all_services.get('user_service')
        self.rating_service = all_services.get('rating_service')
        self.search_service = all_services.get('search_service')
        self.notification_service = all_services.get('notification_service')
        
        # היסטוריית פעולות
        self.admin_actions: List[AdminAction] = []
        
        logger.info("✅ AdminPanel initialized")
    
    # ========================= ממשק מנהלים =========================
    
    async def show_dashboard(self, admin_id: int) -> Dict[str, Any]:
        """הצגת דאשבורד ראשי למנהל"""
        try:
            # סטטיסטיקות כלליות
            stats = await self._get_dashboard_stats()
            
            # בקשות ממתינות
            pending_requests = await self._get_urgent_requests()
            
            # פעילות מנהלים
            admin_activity = await self._get_admin_activity_summary()
            
            # התראות מערכת
            system_alerts = await self._get_system_alerts()
            
            dashboard = {
                'admin_id': admin_id,
                'timestamp': datetime.now().isoformat(),
                'stats': stats,
                'pending_requests': pending_requests,
                'admin_activity': admin_activity,
                'system_alerts': system_alerts,
                'quick_actions': self._get_quick_actions()
            }
            
            logger.info(f"📊 Dashboard generated for admin {admin_id}")
            return dashboard
            
        except Exception as e:
            logger.error(f"❌ Error generating dashboard: {e}")
            return {}
    
    async def show_pending_requests(self, admin_id: int, filters: Dict = None) -> Dict[str, Any]:
        """הצגת בקשות ממתינות עם פילטרים"""
        try:
            filters = filters or {}
            
            # קבלת בקשות ממתינות
            pending_data = await self.request_service.get_pending_requests(
                limit=filters.get('limit', 50),
                sort_by=filters.get('sort_by', 'priority_and_age')
            )
            
            # עיבוד נתונים למנהלים
            processed_requests = []
            for request in pending_data.get('requests', []):
                processed_req = await self._process_request_for_admin(request)
                processed_requests.append(processed_req)
            
            return {
                'requests': processed_requests,
                'total_count': len(processed_requests),
                'filters_applied': filters,
                'suggested_actions': await self._get_suggested_actions(processed_requests),
                'bulk_actions_available': True
            }
            
        except Exception as e:
            logger.error(f"❌ Error showing pending requests: {e}")
            return {'requests': [], 'total_count': 0}
    
    async def show_user_management(self, admin_id: int) -> Dict[str, Any]:
        """הצגת ממשק ניהול משתמשים"""
        try:
            # משתמשים פעילים
            active_users = await self.user_service.get_active_users(days=30)
            
            # משתמשים בעייתיים
            problem_users = await self.user_service.get_problem_users()
            
            # סטטיסטיקות משתמשים
            user_stats = await self.user_service.get_user_engagement_stats()
            
            return {
                'active_users': active_users[:20],  # Top 20
                'problem_users': problem_users,
                'user_statistics': user_stats,
                'management_actions': [
                    'ban_user', 'unban_user', 'add_warning', 
                    'remove_warning', 'view_user_details'
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error in user management: {e}")
            return {}
    
    async def show_system_stats(self, admin_id: int) -> Dict[str, Any]:
        """הצגת סטטיסטיקות מערכת"""
        try:
            # סטטיסטיקות בקשות
            request_stats = await self.request_service.get_advanced_stats()
            
            # סטטיסטיקות דירוגים
            rating_stats = await self.rating_service.get_satisfaction_metrics()
            
            # ביצועי מערכת
            system_performance = await self._get_system_performance()
            
            return {
                'requests': request_stats.__dict__ if hasattr(request_stats, '__dict__') else request_stats,
                'ratings': rating_stats,
                'performance': system_performance,
                'trends': await self._calculate_trends()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting system stats: {e}")
            return {}
    
    async def show_performance_metrics(self, admin_id: int) -> Dict[str, Any]:
        """הצגת מדדי ביצועים מתקדמים"""
        try:
            # ביצועי מנהלים
            admin_performance = await self._get_all_admin_performance()
            
            # זמני תגובה
            response_times = await self._get_response_time_metrics()
            
            # שביעות רצון
            satisfaction_trends = await self.rating_service.get_trending_ratings(days=30)
            
            return {
                'admin_performance': admin_performance,
                'response_times': response_times,
                'satisfaction': satisfaction_trends,
                'efficiency_score': await self._calculate_efficiency_score()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting performance metrics: {e}")
            return {}
    
    # ========================= פעולות מנהלים =========================
    
    async def handle_admin_action(self, admin_id: int, action: str, params: Dict) -> Dict[str, Any]:
        """טיפול בפעולת מנהל"""
        try:
            action_id = f"{admin_id}_{datetime.now().timestamp()}"
            
            # רישום הפעולה
            admin_action = AdminAction(
                action_id=action_id,
                admin_id=admin_id,
                action_type=action,
                target_id=params.get('target_id'),
                details=params,
                timestamp=datetime.now()
            )
            
            self.admin_actions.append(admin_action)
            
            # ביצוע הפעולה
            result = await self._execute_admin_action(action, params)
            admin_action.result = result.get('status', 'unknown')
            
            # התראה למנהלים אחרים אם נדרש
            if action in ['ban_user', 'system_maintenance', 'bulk_reject']:
                await self._notify_other_admins(admin_id, action, params)
            
            logger.info(f"🔧 Admin {admin_id} performed action: {action}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error handling admin action: {e}")
            return {'success': False, 'error': str(e)}
    
    async def bulk_fulfill_requests(self, admin_id: int, request_ids: List[int]) -> Dict[str, Any]:
        """מילוי בקשות מרובות"""
        try:
            results = {
                'successful': [],
                'failed': [],
                'total_processed': len(request_ids)
            }
            
            for request_id in request_ids:
                try:
                    result = await self.request_service.fulfill_request(
                        request_id=request_id,
                        admin_user={'id': admin_id},  # Simplified admin user
                        notes="Bulk fulfillment"
                    )
                    
                    if result.get('success'):
                        results['successful'].append(request_id)
                    else:
                        results['failed'].append({
                            'id': request_id,
                            'error': result.get('error', 'Unknown error')
                        })
                        
                except Exception as e:
                    results['failed'].append({
                        'id': request_id,
                        'error': str(e)
                    })
            
            # התראה על התוצאות
            summary_msg = f"🔄 Bulk fulfill: {len(results['successful'])} success, {len(results['failed'])} failed"
            await self.notification_service.notify_admins(summary_msg)
            
            logger.info(f"📦 Bulk fulfill by admin {admin_id}: {len(results['successful'])}/{len(request_ids)} successful")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in bulk fulfill: {e}")
            return {'successful': [], 'failed': request_ids}
    
    async def bulk_reject_requests(self, admin_id: int, request_ids: List[int], reason: str) -> Dict[str, Any]:
        """דחיית בקשות מרובות"""
        try:
            results = {
                'successful': [],
                'failed': [],
                'total_processed': len(request_ids)
            }
            
            for request_id in request_ids:
                try:
                    result = await self.request_service.reject_request(
                        request_id=request_id,
                        admin_user={'id': admin_id},
                        reason=reason
                    )
                    
                    if result.get('success'):
                        results['successful'].append(request_id)
                    else:
                        results['failed'].append({
                            'id': request_id,
                            'error': result.get('error', 'Unknown error')
                        })
                        
                except Exception as e:
                    results['failed'].append({
                        'id': request_id,
                        'error': str(e)
                    })
            
            logger.info(f"🚫 Bulk reject by admin {admin_id}: {len(results['successful'])}/{len(request_ids)} successful")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in bulk reject: {e}")
            return {'successful': [], 'failed': request_ids}
    
    async def manage_user_permissions(self, admin_id: int, target_user_id: int, action: str) -> Dict[str, Any]:
        """ניהול הרשאות משתמש"""
        try:
            valid_actions = ['ban', 'unban', 'warn', 'unwarn', 'view_details']
            
            if action not in valid_actions:
                return {'success': False, 'error': f'Invalid action: {action}'}
            
            if action == 'ban':
                result = await self.user_service.ban_user(target_user_id, reason="Admin action")
            elif action == 'unban':
                result = await self.user_service.unban_user(target_user_id, admin_id)
            elif action == 'warn':
                result = await self.user_service.add_warning(target_user_id, "Admin warning", admin_id)
            elif action == 'view_details':
                result = await self.user_service.generate_user_report(target_user_id)
            else:
                result = {'success': False, 'error': 'Action not implemented yet'}
            
            logger.info(f"👤 Admin {admin_id} performed {action} on user {target_user_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error managing user permissions: {e}")
            return {'success': False, 'error': str(e)}
    
    # ========================= דוחות ואנליטיקס =========================
    
    async def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """יצירת דוח יומי"""
        try:
            target_date = date or datetime.now().date()
            
            # נתוני בקשות
            daily_requests = await self._get_daily_requests_data(target_date)
            
            # ביצועי מנהלים
            admin_performance = await self._get_daily_admin_performance(target_date)
            
            # דירוגים ומשוב
            ratings_data = await self._get_daily_ratings_data(target_date)
            
            report = {
                'date': target_date.isoformat(),
                'requests': daily_requests,
                'admin_performance': admin_performance,
                'ratings': ratings_data,
                'highlights': await self._generate_daily_highlights(target_date),
                'recommendations': await self._generate_recommendations(daily_requests, admin_performance)
            }
            
            logger.info(f"📋 Daily report generated for {target_date}")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error generating daily report: {e}")
            return {}
    
    async def generate_performance_report(self, admin_id: int, period: str) -> Dict[str, Any]:
        """יצירת דוח ביצועים למנהל"""
        try:
            # קביעת תקופה
            end_date = datetime.now()
            if period == 'week':
                start_date = end_date - timedelta(weeks=1)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)
            
            # ביצועי המנהל
            admin_stats = await self._get_admin_performance_detailed(admin_id, start_date, end_date)
            
            # השוואה לממוצע
            avg_performance = await self._get_average_admin_performance(start_date, end_date)
            
            # המלצות לשיפור
            recommendations = await self._generate_admin_recommendations(admin_stats, avg_performance)
            
            return {
                'admin_id': admin_id,
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'performance': admin_stats,
                'compared_to_average': avg_performance,
                'recommendations': recommendations,
                'achievements': await self._get_admin_achievements(admin_id, admin_stats)
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating performance report: {e}")
            return {}
    
    async def export_system_data(self, data_type: str, format: str = 'csv') -> Dict[str, Any]:
        """ייצוא נתוני מערכת"""
        try:
            # זה יקרא לשירות הייצוא כשיהיה זמין
            if hasattr(self, 'export_service'):
                return await self.export_service.export_data(data_type, format)
            
            # fallback פשוט
            return {
                'success': True,
                'message': f'Export of {data_type} in {format} format scheduled',
                'note': 'Advanced export functionality will be available when ExportManager is implemented'
            }
            
        except Exception as e:
            logger.error(f"❌ Error exporting system data: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_admin_activity_log(self, admin_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """קבלת לוג פעילות מנהל"""
        try:
            # פילטור פעולות של המנהל הספציפי
            admin_actions = [
                action for action in self.admin_actions
                if action.admin_id == admin_id
            ]
            
            # מיון לפי זמן (החדש ביותר ראשון)
            admin_actions.sort(key=lambda x: x.timestamp, reverse=True)
            
            # המרה לפורמט מתאים
            activity_log = []
            for action in admin_actions[:limit]:
                activity_log.append({
                    'action_id': action.action_id,
                    'action_type': action.action_type,
                    'target_id': action.target_id,
                    'timestamp': action.timestamp.isoformat(),
                    'details': action.details,
                    'result': action.result
                })
            
            return activity_log
            
        except Exception as e:
            logger.error(f"❌ Error getting admin activity log: {e}")
            return []
    
    # ========================= הגדרות מערכת =========================
    
    async def update_system_settings(self, admin_id: int, settings: Dict[str, Any]) -> Dict[str, Any]:
        """עדכון הגדרות מערכת"""
        try:
            allowed_settings = [
                'auto_response_enabled', 'duplicate_threshold', 
                'max_requests_per_day', 'notification_settings'
            ]
            
            updated_settings = {}
            for key, value in settings.items():
                if key in allowed_settings:
                    # כאן תהיה לוגיקה לעדכון ההגדרות בפועל
                    updated_settings[key] = value
                    logger.info(f"🔧 Admin {admin_id} updated setting {key} to {value}")
            
            return {
                'success': True,
                'updated_settings': updated_settings,
                'message': f'Updated {len(updated_settings)} settings'
            }
            
        except Exception as e:
            logger.error(f"❌ Error updating system settings: {e}")
            return {'success': False, 'error': str(e)}
    
    async def manage_categories(self, admin_id: int, action: str, category_data: Dict) -> Dict[str, Any]:
        """ניהול קטגוריות תוכן"""
        try:
            if action == 'add':
                # הוספת קטגוריה חדשה
                category_id = category_data.get('id')
                category_name = category_data.get('name')
                
                # כאן תהיה לוגיקה להוספת קטגוריה
                logger.info(f"➕ Admin {admin_id} added category: {category_name}")
                
            elif action == 'remove':
                category_id = category_data.get('id')
                
                # כאן תהיה לוגיקה להסרת קטגוריה
                logger.info(f"➖ Admin {admin_id} removed category: {category_id}")
                
            elif action == 'update':
                category_id = category_data.get('id')
                updates = category_data.get('updates', {})
                
                # כאן תהיה לוגיקה לעדכון קטגוריה
                logger.info(f"🔄 Admin {admin_id} updated category: {category_id}")
            
            return {'success': True, 'message': f'Category {action} completed'}
            
        except Exception as e:
            logger.error(f"❌ Error managing categories: {e}")
            return {'success': False, 'error': str(e)}
    
    async def set_auto_responses(self, admin_id: int, responses_data: Dict) -> Dict[str, Any]:
        """הגדרת תגובות אוטומטיות"""
        try:
            # כאן תהיה לוגיקה לעדכון תגובות אוטומטיות
            updated_responses = 0
            
            for response_type, response_config in responses_data.items():
                # עדכון התגובה האוטומטית
                updated_responses += 1
            
            logger.info(f"🤖 Admin {admin_id} updated {updated_responses} auto responses")
            
            return {
                'success': True,
                'updated_count': updated_responses,
                'message': 'Auto responses updated successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Error setting auto responses: {e}")
            return {'success': False, 'error': str(e)}
    
    # ========================= פונקציות עזר פרטיות =========================
    
    async def _get_dashboard_stats(self) -> Dict[str, Any]:
        """קבלת סטטיסטיקות לדאשבורד"""
        try:
            if self.request_service:
                stats = await self.request_service.get_advanced_stats()
                if hasattr(stats, '__dict__'):
                    return stats.__dict__
                return stats
            return {}
        except:
            return {}
    
    async def _get_urgent_requests(self) -> List[Dict[str, Any]]:
        """קבלת בקשות דחופות"""
        try:
            if self.request_service:
                pending = await self.request_service.get_pending_requests(limit=10, sort_by='priority')
                return pending.get('requests', [])[:5]  # Top 5 urgent
            return []
        except:
            return []
    
    async def _get_admin_activity_summary(self) -> Dict[str, Any]:
        """סיכום פעילות מנהלים"""
        today = datetime.now().date()
        
        today_actions = [
            action for action in self.admin_actions
            if action.timestamp.date() == today
        ]
        
        return {
            'today_actions': len(today_actions),
            'active_admins': len(set(action.admin_id for action in today_actions)),
            'most_common_action': self._get_most_common_action(today_actions)
        }
    
    async def _get_system_alerts(self) -> List[Dict[str, Any]]:
        """קבלת התראות מערכת"""
        alerts = []
        
        # בדיקת בקשות ישנות
        try:
            if self.request_service:
                old_requests = await self._count_old_requests()
                if old_requests > 10:
                    alerts.append({
                        'type': 'warning',
                        'message': f'{old_requests} בקשות ישנות ללא טיפול',
                        'action': 'review_old_requests'
                    })
        except:
            pass
        
        return alerts
    
    def _get_quick_actions(self) -> List[Dict[str, str]]:
        """קבלת פעולות מהירות"""
        return [
            {'name': 'pending_requests', 'label': 'בקשות ממתינות'},
            {'name': 'bulk_fulfill', 'label': 'מילוי מרובה'},
            {'name': 'user_management', 'label': 'ניהול משתמשים'},
            {'name': 'system_stats', 'label': 'סטטיסטיקות'},
            {'name': 'export_data', 'label': 'ייצוא נתונים'}
        ]
    
    async def _process_request_for_admin(self, request: Dict) -> Dict[str, Any]:
        """עיבוד בקשה להצגה למנהל"""
        processed = dict(request)
        
        # הוספת מידע נוסף למנהלים
        processed['age_hours'] = self._calculate_request_age_hours(request)
        processed['priority_score'] = self._calculate_priority_score(request)
        processed['suggested_action'] = self._suggest_action_for_request(request)
        
        return processed
    
    async def _get_suggested_actions(self, requests: List[Dict]) -> List[str]:
        """קבלת הצעות פעולה"""
        suggestions = []
        
        old_requests = [r for r in requests if self._calculate_request_age_hours(r) > 48]
        if old_requests:
            suggestions.append(f"יש {len(old_requests)} בקשות ישנות - כדאי לטפל בהן")
        
        high_priority = [r for r in requests if r.get('priority') in ['urgent', 'high']]
        if high_priority:
            suggestions.append(f"{len(high_priority)} בקשות בעדיפות גבוהה")
        
        return suggestions
    
    def _calculate_request_age_hours(self, request: Dict) -> float:
        """חישוב גיל הבקשה בשעות"""
        created_at = request.get('created_at')
        if isinstance(created_at, datetime):
            return (datetime.now() - created_at).total_seconds() / 3600
        return 0
    
    def _calculate_priority_score(self, request: Dict) -> int:
        """חישוב ציון עדיפות"""
        priority_scores = {'low': 1, 'medium': 2, 'high': 3, 'urgent': 4, 'vip': 5}
        return priority_scores.get(request.get('priority', 'medium'), 2)
    
    def _suggest_action_for_request(self, request: Dict) -> str:
        """הצעת פעולה לבקשה"""
        age_hours = self._calculate_request_age_hours(request)
        priority = request.get('priority', 'medium')
        
        if age_hours > 72:
            return "urgent_attention"
        elif priority in ['urgent', 'vip']:
            return "high_priority_review"
        else:
            return "standard_review"
    
    async def _execute_admin_action(self, action: str, params: Dict) -> Dict[str, Any]:
        """ביצוע פעולת מנהל"""
        if action == 'fulfill_request':
            return await self.request_service.fulfill_request(**params)
        elif action == 'reject_request':
            return await self.request_service.reject_request(**params)
        elif action == 'ban_user':
            return await self.user_service.ban_user(**params)
        else:
            return {'success': False, 'error': f'Unknown action: {action}'}
    
    async def _notify_other_admins(self, admin_id: int, action: str, params: Dict):
        """התראה למנהלים אחרים"""
        if self.notification_service:
            message = f"Admin {admin_id} performed {action}"
            await self.notification_service.notify_admins(message, priority='low')
    
    def _get_most_common_action(self, actions: List[AdminAction]) -> str:
        """קבלת הפעולה הנפוצה ביותר"""
        if not actions:
            return "none"
        
        action_counts = {}
        for action in actions:
            action_counts[action.action_type] = action_counts.get(action.action_type, 0) + 1
        
        return max(action_counts, key=action_counts.get)
    
    async def _count_old_requests(self) -> int:
        """ספירת בקשות ישנות"""
        try:
            if self.request_service:
                pending = await self.request_service.get_pending_requests(limit=1000)
                old_count = 0
                for req in pending.get('requests', []):
                    if self._calculate_request_age_hours(req) > 48:
                        old_count += 1
                return old_count
            return 0
        except:
            return 0
    
    # שאר הפונקציות יתמלאו בעתיד...
    async def _get_system_performance(self): return {}
    async def _calculate_trends(self): return {}
    async def _get_all_admin_performance(self): return {}
    async def _get_response_time_metrics(self): return {}
    async def _calculate_efficiency_score(self): return 0
    async def _get_daily_requests_data(self, date): return {}
    async def _get_daily_admin_performance(self, date): return {}
    async def _get_daily_ratings_data(self, date): return {}
    async def _generate_daily_highlights(self, date): return []
    async def _generate_recommendations(self, req_data, admin_data): return []
    async def _get_admin_performance_detailed(self, admin_id, start, end): return {}
    async def _get_average_admin_performance(self, start, end): return {}
    async def _generate_admin_recommendations(self, stats, avg): return []
    async def _get_admin_achievements(self, admin_id, stats): return []

# ========================= פונקציות דוחות =========================

def format_dashboard_data(stats: Dict[str, Any]) -> Dict[str, Any]:
    """פורמט נתוני דאשבורד"""
    return {
        'summary': {
            'total_requests': stats.get('total_requests', 0),
            'pending': stats.get('pending', 0),
            'fulfilled_today': stats.get('today_fulfilled', 0),
            'success_rate': f"{stats.get('success_rate', 0):.1f}%"
        },
        'trends': {
            'requests_trend': 'stable',  # יחושב בעתיד
            'response_time_trend': 'improving'
        }
    }

def calculate_admin_performance(admin_data: Dict[str, Any]) -> Dict[str, Any]:
    """חישוב ביצועי מנהל"""
    fulfilled = admin_data.get('fulfilled', 0)
    rejected = admin_data.get('rejected', 0)
    total = fulfilled + rejected
    
    return {
        'total_handled': total,
        'success_rate': (fulfilled / total * 100) if total > 0 else 0,
        'efficiency_score': min(100, (total / 10) * 100),  # 10 בקשות = 100%
        'grade': 'A' if total > 20 else 'B' if total > 10 else 'C'
    }

def generate_charts_data(stats: Dict[str, Any]) -> Dict[str, Any]:
    """יצירת נתונים לגרפים"""
    return {
        'requests_chart': {
            'labels': ['Pending', 'Fulfilled', 'Rejected'],
            'data': [
                stats.get('pending', 0),
                stats.get('fulfilled', 0),
                stats.get('rejected', 0)
            ]
        },
        'time_series': {
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'data': [10, 15, 12, 18, 22, 8, 5]  # דמי - יתמלא מנתונים אמיתיים
        }
    }