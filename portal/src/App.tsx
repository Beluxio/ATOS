import { useState, useRef, useEffect } from 'react'

const API = 'https://api.beluxio.org'


// ── Types ──────────────────────────────────────────────────────────────────
type View = 'login' | 'forgot' | 'reset' | 'home'
interface ChatMsg { role: 'user' | 'assistant'; content: string }

interface DBAccess {
  id: number
  database_name: string
  db_username: string
  db_password: string
  status: string
  expires_at: string | null
  days_left: number | null
  expiring_soon: boolean
}

// ── ATOS Chat Widget ───────────────────────────────────────────────────────
function ATOSWidget({ userEmail }: { userEmail: string }) {
  const [open, setOpen]         = useState(false)
  const [input, setInput]       = useState('')
  const [msgs, setMsgs]         = useState<ChatMsg[]>([])
  const [history, setHistory]   = useState<object[]>([])
  const [loading, setLoading]   = useState(false)
  const sessionId = useRef(`portal-${Date.now()}`)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [msgs, open])

  async function send() {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setMsgs(p => [...p, { role: 'user', content: text }])
    setLoading(true)
    try {
      const r = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId.current, history }),
      })
      const d = await r.json()
      setHistory(d.history ?? [])
      setMsgs(p => [...p, { role: 'assistant', content: d.reply }])
    } catch {
      setMsgs(p => [...p, { role: 'assistant', content: '⚠️ Sin conexión con el soporte.' }])
    } finally { setLoading(false) }
  }

  return (
    <>
      <button data-atos-fab onClick={() => setOpen(o => !o)} style={s.fab}>
        {open ? '✕' : '💬'}
      </button>
      {open && (
        <div style={s.chatPanel}>
          <div style={s.chatHeader}>
            <div style={{ display:'flex', alignItems:'center', gap:10 }}>
              <div style={s.atosAvatar}>A</div>
              <div>
                <div style={{ fontWeight:600, fontSize:14 }}>ATOS Support</div>
                <div style={{ fontSize:11, color:'#9b9b9b' }}>{userEmail}</div>
              </div>
            </div>
            <div style={{ width:8, height:8, borderRadius:'50%', background:'#4caf50' }} />
          </div>
          <div style={s.chatMsgs}>
            {msgs.length === 0 && (
              <div style={s.emptyChat}>
                <div style={{ fontSize:28, marginBottom:8 }}>👋</div>
                <div style={{ fontWeight:500, marginBottom:4 }}>¿En qué te ayudo?</div>
                <div style={{ color:'#9b9b9b', fontSize:13 }}>Escríbeme si tienes problemas con tu cuenta.</div>
              </div>
            )}
            {msgs.map((m, i) => (
              <div key={i} style={{ display:'flex', justifyContent: m.role==='user' ? 'flex-end' : 'flex-start', marginBottom:8 }}>
                <div style={m.role==='user' ? s.bubbleUser : s.bubbleBot}>{m.content}</div>
              </div>
            ))}
            {loading && (
              <div style={{ display:'flex', marginBottom:8 }}>
                <div style={{ ...s.bubbleBot, gap:4 }}>
                  {[0,0.2,0.4].map((d,i) => <span key={i} style={{ ...s.dot, animationDelay:`${d}s` }} />)}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <div style={s.chatInputRow}>
            <input style={s.chatInput} placeholder="Escribe tu mensaje..." value={input}
              onChange={e => setInput(e.target.value)} onKeyDown={e => e.key==='Enter' && send()}
              disabled={loading} />
            <button style={s.sendBtn} onClick={send} disabled={loading || !input.trim()}>➤</button>
          </div>
        </div>
      )}
    </>
  )
}


// ── Home View ─────────────────────────────────────────────────────────────
function HomeView({ user, onLogout }: { user: { email: string; role: string; name: string; password: string }; onLogout: () => void }) {
  const [accesses, setAccesses] = useState<DBAccess[]>([])
  const [loadingDb, setLoadingDb] = useState(true)
  const [token, setToken] = useState<string | null>(null)
  const [showPwd, setShowPwd] = useState<Record<number, boolean>>({})

  useEffect(() => {
    async function init() {
      // Obtener token para llamadas autenticadas
      const r = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: user.email, password: user.password }),
      })
      const d = await r.json()
      if (d.access_token) {
        setToken(d.access_token)
        const ra = await fetch(`${API}/api/db-access/my-accesses`, {
          headers: { Authorization: `Bearer ${d.access_token}` },
        })
        if (ra.ok) {
          const data = await ra.json()
          setAccesses(data.accesses ?? [])
        }
      }
      setLoadingDb(false)
    }
    init()
  }, [user.email, user.password])

  const active = accesses.filter(a => a.status === 'active')
  const inactive = accesses.filter(a => a.status !== 'active')

  return (
    <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg,#1a1a1e 0%,#1f1f28 100%)', padding: '32px 16px' }}>
      <div style={{ maxWidth: 760, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 20 }}>

        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 22, color: '#ff5722' }}>◈</span>
            <span style={{ fontSize: 17, fontWeight: 600 }}>DataCo Analytics</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 13, fontWeight: 500 }}>{user.name}</div>
              <div style={{ fontSize: 11, color: '#9b9b9b' }}>{user.email}</div>
            </div>
            <button onClick={onLogout} style={{ ...s.btn, width: 'auto', marginTop: 0, padding: '7px 14px',
              background: '#3a3a40', fontSize: 13 }}>Salir</button>
          </div>
        </div>

        {/* Welcome */}
        <div style={{ background: '#25252b', border: '1px solid #35353d', borderRadius: 12, padding: '20px 24px' }}>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>Bienvenido de vuelta 👋</div>
          <div style={{ fontSize: 13, color: '#9b9b9b' }}>
            Tienes <strong style={{ color: '#4ade80' }}>{active.length}</strong> acceso{active.length !== 1 ? 's' : ''} activo{active.length !== 1 ? 's' : ''} a bases de datos.
            Usa el chat de soporte si necesitas solicitar nuevos accesos.
          </div>
        </div>

        {/* Active accesses */}
        <div style={{ background: '#25252b', border: '1px solid #35353d', borderRadius: 12, padding: 20 }}>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 16 }}>🗄️ Mis accesos activos</div>

          {loadingDb ? (
            <div style={{ color: '#9b9b9b', fontSize: 13 }}>Cargando...</div>
          ) : active.length === 0 ? (
            <div style={{ padding: '24px 0', textAlign: 'center', color: '#9b9b9b', fontSize: 13 }}>
              No tienes accesos activos a ninguna base de datos.<br />
              <span style={{ color: '#ff7043' }}>Usa el chat 💬 para solicitarlos.</span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {active.map(a => (
                <div key={a.id} style={{ background: '#1c1c1e', border: `1px solid ${a.expiring_soon ? '#facc1544' : '#35353d'}`,
                  borderRadius: 10, padding: '14px 16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 6 }}>
                        {a.database_name}
                        {a.expiring_soon && <span style={{ marginLeft: 8, fontSize: 11, color: '#facc15' }}>⚠️ Expira pronto</span>}
                      </div>
                      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                        <div>
                          <div style={{ fontSize: 11, color: '#9b9b9b', marginBottom: 2 }}>USUARIO</div>
                          <code style={{ fontSize: 13, color: '#e0e0e0' }}>{a.db_username}</code>
                        </div>
                        <div>
                          <div style={{ fontSize: 11, color: '#9b9b9b', marginBottom: 2 }}>CONTRASEÑA</div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <code style={{ fontSize: 13, color: showPwd[a.id] ? '#facc15' : '#9b9b9b' }}>
                              {showPwd[a.id] ? a.db_password : '••••••••••••'}
                            </code>
                            <button onClick={() => setShowPwd(p => ({ ...p, [a.id]: !p[a.id] }))}
                              style={{ background: 'none', border: 'none', color: '#9b9b9b', cursor: 'pointer', fontSize: 12 }}>
                              {showPwd[a.id] ? '🙈' : '👁'}
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', fontSize: 12, color: a.expiring_soon ? '#facc15' : '#9b9b9b' }}>
                      {a.days_left !== null ? `Expira en ${a.days_left} días` : ''}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Inactive accesses */}
        {inactive.length > 0 && (
          <div style={{ background: '#25252b', border: '1px solid #35353d', borderRadius: 12, padding: 20 }}>
            <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 14, color: '#9b9b9b' }}>Accesos anteriores</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {inactive.map(a => (
                <div key={a.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px',
                  background: '#1c1c1e', borderRadius: 8, fontSize: 13 }}>
                  <span style={{ color: '#9b9b9b' }}>{a.database_name}</span>
                  <span style={{ color: '#f87171', fontSize: 12 }}>{a.status}</span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
      <ATOSWidget userEmail={user.email} />
    </div>
  )
}


// ── Main App ───────────────────────────────────────────────────────────────
export default function App() {
  const [view, setView]           = useState<View>('login')
  const [email, setEmail]         = useState('')
  const [password, setPassword]   = useState('')
  const [error, setError]         = useState('')
  const [loggedUser, setLoggedUser] = useState<{ email: string; password: string; name: string; role: string } | null>(null)

  // Forgot flow
  const [forgotEmail, setForgotEmail]     = useState('')
  const [forgotMsg, setForgotMsg]         = useState('')
  const [forgotToken, setForgotToken]     = useState('')
  const [forgotLoading, setForgotLoading] = useState(false)
  const [snapshotBefore, setSnapshotBefore] = useState<string | null>(null)

  // Reset confirm flow
  const [token, setToken]               = useState('')
  const [newPass, setNewPass]           = useState('')
  const [resetMsg, setResetMsg]         = useState('')
  const [resetLoading, setResetLoading] = useState(false)
  const [resetOk, setResetOk]           = useState(false)
  const [snapshotAfter, setSnapshotAfter] = useState<string | null>(null)


  // ── Login via ATOS auth ──
  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    try {
      const r = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const d = await r.json()
      if (r.ok && d.access_token) {
        setLoggedUser({ email, password, name: email.split('@')[0], role: d.user?.role ?? 'user' })
        setView('home')
      } else {
        setError(d.message ?? d.detail ?? 'Credenciales incorrectas.')
      }
    } catch {
      setError('No se pudo conectar con el servidor.')
    }
  }

  // ── Request reset token ──
  async function handleForgot(e: React.FormEvent) {
    e.preventDefault()
    setForgotLoading(true)
    setForgotMsg('')
    setSnapshotBefore(null)
    try {
      const r = await fetch(`${API}/api/reset-password/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail }),
      })
      const d = await r.json()
      if (r.ok && d.token) {
        setForgotToken(d.token)
        if (d.email_sent) {
          setForgotMsg(`📧 Token enviado a ${forgotEmail}. Revisa tu correo.\n\nSi no llega, usa este token directamente:\n${d.token}`)
        } else {
          setForgotMsg(`✅ Token generado (modo demo):\n\n${d.token}`)
        }
      } else {
        setForgotMsg(`Error: ${d.detail ?? d.message ?? JSON.stringify(d)}`)
      }
    } catch {
      setForgotMsg('Error de conexión.')
    } finally { setForgotLoading(false) }
  }

  // ── Confirm new password ──
  async function handleReset(e: React.FormEvent) {
    e.preventDefault()
    setResetLoading(true)
    setResetMsg('')
    try {
      const r = await fetch(`${API}/api/reset-password/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: newPass }),
      })
      const d = await r.json()
      if (r.ok) {
        setResetOk(true)
        setResetMsg('✅ Contraseña actualizada. Ya puedes iniciar sesión.')
        // Captura estado DESPUÉS del reset
        const snap = await fetch(`${API}/api/accounts/${encodeURIComponent(forgotEmail)}/status`)
        if (snap.ok) {
          const sd = await snap.json()
          setSnapshotAfter(sd.account?.updated_at ?? null)
        }
      } else {
        setResetMsg(`Error: ${d.detail ?? d.message ?? JSON.stringify(d)}`)
      }
    } catch {
      setResetMsg('Error de conexión.')
    } finally { setResetLoading(false) }
  }

  // ── Home ──
  if (view === 'home' && loggedUser) {
    return <HomeView user={loggedUser} onLogout={() => { setView('login'); setEmail(''); setPassword(''); setLoggedUser(null) }} />
  }

  // ── Forgot password ──
  if (view === 'forgot') {
    return (
      <div style={s.page}>
        <div style={s.card}>
          <Logo />
          <h2 style={s.title}>Recuperar contraseña</h2>
          <p style={{ fontSize:13, color:'#9b9b9b', marginBottom:20, alignSelf:'flex-start' }}>
            Ingresa tu email y te generaremos un token de reset.
          </p>
          <form onSubmit={handleForgot} style={{ width:'100%' }}>
            <label style={s.label}>Email</label>
            <input style={s.input} type="email" placeholder="usuario@dataco.com"
              value={forgotEmail} onChange={e => setForgotEmail(e.target.value)} required />
            <button type="submit" style={s.btn} disabled={forgotLoading}>
              {forgotLoading ? 'Generando...' : 'Obtener token'}
            </button>
          </form>

          {forgotMsg && (
            <div style={{ ...s.infoBox, marginTop:16, whiteSpace:'pre-wrap', wordBreak:'break-all' }}>
              {forgotMsg}
              {forgotToken && (
                <button onClick={() => { setToken(forgotToken); setView('reset') }}
                  style={{ ...s.btn, marginTop:12, background:'#ff5722' }}>
                  Cambiar contraseña →
                </button>
              )}
            </div>
          )}

          <button onClick={() => { setView('login'); setForgotMsg('') }}
            style={{ ...s.btn, marginTop:12, background:'transparent', color:'#9b9b9b', border:'1px solid #3a3a42' }}>
            ← Volver al login
          </button>
        </div>
        <ATOSWidget userEmail={forgotEmail} />
      </div>
    )
  }

  // ── Reset confirm ──
  if (view === 'reset') {
    return (
      <div style={s.page}>
        <div style={s.card}>
          <Logo />
          <h2 style={s.title}>Nueva contraseña</h2>
          <form onSubmit={handleReset} style={{ width:'100%' }}>
            <label style={s.label}>Token de reset</label>
            <input style={s.input} type="text" placeholder="Pega el token aquí"
              value={token} onChange={e => setToken(e.target.value)} required />
            <label style={{ ...s.label, marginTop:14 }}>Nueva contraseña</label>
            <input style={s.input} type="password" placeholder="Mínimo 8 caracteres"
              value={newPass} onChange={e => setNewPass(e.target.value)} required />
            <button type="submit" style={s.btn} disabled={resetLoading || resetOk}>
              {resetLoading ? 'Actualizando...' : 'Cambiar contraseña'}
            </button>
          </form>

          {resetMsg && (
            <div style={{ ...s.infoBox, marginTop:16, color: resetOk ? '#4caf50' : '#ff7043' }}>
              {resetMsg}
            </div>
          )}

          {/* Comparación antes / después */}
          {resetOk && snapshotBefore && snapshotAfter && (
            <div style={{ width:'100%', marginTop:16 }}>
              <div style={{ fontSize:12, color:'#9b9b9b', marginBottom:8, textAlign:'center' }}>
                Verificación del cambio en base de datos
              </div>
              <div style={{ display:'flex', gap:8 }}>
                <div style={{ flex:1, padding:'10px 12px', background:'#1c1c1e', borderRadius:8,
                              border:'1px solid #3a3a42', textAlign:'center' }}>
                  <div style={{ fontSize:11, color:'#9b9b9b', marginBottom:4 }}>ANTES</div>
                  <div style={{ fontSize:11, color:'#ff7043', fontFamily:'monospace', wordBreak:'break-all' }}>
                    {new Date(snapshotBefore).toLocaleTimeString()}
                  </div>
                </div>
                <div style={{ display:'flex', alignItems:'center', color:'#4caf50', fontSize:18 }}>→</div>
                <div style={{ flex:1, padding:'10px 12px', background:'#1c1c1e', borderRadius:8,
                              border:'1px solid #4caf50', textAlign:'center' }}>
                  <div style={{ fontSize:11, color:'#9b9b9b', marginBottom:4 }}>DESPUÉS</div>
                  <div style={{ fontSize:11, color:'#4caf50', fontFamily:'monospace', wordBreak:'break-all' }}>
                    {new Date(snapshotAfter).toLocaleTimeString()}
                  </div>
                </div>
              </div>
              <div style={{ fontSize:11, color:'#4caf50', textAlign:'center', marginTop:8 }}>
                ✓ El registro fue actualizado en la base de datos
              </div>
            </div>
          )}

          {resetOk
            ? <button onClick={() => { setView('login'); setToken(''); setNewPass(''); setResetMsg(''); setResetOk(false) }}
                style={{ ...s.btn, marginTop:12, background:'#ff5722' }}>
                Ir al login
              </button>
            : <button onClick={() => setView('forgot')}
                style={{ ...s.btn, marginTop:12, background:'transparent', color:'#9b9b9b', border:'1px solid #3a3a42' }}>
                ← Volver
              </button>
          }
        </div>
        <ATOSWidget userEmail={forgotEmail} />
      </div>
    )
  }

  // ── Login ──
  return (
    <div style={s.page}>
      <div style={s.card}>
        <Logo />
        <h1 style={s.title}>Sign in</h1>
        <form onSubmit={handleLogin} style={{ width:'100%' }}>
          <label style={s.label}>Email</label>
          <input style={s.input} type="email" placeholder="usuario@dataco.com"
            value={email} onChange={e => setEmail(e.target.value)} autoFocus required />
          <label style={{ ...s.label, marginTop:14 }}>Password</label>
          <input style={s.input} type="password" placeholder="••••••••"
            value={password} onChange={e => setPassword(e.target.value)} required />
          {error && <div style={s.errorBox}>{error}</div>}
          <button type="submit" style={s.btn}>Sign in</button>
        </form>

        <div style={{ display:'flex', justifyContent:'space-between', width:'100%', marginTop:14 }}>
          <span style={{ fontSize:13, color:'#9b9b9b' }}>¿Olvidaste tu contraseña?</span>
          <button style={s.linkBtn} onClick={() => { setForgotEmail(email); setView('forgot') }}>
            Recuperar →
          </button>
        </div>

      </div>

      <ATOSWidget userEmail={email} />
    </div>
  )
}

function Logo() {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:28 }}>
      <span style={{ fontSize:26, color:'#ff5722' }}>◈</span>
      <span style={{ fontSize:19, fontWeight:600, letterSpacing:'-0.3px' }}>DataCo Analytics</span>
    </div>
  )
}

// ── Styles ─────────────────────────────────────────────────────────────────
const s: Record<string, React.CSSProperties> = {
  page:     { minHeight:'100vh', display:'flex', alignItems:'center', justifyContent:'center',
              background:'linear-gradient(135deg,#1a1a1e 0%,#1f1f28 100%)' },
  card:     { background:'#25252b', border:'1px solid #35353d', borderRadius:16, padding:'40px 36px',
              width:'100%', maxWidth:420, display:'flex', flexDirection:'column', alignItems:'center',
              boxShadow:'0 20px 60px rgba(0,0,0,0.4)' },
  title:    { fontSize:22, fontWeight:600, marginBottom:22, alignSelf:'flex-start', color:'#f0f0f0' },
  label:    { display:'block', fontSize:13, fontWeight:500, color:'#aaa', marginBottom:6, width:'100%' },
  input:    { width:'100%', padding:'11px 14px', background:'#1c1c1e', border:'1px solid #3a3a42',
              borderRadius:8, color:'#f0f0f0', fontSize:14, outline:'none', fontFamily:'inherit' },
  btn:      { width:'100%', marginTop:16, padding:'12px', background:'#ff5722', color:'#fff',
              border:'none', borderRadius:8, fontSize:14, fontWeight:600, cursor:'pointer', fontFamily:'inherit' },
  linkBtn:  { background:'none', border:'none', color:'#ff7043', fontSize:13, cursor:'pointer',
              fontWeight:500, fontFamily:'inherit' },
  errorBox: { marginTop:12, padding:'10px 14px', background:'rgba(255,87,34,0.12)',
              border:'1px solid rgba(255,87,34,0.3)', borderRadius:8, color:'#ff7043', fontSize:13, width:'100%' },
  infoBox:  { padding:'12px 14px', background:'#1c1c1e', border:'1px solid #3a3a42',
              borderRadius:8, fontSize:13, color:'#e0e0e0', width:'100%' },
  // Widget
  fab:      { position:'fixed', bottom:28, right:28, width:56, height:56, borderRadius:'50%',
              background:'#ff5722', color:'#fff', border:'none', fontSize:22, cursor:'pointer',
              boxShadow:'0 4px 20px rgba(255,87,34,0.5)', zIndex:1000 },
  chatPanel:{ position:'fixed', bottom:96, right:28, width:360, height:500, background:'#25252b',
              border:'1px solid #35353d', borderRadius:16, display:'flex', flexDirection:'column',
              boxShadow:'0 20px 60px rgba(0,0,0,0.5)', zIndex:999, overflow:'hidden' },
  chatHeader:{ padding:'14px 16px', background:'#1e1e24', borderBottom:'1px solid #35353d',
               display:'flex', alignItems:'center', justifyContent:'space-between' },
  atosAvatar:{ width:34, height:34, borderRadius:'50%', background:'#ff5722', display:'flex',
               alignItems:'center', justifyContent:'center', fontWeight:700, fontSize:15, color:'#fff' },
  chatMsgs: { flex:1, overflowY:'auto', padding:'16px', display:'flex', flexDirection:'column' },
  emptyChat:{ textAlign:'center', padding:'40px 16px', color:'#f0f0f0', fontSize:14 },
  bubbleUser:{ maxWidth:'78%', padding:'9px 13px', background:'#ff5722', color:'#fff',
               borderRadius:'14px 14px 2px 14px', fontSize:13, lineHeight:1.5, whiteSpace:'pre-wrap', wordBreak:'break-word' },
  bubbleBot: { maxWidth:'78%', padding:'9px 13px', background:'#2e2e36', color:'#e0e0e0',
               borderRadius:'14px 14px 14px 2px', fontSize:13, lineHeight:1.5, whiteSpace:'pre-wrap', wordBreak:'break-word' },
  dot:       { display:'inline-block', width:6, height:6, borderRadius:'50%', background:'#9b9b9b',
               animation:'bounce 1s infinite' },
  chatInputRow:{ display:'flex', padding:'12px', borderTop:'1px solid #35353d', gap:8 },
  chatInput: { flex:1, padding:'9px 12px', background:'#1c1c1e', border:'1px solid #3a3a42',
               borderRadius:8, color:'#f0f0f0', fontSize:13, outline:'none', fontFamily:'inherit' },
  sendBtn:   { padding:'9px 14px', background:'#ff5722', color:'#fff', border:'none',
               borderRadius:8, cursor:'pointer', fontSize:14 },
}
