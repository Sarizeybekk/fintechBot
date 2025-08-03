// Global değişkenler
let isLoading = false;
let isRecording = false;
let recognition = null;
let currentSessionId = null;
let chatMessages = []; // Sohbet mesajlarını saklamak için

// Web Speech API desteğini kontrol et
function checkSpeechSupport() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.warn('Web Speech API desteklenmiyor');
        return false;
    }
    return true;
}

// Speech Recognition başlat
function initSpeechRecognition() {
    if (!checkSpeechSupport()) {
        showToast('Tarayıcınız ses kaydını desteklemiyor', 'error');
        return null;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'tr-TR';
    recognition.maxAlternatives = 1;
    
    recognition.onstart = function() {
        console.log('Ses kaydı başladı');
        isRecording = true;
        updateVoiceUI(true);
    };
    
    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript;
        console.log('Tanınan metin:', transcript);
        
        // Input alanına yaz
        document.getElementById('messageInput').value = transcript;
        
        // Otomatik olarak mesajı gönder
        sendMessage(transcript);
    };
    
    recognition.onerror = function(event) {
        console.error('Ses tanıma hatası:', event.error);
        let errorMessage = 'Ses tanıma hatası';
        
        switch(event.error) {
            case 'no-speech':
                errorMessage = 'Ses algılanamadı. Lütfen tekrar deneyin.';
                break;
            case 'audio-capture':
                errorMessage = 'Mikrofon erişimi sağlanamadı.';
                break;
            case 'not-allowed':
                errorMessage = 'Mikrofon izni verilmedi.';
                break;
            case 'network':
                errorMessage = 'Ağ hatası oluştu.';
                break;
            default:
                errorMessage = 'Bilinmeyen hata oluştu.';
        }
        
        showToast(errorMessage, 'error');
        updateVoiceUI(false);
    };
    
    recognition.onend = function() {
        console.log('Ses kaydı bitti');
        isRecording = false;
        updateVoiceUI(false);
    };
    
    return recognition;
}

// Ses kayıt UI'ını güncelle
function updateVoiceUI(recording) {
    const voiceBtn = document.getElementById('voiceBtn');
    const voiceStatus = document.getElementById('voiceStatus');
    const voiceIndicator = voiceStatus.querySelector('.voice-indicator');
    
    if (recording) {
        voiceBtn.classList.add('recording');
        voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
        voiceBtn.title = 'Kaydı durdur';
        
        voiceStatus.style.display = 'block';
        voiceIndicator.classList.add('recording');
        voiceIndicator.innerHTML = '<i class="fas fa-microphone"></i><span>Ses kaydı yapılıyor...</span>';
    } else {
        voiceBtn.classList.remove('recording');
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        voiceBtn.title = 'Ses ile soru sor';
        
        voiceStatus.style.display = 'none';
        voiceIndicator.classList.remove('recording');
        voiceIndicator.innerHTML = '<i class="fas fa-microphone-slash"></i><span>Ses kaydı durduruldu</span>';
    }
}

// Ses kayıt toggle fonksiyonu
function toggleVoiceRecording() {
    if (!recognition) {
        recognition = initSpeechRecognition();
        if (!recognition) return;
    }
    
    if (isRecording) {
        // Kaydı durdur
        recognition.stop();
    } else {
        // Kaydı başlat
        try {
            recognition.start();
        } catch (error) {
            console.error('Ses kaydı başlatılamadı:', error);
            showToast('Ses kaydı başlatılamadı', 'error');
        }
    }
}

// DOM yüklendiğinde çalışacak fonksiyonlar
document.addEventListener('DOMContentLoaded', function() {
    // Moment.js Türkçe ayarları
    moment.locale('tr');
    
    // Input alanına odaklan
    document.getElementById('messageInput').focus();
    
    // Chat mesajlarını en alta kaydır
    scrollToBottom();
    
    // Ses API'sini başlat
    if (checkSpeechSupport()) {
        initSpeechRecognition();
        console.log('Ses API başlatıldı');
    } else {
        console.warn('Ses API desteklenmiyor');
        // Ses butonunu devre dışı bırak
        const voiceBtn = document.getElementById('voiceBtn');
        voiceBtn.disabled = true;
        voiceBtn.title = 'Ses kaydı desteklenmiyor';
        voiceBtn.style.opacity = '0.5';
        voiceBtn.style.cursor = 'not-allowed';
    }
    
    // ESC tuşu ile modal kapatma
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const searchModal = document.getElementById('searchModal');
            const shareModal = document.getElementById('shareModal');
            
            if (searchModal.classList.contains('show')) {
                closeSearchModal();
            } else if (shareModal.classList.contains('show')) {
                closeShareModal();
            }
        }
    });
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
        
        // Session ID'yi güncelle
        if (data.session_id) {
            currentSessionId = data.session_id;
        }
        
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
    const chatMessagesElement = document.getElementById('chatMessages');
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
    chatMessagesElement.appendChild(messageDiv);
    
    // Mesajı global array'e ekle
    chatMessages.push({
        id: Date.now().toString(),
        text: text,
        sender: sender,
        type: type,
        data: data,
        timestamp: currentTime,
        element: messageDiv
    });
    
    // Mesajları en alta kaydır
    scrollToBottom();
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
async function startNewChat() {
    try {
        // Yeni sohbet oturumu oluştur
        const response = await fetch('/api/new_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentSessionId = data.session_id;
            
            const chatMessagesElement = document.getElementById('chatMessages');
            const suggestedPrompts = document.getElementById('suggestedPrompts');
            
            // Mesajları temizle (ilk karşılama mesajı hariç)
            const welcomeMessage = chatMessagesElement.querySelector('.bot-message');
            chatMessagesElement.innerHTML = '';
            chatMessagesElement.appendChild(welcomeMessage);
            
            // Global mesaj array'ini temizle
            chatMessages = [];
            
            // Önerileri göster
            suggestedPrompts.style.display = 'flex';
            
            // Input alanını temizle ve odaklan
            const messageInput = document.getElementById('messageInput');
            messageInput.value = '';
            messageInput.focus();
            
            // Mesajları en alta kaydır
            scrollToBottom();
            
            showToast('Yeni sohbet başlatıldı', 'success');
        } else {
            showToast('Yeni sohbet başlatılamadı', 'error');
        }
    } catch (error) {
        console.error('Yeni sohbet hatası:', error);
        showToast('Yeni sohbet başlatılamadı', 'error');
    }
}

// Sohbet geçmişini indirme
async function downloadChatHistory() {
    if (!currentSessionId) {
        showToast('İndirilecek sohbet geçmişi bulunamadı', 'error');
        return;
    }
    
    try {
        // İndirme linki oluştur
        const downloadUrl = `/api/chat_history?session_id=${currentSessionId}`;
        
        // Link oluştur ve tıkla
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = `kchol_chat_history_${currentSessionId}.txt`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showToast('Sohbet geçmişi indiriliyor...', 'success');
    } catch (error) {
        console.error('İndirme hatası:', error);
        showToast('Sohbet geçmişi indirilemedi', 'error');
    }
}

// Arama modalı açma
function openSearchModal() {
    const searchModal = document.getElementById('searchModal');
    searchModal.classList.add('show');
    document.getElementById('searchInput').focus();
    
    // Modal dışına tıklayarak kapatma
    searchModal.addEventListener('click', function(event) {
        if (event.target === searchModal) {
            closeSearchModal();
        }
    });
}

// Arama modalı kapatma
function closeSearchModal() {
    const searchModal = document.getElementById('searchModal');
    searchModal.classList.remove('show');
    document.getElementById('searchInput').value = '';
    document.getElementById('searchResults').innerHTML = '';
}

// Arama yapma
function performSearch() {
    const searchTerm = document.getElementById('searchInput').value.trim().toLowerCase();
    if (!searchTerm) {
        showToast('Lütfen arama terimi girin', 'error');
        return;
    }
    
    searchInMessages(searchTerm);
}

// Mesajlarda arama
function searchInMessages(searchTerm) {
    const searchResults = document.getElementById('searchResults');
    const results = [];
    
    // Tüm mesajlarda arama yap
    chatMessages.forEach(message => {
        if (message.text.toLowerCase().includes(searchTerm)) {
            results.push(message);
        }
    });
    
    // Sonuçları göster
    displaySearchResults(results, searchTerm);
}

// Arama sonuçlarını gösterme
function displaySearchResults(results, searchTerm) {
    const searchResults = document.getElementById('searchResults');
    
    if (results.length === 0) {
        searchResults.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search" style="font-size: 24px; margin-bottom: 12px; display: block;"></i>
                <p>"${searchTerm}" için sonuç bulunamadı</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    results.forEach(message => {
        const highlightedText = message.text.replace(
            new RegExp(searchTerm, 'gi'),
            match => `<span class="search-highlight">${match}</span>`
        );
        
        html += `
            <div class="search-result-item" onclick="scrollToMessage('${message.id}')">
                <div class="search-result-sender">${message.sender === 'bot' ? 'KCHOL Asistan' : 'Siz'}</div>
                <div class="search-result-text">${highlightedText}</div>
                <div class="search-result-time">${message.timestamp}</div>
            </div>
        `;
    });
    
    searchResults.innerHTML = html;
}

// Mesaja kaydırma
function scrollToMessage(messageId) {
    const message = chatMessages.find(m => m.id === messageId);
    if (message && message.element) {
        message.element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        message.element.style.animation = 'pulse 1s ease';
        setTimeout(() => {
            message.element.style.animation = '';
        }, 1000);
        closeSearchModal();
    }
}

// Enter tuşu ile arama
function searchMessages(event) {
    if (event.key === 'Enter') {
        performSearch();
    }
}

// Paylaşma modalı açma
function openShareModal() {
    const shareModal = document.getElementById('shareModal');
    shareModal.classList.add('show');
    
    // Paylaşım önizlemesini güncelle
    updateSharePreview();
    
    // Modal dışına tıklayarak kapatma
    shareModal.addEventListener('click', function(event) {
        if (event.target === shareModal) {
            closeShareModal();
        }
    });
}

// Paylaşma modalı kapatma
function closeShareModal() {
    const shareModal = document.getElementById('shareModal');
    shareModal.classList.remove('show');
}

// Paylaşım önizlemesini güncelle
function updateSharePreview() {
    const preview = document.getElementById('sharePreview');
    let content = '';
    
    if (chatMessages.length === 0) {
        content = 'Henüz mesaj yok.';
    } else {
        // Son 3 mesajı al
        const recentMessages = chatMessages.slice(-3);
        content = recentMessages.map(msg => {
            const sender = msg.sender === 'bot' ? 'KCHOL Asistan' : 'Siz';
            return `[${sender}]: ${msg.text.substring(0, 100)}${msg.text.length > 100 ? '...' : ''}`;
        }).join('\n\n');
    }
    
    preview.textContent = content;
}

// WhatsApp'ta paylaş
function shareToWhatsApp() {
    const shareText = generateShareText();
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(shareText)}`;
    window.open(whatsappUrl, '_blank');
    closeShareModal();
    showToast('WhatsApp\'ta paylaşılıyor...', 'success');
}

// Telegram'da paylaş
function shareToTelegram() {
    const shareText = generateShareText();
    const telegramUrl = `https://t.me/share/url?url=${encodeURIComponent(window.location.href)}&text=${encodeURIComponent(shareText)}`;
    window.open(telegramUrl, '_blank');
    closeShareModal();
    showToast('Telegram\'da paylaşılıyor...', 'success');
}

// E-posta ile paylaş
function shareToEmail() {
    const shareText = generateShareText();
    const subject = 'KCHOL Hisse Senedi Asistanı - Sohbet Geçmişi';
    const body = shareText;
    const mailtoUrl = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.location.href = mailtoUrl;
    closeShareModal();
    showToast('E-posta uygulaması açılıyor...', 'success');
}

// Panoya kopyala
async function copyToClipboard() {
    try {
        const shareText = generateShareText();
        await navigator.clipboard.writeText(shareText);
        closeShareModal();
        showToast('Panoya kopyalandı!', 'success');
    } catch (error) {
        console.error('Kopyalama hatası:', error);
        showToast('Kopyalama başarısız', 'error');
    }
}

// Twitter'da paylaş
function shareToTwitter() {
    const shareText = generateShareText();
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}`;
    window.open(twitterUrl, '_blank');
    closeShareModal();
    showToast('Twitter\'da paylaşılıyor...', 'success');
}

// LinkedIn'de paylaş
function shareToLinkedIn() {
    const shareText = generateShareText();
    const linkedinUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(window.location.href)}&title=${encodeURIComponent('KCHOL Hisse Senedi Asistanı')}&summary=${encodeURIComponent(shareText)}`;
    window.open(linkedinUrl, '_blank');
    closeShareModal();
    showToast('LinkedIn\'de paylaşılıyor...', 'success');
}

// Paylaşım metni oluştur
function generateShareText() {
    let text = '🤖 KCHOL Hisse Senedi Asistanı\n\n';
    
    if (chatMessages.length === 0) {
        text += 'Henüz sohbet geçmişi yok.';
    } else {
        // Son 5 mesajı al
        const recentMessages = chatMessages.slice(-5);
        text += recentMessages.map(msg => {
            const sender = msg.sender === 'bot' ? '🤖 KCHOL Asistan' : '👤 Siz';
            return `${sender}: ${msg.text}`;
        }).join('\n\n');
    }
    
    text += `\n\n💬 Sohbet etmek için: ${window.location.href}`;
    text += '\n📊 KCHOL hisse senedi fiyat tahmini ve finansal analiz';
    
    return text;
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