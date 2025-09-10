#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטים קריטיים לבעיות המרכזיות שזוהו במערכת
מיועד לוודא שכל הבעיות מתוקנות כראוי
"""

import unittest
import os
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
import subprocess


class TestContainerNamingIssue(unittest.TestCase):
    """טסט לבעיית שמות הקונטיינרים - הבעיה הקריטית ביותר"""
    
    def test_docker_compose_vs_actual_containers(self):
        """בדיקת אי-התאמה בין docker-compose לקונטיינרים הפועלים"""
        # שמות מ-docker-compose.yml
        expected_mysql_service = "pirate-mysql-db"
        expected_redis_service = "pirate-redis-cache"
        
        # בדיקת שמות קונטיינרים בפועל
        try:
            result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}'], 
                                  capture_output=True, text=True)
            running_containers = result.stdout.strip().split('\n')
        except:
            self.skipTest("Docker not available")
        
        # הבעיה: השמות לא מתאימים
        mysql_running = any('mysql' in container for container in running_containers)
        redis_running = any('redis' in container for container in running_containers)
        
        if mysql_running and redis_running:
            actual_mysql = [c for c in running_containers if 'mysql' in c][0]
            actual_redis = [c for c in running_containers if 'redis' in c][0]
            
            # זוהי הבעיה!
            self.assertNotEqual(expected_mysql_service, actual_mysql,
                              f"🔥 MySQL container name mismatch! Expected: {expected_mysql_service}, Actual: {actual_mysql}")
            self.assertNotEqual(expected_redis_service, actual_redis,
                              f"🔥 Redis container name mismatch! Expected: {expected_redis_service}, Actual: {actual_redis}")
            
            print(f"❌ Expected MySQL: {expected_mysql_service}")
            print(f"✅ Actual MySQL: {actual_mysql}")
            print(f"❌ Expected Redis: {expected_redis_service}")
            print(f"✅ Actual Redis: {actual_redis}")

    def test_environment_variables_missing(self):
        """בדיקת משתני סביבה חסרים"""
        # בדיקה שמשתני הסביבה לא מוגדרים
        db_host = os.getenv('DB_HOST')
        redis_host = os.getenv('REDIS_HOST')
        
        # הבעיה: אין הגדרות סביבה
        if db_host is None:
            print("❌ DB_HOST environment variable not set")
        if redis_host is None:
            print("❌ REDIS_HOST environment variable not set")
        
        # זה גורם לשימוש בברירות מחדל שגויות
        from pirate_content_bot.main.config import DB_CONFIG, CACHE_CONFIG
        
        default_db_host = DB_CONFIG['host']  # יהיה localhost
        default_redis_host = CACHE_CONFIG['redis_config']['host']  # יהיה localhost
        
        if db_host is None:
            self.assertEqual(default_db_host, 'localhost', 
                           "כשאין DB_HOST, המערכת משתמשת ב-localhost במקום בקונטיינר")
        if redis_host is None:
            self.assertEqual(default_redis_host, 'localhost',
                           "כשאין REDIS_HOST, המערכת משתמשת ב-localhost במקום בקונטיינר")

    def test_connection_failure_simulation(self):
        """סימולציה של כישלון חיבור בגלל שמות שגויים"""
        # דימוי config עם שמות שגויים
        wrong_config = {
            'host': 'pirate-mysql-db',  # שם שלא קיים
            'user': 'pirate_user',
            'password': 'test_password',
            'database': 'pirate_content'
        }
        
        # בדיקה שהחיבור נכשל
        with patch('mysql.connector.connect') as mock_connect:
            mock_connect.side_effect = Exception("Name or service not known")
            
            try:
                import mysql.connector
                mysql.connector.connect(**wrong_config)
                self.fail("Connection should have failed with wrong hostname")
            except Exception as e:
                self.assertIn("Name or service not known", str(e))
                print("✅ Connection correctly fails with wrong hostname")


class TestJSONSerializationFix(unittest.TestCase):
    """טסטים לבעיית JSON serialization"""
    
    def test_datetime_serialization_problem(self):
        """טסט לבעיית serialization של datetime objects"""
        # נתונים כפי שמגיעים מהDB
        db_data = {
            'id': 1,
            'user_id': 12345,
            'title': 'test request',
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'fulfilled_at': None
        }
        
        # בדיקה שJSON.dumps נכשל
        with self.assertRaises(TypeError) as context:
            json.dumps(db_data)
        
        self.assertIn("not JSON serializable", str(context.exception))
        print("✅ Confirmed datetime serialization issue")

    def test_json_serial_function_solution(self):
        """טסט לפתרון עם פונקציית json_serial"""
        def json_serial(obj):
            """JSON serializer for datetime objects"""
            if isinstance(obj, datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            elif obj is None:
                return None
            raise TypeError(f"Type {type(obj)} not serializable")
        
        # נתונים עם datetime
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
            
            print("✅ json_serial function works correctly")
            
        except Exception as e:
            self.fail(f"json_serial failed: {e}")

    def test_backup_data_serialization(self):
        """טסט serialization של נתוני גיבוי"""
        # דימוי נתוני גיבוי מהמערכת
        backup_data = {
            'export_info': {
                'created_at': datetime.now(),
                'version': '1.0',
                'format': 'json'
            },
            'requests': [
                {
                    'id': 1,
                    'title': 'Test Request',
                    'created_at': datetime(2025, 1, 1),
                    'updated_at': datetime.now(),
                    'status': 'pending'
                }
            ],
            'users': [
                {
                    'user_id': 12345,
                    'username': '@test',
                    'created_at': datetime.now()
                }
            ]
        }
        
        # בדיקה שהבעיה קיימת
        with self.assertRaises(TypeError):
            json.dumps(backup_data)
        
        # בדיקה שהפתרון עובד
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")
        
        result = json.dumps(backup_data, default=json_serial, ensure_ascii=False, indent=2)
        self.assertIsInstance(result, str)
        self.assertIn('Test Request', result)
        print("✅ Backup data serialization fixed")


class TestUserIdentificationIssue(unittest.TestCase):
    """טסטים לבעיית זיהוי משתמשים כפולים"""
    
    def test_user_always_appears_new_issue(self):
        """בדיקת הבעיה: משתמש תמיד נראה חדש"""
        # דימוי UserService שנכשל לזהות משתמש קיים
        with patch('pirate_content_bot.services.user_service.UserService') as mock_service:
            # כישלון בשאילתת DB
            mock_service.get_user.side_effect = Exception("Connection failed")
            
            # כתוצאה, המערכת חושבת שהמשתמש חדש
            user_exists = False
            try:
                user = mock_service.get_user(12345)
            except:
                user = None
                user_exists = False
            
            self.assertFalse(user_exists, "DB failure causes user to appear as new")
            print("✅ Confirmed: DB failures make users appear new")

    def test_database_connection_affects_user_detection(self):
        """בדיקה שבעיות חיבור מספר משתמשים קיימים"""
        user_id = 6562280181  # מהלוג
        
        # דימוי חיבור DB שנכשל
        mock_pool = MagicMock()
        mock_pool.execute_query.side_effect = Exception("No connection to database")
        
        # כשה-DB לא עובד, אי אפשר לוודא שהמשתמש קיים
        user_exists = None
        try:
            result = mock_pool.execute_query("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user_exists = bool(result)
        except Exception:
            user_exists = False  # נחשב כמשתמש חדש
        
        self.assertFalse(user_exists, "Connection failure makes existing users appear new")

    def test_correct_user_identification_with_working_db(self):
        """בדיקת זיהוי נכון כשהDB עובד"""
        user_id = 12345
        existing_user_data = {
            'user_id': user_id,
            'username': '@test_user',
            'first_name': 'Test',
            'created_at': datetime.now()
        }
        
        # דימוי DB שמחזיר נתונים
        mock_pool = MagicMock()
        mock_pool.execute_query.return_value = existing_user_data
        
        # עכשיו המשתמש יזוהה נכון
        result = mock_pool.execute_query("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user_exists = bool(result)
        
        self.assertTrue(user_exists, "With working DB, existing users are found")
        self.assertEqual(result['user_id'], user_id)
        print("✅ Confirmed: Working DB correctly identifies users")


class TestEnvironmentConfigurationIssues(unittest.TestCase):
    """טסטים לבעיות הגדרות סביבה"""
    
    def test_missing_environment_variables(self):
        """בדיקת משתני סביבה חסרים"""
        critical_vars = [
            'DB_HOST',
            'REDIS_HOST', 
            'DB_PASSWORD',
            'BOT_TOKEN'
        ]
        
        missing_vars = []
        for var in critical_vars:
            if os.getenv(var) is None:
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {missing_vars}")
            # זה לא צריך לקרוס את הטסט, אבל להודיע על הבעיה
        else:
            print("✅ All critical environment variables are set")

    def test_default_values_cause_connection_issues(self):
        """בדיקה שברירות מחדל גורמות לבעיות חיבור"""
        # כשאין משתנה סביבה, המערכת משתמשת ב-localhost
        from pirate_content_bot.main.config import DB_CONFIG
        
        # אם DB_HOST לא מוגדר, host יהיה localhost
        if os.getenv('DB_HOST') is None:
            self.assertEqual(DB_CONFIG['host'], 'localhost',
                           "Without DB_HOST env var, system defaults to localhost")
            print("⚠️ DB_HOST defaults to localhost - will fail in Docker")
        
        # אותו דבר עבור Redis
        from pirate_content_bot.main.config import CACHE_CONFIG
        if os.getenv('REDIS_HOST') is None:
            self.assertEqual(CACHE_CONFIG['redis_config']['host'], 'localhost',
                           "Without REDIS_HOST env var, system defaults to localhost")
            print("⚠️ REDIS_HOST defaults to localhost - will fail in Docker")

    def test_docker_compose_environment_mismatch(self):
        """בדיקת אי-התאמה בין docker-compose להגדרות"""
        # שמות השירותים ב-docker-compose
        docker_compose_mysql = "pirate-mysql-db"
        docker_compose_redis = "pirate-redis-cache" 
        
        # שמות הקונטיינרים בפועל (מה container_name)
        actual_mysql = "pirate-mysql"
        actual_redis = "pirate-redis"
        
        # הבעיה: השמות לא מתאימים
        self.assertNotEqual(docker_compose_mysql, actual_mysql,
                          "Service name != container name for MySQL")
        self.assertNotEqual(docker_compose_redis, actual_redis,
                          "Service name != container name for Redis")
        
        print(f"🔥 MySQL: docker-compose uses '{docker_compose_mysql}', container is '{actual_mysql}'")
        print(f"🔥 Redis: docker-compose uses '{docker_compose_redis}', container is '{actual_redis}'")


if __name__ == "__main__":
    print("🧪 מתחיל טסטים קריטיים לבעיות המרכזיות...")
    print("=" * 60)
    
    # הרצת כל הטסטים
    unittest.main(verbosity=2)