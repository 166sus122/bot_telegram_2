#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏴‍☠️ בוט התמימים הפיראטים - מבחנים כוללים
Comprehensive test suite for the pirate content bot functionality
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# הוספת נתיב הפרויקט ל-PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ייבוא המודולים של הבוט
try:
    from pirate_content_bot.services.request_service import RequestService
    from pirate_content_bot.services.user_service import UserService
    from pirate_content_bot.main.config import THREAD_IDS
    print("✅ Successfully imported bot modules")
except ImportError as e:
    print(f"❌ Failed to import bot modules: {e}")
    sys.exit(1)

class BotTester:
    """בודק כללי לפונקציונליות הבוט"""
    
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.passed_tests = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """רישום תוצאת מבחן"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if success:
            self.passed_tests.append(test_name)
            print(f"✅ {test_name} - PASSED")
        else:
            self.failed_tests.append(test_name)
            print(f"❌ {test_name} - FAILED: {details}")
        
        if details:
            print(f"   💡 Details: {details}")
    
    async def test_config_validation(self):
        """מבחן קונפיגורציה והגדרות"""
        print("\n🔧 Testing Configuration...")
        
        # בדיקת Thread IDs
        try:
            assert isinstance(THREAD_IDS, dict), "THREAD_IDS should be a dictionary"
            
            expected_categories = [
                'updates', 'series', 'software', 'books', 
                'movies', 'spotify', 'games', 'apps', 'general'
            ]
            
            missing_categories = [cat for cat in expected_categories if cat not in THREAD_IDS]
            assert not missing_categories, f"Missing categories: {missing_categories}"
            
            # בדיקה שיש Thread IDs חוקיים
            valid_threads = [tid for tid in THREAD_IDS.values() if tid is not None and isinstance(tid, int)]
            assert len(valid_threads) >= 8, f"Should have at least 8 valid thread IDs, got {len(valid_threads)}"
            
            self.log_test("Config - Thread IDs", True, f"Found {len(THREAD_IDS)} categories with {len(valid_threads)} valid thread IDs")
            
        except Exception as e:
            self.log_test("Config - Thread IDs", False, str(e))
    
    async def test_request_service_basic(self):
        """מבחנים בסיסיים לשירות הבקשות"""
        print("\n📋 Testing Request Service...")
        
        # יצירת שירות בקשות (ללא חיבור למסד נתונים)
        try:
            request_service = RequestService(
                storage_manager=None,  # Test without database
                content_analyzer=None,
                duplicate_detector=None,
                notification_callback=None
            )
            
            self.log_test("RequestService - Initialization", True, "Service created without database connection")
            
            # בדיקת פונקציות analytics עם cache
            start_date = datetime.now() - timedelta(days=7)
            
            # Test analytics methods
            try:
                priority_dist = await request_service._get_priority_distribution(start_date)
                assert isinstance(priority_dist, list), "Priority distribution should return a list"
                self.log_test("RequestService - Priority Distribution", True, f"Returned {len(priority_dist)} priority entries")
            except Exception as e:
                self.log_test("RequestService - Priority Distribution", False, str(e))
            
            try:
                response_times = await request_service._get_average_response_times(start_date)
                assert isinstance(response_times, dict), "Response times should return a dict"
                
                expected_keys = ['avg_fulfillment_hours', 'avg_rejection_hours', 'fastest_response_hours', 'slowest_response_hours']
                missing_keys = [key for key in expected_keys if key not in response_times]
                assert not missing_keys, f"Missing response time keys: {missing_keys}"
                
                self.log_test("RequestService - Response Times", True, "All expected response time metrics present")
            except Exception as e:
                self.log_test("RequestService - Response Times", False, str(e))
            
            try:
                top_users = await request_service._get_top_users(start_date, limit=5)
                assert isinstance(top_users, list), "Top users should return a list"
                self.log_test("RequestService - Top Users", True, f"Returned {len(top_users)} top users")
            except Exception as e:
                self.log_test("RequestService - Top Users", False, str(e))
            
        except Exception as e:
            self.log_test("RequestService - Initialization", False, str(e))
    
    async def test_cache_functionality(self):
        """מבחנים לפונקציונליות המטמון"""
        print("\n💾 Testing Cache Functionality...")
        
        try:
            request_service = RequestService(
                storage_manager=None,
                content_analyzer=None,
                duplicate_detector=None,
                notification_callback=None
            )
            
            # הוספת נתונים למטמון
            test_request = {
                'id': 999,
                'user_id': 123456789,
                'title': 'Test Request for Cache',
                'content': 'This is a test request for cache functionality',
                'category': 'software',
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # הוספה למטמון
            request_service._request_cache[999] = test_request
            
            # בדיקה שהנתונים נשמרו
            cached_request = request_service._request_cache.get(999)
            assert cached_request is not None, "Request should be saved in cache"
            assert cached_request['title'] == test_request['title'], "Cached data should match input"
            
            # בדיקת חישוב response times מהמטמון
            start_date = datetime.now() - timedelta(days=1)
            
            # הוספת בקשה שהושלמה למטמון
            completed_request = test_request.copy()
            completed_request['id'] = 1000
            completed_request['status'] = 'fulfilled'
            completed_request['updated_at'] = (datetime.now() + timedelta(hours=2)).isoformat()
            request_service._request_cache[1000] = completed_request
            
            # חישוב response times
            cache_response_times = await request_service._calculate_cache_response_times(start_date)
            
            assert isinstance(cache_response_times, dict), "Cache response times should return dict"
            assert 'avg_fulfillment_hours' in cache_response_times, "Should include average fulfillment time"
            
            self.log_test("Cache - Response Time Calculation", True, f"Calculated response times from {len(request_service._request_cache)} cached requests")
            
        except Exception as e:
            self.log_test("Cache - Response Time Calculation", False, str(e))
    
    async def test_notification_callback(self):
        """מבחן callback להתראות"""
        print("\n📧 Testing Notification Callback...")
        
        notification_calls = []
        
        async def mock_notification_callback(user_id: int, message: str):
            notification_calls.append({
                'user_id': user_id,
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
        
        try:
            request_service = RequestService(
                storage_manager=None,
                content_analyzer=None,
                duplicate_detector=None,
                notification_callback=mock_notification_callback
            )
            
            # בדיקת התראה על מילוי בקשה
            await request_service._notify_user_request_fulfilled(
                user_id=123456789,
                request_id=999,
                notes="Test fulfillment note"
            )
            
            assert len(notification_calls) == 1, "Should have one notification call"
            assert notification_calls[0]['user_id'] == 123456789, "User ID should match"
            assert 'מולאה' in notification_calls[0]['message'], "Message should contain fulfillment text"
            
            # בדיקת התראה על דחיית בקשה
            await request_service._notify_user_request_rejected(
                user_id=987654321,
                request_id=888,
                reason="Test rejection reason"
            )
            
            assert len(notification_calls) == 2, "Should have two notification calls"
            assert notification_calls[1]['user_id'] == 987654321, "Second user ID should match"
            assert 'נדחתה' in notification_calls[1]['message'], "Message should contain rejection text"
            
            self.log_test("Notifications - Callback System", True, f"Successfully sent {len(notification_calls)} notifications")
            
        except Exception as e:
            self.log_test("Notifications - Callback System", False, str(e))
    
    async def test_thread_validation_logic(self):
        """מבחן לוגיקת Thread validation"""
        print("\n🧵 Testing Thread Validation Logic...")
        
        # נוצר מבחן פשוט לפונקציונליות Thread
        try:
            # בדיקת מיפוי Thread IDs
            thread_mapping = {v: k for k, v in THREAD_IDS.items() if v is not None}
            assert len(thread_mapping) >= 8, f"Should have at least 8 thread mappings, got {len(thread_mapping)}"
            
            # בדיקת קטגוריות נפוצות
            expected_threads = {
                11432: 'updates',
                11418: 'series', 
                11415: 'software',
                11423: 'books',
                11411: 'movies',
                11422: 'spotify',
                11419: 'games',
                11420: 'apps'
            }
            
            correct_mappings = 0
            for thread_id, expected_category in expected_threads.items():
                if thread_mapping.get(thread_id) == expected_category:
                    correct_mappings += 1
            
            success_rate = (correct_mappings / len(expected_threads)) * 100
            
            if success_rate >= 80:
                self.log_test("Thread Validation - ID Mapping", True, f"{correct_mappings}/{len(expected_threads)} correct mappings ({success_rate:.1f}%)")
            else:
                self.log_test("Thread Validation - ID Mapping", False, f"Only {correct_mappings}/{len(expected_threads)} correct mappings ({success_rate:.1f}%)")
            
        except Exception as e:
            self.log_test("Thread Validation - ID Mapping", False, str(e))
    
    async def test_export_and_backup(self):
        """מבחן פונקציות ייצוא וגיבוי"""
        print("\n💾 Testing Export and Backup Functions...")
        
        try:
            request_service = RequestService(
                storage_manager=None,
                content_analyzer=None, 
                duplicate_detector=None,
                notification_callback=None
            )
            
            # הוספת נתונים דמה למטמון
            for i in range(5):
                test_request = {
                    'id': 2000 + i,
                    'user_id': 100000 + i,
                    'title': f'Test Export Request {i}',
                    'content': f'Content for test request {i}',
                    'category': ['software', 'movies', 'games'][i % 3],
                    'status': ['pending', 'fulfilled', 'rejected'][i % 3],
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                request_service._request_cache[2000 + i] = test_request
            
            # בדיקת ייצוא
            export_data = await request_service.export_data('json')
            
            assert isinstance(export_data, dict), "Export should return a dictionary"
            assert 'metadata' in export_data, "Export should include metadata"
            assert 'requests' in export_data, "Export should include requests data"
            assert 'export_date' in export_data['metadata'], "Metadata should include export date"
            
            exported_requests = export_data['requests']
            assert len(exported_requests) == 5, f"Should export 5 requests, got {len(exported_requests)}"
            
            # בדיקת גיבוי
            backup_data = await request_service.create_backup()
            
            assert isinstance(backup_data, dict), "Backup should return a dictionary"
            assert 'backup_metadata' in backup_data, "Backup should include metadata"
            assert 'system_info' in backup_data['backup_metadata'], "Backup metadata should include system info"
            
            self.log_test("Export/Backup - Data Export", True, f"Successfully exported {len(exported_requests)} requests")
            self.log_test("Export/Backup - System Backup", True, "System backup created successfully")
            
        except Exception as e:
            self.log_test("Export/Backup - Functions", False, str(e))
    
    def generate_report(self) -> str:
        """יצירת דו"ח מבחנים מקיף"""
        total_tests = len(self.test_results)
        passed_count = len(self.passed_tests)
        failed_count = len(self.failed_tests)
        success_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0
        
        report = f"""
🏴‍☠️ דו"ח מבחנים כולל - בוט התמימים הפיראטים
============================================

📊 תוצאות כלליות:
• סה"כ מבחנים: {total_tests}
• הצליחו: {passed_count} ✅
• נכשלו: {failed_count} ❌
• אחוז הצלחה: {success_rate:.1f}%

📝 מבחנים שהצליחו:
"""
        for test in self.passed_tests:
            report += f"  ✅ {test}\n"
        
        if self.failed_tests:
            report += f"\n❌ מבחנים שנכשלו:\n"
            for test in self.failed_tests:
                report += f"  ❌ {test}\n"
        
        report += f"\n🕒 זמן ביצוע הדו\"ח: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # מציאת פרטי כשלים
        failed_details = [result for result in self.test_results if not result['success']]
        if failed_details:
            report += "\n🔍 פרטי כשלים:\n"
            for failure in failed_details:
                report += f"  • {failure['test_name']}: {failure['details']}\n"
        
        report += f"\n🎯 המלצות:\n"
        if success_rate >= 90:
            report += "  🎉 המערכת עובדת מצויין! כל הפונקציות הבסיסיות תקינות.\n"
        elif success_rate >= 75:
            report += "  👍 המערכת עובדת טוב, יש מספר תחומים לשיפור.\n"
        else:
            report += "  ⚠️  המערכת זקוקה לתשומת לב - מספר רכיבים חיוניים לא עובדים.\n"
        
        if failed_count > 0:
            report += f"  🔧 יש לטפל ב-{failed_count} בעיות שזוהו.\n"
        
        return report
    
    def save_detailed_results(self, filename: str = "test_results.json"):
        """שמירת תוצאות מפורטות לקובץ"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    'test_summary': {
                        'total_tests': len(self.test_results),
                        'passed': len(self.passed_tests),
                        'failed': len(self.failed_tests),
                        'success_rate': (len(self.passed_tests) / len(self.test_results) * 100) if self.test_results else 0,
                        'test_date': datetime.now().isoformat()
                    },
                    'test_results': self.test_results
                }, f, ensure_ascii=False, indent=2)
            
            print(f"💾 תוצאות מפורטות נשמרו ב: {filename}")
            
        except Exception as e:
            print(f"❌ שגיאה בשמירת התוצאות: {e}")

async def run_comprehensive_tests():
    """הרצת מבחנים כוללים"""
    print("🏴‍☠️ מתחיל מבחנים כוללים לבוט התמימים הפיראטים")
    print("=" * 60)
    
    tester = BotTester()
    
    try:
        # הרצת כל המבחנים
        await tester.test_config_validation()
        await tester.test_request_service_basic()
        await tester.test_cache_functionality()
        await tester.test_notification_callback()
        await tester.test_thread_validation_logic()
        await tester.test_export_and_backup()
        
        # יצירת דו"ח
        report = tester.generate_report()
        print("\n" + "=" * 60)
        print(report)
        
        # שמירת תוצאות מפורטות
        tester.save_detailed_results()
        
        return len(tester.failed_tests) == 0
        
    except Exception as e:
        print(f"❌ שגיאה כללית במבחנים: {e}")
        return False

if __name__ == "__main__":
    print("🚀 מתחיל בדיקת פונקציונליות הבוט...")
    
    success = asyncio.run(run_comprehensive_tests())
    
    if success:
        print("\n🎉 כל המבחנים הושלמו בהצלחה!")
        sys.exit(0)
    else:
        print("\n⚠️  חלק מהמבחנים נכשלו. עיין בדו\"ח לפרטים.")
        sys.exit(1)