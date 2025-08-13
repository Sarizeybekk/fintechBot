// Global değişkenler
let isLoading = false;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let recognition = null;
let currentTheme = 'light'; // Varsayılan tema
let chatHistory = []; // Sohbet geçmişi
let currentChatId = null; // Aktif sohbet ID'si

// Tema yönetimi
function initTheme() {
    // Local storage'dan tema tercihini al
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        currentTheme = savedTheme;
        applyTheme(currentTheme);
    } else {
        // Sistem temasını kontrol et
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            currentTheme = 'auto';
        }
        applyTheme(currentTheme);
    }
}

// Temayı uygula
function applyTheme(theme) {
    const body = document.documentElement;
    
    if (theme === 'auto') {
        // Sistem temasını kontrol et
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            body.setAttribute('data-theme', 'dark');
        } else {
            body.setAttribute('data-theme', 'light');
        }
    } else {
        body.setAttribute('data-theme', theme);
    }
    
    currentTheme = theme;
    localStorage.setItem('theme', theme);
    
    // Tema modal'ındaki aktif seçeneği güncelle
    updateThemeModal();
}

// Tema modal'ını aç
function openThemeModal() {
    const themeModal = document.getElementById('themeModal');
    themeModal.classList.add('show');
    updateThemeModal();
}

// Tema modal'ını kapat
function closeThemeModal() {
    const themeModal = document.getElementById('themeModal');
    themeModal.classList.remove('show');
}

// Tema modal'ındaki aktif seçeneği güncelle
function updateThemeModal() {
    const themeOptions = document.querySelectorAll('.theme-option');
    themeOptions.forEach(option => {
        option.classList.remove('active');
    });
    
    const activeOption = document.getElementById(`${currentTheme}-theme`);
    if (activeOption) {
        activeOption.classList.add('active');
    }
}

// Tema değiştir
function changeTheme(theme) {
    applyTheme(theme);
    closeThemeModal();
    
    // Tema butonuna animasyon ekle
    const themeBtn = document.querySelector('.theme-btn');
    if (themeBtn) {
        themeBtn.style.transform = 'scale(1.2) rotate(180deg)';
        setTimeout(() => {
            themeBtn.style.transform = 'scale(1) rotate(0deg)';
        }, 300);
    }
    
    const themeNames = {
        'light': 'Açık Tema',
        'dark': 'Koyu Tema',
        'auto': 'Otomatik Tema'
    };
    
    showToast(`${themeNames[theme]} uygulandı`, 'success');
}

// Sistem tema değişikliğini dinle
function watchSystemTheme() {
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (currentTheme === 'auto') {
                applyTheme('auto');
            }
        });
    }
}

// Speech Recognition API'sini başlat
function initSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'tr-TR';
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('messageInput').value = transcript;
            showToast('Ses tanıma tamamlandı!', 'success');
        };
        
        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            showToast('Ses tanıma hatası: ' + event.error, 'error');
            stopVoiceRecording();
        };
        
        recognition.onend = function() {
            stopVoiceRecording();
        };
    } else {
        console.warn('Speech Recognition API desteklenmiyor');
        showToast('Tarayıcınız ses tanıma özelliğini desteklemiyor', 'error');
    }
}

// Ses kaydını başlat/durdur
function toggleVoiceRecording() {
    if (isRecording) {
        stopVoiceRecording();
    } else {
        startVoiceRecording();
    }
}

// Ses kaydını başlat
function startVoiceRecording() {
    if (!recognition) {
        initSpeechRecognition();
    }
    
    if (recognition) {
        try {
            recognition.start();
            isRecording = true;
            updateVoiceButton();
            showVoiceStatus('Ses kaydı başlatıldı...');
            showToast('Ses kaydı başlatıldı, konuşmaya başlayın', 'info');
        } catch (error) {
            console.error('Ses kaydı başlatma hatası:', error);
            showToast('Ses kaydı başlatılamadı', 'error');
        }
    }
}

// Ses kaydını durdur
function stopVoiceRecording() {
    if (recognition && isRecording) {
        try {
            recognition.stop();
        } catch (error) {
            console.error('Ses kaydı durdurma hatası:', error);
        }
    }
    
    isRecording = false;
    updateVoiceButton();
    hideVoiceStatus();
}

// Ses butonunu güncelle
function updateVoiceButton() {
    const voiceBtn = document.getElementById('voiceBtn');
    const icon = voiceBtn.querySelector('i');
    
    if (isRecording) {
        icon.className = 'fas fa-stop';
        voiceBtn.style.backgroundColor = '#ef4444';
        voiceBtn.style.color = 'white';
        voiceBtn.title = 'Ses kaydını durdur';
    } else {
        icon.className = 'fas fa-microphone';
        voiceBtn.style.backgroundColor = '';
        voiceBtn.style.color = '';
        voiceBtn.title = 'Ses ile soru sor';
    }
}

// Ses durumu göstergesini göster
function showVoiceStatus(message) {
    const voiceStatus = document.getElementById('voiceStatus');
    const statusText = voiceStatus.querySelector('span');
    const icon = voiceStatus.querySelector('i');
    
    if (isRecording) {
        icon.className = 'fas fa-microphone';
        statusText.textContent = message;
    } else {
        icon.className = 'fas fa-microphone-slash';
        statusText.textContent = 'Ses kaydı durduruldu';
    }
    
    voiceStatus.style.display = 'flex';
}

// Ses durumu göstergesini gizle
function hideVoiceStatus() {
    const voiceStatus = document.getElementById('voiceStatus');
    voiceStatus.style.display = 'none';
}

// DOM yüklendiğinde çalışacak fonksiyonlar
document.addEventListener('DOMContentLoaded', function() {
    // Moment.js Türkçe ayarları
    moment.locale('tr');
    
    // Temayı başlat
    initTheme();
    watchSystemTheme();
    
    // Speech Recognition'ı başlat
    initSpeechRecognition();
    
    // Sohbet geçmişini başlat
    initChatHistory();
    
    // Ayarları yükle ve uygula
    const settings = JSON.parse(localStorage.getItem('settings') || '{}');
    applySettings(settings);
    
    // Input alanına odaklan
    document.getElementById('messageInput').focus();
});

// Mesaj gönderme fonksiyonu
async function sendMessage(message = null) {
    const messageInput = document.getElementById('messageInput');
    const messageText = message || messageInput.value.trim();
    
    if (!messageText || isLoading) return;
    
    // Loading durumunu başlat
    setLoading(true);
    
    // Kullanıcı mesajını ekle
    addMessage(messageText, 'user');
    
    // Input alanını temizle
    messageInput.value = '';
    
    try {
        // API'ye istek gönder
        const sessionId = getCurrentSessionId();
        console.log('Session ID:', sessionId);
        console.log('Sending message:', messageText);
        
        const requestBody = { 
            message: messageText,
            session_id: sessionId
        };
        console.log('Request body:', requestBody);
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        const data = await response.json();
        
        // Bot yanıtını ekle
        addMessage(data.response, 'bot', data.type, data.data);
        
    } catch (error) {
        console.error('Hata:', error);
        addMessage('Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.', 'bot', 'error');
    } finally {
        // Loading durumunu bitir
        setLoading(false);
    }
}

// Mesaj ekleme fonksiyonu
function addMessage(text, sender, type = 'normal', data = null) {
    // Mesajı DOM'a ekle
    addMessageToDOM(text, sender, type, data, true);
    
    // Mesajı sohbet geçmişine kaydet
    if (currentChatId) {
        const currentChat = chatHistory.find(c => c.id === currentChatId);
        if (currentChat) {
            const message = {
                text,
                sender,
                type,
                data,
                timestamp: new Date().toISOString()
            };
            
            currentChat.messages.push(message);
            
            // Sohbet başlığını güncelle (ilk kullanıcı mesajından)
            if (sender === 'user' && currentChat.title === 'Yeni Sohbet') {
                currentChat.title = text.length > 30 ? text.substring(0, 30) + '...' : text;
            }
            
            // Sohbet önizlemesini güncelle
            currentChat.preview = text.length > 50 ? text.substring(0, 50) + '...' : text;
            currentChat.timestamp = new Date().toISOString();
            
            saveChatHistory();
            renderChatList();
        }
    }
}

// Mesajı DOM'a ekle
function addMessageToDOM(text, sender, type = 'normal', data = null, scroll = true) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    const currentTime = moment().format('HH:mm');
    
    messageDiv.className = `message ${sender}-message`;
    
    let avatarIcon = sender === 'bot' ? 'fas fa-robot' : 'fas fa-user';
    let senderName = sender === 'bot' ? 'Fintra Asistan' : 'Siz';
    
    // Mesaj içeriğini oluştur
    let messageContent = `
        <div class="message-avatar">
            <i class="${avatarIcon}"></i>
        </div>
        <div class="message-content">
            <div class="message-header">
                <span class="sender-name">${senderName}</span>
                <span class="message-time">${currentTime}</span>
            </div>
            <div class="message-text">${formatMessage(text, type, data)}</div>
        </div>
    `;
    
    messageDiv.innerHTML = messageContent;
    chatMessages.appendChild(messageDiv);
    
    // Mesajları en alta kaydır
    if (scroll) {
    scrollToBottom();
    }
}

// Mesaj formatlama fonksiyonu
function formatMessage(text, type, data) {
    console.log('Formatting message:', { text, type, data }); // Debug log
    
    if (type === 'prediction' && data) {
        return `
            ${text}
            <div class="prediction-result">
                <div class="prediction-item">
                    <span class="prediction-label">Mevcut Fiyat:</span>
                    <span class="prediction-value">${data.current_price} TL</span>
                </div>
                <div class="prediction-item">
                    <span class="prediction-label">Tahmin Edilen:</span>
                    <span class="prediction-value">${data.predicted_price} TL</span>
                </div>
                <div class="prediction-item">
                    <span class="prediction-label">Değişim:</span>
                    <span class="prediction-change ${data.change >= 0 ? 'positive' : 'negative'}">
                        ${data.change >= 0 ? '+' : ''}${data.change} TL (${data.change_percent >= 0 ? '+' : ''}${data.change_percent}%)
                    </span>
                </div>
                <div class="prediction-item">
                    <span class="prediction-label">Tahmin Tarihi:</span>
                    <span class="prediction-value">${data.prediction_date}</span>
                </div>
            </div>
        `;
    }
    
    // Teknik analiz için özel formatlama
    if (type === 'technical_analysis' && data) {
        console.log('Technical analysis data:', data);
        let chartsHtml = '';
        
        if (data.charts && data.charts.length > 0) {
            console.log('Charts found:', data.charts.length);
            chartsHtml = '<div class="technical-charts">';
            
            // Tüm grafikleri indir butonu (birden fazla grafik varsa)
            if (data.charts.length > 1) {
                chartsHtml += `
                    <div class="download-all-charts">
                        <button class="download-all-btn" onclick="downloadAllCharts()">
                            <i class="fas fa-download"></i>
                            Tüm Grafikleri İndir (${data.charts.length})
                        </button>
                    </div>
                `;
            }
            
            data.charts.forEach((chart, index) => {
                console.log(`Chart ${index}:`, chart.title, 'Data length:', chart.data.length);
                const chartId = `chart-${Date.now()}-${index}`;
                chartsHtml += `
                    <div class="chart-container" id="${chartId}-container">
                        <div class="chart-header">
                        <h4>${chart.title}</h4>
                            <div class="chart-controls">
                                <button class="chart-btn" onclick="downloadChart('${chartId}')" title="Grafiği İndir">
                                    <i class="fas fa-download"></i>
                                </button>
                                <button class="chart-btn" onclick="toggleChartSize('${chartId}')" title="Büyüt/Küçült">
                                    <i class="fas fa-expand"></i>
                                </button>
                                <button class="chart-btn" onclick="resetChartSize('${chartId}')" title="Orijinal Boyut">
                                    <i class="fas fa-compress"></i>
                                </button>
                                <button class="chart-btn close-chart-btn" onclick="closeExpandedChart('${chartId}')" title="Kapat" style="display: none;">
                                    <i class="fas fa-times"></i>
                                </button>
                            </div>
                        </div>
                        <div class="chart-image" id="${chartId}">
                            ${chart.data}
                        </div>
                    </div>
                `;
            });
            chartsHtml += '</div>';
        } else {
            console.log('No charts found in data');
        }
        
        return `
            <div class="technical-analysis">
                <div class="analysis-content">
                    ${text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\*(.*?)\*/g, '<em>$1</em>')
                          .replace(/\n/g, '<br>')}
                </div>
                ${chartsHtml}
            </div>
        `;
    }
    
    // AI response için özel formatlama
    if (type === 'ai_response') {
        return `
            <div class="ai-response">
                <div class="ai-icon">
                    <i class="fas fa-brain"></i>
                </div>
                <div class="ai-content">
                    ${text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                          .replace(/\*(.*?)\*/g, '<em>$1</em>')
                          .replace(/\n/g, '<br>')}
                </div>
            </div>
        `;
    }
    
    // Markdown benzeri formatlamayı HTML'e çevir
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

// Loading durumu yönetimi
function setLoading(loading) {
    isLoading = loading;
    const loadingOverlay = document.getElementById('loadingOverlay');
    const sendBtn = document.querySelector('.send-btn');
    
    if (loading) {
        loadingOverlay.classList.add('show');
        sendBtn.disabled = true;
    } else {
        loadingOverlay.classList.remove('show');
        sendBtn.disabled = false;
    }
}

// Mesajları en alta kaydırma
function scrollToBottom() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Enter tuşu ile mesaj gönderme
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Yeni sohbet başlatma
function startNewChat() {
    createNewChat();
    
    // Önerileri göster
    const suggestedPrompts = document.getElementById('suggestedPrompts');
    suggestedPrompts.style.display = 'flex';
    
    // Input alanını temizle ve odaklan
    const messageInput = document.getElementById('messageInput');
    messageInput.value = '';
    messageInput.focus();
}

// Öneri butonlarını gizleme (tahmin yapıldıktan sonra)
function hideSuggestedPrompts() {
    const suggestedPrompts = document.getElementById('suggestedPrompts');
    suggestedPrompts.style.display = 'none';
}

// Tahmin yapıldığında önerileri gizle
document.addEventListener('DOMContentLoaded', function() {
    // Tahmin butonlarına tıklandığında önerileri gizle
    const predictionButtons = document.querySelectorAll('.prompt-btn');
    predictionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const buttonText = this.textContent.trim();
            if (buttonText.includes('tahmin') || buttonText.includes('ne olacak') || 
                buttonText.includes('Yükselir') || buttonText.includes('Düşer')) {
                setTimeout(hideSuggestedPrompts, 1000);
            }
        });
    });
});

// Hata mesajları için toast bildirimi
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Toast stilleri
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#06b6d4'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1001;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    // Animasyon
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    // Otomatik kaldırma
    setTimeout(() => {
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}

// Sayfa yüklendiğinde hoş geldin mesajı
window.addEventListener('load', function() {
    // Sayfa yüklendiğinde input alanına odaklan
    setTimeout(() => {
        document.getElementById('messageInput').focus();
    }, 500);
});

// Responsive tasarım için sidebar toggle
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('show');
}

// Mobil cihazlarda sidebar'ı gizle
if (window.innerWidth <= 768) {
    const sidebar = document.querySelector('.sidebar');
    sidebar.style.display = 'none';
}

// Pencere boyutu değiştiğinde responsive ayarları
window.addEventListener('resize', function() {
    const sidebar = document.querySelector('.sidebar');
    if (window.innerWidth <= 768) {
        sidebar.style.display = 'none';
    } else {
        sidebar.style.display = 'flex';
    }
}); 

// Dosya yükleme modalını aç
function openFileUpload() {
    document.getElementById('fileInput').click();
}

// Dosya yükleme işlemi
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Dosya boyutu kontrolü (10MB)
    if (file.size > 10 * 1024 * 1024) {
        showToast('Dosya boyutu 10MB\'dan büyük olamaz', 'error');
        return;
    }
    
    // Dosya türü kontrolü
    const allowedTypes = [
        'application/pdf',
        'image/jpeg',
        'image/jpg',
        'image/png',
        'image/gif',
        'text/plain',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    
    if (!allowedTypes.includes(file.type)) {
        showToast('Desteklenmeyen dosya türü', 'error');
        return;
    }
    
    try {
        // Loading göster
        setLoading(true);
        
        // FormData oluştur
        const formData = new FormData();
        formData.append('file', file);
        
        // Dosyayı yükle
        const response = await fetch('/api/add_document', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('Dosya başarıyla yüklendi!', 'success');
            
            // Kullanıcı mesajı olarak dosya bilgisini ekle
            const fileInfo = `📎 Dosya yüklendi: ${file.name} (${formatFileSize(file.size)})`;
            addMessage(fileInfo, 'user', 'file_upload');
            
            // Bot yanıtı
            const botResponse = `Dosyanız başarıyla yüklendi: **${file.name}**
            
Dosya türü: ${file.type}
Boyut: ${formatFileSize(file.size)}

Bu dosyayı analiz etmek için sorularınızı sorabilirsiniz.`;
            
            addMessage(botResponse, 'bot', 'file_upload_response');
            
        } else {
            showToast('Dosya yükleme hatası: ' + result.message, 'error');
        }
        
    } catch (error) {
        console.error('Dosya yükleme hatası:', error);
        showToast('Dosya yükleme sırasında hata oluştu', 'error');
    } finally {
        setLoading(false);
        // Input'u temizle
        event.target.value = '';
    }
}

// Dosya boyutunu formatla
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Ekran görüntüsü alma
async function takeScreenshot() {
    try {
        showToast('Ekran görüntüsü alınıyor...', 'info');
        
        // html2canvas kütüphanesini yükle (eğer yoksa)
        if (typeof html2canvas === 'undefined') {
            await loadHtml2Canvas();
        }
        
        // Chat alanının ekran görüntüsünü al
        const chatArea = document.querySelector('.main-chat');
        const canvas = await html2canvas(chatArea, {
            backgroundColor: '#ffffff',
            scale: 2, // Yüksek kalite
            useCORS: true,
            allowTaint: true
        });
        
        // Canvas'ı blob'a çevir
        canvas.toBlob(async (blob) => {
            // Dosya adı oluştur
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `kchol-chat-${timestamp}.png`;
            
            // Dosyayı indir
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showToast('Ekran görüntüsü başarıyla kaydedildi!', 'success');
            
            // Kullanıcı mesajı olarak ekle
            const screenshotInfo = `📸 Ekran görüntüsü alındı: ${filename}`;
            addMessage(screenshotInfo, 'user', 'screenshot');
            
        }, 'image/png', 0.9);
        
    } catch (error) {
        console.error('Ekran görüntüsü hatası:', error);
        showToast('Ekran görüntüsü alınamadı', 'error');
    }
}

// html2canvas kütüphanesini dinamik olarak yükle
async function loadHtml2Canvas() {
    return new Promise((resolve, reject) => {
        if (typeof html2canvas !== 'undefined') {
            resolve();
            return;
        }
        
        const script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
} 

// Arama modalını aç
function openSearchModal() {
    const searchModal = document.getElementById('searchModal');
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    
    searchModal.classList.add('show');
    
    // Arama alanını temizle ve odaklan
    if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
    }
    
    // Arama sonuçlarını temizle
    if (searchResults) {
        searchResults.innerHTML = '<div class="no-results">Arama yapmak için yazmaya başlayın...</div>';
    }
}

// Arama modalını kapat
function closeSearchModal() {
    const searchModal = document.getElementById('searchModal');
    searchModal.classList.remove('show');
    
    // Arama timeout'unu temizle
    if (window.searchTimeout) {
        clearTimeout(window.searchTimeout);
        window.searchTimeout = null;
    }
}

// Paylaşım modalını aç
function openShareModal() {
    const shareModal = document.getElementById('shareModal');
    shareModal.classList.add('show');
    
    // Paylaşım önizlemesini güncelle
    updateSharePreview();
}

// Paylaşım modalını kapat
function closeShareModal() {
    const shareModal = document.getElementById('shareModal');
    shareModal.classList.remove('show');
}

// Paylaşım önizlemesini güncelle
function updateSharePreview() {
    const preview = document.getElementById('sharePreview');
    const messages = document.querySelectorAll('.message');
    let chatContent = '';
    
    // Son 5 mesajı al
    const recentMessages = Array.from(messages).slice(-5);
    recentMessages.forEach(msg => {
        const sender = msg.classList.contains('user-message') ? 'Siz' : 'Fintra Asistan';
        const text = msg.querySelector('.message-text').textContent;
        chatContent += `${sender}: ${text}\n`;
    });
    
    preview.textContent = chatContent.substring(0, 200) + '...';
}

// WhatsApp'ta paylaş
function shareToWhatsApp() {
    const text = encodeURIComponent('KCHOL Hisse Senedi Asistanı ile sohbet ettim! 📈');
    window.open(`https://wa.me/?text=${text}`, '_blank');
}

// Telegram'da paylaş
function shareToTelegram() {
    const text = encodeURIComponent('KCHOL Hisse Senedi Asistanı ile sohbet ettim! 📈');
    window.open(`https://t.me/share/url?url=${encodeURIComponent(window.location.href)}&text=${text}`, '_blank');
}

// E-posta ile paylaş
function shareToEmail() {
    const subject = encodeURIComponent('KCHOL Hisse Senedi Asistanı');
    const body = encodeURIComponent('KCHOL Hisse Senedi Asistanı ile sohbet ettim! 📈\n\n' + window.location.href);
    window.open(`mailto:?subject=${subject}&body=${body}`, '_blank');
}

// Panoya kopyala
function copyToClipboard() {
    const messages = document.querySelectorAll('.message');
    let chatContent = 'KCHOL Hisse Senedi Asistanı - Sohbet Geçmişi\n\n';
    
    messages.forEach(msg => {
        const sender = msg.classList.contains('user-message') ? 'Siz' : 'KCHOL Asistan';
        const text = msg.querySelector('.message-text').textContent;
        chatContent += `${sender}: ${text}\n\n`;
    });
    
    navigator.clipboard.writeText(chatContent).then(() => {
        showToast('Sohbet geçmişi panoya kopyalandı!', 'success');
    }).catch(() => {
        showToast('Kopyalama başarısız', 'error');
    });
}

// Twitter'da paylaş
function shareToTwitter() {
    const text = encodeURIComponent('KCHOL Hisse Senedi Asistanı ile sohbet ettim! 📈 #KCHOL #Finans');
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${encodeURIComponent(window.location.href)}`, '_blank');
}

// LinkedIn'de paylaş
function shareToLinkedIn() {
    const text = encodeURIComponent('KCHOL Hisse Senedi Asistanı ile sohbet ettim! 📈');
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(window.location.href)}`, '_blank');
}

// Sohbet geçmişini indir
async function downloadChatHistory(format = 'txt') {
    try {
        showToast('Sohbet geçmişi hazırlanıyor...', 'info');
        
        // Session ID olmadan direkt istek gönder (backend mevcut oturumu kullanacak)
        const url = `/api/chat_history?format=${format}`;
        
        const response = await fetch(url);
        if (response.ok) {
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            
            // Format'a göre dosya adı
            const timestamp = new Date().toISOString().split('T')[0];
            const extension = format === 'json' ? 'json' : format === 'html' ? 'html' : 'txt';
            a.download = `kchol_chat_history_${timestamp}.${extension}`;
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);
            
            const formatNames = {
                'txt': 'Metin',
                'json': 'JSON',
                'html': 'HTML'
            };
            
            showToast(`${formatNames[format]} formatında sohbet geçmişi indirildi!`, 'success');
        } else {
            const errorData = await response.json();
            showToast('Sohbet geçmişi indirilemedi: ' + errorData.message, 'error');
        }
    } catch (error) {
        console.error('İndirme hatası:', error);
        showToast('İndirme sırasında hata oluştu', 'error');
    }
}

// Mesajlarda arama yap
function searchMessages(event) {
    if (event.key === 'Enter') {
        performSearch();
    } else if (event.key === 'Escape') {
        closeSearchModal();
    } else {
        // Gerçek zamanlı arama (500ms gecikme ile)
        clearTimeout(window.searchTimeout);
        window.searchTimeout = setTimeout(() => {
            const searchTerm = event.target.value.trim();
            if (searchTerm.length > 0) {
                performSearch();
            } else {
                const searchResults = document.getElementById('searchResults');
                if (searchResults) {
                    searchResults.innerHTML = '<div class="no-results">Arama yapmak için yazmaya başlayın...</div>';
                }
            }
        }, 500);
    }
}

// Arama işlemini gerçekleştir
function performSearch() {
    try {
        const searchTerm = document.getElementById('searchInput').value.toLowerCase();
        const messages = document.querySelectorAll('.message');
        const searchResults = document.getElementById('searchResults');
        
        console.log('Arama yapılıyor:', { searchTerm, messageCount: messages.length });
        
        if (!searchResults) {
            console.error('searchResults element bulunamadı');
            return;
        }
        
        if (!searchTerm.trim()) {
            searchResults.innerHTML = '<div class="no-results">Arama terimi girin</div>';
            return;
        }
        
        if (messages.length === 0) {
            searchResults.innerHTML = '<div class="no-results">Henüz mesaj bulunmuyor</div>';
            return;
        }
        
        const results = [];
        messages.forEach((msg, index) => {
            try {
                const messageText = msg.querySelector('.message-text');
                const messageTime = msg.querySelector('.message-time');
                
                if (messageText && messageTime) {
                    const text = messageText.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        const sender = msg.classList.contains('user-message') ? 'Siz' : 'Fintra Asistan';
                        const time = messageTime.textContent;
                        results.push({
                            sender,
                            text: messageText.textContent,
                            time,
                            index
                        });
                    }
                }
            } catch (error) {
                console.error('Mesaj işlenirken hata:', error, msg);
            }
        });
        
        console.log('Arama sonuçları:', results);
        displayChatSearchResults(results, searchTerm);
        
    } catch (error) {
        console.error('Arama işlemi hatası:', error);
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            searchResults.innerHTML = '<div class="no-results">Arama sırasında hata oluştu</div>';
        }
    }
}

// Arama sonuçlarını göster (sohbet araması için)
function displayChatSearchResults(results, searchTerm) {
    try {
        const searchResults = document.getElementById('searchResults');
        
        if (!searchResults) {
            console.error('searchResults element bulunamadı');
            return;
        }
        
        if (!Array.isArray(results)) {
            console.error('Geçersiz sonuç formatı:', results);
            searchResults.innerHTML = '<div class="no-results">Arama sonuçları yüklenemedi</div>';
            return;
        }
        
        if (results.length === 0) {
            searchResults.innerHTML = '<div class="no-results">Sonuç bulunamadı</div>';
            return;
        }
        
        let html = '';
        results.forEach((result, index) => {
            try {
                if (result && typeof result === 'object') {
                    const highlightedText = (result.text || '').replace(
                        new RegExp(searchTerm, 'gi'),
                        match => `<span class="search-highlight">${match}</span>`
                    );
                    
                    html += `
                        <div class="search-result-item" onclick="scrollToMessage(${result.index || index})">
                            <div class="search-result-sender">${result.sender || 'Bilinmeyen'}</div>
                            <div class="search-result-text">${highlightedText}</div>
                            <div class="search-result-time">${result.time || ''}</div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Sonuç öğesi işlenirken hata:', error, result);
            }
        });
        
        searchResults.innerHTML = html;
        
    } catch (error) {
        console.error('Arama sonuçları gösterme hatası:', error);
        const searchResults = document.getElementById('searchResults');
        if (searchResults) {
            searchResults.innerHTML = '<div class="no-results">Sonuçlar gösterilirken hata oluştu</div>';
        }
    }
}

// Mesaja kaydır
function scrollToMessage(index) {
    const messages = document.querySelectorAll('.message');
    if (messages[index]) {
        messages[index].scrollIntoView({ behavior: 'smooth', block: 'center' });
        messages[index].style.backgroundColor = '#fef3c7';
        setTimeout(() => {
            messages[index].style.backgroundColor = '';
        }, 2000);
        closeSearchModal();
    }
}

// Mesaja kaydır
function scrollToMessage(index) {
    const messages = document.querySelectorAll('.message');
    if (messages[index]) {
        messages[index].scrollIntoView({ behavior: 'smooth', block: 'center' });
        messages[index].style.backgroundColor = '#fef3c7';
        setTimeout(() => {
            messages[index].style.backgroundColor = '';
        }, 2000);
        closeSearchModal();
    }
} 

// Download dropdown'ı aç/kapat
function toggleDownloadDropdown() {
    const downloadOptions = document.getElementById('downloadOptions');
    downloadOptions.classList.toggle('show');
    
    // Diğer dropdown'ları kapat
    closeSearchModal();
    closeShareModal();
}

// Sayfa dışına tıklandığında dropdown'ları kapat
document.addEventListener('click', function(event) {
    const downloadDropdown = document.querySelector('.download-dropdown');
    const downloadOptions = document.getElementById('downloadOptions');
    const themeModal = document.getElementById('themeModal');
    const helpModal = document.getElementById('helpModal');
    const settingsModal = document.getElementById('settingsModal');
    
    if (downloadDropdown && !downloadDropdown.contains(event.target)) {
        downloadOptions.classList.remove('show');
    }
    
    // Tema modal'ını kapat
    if (themeModal && event.target === themeModal) {
        closeThemeModal();
    }
    
    // Yardım modal'ını kapat
    if (helpModal && event.target === helpModal) {
        closeHelpModal();
    }
    
    // Ayarlar modal'ını kapat
    if (settingsModal && event.target === settingsModal) {
        closeSettingsModal();
    }
}); 

// Grafik indirme fonksiyonu
async function downloadChart(chartId) {
    try {
        showToast('Grafik indiriliyor...', 'info');
        
        const chartElement = document.getElementById(chartId);
        if (!chartElement) {
            showToast('Grafik bulunamadı', 'error');
            return;
        }
        
        // html2canvas kütüphanesini yükle (eğer yoksa)
        if (typeof html2canvas === 'undefined') {
            await loadHtml2Canvas();
        }
        
        // Grafiğin ekran görüntüsünü al
        const canvas = await html2canvas(chartElement, {
            backgroundColor: '#ffffff',
            scale: 2, // Yüksek kalite
            useCORS: true,
            allowTaint: true,
            logging: false
        });
        
        // Canvas'ı blob'a çevir
        canvas.toBlob(async (blob) => {
            // Dosya adı oluştur
            const chartTitle = chartElement.closest('.chart-container').querySelector('h4').textContent;
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const filename = `${chartTitle.replace(/[^a-zA-Z0-9]/g, '_')}_${timestamp}.png`;
            
            // Dosyayı indir
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showToast('Grafik başarıyla indirildi!', 'success');
            
        }, 'image/png', 0.9);
        
    } catch (error) {
        console.error('Grafik indirme hatası:', error);
        showToast('Grafik indirilemedi', 'error');
    }
}

// Tüm grafikleri indir
async function downloadAllCharts() {
    try {
        const chartContainers = document.querySelectorAll('.chart-container');
        if (chartContainers.length === 0) {
            showToast('İndirilecek grafik bulunamadı', 'error');
            return;
        }
        
        showToast(`${chartContainers.length} grafik indiriliyor...`, 'info');
        
        // html2canvas kütüphanesini yükle (eğer yoksa)
        if (typeof html2canvas === 'undefined') {
            await loadHtml2Canvas();
        }
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        
        for (let i = 0; i < chartContainers.length; i++) {
            const container = chartContainers[i];
            const chartElement = container.querySelector('.chart-image');
            const chartTitle = container.querySelector('h4').textContent;
            
            try {
                // Grafiğin ekran görüntüsünü al
                const canvas = await html2canvas(chartElement, {
                    backgroundColor: '#ffffff',
                    scale: 2,
                    useCORS: true,
                    allowTaint: true,
                    logging: false
                });
                
                // Canvas'ı blob'a çevir
                canvas.toBlob(async (blob) => {
                    const filename = `${chartTitle.replace(/[^a-zA-Z0-9]/g, '_')}_${timestamp}_${i + 1}.png`;
                    
                    // Dosyayı indir
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }, 'image/png', 0.9);
                
                // Grafikler arasında kısa bir bekleme
                await new Promise(resolve => setTimeout(resolve, 500));
                
            } catch (error) {
                console.error(`Grafik ${i + 1} indirme hatası:`, error);
            }
        }
        
        showToast('Tüm grafikler başarıyla indirildi!', 'success');
        
    } catch (error) {
        console.error('Toplu grafik indirme hatası:', error);
        showToast('Grafikler indirilirken hata oluştu', 'error');
    }
}

// Grafik boyutunu değiştir
function toggleChartSize(chartId) {
    const chartContainer = document.getElementById(`${chartId}-container`);
    const chartImage = document.getElementById(chartId);
    const expandBtn = chartContainer.querySelector('.fa-expand');
    const compressBtn = chartContainer.querySelector('.fa-compress');
    const closeBtn = chartContainer.querySelector('.close-chart-btn');
    
    if (chartContainer.classList.contains('expanded')) {
        // Küçült
        chartContainer.classList.remove('expanded');
        chartImage.style.maxWidth = '100%';
        chartImage.style.maxHeight = '300px';
        expandBtn.style.display = 'inline';
        compressBtn.style.display = 'none';
        closeBtn.style.display = 'none';
        showToast('Grafik küçültüldü', 'info');
    } else {
        // Büyüt
        chartContainer.classList.add('expanded');
        chartImage.style.maxWidth = '90vw';
        chartImage.style.maxHeight = '70vh';
        expandBtn.style.display = 'none';
        compressBtn.style.display = 'inline';
        closeBtn.style.display = 'inline';
        showToast('Grafik büyütüldü', 'info');
    }
}

// Grafik boyutunu sıfırla
function resetChartSize(chartId) {
    const chartContainer = document.getElementById(`${chartId}-container`);
    const chartImage = document.getElementById(chartId);
    const expandBtn = chartContainer.querySelector('.fa-expand');
    const compressBtn = chartContainer.querySelector('.fa-compress');
    const closeBtn = chartContainer.querySelector('.close-chart-btn');
    
    chartContainer.classList.remove('expanded');
    chartImage.style.maxWidth = '100%';
    chartImage.style.maxHeight = '300px';
    expandBtn.style.display = 'inline';
    compressBtn.style.display = 'none';
    closeBtn.style.display = 'none';
    showToast('Grafik orijinal boyuta getirildi', 'info');
} 

// Genişletilmiş grafikleri kapat
function closeExpandedChart(chartId) {
    const chartContainer = document.getElementById(`${chartId}-container`);
    const chartImage = document.getElementById(chartId);
    const expandBtn = chartContainer.querySelector('.fa-expand');
    const compressBtn = chartContainer.querySelector('.fa-compress');
    const closeBtn = chartContainer.querySelector('.close-chart-btn');
    
    chartContainer.classList.remove('expanded');
    chartImage.style.maxWidth = '100%';
    chartImage.style.maxHeight = '300px';
    expandBtn.style.display = 'inline';
    compressBtn.style.display = 'none';
    closeBtn.style.display = 'none';
    showToast('Grafik kapatıldı', 'info');
} 

 

// Yardım modal'ını aç
function openHelpModal() {
    const helpModal = document.getElementById('helpModal');
    helpModal.classList.add('show');
}

// Yardım modal'ını kapat
function closeHelpModal() {
    const helpModal = document.getElementById('helpModal');
    helpModal.classList.remove('show');
}

// Yardım modal'ından soru gönder
function sendHelpQuestion(question) {
    closeHelpModal();
    
    // Mesajı input'a yaz ve gönder
    const messageInput = document.getElementById('messageInput');
    messageInput.value = question;
    
    // Kısa bir gecikme ile gönder
    setTimeout(() => {
        sendMessage();
    }, 100);
}

// Klavye kısayolları
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + K ile arama modalını aç
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        openSearchModal();
    }
    
    // ESC tuşu ile modalları kapat
    if (event.key === 'Escape') {
        const expandedCharts = document.querySelectorAll('.chart-container.expanded');
        if (expandedCharts.length > 0) {
            expandedCharts.forEach(chart => {
                const chartId = chart.id.replace('-container', '');
                closeExpandedChart(chartId);
            });
        } else {
            closeSearchModal();
            closeShareModal();
            closeThemeModal();
            closeHelpModal();
            closeSettingsModal();
        }
    }
}); 

// Sohbet geçmişi yönetimi
function initChatHistory() {
    // Local storage'dan sohbet geçmişini yükle
    const savedHistory = localStorage.getItem('chatHistory');
    if (savedHistory) {
        chatHistory = JSON.parse(savedHistory);
        renderChatList();
    } else {
        // İlk sohbeti oluştur
        createNewChat();
    }
}

// Yeni sohbet oluştur
function createNewChat() {
    const chatId = Date.now().toString();
    const newChat = {
        id: chatId,
        title: 'Yeni Sohbet',
        preview: 'Henüz mesaj yok',
        timestamp: new Date().toISOString(),
        messages: []
    };
    
    chatHistory.unshift(newChat);
    currentChatId = chatId;
    
    saveChatHistory();
    renderChatList();
    clearChatMessages();
    showWelcomeMessage();
}

// Sohbet geçmişini kaydet
function saveChatHistory() {
    localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
}

// Sohbet listesini render et
function renderChatList() {
    const chatList = document.getElementById('chatList');
    const noChats = document.getElementById('noChats');
    
    if (chatHistory.length === 0) {
        chatList.style.display = 'none';
        noChats.style.display = 'flex';
        return;
    }
    
    chatList.style.display = 'flex';
    noChats.style.display = 'none';
    
    chatList.innerHTML = '';
    
    chatHistory.forEach(chat => {
        const chatItem = document.createElement('div');
        chatItem.className = `chat-list-item ${chat.id === currentChatId ? 'active' : ''}`;
        chatItem.onclick = () => switchToChat(chat.id);
        
        const timeAgo = getTimeAgo(new Date(chat.timestamp));
        
        chatItem.innerHTML = `
            <div class="chat-icon">
                <i class="fas fa-comment"></i>
            </div>
            <div class="chat-content">
                <div class="chat-title">${chat.title}</div>
                <div class="chat-preview">${chat.preview}</div>
            </div>
            <div class="chat-time">${timeAgo}</div>
            <button class="delete-chat" onclick="deleteChat('${chat.id}', event)" title="Sohbeti Sil">
                <i class="fas fa-trash"></i>
            </button>
        `;
        
        chatList.appendChild(chatItem);
    });
}

// Sohbete geç
function switchToChat(chatId) {
    currentChatId = chatId;
    const chat = chatHistory.find(c => c.id === chatId);
    
    if (chat) {
        renderChatList();
        loadChatMessages(chat);
    }
}

// Sohbet mesajlarını yükle
function loadChatMessages(chat) {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';
    
    if (chat.messages.length === 0) {
        showWelcomeMessage();
    } else {
        chat.messages.forEach(msg => {
            addMessageToDOM(msg.text, msg.sender, msg.type, msg.data, false);
        });
    }
    
    scrollToBottom();
}

// Sohbeti sil
function deleteChat(chatId, event) {
    event.stopPropagation();
    
    if (confirm('Bu sohbeti silmek istediğinizden emin misiniz?')) {
        const index = chatHistory.findIndex(c => c.id === chatId);
        if (index > -1) {
            chatHistory.splice(index, 1);
            
            // Eğer silinen sohbet aktif sohbetse, ilk sohbete geç
            if (chatId === currentChatId) {
                if (chatHistory.length > 0) {
                    currentChatId = chatHistory[0].id;
                    switchToChat(currentChatId);
                } else {
                    createNewChat();
                }
            }
            
            saveChatHistory();
            renderChatList();
        }
    }
}

// Zaman önce hesapla
function getTimeAgo(date) {
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Şimdi';
    if (diffInMinutes < 60) return `${diffInMinutes} dk`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} sa`;
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays} gün`;
    
    return date.toLocaleDateString('tr-TR');
}

// Hoş geldin mesajını göster
function showWelcomeMessage() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = `
        <div class="message bot-message">
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="sender-name">Fintra Asistan</span>
                    <span class="message-time">${new Date().toLocaleTimeString('tr-TR', {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
                <div class="message-text">
                    <h3> Hisse Senedi Fiyat Tahmini Asistanına Hoş Geldiniz!</h3>
                    <p>Ben yapay zeka destekli bir finans uzmanıyım ve size yardımcı olmak için buradayım.</p>
                    <p> Hisse senedi fiyat tahmini yapmak için aşağıdaki önerilerden birini seçebilir veya kendi sorunuzu yazabilirsiniz.</p>
                    <p><strong>Yeni Özellik:</strong> Artık Finans, yatırım ve ekonomi hakkında her türlü sorunuzu yanıtlayabilirim!</p>
                </div>
            </div>
        </div>
    `;
}

// Chat mesajlarını temizle
function clearChatMessages() {
    const chatMessages = document.getElementById('chatMessages');
    chatMessages.innerHTML = '';
} 

// Ayarlar modal'ını aç
function openSettingsModal() {
    const settingsModal = document.getElementById('settingsModal');
    settingsModal.classList.add('show');
    loadSettings();
}

// Ayarlar modal'ını kapat
function closeSettingsModal() {
    const settingsModal = document.getElementById('settingsModal');
    settingsModal.classList.remove('show');
    saveSettings();
}

// Ayarları yükle
function loadSettings() {
    const settings = JSON.parse(localStorage.getItem('settings') || '{}');
    
    // Toggle switch'leri ayarla
    document.getElementById('autoSave').checked = settings.autoSave !== false;
    document.getElementById('autoScroll').checked = settings.autoScroll !== false;
    document.getElementById('showSuggestions').checked = settings.showSuggestions !== false;
    document.getElementById('voiceRecognition').checked = settings.voiceRecognition !== false;
    
    // Select'leri ayarla
    document.getElementById('voiceLanguage').value = settings.voiceLanguage || 'tr-TR';
    document.getElementById('chartQuality').value = settings.chartQuality || '2';
    document.getElementById('chartFormat').value = settings.chartFormat || 'png';
}

// Ayarları kaydet
function saveSettings() {
    const settings = {
        autoSave: document.getElementById('autoSave').checked,
        autoScroll: document.getElementById('autoScroll').checked,
        showSuggestions: document.getElementById('showSuggestions').checked,
        voiceRecognition: document.getElementById('voiceRecognition').checked,
        voiceLanguage: document.getElementById('voiceLanguage').value,
        chartQuality: document.getElementById('chartQuality').value,
        chartFormat: document.getElementById('chartFormat').value
    };
    
    localStorage.setItem('settings', JSON.stringify(settings));
    
    // Ayarları uygula
    applySettings(settings);
}

// Ayarları uygula
function applySettings(settings) {
    // Ses tanıma ayarlarını uygula
    if (recognition) {
        recognition.lang = settings.voiceLanguage;
    }
    
    // Önerilen soruları göster/gizle
    const suggestedPrompts = document.getElementById('suggestedPrompts');
    if (suggestedPrompts) {
        suggestedPrompts.style.display = settings.showSuggestions ? 'flex' : 'none';
    }
    
    showToast('Ayarlar kaydedildi', 'success');
}

// Tüm sohbetleri temizle
function clearAllChats() {
    if (confirm('Tüm sohbet geçmişini silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.')) {
        chatHistory = [];
        currentChatId = null;
        localStorage.removeItem('chatHistory');
        createNewChat();
        showToast('Tüm sohbetler temizlendi', 'success');
    }
}

// Ayarları sıfırla
function resetSettings() {
    // Ayarları varsayılana döndür
    localStorage.removeItem('theme');
    localStorage.removeItem('settings');
    
    // Varsayılan ayarları uygula
    applyTheme('light');
    applySettings({
        autoSave: true,
        autoScroll: true,
        showSuggestions: true,
        voiceRecognition: true,
        voiceLanguage: 'tr-TR',
        chartQuality: 2,
        chartFormat: 'png'
    });
    
    showToast('Ayarlar varsayılana döndürüldü', 'success');
    closeSettingsModal();
}

// Simulation Modal Functions
function openSimulationModal() {
    const simulationModal = document.getElementById('simulationModal');
    simulationModal.classList.add('show');
    
    // Reset form
    resetSimulationForm();
    
    // Hide result section
    const resultSection = document.getElementById('simulationResult');
    resultSection.style.display = 'none';
}

function closeSimulationModal() {
    const simulationModal = document.getElementById('simulationModal');
    simulationModal.classList.remove('show');
}

function resetSimulationForm() {
    document.getElementById('simulationStock').value = 'KCHOL.IS';
    document.getElementById('simulationDate').value = '6 ay önce';
    document.getElementById('simulationAmount').value = '10000';
}

function loadSimulationExample(stock, date, amount) {
    document.getElementById('simulationStock').value = stock;
    document.getElementById('simulationDate').value = date;
    document.getElementById('simulationAmount').value = amount;
    
    // Highlight the clicked example button
    const exampleButtons = document.querySelectorAll('.example-btn');
    exampleButtons.forEach(btn => btn.classList.remove('active'));
    
    // Find and highlight the clicked button
    const clickedButton = Array.from(exampleButtons).find(btn => 
        btn.textContent.includes(stock.split('.')[0]) && 
        btn.textContent.includes(amount.toString())
    );
    
    if (clickedButton) {
        clickedButton.classList.add('active');
        setTimeout(() => clickedButton.classList.remove('active'), 2000);
    }
}

async function runSimulation() {
    const stock = document.getElementById('simulationStock').value.trim();
    const date = document.getElementById('simulationDate').value.trim();
    const amount = parseFloat(document.getElementById('simulationAmount').value);
    
    // Validation
    if (!stock) {
        showToast('Lütfen hisse kodunu girin', 'error');
        return;
    }
    
    if (!date) {
        showToast('Lütfen başlangıç tarihini girin', 'error');
        return;
    }
    
    if (!amount || amount < 100) {
        showToast('Lütfen geçerli bir yatırım tutarı girin (minimum 100 TL)', 'error');
        return;
    }
    
    // Show loading state
    const resultSection = document.getElementById('simulationResult');
    const resultContent = document.getElementById('resultContent');
    
    resultSection.style.display = 'block';
    resultContent.innerHTML = `
        <div class="simulation-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Simülasyon hesaplanıyor...</p>
        </div>
    `;
    
    // Scroll to result
    resultSection.scrollIntoView({ behavior: 'smooth' });
    
    try {
        // Create simulation message
        const simulationMessage = `${stock} hissesine ${date} ${amount.toLocaleString('tr-TR')} TL yatırsaydım ne olurdu?`;
        
        // Send to chat API
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: simulationMessage
            })
        });
        
        const data = await response.json();
        
        if (data.success === false) {
            throw new Error(data.response || 'Simülasyon hatası');
        }
        
        // Display result
        displaySimulationResult(data);
        
    } catch (error) {
        console.error('Simulation error:', error);
        resultContent.innerHTML = `
            <div class="simulation-error">
                <i class="fas fa-exclamation-triangle"></i>
                <span>Simülasyon hatası: ${error.message}</span>
            </div>
        `;
    }
}

function displaySimulationResult(data) {
    const resultContent = document.getElementById('resultContent');
    
    if (data.type === 'simulation' && data.data) {
        const simData = data.data;
        
        // Check if there's an error
        if (simData.hata) {
            resultContent.innerHTML = `
                <div class="simulation-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>${simData.hata}</span>
                </div>
            `;
            return;
        }
        
        // Format the result
        const profitClass = simData['net kazanç'] > 0 ? 'profit' : simData['net kazanç'] < 0 ? 'loss' : 'neutral';
        const profitIcon = simData['net kazanç'] > 0 ? '🟢' : simData['net kazanç'] < 0 ? '🔴' : '⚪';
        
        resultContent.innerHTML = `
            <div class="result-item">
                <span class="result-label">Hisse Kodu:</span>
                <span class="result-value">${simData.hisse}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Başlangıç Tarihi:</span>
                <span class="result-value">${simData['başlangıç tarihi']}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Yatırım Tutarı:</span>
                <span class="result-value">${parseFloat(simData['şu anki değer'] - simData['net kazanç']).toLocaleString('tr-TR')} TL</span>
            </div>
            <div class="result-item">
                <span class="result-label">Başlangıç Fiyatı:</span>
                <span class="result-value">${simData['başlangıç fiyatı']} TL</span>
            </div>
            <div class="result-item">
                <span class="result-label">Güncel Fiyat:</span>
                <span class="result-value">${simData['güncel fiyat']} TL</span>
            </div>
            <div class="result-item">
                <span class="result-label">Alınan Lot:</span>
                <span class="result-value">${simData['alınan lot']} adet</span>
            </div>
            <div class="result-item">
                <span class="result-label">Şu Anki Değer:</span>
                <span class="result-value">${simData['şu anki değer'].toLocaleString('tr-TR')} TL</span>
            </div>
            <div class="result-item">
                <span class="result-label">Net Kazanç:</span>
                <span class="result-value ${profitClass}">${profitIcon} ${simData['net kazanç'].toLocaleString('tr-TR')} TL</span>
            </div>
            <div class="result-item">
                <span class="result-label">Getiri Oranı:</span>
                <span class="result-value ${profitClass}">%${simData['getiri %'].toFixed(2)}</span>
            </div>
        `;
        
        // Store result for sharing/downloading
        window.lastSimulationResult = {
            data: simData,
            timestamp: new Date().toISOString(),
            message: data.response
        };
        
    } else {
        // Fallback: display the response text
        resultContent.innerHTML = `
            <div class="result-content">
                <p>${data.response}</p>
            </div>
        `;
    }
}

function shareSimulationResult() {
    if (!window.lastSimulationResult) {
        showToast('Paylaşılacak sonuç bulunamadı', 'error');
        return;
    }
    
    const result = window.lastSimulationResult;
    const shareText = `📊 Hisse Senedi Simülasyon Sonucu

${result.data.hisse} - ${result.data['başlangıç tarihi']}
Yatırım: ${(result.data['şu anki değer'] - result.data['net kazanç']).toLocaleString('tr-TR')} TL
Güncel Değer: ${result.data['şu anki değer'].toLocaleString('tr-TR')} TL
Net Kazanç: ${result.data['net kazanç'].toLocaleString('tr-TR')} TL (%${result.data['getiri %'].toFixed(2)})

Fintra Hisse Senedi Asistanı ile hesaplandı`;

    // Try to use Web Share API
    if (navigator.share) {
        navigator.share({
            title: 'Hisse Senedi Simülasyon Sonucu',
            text: shareText,
            url: window.location.href
        }).catch(err => {
            console.log('Share failed:', err);
            copyToClipboard(shareText);
        });
    } else {
        copyToClipboard(shareText);
    }
}

function downloadSimulationResult() {
    if (!window.lastSimulationResult) {
        showToast('İndirilecek sonuç bulunamadı', 'error');
        return;
    }
    
    const result = window.lastSimulationResult;
    const content = `Hisse Senedi Simülasyon Raporu
=====================================

Tarih: ${new Date(result.timestamp).toLocaleString('tr-TR')}
Hisse: ${result.data.hisse}
Başlangıç Tarihi: ${result.data['başlangıç tarihi']}

YATIRIM DETAYLARI:
- Yatırım Tutarı: ${(result.data['şu anki değer'] - result.data['net kazanç']).toLocaleString('tr-TR')} TL
- Başlangıç Fiyatı: ${result.data['başlangıç fiyatı']} TL
- Alınan Lot: ${result.data['alınan lot']} adet

GÜNCEL DURUM:
- Güncel Fiyat: ${result.data['güncel fiyat']} TL
- Şu Anki Değer: ${result.data['şu anki değer'].toLocaleString('tr-TR')} TL
- Net Kazanç: ${result.data['net kazanç'].toLocaleString('tr-TR')} TL
- Getiri Oranı: %${result.data['getiri %'].toFixed(2)}

${result.data['net kazanç'] > 0 ? '✅ KARLILIK' : result.data['net kazanç'] < 0 ? '❌ ZARAR' : '⚪ BREAKEVEN'}

Not: Bu simülasyon geçmiş verilere dayalıdır. Gelecekteki performans garantisi vermez.
Fintra Hisse Senedi Asistanı ile oluşturulmuştur.`;

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `simulasyon_${result.data.hisse.replace('.IS', '')}_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('Simülasyon sonucu indirildi', 'success');
}

function runNewSimulation() {
    resetSimulationForm();
    const resultSection = document.getElementById('simulationResult');
    resultSection.style.display = 'none';
    
    // Focus on stock input
    document.getElementById('simulationStock').focus();
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const simulationModal = document.getElementById('simulationModal');
    if (event.target === simulationModal) {
        closeSimulationModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeSimulationModal();
    }
});

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    initSpeechRecognition();
    initChatHistory();
    showWelcomeMessage();
    
    // Event listeners
    document.getElementById('messageInput').addEventListener('keypress', handleKeyPress);
    
    // Tema değişikliği dinleyicisi
    watchSystemTheme();
}); 

// Portfolio Management Functions
function openPortfolioModal() {
    const portfolioModal = document.getElementById('portfolioModal');
    portfolioModal.classList.add('show');
    loadPortfolioData();
}

function closePortfolioModal() {
    const portfolioModal = document.getElementById('portfolioModal');
    portfolioModal.classList.remove('show');
}

async function loadPortfolioData() {
    try {
        const response = await fetch('/api/portfolio?user_id=default_user');
        const data = await response.json();
        
        if (data.success) {
            updatePortfolioSummary(data.data);
            updatePortfolioTable(data.data);
            createPortfolioChart(data.data);
        } else {
            showToast('Portföy yüklenirken hata oluştu', 'error');
        }
    } catch (error) {
        console.error('Portföy yükleme hatası:', error);
        showToast('Portföy yüklenirken hata oluştu', 'error');
    }
}

function updatePortfolioSummary(data) {
    const portfolioValue = data.portfolio_value;
    
    document.getElementById('totalInvested').textContent = `${portfolioValue.total_invested.toLocaleString('tr-TR')} TL`;
    document.getElementById('currentValue').textContent = `${portfolioValue.current_value.toLocaleString('tr-TR')} TL`;
    
    const pnlElement = document.getElementById('totalPnl');
    const pnlPercentElement = document.getElementById('totalPnlPercent');
    
    pnlElement.textContent = `${portfolioValue.total_pnl.toLocaleString('tr-TR')} TL`;
    pnlPercentElement.textContent = `%${portfolioValue.total_pnl_percent.toFixed(2)}`;
    
    // Kar/zarar rengini ayarla
    if (portfolioValue.total_pnl > 0) {
        pnlElement.style.color = 'var(--success-color)';
        pnlPercentElement.style.color = 'var(--success-color)';
    } else if (portfolioValue.total_pnl < 0) {
        pnlElement.style.color = 'var(--error-color)';
        pnlPercentElement.style.color = 'var(--error-color)';
    } else {
        pnlElement.style.color = 'var(--text-primary)';
        pnlPercentElement.style.color = 'var(--text-primary)';
    }
}

function updatePortfolioTable(data) {
    const portfolioTable = document.getElementById('portfolioTable');
    const portfolioValue = data.portfolio_value;
    
    if (portfolioValue.stocks.length === 0) {
        portfolioTable.innerHTML = `
            <div style="padding: 40px; text-align: center; color: var(--text-muted);">
                <i class="fas fa-briefcase" style="font-size: 48px; margin-bottom: 16px;"></i>
                <p>Portföyünüzde henüz hisse senedi bulunmuyor</p>
                <p>Yeni hisse eklemek için "Hisse Ekle" butonuna tıklayın</p>
            </div>
        `;
        return;
    }
    
    let tableHTML = `
        <table>
            <thead>
                <tr>
                    <th>Hisse</th>
                    <th>Miktar</th>
                    <th>Ort. Alış</th>
                    <th>Güncel</th>
                    <th>Yatırım</th>
                    <th>Değer</th>
                    <th>Kar/Zarar</th>
                    <th>İşlemler</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    portfolioValue.stocks.forEach(stock => {
        const pnlClass = stock.pnl >= 0 ? 'positive' : 'negative';
        const pnlSign = stock.pnl >= 0 ? '+' : '';
        
        tableHTML += `
            <tr>
                <td class="stock-symbol">${stock.symbol}</td>
                <td>${stock.quantity.toLocaleString('tr-TR')}</td>
                <td>${stock.avg_price.toFixed(2)} TL</td>
                <td>${stock.current_price.toFixed(2)} TL</td>
                <td>${stock.invested.toLocaleString('tr-TR')} TL</td>
                <td>${stock.current_value.toLocaleString('tr-TR')} TL</td>
                <td class="stock-pnl ${pnlClass}">
                    ${pnlSign}${stock.pnl.toFixed(2)} TL
                    <br>
                    <small>(${pnlSign}%${stock.pnl_percent.toFixed(2)})</small>
                </td>
                <td class="stock-actions">
                    <button class="stock-action-btn" onclick="editStock('${stock.symbol}')" title="Düzenle">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="stock-action-btn danger" onclick="removeStock('${stock.symbol}')" title="Çıkar">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tableHTML += `
            </tbody>
        </table>
    `;
    
    portfolioTable.innerHTML = tableHTML;
}

function createPortfolioChart(data) {
    const portfolioValue = data.portfolio_value;
    
    if (!portfolioValue || !portfolioValue.stocks || portfolioValue.stocks.length === 0) {
        document.getElementById('portfolioChart').innerHTML = `
            <div style="padding: 40px; text-align: center; color: var(--text-muted);">
                <i class="fas fa-chart-pie" style="font-size: 48px; margin-bottom: 16px;"></i>
                <p>Portföy grafiği için hisse senedi gerekli</p>
            </div>
        `;
        return;
    }
    
    // Grafik verilerini hazırla
    const stocks = portfolioValue.stocks;
    const chartData = [{
        values: stocks.map(stock => stock.current_value),
        labels: stocks.map(stock => stock.symbol),
        type: 'pie',
        textinfo: 'label+percent+value',
        textposition: 'outside',
        hovertemplate: '<b>%{label}</b><br>' +
                      'Değer: %{value:,.2f} TL<br>' +
                      'Yüzde: %{percent}<extra></extra>',
        marker: {
            colors: getChartColors(stocks.length),
            line: {
                color: '#ecf0f1',
                width: 2
            }
        },
        textfont: {
            size: 14,
            color: '#2c3e50'
        }
    }];
    
    const layout = {
        title: {
            text: 'Portföy Dağılımı',
            font: {
                size: 20,
                color: '#2c3e50',
                family: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif'
            }
        },
        font: {
            family: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
            size: 13,
            color: '#34495e'
        },
        margin: {
            t: 80,
            b: 50,
            l: 50,
            r: 50
        },
        showlegend: true,
        legend: {
            orientation: 'v',
            x: 1.05,
            y: 0.5,
            font: {
                size: 13,
                color: '#34495e'
            },
            bgcolor: 'rgba(255,255,255,0.95)',
            bordercolor: '#bdc3c7',
            borderwidth: 1,
            bordercornerradius: 8
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        hovermode: 'closest'
    };
    
    const config = {
        responsive: true,
        displayModeBar: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    };
    
    Plotly.newPlot('portfolioChart', chartData, layout, config);
}

function getChartColors(count) {
    const colors = [
        '#3498db', // Mavi (ana tema rengi)
        '#e74c3c', // Kırmızı
        '#2ecc71', // Yeşil
        '#f39c12', // Turuncu
        '#9b59b6', // Mor
        '#1abc9c', // Turkuaz
        '#e67e22', // Koyu turuncu
        '#34495e', // Koyu gri-mavi
        '#16a085', // Koyu turkuaz
        '#8e44ad', // Koyu mor
        '#27ae60', // Koyu yeşil
        '#d35400', // Çok koyu turuncu
        '#2980b9', // Koyu mavi
        '#c0392b', // Koyu kırmızı
        '#7f8c8d', // Gri
        '#f1c40f', // Sarı
        '#e91e63', // Pembe
        '#00bcd4', // Açık mavi
        '#4caf50', // Material yeşil
        '#ff9800'  // Material turuncu
    ];
    
    return colors.slice(0, count);
}

function showAddStockForm() {
    document.getElementById('addStockForm').style.display = 'block';
    document.getElementById('stockSymbol').focus();
}

function hideAddStockForm() {
    document.getElementById('addStockForm').style.display = 'none';
    document.getElementById('stockSymbol').value = '';
    document.getElementById('stockQuantity').value = '';
    document.getElementById('stockPrice').value = '';
}

async function addStockToPortfolio() {
    const symbol = document.getElementById('stockSymbol').value.trim().toUpperCase();
    const quantity = parseFloat(document.getElementById('stockQuantity').value);
    const price = parseFloat(document.getElementById('stockPrice').value);
    
    if (!symbol || !quantity || !price) {
        showToast('Lütfen tüm alanları doldurun', 'error');
        return;
    }
    
    if (quantity <= 0 || price <= 0) {
        showToast('Miktar ve fiyat pozitif olmalı', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/portfolio/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: 'default_user',
                symbol: symbol,
                quantity: quantity,
                avg_price: price
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            hideAddStockForm();
            loadPortfolioData(); // Portföyü yenile
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        console.error('Hisse ekleme hatası:', error);
        showToast('Hisse eklenirken hata oluştu', 'error');
    }
}

async function removeStock(symbol) {
    if (!confirm(`${symbol} hissesini portföyden çıkarmak istediğinizden emin misiniz?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/portfolio/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: 'default_user',
                symbol: symbol
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(data.message, 'success');
            loadPortfolioData(); // Portföyü yenile
        } else {
            showToast(data.message, 'error');
        }
    } catch (error) {
        console.error('Hisse çıkarma hatası:', error);
        showToast('Hisse çıkarılırken hata oluştu', 'error');
    }
}

function editStock(symbol) {
    // Basit düzenleme - yeni miktar ve fiyat gir
    const newQuantity = prompt(`${symbol} için yeni miktar:`, '');
    const newPrice = prompt(`${symbol} için yeni ortalama fiyat:`, '');
    
    if (newQuantity && newPrice) {
        const quantity = parseFloat(newQuantity);
        const price = parseFloat(newPrice);
        
        if (quantity > 0 && price > 0) {
            // Önce mevcut hisseyi çıkar, sonra yenisini ekle
            removeStock(symbol).then(() => {
                setTimeout(() => {
                    // Form alanlarını doldur ve ekle
                    document.getElementById('stockSymbol').value = symbol;
                    document.getElementById('stockQuantity').value = quantity;
                    document.getElementById('stockPrice').value = price;
                    addStockToPortfolio();
                }, 500);
            });
        } else {
            showToast('Geçersiz değerler', 'error');
        }
    }
}

// Portföy yenileme fonksiyonu
function refreshPortfolio() {
    if (document.getElementById('portfolioModal').classList.contains('show')) {
        loadPortfolioData();
    }
}

// Sayfa yüklendiğinde portföy butonunu aktif et
document.addEventListener('DOMContentLoaded', function() {
    // Mevcut event listener'lar...
    
    // Portföy yenileme için otomatik yenileme (5 dakikada bir)
    setInterval(refreshPortfolio, 5 * 60 * 1000);
}); 

// Finansal Takvim Fonksiyonları
function openCalendarModal() {
    const calendarModal = document.getElementById('calendarModal');
    calendarModal.classList.add('show');
    loadCalendarData();
}

function closeCalendarModal() {
    const calendarModal = document.getElementById('calendarModal');
    calendarModal.classList.remove('show');
}

function switchCalendarTab(tabName) {
    // Tüm tab butonlarını pasif yap
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => btn.classList.remove('active'));
    
    // Tüm tab içeriklerini gizle
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Seçilen tab'ı aktif yap
    const activeTabBtn = document.querySelector(`[onclick="switchCalendarTab('${tabName}')"]`);
    if (activeTabBtn) {
        activeTabBtn.classList.add('active');
    }
    
    const activeTabContent = document.getElementById(`${tabName}Tab`);
    if (activeTabContent) {
        activeTabContent.classList.add('active');
    }
    
    // Tab'a özel veri yükle
    switch(tabName) {
        case 'overview':
            loadCalendarOverview();
            break;
        case 'company':
            loadCompanyList();
            break;
        case 'upcoming':
            loadUpcomingEvents();
            break;
        case 'add':
            resetEventForm();
            break;
    }
}

async function loadCalendarData() {
    try {
        const response = await fetch('/api/calendar');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Genel bakış tab'ını yükle
                loadCalendarOverview();
                // Şirket listesini yükle
                loadCompanyList();
            }
        }
    } catch (error) {
        console.error('Takvim verisi yükleme hatası:', error);
        showToast('Takvim verisi yüklenirken hata oluştu', 'error');
    }
}

async function loadCalendarOverview() {
    try {
        const response = await fetch('/api/calendar');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                updateCompanyStats(data.data);
                updateCalendarTable(data.data);
            }
        }
    } catch (error) {
        console.error('Genel bakış yükleme hatası:', error);
    }
}

function updateCompanyStats(calendarData) {
    const companyStats = document.getElementById('companyStats');
    if (!companyStats) return;
    
    const companies = Object.keys(calendarData);
    const totalEvents = companies.reduce((total, company) => {
        return total + calendarData[company].events.length;
    }, 0);
    
    const completedEvents = companies.reduce((total, company) => {
        return total + calendarData[company].events.filter(event => event.status === 'tamamlandı').length;
    }, 0);
    
    const pendingEvents = totalEvents - completedEvents;
    
    companyStats.innerHTML = `
        <div class="company-stat-card">
            <h5>Toplam Şirket</h5>
            <div class="stat-value">${companies.length}</div>
        </div>
        <div class="company-stat-card">
            <h5>Toplam Olay</h5>
            <div class="stat-value">${totalEvents}</div>
        </div>
        <div class="company-stat-card">
            <h5>Tamamlanan</h5>
            <div class="stat-value">${completedEvents}</div>
        </div>
        <div class="company-stat-card">
            <h5>Bekleyen</h5>
            <div class="stat-value">${pendingEvents}</div>
        </div>
    `;
}

function updateCalendarTable(calendarData) {
    const calendarTable = document.getElementById('calendarTable');
    if (!calendarTable) return;
    
    let tableHTML = `
        <table>
            <thead>
                <tr>
                    <th>Şirket</th>
                    <th>Olay Türü</th>
                    <th>Tarih</th>
                    <th>Açıklama</th>
                    <th>Durum</th>
                    <th>Kaynak</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    const companies = Object.keys(calendarData);
    companies.forEach(company => {
        const companyData = calendarData[company];
        companyData.events.forEach(event => {
            const statusClass = event.status === 'tamamlandı' ? 'completed' : 'pending';
            const statusText = event.status === 'tamamlandı' ? 'Tamamlandı' : 'Bekliyor';
            
            tableHTML += `
                <tr>
                    <td><strong>${companyData.company_name} (${company})</strong></td>
                    <td>${event.type.charAt(0).toUpperCase() + event.type.slice(1)}</td>
                    <td>${formatDate(event.date)}</td>
                    <td>${event.description}</td>
                    <td><span class="event-status ${statusClass}">${statusText}</span></td>
                    <td>${event.source}</td>
                </tr>
            `;
        });
    });
    
    tableHTML += '</tbody></table>';
    calendarTable.innerHTML = tableHTML;
}

async function loadCompanyList() {
    try {
        const response = await fetch('/api/calendar');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                const companySelect = document.getElementById('companySelect');
                const updateCompanyBtn = document.getElementById('updateCompanyBtn');
                
                // Mevcut seçimi sakla
                const currentSelection = companySelect.value;
                
                // Şirket listesini güncelle
                    companySelect.innerHTML = '<option value="">Şirket seçin...</option>';
                    
                Object.keys(data.data).forEach(symbol => {
                        const option = document.createElement('option');
                    option.value = symbol;
                    option.textContent = `${symbol} - ${data.data[symbol].company_name}`;
                        companySelect.appendChild(option);
                    });
                
                // Önceki seçimi geri yükle
                if (currentSelection && data.data[currentSelection]) {
                    companySelect.value = currentSelection;
                    loadCompanyCalendar();
                }
                
                // Güncelleme butonunu göster
                if (updateCompanyBtn) {
                    updateCompanyBtn.style.display = 'inline-block';
                }
            }
        }
    } catch (error) {
        console.error('Şirket listesi yükleme hatası:', error);
    }
}

async function updateSelectedCompany() {
    const companySelect = document.getElementById('companySelect');
    const selectedSymbol = companySelect.value;
    
    if (!selectedSymbol) {
        showToast('Lütfen bir şirket seçin', 'warning');
        return;
    }
    
    await updateCompanyCalendar(selectedSymbol);
}

async function loadCompanyCalendar() {
    const companySelect = document.getElementById('companySelect');
    const companyEvents = document.getElementById('companyEvents');
    
    if (!companySelect || !companyEvents || !companySelect.value) {
        return;
    }
    
    try {
        const response = await fetch(`/api/calendar/company/${companySelect.value}`);
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                displayCompanyEvents(data.data);
            }
        }
    } catch (error) {
        console.error('Şirket takvimi yükleme hatası:', error);
        showToast('Şirket takvimi yüklenirken hata oluştu', 'error');
    }
}

function displayCompanyEvents(companyData) {
    const companyEvents = document.getElementById('companyEvents');
    if (!companyEvents) return;
    
    let eventsHTML = `
        <h4><i class="fas fa-building"></i> ${companyData.company_name} Finansal Olayları</h4>
    `;
    
    if (companyData.events.length === 0) {
        eventsHTML += '<p>Bu şirket için henüz finansal olay bulunmamaktadır.</p>';
    } else {
        companyData.events.forEach(event => {
            const statusIcon = event.status === 'tamamlandı' ? '✅' : '⏳';
            eventsHTML += `
                <div class="event-item">
                    <div class="event-header">
                        <span class="event-type">${statusIcon} ${event.type.charAt(0).toUpperCase() + event.type.slice(1)}</span>
                        <span class="event-date">${formatDate(event.date)}</span>
                    </div>
                    <div class="event-description">${event.description}</div>
                    <div class="event-meta">
                        <span><i class="fas fa-link"></i> ${event.source}</span>
                        <span><i class="fas fa-info-circle"></i> ${event.status === 'tamamlandı' ? 'Tamamlandı' : 'Bekliyor'}</span>
                    </div>
                </div>
            `;
        });
    }
    
    companyEvents.innerHTML = eventsHTML;
}

async function loadUpcomingEvents() {
    const upcomingDays = document.getElementById('upcomingDays');
    const days = upcomingDays ? upcomingDays.value : 30;
    
    try {
        const response = await fetch(`/api/calendar/upcoming?days=${days}`);
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                displayUpcomingEvents(data.data);
            }
        }
    } catch (error) {
        console.error('Yaklaşan olaylar yükleme hatası:', error);
        showToast('Yaklaşan olaylar yüklenirken hata oluştu', 'error');
    }
}

function displayUpcomingEvents(events) {
    const upcomingEvents = document.getElementById('upcomingEvents');
    if (!upcomingEvents) return;
    
    let eventsHTML = `
        <h4><i class="fas fa-clock"></i> Yaklaşan Finansal Olaylar</h4>
    `;
    
    if (events.length === 0) {
        eventsHTML += '<p>Önümüzdeki günlerde finansal olay bulunmamaktadır.</p>';
    } else {
        events.forEach(event => {
            const daysUntil = Math.ceil((new Date(event.date) - new Date()) / (1000 * 60 * 60 * 24));
            const daysText = daysUntil === 0 ? 'Bugün' : daysUntil === 1 ? 'Yarın' : `${daysUntil} gün sonra`;
            
            eventsHTML += `
                <div class="event-item">
                    <div class="event-header">
                        <span class="event-type">${event.type.charAt(0).toUpperCase() + event.type.slice(1)}</span>
                        <span class="event-date">${formatDate(event.date)} (${daysText})</span>
                    </div>
                    <div class="event-description">${event.description}</div>
                    <div class="event-meta">
                        <span><i class="fas fa-building"></i> ${event.company_name} (${event.symbol})</span>
                        <span><i class="fas fa-link"></i> ${event.source}</span>
                    </div>
                </div>
            `;
        });
    }
    
    upcomingEvents.innerHTML = eventsHTML;
}

async function addCalendarEvent() {
    const symbol = document.getElementById('eventSymbol').value.trim();
    const eventType = document.getElementById('eventType').value;
    const eventDate = document.getElementById('eventDate').value;
    const description = document.getElementById('eventDescription').value.trim();
    const source = document.getElementById('eventSource').value.trim();
    const status = document.getElementById('eventStatus').value;
    
    if (!symbol || !eventType || !eventDate || !description) {
        showToast('Lütfen tüm gerekli alanları doldurun', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/calendar/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbol: symbol.toUpperCase(),
                type: eventType,
                date: eventDate,
                description: description,
                source: source || 'KAP',
                status: status
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                showToast('Olay başarıyla eklendi', 'success');
                resetEventForm();
                // Takvimi yenile
                loadCalendarData();
            } else {
                showToast(data.message || 'Olay eklenirken hata oluştu', 'error');
            }
        } else {
            const errorData = await response.json();
            showToast(errorData.message || 'Olay eklenirken hata oluştu', 'error');
        }
    } catch (error) {
        console.error('Olay ekleme hatası:', error);
        showToast('Olay eklenirken hata oluştu', 'error');
    }
}

function resetEventForm() {
    document.getElementById('eventSymbol').value = '';
    document.getElementById('eventType').value = 'bilanço';
    document.getElementById('eventDate').value = '';
    document.getElementById('eventDescription').value = '';
    document.getElementById('eventSource').value = 'KAP';
    document.getElementById('eventStatus').value = 'bekliyor';
}

async function importCalendarCSV() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv';
    input.onchange = async (event) => {
        const file = event.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/calendar/import', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    showToast('CSV dosyası başarıyla yüklendi', 'success');
                    loadCalendarData();
                } else {
                    showToast(data.message || 'CSV yükleme hatası', 'error');
                }
            } else {
                const errorData = await response.json();
                showToast(errorData.message || 'CSV yükleme hatası', 'error');
            }
        } catch (error) {
            console.error('CSV yükleme hatası:', error);
            showToast('CSV yüklenirken hata oluştu', 'error');
        }
    };
    
    input.click();
}

async function exportCalendarCSV() {
    try {
        const response = await fetch('/api/calendar/export');
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'financial_calendar.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showToast('CSV dosyası başarıyla indirildi', 'success');
        } else {
            const errorData = await response.json();
            showToast(errorData.message || 'CSV indirme hatası', 'error');
        }
    } catch (error) {
        console.error('CSV indirme hatası:', error);
        showToast('CSV indirilirken hata oluştu', 'error');
    }
}

async function refreshCalendar() {
    try {
    showToast('Takvim yenileniyor...', 'info');
    await loadCalendarData();
        showToast('Takvim yenilendi', 'success');
    } catch (error) {
        console.error('Takvim yenileme hatası:', error);
        showToast('Takvim yenilenirken hata oluştu', 'error');
    }
}

async function updateCompanyCalendar(symbol) {
    try {
        showToast(`${symbol} için veri güncelleniyor...`, 'info');
        
        const response = await fetch(`/api/calendar/update/${symbol}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                showToast(`${symbol} güncellendi`, 'success');
                // Şirket verilerini yenile
                if (symbol === document.getElementById('companySelect').value) {
                    loadCompanyCalendar();
                }
                // Genel bakışı yenile
                loadCalendarOverview();
            } else {
                showToast(data.message || 'Güncelleme başarısız', 'error');
            }
        } else {
            showToast('Güncelleme hatası', 'error');
        }
    } catch (error) {
        console.error('Güncelleme hatası:', error);
        showToast('Güncelleme sırasında hata oluştu', 'error');
    }
}

async function updateAllCompanies() {
    try {
        showToast('Tüm şirketler güncelleniyor...', 'info');
        
        const response = await fetch('/api/calendar/update-all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                symbols: ['THYAO', 'KCHOL', 'GARAN', 'AKBNK', 'ISCTR', 'SAHOL', 'ASELS', 'EREGL'],
                force: true
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                showToast(data.message, 'success');
                // Tüm verileri yenile
                loadCalendarData();
            } else {
                showToast(data.message || 'Toplu güncelleme başarısız', 'error');
            }
        } else {
            showToast('Toplu güncelleme hatası', 'error');
        }
    } catch (error) {
        console.error('Toplu güncelleme hatası:', error);
        showToast('Toplu güncelleme sırasında hata oluştu', 'error');
    }
}

async function searchCalendarEvents(query) {
    try {
        if (!query || query.trim() === '') {
            showToast('Arama terimi gerekli', 'warning');
            return;
        }
        
        const response = await fetch(`/api/calendar/search/${encodeURIComponent(query.trim())}`);
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                displaySearchResults(data.data, query);
            } else {
                showToast(data.message || 'Arama başarısız', 'error');
            }
        } else {
            showToast('Arama hatası', 'error');
        }
    } catch (error) {
        console.error('Arama hatası:', error);
        showToast('Arama sırasında hata oluştu', 'error');
    }
}

function displaySearchResults(results, query) {
    const searchResultsContainer = document.getElementById('searchResults');
    if (!searchResultsContainer) return;
    
    if (results.length === 0) {
        searchResultsContainer.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <p>"${query}" için sonuç bulunamadı</p>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="search-results-header">
            <h4>"${query}" için ${results.length} sonuç bulundu</h4>
        </div>
        <div class="search-results-list">
    `;
    
    results.forEach(event => {
        const eventDate = new Date(event.date);
        const isUpcoming = eventDate > new Date();
        const statusClass = isUpcoming ? 'upcoming' : 'completed';
        
        html += `
            <div class="search-result-item ${statusClass}">
                <div class="result-header">
                    <span class="company-symbol">${event.symbol}</span>
                    <span class="event-type">${event.type}</span>
                    <span class="event-date">${formatDate(event.date)}</span>
                </div>
                <div class="result-description">${event.description}</div>
                <div class="result-meta">
                    <span class="source">${event.source}</span>
                    <span class="status ${statusClass}">${event.status}</span>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    searchResultsContainer.innerHTML = html;
}

async function getCalendarSummary() {
    try {
        const response = await fetch('/api/calendar/summary');
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                updateCalendarSummary(data.data);
            }
        }
    } catch (error) {
        console.error('Özet getirme hatası:', error);
    }
}

function updateCalendarSummary(summary) {
    const summaryContainer = document.getElementById('calendarSummary');
    if (!summaryContainer) return;
    
    summaryContainer.innerHTML = `
        <div class="summary-grid">
            <div class="summary-item">
                <div class="summary-icon">
                    <i class="fas fa-building"></i>
                </div>
                <div class="summary-content">
                    <div class="summary-value">${summary.total_companies}</div>
                    <div class="summary-label">Toplam Şirket</div>
                </div>
            </div>
            <div class="summary-item">
                <div class="summary-icon">
                    <i class="fas fa-calendar-check"></i>
                </div>
                <div class="summary-content">
                    <div class="summary-value">${summary.total_events}</div>
                    <div class="summary-label">Toplam Olay</div>
                </div>
            </div>
            <div class="summary-item">
                <div class="summary-icon">
                    <i class="fas fa-clock"></i>
                </div>
                <div class="summary-content">
                    <div class="summary-value">${summary.upcoming_events}</div>
                    <div class="summary-label">Yaklaşan (30 gün)</div>
                </div>
            </div>
            <div class="summary-item">
                <div class="summary-icon">
                    <i class="fas fa-sync-alt"></i>
                </div>
                <div class="summary-content">
                    <div class="summary-value">${summary.last_updated}</div>
                    <div class="summary-label">Son Güncelleme</div>
                </div>
            </div>
        </div>
    `;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Alarmlar Modal Functions
function openAlertsModal() {
    const alertsModal = document.getElementById('alertsModal');
    alertsModal.classList.add('show');
    loadAlertsData();
}

function closeAlertsModal() {
    const alertsModal = document.getElementById('alertsModal');
    alertsModal.classList.remove('show');
}

function switchAlertsTab(tabName) {
    // Tüm tab butonlarından active class'ını kaldır
    const tabBtns = document.querySelectorAll('.alerts-tabs .tab-btn');
    tabBtns.forEach(btn => btn.classList.remove('active'));
    
    // Tüm tab içeriklerini gizle
    const tabContents = document.querySelectorAll('.alerts-content .tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Seçilen tab'ı aktif yap
    const selectedBtn = document.querySelector(`[onclick="switchAlertsTab('${tabName}')"]`);
    if (selectedBtn) selectedBtn.classList.add('active');
    
    const selectedContent = document.getElementById(`${tabName}AlertsTab`);
    if (selectedContent) selectedContent.classList.add('active');
    
    // Seçilen tab'a göre veri yükle
    if (tabName === 'active') {
        loadActiveAlerts();
    } else if (tabName === 'triggered') {
        loadTriggeredAlerts();
    } else if (tabName === 'cancelled') {
        loadCancelledAlerts();
    }
}

async function loadAlertsData() {
    try {
        // Önce özet bilgileri yükle
        await loadAlertsSummary();
        
        // Aktif alarmları yükle
        await loadActiveAlerts();
        
        // Diğer tab'ları da yükle
        await loadTriggeredAlerts();
        await loadCancelledAlerts();
        
    } catch (error) {
        console.error('Alarm verileri yüklenirken hata:', error);
        showToast('Alarm verileri yüklenirken hata oluştu', 'error');
    }
}

async function loadAlertsSummary() {
    try {
        const sessionId = getCurrentSessionId();
        const response = await fetch(`/api/alerts/summary?session_id=${sessionId}`);
        const data = await response.json();
        
        if (data.success) {
            updateAlertsSummary(data.data);
        }
    } catch (error) {
        console.error('Alarm özeti yüklenirken hata:', error);
    }
}

function updateAlertsSummary(summary) {
    const activeCount = document.getElementById('activeAlertsCount');
    const nextAlertDate = document.getElementById('nextAlertDate');
    
    if (activeCount) {
        activeCount.textContent = summary.active_count || 0;
    }
    
    if (nextAlertDate) {
        if (summary.next_alert) {
            nextAlertDate.textContent = formatDate(summary.next_alert.alert_date);
        } else {
            nextAlertDate.textContent = '-';
        }
    }
}

async function loadActiveAlerts() {
    try {
        const sessionId = getCurrentSessionId();
        const response = await fetch(`/api/alerts?session_id=${sessionId}&status=active`);
        const data = await response.json();
        
        if (data.success) {
            displayAlerts(data.data.active || [], 'activeAlertsList');
        }
    } catch (error) {
        console.error('Aktif alarmlar yüklenirken hata:', error);
    }
}

async function loadTriggeredAlerts() {
    try {
        const sessionId = getCurrentSessionId();
        const response = await fetch(`/api/alerts?session_id=${sessionId}&status=triggered`);
        const data = await response.json();
        
        if (data.success) {
            displayAlerts(data.data.triggered || [], 'triggeredAlertsList');
        }
    } catch (error) {
        console.error('Tetiklenen alarmlar yüklenirken hata:', error);
    }
}

async function loadCancelledAlerts() {
    try {
        const sessionId = getCurrentSessionId();
        const response = await fetch(`/api/alerts?session_id=${sessionId}&status=cancelled`);
        const data = await response.json();
        
        if (data.success) {
            displayAlerts(data.data.cancelled || [], 'cancelledAlertsList');
        }
    } catch (error) {
        console.error('İptal edilen alarmlar yüklenirken hata:', error);
    }
}

function displayAlerts(alerts, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="no-alerts">
                <i class="fas fa-bell-slash"></i>
                <p>Alarm bulunamadı</p>
                <span>Bu kategoride henüz alarm yok</span>
            </div>
        `;
        return;
    }
    
    container.innerHTML = alerts.map(alert => createAlertHTML(alert)).join('');
}

function createAlertHTML(alert) {
    const alertDate = formatDate(alert.alert_date);
    const eventDate = formatDate(alert.event_date);
    const createdDate = formatDate(alert.created_at);
    
    let statusBadge = '';
    if (alert.status === 'active') {
        statusBadge = '<span class="alert-status active">Aktif</span>';
    } else if (alert.status === 'triggered') {
        statusBadge = '<span class="alert-status triggered">Tetiklendi</span>';
    } else if (alert.status === 'cancelled') {
        statusBadge = '<span class="alert-status cancelled">İptal Edildi</span>';
    }
    
    let actionButtons = '';
    if (alert.status === 'active') {
        actionButtons = `
            <button class="alert-action-btn cancel" onclick="cancelAlert(${alert.id})">
                <i class="fas fa-ban"></i>
                İptal Et
            </button>
            <button class="alert-action-btn delete" onclick="deleteAlert(${alert.id})">
                <i class="fas fa-trash"></i>
                Sil
            </button>
        `;
    }
    
    return `
        <div class="alert-item">
            <div class="alert-header">
                <div class="alert-info">
                    <span class="alert-symbol">${alert.symbol}</span>
                    <span class="alert-type">${alert.event_type}</span>
                    ${statusBadge}
                </div>
            </div>
            
            <div class="alert-dates">
                <div class="alert-date-item">
                    <i class="fas fa-bell"></i>
                    <span class="alert-date-label">Alarm Tarihi:</span>
                    <span class="alert-date-value">${alertDate}</span>
                </div>
                <div class="alert-date-item">
                    <span class="alert-date-label">Olay Tarihi:</span>
                    <span class="alert-date-value">${eventDate}</span>
                </div>
                <div class="alert-date-item">
                    <i class="fas fa-clock"></i>
                    <span class="alert-date-label">Oluşturulma:</span>
                    <span class="alert-date-value">${createdDate}</span>
                </div>
            </div>
            
            <div class="alert-description">
                ${alert.description}
            </div>
            
            ${actionButtons ? `<div class="alert-actions">${actionButtons}</div>` : ''}
        </div>
    `;
}

async function cancelAlert(alertId) {
    if (!confirm('Bu alarmı iptal etmek istediğinizden emin misiniz?')) {
        return;
    }
    
    try {
        const sessionId = getCurrentSessionId();
        const response = await fetch(`/api/alerts/cancel/${alertId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Alarm başarıyla iptal edildi', 'success');
            loadAlertsData(); // Verileri yenile
        } else {
            showToast('Alarm iptal edilirken hata oluştu', 'error');
        }
    } catch (error) {
        console.error('Alarm iptal edilirken hata:', error);
        showToast('Alarm iptal edilirken hata oluştu', 'error');
    }
}

async function deleteAlert(alertId) {
    if (!confirm('Bu alarmı silmek istediğinizden emin misiniz? Bu işlem geri alınamaz.')) {
        return;
    }
    
    try {
        const sessionId = getCurrentSessionId();
        const response = await fetch(`/api/alerts/delete/${alertId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ session_id: sessionId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Alarm başarıyla silindi', 'success');
            loadAlertsData(); // Verileri yenile
        } else {
            showToast('Alarm silinirken hata oluştu', 'error');
            }
    } catch (error) {
        console.error('Alarm silinirken hata:', error);
        showToast('Alarm silinirken hata oluştu', 'error');
    }
}

function refreshAlerts() {
    loadAlertsData();
    showToast('Alarmlar yenilendi', 'success');
}

async function exportAlertsCSV() {
    try {
        const sessionId = getCurrentSessionId();
        const response = await fetch(`/api/alerts?session_id=${sessionId}`);
        const data = await response.json();
        
        if (data.success) {
            const allAlerts = [
                ...(data.data.active || []),
                ...(data.data.triggered || []),
                ...(data.cancelled || [])
            ];
            
            if (allAlerts.length === 0) {
                showToast('Dışa aktarılacak alarm bulunamadı', 'warning');
                return;
            }
            
            // CSV formatına çevir
            const csvContent = convertAlertsToCSV(allAlerts);
            
            // CSV dosyasını indir
            downloadCSV(csvContent, 'alarmlar.csv');
            
            showToast('Alarmlar CSV olarak indirildi', 'success');
        }
    } catch (error) {
        console.error('Alarmlar dışa aktarılırken hata:', error);
        showToast('Alarmlar dışa aktarılırken hata oluştu', 'error');
    }
}

function convertAlertsToCSV(alerts) {
    const headers = ['ID', 'Şirket', 'Olay Türü', 'Olay Tarihi', 'Alarm Tarihi', 'Açıklama', 'Durum', 'Oluşturulma Tarihi'];
    
    const rows = alerts.map(alert => [
        alert.id,
        alert.symbol,
        alert.event_type,
        alert.event_date,
        alert.alert_date,
        alert.description,
        alert.status,
        alert.created_at
    ]);
    
    return [headers, ...rows]
        .map(row => row.map(field => `"${field}"`).join(','))
        .join('\n');
}

function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function getCurrentSessionId() {
    // Session ID'yi localStorage'dan al veya yeni oluştur
    let sessionId = localStorage.getItem('currentSessionId');
    if (!sessionId) {
        sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('currentSessionId', sessionId);
    }
    return sessionId;
}