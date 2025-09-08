# 🚀 פריסה מהירה לייצור

## לפני שמתחילים - הגדרות חד-פעמיות:

### 1. צור GitHub Repository
```bash
# ב-GitHub.com צור repository בשם: pirate-content-bot
# אחר כך:
git remote add origin https://github.com/YOUR_USERNAME/pirate-content-bot.git
```

### 2. הגדר Secrets ב-GitHub
`GitHub.com → Repository → Settings → Secrets and variables → Actions`

```
DOCKER_USERNAME = שם_המשתמש_שלך_ב_docker_hub
DOCKER_PASSWORD = סיסמה_או_token_של_docker_hub
SERVER_HOST = כתובת_IP_של_השרת_שלך
SERVER_USER = שם_משתמש_בשרת
SERVER_SSH_KEY = מפתח_SSH_פרטי (או SERVER_PASSWORD)
```

---

## 🎯 פריסה אוטומטית במטש אחד:

```bash
# הרץ פקודה אחת זו - והכל יקרה אוטומטית!
./deploy-to-production.sh
```

**זה יעשה:**
1. ✅ ישמור את כל השינויים ב-git
2. 🛑 יעצור את הדוכר המקומי
3. ⬆️ יעלה ל-GitHub
4. 🤖 יפעיל את GitHub Actions
5. 🧪 יריץ בדיקות
6. 🐳 יבנה Docker image
7. 🚀 יפרים לשרת
8. ✨ הבוט יעבוד בייצור!

---

## 📊 מעקב אחר התהליך:

- **GitHub Actions**: https://github.com/YOUR_USERNAME/pirate-content-bot/actions  
- **זמן משוער**: 3-5 דקות
- **סטטוס**: ירוק = הצלחה, אדום = כישלון

---

## 🔄 אם משהו השתבש:

```bash
# חזרה למצב מקומי
cd /home/dovber/pirate-content-bot/pirate_content_bot
docker-compose up -d

# בדיקת לוגים
docker-compose logs -f
```