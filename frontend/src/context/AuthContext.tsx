/**
 * Contexto de autenticación
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { User, LoginCredentials, RegisterData, AuthToken } from '../types';
import { authApi } from '../lib/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Verificar token al cargar
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      const savedUser = localStorage.getItem('user');
      
      if (token && savedUser) {
        try {
          // Verificar que el token sigue siendo válido
          const currentUser = await authApi.getMe();
          setUser(currentUser);
        } catch {
          // Token inválido, limpiar
          localStorage.removeItem('access_token');
          localStorage.removeItem('user');
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const response: AuthToken = await authApi.login(credentials);
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('user', JSON.stringify(response.user));
    setUser(response.user);
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    const response: AuthToken = await authApi.register(data);
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('user', JSON.stringify(response.user));
    setUser(response.user);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
