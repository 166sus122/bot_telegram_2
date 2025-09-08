#!/bin/bash
# בוט התמימים הפיראטים - סקריפט אתחול

set -e

echo "🏴‍☠️ בוט התמימים הפיראטים - אתחול מערכת"
echo "=================================================="

# בדיקת משתני סביבה נדרשים
required_vars=("BOT_TOKEN" "ADMIN_IDS")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ משתנה סביבה נדרש חסר: $var"
        exit 1
    fi
done

# יצירת תיקיות נדרשות
mkdir -p /app/logs /app/exports /app/data /app/cache
echo "✅ תיקיות נוצרו בהצלחה"

# בדיקת חיבור למסד נתונים (אם מופעל)
if [ "${USE_DATABASE:-false}" = "true" ]; then
    echo "🔍 בודק חיבור למסד נתונים..."
    
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if python3 -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(
        host='${DB_HOST:-localhost}',
        database='${DB_NAME:-pirate_content}',
        user='${DB_USER:-pirate_user}',
        password='${DB_PASSWORD}'
    )
    conn.close()
    print('Database connection successful')
    exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
" 2>/dev/null; then
            echo "✅ חיבור למסד נתונים הצליח"
            break
        fi
        
        attempt=$((attempt + 1))
        echo "⏳ נסיון $attempt/$max_attempts - ממתין למסד נתונים..."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ לא הצליח להתחבר למסד נתונים לאחר $max_attempts נסיונות"
        exit 1
    fi
fi

# בדיקת חיבור ל-Redis (אם מופעל)
if [ "${CACHE_TYPE:-memory}" = "redis" ]; then
    echo "🔍 בודק חיבור ל-Redis..."
    
    if python3 -c "
import redis
try:
    r = redis.Redis(host='${REDIS_HOST:-localhost}', port=${REDIS_PORT:-6379}, db=${REDIS_DB:-0})
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
    exit(1)
" 2>/dev/null; then
        echo "✅ חיבור ל-Redis הצליח"
    else
        echo "⚠️ לא הצליח להתחבר ל-Redis, ממשיך עם cache בזיכרון"
        export CACHE_TYPE=memory
    fi
fi

# הגדרת הרשאות קבצים
chmod -R 755 /app
chown -R app:app /app 2>/dev/null || true

echo "🚀 אתחול הושלם בהצלחה!"
echo "🎯 הפעלת הבוט..."

# הפעלת הבוט
exec python3 pirate_bot_main.py