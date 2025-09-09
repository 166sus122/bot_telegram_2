#!/bin/bash
# 🚀 סקריפט התקנה מהירה לבוט התמימים הפיראטים
# רק git clone ו-docker-compose up!

echo "🏴‍☠️ מתקין בוט התמימים הפיראטים..."

# יצירת קובץ .env אם לא קיים
if [ ! -f .env ]; then
    echo "📝 יוצר קובץ .env..."
    cat > .env << 'EOF'
# הגדרות בוט - החלף בערכים שלך!
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
MAIN_GROUP_ID=YOUR_GROUP_ID
LOG_CHANNEL_ID=YOUR_LOG_CHANNEL_ID
ADMIN_IDS=6562280181

# סיסמאות מסד נתונים - אל תשכח לשנות!
DB_PASSWORD=PirateBot2025Secure!
DB_ROOT_PASSWORD=RootPassword2025Strong!

# אופציונליות
GRAFANA_PASSWORD=admin123
DEBUG=false
LOG_LEVEL=INFO
EOF
    echo "⚠️  עדכן את קובץ .env עם הערכים שלך!"
    echo ""
fi

echo "🧹 מנקה קונטיינרים ישנים..."
docker-compose down 2>/dev/null || true
docker system prune -f -q

echo "🚀 מפעיל מסד נתונים..."
docker-compose up -d pirate-mysql-db

echo "⏳ מחכה למסד נתונים להתייצב (30 שניות)..."
sleep 30

echo "🔍 בודק שמסד הנתונים עובד..."
if docker-compose exec pirate-mysql-db mysql -uroot -p$DB_ROOT_PASSWORD -e "SHOW DATABASES;" > /dev/null 2>&1; then
    echo "✅ מסד הנתונים מוכן!"
else
    echo "❌ בעיה עם מסד הנתונים"
    exit 1
fi

echo "🎯 מפעיל שאר השירותים..."
docker-compose up -d

echo "📊 סטטוס המערכת:"
docker-compose ps

echo ""
echo "🎉 ההתקנה הושלמה!"
echo "📱 הבוט צריך להיות פעיל עכשיו"
echo "📋 לצפייה בלוגים: docker-compose logs -f pirate-bot"
echo "🔧 לעדכונים: git pull && docker-compose restart"
echo ""
echo "⚠️  אל תשכח לעדכן את קובץ .env עם הטוקן והמזהים שלך!"