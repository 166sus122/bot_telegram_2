#!/bin/bash
# 🚀 סקריפט פריסה אוטומטי מלא – commit, push, build Docker, deploy לשרת
# מותאם ל-GitHub repository: 166sus122/bot_telegram_2
# Docker Hub: dov121212
# Server: testuser@173.249.34.10

set -e

echo "=================================="
echo "🚀 מתחיל תהליך פריסה אוטומטי..."
echo "=================================="

# 1️⃣ בדיקת מצב קונטיינרים מקומיים
echo "📊 מצב נוכחי של הקונטיינרים:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2️⃣ שמירת שינויים ב-git (commit אוטומטי)
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️  יש שינויים לא שמורים. מוסיף commit אוטומטי..."
    git add .
    commit_message="עדכון אוטומטי לפני פריסה"
    git commit -m "$commit_message"
else
    echo "✅ כל השינויים שמורים ב-git"
fi

# 3️⃣ עצירת Docker מקומי
if [[ -d "pirate_content_bot" ]]; then
    cd pirate_content_bot
    if docker-compose ps | grep -q "Up"; then
        echo "🛑 עוצר קונטיינרים מקומיים..."
        docker-compose down
        echo "🧹 מנקה קונטיינרים ישנים..."
        docker container prune -f
    else
        echo "ℹ️  Docker כבר נעצר"
    fi
    cd ..
fi

# 4️⃣ Push אוטומטי ל-GitHub דרך SSH
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "⬆️  מעלה את השינויים ל-GitHub ב-branch $CURRENT_BRANCH..."
git push -u origin $CURRENT_BRANCH

echo "🔄 GitHub Actions ירוץ אוטומטית עכשיו:"
echo "https://github.com/166sus122/bot_telegram_2/actions"

# 5️⃣ Deploy לשרת דרך SSH (מפתח פרטי)
# מניח שה-SSH key כבר קיים ומחובר לשרת
SERVER_USER="testuser"
SERVER_HOST="173.249.34.10"

echo "🔐 מחבר לשרת ומריץ deploy..."
ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" << 'ENDSSH'
echo "📂 יצירת תיקיית הפרוייקט..."
mkdir -p /opt/pirate-content-bot
cd /opt/pirate-content-bot

echo "🧹 ניקוי קונטיינרים ישנים..."
docker-compose down || true
docker system prune -f || true

echo "📥 מוריד קבצי הגדרה מ-GitHub..."
curl -L https://raw.githubusercontent.com/166sus122/bot_telegram_2/master/docker-compose.yml -o docker-compose.yml
curl -L https://raw.githubusercontent.com/166sus122/bot_telegram_2/master/.env.example -o .env.template

echo "⚙️ יוצר קובץ .env עם הגדרות בסיסיות..."
cp .env.template .env

# הגדרת משתנים חיוניים (יש לעדכן בהתאם לסביבה)
echo "DB_ROOT_PASSWORD=pirate_root_2024" >> .env
echo "DB_PASSWORD=pirate_secure_2024" >> .env

echo "🐳 מושך את כל ה-Docker images הנדרשים..."
docker pull dov121212/bot_telegram_2:latest || echo "⚠️ Failed to pull bot image"
docker pull mysql:8.0 || echo "⚠️ Failed to pull MySQL image"
docker pull redis:7-alpine || echo "⚠️ Failed to pull Redis image"

echo "📋 בודק תוכן docker-compose.yml..."
ls -la docker-compose.yml
head -10 docker-compose.yml

echo "🚀 מפעיל את כל השירותים..."
docker-compose up -d --remove-orphans

echo "⏳ ממתין לאתחול השירותים (60 שניות)..."
sleep 60

echo "🔍 בדיקת סטטוס השירותים..."
docker-compose ps -a

echo "📊 בדיקת לוגים..."
docker-compose logs --tail=10 mysql || echo "MySQL logs not available"
docker-compose logs --tail=10 redis || echo "Redis logs not available"
docker-compose logs --tail=10 pirate-bot || echo "Bot logs not available"

echo "🌐 בדיקת פורטים פתוחים..."
netstat -tlnp | grep -E ":(3306|6379|8080)" || echo "Ports check failed"

ENDSSH

echo "🎉 פריסה אוטומטית הושלמה בהצלחה!"
echo "=================================="