import json
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import sqlite3
from dataclasses import dataclass, asdict
import threading
import time

@dataclass
class FinancialAlert:
    id: Optional[int]
    user_id: str
    symbol: str
    event_type: str
    event_date: str
    alert_date: str  # Ne zaman uyarılacak
    description: str
    status: str  # 'active', 'triggered', 'cancelled'
    created_at: str
    triggered_at: Optional[str]

class FinancialAlertSystem:
    def __init__(self, db_file: str = "financial_alerts.db"):
        self.db_file = db_file
        self.init_database()
        self.start_alert_monitor()
    
    def init_database(self):
        """Veritabanını başlat ve tabloları oluştur"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_date TEXT NOT NULL,
                alert_date TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TEXT NOT NULL,
                triggered_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_alert(self, user_id: str, symbol: str, event_type: str, 
                     event_date: str, description: str, days_before: int = 1) -> Dict:
        """Yeni finansal alarm oluştur"""
        try:
            # Event tarihini parse et
            event_dt = datetime.strptime(event_date, "%Y-%m-%d")
            alert_dt = event_dt - timedelta(days=days_before)
            
            # Eğer alarm tarihi geçmişse, bugün uyar
            if alert_dt.date() <= date.today():
                alert_dt = datetime.now()
            
            alert_date = alert_dt.strftime("%Y-%m-%d")
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO financial_alerts 
                (user_id, symbol, event_type, event_date, alert_date, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, symbol, event_type, event_date, alert_date, description, 'active', created_at))
            
            alert_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'alert_id': alert_id,
                'message': f'{symbol} {event_type} için {days_before} gün önce alarm kuruldu'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_alerts(self, user_id: str, status: str = 'active') -> List[FinancialAlert]:
        """Kullanıcının alarmlarını getir"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM financial_alerts 
            WHERE user_id = ? AND status = ?
            ORDER BY alert_date ASC
        ''', (user_id, status))
        
        rows = cursor.fetchall()
        conn.close()
        
        alerts = []
        for row in rows:
            alert = FinancialAlert(
                id=row[0],
                user_id=row[1],
                symbol=row[2],
                event_type=row[3],
                event_date=row[4],
                alert_date=row[5],
                description=row[6],
                status=row[7],
                created_at=row[8],
                triggered_at=row[9]
            )
            alerts.append(alert)
        
        return alerts
    
    def get_pending_alerts(self) -> List[FinancialAlert]:
        """Tetiklenmeyi bekleyen alarmları getir"""
        today = date.today().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM financial_alerts 
            WHERE status = 'active' AND alert_date <= ?
            ORDER BY alert_date ASC
        ''', (today,))
        
        rows = cursor.fetchall()
        conn.close()
        
        alerts = []
        for row in rows:
            alert = FinancialAlert(
                id=row[0],
                user_id=row[1],
                symbol=row[2],
                event_type=row[3],
                event_date=row[4],
                alert_date=row[5],
                description=row[6],
                status=row[7],
                created_at=row[8],
                triggered_at=row[9]
            )
            alerts.append(alert)
        
        return alerts
    
    def mark_alert_triggered(self, alert_id: int) -> bool:
        """Alarmı tetiklendi olarak işaretle"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            triggered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                UPDATE financial_alerts 
                SET status = 'triggered', triggered_at = ?
                WHERE id = ?
            ''', (triggered_at, alert_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Alarm güncelleme hatası: {e}")
            return False
    
    def cancel_alert(self, alert_id: int, user_id: str) -> bool:
        """Alarmı iptal et"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE financial_alerts 
                SET status = 'cancelled'
                WHERE id = ? AND user_id = ?
            ''', (alert_id, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Alarm iptal hatası: {e}")
            return False
    
    def delete_alert(self, alert_id: int, user_id: str) -> bool:
        """Alarmı sil"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM financial_alerts 
                WHERE id = ? AND user_id = ?
            ''', (alert_id, user_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Alarm silme hatası: {e}")
            return False
    
    def start_alert_monitor(self):
        """Alarm monitörünü başlat"""
        def monitor_alerts():
            while True:
                try:
                    pending_alerts = self.get_pending_alerts()
                    
                    for alert in pending_alerts:
                        # Alarmı tetikle
                        if self.mark_alert_triggered(alert.id):
                            print(f"ALARM: {alert.user_id} için {alert.symbol} {alert.event_type} - {alert.description}")
                            
                            # Burada gerçek bildirim sistemi entegre edilebilir
                            # - Email gönderimi
                            # - Push notification
                            # - WebSocket ile real-time bildirim
                            # - SMS gönderimi
                    
                    # 5 dakikada bir kontrol et
                    time.sleep(300)
                    
                except Exception as e:
                    print(f"Alarm monitör hatası: {e}")
                    time.sleep(60)
        
        # Arka planda çalıştır
        monitor_thread = threading.Thread(target=monitor_alerts, daemon=True)
        monitor_thread.start()
    
    def get_alert_summary(self, user_id: str) -> Dict:
        """Kullanıcının alarm özetini getir"""
        active_alerts = self.get_user_alerts(user_id, 'active')
        triggered_alerts = self.get_user_alerts(user_id, 'triggered')
        cancelled_alerts = self.get_user_alerts(user_id, 'cancelled')
        
        return {
            'active_count': len(active_alerts),
            'triggered_count': len(triggered_alerts),
            'cancelled_count': len(cancelled_alerts),
            'total_count': len(active_alerts) + len(triggered_alerts) + len(cancelled_alerts),
            'next_alert': active_alerts[0] if active_alerts else None
        }
    
    def create_alert_from_calendar(self, user_id: str, symbol: str, 
                                  calendar_events: List[Dict], days_before: int = 1) -> Dict:
        """Finansal takvimden otomatik alarm oluştur"""
        created_count = 0
        skipped_count = 0
        errors = []
        
        for event in calendar_events:
            if event['status'] == 'bekliyor':  # Sadece bekleyen olaylar için
                # Önce mevcut alarmları kontrol et
                existing_alerts = self.get_user_alerts(user_id, 'active')
                
                # Aynı olay için zaten alarm var mı kontrol et
                duplicate_exists = any(
                    alert.symbol == symbol and 
                    alert.event_type == event['type'] and 
                    alert.event_date == event['date'] and
                    alert.status == 'active'
                    for alert in existing_alerts
                )
                
                if duplicate_exists:
                    skipped_count += 1
                    continue
                
                # Yeni alarm oluştur
                result = self.create_alert(
                    user_id=user_id,
                    symbol=symbol,
                    event_type=event['type'],
                    event_date=event['date'],
                    description=event['description'],
                    days_before=days_before
                )
                
                if result['success']:
                    created_count += 1
                else:
                    errors.append(f"{event['type']}: {result['error']}")
        
        message = f'{created_count} alarm oluşturuldu'
        if skipped_count > 0:
            message += f', {skipped_count} alarm zaten mevcut'
        
        return {
            'success': True,
            'created_count': created_count,
            'skipped_count': skipped_count,
            'errors': errors,
            'message': message
        }

# Test fonksiyonu
if __name__ == "__main__":
    alert_system = FinancialAlertSystem()
    
    # Test alarm oluştur
    result = alert_system.create_alert(
        user_id="test_user",
        symbol="THYAO",
        event_type="bilanço",
        event_date="2025-08-31",
        description="2025 Yılı 2. Çeyrek Bilanço",
        days_before=1
    )
    
    print(f"Alarm oluşturma sonucu: {result}")
    
    # Kullanıcı alarmlarını getir
    alerts = alert_system.get_user_alerts("test_user")
    print(f"Kullanıcı alarmları: {len(alerts)}")
    
    # Bekleyen alarmları getir
    pending = alert_system.get_pending_alerts()
    print(f"Bekleyen alarmlar: {len(pending)}") 