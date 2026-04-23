import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

interface AuthContextType {
  isAuthenticated: boolean;
  userName: string;
  isAdmin: boolean;
  login: (username: string, password: string) => boolean;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return sessionStorage.getItem('infosearch_auth') === 'true';
  });
  const [userName, setUserName] = useState(() => {
    return sessionStorage.getItem('infosearch_user') || '';
  });
  const [isAdmin, setIsAdmin] = useState(() => {
    return sessionStorage.getItem('infosearch_is_admin') === 'true';
  });

  useEffect(() => {
    sessionStorage.setItem('infosearch_auth', String(isAuthenticated));
    sessionStorage.setItem('infosearch_user', userName);
    sessionStorage.setItem('infosearch_is_admin', String(isAdmin));
  }, [isAuthenticated, userName, isAdmin]);

  const login = (username: string, password: string): boolean => {
    const validUser = import.meta.env.VITE_ADMIN_USERNAME || 'admin';
    const validPass = import.meta.env.VITE_ADMIN_PASSWORD || 'admin';
    if (username === validUser && password === validPass) {
      setIsAuthenticated(true);
      setUserName(username);
      setIsAdmin(true);
      return true;
    }
    return false;
  };

  const logout = () => {
    setIsAuthenticated(false);
    setUserName('');
    setIsAdmin(false);
    sessionStorage.removeItem('infosearch_auth');
    sessionStorage.removeItem('infosearch_user');
    sessionStorage.removeItem('infosearch_is_admin');
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, userName, isAdmin, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
