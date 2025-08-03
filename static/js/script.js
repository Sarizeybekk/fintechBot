// Global değişkenler
let isLoading = false;

// DOM yüklendiğinde çalışacak fonksiyonlar
document.addEventListener('DOMContentLoaded', function() {
    // Moment.js Türkçe ayarları
    moment.locale('tr');
    
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