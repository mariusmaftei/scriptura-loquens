import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import api from "../services/api";

const AUTH_TOKEN_KEY = "scriptura_auth_token";

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem(AUTH_TOKEN_KEY));
  const [loading, setLoading] = useState(true);

  const login = useCallback(async (email, password) => {
    const { data } = await api.post("/login", { email, password });
    if (data.token) {
      localStorage.setItem(AUTH_TOKEN_KEY, data.token);
      setToken(data.token);
      return data;
    }
    throw new Error("Login failed");
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setToken(null);
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem(AUTH_TOKEN_KEY);
    setToken(stored);
    setLoading(false);
  }, []);

  useEffect(() => {
    const handleLogout = () => setToken(null);
    window.addEventListener("auth:logout", handleLogout);
    return () => window.removeEventListener("auth:logout", handleLogout);
  }, []);

  useEffect(() => {
    if (token) {
      api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common["Authorization"];
    }
  }, [token]);

  const value = {
    token,
    isAuthenticated: !!token,
    login,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
