#!/usr/bin/env python3
"""
Professional RAG (Retrieval-Augmented Generation) Agent with Document Processing
Supports PDF, CSV, TXT, and other document formats
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from typing import List, Dict, Optional, Tuple
import yfinance as yf
import pandas as pd
import numpy as np
from pathlib import Path
import re
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import io
import base64

try:
    import PyPDF2
    import fitz  
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("PDF processing not available. Install: pip install PyPDF2 PyMuPDF")

try:
    from sentence_transformers import SentenceTransformer
    import faiss
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("Embeddings not available. Install: pip install sentence-transformers faiss-cpu")

# Load environment variables
load_dotenv()

class DocumentRAGAgent:
    def __init__(self, documents_path: str = "documents"):
        """Initialize Document RAG Agent"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
        
        # Document processing
        self.documents_path = Path(documents_path)
        self.documents_path.mkdir(exist_ok=True)
        
        # Initialize embeddings if available
        self.embeddings_model = None
        self.vector_index = None
        self.document_chunks = []
        
        if EMBEDDINGS_AVAILABLE:
            self._initialize_embeddings()
        
        # Load and process documents
        self._load_documents()
        
    def _initialize_embeddings(self):
        """Initialize sentence transformer for embeddings"""
        try:
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Embeddings model loaded successfully")
        except Exception as e:
            print(f"Failed to load embeddings model: {e}")
            self.embeddings_model = None
    
    def _load_documents(self):
        """Load and process all documents in the documents folder"""
        if not self.documents_path.exists():
            print(f"Creating documents folder: {self.documents_path}")
            return
        
        print(f"Loading documents from: {self.documents_path}")
        
        for file_path in self.documents_path.glob("*"):
            if file_path.is_file():
                try:
                    content = self._read_document(file_path)
                    if content:
                        chunks = self._chunk_text(content, chunk_size=500, overlap=50)
                        self.document_chunks.extend(chunks)
                        print(f"Loaded {len(chunks)} chunks from {file_path.name}")
                except Exception as e:
                    print(f"Error loading {file_path.name}: {e}")
        
        # Create vector index if embeddings are available
        if self.embeddings_model and self.document_chunks:
            self._create_vector_index()
    
    def _read_document(self, file_path: Path) -> str:
        """Read different document formats"""
        file_extension = file_path.suffix.lower()
        
        try:
            if file_extension == '.pdf':
                return self._read_pdf(file_path)
            elif file_extension == '.txt':
                return self._read_txt(file_path)
            elif file_extension == '.csv':
                return self._read_csv(file_path)
            elif file_extension == '.json':
                return self._read_json(file_path)
            else:
                print(f"Unsupported file format: {file_extension}")
                return ""
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")
            return ""
    
    def _read_pdf(self, file_path: Path) -> str:
        """Read PDF file"""
        if not PDF_AVAILABLE:
            return ""
        
        try:
            # Try PyMuPDF first (better text extraction)
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except:
            try:
                # Fallback to PyPDF2
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text()
                return text
            except Exception as e:
                print(f"PDF reading error: {e}")
                return ""
    
    def _read_txt(self, file_path: Path) -> str:
        """Read text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"TXT reading error: {e}")
            return ""
    
    def _read_csv(self, file_path: Path) -> str:
        """Read CSV file and convert to text"""
        try:
            df = pd.read_csv(file_path)
            return df.to_string(index=False)
        except Exception as e:
            print(f"CSV reading error: {e}")
            return ""
    
    def _read_json(self, file_path: Path) -> str:
        """Read JSON file and convert to text"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"JSON reading error: {e}")
            return ""
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        if not text.strip():
            return []
        
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for i in range(end, max(start, end - 100), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _create_vector_index(self):
        """Create FAISS vector index for document chunks"""
        if not self.embeddings_model or not self.document_chunks:
            return
        
        try:
            # Generate embeddings
            embeddings = self.embeddings_model.encode(self.document_chunks)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.vector_index = faiss.IndexFlatL2(dimension)
            self.vector_index.add(embeddings.astype('float32'))
            
            print(f"Vector index created with {len(self.document_chunks)} chunks")
        except Exception as e:
            print(f"Error creating vector index: {e}")
    
    def _search_documents(self, query: str, top_k: int = 5) -> List[str]:
        """Search documents using vector similarity"""
        if not self.vector_index or not self.embeddings_model:
            # Fallback to simple keyword search
            return self._simple_search(query, top_k)
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings_model.encode([query])
            
            # Search in vector index
            distances, indices = self.vector_index.search(
                query_embedding.astype('float32'), top_k
            )
            
            # Return relevant chunks
            relevant_chunks = []
            for idx in indices[0]:
                if idx < len(self.document_chunks):
                    relevant_chunks.append(self.document_chunks[idx])
            
            return relevant_chunks
        except Exception as e:
            print(f"Vector search error: {e}")
            return self._simple_search(query, top_k)
    
    def _simple_search(self, query: str, top_k: int = 5) -> List[str]:
        """Simple keyword-based search"""
        query_terms = query.lower().split()
        scored_chunks = []
        
        for chunk in self.document_chunks:
            chunk_lower = chunk.lower()
            score = sum(1 for term in query_terms if term in chunk_lower)
            if score > 0:
                scored_chunks.append((score, chunk))
        
        # Sort by score and return top chunks
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scored_chunks[:top_k]]
    
    def get_stock_data(self, symbol: str = "KCHOL.IS") -> Dict:
        """Get current stock data and technical indicators from Yahoo Finance"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # Get historical data for technical analysis (last 100 days)
            hist = stock.history(period="100d")
            if hist.empty:
                return {}
            
            current_price = hist['Close'].iloc[-1]
            
            # Calculate technical indicators
            technical_data = self._calculate_technical_indicators(hist)
            
            return {
                "current_price": current_price,
                "market_cap": info.get('marketCap'),
                "volume": info.get('volume'),
                "pe_ratio": info.get('trailingPE'),
                "dividend_yield": info.get('dividendYield'),
                "52_week_high": info.get('fiftyTwoWeekHigh'),
                "52_week_low": info.get('fiftyTwoWeekLow'),
                "technical_indicators": technical_data
            }
        except Exception as e:
            print(f"Stock data error: {e}")
            return {}
    
    def _calculate_technical_indicators(self, hist: pd.DataFrame) -> Dict:
        """Calculate technical indicators from historical data"""
        try:
            # Basic price data
            close_prices = hist['Close']
            high_prices = hist['High']
            low_prices = hist['Low']
            volumes = hist['Volume']
            
            # Moving Averages
            sma_20 = close_prices.rolling(window=20).mean().iloc[-1]
            sma_50 = close_prices.rolling(window=50).mean().iloc[-1]
            sma_200 = close_prices.rolling(window=200).mean().iloc[-1]
            
            # RSI (Relative Strength Index)
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # MACD (Moving Average Convergence Divergence)
            ema_12 = close_prices.ewm(span=12).mean()
            ema_26 = close_prices.ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            macd_histogram = macd_line - signal_line
            
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_histogram = macd_histogram.iloc[-1]
            
            # Bollinger Bands
            bb_middle = close_prices.rolling(window=20).mean()
            bb_std = close_prices.rolling(window=20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            
            current_bb_upper = bb_upper.iloc[-1]
            current_bb_lower = bb_lower.iloc[-1]
            current_bb_middle = bb_middle.iloc[-1]
            
            # Volume indicators
            avg_volume = volumes.rolling(window=20).mean().iloc[-1]
            current_volume = volumes.iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Price momentum
            price_change_1d = ((close_prices.iloc[-1] - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100
            price_change_5d = ((close_prices.iloc[-1] - close_prices.iloc[-6]) / close_prices.iloc[-6]) * 100
            price_change_20d = ((close_prices.iloc[-1] - close_prices.iloc[-21]) / close_prices.iloc[-21]) * 100
            
            return {
                "sma_20": round(sma_20, 2) if not pd.isna(sma_20) else None,
                "sma_50": round(sma_50, 2) if not pd.isna(sma_50) else None,
                "sma_200": round(sma_200, 2) if not pd.isna(sma_200) else None,
                "rsi": round(current_rsi, 2) if not pd.isna(current_rsi) else None,
                "macd": round(current_macd, 2) if not pd.isna(current_macd) else None,
                "macd_signal": round(current_signal, 2) if not pd.isna(current_signal) else None,
                "macd_histogram": round(current_histogram, 2) if not pd.isna(current_histogram) else None,
                "bb_upper": round(current_bb_upper, 2) if not pd.isna(current_bb_upper) else None,
                "bb_lower": round(current_bb_lower, 2) if not pd.isna(current_bb_lower) else None,
                "bb_middle": round(current_bb_middle, 2) if not pd.isna(current_bb_middle) else None,
                "volume_ratio": round(volume_ratio, 2),
                "price_change_1d": round(price_change_1d, 2),
                "price_change_5d": round(price_change_5d, 2),
                "price_change_20d": round(price_change_20d, 2)
            }
            
        except Exception as e:
            print(f"Technical indicators calculation error: {e}")
            return {}
    
    def generate_response(self, query: str, context: str = "") -> str:
        """Generate response using RAG approach"""
        try:
            # Check if user wants charts
            chart_keywords = ['grafik', 'chart', 'çiz', 'göster', 'plot', 'görsel', 'rsi', 'macd', 'bollinger', 'hacim', 'volume']
            wants_chart = any(keyword in query.lower() for keyword in chart_keywords)
            
            if wants_chart:
                return self._generate_chart_response(query, context)
            
            # Create enhanced prompt with context
            prompt = f"""
Sen Türkçe konuşan bir finans ve yatırım uzmanısın. KCHOL hisse senedi ve genel finans konularında uzman bilgi veriyorsun.

KULLANICI SORUSU: {query}

BAĞLAM BİLGİLERİ (Dokümanlardan ve güncel verilerden):
{context if context else "Bağlam bilgisi bulunamadı."}

Lütfen aşağıdaki kurallara uygun olarak yanıt ver:
1. Dokümanlardaki bilgileri doğal bir şekilde entegre et
2. Dokümanlarda bilgi yoksa kendi uzmanlığını kullan
3. Sadece Türkçe yanıt ver
4. Finansal tavsiye verme, sadece bilgilendirici ol
5. Kısa ve öz yanıtlar ver
6. Profesyonel ve anlaşılır dil kullan
7. "Dokümanlarda belirtildiği gibi" gibi ifadeler kullanma
8. Bilgileri doğal ve akıcı bir şekilde sun
9. Güncel ve doğru bilgiler ver

Yanıtını ver:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"RAG generation error: {e}")
            return "Üzgünüm, şu anda yanıt veremiyorum. Lütfen daha sonra tekrar deneyin."
    
    def _generate_chart_response(self, query: str, context: str = "") -> str:
        """Generate chart code and execute it"""
        try:
            # Get stock data for chart generation
            stock_data = self.get_stock_data()
            if not stock_data:
                return "Hisse verisi alınamadı. Lütfen daha sonra tekrar deneyin."
            
            # Generate chart code using Gemini
            chart_code = self._generate_chart_code(query, stock_data)
            if not chart_code:
                return "Grafik kodu oluşturulamadı. Lütfen tekrar deneyin."
            
            # Execute the chart code
            chart_image = self._execute_chart_code(chart_code, stock_data)
            if not chart_image:
                return "Grafik oluşturulamadı. Lütfen tekrar deneyin."
            
            return f"Teknik analiz grafiği oluşturuldu:\n\n![Teknik Analiz Grafiği](data:image/png;base64,{chart_image})"
            
        except Exception as e:
            print(f"Chart generation error: {e}")
            return "Grafik oluşturulurken bir hata oluştu. Lütfen tekrar deneyin."
    
    def _generate_chart_code(self, query: str, stock_data: Dict) -> str:
        """Generate Python code for creating technical analysis charts"""
        try:
            # Create prompt for dynamic code generation
            prompt = f"""
KCHOL hisse senedi için {query} grafiği oluşturacak Python kodu yaz.

MEVCUT VERİLER: hist DataFrame (hist['Close'], hist['Volume'])

GEREKSİNİMLER:
- Sadece matplotlib, numpy, io, base64 kullan
- Türkçe etiketler
- chart_base64 değişkenine base64 string ata
- FONKSİYON TANIMLAMA YOK, SADECE KOD YAZ

ÖRNEK RSI KODU:
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial Unicode MS', 'sans-serif']

delta = hist['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs))

plt.figure(figsize=(12, 6))
plt.plot(hist.index, rsi, label='RSI', linewidth=2, color='purple')
plt.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='Aşırı Alım (70)')
plt.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='Aşırı Satım (30)')
plt.title('KCHOL RSI Göstergesi')
plt.ylabel('RSI')
plt.xlabel('Tarih')
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(0, 100)

buffer = io.BytesIO()
plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
buffer.seek(0)
chart_base64 = base64.b64encode(buffer.getvalue()).decode()
plt.close()

SADECE KOD YAZ, FONKSİYON TANIMLAMA YOK:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Chart code generation error: {e}")
            return ""
    
    def _execute_chart_code(self, code: str, stock_data: Dict) -> str:
        """Execute the generated chart code and return base64 image"""
        try:
            # Get historical data for chart
            stock = yf.Ticker("KCHOL.IS")
            hist = stock.history(period="100d")
            
            # Create a safe execution environment
            local_vars = {
                'hist': hist,
                'plt': plt,
                'np': np,
                'io': io,
                'base64': base64
            }
            
            # Execute the code
            exec(code, {}, local_vars)
            
            # Get the result
            if 'chart_base64' in local_vars:
                return local_vars['chart_base64']
            else:
                print("chart_base64 variable not found in executed code")
                return ""
                
        except Exception as e:
            print(f"Chart code execution error: {e}")
            return ""
    
    def process_query(self, query: str) -> str:
        """Main method to process user query using Document RAG"""
        try:
            # Step 1: Search documents
            relevant_chunks = self._search_documents(query)
            
            # Step 2: Get current stock data
            stock_data = self.get_stock_data()
            
            # Step 3: Format context
            context = self._format_context(relevant_chunks, stock_data)
            
            # Step 4: Generate response
            response = self.generate_response(query, context)
            
            return response
            
        except Exception as e:
            print(f"Document RAG processing error: {e}")
            return "Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin."
    
    def _format_context(self, relevant_chunks: List[str], stock_data: Dict) -> str:
        """Format search results and stock data into context"""
        context_parts = []
        
        # Add relevant document chunks as primary context
        if relevant_chunks:
            context_parts.append("DOKÜMAN BAĞLAMI:")
            for i, chunk in enumerate(relevant_chunks, 1):
                context_parts.append(f"{i}. {chunk}")
            context_parts.append("")
        else:
            context_parts.append("DOKÜMAN BAĞLAMI: İlgili doküman bulunamadı.")
            context_parts.append("")
        
        # Add stock data as additional context
        if stock_data:
            context_parts.append("GÜNCEL BORSA VERİLERİ:")
            if stock_data.get('current_price'):
                context_parts.append(f"- Mevcut Fiyat: {stock_data['current_price']:.2f} TL")
            if stock_data.get('market_cap'):
                context_parts.append(f"- Piyasa Değeri: {stock_data['market_cap']:,.0f} TL")
            if stock_data.get('volume'):
                context_parts.append(f"- İşlem Hacmi: {stock_data['volume']:,.0f}")
            if stock_data.get('pe_ratio'):
                context_parts.append(f"- P/E Oranı: {stock_data['pe_ratio']:.2f}")
            context_parts.append("")
            
            # Add technical indicators if available
            if stock_data.get('technical_indicators'):
                tech = stock_data['technical_indicators']
                context_parts.append("TEKNİK GÖSTERGELER:")
                
                # Moving Averages
                if tech.get('sma_20') and tech.get('sma_50'):
                    context_parts.append(f"- SMA 20: {tech['sma_20']:.2f} TL")
                    context_parts.append(f"- SMA 50: {tech['sma_50']:.2f} TL")
                    if tech.get('sma_200'):
                        context_parts.append(f"- SMA 200: {tech['sma_200']:.2f} TL")
                
                # RSI
                if tech.get('rsi'):
                    rsi_status = "Aşırı Alım" if tech['rsi'] > 70 else "Aşırı Satım" if tech['rsi'] < 30 else "Nötr"
                    context_parts.append(f"- RSI: {tech['rsi']:.2f} ({rsi_status})")
                
                # MACD
                if tech.get('macd') and tech.get('macd_signal'):
                    macd_signal = "Alım" if tech['macd'] > tech['macd_signal'] else "Satım"
                    context_parts.append(f"- MACD: {tech['macd']:.2f} | Sinyal: {tech['macd_signal']:.2f} ({macd_signal})")
                
                # Bollinger Bands
                if tech.get('bb_upper') and tech.get('bb_lower'):
                    current_price = stock_data.get('current_price', 0)
                    bb_position = "Üst Band" if current_price > tech['bb_upper'] else "Alt Band" if current_price < tech['bb_lower'] else "Orta Bölge"
                    context_parts.append(f"- Bollinger Bands: {tech['bb_lower']:.2f} - {tech['bb_upper']:.2f} TL ({bb_position})")
                
                # Price Changes
                if tech.get('price_change_1d'):
                    context_parts.append(f"- 1 Günlük Değişim: {tech['price_change_1d']:+.2f}%")
                if tech.get('price_change_5d'):
                    context_parts.append(f"- 5 Günlük Değişim: {tech['price_change_5d']:+.2f}%")
                if tech.get('price_change_20d'):
                    context_parts.append(f"- 20 Günlük Değişim: {tech['price_change_20d']:+.2f}%")
                
                # Volume
                if tech.get('volume_ratio'):
                    volume_status = "Yüksek" if tech['volume_ratio'] > 1.5 else "Düşük" if tech['volume_ratio'] < 0.5 else "Normal"
                    context_parts.append(f"- Hacim Oranı: {tech['volume_ratio']:.2f}x ({volume_status})")
                
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def add_document(self, file_path: str) -> bool:
        """Add a new document to the knowledge base"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"File not found: {file_path}")
                return False
            
            # Read and process document
            content = self._read_document(file_path)
            if not content:
                return False
            
            # Create chunks
            chunks = self._chunk_text(content)
            self.document_chunks.extend(chunks)
            
            # Update vector index if available
            if self.embeddings_model:
                self._create_vector_index()
            
            print(f"Added {len(chunks)} chunks from {file_path.name}")
            return True
            
        except Exception as e:
            print(f"Error adding document: {e}")
            return False

# Test function
def test_document_rag():
    """Test the Document RAG agent"""
    try:
        agent = DocumentRAGAgent()
        
        test_queries = [
            "KCHOL hisse senedi hakkında bilgi ver",
            "KCHOL şirketi hangi sektörlerde faaliyet gösteriyor?",
            "Yatırım stratejisi öner"
        ]
        
        print("Document RAG Agent Test Baslatiliyor...")
        print("=" * 60)
        
        for query in test_queries:
            print(f"Soru: {query}")
            response = agent.process_query(query)
            print(f"Yanit: {response}")
            print("-" * 60)
        
        print("Document RAG Agent test tamamlandi!")
        
    except Exception as e:
        print(f"Test hatasi: {e}")

if __name__ == "__main__":
    test_document_rag() 