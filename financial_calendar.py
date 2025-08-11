import json
import csv
from datetime import datetime, date
from typing import List, Dict, Optional
import os
import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin

class FinancialCalendar:
    def __init__(self, data_file: str = "financial_calendar.json"):
        self.data_file = data_file
        self.events = self.load_events()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def load_events(self) -> Dict:
        """Finansal takvim verilerini yükle"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        else:
            return {}
    
    def scrape_kap_events(self, symbol: str) -> List[Dict]:
        """KAP'tan şirket duyurularını çek"""
        try:
            # KAP arama URL'si
            search_url = f"https://www.kap.org.tr/tr/sirket-bilgileri/{symbol}"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Duyuru tablosunu bul
            announcement_table = soup.find('table', {'class': 'announcement-table'})
            if not announcement_table:
                # Alternatif arama
                announcement_table = soup.find('div', {'class': 'announcements'})
            
            if announcement_table:
                rows = announcement_table.find_all('tr')
                for row in rows[1:]:  # Header'ı atla
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        try:
                            date_text = cells[0].get_text(strip=True)
                            title = cells[1].get_text(strip=True)
                            category = cells[2].get_text(strip=True)
                            
                            # Tarihi parse et
                            event_date = self.parse_turkish_date(date_text)
                            if event_date:
                                event_type = self.categorize_announcement(title, category)
                                events.append({
                                    "type": event_type,
                                    "date": event_date.strftime("%Y-%m-%d"),
                                    "description": title,
                                    "source": "KAP",
                                    "status": "bekliyor" if event_date > date.today() else "tamamlandı"
                                })
                        except Exception as e:
                            continue
            
            return events
            
        except Exception as e:
            print(f"KAP scraping hatası ({symbol}): {e}")
            return []
    
    def scrape_bist_events(self, symbol: str) -> List[Dict]:
        """BIST'ten şirket bilgilerini çek"""
        try:
            # BIST şirket sayfası
            bist_url = f"https://borsaistanbul.com/tr/sirketler/{symbol}"
            
            response = self.session.get(bist_url, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Genel kurul tarihleri
            gk_section = soup.find('div', string=re.compile(r'Genel Kurul', re.IGNORECASE))
            if gk_section:
                parent = gk_section.find_parent()
                if parent:
                    date_elem = parent.find('span', {'class': 'date'}) or parent.find('time')
                    if date_elem:
                        date_text = date_elem.get_text(strip=True)
                        event_date = self.parse_turkish_date(date_text)
                        if event_date:
                            events.append({
                                "type": "genel_kurul",
                                "date": event_date.strftime("%Y-%m-%d"),
                                "description": "Genel Kurul Toplantısı",
                                "source": "BIST",
                                "status": "bekliyor" if event_date > date.today() else "tamamlandı"
                            })
            
            return events
            
        except Exception as e:
            print(f"BIST scraping hatası ({symbol}): {e}")
            return []
    
    def scrape_finansal_haberler(self, symbol: str) -> List[Dict]:
        """Finansal haber sitelerinden bilgi çek"""
        try:
            # BloombergHT veya benzeri siteden
            news_url = f"https://www.bloomberght.com/borsa/hisse/{symbol}"
            
            response = self.session.get(news_url, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Bilanço haberleri
            news_items = soup.find_all('div', {'class': 'news-item'})
            for item in news_items[:5]:  # Son 5 haber
                title = item.find('h3')
                if title:
                    title_text = title.get_text(strip=True)
                    if any(keyword in title_text.lower() for keyword in ['bilanço', 'gelir', 'kar', 'zarar']):
                        date_elem = item.find('time') or item.find('span', {'class': 'date'})
                        if date_elem:
                            date_text = date_elem.get_text(strip=True)
                            event_date = self.parse_turkish_date(date_text)
                            if event_date:
                                events.append({
                                    "type": "bilanço",
                                    "date": event_date.strftime("%Y-%m-%d"),
                                    "description": title_text,
                                    "source": "BloombergHT",
                                    "status": "bekliyor" if event_date > date.today() else "tamamlandı"
                                })
            
            return events
            
        except Exception as e:
            print(f"Finansal haber scraping hatası ({symbol}): {e}")
            return []
    
    def parse_turkish_date(self, date_text: str) -> Optional[date]:
        """Türkçe tarih formatını parse et"""
        try:
            # Farklı tarih formatlarını dene
            date_patterns = [
                r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # 15.03.2025
                r'(\d{1,2})/(\d{1,2})/(\d{4})',   # 15/03/2025
                r'(\d{1,2})-(\d{1,2})-(\d{4})',   # 15-03-2025
                r'(\d{4})-(\d{1,2})-(\d{1,2})',   # 2025-03-15
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, date_text)
                if match:
                    if len(match.group(1)) == 4:  # Yıl ilk sırada
                        year, month, day = match.groups()
                    else:  # Gün ilk sırada
                        day, month, year = match.groups()
                    
                    return date(int(year), int(month), int(day))
            
            # Türkçe ay isimleri
            turkish_months = {
                'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
                'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
                'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
            }
            
            for month_name, month_num in turkish_months.items():
                if month_name in date_text.lower():
                    # "15 Mart 2025" formatı
                    day_match = re.search(r'(\d{1,2})', date_text)
                    year_match = re.search(r'(\d{4})', date_text)
                    if day_match and year_match:
                        return date(int(year_match.group(1)), month_num, int(day_match.group(1)))
            
            return None
            
        except Exception as e:
            print(f"Tarih parse hatası: {e}")
            return None
    
    def categorize_announcement(self, title: str, category: str) -> str:
        """Duyuru başlığına göre kategori belirle"""
        title_lower = title.lower()
        category_lower = category.lower()
        
        if any(keyword in title_lower for keyword in ['bilanço', 'finansal', 'gelir', 'kar', 'zarar']):
            return "bilanço"
        elif any(keyword in title_lower for keyword in ['genel kurul', 'gk', 'toplantı']):
            return "genel_kurul"
        elif any(keyword in title_lower for keyword in ['temettü', 'kar payı', 'dividend']):
            return "temettü"
        elif any(keyword in title_lower for keyword in ['hisse', 'sermaye', 'artırım']):
            return "sermaye_artırımı"
        elif any(keyword in title_lower for keyword in ['birleşme', 'devralma', 'satın alma']):
            return "kurumsal_olay"
        else:
            return "diğer"
    
    def update_company_events(self, symbol: str, force_update: bool = False) -> bool:
        """Şirket olaylarını güncelle"""
        try:
            # Son güncelleme kontrolü (24 saat)
            if not force_update and symbol in self.events:
                last_update = self.events[symbol].get('last_update')
                if last_update:
                    last_update_date = datetime.strptime(last_update, "%Y-%m-%d").date()
                    if (date.today() - last_update_date).days < 1:
                        return True  # Güncel, güncelleme gerekmez
            
            print(f"{symbol} için finansal takvim güncelleniyor...")
            
            # Farklı kaynaklardan veri çek
            kap_events = self.scrape_kap_events(symbol)
            bist_events = self.scrape_bist_events(symbol)
            news_events = self.scrape_finansal_haberler(symbol)
            
            # Tüm olayları birleştir
            all_events = kap_events + bist_events + news_events
            
            # Tekrarlanan olayları temizle
            unique_events = []
            seen_descriptions = set()
            
            for event in all_events:
                event_key = f"{event['date']}_{event['type']}_{event['description'][:50]}"
                if event_key not in seen_descriptions:
                    seen_descriptions.add(event_key)
                    unique_events.append(event)
            
            # Şirket bilgilerini güncelle
            if symbol not in self.events:
                self.events[symbol] = {
                    "company_name": symbol,
                    "events": [],
                    "last_update": date.today().strftime("%Y-%m-%d")
                }
            
            self.events[symbol]["events"] = unique_events
            self.events[symbol]["last_update"] = date.today().strftime("%Y-%m-%d")
            
            # Verileri kaydet
            self.save_events()
            
            print(f"{symbol} için {len(unique_events)} olay güncellendi")
            return True
            
        except Exception as e:
            print(f"{symbol} güncelleme hatası: {e}")
            return False
    
    def update_all_companies(self, symbols: List[str] = None) -> Dict[str, bool]:
        """Tüm şirketleri güncelle"""
        if symbols is None:
            symbols = ['THYAO', 'KCHOL', 'GARAN', 'AKBNK', 'ISCTR', 'SAHOL', 'ASELS', 'EREGL']
        
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.update_company_events(symbol)
                time.sleep(2)  # Rate limiting
            except Exception as e:
                results[symbol] = False
                print(f"{symbol} güncelleme hatası: {e}")
        
        return results
    
    def get_company_events(self, symbol: str, auto_update: bool = True) -> Optional[Dict]:
        """Belirli şirketin finansal olaylarını getir"""
        if auto_update and symbol not in self.events:
            self.update_company_events(symbol)
        
        return self.events.get(symbol.upper())
    
    def save_events(self):
        """Finansal takvim verilerini kaydet"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)
    
    def add_event(self, symbol: str, event_type: str, event_date: str, 
                  description: str, source: str = "KAP", status: str = "bekliyor"):
        """Yeni finansal olay ekle"""
        if symbol not in self.events:
            self.events[symbol] = {
                "company_name": symbol,
                "events": [],
                "last_update": date.today().strftime("%Y-%m-%d")
            }
        
        event = {
            "type": event_type,
            "date": event_date,
            "description": description,
            "source": source,
            "status": status
        }
        
        self.events[symbol]["events"].append(event)
        self.save_events()
        return True
    
    def search_events(self, query: str) -> List[Dict]:
        """Finansal olaylarda arama yap"""
        results = []
        query_lower = query.lower()
        
        for symbol, company_data in self.events.items():
            for event in company_data["events"]:
                if (query_lower in event["type"].lower() or 
                    query_lower in event["description"].lower() or
                    query_lower in company_data["company_name"].lower()):
                    results.append({
                        "symbol": symbol,
                        "company_name": company_data["company_name"],
                        **event
                    })
        
        return results
    
    def get_upcoming_events(self, days: int = 30) -> List[Dict]:
        """Yaklaşan finansal olayları getir"""
        today = date.today()
        upcoming = []
        
        for symbol, company_data in self.events.items():
            for event in company_data["events"]:
                try:
                    event_date = datetime.strptime(event["date"], "%Y-%m-%d").date()
                    if event_date >= today and (event_date - today).days <= days:
                        upcoming.append({
                            "symbol": symbol,
                            "company_name": company_data["company_name"],
                            **event
                        })
                except:
                    continue
        
        # Tarihe göre sırala
        upcoming.sort(key=lambda x: x["date"])
        return upcoming
    
    def import_from_csv(self, csv_file: str) -> bool:
        """CSV dosyasından finansal takvim verisi yükle"""
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.add_event(
                        symbol=row["symbol"],
                        event_type=row["type"],
                        event_date=row["date"],
                        description=row["description"],
                        source=row.get("source", "KAP"),
                        status=row.get("status", "bekliyor")
                    )
            return True
        except Exception as e:
            print(f"CSV yükleme hatası: {e}")
            return False
    
    def export_to_csv(self, csv_file: str) -> bool:
        """Finansal takvim verilerini CSV olarak dışa aktar"""
        try:
            with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ["symbol", "company_name", "type", "date", "description", "source", "status"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for symbol, company_data in self.events.items():
                    for event in company_data["events"]:
                        writer.writerow({
                            "symbol": symbol,
                            "company_name": company_data["company_name"],
                            **event
                        })
            return True
        except Exception as e:
            print(f"CSV dışa aktarma hatası: {e}")
            return False
    
    def get_event_types(self) -> List[str]:
        """Mevcut olay türlerini getir"""
        types = set()
        for company_data in self.events.values():
            for event in company_data["events"]:
                types.add(event["type"])
        return list(types)
    
    def get_companies(self) -> List[str]:
        """Takvimde bulunan şirketleri getir"""
        return list(self.events.keys())
    
    def get_calendar_summary(self) -> Dict:
        """Takvim özeti getir"""
        total_companies = len(self.events)
        total_events = sum(len(company_data["events"]) for company_data in self.events.values())
        
        # Olay türlerine göre dağılım
        event_types = {}
        for company_data in self.events.values():
            for event in company_data["events"]:
                event_type = event["type"]
                event_types[event_type] = event_types.get(event_type, 0) + 1
        
        # Yaklaşan olaylar
        upcoming_count = len(self.get_upcoming_events(30))
        
        return {
            "total_companies": total_companies,
            "total_events": total_events,
            "event_types": event_types,
            "upcoming_events": upcoming_count,
            "last_updated": max([company_data.get("last_update", "1900-01-01") 
                                for company_data in self.events.values()], default="1900-01-01")
        }

# Test fonksiyonu
if __name__ == "__main__":
    calendar = FinancialCalendar()
    
    # Test: THYAO için veri çek
    print("THYAO için finansal takvim güncelleniyor...")
    success = calendar.update_company_events("THYAO")
    print(f"Güncelleme başarılı: {success}")
    
    # Test: THYAO olayları
    thyao_events = calendar.get_company_events("THYAO")
    if thyao_events:
        print(f"\nTHYAO ({thyao_events['company_name']}) olayları:")
        for event in thyao_events["events"]:
            print(f"- {event['type']}: {event['date']} - {event['description']}")
    
    # Test: Takvim özeti
    summary = calendar.get_calendar_summary()
    print(f"\nTakvim Özeti:")
    print(f"- Toplam şirket: {summary['total_companies']}")
    print(f"- Toplam olay: {summary['total_events']}")
    print(f"- Yaklaşan olaylar (30 gün): {summary['upcoming_events']}")
    print(f"- Son güncelleme: {summary['last_updated']}") 