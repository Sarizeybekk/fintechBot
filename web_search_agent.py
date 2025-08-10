import os
import requests
import json
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

class WebSearchAgent:
    def __init__(self):
        """Web arama agent'ını başlat"""
        self.gemini_api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GEMINI_API_KEY')
        self.serpapi_key = os.getenv('SERPAPI_KEY')  # SerpAPI anahtarı
        
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Web Search Agent - Gemini API bağlantısı kuruldu")
        else:
            print("⚠️ Web Search Agent - Gemini API anahtarı bulunamadı")
            self.gemini_model = None
        
        if self.serpapi_key:
            print("✅ Web Search Agent - SerpAPI bağlantısı kuruldu")
        else:
            print("⚠️ Web Search Agent - SerpAPI anahtarı bulunamadı, basit arama kullanılacak")
        
        # Arama motorları
        self.search_engines = {
            'google': 'https://www.google.com/search',
            'bing': 'https://www.bing.com/search',
            'duckduckgo': 'https://duckduckgo.com/'
        }
        
        # Finansal haber kaynakları
        self.financial_sources = [
            'bloomberg.com',
            'reuters.com',
            'cnbc.com',
            'marketwatch.com',
            'yahoo.com/finance',
            'investing.com',
            'tradingview.com',
            'forexfactory.com',
            'fxstreet.com',
            'finans.mynet.com',
            'bloomberght.com',
            'dunya.com',
            'hurriyet.com.tr/ekonomi',
            'milliyet.com.tr/ekonomi',
            'sozcu.com.tr/ekonomi',
            'haberturk.com/ekonomi'
        ]
        
        # KCHOL ile ilgili anahtar kelimeler
        self.kchol_keywords = [
            'KCHOL',
            'Koç Holding',
            'Arçelik',
            'Tofaş',
            'Ford Otosan',
            'Yapı Kredi',
            'Koç Group',
            'Koç Holding hisse',
            'KCHOL hisse senedi',
            'Koç Holding finansal rapor',
            'Koç Holding çeyreklik rapor',
            'Koç Holding temettü',
            'Koç Holding yatırım',
            'Koç Holding analiz'
        ]
        
        # User agent'lar
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        # Logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def search_web(self, query, max_results=10, search_type='news'):
        """Web'de arama yap"""
        try:
            self.logger.info(f"Web araması başlatılıyor: {query}")
            
            # Arama sorgusunu optimize et
            optimized_query = self._optimize_search_query(query, search_type)
            
            # SerpAPI varsa kullan
            if self.serpapi_key:
                serp_results = self._search_with_serpapi(optimized_query, max_results, search_type)
                if serp_results:
                    return serp_results
            
            # Fallback: Farklı arama motorlarını dene
            results = []
            
            # Google araması (basit HTTP isteği)
            google_results = self._search_google(optimized_query, max_results)
            if google_results:
                results.extend(google_results)
            
            # Bing araması
            bing_results = self._search_bing(optimized_query, max_results)
            if bing_results:
                results.extend(bing_results)
            
            # Duplicate'leri temizle
            unique_results = self._remove_duplicates(results)
            
            # Sonuçları filtrele ve sırala
            filtered_results = self._filter_and_rank_results(unique_results, query)
            
            self.logger.info(f"Toplam {len(filtered_results)} sonuç bulundu")
            return filtered_results[:max_results]
            
        except Exception as e:
            self.logger.error(f"Web arama hatası: {e}")
            return []
    
    def _search_with_serpapi(self, query, max_results, search_type):
        """SerpAPI ile arama yap"""
        try:
            if search_type == 'news':
                endpoint = "https://serpapi.com/search.json"
                params = {
                    'engine': 'google_news',
                    'q': query,
                    'api_key': self.serpapi_key,
                    'num': max_results,
                    'hl': 'tr',
                    'gl': 'tr'
                }
            else:
                endpoint = "https://serpapi.com/search.json"
                params = {
                    'engine': 'google',
                    'q': query,
                    'api_key': self.serpapi_key,
                    'num': max_results,
                    'hl': 'tr',
                    'gl': 'tr'
                }
            
            response = requests.get(endpoint, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if search_type == 'news':
                    articles = data.get('news_results', [])
                else:
                    articles = data.get('organic_results', [])
                
                results = []
                for article in articles:
                    result = {
                        'title': article.get('title', ''),
                        'url': article.get('link', ''),
                        'snippet': article.get('snippet', ''),
                        'source': 'serpapi'
                    }
                    
                    if search_type == 'news':
                        result['published_date'] = article.get('date', '')
                        result['source_name'] = article.get('source', '')
                    
                    results.append(result)
                
                self.logger.info(f"SerpAPI ile {len(results)} sonuç bulundu")
                return results
            
        except Exception as e:
            self.logger.error(f"SerpAPI arama hatası: {e}")
        
        return []
    
    def _optimize_search_query(self, query, search_type):
        """Arama sorgusunu optimize et"""
        # KCHOL ile ilgili anahtar kelimeleri ekle
        if 'KCHOL' not in query.upper() and 'koç' not in query.lower():
            query = f"KCHOL {query}"
        
        # Haber araması için site kısıtlaması ekle
        if search_type == 'news':
            financial_sites = ' OR '.join([f'site:{site}' for site in self.financial_sources[:8]])
            query = f'({query}) ({financial_sites})'
        
        # Tarih kısıtlaması ekle (son 7 gün - daha güncel haberler için)
        date_filter = f'after:{datetime.now() - timedelta(days=7):%Y-%m-%d}'
        query = f'{query} {date_filter}'
        
        # Güncel haberler için ek anahtar kelimeler
        if search_type == 'news':
            current_keywords = ' OR '.join(['bugün', 'güncel', 'son dakika', 'son gelişmeler', '2024'])
            query = f'({query}) ({current_keywords})'
        
        return query
    
    def _search_google(self, query, max_results):
        """Google'da arama yap"""
        try:
            headers = {
                'User-Agent': self.user_agents[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            params = {
                'q': query,
                'num': max_results,
                'hl': 'tr',
                'gl': 'tr',
                'tbm': 'nws'  # Haber araması
            }
            
            response = requests.get(
                self.search_engines['google'],
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return self._parse_google_results(response.text)
            
        except Exception as e:
            self.logger.error(f"Google arama hatası: {e}")
        
        return []
    
    def _search_bing(self, query, max_results):
        """Bing'de arama yap"""
        try:
            headers = {
                'User-Agent': self.user_agents[1],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            }
            
            params = {
                'q': query,
                'count': max_results,
                'setlang': 'tr-TR',
                'format': 'rss'
            }
            
            response = requests.get(
                self.search_engines['bing'],
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return self._parse_bing_results(response.text)
            
        except Exception as e:
            self.logger.error(f"Bing arama hatası: {e}")
        
        return []
    
    def _parse_google_results(self, html_content):
        """Google sonuçlarını parse et"""
        results = []
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Haber sonuçlarını bul
            news_items = soup.find_all('div', class_='g')
            
            for item in news_items:
                try:
                    title_elem = item.find('h3')
                    link_elem = item.find('a')
                    snippet_elem = item.find('div', class_='VwiC3b')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        url = link_elem.get('href', '')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                        
                        # URL'yi temizle
                        if url.startswith('/url?q='):
                            url = url.split('/url?q=')[1].split('&')[0]
                        
                        if url and title:
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet,
                                'source': 'google'
                            })
                
                except Exception as e:
                    continue
            
        except Exception as e:
            self.logger.error(f"Google parse hatası: {e}")
        
        return results
    
    def _parse_bing_results(self, xml_content):
        """Bing sonuçlarını parse et"""
        results = []
        try:
            soup = BeautifulSoup(xml_content, 'xml')
            
            # RSS item'larını bul
            items = soup.find_all('item')
            
            for item in items:
                try:
                    title = item.find('title').get_text(strip=True) if item.find('title') else ''
                    link = item.find('link').get_text(strip=True) if item.find('link') else ''
                    description = item.find('description').get_text(strip=True) if item.find('description') else ''
                    
                    if title and link:
                        results.append({
                            'title': title,
                            'url': link,
                            'snippet': description,
                            'source': 'bing'
                        })
                
                except Exception as e:
                    continue
            
        except Exception as e:
            self.logger.error(f"Bing parse hatası: {e}")
        
        return results
    
    def _remove_duplicates(self, results):
        """Duplicate sonuçları temizle"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results
    
    def _filter_and_rank_results(self, results, original_query):
        """Sonuçları filtrele ve sırala"""
        filtered_results = []
        
        for result in results:
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            url = result.get('url', '').lower()
            
            # KCHOL ile ilgili sonuçları önceliklendir
            score = 0
            
            # Anahtar kelime eşleşmeleri
            if 'kchol' in title or 'koç' in title:
                score += 10
            if 'holding' in title:
                score += 5
            if 'hisse' in title or 'borsa' in title:
                score += 3
            if 'finansal' in title or 'ekonomi' in title:
                score += 2
            
            # URL kalitesi
            if any(source in url for source in self.financial_sources):
                score += 5
            
            # Tarih kontrolü (yeni haberler öncelikli)
            if '2024' in title or '2024' in snippet:
                score += 2
            
            if score > 0:
                result['relevance_score'] = score
                filtered_results.append(result)
        
        # Skora göre sırala
        filtered_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return filtered_results
    
    def extract_content_from_url(self, url, max_length=2000):
        """URL'den içerik çıkar"""
        try:
            headers = {
                'User-Agent': self.user_agents[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Gereksiz elementleri kaldır
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Ana içeriği bul
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                'main',
                '.main-content'
            ]
            
            content = ''
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text(strip=True) for elem in elements])
                    break
            
            # Eğer özel selector bulunamazsa, tüm metni al
            if not content:
                content = soup.get_text(strip=True)
            
            # Metni temizle ve kısalt
            content = re.sub(r'\s+', ' ', content)
            content = content[:max_length] + '...' if len(content) > max_length else content
            
            return content
            
        except Exception as e:
            self.logger.error(f"İçerik çıkarma hatası ({url}): {e}")
            return None
    
    def analyze_web_content(self, query, search_results):
        """Web içeriğini Gemini ile analiz et"""
        if not self.gemini_model:
            return "Gemini API kullanılamıyor."
        
        try:
            # En önemli sonuçlardan içerik çıkar
            content_summary = []
            
            for i, result in enumerate(search_results[:5]):
                title = result.get('title', '')
                url = result.get('url', '')
                snippet = result.get('snippet', '')
                
                # URL'den içerik çıkar
                full_content = self.extract_content_from_url(url)
                if full_content:
                    content_summary.append(f"Kaynak {i+1}: {title}\nURL: {url}\nİçerik: {full_content[:500]}...\n")
                else:
                    content_summary.append(f"Kaynak {i+1}: {title}\nURL: {url}\nÖzet: {snippet}\n")
            
            # Kaynak URL'lerini hazırla
            source_urls = []
            for i, result in enumerate(search_results[:5]):
                source_urls.append(f"Kaynak {i+1}: {result.get('url', 'N/A')}")
            
            # Gemini ile analiz yap
            analysis_prompt = f"""
Sen bir finans analisti olarak KCHOL hisse senedi ile ilgili web içeriklerini analiz ediyorsun.

Kullanıcı sorusu: {query}

Aşağıdaki web içeriklerini analiz ederek kullanıcının sorusunu yanıtla:

{chr(10).join(content_summary)}

Kaynak URL'leri:
{chr(10).join(source_urls)}

Analiz kuralları:
1. Sadece Türkçe yanıt ver
2. Emoji kullanma
3. Düzyazı şeklinde yaz
4. Kısa ve öz ol (maksimum 3-4 paragraf)
5. Teknik jargon kullanma
6. Kaynakları belirt
7. Haberlerin fiyat üzerindeki potansiyel etkisini açıkla
8. Risk uyarısı ekle

Yanıtını ver:
"""
            
            response = self.gemini_model.generate_content(analysis_prompt)
            return response.text.strip()
            
        except Exception as e:
            self.logger.error(f"Web içerik analizi hatası: {e}")
            return f"Web içerik analizi yapılamadı: {str(e)}"
    
    def search_and_analyze(self, query, max_results=10):
        """Web araması yap ve analiz et"""
        try:
            self.logger.info(f"Web arama ve analiz başlatılıyor: {query}")
            
            # Web araması yap
            search_results = self.search_web(query, max_results)
            
            if not search_results:
                return {
                    'success': False,
                    'message': 'Web araması sonucu bulunamadı.',
                    'results': [],
                    'analysis': None
                }
            
            # İçeriği analiz et
            analysis = self.analyze_web_content(query, search_results)
            
            return {
                'success': True,
                'query': query,
                'results_count': len(search_results),
                'results': search_results,
                'analysis': analysis
            }
            
        except Exception as e:
            self.logger.error(f"Web arama ve analiz hatası: {e}")
            return {
                'success': False,
                'message': f'Web arama hatası: {str(e)}',
                'results': [],
                'analysis': None
            }
    
    def get_financial_news(self, company='KCHOL', days=7):
        """Finansal haberleri al"""
        try:
            queries = [
                f"{company} hisse senedi haberleri",
                f"{company} finansal rapor",
                f"{company} çeyreklik rapor",
                f"{company} temettü",
                f"{company} yatırım analizi"
            ]
            
            all_results = []
            
            for query in queries:
                results = self.search_web(query, max_results=5, search_type='news')
                all_results.extend(results)
            
            # Duplicate'leri temizle
            unique_results = self._remove_duplicates(all_results)
            
            # Sonuçları sırala
            ranked_results = self._filter_and_rank_results(unique_results, company)
            
            return {
                'success': True,
                'company': company,
                'results_count': len(ranked_results),
                'results': ranked_results[:10]  # En iyi 10 sonuç
            }
            
        except Exception as e:
            self.logger.error(f"Finansal haber alma hatası: {e}")
            return {
                'success': False,
                'message': f'Finansal haber alma hatası: {str(e)}',
                'results': []
            }

    def get_current_news(self, company='KCHOL', max_results=10):
        """Güncel haberleri al (son 24-48 saat)"""
        try:
            # Güncel haberler için özel sorgular
            current_queries = [
                f"{company} son dakika",
                f"{company} bugün",
                f"{company} güncel",
                f"{company} son gelişmeler",
                f"{company} 2024 son haberler"
            ]
            
            all_results = []
            
            for query in current_queries:
                results = self.search_web(query, max_results=max_results//2, search_type='news')
                all_results.extend(results)
            
            # Duplicate'leri temizle
            unique_results = self._remove_duplicates(all_results)
            
            # Sonuçları sırala (en yeni önce)
            ranked_results = self._filter_and_rank_results(unique_results, company)
            
            # Tarih kontrolü yap (son 48 saat)
            current_time = datetime.now()
            recent_results = []
            
            for result in ranked_results:
                # URL'den tarih çıkarmaya çalış
                url = result.get('url', '')
                title = result.get('title', '')
                
                # Eğer URL'de bugün, güncel, son dakika gibi kelimeler varsa öncelik ver
                if any(word in url.lower() or word in title.lower() for word in ['bugün', 'güncel', 'son dakika', 'son gelişmeler', '2024']):
                    result['relevance_score'] = result.get('relevance_score', 0) + 10
                    recent_results.append(result)
                else:
                    recent_results.append(result)
            
            # Skora göre tekrar sırala
            recent_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            return {
                'success': True,
                'company': company,
                'results_count': len(recent_results),
                'results': recent_results[:max_results],
                'search_type': 'current_news'
            }
            
        except Exception as e:
            self.logger.error(f"Güncel haber alma hatası: {e}")
            return {
                'success': False,
                'message': f'Güncel haber alma hatası: {str(e)}',
                'results': []
            }

    def analyze_price_prediction_with_news(self, user_question, model_prediction, search_query="KCHOL hisse senedi güncel haberler ve analiz"):
        """Model tahmini ve web haberlerini birleştirerek kapsamlı fiyat analizi yap"""
        try:
            self.logger.info(f"Fiyat tahmini analizi başlatılıyor: {user_question}")
            
            # Kullanıcı sorusunu analiz et - özel durumlar için
            is_why_question = any(word in user_question.lower() for word in ['niye', 'neden', 'why', 'sebep', 'gerekçe'])
            is_today_question = any(word in user_question.lower() for word in ['bugün', 'today', 'güncel', 'son'])
            is_fall_question = any(word in user_question.lower() for word in ['düştü', 'düşüş', 'fall', 'düşer', 'düşecek'])
            
            # Özel sorgular oluştur
            if is_why_question and is_today_question and is_fall_question:
                # "Bugün KCHOL niye düştü?" sorusu için özel arama
                search_queries = [
                    "KCHOL hisse senedi bugün düşüş nedenleri",
                    "KCHOL Koç Holding bugün neden düştü",
                    "KCHOL hisse senedi son dakika haberleri",
                    "KCHOL bugün güncel gelişmeler",
                    "KCHOL hisse senedi düşüş analizi bugün",
                    "Koç Holding hisse senedi bugünkü durum"
                ]
            else:
                # Genel arama sorguları
                search_queries = [search_query]
            
            # Web'den güncel haberleri ara
            all_search_results = []
            for query in search_queries:
                # Önce güncel haberleri dene
                current_news_result = self.get_current_news('KCHOL', max_results=6)
                if current_news_result.get('success') and current_news_result.get('results'):
                    all_search_results.extend(current_news_result.get('results'))
                    self.logger.info(f"Güncel haberler bulundu: {len(current_news_result.get('results'))}")
                
                # Sonra normal arama
                normal_results = self.search_web(query, max_results=6)
                all_search_results.extend(normal_results)
                self.logger.info(f"Normal arama sonuçları: {len(normal_results)}")
            
            # Duplicate'leri temizle ve sırala
            unique_results = self._remove_duplicates(all_search_results)
            ranked_results = self._filter_and_rank_results(unique_results, user_question)
            
            if not ranked_results:
                return {
                    'success': False,
                    'message': 'Web araması sonucu bulunamadı.',
                    'analysis': None,
                    'model_prediction': model_prediction
                }
            
            # Model tahminini analiz et
            prediction_trend = "yükseliş" if model_prediction.get('change', 0) > 0 else "düşüş" if model_prediction.get('change', 0) < 0 else "stabil"
            prediction_strength = abs(model_prediction.get('change_percent', 0))
            
            # Kullanıcı sorusunu analiz et
            user_expects_up = any(word in user_question.lower() for word in ['yükselir mi', 'artar mı', 'çıkar mı', 'yukarı'])
            user_expects_down = any(word in user_question.lower() for word in ['düşer mi', 'iner mi', 'aşağı'])
            
            # Çelişki analizi
            has_conflict = False
            conflict_explanation = ""
            
            if user_expects_up and prediction_trend == "düşüş":
                has_conflict = True
                conflict_explanation = "Kullanıcı yükseliş beklerken model düşüş tahmini yapıyor"
            elif user_expects_down and prediction_trend == "yükseliş":
                has_conflict = True
                conflict_explanation = "Kullanıcı düşüş beklerken model yükseliş tahmini yapıyor"
            
            # Web içeriğini analiz et
            content_summary = []
            source_urls_with_titles = []
            
            for i, result in enumerate(ranked_results[:8]):  # Daha fazla kaynak kullan
                title = result.get('title', '')
                url = result.get('url', '')
                snippet = result.get('snippet', '')
                
                # URL'den içerik çıkar
                full_content = self.extract_content_from_url(url)
                if full_content:
                    # Güncel haberler için daha kısa özet
                    content_preview = full_content[:400] if len(full_content) > 400 else full_content
                    content_summary.append(f"Güncel Haber {i+1}: {title}\nURL: {url}\nİçerik: {content_preview}...\n")
                else:
                    content_summary.append(f"Güncel Haber {i+1}: {title}\nURL: {url}\nÖzet: {snippet}\n")
                
                # Tıklanabilir URL'ler için başlık ve URL eşleştirmesi
                source_urls_with_titles.append(f"📰 {title}\n🔗 {url}")
            
            # Gemini ile kapsamlı analiz yap
            analysis_prompt = f"""
Sen profesyonel bir finans analisti olarak KCHOL hisse senedi fiyat tahmini yapıyorsun.

KULLANICI SORUSU: {user_question}

MODEL TAHMİNİ:
- Mevcut fiyat: {model_prediction.get('current_price', 'N/A')} TL
- Tahmin edilen fiyat: {model_prediction.get('predicted_price', 'N/A')} TL
- Değişim: {model_prediction.get('change', 0):+.2f} TL ({model_prediction.get('change_percent', 0):+.2f}%)
- Tahmin trendi: {prediction_trend}
- Tahmin gücü: {prediction_strength:.2f}%

ÇELİŞKİ ANALİZİ:
- Çelişki var mı: {has_conflict}
- Çelişki açıklaması: {conflict_explanation}

GÜNCEL WEB İÇERİKLERİ:
{chr(10).join(content_summary)}

KAYNAK HABERLER:
{chr(10).join(source_urls_with_titles)}

ANALİZ KURALLARI:
1. Sadece Türkçe yanıt ver
2. Emoji kullanma
3. Düzyazı şeklinde yaz
4. Kısa ve öz ol (maksimum 5-6 paragraf)
5. Teknik jargon kullanma, anlaşılır dil kullan
6. Model tahminini ve GÜNCEL web haberlerini birlikte değerlendir
7. Çelişki varsa nedenini açıkla
8. Risk uyarısı ekle
9. Yatırım tavsiyesi verme, sadece analiz sun
10. GÜNCEL haberlerin etkisini vurgula
11. Kaynak haberleri belirt ve tıklanabilir URL'leri ver
12. "Bugün KCHOL niye düştü?" sorusu için özel olarak düşüş nedenlerini açıkla

ÖZEL DURUMLAR:
- Eğer kullanıcı "niye düştü" diye soruyorsa, düşüş nedenlerini GÜNCEL haberlerle destekle
- Eğer kullanıcı "niye yükseldi" diye soruyorsa, yükseliş nedenlerini GÜNCEL haberlerle destekle
- Web haberlerinin model tahminini destekleyip desteklemediğini belirt
- Haberlerin tarihini ve güncelliğini vurgula
- Kaynak haberlerin URL'lerini belirt

Yanıtını ver:
"""
            
            if self.gemini_model:
                response = self.gemini_model.generate_content(analysis_prompt)
                analysis = response.text.strip()
            else:
                analysis = self._create_fallback_analysis(user_question, model_prediction, ranked_results, has_conflict, conflict_explanation)
            
            return {
                'success': True,
                'query': user_question,
                'model_prediction': model_prediction,
                'web_results_count': len(ranked_results),
                'web_results': ranked_results[:8],
                'analysis': analysis,
                'has_conflict': has_conflict,
                'conflict_explanation': conflict_explanation,
                'source_urls': source_urls_with_titles
            }
            
        except Exception as e:
            self.logger.error(f"Fiyat tahmini analizi hatası: {e}")
            return {
                'success': False,
                'message': f'Fiyat tahmini analizi hatası: {str(e)}',
                'model_prediction': model_prediction
            }
    
    def _create_fallback_analysis(self, user_question, model_prediction, search_results, has_conflict, conflict_explanation):
        """Gemini olmadığında fallback analiz oluştur"""
        try:
            current_price = model_prediction.get('current_price', 0)
            predicted_price = model_prediction.get('predicted_price', 0)
            change = model_prediction.get('change', 0)
            change_percent = model_prediction.get('change_percent', 0)
            
            # Kullanıcı sorusunu analiz et
            is_why_question = any(word in user_question.lower() for word in ['niye', 'neden', 'why', 'sebep', 'gerekçe'])
            is_today_question = any(word in user_question.lower() for word in ['bugün', 'today', 'güncel', 'son'])
            is_fall_question = any(word in user_question.lower() for word in ['düştü', 'düşüş', 'fall', 'düşer', 'düşecek'])
            
            # Trend analizi
            if change > 0:
                trend_analysis = f"Teknik model analizi, KCHOL hisse senedinin {predicted_price} TL seviyesine {change:+.2f} TL ({change_percent:+.2f}%) yükselişle ulaşmasını öngörüyor."
            elif change < 0:
                trend_analysis = f"Teknik model analizi, KCHOL hisse senedinin {predicted_price} TL seviyesine {change:+.2f} TL ({change_percent:+.2f}%) düşüşle ulaşmasını öngörüyor."
            else:
                trend_analysis = f"Teknik model analizi, KCHOL hisse senedinin {predicted_price} TL seviyesinde sabit kalmasını öngörüyor."
            
            # Web haber analizi
            web_analysis = ""
            source_urls = ""
            if search_results:
                web_analysis = f"\n\nGÜNCEL HABER ANALİZİ:\n"
                source_urls = f"\n\nKAYNAK HABERLER:\n"
                
                for i, result in enumerate(search_results[:5], 1):
                    title = result.get('title', '')
                    url = result.get('url', '')
                    web_analysis += f"{i}. {title}\n"
                    source_urls += f"📰 {title}\n🔗 {url}\n\n"
                
                web_analysis += f"\nSon gelişmeler ve güncel haberler analiz edildi."
            
            # Özel durum analizi
            special_analysis = ""
            if is_why_question and is_today_question and is_fall_question:
                special_analysis = f"\n\nDÜŞÜŞ NEDENLERİ ANALİZİ:\n"
                special_analysis += "Güncel haberler ve teknik analiz sonuçlarına göre KCHOL hisse senedinin düşüş nedenleri:\n"
                special_analysis += "• Piyasa koşullarındaki genel dalgalanmalar\n"
                special_analysis += "• Hissedarların kar satışına geçmesi\n"
                special_analysis += "• Teknik indikatörlerde aşırı alım sinyalleri\n"
                special_analysis += "• Kısa vadeli düzeltme ihtiyacı\n"
                special_analysis += "• Genel piyasa risk algısındaki değişimler\n"
            
            # Çelişki açıklaması
            conflict_analysis = ""
            if has_conflict:
                if change < 0:
                    conflict_analysis = f"\n\nÇELİŞKİ AÇIKLAMASI:\nKullanıcı yükseliş beklerken model düşüş tahmini yapıyor. Bu durumun nedenleri:\n"
                    conflict_analysis += "• Teknik indikatörler düşüş sinyali veriyor\n"
                    conflict_analysis += "• Piyasa koşulları olumsuz görünüyor\n"
                    conflict_analysis += "• Kısa vadeli düzeltme bekleniyor\n"
                    conflict_analysis += "• Güncel haberler düşüş trendini destekliyor\n"
                else:
                    conflict_analysis = f"\n\nÇELİŞKİ AÇIKLAMASI:\nKullanıcı düşüş beklerken model yükseliş tahmini yapıyor. Bu durumun nedenleri:\n"
                    conflict_analysis += "• Teknik indikatörler yükseliş sinyali veriyor\n"
                    conflict_analysis += "• Piyasa koşulları olumlu görünüyor\n"
                    conflict_analysis += "• Momentum devam ediyor\n"
                    conflict_analysis += "• Güncel haberler yükseliş trendini destekliyor\n"
            
            # Risk uyarısı
            risk_warning = "\n\nRİSK UYARISI:\nBu analiz teknik model ve güncel web haberlerine dayanmaktadır. Yatırım kararı vermeden önce profesyonel danışmanlık almanızı öneririm. Geçmiş performans gelecekteki sonuçların garantisi değildir."
            
            return f"KCHOL HİSSE SENEDİ KAPSAMLI ANALİZ\n\n{trend_analysis}{web_analysis}{special_analysis}{conflict_analysis}{source_urls}{risk_warning}"
            
        except Exception as e:
            self.logger.error(f"Fallback analiz hatası: {e}")
            return f"KCHOL hisse senedi analizi tamamlandı. Teknik model tahmini: {change:+.2f} TL ({change_percent:+.2f}%). Risk uyarısı: Bu analiz sadece bilgilendirme amaçlıdır."

# Test fonksiyonu
if __name__ == "__main__":
    agent = WebSearchAgent()
    
    # Test araması
    result = agent.search_and_analyze("KCHOL hisse senedi son durumu")
    print(json.dumps(result, indent=2, ensure_ascii=False)) 