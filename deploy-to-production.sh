#!/bin/bash
# 🚀 סקריפט פריסה מלא – מעצור דוקר מקומי ופריסה לייצור
# מותאם ל-GitHub repository: 166sus122/bot_telegram_2
# ודוקר מקומי + deploy לשרת דרך SSH עם סיסמה רגילה

set -e  # עצור אם יש שגיאה

echo "=================================="
echo "🚀 מתחיל תהליך פריסה לייצור..."
echo "=================================="

# 1️⃣ בדיקת מצב נוכחי
echo "📊 מצב נוכחי של הקונטיינרים:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2️⃣ שמירת שינויים ב-git
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️  יש שינויים לא שמורים. מוסיף commit אוטומטי..."
    git add .
    read -p "הזן הודעת commit: " commit_message
    if [[ -z "$commit_message" ]]; then
        commit_message="עדכון אוטומטי לפני פריסה"
    fi
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

# 4️⃣ Push ל-GitHub
echo "⬆️  מעלה את השינויים ל-GitHub..."
git push -u origin master

# 5️⃣ Docker build & push דרך GitHub Actions
echo "🔄 GitHub Actions ירוץ אוטומטית עכשיו:"
echo "https://github.com/166sus122/bot_telegram_2/actions"

# 6️⃣ Deploy לשרת דרך SSH עם סיסמה רגילה
echo "🔐 מחבר לשרת ומריץ deploy..."
ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" << 'ENDSSH'
echo "🐳 מושך Docker image חדש..."
docker pull dov121212/bot_telegram_2:latest || true
echo "🛑 עוצר קונטיינר קיים אם קיים..."
docker stop bot_telegram_2 || true
docker rm bot_telegram_2 || true
echo "🚀 מפעיל קונטיינר חדש..."
docker run -d --name bot_telegram_2 dov121212/bot_telegram_2:latest
ENDSSH

echo "🎉 פריסה הסתיימה בהצלחה!"
echo "=================================="
echo "✅ כל השלבים הושלמו בהצלחה!"
echo "=================================="