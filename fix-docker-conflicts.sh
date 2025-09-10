#!/bin/bash
# סקריפט לפתרון התנגשויות Docker בשרת
# להרצה ידנית בשרת במקרה של בעיות

echo "🔧 פותר התנגשויות Docker ומנקה המערכת..."
echo "=============================================="

# צבעים
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# שלב 1: עצירת כל קונטיינרים של הפרויקט
print_step "עצירת כל קונטיינרים של הפרויקט..."

PROJECT_CONTAINERS="pirate-bot-main-2025 pirate-mysql pirate-redis pirate-nginx pirate-prometheus pirate-grafana"

for container in $PROJECT_CONTAINERS; do
    if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
        echo "עוצר קונטיינר: $container"
        docker stop "$container" 2>/dev/null || true
        docker rm -f "$container" 2>/dev/null || true
        print_success "קונטיינר $container נוקה"
    else
        echo "קונטיינר $container לא נמצא או כבר נוקה"
    fi
done

# שלב 2: ניקוי networks
print_step "ניקוי networks של הפרויקט..."

PROJECT_NETWORKS="pirate-content-network-2025"

for network in $PROJECT_NETWORKS; do
    if docker network ls --format "{{.Name}}" | grep -q "^${network}$"; then
        echo "מוחק network: $network"
        docker network rm "$network" 2>/dev/null || true
        print_success "Network $network נמחק"
    else
        echo "Network $network לא נמצא או כבר נמחק"
    fi
done

# שלב 3: ניקוי volumes יתומים (אבל שמירה על הנתונים)
print_step "זיהוי volumes..."

PROJECT_VOLUMES="pirate-mysql-data-2025 pirate-redis-data-2025 pirate-prometheus-data pirate-grafana-data"
FOUND_VOLUMES=""

for volume in $PROJECT_VOLUMES; do
    if docker volume ls --format "{{.Name}}" | grep -q "^${volume}$"; then
        FOUND_VOLUMES="$FOUND_VOLUMES $volume"
    fi
done

if [ -n "$FOUND_VOLUMES" ]; then
    print_warning "נמצאו volumes של הפרויקט:"
    echo "$FOUND_VOLUMES"
    print_warning "Volumes יישמרו כדי לא לאבד נתונים"
else
    print_success "לא נמצאו volumes של הפרויקט"
fi

# שלב 4: ניקוי images ישנים ובלתי מוגדרים
print_step "ניקוי images בלתי מוגדרים..."

DANGLING_IMAGES=$(docker images -f "dangling=true" -q 2>/dev/null || echo "")
if [ -n "$DANGLING_IMAGES" ]; then
    echo "מוחק images בלתי מוגדרים:"
    echo "$DANGLING_IMAGES" | xargs -r docker rmi -f 2>/dev/null || true
    print_success "Images בלתי מוגדרים נמחקו"
else
    print_success "אין images בלתי מוגדרים למחיקה"
fi

# שלב 5: ניקוי כללי של Docker
print_step "ניקוי כללי של מערכת Docker..."

docker system prune -f --volumes=false 2>/dev/null || true
print_success "ניקוי כללי הושלם"

# שלב 6: בדיקת המצב הנוכחי
print_step "בדיקת המצב הנוכחי..."

echo "📊 קונטיינרים פעילים:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "📊 Networks קיימים:"
docker network ls --format "table {{.Name}}\t{{.Driver}}"

echo ""
echo "📊 Volumes קיימים:"
docker volume ls --format "table {{.Name}}\t{{.Driver}}"

# שלב 7: הכנה לפריסה חדשה
print_step "הכנת המערכת לפריסה חדשה..."

# בדיקת קיום תיקייה
if [ -d "$HOME/pirate-content-bot" ]; then
    cd "$HOME/pirate-content-bot"
    
    # בדיקת קיום docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        print_success "קובץ docker-compose.yml נמצא"
        
        # בדיקת תקינות
        if docker-compose config >/dev/null 2>&1; then
            print_success "קובץ docker-compose.yml תקין"
        else
            print_error "קובץ docker-compose.yml לא תקין"
            docker-compose config
        fi
    else
        print_warning "קובץ docker-compose.yml לא נמצא"
        echo "הורד את הקובץ עם:"
        echo "curl -L https://raw.githubusercontent.com/166sus122/bot_telegram_2/master/docker-compose.yml -o docker-compose.yml"
    fi
    
    # בדיקת קובץ .env
    if [ -f ".env" ]; then
        print_success "קובץ .env נמצא"
    else
        print_warning "קובץ .env לא נמצא"
        echo "צור קובץ .env עם המשתנים הנדרשים"
    fi
    
else
    print_warning "תיקיית הפרויקט לא נמצאה"
    echo "צור תיקייה עם:"
    echo "mkdir -p \$HOME/pirate-content-bot"
fi

echo ""
echo "🎯 סיכום:"
echo "=========="
print_success "כל התנגשויות Docker נוקו בהצלחה"
print_success "המערכת מוכנה לפריסה חדשה"

echo ""
echo "📋 פקודות לפריסה ידנית:"
echo "========================"
echo "1. cd \$HOME/pirate-content-bot"
echo "2. docker-compose pull"
echo "3. docker-compose up -d --force-recreate"
echo ""

print_success "🎉 סקריפט ניקוי הושלם בהצלחה!"