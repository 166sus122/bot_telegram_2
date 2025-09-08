#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TaskScheduler - מתזמן משימות מתקדם
תזמון גמיש למשימות חד פעמיות וחוזרות עם תמיכה ב-CRON
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import re

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """סטטוס משימה"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ScheduledTask:
    """משימה מתוזמנת"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    
    # תזמון
    scheduled_time: Optional[datetime] = None
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    
    # מצב
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    # תוצאות
    run_count: int = 0
    error_count: int = 0
    last_result: Any = None
    last_error: Optional[str] = None
    
    # הגדרות
    max_retries: int = 3
    retry_count: int = 0
    timeout_seconds: Optional[int] = None
    
    # Handle של AsyncIO
    task_handle: Optional[asyncio.Task] = None

class TaskScheduler:
    """מתזמן משימות מתקדם"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.error_handler: Optional[Callable] = None
        
        # הגדרות ברירת מחדל
        self.default_timeout = 300  # 5 דקות
        self.cleanup_interval = 3600  # שעה
        
        logger.info("✅ TaskScheduler initialized")
    
    # ========================= תזמון בסיסי =========================
    
    def schedule_once(self, delay_seconds: int, task_func: Callable, *args, **kwargs) -> str:
        """תזמון משימה חד פעמית"""
        task_id = str(uuid.uuid4())
        scheduled_time = datetime.now() + timedelta(seconds=delay_seconds)
        
        task = ScheduledTask(
            id=task_id,
            name=getattr(task_func, '__name__', 'anonymous'),
            func=task_func,
            args=args,
            kwargs=kwargs,
            scheduled_time=scheduled_time,
            next_run=scheduled_time
        )
        
        self.tasks[task_id] = task
        
        if self.running:
            self._start_task_runner(task)
        
        logger.info(f"📅 Scheduled one-time task {task.name} for {scheduled_time}")
        return task_id
    
    def schedule_recurring(self, interval_seconds: int, task_func: Callable, *args, **kwargs) -> str:
        """תזמון משימה חוזרת"""
        task_id = str(uuid.uuid4())
        next_run = datetime.now() + timedelta(seconds=interval_seconds)
        
        task = ScheduledTask(
            id=task_id,
            name=getattr(task_func, '__name__', 'anonymous'),
            func=task_func,
            args=args,
            kwargs=kwargs,
            interval_seconds=interval_seconds,
            next_run=next_run
        )
        
        self.tasks[task_id] = task
        
        if self.running:
            self._start_task_runner(task)
        
        logger.info(f"🔄 Scheduled recurring task {task.name} every {interval_seconds}s")
        return task_id
    
    def schedule_cron(self, cron_expression: str, task_func: Callable, *args, **kwargs) -> str:
        """תזמון משימה עם ביטוי CRON"""
        task_id = str(uuid.uuid4())
        
        # וולידציה של ביטוי CRON
        if not self._validate_cron_expression(cron_expression):
            raise ValueError(f"Invalid CRON expression: {cron_expression}")
        
        next_run = self._calculate_next_cron_run(cron_expression)
        
        task = ScheduledTask(
            id=task_id,
            name=getattr(task_func, '__name__', 'anonymous'),
            func=task_func,
            args=args,
            kwargs=kwargs,
            cron_expression=cron_expression,
            next_run=next_run
        )
        
        self.tasks[task_id] = task
        
        if self.running:
            self._start_task_runner(task)
        
        logger.info(f"⏰ Scheduled CRON task {task.name} with '{cron_expression}'")
        return task_id
    
    def cancel_scheduled(self, task_id: str) -> bool:
        """ביטול משימה מתוזמנת"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        # ביטול ה-Task אם פועל
        if task.task_handle and not task.task_handle.done():
            task.task_handle.cancel()
        
        task.status = TaskStatus.CANCELLED
        
        logger.info(f"🚫 Cancelled task {task.name} ({task_id})")
        return True
    
    # ========================= ניהול תור =========================
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """קבלת משימות ממתינות"""
        pending_tasks = []
        
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                pending_tasks.append({
                    'id': task.id,
                    'name': task.name,
                    'next_run': task.next_run.isoformat() if task.next_run else None,
                    'type': self._get_task_type(task),
                    'created_at': task.created_at.isoformat()
                })
        
        # מיון לפי זמן הרצה הבא
        pending_tasks.sort(key=lambda x: x['next_run'] or '9999')
        return pending_tasks
    
    def clear_all_scheduled(self):
        """ניקוי כל המשימות המתוזמנות"""
        for task in self.tasks.values():
            if task.task_handle and not task.task_handle.done():
                task.task_handle.cancel()
        
        cleared_count = len(self.tasks)
        self.tasks.clear()
        
        logger.info(f"🗑️ Cleared {cleared_count} scheduled tasks")
    
    def pause_scheduler(self):
        """השהיית המתזמן"""
        self.running = False
        
        # השהיית כל המשימות הפועלות
        for task in self.tasks.values():
            if task.task_handle and not task.task_handle.done():
                task.task_handle.cancel()
        
        logger.info("⏸️ Scheduler paused")
    
    def resume_scheduler(self):
        """חידוש פעילות המתזמן"""
        if self.running:
            return
        
        self.running = True
        
        # התחלת כל המשימות הממתינות
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                self._start_task_runner(task)
        
        # הפעלת משימת ניקוי
        self._start_cleanup_task()
        
        logger.info("▶️ Scheduler resumed")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """קבלת סטטוס המתזמן"""
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(1 for t in self.tasks.values() if t.status == status)
        
        return {
            'running': self.running,
            'total_tasks': len(self.tasks),
            'status_breakdown': status_counts,
            'next_task': self._get_next_scheduled_task(),
            'error_handler_set': self.error_handler is not None
        }
    
    # ========================= טיפול בשגיאות =========================
    
    def set_error_handler(self, handler_func: Callable):
        """הגדרת פונקציית טיפול בשגיאות"""
        self.error_handler = handler_func
        logger.info("🛠️ Error handler set")
    
    def retry_failed_task(self, task_id: str, max_retries: int = 3) -> bool:
        """ניסיון חוזר למשימה שנכשלה"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        
        if task.status != TaskStatus.FAILED:
            return False
        
        task.max_retries = max_retries
        task.retry_count = 0
        task.status = TaskStatus.PENDING
        task.last_error = None
        
        # עדכון זמן הרצה הבא
        if task.interval_seconds:
            task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)
        elif task.cron_expression:
            task.next_run = self._calculate_next_cron_run(task.cron_expression)
        else:
            task.next_run = datetime.now()
        
        if self.running:
            self._start_task_runner(task)
        
        logger.info(f"🔄 Retrying failed task {task.name} ({task_id})")
        return True
    
    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """קבלת משימות שנכשלו"""
        failed_tasks = []
        
        for task in self.tasks.values():
            if task.status == TaskStatus.FAILED:
                failed_tasks.append({
                    'id': task.id,
                    'name': task.name,
                    'last_error': task.last_error,
                    'error_count': task.error_count,
                    'last_run': task.last_run.isoformat() if task.last_run else None,
                    'retry_count': task.retry_count,
                    'max_retries': task.max_retries
                })
        
        return failed_tasks
    
    # ========================= פונקציות פרטיות =========================
    
    def _start_task_runner(self, task: ScheduledTask):
        """הפעלת runner למשימה"""
        async def task_runner():
            while self.running and task.status == TaskStatus.PENDING:
                try:
                    # המתנה עד זמן ההרצה
                    if task.next_run:
                        wait_seconds = (task.next_run - datetime.now()).total_seconds()
                        if wait_seconds > 0:
                            await asyncio.sleep(wait_seconds)
                    
                    if not self.running or task.status != TaskStatus.PENDING:
                        break
                    
                    # הרצת המשימה
                    await self._execute_task(task)
                    
                    # עדכון זמן הרצה הבא
                    if task.interval_seconds:
                        task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)
                    elif task.cron_expression:
                        task.next_run = self._calculate_next_cron_run(task.cron_expression)
                    else:
                        # משימה חד פעמית - סיום
                        task.status = TaskStatus.COMPLETED
                        break
                    
                except asyncio.CancelledError:
                    task.status = TaskStatus.CANCELLED
                    break
                except Exception as e:
                    logger.error(f"Task runner error for {task.name}: {e}")
                    task.status = TaskStatus.FAILED
                    break
        
        task.task_handle = asyncio.create_task(task_runner())
    
    async def _execute_task(self, task: ScheduledTask):
        """הרצת משימה יחידה"""
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now()
        
        try:
            # הרצה עם timeout
            if task.timeout_seconds:
                result = await asyncio.wait_for(
                    self._call_task_function(task),
                    timeout=task.timeout_seconds
                )
            else:
                result = await self._call_task_function(task)
            
            # עדכון תוצאה
            task.last_result = result
            task.run_count += 1
            task.retry_count = 0
            
            if task.interval_seconds or task.cron_expression:
                task.status = TaskStatus.PENDING
            else:
                task.status = TaskStatus.COMPLETED
            
            logger.debug(f"Task {task.name} executed successfully")
            
        except Exception as e:
            await self._handle_task_error(task, e)
    
    async def _call_task_function(self, task: ScheduledTask):
        """קריאה לפונקציית המשימה"""
        if asyncio.iscoroutinefunction(task.func):
            return await task.func(*task.args, **task.kwargs)
        else:
            return task.func(*task.args, **task.kwargs)
    
    async def _handle_task_error(self, task: ScheduledTask, error: Exception):
        """טיפול בשגיאת משימה"""
        task.error_count += 1
        task.last_error = str(error)
        
        logger.error(f"Task {task.name} failed: {error}")
        
        # ניסיון חוזר
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            
            # המתנה לפני ניסיון חוזר (exponential backoff)
            delay = min(300, 2 ** task.retry_count)  # מקסימום 5 דקות
            task.next_run = datetime.now() + timedelta(seconds=delay)
            
            logger.info(f"Retrying task {task.name} in {delay}s (attempt {task.retry_count}/{task.max_retries})")
        else:
            task.status = TaskStatus.FAILED
            
            # קריאה ל-error handler
            if self.error_handler:
                try:
                    await self._call_error_handler(task, error)
                except Exception as handler_error:
                    logger.error(f"Error handler failed: {handler_error}")
    
    async def _call_error_handler(self, task: ScheduledTask, error: Exception):
        """קריאה ל-error handler"""
        if asyncio.iscoroutinefunction(self.error_handler):
            await self.error_handler(task, error)
        else:
            self.error_handler(task, error)
    
    def _get_task_type(self, task: ScheduledTask) -> str:
        """קביעת סוג המשימה"""
        if task.cron_expression:
            return 'cron'
        elif task.interval_seconds:
            return 'recurring'
        else:
            return 'one-time'
    
    def _get_next_scheduled_task(self) -> Optional[Dict[str, Any]]:
        """קבלת המשימה הבאה בתור"""
        pending_tasks = [
            task for task in self.tasks.values() 
            if task.status == TaskStatus.PENDING and task.next_run
        ]
        
        if not pending_tasks:
            return None
        
        next_task = min(pending_tasks, key=lambda t: t.next_run)
        
        return {
            'id': next_task.id,
            'name': next_task.name,
            'next_run': next_task.next_run.isoformat(),
            'type': self._get_task_type(next_task)
        }
    
    def _start_cleanup_task(self):
        """הפעלת משימת ניקוי"""
        async def cleanup_completed_tasks():
            while self.running:
                try:
                    # ניקוי משימות שהושלמו לפני 24 שעות
                    cutoff_time = datetime.now() - timedelta(hours=24)
                    
                    to_remove = [
                        task_id for task_id, task in self.tasks.items()
                        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                        and task.last_run and task.last_run < cutoff_time
                    ]
                    
                    for task_id in to_remove:
                        del self.tasks[task_id]
                    
                    if to_remove:
                        logger.info(f"Cleaned up {len(to_remove)} old tasks")
                    
                except Exception as e:
                    logger.error(f"Cleanup task error: {e}")
                
                await asyncio.sleep(self.cleanup_interval)
        
        asyncio.create_task(cleanup_completed_tasks())
    
    # ========================= CRON Support =========================
    
    def _validate_cron_expression(self, cron_expr: str) -> bool:
        """וולידציה של ביטוי CRON"""
        # פורמט פשוט: minute hour day month day_of_week
        parts = cron_expr.strip().split()
        
        if len(parts) != 5:
            return False
        
        # בדיקה בסיסית של כל חלק
        minute, hour, day, month, day_of_week = parts
        
        return (
            self._validate_cron_field(minute, 0, 59) and
            self._validate_cron_field(hour, 0, 23) and
            self._validate_cron_field(day, 1, 31) and
            self._validate_cron_field(month, 1, 12) and
            self._validate_cron_field(day_of_week, 0, 6)
        )
    
    def _validate_cron_field(self, field: str, min_val: int, max_val: int) -> bool:
        """וולידציה של שדה CRON"""
        if field == '*':
            return True
        
        try:
            # טווח (1-5)
            if '-' in field:
                start, end = map(int, field.split('-'))
                return min_val <= start <= end <= max_val
            
            # רשימה (1,3,5)
            if ',' in field:
                values = [int(x) for x in field.split(',')]
                return all(min_val <= v <= max_val for v in values)
            
            # מספר יחיד
            value = int(field)
            return min_val <= value <= max_val
            
        except (ValueError, TypeError):
            return False
    
    def _calculate_next_cron_run(self, cron_expr: str) -> datetime:
        """חישוב זמן הרצה הבא עבור CRON"""
        # יישום בסיסי - בפועל כדאי להשתמש בספרייה כמו croniter
        
        parts = cron_expr.split()
        minute, hour, day, month, day_of_week = parts
        
        now = datetime.now()
        next_run = now.replace(second=0, microsecond=0)
        
        # הוספת דקה אחת כנקודת התחלה
        next_run += timedelta(minutes=1)
        
        # לולאה למציאת הזמן הבא המתאים
        for _ in range(366):  # מקסימום שנה
            if self._matches_cron_time(next_run, cron_expr):
                return next_run
            next_run += timedelta(minutes=1)
        
        # fallback - שעה מהעכשיו
        return datetime.now() + timedelta(hours=1)
    
    def _matches_cron_time(self, dt: datetime, cron_expr: str) -> bool:
        """בדיקה האם זמן מתאים לביטוי CRON"""
        parts = cron_expr.split()
        minute, hour, day, month, day_of_week = parts
        
        return (
            self._matches_cron_field(dt.minute, minute) and
            self._matches_cron_field(dt.hour, hour) and
            self._matches_cron_field(dt.day, day) and
            self._matches_cron_field(dt.month, month) and
            self._matches_cron_field(dt.weekday(), day_of_week)
        )
    
    def _matches_cron_field(self, value: int, field: str) -> bool:
        """בדיקה האם ערך מתאים לשדה CRON"""
        if field == '*':
            return True
        
        try:
            if '-' in field:
                start, end = map(int, field.split('-'))
                return start <= value <= end
            
            if ',' in field:
                values = [int(x) for x in field.split(',')]
                return value in values
            
            return value == int(field)
            
        except (ValueError, TypeError):
            return False

# ========================= פונקציות עזר לתזמון =========================

def parse_cron_expression(expression: str) -> Dict[str, Any]:
    """פירוק ביטוי CRON למידע מובן"""
    parts = expression.split()
    if len(parts) != 5:
        return {}
    
    return {
        'minute': parts[0],
        'hour': parts[1],
        'day': parts[2],
        'month': parts[3],
        'day_of_week': parts[4],
        'description': _describe_cron_expression(expression)
    }

def calculate_next_run(cron_expression: str) -> Optional[datetime]:
    """חישוב זמן הרצה הבא"""
    scheduler = TaskScheduler()
    try:
        return scheduler._calculate_next_cron_run(cron_expression)
    except:
        return None

def validate_task_function(func: Callable) -> bool:
    """וולידציה של פונקציית משימה"""
    return callable(func) and hasattr(func, '__name__')

def _describe_cron_expression(cron_expr: str) -> str:
    """תיאור בעברית של ביטוי CRON"""
    parts = cron_expr.split()
    if len(parts) != 5:
        return "ביטוי לא תקין"
    
    minute, hour, day, month, day_of_week = parts
    
    # תיאורים פשוטים
    if cron_expr == "0 0 * * *":
        return "כל יום בחצות"
    elif cron_expr == "0 * * * *":
        return "כל שעה"
    elif cron_expr == "*/5 * * * *":
        return "כל 5 דקות"
    elif cron_expr == "0 9 * * 1-5":
        return "כל יום עבודה ב-9:00"
    elif cron_expr == "0 0 1 * *":
        return "כל ראש חודש"
    else:
        return f"דקה {minute}, שעה {hour}, יום {day}, חודש {month}, יום בשבוע {day_of_week}"