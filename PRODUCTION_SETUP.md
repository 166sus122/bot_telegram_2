# 🏴‍☠️ הוראות הפעלה לשרת הראשי - בוט התמימים הפיראטים

## 🚀 הפעלה מהירה

### שלב 1: הכנת משתני סביבה

צור קובץ `.env` בתיקיית השורש עם המשתנים הבאים:

```bash
# הגדרות בוט
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
MAIN_GROUP_ID=YOUR_GROUP_ID
LOG_CHANNEL_ID=YOUR_LOG_CHANNEL_ID
ADMIN_IDS=6562280181,OTHER_ADMIN_IDS

# הגדרות מסד נתונים
DB_PASSWORD=YOUR_SECURE_DB_PASSWORD
DB_ROOT_PASSWORD=YOUR_SECURE_ROOT_PASSWORD

# הגדרות אופציונליות
GRAFANA_PASSWORD=admin
```

### שלב 2: הפעלת המערכת

```bash
# שכפול הפרויקט
git clone https://github.com/YOUR_USERNAME/pirate-content-bot.git
cd pirate-content-bot

# הפעלת כל השירותים
docker-compose up -d

# בדיקת סטטוס
docker-compose ps
docker-compose logs pirate-bot
```

### שלב 3: אימות שהכל עובד

```bash
# בדיקת בריאות המערכת
docker-compose exec pirate-bot python -c "print('✅ Bot container is running')"

# בדיקת חיבור למסד נתונים
docker-compose exec mysql mysql -upirate_user -p$DB_PASSWORD pirate_content -e "SELECT 'Database connection OK' as status;"

# צפייה בלוגים
docker-compose logs -f pirate-bot
```

## 🔧 פתרון בעיות נפוצות

### שגיאת "Access denied for user"
```bash
# איפוס סיסמת המשתמש
docker-compose exec mysql mysql -uroot -p$DB_ROOT_PASSWORD -e "
ALTER USER 'pirate_user'@'%' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON pirate_content.* TO 'pirate_user'@'%';
FLUSH PRIVILEGES;"
```

### בוט לא מגיב
```bash
# בדיקת לוגים
docker-compose logs pirate-bot | tail -50

# הפעלה מחדש
docker-compose restart pirate-bot
```

### מסד הנתונים לא עולה
```bash
# בדיקת נפח דיסק
df -h

# ניקוי כשלים קודמים
docker-compose down
docker system prune -f
docker-compose up -d
```

## 🔄 עדכון לגרסה חדשה

```bash
# עצירת השירותים
docker-compose down

# משיכת עדכונים
git pull origin master

# בנייה מחדש והפעלה
docker-compose build --no-cache
docker-compose up -d

# בדיקת הגרסה החדשה
docker-compose logs pirate-bot | grep "Enhanced Pirate Bot initialized"
```

## 📊 מעקב ומוניטורינג

### לוגים חיים
```bash
# כל השירותים
docker-compose logs -f

# רק הבוט
docker-compose logs -f pirate-bot

# רק מסד הנתונים
docker-compose logs -f mysql
```

### סטטיסטיקות חיבור
```bash
# בדיקת שימוש CPU ו-RAM
docker stats

# בדיקת חיבורי מסד נתונים
docker-compose exec mysql mysql -uroot -p$DB_ROOT_PASSWORD -e "SHOW PROCESSLIST;"
```

## 🔐 אבטחה

### גיבוי מסד נתונים
```bash
# יצירת גיבוי יומי
docker-compose exec mysql mysqldump -uroot -p$DB_ROOT_PASSWORD pirate_content > backup_$(date +%Y%m%d).sql

# שחזור מגיבוי
docker-compose exec -i mysql mysql -uroot -p$DB_ROOT_PASSWORD pirate_content < backup_20250909.sql
```

### רוטציית לוגים
הלוגים נשמרים ב:
- `./logs/` - לוגי הבוט
- Docker logs - לוגי המערכת

## 🌟 תכונות חדשות

### ✅ מסד נתונים מתקדם
- Connection Pool עם 10-20 חיבורים במקביל
- מיגרציות אוטומטיות עם 11 שדרגות
- Redis cache למהירות מירבית
- גיבוי אוטומטי של נתונים

### ✅ בדיקות מקיפות
- 25 בדיקות אוטומטיות לכל הפונקציות
- וולידציה של דיוק מידע ופורמטים
- בדיקות טיפול בשגיאות

### ✅ ארכיטקטורה שירותים
- UserService - ניהול משתמשים
- RequestService - ניהול בקשות
- RatingService - מערכת דירוגים
- SearchService - חיפוש מתקדם

## ⚠️ הערות חשובות לשרת

1. **RAM**: מינימום 2GB RAM (מומלץ 4GB)
2. **דיסק**: מינימום 10GB פנויים
3. **רשת**: פורטים 3306 (MySQL), 6379 (Redis), 80/443 (HTTP/HTTPS)
4. **Docker**: גרסה 20.10+ עם Docker Compose V2

## 🆘 תמיכה

אם יש בעיות:
1. בדוק לוגים: `docker-compose logs pirate-bot`
2. בדוק משתני סביבה: `cat .env`
3. בדוק חיבור רשת: `docker-compose ps`
4. אתה יכול ליצור issue בגיטהאב

---
🤖 **נוצר עם Claude Code** - מערכת מתקדמת לניהול תוכן פיראטי