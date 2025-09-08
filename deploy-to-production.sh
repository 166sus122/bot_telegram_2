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
echo "🐳 מושך Docker image חדש מ-Docker Hub..."
docker login -u dov121212 -p dckr_pat_IuxreLSty0V83becfCRXSMB2lbU
docker pull dov121212/bot_telegram_2:latest || true
echo "🛑 עוצר קונטיינר קיים אם קיים..."
docker stop bot_telegram_2 || true
docker rm bot_telegram_2 || true
echo "🚀 מפעיל קונטיינר חדש..."
docker run -d --name bot_telegram_2 dov121212/bot_telegram_2:latest
ENDSSH

echo "🎉 פריסה אוטומטית הושלמה בהצלחה!"
echo "=================================="