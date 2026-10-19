/**
 * ISVANTE AI HOROLOGY CONCIERGE
 * Client interaction widget with dynamic catalog grounding
 */

(function() {
  let chatHistory = [];
  let isSending = false;

  function initChatbot() {
    const toggleBtn = document.getElementById('chatbot-toggle-btn');
    const modal = document.getElementById('chatbot-modal');
    const closeBtn = document.getElementById('chatbot-close-btn');
    const form = document.getElementById('chat-form');
    const input = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    const quickChips = document.querySelectorAll('.quick-chip');

    if (!toggleBtn || !modal) return;

    // Toggle open/close
    toggleBtn.addEventListener('click', () => {
      const isActive = modal.classList.toggle('active');
      if (isActive && messagesContainer.children.length === 0) {
        addBotMessage("Greetings. I am the **ISVANTE AI Concierge**. How may I assist you with our luxury timepieces, Cash on Delivery in Pakistan, or order details today?");
      }
      if (isActive && input) {
        setTimeout(() => input.focus(), 200);
      }
    });

    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        modal.classList.remove('active');
      });
    }

    // Quick chips
    quickChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const text = chip.dataset.query || chip.textContent;
        sendMessage(text);
      });
    });

    // Form submit
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (text && !isSending) {
          sendMessage(text);
          input.value = '';
        }
      });
    }
  }

  function addBotMessage(text) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble bot';
    bubble.innerHTML = formatMarkdown(text);
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;

    chatHistory.push({ sender: 'bot', text: text });
  }

  function addUserMessage(text) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble user';
    bubble.textContent = text;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;

    chatHistory.push({ sender: 'user', text: text });
  }

  function showTypingIndicator() {
    const container = document.getElementById('chat-messages');
    const indicator = document.createElement('div');
    indicator.id = 'chat-typing-indicator';
    indicator.className = 'chat-bubble bot';
    indicator.innerHTML = `
      <div style="display: flex; gap: 4px; align-items: center; padding: 4px 0;">
        <span style="width: 6px; height: 6px; background: var(--gold-primary); border-radius: 50%; animation: pulse 1s infinite;"></span>
        <span style="width: 6px; height: 6px; background: var(--gold-primary); border-radius: 50%; animation: pulse 1s infinite 0.2s;"></span>
        <span style="width: 6px; height: 6px; background: var(--gold-primary); border-radius: 50%; animation: pulse 1s infinite 0.4s;"></span>
      </div>
    `;
    container.appendChild(indicator);
    container.scrollTop = container.scrollHeight;
  }

  function removeTypingIndicator() {
    const indicator = document.getElementById('chat-typing-indicator');
    if (indicator) indicator.remove();
  }

  async function sendMessage(text) {
    addUserMessage(text);
    isSending = true;
    showTypingIndicator();

    try {
      const res = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: chatHistory.slice(-6)
        })
      });
      const data = await res.json();
      removeTypingIndicator();

      if (data.success) {
        addBotMessage(data.reply);
      } else {
        addBotMessage("I apologize, but our concierge is momentarily offline. Please reach us directly on WhatsApp for prompt assistance.");
      }
    } catch (e) {
      removeTypingIndicator();
      addBotMessage("Unable to reach the concierge server. Please verify your connection or contact our team via WhatsApp.");
    } finally {
      isSending = false;
    }
  }

  // Basic markdown parser for bold, links, lists
  function formatMarkdown(str) {
    if (!str) return '';
    let html = str
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/~~(.*?)~~/g, '<del>$1</del>')
      .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color: var(--gold-light); text-decoration: underline;">$1</a>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n/g, '<br>');
    return html;
  }

  document.addEventListener('DOMContentLoaded', initChatbot);
})();
