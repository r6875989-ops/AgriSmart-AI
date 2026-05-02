import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem('agrismart_token');
    const savedUser = localStorage.getItem('agrismart_user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      
      // Verify token is still valid
      authAPI.getMe()
        .then((res) => {
          setUser(res.data.user);
          localStorage.setItem('agrismart_user', JSON.stringify(res.data.user));
        })
        .catch(() => {
          logout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const res = await authAPI.login({ email, password });
    const { token: newToken, user: newUser } = res.data;
    
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('agrismart_token', newToken);
    localStorage.setItem('agrismart_user', JSON.stringify(newUser));
    
    return res.data;
  };

  const register = async (name, email, password, confirm_password) => {
    const res = await authAPI.register({ name, email, password, confirm_password });
    const { token: newToken, user: newUser } = res.data;
    
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('agrismart_token', newToken);
    localStorage.setItem('agrismart_user', JSON.stringify(newUser));
    
    return res.data;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('agrismart_token');
    localStorage.removeItem('agrismart_user');
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
