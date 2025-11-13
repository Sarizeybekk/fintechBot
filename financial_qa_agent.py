#!/usr/bin/env python3
"""
Financial Q&A Agent using Gemini
Handles natural language financial questions with comprehensive analysis
"""

import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from finta import TA
import requests
import json

# Load environment variables
load_dotenv()

class FinancialQAAgent:
    def __init__(self):
        """Finansal Q&A agent'ını başlat"""
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            print(" Financial Q&A Agent - Gemini API bağlantısı kuruldu")
        else:
            print("Financial Q&A Agent - Gemini API anahtarı bulunamadı")
            self.gemini_model = None
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Türk hisse senetleri listesi
        self.turkish_stocks = {
            'KCHOL': 'KCHOL.IS',
            'THYAO': 'THYAO.IS',
            'GARAN': 'GARAN.IS',
            'AKBNK': 'AKBNK.IS',
            'ISCTR': 'ISCTR.IS',
            'ASELS': 'ASELS.IS',
            'EREGL': 'EREGL.IS',
            'SASA': 'SASA.IS',
            'BIMAS': 'BIMAS.IS',
            'TUPRS': 'TUPRS.IS',
            'XU100': 'XU100.IS'  # BIST 100 endeksi
        }
    
    def analyze_question_type(self, question):
        """Soru tipini analiz et"""
        question_lower = question.lower()
        
        # Finansal eğitim soruları (öncelikli)
        if any(word in question_lower for word in ['nedir', 'ne demek', 'açıkla', 'anlat', 'eğitim', 'öğren', 'rehber']):
            return 'financial_education'
        
        # Hacim analizi
        if any(word in question_lower for word in ['hacim', 'volume', 'ortalama hacim', 'hacmi nedir']):
            return 'volume_analysis'
        
        # Endeks analizi
        if any(word in question_lower for word in ['xu100', 'bist', 'endeks', 'index']):
            return 'index_analysis'
        
        # Teknik indikatör analizi
        if any(word in question_lower for word in ['rsi', 'macd', 'sma', 'bollinger', 'williams']):
            return 'technical_analysis'
        
        # Fiyat analizi
        if any(word in question_lower for word in ['fiyat', 'price', 'düştü', 'yükseldi', 'değişim']):
            return 'price_analysis'
        
        # Genel finansal soru
        return 'general_financial'
    
    def get_stock_data(self, symbol, days=180):
        """Hisse verisi al"""
        try:
            # Türk hisse senetleri için .IS ekle
            if symbol in self.turkish_stocks:
                yf_symbol = self.turkish_stocks[symbol]
            else:
                yf_symbol = symbol
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            self.logger.info(f"Veri alınıyor: {yf_symbol} - {start_date} to {end_date}")
            
            # Farklı sembol formatlarını dene
            df = None
            symbol_variants = [yf_symbol, f"{symbol}.IS", symbol]
            
            for variant in symbol_variants:
                try:
                    self.logger.info(f"Deneniyor: {variant}")
                    df = yf.download(variant, start_date, end_date, progress=False, timeout=30)
                    if not df.empty:
                        self.logger.info(f"Başarılı: {variant} - Veri boyutu: {df.shape}")
                        break
                except Exception as e:
                    self.logger.warning(f"Başarısız: {variant} - Hata: {e}")
                    continue
            
            if df is None or df.empty:
                self.logger.error(f"Hiçbir sembol formatı çalışmadı: {symbol}")
                return None
            
            # Sütun isimlerini düzenleme
            try:
                df.columns = ['_'.join(col).lower() for col in df.columns]
                df.columns = [col.split('_')[0] for col in df.columns]
                self.logger.info(f"Düzenlenmiş sütunlar: {df.columns.tolist()}")
            except Exception as e:
                self.logger.error(f"Sütun düzenleme hatası: {e}")
                return None
            
            # Gerekli sütunların varlığını kontrol et
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"Eksik sütunlar: {missing_columns}")
                return None
            
            # Teknik indikatörler ekle
            try:
                # Temel teknik indikatörler
                df['SMA20'] = TA.SMA(df, 20)
                df['SMA50'] = TA.SMA(df, 50)
                df['RSI'] = TA.RSI(df)
                
                # Sadece RSI için hacim analizi yapılacaksa diğer indikatörleri atla
                if 'rsi' in question.lower() if 'question' in locals() else False:
                    self.logger.info("Sadece RSI hesaplanıyor")
                    return df
                
                # Diğer teknik indikatörler (opsiyonel)
                try:
                    df['SMA200'] = TA.SMA(df, 200)
                except:
                    df['SMA200'] = np.nan
                
                # MACD hesapla
                try:
                    macd_data = TA.MACD(df)
                    df['MACD'] = macd_data['MACD']
                    df['MACD_SIGNAL'] = macd_data['MACD_SIGNAL']
                except Exception as e:
                    self.logger.warning(f"MACD hesaplama hatası: {e}")
                    df['MACD'] = np.nan
                    df['MACD_SIGNAL'] = np.nan
                
                # Bollinger Bands hesapla
                try:
                    bb_data = TA.BBANDS(df)
                    df['BB_UPPER'] = bb_data['BB_UPPER']
                    df['BB_LOWER'] = bb_data['BB_LOWER']
                except Exception as e:
                    self.logger.warning(f"Bollinger Bands hesaplama hatası: {e}")
                    df['BB_UPPER'] = np.nan
                    df['BB_LOWER'] = np.nan
                
                try:
                    df['WILLIAMS_R'] = TA.WILLIAMS(df)
                except:
                    df['WILLIAMS_R'] = np.nan
                
                try:
                    df['ATR'] = TA.ATR(df)
                except:
                    df['ATR'] = np.nan
                
                self.logger.info(f"Teknik indikatörler eklendi. Final veri boyutu: {df.shape}")
                
            except Exception as e:
                self.logger.error(f"Teknik indikatör ekleme hatası: {e}")
                return None
            
            # NaN değerleri temizle (sadece gerekli sütunlar için)
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            df_cleaned = df[required_columns].dropna()
            
            # Teknik indikatör sütunlarını ekle (NaN olsa bile)
            for col in df.columns:
                if col not in required_columns:
                    df_cleaned[col] = df[col]
            
            self.logger.info(f"Temizlenmiş veri boyutu: {df_cleaned.shape}")
            
            if len(df_cleaned) < 5:  # Minimum veri noktası
                self.logger.warning(f"Yeterli veri yok: {len(df_cleaned)} nokta")
                return None
            
            return df_cleaned
            
        except Exception as e:
            self.logger.error(f"Genel veri alma hatası ({symbol}): {e}")
            return None
    
    def _get_volume_data(self, symbol, days=180):
        """Hacim analizi için özel veri alma fonksiyonu"""
        try:
            # Türk hisse senetleri için .IS ekle
            if symbol in self.turkish_stocks:
                yf_symbol = self.turkish_stocks[symbol]
            else:
                yf_symbol = symbol
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            self.logger.info(f"Hacim verisi alınıyor: {yf_symbol} - {start_date} to {end_date}")
            
            # Farklı sembol formatlarını dene
            df = None
            symbol_variants = [yf_symbol, f"{symbol}.IS", symbol]
            
            for variant in symbol_variants:
                try:
                    self.logger.info(f"Deneniyor: {variant}")
                    df = yf.download(variant, start_date, end_date, progress=False, timeout=30)
                    if not df.empty:
                        self.logger.info(f"Başarılı: {variant} - Veri boyutu: {df.shape}")
                        break
                except Exception as e:
                    self.logger.warning(f"Başarısız: {variant} - Hata: {e}")
                    continue
            
            if df is None or df.empty:
                self.logger.error(f"Hiçbir sembol formatı çalışmadı: {symbol}")
                return None
            
            # Sütun isimlerini düzenleme
            try:
                df.columns = ['_'.join(col).lower() for col in df.columns]
                df.columns = [col.split('_')[0] for col in df.columns]
                self.logger.info(f"Düzenlenmiş sütunlar: {df.columns.tolist()}")
            except Exception as e:
                self.logger.error(f"Sütun düzenleme hatası: {e}")
                return None
            
            # Gerekli sütunların varlığını kontrol et
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.error(f"Eksik sütunlar: {missing_columns}")
                return None
            
            # Sadece gerekli sütunları tut
            df_volume = df[required_columns].copy()
            
            # NaN değerleri temizle
            df_cleaned = df_volume.dropna()
            self.logger.info(f"Hacim verisi temizlendikten sonra boyut: {df_cleaned.shape}")
            
            if len(df_cleaned) < 5:  # Minimum veri noktası
                self.logger.warning(f"Yeterli hacim verisi yok: {len(df_cleaned)} nokta")
                return None
            
            return df_cleaned
            
        except Exception as e:
            self.logger.error(f"Hacim verisi alma hatası ({symbol}): {e}")
            return None
    
    def provide_financial_education(self, question):
        """Finansal eğitim ve rehberlik sağla"""
        try:
            self.logger.info(f"Finansal eğitim sorusu: {question}")
            question_lower = question.lower()
            
            # RSI Eğitimi
            if 'rsi' in question_lower:
                return self._explain_rsi_with_example()
            
            # Volatilite Eğitimi
            elif 'volatilite' in question_lower:
                return self._explain_volatility_with_example()
            
            # SMA Eğitimi
            elif 'sma' in question_lower:
                return self._explain_sma_with_example()
            
            # MACD Eğitimi
            elif 'macd' in question_lower:
                return self._explain_macd_with_example()
            
            # Bollinger Bands Eğitimi
            elif 'bollinger' in question_lower or 'bant' in question_lower:
                return self._explain_bollinger_with_example()
            
            # Hacim Eğitimi
            elif 'hacim' in question_lower or 'volume' in question_lower:
                return self._explain_volume_with_example()
            
            # Genel finansal terimler
            else:
                return self._explain_general_financial_terms(question)
                
        except Exception as e:
            self.logger.error(f"Finansal eğitim hatası: {e}")
            return None
    
    def _explain_rsi_with_example(self):
        """RSI'yi açıkla ve gerçek örnek ver"""
        try:
            # KCHOL için RSI hesapla
            df = self.get_stock_data('KCHOL', days=30)
            if df is not None and 'RSI' in df.columns:
                current_rsi = df['RSI'].iloc[-1]
                current_price = df['close'].iloc[-1]
                
                # RSI durumunu belirle
                if current_rsi > 70:
                    rsi_status = "Aşırı Alım Bölgesi"
                    rsi_advice = "Dikkatli olunmalı, düzeltme beklenebilir"
                elif current_rsi < 30:
                    rsi_status = "Aşırı Satım Bölgesi"
                    rsi_advice = "Alım fırsatı olabilir"
                else:
                    rsi_status = "Nötr Bölge"
                    rsi_advice = "Normal seyir devam ediyor"
                
                explanation = f"""📚 **RSI (Relative Strength Index) Nedir?**

**🔍 Tanım:**
RSI, bir hisse senedinin aşırı alım veya aşırı satım bölgesinde olup olmadığını gösteren teknik bir göstergedir.

**📊 Nasıl Hesaplanır:**
• 0-100 arasında değer alır
• 14 günlük ortalama kazanç/kayıp oranına dayanır
• Formül: RSI = 100 - (100 / (1 + RS))

**🎯 Yorumlama:**
• **70+**: Aşırı alım bölgesi (satış sinyali)
• **30-**: Aşırı satım bölgesi (alım sinyali)
• **30-70**: Nötr bölge

**💡 KCHOL Örneği:**
• Güncel RSI: {current_rsi:.2f}
• Güncel Fiyat: {current_price:.2f} TL
• Durum: {rsi_status}
• Tavsiye: {rsi_advice}

**Önemli Not:**
RSI tek başına yeterli değildir. Diğer göstergelerle birlikte kullanılmalıdır.

**🔗 İlgili Terimler:**
• Aşırı Alım/Satım
• Momentum
• Teknik Analiz"""
                
                return {
                    'type': 'financial_education',
                    'topic': 'RSI',
                    'explanation': explanation,
                    'example_data': {
                        'symbol': 'KCHOL',
                        'current_rsi': round(current_rsi, 2),
                        'current_price': round(current_price, 2),
                        'status': rsi_status
                    }
                }
            else:
                return self._explain_rsi_general()
                
        except Exception as e:
            self.logger.error(f"RSI açıklama hatası: {e}")
            return self._explain_rsi_general()
    
    def _explain_rsi_general(self):
        """RSI genel açıklaması"""
        explanation = f"""📚 **RSI (Relative Strength Index) Nedir?**

**🔍 Tanım:**
RSI, bir hisse senedinin aşırı alım veya aşırı satım bölgesinde olup olmadığını gösteren teknik bir göstergedir.

**📊 Nasıl Hesaplanır:**
• 0-100 arasında değer alır
• 14 günlük ortalama kazanç/kayıp oranına dayanır
• Formül: RSI = 100 - (100 / (1 + RS))

**🎯 Yorumlama:**
• **70+**: Aşırı alım bölgesi (satış sinyali)
• **30-**: Aşırı satım bölgesi (alım sinyali)
• **30-70**: Nötr bölge

**💡 Pratik Örnek:**
KCHOL hissesi için RSI değeri hesaplayabilirsiniz:
"KCHOL'un RSI değeri nedir?"

**Önemli Not:**
RSI tek başına yeterli değildir. Diğer göstergelerle birlikte kullanılmalıdır.

**🔗 İlgili Terimler:**
• Aşırı Alım/Satım
• Momentum
• Teknik Analiz"""
        
        return {
            'type': 'financial_education',
            'topic': 'RSI',
            'explanation': explanation
        }
    
    def _explain_volatility_with_example(self):
        """Volatiliteyi açıkla ve gerçek örnek ver"""
        try:
            # GARAN için volatilite hesapla
            df = self.get_stock_data('GARAN', days=30)
            if df is not None:
                returns = df['close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252) * 100  # Yıllık volatilite
                current_price = df['close'].iloc[-1]
                
                # Volatilite seviyesini belirle
                if volatility > 50:
                    vol_level = "Çok Yüksek"
                    vol_advice = "Yüksek risk, dikkatli olunmalı"
                elif volatility > 30:
                    vol_level = "Yüksek"
                    vol_advice = "Orta-yüksek risk"
                elif volatility > 15:
                    vol_level = "Orta"
                    vol_advice = "Normal risk seviyesi"
                else:
                    vol_level = "Düşük"
                    vol_advice = "Düşük risk"
                
                explanation = f"""📚 **Volatilite Nedir?**

**🔍 Tanım:**
Volatilite, bir hisse senedinin fiyatının ne kadar dalgalandığını gösteren risk ölçüsüdür.

**📊 Nasıl Hesaplanır:**
• Günlük getirilerin standart sapması
• Yıllık volatilite = Günlük volatilite × √252
• Yüzde olarak ifade edilir

**🎯 Yorumlama:**
• **%50+**: Çok yüksek volatilite (yüksek risk)
• **%30-50**: Yüksek volatilite
• **%15-30**: Orta volatilite
• **%15-**: Düşük volatilite (düşük risk)

**💡 GARAN Örneği:**
• Güncel Fiyat: {current_price:.2f} TL
• Yıllık Volatilite: %{volatility:.1f}
• Volatilite Seviyesi: {vol_level}
• Risk Değerlendirmesi: {vol_advice}

**Önemli Not:**
Yüksek volatilite hem fırsat hem de risk demektir.

**🔗 İlgili Terimler:**
• Risk
• Standart Sapma
• Beta"""
                
                return {
                    'type': 'financial_education',
                    'topic': 'Volatilite',
                    'explanation': explanation,
                    'example_data': {
                        'symbol': 'GARAN',
                        'volatility': round(volatility, 1),
                        'current_price': round(current_price, 2),
                        'level': vol_level
                    }
                }
            else:
                return self._explain_volatility_general()
                
        except Exception as e:
            self.logger.error(f"Volatilite açıklama hatası: {e}")
            return self._explain_volatility_general()
    
    def _explain_volatility_general(self):
        """Volatilite genel açıklaması"""
        explanation = f"""📚 **Volatilite Nedir?**

**🔍 Tanım:**
Volatilite, bir hisse senedinin fiyatının ne kadar dalgalandığını gösteren risk ölçüsüdür.

**📊 Nasıl Hesaplanır:**
• Günlük getirilerin standart sapması
• Yıllık volatilite = Günlük volatilite × √252
• Yüzde olarak ifade edilir

**🎯 Yorumlama:**
• **%50+**: Çok yüksek volatilite (yüksek risk)
• **%30-50**: Yüksek volatilite
• **%15-30**: Orta volatilite
• **%15-**: Düşük volatilite (düşük risk)

**💡 Pratik Örnek:**
"GARAN'ın volatilitesi nedir?" diye sorabilirsiniz.

**Önemli Not:**
Yüksek volatilite hem fırsat hem de risk demektir.

**🔗 İlgili Terimler:**
• Risk
• Standart Sapma
• Beta"""
        
        return {
            'type': 'financial_education',
            'topic': 'Volatilite',
            'explanation': explanation
        }
    
    def _explain_sma_with_example(self):
        """SMA'yı açıkla ve gerçek örnek ver"""
        try:
            # THYAO için SMA hesapla
            df = self.get_stock_data('THYAO', days=60)
            if df is not None and 'SMA20' in df.columns and 'SMA50' in df.columns:
                current_price = df['close'].iloc[-1]
                sma20 = df['SMA20'].iloc[-1]
                sma50 = df['SMA50'].iloc[-1]
                
                # Trend analizi
                if current_price > sma20 > sma50:
                    trend = "Güçlü Yükseliş"
                    signal = "Alım sinyali"
                elif current_price < sma20 < sma50:
                    trend = "Güçlü Düşüş"
                    signal = "Satış sinyali"
                elif current_price > sma20 and sma20 < sma50:
                    trend = "Kararsız"
                    signal = "Bekle ve gör"
                else:
                    trend = "Kararsız"
                    signal = "Dikkatli ol"
                
                explanation = f"""📚 **SMA (Simple Moving Average) Nedir?**

**🔍 Tanım:**
SMA, belirli bir dönemdeki fiyatların ortalamasını alarak trend yönünü gösteren teknik göstergedir.

**📊 Nasıl Hesaplanır:**
• SMA = (Fiyat1 + Fiyat2 + ... + FiyatN) / N
• SMA 20: Son 20 günün ortalaması
• SMA 50: Son 50 günün ortalaması
• SMA 200: Son 200 günün ortalaması

**🎯 Yorumlama:**
• **Fiyat > SMA**: Yükseliş trendi
• **Fiyat < SMA**: Düşüş trendi
• **SMA20 > SMA50**: Kısa vadeli güçlü
• **Altın Kesişim**: SMA20, SMA50'yi yukarı keser

**💡 THYAO Örneği:**
• Güncel Fiyat: {current_price:.2f} TL
• SMA 20: {sma20:.2f} TL
• SMA 50: {sma50:.2f} TL
• Trend: {trend}
• Sinyal: {signal}

**Önemli Not:**
SMA'lar geçmiş verilere dayanır, geleceği garanti etmez.

**🔗 İlgili Terimler:**
• Trend
• Altın Kesişim
• Ölüm Kesişimi"""
                
                return {
                    'type': 'financial_education',
                    'topic': 'SMA',
                    'explanation': explanation,
                    'example_data': {
                        'symbol': 'THYAO',
                        'current_price': round(current_price, 2),
                        'sma20': round(sma20, 2),
                        'sma50': round(sma50, 2),
                        'trend': trend
                    }
                }
            else:
                return self._explain_sma_general()
                
        except Exception as e:
            self.logger.error(f"SMA açıklama hatası: {e}")
            return self._explain_sma_general()
    
    def _explain_sma_general(self):
        """SMA genel açıklaması"""
        explanation = f"""📚 **SMA (Simple Moving Average) Nedir?**

**🔍 Tanım:**
SMA, belirli bir dönemdeki fiyatların ortalamasını alarak trend yönünü gösteren teknik göstergedir.

**📊 Nasıl Hesaplanır:**
• SMA = (Fiyat1 + Fiyat2 + ... + FiyatN) / N
• SMA 20: Son 20 günün ortalaması
• SMA 50: Son 50 günün ortalaması
• SMA 200: Son 200 günün ortalaması

**🎯 Yorumlama:**
• **Fiyat > SMA**: Yükseliş trendi
• **Fiyat < SMA**: Düşüş trendi
• **SMA20 > SMA50**: Kısa vadeli güçlü
• **Altın Kesişim**: SMA20, SMA50'yi yukarı keser

**💡 Pratik Örnek:**
"THYAO'nun SMA 20 ve SMA 50 değerleri nedir?" diye sorabilirsiniz.

**Önemli Not:**
SMA'lar geçmiş verilere dayanır, geleceği garanti etmez.

**🔗 İlgili Terimler:**
• Trend
• Altın Kesişim
• Ölüm Kesişimi"""
        
        return {
            'type': 'financial_education',
            'topic': 'SMA',
            'explanation': explanation
        }
    
    def _explain_macd_with_example(self):
        """MACD'yi açıkla ve gerçek örnek ver"""
        explanation = f"""📚 **MACD (Moving Average Convergence Divergence) Nedir?**

**🔍 Tanım:**
MACD, iki farklı periyottaki hareketli ortalamaların farkını kullanarak momentum değişimlerini gösteren göstergedir.

**📊 Nasıl Hesaplanır:**
• MACD Çizgisi = 12 günlük EMA - 26 günlük EMA
• Sinyal Çizgisi = MACD'nin 9 günlük EMA'sı
• Histogram = MACD - Sinyal Çizgisi

**🎯 Yorumlama:**
• **MACD > Sinyal**: Alım sinyali
• **MACD < Sinyal**: Satış sinyali
• **Histogram pozitif**: Momentum artıyor
• **Histogram negatif**: Momentum azalıyor

**💡 Pratik Örnek:**
"KCHOL'un MACD değerleri nedir?" diye sorabilirsiniz.

**Önemli Not:**
MACD gecikmeli bir göstergedir, trend değişimlerini geç gösterir.

**🔗 İlgili Terimler:**
• Momentum
• EMA (Exponential Moving Average)
• Histogram"""
        
        return {
            'type': 'financial_education',
            'topic': 'MACD',
            'explanation': explanation
        }
    
    def _explain_bollinger_with_example(self):
        """Bollinger Bands'ı açıkla ve gerçek örnek ver"""
        explanation = f"""📚 **Bollinger Bands Nedir?**

**🔍 Tanım:**
Bollinger Bands, fiyat volatilitesini ve olası destek/direnç seviyelerini gösteren teknik göstergedir.

**📊 Nasıl Hesaplanır:**
• Orta Bant = 20 günlük SMA
• Üst Bant = Orta Bant + (2 × Standart Sapma)
• Alt Bant = Orta Bant - (2 × Standart Sapma)

**🎯 Yorumlama:**
• **Fiyat üst banda yakın**: Aşırı alım
• **Fiyat alt banda yakın**: Aşırı satım
• **Bantlar daralıyor**: Volatilite azalıyor
• **Bantlar genişliyor**: Volatilite artıyor

**💡 Pratik Örnek:**
"GARAN'ın Bollinger Bands değerleri nedir?" diye sorabilirsiniz.

**Önemli Not:**
Bollinger Bands trend yönünü göstermez, sadece volatilite ve aşırı alım/satım bölgelerini gösterir.

**🔗 İlgili Terimler:**
• Volatilite
• Standart Sapma
• Aşırı Alım/Satım"""
        
        return {
            'type': 'financial_education',
            'topic': 'Bollinger Bands',
            'explanation': explanation
        }
    
    def _explain_volume_with_example(self):
        """Hacmi açıkla ve gerçek örnek ver"""
        try:
            # AKBNK için hacim analizi
            volume_data = self.analyze_volume('AKBNK', 1)
            if volume_data:
                explanation = f"""📚 **Hacim (Volume) Nedir?**

**🔍 Tanım:**
Hacim, belirli bir dönemde işlem gören hisse senedi sayısını gösterir.

**📊 Nasıl Yorumlanır:**
• **Yüksek hacim**: Güçlü piyasa ilgisi
• **Düşük hacim**: Zayıf piyasa ilgisi
• **Hacim artışı + fiyat artışı**: Güçlü alım
• **Hacim artışı + fiyat düşüşü**: Güçlü satım

**💡 AKBNK Örneği:**
• Ortalama Hacim: {volume_data['average_volume']:,} adet
• Güncel Hacim: {volume_data['current_volume']:,} adet
• Hacim Değişimi: %{volume_data['volume_change_percent']:.1f}
• Hacim Trendi: {volume_data['volume_trend']}

**Önemli Not:**
Hacim, fiyat hareketlerinin güvenilirliğini doğrular.

**🔗 İlgili Terimler:**
• Ortalama Hacim
• Hacim Trendi
• Likidite"""
                
                return {
                    'type': 'financial_education',
                    'topic': 'Hacim',
                    'explanation': explanation,
                    'example_data': volume_data
                }
            else:
                return self._explain_volume_general()
                
        except Exception as e:
            self.logger.error(f"Hacim açıklama hatası: {e}")
            return self._explain_volume_general()
    
    def _explain_volume_general(self):
        """Hacim genel açıklaması"""
        explanation = f"""📚 **Hacim (Volume) Nedir?**

**🔍 Tanım:**
Hacim, belirli bir dönemde işlem gören hisse senedi sayısını gösterir.

**📊 Nasıl Yorumlanır:**
• **Yüksek hacim**: Güçlü piyasa ilgisi
• **Düşük hacim**: Zayıf piyasa ilgisi
• **Hacim artışı + fiyat artışı**: Güçlü alım
• **Hacim artışı + fiyat düşüşü**: Güçlü satım

**💡 Pratik Örnek:**
"AKBNK'nın son 1 aylık hacim analizi" diye sorabilirsiniz.

**Önemli Not:**
Hacim, fiyat hareketlerinin güvenilirliğini doğrular.

**🔗 İlgili Terimler:**
• Ortalama Hacim
• Hacim Trendi
• Likidite"""
        
        return {
            'type': 'financial_education',
            'topic': 'Hacim',
            'explanation': explanation
        }
    
    def _explain_general_financial_terms(self, question):
        """Genel finansal terimleri açıkla"""
        question_lower = question.lower()
        
        if 'beta' in question_lower:
            explanation = f"""📚 **Beta Nedir?**

**🔍 Tanım:**
Beta, bir hisse senedinin piyasa ortalamasına göre ne kadar volatil olduğunu gösteren risk ölçüsüdür.

**📊 Yorumlama:**
• **Beta > 1**: Piyasadan daha volatil
• **Beta = 1**: Piyasa ortalaması
• **Beta < 1**: Piyasadan daha az volatil
• **Beta = 0**: Piyasa ile korelasyon yok

**💡 Örnek:**
Beta = 1.5 olan bir hisse, piyasa %10 yükseldiğinde %15 yükselir.

**Önemli Not:**
Beta, sistematik riski ölçer."""
        
        elif 'pe' in question_lower or 'f/k' in question_lower:
            explanation = f"""📚 **P/E (F/K) Oranı Nedir?**

**🔍 Tanım:**
P/E oranı, bir hisse senedinin fiyatının kazancının kaç katı olduğunu gösterir.

**📊 Yorumlama:**
• **Düşük P/E**: Ucuz hisse (potansiyel fırsat)
• **Yüksek P/E**: Pahalı hisse (yüksek beklenti)
• **Ortalama P/E**: Sektör ortalamasına bakılmalı

**💡 Hesaplama:**
P/E = Hisse Fiyatı / Hisse Başına Kazanç

**Önemli Not:**
P/E tek başına yeterli değildir, büyüme ve sektör analizi gerekir."""
        
        elif 'dividend' in question_lower or 'temettü' in question_lower:
            explanation = f"""📚 **Temettü (Dividend) Nedir?**

**🔍 Tanım:**
Temettü, şirketin karının bir kısmını hissedarlarına dağıtmasıdır.

**📊 Türleri:**
• **Nakit Temettü**: Para olarak ödeme
• **Hisse Temettüsü**: Yeni hisse dağıtımı
• **Temettü Verimi**: Yıllık temettü / Hisse fiyatı

**💡 Avantajları:**
• Düzenli gelir
• Şirket güvenilirliği göstergesi
• Vergi avantajı

**Önemli Not:**
Temettü garantisi yoktur, şirket karına bağlıdır."""
        
        else:
            explanation = f"""📚 **Finansal Terimler Rehberi**

**🔍 Popüler Terimler:**

**📊 Teknik Analiz:**
• RSI: Aşırı alım/satım göstergesi
• MACD: Momentum göstergesi
• SMA: Hareketli ortalama
• Bollinger Bands: Volatilite göstergesi

**📈 Temel Analiz:**
• P/E: Fiyat/Kazanç oranı
• Beta: Risk ölçüsü
• Temettü: Kar payı
• Hacim: İşlem miktarı

**💡 Nasıl Öğrenirim?**
"RSI nedir?", "Volatilite ne demek?" gibi sorular sorabilirsiniz.

**Önemli Not:**
Her terim için gerçek örneklerle açıklama alabilirsiniz."""
        
        return {
            'type': 'financial_education',
            'topic': 'Genel Finansal Terimler',
            'explanation': explanation
        }
    
    def analyze_volume(self, symbol, period_months=6):
        """Hacim analizi yap"""
        try:
            self.logger.info(f"Hacim analizi başlatılıyor: {symbol} - {period_months} ay")
            
            days = period_months * 30
            
            # Hacim analizi için özel veri alma
            df = self._get_volume_data(symbol, days)
            
            if df is None or df.empty:
                self.logger.error(f"Veri alınamadı: {symbol}")
                return None
            
            # Volume sütununun varlığını kontrol et
            if 'volume' not in df.columns:
                self.logger.error(f"Volume sütunu bulunamadı. Mevcut sütunlar: {df.columns.tolist()}")
                return None
            
            # Hacim verilerini kontrol et
            volume_data = df['volume']
            if volume_data.isnull().all() or volume_data.sum() == 0:
                self.logger.error(f"Volume verisi boş veya geçersiz: {symbol}")
                return None
            
            self.logger.info(f"Volume verisi alındı. Veri noktası sayısı: {len(volume_data)}")
            
            # Hacim analizi
            avg_volume = volume_data.mean()
            current_volume = volume_data.iloc[-1]
            volume_change = ((current_volume - avg_volume) / avg_volume) * 100 if avg_volume > 0 else 0
            
            # Son 30 günün hacim verileri
            recent_volume = volume_data.tail(30).mean() if len(volume_data) >= 30 else volume_data.mean()
            volume_trend = "artış" if recent_volume > avg_volume else "azalış"
            
            # Ek istatistikler
            max_volume = volume_data.max()
            min_volume = volume_data.min()
            volume_volatility = volume_data.std() / avg_volume if avg_volume > 0 else 0
            
            analysis = {
                'symbol': symbol,
                'period_months': period_months,
                'average_volume': int(avg_volume),
                'current_volume': int(current_volume),
                'volume_change_percent': round(volume_change, 2),
                'recent_volume': int(recent_volume),
                'volume_trend': volume_trend,
                'max_volume': int(max_volume),
                'min_volume': int(min_volume),
                'volume_volatility': round(volume_volatility, 3),
                'data_points': len(df),
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.logger.info(f"Hacim analizi tamamlandı: {symbol}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Hacim analizi hatası ({symbol}): {e}")
            return None
    
    def analyze_index_components(self, index_symbol='XU100'):
        """Endeks bileşenlerini analiz et"""
        try:
            # BIST 100 endeksi verisi
            df = self.get_stock_data(index_symbol, days=30)
            
            if df is None or df.empty:
                return None
            
            # Endeks değişimi
            current_price = df['close'].iloc[-1]
            previous_price = df['close'].iloc[-2]
            daily_change = ((current_price - previous_price) / previous_price) * 100
            
            # BIST 100 bileşenlerini al (örnek veri)
            # Gerçek uygulamada BIST API'si kullanılabilir
            sample_components = [
                {'symbol': 'KCHOL', 'name': 'Koç Holding', 'weight': 8.5, 'change': -2.1},
                {'symbol': 'GARAN', 'name': 'Garanti Bankası', 'weight': 6.2, 'change': 1.3},
                {'symbol': 'AKBNK', 'name': 'Akbank', 'weight': 5.8, 'change': -0.8},
                {'symbol': 'THYAO', 'name': 'Türk Hava Yolları', 'weight': 4.1, 'change': 3.2},
                {'symbol': 'EREGL', 'name': 'Ereğli Demir Çelik', 'weight': 3.9, 'change': -1.5}
            ]
            
            # Düşen hisseleri filtrele
            falling_stocks = [stock for stock in sample_components if stock['change'] < 0]
            
            analysis = {
                'index_symbol': index_symbol,
                'current_price': round(current_price, 2),
                'daily_change': round(daily_change, 2),
                'falling_stocks_count': len(falling_stocks),
                'falling_stocks': falling_stocks,
                'total_components': len(sample_components)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Endeks analizi hatası: {e}")
            return None
    
    def analyze_technical_indicators(self, symbol, indicator='RSI', threshold=70):
        """Teknik indikatör analizi"""
        try:
            df = self.get_stock_data(symbol, days=60)
            
            if df is None or df.empty:
                return None
            
            current_price = df['close'].iloc[-1]
            current_rsi = df['RSI'].iloc[-1]
            
            # RSI analizi
            if indicator.upper() == 'RSI':
                rsi_status = "Aşırı alım" if current_rsi > threshold else "Aşırı satım" if current_rsi < 30 else "Nötr"
                rsi_signal = "Satış sinyali" if current_rsi > threshold else "Alım sinyali" if current_rsi < 30 else "Bekle"
                
                analysis = {
                    'symbol': symbol,
                    'indicator': 'RSI',
                    'current_value': round(current_rsi, 2),
                    'threshold': threshold,
                    'status': rsi_status,
                    'signal': rsi_signal,
                    'current_price': round(current_price, 2)
                }
                
                return analysis
            
            # Diğer indikatörler için genişletilebilir
            return None
            
        except Exception as e:
            self.logger.error(f"Teknik indikatör analizi hatası: {e}")
            return None
    
    def get_multiple_stocks_rsi(self, threshold=70):
        """Birden fazla hissenin RSI değerlerini al"""
        try:
            high_rsi_stocks = []
            
            for symbol in ['KCHOL', 'THYAO', 'GARAN', 'AKBNK', 'ISCTR', 'ASELS', 'EREGL', 'SASA']:
                df = self.get_stock_data(symbol, days=30)
                
                if df is not None and not df.empty:
                    current_rsi = df['RSI'].iloc[-1]
                    current_price = df['close'].iloc[-1]
                    
                    if current_rsi > threshold:
                        high_rsi_stocks.append({
                            'symbol': symbol,
                            'rsi': round(current_rsi, 2),
                            'price': round(current_price, 2),
                            'status': 'Aşırı alım'
                        })
            
            return {
                'threshold': threshold,
                'high_rsi_count': len(high_rsi_stocks),
                'stocks': high_rsi_stocks
            }
            
        except Exception as e:
            self.logger.error(f"Çoklu RSI analizi hatası: {e}")
            return None
    
    def generate_gemini_response(self, question, analysis_data, question_type):
        """Gemini ile yanıt oluştur"""
        if not self.gemini_model:
            return self._create_fallback_response(question, analysis_data, question_type)
        
        try:
            # Soru tipine göre prompt oluştur
            if question_type == 'volume_analysis':
                prompt = f"""
Sen profesyonel bir finans analisti olarak hacim analizi yapıyorsun.

KULLANICI SORUSU: {question}

HACİM ANALİZ VERİLERİ:
{json.dumps(analysis_data, indent=2, ensure_ascii=False)}

Bu verileri kullanarak kullanıcının sorusunu yanıtla:

YANIT KURALLARI:
1. Sadece Türkçe yanıt ver
2. Emoji kullanma
3. Düzyazı şeklinde yaz
4. Sayısal verileri belirt
5. Hacim trendini açıkla
6. Anlaşılır dil kullan
7. Risk uyarısı ekle
8. Maksimum 3-4 paragraf yaz

Yanıtını ver:
"""
            
            elif question_type == 'index_analysis':
                prompt = f"""
Sen profesyonel bir finans analisti olarak endeks analizi yapıyorsun.

KULLANICI SORUSU: {question}

ENDЕKS ANALİZ VERİLERİ:
{json.dumps(analysis_data, indent=2, ensure_ascii=False)}

Bu verileri kullanarak kullanıcının sorusunu yanıtla:

YANIT KURALLARI:
1. Sadece Türkçe yanıt ver
2. Emoji kullanma
3. Düzyazı şeklinde yaz
4. Düşen hisseleri listele
5. Endeks değişimini açıkla
6. Anlaşılır dil kullan
7. Risk uyarısı ekle
8. Maksimum 4-5 paragraf yaz

Yanıtını ver:
"""
            
            elif question_type == 'technical_analysis':
                prompt = f"""
Sen profesyonel bir finans analisti olarak teknik analiz yapıyorsun.

KULLANICI SORUSU: {question}

TEKNİK ANALİZ VERİLERİ:
{json.dumps(analysis_data, indent=2, ensure_ascii=False)}

Bu verileri kullanarak kullanıcının sorusunu yanıtla:

YANIT KURALLARI:
1. Sadece Türkçe yanıt ver
2. Emoji kullanma
3. Düzyazı şeklinde yaz
4. Teknik indikatör değerlerini belirt
5. Sinyalleri açıkla
6. Anlaşılır dil kullan
7. Risk uyarısı ekle
8. Maksimum 4-5 paragraf yaz

Yanıtını ver:
"""
            
            else:
                prompt = f"""
Sen profesyonel bir finans analisti olarak genel finansal soruları yanıtlıyorsun.

KULLANICI SORUSU: {question}

ANALİZ VERİLERİ:
{json.dumps(analysis_data, indent=2, ensure_ascii=False)}

Bu verileri kullanarak kullanıcının sorusunu yanıtla:

YANIT KURALLARI:
1. Sadece Türkçe yanıt ver
2. Emoji kullanma
3. Düzyazı şeklinde yaz
4. Verileri açıkla
5. Anlaşılır dil kullan
6. Risk uyarısı ekle
7. Maksimum 3-4 paragraf yaz

Yanıtını ver:
"""
            
            response = self.gemini_model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            self.logger.error(f"Gemini yanıt oluşturma hatası: {e}")
            return self._create_fallback_response(question, analysis_data, question_type)
    
    def _create_fallback_response(self, question, analysis_data, question_type):
        """Gemini olmadığında fallback yanıt oluştur"""
        try:
            if question_type == 'volume_analysis' and analysis_data:
                symbol = analysis_data.get('symbol', 'Hisse')
                avg_volume = analysis_data.get('average_volume', 0)
                current_volume = analysis_data.get('current_volume', 0)
                volume_change = analysis_data.get('volume_change_percent', 0)
                max_volume = analysis_data.get('max_volume', 0)
                min_volume = analysis_data.get('min_volume', 0)
                volume_volatility = analysis_data.get('volume_volatility', 0)
                
                return f"""{symbol} Hisse Senedi Hacim Analizi

📊 Analiz Dönemi: Son {analysis_data.get('period_months', 6)} ay
📅 Analiz Tarihi: {analysis_data.get('analysis_date', 'Bilinmiyor')}

📈 Hacim İstatistikleri:
• Ortalama hacim: {avg_volume:,} adet
• Güncel hacim: {current_volume:,} adet
• Maksimum hacim: {max_volume:,} adet
• Minimum hacim: {min_volume:,} adet
• Hacim değişimi: %{volume_change:.2f}
• Hacim volatilitesi: %{volume_volatility:.1f}

📊 Trend Analizi:
• Hacim trendi: {analysis_data.get('volume_trend', 'Bilinmiyor')}
• Veri noktası sayısı: {analysis_data.get('data_points', 0)} gün

💡 Yorum:
{self._get_volume_interpretation(volume_change, volume_volatility)}

Risk Uyarısı: Bu analiz sadece bilgilendirme amaçlıdır. Yatırım kararı vermeden önce profesyonel danışmanlık alın."""
            
            elif question_type == 'index_analysis' and analysis_data:
                return f"""BIST 100 Endeks Analizi

Güncel endeks değeri: {analysis_data.get('current_price', 'Bilinmiyor')}
Günlük değişim: %{analysis_data.get('daily_change', 0):.2f}
Düşen hisse sayısı: {analysis_data.get('falling_stocks_count', 0)}

Düşen Hisseler:
{chr(10).join([f"• {stock['symbol']} ({stock['name']}): %{stock['change']:.1f}" for stock in analysis_data.get('falling_stocks', [])])}

Analiz: BIST 100 endeksinin günlük performansı ve düşen hisseler listelendi.

Risk Uyarısı: Bu analiz sadece bilgilendirme amaçlıdır. Yatırım kararı vermeden önce profesyonel danışmanlık alın."""
            
            elif question_type == 'technical_analysis' and analysis_data:
                if 'stocks' in analysis_data:  # Çoklu RSI analizi
                    high_rsi_stocks = analysis_data.get('stocks', [])
                    if high_rsi_stocks:
                        stock_list = chr(10).join([f"• {stock['symbol']}: RSI {stock['rsi']} (Fiyat: {stock['price']} TL)" for stock in high_rsi_stocks])
                        return f"""RSI 70 Üstü Hisseler

Eşik değeri: {analysis_data.get('threshold', 70)}
Yüksek RSI'lı hisse sayısı: {analysis_data.get('high_rsi_count', 0)}

Hisseler:
{stock_list}

Analiz: RSI değeri 70'in üzerinde olan hisseler listelendi. Bu hisseler aşırı alım bölgesinde olabilir.

Risk Uyarısı: Bu analiz sadece bilgilendirme amaçlıdır. Yatırım kararı vermeden önce profesyonel danışmanlık alın."""
                    else:
                        return """RSI Analizi

RSI değeri 70'in üzerinde olan hisse bulunamadı. Bu, piyasanın genel olarak aşırı alım bölgesinde olmadığını gösterebilir.

Risk Uyarısı: Bu analiz sadece bilgilendirme amaçlıdır. Yatırım kararı vermeden önce profesyonel danışmanlık alın."""
                else:  # Tek hisse RSI analizi
                    symbol = analysis_data.get('symbol', 'Hisse')
                    rsi_value = analysis_data.get('current_value', 0)
                    status = analysis_data.get('status', 'Bilinmiyor')
                    signal = analysis_data.get('signal', 'Bilinmiyor')
                    
                    return f"""{symbol} RSI Analizi

Güncel RSI değeri: {rsi_value:.2f}
Durum: {status}
Sinyal: {signal}
Güncel fiyat: {analysis_data.get('current_price', 'Bilinmiyor')} TL

Analiz: {symbol} hisse senedinin RSI değeri hesaplandı ve teknik sinyal analizi yapıldı.

Risk Uyarısı: Bu analiz sadece bilgilendirme amaçlıdır. Yatırım kararı vermeden önce profesyonel danışmanlık alın."""
            
            else:
                return f"""Finansal Analiz

Soru: {question}

Bu soru için detaylı analiz yapılamadı. Lütfen daha spesifik bir soru sorun veya daha sonra tekrar deneyin.

Örnek sorular:
• "Son 6 ayda THYAO'nun ortalama hacmi nedir?"
• "XU100 endeksinden hangi hisseler bugün düştü?"
• "Bana RSI'si 70 üstü olan hisseleri listeler misin?"
• "KCHOL'un RSI değeri nedir?"

Risk Uyarısı: Bu analiz sadece bilgilendirme amaçlıdır. Yatırım kararı vermeden önce profesyonel danışmanlık alın."""
                
        except Exception as e:
            self.logger.error(f"Fallback yanıt oluşturma hatası: {e}")
            return f"Yanıt oluşturulamadı: {str(e)}"
    
    def _get_volume_interpretation(self, volume_change, volume_volatility):
        """Hacim değişimi ve volatiliteye göre yorum oluştur"""
        interpretation = ""
        
        # Hacim değişimi yorumu
        if volume_change > 50:
            interpretation += "Hacimde güçlü artış gözlemleniyor. Bu durum genellikle yüksek piyasa ilgisini gösterir. "
        elif volume_change > 20:
            interpretation += "Hacimde orta düzeyde artış var. Piyasa ilgisi artıyor. "
        elif volume_change > -20:
            interpretation += "Hacimde stabil seyir devam ediyor. "
        elif volume_change > -50:
            interpretation += "Hacimde azalma gözlemleniyor. Piyasa ilgisi düşüyor. "
        else:
            interpretation += "Hacimde belirgin düşüş var. Dikkatli olunmalı. "
        
        # Volatilite yorumu
        if volume_volatility > 0.5:
            interpretation += "Hacim volatilitesi yüksek, bu da belirsizlik göstergesi olabilir. "
        elif volume_volatility > 0.3:
            interpretation += "Orta düzeyde hacim volatilitesi mevcut. "
        else:
            interpretation += "Düşük hacim volatilitesi, stabil seyir devam ediyor. "
        
        return interpretation if interpretation else "Hacim analizi tamamlandı."
    
    def process_financial_question(self, question):
        """Finansal soruyu işle ve yanıt oluştur"""
        try:
            self.logger.info(f"Finansal soru işleniyor: {question}")
            
            # Soru tipini analiz et
            question_type = self.analyze_question_type(question)
            self.logger.info(f"Soru tipi: {question_type}")
            
            # Soru tipine göre analiz yap
            if question_type == 'financial_education':
                # Finansal eğitim
                education_data = self.provide_financial_education(question)
                if education_data:
                    response = education_data['explanation']
                    analysis_data = education_data
                else:
                    response = "Bu konuda eğitim materyali bulunamadı."
                    analysis_data = None
            
            elif question_type == 'volume_analysis':
                # Hacim analizi
                symbol = self.extract_symbol_from_question(question)
                period_months = self.extract_period_from_question(question)
                
                analysis_data = self.analyze_volume(symbol, period_months)
                if analysis_data:
                    response = self.generate_gemini_response(question, analysis_data, question_type)
                else:
                    response = f"{symbol} hisse senedi için hacim verisi bulunamadı."
            
            elif question_type == 'index_analysis':
                # Endeks analizi
                analysis_data = self.analyze_index_components('XU100')
                if analysis_data:
                    response = self.generate_gemini_response(question, analysis_data, question_type)
                else:
                    response = "BIST 100 endeksi verisi bulunamadı."
            
            elif question_type == 'technical_analysis':
                # Teknik indikatör analizi
                if 'rsi' in question.lower() and '70' in question:
                    # Çoklu RSI analizi
                    analysis_data = self.get_multiple_stocks_rsi(70)
                    if analysis_data:
                        response = self.generate_gemini_response(question, analysis_data, question_type)
                    else:
                        response = "RSI analizi yapılamadı."
                else:
                    # Tek hisse teknik analizi
                    symbol = self.extract_symbol_from_question(question)
                    analysis_data = self.analyze_technical_indicators(symbol, 'RSI', 70)
                    if analysis_data:
                        response = self.generate_gemini_response(question, analysis_data, question_type)
                    else:
                        response = f"{symbol} hisse senedi için teknik analiz yapılamadı."
            
            else:
                # Genel finansal soru
                response = self.generate_gemini_response(question, {}, question_type)
            
            return {
                'success': True,
                'question': question,
                'question_type': question_type,
                'response': response,
                'analysis_data': analysis_data if 'analysis_data' in locals() else None
            }
            
        except Exception as e:
            self.logger.error(f"Finansal soru işleme hatası: {e}")
            return {
                'success': False,
                'question': question,
                'error': str(e),
                'response': f"Soru işlenirken hata oluştu: {str(e)}"
            }
    
    def extract_symbol_from_question(self, question):
        """Soru içinden hisse sembolü çıkar"""
        question_upper = question.upper()
        
        for symbol in self.turkish_stocks.keys():
            if symbol in question_upper:
                return symbol
        
        # Varsayılan olarak KCHOL
        return 'KCHOL'
    
    def extract_period_from_question(self, question):
        """Soru içinden süre bilgisini çıkar"""
        question_lower = question.lower()
        
        if '6 ay' in question_lower or '6 ayda' in question_lower:
            return 6
        elif '3 ay' in question_lower or '3 ayda' in question_lower:
            return 3
        elif '1 ay' in question_lower or '1 ayda' in question_lower:
            return 1
        else:
            return 6  # Varsayılan

# Test fonksiyonu
if __name__ == "__main__":
    agent = FinancialQAAgent()
    
    # Test soruları
    test_questions = [
        "Son 6 ayda THYAO'nun ortalama hacmi nedir?",
        "XU100 endeksinden hangi hisseler bugün düştü?",
        "Bana RSI'si 70 üstü olan hisseleri listeler misin?",
        "KCHOL'un RSI değeri nedir?"
    ]
    
    for question in test_questions:
        print(f"\n{'='*50}")
        print(f"SORU: {question}")
        print(f"{'='*50}")
        
        result = agent.process_financial_question(question)
        
        if result['success']:
            print(f"YANIT:\n{result['response']}")
        else:
            print(f"HATA: {result['error']}") 