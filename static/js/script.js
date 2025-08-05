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
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: messageText })
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
    let senderName = sender === 'bot' ? 'KCHOL Asistan' : 'Siz';
    
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
    searchModal.classList.add('show');
    document.getElementById('searchInput').focus();
}

// Arama modalını kapat
function closeSearchModal() {
    const searchModal = document.getElementById('searchModal');
    searchModal.classList.remove('show');
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
        const sender = msg.classList.contains('user-message') ? 'Siz' : 'KCHOL Asistan';
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
    }
}

// Arama işlemini gerçekleştir
function performSearch() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const messages = document.querySelectorAll('.message');
    const searchResults = document.getElementById('searchResults');
    
    if (!searchTerm.trim()) {
        searchResults.innerHTML = '<div class="no-results">Arama terimi girin</div>';
        return;
    }
    
    const results = [];
    messages.forEach((msg, index) => {
        const text = msg.querySelector('.message-text').textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            const sender = msg.classList.contains('user-message') ? 'Siz' : 'KCHOL Asistan';
            const time = msg.querySelector('.message-time').textContent;
            results.push({
                sender,
                text: msg.querySelector('.message-text').textContent,
                time,
                index
            });
        }
    });
    
    displaySearchResults(results, searchTerm);
}

// Arama sonuçlarını göster
function displaySearchResults(results, searchTerm) {
    const searchResults = document.getElementById('searchResults');
    
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="no-results">Sonuç bulunamadı</div>';
        return;
    }
    
    let html = '';
    results.forEach(result => {
        const highlightedText = result.text.replace(
            new RegExp(searchTerm, 'gi'),
            match => `<span class="search-highlight">${match}</span>`
        );
        
        html += `
            <div class="search-result-item" onclick="scrollToMessage(${result.index})">
                <div class="search-result-sender">${result.sender}</div>
                <div class="search-result-text">${highlightedText}</div>
                <div class="search-result-time">${result.time}</div>
            </div>
        `;
    });
    
    searchResults.innerHTML = html;
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
                    <span class="sender-name">KCHOL Asistan</span>
                    <span class="message-time">${new Date().toLocaleTimeString('tr-TR', {hour: '2-digit', minute:'2-digit'})}</span>
                </div>
                <div class="message-text">
                    <h3>KCHOL Hisse Senedi Fiyat Tahmini Asistanına Hoş Geldiniz!</h3>
                    <p>Ben yapay zeka destekli bir finans uzmanıyım ve size yardımcı olmak için buradayım.</p>
                    <p>KCHOL hisse senedi fiyat tahmini yapmak için aşağıdaki önerilerden birini seçebilir veya kendi sorunuzu yazabilirsiniz.</p>
                    <p><strong>Yeni Özellik:</strong> Artık KCHOL, finans, yatırım ve ekonomi hakkında her türlü sorunuzu yanıtlayabilirim!</p>
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
    if (confirm('Tüm ayarları varsayılana döndürmek istediğinizden emin misiniz?')) {
        // Varsayılan ayarları yükle
        document.getElementById('autoSave').checked = true;
        document.getElementById('autoScroll').checked = true;
        document.getElementById('showSuggestions').checked = true;
        document.getElementById('voiceRecognition').checked = true;
        document.getElementById('voiceLanguage').value = 'tr-TR';
        document.getElementById('chartQuality').value = '2';
        document.getElementById('chartFormat').value = 'png';
        
        // Ayarları kaydet ve uygula
        saveSettings();
        showToast('Ayarlar sıfırlandı', 'success');
    }
} 