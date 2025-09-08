# 🏴‍☠️ בוט תוכן הפיראטים

בוט טלגרם מתקדם לניהול בקשות תוכן עם יכולות מתקדמות.

## 🚀 פייפליין CI/CD אוטומטי

הפרויקט משתמש ב-GitHub Actions לבדיקות ופריסה אוטומטיות:

### שלבי הפייפליין:
1. **בדיקות** - מריץ בדיקות מקיפות עם MySQL ו-Redis
2. **בנייה** - בונה Docker image אם הבדיקות עברו
3. **פריסה** - מפרים אוטומטית לשרת הייצור

### סודות נדרשים:
הגדר את הסודות הבאים ב-GitHub repository שלך (`Settings > Secrets and variables > Actions`):

```
DOCKER_USERNAME=שם_המשתמש_שלך_ב_docker_hub
DOCKER_PASSWORD=סיסמת_docker_hub_שלך
SERVER_HOST=כתובת_IP_של_השרת
SERVER_USER=שם_המשתמש_בשרת
SERVER_SSH_KEY=מפתח_SSH_פרטי (מומלץ)
SERVER_PASSWORD=סיסמת_השרת (חלופה למפתח SSH)
```

### תהליך הפריסה:
1. Push לבראנץ' `master`
2. GitHub Actions מריץ בדיקות אוטומטית
3. אם הבדיקות עברו → בונה ומעלה Docker image
4. השרת מוריד את הקונטיינר החדש ומפעיל אותו

## 🧪 בדיקות מקומיות

```bash
# הרצת בדיקות ספציפיות
cd pirate_content_bot
DB_HOST=localhost PYTHONPATH=. python tests/test_specific_requests.py
DB_HOST=localhost PYTHONPATH=. python test_commands.py
DB_HOST=localhost PYTHONPATH=. python tests/test_admin_commands.py

# הרצת כל הבדיקות
pytest
```

## 🐳 פקודות Docker

```bash
# בנייה מקומית
docker-compose build --no-cache

# הרצה מקומית
docker-compose up -d

# עצירת קונטיינרים מקומיים (כשהייצור רץ)
docker-compose down

# צפייה בלוגים
docker-compose logs -f
```

## 🔧 משתני סביבה

משתני הסביבה הנדרשים:

```env
BOT_TOKEN=טוקן_הבוט_מטלגרם
DB_HOST=כתובת_בסיס_הנתונים
DB_USER=שם_משתמש_בסיס_נתונים
DB_PASSWORD=סיסמת_בסיס_נתונים
ADMIN_IDS=מזהי_מנהלים_מופרדים_בפסיק
```

## 📊 תכונות

- זיהוי וניתוח בקשות מתקדם
- פאנל ניהול עם אנליטיקס
- יכולות חיפוש מתקדמות
- שידור הודעות
- ניהול משתמשים
- מעקב אחר מימוש בקשות

---

🤖 *פייפליין CI/CD אוטומטי מופעל על ידי GitHub Actions*