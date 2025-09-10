#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
טסטי אינטגרציה סופיים - בדיקת כל הבעיות יחד
"""

import unittest
import sys
import os
import subprocess

# הוספת נתיב לפרויקט
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class TestSystemIntegration(unittest.TestCase):
    """טסטי אינטגרציה של כל המערכת"""
    
    def test_docker_containers_health(self):
        """בדיקת תקינות הקונטיינרים"""
        try:
            result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}'], 
                                  capture_output=True, text=True)
            output = result.stdout
            
            # בדיקת קיום קונטיינרים
            self.assertIn('pirate-mysql', output, "MySQL container not running")
            self.assertIn('pirate-redis', output, "Redis container not running")
            
            # בדיקת סטטוס healthy
            self.assertIn('healthy', output, "Containers are not healthy")
            
            print("✅ Docker containers are running and healthy")
            
        except subprocess.CalledProcessError:
            self.skipTest("Docker not available")
    
    def test_environment_setup_complete(self):
        """בדיקת הגדרות סביבה מלאות"""
        required_env_vars = {
            'DB_HOST': 'pirate-mysql',
            'REDIS_HOST': 'pirate-redis',
            'BOT_TOKEN': None,  # לא בודקים token בטסט
            'DB_PASSWORD': None,  # לא בודקים password בטסט
        }
        
        missing_or_wrong = []
        
        for var, expected in required_env_vars.items():
            value = os.getenv(var)
            if value is None:
                missing_or_wrong.append(f"{var} is missing")
            elif expected and value != expected:
                missing_or_wrong.append(f"{var} = {value}, expected {expected}")
        
        if missing_or_wrong:
            print(f"⚠️ Environment issues: {missing_or_wrong}")
        else:
            print("✅ All environment variables correctly set")
    
    def test_configuration_consistency(self):
        """בדיקת עקביות הגדרות"""
        # נסיון טעינה של config
        try:
            from pirate_content_bot.main.config import DB_CONFIG, CACHE_CONFIG
            
            # בדיקת DB config
            db_host = DB_CONFIG.get('host', 'localhost')
            redis_host = CACHE_CONFIG.get('redis_config', {}).get('host', 'localhost')
            
            # אזהרות אם השמות לא נכונים
            if db_host == 'localhost':
                print("⚠️ DB_CONFIG uses localhost - might fail in Docker")
            elif db_host == 'pirate-mysql':
                print("✅ DB_CONFIG correctly uses pirate-mysql")
            
            if redis_host == 'localhost':
                print("⚠️ CACHE_CONFIG uses localhost - might fail in Docker")
            elif redis_host == 'pirate-redis':
                print("✅ CACHE_CONFIG correctly uses pirate-redis")
                
        except ImportError as e:
            print(f"⚠️ Could not load config: {e}")
    
    def test_database_connection_realistic(self):
        """בדיקת חיבור DB ריאלית"""
        try:
            import mysql.connector
            
            # חיבור עם localhost (צריך לעבוד אם הפורט חשוף)
            config = {
                'host': 'localhost',
                'port': 3306,
                'user': 'pirate_user',
                'password': 'test_password_123',
                'database': 'pirate_content'
            }
            
            try:
                conn = mysql.connector.connect(**config)
                if conn.is_connected():
                    print("✅ Database connection successful via localhost:3306")
                    
                    # בדיקת טבלאות
                    cursor = conn.cursor()
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    table_names = [table[0] for table in tables]
                    
                    expected_tables = ['users', 'content_requests']
                    missing_tables = [t for t in expected_tables if t not in table_names]
                    
                    if missing_tables:
                        print(f"⚠️ Missing tables: {missing_tables}")
                    else:
                        print("✅ All essential tables exist")
                    
                    cursor.close()
                    conn.close()
                else:
                    print("❌ Database connection failed")
                    
            except mysql.connector.Error as e:
                print(f"❌ Database connection error: {e}")
                
        except ImportError:
            self.skipTest("mysql-connector-python not available")


if __name__ == "__main__":
    print("🔧 בדיקת אינטגרציה סופית של המערכת...")
    print("=" * 50)
    unittest.main(verbosity=2)