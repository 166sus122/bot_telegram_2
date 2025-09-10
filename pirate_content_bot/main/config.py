#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
קובץ הגדרות מתקדם לבוט התמימים הפיראטים
עדכן את ההגדרות לפי הצרכים שלך
"""

import os
from typing import Dict, List, Any

# ========================= הגדרות בוט =========================

# טוקן הבוט מ-BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN', '8121822235:AAGafdtbSaOvKKtwLiPqhvTZ3IRXZkZs7Vs')

# ID של הקבוצה הראשית
MAIN_GROUP_ID = int(os.getenv('MAIN_GROUP_ID', '-1002231406288'))

# ID של ערוץ הלוגים
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '-1003008192507'))

# ========================= Thread IDs לקטגוריות =========================
# Thread IDs לקטגוריות שונות בקבוצה הראשית

# הגדרת Thread IDs - ניתן להגדרה באמצעות משתני סביבה
DEFAULT_THREAD_IDS = {
    'updates': 11432,      # עדכונים
    'series': 11418,       # סדרות
    'software': 11415,     # תוכנות
    'books': 11423,        # ספרים
    'movies': 11411,       # סרטים
    'spotify': 11422,      # ספוטיפיי
    'games': 11419,        # משחקים
    'apps': 11420,         # אפליקציות
    'general': None        # צ'אט כללי (ללא thread)
}

# קריאה ממשתני סביבה עם fallback לברירת המחדל
THREAD_IDS = {}
for category, default_id in DEFAULT_THREAD_IDS.items():
    env_key = f'THREAD_ID_{category.upper()}'
    env_value = os.getenv(env_key)
    if env_value:
        THREAD_IDS[category] = int(env_value) if env_value.isdigit() else None
    else:
        THREAD_IDS[category] = default_id

# ========================= רשימת מנהלים =========================
# 🔥 חשוב: עדכן את הרשימה עם ה-User ID שלך!
# השתמש בקובץ get_my_id.py כדי לגלות את ה-ID שלך

# קריאת רשימת מנהלים ממשתנה סביבה (ללא hardcoded fallback)
admin_ids_str = os.getenv('ADMIN_IDS')
if admin_ids_str:
    ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(',') if id.strip()]
else:
    # אין מנהלים מוגדרים - רק בהגדרת משתנה סביבה
    ADMIN_IDS = []
    logger.warning("⚠️ No admin IDs configured! Set ADMIN_IDS environment variable.")

# ========================= הגדרות מערכת מתקדמות =========================

# הגדרות אחסון
USE_DATABASE = os.getenv('USE_DATABASE', 'false').lower() == 'true'

# הגדרות בסיס נתונים (מתקדם)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'pirate_content'),
    'user': os.getenv('DB_USER', 'pirate_user'),
    'password': os.getenv('DB_PASSWORD', 'test_password_123'),  # Better default for development
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'autocommit': True,
    'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
    'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
    'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600'))
}

# ========================= הגדרות Connection Pool =========================

CONNECTION_POOL_CONFIG = {
    # MySQL Connector Pool parameters
    'pool_name': 'pirate_pool',
    'pool_size': int(os.getenv('POOL_SIZE', '10')),
    'pool_reset_session': True,
    
    # Legacy parameters (kept for compatibility)
    'enabled': USE_DATABASE,
    'retry_attempts': int(os.getenv('POOL_RETRY_ATTEMPTS', '3')),
    'health_check_interval': int(os.getenv('POOL_HEALTH_CHECK', '60'))  # seconds
}

# ========================= הגדרות Cache מתקדמות =========================

CACHE_CONFIG = {
    'enabled': True,
    'type': os.getenv('CACHE_TYPE', 'memory'),  # memory, redis, memcached
    'ttl': {
        'requests': int(os.getenv('CACHE_TTL_REQUESTS', '300')),  # 5 minutes
        'users': int(os.getenv('CACHE_TTL_USERS', '600')),  # 10 minutes
        'stats': int(os.getenv('CACHE_TTL_STATS', '180')),  # 3 minutes
        'duplicates': int(os.getenv('CACHE_TTL_DUPLICATES', '120'))  # 2 minutes
    },
    'max_size': int(os.getenv('CACHE_MAX_SIZE', '1000')),
    'cleanup_interval': int(os.getenv('CACHE_CLEANUP_INTERVAL', '300')),  # 5 minutes
    'redis_config': {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', '6379')),
        'db': int(os.getenv('REDIS_DB', '0')),
        'password': os.getenv('REDIS_PASSWORD', None),
        'decode_responses': True
    }
}

# ========================= הגדרות Background Tasks =========================

BACKGROUND_TASKS_CONFIG = {
    'enabled': True,
    'cleanup_interval': int(os.getenv('CLEANUP_INTERVAL', '3600')),  # 1 hour
    'statistics_update_interval': int(os.getenv('STATS_UPDATE_INTERVAL', '300')),  # 5 minutes
    'notification_check_interval': int(os.getenv('NOTIFICATION_CHECK_INTERVAL', '60')),  # 1 minute
    'duplicate_cleanup_interval': int(os.getenv('DUPLICATE_CLEANUP_INTERVAL', '1800')),  # 30 minutes
    'old_requests_cleanup_days': int(os.getenv('OLD_REQUESTS_CLEANUP_DAYS', '30')),
    'failed_notifications_retry_interval': int(os.getenv('FAILED_NOTIFICATIONS_RETRY', '600')),  # 10 minutes
    'max_concurrent_tasks': int(os.getenv('MAX_CONCURRENT_TASKS', '5'))
}

# ========================= הגדרות Fuzzy Matching מתקדמות =========================

FUZZY_MATCHING_CONFIG = {
    'enabled': True,
    'algorithms': {
        'levenshtein': {
            'enabled': True,
            'weight': 0.4,
            'threshold': 0.8
        },
        'jaro_winkler': {
            'enabled': True,
            'weight': 0.3,
            'threshold': 0.85
        },
        'soundex': {
            'enabled': True,
            'weight': 0.2,
            'threshold': 0.9
        },
        'metaphone': {
            'enabled': True,
            'weight': 0.1,
            'threshold': 0.9
        }
    },
    'preprocessing': {
        'normalize_unicode': True,
        'remove_punctuation': True,
        'lowercase': True,
        'remove_extra_spaces': True,
        'remove_stop_words': True
    },
    'stop_words': ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                   'את', 'של', 'על', 'ב', 'ל', 'מ', 'ה', 'ו', 'כ', 'ש', 'ז', 'ע', 'ר', 'ד', 'ג', 'כמו', 'עם']
}

# ========================= הגדרות בדיקת כפילויות מתקדמות =========================

DUPLICATE_DETECTION_CONFIG = {
    'threshold': float(os.getenv('DUPLICATE_THRESHOLD', '0.85')),
    'title_weight': 0.6,
    'description_weight': 0.3,
    'category_weight': 0.1,
    'time_window_hours': int(os.getenv('DUPLICATE_TIME_WINDOW', '24')),
    'user_specific': True,
    'cross_category_check': False,
    'fuzzy_enabled': True,
    'exact_match_priority': True
}

# ========================= הגדרות הגבלות מתקדמות =========================

RATE_LIMITING_CONFIG = {
    'enabled': True,
    'requests_per_minute': int(os.getenv('REQUESTS_PER_MINUTE', '10')),
    'requests_per_hour': int(os.getenv('REQUESTS_PER_HOUR', '50')),
    'requests_per_day': int(os.getenv('REQUESTS_PER_DAY', '100')),
    'admin_multiplier': 5,  # Admins get 5x more requests
    'cooldown_seconds': int(os.getenv('REQUEST_COOLDOWN', '60')),
    'burst_allowance': int(os.getenv('BURST_ALLOWANCE', '5')),
    'progressive_penalties': {
        'first_violation': 300,  # 5 minutes
        'second_violation': 900,  # 15 minutes
        'third_violation': 3600,  # 1 hour
        'persistent_violation': 86400  # 24 hours
    }
}

# הגדרות הגבלות תוכן
CONTENT_LIMITS = {
    'max_request_length': int(os.getenv('MAX_REQUEST_LENGTH', '1000')),
    'max_title_length': int(os.getenv('MAX_TITLE_LENGTH', '200')),
    'max_description_length': int(os.getenv('MAX_DESCRIPTION_LENGTH', '500')),
    'max_notes_length': int(os.getenv('MAX_NOTES_LENGTH', '300')),
    'min_request_length': int(os.getenv('MIN_REQUEST_LENGTH', '5')),
    'max_attachments_per_request': int(os.getenv('MAX_ATTACHMENTS', '3'))
}

# ========================= הגדרות התראות מתקדמות =========================

NOTIFICATION_CONFIG = {
    'enabled': True,
    'channels': {
        'telegram': True,
        'email': os.getenv('EMAIL_NOTIFICATIONS', 'false').lower() == 'true',
        'webhook': os.getenv('WEBHOOK_NOTIFICATIONS', 'false').lower() == 'true'
    },
    'user_notifications': {
        'request_created': True,
        'request_fulfilled': True,
        'request_rejected': True,
        'request_updated': True,
        'system_maintenance': True
    },
    'admin_notifications': {
        'new_request': True,
        'urgent_request': True,
        'system_errors': True,
        'daily_summary': True,
        'user_feedback': True
    },
    'timing': {
        'immediate': ['request_fulfilled', 'urgent_request', 'system_errors'],
        'batched': ['daily_summary'],
        'delayed': ['request_rejected']
    },
    'retry_config': {
        'max_attempts': 3,
        'backoff_factor': 2,
        'initial_delay': 60
    }
}

# ========================= הגדרות תגובות אוטומטיות משופרות =========================

AUTO_RESPONSE_CONFIG = {
    'enabled': True,
    'delay_range': (5, 15),  # Random delay between 5-15 seconds
    'confidence_threshold': 0.15,
    'response_types': {
        'thanks': {
            'enabled': True,
            'probability': 0.8,
            'cooldown': 300  # 5 minutes between responses
        },
        'bump': {
            'enabled': True,
            'probability': 0.6,
            'cooldown': 600  # 10 minutes between responses
        },
        'help': {
            'enabled': True,
            'probability': 0.9,
            'cooldown': 120  # 2 minutes between responses
        }
    }
}

# ========================= מילות מפתח מתקדמות =========================

# מילות תודה לתגובות אוטומטיות
THANKS_KEYWORDS = [
    'תודה', 'תודה רבה', 'יא מלך', 'חבר', 'אלוף', 'גדול',
    'אחלה', 'מעולה', 'perfect', 'thanks', 'thx', 'אלופים',
    'מלכים', 'legends', 'חמודים', 'יפים', 'כבוד', 'respect',
    'תודה ענקית', 'אני חייב לך', 'מושלם', 'פצצה', 'וואו'
]

# מילות bump מורחבות
BUMP_KEYWORDS = [
    '.', 'בעמפ', 'up', 'bump', 'בדיקה', 'עדכון?', 'נו?',
    '??', '???', 'נו', 'מה קורה', 'עדכון', 'יש חדשות?',
    'מישהו?', 'הלו?', 'anyone?', 'עוד מישהו מחפש?',
    'עדיין מחפש', 'עדיין צריך', 'still looking'
]

# מילות מפתח לעדיפות דחופה
URGENT_KEYWORDS = [
    'דחוף', 'דחופה', 'חירום', 'בעיה', 'בעיות', 'קריטי',
    'לא עובד', 'נחוץ מהר', 'urgent', 'emergency', 'critical',
    'מיידי', 'עכשיו', 'now', 'immediately', 'asap', 'בהקדם'
]

# מילות מפתח לעדיפות גבוהה
HIGH_PRIORITY_KEYWORDS = [
    'חשוב', 'צריך מהר', 'בקרוב', 'חיפוש ממושך', 'important',
    'כבר זמן', 'מחפש הרבה זמן', 'חפשתי בכל מקום',
    'לא מוצא', 'נואש', 'פרויקט', 'עבודה', 'לימודים'
]

# מילות מפתח ל-VIP
VIP_KEYWORDS = [
    'vip', 'ויי איי פי', 'מיוחד', 'פרימיום', 'premium',
    'בלעדי', 'exclusive', 'special', 'תורם', 'donor'
]

# ========================= קטגוריות תוכן מורחבות =========================

CONTENT_CATEGORIES = {
    'series': {
        'name': 'סדרות 📺',
        'keywords': ['סדרה', 'עונה', 'פרק', 'season', 'episode', 'סדרת', 'show', 'tv series'],
        'emoji': '📺',
        'aliases': ['tv', 'television', 'סידרה', 'שואו'],
        'subcategories': ['drama', 'comedy', 'action', 'documentary_series']
    },
    'movies': {
        'name': 'סרטים 🎬',
        'keywords': ['סרט', 'movie', 'film', 'cinema', 'הסרט', 'picture'],
        'emoji': '🎬',
        'aliases': ['motion picture', 'flick', 'סרטון'],
        'subcategories': ['action', 'comedy', 'drama', 'horror', 'sci-fi', 'animation']
    },
    'books': {
        'name': 'ספרים 📚',
        'keywords': ['ספר', 'book', 'קריאה', 'PDF', 'epub', 'הספר', 'novel', 'כתב'],
        'emoji': '📚',
        'aliases': ['ebook', 'audiobook', 'ספרות', 'רומן'],
        'subcategories': ['fiction', 'non-fiction', 'textbook', 'comic', 'manga']
    },
    'games': {
        'name': 'משחקים 🎮',
        'keywords': ['משחק', 'game', 'גיים', 'PS', 'Xbox', 'PC', 'המשחק', 'gaming'],
        'emoji': '🎮',
        'aliases': ['video game', 'computer game', 'משחקי מחשב'],
        'subcategories': ['pc', 'console', 'mobile', 'arcade', 'retro']
    },
    'spotify': {
        'name': 'ספוטיפיי 🎵',
        'keywords': ['ספוטיפיי', 'spotify', 'playlist', 'מוזיקה', 'שיר', 'music'],
        'emoji': '🎵',
        'aliases': ['מיוזיק', 'פלייליסט', 'album', 'track'],
        'subcategories': ['playlist', 'album', 'single', 'podcast']
    },
    'apps': {
        'name': 'אפליקציות 📱',
        'keywords': ['אפליקציה', 'app', 'אפ', 'APK', 'iOS', 'האפליקציה', 'application'],
        'emoji': '📱',
        'aliases': ['אפליקציה', 'תוכנת נייד', 'mobile app'],
        'subcategories': ['android', 'ios', 'web_app', 'desktop_app']
    },
    'software': {
        'name': 'תוכנות 💻',
        'keywords': ['תוכנה', 'software', 'program', 'exe', 'installer', 'tool'],
        'emoji': '💻',
        'aliases': ['תוכנית', 'כלי', 'utility', 'application'],
        'subcategories': ['productivity', 'creative', 'development', 'system']
    },
    'anime': {
        'name': 'אנימה 🍙',
        'keywords': ['אנימה', 'anime', 'מנגה', 'manga', 'japanese'],
        'emoji': '🍙',
        'aliases': ['אנימציה יפנית', 'manga', 'manhwa'],
        'subcategories': ['shounen', 'shoujo', 'seinen', 'josei']
    },
    'documentaries': {
        'name': 'דוקו 🎥',
        'keywords': ['דוקומנטרי', 'documentary', 'דוקו', 'תיעודי', 'educational'],
        'emoji': '🎥',
        'aliases': ['תיעוד', 'סרט תיעודי', 'doc'],
        'subcategories': ['nature', 'history', 'science', 'biography']
    },
    'audiobooks': {
        'name': 'ספרי שמע 🎧',
        'keywords': ['audiobook', 'ספר מוקלט', 'שמע', 'הקראה', 'נרטיב'],
        'emoji': '🎧',
        'aliases': ['ספר מוקלט', 'הקראה'],
        'subcategories': ['fiction', 'non-fiction', 'educational']
    },
    'general': {
        'name': 'כללי 📋',
        'keywords': [],
        'emoji': '📋',
        'aliases': [],
        'subcategories': []
    }
}

# ========================= רמות עדיפות מתקדמות =========================

PRIORITY_LEVELS = {
    'low': {
        'name': '🟢 רגילה',
        'value': 1,
        'sla_hours': 72,
        'auto_escalate': False
    },
    'medium': {
        'name': '🟡 בינונית',
        'value': 2,
        'sla_hours': 48,
        'auto_escalate': True
    },
    'high': {
        'name': '🟠 גבוהה',
        'value': 3,
        'sla_hours': 24,
        'auto_escalate': True
    },
    'urgent': {
        'name': '🔴 דחופה',
        'value': 4,
        'sla_hours': 6,
        'auto_escalate': True
    },
    'vip': {
        'name': '💎 VIP',
        'value': 5,
        'sla_hours': 2,
        'auto_escalate': True
    }
}

# ========================= הגדרות DEBUG ומעקב =========================

DEBUG_CONFIG = {
    'enabled': os.getenv('DEBUG', 'false').lower() == 'true',
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'log_rotation': {
        'enabled': True,
        'max_bytes': int(os.getenv('LOG_MAX_BYTES', '10485760')),  # 10MB
        'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5'))
    },
    'performance_monitoring': {
        'enabled': True,
        'slow_query_threshold': float(os.getenv('SLOW_QUERY_THRESHOLD', '1.0')),
        'memory_monitoring': True,
        'response_time_tracking': True
    },
    'error_reporting': {
        'enabled': True,
        'webhook_url': os.getenv('ERROR_WEBHOOK_URL', ''),
        'include_traceback': True,
        'rate_limit': 10  # max 10 error reports per minute
    }
}

# ========================= הודעות מערכת =========================

SYSTEM_MESSAGES = {
    'welcome': """
🏴‍☠️ ברוך הבא לקהילת התמימים הפיראטים המתקדמת!

🎬 מערכת בקשות תוכן מתקדמת
📺 סדרות | 🎬 סרטים | 📚 ספרים | 🎮 משחקים | 🎵 מוזיקה

✨ פשוט כתוב מה אתה מחפש - הבוט יזהה אוטומטית!
🤖 זיהוי חכם עם AI | 🔍 חיפוש כפילויות | 📊 מעקב מתקדם

💡 /help - לכל הפקודות והטיפים
    """,

    'invalid_request': """
❌ לא הצלחתי לזהות בקשה ברורה.

💡 טיפים לבקשה מושלמת:
• ציין כותרת מלאה וברורה
• הוסף שנה במידת האפשר
• לסדרות - ציין עונה ופרק
• ציין פלטפורמה (PC/PS5/Xbox)

🎯 דוגמאות מושלמות:
• "הסדרה Breaking Bad 2008 עונה 1"
• "הסרט Avatar The Way of Water 2022"
• "המשחק Cyberpunk 2077 PC"

🤖 הבוט לומד מהבקשות שלך ומשתפר כל הזמן!
    """,

    'request_created': """
✅ בקשה נוצרה בהצלחה במערכת המתקדמת!

📋 הבקשה נשלחה למנהלים עם עדיפות חכמה
🔔 תקבל התראה מיידית כשהבקשה תמולא
📊 המערכת תעקב אחר הסטטוס אוטומטית

💡 /my_requests - לצפייה בכל הבקשות שלך
    """,

    'maintenance_mode': """
🔧 המערכת במצב תחזוקה זמנית

⏰ זמן משוער: 10-15 דקות
🔄 כל הבקשות נשמרות ויטופלו בהמשך

תודה על הסבלנות! 🙏
    """,

    'system_upgrade': """
🚀 המערכת עודכנה בהצלחה!

✨ חידושים במהדורה זו:
• זיהוי חכם משופר
• מהירות תגובה מוגברת
• ממשק משתמש מחודש
• הגנה מפני ספאם

המשיכו ליהנות! 🎉
    """
}

# ========================= אמצעי אבטחה מתקדמים =========================

SECURITY_CONFIG = {
    'enabled': True,
    'rate_limiting': True,
    'spam_detection': {
        'enabled': True,
        'max_identical_messages': 3,
        'time_window': 300,  # 5 minutes
        'auto_ban_threshold': 5,
        'ban_duration': 3600  # 1 hour
    },
    'content_filtering': {
        'enabled': True,
        'max_message_length': int(os.getenv('MAX_MESSAGE_LENGTH', '2000')),
        'blocked_patterns': [
            r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+)',
            r'(@[a-zA-Z0-9_]+)',  # Mention spam
            r'(\+\d{10,15})'  # Phone numbers
        ],
        'whitelist_admins': True
    },
    'user_verification': {
        'enabled': False,
        'require_username': False,
        'min_account_age': 0,  # days
        'require_profile_photo': False
    },
    'flood_protection': {
        'enabled': True,
        'max_messages_per_second': 2,
        'max_messages_per_minute': 20,
        'auto_mute_duration': 300  # 5 minutes
    }
}

# רשימה שחורה של מילים (מותאמת למערכת הישראלית)
BLOCKED_WORDS = [
    # הוסף מילים שאתה רוצה לחסום
    # דוגמאות: ספאם, פרסומות לא רצויות, וכו'
]

# רשימה לבנה של דומיינים מהימנים
TRUSTED_DOMAINS = [
    'drive.google.com',
    'mega.nz',
    'mediafire.com',
    'dropbox.com'
]

# ========================= הגדרות ביצועים =========================

PERFORMANCE_CONFIG = {
    'async_processing': True,
    'max_concurrent_requests': int(os.getenv('MAX_CONCURRENT_REQUESTS', '50')),
    'request_timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
    'batch_processing': {
        'enabled': True,
        'batch_size': int(os.getenv('BATCH_SIZE', '10')),
        'batch_timeout': int(os.getenv('BATCH_TIMEOUT', '5'))
    },
    'caching_strategy': 'aggressive',  # conservative, balanced, aggressive
    'precompute_stats': True,
    'lazy_loading': True
}

# ========================= הגדרות Analytics =========================

ANALYTICS_CONFIG = {
    'enabled': True,
    'track_events': [
        'request_created',
        'request_fulfilled',
        'request_rejected',
        'user_interaction',
        'button_clicked',
        'command_used'
    ],
    'retention_days': int(os.getenv('ANALYTICS_RETENTION_DAYS', '90')),
    'real_time_stats': True,
    'export_formats': ['json', 'csv', 'excel'],
    'dashboard_enabled': False,
    'privacy_mode': True  # Hash user IDs for privacy
}

# ========================= הערות למפתח המתקדם =========================

"""
📝 הוראות עדכון מתקדמות:

🔑 הגדרות חובה:
1. BOT_TOKEN - הטוקן מ-@BotFather
2. ADMIN_IDS - רשימת User IDs של מנהלים
3. LOG_CHANNEL_ID - ID של ערוץ לוגים
4. MAIN_GROUP_ID - ID של קבוצה ראשית

🗄️ הגדרות בסיס נתונים:
- USE_DATABASE=true עבור PostgreSQL/MySQL
- DB_CONFIG עבור פרטי החיבור
- CONNECTION_POOL_CONFIG עבור ביצועים מיטביים

🚀 הגדרות ביצועים:
- CACHE_CONFIG עבור מהירות מוגברת
- PERFORMANCE_CONFIG עבור עיבוד אסינכרוני
- BACKGROUND_TASKS_CONFIG עבור משימות אוטומטיות

🔒 הגדרות אבטחה:
- SECURITY_CONFIG עבור הגנה מפני ספאם
- RATE_LIMITING_CONFIG עבור בקרת תעבורה
- BLOCKED_WORDS עבור סינון תוכן

🤖 הגדרות AI מתקדמות:
- FUZZY_MATCHING_CONFIG עבור זיהוי חכם
- DUPLICATE_DETECTION_CONFIG עבור מניעת כפילויות
- AUTO_RESPONSE_CONFIG עבור תגובות אוטומטיות

📊 מעקב ואנליטיקה:
- ANALYTICS_CONFIG עבור מעקב שימוש
- DEBUG_CONFIG עבור ניטור ביצועים
- NOTIFICATION_CONFIG עבור התראות מתקדמות

⚠️ חשוב:
- אל תשתף את הטוקן עם אחרים
- גבה את קובץ ההגדרות באופן קבוע
- בדוק את רשימת המנהלים לעתים קרובות
- עקוב אחר לוגי המערכת להבטחת פעילות תקינה

🔄 עדכונים תקופתיים:
- בדוק עדכוני Telegram Bot API
- עדכן רשימות מילות מפתח
- סקור הגדרות אבטחה וביצועים
- בצע גיבוי של בסיס הנתונים

📞 תמיכה:
ליצירת קשר עם מפתח המערכת, השאר הודעה בערוץ הלוגים
"""