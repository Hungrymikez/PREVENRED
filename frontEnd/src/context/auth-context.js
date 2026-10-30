import { createContext } from 'react'

/** Sesión actual. El valor lo entrega <AuthProvider>; se lee con useAuth(). */
export const AuthContext = createContext(null)
