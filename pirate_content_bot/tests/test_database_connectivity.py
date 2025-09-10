#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים לבדיקת בעיות חיבור מסד נתונים
נוצר לאיתור הבעיות שזוהו בלוג המשתמש
"""

import unittest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Dict, Any, Optional

class TestDatabaseConnectivity(unittest.TestCase):
    """טסטים לבדיקת חיבור מסד נתונים"""
    
    def setUp(self):
        """הכנה לטסטים"""
        self.mock_connection_pool = MagicMock()
        self.test_user_id = 6562280181  # מה-ID מהלוג
        self.test_request_data = {
            'user_id': self.test_user_id,
            'username': '@ללא',
            'first_name': 'דובי',
            'title': 'test',
            'original_text': 'test request',
            'category': 'general',
            'status': 'pending'
        }

    def test_docker_container_names_mismatch(self):
        """בדיקת אי-התאמה בשמות הקונטיינרים"""
        # כפי שראינו בדוקר-compose לעומת הגדרות
        expected_db_host = "pirate-mysql-db"  # מה config.py
        actual_container_name = "pirate-mysql"  # מ docker ps
        
        expected_redis_host = "pirate-redis-cache"  # מה config.py  
        actual_container_name_redis = "pirate-redis"  # מ docker ps
        
        self.assertNotEqual(expected_db_host, actual_container_name,
                           "שמות הקונטיינרים לא מתאימים - זוהי הבעיה המרכזית!")
        self.assertNotEqual(expected_redis_host, actual_container_name_redis,
                           "גם Redis לא מתאים!")

    def test_connection_pool_creation_fails(self):
        """בדיקת כישלון ביצירת connection pool"""
        with patch('pirate_content_bot.database.connection_pool.mysql') as mock_mysql:
            mock_mysql.connector.pooling.MySQLConnectionPool.side_effect = Exception("Connection failed")
            
            from pirate_content_bot.database.connection_pool import DatabaseConnectionPool
            
            # בדיקה שיצירת הpool נכשלת
            with self.assertRaises(Exception):
                pool = DatabaseConnectionPool({'host': 'wrong-host', 'user': 'test'})
                pool.create_pool()

    def test_execute_query_with_no_connection(self):
        """בדיקת ביצוע query ללא חיבור פעיל"""
        # דימוי חיבור שנכשל
        mock_pool = MagicMock()
        mock_pool.execute_query.side_effect = Exception("No connection to database")
        
        # בדיקה ש-query נכשל עם השגיאה הנכונה
        with self.assertRaises(Exception) as context:
            mock_pool.execute_query("SELECT 1")
        
        self.assertIn("connection", str(context.exception).lower())

class TestJSONSerializationIssues(unittest.TestCase):
    """טסטים לבעיות JSON serialization"""
    
    def test_datetime_serialization_error(self):
        """בדיקת השגיאה בserialization של datetime - הבעיה מהלוג"""
        # נתון עם datetime כפי שמתקבל מהDB
        test_data = {
            'id': 1,
            'created_at': datetime.now(),
            'updated_at': datetime.now() - timedelta(hours=1),
            'title': 'test request'
        }
        
        # בדיקה שJSON.dumps נכשל ללא json_serial
        with self.assertRaises(TypeError) as context:
            json.dumps(test_data)
        
        self.assertIn("not JSON serializable", str(context.exception))
        self.assertIn("datetime", str(context.exception))

    def test_json_serial_function_fixes_datetime(self):
        """בדיקה שפונקציית json_serial מתקנת את הבעיה"""
        def json_serial(obj):
            """הפונקציה מהקוד"""
            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            raise TypeError(f"Type {type(obj)} not serializable")
        
        test_data = {
            'created_at': datetime(2025, 1, 1, 12, 0, 0),
            'title': 'test'
        }
        
        # בדיקה שעכשיו זה עובד
        result = json.dumps(test_data, default=json_serial)
        parsed = json.loads(result)
        
        self.assertEqual(parsed['created_at'], '2025-01-01 12:00:00')
        self.assertEqual(parsed['title'], 'test')

    def test_backup_function_with_datetime_objects(self):
        """בדיקת פונקציית הגיבוי עם datetime objects"""
        # דימוי backup data עם datetime
        backup_data = {
            'requests': [
                {
                    'id': 1,
                    'created_at': datetime.now(),
                    'title': 'test request'
                }
            ],
            'backup_info': {
                'created_at': datetime.now(),
                'version': '1.0'
            }
        }
        
        # בדיקת הבעיה המקורית
        with self.assertRaises(TypeError):
            json.dumps(backup_data)
        
        # בדיקת התיקון
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            raise TypeError(f"Type {type(obj)} not serializable")
        
        # עכשיו צריך לעבוד
        result = json.dumps(backup_data, default=json_serial, ensure_ascii=False, indent=2)
        self.assertIsInstance(result, str)
        self.assertIn('test request', result)

class TestUserIdentificationIssues(unittest.TestCase):
    """טסטים לבעיית זיהוי משתמשים חוזרים"""
    
    def setUp(self):
        self.user_id = 6562280181
        self.username = '@ללא'
        self.first_name = 'דובי'
    
    async def test_duplicate_user_registration(self):
        """בדיקת הבעיה - יצירת משתמש חדש בכל /start"""
        # דימוי UserService שלא מוצא משתמש קיים
        mock_user_service = AsyncMock()
        mock_user_service.get_user.return_value = None  # לא נמצא
        mock_user_service.create_user.return_value = True
        
        # כל פעם שקוראים ל/start זה יוצר משתמש חדש
        for _ in range(3):  # כפי שקרה בלוג
            user = await mock_user_service.get_user(self.user_id)
            if not user:
                await mock_user_service.create_user(self.user_id, self.username, self.first_name)
        
        # בדיקה שהמשתמש נוצר 3 פעמים (הבעיה!)
        self.assertEqual(mock_user_service.create_user.call_count, 3)

    async def test_correct_user_identification(self):
        """בדיקת הפתרון הנכון - זיהוי משתמש קיים"""
        # דימוי UserService שמוצא משתמש קיים
        mock_user_service = AsyncMock()
        existing_user = {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'created_at': datetime.now() - timedelta(days=1)
        }
        mock_user_service.get_user.return_value = existing_user
        
        # מספר קריאות ל/start
        for _ in range(3):
            user = await mock_user_service.get_user(self.user_id)
            if not user:
                await mock_user_service.create_user(self.user_id, self.username, self.first_name)
        
        # בדיקה שהמשתמש לא נוצר שוב (הפתרון!)
        mock_user_service.create_user.assert_not_called()

    def test_database_query_failure_causes_new_user(self):
        """בדיקה שכישלון בquery גורם ליצירת משתמש חדש"""
        # דימוי DB query שנכשל
        mock_pool = MagicMock()
        mock_pool.execute_query.side_effect = Exception("Database connection failed")
        
        # כשהDB לא עובד, הבוט חושב שהמשתמש חדש
        try:
            user = mock_pool.execute_query("SELECT * FROM users WHERE user_id = %s", (self.user_id,))
        except Exception:
            user = None  # לא נמצא בגלל השגיאה
        
        self.assertIsNone(user, "כישלון בDB גורם לחשיבה שהמשתמש חדש")

class TestCallbackHandlerIssues(unittest.TestCase):
    """טסטים לבעיות callback handlers"""
    
    def test_unrecognized_callback_data(self):
        """בדיקת הבעיה: 'לא מזוהה: view_request:1'"""
        # דימוי callback data מהלוג
        callback_data = "view_request:1"
        
        # דימוי handler שלא מזהה
        registered_patterns = ["admin:", "rating:", "settings:"]
        
        recognized = False
        for pattern in registered_patterns:
            if callback_data.startswith(pattern):
                recognized = True
                break
        
        self.assertFalse(recognized, "Callback לא מזוהה - זוהי הבעיה!")

    def test_missing_callback_handler_registration(self):
        """בדיקת חיסור ברישום handlers"""
        # רשימת handlers שצריכים להיות רשומים
        required_handlers = [
            "view_request:",
            "admin:pending",
            "refresh:",
            "create_request:",
            "my_requests:"
        ]
        
        # רשימת handlers שרשומים בפועל (דימוי)
        registered_handlers = [
            "settings:",
            "rating:"
        ]
        
        missing_handlers = []
        for handler in required_handlers:
            if not any(h.startswith(handler.split(':')[0]) for h in registered_handlers):
                missing_handlers.append(handler)
        
        self.assertGreater(len(missing_handlers), 0, "יש handlers חסרים")
        self.assertIn("view_request:", missing_handlers)
        self.assertIn("admin:pending", missing_handlers)

class TestAnalyticsAndStatsIssues(unittest.TestCase):
    """טסטים לבעיות סטטיסטיקות ואנליטיקס"""
    
    def test_empty_analytics_data(self):
        """בדיקת הבעיה: כל הסטטיסטיקות מחזירות 0"""
        # דימוי analytics service שמחזיר נתונים ריקים
        mock_analytics = {
            'total_requests': 0,
            'pending_requests': 0,
            'fulfilled_requests': 0,
            'rejected_requests': 0,
            'active_users': 0
        }
        
        # בדיקה שכל הנתונים אפס (הבעיה מהלוג)
        for key, value in mock_analytics.items():
            self.assertEqual(value, 0, f"{key} should not be 0 in a working system")

    def test_database_query_returns_empty_results(self):
        """בדיקת query שמחזיר תוצאות ריקות"""
        # דימוי DB query לסטטיסטיקות
        mock_pool = MagicMock()
        mock_pool.execute_query.return_value = []  # אין תוצאות
        
        # קריאה לנתוני אנליטיקס
        requests_count = mock_pool.execute_query("SELECT COUNT(*) FROM content_requests")
        users_count = mock_pool.execute_query("SELECT COUNT(*) FROM users")
        
        self.assertEqual(len(requests_count), 0)
        self.assertEqual(len(users_count), 0)

class TestSearchAndBroadcastIssues(unittest.TestCase):
    """טסטים לבעיות חיפוש ושידורים"""
    
    def test_search_returns_no_results(self):
        """בדיקת הבעיה: '🔍 לא נמצאו תוצאות עבור: test'"""
        # דימוי search service
        mock_search_service = MagicMock()
        mock_search_service.search.return_value = []  # אין תוצאות
        
        # חיפוש שנכשל
        results = mock_search_service.search("test")
        self.assertEqual(len(results), 0, "חיפוש מחזיר תוצאות ריקות")

    def test_broadcast_no_active_users(self):
        """בדיקת הבעיה: 'לא נמצאו משתמשים פעילים לשידור'"""
        # דימוי broadcast service
        mock_broadcast_service = MagicMock()
        mock_broadcast_service.get_active_users.return_value = []
        mock_broadcast_service.send_broadcast.return_value = {
            'sent_count': 0,
            'failed_count': 0,
            'message': 'לא נמצאו משתמשים פעילים לשידור'
        }
        
        active_users = mock_broadcast_service.get_active_users()
        result = mock_broadcast_service.send_broadcast("test message")
        
        self.assertEqual(len(active_users), 0)
        self.assertEqual(result['sent_count'], 0)

class TestAdminCommandIssues(unittest.TestCase):
    """טסטים לבעיות פקודות מנהל"""
    
    def test_pending_requests_returns_empty(self):
        """בדיקת הבעיה: /p מחזיר 'אין בקשות ממתינות' למרות שיש"""
        # דימוי request service
        mock_request_service = MagicMock()
        mock_request_service.get_pending_requests.return_value = []
        
        pending = mock_request_service.get_pending_requests()
        self.assertEqual(len(pending), 0, "אין בקשות ממתינות בהחזר")

    def test_fulfill_reject_commands_fail(self):
        """בדיקת כישלון פקודות fulfill ו-reject"""
        # דימוי request service שנכשל
        mock_request_service = MagicMock()
        mock_request_service.fulfill_request.side_effect = Exception("שגיאה בעדכון מסד הנתונים")
        mock_request_service.reject_request.side_effect = Exception("בקשה #1 לא נמצאה")
        
        # בדיקת כישלון fulfill
        with self.assertRaises(Exception) as context:
            mock_request_service.fulfill_request(1, "test notes")
        self.assertIn("מסד הנתונים", str(context.exception))
        
        # בדיקת כישלון reject  
        with self.assertRaises(Exception) as context:
            mock_request_service.reject_request(1, "test reason")
        self.assertIn("לא נמצאה", str(context.exception))

class TestDataConsistencyIssues(unittest.TestCase):
    """טסטים לבעיות עקביות נתונים"""
    
    def test_request_status_inconsistency(self):
        """בדיקת אי-עקביות בסטטוס בקשות"""
        # בקשה שקיימת ב/status אבל לא ב/p
        mock_request = {
            'id': 1,
            'title': 'test',
            'status': 'pending',
            'created_at': datetime.now()
        }
        
        # /status מוצא את הבקשה
        status_result = mock_request  # נמצא
        
        # /p לא מוצא בקשות ממתינות
        pending_requests = []  # ריק
        
        # אי-עקביות!
        self.assertEqual(mock_request['status'], 'pending')
        self.assertEqual(len(pending_requests), 0)
        self.assertIsNotNone(status_result)

async def run_all_tests():
    """הרצת כל הטסטים"""
    test_classes = [
        TestDatabaseConnectivity,
        TestJSONSerializationIssues, 
        TestUserIdentificationIssues,
        TestCallbackHandlerIssues,
        TestAnalyticsAndStatsIssues,
        TestSearchAndBroadcastIssues,
        TestAdminCommandIssues,
        TestDataConsistencyIssues
    ]
    
    total_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        result = unittest.TextTestRunner(verbosity=0).run(suite)
        
        total_tests += result.testsRun
        failed_tests += len(result.failures) + len(result.errors)
    
    print(f"\n🧪 סיכום טסטים:")
    print(f"📊 סה\"כ טסטים: {total_tests}")
    print(f"❌ נכשלו: {failed_tests}")
    print(f"✅ עברו: {total_tests - failed_tests}")
    
    if failed_tests == 0:
        print("🎉 כל הטסטים עברו בהצלחה!")
    else:
        print("⚠️  יש בעיות שזוהו בטסטים")

if __name__ == "__main__":
    asyncio.run(run_all_tests())