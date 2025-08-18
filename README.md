# Fintra - Finansal Yatırım Asistanı

FintraBot, kullanıcıların finansal sorularına yanıt veren, piyasa analizi yapan ve  kişiselleştirilmiş finansal tavsiyelerde bulunan bir chatbot'tur

## Proje Özeti


### Ana Hedefler
- **Demokratikleştirme**: Profesyonel finansal analiz araçlarını bireysel yatırımcılara sunma
- **Otomasyon**: Manuel analiz süreçlerini otomatikleştirerek zaman tasarrufu sağlama
- **Eğitim**: Finansal okuryazarlığı artırmak için eğitici içerik ve rehberlik
- **Entegrasyon**: Tek platformda tüm yatırım ihtiyaçlarını karşılama

### Hedef Kitle
- **Bireysel Yatırımcılar**: Hisse senedi piyasasında aktif olan kişiler
- **Yeni Başlayanlar**: Finansal piyasaları öğrenmek isteyenler
- **Orta Seviye Yatırımcılar**: Teknik analiz ve portföy yönetimi konularında derinleşmek isteyenler
- **Finansal Danışmanlar**: Müşterilerine daha iyi hizmet vermek isteyen profesyoneller

### Platform Özellikleri
Platform, teknik analiz, haber analizi, portföy yönetimi, finansal takvim ve yapay zeka destekli asistan özelliklerini tek bir entegre sistemde birleştirir. Kullanıcılar doğal dil ile sorularını sorabilir, otomatik fiyat tahminleri alabilir, portföylerini takip edebilir ve finansal olaylar hakkında uyarı alabilirler.
Aynı zamanda hisse simulasyonu yaparak kar zarar oranlarını tahmin edebilmektedir.

### Teknoloji Yaklaşımı
- **Makine Öğrenmesi**: XGBoost ile fiyat tahmini ve teknik analiz
- **Yapay Zeka**: Gemini AI ile doğal dil işleme ve akıllı yanıtlar
- **RAG Sistemi**: Belge tabanlı bilgi çıkarma ve indeksleme
- **AI Agent'ları**: Özelleştirilmiş finansal analiz ve portföy yönetimi agent'ları
- **Real-time Data**: Canlı piyasa verileri ve anlık güncellemeler
- **Modüler Mimari**: Genişletilebilir ve sürdürülebilir kod yapısı
- **Web Teknolojileri**: Flask backend ve modern frontend framework'leri

## Temel Özellikler

### Fiyat Tahmini ve Analiz
- **Makine Öğrenmesi Modeli**: 300 günlük geçmiş veri ile eğitilmiş, %85+ doğruluk oranı
- **Gerçek Zamanlı Veri**: yfinance API ile canlı hisse senedi verileri
- **Teknik İndikatör Analizi**: RSI, MACD, SMA (20, 50, 200 günlük), Bollinger Bands, Williams %R, ATR
- **Sentiment Analizi**: News API ile haber analizi ve TextBlob ile duygu analizi
- **Fiyat Düzeltmesi**: Haber sentiment skoruna göre otomatik fiyat tahmini düzeltmesi
- **Trend Yönü Belirleme**: Yükseliş/düşüş trendi ve güven seviyesi hesaplama

### Teknik Analiz Motoru
- **Gelişmiş Grafik Sistemi**: Matplotlib ve Plotly ile interaktif grafikler
- **Çoklu Zaman Dilimi**: Günlük, haftalık, aylık analiz seçenekleri
- **Otomatik Sinyal Üretimi**: RSI aşırı alım/satım, MACD kesişim, Bollinger Bands kırılım sinyalleri
- **Destek ve Direnç Seviyeleri**: Otomatik pivot noktası hesaplama
- **Hacim Analizi**: Hacim bazlı trend doğrulama ve anomali tespiti
- **Volatilite Hesaplama**: ATR ile volatilite analizi ve risk değerlendirmesi

### Finansal Takvim ve Alarm Sistemi
- **BIST Şirket Takibi**: THYAO, KCHOL, GARAN, AKBNK, ISCTR, ASELS, EREGL, SASA ve 20+ şirket
- **Olay Türleri**: Bilanço açıklama, genel kurul, temettü ödemesi, KAP duyuruları
- **Akıllı Alarm Sistemi**: Olay tarihinden 1-7 gün önce otomatik uyarı
- **CSV Import/Export**: Toplu veri yükleme ve dışa aktarma
- **Web Scraping**: Otomatik veri güncelleme ve senkronizasyon
- **Filtreleme ve Arama**: Tarih, şirket ve olay türüne göre filtreleme

### Portföy Yönetimi
- **Çoklu Hisse Takibi**: Sınırsız hisse senedi ekleme ve takip
- **Otomatik Hesaplama**: Gerçek zamanlı kar/zarar, getiri oranı, ortalama maliyet
- **Risk Analizi**: Portföy çeşitlendirme skoru ve risk metrikleri
- **Performans Simülasyonu**: "Ne olurdu" senaryoları ile geçmiş yatırım analizi
- **Portföy Özeti**: Toplam değer, günlük değişim, en iyi/kötü performans gösteren hisseler
- **Dışa Aktarma**: Portföy verilerini CSV ve JSON formatında indirme

### Yapay Zeka Destekli Asistan
- **Gemini AI Entegrasyonu**: Google'ın en gelişmiş AI modeli ile doğal dil işleme
- **Finansal Eğitim Sistemi**: RSI, MACD, volatilite gibi kavramların açıklanması
- **Kişiselleştirilmiş Tavsiyeler**: Risk profili ve yatırım hedeflerine göre öneriler
- **Belge Tabanlı Bilgi**: PDF, CSV, TXT dosyalarından bilgi çıkarma (RAG)
- **Çok Dilli Destek**: Türkçe ağırlıklı, İngilizce destekli,ses ile yazma 
- **Akıllı Soru Cevaplama**: Finansal terimler ve kavramlar hakkında detaylı açıklamalar

### Web Arayüzü ve Kullanıcı Deneyimi
- **Modern Tasarım**: Material Design prensipleri ile responsive arayüz
- **Gerçek Zamanlı Sohbet**: WebSocket benzeri hızlı mesajlaşma
- **Sohbet Geçmişi**: Oturum bazlı sohbet kaydetme ve yönetimi
- **Çoklu Format Dışa Aktarma**: TXT, JSON, HTML formatlarında sohbet indirme
- **Tema Sistemi**: Açık/koyu tema ve özelleştirilebilir renkler
- **Mobil Uyumluluk**: Tüm cihazlarda optimize edilmiş görünüm

### Gelişmiş Analiz Özellikleri
- **Haber Sentiment Analizi**: Koç Holding ve bağlı şirketler hakkında haber analizi
- **Şirket Bazlı Filtreleme**: Belirli şirketler hakkında özelleştirilmiş analiz
- **Teknik Gösterge Kombinasyonu**: Birden fazla göstergeyi birleştirerek sinyal üretimi
- **Otomatik Raporlama**: Günlük, haftalık analiz raporları

### Veri Yönetimi ve Güvenlik
- **SQLite Veritabanı**: Hafif ve hızlı veri saklama
- **Otomatik Yedekleme**: Kritik verilerin otomatik yedeklenmesi
- **API Rate Limiting**: API kullanımında aşırı yüklenmeyi önleme
- **Hata Yönetimi**: Kapsamlı hata yakalama ve kullanıcı dostu mesajlar
- **Log Sistemi**: Detaylı işlem kayıtları ve debug bilgileri
- **Çevre Değişkenleri**: Güvenli API anahtarı yönetimi

## Teknik Detaylar

### Kullanılan Teknolojiler
- **Backend**: Flask (Python)
- **Makine Öğrenmesi**: XGBoost, Scikit-learn
- **Veri Analizi**: Pandas, NumPy, yfinance
- **Teknik Analiz**: Finta, TA-Lib
- **Yapay Zeka**: Google Gemini AI
- **RAG Sistemi**: Document processing ve vector indexing
- **AI Agents**: Özelleştirilmiş finansal analiz agent'ları
- **Veritabanı**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Grafik**: Matplotlib, Plotly


## Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.8+
- pip paket yöneticisi
- Google Gemini API anahtarı

### Kurulum Adımları

1. **Repository'yi klonlayın**
```bash
git clone https://github.com/Sarizeybekk/fintechBot.git
cd fintechBot
```

2. **Sanal ortam oluşturun**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate     # Windows
```

3. **Bağımlılıkları yükleyin**
```bash
pip install -r requirements.txt
```

4. **Çevre değişkenlerini ayarlayın**
```bash
cp .env.example .env
# .env dosyasını düzenleyerek API anahtarlarınızı ekleyin
```

5. **Uygulamayı çalıştırın**
```bash
python app.py
```

Uygulama http://localhost:3005 adresinde çalışmaya başlayacaktır.

### Çevre Değişkenleri
```env
GOOGLE_API_KEY=your_gemini_api_key
NEWS_API_KEY=your_news_api_key
GEMINI_MODEL=gemini-1.5-flash
```

## Kullanım Örnekleri

### Fiyat Tahmini ve Analiz
```
"KCHOL hisse senedi için fiyat tahmini yap"
"KCHOL bugün neden düştü?"

```

### Teknik Analiz ve Grafikler
```
"KCHOL için teknik analiz yap"
"RSI analizi göster"
"MACD göstergesi nedir?"
"Bollinger Bands analizi yap"
"KCHOL'da destek ve direnç seviyeleri neler?"
```

### Portföy Simülasyonu ve Analiz
```
"KCHOL'a 6 ay önce 10.000 TL yatırsaydım ne olurdu?"
"THYAO'ya 1 yıl önce 50.000 TL yatırım simülasyonu"
"GARAN'a 3 ay önce 25.000 TL yatırsaydım kaç para kazanırdım?"
"AKBNK'ya 2023 başında 100.000 TL yatırım simülasyonu"
"Portföyümde en iyi performans gösteren hisse hangisi?"
"Risk analizi yap"
```

### Finansal Takvim ve Alarmlar
```
"THYAO bilançosu ne zaman?"
"KCHOL genel kurul tarihi"
"GARAN temettü ödemesi ne zaman?"
"KCHOL bilançosu için 1 gün önce uyar"
"THYAO genel kurulu için 3 gün önce alarm kur"
"Bu ay hangi şirketlerde önemli olaylar var?"
"Yaklaşan finansal olayları listele"
```

### Haber Analizi ve Sentiment
```
"KCHOL hakkında son haberleri analiz et"
"Koç Holding ile ilgili haber sentiment'i nedir?"
"Haber analizi yap"
```

### Finansal Eğitim ve Q&A
```
"RSI nedir ve nasıl yorumlanır?"
"Volatilite yüksek ne demek?"
"SMA 50 ve SMA 200 neyi ifade eder?"
"Stop-loss nasıl belirlenir?"
"Portföy çeşitlendirmesi neden önemli?"
"Risk yönetimi nasıl yapılır?"
```

### Kişiselleştirilmiş Yatırım Tavsiyeleri
```
"Konservatif yatırımcı için öneriler"
"Agresif yatırım stratejisi öner"
"Uzun vadeli yatırım için hangi hisseler uygun?"
"Kısa vadeli trading için strateji öner"
"Risk toleransıma göre portföy önerisi"
"Düşüşte alım stratejisi nasıl uygulanır?"
```


### Gelişmiş Analiz Sorguları
```
"Son 6 ayda THYAO'nun ortalama hacmi nedir?"
"Bana RSI'si 70 üstü olan hisseleri listeler misin?"
"KCHOL'un RSI değeri nedir?"
"GARAN'ın son 3 aylık hacim analizi"
"BIST'te en çok işlem gören hisseler hangileri?"
"Volatilitesi en yüksek hisseler neler?"
```

## Özellik Detayları

### Makine Öğrenmesi Modeli
- **XGBoost Algoritması**: Gradient boosting framework ile yüksek performans
- **Veri Seti**: 300 günlük OHLCV verisi + 10 teknik gösterge
- **Özellik Mühendisliği**: Fiyat, hacim, momentum ve volatilite özellikleri
- **Model Performansı**: %85+ doğruluk oranı, RMSE < 2.5
- **Otomatik Güncelleme**: Haftalık model yeniden eğitimi
- **Overfitting Önleme**: Cross-validation ve regularization teknikleri

### Teknik Analiz Motoru
- **25+ Teknik Gösterge**: RSI, MACD, SMA, EMA, Bollinger Bands, Williams %R, ATR, Stochastic, CCI
- **Çoklu Zaman Dilimi**: 1 dakika, 5 dakika, 15 dakika, 1 saat, günlük, haftalık
- **Otomatik Sinyal Sistemi**: Golden Cross, Death Cross, RSI divergence, MACD crossover
- **Görsel Analiz**: Candlestick, line, area, volume grafikleri
- **Destek/Direnç**: Fibonacci retracement, pivot points, trend lines
- **Hacim Profili**: Volume Weighted Average Price (VWAP), On-Balance Volume (OBV)

### Haber Analizi ve Sentiment
- **News API Entegrasyonu**: 7 günlük geriye dönük haber analizi
- **Sentiment Analizi**: TextBlob ile -1 ile +1 arası skorlama
- **Şirket Filtreleme**: Koç Holding, Arçelik, Tofaş, Ford Otosan, Yapı Kredi
- **Fiyat Entegrasyonu**: Sentiment skoruna göre %2'ye kadar fiyat düzeltmesi
- **Haber Kategorilendirme**: Finansal, operasyonel, yönetimsel olaylar
- **Trend Analizi**: Haber sentiment trendi ve fiyat korelasyonu

### Portföy Simülasyonu ve Yönetimi
- **Geçmiş Senaryolar**: "Ne olurdu" analizi ile alternatif yatırım karşılaştırması
- **Kar/Zarar Hesaplama**: Gerçek zamanlı P&L, getiri oranı, Sharpe ratio
- **Risk Metrikleri**: Value at Risk (VaR), Maximum Drawdown, Beta hesaplama
- **Portföy Çeşitlendirme**: Sektör, büyüklük, coğrafi dağılım analizi
- **Performans Benchmark**: BIST100, BIST30, sektör endeksleri ile karşılaştırma
- **Dışa Aktarma**: CSV, JSON, PDF formatlarında rapor oluşturma

### Finansal Takvim Sistemi
- **20+ BIST Şirketi**: THYAO, KCHOL, GARAN, AKBNK, ISCTR, ASELS, EREGL, SASA, BİMAS, ALARK, TUPRS
- **Olay Kategorileri**: Bilanço, genel kurul, temettü, KAP duyuruları, özel olaylar
- **Akıllı Alarmlar**: 1-7 gün öncesinden uyarı, email/SMS entegrasyonu hazır
- **Web Scraping**: KAP, şirket web siteleri ve finansal haber kaynakları
- **CSV Import/Export**: Toplu veri yükleme, Excel uyumlu format
- **Filtreleme**: Tarih aralığı, şirket, olay türü, durum bazında arama

### Yapay Zeka Asistan Sistemi
- **Gemini AI Modeli**: Google'ın en gelişmiş multimodal AI modeli
- **Doğal Dil İşleme**: Türkçe ağırlıklı, finansal terminoloji uzmanlığı
- **RAG Sistemi**: PDF, CSV, TXT dosyalarından bilgi çıkarma ve indeksleme
- **Kişiselleştirme**: Risk profili, yatırım hedefleri, deneyim seviyesi
- **Eğitim Modülü**: Finansal kavramlar, teknik analiz, risk yönetimi
- **Çok Dilli Destek**: Türkçe, İngilizce sesli komut destegiyle kullanıcıya kolaylık sağlar.




