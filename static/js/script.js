// Global değişkenler
let isLoading = false;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let recognition = null;

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
    
    // Speech Recognition'ı başlat
    initSpeechRecognition();
    
    // Input alanına odaklan
    document.getElementById('messageInput').focus();
    
    // Chat mesajlarını en alta kaydır
    scrollToBottom();
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
function startNewChat() {
    const chatMessages = document.getElementById('chatMessages');
    const suggestedPrompts = document.getElementById('suggestedPrompts');
    
    // Mesajları temizle (ilk karşılama mesajı hariç)
    const welcomeMessage = chatMessages.querySelector('.bot-message');
    chatMessages.innerHTML = '';
    chatMessages.appendChild(welcomeMessage);
    
    // Önerileri göster
    suggestedPrompts.style.display = 'flex';
    
    // Input alanını temizle ve odaklan
    const messageInput = document.getElementById('messageInput');
    messageInput.value = '';
    messageInput.focus();
    
    // Mesajları en alta kaydır
    scrollToBottom();
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
    
    if (downloadDropdown && !downloadDropdown.contains(event.target)) {
        downloadOptions.classList.remove('show');
    }
}); 