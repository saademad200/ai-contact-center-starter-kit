import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { MessageSquare, Ticket, FileText, Settings, Award, LogOut, LayoutDashboard } from 'lucide-react';
import './index.css';

const API_BASE = '/api/v1';

// --- Auth Context ---
const AuthContext = React.createContext(null);

function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('alf_admin_token'));

  const login = (newToken) => {
    localStorage.setItem('alf_admin_token', newToken);
    setToken(newToken);
  };

  const logout = () => {
    localStorage.removeItem('alf_admin_token');
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// --- API Helper ---
async function apiFetch(endpoint, token, options = {}) {
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
  if (res.status === 401) throw new Error("Unauthorized");
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "API Request Failed");
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
    { path: '/admin/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/admin/conversations', icon: MessageSquare, label: 'Conversations' },
    { path: '/admin/tickets', icon: Ticket, label: 'Tickets' },
    { path: '/admin/knowledge-base', icon: FileText, label: 'Knowledge Base' },
    { path: '/admin/llmops', icon: Settings, label: 'LLMOps' },
    { path: '/admin/quality', icon: Award, label: 'Quality' },
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
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <a
                key={item.path}
                href="#"
                onClick={(e) => { e.preventDefault(); navigate(item.path); }}
                className={`nav-item ${loc.pathname === item.path ? 'active' : ''}`}
              >
                <Icon className="nav-icon" size={18} /> {item.label}
              </a>
            );
          })}
        </nav>
        <div className="sidebar-footer">
          <a href="#" onClick={(e) => { e.preventDefault(); logout(); }} className="logout-btn">
            <LogOut size={16} /> Sign out
          </a>
        </div>
      </aside>
      <main className="main-content">
        <header className="topbar">
          <h1 className="page-title">{title}</h1>
          <div className="topbar-user"><span className="user-badge">Admin</span></div>
        </header>
        <div className="content-body">
          {children}
        </div>
      </main>
    </div>
  );
}

// --- Pages ---

function Login() {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = React.useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    try {
      const res = await fetch(`${API_BASE}/auth/token`, { method: 'POST', body: formData });
      if (!res.ok) throw new Error("Invalid credentials");
      const data = await res.json();
      login(data.access_token);
      navigate('/admin/dashboard');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <div className="brand-dot"></div>
          <span>Alfalah GPT</span>
        </div>
        <h2>Admin Sign In</h2>
        <p className="login-sub">Secure access to the LLMOps dashboard</p>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <label>Username</label>
            <input name="username" value={username} onChange={e=>setUsername(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input name="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} required placeholder="••••••••" />
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
      .catch(e => { if(e.message === 'Unauthorized') logout(); else setError(e.message); });
  }, [token, logout]);

  if (error) return <div className="alert alert-error">{error}</div>;
  if (!stats) return <div className="empty-state">Loading stats...</div>;

  return (
    <>
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon"><MessageSquare size={28}/></div>
          <div className="stat-value">{stats.total_conversations}</div>
          <div className="stat-label">Total Conversations</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Ticket size={28}/></div>
          <div className="stat-value">{stats.open_tickets}</div>
          <div className="stat-label">Open Tickets</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><FileText size={28}/></div>
          <div className="stat-value">{stats.total_documents}</div>
          <div className="stat-label">KB Documents</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon"><Settings size={28}/></div>
          <div className="stat-value" style={{fontSize: '1.2rem', lineHeight: '1.5rem'}}>{stats.active_model}</div>
          <div className="stat-label">Active Model</div>
        </div>
      </div>
      <div className="card mt-6">
        <div className="card-header">
          <h3>Active System Prompt</h3>
        </div>
        <div className="card-body">
          <pre className="prompt-preview">{stats.active_prompt}</pre>
        </div>
      </div>
    </>
  );
}

function LandingPage() {
  return (
    <>
      <nav>
        <a href="/" className="nav-logo">
          <div className="nav-logo-dot"></div>
          <span>Alfalah Investments</span>
        </a>
        <ul>
          <li><a href="#">Funds</a></li>
          <li><a href="/admin/login" className="nav-admin">Admin Portal →</a></li>
        </ul>
      </nav>
      <section className="hero">
        <h1>Invest with <span>Confidence.</span><br/>Grow with Purpose.</h1>
        <p>Alfalah Investments offers a diverse range of Shariah-compliant and conventional mutual funds.</p>
        <div className="hero-cta">
          <a href="#funds" className="btn-primary">Explore Funds</a>
        </div>
      </section>
      <div className="stats" style={{ display: 'flex', justifyContent: 'center', gap: '3rem', padding: '2.5rem', background: '#fff' }}>
        <div className="stat" style={{textAlign: 'center'}}><div className="stat-value" style={{fontSize: '2rem', fontWeight: 700, color: '#003057'}}>PKR 150B+</div><div className="stat-label">Assets Under Management</div></div>
        <div className="stat" style={{textAlign: 'center'}}><div className="stat-value" style={{fontSize: '2rem', fontWeight: 700, color: '#003057'}}>30+</div><div className="stat-label">Fund Products</div></div>
      </div>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/admin/login" element={<Login />} />
          <Route path="/admin/dashboard" element={<ProtectedRoute><AdminLayout title="Dashboard"><Dashboard /></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/conversations" element={<ProtectedRoute><AdminLayout title="Conversations"><div className="empty-state">Conversations UI...</div></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/tickets" element={<ProtectedRoute><AdminLayout title="Tickets"><div className="empty-state">Tickets UI...</div></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/knowledge-base" element={<ProtectedRoute><AdminLayout title="Knowledge Base"><div className="empty-state">KB UI...</div></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/llmops" element={<ProtectedRoute><AdminLayout title="LLMOps"><div className="empty-state">LLMOps UI...</div></AdminLayout></ProtectedRoute>} />
          <Route path="/admin/quality" element={<ProtectedRoute><AdminLayout title="Quality"><div className="empty-state">Quality UI...</div></AdminLayout></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}
