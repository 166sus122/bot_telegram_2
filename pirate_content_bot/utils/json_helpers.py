#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
עזרי JSON - פתרון לבעיות serialization
"""

import json
import logging
from datetime import datetime, date, time
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


class DateTimeEncoder(json.JSONEncoder):
    """JSON Encoder מותאם אישית שמטפל בdatetime objects"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        
        # קריאה לsuper().default() לטיפול בטיפוסים רגילים
        return super().default(obj)


def json_serial(obj: Any) -> Any:
    """
    JSON serializer עבור objects שלא נתמכים בשיטה הרגילה
    
    Args:
        obj: אובייקט לserialization
        
    Returns:
        Serialized value
        
    Raises:
        TypeError: אם הטיפוס לא נתמך
    """
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    
    elif isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    
    elif isinstance(obj, time):
        return obj.strftime('%H:%M:%S')
        
    elif isinstance(obj, Decimal):
        return float(obj)
        
    elif obj is None:
        return None
        
    elif hasattr(obj, '__dict__'):
        # אובייקטים עם __dict__ (כמו dataclass או custom objects)
        return obj.__dict__
        
    elif hasattr(obj, 'isoformat'):
        # תאריכים ושעות נוספים
        return obj.isoformat()
    
    # אם לא מצאנו טיפוס מתאים
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    JSON dumps בטוח שמטפל בכל הטיפוסים הבעייתיים
    
    Args:
        obj: אובייקט לserialization
        **kwargs: פרמטרים נוספים ל-json.dumps
        
    Returns:
        JSON string
    """
    # ברירות מחדל טובות
    default_kwargs = {
        'ensure_ascii': False,
        'indent': 2,
        'default': json_serial,
        'sort_keys': False
    }
    
    # עדכון עם הפרמטרים שהתקבלו
    default_kwargs.update(kwargs)
    
    return json.dumps(obj, **default_kwargs)


def safe_json_loads(json_str: str, **kwargs) -> Any:
    """
    JSON loads בטוח עם error handling
    
    Args:
        json_str: JSON string
        **kwargs: פרמטרים נוספים ל-json.loads
        
    Returns:
        Parsed object או None במקרה של שגיאה
    """
    try:
        return json.loads(json_str, **kwargs)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"⚠️ JSON parsing error: {e}")
        return None


def clean_for_json(obj: Any) -> Any:
    """
    ניקוי אובייקט לפני JSON serialization
    
    Args:
        obj: אובייקט לניקוי
        
    Returns:
        אובייקט נקי לserialization
    """
    if isinstance(obj, dict):
        return {key: clean_for_json(value) for key, value in obj.items()}
    
    elif isinstance(obj, (list, tuple)):
        return [clean_for_json(item) for item in obj]
    
    elif isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    
    elif isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    
    elif isinstance(obj, Decimal):
        return float(obj)
    
    elif obj is None:
        return None
    
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    
    else:
        # ניסיון להמיר לstring
        try:
            return str(obj)
        except Exception as e:
            logger.debug(f"Could not serialize object to string: {e}")
            return f"<{type(obj).__name__} object>"


def format_json_for_export(data: Any, format_type: str = 'pretty') -> str:
    """
    פורמט JSON מיועד לייצוא
    
    Args:
        data: נתונים לפורמט
        format_type: סוג הפורמט - 'pretty', 'compact', 'minified'
        
    Returns:
        JSON string מפורמט
    """
    if format_type == 'compact':
        return safe_json_dumps(data, indent=None, separators=(',', ':'))
    
    elif format_type == 'minified':
        return safe_json_dumps(data, indent=None, separators=(',', ':'), ensure_ascii=True)
    
    else:  # pretty (default)
        return safe_json_dumps(data, indent=2)


# דוגמאות שימוש
if __name__ == "__main__":
    # דוגמה עם datetime
    test_data = {
        'created_at': datetime.now(),
        'user_id': 12345,
        'title': 'Test Request בעברית',
        'metadata': {
            'priority': 'high',
            'tags': ['urgent', 'vip'],
            'updated_at': datetime.now()
        },
        'price': Decimal('19.99'),
        'active': True,
        'notes': None
    }
    
    print("🧪 בדיקת JSON serialization:")
    print("=" * 50)
    
    # בדיקת הפונקציה הבטוחה
    try:
        result = safe_json_dumps(test_data)
        print("✅ safe_json_dumps עבד בהצלחה:")
        print(result[:200] + "..." if len(result) > 200 else result)
    except Exception as e:
        print(f"❌ safe_json_dumps נכשל: {e}")
    
    # בדיקת clean_for_json
    try:
        cleaned = clean_for_json(test_data)
        result = json.dumps(cleaned, ensure_ascii=False, indent=2)
        print("\n✅ clean_for_json עבד בהצלחה")
    except Exception as e:
        print(f"❌ clean_for_json נכשל: {e}")