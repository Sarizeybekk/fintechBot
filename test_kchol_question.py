#!/usr/bin/env python3
"""
Test script for the specific question: "Bugün KCHOL niye düştü?"
"""

import json
from web_search_agent import WebSearchAgent

def test_kchol_why_fell_question():
    """Test the specific question about why KCHOL fell today"""
    
    print("🧪 KCHOL 'Niye Düştü?' Sorusu Testi Başlatılıyor...")
    
    try:
        # Web Search Agent'ı başlat
        agent = WebSearchAgent()
        print("✅ Web Search Agent başarıyla başlatıldı")
        
        # Test sorusu
        test_question = "Bugün KCHOL niye düştü?"
        
        # Mock model prediction (gerçek uygulamada bu teknik analizden gelir)
        mock_prediction = {
            'current_price': 150.0,
            'predicted_price': 145.0,
            'change': -5.0,
            'change_percent': -3.33
        }
        
        print(f"📝 Test sorusu: {test_question}")
        print(f"📊 Mock model tahmini: {mock_prediction}")
        
        # Web arama ve analiz yap
        print("\n🔍 Web arama ve analiz başlatılıyor...")
        result = agent.analyze_price_prediction_with_news(test_question, mock_prediction)
        
        if result.get('success'):
            print("✅ Analiz başarılı!")
            print(f"📊 Web sonuç sayısı: {result.get('web_results_count', 0)}")
            print(f"🔍 Çelişki var mı: {result.get('has_conflict', False)}")
            
            # Analizi göster
            analysis = result.get('analysis', '')
            print(f"\n📝 ANALİZ SONUCU:\n{analysis}")
            
            # Kaynak URL'leri göster
            source_urls = result.get('source_urls', [])
            if source_urls:
                print(f"\n🔗 KAYNAK URL'LERİ:")
                for i, url_info in enumerate(source_urls[:5], 1):
                    print(f"{i}. {url_info}")
            
            # Web sonuçlarını göster
            web_results = result.get('web_results', [])
            if web_results:
                print(f"\n📰 WEB SONUÇLARI:")
                for i, result_item in enumerate(web_results[:3], 1):
                    title = result_item.get('title', 'N/A')
                    url = result_item.get('url', 'N/A')
                    print(f"{i}. {title}")
                    print(f"   URL: {url}")
                    print()
            
        else:
            print(f"❌ Analiz başarısız: {result.get('message', 'Bilinmeyen hata')}")
            
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_kchol_why_fell_question() 