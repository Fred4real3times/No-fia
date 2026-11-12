import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { api, HttpError } from './api';

type User = { id: number; email: string; full_name: string };
type Workspace = { id: string; name: string; default_currency: string; timezone: string; role: string };
type Entity = { id: string; name: string; code: string; country_code: string; functional_currency: string; sector: string; status: string };
type Metric = { metric_key: string; label: string; value: string; currency: string; unit: string; period_start: string; period_end: string; entity_id: string | null; entity_ids: string[]; entity_names: string[]; entity_count: number; fact_count: number; last_collected_at: string; sources: {id: string; file: string; created_at: string}[]; coverage: string };
type Cockpit = { workspace_id: string; generated_at: string; metrics: Metric[]; latest_validated_import: {id: string; original_filename: string; report_type: string; validated_at: string}[]; open_actions: number; overdue_actions: number };
type Action = { id: string; entity: string | null; title: string; description: string; priority: string; status: string; created_by_name: string; assigned_to: number | null; assigned_to_name: string; due_at: string | null; completed_at: string | null; created_at: string };
type Alert = { id: string; entity_id: string | null; entity_name: string | null; rule_key: string; title: string; explanation: string; severity: string; status: string; evidence: Record<string, unknown>; triggered_at: string };
type ImportBatch = { id: string; entity: string; original_filename: string; sha256: string; size_bytes: number; report_type: string; period_start: string; period_end: string; currency: string; status: string; rows_seen: number; rows_staged: number; rows_rejected: number; created_at: string };
type Member = { id: number; user_id: number; email: string; full_name: string; role: string };
type Audit = { id: string; actor: string; action: string; target_type: string; target_id: string; metadata: Record<string, unknown>; created_at: string };
type ImportPreview = { batch_id: string; format: string; columns?: string[]; row_count?: number; sample?: Record<string, string>[]; suggested_mapping?: { amount?: string; date?: string }; metric_key?: string; can_stage: boolean; assisted?: boolean; text_preview?: string; message?: string; mapping_note?: string };
type Staged = { batch: ImportBatch; metric_label: string; rows_staged: number; rows_rejected: number; issues: {row_number: number; field_name: string; raw_value: string; message: string}[]; requires_confirmation: boolean };

type Screen = 'overview' | 'companies' | 'data' | 'actions' | 'analysis' | 'settings' | 'assistant';
const SCREEN_LABELS: Record<Screen, string> = {
  overview: 'Mon portefeuille', companies: 'Entreprises', data: 'Données & imports',
  actions: 'Centre d’actions', analysis: 'Analyse', assistant: 'Assistant IA', settings: 'Paramètres',
};
const REPORT_TYPES = [
  ['SALES', 'Chiffre d’affaires / ventes'], ['CASH', 'Encaissements'], ['BANK', 'Solde de trésorerie déclaré'],
  ['EXPENSES', 'Dépenses'], ['RECEIVABLES', 'Créances clients'], ['PAYABLES', 'Dettes fournisseurs'], ['OTHER', 'Autre rapport'],
];
const METRIC_ORDER = ['reported_revenue', 'reported_collections', 'reported_cash_balance', 'reported_expenses', 'reported_receivables', 'reported_payables'];

function formatNumber(value: string | number, currency?: string) {
  const raw = String(value).trim();
  const match = raw.match(/^(-?)(\d+)(?:[.,](\d+))?$/);
  if (!match) return '—';
  // Monetary values can exceed the 53-bit integer precision of Number.
  // Round the displayed whole amount with BigInt; the API keeps Decimal precision.
  let whole = BigInt(match[2]);
  if (match[3] && Number(match[3][0]) >= 5) whole += 1n;
  const formatted = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(whole);
  return `${match[1]}${formatted}${currency ? ` ${currency}` : ''}`;
}
function localDateInputValue(date: Date) {
  const pad = (part: number) => String(part).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}
function shortDate(dateValue?: string | null) {
  if (!dateValue) return '—';
  const date = new Date(dateValue);
  return Number.isNaN(date.getTime()) ? dateValue : new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium' }).format(date);
}
function dateTime(dateValue?: string | null) {
  if (!dateValue) return '—';
  const date = new Date(dateValue);
  return Number.isNaN(date.getTime()) ? dateValue : new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
}
function errorMessage(error: unknown) {
  if (error instanceof HttpError) {
    const payload = error.payload;
    const values = Object.values(payload).flatMap(v => Array.isArray(v) ? v : [v]);
    return values.map(value => typeof value === 'string' ? value : '').filter(Boolean).join(' ') || error.message;
  }
  return error instanceof Error ? error.message : 'Une erreur inattendue est survenue.';
}

function Icon({ name, size = 18 }: { name: string; size?: number }) {
  const common = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, 'aria-hidden': true as const };
  const paths: Record<string, ReactNode> = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></>,
    building: <><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M9 7h2m2 0h2M9 11h2m2 0h2M9 15h2m2 0h2M10 21v-3h4v3"/></>,
    file: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8m-8 4h8"/></>,
    check: <><path d="m5 12 4 4L19 6"/></>,
    chart: <><path d="M3 3v18h18"/><path d="m7 14 4-4 4 3 5-7"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="m19.4 15 .1.1 1.4 1.1-1.4 2.4-1.7-.6a8 8 0 0 1-1.5.9l-.3 1.8h-2.8l-.3-1.8a8 8 0 0 1-1.5-.9l-1.7.6-1.4-2.4 1.4-1.1a8 8 0 0 1 0-1.8l-1.4-1.1 1.4-2.4 1.7.6a8 8 0 0 1 1.5-.9l.3-1.8h2.8l.3 1.8a8 8 0 0 1 1.5.9l1.7-.6 1.4 2.4-1.4 1.1a8 8 0 0 1 0 1.7Z"/></>,
    spark: <><path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3Z"/><path d="m19 16 .8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8L19 16Z"/></>,
    plus: <><path d="M12 5v14M5 12h14"/></>,
    arrow: <><path d="M5 12h14m-6-6 6 6-6 6"/></>,
    bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></>,
    search: <><circle cx="10.8" cy="10.8" r="6.8"/><path d="m16 16 5 5"/></>,
    logout: <><path d="M10 17l5-5-5-5m5 5H3"/><path d="M12 3h7a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-7"/></>,
    menu: <><path d="M4 6h16M4 12h16M4 18h16"/></>,
    close: <><path d="m6 6 12 12M18 6 6 18"/></>,
    download: <><path d="M12 3v12m-5-5 5 5 5-5M4 20h16"/></>,
    clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    shield: <><path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z"/><path d="m9 12 2 2 4-4"/></>,
  };
  return <svg {...common}>{paths[name] || paths.grid}</svg>;
}

export default function App() {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem('yfen_token'));
  const [user, setUser] = useState<User | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [screen, setScreen] = useState<Screen>('overview');
  const [loading, setLoading] = useState(false);
  const [booting, setBooting] = useState(Boolean(token));
  const [toast, setToast] = useState('');
  const [error, setError] = useState('');
  const [mobileNav, setMobileNav] = useState(false);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [cockpit, setCockpit] = useState<Cockpit | null>(null);
  const [actions, setActions] = useState<Action[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [imports, setImports] = useState<ImportBatch[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [audit, setAudit] = useState<Audit[]>([]);

  const notify = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(''), 3200);
  }, []);

  const logout = useCallback(async () => {
    if (token) {
      try { await api('/auth/logout/', token, { method: 'POST', body: {} }); } catch { /* token may already be invalid */ }
    }
    sessionStorage.removeItem('yfen_token');
    sessionStorage.removeItem('yfen_workspace');
    setToken(null); setUser(null); setWorkspace(null); setWorkspaces([]);
    setEntities([]); setCockpit(null); setActions([]); setAlerts([]); setImports([]); setMembers([]); setAudit([]);
  }, [token]);

  const bootstrap = useCallback(async (currentToken: string) => {
    setBooting(true);
    try {
      const [me, list] = await Promise.all([
        api<User>('/auth/me/', currentToken), api<Workspace[]>('/workspaces/', currentToken),
      ]);
      setUser(me);
      setWorkspaces(list);
      const savedId = sessionStorage.getItem('yfen_workspace');
      setWorkspace(list.find(item => item.id === savedId) || list[0] || null);
    } catch (e) {
      sessionStorage.removeItem('yfen_token');
      setToken(null);
      setError(errorMessage(e));
    } finally { setBooting(false); }
  }, []);

  useEffect(() => { if (token) void bootstrap(token); }, [token, bootstrap]);

  const refreshWorkspaceData = useCallback(async () => {
    if (!token || !workspace) return;
    setLoading(true); setError('');
    try {
      const query = `?workspace_id=${encodeURIComponent(workspace.id)}`;
      const [entityRows, cockpitData, actionRows, alertRows, importRows] = await Promise.all([
        api<Entity[]>(`/entities/${query}`, token),
        api<Cockpit>(`/cockpit/${query}`, token),
        api<Action[]>(`/actions/${query}`, token),
        api<Alert[]>(`/alerts/${query}&evaluate=true`, token),
        api<ImportBatch[]>(`/imports/${query}`, token),
      ]);
      setEntities(entityRows); setCockpit(cockpitData); setActions(actionRows); setAlerts(alertRows); setImports(importRows);
      try { setMembers(await api<Member[]>(`/members/${query}`, token)); } catch { setMembers([]); }
      if (['settings'].includes(screen)) {
        try { setAudit(await api<Audit[]>(`/audit/${query}`, token)); } catch { setAudit([]); }
      }
    } catch (e) { setError(errorMessage(e)); }
    finally { setLoading(false); }
  }, [token, workspace, screen]);

  useEffect(() => { void refreshWorkspaceData(); }, [refreshWorkspaceData]);

  const onAuthenticated = (result: { token: string; user: User }) => {
    setBooting(true);
    sessionStorage.setItem('yfen_token', result.token);
    setUser(result.user); setToken(result.token); setError('');
  };
  const changeWorkspace = (id: string) => {
    const target = workspaces.find(item => item.id === id) || null;
    sessionStorage.setItem('yfen_workspace', id);
    setWorkspace(target);
  };
  const showScreen = (target: Screen) => { setScreen(target); setMobileNav(false); setError(''); };

  if (!token) return <AuthPage onAuthenticated={onAuthenticated} />;
  if (booting || !user) return <div className="boot-screen"><Brand /><div className="spinner" /><span>Initialisation de votre espace sécurisé…</span></div>;
  if (!workspaces.length) return <WorkspaceOnboarding token={token} user={user} onCreated={async () => {
    const list = await api<Workspace[]>('/workspaces/', token); setWorkspaces(list); setWorkspace(list[0] || null);
  }} onLogout={logout} />;

  const nav: { key: Screen; label: string; icon: string; soon?: boolean }[] = [
    { key: 'overview', label: 'Mon portefeuille', icon: 'grid' },
    { key: 'companies', label: 'Entreprises', icon: 'building' },
    { key: 'data', label: 'Données & imports', icon: 'file' },
    { key: 'actions', label: 'Actions', icon: 'check' },
    { key: 'analysis', label: 'Analyse', icon: 'chart' },
    { key: 'assistant', label: 'Assistant IA', icon: 'spark', soon: true },
  ];

  return <div className="app-shell">
    <aside className={`sidebar ${mobileNav ? 'mobile-open' : ''}`}>
      <div className="sidebar-brand"><Brand /><button className="icon-btn mobile-close" onClick={() => setMobileNav(false)} aria-label="Fermer"><Icon name="close" /></button></div>
      <div className="workspace-select-wrap">
        <label className="eyebrow">ESPACE ACTIF</label>
        <select className="workspace-select" value={workspace?.id || ''} onChange={e => changeWorkspace(e.target.value)}>
          {workspaces.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
        <span className="role-tag">{workspace?.role || 'MEMBRE'}</span>
      </div>
      <div className="sidebar-section-label">PILOTAGE</div>
      <nav className="side-nav">
        {nav.map(item => <button key={item.key} className={`nav-link ${screen === item.key ? 'active' : ''} ${item.soon ? 'locked' : ''}`} onClick={() => showScreen(item.key)}>
          <Icon name={item.icon} size={18} /><span>{item.label}</span>{item.soon && <small>P1</small>}
        </button>)}
      </nav>
      <div className="sidebar-spacer" />
      <button className={`nav-link ${screen === 'settings' ? 'active' : ''}`} onClick={() => showScreen('settings')}><Icon name="settings" /><span>Paramètres & accès</span></button>
      <div className="sidebar-user">
        <div className="user-avatar">{(user.full_name || user.email).slice(0, 1).toUpperCase()}</div>
        <div className="user-meta"><b>{user.full_name || 'Utilisateur YFEN'}</b><span>{user.email}</span></div>
        <button className="icon-btn quiet" onClick={() => void logout()} aria-label="Déconnexion" title="Déconnexion"><Icon name="logout" size={17} /></button>
      </div>
      <div className="sidebar-foot"><span className="status-dot" /> Données privées · accès contrôlé</div>
    </aside>
    {mobileNav && <button className="nav-overlay" aria-label="Fermer la navigation" onClick={() => setMobileNav(false)} />}
    <main className="main-area">
      <header className="topbar">
        <div className="topbar-left">
          <button className="icon-btn menu-trigger" onClick={() => setMobileNav(true)} aria-label="Ouvrir le menu"><Icon name="menu" /></button>
          <div><div className="breadcrumb">YFEN <span>/</span> {SCREEN_LABELS[screen]}</div><div className="topbar-sub">{workspace?.name || 'Votre espace de pilotage'}</div></div>
        </div>
        <div className="topbar-right"><span className="network-pill"><span className="status-dot" /> Connecté</span><button className="icon-btn" onClick={() => void refreshWorkspaceData()} title="Actualiser" aria-label="Actualiser"><Icon name="clock" /></button><div className="topbar-avatar">{(user.full_name || user.email).slice(0,1).toUpperCase()}</div></div>
      </header>
      <div className="page-content">
        {error && <div className="alert-banner error-banner"><span>{error}</span><button onClick={() => setError('')}>Fermer</button></div>}
        {loading && <div className="loading-line"><span /> Synchronisation des données autorisées…</div>}
        {screen === 'overview' && <OverviewScreen workspace={workspace!} entities={entities} cockpit={cockpit} actions={actions} alerts={alerts} imports={imports} onNavigate={showScreen} token={token} onRefresh={refreshWorkspaceData} onToast={notify} />}
        {screen === 'companies' && <CompaniesScreen token={token} workspace={workspace!} entities={entities} onRefresh={refreshWorkspaceData} onToast={notify} />}
        {screen === 'data' && <DataScreen token={token} workspace={workspace!} entities={entities} imports={imports} onRefresh={refreshWorkspaceData} onToast={notify} />}
        {screen === 'actions' && <ActionsScreen token={token} workspace={workspace!} entities={entities} actions={actions} members={members} onRefresh={refreshWorkspaceData} onToast={notify} />}
        {screen === 'analysis' && <AnalysisScreen cockpit={cockpit} entities={entities} />}
        {screen === 'assistant' && <AssistantScreen />}
        {screen === 'settings' && <SettingsScreen token={token} workspace={workspace!} user={user} members={members} audit={audit} onRefresh={refreshWorkspaceData} onToast={notify} onLogout={logout} />}
      </div>
      <footer className="main-footer"><span>YFEN · AI BUSINESS CONTROL TOWER</span><span>Les montants présentés proviennent de rapports importés et validés — pas de flux bancaire temps réel.</span></footer>
    </main>
    {toast && <div className="toast"><Icon name="check" size={16} />{toast}</div>}
    <nav className="mobile-bottom-nav">
      {(['overview', 'companies', 'data', 'actions', 'settings'] as Screen[]).map(key => <button key={key} className={screen === key ? 'active' : ''} onClick={() => showScreen(key)}><Icon name={({overview:'grid',companies:'building',data:'file',actions:'check',settings:'settings'} as Record<string,string>)[key]} size={18} /><span>{({overview:'Accueil',companies:'Sociétés',data:'Données',actions:'Actions',settings:'Profil'} as Record<string,string>)[key]}</span></button>)}
    </nav>
  </div>;
}

function Brand() {
  return <div className="brand-lockup"><div className="brand-mark"><svg viewBox="0 0 28 28" width="25" height="25" fill="none" stroke="#04150d" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 20 11 12l5 5 8-10"/><path d="M18 7h6v6"/></svg></div><div className="brand-word"><strong>YFEN</strong><span>CONTROL TOWER</span></div></div>;
}

function AuthPage({ onAuthenticated }: { onAuthenticated: (result: {token: string; user: User}) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [fullName, setFullName] = useState('');
  const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError('');
    try {
      const result = await api<{token: string; user: User}>(`/auth/${mode === 'login' ? 'login' : 'register'}/`, null,
        { method: 'POST', body: { email, password, full_name: fullName } });
      onAuthenticated(result);
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  };
  return <div className="auth-page">
    <div className="auth-visual"><div className="ambient ambient-one"/><div className="ambient ambient-two"/><div className="auth-visual-content"><Brand /><div className="auth-headline"><span className="overline">PILOTAGE EXÉCUTIF · AFRIQUE FRANCOPHONE</span><h1>Voyez clair.<br/><em>Décidez juste.</em><br/>Agissez à temps.</h1><p>Le cockpit qui rassemble les données de vos activités, met les écarts en évidence et transforme les priorités en actions suivies.</p></div><div className="visual-card"><div className="visual-card-top"><span>VUE PORTEFEUILLE</span><span className="visual-dot"/> <small>DONNÉES DE DÉMO</small></div><div className="visual-metric"><b>3</b><span>activités suivies</span></div><div className="visual-bars"><i style={{height:'42%'}}/><i style={{height:'77%'}}/><i style={{height:'56%'}}/><i style={{height:'92%'}}/><i style={{height:'64%'}}/><i style={{height:'84%'}}/><i style={{height:'49%'}}/></div><div className="visual-card-foot"><span>Provenance visible</span><span>Actions traçables</span><span>Multi-entités</span></div></div></div><div className="auth-visual-foot">Une couche de pilotage au-dessus de vos outils existants. Pas un ERP de plus.</div></div>
    <div className="auth-panel"><div className="auth-panel-inner"><div className="auth-panel-brand"><Brand /></div><span className="eyebrow">ESPACE DE PILOTAGE</span><h2>{mode === 'login' ? 'Heureux de vous revoir.' : 'Créez votre accès YFEN.'}</h2><p className="muted">{mode === 'login' ? 'Connectez-vous pour retrouver votre portefeuille.' : 'Créez un compte administrateur pour démarrer votre espace.'}</p>
      <div className="auth-switch"><button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Connexion</button><button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>Créer un compte</button></div>
      <form onSubmit={submit} className="form-stack">{mode === 'register' && <label>Nom complet<input value={fullName} onChange={e => setFullName(e.target.value)} autoComplete="name" placeholder="Votre nom" required /></label>}<label>Adresse e-mail<input type="email" value={email} onChange={e => setEmail(e.target.value)} autoComplete="email" placeholder="vous@entreprise.com" required /></label><label>Mot de passe<input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} placeholder={mode === 'login' ? 'Votre mot de passe' : '12 caractères minimum'} minLength={mode === 'register' ? 12 : 1} required /></label>
        {error && <div className="form-error">{error}</div>}<button className="btn btn-primary full" disabled={busy}>{busy ? 'Veuillez patienter…' : mode === 'login' ? 'Accéder à mon espace' : 'Créer mon compte'}<Icon name="arrow" size={17}/></button></form>
      <div className="auth-assurance"><Icon name="shield" size={16}/><span>Accès authentifié. Les données financières ne sont pas exposées dans les caches hors ligne.</span></div>
      <div className="auth-legal">En continuant, vous acceptez les règles d’utilisation de votre organisation. Les conditions et mentions légales seront validées avant le pilote commercial.</div>
    </div></div>
  </div>;
}

function WorkspaceOnboarding({ token, user, onCreated, onLogout }: {token: string; user: User; onCreated: () => Promise<void>; onLogout: () => Promise<void>}) {
  const [name, setName] = useState(''); const [currency, setCurrency] = useState('XAF'); const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true); setError('');
    try { await api('/workspaces/', token, {method:'POST', body:{name, default_currency:currency, timezone:'Africa/Douala'}}); await onCreated(); }
    catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  };
  return <div className="onboarding-wrap"><div className="onboarding-card"><Brand /><span className="eyebrow">BIENVENUE {user.full_name.toUpperCase()}</span><h1>Créons votre premier espace de pilotage.</h1><p>Un espace regroupe les entreprises, les rapports, les indicateurs et les actions que votre équipe est autorisée à consulter.</p><form onSubmit={submit} className="form-stack"><label>Nom de l’espace<input value={name} onChange={e => setName(e.target.value)} placeholder="Ex. Groupe Atlantique" required maxLength={160}/></label><label>Devise par défaut<select value={currency} onChange={e => setCurrency(e.target.value)}><option value="XAF">XAF — Franc CFA BEAC</option><option value="XOF">XOF — Franc CFA BCEAO</option><option value="EUR">EUR — Euro</option><option value="USD">USD — Dollar US</option></select></label>{error && <div className="form-error">{error}</div>}<button className="btn btn-primary full" disabled={busy}>{busy ? 'Création…' : 'Créer mon espace'}<Icon name="arrow"/></button></form><button className="text-button" onClick={() => void onLogout()}>Se déconnecter</button></div></div>;
}

function PageHeading({ kicker, title, description, action }: {kicker: string; title: string; description: string; action?: React.ReactNode}) {
  return <div className="page-heading"><div><div className="eyebrow">{kicker}</div><h1>{title}</h1><p>{description}</p></div>{action && <div className="page-heading-action">{action}</div>}</div>;
}
function StatCard({ icon, label, value, note, tone = 'mint' }: {icon: string; label: string; value: string | number; note: string; tone?: string}) {
  return <div className="stat-card"><div className={`stat-icon ${tone}`}><Icon name={icon} size={19}/></div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-note">{note}</div></div>;
}
function MetricCard({ metric, entityName }: {metric: Metric; entityName: string}) {
  return <div className="metric-card"><div className="metric-top"><span className="eyebrow">{metric.label}</span><span className="metric-trace"><Icon name="shield" size={13}/> Vérifié</span></div><div className="metric-value">{formatNumber(metric.value, metric.currency || undefined)}</div><div className="metric-meta"><span>{entityName}</span><span>{shortDate(metric.period_start)} – {shortDate(metric.period_end)}</span></div><div className="metric-source"><Icon name="file" size={13}/><span>{metric.sources.length} source(s) · {metric.fact_count} ligne(s) agrégée(s)</span></div></div>;
}

function OverviewScreen({ workspace, entities, cockpit, actions, alerts, imports, onNavigate, token, onRefresh, onToast }: {
  workspace: Workspace; entities: Entity[]; cockpit: Cockpit | null; actions: Action[]; alerts: Alert[]; imports: ImportBatch[];
  onNavigate: (screen: Screen) => void; token: string; onRefresh: () => Promise<void>; onToast: (message: string) => void;
}) {
  const metricRows = cockpit?.metrics || [];
  const overdue = actions.filter(action => action.due_at && new Date(action.due_at) < new Date() && !['DONE','CANCELLED'].includes(action.status));
  const topMetrics = metricRows.filter(metric => METRIC_ORDER.includes(metric.metric_key)).slice(0, 6);
  return <>
    <PageHeading kicker="VUE EXÉCUTIVE · AUJOURD’HUI" title={`Bonjour, ${workspace.name}`} description="Votre portefeuille en un regard. Les indicateurs affichés sont issus d’imports validés et restent reliés à leurs sources." action={<button className="btn btn-secondary" onClick={() => void onRefresh()}><Icon name="clock"/> Actualiser les données</button>} />
    <div className="summary-strip"><div><span className="status-dot"/><b>Cockpit généré</b><span>{dateTime(cockpit?.generated_at)}</span></div><div><b>Devise de référence</b><span>{workspace.default_currency} · valeurs par devise conservées</span></div><div><b>Entités suivies</b><span>{entities.length} entité(s)</span></div></div>
    <div className="stats-grid"><StatCard icon="building" label="ENTITÉS ACTIVES" value={entities.filter(entity => entity.status === 'ACTIVE').length} note="Entreprises et activités"/><StatCard icon="file" label="IMPORTS VALIDÉS" value={imports.filter(item => item.status === 'VALIDATED').length} note="Lots publiés dans les indicateurs" tone="blue"/><StatCard icon="check" label="ACTIONS OUVERTES" value={cockpit?.open_actions ?? actions.filter(a => !['DONE','CANCELLED'].includes(a.status)).length} note={`${overdue.length} échue(s) à traiter`} tone="violet"/><StatCard icon="bell" label="ALERTES OUVERTES" value={alerts.filter(a => a.status === 'OPEN').length} note="Règles explicables" tone="coral"/></div>
    <div className="section-head"><div><h2>Indicateurs prioritaires</h2><p>Chaque valeur conserve sa période, sa devise et sa provenance.</p></div><button className="text-link" onClick={() => onNavigate('analysis')}>Voir l’analyse <Icon name="arrow" size={14}/></button></div>
    {topMetrics.length ? <div className="metrics-grid">{topMetrics.map((metric, i) => <MetricCard key={`${metric.metric_key}-${metric.entity_ids.join(',')}-${metric.currency}-${metric.period_start}-${i}`} metric={metric} entityName={metric.entity_count > 1 ? `${metric.entity_count} entités · somme du portefeuille` : (metric.entity_names[0] || entities.find(e => e.id === metric.entity_id)?.name || 'Entité')}/>)}</div> : <EmptyState icon="chart" title="Aucun indicateur publié pour le moment" text="Ajoutez une entreprise, importez un rapport CSV/XLSX, vérifiez les colonnes puis confirmez le lot. Les données restent exclues du cockpit tant qu’elles ne sont pas validées." action={<button className="btn btn-primary" onClick={() => onNavigate(entities.length ? 'data' : 'companies')}>{entities.length ? 'Importer un rapport' : 'Ajouter une entreprise'}<Icon name="arrow"/></button>} />}
    <div className="two-col-section"><section className="panel"><div className="panel-head"><div><h3>À surveiller</h3><p>Exceptions générées par des règles déterministes</p></div><span className="count-badge">{alerts.filter(a => a.status === 'OPEN').length}</span></div>{alerts.filter(a => a.status === 'OPEN').length ? <div className="alert-list">{alerts.filter(a => a.status === 'OPEN').slice(0,4).map(alert => <div key={alert.id} className="alert-row"><span className={`severity ${alert.severity.toLowerCase()}`}/><div><b>{alert.title}</b><p>{alert.explanation}</p><small>{alert.entity_name || 'Portefeuille'} · {dateTime(alert.triggered_at)}</small></div><button className="small-action" onClick={async () => { try { await api(`/alerts/${alert.id}/acknowledge/?workspace_id=${workspace.id}`, token, {method:'POST', body:{workspace_id:workspace.id}}); await onRefresh(); onToast('Alerte prise en compte'); } catch(e) { onToast(errorMessage(e)); } }}>Prendre en compte</button></div>)}</div> : <div className="empty-inline"><Icon name="check"/>Aucune alerte ouverte détectée.</div>}</section>
      <section className="panel"><div className="panel-head"><div><h3>Actions prioritaires</h3><p>Responsable et échéance visibles</p></div><button className="text-link" onClick={() => onNavigate('actions')}>Tout voir <Icon name="arrow" size={13}/></button></div>{actions.filter(a => !['DONE','CANCELLED'].includes(a.status)).slice(0,4).length ? <div className="action-list compact">{actions.filter(a => !['DONE','CANCELLED'].includes(a.status)).slice(0,4).map(action => <ActionRow key={action.id} action={action}/>)}</div> : <div className="empty-inline">Aucune action en attente. Créez une action à partir d’un écart ou d’une priorité.</div>}</section></div>
    <div className="section-head"><div><h2>Couverture des données</h2><p>La date de réception ne signifie pas disponibilité temps réel.</p></div><button className="text-link" onClick={() => onNavigate('data')}>Historique des imports <Icon name="arrow" size={14}/></button></div>
    <div className="coverage-row"><div className="coverage-icon"><Icon name="file"/></div><div className="coverage-content"><b>{cockpit?.latest_validated_import?.[0]?.original_filename || 'Aucun import validé'}</b><span>{cockpit?.latest_validated_import?.[0] ? `Dernier rapport validé le ${dateTime(cockpit.latest_validated_import[0].validated_at)}` : 'Les indicateurs restent vides jusqu’à la validation d’un premier rapport.'}</span></div><span className={`status-pill ${cockpit?.latest_validated_import?.length ? 'success' : 'neutral'}`}>{cockpit?.latest_validated_import?.length ? 'Source validée' : 'En attente'}</span></div>
  </>;
}

function EmptyState({ icon, title, text, action }: {icon: string; title: string; text: string; action?: React.ReactNode}) {
  return <div className="empty-state"><div className="empty-state-icon"><Icon name={icon} size={25}/></div><h3>{title}</h3><p>{text}</p>{action}</div>;
}
function ActionRow({ action }: {action: Action}) {
  return <div className="action-row"><span className={`priority-mark ${action.priority.toLowerCase()}`}/><div className="action-row-main"><b>{action.title}</b><span>{action.assigned_to_name || 'Non assignée'} · {action.due_at ? shortDate(action.due_at) : 'Sans échéance'}</span></div><span className={`status-pill ${action.status.toLowerCase()}`}>{statusLabel(action.status)}</span></div>;
}
function statusLabel(status: string) {
  const labels: Record<string,string> = {OPEN:'À faire', IN_PROGRESS:'En cours', BLOCKED:'Bloquée', DONE:'Terminée', CANCELLED:'Annulée', QUARANTINED:'Quarantaine', REVIEW:'À vérifier', VALIDATED:'Validé', FAILED:'Échec', CANCELLED:'Annulé'};
  return labels[status] || status;
}

function CompaniesScreen({ token, workspace, entities, onRefresh, onToast }: {token: string; workspace: Workspace; entities: Entity[]; onRefresh: () => Promise<void>; onToast: (message: string) => void}) {
  const [showForm,setShowForm]=useState(false); const [name,setName]=useState(''); const [code,setCode]=useState(''); const [currency,setCurrency]=useState(workspace.default_currency); const [sector,setSector]=useState('Commerce / Distribution'); const [busy,setBusy]=useState(false);
  const [unitEntity,setUnitEntity]=useState(''); const [unitName,setUnitName]=useState(''); const [unitCode,setUnitCode]=useState('');
  const submit = async (event: FormEvent) => { event.preventDefault(); setBusy(true); try { await api(`/entities/?workspace_id=${workspace.id}`,token,{method:'POST',body:{name,code:code.toUpperCase(),functional_currency:currency,sector,country_code:'CM',timezone:'Africa/Douala'}}); setName('');setCode('');setShowForm(false);await onRefresh();onToast('Entreprise ajoutée au portefeuille'); } catch(e){onToast(errorMessage(e));} finally{setBusy(false);} };
  const addUnit = async (event: FormEvent) => { event.preventDefault(); try { await api(`/business-units/?workspace_id=${workspace.id}`,token,{method:'POST',body:{entity:unitEntity,name:unitName,code:unitCode.toUpperCase(),unit_type:'LOCATION'}}); setUnitName('');setUnitCode('');await onRefresh();onToast('Établissement ajouté'); } catch(e){onToast(errorMessage(e));} };
  return <><PageHeading kicker="PORTEFEUILLE" title="Entreprises & activités" description="Organisez le groupe par entité légale, établissement ou unité opérationnelle." action={<button className="btn btn-primary" onClick={()=>setShowForm(v=>!v)}><Icon name="plus"/> Ajouter une entreprise</button>}/>
    {showForm && <section className="panel form-panel"><div className="panel-head"><div><h3>Nouvelle entreprise</h3><p>Les données de chaque entité restent isolées dans son espace autorisé.</p></div><button className="icon-btn" onClick={()=>setShowForm(false)}><Icon name="close"/></button></div><form className="form-grid" onSubmit={submit}><label>Raison sociale<input value={name} onChange={e=>setName(e.target.value)} required maxLength={180} placeholder="Ex. Distribution Cameroun SARL"/></label><label>Code interne<input value={code} onChange={e=>setCode(e.target.value)} required maxLength={40} placeholder="Ex. DIST-CM"/></label><label>Devise fonctionnelle<select value={currency} onChange={e=>setCurrency(e.target.value)}><option>XAF</option><option>XOF</option><option>EUR</option><option>USD</option></select></label><label>Secteur<select value={sector} onChange={e=>setSector(e.target.value)}><option>Commerce / Distribution</option><option>Services B2B</option><option>Industrie</option><option>Transport / Logistique</option><option>Autre</option></select></label><div className="form-actions"><button className="btn btn-primary" disabled={busy}>{busy?'Enregistrement…':'Créer l’entreprise'}</button></div></form></section>}
    {entities.length ? <div className="entity-grid">{entities.map(entity=><article className="entity-card" key={entity.id}><div className="entity-card-top"><div className="entity-logo"><Icon name="building" size={22}/></div><span className={`status-pill ${entity.status==='ACTIVE'?'success':'neutral'}`}>{entity.status==='ACTIVE'?'Active':'Archivée'}</span></div><h3>{entity.name}</h3><div className="entity-code">{entity.code}</div><div className="entity-meta"><span><b>Pays</b> Cameroun</span><span><b>Devise</b> {entity.functional_currency}</span><span><b>Secteur</b> {entity.sector || 'Non renseigné'}</span></div><button className="text-link" onClick={()=>{setUnitEntity(entity.id);setUnitName('');setUnitCode('');}}>Ajouter un établissement <Icon name="plus" size={13}/></button>{unitEntity===entity.id && <form className="unit-form" onSubmit={addUnit}><input placeholder="Nom du site" value={unitName} onChange={e=>setUnitName(e.target.value)} required/><input placeholder="Code" value={unitCode} onChange={e=>setUnitCode(e.target.value)} required/><button className="btn btn-small btn-primary">Ajouter</button></form>}</article>)}</div> : <EmptyState icon="building" title="Votre portefeuille est encore vide" text="Ajoutez vos entreprises ou unités opérationnelles avant d’importer des rapports." action={<button className="btn btn-primary" onClick={()=>setShowForm(true)}><Icon name="plus"/> Ajouter une entreprise</button>}/>}
  </>;
}

function DataScreen({ token, workspace, entities, imports, onRefresh, onToast }: {token: string; workspace: Workspace; entities: Entity[]; imports: ImportBatch[]; onRefresh: () => Promise<void>; onToast: (message: string) => void}) {
  const today = localDateInputValue(new Date()); const monthStart = `${today.slice(0, 7)}-01`;
  const [entity,setEntity]=useState(''); const [reportType,setReportType]=useState('SALES'); const [currency,setCurrency]=useState(workspace.default_currency); const [start,setStart]=useState(monthStart); const [end,setEnd]=useState(today); const [file,setFile]=useState<File|null>(null); const [busy,setBusy]=useState(false); const [preview,setPreview]=useState<ImportPreview|null>(null); const [mapping,setMapping]=useState({amount:'',date:''}); const [staged,setStaged]=useState<Staged|null>(null); const [selectedBatch,setSelectedBatch]=useState('');
  useEffect(()=>{if(!entity&&entities[0])setEntity(entities[0].id);},[entities,entity]);
  const selectedBatchIsBank = imports.find(batch=>batch.id===selectedBatch)?.report_type === 'BANK';
  const upload = async (event:FormEvent) => { event.preventDefault(); if(!file){onToast('Sélectionnez un fichier');return;} setBusy(true); try {const batch=await api<ImportBatch>(`/imports/?workspace_id=${workspace.id}`,token,{method:'POST',file,body:{entity,report_type:reportType,currency,period_start:start,period_end:end,workspace_id:workspace.id}});setSelectedBatch(batch.id);const data=await api<ImportPreview>(`/imports/${batch.id}/preview/?workspace_id=${workspace.id}`,token,{method:'POST',body:{workspace_id:workspace.id}});setPreview(data);setStaged(null);setMapping({amount:data.suggested_mapping?.amount||'',date:data.suggested_mapping?.date||''});await onRefresh();onToast('Fichier placé en quarantaine. Vérifiez les colonnes.');}catch(e){onToast(errorMessage(e));}finally{setBusy(false);} };
  const stage = async () => { if(!preview||!selectedBatch)return; setBusy(true);try{const result=await api<Staged>(`/imports/${selectedBatch}/stage/?workspace_id=${workspace.id}`,token,{method:'POST',body:{workspace_id:workspace.id,mapping}});setStaged(result);await onRefresh();}catch(e){onToast(errorMessage(e));}finally{setBusy(false);} };
  const confirm = async () => { if(!selectedBatch)return; setBusy(true);try{const result=await api<{facts_published:number;rejected_rows:number}>(`/imports/${selectedBatch}/confirm/?workspace_id=${workspace.id}`,token,{method:'POST',body:{workspace_id:workspace.id}});onToast(`${result.facts_published} ligne(s) publiées dans le cockpit`);setPreview(null);setStaged(null);setSelectedBatch('');setFile(null);await onRefresh();}catch(e){onToast(errorMessage(e));}finally{setBusy(false);} };
  return <><PageHeading kicker="QUALITÉ & PROVENANCE" title="Données & imports" description="Aucun chiffre ne rejoint le cockpit sans prévisualisation, contrôle et confirmation explicite." action={<span className="status-pill neutral">CSV · XLSX · PDF textuel assisté</span>}/>
    {entities.length===0 ? <EmptyState icon="building" title="Ajoutez d’abord une entreprise" text="Un import doit toujours être rattaché à une entité de votre portefeuille."/> : <div className="data-layout"><section className="panel import-panel"><div className="panel-head"><div><h3>Importer un rapport</h3><p>Fichier source conservé en quarantaine avant traitement.</p></div><span className="file-limit">MAX. 10 MO</span></div><form className="form-stack" onSubmit={upload}><label>Entreprise<select value={entity} onChange={e=>setEntity(e.target.value)} required>{entities.map(e=><option key={e.id} value={e.id}>{e.name}</option>)}</select></label><label>Famille de rapport<select value={reportType} onChange={e=>setReportType(e.target.value)}>{REPORT_TYPES.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><div className="form-grid two"><label>Début de période<input type="date" value={start} onChange={e=>setStart(e.target.value)} required/></label><label>Fin de période<input type="date" value={end} onChange={e=>setEnd(e.target.value)} required min={start}/></label></div><label>Devise du rapport<select value={currency} onChange={e=>setCurrency(e.target.value)}><option>XAF</option><option>XOF</option><option>EUR</option><option>USD</option></select></label><label className="file-drop"><input type="file" accept=".csv,.xlsx,.pdf,application/pdf,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={e=>setFile(e.target.files?.[0]||null)} required/><Icon name="file" size={24}/><b>{file?.name||'Choisir un fichier ou le déposer ici'}</b><span>CSV, Excel ou PDF textuel · maximum 10 Mo</span></label><button className="btn btn-primary full" disabled={busy}>{busy?'Téléversement…':'Placer le fichier en quarantaine'}<Icon name="arrow"/></button></form><div className="import-security"><Icon name="shield" size={15}/><span>Les macros et formules ne sont jamais exécutées. Les fichiers PDF scannés ne sont pas traités par OCR.</span></div></section>
      <section className="panel import-flow"><div className="panel-head"><div><h3>Parcours de validation</h3><p>Une étape humaine avant la publication.</p></div></div><div className="flow-steps"><div className={preview?'done':''}><span>01</span><div><b>Prévisualiser</b><small>Colonnes détectées et échantillon de lignes</small></div></div><div className={staged?'done':''}><span>02</span><div><b>Mapper & contrôler</b><small>Montant, date, période et anomalies</small></div></div><div className={staged?'current':''}><span>03</span><div><b>Confirmer</b><small>Seules les lignes en revue seront publiées</small></div></div></div>
        {preview && <div className="preview-box"><div className="preview-head"><div><span className="eyebrow">PRÉVISUALISATION</span><b>{imports.find(b=>b.id===selectedBatch)?.original_filename || 'Fichier importé'}</b></div><button className="icon-btn" onClick={()=>{setPreview(null);setStaged(null);}}><Icon name="close"/></button></div>{preview.assisted ? <><div className="form-hint">{preview.message}</div><pre className="pdf-preview">{preview.text_preview || 'Aucun texte détecté.'}</pre></> : <><div className="preview-count"><b>{preview.row_count}</b><span>lignes détectées</span><b>{preview.columns?.length}</b><span>colonnes</span></div>{preview.mapping_note && <div className="form-hint mapping-note">{preview.mapping_note}</div>}{!staged && <div className="form-grid two"><label>Colonne du montant<select value={mapping.amount} onChange={e=>setMapping(v=>({...v,amount:e.target.value}))}><option value="">Sélectionner…</option>{preview.columns?.map(c=><option key={c}>{c}</option>)}</select></label><label>Colonne de date {selectedBatchIsBank ? '(obligatoire pour un relevé bancaire)' : '(facultatif)'}<select value={mapping.date} onChange={e=>setMapping(v=>({...v,date:e.target.value}))}><option value="">Aucune</option>{preview.columns?.map(c=><option key={c}>{c}</option>)}</select></label></div>}<div className="table-wrap preview-table"><table><thead><tr>{preview.columns?.map(col=><th key={col}>{col}</th>)}</tr></thead><tbody>{preview.sample?.slice(0,6).map((row,i)=><tr key={i}>{preview.columns?.map(col=><td key={col}>{row[col]||'—'}</td>)}</tr>)}</tbody></table></div>{!staged ? <button className="btn btn-primary full" onClick={()=>void stage()} disabled={busy||!mapping.amount||(selectedBatchIsBank&&!mapping.date)}>{busy?'Analyse…':'Enregistrer le mapping & contrôler'}</button> : <div className="staged-result"><div className="staged-numbers"><div><b>{staged.rows_staged}</b><span>lignes préparées</span></div><div><b>{staged.rows_rejected}</b><span>lignes rejetées</span></div></div><p><b>{staged.metric_label}</b> — les montants sont conservés en {currency}. Aucun total n’est encore publié.</p>{staged.issues.length>0 && <div className="issues-list">{staged.issues.slice(0,5).map(issue=><div key={issue.row_number}><b>Ligne {issue.row_number}</b><span>{issue.message}</span></div>)}</div>}<div className="confirm-box"><Icon name="shield"/><span>Vous confirmez que la période, la devise et la colonne choisie sont correctes. La confirmation publiera uniquement les lignes acceptées.</span></div><button className="btn btn-primary full" disabled={busy||staged.rows_staged===0} onClick={()=>void confirm()}>{busy?'Confirmation…':`Confirmer et publier ${staged.rows_staged} ligne(s)`}</button></div>}</>}</div>}
      </section></div>}
    <div className="section-head"><div><h2>Historique des imports</h2><p>Provenance, statut et volume de chaque lot reçu.</p></div><span className="count-badge">{imports.length}</span></div>
    <div className="panel table-panel"><div className="table-wrap"><table><thead><tr><th>Fichier source</th><th>Entreprise</th><th>Type</th><th>Période</th><th>Lignes</th><th>Statut</th><th>Réception</th></tr></thead><tbody>{imports.map(batch=><tr key={batch.id}><td><b className="file-name"><Icon name="file" size={14}/>{batch.original_filename}</b><small className="hash">SHA-256 · {batch.sha256.slice(0,12)}…</small></td><td>{entities.find(e=>e.id===batch.entity)?.name||'—'}</td><td>{REPORT_TYPES.find(([v])=>v===batch.report_type)?.[1]||batch.report_type}</td><td>{shortDate(batch.period_start)} – {shortDate(batch.period_end)}</td><td>{batch.rows_staged || batch.rows_seen || '—'}<small>{batch.rows_rejected ? `${batch.rows_rejected} rejetée(s)` : ''}</small></td><td><span className={`status-pill ${batch.status.toLowerCase()}`}>{statusLabel(batch.status)}</span></td><td>{dateTime(batch.created_at)}</td></tr>)}{imports.length===0&&<tr><td colSpan={7} className="table-empty">Aucun rapport reçu.</td></tr>}</tbody></table></div></div>
  </>;
}

function ActionsScreen({ token, workspace, entities, actions, members, onRefresh, onToast }: {token:string;workspace:Workspace;entities:Entity[];actions:Action[];members:Member[];onRefresh:()=>Promise<void>;onToast:(message:string)=>void}) {
  const [showForm,setShowForm]=useState(false);const [title,setTitle]=useState('');const [description,setDescription]=useState('');const [entity,setEntity]=useState('');const [assigned,setAssigned]=useState('');const [priority,setPriority]=useState('MEDIUM');const [due,setDue]=useState('');const [busy,setBusy]=useState(false);const [filter,setFilter]=useState('ALL');
  const create = async (event:FormEvent)=>{event.preventDefault();setBusy(true);try{const body:Record<string,unknown>={workspace_id:workspace.id,title,description,priority};if(entity)body.entity=entity;if(assigned)body.assigned_to=Number(assigned);if(due)body.due_at=new Date(due).toISOString();await api(`/actions/?workspace_id=${workspace.id}`,token,{method:'POST',body});setTitle('');setDescription('');setShowForm(false);await onRefresh();onToast('Action créée et journalisée');}catch(e){onToast(errorMessage(e));}finally{setBusy(false);}};
  const update=async(action:Action,next:string)=>{try{await api(`/actions/${action.id}/?workspace_id=${workspace.id}`,token,{method:'PATCH',body:{status:next}});await onRefresh();onToast('Statut de l’action mis à jour');}catch(e){onToast(errorMessage(e));}};
  const visible=actions.filter(a=>filter==='ALL'||a.status===filter);
  return <><PageHeading kicker="EXÉCUTION & RESPONSABILITÉS" title="Centre d’actions" description="Transformez les alertes et écarts en tâches attribuées, échéancées et suivies jusqu’à leur clôture." action={<button className="btn btn-primary" onClick={()=>setShowForm(v=>!v)}><Icon name="plus"/> Créer une action</button>}/>
    <div className="stats-grid three"><StatCard icon="check" label="À FAIRE" value={actions.filter(a=>a.status==='OPEN').length} note="Responsable à confirmer"/><StatCard icon="clock" label="EN COURS" value={actions.filter(a=>a.status==='IN_PROGRESS').length} note="Traitement engagé" tone="blue"/><StatCard icon="bell" label="EN RETARD" value={actions.filter(a=>a.due_at&&new Date(a.due_at)<new Date()&&!['DONE','CANCELLED'].includes(a.status)).length} note="Échéance dépassée" tone="coral"/></div>
    {showForm&&<section className="panel form-panel"><div className="panel-head"><div><h3>Nouvelle action de pilotage</h3><p>Une action doit avoir un responsable ou être explicitement identifiée comme non assignée.</p></div><button className="icon-btn" onClick={()=>setShowForm(false)}><Icon name="close"/></button></div><form className="form-grid" onSubmit={create}><label className="span-2">Intitulé<input value={title} onChange={e=>setTitle(e.target.value)} required maxLength={180} placeholder="Ex. Vérifier l’écart de dépenses du site Bonabéri"/></label><label className="span-2">Description<textarea value={description} onChange={e=>setDescription(e.target.value)} rows={3} placeholder="Contexte, décision attendue et élément de preuve."/></label><label>Entreprise<select value={entity} onChange={e=>setEntity(e.target.value)}><option value="">Portefeuille</option>{entities.map(e=><option key={e.id} value={e.id}>{e.name}</option>)}</select></label><label>Responsable<select value={assigned} onChange={e=>setAssigned(e.target.value)}><option value="">Non assignée</option>{members.map(m=><option key={m.user_id} value={m.user_id}>{m.full_name||m.email} · {m.role}</option>)}</select></label><label>Priorité<select value={priority} onChange={e=>setPriority(e.target.value)}><option value="LOW">Faible</option><option value="MEDIUM">Normale</option><option value="HIGH">Élevée</option><option value="CRITICAL">Critique</option></select></label><label>Échéance<input type="datetime-local" value={due} onChange={e=>setDue(e.target.value)}/></label><div className="form-actions"><button className="btn btn-primary" disabled={busy}>{busy?'Création…':'Créer l’action'}</button></div></form></section>}
    <div className="section-head"><div><h2>Suivi des actions</h2><p>Historique conservé à chaque changement de statut.</p></div><select className="filter-select" value={filter} onChange={e=>setFilter(e.target.value)}><option value="ALL">Tous les statuts</option><option value="OPEN">À faire</option><option value="IN_PROGRESS">En cours</option><option value="BLOCKED">Bloquée</option><option value="DONE">Terminées</option></select></div>
    {visible.length===0?<EmptyState icon="check" title="Aucune action dans cette vue" text="Créez une action depuis une priorité ou un écart observé dans le cockpit." action={<button className="btn btn-primary" onClick={()=>setShowForm(true)}><Icon name="plus"/> Créer une action</button>}/>:<div className="action-board">{visible.map(action=><article className="action-card" key={action.id}><div className="action-card-head"><span className={`priority-tag ${action.priority.toLowerCase()}`}>{priorityLabel(action.priority)}</span><span className={`status-pill ${action.status.toLowerCase()}`}>{statusLabel(action.status)}</span></div><h3>{action.title}</h3>{action.description&&<p>{action.description}</p>}<div className="action-card-meta"><span><Icon name="building" size={14}/>{entities.find(e=>e.id===action.entity)?.name||'Portefeuille'}</span><span><Icon name="shield" size={14}/>{action.assigned_to_name||'Non assignée'}</span><span><Icon name="clock" size={14}/>{action.due_at?dateTime(action.due_at):'Sans échéance'}</span></div><div className="action-card-foot"><span>Créée le {shortDate(action.created_at)}</span>{action.status!=='DONE'&&action.status!=='CANCELLED'&&<select value={action.status} onChange={e=>void update(action,e.target.value)} aria-label="Changer le statut"><option value="OPEN">À faire</option><option value="IN_PROGRESS">En cours</option><option value="BLOCKED">Bloquée</option><option value="DONE">Terminée</option><option value="CANCELLED">Annulée</option></select>}</div></article>)}</div>}
  </>;
}
function priorityLabel(priority:string){return ({LOW:'Faible',MEDIUM:'Normale',HIGH:'Élevée',CRITICAL:'Critique'} as Record<string,string>)[priority]||priority;}

function AnalysisScreen({ cockpit, entities }: {cockpit:Cockpit|null;entities:Entity[]}) {
  const metrics=cockpit?.metrics||[];
  const unique=Array.from(new Set(metrics.map(m=>m.metric_key)));
  return <><PageHeading kicker="LECTURE DES DONNÉES" title="Analyse du portefeuille" description="Les analyses restent strictement limitées aux faits validés. Les devises et périodes non comparables sont séparées."/><div className="analysis-notice"><Icon name="shield"/><div><b>Règle de fiabilité</b><span>YFEN ne convertit ni n’additionne des devises différentes sans un taux, une date et une méthode documentés.</span></div></div>
    {metrics.length===0?<EmptyState icon="chart" title="Pas encore de base d’analyse" text="Les visualisations apparaîtront après confirmation d’au moins un import et validation de ses lignes."/>:<><div className="analysis-kpis"><div className="panel"><span className="eyebrow">FAMILLES DE MÉTRIQUES</span><b>{unique.length}</b><small>Familles disposant de données validées</small></div><div className="panel"><span className="eyebrow">FAITS VALIDÉS</span><b>{metrics.reduce((sum,m)=>sum+m.fact_count,0)}</b><small>Nombre de lignes source agrégées</small></div><div className="panel"><span className="eyebrow">SOURCES CITÉES</span><b>{new Set(metrics.flatMap(m=>m.sources.map(s=>s.id))).size}</b><small>Lots d’import référencés</small></div></div><div className="analysis-list">{metrics.map((metric,index)=><div className="panel analysis-row" key={`${metric.metric_key}-${metric.entity_id}-${metric.currency}-${metric.period_start}-${index}`}><div><span className="eyebrow">{metric.label}</span><h3>{metric.entity_count > 1 ? `${metric.entity_count} entités · total arithmétique` : (metric.entity_names[0] || entities.find(e=>e.id===metric.entity_id)?.name || 'Entité')}</h3><small>{shortDate(metric.period_start)} – {shortDate(metric.period_end)} · {metric.fact_count} ligne(s) · hors élimination intragroupe</small></div><div className="analysis-value"><b>{formatNumber(metric.value,metric.currency||undefined)}</b><small>{metric.unit==='AMOUNT'?'Montant rapporté':'Unité déclarée'}</small></div><div className="analysis-source"><b>{metric.sources.length} source(s)</b>{metric.sources.map(source=><small key={source.id}>{source.file}</small>)}</div></div>)}</div></>}
  </>;
}

function AssistantScreen() {
  return <><PageHeading kicker="ASSISTANCE INTELLIGENTE · P1" title="Assistant exécutif" description="L’assistant sera activé uniquement quand les imports, les KPI et la traçabilité auront passé les contrôles de qualité."/><div className="assistant-locked"><div className="assistant-orb"><Icon name="spark" size={29}/></div><span className="status-pill neutral">MODULE P1 · NON ACTIVÉ</span><h2>Une IA qui explique des faits vérifiables.</h2><p>Le modèle ne recevra pas de connexion SQL ni d’accès direct aux fichiers bruts. Il formulera des réponses à partir de métriques structurées autorisées, avec période, devise et sources.</p><div className="assistant-principles"><div><Icon name="check"/><span>Calculs déterministes côté backend</span></div><div><Icon name="check"/><span>Références de source visibles dans les réponses</span></div><div><Icon name="check"/><span>Aucune exécution autonome d’opérations sensibles</span></div></div></div></>;
}

function SettingsScreen({ token, workspace, user, members, audit, onRefresh, onToast, onLogout }: {token:string;workspace:Workspace;user:User;members:Member[];audit:Audit[];onRefresh:()=>Promise<void>;onToast:(message:string)=>void;onLogout:()=>Promise<void>}) {
  const [email,setEmail]=useState('');const [role,setRole]=useState('VIEWER');const [busy,setBusy]=useState(false);
  const addMember=async(event:FormEvent)=>{event.preventDefault();setBusy(true);try{await api(`/members/?workspace_id=${workspace.id}`,token,{method:'POST',body:{workspace_id:workspace.id,email,role}});setEmail('');await onRefresh();onToast('Membre ajouté à l’espace');}catch(e){onToast(errorMessage(e));}finally{setBusy(false);}};
  return <><PageHeading kicker="ADMINISTRATION & TRAÇABILITÉ" title="Paramètres & accès" description="Gérez votre espace, les accès de votre équipe et les événements sensibles."/><div className="settings-grid"><section className="panel"><div className="panel-head"><div><h3>Workspace</h3><p>Paramètres de votre environnement actif.</p></div></div><div className="setting-line"><span>Nom de l’espace</span><b>{workspace.name}</b></div><div className="setting-line"><span>Devise par défaut</span><b>{workspace.default_currency}</b></div><div className="setting-line"><span>Fuseau horaire</span><b>{workspace.timezone}</b></div><div className="setting-line"><span>Votre rôle</span><b>{workspace.role}</b></div><div className="setting-line"><span>Compte connecté</span><b>{user.email}</b></div><div className="security-note"><Icon name="shield"/><span>Le contrôle d’appartenance au workspace est appliqué côté API à chaque requête métier. Les données sont isolées par espace.</span></div></section>
    <section className="panel"><div className="panel-head"><div><h3>Membres & rôles</h3><p>Ajout d’un compte déjà créé sur YFEN (invitation e-mail à venir).</p></div><span className="count-badge">{members.length}</span></div>{(workspace.role==='OWNER'||workspace.role==='ADMIN')&&<form className="member-form" onSubmit={addMember}><input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="email@entreprise.com" required/><select value={role} onChange={e=>setRole(e.target.value)}><option value="VIEWER">Lecteur</option><option value="MANAGER">Responsable</option><option value="ACCOUNTANT">Comptable</option><option value="ADMIN">Administrateur</option></select><button className="btn btn-primary btn-small" disabled={busy}>{busy?'…':'Ajouter'}</button></form>}<div className="member-list">{members.map(member=><div className="member-row" key={member.id}><div className="user-avatar small">{(member.full_name||member.email).slice(0,1).toUpperCase()}</div><div><b>{member.full_name||member.email}</b><small>{member.email}</small></div><span className="role-tag">{member.role}</span></div>)}{members.length===0&&<div className="empty-inline">Aucun membre listé.</div>}</div></section></div>
    <div className="section-head"><div><h2>Journal d’activité</h2><p>Trace les actions sur l’espace, les imports et les changements de statut.</p></div><button className="btn btn-secondary btn-small" onClick={()=>void onRefresh()}><Icon name="clock"/> Actualiser</button></div><div className="panel table-panel"><div className="table-wrap"><table><thead><tr><th>Horodatage</th><th>Acteur</th><th>Événement</th><th>Objet</th><th>Détails</th></tr></thead><tbody>{audit.map(item=><tr key={item.id}><td>{dateTime(item.created_at)}</td><td>{item.actor}</td><td><b>{item.action}</b></td><td>{item.target_type}</td><td><code>{JSON.stringify(item.metadata)}</code></td></tr>)}{audit.length===0&&<tr><td colSpan={5} className="table-empty">Aucun événement visible ou droits insuffisants pour lire le journal.</td></tr>}</tbody></table></div></div>
    <div className="settings-danger"><div><b>Terminer votre session</b><span>Le token d’accès de cette session sera révoqué côté serveur.</span></div><button className="btn btn-danger" onClick={()=>void onLogout()}><Icon name="logout"/> Se déconnecter</button></div>
  </>;
}
