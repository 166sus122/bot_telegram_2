#!/usr/bin/env python3
"""
Script to fix bare except clauses
"""

import os
import re

def fix_bare_except(file_path):
    """Fix bare except clauses in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match bare except clauses
        # Look for 'except:' followed by optional whitespace and comment/code
        patterns = [
            # Basic bare except with comment
            (r'except:\s*\n(\s*)#\s*(.*)', r'except Exception as e:\n\1# \2\n\1logger.debug(f"Error in {os.path.basename(file_path)}: {e}")'),
            
            # Bare except with pass
            (r'except:\s*\n(\s*)pass', r'except Exception as e:\n\1logger.debug(f"Error in {os.path.basename(file_path)}: {e}")'),
            
            # Bare except with simple comment
            (r'except:\s*\n(\s*)# fallback למטמון', r'except Exception as e:\n\1# fallback למטמון - database error\n\1logger.debug(f"Database error, using cache fallback: {e}")'),
            
            # Generic bare except
            (r'except:\s*\n', r'except Exception as e:\n                logger.debug(f"Unexpected error: {e}")\n'),
        ]
        
        fixed = False
        for pattern, replacement in patterns:
            new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
            if count > 0:
                content = new_content
                fixed = True
        
        # If we made changes, write back to file
        if fixed and content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    # Files with known bare except issues
    files_to_fix = [
        '/home/dovber/pirate-content-bot/pirate_content_bot/database/models.py',
        '/home/dovber/pirate-content-bot/pirate_content_bot/database/migrations.py',
        '/home/dovber/pirate-content-bot/pirate_content_bot/services/search_service.py',
        '/home/dovber/pirate-content-bot/pirate_content_bot/tasks/scheduler.py',
        '/home/dovber/pirate-content-bot/pirate_content_bot/utils/cache_manager.py',
        '/home/dovber/pirate-content-bot/pirate_content_bot/core/storage_manager.py'
    ]
    
    fixed_count = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_bare_except(file_path):
                fixed_count += 1
                print(f"✅ Fixed error handling in {os.path.basename(file_path)}")
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n🎯 Fixed error handling in {fixed_count} files")

if __name__ == "__main__":
    main()