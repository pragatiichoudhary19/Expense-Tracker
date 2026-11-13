import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "./api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(Boolean(getToken()));

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    if (!getToken()) return;
    api
      .me()
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    window.addEventListener("spendwise:logout", logout);
    return () => window.removeEventListener("spendwise:logout", logout);
  }, [logout]);

  const authenticate = async (fn, body) => {
    const res = await fn(body);
    setToken(res.access_token);
    setUser(res.user);
  };

  const value = {
    user,
    loading,
    login: (body) => authenticate(api.login, body),
    register: (body) => authenticate(api.register, body),
    logout,
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
