#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyboard Builder לבוט התמימים הפיראטים
בניית מקלדות אינליין מתקדמות
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json

logger = logging.getLogger(__name__)

class KeyboardBuilder:
    """בונה מקלדות אינליין מתקדמות"""
    
    def __init__(self):
        # הגדרות ברירת מחדל
        self.max_buttons_per_row = 3
        self.max_callback_data_length = 64
        self.default_pagination_size = 10
        
        # אמוג'ים נפוצים
        self.emojis = {
            'yes': '✅',
            'no': '❌',
            'back': '⬅️',
            'forward': '➡️',
            'home': '🏠',
            'search': '🔍',
            'settings': '⚙️',
            'info': 'ℹ️',
            'warning': '⚠️',
            'success': '✅',
            'error': '❌',
            'pending': '⏳',
            'fulfilled': '✅',
            'rejected': '❌',
            'admin': '👑',
            'user': '👤',
            'stats': '📊',
            'edit': '✏️',
            'delete': '🗑️',
            'add': '➕',
            'remove': '➖'
        }
        
        logger.info("Keyboard Builder initialized")
    
    # ========================= מקלדות ראשיות =========================
    
    def build_main_menu(self, user_id: int, is_admin: bool = False) -> InlineKeyboardMarkup:
        """מקלדת תפריט ראשי"""
        try:
            buttons = [
                [
                    self._create_button("📝 בקשה חדשה", "action:new_request"),
                    self._create_button("🔍 הבקשות שלי", "action:my_requests")
                ],
                [
                    self._create_button("📊 סטטיסטיקות", "action:stats"),
                    self._create_button("🆘 עזרה", "action:help")
                ]
            ]
            
            # כפתורים למנהלים
            if is_admin:
                admin_buttons = [
                    [
                        self._create_button("👑 פאנל מנהלים", "admin:panel"),
                        self._create_button("⏳ בקשות ממתינות", "admin:pending")
                    ]
                ]
                buttons.extend(admin_buttons)
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build main menu: {e}")
            return self._create_error_keyboard()
    
    def build_request_actions(self, request_id: int, user_role: str, 
                            request_status: str = 'pending') -> InlineKeyboardMarkup:
        """מקלדת פעולות לבקשה"""
        try:
            buttons = []
            
            if user_role == 'admin':
                if request_status == 'pending':
                    # פעולות מנהל לבקשה ממתינה
                    buttons.extend([
                        [
                            self._create_button("✅ אשר בקשה", f"admin:fulfill:{request_id}"),
                            self._create_button("❌ דחה בקשה", f"admin:reject:{request_id}")
                        ],
                        [
                            self._create_button("ℹ️ פרטים מלאים", f"admin:details:{request_id}"),
                            self._create_button("👤 פרופיל משתמש", f"admin:user_profile:{request_id}")
                        ]
                    ])
                elif request_status == 'fulfilled':
                    # פעולות לבקשה שמולאה
                    buttons.append([
                        self._create_button("📊 צפה בדירוגים", f"admin:ratings:{request_id}"),
                        self._create_button("ℹ️ פרטים", f"admin:details:{request_id}")
                    ])
            
            else:  # user role
                if request_status == 'pending':
                    buttons.append([
                        self._create_button("❌ בטל בקשה", f"user:cancel:{request_id}"),
                        self._create_button("✏️ ערוך בקשה", f"user:edit:{request_id}")
                    ])
                elif request_status == 'fulfilled':
                    buttons.append([
                        self._create_button("⭐ דרג את השירות", f"user:rate:{request_id}"),
                        self._create_button("ℹ️ פרטי בקשה", f"user:details:{request_id}")
                    ])
            
            # כפתור חזרה
            buttons.append([self._create_button("⬅️ חזרה", "action:back")])
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build request actions: {e}")
            return self._create_error_keyboard()
    
    def build_admin_menu(self, pending_count: int = 0, stats: Dict = None) -> InlineKeyboardMarkup:
        """מקלדת פאנל מנהלים"""
        try:
            pending_text = f"⏳ בקשות ממתינות ({pending_count})" if pending_count > 0 else "⏳ בקשות ממתינות"
            
            buttons = [
                [
                    self._create_button(pending_text, "admin:pending_list"),
                    self._create_button("📊 סטטיסטיקות", "admin:statistics")
                ],
                [
                    self._create_button("👥 ניהול משתמשים", "admin:users"),
                    self._create_button("🔍 חיפוש מתקדם", "admin:search")
                ],
                [
                    self._create_button("📈 דוחות", "admin:reports"),
                    self._create_button("⚙️ הגדרות", "admin:settings")
                ],
                [
                    self._create_button("📤 ייצוא נתונים", "admin:export"),
                    self._create_button("🔧 תחזוקה", "admin:maintenance")
                ]
            ]
            
            # כפתור חזרה לתפריט הראשי
            buttons.append([self._create_button("🏠 תפריט ראשי", "action:main_menu")])
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build admin menu: {e}")
            return self._create_error_keyboard()
    
    def build_rating_keyboard(self, request_id: int) -> InlineKeyboardMarkup:
        """מקלדת דירוג שירות"""
        try:
            buttons = [
                [
                    self._create_button("⭐⭐⭐⭐⭐ (5)", f"rate:{request_id}:5"),
                    self._create_button("⭐⭐⭐⭐ (4)", f"rate:{request_id}:4")
                ],
                [
                    self._create_button("⭐⭐⭐ (3)", f"rate:{request_id}:3"),
                    self._create_button("⭐⭐ (2)", f"rate:{request_id}:2")
                ],
                [
                    self._create_button("⭐ (1)", f"rate:{request_id}:1")
                ],
                [
                    self._create_button("💬 דירוג + הערה", f"rate_with_comment:{request_id}"),
                    self._create_button("⬅️ חזרה", "action:back")
                ]
            ]
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build rating keyboard: {e}")
            return self._create_error_keyboard()
    
    # ========================= מקלדות דינמיות =========================
    
    def build_category_selector(self, categories: Dict[str, Any], 
                              selected: Optional[str] = None) -> InlineKeyboardMarkup:
        """בחירת קטגוריה"""
        try:
            buttons = []
            
            # מיון קטגוריות לפי שם
            sorted_categories = sorted(categories.items(), 
                                     key=lambda x: x[1].get('name', x[0]))
            
            # יצירת כפתורים
            row = []
            for category_id, category_info in sorted_categories:
                name = category_info.get('name', category_id)
                emoji = category_info.get('emoji', '📋')
                
                # סימון קטגוריה נבחרת
                if category_id == selected:
                    button_text = f"✅ {emoji} {name}"
                else:
                    button_text = f"{emoji} {name}"
                
                button = self._create_button(button_text, f"category:{category_id}")
                row.append(button)
                
                # מעבר לשורה חדשה כל 2 כפתורים
                if len(row) >= 2:
                    buttons.append(row)
                    row = []
            
            # הוספת שורה אחרונה אם נותרה
            if row:
                buttons.append(row)
            
            # כפתורי פעולה
            action_buttons = [
                self._create_button("🔍 הכל", "category:all"),
                self._create_button("⬅️ חזרה", "action:back")
            ]
            buttons.append(action_buttons)
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build category selector: {e}")
            return self._create_error_keyboard()
    
    def build_pagination_keyboard(self, current_page: int, total_pages: int, 
                                prefix: str, extra_buttons: Optional[List] = None) -> InlineKeyboardMarkup:
        """מקלדת עמודים (pagination)"""
        try:
            buttons = []
            
            # כפתורים נוספים אם יש
            if extra_buttons:
                buttons.extend(extra_buttons)
            
            # כפתורי ניווט
            nav_buttons = []
            
            # כפתור עמוד קודם
            if current_page > 1:
                nav_buttons.append(
                    self._create_button("⬅️ קודם", f"{prefix}:page:{current_page - 1}")
                )
            
            # מידע על עמוד נוכחי
            if total_pages > 1:
                page_info = f"📄 {current_page}/{total_pages}"
                nav_buttons.append(
                    self._create_button(page_info, f"{prefix}:page_info")
                )
            
            # כפתור עמוד הבא
            if current_page < total_pages:
                nav_buttons.append(
                    self._create_button("➡️ הבא", f"{prefix}:page:{current_page + 1}")
                )
            
            if nav_buttons:
                buttons.append(nav_buttons)
            
            # כפתור חזרה
            buttons.append([self._create_button("⬅️ חזרה", "action:back")])
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build pagination keyboard: {e}")
            return self._create_error_keyboard()
    
    def build_confirmation_keyboard(self, action_type: str, target_id: Union[int, str],
                                  confirm_text: str = "✅ אשר", 
                                  cancel_text: str = "❌ בטל") -> InlineKeyboardMarkup:
        """מקלדת אישור פעולה"""
        try:
            buttons = [
                [
                    self._create_button(confirm_text, f"confirm:{action_type}:{target_id}"),
                    self._create_button(cancel_text, f"cancel:{action_type}:{target_id}")
                ]
            ]
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build confirmation keyboard: {e}")
            return self._create_error_keyboard()
    
    def build_filter_keyboard(self, available_filters: Dict[str, Any], 
                            current_filters: Dict[str, Any]) -> InlineKeyboardMarkup:
        """מקלדת פילטרים"""
        try:
            buttons = []
            
            for filter_key, filter_info in available_filters.items():
                filter_name = filter_info.get('name', filter_key)
                filter_emoji = filter_info.get('emoji', '🔹')
                
                # בדיקה אם הפילטר פעיל
                is_active = filter_key in current_filters
                
                if is_active:
                    button_text = f"✅ {filter_emoji} {filter_name}"
                    callback_data = f"filter_remove:{filter_key}"
                else:
                    button_text = f"⬜ {filter_emoji} {filter_name}"
                    callback_data = f"filter_add:{filter_key}"
                
                buttons.append([self._create_button(button_text, callback_data)])
            
            # כפתורי פעולה
            action_buttons = [
                self._create_button("🔍 החל פילטרים", "filter:apply"),
                self._create_button("🗑️ נקה הכל", "filter:clear")
            ]
            buttons.append(action_buttons)
            
            # כפתור חזרה
            buttons.append([self._create_button("⬅️ חזרה", "action:back")])
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build filter keyboard: {e}")
            return self._create_error_keyboard()
    
    # ========================= מקלדות מותאמות =========================
    
    def build_custom_keyboard(self, buttons_data: List[Dict], 
                            max_per_row: int = 2) -> InlineKeyboardMarkup:
        """בניית מקלדת מותאמת אישית"""
        try:
            buttons = []
            current_row = []
            
            for button_data in buttons_data:
                text = button_data.get('text', 'כפתור')
                callback_data = button_data.get('callback_data', 'no_action')
                url = button_data.get('url')  # כפתור עם URL
                
                if url:
                    button = InlineKeyboardButton(text, url=url)
                else:
                    button = self._create_button(text, callback_data)
                
                current_row.append(button)
                
                # מעבר לשורה חדשה
                if len(current_row) >= max_per_row:
                    buttons.append(current_row)
                    current_row = []
            
            # הוספת שורה אחרונה
            if current_row:
                buttons.append(current_row)
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build custom keyboard: {e}")
            return self._create_error_keyboard()
    
    def build_search_results_keyboard(self, results: List[Dict], page: int = 0,
                                    results_per_page: int = 5) -> InlineKeyboardMarkup:
        """מקלדת תוצאות חיפוש"""
        try:
            buttons = []
            
            # חישוב טווח תוצאות לעמוד נוכחי
            start_idx = page * results_per_page
            end_idx = min(start_idx + results_per_page, len(results))
            
            page_results = results[start_idx:end_idx]
            
            # יצירת כפתור לכל תוצאה
            for result in page_results:
                request_id = result.get('id')
                title = result.get('title', 'ללא כותרת')
                status = result.get('status', 'unknown')
                
                # אמוג'י לפי סטטוס
                status_emoji = {
                    'pending': '⏳',
                    'fulfilled': '✅',
                    'rejected': '❌'
                }.get(status, '❓')
                
                # קיצור כותרת אם נדרש
                if len(title) > 30:
                    title = title[:27] + "..."
                
                button_text = f"{status_emoji} {title}"
                callback_data = f"view_request:{request_id}"
                
                buttons.append([self._create_button(button_text, callback_data)])
            
            # כפתורי ניווט
            total_pages = (len(results) + results_per_page - 1) // results_per_page
            
            if total_pages > 1:
                nav_keyboard = self.build_pagination_keyboard(
                    page + 1, total_pages, "search_results"
                )
                # החזרת הכפתורים עם הפגינציה
                nav_keyboard.inline_keyboard = buttons + nav_keyboard.inline_keyboard
                return nav_keyboard
            else:
                # רק כפתור חזרה
                buttons.append([self._create_button("⬅️ חזרה", "action:back")])
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build search results keyboard: {e}")
            return self._create_error_keyboard()
    
    def build_user_actions_keyboard(self, user_id: int, is_admin: bool = False,
                                  user_status: str = 'active') -> InlineKeyboardMarkup:
        """מקלדת פעולות משתמש"""
        try:
            buttons = []
            
            if is_admin:
                # פעולות מנהל על משתמש
                buttons.extend([
                    [
                        self._create_button("📊 סטטיסטיקות", f"admin:user_stats:{user_id}"),
                        self._create_button("📜 היסטוריה", f"admin:user_history:{user_id}")
                    ],
                    [
                        self._create_button("⚠️ הוספת אזהרה", f"admin:warn_user:{user_id}"),
                        self._create_button("🚫 חסימת משתמש", f"admin:ban_user:{user_id}")
                    ]
                ])
                
                if user_status == 'banned':
                    buttons.append([
                        self._create_button("🔓 ביטול חסימה", f"admin:unban_user:{user_id}")
                    ])
            else:
                # פעולות משתמש רגיל
                buttons.extend([
                    [
                        self._create_button("📝 הבקשות שלי", f"user:my_requests:{user_id}"),
                        self._create_button("📊 הסטטיסטיקות שלי", f"user:my_stats:{user_id}")
                    ],
                    [
                        self._create_button("⚙️ הגדרות", f"user:settings:{user_id}"),
                        self._create_button("🆘 עזרה", "action:help")
                    ]
                ])
            
            # כפתור חזרה
            buttons.append([self._create_button("⬅️ חזרה", "action:back")])
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build user actions keyboard: {e}")
            return self._create_error_keyboard()
    
    # ========================= מקלדות מיוחדות =========================
    
    def build_quick_actions_keyboard(self, context: str) -> InlineKeyboardMarkup:
        """מקלדת פעולות מהירות לפי קונטקסט"""
        try:
            buttons = []
            
            if context == 'new_user':
                buttons = [
                    [self._create_button("📝 צור בקשה ראשונה", "action:new_request")],
                    [self._create_button("🆘 מדריך למתחילים", "action:tutorial")],
                    [self._create_button("📊 דוגמאות בקשות", "action:examples")]
                ]
            
            elif context == 'pending_requests':
                buttons = [
                    [
                        self._create_button("✅ אשר הכל", "admin:bulk_fulfill"),
                        self._create_button("❌ דחה הכל", "admin:bulk_reject")
                    ],
                    [self._create_button("📊 סינון מתקדם", "admin:filter_pending")]
                ]
            
            elif context == 'user_profile':
                buttons = [
                    [
                        self._create_button("📝 בקשה חדשה", "action:new_request"),
                        self._create_button("📊 הסטטיסטיקות שלי", "user:my_stats")
                    ]
                ]
            
            # כפתור חזרה תמיד
            buttons.append(self.create_back_button())
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build quick actions keyboard: {e}")
            return self._create_error_keyboard()
    
    def build_dynamic_menu(self, menu_data: Dict[str, Any]) -> InlineKeyboardMarkup:
        """בניית תפריט דינמי מנתונים"""
        try:
            buttons = []
            
            for item in menu_data.get('items', []):
                text = item.get('text', 'פריט')
                callback_data = item.get('callback_data', 'no_action')
                emoji = item.get('emoji', '🔹')
                
                full_text = f"{emoji} {text}"
                button = self._create_button(full_text, callback_data)
                
                # סידור בשורות
                row_size = item.get('row_size', 1)
                if len(buttons) == 0 or len(buttons[-1]) >= row_size:
                    buttons.append([button])
                else:
                    buttons[-1].append(button)
            
            # כפתורי פעולה נוספים
            footer_items = menu_data.get('footer', [])
            if footer_items:
                for footer_item in footer_items:
                    text = footer_item.get('text', 'פעולה')
                    callback_data = footer_item.get('callback_data', 'no_action')
                    emoji = footer_item.get('emoji', '')
                    
                    full_text = f"{emoji} {text}".strip()
                    button = self._create_button(full_text, callback_data)
                    buttons.append([button])
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Failed to build dynamic menu: {e}")
            return self._create_error_keyboard()
    
    # ========================= עיבוד callbacks =========================
    
    def parse_callback_data(self, callback_data: str) -> Dict[str, Any]:
        """פירוק נתוני callback"""
        try:
            if ':' in callback_data:
                parts = callback_data.split(':')
                return {
                    'action': parts[0],
                    'type': parts[1] if len(parts) > 1 else None,
                    'id': parts[2] if len(parts) > 2 else None,
                    'extra': parts[3:] if len(parts) > 3 else [],
                    'raw': callback_data
                }
            else:
                return {
                    'action': callback_data,
                    'type': None,
                    'id': None,
                    'extra': [],
                    'raw': callback_data
                }
                
        except Exception as e:
            logger.error(f"Failed to parse callback data '{callback_data}': {e}")
            return {
                'action': 'error',
                'type': None,
                'id': None,
                'extra': [],
                'raw': callback_data,
                'error': str(e)
            }
    
    def build_callback_data(self, action: str, **params) -> str:
        """בניית נתוני callback"""
        try:
            parts = [action]
            
            # הוספת פרמטרים בסדר
            for key in ['type', 'id', 'page', 'filter', 'status']:
                if key in params:
                    parts.append(str(params[key]))
            
            # הוספת פרמטרים נוספים
            for key, value in params.items():
                if key not in ['type', 'id', 'page', 'filter', 'status'] and value is not None:
                    parts.append(str(value))
            
            callback_data = ':'.join(parts)
            
            # בדיקת אורך
            if len(callback_data) > self.max_callback_data_length:
                logger.warning(f"Callback data too long: {len(callback_data)} chars")
                callback_data = callback_data[:self.max_callback_data_length]
            
            return callback_data
            
        except Exception as e:
            logger.error(f"Failed to build callback data: {e}")
            return f"error:{action}"
    
    def validate_callback_permissions(self, callback_data: str, user_id: int, 
                                    is_admin: bool = False) -> Dict[str, Any]:
        """בדיקת הרשאות callback"""
        try:
            parsed = self.parse_callback_data(callback_data)
            action = parsed.get('action', '')
            
            result = {
                'is_allowed': True,
                'reason': None,
                'requires_confirmation': False
            }
            
            # בדיקות הרשאות
            if action.startswith('admin:'):
                if not is_admin:
                    result['is_allowed'] = False
                    result['reason'] = 'Admin privileges required'
            
            # פעולות שדורשות אישור
            destructive_actions = ['ban_user', 'delete', 'reject', 'cancel']
            if any(destructive in callback_data for destructive in destructive_actions):
                result['requires_confirmation'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Permission validation failed: {e}")
            return {
                'is_allowed': False,
                'reason': 'Validation error',
                'requires_confirmation': False
            }
    
    # ========================= כלים למפתחים =========================
    
    def get_keyboard_stats(self) -> Dict[str, Any]:
        """סטטיסטיקות בונה המקלדות"""
        return {
            'max_buttons_per_row': self.max_buttons_per_row,
            'max_callback_data_length': self.max_callback_data_length,
            'default_pagination_size': self.default_pagination_size,
            'available_emojis': len(self.emojis),
            'emoji_list': list(self.emojis.keys())
        }
    
    def validate_keyboard_structure(self, keyboard: InlineKeyboardMarkup) -> Dict[str, Any]:
        """בדיקת תקינות מבנה מקלדת"""
        try:
            result = {
                'is_valid': True,
                'warnings': [],
                'stats': {}
            }
            
            total_buttons = 0
            max_row_length = 0
            callback_data_lengths = []
            
            for row in keyboard.inline_keyboard:
                row_length = len(row)
                total_buttons += row_length
                max_row_length = max(max_row_length, row_length)
                
                for button in row:
                    if button.callback_data:
                        callback_data_lengths.append(len(button.callback_data))
                        
                        if len(button.callback_data) > self.max_callback_data_length:
                            result['warnings'].append(
                                f"Callback data too long: {len(button.callback_data)} chars"
                            )
            
            result['stats'] = {
                'total_buttons': total_buttons,
                'total_rows': len(keyboard.inline_keyboard),
                'max_row_length': max_row_length,
                'avg_callback_length': sum(callback_data_lengths) / len(callback_data_lengths) if callback_data_lengths else 0
            }
            
            # אזהרות
            if total_buttons > 20:
                result['warnings'].append(f"Many buttons ({total_buttons}) may affect user experience")
            
            if max_row_length > 3:
                result['warnings'].append(f"Row with {max_row_length} buttons may be too wide")
            
            return result
            
        except Exception as e:
            logger.error(f"Keyboard validation failed: {e}")
            return {
                'is_valid': False,
                'error': str(e),
                'warnings': [],
                'stats': {}
            }
    
    def debug_callback_data(self, callback_data: str) -> Dict[str, Any]:
        """ניפוי שגיאות callback data"""
        try:
            parsed = self.parse_callback_data(callback_data)
            
            debug_info = {
                'original': callback_data,
                'length': len(callback_data),
                'is_valid_length': len(callback_data) <= self.max_callback_data_length,
                'parsed': parsed,
                'parts_count': len(callback_data.split(':')),
                'encoding': callback_data.encode('utf-8'),
                'is_ascii': callback_data.isascii()
            }
            
            return debug_info
            
        except Exception as e:
            return {
                'original': callback_data,
                'error': str(e),
                'debug_failed': True
            }
    
    # ========================= פונקציות עזר =========================
    
    def _create_button(self, text: str, callback_data: str) -> InlineKeyboardButton:
        """יצירת כפתור אינליין"""
        try:
            # וידוא שאורך callback_data תקין
            if len(callback_data) > self.max_callback_data_length:
                logger.warning(f"Trimming callback data: {callback_data}")
                callback_data = callback_data[:self.max_callback_data_length]
            
            return InlineKeyboardButton(text, callback_data=callback_data)
            
        except Exception as e:
            logger.error(f"Failed to create button: {e}")
            return InlineKeyboardButton("שגיאה", callback_data="error")
    
    def _create_error_keyboard(self) -> InlineKeyboardMarkup:
        """מקלדת שגיאה גנרית"""
        return InlineKeyboardMarkup([
            [self._create_button("❌ שגיאה ביצירת מקלדת", "error:keyboard")],
            [self._create_button("🏠 תפריט ראשי", "action:main_menu")]
        ])
    
    def arrange_buttons_in_rows(self, buttons: List[InlineKeyboardButton], 
                               max_per_row: int = 2) -> List[List[InlineKeyboardButton]]:
        """סידור כפתורים בשורות"""
        try:
            rows = []
            current_row = []
            
            for button in buttons:
                current_row.append(button)
                
                if len(current_row) >= max_per_row:
                    rows.append(current_row)
                    current_row = []
            
            # הוספת שורה אחרונה
            if current_row:
                rows.append(current_row)
            
            return rows
            
        except Exception as e:
            logger.error(f"Failed to arrange buttons: {e}")
            return [[self._create_button("שגיאה", "error")]]
    
    def add_navigation_buttons(self, keyboard: List[List[InlineKeyboardButton]], 
                             has_prev: bool, has_next: bool, 
                             prefix: str) -> List[List[InlineKeyboardButton]]:
        """הוספת כפתורי ניווט"""
        try:
            nav_buttons = []
            
            if has_prev:
                nav_buttons.append(self._create_button("⬅️ קודם", f"{prefix}:prev"))
            
            if has_next:
                nav_buttons.append(self._create_button("➡️ הבא", f"{prefix}:next"))
            
            if nav_buttons:
                keyboard.append(nav_buttons)
            
            return keyboard
            
        except Exception as e:
            logger.error(f"Failed to add navigation buttons: {e}")
            return keyboard
    
    def create_back_button(self, target: str = 'main_menu') -> List[InlineKeyboardButton]:
        """יצירת כפתור חזרה"""
        back_texts = {
            'main_menu': '🏠 תפריט ראשי',
            'admin_panel': '👑 פאנל מנהלים',
            'back': '⬅️ חזרה'
        }
        
        text = back_texts.get(target, '⬅️ חזרה')
        return [self._create_button(text, f"action:{target}")]
    
    # ========================= פונקציות keyboard חדשות =========================
    
    def get_request_confirmation_keyboard(self, user_id: int, analysis: dict) -> InlineKeyboardMarkup:
        """מקלדת אישור יצירת בקשה"""
        category = analysis.get('category', 'general')
        buttons = [
            [
                self._create_button("✅ יצר בקשה", f"create_request:{user_id}:{category}"),
                self._create_button("❌ ביטול", "dismiss")
            ]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def get_maybe_request_keyboard(self, confidence_or_user_id, category=None) -> InlineKeyboardMarkup:
        """מקלדת לבקשה אפשרית"""
        if isinstance(confidence_or_user_id, (int, float)) and confidence_or_user_id <= 1.0:
            # זה confidence + category
            confidence = confidence_or_user_id
            detected_category = category or 'general'
            category_text = f" ({detected_category})" if detected_category != 'general' else ""
            confidence_percent = int(confidence * 100)
            
            buttons = [
                [
                    self._create_button(f"✅ כן{category_text}", f"confirm_request:{confidence_percent}:{detected_category}"),
                    self._create_button("❌ לא", "not_request")
                ]
            ]
            
            # הוספת כפתור להבהרה אם הביטחון נמוך מאוד
            if confidence < 0.6:
                buttons.append([
                    self._create_button("💬 הבהר", "clarify_request")
                ])
        else:
            # זה user_id בלבד
            user_id = confidence_or_user_id
            buttons = [
                [
                    self._create_button("✅ כן", f"confirm_request:{user_id}:general"),
                    self._create_button("❌ לא", "dismiss")
                ]
            ]
            
        # כפתור עזרה
        buttons.append([
            self._create_button("🆘 עזרה", "action:help")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    def get_duplicate_handling_keyboard(self, request_id: int) -> InlineKeyboardMarkup:
        """מקלדת טיפול בכפילויות"""
        buttons = [
            [
                self._create_button("🔄 בקש בכל זאת", f"create_duplicate:{request_id}"),
                self._create_button("👀 ראה קיימת", f"view_request:{request_id}")
            ],
            [self._create_button("❌ ביטול", "dismiss")]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def get_main_menu_keyboard(self, is_admin: bool = False) -> InlineKeyboardMarkup:
        """מקלדת תפריט ראשי"""
        buttons = [
            [self._create_button("🎯 בקשה חדשה", "action:new_request")],
            [self._create_button("📋 הבקשות שלי", "action:my_requests")]
        ]
        if is_admin:
            buttons.append([self._create_button("👑 מנהלים", "action:admin_panel")])
        buttons.append([self._create_button("❓ עזרה", "action:help")])
        return InlineKeyboardMarkup(buttons)
    
    def get_help_keyboard(self, is_admin: bool = False) -> InlineKeyboardMarkup:
        """מקלדת עזרה"""
        buttons = [
            [self._create_button("🏠 ראשי", "action:main_menu")]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def get_settings_keyboard(self, user_settings: dict) -> InlineKeyboardMarkup:
        """מקלדת הגדרות"""
        buttons = [
            [self._create_button("🏠 ראשי", "action:main_menu")]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def get_request_help_keyboard(self) -> InlineKeyboardMarkup:
        """מקלדת עזרה לבקשות"""
        buttons = [
            [self._create_button("🏠 ראשי", "action:main_menu")]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def get_request_created_keyboard(self, request_id: int) -> InlineKeyboardMarkup:
        """מקלדת לאחר יצירת בקשה"""
        buttons = [
            [
                self._create_button("👀 ראה", f"view_request:{request_id}"),
                self._create_button("📋 הבקשות שלי", "action:my_requests")
            ],
            [self._create_button("🏠 ראשי", "action:main_menu")]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def get_admin_pending_keyboard(self) -> InlineKeyboardMarkup:
        """מקלדת בקשות ממתינות למנהלים"""
        buttons = [
            [self._create_button("🔄 רענון", "admin:refresh_pending")],
            [self._create_button("👑 מנהלים", "action:admin_panel")]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def get_fulfill_success_keyboard(self, request_id: int) -> InlineKeyboardMarkup:
        """מקלדת הצלחת מילוי בקשה"""
        buttons = [
            [self._create_button("📋 ממתינות", "admin:pending_list")],
            [self._create_button("👑 מנהלים", "action:admin_panel")]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def get_admin_stats_keyboard(self) -> InlineKeyboardMarkup:
        """מקלדת סטטיסטיקות מנהלים"""
        buttons = [
            [self._create_button("👑 מנהלים", "action:admin_panel")]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def get_analytics_keyboard(self) -> InlineKeyboardMarkup:
        """מקלדת אנליטיקס"""
        buttons = [
            [self._create_button("👑 מנהלים", "action:admin_panel")]
        ]
        return InlineKeyboardMarkup(buttons)
    
    def get_user_requests_keyboard(self) -> InlineKeyboardMarkup:
        """מקלדת בקשות המשתמש"""
        buttons = [
            [self._create_button("🏠 ראשי", "action:main_menu")]
        ]
        return InlineKeyboardMarkup(buttons)


# ========================= פונקציות עזר גלובליות =========================

def create_button(text: str, callback_data: str) -> InlineKeyboardButton:
    """פונקציה גלובלית ליצירת כפתור"""
    return InlineKeyboardButton(text, callback_data=callback_data)

def arrange_buttons_in_rows(buttons: List[InlineKeyboardButton], 
                           max_per_row: int = 2) -> List[List[InlineKeyboardButton]]:
    """סידור כפתורים בשורות - פונקציה גלובלית"""
    rows = []
    current_row = []
    
    for button in buttons:
        current_row.append(button)
        
        if len(current_row) >= max_per_row:
            rows.append(current_row)
            current_row = []
    
    if current_row:
        rows.append(current_row)
    
    return rows

def add_navigation_buttons(keyboard: List[List[InlineKeyboardButton]], 
                          has_prev: bool, has_next: bool, prefix: str) -> List[List[InlineKeyboardButton]]:
    """הוספת כפתורי ניווט - פונקציה גלובלית"""
    nav_buttons = []
    
    if has_prev:
        nav_buttons.append(create_button("⬅️ קודם", f"{prefix}:prev"))
    
    if has_next:
        nav_buttons.append(create_button("➡️ הבא", f"{prefix}:next"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    return keyboard

def create_back_button(target: str = 'main_menu') -> List[InlineKeyboardButton]:
    """יצירת כפתור חזרה - פונקציה גלובלית"""
    back_texts = {
        'main_menu': '🏠 תפריט ראשי',
        'admin_panel': '👑 פאנל מנהלים', 
        'back': '⬅️ חזרה'
    }
    
    text = back_texts.get(target, '⬅️ חזרה')
    return [create_button(text, f"action:{target}")]

def build_simple_menu(items: List[Tuple[str, str]], back_button: bool = True) -> InlineKeyboardMarkup:
    """בניית תפריט פשוט מרשימת פריטים"""
    buttons = []
    
    for text, callback_data in items:
        buttons.append([create_button(text, callback_data)])
    
    if back_button:
        buttons.extend([create_back_button()])
    
    return InlineKeyboardMarkup(buttons)