#!/usr/bin/env python3
"""
Script to run all tests with proper environment setup
"""
import os
import sys
import subprocess
import logging

# Setup minimal logging to suppress verbose output during testing
logging.basicConfig(level=logging.ERROR)

# Set environment variables for testing
os.environ['USE_DATABASE'] = 'true'
os.environ['DB_HOST'] = '127.0.0.1'
os.environ['DB_PASSWORD'] = 'test_password_123'
os.environ['BOT_TOKEN'] = 'test_token'
os.environ['PYTHONPATH'] = '.'

def run_test_file(test_file, quiet=True):
    """Run a specific test file"""
    cmd = [sys.executable, '-m', 'unittest', f'pirate_content_bot.tests.{test_file}', '-v']
    
    try:
        if quiet:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, timeout=60)
            return result.returncode == 0, "", ""
    except subprocess.TimeoutExpired:
        return False, "", "Test timed out"
    except Exception as e:
        return False, "", str(e)

def main():
    """Run all tests"""
    print("🧪 Running all available tests with Docker services...")
    print("=" * 60)
    
    # Test files to run
    test_files = [
        'test_zero_response_bug',
        'test_all_buttons', 
        'test_admin_commands',
        'test_user_responses'
    ]
    
    results = {}
    
    for test_file in test_files:
        print(f"\n🔬 Testing {test_file}...")
        success, stdout, stderr = run_test_file(test_file, quiet=True)
        
        results[test_file] = success
        
        if success:
            print(f"✅ {test_file}: PASSED")
            # Show only the summary line
            for line in stdout.split('\n'):
                if 'Ran' in line and 'test' in line:
                    print(f"   {line}")
        else:
            print(f"❌ {test_file}: FAILED")
            if stderr:
                print(f"   Error: {stderr[:200]}...")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_file, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_file:<25} {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())