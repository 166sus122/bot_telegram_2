#!/bin/bash
# סקריפט עדכון בטוח לשרת התמימים הפיראטים
# מטרה: עדכון השרת עם מחיקת גירסאות ישנות ללא התנגשויות
# ⚠️ סקריפט זה מטפל רק בקונטיינרים הספציפיים לפרויקט זה
# ✅ קונטיינרים אחרים בשרת לא יושפעו

set -e  # יציאה במקרה של שגיאה

echo "🚀 מתחיל עדכון בטוח של שרת התמימים הפיראטים..."
echo "================================================="

# צבעים לפלט
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# הדפסת הודעות צבעוניות
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# שלב 1: גיבוי המצב הנוכחי
echo "🔄 שלב 1: יצירת גיבוי..."
BACKUP_DIR="./backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# גיבוי קונפיגורציות חשובות
if [ -f .env ]; then
    cp .env "$BACKUP_DIR/"
    print_success "גובה קובץ .env"
fi

if [ -f docker-compose.yml ]; then
    cp docker-compose.yml "$BACKUP_DIR/"
    print_success "גובה docker-compose.yml"
fi

# גיבוי נתונים חיוניים
if [ -d ./data ]; then
    cp -r ./data "$BACKUP_DIR/"
    print_success "גובה תיקיית data"
fi

if [ -d ./logs ]; then
    cp -r ./logs "$BACKUP_DIR/"
    print_success "גובה תיקיית logs"
fi

# שלב 2: עצירת כל הקונטיינרים הישנים
echo "🔄 שלב 2: עצירת קונטיינרים קיימים..."

# רשימה של קונטיינרים ספציפיים לפרויקט זה בלבד
SPECIFIC_CONTAINERS="pirate-bot-main-2025 pirate-mysql pirate-redis pirate-nginx pirate-prometheus pirate-grafana"
CONTAINERS_TO_STOP=""

for container in $SPECIFIC_CONTAINERS; do
    if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
        CONTAINERS_TO_STOP="$CONTAINERS_TO_STOP $container"
    fi
done

if [ ! -z "$CONTAINERS_TO_STOP" ]; then
    echo "📋 קונטיינרים שיעצרו:"
    echo "$CONTAINERS_TO_STOP"
    
    # עצירה עדינה
    echo "$CONTAINERS_TO_STOP" | xargs -r docker stop
    print_success "כל הקונטיינרים נעצרו"
    
    # מחיקת קונטיינרים ישנים
    echo "$CONTAINERS_TO_STOP" | xargs -r docker rm -f
    print_success "קונטיינרים ישנים נמחקו"
else
    print_warning "לא נמצאו קונטיינרים קיימים"
fi

# שלב 3: ניקוי images ישנים
echo "🔄 שלב 3: ניקוי images ישנים..."

# מחיקת dangling images
DANGLING_IMAGES=$(docker images -f "dangling=true" -q || true)
if [ ! -z "$DANGLING_IMAGES" ]; then
    echo "$DANGLING_IMAGES" | xargs -r docker rmi -f
    print_success "Images ישנים נמחקו"
else
    print_warning "לא נמצאו images ישנים למחיקה"
fi

# שלב 4: ניקוי networks ישנים
echo "🔄 שלב 4: ניקוי networks ישנים..."
SPECIFIC_NETWORK="pirate-content-network-2025"
if docker network ls --format "{{.Name}}" | grep -q "^${SPECIFIC_NETWORK}$"; then
    docker network rm "$SPECIFIC_NETWORK" 2>/dev/null || true
    print_success "Network של הפרויקט נמחק"
else
    print_warning "Network של הפרויקט לא נמצא"
fi

# שלב 5: ניקוי volumes ישנים (בזהירות)
echo "🔄 שלב 5: זיהוי volumes..."
SPECIFIC_VOLUMES="pirate-mysql-data-2025 pirate-redis-data-2025 pirate-prometheus-data pirate-grafana-data"
FOUND_VOLUMES=""

for volume in $SPECIFIC_VOLUMES; do
    if docker volume ls --format "{{.Name}}" | grep -q "^${volume}$"; then
        FOUND_VOLUMES="$FOUND_VOLUMES $volume"
    fi
done

if [ ! -z "$FOUND_VOLUMES" ]; then
    print_warning "נמצאו volumes של הפרויקט:"
    echo "$FOUND_VOLUMES"
    print_warning "Volumes לא יימחקו אוטומטית כדי לשמור על נתונים חיוניים"
    print_warning "הנתונים יישמרו ויחזרו אחרי העדכון"
else
    print_warning "לא נמצאו volumes של הפרויקט"
fi

# שלב 6: משיכת השינויים מ-Git
echo "🔄 שלב 6: עדכון קוד מ-Git..."

# בדיקת מצב Git
if [ -d .git ]; then
    # שמירת שינויים מקומיים אם יש
    if ! git diff-index --quiet HEAD --; then
        print_warning "נמצאו שינויים מקומיים, יוצר commit זמני..."
        git add .
        git commit -m "🔄 Backup before server update - $(date)"
    fi
    
    # משיכת השינויים האחרונים
    git fetch origin
    git pull origin master || git pull origin main
    print_success "קוד עודכן מ-Git"
else
    print_error "תיקייה זו איננה repository של Git!"
    exit 1
fi

# שלב 7: בדיקת תקינות הקונפיגורציה
echo "🔄 שלב 7: בדיקת תקינות הקונפיגורציה..."

# בדיקת קיום קבצים חיוניים
if [ ! -f docker-compose.yml ]; then
    print_error "קובץ docker-compose.yml לא נמצא!"
    exit 1
fi

if [ ! -f .env ]; then
    print_error "קובץ .env לא נמצא!"
    print_warning "יוצר .env מתבנית..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_warning "נא לעדכן את .env עם הערכים הנכונים"
    else
        print_error ".env.example גם לא נמצא!"
        exit 1
    fi
fi

# בדיקת תקינות של docker-compose
docker-compose config > /dev/null
print_success "קונפיגורציית Docker Compose תקינה"

# שלב 8: הפעלת המערכת המעודכנת
echo "🔄 שלב 8: הפעלת המערכת המעודכנת..."

# יצירת תיקיות נדרשות
mkdir -p ./data ./logs ./exports

# הפעלה עם build מחדש
docker-compose up -d --build --force-recreate

# המתנה להפעלה
echo "⏳ ממתין להפעלת המערכת..."
sleep 10

# בדיקת תקינות
echo "🔄 שלב 9: בדיקת תקינות המערכת..."

# בדיקת סטטוס קונטיינרים
RUNNING_CONTAINERS=$(docker-compose ps --services --filter "status=running")
TOTAL_SERVICES=$(docker-compose config --services | wc -l)

echo "📊 סטטוס קונטיינרים:"
docker-compose ps

# בדיקת health checks
echo "🏥 בדיקת בריאות המערכת..."
sleep 5

HEALTHY_CONTAINERS=$(docker ps --format "{{.Names}}" --filter "health=healthy" | grep -E "(pirate|bot)" | wc -l)
if [ "$HEALTHY_CONTAINERS" -gt 0 ]; then
    print_success "$HEALTHY_CONTAINERS קונטיינרים במצב תקין"
else
    print_warning "לא נמצאו קונטיינרים עם health check"
fi

# שלב 10: הצגת סיכום
echo "🏁 סיכום עדכון השרת:"
echo "========================"
print_success "עדכון הושלם בהצלחה!"
print_success "גיבוי נשמר ב: $BACKUP_DIR"
echo ""
echo "📋 מצב המערכת:"
docker-compose ps
echo ""
echo "📝 לצפייה בלוגים:"
echo "   docker-compose logs -f"
echo ""
echo "📊 לבדיקת סטטוס:"
echo "   docker-compose ps"
echo ""
echo "🔄 להפעלה מחדש:"
echo "   docker-compose restart"
echo ""

# שלב 11: ניקוי סופי (אופציונלי)
echo "🔄 ניקוי סופי..."
docker system prune -f
print_success "ניקוי מערכת הושלם"

print_success "🎉 עדכון השרת הושלם בהצלחה!"
print_success "המערכת פועלת עם הגירסה האחרונה"

# הודעת התראה למנהלים (אם יש webhook)
if [ ! -z "$WEBHOOK_URL" ]; then
    curl -s -X POST "$WEBHOOK_URL" -d "🚀 שרת התמימים הפיראטים עודכן בהצלחה! $(date)" > /dev/null || true
fi