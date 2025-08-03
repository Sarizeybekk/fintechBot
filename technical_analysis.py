import google.generativeai as genai
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import json
import subprocess
import tempfile
import os
from datetime import datetime, timedelta
from finta import TA
import warnings
warnings.filterwarnings('ignore')

# Gemini API anahtarını ayarla (environment variable'dan al)
import os
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class TechnicalAnalysisEngine:
    def __init__(self):
        self.model = None
        if GOOGLE_API_KEY:
            try:
                self.model = genai.GenerativeModel('gemini-pro')
            except Exception as e:
                print(f"Gemini model yüklenirken hata: {e}")
    
    def get_stock_data(self, symbol='KCHOL.IS', days=300):
        """Hisse verisi al ve teknik indikatörleri hesapla"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = yf.download(symbol, start_date, end_date, progress=False)
            
            if df.empty:
                return None
            
            # Sütun isimlerini düzenleme
            df.columns = ['_'.join(col).lower() for col in df.columns]
            df.columns = [col.split('_')[0] for col in df.columns]
            
            # Teknik indikatörler
            df['SMA20'] = TA.SMA(df, 20)
            df['SMA50'] = TA.SMA(df, 50)
            df['SMA200'] = TA.SMA(df, 200)
            df['RSI'] = TA.RSI(df)
            df['MACD'] = TA.MACD(df)['MACD']
            df['MACD_Signal'] = TA.MACD(df)['MACD_signal']
            df['BB_Upper'] = TA.BBANDS(df)['BB_UPPER']
            df['BB_Lower'] = TA.BBANDS(df)['BB_LOWER']
            df['BB_Middle'] = TA.BBANDS(df)['BB_MIDDLE']
            df['ATR'] = TA.ATR(df)
            df['Williams'] = TA.WILLIAMS(df)
            
            # NaN değerleri temizleme
            df = df.dropna()
            
            return df
        except Exception as e:
            print(f"Veri alma hatası: {e}")
            return None
    
    def generate_python_code(self, user_request, df):
        """Kullanıcı isteğine göre Python kodu üret"""
        if not self.model:
            return None, "Gemini model kullanılamıyor"
        
        try:
            # DataFrame'in yapısını string olarak hazırla
            df_info = f"""
DataFrame yapısı:
- Sütunlar: {list(df.columns)}
- Satır sayısı: {len(df)}
- Tarih aralığı: {df.index[0].strftime('%Y-%m-%d')} - {df.index[-1].strftime('%Y-%m-%d')}
- Son fiyat: {df['close'].iloc[-1]:.2f} TL
"""
            
            prompt = f"""
Sen bir finansal analiz uzmanısın. Kullanıcının isteğine göre Python kodu yazacaksın.

Kullanıcı isteği: {user_request}

Mevcut veri:
{df_info}

Gereksinimler:
1. Sadece Python kodu yaz, açıklama ekleme
2. DataFrame 'df' olarak mevcut
3. Plotly kullanarak interaktif grafikler oluştur
4. Grafikleri base64 formatında encode et
5. Sonuçları JSON formatında döndür
6. Türkçe etiketler kullan
7. Modern ve güzel görünümlü grafikler yap

Örnek çıktı formatı:
{{
    "charts": [
        {{
            "title": "Grafik Başlığı",
            "type": "line/candlestick/bar",
            "data": "base64_encoded_image"
        }}
    ],
    "analysis": "Analiz metni",
    "summary": "Özet bilgiler"
}}

Kod:
"""
            
            response = self.model.generate_content(prompt)
            return response.text, None
            
        except Exception as e:
            return None, f"Kod üretme hatası: {e}"
    
    def execute_python_code(self, code, df):
        """Python kodunu güvenli bir şekilde çalıştır"""
        try:
            # Geçici dosya oluştur
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Güvenli çalışma ortamı oluştur
            safe_globals = {
                'df': df,
                'pd': pd,
                'np': np,
                'go': go,
                'px': px,
                'make_subplots': make_subplots,
                'plt': plt,
                'sns': sns,
                'io': io,
                'base64': base64,
                'json': json,
                'datetime': datetime,
                'timedelta': timedelta,
                'TA': TA
            }
            
            # Kodu çalıştır
            exec(code, safe_globals)
            
            # Sonuçları al
            result = safe_globals.get('result', {})
            
            # Geçici dosyayı sil
            os.unlink(temp_file)
            
            return result, None
            
        except Exception as e:
            return None, f"Kod çalıştırma hatası: {e}"
    
    def create_default_charts(self, df):
        """Varsayılan teknik analiz grafikleri oluştur"""
        try:
            charts = []
            
            # 1. Mum grafiği ve SMA'lar
            fig1 = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                subplot_titles=('Fiyat Grafiği ve Hareketli Ortalamalar', 'Hacim'),
                row_width=[0.7, 0.3]
            )
            
            # Mum grafiği
            fig1.add_trace(go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='KCHOL',
                increasing_line_color='#00ff88',
                decreasing_line_color='#ff4444'
            ), row=1, col=1)
            
            # SMA'lar
            fig1.add_trace(go.Scatter(
                x=df.index, y=df['SMA20'],
                mode='lines', name='SMA 20',
                line=dict(color='orange', width=1)
            ), row=1, col=1)
            
            fig1.add_trace(go.Scatter(
                x=df.index, y=df['SMA50'],
                mode='lines', name='SMA 50',
                line=dict(color='blue', width=1)
            ), row=1, col=1)
            
            fig1.add_trace(go.Scatter(
                x=df.index, y=df['SMA200'],
                mode='lines', name='SMA 200',
                line=dict(color='red', width=1)
            ), row=1, col=1)
            
            # Hacim
            fig1.add_trace(go.Bar(
                x=df.index, y=df['volume'],
                name='Hacim',
                marker_color='rgba(0,0,255,0.3)'
            ), row=2, col=1)
            
            fig1.update_layout(
                title='KCHOL Teknik Analiz - Fiyat ve Hacim',
                xaxis_rangeslider_visible=False,
                height=600,
                template='plotly_dark'
            )
            
            # Grafiği base64'e çevir
            img_bytes = fig1.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode()
            
            charts.append({
                "title": "Fiyat Grafiği ve Hareketli Ortalamalar",
                "type": "candlestick",
                "data": img_base64
            })
            
            # 2. RSI Grafiği
            fig2 = go.Figure()
            
            fig2.add_trace(go.Scatter(
                x=df.index, y=df['RSI'],
                mode='lines', name='RSI',
                line=dict(color='purple', width=2)
            ))
            
            fig2.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Aşırı Alım")
            fig2.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Aşırı Satım")
            fig2.add_hline(y=50, line_dash="dot", line_color="gray", annotation_text="Nötr")
            
            fig2.update_layout(
                title='RSI (Relative Strength Index)',
                xaxis_title='Tarih',
                yaxis_title='RSI',
                height=400,
                template='plotly_dark'
            )
            
            img_bytes = fig2.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode()
            
            charts.append({
                "title": "RSI Analizi",
                "type": "line",
                "data": img_base64
            })
            
            # 3. MACD Grafiği
            fig3 = go.Figure()
            
            fig3.add_trace(go.Scatter(
                x=df.index, y=df['MACD'],
                mode='lines', name='MACD',
                line=dict(color='blue', width=2)
            ))
            
            fig3.add_trace(go.Scatter(
                x=df.index, y=df['MACD_Signal'],
                mode='lines', name='Sinyal',
                line=dict(color='red', width=2)
            ))
            
            fig3.add_trace(go.Bar(
                x=df.index, y=df['MACD'] - df['MACD_Signal'],
                name='Histogram',
                marker_color='rgba(0,255,0,0.5)'
            ))
            
            fig3.update_layout(
                title='MACD (Moving Average Convergence Divergence)',
                xaxis_title='Tarih',
                yaxis_title='MACD',
                height=400,
                template='plotly_dark'
            )
            
            img_bytes = fig3.to_image(format="png")
            img_base64 = base64.b64encode(img_bytes).decode()
            
            charts.append({
                "title": "MACD Analizi",
                "type": "line",
                "data": img_base64
            })
            
            return charts
            
        except Exception as e:
            print(f"Varsayılan grafik oluşturma hatası: {e}")
            return []
    
    def analyze_technical_indicators(self, df):
        """Teknik indikatörleri analiz et"""
        try:
            current_price = df['close'].iloc[-1]
            prev_price = df['close'].iloc[-2]
            
            # RSI analizi
            current_rsi = df['RSI'].iloc[-1]
            rsi_signal = "Aşırı alım bölgesinde" if current_rsi > 70 else "Aşırı satım bölgesinde" if current_rsi < 30 else "Nötr bölgede"
            
            # MACD analizi
            current_macd = df['MACD'].iloc[-1]
            current_signal = df['MACD_Signal'].iloc[-1]
            macd_signal = "Pozitif" if current_macd > current_signal else "Negatif"
            
            # SMA analizi
            sma20 = df['SMA20'].iloc[-1]
            sma50 = df['SMA50'].iloc[-1]
            sma200 = df['SMA200'].iloc[-1]
            
            sma_signal = ""
            if current_price > sma20 > sma50 > sma200:
                sma_signal = "Güçlü yükseliş trendi"
            elif current_price < sma20 < sma50 < sma200:
                sma_signal = "Güçlü düşüş trendi"
            elif current_price > sma20 and sma20 > sma50:
                sma_signal = "Orta vadeli yükseliş trendi"
            elif current_price < sma20 and sma20 < sma50:
                sma_signal = "Orta vadeli düşüş trendi"
            else:
                sma_signal = "Kararsız trend"
            
            analysis = f"""
**Teknik Analiz Özeti:**

💰 **Mevcut Fiyat:** {current_price:.2f} TL
📈 **Günlük Değişim:** {((current_price - prev_price) / prev_price * 100):+.2f}%

📊 **RSI ({current_rsi:.1f}):** {rsi_signal}
📈 **MACD:** {macd_signal} sinyali
📉 **Trend:** {sma_signal}

**Öneriler:**
- RSI {current_rsi:.1f} seviyesinde {'aşırı alım' if current_rsi > 70 else 'aşırı satım' if current_rsi < 30 else 'nötr'} bölgesinde
- MACD {'pozitif' if current_macd > current_signal else 'negatif'} sinyal veriyor
- {sma_signal}
"""
            
            return analysis
            
        except Exception as e:
            return f"Analiz hatası: {e}"
    
    def process_technical_analysis_request(self, user_request):
        """Teknik analiz isteğini işle"""
        try:
            # Hisse verisi al
            df = self.get_stock_data()
            if df is None:
                return {
                    "error": "Hisse verisi alınamadı",
                    "charts": [],
                    "analysis": "",
                    "summary": ""
                }
            
            # Kullanıcı özel istek yapmışsa
            if any(word in user_request.lower() for word in ['grafik', 'chart', 'analiz', 'hesapla', 'göster']):
                # Gemini ile kod üret
                code, error = self.generate_python_code(user_request, df)
                if error:
                    return {
                        "error": error,
                        "charts": [],
                        "analysis": "",
                        "summary": ""
                    }
                
                # Kodu çalıştır
                result, error = self.execute_python_code(code, df)
                if error:
                    return {
                        "error": error,
                        "charts": [],
                        "analysis": "",
                        "summary": ""
                    }
                
                return result
            
            # Varsayılan teknik analiz
            charts = self.create_default_charts(df)
            analysis = self.analyze_technical_indicators(df)
            
            return {
                "charts": charts,
                "analysis": analysis,
                "summary": f"KCHOL hisse senedi teknik analizi tamamlandı. {len(charts)} grafik oluşturuldu.",
                "error": None
            }
            
        except Exception as e:
            return {
                "error": f"Teknik analiz hatası: {e}",
                "charts": [],
                "analysis": "",
                "summary": ""
            } 