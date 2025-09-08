#!/bin/bash
# סקריפט פריסה מלא - מעצור דוקר מקומי ומעלה לייצור

echo "🚀 מתחיל תהליך פריסה לייצור..."
echo "=================================="

# שלב 1: בדיקת מצב נוכחי
echo "📊 בודק מצב נוכחי..."
echo "📍 תיקייה נוכחית: $(pwd)"
echo "🐳 קונטיינרים פעילים:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# שלב 2: וידוא שהשינויים שמורים ב-git
echo ""
echo "📝 בודק שינויים ב-git..."
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️  יש שינויים לא שמורים. שומר אותם..."
    git add .
    read -p "הזן הודעת commit: " commit_message
    if [[ -z "$commit_message" ]]; then
        commit_message="עדכון אוטומטי לפני פריסה"
    fi
    git commit -m "$commit_message"
else
    echo "✅ כל השינויים שמורים ב-git"
fi

# שלב 3: עצירת דוכרים מקומיים
echo ""
echo "🛑 עוצר דוכרים מקומיים..."
cd /home/dovber/pirate-content-bot/pirate_content_bot
if docker-compose ps | grep -q "Up"; then
    echo "📦 עוצר קונטיינרים מקומיים..."
    docker-compose down
    echo "🧹 מנקה קונטיינרים ישנים..."
    docker container prune -f
    echo "✅ דוכר מקומי נעצר בהצלחה"
else
    echo "ℹ️  דוכר מקומי כבר עצור"
fi

# שלב 4: חזרה לתיקייה הראשית ו-push
echo ""
echo "⬆️  מעלה ל-GitHub ומפעיל פייפליין..."
cd /home/dovber/pirate-content-bot

# בדיקה שיש remote
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "❌ שגיאה: לא הוגדר GitHub remote"
    echo "💡 הרץ: git remote add origin https://github.com/YOUR_USERNAME/pirate-content-bot.git"
    exit 1
fi

# Push ל-GitHub
echo "🔄 מעלה את כל השינויים ל-GitHub..."
git push -u origin master

echo ""
echo "🎉 תהליך הפריסה החל!"
echo "=================================="
echo "📋 מה קורה עכשיו:"
echo "   1. ✅ דוכר מקומי נעצר"
echo "   2. 🔄 GitHub Actions מתחיל לרוץ"
echo "   3. 🧪 מריץ את כל הבדיקות"
echo "   4. 🐳 בונה Docker image"
echo "   5. 📤 מעלה ל-Docker Hub"
echo "   6. 🚀 מפרים לשרת הייצור"
echo ""
echo "🔍 לעקוב אחר התהליך:"
echo "   GitHub Actions: https://github.com/YOUR_USERNAME/pirate-content-bot/actions"
echo ""
echo "⏰ זמן משוער: 3-5 דקות"
echo "✨ הבוט יעבוד על השרת בייצור בקרוב!"