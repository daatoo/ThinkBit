import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { getCurrentUser, getToken, logout as apiLogout, setToken, UserResponse } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface AuthContextType {
  user: UserResponse | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  const checkAuth = async () => {
    if (getToken()) {
      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (error) {
        // Token invalid, clear it
        apiLogout();
        setUser(null);
      }
    } else {
      setUser(null);
    }
    setLoading(false);
  };

  useEffect(() => {
    checkAuth();
  }, []);

  const login = async (token: string) => {
    // Set the token if provided (in case it wasn't set by api.ts)
    if (token) {
      setToken(token);
    }
    await checkAuth();
  };

  const logout = () => {
    apiLogout();
    setUser(null);
    toast({
      title: "Logged out",
      description: "You have been logged out successfully",
    });
  };

  const refreshUser = async () => {
    if (getToken()) {
      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (error) {
        apiLogout();
        setUser(null);
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

