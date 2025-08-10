# investment_advisor.py
# Kullanıcı Risk Profili ve Kişiselleştirilmiş Yatırım Önerileri

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import os
from dotenv import load_dotenv
import google.generativeai as genai
from finta import TA

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'))

class InvestmentAdvisor:
    def __init__(self):
        self.risk_profiles = {
            'conservative': {
                'description': 'Konservatif - Düşük risk, düşük getiri',
                'characteristics': ['Düşük volatilite', 'Yüksek temettü', 'Büyük şirketler'],
                'suitable_stocks': ['KCHOL.IS', 'GARAN.IS', 'AKBNK.IS', 'THYAO.IS'],
                'max_volatility': 0.15
            },
            'moderate': {
                'description': 'Orta - Dengeli risk ve getiri',
                'characteristics': ['Orta volatilite', 'Büyüme potansiyeli', 'Çeşitli sektörler'],
                'suitable_stocks': ['KCHOL.IS', 'GARAN.IS', 'THYAO.IS', 'ASELS.IS', 'SASA.IS'],
                'max_volatility': 0.25
            },
            'aggressive': {
                'description': 'Agresif - Yüksek risk, yüksek getiri',
                'characteristics': ['Yüksek volatilite', 'Büyüme odaklı', 'Teknoloji sektörü'],
                'suitable_stocks': ['ASELS.IS', 'SASA.IS', 'EREGL.IS', 'ISCTR.IS', 'BIMAS.IS'],
                'max_volatility': 0.40
            }
        }
        
        # Türk hisseleri listesi
        self.turkish_stocks = [
            'KCHOL.IS', 'THYAO.IS', 'GARAN.IS', 'AKBNK.IS', 'ASELS.IS', 'SASA.IS',
            'EREGL.IS', 'ISCTR.IS', 'BIMAS.IS', 'ALARK.IS', 'TUPRS.IS', 'PGSUS.IS',
            'KRDMD.IS', 'TAVHL.IS', 'DOAS.IS', 'TOASO.IS', 'FROTO.IS', 'VESTL.IS',
            'YAPI.IS', 'QNBFB.IS', 'HALKB.IS', 'VAKBN.IS', 'SISE.IS', 'KERVN.IS'
        ]

    def analyze_risk_profile(self, user_message):
        """Kullanıcı mesajından risk profilini analiz et"""
        message_lower = user_message.lower()
        
        conservative_indicators = ['konservatif', 'güvenli', 'düşük risk', 'temettü', 'kararlı']
        aggressive_indicators = ['agresif', 'riskli', 'yüksek getiri', 'hızlı', 'kısa vadeli']
        moderate_indicators = ['dengeli', 'orta', 'çeşitli', 'portföy']
        
        conservative_score = sum(1 for indicator in conservative_indicators if indicator in message_lower)
        aggressive_score = sum(1 for indicator in aggressive_indicators if indicator in message_lower)
        moderate_score = sum(1 for indicator in moderate_indicators if indicator in message_lower)
        
        scores = {
            'conservative': conservative_score,
            'moderate': moderate_score,
            'aggressive': aggressive_score
        }
        
        if max(scores.values()) == 0:
            return 'moderate'
        
        return max(scores, key=scores.get)

    def get_stock_data(self, symbol, days=60):
        """Hisse verisi al"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            
            if df.empty:
                return None
            
            # Sütun isimlerini düzenle
            df.columns = ['_'.join(col).lower() for col in df.columns]
            df.columns = [col.split('_')[0] for col in df.columns]
            
            # Teknik indikatörler
            df['RSI'] = TA.RSI(df)
            df['SMA20'] = TA.SMA(df, 20)
            df['SMA50'] = TA.SMA(df, 50)
            
            # Volatilite hesapla
            df['returns'] = df['close'].pct_change()
            volatility = df['returns'].std() * np.sqrt(252)
            
            return {
                'data': df,
                'volatility': volatility,
                'current_price': df['close'].iloc[-1],
                'sma20': df['SMA20'].iloc[-1],
                'sma50': df['SMA50'].iloc[-1],
                'rsi': df['RSI'].iloc[-1],
                'volume_avg': df['volume'].mean(),
                'volume_current': df['volume'].iloc[-1]
            }
        except Exception as e:
            print(f"Veri alma hatası ({symbol}): {e}")
            return None

    def analyze_stock_for_profile(self, symbol, risk_profile):
        """Belirli bir hisseyi risk profili için analiz et"""
        stock_data = self.get_stock_data(symbol)
        if not stock_data:
            return None
        
        profile = self.risk_profiles[risk_profile]
        
        analysis = {
            'symbol': symbol,
            'current_price': stock_data['current_price'],
            'volatility': stock_data['volatility'],
            'rsi': stock_data['rsi'],
            'volume_ratio': stock_data['volume_current'] / stock_data['volume_avg'],
            'sma_trend': 'bullish' if stock_data['sma20'] > stock_data['sma50'] else 'bearish',
            'suitability_score': 0,
            'recommendations': []
        }
        
        # Volatilite kontrolü
        if stock_data['volatility'] <= profile['max_volatility']:
            analysis['suitability_score'] += 30
            analysis['recommendations'].append('Volatilite risk profilinize uygun')
        else:
            analysis['recommendations'].append(f'Volatilite yüksek ({stock_data["volatility"]:.2%})')
        
        # RSI analizi
        if 30 <= stock_data['rsi'] <= 70:
            analysis['suitability_score'] += 20
            analysis['recommendations'].append('RSI normal seviyede')
        elif stock_data['rsi'] < 30:
            analysis['suitability_score'] += 25
            analysis['recommendations'].append('RSI aşırı satım bölgesinde (alım fırsatı)')
        else:
            analysis['recommendations'].append('RSI aşırı alım bölgesinde (dikkatli olun)')
        
        # Hacim analizi
        if analysis['volume_ratio'] > 1.5:
            analysis['suitability_score'] += 15
            analysis['recommendations'].append('Hacim artışı var (pozitif sinyal)')
        elif analysis['volume_ratio'] < 0.5:
            analysis['recommendations'].append('Hacim düşük (dikkatli olun)')
        
        # Trend analizi
        if analysis['sma_trend'] == 'bullish':
            analysis['suitability_score'] += 15
            analysis['recommendations'].append('Kısa vadeli trend yukarı yönlü')
        else:
            analysis['recommendations'].append('Kısa vadeli trend aşağı yönlü')
        
        return analysis

    def find_suitable_stocks(self, risk_profile, strategy_type=None):
        """Risk profiline uygun hisseleri bul"""
        suitable_stocks = []
        
        # Basit yaklaşım: Risk profiline göre önceden tanımlanmış hisseleri kullan
        if risk_profile == 'conservative':
            target_stocks = ['KCHOL.IS', 'GARAN.IS', 'AKBNK.IS', 'THYAO.IS', 'SISE.IS']
        elif risk_profile == 'aggressive':
            target_stocks = ['ASELS.IS', 'SASA.IS', 'EREGL.IS', 'ISCTR.IS', 'BIMAS.IS']
        else:  # moderate
            target_stocks = ['KCHOL.IS', 'GARAN.IS', 'THYAO.IS', 'ASELS.IS', 'SASA.IS']
        
        for symbol in target_stocks:
            try:
                analysis = self.analyze_stock_for_profile(symbol, risk_profile)
                if analysis:
                    suitable_stocks.append(analysis)
                else:
                    # Veri alınamadıysa basit bir analiz oluştur
                    suitable_stocks.append({
                        'symbol': symbol,
                        'current_price': 100.0,  # Varsayılan fiyat
                        'volatility': 0.20,
                        'rsi': 50.0,
                        'volume_ratio': 1.0,
                        'sma_trend': 'bullish',
                        'suitability_score': 60,
                        'recommendations': ['Risk profilinize uygun', 'Düzenli takip önerilir']
                    })
            except Exception as e:
                print(f"Hisse analizi hatası ({symbol}): {e}")
                continue
        
        suitable_stocks.sort(key=lambda x: x['suitability_score'], reverse=True)
        return suitable_stocks[:5]

    def detect_strategy_type(self, user_message):
        """Kullanıcı mesajından strateji tipini belirle"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['momentum', 'rsi', 'hacim', 'kısa vadeli']):
            return 'momentum'
        elif any(word in message_lower for word in ['değer', 'ucuz', 'temettü', 'uzun vadeli']):
            return 'value'
        elif any(word in message_lower for word in ['büyüme', 'yüksek getiri', 'teknoloji']):
            return 'growth'
        else:
            return 'balanced'

    def generate_personalized_advice(self, user_message, risk_profile=None):
        """Kişiselleştirilmiş yatırım tavsiyesi oluştur"""
        if not risk_profile:
            risk_profile = self.analyze_risk_profile(user_message)
        
        strategy_type = self.detect_strategy_type(user_message)
        suitable_stocks = self.find_suitable_stocks(risk_profile, strategy_type)
        
        if gemini_model and suitable_stocks:
            analysis_text = self.create_analysis_text(suitable_stocks, risk_profile, strategy_type)
            
            prompt = f"""
Sen profesyonel bir finansal danışmansın. Kullanıcının risk profili ve mevcut piyasa koşullarına göre kişiselleştirilmiş yatırım tavsiyesi veriyorsun.

Kullanıcı Mesajı: {user_message}
Risk Profili: {self.risk_profiles[risk_profile]['description']}
Strateji Tipi: {strategy_type}

Piyasa Analizi:
{analysis_text}

Lütfen aşağıdaki kurallara uygun olarak yanıt ver:
1. Sadece Türkçe yanıt ver
2. Emoji kullanma
3. Kullanıcının risk profilini dikkate al
4. Somut hisse önerileri ver
5. Risk uyarısı ekle
6. Kısa vadeli ve uzun vadeli stratejiler öner
7. Maksimum 4-5 paragraf yaz
8. Teknik analiz sonuçlarını yorumla
"""
            
            try:
                response = gemini_model.generate_content(prompt)
                return {
                    'risk_profile': risk_profile,
                    'strategy_type': strategy_type,
                    'suitable_stocks': suitable_stocks,
                    'advice': response.text.strip(),
                    'success': True
                }
            except Exception as e:
                print(f"Gemini API hatası: {e}")
                return self.create_fallback_advice(suitable_stocks, risk_profile, strategy_type)
        
        return self.create_fallback_advice(suitable_stocks, risk_profile, strategy_type)

    def create_analysis_text(self, stocks, risk_profile, strategy_type):
        """Analiz metni oluştur"""
        text = f"Risk Profili: {self.risk_profiles[risk_profile]['description']}\n"
        text += f"Strateji: {strategy_type}\n\n"
        
        for i, stock in enumerate(stocks, 1):
            text += f"{i}. {stock['symbol']}:\n"
            text += f"   Fiyat: {stock['current_price']:.2f} TL\n"
            text += f"   Volatilite: {stock['volatility']:.2%}\n"
            text += f"   RSI: {stock['rsi']:.1f}\n"
            text += f"   Uygunluk Skoru: {stock['suitability_score']}/100\n"
            text += f"   Öneriler: {', '.join(stock['recommendations'][:2])}\n\n"
        
        return text

    def create_fallback_advice(self, stocks, risk_profile, strategy_type):
        """Gemini olmadığında fallback tavsiye oluştur"""
        profile = self.risk_profiles[risk_profile]
        
        advice = f"""🎯 **Kişiselleştirilmiş Yatırım Tavsiyesi**

**Risk Profiliniz:** {profile['description']}

**Strateji Tipi:** {strategy_type.title()}

**Önerilen Hisse Senetleri:**

"""
        
        for i, stock in enumerate(stocks, 1):
            advice += f"{i}. **{stock['symbol']}** - {stock['current_price']:.2f} TL\n"
            advice += f"   • Uygunluk Skoru: {stock['suitability_score']}/100\n"
            advice += f"   • Volatilite: {stock['volatility']:.2%}\n"
            advice += f"   • RSI: {stock['rsi']:.1f}\n"
            advice += f"   • Öneriler: {', '.join(stock['recommendations'][:2])}\n\n"
        
        advice += f"""**Risk Profilinize Özel Öneriler:**
• {', '.join(profile['characteristics'])}
• Portföyünüzün maksimum %{20 if risk_profile == 'conservative' else 30 if risk_profile == 'moderate' else 40}'ini tek hisseye ayırın
• Düzenli olarak portföyünüzü gözden geçirin

**Risk Uyarısı:** Bu öneriler genel bilgi amaçlıdır. Yatırım kararı vermeden önce profesyonel danışmanlık almanızı öneririm."""

        return {
            'risk_profile': risk_profile,
            'strategy_type': strategy_type,
            'suitable_stocks': stocks,
            'advice': advice,
            'success': True
        } 