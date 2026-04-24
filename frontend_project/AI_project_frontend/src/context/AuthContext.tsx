import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import client from '../api/client';

interface AuthUser {
  id: number;
  username: string;
  display_name?: string | null;
  role: string;
  is_admin: boolean;
}

interface AuthContextType {
  isAuthenticated: boolean;
  userName: string;
  isAdmin: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const bootstrapAuth = async () => {
      try {
        const { data } = await client.get<AuthUser>('/auth/me');
        setUser(data);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    bootstrapAuth();
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const { data } = await client.post<{ user: AuthUser }>('/auth/login', { username, password });
      setUser(data.user);
      return true;
    } catch {
      setUser(null);
      return false;
    }
  };

  const logout = async () => {
    try {
      await client.post('/auth/logout');
    } finally {
      setUser(null);
      sessionStorage.removeItem('infosearch_display');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: Boolean(user),
        userName: user?.display_name || user?.username || '',
        isAdmin: Boolean(user?.is_admin),
        login,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
