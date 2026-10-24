"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

interface Vendor {
  id: string;
  email: string;
  full_name: string;
  instagram_handle: string | null;
  upi_id: string | null;
  created_at: string;
}

interface AuthContextType {
  vendor: Vendor | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

interface SignupData {
  email: string;
  password: string;
  full_name: string;
  instagram_handle?: string;
  upi_id?: string;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [vendor, setVendor] = useState<Vendor | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const storedToken = localStorage.getItem("shopthread_token");
    const storedVendor = localStorage.getItem("shopthread_vendor");
    if (storedToken && storedVendor) {
      setToken(storedToken);
      setVendor(JSON.parse(storedVendor));
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.post("/auth/login", { email, password });
    const { access_token, vendor } = res.data;
    localStorage.setItem("shopthread_token", access_token);
    localStorage.setItem("shopthread_vendor", JSON.stringify(vendor));
    setToken(access_token);
    setVendor(vendor);
    router.push("/dashboard");
  };

  const signup = async (data: SignupData) => {
    const res = await api.post("/auth/signup", data);
    const { access_token, vendor } = res.data;
    localStorage.setItem("shopthread_token", access_token);
    localStorage.setItem("shopthread_vendor", JSON.stringify(vendor));
    setToken(access_token);
    setVendor(vendor);
    router.push("/dashboard");
  };

  const logout = () => {
    localStorage.removeItem("shopthread_token");
    localStorage.removeItem("shopthread_vendor");
    setToken(null);
    setVendor(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider value={{ vendor, token, login, signup, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
