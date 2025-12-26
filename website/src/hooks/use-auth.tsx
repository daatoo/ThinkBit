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
    const token = getToken();
    if (token) {
      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (error) {
        // Token invalid or expired, clear it silently
        console.debug("Token validation failed, clearing auth state");
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
    if (!token) {
      throw new Error("No token provided");
    }
    
    // Token should already be set by api.ts login(), but ensure it's set
    setToken(token);
    
    // Fetch user data immediately (token is now in localStorage)
    try {
      const userData = await getCurrentUser();
      setUser(userData);
      setLoading(false);
    } catch (error) {
      // Token invalid, clear it
      apiLogout();
      setUser(null);
      setLoading(false);
      throw error;
    }
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

