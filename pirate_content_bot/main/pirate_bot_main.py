#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בוט התמימים הפיראטים - מהדורה מתקדמת עם ארכיטקטורת Services
מערכת ניהול תוכן מתקדמת עם זיהוי חכם, מעקב ביצועים והתראות
"""

import os
import sys
import logging
import asyncio
import signal
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from contextlib import asynccontextmanager

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)

# טעינת הגדרות
from pirate_content_bot.main.config import *

# Core imports
try:
    from pirate_content_bot.core.content_analyzer import AdvancedContentAnalyzer
except ImportError:
    AdvancedContentAnalyzer = None

from pirate_content_bot.core.storage_manager import StorageManager

try:
    from pirate_content_bot.core.auto_response import AdvancedAutoResponseManager
except ImportError:
    AdvancedAutoResponseManager = None

# Services imports
from pirate_content_bot.services.request_service import RequestService

try:
    from pirate_content_bot.services.rating_service import RatingService
except ImportError:
    RatingService = None
try:
    from pirate_content_bot.services.notification_service import NotificationService
except ImportError:
    NotificationService = None

try:
    from pirate_content_bot.services.search_service import SearchService
except ImportError:
    SearchService = None

try:
    from pirate_content_bot.services.user_service import UserService
except ImportError:
    UserService = None

# Utils imports
try:
    from pirate_content_bot.utils.duplicate_detector import DuplicateDetector
except ImportError:
    DuplicateDetector = None

try:
    from pirate_content_bot.utils.validators import InputValidator
except ImportError:
    InputValidator = None
try:
    from pirate_content_bot.utils.keyboards import KeyboardBuilder
except ImportError:
    KeyboardBuilder = None

try:
    from pirate_content_bot.utils.cache_manager import CacheManager
except ImportError:
    CacheManager = None

# Database imports
try:
    from pirate_content_bot.database.connection_pool import DatabaseConnectionPool
except ImportError:
    DatabaseConnectionPool = None

try:
    from pirate_content_bot.database.models import RequestModel, UserModel, RatingModel
except ImportError:
    RequestModel = UserModel = RatingModel = None

# הגדרת logging מתקדם
def setup_advanced_logging():
    """הגדרת מערכת logging מתקדמת"""
    log_config = DEBUG_CONFIG
    
    # יצירת formatter מותאם
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)-20s | %(levelname)-8s | %(funcName)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # הגדרת handler עבור קובץ
    if log_config['log_rotation']['enabled']:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            'pirate_bot_advanced.log',
            maxBytes=log_config['log_rotation']['max_bytes'],
            backupCount=log_config['log_rotation']['backup_count'],
            encoding='utf-8'
        )
    else:
        file_handler = logging.FileHandler('pirate_bot_advanced.log', encoding='utf-8')
    
    file_handler.setFormatter(formatter)
    
    # הגדרת console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # הגדרת root logger
    logging.basicConfig(
        level=getattr(logging, log_config['log_level']),
        handlers=[file_handler, console_handler],
        force=True
    )
    
    # הגדרת רמות לוג ספציפיות
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

# הגדרת הלוגינג
setup_advanced_logging()
logger = logging.getLogger(__name__)

# הגדרת משתנים גלובליים לבדיקת זמינות רכיבים
SERVICES_AVAILABLE = True
UTILS_AVAILABLE = True  
DATABASE_AVAILABLE = USE_DATABASE

try:
    # בדיקת זמינות Services
    from services.request_service import RequestService
    from services.rating_service import RatingService
    from services.notification_service import NotificationService
    from services.search_service import SearchService
    from services.user_service import UserService
except ImportError as e:
    logger.warning(f"Some services not available: {e}")
    SERVICES_AVAILABLE = False

try:
    # בדיקת זמינות Utils
    from utils.duplicate_detector import DuplicateDetector
    from utils.validators import InputValidator
    from utils.keyboards import KeyboardBuilder
    from utils.cache_manager import CacheManager
except ImportError as e:
    logger.warning(f"Some utils not available: {e}")
    UTILS_AVAILABLE = False

class EnhancedPirateBot:
    """בוט התמימים הפיראטים המתקדם עם ארכיטקטורת Services"""
    
    def __init__(self):
        logger.info("🚀 Initializing Enhanced Pirate Bot with Services Architecture")
        
        # אתחול רכיבים בסיסיים
        self._init_core_components()
        
        # אתחול Utils (נדרש לפני Services)
        self._init_utils()
        
        # אתחול Services
        self._init_services()
        
        # יצירת Application
        self.application = self._create_application()
        
        # הגדרת handlers
        self._setup_handlers()
        
        # אתחול background tasks
        self._init_background_tasks()
        
        # הגדרת graceful shutdown
        self._setup_signal_handlers()
        
        logger.info("✅ Enhanced Pirate Bot initialized successfully")
    
    def _init_core_components(self):
        """אתחול רכיבים בסיסיים"""
        try:
            # חיבור לבסיס נתונים
            if USE_DATABASE:
                self.db_pool = DatabaseConnectionPool(DB_CONFIG)
            else:
                self.db_pool = None

            # מנהל Cache
            self.cache_manager = CacheManager(CACHE_CONFIG)

            # רכיבי ליבה
            self.storage = StorageManager()
            self.storage._init_database_with_pool()  # אתחול מסד הנתונים
            
            # אתחול בטוח של analyzer
            if AdvancedContentAnalyzer:
                self.analyzer = AdvancedContentAnalyzer()
            else:
                logger.warning("AdvancedContentAnalyzer not available - using basic mode")
                self.analyzer = None
                
            # אתחול בטוח של auto response
            if AdvancedAutoResponseManager:
                self.auto_response = AdvancedAutoResponseManager()
            else:
                logger.warning("AdvancedAutoResponseManager not available - using basic mode")
                self.auto_response = None

            logger.info("✅ Core components initialized")

        except Exception as e:
            logger.error(f"❌ Failed to start enhanced bot: {e}", exc_info=True)
            print(f"❌ שגיאה בהפעלת הבוט: {e}")
            print("💡 בדוק את הגדרות הטוקן והרשאות")
            raise

    
    def _init_services(self):
        """אתחול Services"""
        try:
            self.request_service = RequestService(
                storage_manager=self.storage,
                content_analyzer=self.analyzer,
                duplicate_detector=self.duplicate_detector,
                notification_callback=self._send_notification_to_user
            )
            
            self.rating_service = RatingService(
                storage_manager=self.storage
            )
            
            # NotificationService needs bot instance and admin_ids, we'll initialize it differently
            self.notification_service = None  # Will be initialized after application is created
            
            self.search_service = SearchService(
                storage_manager=self.storage,
                cache_manager=self.cache_manager
            )
            
            self.user_service = UserService(
                storage_manager=self.storage,
                notification_service=None  # Will be set later
            )
            
            logger.info("✅ Services initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            raise
    
    def _init_utils(self):
        """אתחול Utils"""
        try:
            self.duplicate_detector = DuplicateDetector()
            self.input_validator = InputValidator()
            self.keyboard_builder = KeyboardBuilder()
            
            logger.info("✅ Utils initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize utils: {e}")
            raise
    
    def _create_application(self) -> Application:
        """יצירת Telegram Application מתקדם"""
        try:
            builder = Application.builder()
            builder.token(BOT_TOKEN)
            
            # הגדרות ביצועים
            if PERFORMANCE_CONFIG['async_processing']:
                builder.concurrent_updates(PERFORMANCE_CONFIG['max_concurrent_requests'])
            
            # הגדרת timeout
            builder.connect_timeout(PERFORMANCE_CONFIG['request_timeout'])
            builder.read_timeout(PERFORMANCE_CONFIG['request_timeout'])
            
            app = builder.build()
            
            logger.info("✅ Telegram Application created")
            return app
            
        except Exception as e:
            logger.error(f"❌ Failed to create application: {e}")
            raise
    
    def _setup_handlers(self):
        """הגדרת handlers מתקדמים"""
        app = self.application
        
        try:
            # פקודות בסיסיות
            app.add_handler(CommandHandler("start", self.start_command))
            app.add_handler(CommandHandler("help", self.help_command))
            app.add_handler(CommandHandler("settings", self.settings_command))
            
            # פקודות בקשות
            app.add_handler(CommandHandler("request", self.request_command))
            app.add_handler(CommandHandler("req", self.request_command))
            app.add_handler(CommandHandler("my_requests", self.my_requests_command))
            app.add_handler(CommandHandler("myreq", self.my_requests_command))
            app.add_handler(CommandHandler("search", self.search_command))
            app.add_handler(CommandHandler("status", self.status_command))
            app.add_handler(CommandHandler("cancel", self.cancel_request_command))
            
            # פקודות זמינות לכולם
            app.add_handler(CommandHandler("pending", self.pending_command))
            app.add_handler(CommandHandler("p", self.pending_command))
            app.add_handler(CommandHandler("fulfill", self.fulfill_command))
            app.add_handler(CommandHandler("reject", self.reject_command))
            app.add_handler(CommandHandler("admin_stats", self.admin_stats_command))
            app.add_handler(CommandHandler("broadcast", self.broadcast_command))
            app.add_handler(CommandHandler("maintenance", self.maintenance_command))
            
            # פקודות מתקדמות
            app.add_handler(CommandHandler("analytics", self.analytics_command))
            app.add_handler(CommandHandler("export", self.export_command))
            app.add_handler(CommandHandler("backup", self.backup_command))
            
            # 🔥 פקודות מהירות למנהלים - shortcuts
            app.add_handler(CommandHandler("p", self.pending_command))           # /p = /pending
            app.add_handler(CommandHandler("f", self.fulfill_command))           # /f = /fulfill  
            app.add_handler(CommandHandler("r", self.reject_command))            # /r = /reject
            app.add_handler(CommandHandler("s", self.admin_stats_command))       # /s = /admin_stats
            app.add_handler(CommandHandler("a", self.analytics_command))         # /a = /analytics
            app.add_handler(CommandHandler("b", self.broadcast_command))         # /b = /broadcast
            app.add_handler(CommandHandler("m", self.maintenance_command))       # /m = /maintenance
            app.add_handler(CommandHandler("commands", self.admin_commands_command))  # /commands = help for admins
            
            # טיפול בהודעות - זיהוי חכם משופר
            app.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND & ~filters.UpdateType.EDITED,
                self.enhanced_message_handler
            ))
            
            # כפתורים
            app.add_handler(CallbackQueryHandler(self.enhanced_button_callback))
            
            # Error handler מתקדם
            app.add_error_handler(self.enhanced_error_handler)
            
            logger.info("✅ Handlers configured")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup handlers: {e}")
            raise
    
    def _init_background_tasks(self):
        """אתחול משימות רקע"""
        if BACKGROUND_TASKS_CONFIG['enabled']:
            self.background_tasks = []
            logger.info("🔄 Background tasks initialized")
    
    def _setup_signal_handlers(self):
        """הגדרת signal handlers לסגירה חלקה"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _is_admin(self, user_id: int) -> bool:
        """בדיקה מתקדמת אם משתמש הוא מנהל"""
        try:
            return user_id in ADMIN_IDS
        except Exception as e:
            self.logger.error(f"Error checking admin status for user {user_id}: {e}")
            return False
    
    async def _is_rate_limited(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """בדיקת הגבלות קצב מתקדמת"""
        if not RATE_LIMITING_CONFIG['enabled']:
            return False, None
        
        if self._is_admin(user_id):
            return False, None
        
        # Implementation של rate limiting
        try:
            is_allowed, remaining_time = await self.user_service.check_rate_limit(user_id)
            if is_allowed:
                # Not rate limited - allow the request
                return False, None
            else:
                # Rate limited - create proper message and block
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                if minutes > 0:
                    message = f"⏳ יותר מדי בקשות. נסה שוב בעוד {minutes} דקות ו-{seconds} שניות"
                else:
                    message = f"⏳ יותר מדי בקשות. נסה שוב בעוד {seconds} שניות"
                return True, message
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}")
            return False, None
    
    # ========================= פקודות בסיסיות =========================
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת התחלה מתקדמת"""
        user = update.effective_user
        
        try:
            # רישום המשתמש במערכת
            await self.user_service.register_or_update_user(user)
            
            # הודעת ברוכים הבאים מותאמת
            is_returning = await self.user_service.is_returning_user(user.id)
            
            if is_returning:
                welcome_text = f"""
🏴‍☠️ ברוך השב, {user.first_name}! 

🎉 שמח לראות אותך שוב בקהילת התמימים הפיראטים!
📊 סטטיסטיקות שלך: {await self.user_service.get_user_stats(user.id)}

🚀 מה חדש במערכת:
• זיהוי חכם משופר עם AI
• מהירות תגובה מוגברת
• ממשק חדש וידידותי

💬 פשוט כתוב מה אתה מחפש והבוט יטפל בשאר!
                """
            else:
                welcome_text = SYSTEM_MESSAGES['welcome']
            
            keyboard = self.keyboard_builder.get_main_menu_keyboard(is_admin=self._is_admin(user.id))
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            # התראה למנהלים על משתמש חדש
            if not is_returning and self.notification_service:
                await self.notification_service.notify_new_user(user)
            
            logger.info(f"👤 User {user.first_name} ({user.id}) started the bot")
            
        except Exception as e:
            logger.error(f"❌ Error in start command: {e}")
            await update.message.reply_text("❌ שגיאה בטעינת המערכת. נסה שוב עוד רגע.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת עזרה מתקדמת"""
        user = update.effective_user
        is_admin = self._is_admin(user.id)
        
        try:
            # עזרה מותאמת לרמת המשתמש
            help_data = await self.user_service.get_personalized_help(user.id, is_admin)
            
            keyboard = self.keyboard_builder.get_help_keyboard(is_admin)
            
            await update.message.reply_text(
                help_data['text'],
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"❌ Error in help command: {e}")
            await update.message.reply_text("❌ שגיאה בטעינת העזרה")
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת הגדרות משתמש"""
        user = update.effective_user
        
        try:
            user_settings = await self.user_service.get_user_settings(user.id)
            
            settings_text = f"""
⚙️ **ההגדרות שלך**

🔔 התראות: {'🟢 פעיל' if user_settings.get('notifications', True) else '🔴 כבוי'}
🎯 זיהוי אוטומטי: {'🟢 פעיל' if user_settings.get('auto_detection', True) else '🔴 כבוי'}
📊 מעקב סטטיסטיקות: {'🟢 פעיל' if user_settings.get('analytics', True) else '🔴 כבוי'}

🌐 שפה: {user_settings.get('language', 'עברית')}
📱 מצב תצוגה: {user_settings.get('display_mode', 'רגיל')}
            """
            
            keyboard = self.keyboard_builder.get_settings_keyboard(user_settings)
            
            await update.message.reply_text(
                settings_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"❌ Error in settings command: {e}")
            await update.message.reply_text("❌ שגיאה בטעינת ההגדרות")
    
    # ========================= הטיפול החכם המתקדם =========================
    
    async def enhanced_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """טיפול חכם בהודעות עם סינון מוקפד ואגרסיבי של הודעות לא רלוונטיות"""
        user = update.effective_user
        text = update.message.text
        chat_type = update.effective_chat.type
        
        try:
            # בדיקות בסיסיות
            is_limited, limit_message = await self._is_rate_limited(user.id)
            if is_limited:
                await update.message.reply_text(limit_message)
                return
            
            # ניקוי הטקסט
            clean_text = self._clean_and_normalize_text(text)
            text_lower = clean_text.lower()
            
            logger.info(f"📨 Message from {user.first_name} ({user.id}): '{clean_text[:100]}...'")
            
            # לוג לטלגרם רק עבור בקשות שיצרו רשומה בפועל (נעשה מאוחר יותר)
            
            # שלב 1: סינון אגרסיבי - אם זה לא נראה כמו בקשה, לא ממשיכים
            if not self._could_be_content_request(text_lower, clean_text):
                logger.debug(f"🚫 Filtered out non-request: '{clean_text[:50]}...'")
                return
            
            # שלב 2: זיהוי ברור של בקשות תוכן בלבד
            request_score = self._calculate_request_score(text_lower, clean_text)
            
            logger.info(f"🎯 Request score: {request_score}")
            
            # רק אם הניקוד גבוה מספיק, ממשיכים
            from pirate_content_bot.main.config import AUTO_RESPONSE_CONFIG
            threshold = AUTO_RESPONSE_CONFIG['confidence_threshold'] * 100  # המרה מ-0.25 ל-25
            if request_score < threshold:
                logger.debug(f"🚫 Score too low ({request_score} < {threshold}), ignoring")
                return
            
            # שלב 3: ניתוח מפורט רק לבקשות עם ניקוד גבוה
            detailed_analysis = self._analyze_high_score_request(text_lower, clean_text, request_score)
            
            # עיבוד רק אם זה באמת נראה כמו בקשה חזקה
            logger.info(f"Analysis: is_clear={detailed_analysis['is_clear_request']}, might_be={detailed_analysis['might_be_request']}, score={request_score}")
            
            if detailed_analysis['is_clear_request']:
                logger.info("Processing as clear request")
                await self._process_validated_request(update, user, text, detailed_analysis)
            elif detailed_analysis['might_be_request'] and request_score >= threshold:
                logger.info("Processing as possible request with confirmation")
                await self._ask_brief_confirmation(update, user, text, detailed_analysis)
            else:
                logger.info("Ignoring message - doesn't meet criteria")
            # אחרת - התעלמות מלאה
            
            # עדכון סטטיסטיקות
            await self.user_service.update_interaction_stats(user.id, 'message_processed')
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced message handler: {e}")
            # לא שולחים הודעת שגיאה למשתמש כדי לא להפריע
    
    async def _handle_high_confidence_request(self, update: Update, user, text: str, analysis: Dict):
        """טיפול בבקשות בוטחון גבוה"""
        try:
            # בדיקת כפילויות מתקדמת
            existing_requests = await self.request_service.get_pending_requests(
                category=analysis['category'],
                limit=50
            )
            duplicates = self.duplicate_detector.find_duplicates(
                analysis['title'], 
                existing_requests
            )
            
            if duplicates:
                # בחירת הכפילות הכי דומה
                best_match_id, similarity = duplicates[0]
                matching_request = next((req for req in existing_requests if req.get('id') == best_match_id), None)
                
                if matching_request:
                    duplicate_info = {
                        'found': True,
                        'request_id': best_match_id,
                        'title': matching_request.get('title', ''),
                        'status': matching_request.get('status', 'pending'),
                        'similarity': similarity * 100
                    }
                    await self._handle_duplicate_request(update, duplicate_info)
                    return
            
            # הצעת יצירת בקשה
            suggestion_text = f"""
🎯 **זיהיתי בקשת תוכן מתקדמת!**

📝 **{analysis['title']}**
📂 {CONTENT_CATEGORIES[analysis['category']]['name']}
🎯 ביטחון: {analysis['confidence']:.1f}%
⭐ עדיפות: {PRIORITY_LEVELS[analysis.get('priority', 'medium')]['name']}

האם ליצור בקשה רשמית עם הפרטים האלה?
            """
            
            keyboard = self.keyboard_builder.get_request_confirmation_keyboard(user.id, analysis)
            
            await update.message.reply_text(
                suggestion_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            # שמירה זמנית במעכת Cache
            cache_key = f"pending_request:{user.id}"
            cache_data = {
                'original_text': text,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat(),
                'chat_id': update.effective_chat.id
            }
            logger.info(f"💾 Saving to cache: {cache_key}")
            result = self.cache_manager.set(cache_key, cache_data, ttl=300)
            logger.info(f"💾 Cache save result: {result}")
            
            logger.info(f"💡 High confidence suggestion for user {user.id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling high confidence request: {e}")
            await update.message.reply_text("❌ שגיאה בעיבוד הבקשה")
    
    async def _handle_medium_confidence_request(self, update: Update, user, text: str, analysis: Dict):
        """טיפול בבקשות בוטחון בינוני"""
        try:
            ask_text = f"""
🤔 **האם זו בקשה לתוכן?**

נראה שאתה מחפש: **{analysis['title']}**
📂 {CONTENT_CATEGORIES[analysis['category']]['name']}
🎯 ביטחון: {analysis['confidence']:.1f}%

מה תרצה לעשות?
            """
            
            keyboard = self.keyboard_builder.get_maybe_request_keyboard(user.id)
            
            await update.message.reply_text(
                ask_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
            # שמירה זמנית
            maybe_cache_key = f"maybe_request:{user.id}"
            maybe_cache_data = {
                'original_text': text,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
            logger.info(f"💾 Saving to maybe cache: {maybe_cache_key}")
            maybe_result = self.cache_manager.set(maybe_cache_key, maybe_cache_data, ttl=300)
            logger.info(f"💾 Maybe cache save result: {maybe_result}")
            
            logger.info(f"❓ Medium confidence question for user {user.id}")
            
        except Exception as e:
            logger.error(f"❌ Error handling medium confidence request: {e}")
    
    async def _handle_duplicate_request(self, update: Update, duplicate_info: Dict):
        """טיפול בבקשות כפולות"""
        duplicate_text = f"""
⚠️ **נמצאה בקשה דומה קיימת**

🆔 בקשה #{duplicate_info['request_id']}
📝 {duplicate_info['title']}
📊 סטטוס: {duplicate_info['status']}
🎯 דמיון: {duplicate_info['similarity']:.1f}%

מה תרצה לעשות?
        """
        
        keyboard = self.keyboard_builder.get_duplicate_handling_keyboard(duplicate_info['request_id'])
        
        await update.message.reply_text(
            duplicate_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

    def _extract_message_source_info(self, update: Update) -> Dict[str, Any]:
        """חילוץ מידע על מקור ההודעה"""
        try:
            chat = update.effective_chat
            message = update.message
            
            source_info = {
                'message_id': message.message_id if message else 0,
                'chat_title': chat.title if chat.title else '',
                'source_location': str(chat.id),
            }
            
            # זיהוי סוג המקור
            if chat.type == 'private':
                source_info.update({
                    'source_type': 'private',
                    'thread_category': 'private'
                })
            elif chat.type in ['group', 'supergroup']:
                thread_id = getattr(message, 'message_thread_id', None)
                
                if thread_id:
                    source_info.update({
                        'source_type': 'thread',
                        'source_location': f"{chat.id}:{thread_id}",
                        'thread_id': thread_id
                    })
                else:
                    source_info.update({
                        'source_type': 'group',
                        'thread_category': 'general'
                    })
            else:
                source_info.update({
                    'source_type': 'unknown'
                })
            
            return source_info
            
        except Exception as e:
            logger.error(f"Error extracting message source info: {e}")
            return {
                'source_type': 'unknown',
                'source_location': '',
                'thread_category': 'general',
                'chat_title': '',
                'message_id': 0
            }

    def _format_source_info(self, request_info: Dict) -> str:
        """עיצוב מידע מקור ההודעה"""
        try:
            source_type = request_info.get('source_type', 'unknown')
            chat_title = request_info.get('chat_title', '')
            thread_category = request_info.get('thread_category', 'general')
            
            if source_type == 'private':
                return "📱 **מקור:** הודעה פרטית"
            elif source_type == 'thread':
                thread_names = {
                    'updates': 'עדכונים',
                    'series': 'סדרות', 
                    'movies': 'סרטים',
                    'software': 'תוכנות',
                    'books': 'ספרים',
                    'games': 'משחקים',
                    'apps': 'אפליקציות',
                    'spotify': 'ספוטיפיי'
                }
                thread_name = thread_names.get(thread_category, thread_category)
                return f"💬 **מקור:** נושא {thread_name}"
            elif source_type == 'group':
                return f"👥 **מקור:** צ'אט כללי"
            else:
                return "❓ **מקור:** לא ידוע"
                
        except Exception:
            return "❓ **מקור:** לא ידוע"

    def _validate_thread_location(self, update: Update, text: str) -> Dict[str, Any]:
        """בדיקת מיקום הבקשה לפי Thread ID"""
        try:
            # בדיקה אם מדובר בצ'אט פרטי
            if update.effective_chat.type == 'private':
                return {
                    'is_valid': True,
                    'thread_category': None,
                    'message': 'פרטי'
                }
            
            # קבלת Thread ID מההודעה
            thread_id = update.message.message_thread_id if hasattr(update.message, 'message_thread_id') else None
            
            # אם אין Thread ID, זה הצ'אט הכללי
            if thread_id is None:
                return {
                    'is_valid': True,
                    'thread_category': 'general',
                    'message': 'צ\'אט כללי'
                }
            
            # בדיקה לפי Thread ID
            thread_mapping = {v: k for k, v in self.config.THREAD_IDS.items() if v is not None}
            
            if thread_id in thread_mapping:
                category = thread_mapping[thread_id]
                return {
                    'is_valid': True,
                    'thread_category': category,
                    'thread_id': thread_id,
                    'message': f'נושא מתאים: {category}'
                }
            
            # Thread ID לא מוכר
            return {
                'is_valid': False,
                'thread_category': None,
                'thread_id': thread_id,
                'message': f'נושא לא מוכר: {thread_id}',
                'suggested_threads': self._get_suggested_threads_for_text(text)
            }
            
        except Exception as e:
            logger.error(f"Error in thread validation: {e}")
            # במקרה של שגיאה, נאשר את הבקשה כדי לא לחסום את המשתמש
            return {
                'is_valid': True,
                'thread_category': 'general',
                'message': 'שגיאה בבדיקת נושא - מאשר אוטומטית'
            }

    def _get_suggested_threads_for_text(self, text: str) -> Dict[str, int]:
        """הצעת נושא מתאים לפי תוכן הטקסט"""
        suggestions = {}
        text_lower = text.lower()
        
        # מיפוי מילות מפתח לקטגוריות
        keywords_mapping = {
            'movies': ['סרט', 'פילם', 'movie', 'film', 'cinema', 'סינמה'],
            'series': ['סדרה', 'עונה', 'פרק', 'series', 'season', 'episode', 'netflix', 'נטפליקס'],
            'software': ['תוכנה', 'תכנית', 'software', 'program', 'app', 'אפליקציה', 'crack', 'קראק'],
            'games': ['משחק', 'game', 'גיים', 'pc', 'ps4', 'ps5', 'xbox', 'steam'],
            'books': ['ספר', 'book', 'pdf', 'epub', 'קריאה', 'ebook'],
            'spotify': ['ספוטיפי', 'spotify', 'מוזיקה', 'music', 'שיר', 'אלבום', 'אמן'],
            'apps': ['אפליקציה', 'app', 'mobile', 'android', 'ios', 'יישום'],
            'updates': ['עדכון', 'update', 'חדש', 'new', 'גרסה', 'version']
        }
        
        # חיפוש התאמות
        for category, keywords in keywords_mapping.items():
            if any(keyword in text_lower for keyword in keywords):
                if category in self.config.THREAD_IDS:
                    suggestions[category] = self.config.THREAD_IDS[category]
        
        return suggestions

    async def _handle_wrong_thread(self, update: Update, user, thread_validation: Dict[str, Any]):
        """טיפול בבקשה בנושא שגוי"""
        try:
            current_thread = thread_validation.get('thread_id', 'לא ידוע')
            suggested_threads = thread_validation.get('suggested_threads', {})
            
            wrong_thread_text = f"""
❌ **בקשה במיקום שגוי**

📍 **נושא נוכחי:** {current_thread}
⚠️ נושא זה לא מיועד לבקשות תוכן

🎯 **נושאים מתאימים לבקשה שלך:**
"""
            
            # הוספת הצעות Thread
            if suggested_threads:
                for category, thread_id in suggested_threads.items():
                    category_names = {
                        'updates': '🔄 עדכונים',
                        'series': '📺 סדרות',
                        'software': '💻 תוכנות',
                        'books': '📚 ספרים',
                        'movies': '🎬 סרטים',
                        'spotify': '🎵 ספוטיפיי',
                        'games': '🎮 משחקים',
                        'apps': '📱 אפליקציות'
                    }
                    category_name = category_names.get(category, category)
                    wrong_thread_text += f"• {category_name} (נושא #{thread_id})\n"
            else:
                # הצגת כל הנושאים הזמינים
                wrong_thread_text += """
• 🔄 עדכונים (נושא #11432)
• 📺 סדרות (נושא #11418) 
• 💻 תוכנות (נושא #11415)
• 📚 ספרים (נושא #11423)
• 🎬 סרטים (נושא #11411)
• 🎵 ספוטיפיי (נושא #11422)
• 🎮 משחקים (נושא #11419)
• 📱 אפליקציות (נושא #11420)
"""
            
            wrong_thread_text += """
💡 **איך לעבור לנושא הנכון:**
1. לחץ על שם הקבוצה למעלה
2. בחר את הנושא המתאים
3. כתוב שוב את הבקשה שלך

🤖 **או פשוט תשלח לי הודעה פרטית!**
            """
            
            await update.message.reply_text(
                wrong_thread_text,
                parse_mode='Markdown'
            )
            
            logger.info(f"Rejected request from wrong thread: {current_thread} by user {user.id}")
            
        except Exception as e:
            logger.error(f"Error handling wrong thread: {e}")
            await update.message.reply_text(
                "❌ בקשה זו לא יכולה להיות מעובדת בנושא הנוכחי. אנא עבור לנושא המתאים או שלח הודעה פרטית."
            )

    async def _send_notification_to_user(self, user_id: int, message: str):
        """שליחת התראה למשתמש"""
        try:
            await self.application.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"📤 Notification sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")

    async def _log_to_telegram(self, message: str, log_type: str = "INFO"):
        """שליחת הודעת לוג לערוץ הלוגים בטלגרם"""
        try:
            if not hasattr(self, 'application') or not self.application:
                return
                
            log_channel_id = LOG_CHANNEL_ID
            if not log_channel_id:
                return
                
            # פורמט הודעת הלוג עם timestamp ואייקונים
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_icons = {
                "INFO": "ℹ️",
                "SUCCESS": "✅", 
                "WARNING": "⚠️",
                "ERROR": "❌",
                "NEW_REQUEST": "📝",
                "FULFILLED": "🎉",
                "REJECTED": "❌",
                "USER_ACTION": "👤",
                "ADMIN_ACTION": "👮‍♂️"
            }
            
            icon = log_icons.get(log_type, "📋")
            log_message = f"{icon} `{timestamp}`\n{message}"
            
            await self.application.bot.send_message(
                chat_id=log_channel_id,
                text=log_message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Failed to send log to Telegram channel: {e}")
    
    # ========================= פקודות בקשות מתקדמות =========================
    
    async def request_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת בקשת תוכן מתקדמת"""
        user = update.effective_user
        
        if not context.args:
            help_text = """
📝 **שימוש מתקדם ב-/request**

🎯 דרכים ליצירת בקשה:
• `/request <תיאור התוכן>` - בקשה ישירה
• פשוט כתוב מה אתה מחפש - זיהוי אוטומטי!

💡 **דוגמאות מושלמות:**
• `/request הסדרה Stranger Things עונה 4`
• `/request הסרט Top Gun Maverick 2022 4K`
• `/request המשחק Cyberpunk 2077 PC מקורק`
• `/request ספר Harry Potter בעברית PDF`

🤖 **הבוט יזהה אוטומטית:**
• קטגוריה (סדרה/סרט/משחק/ספר)
• רמת עדיפות
• איכות רצויה
• פלטפורמה

✨ פשוט כתוב את מה שאתה מחפש!
            """
            
            keyboard = self.keyboard_builder.get_request_help_keyboard()
            
            await update.message.reply_text(
                help_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            return
        
        # עיבוד הבקשה
        request_text = " ".join(context.args)
        await self._process_advanced_request(update, user, request_text)
    
    async def _process_advanced_request(self, update: Update, user, text: str):
        """עיבוד מתקדם של בקשת תוכן - מעודכן לשירותים החדשים"""
        try:
            # בדיקת תקינות הבקשה דרך Service
            validation_result = self.input_validator.validate_content_request(text)
            is_valid = validation_result['is_valid']
            error_msg = validation_result.get('error', '')
            if not is_valid:
                await update.message.reply_text(f"❌ {error_msg}")
                return
            
            # ניתוח מתקדם
            analysis = self.analyzer.analyze_request(text, user.id)
            
            if analysis['confidence'] < 20 or not analysis['title']:
                await update.message.reply_text(
                    "❌ לא הצלחתי לזהות בקשה ברורה.\n\n"
                    "💡 **טיפים לבקשה מושלמת:**\n"
                    "• ציין כותרת מלאה ומדויקת\n"
                    "• הוסף שנת יציאה אם ידועה\n"
                    "• לסדרות: ציין עונה ופרק\n"
                    "• ציין פלטפורמה או איכות\n\n"
                    "🎯 **דוגמה:** 'הסדרה Breaking Bad 2008 עונה 1 HD'\n\n"
                    "נסה שוב עם פרטים נוספים!"
                )
                return
            
            # בדיקת כפילויות מתקדמת דרך Service
            existing_requests = await self.request_service.get_pending_requests(
                category=analysis['category'],
                limit=50
            )
            duplicates = self.duplicate_detector.find_duplicates(
                analysis['title'], 
                existing_requests
            )
            
            if duplicates:
                # בחירת הכפילות הכי דומה
                best_match_id, similarity = duplicates[0]
                matching_request = next((req for req in existing_requests if req.get('id') == best_match_id), None)
                
                if matching_request:
                    duplicate_info = {
                        'found': True,
                        'request_id': best_match_id,
                        'title': matching_request.get('title', ''),
                        'status': matching_request.get('status', 'pending'),
                        'similarity': similarity * 100
                    }
                    await self._handle_duplicate_request(update, duplicate_info)
                    return
            
            # יצירת הבקשה דרך RequestService
            request_id = await self.request_service.create_request(
                user_data=user,
                content_text=text,
                analysis=analysis
            )
            
            # לוג לטלגרם על בקשה חדשה
            await self._log_to_telegram(
                f"**בקשה חדשה #{request_id}**\n" +
                f"👤 משתמש: {user.first_name} ({user.id})\n" +
                f"📝 תוכן: {text[:100]}{'...' if len(text) > 100 else ''}\n" +
                f"🏷️ קטגוריה: {analysis.get('category', 'כללי')}\n" +
                f"⚖️ עדיפות: {analysis.get('priority', 'רגילה')}",
                "NEW_REQUEST"
            )
            
            if request_id:
                request_result = {'success': True, 'request_id': request_id}
                
                confirmation_text = f"""
✅ **בקשה נוצרה בהצלחה במערכת המתקדמת!**

🆔 מספר: #{request_id}
📝 כותרת: {analysis['title']}
📂 קטגוריה: {CONTENT_CATEGORIES[analysis['category']]['name']}
⭐ עדיפות: {PRIORITY_LEVELS[analysis.get('priority', 'medium')]['name']}
🎯 ביטחון: {analysis['confidence']:.1f}%

📋 הבקשה נשלחה למנהלים עם עדיפות חכמה
🔔 תקבל התראה מיידית כשהבקשה תמולא
📊 המערכת תעקב אחר הסטטוס אוטומטית

💡 `/status {request_id}` - לבדיקת סטטוס
                """
                
                keyboard = self.keyboard_builder.get_request_created_keyboard(request_id)
                
                await update.message.reply_text(
                    confirmation_text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
                # הודעה למנהלים דרך Service
                if self.notification_service:
                    await self.notification_service.notify_admins_new_request(request_id, user, analysis)
                
                logger.info(f"✅ Request {request_id} created by {user.first_name} ({user.id})")
            
            else:
                await update.message.reply_text(f"❌ {request_result['error']}")
            
        except Exception as e:
            logger.error(f"❌ Error processing advanced request: {e}", exc_info=True)
            await update.message.reply_text("❌ שגיאה ביצירת הבקשה. נסה שוב מאוחר יותר")
    # ========================= פקודות מנהלים מתקדמות =========================
    
    async def pending_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """הצגת בקשות ממתינות - זמין לכולם"""
        user = update.effective_user
        is_admin = self._is_admin(user.id)
        
        try:
            # קבלת בקשות ממתינות דרך Service
            pending_requests = await self.request_service.get_pending_requests(
                limit=20 if is_admin else 10
            )
            
            if not pending_requests:
                if is_admin:
                    stats_text = """
📋 **אין בקשות ממתינות כרגע**

✅ כל הבקשות טופלו
                    """
                else:
                    stats_text = """
📋 **אין בקשות ממתينות כרגע**

🎉 הקהילה עדכנית! כל הבקשות טופלו
                    """
                await update.message.reply_text(stats_text, parse_mode='Markdown')
                return
            
            # תצוגה שונה למנהלים ומשתמשים רגילים
            if is_admin:
                response = f"📋 **בקשות ממתינות** ({len(pending_requests)}):\n\n"
                
                for req in pending_requests[:10]:
                    response += f"**#{req.get('id', '?')}** {req.get('title', 'ללא כותרת')[:50]}{'...' if len(req.get('title', '')) > 50 else ''}\n"
                    response += f"👤 {req.get('username', 'ללא שם')} | 📂 {req.get('category', 'כללי')}\n"
                    response += f"🎯 `/f {req.get('id', '?')}` | `/r {req.get('id', '?')}`\n\n"
                
                if len(pending_requests) > 10:
                    response += f"... ועוד {len(pending_requests) - 10} בקשות\n"
            else:
                # תצוגה ידידותית למשתמשים רגילים
                response = f"📋 **בקשות ממתינות בקהילה** ({len(pending_requests)}):\n\n"
                
                for req in pending_requests[:8]:
                    response += f"**#{req.get('id', '?')}** {req.get('title', 'ללא כותרת')[:60]}{'...' if len(req.get('title', '')) > 60 else ''}\n"
                    response += f"📂 {req.get('category', 'כללי')} | ⏳ ממתין\n\n"
                
                if len(pending_requests) > 8:
                    response += f"... ועוד {len(pending_requests) - 8} בקשות\n"
                
                response += "\n💡 רוצה לראות הבקשות שלך? `/myreq`"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error in pending command: {e}")
            if is_admin:
                await update.message.reply_text("❌ שגיאה בטעינת בקשות ממתינות")
            else:
                await update.message.reply_text("❌ שגיאה בטעינת רשימת הבקשות")
    
    async def fulfill_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """מילוי בקשה מתקדם - מנהלים"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ פקודה זמינה רק למנהלים")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📝 **שימוש מתקדם:**\n"
                "`/fulfill <מספר> [הערות]`\n\n"
                "💡 **דוגמאות:**\n"
                "• `/fulfill 123` - מילוי בסיסי\n"
                "• `/fulfill 123 הועלה לדרייב` - עם הערות\n"
                "• `/fulfill 123 איכות HD, תיקיית סדרות` - מפורט",
                parse_mode='Markdown'
            )
            return
        
        try:
            request_id = int(context.args[0])
            notes = " ".join(context.args[1:]) if len(context.args) > 1 else None
            admin_user = update.effective_user
            
            # מילוי דרך Service
            result = await self.request_service.fulfill_request(
                request_id=request_id,
                admin_user=admin_user,
                notes=notes
            )
            
            if result['success']:
                # לוג לטלגרם על מילוי בקשה
                await self._log_to_telegram(
                    f"**בקשה #{request_id} מולאה** ✅\n" +
                    f"👮‍♂️ מנהל: {admin_user.first_name} ({admin_user.id})\n" +
                    f"💬 הערות: {notes if notes else 'ללא הערות'}\n" +
                    f"👤 משתמש: {result.get('user_name', 'לא ידוע')}",
                    "FULFILLED"
                )
                
                success_text = f"""
✅ **בקשה #{request_id} מולאה בהצלחה!**

{"💬 הערות: " + notes if notes else "📦 ללא הערות נוספות"}

📊 **הביצועים שלך היום:**
• מילאת: {result.get('admin_stats', {}).get('fulfilled_today', 1)} בקשות
• דחית: {result.get('admin_stats', {}).get('rejected_today', 0)} בקשות
• סה"כ טופלו: {result.get('admin_stats', {}).get('total_today', 1)} בקשות
                """
                
                keyboard = self.keyboard_builder.get_fulfill_success_keyboard(request_id)
                
                await update.message.reply_text(
                    success_text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
                
                logger.info(f"✅ Request {request_id} fulfilled by admin {admin_user.id}")
                
            else:
                await update.message.reply_text(f"❌ {result['error']}")
                
        except ValueError:
            await update.message.reply_text("❌ מספר בקשה לא תקין")
        except Exception as e:
            logger.error(f"❌ Error in fulfill command: {e}")
            await update.message.reply_text("❌ שגיאה במילוי הבקשה")
    
    async def admin_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """סטטיסטיקות מנהלים מתקדמות"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ פקודה זמינה רק למנהלים")
            return
        
        try:
            # קבלת סטטיסטיקות בסיסיות
            pending_requests = await self.request_service.get_pending_requests()
            service_stats = self.request_service.get_service_stats()
            
            pending_count = len(pending_requests) if isinstance(pending_requests, list) else pending_requests.get('count', 0)
            
            stats_text = f"""
📊 **סטטיסטיקות מערכת**

⚡ **סטטוס נוכחי:**
• ממתינות: {pending_count} ⏳

🛠️ **מידע שירות:**
• מטמון בקשות: {service_stats.get('cache_size', 0)}
• מטמון משתמשים: {service_stats.get('user_cache_size', 0)}
• ניתוח זמין: {'✅' if service_stats.get('has_analyzer') else '❌'}
• זיהוי כפילויות: {'✅' if service_stats.get('has_duplicate_detector') else '❌'}

🎯 **מנהלים:**
• מספר מנהלים: {len(getattr(self, 'admin_ids', []))}
• פעיל כרגע: ✅
            """
            
            await update.message.reply_text(stats_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error in admin stats: {e}")
            await update.message.reply_text("❌ שגיאה בטעינת סטטיסטיקות")
    
    async def admin_commands_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """🔥 מדריך פקודות מהירות למנהלים"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ פקודה זמינה רק למנהלים")
            return
        
        commands_text = """🏴‍☠️ מדריך פקודות מנהלים - בוט התמימים הפיראטים

🔥 פקודות מהירות (מומלץ!):
• /p - בקשות ממתינות (pending)
• /f [מספר] [הערות] - מילוי בקשה (fulfill)  
• /r [מספר] [סיבה] - דחיית בקשה (reject)
• /s - סטטיסטיקות מנהלים (admin_stats)
• /a - אנליטיקס מתקדם (analytics)
• /b [הודעה] - שידור למשתמשים (broadcast)
• /m - מצב תחזוקה (maintenance)

📋 פקודות מלאות:
• /pending - רשימת בקשות ממתינות
• /fulfill [מספר] [הערות] - מילוי בקשה
• /reject [מספר] [סיבה] - דחיית בקשה  
• /admin_stats - סטטיסטיקות מערכת
• /analytics - דוחות אנליטיקס
• /broadcast [הודעה] - הודעה לכל המשתמשים
• /maintenance - הפעלת מצב תחזוקה
• /export - ייצוא נתונים
• /backup - גיבוי מסד נתונים

💡 דוגמאות שימוש:
• /f 123 נמצא בקטלוג, שולח לינק - מילוי בקשה 123
• /r 456 לא נמצא במאגר - דחיית בקשה 456
• /b עדכון חשוב: שירות זמינות 24/7 - שידור הודעה

⚡ טיפים מהירים:
• השתמש בפקודות הקצרות לעבודה מהירה
• /p ואז מספר בקשה = מילוי מיידי
• עבור לחץ גבוה: /p ← /f ← /p"""
        
        await update.message.reply_text(
            commands_text,
            disable_web_page_preview=True
        )
    
    # ========================= פקודות מתקדמות =========================
    
    async def analytics_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """פקודת אנליטיקס מתקדמת"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ פקודה זמינה רק למנהלים")
            return
        
        try:
            if not self.request_service:
                await update.message.reply_text("❌ שירות הבקשות אינו זמין")
                return
                
            analytics_data = await self.request_service.get_request_analytics(period_days=7)
            
            if not analytics_data:
                await update.message.reply_text("❌ שגיאה בטעינת נתוני אנליטיקס (או שאין חיבור ל-DB)")
                return
            
            basic_stats = analytics_data.get('basic_stats', {})
            category_stats = analytics_data.get('category_distribution', [])
            
            analytics_text = f"""
📈 **אנליטיקס מתקדם - שבוע אחרון**

📊 **סטטיסטיקות כלליות:**
• סה"כ בקשות: {basic_stats.get('total_requests', 0)}
• בקשות ממתינות: {basic_stats.get('pending', 0)}
• בקשות מולאו: {basic_stats.get('fulfilled', 0)}
• בקשות נדחו: {basic_stats.get('rejected', 0)}

🎯 **התפלגות קטגוריות:**
            """
            
            if category_stats and isinstance(category_stats, list):
                for category_data in category_stats[:5]:
                    if isinstance(category_data, dict):
                        category = category_data.get('category', 'לא ידוע')
                        count = category_data.get('count', 0)
                        analytics_text += f"• {category}: {count} בקשות\n"
            elif category_stats and isinstance(category_stats, dict):
                # Handle as dict (backward compatibility)
                for category, count in list(category_stats.items())[:5]:
                    analytics_text += f"• {category}: {count} בקשות\n"
            else:
                analytics_text += "• אין נתונים זמינים\n"
            
            response_times = analytics_data.get('response_times', {})
            top_users = analytics_data.get('top_users', [])
            
            analytics_text += f"""

⚡ **ביצועים:**
• זמן תגובה ממוצע: {response_times.get('avg_response_time', 0):.1f}h
• רמת שירות: {(basic_stats.get('fulfilled', 0) / max(basic_stats.get('total_requests', 1), 1) * 100):.1f}%

👥 **משתמשים פעילים:**
            """
            
            if top_users:
                for user in top_users[:3]:
                    analytics_text += f"• {user.get('username', 'ללא שם')}: {user.get('request_count', 0)} בקשות\n"
            else:
                analytics_text += "• אין נתונים זמינים\n"
            
            await update.message.reply_text(
                analytics_text,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"❌ Error in analytics command: {e}")
            await update.message.reply_text("❌ שגיאה בטעינת אנליטיקס")
    
    # ========================= כפתורים מתקדמים =========================
    
    async def enhanced_button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """טיפול מתקדם בכפתורים"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user = query.from_user
        
        logger.info(f"🔘 Enhanced button: {data} by {user.first_name} ({user.id})")
        
        try:
            # ניתוב מתקדם לפי סוג הכפתור
            if data.startswith("create_request:"):
                await self._handle_create_request_button(query, data)
            elif data.startswith("create_duplicate:"):
                await self._handle_create_duplicate_button(query, data)
            elif data.startswith("view_request:"):
                await self._handle_view_request_button(query, data)
            elif data.startswith("edit_request:"):
                await self._handle_edit_request_button(query, data)
            elif data.startswith("duplicate_action:"):
                await self._handle_duplicate_action_button(query, data)
            elif data.startswith("rate_request:"):
                await self._handle_rating_button(query, data)
            elif data.startswith("admin_action:"):
                await self._handle_admin_action_button(query, data)
            elif data.startswith("admin:"):
                await self._handle_admin_button(query, data)
            elif data.startswith("settings:"):
                await self._handle_settings_button(query, data)
            elif data.startswith("action:"):
                await self._handle_action_button(query, data)
            elif data == "dismiss":
                await query.edit_message_text("👍 בסדר!")
            else:
                await self._handle_generic_button(query, data)
                
        except Exception as e:
            logger.error(f"❌ Error in button callback: {e}")
            await query.edit_message_text("❌ שגיאה בעיבוד הכפתור")
    
    async def _handle_create_request_button(self, query, data: str):
        """טיפול בכפתור יצירת בקשה"""
        user = query.from_user
        user_id = user.id
        
        # קבלת הבקשה הזמנית מ-Cache
        pending_data = self.cache_manager.get(f"pending_request:{user_id}")
        
        if not pending_data:
            await query.edit_message_text("❌ הבקשה פגה. נסה לכתוב שוב מה אתה מחפש")
            return
        
        try:
            # יצירת הבקשה דרך Service
            request_id = await self.request_service.create_request(
                user_data=user,
                content_text=pending_data['original_text'],
                analysis=pending_data['analysis']
            )
            
            # לוג לטלגרם על בקשה חדשה
            await self._log_to_telegram(
                f"**בקשה חדשה #{request_id}** (אושרה)\n" +
                f"👤 משתמש: {user.first_name} ({user.id})\n" +
                f"📝 תוכן: {pending_data['original_text'][:100]}{'...' if len(pending_data['original_text']) > 100 else ''}\n" +
                f"🏷️ קטגוריה: {pending_data['analysis'].get('category', 'כללי')}",
                "NEW_REQUEST"
            )
            
            if request_id:
                result = {'success': True, 'request_id': request_id}
                
                success_text = f"""
✅ **בקשה נוצרה בהצלחה!**

📝 {pending_data['analysis']['title']}
🆔 מספר בקשה: #{request_id}
⏱️ זמן עיבוד צפוי: {result['estimated_processing_time']} שעות

🔔 תקבל הודעה מיידית כשהבקשה תמולא!
                """
                
                await query.edit_message_text(success_text, parse_mode='Markdown')
                
                # הודעה למנהלים
                if self.notification_service:
                    await self.notification_service.notify_admins_new_request(
                        request_id, user, pending_data['analysis']
                    )
                
                # ניקוי Cache
                self.cache_manager.delete(f"pending_request:{user_id}")
                
                logger.info(f"✅ Request {request_id} created from button by user {user_id}")
                
            else:
                await query.edit_message_text(f"❌ {result['error']}")
                
        except Exception as e:
            logger.error(f"❌ Error creating request from button: {e}")
            await query.edit_message_text("❌ שגיאה ביצירת הבקשה")

    async def _handle_edit_request_button(self, query, data: str):
        """טיפול בכפתור עריכת בקשה"""
        await query.edit_message_text("🚧 עריכת בקשות בפיתוח")
    
    async def _handle_duplicate_action_button(self, query, data: str):
        """טיפול בכפתור פעולות כפילויות"""
        await query.edit_message_text("🚧 ניהול כפילויות בפיתוח")
    
    async def _handle_rating_button(self, query, data: str):
        """טיפול בכפתור דירוג"""
        await query.edit_message_text("🚧 מערכת דירוג בפיתוח")
    
    async def _handle_create_duplicate_button(self, query, data: str):
        """טיפול בכפתור יצירת בקשה כפולה"""
        try:
            # חילוץ request_id מהנתונים
            request_id = data.split(":", 1)[1] if ":" in data else ""
            user = query.from_user
            user_id = user.id
            
            logger.info(f"🔄 User {user_id} chose to create duplicate request (original: {request_id})")
            
            # קבלת הנתונים הזמניים של המשתמש מה-Cache
            pending_data = self.cache_manager.get(f"pending_request:{user_id}")
            if not pending_data:
                await query.edit_message_text("❌ הבקשה לא נמצאה במטמון. נסה לכתוב שוב.")
                return
            
            # יצירת הבקשה למרות הכפילות
            analysis = pending_data.get('analysis', {})
            analysis['force_duplicate'] = True  # סימון שזה בכוונה כפילות
            
            # יצירת הבקשה דרך RequestService
            request_result = await self.request_service.create_request(
                user_data=user,
                content_text=pending_data['original_text'],
                analysis=analysis
            )
            
            if request_result:
                success_text = f"""
✅ **בקשה נוצרה בהצלחה!**

📝 {analysis.get('title', 'בקשה חדשה')}
🆔 מספר בקשה: #{request_result}
⚠️ הבקשה נוצרה למרות הדמיון לבקשה #{request_id}

🔔 תקבל הודעה כשהבקשה תמולא!
                """
                
                await query.edit_message_text(success_text, parse_mode='Markdown')
                
                # הודעה למנהלים על כפילות מכוונת
                if self.notification_service:
                    await self.notification_service.notify_admins_new_request(
                        request_result, user, analysis, is_duplicate=True, original_id=request_id
                    )
                
                # ניקוי Cache
                self.cache_manager.delete(f"pending_request:{user_id}")
                
                logger.info(f"✅ Duplicate request {request_result} created by user {user_id}")
                
            else:
                await query.edit_message_text("❌ שגיאה ביצירת הבקשה")
                
        except Exception as e:
            logger.error(f"❌ Error creating duplicate request: {e}")
            await query.edit_message_text("❌ שגיאה ביצירת בקשה כפולה")
    
    async def _handle_view_request_button(self, query, data: str):
        """טיפול בכפתור הצגת בקשה קיימת"""
        try:
            # חילוץ request_id מהנתונים
            request_id = data.split(":", 1)[1] if ":" in data else ""
            
            if not request_id:
                await query.edit_message_text("❌ מספר בקשה לא תקין")
                return
                
            logger.info(f"👀 Viewing request {request_id}")
            
            # קבלת פרטי הבקשה
            if self.request_service:
                request_details = await self.request_service.get_request_by_id(int(request_id))
                
                if request_details:
                    status_emoji = {
                        'pending': '⏳',
                        'fulfilled': '✅',
                        'rejected': '❌',
                        'in_progress': '🔄'
                    }.get(request_details.get('status', 'pending'), '❓')
                    
                    priority_emoji = {
                        'low': '🔵',
                        'medium': '🟡', 
                        'high': '🔴',
                        'urgent': '🚨'
                    }.get(request_details.get('priority', 'medium'), '🟡')
                    
                    request_text = f"""
👀 **פרטי בקשה #{request_id}**

📝 **כותרת:** {request_details.get('title', 'ללא כותרת')}
{status_emoji} **סטטוס:** {request_details.get('status', 'לא ידוע')}
{priority_emoji} **עדיפות:** {request_details.get('priority', 'בינונית')}
📂 **קטגוריה:** {request_details.get('category', 'כללי')}
👤 **מבקש:** {request_details.get('first_name', 'לא ידוע')}
📅 **נוצרה:** {request_details.get('created_at', 'לא ידוע')}

📄 **תיאור מלא:**
{request_details.get('original_text', 'אין תיאור')[:500]}
                    """
                    
                    if request_details.get('notes'):
                        request_text += f"\n\n💬 **הערות:** {request_details['notes']}"
                    
                    # כפתורים נוספים
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 חזור", callback_data="dismiss")]
                    ])
                    
                    await query.edit_message_text(
                        request_text, 
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
                    
                else:
                    await query.edit_message_text(f"❌ בקשה #{request_id} לא נמצאה")
                    
            else:
                await query.edit_message_text("❌ שירות הבקשות אינו זמין")
                
        except Exception as e:
            logger.error(f"❌ Error viewing request: {e}")
            await query.edit_message_text("❌ שגיאה בהצגת הבקשה")
    
    async def _handle_admin_action_button(self, query, data: str):
        """טיפול בכפתור פעולות מנהל"""
        await query.edit_message_text("🚧 פעולות מנהל בפיתוח")
    
    async def _handle_admin_button(self, query, data: str):
        """טיפול בכפתורי אדמין"""
        user = query.from_user
        admin_action = data.split(":", 1)[1] if ":" in data else ""
        
        logger.info(f"🔘 Admin button: {admin_action} by {user.first_name} ({user.id})")
        
        # בדיקת הרשאת מנהל
        if not self._is_admin(user.id):
            await query.edit_message_text("❌ אין לך הרשאות מנהל")
            return
        
        try:
            if admin_action == "pending":
                # הצגת בקשות ממתינות
                if self.request_service:
                    pending_requests = await self.request_service.get_pending_requests(limit=10)
                    if pending_requests:
                        text = "⏳ **בקשות ממתינות:**\n\n"
                        for req in pending_requests[:5]:  # הצג 5 ראשונות
                            text += f"🆔 #{req.get('id')} - {req.get('title', 'ללא כותרת')[:30]}\n"
                            text += f"👤 {req.get('user_first_name', 'לא ידוע')}\n"
                            text += f"📅 {req.get('category', 'כללי')}\n"
                            if req.get('created_at'):
                                text += f"⏰ {req.get('created_at')}\n"
                            text += "\n"
                        
                        if len(pending_requests) > 5:
                            text += f"... ועוד {len(pending_requests) - 5} בקשות\n\n"
                    else:
                        text = "✅ **אין בקשות ממתינות**\n\n"
                else:
                    text = "❌ שירות הבקשות לא זמין\n\n"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 רענן", callback_data="admin:pending")],
                    [InlineKeyboardButton("🏠 ראשי", callback_data="action:main_menu")]
                ])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
            elif admin_action == "stats":
                # הצגת סטטיסטיקות
                if self.request_service:
                    from datetime import datetime, timedelta
                    start_date = datetime.now() - timedelta(days=30)
                    stats = await self.request_service._get_basic_request_stats(start_date)
                    
                    if stats:
                        text = "📊 **סטטיסטיקות מערכת (30 ימים):**\n\n"
                        text += f"📋 סה\"כ בקשות: {stats.get('total_requests', 0)}\n"
                        text += f"⏳ ממתינות: {stats.get('pending', 0)}\n"
                        text += f"✅ מולאו: {stats.get('fulfilled', 0)}\n"
                        text += f"❌ נדחו: {stats.get('rejected', 0)}\n"
                        text += f"👥 משתמשים ייחודיים: {stats.get('unique_users', 0)}\n\n"
                        
                        total = stats.get('total_requests', 0)
                        if total > 0:
                            fulfilled_rate = (stats.get('fulfilled', 0) / total) * 100
                            text += f"📈 שיעור מילוי: {fulfilled_rate:.1f}%\n"
                            
                        avg_conf = stats.get('avg_confidence', 0)
                        if avg_conf:
                            text += f"🎯 ביטחון ממוצע: {avg_conf:.1f}%"
                    else:
                        text = "📊 אין נתוני סטטיסטיקה זמינים"
                else:
                    text = "❌ שירות הבקשות לא זמין"
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 רענן", callback_data="admin:stats")],
                    [InlineKeyboardButton("🏠 ראשי", callback_data="action:main_menu")]
                ])
                
                await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
            
            else:
                # פעולה לא מוכרת
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 ראשי", callback_data="action:main_menu")]])
                await query.edit_message_text(f"❌ פעולת מנהל לא מוכרת: {admin_action}", reply_markup=keyboard)
                
        except Exception as e:
            logger.error(f"❌ Error in admin button handler: {e}")
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 ראשי", callback_data="action:main_menu")]])
            await query.edit_message_text("❌ שגיאה בעיבוד פעולת המנהל", reply_markup=keyboard)
    
    async def _handle_settings_button(self, query, data: str):
        """טיפול בכפתור הגדרות"""
        await query.edit_message_text("🚧 הגדרות בפיתוח")
    
    async def _handle_generic_button(self, query, data: str):
        """טיפול בכפתור כללי"""
        user = query.from_user
        
        if data.startswith("confirm_request:"):
            parts = data.split(":")
            if len(parts) >= 3:
                request_id = parts[1]
                category = parts[2] if len(parts) > 2 else "general"
                
                await self._handle_confirm_request(query, user, request_id, category)
        else:
            await query.edit_message_text(f"לא מזוהה: {data}")

    async def _handle_confirm_request(self, query, user, request_id: str, category: str):
        """אישור בקשה"""
        user_id = user.id
        logger.info(f"🔍 Looking for pending data for user {user_id}")
        
        # נבדוק גם pending_request וגם maybe_request
        pending_data = self.cache_manager.get(f"pending_request:{user_id}")
        if not pending_data:
            pending_data = self.cache_manager.get(f"maybe_request:{user_id}")
            logger.info(f"📦 Found maybe_request data: {bool(pending_data)}")
        else:
            logger.info(f"📦 Found pending_request data: {bool(pending_data)}")
        
        if not pending_data:
            logger.warning(f"❌ No pending data found for user {user_id}")
            await query.edit_message_text("❌ פג תוקף")
            return
            
        try:
            created_request = await self.request_service.create_request(
                user_data=user,
                content_text=pending_data['original_text'],
                analysis=pending_data['analysis']
            )
            
            # לוג לטלגרם על בקשה חדשה
            await self._log_to_telegram(
                f"**בקשה חדשה #{created_request}** (אושרה מחדש)\n" +
                f"👤 משתמש: {user.first_name} ({user.id})\n" +
                f"📝 תוכן: {pending_data['original_text'][:100]}{'...' if len(pending_data['original_text']) > 100 else ''}",
                "NEW_REQUEST"
            )
            
            if created_request:
                await query.edit_message_text(f"✅ בקשה #{created_request} נוצרה!")
                
                # שליחת התראה למנהלים
                if self.notification_service:
                    try:
                        await self.notification_service.notify_admins_new_request(
                            request_id=created_request,
                            user=user,
                            analysis=pending_data['analysis']
                        )
                        logger.info(f"📢 Admin notification sent for request {created_request}")
                    except Exception as notify_error:
                        logger.error(f"❌ Failed to notify admins about request {created_request}: {notify_error}")
                
                # נקה את שני הסוגים של נתונים זמניים
                self.cache_manager.delete(f"pending_request:{user_id}")
                self.cache_manager.delete(f"maybe_request:{user_id}")
                logger.info(f"✅ Request {created_request} created and cache cleared")
            else:
                await query.edit_message_text("❌ שגיאה ביצירה")
                logger.error(f"❌ Failed to create request for user {user_id}")
                
        except Exception as e:
            logger.error(f"❌ Error confirming request: {e}")
            await query.edit_message_text("❌ שגיאה")
    
    async def _handle_action_button(self, query, data: str):
        """טיפול בכפתורי Action"""
        user = query.from_user
        action = data.split(":", 1)[1] if ":" in data else ""
        
        logger.info(f"🔘 Action button: {action} by {user.first_name} ({user.id})")
        
        try:
            if action == "main_menu":
                # הצגת תפריט ראשי
                is_admin = self._is_admin(user.id)
                keyboard = self.keyboard_builder.get_main_menu_keyboard(is_admin)
                
                welcome_text = "🏠 **תפריט ראשי**\n\n"
                welcome_text += "ברוכים הבאים למערכת ניהול התוכן המתקדמת!\n"
                welcome_text += "בחרו את הפעולה הרצויה:"
                
                await query.edit_message_text(
                    welcome_text, 
                    reply_markup=keyboard, 
                    parse_mode='Markdown'
                )
            
            elif action == "help":
                # הצגת עזרה
                is_admin = self._is_admin(user.id)
                help_data = await self.user_service.get_personalized_help(user.id, is_admin) if self.user_service else {}
                keyboard = self.keyboard_builder.get_help_keyboard(is_admin)
                
                help_text = help_data.get('text', "🆘 **מדריך השימוש**\n\nכתבו מה אתם מחפשים והמערכת תזהה אוטומטית!")
                
                await query.edit_message_text(
                    help_text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            
            elif action == "my_requests":
                # הצגת בקשות המשתמש
                keyboard = self.keyboard_builder.get_user_requests_keyboard()
                await query.edit_message_text(
                    "📋 **הבקשות שלי**\n\nכאן יוצגו הבקשות שלך",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            
            elif action == "stats":
                # הצגת סטטיסטיקות
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 ראשי", callback_data="action:main_menu")]])
                await query.edit_message_text(
                    "📊 **סטטיסטיקות**\n\nכאן יוצגו הסטטיסטיקות",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            
            elif action == "new_request":
                # תחילת בקשה חדשה
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 ראשי", callback_data="action:main_menu")]])
                await query.edit_message_text(
                    "📝 **בקשה חדשה**\n\nכתבו מה אתם מחפשים והמערכת תזהה אוטומטית את הקטגוריה!",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            
            elif action == "admin_panel" and self._is_admin(user.id):
                # פאנל מנהלים
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⏳ בקשות ממתינות", callback_data="admin:pending")],
                    [InlineKeyboardButton("📊 סטטיסטיקות", callback_data="admin:stats")],
                    [InlineKeyboardButton("🏠 ראשי", callback_data="action:main_menu")]
                ])
                await query.edit_message_text(
                    "👑 **פאנל מנהלים**\n\nבחרו פעולה:",
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            
            else:
                # פעולה לא מוכרת
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 ראשי", callback_data="action:main_menu")]])
                await query.edit_message_text(
                    f"❌ פעולה לא מוכרת: {action}",
                    reply_markup=keyboard
                )
                
        except Exception as e:
            logger.error(f"❌ Error in action button handler: {e}")
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 ראשי", callback_data="action:main_menu")]])
            await query.edit_message_text(
                "❌ שגיאה בעיבוד הפעולה",
                reply_markup=keyboard
            )
    
    # ========================= פונקציות עזר מתקדמות =========================
    
    def _might_be_request(self, text: str) -> bool:
        """זיהוי משופר אם זו אולי בקשה"""
        text_lower = text.lower()
        
        # מילות מפתח חזקות
        strong_indicators = [
            'רוצה את', 'מחפש את', 'צריך את', 'יש לכם את',
            'want', 'need', 'looking for', 'do you have'
        ]
        
        # מילות מפתח חלשות
        weak_indicators = [
            'רוצה', 'מחפש', 'צריך', 'אפשר', 'תן לי',
            'want', 'need', 'can you', 'give me'
        ]
        
        # קטגוריות תוכן
        content_indicators = [
            'סדרה', 'סרט', 'משחק', 'ספר', 'אפליקציה', 'תוכנה',
            'series', 'movie', 'game', 'book', 'app', 'software'
        ]
        
        strong_match = any(indicator in text_lower for indicator in strong_indicators)
        weak_match = any(indicator in text_lower for indicator in weak_indicators)
        content_match = any(indicator in text_lower for indicator in content_indicators)
        
        return strong_match or (weak_match and content_match)
    
    def _clean_and_normalize_text(self, text: str) -> str:
        """ניקוי וניירמול טקסט"""
        import re
        cleaned = re.sub(r'\s+', ' ', text.strip())
        cleaned = re.sub(r'@\w+', '', cleaned)
        return cleaned.strip()

    def _could_be_content_request(self, text_lower: str, original_text: str) -> bool:
        """סינון ראשוני אגרסיבי - רק דברים שבאמת יכולים להיות בקשות"""
        
        # אם ההודעה קצרה מדי - לא בקשה
        if len(text_lower) < 8:
            return False
        
        # אם יש פחות מ-2 מילים - לא בקשה
        if len(text_lower.split()) < 2:
            return False
        
        # סינון תגובות תודה/רגשיות מיד
        immediate_filters = [
            # תגובות תודה
            'תודה', 'טנקס', 'תנקס', 'thanks', 'thank you', 'תודה רבה',
            # תגובות רגשיות
            'וואו', 'ואו', 'אמאמא', 'יפה', 'מגניב', 'אחלה', 'מעולה',
            # תגובות קצרות
            'כן', 'לא', 'אוק', 'אוקיי', 'ok', 'okay', 'בסדר', 'טוב',
            # צחוק
            'חח', 'חחחח', 'ההה', 'lol', 'haha',
            # הודעות זמן
            'שניה', 'רגע', 'מיד', 'עכשיו אני',
            # שיחה אישית
            'אני בא', 'אני הולך', 'אתה בא', 'מה קורה', 'מה נשמע'
        ]
        
        # אם ההודעה מתחילה או מכילה רק דברים אלה - לא בקשה
        if any(text_lower.startswith(filter_word) for filter_word in immediate_filters):
            return False
        
        if text_lower in immediate_filters:
            return False
        
        # סינון אמוג'ים בלבד או כמעט
        import re
        if re.match(r'^[🫶❤️😘👍👌🔥💯⭐😊😎🎉🎊\s]*$', original_text):
            return False
        
        # סינון חזרות תווים
        if len(set(text_lower)) <= 3 and len(text_lower) > 5:
            return False
        
        # עכשיו בדיקה חיובית - חייבת להיות לפחות מילה אחת שמעידה על בקשה
        request_indicators = [
            'אפשר', 'יש', 'מחפש', 'רוצה', 'צריך', 'תן', 'איפה', 'מי יש',
            'can i get', 'do you have', 'looking for', 'i want', 'i need',
            'where is', 'who has', 'help me find'
        ]
        
        has_request_word = any(indicator in text_lower for indicator in request_indicators)
        
        # או לפחות מילה שמעידה על תוכן
        content_indicators = [
            'סרט', 'סדרה', 'משחק', 'ספר', 'תוכנה', 'אפליקצי', 'מוזיקה',
            'movie', 'series', 'game', 'book', 'software', 'app', 'music',
            'קורס', 'course', 'tutorial', 'מדריך'
        ]
        
        has_content_word = any(indicator in text_lower for indicator in content_indicators)
        
        # אם יש מילת בקשה, זה יכול להיות בקשה אפילו בלי מילת תוכן מפורשת
        # (למשל "אפשר את שובר שורות" או "אפשר את סופרמן")
        if has_request_word:
            return True
            
        # או אם יש מילת תוכן ברורה, גם זה יכול להיות בקשה
        if has_content_word:
            return True
        
        # ביטויים ספציפיים שמעידים על בקשה
        specific_patterns = [
            'שובר שורות', 'prison break', 'friends', 'avatar', 'superman', 'batman',
            'marvel', 'dc', 'netflix', 'amazon prime', 'disney+', 'hbo'
        ]
        
        has_specific_pattern = any(pattern in text_lower for pattern in specific_patterns)
        
        return has_specific_pattern

    def _calculate_request_score(self, text_lower: str, original_text: str) -> int:
        """חישוב ניקוד בקשה עם דגש על דיוק מקסימלי"""
        score = 0
        
        # מילות בקשה מפורשות - נקודות גבוהות רק לביטויים ברורים
        explicit_requests = [
            'אפשר את ה', 'אפשר את', 'יש את ה', 'יש את', 'מחפש את ה', 'מחפש את',
            'רוצה את ה', 'רוצה את', 'צריך את ה', 'צריך את', 'תן לי את',
            'איפה יש את', 'איפה הספר', 'איפה הסרט', 'איפה הסדרה', 'איפה המשחק',
            'can i get the', 'do you have the', 'looking for the', 'i want the',
            # הוספת ביטויים נוספים נפוצים - הורדת רף משמעותי
            'אפשר', 'יש לכם', 'מישהו יש', 'מי יש לו', 'חפש', 'need', 'want', 
            'יש', 'קיים', 'זמין', 'available', 'have', 'exists',
            'איפה', 'where', 'מוצא', 'find', 'locate'
        ]
        
        # ניקוד לביטויים - הפחתה לביטויים פשוטים
        high_score_phrases = [
            'אפשר את ה', 'אפשר את', 'יש את ה', 'יש את', 'מחפש את ה', 'מחפש את',
            'רוצה את ה', 'רוצה את', 'צריך את ה', 'צריך את', 'תן לי את'
        ]
        
        medium_score_phrases = [
            'אפשר', 'יש לכם', 'מישהו יש', 'מי יש לו', 'חפש', 
            'איפה', 'where', 'מוצא', 'find', 'locate'
        ]
        
        low_score_phrases = [
            'יש', 'קיים', 'זמין', 'available', 'have', 'exists', 'need', 'want'
        ]
        
        # ניקוד גבוה לביטויים מפורשים
        for phrase in high_score_phrases:
            if phrase in text_lower:
                score += 35
                break
        
        # ניקוד בינוני לביטויים כלליים
        for phrase in medium_score_phrases:
            if phrase in text_lower:
                score += 20
                break
                
        # ניקוד נמוך לביטויים פשוטים
        for phrase in low_score_phrases:
            if phrase in text_lower:
                score += 15
                break
        
        # קטגוריות תוכן ברורות
        clear_content_categories = {
            'entertainment': ['הסרט', 'הסדרה', 'netflix', 'disney', 'hbo', 'סרט', 'סדרה', 'movie', 'series', 'show', 'film'],
            'software': ['תוכנת', 'התוכנה', 'photoshop', 'office', 'windows', 'תוכנה', 'software', 'app', 'אפליקציה'],
            'gaming': ['המשחק', 'steam', 'ps4', 'ps5', 'xbox', 'nintendo', 'משחק', 'game'],
            'education': ['הקורס', 'tutorial', 'course', 'udemy', 'coursera', 'קורס', 'מדריך'],
            'books': ['הספר', 'pdf', 'epub', 'ebook', 'ספר', 'book'],
            'music': ['השיר', 'האלבום', 'mp3', 'flac', 'spotify', 'שיר', 'אלבום', 'מוזיקה', 'music'],
            'content_names': ['friends', 'avatar', 'superman', 'batman', 'marvel', 'שובר שורות', 'prison break', 'סופרמן', 'בטמן', 'איירון מן', 'iron man', 'הבלתי מנוצחים', 'avengers', 'ארץ הקסמים', 'wonderland']
        }
        
        category_found = False
        for category, keywords in clear_content_categories.items():
            if any(keyword in text_lower for keyword in keywords):
                score += 25
                category_found = True
                break
        
        # אם לא נמצאה קטגוריה ברורה - הורדת ניקוד קלה יותר
        if not category_found:
            score -= 5
        
        # בונוס לפרטים טכניים
        technical_details = ['2024', '2023', '2022', '2021', '2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011', '2010', '4k', '1080p', 'hd', 'crack', 'free']
        if any(detail in text_lower for detail in technical_details):
            score += 15
        
        # הפחתה חדה לסימנים של שיחה כללית
        casual_penalties = [
            'איך אתה', 'מה שלומך', 'מה קורה', 'איך היה', 'מה נשמע',
            'אני חושב', 'לדעתי', 'מה דעתך', 'אני מסכים'
        ]
        
        for penalty in casual_penalties:
            if penalty in text_lower:
                score -= 30
        
        # הפחתה אם ההודעה ארוכה מדי (יכולה להיות שיחה)
        if len(original_text) > 200:
            score -= 15
        
        # הפחתה רק אם יש הרבה מדי סימני שאלה (יכולה להיות שיחה מבולבלת)
        if original_text.count('?') > 3:
            score -= 10
        
        return max(0, score)

    def _analyze_high_score_request(self, text_lower: str, original_text: str, base_score: int) -> dict:
        """ניתוח מפורט רק להודעות עם ניקוד גבוה"""
        
        # זיהוי קטגוריה ספציפית
        categories = {
            'entertainment': ['סרט', 'סדרה', 'נטפליקס', 'דיסני', 'movie', 'series', 'netflix'],
            'software': ['תוכנה', 'תוכנת', 'photoshop', 'office', 'software'],
            'gaming': ['משחק', 'steam', 'playstation', 'xbox', 'game'],
            'education': ['קורס', 'שיעור', 'course', 'tutorial', 'udemy'],
            'books': ['ספר', 'pdf', 'ebook', 'book'],
            'music': ['שיר', 'אלבום', 'מוזיקה', 'music', 'song']
        }
        
        detected_category = 'general'
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_category = category
                break
        
        # קביעה אם זו בקשה ברורה
        clear_request_patterns = [
            r'אפשר\s+(את\s+)?ה?(סרט|סדרה|משחק|ספר|תוכנה)',
            r'יש\s+(את\s+)?ה?(סרט|סדרה|משחק|ספר|תוכנה)',
            r'מחפש\s+(את\s+)?ה?(סרט|סדרה|משחק|ספר|תוכנה)',
            r'(can\s+i\s+get|do\s+you\s+have).+(movie|series|game|book|software)',
            # דפוסים פשוטים יותר
            r'אפשר\s+\w+',  # "אפשר משהו"
            r'יש\s+\w+',    # "יש משהו"  
            r'איפה\s+\w+',  # "איפה משהו"
            r'מחפש\s+\w+',  # "מחפש משהו"
        ]
        
        import re
        is_clear_request = any(re.search(pattern, text_lower) for pattern in clear_request_patterns)
        
        # האם זה אולי בקשה (פחות ברור)
        might_be_request = (
            base_score >= 15 and 
            detected_category != 'general'
        ) or (
            base_score >= 30
        )
        
        return {
            'category': detected_category,
            'is_clear_request': is_clear_request,
            'might_be_request': might_be_request,
            'confidence': min(95, base_score),
            'original_score': base_score
        }
    
    def _generate_analytics_chart(self, data: Dict) -> str:
        """יצירת 'גרף' טקסטואלי לאנליטיקס"""
        # פונקציה פשוטה ליצירת ייצוג חזותי של נתונים
        chart_lines = []
        max_value = max(data.get('daily_requests', [1]))
        
        for day, requests in enumerate(data.get('daily_requests', [])):
            bar_length = int((requests / max_value) * 20) if max_value > 0 else 0
            bar = "█" * bar_length + "░" * (20 - bar_length)
            chart_lines.append(f"יום {day+1}: {bar} {requests}")
        
        return "\n".join(chart_lines)
    
    async def _process_validated_request(self, update: Update, user, text: str, analysis: dict):
        """עיבוד בקשה מאומתת בלבד"""
        try:
            # בדיקת Thread ID ומיקום הבקשה
            thread_validation = self._validate_thread_location(update, text)
            if not thread_validation['is_valid']:
                await self._handle_wrong_thread(update, user, thread_validation)
                return
            
            # יצירת ניתוח מפורט
            if self.analyzer:
                detailed_analysis = self.analyzer.analyze_advanced(text, user.id)
                detailed_analysis.update(analysis)
            else:
                # אם אין analyzer, נשתמש בניתוח הבסיסי
                detailed_analysis = analysis.copy()
                detailed_analysis.update({
                    'title': text[:50] if len(text) > 50 else text,
                    'category': 'general',
                    'confidence': 50
                })
            
            # עדכון קטגוריה לפי Thread ID
            if thread_validation['thread_category']:
                detailed_analysis['category'] = thread_validation['thread_category']
            
            # הוספת מידע מקור הודעה
            detailed_analysis.update(self._extract_message_source_info(update))
            
            # בדיקת כפילויות
            existing_requests = await self.request_service.get_pending_requests(
                category=analysis['category'],
                limit=50
            )
            
            duplicates = []
            if self.duplicate_detector:
                duplicates = self.duplicate_detector.find_duplicates(
                    detailed_analysis.get('title', text), 
                    existing_requests
                )
            
            if duplicates:
                # בחירת הכפילות הכי דומה
                best_match_id, similarity = duplicates[0]
                matching_request = next((req for req in existing_requests if req.get('id') == best_match_id), None)
                
                if matching_request:
                    duplicate_info = {
                        'found': True,
                        'request_id': best_match_id,
                        'title': matching_request.get('title', ''),
                        'status': matching_request.get('status', 'pending'),
                        'similarity': similarity * 100
                    }
                    await self._handle_duplicate_request(update, duplicate_info)
                    return
            
            # יצירת הבקשה
            request_id = await self.request_service.create_request(
                user_data=user, content_text=text, analysis=detailed_analysis
            )
            
            if request_id:
                request_result = {'success': True, 'request_id': request_id}
                await self._send_minimal_confirmation(update, request_result)
                if hasattr(self, 'notification_service') and self.notification_service:
                    await self.notification_service.notify_admins_new_request(
                        request_id, user, detailed_analysis
                    )
            else:
                await update.message.reply_text("❌ לא הצלחתי ליצור את הבקשה. נסה שוב מאוחר יותר.")
                
        except Exception as e:
            logger.error(f"❌ Error processing validated request: {e}")
            # לא שולחים הודעת שגיאה למשתמש

    async def _ask_brief_confirmation(self, update: Update, user, text: str, analysis: dict):
        """שאלת אישור קצרה ולעניין"""
        confirmation_text = f"""
🤔 **נראה שאתה מבקש תוכן**

"{text[:60]}{'...' if len(text) > 60 else ''}"

ליצור בקשה רשמית?
        """
        
        keyboard = self.keyboard_builder.get_maybe_request_keyboard(
            analysis.get('confidence', 0.5), 
            analysis.get('category', 'general')
        )
        
        await update.message.reply_text(
            confirmation_text,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        # שמירה זמנית במטמון
        brief_cache_key = f"maybe_request:{user.id}"
        
        # וודא שיש כותרת ב-analysis
        if 'title' not in analysis or not analysis.get('title'):
            analysis['title'] = text[:50] + ('...' if len(text) > 50 else '')
            
        brief_cache_data = {
            'original_text': text,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat(),
            'chat_id': update.effective_chat.id
        }
        logger.info(f"💾 Saving brief confirmation to cache: {brief_cache_key}")
        logger.info(f"💾 Analysis includes title: {analysis.get('title', 'MISSING')}")
        brief_result = self.cache_manager.set(brief_cache_key, brief_cache_data, ttl=300)
        logger.info(f"💾 Brief cache save result: {brief_result}")

    async def _send_minimal_confirmation(self, update: Update, request_result: dict):
        """אישור הצלחה מינימלי"""
        try:
            logger.info(f"Sending confirmation for request {request_result['request_id']}")
            confirmation_text = f"""
✅ **בקשה #{request_result['request_id']} נוצרה**

🔔 תקבל הודעה כשתמולא
💡 `/status {request_result['request_id']}` לבדיקה
            """
            
            await update.message.reply_text(confirmation_text, parse_mode='Markdown')
            logger.info(f"Confirmation sent for request {request_result['request_id']}")
        except Exception as e:
            logger.error(f"Failed to send confirmation: {e}")
    
    # ========================= Error Handling מתקדם =========================
    
    async def enhanced_error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """טיפול שגיאות מתקדם"""
        error = context.error
        
        logger.error(f"❌ Enhanced error occurred: {error}")
        
        try:
            if isinstance(update, Update) and update.effective_message:
                error_message = """
❌ **אירעה שגיאה במערכת**

🔧 המערכת עובדת על פתרון הבעיה
⏳ נסה שוב בעוד כמה דקות

🆘 אם הבעיה נמשכת, צור קשר עם המנהלים
                """
                
                await update.effective_message.reply_text(
                    error_message,
                    parse_mode='Markdown'
                )
            
            # דיווח שגיאה למנהלים
            if DEBUG_CONFIG['error_reporting']['enabled'] and self.notification_service:
                try:
                    # שליחת הודעת שגיאה למנהלים דרך notify_admins
                    error_msg = f"🚨 **שגיאה במערכת**\n📍 מיקום: {str(error)[:100]}"
                    await self.notification_service.notify_admins(
                        title="שגיאה מערכתית",
                        message=error_msg,
                        priority="high"
                    )
                except Exception as e:
                    logger.warning(f"Failed to notify admins about error: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error in error handler: {e}")
    
    # ========================= Background Tasks =========================
    
    async def start_background_tasks(self):
        """הפעלת משימות רקע"""
        if not BACKGROUND_TASKS_CONFIG['enabled']:
            return
        
        logger.info("🔄 Starting background tasks")
        
        tasks = [
            self._cleanup_task(),
            self._statistics_update_task(),
            self._notification_check_task(),
            self._duplicate_cleanup_task()
        ]
        
        self.background_tasks = [asyncio.create_task(task) for task in tasks]
    
    async def _cleanup_task(self):
        """משימת ניקוי תקופתית"""
        while True:
            try:
                await asyncio.sleep(BACKGROUND_TASKS_CONFIG['cleanup_interval'])
                
                # ניקוי בקשות ישנות
                cleaned = await self.request_service.cleanup_old_requests(
                    days=BACKGROUND_TASKS_CONFIG['old_requests_cleanup_days']
                )
                
                # ניקוי Cache
                self.cache_manager.cleanup()
                
                logger.info(f"🧹 Cleanup completed: {cleaned} items removed")
                
            except Exception as e:
                logger.error(f"❌ Error in cleanup task: {e}")
    
    async def _statistics_update_task(self):
        """משימת עדכון סטטיסטיקות"""
        while True:
            try:
                await asyncio.sleep(BACKGROUND_TASKS_CONFIG['statistics_update_interval'])
                
                # עדכון סטטיסטיקות
                await self.request_service.update_statistics()
                # עדכון analytics רק אם יש נתונים פעילים
                try:
                    # יכול להיות שנקרא update_user_analytics עם פרמטרים ספציפיים
                    # אבל כרגע זה לא נדרש במשימה רק פתית
                    pass  
                except Exception as e:
                    logger.warning(f"User analytics update skipped: {e}")
                
                logger.debug("📊 Statistics updated")
                
            except Exception as e:
                logger.error(f"❌ Error in statistics task: {e}")
    
    async def _notification_check_task(self):
        """משימת בדיקת התראות"""
        while True:
            try:
                await asyncio.sleep(BACKGROUND_TASKS_CONFIG['notification_check_interval'])
                
                # בדיקת התראות ממתינות רק אם השירות זמין
                if self.notification_service:
                    await self.notification_service.process_pending_notifications()
                
            except Exception as e:
                logger.error(f"❌ Error in notification task: {e}")
    
    async def _duplicate_cleanup_task(self):
        """משימת ניקוי כפילויות"""
        while True:
            try:
                await asyncio.sleep(BACKGROUND_TASKS_CONFIG['duplicate_cleanup_interval'])
                
                # ניקוי זיכרון הכפילויות
                await self.duplicate_detector.cleanup_cache()
                
                logger.debug("🔄 Duplicate cache cleaned")
                
            except Exception as e:
                logger.error(f"❌ Error in duplicate cleanup: {e}")
    
    # ========================= Graceful Shutdown =========================
    
    async def shutdown(self):
        """סגירה חלקה של המערכת"""
        logger.info("🛑 Initiating graceful shutdown")
        
        try:
            # עצירת background tasks
            if hasattr(self, 'background_tasks'):
                for task in self.background_tasks:
                    task.cancel()
                await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
            # שמירת מצב במטמון (אם השירות תומך בזה)
            if hasattr(self.cache_manager, 'save_state'):
                self.cache_manager.save_state()
            
            # סגירת חיבורי DB
            if self.db_pool:
                await self.db_pool.close()
            
            # עצירת האפליקציה
            await self.application.shutdown()
            
            logger.info("✅ Graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
    
    async def health_check(self) -> bool:
        """בדיקת תקינות המערכת"""
        try:
            # בדיקת חיבור לבסיס נתונים
            if self.db_pool:
                # TODO: implement test_connection method
                pass
            
            # בדיקת Cache
            # TODO: implement cache test
            pass
            
            # בדיקת Services
            services_ok = (
                self.request_service and
                self.user_service and
                self.notification_service
            )
            
            logger.info("✅ System health check passed")
            return services_ok
            
        except Exception as e:
            logger.error(f"❌ System health check failed: {e}")
            return False
    
    async def cleanup_resources(self):
        """ניקוי משאבים לפני סגירה"""
        try:
            # ניקוי Cache
            if hasattr(self, 'cache_manager'):
                # TODO: implement cleanup method
                pass
            
            # שמירת סטטיסטיקות אחרונות
            if hasattr(self, 'request_service'):
                # TODO: implement save_final_stats method
                pass
            
            logger.info("🧹 Resources cleaned up successfully")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up resources: {e}")
    
    async def _help_clarify_request(self, update: Update, user, text: str):
        """עזרה בהבהרת בקשה"""
        help_text = f"""
🤔 **נראה שאתה מחפש משהו, בואו נעזור לך לנסח את זה טוב יותר!**

📝 **מה כתבת:** "{text[:50]}..."

💡 **טיפים לבקשה מושלמת:**
• ציין בבירור מה אתה מחפש
• הוסף שנת יציאה אם ידועה
• לסדרות - ציין עונה ופרק
• למשחקים - ציין פלטפורמה

🎯 **דוגמאות טובות:**
• "הסדרה Friends עונה 1"
• "הסרט Avatar 2022"
• "המשחק FIFA 23 PS5"

נסה שוב עם פרטים נוספים! 😊
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def my_requests_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """הצגת בקשות המשתמש"""
        user = update.effective_user
        
        try:
            # השתמש ב-user_service לקבלת הבקשות
            user_requests = await self.user_service.get_user_requests(user.id, limit=10)
            
            if not user_requests:
                await update.message.reply_text(
                    "📋 עדיין לא יש לך בקשות במערכת\n\n"
                    "💡 כתוב מה אתה מחפש והבוט יטפל בשאר!"
                )
                return
            
            response = f"📋 **הבקשות שלך** ({len(user_requests)}):\n\n"
            
            for req in user_requests:
                status_emoji = {"pending": "⏳", "fulfilled": "✅", "rejected": "❌"}.get(req['status'], "❓")
                title = req['title'][:40] + ('...' if len(req['title']) > 40 else '')
                response += f"{status_emoji} **#{req['id']}** {title}\n"
                
                # עיבוד תאריך יצירה
                created_at = req['created_at']
                if isinstance(created_at, str):
                    from datetime import datetime
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
                response += f"📅 {created_at.strftime('%d/%m/%Y')} | 📂 {req['category']}\n\n"
            
            keyboard = self.keyboard_builder.get_user_requests_keyboard()
            
            await update.message.reply_text(
                response,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"❌ Error in my_requests command: {e}")
            await update.message.reply_text("❌ שגיאה בטעינת הבקשות שלך")
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """חיפוש בקשות - מנהלים בלבד"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ פקודה זמינה רק למנהלים")
            return
            
        if not context.args:
            await update.message.reply_text(
                "🔍 **שימוש בחיפוש:**\n"
                "`/search <מונח חיפוש>`\n\n"
                "💡 דוגמאות:\n"
                "• `/search Breaking Bad`\n"
                "• `/search סדרות`\n"
                "• `/search 2022`"
            )
            return
        
        search_term = " ".join(context.args)
        
        try:
            # השתמש ב-search_service - מחזיר tuple: (results, total_count, metadata)
            search_result = await self.search_service.search_requests(search_term, limit=10)
            results, total_count, metadata = search_result
            
            if not results:
                await update.message.reply_text(f"🔍 לא נמצאו תוצאות עבור: **{search_term}**")
                return
            
            response = f"🔍 **תוצאות חיפוש עבור:** {search_term}\n\n"
            
            for result in results[:5]:  # הגבל ל-5 תוצאות
                # Handle both dict and object results
                if isinstance(result, dict):
                    status = result.get('status', 'unknown')
                    result_id = result.get('id', 'N/A')
                    title = result.get('title', 'ללא כותרת')
                    created_at = result.get('created_at')
                    category = result.get('category', 'ללא קטגוריה')
                else:
                    status = getattr(result, 'status', 'unknown')
                    result_id = getattr(result, 'id', 'N/A')
                    title = getattr(result, 'title', 'ללא כותרת')
                    created_at = getattr(result, 'created_at', None)
                    category = getattr(result, 'category', 'ללא קטגוריה')
                
                status_emoji = {"pending": "⏳", "fulfilled": "✅", "rejected": "❌"}.get(status, "❓")
                response += f"{status_emoji} **#{result_id}** {title}\n"
                
                if created_at:
                    if hasattr(created_at, 'strftime'):
                        date_str = created_at.strftime('%d/%m/%Y')
                    else:
                        date_str = str(created_at)[:10]  # First 10 chars should be date
                    response += f"📅 {date_str} | 📂 {category}\n\n"
                else:
                    response += f"📂 {category}\n\n"
            
            if total_count > 5:
                response += f"... ועוד {total_count - 5} תוצאות\n"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"❌ Error in search command: {e}")
            await update.message.reply_text("❌ שגיאה בחיפוש")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """בדיקת סטטוס בקשה"""
        if not context.args:
            await update.message.reply_text(
                "📊 **שימוש בבדיקת סטטוס:**\n"
                "`/status <מספר בקשה>`\n\n"
                "💡 דוגמה: `/status 123`"
            )
            return
        
        try:
            request_id = int(context.args[0])
            request_info = await self.request_service.get_request_status(request_id)
            
            if not request_info:
                await update.message.reply_text(f"❌ לא נמצאה בקשה מספר #{request_id}")
                return
            
            status_emoji = {"pending": "⏳", "fulfilled": "✅", "rejected": "❌"}.get(request_info.get('status'), "❓")
            
            # המרת תאריך מ-string אם צריך
            created_at = request_info.get('created_at')
            if isinstance(created_at, str):
                try:
                    from datetime import datetime
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_str = created_at.strftime('%d/%m/%Y %H:%M')
                except:
                    date_str = str(created_at)
            elif hasattr(created_at, 'strftime'):
                date_str = created_at.strftime('%d/%m/%Y %H:%M')
            else:
                date_str = "לא ידוע"
            
            status_text = f"""
📊 **סטטוס בקשה #{request_id}**

{status_emoji} **סטטוס:** {request_info.get('status', 'לא ידוע')}
📝 **כותרת:** {request_info.get('title', 'ללא כותרת')}
📂 **קטגוריה:** {request_info.get('category', 'כללי')}
📅 **נוצרה:** {date_str}
            """
            
            # מידע נוסף
            priority_emoji = {"low": "🔵", "medium": "🟡", "high": "🔴", "urgent": "🚨"}.get(request_info.get('priority'), "🟡")
            
            # מקור ההודעה
            source_info = self._format_source_info(request_info)
            
            # זמן טיפול ממוצע אמיתי
            avg_processing = request_info.get('avg_processing_time', {})
            if avg_processing.get('sample_size', 0) > 0:
                avg_time = avg_processing.get('overall_avg', 24.0)
                processing_text = f"⏱️ **זמן טיפול ממוצע:** {avg_time:.1f} שעות (מבוסס על {avg_processing['sample_size']} בקשות)"
            else:
                processing_text = "⏱️ **זמן ממוצע לטיפול:** 24-48 שעות (הערכה)"
            
            status_text += f"""
{priority_emoji} **עדיפות:** {request_info.get('priority', 'בינונית')}
{source_info}
{processing_text}
            """
            
            if request_info.get('notes'):
                status_text += f"\n💬 **הערות:** {request_info.get('notes')}"
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
            
        except ValueError:
            await update.message.reply_text("❌ מספר בקשה לא תקין")
        except Exception as e:
            logger.error(f"❌ Error in status command: {e}")
            await update.message.reply_text("❌ שגיאה בבדיקת הסטטוס")
    
    async def cancel_request_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """ביטול בקשה"""
        if not context.args:
            await update.message.reply_text(
                "🚫 **שימוש בביטול בקשה:**\n"
                "`/cancel <מספר בקשה>`\n\n"
                "💡 דוגמה: `/cancel 123`"
            )
            return
        
        try:
            request_id = int(context.args[0])
            user = update.effective_user
            
            # בדוק אם הבקשה שייכת למשתמש
            result = await self.request_service.cancel_request(request_id, user.id)
            
            if result['success']:
                await update.message.reply_text(f"✅ בקשה #{request_id} בוטלה בהצלחה")
            else:
                await update.message.reply_text(f"❌ {result['error']}")
                
        except ValueError:
            await update.message.reply_text("❌ מספר בקשה לא תקין")
        except Exception as e:
            logger.error(f"❌ Error in cancel command: {e}")
            await update.message.reply_text("❌ שגיאה בביטול הבקשה")
    
    async def reject_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """דחיית בקשה - מנהלים"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ פקודה זמינה רק למנהלים")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📝 **שימוש מתקדם:**\n"
                "`/reject <מספר> [סיבת דחייה]`\n\n"
                "💡 **דוגמאות:**\n"
                "• `/reject 123 לא זמין`\n"
                "• `/reject 123 בקשה לא ברורה`",
                parse_mode='Markdown'
            )
            return
        
        try:
            request_id = int(context.args[0])
            reason = " ".join(context.args[1:]) if len(context.args) > 1 else "לא צויינה סיבה"
            admin_user = update.effective_user
            
            # דחיית הבקשה דרך Service
            result = await self.request_service.reject_request(
                request_id=request_id,
                admin_user=admin_user,
                reason=reason
            )
            
            if result['success']:
                # לוג לטלגרם על דחיית בקשה
                await self._log_to_telegram(
                    f"**בקשה #{request_id} נדחתה** ❌\n" +
                    f"👮‍♂️ מנהל: {admin_user.first_name} ({admin_user.id})\n" +
                    f"💬 סיבה: {reason}\n" +
                    f"👤 משתמש: {result.get('user_name', 'לא ידוע')}",
                    "REJECTED"
                )
                
                success_text = f"""
❌ **בקשה #{request_id} נדחתה**

💬 סיבת דחייה: {reason}

📊 **הביצועים שלך היום:**
• מילאת: {result.get('admin_stats', {}).get('fulfilled_today', 0)} בקשות
• דחית: {result.get('admin_stats', {}).get('rejected_today', 1)} בקשות
• סה"כ טופלו: {result.get('admin_stats', {}).get('total_today', 1)} בקשות
                """
                
                await update.message.reply_text(success_text, parse_mode='Markdown')
                logger.info(f"❌ Request {request_id} rejected by admin {admin_user.id}")
                
            else:
                await update.message.reply_text(f"❌ {result['error']}")
                
        except ValueError:
            await update.message.reply_text("❌ מספר בקשה לא תקין")
        except Exception as e:
            logger.error(f"❌ Error in reject command: {e}")
            await update.message.reply_text("❌ שגיאה בדחיית הבקשה")
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """שידור הודעה - מנהלים"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ פקודה זמינה רק למנהלים")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📢 **שימוש בשידור:**\n"
                "`/broadcast <הודעה לשידור>`\n\n"
                "⚠️ **זהירות:** ההודעה תשלח לכל המשתמשים הפעילים"
            )
            return
        
        message = " ".join(context.args)
        
        try:
            # בדיקה שהשירות זמין
            if not self.notification_service:
                await update.message.reply_text("❌ שירות השידורים אינו זמין כרגע")
                return
            
            # קבלת רשימת משתמשים פעילים
            try:
                active_users = await self.user_service.get_active_users(days=30) if self.user_service else []
            except Exception as e:
                self.logger.error(f"Error getting active users: {e}")
                active_users = []
            
            if not active_users:
                await update.message.reply_text("📢 לא נמצאו משתמשים פעילים לשידור (או שאין חיבור ל-DB)")
                return
            
            # שליחת ההודעה לכל המשתמשים הפעילים
            sent_count = 0
            failed_count = 0
            
            for user in active_users:
                try:
                    user_id = user.get('user_id') or user.get('id')
                    if user_id and user_id != update.effective_user.id:  # לא לשלוח למשלח
                        await self.notification_service.notify_user(
                            user_id=user_id,
                            title="📢 הודעת שידור",
                            message=message,
                            priority="medium"
                        )
                        sent_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.warning(f"Failed to send broadcast to user {user_id}: {e}")
            
            result_text = f"📢 שידור הסתיים:\n"
            result_text += f"• נשלח בהצלחה ל-{sent_count} משתמשים\n"
            if failed_count > 0:
                result_text += f"• נכשל לשלוח ל-{failed_count} משתמשים"
            
            # לוג פנימי בלבד - ללא שליחה לטלגרם למניעת ספאם
            logger.info(f"📢 Broadcast sent by {update.effective_user.first_name}: sent={sent_count}, failed={failed_count}")
            
            await update.message.reply_text(result_text)
            
        except Exception as e:
            logger.error(f"❌ Error in broadcast command: {e}")
            await update.message.reply_text("❌ שגיאה בשידור ההודעה")
    
    async def maintenance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """מצב תחזוקה - מנהלים"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ פקודה זמינה רק למנהלים")
            return
        
        if not context.args:
            await update.message.reply_text(
                "🔧 **מצב תחזוקה:**\n"
                "`/maintenance on` - הפעלת מצב תחזוקה\n"
                "`/maintenance off` - כיבוי מצב תחזוקה\n"
                "`/maintenance status` - בדיקת סטטוס"
            )
            return
        
        action = context.args[0].lower()
        
        if action == "on":
            # הפעל מצב תחזוקה
            self.cache_manager.set("maintenance_mode", True, ttl=3600)
            await update.message.reply_text("🔧 מצב תחזוקה הופעל")
            
        elif action == "off":
            # כבה מצב תחזוקה  
            self.cache_manager.delete("maintenance_mode")
            await update.message.reply_text("✅ מצב תחזוקה כובה")
            
        elif action == "status":
            # בדוק סטטוס
            is_maintenance = self.cache_manager.get("maintenance_mode")
            status = "🔧 פעיל" if is_maintenance else "✅ כבוי"
            await update.message.reply_text(f"מצב תחזוקה: {status}")
        
        else:
            await update.message.reply_text("❌ פעולה לא חוקית")
    
    async def export_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """יצוא נתונים - מנהלים"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ פקודה זמינה רק למנהלים")
            return
        
        await update.message.reply_text(
            "📊 **יצוא נתונים:**\n"
            "מכין קובץ יצוא... זה יכול לקחת כמה דקות"
        )
        
        try:
            import os
            admin_user_id = update.effective_user.id
            export_result = await self.request_service.export_data('json', admin_user_id)
            
            if export_result['success']:
                # שליחת הקובץ למנהל
                if export_result.get('file_path') and os.path.exists(export_result['file_path']):
                    with open(export_result['file_path'], 'rb') as f:
                        # שלח גם בתגובה וגם בהודעה פרטית למנהל
                        await update.message.reply_document(
                            document=f,
                            filename=export_result['filename'],
                            caption=f"📁 ייצוא נתונים: {export_result['records_count']} רשומות"
                        )
                        
                        # נסה לשלוח גם בפרטי למנהל
                        try:
                            f.seek(0)  # חזור לתחילת הקובץ
                            await context.bot.send_document(
                                chat_id=admin_user_id,
                                document=f,
                                filename=export_result['filename'],
                                caption=f"📁 ייצוא נתונים פרטי: {export_result['records_count']} רשומות"
                            )
                        except Exception as dm_error:
                            logger.warning(f"Could not send private export to admin: {dm_error}")
                    
                    # מחיקת הקובץ הזמני
                    try:
                        os.remove(export_result['file_path'])
                    except:
                        pass
                else:
                    await update.message.reply_text(
                        f"✅ יצוא הושלם!\n"
                        f"📁 {export_result['records_count']} רשומות\n"
                        f"📄 קובץ: {export_result['filename']}\n"
                        f"⚠️ לא ניתן היה ליצור קובץ זמני"
                    )
            else:
                await update.message.reply_text(f"❌ {export_result['error']}")
                
        except Exception as e:
            logger.error(f"❌ Error in export command: {e}")
            await update.message.reply_text("❌ שגיאה ביצוא הנתונים")
    
    async def backup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """גיבוי מערכת - מנהלים"""
        if not self._is_admin(update.effective_user.id):
            await update.message.reply_text("❌ פקודה זמינה רק למנהלים")
            return
        
        await update.message.reply_text("💾 מתחיל גיבוי מערכת...")
        
        try:
            backup_result = await self.request_service.create_backup()
            
            if backup_result['success']:
                await update.message.reply_text(
                    f"✅ גיבוי הושלם!\n"
                    f"📁 גודל: {backup_result['size']}\n"  
                    f"📄 קובץ: {backup_result['filename']}"
                )
            else:
                await update.message.reply_text(f"❌ {backup_result['error']}")
                
        except Exception as e:
            logger.error(f"❌ Error in backup command: {e}")
            await update.message.reply_text("❌ שגיאה בגיבוי המערכת")
    
    # ========================= הפעלה =========================
    
    async def setup_bot_commands(self):
        """הגדרת תפריט פקודות בוט"""
        
        # אתחול שירות ההתראות אחרי יצירת האפליקציה
        try:
            if self.notification_service is None and NotificationService is not None:
                self.notification_service = NotificationService(
                    bot_instance=self.application.bot,
                    admin_ids=ADMIN_IDS
                )
                logger.info("✅ NotificationService initialized successfully")
                
                # עדכון user_service עם שירות ההתראות
                if self.user_service and hasattr(self.user_service, 'notification_service'):
                    self.user_service.notification_service = self.notification_service
                    logger.info("✅ UserService updated with NotificationService")
                    
        except Exception as e:
            logger.error(f"❌ Failed to initialize NotificationService: {e}")
            
        commands = [
            BotCommand("start", "🏠 התחלה"),
            BotCommand("help", "🆘 עזרה"),
            BotCommand("request", "📝 בקשה חדשה"),
            BotCommand("my_requests", "📋 הבקשות שלי"),
            BotCommand("search", "🔍 חיפוש בקשות"),
            BotCommand("status", "📊 סטטוס בקשה"),
            BotCommand("settings", "⚙️ הגדרות"),
            BotCommand("commands", "🔥 פקודות מנהלים"),
        ]
        
        # פקודות מנהלים (מלאות + מהירות)
        admin_commands = [
            BotCommand("pending", "⏳ בקשות ממתינות"),
            BotCommand("admin_stats", "📊 סטטיסטיקות"),
            BotCommand("analytics", "📈 אנליטיקס"),
            BotCommand("commands", "🔥 מדריך פקודות מהירות"),
            # פקודות מהירות
            BotCommand("p", "⚡ בקשות ממתינות (מהיר)"),
            BotCommand("f", "⚡ מילוי בקשה (מהיר)"),
            BotCommand("r", "⚡ דחיית בקשה (מהיר)"),
            BotCommand("s", "⚡ סטטיסטיקות (מהיר)"),
            BotCommand("a", "⚡ אנליטיקס (מהיר)"),
        ]
        
        try:
            await self.application.bot.set_my_commands(commands)
            logger.info("✅ Bot commands configured")
        except Exception as e:
            logger.error(f"❌ Failed to set bot commands: {e}")
    
    def run(self):
        """הפעלת הבוט המתקדם"""
        logger.info("🚀 Starting Enhanced Pirate Content Bot")
        
        # הדפסת מידע אתחול
        self._print_startup_info()
        
        try:
            # בדיקת תקינות מערכת
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            health_ok = loop.run_until_complete(self.health_check())
            if not health_ok:
                print("⚠️ חלק מהמערכות לא תקינות, ממשיך בכל זאת...")
            
            # הגדרת פקודות בוט
            loop.run_until_complete(self.setup_bot_commands())
            
            # הפעלת משימות רקע בסיסיות
            loop.create_task(self.start_background_tasks())
            
            # הפעלת הבוט
            logger.info("🎬 Bot is now running!")
            
            # לוג פנימי על הפעלה - ללא שליחה לטלגרם למניעת ספאם
            # (הלוג נשמר רק בקבצי הלוג הפנימיים)
            
            self.application.run_polling(
                drop_pending_updates=True,
                close_loop=False
            )
            
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Critical error: {e}")
            print(f"❌ שגיאה קריטית: {e}")
        finally:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.shutdown())
            loop.run_until_complete(self.cleanup_resources())
            print("👋 תודה שהשתמשת בבוט התמימים הפיראטים המתקדם!")
    
    def _print_startup_info(self):
        """הדפסת מידע אתחול"""
        print("🏴‍☠️ בוט התמימים הפיראטים - מהדורה מתקדמת")
        print("=" * 65)
        print("🤖 ארכיטקטורת Services | 🧠 זיהוי AI משופר | 📊 אנליטיקס מתקדם")
        print("⚡ עיבוד אסינכרוני | 🗄️ מנהל Cache חכם | 🔒 אבטחה מתקדמת")
        print("🔔 התראות בזמן אמת | 📈 מעקב ביצועים | 🛠️ ניהול אוטומטי")
        print("=" * 65)
        
        config_info = [
            f"🤖 מנהלים: {len(ADMIN_IDS)}",
            f"📂 קטגוריות: {len(CONTENT_CATEGORIES)}",
            f"🗄️ DB: {'🟢 מחובר' if USE_DATABASE else '🟠 מקומי'}",
            f"💾 Cache: {'🟢 ' + CACHE_CONFIG['type'].title() if CACHE_CONFIG['enabled'] else '🔴 כבוי'}",
            f"🔄 Background: {'🟢 פעיל' if BACKGROUND_TASKS_CONFIG['enabled'] else '🔴 כבוי'}",
            f"🎯 זיהוי: {AUTO_RESPONSE_CONFIG['confidence_threshold']*100:.0f}% סף",
            f"🔒 אבטחה: {'🟢 מלא' if SECURITY_CONFIG['enabled'] else '🟠 בסיסי'}"
        ]
        
        print(" | ".join(config_info))
        print(f"\n🚀 המערכת מוכנה - Services: {'✅' if SERVICES_AVAILABLE else '⚠️'} | Utils: {'✅' if UTILS_AVAILABLE else '⚠️'} | DB: {'✅' if DATABASE_AVAILABLE else '⚠️'}")
        print("💬 משתמשים יכולים לכתוב בשפה טבעית וליהנות מזיהוי חכם")
        print("📱 לבדיקה: 'רוצה את הסדרה Friends' או 'יש לכם Avatar 2022?'")
        print("🔧 מנהלים: /pending, /admin_stats, /analytics")

def main():
    """פונקציה ראשית מתקדמת"""
    print("🏴‍☠️ בוט התמימים הפיראטים - אתחול מערכת מתקדמת")
    print("🔧 בודק הגדרות מתקדמות...")
    
    # בדיקות בסיסיות
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ שגיאה: לא הוגדר BOT_TOKEN")
        print("💡 עדכן את הטוקן בקובץ config.py")
        return
    
    if not ADMIN_IDS or ADMIN_IDS == [123456789, 987654321]:
        print("⚠️  אזהרה: עדכן את רשימת המנהלים ב-ADMIN_IDS")
        print("📝 ערוך את קובץ config.py")
        print("🆔 השתמש ב: python get_my_id.py כדי לגלות את ה-ID שלך")
        
        response = input("\nהאם להמשיך בכל זאת? (y/n): ")
        if response.lower() != 'y':
            print("👋 נסה שוב אחרי עדכון המנהלים")
            return
    
    # בדיקות מתקדמות
    print("🔍 בודק הגדרות מתקדמות...")
    
    if USE_DATABASE:
        print(f"🗄️  מצב בסיס נתונים: {DB_CONFIG['host']}:{DB_CONFIG.get('port', 5432)}")
    
    if CACHE_CONFIG['enabled']:
        print(f"💾 מצב Cache: {CACHE_CONFIG['type']} (TTL: {CACHE_CONFIG['ttl']['requests']}s)")
    
    if BACKGROUND_TASKS_CONFIG['enabled']:
        print(f"🔄 משימות רקע: {BACKGROUND_TASKS_CONFIG['max_concurrent_tasks']} מקבילות")
    
    print(f"🎯 סף זיהוי: {AUTO_RESPONSE_CONFIG['confidence_threshold']*100:.0f}%")
    print(f"🔒 אבטחה: {'מלאה' if SECURITY_CONFIG['enabled'] else 'בסיסית'}")
    
    # יצירת הבוט המתקדם
    try:
        print("\n🚀 יוצר מערכת מתקדמת...")
        bot = EnhancedPirateBot()
        print("✅ מערכת מתקדמת מוכנה!")
        bot.run()
    except ImportError as e:
        missing_module = str(e).split("'")[1] if "'" in str(e) else "unknown"
        print(f"❌ חסר מודול: {missing_module}")
        print("💡 התקן עם: pip install -r requirements.txt")
    except Exception as e:
        logger.error(f"Failed to start enhanced bot: {e}")
        print(f"❌ שגיאה בהפעלת הבוט: {e}")
        print("💡 בדוק את הגדרות הטוקן והרשאות")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Failed to initialize core components: {e}")
        raise