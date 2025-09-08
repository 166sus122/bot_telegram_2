#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BackgroundTaskManager - מנהל משימות רקע מתקדם
ביצוע משימות אוטומטיות ותחזוקה של המערכת
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class TaskInfo:
    """מידע על משימת רקע"""
    name: str
    func: Callable
    interval_minutes: int
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    task_handle: Optional[asyncio.Task] = None

class BackgroundTaskManager:
    """מנהל משימות רקע מתקדם"""
    
    def __init__(self, storage_manager, notification_service):
        self.storage = storage_manager
        self.notification_service = notification_service
        
        # מידע על משימות
        self.tasks: Dict[str, TaskInfo] = {}
        self.running = False
        self.health_check_interval = 300  # 5 דקות
        
        logger.info("✅ BackgroundTaskManager initialized")
    
    # ========================= ניהול משימות =========================
    
    def start_all_tasks(self):
        """הפעלת כל המשימות"""
        if self.running:
            logger.warning("⚠️ Tasks already running")
            return
        
        self.running = True
        
        # רישום משימות ברירת מחדל
        self._register_default_tasks()
        
        # הפעלת כל המשימות הפעילות
        for task_name, task_info in self.tasks.items():
            if task_info.enabled:
                self._start_single_task(task_info)
        
        # הפעלת משימת בדיקת תקינות
        self._start_health_monitor()
        
        logger.info(f"🚀 Started {len(self.tasks)} background tasks")
    
    def stop_all_tasks(self):
        """עצירת כל המשימות"""
        if not self.running:
            return
        
        self.running = False
        
        # ביטול כל המשימות
        for task_info in self.tasks.values():
            if task_info.task_handle and not task_info.task_handle.done():
                task_info.task_handle.cancel()
        
        logger.info("🛑 All background tasks stopped")
    
    def add_task(self, task_func: Callable, interval_minutes: int, name: str):
        """הוספת משימת רקע חדשה"""
        if name in self.tasks:
            logger.warning(f"⚠️ Task {name} already exists")
            return False
        
        task_info = TaskInfo(
            name=name,
            func=task_func,
            interval_minutes=interval_minutes
        )
        
        self.tasks[name] = task_info
        
        # הפעלה אם המנהל כבר פועל
        if self.running:
            self._start_single_task(task_info)
        
        logger.info(f"➕ Added task: {name} (every {interval_minutes}m)")
        return True
    
    def remove_task(self, task_name: str):
        """הסרת משימת רקע"""
        if task_name not in self.tasks:
            return False
        
        task_info = self.tasks[task_name]
        
        # ביטול המשימה אם פועלת
        if task_info.task_handle and not task_info.task_handle.done():
            task_info.task_handle.cancel()
        
        del self.tasks[task_name]
        logger.info(f"➖ Removed task: {task_name}")
        return True
    
    def get_task_status(self, task_name: Optional[str] = None) -> Dict[str, Any]:
        """קבלת סטטוס משימות"""
        if task_name:
            if task_name not in self.tasks:
                return {}
            
            task_info = self.tasks[task_name]
            return self._format_task_status(task_info)
        
        # כל המשימות
        status = {
            'running': self.running,
            'total_tasks': len(self.tasks),
            'active_tasks': sum(1 for t in self.tasks.values() if t.enabled),
            'tasks': {}
        }
        
        for name, task_info in self.tasks.items():
            status['tasks'][name] = self._format_task_status(task_info)
        
        return status
    
    # ========================= משימות ספציפיות =========================
    
    async def check_old_requests(self):
        """בדיקת בקשות ישנות"""
        try:
            logger.debug("🕒 Checking old requests")
            
            # בקשות שעברו 48 שעות ללא טיפול
            cutoff_time = datetime.now() - timedelta(hours=48)
            
            old_requests = []
            if hasattr(self.storage, 'get_requests_older_than'):
                old_requests = await self.storage.get_requests_older_than(cutoff_time)
            
            if old_requests:
                # התראה למנהלים
                message = f"⚠️ יש {len(old_requests)} בקשות ישנות שדורשות תשומת לב"
                await self.notification_service.notify_admins(message, priority='high')
                
                logger.info(f"⏰ Found {len(old_requests)} old requests")
            
        except Exception as e:
            logger.error(f"❌ Error checking old requests: {e}")
    
    async def update_statistics(self):
        """עדכון סטטיסטיקות מערכת"""
        try:
            logger.debug("📊 Updating system statistics")
            
            # עדכון מטמון סטטיסטיקות
            if hasattr(self.storage, 'update_cached_stats'):
                await self.storage.update_cached_stats()
            
            # חישוב מדדי ביצועים
            stats = await self._calculate_performance_metrics()
            
            # שמירה למעקב היסטורי
            if hasattr(self.storage, 'save_daily_stats'):
                await self.storage.save_daily_stats(stats)
            
            logger.debug("📈 Statistics updated successfully")
            
        except Exception as e:
            logger.error(f"❌ Error updating statistics: {e}")
    
    async def cleanup_cache(self):
        """ניקוי מטמון"""
        try:
            logger.debug("🧹 Cleaning up cache")
            
            cleaned_items = 0
            
            # ניקוי מטמון אם זמין
            if hasattr(self.storage, 'cleanup_expired_cache'):
                cleaned_items = await self.storage.cleanup_expired_cache()
            
            # ניקוי קבצי זמניים
            temp_files_cleaned = await self._cleanup_temp_files()
            
            logger.info(f"🗑️ Cleaned {cleaned_items} cache items, {temp_files_cleaned} temp files")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning cache: {e}")
    
    async def send_pending_notifications(self):
        """שליחת התראות ממתינות"""
        try:
            logger.debug("📬 Processing pending notifications")
            
            if hasattr(self.notification_service, 'process_pending_notifications'):
                sent_count = await self.notification_service.process_pending_notifications()
                
                if sent_count > 0:
                    logger.info(f"📨 Sent {sent_count} pending notifications")
            
        except Exception as e:
            logger.error(f"❌ Error sending notifications: {e}")
    
    async def archive_completed_requests(self):
        """ארכוב בקשות שהושלמו"""
        try:
            logger.debug("📦 Archiving completed requests")
            
            # בקשות שהושלמו לפני 30 יום
            cutoff_date = datetime.now() - timedelta(days=30)
            
            archived_count = 0
            if hasattr(self.storage, 'archive_old_completed_requests'):
                archived_count = await self.storage.archive_old_completed_requests(cutoff_date)
            
            if archived_count > 0:
                logger.info(f"📁 Archived {archived_count} completed requests")
            
        except Exception as e:
            logger.error(f"❌ Error archiving requests: {e}")
    
    # ========================= ניטור ובקרה =========================
    
    def get_task_history(self, task_name: str) -> Dict[str, Any]:
        """קבלת היסטוריית משימה"""
        if task_name not in self.tasks:
            return {}
        
        task_info = self.tasks[task_name]
        
        return {
            'name': task_info.name,
            'total_runs': task_info.run_count,
            'errors': task_info.error_count,
            'last_run': task_info.last_run.isoformat() if task_info.last_run else None,
            'next_run': task_info.next_run.isoformat() if task_info.next_run else None,
            'last_error': task_info.last_error,
            'success_rate': (task_info.run_count - task_info.error_count) / max(task_info.run_count, 1) * 100
        }
    
    def set_task_enabled(self, task_name: str, enabled: bool):
        """הפעלה/השבתה של משימה"""
        if task_name not in self.tasks:
            return False
        
        task_info = self.tasks[task_name]
        
        if task_info.enabled == enabled:
            return True
        
        task_info.enabled = enabled
        
        if self.running:
            if enabled:
                self._start_single_task(task_info)
            else:
                if task_info.task_handle and not task_info.task_handle.done():
                    task_info.task_handle.cancel()
        
        action = "enabled" if enabled else "disabled"
        logger.info(f"🔄 Task {task_name} {action}")
        return True
    
    def reschedule_task(self, task_name: str, new_interval: int):
        """שינוי מרווח זמן של משימה"""
        if task_name not in self.tasks:
            return False
        
        task_info = self.tasks[task_name]
        old_interval = task_info.interval_minutes
        
        task_info.interval_minutes = new_interval
        
        # אתחול מחדש אם המשימה פועלת
        if self.running and task_info.enabled:
            if task_info.task_handle and not task_info.task_handle.done():
                task_info.task_handle.cancel()
            self._start_single_task(task_info)
        
        logger.info(f"⏰ Task {task_name} rescheduled: {old_interval}m → {new_interval}m")
        return True
    
    def get_system_health(self) -> Dict[str, Any]:
        """בדיקת תקינות מערכת"""
        health_status = {
            'overall': 'healthy',
            'tasks_running': self.running,
            'total_tasks': len(self.tasks),
            'healthy_tasks': 0,
            'problematic_tasks': [],
            'system_load': 'normal',
            'memory_usage': 'normal'
        }
        
        # בדיקת משימות
        for name, task_info in self.tasks.items():
            if task_info.enabled:
                error_rate = task_info.error_count / max(task_info.run_count, 1)
                
                if error_rate < 0.1:  # פחות מ-10% שגיאות
                    health_status['healthy_tasks'] += 1
                else:
                    health_status['problematic_tasks'].append({
                        'name': name,
                        'error_rate': error_rate * 100,
                        'last_error': task_info.last_error
                    })
        
        # קביעת סטטוס כללי
        if health_status['problematic_tasks']:
            health_status['overall'] = 'warning' if len(health_status['problematic_tasks']) < len(self.tasks) / 2 else 'critical'
        
        return health_status
    
    # ========================= פונקציות פרטיות =========================
    
    def _register_default_tasks(self):
        """רישום משימות ברירת מחדל"""
        default_tasks = [
            ('check_old_requests', self.check_old_requests, 60),  # כל שעה
            ('update_statistics', self.update_statistics, 15),   # כל 15 דקות
            ('cleanup_cache', self.cleanup_cache, 120),          # כל שעתיים
            ('send_notifications', self.send_pending_notifications, 5),  # כל 5 דקות
            ('archive_requests', self.archive_completed_requests, 1440)  # פעם ביום
        ]
        
        for name, func, interval in default_tasks:
            if name not in self.tasks:
                self.add_task(func, interval, name)
    
    def _start_single_task(self, task_info: TaskInfo):
        """הפעלת משימה יחידה"""
        async def task_runner():
            while self.running and task_info.enabled:
                try:
                    start_time = datetime.now()
                    task_info.next_run = start_time + timedelta(minutes=task_info.interval_minutes)
                    
                    # הפעלת המשימה
                    if asyncio.iscoroutinefunction(task_info.func):
                        await task_info.func()
                    else:
                        task_info.func()
                    
                    # עדכון נתונים
                    task_info.last_run = start_time
                    task_info.run_count += 1
                    
                    logger.debug(f"✅ Task {task_info.name} completed successfully")
                    
                except Exception as e:
                    task_info.error_count += 1
                    task_info.last_error = str(e)
                    logger.error(f"❌ Task {task_info.name} failed: {e}")
                
                # המתנה לריצה הבאה
                await asyncio.sleep(task_info.interval_minutes * 60)
        
        task_info.task_handle = asyncio.create_task(task_runner())
        logger.debug(f"🚀 Started task: {task_info.name}")
    
    def _start_health_monitor(self):
        """הפעלת מוניטור תקינות"""
        async def health_monitor():
            while self.running:
                try:
                    health = self.get_system_health()
                    
                    if health['overall'] == 'critical':
                        message = f"🚨 CRITICAL: System health is critical. {len(health['problematic_tasks'])} tasks failing."
                        await self.notification_service.notify_admins(message, priority='urgent')
                    
                    elif health['overall'] == 'warning':
                        logger.warning(f"⚠️ System health warning: {len(health['problematic_tasks'])} problematic tasks")
                
                except Exception as e:
                    logger.error(f"❌ Health monitor error: {e}")
                
                await asyncio.sleep(self.health_check_interval)
        
        asyncio.create_task(health_monitor())
        logger.info("💊 Health monitor started")
    
    def _format_task_status(self, task_info: TaskInfo) -> Dict[str, Any]:
        """פורמט סטטוס משימה"""
        return {
            'enabled': task_info.enabled,
            'interval_minutes': task_info.interval_minutes,
            'last_run': task_info.last_run.isoformat() if task_info.last_run else None,
            'next_run': task_info.next_run.isoformat() if task_info.next_run else None,
            'run_count': task_info.run_count,
            'error_count': task_info.error_count,
            'last_error': task_info.last_error,
            'running': task_info.task_handle is not None and not task_info.task_handle.done()
        }
    
    async def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """חישוב מדדי ביצועים"""
        return {
            'timestamp': datetime.now().isoformat(),
            'tasks_count': len(self.tasks),
            'active_tasks': sum(1 for t in self.tasks.values() if t.enabled),
            'total_runs': sum(t.run_count for t in self.tasks.values()),
            'total_errors': sum(t.error_count for t in self.tasks.values()),
        }
    
    async def _cleanup_temp_files(self) -> int:
        """ניקוי קבצי זמניים"""
        # כאן תהיה לוגיקה לניקוי קבצי זמניים
        return 0

# ========================= פונקציות משימות רקע =========================

async def maintenance_task():
    """משימת תחזוקה כללית"""
    logger.info("🔧 Running maintenance task")
    # כאן תהיה לוגיקת תחזוקה כללית

async def stats_update_task():
    """משימת עדכון סטטיסטיקות"""
    logger.info("📊 Running stats update task")
    # כאן תהיה לוגיקת עדכון סטטיסטיקות

async def notification_sender_task():
    """משימת שליחת התראות"""
    logger.info("📬 Running notification sender task")
    # כאן תהיה לוגיקת שליחת התראות

async def cache_cleanup_task():
    """משימת ניקוי מטמון"""
    logger.info("🗑️ Running cache cleanup task")
    # כאן תהיה לוגיקת ניקוי מטמון