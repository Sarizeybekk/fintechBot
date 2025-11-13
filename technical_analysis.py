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
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    print(f" Gemini API anahtarı yüklendi: {GOOGLE_API_KEY[:10]}...")
else:
    print("  Gemini API anahtarı bulunamadı. .env dosyasında GOOGLE_API_KEY veya GEMINI_API_KEY tanımlayın.")

class TechnicalAnalysisEngine:
    def __init__(self):
        self.model = None
        if GOOGLE_API_KEY:
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
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
            
            # Sütun isimlerini düzenleme - MultiIndex kontrolü
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
            
            # Teknik indikatörler - sütun isimlerini küçük harfe çevir
            df.columns = [col.lower() for col in df.columns]
            
            # Teknik indikatörler
            df['SMA20'] = TA.SMA(df, 20)
            df['SMA50'] = TA.SMA(df, 50)
            df['SMA200'] = TA.SMA(df, 200)
            df['RSI'] = TA.RSI(df)
            
            # MACD hesaplama
            try:
                macd_data = TA.MACD(df)
                df['MACD'] = macd_data['MACD']
                # MACD signal hesapla (9 günlük EMA)
                df['MACD_Signal'] = df['MACD'].rolling(window=9).mean()
            except Exception as e:
                print(f"MACD hesaplama hatası: {e}")
                # Basit MACD hesaplama
                ema12 = df['close'].ewm(span=12).mean()
                ema26 = df['close'].ewm(span=26).mean()
                df['MACD'] = ema12 - ema26
                df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            
            # Bollinger Bands hesaplama
            bb_data = TA.BBANDS(df)
            df['BB_Upper'] = bb_data['BB_UPPER']
            df['BB_Lower'] = bb_data['BB_LOWER']
            df['BB_Middle'] = bb_data['BB_MIDDLE']
            
            df['ATR'] = TA.ATR(df)
            df['Williams'] = TA.WILLIAMS(df)
            
            # NaN değerleri temizleme - sadece temel sütunlarda
            basic_columns = ['close', 'high', 'low', 'open', 'volume']
            df_clean = df[basic_columns].dropna()
            
            # Teknik indikatörleri sadece mevcut olanlarla ekle
            if 'SMA20' in df.columns:
                df_clean['SMA20'] = df['SMA20']
            if 'SMA50' in df.columns:
                df_clean['SMA50'] = df['SMA50']
            if 'SMA200' in df.columns:
                df_clean['SMA200'] = df['SMA200']
            if 'RSI' in df.columns:
                df_clean['RSI'] = df['RSI']
            if 'MACD' in df.columns:
                df_clean['MACD'] = df['MACD']
            if 'MACD_Signal' in df.columns:
                df_clean['MACD_Signal'] = df['MACD_Signal']
            if 'BB_Upper' in df.columns:
                df_clean['BB_Upper'] = df['BB_Upper']
            if 'BB_Lower' in df.columns:
                df_clean['BB_Lower'] = df['BB_Lower']
            if 'BB_Middle' in df.columns:
                df_clean['BB_Middle'] = df['BB_Middle']
            if 'ATR' in df.columns:
                df_clean['ATR'] = df['ATR']
            if 'Williams' in df.columns:
                df_clean['Williams'] = df['Williams']
            
            return df_clean
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
            
            # 1. Mum grafiği ve SMA'lar - Sadece Matplotlib kullan
            
            # Grafiği HTML formatında kaydet
            try:
                # Matplotlib ile grafik oluştur
                import matplotlib.pyplot as plt
                import matplotlib.dates as mdates
                import base64
                import io
                
                # Grafik boyutunu ayarla
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
                
                # Mum grafiği
                ax1.plot(df.index, df['close'], color='white', linewidth=1, alpha=0.7)
                ax1.plot(df.index, df['SMA20'], color='orange', linewidth=1, label='SMA 20')
                ax1.plot(df.index, df['SMA50'], color='blue', linewidth=1, label='SMA 50')
                ax1.plot(df.index, df['SMA200'], color='red', linewidth=1, label='SMA 200')
                
                ax1.set_title('KCHOL Teknik Analiz - Fiyat ve Hareketli Ortalamalar', color='white', fontsize=14)
                ax1.set_ylabel('Fiyat (TL)', color='white')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                ax1.set_facecolor('#1e293b')
                fig.patch.set_facecolor('#1e293b')
                
                # Hacim grafiği
                ax2.bar(df.index, df['volume'], color='blue', alpha=0.3)
                ax2.set_ylabel('Hacim', color='white')
                ax2.set_xlabel('Tarih', color='white')
                ax2.grid(True, alpha=0.3)
                ax2.set_facecolor('#1e293b')
                
                # Tarih formatını ayarla
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                ax2.xaxis.set_major_locator(mdates.DayLocator(interval=7))
                plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
                
                # Grafik renklerini ayarla
                for ax in [ax1, ax2]:
                    ax.tick_params(colors='white')
                    ax.spines['bottom'].set_color('white')
                    ax.spines['top'].set_color('white')
                    ax.spines['left'].set_color('white')
                    ax.spines['right'].set_color('white')
                
                # Grafiği base64'e çevir
                buffer = io.BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='#1e293b')
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
                
                # HTML img tag'i oluştur
                img_html = f'<img src="data:image/png;base64,{img_base64}" alt="Fiyat Grafiği" style="width:100%; height:auto; border-radius:8px;">'
                img_base64 = img_html
                
            except Exception as e:
                print(f"Matplotlib grafik hatası: {e}")
                img_base64 = "<div style='color:red; padding:20px; text-align:center;'>Grafik yüklenemedi</div>"
            
            charts.append({
                "title": "Fiyat Grafiği ve Hareketli Ortalamalar",
                "type": "candlestick",
                "data": img_base64
            })
            
            # 2. RSI Grafiği - Sadece Matplotlib kullan
            
            try:
                # Matplotlib ile RSI grafiği oluştur
                import matplotlib.pyplot as plt
                import matplotlib.dates as mdates
                import base64
                import io
                
                # Grafik oluştur
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # RSI çizgisi
                ax.plot(df.index, df['RSI'], color='purple', linewidth=2, label='RSI')
                
                # Seviye çizgileri
                ax.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Aşırı Alım (70)')
                ax.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Aşırı Satım (30)')
                ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5, label='Nötr (50)')
                
                ax.set_title('RSI (Relative Strength Index)', color='white', fontsize=14)
                ax.set_ylabel('RSI', color='white')
                ax.set_xlabel('Tarih', color='white')
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_facecolor('#1e293b')
                fig.patch.set_facecolor('#1e293b')
                
                # Tarih formatını ayarla
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                
                # Grafik renklerini ayarla
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['left'].set_color('white')
                ax.spines['right'].set_color('white')
                
                # Grafiği base64'e çevir
                buffer = io.BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='#1e293b')
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
                
                # HTML img tag'i oluştur
                img_html = f'<img src="data:image/png;base64,{img_base64}" alt="RSI Grafiği" style="width:100%; height:auto; border-radius:8px;">'
                img_base64 = img_html
                
            except Exception as e:
                print(f"RSI Matplotlib grafik hatası: {e}")
                img_base64 = "<div style='color:red; padding:20px; text-align:center;'>RSI Grafik yüklenemedi</div>"
            
            charts.append({
                "title": "RSI Analizi",
                "type": "line",
                "data": img_base64
            })
            
            # 3. MACD Grafiği - Sadece Matplotlib kullan
            
            try:
                # Matplotlib ile MACD grafiği oluştur
                import matplotlib.pyplot as plt
                import matplotlib.dates as mdates
                import base64
                import io
                
                # Grafik oluştur
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})
                
                # MACD çizgileri
                ax1.plot(df.index, df['MACD'], color='blue', linewidth=2, label='MACD')
                ax1.plot(df.index, df['MACD_Signal'], color='red', linewidth=2, label='Sinyal')
                
                ax1.set_title('MACD (Moving Average Convergence Divergence)', color='white', fontsize=14)
                ax1.set_ylabel('MACD', color='white')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
                ax1.set_facecolor('#1e293b')
                
                # Histogram
                histogram = df['MACD'] - df['MACD_Signal']
                colors = ['green' if x >= 0 else 'red' for x in histogram]
                ax2.bar(df.index, histogram, color=colors, alpha=0.7, label='Histogram')
                ax2.set_ylabel('Histogram', color='white')
                ax2.set_xlabel('Tarih', color='white')
                ax2.grid(True, alpha=0.3)
                ax2.set_facecolor('#1e293b')
                
                # Tarih formatını ayarla
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                ax2.xaxis.set_major_locator(mdates.DayLocator(interval=7))
                plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
                
                # Grafik renklerini ayarla
                for ax in [ax1, ax2]:
                    ax.tick_params(colors='white')
                    ax.spines['bottom'].set_color('white')
                    ax.spines['top'].set_color('white')
                    ax.spines['left'].set_color('white')
                    ax.spines['right'].set_color('white')
                
                fig.patch.set_facecolor('#1e293b')
                
                # Grafiği base64'e çevir
                buffer = io.BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='#1e293b')
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
                
                # HTML img tag'i oluştur
                img_html = f'<img src="data:image/png;base64,{img_base64}" alt="MACD Grafiği" style="width:100%; height:auto; border-radius:8px;">'
                img_base64 = img_html
                
            except Exception as e:
                print(f"MACD Matplotlib grafik hatası: {e}")
                img_base64 = "<div style='color:red; padding:20px; text-align:center;'>MACD Grafik yüklenemedi</div>"
            
            charts.append({
                "title": "MACD Analizi",
                "type": "line",
                "data": img_base64
            })
            
            # 4. Bollinger Bands Grafiği - Sadece Matplotlib kullan
            
            try:
                # Matplotlib ile Bollinger Bands grafiği oluştur
                import matplotlib.pyplot as plt
                import matplotlib.dates as mdates
                import base64
                import io
                
                # Grafik oluştur
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Fiyat ve bantlar
                ax.plot(df.index, df['close'], color='white', linewidth=2, label='Fiyat')
                ax.plot(df.index, df['BB_Upper'], color='red', linewidth=1, linestyle='--', label='Üst Bant')
                ax.plot(df.index, df['BB_Lower'], color='green', linewidth=1, linestyle='--', label='Alt Bant')
                ax.plot(df.index, df['BB_Middle'], color='blue', linewidth=1, label='Orta Bant')
                
                # Bantları doldur
                ax.fill_between(df.index, df['BB_Upper'], df['BB_Lower'], alpha=0.1, color='gray')
                
                ax.set_title('Bollinger Bands', color='white', fontsize=14)
                ax.set_ylabel('Fiyat (TL)', color='white')
                ax.set_xlabel('Tarih', color='white')
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_facecolor('#1e293b')
                fig.patch.set_facecolor('#1e293b')
                
                # Tarih formatını ayarla
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                
                # Grafik renklerini ayarla
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['left'].set_color('white')
                ax.spines['right'].set_color('white')
                
                # Grafiği base64'e çevir
                buffer = io.BytesIO()
                plt.tight_layout()
                plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='#1e293b')
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                plt.close()
                
                # HTML img tag'i oluştur
                img_html = f'<img src="data:image/png;base64,{img_base64}" alt="Bollinger Bands Grafiği" style="width:100%; height:auto; border-radius:8px;">'
                img_base64 = img_html
                
            except Exception as e:
                print(f"Bollinger Bands Matplotlib grafik hatası: {e}")
                img_base64 = "<div style='color:red; padding:20px; text-align:center;'>Bollinger Bands Grafik yüklenemedi</div>"
            
            charts.append({
                "title": "Bollinger Bands Analizi",
                "type": "line",
                "data": img_base64
            })
            
            return charts
            
        except Exception as e:
            print(f"Varsayılan grafik oluşturma hatası: {e}")
            return []
    
    def create_rsi_chart(self, df):
        """Sadece RSI grafiği oluştur"""
        try:
            charts = []
            
            # Matplotlib ile RSI grafiği oluştur
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            import base64
            import io
            
            # Grafik oluştur
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # RSI çizgisi
            ax.plot(df.index, df['RSI'], color='purple', linewidth=2, label='RSI')
            
            # Seviye çizgileri
            ax.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Aşırı Alım (70)')
            ax.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Aşırı Satım (30)')
            ax.axhline(y=50, color='gray', linestyle=':', alpha=0.5, label='Nötr (50)')
            
            ax.set_title('RSI (Relative Strength Index)', color='white', fontsize=14)
            ax.set_ylabel('RSI', color='white')
            ax.set_xlabel('Tarih', color='white')
            ax.legend()
            ax.grid(True, alpha=0.3)
            ax.set_facecolor('#1e293b')
            fig.patch.set_facecolor('#1e293b')
            
            # Tarih formatını ayarla
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=7))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Grafik renklerini ayarla
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['right'].set_color('white')
            
            # Grafiği base64'e çevir
            buffer = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='#1e293b')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
            # HTML img tag'i oluştur
            img_html = f'<img src="data:image/png;base64,{img_base64}" alt="RSI Grafiği" style="width:100%; height:auto; border-radius:8px;">'
            
            charts.append({
                "title": "RSI Analizi",
                "type": "line",
                "data": img_html
            })
            
            return charts
            
        except Exception as e:
            print(f"RSI grafik oluşturma hatası: {e}")
            return []
    
    def create_macd_chart(self, df):
        """Sadece MACD grafiği oluştur"""
        try:
            charts = []
            
            # Matplotlib ile MACD grafiği oluştur
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            import base64
            import io
            
            # Grafik oluştur
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})
            
            # MACD çizgileri
            ax1.plot(df.index, df['MACD'], color='blue', linewidth=2, label='MACD')
            ax1.plot(df.index, df['MACD_Signal'], color='red', linewidth=2, label='Sinyal')
            
            ax1.set_title('MACD (Moving Average Convergence Divergence)', color='white', fontsize=14)
            ax1.set_ylabel('MACD', color='white')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.set_facecolor('#1e293b')
            
            # Histogram
            histogram = df['MACD'] - df['MACD_Signal']
            colors = ['green' if x >= 0 else 'red' for x in histogram]
            ax2.bar(df.index, histogram, color=colors, alpha=0.7, label='Histogram')
            ax2.set_ylabel('Histogram', color='white')
            ax2.set_xlabel('Tarih', color='white')
            ax2.grid(True, alpha=0.3)
            ax2.set_facecolor('#1e293b')
            
            # Tarih formatını ayarla
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax2.xaxis.set_major_locator(mdates.DayLocator(interval=7))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            # Grafik renklerini ayarla
            for ax in [ax1, ax2]:
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['left'].set_color('white')
                ax.spines['right'].set_color('white')
            
            fig.patch.set_facecolor('#1e293b')
            
            # Grafiği base64'e çevir
            buffer = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', facecolor='#1e293b')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
            # HTML img tag'i oluştur
            img_html = f'<img src="data:image/png;base64,{img_base64}" alt="MACD Grafiği" style="width:100%; height:auto; border-radius:8px;">'
            
            charts.append({
                "title": "MACD Analizi",
                "type": "line",
                "data": img_html
            })
            
            return charts
            
        except Exception as e:
            print(f"MACD grafik oluşturma hatası: {e}")
            return []
    
    def create_bollinger_chart(self, df):
        """Sadece Bollinger Bands grafiği oluştur"""
        try:
            charts = []
            
            # Bollinger Bands Grafiği
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df.index, y=df['close'],
                mode='lines', name='Fiyat',
                line=dict(color='white', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=df.index, y=df['BB_Upper'],
                mode='lines', name='Üst Bant',
                line=dict(color='red', width=1, dash='dash')
            ))
            
            fig.add_trace(go.Scatter(
                x=df.index, y=df['BB_Lower'],
                mode='lines', name='Alt Bant',
                line=dict(color='green', width=1, dash='dash'),
                fill='tonexty'
            ))
            
            fig.add_trace(go.Scatter(
                x=df.index, y=df['BB_Middle'],
                mode='lines', name='Orta Bant',
                line=dict(color='blue', width=1)
            ))
            
            fig.update_layout(
                title='Bollinger Bands',
                xaxis_title='Tarih',
                yaxis_title='Fiyat (TL)',
                height=400,
                template='plotly_dark'
            )
            
            try:
                # Matplotlib ile Bollinger Bands grafiği oluştur
                import matplotlib.pyplot as plt
                import matplotlib.dates as mdates
                import base64
                import io
                
                # Grafik oluştur
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Fiyat ve bantlar
                ax.plot(df.index, df['close'], color='white', linewidth=2, label='Fiyat')
                ax.plot(df.index, df['BB_Upper'], color='red', linewidth=1, linestyle='--', label='Üst Bant')
                ax.plot(df.index, df['BB_Lower'], color='green', linewidth=1, linestyle='--', label='Alt Bant')
                ax.plot(df.index, df['BB_Middle'], color='blue', linewidth=1, label='Orta Bant')
                
                # Alt bantları doldur
                ax.fill_between(df.index, df['BB_Lower'], df['BB_Upper'], alpha=0.3, color='gray')
                
                # Grafik ayarları
                ax.set_title('Bollinger Bands', color='white', fontsize=14, fontweight='bold')
                ax.set_xlabel('Tarih', color='white', fontsize=12)
                ax.set_ylabel('Fiyat', color='white', fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.legend(loc='upper left')
                
                # Tarih formatı
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                
                # Arka plan rengi
                ax.set_facecolor('#1e1e1e')
                fig.patch.set_facecolor('#1e1e1e')
                
                # Eksen renkleri
                ax.tick_params(colors='white')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_color('white')
                ax.spines['left'].set_color('white')
                
                # Grafiği base64'e çevir
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                buffer.close()
                plt.close()
                
                img_base64 = f"<img src=\"data:image/png;base64,{img_base64}\" alt=\"Bollinger Bands Grafiği\" style=\"width:100%; height:auto; border-radius:8px;\">"
                
            except Exception as e:
                print(f"Bollinger Bands grafik oluşturma hatası: {e}")
                img_base64 = "<div style='color:red; padding:20px; text-align:center;'>Bollinger Bands Grafik yüklenemedi</div>"
            
            charts.append({
                "title": "Bollinger Bands Analizi",
                "type": "line",
                "data": img_base64
            })
            
            return charts
            
        except Exception as e:
            print(f"Bollinger Bands grafik oluşturma hatası: {e}")
            return []
    
    def create_sma_chart(self, df):
        """Sadece SMA grafiği oluştur"""
        try:
            charts = []
            
            # SMA Grafiği
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df.index, y=df['close'],
                mode='lines', name='Fiyat',
                line=dict(color='white', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA20'],
                mode='lines', name='SMA 20',
                line=dict(color='orange', width=1)
            ))
            
            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA50'],
                mode='lines', name='SMA 50',
                line=dict(color='blue', width=1)
            ))
            
            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA200'],
                mode='lines', name='SMA 200',
                line=dict(color='red', width=1)
            ))
            
            fig.update_layout(
                title='Hareketli Ortalamalar',
                xaxis_title='Tarih',
                yaxis_title='Fiyat (TL)',
                height=400,
                template='plotly_dark'
            )
            
            try:
                # Matplotlib ile SMA grafiği oluştur
                import matplotlib.pyplot as plt
                import matplotlib.dates as mdates
                import base64
                import io
                
                # Grafik oluştur
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Fiyat ve hareketli ortalamalar
                ax.plot(df.index, df['close'], color='white', linewidth=2, label='Fiyat')
                ax.plot(df.index, df['SMA20'], color='orange', linewidth=1, label='SMA 20')
                ax.plot(df.index, df['SMA50'], color='blue', linewidth=1, label='SMA 50')
                ax.plot(df.index, df['SMA200'], color='red', linewidth=1, label='SMA 200')
                
                # Grafik ayarları
                ax.set_title('Hareketli Ortalamalar', color='white', fontsize=14, fontweight='bold')
                ax.set_xlabel('Tarih', color='white', fontsize=12)
                ax.set_ylabel('Fiyat', color='white', fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.legend(loc='upper left')
                
                # Tarih formatı
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                
                # Arka plan rengi
                ax.set_facecolor('#1e1e1e')
                fig.patch.set_facecolor('#1e1e1e')
                
                # Eksen renkleri
                ax.tick_params(colors='white')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_color('white')
                ax.spines['left'].set_color('white')
                
                # Grafiği base64'e çevir
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                buffer.close()
                plt.close()
                
                img_base64 = f"<img src=\"data:image/png;base64,{img_base64}\" alt=\"SMA Grafiği\" style=\"width:100%; height:auto; border-radius:8px;\">"
                
            except Exception as e:
                print(f"SMA grafik oluşturma hatası: {e}")
                img_base64 = "<div style='color:red; padding:20px; text-align:center;'>SMA Grafik yüklenemedi</div>"
            
            charts.append({
                "title": "Hareketli Ortalamalar",
                "type": "line",
                "data": img_base64
            })
            
            return charts
            
        except Exception as e:
            print(f"SMA grafik oluşturma hatası: {e}")
            return []
    
    def create_volume_chart(self, df):
        """Sadece hacim grafiği oluştur"""
        try:
            charts = []
            
            # Hacim Grafiği - Sadece Matplotlib kullan
            
            try:
                # Matplotlib ile hacim grafiği oluştur
                import matplotlib.dates as mdates
                import base64
                import io
                
                # Grafik oluştur
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Hacim grafiği
                ax.bar(df.index, df['volume'], color='blue', alpha=0.7, label='Hacim')
                
                # Grafik ayarları
                ax.set_title('İşlem Hacmi', color='white', fontsize=14, fontweight='bold')
                ax.set_xlabel('Tarih', color='white', fontsize=12)
                ax.set_ylabel('Hacim', color='white', fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.legend(loc='upper left')
                
                # Tarih formatı
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                
                # Arka plan rengi
                ax.set_facecolor('#1e1e1e')
                fig.patch.set_facecolor('#1e1e1e')
                
                # Eksen renkleri
                ax.tick_params(colors='white')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_color('white')
                ax.spines['left'].set_color('white')
                
                # Grafiği base64'e çevir
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                buffer.close()
                plt.close()
                
                img_base64 = f"<img src=\"data:image/png;base64,{img_base64}\" alt=\"Hacim Grafiği\" style=\"width:100%; height:auto; border-radius:8px;\">"
                
            except Exception as e:
                print(f"Hacim Matplotlib grafik hatası: {e}")
                img_base64 = "<div style='color:red; padding:20px; text-align:center;'>Hacim Grafik yüklenemedi</div>"
            
            charts.append({
                "title": "İşlem Hacmi",
                "type": "bar",
                "data": img_base64
            })
            
            return charts
            
        except Exception as e:
            print(f"Hacim grafik oluşturma hatası: {e}")
            return []
    
    def create_price_chart(self, df):
        """Sadece fiyat grafiği oluştur"""
        try:
            charts = []
            
            try:
                # Matplotlib ile fiyat grafiği oluştur
                import matplotlib.dates as mdates
                import base64
                import io
                
                # Grafik oluştur
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Fiyat grafiği (çizgi olarak)
                ax.plot(df.index, df['close'], color='white', linewidth=2, label='Fiyat')
                
                # Grafik ayarları
                ax.set_title('KCHOL Fiyat Grafiği', color='white', fontsize=14, fontweight='bold')
                ax.set_xlabel('Tarih', color='white', fontsize=12)
                ax.set_ylabel('Fiyat (TL)', color='white', fontsize=12)
                ax.grid(True, alpha=0.3)
                ax.legend(loc='upper left')
                
                # Tarih formatı
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
                
                # Arka plan rengi
                ax.set_facecolor('#1e1e1e')
                fig.patch.set_facecolor('#1e1e1e')
                
                # Eksen renkleri
                ax.tick_params(colors='white')
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_color('white')
                ax.spines['left'].set_color('white')
                
                # Grafiği base64'e çevir
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
                buffer.seek(0)
                img_base64 = base64.b64encode(buffer.getvalue()).decode()
                buffer.close()
                plt.close()
                
                img_base64 = f"<img src=\"data:image/png;base64,{img_base64}\" alt=\"Fiyat Grafiği\" style=\"width:100%; height:auto; border-radius:8px;\">"
                
            except Exception as e:
                print(f"Fiyat Matplotlib grafik hatası: {e}")
                img_base64 = "<div style='color:red; padding:20px; text-align:center;'>Fiyat Grafik yüklenemedi</div>"
            
            charts.append({
                "title": "KCHOL Fiyat Grafiği",
                "type": "line",
                "data": img_base64
            })
            
            return charts
            
        except Exception as e:
            print(f"Fiyat grafik oluşturma hatası: {e}")
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
            
            # Bollinger Bands analizi
            bb_upper = df['BB_Upper'].iloc[-1]
            bb_lower = df['BB_Lower'].iloc[-1]
            bb_middle = df['BB_Middle'].iloc[-1]
            
            bb_signal = ""
            if current_price > bb_upper:
                bb_signal = "Üst banda dokundu - Aşırı alım sinyali"
            elif current_price < bb_lower:
                bb_signal = "Alt banda dokundu - Aşırı satım sinyali"
            else:
                bb_signal = "Bantlar arasında - Normal seviye"
            
            # Williams %R analizi
            williams_r = df['Williams'].iloc[-1]
            williams_signal = "Aşırı alım" if williams_r > -20 else "Aşırı satım" if williams_r < -80 else "Nötr"
            
            # ATR analizi (Volatilite)
            atr = df['ATR'].iloc[-1]
            avg_atr = df['ATR'].mean()
            volatility_signal = "Yüksek volatilite" if atr > avg_atr * 1.5 else "Düşük volatilite" if atr < avg_atr * 0.5 else "Normal volatilite"
            
            # Yatırım stratejisi önerileri
            strategy_recommendations = self.generate_investment_strategy(df, current_rsi, macd_signal, sma_signal, bb_signal, volatility_signal)
            
            analysis = f"""
**KCHOL Teknik Analiz Raporu**

💰 **Fiyat Bilgileri:**
• Mevcut Fiyat: {current_price:.2f} TL
• Günlük Değişim: {((current_price - prev_price) / prev_price * 100):+.2f}%
• Önceki Kapanış: {prev_price:.2f} TL

📊 **Teknik İndikatörler:**

**RSI ({current_rsi:.1f}):** {rsi_signal}
**MACD:** {macd_signal} sinyali (MACD: {current_macd:.4f}, Sinyal: {current_signal:.4f})
**Williams %R ({williams_r:.1f}):** {williams_signal}
**ATR ({atr:.2f}):** {volatility_signal}

**Hareketli Ortalamalar:**
• SMA 20: {sma20:.2f} TL
• SMA 50: {sma50:.2f} TL  
• SMA 200: {sma200:.2f} TL

**Bollinger Bands:**
• Üst Bant: {bb_upper:.2f} TL
• Orta Bant: {bb_middle:.2f} TL
• Alt Bant: {bb_lower:.2f} TL
• Durum: {bb_signal}

📈 **Trend Analizi:**
{sma_signal}

🎯 **Teknik Öneriler:**
• RSI {current_rsi:.1f} seviyesinde {'aşırı alım' if current_rsi > 70 else 'aşırı satım' if current_rsi < 30 else 'nötr'} bölgesinde
• MACD {'pozitif' if current_macd > current_signal else 'negatif'} sinyal veriyor
• Williams %R {williams_signal} bölgesinde
• Volatilite {volatility_signal.lower()} seviyesinde
• {sma_signal}

---

**YATIRIM STRATEJİSİ ÖNERİLERİ**

{strategy_recommendations}
"""
            
            return analysis
            
        except Exception as e:
            return f"Analiz hatası: {e}"
    
    def generate_investment_strategy(self, df, current_rsi, macd_signal, sma_signal, bb_signal, volatility_signal):
        """Teknik analiz sonuçlarına göre yatırım stratejisi üret"""
        try:
            current_price = df['close'].iloc[-1]
            sma20 = df['SMA20'].iloc[-1]
            sma50 = df['SMA50'].iloc[-1]
            sma200 = df['SMA200'].iloc[-1]
            
            # Risk seviyesi belirleme
            risk_level = "Yüksek"
            if "Normal volatilite" in volatility_signal:
                risk_level = "Orta"
            elif "Düşük volatilite" in volatility_signal:
                risk_level = "Düşük"
            
            # Trend yönü belirleme
            trend_direction = "Yükseliş"
            if "düşüş" in sma_signal.lower():
                trend_direction = "Düşüş"
            elif "kararsız" in sma_signal.lower():
                trend_direction = "Kararsız"
            
            # Kısa vadeli strateji
            short_term_strategy = ""
            if current_rsi > 70:
                short_term_strategy = "Aşırı alım bölgesinde - Kısa vadede düzeltme beklenebilir. Mevcut pozisyonları koruyun, yeni alım yapmayın."
            elif current_rsi < 30:
                short_term_strategy = "Aşırı satım bölgesinde - Kısa vadede toparlanma beklenebilir. Dikkatli alım fırsatı olabilir."
            else:
                if "pozitif" in macd_signal.lower():
                    short_term_strategy = "Momentum pozitif - Kısa vadeli alım fırsatları değerlendirilebilir."
                else:
                    short_term_strategy = "Momentum negatif - Kısa vadeli satış baskısı olabilir."
            
            # Orta vadeli strateji
            medium_term_strategy = ""
            if "güçlü yükseliş" in sma_signal.lower():
                medium_term_strategy = "Güçlü yükseliş trendi - Orta vadeli pozisyon alımı uygun olabilir."
            elif "güçlü düşüş" in sma_signal.lower():
                medium_term_strategy = "Güçlü düşüş trendi - Orta vadeli pozisyon alımı için trend dönüşü bekleyin."
            else:
                medium_term_strategy = "Kararsız trend - Orta vadeli pozisyon için daha net sinyaller bekleyin."
            
            # Risk yönetimi önerileri
            risk_management = ""
            if risk_level == "Yüksek":
                risk_management = "Yüksek volatilite - Stop-loss seviyelerini sıkı tutun, pozisyon büyüklüğünü azaltın."
            elif risk_level == "Orta":
                risk_management = "Normal volatilite - Standart risk yönetimi uygulayın."
            else:
                risk_management = "Düşük volatilite - Daha geniş stop-loss seviyeleri kullanabilirsiniz."
            
            # Bollinger Bands stratejisi
            bb_strategy = ""
            if "aşırı alım" in bb_signal.lower():
                bb_strategy = "Bollinger üst bandına dokundu - Kısa vadede düzeltme beklenebilir."
            elif "aşırı satım" in bb_signal.lower():
                bb_strategy = "Bollinger alt bandına dokundu - Kısa vadede toparlanma beklenebilir."
            else:
                bb_strategy = "Bollinger bantları arasında - Normal fiyat hareketi."
            
            strategy = f"""
**Kısa Vadeli Strateji (1-4 hafta):**
{short_term_strategy}

**Orta Vadeli Strateji (1-6 ay):**
{medium_term_strategy}

**Risk Yönetimi:**
• Risk Seviyesi: {risk_level}
• {risk_management}
• Pozisyon büyüklüğünü risk toleransınıza göre ayarlayın
• Farklı zaman dilimlerinde analiz yapın

**Teknik Seviyeler:**
• Destek: {sma50:.2f} TL (SMA 50)
• Direnç: {sma20:.2f} TL (SMA 20)
• Uzun vadeli trend: {sma200:.2f} TL (SMA 200)

**Bollinger Bands Stratejisi:**
{bb_strategy}

**Genel Öneriler:**
• Trend yönü: {trend_direction}
• Volatilite: {volatility_signal}
• Portföy çeşitlendirmesi yapın
• Düzenli olarak analizleri güncelleyin

**Not:** Bu öneriler teknik analiz sonuçlarına dayalıdır. Yatırım kararı vermeden önce profesyonel danışmanlık almanızı öneririm."""
            
            return strategy
            
        except Exception as e:
            return f"Strateji üretme hatası: {e}"
    
    def analyze_rsi(self, df):
        """Sadece RSI analizi"""
        try:
            current_rsi = df['RSI'].iloc[-1]
            prev_rsi = df['RSI'].iloc[-2]
            
            rsi_signal = ""
            if current_rsi > 70:
                rsi_signal = "Aşırı alım bölgesinde - Satış sinyali"
            elif current_rsi < 30:
                rsi_signal = "Aşırı satım bölgesinde - Alış sinyali"
            else:
                rsi_signal = "Nötr bölgede"
            
            rsi_trend = "Yükseliyor" if current_rsi > prev_rsi else "Düşüyor" if current_rsi < prev_rsi else "Sabit"
            
            analysis = f"""
**RSI (Relative Strength Index) Analizi**

📊 **Mevcut RSI:** {current_rsi:.1f}
📈 **Önceki RSI:** {prev_rsi:.1f}
🔄 **Trend:** {rsi_trend}

**Sinyal:** {rsi_signal}

**Yorum:**
• RSI {current_rsi:.1f} seviyesinde
• {'Aşırı alım bölgesinde - Dikkatli olun' if current_rsi > 70 else 'Aşırı satım bölgesinde - Fırsat olabilir' if current_rsi < 30 else 'Nötr bölgede - Trend devam ediyor'}
• {'RSI yükseliyor - Momentum artıyor' if current_rsi > prev_rsi else 'RSI düşüyor - Momentum azalıyor' if current_rsi < prev_rsi else 'RSI sabit - Momentum dengeli'}
"""
            return analysis
            
        except Exception as e:
            return f"RSI analiz hatası: {e}"
    
    def analyze_macd(self, df):
        """Sadece MACD analizi"""
        try:
            current_macd = df['MACD'].iloc[-1]
            current_signal = df['MACD_Signal'].iloc[-1]
            prev_macd = df['MACD'].iloc[-2]
            prev_signal = df['MACD_Signal'].iloc[-2]
            
            macd_signal = "Pozitif" if current_macd > current_signal else "Negatif"
            macd_trend = "Güçleniyor" if current_macd > prev_macd else "Zayıflıyor" if current_macd < prev_macd else "Sabit"
            
            histogram = current_macd - current_signal
            prev_histogram = prev_macd - prev_signal
            histogram_trend = "Artıyor" if histogram > prev_histogram else "Azalıyor" if histogram < prev_histogram else "Sabit"
            
            analysis = f"""
**MACD (Moving Average Convergence Divergence) Analizi**

📊 **MACD:** {current_macd:.4f}
📈 **Sinyal:** {current_signal:.4f}
📊 **Histogram:** {histogram:.4f}

**Sinyal:** {macd_signal}
**Trend:** {macd_trend}
**Histogram Trend:** {histogram_trend}

**Yorum:**
• MACD {'pozitif' if current_macd > current_signal else 'negatif'} sinyal veriyor
• {'MACD güçleniyor - Yükseliş trendi devam ediyor' if current_macd > prev_macd else 'MACD zayıflıyor - Trend değişebilir' if current_macd < prev_macd else 'MACD sabit - Trend dengeli'}
• Histogram {histogram_trend.lower()} - Momentum {'artıyor' if histogram > prev_histogram else 'azalıyor' if histogram < prev_histogram else 'sabit'}
"""
            return analysis
            
        except Exception as e:
            return f"MACD analiz hatası: {e}"
    
    def analyze_bollinger(self, df):
        """Sadece Bollinger Bands analizi"""
        try:
            current_price = df['close'].iloc[-1]
            bb_upper = df['BB_Upper'].iloc[-1]
            bb_lower = df['BB_Lower'].iloc[-1]
            bb_middle = df['BB_Middle'].iloc[-1]
            
            bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) * 100
            
            bb_signal = ""
            if current_price > bb_upper:
                bb_signal = "Üst banda dokundu - Aşırı alım sinyali"
            elif current_price < bb_lower:
                bb_signal = "Alt banda dokundu - Aşırı satım sinyali"
            else:
                bb_signal = "Bantlar arasında - Normal seviye"
            
            bb_width = bb_upper - bb_lower
            avg_bb_width = (df['BB_Upper'] - df['BB_Lower']).mean()
            volatility = "Yüksek" if bb_width > avg_bb_width * 1.2 else "Düşük" if bb_width < avg_bb_width * 0.8 else "Normal"
            
            analysis = f"""
**Bollinger Bands Analizi**

💰 **Mevcut Fiyat:** {current_price:.2f} TL
📊 **Üst Bant:** {bb_upper:.2f} TL
📊 **Alt Bant:** {bb_lower:.2f} TL
📊 **Orta Bant:** {bb_middle:.2f} TL

**Bant Pozisyonu:** %{bb_position:.1f}
**Volatilite:** {volatility}

**Sinyal:** {bb_signal}

**Yorum:**
• Fiyat {'üst banda yakın - Aşırı alım bölgesi' if current_price > bb_upper * 0.95 else 'alt banda yakın - Aşırı satım bölgesi' if current_price < bb_lower * 1.05 else 'bantlar arasında - Normal seviye'}
• Volatilite {volatility.lower()} seviyede
• {'Bantlar genişliyor - Volatilite artıyor' if bb_width > avg_bb_width * 1.2 else 'Bantlar daralıyor - Volatilite azalıyor' if bb_width < avg_bb_width * 0.8 else 'Bantlar normal - Volatilite dengeli'}
"""
            return analysis
            
        except Exception as e:
            return f"Bollinger Bands analiz hatası: {e}"
    
    def analyze_sma(self, df):
        """Sadece SMA analizi"""
        try:
            current_price = df['close'].iloc[-1]
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
**Hareketli Ortalama Analizi**

💰 **Mevcut Fiyat:** {current_price:.2f} TL
📊 **SMA 20:** {sma20:.2f} TL
📊 **SMA 50:** {sma50:.2f} TL
📊 **SMA 200:** {sma200:.2f} TL

**Trend:** {sma_signal}

**Yorum:**
• Fiyat {'SMA 20\'nin üstünde - Kısa vadeli yükseliş' if current_price > sma20 else 'SMA 20\'nin altında - Kısa vadeli düşüş'}
• SMA 20 {'SMA 50\'nin üstünde - Orta vadeli yükseliş' if sma20 > sma50 else 'SMA 50\'nin altında - Orta vadeli düşüş'}
• SMA 50 {'SMA 200\'ün üstünde - Uzun vadeli yükseliş' if sma50 > sma200 else 'SMA 200\'ün altında - Uzun vadeli düşüş'}
• {sma_signal}
"""
            return analysis
            
        except Exception as e:
            return f"SMA analiz hatası: {e}"
    
    def analyze_volume(self, df):
        """Sadece hacim analizi"""
        try:
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].mean()
            volume_ratio = current_volume / avg_volume
            
            volume_signal = ""
            if volume_ratio > 2:
                volume_signal = "Çok yüksek hacim - Güçlü hareket"
            elif volume_ratio > 1.5:
                volume_signal = "Yüksek hacim - Güçlü sinyal"
            elif volume_ratio < 0.5:
                volume_signal = "Düşük hacim - Zayıf sinyal"
            else:
                volume_signal = "Normal hacim"
            
            analysis = f"""
**Hacim Analizi**

📊 **Günlük Hacim:** {current_volume:,.0f}
📊 **Ortalama Hacim:** {avg_volume:,.0f}
📊 **Hacim Oranı:** {volume_ratio:.2f}x

**Sinyal:** {volume_signal}

**Yorum:**
• Hacim {'ortalamanın üstünde - Güçlü hareket' if volume_ratio > 1.2 else 'ortalamanın altında - Zayıf hareket' if volume_ratio < 0.8 else 'normal seviyede'}
• {'Yüksek hacim trendi destekliyor' if volume_ratio > 1.5 else 'Düşük hacim trend zayıf' if volume_ratio < 0.5 else 'Normal hacim trend dengeli'}
• {volume_signal}
"""
            return analysis
            
        except Exception as e:
            return f"Hacim analiz hatası: {e}"
    
    def analyze_price(self, df):
        """Sadece fiyat analizi"""
        try:
            current_price = df['close'].iloc[-1]
            prev_price = df['close'].iloc[-2]
            change = current_price - prev_price
            change_percent = (change / prev_price) * 100
            
            high_52w = df['high'].max()
            low_52w = df['low'].min()
            price_position = (current_price - low_52w) / (high_52w - low_52w) * 100
            
            analysis = f"""
**Fiyat Analizi**

💰 **Mevcut Fiyat:** {current_price:.2f} TL
📈 **Günlük Değişim:** {change:+.2f} TL ({change_percent:+.2f}%)
📊 **52 Hafta En Yüksek:** {high_52w:.2f} TL
📊 **52 Hafta En Düşük:** {low_52w:.2f} TL
📊 **52 Hafta Pozisyonu:** %{price_position:.1f}

**Yorum:**
• Fiyat {'yükseliyor' if change > 0 else 'düşüyor' if change < 0 else 'sabit'}
• {'Güçlü yükseliş' if change_percent > 2 else 'Hafif yükseliş' if change_percent > 0 else 'Hafif düşüş' if change_percent > -2 else 'Güçlü düşüş'}
• 52 hafta aralığının {'üst yarısında' if price_position > 50 else 'alt yarısında'}
• {'Yüksek seviyelerde' if price_position > 80 else 'Düşük seviyelerde' if price_position < 20 else 'Orta seviyelerde'}
"""
            return analysis
            
        except Exception as e:
            return f"Fiyat analiz hatası: {e}"
    
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
            
            # Gemini ile kullanıcı isteğini analiz et
            if self.model:
                try:
                    analysis_result = self.analyze_request_with_gemini(user_request, df)
                    if analysis_result:
                        return analysis_result
                except Exception as e:
                    print(f"Gemini analiz hatası: {e}")
                    # Fallback to rule-based analysis
            
            # Fallback: Rule-based analiz
            return self.rule_based_analysis(user_request, df)
            
        except Exception as e:
            return {
                "error": f"Teknik analiz hatası: {e}",
                "charts": [],
                "analysis": "",
                "summary": ""
            }
    
    def analyze_request_with_gemini(self, user_request, df):
        """Gemini ile kullanıcı isteğini analiz et"""
        try:
            # Mevcut teknik verileri hazırla
            current_price = df['close'].iloc[-1]
            current_rsi = df['RSI'].iloc[-1]
            current_macd = df['MACD'].iloc[-1]
            current_signal = df['MACD_Signal'].iloc[-1]
            sma20 = df['SMA20'].iloc[-1]
            sma50 = df['SMA50'].iloc[-1]
            sma200 = df['SMA200'].iloc[-1]
            bb_upper = df['BB_Upper'].iloc[-1]
            bb_lower = df['BB_Lower'].iloc[-1]
            bb_middle = df['BB_Middle'].iloc[-1]
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].mean()
            
            prompt = f"""
Sen bir finansal analiz uzmanısın. Kullanıcının teknik analiz isteğini anlayıp uygun grafikleri ve analizleri öner.

Kullanıcı isteği: "{user_request}"

Mevcut teknik veriler:
- Fiyat: {current_price:.2f} TL
- RSI: {current_rsi:.1f}
- MACD: {current_macd:.4f}, Sinyal: {current_signal:.4f}
- SMA 20: {sma20:.2f}, SMA 50: {sma50:.2f}, SMA 200: {sma200:.2f}
- Bollinger: Üst {bb_upper:.2f}, Alt {bb_lower:.2f}, Orta {bb_middle:.2f}
- Hacim: {current_volume:,.0f} (Ortalama: {avg_volume:,.0f})

Kullanıcının isteğine göre hangi analizleri yapmam gerekiyor? Aşağıdaki seçeneklerden uygun olanları seç:

1. RSI_ANALYSIS - RSI grafiği ve analizi
2. MACD_ANALYSIS - MACD grafiği ve analizi  
3. BOLLINGER_ANALYSIS - Bollinger Bands grafiği ve analizi
4. SMA_ANALYSIS - Hareketli ortalama grafiği ve analizi
5. VOLUME_ANALYSIS - Hacim grafiği ve analizi
6. PRICE_ANALYSIS - Fiyat grafiği ve analizi
7. FULL_ANALYSIS - Tüm grafikler ve genel analiz

Sadece JSON formatında yanıt ver:
{{
    "analyses": ["RSI_ANALYSIS", "MACD_ANALYSIS"],
    "reasoning": "Kullanıcı RSI ve MACD hakkında soru sordu",
    "custom_message": "RSI ve MACD analizleri hazırlanıyor..."
}}

Eğer kullanıcı genel bir analiz istiyorsa FULL_ANALYSIS seç.
"""
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # JSON yanıtını parse et
            import json
            try:
                result = json.loads(response_text)
                analyses = result.get('analyses', [])
                custom_message = result.get('custom_message', '')
                
                # Analizleri uygula
                charts = []
                analysis_text = ""
                
                for analysis in analyses:
                    if analysis == "RSI_ANALYSIS":
                        charts.extend(self.create_rsi_chart(df))
                        analysis_text += self.analyze_rsi(df) + "\n\n"
                    elif analysis == "MACD_ANALYSIS":
                        charts.extend(self.create_macd_chart(df))
                        analysis_text += self.analyze_macd(df) + "\n\n"
                    elif analysis == "BOLLINGER_ANALYSIS":
                        charts.extend(self.create_bollinger_chart(df))
                        analysis_text += self.analyze_bollinger(df) + "\n\n"
                    elif analysis == "SMA_ANALYSIS":
                        charts.extend(self.create_sma_chart(df))
                        analysis_text += self.analyze_sma(df) + "\n\n"
                    elif analysis == "VOLUME_ANALYSIS":
                        charts.extend(self.create_volume_chart(df))
                        analysis_text += self.analyze_volume(df) + "\n\n"
                    elif analysis == "PRICE_ANALYSIS":
                        charts.extend(self.create_price_chart(df))
                        analysis_text += self.analyze_price(df) + "\n\n"
                    elif analysis == "FULL_ANALYSIS":
                        charts.extend(self.create_default_charts(df))
                        analysis_text += self.analyze_technical_indicators(df)
                
                return {
                    "charts": charts,
                    "analysis": analysis_text,
                    "summary": custom_message or f"{len(charts)} grafik oluşturuldu.",
                    "error": None
                }
                
            except json.JSONDecodeError:
                print(f"Gemini JSON parse hatası: {response_text}")
                return None
                
        except Exception as e:
            print(f"Gemini analiz hatası: {e}")
            return None
    
    def rule_based_analysis(self, user_request, df):
        """Rule-based analiz (fallback)"""
        user_request_lower = user_request.lower()
        
        # Spesifik analiz istekleri
        if any(word in user_request_lower for word in ['rsi', 'relative strength']):
            charts = self.create_rsi_chart(df)
            analysis = self.analyze_rsi(df)
            summary = "RSI analizi tamamlandı."
            
        elif any(word in user_request_lower for word in ['macd', 'moving average convergence']):
            charts = self.create_macd_chart(df)
            analysis = self.analyze_macd(df)
            summary = "MACD analizi tamamlandı."
            
        elif any(word in user_request_lower for word in ['bollinger', 'bb', 'bant']):
            charts = self.create_bollinger_chart(df)
            analysis = self.analyze_bollinger(df)
            summary = "Bollinger Bands analizi tamamlandı."
            
        elif any(word in user_request_lower for word in ['sma', 'hareketli ortalama', 'moving average']):
            charts = self.create_sma_chart(df)
            analysis = self.analyze_sma(df)
            summary = "Hareketli ortalama analizi tamamlandı."
            
        elif any(word in user_request_lower for word in ['hacim', 'volume']):
            charts = self.create_volume_chart(df)
            analysis = self.analyze_volume(df)
            summary = "Hacim analizi tamamlandı."
            
        elif any(word in user_request_lower for word in ['fiyat', 'price', 'mum', 'candlestick']):
            charts = self.create_price_chart(df)
            analysis = self.analyze_price(df)
            summary = "Fiyat analizi tamamlandı."
            
        else:
            # Genel teknik analiz - tüm grafikleri getir
            charts = self.create_default_charts(df)
            analysis = self.analyze_technical_indicators(df)
            summary = f"KCHOL hisse senedi teknik analizi tamamlandı. {len(charts)} grafik oluşturuldu."
        
        return {
            "charts": charts,
            "analysis": analysis,
            "summary": summary,
            "error": None
        } 