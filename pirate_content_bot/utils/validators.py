#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validators לבוט התמימים הפיראטים
בדיקות תקינות וביטחון קלט
"""

import logging
import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import html
import urllib.parse

logger = logging.getLogger(__name__)

class InputValidator:
    """מערכת בדיקת תקינות קלט"""
    
    # רשימות שחורות ברירת מחדל
    MALICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<form[^>]*>',
        r'<input[^>]*>',
        r'eval\s*\(',
        r'document\.',
        r'window\.',
        r'alert\s*\(',
    ]
    
    SPAM_INDICATORS = [
        r'(?:https?://)?(?:www\.)?(?:bit\.ly|tinyurl|t\.co|short\.link)',
        r'(?:telegram|whatsapp|discord)\.(?:me|com|org)',
        r'(?:join|click|visit|download).*(?:now|here|link)',
        r'(?:free|win|prize|money|cash|discount)',
        r'(?:urgent|limited|offer|deal|sale)',
        r'[💰💎💵💸🤑💲]',
        r'[🔥⚡🚨🎯🎉🎊]'
    ]
    
    PROHIBITED_CONTENT = [
        r'(?:porn|xxx|adult|sex)',
        r'(?:drug|cocaine|heroin|marijuana)',
        r'(?:weapon|gun|bomb|explosive)',
        r'(?:hack|crack|keygen|serial)',
        r'(?:pirat|torrent|download.*free)',
        r'(?:illegal|stolen|counterfeit)'
    ]
    
    # הגדרות validation
    MAX_TEXT_LENGTH = 1000
    MIN_TEXT_LENGTH = 2
    MAX_TITLE_LENGTH = 200
    MIN_TITLE_LENGTH = 3
    
    @staticmethod
    def validate_user_input(text: str, max_length: int = MAX_TEXT_LENGTH) -> Dict[str, Any]:
        """
        בדיקת תקינות כוללת של קלט משתמש
        
        Returns:
            Dict עם תוצאות הבדיקה
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'cleaned_text': text,
            'metadata': {}
        }
        
        try:
            if not text or not isinstance(text, str):
                result['is_valid'] = False
                result['errors'].append('Input text is required and must be a string')
                return result
            
            # בדיקת אורך
            if len(text) > max_length:
                result['is_valid'] = False
                result['errors'].append(f'Text too long (max {max_length} characters)')
            
            if len(text.strip()) < InputValidator.MIN_TEXT_LENGTH:
                result['is_valid'] = False
                result['errors'].append(f'Text too short (min {InputValidator.MIN_TEXT_LENGTH} characters)')
            
            # בדיקת תוכן זדוני
            malicious_check = InputValidator.check_malicious_content(text)
            if not malicious_check['is_safe']:
                result['is_valid'] = False
                result['errors'].extend(malicious_check['threats'])
            
            # בדיקת spam
            spam_check = InputValidator.check_spam_indicators(text)
            if spam_check['is_spam']:
                result['warnings'].append('Content may contain spam indicators')
                result['metadata']['spam_score'] = spam_check['score']
            
            # בדיקת תוכן אסור
            prohibited_check = InputValidator.check_prohibited_content(text)
            if not prohibited_check['is_allowed']:
                result['is_valid'] = False
                result['errors'].extend(prohibited_check['violations'])
            
            # ניקוי טקסט
            result['cleaned_text'] = InputValidator.sanitize_input(text)
            
            # מטא-דאטא נוסף
            result['metadata'].update({
                'original_length': len(text),
                'cleaned_length': len(result['cleaned_text']),
                'has_urls': InputValidator._has_urls(text),
                'language_hints': InputValidator._detect_language(text),
                'quality_score': InputValidator._calculate_text_quality(text)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            result['is_valid'] = False
            result['errors'].append('Validation error occurred')
            return result
    
    @staticmethod
    def validate_request_title(title: str) -> Dict[str, Any]:
        """בדיקת תקינות כותרת בקשה"""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'cleaned_title': title,
            'extracted_info': {}
        }
        
        try:
            if not title or not isinstance(title, str):
                result['is_valid'] = False
                result['errors'].append('Title is required')
                return result
            
            title = title.strip()
            
            # בדיקת אורך
            if len(title) > InputValidator.MAX_TITLE_LENGTH:
                result['is_valid'] = False
                result['errors'].append(f'Title too long (max {InputValidator.MAX_TITLE_LENGTH} characters)')
            
            if len(title) < InputValidator.MIN_TITLE_LENGTH:
                result['is_valid'] = False
                result['errors'].append(f'Title too short (min {InputValidator.MIN_TITLE_LENGTH} characters)')
            
            # בדיקת תוכן
            if not InputValidator._has_meaningful_content(title):
                result['warnings'].append('Title may lack meaningful content')
            
            # חילוץ מידע
            result['extracted_info'] = InputValidator._extract_title_info(title)
            
            # ניקוי
            result['cleaned_title'] = InputValidator._clean_title(title)
            
            return result
            
        except Exception as e:
            logger.error(f"Title validation failed: {e}")
            result['is_valid'] = False
            result['errors'].append('Title validation error occurred')
            return result
    
    @staticmethod
    def validate_user_id(user_id: Union[int, str]) -> Dict[str, Any]:
        """בדיקת תקינות User ID של טלגרם"""
        result = {
            'is_valid': True,
            'errors': [],
            'normalized_id': None
        }
        
        try:
            # המרה למספר אם נדרש
            if isinstance(user_id, str):
                if not user_id.isdigit():
                    result['is_valid'] = False
                    result['errors'].append('User ID must be numeric')
                    return result
                user_id = int(user_id)
            
            # בדיקת טווח (Telegram user IDs הם חיוביים ולא גדולים מדי)
            if user_id <= 0:
                result['is_valid'] = False
                result['errors'].append('User ID must be positive')
            elif user_id > 2147483647:  # MAX_INT של Telegram API
                result['is_valid'] = False
                result['errors'].append('User ID exceeds maximum value')
            
            result['normalized_id'] = user_id
            
            return result
            
        except (ValueError, TypeError) as e:
            result['is_valid'] = False
            result['errors'].append('Invalid user ID format')
            return result
    
    @staticmethod
    def validate_request_id(request_id: Union[int, str]) -> Dict[str, Any]:
        """בדיקת תקינות Request ID"""
        result = {
            'is_valid': True,
            'errors': [],
            'normalized_id': None
        }
        
        try:
            if isinstance(request_id, str):
                if not request_id.isdigit():
                    result['is_valid'] = False
                    result['errors'].append('Request ID must be numeric')
                    return result
                request_id = int(request_id)
            
            if request_id <= 0:
                result['is_valid'] = False
                result['errors'].append('Request ID must be positive')
            
            result['normalized_id'] = request_id
            
            return result
            
        except (ValueError, TypeError):
            result['is_valid'] = False
            result['errors'].append('Invalid request ID format')
            return result
    
    # ========================= בדיקות ביטחון =========================
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """ניקוי וחיטוי קלט"""
        try:
            if not text:
                return ""
            
            # HTML encoding
            sanitized = html.escape(text)
            
            # הסרת תווי בקרה מסוכנים
            sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
            
            # ניקוי רווחים מיותרים
            sanitized = ' '.join(sanitized.split())
            
            # הגבלת אורך (כאמצעי ביטחון נוסף)
            if len(sanitized) > InputValidator.MAX_TEXT_LENGTH:
                sanitized = sanitized[:InputValidator.MAX_TEXT_LENGTH] + "..."
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Input sanitization failed: {e}")
            return text  # החזרת הטקסט המקורי במקרה של שגיאה
    
    @staticmethod
    def check_malicious_content(text: str) -> Dict[str, Any]:
        """בדיקת תוכן זדוני"""
        result = {
            'is_safe': True,
            'threats': [],
            'risk_level': 'low'
        }
        
        try:
            text_lower = text.lower()
            threat_count = 0
            
            for pattern in InputValidator.MALICIOUS_PATTERNS:
                if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                    result['is_safe'] = False
                    result['threats'].append(f'Malicious pattern detected: {pattern[:20]}...')
                    threat_count += 1
            
            # קביעת רמת סיכון
            if threat_count > 3:
                result['risk_level'] = 'high'
            elif threat_count > 1:
                result['risk_level'] = 'medium'
            elif threat_count > 0:
                result['risk_level'] = 'low'
            
            return result
            
        except Exception as e:
            logger.error(f"Malicious content check failed: {e}")
            result['is_safe'] = False
            result['threats'].append('Security check error')
            return result
    
    @staticmethod
    def check_spam_indicators(text: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """בדיקת אינדיקטורים לספאם"""
        result = {
            'is_spam': False,
            'score': 0.0,
            'indicators': [],
            'confidence': 'low'
        }
        
        try:
            text_lower = text.lower()
            spam_score = 0.0
            
            # בדיקת דפוסי ספאם
            for pattern in InputValidator.SPAM_INDICATORS:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                if matches > 0:
                    spam_score += matches * 0.2
                    result['indicators'].append(f'Spam pattern: {pattern[:20]}...')
            
            # בדיקות נוספות
            # הרבה לינקים
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
            if len(urls) > 2:
                spam_score += 0.3
                result['indicators'].append('Multiple URLs detected')
            
            # הרבה אמוג'ים
            emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', text))
            if emoji_count > 5:
                spam_score += 0.2
                result['indicators'].append('Excessive emojis')
            
            # טקסט חוזר
            words = text.split()
            if len(words) > 0:
                unique_words = set(words)
                repetition_ratio = 1 - (len(unique_words) / len(words))
                if repetition_ratio > 0.5:
                    spam_score += 0.3
                    result['indicators'].append('High word repetition')
            
            # הרבה אותיות גדולות
            caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
            if caps_ratio > 0.5 and len(text) > 10:
                spam_score += 0.2
                result['indicators'].append('Excessive capitalization')
            
            # קביעת תוצאה סופית
            result['score'] = min(spam_score, 1.0)
            
            if spam_score >= 0.8:
                result['is_spam'] = True
                result['confidence'] = 'high'
            elif spam_score >= 0.5:
                result['is_spam'] = True
                result['confidence'] = 'medium'
            elif spam_score >= 0.3:
                result['confidence'] = 'low'
            
            return result
            
        except Exception as e:
            logger.error(f"Spam check failed: {e}")
            result['indicators'].append('Spam check error')
            return result
    
    @staticmethod
    def validate_file_upload(file_data: Dict) -> Dict[str, Any]:
        """בדיקת תקינות העלאת קובץ"""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        try:
            # בדיקות בסיסיות
            if not file_data:
                result['is_valid'] = False
                result['errors'].append('No file data provided')
                return result
            
            # בדיקת גודל
            file_size = file_data.get('file_size', 0)
            max_size = 50 * 1024 * 1024  # 50MB
            
            if file_size > max_size:
                result['is_valid'] = False
                result['errors'].append(f'File too large (max {max_size // (1024*1024)}MB)')
            
            # בדיקת סוג קובץ
            file_name = file_data.get('file_name', '')
            allowed_extensions = {'.txt', '.pdf', '.doc', '.docx', '.jpg', '.png', '.zip'}
            
            if file_name:
                extension = '.' + file_name.split('.')[-1].lower()
                if extension not in allowed_extensions:
                    result['warnings'].append(f'File type {extension} may not be supported')
            
            # מידע על הקובץ
            result['file_info'] = {
                'name': file_name,
                'size': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'extension': extension if file_name else None,
                'is_text': extension in {'.txt', '.pdf', '.doc', '.docx'},
                'is_image': extension in {'.jpg', '.jpeg', '.png', '.gif'},
                'is_archive': extension in {'.zip', '.rar', '.7z'}
            }
            
            return result
            
        except Exception as e:
            logger.error(f"File validation failed: {e}")
            result['is_valid'] = False
            result['errors'].append('File validation error')
            return result
    
    @staticmethod
    def check_prohibited_content(text: str) -> Dict[str, Any]:
        """בדיקת תוכן אסור"""
        result = {
            'is_allowed': True,
            'violations': [],
            'severity': 'none'
        }
        
        try:
            text_lower = text.lower()
            violation_count = 0
            
            for pattern in InputValidator.PROHIBITED_CONTENT:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    result['is_allowed'] = False
                    result['violations'].append(f'Prohibited content detected')
                    violation_count += 1
            
            # קביעת חומרה
            if violation_count > 2:
                result['severity'] = 'high'
            elif violation_count > 0:
                result['severity'] = 'medium'
            
            return result
            
        except Exception as e:
            logger.error(f"Prohibited content check failed: {e}")
            result['is_allowed'] = False
            result['violations'].append('Content check error')
            return result
    
    # ========================= בדיקות תוכן =========================
    
    @staticmethod
    def validate_content_request(text: str) -> Dict[str, Any]:
        """בדיקת תקינות בקשת תוכן"""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'content_hints': {},
            'quality_score': 0.0
        }
        
        try:
            # בדיקות בסיסיות
            basic_validation = InputValidator.validate_user_input(text)
            if not basic_validation['is_valid']:
                result['is_valid'] = False
                result['errors'].extend(basic_validation['errors'])
                return result
            
            # בדיקת תוכן משמעותי
            if not InputValidator._has_meaningful_content(text):
                result['warnings'].append('Request may lack specific content information')
                result['quality_score'] -= 0.2
            
            # זיהוי סוג תוכן
            content_type = InputValidator._detect_content_type(text)
            result['content_hints']['type'] = content_type
            
            # זיהוי פרטים נוספים
            details = InputValidator._extract_content_details(text)
            result['content_hints'].update(details)
            
            # חישוב ציון איכות
            result['quality_score'] = InputValidator._calculate_request_quality(text, details)
            
            # המלצות לשיפור
            if result['quality_score'] < 0.6:
                result['warnings'].append('Consider adding more specific details (year, season, quality, etc.)')
            
            return result
            
        except Exception as e:
            logger.error(f"Content request validation failed: {e}")
            result['is_valid'] = False
            result['errors'].append('Content validation error')
            return result
    
    @staticmethod
    def validate_category(category: str) -> Dict[str, Any]:
        """בדיקת תקינות קטגוריה"""
        result = {
            'is_valid': True,
            'errors': [],
            'normalized_category': category
        }
        
        try:
            # רשימת קטגוריות מותרות
            valid_categories = {
                'series', 'movies', 'books', 'games', 'spotify', 
                'apps', 'software', 'anime', 'documentaries', 'general'
            }
            
            if not category:
                result['normalized_category'] = 'general'
            elif category.lower() not in valid_categories:
                result['is_valid'] = False
                result['errors'].append(f'Invalid category: {category}')
            else:
                result['normalized_category'] = category.lower()
            
            return result
            
        except Exception as e:
            logger.error(f"Category validation failed: {e}")
            result['is_valid'] = False
            result['errors'].append('Category validation error')
            return result
    
    @staticmethod
    def check_text_quality(text: str) -> Dict[str, Any]:
        """בדיקת איכות טקסט"""
        result = {
            'quality_score': 0.0,
            'factors': {},
            'suggestions': []
        }
        
        try:
            factors = {}
            
            # אורך טקסט
            length_score = min(len(text) / 100, 1.0) if len(text) < 100 else 1.0
            factors['length'] = length_score
            
            # מגוון מילים
            words = text.split()
            unique_words = set(words)
            diversity_score = len(unique_words) / max(len(words), 1)
            factors['diversity'] = diversity_score
            
            # תווים מיוחדים ומספרים (מצביעים על פרטים)
            special_chars_score = min(len(re.findall(r'[0-9]', text)) * 0.1, 0.3)
            factors['specificity'] = special_chars_score
            
            # תיקון כתיב (בדיקה בסיסית)
            spelling_score = 1.0 - min(len(re.findall(r'\b\w{15,}\b', text)) * 0.1, 0.3)
            factors['spelling'] = spelling_score
            
            # ציון כולל
            result['quality_score'] = sum(factors.values()) / len(factors)
            result['factors'] = factors
            
            # הצעות לשיפור
            if factors['length'] < 0.3:
                result['suggestions'].append('Add more details to your request')
            if factors['diversity'] < 0.5:
                result['suggestions'].append('Use more varied vocabulary')
            if factors['specificity'] < 0.2:
                result['suggestions'].append('Include specific details (year, season, quality)')
            
            return result
            
        except Exception as e:
            logger.error(f"Text quality check failed: {e}")
            return result
    
    # ========================= בדיקות פורמט =========================
    
    @staticmethod
    def validate_rating(rating: Union[int, str, float]) -> Dict[str, Any]:
        """בדיקת תקינות דירוג"""
        result = {
            'is_valid': True,
            'errors': [],
            'normalized_rating': None
        }
        
        try:
            # המרה למספר
            if isinstance(rating, str):
                if not rating.isdigit():
                    result['is_valid'] = False
                    result['errors'].append('Rating must be a number')
                    return result
                rating = int(rating)
            elif isinstance(rating, float):
                rating = int(rating)
            
            # בדיקת טווח
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                result['is_valid'] = False
                result['errors'].append('Rating must be between 1 and 5')
            else:
                result['normalized_rating'] = rating
            
            return result
            
        except (ValueError, TypeError):
            result['is_valid'] = False
            result['errors'].append('Invalid rating format')
            return result
    
    @staticmethod
    def validate_date_format(date_string: str, expected_format: str = '%Y-%m-%d') -> Dict[str, Any]:
        """בדיקת פורמט תאריך"""
        result = {
            'is_valid': True,
            'errors': [],
            'parsed_date': None
        }
        
        try:
            if not date_string:
                result['is_valid'] = False
                result['errors'].append('Date string is required')
                return result
            
            # ניסיון לפרסר את התאריך
            parsed_date = datetime.strptime(date_string, expected_format)
            result['parsed_date'] = parsed_date
            
            # בדיקת הגיונות (לא תאריך עתידי רחוק מדי)
            if parsed_date > datetime.now() + timedelta(days=365):
                result['errors'].append('Date is too far in the future')
            elif parsed_date < datetime(1900, 1, 1):
                result['errors'].append('Date is too far in the past')
            
            return result
            
        except ValueError as e:
            result['is_valid'] = False
            result['errors'].append(f'Invalid date format: {e}')
            return result
    
    @staticmethod
    def validate_admin_command(command: str, args: List[str]) -> Dict[str, Any]:
        """בדיקת תקינות פקודת מנהל"""
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'parsed_args': {}
        }
        
        try:
            # רשימת פקודות מותרות
            valid_commands = {
                'fulfill': {'min_args': 1, 'max_args': 10},
                'reject': {'min_args': 1, 'max_args': 10},
                'ban': {'min_args': 1, 'max_args': 5},
                'unban': {'min_args': 1, 'max_args': 3},
                'warn': {'min_args': 2, 'max_args': 5}
            }
            
            if command not in valid_commands:
                result['is_valid'] = False
                result['errors'].append(f'Unknown command: {command}')
                return result
            
            cmd_rules = valid_commands[command]
            
            # בדיקת מספר ארגומנטים
            if len(args) < cmd_rules['min_args']:
                result['is_valid'] = False
                result['errors'].append(f'Too few arguments (min {cmd_rules["min_args"]})')
            elif len(args) > cmd_rules['max_args']:
                result['warnings'].append(f'Many arguments provided (max {cmd_rules["max_args"]} recommended)')
            
            # בדיקת ארגומנט ראשון (בדרך כלל ID)
            if args and command in ['fulfill', 'reject', 'ban', 'unban']:
                id_validation = InputValidator.validate_request_id(args[0])
                if not id_validation['is_valid']:
                    result['is_valid'] = False
                    result['errors'].extend(id_validation['errors'])
                else:
                    result['parsed_args']['target_id'] = id_validation['normalized_id']
            
            # בדיקת ארגומנטים נוספים
            if len(args) > 1:
                result['parsed_args']['message'] = ' '.join(args[1:])
                
                # בדיקת תקינות ההודעה
                message_validation = InputValidator.validate_user_input(result['parsed_args']['message'])
                if not message_validation['is_valid']:
                    result['warnings'].append('Command message may contain issues')
            
            return result
            
        except Exception as e:
            logger.error(f"Admin command validation failed: {e}")
            result['is_valid'] = False
            result['errors'].append('Command validation error')
            return result
    
    # ========================= פונקציות עזר פרטיות =========================
    
    @staticmethod
    def _has_urls(text: str) -> bool:
        """בדיקה אם יש URLs בטקסט"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return bool(re.search(url_pattern, text))
    
    @staticmethod
    def _detect_language(text: str) -> str:
        """זיהוי שפה בסיסי"""
        hebrew_chars = len(re.findall(r'[\u0590-\u05FF]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        if hebrew_chars > english_chars:
            return 'hebrew'
        elif english_chars > hebrew_chars:
            return 'english'
        else:
            return 'mixed'
    
    @staticmethod
    def _calculate_text_quality(text: str) -> float:
        """חישוב ציון איכות טקסט"""
        try:
            score = 0.0
            
            # בדיקות בסיסיות
            if len(text) >= 10:
                score += 0.2
            if len(text.split()) >= 3:
                score += 0.2
            if re.search(r'[0-9]', text):
                score += 0.2  # פרטים מספריים
            if not re.search(r'[!@#$%^&*()_+=\[\]{}|;:,.<>?]', text):
                score += 0.2  # ללא תווים מיוחדים מוזרים
            if len(set(text.split())) / max(len(text.split()), 1) > 0.7:
                score += 0.2  # מגוון מילים
            
            return min(score, 1.0)
            
        except:
            return 0.5
    
    @staticmethod
    def _has_meaningful_content(text: str) -> bool:
        """בדיקה אם יש תוכן משמעותי"""
        # הסרת מילות עצירה ובדיקה
        meaningful_words = re.findall(r'\b\w{3,}\b', text.lower())
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        meaningful_words = [w for w in meaningful_words if w not in stop_words]
        
        return len(meaningful_words) >= 2
    
    @staticmethod
    def _extract_title_info(title: str) -> Dict[str, Any]:
        """חילוץ מידע מכותרת"""
        info = {}
        
        # שנה
        year_match = re.search(r'\b(19|20)\d{2}\b', title)
        if year_match:
            info['year'] = int(year_match.group())
        
        # עונה ופרק
        season_match = re.search(r'(?:season|עונה|s)[\s]*(\d+)', title, re.IGNORECASE)
        if season_match:
            info['season'] = int(season_match.group(1))
        
        episode_match = re.search(r'(?:episode|פרק|e|ep)[\s]*(\d+)', title, re.IGNORECASE)
        if episode_match:
            info['episode'] = int(episode_match.group(1))
        
        return info
    
    @staticmethod
    def _clean_title(title: str) -> str:
        """ניקוי כותרת"""
        # הסרת תווים מיוחדים
        cleaned = re.sub(r'[<>"\']', '', title)
        # ניקוי רווחים
        cleaned = ' '.join(cleaned.split())
        return cleaned.strip()
    
    @staticmethod
    def _detect_content_type(text: str) -> str:
        """זיהוי סוג תוכן"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['series', 'season', 'episode', 'סדרה', 'עונה', 'פרק']):
            return 'series'
        elif any(word in text_lower for word in ['movie', 'film', 'cinema', 'סרט']):
            return 'movies'
        elif any(word in text_lower for word in ['game', 'gaming', 'משחק']):
            return 'games'
        elif any(word in text_lower for word in ['book', 'ebook', 'pdf', 'ספר']):
            return 'books'
        elif any(word in text_lower for word in ['app', 'application', 'software', 'אפליקציה', 'תוכנה']):
            return 'apps'
        elif any(word in text_lower for word in ['music', 'song', 'album', 'spotify', 'מוזיקה', 'שיר']):
            return 'spotify'
        else:
            return 'general'
    
    @staticmethod
    def _extract_content_details(text: str) -> Dict[str, Any]:
        """חילוץ פרטי תוכן"""
        details = {}
        
        # איכות
        quality_match = re.search(r'\b(HD|4K|1080p|720p|480p|BluRay|DVD)\b', text, re.IGNORECASE)
        if quality_match:
            details['quality'] = quality_match.group().upper()
        
        # שפה
        if any(word in text.lower() for word in ['english', 'hebrew', 'עברית', 'אנגלית']):
            details['language_specified'] = True
        
        # שנה
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            details['year'] = int(year_match.group())
        
        return details
    
    @staticmethod
    def _calculate_request_quality(text: str, details: Dict) -> float:
        """חישוב איכות בקשה"""
        score = 0.3  # בסיס
        
        # אורך הטקסט
        if len(text) > 20:
            score += 0.2
        
        # פרטים ספציפיים
        if details.get('year'):
            score += 0.2
        if details.get('quality'):
            score += 0.1
        if details.get('language_specified'):
            score += 0.1
        
        # מילים משמעותיות
        if InputValidator._has_meaningful_content(text):
            score += 0.1
        
        return min(score, 1.0)


# ========================= פונקציות עזר גלובליות =========================

def clean_html_tags(text: str) -> str:
    """הסרת תגי HTML"""
    try:
        return re.sub(r'<[^>]+>', '', text)
    except:
        return text

def normalize_unicode(text: str) -> str:
    """נרמול Unicode"""
    try:
        import unicodedata
        return unicodedata.normalize('NFKD', text)
    except:
        return text

def check_language(text: str) -> str:
    """זיהוי שפה מתקדם יותר"""
    hebrew_score = len(re.findall(r'[\u0590-\u05FF]', text))
    english_score = len(re.findall(r'[a-zA-Z]', text))
    arabic_score = len(re.findall(r'[\u0600-\u06FF]', text))
    
    scores = {'hebrew': hebrew_score, 'english': english_score, 'arabic': arabic_score}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else 'unknown'

def extract_urls(text: str) -> List[str]:
    """חילוץ כל ה-URLs מטקסט"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.findall(url_pattern, text)