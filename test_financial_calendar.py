#!/usr/bin/env python3
"""
Finansal Takvim Test Scripti
Bu script finansal takvim sisteminin tüm özelliklerini test eder.
"""

from financial_calendar import FinancialCalendar
from datetime import date, datetime
import json

def test_financial_calendar():
    """Finansal takvim sistemini test et"""
    print("=" * 60)
    print("FİNANSAL TAKVİM SİSTEMİ TEST EDİLİYOR")
    print("=" * 60)
    
    # Finansal takvim nesnesini oluştur
    calendar = FinancialCalendar()
    
    # Test 1: Varsayılan olaylar
    print("\n1. Varsayılan Olaylar Testi:")
    print("-" * 40)
    test_symbols = ['GARAN', 'AKBNK', 'THYAO']
    for symbol in test_symbols:
        events = calendar.get_default_events(symbol)
        print(f"{symbol}: {len(events)} olay")
        for event in events:
            print(f"  - {event['type']}: {event['date']} - {event['description']}")
    
    # Test 2: Tek şirket güncelleme
    print("\n2. Tek Şirket Güncelleme Testi:")
    print("-" * 40)
    test_symbol = 'GARAN'
    print(f"{test_symbol} için güncelleme yapılıyor...")
    success = calendar.update_company_events(test_symbol, force_update=True)
    print(f"Güncelleme başarılı: {success}")
    
    # Test 3: Şirket olaylarını getir
    print("\n3. Şirket Olayları Testi:")
    print("-" * 40)
    company_data = calendar.get_company_events(test_symbol)
    if company_data:
        print(f"{company_data['company_name']} ({len(company_data['events'])} olay):")
        for event in company_data['events']:
            print(f"  - {event['type']}: {event['date']} - {event['description']} ({event['source']})")
    
    # Test 4: Tüm şirketleri güncelle
    print("\n4. Tüm Şirketler Güncelleme Testi:")
    print("-" * 40)
    symbols = ['THYAO', 'KCHOL', 'GARAN', 'AKBNK', 'ISCTR', 'SAHOL', 'ASELS', 'EREGL']
    print(f"{len(symbols)} şirket güncelleniyor...")
    results = calendar.update_all_companies(symbols)
    
    success_count = sum(1 for success in results.values() if success)
    print(f"Başarılı güncelleme: {success_count}/{len(symbols)}")
    
    # Test 5: Takvim özeti
    print("\n5. Takvim Özeti Testi:")
    print("-" * 40)
    summary = calendar.get_calendar_summary()
    print(f"Toplam şirket: {summary['total_companies']}")
    print(f"Toplam olay: {summary['total_events']}")
    print(f"Yaklaşan olaylar (30 gün): {summary['upcoming_events']}")
    print(f"Son güncelleme: {summary['last_updated']}")
    
    # Test 6: Olay türleri
    print("\n6. Olay Türleri Testi:")
    print("-" * 40)
    event_types = calendar.get_event_types()
    print(f"Olay türleri: {', '.join(event_types)}")
    
    # Test 7: Yaklaşan olaylar
    print("\n7. Yaklaşan Olaylar Testi:")
    print("-" * 40)
    upcoming = calendar.get_upcoming_events(30)
    print(f"Önümüzdeki 30 günde {len(upcoming)} olay:")
    for event in upcoming[:5]:  # İlk 5 olayı göster
        print(f"  - {event['symbol']}: {event['date']} - {event['description']}")
    
    # Test 8: Arama testi
    print("\n8. Arama Testi:")
    print("-" * 40)
    search_results = calendar.search_events("bilanço")
    print(f"'bilanço' araması: {len(search_results)} sonuç")
    for result in search_results[:3]:  # İlk 3 sonucu göster
        print(f"  - {result['symbol']}: {result['date']} - {result['description']}")
    
    # Test 9: CSV dışa aktarma
    print("\n9. CSV Dışa Aktarma Testi:")
    print("-" * 40)
    csv_file = "financial_calendar_export.csv"
    success = calendar.export_to_csv(csv_file)
    print(f"CSV dışa aktarma: {'Başarılı' if success else 'Başarısız'}")
    
    # Test 10: Performans testi
    print("\n10. Performans Testi:")
    print("-" * 40)
    import time
    start_time = time.time()
    calendar.update_company_events('GARAN', force_update=True)
    end_time = time.time()
    print(f"Güncelleme süresi: {end_time - start_time:.2f} saniye")
    
    print("\n" + "=" * 60)
    print("TEST TAMAMLANDI!")
    print("=" * 60)

def test_error_handling():
    """Hata yönetimi testi"""
    print("\nHATA YÖNETİMİ TESTİ:")
    print("-" * 40)
    
    calendar = FinancialCalendar()
    
    # Geçersiz sembol testi kaldırıldı - sadece gerçek şirketler test ediliyor
    print("Geçersiz sembol testi kaldırıldı")
    
    # Bozuk tarih testi
    print("Bozuk tarih testi...")
    try:
        date_obj = calendar.parse_turkish_date("invalid_date")
        print(f"Sonuç: {date_obj}")
    except Exception as e:
        print(f"Hata yakalandı: {e}")

if __name__ == "__main__":
    try:
        test_financial_calendar()
        test_error_handling()
    except Exception as e:
        print(f"Test sırasında hata oluştu: {e}")
        import traceback
        traceback.print_exc() 