#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notification Service לבוט התמימים הפיראטים
מערכת התראות חכמה למנהלים ומשתמשים
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import asyncio
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class NotificationPriority(Enum):
    """רמות עדיפות התראות"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class NotificationType(Enum):
    """סוגי התראות"""
    NEW_REQUEST = "new_request"
    REQUEST_FULFILLED = "request_fulfilled"
    REQUEST_REJECTED = "request_rejected"
    REQUEST_EXPIRED = "request_expired"
    LOW_RATING = "low_rating"
    SYSTEM_ALERT = "system_alert"
    ADMIN_REMINDER = "admin_reminder"
    USER_WARNING = "user_warning"
    BULK_ACTION = "bulk_action"

@dataclass
class NotificationData:
    """מבנה נתוני התראה"""
    recipient_id: int
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    data: Optional[Dict] = None
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class NotificationService:
    """שירות התראות מתקדם"""
    
    def __init__(self, bot_instance, admin_ids: List[int]):
        self.bot = bot_instance
        self.admin_ids = set(admin_ids)
        
        # מעקב throttling
        self._user_throttling = {}  # user_id -> last_notification_time
        self._notification_counts = {}  # user_id -> count_in_hour
        self._failed_attempts = {}  # user_id -> count
        
        # התראות ממתינות
        self._pending_notifications = []
        self._notification_queue = asyncio.Queue()
        
        # הגדרות התרעה
        self.throttle_minutes = 5  # זמן מינימום בין התראות לאותו משתמש
        self.max_notifications_per_hour = 10
        self.max_retry_attempts = 3
        self.notification_expiry_hours = 24
        
        # מטמון לביצועים
        self._admin_preferences = {}
        self._notification_stats = {
            'total_sent': 0,
            'total_failed': 0,
            'by_type': {},
            'by_priority': {}
        }
        
        logger.info(f"Notification Service initialized with {len(admin_ids)} admins")
    
    # ========================= התראות בסיסיות =========================
    
    async def notify_admins(self, title: str, message: str, 
                           notification_type: NotificationType = NotificationType.SYSTEM_ALERT,
                           priority: NotificationPriority = NotificationPriority.NORMAL,
                           data: Optional[Dict] = None, 
                           exclude_admin_ids: Optional[Set[int]] = None) -> Dict[int, bool]:
        """
        שליחת התראה לכל המנהלים
        
        Returns:
            Dict של admin_id -> success/failure
        """
        try:
            exclude_admin_ids = exclude_admin_ids or set()
            target_admins = self.admin_ids - exclude_admin_ids
            
            results = {}
            
            # יצירת התראות לכל מנהל
            notifications = []
            for admin_id in target_admins:
                notification = NotificationData(
                    recipient_id=admin_id,
                    notification_type=notification_type,
                    priority=priority,
                    title=title,
                    message=message,
                    data=data
                )
                notifications.append(notification)
            
            # שליחת התראות במקביל
            tasks = [self._send_single_notification(notif) for notif in notifications]
            send_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # עיבוד תוצאות
            for admin_id, result in zip(target_admins, send_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to notify admin {admin_id}: {result}")
                    results[admin_id] = False
                else:
                    results[admin_id] = result
            
            # עדכון סטטיסטיקות
            successful = sum(1 for success in results.values() if success)
            logger.info(f"Notified {successful}/{len(target_admins)} admins: {title}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to notify admins: {e}")
            return {}
    
    async def notify_user(self, user_id: int, title: str, message: str,
                         notification_type: NotificationType = NotificationType.SYSTEM_ALERT,
                         priority: NotificationPriority = NotificationPriority.NORMAL,
                         data: Optional[Dict] = None,
                         keyboard = None) -> bool:
        """שליחת התראה למשתמש יחיד"""
        try:
            # בדיקת throttling
            if not self._check_user_throttling(user_id, priority):
                logger.warning(f"User {user_id} is throttled for notifications")
                return False
            
            notification = NotificationData(
                recipient_id=user_id,
                notification_type=notification_type,
                priority=priority,
                title=title,
                message=message,
                data=data
            )
            
            success = await self._send_single_notification(notification, keyboard)
            
            if success:
                self._update_throttling(user_id)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
            return False
    
    async def notify_admin_specific(self, admin_id: int, title: str, message: str,
                                  notification_type: NotificationType = NotificationType.SYSTEM_ALERT,
                                  priority: NotificationPriority = NotificationPriority.NORMAL,
                                  data: Optional[Dict] = None) -> bool:
        """התראה למנהל ספציפי"""
        if admin_id not in self.admin_ids:
            logger.warning(f"User {admin_id} is not an admin")
            return False
        
        return await self.notify_user(admin_id, title, message, notification_type, priority, data)
    
    # ========================= התראות חכמות =========================
    
    async def smart_admin_notification(self, request_data: Dict, action_type: str, 
                                     additional_context: Optional[Dict] = None) -> bool:
        """התראה חכמה למנהלים עם קונטקסט"""
        try:
            # בניית הודעה דינמית לפי סוג הפעולה
            title, message, priority = self._build_smart_message(request_data, action_type, additional_context)
            
            # בחירת מנהל המתאים ביותר (אם רלוונטי)
            target_admin = self._select_best_admin(request_data, action_type)
            
            if target_admin:
                # התראה למנהל ספציפי
                return await self.notify_admin_specific(
                    target_admin, title, message,
                    NotificationType.NEW_REQUEST if action_type == 'new_request' else NotificationType.SYSTEM_ALERT,
                    priority,
                    data={'request_id': request_data.get('id'), 'action_type': action_type}
                )
            else:
                # התראה לכל המנהלים
                results = await self.notify_admins(
                    title, message,
                    NotificationType.NEW_REQUEST if action_type == 'new_request' else NotificationType.SYSTEM_ALERT,
                    priority,
                    data={'request_id': request_data.get('id'), 'action_type': action_type}
                )
                return any(results.values())
                
        except Exception as e:
            logger.error(f"Smart admin notification failed: {e}")
            return False
    
    def _build_smart_message(self, request_data: Dict, action_type: str, 
                           additional_context: Optional[Dict]) -> tuple[str, str, NotificationPriority]:
        """בניית הודעה חכמה"""
        title = ""
        message = ""
        priority = NotificationPriority.NORMAL
        
        request_id = request_data.get('id')
        user_name = request_data.get('first_name', 'משתמש')
        title_text = request_data.get('title', 'ללא כותרת')
        category = request_data.get('category', 'general')
        
        if action_type == 'new_request':
            priority_level = request_data.get('priority', 'medium')
            confidence = request_data.get('confidence', 50)
            
            # קביעת עדיפות התראה
            if priority_level in ['urgent', 'vip']:
                priority = NotificationPriority.HIGH
            elif priority_level == 'high':
                priority = NotificationPriority.NORMAL
            else:
                priority = NotificationPriority.LOW
            
            title = f"בקשה חדשה #{request_id}"
            message = f"""
📝 {title_text}
👤 מאת: {user_name}
📂 {self._get_category_emoji(category)} {category}
🎯 ביטחון: {confidence}%
⭐ עדיפות: {priority_level}

🔧 פעולות:
/fulfill {request_id} - מילוי בקשה
/reject {request_id} - דחיית בקשה
            """.strip()
            
        elif action_type == 'request_expired':
            age_hours = additional_context.get('age_hours', 0) if additional_context else 0
            priority = NotificationPriority.HIGH if age_hours > 48 else NotificationPriority.NORMAL
            
            title = f"בקשה מתיישנת #{request_id}"
            message = f"""
⏰ בקשה ישנה זקוקה לטיפול!

📝 {title_text}
👤 מאת: {user_name}
🕐 גיל: {age_hours} שעות
📂 {category}

💡 מומלץ לטפל בהקדם!
            """.strip()
            
        elif action_type == 'low_rating':
            rating = additional_context.get('rating', 0) if additional_context else 0
            priority = NotificationPriority.HIGH
            
            title = f"דירוג נמוך לבקשה #{request_id}"
            message = f"""
⚠️ בקשה קיבלה דירוג נמוך!

📝 {title_text}
⭐ דירוג: {rating}/5
👤 מאת: {user_name}

💡 מומלץ לבדוק מה השתבש
            """.strip()
            
        elif action_type == 'bulk_reminder':
            pending_count = additional_context.get('pending_count', 0) if additional_context else 0
            priority = NotificationPriority.NORMAL
            
            title = f"תזכורת: {pending_count} בקשות ממתינות"
            message = f"""
📋 יש {pending_count} בקשות ממתינות לטיפול

/pending - צפייה בבקשות
/admin_stats - סטטיסטיקות מנהלים
            """.strip()
        
        return title, message, priority
    
    def _select_best_admin(self, request_data: Dict, action_type: str) -> Optional[int]:
        """בחירת המנהל המתאים ביותר"""
        # כרגע מחזיר None - כל המנהלים מקבלים
        # ניתן להרחיב עם לוגיקה של התמחויות מנהלים
        return None
    
    def _get_category_emoji(self, category: str) -> str:
        """קבלת אמוג'י לקטגוריה"""
        category_emojis = {
            'series': '📺',
            'movies': '🎬', 
            'books': '📚',
            'games': '🎮',
            'spotify': '🎵',
            'apps': '📱',
            'software': '💻',
            'anime': '🍙',
            'documentaries': '🎥'
        }
        return category_emojis.get(category, '📋')
    
    # ========================= התראות מתוזמנות =========================
    
    async def schedule_notification(self, notification_data: NotificationData, 
                                  delay_minutes: int) -> bool:
        """תזמון התראה לעתיד"""
        try:
            notification_data.scheduled_for = datetime.now() + timedelta(minutes=delay_minutes)
            notification_data.expires_at = notification_data.scheduled_for + timedelta(hours=self.notification_expiry_hours)
            
            self._pending_notifications.append(notification_data)
            logger.info(f"Scheduled notification for {notification_data.recipient_id} in {delay_minutes} minutes")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule notification: {e}")
            return False
    
    async def schedule_reminder(self, admin_id: int, request_id: int, 
                              reminder_text: str, hours_delay: int = 4) -> bool:
        """תזמון תזכורת למנהל"""
        title = f"תזכורת: בקשה #{request_id}"
        message = f"🔔 {reminder_text}\n\n/fulfill {request_id} | /reject {request_id}"
        
        notification = NotificationData(
            recipient_id=admin_id,
            notification_type=NotificationType.ADMIN_REMINDER,
            priority=NotificationPriority.NORMAL,
            title=title,
            message=message,
            data={'request_id': request_id}
        )
        
        return await self.schedule_notification(notification, hours_delay * 60)
    
    async def escalate_to_main_admin(self, request_id: int, reason: str, 
                                   original_admin_id: Optional[int] = None) -> bool:
        """escalation למנהל ראשי"""
        try:
            # המנהל הראשי הוא הראשון ברשימה
            main_admin_id = next(iter(self.admin_ids)) if self.admin_ids else None
            
            if not main_admin_id or main_admin_id == original_admin_id:
                # אם אין מנהל ראשי או שזה אותו מנהל, שלח לכולם
                return await self.notify_admins(
                    f"🚨 Escalation: בקשה #{request_id}",
                    f"⬆️ **דורש טיפול דחוף**\n\n📋 סיבה: {reason}\n\n/fulfill {request_id} | /reject {request_id}",
                    NotificationType.SYSTEM_ALERT,
                    NotificationPriority.URGENT,
                    data={'request_id': request_id, 'escalation_reason': reason}
                )
            else:
                return await self.notify_admin_specific(
                    main_admin_id,
                    f"🚨 Escalation: בקשה #{request_id}",
                    f"⬆️ **דורש טיפול דחוף**\n\n📋 סיבה: {reason}\n\n/fulfill {request_id} | /reject {request_id}",
                    NotificationType.SYSTEM_ALERT,
                    NotificationPriority.URGENT,
                    data={'request_id': request_id, 'escalation_reason': reason}
                )
                
        except Exception as e:
            logger.error(f"Failed to escalate to main admin: {e}")
            return False
    
    # ========================= עיבוד התראות ממתינות =========================
    
    async def process_pending_notifications(self) -> int:
        """עיבוד התראות ממתינות"""
        try:
            now = datetime.now()
            processed_count = 0
            
            # סינון התראות שצריך לשלוח
            to_send = []
            still_pending = []
            
            for notification in self._pending_notifications:
                if notification.expires_at and now > notification.expires_at:
                    # פג תוקף - דלג
                    logger.warning(f"Notification expired for user {notification.recipient_id}")
                    continue
                elif notification.scheduled_for and now >= notification.scheduled_for:
                    # זמן לשלוח
                    to_send.append(notification)
                else:
                    # עדיין ממתין
                    still_pending.append(notification)
            
            # עדכון רשימת הממתינים
            self._pending_notifications = still_pending
            
            # שליחת התראות
            for notification in to_send:
                try:
                    success = await self._send_single_notification(notification)
                    if success:
                        processed_count += 1
                    else:
                        # נסיון נוסף מאוחר יותר
                        notification.scheduled_for = now + timedelta(minutes=5)
                        self._pending_notifications.append(notification)
                        
                except Exception as e:
                    logger.error(f"Failed to send pending notification: {e}")
            
            if processed_count > 0:
                logger.info(f"Processed {processed_count} pending notifications")
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Failed to process pending notifications: {e}")
            return 0
    
    # ========================= ניהול Throttling =========================
    
    def _check_user_throttling(self, user_id: int, priority: NotificationPriority) -> bool:
        """בדיקת throttling למשתמש"""
        now = datetime.now()
        
        # בדיקת throttling זמני
        if user_id in self._user_throttling:
            last_notification = self._user_throttling[user_id]
            time_since_last = (now - last_notification).total_seconds() / 60
            
            # התראות דחופות עוקפות throttling
            if priority.value >= NotificationPriority.HIGH.value:
                return True
            
            if time_since_last < self.throttle_minutes:
                return False
        
        # בדיקת מגבלה שעתית
        hour_key = now.replace(minute=0, second=0, microsecond=0)
        count_key = (user_id, hour_key)
        
        if count_key in self._notification_counts:
            if self._notification_counts[count_key] >= self.max_notifications_per_hour:
                # התראות קריטיות עוקפות מגבלה שעתית
                return priority == NotificationPriority.CRITICAL
        
        return True
    
    def _update_throttling(self, user_id: int):
        """עדכון נתוני throttling"""
        now = datetime.now()
        
        # עדכון זמן אחרון
        self._user_throttling[user_id] = now
        
        # עדכון מונה שעתי
        hour_key = now.replace(minute=0, second=0, microsecond=0)
        count_key = (user_id, hour_key)
        
        if count_key in self._notification_counts:
            self._notification_counts[count_key] += 1
        else:
            self._notification_counts[count_key] = 1
        
        # ניקוי נתונים ישנים
        self._cleanup_old_throttling_data()
    
    def _cleanup_old_throttling_data(self):
        """ניקוי נתוני throttling ישנים"""
        now = datetime.now()
        cutoff_time = now - timedelta(hours=2)
        
        # ניקוי מונים שעתיים
        keys_to_remove = []
        for (user_id, hour_key) in self._notification_counts.keys():
            if hour_key < cutoff_time:
                keys_to_remove.append((user_id, hour_key))
        
        for key in keys_to_remove:
            del self._notification_counts[key]
    
    # ========================= שליחת התראות =========================
    
    async def _send_single_notification(self, notification: NotificationData, 
                                      keyboard = None) -> bool:
        """שליחת התראה יחידה"""
        try:
            recipient_id = notification.recipient_id
            
            # בניית הודעה מלאה
            full_message = self._format_notification_message(notification)
            
            # שליחת ההודעה
            await self.bot.send_message(
                chat_id=recipient_id,
                text=full_message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            # עדכון סטטיסטיקות
            self._update_notification_stats(notification, success=True)
            
            logger.debug(f"Notification sent successfully to {recipient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification to {notification.recipient_id}: {e}")
            
            # עדכון כשלונות
            self._update_notification_stats(notification, success=False)
            self._track_failed_attempt(notification.recipient_id)
            
            return False
    
    def _format_notification_message(self, notification: NotificationData) -> str:
        """עיצוב הודעת התראה"""
        priority_emoji = {
            NotificationPriority.LOW: '',
            NotificationPriority.NORMAL: '',
            NotificationPriority.HIGH: '❗',
            NotificationPriority.URGENT: '🚨',
            NotificationPriority.CRITICAL: '🔴'
        }
        
        emoji = priority_emoji.get(notification.priority, '')
        title_with_emoji = f"{emoji} {notification.title}".strip()
        
        return f"**{title_with_emoji}**\n\n{notification.message}"
    
    def _update_notification_stats(self, notification: NotificationData, success: bool):
        """עדכון סטטיסטיקות התראות"""
        if success:
            self._notification_stats['total_sent'] += 1
        else:
            self._notification_stats['total_failed'] += 1
        
        # סטטיסטיקות לפי סוג
        type_key = notification.notification_type.value
        if type_key not in self._notification_stats['by_type']:
            self._notification_stats['by_type'][type_key] = {'sent': 0, 'failed': 0}
        
        if success:
            self._notification_stats['by_type'][type_key]['sent'] += 1
        else:
            self._notification_stats['by_type'][type_key]['failed'] += 1
        
        # סטטיסטיקות לפי עדיפות
        priority_key = notification.priority.name.lower()
        if priority_key not in self._notification_stats['by_priority']:
            self._notification_stats['by_priority'][priority_key] = {'sent': 0, 'failed': 0}
        
        if success:
            self._notification_stats['by_priority'][priority_key]['sent'] += 1
        else:
            self._notification_stats['by_priority'][priority_key]['failed'] += 1
    
    def _track_failed_attempt(self, user_id: int):
        """מעקב אחר כשלונות שליחה"""
        if user_id not in self._failed_attempts:
            self._failed_attempts[user_id] = 0
        
        self._failed_attempts[user_id] += 1
        
        # אם יש יותר מדי כשלונות, הוסף לרשימה שחורה זמנית
        if self._failed_attempts[user_id] >= self.max_retry_attempts:
            logger.warning(f"User {user_id} marked as temporarily unreachable")
    
    # ========================= סטטיסטיקות וניטור =========================
    
    async def notify_admins_new_request(self, request_id: int, user, analysis: Dict):
        """שליחת התראה למנהלים על בקשה חדשה"""
        try:
            title = analysis.get('title', 'בקשה חדשה')
            category = analysis.get('category', 'כללי')
            category_emoji = self._get_category_emoji(category)
            
            message = f"""
{category_emoji} **בקשה חדשה #{request_id}**

📋 **תוכן:** {title}
👤 **מבקש:** {user.first_name} (@{user.username or 'ללא'})
🆔 **ID:** {user.id}
📂 **קטגוריה:** {category}

⏰ הבקשה ממתינה לטיפול
            """
            
            await self.notify_admins(
                title=f"בקשה חדשה #{request_id}",
                message=message,
                priority=NotificationPriority.HIGH
            )
            
            logger.info(f"✅ Admin notification sent for request {request_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to notify admins about request {request_id}: {e}")

    async def notify_new_user(self, user):
        """שליחת התראה למנהלים על משתמש חדש"""
        try:
            message = f"""
👋 **משתמש חדש נרשם!**

👤 **שם:** {user.first_name} {user.last_name or ''}
🆔 **ID:** {user.id}
📧 **Username:** @{user.username or 'ללא'}
🕐 **הצטרפות:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

🎉 ברוכים הבאים למשפחת התמימים הפיראטים!
            """
            
            await self.notify_admins(
                title="משתמש חדש נרשם",
                message=message,
                priority=NotificationPriority.NORMAL
            )
            
            logger.info(f"✅ New user notification sent for {user.id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to notify admins about new user {user.id}: {e}")

    def get_notification_stats(self) -> Dict[str, Any]:
        """קבלת סטטיסטיקות התראות"""
        total_attempts = self._notification_stats['total_sent'] + self._notification_stats['total_failed']
        success_rate = (self._notification_stats['total_sent'] / max(total_attempts, 1)) * 100
        
        return {
            **self._notification_stats,
            'success_rate': round(success_rate, 1),
            'pending_notifications': len(self._pending_notifications),
            'throttled_users': len(self._user_throttling),
            'failed_users': len(self._failed_attempts),
            'admin_count': len(self.admin_ids)
        }
    
    def get_throttling_status(self, user_id: int) -> Dict[str, Any]:
        """בדיקת סטטוס throttling למשתמש"""
        now = datetime.now()
        
        # זמן התראה אחרונה
        last_notification = self._user_throttling.get(user_id)
        time_since_last = None
        if last_notification:
            time_since_last = (now - last_notification).total_seconds() / 60
        
        # מונה שעתי
        hour_key = now.replace(minute=0, second=0, microsecond=0)
        count_key = (user_id, hour_key)
        hourly_count = self._notification_counts.get(count_key, 0)
        
        # כשלונות
        failed_count = self._failed_attempts.get(user_id, 0)
        
        return {
            'user_id': user_id,
            'last_notification_minutes_ago': round(time_since_last, 1) if time_since_last else None,
            'notifications_this_hour': hourly_count,
            'failed_attempts': failed_count,
            'is_throttled': not self._check_user_throttling(user_id, NotificationPriority.NORMAL),
            'can_receive_urgent': self._check_user_throttling(user_id, NotificationPriority.HIGH)
        }
    
    async def test_notification(self, recipient_id: int, test_type: str = 'basic') -> bool:
        """בדיקת התראה לצורכי debug"""
        try:
            test_messages = {
                'basic': ('🧪 בדיקת התראות', 'זוהי הודעת בדיקה להתראות המערכת'),
                'priority': ('🚨 בדיקת עדיפות גבוהה', 'בדיקת התראה עם עדיפות גבוהה'),
                'admin': ('👑 בדיקת מנהלים', 'בדיקת התראות למנהלים')
            }
            
            title, message = test_messages.get(test_type, test_messages['basic'])
            priority = NotificationPriority.HIGH if test_type == 'priority' else NotificationPriority.LOW
            
            return await self.notify_user(recipient_id, title, message, 
                                        NotificationType.SYSTEM_ALERT, priority)
            
        except Exception as e:
            logger.error(f"Test notification failed: {e}")
            return False
    
    def reset_user_throttling(self, user_id: int):
        """איפוס throttling למשתמש"""
        self._user_throttling.pop(user_id, None)
        
        # איפוס מונים שעתיים
        keys_to_remove = [key for key in self._notification_counts.keys() if key[0] == user_id]
        for key in keys_to_remove:
            del self._notification_counts[key]
        
        # איפוס כשלונות
        self._failed_attempts.pop(user_id, None)
        
        logger.info(f"Reset throttling for user {user_id}")
    
    def set_throttle_settings(self, throttle_minutes: int = None, 
                            max_per_hour: int = None, max_retries: int = None):
        """עדכון הגדרות throttling"""
        if throttle_minutes is not None:
            self.throttle_minutes = throttle_minutes
        
        if max_per_hour is not None:
            self.max_notifications_per_hour = max_per_hour
            
        if max_retries is not None:
            self.max_retry_attempts = max_retries
        
        logger.info(f"Updated throttle settings: {self.throttle_minutes}min, {self.max_notifications_per_hour}/hour, {self.max_retry_attempts} retries")