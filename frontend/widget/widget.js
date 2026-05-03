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

  // ── DOM refs (set after inject) ───────────────────────────
  let $window, $messages, $input, $send, $typing, $offline, $launcher, $badge;

  // ── Inject HTML ───────────────────────────────────────────
  function injectHTML() {
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = new URL("widget.css", document.currentScript
      ? document.currentScript.src
      : location.href
    ).href;
    document.head.appendChild(css);

    document.body.insertAdjacentHTML("beforeend", `
      <button id="alf-launcher" aria-label="Open Alfalah GPT chat">
        <svg viewBox="0 0 24 24"><path d="M20 2H4a2 2 0 0 0-2 2v18l4-4h14a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2z"/></svg>
        <span id="alf-unread-badge"></span>
      </button>

      <div id="alf-window" class="alf-hidden" role="dialog" aria-label="Alfalah GPT chat">
        <div id="alf-header">
          <div id="alf-avatar">🤖</div>
          <div id="alf-header-text">
            <p id="alf-header-title">Alfalah GPT</p>
            <p id="alf-header-sub">Powered by AI · Always here to help</p>
          </div>
          <div id="alf-status-dot"></div>
          <button id="alf-close-btn" aria-label="Close chat">✕</button>
        </div>
        <div id="alf-offline">⚡ Reconnecting...</div>
        <div id="alf-messages" role="log" aria-live="polite"></div>
        <div id="alf-input-area">
          <textarea
            id="alf-input"
            placeholder="Ask about funds, NAVs, or account help…"
            rows="1"
            aria-label="Message input"
          ></textarea>
          <button id="alf-send" aria-label="Send message">
            <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
          </button>
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

    // Typing indicator element
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
    bubble.innerHTML = escapeHtml(text).replace(/\n/g, "<br>");
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

    ws.onmessage = (e) => {
      let text = e.data;
      let toolIndicator = null;

      // Detect tool call hints embedded in message (e.g. "[TOOL:get_fund_nav]")
      const toolMatch = text.match(/^\[TOOL:([^\]]+)\]/);
      if (toolMatch) {
        const toolName = toolMatch[1].replace(/_/g, " ");
        toolIndicator = appendToolIndicator(`🔍 ${toolName}…`);
        text = text.replace(toolMatch[0], "").trim();
      }

      showTyping(false);
      if (toolIndicator) toolIndicator.remove();

      const sk = Date.now() + "-" + Math.random().toString(36).slice(2, 8);
      appendMessage("bot", text, sk);

      // Show badge if window is closed
      if ($window.classList.contains("alf-hidden")) {
        $badge.style.display = "flex";
        $badge.textContent = (parseInt($badge.textContent || "0") + 1).toString();
      }
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
      $window.classList.toggle("alf-hidden");
      $badge.style.display = "none";
      $badge.textContent = "0";
      if (!$window.classList.contains("alf-hidden")) $input.focus();
    });

    document.getElementById("alf-close-btn").addEventListener("click", () => {
      $window.classList.add("alf-hidden");
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
