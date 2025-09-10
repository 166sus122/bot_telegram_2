#!/bin/bash
# סקריפט לאבחון בעיות פריסה
# מטרה: זיהוי וחיבור בעיות נפוצות בפריסה לשרת

echo "🔍 מתחיל אבחון בעיות הפריסה..."
echo "======================================"

# צבעים
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}🔍 $1${NC}"
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

# בדיקה 1: Git ו-Repository
print_step "בדיקת Git Repository..."
if [ -d .git ]; then
    print_success "זוהי Git repository תקינה"
    
    # בדיקת remote
    REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "None")
    echo "Remote URL: $REMOTE_URL"
    
    # בדיקת branch
    CURRENT_BRANCH=$(git branch --show-current)
    echo "Current branch: $CURRENT_BRANCH"
    
    # בדיקת מצב
    if git diff-index --quiet HEAD --; then
        print_success "אין שינויים מקומיים"
    else
        print_warning "יש שינויים מקומיים שלא נשמרו"
        echo "שינויים:"
        git status --porcelain
    fi
    
    # בדיקת קישור לremote
    if git ls-remote origin HEAD >/dev/null 2>&1; then
        print_success "חיבור לremote repository תקין"
        
        # בדיקה אם יש עדכונים
        git fetch origin
        COMMITS_BEHIND=$(git rev-list --count HEAD..origin/$CURRENT_BRANCH 2>/dev/null || echo "0")
        if [ "$COMMITS_BEHIND" -gt 0 ]; then
            print_warning "הrepository מאחור ב-$COMMITS_BEHIND commits"
            echo "הרץ: git pull origin $CURRENT_BRANCH"
        else
            print_success "הrepository מעודכן"
        fi
    else
        print_error "אין חיבור לremote repository"
    fi
else
    print_error "זה לא Git repository!"
    echo "אולי אתה בתיקייה הלא נכונה?"
    exit 1
fi

# בדיקה 2: קבצים חיוניים
print_step "בדיקת קבצים חיוניים..."

REQUIRED_FILES=(
    "docker-compose.yml"
    ".env"
    "update-server-safely.sh"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "קובץ $file קיים"
    else
        print_error "קובץ $file חסר!"
    fi
done

# בדיקת הרשאות סקריפט
if [ -x "update-server-safely.sh" ]; then
    print_success "סקריפט העדכון בר-ביצוע"
else
    print_warning "סקריפט העדכון לא בר-ביצוע"
    echo "הרץ: chmod +x update-server-safely.sh"
fi

# בדיקה 3: Docker
print_step "בדיקת Docker..."

if command -v docker >/dev/null 2>&1; then
    print_success "Docker מותקן"
    
    # בדיקת הרשאות docker
    if docker ps >/dev/null 2>&1; then
        print_success "הרשאות Docker תקינות"
    else
        print_error "אין הרשאות Docker"
        echo "אולי צריך לרוץ עם sudo או להוסיף משתמש לקבוצת docker"
    fi
    
    # בדיקת docker-compose
    if command -v docker-compose >/dev/null 2>&1; then
        print_success "Docker Compose מותקן"
        
        # בדיקת תקינות קובץ
        if docker-compose config >/dev/null 2>&1; then
            print_success "קובץ docker-compose.yml תקין"
        else
            print_error "קובץ docker-compose.yml לא תקין!"
            echo "בדוק שגיאות:"
            docker-compose config
        fi
    else
        print_error "Docker Compose לא מותקן!"
    fi
else
    print_error "Docker לא מותקן!"
fi

# בדיקה 4: משתני סביבה
print_step "בדיקת משתני סביבה..."

if [ -f .env ]; then
    print_success "קובץ .env קיים"
    
    # בדיקת משתנים קריטיים
    CRITICAL_VARS=(
        "BOT_TOKEN"
        "DB_PASSWORD"
        "ADMIN_IDS"
    )
    
    for var in "${CRITICAL_VARS[@]}"; do
        if grep -q "^$var=" .env; then
            VALUE=$(grep "^$var=" .env | cut -d'=' -f2)
            if [ -n "$VALUE" ] && [ "$VALUE" != "your_value_here" ]; then
                print_success "משתנה $var מוגדר"
            else
                print_error "משתנה $var ריק או לא מוגדר!"
            fi
        else
            print_error "משתנה $var לא נמצא ב-.env!"
        fi
    done
else
    print_error "קובץ .env לא קיים!"
    if [ -f .env.example ]; then
        print_warning "נמצא .env.example - העתק אותו ועדכן:"
        echo "cp .env.example .env"
    fi
fi

# בדיקה 5: רשת וחיבורים
print_step "בדיקת רשת וחיבורים..."

# בדיקת חיבור אינטרנט
if ping -c 1 google.com >/dev/null 2>&1; then
    print_success "חיבור אינטרנט תקין"
else
    print_error "אין חיבור אינטרנט!"
fi

# בדיקת פורטים
PORTS_TO_CHECK=(3306 6379)
for port in "${PORTS_TO_CHECK[@]}"; do
    if netstat -ln | grep -q ":$port "; then
        print_warning "פורט $port כבר תפוס"
        echo "שירותים על פורט $port:"
        netstat -lnp | grep ":$port " || lsof -i :$port
    else
        print_success "פורט $port פנוי"
    fi
done

# בדיקה 6: מצב קונטיינרים קיימים
print_step "בדיקת קונטיינרים קיימים..."

RUNNING_CONTAINERS=$(docker ps --format "{{.Names}}" 2>/dev/null || echo "")
if [ -n "$RUNNING_CONTAINERS" ]; then
    print_warning "קונטיינרים פעילים:"
    echo "$RUNNING_CONTAINERS"
    
    # בדיקת קונטיינרים של הפרויקט
    PROJECT_CONTAINERS=$(echo "$RUNNING_CONTAINERS" | grep -E "(pirate|bot)" || echo "")
    if [ -n "$PROJECT_CONTAINERS" ]; then
        print_warning "קונטיינרים של הפרויקט שעדיין רצים:"
        echo "$PROJECT_CONTAINERS"
        echo "אולי צריך לעצור אותם לפני העדכון"
    fi
else
    print_success "אין קונטיינרים פעילים"
fi

# בדיקה 7: מקום פנוי בדיסק
print_step "בדיקת מקום פנוי בדיסק..."

DISK_USAGE=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 85 ]; then
    print_success "מספיק מקום בדיסק (${DISK_USAGE}% בשימוש)"
else
    print_error "מעט מקום בדיסק (${DISK_USAGE}% בשימוש)"
    echo "שקול לנקות קבצים או docker images ישנים"
fi

# בדיקה 8: זכרון מערכת
print_step "בדיקת זכרון מערכת..."

MEMORY_USAGE=$(free | awk 'NR==2 {printf "%.0f", ($3/$2)*100}')
if [ "$MEMORY_USAGE" -lt 85 ]; then
    print_success "מספיק זכרון (${MEMORY_USAGE}% בשימוש)"
else
    print_warning "זכרון גבוה (${MEMORY_USAGE}% בשימוש)"
fi

# סיכום והמלצות
echo ""
echo "🎯 סיכום ואבחון:"
echo "=================="

# ניתוח בעיות ופתרונות
echo ""
echo "💡 פתרונות לבעיות נפוצות:"
echo "=========================="

echo "1. אם Docker לא עובד:"
echo "   sudo systemctl start docker"
echo "   sudo usermod -aG docker \$USER  # ואז התחבר מחדש"

echo ""
echo "2. אם יש בעיות רשת בקונטיינרים:"
echo "   docker network prune"
echo "   docker system prune -f"

echo ""
echo "3. אם images לא מתעדכנים:"
echo "   docker-compose pull"
echo "   docker-compose up -d --force-recreate"

echo ""
echo "4. אם יש בעיות הרשאות:"
echo "   sudo chown -R \$(whoami):\$(whoami) ."
echo "   chmod +x update-server-safely.sh"

echo ""
echo "5. אם .env לא תקין:"
echo "   cp .env.example .env"
echo "   # ערוך את .env עם הערכים הנכונים"

echo ""
echo "🚀 לביצוע עדכון מהיר:"
echo "git pull && docker-compose up -d --build"

echo ""
print_success "אבחון הושלם! בדוק את השגיאות למעלה ופתור אותן."