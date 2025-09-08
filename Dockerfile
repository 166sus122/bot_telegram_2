# בוט התמימים הפיראטים - Dockerfile מתקדם
FROM python:3.11-slim

# הגדרת משתני סביבה
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# יצירת משתמש לא-root לביטחון
RUN useradd --create-home --shell /bin/bash app

# התקנת dependencies מערכת
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# יצירת תיקית עבודה
WORKDIR /app

# העתקת requirements ראשון לשימוש ב-cache
COPY pirate_content_bot/requirements.txt .

# התקנת Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# העתקת כל הקוד
COPY pirate_content_bot /app/pirate_content_bot

# יצירת תיקיות נדרשות
RUN mkdir -p logs exports cache data && \
    chown -R app:app /app

# עבור למשתמש לא-root
USER app

# חשיפת פורט (אם נדרש לweb interface בעתיד)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# הגדרת volume לנתונים
VOLUME ["/app/data", "/app/logs", "/app/exports"]

# פקודת הפעלה
CMD ["python", "pirate_content_bot/main/pirate_bot_main.py"]