/**
 * Alfalah GPT Chat Widget
 * Self-contained IIFE — embed via <script src="widget.js"></script>
 *
 * Usage:
 *   AlfalahChat.init({
 *     apiUrl:  "ws://your-alb-dns/ws/chat/",  // trailing slash required
 *     rateUrl: "http://your-alb-dns/api/v1/ratings",
 *   });
 */
(function () {
  "use strict";

  // Capture before any async context makes document.currentScript null
  const SCRIPT_SRC = document.currentScript ? document.currentScript.src : null;

  // ── Config ────────────────────────────────────────────────
  const defaults = {
    apiUrl:  "ws://localhost:8000/ws/chat/",
    rateUrl: "http://localhost:8000/api/v1/ratings",
  };

  // ── State ─────────────────────────────────────────────────
  let ws = null;
  let conversationId = null;
  let config = {};
  let reconnectAttempts = 0;
  const MAX_RECONNECT = 5;

  // ── Helpers ───────────────────────────────────────────────
  function uuid() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
    });
  }

  function formatTime(date) {
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function escapeHtml(text) {
    const d = document.createElement("div");
    d.appendChild(document.createTextNode(text));
    return d.innerHTML;
  }

  // ── Minimal inline markdown renderer (no external deps) ──────────────
  function miniMd(text) {
    return text
      // Bold **text** or __text__
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/__(.+?)__/g, "<strong>$1</strong>")
      // Italic *text* or _text_
      .replace(/\*([^*]+)\*/g, "<em>$1</em>")
      .replace(/_([^_]+)_/g, "<em>$1</em>")
      // Code `text`
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      // ### H3 / ## H2 / # H1
      .replace(/^### (.+)$/gm, "<h3>$1</h3>")
      .replace(/^## (.+)$/gm, "<h2>$1</h2>")
      .replace(/^# (.+)$/gm, "<h1>$1</h1>")
      // Unordered list items: lines starting with - or *
      .replace(/^[\-\*] (.+)$/gm, "<li>$1</li>")
      // Wrap consecutive <li> blocks in <ul>
      .replace(/(<li>.*<\/li>\n?)+/g, (m) => "<ul>" + m + "</ul>")
      // Horizontal rule
      .replace(/^---+$/gm, "<hr>")
      // Newlines to <br> (skip inside block elements)
      .replace(/\n(?!<\/?(?:ul|li|h[123]|hr))/g, "<br>");
  }

  // ── DOM refs (set after inject) ───────────────────────────
  let $window, $messages, $input, $send, $typing, $offline, $launcher, $badge;

  // ── Logo SVG (Alfalah geometric mark) ─────────────────────
  const LOGO_SVG = `<svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M20 4L34 12V28L20 36L6 28V12L20 4Z" fill="#003057"/>
    <path d="M20 10L28 15V25L20 30L12 25V15L20 10Z" fill="#F37021"/>
    <path d="M20 16L24 18.5V23.5L20 26L16 23.5V18.5L20 16Z" fill="#fff"/>
  </svg>`;

  // ── Inject HTML ───────────────────────────────────────────
  function injectHTML() {
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = new URL("widget.css", SCRIPT_SRC || location.href).href;
    document.head.appendChild(css);

    document.body.insertAdjacentHTML("beforeend", `
      <button id="alf-launcher" aria-label="Open Alfalah GPT chat">
        <span id="alf-launcher-label">Alfalah GPT</span>
        <span id="alf-launcher-logo">${LOGO_SVG}</span>
        <span id="alf-unread-badge"></span>
      </button>

      <div id="alf-window" class="alf-hidden" role="dialog" aria-label="Alfalah GPT chat">
        <div id="alf-header">
          <span id="alf-header-logo">${LOGO_SVG}</span>
          <p id="alf-header-title">Alfalah GPT</p>
          <button id="alf-end-btn">End Chat</button>
          <button id="alf-minimize-btn" aria-label="Minimize chat">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
        </div>
        <div id="alf-offline">⚡ Reconnecting...</div>
        <div id="alf-messages" role="log" aria-live="polite"></div>
        <div id="alf-input-area">
          <div id="alf-input-row">
            <textarea
              id="alf-input"
              placeholder="Type your message here..."
              rows="1"
              aria-label="Message input"
            ></textarea>
            <button id="alf-send" aria-label="Send message">
              <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
          </div>
        </div>
        <div id="alf-footer">
          By using this AI assistant, you acknowledge and agree that responses are AI-generated.
          <a href="#">Read more</a>
        </div>
      </div>
    `);

    $window   = document.getElementById("alf-window");
    $messages = document.getElementById("alf-messages");
    $input    = document.getElementById("alf-input");
    $send     = document.getElementById("alf-send");
    $typing   = document.createElement("div");
    $offline  = document.getElementById("alf-offline");
    $launcher = document.getElementById("alf-launcher");
    $badge    = document.getElementById("alf-unread-badge");

    $typing.id = "alf-typing";
    $typing.innerHTML = '<span class="alf-dot"></span><span class="alf-dot"></span><span class="alf-dot"></span>';
    $messages.appendChild($typing);

    bindEvents();
  }

  // ── Append messages ───────────────────────────────────────
  function appendMessage(role, text, msgSk) {
    const wrap = document.createElement("div");
    wrap.className = `alf-msg alf-${role}`;

    const bubble = document.createElement("div");
    bubble.className = "alf-bubble";
    if (role === "bot") {
      bubble.innerHTML = miniMd(text);
    } else {
      bubble.innerHTML = escapeHtml(text).replace(/\n/g, "<br>");
    }
    wrap.appendChild(bubble);

    const ts = document.createElement("span");
    ts.className = "alf-timestamp";
    ts.textContent = formatTime(new Date());
    wrap.appendChild(ts);

    // Rating buttons for bot messages
    if (role === "bot" && msgSk) {
      const rating = document.createElement("div");
      rating.className = "alf-rating";
      rating.innerHTML = `
        <button data-sk="${msgSk}" data-val="1" aria-label="Thumbs up">👍</button>
        <button data-sk="${msgSk}" data-val="-1" aria-label="Thumbs down">👎</button>
      `;
      rating.querySelectorAll("button").forEach((btn) => {
        btn.addEventListener("click", () => submitRating(msgSk, parseInt(btn.dataset.val), rating));
      });
      wrap.appendChild(rating);
    }

    // Insert before typing indicator
    $messages.insertBefore(wrap, $typing);
    $messages.scrollTop = $messages.scrollHeight;
    return wrap;
  }

  function appendToolIndicator(text) {
    const el = document.createElement("div");
    el.className = "alf-tool-indicator";
    el.textContent = text;
    $messages.insertBefore(el, $typing);
    $messages.scrollTop = $messages.scrollHeight;
    return el;
  }

  function showTyping(show) {
    $typing.className = show ? "alf-typing alf-show" : "alf-typing";
    if (show) $messages.scrollTop = $messages.scrollHeight;
  }

  function setOffline(offline) {
    $offline.className = offline ? "alf-show" : "";
  }

  // ── Rating submission ──────────────────────────────────────
  async function submitRating(msgSk, val, container) {
    try {
      await fetch(config.rateUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: conversationId,
          message_sk: msgSk,
          rating: val,
        }),
      });
      container.querySelectorAll("button").forEach((b) => {
        b.classList.toggle("alf-rated", parseInt(b.dataset.val) === val);
        b.disabled = true;
      });
    } catch (_) { /* silent */ }
  }

  // ── WebSocket ──────────────────────────────────────────────
  function connect() {
    const url = `${config.apiUrl}${conversationId}`;
    ws = new WebSocket(url);

    ws.onopen = () => {
      reconnectAttempts = 0;
      setOffline(false);
      $send.disabled = false;
    };

    // Streaming state — one active bubble accumulates chunks
    let _streamBubble = null;
    let _streamText   = "";
    let _streamSk     = null;
    let _toolIndicator = null;

    ws.onmessage = (e) => {
      const data = e.data;

      // ── Tool hint ────────────────────────────────────────────────────────
      const toolMatch = data.match(/^\[TOOL:([^\]]+)\]$/);
      if (toolMatch) {
        const toolName = toolMatch[1].replace(/_/g, " ");
        if (_toolIndicator) _toolIndicator.remove();
        _toolIndicator = appendToolIndicator(`🔍 Looking up ${toolName}…`);
        _streamBubble = null;
        _streamText   = "";
        _streamSk     = null;
        return;
      }

      // ── Stream end sentinel — finalise bubble ────────────────────────────
      if (data === "[STREAM_END]") {
        if (_toolIndicator) { _toolIndicator.remove(); _toolIndicator = null; }
        if (_streamBubble) {
          // Apply markdown to the complete accumulated text
          _streamBubble.innerHTML = miniMd(_streamText);
          $messages.scrollTop = $messages.scrollHeight;

          // Add rating buttons
          const wrap = _streamBubble.parentElement;
          if (wrap && wrap._ratingPending) {
            wrap._ratingPending = false;
            const rating = document.createElement("div");
            rating.className = "alf-rating";
            rating.innerHTML = `
              <button data-sk="${wrap._sk}" data-val="1" aria-label="Thumbs up">👍</button>
              <button data-sk="${wrap._sk}" data-val="-1" aria-label="Thumbs down">👎</button>
            `;
            rating.querySelectorAll("button").forEach((btn) => {
              btn.addEventListener("click", () => submitRating(wrap._sk, parseInt(btn.dataset.val), rating));
            });
            wrap.appendChild(rating);
          }

          // Badge when window is closed
          if ($window.classList.contains("alf-hidden")) {
            $badge.style.display = "flex";
            $badge.textContent = (parseInt($badge.textContent || "0") + 1).toString();
          }

          _streamBubble = null;
          _streamText   = "";
          _streamSk     = null;
        }
        // Re-enable send
        $send.disabled = ws.readyState !== WebSocket.OPEN;
        return;
      }

      // ── Text chunk — accumulate raw text, show as plain during streaming ─
      showTyping(false);
      if (_toolIndicator) { _toolIndicator.remove(); _toolIndicator = null; }

      if (!_streamBubble) {
        _streamSk = Date.now() + "-" + Math.random().toString(36).slice(2, 8);
        const wrap = document.createElement("div");
        wrap.className = "alf-msg alf-bot";
        _streamBubble = document.createElement("div");
        _streamBubble.className = "alf-bubble alf-streaming";
        wrap.appendChild(_streamBubble);

        const ts = document.createElement("span");
        ts.className = "alf-timestamp";
        ts.textContent = formatTime(new Date());
        wrap.appendChild(ts);

        wrap._ratingPending = true;
        wrap._sk = _streamSk;
        $messages.insertBefore(wrap, $typing);
      }

      _streamText += data;
      // Show raw text while streaming (markdown will be applied at STREAM_END)
      _streamBubble.textContent = _streamText;
      $messages.scrollTop = $messages.scrollHeight;
    };

    ws.onerror = () => setOffline(true);

    ws.onclose = () => {
      setOffline(true);
      $send.disabled = true;
      showTyping(false);
      scheduleReconnect();
    };
  }

  function scheduleReconnect() {
    if (reconnectAttempts >= MAX_RECONNECT) return;
    const delay = Math.min(1000 * 2 ** reconnectAttempts, 16000);
    reconnectAttempts++;
    setTimeout(connect, delay);
  }

  // ── Send message ───────────────────────────────────────────
  function sendMessage() {
    const text = $input.value.trim();
    if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;

    appendMessage("user", text, null);
    showTyping(true);
    $send.disabled = true;
    $input.value = "";
    $input.style.height = "auto";

    ws.send(text);
    setTimeout(() => { $send.disabled = ws.readyState !== WebSocket.OPEN; }, 100);
  }

  // ── Event binding ─────────────────────────────────────────
  function bindEvents() {
    $launcher.addEventListener("click", () => {
      $window.classList.remove("alf-hidden");
      $badge.style.display = "none";
      $badge.textContent = "0";
      $input.focus();
    });

    document.getElementById("alf-minimize-btn").addEventListener("click", () => {
      $window.classList.add("alf-hidden");
    });

    document.getElementById("alf-end-btn").addEventListener("click", () => {
      $window.classList.add("alf-hidden");
      if (ws) { ws.close(); ws = null; }
      $messages.querySelectorAll(".alf-msg, .alf-tool-indicator").forEach(el => el.remove());
      conversationId = null;
      sessionStorage.removeItem("alf_conv_id");
    });

    $send.addEventListener("click", sendMessage);

    $input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Auto-resize textarea
    $input.addEventListener("input", () => {
      $input.style.height = "auto";
      $input.style.height = Math.min($input.scrollHeight, 120) + "px";
    });
  }

  // ── Public API ────────────────────────────────────────────
  window.AlfalahChat = {
    init(userConfig) {
      config = Object.assign({}, defaults, userConfig);
      conversationId =
        sessionStorage.getItem("alf_conv_id") || uuid();
      sessionStorage.setItem("alf_conv_id", conversationId);

      injectHTML();
      connect();

      // Welcome message
      appendMessage(
        "bot",
        "Hello! I'm Alfalah GPT 👋\n\nI can help you with fund NAVs, performance data, account queries, and more. How can I help you today?",
        null
      );
    },
  };
})();
