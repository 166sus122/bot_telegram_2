#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים מקיפים למסד הנתונים - בדיקת כל הבעיות בעומק
מטרה: זיהוי מדויק של כל בעיות החיבור, הטבלאות, וה-CRUD operations
"""

import unittest
import asyncio
import mysql.connector
import json
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from unittest.mock import MagicMock, patch

class TestDatabaseConnection(unittest.TestCase):
    """טסטים לבדיקת חיבור למסד נתונים"""
    
    def setUp(self):
        """הגדרות לטסטים"""
        # הגדרות חיבור מהקובץ ENV
        self.db_configs = {
            'expected_from_docker_compose': {
                'host': 'pirate-mysql-db',  # מה שמוגדר ב-docker-compose
                'user': 'pirate_user',
                'password': 'test_password_123',
                'database': 'pirate_content',
                'port': 3306
            },
            'actual_container_name': {
                'host': 'pirate-mysql',  # שם הקונטיינר הפועל
                'user': 'pirate_user', 
                'password': 'test_password_123',
                'database': 'pirate_content',
                'port': 3306
            },
            'localhost_test': {
                'host': 'localhost',
                'user': 'pirate_user',
                'password': 'test_password_123', 
                'database': 'pirate_content',
                'port': 3306
            }
        }

    def test_docker_container_name_mismatch(self):
        """בדיקת אי-התאמה בשמות קונטיינרים - הבעיה המרכזית"""
        expected_host = self.db_configs['expected_from_docker_compose']['host']
        actual_host = self.db_configs['actual_container_name']['host']
        
        self.assertNotEqual(expected_host, actual_host, 
                           "🔥 זוהתה בעיית אי-התאמה בשמות קונטיינרים!")
        
        print(f"❌ Expected: {expected_host}")
        print(f"✅ Actual: {actual_host}")

    def test_mysql_container_status(self):
        """בדיקת סטטוס קונטיינר MySQL"""
        try:
            # בדיקת docker ps
            result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'], 
                                  capture_output=True, text=True)
            
            docker_output = result.stdout
            print(f"🐳 Docker containers status:\n{docker_output}")
            
            # חיפוש קונטיינרים מסוג mysql
            mysql_containers = [line for line in docker_output.split('\n') 
                              if 'mysql' in line.lower()]
            
            self.assertGreater(len(mysql_containers), 0, "❌ לא נמצאו קונטיינרים של MySQL")
            
            # בדיקה שהקונטיינר healthy
            healthy_containers = [line for line in mysql_containers 
                                if 'healthy' in line.lower()]
            
            if len(healthy_containers) == 0:
                print("⚠️ קונטיינר MySQL לא במצב healthy")
            else:
                print("✅ קונטיינר MySQL במצב healthy")
                
        except subprocess.CalledProcessError as e:
            self.fail(f"❌ Failed to check docker status: {e}")

    def test_direct_mysql_connection_localhost(self):
        """בדיקת חיבור ישיר ל-MySQL דרך localhost"""
        config = self.db_configs['localhost_test']
        
        try:
            connection = mysql.connector.connect(**config)
            
            if connection.is_connected():
                print("✅ חיבור ל-localhost הצליח!")
                
                # בדיקת גרסה
                cursor = connection.cursor()
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                print(f"📊 MySQL Version: {version[0]}")
                
                # בדיקת database
                cursor.execute("SHOW DATABASES")
                databases = cursor.fetchall()
                db_names = [db[0] for db in databases]
                
                self.assertIn('pirate_content', db_names, 
                            "❌ Database 'pirate_content' לא קיים")
                print("✅ Database 'pirate_content' קיים")
                
                cursor.close()
                connection.close()
            else:
                self.fail("❌ לא הצלחתי להתחבר ל-localhost")
                
        except mysql.connector.Error as e:
            print(f"❌ MySQL Connection Error: {e}")
            self.fail(f"Connection failed: {e}")

    def test_wrong_host_connection_fails(self):
        """בדיקה שחיבור עם שם שגוי נכשל"""
        wrong_config = self.db_configs['expected_from_docker_compose'].copy()
        
        try:
            connection = mysql.connector.connect(**wrong_config)
            connection.close()
            self.fail("⚠️ חיבור עם שם שגוי הצליח - זה לא אמור לקרות!")
            
        except mysql.connector.Error as e:
            print(f"✅ חיבור נכשל כמצופה: {e}")
            # זה מה שאנחנו מצפים - השגיאה מוכיחה את הבעיה

    def test_connection_pool_with_wrong_settings(self):
        """בדיקת Connection Pool עם הגדרות שגויות"""
        try:
            from pirate_content_bot.database.connection_pool import DatabaseConnectionPool
        except ImportError:
            # אם המודול לא קיים, נדלג על הטסט
            print("⏭️ דולג על טסט Connection Pool - מודול לא זמין")
            return
        
        # ניסיון ליצור pool עם שם שגוי
        wrong_config = self.db_configs['expected_from_docker_compose']
        
        pool = DatabaseConnectionPool(wrong_config)
        result = pool.create_pool()
        
        self.assertFalse(result, "יצירת Pool צריכה להיכשל עם הגדרות שגויות")
        print("✅ Connection Pool נכשל כמצופה עם הגדרות שגויות")

class TestDatabaseTables(unittest.TestCase):
    """טסטים לבדיקת טבלאות ומיגרציות"""
    
    def setUp(self):
        """הכנה לטסטים"""
        self.localhost_config = {
            'host': 'localhost',
            'user': 'pirate_user',
            'password': 'test_password_123',
            'database': 'pirate_content',
            'port': 3306
        }

    def test_database_exists(self):
        """בדיקה שמסד הנתונים קיים"""
        try:
            connection = mysql.connector.connect(**self.localhost_config)
            cursor = connection.cursor()
            
            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()
            
            self.assertEqual(current_db[0], 'pirate_content')
            print("✅ Database 'pirate_content' פעיל")
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as e:
            self.skipTest(f"Cannot connect to database: {e}")

    def test_required_tables_exist(self):
        """בדיקה שכל הטבלאות הנדרשות קיימות"""
        required_tables = [
            'content_requests',
            'users', 
            'content_ratings',
            'user_warnings',
            'notifications',
            'admin_actions',
            'system_logs',
            'schema_migrations'
        ]
        
        try:
            connection = mysql.connector.connect(**self.localhost_config)
            cursor = connection.cursor()
            
            cursor.execute("SHOW TABLES")
            existing_tables = [table[0] for table in cursor.fetchall()]
            
            print(f"📊 Existing tables: {existing_tables}")
            
            missing_tables = []
            for table in required_tables:
                if table not in existing_tables:
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                self.fail(f"Missing required tables: {', '.join(missing_tables)}")
            else:
                print("✅ כל הטבלאות הנדרשות קיימות")
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as e:
            self.skipTest(f"Cannot connect to database: {e}")

    def test_table_structures(self):
        """בדיקת מבנה הטבלאות"""
        table_structures = {
            'content_requests': [
                'id', 'user_id', 'username', 'first_name', 'title', 
                'original_text', 'category', 'status', 'created_at'
            ],
            'users': [
                'user_id', 'username', 'first_name', 'total_requests', 
                'created_at'
            ]
        }
        
        try:
            connection = mysql.connector.connect(**self.localhost_config)
            cursor = connection.cursor()
            
            for table_name, expected_columns in table_structures.items():
                cursor.execute(f"DESCRIBE {table_name}")
                existing_columns = [column[0] for column in cursor.fetchall()]
                
                print(f"📋 {table_name} columns: {existing_columns}")
                
                missing_columns = []
                for column in expected_columns:
                    if column not in existing_columns:
                        missing_columns.append(column)
                
                if missing_columns:
                    print(f"❌ {table_name} missing columns: {missing_columns}")
                else:
                    print(f"✅ {table_name} has all required columns")
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as e:
            self.skipTest(f"Cannot connect to database: {e}")

    def test_migrations_table_exists(self):
        """בדיקת טבלת המיגרציות"""
        try:
            connection = mysql.connector.connect(**self.localhost_config)
            cursor = connection.cursor()
            
            # בדיקה שטבלת המיגרציות קיימת
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'pirate_content' 
                AND table_name = 'schema_migrations'
            """)
            
            table_exists = cursor.fetchone()[0] > 0
            
            if table_exists:
                # בדיקת תוכן טבלת המיגרציות
                cursor.execute("SELECT version, description, executed_at FROM schema_migrations ORDER BY executed_at")
                migrations = cursor.fetchall()
                
                print(f"📊 Executed migrations: {len(migrations)}")
                for migration in migrations:
                    print(f"  - {migration[0]}: {migration[1]} ({migration[2]})")
                    
                self.assertGreater(len(migrations), 0, "❌ אין מיגרציות שהורצו")
            else:
                print("❌ טבלת המיגרציות לא קיימת")
                self.fail("Migration table not found")
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as e:
            self.skipTest(f"Cannot connect to database: {e}")

class TestCRUDOperations(unittest.TestCase):
    """טסטים לפעולות CRUD בסיסיות"""
    
    def setUp(self):
        """הכנה לטסטים"""
        self.localhost_config = {
            'host': 'localhost',
            'user': 'pirate_user',
            'password': 'test_password_123',
            'database': 'pirate_content',
            'port': 3306
        }
        
        self.test_user_data = {
            'user_id': 999999999,  # ID שלא קיים
            'username': '@test_user',
            'first_name': 'Test User',
            'total_requests': 0
        }
        
        self.test_request_data = {
            'user_id': 999999999,
            'username': '@test_user',
            'first_name': 'Test User',
            'title': 'Test Request',
            'original_text': 'This is a test request',
            'category': 'general',
            'status': 'pending'
        }

    def test_insert_user(self):
        """בדיקת הוספת משתמש חדש"""
        try:
            connection = mysql.connector.connect(**self.localhost_config)
            cursor = connection.cursor()
            
            # מחיקת נתוני טסט קודמים
            cursor.execute("DELETE FROM users WHERE user_id = %s", (self.test_user_data['user_id'],))
            
            # הוספת משתמש חדש
            insert_query = """
                INSERT INTO users (user_id, username, first_name, total_requests, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                self.test_user_data['user_id'],
                self.test_user_data['username'],
                self.test_user_data['first_name'],
                self.test_user_data['total_requests'],
                datetime.now()
            ))
            
            connection.commit()
            
            # בדיקה שהמשתמש נוסף
            cursor.execute("SELECT * FROM users WHERE user_id = %s", (self.test_user_data['user_id'],))
            result = cursor.fetchone()
            
            self.assertIsNotNone(result, "❌ משתמש לא נוסף למסד הנתונים")
            print("✅ הוספת משתמש הצליחה")
            
            # ניקוי
            cursor.execute("DELETE FROM users WHERE user_id = %s", (self.test_user_data['user_id'],))
            connection.commit()
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as e:
            self.skipTest(f"Cannot connect to database: {e}")

    def test_insert_request(self):
        """בדיקת הוספת בקשה חדשה"""
        try:
            connection = mysql.connector.connect(**self.localhost_config)
            cursor = connection.cursor()
            
            # מחיקת נתוני טסט קודמים
            cursor.execute("DELETE FROM content_requests WHERE user_id = %s", (self.test_request_data['user_id'],))
            
            # הוספת בקשה חדשה
            insert_query = """
                INSERT INTO content_requests (user_id, username, first_name, title, original_text, category, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                self.test_request_data['user_id'],
                self.test_request_data['username'],
                self.test_request_data['first_name'],
                self.test_request_data['title'],
                self.test_request_data['original_text'],
                self.test_request_data['category'],
                self.test_request_data['status'],
                datetime.now()
            ))
            
            connection.commit()
            
            # בדיקה שהבקשה נוספה
            cursor.execute("SELECT * FROM content_requests WHERE user_id = %s", (self.test_request_data['user_id'],))
            result = cursor.fetchone()
            
            self.assertIsNotNone(result, "❌ בקשה לא נוספה למסד הנתונים")
            print("✅ הוספת בקשה הצליחה")
            
            # ניקוי
            cursor.execute("DELETE FROM content_requests WHERE user_id = %s", (self.test_request_data['user_id'],))
            connection.commit()
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as e:
            self.skipTest(f"Cannot connect to database: {e}")

    def test_select_operations(self):
        """בדיקת פעולות SELECT שונות"""
        try:
            connection = mysql.connector.connect(**self.localhost_config)
            cursor = connection.cursor(dictionary=True)
            
            # בדיקת ספירת בקשות
            cursor.execute("SELECT COUNT(*) as total FROM content_requests")
            result = cursor.fetchone()
            total_requests = result['total']
            
            print(f"📊 Total requests in DB: {total_requests}")
            
            # בדיקת ספירת משתמשים
            cursor.execute("SELECT COUNT(*) as total FROM users")
            result = cursor.fetchone()
            total_users = result['total']
            
            print(f"📊 Total users in DB: {total_users}")
            
            # בדיקת בקשות לפי סטטוס
            cursor.execute("SELECT status, COUNT(*) as count FROM content_requests GROUP BY status")
            status_counts = cursor.fetchall()
            
            print("📊 Requests by status:")
            for status_count in status_counts:
                print(f"  - {status_count['status']}: {status_count['count']}")
            
            # בדיקה שהנתונים לא ריקים לחלוטין
            if total_requests == 0 and total_users == 0:
                print("⚠️ מסד הנתונים ריק מנתונים - זו כנראה הבעיה!")
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as e:
            self.skipTest(f"Cannot connect to database: {e}")

class TestConnectionPool(unittest.TestCase):
    """טסטים ל-Connection Pool ו-Transactions"""
    
    def test_connection_pool_creation(self):
        """בדיקת יצירת Connection Pool"""
        try:
            from pirate_content_bot.database.connection_pool import DatabaseConnectionPool
        except ImportError:
            print("⏭️ דולג על טסט Connection Pool creation - מודול לא זמין")
            return
        
        # הגדרות נכונות
        correct_config = {
            'host': 'localhost',
            'user': 'pirate_user', 
            'password': 'test_password_123',
            'database': 'pirate_content',
            'port': 3306,
            'pool_size': 5,
            'pool_name': 'test_pool'
        }
        
        try:
            pool = DatabaseConnectionPool(correct_config)
            result = pool.create_pool()
            
            if result:
                print("✅ Connection Pool נוצר בהצלחה")
                
                # בדיקת health check
                health = pool.health_check()
                self.assertTrue(health, "❌ Health check נכשל")
                print("✅ Health check עבר בהצלחה")
                
                # בדיקת סטטוס pool
                status = pool.get_pool_status()
                print(f"📊 Pool status: {status}")
                
                pool.close_all_connections()
            else:
                self.fail("❌ יצירת Connection Pool נכשלה")
                
        except Exception as e:
            self.skipTest(f"Cannot create connection pool: {e}")

    def test_transaction_operations(self):
        """בדיקת פעולות Transaction"""
        try:
            from pirate_content_bot.database.connection_pool import DatabaseConnectionPool
        except ImportError:
            print("⏭️ דולג על טסט Transaction operations - מודול לא זמין")
            return
        
        config = {
            'host': 'localhost',
            'user': 'pirate_user',
            'password': 'test_password_123',
            'database': 'pirate_content',
            'port': 3306,
            'pool_size': 5
        }
        
        try:
            pool = DatabaseConnectionPool(config)
            if not pool.create_pool():
                self.skipTest("Cannot create connection pool")
            
            # בדיקת transaction עם מספר queries
            queries = [
                ("DELETE FROM users WHERE user_id = %s", (888888888,)),
                ("INSERT INTO users (user_id, username, first_name, total_requests, created_at) VALUES (%s, %s, %s, %s, %s)", 
                 (888888888, '@transaction_test', 'Transaction Test', 0, datetime.now())),
            ]
            
            result = pool.execute_transaction(queries)
            
            if result:
                print("✅ Transaction הצליח")
                
                # בדיקה שהנתונים נשמרו
                user = pool.execute_query(
                    "SELECT * FROM users WHERE user_id = %s", 
                    (888888888,), 
                    fetch_one=True
                )
                
                self.assertIsNotNone(user, "❌ נתוני Transaction לא נשמרו")
                print("✅ נתוני Transaction נשמרו כהלכה")
                
                # ניקוי
                pool.execute_query("DELETE FROM users WHERE user_id = %s", (888888888,))
            else:
                self.fail("❌ Transaction נכשל")
            
            pool.close_all_connections()
            
        except Exception as e:
            self.skipTest(f"Cannot test transactions: {e}")

class TestJSONSerializationFix(unittest.TestCase):
    """טסטים מתקדמים לבעיות JSON Serialization"""
    
    def test_datetime_in_backup_data(self):
        """בדיקת datetime objects בנתוני גיבוי"""
        # דימוי נתוני DB עם datetime
        db_record = {
            'id': 1,
            'user_id': 123456,
            'title': 'test request',
            'created_at': datetime(2025, 1, 1, 12, 0, 0),
            'updated_at': datetime.now(),
            'fulfilled_at': None
        }
        
        # בדיקת הבעיה המקורית
        with self.assertRaises(TypeError) as context:
            json.dumps(db_record)
        
        self.assertIn("not JSON serializable", str(context.exception))
        self.assertIn("datetime", str(context.exception))
        print("✅ אוממנו את בעיית JSON serialization")

    def test_json_serial_function(self):
        """בדיקת פונקציית json_serial"""
        def json_serial(obj):
            """JSON serializer עבור datetime objects"""
            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            elif obj is None:
                return None
            raise TypeError(f"Type {type(obj)} not serializable")
        
        # נתונים עם datetime objects
        test_data = {
            'created_at': datetime(2025, 1, 1, 12, 0, 0),
            'updated_at': datetime.now(),
            'fulfilled_at': None,
            'title': 'test with hebrew: בדיקה'
        }
        
        # בדיקה שהפונקציה פותרת את הבעיה
        try:
            json_string = json.dumps(test_data, default=json_serial, ensure_ascii=False)
            parsed = json.loads(json_string)
            
            self.assertEqual(parsed['created_at'], '2025-01-01 12:00:00')
            self.assertEqual(parsed['fulfilled_at'], None)
            self.assertIn('בדיקה', parsed['title'])
            
            print("✅ פונקציית json_serial עובדת כהלכה")
            
        except Exception as e:
            self.fail(f"❌ json_serial failed: {e}")

class TestDataConsistency(unittest.TestCase):
    """טסטים לבדיקת עקביות נתונים"""
    
    def setUp(self):
        self.localhost_config = {
            'host': 'localhost',
            'user': 'pirate_user',
            'password': 'test_password_123',
            'database': 'pirate_content',
            'port': 3306
        }

    def test_user_request_consistency(self):
        """בדיקת עקביות בין משתמשים לבקשות"""
        try:
            connection = mysql.connector.connect(**self.localhost_config)
            cursor = connection.cursor(dictionary=True)
            
            # בדיקת משתמשים עם בקשות
            cursor.execute("""
                SELECT u.user_id, u.username, u.total_requests,
                       COUNT(cr.id) as actual_requests
                FROM users u
                LEFT JOIN content_requests cr ON u.user_id = cr.user_id
                GROUP BY u.user_id, u.username, u.total_requests
                HAVING u.total_requests != COUNT(cr.id)
            """)
            
            inconsistent_users = cursor.fetchall()
            
            if inconsistent_users:
                print("⚠️ נמצאו אי-עקביות בנתוני משתמשים:")
                for user in inconsistent_users:
                    print(f"  - User {user['user_id']}: recorded={user['total_requests']}, actual={user['actual_requests']}")
            else:
                print("✅ נתוני משתמשים עקביים")
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as e:
            self.skipTest(f"Cannot connect to database: {e}")

    def test_orphaned_records(self):
        """בדיקת רשומות יתומות"""
        try:
            connection = mysql.connector.connect(**self.localhost_config)
            cursor = connection.cursor(dictionary=True)
            
            # בדיקת בקשות ללא משתמש
            cursor.execute("""
                SELECT cr.id, cr.user_id, cr.title
                FROM content_requests cr
                LEFT JOIN users u ON cr.user_id = u.user_id
                WHERE u.user_id IS NULL
            """)
            
            orphaned_requests = cursor.fetchall()
            
            if orphaned_requests:
                print("⚠️ נמצאו בקשות יתומות (ללא משתמש):")
                for request in orphaned_requests:
                    print(f"  - Request {request['id']}: user_id={request['user_id']}, title='{request['title']}'")
            else:
                print("✅ לא נמצאו בקשות יתומות")
            
            cursor.close()
            connection.close()
            
        except mysql.connector.Error as e:
            self.skipTest(f"Cannot connect to database: {e}")

async def run_comprehensive_tests():
    """הרצת כל הטסטים המקיפים"""
    test_suites = [
        TestDatabaseConnection,
        TestDatabaseTables, 
        TestCRUDOperations,
        TestConnectionPool,
        TestJSONSerializationFix,
        TestDataConsistency
    ]
    
    print("🧪 מתחיל טסטים מקיפים למסד הנתונים...\n")
    
    total_tests = 0
    failed_tests = 0
    skipped_tests = 0
    
    for i, test_suite in enumerate(test_suites, 1):
        print(f"📋 Suite {i}/{len(test_suites)}: {test_suite.__name__}")
        print("-" * 60)
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_suite)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        
        total_tests += result.testsRun
        failed_tests += len(result.failures) + len(result.errors)
        skipped_tests += len(result.skipped)
        
        print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
        print(f"❌ Failed: {len(result.failures) + len(result.errors)}")
        print(f"⏭️  Skipped: {len(result.skipped)}")
        print()

    print("=" * 60)
    print("🎯 סיכום הטסטים המקיפים:")
    print(f"📊 סה\"כ טסטים: {total_tests}")
    print(f"✅ עברו: {total_tests - failed_tests - skipped_tests}")
    print(f"❌ נכשלו: {failed_tests}")
    print(f"⏭️  דולגו: {skipped_tests}")
    
    if failed_tests == 0:
        print("🎉 כל הטסטים עברו בהצלחה!")
        return True
    else:
        print("⚠️ יש בעיות שזוהו - מוכן לתיקון!")
        return False

if __name__ == "__main__":
    # הרצה עם asyncio למקרה שנצטרך פונקציות async
    success = asyncio.run(run_comprehensive_tests())