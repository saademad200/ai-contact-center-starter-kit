import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { MessageSquare, Ticket, FileText, Settings, Award, LogOut, LayoutDashboard, Users, Upload, RefreshCw } from 'lucide-react';
import { marked } from 'marked';
import './index.css';

// Configure marked for safe inline rendering
marked.setOptions({ breaks: true, gfm: true });

const API_BASE = '/api/v1';

// --- Auth Context ---
const AuthContext = React.createContext(null);

function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('alf_admin_token'));
  const login  = (t) => { localStorage.setItem('alf_admin_token', t); setToken(t); };
  const logout = ()  => { localStorage.removeItem('alf_admin_token'); setToken(null); };
  return <AuthContext.Provider value={{ token, login, logout }}>{children}</AuthContext.Provider>;
}

// --- API Helper ---
async function apiFetch(endpoint, token, options = {}) {
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (res.status === 401) throw new Error('Unauthorized');
  if (res.status === 204) return null;
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || 'API Request Failed');
  }
  return res.json();
}

// --- Protected Route ---
function ProtectedRoute({ children }) {
  const { token } = React.useContext(AuthContext);
  if (!token) return <Navigate to="/admin/login" />;
  return children;
}

// --- Layout ---
function AdminLayout({ children, title }) {
  const { logout } = React.useContext(AuthContext);
  const navigate = useNavigate();
  const loc = useLocation();

  const navItems = [
    { path: '/admin/dashboard',      icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/admin/conversations',  icon: MessageSquare,   label: 'Conversations' },
    { path: '/admin/tickets',        icon: Ticket,          label: 'Tickets' },
    { path: '/admin/knowledge-base', icon: FileText,        label: 'Knowledge Base' },
    { path: '/admin/llmops',         icon: Settings,        label: 'LLMOps' },
    { path: '/admin/quality',        icon: Award,           label: 'Quality' },
    { path: '/admin/users',          icon: Users,           label: 'Users' },
  ];

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-dot"></div>
          <span>Alfalah GPT</span>
          <small>Admin</small>
        </div>
        <nav className="sidebar-nav">
          {navItems.map(({ path, icon: Icon, label }) => (
            <a key={path} href="#"
              onClick={e => { e.preventDefault(); navigate(path); }}
              className={`nav-item ${loc.pathname === path ? 'active' : ''}`}>
              <Icon className="nav-icon" size={18} /> {label}
            </a>
          ))}
        </nav>
        <div className="sidebar-footer">
          <a href="#" onClick={e => { e.preventDefault(); logout(); }} className="logout-btn">
            <LogOut size={16} /> Sign out
          </a>
        </div>
      </aside>
      <main className="main-content">
        <header className="topbar">
          <h1 className="page-title">{title}</h1>
          <div className="topbar-user"><span className="user-badge">Admin</span></div>
        </header>
        <div className="content-body">{children}</div>
      </main>
    </div>
  );
}

// --- Reusable ---
function PageError({ msg }) {
  return msg ? <div className="alert alert-error">{msg}</div> : null;
}

function StatusBadge({ status }) {
  const colors = {
    open: '#e3f2fd:#1565c0',
    in_progress: '#fff8e1:#e65100',
    resolved: '#e8f5e9:#2e7d32',
    active: '#e8f5e9:#2e7d32',
    archived: '#f5f5f5:#666',
    ingested: '#e8f5e9:#2e7d32',
    uploaded_to_s3: '#e3f2fd:#1565c0',
    processing: '#fff8e1:#e65100',
    deleted: '#ffebee:#c62828',
    pending: '#fff8e1:#e65100',
    succeeded: '#e8f5e9:#2e7d32',
    failed: '#ffebee:#c62828',
  };
  const [bg, color] = (colors[status] || '#f5f5f5:#666').split(':');
  return (
    <span style={{ background: bg, color, padding: '2px 8px', borderRadius: 4, fontSize: 12, fontWeight: 600 }}>
      {status?.replace('_', ' ')}
    </span>
  );
}

// ─────────────────────────────────────────────
// Pages
// ─────────────────────────────────────────────

function Login() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = React.useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    const form = new FormData();
    form.append('username', username);
    form.append('password', password);
    try {
      const res = await fetch(`${API_BASE}/auth/token`, { method: 'POST', body: form });
      if (!res.ok) throw new Error('Invalid credentials');
      const data = await res.json();
      login(data.access_token);
      navigate('/admin/dashboard');
    } catch (err) { setError(err.message); }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo"><div className="brand-dot"></div><span>Alfalah GPT</span></div>
        <h2>Admin Sign In</h2>
        <p className="login-sub">Secure access to the LLMOps dashboard</p>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <label>Username</label>
            <input name="username" value={username} onChange={e => setUsername(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input name="password" type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="••••••••" />
          </div>
          <button type="submit" className="btn btn-primary btn-full">Sign In →</button>
        </form>
      </div>
    </div>
  );
}

function Dashboard() {
  const { token, logout } = React.useContext(AuthContext);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch('/admin/stats', token)
      .then(setStats)
      .catch(e => { if (e.message === 'Unauthorized') logout(); else setError(e.message); });
  }, [token, logout]);

  if (error) return <PageError msg={error} />;
  if (!stats) return <div className="empty-state">Loading stats...</div>;

  return (
    <>
      <div className="stats-grid">
        <div className="stat-card"><div className="stat-icon"><MessageSquare size={28}/></div><div className="stat-value">{stats.total_conversations}</div><div className="stat-label">Total Conversations</div></div>
        <div className="stat-card"><div className="stat-icon"><Ticket size={28}/></div><div className="stat-value">{stats.open_tickets}</div><div className="stat-label">Open Tickets</div></div>
        <div className="stat-card"><div className="stat-icon"><FileText size={28}/></div><div className="stat-value">{stats.total_documents}</div><div className="stat-label">KB Documents</div></div>
        <div className="stat-card"><div className="stat-icon"><Settings size={28}/></div><div className="stat-value" style={{fontSize:'1.1rem'}}>{stats.active_model}</div><div className="stat-label">Active Model</div></div>
      </div>
      <div className="card mt-6">
        <div className="card-header"><h3>Active System Prompt</h3></div>
        <div className="card-body"><pre className="prompt-preview">{stats.active_prompt}</pre></div>
      </div>
    </>
  );
}

function ConversationsPage() {
  const { token, logout } = React.useContext(AuthContext);
  const [convs, setConvs] = useState([]);
  const [selected, setSelected] = useState(null);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  const load = () => apiFetch('/conversations', token)
    .then(d => setConvs(d.conversations || []))
    .catch(e => { if (e.message === 'Unauthorized') logout(); else setError(e.message); });

  useEffect(() => { load(); }, [token]);

  const openTranscript = async (id) => {
    try {
      const d = await apiFetch(`/conversations/${id}`, token);
      setSelected(d.conversation);
      setMessages(d.messages || []);
    } catch (e) { setError(e.message); }
  };

  const archive = async (id) => {
    if (!confirm('Archive this conversation?')) return;
    try {
      await apiFetch(`/conversations/${id}`, token, { method: 'DELETE' });
      load();
      if (selected?.pk === id) setSelected(null);
    } catch (e) { setError(e.message); }
  };

  const filtered = convs.filter(c =>
    c.pk?.toLowerCase().includes(search.toLowerCase()) ||
    c.status?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <PageError msg={error} />
      <div style={{ display: 'flex', gap: '1.5rem' }}>
        <div className="card" style={{ flex: selected ? '0 0 55%' : '1' }}>
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Conversations ({filtered.length})</h3>
            <input className="search-input" placeholder="Search…" value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <div className="card-body" style={{ padding: 0 }}>
            {filtered.length === 0 ? <div className="empty-state">No conversations yet.</div> : (
              <table className="data-table">
                <thead><tr><th>ID</th><th>Status</th><th>Created</th><th></th></tr></thead>
                <tbody>
                  {filtered.map(c => (
                    <tr key={c.pk} style={{ cursor: 'pointer', background: selected?.pk === c.pk ? 'var(--bg)' : '' }}
                      onClick={() => openTranscript(c.pk)}>
                      <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{c.pk?.slice(0, 18)}…</td>
                      <td><StatusBadge status={c.status} /></td>
                      <td>{c.created_at ? new Date(c.created_at).toLocaleDateString() : '—'}</td>
                      <td onClick={e => { e.stopPropagation(); archive(c.pk); }}>
                        <button className="btn btn-danger btn-sm">Archive</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {selected && (
          <div className="card" style={{ flex: 1 }}>
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
              <h3>Transcript</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setSelected(null)}>✕ Close</button>
            </div>
            <div className="card-body chat-transcript" style={{ maxHeight: 480, overflowY: 'auto' }}>
              {messages.length === 0 ? <div className="empty-state">No messages.</div> :
                messages.map((m, i) => (
                  <div key={i} className={`transcript-msg transcript-${m.role === 'user' ? 'user' : 'assistant'}`}>
                    <span className="transcript-role">{m.role}</span>
                    <div
                      className="transcript-bubble"
                      dangerouslySetInnerHTML={{ __html: marked.parse(m.content || '') }}
                    />
                  </div>
                ))
              }
            </div>
          </div>
        )}
      </div>
    </>
  );
}

function TicketsPage() {
  const { token, logout } = React.useContext(AuthContext);
  const [tickets, setTickets] = useState([]);
  const [error, setError] = useState('');

  const load = () => apiFetch('/tickets', token)
    .then(d => setTickets(d.tickets || []))
    .catch(e => { if (e.message === 'Unauthorized') logout(); else setError(e.message); });

  useEffect(() => { load(); }, [token]);

  const updateStatus = async (id, status) => {
    try {
      await apiFetch(`/tickets/${id}`, token, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      load();
    } catch (e) { setError(e.message); }
  };

  return (
    <>
      <PageError msg={error} />
      <div className="card">
        <div className="card-header"><h3>Support Tickets ({tickets.length})</h3></div>
        <div className="card-body" style={{ padding: 0 }}>
          {tickets.length === 0 ? <div className="empty-state">No tickets yet.</div> : (
            <table className="data-table">
              <thead><tr><th>Ticket ID</th><th>Conversation</th><th>Status</th><th>Created</th><th>Update Status</th></tr></thead>
              <tbody>
                {tickets.map(t => (
                  <tr key={t.pk}>
                    <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{t.pk?.slice(0, 16)}…</td>
                    <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{t.conversation_id?.slice(0, 16) || '—'}…</td>
                    <td><StatusBadge status={t.status} /></td>
                    <td>{t.created_at ? new Date(t.created_at).toLocaleDateString() : '—'}</td>
                    <td>
                      <select
                        value={t.status}
                        onChange={e => updateStatus(t.pk, e.target.value)}
                        style={{ padding: '4px 8px', borderRadius: 4, border: '1px solid var(--border)', fontSize: 13 }}
                      >
                        <option value="open">Open</option>
                        <option value="in_progress">In Progress</option>
                        <option value="resolved">Resolved</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}

function KnowledgeBasePage() {
  const { token, logout } = React.useContext(AuthContext);
  const [docs, setDocs] = useState([]);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [formError, setFormError] = useState('');
  const [destination, setDestination] = useState('rag');
  const [fundName, setFundName] = useState('');
  const fileRef = useRef(null);

  const load = () => apiFetch('/documents', token)
    .then(d => setDocs(d.documents || []))
    .catch(e => { if (e.message === 'Unauthorized') logout(); else setError(e.message); });

  useEffect(() => { load(); }, [token]);

  const handleUpload = async (e) => {
    e.preventDefault();
    setFormError('');
    const files = Array.from(fileRef.current?.files || []);
    if (!files.length) { setFormError('Select at least one file.'); return; }

    setUploading(true);
    try {
      for (const file of files) {
        const form = new FormData();
        form.append('file', file);
        form.append('destination', destination);
        form.append('fund_name', fundName);
        await fetch(`${API_BASE}/documents/upload`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: form,
        }).then(async res => {
          if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(`${file.name}: ${d.detail || 'Upload failed'}`); }
          return res.json();
        });
      }
      setShowModal(false);
      setFundName('');
      if (fileRef.current) fileRef.current.value = '';
      load();
    } catch (err) { setFormError(err.message); }
    finally { setUploading(false); }
  };

  const deleteDoc = async (id) => {
    if (!confirm('Delete this document?')) return;
    try {
      await apiFetch(`/documents/${id}`, token, { method: 'DELETE' });
      load();
    } catch (e) { setError(e.message); }
  };

  const visible = docs.filter(d => d.status !== 'deleted');

  return (
    <>
      <PageError msg={error} />
      <div className="card">
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>Documents ({visible.length})</h3>
          <button className="btn btn-primary" onClick={() => { setShowModal(true); setFormError(''); }}>
            <Upload size={14} style={{ marginRight: 6 }} />Upload
          </button>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {visible.length === 0 ? <div className="empty-state">No documents uploaded yet.</div> : (
            <table className="data-table">
              <thead><tr><th>Filename</th><th>Destination</th><th>Fund</th><th>Status</th><th>Chunks</th><th>Uploaded</th><th></th></tr></thead>
              <tbody>
                {visible.map(d => (
                  <tr key={d.pk}>
                    <td>{d.filename}</td>
                    <td><StatusBadge status={d.destination} /></td>
                    <td>{d.fund_name || '—'}</td>
                    <td><StatusBadge status={d.status} /></td>
                    <td>{d.chunks_count ?? '—'}</td>
                    <td>{d.created_at ? new Date(d.created_at).toLocaleDateString() : '—'}</td>
                    <td><button className="btn btn-danger btn-sm" onClick={() => deleteDoc(d.pk)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <h3>Upload Document</h3>
            {formError && <div className="alert alert-error">{formError}</div>}
            <form onSubmit={handleUpload} className="login-form">
              <div className="form-group">
                <label>Files</label>
                <input type="file" ref={fileRef} accept=".pdf,.docx,.txt,.jsonl" multiple required />
              </div>
              <div className="form-group">
                <label>Destination</label>
                <select value={destination} onChange={e => setDestination(e.target.value)}
                  style={{ padding: '8px 12px', border: '1.5px solid var(--border)', borderRadius: 6, fontSize: 13 }}>
                  <option value="rag">RAG (Knowledge Base)</option>
                  <option value="finetune">Fine-Tuning (S3)</option>
                </select>
              </div>
              <div className="form-group">
                <label>Fund Name <small>(optional)</small></label>
                <input value={fundName} onChange={e => setFundName(e.target.value)} placeholder="e.g. Alfalah GHP Income Fund" />
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="submit" className="btn btn-primary" disabled={uploading}>
                  {uploading ? 'Uploading…' : 'Upload'}
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

function LLMOpsPage() {
  const { token, logout } = React.useContext(AuthContext);
  const [prompts, setPrompts] = useState([]);
  const [models, setModels] = useState([]);
  const [ftDocs, setFtDocs] = useState([]);
  const [error, setError] = useState('');
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [showFTModal, setShowFTModal] = useState(false);
  const [promptLabel, setPromptLabel] = useState('');
  const [promptContent, setPromptContent] = useState('');
  const [ftS3Keys, setFtS3Keys] = useState([]);
  const [ftSuffix, setFtSuffix] = useState('');
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadPrompts = () => apiFetch('/llmops/prompts', token).then(d => setPrompts(d.prompts || [])).catch(e => { if (e.message === 'Unauthorized') logout(); else setError(e.message); });
  const loadModels  = () => apiFetch('/llmops/models', token).then(d => setModels(d.models || [])).catch(e => setError(e.message));
  const loadFtDocs  = () => apiFetch('/documents/s3-jsonl', token).then(d => setFtDocs(d.files || [])).catch(() => {});

  useEffect(() => { loadPrompts(); loadModels(); loadFtDocs(); }, [token]);

  const createPrompt = async (e) => {
    e.preventDefault();
    setFormError(''); setSubmitting(true);
    try {
      await apiFetch('/llmops/prompts', token, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ label: promptLabel, content: promptContent }) });
      setShowPromptModal(false); setPromptLabel(''); setPromptContent('');
      loadPrompts();
    } catch (err) { setFormError(err.message); }
    finally { setSubmitting(false); }
  };

  const activatePrompt = async (pk) => {
    try { await apiFetch(`/llmops/prompts/${encodeURIComponent(pk)}/activate`, token, { method: 'PUT' }); loadPrompts(); }
    catch (e) { setError(e.message); }
  };

  const triggerFinetune = async (e) => {
    e.preventDefault();
    if (!ftS3Keys.length) { setFormError('Select at least one file.'); return; }
    setFormError(''); setSubmitting(true);
    try {
      await apiFetch('/llmops/finetune', token, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ s3_keys: ftS3Keys, suffix: ftSuffix }),
      });
      setShowFTModal(false); setFtS3Keys([]); setFtSuffix('');
      loadModels();
    } catch (err) { setFormError(err.message); }
    finally { setSubmitting(false); }
  };

  const refreshStatus = async (jobId) => {
    try { await apiFetch(`/llmops/finetune/${jobId}`, token); loadModels(); }
    catch (e) { setError(e.message); }
  };

  const activateModel = async (jobId) => {
    try { await apiFetch(`/llmops/models/${encodeURIComponent(jobId)}/activate`, token, { method: 'PUT' }); loadModels(); }
    catch (e) { setError(e.message); }
  };

  return (
    <>
      <PageError msg={error} />

      {/* Prompts */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>System Prompts</h3>
          <button className="btn btn-primary" onClick={() => { setShowPromptModal(true); setFormError(''); }}>+ New Prompt</button>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {prompts.length === 0 ? <div className="empty-state">No prompts yet.</div> : (
            <table className="data-table">
              <thead><tr><th>Label</th><th>Preview</th><th>Created</th><th></th></tr></thead>
              <tbody>
                {(() => {
                  const activePk = prompts.find(p => p.sk === 'ACTIVE_PROMPT')?.source_pk;
                  return prompts.filter(p => p.sk === 'PROMPT').map(p => (
                    <tr key={p.pk}>
                      <td>{p.label}</td>
                      <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12, color: 'var(--muted)' }}>{p.content}</td>
                      <td>{p.created_at ? new Date(p.created_at).toLocaleDateString() : '—'}</td>
                      <td>{p.pk === activePk
                        ? <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--success, #16a34a)' }}>✓ Active</span>
                        : <button className="btn btn-secondary btn-sm" onClick={() => activatePrompt(p.pk)}>Activate</button>}
                      </td>
                    </tr>
                  ));
                })()}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>Fine-Tuning Jobs</h3>
          <button className="btn btn-primary" onClick={() => { setShowFTModal(true); setFormError(''); }}>+ Fine-Tune</button>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {models.length === 0 ? <div className="empty-state">No fine-tuning jobs yet.</div> : (() => {
            const activeModelId = models.find(m => m.sk === 'ACTIVE_MODEL')?.openai_model_id;
            return (
              <table className="data-table">
                <thead><tr><th>Job ID</th><th>Training Files</th><th>Status</th><th>Model</th><th>Created</th><th></th></tr></thead>
                <tbody>
                  {models.filter(m => m.sk === 'FT_JOB').map(m => (
                    <tr key={m.pk}>
                      <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{m.pk?.slice(0, 20)}…</td>
                      <td style={{ fontSize: 12 }}>
                        {Array.isArray(m.s3_keys)
                          ? m.s3_keys.map(k => <div key={k}>{k}</div>)
                          : (m.s3_key || '—')}
                      </td>
                      <td><StatusBadge status={m.status} /></td>
                      <td style={{ fontSize: 12 }}>{m.openai_model_id || '—'}</td>
                      <td>{m.created_at ? new Date(m.created_at).toLocaleDateString() : '—'}</td>
                      <td style={{ display: 'flex', gap: 6 }}>
                        <button className="btn btn-secondary btn-sm" onClick={() => refreshStatus(m.pk)}><RefreshCw size={12} /></button>
                        {m.status === 'succeeded' && (
                          m.openai_model_id && m.openai_model_id === activeModelId
                            ? <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--success, #16a34a)' }}>✓ Active</span>
                            : <button className="btn btn-secondary btn-sm" onClick={() => activateModel(m.pk)}>Activate</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            );
          })()}
        </div>
      </div>

      {showPromptModal && (
        <div className="modal-overlay" onClick={() => setShowPromptModal(false)}>
          <div className="modal-card" style={{ maxWidth: 540 }} onClick={e => e.stopPropagation()}>
            <h3>New System Prompt</h3>
            {formError && <div className="alert alert-error">{formError}</div>}
            <form onSubmit={createPrompt} className="login-form">
              <div className="form-group"><label>Label</label><input value={promptLabel} onChange={e => setPromptLabel(e.target.value)} required autoFocus /></div>
              <div className="form-group">
                <label>Content</label>
                <textarea value={promptContent} onChange={e => setPromptContent(e.target.value)} required rows={6}
                  style={{ width: '100%', padding: '8px 12px', border: '1.5px solid var(--border)', borderRadius: 6, fontSize: 13, fontFamily: 'inherit', resize: 'vertical' }} />
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? 'Saving…' : 'Save Prompt'}</button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowPromptModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showFTModal && (
        <div className="modal-overlay" onClick={() => setShowFTModal(false)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <h3>Trigger Fine-Tuning</h3>
            {formError && <div className="alert alert-error">{formError}</div>}
            <form onSubmit={triggerFinetune} className="login-form">
              <div className="form-group">
                <label>Training Files <small>({ftS3Keys.length} selected)</small></label>
                {ftDocs.length === 0
                  ? <p style={{ fontSize: 13, color: 'var(--muted)', margin: '4px 0' }}>No JSONL files found in S3. Upload a JSONL file via the Knowledge Base tab first.</p>
                  : <div style={{ border: '1.5px solid var(--border)', borderRadius: 6, padding: '6px 4px', maxHeight: 200, overflowY: 'auto' }}>
                      {ftDocs.map(d => {
                        const checked = ftS3Keys.includes(d.s3_key);
                        return (
                          <label key={d.s3_key} style={{
                            display: 'flex', alignItems: 'center', gap: 10, padding: '7px 10px',
                            borderRadius: 5, cursor: 'pointer', fontSize: 13,
                            background: checked ? 'var(--primary-light, #e8f0fe)' : 'transparent',
                          }}>
                            <input
                              type="checkbox"
                              checked={checked}
                              onChange={() => setFtS3Keys(prev =>
                                checked ? prev.filter(k => k !== d.s3_key) : [...prev, d.s3_key]
                              )}
                              style={{ accentColor: 'var(--primary)', width: 15, height: 15 }}
                            />
                            <span style={{ fontWeight: checked ? 600 : 400 }}>{d.filename}</span>
                            <span style={{ color: 'var(--muted)', fontSize: 11, marginLeft: 'auto' }}>{d.s3_key}</span>
                          </label>
                        );
                      })}
                    </div>
                }
              </div>
              <div className="form-group"><label>Model Suffix <small>(optional)</small></label><input value={ftSuffix} onChange={e => setFtSuffix(e.target.value)} placeholder="e.g. alfalah-v2" /></div>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="submit" className="btn btn-primary" disabled={submitting || !ftS3Keys.length}>{submitting ? 'Starting…' : `Start Job (${ftS3Keys.length} file${ftS3Keys.length !== 1 ? 's' : ''})`}</button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowFTModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

function QualityPage() {
  const { token, logout } = React.useContext(AuthContext);
  const [ratings, setRatings] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    apiFetch('/admin/ratings', token)
      .then(d => setRatings(d.ratings || []))
      .catch(e => { if (e.message === 'Unauthorized') logout(); else setError(e.message); });
  }, [token]);

  const thumbsUp   = ratings.filter(r => r.rating === 1).length;
  const thumbsDown = ratings.filter(r => r.rating === -1).length;
  const total      = ratings.length;
  const score      = total ? Math.round((thumbsUp / total) * 100) : 0;

  return (
    <>
      <PageError msg={error} />
      <div className="stats-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: '1.5rem' }}>
        <div className="stat-card"><div className="stat-value">{thumbsUp}</div><div className="stat-label">👍 Positive</div></div>
        <div className="stat-card"><div className="stat-value">{thumbsDown}</div><div className="stat-label">👎 Negative</div></div>
        <div className="stat-card"><div className="stat-value">{score}%</div><div className="stat-label">Satisfaction Score</div></div>
      </div>
      <div className="card">
        <div className="card-header"><h3>Response Ratings ({total})</h3></div>
        <div className="card-body" style={{ padding: 0 }}>
          {ratings.length === 0 ? <div className="empty-state">No ratings yet.</div> : (
            <table className="data-table">
              <thead><tr><th>Rating</th><th>Conversation</th><th>Feedback</th><th>Date</th></tr></thead>
              <tbody>
                {[...ratings].sort((a, b) => b.created_at?.localeCompare(a.created_at || '') || 0).map((r, i) => (
                  <tr key={i}>
                    <td style={{ fontSize: 20 }}>{r.rating === 1 ? '👍' : '👎'}</td>
                    <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{r.pk?.replace('RATING#', '').slice(0, 18)}…</td>
                    <td style={{ color: 'var(--muted)', fontSize: 13 }}>{r.feedback || '—'}</td>
                    <td>{r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}

function UsersPage() {
  const { token, logout } = React.useContext(AuthContext);
  const [users, setUsers] = useState([]);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const load = () => apiFetch('/admin/users', token)
    .then(setUsers)
    .catch(e => { if (e.message === 'Unauthorized') logout(); else setError(e.message); });

  useEffect(() => { load(); }, [token]);

  const handleCreate = async (e) => {
    e.preventDefault(); setFormError(''); setSubmitting(true);
    try {
      await apiFetch('/admin/users', token, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: newUsername, password: newPassword }) });
      setShowModal(false); setNewUsername(''); setNewPassword(''); load();
    } catch (err) { setFormError(err.message); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async (username) => {
    if (!confirm(`Delete admin "${username}"?`)) return;
    try { await apiFetch(`/admin/users/${username}`, token, { method: 'DELETE' }); load(); }
    catch (err) { setError(err.message); }
  };

  return (
    <>
      <PageError msg={error} />
      <div className="card">
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>Admin Users</h3>
          <button className="btn btn-primary" onClick={() => { setShowModal(true); setFormError(''); }}>+ Add Admin</button>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {users.length === 0 ? <div className="empty-state">No users found.</div> : (
            <table className="data-table">
              <thead><tr><th>Username</th><th>Role</th><th>Created</th><th></th></tr></thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.username}>
                    <td>{u.username}</td>
                    <td><span className="user-badge">{u.role}</span></td>
                    <td>{u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
                    <td><button className="btn btn-danger btn-sm" onClick={() => handleDelete(u.username)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <h3>Add Admin User</h3>
            {formError && <div className="alert alert-error">{formError}</div>}
            <form onSubmit={handleCreate} className="login-form">
              <div className="form-group"><label>Username</label><input value={newUsername} onChange={e => setNewUsername(e.target.value)} required autoFocus /></div>
              <div className="form-group"><label>Password <small>(min 8 chars)</small></label><input type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required placeholder="••••••••" minLength={8} /></div>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
                <button type="submit" className="btn btn-primary" disabled={submitting}>{submitting ? 'Creating…' : 'Create Admin'}</button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

// ─────────────────────────────────────────────
// Landing Page
// ─────────────────────────────────────────────

function LandingPage() {
  return (
    <>
      <nav>
        <a href="/" className="nav-logo"><div className="nav-logo-dot"></div><span>Alfalah Investments</span></a>
        <ul>
          <li><a href="#">Funds</a></li>
          <li><a href="/admin/login" className="nav-admin">Admin Portal →</a></li>
        </ul>
      </nav>
      <section className="hero">
        <h1>Invest with <span>Confidence.</span><br/>Grow with Purpose.</h1>
        <p>Alfalah Investments offers a diverse range of Shariah-compliant and conventional mutual funds.</p>
        <div className="hero-cta"><a href="#funds" className="btn-primary">Explore Funds</a></div>
      </section>
      <div className="stats" style={{ display: 'flex', justifyContent: 'center', gap: '3rem', padding: '2.5rem', background: '#fff' }}>
        <div className="stat" style={{textAlign:'center'}}><div className="stat-value" style={{fontSize:'2rem',fontWeight:700,color:'#003057'}}>PKR 150B+</div><div className="stat-label">Assets Under Management</div></div>
        <div className="stat" style={{textAlign:'center'}}><div className="stat-value" style={{fontSize:'2rem',fontWeight:700,color:'#003057'}}>30+</div><div className="stat-label">Fund Products</div></div>
      </div>
    </>
  );
}

// ─────────────────────────────────────────────
// App
// ─────────────────────────────────────────────

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/admin/login" element={<Login />} />
          <Route path="/admin/dashboard"      element={<ProtectedRoute><AdminLayout title="Dashboard">     <Dashboard />        </AdminLayout></ProtectedRoute>} />
          <Route path="/admin/conversations"  element={<ProtectedRoute><AdminLayout title="Conversations"> <ConversationsPage /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/tickets"        element={<ProtectedRoute><AdminLayout title="Tickets">       <TicketsPage />       </AdminLayout></ProtectedRoute>} />
          <Route path="/admin/knowledge-base" element={<ProtectedRoute><AdminLayout title="Knowledge Base"><KnowledgeBasePage /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/llmops"         element={<ProtectedRoute><AdminLayout title="LLMOps">        <LLMOpsPage />        </AdminLayout></ProtectedRoute>} />
          <Route path="/admin/quality"        element={<ProtectedRoute><AdminLayout title="Quality">       <QualityPage />       </AdminLayout></ProtectedRoute>} />
          <Route path="/admin/users"          element={<ProtectedRoute><AdminLayout title="Users">         <UsersPage />         </AdminLayout></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}
