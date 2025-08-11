#!/usr/bin/env python3
"""
Test script for Web Search Agent functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from web_search_agent import WebSearchAgent
import json

def test_web_search_agent():
    """Test the web search agent functionality"""
    print("🧪 Web Search Agent Test Başlatılıyor...")
    
    try:
        # Web Search Agent'ı başlat
        agent = WebSearchAgent()
        print("✅ Web Search Agent başarıyla başlatıldı")
        
        # Test 1: Güncel haberleri al
        print("\n📰 Test 1: Güncel haberleri al")
        current_news = agent.get_current_news('KCHOL', max_results=5)
        
        if current_news.get('success'):
            print(f"✅ Güncel haberler alındı: {current_news.get('results_count', 0)} haber")
            for i, news in enumerate(current_news.get('results', [])[:3], 1):
                print(f"  {i}. {news.get('title', 'Başlık yok')}")
        else:
            print(f"❌ Güncel haberler alınamadı: {current_news.get('message', 'Bilinmeyen hata')}")
        
        # Test 2: Fiyat tahmini analizi
        print("\n📈 Test 2: Fiyat tahmini analizi")
        mock_prediction = {
            'current_price': 150.0,
            'predicted_price': 155.0,
            'change': 5.0,
            'change_percent': 3.33,
            'prediction_date': '2024-01-15'
        }
        
        analysis_result = agent.analyze_price_prediction_with_news(
            "KCHOL fiyat tahmini yap", 
            mock_prediction, 
            "KCHOL hisse senedi güncel haberler"
        )
        
        if analysis_result.get('success'):
            print("✅ Fiyat tahmini analizi başarılı")
            print(f"📊 Web sonuç sayısı: {analysis_result.get('web_results_count', 0)}")
            print(f"🔍 Çelişki var mı: {analysis_result.get('has_conflict', False)}")
            
            # Analiz özetini göster
            analysis = analysis_result.get('analysis', '')
            if analysis:
                print(f"📝 Analiz özeti: {analysis[:200]}...")
        else:
            print(f"❌ Fiyat tahmini analizi başarısız: {analysis_result.get('message', 'Bilinmeyen hata')}")
        
        # Test 3: Web araması
        print("\n🔍 Test 3: Web araması")
        search_results = agent.search_web("KCHOL hisse senedi güncel haberler", max_results=5, search_type='news')
        
        if search_results:
            print(f"✅ Web araması başarılı: {len(search_results)} sonuç")
            for i, result in enumerate(search_results[:3], 1):
                print(f"  {i}. {result.get('title', 'Başlık yok')}")
        else:
            print("❌ Web araması başarısız")
        
        print("\n🎉 Test tamamlandı!")
        
    except Exception as e:
        print(f"❌ Test hatası: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_search_agent() 