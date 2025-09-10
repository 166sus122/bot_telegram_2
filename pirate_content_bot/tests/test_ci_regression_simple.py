#!/usr/bin/env python3
"""
טסטי רגרסיה פשוטים עבור CI/CD
מיועד לרוץ ב-GitHub Actions ללא dependencies מורכבים

בדיקות בסיסיות שמזהות את הבעיות העיקריות:
1. JSON serialization עם datetime objects
2. Callback routing logic
3. Error handling patterns
4. Database connection fallbacks
"""

import sys
import os
import json
from datetime import datetime, date
import re

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_json_serialization():
    """בדיקת JSON serialization עם datetime objects"""
    print("🧪 Testing JSON serialization...")
    
    try:
        # Import the json helpers
        from utils.json_helpers import safe_json_dumps, json_serial
        
        # Test datetime object
        test_data = {
            'timestamp': datetime(2023, 12, 25, 10, 30, 0),
            'date': date(2023, 12, 25),
            'user_id': 123,
            'message': 'test message'
        }
        
        # This should work without throwing an exception
        result = safe_json_dumps(test_data)
        
        # Should be able to parse back
        parsed = json.loads(result)
        
        # Verify data integrity
        assert parsed['user_id'] == 123
        assert parsed['message'] == 'test message'
        assert '2023-12-25' in parsed['timestamp']
        assert '2023-12-25' in parsed['date']
        
        print("✅ JSON serialization test passed")
        return True
        
    except Exception as e:
        print(f"❌ JSON serialization test failed: {e}")
        return False

def test_callback_patterns():
    """בדיקת patterns של callback data"""
    print("🧪 Testing callback patterns...")
    
    try:
        # Test callback patterns that should be recognized
        callback_patterns = [
            r"^view_request:\d+$",
            r"^admin:(pending|stats|backup)$", 
            r"^create_request:\w+$",
            r"^edit_request:\d+$",
            r"^admin_action:(approve|reject)$",
            r"^action:main_menu$"
        ]
        
        test_callbacks = [
            "view_request:123",
            "admin:pending",
            "admin:stats", 
            "create_request:general",
            "edit_request:456",
            "admin_action:approve",
            "action:main_menu"
        ]
        
        for callback in test_callbacks:
            matched = False
            for pattern in callback_patterns:
                if re.match(pattern, callback):
                    matched = True
                    break
            
            if not matched:
                print(f"❌ Callback '{callback}' doesn't match any pattern!")
                return False
        
        print("✅ Callback patterns test passed")
        return True
        
    except Exception as e:
        print(f"❌ Callback patterns test failed: {e}")
        return False

def test_file_structure():
    """בדיקת מבנה הקבצים הקריטיים"""
    print("🧪 Testing critical file structure...")
    
    try:
        base_path = os.path.dirname(os.path.dirname(__file__))
        
        critical_files = [
            'main/pirate_bot_main.py',
            'services/request_service.py',
            'services/user_service.py',
            'utils/json_helpers.py',
        ]
        
        for file_path in critical_files:
            full_path = os.path.join(base_path, file_path)
            if not os.path.exists(full_path):
                print(f"❌ Critical file missing: {file_path}")
                return False
        
        print("✅ File structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ File structure test failed: {e}")
        return False

def test_error_handling_patterns():
    """בדיקת patterns של error handling"""
    print("🧪 Testing error handling patterns...")
    
    try:
        base_path = os.path.dirname(os.path.dirname(__file__))
        
        # Check that error messages exist in the code
        main_file = os.path.join(base_path, 'main/pirate_bot_main.py')
        request_service_file = os.path.join(base_path, 'services/request_service.py')
        
        with open(main_file, 'r', encoding='utf-8') as f:
            main_content = f.read()
            
        with open(request_service_file, 'r', encoding='utf-8') as f:
            request_content = f.read()
        
        # Check for critical error messages
        critical_patterns = [
            'לא מזוהה',  # Should be in main file
            'שגיאה בעדכון מסד הנתונים',  # Should be in request service
            'אין נתונים זמינים'  # Should be in main file
        ]
        
        if 'לא מזוהה' not in main_content:
            print("❌ 'לא מזוהה' pattern not found in main file")
            return False
            
        if 'שגיאה בעדכון מסד הנתונים' not in request_content:
            print("❌ 'שגיאה בעדכון מסד הנתונים' pattern not found in request service")
            return False
            
        if 'אין נתונים זמינים' not in main_content:
            print("❌ 'אין נתונים זמינים' pattern not found in main file")
            return False
        
        print("✅ Error handling patterns test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error handling patterns test failed: {e}")
        return False

def test_callback_routing_logic():
    """בדיקת לוגיקת routing של callbacks"""
    print("🧪 Testing callback routing logic...")
    
    try:
        base_path = os.path.dirname(os.path.dirname(__file__))
        main_file = os.path.join(base_path, 'main/pirate_bot_main.py')
        
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for enhanced_button_callback function
        if 'async def enhanced_button_callback' not in content:
            print("❌ enhanced_button_callback function not found")
            return False
        
        # Check for proper routing patterns
        routing_patterns = [
            'data.startswith("view_request:")',
            'data.startswith("admin:")',
            'data.startswith("create_request:")',
            'await self._handle_generic_button(query, data)'
        ]
        
        for pattern in routing_patterns:
            if pattern not in content:
                print(f"❌ Routing pattern not found: {pattern}")
                return False
        
        print("✅ Callback routing logic test passed")
        return True
        
    except Exception as e:
        print(f"❌ Callback routing logic test failed: {e}")
        return False

def test_user_service_fallback():
    """בדיקת fallback logic ב-user service"""
    print("🧪 Testing user service fallback logic...")
    
    try:
        base_path = os.path.dirname(os.path.dirname(__file__))
        user_service_file = os.path.join(base_path, 'services/user_service.py')
        
        with open(user_service_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for is_returning_user function
        if 'async def is_returning_user' not in content:
            print("❌ is_returning_user function not found")
            return False
        
        # Check for proper error handling (should return True on error)
        if 'except Exception' not in content:
            print("❌ Exception handling not found in user service")
            return False
        
        print("✅ User service fallback test passed")
        return True
        
    except Exception as e:
        print(f"❌ User service fallback test failed: {e}")
        return False

def main():
    """הרצת כל טסטי הרגרסיה הפשוטים"""
    print("🚀 Starting CI Regression Tests")
    print("=" * 50)
    
    tests = [
        ("JSON Serialization", test_json_serialization),
        ("Callback Patterns", test_callback_patterns),
        ("File Structure", test_file_structure),
        ("Error Handling Patterns", test_error_handling_patterns),
        ("Callback Routing Logic", test_callback_routing_logic),
        ("User Service Fallback", test_user_service_fallback)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔄 Running {test_name}...")
        
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1
    
    # סיכום
    print("\n" + "=" * 50)
    print(f"🎯 CI Regression Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 All CI regression tests passed!")
        return 0
    else:
        print("⚠️ Some CI regression tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())