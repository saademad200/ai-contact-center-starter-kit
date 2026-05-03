/**
 * Alfalah GPT Admin Panel SPA — JS
 */

const API_BASE = '/api/v1';

// --- Auth & JWT ---
function getToken() {
  return localStorage.getItem('alf_admin_token');
}

function setToken(token) {
  localStorage.setItem('alf_admin_token', token);
}

function logout() {
  localStorage.removeItem('alf_admin_token');
  window.location.href = '/admin/login.html';
}

async function apiFetch(endpoint, options = {}) {
  const token = getToken();
  if (!token && !endpoint.includes('/auth/token')) {
    logout();
    return;
  }
  
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  
  if (res.status === 401) {
    logout();
    throw new Error("Unauthorized");
  }
  
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "API Request Failed");
  }
  
  return res.json();
}

// --- Login Page ---
const loginForm = document.getElementById('login-form');
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(loginForm);
    try {
      const res = await fetch(`${API_BASE}/auth/token`, {
        method: 'POST',
        body: formData
      });
      if (!res.ok) throw new Error("Invalid credentials");
      const data = await res.json();
      setToken(data.access_token);
      window.location.href = '/admin/dashboard.html';
    } catch (err) {
      const msg = document.getElementById('error-msg');
      msg.textContent = err.message;
      msg.classList.remove('hidden');
    }
  });
}

// --- Layout Injector ---
function injectLayout(activeTab, title) {
  const sidebar = `
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-dot"></div><span>Alfalah GPT</span><small>Admin</small>
      </div>
      <nav class="sidebar-nav">
        <a href="/admin/dashboard.html" class="nav-item ${activeTab==='dashboard'?'active':''}"><span class="nav-icon">📊</span> Dashboard</a>
        <a href="/admin/conversations.html" class="nav-item ${activeTab==='conversations'?'active':''}"><span class="nav-icon">💬</span> Conversations</a>
        <a href="/admin/tickets.html" class="nav-item ${activeTab==='tickets'?'active':''}"><span class="nav-icon">🎫</span> Tickets</a>
        <a href="/admin/knowledge_base.html" class="nav-item ${activeTab==='knowledge_base'?'active':''}"><span class="nav-icon">📚</span> Knowledge Base</a>
        <a href="/admin/llmops.html" class="nav-item ${activeTab==='llmops'?'active':''}"><span class="nav-icon">🤖</span> LLMOps</a>
        <a href="/admin/quality.html" class="nav-item ${activeTab==='quality'?'active':''}"><span class="nav-icon">⭐</span> Quality</a>
      </nav>
      <div class="sidebar-footer">
        <a href="#" onclick="logout()" class="logout-btn">Sign out</a>
      </div>
    </aside>
  `;
  
  const header = `
    <header class="topbar">
      <h1 class="page-title">${title}</h1>
      <div class="topbar-user"><span class="user-badge">Admin</span></div>
    </header>
  `;

  document.body.innerHTML = `
    <div class="layout">
      ${sidebar}
      <main class="main-content">
        ${header}
        <div class="content-body" id="main-content"></div>
      </main>
    </div>
  `;
}

// --- Dashboard ---
async function loadDashboard() {
  injectLayout('dashboard', 'Dashboard');
  const main = document.getElementById('main-content');
  main.innerHTML = `<div class="empty-state">Loading stats...</div>`;
  
  try {
    const stats = await apiFetch('/admin/stats');
    main.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-icon">💬</div><div class="stat-value">${stats.total_conversations}</div><div class="stat-label">Total Conversations</div></div>
        <div class="stat-card"><div class="stat-icon">🎫</div><div class="stat-value">${stats.open_tickets}</div><div class="stat-label">Open Tickets</div></div>
        <div class="stat-card"><div class="stat-icon">📚</div><div class="stat-value">${stats.total_documents}</div><div class="stat-label">KB Documents</div></div>
        <div class="stat-card"><div class="stat-icon">🤖</div><div class="stat-value" style="font-size:1.2rem;line-height:1.5rem">${stats.active_model}</div><div class="stat-label">Active Model</div></div>
      </div>
      <div class="card mt-6">
        <div class="card-header"><h3>Active System Prompt</h3><a href="/admin/llmops.html" class="btn btn-sm">Manage →</a></div>
        <div class="card-body"><pre class="prompt-preview">${stats.active_prompt}</pre></div>
      </div>
    `;
  } catch(e) { main.innerHTML = `<div class="alert alert-error">${e.message}</div>`; }
}

// --- Setup Router ---
const path = window.location.pathname;
if (!getToken() && !path.includes('login.html')) {
  window.location.href = '/admin/login.html';
}

// --- Page Renderers ---

async function loadConversations() {
  injectLayout('conversations', 'Conversations');
  const main = document.getElementById('main-content');
  try {
    const data = await apiFetch('/conversations');
    let rows = data.map(c => `
      <tr>
        <td><code class="mono">${c.pk}</code></td>
        <td><span class="badge badge-${c.status==='active'?'success':'muted'}">${c.status}</span></td>
        <td>${c.created_at.substring(0, 19).replace('T', ' ')}</td>
        <td><a href="#" class="btn btn-sm">View →</a></td>
      </tr>
    `).join('');
    main.innerHTML = `
      <div class="card"><table class="data-table">
        <thead><tr><th>ID</th><th>Status</th><th>Started</th><th>Actions</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="4" class="empty-state">No conversations yet.</td></tr>'}</tbody>
      </table></div>
    `;
  } catch(e) { main.innerHTML = `<div class="alert alert-error">${e.message}</div>`; }
}

async function loadTickets() {
  injectLayout('tickets', 'Support Tickets');
  const main = document.getElementById('main-content');
  try {
    const data = await apiFetch('/tickets');
    let rows = data.map(t => `
      <tr>
        <td><code class="mono">${t.pk}</code></td>
        <td>${t.conversation_id}</td>
        <td><span class="badge badge-${t.status==='open'?'warning':'success'}">${t.status}</span></td>
        <td>${t.created_at.substring(0, 19).replace('T', ' ')}</td>
      </tr>
    `).join('');
    main.innerHTML = `
      <div class="card"><table class="data-table">
        <thead><tr><th>Ticket ID</th><th>Conversation</th><th>Status</th><th>Created</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="4" class="empty-state">No tickets yet.</td></tr>'}</tbody>
      </table></div>
    `;
  } catch(e) { main.innerHTML = `<div class="alert alert-error">${e.message}</div>`; }
}

// --- Setup Router ---
const path = window.location.pathname;
if (!getToken() && !path.includes('login.html')) {
  window.location.href = '/admin/login.html';
}

if (path.includes('dashboard.html')) loadDashboard();
else if (path.includes('conversations.html')) loadConversations();
else if (path.includes('tickets.html')) loadTickets();
else if (path.includes('llmops.html')) { injectLayout('llmops', 'LLMOps'); document.getElementById('main-content').innerHTML = '<div class="empty-state">LLMOps UI loaded via API.</div>'; }
else if (path.includes('knowledge_base.html')) { injectLayout('knowledge_base', 'Knowledge Base'); document.getElementById('main-content').innerHTML = '<div class="empty-state">KB UI loaded via API.</div>'; }
else if (path.includes('quality.html')) { injectLayout('quality', 'Quality'); document.getElementById('main-content').innerHTML = '<div class="empty-state">Quality UI loaded via API.</div>'; }
