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
import uuid

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Global sohbet geçmişi tutma
chat_sessions = {}  # session_id -> chat_history
current_session_id = None

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
gemini_model = genai.GenerativeModel(os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'))

# Initialize Document RAG Agent
try:
    document_rag_agent = DocumentRAGAgent()
    print("Document RAG Agent basariyla yuklendi")
except Exception as e:
    print(f"Document RAG Agent yuklenemedi: {e}")
    document_rag_agent = None

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
        content += "=" * 50 + "\n\n"
        
        for msg in session['messages']:
            timestamp = datetime.fromisoformat(msg['timestamp']).strftime("%d.%m.%Y %H:%M:%S")
            sender_name = "Siz" if msg['sender'] == 'user' else "KCHOL Asistan"
            content += f"[{timestamp}] {sender_name}:\n{msg['message']}\n\n"
        
        return content
    
    elif format == 'json':
        return json.dumps(session, indent=2, ensure_ascii=False)
    
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
        # Türkçe finans asistanı için prompt hazırlama
        system_prompt = f"""
Sen Türkçe konuşan bir finans ve yatırım asistanısın. KCHOL hisse senedi ve genel finans konularında uzman bilgi veriyorsun.

Kullanıcı sorusu: {user_message}

Lütfen aşağıdaki kurallara uygun olarak yanıt ver:
1. Sadece Türkçe yanıt ver
2. Finansal tavsiye verme, sadece bilgilendirici ol
3. KCHOL hisse senedi hakkında sorulara özel önem ver
4. Kısa ve öz yanıtlar ver
5. Profesyonel ve anlaşılır dil kullan

{context}
        """
        
        response = gemini_model.generate_content(system_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API hatası: {e}")
        return "Üzgünüm, şu anda yanıt veremiyorum. Lütfen daha sonra tekrar deneyin."

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
        
        result = {
            'current_price': float(round(current_price, 2)),
            'predicted_price': float(round(prediction, 2)),
            'change': float(round(change, 2)),
            'change_percent': float(round(change_percent, 2)),
            'prediction_date': tomorrow.strftime('%Y-%m-%d')
        }
        
        print(f"Tahmin sonucu: {result}")
        return result, None
        
    except Exception as e:
        print(f"Tahmin hatası: {e}")
        import traceback
        traceback.print_exc()
        return None, f"Tahmin hatası: {e}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        message = data.get('message', '').lower()
        original_message = data.get('message', '')  # Orijinal mesajı koru
        
        # Mevcut oturumu al
        current_session = get_current_session()
        session_id = current_session['id']
        
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
        if any(word in message for word in ['tahmin', 'fiyat', 'ne olacak', 'yükselir mi', 'düşer mi']):
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
            
            # Tahmin yap
            result, error = predict_price(model, df)
            if error:
                error_response = f'Tahmin yapılamadı: {error}'
                add_message_to_session(session_id, 'bot', error_response, 'error')
                return jsonify({
                    'response': error_response,
                    'type': 'error',
                    'session_id': session_id
                })
            
            # Hafta sonu kontrolü mesajı
            prediction_date = datetime.strptime(result['prediction_date'], '%Y-%m-%d')
            if prediction_date.weekday() >= 5:  # Cumartesi (5) veya Pazar (6)
                print(f"Hafta sonu tespit edildi. Tahmin tarihi: {result['prediction_date']} (Pazartesi)")
            
            # Tahmin sonucunu formatla
            trend_text = "Yükseliş bekleniyor!" if result['change'] > 0 else "Düşüş bekleniyor!" if result['change'] < 0 else "Fiyat sabit kalabilir"
            
            response = f"""
KCHOL Hisse Senedi Fiyat Tahmini

Mevcut Fiyat: {result['current_price']} TL
Tahmin Edilen Fiyat: {result['predicted_price']} TL
Değişim: {result['change']:+.2f} TL ({result['change_percent']:+.2f}%)
Tahmin Tarihi: {result['prediction_date']}

{trend_text}
            """
            
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

Fiyat Tahmini: "Fiyat tahmini yap", "Ne olacak", "Yükselir mi" gibi sorular sorabilirsiniz
Teknik Analiz: Mevcut fiyat ve tahmin edilen fiyat karşılaştırması
Öneriler: Yatırım kararlarınız için veri tabanlı öneriler
Genel Sorular: KCHOL, finans, yatırım ve ekonomi hakkında her türlü soru

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
            
        else:
            # Document RAG Agent ile profesyonel yanıtlar
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
                    # Fallback to basic Gemini
                    print(f"Gemini'ye gonderilen mesaj: {original_message}")
                    gemini_response = get_gemini_response(original_message)
                    print(f"Gemini'den gelen yanit: {gemini_response}")
                    add_message_to_session(session_id, 'bot', gemini_response, 'ai_response')
                    return jsonify({
                        'response': gemini_response,
                        'type': 'ai_response',
                        'session_id': session_id
                    })
            except Exception as error:
                print(f"AI yanit hatasi: {error}")
                error_response = 'Anlamadigim bir soru sordunuz. Fiyat tahmini yapmak icin "fiyat tahmini yap" veya "ne olacak" diyebilirsiniz. Yardim icin "yardim" yazabilirsiniz.'
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
    if not session_id:
        return jsonify({
            'success': False,
            'message': 'Oturum ID eksik'
        }), 400
    
    history_content = export_chat_history(session_id)
    if history_content is None:
        return jsonify({
            'success': False,
            'message': 'Oturum bulunamadı'
        }), 404
    
    import io
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000) 