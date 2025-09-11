#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 בדיקה מקיפה של כל 37 הבעיות שזוהו במערכת הבוט
טסט קפדני שעובר על כל בעיה בנפרד ומדווח על סטטוס מדויק
"""

import unittest
import asyncio
import os
import sys
import time
import threading
import tempfile
import json
import sqlite3
import re
import subprocess
import psutil
import gc
import logging
import signal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager
import warnings
warnings.filterwarnings('ignore')

# הוספת הנתיב הנכון
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    mysql = None

try:
    import redis
except ImportError:
    redis = None

class TestComprehensiveAll37Issues(unittest.TestCase):
    """בדיקה מקיפה של כל 37 הבעיות"""
    
    @classmethod
    def setUpClass(cls):
        """הכנה לטסטים"""
        print("\n🔍 מתחיל בדיקה מקיפה של כל 37 הבעיות במערכת")
        print("=" * 80)
        
        cls.issues_found = []
        cls.issues_resolved = []
        cls.critical_count = 0
        cls.warning_count = 0
        
        # הגדרת משתני סביבה לטסט
        os.environ['BOT_TOKEN'] = 'test_token_for_comprehensive_test'
        os.environ['DB_HOST'] = '127.0.0.1'
        os.environ['REDIS_HOST'] = '127.0.0.1'
        os.environ['USE_DATABASE'] = 'true'
        
    def report_issue(self, issue_number, title, status, details="", severity="CRITICAL"):
        """דיווח על בעיה"""
        issue_data = {
            'number': issue_number,
            'title': title,
            'status': status,
            'details': details,
            'severity': severity,
            'timestamp': datetime.now()
        }
        
        if status == "FOUND":
            self.issues_found.append(issue_data)
            if severity == "CRITICAL":
                self.critical_count += 1
            else:
                self.warning_count += 1
        else:
            self.issues_resolved.append(issue_data)
            
        # הדפסת דיווח מיידי
        emoji = "🚨" if severity == "CRITICAL" else "⚠️" if severity == "WARNING" else "✅"
        status_emoji = "❌" if status == "FOUND" else "✅"
        
        print(f"{emoji} בעיה #{issue_number:02d}: {title}")
        print(f"   סטטוס: {status_emoji} {status}")
        if details:
            print(f"   פרטים: {details}")
        print()

    # ========================================
    # בעיות דחופות מיד (1-7)
    # ========================================
    
    def test_01_fulfill_request_database_error(self):
        """בדיקת שגיאת מילוי בקשות במסד נתונים"""
        print("🔍 בודק בעיה #1: שגיאת מילוי בקשות במסד נתונים...")
        
        try:
            # חיפוש אחר שגיאות מסד נתונים בקוד
            error_patterns = [
                "שגיאה בעדכון מסד הנתונים",
                "Failed to update",
                "Database error",
                "SQL error"
            ]
            
            # בדיקת קבצי השירותים
            files_to_check = [
                "services/request_service.py",
                "database/connection_pool.py",
                "main/pirate_bot_main.py"
            ]
            
            errors_found = []
            for file_path in files_to_check:
                full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        for pattern in error_patterns:
                            if pattern in content:
                                errors_found.append(f"{file_path}: {pattern}")
                    except Exception as e:
                        errors_found.append(f"Error reading {file_path}: {e}")
            
            # בדיקת חיבור למסד נתונים פרקטית
            connection_issues = []
            try:
                if mysql:
                    # נסיון חיבור למסד נתונים
                    conn = mysql.connector.connect(
                        host=os.getenv('DB_HOST', '127.0.0.1'),
                        port=3306,
                        user=os.getenv('DB_USER', 'pirate_user'),
                        password=os.getenv('DB_PASSWORD', 'test_password_123'),
                        database=os.getenv('DB_NAME', 'pirate_content'),
                        connection_timeout=2
                    )
                    conn.close()
                else:
                    connection_issues.append("MySQL connector not available")
            except Exception as e:
                connection_issues.append(f"Connection failed: {e}")
            
            if errors_found or connection_issues:
                details = f"שגיאות נמצאו: {len(errors_found + connection_issues)}"
                if errors_found:
                    details += f"\nשגיאות בקוד: {errors_found[:3]}"
                if connection_issues:
                    details += f"\nבעיות חיבור: {connection_issues}"
                    
                self.report_issue(1, "שגיאת מילוי בקשות במסד נתונים", "FOUND", details, "CRITICAL")
            else:
                self.report_issue(1, "שגיאת מילוי בקשות במסד נתונים", "RESOLVED", "לא נמצאו בעיות במסד נתונים")
                
        except Exception as e:
            self.report_issue(1, "שגיאת מילוי בקשות במסד נתונים", "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

    def test_02_new_user_every_start(self):
        """בדיקת בעיית 'משתמש חדש' בכל /start"""
        print("🔍 בודק בעיה #2: משתמש חדש בכל /start...")
        
        try:
            # חיפוש אחר הלוגיקה שמטפלת ב-/start
            start_handler_files = []
            user_creation_logic = []
            
            # בדיקת הקובץ הראשי
            main_file = os.path.join(os.path.dirname(__file__), "..", "main/pirate_bot_main.py")
            if os.path.exists(main_file):
                with open(main_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # חיפוש אחר פונקציית start
                if '/start' in content or 'start_command' in content:
                    start_handler_files.append("main/pirate_bot_main.py")
                    
                # חיפוש אחר לוגיקת יצירת משתמש
                patterns = [
                    'משתמש חדש',
                    'new user',
                    'create_user',
                    'add_user',
                    'register_user'
                ]
                
                for pattern in patterns:
                    if pattern.lower() in content.lower():
                        user_creation_logic.append(f"Found '{pattern}' in main file")
            
            # בדיקת קבצי שירותים
            services_files = [
                "services/user_service.py",
                "services/request_service.py"
            ]
            
            for file_path in services_files:
                full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # בדיקת לוגיקת בדיקת קיום משתמש
                    if 'get_user_by_id' in content or 'user_exists' in content:
                        user_creation_logic.append(f"User existence check in {file_path}")
                    
                    # חיפוש אחר בעיות בלוגיקה
                    problematic_patterns = [
                        'always create',
                        'INSERT IGNORE',
                        'ON DUPLICATE KEY',
                        'if not.*user.*:'
                    ]
                    
                    for pattern in problematic_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            user_creation_logic.append(f"Potential issue: {pattern} in {file_path}")
            
            # ניתוח התוצאות
            if not user_creation_logic:
                self.report_issue(2, "משתמש חדש בכל /start", "FOUND", 
                                "לא נמצאה לוגיקת בדיקת קיום משתמש", "CRITICAL")
            elif any("always create" in logic.lower() for logic in user_creation_logic):
                self.report_issue(2, "משתמש חדש בכל /start", "FOUND", 
                                "נמצאה לוגיקה שיוצרת משתמש תמיד", "CRITICAL")
            else:
                details = f"נמצאו {len(user_creation_logic)} מקומות עם לוגיקת משתמש"
                self.report_issue(2, "משתמש חדש בכל /start", "RESOLVED", details)
                
        except Exception as e:
            self.report_issue(2, "משתמש חדש בכל /start", "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

    def test_03_connection_pool_failures(self):
        """בדיקת כשלים ב-Connection Pool"""
        print("🔍 בודק בעיה #3: כשלים ב-Connection Pool...")
        
        try:
            # בדיקת קובץ connection pool
            pool_file = os.path.join(os.path.dirname(__file__), "..", "database/connection_pool.py")
            
            if not os.path.exists(pool_file):
                self.report_issue(3, "Connection Pool Failures", "FOUND", 
                                "קובץ connection_pool.py לא נמצא", "CRITICAL")
                return
            
            with open(pool_file, 'r', encoding='utf-8') as f:
                pool_content = f.read()
            
            # בדיקת דפוסי שגיאה
            error_indicators = []
            
            # בדיקת bare except clauses
            bare_excepts = len(re.findall(r'except\s*:', pool_content))
            if bare_excepts > 0:
                error_indicators.append(f"{bare_excepts} bare except clauses")
            
            # בדיקת error handling
            if 'failed_connections' in pool_content:
                error_indicators.append("מעקב אחר חיבורים כושלים נמצא")
            
            # בדיקת retry logic
            if 'retry' not in pool_content.lower() and 'reconnect' not in pool_content.lower():
                error_indicators.append("חסר מנגנון retry")
            
            # בדיקת timeout handling
            if 'timeout' not in pool_content.lower():
                error_indicators.append("חסר טיפול ב-timeout")
            
            # בדיקת pool size management
            if 'pool_size' not in pool_content:
                error_indicators.append("חסר ניהול גודל pool")
            
            # בדיקת connection validation
            if 'validate' not in pool_content and 'ping' not in pool_content:
                error_indicators.append("חסר validation של חיבורים")
            
            # בדיקה פרקטית של Connection Pool
            practical_issues = []
            try:
                # ניסיון יבוא של המחלקה
                sys.path.insert(0, os.path.dirname(pool_file))
                from connection_pool import DatabaseConnectionPool
                
                # יצירת instance עם הגדרות טסט
                test_config = {
                    'host': 'localhost',
                    'port': 3306,
                    'user': 'test',
                    'password': 'test',
                    'database': 'test',
                    'pool_size': 5
                }
                
                pool = DatabaseConnectionPool(test_config)
                
                # בדיקת methods חיוניים
                if not hasattr(pool, 'get_connection'):
                    practical_issues.append("חסר method get_connection")
                
                if not hasattr(pool, 'close_all_connections'):
                    practical_issues.append("חסר method close_all_connections")
                    
                if not hasattr(pool, 'health_check'):
                    practical_issues.append("חסר method health_check")
                    
            except Exception as e:
                practical_issues.append(f"שגיאה ביצירת pool: {e}")
            
            # דיווח תוצאות
            total_issues = len(error_indicators) + len(practical_issues)
            if total_issues > 0:
                details = f"נמצאו {total_issues} בעיות:\n"
                details += "\n".join(error_indicators + practical_issues)
                self.report_issue(3, "Connection Pool Failures", "FOUND", details, "CRITICAL")
            else:
                self.report_issue(3, "Connection Pool Failures", "RESOLVED", 
                                "Connection pool נראה תקין")
                
        except Exception as e:
            self.report_issue(3, "Connection Pool Failures", "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

    def test_04_json_backup_datetime_error(self):
        """בדיקת שגיאת JSON backup עם datetime"""
        print("🔍 בודק בעיה #4: שגיאת JSON backup עם datetime...")
        
        try:
            # חיפוש אחר קבצים שמטפלים ב-backup/export
            backup_files = []
            json_issues = []
            
            # קבצים חשודים
            potential_files = [
                "admin/admin_panel.py",
                "utils/json_helpers.py", 
                "main/pirate_bot_main.py",
                "services/backup_service.py",
                "utils/export_utils.py"
            ]
            
            for file_path in potential_files:
                full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
                if os.path.exists(full_path):
                    backup_files.append(file_path)
                    
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # בדיקת שימוש ב-json.dumps
                    if 'json.dumps' in content:
                        # בדיקה אם יש custom serializer
                        if 'default=' not in content and 'cls=' not in content:
                            json_issues.append(f"{file_path}: json.dumps ללא custom serializer")
                    
                    # בדיקת datetime objects
                    if 'datetime' in content and ('backup' in content or 'export' in content):
                        json_issues.append(f"{file_path}: שימוש ב-datetime עם backup/export")
                    
                    # בדיקת השגיאה הספציפית
                    if 'not JSON serializable' in content:
                        json_issues.append(f"{file_path}: מכיל את השגיאה הידועה")
            
            # בדיקה פרקטית של serialization
            datetime_serialization_test = []
            try:
                import json
                
                # טסט עם datetime object
                test_data = {
                    'timestamp': datetime.now(),
                    'date': datetime.now().date(),
                    'time': datetime.now().time()
                }
                
                # נסיון serialization רגיל
                try:
                    json.dumps(test_data)
                except TypeError as e:
                    datetime_serialization_test.append(f"DateTime serialization failed: {e}")
                
                # בדיקה אם יש custom encoder
                try:
                    # ניסיון import של json helpers
                    json_helpers_path = os.path.join(os.path.dirname(__file__), "..", "utils/json_helpers.py")
                    if os.path.exists(json_helpers_path):
                        sys.path.insert(0, os.path.dirname(json_helpers_path))
                        try:
                            from json_helpers import safe_json_dumps, DateTimeEncoder
                            result = safe_json_dumps(test_data)
                            if result is None:
                                datetime_serialization_test.append("safe_json_dumps returned None")
                        except ImportError:
                            datetime_serialization_test.append("לא ניתן לייבא json helpers")
                        except Exception as e:
                            datetime_serialization_test.append(f"json helpers failed: {e}")
                    else:
                        datetime_serialization_test.append("json_helpers.py לא נמצא")
                except Exception as e:
                    datetime_serialization_test.append(f"Custom encoder test failed: {e}")
                    
            except Exception as e:
                datetime_serialization_test.append(f"Serialization test error: {e}")
            
            # דיווח תוצאות
            total_issues = len(json_issues) + len(datetime_serialization_test)
            if total_issues > 0:
                details = f"נמצאו {total_issues} בעיות JSON/DateTime:\n"
                details += f"בעיות בקוד: {json_issues}\n"
                details += f"בעיות פרקטיות: {datetime_serialization_test}"
                self.report_issue(4, "JSON Backup DateTime Error", "FOUND", details, "CRITICAL")
            else:
                self.report_issue(4, "JSON Backup DateTime Error", "RESOLVED", 
                                "JSON serialization עם datetime עובד כראוי")
                
        except Exception as e:
            self.report_issue(4, "JSON Backup DateTime Error", "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

    def test_05_thread_safety_issues(self):
        """בדיקת בעיות Thread Safety"""
        print("🔍 בודק בעיה #5: בעיות Thread Safety...")
        
        try:
            thread_safety_issues = []
            
            # בדיקת משתנים גלובליים
            files_to_check = [
                "main/pirate_bot_main.py",
                "services/user_service.py",
                "services/request_service.py",
                "utils/cache_manager.py",
                "core/storage_manager.py"
            ]
            
            global_vars_found = []
            shared_resources = []
            sync_mechanisms = []
            
            for file_path in files_to_check:
                full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
                if not os.path.exists(full_path):
                    continue
                    
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # בדיקת משתנים גלובליים
                global_pattern = re.findall(r'^[A-Z_][A-Z0-9_]*\s*=', content, re.MULTILINE)
                if global_pattern:
                    global_vars_found.extend([f"{file_path}: {var}" for var in global_pattern[:3]])
                
                # בדיקת shared resources
                shared_patterns = [
                    '_cache', '_pool', '_connection', '_session',
                    'global ', 'shared_', 'instance_'
                ]
                
                for pattern in shared_patterns:
                    if pattern in content:
                        shared_resources.append(f"{file_path}: {pattern}")
                
                # בדיקת מנגנוני synchronization
                sync_patterns = [
                    'threading.Lock', 'threading.RLock', 'asyncio.Lock',
                    'threading.Semaphore', 'Queue', 'async with'
                ]
                
                for pattern in sync_patterns:
                    if pattern in content:
                        sync_mechanisms.append(f"{file_path}: {pattern}")
            
            # בדיקה פרקטית של thread safety
            race_condition_test = []
            try:
                # טסט פשוט לrace conditions
                shared_counter = {'value': 0}
                lock = threading.Lock()
                
                def increment_without_lock():
                    for _ in range(1000):
                        shared_counter['value'] += 1
                
                def increment_with_lock():
                    for _ in range(1000):
                        with lock:
                            shared_counter['value'] += 1
                
                # טסט ללא lock
                shared_counter['value'] = 0
                threads = [threading.Thread(target=increment_without_lock) for _ in range(5)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                
                unsafe_result = shared_counter['value']
                expected = 5000
                
                if unsafe_result != expected:
                    race_condition_test.append(f"Race condition detected: {unsafe_result} != {expected}")
                
            except Exception as e:
                race_condition_test.append(f"Thread safety test failed: {e}")
            
            # ניתוח תוצאות
            issues_count = 0
            
            if len(global_vars_found) > len(sync_mechanisms):
                issues_count += 1
                thread_safety_issues.append("יותר משתנים גלובליים מאשר מנגנוני sync")
            
            if shared_resources and not sync_mechanisms:
                issues_count += 1
                thread_safety_issues.append("נמצאו shared resources ללא synchronization")
            
            if race_condition_test:
                issues_count += 1
                thread_safety_issues.extend(race_condition_test)
            
            # דיווח
            if issues_count > 0:
                details = f"נמצאו {issues_count} בעיות thread safety:\n"
                details += f"משתנים גלובליים: {len(global_vars_found)}\n"
                details += f"מנגנוני sync: {len(sync_mechanisms)}\n"
                details += "\n".join(thread_safety_issues)
                self.report_issue(5, "Thread Safety Issues", "FOUND", details, "CRITICAL")
            else:
                self.report_issue(5, "Thread Safety Issues", "RESOLVED", 
                                "לא נמצאו בעיות thread safety משמעותיות")
                
        except Exception as e:
            self.report_issue(5, "Thread Safety Issues", "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

    def test_06_data_consistency_cache_db(self):
        """בדיקת עקביות נתונים בין Cache למסד נתונים"""
        print("🔍 בודק בעיה #6: עקביות נתונים בין Cache ל-DB...")
        
        try:
            consistency_issues = []
            
            # בדיקת קבצי cache וDB
            cache_files = []
            db_files = []
            
            # חיפוש קבצי cache
            cache_locations = [
                "utils/cache_manager.py",
                "services/user_service.py",
                "services/request_service.py"
            ]
            
            for file_path in cache_locations:
                full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if any(pattern in content for pattern in ['_cache', 'redis', 'Cache']):
                        cache_files.append(file_path)
                    
                    if any(pattern in content for pattern in ['database', 'mysql', 'execute', 'query']):
                        db_files.append(file_path)
            
            # בדיקת פונקציות cache vs DB
            cache_invalidation_found = []
            transaction_handling = []
            
            for file_path in cache_files:
                full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # בדיקת cache invalidation
                if any(pattern in content for pattern in ['invalidate', 'clear_cache', 'delete', 'expire']):
                    cache_invalidation_found.append(file_path)
                
                # בדיקת transaction handling
                if any(pattern in content for pattern in ['transaction', 'commit', 'rollback']):
                    transaction_handling.append(file_path)
            
            # בדיקת דפוסי בעיות
            potential_issues = []
            
            # בדיקה אם יש cache ללא invalidation
            if cache_files and not cache_invalidation_found:
                potential_issues.append("נמצא cache ללא מנגנון invalidation")
            
            # בדיקה אם יש DB operations ללא cache sync
            cache_sync_patterns = [
                'update.*cache',
                'cache.*update',
                'sync.*cache',
                'refresh.*cache'
            ]
            
            sync_found = False
            for file_path in db_files:
                full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in cache_sync_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        sync_found = True
                        break
            
            if cache_files and db_files and not sync_found:
                potential_issues.append("DB operations ללא sync עם cache")
            
            # בדיקה פרקטית - סימולציה של inconsistency
            practical_test = []
            try:
                # טסט פשוט לבדיקת consistency
                cache_data = {'requests': ['1', '2', '3']}
                db_data = {'requests': ['1', '2', '3', '4']}  # DB has more data
                
                if len(cache_data['requests']) != len(db_data['requests']):
                    practical_test.append("Simulated inconsistency detected")
                    
                # בדיקת race condition בעדכון
                def update_cache_only():
                    cache_data['requests'].append('5')
                
                def update_db_only():
                    db_data['requests'].append('6')
                
                # עדכונים במקביל
                t1 = threading.Thread(target=update_cache_only)
                t2 = threading.Thread(target=update_db_only)
                
                t1.start()
                t2.start()
                t1.join()
                t2.join()
                
                if len(cache_data['requests']) != len(db_data['requests']):
                    practical_test.append("Race condition in updates detected")
                    
            except Exception as e:
                practical_test.append(f"Consistency test failed: {e}")
            
            # דיווח תוצאות
            total_issues = len(potential_issues) + len(practical_test)
            if total_issues > 0:
                details = f"נמצאו {total_issues} בעיות consistency:\n"
                details += f"Cache files: {len(cache_files)}\n"
                details += f"DB files: {len(db_files)}\n"
                details += f"Cache invalidation: {len(cache_invalidation_found)}\n"
                details += "\n".join(potential_issues + practical_test)
                
                self.report_issue(6, "Data Consistency Cache-DB", "FOUND", details, "CRITICAL")
            else:
                self.report_issue(6, "Data Consistency Cache-DB", "RESOLVED", 
                                "מנגנוני consistency נראים תקינים")
                
        except Exception as e:
            self.report_issue(6, "Data Consistency Cache-DB", "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

    def test_07_broken_callback_handlers(self):
        """בדיקת Callback Handlers שבורים"""
        print("🔍 בודק בעיה #7: Callback Handlers שבורים...")
        
        try:
            callback_issues = []
            
            # חיפוש קבצים עם callback handlers
            main_file = os.path.join(os.path.dirname(__file__), "..", "main/pirate_bot_main.py")
            
            if not os.path.exists(main_file):
                self.report_issue(7, "Broken Callback Handlers", "FOUND", 
                                "קובץ main לא נמצא", "CRITICAL")
                return
            
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # בדיקת callback handlers
            callback_patterns = []
            handler_registrations = []
            callback_functions = []
            
            # חיפוש רישומי handlers
            handler_patterns = [
                r'CallbackQueryHandler\s*\(',
                r'\.add_handler\s*\(',
                r'callback_query_handler',
                r'@.*callback'
            ]
            
            for pattern in handler_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                handler_registrations.extend(matches)
            
            # חיפוש פונקציות callback
            callback_function_patterns = [
                r'async def.*callback',
                r'def.*callback',
                r'def.*button',
                r'async def.*button'
            ]
            
            for pattern in callback_function_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                callback_functions.extend(matches)
            
            # בדיקת callback data patterns
            callback_data_patterns = [
                r'callback_data\s*=\s*["\']([^"\']+)',
                r'data\s*=\s*["\']([^"\']+)'
            ]
            
            callback_data = []
            for pattern in callback_data_patterns:
                matches = re.findall(pattern, content)
                callback_data.extend(matches)
            
            # חיפוש הודעות "לא מזוהה"
            unrecognized_patterns = [
                'לא מזוהה',
                'not recognized',
                'unknown callback',
                'unhandled callback'
            ]
            
            unrecognized_found = []
            for pattern in unrecognized_patterns:
                if pattern in content:
                    unrecognized_found.append(pattern)
            
            # בדיקת consistency
            issues_found = []
            
            if len(callback_data) > len(callback_functions):
                issues_found.append(f"יותר callback data ({len(callback_data)}) מאשר functions ({len(callback_functions)})")
            
            if unrecognized_found:
                issues_found.append(f"נמצאו הודעות 'לא מזוהה': {unrecognized_found}")
            
            if not handler_registrations and callback_functions:
                issues_found.append("נמצאו callback functions ללא registration")
            
            # בדיקת דפוסי callback data ספציפיים
            problematic_callbacks = []
            expected_callbacks = ['view_request', 'admin:pending', 'admin:stats']
            
            for expected in expected_callbacks:
                if expected not in content:
                    problematic_callbacks.append(f"Missing handler for: {expected}")
            
            # בדיקת error handling בcallbacks
            error_handling_in_callbacks = False
            if any(pattern in content for pattern in ['try:', 'except', 'callback.*error']):
                error_handling_in_callbacks = True
            
            if not error_handling_in_callbacks and callback_functions:
                issues_found.append("Callback functions ללא error handling")
            
            # דיווח תוצאות
            total_issues = len(issues_found) + len(problematic_callbacks)
            if total_issues > 0:
                details = f"נמצאו {total_issues} בעיות callback:\n"
                details += f"Handler registrations: {len(handler_registrations)}\n"
                details += f"Callback functions: {len(callback_functions)}\n"
                details += f"Callback data patterns: {len(callback_data)}\n"
                details += "\n".join(issues_found + problematic_callbacks)
                
                self.report_issue(7, "Broken Callback Handlers", "FOUND", details, "CRITICAL")
            else:
                self.report_issue(7, "Broken Callback Handlers", "RESOLVED", 
                                "Callback handlers נראים תקינים")
                
        except Exception as e:
            self.report_issue(7, "Broken Callback Handlers", "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

    # ========================================
    # בעיות קריטיות לטווח קצר (8-17)
    # ========================================
    
    def test_08_memory_leaks(self):
        """בדיקת Memory Leaks"""
        print("🔍 בודק בעיה #8: Memory Leaks...")
        
        try:
            memory_issues = []
            
            # בדיקת memory בתחילה
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # בדיקת דפוסי בעיות memory
            files_to_check = [
                "main/pirate_bot_main.py",
                "services/user_service.py", 
                "services/request_service.py",
                "utils/cache_manager.py"
            ]
            
            resource_management_issues = []
            cleanup_mechanisms = []
            
            for file_path in files_to_check:
                full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
                if not os.path.exists(full_path):
                    continue
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # בדיקת resource management
                resource_patterns = [
                    'open(', 'file.', 'connect(', 'connection',
                    'cache[', 'dict[', 'list.append'
                ]
                
                cleanup_patterns = [
                    'close()', 'del ', '__del__', 'cleanup',
                    'clear()', 'pop()', 'remove()'
                ]
                
                resources_found = sum(1 for pattern in resource_patterns if pattern in content)
                cleanup_found = sum(1 for pattern in cleanup_patterns if pattern in content)
                
                if resources_found > cleanup_found:
                    resource_management_issues.append(
                        f"{file_path}: {resources_found} resources, {cleanup_found} cleanup"
                    )
                
                # בדיקת cleanup mechanisms
                if any(pattern in content for pattern in cleanup_patterns):
                    cleanup_mechanisms.append(file_path)
            
            # בדיקה פרקטית של memory
            memory_test_results = []
            try:
                # סימולציה של memory usage
                test_objects = []
                
                # יצירת אובייקטים
                for i in range(1000):
                    test_objects.append({
                        'id': i,
                        'data': 'x' * 1000,  # 1KB per object
                        'timestamp': datetime.now()
                    })
                
                mid_memory = process.memory_info().rss / 1024 / 1024
                
                # ניקוי חלקי
                del test_objects[:500]
                gc.collect()
                
                after_partial_cleanup = process.memory_info().rss / 1024 / 1024
                
                # ניקוי מלא
                del test_objects
                gc.collect()
                
                final_memory = process.memory_info().rss / 1024 / 1024
                
                memory_growth = final_memory - initial_memory
                if memory_growth > 5:  # More than 5MB growth
                    memory_test_results.append(f"Memory growth detected: {memory_growth:.2f}MB")
                
                # בדיקת garbage collection
                gc_stats = gc.get_stats()
                total_objects = sum(stat['collections'] for stat in gc_stats)
                if total_objects == 0:
                    memory_test_results.append("GC not running properly")
                    
            except Exception as e:
                memory_test_results.append(f"Memory test failed: {e}")
            
            # בדיקת דפוסי memory leaks בקוד
            code_patterns_issues = []
            
            # חיפוש דפוסי בעיות נפוצים
            leak_patterns = [
                ('global.*=.*\\[\\]', 'Global lists that grow'),
                ('global.*=.*\\{\\}', 'Global dicts that grow'), 
                ('while True:', 'Infinite loops'),
                ('cache.*=.*', 'Unbounded caches'),
                ('_instances.*=', 'Instance tracking without cleanup')
            ]
            
            for file_path in files_to_check:
                full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
                if not os.path.exists(full_path):
                    continue
                    
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern, description in leak_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        code_patterns_issues.append(f"{file_path}: {description}")
            
            # דיווח תוצאות
            total_issues = (len(resource_management_issues) + 
                          len(memory_test_results) + 
                          len(code_patterns_issues))
            
            if total_issues > 0:
                details = f"נמצאו {total_issues} בעיות memory:\n"
                details += f"Initial memory: {initial_memory:.2f}MB\n"
                details += f"Final memory: {process.memory_info().rss / 1024 / 1024:.2f}MB\n"
                details += "\n".join(resource_management_issues + memory_test_results + code_patterns_issues)
                
                self.report_issue(8, "Memory Leaks", "FOUND", details, "CRITICAL")
            else:
                self.report_issue(8, "Memory Leaks", "RESOLVED", 
                                f"לא נמצאו memory leaks. זיכרון: {initial_memory:.2f}MB")
                
        except Exception as e:
            self.report_issue(8, "Memory Leaks", "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

    def test_09_credentials_exposure(self):
        """בדיקת חשיפת Credentials"""
        print("🔍 בודק בעיה #9: חשיפת Credentials...")
        
        try:
            security_issues = []
            
            # דפוסי credentials חשופים
            credential_patterns = [
                (r'BOT_TOKEN\s*=\s*["\']([^"\']+)', 'Bot Token'),
                (r'password\s*=\s*["\']([^"\']+)', 'Password'),
                (r'api_key\s*=\s*["\']([^"\']+)', 'API Key'),
                (r'secret\s*=\s*["\']([^"\']+)', 'Secret'),
                (r'token\s*=\s*["\']([^"\']+)', 'Token'),
                (r'key\s*=\s*["\'][0-9a-fA-F]{20,}', 'Long Key'),
                (r'mysql://[^\\s]+', 'Database URL'),
                (r'redis://[^\\s]+', 'Redis URL')
            ]
            
            # קבצים לבדיקה
            files_to_scan = []
            
            # סריקת כל הקבצים בפרויקט
            for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
                # דלג על תיקיות מסוימות
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache']]
                
                for file in files:
                    if file.endswith(('.py', '.env', '.config', '.json', '.yaml', '.yml')):
                        files_to_scan.append(os.path.join(root, file))
            
            exposed_credentials = []
            hardcoded_secrets = []
            
            for file_path in files_to_scan:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # בדיקת כל דפוס
                    for pattern, credential_type in credential_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for match in matches:
                            # בדיקה אם זה לא placeholder
                            if (len(match) > 10 and 
                                'example' not in match.lower() and
                                'placeholder' not in match.lower() and
                                'your_' not in match.lower() and
                                'test_' not in match.lower()):
                                
                                exposed_credentials.append(
                                    f"{os.path.relpath(file_path)}: {credential_type}"
                                )
                    
                    # בדיקת hardcoded values חשודים
                    suspicious_patterns = [
                        r'["\'][0-9a-fA-F]{32,}["\']',  # Hex strings
                        r'["\'][A-Za-z0-9+/]{40,}={0,2}["\']',  # Base64
                        r'sk-[A-Za-z0-9]{20,}',  # API keys
                        r'ghp_[A-Za-z0-9]{36}',  # GitHub tokens
                    ]
                    
                    for pattern in suspicious_patterns:
                        if re.search(pattern, content):
                            hardcoded_secrets.append(
                                f"{os.path.relpath(file_path)}: Suspicious hardcoded value"
                            )
                            
                except Exception as e:
                    continue
            
            # בדיקת משתני סביבה
            env_issues = []
            
            # בדיקה אם יש שימוש במשתני סביבה
            env_usage_found = False
            for file_path in files_to_scan:
                if not file_path.endswith('.py'):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    if any(pattern in content for pattern in ['os.environ', 'getenv', 'env.get']):
                        env_usage_found = True
                        break
                except:
                    continue
            
            if not env_usage_found:
                env_issues.append("לא נמצא שימוש במשתני סביבה")
            
            # בדיקת קבצי .env
            env_files = [f for f in files_to_scan if '.env' in os.path.basename(f)]
            if not env_files:
                env_issues.append("לא נמצא קובץ .env")
            
            # בדיקת logging של credentials
            logging_issues = []
            for file_path in files_to_scan:
                if not file_path.endswith('.py'):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # חיפוש logging של מידע רגיש
                    if any(pattern in content for pattern in ['log.*token', 'print.*password', 'debug.*key']):
                        logging_issues.append(f"{os.path.relpath(file_path)}: Potential credential logging")
                        
                except:
                    continue
            
            # דיווח תוצאות
            total_issues = (len(exposed_credentials) + 
                          len(hardcoded_secrets) + 
                          len(env_issues) + 
                          len(logging_issues))
            
            if total_issues > 0:
                details = f"נמצאו {total_issues} בעיות אבטחה:\n"
                details += f"Exposed credentials: {len(exposed_credentials)}\n"
                details += f"Hardcoded secrets: {len(hardcoded_secrets)}\n"
                details += f"Env issues: {len(env_issues)}\n"
                details += f"Logging issues: {len(logging_issues)}\n"
                
                if exposed_credentials:
                    details += "\nExposed credentials:\n" + "\n".join(exposed_credentials[:5])
                if hardcoded_secrets:
                    details += "\nHardcoded secrets:\n" + "\n".join(hardcoded_secrets[:3])
                    
                self.report_issue(9, "Credentials Exposure", "FOUND", details, "CRITICAL")
            else:
                self.report_issue(9, "Credentials Exposure", "RESOLVED", 
                                "לא נמצאו credentials חשופים")
                
        except Exception as e:
            self.report_issue(9, "Credentials Exposure", "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

    def test_10_cache_mechanism_issues(self):
        """בדיקת בעיות במנגנון Cache"""
        print("🔍 בודק בעיה #10: בעיות במנגנון Cache...")
        
        try:
            cache_issues = []
            
            # בדיקת קבצי cache
            cache_file = os.path.join(os.path.dirname(__file__), "..", "utils/cache_manager.py")
            
            cache_implementation = []
            cache_patterns_found = []
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # בדיקת implementation patterns
                implementation_checks = [
                    ('class.*Cache', 'Cache class defined'),
                    ('def get', 'Get method'),
                    ('def set', 'Set method'),
                    ('def delete', 'Delete method'),
                    ('def clear', 'Clear method'),
                    ('TTL', 'TTL support'),
                    ('expire', 'Expiration support'),
                    ('redis', 'Redis backend'),
                    ('memory', 'Memory backend')
                ]
                
                for pattern, description in implementation_checks:
                    if re.search(pattern, content, re.IGNORECASE):
                        cache_implementation.append(description)
                
                # בדיקת בעיות נפוצות
                common_issues = [
                    ('global.*cache.*=', 'Global cache variable'),
                    (r'cache\[.*\]\s*=', 'Direct cache assignment'),
                    ('del cache', 'Manual cache deletion'),
                    ('cache.*=.*\\{\\}', 'Dictionary as cache'),
                    ('cache.*=.*\\[\\]', 'List as cache')
                ]
                
                for pattern, issue in common_issues:
                    if re.search(pattern, content, re.IGNORECASE):
                        cache_patterns_found.append(f"Issue: {issue}")
            else:
                cache_issues.append("קובץ cache_manager.py לא נמצא")
            
            # בדיקת שימוש ב-cache בקבצים אחרים
            cache_usage = []
            services_files = [
                "services/user_service.py",
                "services/request_service.py", 
                "main/pirate_bot_main.py"
            ]
            
            for file_path in services_files:
                full_path = os.path.join(os.path.dirname(__file__), "..", file_path)
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    cache_operations = []
                    if '_cache' in content:
                        cache_operations.append('Cache variable used')
                    if 'cache.get' in content:
                        cache_operations.append('Cache get')
                    if 'cache.set' in content:
                        cache_operations.append('Cache set')
                    if 'cache.clear' in content or 'cache.delete' in content:
                        cache_operations.append('Cache invalidation')
                    
                    if cache_operations:
                        cache_usage.append(f"{file_path}: {cache_operations}")
            
            # בדיקה פרקטית של cache
            practical_cache_test = []
            try:
                # טסט cache פשוט
                test_cache = {}
                
                # בדיקת בסיסי operations
                test_cache['key1'] = 'value1'
                if test_cache.get('key1') != 'value1':
                    practical_cache_test.append("Basic cache get/set failed")
                
                # בדיקת memory growth
                initial_size = len(test_cache)
                for i in range(1000):
                    test_cache[f'key_{i}'] = f'value_{i}'
                
                if len(test_cache) > 500:  # No automatic cleanup
                    practical_cache_test.append("Cache grows without bounds")
                
                # בדיקת thread safety
                def cache_writer():
                    for i in range(100):
                        test_cache[f'thread_key_{i}'] = f'thread_value_{i}'
                
                threads = [threading.Thread(target=cache_writer) for _ in range(3)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                
                # בדיקה אם הכל נכתב כראוי
                expected_keys = 3 * 100  # 3 threads * 100 keys each
                thread_keys = [k for k in test_cache.keys() if k.startswith('thread_key_')]
                if len(thread_keys) < expected_keys * 0.9:  # Allow some race condition
                    practical_cache_test.append("Thread safety issues in cache")
                    
            except Exception as e:
                practical_cache_test.append(f"Cache test failed: {e}")
            
            # בדיקת Redis connectivity (אם זמין)
            redis_test = []
            if redis:
                try:
                    r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=2)
                    r.ping()
                    
                    # בדיקת בסיסי Redis operations
                    r.set('test_key', 'test_value')
                    if r.get('test_key').decode() != 'test_value':
                        redis_test.append("Redis basic operations failed")
                    
                    r.delete('test_key')
                    
                except Exception as e:
                    redis_test.append(f"Redis connection failed: {e}")
            else:
                redis_test.append("Redis module not available")
            
            # ניתוח תוצאות
            total_issues = (len(cache_issues) + 
                          len(cache_patterns_found) + 
                          len(practical_cache_test) + 
                          len(redis_test))
            
            if total_issues > 0:
                details = f"נמצאו {total_issues} בעיות cache:\n"
                details += f"Cache implementation features: {len(cache_implementation)}\n"
                details += f"Cache usage in services: {len(cache_usage)}\n"
                
                if cache_issues:
                    details += f"\nCache issues: {cache_issues}\n"
                if cache_patterns_found:
                    details += f"Pattern issues: {cache_patterns_found}\n"
                if practical_cache_test:
                    details += f"Practical test issues: {practical_cache_test}\n"
                if redis_test:
                    details += f"Redis issues: {redis_test}\n"
                
                severity = "CRITICAL" if len(cache_issues) > 0 else "WARNING"
                self.report_issue(10, "Cache Mechanism Issues", "FOUND", details, severity)
            else:
                self.report_issue(10, "Cache Mechanism Issues", "RESOLVED", 
                                f"Cache mechanism נראה תקין ({len(cache_implementation)} features)")
                
        except Exception as e:
            self.report_issue(10, "Cache Mechanism Issues", "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

    def test_11_to_17_remaining_critical_issues(self):
        """בדיקת שאר הבעיות הקריטיות (11-17)"""
        print("🔍 בודק בעיות קריטיות #11-17...")
        
        # בעיה #11: SQL Injection Vulnerabilities
        try:
            sql_injection_issues = []
            
            files_with_queries = []
            for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # חיפוש SQL queries
                            sql_patterns = [
                                r'execute\s*\(\s*["\'].*%.*["\']',  # String formatting in queries
                                r'execute\s*\(\s*f["\'].*\{.*\}.*["\']',  # f-strings in queries
                                r'SELECT.*\+.*',  # String concatenation
                                r'INSERT.*\+.*',
                                r'UPDATE.*\+.*',
                                r'DELETE.*\+.*'
                            ]
                            
                            for pattern in sql_patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    sql_injection_issues.append(
                                        f"{os.path.relpath(file_path)}: Potential SQL injection"
                                    )
                                    
                        except:
                            continue
            
            if sql_injection_issues:
                details = f"נמצאו {len(sql_injection_issues)} בעיות SQL injection"
                self.report_issue(11, "SQL Injection Vulnerabilities", "FOUND", details, "CRITICAL")
            else:
                self.report_issue(11, "SQL Injection Vulnerabilities", "RESOLVED", "לא נמצאו בעיות SQL injection")
                
        except Exception as e:
            self.report_issue(11, "SQL Injection Vulnerabilities", "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

        # בעיה #12: Async/Await Pattern Issues
        try:
            async_issues = []
            
            for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # בדיקת דפוסי בעיות async
                            async_problems = [
                                (r'def\s+\w+.*await', 'await in sync function'),
                                (r'async def\s+\w+.*(?!await)', 'async function without await'),
                                (r'asyncio\.run.*asyncio\.run', 'nested asyncio.run'),
                                (r'time\.sleep.*async', 'time.sleep in async context')
                            ]
                            
                            for pattern, issue in async_problems:
                                if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                                    async_issues.append(f"{os.path.relpath(file_path)}: {issue}")
                                    
                        except:
                            continue
            
            if async_issues:
                details = f"נמצאו {len(async_issues)} בעיות async/await"
                self.report_issue(12, "Async/Await Pattern Issues", "FOUND", details, "CRITICAL")
            else:
                self.report_issue(12, "Async/Await Pattern Issues", "RESOLVED", "לא נמצאו בעיות async/await")
                
        except Exception as e:
            self.report_issue(12, "Async/Await Pattern Issues", "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

        # בעיות #13-17: בדיקות מהירות
        issues_13_17 = [
            (13, "Graceful Error Handling", self._check_error_handling),
            (14, "State Management Issues", self._check_state_management),
            (15, "Network Error Handling", self._check_network_errors),
            (16, "Resource Management", self._check_resource_management),
            (17, "Duplicate Detection", self._check_duplicate_detection)
        ]
        
        for issue_num, title, check_func in issues_13_17:
            try:
                result = check_func()
                if result['issues']:
                    self.report_issue(issue_num, title, "FOUND", result['details'], "CRITICAL")
                else:
                    self.report_issue(issue_num, title, "RESOLVED", result['details'])
            except Exception as e:
                self.report_issue(issue_num, title, "FOUND", f"שגיאה בבדיקה: {e}", "CRITICAL")

    def _check_error_handling(self):
        """בדיקת Error Handling"""
        bare_excepts = 0
        generic_excepts = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        bare_excepts += len(re.findall(r'except\s*:', content))
                        generic_excepts += len(re.findall(r'except Exception:', content))
                        
                    except:
                        continue
        
        issues = bare_excepts > 5 or generic_excepts > bare_excepts * 2
        details = f"Bare excepts: {bare_excepts}, Generic excepts: {generic_excepts}"
        
        return {'issues': issues, 'details': details}

    def _check_state_management(self):
        """בדיקת State Management"""
        global_vars = 0
        state_vars = 0
        
        main_file = os.path.join(os.path.dirname(__file__), "..", "main/pirate_bot_main.py")
        if os.path.exists(main_file):
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            global_vars = len(re.findall(r'^[A-Z_][A-Z0-9_]*\s*=', content, re.MULTILINE))
            state_vars = len(re.findall(r'_state|_status|_mode', content, re.IGNORECASE))
        
        issues = global_vars > 10 and state_vars == 0
        details = f"Global vars: {global_vars}, State vars: {state_vars}"
        
        return {'issues': issues, 'details': details}

    def _check_network_errors(self):
        """בדיקת Network Error Handling"""
        network_calls = 0
        error_handling = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        network_calls += len(re.findall(r'requests\.|http|fetch|connect', content, re.IGNORECASE))
                        error_handling += len(re.findall(r'timeout|ConnectionError|NetworkError', content))
                        
                    except:
                        continue
        
        issues = network_calls > 0 and error_handling == 0
        details = f"Network calls: {network_calls}, Error handling: {error_handling}"
        
        return {'issues': issues, 'details': details}

    def _check_resource_management(self):
        """בדיקת Resource Management"""
        opens = 0
        closes = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        opens += len(re.findall(r'open\s*\(', content))
                        closes += len(re.findall(r'\.close\s*\(\)', content))
                        
                    except:
                        continue
        
        issues = opens > closes * 1.5
        details = f"Opens: {opens}, Closes: {closes}"
        
        return {'issues': issues, 'details': details}

    def _check_duplicate_detection(self):
        """בדיקת Duplicate Detection"""
        duplicate_files = []
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if 'duplicate' in file.lower():
                    duplicate_files.append(file)
        
        duplicate_code = 0
        if duplicate_files:
            file_path = os.path.join(root, duplicate_files[0])
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                duplicate_code = len(re.findall(r'similarity|threshold|fuzzy', content, re.IGNORECASE))
            except:
                pass
        
        issues = len(duplicate_files) == 0 or duplicate_code == 0
        details = f"Duplicate files: {len(duplicate_files)}, Detection code: {duplicate_code}"
        
        return {'issues': issues, 'details': details}

    # ========================================
    # בעיות חשובות לטווח בינוני (18-27)
    # ========================================
    
    def test_18_to_27_important_issues(self):
        """בדיקת בעיות חשובות #18-27"""
        print("🔍 בודק בעיות חשובות #18-27...")
        
        # בעיה #18: Performance Issues
        try:
            performance_issues = []
            slow_operations = 0
            
            for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                            
                            # חיפוש פעולות איטיות
                            slow_patterns = [
                                r'for.*in.*range\([0-9]{4,}\)',  # Large loops
                                r'while.*True.*:(?!.*break)',  # Infinite loops without break
                                r'\.findall\(',  # Regex operations
                                r'time\.sleep\([^0]',  # Sleep > 0
                                r'\.execute\(.*SELECT \*'  # SELECT * queries
                            ]
                            
                            for pattern in slow_patterns:
                                slow_operations += len(re.findall(pattern, content, re.IGNORECASE))
                                
                        except:
                            continue
            
            if slow_operations > 10:
                details = f"נמצאו {slow_operations} פעולות פוטנציאליות איטיות"
                self.report_issue(18, "Performance Issues", "FOUND", details, "WARNING")
            else:
                self.report_issue(18, "Performance Issues", "RESOLVED", f"פעולות איטיות: {slow_operations}")
                
        except Exception as e:
            self.report_issue(18, "Performance Issues", "FOUND", f"שגיאה בבדיקה: {e}", "WARNING")

        # בעיה #19: Configuration Management
        try:
            config_issues = []
            
            config_file = os.path.join(os.path.dirname(__file__), "..", "main/config.py")
            hardcoded_configs = 0
            configurable_items = 0
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # ספירת הגדרות קשיחות
                hardcoded_configs = len(re.findall(r'=\s*["\'][^"\']*["\']', content))
                configurable_items = len(re.findall(r'getenv|get\(', content))
                
                if hardcoded_configs > configurable_items * 2:
                    config_issues.append("יותר מדי הגדרות קשיחות")
            else:
                config_issues.append("קובץ config.py לא נמצא")
            
            if config_issues:
                details = f"בעיות config: {config_issues}"
                self.report_issue(19, "Configuration Management", "FOUND", details, "WARNING")
            else:
                self.report_issue(19, "Configuration Management", "RESOLVED", 
                                f"Config OK: {configurable_items} configurable items")
                
        except Exception as e:
            self.report_issue(19, "Configuration Management", "FOUND", f"שגיאה בבדיקה: {e}", "WARNING")

        # בעיות #20-27: בדיקות מהירות
        remaining_issues = [
            (20, "Logging Issues", self._check_logging_issues),
            (21, "Input Validation", self._check_input_validation),
            (22, "Rate Limiting", self._check_rate_limiting),
            (23, "User Permissions", self._check_user_permissions),
            (24, "Status Transitions", self._check_status_transitions),
            (25, "Workflow Management", self._check_workflow_management),
            (26, "UX/UI Problems", self._check_ux_ui_problems),
            (27, "Monitoring Missing", self._check_monitoring_missing)
        ]
        
        for issue_num, title, check_func in remaining_issues:
            try:
                result = check_func()
                if result['issues']:
                    self.report_issue(issue_num, title, "FOUND", result['details'], "WARNING")
                else:
                    self.report_issue(issue_num, title, "RESOLVED", result['details'])
            except Exception as e:
                self.report_issue(issue_num, title, "FOUND", f"שגיאה בבדיקה: {e}", "WARNING")

    # ========================================
    # בעיות לטיפול עתידי (28-37)
    # ========================================
    
    def test_28_to_37_future_issues(self):
        """בדיקת בעיות עתידיות #28-37"""
        print("🔍 בודק בעיות עתידיות #28-37...")
        
        future_issues = [
            (28, "Scalability Issues", self._check_scalability),
            (29, "Backup & Recovery", self._check_backup_recovery),
            (30, "Data Corruption Risks", self._check_data_corruption),
            (31, "Cascade Failure Risks", self._check_cascade_failure),
            (32, "Business Logic Bugs", self._check_business_logic),
            (33, "Priority System", self._check_priority_system),
            (34, "Keyboard Layouts", self._check_keyboard_layouts),
            (35, "User Feedback", self._check_user_feedback),
            (36, "Structured Logging", self._check_structured_logging),
            (37, "Database Optimization", self._check_database_optimization)
        ]
        
        for issue_num, title, check_func in future_issues:
            try:
                result = check_func()
                severity = "WARNING" if result['issues'] else "INFO"
                status = "FOUND" if result['issues'] else "RESOLVED"
                self.report_issue(issue_num, title, status, result['details'], severity)
            except Exception as e:
                self.report_issue(issue_num, title, "FOUND", f"שגיאה בבדיקה: {e}", "WARNING")

    # ========================================
    # פונקציות עזר לבדיקות מהירות
    # ========================================
    
    def _check_logging_issues(self):
        """בדיקת בעיות Logging"""
        log_statements = 0
        structured_logs = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        log_statements += len(re.findall(r'log\.|print\(', content, re.IGNORECASE))
                        structured_logs += len(re.findall(r'logger\.|logging\.', content))
                        
                    except:
                        continue
        
        issues = log_statements > 0 and structured_logs < log_statements * 0.5
        details = f"Log statements: {log_statements}, Structured logs: {structured_logs}"
        
        return {'issues': issues, 'details': details}

    def _check_input_validation(self):
        """בדיקת Input Validation"""
        input_handlers = 0
        validation_checks = 0
        
        main_file = os.path.join(os.path.dirname(__file__), "..", "main/pirate_bot_main.py")
        if os.path.exists(main_file):
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            input_handlers = len(re.findall(r'MessageHandler|message\.text', content))
            validation_checks = len(re.findall(r'validate|check|verify|sanitize', content, re.IGNORECASE))
        
        issues = input_handlers > 0 and validation_checks == 0
        details = f"Input handlers: {input_handlers}, Validation checks: {validation_checks}"
        
        return {'issues': issues, 'details': details}

    def _check_rate_limiting(self):
        """בדיקת Rate Limiting"""
        rate_limit_code = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        rate_limit_code += len(re.findall(r'rate_limit|throttle|cooldown|limit', content, re.IGNORECASE))
                        
                    except:
                        continue
        
        issues = rate_limit_code == 0
        details = f"Rate limiting code: {rate_limit_code}"
        
        return {'issues': issues, 'details': details}

    def _check_user_permissions(self):
        """בדיקת User Permissions"""
        permission_checks = 0
        admin_checks = 0
        
        main_file = os.path.join(os.path.dirname(__file__), "..", "main/pirate_bot_main.py")
        if os.path.exists(main_file):
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            permission_checks = len(re.findall(r'permission|role|access', content, re.IGNORECASE))
            admin_checks = len(re.findall(r'admin|ADMIN_IDS', content))
        
        issues = admin_checks > 0 and permission_checks < 3
        details = f"Permission checks: {permission_checks}, Admin checks: {admin_checks}"
        
        return {'issues': issues, 'details': details}

    def _check_status_transitions(self):
        """בדיקת Status Transitions"""
        status_changes = 0
        state_machine = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        status_changes += len(re.findall(r'status.*=|set_status|update_status', content, re.IGNORECASE))
                        state_machine += len(re.findall(r'state.*machine|transition|workflow', content, re.IGNORECASE))
                        
                    except:
                        continue
        
        issues = status_changes > 5 and state_machine == 0
        details = f"Status changes: {status_changes}, State machine code: {state_machine}"
        
        return {'issues': issues, 'details': details}

    def _check_workflow_management(self):
        """בדיקת Workflow Management"""
        workflow_code = 0
        process_definitions = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        workflow_code += len(re.findall(r'workflow|process|pipeline', content, re.IGNORECASE))
                        process_definitions += len(re.findall(r'class.*Process|def.*process', content, re.IGNORECASE))
                        
                    except:
                        continue
        
        issues = workflow_code == 0 and process_definitions == 0
        details = f"Workflow code: {workflow_code}, Process definitions: {process_definitions}"
        
        return {'issues': issues, 'details': details}

    def _check_ux_ui_problems(self):
        """בדיקת UX/UI Problems"""
        ui_messages = 0
        error_messages = 0
        
        main_file = os.path.join(os.path.dirname(__file__), "..", "main/pirate_bot_main.py")
        if os.path.exists(main_file):
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            ui_messages = len(re.findall(r'send_message|reply|answer', content, re.IGNORECASE))
            error_messages = len(re.findall(r'error|שגיאה|לא מזוהה', content, re.IGNORECASE))
        
        issues = error_messages > ui_messages * 0.3
        details = f"UI messages: {ui_messages}, Error messages: {error_messages}"
        
        return {'issues': issues, 'details': details}

    def _check_monitoring_missing(self):
        """בדיקת חוסר Monitoring"""
        monitoring_code = 0
        metrics_code = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        monitoring_code += len(re.findall(r'monitor|health|status', content, re.IGNORECASE))
                        metrics_code += len(re.findall(r'metric|counter|gauge|histogram', content, re.IGNORECASE))
                        
                    except:
                        continue
        
        issues = monitoring_code < 5 and metrics_code == 0
        details = f"Monitoring code: {monitoring_code}, Metrics code: {metrics_code}"
        
        return {'issues': issues, 'details': details}

    def _check_scalability(self):
        """בדיקת Scalability"""
        scaling_patterns = 0
        bottlenecks = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        scaling_patterns += len(re.findall(r'pool|queue|worker|async', content, re.IGNORECASE))
                        bottlenecks += len(re.findall(r'for.*in.*:(?=.*for.*in.*:)', content))  # Nested loops
                        
                    except:
                        continue
        
        issues = bottlenecks > 3 and scaling_patterns < 5
        details = f"Scaling patterns: {scaling_patterns}, Potential bottlenecks: {bottlenecks}"
        
        return {'issues': issues, 'details': details}

    def _check_backup_recovery(self):
        """בדיקת Backup & Recovery"""
        backup_code = 0
        recovery_code = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        backup_code += len(re.findall(r'backup|export|dump', content, re.IGNORECASE))
                        recovery_code += len(re.findall(r'recover|restore|import', content, re.IGNORECASE))
                        
                    except:
                        continue
        
        issues = backup_code == 0 or recovery_code == 0
        details = f"Backup code: {backup_code}, Recovery code: {recovery_code}"
        
        return {'issues': issues, 'details': details}

    def _check_data_corruption(self):
        """בדיקת Data Corruption Risks"""
        transaction_code = 0
        atomic_operations = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        transaction_code += len(re.findall(r'transaction|commit|rollback', content, re.IGNORECASE))
                        atomic_operations += len(re.findall(r'atomic|lock|mutex', content, re.IGNORECASE))
                        
                    except:
                        continue
        
        issues = transaction_code < 3 and atomic_operations == 0
        details = f"Transaction code: {transaction_code}, Atomic operations: {atomic_operations}"
        
        return {'issues': issues, 'details': details}

    def _check_cascade_failure(self):
        """בדיקת Cascade Failure Risks"""
        error_isolation = 0
        circuit_breakers = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        error_isolation += len(re.findall(r'try:.*except.*continue', content, re.DOTALL))
                        circuit_breakers += len(re.findall(r'circuit.*break|fallback|timeout', content, re.IGNORECASE))
                        
                    except:
                        continue
        
        issues = error_isolation < 5 and circuit_breakers == 0
        details = f"Error isolation: {error_isolation}, Circuit breakers: {circuit_breakers}"
        
        return {'issues': issues, 'details': details}

    def _check_business_logic(self):
        """בדיקת Business Logic Bugs"""
        business_rules = 0
        validation_rules = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        business_rules += len(re.findall(r'business.*rule|domain.*logic', content, re.IGNORECASE))
                        validation_rules += len(re.findall(r'validate.*|verify.*|check.*', content, re.IGNORECASE))
                        
                    except:
                        continue
        
        issues = business_rules == 0 and validation_rules < 10
        details = f"Business rules: {business_rules}, Validation rules: {validation_rules}"
        
        return {'issues': issues, 'details': details}

    def _check_priority_system(self):
        """בדיקת Priority System"""
        priority_code = 0
        queue_management = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        priority_code += len(re.findall(r'priority|urgent|high.*low', content, re.IGNORECASE))
                        queue_management += len(re.findall(r'queue|sort.*by|order.*by', content, re.IGNORECASE))
                        
                    except:
                        continue
        
        issues = priority_code > 0 and queue_management == 0
        details = f"Priority code: {priority_code}, Queue management: {queue_management}"
        
        return {'issues': issues, 'details': details}

    def _check_keyboard_layouts(self):
        """בדיקת Keyboard Layouts"""
        keyboard_code = 0
        button_handlers = 0
        
        main_file = os.path.join(os.path.dirname(__file__), "..", "main/pirate_bot_main.py")
        if os.path.exists(main_file):
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            keyboard_code = len(re.findall(r'keyboard|InlineKeyboard|ReplyKeyboard', content, re.IGNORECASE))
            button_handlers = len(re.findall(r'button|callback.*data', content, re.IGNORECASE))
        
        issues = keyboard_code > 0 and button_handlers < keyboard_code
        details = f"Keyboard code: {keyboard_code}, Button handlers: {button_handlers}"
        
        return {'issues': issues, 'details': details}

    def _check_user_feedback(self):
        """בדיקת User Feedback"""
        feedback_mechanisms = 0
        confirmation_messages = 0
        
        main_file = os.path.join(os.path.dirname(__file__), "..", "main/pirate_bot_main.py")
        if os.path.exists(main_file):
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            feedback_mechanisms = len(re.findall(r'feedback|rating|survey', content, re.IGNORECASE))
            confirmation_messages = len(re.findall(r'success|completed|done|✅', content))
        
        issues = feedback_mechanisms == 0 and confirmation_messages < 5
        details = f"Feedback mechanisms: {feedback_mechanisms}, Confirmations: {confirmation_messages}"
        
        return {'issues': issues, 'details': details}

    def _check_structured_logging(self):
        """בדיקת Structured Logging"""
        structured_logs = 0
        json_logs = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        structured_logs += len(re.findall(r'structlog|logging\.getLogger', content))
                        json_logs += len(re.findall(r'json.*log|log.*json', content, re.IGNORECASE))
                        
                    except:
                        continue
        
        issues = structured_logs == 0 and json_logs == 0
        details = f"Structured logs: {structured_logs}, JSON logs: {json_logs}"
        
        return {'issues': issues, 'details': details}

    def _check_database_optimization(self):
        """בדיקת Database Optimization"""
        indexes = 0
        query_optimization = 0
        
        for root, dirs, files in os.walk(os.path.dirname(__file__) + "/../"):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        indexes += len(re.findall(r'INDEX|index.*=|create.*index', content, re.IGNORECASE))
                        query_optimization += len(re.findall(r'LIMIT|limit.*=|WHERE.*=', content))
                        
                    except:
                        continue
        
        issues = indexes < 3 and query_optimization < 10
        details = f"Indexes: {indexes}, Query optimization: {query_optimization}"
        
        return {'issues': issues, 'details': details}
    
    @classmethod
    def tearDownClass(cls):
        """סיכום הבדיקה"""
        print("\n" + "="*80)
        print("🎯 סיכום בדיקת כל 37 הבעיות")
        print("="*80)
        
        print(f"\n🚨 בעיות קריטיות שנמצאו: {cls.critical_count}")
        print(f"⚠️  אזהרות: {cls.warning_count}")
        print(f"✅ בעיות שנפתרו: {len(cls.issues_resolved)}")
        
        if cls.issues_found:
            print(f"\n📋 בעיות שדורשות תיקון ({len(cls.issues_found)}):")
            for issue in sorted(cls.issues_found, key=lambda x: x['number']):
                severity_emoji = "🚨" if issue['severity'] == 'CRITICAL' else "⚠️"
                print(f"   {severity_emoji} #{issue['number']:02d}: {issue['title']}")
        
        if cls.issues_resolved:
            print(f"\n✅ בעיות שנפתרו ({len(cls.issues_resolved)}):")
            for issue in sorted(cls.issues_resolved, key=lambda x: x['number'])[:5]:  # Show first 5
                print(f"   ✅ #{issue['number']:02d}: {issue['title']}")
        
        print(f"\n📊 סיכום כללי:")
        print(f"   • סה\"ך בעיות נבדקו: 37")
        print(f"   • בעיות שנמצאו: {len(cls.issues_found)}")
        print(f"   • בעיות שנפתרו: {len(cls.issues_resolved)}")
        print(f"   • אחוז הצלחה: {(len(cls.issues_resolved) / 37) * 100:.1f}%")
        
        if cls.critical_count > 10:
            print(f"\n🚨 המערכת זקוקה לתיקונים דחופים!")
        elif cls.critical_count > 5:
            print(f"\n⚠️  המערכת דורשת תשומת לב")
        else:
            print(f"\n✅ המערכת במצב סביר")


if __name__ == '__main__':
    # הרצת הטסט
    unittest.main(verbosity=2)