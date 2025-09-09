#!/usr/bin/env python3
"""
Script to verify which tests are being executed in CI
"""

import unittest
import sys
import os

# הוספת הפרוייקט ל-path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 Verifying CI Test Discovery...")
print("=" * 50)

# בדיקה אם Python מוצא טסטים אוטומטית
loader = unittest.TestLoader()

# בדיקה של התיקיה הנוכחית
current_dir_tests = loader.discover('.', pattern='test*.py')
test_count = current_dir_tests.countTestCases()

print(f"📊 Tests found in current directory: {test_count}")

# בדיקה של תיקיית tests
if os.path.exists('tests'):
    tests_dir_tests = loader.discover('tests', pattern='test*.py')
    tests_dir_count = tests_dir_tests.countTestCases()
    print(f"📊 Tests found in tests/ directory: {tests_dir_count}")
else:
    tests_dir_count = 0
    print("📁 No tests/ directory found")

total_discovered = test_count + tests_dir_count
print(f"📊 Total tests that would be discovered: {total_discovered}")

print("\n🎯 Tests that SHOULD run in CI:")
print("- test_ci_safe.py: ~8 tests")
print("- test_commands.py: ~4 tests")
print(f"Expected total: ~12 tests")

print(f"\n⚠️  Discrepancy detected: {total_discovered - 12} extra tests")

if total_discovered > 15:
    print("🚨 WARNING: Too many tests being discovered!")
    print("This explains why CI is running 68 tests instead of 12")
    
    # מציג רשימה של כל הטסטים
    print("\n📋 All discovered test files:")
    for suite in [current_dir_tests, tests_dir_tests if tests_dir_count > 0 else unittest.TestSuite()]:
        for test_group in suite:
            if hasattr(test_group, '_tests'):
                for test in test_group._tests:
                    print(f"  - {test.__class__.__module__}.{test.__class__.__name__}")

print("=" * 50)