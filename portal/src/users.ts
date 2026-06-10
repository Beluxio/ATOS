export interface PortalUser {
  email: string
  password: string
  name: string
  role: string
}

// Usuarios ficticios del portal DataCo — distintos a los usuarios de ATOS
export const PORTAL_USERS: PortalUser[] = [
  { email: 'carlos.garcia@dataco.com',  password: 'Carlos123!',  name: 'Carlos García',  role: 'Data Engineer' },
  { email: 'maria.lopez@dataco.com',    password: 'Maria456!',   name: 'María López',    role: 'Data Analyst' },
  { email: 'juan.torres@dataco.com',    password: 'Juan789!',    name: 'Juan Torres',    role: 'ML Engineer' },
  { email: 'ana.mendez@dataco.com',     password: 'Ana2025!',    name: 'Ana Méndez',     role: 'Platform Admin' },
]

export function authenticate(email: string, password: string): PortalUser | null {
  return PORTAL_USERS.find(u => u.email === email && u.password === password) ?? null
}
