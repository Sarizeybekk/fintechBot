from flask import Flask, render_template, request, jsonify, send_file
import pickle
import yfinance as yf
import pandas as pd
import numpy as np
from finta import TA
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from document_rag_agent import DocumentRAGAgent
from technical_analysis import TechnicalAnalysisEngine
import uuid
import requests
from textblob import TextBlob
import re
from bs4 import BeautifulSoup
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Global sohbet geçmişi tutma
chat_sessions = {}  # session_id -> chat_history
current_session_id = None

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'))
    print(f"✅ Gemini API anahtarı yüklendi: {GEMINI_API_KEY[:10]}...")
else:
    print("⚠️  Gemini API anahtarı bulunamadı. .env dosyasında GOOGLE_API_KEY veya GEMINI_API_KEY tanımlayın.")
    gemini_model = None

# News API Configuration
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '67b1d8b38f8b4ba8ba13fada3b9deac1')  # API key
NEWS_API_URL = "https://newsapi.org/v2/everything"

# Initialize Document RAG Agent
try:
    document_rag_agent = DocumentRAGAgent()
    print("Document RAG Agent basariyla yuklendi")
except Exception as e:
    print(f"Document RAG Agent yuklenemedi: {e}")
    document_rag_agent = None

# Initialize Technical Analysis Engine
try:
    technical_analysis_engine = TechnicalAnalysisEngine()
    print("Technical Analysis Engine basariyla yuklendi")
except Exception as e:
    print(f"Technical Analysis Engine yuklenemedi: {e}")
    technical_analysis_engine = None

# Initialize Financial Q&A Agent
try:
    from financial_qa_agent import FinancialQAAgent
    financial_qa_agent = FinancialQAAgent()
    print("Financial Q&A Agent basariyla yuklendi")
except Exception as e:
    print(f"Financial Q&A Agent yuklenemedi: {e}")
    financial_qa_agent = None

# Initialize Investment Advisor
try:
    from investment_advisor import InvestmentAdvisor
    investment_advisor = InvestmentAdvisor()
    print("✅ Investment Advisor başarıyla yüklendi")
except Exception as e:
    print(f"❌ Investment Advisor yüklenemedi: {e}")
    investment_advisor = None

# Hisse simülasyon modülünü import et
try:
    from hisse_simulasyon import hisse_simulasyon
    print("✅ Hisse Simülasyon modülü başarıyla yüklendi")
except Exception as e:
    print(f"❌ Hisse Simülasyon modülü yüklenemedi: {e}")
    hisse_simulasyon = None

# Initialize Portfolio Manager
try:
    from portfolio_manager import PortfolioManager
    portfolio_manager = PortfolioManager()
    print("✅ Portfolio Manager başarıyla yüklendi")
except Exception as e:
    print(f"❌ Portfolio Manager yüklenemedi: {e}")
    portfolio_manager = None

# Initialize Financial Calendar
try:
    from financial_calendar import FinancialCalendar
    financial_calendar = FinancialCalendar()
    print("✅ Financial Calendar başarıyla yüklendi")
except Exception as e:
    print(f"❌ Financial Calendar yüklenemedi: {e}")
    financial_calendar = None

# Initialize Financial Alert System
try:
    from financial_alerts import FinancialAlertSystem
    financial_alert_system = FinancialAlertSystem()
    print("✅ Financial Alert System başarıyla yüklendi")
except Exception as e:
    print(f"❌ Financial Alert System yüklenemedi: {e}")
    financial_alert_system = None

# Sohbet geçmişi yönetimi
def create_new_session():
    """Yeni sohbet oturumu oluştur"""
    global current_session_id
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = {
        'id': session_id,
        'title': f'KCHOL Sohbet - {datetime.now().strftime("%d.%m.%Y %H:%M")}',
        'created_at': datetime.now().isoformat(),
        'messages': []
    }
    current_session_id = session_id
    return session_id

def get_current_session():
    """Mevcut oturumu al veya yeni oluştur"""
    global current_session_id
    if current_session_id is None or current_session_id not in chat_sessions:
        create_new_session()
    return chat_sessions[current_session_id]

def add_message_to_session(session_id, sender, message, message_type='text', data=None):
    """Oturuma mesaj ekle"""
    if session_id not in chat_sessions:
        return False
    
    chat_sessions[session_id]['messages'].append({
        'id': str(uuid.uuid4()),
        'sender': sender,  # 'user' veya 'bot'
        'message': message,
        'type': message_type,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })
    return True

def export_chat_history(session_id, format='txt'):
    """Sohbet geçmişini dışa aktar"""
    if session_id not in chat_sessions:
        return None
    
    session = chat_sessions[session_id]
    
    if format == 'txt':
        content = f"KCHOL Hisse Senedi Asistanı - Sohbet Geçmişi\n"
        content += f"Tarih: {session['created_at']}\n"
        content += f"Oturum ID: {session['id']}\n"
        content += f"Toplam Mesaj: {len(session['messages'])}\n"
        content += "=" * 50 + "\n\n"
        
        for msg in session['messages']:
            timestamp = datetime.fromisoformat(msg['timestamp']).strftime("%d.%m.%Y %H:%M:%S")
            sender_name = "Siz" if msg['sender'] == 'user' else "KCHOL Asistan"
            message_type = msg.get('type', 'text')
            
            content += f"[{timestamp}] {sender_name} ({message_type}):\n"
            content += f"{msg['message']}\n\n"
            
            # Eğer mesajda data varsa ekle
            if msg.get('data'):
                content += f"Ek Veri: {json.dumps(msg['data'], indent=2, ensure_ascii=False)}\n\n"
        
        return content
    
    elif format == 'json':
        return json.dumps(session, indent=2, ensure_ascii=False)
    
    elif format == 'html':
        html_content = f"""
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KCHOL Sohbet Geçmişi - {session['id']}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #06b6d4; padding-bottom: 20px; margin-bottom: 30px; }}
        .header h1 {{ color: #06b6d4; margin: 0; }}
        .header p {{ color: #666; margin: 5px 0; }}
        .message {{ margin-bottom: 20px; padding: 15px; border-radius: 8px; }}
        .user-message {{ background: #e3f2fd; border-left: 4px solid #2196f3; }}
        .bot-message {{ background: #f3e5f5; border-left: 4px solid #9c27b0; }}
        .message-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
        .sender {{ font-weight: bold; color: #333; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
        .message-content {{ line-height: 1.6; }}
        .prediction-result {{ background: #fff3e0; padding: 15px; border-radius: 5px; margin-top: 10px; }}
        .prediction-item {{ display: flex; justify-content: space-between; margin: 5px 0; }}
        .positive {{ color: #4caf50; }}
        .negative {{ color: #f44336; }}
        .stats {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>KCHOL Hisse Senedi Asistanı</h1>
            <p>Sohbet Geçmişi</p>
            <p>Oluşturulma: {session['created_at']}</p>
            <p>Oturum ID: {session['id']}</p>
            <p>Toplam Mesaj: {len(session['messages'])}</p>
        </div>
"""
        
        for msg in session['messages']:
            timestamp = datetime.fromisoformat(msg['timestamp']).strftime("%d.%m.%Y %H:%M:%S")
            sender_name = "Siz" if msg['sender'] == 'user' else "KCHOL Asistan"
            message_class = "user-message" if msg['sender'] == 'user' else "bot-message"
            message_type = msg.get('type', 'text')
            
            html_content += f"""
        <div class="message {message_class}">
            <div class="message-header">
                <span class="sender">{sender_name}</span>
                <span class="timestamp">{timestamp}</span>
            </div>
            <div class="message-content">
                {msg['message'].replace(chr(10), '<br>')}
            </div>
"""
            
            # Eğer tahmin verisi varsa özel formatla
            if msg.get('data') and msg.get('type') == 'prediction':
                data = msg['data']
                html_content += f"""
            <div class="prediction-result">
                <div class="prediction-item">
                    <span>Mevcut Fiyat:</span>
                    <span>{data.get('current_price', 'N/A')} TL</span>
                </div>
                <div class="prediction-item">
                    <span>Tahmin Edilen:</span>
                    <span>{data.get('predicted_price', 'N/A')} TL</span>
                </div>
                <div class="prediction-item">
                    <span>Değişim:</span>
                    <span class="{'positive' if data.get('change', 0) >= 0 else 'negative'}">
                        {data.get('change', 0):+.2f} TL ({data.get('change_percent', 0):+.2f}%)
                    </span>
                </div>
                <div class="prediction-item">
                    <span>Tahmin Tarihi:</span>
                    <span>{data.get('prediction_date', 'N/A')}</span>
                </div>
            </div>
"""
            
            html_content += """
        </div>
"""
        
        html_content += """
    </div>
</body>
</html>
"""
        return html_content
    
    return None

# Model yükleme
def load_model():
    try:
        with open('model/kchol_xgb_model.pkl', 'rb') as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        print(f"Model yüklenirken hata: {e}")
        return None

# Gemini AI ile genel soruları yanıtlama
def get_gemini_response(user_message, context=""):
    try:
        # Fiyat tahmini için özel prompt
        if any(word in user_message.lower() for word in ['tahmin', 'fiyat', 'ne olacak', 'yükselir mi', 'düşer mi']):
            system_prompt = f"""
Sen profesyonel bir finans analisti olarak KCHOL hisse senedi fiyat tahmini yapıyorsun.

Aşağıdaki verileri kullanarak net, anlaşılır ve profesyonel bir fiyat tahmini yanıtı ver:

{context}

Yanıt kuralları:
1. Sadece Türkçe yanıt ver
2. Emoji kullanma
3. Düzyazı şeklinde yaz
4. ChatGPT tarzında net ve kısa cevaplar ver
5. Teknik jargon kullanma, anlaşılır dil kullan
6. Yatırım tavsiyesi verme, sadece analiz sun
7. Risk uyarısı ekle
8. Maksimum 3-4 paragraf yaz
9. Hata mesajı verme, sadece analiz yap

Kullanıcı sorusu: {user_message}
"""
        else:
            # Genel sorular için
            system_prompt = f"""
Sen Türkçe konuşan bir finans ve yatırım asistanısın. KCHOL hisse senedi ve genel finans konularında uzman bilgi veriyorsun.

Kullanıcı sorusu: {user_message}

Lütfen aşağıdaki kurallara uygun olarak yanıt ver:
1. Sadece Türkçe yanıt ver
2. Emoji kullanma
3. Düzyazı şeklinde yaz
4. Finansal tavsiye verme, sadece bilgilendirici ol
5. KCHOL hisse senedi hakkında sorulara özel önem ver
6. Kısa ve öz yanıtlar ver
7. Profesyonel ve anlaşılır dil kullan
8. Hata mesajı verme, sadece bilgi ver

{context}
"""
        
        response = gemini_model.generate_content(system_prompt)
        response_text = response.text.strip()
        
        # Eğer Gemini hata mesajı veriyorsa None döndür
        if "Üzgünüm" in response_text or "şu anda yanıt veremiyorum" in response_text or "error" in response_text.lower():
            return None
            
        return response_text
    except Exception as e:
        print(f"Gemini API hatası: {e}")
        return None

# Hisse verisi alma ve özellik çıkarma
def get_stock_data(symbol='KCHOL.IS', days=300):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        print(f"Veri alınıyor: {symbol} - {start_date} to {end_date}")
        df = yf.download(symbol, start_date, end_date, progress=False)
        
        print(f"Alınan veri boyutu: {df.shape}")
        
        if df.empty:
            print("Veri boş!")
            return None
            
        print(f"Orijinal sütunlar: {df.columns.tolist()}")
        
        # Sütun isimlerini düzenleme
        df.columns = ['_'.join(col).lower() for col in df.columns]
        df.columns = [col.split('_')[0] for col in df.columns]
        
        print(f"Düzenlenmiş sütunlar: {df.columns.tolist()}")
        
        # Teknik indikatörler
        df['SMA200'] = TA.SMA(df, 200)
        df['RSI'] = TA.RSI(df)
        df['ATR'] = TA.ATR(df)
        df['BBWidth'] = TA.BBWIDTH(df)
        df['Williams'] = TA.WILLIAMS(df)
        
        print(f"Teknik indikatörler eklendi. Veri boyutu: {df.shape}")
        
        # NaN değerleri temizleme
        df = df.dropna()
        
        print(f"NaN temizlendikten sonra veri boyutu: {df.shape}")
        
        if len(df) < 1:
            print("Yeterli veri yok!")
            return None
            
        return df
    except Exception as e:
        print(f"Veri alma hatası: {e}")
        return None

# Tahmin fonksiyonu
def create_model_explanation(X, features, predicted_price, current_price):
    """Model tahminini açıklayan basit analiz (SHAP olmadan)"""
    try:
        # Özellik değerlerini al
        feature_values = X[0] if len(X.shape) > 1 else X
        
        # Özellik katkılarını hesapla (basit yaklaşım)
        explanations = []
        
        # Fiyat verileri analizi
        close_price = feature_values[features.index('close')]
        high_price = feature_values[features.index('high')]
        low_price = feature_values[features.index('low')]
        open_price = feature_values[features.index('open')]
        volume = feature_values[features.index('volume')]
        
        # Teknik göstergeler
        sma200 = feature_values[features.index('SMA200')]
        rsi = feature_values[features.index('RSI')]
        atr = feature_values[features.index('ATR')]
        bbwidth = feature_values[features.index('BBWidth')]
        williams = feature_values[features.index('Williams')]
        
        # Fiyat pozisyonu analizi
        if close_price > sma200:
            explanations.append(f"Kapanış fiyatı ({close_price:.2f} TL) 200 günlük ortalamanın ({sma200:.2f} TL) üzerinde - Yükseliş trendi")
        else:
            explanations.append(f"Kapanış fiyatı ({close_price:.2f} TL) 200 günlük ortalamanın ({sma200:.2f} TL) altında - Düşüş trendi")
        
        # RSI analizi
        if rsi > 70:
            explanations.append(f"RSI ({rsi:.1f}) aşırı alım bölgesinde - Düşüş riski")
        elif rsi < 30:
            explanations.append(f"RSI ({rsi:.1f}) aşırı satım bölgesinde - Yükseliş fırsatı")
        else:
            explanations.append(f"RSI ({rsi:.1f}) nötr bölgede - Trend devam edebilir")
        
        # Volatilite analizi
        if atr > 5:
            explanations.append(f"Yüksek volatilite (ATR: {atr:.2f}) - Fiyat hareketleri büyük olabilir")
        else:
            explanations.append(f"Düşük volatilite (ATR: {atr:.2f}) - Fiyat hareketleri sınırlı olabilir")
        
        # Bollinger Bant analizi
        if bbwidth > 0.2:
            explanations.append(f"Geniş Bollinger Bantları ({bbwidth:.3f}) - Volatilite artıyor")
        else:
            explanations.append(f"Dar Bollinger Bantları ({bbwidth:.3f}) - Volatilite azalıyor")
        
        # Williams %R analizi
        if williams < -80:
            explanations.append(f"Williams %R ({williams:.1f}) aşırı satım - Yükseliş sinyali")
        elif williams > -20:
            explanations.append(f"Williams %R ({williams:.1f}) aşırı alım - Düşüş sinyali")
        else:
            explanations.append(f"Williams %R ({williams:.1f}) nötr bölge")
        
        # Hacim analizi
        avg_volume = volume / 1000000  # Milyon cinsinden
        if avg_volume > 10:
            explanations.append(f"Yüksek işlem hacmi ({avg_volume:.1f}M) - Güçlü trend")
        else:
            explanations.append(f"Düşük işlem hacmi ({avg_volume:.1f}M) - Zayıf trend")
        
        # Tahmin yönü analizi
        if predicted_price > current_price:
            trend_direction = "YÜKSELİŞ"
            confidence = "Yüksek" if abs(predicted_price - current_price) > 5 else "Orta"
        else:
            trend_direction = "DÜŞÜŞ"
            confidence = "Yüksek" if abs(predicted_price - current_price) > 5 else "Orta"
        
        return {
            'trend_direction': trend_direction,
            'confidence': confidence,
            'explanations': explanations,
            'key_factors': {
                'price_vs_sma200': "Yukarı" if close_price > sma200 else "Aşağı",
                'rsi_signal': "Aşırı alım" if rsi > 70 else "Aşırı satım" if rsi < 30 else "Nötr",
                'volatility': "Yüksek" if atr > 5 else "Düşük",
                'volume_strength': "Güçlü" if avg_volume > 10 else "Zayıf"
            }
        }
        
    except Exception as e:
        print(f"Model açıklama hatası: {e}")
        return {
            'trend_direction': "Belirsiz",
            'confidence': "Düşük",
            'explanations': ["Model açıklaması oluşturulamadı"],
            'key_factors': {}
        }

def predict_price(model, df):
    try:
        print(f"Tahmin fonksiyonu başladı. Veri boyutu: {len(df) if df is not None else 'None'}")
        
        if df is None:
            return None, "Veri bulunamadı"
            
        if len(df) < 1:
            return None, f"Yeterli veri bulunamadı. Mevcut veri: {len(df)} satır"
        
        # Son veriyi al
        latest_data = df.iloc[-1:].copy()
        print(f"Son veri sütunları: {latest_data.columns.tolist()}")
        
        # Gerekli özellikler
        features = ['close', 'high', 'low', 'open', 'volume', 'SMA200', 'RSI', 'ATR', 'BBWidth', 'Williams']
        
        # Eksik özellikleri kontrol et
        missing_features = [f for f in features if f not in latest_data.columns]
        if missing_features:
            print(f"Eksik özellikler: {missing_features}")
            return None, f"Eksik özellikler: {missing_features}"
        
        # Tahmin için veriyi hazırla
        X = latest_data[features].values
        print(f"Tahmin verisi şekli: {X.shape}")
        print(f"Tahmin verisi: {X}")
        
        # Tahmin yap
        prediction = model.predict(X)[0]
        print(f"Tahmin sonucu: {prediction}")
        
        current_price = latest_data['close'].iloc[0]
        change = prediction - current_price
        change_percent = (change / current_price) * 100
        
        # Tahmin tarihini hesapla (hafta sonu kontrolü ile)
        tomorrow = datetime.now() + timedelta(days=1)
        if tomorrow.weekday() >= 5:  # Cumartesi veya Pazar
            # Sonraki iş gününe kadar ilerle
            while tomorrow.weekday() >= 5:
                tomorrow = tomorrow + timedelta(days=1)
        
        # Model açıklaması oluştur (SHAP olmadan)
        model_explanation = create_model_explanation(X, features, prediction, current_price)
        
        result = {
            'current_price': float(round(current_price, 2)),
            'predicted_price': float(round(prediction, 2)),
            'change': float(round(change, 2)),
            'change_percent': float(round(change_percent, 2)),
            'prediction_date': tomorrow.strftime('%Y-%m-%d'),
            'model_explanation': model_explanation
        }
        
        print(f"Tahmin sonucu: {result}")
        return result, None
        
    except Exception as e:
        print(f"Tahmin hatası: {e}")
        import traceback
        traceback.print_exc()
        return None, f"Tahmin hatası: {e}"

# Haber analizi fonksiyonları
def get_news_articles(query="KCHOL Koç Holding", days=7):
    """Haber API'sinden makaleleri al"""
    try:
        # Son 7 günün haberlerini al
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Koç Holding ile ilgili şirketlerin haberlerini ara
        search_queries = [
            "KCHOL",
            "Koç Holding",
            "Arçelik",
            "Tofaş",
            "Ford Otosan",
            "Yapı Kredi"
        ]
        
        all_articles = []
        
        for search_query in search_queries:
            params = {
                'q': search_query,
                'sortBy': 'publishedAt',
                'apiKey': NEWS_API_KEY,
                'pageSize': 10
            }
            
            print(f"Geniş arama yapılıyor: {search_query}")
            
            response = requests.get(NEWS_API_URL, params=params)
            
            print(f"Arama sorgusu: {search_query}")
            print(f"API URL: {response.url}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                print(f"Bulunan haber sayısı: {len(articles)}")
                
                # Her makaleye kaynak şirket bilgisi ekle
                for article in articles:
                    article['source_company'] = search_query
                all_articles.extend(articles)
            else:
                print(f"News API hatası ({search_query}): {response.status_code}")
                print(f"Response: {response.text}")
        
        # Duplicate makaleleri temizle (URL'ye göre)
        unique_articles = []
        seen_urls = set()
        
        for article in all_articles:
            if article.get('url') not in seen_urls:
                seen_urls.add(article.get('url'))
                unique_articles.append(article)
        
        print(f"Toplam {len(unique_articles)} benzersiz haber bulundu")
        return unique_articles
            
    except Exception as e:
        print(f"Haber alma hatası: {e}")
        return []

def analyze_sentiment(text):
    """Metin sentiment analizi"""
    try:
        # TextBlob ile sentiment analizi
        blob = TextBlob(text)
        sentiment_score = blob.sentiment.polarity
        
        # Sentiment kategorileri
        if sentiment_score > 0.1:
            return 'positive', sentiment_score
        elif sentiment_score < -0.1:
            return 'negative', sentiment_score
        else:
            return 'neutral', sentiment_score
            
    except Exception as e:
        print(f"Sentiment analizi hatası: {e}")
        return 'neutral', 0.0

def analyze_news_sentiment(articles):
    """Haber makalelerinin sentiment analizi"""
    if not articles:
        return {
            'total_articles': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'overall_sentiment': 'neutral',
            'sentiment_score': 0.0,
            'key_articles': []
        }
    
    sentiment_results = []
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    total_sentiment = 0.0
    company_breakdown = {}
    
    for article in articles[:20]:  # İlk 20 makaleyi analiz et
        title = article.get('title', '')
        description = article.get('description', '')
        content = article.get('content', '')
        source_company = article.get('source_company', 'Unknown')
        
        # Tüm metni birleştir
        full_text = f"{title} {description} {content}"
        
        # HTML tag'lerini temizle
        clean_text = re.sub(r'<[^>]+>', '', full_text)
        
        # Sentiment analizi
        sentiment, score = analyze_sentiment(clean_text)
        
        if sentiment == 'positive':
            positive_count += 1
        elif sentiment == 'negative':
            negative_count += 1
        else:
            neutral_count += 1
            
        total_sentiment += score
        
        # Şirket bazında analiz
        if source_company not in company_breakdown:
            company_breakdown[source_company] = {
                'count': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'total_score': 0.0
            }
        
        company_breakdown[source_company]['count'] += 1
        company_breakdown[source_company]['total_score'] += score
        
        if sentiment == 'positive':
            company_breakdown[source_company]['positive'] += 1
        elif sentiment == 'negative':
            company_breakdown[source_company]['negative'] += 1
        else:
            company_breakdown[source_company]['neutral'] += 1
        
        sentiment_results.append({
            'title': title,
            'sentiment': sentiment,
            'score': score,
            'url': article.get('url', ''),
            'published_at': article.get('publishedAt', ''),
            'source': article.get('source', {}).get('name', ''),
            'source_company': source_company
        })
    
    # Genel sentiment hesapla
    avg_sentiment = total_sentiment / len(articles) if articles else 0.0
    
    if avg_sentiment > 0.1:
        overall_sentiment = 'positive'
    elif avg_sentiment < -0.1:
        overall_sentiment = 'negative'
    else:
        overall_sentiment = 'neutral'
    
    # En önemli makaleleri seç (en yüksek sentiment skorları)
    key_articles = sorted(sentiment_results, key=lambda x: abs(x['score']), reverse=True)[:5]
    
    return {
        'total_articles': len(articles),
        'positive_count': positive_count,
        'negative_count': negative_count,
        'neutral_count': neutral_count,
        'overall_sentiment': overall_sentiment,
        'sentiment_score': avg_sentiment,
        'key_articles': key_articles,
        'company_breakdown': company_breakdown
    }

def get_news_based_prediction(sentiment_analysis, technical_prediction):
    """Haber sentiment analizine göre tahmin düzeltmesi"""
    sentiment_score = sentiment_analysis['sentiment_score']
    overall_sentiment = sentiment_analysis['overall_sentiment']
    
    # Sentiment skoruna göre düzeltme faktörü
    sentiment_adjustment = 0.0
    
    if overall_sentiment == 'positive':
        sentiment_adjustment = 0.02  # %2 yukarı düzeltme
    elif overall_sentiment == 'negative':
        sentiment_adjustment = -0.02  # %2 aşağı düzeltme
    
    # Teknik tahmin üzerine sentiment düzeltmesi uygula
    if technical_prediction:
        adjusted_price = technical_prediction['predicted_price'] * (1 + sentiment_adjustment)
        adjusted_change = adjusted_price - technical_prediction['current_price']
        adjusted_change_percent = (adjusted_change / technical_prediction['current_price']) * 100
        
        return {
            'original_prediction': technical_prediction,
            'adjusted_prediction': {
                'current_price': technical_prediction['current_price'],
                'predicted_price': round(adjusted_price, 2),
                'change': round(adjusted_change, 2),
                'change_percent': round(adjusted_change_percent, 2),
                'prediction_date': technical_prediction['prediction_date']
            },
            'sentiment_analysis': sentiment_analysis,
            'sentiment_adjustment': sentiment_adjustment
        }
    
    return None

def generate_news_insights(sentiment_analysis):
    """Haber analizine göre içgörüler oluştur"""
    if sentiment_analysis['total_articles'] == 0:
        return "Son günlerde Koç Holding ile ilgili haber bulunamadı."
    
    # Gemini ile daha iyi haber analizi yanıtı oluştur
    news_context = f"""
Haber analizi verileri:
- Toplam haber sayısı: {sentiment_analysis['total_articles']}
- Olumlu haber: {sentiment_analysis['positive_count']}
- Olumsuz haber: {sentiment_analysis['negative_count']}
- Nötr haber: {sentiment_analysis['neutral_count']}
- Genel sentiment: {sentiment_analysis['overall_sentiment']}
- Sentiment skoru: {sentiment_analysis['sentiment_score']:.3f}

Şirket bazında analiz:
"""
    
    if 'company_breakdown' in sentiment_analysis and sentiment_analysis['company_breakdown']:
        for company, data in sentiment_analysis['company_breakdown'].items():
            if data['count'] > 0:
                avg_score = data['total_score'] / data['count']
                sentiment_text = "Olumlu" if avg_score > 0.1 else "Olumsuz" if avg_score < -0.1 else "Nötr"
                news_context += f"- {company}: {data['count']} haber ({data['positive']} olumlu, {data['negative']} olumsuz) - {sentiment_text}\n"
    
    if sentiment_analysis['key_articles']:
        news_context += "\nÖnemli haberler:\n"
        for i, article in enumerate(sentiment_analysis['key_articles'][:3], 1):
            sentiment_text = "Olumlu" if article['sentiment'] == 'positive' else "Olumsuz" if article['sentiment'] == 'negative' else "Nötr"
            company_info = f" [{article.get('source_company', '')}]" if article.get('source_company') else ""
            news_context += f"- {article['title'][:60]}...{company_info} ({sentiment_text})\n"
    
    # Akıllı haber analizi yanıtı oluştur
    def create_smart_news_response():
        insights = []
        
        # Genel sentiment durumu
        if sentiment_analysis['overall_sentiment'] == 'positive':
            insights.append("Haberler genel olarak olumlu görünüyor. Bu durum hisse senedi fiyatına olumlu etki yapabilir.")
        elif sentiment_analysis['overall_sentiment'] == 'negative':
            insights.append("Haberler genel olarak olumsuz görünüyor. Bu durum hisse senedi fiyatına olumsuz etki yapabilir.")
        else:
            insights.append("Haberler nötr görünüyor. Bu durumda teknik analiz daha belirleyici olacaktır.")
        
        # Haber sayıları ve analiz
        insights.append(f"Toplam {sentiment_analysis['total_articles']} haber analiz edildi. Olumlu: {sentiment_analysis['positive_count']}, Olumsuz: {sentiment_analysis['negative_count']}, Nötr: {sentiment_analysis['neutral_count']}")
        
        # Şirket bazında analiz
        if 'company_breakdown' in sentiment_analysis and sentiment_analysis['company_breakdown']:
            insights.append("\nŞirket bazında analiz:")
            for company, data in sentiment_analysis['company_breakdown'].items():
                if data['count'] > 0:
                    avg_score = data['total_score'] / data['count']
                    sentiment_text = "Olumlu" if avg_score > 0.1 else "Olumsuz" if avg_score < -0.1 else "Nötr"
                    insights.append(f"• {company}: {data['count']} haber ({data['positive']} olumlu, {data['negative']} olumsuz) - {sentiment_text}")
        
        # Önemli haberler
        if sentiment_analysis['key_articles']:
            insights.append("\nÖnemli haberler:")
            for i, article in enumerate(sentiment_analysis['key_articles'][:3], 1):
                sentiment_text = "Olumlu" if article['sentiment'] == 'positive' else "Olumsuz" if article['sentiment'] == 'negative' else "Nötr"
                company_info = f" [{article.get('source_company', '')}]" if article.get('source_company') else ""
                insights.append(f"{i}. {article['title'][:60]}...{company_info} ({sentiment_text})")
        
        return "\n".join(insights)
    
    # Gemini ile yanıt oluşturmayı dene
    if gemini_model:
        try:
            gemini_prompt = f"""
Sen bir finans analisti olarak haber analizi yapıyorsun.

Aşağıdaki haber analizi verilerini kullanarak net ve anlaşılır bir özet çıkar:

{news_context}

Yanıt kuralları:
1. Sadece Türkçe yanıt ver
2. Emoji kullanma
3. Düzyazı şeklinde yaz
4. Kısa ve öz ol (maksimum 2-3 paragraf)
5. Teknik jargon kullanma
6. Haberlerin fiyat üzerindeki potansiyel etkisini açıkla
"""
            response = gemini_model.generate_content(gemini_prompt)
            response_text = response.text.strip()
            if response_text and "Üzgünüm" not in response_text and "şu anda yanıt veremiyorum" not in response_text:
                return response_text
            else:
                return create_smart_news_response()
        except Exception as e:
            print(f"Gemini haber analizi hatası: {e}")
            return create_smart_news_response()
    else:
        return create_smart_news_response()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '').lower()
        original_message = data.get('message', '')  # Orijinal mesajı koru
        
        # Session ID'yi request'ten al veya mevcut oturumu kullan
        requested_session_id = data.get('session_id')
        print(f"Requested session_id: {requested_session_id}")
        if requested_session_id:
            session_id = requested_session_id
            print(f"Using requested session_id: {session_id}")
        else:
            # Mevcut oturumu al
            current_session = get_current_session()
            session_id = current_session['id']
            print(f"Using current session_id: {session_id}")
        
        # Kullanıcı mesajını oturuma ekle
        add_message_to_session(session_id, 'user', original_message)
        
        # Model yükleme
        model = load_model()
        if model is None:
            error_response = 'Üzgünüm, model şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin.'
            add_message_to_session(session_id, 'bot', error_response, 'error')
            return jsonify({
                'response': error_response,
                'type': 'error',
                'session_id': session_id
            })
        
        # Kullanıcı mesajlarını analiz et
        # Önce eğitim sorularını kontrol et
        if any(word in message for word in ['nedir', 'ne demek', 'açıkla', 'anlat', 'eğitim', 'öğren', 'rehber']):
            # Finansal eğitim soruları
            if financial_qa_agent:
                try:
                    print(f"Finansal Eğitim Agent'a gönderilen soru: {original_message}")
                    qa_result = financial_qa_agent.process_financial_question(original_message)
                    
                    if qa_result.get('success') and qa_result.get('question_type') == 'financial_education':
                        response = qa_result.get('response', 'Yanıt oluşturulamadı.')
                        
                        add_message_to_session(session_id, 'bot', response, 'financial_education', qa_result)
                        return jsonify({
                            'response': response,
                            'type': 'financial_education',
                            'data': qa_result,
                            'session_id': session_id
                        })
                except Exception as e:
                    print(f"Finansal eğitim hatası: {e}")
        
        # Finansal takvim sorguları (alarm kurma olmadan)
        if (any(word in message for word in ['ne zaman', 'tarih', 'bilanço', 'genel kurul', 'temettü', 'takvim', 'olay']) and 
            any(word in message.lower() for word in ['thyao', 'kchol', 'garan', 'akbnk', 'asels', 'sasa', 'eregl', 'isctr', 'bimas', 'alark', 'tuprs', 'pgsus', 'krdmd', 'tavhl', 'doas', 'toaso', 'froto', 'vestl', 'yapi', 'qnbfb', 'halkb', 'vakbn', 'sise', 'kervn']) and
            not any(word in message.lower() for word in ['uyar', 'alarm', 'hatırlat', 'bildir'])):
            # Finansal takvim sorgusu
            if financial_calendar:
                try:
                    # Şirket sembolünü bul
                    symbols = ['thyao', 'kchol', 'garan', 'akbnk', 'asels', 'sasa', 'eregl', 'isctr', 'bimas', 'alark', 'tuprs', 'pgsus', 'krdmd', 'tavhl', 'doas', 'toaso', 'froto', 'vestl', 'yapi', 'qnbfb', 'halkb', 'vakbn', 'sise', 'kervn']
                    found_symbol = None
                    for symbol in symbols:
                        if symbol in message.lower():
                            found_symbol = symbol.upper()
                            break
                    
                    if found_symbol:
                        company_events = financial_calendar.get_company_events(found_symbol)
                        if company_events:
                            response = f"{company_events['company_name']} ({found_symbol}) Finansal Takvimi\n\n"
                            
                            # Olay türüne göre filtrele
                            event_types = ['bilanço', 'genel_kurul', 'temettü']
                            filtered_events = []
                            
                            for event in company_events['events']:
                                if any(event_type in message.lower() for event_type in event_types):
                                    filtered_events.append(event)
                            
                            if not filtered_events:
                                filtered_events = company_events['events']  # Tüm olayları göster
                            
                            for event in filtered_events:
                                status_text = "Tamamlandı" if event['status'] == 'tamamlandı' else "Bekliyor"
                                response += f"{event['type'].title()} - {event['date']} ({status_text})\n"
                                response += f"   {event['description']}\n"
                                response += f"   Kaynak: {event['source']}\n\n"
                            
                            # Alarm kurma önerisi ekle
                            if any(word in message.lower() for word in ['uyar', 'alarm', 'hatırlat', 'bildir']):
                                response += f"\n\nAlarm kurmak ister misiniz? '{found_symbol} bilançosu için 1 gün önce uyar' şeklinde yazabilirsiniz."
                            
                            add_message_to_session(session_id, 'bot', response, 'financial_calendar', {'company': found_symbol, 'events': company_events})
                            return jsonify({
                                'response': response,
                                'type': 'financial_calendar',
                                'data': {'company': found_symbol, 'events': company_events},
                                'session_id': session_id
                            })
                        else:
                            response = f"{found_symbol} için finansal takvim bilgisi bulunamadı."
                            add_message_to_session(session_id, 'bot', response, 'error')
                            return jsonify({
                                'response': response,
                                'type': 'error',
                                'session_id': session_id
                            })
                    else:
                        response = "Hangi şirket hakkında finansal takvim bilgisi istiyorsunuz? (THYAO, KCHOL, GARAN vb.)"
                        add_message_to_session(session_id, 'bot', response, 'text')
                        return jsonify({
                            'response': response,
                            'type': 'text',
                            'session_id': session_id
                        })
                except Exception as e:
                    print(f"Finansal takvim hatası: {e}")
                    response = "Finansal takvim bilgisi alınırken bir hata oluştu."
                    add_message_to_session(session_id, 'bot', response, 'error')
                    return jsonify({
                        'response': response,
                        'type': 'error',
                        'session_id': session_id
                    })
        
        # Finansal alarm kurma sorguları
        if any(word in message.lower() for word in ['uyar', 'alarm', 'hatırlat', 'bildir']) and any(word in message.lower() for word in ['thyao', 'kchol', 'garan', 'akbnk', 'asels', 'sasa', 'eregl', 'isctr', 'bimas', 'alark', 'tuprs', 'pgsus', 'krdmd', 'tavhl', 'doas', 'toaso', 'froto', 'vestl', 'yapi', 'qnbfb', 'halkb', 'vakbn', 'sise', 'kervn']):
            print(f"Alarm kurma sorgusu tespit edildi. Session ID: {session_id}")
            if financial_alert_system and financial_calendar:
                try:
                    # Şirket sembolünü bul
                    symbols = ['thyao', 'kchol', 'garan', 'akbnk', 'asels', 'sasa', 'eregl', 'isctr', 'bimas', 'alark', 'tuprs', 'pgsus', 'krdmd', 'tavhl', 'doas', 'toaso', 'froto', 'vestl', 'yapi', 'qnbfb', 'halkb', 'vakbn', 'sise', 'kervn']
                    found_symbol = None
                    for symbol in symbols:
                        if symbol in message.lower():
                            found_symbol = symbol.upper()
                            break
                    
                    if found_symbol:
                        # Kaç gün önce uyarılacağını belirle
                        days_before = 1  # Varsayılan
                        if '1 gün' in message or 'bir gün' in message:
                            days_before = 1
                        elif '2 gün' in message or 'iki gün' in message:
                            days_before = 2
                        elif '3 gün' in message or 'üç gün' in message:
                            days_before = 3
                        elif '1 hafta' in message or 'bir hafta' in message:
                            days_before = 7
                        
                        # Şirket olaylarını al
                        company_events = financial_calendar.get_company_events(found_symbol)
                        if company_events and company_events['events']:
                            # Bekleyen olaylar için alarm kur
                            pending_events = [e for e in company_events['events'] if e['status'] == 'bekliyor']
                            
                            if pending_events:
                                # Kullanıcı ID'si (şimdilik session ID kullanıyoruz)
                                user_id = f"user_{session_id}"
                                
                                # Alarm kur
                                alert_result = financial_alert_system.create_alert_from_calendar(
                                    user_id=user_id,
                                    symbol=found_symbol,
                                    calendar_events=pending_events,
                                    days_before=days_before
                                )
                                
                                if alert_result['success']:
                                    response = f"{found_symbol} için {alert_result['created_count']} alarm kuruldu.\n\n"
                                    response += f"Alarmlar {days_before} gün önce tetiklenecek.\n\n"
                                    
                                    for event in pending_events:
                                        response += f"{event['type'].title()} - {event['date']}\n"
                                        response += f"   {event['description']}\n\n"
                                    
                                    response += "Alarmlarınızı 'Alarmlarım' menüsünden takip edebilirsiniz."
                                    
                                    add_message_to_session(session_id, 'bot', response, 'financial_alert', alert_result)
                                    return jsonify({
                                        'response': response,
                                        'type': 'financial_alert',
                                        'data': alert_result,
                                        'session_id': session_id
                                    })
                                else:
                                    response = f"Alarm kurulurken hata oluştu: {alert_result.get('errors', [])}"
                                    add_message_to_session(session_id, 'bot', response, 'error')
                                    return jsonify({
                                        'response': response,
                                        'type': 'error',
                                        'session_id': session_id
                                    })
                            else:
                                response = f"{found_symbol} için bekleyen finansal olay bulunamadı."
                                add_message_to_session(session_id, 'bot', response, 'text')
                                return jsonify({
                                    'response': response,
                                    'type': 'text',
                                    'session_id': session_id
                                })
                        else:
                            response = f"{found_symbol} için finansal takvim bilgisi bulunamadı."
                            add_message_to_session(session_id, 'bot', response, 'error')
                            return jsonify({
                                'response': response,
                                'type': 'error',
                                'session_id': session_id
                            })
                    else:
                        response = "Hangi şirket için alarm kurmak istiyorsunuz? (THYAO, KCHOL, GARAN vb.)"
                        add_message_to_session(session_id, 'bot', response, 'text')
                        return jsonify({
                            'response': response,
                            'type': 'text',
                            'session_id': session_id
                        })
                except Exception as e:
                    print(f"Finansal alarm hatası: {e}")
                    response = "Alarm kurulurken bir hata oluştu."
                    add_message_to_session(session_id, 'bot', response, 'error')
                    return jsonify({
                        'response': response,
                        'type': 'error',
                        'session_id': session_id
                    })
        
        # Teknik analiz soruları - ÖNCELİKLİ - sadece belirli hisse için
        if any(word in message for word in ['grafik', 'göster', 'teknik analiz', 'teknik', 'indikatör', 'rsi', 'macd', 'bollinger', 'sma', 'hacim', 'fiyat']) and not any(word in message for word in ['nedir', 'ne demek', 'açıkla', 'anlat']):
            # Teknik analiz yap
            if technical_analysis_engine:
                try:
                    result = technical_analysis_engine.process_technical_analysis_request(original_message)
                    
                    if result.get('error'):
                        error_response = f'Teknik analiz hatası: {result["error"]}'
                        add_message_to_session(session_id, 'bot', error_response, 'error')
                        return jsonify({
                            'response': error_response,
                            'type': 'error',
                            'session_id': session_id
                        })
                    
                    # Teknik analiz sonucunu Gemini ile yorumla ve yatırım stratejisi ekle
                    def create_enhanced_technical_response():
                        # Grafikleri al
                        charts = result.get('charts', [])
                        charts_html = ""
                        
                        if charts:
                            charts_html = "\n\n📊 **TEKNİK ANALİZ GRAFİKLERİ**\n\n"
                            for i, chart in enumerate(charts, 1):
                                charts_html += f"**{i}. {chart.get('title', 'Grafik')}**\n"
                                charts_html += f"{chart.get('data', '')}\n\n"
                                charts_html += "---\n\n"
                        
                        # Teknik analiz verilerini hazırla
                        technical_data = result.get('analysis', '') + "\n\n" + result.get('summary', '')
                        
                        # Gemini ile yatırım stratejisi önerisi al
                        if gemini_model:
                            try:
                                strategy_prompt = f"""
Sen bir finansal analiz uzmanısın. Aşağıdaki teknik analiz sonuçlarını yorumlayarak KCHOL hisse senedi için yatırım stratejisi önerileri sun.

Teknik Analiz Sonuçları:
{technical_data}

Bu teknik analiz sonuçlarına göre:
1. Mevcut durumu değerlendir
2. Kısa vadeli (1-4 hafta) yatırım stratejisi öner
3. Orta vadeli (1-6 ay) yatırım stratejisi öner
4. Risk seviyesini belirt
5. Dikkat edilmesi gereken noktaları açıkla

Yanıt kuralları:
- Sadece Türkçe yanıt ver
- Emoji kullanma
- Düzyazı şeklinde yaz
- Pratik ve uygulanabilir öneriler ver
- Risk uyarısı ekle
- Maksimum 4-5 paragraf yaz
"""
                                strategy_response = gemini_model.generate_content(strategy_prompt)
                                strategy_text = strategy_response.text.strip()
                                
                                if strategy_text and "Üzgünüm" not in strategy_text:
                                    enhanced_response = f"""KCHOL Teknik Analiz Raporu

{result.get('analysis', '')}

{result.get('summary', '')}

---

YATIRIM STRATEJİSİ ÖNERİLERİ

{strategy_text}"""
                                else:
                                    enhanced_response = f"""KCHOL Teknik Analiz Raporu

{result.get('analysis', '')}

{result.get('summary', '')}

---

YATIRIM STRATEJİSİ ÖNERİLERİ

Teknik analiz sonuçlarına göre, KCHOL hisse senedi için aşağıdaki stratejileri öneriyorum:

Kısa Vadeli Strateji (1-4 hafta):
• Teknik indikatörlerin gösterdiği yöne göre pozisyon alın
• Stop-loss seviyeleri belirleyin
• Hacim artışlarını takip edin

Orta Vadeli Strateji (1-6 ay):
• Trend yönünde pozisyon alın
• Düzenli alım stratejisi uygulayın
• Portföy çeşitlendirmesi yapın

Risk Yönetimi:
• Pozisyon büyüklüğünü risk toleransınıza göre ayarlayın
• Farklı zaman dilimlerinde analiz yapın
• Piyasa koşullarını sürekli izleyin

Not: Bu öneriler teknik analiz sonuçlarına dayalıdır. Yatırım kararı vermeden önce profesyonel danışmanlık almanızı öneririm."""
                            except Exception as e:
                                print(f"Gemini strateji hatası: {e}")
                                enhanced_response = f"""KCHOL Teknik Analiz Raporu

{result.get('analysis', '')}

{result.get('summary', '')}

---

YATIRIM STRATEJİSİ ÖNERİLERİ

Teknik analiz sonuçlarına göre, KCHOL hisse senedi için aşağıdaki stratejileri öneriyorum:

Kısa Vadeli Strateji (1-4 hafta):
• Teknik indikatörlerin gösterdiği yöne göre pozisyon alın
• Stop-loss seviyeleri belirleyin
• Hacim artışlarını takip edin

Orta Vadeli Strateji (1-6 ay):
• Trend yönünde pozisyon alın
• Düzenli alım stratejisi uygulayın
• Portföy çeşitlendirmesi yapın

Risk Yönetimi:
• Pozisyon büyüklüğünü risk toleransınıza göre ayarlayın
• Farklı zaman dilimlerinde analiz yapın
• Piyasa koşullarını sürekli izleyin

Not: Bu öneriler teknik analiz sonuçlarına dayalıdır. Yatırım kararı vermeden önce profesyonel danışmanlık almanızı öneririm."""
                        else:
                            enhanced_response = f"""KCHOL Teknik Analiz Raporu

{result.get('analysis', '')}

{result.get('summary', '')}

---

YATIRIM STRATEJİSİ ÖNERİLERİ

Teknik analiz sonuçlarına göre, KCHOL hisse senedi için aşağıdaki stratejileri öneriyorum:

Kısa Vadeli Strateji (1-4 hafta):
• Teknik indikatörlerin gösterdiği yöne göre pozisyon alın
• Stop-loss seviyeleri belirleyin
• Hacim artışlarını takip edin

Orta Vadeli Strateji (1-6 ay):
• Trend yönünde pozisyon alın
• Düzenli alım stratejisi uygulayın
• Portföy çeşitlendirmesi yapın

Risk Yönetimi:
• Pozisyon büyüklüğünü risk toleransınıza göre ayarlayın
• Farklı zaman dilimlerinde analiz yapın
• Piyasa koşullarını sürekli izleyin

Not: Bu öneriler teknik analiz sonuçlarına dayalıdır. Yatırım kararı vermeden önce profesyonel danışmanlık almanızı öneririm."""
                        
                        return enhanced_response
                    
                    response = create_enhanced_technical_response()
                    
                    # Bot yanıtını oturuma ekle
                    add_message_to_session(session_id, 'bot', response, 'technical_analysis', result)
                    
                    return jsonify({
                        'response': response,
                        'type': 'technical_analysis',
                        'data': result,
                        'session_id': session_id
                    })
                    
                except Exception as e:
                    error_response = f'Teknik analiz yapılamadı: {str(e)}'
                    add_message_to_session(session_id, 'bot', error_response, 'error')
                    return jsonify({
                        'response': error_response,
                        'type': 'error',
                        'session_id': session_id
                    })
            else:
                error_response = 'Teknik analiz motoru şu anda kullanılamıyor.'
                add_message_to_session(session_id, 'bot', error_response, 'error')
                return jsonify({
                    'response': error_response,
                    'type': 'error',
                    'session_id': session_id
                })
                
        elif any(word in message for word in ['tahmin', 'fiyat', 'ne olacak', 'yükselir mi', 'düşer mi', 'niye düştü', 'neden düştü', 'bugün niye', 'bugün neden']):
            # Hisse verisi al
            df = get_stock_data()
            if df is None:
                error_response = 'Hisse verisi alınamadı. Lütfen daha sonra tekrar deneyin.'
                add_message_to_session(session_id, 'bot', error_response, 'error')
                return jsonify({
                    'response': error_response,
                    'type': 'error',
                    'session_id': session_id
                })
            
            # Teknik tahmin yap
            result, error = predict_price(model, df)
            if error:
                error_response = f'Tahmin yapılamadı: {error}'
                add_message_to_session(session_id, 'bot', error_response, 'error')
                return jsonify({
                    'response': error_response,
                    'type': 'error',
                    'session_id': session_id
                })
            
            # Sadece model tahmini ve teknik analiz ile cevap ver (web araması yapma)
            print("Model tahmini ve teknik analiz ile yanıt oluşturuluyor...")
            
            # Trend metni oluştur
            trend_text = "Yükseliş bekleniyor!" if result['change'] > 0 else "Düşüş bekleniyor!" if result['change'] < 0 else "Fiyat sabit kalabilir"
            
            # Model açıklamasını ekle - profesyonel paragraf formatında
            model_explanation = result.get('model_explanation', {})
            explanation_text = ""
            if model_explanation:
                explanation_text = f"""

Teknik analiz sonuçlarına göre trend yönü {model_explanation.get('trend_direction', 'Belirsiz')} olarak belirlenmiştir. Güven seviyesi {model_explanation.get('confidence', 'Düşük')} olarak hesaplanmıştır.

"""
                for explanation in model_explanation.get('explanations', [])[:3]:  # İlk 3 açıklama
                    explanation_text += f"{explanation} "
                
                # Ana faktörlerin detaylarını ekle - profesyonel paragraf formatında
                key_factors = model_explanation.get('key_factors', {})
                if key_factors:
                    explanation_text += f"""

Teknik göstergelerin detaylı analizi sonucunda, fiyat 200 günlük hareketli ortalamanın {key_factors.get('price_vs_sma200', 'Belirsiz')} tarafında konumlanmaktadır. RSI göstergesi {key_factors.get('rsi_signal', 'Belirsiz')} seviyede olup, volatilite {key_factors.get('volatility', 'Belirsiz')} seviyede seyretmektedir. Hacim verileri ise {key_factors.get('volume_strength', 'Belirsiz')} bir yapı göstermektedir."""
            
            # Teknik analiz özeti - bağlamlı ve neden-sonuç ilişkili
            technical_summary = f"""

TEKNİK ANALİZ ÖZETİ

KCHOL hisse senedi şu anda {result['current_price']} TL seviyesinde işlem görüyor.

Model tahminine göre hisse senedi {result['predicted_price']:.2f} TL seviyesine ulaşacak.

Beklenen değişim {result['change']:+.2f} TL olacak, bu da {result['change_percent']:+.2f}% anlamına geliyor.

Tahmin tarihi: {result['prediction_date']}

{explanation_text}

RİSK UYARISI: Bu analiz sadece teknik göstergelere dayalıdır ve yatırım tavsiyesi değildir. Hisse senedi yatırımları risklidir ve kayıplara yol açabilir. Yatırım kararı vermeden önce kendi araştırmalarınızı yapmalı ve finansal danışmanınızla görüşmelisiniz."""
            
            response = f"""KCHOL Hisse Senedi Fiyat Tahmini

KCHOL hisse senedi şu anda {result['current_price']} TL seviyesinde işlem görüyor. Teknik analiz sonuçlarına göre, hisse senedinin {result['predicted_price']:.2f} TL seviyesine {result['change']:+.2f} TL ({result['change_percent']:+.2f}%) değişimle ulaşması bekleniyor. {trend_text}

{explanation_text}

Bu analiz, hisse senedinin geçmiş fiyat hareketleri, teknik göstergeler ve piyasa dinamikleri dikkate alınarak yapılmıştır. Sistemimiz, 200 günlük hareketli ortalama, RSI, MACD, Bollinger Bantları ve hacim verilerini analiz ederek tahmin üretmektedir. Ancak, bu tahminlerin kesinliği ve doğruluğu hakkında kesin bir yorum yapmak mümkün değildir. Tahmin yalnızca bir olasılığı temsil etmektedir.

⚠️ RİSK UYARISI: Bu analiz sadece teknik göstergelere dayalıdır ve yatırım tavsiyesi değildir. Hisse senedi yatırımları risklidir ve kayıplara yol açabilir. Yatırım kararı vermeden önce kendi araştırmalarınızı yapmalı ve finansal danışmanınızla görüşmelisiniz."""
            
            # Bot yanıtını oturuma ekle
            add_message_to_session(session_id, 'bot', response, 'prediction', result)
            
            return jsonify({
                'response': response,
                'type': 'prediction',
                'data': result,
                'session_id': session_id
            })
            
        elif any(word in message for word in ['yardım', 'help', 'nasıl', 'ne yapabilir']):
            help_response = """
KCHOL Hisse Senedi Asistanı

Size şu konularda yardımcı olabilirim:

📊 Teknik Analiz: "Teknik analiz yap", "RSI göster", "MACD analizi" gibi sorular
📈 Fiyat Tahmini: "Fiyat tahmini yap", "Ne olacak", "Yükselir mi" gibi sorular
📰 Haber Analizi: "Haber analizi yap", "Son haberler" gibi sorular
💡 Öneriler: Yatırım kararlarınız için veri tabanlı öneriler
🔍 Finansal Q&A: Doğal dil ile finansal sorular
🎯 Hisse Simülasyonu: Geçmiş yatırım senaryoları

📊 **Hisse Simülasyon Örnekleri:**
• "KCHOL'a 6 ay önce 10.000 TL yatırsaydım ne olurdu?"
• "THYAO'ya 1 yıl önce 50.000 TL yatırsaydım kaç para kazanırdım?"
• "GARAN'a 3 ay önce 25.000 TL yatırım simülasyonu"
• "AKBNK'ya 2023 başında 100.000 TL yatırsaydım ne olurdu?"

🔍 **Finansal Q&A Örnekleri:**
• "Son 6 ayda THYAO'nun ortalama hacmi nedir?"
• "XU100 endeksinden hangi hisseler bugün düştü?"
• "Bana RSI'si 70 üstü olan hisseleri listeler misin?"
• "KCHOL'un RSI değeri nedir?"
• "GARAN'ın son 3 aylık hacim analizi"

📚 **Finansal Eğitim:**
• "RSI nedir?" - Teknik gösterge eğitimi
• "Volatilite yüksek ne demek?" - Risk analizi
• "SMA 50 ve SMA 200 neyi ifade eder?" - Hareketli ortalamalar

📈 **Teknik Analiz Özellikleri:**
• RSI (Relative Strength Index)
• MACD (Moving Average Convergence Divergence)
• SMA (Simple Moving Average) - 20, 50, 200 günlük
• Bollinger Bands
• Williams %R
• ATR (Average True Range)

Sadece sorunuzu yazın, size yardımcı olayım!
            """
            add_message_to_session(session_id, 'bot', help_response, 'help')
            return jsonify({
                'response': help_response,
                'type': 'help',
                'session_id': session_id
            })
            
        elif any(word in message for word in ['merhaba', 'selam', 'hi', 'hello']) and len(message.split()) <= 3:
            # Sadece kısa selamlaşma mesajları için greeting
            greeting_response = 'Merhaba! Ben KCHOL hisse senedi fiyat tahmin asistanınız. Size yardımcı olmak için buradayım. Fiyat tahmini yapmak ister misiniz?'
            add_message_to_session(session_id, 'bot', greeting_response, 'greeting')
            return jsonify({
                'response': greeting_response,
                'type': 'greeting',
                'session_id': session_id
            })
            
        elif any(word in message for word in ['haber analizi', 'haber', 'news']):
            # Haber analizi yap
            try:
                print("Haber analizi başlatılıyor...")
                news_articles = get_news_articles("KCHOL Koç Holding", days=7)
                sentiment_analysis = analyze_news_sentiment(news_articles)
                news_insights = generate_news_insights(sentiment_analysis)
                
                response = f"""
KCHOL Haber Analizi

{news_insights}

Sentiment Skoru: {sentiment_analysis['sentiment_score']:.3f}
Genel Durum: {sentiment_analysis['overall_sentiment'].upper()}
            """
                
                add_message_to_session(session_id, 'bot', response, 'news_analysis', sentiment_analysis)
                return jsonify({
                    'response': response,
                    'type': 'news_analysis',
                    'data': sentiment_analysis,
                    'session_id': session_id
                })
            except Exception as error:
                print(f"Haber analizi hatası: {error}")
                error_response = 'Haber analizi yapılamadı. Lütfen daha sonra tekrar deneyin.'
                add_message_to_session(session_id, 'bot', error_response, 'error')
                return jsonify({
                    'response': error_response,
                    'type': 'error',
                    'session_id': session_id
                })
                
        elif any(word in message for word in ['konservatif', 'agresif', 'dengeli', 'riskli', 'güvenli', 'düşüşte alım', 'kişiselleştirilmiş', 'özel tavsiye', 'risk profili', 'yatırım tavsiyesi', 'hangi hisseler', 'uygun hisseler', 'öneri', 'tavsiye']) or ('kısa vadeli' in message.lower() and ('yatırımcı' in message.lower() or 'yatırım' in message.lower())) or ('uzun vadeli' in message.lower() and ('yatırımcı' in message.lower() or 'yatırım' in message.lower())) or ('orta vadeli' in message.lower() and ('yatırımcı' in message.lower() or 'yatırım' in message.lower())):
            # Kişiselleştirilmiş yatırım tavsiyesi
            if investment_advisor:
                try:
                    print(f"Investment Advisor'a gönderilen soru: {original_message}")
                    advice_result = investment_advisor.generate_personalized_advice(original_message)
                    
                    if advice_result.get('success'):
                        response = advice_result.get('advice', 'Tavsiye oluşturulamadı.')
                        
                        add_message_to_session(session_id, 'bot', response, 'personalized_advice', advice_result)
                        return jsonify({
                            'response': response,
                            'type': 'personalized_advice',
                            'data': advice_result,
                            'session_id': session_id
                        })
                except Exception as e:
                    print(f"Investment Advisor hatası: {e}")
            
            # Fallback: Eski strateji yanıtı
            def create_investment_strategy_response():
                # Mevcut fiyat bilgisini al
                try:
                    df = get_stock_data()
                    current_price = df.iloc[-1]['close'] if df is not None else "Bilinmiyor"
                except:
                    current_price = "Bilinmiyor"
                
                # Strateji türüne göre yanıt oluştur
                if any(word in message for word in ['uzun vadeli', 'long term', 'value investing']):
                    strategy_type = "Uzun Vadeli Yatırım Stratejisi"
                    strategy_details = """
• KCHOL, Türkiye'nin en büyük holding şirketlerinden biri olarak uzun vadeli büyüme potansiyeli sunar
• Otomotiv, dayanıklı tüketim ve enerji sektörlerinde güçlü pozisyon
• Düzenli temettü ödemeleri ile gelir getirisi
• 5-10 yıllık yatırım ufku önerilir
• Düzenli alım stratejisi (DCA) uygulayın"""
                elif any(word in message for word in ['kısa vadeli', 'short term', 'swing trading', 'day trading']):
                    strategy_type = "Kısa Vadeli Trading Stratejisi"
                    strategy_details = """
• Teknik analiz odaklı yaklaşım
• RSI, MACD, Bollinger Bands kullanın
• Stop-loss seviyeleri mutlaka belirleyin
• Risk/ödül oranı 1:2 veya daha iyi olmalı
• Günlük/haftalık grafikleri takip edin"""
                elif any(word in message for word in ['dca', 'dollar cost averaging', 'düzenli alım']):
                    strategy_type = "Düzenli Alım Stratejisi (DCA)"
                    strategy_details = """
• Aylık düzenli alım yapın (örn: 1000 TL)
• Fiyat düştüğünde daha fazla hisse alırsınız
• Ortalama maliyeti düşürür
• Piyasa volatilitesinden etkilenmez
• Uzun vadede etkili bir strateji"""
                else:
                    strategy_type = "Genel Yatırım Stratejisi"
                    strategy_details = """
• Portföyünüzün maksimum %10-15'ini KCHOL'a ayırın
• Risk toleransınıza göre pozisyon büyüklüğü belirleyin
• Teknik ve temel analizi birlikte kullanın
• Düzenli olarak portföyünüzü gözden geçirin
• Stop-loss ve take-profit seviyeleri belirleyin"""
                
                response = f"""KCHOL Hisse Senedi {strategy_type}

Mevcut Fiyat: {current_price} TL

{strategy_details}

Risk Yönetimi:
• Portföy çeşitlendirmesi yapın
• Farklı sektörlerde hisse senetleri bulundurun
• Altın, döviz gibi alternatif yatırım araçları ekleyin
• Risk toleransınıza uygun varlık dağılımı yapın

Teknik Analiz Kullanımı:
• RSI, MACD gibi teknik indikatörleri takip edin
• 200 günlük hareketli ortalama seviyelerini izleyin
• Hacim analizini göz önünde bulundurun
• Destek ve direnç seviyelerini belirleyin

Temel Analiz:
• Çeyreklik finansal raporları takip edin
• Sektörel trendleri analiz edin
• Makroekonomik faktörleri değerlendirin
• Şirket yönetimi ve stratejilerini izleyin

Not: Bu öneriler genel bilgi amaçlıdır. Yatırım kararı vermeden önce profesyonel danışmanlık almanızı öneririm."""
                
                return response
            
            strategy_response = create_investment_strategy_response()
            
            add_message_to_session(session_id, 'bot', strategy_response, 'investment_strategy')
            return jsonify({
                'response': strategy_response,
                'type': 'investment_strategy',
                'session_id': session_id
            })
            
        elif any(word in message for word in ['simülasyon', 'simulasyon', 'simulation', 'yatırım simülasyonu', 'yatirim simulasyonu', 'ne olurdu', 'olurdu', 'kaç para', 'kac para', 'kazanç', 'kazanc']):
            # Hisse simülasyon analizi
            if hisse_simulasyon:
                try:
                    print(f"Hisse Simülasyon'a gönderilen soru: {original_message}")
                    
                    # Kullanıcı mesajından bilgileri çıkar
                    import re
                    
                    # Hisse kodu çıkar
                    hisse_pattern = r'\b([A-Z]{2,6}(?:\.IS)?)\b'
                    hisse_match = re.search(hisse_pattern, original_message.upper())
                    hisse_kodu = hisse_match.group(1) if hisse_match else None
                    
                    # Tarih çıkar
                    tarih_pattern = r'\b(\d+\s*(?:ay|yıl|hafta|gün)\s*önce|\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{4}\s*başı|\d{4}\s*sonu)\b'
                    tarih_match = re.search(tarih_pattern, original_message.lower())
                    tarih = tarih_match.group(1) if tarih_match else "1 ay önce"
                    
                    # Tutar çıkar - gelişmiş yaklaşım
                    # Önce "bin" kelimesini kontrol et
                    if "bin" in original_message.lower():
                        # "10 bin" -> 10000
                        bin_pattern = r'(\d+)\s*bin'
                        bin_match = re.search(bin_pattern, original_message.lower())
                        if bin_match:
                            tutar = float(bin_match.group(1)) * 1000
                        else:
                            tutar = 10000.0
                    else:
                        # Tüm sayıları bul ve en büyük olanı al
                        # Önce çoklu noktalı sayıları (1.500.000 gibi) bul
                        multi_dot_numbers = re.findall(r'\d+\.\d+\.\d+', original_message)
                        if multi_dot_numbers:
                            # Çoklu noktalı sayıları işle (1.500.000 -> 1500000)
                            numbers = []
                            for num_str in multi_dot_numbers:
                                # Tüm noktaları kaldır ve sayıya çevir
                                clean_num = num_str.replace('.', '')
                                numbers.append(int(clean_num))
                            tutar = max(numbers)
                        else:
                            # Tek noktalı sayıları (10.000 gibi) bul
                            dot_numbers = re.findall(r'\d+\.\d+', original_message)
                            if dot_numbers:
                                # Noktalı sayıları işle (10.000 -> 10000)
                                numbers = []
                                for num_str in dot_numbers:
                                    # Noktayı kaldır ve sayıya çevir
                                    clean_num = num_str.replace('.', '')
                                    numbers.append(int(clean_num))
                                tutar = max(numbers)
                            else:
                                # Normal sayıları bul
                                all_numbers = re.findall(r'\d+', original_message)
                                if all_numbers:
                                    # En büyük sayıyı bul (muhtemelen yatırım tutarı)
                                    numbers = [int(num) for num in all_numbers]
                                    tutar = max(numbers)
                                else:
                                    # Varsayılan tutar
                                    tutar = 10000.0
                    
                    if not hisse_kodu:
                        # Varsayılan hisse kodları
                        default_hisseler = ['KCHOL.IS', 'THYAO.IS', 'GARAN.IS', 'AKBNK.IS']
                        for hisse in default_hisseler:
                            if hisse.lower().replace('.is', '') in original_message.lower():
                                hisse_kodu = hisse
                                break
                        
                        if not hisse_kodu:
                            hisse_kodu = 'KCHOL.IS'  # Varsayılan
                    
                    # Simülasyon çalıştır
                    sim_result = hisse_simulasyon(hisse_kodu, tarih, tutar)
                    
                    if 'hata' not in sim_result:
                        response = f"""📊 **Hisse Senedi Simülasyon Sonucu**

🎯 **Simülasyon Detayları:**
• **Hisse:** {sim_result['hisse']}
• **Başlangıç Tarihi:** {sim_result['başlangıç tarihi']}
• **Yatırım Tutarı:** {tutar:,.2f} TL

💰 **Fiyat Analizi:**
• **Başlangıç Fiyatı:** {sim_result['başlangıç fiyatı']} TL
• **Güncel Fiyat:** {sim_result['güncel fiyat']} TL
• **Alınan Lot:** {sim_result['alınan lot']} adet

📈 **Sonuç:**
• **Şu Anki Değer:** {sim_result['şu anki değer']:,.2f} TL
• **Net Kazanç:** {sim_result['net kazanç']:,.2f} TL
• **Getiri Oranı:** %{sim_result['getiri %']:.2f}

{'🟢 **KARLILIK**' if sim_result['net kazanç'] > 0 else '🔴 **ZARAR**' if sim_result['net kazanç'] < 0 else '⚪ **BREAKEVEN**'}

⚠️ **Risk Uyarısı:** Bu simülasyon geçmiş verilere dayalıdır. Gelecekteki performans garantisi vermez. Yatırım kararı vermeden önce profesyonel danışmanlık alın."""
                    else:
                        response = f"❌ Simülasyon hatası: {sim_result['hata']}"
                    
                    add_message_to_session(session_id, 'bot', response, 'simulation', sim_result)
                    return jsonify({
                        'response': response,
                        'type': 'simulation',
                        'data': sim_result,
                        'session_id': session_id
                    })
                        
                except Exception as sim_error:
                    print(f"Hisse simülasyon hatası: {sim_error}")
                    error_response = 'Hisse simülasyonu yapılamadı. Lütfen daha sonra tekrar deneyin.'
                    add_message_to_session(session_id, 'bot', error_response, 'error')
                    return jsonify({
                        'response': error_response,
                        'type': 'error',
                        'session_id': session_id
                    })
            else:
                error_response = 'Hisse simülasyon sistemi şu anda kullanılamıyor.'
                add_message_to_session(session_id, 'bot', error_response, 'error')
                return jsonify({
                    'response': error_response,
                    'type': 'error',
                    'session_id': session_id
                })
            
        elif any(word in message for word in ['xu100', 'bist', 'endeks', 'index', '70 üstü', '70 üzeri', '70 ustu', '70 uzeri', 'thyao', 'garan', 'akbnk', 'isctr', 'asels', 'eregl', 'sasa']) and not any(word in message for word in ['grafik', 'göster', 'analiz', 'teknik']):
            # Finansal Q&A Agent ile doğal dil soruları
            if financial_qa_agent:
                try:
                    print(f"Finansal Q&A Agent'a gönderilen soru: {original_message}")
                    qa_result = financial_qa_agent.process_financial_question(original_message)
                    
                    if qa_result.get('success'):
                        response = qa_result.get('response', 'Yanıt oluşturulamadı.')
                        question_type = qa_result.get('question_type', 'unknown')
                        
                        add_message_to_session(session_id, 'bot', response, 'financial_qa', qa_result)
                        return jsonify({
                            'response': response,
                            'type': 'financial_qa',
                            'data': qa_result,
                            'session_id': session_id
                        })
                    else:
                        error_response = f"Finansal analiz hatası: {qa_result.get('error', 'Bilinmeyen hata')}"
                        add_message_to_session(session_id, 'bot', error_response, 'error')
                        return jsonify({
                            'response': error_response,
                            'type': 'error',
                            'session_id': session_id
                        })
                        
                except Exception as qa_error:
                    print(f"Finansal Q&A hatası: {qa_error}")
                    error_response = 'Finansal analiz yapılamadı. Lütfen daha sonra tekrar deneyin.'
                    add_message_to_session(session_id, 'bot', error_response, 'error')
                    return jsonify({
                        'response': error_response,
                        'type': 'error',
                        'session_id': session_id
                    })
            else:
                error_response = 'Finansal Q&A sistemi şu anda kullanılamıyor.'
                add_message_to_session(session_id, 'bot', error_response, 'error')
                return jsonify({
                    'response': error_response,
                    'type': 'error',
                    'session_id': session_id
                })
            
        else:
            # Genel sorulara Gemini'den cevap al
            try:
                print(f"Genel soru Gemini'ye gönderiliyor: {original_message}")
                
                # Gemini prompt'u hazırla
                gemini_prompt = f"""
Sen bir finansal asistan ve yatırım danışmanısın. Kullanıcının sorusuna Türkçe olarak, profesyonel ve anlaşılır bir şekilde cevap ver.

Kullanıcı sorusu: {original_message}

Yanıt kuralları:
- Sadece Türkçe yanıt ver
- Emoji kullanma
- Düzyazı şeklinde yaz
- Finansal konularda güvenilir bilgi ver
- Gerektiğinde örnekler kullan
- Risk uyarıları ekle
- Maksimum 3-4 paragraf yaz
- Eğer yatırım tavsiyesi ise "Bu bir yatırım tavsiyesi değildir" uyarısı ekle

Eğer soru finansal değilse, genel bilgi ver ve finansal konulara yönlendir.
"""
                
                gemini_response = get_gemini_response(gemini_prompt)
                print(f"Gemini'den gelen yanit: {gemini_response}")
                
                add_message_to_session(session_id, 'bot', gemini_response, 'ai_response')
                return jsonify({
                    'response': gemini_response,
                    'type': 'ai_response',
                    'session_id': session_id
                })
                
            except Exception as error:
                print(f"Gemini yanit hatasi: {error}")
                
                # Fallback to Document RAG Agent
                try:
                    if document_rag_agent:
                        print(f"Document RAG Agent'a gonderilen mesaj: {original_message}")
                        rag_response = document_rag_agent.process_query(original_message)
                        print(f"Document RAG Agent'dan gelen yanit: {rag_response}")
                        add_message_to_session(session_id, 'bot', rag_response, 'ai_response')
                        return jsonify({
                            'response': rag_response,
                            'type': 'ai_response',
                            'session_id': session_id
                        })
                    else:
                        # Final fallback
                        error_response = 'Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen daha sonra tekrar deneyin.'
                        add_message_to_session(session_id, 'bot', error_response, 'unknown')
                        return jsonify({
                            'response': error_response,
                            'type': 'unknown',
                            'session_id': session_id
                        })
                except Exception as rag_error:
                    print(f"Document RAG Agent hatasi: {rag_error}")
                    error_response = 'Üzgünüm, şu anda size yardımcı olamıyorum. Lütfen daha sonra tekrar deneyin.'
                    add_message_to_session(session_id, 'bot', error_response, 'unknown')
                    return jsonify({
                        'response': error_response,
                        'type': 'unknown',
                        'session_id': session_id
                    })
            
    except Exception as e:
        return jsonify({
            'response': f'Bir hata oluştu: {str(e)}',
            'type': 'error'
        })

@app.route('/api/add_document', methods=['POST'])
def add_document():
    """Add a new document to the knowledge base"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Dosya bulunamadı'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Dosya seçilmedi'
            }), 400
        
        # Save file to documents folder
        documents_path = Path('documents')
        documents_path.mkdir(exist_ok=True)
        
        file_path = documents_path / file.filename
        file.save(file_path)
        
        # Add to Document RAG Agent if available
        if document_rag_agent:
            success = document_rag_agent.add_document(str(file_path))
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Doküman başarıyla eklendi: {file.filename}'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Doküman işlenirken hata oluştu'
                }), 500
        
        return jsonify({
            'success': True,
            'message': f'Doküman kaydedildi: {file.filename}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/new_chat', methods=['POST'])
def new_chat():
    """Yeni sohbet başlat"""
    try:
        session_id = create_new_session()
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Yeni sohbet başlatıldı'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/chat_history', methods=['GET'])
def get_chat_history():
    """Sohbet geçmişini döndür"""
    session_id = request.args.get('session_id')
    format_type = request.args.get('format', 'txt')  # txt, json, html
    
    print(f"Chat history request - Session ID: {session_id}, Format: {format_type}")
    print(f"Available sessions: {list(chat_sessions.keys())}")
    
    # Eğer session_id yoksa mevcut oturumu kullan
    if not session_id:
        current_session = get_current_session()
        if current_session:
            session_id = current_session['id']
            print(f"Using current session: {session_id}")
        else:
            print("No current session found")
            return jsonify({
                'success': False,
                'message': 'Aktif oturum bulunamadı'
            }), 400
    
    print(f"Exporting history for session: {session_id}")
    history_content = export_chat_history(session_id, format_type)
    if history_content is None:
        print(f"Session not found: {session_id}")
        return jsonify({
            'success': False,
            'message': f'Oturum bulunamadı: {session_id}'
        }), 404
    
    print(f"History content length: {len(history_content) if history_content else 0}")
    
    import io
    
    if format_type == 'json':
        return send_file(
            io.BytesIO(history_content.encode('utf-8')),
            mimetype='application/json',
            as_attachment=True,
            download_name=f'kchol_chat_history_{session_id}.json'
        )
    elif format_type == 'html':
        return send_file(
            io.BytesIO(history_content.encode('utf-8')),
            mimetype='text/html',
            as_attachment=True,
            download_name=f'kchol_chat_history_{session_id}.html'
        )
    else:  # txt
        return send_file(
            io.BytesIO(history_content.encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name=f'kchol_chat_history_{session_id}.txt'
        )

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Tüm sohbet oturumlarını listele"""
    try:
        sessions_list = []
        for session_id, session_data in chat_sessions.items():
            sessions_list.append({
                'id': session_id,
                'title': session_data['title'],
                'created_at': session_data['created_at'],
                'message_count': len(session_data['messages'])
            })
        
        # Tarihe göre sırala (en yeni önce)
        sessions_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'sessions': sessions_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hata: {str(e)}'
        }), 500

@app.route('/api/news_analysis', methods=['GET'])
def get_news_analysis():
    """KCHOL ile ilgili haber analizini döndür"""
    try:
        query = request.args.get('query', 'KCHOL Koç Holding')
        days = int(request.args.get('days', 7))
        
        # Haberleri al
        articles = get_news_articles("Koç Holding", days)
        
        # Sentiment analizi yap
        sentiment_analysis = analyze_news_sentiment(articles)
        
        # İçgörüler oluştur
        insights = generate_news_insights(sentiment_analysis)
        
        return jsonify({
            'success': True,
            'query': query,
            'days': days,
            'sentiment_analysis': sentiment_analysis,
            'insights': insights,
            'articles_count': len(articles)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Haber analizi hatası: {str(e)}'
        }), 500

@app.route('/api/technical_analysis', methods=['POST'])
def get_technical_analysis():
    """Teknik analiz isteğini işle"""
    try:
        data = request.get_json()
        user_request = data.get('request', '')
        
        if not technical_analysis_engine:
            return jsonify({
                'success': False,
                'message': 'Teknik analiz motoru kullanılamıyor'
            }), 500
        
        # Teknik analiz yap
        result = technical_analysis_engine.process_technical_analysis_request(user_request)
        
        if result.get('error'):
            # Gemini API olmadan da çalışabilmeli
            if "Gemini model" in result['error']:
                # Varsayılan analiz yap
                df = technical_analysis_engine.get_stock_data()
                if df is not None:
                    charts = technical_analysis_engine.create_default_charts(df)
                    analysis = technical_analysis_engine.analyze_technical_indicators(df)
                    
                    result = {
                        "charts": charts,
                        "analysis": analysis,
                        "summary": f"KCHOL hisse senedi teknik analizi tamamlandı. {len(charts)} grafik oluşturuldu.",
                        "error": None
                    }
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Hisse verisi alınamadı'
                    }), 500
            else:
                return jsonify({
                    'success': False,
                    'message': result['error']
                }), 500
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Teknik analiz hatası: {str(e)}'
        }), 500

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Kullanıcının portföyünü getir"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        if not portfolio_manager:
            return jsonify({
                'success': False,
                'message': 'Portföy yöneticisi kullanılamıyor'
            }), 500
        
        portfolio_summary = portfolio_manager.get_portfolio_summary(user_id)
        
        return jsonify({
            'success': True,
            'data': portfolio_summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Portföy getirme hatası: {str(e)}'
        }), 500

@app.route('/api/portfolio/add', methods=['POST'])
def add_stock_to_portfolio():
    """Portföye yeni hisse senedi ekle"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        symbol = data.get('symbol', '').upper()
        quantity = float(data.get('quantity', 0))
        avg_price = float(data.get('avg_price', 0))
        
        if not symbol or quantity <= 0 or avg_price <= 0:
            return jsonify({
                'success': False,
                'message': 'Geçersiz veri: symbol, quantity ve avg_price pozitif olmalı'
            }), 400
        
        if not portfolio_manager:
            return jsonify({
                'success': False,
                'message': 'Portföy yöneticisi kullanılamıyor'
            }), 500
        
        result = portfolio_manager.add_stock(user_id, symbol, quantity, avg_price)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hisse ekleme hatası: {str(e)}'
        }), 500

@app.route('/api/portfolio/remove', methods=['POST'])
def remove_stock_from_portfolio():
    """Portföyden hisse senedi çıkar"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        symbol = data.get('symbol', '').upper()
        quantity = data.get('quantity')  # None ise tüm hisseyi çıkar
        
        if not symbol:
            return jsonify({
                'success': False,
                'message': 'Geçersiz symbol'
            }), 400
        
        if not portfolio_manager:
            return jsonify({
                'success': False,
                'message': 'Portföy yöneticisi kullanılamıyor'
            }), 500
        
        if quantity is not None:
            quantity = float(quantity)
            if quantity <= 0:
                return jsonify({
                    'success': False,
                    'message': 'Quantity pozitif olmalı'
                }), 400
        
        result = portfolio_manager.remove_stock(user_id, symbol, quantity)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Hisse çıkarma hatası: {str(e)}'
        }), 500

@app.route('/api/portfolio/calculate', methods=['GET'])
def calculate_portfolio_value():
    """Portföy değerini hesapla"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        if not portfolio_manager:
            return jsonify({
                'success': False,
                'message': 'Portföy yöneticisi kullanılamıyor'
            }), 500
        
        portfolio_value = portfolio_manager.calculate_portfolio_value(user_id)
        
        return jsonify({
            'success': True,
            'data': portfolio_value
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Portföy hesaplama hatası: {str(e)}'
        }), 500

# Finansal Takvim API Endpoint'leri
@app.route('/api/calendar', methods=['GET'])
def get_financial_calendar():
    """Finansal takvim verilerini getir"""
    try:
        if not financial_calendar:
            return jsonify({
                'success': False,
                'message': 'Finansal takvim kullanılamıyor'
            }), 500
        
        # Tüm şirketleri getir
        companies = financial_calendar.get_companies()
        calendar_data = {}
        
        for company in companies:
            company_events = financial_calendar.get_company_events(company)
            if company_events:
                calendar_data[company] = company_events
        
        return jsonify({
            'success': True,
            'data': calendar_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Finansal takvim hatası: {str(e)}'
        }), 500

@app.route('/api/calendar/company/<symbol>', methods=['GET'])
def get_company_calendar(symbol):
    """Belirli şirketin finansal takvimini getir"""
    try:
        if not financial_calendar:
            return jsonify({
                'success': False,
                'message': 'Finansal takvim kullanılamıyor'
            }), 500
        
        company_events = financial_calendar.get_company_events(symbol.upper())
        
        if not company_events:
            return jsonify({
                'success': False,
                'message': f'{symbol} için finansal takvim bulunamadı'
            }), 404
        
        return jsonify({
            'success': True,
            'data': company_events
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Şirket takvimi hatası: {str(e)}'
        }), 500

@app.route('/api/calendar/upcoming', methods=['GET'])
def get_upcoming_events():
    """Yaklaşan finansal olayları getir"""
    try:
        if not financial_calendar:
            return jsonify({
                'success': False,
                'message': 'Finansal takvim kullanılamıyor'
            }), 500
        
        days = request.args.get('days', 30, type=int)
        upcoming_events = financial_calendar.get_upcoming_events(days)
        
        return jsonify({
            'success': True,
            'data': upcoming_events
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Yaklaşan olaylar hatası: {str(e)}'
        }), 500

@app.route('/api/calendar/search', methods=['POST'])
def search_calendar_events():
    """Finansal takvimde arama yap"""
    try:
        if not financial_calendar:
            return jsonify({
                'success': False,
                'message': 'Finansal takvim kullanılamıyor'
            }), 500
        
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'success': False,
                'message': 'Arama sorgusu gerekli'
            }), 400
        
        search_results = financial_calendar.search_events(query)
        
        return jsonify({
            'success': True,
            'data': search_results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Arama hatası: {str(e)}'
        }), 500

@app.route('/api/calendar/add', methods=['POST'])
def add_calendar_event():
    """Finansal takvime yeni olay ekle"""
    try:
        if not financial_calendar:
            return jsonify({
                'success': False,
                'message': 'Finansal takvim kullanılamıyor'
            }), 500
        
        data = request.get_json()
        symbol = data.get('symbol', '').upper()
        event_type = data.get('type', '')
        event_date = data.get('date', '')
        description = data.get('description', '')
        source = data.get('source', 'KAP')
        status = data.get('status', 'bekliyor')
        
        if not all([symbol, event_type, event_date, description]):
            return jsonify({
                'success': False,
                'message': 'symbol, type, date ve description alanları gerekli'
            }), 400
        
        # Tarih formatını kontrol et
        try:
            datetime.strptime(event_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Geçersiz tarih formatı. YYYY-MM-DD formatında olmalı'
            }), 400
        
        result = financial_calendar.add_event(
            symbol=symbol,
            event_type=event_type,
            event_date=event_date,
            description=description,
            source=source,
            status=status
        )
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Olay başarıyla eklendi'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Olay eklenemedi'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Olay ekleme hatası: {str(e)}'
        }), 500

@app.route('/api/calendar/import', methods=['POST'])
def import_calendar_csv():
    """CSV dosyasından finansal takvim verisi yükle"""
    try:
        if not financial_calendar:
            return jsonify({
                'success': False,
                'message': 'Finansal takvim kullanılamıyor'
            }), 500
        
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'CSV dosyası gerekli'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'Dosya seçilmedi'
            }), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({
                'success': False,
                'message': 'Sadece CSV dosyaları kabul edilir'
            }), 400
        
        # Geçici dosya olarak kaydet
        temp_file = f"temp_calendar_{int(time.time())}.csv"
        file.save(temp_file)
        
        try:
            result = financial_calendar.import_from_csv(temp_file)
            if result:
                return jsonify({
                    'success': True,
                    'message': 'CSV dosyası başarıyla yüklendi'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'CSV yükleme hatası'
                }), 500
        finally:
            # Geçici dosyayı sil
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'CSV yükleme hatası: {str(e)}'
        }), 500

@app.route('/api/calendar/export', methods=['GET'])
def export_calendar_csv():
    """Finansal takvim verilerini CSV olarak dışa aktar"""
    try:
        if not financial_calendar:
            return jsonify({
                'success': False,
                'message': 'Finansal takvim kullanılamıyor'
            }), 500
        
        # Geçici dosya oluştur
        temp_file = f"financial_calendar_{int(time.time())}.csv"
        
        result = financial_calendar.export_to_csv(temp_file)
        if result:
            return send_file(
                temp_file,
                as_attachment=True,
                download_name=f"financial_calendar_{datetime.now().strftime('%Y%m%d')}.csv",
                mimetype='text/csv'
            )
        else:
            return jsonify({
                'success': False,
                'message': 'CSV dışa aktarma hatası'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'CSV dışa aktarma hatası: {str(e)}'
        }), 500

@app.route('/api/calendar/update/<symbol>', methods=['POST'])
def update_company_calendar(symbol):
    """Belirli şirketin finansal takvimini güncelle (scraping)"""
    try:
        if not financial_calendar:
            return jsonify({
                'success': False,
                'message': 'Finansal takvim kullanılamıyor'
            }), 500
        
        symbol = symbol.upper()
        force_update = request.args.get('force', 'false').lower() == 'true'
        
        print(f"{symbol} için finansal takvim güncelleniyor...")
        result = financial_calendar.update_company_events(symbol, force_update)
        
        if result:
            # Güncel veriyi getir
            company_data = financial_calendar.get_company_events(symbol, auto_update=False)
            return jsonify({
                'success': True,
                'message': f'{symbol} finansal takvimi güncellendi',
                'data': company_data
            })
        else:
            return jsonify({
                'success': False,
                'message': f'{symbol} güncellenemedi'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Güncelleme hatası: {str(e)}'
        }), 500

@app.route('/api/calendar/update-all', methods=['POST'])
def update_all_companies_calendar():
    """Tüm şirketlerin finansal takvimini güncelle (scraping)"""
    try:
        if not financial_calendar:
            return jsonify({
                'success': False,
                'message': 'Finansal takvim kullanılamıyor'
            }), 500
        
        # Hangi şirketleri güncelleyeceğimizi al
        data = request.get_json() or {}
        symbols = data.get('symbols', ['THYAO', 'KCHOL', 'GARAN', 'AKBNK', 'ISCTR', 'SAHOL', 'ASELS', 'EREGL'])
        force_update = data.get('force', False)
        
        print(f"Tüm şirketler için finansal takvim güncelleniyor...")
        results = financial_calendar.update_all_companies(symbols)
        
        # Başarılı güncellemeleri say
        successful_updates = sum(1 for success in results.values() if success)
        total_companies = len(symbols)
        
        return jsonify({
            'success': True,
            'message': f'{successful_updates}/{total_companies} şirket güncellendi',
            'data': {
                'results': results,
                'successful_updates': successful_updates,
                'total_companies': total_companies
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Toplu güncelleme hatası: {str(e)}'
        }), 500

@app.route('/api/calendar/summary', methods=['GET'])
def get_calendar_summary():
    """Finansal takvim özeti getir"""
    try:
        if not financial_calendar:
            return jsonify({
                'success': False,
                'message': 'Finansal takvim kullanılamıyor'
            }), 500
        
        summary = financial_calendar.get_calendar_summary()
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Özet getirme hatası: {str(e)}'
        }), 500

@app.route('/api/calendar/search/<query>', methods=['GET'])
def search_calendar_by_query(query):
    """Finansal takvimde arama yap"""
    try:
        if not financial_calendar:
            return jsonify({
                'success': False,
                'message': 'Finansal takvim kullanılamıyor'
            }), 500
        
        results = financial_calendar.search_events(query)
        return jsonify({
            'success': True,
            'data': results,
            'query': query,
            'result_count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Arama hatası: {str(e)}'
        }), 500

# Finansal Alarm API Endpoint'leri
@app.route('/api/alerts', methods=['GET'])
def get_user_alerts():
    """Kullanıcının alarmlarını getir"""
    try:
        if not financial_alert_system:
            return jsonify({
                'success': False,
                'message': 'Alarm sistemi kullanılamıyor'
            }), 500
        
        # Session ID'den user ID oluştur (şimdilik)
        session_id = request.args.get('session_id', 'default')
        user_id = f"user_{session_id}"
        
        active_alerts = financial_alert_system.get_user_alerts(user_id, 'active')
        triggered_alerts = financial_alert_system.get_user_alerts(user_id, 'triggered')
        cancelled_alerts = financial_alert_system.get_user_alerts(user_id, 'cancelled')
        
        # Dataclass'ları dict'e çevir
        def alert_to_dict(alert):
            return {
                'id': alert.id,
                'symbol': alert.symbol,
                'event_type': alert.event_type,
                'event_date': alert.event_date,
                'alert_date': alert.alert_date,
                'description': alert.description,
                'status': alert.status,
                'created_at': alert.created_at,
                'triggered_at': alert.triggered_at
            }
        
        return jsonify({
            'success': True,
            'data': {
                'active': [alert_to_dict(alert) for alert in active_alerts],
                'triggered': [alert_to_dict(alert) for alert in triggered_alerts],
                'cancelled': [alert_to_dict(alert) for alert in cancelled_alerts]
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Alarm getirme hatası: {str(e)}'
        }), 500

@app.route('/api/alerts/summary', methods=['GET'])
def get_alerts_summary():
    """Kullanıcının alarm özetini getir"""
    try:
        if not financial_alert_system:
            return jsonify({
                'success': False,
                'message': 'Alarm sistemi kullanılamıyor'
            }), 500
        
        session_id = request.args.get('session_id', 'default')
        user_id = f"user_{session_id}"
        
        summary = financial_alert_system.get_alert_summary(user_id)
        
        # Next alert'i dict'e çevir
        if summary['next_alert']:
            summary['next_alert'] = {
                'id': summary['next_alert'].id,
                'symbol': summary['next_alert'].symbol,
                'event_type': summary['next_alert'].event_type,
                'event_date': summary['next_alert'].event_date,
                'alert_date': summary['next_alert'].alert_date,
                'description': summary['next_alert'].description
            }
        
        return jsonify({
            'success': True,
            'data': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Alarm özeti getirme hatası: {str(e)}'
        }), 500

@app.route('/api/alerts/cancel/<int:alert_id>', methods=['POST'])
def cancel_alert(alert_id):
    """Alarmı iptal et"""
    try:
        if not financial_alert_system:
            return jsonify({
                'success': False,
                'message': 'Alarm sistemi kullanılamıyor'
            }), 500
        
        data = request.get_json() or {}
        session_id = data.get('session_id', 'default')
        user_id = f"user_{session_id}"
        
        success = financial_alert_system.cancel_alert(alert_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Alarm iptal edildi'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Alarm iptal edilemedi'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Alarm iptal hatası: {str(e)}'
        }), 500

@app.route('/api/alerts/delete/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Alarmı sil"""
    try:
        if not financial_alert_system:
            return jsonify({
                'success': False,
                'message': 'Alarm sistemi kullanılamıyor'
            }), 500
        
        data = request.get_json() or {}
        session_id = data.get('session_id', 'default')
        user_id = f"user_{session_id}"
        
        success = financial_alert_system.delete_alert(alert_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Alarm silindi'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Alarm silinemedi'
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Alarm silme hatası: {str(e)}'
        }), 500

@app.route('/api/alerts/create', methods=['POST'])
def create_alert():
    """Manuel alarm oluştur"""
    try:
        if not financial_alert_system:
            return jsonify({
                'success': False,
                'message': 'Alarm sistemi kullanılamıyor'
            }), 500
        
        data = request.get_json()
        session_id = request.args.get('session_id', 'default')
        user_id = f"user_{session_id}"
        
        required_fields = ['symbol', 'event_type', 'event_date', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'{field} alanı gerekli'
                }), 400
        
        days_before = data.get('days_before', 1)
        
        result = financial_alert_system.create_alert(
            user_id=user_id,
            symbol=data['symbol'].upper(),
            event_type=data['event_type'],
            event_date=data['event_date'],
            description=data['description'],
            days_before=days_before
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'alert_id': result['alert_id']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['error']
            }), 500
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Alarm oluşturma hatası: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)