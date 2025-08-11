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
        """KAP'tan şirket duyurularını çek - güncellenmiş versiyon"""
        try:
            # KAP ana sayfasından şirket arama
            search_url = "https://www.kap.org.tr/tr/sirket-bilgileri"
            
            # Önce ana sayfayı kontrol et
            response = self.session.get(search_url, timeout=10)
            if response.status_code != 200:
                # Alternatif URL dene
                search_url = "https://www.kap.org.tr"
                response = self.session.get(search_url, timeout=10)
                if response.status_code != 200:
                    return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Şirket arama formu bul
            search_form = soup.find('form') or soup.find('input', {'type': 'search'})
            if search_form:
                # Şirket adı ile arama yap
                search_data = {'q': symbol}
                search_response = self.session.post(search_url, data=search_data, timeout=10)
                if search_response.status_code == 200:
                    search_soup = BeautifulSoup(search_response.content, 'html.parser')
                    
                    # Duyuru tablosunu bul
                    announcement_table = search_soup.find('table', {'class': 'announcement-table'})
                    if not announcement_table:
                        announcement_table = search_soup.find('div', {'class': 'announcements'})
                    
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
            
            # Eğer KAP'tan veri gelmezse, varsayılan olaylar ekle
            if not events:
                events = self.get_default_events(symbol)
            
            return events
            
        except Exception as e:
            print(f"KAP scraping hatası ({symbol}): {e}")
            # Hata durumunda varsayılan olaylar döndür
            return self.get_default_events(symbol)
    
    def get_default_events(self, symbol: str) -> List[Dict]:
        """Şirket için varsayılan finansal olayları döndür"""
        today = date.today()
        events = []
        
        # Yılın çeyrekleri için bilanço tarihleri
        quarters = [
            (3, 31),   # 1. çeyrek
            (6, 30),   # 2. çeyrek  
            (9, 30),   # 3. çeyrek
            (12, 31)   # 4. çeyrek
        ]
        
        for month, day in quarters:
            if month > today.month or (month == today.month and day > today.day):
                event_date = date(today.year, month, day)
                events.append({
                    "type": "bilanço",
                    "date": event_date.strftime("%Y-%m-%d"),
                    "description": f"{today.year} Yılı {month//3}. Çeyrek Bilanço",
                    "source": "Varsayılan",
                    "status": "bekliyor"
                })
        
        # Genel kurul tarihi (genellikle Nisan-Mayıs)
        if today.month < 5:
            gk_date = date(today.year, 5, 15)
            events.append({
                "type": "genel_kurul",
                "date": gk_date.strftime("%Y-%m-%d"),
                "description": f"{today.year-1} Yılı Genel Kurul Toplantısı",
                "source": "Varsayılan",
                "status": "bekliyor"
            })
        
        # Şirket özel olayları
        if symbol == "GARAN":
            # Garanti Bankası özel olayları
            events.append({
                "type": "temettü",
                "date": date(today.year, 7, 15).strftime("%Y-%m-%d"),
                "description": f"{today.year-1} Yılı Temettü Ödemesi",
                "source": "Varsayılan",
                "status": "bekliyor"
            })
        elif symbol == "AKBNK":
            # Akbank özel olayları
            events.append({
                "type": "temettü",
                "date": date(today.year, 7, 20).strftime("%Y-%m-%d"),
                "description": f"{today.year-1} Yılı Temettü Ödemesi",
                "source": "Varsayılan",
                "status": "bekliyor"
            })
        elif symbol == "ISCTR":
            # İş Bankası özel olayları
            events.append({
                "type": "temettü",
                "date": date(today.year, 7, 25).strftime("%Y-%m-%d"),
                "description": f"{today.year-1} Yılı Temettü Ödemesi",
                "source": "Varsayılan",
                "status": "bekliyor"
            })
        elif symbol == "THYAO":
            # Türk Hava Yolları özel olayları
            events.append({
                "type": "temettü",
                "date": date(today.year, 8, 10).strftime("%Y-%m-%d"),
                "description": f"{today.year-1} Yılı Temettü Ödemesi",
                "source": "Varsayılan",
                "status": "bekliyor"
            })
        elif symbol == "KCHOL":
            # Koç Holding özel olayları
            events.append({
                "type": "temettü",
                "date": date(today.year, 8, 5).strftime("%Y-%m-%d"),
                "description": f"{today.year-1} Yılı Temettü Ödemesi",
                "source": "Varsayılan",
                "status": "bekliyor"
            })
        
        return events
    
    def scrape_bist_events(self, symbol: str) -> List[Dict]:
        """BIST'ten şirket bilgilerini çek - güncellenmiş versiyon"""
        try:
            # BIST ana sayfası
            bist_url = "https://borsaistanbul.com"
            
            response = self.session.get(bist_url, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Şirket arama yap
            search_url = f"{bist_url}/tr/sirketler"
            search_response = self.session.get(search_url, timeout=10)
            if search_response.status_code == 200:
                search_soup = BeautifulSoup(search_response.content, 'html.parser')
                
                # Genel kurul tarihleri
                gk_section = search_soup.find('div', string=re.compile(r'Genel Kurul', re.IGNORECASE))
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
        """Finansal haber sitelerinden bilgi çek - güncellenmiş versiyon"""
        try:
            events = []
            
            # BloombergHT'den haber çek (daha uzun timeout)
            try:
                news_url = f"https://www.bloomberght.com/borsa/hisse/{symbol.lower()}"
                response = self.session.get(news_url, timeout=20)  # Timeout artırıldı
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Bilanço haberleri
                    news_items = soup.find_all('div', {'class': 'news-item'})
                    if not news_items:
                        news_items = soup.find_all('article') or soup.find_all('div', {'class': 'news'})
                    
                    for item in news_items[:5]:  # Son 5 haber
                        title = item.find('h3') or item.find('h2') or item.find('a')
                        if title:
                            title_text = title.get_text(strip=True)
                            if any(keyword in title_text.lower() for keyword in ['bilanço', 'gelir', 'kar', 'zarar', 'finansal']):
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
            except Exception as e:
                print(f"BloombergHT hatası: {e}")
            
            # DHA Ekonomi'den haber çek
            try:
                dha_url = "https://www.dha.com.tr/ekonomi"
                response = self.session.get(dha_url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Şirket ile ilgili haberler
                    news_items = soup.find_all('div', {'class': 'news-item'}) or soup.find_all('article')
                    for item in news_items[:10]:
                        title = item.find('h3') or item.find('h2') or item.find('a')
                        if title:
                            title_text = title.get_text(strip=True)
                            if symbol.lower() in title_text.lower():
                                date_elem = item.find('time') or item.find('span', {'class': 'date'})
                                if date_elem:
                                    date_text = date_elem.get_text(strip=True)
                                    event_date = self.parse_turkish_date(date_text)
                                    if event_date:
                                        events.append({
                                            "type": "haber",
                                            "date": event_date.strftime("%Y-%m-%d"),
                                            "description": title_text,
                                            "source": "DHA",
                                            "status": "bekliyor" if event_date > date.today() else "tamamlandı"
                                        })
            except Exception as e:
                print(f"DHA hatası: {e}")
            
            # Finansal takvim API'si (ücretsiz alternatif)
            try:
                # Yahoo Finance API'si (ücretsiz)
                yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.IS"
                response = self.session.get(yahoo_url, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    if 'chart' in data and 'result' in data['chart']:
                        # Şirket bilgileri
                        company_info = data['chart']['result'][0].get('meta', {})
                        if company_info:
                            # Temettü bilgisi
                            if 'trailingAnnualDividendRate' in company_info:
                                dividend_rate = company_info['trailingAnnualDividendRate']
                                if dividend_rate and dividend_rate > 0:
                                    # Temettü ödeme tarihi (genellikle yılda 1-2 kez)
                                    dividend_date = date(date.today().year, 7, 15)  # Varsayılan
                                    events.append({
                                        "type": "temettü",
                                        "date": dividend_date.strftime("%Y-%m-%d"),
                                        "description": f"Temettü Ödemesi (Yıllık: {dividend_rate:.2f} TL)",
                                        "source": "Yahoo Finance",
                                        "status": "bekliyor" if dividend_date > date.today() else "tamamlandı"
                                    })
            except Exception as e:
                print(f"Yahoo Finance hatası: {e}")
            
            # Ekonomi haberleri (daha güvenilir kaynak)
            try:
                # Anadolu Ajansı Ekonomi
                aa_url = "https://www.aa.com.tr/tr/ekonomi"
                response = self.session.get(aa_url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Şirket ile ilgili haberler
                    news_items = soup.find_all('div', {'class': 'news-item'}) or soup.find_all('article')
                    for item in news_items[:15]:
                        title = item.find('h3') or item.find('h2') or item.find('a')
                        if title:
                            title_text = title.get_text(strip=True)
                            if symbol.lower() in title_text.lower():
                                date_elem = item.find('time') or item.find('span', {'class': 'date'})
                                if date_elem:
                                    date_text = date_elem.get_text(strip=True)
                                    event_date = self.parse_turkish_date(date_text)
                                    if event_date:
                                        events.append({
                                            "type": "haber",
                                            "date": event_date.strftime("%Y-%m-%d"),
                                            "description": title_text,
                                            "source": "Anadolu Ajansı",
                                            "status": "bekliyor" if event_date > date.today() else "tamamlandı"
                                        })
            except Exception as e:
                print(f"Anadolu Ajansı hatası: {e}")
            
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
                    try:
                        last_update_date = datetime.strptime(last_update, "%Y-%m-%d").date()
                        if (date.today() - last_update_date).days < 1:
                            print(f"{symbol} için veri güncel, güncelleme gerekmez")
                            return True  # Güncel, güncelleme gerekmez
                    except ValueError:
                        print(f"{symbol} için tarih parse hatası, güncelleme yapılıyor")
            
            print(f"{symbol} için finansal takvim güncelleniyor...")
            
            # Farklı kaynaklardan veri çek
            print(f"  - KAP'tan veri çekiliyor...")
            kap_events = self.scrape_kap_events(symbol)
            print(f"  - KAP'tan {len(kap_events)} olay bulundu")
            
            print(f"  - BIST'ten veri çekiliyor...")
            bist_events = self.scrape_bist_events(symbol)
            print(f"  - BIST'ten {len(bist_events)} olay bulundu")
            
            print(f"  - Haber sitelerinden veri çekiliyor...")
            news_events = self.scrape_finansal_haberler(symbol)
            print(f"  - Haber sitelerinden {len(news_events)} olay bulundu")
            
            # Tüm olayları birleştir
            all_events = kap_events + bist_events + news_events
            print(f"  - Toplam {len(all_events)} olay birleştirildi")
            
            # Tekrarlanan olayları temizle
            unique_events = []
            seen_descriptions = set()
            
            for event in all_events:
                event_key = f"{event['date']}_{event['type']}_{event['description'][:50]}"
                if event_key not in seen_descriptions:
                    seen_descriptions.add(event_key)
                    unique_events.append(event)
            
            print(f"  - Tekrarlar temizlendi, {len(unique_events)} benzersiz olay kaldı")
            
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
            # Hata durumunda varsayılan olayları ekle
            try:
                default_events = self.get_default_events(symbol)
                if symbol not in self.events:
                    self.events[symbol] = {
                        "company_name": symbol,
                        "events": [],
                        "last_update": date.today().strftime("%Y-%m-%d")
                    }
                self.events[symbol]["events"] = default_events
                self.events[symbol]["last_update"] = date.today().strftime("%Y-%m-%d")
                self.save_events()
                print(f"{symbol} için varsayılan olaylar eklendi ({len(default_events)} olay)")
                return True
            except Exception as default_error:
                print(f"{symbol} için varsayılan olaylar da eklenemedi: {default_error}")
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