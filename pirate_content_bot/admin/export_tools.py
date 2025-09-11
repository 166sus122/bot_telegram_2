#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ExportManager - כלי ייצוא נתונים מתקדם
ייצוא נתונים בפורמטים שונים עם אפשרויות מתקדמות
"""

import csv
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import zipfile
import tempfile
import os

logger = logging.getLogger(__name__)

class ExportManager:
    """מנהל ייצוא נתונים מתקדם"""
    
    def __init__(self, storage_manager):
        self.storage = storage_manager
        self.export_history = []
        
        # הגדרות ברירת מחדל
        self.default_export_path = "exports"
        self.max_export_age_days = 7
        
        # יצירת תיקיית ייצוא
        self.export_path = Path(self.default_export_path)
        self.export_path.mkdir(exist_ok=True)
        
        logger.info("✅ ExportManager initialized")
    
    # ========================= ייצוא בסיסי =========================
    
    async def export_requests(self, filters: Dict = None, format: str = 'csv') -> Dict[str, Any]:
        """ייצוא בקשות"""
        try:
            logger.info(f"📤 Starting requests export in {format} format")
            
            # קבלת נתוני בקשות
            requests_data = await self._get_requests_data(filters)
            
            if not requests_data:
                return {'success': False, 'error': 'No data to export'}
            
            # יצירת קובץ
            filename = f"requests_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            
            if format.lower() == 'csv':
                filepath = await self.to_csv(requests_data, filename)
            elif format.lower() == 'json':
                filepath = await self.to_json(requests_data, filename)
            elif format.lower() == 'xlsx':
                filepath = await self.to_excel(requests_data, filename)
            else:
                return {'success': False, 'error': f'Unsupported format: {format}'}
            
            # רישום בהיסטוריה
            self._record_export('requests', format, filepath, len(requests_data))
            
            logger.info(f"✅ Requests export completed: {filepath}")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'record_count': len(requests_data),
                'format': format
            }
            
        except Exception as e:
            logger.error(f"❌ Error exporting requests: {e}")
            return {'success': False, 'error': str(e)}
    
    async def export_users(self, filters: Dict = None, format: str = 'csv') -> Dict[str, Any]:
        """ייצוא משתמשים"""
        try:
            logger.info(f"📤 Starting users export in {format} format")
            
            # קבלת נתוני משתמשים
            users_data = await self._get_users_data(filters)
            
            if not users_data:
                return {'success': False, 'error': 'No user data to export'}
            
            # יצירת קובץ
            filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            
            if format.lower() == 'csv':
                filepath = await self.to_csv(users_data, filename)
            elif format.lower() == 'json':
                filepath = await self.to_json(users_data, filename)
            elif format.lower() == 'xlsx':
                filepath = await self.to_excel(users_data, filename)
            else:
                return {'success': False, 'error': f'Unsupported format: {format}'}
            
            # רישום בהיסטוריה
            self._record_export('users', format, filepath, len(users_data))
            
            logger.info(f"✅ Users export completed: {filepath}")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'record_count': len(users_data),
                'format': format
            }
            
        except Exception as e:
            logger.error(f"❌ Error exporting users: {e}")
            return {'success': False, 'error': str(e)}
    
    async def export_ratings(self, filters: Dict = None, format: str = 'csv') -> Dict[str, Any]:
        """ייצוא דירוגים"""
        try:
            logger.info(f"📤 Starting ratings export in {format} format")
            
            # קבלת נתוני דירוגים
            ratings_data = await self._get_ratings_data(filters)
            
            if not ratings_data:
                return {'success': False, 'error': 'No ratings data to export'}
            
            # יצירת קובץ
            filename = f"ratings_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            
            if format.lower() == 'csv':
                filepath = await self.to_csv(ratings_data, filename)
            elif format.lower() == 'json':
                filepath = await self.to_json(ratings_data, filename)
            elif format.lower() == 'xlsx':
                filepath = await self.to_excel(ratings_data, filename)
            else:
                return {'success': False, 'error': f'Unsupported format: {format}'}
            
            # רישום בהיסטוריה
            self._record_export('ratings', format, filepath, len(ratings_data))
            
            logger.info(f"✅ Ratings export completed: {filepath}")
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'record_count': len(ratings_data),
                'format': format
            }
            
        except Exception as e:
            logger.error(f"❌ Error exporting ratings: {e}")
            return {'success': False, 'error': str(e)}
    
    async def export_system_logs(self, date_range: Dict, format: str = 'txt') -> Dict[str, Any]:
        """ייצוא לוגי מערכת"""
        try:
            start_date = datetime.fromisoformat(date_range['start_date'])
            end_date = datetime.fromisoformat(date_range['end_date'])
            
            logger.info(f"📤 Starting system logs export from {start_date} to {end_date}")
            
            # קריאת לוגי מערכת
            logs_data = await self._get_system_logs(start_date, end_date)
            
            # יצירת קובץ
            filename = f"system_logs_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.{format}"
            filepath = self.export_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                if format == 'txt':
                    for log_entry in logs_data:
                        f.write(f"{log_entry}\n")
                elif format == 'json':
                    json.dump(logs_data, f, ensure_ascii=False, indent=2)
            
            self._record_export('system_logs', format, filepath, len(logs_data))
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'record_count': len(logs_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Error exporting system logs: {e}")
            return {'success': False, 'error': str(e)}
    
    # ========================= ייצוא מתקדם =========================
    
    async def export_custom_report(self, query: str, format: str = 'xlsx') -> Dict[str, Any]:
        """ייצוא דוח מותאם אישית"""
        try:
            logger.info(f"📤 Starting custom report export: {query}")
            
            # ביצוע השאילתה המותאמת
            report_data = await self._execute_custom_query(query)
            
            if not report_data:
                return {'success': False, 'error': 'No data returned from query'}
            
            # יצירת קובץ
            filename = f"custom_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
            
            if format == 'xlsx':
                filepath = await self.to_excel(report_data, filename, sheets={'Report': report_data})
            else:
                filepath = await self.to_csv(report_data, filename)
            
            self._record_export('custom_report', format, filepath, len(report_data))
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'record_count': len(report_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Error exporting custom report: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_analytics_export(self, period: str, metrics: List[str]) -> Dict[str, Any]:
        """יצירת ייצוא אנליטיקס"""
        try:
            logger.info(f"📊 Creating analytics export for {period} with metrics: {metrics}")
            
            # חישוב תקופה
            end_date = datetime.now()
            if period == 'week':
                start_date = end_date - timedelta(weeks=1)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=7)
            
            # איסוף נתוני אנליטיקס
            analytics_data = {}
            
            for metric in metrics:
                analytics_data[metric] = await self._calculate_metric(metric, start_date, end_date)
            
            # יצירת קובץ Excel עם גרפים
            filename = f"analytics_{period}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            filepath = await self.export_with_charts(analytics_data, ['line', 'bar'])
            
            self._record_export('analytics', 'xlsx', filepath, len(analytics_data))
            
            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'metrics_count': len(metrics),
                'period': period
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating analytics export: {e}")
            return {'success': False, 'error': str(e)}
    
    async def export_with_charts(self, data: Dict[str, Any], chart_types: List[str]) -> Path:
        """ייצוא עם גרפים"""
        try:
            filename = f"charts_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = self.export_path / filename
            
            # כאן יהיה קוד ליצירת Excel עם גרפים
            # לעת עתה נשמור כ-JSON
            json_data = {
                'data': data,
                'chart_types': chart_types,
                'generated_at': datetime.now().isoformat()
            }
            
            json_filepath = filepath.with_suffix('.json')
            
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            return json_filepath
            
        except Exception as e:
            logger.error(f"❌ Error exporting with charts: {e}")
            raise
    
    async def schedule_recurring_export(self, export_config: Dict, schedule: str) -> Dict[str, Any]:
        """תזמון ייצוא חוזר"""
        try:
            export_id = f"recurring_{datetime.now().timestamp()}"
            
            # כאן תהיה אינטגרציה עם מתזמן המשימות
            logger.info(f"📅 Scheduled recurring export: {export_id} with schedule: {schedule}")
            
            return {
                'success': True,
                'export_id': export_id,
                'schedule': schedule,
                'config': export_config,
                'next_run': 'Will be calculated by scheduler'
            }
            
        except Exception as e:
            logger.error(f"❌ Error scheduling recurring export: {e}")
            return {'success': False, 'error': str(e)}
    
    # ========================= פורמטים שונים =========================
    
    async def to_csv(self, data: List[Dict], filename: str) -> Path:
        """המרה ל-CSV"""
        filepath = self.export_path / filename
        
        if not data:
            raise ValueError("No data to export")
        
        # כתיבה ל-CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                # ניקוי נתונים מורכבים
                clean_row = {}
                for key, value in row.items():
                    if isinstance(value, (dict, list)):
                        clean_row[key] = json.dumps(value, ensure_ascii=False)
                    elif isinstance(value, datetime):
                        clean_row[key] = value.isoformat()
                    else:
                        clean_row[key] = value
                writer.writerow(clean_row)
        
        return filepath
    
    async def to_json(self, data: List[Dict], filename: str) -> Path:
        """המרה ל-JSON עם טיפול בdatetime objects"""
        from pirate_content_bot.utils.json_helpers import safe_json_dumps
        
        filepath = self.export_path / filename
        
        if not data:
            raise ValueError("No data to export")
        
        # יצירת JSON עם datetime support
        try:
            json_output = {
                'metadata': {
                    'export_timestamp': datetime.now(),
                    'record_count': len(data),
                    'export_type': 'data_export',
                    'version': '2.0'
                },
                'data': data
            }
            
            # שימוש בfafe_json_dumps שמטפל בdatetime
            json_content = safe_json_dumps(json_output, indent=2)
            
            # כתיבה לקובץ
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                jsonfile.write(json_content)
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating JSON export: {e}")
            raise
    
    async def to_excel(self, data: List[Dict], filename: str) -> Path:
        """המרה ל-Excel (placeholder)"""
        # לעת עתה נשמור כ-JSON
        json_filename = filename.replace('.xlsx', '.json')
        return await self.to_json(data, json_filename)
    
    def _record_export(self, export_type: str, format: str, filepath: Path, record_count: int):
        """רישום ייצוא בהיסטוריה"""
        export_record = {
            'timestamp': datetime.now(),
            'export_type': export_type,
            'format': format,
            'filepath': str(filepath),
            'record_count': record_count,
            'file_size': filepath.stat().st_size if filepath.exists() else 0
        }
        self.export_history.append(export_record)
    
    # ========================= פונקציות עזר נוספות =========================
    
    async def _get_requests_data(self, filters: Dict = None) -> List[Dict]:
        """קבלת נתוני בקשות מהמערכת"""
        # placeholder - יחזיר נתונים מהstorage
        return []
    
    async def _get_users_data(self, filters: Dict = None) -> List[Dict]:
        """קבלת נתוני משתמשים מהמערכת"""
        # placeholder
        return []
    
    async def _get_ratings_data(self, filters: Dict = None) -> List[Dict]:
        """קבלת נתוני דירוגים מהמערכת"""
        # placeholder
        return []